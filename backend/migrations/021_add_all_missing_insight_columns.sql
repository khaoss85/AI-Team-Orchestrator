-- =============================================================================
-- 🔧 ADD ALL MISSING COLUMNS FOR USER INSIGHTS MANAGEMENT
-- =============================================================================
-- Migration: 021_add_all_missing_insight_columns.sql
-- Purpose: Add all missing columns required by User Insights Management System
-- Issue: Multiple columns expected by the system don't exist in workspace_insights
-- Date: 2025-09-03
-- =============================================================================

-- Add missing columns one by one with proper defaults
ALTER TABLE workspace_insights 
ADD COLUMN IF NOT EXISTS business_value_score FLOAT DEFAULT 0.5;

ALTER TABLE workspace_insights 
ADD COLUMN IF NOT EXISTS quantifiable_metrics JSONB DEFAULT '{}';

ALTER TABLE workspace_insights 
ADD COLUMN IF NOT EXISTS insight_category VARCHAR(100) DEFAULT 'general';

ALTER TABLE workspace_insights 
ADD COLUMN IF NOT EXISTS domain_type VARCHAR(100) DEFAULT 'general';

ALTER TABLE workspace_insights 
ADD COLUMN IF NOT EXISTS action_recommendations TEXT[] DEFAULT '{}';

-- Add comments for documentation
COMMENT ON COLUMN workspace_insights.business_value_score IS 
'Business value score from 0.0 to 1.0 indicating the importance of this insight';

COMMENT ON COLUMN workspace_insights.quantifiable_metrics IS 
'JSON object containing quantifiable metrics associated with the insight';

COMMENT ON COLUMN workspace_insights.insight_category IS 
'Category classification for the insight (e.g., knowledge, learning, best_practice)';

COMMENT ON COLUMN workspace_insights.domain_type IS 
'Business domain type (e.g., technical, business, operational)';

COMMENT ON COLUMN workspace_insights.action_recommendations IS 
'Array of actionable recommendations derived from the insight';

-- =============================================================================
-- VERIFICATION
-- =============================================================================

DO $$
DECLARE
    missing_columns TEXT := '';
    col_exists BOOLEAN;
BEGIN
    -- Check each column exists
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workspace_insights' AND column_name = 'business_value_score'
    ) INTO col_exists;
    IF NOT col_exists THEN
        missing_columns := missing_columns || 'business_value_score, ';
    END IF;
    
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workspace_insights' AND column_name = 'quantifiable_metrics'
    ) INTO col_exists;
    IF NOT col_exists THEN
        missing_columns := missing_columns || 'quantifiable_metrics, ';
    END IF;
    
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workspace_insights' AND column_name = 'insight_category'
    ) INTO col_exists;
    IF NOT col_exists THEN
        missing_columns := missing_columns || 'insight_category, ';
    END IF;
    
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workspace_insights' AND column_name = 'domain_type'
    ) INTO col_exists;
    IF NOT col_exists THEN
        missing_columns := missing_columns || 'domain_type, ';
    END IF;
    
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workspace_insights' AND column_name = 'action_recommendations'
    ) INTO col_exists;
    IF NOT col_exists THEN
        missing_columns := missing_columns || 'action_recommendations, ';
    END IF;
    
    -- Report results
    IF missing_columns = '' THEN
        RAISE NOTICE '✅ All required columns successfully added to workspace_insights table';
    ELSE
        RAISE EXCEPTION '❌ Failed to add columns: %', missing_columns;
    END IF;
END $$;

-- Grant permissions if needed
GRANT SELECT, INSERT, UPDATE ON workspace_insights TO authenticated;

RAISE NOTICE '🚀 Migration 021 completed - All missing columns added for User Insights Management!';