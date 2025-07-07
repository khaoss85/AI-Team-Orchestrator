-- ====================================================================
-- UNIQUE CONSTRAINTS - Database Integrity Enhancement (Task 1.10)
-- ====================================================================
-- Adds UNIQUE constraints to critical tables to prevent duplicate entries
-- and improve data integrity. Part of Phase 1 refactoring plan.
-- 
-- Execute manually via SQL Editor per user instruction
-- ====================================================================

-- 1. WORKSPACES TABLE - Prevent duplicate workspace names per user
-- ====================================================================
-- Add unique constraint on (user_id, name) to prevent users from creating
-- workspaces with identical names

ALTER TABLE workspaces 
ADD CONSTRAINT unique_workspace_per_user 
UNIQUE (user_id, name);

-- Optional: Add index for performance (automatically created with UNIQUE constraint)
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_workspaces_user_name ON workspaces(user_id, name);

COMMENT ON CONSTRAINT unique_workspace_per_user ON workspaces IS 
'Prevents duplicate workspace names for the same user';


-- 2. AGENTS TABLE - Prevent duplicate agent names/roles per workspace
-- ====================================================================
-- Add unique constraint on (workspace_id, name) to prevent duplicate agent names
-- within the same workspace

ALTER TABLE agents 
ADD CONSTRAINT unique_agent_name_per_workspace 
UNIQUE (workspace_id, name);

-- Optional: Also prevent duplicate role+seniority combinations per workspace
-- This ensures role specialization within teams
ALTER TABLE agents 
ADD CONSTRAINT unique_agent_role_seniority_per_workspace 
UNIQUE (workspace_id, role, seniority);

COMMENT ON CONSTRAINT unique_agent_name_per_workspace ON agents IS 
'Prevents duplicate agent names within the same workspace';

COMMENT ON CONSTRAINT unique_agent_role_seniority_per_workspace ON agents IS 
'Prevents duplicate role+seniority combinations within the same workspace';


-- 3. TASKS TABLE - Prevent duplicate task names per workspace
-- ====================================================================
-- Add unique constraint on (workspace_id, name) to prevent duplicate task names
-- within the same workspace

ALTER TABLE tasks 
ADD CONSTRAINT unique_task_name_per_workspace 
UNIQUE (workspace_id, name);

COMMENT ON CONSTRAINT unique_task_name_per_workspace ON tasks IS 
'Prevents duplicate task names within the same workspace';


-- 4. CUSTOM_TOOLS TABLE - Prevent duplicate tool names per workspace
-- ====================================================================
-- Add unique constraint on (workspace_id, name) to prevent duplicate tool names

ALTER TABLE custom_tools 
ADD CONSTRAINT unique_tool_name_per_workspace 
UNIQUE (workspace_id, name);

COMMENT ON CONSTRAINT unique_tool_name_per_workspace ON custom_tools IS 
'Prevents duplicate tool names within the same workspace';


-- 5. AGENT_HANDOFFS TABLE - Prevent duplicate handoff configurations
-- ====================================================================
-- Add unique constraint to prevent duplicate handoff paths between same agents

ALTER TABLE agent_handoffs 
ADD CONSTRAINT unique_agent_handoff_path 
UNIQUE (source_agent_id, target_agent_id);

COMMENT ON CONSTRAINT unique_agent_handoff_path ON agent_handoffs IS 
'Prevents duplicate handoff configurations between the same agent pair';


-- 6. TEAM_PROPOSALS TABLE - Prevent duplicate proposals per workspace
-- ====================================================================
-- Add unique constraint to prevent multiple pending proposals for same workspace
-- (only applies to pending status to allow historical tracking)

-- Create partial unique index for pending proposals only
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS unique_pending_team_proposal_per_workspace 
ON team_proposals (workspace_id) 
WHERE status = 'pending';

COMMENT ON INDEX unique_pending_team_proposal_per_workspace IS 
'Prevents multiple pending team proposals for the same workspace';


-- 7. HUMAN_FEEDBACK_REQUESTS TABLE - Prevent duplicate pending requests
-- ====================================================================
-- Add constraint to prevent duplicate pending feedback requests of same type

CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS unique_pending_feedback_request 
ON human_feedback_requests (workspace_id, request_type, title) 
WHERE status = 'pending';

COMMENT ON INDEX unique_pending_feedback_request IS 
'Prevents duplicate pending feedback requests of same type and title per workspace';


-- 8. DOCUMENTS TABLE - Prevent duplicate document names per workspace+agent
-- ====================================================================
-- Add unique constraint on (workspace_id, agent_id, name) for document uniqueness

ALTER TABLE documents 
ADD CONSTRAINT unique_document_per_agent_workspace 
UNIQUE (workspace_id, agent_id, name);

COMMENT ON CONSTRAINT unique_document_per_agent_workspace ON documents IS 
'Prevents duplicate document names for the same agent within a workspace';


-- ====================================================================
-- VALIDATION QUERIES - Run these to verify constraint creation
-- ====================================================================

-- Check all newly created constraints
SELECT 
    tc.table_name,
    tc.constraint_name,
    tc.constraint_type,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints tc
LEFT JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
LEFT JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.table_schema = 'public'
    AND tc.constraint_name LIKE '%unique%'
    AND tc.table_name IN ('workspaces', 'agents', 'tasks', 'custom_tools', 'agent_handoffs', 'documents')
ORDER BY tc.table_name, tc.constraint_name;

-- Check unique indexes
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public'
    AND indexname LIKE '%unique%'
    AND tablename IN ('team_proposals', 'human_feedback_requests')
ORDER BY tablename, indexname;


-- ====================================================================
-- EXPECTED BENEFITS
-- ====================================================================
-- ✅ Prevents duplicate workspace names per user
-- ✅ Prevents duplicate agent names and role conflicts per workspace  
-- ✅ Prevents duplicate task names per workspace
-- ✅ Prevents duplicate tool names per workspace
-- ✅ Prevents duplicate handoff configurations
-- ✅ Prevents multiple pending team proposals per workspace
-- ✅ Prevents duplicate pending feedback requests
-- ✅ Prevents duplicate document names per agent/workspace
-- ✅ Improves data integrity score in audit
-- ✅ Reduces potential for data corruption and conflicts
-- ✅ Enables more reliable business logic

-- Expected audit score improvement: +15-20 points (targeting 70/100 for Phase 1)