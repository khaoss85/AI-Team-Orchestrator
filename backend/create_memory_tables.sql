-- Memory System Tables - Pillar 6: Memory System
-- Tables for context retention, learning patterns, and memory-driven insights

-- Memory Context Table
CREATE TABLE IF NOT EXISTS memory_context (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL,
    context TEXT NOT NULL,
    context_type VARCHAR(50) DEFAULT 'general',
    importance VARCHAR(20) DEFAULT 'medium',
    importance_score DECIMAL(3,2) DEFAULT 0.5,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    embedding_vector VECTOR(1536), -- For semantic search
    
    CONSTRAINT memory_context_importance_check CHECK (importance IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT memory_context_importance_score_check CHECK (importance_score >= 0.0 AND importance_score <= 1.0)
);

-- Learning Patterns Table
CREATE TABLE IF NOT EXISTS learning_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL,
    pattern_type VARCHAR(50) NOT NULL,
    pattern_name VARCHAR(200) NOT NULL,
    pattern_description TEXT,
    pattern_strength DECIMAL(3,2) DEFAULT 0.5,
    pattern_data JSONB DEFAULT '{}',
    confidence_score DECIMAL(3,2) DEFAULT 0.5,
    usage_count INTEGER DEFAULT 1,
    last_reinforced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT learning_patterns_strength_check CHECK (pattern_strength >= 0.0 AND pattern_strength <= 1.0),
    CONSTRAINT learning_patterns_confidence_check CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_memory_context_workspace_id ON memory_context(workspace_id);
CREATE INDEX IF NOT EXISTS idx_memory_context_importance_score ON memory_context(importance_score DESC);
CREATE INDEX IF NOT EXISTS idx_memory_context_created_at ON memory_context(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memory_context_type ON memory_context(context_type);

CREATE INDEX IF NOT EXISTS idx_learning_patterns_workspace_id ON learning_patterns(workspace_id);
CREATE INDEX IF NOT EXISTS idx_learning_patterns_strength ON learning_patterns(pattern_strength DESC);
CREATE INDEX IF NOT EXISTS idx_learning_patterns_type ON learning_patterns(pattern_type);

-- Row Level Security (if needed)
ALTER TABLE memory_context ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_patterns ENABLE ROW LEVEL SECURITY;

-- RLS Policies (basic - allow all for now)
-- Drop existing policies if they exist, then create new ones
DROP POLICY IF EXISTS "Allow all operations on memory_context" ON memory_context;
DROP POLICY IF EXISTS "Allow all operations on learning_patterns" ON learning_patterns;

CREATE POLICY "Allow all operations on memory_context" ON memory_context FOR ALL USING (true);
CREATE POLICY "Allow all operations on learning_patterns" ON learning_patterns FOR ALL USING (true);

-- Comments
COMMENT ON TABLE memory_context IS 'Stores contextual memory for workspaces - Pillar 6: Memory System';
COMMENT ON TABLE learning_patterns IS 'Stores learning patterns and insights - Pillar 6: Memory System';