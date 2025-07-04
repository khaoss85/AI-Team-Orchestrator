-- ========================================================================
-- 🧠 Universal Memory Architecture (UMA) Database Schema
-- ========================================================================
-- Tables per supportare UMA Enhanced Memory System
-- Compatibile con il nuovo database linkage (goal_id atomico nei task)

-- Table: memory_context_cache
-- Purpose: High-performance semantic cache per context retrieval
CREATE TABLE IF NOT EXISTS memory_context_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_hash VARCHAR(64) UNIQUE NOT NULL,
    context_data JSONB NOT NULL,
    original_query JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    access_count INTEGER DEFAULT 1,
    
    -- Indexes for performance
    CONSTRAINT valid_expires_at CHECK (expires_at > created_at)
);

-- Index per performance ottimizzata
CREATE INDEX IF NOT EXISTS idx_memory_context_cache_hash ON memory_context_cache (query_hash);
CREATE INDEX IF NOT EXISTS idx_memory_context_cache_expires ON memory_context_cache (expires_at);
CREATE INDEX IF NOT EXISTS idx_memory_context_cache_workspace ON memory_context_cache 
    USING GIN ((original_query->'workspace_id'));

-- Table: memory_context_entries  
-- Purpose: Structured context storage con semantic features
CREATE TABLE IF NOT EXISTS memory_context_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL,
    context_type VARCHAR(100) NOT NULL DEFAULT 'general',
    content JSONB NOT NULL,
    importance_score DECIMAL(3,2) NOT NULL DEFAULT 0.5,
    semantic_hash VARCHAR(64) NOT NULL,
    goal_context JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    access_count INTEGER DEFAULT 0,
    
    -- Constraints
    CONSTRAINT valid_importance_score CHECK (importance_score >= 0.0 AND importance_score <= 1.0),
    CONSTRAINT valid_access_count CHECK (access_count >= 0)
);

-- Indexes per memory_context_entries
CREATE INDEX IF NOT EXISTS idx_memory_context_entries_workspace ON memory_context_entries (workspace_id);
CREATE INDEX IF NOT EXISTS idx_memory_context_entries_type ON memory_context_entries (context_type);
CREATE INDEX IF NOT EXISTS idx_memory_context_entries_importance ON memory_context_entries (importance_score DESC);
CREATE INDEX IF NOT EXISTS idx_memory_context_entries_semantic ON memory_context_entries (semantic_hash);
CREATE INDEX IF NOT EXISTS idx_memory_context_entries_created ON memory_context_entries (created_at DESC);

-- Table: memory_patterns
-- Purpose: Cross-domain learning patterns storage
CREATE TABLE IF NOT EXISTS memory_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_id VARCHAR(100) UNIQUE NOT NULL,
    pattern_type VARCHAR(100) NOT NULL,
    semantic_features JSONB NOT NULL DEFAULT '{}',
    success_indicators JSONB NOT NULL DEFAULT '[]',
    domain_context JSONB NOT NULL DEFAULT '{}',
    confidence DECIMAL(3,2) NOT NULL DEFAULT 0.5,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_confidence CHECK (confidence >= 0.0 AND confidence <= 1.0),
    CONSTRAINT valid_usage_count CHECK (usage_count >= 0)
);

-- Indexes per memory_patterns
CREATE INDEX IF NOT EXISTS idx_memory_patterns_type ON memory_patterns (pattern_type);
CREATE INDEX IF NOT EXISTS idx_memory_patterns_confidence ON memory_patterns (confidence DESC);
CREATE INDEX IF NOT EXISTS idx_memory_patterns_usage ON memory_patterns (usage_count DESC);
CREATE INDEX IF NOT EXISTS idx_memory_patterns_domain ON memory_patterns 
    USING GIN (domain_context);

-- Table: uma_performance_metrics
-- Purpose: Track UMA performance and health metrics
CREATE TABLE IF NOT EXISTS uma_performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID,
    metric_type VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    metric_metadata JSONB DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_metric_value CHECK (metric_value >= 0.0)
);

-- Indexes per uma_performance_metrics
CREATE INDEX IF NOT EXISTS idx_uma_performance_workspace ON uma_performance_metrics (workspace_id);
CREATE INDEX IF NOT EXISTS idx_uma_performance_type ON uma_performance_metrics (metric_type);
CREATE INDEX IF NOT EXISTS idx_uma_performance_recorded ON uma_performance_metrics (recorded_at DESC);

-- ========================================================================
-- 🔗 Integration con Existing Tables
-- ========================================================================

-- Ensure compatibility with enhanced goal-task linkage
-- (Il recente fix garantisce che task.goal_id sia sempre populated)

-- Add foreign key relationships where appropriate
ALTER TABLE memory_context_entries 
ADD CONSTRAINT fk_memory_context_workspace 
FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE;

-- ========================================================================
-- 🧹 Cleanup Functions
-- ========================================================================

-- Function: cleanup_expired_cache
-- Purpose: Remove expired cache entries automatically
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM memory_context_cache 
    WHERE expires_at < NOW();
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Log cleanup activity
    INSERT INTO uma_performance_metrics (metric_type, metric_value, metric_metadata)
    VALUES ('cache_cleanup', deleted_count, jsonb_build_object('cleanup_timestamp', NOW()));
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function: calculate_memory_health
-- Purpose: Calculate memory system health score
CREATE OR REPLACE FUNCTION calculate_memory_health(target_workspace_id UUID)
RETURNS DECIMAL(3,2) AS $$
DECLARE
    context_count INTEGER;
    avg_importance DECIMAL(3,2);
    pattern_count INTEGER;
    health_score DECIMAL(3,2);
BEGIN
    -- Get context metrics
    SELECT COUNT(*), COALESCE(AVG(importance_score), 0.0)
    INTO context_count, avg_importance
    FROM memory_context_entries
    WHERE workspace_id = target_workspace_id
    AND created_at > NOW() - INTERVAL '7 days';
    
    -- Get pattern metrics
    SELECT COUNT(*)
    INTO pattern_count
    FROM memory_patterns
    WHERE domain_context->>'workspace_id' = target_workspace_id::text;
    
    -- Calculate health score (weighted average)
    health_score := (
        LEAST(context_count / 10.0, 1.0) * 0.4 +
        avg_importance * 0.4 +
        LEAST(pattern_count / 5.0, 1.0) * 0.2
    );
    
    -- Record health metric
    INSERT INTO uma_performance_metrics (workspace_id, metric_type, metric_value, metric_metadata)
    VALUES (target_workspace_id, 'memory_health', health_score, 
            jsonb_build_object(
                'context_count', context_count,
                'avg_importance', avg_importance,
                'pattern_count', pattern_count
            ));
    
    RETURN health_score;
END;
$$ LANGUAGE plpgsql;

-- ========================================================================
-- 🕒 Scheduled Maintenance
-- ========================================================================

-- Note: These would typically be set up as cron jobs or scheduled tasks
-- For now, they're available as callable functions

-- Automatic cache cleanup (call every hour)
-- SELECT cleanup_expired_cache();

-- Health monitoring (call every day) 
-- SELECT calculate_memory_health(workspace_id) FROM workspaces WHERE status = 'active';

-- ========================================================================
-- 🎯 Views for UMA Insights
-- ========================================================================

-- View: memory_health_summary
-- Purpose: Provide quick health overview per workspace
CREATE OR REPLACE VIEW memory_health_summary AS
SELECT 
    w.id as workspace_id,
    w.name as workspace_name,
    COUNT(mce.id) as context_entries,
    COALESCE(AVG(mce.importance_score), 0.0) as avg_importance,
    COUNT(DISTINCT mce.context_type) as context_type_diversity,
    COUNT(mp.id) as learning_patterns,
    COALESCE(MAX(upm.metric_value), 0.0) as latest_health_score
FROM workspaces w
LEFT JOIN memory_context_entries mce ON w.id = mce.workspace_id 
    AND mce.created_at > NOW() - INTERVAL '7 days'
LEFT JOIN memory_patterns mp ON w.id::text = mp.domain_context->>'workspace_id'
LEFT JOIN uma_performance_metrics upm ON w.id = upm.workspace_id 
    AND upm.metric_type = 'memory_health'
    AND upm.recorded_at > NOW() - INTERVAL '1 day'
WHERE w.status = 'active'
GROUP BY w.id, w.name;

-- View: cache_performance_summary  
-- Purpose: Monitor cache performance metrics
CREATE OR REPLACE VIEW cache_performance_summary AS
SELECT 
    DATE_TRUNC('hour', created_at) as hour_bucket,
    COUNT(*) as entries_created,
    SUM(access_count) as total_accesses,
    ROUND(AVG(access_count), 2) as avg_accesses_per_entry,
    COUNT(CASE WHEN access_count > 1 THEN 1 END) as cache_hits,
    ROUND(
        COUNT(CASE WHEN access_count > 1 THEN 1 END)::DECIMAL / COUNT(*) * 100, 
        2
    ) as hit_rate_percentage
FROM memory_context_cache
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', created_at)
ORDER BY hour_bucket DESC;

-- ========================================================================
-- 🔐 Security & Access Control
-- ========================================================================

-- Add RLS (Row Level Security) policies if needed
-- ALTER TABLE memory_context_entries ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE memory_patterns ENABLE ROW LEVEL SECURITY;

-- Grant appropriate permissions
-- GRANT SELECT, INSERT, UPDATE, DELETE ON memory_context_cache TO authenticated;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON memory_context_entries TO authenticated;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON memory_patterns TO authenticated;
-- GRANT SELECT, INSERT, UPDATE ON uma_performance_metrics TO authenticated;

COMMENT ON TABLE memory_context_cache IS 'UMA: High-performance semantic cache for context retrieval';
COMMENT ON TABLE memory_context_entries IS 'UMA: Structured context storage with semantic features';  
COMMENT ON TABLE memory_patterns IS 'UMA: Cross-domain learning patterns storage';
COMMENT ON TABLE uma_performance_metrics IS 'UMA: Performance and health metrics tracking';

-- Success message
DO $$
BEGIN
    RAISE NOTICE '🧠 Universal Memory Architecture (UMA) tables created successfully!';
    RAISE NOTICE '✅ Enhanced memory system ready for AI-driven context resolution';
    RAISE NOTICE '🔗 Compatible with enhanced goal-task linkage system';
END $$;