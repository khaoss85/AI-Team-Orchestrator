-- COMPLETE SCHEMA FIX for AI Goal Extraction
-- Adds all missing columns needed for AI-driven goal extraction

-- Add goal_type column (required by AI extractor)
ALTER TABLE workspace_goals 
ADD COLUMN IF NOT EXISTS goal_type TEXT DEFAULT 'deliverable' 
CHECK (goal_type IN ('deliverable', 'metric', 'quality', 'timeline', 'quantity'));

-- Add confidence column for AI extraction confidence scoring  
ALTER TABLE workspace_goals 
ADD COLUMN IF NOT EXISTS confidence DECIMAL(3,2) DEFAULT 0.8 
CHECK (confidence >= 0.0 AND confidence <= 1.0);

-- Add semantic_context column for AI-driven contextual understanding
ALTER TABLE workspace_goals 
ADD COLUMN IF NOT EXISTS semantic_context JSONB DEFAULT '{}'::jsonb;

-- Add is_percentage column (used by AI extractor)
ALTER TABLE workspace_goals 
ADD COLUMN IF NOT EXISTS is_percentage BOOLEAN DEFAULT false;

-- Add is_minimum column (used by AI extractor) 
ALTER TABLE workspace_goals 
ADD COLUMN IF NOT EXISTS is_minimum BOOLEAN DEFAULT false;

-- Update existing records to have default values
UPDATE workspace_goals SET goal_type = 'deliverable' WHERE goal_type IS NULL;
UPDATE workspace_goals SET confidence = 0.8 WHERE confidence IS NULL;
UPDATE workspace_goals SET semantic_context = '{}'::jsonb WHERE semantic_context IS NULL;
UPDATE workspace_goals SET is_percentage = false WHERE is_percentage IS NULL;
UPDATE workspace_goals SET is_minimum = false WHERE is_minimum IS NULL;

-- Create helpful indexes for AI queries
CREATE INDEX IF NOT EXISTS idx_workspace_goals_goal_type ON workspace_goals(goal_type);
CREATE INDEX IF NOT EXISTS idx_workspace_goals_confidence ON workspace_goals(confidence);
CREATE INDEX IF NOT EXISTS idx_workspace_goals_semantic_context ON workspace_goals USING GIN(semantic_context);
CREATE INDEX IF NOT EXISTS idx_workspace_goals_ai_flags ON workspace_goals(is_percentage, is_minimum);

-- Add comments for documentation
COMMENT ON COLUMN workspace_goals.goal_type IS 'AI-extracted goal type: deliverable, metric, quality, timeline, quantity';
COMMENT ON COLUMN workspace_goals.confidence IS 'AI extraction confidence score (0.0-1.0)';
COMMENT ON COLUMN workspace_goals.semantic_context IS 'AI-extracted semantic context and metadata';
COMMENT ON COLUMN workspace_goals.is_percentage IS 'True if target_value represents a percentage';
COMMENT ON COLUMN workspace_goals.is_minimum IS 'True if target_value is a minimum threshold (≥)';

-- Verify the schema changes
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'workspace_goals' 
AND column_name IN ('goal_type', 'confidence', 'semantic_context', 'is_percentage', 'is_minimum')
ORDER BY column_name;