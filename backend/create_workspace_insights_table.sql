-- Migration: Create workspace_insights table for workspace memory system
-- Run this SQL script in your Supabase database

-- Create workspace_insights table
CREATE TABLE IF NOT EXISTS workspace_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL,
    task_id UUID NOT NULL,
    agent_role TEXT NOT NULL,
    insight_type TEXT NOT NULL CHECK (insight_type IN ('success_pattern', 'failure_lesson', 'discovery', 'constraint', 'optimization')),
    content TEXT NOT NULL CHECK (char_length(content) <= 200 AND char_length(content) >= 10),
    relevance_tags TEXT[] DEFAULT '{}',
    confidence_score DECIMAL(3,2) NOT NULL DEFAULT 1.0 CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_workspace_insights_workspace_id ON workspace_insights(workspace_id);
CREATE INDEX IF NOT EXISTS idx_workspace_insights_lookup ON workspace_insights(workspace_id, insight_type, confidence_score DESC, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_workspace_insights_tags ON workspace_insights USING GIN(relevance_tags);
CREATE INDEX IF NOT EXISTS idx_workspace_insights_expires ON workspace_insights(expires_at) WHERE expires_at IS NOT NULL;

-- Create composite index for common queries
CREATE INDEX IF NOT EXISTS idx_workspace_insights_composite ON workspace_insights(workspace_id, insight_type, confidence_score DESC) WHERE expires_at IS NULL OR expires_at > NOW();

-- Add comments for documentation
COMMENT ON TABLE workspace_insights IS 'Stores AI-extracted insights from task executions for workspace memory system';
COMMENT ON COLUMN workspace_insights.workspace_id IS 'Reference to the workspace this insight belongs to';
COMMENT ON COLUMN workspace_insights.task_id IS 'Reference to the task that generated this insight';
COMMENT ON COLUMN workspace_insights.agent_role IS 'Role of the agent that generated the insight';
COMMENT ON COLUMN workspace_insights.insight_type IS 'Type of insight: success_pattern, failure_lesson, discovery, constraint, optimization';
COMMENT ON COLUMN workspace_insights.content IS 'The insight content (10-200 characters)';
COMMENT ON COLUMN workspace_insights.relevance_tags IS 'Array of tags for categorization and filtering';
COMMENT ON COLUMN workspace_insights.confidence_score IS 'Confidence in the insight (0.0-1.0)';
COMMENT ON COLUMN workspace_insights.expires_at IS 'Optional expiration date for time-sensitive insights';

-- Create function to auto-cleanup expired insights
CREATE OR REPLACE FUNCTION cleanup_expired_insights()
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM workspace_insights 
    WHERE expires_at IS NOT NULL AND expires_at < NOW();
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Log cleanup if any rows were deleted
    IF deleted_count > 0 THEN
        RAISE NOTICE 'Cleaned up % expired insights', deleted_count;
    END IF;
    
    RETURN deleted_count;
END;
$$;

-- Create scheduled cleanup (optional - requires pg_cron extension)
-- Uncomment the following line if you have pg_cron enabled:
-- SELECT cron.schedule('cleanup-expired-insights', '0 2 * * *', 'SELECT cleanup_expired_insights();');

-- Grant permissions (adjust based on your setup)
-- Replace 'your_app_user' with your actual application user
-- GRANT SELECT, INSERT, UPDATE, DELETE ON workspace_insights TO your_app_user;

-- Sample data for testing (optional)
-- INSERT INTO workspace_insights (workspace_id, task_id, agent_role, insight_type, content, relevance_tags, confidence_score)
-- VALUES 
--     (gen_random_uuid(), gen_random_uuid(), 'Analysis Specialist', 'discovery', 'LinkedIn contact research limited to 100 searches per day without automation tools', ARRAY['linkedin', 'contact_research', 'limitation'], 0.9),
--     (gen_random_uuid(), gen_random_uuid(), 'Email Specialist', 'success_pattern', 'B2B email sequences with problem-solution-urgency structure achieved 35% open rates', ARRAY['email_strategy', 'b2b', 'open_rates'], 0.95),
--     (gen_random_uuid(), gen_random_uuid(), 'Project Manager', 'constraint', 'GDPR compliance required for all EU contact data collection and storage', ARRAY['gdpr', 'compliance', 'eu_contacts'], 0.85);

-- Verify table creation
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'workspace_insights' 
ORDER BY ordinal_position;