-- Create goal_progress_logs table
CREATE TABLE IF NOT EXISTS goal_progress_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID NOT NULL,
    progress_percentage DECIMAL(5,2) NOT NULL DEFAULT 0,
    quality_score DECIMAL(5,2) DEFAULT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    calculation_method VARCHAR(100) DEFAULT 'manual',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_goal_progress_logs_goal_id ON goal_progress_logs(goal_id);
CREATE INDEX IF NOT EXISTS idx_goal_progress_logs_timestamp ON goal_progress_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_goal_progress_logs_created_at ON goal_progress_logs(created_at);

-- Add foreign key constraint (if workspace_goals table exists)
-- Note: This will silently fail if workspace_goals doesn't exist, which is fine
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'workspace_goals') THEN
        ALTER TABLE goal_progress_logs 
        ADD CONSTRAINT fk_goal_progress_logs_goal_id 
        FOREIGN KEY (goal_id) REFERENCES workspace_goals(id) ON DELETE CASCADE;
    END IF;
EXCEPTION 
    WHEN duplicate_object THEN NULL;
END $$;

-- Add comment
COMMENT ON TABLE goal_progress_logs IS 'Tracks progress updates for workspace goals with timestamps and quality metrics';
EOF < /dev/null
