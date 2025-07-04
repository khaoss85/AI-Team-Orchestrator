-- Migration: Add workspace_id to asset_artifacts table
-- Purpose: Link asset_artifacts directly to workspaces for better data integrity and querying.

ALTER TABLE asset_artifacts
ADD COLUMN IF NOT EXISTS workspace_id UUID;

-- Optional: Add a foreign key constraint if the 'workspaces' table exists and 'id' is its primary key
-- This ensures referential integrity. Uncomment if applicable.
-- ALTER TABLE asset_artifacts
-- ADD CONSTRAINT fk_asset_artifacts_workspace
-- FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE;

-- Optional: Create an index for faster lookups by workspace_id
CREATE INDEX IF NOT EXISTS idx_asset_artifacts_workspace_id ON asset_artifacts (workspace_id);

-- Optional: Populate existing records with a workspace_id if possible
-- This assumes you have a way to derive the workspace_id for existing artifacts.
-- For example, if artifacts are linked to goal_asset_requirements which are linked to workspace_goals.
-- This part is highly dependent on your existing data structure and might require a custom script.
-- Example (conceptual, adjust as needed):
-- UPDATE asset_artifacts aa
-- SET workspace_id = wg.workspace_id
-- FROM goal_asset_requirements gar
-- JOIN workspace_goals wg ON gar.goal_id = wg.id
-- WHERE aa.goal_asset_requirement_id = gar.id
-- AND aa.workspace_id IS NULL;

COMMENT ON COLUMN asset_artifacts.workspace_id IS 'Foreign key to the workspace this asset artifact belongs to.';

RAISE NOTICE 'Column workspace_id added to asset_artifacts table and indexed.';
