-- Migration 016: Enhance workspace_insights table for Content-Aware Learning System
-- Purpose: Add domain-specific fields for storing BusinessInsight data with quantifiable metrics

-- Add domain-specific columns to workspace_insights table
ALTER TABLE workspace_insights ADD COLUMN IF NOT EXISTS domain_type TEXT DEFAULT 'general';
ALTER TABLE workspace_insights ADD COLUMN IF NOT EXISTS domain_specific_metadata JSONB DEFAULT '{}';
ALTER TABLE workspace_insights ADD COLUMN IF NOT EXISTS quantifiable_metrics JSONB DEFAULT '{}';
ALTER TABLE workspace_insights ADD COLUMN IF NOT EXISTS action_recommendations JSONB DEFAULT '[]';
ALTER TABLE workspace_insights ADD COLUMN IF NOT EXISTS business_value_score DECIMAL(3,2) DEFAULT 0.0;

-- Add new insight categories for content-aware learning
ALTER TABLE workspace_insights ADD COLUMN IF NOT EXISTS insight_category TEXT DEFAULT 'general';
ALTER TABLE workspace_insights ADD COLUMN IF NOT EXISTS content_source_type TEXT DEFAULT 'task_result';
ALTER TABLE workspace_insights ADD COLUMN IF NOT EXISTS extraction_method TEXT DEFAULT 'manual';

-- Add quality and validation fields
ALTER TABLE workspace_insights ADD COLUMN IF NOT EXISTS quality_threshold DECIMAL(3,2) DEFAULT 0.0;
ALTER TABLE workspace_insights ADD COLUMN IF NOT EXISTS validation_status TEXT DEFAULT 'pending';
ALTER TABLE workspace_insights ADD COLUMN IF NOT EXISTS learning_priority INTEGER DEFAULT 1;

-- Add performance tracking fields
ALTER TABLE workspace_insights ADD COLUMN IF NOT EXISTS performance_impact_score DECIMAL(3,2) DEFAULT 0.0;
ALTER TABLE workspace_insights ADD COLUMN IF NOT EXISTS application_count INTEGER DEFAULT 0;
ALTER TABLE workspace_insights ADD COLUMN IF NOT EXISTS last_applied_at TIMESTAMP;

-- Create indices for efficient domain-specific queries
CREATE INDEX IF NOT EXISTS idx_workspace_insights_domain_type ON workspace_insights(domain_type);
CREATE INDEX IF NOT EXISTS idx_workspace_insights_domain_workspace ON workspace_insights(domain_type, workspace_id);
CREATE INDEX IF NOT EXISTS idx_workspace_insights_business_value ON workspace_insights(business_value_score DESC);
CREATE INDEX IF NOT EXISTS idx_workspace_insights_quality_threshold ON workspace_insights(quality_threshold);
CREATE INDEX IF NOT EXISTS idx_workspace_insights_insight_category ON workspace_insights(insight_category);
CREATE INDEX IF NOT EXISTS idx_workspace_insights_content_source ON workspace_insights(content_source_type);
CREATE INDEX IF NOT EXISTS idx_workspace_insights_validation_status ON workspace_insights(validation_status);

-- Create composite index for domain-specific learning queries
CREATE INDEX IF NOT EXISTS idx_workspace_insights_domain_learning 
    ON workspace_insights(domain_type, workspace_id, business_value_score DESC, confidence_score DESC);

-- Create index for performance tracking
CREATE INDEX IF NOT EXISTS idx_workspace_insights_performance 
    ON workspace_insights(performance_impact_score DESC, application_count DESC);

-- Add constraints for data integrity
ALTER TABLE workspace_insights ADD CONSTRAINT IF NOT EXISTS chk_business_value_score 
    CHECK (business_value_score >= 0.0 AND business_value_score <= 1.0);
ALTER TABLE workspace_insights ADD CONSTRAINT IF NOT EXISTS chk_performance_impact_score 
    CHECK (performance_impact_score >= 0.0 AND performance_impact_score <= 1.0);
ALTER TABLE workspace_insights ADD CONSTRAINT IF NOT EXISTS chk_quality_threshold 
    CHECK (quality_threshold >= 0.0 AND quality_threshold <= 1.0);

-- Add check constraint for valid domain types (expandable)
ALTER TABLE workspace_insights ADD CONSTRAINT IF NOT EXISTS chk_domain_type 
    CHECK (domain_type IN ('general', 'instagram_marketing', 'email_marketing', 'lead_generation', 
                          'content_creation', 'social_media', 'advertising', 'analytics', 
                          'customer_engagement', 'conversion_optimization', 'seo', 'brand_management'));

-- Add check constraint for valid insight categories
ALTER TABLE workspace_insights ADD CONSTRAINT IF NOT EXISTS chk_insight_category 
    CHECK (insight_category IN ('general', 'performance_metric', 'best_practice', 'optimization_tip', 
                                'failure_pattern', 'success_pattern', 'timing_insight', 'audience_insight',
                                'content_strategy', 'engagement_tactic', 'conversion_strategy'));

-- Add check constraint for content source types
ALTER TABLE workspace_insights ADD CONSTRAINT IF NOT EXISTS chk_content_source_type 
    CHECK (content_source_type IN ('task_result', 'deliverable_content', 'user_feedback', 
                                  'system_analysis', 'performance_data', 'external_api'));

-- Add check constraint for extraction methods
ALTER TABLE workspace_insights ADD CONSTRAINT IF NOT EXISTS chk_extraction_method 
    CHECK (extraction_method IN ('manual', 'ai_analysis', 'pattern_recognition', 
                                'content_parsing', 'performance_analysis', 'hybrid'));

-- Add check constraint for validation status
ALTER TABLE workspace_insights ADD CONSTRAINT IF NOT EXISTS chk_validation_status 
    CHECK (validation_status IN ('pending', 'validated', 'rejected', 'needs_review', 'applied'));

-- Create function to automatically update learning priority based on business value and confidence
CREATE OR REPLACE FUNCTION update_learning_priority()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate priority based on business value score and confidence score
    -- Higher business value + higher confidence = higher priority (lower number = higher priority)
    NEW.learning_priority = CASE
        WHEN NEW.business_value_score >= 0.8 AND NEW.confidence_score >= 0.8 THEN 1
        WHEN NEW.business_value_score >= 0.6 AND NEW.confidence_score >= 0.6 THEN 2
        WHEN NEW.business_value_score >= 0.4 AND NEW.confidence_score >= 0.4 THEN 3
        WHEN NEW.business_value_score >= 0.2 AND NEW.confidence_score >= 0.2 THEN 4
        ELSE 5
    END;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update learning priority
DROP TRIGGER IF EXISTS trigger_update_learning_priority ON workspace_insights;
CREATE TRIGGER trigger_update_learning_priority
    BEFORE INSERT OR UPDATE ON workspace_insights
    FOR EACH ROW
    EXECUTE FUNCTION update_learning_priority();

-- Add comments for documentation
COMMENT ON COLUMN workspace_insights.domain_type IS 'Business domain for domain-specific learning (instagram_marketing, email_marketing, etc.)';
COMMENT ON COLUMN workspace_insights.domain_specific_metadata IS 'JSON metadata specific to the business domain (engagement_rate, conversion_metrics, etc.)';
COMMENT ON COLUMN workspace_insights.quantifiable_metrics IS 'JSON object containing quantifiable business metrics with before/after values';
COMMENT ON COLUMN workspace_insights.action_recommendations IS 'JSON array of specific actionable recommendations for future tasks';
COMMENT ON COLUMN workspace_insights.business_value_score IS 'Score (0.0-1.0) indicating business value potential of this insight';
COMMENT ON COLUMN workspace_insights.insight_category IS 'Category of insight for better organization and retrieval';
COMMENT ON COLUMN workspace_insights.content_source_type IS 'Source of the insight content (deliverable, task result, etc.)';
COMMENT ON COLUMN workspace_insights.extraction_method IS 'Method used to extract this insight (AI analysis, manual, etc.)';
COMMENT ON COLUMN workspace_insights.quality_threshold IS 'Minimum quality score required for this insight to be applied';
COMMENT ON COLUMN workspace_insights.validation_status IS 'Validation status of the insight';
COMMENT ON COLUMN workspace_insights.learning_priority IS 'Priority level for applying this insight (1=highest, 5=lowest)';
COMMENT ON COLUMN workspace_insights.performance_impact_score IS 'Measured impact score of applying this insight';
COMMENT ON COLUMN workspace_insights.application_count IS 'Number of times this insight has been applied to tasks';
COMMENT ON COLUMN workspace_insights.last_applied_at IS 'Timestamp when this insight was last applied to a task';

-- Create view for high-value domain insights
CREATE OR REPLACE VIEW high_value_domain_insights AS
SELECT 
    wi.*,
    w.name as workspace_name,
    (wi.business_value_score * wi.confidence_score) as composite_score
FROM workspace_insights wi
LEFT JOIN workspaces w ON wi.workspace_id = w.id
WHERE wi.business_value_score >= 0.7 
  AND wi.confidence_score >= 0.7
  AND wi.validation_status IN ('validated', 'applied')
ORDER BY composite_score DESC, wi.created_at DESC;

-- Create view for domain-specific insights summary
CREATE OR REPLACE VIEW domain_insights_summary AS
SELECT 
    domain_type,
    COUNT(*) as total_insights,
    AVG(business_value_score) as avg_business_value,
    AVG(confidence_score) as avg_confidence,
    SUM(application_count) as total_applications,
    MAX(last_applied_at) as last_application_date,
    COUNT(CASE WHEN validation_status = 'validated' THEN 1 END) as validated_count,
    COUNT(CASE WHEN learning_priority <= 2 THEN 1 END) as high_priority_count
FROM workspace_insights
WHERE domain_type != 'general'
GROUP BY domain_type
ORDER BY avg_business_value DESC, total_insights DESC;

-- Sample domain-specific insight for testing
INSERT INTO workspace_insights (
    id,
    workspace_id,
    insight_type,
    content,
    domain_type,
    domain_specific_metadata,
    quantifiable_metrics,
    action_recommendations,
    business_value_score,
    confidence_score,
    insight_category,
    content_source_type,
    extraction_method,
    quality_threshold,
    validation_status,
    relevance_tags,
    agent_role,
    metadata
) VALUES (
    gen_random_uuid(),
    '1f1bf9cf-3c46-48ed-96f3-ec826742ee02', -- Social Growth workspace
    'success_pattern',
    'Instagram hashtags with mix of niche and broad tags achieve 35% higher engagement than broad-only strategies',
    'instagram_marketing',
    '{"platform": "instagram", "content_type": "hashtag_strategy", "audience_size": "mid-tier"}',
    '{"engagement_rate_before": 0.02, "engagement_rate_after": 0.027, "improvement_percentage": 35, "sample_size": 150}',
    '["Use 30% niche hashtags and 70% broad hashtags", "Test hashtag combinations for optimal reach", "Monitor engagement rates weekly"]',
    0.85,
    0.90,
    'performance_metric',
    'deliverable_content',
    'ai_analysis',
    0.70,
    'validated',
    ARRAY['instagram', 'hashtags', 'engagement', 'strategy'],
    'content_aware_learning_engine',
    '{"extraction_date": "2025-09-01", "source_deliverable_type": "hashtag_list", "analysis_method": "performance_comparison"}'
) ON CONFLICT (id) DO NOTHING;

-- Success message
SELECT 'Migration 016 completed successfully: Enhanced workspace_insights table for Content-Aware Learning System' as status;