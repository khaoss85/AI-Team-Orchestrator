-- Add content_type column to memory_patterns table
ALTER TABLE public.memory_patterns
ADD COLUMN content_type TEXT;

-- Add a comment to describe the new column's purpose
COMMENT ON COLUMN public.memory_patterns.content_type IS 'Stores the content type of the learned pattern (e.g., text, json, code).';
