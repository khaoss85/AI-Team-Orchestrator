-- ================================================================================================
-- RECOVERY SYSTEM PERFORMANCE ANALYSIS
-- ================================================================================================
-- Purpose: Analyze the performance impact of the recovery system tables and indexes
-- Date: 2025-08-26
-- Author: AI-Team-Orchestrator Auto-Recovery System
-- ================================================================================================

-- ================================================================================================
-- 1. INDEX USAGE ANALYSIS
-- ================================================================================================

-- Analyze index usage on recovery tables
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch,
    idx_scan,
    CASE 
        WHEN idx_scan > 0 THEN ROUND((idx_tup_read::numeric / idx_scan::numeric), 2)
        ELSE 0 
    END as avg_tuples_per_scan
FROM pg_stat_user_indexes 
WHERE tablename IN ('failure_patterns', 'recovery_attempts', 'recovery_explanations', 'tasks', 'workspaces')
ORDER BY tablename, idx_scan DESC;

-- ================================================================================================
-- 2. TABLE SIZE AND GROWTH ANALYSIS
-- ================================================================================================

-- Analyze table sizes for recovery system
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as index_size,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows,
    CASE 
        WHEN n_live_tup > 0 THEN ROUND((n_dead_tup::numeric / n_live_tup::numeric) * 100, 2)
        ELSE 0 
    END as dead_row_percentage
FROM pg_stat_user_tables 
WHERE tablename IN (
    'failure_patterns', 'recovery_attempts', 'recovery_explanations', 
    'tasks', 'workspaces', 'task_executions', 'execution_logs'
)
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- ================================================================================================
-- 3. QUERY PERFORMANCE ANALYSIS
-- ================================================================================================

-- Most expensive queries related to recovery system (requires pg_stat_statements extension)
-- This query will only work if pg_stat_statements is enabled
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time,
    stddev_time,
    rows as total_rows,
    CASE 
        WHEN calls > 0 THEN ROUND((rows::numeric / calls::numeric), 2)
        ELSE 0 
    END as avg_rows_per_call
FROM pg_stat_statements 
WHERE query LIKE '%failure_patterns%' 
   OR query LIKE '%recovery_attempts%' 
   OR query LIKE '%recovery_explanations%'
ORDER BY mean_time DESC
LIMIT 20;

-- ================================================================================================
-- 4. RECOVERY SYSTEM METRICS
-- ================================================================================================

-- Current recovery system usage statistics
SELECT 
    'Recovery Tables Summary' as metric_category,
    (SELECT COUNT(*) FROM failure_patterns) as failure_patterns_count,
    (SELECT COUNT(*) FROM recovery_attempts) as recovery_attempts_count,
    (SELECT COUNT(*) FROM recovery_explanations) as recovery_explanations_count,
    (SELECT COUNT(*) FROM tasks WHERE recovery_count > 0) as tasks_with_recoveries,
    (SELECT COUNT(*) FROM workspaces WHERE total_recovery_attempts > 0) as workspaces_with_recoveries;

-- Recovery success rates by failure type
SELECT 
    fp.failure_type,
    COUNT(ra.id) as total_attempts,
    COUNT(CASE WHEN ra.success = true THEN 1 END) as successful_attempts,
    CASE 
        WHEN COUNT(ra.id) > 0 THEN 
            ROUND((COUNT(CASE WHEN ra.success = true THEN 1 END)::numeric / COUNT(ra.id)::numeric) * 100, 2)
        ELSE 0 
    END as success_rate_percentage,
    AVG(EXTRACT(EPOCH FROM ra.actual_resolution_time)) as avg_resolution_seconds
FROM failure_patterns fp
LEFT JOIN recovery_attempts ra ON fp.id = ra.failure_pattern_id
GROUP BY fp.failure_type
ORDER BY success_rate_percentage DESC;

-- Most common failure patterns
SELECT 
    failure_type,
    COUNT(*) as pattern_count,
    SUM(occurrence_count) as total_occurrences,
    AVG(confidence_score) as avg_confidence,
    MAX(last_detected_at) as last_seen,
    COUNT(CASE WHEN is_transient = true THEN 1 END) as transient_patterns,
    COUNT(CASE WHEN is_transient = false THEN 1 END) as permanent_patterns
FROM failure_patterns
GROUP BY failure_type
ORDER BY total_occurrences DESC;

-- ================================================================================================
-- 5. PERFORMANCE OPTIMIZATION RECOMMENDATIONS
-- ================================================================================================

-- Identify missing indexes based on query patterns
SELECT 
    'Index Analysis' as analysis_type,
    'Check for missing indexes on frequently filtered columns' as recommendation,
    'Monitor pg_stat_user_tables.seq_scan vs idx_scan ratios' as details
UNION ALL
SELECT 
    'Partitioning',
    'Consider partitioning large tables by time period',
    'failure_patterns and recovery_attempts may benefit from monthly partitioning'
UNION ALL
SELECT 
    'Archival',
    'Implement automatic data archival for old records',
    'Use cleanup_old_recovery_data() function regularly'
UNION ALL
SELECT 
    'Monitoring',
    'Set up alerts for recovery system table growth',
    'Monitor for tables growing faster than expected';

-- ================================================================================================
-- 6. DATA QUALITY CHECKS
-- ================================================================================================

-- Check for data quality issues in recovery system
SELECT 
    'Data Quality Issues' as check_category,
    'Orphaned recovery attempts' as issue_type,
    COUNT(*) as count
FROM recovery_attempts ra
LEFT JOIN failure_patterns fp ON ra.failure_pattern_id = fp.id
WHERE ra.failure_pattern_id IS NOT NULL AND fp.id IS NULL

UNION ALL

SELECT 
    'Data Quality Issues',
    'Recovery attempts without completion time but marked complete',
    COUNT(*)
FROM recovery_attempts
WHERE status IN ('completed', 'failed') AND completed_at IS NULL

UNION ALL

SELECT 
    'Data Quality Issues', 
    'Tasks with recovery count but no recovery attempts',
    COUNT(*)
FROM tasks t
LEFT JOIN recovery_attempts ra ON t.id = ra.task_id
WHERE t.recovery_count > 0 AND ra.id IS NULL;

-- ================================================================================================
-- 7. STORAGE OPTIMIZATION ANALYSIS
-- ================================================================================================

-- Analyze JSONB column sizes and usage
SELECT 
    'JSONB Usage Analysis' as analysis_type,
    'context_metadata' as column_name,
    'failure_patterns' as table_name,
    AVG(LENGTH(context_metadata::text)) as avg_size_bytes,
    MAX(LENGTH(context_metadata::text)) as max_size_bytes,
    COUNT(CASE WHEN context_metadata = '{}' THEN 1 END) as empty_count,
    COUNT(*) as total_count
FROM failure_patterns

UNION ALL

SELECT 
    'JSONB Usage Analysis',
    'recovery_context',
    'recovery_attempts',
    AVG(LENGTH(recovery_context::text)),
    MAX(LENGTH(recovery_context::text)),
    COUNT(CASE WHEN recovery_context = '{}' THEN 1 END),
    COUNT(*)
FROM recovery_attempts

UNION ALL

SELECT 
    'JSONB Usage Analysis',
    'technical_details',
    'recovery_explanations',
    AVG(LENGTH(technical_details::text)),
    MAX(LENGTH(technical_details::text)),
    COUNT(CASE WHEN technical_details = '{}' THEN 1 END),
    COUNT(*)
FROM recovery_explanations;

-- ================================================================================================
-- 8. CONCURRENCY AND LOCKING ANALYSIS
-- ================================================================================================

-- Check for potential locking issues
SELECT 
    'Concurrency Analysis' as analysis_type,
    'Current locks on recovery tables' as metric,
    COUNT(*) as active_locks
FROM pg_locks l
JOIN pg_class c ON l.relation = c.oid
WHERE c.relname IN ('failure_patterns', 'recovery_attempts', 'recovery_explanations')
AND NOT l.granted;

-- Check for long-running transactions affecting recovery tables
SELECT 
    'Long-running transactions' as analysis_type,
    pid,
    now() - pg_stat_activity.query_start as duration,
    state,
    query
FROM pg_stat_activity
WHERE state = 'active'
AND query LIKE '%failure_patterns%' OR query LIKE '%recovery_attempts%' OR query LIKE '%recovery_explanations%'
AND now() - pg_stat_activity.query_start > interval '30 seconds';

-- ================================================================================================
-- ANALYSIS COMPLETE
-- ================================================================================================

-- Summary metrics for monitoring dashboard
SELECT 
    'Recovery System Health Summary' as summary_section,
    (SELECT COUNT(*) FROM failure_patterns WHERE last_detected_at > now() - interval '24 hours') as recent_failures,
    (SELECT COUNT(*) FROM recovery_attempts WHERE status = 'in_progress') as active_recoveries,
    (SELECT COUNT(*) FROM recovery_attempts WHERE started_at > now() - interval '24 hours') as recoveries_24h,
    (SELECT ROUND(AVG(confidence_score), 2) FROM recovery_attempts WHERE confidence_score IS NOT NULL) as avg_confidence,
    (SELECT COUNT(*) FROM tasks WHERE auto_recovery_enabled = false) as recovery_disabled_tasks;