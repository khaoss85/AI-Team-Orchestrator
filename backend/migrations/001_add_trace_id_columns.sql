-- Migration: Add trace_id columns to critical tables
-- Date: 2025-07-06
-- Phase: 1 - Critical Interventions
-- Purpose: Enable end-to-end traceability across all database operations

-- This migration adds trace_id UUID columns to all critical tables
-- to support X-Trace-ID propagation throughout the system

BEGIN;

-- Add trace_id columns to critical tables
-- These columns will store the X-Trace-ID from the request that created/modified the record

-- 1. WORKSPACES table
ALTER TABLE workspaces 
ADD COLUMN IF NOT EXISTS trace_id UUID;

-- 2. WORKSPACE_GOALS table  
ALTER TABLE workspace_goals 
ADD COLUMN IF NOT EXISTS trace_id UUID;

-- 3. TASKS table
ALTER TABLE tasks 
ADD COLUMN IF NOT EXISTS trace_id UUID;

-- 4. AGENTS table
ALTER TABLE agents 
ADD COLUMN IF NOT EXISTS trace_id UUID;

-- 5. EXECUTION_LOGS table
ALTER TABLE execution_logs 
ADD COLUMN IF NOT EXISTS trace_id UUID;

-- 6. THINKING_PROCESS_STEPS table (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'thinking_process_steps') THEN
        EXECUTE 'ALTER TABLE thinking_process_steps ADD COLUMN IF NOT EXISTS trace_id UUID';
    END IF;
END $$;

-- 7. ASSET_ARTIFACTS table (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'asset_artifacts') THEN
        EXECUTE 'ALTER TABLE asset_artifacts ADD COLUMN IF NOT EXISTS trace_id UUID';
    END IF;
END $$;

-- 8. DELIVERABLES table (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'deliverables') THEN
        EXECUTE 'ALTER TABLE deliverables ADD COLUMN IF NOT EXISTS trace_id UUID';
    ELSIF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'workspace_deliverables') THEN
        EXECUTE 'ALTER TABLE workspace_deliverables ADD COLUMN IF NOT EXISTS trace_id UUID';
    END IF;
END $$;

-- 9. HUMAN_FEEDBACK_REQUESTS table (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'human_feedback_requests') THEN
        EXECUTE 'ALTER TABLE human_feedback_requests ADD COLUMN IF NOT EXISTS trace_id UUID';
    END IF;
END $$;

-- 10. TEAM_PROPOSALS table (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'team_proposals') THEN
        EXECUTE 'ALTER TABLE team_proposals ADD COLUMN IF NOT EXISTS trace_id UUID';
    END IF;
END $$;

-- Add indexes for performance on trace_id columns
-- These indexes will enable fast queries by trace_id for debugging and audit

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_workspaces_trace_id 
ON workspaces(trace_id) WHERE trace_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_workspace_goals_trace_id 
ON workspace_goals(trace_id) WHERE trace_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tasks_trace_id 
ON tasks(trace_id) WHERE trace_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agents_trace_id 
ON agents(trace_id) WHERE trace_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_execution_logs_trace_id 
ON execution_logs(trace_id) WHERE trace_id IS NOT NULL;

-- Conditional indexes for tables that might not exist
DO $$
BEGIN
    -- thinking_process_steps index
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'thinking_process_steps') THEN
        EXECUTE 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_thinking_process_steps_trace_id 
                 ON thinking_process_steps(trace_id) WHERE trace_id IS NOT NULL';
    END IF;
    
    -- asset_artifacts index
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'asset_artifacts') THEN
        EXECUTE 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_asset_artifacts_trace_id 
                 ON asset_artifacts(trace_id) WHERE trace_id IS NOT NULL';
    END IF;
    
    -- deliverables index
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'deliverables') THEN
        EXECUTE 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_deliverables_trace_id 
                 ON deliverables(trace_id) WHERE trace_id IS NOT NULL';
    ELSIF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'workspace_deliverables') THEN
        EXECUTE 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_workspace_deliverables_trace_id 
                 ON workspace_deliverables(trace_id) WHERE trace_id IS NOT NULL';
    END IF;
    
    -- human_feedback_requests index
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'human_feedback_requests') THEN
        EXECUTE 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_human_feedback_requests_trace_id 
                 ON human_feedback_requests(trace_id) WHERE trace_id IS NOT NULL';
    END IF;
    
    -- team_proposals index
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'team_proposals') THEN
        EXECUTE 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_team_proposals_trace_id 
                 ON team_proposals(trace_id) WHERE trace_id IS NOT NULL';
    END IF;
END $$;

-- Add comments to document the purpose of trace_id columns
COMMENT ON COLUMN workspaces.trace_id IS 'X-Trace-ID from the request that created/modified this workspace';
COMMENT ON COLUMN workspace_goals.trace_id IS 'X-Trace-ID from the request that created/modified this goal';
COMMENT ON COLUMN tasks.trace_id IS 'X-Trace-ID from the request that created/modified this task';
COMMENT ON COLUMN agents.trace_id IS 'X-Trace-ID from the request that created/modified this agent';
COMMENT ON COLUMN execution_logs.trace_id IS 'X-Trace-ID from the request that created this log entry';

COMMIT;

-- Verification queries to confirm the migration
-- These can be run separately to verify the migration was successful

/*
-- Check that trace_id columns were added to all expected tables
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE column_name = 'trace_id' 
AND table_schema = 'public'
ORDER BY table_name;

-- Check that indexes were created
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE indexname LIKE '%trace_id%'
ORDER BY tablename, indexname;

-- Count tables with trace_id column
SELECT COUNT(*) as tables_with_trace_id
FROM information_schema.columns 
WHERE column_name = 'trace_id' 
AND table_schema = 'public';
*/