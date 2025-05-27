# AI Team Orchestrator - Documentazione API Frontend

## 📋 Indice

1. [Overview del Sistema](#overview-del-sistema)
2. [Architettura API](#architettura-api)
3. [Endpoint Reference](#endpoint-reference)
4. [🆕 Asset Management](#asset-management)
5. [Modelli di Dati](#modelli-di-dati)
6. [Flussi di Lavoro](#flussi-di-lavoro)
7. [Stati e Transizioni](#stati-e-transizioni)
8. [Monitoring e Debugging](#monitoring-e-debugging)
9. [Esempi Pratici](#esempi-pratici)

---

## 🎯 Overview del Sistema

**AI Team Orchestrator** è una piattaforma che permette di creare e gestire team di agenti AI che collaborano su progetti complessi. Il sistema gestisce:

- **Workspace**: Progetti contenenti team di agenti
- **Agenti AI**: Specialisti con ruoli specifici (PM, Analyst, Content Creator, etc.)
- **Task**: Attività assegnate agli agenti con esecuzione automatica
- **Handoffs**: Passaggi di lavoro tra agenti
- **🆕 Asset Production**: Task specifici per produrre asset azionabili
- **🆕 Deliverable Intelligence**: Analisi dinamica dei requisiti deliverable
- **Deliverable**: Output finali aggregati del progetto

### Caratteristiche Principali

✅ **Anti-Loop Protection**: Prevenzione di loop infiniti nei task  
✅ **Budget Tracking**: Monitoraggio costi token/LLM  
✅ **Phase Management**: Gestione fasi progetto (Analysis → Implementation → Finalization)  
✅ **Human Feedback**: Sistema di approvazione manuale  
✅ **Real-time Monitoring**: Dashboard per monitoraggio in tempo reale  
✅ **🆕 Asset-Oriented Workflow**: Produzione automatica di asset business-ready  
✅ **🆕 Dynamic Requirements Analysis**: Analisi intelligente dei requisiti deliverable  
✅ **🆕 Schema-Driven Validation**: Validazione asset contro schemi dinamici  

---

## 🏗️ Architettura API

### Base URL
```
http://localhost:8000
```

### Struttura Router
```
/workspaces         # Gestione progetti
/agents             # Gestione agenti AI
/director           # Creazione team automatica
/tools              # Tool personalizzati
/monitoring         # Monitoraggio sistema
/human-feedback     # Approvazioni manuali
/projects           # Insights e deliverable
/delegation         # Analisi delegazione
/asset-management   # 🆕 Gestione asset e schemi
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

#### 🆕 Asset Tracking
```http
GET /monitoring/workspace/{workspace_id}/asset-tracking
```

**Response:**
```json
{
  "workspace_id": "uuid",
  "asset_summary": {
    "total_asset_tasks": 5,
    "completed_asset_tasks": 3,
    "pending_asset_tasks": 2,
    "completion_rate": 60.0,
    "deliverable_ready": false
  },
  "asset_types_breakdown": {
    "content_calendar": {"total": 1, "completed": 1},
    "contact_database": {"total": 1, "completed": 1},
    "training_program": {"total": 1, "completed": 0}
  },
  "completed_assets": [
    {
      "task_id": "uuid",
      "task_name": "PRODUCE ASSET: Instagram Content Calendar",
      "asset_type": "content_calendar",
      "status": "completed",
      "agent_role": "Content Specialist"
    }
  ],
  "pending_assets": [
    {
      "task_id": "uuid",
      "task_name": "PRODUCE ASSET: Lead Contact Database",
      "asset_type": "contact_database",
      "status": "pending",
      "agent_role": "Data Analyst"
    }
  ]
}
```

#### 🆕 Deliverable Readiness
```http
GET /monitoring/workspace/{workspace_id}/deliverable-readiness
```

**Response:**
```json
{
  "workspace_id": "uuid",
  "is_ready_for_deliverable": true,
  "has_existing_deliverable": false,
  "readiness_details": {
    "total_tasks": 20,
    "completed_tasks": 15,
    "pending_tasks": 5,
    "completion_rate": 0.75,
    "asset_tasks": 5,
    "completed_assets": 4,
    "asset_completion_rate": 0.8
  },
  "next_action": "create_deliverable",
  "checked_at": "2024-01-20T16:00:00Z"
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

#### Analisi Task (Enhanced)
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

#### 🆕 Asset Insights
```http
GET /projects/{workspace_id}/asset-insights
```

**Response:**
```json
{
  "workspace_id": "uuid",
  "deliverable_category": "marketing",
  "requirements_analysis": {
    "total_assets_needed": 3,
    "required_asset_types": ["content_calendar", "audience_analysis", "contact_database"],
    "asset_coverage_rate": 66.7,
    "covered_assets": ["content_calendar", "contact_database"],
    "missing_assets": ["audience_analysis"]
  },
  "asset_schemas_available": {
    "content_calendar": {
      "automation_ready": true,
      "validation_rules_count": 3,
      "main_fields": ["posts", "posting_schedule", "performance_targets"]
    }
  },
  "current_asset_tasks": [
    {
      "task_id": "uuid",
      "name": "Create Instagram Content Calendar",
      "status": "completed",
      "asset_type": "content_calendar",
      "agent_role": "Content Specialist"
    }
  ],
  "recommendations": [
    "Create audience_analysis production task"
  ]
}
```

#### 🆕 Trigger Asset Analysis
```http
POST /projects/{workspace_id}/trigger-asset-analysis
```

**Response:**
```json
{
  "success": true,
  "message": "Asset requirements analysis completed",
  "workspace_id": "uuid",
  "analysis_results": {
    "deliverable_category": "marketing",
    "assets_needed": 3,
    "asset_types": ["content_calendar", "audience_analysis", "contact_database"]
  },
  "triggered_at": "2024-01-20T16:30:00Z"
}
```

#### Deliverable Progetto (Enhanced)
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
      "task_name": "🎯 FINAL ASSET-READY DELIVERABLE",
      "output": "Executive Summary: Comprehensive Instagram marketing strategy with 3 actionable business assets ready for immediate implementation...",
      "agent_name": "Content Strategist",
      "agent_role": "Content Strategy Specialist",
      "type": "final_deliverable",
      "created_at": "2024-01-20T15:00:00Z",
      "title": "Final Asset-Ready Deliverable",
      "key_insights": [
        "Content calendar with 30 days of posts ready for scheduling",
        "Qualified contact database with 150+ leads",
        "Audience analysis report with actionable insights"
      ],
      "metrics": {
        "actionability_score": 95,
        "automation_ready": true,
        "assets_included": 3
      }
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
    "Implement content calendar using provided schedule",
    "Begin outreach to qualified leads in contact database",
    "Use audience insights for targeted content creation"
  ],
  "next_steps": [
    "IMMEDIATE (Week 1): Upload content calendar to scheduling tool",
    "SHORT-TERM (Week 2-3): Import contact database to CRM",
    "ONGOING (Month 1+): Monitor performance metrics and optimize"
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

## 🆕 Asset Management

### Asset Requirements Analysis

#### Get Asset Requirements
```http
GET /asset-management/workspace/{workspace_id}/requirements
```

**Response:**
```json
{
  "workspace_id": "uuid",
  "deliverable_category": "marketing",
  "primary_assets_needed": [
    {
      "asset_type": "content_calendar",
      "asset_format": "structured_data",
      "actionability_level": "ready_to_use",
      "business_impact": "immediate",
      "priority": 1,
      "validation_criteria": ["posts_with_dates", "complete_captions", "hashtags_included"]
    },
    {
      "asset_type": "qualified_contact_database",
      "asset_format": "structured_data", 
      "actionability_level": "ready_to_use",
      "business_impact": "immediate",
      "priority": 1,
      "validation_criteria": ["contact_info_complete", "qualification_scores", "next_actions"]
    }
  ],
  "deliverable_structure": {
    "executive_summary": "required",
    "actionable_assets": {
      "content_calendar": {"asset_type": "content_calendar"},
      "qualified_contact_database": {"asset_type": "qualified_contact_database"}
    },
    "usage_guide": "required",
    "automation_instructions": "optional"
  },
  "generated_at": "2024-01-20T16:00:00Z"
}
```

### Asset Schemas

#### Get Asset Schemas
```http
GET /asset-management/workspace/{workspace_id}/schemas
```

**Response:**
```json
{
  "workspace_id": "uuid",
  "available_schemas": {
    "content_calendar": {
      "asset_name": "content_calendar",
      "schema_definition": {
        "posts": [
          {
            "date": "YYYY-MM-DD",
            "time": "HH:MM",
            "platform": "instagram|facebook|linkedin|twitter",
            "content_type": "image|video|carousel|story",
            "caption": "string",
            "hashtags": ["string"],
            "visual_description": "string",
            "call_to_action": "string"
          }
        ],
        "posting_schedule": {
          "frequency": "daily|weekly|biweekly",
          "optimal_times": ["HH:MM"],
          "content_mix": {
            "educational": "percentage",
            "promotional": "percentage"
          }
        }
      },
      "validation_rules": ["posts_with_dates", "complete_captions"],
      "usage_instructions": "Import into your content management tool and schedule posts according to the recommended timeline.",
      "automation_ready": true
    }
  },
  "schema_count": 2,
  "generated_at": "2024-01-20T16:00:00Z"
}
```

### Asset Extraction Status

#### Get Extraction Status
```http
GET /asset-management/workspace/{workspace_id}/extraction-status
```

**Response:**
```json
{
  "workspace_id": "uuid",
  "extraction_summary": {
    "total_completed_tasks": 18,
    "asset_production_tasks": 5,
    "extraction_ready_tasks": 4,
    "extraction_readiness_rate": 80.0
  },
  "extraction_candidates": [
    {
      "task_id": "uuid",
      "task_name": "PRODUCE ASSET: Instagram Content Calendar",
      "asset_type": "content_calendar",
      "has_structured_output": true,
      "output_size": 2540,
      "extraction_ready": true,
      "completed_at": "2024-01-20T14:30:00Z"
    }
  ],
  "next_steps": [
    "Run asset extraction on ready tasks",
    "Create final deliverable with extracted assets"
  ],
  "analyzed_at": "2024-01-20T16:00:00Z"
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

### Task (Enhanced)
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
  context_data?: {
    // 🆕 Asset-oriented fields
    asset_production?: boolean;
    asset_oriented_task?: boolean;
    asset_type?: string;
    detected_asset_type?: string;
    project_phase?: "ANALYSIS" | "IMPLEMENTATION" | "FINALIZATION";
    // Other context data...
    [key: string]: any;
  };
  result?: any;
  created_at: string;
  updated_at: string;
}
```

### 🆕 Asset Requirements
```typescript
interface AssetRequirement {
  asset_type: string;
  asset_format: "structured_data" | "document" | "spreadsheet";
  actionability_level: "ready_to_use" | "needs_customization" | "template";
  business_impact: "immediate" | "short_term" | "strategic";
  priority: number;
  validation_criteria: string[];
}

interface DeliverableRequirements {
  workspace_id: string;
  deliverable_category: string;
  primary_assets_needed: AssetRequirement[];
  deliverable_structure: {
    executive_summary: string;
    actionable_assets: Record<string, AssetRequirement>;
    usage_guide: string;
    automation_instructions?: string;
  };
  generated_at: string;
}
```

### 🆕 Asset Schema
```typescript
interface AssetSchema {
  asset_name: string;
  schema_definition: Record<string, any>;
  validation_rules: string[];
  usage_instructions: string;
  automation_ready: boolean;
}
```

### 🆕 Asset Tracking
```typescript
interface AssetTrackingData {
  workspace_id: string;
  asset_summary: {
    total_asset_tasks: number;
    completed_asset_tasks: number;
    pending_asset_tasks: number;
    completion_rate: number;
    deliverable_ready: boolean;
  };
  asset_types_breakdown: Record<string, {
    total: number;
    completed: number;
  }>;
  completed_assets: AssetTaskInfo[];
  pending_assets: AssetTaskInfo[];
}

interface AssetTaskInfo {
  task_id: string;
  task_name: string;
  asset_type?: string;
  status: string;
  agent_role?: string;
  created_at?: string;
  updated_at?: string;
}
```

### Task Execution Result (Enhanced)
```typescript
interface TaskExecutionResult {
  task_id: string;
  status: "completed" | "failed" | "requires_handoff";
  summary: string;
  detailed_results_json?: string; // 🆕 Can contain structured asset data
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
  // 🆕 Asset-specific fields
  asset_validation_score?: number;
  actionability_score?: number;
  automation_ready?: boolean;
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

### 2. 🆕 Workflow Asset-Oriented

```mermaid
graph TD
    A[Progetto Attivo] --> B[Analisi Requirements]
    B --> C[Generazione Schemi Asset]
    C --> D[Creazione Task Asset]
    D --> E[Produzione Asset]
    E --> F[Validazione Asset]
    F --> G[Estrazione Asset]
    G --> H[Aggregazione Deliverable]
    H --> I[Deliverable Finale]
```

**Sequenza API Asset-Oriented:**
1. `GET /asset-management/workspace/{id}/requirements` - Analizza requirements
2. `GET /asset-management/workspace/{id}/schemas` - Ottieni schemi
3. `POST /agents/{workspace_id}/tasks` - Crea asset production task
4. `GET /monitoring/workspace/{id}/asset-tracking` - Monitora progresso
5. `GET /asset-management/workspace/{id}/extraction-status` - Status estrazione
6. `GET /projects/{id}/deliverables` - Deliverable finale con asset

### 3. Monitoraggio Progetto (Enhanced)

```mermaid
graph TD
    A[Dashboard] --> B[Status Workspace]
    A --> C[Analisi Task]
    A --> D[Budget Tracking]
    A --> E[Insights Progetto]
    A --> F[🆕 Asset Tracking]
    A --> G[🆕 Deliverable Readiness]
    B --> H[Azioni Correttive]
    C --> H
    D --> H
    E --> I[Deliverable Ready]
    F --> I
    G --> I
```

**Endpoint Chiave:**
- `GET /monitoring/workspace/{id}/status` - Status generale
- `GET /monitoring/workspace/{id}/task-analysis` - Analisi dettagliata
- `GET /monitoring/workspace/{id}/budget` - Monitoraggio costi
- `GET /projects/{id}/insights` - Insights avanzati
- `GET /monitoring/workspace/{id}/asset-tracking` - 🆕 Tracking asset
- `GET /monitoring/workspace/{id}/deliverable-readiness` - 🆕 Readiness deliverable

### 4. Gestione Fasi Progetto (Enhanced)

Il sistema gestisce automaticamente 3 fasi con **asset intelligence**:

1. **ANALYSIS** - Ricerca, analisi competitor, audience
2. **IMPLEMENTATION** - Strategia, framework, pianificazione  
3. **FINALIZATION** - 🆕 **Asset production**, deliverable finali

**Endpoint Monitoraggio Fasi:**
```http
GET /monitoring/workspace/{workspace_id}/finalization-status
```

**Response (Enhanced):**
```json
{
  "finalization_phase_active": true,
  "finalization_tasks_completed": 2,
  "final_deliverables_completed": 1,
  "project_completion_percentage": 85,
  "next_action_needed": "COMPLETE_DELIVERABLES",
  "asset_production_status": {
    "asset_tasks_in_finalization": 3,
    "completed_asset_tasks": 2,
    "asset_completion_rate": 66.7
  }
}
```

---

## 🚦 Stati e Transizioni

### Stati Workspace
- **created** → **active** (quando viene avviato il team)
- **active** → **paused** (pausa manuale)
- **active** → **completed** (progetto finito con deliverable)
- **active** → **needs_intervention** (problemi rilevati)

### Stati Task (Enhanced)
- **pending** → **in_progress** → **completed**
- **pending** → **in_progress** → **failed**
- **pending** → **canceled**
- **🆕 Asset Production States:**
  - **asset_production: true** (task marcato per asset)
  - **asset_type: "content_calendar"** (tipo asset da produrre)
  - **project_phase: "FINALIZATION"** (fase di produzione asset)

### Stati Agent
- **created** → **active** → **paused**/**terminated**

### 🆕 Asset States
- **Requirements**: **analyzed** → **schemas_generated** → **tasks_created**
- **Asset Tasks**: **pending** → **producing** → **validating** → **extracted**
- **Deliverable**: **not_ready** → **ready** → **creating** → **completed**

### Gestione Errori (Enhanced)

**Runaway Detection**: Il sistema rileva automaticamente loop infiniti
```http
GET /monitoring/runaway-protection/status
POST /monitoring/workspace/{id}/reset-runaway
```

**Task Reset**: Ripristina task falliti
```http
POST /monitoring/tasks/{task_id}/reset
```

**🆕 Asset Validation**: Verifica qualità asset
```http
GET /asset-management/workspace/{id}/extraction-status
```

---

## 🔍 Monitoring e Debugging

### Dashboard Real-time (Enhanced)

**Endpoint Chiave per Dashboard:**
```javascript
// Status generale ogni 5 secondi
GET /monitoring/workspace/{id}/status

// 🆕 Asset tracking ogni 10 secondi
GET /monitoring/workspace/{id}/asset-tracking

// Attività recente ogni 10 secondi  
GET /monitoring/workspace/{id}/activity?limit=20

// Budget ogni 30 secondi
GET /monitoring/workspace/{id}/budget

// 🆕 Deliverable readiness ogni 30 secondi
GET /monitoring/workspace/{id}/deliverable-readiness

// Analisi completa ogni 2 minuti
GET /monitoring/workspace/{id}/task-analysis

// 🆕 Asset insights ogni 5 minuti
GET /projects/{id}/asset-insights
```

### Indicatori di Salute (Enhanced)

**Health Score**: 0-100 basato su:
- Tasso di completamento task
- Ratio fallimenti  
- Attività agenti
- Performance temporale
- 🆕 **Asset completion rate**
- 🆕 **Deliverable readiness score**

**Warning Signs:**
- `health_score < 60` - Problemi performance
- `runaway_detected: true` - Loop infiniti
- `excessive_handoffs: true` - Troppi passaggi
- `stuck_agents: [...]` - Agenti inattivi
- 🆕 `asset_completion_rate < 0.5` - Asset production lenta
- 🆕 `deliverable_ready: false` - Deliverable non pronto

### Log e Debug (Enhanced)

**Executor Status:**
```http
GET /monitoring/executor/status
GET /monitoring/executor/detailed-stats  # 🆕 Include asset metrics
```

**Controllo Executor:**
```http
POST /monitoring/executor/pause
POST /monitoring/executor/resume
```

**🆕 Asset Debugging:**
```http
# Trigger manual asset analysis
POST /projects/{workspace_id}/trigger-asset-analysis

# Check asset extraction readiness
GET /asset-management/workspace/{id}/extraction-status

# View asset schemas for debugging
GET /asset-management/workspace/{id}/schemas
```

---

## 📊 Esempi Pratici

### Esempio Dashboard Component (React)

```typescript
import React, { useState, useEffect } from 'react';

interface DashboardData {
  status: any;
  assetTracking: any;
  deliverableReadiness: any;
  budget: any;
}

export const WorkspaceDashboard: React.FC<{workspaceId: string}> = ({ workspaceId }) => {
  const [data, setData] = useState<DashboardData>();
  
  useEffect(() => {
    const fetchData = async () => {
      const [status, assets, readiness, budget] = await Promise.all([
        fetch(`/monitoring/workspace/${workspaceId}/status`).then(r => r.json()),
        fetch(`/monitoring/workspace/${workspaceId}/asset-tracking`).then(r => r.json()),
        fetch(`/monitoring/workspace/${workspaceId}/deliverable-readiness`).then(r => r.json()),
        fetch(`/monitoring/workspace/${workspaceId}/budget`).then(r => r.json())
      ]);
      
      setData({
        status,
        assetTracking: assets,
        deliverableReadiness: readiness,
        budget
      });
    };
    
    fetchData();
    const interval = setInterval(fetchData, 10000); // Update every 10s
    
    return () => clearInterval(interval);
  }, [workspaceId]);

  if (!data) return <div>Loading...</div>;

  return (
    <div className="dashboard">
      {/* Status Overview */}
      <div className="status-card">
        <h3>Project Status</h3>
        <p>Phase: {data.status.current_state?.phase}</p>
        <p>Progress: {data.status.overview?.progress_percentage}%</p>
        <p>Health Score: {data.status.overview?.health_score}/100</p>
      </div>

      {/* 🆕 Asset Tracking */}
      <div className="asset-card">
        <h3>Asset Production</h3>
        <p>Completed Assets: {data.assetTracking.asset_summary?.completed_asset_tasks}</p>
        <p>Pending Assets: {data.assetTracking.asset_summary?.pending_asset_tasks}</p>
        <p>Completion Rate: {data.assetTracking.asset_summary?.completion_rate}%</p>
        {data.assetTracking.asset_summary?.deliverable_ready && (
          <div className="ready-indicator">✅ Deliverable Ready!</div>
        )}
      </div>

      {/* 🆕 Deliverable Readiness */}
      <div className="readiness-card">
        <h3>Deliverable Status</h3>
        <p>Ready: {data.deliverableReadiness.is_ready_for_deliverable ? 'Yes' : 'No'}</p>
        <p>Next Action: {data.deliverableReadiness.next_action}</p>
        {data.deliverableReadiness.next_action === 'create_deliverable' && (
          <button onClick={() => createDeliverable(workspaceId)}>
            Create Final Deliverable
          </button>
        )}
      </div>

      {/* Budget */}
      <div className="budget-card">
        <h3>Budget</h3>
        <p>Used: ${data.budget.total_cost}</p>
        <p>Limit: ${data.budget.budget_limit}</p>
        <p>Usage: {data.budget.budget_percentage}%</p>
      </div>
    </div>
  );
};

const createDeliverable = async (workspaceId: string) => {
  // This would trigger the deliverable creation process
  const response = await fetch(`/projects/${workspaceId}/deliverables`, {
    method: 'POST'
  });
  console.log('Deliverable creation triggered');
};
```

Questo README aggiornato ora include tutte le nuove funzionalità asset-oriented mantenendo la struttura e lo stile originale, fornendo una documentazione completa per il frontend delle nuove capabilities del sistema.