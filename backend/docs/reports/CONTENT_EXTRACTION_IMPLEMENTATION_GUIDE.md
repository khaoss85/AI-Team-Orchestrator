# PDF Content Extraction System - Implementation Guide

## 🎯 Overview

Il sistema di content extraction per PDF è stato preparato con tutti i componenti necessari per abilitare le funzionalità RAG (Retrieval-Augmented Generation) complete. Questo documento contiene le istruzioni finali per completare l'implementazione.

## ✅ Componenti Completati

### 1. Database Migration
- **File**: `migrations/add_document_content_extraction_fields.sql`
- **Status**: Creato e pronto per l'applicazione
- **Campi aggiunti**:
  - `extracted_text TEXT` - Contenuto estratto dal PDF
  - `text_chunks JSONB` - Chunks di testo per search semantico
  - `extraction_confidence FLOAT` - Score di confidence (0.0-1.0)
  - `extraction_method VARCHAR(50)` - Metodo di estrazione utilizzato
  - `extraction_timestamp TIMESTAMP` - Timestamp dell'estrazione

### 2. Modelli Pydantic
- **File**: `backend/models.py` (linee 1167-1377)
- **Status**: ✅ Implementato e testato
- **Modelli creati**:
  - `DocumentContentExtraction` - Modello principale per documenti con contenuto estratto
  - `DocumentContentExtractionCreate` - Modello per creazione documenti
  - `DocumentContentUpdate` - Modello per aggiornamento contenuto estratto
  - `DocumentSearchQuery` - Modello per query di ricerca
  - `DocumentSearchResult` - Modello per risultati di ricerca
  - `ContentExtractionStatus` - Modello per status del processo
  - `RAGDocumentResponse` - Modello per risposte RAG
  - **Enums**: `ExtractionMethod`, `ExtractionStatus`, `DocumentMimeType`

### 3. Indici per Performance
- **Full-text search**: Indice GIN per ricerca testuale veloce
- **Confidence filtering**: Indice per filtraggio per livello di confidence
- **Workspace filtering**: Indice composito per query per workspace

### 4. View per Query Ottimizzate
- **Nome**: `documents_with_content`
- **Scopo**: Query ottimizzata per documenti con contenuto estratto
- **Campi aggiuntivi**: `content_length`, `confidence_level`

## 🚨 Azione Richiesta: Applicazione Migration Database

### **CRITICO**: La migration deve essere applicata manualmente

Dal momento che il sistema Supabase non consente l'esecuzione di SQL arbitrario tramite API, la migration deve essere applicata attraverso il Supabase Dashboard.

#### Passi da Seguire:

1. **Accedi a Supabase Dashboard**
   - Vai a: https://app.supabase.com
   - Seleziona il progetto: `szerliaxjcverzdoisik`

2. **Naviga al SQL Editor**
   - Sidebar > SQL Editor > New Query

3. **Copia e incolla il seguente SQL**:
   ```sql
   -- Add columns for content extraction to workspace_documents table
   ALTER TABLE workspace_documents 
   ADD COLUMN IF NOT EXISTS extracted_text TEXT,
   ADD COLUMN IF NOT EXISTS text_chunks JSONB,
   ADD COLUMN IF NOT EXISTS extraction_confidence FLOAT,
   ADD COLUMN IF NOT EXISTS extraction_method VARCHAR(50),
   ADD COLUMN IF NOT EXISTS extraction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

   -- Add indexes for better search performance
   CREATE INDEX IF NOT EXISTS idx_workspace_documents_extracted_text 
   ON workspace_documents USING gin(to_tsvector('english', COALESCE(extracted_text, '')));

   CREATE INDEX IF NOT EXISTS idx_workspace_documents_extraction_confidence 
   ON workspace_documents(extraction_confidence);

   CREATE INDEX IF NOT EXISTS idx_workspace_documents_workspace_extracted 
   ON workspace_documents(workspace_id, extraction_confidence) 
   WHERE extracted_text IS NOT NULL;

   -- Add comment explaining the fields
   COMMENT ON COLUMN workspace_documents.extracted_text IS 'Extracted text content from the document (first 5000 chars for storage efficiency)';
   COMMENT ON COLUMN workspace_documents.text_chunks IS 'JSON array of text chunks for retrieval, with overlap for context preservation';
   COMMENT ON COLUMN workspace_documents.extraction_confidence IS 'Confidence score (0.0-1.0) indicating quality of extraction';
   COMMENT ON COLUMN workspace_documents.extraction_method IS 'Method used for extraction (pymupdf, pdfplumber, pypdf2, openai, fallback)';
   COMMENT ON COLUMN workspace_documents.extraction_timestamp IS 'When the content was extracted';

   -- Create a view for documents with extracted content
   CREATE OR REPLACE VIEW documents_with_content AS
   SELECT 
       wd.*,
       LENGTH(wd.extracted_text) as content_length,
       CASE 
           WHEN wd.extraction_confidence >= 0.9 THEN 'high'
           WHEN wd.extraction_confidence >= 0.7 THEN 'medium'
           WHEN wd.extraction_confidence >= 0.5 THEN 'low'
           ELSE 'very_low'
       END as confidence_level
   FROM workspace_documents wd
   WHERE wd.extracted_text IS NOT NULL;

   -- Grant permissions
   GRANT SELECT ON documents_with_content TO authenticated;
   GRANT ALL ON workspace_documents TO authenticated;
   ```

4. **Esegui la Query**
   - Clicca "Run" o Cmd+Enter
   - Verifica che non ci siano errori

5. **Verifica l'Applicazione**
   ```sql
   -- Query di verifica
   SELECT column_name, data_type, is_nullable 
   FROM information_schema.columns 
   WHERE table_name = 'workspace_documents' 
   AND column_name IN ('extracted_text', 'text_chunks', 'extraction_confidence', 'extraction_method', 'extraction_timestamp');
   ```

## 🔄 Verifica Post-Migration

Dopo aver applicato la migration, verifica che il sistema funzioni:

```python
# Test di verifica rapida
python3 -c "
from backend.models import DocumentContentExtraction
from backend.database import get_supabase_client
from uuid import uuid4

supabase = get_supabase_client()
result = supabase.table('workspace_documents').select('id, filename, extracted_text, text_chunks, extraction_confidence').limit(1).execute()
print('✅ Content extraction fields available in database!')
"
```

## 🛠 Prossimi Passi per l'Integrazione Completa

### 1. Servizio di Estrazione Contenuti
Creare `services/pdf_content_extractor.py` con:
- Integrazione PyMuPDF/pdfplumber/pypdf2
- Chunking intelligente del testo
- Confidence scoring
- Fallback tra diversi metodi

### 2. API Endpoints
Creare `routes/document_content.py` con:
- `POST /documents/{id}/extract` - Avvia estrazione contenuto
- `GET /documents/{id}/content` - Recupera contenuto estratto  
- `POST /documents/search` - Ricerca nel contenuto
- `GET /documents/{id}/chunks` - Recupera chunks per RAG

### 3. Integrazione RAG
Aggiornare il sistema RAG esistente per utilizzare:
- `text_chunks` per ricerca semantica
- `extraction_confidence` per ranking risultati
- Full-text search su `extracted_text`

### 4. Frontend Updates
Aggiornare i componenti per mostrare:
- Status di estrazione contenuto
- Preview del contenuto estratto
- Livelli di confidence
- Search attraverso i contenuti

## 📊 Schema Database Finale

Dopo la migration, la tabella `workspace_documents` avrà:

```sql
-- Campi esistenti
id, workspace_id, filename, file_size, mime_type, upload_date, 
uploaded_by, sharing_scope, vector_store_id, openai_file_id, 
description, tags, file_hash, created_at, updated_at

-- Nuovi campi content extraction
extracted_text,           -- TEXT
text_chunks,             -- JSONB  
extraction_confidence,   -- FLOAT
extraction_method,       -- VARCHAR(50)
extraction_timestamp     -- TIMESTAMP
```

## 🎉 Risultato Atteso

Una volta completata l'implementazione, il sistema supporterà:

1. **Upload PDF** → Estrazione automatica contenuto
2. **Search semantico** attraverso i chunks
3. **RAG queries** con contesto dai documenti
4. **Quality scoring** basato su confidence
5. **Multi-method extraction** con fallback automatico

## 🔧 File Modificati in questa Implementazione

- ✅ `backend/models.py` - Aggiunto modelli content extraction (linee 1167-1377)
- ✅ `migrations/add_document_content_extraction_fields.sql` - Migration database
- ✅ `CONTENT_EXTRACTION_IMPLEMENTATION_GUIDE.md` - Questa guida

## ⚠️ Note Importanti

1. **Sicurezza**: I campi sono protetti da RLS (Row Level Security) di Supabase
2. **Performance**: Gli indici garantiscono query veloci anche con grandi volumi
3. **Scalabilità**: Il design supporta diversi tipi di documento (non solo PDF)
4. **Backward Compatibility**: Tutti i documenti esistenti continuano a funzionare
5. **Privacy**: Il contenuto estratto rispetta lo `sharing_scope` del documento originale

---
**Status**: ✅ Ready for Database Migration  
**Next Action**: Apply SQL migration in Supabase Dashboard  
**Timeline**: ~15 minutes for manual migration application