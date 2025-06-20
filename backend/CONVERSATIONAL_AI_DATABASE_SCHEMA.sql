-- Conversational AI Database Schema
-- Core tables for the conversational AI system

-- Main conversations table
CREATE TABLE IF NOT EXISTS conversations (
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    chat_id TEXT NOT NULL,
    schema_version TEXT DEFAULT 'v2025-06-A',
    title TEXT,
    description TEXT,
    active_messages JSONB DEFAULT '[]',
    archived_summaries JSONB DEFAULT '[]',
    conversational_features JSONB DEFAULT '{"context_aware": true, "tool_integration": true, "progressive_summarization": true}',
    metadata JSONB DEFAULT '{}',
    last_summarization TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (workspace_id, chat_id)
);

-- Conversation messages table
CREATE TABLE IF NOT EXISTS conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id TEXT NOT NULL, -- format: workspace_id_chat_id
    message_id TEXT NOT NULL,
    role TEXT NOT NULL, -- user, assistant, system
    content TEXT,
    content_type TEXT DEFAULT 'text', -- text, confirmation, clarification, error
    tools_used TEXT[] DEFAULT '{}',
    actions_performed JSONB DEFAULT '[]',
    artifacts_generated JSONB DEFAULT '[]',
    context_snapshot JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(conversation_id, message_id)
);

-- Pending confirmations table (for two-step confirmation system)
CREATE TABLE IF NOT EXISTS pending_confirmations (
    action_id TEXT PRIMARY KEY,
    conversation_id TEXT,
    message_id TEXT,
    action_type TEXT NOT NULL,
    action_description TEXT,
    parameters JSONB NOT NULL,
    risk_level TEXT NOT NULL, -- low, medium, high, critical
    status TEXT DEFAULT 'pending', -- pending, confirmed, cancelled, expired
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    confirmed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent knowledge base table
CREATE TABLE IF NOT EXISTS agent_knowledge (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content TEXT,
    processed_content TEXT, -- AI-enhanced version
    document_type TEXT DEFAULT 'text', -- text, pdf, url, file
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Workflow automations table
CREATE TABLE IF NOT EXISTS workflow_automations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    trigger_event TEXT NOT NULL, -- task_completed, budget_threshold, etc.
    actions JSONB NOT NULL, -- Array of actions to perform
    conditions JSONB DEFAULT '[]', -- Optional conditions to check
    optimizations JSONB DEFAULT '{}', -- AI-driven optimizations
    is_active BOOLEAN DEFAULT true,
    execution_count INTEGER DEFAULT 0,
    last_executed TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Cross-workspace learning insights (anonymized)
CREATE TABLE IF NOT EXISTS cross_workspace_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain TEXT NOT NULL, -- e.g., 'software_development', 'marketing', 'consulting'
    insight_type TEXT NOT NULL, -- 'productivity', 'estimation', 'team_composition'
    insight_description TEXT NOT NULL,
    confidence_score INTEGER NOT NULL, -- 0-100
    supporting_data JSONB DEFAULT '{}', -- Anonymized metrics
    applicable_contexts TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_conversations_workspace ON conversations(workspace_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversation_messages_conversation ON conversation_messages(conversation_id, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_conversation_messages_role ON conversation_messages(role, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pending_confirmations_status ON pending_confirmations(status, expires_at);
CREATE INDEX IF NOT EXISTS idx_pending_confirmations_workspace ON pending_confirmations(conversation_id);
CREATE INDEX IF NOT EXISTS idx_agent_knowledge_agent ON agent_knowledge(agent_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_knowledge_workspace ON agent_knowledge(workspace_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_workflow_automations_workspace ON workflow_automations(workspace_id, is_active);
CREATE INDEX IF NOT EXISTS idx_workflow_automations_trigger ON workflow_automations(trigger_event, is_active);
CREATE INDEX IF NOT EXISTS idx_cross_workspace_insights_domain ON cross_workspace_insights(domain, confidence_score DESC);

-- RLS policies
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE pending_confirmations ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_knowledge ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_automations ENABLE ROW LEVEL SECURITY;
ALTER TABLE cross_workspace_insights ENABLE ROW LEVEL SECURITY;

-- Conversations access
CREATE POLICY "conversations_workspace_access" ON conversations 
FOR ALL USING (workspace_id IN (SELECT id FROM workspaces WHERE auth.uid() = owner_id));

-- Conversation messages access
CREATE POLICY "conversation_messages_workspace_access" ON conversation_messages 
FOR ALL USING (
  conversation_id LIKE (
    SELECT workspace_id::text || '_%' 
    FROM workspaces 
    WHERE auth.uid() = owner_id
  )
);

-- Pending confirmations access
CREATE POLICY "pending_confirmations_workspace_access" ON pending_confirmations 
FOR ALL USING (
  conversation_id LIKE (
    SELECT workspace_id::text || '_%' 
    FROM workspaces 
    WHERE auth.uid() = owner_id
  )
);

-- Agent knowledge access
CREATE POLICY "agent_knowledge_workspace_access" ON agent_knowledge 
FOR ALL USING (workspace_id IN (SELECT id FROM workspaces WHERE auth.uid() = owner_id));

-- Workflow automations access
CREATE POLICY "workflow_automations_workspace_access" ON workflow_automations 
FOR ALL USING (workspace_id IN (SELECT id FROM workspaces WHERE auth.uid() = owner_id));

-- Cross-workspace insights (read-only for all authenticated users)
CREATE POLICY "cross_workspace_insights_read_all" ON cross_workspace_insights 
FOR SELECT USING (auth.role() = 'authenticated');

-- Functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_conversations_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_conversations_timestamp_trigger
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_conversations_timestamp();

-- Cleanup function for expired confirmations
CREATE OR REPLACE FUNCTION cleanup_expired_confirmations()
RETURNS INTEGER AS $$
DECLARE
    expired_count INTEGER;
BEGIN
    UPDATE pending_confirmations 
    SET status = 'expired' 
    WHERE status = 'pending' 
    AND expires_at < NOW();
    
    GET DIAGNOSTICS expired_count = ROW_COUNT;
    RETURN expired_count;
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON TABLE conversations IS 'Main conversations between users and AI assistants';
COMMENT ON TABLE conversation_messages IS 'Individual messages within conversations with full context';
COMMENT ON TABLE pending_confirmations IS 'Two-step confirmation system for destructive actions';
COMMENT ON TABLE agent_knowledge IS 'Knowledge base for individual agents';
COMMENT ON TABLE workflow_automations IS 'Automated workflows triggered by events';
COMMENT ON TABLE cross_workspace_insights IS 'Anonymized insights shared across workspaces';

COMMENT ON COLUMN conversations.active_messages IS 'Recent messages kept in active memory';
COMMENT ON COLUMN conversations.archived_summaries IS 'AI-generated summaries of older message chunks';
COMMENT ON COLUMN conversation_messages.tools_used IS 'List of tools/functions called in this message';
COMMENT ON COLUMN conversation_messages.actions_performed IS 'Detailed log of actions taken';
COMMENT ON COLUMN pending_confirmations.risk_level IS 'Risk assessment: low, medium, high, critical';
COMMENT ON COLUMN workflow_automations.optimizations IS 'AI-driven workflow improvements';
COMMENT ON COLUMN cross_workspace_insights.confidence_score IS 'Confidence level (0-100) for the insight';