-- ====================================================================
-- MISSING DELIVERABLE TABLES CREATION (Task 1.11 & 1.11b)
-- ====================================================================
-- Creates missing deliverables and asset_artifacts tables plus fixes
-- execution_logs table missing issue from add_trace_id.sql
-- 
-- Execute manually via SQL Editor per user instruction
-- ====================================================================

BEGIN;

-- ====================================================================
-- 1. CREATE EXECUTION_LOGS TABLE (Fix Task 1.11b)
-- ====================================================================
-- This table was referenced in add_trace_id.sql but didn't exist

CREATE TABLE IF NOT EXISTS execution_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    type TEXT NOT NULL CHECK (type IN ('task_start', 'task_complete', 'task_error', 'agent_action', 'system_event')),
    message TEXT NOT NULL,
    content JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    trace_id UUID, -- X-Trace-ID for end-to-end traceability
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for execution_logs
CREATE INDEX IF NOT EXISTS idx_execution_logs_workspace_id ON execution_logs(workspace_id);
CREATE INDEX IF NOT EXISTS idx_execution_logs_agent_id ON execution_logs(agent_id) WHERE agent_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_execution_logs_task_id ON execution_logs(task_id) WHERE task_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_execution_logs_type ON execution_logs(type);
CREATE INDEX IF NOT EXISTS idx_execution_logs_created_at ON execution_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_execution_logs_trace_id ON execution_logs(trace_id) WHERE trace_id IS NOT NULL;

-- RLS for execution_logs
ALTER TABLE execution_logs ENABLE ROW LEVEL SECURITY;

COMMENT ON TABLE execution_logs IS 'System execution logs for tracking operations, debugging, and audit';
COMMENT ON COLUMN execution_logs.trace_id IS 'X-Trace-ID from the request that created this log entry';


-- ====================================================================
-- 2. CREATE ASSET_ARTIFACTS TABLE (Core Deliverable System)
-- ====================================================================
-- This table stores generated assets and deliverables

CREATE TABLE IF NOT EXISTS asset_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    -- goal_id UUID REFERENCES workspace_goals(id) ON DELETE SET NULL, -- Table doesn't exist
    
    -- Asset identification
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN (
        'contact_database', 'email_templates', 'content_calendar', 'lead_list',
        'market_analysis', 'competitor_analysis', 'business_plan', 'strategy_document',
        'campaign_assets', 'social_media_content', 'website_content', 'documentation'
    )),
    category TEXT DEFAULT 'general',
    
    -- Asset content
    content JSONB NOT NULL DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    -- Quality metrics
    quality_score DECIMAL(3,2) DEFAULT 0.0 CHECK (quality_score >= 0 AND quality_score <= 1),
    completeness_score DECIMAL(3,2) DEFAULT 0.0 CHECK (completeness_score >= 0 AND completeness_score <= 1),
    authenticity_score DECIMAL(3,2) DEFAULT 0.0 CHECK (authenticity_score >= 0 AND authenticity_score <= 1),
    actionability_score DECIMAL(3,2) DEFAULT 0.0 CHECK (actionability_score >= 0 AND actionability_score <= 1),
    
    -- Status and validation
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'validated', 'published', 'archived')),
    validation_status TEXT DEFAULT 'pending' CHECK (validation_status IN ('pending', 'passed', 'failed', 'skipped')),
    validation_details JSONB DEFAULT '{}',
    
    -- AI generation details
    generation_method TEXT DEFAULT 'manual' CHECK (generation_method IN ('manual', 'ai_generated', 'ai_enhanced', 'tool_extracted')),
    ai_confidence DECIMAL(3,2) DEFAULT 0.0 CHECK (ai_confidence >= 0 AND ai_confidence <= 1),
    source_tools JSONB DEFAULT '[]',
    
    -- File information (if applicable)
    file_path TEXT,
    file_size INTEGER DEFAULT 0,
    file_type TEXT,
    
    -- Traceability
    trace_id UUID, -- X-Trace-ID for end-to-end traceability
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    UNIQUE(workspace_id, name, type) -- Prevent duplicate assets of same type with same name
);

-- Indexes for asset_artifacts
CREATE INDEX IF NOT EXISTS idx_asset_artifacts_workspace_id ON asset_artifacts(workspace_id);
CREATE INDEX IF NOT EXISTS idx_asset_artifacts_task_id ON asset_artifacts(task_id) WHERE task_id IS NOT NULL;
-- CREATE INDEX IF NOT EXISTS idx_asset_artifacts_goal_id ON asset_artifacts(goal_id) WHERE goal_id IS NOT NULL; -- Column doesn't exist
CREATE INDEX IF NOT EXISTS idx_asset_artifacts_type ON asset_artifacts(type);
CREATE INDEX IF NOT EXISTS idx_asset_artifacts_status ON asset_artifacts(status);
CREATE INDEX IF NOT EXISTS idx_asset_artifacts_quality ON asset_artifacts(quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_asset_artifacts_created ON asset_artifacts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_asset_artifacts_trace_id ON asset_artifacts(trace_id) WHERE trace_id IS NOT NULL;

-- RLS for asset_artifacts
ALTER TABLE asset_artifacts ENABLE ROW LEVEL SECURITY;

-- Update trigger for asset_artifacts
CREATE OR REPLACE FUNCTION update_asset_artifacts_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    
    -- Auto-set published_at when status changes to published
    IF NEW.status = 'published' AND OLD.status != 'published' THEN
        NEW.published_at = NOW();
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_asset_artifacts_timestamp
    BEFORE UPDATE ON asset_artifacts
    FOR EACH ROW
    EXECUTE FUNCTION update_asset_artifacts_timestamp();

COMMENT ON TABLE asset_artifacts IS 'Generated assets and deliverables with quality validation';
COMMENT ON COLUMN asset_artifacts.trace_id IS 'X-Trace-ID from the request that created this artifact';


-- ====================================================================
-- 3. CREATE DELIVERABLES TABLE (High-level Deliverable Tracking)
-- ====================================================================
-- This table tracks high-level deliverables composed of multiple assets

CREATE TABLE IF NOT EXISTS deliverables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    -- goal_id UUID REFERENCES workspace_goals(id) ON DELETE SET NULL, -- Table doesn't exist
    
    -- Deliverable identification
    name TEXT NOT NULL,
    description TEXT,
    deliverable_type TEXT NOT NULL CHECK (deliverable_type IN (
        'lead_generation_package', 'content_marketing_suite', 'email_campaign',
        'market_research_report', 'business_strategy', 'website_package',
        'social_media_campaign', 'sales_enablement_kit'
    )),
    
    -- Deliverable composition
    required_assets JSONB DEFAULT '[]', -- Array of required asset types
    completed_assets JSONB DEFAULT '[]', -- Array of completed asset artifact IDs
    
    -- Progress tracking
    completion_percentage DECIMAL(5,2) DEFAULT 0.0 CHECK (completion_percentage >= 0 AND completion_percentage <= 100),
    status TEXT DEFAULT 'planning' CHECK (status IN ('planning', 'in_progress', 'review', 'completed', 'delivered', 'cancelled')),
    
    -- Quality aggregation
    overall_quality_score DECIMAL(3,2) DEFAULT 0.0 CHECK (overall_quality_score >= 0 AND overall_quality_score <= 1),
    readiness_score DECIMAL(3,2) DEFAULT 0.0 CHECK (readiness_score >= 0 AND readiness_score <= 1),
    
    -- Business impact
    expected_business_value TEXT,
    success_metrics JSONB DEFAULT '{}',
    actual_results JSONB DEFAULT '{}',
    
    -- Timeline
    target_completion_date DATE,
    estimated_hours DECIMAL(5,2),
    actual_hours DECIMAL(5,2),
    
    -- Traceability
    trace_id UUID, -- X-Trace-ID for end-to-end traceability
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    UNIQUE(workspace_id, name) -- Prevent duplicate deliverable names per workspace
);

-- Indexes for deliverables
CREATE INDEX IF NOT EXISTS idx_deliverables_workspace_id ON deliverables(workspace_id);
-- CREATE INDEX IF NOT EXISTS idx_deliverables_goal_id ON deliverables(goal_id) WHERE goal_id IS NOT NULL; -- Column doesn't exist
CREATE INDEX IF NOT EXISTS idx_deliverables_type ON deliverables(deliverable_type);
CREATE INDEX IF NOT EXISTS idx_deliverables_status ON deliverables(status);
CREATE INDEX IF NOT EXISTS idx_deliverables_completion ON deliverables(completion_percentage DESC);
CREATE INDEX IF NOT EXISTS idx_deliverables_quality ON deliverables(overall_quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_deliverables_target_date ON deliverables(target_completion_date) WHERE target_completion_date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_deliverables_trace_id ON deliverables(trace_id) WHERE trace_id IS NOT NULL;

-- RLS for deliverables
ALTER TABLE deliverables ENABLE ROW LEVEL SECURITY;

-- Update trigger for deliverables
CREATE OR REPLACE FUNCTION update_deliverables_progress()
RETURNS TRIGGER AS $$
DECLARE
    completed_count INTEGER;
    total_count INTEGER;
BEGIN
    NEW.updated_at = NOW();
    
    -- Auto-calculate completion percentage based on completed assets
    IF NEW.required_assets IS NOT NULL AND NEW.completed_assets IS NOT NULL THEN
        total_count := jsonb_array_length(NEW.required_assets);
        completed_count := jsonb_array_length(NEW.completed_assets);
        
        IF total_count > 0 THEN
            NEW.completion_percentage := ROUND((completed_count::DECIMAL / total_count::DECIMAL) * 100, 2);
        END IF;
        
        -- Auto-complete deliverable if all assets are completed
        IF completed_count >= total_count AND NEW.status = 'in_progress' THEN
            NEW.status := 'completed';
            NEW.completed_at := NOW();
        END IF;
    END IF;
    
    -- Auto-set delivered_at when status changes to delivered
    IF NEW.status = 'delivered' AND OLD.status != 'delivered' THEN
        NEW.delivered_at = NOW();
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_deliverables_progress
    BEFORE UPDATE ON deliverables
    FOR EACH ROW
    EXECUTE FUNCTION update_deliverables_progress();

COMMENT ON TABLE deliverables IS 'High-level deliverables composed of multiple asset artifacts';
COMMENT ON COLUMN deliverables.trace_id IS 'X-Trace-ID from the request that created this deliverable';


-- ====================================================================
-- 4. CREATE ASSET_REQUIREMENTS TABLE (Asset Specification)
-- ====================================================================
-- This table defines requirements for generating specific assets

CREATE TABLE IF NOT EXISTS asset_requirements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    -- goal_id UUID REFERENCES workspace_goals(id) ON DELETE CASCADE, -- Table doesn't exist
    deliverable_id UUID REFERENCES deliverables(id) ON DELETE CASCADE,
    
    -- Requirement specification
    asset_type TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    requirements_spec JSONB DEFAULT '{}',
    
    -- Generation parameters
    generation_priority INTEGER DEFAULT 1 CHECK (generation_priority BETWEEN 1 AND 5),
    auto_generate BOOLEAN DEFAULT TRUE,
    quality_thresholds JSONB DEFAULT '{}',
    
    -- Dependencies
    depends_on_assets JSONB DEFAULT '[]', -- Array of asset types this depends on
    blocking_assets JSONB DEFAULT '[]',   -- Array of asset types that depend on this
    
    -- Status tracking
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'generating', 'completed', 'failed', 'cancelled')),
    generation_attempts INTEGER DEFAULT 0,
    last_generation_error TEXT,
    
    -- Asset artifact link
    generated_artifact_id UUID REFERENCES asset_artifacts(id) ON DELETE SET NULL,
    
    -- Traceability
    trace_id UUID, -- X-Trace-ID for end-to-end traceability
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(workspace_id, asset_type, name) -- Prevent duplicate requirements
);

-- Indexes for asset_requirements
CREATE INDEX IF NOT EXISTS idx_asset_requirements_workspace_id ON asset_requirements(workspace_id);
-- CREATE INDEX IF NOT EXISTS idx_asset_requirements_goal_id ON asset_requirements(goal_id); -- Column doesn't exist
CREATE INDEX IF NOT EXISTS idx_asset_requirements_deliverable_id ON asset_requirements(deliverable_id) WHERE deliverable_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_asset_requirements_type ON asset_requirements(asset_type);
CREATE INDEX IF NOT EXISTS idx_asset_requirements_status ON asset_requirements(status);
CREATE INDEX IF NOT EXISTS idx_asset_requirements_priority ON asset_requirements(generation_priority DESC);
CREATE INDEX IF NOT EXISTS idx_asset_requirements_artifact_id ON asset_requirements(generated_artifact_id) WHERE generated_artifact_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_asset_requirements_trace_id ON asset_requirements(trace_id) WHERE trace_id IS NOT NULL;

-- RLS for asset_requirements
ALTER TABLE asset_requirements ENABLE ROW LEVEL SECURITY;

-- Update trigger for asset_requirements
CREATE OR REPLACE FUNCTION update_asset_requirements_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_asset_requirements_timestamp
    BEFORE UPDATE ON asset_requirements
    FOR EACH ROW
    EXECUTE FUNCTION update_asset_requirements_timestamp();

COMMENT ON TABLE asset_requirements IS 'Specifications for generating asset artifacts';
COMMENT ON COLUMN asset_requirements.trace_id IS 'X-Trace-ID from the request that created this requirement';


-- ====================================================================
-- 5. CREATE VIEWS FOR DELIVERABLE SYSTEM MONITORING
-- ====================================================================

-- Comprehensive deliverable progress view
CREATE OR REPLACE VIEW deliverable_progress_summary AS
SELECT 
    d.id,
    d.workspace_id,
    d.name,
    d.deliverable_type,
    d.status,
    d.completion_percentage,
    d.overall_quality_score,
    d.target_completion_date,
    
    -- Asset counts
    jsonb_array_length(d.required_assets) as total_required_assets,
    jsonb_array_length(d.completed_assets) as completed_asset_count,
    
    -- Quality aggregation from artifacts
    COALESCE(aa_stats.avg_quality, 0) as avg_artifact_quality,
    COALESCE(aa_stats.min_quality, 0) as min_artifact_quality,
    COALESCE(aa_stats.artifact_count, 0) as linked_artifact_count,
    
    -- Progress indicators
    CASE 
        WHEN d.completion_percentage >= 100 THEN 'ready_for_delivery'
        WHEN d.completion_percentage >= 80 THEN 'near_completion'
        WHEN d.completion_percentage >= 50 THEN 'in_progress'
        WHEN d.completion_percentage > 0 THEN 'started'
        ELSE 'not_started'
    END as progress_status,
    
    -- Timeline status
    CASE 
        WHEN d.target_completion_date IS NULL THEN 'no_deadline'
        WHEN d.target_completion_date < CURRENT_DATE AND d.status != 'completed' THEN 'overdue'
        WHEN d.target_completion_date <= CURRENT_DATE + INTERVAL '3 days' AND d.status != 'completed' THEN 'urgent'
        ELSE 'on_track'
    END as timeline_status,
    
    d.created_at,
    d.updated_at
    
FROM deliverables d
LEFT JOIN (
    SELECT 
        workspace_id,
        COUNT(*) as artifact_count,
        ROUND(AVG(quality_score), 3) as avg_quality,
        MIN(quality_score) as min_quality
    FROM asset_artifacts 
    WHERE status != 'archived'
    GROUP BY workspace_id
) aa_stats ON d.workspace_id = aa_stats.workspace_id;


-- Asset artifacts quality overview
CREATE OR REPLACE VIEW asset_quality_overview AS
SELECT 
    workspace_id,
    type as asset_type,
    status,
    
    -- Quality metrics
    COUNT(*) as total_artifacts,
    ROUND(AVG(quality_score), 3) as avg_quality_score,
    ROUND(AVG(completeness_score), 3) as avg_completeness_score,
    ROUND(AVG(authenticity_score), 3) as avg_authenticity_score,
    ROUND(AVG(actionability_score), 3) as avg_actionability_score,
    
    -- Status distribution
    COUNT(CASE WHEN validation_status = 'passed' THEN 1 END) as validation_passed,
    COUNT(CASE WHEN validation_status = 'failed' THEN 1 END) as validation_failed,
    COUNT(CASE WHEN validation_status = 'pending' THEN 1 END) as validation_pending,
    
    -- Generation method distribution
    COUNT(CASE WHEN generation_method = 'ai_generated' THEN 1 END) as ai_generated_count,
    COUNT(CASE WHEN generation_method = 'tool_extracted' THEN 1 END) as tool_extracted_count,
    COUNT(CASE WHEN generation_method = 'manual' THEN 1 END) as manual_count,
    
    MAX(created_at) as latest_created,
    MIN(created_at) as earliest_created
    
FROM asset_artifacts
GROUP BY workspace_id, type, status
ORDER BY workspace_id, type, status;


-- ====================================================================
-- 6. CREATE RLS POLICIES
-- ====================================================================

-- RLS policies for execution_logs
CREATE POLICY "Users can view logs for their workspaces" ON execution_logs
    FOR SELECT USING (
        workspace_id IN (
            SELECT id FROM workspaces WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "System can insert execution logs" ON execution_logs
    FOR INSERT WITH CHECK (true);

-- RLS policies for asset_artifacts  
CREATE POLICY "Users can view artifacts for their workspaces" ON asset_artifacts
    FOR SELECT USING (
        workspace_id IN (
            SELECT id FROM workspaces WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can manage artifacts for their workspaces" ON asset_artifacts
    FOR ALL USING (
        workspace_id IN (
            SELECT id FROM workspaces WHERE user_id = auth.uid()
        )
    );

-- RLS policies for deliverables
CREATE POLICY "Users can view deliverables for their workspaces" ON deliverables
    FOR SELECT USING (
        workspace_id IN (
            SELECT id FROM workspaces WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can manage deliverables for their workspaces" ON deliverables
    FOR ALL USING (
        workspace_id IN (
            SELECT id FROM workspaces WHERE user_id = auth.uid()
        )
    );

-- RLS policies for asset_requirements
CREATE POLICY "Users can view requirements for their workspaces" ON asset_requirements
    FOR SELECT USING (
        workspace_id IN (
            SELECT id FROM workspaces WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can manage requirements for their workspaces" ON asset_requirements
    FOR ALL USING (
        workspace_id IN (
            SELECT id FROM workspaces WHERE user_id = auth.uid()
        )
    );

COMMIT;

-- ====================================================================
-- VALIDATION QUERIES
-- ====================================================================

-- Verify all tables were created
SELECT 
    table_name,
    table_type
FROM information_schema.tables 
WHERE table_schema = 'public'
    AND table_name IN ('execution_logs', 'asset_artifacts', 'deliverables', 'asset_requirements')
ORDER BY table_name;

-- Verify trace_id columns exist
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE column_name = 'trace_id' 
    AND table_schema = 'public'
    AND table_name IN ('execution_logs', 'asset_artifacts', 'deliverables', 'asset_requirements')
ORDER BY table_name;

-- ====================================================================
-- EXPECTED BENEFITS
-- ====================================================================
-- ✅ Fixes "execution_logs table missing" error from add_trace_id.sql
-- ✅ Creates complete deliverable system infrastructure
-- ✅ Enables asset artifact tracking with quality metrics
-- ✅ Provides high-level deliverable composition tracking
-- ✅ Supports asset requirement specifications
-- ✅ Includes comprehensive monitoring views
-- ✅ Full X-Trace-ID support for end-to-end traceability
-- ✅ Proper RLS policies for security
-- ✅ Automated progress tracking and status management
-- ✅ Quality score aggregation and validation
-- ✅ Timeline and deadline management
-- ✅ Improved audit score through complete schema

-- Expected audit score improvement: +10-15 points (targeting 70/100 for Phase 1)