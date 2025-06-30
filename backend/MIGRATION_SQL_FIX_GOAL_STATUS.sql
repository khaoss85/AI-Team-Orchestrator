-- Migration: Add 'completed_pending_review' to workspace_goals status check
-- This SQL command updates the CHECK constraint for the 'status' column in the 'workspace_goals' table.
-- It adds 'completed_pending_review' as a valid status, which is used when a goal is numerically complete
-- but has a low business value score, requiring human review.

-- IMPORTANT: Before running, ensure no pending transactions or locks on the 'workspace_goals' table.

ALTER TABLE workspace_goals
DROP CONSTRAINT IF EXISTS workspace_goals_status_check;

ALTER TABLE workspace_goals
ADD CONSTRAINT workspace_goals_status_check
CHECK (status IN ('active', 'completed', 'failed', 'archived', 'completed_pending_review'));

-- Optional: Verify the constraint has been updated (this is for PostgreSQL)
-- SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'workspace_goals'::regclass AND contype = 'c';
