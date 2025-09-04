-- ROLLBACK Migration 022: Remove AI-Driven Dual-Format Display Fields from deliverables table
-- Date: 2025-09-03
-- Purpose: Rollback display content fields if needed

BEGIN;

-- Drop indexes first
DROP INDEX IF EXISTS idx_deliverables_display_format;
DROP INDEX IF EXISTS idx_deliverables_transformation_status;
DROP INDEX IF EXISTS idx_deliverables_display_quality;
DROP INDEX IF EXISTS idx_deliverables_auto_generated;
DROP INDEX IF EXISTS idx_deliverables_transformation_timestamp;

-- Remove display content fields
ALTER TABLE deliverables 
DROP COLUMN IF EXISTS display_content,
DROP COLUMN IF EXISTS display_format,
DROP COLUMN IF EXISTS display_summary,
DROP COLUMN IF EXISTS display_metadata,
DROP COLUMN IF EXISTS auto_display_generated,
DROP COLUMN IF EXISTS display_content_updated_at,
DROP COLUMN IF EXISTS transformation_timestamp;

-- Remove content transformation tracking fields
ALTER TABLE deliverables
DROP COLUMN IF EXISTS content_transformation_status,
DROP COLUMN IF EXISTS content_transformation_error,
DROP COLUMN IF EXISTS transformation_method;

-- Remove display quality metrics
ALTER TABLE deliverables
DROP COLUMN IF EXISTS display_quality_score,
DROP COLUMN IF EXISTS user_friendliness_score,
DROP COLUMN IF EXISTS readability_score;

-- Remove AI confidence field
ALTER TABLE deliverables
DROP COLUMN IF EXISTS ai_confidence;

COMMIT;

-- Verification query
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'deliverables'
    AND column_name LIKE 'display_%' 
    OR column_name LIKE 'transformation_%'
ORDER BY ordinal_position;