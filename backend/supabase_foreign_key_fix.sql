-- ================================================================
-- IMMEDIATE SUPABASE FIX: insight_audit_trail foreign key constraint
-- ================================================================
-- Execute these commands directly in Supabase SQL Editor
-- to resolve workspace deletion blocking issue
-- ================================================================

-- STEP 1: DIAGNOSTIC QUERIES (run first to understand current state)
-- ================================================================

-- Check current foreign key constraints on insight_audit_trail
SELECT 
    tc.constraint_name,
    tc.constraint_type,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.delete_rule
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
  AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
  AND ccu.table_schema = tc.table_schema
LEFT JOIN information_schema.referential_constraints AS rc
  ON tc.constraint_name = rc.constraint_name
WHERE tc.table_name = 'insight_audit_trail' 
  AND tc.constraint_type = 'FOREIGN KEY';

-- Check how many audit records reference workspaces
SELECT 
    COUNT(*) as total_audit_records,
    COUNT(DISTINCT workspace_id) as unique_workspaces_referenced,
    COUNT(CASE WHEN workspace_id IS NULL THEN 1 END) as null_workspace_ids
FROM insight_audit_trail;

-- Check for potential orphaned audit records
SELECT 
    iat.workspace_id,
    COUNT(*) as audit_record_count,
    CASE WHEN w.id IS NULL THEN 'ORPHANED' ELSE 'VALID' END as status
FROM insight_audit_trail iat
LEFT JOIN workspaces w ON iat.workspace_id = w.id
GROUP BY iat.workspace_id, w.id
ORDER BY audit_record_count DESC;

-- ================================================================
-- STEP 2: APPLY THE FIX (run after reviewing diagnostics)
-- ================================================================

-- Drop the problematic foreign key constraint
ALTER TABLE insight_audit_trail 
DROP CONSTRAINT insight_audit_trail_workspace_id_fkey;

-- Recreate with CASCADE behavior
ALTER TABLE insight_audit_trail 
ADD CONSTRAINT insight_audit_trail_workspace_id_fkey 
FOREIGN KEY (workspace_id) 
REFERENCES workspaces(id) 
ON DELETE CASCADE;

-- ================================================================
-- STEP 3: VERIFICATION (run to confirm fix worked)
-- ================================================================

-- Verify the new constraint has CASCADE behavior
SELECT 
    tc.constraint_name,
    rc.delete_rule as on_delete_behavior
FROM information_schema.table_constraints AS tc
LEFT JOIN information_schema.referential_constraints AS rc
  ON tc.constraint_name = rc.constraint_name
WHERE tc.table_name = 'insight_audit_trail' 
  AND tc.constraint_type = 'FOREIGN KEY'
  AND tc.constraint_name = 'insight_audit_trail_workspace_id_fkey';

-- Success message
SELECT 'SUCCESS: Workspace deletion is now unblocked. Audit records will cascade automatically.' as result;

-- ================================================================
-- ALTERNATIVE SOLUTION: If you prefer to clean up first
-- ================================================================

-- Option A: Delete specific audit records before workspace deletion
-- DELETE FROM insight_audit_trail WHERE workspace_id = 'your-workspace-id-here';

-- Option B: Clean up all audit records (if you don't need audit history)
-- DELETE FROM insight_audit_trail WHERE workspace_id IS NOT NULL;
-- WARNING: This removes all audit history - use with caution