-- Create workspace_goals table for explicit goal decomposition
-- This enables goal-driven task generation and numerical target tracking

CREATE TABLE IF NOT EXISTS workspace_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    
    -- Goal definition
    metric_type TEXT NOT NULL CHECK (metric_type IN (
        'contacts', 'email_sequences', 'content_pieces', 'campaigns',
        'revenue', 'conversion_rate', 'engagement_rate', 'quality_score',
        'deliverables', 'tasks_completed', 'timeline_days'
    )),
    target_value DECIMAL(10,2) NOT NULL CHECK (target_value > 0),
    current_value DECIMAL(10,2) DEFAULT 0,
    unit TEXT DEFAULT '',
    
    -- Priority and status
    priority INTEGER DEFAULT 1 CHECK (priority BETWEEN 1 AND 5),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'paused', 'cancelled')),
    
    -- Success criteria and metadata
    success_criteria JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    -- Goal context
    description TEXT,
    source_goal_text TEXT, -- Original workspace goal text
    
    -- Tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Performance tracking
    last_validation_at TIMESTAMP WITH TIME ZONE,
    validation_frequency_minutes INTEGER DEFAULT 20,
    
    -- Constraints
    UNIQUE(workspace_id, metric_type) -- One goal per metric type per workspace
);

-- Create indexes for performance
CREATE INDEX idx_workspace_goals_workspace_id ON workspace_goals(workspace_id);
CREATE INDEX idx_workspace_goals_status ON workspace_goals(status);
CREATE INDEX idx_workspace_goals_priority ON workspace_goals(priority DESC);
CREATE INDEX idx_workspace_goals_metric_type ON workspace_goals(metric_type);
CREATE INDEX idx_workspace_goals_validation ON workspace_goals(last_validation_at, status) WHERE status = 'active';

-- Add RLS for security
ALTER TABLE workspace_goals ENABLE ROW LEVEL SECURITY;

-- Create update timestamp trigger
CREATE OR REPLACE FUNCTION update_workspace_goals_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    
    -- Auto-complete goal if target reached
    IF NEW.current_value >= NEW.target_value AND OLD.status = 'active' THEN
        NEW.status = 'completed';
        NEW.completed_at = NOW();
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_workspace_goals_timestamp
    BEFORE UPDATE ON workspace_goals
    FOR EACH ROW
    EXECUTE FUNCTION update_workspace_goals_timestamp();

-- Create validation tracking function
CREATE OR REPLACE FUNCTION mark_goal_validated(goal_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE workspace_goals 
    SET last_validation_at = NOW()
    WHERE id = goal_id;
END;
$$ LANGUAGE plpgsql;

-- Sample goal decomposition for testing
INSERT INTO workspace_goals (workspace_id, metric_type, target_value, unit, description, source_goal_text) VALUES
-- Example for "50 contatti ICP" goal
-- (uuid_generate_v4(), 'contacts', 50, 'contacts', 'Collect 50 ICP contacts (CMO/CTO di aziende SaaS europee)', 'Raccogliere 50 contatti ICP (CMO/CTO di aziende SaaS europee) in 6 settimane'),
-- (uuid_generate_v4(), 'email_sequences', 3, 'sequences', 'Create 3 email sequences for B2B outreach', 'Creare 3 sequenze email per B2B outreach con ≥30% open rate')
ON CONFLICT DO NOTHING;

-- View for goal progress tracking
CREATE OR REPLACE VIEW workspace_goals_progress AS
SELECT 
    wg.*,
    ROUND((current_value / target_value * 100), 1) as completion_percentage,
    (target_value - current_value) as remaining_value,
    CASE 
        WHEN current_value >= target_value THEN 'completed'
        WHEN current_value >= target_value * 0.8 THEN 'near_completion'
        WHEN current_value >= target_value * 0.5 THEN 'in_progress'
        WHEN current_value > 0 THEN 'started'
        ELSE 'not_started'
    END as progress_status,
    CASE 
        WHEN last_validation_at IS NULL THEN true
        WHEN last_validation_at < NOW() - INTERVAL '1 minute' * validation_frequency_minutes THEN true
        ELSE false
    END as needs_validation
FROM workspace_goals wg
WHERE status = 'active';

COMMENT ON TABLE workspace_goals IS 'Explicit goal decomposition for goal-driven task generation';
COMMENT ON COLUMN workspace_goals.metric_type IS 'Type of measurable metric (contacts, email_sequences, etc.)';
COMMENT ON COLUMN workspace_goals.target_value IS 'Numerical target to achieve';
COMMENT ON COLUMN workspace_goals.current_value IS 'Current progress towards target';
COMMENT ON COLUMN workspace_goals.success_criteria IS 'JSONB with specific criteria for goal completion';
COMMENT ON VIEW workspace_goals_progress IS 'Real-time view of goal progress and validation needs';