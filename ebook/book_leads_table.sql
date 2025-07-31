-- SQL per creare tabella book_leads in Supabase
-- Esegui questo nel SQL Editor di Supabase

CREATE TABLE book_leads (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50),
    challenge TEXT,
    gdpr_consent BOOLEAN NOT NULL DEFAULT false,
    marketing_consent BOOLEAN NOT NULL DEFAULT false,
    book_chapter VARCHAR(50) NOT NULL DEFAULT 'chapter-2',
    user_agent TEXT,
    ip_address INET,
    referrer_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indici per performance
CREATE INDEX idx_book_leads_email ON book_leads(email);
CREATE INDEX idx_book_leads_created_at ON book_leads(created_at);
CREATE INDEX idx_book_leads_role ON book_leads(role);

-- RLS (Row Level Security) - se vuoi abilitarla
ALTER TABLE book_leads ENABLE ROW LEVEL SECURITY;

-- Policy per permettere inserimenti (se usi RLS)
CREATE POLICY "Allow public inserts" ON book_leads
    FOR INSERT 
    TO public 
    WITH CHECK (true);

-- Policy per permettere letture solo agli admin autenticati (se usi RLS)
CREATE POLICY "Allow authenticated reads" ON book_leads
    FOR SELECT 
    TO authenticated 
    USING (true);

-- Trigger per aggiornare updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_book_leads_updated_at 
    BEFORE UPDATE ON book_leads 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Commenti per documentazione
COMMENT ON TABLE book_leads IS 'Lead generation data from AI Team Orchestrator ebook';
COMMENT ON COLUMN book_leads.name IS 'Nome completo del lead';
COMMENT ON COLUMN book_leads.email IS 'Email del lead (campo chiave per follow-up)';
COMMENT ON COLUMN book_leads.role IS 'Ruolo professionale: ceo, cto, developer, manager, consultant, student, other';
COMMENT ON COLUMN book_leads.challenge IS 'Sfida principale con AI descritta dal lead';
COMMENT ON COLUMN book_leads.gdpr_consent IS 'Consenso GDPR obbligatorio';
COMMENT ON COLUMN book_leads.marketing_consent IS 'Consenso opzionale per newsletter';
COMMENT ON COLUMN book_leads.book_chapter IS 'Capitolo dove è apparso il popup';
COMMENT ON COLUMN book_leads.user_agent IS 'Browser info per analytics';
COMMENT ON COLUMN book_leads.ip_address IS 'IP per geo-analytics (opzionale)';
COMMENT ON COLUMN book_leads.referrer_url IS 'URL di provenienza (opzionale)';