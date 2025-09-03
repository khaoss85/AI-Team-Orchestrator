-- =============================================================================
-- 🔧 ADD MISSING ACTION_RECOMMENDATIONS COLUMN
-- =============================================================================
-- Migration: 020_add_missing_action_recommendations_column.sql
-- Purpose: Add missing action_recommendations column to workspace_insights table
-- Issue: User Insights Management System expects this column but it doesn't exist
-- Date: 2025-09-03
-- =============================================================================

-- Add the missing column
ALTER TABLE workspace_insights 
ADD COLUMN IF NOT EXISTS action_recommendations TEXT[] DEFAULT '{}';

-- Add comment for documentation
COMMENT ON COLUMN workspace_insights.action_recommendations IS 
'Array of actionable recommendations derived from the insight. Used by User Insights Management System.';

-- =============================================================================
-- VERIFICATION
-- =============================================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'workspace_insights' 
        AND column_name = 'action_recommendations'
    ) THEN
        RAISE NOTICE '✅ Column action_recommendations successfully added to workspace_insights table';
    ELSE
        RAISE EXCEPTION '❌ Failed to add action_recommendations column';
    END IF;
END $$;

-- Grant permissions if needed
GRANT SELECT, INSERT, UPDATE ON workspace_insights TO authenticated;

RAISE NOTICE '🚀 Migration 020 completed - action_recommendations column added!';