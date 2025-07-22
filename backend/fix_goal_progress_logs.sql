-- Fix goal_progress_logs table structure and constraints
-- Run this SQL script manually in your Supabase SQL editor

-- First, drop the table if it exists with wrong structure
DROP TABLE IF EXISTS goal_progress_logs CASCADE;

-- Create goal_progress_logs table with correct structure
CREATE TABLE goal_progress_logs (
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
CREATE INDEX idx_goal_progress_logs_goal_id ON goal_progress_logs(goal_id);
CREATE INDEX idx_goal_progress_logs_timestamp ON goal_progress_logs(timestamp);
CREATE INDEX idx_goal_progress_logs_created_at ON goal_progress_logs(created_at);

-- Add foreign key constraint (if workspace_goals table exists)
DO $$
BEGIN
    -- Check if workspace_goals table exists and add FK constraint
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'workspace_goals' AND table_schema = 'public') THEN
        ALTER TABLE goal_progress_logs 
        ADD CONSTRAINT fk_goal_progress_logs_goal_id 
        FOREIGN KEY (goal_id) REFERENCES workspace_goals(id) ON DELETE CASCADE;
        
        RAISE NOTICE 'Added foreign key constraint to workspace_goals';
    ELSE 
        RAISE NOTICE 'workspace_goals table not found, skipping FK constraint';
    END IF;
EXCEPTION 
    WHEN duplicate_object THEN 
        RAISE NOTICE 'Foreign key constraint already exists';
END $$;

-- Add table comment
COMMENT ON TABLE goal_progress_logs IS 'Tracks progress updates for workspace goals with timestamps and quality metrics';

-- Add column comments
COMMENT ON COLUMN goal_progress_logs.goal_id IS 'Reference to workspace_goals.id';
COMMENT ON COLUMN goal_progress_logs.progress_percentage IS 'Progress percentage (0-100)';
COMMENT ON COLUMN goal_progress_logs.quality_score IS 'Quality score (0-100)';
COMMENT ON COLUMN goal_progress_logs.timestamp IS 'When this progress measurement was taken';
COMMENT ON COLUMN goal_progress_logs.calculation_method IS 'Method used to calculate progress (manual, asset_driven, etc.)';
COMMENT ON COLUMN goal_progress_logs.metadata IS 'Additional metadata about the progress calculation';

-- Test the table by inserting and deleting a test record
DO $$
DECLARE
    test_id UUID;
BEGIN
    -- Insert test record
    INSERT INTO goal_progress_logs (goal_id, progress_percentage, quality_score, calculation_method, metadata)
    VALUES ('00000000-0000-0000-0000-000000000000', 50.0, 75.5, 'test_verification', '{"test": true}')
    RETURNING id INTO test_id;
    
    -- Delete test record
    DELETE FROM goal_progress_logs WHERE id = test_id;
    
    RAISE NOTICE 'Table structure verification successful';
EXCEPTION 
    WHEN OTHERS THEN 
        RAISE EXCEPTION 'Table verification failed: %', SQLERRM;
END $$;

-- Show final table structure
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'goal_progress_logs' 
ORDER BY ordinal_position;