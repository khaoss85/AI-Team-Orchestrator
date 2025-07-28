-- Add business_context column to memory_patterns table
ALTER TABLE memory_patterns ADD COLUMN business_context TEXT;

-- Add a comment to describe the new column's purpose
COMMENT ON COLUMN memory_patterns.business_context IS 'Stores the business context or domain-specific information related to the learned pattern.';
