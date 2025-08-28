-- Migration 012: Add AI-Driven Dual-Format Display Fields to asset_artifacts
-- Date: 2025-08-28
-- Purpose: Enable dual-format architecture with execution and display content separation
-- Backward compatible: YES - All fields have proper defaults

BEGIN;

-- Add display content fields
ALTER TABLE asset_artifacts 
ADD COLUMN IF NOT EXISTS display_content TEXT,
ADD COLUMN IF NOT EXISTS display_format VARCHAR(20) DEFAULT 'html',
ADD COLUMN IF NOT EXISTS display_summary TEXT,
ADD COLUMN IF NOT EXISTS display_metadata JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS auto_display_generated BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS display_content_updated_at TIMESTAMP;

-- Add content transformation tracking fields
ALTER TABLE asset_artifacts
ADD COLUMN IF NOT EXISTS content_transformation_status VARCHAR(20) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS content_transformation_error TEXT,
ADD COLUMN IF NOT EXISTS transformation_timestamp TIMESTAMP,
ADD COLUMN IF NOT EXISTS transformation_method VARCHAR(20) DEFAULT 'ai';

-- Add display quality metrics
ALTER TABLE asset_artifacts
ADD COLUMN IF NOT EXISTS display_quality_score FLOAT DEFAULT 0.0 CHECK (display_quality_score >= 0.0 AND display_quality_score <= 1.0),
ADD COLUMN IF NOT EXISTS user_friendliness_score FLOAT DEFAULT 0.0 CHECK (user_friendliness_score >= 0.0 AND user_friendliness_score <= 1.0),
ADD COLUMN IF NOT EXISTS readability_score FLOAT DEFAULT 0.0 CHECK (readability_score >= 0.0 AND readability_score <= 1.0);

-- Add field to track AI confidence for display transformation
ALTER TABLE asset_artifacts
ADD COLUMN IF NOT EXISTS ai_confidence FLOAT DEFAULT 0.0 CHECK (ai_confidence >= 0.0 AND ai_confidence <= 1.0);

-- Add indexes for performance on commonly queried fields
CREATE INDEX IF NOT EXISTS idx_asset_artifacts_display_format ON asset_artifacts(display_format);
CREATE INDEX IF NOT EXISTS idx_asset_artifacts_transformation_status ON asset_artifacts(content_transformation_status);
CREATE INDEX IF NOT EXISTS idx_asset_artifacts_display_quality ON asset_artifacts(display_quality_score) WHERE display_quality_score > 0.0;
CREATE INDEX IF NOT EXISTS idx_asset_artifacts_auto_generated ON asset_artifacts(auto_display_generated) WHERE auto_display_generated = true;

-- Add comments for documentation
COMMENT ON COLUMN asset_artifacts.display_content IS 'AI-transformed user-friendly display content (HTML/Markdown)';
COMMENT ON COLUMN asset_artifacts.display_format IS 'Format of display content: html, markdown, or text';
COMMENT ON COLUMN asset_artifacts.display_summary IS 'Brief summary for UI cards and previews';
COMMENT ON COLUMN asset_artifacts.display_metadata IS 'Display-specific metadata like styling, layout hints';
COMMENT ON COLUMN asset_artifacts.content_transformation_status IS 'Status: pending, success, failed, skipped';
COMMENT ON COLUMN asset_artifacts.transformation_timestamp IS 'When the display content was last transformed';
COMMENT ON COLUMN asset_artifacts.display_quality_score IS 'Quality assessment of display content (0.0-1.0)';
COMMENT ON COLUMN asset_artifacts.user_friendliness_score IS 'How user-friendly the display format is (0.0-1.0)';
COMMENT ON COLUMN asset_artifacts.readability_score IS 'Text readability score (0.0-1.0)';

-- Update existing records with default values where appropriate
UPDATE asset_artifacts 
SET 
    display_format = 'html',
    content_transformation_status = CASE 
        WHEN content IS NOT NULL AND content != '{}' THEN 'pending'
        ELSE 'skipped'
    END,
    display_quality_score = LEAST(quality_score, 1.0), -- Map existing quality_score to display range
    transformation_method = 'manual' -- Mark existing records as manually created
WHERE display_format IS NULL;

COMMIT;

-- Performance verification query
-- This should complete quickly on the updated table
SELECT 
    COUNT(*) as total_artifacts,
    COUNT(display_content) as with_display_content,
    COUNT(CASE WHEN content_transformation_status = 'pending' THEN 1 END) as pending_transformation,
    AVG(display_quality_score) as avg_display_quality
FROM asset_artifacts;