-- Migration: Fix thinking_steps schema for created_at column
-- Issue: Python code expects 'created_at' but table has 'timestamp'
-- Solution: Add 'created_at' column and populate from 'timestamp' for backward compatibility

-- Step 1: Add created_at column if it doesn't exist
ALTER TABLE thinking_steps 
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE;

-- Step 2: Populate created_at from existing timestamp data
UPDATE thinking_steps 
SET created_at = timestamp 
WHERE created_at IS NULL;

-- Step 3: Set default for new records
ALTER TABLE thinking_steps 
ALTER COLUMN created_at SET DEFAULT NOW();

-- Step 4: Add index for performance (matching the pattern from other tables)
CREATE INDEX IF NOT EXISTS idx_thinking_steps_created_at ON thinking_steps(created_at DESC);

-- Step 5: Update comments to reflect the change
COMMENT ON COLUMN thinking_steps.created_at IS 'Created timestamp for Python code compatibility - matches thinking_events.created_at pattern';
COMMENT ON COLUMN thinking_steps.timestamp IS 'Original timestamp column - maintained for backward compatibility';

-- Verification query (comment out in production)
-- SELECT COUNT(*) as total_steps, 
--        COUNT(created_at) as with_created_at, 
--        COUNT(timestamp) as with_timestamp
-- FROM thinking_steps;