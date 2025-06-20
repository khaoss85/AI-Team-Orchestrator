-- Add document management tables
-- Migration 008: Document and Vector Store Management

-- Table for storing document metadata
CREATE TABLE IF NOT EXISTS workspace_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type TEXT NOT NULL,
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    uploaded_by TEXT NOT NULL, -- 'chat' or agent_id
    sharing_scope TEXT NOT NULL, -- 'team' or specific agent_id
    vector_store_id TEXT, -- OpenAI vector store ID
    openai_file_id TEXT, -- OpenAI file ID
    description TEXT,
    tags TEXT[] DEFAULT '{}',
    file_hash TEXT, -- SHA256 hash for deduplication
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for tracking vector stores
CREATE TABLE IF NOT EXISTS workspace_vector_stores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    openai_vector_store_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    scope TEXT NOT NULL, -- 'team' or specific agent_id
    file_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_workspace_documents_workspace_id ON workspace_documents(workspace_id);
CREATE INDEX IF NOT EXISTS idx_workspace_documents_scope ON workspace_documents(sharing_scope);
CREATE INDEX IF NOT EXISTS idx_workspace_documents_hash ON workspace_documents(file_hash);
CREATE INDEX IF NOT EXISTS idx_workspace_vector_stores_workspace_id ON workspace_vector_stores(workspace_id);
CREATE INDEX IF NOT EXISTS idx_workspace_vector_stores_scope ON workspace_vector_stores(workspace_id, scope);

-- Update function for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for automatic updated_at
CREATE TRIGGER update_workspace_documents_updated_at
    BEFORE UPDATE ON workspace_documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE workspace_documents IS 'Stores metadata for uploaded documents in workspaces';
COMMENT ON TABLE workspace_vector_stores IS 'Tracks OpenAI vector stores for document search';
COMMENT ON COLUMN workspace_documents.sharing_scope IS 'Determines document visibility: team (all agents) or specific agent_id';
COMMENT ON COLUMN workspace_documents.file_hash IS 'SHA256 hash for preventing duplicate uploads';
COMMENT ON COLUMN workspace_vector_stores.scope IS 'Vector store scope: team (shared) or agent_id (agent-specific)';