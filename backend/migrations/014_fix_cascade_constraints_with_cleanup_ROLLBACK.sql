-- =============================================================================
-- 🔄 Migration 014 ROLLBACK: Revert CASCADE DELETE Constraints and Schema Changes
-- =============================================================================
-- Rollback script for migration 014_fix_cascade_constraints_with_cleanup.sql
-- 
-- WARNING: This rollback will:
-- 1. Remove CASCADE DELETE constraints (data will remain)
-- 2. Revert workspace_insights schema changes
-- 3. Remove auto-generated knowledge insights
-- 
-- NOTE: Orphaned data cleanup cannot be rolled back (data is permanently deleted)
-- =============================================================================

-- =============================================================================
-- ✅ STEP 1: Remove CASCADE DELETE Constraints
-- =============================================================================

-- Remove CASCADE constraint from memory_context_entries
DO $$
BEGIN
    -- Drop CASCADE constraint
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'memory_context_entries'
        AND constraint_name = 'memory_context_entries_workspace_cascade'
    ) THEN
        ALTER TABLE memory_context_entries 
        DROP CONSTRAINT memory_context_entries_workspace_cascade;
        RAISE NOTICE '🔧 REMOVED CASCADE constraint: memory_context_entries_workspace_cascade';
    END IF;
    
    -- Add back regular foreign key constraint (without CASCADE)
    ALTER TABLE memory_context_entries
    ADD CONSTRAINT memory_context_entries_workspace_id_fkey
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id);
    
    RAISE NOTICE '✅ RESTORED regular FK constraint: memory_context_entries_workspace_id_fkey';
    
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION '❌ ERROR removing CASCADE constraint from memory_context_entries: %', SQLERRM;
END $$;

-- Remove CASCADE constraint from uma_performance_metrics
DO $$
BEGIN
    -- Drop CASCADE constraint
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'uma_performance_metrics'
        AND constraint_name = 'uma_performance_metrics_workspace_cascade'
    ) THEN
        ALTER TABLE uma_performance_metrics 
        DROP CONSTRAINT uma_performance_metrics_workspace_cascade;
        RAISE NOTICE '🔧 REMOVED CASCADE constraint: uma_performance_metrics_workspace_cascade';
    END IF;
    
    -- Add back regular foreign key constraint (without CASCADE)
    ALTER TABLE uma_performance_metrics
    ADD CONSTRAINT uma_performance_metrics_workspace_id_fkey
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id);
    
    RAISE NOTICE '✅ RESTORED regular FK constraint: uma_performance_metrics_workspace_id_fkey';
    
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION '❌ ERROR removing CASCADE constraint from uma_performance_metrics: %', SQLERRM;
END $$;

-- =============================================================================
-- ✅ STEP 2: Remove Auto-Generated Knowledge Insights
-- =============================================================================

-- Remove auto-generated insights for target workspace
DO $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM workspace_insights 
    WHERE workspace_id = '1f1bf9cf-3c46-48ed-96f3-ec826742ee02'
    AND metadata->>'auto_generated' = 'true';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RAISE NOTICE '🧹 REMOVED % auto-generated knowledge insights', deleted_count;
END $$;

-- =============================================================================
-- ✅ STEP 3: Revert workspace_insights Schema Changes
-- =============================================================================

-- Remove columns added in migration 014
-- Note: This may fail if the columns are in use or have data
-- In production, consider keeping the columns but marking them as deprecated

DO $$
BEGIN
    -- Remove task_id column
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workspace_insights' AND column_name = 'task_id'
    ) THEN
        ALTER TABLE workspace_insights DROP COLUMN IF EXISTS task_id;
        RAISE NOTICE '🔧 REMOVED column: workspace_insights.task_id';
    END IF;
    
    -- Remove agent_role column (check if it has non-default values first)
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workspace_insights' AND column_name = 'agent_role'
    ) THEN
        -- Only remove if all values are default
        IF NOT EXISTS (
            SELECT 1 FROM workspace_insights 
            WHERE agent_role IS NOT NULL AND agent_role != 'system'
        ) THEN
            ALTER TABLE workspace_insights DROP COLUMN agent_role;
            RAISE NOTICE '🔧 REMOVED column: workspace_insights.agent_role';
        ELSE
            RAISE NOTICE '⚠️  KEEPING column: workspace_insights.agent_role (contains non-default data)';
        END IF;
    END IF;
    
    -- Remove relevance_tags column
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workspace_insights' AND column_name = 'relevance_tags'
    ) THEN
        ALTER TABLE workspace_insights DROP COLUMN IF EXISTS relevance_tags;
        RAISE NOTICE '🔧 REMOVED column: workspace_insights.relevance_tags';
    END IF;
    
    -- Remove confidence_score column
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workspace_insights' AND column_name = 'confidence_score'
    ) THEN
        ALTER TABLE workspace_insights DROP COLUMN IF EXISTS confidence_score;
        RAISE NOTICE '🔧 REMOVED column: workspace_insights.confidence_score';
    END IF;
    
    -- Remove expires_at column
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workspace_insights' AND column_name = 'expires_at'
    ) THEN
        ALTER TABLE workspace_insights DROP COLUMN IF EXISTS expires_at;
        RAISE NOTICE '🔧 REMOVED column: workspace_insights.expires_at';
    END IF;
    
    -- Remove metadata column (check if it has non-default values first)
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workspace_insights' AND column_name = 'metadata'
    ) THEN
        -- Only remove if all values are default
        IF NOT EXISTS (
            SELECT 1 FROM workspace_insights 
            WHERE metadata IS NOT NULL AND metadata != '{}'::jsonb
        ) THEN
            ALTER TABLE workspace_insights DROP COLUMN metadata;
            RAISE NOTICE '🔧 REMOVED column: workspace_insights.metadata';
        ELSE
            RAISE NOTICE '⚠️  KEEPING column: workspace_insights.metadata (contains non-default data)';
        END IF;
    END IF;
    
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '⚠️  ERROR reverting workspace_insights schema: % (some columns may have been kept)', SQLERRM;
END $$;

-- =============================================================================
-- ✅ STEP 4: Validation
-- =============================================================================

-- Verify CASCADE constraints are removed
DO $$
DECLARE
    mce_cascade_exists BOOLEAN;
    upm_cascade_exists BOOLEAN;
    mce_regular_exists BOOLEAN;
    upm_regular_exists BOOLEAN;
BEGIN
    -- Check CASCADE constraints are gone
    SELECT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'memory_context_entries'
        AND constraint_name = 'memory_context_entries_workspace_cascade'
    ) INTO mce_cascade_exists;
    
    SELECT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'uma_performance_metrics'
        AND constraint_name = 'uma_performance_metrics_workspace_cascade'
    ) INTO upm_cascade_exists;
    
    -- Check regular FK constraints exist
    SELECT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'memory_context_entries'
        AND constraint_name = 'memory_context_entries_workspace_id_fkey'
    ) INTO mce_regular_exists;
    
    SELECT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'uma_performance_metrics'
        AND constraint_name = 'uma_performance_metrics_workspace_id_fkey'
    ) INTO upm_regular_exists;
    
    -- Report results
    IF NOT mce_cascade_exists AND mce_regular_exists THEN
        RAISE NOTICE '✅ VERIFIED: memory_context_entries CASCADE removed, regular FK restored';
    ELSE
        RAISE NOTICE '⚠️  WARNING: memory_context_entries constraint state unexpected';
    END IF;
    
    IF NOT ump_cascade_exists AND upm_regular_exists THEN
        RAISE NOTICE '✅ VERIFIED: uma_performance_metrics CASCADE removed, regular FK restored';
    ELSE
        RAISE NOTICE '⚠️  WARNING: uma_performance_metrics constraint state unexpected';
    END IF;
END $$;

-- Check remaining insights
DO $$
DECLARE
    insights_remaining INTEGER;
BEGIN
    SELECT COUNT(*) INTO insights_remaining
    FROM workspace_insights 
    WHERE workspace_id = '1f1bf9cf-3c46-48ed-96f3-ec826742ee02';
    
    RAISE NOTICE '📊 REMAINING insights for target workspace: %', insights_remaining;
END $$;

-- Final rollback completion message
DO $$
BEGIN
    RAISE NOTICE '🔄 MIGRATION 014 ROLLBACK COMPLETED!';
    RAISE NOTICE '✅ CASCADE DELETE constraints removed';
    RAISE NOTICE '✅ Regular FK constraints restored';
    RAISE NOTICE '✅ Auto-generated knowledge insights removed';
    RAISE NOTICE '⚠️  Schema changes partially reverted (some columns may be kept if they contain data)';
    RAISE NOTICE '❗ NOTE: Orphaned data cleanup cannot be rolled back (data is permanently deleted)';
END $$;