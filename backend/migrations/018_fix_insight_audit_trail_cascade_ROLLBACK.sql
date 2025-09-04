-- ================================================================
-- Migration 018 ROLLBACK: Revert insight_audit_trail CASCADE fix
-- ================================================================
-- 
-- This rollback script reverts the foreign key constraint back to
-- RESTRICT behavior (the original problematic state).
--
-- WARNING: This rollback will restore the original problem where
-- workspaces cannot be deleted if they have audit trail records.
-- ================================================================

-- Step 1: Drop the CASCADE constraint
ALTER TABLE insight_audit_trail 
DROP CONSTRAINT IF EXISTS insight_audit_trail_workspace_id_fkey;

-- Step 2: Recreate the original RESTRICT constraint (default behavior)
ALTER TABLE insight_audit_trail 
ADD CONSTRAINT insight_audit_trail_workspace_id_fkey 
FOREIGN KEY (workspace_id) 
REFERENCES workspaces(id);
-- Note: No ON DELETE clause = RESTRICT behavior (original problem)

-- Step 3: Log rollback completion
DO $$
BEGIN
    RAISE NOTICE 'ROLLBACK COMPLETE: Foreign key constraint reverted to RESTRICT behavior';
    RAISE NOTICE 'WARNING: Workspace deletion will again be blocked if audit records exist';
END $$;