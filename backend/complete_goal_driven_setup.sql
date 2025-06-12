-- 🎯 COMPLETE GOAL-DRIVEN SYSTEM DATABASE SETUP
-- Execute these SQL statements in Supabase SQL Editor in order

-- ============================================
-- 1️⃣ WORKSPACE GOALS TABLE (Step 1: Goal Decomposition)
-- ============================================

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

-- ============================================
-- 2️⃣ WORKSPACE INSIGHTS TABLE (Memory System)
-- ============================================

CREATE TABLE IF NOT EXISTS workspace_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    agent_role TEXT NOT NULL,
    insight_type TEXT NOT NULL CHECK (insight_type IN ('success_pattern', 'failure_lesson', 'discovery', 'constraint', 'optimization')),
    content TEXT NOT NULL CHECK (length(content) >= 5 AND length(content) <= 200),
    relevance_tags TEXT[] DEFAULT '{}',
    confidence_score DECIMAL(3,2) DEFAULT 1.0 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for workspace_insights
CREATE INDEX idx_workspace_insights_workspace_id ON workspace_insights(workspace_id);
CREATE INDEX idx_workspace_insights_task_id ON workspace_insights(task_id) WHERE task_id IS NOT NULL;
CREATE INDEX idx_workspace_insights_type ON workspace_insights(insight_type);
CREATE INDEX idx_workspace_insights_expires ON workspace_insights(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX idx_workspace_insights_tags ON workspace_insights USING GIN(relevance_tags);
CREATE INDEX idx_workspace_insights_created ON workspace_insights(created_at DESC);

-- Enable RLS
ALTER TABLE workspace_insights ENABLE ROW LEVEL SECURITY;

-- Anti-pollution: Limit insights per workspace
CREATE OR REPLACE FUNCTION check_workspace_insight_limit()
RETURNS TRIGGER AS $$
DECLARE
    insight_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO insight_count 
    FROM workspace_insights 
    WHERE workspace_id = NEW.workspace_id;
    
    IF insight_count >= 100 THEN
        -- Delete oldest insights if limit reached
        DELETE FROM workspace_insights
        WHERE workspace_id = NEW.workspace_id
        AND id IN (
            SELECT id FROM workspace_insights
            WHERE workspace_id = NEW.workspace_id
            ORDER BY created_at ASC
            LIMIT 10
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_workspace_insight_limit
    BEFORE INSERT ON workspace_insights
    FOR EACH ROW
    EXECUTE FUNCTION check_workspace_insight_limit();

-- ============================================
-- 3️⃣ GOAL-DRIVEN TASK FIELDS (Step 2: Task Planner)
-- ============================================

-- Add goal-driven columns to tasks table
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS goal_id UUID REFERENCES workspace_goals(id) ON DELETE SET NULL;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS metric_type TEXT;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS contribution_expected DECIMAL(10,2);
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS numerical_target JSONB DEFAULT '{}';
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS is_corrective BOOLEAN DEFAULT FALSE;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS success_criteria JSONB DEFAULT '[]';

-- Add constraints
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS check_metric_type;
ALTER TABLE tasks ADD CONSTRAINT check_metric_type 
    CHECK (metric_type IS NULL OR metric_type IN (
        'contacts', 'email_sequences', 'content_pieces', 'campaigns',
        'revenue', 'conversion_rate', 'engagement_rate', 'quality_score',
        'deliverables', 'tasks_completed', 'timeline_days'
    ));

ALTER TABLE tasks DROP CONSTRAINT IF EXISTS check_contribution_expected;
ALTER TABLE tasks ADD CONSTRAINT check_contribution_expected
    CHECK (contribution_expected IS NULL OR contribution_expected >= 0);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_tasks_goal_id ON tasks(goal_id) WHERE goal_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_metric_type ON tasks(metric_type) WHERE metric_type IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_corrective ON tasks(is_corrective) WHERE is_corrective = TRUE;
CREATE INDEX IF NOT EXISTS idx_tasks_goal_status ON tasks(goal_id, status) WHERE goal_id IS NOT NULL;

-- ============================================
-- 4️⃣ TASK COMPLETION VALIDATION FUNCTIONS
-- ============================================

-- Function to validate task completion against numerical targets
CREATE OR REPLACE FUNCTION validate_task_numerical_target(
    task_id UUID,
    completed_result JSONB
) RETURNS BOOLEAN AS $$
DECLARE
    task_record RECORD;
    target_config JSONB;
    actual_value DECIMAL;
    target_value DECIMAL;
BEGIN
    -- Get task with numerical target
    SELECT * INTO task_record 
    FROM tasks 
    WHERE id = task_id AND numerical_target IS NOT NULL;
    
    IF NOT FOUND THEN
        RETURN TRUE; -- No numerical validation needed
    END IF;
    
    target_config := task_record.numerical_target;
    
    -- Extract target value
    target_value := (target_config->>'target')::DECIMAL;
    
    -- Extract actual value from result based on metric type
    CASE task_record.metric_type
        WHEN 'contacts' THEN
            -- Count contacts in result
            actual_value := COALESCE(
                jsonb_array_length(completed_result->'contacts'),
                jsonb_array_length(completed_result->'actionable_assets'->'contact_database'->'data'->'contacts'),
                0
            );
        WHEN 'email_sequences' THEN
            -- Count email sequences
            actual_value := COALESCE(
                jsonb_array_length(completed_result->'email_sequences'),
                jsonb_array_length(completed_result->'actionable_assets'->'email_templates'->'data'->'email_sequences'),
                0
            );
        WHEN 'content_pieces' THEN
            -- Count content pieces
            actual_value := COALESCE(
                jsonb_array_length(completed_result->'content_pieces'),
                jsonb_array_length(completed_result->'content_calendar'),
                0
            );
        ELSE
            -- Generic numerical extraction
            actual_value := COALESCE(
                (completed_result->target_config->>'metric')::DECIMAL,
                0
            );
    END CASE;
    
    -- Validate achievement
    RETURN actual_value >= target_value;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 5️⃣ AUTOMATIC GOAL PROGRESS UPDATE
-- ============================================

-- Function to update workspace goal progress when task completes
CREATE OR REPLACE FUNCTION update_goal_progress_on_task_completion()
RETURNS TRIGGER AS $$
DECLARE
    actual_contribution DECIMAL;
    target_config JSONB;
BEGIN
    -- Only process when task status changes to completed
    IF NEW.status = 'completed' AND OLD.status != 'completed' AND NEW.goal_id IS NOT NULL THEN
        
        -- Calculate actual contribution from task result
        IF NEW.numerical_target IS NOT NULL AND NEW.result IS NOT NULL THEN
            -- Use validation function to get actual value
            SELECT CASE NEW.metric_type
                WHEN 'contacts' THEN COALESCE(
                    jsonb_array_length(NEW.result->'contacts'),
                    jsonb_array_length(NEW.result->'actionable_assets'->'contact_database'->'data'->'contacts'),
                    NEW.contribution_expected
                )
                WHEN 'email_sequences' THEN COALESCE(
                    jsonb_array_length(NEW.result->'email_sequences'),
                    jsonb_array_length(NEW.result->'actionable_assets'->'email_templates'->'data'->'email_sequences'),
                    NEW.contribution_expected
                )
                WHEN 'content_pieces' THEN COALESCE(
                    jsonb_array_length(NEW.result->'content_pieces'),
                    jsonb_array_length(NEW.result->'content_calendar'),
                    NEW.contribution_expected
                )
                ELSE NEW.contribution_expected
            END INTO actual_contribution;
        ELSE
            actual_contribution := COALESCE(NEW.contribution_expected, 0);
        END IF;
        
        -- Update workspace goal current_value
        UPDATE workspace_goals 
        SET 
            current_value = current_value + actual_contribution,
            updated_at = NOW()
        WHERE id = NEW.goal_id;
        
        -- Log the progress update
        INSERT INTO logs (workspace_id, agent_id, type, message, metadata, created_at)
        VALUES (
            NEW.workspace_id,
            NEW.agent_id,
            'system',
            'Goal progress updated from task completion',
            jsonb_build_object(
                'task_id', NEW.id,
                'task_name', NEW.name,
                'goal_id', NEW.goal_id,
                'metric_type', NEW.metric_type,
                'contribution', actual_contribution,
                'expected_contribution', NEW.contribution_expected
            ),
            NOW()
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic goal progress updates
DROP TRIGGER IF EXISTS trigger_update_goal_progress ON tasks;
CREATE TRIGGER trigger_update_goal_progress
    AFTER UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_goal_progress_on_task_completion();

-- ============================================
-- 6️⃣ ANALYSIS VIEWS
-- ============================================

-- View for goal-driven task analysis
CREATE OR REPLACE VIEW goal_driven_tasks_analysis AS
SELECT 
    t.id,
    t.name,
    t.status,
    t.metric_type,
    t.contribution_expected,
    t.is_corrective,
    t.created_at,
    t.updated_at,
    
    -- Goal information
    wg.id as goal_id,
    wg.target_value as goal_target,
    wg.current_value as goal_current,
    wg.completion_percentage as goal_completion_pct,
    
    -- Task effectiveness
    CASE 
        WHEN t.status = 'completed' AND t.numerical_target IS NOT NULL THEN
            validate_task_numerical_target(t.id, t.result)
        ELSE NULL
    END as meets_numerical_target,
    
    -- Progress contribution
    CASE 
        WHEN t.status = 'completed' THEN
            ROUND((t.contribution_expected / wg.target_value * 100), 2)
        ELSE 0
    END as progress_contribution_pct
    
FROM tasks t
LEFT JOIN workspace_goals wg ON t.goal_id = wg.id
WHERE t.goal_id IS NOT NULL;

-- Performance view for goal-driven task monitoring
CREATE OR REPLACE VIEW goal_task_performance AS
SELECT 
    wg.workspace_id,
    wg.metric_type,
    wg.target_value,
    wg.current_value,
    wg.completion_percentage,
    
    -- Task counts
    COUNT(t.id) as total_tasks,
    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks,
    COUNT(CASE WHEN t.status = 'in_progress' THEN 1 END) as active_tasks,
    COUNT(CASE WHEN t.is_corrective = TRUE THEN 1 END) as corrective_tasks,
    
    -- Contribution analysis
    SUM(CASE WHEN t.status = 'completed' THEN t.contribution_expected ELSE 0 END) as total_contribution,
    AVG(CASE WHEN t.status = 'completed' THEN t.contribution_expected ELSE NULL END) as avg_task_contribution,
    
    -- Effectiveness
    ROUND(
        COUNT(CASE WHEN t.status = 'completed' THEN 1 END)::DECIMAL / 
        NULLIF(COUNT(t.id), 0) * 100, 
        1
    ) as task_completion_rate,
    
    wg.last_validation_at,
    wg.needs_validation
    
FROM workspace_goals wg
LEFT JOIN tasks t ON wg.id = t.goal_id
WHERE wg.status = 'active'
GROUP BY wg.id, wg.workspace_id, wg.metric_type, wg.target_value, wg.current_value, 
         wg.completion_percentage, wg.last_validation_at, wg.needs_validation;

-- ============================================
-- 7️⃣ COMMENTS FOR DOCUMENTATION
-- ============================================

COMMENT ON TABLE workspace_goals IS 'Explicit goal decomposition for goal-driven task generation';
COMMENT ON COLUMN workspace_goals.metric_type IS 'Type of measurable metric (contacts, email_sequences, etc.)';
COMMENT ON COLUMN workspace_goals.target_value IS 'Numerical target to achieve';
COMMENT ON COLUMN workspace_goals.current_value IS 'Current progress towards target';
COMMENT ON COLUMN workspace_goals.success_criteria IS 'JSONB with specific criteria for goal completion';
COMMENT ON VIEW workspace_goals_progress IS 'Real-time view of goal progress and validation needs';

COMMENT ON TABLE workspace_insights IS 'Memory system for workspace learnings and insights';
COMMENT ON COLUMN workspace_insights.insight_type IS 'Type of insight (success_pattern, failure_lesson, etc.)';
COMMENT ON COLUMN workspace_insights.relevance_tags IS 'Tags for filtering and context relevance';

COMMENT ON FUNCTION validate_task_numerical_target IS 'Validates if completed task meets its numerical target';
COMMENT ON FUNCTION update_goal_progress_on_task_completion IS 'Automatically updates workspace goal progress when tasks complete';
COMMENT ON VIEW goal_driven_tasks_analysis IS 'Analysis of individual goal-driven tasks and their effectiveness';
COMMENT ON VIEW goal_task_performance IS 'Performance metrics for goal-driven task execution';

-- ============================================
-- 8️⃣ RLS POLICIES (Adjust based on your auth setup)
-- ============================================

-- Basic RLS policies for workspace_goals
CREATE POLICY "Users can view their workspace goals" ON workspace_goals
    FOR SELECT USING (
        workspace_id IN (
            SELECT id FROM workspaces WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert goals for their workspaces" ON workspace_goals
    FOR INSERT WITH CHECK (
        workspace_id IN (
            SELECT id FROM workspaces WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update their workspace goals" ON workspace_goals
    FOR UPDATE USING (
        workspace_id IN (
            SELECT id FROM workspaces WHERE user_id = auth.uid()
        )
    );

-- Basic RLS policies for workspace_insights
CREATE POLICY "Users can view insights for their workspaces" ON workspace_insights
    FOR SELECT USING (
        workspace_id IN (
            SELECT id FROM workspaces WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "System can insert insights" ON workspace_insights
    FOR INSERT WITH CHECK (true); -- Allow system to insert insights

-- ============================================
-- 🎉 SETUP COMPLETE!
-- ============================================

-- Test the setup by checking tables
SELECT 
    'workspace_goals' as table_name, 
    COUNT(*) as row_count 
FROM workspace_goals
UNION ALL
SELECT 
    'workspace_insights' as table_name, 
    COUNT(*) as row_count 
FROM workspace_insights;