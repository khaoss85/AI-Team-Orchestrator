-- Migration 024: Add thinking process UX enhancements (optional, non-breaking)
-- This migration adds title and summary_metadata fields to improve thinking process display
-- These fields are optional and the system works without them (backward compatible)

-- Add title field for concise AI-generated titles
ALTER TABLE thinking_processes 
ADD COLUMN IF NOT EXISTS title TEXT;

-- Add summary_metadata for essential display information
ALTER TABLE thinking_processes 
ADD COLUMN IF NOT EXISTS summary_metadata JSONB DEFAULT '{}';

-- Add indices for better performance (optional)
CREATE INDEX IF NOT EXISTS idx_thinking_processes_title 
ON thinking_processes(title);

CREATE INDEX IF NOT EXISTS idx_thinking_processes_workspace_started 
ON thinking_processes(workspace_id, started_at DESC);

-- Comment on new columns
COMMENT ON COLUMN thinking_processes.title IS 'AI-generated concise title for the thinking process';
COMMENT ON COLUMN thinking_processes.summary_metadata IS 'Essential metadata including agent, tools, duration, and token estimates';