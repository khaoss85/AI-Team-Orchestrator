-- Create deliverables table for final project deliverables
CREATE TABLE IF NOT EXISTS deliverables (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL DEFAULT 'final_report',
    title TEXT NOT NULL,
    content JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
    readiness_score INTEGER DEFAULT 0 CHECK (readiness_score >= 0 AND readiness_score <= 100),
    completion_percentage INTEGER DEFAULT 0 CHECK (completion_percentage >= 0 AND completion_percentage <= 100),
    business_value_score INTEGER DEFAULT 0 CHECK (business_value_score >= 0 AND business_value_score <= 100),
    quality_metrics JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_deliverables_workspace_id ON deliverables(workspace_id);
CREATE INDEX IF NOT EXISTS idx_deliverables_status ON deliverables(status);
CREATE INDEX IF NOT EXISTS idx_deliverables_type ON deliverables(type);
CREATE INDEX IF NOT EXISTS idx_deliverables_created_at ON deliverables(created_at);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_deliverables_updated_at 
    BEFORE UPDATE ON deliverables 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add some comments for documentation
COMMENT ON TABLE deliverables IS 'Final project deliverables and outputs';
COMMENT ON COLUMN deliverables.type IS 'Type of deliverable: final_report, contact_database, email_sequences, etc.';
COMMENT ON COLUMN deliverables.content IS 'Main deliverable content in JSON format';
COMMENT ON COLUMN deliverables.readiness_score IS 'How ready the deliverable is for business use (0-100)';
COMMENT ON COLUMN deliverables.completion_percentage IS 'Percentage of deliverable completion (0-100)';
COMMENT ON COLUMN deliverables.business_value_score IS 'Assessed business value of the deliverable (0-100)';
COMMENT ON COLUMN deliverables.quality_metrics IS 'Quality assessment metrics and scores';
COMMENT ON COLUMN deliverables.metadata IS 'Additional metadata and configuration';