-- ====================================================================
-- DATABASE INTEGRITY AUDIT QUERIES
-- ====================================================================
-- Script per audit database: schema, vincoli, duplicazioni, orfani
-- TODO: Sostituire placeholders con credenziali DB reali

-- ====================================================================
-- 1. SCHEMA VERIFICATION
-- ====================================================================

-- Verifica esistenza tabelle core
SELECT 
    table_name,
    table_type,
    is_insertable_into
FROM information_schema.tables 
WHERE table_schema = 'public'
AND table_name IN (
    'workspaces',
    'workspace_goals', 
    'tasks',
    'agents',
    'team_proposals',
    'asset_artifacts',
    'deliverables'
)
ORDER BY table_name;

-- Verifica colonne per ogni tabella core
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name IN (
    'workspaces',
    'workspace_goals',
    'tasks', 
    'agents',
    'team_proposals',
    'asset_artifacts',
    'deliverables'
)
ORDER BY table_name, ordinal_position;

-- ====================================================================
-- 2. REFERENTIAL INTEGRITY CHECKS
-- ====================================================================

-- Check per workspace_goals orfani
SELECT 
    'workspace_goals' as table_name,
    COUNT(*) as orphaned_records
FROM workspace_goals wg
LEFT JOIN workspaces w ON wg.workspace_id = w.id
WHERE w.id IS NULL;

-- Check per tasks orfani (workspace)
SELECT 
    'tasks_orphaned_workspace' as check_name,
    COUNT(*) as orphaned_records  
FROM tasks t
LEFT JOIN workspaces w ON t.workspace_id = w.id
WHERE w.id IS NULL;

-- Check per tasks orfani (goal)
SELECT 
    'tasks_orphaned_goal' as check_name,
    COUNT(*) as orphaned_records
FROM tasks t  
LEFT JOIN workspace_goals wg ON t.goal_id = wg.id
WHERE t.goal_id IS NOT NULL AND wg.id IS NULL;

-- Check per agents orfani
SELECT 
    'agents_orphaned' as check_name,
    COUNT(*) as orphaned_records
FROM agents a
LEFT JOIN workspaces w ON a.workspace_id = w.id  
WHERE w.id IS NULL;

-- Check per asset_artifacts orfani
SELECT 
    'assets_orphaned' as check_name,
    COUNT(*) as orphaned_records
FROM asset_artifacts aa
LEFT JOIN tasks t ON aa.task_id = t.id
WHERE t.id IS NULL;

-- ====================================================================
-- 3. DUPLICATION DETECTION
-- ====================================================================

-- Duplicate workspace names
SELECT 
    name,
    COUNT(*) as duplicate_count
FROM workspaces
GROUP BY name
HAVING COUNT(*) > 1;

-- Duplicate task names per workspace
SELECT 
    workspace_id,
    name,
    COUNT(*) as duplicate_count
FROM tasks
GROUP BY workspace_id, name
HAVING COUNT(*) > 1;

-- Duplicate agent names per workspace  
SELECT 
    workspace_id,
    name,
    COUNT(*) as duplicate_count
FROM agents
GROUP BY workspace_id, name
HAVING COUNT(*) > 1;

-- Duplicate goal metrics per workspace
SELECT 
    workspace_id,
    metric_type,
    COUNT(*) as duplicate_count
FROM workspace_goals
GROUP BY workspace_id, metric_type
HAVING COUNT(*) > 1;

-- ====================================================================
-- 4. DATA CONSISTENCY CHECKS
-- ====================================================================

-- Tasks senza goal_id valido
SELECT 
    COUNT(*) as tasks_without_valid_goal
FROM tasks t
WHERE t.goal_id IS NOT NULL 
AND NOT EXISTS (
    SELECT 1 FROM workspace_goals wg 
    WHERE wg.id = t.goal_id
);

-- Goals con status inconsistente
SELECT 
    status,
    COUNT(*) as count
FROM workspace_goals
WHERE status NOT IN ('active', 'completed', 'paused', 'cancelled')
GROUP BY status;

-- Tasks con status inconsistente
SELECT 
    status,
    COUNT(*) as count  
FROM tasks
WHERE status NOT IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled')
GROUP BY status;

-- ====================================================================
-- 5. TRACE ID VERIFICATION  
-- ====================================================================

-- TODO: Sostituire AUDIT_TRACE_ID con trace ID reale
-- Workspaces con trace ID specifico
SELECT 
    id,
    name,
    description,
    created_at
FROM workspaces
WHERE description LIKE '%AUDIT_TRACE_ID%'
OR name LIKE '%AUDIT_TRACE_ID%';

-- Goals con trace ID specifico
SELECT 
    id,
    workspace_id,
    description,
    created_at
FROM workspace_goals  
WHERE description LIKE '%AUDIT_TRACE_ID%';

-- Tasks generati per workspace audit
SELECT 
    t.id,
    t.workspace_id,
    t.name,
    t.status,
    t.created_at
FROM tasks t
JOIN workspaces w ON t.workspace_id = w.id
WHERE w.description LIKE '%AUDIT_TRACE_ID%';

-- ====================================================================
-- 6. PERFORMANCE & UTILIZATION METRICS
-- ====================================================================

-- Conteggio record per tabella
SELECT 
    'workspaces' as table_name,
    COUNT(*) as record_count
FROM workspaces
UNION ALL
SELECT 
    'workspace_goals',
    COUNT(*)
FROM workspace_goals  
UNION ALL
SELECT 
    'tasks',
    COUNT(*)
FROM tasks
UNION ALL
SELECT 
    'agents', 
    COUNT(*)
FROM agents
UNION ALL
SELECT 
    'team_proposals',
    COUNT(*)
FROM team_proposals
UNION ALL
SELECT 
    'asset_artifacts',
    COUNT(*)
FROM asset_artifacts;

-- Distribuzione task per status
SELECT 
    status,
    COUNT(*) as task_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM tasks
GROUP BY status
ORDER BY task_count DESC;

-- Workspaces più attivi (per numero task)
SELECT 
    w.id,
    w.name,
    COUNT(t.id) as task_count,
    COUNT(DISTINCT wg.id) as goal_count,
    COUNT(DISTINCT a.id) as agent_count
FROM workspaces w
LEFT JOIN tasks t ON w.id = t.workspace_id
LEFT JOIN workspace_goals wg ON w.id = wg.workspace_id  
LEFT JOIN agents a ON w.id = a.workspace_id
GROUP BY w.id, w.name
ORDER BY task_count DESC
LIMIT 10;

-- ====================================================================
-- 7. QUALITY METRICS
-- ====================================================================

-- Asset artifacts con quality score
SELECT 
    COUNT(*) as total_assets,
    AVG(quality_score) as avg_quality,
    MIN(quality_score) as min_quality,
    MAX(quality_score) as max_quality
FROM asset_artifacts
WHERE quality_score IS NOT NULL;

-- Distribuzione quality score
SELECT 
    CASE 
        WHEN quality_score >= 90 THEN 'Excellent (90+)'
        WHEN quality_score >= 70 THEN 'Good (70-89)'
        WHEN quality_score >= 50 THEN 'Fair (50-69)'
        ELSE 'Poor (<50)'
    END as quality_tier,
    COUNT(*) as asset_count
FROM asset_artifacts
WHERE quality_score IS NOT NULL
GROUP BY quality_tier
ORDER BY MIN(quality_score) DESC;

-- ====================================================================
-- 8. AUDIT CLEANUP VERIFICATION
-- ====================================================================

-- Verifica pulizia dati di test
-- TODO: Eseguire dopo cleanup per verificare rimozione completa
SELECT 
    'Test data cleanup verification' as check_name,
    COUNT(*) as remaining_test_records
FROM workspaces
WHERE name LIKE '%Audit Test%' 
   OR name LIKE '%Test%'
   OR description LIKE '%audit%';

-- Verifica integrità dopo cleanup
SELECT 
    'Post-cleanup integrity' as check_name,
    (SELECT COUNT(*) FROM workspace_goals wg 
     LEFT JOIN workspaces w ON wg.workspace_id = w.id 
     WHERE w.id IS NULL) as orphaned_goals,
    (SELECT COUNT(*) FROM tasks t 
     LEFT JOIN workspaces w ON t.workspace_id = w.id 
     WHERE w.id IS NULL) as orphaned_tasks;

-- ====================================================================
-- 9. CUSTOM INTEGRITY CHECKS  
-- ====================================================================

-- Check per workspace senza goals
SELECT 
    w.id,
    w.name,
    w.created_at
FROM workspaces w
LEFT JOIN workspace_goals wg ON w.id = wg.workspace_id
WHERE wg.id IS NULL
ORDER BY w.created_at DESC;

-- Check per goals senza tasks
SELECT 
    wg.id,
    wg.workspace_id,
    wg.description,
    wg.target_value
FROM workspace_goals wg
LEFT JOIN tasks t ON wg.id = t.goal_id
WHERE t.id IS NULL
AND wg.status = 'active'
ORDER BY wg.created_at DESC;

-- Check per workspaces senza agents
SELECT 
    w.id,
    w.name,
    w.status
FROM workspaces w
LEFT JOIN agents a ON w.id = a.workspace_id
WHERE a.id IS NULL
AND w.status = 'active'
ORDER BY w.created_at DESC;