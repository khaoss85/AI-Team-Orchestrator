-- ========================================================================
-- Task Semantic Hash Migration - Database-First Deduplication Support
-- ========================================================================
-- Adds semantic_hash column and unique constraint to tasks table
-- Required for TaskDeduplicationManager database-first approach
-- ========================================================================

-- 1. Add semantic_hash column to tasks table
ALTER TABLE tasks 
ADD COLUMN IF NOT EXISTS semantic_hash VARCHAR(64);

-- 2. Create unique constraint on (workspace_id, semantic_hash)
-- This prevents duplicate tasks with identical semantic content
ALTER TABLE tasks 
ADD CONSTRAINT unique_task_semantic_hash_per_workspace 
UNIQUE (workspace_id, semantic_hash);

-- 3. Add index for performance on semantic hash lookups
CREATE INDEX IF NOT EXISTS idx_tasks_semantic_hash ON tasks(semantic_hash);

-- 4. Add comment for documentation
COMMENT ON COLUMN tasks.semantic_hash IS 
'SHA-256 hash of task semantic content (name, description, goal_id) for deduplication';

COMMENT ON CONSTRAINT unique_task_semantic_hash_per_workspace ON tasks IS 
'Prevents duplicate tasks with identical semantic content within the same workspace';

-- 5. Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Task semantic hash migration completed successfully!';
    RAISE NOTICE '🔗 Database-first deduplication system is now ready';
    RAISE NOTICE '🚫 Duplicate tasks will be blocked at database level';
END $$;