-- Create general system logs table to fix workspace health manager error
-- This is separate from execution_logs and handles general system logging

-- Create logs table
CREATE TABLE IF NOT EXISTS logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID DEFAULT NULL,
    type VARCHAR(50) NOT NULL DEFAULT 'info',
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add indexes for performance  
CREATE INDEX IF NOT EXISTS idx_logs_workspace_id ON logs(workspace_id);
CREATE INDEX IF NOT EXISTS idx_logs_type ON logs(type);
CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at);

-- Add table comment
COMMENT ON TABLE logs IS 'General system logs for monitoring, alerts, and audit trail';

-- Add column comments
COMMENT ON COLUMN logs.workspace_id IS 'Associated workspace (nullable for system-wide logs)';
COMMENT ON COLUMN logs.type IS 'Log type (info, warning, error, alert, system, etc.)';
COMMENT ON COLUMN logs.message IS 'Human-readable log message';
COMMENT ON COLUMN logs.metadata IS 'Additional structured data about the log entry';

-- Test the table by inserting and deleting a test record
DO $$
DECLARE
    test_id UUID;
BEGIN
    -- Insert test record
    INSERT INTO logs (type, message, metadata)
    VALUES ('test', 'Table structure verification', '{"test": true}')
    RETURNING id INTO test_id;
    
    -- Delete test record
    DELETE FROM logs WHERE id = test_id;
    
    RAISE NOTICE 'Logs table structure verification successful';
EXCEPTION 
    WHEN OTHERS THEN 
        RAISE EXCEPTION 'Logs table verification failed: %', SQLERRM;
END $$;

-- Show final table structure
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'logs' AND table_schema = 'public'
ORDER BY ordinal_position;