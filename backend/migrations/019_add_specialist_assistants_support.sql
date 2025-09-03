-- Migration 019: Add specialist assistants support for shared document access
-- This migration creates infrastructure for specialist agents to access workspace documents

-- Table for mapping specialist agents to their OpenAI assistants
CREATE TABLE IF NOT EXISTS specialist_assistants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    assistant_id VARCHAR(255) NOT NULL, -- OpenAI assistant ID
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure one assistant per agent per workspace
    UNIQUE(workspace_id, agent_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_specialist_assistants_workspace_id 
    ON specialist_assistants(workspace_id);
CREATE INDEX IF NOT EXISTS idx_specialist_assistants_agent_id 
    ON specialist_assistants(agent_id);
CREATE INDEX IF NOT EXISTS idx_specialist_assistants_assistant_id 
    ON specialist_assistants(assistant_id);

-- Add document access permissions tracking
ALTER TABLE specialist_assistants 
ADD COLUMN IF NOT EXISTS document_access_enabled BOOLEAN DEFAULT true,
ADD COLUMN IF NOT EXISTS last_document_sync TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Create function to automatically update last_updated timestamp
CREATE OR REPLACE FUNCTION update_specialist_assistants_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic timestamp updates
DROP TRIGGER IF EXISTS trigger_update_specialist_assistants_updated_at ON specialist_assistants;
CREATE TRIGGER trigger_update_specialist_assistants_updated_at
    BEFORE UPDATE ON specialist_assistants
    FOR EACH ROW
    EXECUTE FUNCTION update_specialist_assistants_updated_at();

-- Add helpful comments
COMMENT ON TABLE specialist_assistants IS 'Maps specialist agents to their OpenAI assistants for document access';
COMMENT ON COLUMN specialist_assistants.workspace_id IS 'Reference to the workspace containing shared documents';
COMMENT ON COLUMN specialist_assistants.agent_id IS 'Reference to the specialist agent';
COMMENT ON COLUMN specialist_assistants.assistant_id IS 'OpenAI assistant ID with document access permissions';
COMMENT ON COLUMN specialist_assistants.document_access_enabled IS 'Whether this specialist has access to workspace documents';
COMMENT ON COLUMN specialist_assistants.last_document_sync IS 'When documents were last synchronized to this assistant';

-- Grant appropriate permissions
GRANT ALL ON specialist_assistants TO authenticated;
GRANT ALL ON specialist_assistants TO service_role;

-- Insert initial data check
DO $$
BEGIN
    -- Log migration completion
    RAISE NOTICE 'Migration 019 completed: specialist_assistants table created with indexes and triggers';
END $$;