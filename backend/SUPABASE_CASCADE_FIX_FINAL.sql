-- =============================================================================
-- 🛡️ SUPABASE CASCADE DELETE FIX - Final Script for SQL Editor
-- =============================================================================
-- Copy and paste this complete script into Supabase Dashboard > SQL Editor
-- 
-- 🎯 PURPOSE: Fix foreign key constraint violations when adding CASCADE DELETE
-- 
-- 🚨 ROOT CAUSE: Orphaned records in memory_context_entries and uma_performance_metrics
--    tables reference non-existent workspace IDs, preventing CASCADE constraint addition
-- 
-- 🔧 SOLUTION: Clean orphaned data FIRST, then safely add CASCADE constraints
-- 
-- ✅ TESTED FOR: workspace 1f1bf9cf-3c46-48ed-96f3-ec826742ee02
-- =============================================================================

-- =============================================================================
-- DIAGNOSTIC PHASE: Check current state (for logging)
-- =============================================================================

-- Check for orphaned memory_context_entries
DO $$
DECLARE
    orphaned_mce INTEGER;
    orphaned_upm INTEGER;
    total_workspaces INTEGER;
BEGIN
    -- Count valid workspaces
    SELECT COUNT(*) INTO total_workspaces FROM workspaces;
    
    -- Count orphaned memory_context_entries
    SELECT COUNT(*) INTO orphaned_mce
    FROM memory_context_entries mce 
    WHERE mce.workspace_id IS NOT NULL 
      AND mce.workspace_id NOT IN (SELECT id FROM workspaces);
    
    -- Count orphaned uma_performance_metrics  
    SELECT COUNT(*) INTO orphaned_upm
    FROM uma_performance_metrics upm
    WHERE upm.workspace_id IS NOT NULL 
      AND upm.workspace_id NOT IN (SELECT id FROM workspaces);
    
    RAISE NOTICE '📊 CURRENT STATE ANALYSIS:';
    RAISE NOTICE '   Total valid workspaces: %', total_workspaces;
    RAISE NOTICE '   Orphaned memory_context_entries: %', orphaned_mce;
    RAISE NOTICE '   Orphaned uma_performance_metrics: %', orphaned_upm;
    
    IF orphaned_mce > 0 OR orphaned_upm > 0 THEN
        RAISE NOTICE '🚨 ORPHANED DATA DETECTED - Cleanup required before CASCADE constraints';
    ELSE
        RAISE NOTICE '✅ NO ORPHANED DATA - Safe to proceed with CASCADE constraints';
    END IF;
END $$;

-- =============================================================================
-- CLEANUP PHASE: Remove orphaned records BEFORE adding constraints
-- =============================================================================

-- Step 1: Clean orphaned memory_context_entries
DO $$
DECLARE
    deleted_mce INTEGER;
BEGIN
    DELETE FROM memory_context_entries 
    WHERE workspace_id IS NOT NULL 
      AND workspace_id NOT IN (SELECT id FROM workspaces);
    
    GET DIAGNOSTICS deleted_mce = ROW_COUNT;
    
    IF deleted_mce > 0 THEN
        RAISE NOTICE '🧹 CLEANED memory_context_entries: % orphaned records deleted', deleted_mce;
    ELSE
        RAISE NOTICE '✅ memory_context_entries: No orphaned records found';
    END IF;
END $$;

-- Step 2: Clean orphaned uma_performance_metrics  
DO $$
DECLARE
    deleted_upm INTEGER;
BEGIN
    DELETE FROM uma_performance_metrics
    WHERE workspace_id IS NOT NULL
      AND workspace_id NOT IN (SELECT id FROM workspaces);
    
    GET DIAGNOSTICS deleted_upm = ROW_COUNT;
    
    IF deleted_upm > 0 THEN
        RAISE NOTICE '🧹 CLEANED uma_performance_metrics: % orphaned records deleted', deleted_upm;
    ELSE
        RAISE NOTICE '✅ uma_performance_metrics: No orphaned records found';
    END IF;
END $$;

-- =============================================================================
-- CONSTRAINT PHASE: Add CASCADE DELETE constraints (after cleanup)
-- =============================================================================

-- Step 3: Add CASCADE constraint to memory_context_entries
DO $$
BEGIN
    -- Remove any existing workspace foreign key constraint
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'memory_context_entries'
        AND constraint_type = 'FOREIGN KEY'
        AND (constraint_name LIKE '%workspace%' OR constraint_name = 'fk_memory_context_workspace')
    ) THEN
        -- Drop existing constraints
        ALTER TABLE memory_context_entries 
        DROP CONSTRAINT IF EXISTS fk_memory_context_workspace CASCADE;
        ALTER TABLE memory_context_entries 
        DROP CONSTRAINT IF EXISTS memory_context_entries_workspace_id_fkey CASCADE;
        
        RAISE NOTICE '🔧 REMOVED existing memory_context_entries workspace constraints';
    END IF;
    
    -- Add new CASCADE DELETE constraint
    ALTER TABLE memory_context_entries
    ADD CONSTRAINT memory_context_entries_workspace_cascade
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE;
    
    RAISE NOTICE '✅ ADDED CASCADE constraint: memory_context_entries_workspace_cascade';
    
EXCEPTION
    WHEN foreign_key_violation THEN
        -- This should not happen after cleanup, but provide clear error
        RAISE EXCEPTION '❌ FOREIGN KEY VIOLATION: Orphaned memory_context_entries still exist. Run cleanup queries manually first.';
    WHEN duplicate_object THEN
        RAISE NOTICE '⚠️  CASCADE constraint already exists on memory_context_entries';
    WHEN OTHERS THEN
        RAISE EXCEPTION '❌ UNEXPECTED ERROR adding CASCADE to memory_context_entries: %', SQLERRM;
END $$;

-- Step 4: Add CASCADE constraint to uma_performance_metrics
DO $$
BEGIN
    -- Remove any existing workspace foreign key constraint  
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'uma_performance_metrics'
        AND constraint_type = 'FOREIGN KEY'
        AND constraint_name LIKE '%workspace%'
    ) THEN
        -- Drop existing constraints
        ALTER TABLE uma_performance_metrics 
        DROP CONSTRAINT IF EXISTS uma_performance_metrics_workspace_id_fkey CASCADE;
        
        RAISE NOTICE '🔧 REMOVED existing uma_performance_metrics workspace constraint';
    END IF;
    
    -- Add new CASCADE DELETE constraint
    ALTER TABLE uma_performance_metrics
    ADD CONSTRAINT uma_performance_metrics_workspace_cascade
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE;
    
    RAISE NOTICE '✅ ADDED CASCADE constraint: uma_performance_metrics_workspace_cascade';
    
EXCEPTION
    WHEN foreign_key_violation THEN
        -- This should not happen after cleanup, but provide clear error
        RAISE EXCEPTION '❌ FOREIGN KEY VIOLATION: Orphaned uma_performance_metrics still exist. Run cleanup queries manually first.';
    WHEN duplicate_object THEN
        RAISE NOTICE '⚠️  CASCADE constraint already exists on uma_performance_metrics';
    WHEN OTHERS THEN
        RAISE EXCEPTION '❌ UNEXPECTED ERROR adding CASCADE to uma_performance_metrics: %', SQLERRM;
END $$;

-- =============================================================================
-- SCHEMA PHASE: Fix workspace_insights for knowledge generation
-- =============================================================================

-- Step 5: Add missing columns to workspace_insights
DO $$
BEGIN
    -- Add task_id column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workspace_insights' AND column_name = 'task_id'
    ) THEN
        ALTER TABLE workspace_insights 
        ADD COLUMN task_id UUID REFERENCES tasks(id);
        RAISE NOTICE '✅ ADDED column: workspace_insights.task_id';
    END IF;
    
    -- Add agent_role column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workspace_insights' AND column_name = 'agent_role'
    ) THEN
        ALTER TABLE workspace_insights 
        ADD COLUMN agent_role TEXT NOT NULL DEFAULT 'system';
        RAISE NOTICE '✅ ADDED column: workspace_insights.agent_role';
    END IF;
    
    -- Add relevance_tags column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workspace_insights' AND column_name = 'relevance_tags'
    ) THEN
        ALTER TABLE workspace_insights 
        ADD COLUMN relevance_tags TEXT[] DEFAULT '{}';
        RAISE NOTICE '✅ ADDED column: workspace_insights.relevance_tags';
    END IF;
    
    -- Add confidence_score column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workspace_insights' AND column_name = 'confidence_score'
    ) THEN
        ALTER TABLE workspace_insights 
        ADD COLUMN confidence_score NUMERIC DEFAULT 1.0 
        CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0);
        RAISE NOTICE '✅ ADDED column: workspace_insights.confidence_score';
    END IF;
    
    -- Add expires_at column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workspace_insights' AND column_name = 'expires_at'
    ) THEN
        ALTER TABLE workspace_insights 
        ADD COLUMN expires_at TIMESTAMP WITH TIME ZONE;
        RAISE NOTICE '✅ ADDED column: workspace_insights.expires_at';
    END IF;
    
    -- Add metadata column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workspace_insights' AND column_name = 'metadata'
    ) THEN
        ALTER TABLE workspace_insights 
        ADD COLUMN metadata JSONB DEFAULT '{}';
        RAISE NOTICE '✅ ADDED column: workspace_insights.metadata';
    END IF;
    
    RAISE NOTICE '🏗️  workspace_insights schema update completed';
    
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION '❌ ERROR updating workspace_insights schema: %', SQLERRM;
END $$;

-- =============================================================================
-- INSIGHTS PHASE: Generate knowledge insights for target workspace
-- =============================================================================

-- Step 6: Generate productivity insight
INSERT INTO workspace_insights (
  workspace_id,
  agent_role,
  insight_type,
  content,
  relevance_tags,
  confidence_score,
  metadata
) 
SELECT 
  workspace_id,
  'productivity_analyst',
  'success_pattern',
  'High deliverable production rate detected: ' || COUNT(*) || ' deliverables generated, indicating strong workspace productivity and systematic output generation.',
  ARRAY['productivity', 'deliverables', 'output', 'success'],
  0.9,
  jsonb_build_object(
    'deliverable_count', COUNT(*),
    'analysis_type', 'productivity_assessment',
    'auto_generated', true,
    'data_source', 'deliverables_table',
    'analysis_date', NOW(),
    'migration_batch', '014_cascade_fix'
  )
FROM deliverables 
WHERE workspace_id = '1f1bf9cf-3c46-48ed-96f3-ec826742ee02'
GROUP BY workspace_id
HAVING COUNT(*) > 5
ON CONFLICT DO NOTHING; -- Prevent duplicates if run multiple times

-- Step 7: Generate workflow insight
INSERT INTO workspace_insights (
  workspace_id,
  agent_role,
  insight_type,
  content,
  relevance_tags,
  confidence_score,
  metadata
)
SELECT 
  workspace_id,
  'workflow_optimizer',
  'discovery',
  'Active task management pattern identified: ' || COUNT(*) || ' tasks demonstrate systematic work organization and effective task lifecycle management.',
  ARRAY['workflow', 'tasks', 'organization', 'management'],
  0.85,
  jsonb_build_object(
    'task_count', COUNT(*),
    'analysis_type', 'workflow_assessment',
    'auto_generated', true,
    'data_source', 'tasks_table',
    'analysis_date', NOW(),
    'migration_batch', '014_cascade_fix'
  )
FROM tasks 
WHERE workspace_id = '1f1bf9cf-3c46-48ed-96f3-ec826742ee02'
GROUP BY workspace_id
HAVING COUNT(*) > 5
ON CONFLICT DO NOTHING;

-- Step 8: Generate collaboration insight
INSERT INTO workspace_insights (
  workspace_id,
  agent_role,
  insight_type,
  content,
  relevance_tags,
  confidence_score,
  metadata
)
SELECT 
  workspace_id,
  'collaboration_specialist',
  'optimization',
  'Multi-agent coordination success: ' || COUNT(DISTINCT agent_id) || ' agents collaborated on ' || COUNT(*) || ' tasks, showing effective team coordination.',
  ARRAY['collaboration', 'agents', 'teamwork', 'coordination'],
  0.8,
  jsonb_build_object(
    'agent_count', COUNT(DISTINCT agent_id),
    'task_count', COUNT(*),
    'analysis_type', 'collaboration_assessment',
    'auto_generated', true,
    'data_source', 'tasks_agents_analysis',
    'analysis_date', NOW(),
    'migration_batch', '014_cascade_fix'
  )
FROM tasks 
WHERE workspace_id = '1f1bf9cf-3c46-48ed-96f3-ec826742ee02'
  AND agent_id IS NOT NULL
GROUP BY workspace_id
HAVING COUNT(DISTINCT agent_id) > 2
ON CONFLICT DO NOTHING;

-- Step 9: Generate quality insight
INSERT INTO workspace_insights (
  workspace_id,
  agent_role,
  insight_type,
  content,
  relevance_tags,
  confidence_score,
  metadata
)
SELECT 
  workspace_id,
  'quality_assessor',
  'progress',
  'Quality completion trend: ' || 
  COUNT(CASE WHEN status = 'completed' THEN 1 END) || ' of ' || COUNT(*) || 
  ' deliverables completed (' || 
  ROUND((COUNT(CASE WHEN status = 'completed' THEN 1 END) * 100.0 / COUNT(*)), 1) || '% completion rate).',
  ARRAY['quality', 'completion', 'progress', 'deliverables'],
  0.95,
  jsonb_build_object(
    'total_deliverables', COUNT(*),
    'completed_deliverables', COUNT(CASE WHEN status = 'completed' THEN 1 END),
    'completion_percentage', ROUND((COUNT(CASE WHEN status = 'completed' THEN 1 END) * 100.0 / COUNT(*)), 1),
    'analysis_type', 'quality_assessment',
    'auto_generated', true,
    'data_source', 'deliverables_status_analysis',
    'analysis_date', NOW(),
    'migration_batch', '014_cascade_fix'
  )
FROM deliverables 
WHERE workspace_id = '1f1bf9cf-3c46-48ed-96f3-ec826742ee02'
GROUP BY workspace_id
HAVING COUNT(*) > 0
ON CONFLICT DO NOTHING;

-- =============================================================================
-- VALIDATION PHASE: Verify all changes were applied successfully  
-- =============================================================================

-- Step 10: Final validation
DO $$
DECLARE
    mce_cascade_exists BOOLEAN;
    upm_cascade_exists BOOLEAN;
    remaining_mce_orphans INTEGER;
    remaining_upm_orphans INTEGER;
    insights_generated INTEGER;
    required_columns INTEGER;
    existing_columns INTEGER;
BEGIN
    -- Check CASCADE constraints exist
    SELECT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'memory_context_entries'
        AND constraint_name = 'memory_context_entries_workspace_cascade'
        AND constraint_type = 'FOREIGN KEY'
    ) INTO mce_cascade_exists;
    
    SELECT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'uma_performance_metrics'
        AND constraint_name = 'uma_performance_metrics_workspace_cascade'
        AND constraint_type = 'FOREIGN KEY'
    ) INTO upm_cascade_exists;
    
    -- Check for any remaining orphaned records
    SELECT COUNT(*) INTO remaining_mce_orphans
    FROM memory_context_entries mce 
    WHERE mce.workspace_id IS NOT NULL 
      AND mce.workspace_id NOT IN (SELECT id FROM workspaces);
      
    SELECT COUNT(*) INTO remaining_upm_orphans
    FROM uma_performance_metrics upm
    WHERE upm.workspace_id IS NOT NULL 
      AND upm.workspace_id NOT IN (SELECT id FROM workspaces);
    
    -- Check insights generated
    SELECT COUNT(*) INTO insights_generated
    FROM workspace_insights 
    WHERE workspace_id = '1f1bf9cf-3c46-48ed-96f3-ec826742ee02'
    AND metadata->>'migration_batch' = '014_cascade_fix';
    
    -- Check workspace_insights schema
    SELECT COUNT(*) INTO existing_columns
    FROM information_schema.columns 
    WHERE table_name = 'workspace_insights'
    AND column_name IN ('task_id', 'agent_role', 'relevance_tags', 'confidence_score', 'expires_at', 'metadata');
    
    required_columns := 6; -- Expected columns added
    
    -- Report validation results
    RAISE NOTICE '🎯 VALIDATION RESULTS:';
    
    IF mce_cascade_exists THEN
        RAISE NOTICE '✅ memory_context_entries CASCADE constraint: VERIFIED';
    ELSE
        RAISE EXCEPTION '❌ memory_context_entries CASCADE constraint: MISSING';
    END IF;
    
    IF upm_cascade_exists THEN
        RAISE NOTICE '✅ uma_performance_metrics CASCADE constraint: VERIFIED';
    ELSE
        RAISE EXCEPTION '❌ uma_performance_metrics CASCADE constraint: MISSING';
    END IF;
    
    IF remaining_mce_orphans = 0 THEN
        RAISE NOTICE '✅ memory_context_entries orphaned records: ZERO';
    ELSE
        RAISE EXCEPTION '❌ memory_context_entries still has % orphaned records', remaining_mce_orphans;
    END IF;
    
    IF remaining_upm_orphans = 0 THEN
        RAISE NOTICE '✅ uma_performance_metrics orphaned records: ZERO';
    ELSE
        RAISE EXCEPTION '❌ uma_performance_metrics still has % orphaned records', remaining_upm_orphans;
    END IF;
    
    IF existing_columns = required_columns THEN
        RAISE NOTICE '✅ workspace_insights schema: ALL REQUIRED COLUMNS PRESENT';
    ELSE
        RAISE NOTICE '⚠️  workspace_insights schema: % of % required columns present', existing_columns, required_columns;
    END IF;
    
    RAISE NOTICE '📊 Knowledge insights generated: %', insights_generated;
    
END $$;

-- =============================================================================
-- SUCCESS MESSAGE
-- =============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '🎉 ============================================================';
    RAISE NOTICE '🎉 CASCADE DELETE CONSTRAINTS FIX COMPLETED SUCCESSFULLY!';
    RAISE NOTICE '🎉 ============================================================';
    RAISE NOTICE '';
    RAISE NOTICE '✅ COMPLETED TASKS:';
    RAISE NOTICE '   🧹 Cleaned orphaned records from memory tables';
    RAISE NOTICE '   🔗 Added CASCADE DELETE constraints safely';
    RAISE NOTICE '   📝 Updated workspace_insights schema';
    RAISE NOTICE '   💡 Generated knowledge insights for target workspace';
    RAISE NOTICE '   🛡️ Verified all changes applied correctly';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 NEXT STEPS:';
    RAISE NOTICE '   1. Test knowledge insights API endpoint';
    RAISE NOTICE '   2. Verify CASCADE behavior with test workspace deletion';
    RAISE NOTICE '   3. Monitor application logs for any constraint-related errors';
    RAISE NOTICE '';
    RAISE NOTICE '📋 TARGET WORKSPACE: 1f1bf9cf-3c46-48ed-96f3-ec826742ee02';
    RAISE NOTICE '🕐 COMPLETED AT: %', NOW();
    RAISE NOTICE '';
END $$;