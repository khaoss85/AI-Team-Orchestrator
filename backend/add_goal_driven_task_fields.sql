-- Add goal-driven fields to tasks table for Step 2: Goal-Driven Task Planner
-- This connects tasks to specific workspace goals with numerical targets

-- Add goal-driven columns to tasks table
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS goal_id UUID REFERENCES workspace_goals(id) ON DELETE SET NULL;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS metric_type TEXT;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS contribution_expected DECIMAL(10,2);
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS numerical_target JSONB DEFAULT '{}';
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS is_corrective BOOLEAN DEFAULT FALSE;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS success_criteria JSONB DEFAULT '[]';

-- Add constraints
ALTER TABLE tasks ADD CONSTRAINT check_metric_type 
    CHECK (metric_type IS NULL OR metric_type IN (
        'contacts', 'email_sequences', 'content_pieces', 'campaigns',
        'revenue', 'conversion_rate', 'engagement_rate', 'quality_score',
        'deliverables', 'tasks_completed', 'timeline_days'
    ));

ALTER TABLE tasks ADD CONSTRAINT check_contribution_expected
    CHECK (contribution_expected IS NULL OR contribution_expected >= 0);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_tasks_goal_id ON tasks(goal_id) WHERE goal_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_metric_type ON tasks(metric_type) WHERE metric_type IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_corrective ON tasks(is_corrective) WHERE is_corrective = TRUE;
CREATE INDEX IF NOT EXISTS idx_tasks_goal_status ON tasks(goal_id, status) WHERE goal_id IS NOT NULL;

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

COMMENT ON FUNCTION validate_task_numerical_target IS 'Validates if completed task meets its numerical target';
COMMENT ON FUNCTION update_goal_progress_on_task_completion IS 'Automatically updates workspace goal progress when tasks complete';
COMMENT ON VIEW goal_driven_tasks_analysis IS 'Analysis of individual goal-driven tasks and their effectiveness';
COMMENT ON VIEW goal_task_performance IS 'Performance metrics for goal-driven task execution';