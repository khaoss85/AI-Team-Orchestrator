-- Add missing AI-driven goal extraction columns to workspace_goals table

-- Add confidence column for AI extraction confidence scoring
ALTER TABLE workspace_goals 
ADD COLUMN IF NOT EXISTS confidence DECIMAL(3,2) DEFAULT 0.8 CHECK (confidence >= 0.0 AND confidence <= 1.0);

-- Add semantic_context column for AI-driven contextual understanding
ALTER TABLE workspace_goals 
ADD COLUMN IF NOT EXISTS semantic_context JSONB DEFAULT '{}';

-- Add comments for documentation
COMMENT ON COLUMN workspace_goals.confidence IS 'AI extraction confidence score (0.0-1.0)';
COMMENT ON COLUMN workspace_goals.semantic_context IS 'AI-extracted semantic context and metadata';

-- Update existing records to have default confidence
UPDATE workspace_goals 
SET confidence = 0.8 
WHERE confidence IS NULL;

-- Update existing records to have empty semantic context
UPDATE workspace_goals 
SET semantic_context = '{}' 
WHERE semantic_context IS NULL;

-- Create index for confidence-based queries
CREATE INDEX IF NOT EXISTS idx_workspace_goals_confidence ON workspace_goals(confidence);

-- Create index for semantic_context queries
CREATE INDEX IF NOT EXISTS idx_workspace_goals_semantic_context ON workspace_goals USING GIN(semantic_context);

-- Verify the changes
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'workspace_goals' 
AND column_name IN ('confidence', 'semantic_context')
ORDER BY column_name;