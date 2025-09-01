-- ROLLBACK Migration 016: Enhance workspace_insights table for Content-Aware Learning System
-- Purpose: Remove domain-specific enhancements if needed

-- Drop views
DROP VIEW IF EXISTS high_value_domain_insights;
DROP VIEW IF EXISTS domain_insights_summary;

-- Drop trigger and function
DROP TRIGGER IF EXISTS trigger_update_learning_priority ON workspace_insights;
DROP FUNCTION IF EXISTS update_learning_priority();

-- Drop indices (in reverse order of creation)
DROP INDEX IF EXISTS idx_workspace_insights_performance;
DROP INDEX IF EXISTS idx_workspace_insights_domain_learning;
DROP INDEX IF EXISTS idx_workspace_insights_validation_status;
DROP INDEX IF EXISTS idx_workspace_insights_content_source;
DROP INDEX IF EXISTS idx_workspace_insights_insight_category;
DROP INDEX IF EXISTS idx_workspace_insights_quality_threshold;
DROP INDEX IF EXISTS idx_workspace_insights_business_value;
DROP INDEX IF EXISTS idx_workspace_insights_domain_workspace;
DROP INDEX IF EXISTS idx_workspace_insights_domain_type;

-- Remove constraints
ALTER TABLE workspace_insights DROP CONSTRAINT IF EXISTS chk_extraction_method;
ALTER TABLE workspace_insights DROP CONSTRAINT IF EXISTS chk_content_source_type;
ALTER TABLE workspace_insights DROP CONSTRAINT IF EXISTS chk_insight_category;
ALTER TABLE workspace_insights DROP CONSTRAINT IF EXISTS chk_domain_type;
ALTER TABLE workspace_insights DROP CONSTRAINT IF EXISTS chk_quality_threshold;
ALTER TABLE workspace_insights DROP CONSTRAINT IF EXISTS chk_performance_impact_score;
ALTER TABLE workspace_insights DROP CONSTRAINT IF EXISTS chk_business_value_score;
ALTER TABLE workspace_insights DROP CONSTRAINT IF EXISTS chk_validation_status;

-- Remove columns (in reverse order of addition)
ALTER TABLE workspace_insights DROP COLUMN IF EXISTS last_applied_at;
ALTER TABLE workspace_insights DROP COLUMN IF EXISTS application_count;
ALTER TABLE workspace_insights DROP COLUMN IF EXISTS performance_impact_score;
ALTER TABLE workspace_insights DROP COLUMN IF EXISTS learning_priority;
ALTER TABLE workspace_insights DROP COLUMN IF EXISTS validation_status;
ALTER TABLE workspace_insights DROP COLUMN IF EXISTS quality_threshold;
ALTER TABLE workspace_insights DROP COLUMN IF EXISTS extraction_method;
ALTER TABLE workspace_insights DROP COLUMN IF EXISTS content_source_type;
ALTER TABLE workspace_insights DROP COLUMN IF EXISTS insight_category;
ALTER TABLE workspace_insights DROP COLUMN IF EXISTS business_value_score;
ALTER TABLE workspace_insights DROP COLUMN IF EXISTS action_recommendations;
ALTER TABLE workspace_insights DROP COLUMN IF EXISTS quantifiable_metrics;
ALTER TABLE workspace_insights DROP COLUMN IF EXISTS domain_specific_metadata;
ALTER TABLE workspace_insights DROP COLUMN IF EXISTS domain_type;

-- Success message
SELECT 'ROLLBACK Migration 016 completed successfully: Removed Content-Aware Learning System enhancements' as status;