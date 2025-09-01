-- 🚨 CRITICAL SCHEMA VIOLATION DETECTED BY DB-STEWARD AGENT
-- Missing core tables: workspace_goals and deliverables
-- These tables are referenced throughout the codebase but not defined in main schema

-- =============================================================================
-- MISSING TABLE: workspace_goals
-- =============================================================================

CREATE TABLE IF NOT EXISTS workspace_goals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    metric_type VARCHAR(100) NOT NULL,
    target_value DECIMAL(15,2) NOT NULL,
    current_value DECIMAL(15,2) DEFAULT 0.00,
    priority INTEGER DEFAULT 1,
    description TEXT,
    unit VARCHAR(50) DEFAULT 'units',
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'failed', 'paused')),
    
    -- AI-Driven Enhancement Fields (inferred from codebase)
    goal_type VARCHAR(50) DEFAULT 'deliverable' CHECK (goal_type IN ('deliverable', 'metric', 'quality', 'timeline', 'quantity')),
    confidence DECIMAL(3,2) DEFAULT 0.80 CHECK (confidence >= 0.0 AND confidence <= 1.0),
    semantic_context JSONB DEFAULT '{}',
    is_percentage BOOLEAN DEFAULT false,
    is_minimum BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- MISSING TABLE: deliverables  
-- =============================================================================

CREATE TABLE IF NOT EXISTS deliverables (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    goal_id UUID REFERENCES workspace_goals(id) ON DELETE SET NULL,
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    
    -- Core deliverable fields
    title VARCHAR(500) NOT NULL,
    description TEXT,
    type VARCHAR(100) DEFAULT 'generic_deliverable',
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'in_progress', 'completed', 'failed')),
    
    -- Content fields (dual-format architecture)
    content JSONB DEFAULT '{}',
    content_format VARCHAR(20) DEFAULT 'json',
    
    -- AI-Driven Dual-Format Display Fields
    display_content TEXT,
    display_format VARCHAR(20) DEFAULT 'html',
    display_summary TEXT,
    display_metadata JSONB DEFAULT '{}',
    auto_display_generated BOOLEAN DEFAULT false,
    display_content_updated_at TIMESTAMP,
    
    -- Content transformation tracking
    content_transformation_status VARCHAR(20) DEFAULT 'pending',
    content_transformation_error TEXT,
    transformation_timestamp TIMESTAMP,
    transformation_method VARCHAR(20) DEFAULT 'ai',
    
    -- Quality metrics
    quality_score DECIMAL(5,2) DEFAULT 0.00,
    business_value_score DECIMAL(5,2) DEFAULT 0.00,
    display_quality_score DECIMAL(3,2) DEFAULT 0.00 CHECK (display_quality_score >= 0.0 AND display_quality_score <= 1.0),
    user_friendliness_score DECIMAL(3,2) DEFAULT 0.00 CHECK (user_friendliness_score >= 0.0 AND user_friendliness_score <= 1.0),
    readability_score DECIMAL(3,2) DEFAULT 0.00 CHECK (readability_score >= 0.0 AND readability_score <= 1.0),
    
    -- AI Enhancement fields (inferred from migrations)
    business_specificity_score DECIMAL(5,2) DEFAULT 0.00,
    tool_usage_score DECIMAL(5,2) DEFAULT 0.00,
    content_quality_score DECIMAL(5,2) DEFAULT 0.00,
    creation_confidence DECIMAL(5,2) DEFAULT 0.00,
    creation_reasoning TEXT,
    learning_patterns_created INTEGER DEFAULT 0,
    execution_time DECIMAL(10,3) DEFAULT 0.000,
    stages_completed INTEGER DEFAULT 0,
    auto_improvements INTEGER DEFAULT 0,
    quality_level VARCHAR(50) DEFAULT 'acceptable',
    
    -- AI confidence tracking
    ai_confidence DECIMAL(3,2) DEFAULT 0.00 CHECK (ai_confidence >= 0.0 AND ai_confidence <= 1.0),
    
    -- Additional fields inferred from codebase
    category VARCHAR(100) DEFAULT 'general',
    completeness_score DECIMAL(3,2) DEFAULT 0.00,
    authenticity_score DECIMAL(3,2) DEFAULT 0.00,
    actionability_score DECIMAL(3,2) DEFAULT 0.00,
    validation_status VARCHAR(20) DEFAULT 'pending',
    validation_passed BOOLEAN DEFAULT false,
    ai_enhanced BOOLEAN DEFAULT false,
    generation_method VARCHAR(20) DEFAULT 'manual',
    source_tools JSONB DEFAULT '[]',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- FOREIGN KEY RELATIONSHIPS & CONSTRAINTS
-- =============================================================================

-- Ensure proper cascading for workspace_goals
ALTER TABLE workspace_goals 
ADD CONSTRAINT fk_workspace_goals_workspace 
FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE;

-- Ensure proper foreign keys for deliverables  
ALTER TABLE deliverables
ADD CONSTRAINT fk_deliverables_workspace 
FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE;

ALTER TABLE deliverables
ADD CONSTRAINT fk_deliverables_goal
FOREIGN KEY (goal_id) REFERENCES workspace_goals(id) ON DELETE SET NULL;

-- Add task_id FK if tasks table exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'tasks') THEN
        ALTER TABLE deliverables
        ADD CONSTRAINT fk_deliverables_task
        FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL;
    END IF;
END $$;

-- =============================================================================
-- PERFORMANCE INDICES
-- =============================================================================

-- workspace_goals indices
CREATE INDEX IF NOT EXISTS idx_workspace_goals_workspace_id ON workspace_goals(workspace_id);
CREATE INDEX IF NOT EXISTS idx_workspace_goals_status ON workspace_goals(status);
CREATE INDEX IF NOT EXISTS idx_workspace_goals_metric_type ON workspace_goals(metric_type);
CREATE INDEX IF NOT EXISTS idx_workspace_goals_goal_type ON workspace_goals(goal_type);
CREATE INDEX IF NOT EXISTS idx_workspace_goals_confidence ON workspace_goals(confidence);
CREATE INDEX IF NOT EXISTS idx_workspace_goals_semantic_context ON workspace_goals USING GIN(semantic_context);
CREATE INDEX IF NOT EXISTS idx_workspace_goals_ai_flags ON workspace_goals(is_percentage, is_minimum);

-- deliverables indices
CREATE INDEX IF NOT EXISTS idx_deliverables_workspace_id ON deliverables(workspace_id);
CREATE INDEX IF NOT EXISTS idx_deliverables_goal_id ON deliverables(goal_id);
CREATE INDEX IF NOT EXISTS idx_deliverables_task_id ON deliverables(task_id);
CREATE INDEX IF NOT EXISTS idx_deliverables_status ON deliverables(status);
CREATE INDEX IF NOT EXISTS idx_deliverables_type ON deliverables(type);
CREATE INDEX IF NOT EXISTS idx_deliverables_display_format ON deliverables(display_format);
CREATE INDEX IF NOT EXISTS idx_deliverables_transformation_status ON deliverables(content_transformation_status);
CREATE INDEX IF NOT EXISTS idx_deliverables_display_quality ON deliverables(display_quality_score);
CREATE INDEX IF NOT EXISTS idx_deliverables_auto_generated ON deliverables(auto_display_generated);
CREATE INDEX IF NOT EXISTS idx_deliverables_workspace_status ON deliverables(workspace_id, content_transformation_status);
CREATE INDEX IF NOT EXISTS idx_deliverables_content_gin ON deliverables USING GIN(content);
CREATE INDEX IF NOT EXISTS idx_deliverables_display_metadata_gin ON deliverables USING GIN(display_metadata);

-- =============================================================================
-- UPDATE TRIGGERS
-- =============================================================================

-- Create update triggers for workspace_goals
CREATE TRIGGER update_workspace_goals_updated_at
BEFORE UPDATE ON workspace_goals
FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

-- Create update triggers for deliverables
CREATE TRIGGER update_deliverables_updated_at
BEFORE UPDATE ON deliverables
FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

-- =============================================================================
-- SCHEMA VALIDATION QUERIES
-- =============================================================================

-- Check workspace_goals table structure
SELECT 
    'workspace_goals' as table_name,
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns
WHERE table_name = 'workspace_goals' AND table_schema = 'public'
ORDER BY ordinal_position;

-- Check deliverables table structure  
SELECT 
    'deliverables' as table_name,
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns
WHERE table_name = 'deliverables' AND table_schema = 'public'
ORDER BY ordinal_position;

-- Validate foreign key relationships
SELECT 
    tc.table_name, 
    tc.constraint_name, 
    tc.constraint_type,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY' 
    AND tc.table_name IN ('workspace_goals', 'deliverables');