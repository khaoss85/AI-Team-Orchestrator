-- Migration 018: Add OpenAI Assistants support for native RAG functionality
-- This migration creates the workspace_assistants table to manage OpenAI Assistant instances

-- Create workspace_assistants table
CREATE TABLE IF NOT EXISTS workspace_assistants (
    workspace_id UUID PRIMARY KEY REFERENCES workspaces(id) ON DELETE CASCADE,
    assistant_id VARCHAR(255) NOT NULL,
    thread_id VARCHAR(255),
    vector_store_ids JSONB DEFAULT '[]'::jsonb,
    configuration JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for efficient lookups
CREATE INDEX IF NOT EXISTS idx_workspace_assistants_assistant_id 
    ON workspace_assistants(assistant_id);

CREATE INDEX IF NOT EXISTS idx_workspace_assistants_thread_id 
    ON workspace_assistants(thread_id);

CREATE INDEX IF NOT EXISTS idx_workspace_assistants_updated 
    ON workspace_assistants(last_updated);

-- Add comment for documentation
COMMENT ON TABLE workspace_assistants IS 'Manages OpenAI Assistant instances for workspace-based RAG functionality';
COMMENT ON COLUMN workspace_assistants.workspace_id IS 'Foreign key to workspaces table';
COMMENT ON COLUMN workspace_assistants.assistant_id IS 'OpenAI Assistant ID';
COMMENT ON COLUMN workspace_assistants.thread_id IS 'OpenAI Thread ID for conversation continuity';
COMMENT ON COLUMN workspace_assistants.vector_store_ids IS 'Array of vector store IDs attached to the assistant';
COMMENT ON COLUMN workspace_assistants.configuration IS 'Assistant configuration (model, temperature, etc.)';

-- Create trigger to update last_updated timestamp
CREATE OR REPLACE FUNCTION update_workspace_assistants_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_workspace_assistants_updated_at_trigger
    BEFORE UPDATE ON workspace_assistants
    FOR EACH ROW
    EXECUTE FUNCTION update_workspace_assistants_updated_at();

-- Grant necessary permissions (adjust based on your user setup)
-- GRANT ALL ON workspace_assistants TO your_app_user;

-- Migration verification query
-- This query helps verify the migration was successful
/*
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM 
    information_schema.columns
WHERE 
    table_name = 'workspace_assistants'
ORDER BY 
    ordinal_position;
*/