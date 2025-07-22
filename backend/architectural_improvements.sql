-- ARCHITECTURAL IMPROVEMENTS SQL
-- Based on AI analysis for eliminating workarounds and improving performance

-- =============================================================================
-- 1. SOSTITUIRE L'ARRAY DI DIPENDENZE CON UNA JUNCTION TABLE
-- =============================================================================

-- Step 1: Creare la tabella di giunzione per le dipendenze
CREATE TABLE IF NOT EXISTS task_dependencies (
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    depends_on_task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (task_id, depends_on_task_id)
);

-- Step 2: Indici per performance
CREATE INDEX IF NOT EXISTS idx_task_dependencies_task_id ON task_dependencies(task_id);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_depends_on_task_id ON task_dependencies(depends_on_task_id);

-- Step 3: Migrazione dei dati esistenti (da eseguire dopo test)
-- NOTA: Decommentare dopo aver verificato che la nuova struttura funziona
-- INSERT INTO task_dependencies (task_id, depends_on_task_id)
-- SELECT id, unnest(depends_on_task_ids)
-- FROM tasks
-- WHERE depends_on_task_ids IS NOT NULL AND array_length(depends_on_task_ids, 1) > 0;

-- Step 4: Deprecare la vecchia colonna (da eseguire dopo migrazione)
-- ALTER TABLE tasks RENAME COLUMN depends_on_task_ids TO _deprecated_depends_on_task_ids;

-- =============================================================================
-- 2. CREARE LA TABELLA TASK_EXECUTIONS PER TRACCIABILITÀ
-- =============================================================================

-- Questa tabella è fondamentale per i Pilastri 10 e 15 (Robustezza e Osservabilità)
CREATE TABLE IF NOT EXISTS task_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('started', 'completed', 'failed_retriable', 'failed_terminal')),
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    execution_time_seconds FLOAT,
    result JSONB,
    logs TEXT,
    token_usage JSONB, -- Es: {"prompt_tokens": 120, "completion_tokens": 350, "total_tokens": 470}
    error_message TEXT,
    error_type TEXT,
    retry_count INTEGER DEFAULT 0,
    openai_trace_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indici per performance
CREATE INDEX IF NOT EXISTS idx_task_executions_task_id ON task_executions(task_id);
CREATE INDEX IF NOT EXISTS idx_task_executions_agent_id ON task_executions(agent_id);
CREATE INDEX IF NOT EXISTS idx_task_executions_workspace_id ON task_executions(workspace_id);
CREATE INDEX IF NOT EXISTS idx_task_executions_status ON task_executions(status);
CREATE INDEX IF NOT EXISTS idx_task_executions_started_at ON task_executions(started_at);

-- =============================================================================
-- 3. FUNZIONI PER QUERY OTTIMIZZATE
-- =============================================================================

-- Funzione per ottenere i task pronti per l'esecuzione
-- Sostituisce la logica Python con una query SQL efficiente
CREATE OR REPLACE FUNCTION get_ready_tasks(p_workspace_id UUID)
RETURNS TABLE (
    task_id UUID,
    task_name TEXT,
    task_description TEXT,
    task_priority TEXT,
    agent_id UUID,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.id,
        t.name,
        t.description,
        t.priority,
        t.agent_id,
        t.created_at
    FROM tasks t
    WHERE t.workspace_id = p_workspace_id
    AND t.status = 'pending'
    AND NOT EXISTS (
        -- Verifica che non ci siano dipendenze non completate
        SELECT 1 
        FROM task_dependencies td
        JOIN tasks dt ON td.depends_on_task_id = dt.id
        WHERE td.task_id = t.id
        AND dt.status != 'completed'
    )
    ORDER BY t.priority DESC, t.created_at ASC;
END;
$$ LANGUAGE plpgsql;

-- Funzione per ottenere statistiche di esecuzione
CREATE OR REPLACE FUNCTION get_task_execution_stats(p_task_id UUID)
RETURNS TABLE (
    total_attempts INTEGER,
    successful_attempts INTEGER,
    failed_attempts INTEGER,
    average_execution_time FLOAT,
    last_execution_status TEXT,
    last_execution_time TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER as total_attempts,
        COUNT(CASE WHEN status = 'completed' THEN 1 END)::INTEGER as successful_attempts,
        COUNT(CASE WHEN status LIKE 'failed%' THEN 1 END)::INTEGER as failed_attempts,
        AVG(execution_time_seconds) as average_execution_time,
        (SELECT status FROM task_executions WHERE task_id = p_task_id ORDER BY started_at DESC LIMIT 1) as last_execution_status,
        (SELECT started_at FROM task_executions WHERE task_id = p_task_id ORDER BY started_at DESC LIMIT 1) as last_execution_time
    FROM task_executions
    WHERE task_id = p_task_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 4. TRIGGERS PER MANTENERE CONSISTENZA
-- =============================================================================

-- Trigger per aggiornare automatically updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Applicare il trigger a task_executions
CREATE TRIGGER update_task_executions_updated_at
    BEFORE UPDATE ON task_executions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- 5. VIEW PER QUERY COMUNI
-- =============================================================================

-- View per task con dipendenze risolte
CREATE OR REPLACE VIEW tasks_with_dependencies AS
SELECT 
    t.*,
    COALESCE(
        array_agg(td.depends_on_task_id) FILTER (WHERE td.depends_on_task_id IS NOT NULL),
        ARRAY[]::UUID[]
    ) as dependency_task_ids,
    COUNT(td.depends_on_task_id) as dependency_count
FROM tasks t
LEFT JOIN task_dependencies td ON t.id = td.task_id
GROUP BY t.id, t.workspace_id, t.name, t.description, t.status, t.priority, t.agent_id, t.created_at, t.updated_at;

-- View per statistiche di esecuzione per workspace
CREATE OR REPLACE VIEW workspace_execution_stats AS
SELECT 
    w.id as workspace_id,
    w.name as workspace_name,
    COUNT(DISTINCT t.id) as total_tasks,
    COUNT(DISTINCT CASE WHEN t.status = 'completed' THEN t.id END) as completed_tasks,
    COUNT(DISTINCT CASE WHEN t.status = 'pending' THEN t.id END) as pending_tasks,
    COUNT(DISTINCT CASE WHEN t.status = 'failed' THEN t.id END) as failed_tasks,
    COUNT(te.id) as total_executions,
    COUNT(CASE WHEN te.status = 'completed' THEN 1 END) as successful_executions,
    COUNT(CASE WHEN te.status LIKE 'failed%' THEN 1 END) as failed_executions,
    AVG(te.execution_time_seconds) as avg_execution_time,
    SUM(COALESCE((te.token_usage->>'total_tokens')::INTEGER, 0)) as total_tokens_used
FROM workspaces w
LEFT JOIN tasks t ON w.id = t.workspace_id
LEFT JOIN task_executions te ON t.id = te.task_id
GROUP BY w.id, w.name;

-- =============================================================================
-- 6. PERMISSIONS E SECURITY
-- =============================================================================

-- Assegnare permissions appropriate
GRANT SELECT, INSERT, UPDATE, DELETE ON task_dependencies TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON task_executions TO authenticated;
GRANT SELECT ON tasks_with_dependencies TO authenticated;
GRANT SELECT ON workspace_execution_stats TO authenticated;
GRANT EXECUTE ON FUNCTION get_ready_tasks(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION get_task_execution_stats(UUID) TO authenticated;

-- Service role permissions
GRANT ALL ON task_dependencies TO service_role;
GRANT ALL ON task_executions TO service_role;
GRANT ALL ON tasks_with_dependencies TO service_role;
GRANT ALL ON workspace_execution_stats TO service_role;
GRANT ALL ON FUNCTION get_ready_tasks(UUID) TO service_role;
GRANT ALL ON FUNCTION get_task_execution_stats(UUID) TO service_role;

-- =============================================================================
-- 7. COMMENTI E DOCUMENTAZIONE
-- =============================================================================

COMMENT ON TABLE task_dependencies IS 'Junction table for task dependencies. Replaces the inefficient depends_on_task_ids array.';
COMMENT ON TABLE task_executions IS 'Tracks all task execution attempts for robustness and observability.';
COMMENT ON FUNCTION get_ready_tasks(UUID) IS 'Returns tasks ready for execution (no incomplete dependencies).';
COMMENT ON FUNCTION get_task_execution_stats(UUID) IS 'Returns execution statistics for a specific task.';
COMMENT ON VIEW tasks_with_dependencies IS 'Tasks with resolved dependency arrays for backward compatibility.';
COMMENT ON VIEW workspace_execution_stats IS 'Aggregated execution statistics per workspace.';