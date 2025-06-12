-- Fix CASCADE DELETE for workspace deletion
-- Run this in Supabase SQL editor to fix orphaned data issue

-- 1. First, clean up any existing orphaned log entries
DELETE FROM logs 
WHERE workspace_id IS NOT NULL 
AND workspace_id NOT IN (SELECT id FROM workspaces);

-- Check how many orphaned entries were removed
SELECT 'Orphaned log entries cleaned up' as status;

-- 2. Add CASCADE DELETE constraint to logs table
-- Note: If the constraint already exists, this will throw an error (which is fine)
ALTER TABLE logs 
ADD CONSTRAINT fk_logs_workspace_id 
FOREIGN KEY (workspace_id) 
REFERENCES workspaces(id) 
ON DELETE CASCADE;

-- 3. Optional: Add agent_id constraint with SET NULL (recommended)
-- This ensures logs remain even if agent is deleted but workspace_id is cleared
ALTER TABLE logs 
ADD CONSTRAINT fk_logs_agent_id 
FOREIGN KEY (agent_id) 
REFERENCES agents(id) 
ON DELETE SET NULL;

-- 4. Verify all CASCADE DELETE constraints are in place
SELECT 
    tc.table_name,
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
    AND tc.table_schema = rc.constraint_schema
WHERE tc.constraint_type = 'FOREIGN KEY' 
    AND ccu.table_name = 'workspaces'
    AND tc.table_schema = 'public'
ORDER BY tc.table_name;

-- 5. Test query to check what would be deleted with a workspace
-- (Don't actually run this DELETE - it's just to show the scope)
-- 
-- This query shows all related tables that would be affected:
SELECT 
    'workspaces' as table_name, count(*) as record_count
FROM workspaces WHERE id = 'YOUR_WORKSPACE_ID_HERE'
UNION ALL
SELECT 'agents', count(*) FROM agents WHERE workspace_id = 'YOUR_WORKSPACE_ID_HERE'
UNION ALL
SELECT 'tasks', count(*) FROM tasks WHERE workspace_id = 'YOUR_WORKSPACE_ID_HERE'
UNION ALL
SELECT 'workspace_goals', count(*) FROM workspace_goals WHERE workspace_id = 'YOUR_WORKSPACE_ID_HERE'
UNION ALL
SELECT 'workspace_insights', count(*) FROM workspace_insights WHERE workspace_id = 'YOUR_WORKSPACE_ID_HERE'
UNION ALL
SELECT 'logs', count(*) FROM logs WHERE workspace_id = 'YOUR_WORKSPACE_ID_HERE'
UNION ALL
SELECT 'execution_logs', count(*) FROM execution_logs WHERE workspace_id = 'YOUR_WORKSPACE_ID_HERE'
UNION ALL
SELECT 'human_feedback_requests', count(*) FROM human_feedback_requests WHERE workspace_id = 'YOUR_WORKSPACE_ID_HERE'
UNION ALL
SELECT 'team_proposals', count(*) FROM team_proposals WHERE workspace_id = 'YOUR_WORKSPACE_ID_HERE'
UNION ALL
SELECT 'custom_tools', count(*) FROM custom_tools WHERE workspace_id = 'YOUR_WORKSPACE_ID_HERE'
UNION ALL
SELECT 'agent_handoffs', count(*) FROM agent_handoffs WHERE workspace_id = 'YOUR_WORKSPACE_ID_HERE';

SELECT 'CASCADE DELETE constraints verification completed' as status;