# 📚 Book Leads System - Setup Guide

## 🎯 **Sistema Implementato**

Abbiamo creato un sistema completo di lead generation per l'ebook che include:

### **✅ Frontend (Ebook)**
- **Popup intelligente** che appare dopo aver letto il Capitolo 2
- **Form GDPR-compliant** con copy simpatico e onesto
- **Prevenzione duplicati** con sessionStorage + localStorage  
- **Backup locale** in caso di problemi API

### **✅ Backend (FastAPI)**
- **API endpoint** `/api/book-leads` per salvare leads
- **Validazione Pydantic** completa con email validation
- **Integrazione Supabase** nativa con la codebase esistente
- **IP tracking** e analytics metadata
- **Endpoint analytics** `/api/book-leads` per visualizzare dati

### **✅ Database (Supabase)**
- **Tabella `book_leads`** con tutti i campi necessari
- **Indici ottimizzati** per performance
- **RLS (Row Level Security)** configurabile
- **Trigger automatici** per updated_at

---

## 🚀 **Setup Instructions**

### **1. Database Setup**
```bash
# 1. Vai su Supabase Dashboard
# 2. Apri SQL Editor
# 3. Esegui il contenuto di: book_leads_table.sql
```

### **2. Backend Setup**
Il backend è già configurato! I nuovi file sono:
- ✅ `models.py` - Aggiornato con BookLead models
- ✅ `main.py` - Aggiornato con API endpoints

### **3. Frontend Setup**  
Il frontend è già configurato! Il popup è attivo nel libro:
- ✅ `AI_Team_Orchestrator_Libro_FINALE.html` - Popup completo

### **4. Test del Sistema**
```bash
# 1. Avvia il backend
cd backend && python main.py

# 2. Apri il libro
cd ebook/web && open AI_Team_Orchestrator_Libro_FINALE.html

# 3. Scorri fino al Capitolo 2 e aspetta 2 secondi
# 4. Il popup dovrebbe apparire automaticamente
```

---

## 📊 **API Endpoints**

### **POST /api/book-leads**
Crea un nuovo lead dall'ebook popup.

**Request Body:**
```json
{
  "name": "Mario Rossi",
  "email": "mario@example.com", 
  "role": "ceo",
  "challenge": "Implementazione AI nel team",
  "gdpr_consent": true,
  "marketing_consent": false,
  "book_chapter": "chapter-2",
  "user_agent": "Mozilla/5.0...",
  "referrer_url": "https://example.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Lead salvato con successo! Grazie per il tuo interesse.",
  "lead_id": "uuid-here"
}
```

### **GET /api/book-leads**
Ottiene la lista dei leads per analytics.

**Query Parameters:**
- `skip`: Offset per paginazione (default: 0)
- `limit`: Numero di leads da restituire (default: 100)

**Response:**
```json
{
  "success": true,
  "leads": [
    {
      "id": "uuid",
      "name": "Mario Rossi",
      "email": "mario@example.com",
      "role": "ceo",
      "challenge": "Implementazione AI",
      "gdpr_consent": true,
      "marketing_consent": false,
      "book_chapter": "chapter-2",
      "ip_address": "192.168.1.1", 
      "created_at": "2025-01-30T10:00:00Z"
    }
  ],
  "count": 1
}
```

---

## 🔧 **Schema Database**

```sql
-- Campi principali
id              UUID PRIMARY KEY
name            VARCHAR(255) NOT NULL  
email           VARCHAR(255) NOT NULL
role            VARCHAR(50)             -- ceo, cto, developer, etc.
challenge       TEXT                    -- Sfida AI descritta
gdpr_consent    BOOLEAN NOT NULL        -- Obbligatorio
marketing_consent BOOLEAN DEFAULT false -- Opzionale
book_chapter    VARCHAR(50)             -- Tracking posizione
user_agent      TEXT                    -- Browser analytics
ip_address      INET                    -- Geo analytics
referrer_url    TEXT                    -- Source tracking
created_at      TIMESTAMP WITH TIME ZONE
updated_at      TIMESTAMP WITH TIME ZONE
```

---

## 🎯 **Features Implementate**

### **🔒 Sicurezza e Privacy**
- ✅ **GDPR Compliance** con checkbox obbligatori
- ✅ **Email Validation** con regex pattern
- ✅ **Input Sanitization** via Pydantic models
- ✅ **IP Tracking** per analytics (opzionale)

### **🚀 User Experience**  
- ✅ **Popup Non-Invasivo** (solo dopo Capitolo 2)
- ✅ **Copy Simpatico** ("classico form di raccolta contatto...")
- ✅ **Prevenzione Duplicati** (sessionStorage + localStorage)
- ✅ **Backup Locale** se API fallisce

### **📊 Analytics Ready**
- ✅ **Metadata Tracking** (user_agent, IP, referrer)  
- ✅ **Role Segmentation** per target analysis
- ✅ **Challenge Insights** per product development
- ✅ **Chapter Tracking** per conversion funnel analysis

### **🔧 Technical Excellence**
- ✅ **Native Supabase Integration** 
- ✅ **Pydantic Validation** completa
- ✅ **Error Handling** robusto
- ✅ **Graceful Fallbacks** (localStorage backup)
- ✅ **RESTful API Design**

---

## 🎉 **Ready to Use!**

Il sistema è **production-ready** e si integra perfettamente con la codebase esistente. 

### **Quick Start:**
1. ✅ Esegui SQL su Supabase
2. ✅ Il backend è già configurato  
3. ✅ Il frontend è già attivo
4. 🚀 **Deploy and collect leads!**

### **Analytics Dashboard:**
Per visualizzare i leads raccolti:
```bash
# API call per ottenere tutti i leads
curl http://localhost:8000/api/book-leads

# Con paginazione
curl "http://localhost:8000/api/book-leads?skip=0&limit=50"
```

Il sistema è pronto per la raccolta dei lead! 🎯