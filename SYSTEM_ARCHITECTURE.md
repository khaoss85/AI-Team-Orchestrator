
# Architettura del Sistema AI Team Orchestrator

## 1. Panoramica

Questo documento descrive l'architettura end-to-end del sistema, progettata per essere **Goal-Driven**, **Scalabile** e **Robusta**. L'obiettivo è orchestrare un team di agenti AI per produrre deliverables concreti che soddisfino obiettivi di business predefiniti.

## 2. Componenti Principali

| Componente | File Principale | Responsabilità |
| :--- | :--- | :--- |
| **Workflow Orchestrator** | `workflow_orchestrator.py` | **CUORE DEL SISTEMA.** Gestisce l'intero ciclo di vita di un goal, dalla pianificazione all'aggiornamento del progresso. |
| **Goal-Driven Task Planner**| `goal_driven_task_planner.py` | Traduce un obiettivo di alto livello in una serie di **task concreti e orientati agli asset**. |
| **Task Executor** | `executor.py` | Gestisce una coda di task e ne coordina l'esecuzione da parte degli agenti AI specializzati. |
| **Specialist Agents** | `specialist.py` | Agenti AI che eseguono i task utilizzando un set di strumenti specifici per il loro ruolo. |
| **Tool Registry** | `utils/tool_registry.py` | Centralizza la creazione e l'accesso a tutti i tool, garantendo coerenza e passaggio del contesto (`workspace_id`). |
| **Quality Gate** | `quality_gate.py` | Valida la qualità di un "asset" prodotto da un task prima che diventi un "deliverable" ufficiale. |
| **Database Module** | `database.py` | Fornisce l'accesso al database (Supabase) con due livelli di privilegio: **user-level** (con RLS) e **service-level** (bypass RLS). |
| **AI Utils** | `utils/ai_utils.py` | Contiene la funzione `get_structured_ai_response` per chiamate a OpenAI robuste e basate su Pydantic. |

## 3. Flusso di Lavoro End-to-End

Il sistema opera seguendo un flusso logico preciso, orchestrato dal `WorkflowOrchestrator`.

```mermaid
graph TD
    subgraph "Phase 1: Goal & Planning"
        A[Goal Definito] --> B(Workflow Orchestrator);
        B --> C{Goal-Driven Task Planner};
        C --> D[Task Asset-Focused];
    end

    subgraph "Phase 2: Execution"
        D --> E{Task Executor};
        E --> F[Agenti AI Specializzati];
        F --> G((Tool Registry));
        F --> H[Asset Prodotto];
    end

    subgraph "Phase 3: Validation & Completion"
        H --> I{Quality Gate};
        I -- Passa --> J[Deliverable Creato];
        I -- Fallisce --> K[Task Marcato "needs_revision"];
        J --> L(Aggiornamento Progresso Goal);
    end

    style B fill:#f9f,stroke:#333,stroke-width:2px
    style I fill:#bbf,stroke:#333,stroke-width:2px
```

## 4. Logica delle Connessioni

1.  **Inizializzazione**: Il `main.py` avvia il `WorkflowOrchestrator`.
2.  **Processo per Workspace**: L'orchestratore recupera i goal attivi dal `database.py`.
3.  **Pianificazione**: Per ogni goal, invoca il `goal_driven_task_planner.py` per generare task.
4.  **Esecuzione**: I task vengono inviati all'`executor.py`, che li assegna agli `specialist.py`.
5.  **Utilizzo Tool**: Gli agenti usano il `tool_registry.py` per accedere agli strumenti necessari, passando il `workspace_id` per ogni operazione.
6.  **Completamento Task**: L'executor notifica all'orchestratore il completamento di un task e il relativo asset prodotto.
7.  **Validazione Qualità**: L'orchestratore passa l'asset al `quality_gate.py`.
8.  **Decisione**:
    *   **Successo**: Se il quality gate è superato, l'orchestratore aggiorna lo stato del task e il progresso del goal tramite `database.py`.
    *   **Fallimento**: Se il quality gate fallisce, il task viene marcato per la revisione, creando un ciclo di feedback.

Questo design assicura che ogni componente abbia una singola responsabilità e che il flusso sia controllato, misurabile e orientato alla qualità.
