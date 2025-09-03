-- =============================================================================
-- 🔧 COMANDI SQL MANUALI PER SUPABASE DASHBOARD
-- =============================================================================
-- Eseguire questi comandi nel SQL Editor del dashboard Supabase
-- per completare l'implementazione del User Insights Management System
-- Data: 2025-09-03
-- =============================================================================

-- STEP 1: Aggiungi colonne mancanti dalla Migration 017 (User Insights Management)
-- =========================================================================
ALTER TABLE workspace_insights 
ADD COLUMN IF NOT EXISTS created_by VARCHAR(255) DEFAULT 'ai_system';

ALTER TABLE workspace_insights 
ADD COLUMN IF NOT EXISTS last_modified_by VARCHAR(255);

ALTER TABLE workspace_insights 
ADD COLUMN IF NOT EXISTS is_user_created BOOLEAN DEFAULT FALSE;

ALTER TABLE workspace_insights 
ADD COLUMN IF NOT EXISTS is_user_modified BOOLEAN DEFAULT FALSE;

ALTER TABLE workspace_insights 
ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE;

ALTER TABLE workspace_insights 
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;

ALTER TABLE workspace_insights 
ADD COLUMN IF NOT EXISTS deleted_by VARCHAR(255);

ALTER TABLE workspace_insights 
ADD COLUMN IF NOT EXISTS version_number INTEGER DEFAULT 1;

ALTER TABLE workspace_insights 
ADD COLUMN IF NOT EXISTS parent_insight_id UUID REFERENCES workspace_insights(id);

ALTER TABLE workspace_insights 
ADD COLUMN IF NOT EXISTS user_flags JSONB DEFAULT '{}';

ALTER TABLE workspace_insights 
ADD COLUMN IF NOT EXISTS title VARCHAR(500);

ALTER TABLE workspace_insights 
ADD COLUMN IF NOT EXISTS original_content TEXT;

ALTER TABLE workspace_insights 
ADD COLUMN IF NOT EXISTS original_metadata JSONB;

-- STEP 2: Aggiungi colonne mancanti dalla Migration 021 (Additional Columns)
-- =========================================================================
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

-- STEP 3: Crea tabelle di supporto per il sistema
-- ===============================================

-- Tabella audit trail per tracking modifiche
CREATE TABLE IF NOT EXISTS insight_audit_trail (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    insight_id UUID REFERENCES workspace_insights(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,
    performed_by VARCHAR(255) NOT NULL,
    performed_at TIMESTAMP DEFAULT NOW(),
    old_values JSONB,
    new_values JSONB,
    change_description TEXT,
    workspace_id UUID REFERENCES workspaces(id),
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    CONSTRAINT chk_action CHECK (action IN (
        'CREATE', 'UPDATE', 'DELETE', 'RESTORE', 
        'FLAG', 'UNFLAG', 'CATEGORIZE', 'VERIFY',
        'BULK_UPDATE', 'BULK_DELETE', 'IMPORT', 'EXPORT'
    ))
);

-- Tabelle categorie utente personalizzate
CREATE TABLE IF NOT EXISTS user_insight_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    category_name VARCHAR(100) NOT NULL,
    category_description TEXT,
    color_hex VARCHAR(7) DEFAULT '#6B7280',
    icon_name VARCHAR(50) DEFAULT 'folder',
    parent_category_id UUID REFERENCES user_insight_categories(id),
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    
    CONSTRAINT uq_workspace_category UNIQUE(workspace_id, category_name)
);

-- Tabella operazioni bulk
CREATE TABLE IF NOT EXISTS insight_bulk_operations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id),
    operation_type VARCHAR(50) NOT NULL,
    affected_insights JSONB NOT NULL,
    performed_by VARCHAR(255) NOT NULL,
    performed_at TIMESTAMP DEFAULT NOW(),
    operation_status VARCHAR(20) DEFAULT 'pending',
    operation_result JSONB,
    error_message TEXT,
    
    CONSTRAINT chk_operation_type CHECK (operation_type IN (
        'BULK_DELETE', 'BULK_CATEGORIZE', 'BULK_FLAG', 
        'BULK_VERIFY', 'BULK_EXPORT', 'BULK_RESTORE'
    )),
    CONSTRAINT chk_operation_status CHECK (operation_status IN (
        'pending', 'in_progress', 'completed', 'failed', 'cancelled'
    ))
);

-- STEP 4: Crea indici per performance
-- ===================================
CREATE INDEX IF NOT EXISTS idx_insights_created_by ON workspace_insights(created_by);
CREATE INDEX IF NOT EXISTS idx_insights_modified_by ON workspace_insights(last_modified_by);
CREATE INDEX IF NOT EXISTS idx_insights_user_created ON workspace_insights(is_user_created) WHERE is_user_created = TRUE;
CREATE INDEX IF NOT EXISTS idx_insights_user_modified ON workspace_insights(is_user_modified) WHERE is_user_modified = TRUE;
CREATE INDEX IF NOT EXISTS idx_insights_deleted ON workspace_insights(is_deleted) WHERE is_deleted = TRUE;
CREATE INDEX IF NOT EXISTS idx_insights_parent ON workspace_insights(parent_insight_id);
CREATE INDEX IF NOT EXISTS idx_insights_source_filter ON workspace_insights(workspace_id, is_user_created, is_deleted, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_insights_user_flags ON workspace_insights USING gin(user_flags);
CREATE INDEX IF NOT EXISTS idx_insights_title ON workspace_insights(title);

-- Indici per audit trail
CREATE INDEX IF NOT EXISTS idx_audit_trail_insight_id ON insight_audit_trail(insight_id);
CREATE INDEX IF NOT EXISTS idx_audit_trail_workspace_id ON insight_audit_trail(workspace_id);
CREATE INDEX IF NOT EXISTS idx_audit_trail_performed_by ON insight_audit_trail(performed_by);
CREATE INDEX IF NOT EXISTS idx_audit_trail_performed_at ON insight_audit_trail(performed_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_trail_action ON insight_audit_trail(action);

-- Indici per categorie utente
CREATE INDEX IF NOT EXISTS idx_user_categories_workspace ON user_insight_categories(workspace_id);
CREATE INDEX IF NOT EXISTS idx_user_categories_parent ON user_insight_categories(parent_category_id);

-- Indici per operazioni bulk
CREATE INDEX IF NOT EXISTS idx_bulk_operations_workspace ON insight_bulk_operations(workspace_id);
CREATE INDEX IF NOT EXISTS idx_bulk_operations_status ON insight_bulk_operations(operation_status);

-- STEP 5: Aggiungi commenti per documentazione
-- =============================================
COMMENT ON COLUMN workspace_insights.created_by IS 'User ID or system identifier that created the insight';
COMMENT ON COLUMN workspace_insights.last_modified_by IS 'User ID of the last person to modify the insight';
COMMENT ON COLUMN workspace_insights.is_user_created IS 'TRUE if insight was manually created by a user';
COMMENT ON COLUMN workspace_insights.is_user_modified IS 'TRUE if insight has been modified by a user';
COMMENT ON COLUMN workspace_insights.is_deleted IS 'Soft delete flag - TRUE means logically deleted';
COMMENT ON COLUMN workspace_insights.user_flags IS 'JSON object containing user-defined flags like verified, important, etc';
COMMENT ON COLUMN workspace_insights.title IS 'User-friendly title for the insight';
COMMENT ON COLUMN workspace_insights.version_number IS 'Version number incremented on each modification';
COMMENT ON COLUMN workspace_insights.parent_insight_id IS 'Reference to parent insight for versioning';
COMMENT ON COLUMN workspace_insights.business_value_score IS 'Business value score from 0.0 to 1.0 indicating the importance of this insight';
COMMENT ON COLUMN workspace_insights.quantifiable_metrics IS 'JSON object containing quantifiable metrics associated with the insight';
COMMENT ON COLUMN workspace_insights.insight_category IS 'Category classification for the insight (e.g., knowledge, learning, best_practice)';
COMMENT ON COLUMN workspace_insights.domain_type IS 'Business domain type (e.g., technical, business, operational)';
COMMENT ON COLUMN workspace_insights.action_recommendations IS 'Array of actionable recommendations derived from the insight';

COMMENT ON TABLE insight_audit_trail IS 'Complete audit trail of all changes to insights';
COMMENT ON TABLE user_insight_categories IS 'User-defined categories for organizing insights';
COMMENT ON TABLE insight_bulk_operations IS 'Tracking table for bulk operations on insights';

-- STEP 6: Imposta permessi
-- ========================
GRANT SELECT, INSERT, UPDATE ON workspace_insights TO authenticated;
GRANT SELECT, INSERT, UPDATE ON insight_audit_trail TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON user_insight_categories TO authenticated;
GRANT SELECT, INSERT, UPDATE ON insight_bulk_operations TO authenticated;

-- STEP 7: Inserisci dati di esempio per testing
-- ==============================================
INSERT INTO workspace_insights (
    id,
    workspace_id,
    insight_type,
    title,
    content,
    domain_type,
    business_value_score,
    confidence_score,
    insight_category,
    created_by,
    is_user_created,
    user_flags,
    relevance_tags,
    agent_role,
    metadata
) VALUES (
    gen_random_uuid(),
    'f35639dc-12ae-4720-882d-3e35a70a79b8', -- Replace with actual workspace ID
    'best_practice',
    'Sistema User Insights Management Operativo',
    'Il sistema di gestione insight utente è ora completamente operativo con tutte le funzionalità di CRUD, audit trail e categorizzazione AI.',
    'technical',
    0.9,
    0.95,
    'system',
    'system_admin',
    TRUE,
    '{"verified": true, "important": true, "system_generated": false}'::jsonb,
    ARRAY['backend', 'frontend', 'database', 'user_management'],
    'system_architect',
    '{"implementation_date": "2025-09-03", "features": ["crud_operations", "audit_trail", "ai_categorization", "bulk_operations"]}'::jsonb
) ON CONFLICT (id) DO NOTHING;

-- =============================================================================
-- VERIFICA COMPLETAMENTO
-- =============================================================================

-- Query di verifica per controllare che tutto sia stato creato correttamente
DO $$
DECLARE
    missing_columns TEXT := '';
    col_exists BOOLEAN;
    table_count INTEGER;
BEGIN
    -- Verifica esistenza colonne workspace_insights
    SELECT COUNT(*) INTO table_count FROM information_schema.columns WHERE table_name = 'workspace_insights';
    RAISE NOTICE 'workspace_insights has % columns', table_count;
    
    -- Verifica tabelle di supporto
    SELECT COUNT(*) INTO table_count FROM information_schema.tables WHERE table_name = 'insight_audit_trail';
    IF table_count = 0 THEN
        RAISE NOTICE '❌ Missing table: insight_audit_trail';
    ELSE
        RAISE NOTICE '✅ Table exists: insight_audit_trail';
    END IF;
    
    SELECT COUNT(*) INTO table_count FROM information_schema.tables WHERE table_name = 'user_insight_categories';
    IF table_count = 0 THEN
        RAISE NOTICE '❌ Missing table: user_insight_categories';
    ELSE
        RAISE NOTICE '✅ Table exists: user_insight_categories';
    END IF;
    
    SELECT COUNT(*) INTO table_count FROM information_schema.tables WHERE table_name = 'insight_bulk_operations';
    IF table_count = 0 THEN
        RAISE NOTICE '❌ Missing table: insight_bulk_operations';
    ELSE
        RAISE NOTICE '✅ Table exists: insight_bulk_operations';
    END IF;
    
    -- Conteggio insights di esempio
    SELECT COUNT(*) INTO table_count FROM workspace_insights WHERE is_user_created = TRUE;
    RAISE NOTICE '✅ User-created insights: %', table_count;
    
    RAISE NOTICE '🚀 User Insights Management System - Database Schema Setup Complete!';
END $$;

-- =============================================================================
-- ISTRUZIONI PER L'ESECUZIONE
-- =============================================================================
/*
COME ESEGUIRE QUESTI COMANDI IN SUPABASE:

1. Vai al dashboard Supabase del tuo progetto
2. Clicca su "SQL Editor" nel menu laterale
3. Crea una nuova query
4. Copia e incolla questi comandi SQL
5. Clicca "RUN" per eseguire
6. Verifica che tutti i messaggi di conferma vengano visualizzati
7. Se ci sono errori, esegui i comandi singolarmente per identificare i problemi

NOTA: Alcuni comandi potrebbero già essere stati eseguiti se le tabelle esistono.
      I comandi usano "IF NOT EXISTS" e "ON CONFLICT" per evitare errori.

Dopo l'esecuzione, il User Insights Management System sarà completamente operativo!
*/