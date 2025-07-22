-- create_deliverables_table.sql

CREATE TABLE IF NOT EXISTS public.deliverables (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
    goal_id UUID REFERENCES public.workspace_goals(id) ON DELETE SET NULL,
    task_id UUID REFERENCES public.tasks(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    description TEXT,
    content JSONB,
    "type" TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    readiness_score FLOAT,
    completion_percentage FLOAT,
    business_value_score FLOAT,
    quality_metrics JSONB,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_deliverables_workspace_id ON public.deliverables(workspace_id);
CREATE INDEX IF NOT EXISTS idx_deliverables_goal_id ON public.deliverables(goal_id);

-- Enable RLS
ALTER TABLE public.deliverables ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Allow users to manage their own deliverables"
ON public.deliverables
FOR ALL
USING (auth.uid() = (SELECT user_id FROM public.workspaces WHERE id = workspace_id));

GRANT ALL ON TABLE public.deliverables TO authenticated;
GRANT ALL ON TABLE public.deliverables TO service_role;
