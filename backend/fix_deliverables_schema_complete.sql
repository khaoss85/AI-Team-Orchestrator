-- FIX DELIVERABLES TABLE SCHEMA: Add all missing AI-driven columns
-- This adds the columns needed for AI-generated deliverables with quality scores

-- Add missing AI quality and scoring columns
ALTER TABLE public.deliverables 
ADD COLUMN IF NOT EXISTS business_specificity_score DECIMAL(5,2) DEFAULT 0.00;

ALTER TABLE public.deliverables
ADD COLUMN IF NOT EXISTS tool_usage_score DECIMAL(5,2) DEFAULT 0.00;

ALTER TABLE public.deliverables
ADD COLUMN IF NOT EXISTS content_quality_score DECIMAL(5,2) DEFAULT 0.00;

ALTER TABLE public.deliverables
ADD COLUMN IF NOT EXISTS creation_confidence DECIMAL(5,2) DEFAULT 0.00;

ALTER TABLE public.deliverables
ADD COLUMN IF NOT EXISTS creation_reasoning TEXT NULL;

ALTER TABLE public.deliverables
ADD COLUMN IF NOT EXISTS learning_patterns_created INTEGER DEFAULT 0;

ALTER TABLE public.deliverables
ADD COLUMN IF NOT EXISTS execution_time DECIMAL(10,3) DEFAULT 0.000;

ALTER TABLE public.deliverables
ADD COLUMN IF NOT EXISTS stages_completed INTEGER DEFAULT 0;

ALTER TABLE public.deliverables
ADD COLUMN IF NOT EXISTS auto_improvements INTEGER DEFAULT 0;

ALTER TABLE public.deliverables
ADD COLUMN IF NOT EXISTS quality_level VARCHAR(50) DEFAULT 'acceptable';

-- Add comments for documentation
COMMENT ON COLUMN public.deliverables.business_specificity_score IS 'AI-calculated score for business domain specificity (0-100)';
COMMENT ON COLUMN public.deliverables.tool_usage_score IS 'AI-calculated score for effective tool usage (0-100)';
COMMENT ON COLUMN public.deliverables.content_quality_score IS 'AI-calculated overall content quality score (0-100)';
COMMENT ON COLUMN public.deliverables.creation_confidence IS 'AI confidence in deliverable creation (0-100)';
COMMENT ON COLUMN public.deliverables.creation_reasoning IS 'AI reasoning behind deliverable creation and quality assessment';
COMMENT ON COLUMN public.deliverables.learning_patterns_created IS 'Number of learning patterns created during generation';
COMMENT ON COLUMN public.deliverables.execution_time IS 'Time taken to execute deliverable generation (in seconds)';
COMMENT ON COLUMN public.deliverables.stages_completed IS 'Number of pipeline stages completed';
COMMENT ON COLUMN public.deliverables.auto_improvements IS 'Number of automatic improvements applied';
COMMENT ON COLUMN public.deliverables.quality_level IS 'Qualitative quality assessment: excellent, good, acceptable';

-- Show final table structure
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'deliverables' AND table_schema = 'public'
ORDER BY ordinal_position;