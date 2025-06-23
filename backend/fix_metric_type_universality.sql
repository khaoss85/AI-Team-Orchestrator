-- Fix Pillar 3 Compliance: Enable Universal Metric Types
-- Remove hardcoded constraint that violates language-agnostic principle

-- Remove the check constraint that limits metric_type to hardcoded enum values
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS check_metric_type;

-- Add a more flexible constraint that only ensures metric_type is reasonable length
ALTER TABLE tasks ADD CONSTRAINT check_metric_type_length 
    CHECK (metric_type IS NULL OR (length(metric_type) >= 1 AND length(metric_type) <= 100));

-- Comment explaining the change
COMMENT ON CONSTRAINT check_metric_type_length ON tasks IS 
    'Ensures metric_type is reasonable length while maintaining universal/language-agnostic compliance (Pillar 3)';

-- Update workspace_goals table to allow universal metric types as well
ALTER TABLE workspace_goals DROP CONSTRAINT IF EXISTS check_metric_type;
ALTER TABLE workspace_goals ADD CONSTRAINT check_workspace_goals_metric_type_length 
    CHECK (metric_type IS NULL OR (length(metric_type) >= 1 AND length(metric_type) <= 100));

COMMENT ON CONSTRAINT check_workspace_goals_metric_type_length ON workspace_goals IS 
    'Ensures metric_type is reasonable length while maintaining universal/language-agnostic compliance (Pillar 3)';