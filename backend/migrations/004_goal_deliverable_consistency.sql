-- Migration: Goal-Deliverable Consistency Triggers
-- Date: 2025-09-06
-- Purpose: Ensure data consistency between goals, deliverables, and tasks

-- =====================================================
-- 1. Add missing columns if they don't exist
-- =====================================================

-- Add goal_id to ai_generated_assets if missing
ALTER TABLE ai_generated_assets 
ADD COLUMN IF NOT EXISTS goal_id UUID REFERENCES workspace_goals(id) ON DELETE SET NULL;

-- Add last_sync_at to workspace_goals for tracking sync status
ALTER TABLE workspace_goals
ADD COLUMN IF NOT EXISTS last_sync_at TIMESTAMP WITH TIME ZONE;

-- Add is_critical flag to tasks for priority weighting
ALTER TABLE tasks
ADD COLUMN IF NOT EXISTS is_critical BOOLEAN DEFAULT FALSE;

-- =====================================================
-- 2. Create function to auto-update goal progress
-- =====================================================

CREATE OR REPLACE FUNCTION update_goal_progress_on_deliverable_change()
RETURNS TRIGGER AS $$
DECLARE
    v_goal_id UUID;
    v_workspace_id UUID;
    v_total_deliverables INTEGER;
    v_completed_deliverables INTEGER;
    v_new_progress FLOAT;
BEGIN
    -- Get goal_id and workspace_id from the deliverable
    IF TG_OP = 'UPDATE' THEN
        v_goal_id := NEW.goal_id;
        v_workspace_id := NEW.workspace_id;
    ELSIF TG_OP = 'INSERT' THEN
        v_goal_id := NEW.goal_id;
        v_workspace_id := NEW.workspace_id;
    ELSIF TG_OP = 'DELETE' THEN
        v_goal_id := OLD.goal_id;
        v_workspace_id := OLD.workspace_id;
    END IF;
    
    -- Skip if no goal_id
    IF v_goal_id IS NULL THEN
        RETURN NEW;
    END IF;
    
    -- Calculate total and completed deliverables for the goal
    SELECT 
        COUNT(*),
        COUNT(CASE WHEN status IN ('completed', 'approved', 'delivered') THEN 1 END)
    INTO v_total_deliverables, v_completed_deliverables
    FROM ai_generated_assets
    WHERE goal_id = v_goal_id
    AND workspace_id = v_workspace_id;
    
    -- Calculate new progress percentage
    IF v_total_deliverables > 0 THEN
        v_new_progress := (v_completed_deliverables::FLOAT / v_total_deliverables::FLOAT) * 100;
    ELSE
        v_new_progress := 0;
    END IF;
    
    -- Update goal progress
    UPDATE workspace_goals
    SET 
        progress = v_new_progress,
        last_sync_at = NOW(),
        updated_at = NOW(),
        status = CASE 
            WHEN v_new_progress >= 100 THEN 'completed'
            WHEN v_new_progress > 0 THEN 'in_progress'
            ELSE status
        END
    WHERE id = v_goal_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 3. Create trigger for deliverable changes
-- =====================================================

DROP TRIGGER IF EXISTS trigger_update_goal_on_deliverable_change ON ai_generated_assets;

CREATE TRIGGER trigger_update_goal_on_deliverable_change
AFTER INSERT OR UPDATE OF status OR DELETE ON ai_generated_assets
FOR EACH ROW
EXECUTE FUNCTION update_goal_progress_on_deliverable_change();

-- =====================================================
-- 4. Create function to ensure goal has tasks
-- =====================================================

CREATE OR REPLACE FUNCTION ensure_goal_has_tasks()
RETURNS TRIGGER AS $$
DECLARE
    v_task_count INTEGER;
BEGIN
    -- Only check for active goals with 0% progress
    IF NEW.status = 'active' AND NEW.progress <= 0 THEN
        -- Count tasks for this goal
        SELECT COUNT(*)
        INTO v_task_count
        FROM tasks
        WHERE goal_id = NEW.id
        AND workspace_id = NEW.workspace_id;
        
        -- If no tasks exist, log for monitoring
        IF v_task_count = 0 THEN
            -- Insert monitoring record (requires monitoring table)
            INSERT INTO goal_validation_log (
                goal_id,
                workspace_id,
                validation_type,
                message,
                created_at
            ) VALUES (
                NEW.id,
                NEW.workspace_id,
                'NO_TASKS',
                'Goal has 0% progress and no tasks - needs validation',
                NOW()
            ) ON CONFLICT DO NOTHING;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 5. Create monitoring table for goal validation
-- =====================================================

CREATE TABLE IF NOT EXISTS goal_validation_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID REFERENCES workspace_goals(id) ON DELETE CASCADE,
    workspace_id UUID NOT NULL,
    validation_type VARCHAR(50) NOT NULL,
    message TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(goal_id, validation_type, created_at)
);

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_goal_validation_log_unresolved 
ON goal_validation_log(workspace_id, resolved) 
WHERE resolved = FALSE;

-- =====================================================
-- 6. Create trigger for goal validation
-- =====================================================

DROP TRIGGER IF EXISTS trigger_ensure_goal_has_tasks ON workspace_goals;

CREATE TRIGGER trigger_ensure_goal_has_tasks
AFTER INSERT OR UPDATE OF status, progress ON workspace_goals
FOR EACH ROW
EXECUTE FUNCTION ensure_goal_has_tasks();

-- =====================================================
-- 7. Create function to link orphaned deliverables
-- =====================================================

CREATE OR REPLACE FUNCTION link_orphaned_deliverables_to_goals()
RETURNS INTEGER AS $$
DECLARE
    v_linked_count INTEGER := 0;
    v_deliverable RECORD;
    v_best_goal_id UUID;
BEGIN
    -- Find deliverables without goal_id
    FOR v_deliverable IN 
        SELECT id, workspace_id, name, metadata
        FROM ai_generated_assets
        WHERE goal_id IS NULL
        AND workspace_id IS NOT NULL
    LOOP
        -- Try to find matching goal based on metadata or name
        SELECT id INTO v_best_goal_id
        FROM workspace_goals
        WHERE workspace_id = v_deliverable.workspace_id
        AND status = 'active'
        AND (
            -- Check if deliverable name contains goal description
            v_deliverable.name ILIKE '%' || SUBSTRING(description, 1, 20) || '%'
            OR
            -- Check metadata for goal reference
            v_deliverable.metadata::text ILIKE '%' || id::text || '%'
        )
        LIMIT 1;
        
        -- Update deliverable with goal_id if found
        IF v_best_goal_id IS NOT NULL THEN
            UPDATE ai_generated_assets
            SET goal_id = v_best_goal_id
            WHERE id = v_deliverable.id;
            
            v_linked_count := v_linked_count + 1;
        END IF;
    END LOOP;
    
    RETURN v_linked_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 8. Create scheduled job for consistency checks
-- =====================================================

-- Note: This requires pg_cron extension or external scheduler
-- Uncomment if pg_cron is available:

-- SELECT cron.schedule(
--     'goal-deliverable-consistency-check',
--     '*/15 * * * *',  -- Every 15 minutes
--     $$
--     SELECT link_orphaned_deliverables_to_goals();
--     
--     -- Clean up old resolved validation logs
--     DELETE FROM goal_validation_log
--     WHERE resolved = TRUE
--     AND resolved_at < NOW() - INTERVAL '7 days';
--     $$
-- );

-- =====================================================
-- 9. Initial data consistency fix
-- =====================================================

-- Link orphaned deliverables
SELECT link_orphaned_deliverables_to_goals();

-- Recalculate all goal progress based on current deliverables
UPDATE workspace_goals g
SET 
    progress = COALESCE((
        SELECT (COUNT(CASE WHEN a.status IN ('completed', 'approved', 'delivered') THEN 1 END)::FLOAT / 
                NULLIF(COUNT(*)::FLOAT, 0)) * 100
        FROM ai_generated_assets a
        WHERE a.goal_id = g.id
        AND a.workspace_id = g.workspace_id
    ), 0),
    last_sync_at = NOW(),
    updated_at = NOW()
WHERE EXISTS (
    SELECT 1 FROM ai_generated_assets 
    WHERE goal_id = g.id
);

-- =====================================================
-- 10. Create view for goal-deliverable summary
-- =====================================================

CREATE OR REPLACE VIEW goal_deliverable_summary AS
SELECT 
    g.id AS goal_id,
    g.workspace_id,
    g.description AS goal_description,
    g.status AS goal_status,
    g.progress AS goal_progress,
    COUNT(a.id) AS total_deliverables,
    COUNT(CASE WHEN a.status IN ('completed', 'approved', 'delivered') THEN 1 END) AS completed_deliverables,
    COUNT(CASE WHEN a.status = 'in_progress' THEN 1 END) AS in_progress_deliverables,
    COUNT(CASE WHEN a.status IN ('pending', 'planned') THEN 1 END) AS pending_deliverables,
    g.last_sync_at,
    MAX(a.updated_at) AS last_deliverable_update
FROM workspace_goals g
LEFT JOIN ai_generated_assets a ON a.goal_id = g.id AND a.workspace_id = g.workspace_id
GROUP BY g.id, g.workspace_id, g.description, g.status, g.progress, g.last_sync_at;

-- Create index for the view
CREATE INDEX IF NOT EXISTS idx_ai_generated_assets_goal_workspace 
ON ai_generated_assets(goal_id, workspace_id, status);

-- =====================================================
-- Migration Complete
-- =====================================================

-- Add migration record
INSERT INTO schema_migrations (version, description, applied_at)
VALUES (
    '004',
    'Goal-Deliverable Consistency Triggers',
    NOW()
) ON CONFLICT (version) DO NOTHING;