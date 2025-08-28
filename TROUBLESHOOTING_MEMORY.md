# Troubleshooting Memory - Pattern Critici e Soluzioni

> Documento di memoria per evitare di rifare lo stesso lavoro diagnostico nei cicli futuri

## 🚨 Pattern Critici Identificati

### 1. Asset-Deliverable Sync Issues

**Sintomo**: Solo 1 asset "unknown" restituito invece di N deliverables attesi

**Bug Pattern**:
```python
# ERRORE: .extend() chiamato su dict invece di list
deliverable_assets = {}
deliverable_assets.extend(asset_list)  # AttributeError: 'dict' object has no attribute 'extend'
```

**Soluzione**:
```python
# CORREZIONE: Verificare sempre il tipo prima di .extend()
if isinstance(deliverable_assets, list):
    deliverable_assets.extend(asset_list)
else:
    deliverable_assets = list(asset_list)
```

**File Coinvolti**:
- `backend/routes/unified_assets.py`
- `backend/deliverable_system/unified_deliverable_engine.py`

### 2. API Contract 404 Issues

**Pattern**: Frontend chiama endpoint senza `/api` prefix causando 404

**Endpoint Problematici Ricorrenti**:
- `/health` → dovrebbe essere `/api/health`
- `/human-feedback/pending` → dovrebbe essere `/api/human-feedback/pending`
- `/unified-assets/{workspace_id}` → dovrebbe essere `/api/unified-assets/{workspace_id}`

**Soluzione - Backward Compatibility**:
```python
# In main.py aggiungere:
@app.get("/health")
async def health_backward_compat():
    return await health()

@app.get("/human-feedback/pending")
async def human_feedback_pending_backward_compat():
    return await get_pending_feedback()
```

**Quando Implementare**:
- Quando vedi 404 patterns nei log frontend
- Prima di modificare tutti i frontend calls

### 3. OpenAI Quota Management

**Sintomo**: Sistema rallenta ma non si blocca completamente

**Pattern**:
- Errore 429 "Quota exceeded" nei log
- Sistema usa fallback provider automaticamente
- Processing continua ma più lento

**Monitoring**:
```bash
# Controllare quota status
grep "429" backend/logs/*.log
grep "quota" backend/logs/*.log -i
```

**Azione**: Non blocca il sistema, solo monitorare performance

### 4. Performance Optimization Breakthrough

**Sintomo Critico**: Unified-assets API richiede 90+ secondi e blocca l'intera UI

**Root Cause**:
- Endpoint `/api/unified-assets/workspace/{id}` fa aggregazioni database pesanti
- UI bloccata in attesa, utenti pensano che l'app sia rotta
- Pattern sequenziale di loading API invece di progressivo

**Soluzione - Progressive Loading Pattern (94% improvement)**:

**Phase 1 (0-200ms) - Essential UI**:
```typescript
// Caricare solo dati essenziali per render immediato
const [workspace, team] = await Promise.all([
  api.workspaces.get(workspaceId),     // Metadati workspace
  api.agents.list(workspaceId)         // Team core per sidebar
])
setLoading(false) // UI ready immediatamente!
```

**Phase 2 (50ms+ background) - Enhancement**:
```typescript
// Loading non-bloccante in background
setTimeout(loadGoalsProgressive, 50)  // Goals + dynamic content
// User vede loading spinner, non app rotta
```

**Phase 3 (on-demand) - Heavy Assets**:
```typescript
// Solo quando esplicitamente richiesto
loadFullAssets: async () => {
  setAssetsLoading(true)
  await loadArtifacts(true) // includeAssets = true
}
```

**Loading States Granulari**:
```typescript
const [loading, setLoading] = useState(true)           // Load iniziale
const [goalsLoading, setGoalsLoading] = useState(false) // Goals phase
const [assetsLoading, setAssetsLoading] = useState(false) // Heavy assets
const [goalsError, setGoalsError] = useState<string | null>(null)
```

**File Coinvolti**:
- `frontend/src/hooks/useConversationalWorkspace.ts` (lines 276-459)
- `frontend/src/components/conversational/ConversationalWorkspace.tsx` (props loading states)

**Anti-Pattern da Evitare**:
```typescript
// ❌ MALE: Loading sequenziale blocca UI
const workspace = await api.workspaces.get(id)
const team = await api.agents.list(id)  
const goals = await api.goals.getAll(id) // UI bloccata fino alla fine

// ✅ BENE: Progressive enhancement
const [workspace, team] = await Promise.all([...]) // Parallel essentials
setTimeout(() => loadGoalsProgressive(), 50)        // Background enhancement
```

### 5. Goal-Deliverable Relationship Issues

**Sintomo Critico**: Frontend mostra "No deliverables available" per goal completati al 100%, ma backend ha deliverable esistenti

**Root Causes Identificate**:

1. **AI-Driven Goal Consolidation**:
   - Sistema trasforma automaticamente goal specifici in goal strategici 
   - Esempio: 6 goal tattici (setup email, sequence 1-3, contatti) → 2 goal strategici
   - Relationships (goal_id) non mantenute durante trasformazione

2. **Orphaned Data Relationship**:
   - Deliverable con `goal_id = NULL` dopo consolidazione
   - Task con `goal_id = NULL` 
   - Frontend API `/deliverables/goal/{id}` restituisce array vuoto

3. **Race Condition Duplicates**:
   - Deliverable duplicati creati simultaneamente 
   - Stesso titolo, contenuto corrotto/troncato
   - `PREVENT_DUPLICATE_DELIVERABLES=true` inefficace per race conditions

**Soluzioni - Goal Relationship Fix**:

```sql
-- 1. Identificare goal correnti
SELECT id, title FROM workspace_goals WHERE workspace_id = '{workspace_id}';

-- 2. Mappare deliverable semanticamente
UPDATE deliverables 
SET goal_id = '{goal_id}' 
WHERE workspace_id = '{workspace_id}' 
AND title LIKE '%keyword%';

-- 3. Prevenire duplicati futuri
ALTER TABLE deliverables 
ADD CONSTRAINT unique_workspace_goal_title 
UNIQUE (workspace_id, goal_id, title);
```

**Diagnostic Pattern**:
```bash
# Verificare orphaned deliverables
curl localhost:8000/api/deliverables/workspace/{workspace_id} | grep "goal_id.*null"

# Contare deliverable per goal
curl localhost:8000/api/deliverables/workspace/{workspace_id}/goal/{goal_id} | grep -c '"id"'
```

**File Coinvolti**:
- Database schema: `workspace_goals`, `deliverables`, `tasks`
- API endpoint: `backend/routes/deliverables.py`
- Frontend: `artifacts` panel goal-specific display

### 6. Sub-Agent Usage Patterns

**Quando Usare Sub-Agents**:

**db-steward** (PROATTIVO per database):
- Data relationship issues (orphaned foreign keys)
- Schema violations e constraint problems
- Database-level fixes e cleanup scripts
- **IMPORTANTE**: Per modifiche DB manuali, chiedere utente di eseguire SQL in Supabase Dashboard

**system-architect**:
- Problemi di sincronizzazione tra sistemi
- Architettura dati inconsistente
- Integration issues tra componenti

**api-contract-guardian**:
- Endpoint mancanti o 404
- API contract violations
- Frontend-backend contract issues

**Esempio Decision Tree**:
```
404 Error → api-contract-guardian
Sync Issues → system-architect
Data Issues/Database → db-steward
Goal-Deliverable Missing → db-steward + system-architect
Performance Issues → Implement progressive loading pattern
Duplicates → db-steward (cleanup + constraints)
Direct Code Fix → Edit tool
```

## 🔍 Diagnostic Workflow Standard

### Quick Diagnostic Checklist

1. **Performance Issues (UI lenta/bloccata)**:
   ```bash
   # Controllare tempi di risposta API
   time curl localhost:8000/api/unified-assets/{workspace_id}
   # Se > 5 secondi, implementare progressive loading
   
   # Verificare loading states nel browser DevTools Network tab
   # UI dovrebbe renderizzare in < 200ms per dati essenziali
   ```

2. **Asset/Deliverable Issues**:
   ```bash
   # Controllare unified assets endpoint
   curl localhost:8000/api/unified-assets/{workspace_id}
   # Aspettarsi: array di deliverables, non singolo "unknown"
   ```

3. **API 404 Issues**:
   ```bash
   # Controllare log per 404 patterns
   grep "404" frontend/logs/*.log
   grep "failed to fetch" frontend/logs/*.log -i
   ```

4. **Backend Health**:
   ```bash
   curl localhost:8000/api/health
   # Dovrebbe restituire status OK
   ```

### Sequence Diagnostica

1. **Identifica Sintomo**:
   - UI bloccata/lenta (>5s) → Performance issue
   - Asset vuoti → Type/Sync issue
   - 404 errors → API contract issue
   - Slow performance → Quota issue

2. **Verifica Root Cause**:
   - Network tab per API response times
   - Log backend per errors
   - Log frontend per failed requests
   - Database queries per data consistency

3. **Scegli Soluzione**:
   - UI performance → Implement progressive loading pattern
   - Code fix diretto → Use Edit tool
   - Architecture issue → Use system-architect
   - API contract → Use api-contract-guardian

## 🧩 Soluzioni Rapide

### Fix Performance UI Bloccata
```typescript
// In useConversationalWorkspace.ts - Progressive Loading Pattern
const initializeWorkspace = useCallback(async () => {
  try {
    setLoading(true)
    setError(null)

    // PHASE 1: Essential data only (fast render)
    const [workspace, team] = await Promise.all([
      api.workspaces.get(workspaceId),
      api.agents.list(workspaceId)
    ])
    
    setWorkspaceContext({
      id: workspaceId,
      name: workspace.name,
      team: team || [],
      goals: [], // Will be loaded progressively
    })
    setLoading(false) // UI ready immediately!

    // PHASE 2: Background enhancement (non-blocking)
    setTimeout(loadGoalsProgressive, 50)
    
  } catch (err) {
    setError(err.message)
  }
}, [workspaceId])

// Separate function for heavy operations
const loadGoalsProgressive = async () => {
  setGoalsLoading(true)
  try {
    const goals = await api.workspaceGoals.getAll(workspaceId)
    setWorkspaceContext(prev => ({ ...prev, goals }))
  } finally {
    setGoalsLoading(false)
  }
}
```

### Fix Asset Sync
```python
# In unified_deliverable_engine.py
def get_deliverable_assets(workspace_id: str):
    assets = []  # Inizializza come list, non dict
    for deliverable in deliverables:
        if deliverable.assets:
            assets.extend(deliverable.assets)  # Safe extend
    return assets
```

### Fix API 404
```python
# In main.py - aggiungere backward compatibility
legacy_routes = ["/health", "/human-feedback/pending"]
for route in legacy_routes:
    # Add redirect or duplicate endpoint
```

### Debug Asset Empty
```python
# Quick debug script
async def debug_assets(workspace_id: str):
    deliverables = await get_deliverables(workspace_id)
    print(f"Found {len(deliverables)} deliverables")
    for d in deliverables:
        print(f"Deliverable {d.id}: {len(d.assets)} assets")
```

## 📋 Prevention Checklist

- [ ] **Performance**: Monitorare API response times (>5s = problema)
- [ ] **Performance**: Implementare progressive loading per UI responsiva
- [ ] **Performance**: Loading states granulari per ogni fase di caricamento
- [ ] **Performance**: Mai bloccare UI per operazioni pesanti
- [ ] **Database**: Sempre usare db-steward per modifiche schema/constraints
- [ ] **Database**: Chiedere utente per modifiche manuali in Supabase Dashboard
- [ ] **Database**: Implementare unique constraints per prevenire duplicati
- [ ] **Goal-Deliverable**: Verificare goal_id relationships dopo consolidazione AI
- [ ] **Race Conditions**: Testare concurrency per deliverable creation
- [ ] Verificare tipo di variabile prima di `.extend()`
- [ ] Testare endpoint con e senza `/api` prefix
- [ ] Monitorare quota OpenAI regolarmente
- [ ] Usare sub-agents per problemi architetturali
- [ ] Documentare nuovi pattern qui trovati

## 🔄 Update Instructions

Quando trovi nuovi pattern critici:

1. Aggiungi sezione con stesso formato
2. Includi sintomo, causa, soluzione
3. Aggiorna checklist diagnostic
4. Testa soluzione su ambiente dev

---
*Ultimo aggiornamento: 2025-08-28*
*Sessione: Goal-Deliverable Relationship Fix + Duplicate Cleanup*
*Risultati: Frontend mostra deliverable per goal completati + duplicati eliminati + constraint DB aggiunto*
*Precedenti: Performance Optimization (94% riduzione tempo caricamento 90s → 3-5s)*