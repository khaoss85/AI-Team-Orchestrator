-- Real-Time Thinking System Tables - Pillar 10: Real-Time Thinking
-- Tables for capturing and storing AI reasoning processes

-- Thinking Processes Table
CREATE TABLE IF NOT EXISTS thinking_processes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    process_id VARCHAR(100) UNIQUE NOT NULL,
    workspace_id UUID NOT NULL,
    context TEXT NOT NULL,
    process_type VARCHAR(50) DEFAULT 'general',
    final_conclusion TEXT,
    overall_confidence DECIMAL(3,2) DEFAULT 0.5,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT thinking_processes_confidence_check CHECK (overall_confidence >= 0.0 AND overall_confidence <= 1.0)
);

-- Thinking Steps Table
CREATE TABLE IF NOT EXISTS thinking_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    step_id VARCHAR(100) UNIQUE NOT NULL,
    process_id VARCHAR(100) NOT NULL REFERENCES thinking_processes(process_id) ON DELETE CASCADE,
    step_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    confidence DECIMAL(3,2) DEFAULT 0.5,
    step_order INTEGER DEFAULT 1,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT thinking_steps_confidence_check CHECK (confidence >= 0.0 AND confidence <= 1.0),
    CONSTRAINT thinking_steps_type_check CHECK (step_type IN ('analysis', 'reasoning', 'evaluation', 'conclusion', 'context_loading', 'perspective', 'critical_review', 'synthesis'))
);

-- Real-Time Thinking Events (for WebSocket broadcasting)
CREATE TABLE IF NOT EXISTS thinking_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL,
    process_id VARCHAR(100),
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT thinking_events_type_check CHECK (event_type IN ('process_started', 'step_added', 'process_completed', 'thinking_updated'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_thinking_processes_workspace_id ON thinking_processes(workspace_id);
CREATE INDEX IF NOT EXISTS idx_thinking_processes_started_at ON thinking_processes(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_thinking_processes_process_type ON thinking_processes(process_type);

CREATE INDEX IF NOT EXISTS idx_thinking_steps_process_id ON thinking_steps(process_id);
CREATE INDEX IF NOT EXISTS idx_thinking_steps_step_order ON thinking_steps(step_order);
CREATE INDEX IF NOT EXISTS idx_thinking_steps_timestamp ON thinking_steps(timestamp);

CREATE INDEX IF NOT EXISTS idx_thinking_events_workspace_id ON thinking_events(workspace_id);
CREATE INDEX IF NOT EXISTS idx_thinking_events_process_id ON thinking_events(process_id);
CREATE INDEX IF NOT EXISTS idx_thinking_events_created_at ON thinking_events(created_at DESC);

-- Row Level Security (if needed)
ALTER TABLE thinking_processes ENABLE ROW LEVEL SECURITY;
ALTER TABLE thinking_steps ENABLE ROW LEVEL SECURITY;
ALTER TABLE thinking_events ENABLE ROW LEVEL SECURITY;

-- RLS Policies (basic - allow all for now)
-- Drop existing policies if they exist, then create new ones
DROP POLICY IF EXISTS "Allow all operations on thinking_processes" ON thinking_processes;
DROP POLICY IF EXISTS "Allow all operations on thinking_steps" ON thinking_steps;
DROP POLICY IF EXISTS "Allow all operations on thinking_events" ON thinking_events;

CREATE POLICY "Allow all operations on thinking_processes" ON thinking_processes FOR ALL USING (true);
CREATE POLICY "Allow all operations on thinking_steps" ON thinking_steps FOR ALL USING (true);
CREATE POLICY "Allow all operations on thinking_events" ON thinking_events FOR ALL USING (true);

-- Comments
COMMENT ON TABLE thinking_processes IS 'Stores AI thinking processes - Pillar 10: Real-Time Thinking';
COMMENT ON TABLE thinking_steps IS 'Individual steps in thinking processes - Pillar 10: Real-Time Thinking';
COMMENT ON TABLE thinking_events IS 'Real-time events for WebSocket broadcasting - Pillar 10: Real-Time Thinking';