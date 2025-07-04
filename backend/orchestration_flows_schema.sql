-- Orchestration Flows Database Schema
-- Creates tables for end-to-end flow tracking in AI Team Orchestrator

-- =====================================================
-- ORCHESTRATION FLOWS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS orchestration_flows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL,
    goal_id UUID,
    flow_type TEXT NOT NULL DEFAULT 'standard', -- standard, expedited, quality_focused
    initiated_by TEXT NOT NULL DEFAULT 'system', -- system, user, automated_goal_monitor
    current_stage TEXT NOT NULL DEFAULT 'GOAL_DECOMPOSITION', 
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused', 'completed', 'failed', 'cancelled')),
    
    -- Stage tracking
    stages_completed JSONB DEFAULT '[]'::JSONB,
    stages_failed JSONB DEFAULT '[]'::JSONB,
    stage_metadata JSONB DEFAULT '{}'::JSONB,
    
    -- Flow metrics
    total_tasks INTEGER DEFAULT 0,
    completed_tasks INTEGER DEFAULT 0,
    failed_tasks INTEGER DEFAULT 0,
    quality_score DECIMAL(5,3) DEFAULT 0.0,
    
    -- Timing information
    estimated_completion_time TIMESTAMP WITH TIME ZONE,
    actual_completion_time TIMESTAMP WITH TIME ZONE,
    stage_durations JSONB DEFAULT '{}'::JSONB,
    
    -- Metadata and context
    metadata JSONB DEFAULT '{}'::JSONB,
    error_details JSONB DEFAULT '{}'::JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Add foreign key constraint for workspace_id
    CONSTRAINT fk_orchestration_flows_workspace 
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

-- =====================================================
-- INTEGRATION EVENTS TABLE  
-- =====================================================
CREATE TABLE IF NOT EXISTS integration_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL,
    flow_id UUID, -- Optional link to orchestration flow
    
    -- Event details
    event_type TEXT NOT NULL, -- task_completed, quality_validated, asset_created, etc.
    source_component TEXT NOT NULL, -- executor, quality_gate, deliverable_pipeline, etc.
    target_component TEXT, -- unified_orchestrator, deliverable_pipeline, etc.
    
    -- Event data and processing
    event_data JSONB DEFAULT '{}'::JSONB,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- Processing information
    processed_at TIMESTAMP WITH TIME ZONE,
    processed_by TEXT,
    processing_duration_ms INTEGER,
    error_message TEXT,
    
    -- Priority and ordering
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10), -- 1=highest, 10=lowest
    sequence_number BIGSERIAL,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key constraints
    CONSTRAINT fk_integration_events_workspace 
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    CONSTRAINT fk_integration_events_flow 
        FOREIGN KEY (flow_id) REFERENCES orchestration_flows(id) ON DELETE SET NULL
);

-- =====================================================
-- COMPONENT HEALTH TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS component_health (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    component_name TEXT UNIQUE NOT NULL,
    
    -- Health status
    status TEXT NOT NULL DEFAULT 'unknown' CHECK (status IN ('healthy', 'degraded', 'unhealthy', 'stopped', 'unknown')),
    health_score DECIMAL(5,3) DEFAULT 0.0 CHECK (health_score >= 0.0 AND health_score <= 1.0),
    
    -- Monitoring data
    last_heartbeat TIMESTAMP WITH TIME ZONE,
    heartbeat_interval_seconds INTEGER DEFAULT 30,
    consecutive_failures INTEGER DEFAULT 0,
    last_error TEXT,
    last_success_at TIMESTAMP WITH TIME ZONE,
    
    -- Performance metrics
    avg_response_time_ms DECIMAL(10,2) DEFAULT 0.0,
    error_rate DECIMAL(5,3) DEFAULT 0.0,
    throughput_per_minute DECIMAL(10,2) DEFAULT 0.0,
    
    -- Configuration and metadata
    component_version TEXT,
    configuration JSONB DEFAULT '{}'::JSONB,
    metadata JSONB DEFAULT '{}'::JSONB,
    
    -- Dependencies
    dependencies TEXT[] DEFAULT '{}',
    dependent_components TEXT[] DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Orchestration Flows Indexes
CREATE INDEX IF NOT EXISTS idx_orchestration_flows_workspace_id ON orchestration_flows(workspace_id);
CREATE INDEX IF NOT EXISTS idx_orchestration_flows_status ON orchestration_flows(status);
CREATE INDEX IF NOT EXISTS idx_orchestration_flows_current_stage ON orchestration_flows(current_stage);
CREATE INDEX IF NOT EXISTS idx_orchestration_flows_created_at ON orchestration_flows(created_at);
CREATE INDEX IF NOT EXISTS idx_orchestration_flows_workspace_status ON orchestration_flows(workspace_id, status);

-- Integration Events Indexes
CREATE INDEX IF NOT EXISTS idx_integration_events_workspace_id ON integration_events(workspace_id);
CREATE INDEX IF NOT EXISTS idx_integration_events_status ON integration_events(status);
CREATE INDEX IF NOT EXISTS idx_integration_events_event_type ON integration_events(event_type);
CREATE INDEX IF NOT EXISTS idx_integration_events_created_at ON integration_events(created_at);
CREATE INDEX IF NOT EXISTS idx_integration_events_target_status ON integration_events(target_component, status);
CREATE INDEX IF NOT EXISTS idx_integration_events_flow_id ON integration_events(flow_id);
CREATE INDEX IF NOT EXISTS idx_integration_events_priority_sequence ON integration_events(priority ASC, sequence_number ASC);

-- Component Health Indexes
CREATE INDEX IF NOT EXISTS idx_component_health_status ON component_health(status);
CREATE INDEX IF NOT EXISTS idx_component_health_last_heartbeat ON component_health(last_heartbeat);
CREATE INDEX IF NOT EXISTS idx_component_health_component_name ON component_health(component_name);

-- =====================================================
-- TRIGGERS FOR AUTO-UPDATES
-- =====================================================

-- Update timestamps trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to tables
CREATE TRIGGER update_orchestration_flows_updated_at BEFORE UPDATE ON orchestration_flows 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_component_health_updated_at BEFORE UPDATE ON component_health 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- INITIAL DATA
-- =====================================================

-- Register core components in component_health
INSERT INTO component_health (component_name, status, metadata) VALUES
    ('unified_orchestrator', 'unknown', '{"description": "Main orchestration engine"}'),
    ('deliverable_pipeline', 'unknown', '{"description": "Deliverable generation pipeline"}'),
    ('executor', 'unknown', '{"description": "Task execution engine"}'),
    ('quality_gate', 'unknown', '{"description": "Quality validation system"}'),
    ('automatic_quality_trigger', 'unknown', '{"description": "Automated quality validation triggers"}'),
    ('memory_system', 'unknown', '{"description": "Context and memory management"}'),
    ('asset_requirements_generator', 'unknown', '{"description": "Asset requirement generation"}')
ON CONFLICT (component_name) DO NOTHING;

-- =====================================================
-- HELPFUL VIEWS
-- =====================================================

-- Active flows with current progress
CREATE OR REPLACE VIEW active_orchestration_flows AS
SELECT 
    f.id,
    f.workspace_id,
    f.goal_id,
    f.current_stage,
    f.progress_percentage,
    f.status,
    f.total_tasks,
    f.completed_tasks,
    f.quality_score,
    f.created_at,
    f.updated_at,
    EXTRACT(EPOCH FROM (NOW() - f.created_at))/3600 as hours_running
FROM orchestration_flows f
WHERE f.status IN ('active', 'paused');

-- Event processing queue
CREATE OR REPLACE VIEW pending_integration_events AS
SELECT 
    e.id,
    e.workspace_id,
    e.flow_id,
    e.event_type,
    e.source_component,
    e.target_component,
    e.priority,
    e.retry_count,
    e.created_at,
    EXTRACT(EPOCH FROM (NOW() - e.created_at))/60 as minutes_pending
FROM integration_events e
WHERE e.status = 'pending'
ORDER BY e.priority ASC, e.sequence_number ASC;

-- Component health summary
CREATE OR REPLACE VIEW component_health_summary AS
SELECT 
    component_name,
    status,
    health_score,
    last_heartbeat,
    consecutive_failures,
    error_rate,
    CASE 
        WHEN last_heartbeat IS NULL THEN 'Never contacted'
        WHEN last_heartbeat < NOW() - INTERVAL '5 minutes' THEN 'Stale'
        WHEN last_heartbeat < NOW() - INTERVAL '1 minute' THEN 'Recent'
        ELSE 'Current'
    END as heartbeat_status
FROM component_health
ORDER BY 
    CASE status 
        WHEN 'unhealthy' THEN 1
        WHEN 'degraded' THEN 2 
        WHEN 'unknown' THEN 3
        WHEN 'stopped' THEN 4
        WHEN 'healthy' THEN 5
    END,
    component_name;

-- =====================================================
-- COMMENTS
-- =====================================================

COMMENT ON TABLE orchestration_flows IS 'Tracks end-to-end orchestration flows from goal to deliverable completion';
COMMENT ON TABLE integration_events IS 'Event-driven communication between system components';
COMMENT ON TABLE component_health IS 'Health monitoring and status tracking for system components';

COMMENT ON COLUMN orchestration_flows.current_stage IS 'Current stage: GOAL_DECOMPOSITION, TASK_GENERATION, TASK_EXECUTION, QUALITY_VALIDATION, ASSET_CREATION, DELIVERABLE_GENERATION, COMPLETED';
COMMENT ON COLUMN integration_events.priority IS 'Event priority: 1=highest (critical), 5=normal, 10=lowest (background)';
COMMENT ON COLUMN component_health.health_score IS 'Health score from 0.0 (completely unhealthy) to 1.0 (perfectly healthy)';

-- Final success message
DO $$
BEGIN
    RAISE NOTICE 'Orchestration Flows schema created successfully!';
    RAISE NOTICE 'Tables created: orchestration_flows, integration_events, component_health';
    RAISE NOTICE 'Views created: active_orchestration_flows, pending_integration_events, component_health_summary';
    RAISE NOTICE 'Ready for end-to-end flow tracking!';
END
$$;