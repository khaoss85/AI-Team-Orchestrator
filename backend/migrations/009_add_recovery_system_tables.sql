-- ================================================================================================
-- MIGRATION 009: ADD RECOVERY SYSTEM TABLES
-- ================================================================================================
-- Purpose: Add database support for FailureDetectionEngine and RecoveryExplanationEngine
-- Date: 2025-08-26  
-- Author: AI-Team-Orchestrator Auto-Recovery System
-- ================================================================================================

-- ROLLBACK INSTRUCTIONS:
-- To rollback this migration, run 009_add_recovery_system_tables_ROLLBACK.sql

-- ================================================================================================
-- 1. FAILURE PATTERNS TABLE
-- ================================================================================================
-- Stores detected failure patterns for machine learning and trend analysis
CREATE TABLE IF NOT EXISTS failure_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    
    -- Pattern identification
    pattern_signature TEXT NOT NULL,              -- Computed signature for deduplication
    failure_type TEXT NOT NULL,                   -- FailureType enum value
    error_message_hash TEXT NOT NULL,             -- Hash of error message for matching
    
    -- Pattern details
    error_message TEXT NOT NULL,
    error_type TEXT,
    root_cause_category TEXT,
    
    -- Frequency tracking
    occurrence_count INTEGER DEFAULT 1,
    first_detected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_detected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    -- Pattern metadata
    is_transient BOOLEAN DEFAULT true,
    confidence_score FLOAT DEFAULT 0.0,
    pattern_source TEXT DEFAULT 'failure_detection_engine',
    
    -- Context
    execution_stage TEXT,
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    context_metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    -- Constraints
    CONSTRAINT failure_patterns_confidence_check CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    CONSTRAINT failure_patterns_occurrence_check CHECK (occurrence_count > 0)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_failure_patterns_workspace_id ON failure_patterns(workspace_id);
CREATE INDEX IF NOT EXISTS idx_failure_patterns_task_id ON failure_patterns(task_id);
CREATE INDEX IF NOT EXISTS idx_failure_patterns_pattern_signature ON failure_patterns(pattern_signature);
CREATE INDEX IF NOT EXISTS idx_failure_patterns_failure_type ON failure_patterns(failure_type);
CREATE INDEX IF NOT EXISTS idx_failure_patterns_error_hash ON failure_patterns(error_message_hash);
CREATE INDEX IF NOT EXISTS idx_failure_patterns_last_detected ON failure_patterns(last_detected_at);

-- Comments
COMMENT ON TABLE failure_patterns IS 'Stores detected failure patterns for trend analysis and machine learning';
COMMENT ON COLUMN failure_patterns.pattern_signature IS 'Computed signature for deduplication (hash of failure_type + error_type + context)';
COMMENT ON COLUMN failure_patterns.error_message_hash IS 'SHA256 hash of error message for fast matching';
COMMENT ON COLUMN failure_patterns.occurrence_count IS 'Number of times this pattern has been detected';

-- ================================================================================================
-- 2. RECOVERY ATTEMPTS TABLE  
-- ================================================================================================
-- Tracks all recovery attempts and their outcomes
CREATE TABLE IF NOT EXISTS recovery_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    
    -- Recovery details
    recovery_strategy TEXT NOT NULL,              -- RecoveryStrategy enum value
    failure_pattern_id UUID REFERENCES failure_patterns(id) ON DELETE SET NULL,
    
    -- Attempt information
    attempt_number INTEGER NOT NULL DEFAULT 1,
    triggered_by TEXT NOT NULL,                   -- 'failure_detection_engine', 'manual', 'system'
    recovery_reason TEXT,                         -- Why this recovery was chosen
    
    -- Execution tracking
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'in_progress',  -- 'in_progress', 'completed', 'failed', 'cancelled'
    
    -- Results
    success BOOLEAN,
    recovery_outcome TEXT,                        -- Description of outcome
    error_message TEXT,                          -- Error if recovery failed
    
    -- Metadata
    recovery_context JSONB DEFAULT '{}',         -- Context data used for recovery
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    estimated_resolution_time INTERVAL,
    actual_resolution_time INTERVAL,
    
    -- AI analysis
    confidence_score FLOAT,
    ai_reasoning TEXT,                           -- AI explanation for recovery choice
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    -- Constraints
    CONSTRAINT recovery_attempts_status_check CHECK (status IN ('in_progress', 'completed', 'failed', 'cancelled')),
    CONSTRAINT recovery_attempts_confidence_check CHECK (confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)),
    CONSTRAINT recovery_attempts_attempt_number_check CHECK (attempt_number > 0),
    CONSTRAINT recovery_attempts_completion_check CHECK (
        (status = 'in_progress' AND completed_at IS NULL) OR
        (status IN ('completed', 'failed', 'cancelled') AND completed_at IS NOT NULL)
    )
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_recovery_attempts_task_id ON recovery_attempts(task_id);
CREATE INDEX IF NOT EXISTS idx_recovery_attempts_workspace_id ON recovery_attempts(workspace_id);
CREATE INDEX IF NOT EXISTS idx_recovery_attempts_failure_pattern_id ON recovery_attempts(failure_pattern_id);
CREATE INDEX IF NOT EXISTS idx_recovery_attempts_status ON recovery_attempts(status);
CREATE INDEX IF NOT EXISTS idx_recovery_attempts_started_at ON recovery_attempts(started_at);
CREATE INDEX IF NOT EXISTS idx_recovery_attempts_strategy ON recovery_attempts(recovery_strategy);

-- Comments
COMMENT ON TABLE recovery_attempts IS 'Tracks all recovery attempts and their outcomes for learning and optimization';
COMMENT ON COLUMN recovery_attempts.attempt_number IS 'Sequential attempt number for this task (1, 2, 3...)';
COMMENT ON COLUMN recovery_attempts.triggered_by IS 'What triggered this recovery attempt';
COMMENT ON COLUMN recovery_attempts.ai_reasoning IS 'AI explanation for why this recovery strategy was chosen';

-- ================================================================================================
-- 3. RECOVERY EXPLANATIONS TABLE
-- ================================================================================================
-- Stores human-readable explanations of recovery decisions for transparency
CREATE TABLE IF NOT EXISTS recovery_explanations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    recovery_attempt_id UUID REFERENCES recovery_attempts(id) ON DELETE CASCADE,
    
    -- Core explanation
    failure_summary TEXT NOT NULL,
    root_cause TEXT NOT NULL,
    retry_decision TEXT NOT NULL,
    confidence_explanation TEXT NOT NULL,
    
    -- User-facing information  
    user_action_required TEXT,
    estimated_resolution_time TEXT,
    severity_level TEXT NOT NULL DEFAULT 'medium',
    display_category TEXT NOT NULL DEFAULT 'System Issue',
    
    -- Technical details
    technical_details JSONB DEFAULT '{}',
    error_pattern_matched TEXT,
    failure_category TEXT,
    recovery_strategy TEXT,
    
    -- Generation metadata
    ai_analysis_used BOOLEAN DEFAULT false,
    explanation_source TEXT DEFAULT 'recovery_explanation_engine',
    generation_model TEXT,                       -- Which AI model generated explanation
    generation_confidence FLOAT,
    
    -- Timestamps
    failure_time TIMESTAMPTZ NOT NULL DEFAULT now(),
    explanation_generated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    -- Constraints
    CONSTRAINT recovery_explanations_severity_check CHECK (severity_level IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT recovery_explanations_confidence_check CHECK (
        generation_confidence IS NULL OR (generation_confidence >= 0.0 AND generation_confidence <= 1.0)
    )
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_recovery_explanations_task_id ON recovery_explanations(task_id);
CREATE INDEX IF NOT EXISTS idx_recovery_explanations_workspace_id ON recovery_explanations(workspace_id);
CREATE INDEX IF NOT EXISTS idx_recovery_explanations_recovery_attempt_id ON recovery_explanations(recovery_attempt_id);
CREATE INDEX IF NOT EXISTS idx_recovery_explanations_severity ON recovery_explanations(severity_level);
CREATE INDEX IF NOT EXISTS idx_recovery_explanations_failure_time ON recovery_explanations(failure_time);

-- Comments
COMMENT ON TABLE recovery_explanations IS 'Human-readable explanations of recovery decisions for transparency and compliance';
COMMENT ON COLUMN recovery_explanations.failure_summary IS 'Brief summary of what went wrong';
COMMENT ON COLUMN recovery_explanations.root_cause IS 'Detailed root cause analysis';
COMMENT ON COLUMN recovery_explanations.retry_decision IS 'Explanation of retry/recovery decision';
COMMENT ON COLUMN recovery_explanations.user_action_required IS 'What action user needs to take (if any)';

-- ================================================================================================
-- 4. UPDATE EXISTING TABLES - ADD RECOVERY FIELDS
-- ================================================================================================

-- Add recovery tracking to tasks table (if not already exists)
DO $$ 
BEGIN 
    -- Add recovery_count if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tasks' 
        AND column_name = 'recovery_count'
        AND table_schema = current_schema()
    ) THEN
        ALTER TABLE tasks ADD COLUMN recovery_count INTEGER DEFAULT 0;
    END IF;
    
    -- Add last_failure_type if it doesn't exist  
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tasks' 
        AND column_name = 'last_failure_type'
        AND table_schema = current_schema()
    ) THEN
        ALTER TABLE tasks ADD COLUMN last_failure_type TEXT;
    END IF;
    
    -- Add last_recovery_attempt_at if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tasks' 
        AND column_name = 'last_recovery_attempt_at'
        AND table_schema = current_schema()
    ) THEN
        ALTER TABLE tasks ADD COLUMN last_recovery_attempt_at TIMESTAMPTZ;
    END IF;
    
    -- Add auto_recovery_enabled flag if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tasks' 
        AND column_name = 'auto_recovery_enabled'
        AND table_schema = current_schema()
    ) THEN
        ALTER TABLE tasks ADD COLUMN auto_recovery_enabled BOOLEAN DEFAULT true;
    END IF;
END $$;

-- Add recovery metrics to workspaces table (if not already exists)
DO $$ 
BEGIN 
    -- Add workspace-level recovery tracking
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workspaces' 
        AND column_name = 'total_recovery_attempts'
        AND table_schema = current_schema()
    ) THEN
        ALTER TABLE workspaces ADD COLUMN total_recovery_attempts INTEGER DEFAULT 0;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workspaces' 
        AND column_name = 'successful_recoveries'
        AND table_schema = current_schema()
    ) THEN
        ALTER TABLE workspaces ADD COLUMN successful_recoveries INTEGER DEFAULT 0;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workspaces' 
        AND column_name = 'last_recovery_check_at'
        AND table_schema = current_schema()
    ) THEN
        ALTER TABLE workspaces ADD COLUMN last_recovery_check_at TIMESTAMPTZ;
    END IF;
END $$;

-- Add indexes for new fields
CREATE INDEX IF NOT EXISTS idx_tasks_recovery_count ON tasks(recovery_count);
CREATE INDEX IF NOT EXISTS idx_tasks_last_failure_type ON tasks(last_failure_type);
CREATE INDEX IF NOT EXISTS idx_tasks_last_recovery_attempt_at ON tasks(last_recovery_attempt_at);
CREATE INDEX IF NOT EXISTS idx_tasks_auto_recovery_enabled ON tasks(auto_recovery_enabled);

-- ================================================================================================
-- 5. TRIGGERS FOR AUTOMATIC UPDATES
-- ================================================================================================

-- Trigger to update updated_at on all new tables
CREATE TRIGGER update_failure_patterns_updated_at
    BEFORE UPDATE ON failure_patterns
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_recovery_attempts_updated_at
    BEFORE UPDATE ON recovery_attempts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_recovery_explanations_updated_at
    BEFORE UPDATE ON recovery_explanations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger to update workspace recovery metrics when recovery attempts change
CREATE OR REPLACE FUNCTION update_workspace_recovery_metrics()
RETURNS TRIGGER AS $$
BEGIN
    -- Update workspace metrics when recovery attempt is completed
    IF (TG_OP = 'INSERT' AND NEW.status IN ('completed', 'failed')) OR 
       (TG_OP = 'UPDATE' AND OLD.status = 'in_progress' AND NEW.status IN ('completed', 'failed')) THEN
        
        UPDATE workspaces 
        SET 
            total_recovery_attempts = (
                SELECT COUNT(*) 
                FROM recovery_attempts 
                WHERE workspace_id = NEW.workspace_id 
                AND status IN ('completed', 'failed')
            ),
            successful_recoveries = (
                SELECT COUNT(*) 
                FROM recovery_attempts 
                WHERE workspace_id = NEW.workspace_id 
                AND status = 'completed' 
                AND success = true
            ),
            last_recovery_check_at = now(),
            updated_at = now()
        WHERE id = NEW.workspace_id;
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_workspace_recovery_metrics
    AFTER INSERT OR UPDATE ON recovery_attempts
    FOR EACH ROW
    EXECUTE FUNCTION update_workspace_recovery_metrics();

-- ================================================================================================
-- 6. DATA RETENTION POLICIES
-- ================================================================================================

-- Function to cleanup old recovery data (retention policy)
CREATE OR REPLACE FUNCTION cleanup_old_recovery_data(retention_days INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
BEGIN
    -- Delete old failure patterns (keep only recent ones for learning)
    DELETE FROM failure_patterns 
    WHERE last_detected_at < now() - INTERVAL '1 day' * retention_days
    AND occurrence_count = 1; -- Keep frequently occurring patterns longer
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Delete old recovery explanations  
    DELETE FROM recovery_explanations 
    WHERE explanation_generated_at < now() - INTERVAL '1 day' * retention_days;
    
    -- Delete old completed recovery attempts (keep failed ones longer for analysis)
    DELETE FROM recovery_attempts 
    WHERE completed_at < now() - INTERVAL '1 day' * retention_days
    AND status = 'completed' 
    AND success = true;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Comments for retention
COMMENT ON FUNCTION cleanup_old_recovery_data IS 'Cleanup old recovery data based on retention policy (default 90 days)';

-- ================================================================================================
-- 7. UTILITY FUNCTIONS
-- ================================================================================================

-- Function to get recovery statistics for a workspace
CREATE OR REPLACE FUNCTION get_workspace_recovery_stats(p_workspace_id UUID)
RETURNS TABLE (
    total_recovery_attempts BIGINT,
    successful_recoveries BIGINT,
    failure_patterns_count BIGINT,
    most_common_failure_type TEXT,
    recovery_success_rate FLOAT,
    avg_resolution_time INTERVAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(DISTINCT ra.id) as total_recovery_attempts,
        COUNT(DISTINCT CASE WHEN ra.success = true THEN ra.id END) as successful_recoveries,
        COUNT(DISTINCT fp.id) as failure_patterns_count,
        (
            SELECT fp2.failure_type 
            FROM failure_patterns fp2 
            WHERE fp2.workspace_id = p_workspace_id 
            ORDER BY fp2.occurrence_count DESC 
            LIMIT 1
        ) as most_common_failure_type,
        CASE 
            WHEN COUNT(DISTINCT ra.id) > 0 THEN 
                COUNT(DISTINCT CASE WHEN ra.success = true THEN ra.id END)::FLOAT / COUNT(DISTINCT ra.id)::FLOAT
            ELSE 0.0 
        END as recovery_success_rate,
        AVG(ra.actual_resolution_time) as avg_resolution_time
    FROM recovery_attempts ra
    LEFT JOIN failure_patterns fp ON fp.workspace_id = p_workspace_id
    WHERE ra.workspace_id = p_workspace_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_workspace_recovery_stats IS 'Get comprehensive recovery statistics for a workspace';

-- ================================================================================================
-- MIGRATION COMPLETE
-- ================================================================================================

-- Log successful migration
INSERT INTO execution_logs (
    id, workspace_id, agent_id, task_id, type, content, created_at
) VALUES (
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000000000',  -- System workspace
    NULL,
    NULL,
    'MIGRATION',
    jsonb_build_object(
        'migration_id', '009',
        'migration_name', 'add_recovery_system_tables',
        'status', 'completed',
        'tables_created', ARRAY['failure_patterns', 'recovery_attempts', 'recovery_explanations'],
        'columns_added', ARRAY['tasks.recovery_count', 'tasks.last_failure_type', 'tasks.auto_recovery_enabled', 'workspaces.total_recovery_attempts'],
        'indexes_created', 15,
        'triggers_created', 4,
        'functions_created', 3
    ),
    now()
);

-- ================================================================================================
-- VERIFICATION QUERIES (for testing)
-- ================================================================================================

-- Verify tables were created
SELECT schemaname, tablename, tableowner 
FROM pg_tables 
WHERE tablename IN ('failure_patterns', 'recovery_attempts', 'recovery_explanations')
AND schemaname = current_schema();

-- Verify columns were added to existing tables
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name IN ('tasks', 'workspaces')
AND column_name IN ('recovery_count', 'last_failure_type', 'auto_recovery_enabled', 'total_recovery_attempts')
AND table_schema = current_schema();

-- Verify indexes were created
SELECT indexname, tablename 
FROM pg_indexes 
WHERE tablename IN ('failure_patterns', 'recovery_attempts', 'recovery_explanations', 'tasks', 'workspaces')
AND indexname LIKE '%recovery%'
AND schemaname = current_schema();