-- Check CASCADE DELETE constraints for workspace deletion
-- Run this in Supabase SQL editor to audit current constraints

-- 1. Show all foreign key constraints that reference workspaces table
SELECT 
    tc.table_name,
    tc.constraint_name,
    kcu.column_name,
    rc.delete_rule,
    CASE 
        WHEN rc.delete_rule = 'CASCADE' THEN '✅ CASCADE DELETE'
        WHEN rc.delete_rule = 'SET NULL' THEN '⚠️ SET NULL'
        WHEN rc.delete_rule = 'RESTRICT' THEN '❌ RESTRICT'
        WHEN rc.delete_rule = 'NO ACTION' THEN '❌ NO ACTION'
        ELSE '❓ UNKNOWN'
    END as status,
    CASE 
        WHEN rc.delete_rule != 'CASCADE' THEN 
            'ALTER TABLE ' || tc.table_name || ' ADD CONSTRAINT fk_' || tc.table_name || '_workspace_id FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE;'
        ELSE NULL
    END as fix_sql
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
    AND kcu.column_name = 'workspace_id'
    AND tc.table_schema = 'public'
ORDER BY tc.table_name;

-- 2. Find tables with workspace_id column but NO foreign key constraint
SELECT 
    t.table_name,
    c.column_name,
    '❌ NO FOREIGN KEY' as status,
    'ALTER TABLE ' || t.table_name || ' ADD CONSTRAINT fk_' || t.table_name || '_workspace_id FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE;' as fix_sql
FROM information_schema.tables t
JOIN information_schema.columns c ON t.table_name = c.table_name
LEFT JOIN (
    SELECT 
        tc.table_name,
        kcu.column_name
    FROM information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
        AND ccu.table_schema = tc.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY' 
        AND ccu.table_name = 'workspaces'
        AND kcu.column_name = 'workspace_id'
        AND tc.table_schema = 'public'
) fk ON t.table_name = fk.table_name AND c.column_name = fk.column_name
WHERE t.table_schema = 'public'
    AND t.table_type = 'BASE TABLE'
    AND c.column_name = 'workspace_id'
    AND fk.table_name IS NULL
ORDER BY t.table_name;

-- 3. Count records in each table with workspace_id for impact analysis
-- (Replace 'YOUR_WORKSPACE_ID' with actual workspace ID to test)
/*
SELECT 
    'workspaces' as table_name, 
    count(*) as record_count,
    'Main table' as notes
FROM workspaces 
WHERE id = 'YOUR_WORKSPACE_ID'

UNION ALL

SELECT 
    'agents', 
    count(*), 
    CASE WHEN count(*) > 0 THEN 'Will be CASCADE deleted' ELSE 'No records' END
FROM agents 
WHERE workspace_id = 'YOUR_WORKSPACE_ID'

UNION ALL

SELECT 
    'tasks', 
    count(*), 
    CASE WHEN count(*) > 0 THEN 'Will be CASCADE deleted' ELSE 'No records' END
FROM tasks 
WHERE workspace_id = 'YOUR_WORKSPACE_ID'

UNION ALL

SELECT 
    'workspace_goals', 
    count(*), 
    CASE WHEN count(*) > 0 THEN 'Will be CASCADE deleted' ELSE 'No records' END
FROM workspace_goals 
WHERE workspace_id = 'YOUR_WORKSPACE_ID'

UNION ALL

SELECT 
    'workspace_insights', 
    count(*), 
    CASE WHEN count(*) > 0 THEN 'Will be CASCADE deleted' ELSE 'No records' END
FROM workspace_insights 
WHERE workspace_id = 'YOUR_WORKSPACE_ID'

UNION ALL

SELECT 
    'logs', 
    count(*), 
    CASE WHEN count(*) > 0 THEN 'Check CASCADE constraint' ELSE 'No records' END
FROM logs 
WHERE workspace_id = 'YOUR_WORKSPACE_ID'

UNION ALL

SELECT 
    'execution_logs', 
    count(*), 
    CASE WHEN count(*) > 0 THEN 'Will be CASCADE deleted' ELSE 'No records' END
FROM execution_logs 
WHERE workspace_id = 'YOUR_WORKSPACE_ID'

UNION ALL

SELECT 
    'human_feedback_requests', 
    count(*), 
    CASE WHEN count(*) > 0 THEN 'Will be CASCADE deleted' ELSE 'No records' END
FROM human_feedback_requests 
WHERE workspace_id = 'YOUR_WORKSPACE_ID'

UNION ALL

SELECT 
    'team_proposals', 
    count(*), 
    CASE WHEN count(*) > 0 THEN 'Will be CASCADE deleted' ELSE 'No records' END
FROM team_proposals 
WHERE workspace_id = 'YOUR_WORKSPACE_ID'

UNION ALL

SELECT 
    'custom_tools', 
    count(*), 
    CASE WHEN count(*) > 0 THEN 'Will be CASCADE deleted' ELSE 'No records' END
FROM custom_tools 
WHERE workspace_id = 'YOUR_WORKSPACE_ID'

UNION ALL

SELECT 
    'agent_handoffs', 
    count(*), 
    CASE WHEN count(*) > 0 THEN 'Will be CASCADE deleted' ELSE 'No records' END
FROM agent_handoffs 
WHERE workspace_id = 'YOUR_WORKSPACE_ID'

ORDER BY record_count DESC;
*/

-- 4. Check for potential orphaned data (records with invalid workspace_id)
SELECT 
    'agents' as table_name,
    count(*) as orphaned_records
FROM agents a
LEFT JOIN workspaces w ON a.workspace_id = w.id
WHERE a.workspace_id IS NOT NULL AND w.id IS NULL

UNION ALL

SELECT 
    'tasks',
    count(*)
FROM tasks t
LEFT JOIN workspaces w ON t.workspace_id = w.id
WHERE t.workspace_id IS NOT NULL AND w.id IS NULL

UNION ALL

SELECT 
    'workspace_goals',
    count(*)
FROM workspace_goals wg
LEFT JOIN workspaces w ON wg.workspace_id = w.id
WHERE wg.workspace_id IS NOT NULL AND w.id IS NULL

UNION ALL

SELECT 
    'workspace_insights',
    count(*)
FROM workspace_insights wi
LEFT JOIN workspaces w ON wi.workspace_id = w.id
WHERE wi.workspace_id IS NOT NULL AND w.id IS NULL

UNION ALL

SELECT 
    'logs',
    count(*)
FROM logs l
LEFT JOIN workspaces w ON l.workspace_id = w.id
WHERE l.workspace_id IS NOT NULL AND w.id IS NULL

UNION ALL

SELECT 
    'execution_logs',
    count(*)
FROM execution_logs el
LEFT JOIN workspaces w ON el.workspace_id = w.id
WHERE el.workspace_id IS NOT NULL AND w.id IS NULL

UNION ALL

SELECT 
    'human_feedback_requests',
    count(*)
FROM human_feedback_requests hfr
LEFT JOIN workspaces w ON hfr.workspace_id = w.id
WHERE hfr.workspace_id IS NOT NULL AND w.id IS NULL

UNION ALL

SELECT 
    'team_proposals',
    count(*)
FROM team_proposals tp
LEFT JOIN workspaces w ON tp.workspace_id = w.id
WHERE tp.workspace_id IS NOT NULL AND w.id IS NULL

UNION ALL

SELECT 
    'custom_tools',
    count(*)
FROM custom_tools ct
LEFT JOIN workspaces w ON ct.workspace_id = w.id
WHERE ct.workspace_id IS NOT NULL AND w.id IS NULL

UNION ALL

SELECT 
    'agent_handoffs',
    count(*)
FROM agent_handoffs ah
LEFT JOIN workspaces w ON ah.workspace_id = w.id
WHERE ah.workspace_id IS NOT NULL AND w.id IS NULL

ORDER BY orphaned_records DESC;

-- Show summary
SELECT 'Cascade constraint audit completed' as status;