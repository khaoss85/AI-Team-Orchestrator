-- ================================================================================================
-- ROLLBACK MIGRATION 009: REMOVE RECOVERY SYSTEM TABLES
-- ================================================================================================
-- Purpose: Rollback the recovery system database schema changes
-- Date: 2025-08-26
-- Author: AI-Team-Orchestrator Auto-Recovery System
-- ================================================================================================

-- WARNING: This will permanently delete all recovery data!
-- Make sure to backup the database before running this rollback.

-- ================================================================================================
-- 1. DROP UTILITY FUNCTIONS
-- ================================================================================================

DROP FUNCTION IF EXISTS get_workspace_recovery_stats(UUID);
DROP FUNCTION IF EXISTS cleanup_old_recovery_data(INTEGER);

-- ================================================================================================
-- 2. DROP TRIGGERS
-- ================================================================================================

DROP TRIGGER IF EXISTS trigger_update_workspace_recovery_metrics ON recovery_attempts;
DROP TRIGGER IF EXISTS update_recovery_explanations_updated_at ON recovery_explanations;
DROP TRIGGER IF EXISTS update_recovery_attempts_updated_at ON recovery_attempts;
DROP TRIGGER IF EXISTS update_failure_patterns_updated_at ON failure_patterns;

-- ================================================================================================
-- 3. DROP TRIGGER FUNCTIONS  
-- ================================================================================================

DROP FUNCTION IF EXISTS update_workspace_recovery_metrics();

-- ================================================================================================
-- 4. REMOVE COLUMNS FROM EXISTING TABLES
-- ================================================================================================

-- Remove recovery-related columns from tasks table
DO $$ 
BEGIN 
    -- Remove recovery_count if it exists
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tasks' 
        AND column_name = 'recovery_count'
        AND table_schema = current_schema()
    ) THEN
        ALTER TABLE tasks DROP COLUMN recovery_count;
    END IF;
    
    -- Remove last_failure_type if it exists
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tasks' 
        AND column_name = 'last_failure_type'
        AND table_schema = current_schema()
    ) THEN
        ALTER TABLE tasks DROP COLUMN last_failure_type;
    END IF;
    
    -- Remove last_recovery_attempt_at if it exists
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tasks' 
        AND column_name = 'last_recovery_attempt_at'
        AND table_schema = current_schema()
    ) THEN
        ALTER TABLE tasks DROP COLUMN last_recovery_attempt_at;
    END IF;
    
    -- Remove auto_recovery_enabled if it exists
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tasks' 
        AND column_name = 'auto_recovery_enabled'
        AND table_schema = current_schema()
    ) THEN
        ALTER TABLE tasks DROP COLUMN auto_recovery_enabled;
    END IF;
END $$;

-- Remove recovery metrics from workspaces table
DO $$ 
BEGIN 
    -- Remove total_recovery_attempts if it exists
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workspaces' 
        AND column_name = 'total_recovery_attempts'
        AND table_schema = current_schema()
    ) THEN
        ALTER TABLE workspaces DROP COLUMN total_recovery_attempts;
    END IF;
    
    -- Remove successful_recoveries if it exists
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workspaces' 
        AND column_name = 'successful_recoveries'
        AND table_schema = current_schema()
    ) THEN
        ALTER TABLE workspaces DROP COLUMN successful_recoveries;
    END IF;
    
    -- Remove last_recovery_check_at if it exists
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workspaces' 
        AND column_name = 'last_recovery_check_at'
        AND table_schema = current_schema()
    ) THEN
        ALTER TABLE workspaces DROP COLUMN last_recovery_check_at;
    END IF;
END $$;

-- ================================================================================================
-- 5. DROP NEW TABLES (in reverse dependency order)
-- ================================================================================================

-- Drop recovery_explanations table (references recovery_attempts)
DROP TABLE IF EXISTS recovery_explanations;

-- Drop recovery_attempts table (references failure_patterns)
DROP TABLE IF EXISTS recovery_attempts;

-- Drop failure_patterns table (base table)
DROP TABLE IF EXISTS failure_patterns;

-- ================================================================================================
-- 6. CLEANUP MIGRATION LOG
-- ================================================================================================

-- Remove the migration log entry
DELETE FROM execution_logs 
WHERE type = 'MIGRATION' 
AND content->>'migration_id' = '009' 
AND content->>'migration_name' = 'add_recovery_system_tables';

-- ================================================================================================
-- ROLLBACK COMPLETE
-- ================================================================================================

-- Log successful rollback
INSERT INTO execution_logs (
    id, workspace_id, agent_id, task_id, type, content, created_at
) VALUES (
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000000000',  -- System workspace
    NULL,
    NULL,
    'MIGRATION_ROLLBACK',
    jsonb_build_object(
        'migration_id', '009',
        'migration_name', 'add_recovery_system_tables',
        'status', 'rolled_back',
        'tables_dropped', ARRAY['failure_patterns', 'recovery_attempts', 'recovery_explanations'],
        'columns_removed', ARRAY['tasks.recovery_count', 'tasks.last_failure_type', 'tasks.auto_recovery_enabled', 'workspaces.total_recovery_attempts'],
        'functions_dropped', 3,
        'triggers_dropped', 4
    ),
    now()
);

-- ================================================================================================
-- VERIFICATION QUERIES (for testing rollback)
-- ================================================================================================

-- Verify tables were dropped
SELECT COUNT(*) as remaining_recovery_tables
FROM pg_tables 
WHERE tablename IN ('failure_patterns', 'recovery_attempts', 'recovery_explanations')
AND schemaname = current_schema();

-- Verify columns were removed from existing tables  
SELECT COUNT(*) as remaining_recovery_columns
FROM information_schema.columns
WHERE table_name IN ('tasks', 'workspaces')
AND column_name IN ('recovery_count', 'last_failure_type', 'auto_recovery_enabled', 'total_recovery_attempts')
AND table_schema = current_schema();

-- Should return 0 for both queries if rollback was successful