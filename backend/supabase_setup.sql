-- Schema for AI Team Orchestrator

-- Workspaces table
CREATE TABLE IF NOT EXISTS workspaces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    user_id UUID NOT NULL,
    status TEXT NOT NULL DEFAULT 'created',
    goal TEXT,
    budget JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agents table
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    seniority TEXT NOT NULL,
    description TEXT,
    system_prompt TEXT,
    status TEXT NOT NULL DEFAULT 'created',
    health JSONB DEFAULT '{"status": "unknown", "last_update": null}'::JSONB,
    model_config JSONB,
    tools JSONB,
    can_create_tools BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent Handoffs
CREATE TABLE IF NOT EXISTS agent_handoffs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    target_agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    result JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Execution Logs
CREATE TABLE IF NOT EXISTS execution_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    content JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Documents (Knowledge Base)
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    content TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create updated_at triggers
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_workspaces_updated_at
BEFORE UPDATE ON workspaces
FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

CREATE TRIGGER update_agents_updated_at
BEFORE UPDATE ON agents
FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

CREATE TRIGGER update_tasks_updated_at
BEFORE UPDATE ON tasks
FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

CREATE TRIGGER update_documents_updated_at
BEFORE UPDATE ON documents
FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_agents_workspace_id ON agents(workspace_id);
CREATE INDEX IF NOT EXISTS idx_tasks_workspace_id ON tasks(workspace_id);
CREATE INDEX IF NOT EXISTS idx_tasks_agent_id ON tasks(agent_id);
CREATE INDEX IF NOT EXISTS idx_execution_logs_workspace_id ON execution_logs(workspace_id);
CREATE INDEX IF NOT EXISTS idx_execution_logs_agent_id ON execution_logs(agent_id);
CREATE INDEX IF NOT EXISTS idx_documents_workspace_id ON documents(workspace_id);
CREATE INDEX IF NOT EXISTS idx_documents_agent_id ON documents(agent_id);


-- Custom Tools table
CREATE TABLE IF NOT EXISTS custom_tools (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    code TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TRIGGER update_custom_tools_updated_at
BEFORE UPDATE ON custom_tools
FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

CREATE INDEX IF NOT EXISTS idx_custom_tools_workspace_id ON custom_tools(workspace_id);

-- Tabella per salvare le proposte di team
CREATE TABLE IF NOT EXISTS team_proposals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    proposal_data JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', -- pending, approved, rejected
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TRIGGER update_team_proposals_updated_at
BEFORE UPDATE ON team_proposals
FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

CREATE INDEX IF NOT EXISTS idx_team_proposals_workspace_id ON team_proposals(workspace_id);
CREATE INDEX IF NOT EXISTS idx_team_proposals_status ON team_proposals(status);

-- Human Feedback Requests table
CREATE TABLE IF NOT EXISTS human_feedback_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE, -- CASCADE DELETE
    request_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    proposed_actions JSONB NOT NULL,
    context JSONB,
    priority TEXT NOT NULL DEFAULT 'medium',
    status TEXT NOT NULL DEFAULT 'pending',
    timeout_hours INTEGER DEFAULT 24,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    response JSONB,
    responded_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TRIGGER update_human_feedback_requests_updated_at
BEFORE UPDATE ON human_feedback_requests
FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

CREATE INDEX IF NOT EXISTS idx_human_feedback_requests_workspace_id ON human_feedback_requests(workspace_id);
CREATE INDEX IF NOT EXISTS idx_human_feedback_requests_status ON human_feedback_requests(status);
CREATE INDEX IF NOT EXISTS idx_human_feedback_requests_expires_at ON human_feedback_requests(expires_at);

-- Aggiungi una colonna workspace_id alla tabella handoffs per una cancellazione più diretta
ALTER TABLE agent_handoffs ADD COLUMN workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE;
-- Rendi la colonna NOT NULL
ALTER TABLE agent_handoffs ALTER COLUMN workspace_id SET NOT NULL;
-- Aggiungi un indice per performance
CREATE INDEX IF NOT EXISTS idx_agent_handoffs_workspace_id ON agent_handoffs(workspace_id);


-- Funzione per aggiornare timestamp (NECESSARIA PRIMA DEI TRIGGER)
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE NOT NULL,
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    assigned_to_role TEXT,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    priority TEXT NOT NULL DEFAULT 'medium',
    parent_task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    depends_on_task_ids UUID[],
    estimated_effort_hours FLOAT,
    deadline TIMESTAMP WITH TIME ZONE,
    context_data JSONB, -- Usare JSONB per flessibilità e indicizzazione campi interni
    result JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks FOR EACH ROW EXECUTE PROCEDURE update_modified_column();
CREATE INDEX IF NOT EXISTS idx_tasks_workspace_id ON tasks(workspace_id);
CREATE INDEX IF NOT EXISTS idx_tasks_agent_id ON tasks(agent_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to_role ON tasks(assigned_to_role);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_parent_task_id ON tasks(parent_task_id);
-- Per depends_on_task_ids, se fai query frequenti per cercare task che dipendono da un ID specifico:
CREATE INDEX IF NOT EXISTS idx_tasks_depends_on_gin ON tasks USING GIN (depends_on_task_ids);
-- Per context_data, se fai query sui campi interni:
CREATE INDEX IF NOT EXISTS idx_tasks_context_data_gin ON tasks USING GIN (context_data);

-- Agent Handoffs (MODIFICATO per includere workspace_id come da tuo schema)
CREATE TABLE IF NOT EXISTS agent_handoffs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE NOT NULL, -- Assicurato NOT NULL
    source_agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    target_agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_agent_handoffs_workspace_id ON agent_handoffs(workspace_id);

ALTER TABLE IF EXISTS agents 
ADD COLUMN IF NOT EXISTS first_name TEXT,
ADD COLUMN IF NOT EXISTS last_name TEXT,
ADD COLUMN IF NOT EXISTS personality_traits JSONB,
ADD COLUMN IF NOT EXISTS communication_style TEXT,
ADD COLUMN IF NOT EXISTS hard_skills JSONB,
ADD COLUMN IF NOT EXISTS soft_skills JSONB,
ADD COLUMN IF NOT EXISTS background_story TEXT;

-- In supabase_setup.sql, aggiungi queste colonne se non esistono già
ALTER TABLE IF EXISTS tasks
ADD COLUMN IF NOT EXISTS created_by_task_id UUID REFERENCES tasks(id),
ADD COLUMN IF NOT EXISTS created_by_agent_id UUID REFERENCES agents(id),
ADD COLUMN IF NOT EXISTS creation_type VARCHAR(50) DEFAULT 'manual',
ADD COLUMN IF NOT EXISTS delegation_depth INTEGER DEFAULT 0;
ALTER TABLE IF EXISTS tasks
ADD COLUMN IF NOT EXISTS iteration_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS max_iterations INTEGER,
ADD COLUMN IF NOT EXISTS dependency_map JSONB;

-- Indici per performance
CREATE INDEX IF NOT EXISTS idx_tasks_created_by_task_id ON tasks(created_by_task_id);
CREATE INDEX IF NOT EXISTS idx_tasks_delegation_depth ON tasks(delegation_depth);
CREATE INDEX IF NOT EXISTS idx_tasks_creation_type ON tasks(creation_type);

-- Optional table for storing individual agent proposals
CREATE TABLE IF NOT EXISTS agent_proposals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    proposal_data JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', -- pending, approved, rejected
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TRIGGER update_agent_proposals_updated_at
BEFORE UPDATE ON agent_proposals
FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

CREATE INDEX IF NOT EXISTS idx_agent_proposals_agent_id ON agent_proposals(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_proposals_status ON agent_proposals(status);
