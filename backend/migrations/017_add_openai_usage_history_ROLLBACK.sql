-- Rollback Migration: 017_add_openai_usage_history_ROLLBACK.sql
-- Purpose: Rollback OpenAI usage history tables and related objects
-- WARNING: This will remove all historical usage data!

-- Drop views first (they depend on tables)
DROP VIEW IF EXISTS model_cost_rankings;
DROP VIEW IF EXISTS current_month_usage;

-- Drop triggers
DROP TRIGGER IF EXISTS update_usage_history_updated_at ON openai_usage_history;
DROP TRIGGER IF EXISTS update_cost_alerts_updated_at ON cost_optimization_alerts;
DROP TRIGGER IF EXISTS update_budget_tracking_updated_at ON openai_budget_tracking;

-- Drop the update function if no other tables use it
-- Be careful: only drop if no other migrations use this function
-- DROP FUNCTION IF EXISTS update_updated_at_column();

-- Drop indexes
DROP INDEX IF EXISTS idx_usage_history_workspace_date;
DROP INDEX IF EXISTS idx_usage_history_date;
DROP INDEX IF EXISTS idx_usage_history_cost;
DROP INDEX IF EXISTS idx_usage_history_aggregation;

DROP INDEX IF EXISTS idx_cost_alerts_workspace_status;
DROP INDEX IF EXISTS idx_cost_alerts_severity;
DROP INDEX IF EXISTS idx_cost_alerts_created;
DROP INDEX IF EXISTS idx_cost_alerts_expires;

DROP INDEX IF EXISTS idx_budget_tracking_workspace;
DROP INDEX IF EXISTS idx_budget_tracking_status;

-- Drop tables
DROP TABLE IF EXISTS openai_budget_tracking;
DROP TABLE IF EXISTS cost_optimization_alerts;
DROP TABLE IF EXISTS openai_usage_history;

-- Log rollback completion
DO $$
BEGIN
    RAISE NOTICE 'Rollback 017_add_openai_usage_history completed successfully';
END $$;