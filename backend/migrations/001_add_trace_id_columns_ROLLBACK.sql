-- Rollback: Remove trace_id columns from all tables
-- Date: 2025-07-06
-- Purpose: Rollback script for 001_add_trace_id_columns.sql

-- WARNING: This will remove all trace_id data from the database
-- Only run this if you need to completely rollback the trace implementation

BEGIN;

-- Drop indexes first (before dropping columns)
DROP INDEX IF EXISTS idx_workspaces_trace_id;
DROP INDEX IF EXISTS idx_workspace_goals_trace_id;
DROP INDEX IF EXISTS idx_tasks_trace_id;
DROP INDEX IF EXISTS idx_agents_trace_id;
DROP INDEX IF EXISTS idx_execution_logs_trace_id;
DROP INDEX IF EXISTS idx_thinking_process_steps_trace_id;
DROP INDEX IF EXISTS idx_asset_artifacts_trace_id;
DROP INDEX IF EXISTS idx_deliverables_trace_id;
DROP INDEX IF EXISTS idx_workspace_deliverables_trace_id;
DROP INDEX IF EXISTS idx_human_feedback_requests_trace_id;
DROP INDEX IF EXISTS idx_team_proposals_trace_id;

-- Remove trace_id columns from all tables
ALTER TABLE workspaces DROP COLUMN IF EXISTS trace_id;
ALTER TABLE workspace_goals DROP COLUMN IF EXISTS trace_id;
ALTER TABLE tasks DROP COLUMN IF EXISTS trace_id;
ALTER TABLE agents DROP COLUMN IF EXISTS trace_id;
ALTER TABLE execution_logs DROP COLUMN IF EXISTS trace_id;

-- Conditional column drops for tables that might not exist
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'thinking_process_steps') THEN
        EXECUTE 'ALTER TABLE thinking_process_steps DROP COLUMN IF EXISTS trace_id';
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'asset_artifacts') THEN
        EXECUTE 'ALTER TABLE asset_artifacts DROP COLUMN IF EXISTS trace_id';
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'deliverables') THEN
        EXECUTE 'ALTER TABLE deliverables DROP COLUMN IF EXISTS trace_id';
    ELSIF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'workspace_deliverables') THEN
        EXECUTE 'ALTER TABLE workspace_deliverables DROP COLUMN IF EXISTS trace_id';
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'human_feedback_requests') THEN
        EXECUTE 'ALTER TABLE human_feedback_requests DROP COLUMN IF EXISTS trace_id';
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'team_proposals') THEN
        EXECUTE 'ALTER TABLE team_proposals DROP COLUMN IF EXISTS trace_id';
    END IF;
END $$;

COMMIT;