-- Add content extraction fields to workspace_documents
-- Migration 013: PDF Content Extraction Support for RAG System
-- Enables true content retrieval beyond metadata search

-- Add columns for extracted content from PDFs
ALTER TABLE workspace_documents 
ADD COLUMN IF NOT EXISTS extracted_text TEXT,
ADD COLUMN IF NOT EXISTS text_chunks JSONB,
ADD COLUMN IF NOT EXISTS extraction_confidence FLOAT;

-- Add indexes for content search performance
CREATE INDEX IF NOT EXISTS idx_workspace_documents_extracted_text 
    ON workspace_documents USING gin(to_tsvector('english', COALESCE(extracted_text, '')));

CREATE INDEX IF NOT EXISTS idx_workspace_documents_text_chunks 
    ON workspace_documents USING gin(text_chunks);

CREATE INDEX IF NOT EXISTS idx_workspace_documents_extraction_confidence 
    ON workspace_documents(extraction_confidence);

-- Comments for documentation
COMMENT ON COLUMN workspace_documents.extracted_text IS 'Full extracted text content from the document (first 5000 chars stored)';
COMMENT ON COLUMN workspace_documents.text_chunks IS 'Chunked text for RAG retrieval (first 10 chunks stored as JSONB)';
COMMENT ON COLUMN workspace_documents.extraction_confidence IS 'Confidence score of content extraction quality (0.0-1.0)';

-- Grant permissions (if using row-level security)
-- Uncomment if RLS is enabled on the table
-- GRANT SELECT ON workspace_documents TO authenticated;
-- GRANT INSERT, UPDATE ON workspace_documents TO authenticated;

-- Migration verification query
-- Run this to verify the migration was successful:
-- SELECT column_name, data_type 
-- FROM information_schema.columns 
-- WHERE table_name = 'workspace_documents' 
-- AND column_name IN ('extracted_text', 'text_chunks', 'extraction_confidence');