-- Migration: Create goal_asset_requirements table
-- Purpose: Store asset requirements generated for each goal by WorkflowOrchestrator

CREATE TABLE IF NOT EXISTS goal_asset_requirements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL,
    goal_id UUID NOT NULL,
    requirement_type VARCHAR(100) NOT NULL DEFAULT 'analysis',
    name VARCHAR(255) NOT NULL,
    description TEXT,
    priority VARCHAR(50) DEFAULT 'medium',
    complexity VARCHAR(50) DEFAULT 'medium', 
    gap TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add foreign key constraints if tables exist
DO $$
BEGIN
    -- Add workspace foreign key if workspaces table exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'workspaces') THEN
        ALTER TABLE goal_asset_requirements 
        ADD CONSTRAINT fk_goal_asset_requirements_workspace 
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE;
    END IF;
    
    -- Add goal foreign key if workspace_goals table exists  
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'workspace_goals') THEN
        ALTER TABLE goal_asset_requirements 
        ADD CONSTRAINT fk_goal_asset_requirements_goal
        FOREIGN KEY (goal_id) REFERENCES workspace_goals(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_goal_asset_requirements_workspace_id ON goal_asset_requirements (workspace_id);
CREATE INDEX IF NOT EXISTS idx_goal_asset_requirements_goal_id ON goal_asset_requirements (goal_id);
CREATE INDEX IF NOT EXISTS idx_goal_asset_requirements_type ON goal_asset_requirements (requirement_type);
CREATE INDEX IF NOT EXISTS idx_goal_asset_requirements_priority ON goal_asset_requirements (priority);

-- Add comments
COMMENT ON TABLE goal_asset_requirements IS 'Asset requirements generated for workspace goals by WorkflowOrchestrator';
COMMENT ON COLUMN goal_asset_requirements.requirement_type IS 'Type of asset requirement (analysis, document, code, etc.)';
COMMENT ON COLUMN goal_asset_requirements.priority IS 'Priority level (low, medium, high, critical)';
COMMENT ON COLUMN goal_asset_requirements.complexity IS 'Complexity level (low, medium, high, expert)';
COMMENT ON COLUMN goal_asset_requirements.gap IS 'JSON string describing requirement gaps and acceptance criteria';

-- Add updated_at trigger
CREATE OR REPLACE FUNCTION update_goal_asset_requirements_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_goal_asset_requirements_updated_at
    BEFORE UPDATE ON goal_asset_requirements
    FOR EACH ROW
    EXECUTE FUNCTION update_goal_asset_requirements_updated_at();

RAISE NOTICE 'Table goal_asset_requirements created successfully with indexes and constraints.';