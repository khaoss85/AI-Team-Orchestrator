-- =====================================================
-- 🧠 AUTHENTIC THINKING PROCESS DATABASE SCHEMA
-- =====================================================
-- Tabelle per supportare il thinking process autentico
-- basato sulla vera todo list derivata dal goal decomposition

-- 1. Goal Decomposition Storage Table
CREATE TABLE IF NOT EXISTS workspace_goal_decompositions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID NOT NULL REFERENCES workspace_goals(id) ON DELETE CASCADE,
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    
    -- Decomposition metadata
    decomposition_method TEXT NOT NULL CHECK (decomposition_method IN ('ai', 'fallback', 'emergency')),
    user_value_score INTEGER NOT NULL CHECK (user_value_score >= 0 AND user_value_score <= 100),
    complexity_level TEXT NOT NULL CHECK (complexity_level IN ('simple', 'medium', 'complex')),
    domain_category TEXT NOT NULL CHECK (domain_category IN ('universal', 'specific')),
    
    -- Asset deliverables (structured data)
    asset_deliverables JSONB NOT NULL DEFAULT '[]',
    thinking_components JSONB NOT NULL DEFAULT '[]',
    completion_criteria JSONB NOT NULL DEFAULT '{}',
    pillar_adherence JSONB NOT NULL DEFAULT '{}',
    
    -- Tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure one decomposition per goal
    UNIQUE(goal_id)
);

-- 2. Todo List Storage Tables
CREATE TABLE IF NOT EXISTS goal_todos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decomposition_id UUID NOT NULL REFERENCES workspace_goal_decompositions(id) ON DELETE CASCADE,
    goal_id UUID NOT NULL REFERENCES workspace_goals(id) ON DELETE CASCADE,
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    
    -- Todo identification
    todo_type TEXT NOT NULL CHECK (todo_type IN ('asset', 'thinking')),
    internal_id TEXT NOT NULL, -- asset_1, thinking_1, etc.
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    
    -- Todo properties
    priority TEXT NOT NULL CHECK (priority IN ('low', 'medium', 'high')),
    estimated_effort TEXT CHECK (estimated_effort IN ('low', 'medium', 'high')),
    user_impact TEXT CHECK (user_impact IN ('immediate', 'short-term', 'long-term')),
    complexity TEXT CHECK (complexity IN ('simple', 'medium', 'complex')),
    
    -- Asset-specific fields (NULL for thinking todos)
    value_proposition TEXT,
    completion_criteria TEXT,
    deliverable_type TEXT CHECK (deliverable_type IN ('concrete_asset', 'strategic_thinking')),
    
    -- Thinking-specific fields (NULL for asset todos)
    supports_assets TEXT[], -- Array of asset names this thinking supports
    
    -- Progress tracking
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'blocked')),
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    
    -- Task linkage
    linked_task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    
    -- Tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    UNIQUE(decomposition_id, internal_id)
);

-- 3. Authentic Thinking Process Tracking
CREATE TABLE IF NOT EXISTS thinking_process_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    todo_id UUID NOT NULL REFERENCES goal_todos(id) ON DELETE CASCADE,
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    
    -- Thinking session grouping
    thinking_session_id UUID NOT NULL,
    
    -- Process identification
    step_sequence INTEGER NOT NULL, -- Order of thinking steps
    step_type TEXT NOT NULL CHECK (step_type IN (
        'analysis', 'research', 'planning', 'evaluation', 
        'decision', 'synthesis', 'validation', 'reflection'
    )),
    
    -- Actual thinking content (not metadata)
    step_title TEXT NOT NULL,
    thinking_content TEXT NOT NULL, -- The actual reasoning/analysis
    inputs_considered TEXT[] DEFAULT '{}', -- What was considered
    conclusions_reached TEXT[] DEFAULT '{}', -- What was concluded
    decisions_made TEXT[] DEFAULT '{}', -- What decisions were made
    next_steps_identified TEXT[] DEFAULT '{}', -- What next steps were identified
    
    -- Authenticity markers
    agent_role TEXT NOT NULL, -- Which agent type did the thinking
    model_used TEXT DEFAULT 'gpt-4o-mini', -- Which AI model generated this thinking
    confidence_level TEXT DEFAULT 'high' CHECK (confidence_level IN ('low', 'medium', 'high')),
    reasoning_quality TEXT DEFAULT 'deep' CHECK (reasoning_quality IN ('shallow', 'adequate', 'deep')),
    
    -- Context and connections
    references_previous_steps UUID[] DEFAULT '{}', -- References to previous thinking steps
    influences_future_steps UUID[] DEFAULT '{}', -- What future steps this influences
    
    -- Progress tracking
    completion_status TEXT NOT NULL DEFAULT 'completed' CHECK (completion_status IN ('draft', 'in_progress', 'completed', 'revised')),
    
    -- Tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure sequential order within session
    UNIQUE(thinking_session_id, step_sequence)
);

-- 4. Todo Progress Tracking Table
CREATE TABLE IF NOT EXISTS todo_progress_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    todo_id UUID NOT NULL REFERENCES goal_todos(id) ON DELETE CASCADE,
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    
    -- Progress snapshot
    progress_percentage INTEGER NOT NULL CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    status_change TEXT, -- What status changed
    progress_description TEXT NOT NULL, -- What progress was made
    
    -- Work details
    work_completed TEXT[] DEFAULT '{}', -- Specific work items completed
    obstacles_encountered TEXT[] DEFAULT '{}', -- Problems encountered
    solutions_applied TEXT[] DEFAULT '{}', -- How obstacles were addressed
    
    -- Quality assessment
    quality_score INTEGER CHECK (quality_score >= 1 AND quality_score <= 10),
    needs_review BOOLEAN DEFAULT FALSE,
    review_feedback TEXT,
    
    -- Agent context
    updated_by_agent_role TEXT NOT NULL,
    agent_confidence TEXT DEFAULT 'high' CHECK (agent_confidence IN ('low', 'medium', 'high')),
    
    -- Tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- PERFORMANCE INDEXES
-- =====================================================

-- Goal decomposition indexes
CREATE INDEX IF NOT EXISTS idx_goal_decompositions_goal_id ON workspace_goal_decompositions(goal_id);
CREATE INDEX IF NOT EXISTS idx_goal_decompositions_workspace_id ON workspace_goal_decompositions(workspace_id);
CREATE INDEX IF NOT EXISTS idx_goal_decompositions_complexity ON workspace_goal_decompositions(complexity_level);
CREATE INDEX IF NOT EXISTS idx_goal_decompositions_user_value ON workspace_goal_decompositions(user_value_score DESC);
CREATE INDEX IF NOT EXISTS idx_goal_decompositions_assets_gin ON workspace_goal_decompositions USING GIN (asset_deliverables);
CREATE INDEX IF NOT EXISTS idx_goal_decompositions_thinking_gin ON workspace_goal_decompositions USING GIN (thinking_components);

-- Todo list indexes
CREATE INDEX IF NOT EXISTS idx_goal_todos_decomposition_id ON goal_todos(decomposition_id);
CREATE INDEX IF NOT EXISTS idx_goal_todos_goal_id ON goal_todos(goal_id);
CREATE INDEX IF NOT EXISTS idx_goal_todos_workspace_id ON goal_todos(workspace_id);
CREATE INDEX IF NOT EXISTS idx_goal_todos_type ON goal_todos(todo_type);
CREATE INDEX IF NOT EXISTS idx_goal_todos_status ON goal_todos(status);
CREATE INDEX IF NOT EXISTS idx_goal_todos_priority ON goal_todos(priority);
CREATE INDEX IF NOT EXISTS idx_goal_todos_task_link ON goal_todos(linked_task_id) WHERE linked_task_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_goal_todos_supports_assets ON goal_todos USING GIN (supports_assets);

-- Thinking process indexes
CREATE INDEX IF NOT EXISTS idx_thinking_steps_todo_id ON thinking_process_steps(todo_id);
CREATE INDEX IF NOT EXISTS idx_thinking_steps_workspace_id ON thinking_process_steps(workspace_id);
CREATE INDEX IF NOT EXISTS idx_thinking_steps_session ON thinking_process_steps(thinking_session_id);
CREATE INDEX IF NOT EXISTS idx_thinking_steps_sequence ON thinking_process_steps(thinking_session_id, step_sequence);
CREATE INDEX IF NOT EXISTS idx_thinking_steps_type ON thinking_process_steps(step_type);
CREATE INDEX IF NOT EXISTS idx_thinking_steps_status ON thinking_process_steps(completion_status);
CREATE INDEX IF NOT EXISTS idx_thinking_steps_agent ON thinking_process_steps(agent_role);
CREATE INDEX IF NOT EXISTS idx_thinking_steps_inputs_gin ON thinking_process_steps USING GIN (inputs_considered);
CREATE INDEX IF NOT EXISTS idx_thinking_steps_conclusions_gin ON thinking_process_steps USING GIN (conclusions_reached);

-- Progress tracking indexes
CREATE INDEX IF NOT EXISTS idx_todo_progress_todo_id ON todo_progress_tracking(todo_id);
CREATE INDEX IF NOT EXISTS idx_todo_progress_workspace_id ON todo_progress_tracking(workspace_id);
CREATE INDEX IF NOT EXISTS idx_todo_progress_created_at ON todo_progress_tracking(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_todo_progress_needs_review ON todo_progress_tracking(needs_review) WHERE needs_review = TRUE;
CREATE INDEX IF NOT EXISTS idx_todo_progress_work_gin ON todo_progress_tracking USING GIN (work_completed);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_goal_todos_workspace_type_status ON goal_todos(workspace_id, todo_type, status);
CREATE INDEX IF NOT EXISTS idx_thinking_steps_todo_completion ON thinking_process_steps(todo_id, completion_status, step_sequence);
CREATE INDEX IF NOT EXISTS idx_todo_progress_recent ON todo_progress_tracking(todo_id, created_at DESC);

-- =====================================================
-- EFFICIENT QUERY VIEWS
-- =====================================================

-- View for thinking tab display
CREATE OR REPLACE VIEW thinking_tab_display AS
SELECT 
    gd.goal_id,
    gd.workspace_id,
    gt.id as todo_id,
    gt.name as todo_name,
    gt.todo_type,
    gt.status as todo_status,
    gt.progress_percentage,
    
    -- Thinking process summary
    COUNT(tps.id) as thinking_steps_count,
    COUNT(CASE WHEN tps.completion_status = 'completed' THEN 1 END) as completed_steps,
    
    -- Latest thinking content
    (SELECT thinking_content 
     FROM thinking_process_steps 
     WHERE todo_id = gt.id 
     ORDER BY step_sequence DESC 
     LIMIT 1) as latest_thinking,
    
    -- Progress summary
    (SELECT progress_description 
     FROM todo_progress_tracking 
     WHERE todo_id = gt.id 
     ORDER BY created_at DESC 
     LIMIT 1) as latest_progress,
    
    gt.updated_at,
    gt.completed_at
    
FROM workspace_goal_decompositions gd
JOIN goal_todos gt ON gd.id = gt.decomposition_id
LEFT JOIN thinking_process_steps tps ON gt.id = tps.todo_id
WHERE gt.todo_type = 'thinking'
GROUP BY gd.goal_id, gd.workspace_id, gt.id, gt.name, gt.todo_type, 
         gt.status, gt.progress_percentage, gt.updated_at, gt.completed_at;

-- View for asset todos progress
CREATE OR REPLACE VIEW asset_todos_progress AS
SELECT 
    gd.goal_id,
    gd.workspace_id,
    gt.id as todo_id,
    gt.name as todo_name,
    gt.value_proposition,
    gt.status,
    gt.progress_percentage,
    gt.deliverable_type,
    
    -- Linked task info
    t.id as task_id,
    t.name as task_name,
    t.status as task_status,
    
    -- Progress tracking
    COUNT(tpt.id) as progress_entries,
    MAX(tpt.quality_score) as best_quality_score,
    COUNT(CASE WHEN tpt.needs_review = TRUE THEN 1 END) as pending_reviews,
    
    gt.updated_at,
    gt.completed_at
    
FROM workspace_goal_decompositions gd
JOIN goal_todos gt ON gd.id = gt.decomposition_id
LEFT JOIN tasks t ON gt.linked_task_id = t.id
LEFT JOIN todo_progress_tracking tpt ON gt.id = tpt.todo_id
WHERE gt.todo_type = 'asset'
GROUP BY gd.goal_id, gd.workspace_id, gt.id, gt.name, gt.value_proposition,
         gt.status, gt.progress_percentage, gt.deliverable_type,
         t.id, t.name, t.status, gt.updated_at, gt.completed_at;

-- =====================================================
-- RLS POLICIES (Row Level Security)
-- =====================================================

-- Enable RLS on all new tables
ALTER TABLE workspace_goal_decompositions ENABLE ROW LEVEL SECURITY;
ALTER TABLE goal_todos ENABLE ROW LEVEL SECURITY;
ALTER TABLE thinking_process_steps ENABLE ROW LEVEL SECURITY;
ALTER TABLE todo_progress_tracking ENABLE ROW LEVEL SECURITY;

-- RLS Policies for workspace_goal_decompositions
CREATE POLICY "Users can access decompositions for their workspaces" ON workspace_goal_decompositions
    FOR ALL USING (true); -- Simplified for development

-- RLS Policies for goal_todos
CREATE POLICY "Users can access todos for their workspaces" ON goal_todos
    FOR ALL USING (true); -- Simplified for development

-- RLS Policies for thinking_process_steps
CREATE POLICY "Users can access thinking steps for their workspaces" ON thinking_process_steps
    FOR ALL USING (true); -- Simplified for development

-- RLS Policies for todo_progress_tracking
CREATE POLICY "Users can access progress tracking for their workspaces" ON todo_progress_tracking
    FOR ALL USING (true); -- Simplified for development

-- =====================================================
-- UTILITY FUNCTIONS
-- =====================================================

-- Function to get thinking process summary for a goal
CREATE OR REPLACE FUNCTION get_goal_thinking_summary(goal_id_param UUID)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'goal_id', goal_id_param,
        'total_todos', COUNT(gt.id),
        'asset_todos', COUNT(CASE WHEN gt.todo_type = 'asset' THEN 1 END),
        'thinking_todos', COUNT(CASE WHEN gt.todo_type = 'thinking' THEN 1 END),
        'completed_todos', COUNT(CASE WHEN gt.status = 'completed' THEN 1 END),
        'thinking_steps', COUNT(tps.id),
        'avg_progress', ROUND(AVG(gt.progress_percentage), 2)
    ) INTO result
    FROM goal_todos gt
    LEFT JOIN thinking_process_steps tps ON gt.id = tps.todo_id
    WHERE gt.goal_id = goal_id_param;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to get latest thinking for a workspace
CREATE OR REPLACE FUNCTION get_workspace_latest_thinking(workspace_id_param UUID, limit_param INTEGER DEFAULT 10)
RETURNS TABLE(
    step_title TEXT,
    thinking_content TEXT,
    agent_role TEXT,
    step_type TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    goal_id UUID,
    todo_name TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        tps.step_title,
        tps.thinking_content,
        tps.agent_role,
        tps.step_type,
        tps.created_at,
        gt.goal_id,
        gt.name as todo_name
    FROM thinking_process_steps tps
    JOIN goal_todos gt ON tps.todo_id = gt.id
    WHERE tps.workspace_id = workspace_id_param
    ORDER BY tps.created_at DESC
    LIMIT limit_param;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- COMMENTS FOR DOCUMENTATION
-- =====================================================

COMMENT ON TABLE workspace_goal_decompositions IS 'Stores goal decomposition results with asset deliverables and thinking components';
COMMENT ON TABLE goal_todos IS 'Todo items derived from goal decomposition - both assets and thinking components';
COMMENT ON TABLE thinking_process_steps IS 'Authentic thinking process steps showing real system reasoning';
COMMENT ON TABLE todo_progress_tracking IS 'Detailed progress tracking for individual todos with quality assessment';

COMMENT ON COLUMN thinking_process_steps.thinking_content IS 'Real thinking content - not fake metadata but actual reasoning';
COMMENT ON COLUMN thinking_process_steps.agent_role IS 'Which agent type performed this thinking step';
COMMENT ON COLUMN thinking_process_steps.reasoning_quality IS 'Quality of reasoning: shallow/adequate/deep';

-- =====================================================
-- COMPLETION MESSAGE
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE '🧠 AUTHENTIC THINKING PROCESS SCHEMA CREATED SUCCESSFULLY';
    RAISE NOTICE '✅ Tables: workspace_goal_decompositions, goal_todos, thinking_process_steps, todo_progress_tracking';
    RAISE NOTICE '✅ Indexes: Optimized for thinking tab queries and todo list performance';
    RAISE NOTICE '✅ Views: thinking_tab_display, asset_todos_progress';
    RAISE NOTICE '✅ Functions: get_goal_thinking_summary, get_workspace_latest_thinking';
    RAISE NOTICE '📊 Ready for authentic thinking process tracking!';
END $$;