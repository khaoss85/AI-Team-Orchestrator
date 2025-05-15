from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional, Union, Literal
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum

class WorkspaceStatus(str, Enum):
    CREATED = "created"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"

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

class ModelType(str, Enum):
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_3_5_TURBO = "gpt-3.5-turbo"

class AgentSeniority(str, Enum):
    JUNIOR = "junior"
    SENIOR = "senior"
    EXPERT = "expert"

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

class AgentHealth(BaseModel):
    status: HealthStatus = HealthStatus.UNKNOWN
    last_update: Optional[datetime] = None
    details: Optional[Dict[str, Any]] = None

class AgentCreate(BaseModel):
    workspace_id: UUID
    name: str
    role: str
    seniority: AgentSeniority
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    llm_config: Optional[Dict[str, Any]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    can_create_tools: bool = False

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    seniority: Optional[AgentSeniority] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    status: Optional[AgentStatus] = None
    health: Optional[AgentHealth] = None
    llm_config: Optional[Dict[str, Any]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    can_create_tools: Optional[bool] = None

class Agent(BaseModel):
    id: UUID
    workspace_id: UUID
    name: str
    role: str
    seniority: AgentSeniority
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    status: AgentStatus
    health: AgentHealth
    llm_config: Optional[Dict[str, Any]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    can_create_tools: bool = False
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Modello per la proposta di Handoff (usa nomi di agenti)
class HandoffProposalCreate(BaseModel):
    # Usa Field per specificare gli alias per la deserializzazione da JSON
    # e per la serializzazione a JSON se model_dump(by_alias=True) è usato.
    source_agent_name: str = Field(..., alias="from")
    target_agent_names: Union[str, List[str]] = Field(..., alias="to")
    description: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True) # Permette di popolare usando sia il nome del campo che l'alias


# Modello per la creazione di Handoff nel DB (usa UUID)
class HandoffCreate(BaseModel):
    source_agent_id: UUID
    target_agent_id: UUID
    description: Optional[str] = None

class Handoff(BaseModel):
    id: UUID
    source_agent_id: UUID
    target_agent_id: UUID
    description: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class TaskCreate(BaseModel):
    workspace_id: UUID
    agent_id: UUID
    name: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING

class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    agent_id: Optional[UUID] = None
    status: Optional[TaskStatus] = None
    result: Optional[Dict[str, Any]] = None

class Task(BaseModel):
    id: UUID
    workspace_id: UUID
    agent_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

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
    completeness_score: int = Field(ge=0, le=100, description="How complete/comprehensive this deliverable is")

class ProjectOutput(BaseModel):
    task_id: str
    task_name: str
    output: str
    agent_name: str
    agent_role: str
    created_at: datetime
    type: str = "general"  # general, analysis, recommendation, document
    summary: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    key_insights: List[str] = Field(default_factory=list)
    metrics: Optional[Dict[str, Any]] = None
    visual_summary: Optional[str] = None
    category: Optional[str] = None
    
class ProjectDeliverables(BaseModel):
    workspace_id: str
    summary: str
    key_outputs: List[ProjectOutput]
    insight_cards: List[ProjectDeliverableCard] = Field(default_factory=list)
    final_recommendations: List[str]
    next_steps: List[str]
    completion_status: Literal["in_progress", "awaiting_review", "completed"]
    total_tasks: int
    completed_tasks: int
    generated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class DeliverableFeedback(BaseModel):
    feedback_type: Literal["approve", "request_changes", "general_feedback"]
    message: str
    specific_tasks: Optional[List[str]] = None
    priority: Literal["low", "medium", "high"] = "medium"
    
