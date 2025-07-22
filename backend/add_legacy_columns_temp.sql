-- TEMPORARY FIX: Add legacy columns to goal_progress_logs table
-- This allows the system to work while we identify and fix the source of the legacy field references

-- Add the legacy columns as nullable to avoid breaking existing functionality
ALTER TABLE public.goal_progress_logs
ADD COLUMN IF NOT EXISTS previous_value DECIMAL(10,2) NULL;

ALTER TABLE public.goal_progress_logs  
ADD COLUMN IF NOT EXISTS new_value DECIMAL(10,2) NULL;

ALTER TABLE public.goal_progress_logs
ADD COLUMN IF NOT EXISTS change_reason VARCHAR(255) NULL;

-- Add comments to indicate these are temporary
COMMENT ON COLUMN public.goal_progress_logs.previous_value IS 'TEMPORARY: Legacy column for backward compatibility';
COMMENT ON COLUMN public.goal_progress_logs.new_value IS 'TEMPORARY: Legacy column for backward compatibility';
COMMENT ON COLUMN public.goal_progress_logs.change_reason IS 'TEMPORARY: Legacy column for backward compatibility';

-- Show final structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'goal_progress_logs' AND table_schema = 'public'
ORDER BY ordinal_position;