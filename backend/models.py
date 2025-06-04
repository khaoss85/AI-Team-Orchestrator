# backend/models.py

from pydantic import BaseModel, Field as PydanticField, ConfigDict
from typing import List, Dict, Any, Optional, Union, Literal
from datetime import datetime
from uuid import UUID
from enum import Enum
import json
import warnings

# Suppress Pydantic JSON schema warnings globally per questo modulo
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic._internal._generate_schema")
# Silence Pydantic JSON schema warnings when building API docs
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic.json_schema")

# --- Enums ---
class WorkspaceStatus(str, Enum):
    CREATED = "created"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"
    NEEDS_INTERVENTION = "needs_intervention"

class AgentStatus(str, Enum):
    CREATED = "created"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    TERMINATED = "terminated"

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"
    TIMED_OUT = "timed_out"

class LogType(str, Enum):
    INFO = "info"
    ERROR = "error"
    WARNING = "warning"
    SYSTEM = "system"
    AGENT_OUTPUT = "agent_output"
    AGENT_INPUT = "agent_input"
    TOOL_CALL = "tool_call"
    HANDOFF = "handoff"

class HealthStatus(str, Enum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class AgentSeniority(str, Enum):
    JUNIOR = "junior"
    SENIOR = "senior"
    EXPERT = "expert"


# --- Workspace Models ---
class WorkspaceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    user_id: UUID
    goal: Optional[str] = None
    budget: Optional[Dict[str, Any]] = None

class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[WorkspaceStatus] = None
    goal: Optional[str] = None
    budget: Optional[Dict[str, Any]] = None

class Workspace(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    user_id: UUID
    status: WorkspaceStatus
    goal: Optional[str] = None
    budget: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Agent Models ---

class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"

class PersonalityTrait(str, Enum):
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    DETAIL_ORIENTED = "detail-oriented"
    PROACTIVE = "proactive"
    COLLABORATIVE = "collaborative"
    DECISIVE = "decisive"
    INNOVATIVE = "innovative"
    METHODICAL = "methodical"
    ADAPTABLE = "adaptable"
    DIPLOMATIC = "diplomatic"

class CommunicationStyle(str, Enum):
    FORMAL = "formal"
    CASUAL = "casual"
    TECHNICAL = "technical"
    CONCISE = "concise"
    DETAILED = "detailed"
    EMPATHETIC = "empathetic"
    ASSERTIVE = "assertive"

class Skill(BaseModel):
    name: str
    level: SkillLevel
    description: Optional[str] = None

    
class AgentHealth(BaseModel):
    status: HealthStatus = HealthStatus.UNKNOWN
    last_update: Optional[datetime] = None
    details: Optional[Dict[str, Any]] = None

class AgentCreate(BaseModel):
    workspace_id: UUID
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str
    seniority: AgentSeniority
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    llm_config: Optional[Dict[str, Any]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    can_create_tools: bool = False
    personality_traits: Optional[List[PersonalityTrait]] = None
    communication_style: Optional[CommunicationStyle] = None
    hard_skills: Optional[List[Skill]] = None
    soft_skills: Optional[List[Skill]] = None
    background_story: Optional[str] = None

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    seniority: Optional[AgentSeniority] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    status: Optional[AgentStatus] = None
    health: Optional[AgentHealth] = None
    llm_config: Optional[Dict[str, Any]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    can_create_tools: Optional[bool] = None
    personality_traits: Optional[List[PersonalityTrait]] = None
    communication_style: Optional[CommunicationStyle] = None
    hard_skills: Optional[List[Skill]] = None
    soft_skills: Optional[List[Skill]] = None
    background_story: Optional[str] = None

class Agent(BaseModel):
    id: UUID
    workspace_id: UUID
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str
    seniority: AgentSeniority
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    status: AgentStatus
    health: AgentHealth
    llm_config: Optional[Dict[str, Any]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    can_create_tools: bool = False
    personality_traits: Optional[List[PersonalityTrait]] = None
    communication_style: Optional[CommunicationStyle] = None
    hard_skills: Optional[List[Skill]] = None
    soft_skills: Optional[List[Skill]] = None
    background_story: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Handoff Models ---
class HandoffProposalCreate(BaseModel):
    source_agent_name: str = PydanticField(alias="from", description="Source agent name")
    target_agent_names: Union[str, List[str]] = PydanticField(alias="to", description="Target agent name(s)")
    description: Optional[str] = PydanticField(default="", description="Handoff description")

    model_config = ConfigDict(populate_by_name=True)

class HandoffCreate(BaseModel):
    source_agent_id: UUID
    target_agent_id: UUID
    description: Optional[str] = None

class Handoff(BaseModel):
    id: UUID
    source_agent_id: UUID
    target_agent_id: UUID
    workspace_id: UUID
    description: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Task Models ---
class TaskCreate(BaseModel):
    workspace_id: UUID
    agent_id: Optional[UUID] = None
    assigned_to_role: Optional[str] = PydanticField(None, description="Role targeted for this task")
    name: str = PydanticField(..., min_length=3, max_length=255)
    description: Optional[str] = PydanticField(None, max_length=8000)
    status: TaskStatus = TaskStatus.PENDING
    priority: Literal["low","medium","high"] = "medium"
    parent_task_id: Optional[UUID] = PydanticField(None, description="ID of parent task")
    depends_on_task_ids: Optional[List[UUID]] = PydanticField(None, description="Dependencies")
    estimated_effort_hours: Optional[float] = PydanticField(None, ge=0)
    deadline: Optional[datetime] = None
    context_data: Optional[Dict[str, Any]] = PydanticField(None, description="Arbitrary JSONB data")

class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    agent_id: Optional[UUID] = None
    assigned_to_role: Optional[str] = None
    status: Optional[TaskStatus] = None
    result: Optional[Dict[str, Any]] = None
    priority: Optional[Literal["low","medium","high"]] = None
    parent_task_id: Optional[UUID] = None
    depends_on_task_ids: Optional[List[UUID]] = None
    estimated_effort_hours: Optional[float] = None
    deadline: Optional[datetime] = None
    context_data: Optional[Dict[str, Any]] = None

class Task(BaseModel):
    id: UUID
    workspace_id: UUID
    agent_id: Optional[UUID] = None
    assigned_to_role: Optional[str] = None
    name: str
    description: Optional[str] = None
    status: TaskStatus
    priority: Literal["low","medium","high"] = "medium"
    parent_task_id: Optional[UUID] = None
    depends_on_task_ids: Optional[List[UUID]] = None
    estimated_effort_hours: Optional[float] = None
    deadline: Optional[datetime] = None
    context_data: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Log Models ---
class LogCreate(BaseModel):
    workspace_id: UUID
    agent_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    type: LogType
    content: Dict[str, Any]

class Log(BaseModel):
    id: UUID
    workspace_id: UUID
    agent_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    type: LogType
    content: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Document Models ---
class DocumentCreate(BaseModel):
    workspace_id: UUID
    agent_id: Optional[UUID] = None
    name: str
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class DocumentUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class Document(BaseModel):
    id: UUID
    workspace_id: UUID
    agent_id: Optional[UUID] = None
    name: str
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Director & Team Proposal ---
class DirectorConfig(BaseModel):
    workspace_id: UUID
    goal: str
    budget_constraint: Dict[str, Any]
    user_id: UUID
    user_feedback: Optional[str] = None

class DirectorTeamProposal(BaseModel):
    workspace_id: UUID
    agents: List[AgentCreate]
    handoffs: List[HandoffProposalCreate]
    estimated_cost: Dict[str, Any]
    rationale: str
    user_feedback: Optional[str] = None

class TeamProposalData(BaseModel):
    id: Optional[UUID] = None
    workspace_id: UUID
    proposal_data: DirectorTeamProposal
    status: str = "pending"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class DirectorTeamProposalResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    agents: List[AgentCreate]
    handoffs: List[HandoffProposalCreate]
    estimated_cost: Dict[str, Any]
    rationale: str
    user_feedback: Optional[str] = None
    created_at: Optional[datetime] = None
    status: str = "pending"

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# --- Tool Outputs ---
class TaskExecutionOutput(BaseModel):
    task_id: str = PydanticField(description="ID of the task")  
    status: Literal["completed", "failed", "requires_handoff"] = PydanticField(default="completed", description="Task completion status")
    summary: str = PydanticField(description="Summary of work performed")  
    detailed_results_json: Optional[str] = PydanticField(default="", description="Detailed structured results as JSON string")
    next_steps: Optional[List[str]] = PydanticField(default_factory=list, description="Suggested next actions")
    suggested_handoff_target_role: Optional[str] = PydanticField(default="", description="Role to hand off to if required")
    resources_consumed_json: Optional[str] = PydanticField(default="", description="Resource usage as JSON string")
    
    model_config = ConfigDict(extra="forbid")

class PMToolCreateSubTaskResponse(BaseModel):
    success: bool
    task_id: Optional[str] = None
    assigned_agent_id: Optional[str] = None
    assigned_agent_name: Optional[str] = None
    message: str
    error: Optional[str] = None
    suggestion: Optional[str] = None


# --- Deliverables Models ---
class ProjectDeliverableCard(BaseModel):
    """User-friendly card representation of project deliverables"""
    id: str
    title: str
    description: str
    category: str
    icon: str
    key_insights: List[str]
    metrics: Optional[Dict[str, Any]] = None
    created_by: str
    created_at: datetime
    completeness_score: int = PydanticField(..., ge=0, le=100, description="How complete this deliverable is")

class ProjectOutput(BaseModel):
    task_id: str
    task_name: str
    output: str
    agent_name: str
    agent_role: str
    created_at: datetime
    type: str = "general"
    summary: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    key_insights: List[str] = PydanticField(default_factory=list)
    metrics: Optional[Dict[str, Any]] = None
    visual_summary: Optional[str] = None
    category: Optional[str] = None

class ProjectDeliverables(BaseModel):
    workspace_id: str
    summary: str
    key_outputs: List[ProjectOutput]
    insight_cards: List[ProjectDeliverableCard] = PydanticField(default_factory=list)
    final_recommendations: List[str]
    next_steps: List[str]
    completion_status: Literal["in_progress","awaiting_review","completed"]
    total_tasks: int
    completed_tasks: int
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DeliverableFeedback(BaseModel):
    feedback_type: Literal["approve","request_changes","general_feedback"]
    message: str
    specific_tasks: Optional[List[str]] = None
    priority: Literal["low","medium","high"] = "medium"
    
class ProjectPhase(str, Enum):
    ANALYSIS = "ANALYSIS"
    IMPLEMENTATION = "IMPLEMENTATION" 
    FINALIZATION = "FINALIZATION"
    COMPLETED = "COMPLETED"

PHASE_SEQUENCE = [
    ProjectPhase.ANALYSIS,
    ProjectPhase.IMPLEMENTATION,
    ProjectPhase.FINALIZATION,
    ProjectPhase.COMPLETED
]

PHASE_DESCRIPTIONS = {
    ProjectPhase.ANALYSIS: "Research, competitor analysis, audience profiling, market research",
    ProjectPhase.IMPLEMENTATION: "Strategy development, planning, frameworks, templates, workflows",
    ProjectPhase.FINALIZATION: "Content creation, publishing, execution, final deliverables"
}
# === DYNAMIC DELIVERABLE SYSTEM MODELS ===

class AssetRequirement(BaseModel):
    """Requisito per un asset azionabile"""
    asset_type: str = PydanticField(..., description="Tipo di asset (es. contact_database, content_calendar)")
    asset_format: str = PydanticField(..., description="Formato dell'asset (structured_data, document, spreadsheet)")
    actionability_level: str = PydanticField(..., description="Livello di azionabilità (ready_to_use, needs_customization, template)")
    business_impact: str = PydanticField(..., description="Impatto business (immediate, short_term, strategic)")
    priority: int = PydanticField(default=1, description="Priorità dell'asset (1=alta, 5=bassa)")
    validation_criteria: List[str] = PydanticField(default_factory=list, description="Criteri di validazione")

class DeliverableRequirements(BaseModel):
    """Requirements dinamici per un deliverable"""
    workspace_id: str
    deliverable_category: str = PydanticField(..., description="Categoria principale (marketing, finance, sports, etc.)")
    primary_assets_needed: List[AssetRequirement]
    deliverable_structure: Dict[str, Any] = PydanticField(..., description="Struttura del deliverable finale")
    generated_at: datetime = PydanticField(default_factory=datetime.now)
    
    model_config = ConfigDict(from_attributes=True)

class AssetSchema(BaseModel):
    """Schema dinamico per un asset"""
    asset_name: str
    schema_definition: Dict[str, Any] = PydanticField(..., description="Schema JSON per l'asset")
    validation_rules: List[str] = PydanticField(default_factory=list)
    usage_instructions: str = PydanticField(default="", description="Istruzioni per l'uso")
    automation_ready: bool = PydanticField(default=False)
    
    model_config = ConfigDict(from_attributes=True)

class ExtractedAsset(BaseModel):
    """Asset estratto da un task"""
    asset_name: str
    asset_data: Dict[str, Any]
    source_task_id: str
    extraction_method: str = PydanticField(..., description="Metodo di estrazione utilizzato")
    validation_score: float = PydanticField(default=0.0, ge=0.0, le=1.0)
    actionability_score: float = PydanticField(default=0.0, ge=0.0, le=1.0)
    ready_to_use: bool = PydanticField(default=False)
    
    model_config = ConfigDict(from_attributes=True)

class ActionableDeliverable(BaseModel):
    """Deliverable finale con asset azionabili"""
    workspace_id: str
    deliverable_id: str
    meta: Dict[str, Any] = PydanticField(..., description="Metadati del deliverable")
    executive_summary: str
    actionable_assets: Dict[str, ExtractedAsset]
    usage_guide: Dict[str, str] = PydanticField(default_factory=dict)
    next_steps: List[str] = PydanticField(default_factory=list)
    automation_ready: bool = PydanticField(default=False)
    actionability_score: int = PydanticField(default=0, ge=0, le=100)
    created_at: datetime = PydanticField(default_factory=datetime.now)
    
    model_config = ConfigDict(from_attributes=True)

# === ENHANCED TASK OUTPUT FOR ASSETS ===

class AssetTaskExecutionOutput(TaskExecutionOutput):
    """Extended TaskExecutionOutput per task di produzione asset"""
    asset_type: Optional[str] = PydanticField(default=None, description="Tipo di asset prodotto")
    asset_schema_validation: Optional[bool] = PydanticField(default=None, description="Se l'asset rispetta lo schema")
    automation_instructions: Optional[str] = PydanticField(default=None, description="Istruzioni per automazione")
    usage_notes: Optional[str] = PydanticField(default=None, description="Note per l'utilizzo")

class AssetProductionContext(BaseModel):
    """Context data per task di produzione asset"""
    asset_production: bool = PydanticField(default=True)
    target_schema: str = PydanticField(..., description="Nome dello schema target")
    asset_type: str = PydanticField(..., description="Tipo di asset da produrre")
    quality_requirements: List[str] = PydanticField(default_factory=list)
    automation_requirements: List[str] = PydanticField(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)