-- Migration: 017_add_openai_usage_history.sql
-- Purpose: Store historical OpenAI usage data for trend analysis and cost tracking
-- Created: 2025
-- Part of: OpenAI Usage API v1 Integration

-- Create table to store daily usage summaries
CREATE TABLE IF NOT EXISTS openai_usage_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    
    -- Time period
    date DATE NOT NULL,
    aggregation_level VARCHAR(20) DEFAULT 'daily', -- daily, hourly, monthly
    
    -- Cost data (in USD)
    total_cost DECIMAL(10, 4) DEFAULT 0.0,
    input_cost DECIMAL(10, 4) DEFAULT 0.0,
    output_cost DECIMAL(10, 4) DEFAULT 0.0,
    
    -- Token usage
    total_tokens BIGINT DEFAULT 0,
    input_tokens BIGINT DEFAULT 0,
    output_tokens BIGINT DEFAULT 0,
    
    -- Request counts
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    
    -- Model breakdown (JSONB for flexibility)
    model_breakdown JSONB DEFAULT '{}',
    -- Example structure:
    -- {
    --   "gpt-4": {
    --     "cost": 12.50,
    --     "tokens": 100000,
    --     "requests": 50
    --   },
    --   "gpt-4o-mini": {
    --     "cost": 0.50,
    --     "tokens": 50000,
    --     "requests": 200
    --   }
    -- }
    
    -- Hourly breakdown (for daily records)
    hourly_breakdown JSONB DEFAULT '{}',
    -- Example structure:
    -- {
    --   "00:00": {"cost": 0.50, "tokens": 5000, "requests": 10},
    --   "01:00": {"cost": 0.75, "tokens": 7500, "requests": 15}
    -- }
    
    -- API method breakdown
    api_methods JSONB DEFAULT '{}',
    -- Example structure:
    -- {
    --   "chat.completions": {"requests": 100, "tokens": 50000},
    --   "embeddings": {"requests": 200, "tokens": 20000}
    -- }
    
    -- Metadata
    source VARCHAR(50) DEFAULT 'usage_api', -- usage_api, estimated, manual
    accuracy_score DECIMAL(5, 2), -- Confidence in data accuracy (0-100)
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint to prevent duplicates
    UNIQUE(workspace_id, date, aggregation_level)
);

-- Create index for efficient queries
CREATE INDEX idx_usage_history_workspace_date ON openai_usage_history(workspace_id, date DESC);
CREATE INDEX idx_usage_history_date ON openai_usage_history(date DESC);
CREATE INDEX idx_usage_history_cost ON openai_usage_history(total_cost DESC);
CREATE INDEX idx_usage_history_aggregation ON openai_usage_history(aggregation_level);

-- Create table for cost optimization alerts
CREATE TABLE IF NOT EXISTS cost_optimization_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    
    -- Alert details
    alert_type VARCHAR(50) NOT NULL, -- duplicate_calls, model_waste, prompt_bloat, etc.
    severity VARCHAR(20) NOT NULL, -- low, medium, high, critical
    title TEXT NOT NULL,
    description TEXT,
    
    -- Financial impact
    potential_daily_savings DECIMAL(10, 4) DEFAULT 0.0,
    confidence_score DECIMAL(5, 2) DEFAULT 0.0, -- 0-100
    
    -- Evidence and recommendations
    evidence JSONB DEFAULT '{}',
    recommendation TEXT,
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'active', -- active, acknowledged, resolved, ignored
    acknowledged_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ DEFAULT (CURRENT_TIMESTAMP + INTERVAL '7 days')
);

-- Create index for alert queries
CREATE INDEX idx_cost_alerts_workspace_status ON cost_optimization_alerts(workspace_id, status);
CREATE INDEX idx_cost_alerts_severity ON cost_optimization_alerts(severity);
CREATE INDEX idx_cost_alerts_created ON cost_optimization_alerts(created_at DESC);
CREATE INDEX idx_cost_alerts_expires ON cost_optimization_alerts(expires_at);

-- Create table for budget tracking
CREATE TABLE IF NOT EXISTS openai_budget_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    
    -- Budget configuration
    monthly_budget_usd DECIMAL(10, 2) DEFAULT 100.00,
    daily_limit_usd DECIMAL(10, 2),
    
    -- Current period tracking
    current_month_spend DECIMAL(10, 4) DEFAULT 0.0,
    current_day_spend DECIMAL(10, 4) DEFAULT 0.0,
    
    -- Projections
    projected_monthly_spend DECIMAL(10, 4),
    projected_overage DECIMAL(10, 4),
    
    -- Status
    budget_status VARCHAR(20) DEFAULT 'normal', -- normal, warning, critical, exceeded
    last_alert_sent TIMESTAMPTZ,
    
    -- Historical tracking
    previous_months JSONB DEFAULT '[]',
    -- Example structure:
    -- [
    --   {"month": "2025-01", "spent": 95.50, "budget": 100.00},
    --   {"month": "2024-12", "spent": 120.00, "budget": 100.00}
    -- ]
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- One budget config per workspace
    UNIQUE(workspace_id)
);

-- Create index for budget queries
CREATE INDEX idx_budget_tracking_workspace ON openai_budget_tracking(workspace_id);
CREATE INDEX idx_budget_tracking_status ON openai_budget_tracking(budget_status);

-- Create function to update timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_usage_history_updated_at BEFORE UPDATE ON openai_usage_history
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cost_alerts_updated_at BEFORE UPDATE ON cost_optimization_alerts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_budget_tracking_updated_at BEFORE UPDATE ON openai_budget_tracking
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create view for current month summary
CREATE OR REPLACE VIEW current_month_usage AS
SELECT 
    workspace_id,
    DATE_TRUNC('month', date) as month,
    SUM(total_cost) as total_cost,
    SUM(total_tokens) as total_tokens,
    SUM(total_requests) as total_requests,
    jsonb_object_agg(
        date::text,
        jsonb_build_object(
            'cost', total_cost,
            'tokens', total_tokens,
            'requests', total_requests
        )
    ) as daily_breakdown
FROM openai_usage_history
WHERE date >= DATE_TRUNC('month', CURRENT_DATE)
    AND aggregation_level = 'daily'
GROUP BY workspace_id, DATE_TRUNC('month', date);

-- Create view for model cost rankings
CREATE OR REPLACE VIEW model_cost_rankings AS
SELECT 
    workspace_id,
    model_key as model,
    SUM((model_data->>'cost')::decimal) as total_cost,
    SUM((model_data->>'tokens')::bigint) as total_tokens,
    SUM((model_data->>'requests')::integer) as total_requests,
    RANK() OVER (PARTITION BY workspace_id ORDER BY SUM((model_data->>'cost')::decimal) DESC) as cost_rank
FROM openai_usage_history,
     jsonb_each(model_breakdown) as models(model_key, model_data)
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY workspace_id, model_key;

-- Insert initial budget tracking for existing workspaces
INSERT INTO openai_budget_tracking (workspace_id, monthly_budget_usd)
SELECT id, 100.00
FROM workspaces
WHERE id NOT IN (SELECT workspace_id FROM openai_budget_tracking)
ON CONFLICT (workspace_id) DO NOTHING;

-- Add comment explaining the schema
COMMENT ON TABLE openai_usage_history IS 'Stores historical OpenAI API usage data fetched from Usage API v1 for cost tracking and analysis';
COMMENT ON TABLE cost_optimization_alerts IS 'AI-generated alerts for cost optimization opportunities based on usage patterns';
COMMENT ON TABLE openai_budget_tracking IS 'Tracks budget limits and spending projections per workspace';

-- Grant appropriate permissions (adjust based on your user setup)
-- GRANT SELECT, INSERT, UPDATE ON openai_usage_history TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE ON cost_optimization_alerts TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE ON openai_budget_tracking TO your_app_user;
-- GRANT SELECT ON current_month_usage TO your_app_user;
-- GRANT SELECT ON model_cost_rankings TO your_app_user;