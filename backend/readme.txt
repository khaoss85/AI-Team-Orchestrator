# AI Team Orchestrator - Documentazione API Frontend

## 📋 Indice

1. [Overview del Sistema](#overview-del-sistema)
2. [Architettura API](#architettura-api)
3. [Endpoint Reference](#endpoint-reference)
4. [Modelli di Dati](#modelli-di-dati)
5. [Flussi di Lavoro](#flussi-di-lavoro)
6. [Stati e Transizioni](#stati-e-transizioni)
7. [Monitoring e Debugging](#monitoring-e-debugging)
8. [Esempi Pratici](#esempi-pratici)

---

## 🎯 Overview del Sistema

**AI Team Orchestrator** è una piattaforma che permette di creare e gestire team di agenti AI che collaborano su progetti complessi. Il sistema gestisce:

- **Workspace**: Progetti contenenti team di agenti
- **Agenti AI**: Specialisti con ruoli specifici (PM, Analyst, Content Creator, etc.)
- **Task**: Attività assegnate agli agenti con esecuzione automatica
- **Handoffs**: Passaggi di lavoro tra agenti
- **Deliverable**: Output finali aggregati del progetto

### Caratteristiche Principali

✅ **Anti-Loop Protection**: Prevenzione di loop infiniti nei task  
✅ **Budget Tracking**: Monitoraggio costi token/LLM  
✅ **Phase Management**: Gestione fasi progetto (Analysis → Implementation → Finalization)  
✅ **Human Feedback**: Sistema di approvazione manuale  
✅ **Real-time Monitoring**: Dashboard per monitoraggio in tempo reale  

---

## 🏗️ Architettura API

### Base URL
```
http://localhost:8000
```

### Struttura Router
```
/workspaces     # Gestione progetti
/agents         # Gestione agenti AI
/director       # Creazione team automatica
/tools          # Tool personalizzati
/monitoring     # Monitoraggio sistema
/human-feedback # Approvazioni manuali
/projects       # Insights e deliverable
/delegation     # Analisi delegazione
```

### Headers Richiesti
```json
{
  "Content-Type": "application/json",
  "Accept": "application/json"
}
```

---

## 📡 Endpoint Reference

### 🏢 Workspaces

#### Crea Workspace
```http
POST /workspaces/
```

**Request Body:**
```json
{
  "name": "Marketing Campaign 2024",
  "description": "Instagram marketing campaign for Q1",
  "user_id": "uuid-string",
  "goal": "Create comprehensive Instagram marketing strategy with content calendar and lead generation system",
  "budget": {
    "max_amount": 1000,
    "currency": "EUR",
    "strategy": "conservative"
  }
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "Marketing Campaign 2024",
  "description": "Instagram marketing campaign for Q1",
  "user_id": "uuid",
  "status": "created",
  "goal": "Create comprehensive Instagram marketing strategy...",
  "budget": { "max_amount": 1000, "currency": "EUR" },
  "created_at": "2024-01-20T10:00:00Z",
  "updated_at": "2024-01-20T10:00:00Z"
}
```

#### Lista Workspace Utente
```http
GET /workspaces/user/{user_id}
```

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Marketing Campaign 2024",
    "status": "active",
    "created_at": "2024-01-20T10:00:00Z",
    "budget": { "max_amount": 1000 }
  }
]
```

#### Elimina Workspace
```http
DELETE /workspaces/{workspace_id}
```

**Response:**
```json
{
  "success": true,
  "message": "Workspace uuid deleted successfully",
  "workspace_id": "uuid"
}
```

### 🤖 Agenti

#### Lista Agenti Workspace
```http
GET /agents/{workspace_id}
```

**Response:**
```json
[
  {
    "id": "uuid",
    "workspace_id": "uuid",
    "name": "Sarah Johnson",
    "role": "Project Manager",
    "seniority": "senior",
    "status": "active",
    "health": {
      "status": "healthy",
      "last_update": "2024-01-20T10:30:00Z"
    },
    "created_at": "2024-01-20T10:00:00Z"
  }
]
```

#### Crea Task
```http
POST /agents/{workspace_id}/tasks
```

**Request Body:**
```json
{
  "workspace_id": "uuid",
  "agent_id": "uuid",
  "name": "Research Instagram competitors",
  "description": "Analyze top 5 competitors in our industry on Instagram",
  "status": "pending",
  "priority": "high"
}
```

#### Esegui Task
```http
POST /agents/{workspace_id}/execute/{task_id}
```

**Response:**
```json
{
  "workspace_id": "uuid",
  "task_id": "uuid",
  "result": {
    "task_id": "uuid",
    "status": "completed",
    "summary": "Analyzed 5 main competitors...",
    "execution_time_seconds": 45.2
  }
}
```

### 🎯 Director (Team AI)

#### Genera Proposta Team
```http
POST /director/proposal
```

**Request Body:**
```json
{
  "workspace_id": "uuid",
  "goal": "Create Instagram marketing strategy with lead generation",
  "budget_constraint": {
    "max_amount": 1000,
    "currency": "EUR"
  },
  "user_id": "uuid"
}
```

**Response:**
```json
{
  "id": "uuid",
  "workspace_id": "uuid",
  "agents": [
    {
      "name": "Marketing Analyst",
      "role": "Marketing Analysis Specialist",
      "seniority": "senior",
      "description": "Specialized in social media analysis..."
    }
  ],
  "handoffs": [
    {
      "from": "Marketing Analyst",
      "to": "Content Creator",
      "description": "Hand off market research for content strategy"
    }
  ],
  "estimated_cost": {
    "total_estimated": 750,
    "currency": "EUR"
  },
  "rationale": "This team composition provides...",
  "status": "pending"
}
```

#### Approva Team
```http
POST /director/approve/{workspace_id}?proposal_id={proposal_id}
```

**Response:**
```json
{
  "status": "success",
  "message": "Team approved and agents created",
  "created_agent_ids": ["uuid1", "uuid2"],
  "created_handoff_ids": ["uuid1"]
}
```

### 📊 Monitoring

#### Status Workspace
```http
GET /monitoring/workspace/{workspace_id}/status
```

**Response:**
```json
{
  "workspace_id": "uuid",
  "workspace_name": "Marketing Campaign 2024",
  "workspace_status": "active",
  "agents": {
    "total": 3,
    "by_status": {
      "active": 3,
      "paused": 0
    }
  },
  "budget": {
    "total_cost": 45.67,
    "currency": "USD",
    "budget_percentage": 4.5
  },
  "recent_activity": [
    {
      "timestamp": "2024-01-20T11:00:00Z",
      "event": "task_completed",
      "task_name": "Instagram competitor analysis"
    }
  ]
}
```

#### Avvia Team
```http
POST /monitoring/workspace/{workspace_id}/start
```

**Response:**
```json
{
  "success": true,
  "message": "Initial task created or already present. Team processes initiated.",
  "initial_task_id": "uuid"
}
```

#### Analisi Task
```http
GET /monitoring/workspace/{workspace_id}/task-analysis
```

**Response:**
```json
{
  "task_counts": {
    "completed": 15,
    "pending": 3,
    "failed": 1
  },
  "failure_analysis": {
    "total_failures": 1,
    "max_turns_failures": 0,
    "execution_errors": 1,
    "failure_reasons": {
      "execution_error": 1
    },
    "average_failure_time": 23.5
  },
  "handoff_analysis": {
    "total_handoff_tasks": 5,
    "handoff_success_rate": 0.8,
    "most_common_handoff_types": {
      "delegation_handoff": 3,
      "escalation_handoff": 2
    }
  },
  "potential_issues": {
    "runaway_detected": false,
    "excessive_handoffs": false,
    "high_failure_rate": false,
    "stuck_agents": [],
    "queue_overflow_risk": false
  },
  "recommendations": [
    "System appears healthy. Continue monitoring."
  ]
}
```

#### Budget Workspace
```http
GET /monitoring/workspace/{workspace_id}/budget
```

**Response:**
```json
{
  "workspace_id": "uuid",
  "total_cost": 67.45,
  "agent_costs": {
    "agent-uuid-1": 23.50,
    "agent-uuid-2": 43.95
  },
  "total_tokens": {
    "input": 15000,
    "output": 8500
  },
  "currency": "USD",
  "budget_limit": 1000,
  "budget_percentage": 6.7
}
```

### 🎨 Project Insights

#### Insights Progetto
```http
GET /projects/{workspace_id}/insights
```

**Response:**
```json
{
  "overview": {
    "total_tasks": 25,
    "completed_tasks": 18,
    "pending_tasks": 4,
    "progress_percentage": 72.0,
    "health_score": 85
  },
  "timing": {
    "time_elapsed_days": 3.5,
    "avg_task_completion_hours": 2.3,
    "estimated_completion_days": 1.2,
    "estimated_completion_date": "2024-01-23T15:30:00Z"
  },
  "current_state": {
    "phase": "Implementation Phase",
    "status": "active",
    "active_agents": 3
  },
  "performance": {
    "cost_per_completed_task": 3.75,
    "total_cost": 67.50,
    "budget_utilization": 6.7
  }
}
```

#### Deliverable Progetto
```http
GET /projects/{workspace_id}/deliverables
```

**Response:**
```json
{
  "workspace_id": "uuid",
  "summary": "Comprehensive Instagram marketing strategy developed with competitor analysis, content calendar, and lead generation system.",
  "key_outputs": [
    {
      "task_id": "uuid",
      "task_name": "🎯 FINAL DELIVERABLE: Content Strategy",
      "output": "Executive Summary: Comprehensive Instagram marketing strategy...",
      "agent_name": "Content Strategist",
      "agent_role": "Content Strategy Specialist",
      "type": "final_deliverable",
      "created_at": "2024-01-20T15:00:00Z"
    }
  ],
  "insight_cards": [
    {
      "id": "analysis_3_20240120",
      "title": "Market Analysis & Research",
      "description": "Comprehensive competitor analysis and audience research completed",
      "category": "analysis",
      "icon": "📊",
      "key_insights": [
        "Identified 5 key competitor strategies",
        "Defined target audience segments",
        "Analyzed engagement patterns"
      ],
      "completeness_score": 95
    }
  ],
  "final_recommendations": [
    "Focus on video content for higher engagement",
    "Implement consistent posting schedule",
    "Use data-driven hashtag strategy"
  ],
  "next_steps": [
    "Implement content calendar",
    "Set up analytics tracking",
    "Launch first campaign"
  ],
  "completion_status": "awaiting_review",
  "generated_at": "2024-01-20T15:30:00Z"
}
```

#### Feedback su Deliverable
```http
POST /projects/{workspace_id}/deliverables/feedback
```

**Request Body:**
```json
{
  "feedback_type": "request_changes",
  "message": "Please add more detail on the content calendar and include specific posting times",
  "specific_tasks": ["content-calendar-task-id"],
  "priority": "high"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Feedback received and task created for handling",
  "feedback_type": "request_changes"
}
```

### 🔄 Delegation Monitor

#### Analisi Delegazione
```http
GET /delegation/workspace/{workspace_id}/analysis
```

**Response:**
```json
{
  "workspace_id": "uuid",
  "analysis_timestamp": "2024-01-20T16:00:00Z",
  "summary": {
    "total_delegation_attempts": 15,
    "successful_delegations": 12,
    "self_executions": 2,
    "escalations": 1,
    "failures": 0,
    "success_rate": 80.0,
    "health_score": 85.5
  },
  "role_statistics": {
    "Project Manager": {
      "total_requests": 8,
      "successful_delegations": 7,
      "self_executions": 1,
      "escalations": 0
    }
  },
  "most_delegated_to": {
    "Content Specialist": 5,
    "Marketing Analyst": 4
  },
  "bottlenecks": {
    "Data Scientist": 2,
    "SEO Specialist": 1
  },
  "recommendations": [
    "System appears healthy. Continue monitoring.",
    "Consider adding SEO Specialist for better coverage."
  ]
}
```

### 🔧 Tools

#### Store Data
```http
POST /tools/store-data
```

**Request Body:**
```json
{
  "key": "competitor_analysis_results",
  "value": {
    "competitors": ["brand1", "brand2"],
    "analysis_date": "2024-01-20"
  },
  "workspace_id": "uuid",
  "agent_id": "uuid"
}
```

#### Retrieve Data
```http
GET /tools/retrieve-data/{workspace_id}/{key}
```

**Response:**
```json
{
  "success": true,
  "key": "competitor_analysis_results",
  "workspace_id": "uuid",
  "data": {
    "competitors": ["brand1", "brand2"],
    "analysis_date": "2024-01-20"
  }
}
```

---

## 📋 Modelli di Dati

### Workspace
```typescript
interface Workspace {
  id: string;
  name: string;
  description?: string;
  user_id: string;
  status: "created" | "active" | "paused" | "completed" | "error" | "needs_intervention";
  goal?: string;
  budget?: {
    max_amount: number;
    currency: string;
    strategy?: string;
  };
  created_at: string;
  updated_at: string;
}
```

### Agent
```typescript
interface Agent {
  id: string;
  workspace_id: string;
  name: string;
  first_name?: string;
  last_name?: string;
  role: string;
  seniority: "junior" | "senior" | "expert";
  description?: string;
  status: "created" | "initializing" | "active" | "paused" | "error" | "terminated";
  health: {
    status: "unknown" | "healthy" | "degraded" | "unhealthy";
    last_update?: string;
    details?: any;
  };
  llm_config?: any;
  tools?: any[];
  can_create_tools: boolean;
  personality_traits?: string[];
  communication_style?: string;
  hard_skills?: Skill[];
  soft_skills?: Skill[];
  background_story?: string;
  created_at: string;
  updated_at: string;
}
```

### Task
```typescript
interface Task {
  id: string;
  workspace_id: string;
  agent_id?: string;
  assigned_to_role?: string;
  name: string;
  description?: string;
  status: "pending" | "in_progress" | "completed" | "failed" | "canceled" | "timed_out";
  priority: "low" | "medium" | "high";
  parent_task_id?: string;
  depends_on_task_ids?: string[];
  estimated_effort_hours?: number;
  deadline?: string;
  context_data?: any;
  result?: any;
  created_at: string;
  updated_at: string;
}
```

### Task Execution Result
```typescript
interface TaskExecutionResult {
  task_id: string;
  status: "completed" | "failed" | "requires_handoff";
  summary: string;
  detailed_results_json?: string;
  next_steps?: string[];
  suggested_handoff_target_role?: string;
  resources_consumed_json?: string;
  execution_time_seconds?: number;
  model_used?: string;
  cost_estimated?: number;
  tokens_used?: {
    input: number;
    output: number;
  };
}
```

---

## 🔄 Flussi di Lavoro

### 1. Creazione Progetto Completo

```mermaid
graph TD
    A[Crea Workspace] --> B[Genera Proposta Team]
    B --> C[Approva Team]
    C --> D[Agenti Creati]
    D --> E[Avvia Team]
    E --> F[Task Iniziale Creato]
    F --> G[Esecuzione Automatica]
```

**Sequenza API:**
1. `POST /workspaces/` - Crea workspace
2. `POST /director/proposal` - Genera team AI
3. `POST /director/approve/{workspace_id}` - Approva e crea agenti
4. `POST /monitoring/workspace/{workspace_id}/start` - Avvia il team

### 2. Monitoraggio Progetto

```mermaid
graph TD
    A[Dashboard] --> B[Status Workspace]
    A --> C[Analisi Task]
    A --> D[Budget Tracking]
    A --> E[Insights Progetto]
    B --> F[Azioni Correttive]
    C --> F
    D --> F
    E --> G[Deliverable Ready]
```

**Endpoint Chiave:**
- `GET /monitoring/workspace/{id}/status` - Status generale
- `GET /monitoring/workspace/{id}/task-analysis` - Analisi dettagliata
- `GET /monitoring/workspace/{id}/budget` - Monitoraggio costi
- `GET /projects/{id}/insights` - Insights avanzati

### 3. Gestione Fasi Progetto

Il sistema gestisce automaticamente 3 fasi:

1. **ANALYSIS** - Ricerca, analisi competitor, audience
2. **IMPLEMENTATION** - Strategia, framework, pianificazione  
3. **FINALIZATION** - Creazione contenuti, deliverable finali

**Endpoint Monitoraggio Fasi:**
```http
GET /monitoring/workspace/{workspace_id}/finalization-status
```

**Response:**
```json
{
  "finalization_phase_active": true,
  "finalization_tasks_completed": 2,
  "final_deliverables_completed": 1,
  "project_completion_percentage": 85,
  "next_action_needed": "COMPLETE_DELIVERABLES"
}
```

---

## 🚦 Stati e Transizioni

### Stati Workspace
- **created** → **active** (quando viene avviato il team)
- **active** → **paused** (pausa manuale)
- **active** → **completed** (progetto finito)
- **active** → **needs_intervention** (problemi rilevati)

### Stati Task
- **pending** → **in_progress** → **completed**
- **pending** → **in_progress** → **failed**
- **pending** → **canceled**

### Stati Agent
- **created** → **active** → **paused**/**terminated**

### Gestione Errori

**Runaway Detection**: Il sistema rileva automaticamente loop infiniti
```http
GET /monitoring/runaway-protection/status
POST /monitoring/workspace/{id}/reset-runaway
```

**Task Reset**: Ripristina task falliti
```http
POST /monitoring/tasks/{task_id}/reset
```

---

## 🔍 Monitoring e Debugging

### Dashboard Real-time

**Endpoint Chiave per Dashboard:**
```javascript
// Status generale ogni 5 secondi
GET /monitoring/workspace/{id}/status

// Attività recente ogni 10 secondi  
GET /monitoring/workspace/{id}/activity?limit=20

// Budget ogni 30 secondi
GET /monitoring/workspace/{id}/budget

// Analisi completa ogni 2 minuti
GET /monitoring/workspace/{id}/task-analysis
```

### Indicatori di Salute

**Health Score**: 0-100 basato su:
- Tasso di completamento task
- Ratio fallimenti  
- Attività agenti
- Performance temporale

**Warning Signs:**
- `health_score < 60` - Problemi performance
- `runaway_detected: true` - Loop infiniti
- `excessive_handoffs: true` - Troppi passaggi
- `stuck_agents: [...]` - Agenti inattivi

### Log e Debug

**Executor Status:**
```http
GET /monitoring/executor/status
GET /monitoring/executor/detailed-stats
```

**Controllo Executor:**
```http
POST /monitoring/executor/pause
POST /monitoring/executor/resume
```