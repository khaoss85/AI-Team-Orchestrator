-- Migration: Add page_count field to workspace_documents table
-- Purpose: Fix missing page_count column causing document upload failures
-- Date: 2025-09-02

-- Add page_count column for PDF and document processing
ALTER TABLE workspace_documents 
ADD COLUMN IF NOT EXISTS page_count INTEGER;

-- Add index for better performance on page_count queries
CREATE INDEX IF NOT EXISTS idx_workspace_documents_page_count 
ON workspace_documents(page_count) 
WHERE page_count IS NOT NULL;

-- Add comment explaining the field
COMMENT ON COLUMN workspace_documents.page_count IS 'Number of pages in document (for PDFs and other paginated documents)';

-- Set default page_count to 1 for existing documents without page count
UPDATE workspace_documents 
SET page_count = 1 
WHERE page_count IS NULL 
  AND mime_type IN ('application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document');

-- Update the view to include page_count
CREATE OR REPLACE VIEW documents_with_content AS
SELECT 
    wd.*,
    LENGTH(wd.extracted_text) as content_length,
    CASE 
        WHEN wd.extraction_confidence >= 0.9 THEN 'high'
        WHEN wd.extraction_confidence >= 0.7 THEN 'medium'
        WHEN wd.extraction_confidence >= 0.5 THEN 'low'
        ELSE 'very_low'
    END as confidence_level,
    CASE 
        WHEN wd.page_count IS NULL THEN 'unknown'
        WHEN wd.page_count = 1 THEN 'single_page'
        WHEN wd.page_count <= 10 THEN 'short'
        WHEN wd.page_count <= 50 THEN 'medium'
        ELSE 'long'
    END as document_length
FROM workspace_documents wd
WHERE wd.extracted_text IS NOT NULL;

-- Grant permissions
GRANT ALL ON workspace_documents TO authenticated;