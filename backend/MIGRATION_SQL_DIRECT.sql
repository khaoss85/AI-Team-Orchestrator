-- DIRECT SQL MIGRATION FOR THINKING_STEPS TABLE
-- Execute this directly in Supabase SQL Editor or psql

-- Step 1: Add created_at column
ALTER TABLE thinking_steps 
ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Step 2: Copy existing timestamp data to created_at
UPDATE thinking_steps 
SET created_at = timestamp;

-- Step 3: Add index for performance
CREATE INDEX idx_thinking_steps_created_at ON thinking_steps(created_at DESC);

-- Step 4: Verify the migration
SELECT 
    COUNT(*) as total_rows,
    COUNT(timestamp) as with_timestamp,
    COUNT(created_at) as with_created_at,
    MIN(created_at) as earliest_created_at,
    MAX(created_at) as latest_created_at
FROM thinking_steps;