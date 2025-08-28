-- ============================================================================
-- MIGRATION: Add unique constraint to deliverables table
-- Version: 011
-- Date: 2025-08-28
-- Purpose: Prevent duplicate deliverables with same workspace_id, goal_id, title
-- ============================================================================

-- First, check if constraint already exists (safety check)
DO $$
BEGIN
    -- Only add constraint if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.table_constraints 
        WHERE table_name = 'deliverables' 
        AND constraint_name = 'unique_workspace_goal_title'
    ) THEN
        -- Add the unique constraint
        ALTER TABLE deliverables 
        ADD CONSTRAINT unique_workspace_goal_title 
        UNIQUE (workspace_id, goal_id, title);
        
        RAISE NOTICE 'Added unique constraint: unique_workspace_goal_title';
    ELSE
        RAISE NOTICE 'Unique constraint unique_workspace_goal_title already exists';
    END IF;
END
$$;