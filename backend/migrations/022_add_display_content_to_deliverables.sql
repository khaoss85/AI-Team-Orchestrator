-- Migration 022: Add AI-Driven Dual-Format Display Fields to deliverables table
-- Date: 2025-09-03
-- Purpose: Enable persistent storage of AI-transformed display content to prevent infinite OpenAI loops
-- Issue Fixed: Deliverables were being re-transformed on EVERY API request causing quota exhaustion
-- Backward compatible: YES - All fields have proper defaults

BEGIN;

-- Add display content fields to deliverables table (similar to asset_artifacts)
ALTER TABLE deliverables 
ADD COLUMN IF NOT EXISTS display_content TEXT,
ADD COLUMN IF NOT EXISTS display_format VARCHAR(20) DEFAULT 'html',
ADD COLUMN IF NOT EXISTS display_summary TEXT,
ADD COLUMN IF NOT EXISTS display_metadata JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS auto_display_generated BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS display_content_updated_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS transformation_timestamp TIMESTAMP;

-- Add content transformation tracking fields
ALTER TABLE deliverables
ADD COLUMN IF NOT EXISTS content_transformation_status VARCHAR(20) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS content_transformation_error TEXT,
ADD COLUMN IF NOT EXISTS transformation_method VARCHAR(20) DEFAULT 'ai';

-- Add display quality metrics
ALTER TABLE deliverables
ADD COLUMN IF NOT EXISTS display_quality_score FLOAT DEFAULT 0.0 CHECK (display_quality_score >= 0.0 AND display_quality_score <= 1.0),
ADD COLUMN IF NOT EXISTS user_friendliness_score FLOAT DEFAULT 0.0 CHECK (user_friendliness_score >= 0.0 AND user_friendliness_score <= 1.0),
ADD COLUMN IF NOT EXISTS readability_score FLOAT DEFAULT 0.0 CHECK (readability_score >= 0.0 AND readability_score <= 1.0);

-- Add field to track AI confidence for display transformation
ALTER TABLE deliverables
ADD COLUMN IF NOT EXISTS ai_confidence FLOAT DEFAULT 0.0 CHECK (ai_confidence >= 0.0 AND ai_confidence <= 1.0);

-- Add indexes for performance on commonly queried fields
CREATE INDEX IF NOT EXISTS idx_deliverables_display_format ON deliverables(display_format);
CREATE INDEX IF NOT EXISTS idx_deliverables_transformation_status ON deliverables(content_transformation_status);
CREATE INDEX IF NOT EXISTS idx_deliverables_display_quality ON deliverables(display_quality_score) WHERE display_quality_score > 0.0;
CREATE INDEX IF NOT EXISTS idx_deliverables_auto_generated ON deliverables(auto_display_generated) WHERE auto_display_generated = true;
CREATE INDEX IF NOT EXISTS idx_deliverables_transformation_timestamp ON deliverables(transformation_timestamp) WHERE transformation_timestamp IS NOT NULL;

-- Add comments for documentation
COMMENT ON COLUMN deliverables.display_content IS 'AI-transformed user-friendly display content (HTML/Markdown) - PERSISTED to prevent re-transformation';
COMMENT ON COLUMN deliverables.display_format IS 'Format of display content: html, markdown, or text';
COMMENT ON COLUMN deliverables.display_summary IS 'Brief summary for UI cards and previews';
COMMENT ON COLUMN deliverables.display_metadata IS 'Display-specific metadata like styling, layout hints';
COMMENT ON COLUMN deliverables.content_transformation_status IS 'Status: pending, success, failed, skipped';
COMMENT ON COLUMN deliverables.transformation_timestamp IS 'When the display content was last transformed - CRITICAL for cache checking';
COMMENT ON COLUMN deliverables.display_quality_score IS 'Quality assessment of display content (0.0-1.0)';
COMMENT ON COLUMN deliverables.user_friendliness_score IS 'How user-friendly the display format is (0.0-1.0)';
COMMENT ON COLUMN deliverables.readability_score IS 'Text readability score (0.0-1.0)';
COMMENT ON COLUMN deliverables.ai_confidence IS 'AI confidence score for the transformation (0.0-1.0)';

-- Mark existing deliverables as needing transformation
UPDATE deliverables 
SET 
    display_format = 'html',
    content_transformation_status = CASE 
        WHEN content IS NOT NULL AND content != '{}' AND content != '[]' THEN 'pending'
        ELSE 'skipped'
    END,
    transformation_method = 'pending' -- Will be set to 'ai' after first transformation
WHERE display_format IS NULL;

COMMIT;

-- Performance verification query
-- This shows how many deliverables need transformation vs already transformed
SELECT 
    COUNT(*) as total_deliverables,
    COUNT(display_content) as with_display_content,
    COUNT(CASE WHEN content_transformation_status = 'pending' THEN 1 END) as pending_transformation,
    COUNT(CASE WHEN content_transformation_status = 'success' THEN 1 END) as already_transformed,
    COUNT(CASE WHEN transformation_timestamp IS NOT NULL THEN 1 END) as with_timestamp,
    AVG(display_quality_score) as avg_display_quality
FROM deliverables;

-- Query to identify deliverables causing infinite loops (no display_content despite being completed)
SELECT 
    id, 
    title, 
    status,
    CASE 
        WHEN display_content IS NULL THEN 'NEEDS_TRANSFORMATION'
        ELSE 'CACHED'
    END as cache_status,
    transformation_timestamp
FROM deliverables
WHERE status = 'completed'
ORDER BY created_at DESC
LIMIT 10;