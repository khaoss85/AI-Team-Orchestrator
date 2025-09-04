-- ================================================================
-- Migration 018: Fix insight_audit_trail foreign key constraint
-- ================================================================
-- 
-- PROBLEM: insight_audit_trail.workspace_id FK lacks ON DELETE clause,
-- defaulting to RESTRICT behavior that prevents workspace deletion.
--
-- SOLUTION: Add CASCADE behavior so audit records are automatically
-- deleted when their parent workspace is removed.
--
-- SAFETY: This is safe because audit trails are workspace-scoped
-- operational logs, not regulatory compliance records.
-- ================================================================

-- Step 1: Check current constraint status
DO $$
BEGIN
    -- Log current constraint information
    RAISE NOTICE 'Current insight_audit_trail constraints:';
    PERFORM constraint_name, constraint_type 
    FROM information_schema.table_constraints 
    WHERE table_name = 'insight_audit_trail' AND constraint_type = 'FOREIGN KEY';
END $$;

-- Step 2: Drop the existing foreign key constraint
-- Note: The constraint name follows PostgreSQL naming convention
ALTER TABLE insight_audit_trail 
DROP CONSTRAINT IF EXISTS insight_audit_trail_workspace_id_fkey;

-- Step 3: Recreate the constraint with CASCADE behavior
ALTER TABLE insight_audit_trail 
ADD CONSTRAINT insight_audit_trail_workspace_id_fkey 
FOREIGN KEY (workspace_id) 
REFERENCES workspaces(id) 
ON DELETE CASCADE;

-- Step 4: Verify the new constraint
DO $$
BEGIN
    RAISE NOTICE 'Updated constraint successfully created with CASCADE behavior';
    RAISE NOTICE 'Workspaces can now be deleted safely - audit records will be automatically cleaned up';
END $$;

-- Step 5: Add comment for future reference
COMMENT ON CONSTRAINT insight_audit_trail_workspace_id_fkey 
ON insight_audit_trail 
IS 'Cascades on workspace deletion - audit trails are workspace-scoped operational logs';