-- Migration 017: Add User Insights Management System
-- Purpose: Enable users to manually add, edit, delete, and manage knowledge insights
-- Extends the AI-driven categorization system with full user control capabilities

-- ================================================================
-- PART 1: Extend workspace_insights table for user management
-- ================================================================

-- Add user management fields to workspace_insights
ALTER TABLE workspace_insights ADD COLUMN IF NOT EXISTS created_by VARCHAR(255) DEFAULT 'ai_system';
ALTER TABLE workspace_insights ADD COLUMN IF NOT EXISTS last_modified_by VARCHAR(255);
ALTER TABLE workspace_insights ADD COLUMN IF NOT EXISTS is_user_created BOOLEAN DEFAULT FALSE;
ALTER TABLE workspace_insights ADD COLUMN IF NOT EXISTS is_user_modified BOOLEAN DEFAULT FALSE;
ALTER TABLE workspace_insights ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE;
ALTER TABLE workspace_insights ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;
ALTER TABLE workspace_insights ADD COLUMN IF NOT EXISTS deleted_by VARCHAR(255);
ALTER TABLE workspace_insights ADD COLUMN IF NOT EXISTS version_number INTEGER DEFAULT 1;
ALTER TABLE workspace_insights ADD COLUMN IF NOT EXISTS parent_insight_id UUID REFERENCES workspace_insights(id);

-- User flags for marking insights as verified/important/etc
ALTER TABLE workspace_insights ADD COLUMN IF NOT EXISTS user_flags JSONB DEFAULT '{}';
-- Expected structure: {"verified": true, "important": false, "outdated": false, "reviewed_by": "user_id", "flag_history": []}

-- Title field for user-friendly display
ALTER TABLE workspace_insights ADD COLUMN IF NOT EXISTS title VARCHAR(500);

-- Original content backup for AI-generated insights that get modified
ALTER TABLE workspace_insights ADD COLUMN IF NOT EXISTS original_content TEXT;
ALTER TABLE workspace_insights ADD COLUMN IF NOT EXISTS original_metadata JSONB;

-- ================================================================
-- PART 2: Create audit trail table for tracking all changes
-- ================================================================

CREATE TABLE IF NOT EXISTS insight_audit_trail (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    insight_id UUID REFERENCES workspace_insights(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,
    performed_by VARCHAR(255) NOT NULL,
    performed_at TIMESTAMP DEFAULT NOW(),
    old_values JSONB,
    new_values JSONB,
    change_description TEXT,
    workspace_id UUID REFERENCES workspaces(id),
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    -- Indices for efficient querying
    CONSTRAINT chk_action CHECK (action IN (
        'CREATE', 'UPDATE', 'DELETE', 'RESTORE', 
        'FLAG', 'UNFLAG', 'CATEGORIZE', 'VERIFY',
        'BULK_UPDATE', 'BULK_DELETE', 'IMPORT', 'EXPORT'
    ))
);

-- Create indices for audit trail
CREATE INDEX IF NOT EXISTS idx_audit_trail_insight_id ON insight_audit_trail(insight_id);
CREATE INDEX IF NOT EXISTS idx_audit_trail_workspace_id ON insight_audit_trail(workspace_id);
CREATE INDEX IF NOT EXISTS idx_audit_trail_performed_by ON insight_audit_trail(performed_by);
CREATE INDEX IF NOT EXISTS idx_audit_trail_performed_at ON insight_audit_trail(performed_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_trail_action ON insight_audit_trail(action);

-- ================================================================
-- PART 3: Create insight categories extension for user-defined categories
-- ================================================================

CREATE TABLE IF NOT EXISTS user_insight_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    category_name VARCHAR(100) NOT NULL,
    category_description TEXT,
    color_hex VARCHAR(7) DEFAULT '#6B7280',
    icon_name VARCHAR(50) DEFAULT 'folder',
    parent_category_id UUID REFERENCES user_insight_categories(id),
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    
    -- Ensure unique category names per workspace
    CONSTRAINT uq_workspace_category UNIQUE(workspace_id, category_name)
);

CREATE INDEX IF NOT EXISTS idx_user_categories_workspace ON user_insight_categories(workspace_id);
CREATE INDEX IF NOT EXISTS idx_user_categories_parent ON user_insight_categories(parent_category_id);

-- ================================================================
-- PART 4: Create bulk operations tracking table
-- ================================================================

CREATE TABLE IF NOT EXISTS insight_bulk_operations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id),
    operation_type VARCHAR(50) NOT NULL,
    affected_insights JSONB NOT NULL, -- Array of insight IDs
    performed_by VARCHAR(255) NOT NULL,
    performed_at TIMESTAMP DEFAULT NOW(),
    operation_status VARCHAR(20) DEFAULT 'pending',
    operation_result JSONB,
    error_message TEXT,
    
    CONSTRAINT chk_operation_type CHECK (operation_type IN (
        'BULK_DELETE', 'BULK_CATEGORIZE', 'BULK_FLAG', 
        'BULK_VERIFY', 'BULK_EXPORT', 'BULK_RESTORE'
    )),
    CONSTRAINT chk_operation_status CHECK (operation_status IN (
        'pending', 'in_progress', 'completed', 'failed', 'cancelled'
    ))
);

CREATE INDEX IF NOT EXISTS idx_bulk_operations_workspace ON insight_bulk_operations(workspace_id);
CREATE INDEX IF NOT EXISTS idx_bulk_operations_status ON insight_bulk_operations(operation_status);

-- ================================================================
-- PART 5: Add indices for user management queries
-- ================================================================

-- Indices for user-created and modified insights
CREATE INDEX IF NOT EXISTS idx_insights_created_by ON workspace_insights(created_by);
CREATE INDEX IF NOT EXISTS idx_insights_modified_by ON workspace_insights(last_modified_by);
CREATE INDEX IF NOT EXISTS idx_insights_user_created ON workspace_insights(is_user_created) WHERE is_user_created = TRUE;
CREATE INDEX IF NOT EXISTS idx_insights_user_modified ON workspace_insights(is_user_modified) WHERE is_user_modified = TRUE;
CREATE INDEX IF NOT EXISTS idx_insights_deleted ON workspace_insights(is_deleted) WHERE is_deleted = TRUE;
CREATE INDEX IF NOT EXISTS idx_insights_parent ON workspace_insights(parent_insight_id);

-- Composite index for filtering user vs AI insights
CREATE INDEX IF NOT EXISTS idx_insights_source_filter 
    ON workspace_insights(workspace_id, is_user_created, is_deleted, created_at DESC);

-- Index for user flags JSONB queries
CREATE INDEX IF NOT EXISTS idx_insights_user_flags ON workspace_insights USING gin(user_flags);

-- Index for title search
CREATE INDEX IF NOT EXISTS idx_insights_title ON workspace_insights(title);
CREATE INDEX IF NOT EXISTS idx_insights_title_trgm ON workspace_insights USING gin(title gin_trgm_ops);

-- ================================================================
-- PART 6: Create triggers for automatic audit logging
-- ================================================================

-- Function to automatically log changes to audit trail
CREATE OR REPLACE FUNCTION log_insight_changes()
RETURNS TRIGGER AS $$
DECLARE
    v_action VARCHAR(50);
    v_old_values JSONB;
    v_new_values JSONB;
BEGIN
    -- Determine the action type
    IF TG_OP = 'INSERT' THEN
        v_action := 'CREATE';
        v_old_values := NULL;
        v_new_values := to_jsonb(NEW);
    ELSIF TG_OP = 'UPDATE' THEN
        -- Check for specific update types
        IF OLD.is_deleted = FALSE AND NEW.is_deleted = TRUE THEN
            v_action := 'DELETE';
        ELSIF OLD.is_deleted = TRUE AND NEW.is_deleted = FALSE THEN
            v_action := 'RESTORE';
        ELSIF OLD.user_flags != NEW.user_flags THEN
            v_action := 'FLAG';
        ELSIF OLD.insight_category != NEW.insight_category THEN
            v_action := 'CATEGORIZE';
        ELSE
            v_action := 'UPDATE';
        END IF;
        v_old_values := to_jsonb(OLD);
        v_new_values := to_jsonb(NEW);
    ELSIF TG_OP = 'DELETE' THEN
        v_action := 'DELETE';
        v_old_values := to_jsonb(OLD);
        v_new_values := NULL;
    END IF;
    
    -- Insert audit log entry
    INSERT INTO insight_audit_trail (
        insight_id,
        action,
        performed_by,
        old_values,
        new_values,
        workspace_id
    ) VALUES (
        COALESCE(NEW.id, OLD.id),
        v_action,
        COALESCE(NEW.last_modified_by, NEW.created_by, 'system'),
        v_old_values,
        v_new_values,
        COALESCE(NEW.workspace_id, OLD.workspace_id)
    );
    
    -- Update version number on UPDATE
    IF TG_OP = 'UPDATE' AND NEW.is_user_modified = TRUE THEN
        NEW.version_number := COALESCE(OLD.version_number, 0) + 1;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for audit logging
DROP TRIGGER IF EXISTS trigger_insight_audit ON workspace_insights;
CREATE TRIGGER trigger_insight_audit
    AFTER INSERT OR UPDATE OR DELETE ON workspace_insights
    FOR EACH ROW
    EXECUTE FUNCTION log_insight_changes();

-- ================================================================
-- PART 7: Create function for insight versioning
-- ================================================================

CREATE OR REPLACE FUNCTION create_insight_version()
RETURNS TRIGGER AS $$
BEGIN
    -- When an insight is modified, create a version copy
    IF OLD.is_user_modified = FALSE AND NEW.is_user_modified = TRUE THEN
        -- Store the original content if not already stored
        IF NEW.original_content IS NULL THEN
            NEW.original_content := OLD.content;
            NEW.original_metadata := OLD.metadata;
        END IF;
        
        -- Create a version entry (linked via parent_insight_id)
        INSERT INTO workspace_insights (
            workspace_id,
            parent_insight_id,
            insight_type,
            content,
            metadata,
            created_by,
            created_at,
            version_number,
            is_deleted
        ) VALUES (
            OLD.workspace_id,
            OLD.id,
            OLD.insight_type,
            OLD.content,
            OLD.metadata,
            'version_system',
            NOW(),
            OLD.version_number,
            TRUE -- Mark versions as deleted so they don't appear in normal queries
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for versioning
DROP TRIGGER IF EXISTS trigger_insight_versioning ON workspace_insights;
CREATE TRIGGER trigger_insight_versioning
    BEFORE UPDATE ON workspace_insights
    FOR EACH ROW
    WHEN (OLD.content IS DISTINCT FROM NEW.content)
    EXECUTE FUNCTION create_insight_version();

-- ================================================================
-- PART 8: Create views for easy access
-- ================================================================

-- View for active user-created insights
CREATE OR REPLACE VIEW user_created_insights AS
SELECT 
    wi.*,
    w.name as workspace_name,
    (wi.user_flags->>'verified')::boolean as is_verified,
    (wi.user_flags->>'important')::boolean as is_important
FROM workspace_insights wi
LEFT JOIN workspaces w ON wi.workspace_id = w.id
WHERE wi.is_user_created = TRUE 
  AND wi.is_deleted = FALSE;

-- View for recently modified insights
CREATE OR REPLACE VIEW recently_modified_insights AS
SELECT 
    wi.*,
    w.name as workspace_name,
    at.performed_by as last_modifier,
    at.performed_at as last_modified_at,
    at.action as last_action
FROM workspace_insights wi
LEFT JOIN workspaces w ON wi.workspace_id = w.id
LEFT JOIN LATERAL (
    SELECT performed_by, performed_at, action
    FROM insight_audit_trail
    WHERE insight_id = wi.id
    ORDER BY performed_at DESC
    LIMIT 1
) at ON TRUE
WHERE wi.is_user_modified = TRUE
  AND wi.is_deleted = FALSE
ORDER BY at.performed_at DESC;

-- View for insights pending review
CREATE OR REPLACE VIEW insights_pending_review AS
SELECT 
    wi.*,
    w.name as workspace_name,
    CASE 
        WHEN wi.is_user_created THEN 'user'
        ELSE 'ai'
    END as source_type
FROM workspace_insights wi
LEFT JOIN workspaces w ON wi.workspace_id = w.id
WHERE (wi.user_flags->>'needs_review')::boolean = TRUE
  AND wi.is_deleted = FALSE
ORDER BY wi.created_at DESC;

-- ================================================================
-- PART 9: Helper functions for common operations
-- ================================================================

-- Function to bulk flag insights
CREATE OR REPLACE FUNCTION bulk_flag_insights(
    p_insight_ids UUID[],
    p_flag_name VARCHAR(50),
    p_flag_value BOOLEAN,
    p_performed_by VARCHAR(255)
)
RETURNS INTEGER AS $$
DECLARE
    v_updated_count INTEGER;
BEGIN
    UPDATE workspace_insights
    SET 
        user_flags = jsonb_set(
            COALESCE(user_flags, '{}'::jsonb),
            ARRAY[p_flag_name],
            to_jsonb(p_flag_value)
        ),
        last_modified_by = p_performed_by,
        updated_at = NOW()
    WHERE id = ANY(p_insight_ids)
      AND is_deleted = FALSE;
    
    GET DIAGNOSTICS v_updated_count = ROW_COUNT;
    RETURN v_updated_count;
END;
$$ LANGUAGE plpgsql;

-- Function to restore deleted insights
CREATE OR REPLACE FUNCTION restore_deleted_insights(
    p_insight_ids UUID[],
    p_restored_by VARCHAR(255)
)
RETURNS INTEGER AS $$
DECLARE
    v_restored_count INTEGER;
BEGIN
    UPDATE workspace_insights
    SET 
        is_deleted = FALSE,
        deleted_at = NULL,
        deleted_by = NULL,
        last_modified_by = p_restored_by,
        updated_at = NOW()
    WHERE id = ANY(p_insight_ids)
      AND is_deleted = TRUE;
    
    GET DIAGNOSTICS v_restored_count = ROW_COUNT;
    RETURN v_restored_count;
END;
$$ LANGUAGE plpgsql;

-- ================================================================
-- PART 10: Add comments for documentation
-- ================================================================

COMMENT ON COLUMN workspace_insights.created_by IS 'User ID or system identifier that created the insight';
COMMENT ON COLUMN workspace_insights.last_modified_by IS 'User ID of the last person to modify the insight';
COMMENT ON COLUMN workspace_insights.is_user_created IS 'TRUE if insight was manually created by a user';
COMMENT ON COLUMN workspace_insights.is_user_modified IS 'TRUE if insight has been modified by a user';
COMMENT ON COLUMN workspace_insights.is_deleted IS 'Soft delete flag - TRUE means logically deleted';
COMMENT ON COLUMN workspace_insights.user_flags IS 'JSON object containing user-defined flags like verified, important, etc';
COMMENT ON COLUMN workspace_insights.title IS 'User-friendly title for the insight';
COMMENT ON COLUMN workspace_insights.version_number IS 'Version number incremented on each modification';
COMMENT ON COLUMN workspace_insights.parent_insight_id IS 'Reference to parent insight for versioning';

COMMENT ON TABLE insight_audit_trail IS 'Complete audit trail of all changes to insights';
COMMENT ON TABLE user_insight_categories IS 'User-defined categories for organizing insights';
COMMENT ON TABLE insight_bulk_operations IS 'Tracking table for bulk operations on insights';

-- ================================================================
-- PART 11: Insert sample data for testing
-- ================================================================

-- Sample user-created insight
INSERT INTO workspace_insights (
    id,
    workspace_id,
    insight_type,
    title,
    content,
    domain_type,
    business_value_score,
    confidence_score,
    insight_category,
    created_by,
    is_user_created,
    user_flags,
    relevance_tags,
    agent_role,
    metadata
) VALUES (
    gen_random_uuid(),
    '1f1bf9cf-3c46-48ed-96f3-ec826742ee02',
    'best_practice',
    'Optimal Posting Times for B2B Audience',
    'Based on our campaign data, B2B audiences on LinkedIn show highest engagement between 7-9 AM and 12-1 PM on weekdays, particularly Tuesday through Thursday.',
    'social_media',
    0.75,
    0.85,
    'best_practice',
    'user_123',
    TRUE,
    '{"verified": true, "important": true, "source": "manual_entry"}'::jsonb,
    ARRAY['linkedin', 'b2b', 'timing', 'engagement'],
    'marketing_specialist',
    '{"data_source": "campaign_analytics", "sample_size": 500}'::jsonb
) ON CONFLICT (id) DO NOTHING;

-- Success message
SELECT 'Migration 017 completed successfully: User Insights Management System implemented' as status;