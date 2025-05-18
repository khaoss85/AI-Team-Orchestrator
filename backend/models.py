# backend/models.py

from pydantic import BaseModel, Field as PydanticField, ConfigDict
from typing import List, Dict, Any, Optional, Union, Literal
from datetime import datetime
from uuid import UUID
from enum import Enum
import json

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
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    personality_traits: Optional[List[PersonalityTrait]] = None
    communication_style: Optional[str] = None
    hard_skills: Optional[List[Skill]] = None
    soft_skills: Optional[List[Skill]] = None
    background_story: Optional[str] = None

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
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    personality_traits: Optional[List[PersonalityTrait]] = None
    communication_style: Optional[str] = None
    hard_skills: Optional[List[Skill]] = None
    soft_skills: Optional[List[Skill]] = None
    background_story: Optional[str] = None

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
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    personality_traits: Optional[List[PersonalityTrait]] = None
    communication_style: Optional[str] = None
    hard_skills: Optional[List[Skill]] = None
    soft_skills: Optional[List[Skill]] = None
    background_story: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# --- Handoff Models ---
class HandoffProposalCreate(BaseModel):
    source_agent_name: str = PydanticField(..., alias="from")
    target_agent_names: Union[str, List[str]] = PydanticField(..., alias="to")
    description: Optional[str] = None

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
    task_id: str
    status: Literal["completed","failed","requires_handoff"] = "completed"
    summary: str
    detailed_results_json: Optional[str] = PydanticField(None, description="JSON string of detailed results")
    next_steps: Optional[List[str]] = PydanticField(None, description="Follow-up actions")
    suggested_handoff_target_role: Optional[str] = PydanticField(None, description="Role for handoff")
    resources_consumed_json: Optional[str] = PydanticField(None, description="Usage metrics JSON")

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

class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class PersonalityTrait(str, Enum):
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    COLLABORATIVE = "collaborative"
    DETAIL_ORIENTED = "detail_oriented"
    EMPATHETIC = "empathetic"
    PROACTIVE = "proactive"
    DIRECT = "direct"
    DIPLOMATIC = "diplomatic"
    OPTIMISTIC = "optimistic"
    CAUTIOUS = "cautious"

class Skill(BaseModel):
    name: str
    level: SkillLevel
    description: Optional[str] = None
