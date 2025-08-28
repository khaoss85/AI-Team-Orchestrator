-- Rollback Migration 012: Remove AI-Driven Dual-Format Display Fields
-- Date: 2025-08-28
-- Purpose: Safely rollback dual-format architecture changes
-- WARNING: This will permanently remove display content data

BEGIN;

-- Drop indexes first (order matters for dependencies)
DROP INDEX IF EXISTS idx_asset_artifacts_display_format;
DROP INDEX IF EXISTS idx_asset_artifacts_transformation_status;
DROP INDEX IF EXISTS idx_asset_artifacts_display_quality;
DROP INDEX IF EXISTS idx_asset_artifacts_auto_generated;

-- Remove display content fields
ALTER TABLE asset_artifacts 
DROP COLUMN IF EXISTS display_content,
DROP COLUMN IF EXISTS display_format,
DROP COLUMN IF EXISTS display_summary,
DROP COLUMN IF EXISTS display_metadata,
DROP COLUMN IF EXISTS auto_display_generated,
DROP COLUMN IF EXISTS display_content_updated_at;

-- Remove transformation tracking fields
ALTER TABLE asset_artifacts
DROP COLUMN IF EXISTS content_transformation_status,
DROP COLUMN IF EXISTS content_transformation_error,
DROP COLUMN IF EXISTS transformation_timestamp,
DROP COLUMN IF EXISTS transformation_method;

-- Remove display quality metrics
ALTER TABLE asset_artifacts
DROP COLUMN IF EXISTS display_quality_score,
DROP COLUMN IF EXISTS user_friendliness_score,
DROP COLUMN IF EXISTS readability_score;

-- Remove AI confidence field
ALTER TABLE asset_artifacts
DROP COLUMN IF EXISTS ai_confidence;

COMMIT;

-- Verification: Confirm columns are removed
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'asset_artifacts' 
AND column_name LIKE 'display%' OR column_name LIKE '%transformation%';
-- This query should return no results if rollback was successful