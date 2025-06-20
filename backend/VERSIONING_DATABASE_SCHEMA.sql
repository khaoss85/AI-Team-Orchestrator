-- Versioning System Database Schema
-- Tables for managing schema versions, compatibility, and migrations

-- Component versions table
CREATE TABLE IF NOT EXISTS component_versions (
    id text PRIMARY KEY,
    component_type text NOT NULL,
    component_name text NOT NULL,
    version text NOT NULL,
    schema_definition jsonb NOT NULL,
    compatibility_matrix jsonb DEFAULT '{}',
    breaking_changes jsonb DEFAULT '[]',
    migration_required boolean DEFAULT false,
    metadata jsonb DEFAULT '{}',
    created_at timestamp with time zone DEFAULT now(),
    is_active boolean DEFAULT true,
    UNIQUE(component_type, component_name, version)
);

-- Version migrations tracking
CREATE TABLE IF NOT EXISTS version_migrations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id uuid REFERENCES workspaces(id) ON DELETE CASCADE,
    conversation_id text,
    component_type text NOT NULL,
    component_name text NOT NULL,
    source_version text NOT NULL,
    target_version text NOT NULL,
    migration_status text DEFAULT 'pending', -- pending, in_progress, completed, failed, rolled_back
    migration_plan jsonb,
    execution_log jsonb DEFAULT '[]',
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    error_message text,
    metadata jsonb DEFAULT '{}',
    created_at timestamp with time zone DEFAULT now()
);

-- Conversation backups for safe migrations
CREATE TABLE IF NOT EXISTS conversation_backups (
    backup_id text PRIMARY KEY,
    workspace_id uuid REFERENCES workspaces(id) ON DELETE CASCADE,
    conversation_id text NOT NULL,
    original_conversation jsonb NOT NULL,
    backup_type text DEFAULT 'migration_backup',
    created_at timestamp with time zone DEFAULT now(),
    expires_at timestamp with time zone DEFAULT (now() + interval '30 days'),
    metadata jsonb DEFAULT '{}'
);

-- Version compatibility matrix (for complex version relationships)
CREATE TABLE IF NOT EXISTS version_compatibility (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    component_type text NOT NULL,
    component_name text NOT NULL,
    source_version text NOT NULL,
    target_version text NOT NULL,
    compatibility_level text NOT NULL, -- fully_compatible, backward_compatible, migration_required, incompatible
    migration_complexity text DEFAULT 'medium', -- low, medium, high, critical
    estimated_time_minutes integer DEFAULT 5,
    breaking_changes jsonb DEFAULT '[]',
    migration_notes text,
    created_at timestamp with time zone DEFAULT now(),
    UNIQUE(component_type, component_name, source_version, target_version)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_component_versions_type_name ON component_versions(component_type, component_name);
CREATE INDEX IF NOT EXISTS idx_component_versions_active ON component_versions(is_active, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_version_migrations_workspace ON version_migrations(workspace_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_version_migrations_status ON version_migrations(migration_status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversation_backups_workspace ON conversation_backups(workspace_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversation_backups_expires ON conversation_backups(expires_at);
CREATE INDEX IF NOT EXISTS idx_version_compatibility_lookup ON version_compatibility(component_type, component_name, source_version, target_version);

-- Initial system versions
INSERT INTO component_versions (id, component_type, component_name, version, schema_definition, metadata) VALUES
('conversation_schema_conversation_v2025-06-A', 'conversation_schema', 'conversation', 'v2025-06-A', 
 '{"fields": {"workspace_id": "string", "chat_id": "string", "schema_version": "string", "title": "string", "description": "string", "active_messages": "array", "archived_summaries": "array", "created_at": "timestamp"}, "required": ["workspace_id", "chat_id", "schema_version"]}',
 '{"release_date": "2025-06-19", "major_features": ["conversational_ai", "progressive_summarization", "context_awareness"], "breaking_changes": []}'),

('tool_schema_conversational_tools_v2025-06-A', 'tool_schema', 'conversational_tools', 'v2025-06-A',
 '{"tools": ["create_deliverable", "update_agent_skills", "create_task", "analyze_team_performance", "upload_knowledge_document", "create_workflow_automation"], "universal": true, "domain_agnostic": true}',
 '{"release_date": "2025-06-19", "tool_count": 6, "universal_design": true}'),

('context_schema_workspace_context_v2025-06-A', 'context_schema', 'workspace_context', 'v2025-06-A',
 '{"context_fields": ["workspace", "agents", "recent_tasks", "deliverables", "budget", "goals", "memory_insights", "learning_insights"], "progressive_summarization": true, "memory_management": true}',
 '{"release_date": "2025-06-19", "context_aware": true, "summarization_enabled": true}')

ON CONFLICT (component_type, component_name, version) DO NOTHING;

-- RLS policies
ALTER TABLE component_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE version_migrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_backups ENABLE ROW LEVEL SECURITY;
ALTER TABLE version_compatibility ENABLE ROW LEVEL SECURITY;

-- Public read access for component versions (system-wide)
CREATE POLICY "component_versions_public_read" ON component_versions FOR SELECT USING (true);

-- Workspace-specific access for migrations and backups
CREATE POLICY "version_migrations_workspace_access" ON version_migrations 
FOR ALL USING (workspace_id IN (SELECT id FROM workspaces WHERE auth.uid() = owner_id));

CREATE POLICY "conversation_backups_workspace_access" ON conversation_backups 
FOR ALL USING (workspace_id IN (SELECT id FROM workspaces WHERE auth.uid() = owner_id));

-- Public read for compatibility matrix
CREATE POLICY "version_compatibility_public_read" ON version_compatibility FOR SELECT USING (true);

-- Comments for documentation
COMMENT ON TABLE component_versions IS 'Registry of all component versions with schema definitions and compatibility information';
COMMENT ON TABLE version_migrations IS 'Tracking table for version migration operations across workspaces';
COMMENT ON TABLE conversation_backups IS 'Safe storage for conversation data before migrations';
COMMENT ON TABLE version_compatibility IS 'Matrix defining compatibility relationships between different versions';

COMMENT ON COLUMN component_versions.schema_definition IS 'JSON schema definition for the component version';
COMMENT ON COLUMN component_versions.compatibility_matrix IS 'Compatibility relationships with other versions';
COMMENT ON COLUMN version_migrations.migration_plan IS 'Detailed plan for executing the migration';
COMMENT ON COLUMN version_migrations.execution_log IS 'Log of migration steps and their outcomes';