# Registro del Debito Tecnico - Migrazione OpenAI SDK

Questo file traccia tutte le semplificazioni, i placeholder e le soluzioni temporanee introdotte durante la migrazione all'OpenAI Agent SDK. L'obiettivo è garantire che ogni voce venga risolta prima di considerare il refactoring completo e "production-ready".

---

### Voci di Debito Tecnico Attuali

#### 1. Implementazione SDK Simulata nel Task Planner
- **Componente:** `backend/goal_driven_task_planner_sdk.py`
- **Tipo di Debito:** Logica Simulata (Placeholder)
- **Motivazione:** Implementare la struttura dell'agente SDK senza avere ancora l'SDK completo e funzionante, per procedere con la migrazione condizionale.
- **Piano di Risoluzione:** Sostituire la risposta simulata con una chiamata reale all'SDK `agents` tramite `AIProviderManager`, includendo la gestione degli errori e del trace.
- **Fase di Risoluzione:** FASE 2: IMPLEMENTAZIONE REALE DELL'SDK

#### 2. Endpoint dei Deliverables Restituisce Errore 500
- **Componente:** `backend/routes/deliverables.py` (e `database.py`)
- **Tipo di Debito:** Bug Critico / Endpoint Non Funzionante
- **Motivazione:** Il problema è stato temporaneamente aggirato nel test E2E per poter procedere, ma la causa principale (probabilmente un errore nella query al DB o nella serializzazione dei dati) non è ancora risolta.
- **Piano di Risoluzione:** Eseguire un deep-dive sulla funzione `get_deliverables` e sulla sua interazione con Supabase per identificare e correggere la causa dell'errore 500.
- **Fase di Risoluzione:** FASE 1: STABILIZZAZIONE DEL CORE LOOP (Ripresa)

#### 3. Gestione Incompleta degli Errori di Import
- **Componente:** `backend/comprehensive_e2e_test.py`
- **Tipo di Debito:** Gestione Errore Temporanea
- **Motivazione:** L'import di `schema_verification` è stato commentato per permettere l'esecuzione del test.
- **Piano di Risoluzione:** Invece di commentare, implementare una gestione degli import più robusta o rimuovere definitivamente la dipendenza se il modulo è obsoleto, verificando tutti i punti del codice che lo utilizzavano.
- **Fase di Risoluzione:** FASE 4: CLEANUP & VALIDATION

#### 4. Placeholder di Classi nel Quality Engine
- **Componente:** `backend/ai_quality_assurance/unified_quality_engine.py`
- **Tipo di Debito:** Placeholder di Classe
- **Motivazione:** Le classi `AIQualityEvaluator` e `EnhancedAIQualityValidator` sono state aggiunte come placeholder vuoti per risolvere errori di import immediati.
- **Piano di Risoluzione:** Analizzare dove queste classi dovrebbero essere definite, se sono state consolidate in altre classi, o se sono semplicemente residui da rimuovere. Aggiornare il codice che le importa di conseguenza.
- **Fase di Risoluzione:** FASE 4: CLEANUP & VALIDATION

#### 5. Assegnazione Agente Basata su Regole
- **Componente:** `backend/executor.py` (funzione `_assign_agent_to_task_by_role`)
- **Tipo di Debito:** Logica Semplificata (Non AI-Driven)
- **Motivazione:** L'attuale logica di fallback per assegnare un agente a un ruolo si basa su semplici `if/elif` e corrispondenze di stringhe. Questo non è robusto né intelligente.
- **Piano di Risoluzione:** Sostituire la logica di fallback con una chiamata semantica tramite `AIProviderManager` a un agente specializzato ("Agent Matcher") che, dato un ruolo e una descrizione del task, seleziona l'agente più adatto dal pool di agenti disponibili.
- **Fase di Risoluzione:** FASE 5: MIGLIORAMENTI AI-DRIVEN (Post-Migrazione)

#### 6. Migrazione Parziale del Motore di Memoria
- **Componente:** `backend/services/unified_memory_engine.py`
- **Tipo di Debito:** Implementazione Temporanea (Agenti Inline)
- **Motivazione:** Le chiamate dirette all'API OpenAI sono state migrate per usare `AIProviderManager`. Tuttavia, per accelerare la migrazione, gli agenti (`SemanticSearchAgent`, `MemoryEnhancedAssetGeneratorAgent`) sono stati definiti come dizionari inline direttamente nelle funzioni chiamanti.
- **Piano di Risoluzione:** Creare file di agenti dedicati per `SemanticSearchAgent` e `MemoryEnhancedAssetGeneratorAgent` nella directory `project_agents/`. Questi file conterranno la configurazione completa dell'agente (istruzioni, modello, ecc.), rendendo il sistema più modulare e manutenibile.
- **Fase di Risoluzione:** FASE 4: CLEANUP & VALIDATION

#### 7. Migrazione Servizi di Supporto
- **Componente:** 
  - `backend/goal_decomposition_system.py`
  - `backend/ai_skill_analyzer.py`
  - `backend/routes/ai_content_processor.py`
  - `backend/services/universal_ai_pipeline_engine.py`
  - `backend/services/deliverable_achievement_mapper.py`
- **Tipo di Debito:** Implementazione Temporanea (Agenti Inline)
- **Motivazione:** Le chiamate dirette all'API OpenAI sono state migrate per usare `AIProviderManager`. Tuttavia, per accelerare la migrazione, gli agenti sono stati definiti come dizionari inline direttamente nelle funzioni chiamanti.
- **Piano di Risoluzione:** Creare file di agenti dedicati per ogni agente temporaneo nella directory `project_agents/`.
- **Fase di Risoluzione:** FASE 4: CLEANUP & VALIDATION

#### 8. Bypass Temporaneo nel Getter dei Deliverables
- **Componente:** `backend/routes/deliverables.py` (funzione `get_workspace_deliverables`)
- **Tipo di Debito:** Logica di Debug
- **Motivazione:** Per isolare la causa dell'errore 500, la funzione è stata modificata per restituire una lista vuota invece di chiamare il database. Questo ci permette di verificare se il problema risiede nella chiamata a `get_deliverables` in `database.py`.
- **Piano di Risoluzione:** Rimuovere il bypass e ripristinare la chiamata originale a `await get_deliverables(workspace_id)` una volta che il problema sottostante nel database è stato risolto.
- **Fase di Risoluzione:** FASE 1: STABILIZZAZIONE DEL CORE LOOP (Ripresa)

#### 9. Placeholder nei Tool degli Agenti
- **Componente:** `backend/ai_agents/tools.py`
- **Tipo di Debito:** Logica Simulata (Placeholder)
- **Motivazione:** Diverse funzioni nei tool comuni (`CommonTools`, `DataTools`) restituivano dati placeholder invece di eseguire logica reale.
- **Stato:** PARZIALMENTE RISOLTO.
  - ✅ `search_web` e `fetch_url` implementati con `web_fetch`.
  - ✅ `analyze_text`, `generate_headlines`, `find_correlation` implementati con `AIProviderManager`.
  - ⚠️ `store_data`, `retrieve_data`, `get_available_handoffs` rimangono come placeholder.
- **Piano di Risoluzione:** Implementare una logica di backend reale per le funzioni rimanenti o collegarle a un database/servizio appropriato.
- **Fase di Risoluzione:** FASE 5: MIGLIORAMENTI AI-DRIVEN (Post-Migrazione)
