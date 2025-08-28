-- Migration 013: Add AI-Driven Dual-Format Display Fields to deliverables table
-- Date: 2025-08-28
-- Purpose: Enable dual-format architecture for the deliverables table (currently used by API)
-- Backward compatible: YES - All fields have proper defaults

BEGIN;

-- Add display content fields
ALTER TABLE deliverables 
ADD COLUMN IF NOT EXISTS display_content TEXT,
ADD COLUMN IF NOT EXISTS display_format VARCHAR(20) DEFAULT 'html',
ADD COLUMN IF NOT EXISTS display_summary TEXT,
ADD COLUMN IF NOT EXISTS display_metadata JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS auto_display_generated BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS display_content_updated_at TIMESTAMP;

-- Add content transformation tracking fields
ALTER TABLE deliverables
ADD COLUMN IF NOT EXISTS content_transformation_status VARCHAR(20) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS content_transformation_error TEXT,
ADD COLUMN IF NOT EXISTS transformation_timestamp TIMESTAMP,
ADD COLUMN IF NOT EXISTS transformation_method VARCHAR(20) DEFAULT 'ai';

-- Add display quality metrics
ALTER TABLE deliverables
ADD COLUMN IF NOT EXISTS display_quality_score FLOAT DEFAULT 0.0 CHECK (display_quality_score >= 0.0 AND display_quality_score <= 1.0),
ADD COLUMN IF NOT EXISTS user_friendliness_score FLOAT DEFAULT 0.0 CHECK (user_friendliness_score >= 0.0 AND user_friendliness_score <= 1.0),
ADD COLUMN IF NOT EXISTS readability_score FLOAT DEFAULT 0.0 CHECK (readability_score >= 0.0 AND readability_score <= 1.0);

-- Add field to track AI confidence for display transformation
ALTER TABLE deliverables
ADD COLUMN IF NOT EXISTS ai_confidence FLOAT DEFAULT 0.0 CHECK (ai_confidence >= 0.0 AND ai_confidence <= 1.0);

-- Add timestamps for better tracking (if they don't exist)
ALTER TABLE deliverables
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Create performance indexes for dual-format queries
CREATE INDEX IF NOT EXISTS idx_deliverables_display_format ON deliverables(display_format);
CREATE INDEX IF NOT EXISTS idx_deliverables_transformation_status ON deliverables(content_transformation_status);
CREATE INDEX IF NOT EXISTS idx_deliverables_display_quality ON deliverables(display_quality_score);
CREATE INDEX IF NOT EXISTS idx_deliverables_auto_generated ON deliverables(auto_display_generated);
CREATE INDEX IF NOT EXISTS idx_deliverables_workspace_status ON deliverables(workspace_id, content_transformation_status);

-- Update existing deliverables to mark them as needing transformation
UPDATE deliverables 
SET content_transformation_status = 'pending',
    transformation_timestamp = NOW(),
    updated_at = NOW()
WHERE content_transformation_status IS NULL OR content_transformation_status = 'pending';

COMMIT;

-- Validation queries (run these after migration)
-- SELECT COUNT(*) as total_deliverables FROM deliverables;
-- SELECT content_transformation_status, COUNT(*) FROM deliverables GROUP BY content_transformation_status;
-- SELECT display_format, COUNT(*) FROM deliverables GROUP BY display_format;

-- Migration complete! ✅