-- ============================================================================
-- ROLLBACK MIGRATION: Remove unique constraint from deliverables table
-- Version: 011
-- Date: 2025-08-28
-- Purpose: Remove unique constraint unique_workspace_goal_title if needed
-- ============================================================================

-- Remove the unique constraint
DO $$
BEGIN
    -- Only remove constraint if it exists
    IF EXISTS (
        SELECT 1 
        FROM information_schema.table_constraints 
        WHERE table_name = 'deliverables' 
        AND constraint_name = 'unique_workspace_goal_title'
    ) THEN
        -- Remove the unique constraint
        ALTER TABLE deliverables 
        DROP CONSTRAINT unique_workspace_goal_title;
        
        RAISE NOTICE 'Removed unique constraint: unique_workspace_goal_title';
    ELSE
        RAISE NOTICE 'Unique constraint unique_workspace_goal_title does not exist';
    END IF;
END
$$;