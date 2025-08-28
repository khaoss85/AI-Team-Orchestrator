# Sistema di Auto-Recovery per Task Falliti
## Architettura di Riutilizzo Componenti Esistenti

### 📋 Executive Summary

Questo documento propone un'architettura per un sistema intelligente di auto-recovery che riutilizza componenti esistenti nel codebase per rilevare automaticamente task falliti per errori risolti e riavviarli senza intervento manuale.

### 🔍 Analisi Componenti Esistenti

#### 1. **Executor.py - Meccanismi di Health & Retry**

**Componenti riutilizzabili identificati:**

- **Circuit Breaker Pattern** (lines 586-595): Sistema già implementato per gestire fallimenti consecutivi
  ```python
  circuit_breaker = {
      'failure_count': 0,
      'last_failure_time': 0,
      'state': 'closed',  # closed, open, half_open
      'failure_threshold': 5,
      'recovery_timeout': 300,  # 5 minutes recovery
      'half_open_max_calls': 3
  }
  ```

- **Task Monitoring Integration** (lines 536-538): Già integrato TaskExecutionMonitor
  ```python
  # Task execution monitoring (will be started when executor starts)
  self.monitoring_started = False
  if TASK_MONITOR_AVAILABLE:
      logger.info("✅ Task execution monitoring ready")
  ```

- **Force Complete Task Method** (lines 1030-1079): Meccanismo per forzare completamento task falliti
- **Anti-loop Protection** (lines 955-1090): Sistema per prevenire loop infiniti su task problematici

#### 2. **Health Monitor.py - Auto-fix Systems**

**Componenti riutilizzabili identificati:**

- **Auto-fix Workspace Errors** (lines 105-119): Sistema automatico per risolvere stati di errore
  ```python
  # Auto-fix error workspaces
  for workspace in error_workspaces:
      self.supabase.table('workspaces').update({
          'status': 'active'
      }).eq('id', workspace['id']).execute()
  ```

- **Executor Health Monitoring** (lines 128-168): Controllo e restart automatico executor
- **Stalled Task Detection** (lines 170-211): Rilevamento task bloccati >30 minuti
- **Health Score Calculation** (lines 252-263): Scoring system per valutare gravità problemi

#### 3. **Task Execution Monitor.py - Monitoring Components**

**Componenti riutilizzabili identificati:**

- **ExecutionStage Enum** (lines 25-39): Tracking dettagliato fasi esecuzione
- **TaskExecutionTrace** (lines 41-58): Sistema di tracciamento completo task
- **Hang Detection** (lines 67-75): Rilevamento automatico task bloccati dopo threshold
- **Background Monitoring** (line 75): Sistema di monitoring continuo

#### 4. **Database.py & Models.py - Task State Management**

**Componenti riutilizzabili identificati:**

- **TaskStatus Enum** (lines 25-29 models.py): Stati standard dei task (PENDING, IN_PROGRESS, COMPLETED, FAILED)
- **update_task_status Function** (line 1177 database.py): Sistema centralizzato aggiornamento stati
- **WorkspaceStatus Management**: Stati workspace con ERROR e NEEDS_INTERVENTION

#### 5. **Workspace Health Manager - Intelligent Recovery**

**Componenti riutilizzabili identificati:**

- **RecoveryStrategy Enum** (lines 43-50): Strategie di recovery predefinite
- **Auto-recovery System** (lines 96-116): Sistema intelligente con confidence scoring
- **Health Assessment** (lines 112-150): Valutazione comprensiva salute workspace
- **Dynamic Threshold Management**: Soglie adattive basate su contesto

---

### 🏗️ Architettura Proposta: Sistema Auto-Recovery

#### Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    INTELLIGENT AUTO-RECOVERY                    │
│                         ORCHESTRATOR                           │
└─────────────────────────────────────────────────────────────────┘
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
        ┌───────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
        │   DETECTION  │ │  ANALYSIS   │ │  RECOVERY   │
        │   ENGINE     │ │   ENGINE    │ │  EXECUTION  │
        └──────────────┘ └─────────────┘ └─────────────┘
```

### 📊 Component Reuse Map

| **Nuovo Componente** | **Riutilizza da** | **Funzionalità** |
|---------------------|-------------------|------------------|
| **FailureDetectionEngine** | TaskExecutionMonitor + HealthMonitor | Rileva task falliti e pattern errore |
| **RecoveryAnalysisEngine** | WorkspaceHealthManager + Circuit Breaker | Analizza cause e determina strategia |
| **AutoRecoveryExecutor** | Executor + force_complete_task | Esegue recovery automatico |
| **RecoveryPolicyManager** | Existing RecoveryStrategy + Enums | Gestisce policy e soglie recovery |

---

### 🎯 Piano di Implementazione

#### Phase 1: Detection Engine (Riutilizzo 80%)
```python
class FailureDetectionEngine:
    """Rileva task falliti per errori temporanei risolti"""
    
    def __init__(self):
        # RIUSO: TaskExecutionMonitor per tracking
        self.task_monitor = task_monitor
        
        # RIUSO: Circuit Breaker logic da executor
        self.circuit_breakers = defaultdict(self._create_circuit_breaker)
        
        # RIUSO: Health scoring da WorkspaceHealthManager  
        self.health_manager = WorkspaceHealthManager()
    
    async def detect_recoverable_failures(self) -> List[RecoverableFailure]:
        """
        RIUSO COMPLETO di:
        - TaskExecutionTrace per identificare hang points
        - Health scoring per priorità recovery
        - Circuit breaker state per evitare retry inutili
        """
```

#### Phase 2: Analysis Engine (Riutilizzo 90%)
```python
class RecoveryAnalysisEngine:
    """Analizza cause failure e determina strategia recovery"""
    
    async def analyze_failure_cause(self, task_id: str) -> RecoveryStrategy:
        """
        RIUSO DIRETTO di:
        - RecoveryStrategy enum esistente
        - HealthIssue classification da WorkspaceHealthManager
        - Circuit breaker recovery logic da executor
        """
```

#### Phase 3: Recovery Executor (Riutilizzo 70%)
```python
class AutoRecoveryExecutor:
    """Esegue recovery automatico basato su strategia"""
    
    async def execute_recovery(self, strategy: RecoveryStrategy, task_id: str):
        """
        RIUSO DIRETTO di:
        - force_complete_task method da executor
        - update_task_status da database
        - Auto-fix logic da HealthMonitor
        """
```

---

### ⚙️ Integration Points

#### 1. **Executor Integration**
```python
# In executor.py - _anti_loop_worker method
if execution_result and execution_result.status == TaskStatus.FAILED:
    # NUOVO: Trigger auto-recovery analysis
    if await auto_recovery_system.should_attempt_recovery(task_id):
        recovery_result = await auto_recovery_system.attempt_recovery(task_id)
        if recovery_result.success:
            logger.info(f"🔄 Auto-recovered task {task_id}")
```

#### 2. **Health Monitor Integration**
```python
# In health_monitor.py - run_health_check method  
# ESTENSIONE: Aggiungi auto-recovery checks
async def _check_auto_recovery_opportunities(self, results):
    """Identifica task falliti ma ora recoverable"""
    recoverable_tasks = await auto_recovery_system.scan_for_recoverable_tasks()
    if recoverable_tasks:
        results['recovery_opportunities'] = len(recoverable_tasks)
```

#### 3. **Task Execution Monitor Integration**
```python
# In task_execution_monitor.py
# ESTENSIONE: Aggiungi recovery triggers
def trace_task_failure(self, task_id: str, error_info: dict):
    """Enhanced failure tracking per auto-recovery"""
    # Existing logic + recovery trigger
    asyncio.create_task(
        auto_recovery_system.evaluate_for_recovery(task_id, error_info)
    )
```

---

### 📈 Expected Benefits

#### **Immediate Impact (30 giorni)**
- **90% reduction** in manual task retry interventions
- **Auto-recovery rate**: 70-80% per errori temporanei
- **MTTR reduction**: da 2-4 ore a 5-10 minuti

#### **Long-term Impact (90 giorni)**  
- **Self-healing system**: Sistema che impara pattern di errore
- **Proactive recovery**: Prevenzione failure basata su pattern
- **Minimal human intervention**: Solo per errori complessi

---

### 🔒 Safety & Constraints

#### **Recovery Limits**
- **Max 3 retry attempts** per task per evitare loop
- **Exponential backoff**: 5min → 15min → 45min
- **Circuit breaker integration**: Stop auto-recovery dopo 5 fallimenti consecutivi

#### **Recovery Triggers**
- ✅ **Temporary network errors** (connection timeout, rate limits)
- ✅ **Transient service errors** (503, 429 HTTP errors)  
- ✅ **Resource availability issues** (memory, API quota)
- ❌ **Logic errors** (require code changes)
- ❌ **Data corruption** (require manual intervention)

---

### 💡 Implementation Priority

| **Priority** | **Component** | **Effort** | **Reuse %** | **Impact** |
|-------------|---------------|------------|-------------|------------|
| **P1** | FailureDetectionEngine | 2 settimane | 85% | Alto |
| **P2** | RecoveryAnalysisEngine | 1 settimana | 90% | Medio |
| **P3** | AutoRecoveryExecutor | 1.5 settimane | 75% | Alto |
| **P4** | Recovery Dashboard/UI | 1 settimana | 60% | Basso |

---

### 📋 Next Steps

1. **Setup Development Environment** con componenti identificati
2. **Create FailureDetectionEngine** riutilizzando TaskExecutionMonitor  
3. **Implement RecoveryAnalysisEngine** basato su WorkspaceHealthManager
4. **Integration Testing** con executor e health_monitor esistenti
5. **Production Rollout** con feature flags per controllo graduale

---

### 🎯 Success Metrics

- **Auto-recovery Success Rate**: >75%
- **False Positive Rate**: <5% 
- **Manual Intervention Reduction**: >80%
- **System Availability Improvement**: >99.5%
- **Recovery Time**: <10 minuti per 90% dei casi

Questo sistema rappresenta un'evoluzione naturale dell'architettura esistente, massimizzando il riutilizzo di componenti già testati e mantenendo la coerenza architetturale del sistema.