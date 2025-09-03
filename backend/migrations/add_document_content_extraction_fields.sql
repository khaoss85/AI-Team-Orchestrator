-- Migration: Add document content extraction fields for true RAG capability
-- Purpose: Enable storage of extracted text content from PDFs and other documents
-- Date: 2025-09-02

-- Add columns for content extraction to workspace_documents table
ALTER TABLE workspace_documents 
ADD COLUMN IF NOT EXISTS extracted_text TEXT,
ADD COLUMN IF NOT EXISTS text_chunks JSONB,
ADD COLUMN IF NOT EXISTS extraction_confidence FLOAT,
ADD COLUMN IF NOT EXISTS extraction_method VARCHAR(50),
ADD COLUMN IF NOT EXISTS extraction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Add indexes for better search performance
CREATE INDEX IF NOT EXISTS idx_workspace_documents_extracted_text 
ON workspace_documents USING gin(to_tsvector('english', COALESCE(extracted_text, '')));

CREATE INDEX IF NOT EXISTS idx_workspace_documents_extraction_confidence 
ON workspace_documents(extraction_confidence);

CREATE INDEX IF NOT EXISTS idx_workspace_documents_workspace_extracted 
ON workspace_documents(workspace_id, extraction_confidence) 
WHERE extracted_text IS NOT NULL;

-- Add comment explaining the fields
COMMENT ON COLUMN workspace_documents.extracted_text IS 'Extracted text content from the document (first 5000 chars for storage efficiency)';
COMMENT ON COLUMN workspace_documents.text_chunks IS 'JSON array of text chunks for retrieval, with overlap for context preservation';
COMMENT ON COLUMN workspace_documents.extraction_confidence IS 'Confidence score (0.0-1.0) indicating quality of extraction';
COMMENT ON COLUMN workspace_documents.extraction_method IS 'Method used for extraction (pymupdf, pdfplumber, pypdf2, openai, fallback)';
COMMENT ON COLUMN workspace_documents.extraction_timestamp IS 'When the content was extracted';

-- Create a view for documents with extracted content
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

-- Grant permissions
GRANT SELECT ON documents_with_content TO authenticated;
GRANT ALL ON workspace_documents TO authenticated;