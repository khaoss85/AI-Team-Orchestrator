-- FINAL FIX: Add missing task_id column to goal_progress_logs table
-- This is the last missing piece preventing task completion

-- Add the task_id column (nullable because not all progress logs are task-related)
ALTER TABLE public.goal_progress_logs
ADD COLUMN IF NOT EXISTS task_id UUID NULL;

-- Add foreign key constraint to maintain referential integrity
ALTER TABLE public.goal_progress_logs
ADD CONSTRAINT IF NOT EXISTS fk_goal_progress_logs_task_id 
FOREIGN KEY (task_id) REFERENCES public.tasks(id) ON DELETE SET NULL;

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_goal_progress_logs_task_id
ON public.goal_progress_logs USING btree (task_id);

-- Add column comment for documentation
COMMENT ON COLUMN public.goal_progress_logs.task_id IS 'Reference to the task that triggered this progress update (nullable for non-task progress)';

-- Verify the fix with a test query
DO $$
BEGIN
    -- Check that the column exists
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'goal_progress_logs' 
        AND column_name = 'task_id'
        AND table_schema = 'public'
    ) THEN
        RAISE NOTICE 'SUCCESS: task_id column exists in goal_progress_logs';
    ELSE
        RAISE EXCEPTION 'FAILED: task_id column is missing from goal_progress_logs';
    END IF;
    
    -- Check that the foreign key exists
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name LIKE '%goal_progress_logs_task_id%'
        AND table_name = 'goal_progress_logs'
        AND constraint_type = 'FOREIGN KEY'
    ) THEN
        RAISE NOTICE 'SUCCESS: Foreign key constraint exists for task_id';
    ELSE
        RAISE NOTICE 'INFO: Foreign key constraint not found (may use different naming)';
    END IF;
END $$;

-- Show final table structure to confirm
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'goal_progress_logs' AND table_schema = 'public'
ORDER BY ordinal_position;