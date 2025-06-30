-- Migration: Add 'actionability_assessment' column to quality_validations table
-- This SQL command adds the 'actionability_assessment' column to the 'quality_validations' table.
-- This column is used to store the assessment of an asset's actionability, which is a key part of the quality validation process.

-- IMPORTANT: Before running, ensure no pending transactions or locks on the 'quality_validations' table.

ALTER TABLE quality_validations
ADD COLUMN IF NOT EXISTS actionability_assessment JSONB;

-- Optional: Verify the column has been added (this is for PostgreSQL)
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'quality_validations' AND column_name = 'actionability_assessment';
