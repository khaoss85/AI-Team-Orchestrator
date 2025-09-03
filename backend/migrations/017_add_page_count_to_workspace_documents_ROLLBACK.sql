-- Rollback Migration: Remove page_count field from workspace_documents table
-- Purpose: Rollback for adding page_count column
-- Date: 2025-09-02

-- Drop the index first
DROP INDEX IF EXISTS idx_workspace_documents_page_count;

-- Remove the page_count column
ALTER TABLE workspace_documents 
DROP COLUMN IF EXISTS page_count;

-- Restore the original view without page_count
CREATE OR REPLACE VIEW documents_with_content AS
SELECT 
    wd.*,
    LENGTH(wd.extracted_text) as content_length,
    CASE 
        WHEN wd.extraction_confidence >= 0.9 THEN 'high'
        WHEN wd.extraction_confidence >= 0.7 THEN 'medium'
        WHEN wd.extraction_confidence >= 0.5 THEN 'low'
        ELSE 'very_low'
    END as confidence_level
FROM workspace_documents wd
WHERE wd.extracted_text IS NOT NULL;