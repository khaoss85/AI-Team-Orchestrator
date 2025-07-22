-- QUICK FIX per deliverables - Esegui questo nel SQL Editor di Supabase

-- 1. Aggiungi colonna mancante
ALTER TABLE deliverables 
ADD COLUMN IF NOT EXISTS auto_improvements JSONB DEFAULT '[]'::jsonb;

-- 2. Fix permessi RLS (più permissivo per il sistema)
DROP POLICY IF EXISTS "Enable all operations for system" ON deliverables;

CREATE POLICY "Enable all operations for system" ON deliverables
    FOR ALL 
    TO authenticated, anon, service_role
    USING (true)
    WITH CHECK (true);

-- 3. Assicurati che RLS sia abilitato
ALTER TABLE deliverables ENABLE ROW LEVEL SECURITY;

-- 4. Grant permessi
GRANT ALL ON deliverables TO authenticated;
GRANT ALL ON deliverables TO anon;
GRANT ALL ON deliverables TO service_role;

-- Test veloce
SELECT 'Deliverables table ready!' as status;