# backend/models.py

from pydantic import BaseModel, Field as PydanticField, ConfigDict

# Compatibility for Pydantic v1
if not hasattr(BaseModel, "model_validate"):
    @classmethod
    def _model_validate(cls, data):
        return cls.parse_obj(data)

    BaseModel.model_validate = _model_validate  # type: ignore
from typing import List, Dict, Any, Optional, Union, Literal
from datetime import datetime
from uuid import UUID, uuid4
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
    PROCESSING_TASKS = "processing_tasks"  # 🔧 FIX: Add status for task generation lock

class AgentStatus(str, Enum):
    CREATED = "created"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    AVAILABLE = "available"  # 🔧 FIX: Add missing status that exists in database
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
    STALE = "stale"

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
    INTERMEDIATE = "intermediate"  # Added for flexible team composition
    SENIOR = "senior"
    EXPERT = "expert"

class GoalStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"        # Goal is blocked by dependencies or issues
    FAILED = "failed"          # Goal has failed and needs intervention
    NEEDS_ATTENTION = "needs_attention"  # Goal requires manual review
    COMPLETED_PENDING_REVIEW = "completed_pending_review" # 🔧 FIX: Add missing status for human review

# 🌍 UNIVERSAL METRIC TYPES: No hardcoded business enums - AI-driven classification only
# All metric types are now free-form strings classified by AI for true universality


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
    ADVANCED = "advanced"
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
    iteration_count: int = 0
    max_iterations: Optional[int] = None
    dependency_map: Optional[Dict[str, List[str]]] = None
    
    # 🎯 Goal-driven task fields (Step 2: Goal-Driven Task Planner)
    goal_id: Optional[UUID] = PydanticField(None, description="Associated workspace goal")
    metric_type: Optional[str] = PydanticField(None, description="Goal metric this task contributes to")
    contribution_expected: Optional[float] = PydanticField(None, description="Expected numerical contribution to goal")
    numerical_target: Optional[Dict[str, Any]] = PydanticField(None, description="Specific numerical validation criteria")
    is_corrective: bool = PydanticField(False, description="Whether this is a corrective task for goal gap")
    success_criteria: Optional[List[str]] = PydanticField(None, description="Specific success criteria for goal achievement")

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
    iteration_count: Optional[int] = None
    max_iterations: Optional[int] = None
    dependency_map: Optional[Dict[str, List[str]]] = None
    
    # Goal-driven task fields
    goal_id: Optional[UUID] = None
    metric_type: Optional[str] = None
    contribution_expected: Optional[float] = None
    numerical_target: Optional[Dict[str, Any]] = None
    is_corrective: Optional[bool] = None
    success_criteria: Optional[List[str]] = None

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
    iteration_count: int = 0
    max_iterations: Optional[int] = None
    dependency_map: Optional[Dict[str, List[str]]] = None
    result: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    # Goal-driven task fields
    goal_id: Optional[UUID] = None
    metric_type: Optional[str] = None
    contribution_expected: Optional[float] = None
    numerical_target: Optional[Dict[str, Any]] = None
    is_corrective: bool = False
    success_criteria: Optional[List[str]] = None
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
    extracted_goals: Optional[List[Dict[str, Any]]] = None  # User-confirmed goals from frontend

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
    status: Literal["completed", "failed", "requires_handoff", "in_progress"] = PydanticField(default="completed", description="Task completion status")
    summary: str = PydanticField(max_length=2000, description="Summary of work performed")  
    detailed_results_json: Optional[str] = PydanticField(default="", max_length=100000, description="Detailed structured results as JSON string (max 100KB)")
    next_steps: Optional[List[str]] = PydanticField(default_factory=list, description="Suggested next actions")
    suggested_handoff_target_role: Optional[str] = PydanticField(default="", description="Role to hand off to if required")
    resources_consumed_json: Optional[str] = PydanticField(default="", max_length=5000, description="Resource usage as JSON string")
    
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
    execution_time_seconds: Optional[float] = None
    cost_estimated: Optional[float] = None
    tokens_used: Optional[Dict[str, int]] = None
    model_used: Optional[str] = None
    rationale: Optional[str] = None
    structured_content: Optional[Dict[str, Any]] = None  # For rich markup content

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

# --- Workspace Goals Models (Step 1: Goal Decomposition) ---
class WorkspaceGoalCreate(BaseModel):
    workspace_id: UUID
    metric_type: str  # 🌍 UNIVERSAL: Now accepts any string for agnostic goal types
    target_value: float = PydanticField(..., gt=0, description="Numerical target to achieve")
    unit: str = ""
    description: Optional[str] = None
    source_goal_text: Optional[str] = None
    priority: int = PydanticField(default=1, ge=1, le=5)
    success_criteria: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    validation_frequency_minutes: int = 20

class WorkspaceGoalUpdate(BaseModel):
    current_value: Optional[float] = None
    target_value: Optional[float] = None
    status: Optional[GoalStatus] = None
    priority: Optional[int] = PydanticField(None, ge=1, le=5)
    success_criteria: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    validation_frequency_minutes: Optional[int] = None

class WorkspaceGoal(BaseModel):
    id: UUID
    workspace_id: UUID
    metric_type: str  # 🌍 UNIVERSAL: Now accepts any string for agnostic goal types
    target_value: float
    current_value: float = 0
    unit: str = ""
    priority: int
    status: GoalStatus = GoalStatus.ACTIVE
    success_criteria: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    source_goal_text: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    last_validation_at: Optional[datetime] = None
    validation_frequency_minutes: int = 20
    
    # Enhanced goal metrics - Asset-driven system
    confidence: float = 0.8
    semantic_context: Optional[Dict[str, Any]] = None
    goal_type: str = "deliverable"
    is_percentage: bool = False
    is_minimum: bool = True
    
    # Asset-driven progress tracking (Pillar 12: Concrete Deliverables)
    progress_percentage: float = 0.0
    asset_completion_rate: float = 0.0
    quality_score: float = 0.0
    asset_requirements_count: int = 0
    assets_completed_count: int = 0
    ai_validation_enabled: bool = True
    memory_insights: Optional[Dict[str, Any]] = None
    
    # Computed properties
    @property
    def completion_percentage(self) -> float:
        if self.target_value <= 0:
            return 0.0
        return round((self.current_value / self.target_value) * 100, 1)
    
    @property
    def remaining_value(self) -> float:
        return max(0, self.target_value - self.current_value)
    
    @property
    def is_completed(self) -> bool:
        return self.current_value >= self.target_value
    
    @property
    def needs_validation(self) -> bool:
        if self.status != GoalStatus.ACTIVE:
            return False
        if self.last_validation_at is None:
            return True
        from datetime import timedelta
        next_validation = self.last_validation_at + timedelta(minutes=self.validation_frequency_minutes)
        return datetime.now() >= next_validation
    
    model_config = ConfigDict(from_attributes=True)

class WorkspaceGoalProgress(BaseModel):
    """Extended view with progress tracking"""
    goal: WorkspaceGoal
    completion_percentage: float
    remaining_value: float
    progress_status: Literal["not_started", "started", "in_progress", "near_completion", "completed"]
    needs_validation: bool
    
    @classmethod
    def from_goal(cls, goal: WorkspaceGoal) -> "WorkspaceGoalProgress":
        # Determine progress status
        if goal.completion_percentage >= 100:
            progress_status = "completed"
        elif goal.completion_percentage >= 80:
            progress_status = "near_completion"
        elif goal.completion_percentage >= 50:
            progress_status = "in_progress"
        elif goal.current_value > 0:
            progress_status = "started"
        else:
            progress_status = "not_started"
        
        return cls(
            goal=goal,
            completion_percentage=goal.completion_percentage,
            remaining_value=goal.remaining_value,
            progress_status=progress_status,
            needs_validation=goal.needs_validation
        )
    
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
    """Enhanced asset requirement from existing goal_asset_requirements"""
    id: UUID = PydanticField(default_factory=uuid4)
    goal_id: UUID = PydanticField(..., description="Goal this requirement serves")
    decomposition_id: Optional[UUID] = PydanticField(default=None, description="From original thinking system")
    workspace_id: UUID = PydanticField(...)
    
    # Asset identification (enhanced from existing)
    asset_type: str = PydanticField(default="document", description="document, data, design, code, presentation")
    asset_format: str = PydanticField(default="structured_data", description="Asset format type")
    asset_name: str = PydanticField(..., description="Name from existing name field")
    description: str = PydanticField(..., description="From existing description field")
    
    # Requirements (enhanced)
    acceptance_criteria: Dict[str, Any] = PydanticField(default_factory=dict)
    weight: float = PydanticField(default=1.0, ge=0.0, le=3.0)
    mandatory: bool = PydanticField(default=True)
    business_value_score: float = PydanticField(default=0.5, ge=0.0, le=1.0)
    validation_rules: Dict[str, Any] = PydanticField(default_factory=dict)
    automation_ready: bool = PydanticField(default=False)
    
    # From existing goal_todos fields
    priority: str = PydanticField(default="medium", description="low, medium, high")
    estimated_effort: Optional[str] = PydanticField(default=None, description="low, medium, high")
    user_impact: Optional[str] = PydanticField(default=None, description="immediate, short-term, long-term")
    complexity: Optional[str] = PydanticField(default=None, description="simple, medium, complex")
    value_proposition: Optional[str] = PydanticField(default=None)
    completion_criteria: Optional[str] = PydanticField(default=None)
    deliverable_type: Optional[str] = PydanticField(default=None)
    supports_assets: List[str] = PydanticField(default_factory=list)
    
    # Status tracking (from existing)
    status: str = PydanticField(default="pending", description="pending, in_progress, completed, blocked")
    progress_percentage: int = PydanticField(default=0, ge=0, le=100)
    linked_task_id: Optional[UUID] = PydanticField(default=None)
    
    # Pillar compliance
    ai_generated: bool = PydanticField(default=True, description="Pillar 2: AI-Driven")
    language_agnostic: bool = PydanticField(default=True, description="Pillar 3: Universal")
    sdk_compatible: bool = PydanticField(default=True, description="Pillar 1: OpenAI SDK")
    
    # Timestamps (from existing)
    created_at: datetime = PydanticField(default_factory=datetime.now)
    updated_at: datetime = PydanticField(default_factory=datetime.now)
    completed_at: Optional[datetime] = PydanticField(default=None)
    
    model_config = ConfigDict(from_attributes=True)

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

class AssetQualityMetrics(BaseModel):
    """Metriche di qualità per asset evaluation"""
    overall_quality: float = PydanticField(..., ge=0.0, le=1.0, description="Score qualità complessiva")
    actionability_score: float = PydanticField(..., ge=0.0, le=1.0, description="Quanto è actionable l'asset")
    completeness_score: float = PydanticField(..., ge=0.0, le=1.0, description="Completezza dell'asset")
    concreteness_score: float = PydanticField(..., ge=0.0, le=1.0, description="Concretezza vs teorico")
    business_value_score: float = PydanticField(..., ge=0.0, le=1.0, description="Valore business stimato")
    needs_enhancement: bool = PydanticField(..., description="Se richiede enhancement")
    enhancement_suggestions: List[str] = PydanticField(default_factory=list, description="Suggerimenti miglioramento")
    
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

# === WORKSPACE MEMORY SYSTEM ===

class InsightType(str, Enum):
    """Tipi di insight per workspace memory"""
    SUCCESS_PATTERN = "success_pattern"     # Cosa ha funzionato bene
    FAILURE_LESSON = "failure_lesson"       # Cosa non ha funzionato
    DISCOVERY = "discovery"                 # Nuove informazioni scoperte
    CONSTRAINT = "constraint"               # Limitazioni o vincoli trovati
    OPTIMIZATION = "optimization"           # Miglioramenti identificati

class WorkspaceInsight(BaseModel):
    """Insight estratto da task execution per workspace memory"""
    id: Optional[UUID] = PydanticField(default=None, description="ID univoco dell'insight")
    workspace_id: UUID = PydanticField(..., description="ID del workspace")
    task_id: Optional[UUID] = PydanticField(default=None, description="ID del task sorgente (opzionale)")
    agent_role: str = PydanticField(..., description="Ruolo dell'agente che ha generato l'insight")
    insight_type: InsightType = PydanticField(..., description="Tipo di insight")
    content: str = PydanticField(..., max_length=200, description="Contenuto dell'insight (max 200 chars)")
    relevance_tags: List[str] = PydanticField(default_factory=list, description="Tag per filtraggio")
    confidence_score: float = PydanticField(default=1.0, ge=0.0, le=1.0, description="Fiducia nell'insight")
    expires_at: Optional[datetime] = PydanticField(default=None, description="Data scadenza insight (anti-stale)")
    created_at: datetime = PydanticField(default_factory=datetime.now, description="Data creazione")
    
    model_config = ConfigDict(from_attributes=True)

class MemoryQueryRequest(BaseModel):
    """Richiesta di query alla memoria del workspace"""
    query: str = PydanticField(..., description="Query di ricerca")
    insight_types: Optional[List[InsightType]] = PydanticField(default=None, description="Filtro per tipi insight")
    tags: Optional[List[str]] = PydanticField(default=None, description="Filtro per tag")
    max_results: int = PydanticField(default=5, ge=1, le=20, description="Numero massimo risultati")
    min_confidence: float = PydanticField(default=0.5, ge=0.0, le=1.0, description="Confidence minima")
    exclude_expired: bool = PydanticField(default=True, description="Escludi insight scaduti")

class MemoryQueryResponse(BaseModel):
    """Risposta di query alla memoria del workspace"""
    insights: List[WorkspaceInsight] = PydanticField(..., description="Insight trovati")
    total_found: int = PydanticField(..., description="Numero totale insight trovati")
    query_context: str = PydanticField(..., description="Context riassuntivo per l'agente")
    
class WorkspaceMemorySummary(BaseModel):
    """Summary della memoria del workspace"""
    workspace_id: UUID = PydanticField(..., description="ID del workspace")
    total_insights: int = PydanticField(default=0, description="Numero totale insights")
    insights_by_type: Dict[str, int] = PydanticField(default_factory=dict, description="Count per tipo")
    top_tags: List[str] = PydanticField(default_factory=list, description="Tag più frequenti")
    recent_discoveries: List[str] = PydanticField(default_factory=list, description="Scoperte recenti")
    key_constraints: List[str] = PydanticField(default_factory=list, description="Vincoli chiave")
    success_patterns: List[str] = PydanticField(default_factory=list, description="Pattern di successo")
    last_updated: datetime = PydanticField(default_factory=datetime.now, description="Ultimo aggiornamento")

# === ASSET-DRIVEN SYSTEM MODELS (PILLAR-COMPLIANT) ===

class AssetArtifact(BaseModel):
    """Asset artifact with pillar compliance - Pillar 12: Concrete Deliverables"""
    id: Optional[UUID] = PydanticField(default=None)
    requirement_id: UUID = PydanticField(..., description="Asset requirement this fulfills")
    task_id: Optional[UUID] = PydanticField(default=None, description="Task that produced this artifact")
    agent_id: Optional[UUID] = PydanticField(default=None, description="Agent that created this")
    workspace_id: Optional[UUID] = PydanticField(default=None, description="Workspace this artifact belongs to")
    
    # Artifact identification (Pillar 12: Concrete Deliverables)
    artifact_name: str = PydanticField(..., max_length=200)
    artifact_type: str = PydanticField(..., description="file, text, json, url, binary, structured_data, openai_asset")
    artifact_format: str = PydanticField(default="text", description="Format of the artifact content")
    
    # Content storage (Pillar 1: OpenAI SDK native)
    content: Optional[str] = PydanticField(default=None, description="Primary content")
    content_format: str = PydanticField(default="text", description="Content format type")
    file_path: Optional[str] = PydanticField(default=None, max_length=500)
    external_url: Optional[str] = PydanticField(default=None, max_length=500)
    openai_file_id: Optional[str] = PydanticField(default=None, max_length=255, description="Pillar 1: OpenAI SDK file reference")
    metadata: Dict[str, Any] = PydanticField(default_factory=dict)
    
    # Content metrics
    size_bytes: Optional[int] = PydanticField(default=None)
    word_count: Optional[int] = PydanticField(default=None)
    checksum: Optional[str] = PydanticField(default=None, max_length=64)
    
    # Quality validation (Pillar 8: AI-first QA)
    quality_score: float = PydanticField(default=0.0, ge=0.0, le=1.0)
    validation_passed: bool = PydanticField(default=False)
    validation_details: Dict[str, Any] = PydanticField(default_factory=dict)
    validation_errors: List[str] = PydanticField(default_factory=list)
    ai_quality_check: Dict[str, Any] = PydanticField(default_factory=dict, description="Pillar 8: AI Quality Gates")
    
    # Approval workflow (Pillar 8: Human-in-the-Loop)
    status: str = PydanticField(default="draft", description="draft, ai_validated, human_review, approved, rejected, needs_improvement")
    version: int = PydanticField(default=1)
    human_review_required: bool = PydanticField(default=False)
    
    # Business metrics (Pillar 12: Actionable Deliverables)
    business_value_score: float = PydanticField(default=0.0, ge=0.0, le=1.0)
    actionability_score: float = PydanticField(default=0.0, ge=0.0, le=1.0)
    automation_ready: bool = PydanticField(default=False)
    
    # AI Enhancement (Pillar 12: AI Content Enhancer)
    ai_enhanced: bool = PydanticField(default=False)
    enhancement_applied: Dict[str, Any] = PydanticField(default_factory=dict)
    original_content_hash: Optional[str] = PydanticField(default=None, max_length=64)
    
    # Language & Universal Support (Pillar 3: Universal)
    detected_language: str = PydanticField(default="auto", max_length=10)
    language_agnostic: bool = PydanticField(default=True)
    
    # Memory Integration (Pillar 6: Memory System)
    memory_context: Dict[str, Any] = PydanticField(default_factory=dict)
    learning_insights: Dict[str, Any] = PydanticField(default_factory=dict)
    
    # Real-time Thinking (Pillar 10: Real-Time Thinking)
    thinking_process: Dict[str, Any] = PydanticField(default_factory=dict)
    reasoning_steps: List[str] = PydanticField(default_factory=list)
    
    # Timestamps
    created_at: datetime = PydanticField(default_factory=datetime.now)
    updated_at: datetime = PydanticField(default_factory=datetime.now)
    approved_at: Optional[datetime] = PydanticField(default=None)
    approved_by_user_id: Optional[UUID] = PydanticField(default=None)
    
    model_config = ConfigDict(from_attributes=True)

class QualityRule(BaseModel):
    """AI-driven quality rule - Pillar 2: AI-Driven, zero hard-coding"""
    id: Optional[UUID] = PydanticField(default=None)
    asset_type: str = PydanticField(..., max_length=50)
    rule_name: str = PydanticField(..., max_length=200)
    rule_description: Optional[str] = PydanticField(default=None)
    
    # AI-driven validation (Pillar 2: AI-Driven, zero hard-coding)
    ai_validation_prompt: str = PydanticField(..., description="AI prompt for validation")
    validation_model: str = PydanticField(default="gpt-4o-mini", description="Pillar 1: OpenAI SDK")
    validation_config: Dict[str, Any] = PydanticField(default_factory=dict)
    threshold_score: float = PydanticField(default=0.8, ge=0.0, le=1.0)
    weight: float = PydanticField(default=1.0, ge=0.0, le=3.0)
    
    # Rule management (Pillar 4: Scalable & auto-apprendente)
    is_active: bool = PydanticField(default=True)
    rule_order: int = PydanticField(default=1)
    failure_action: str = PydanticField(default="ai_enhance", description="warn, block, ai_enhance, human_review")
    auto_learning_enabled: bool = PydanticField(default=True, description="Pillar 4: Auto-learning")
    
    # Memory integration (Pillar 6: Memory System)
    success_patterns: Dict[str, Any] = PydanticField(default_factory=dict)
    failure_lessons: Dict[str, Any] = PydanticField(default_factory=dict)
    
    # Universal support (Pillar 3: Universal)
    language_agnostic: bool = PydanticField(default=True)
    domain_agnostic: bool = PydanticField(default=True)
    
    created_at: datetime = PydanticField(default_factory=datetime.now)
    
    model_config = ConfigDict(from_attributes=True)

class QualityValidation(BaseModel):
    """Quality validation result - Pillar 8: AI-first QA"""
    id: Optional[UUID] = PydanticField(default=None)
    artifact_id: UUID = PydanticField(..., description="Artifact being validated")
    rule_id: Optional[UUID] = PydanticField(default=None, description="Quality rule applied")
    workspace_id: Optional[UUID] = PydanticField(default=None, description="Workspace ID for validation")
    
    # Validation results (Pillar 8: AI-first QA)
    score: float = PydanticField(..., ge=0.0, le=1.0)
    passed: bool = PydanticField(...)
    validation_output: Dict[str, Any] = PydanticField(default_factory=dict)
    feedback: Optional[str] = PydanticField(default=None)
    ai_reasoning: Optional[str] = PydanticField(default=None, description="Pillar 10: Explainability")
    
    # Enhanced AI insights (Pillar 2: AI-Driven)
    ai_assessment: Optional[str] = PydanticField(default=None, description="AI-generated assessment")
    improvement_suggestions: List[str] = PydanticField(default_factory=list, description="AI improvement suggestions")
    business_impact: Optional[str] = PydanticField(default=None, description="Business impact analysis")
    actionability_assessment: Optional[float] = PydanticField(default=None, ge=0.0, le=1.0, description="Actionability score")
    
    # Quality dimensions (Pillar 8: Quality Gates)
    quality_dimensions: Dict[str, float] = PydanticField(default_factory=dict, description="Quality dimension scores")
    
    # Validation metadata (Pillar 1: OpenAI SDK)
    validated_at: datetime = PydanticField(default_factory=datetime.now)
    validator_type: str = PydanticField(default="ai", description="ai, human, automated, hybrid")
    validation_model: Optional[str] = PydanticField(default=None, max_length=50, description="AI model used for validation")
    openai_model_used: Optional[str] = PydanticField(default=None, max_length=50)
    openai_completion_id: Optional[str] = PydanticField(default=None, max_length=255)
    execution_time_ms: Optional[int] = PydanticField(default=None)
    processing_time_ms: Optional[int] = PydanticField(default=None)
    
    # Enhancement tracking (Pillar 12: AI Content Enhancer)
    enhancement_suggested: bool = PydanticField(default=False)
    enhancement_applied: bool = PydanticField(default=False)
    enhancement_details: Dict[str, Any] = PydanticField(default_factory=dict)
    
    # Pillar compliance (Pillar system compliance)
    ai_driven: bool = PydanticField(default=True, description="Whether validation was AI-driven")
    pillar_compliance_check: Dict[str, Any] = PydanticField(default_factory=dict, description="Pillar compliance assessment")
    
    model_config = ConfigDict(from_attributes=True)

# AssetRequirement class moved to line 624 to fix import dependencies

class EnhancedWorkspaceGoal(BaseModel):
    """Enhanced workspace goal with asset tracking"""
    # Existing fields from WorkspaceGoal
    id: Optional[UUID] = PydanticField(default=None)
    workspace_id: UUID = PydanticField(...)
    metric_type: str = PydanticField(..., description="AI-generated goal metric")
    target_value: float = PydanticField(...)
    current_value: float = PydanticField(default=0.0)
    status: GoalStatus = PydanticField(default=GoalStatus.ACTIVE)
    
    # Enhanced asset-driven fields
    asset_completion_rate: float = PydanticField(default=0.0, ge=0.0, le=1.0)
    quality_score: float = PydanticField(default=0.0, ge=0.0, le=1.0)
    asset_requirements_count: int = PydanticField(default=0)
    assets_completed_count: int = PydanticField(default=0)
    ai_validation_enabled: bool = PydanticField(default=True, description="Pillar 8: AI-first QA")
    memory_insights: Dict[str, Any] = PydanticField(default_factory=dict, description="Pillar 6: Memory System")
    
    # Existing timestamps
    created_at: datetime = PydanticField(default_factory=datetime.now)
    updated_at: datetime = PydanticField(default_factory=datetime.now)
    last_validation_at: Optional[datetime] = PydanticField(default=None)
    
    model_config = ConfigDict(from_attributes=True)

class EnhancedTask(BaseModel):
    """Enhanced task with asset production capabilities"""
    # Existing core Task fields (inherit from existing Task model)
    id: Optional[UUID] = PydanticField(default=None)
    workspace_id: UUID = PydanticField(...)
    agent_id: Optional[UUID] = PydanticField(default=None)
    name: str = PydanticField(...)
    description: str = PydanticField(...)
    status: TaskStatus = PydanticField(default=TaskStatus.PENDING)
    priority: str = PydanticField(default="medium")
    
    # Enhanced asset production fields
    target_asset_type: Optional[str] = PydanticField(default=None, max_length=50)
    produces_artifact: bool = PydanticField(default=False)
    asset_requirement_id: Optional[UUID] = PydanticField(default=None)
    quality_validated: bool = PydanticField(default=False)
    ai_enhanced: bool = PydanticField(default=False, description="Pillar 12: AI Content Enhancer")
    openai_thread_id: Optional[str] = PydanticField(default=None, max_length=255, description="Pillar 1: OpenAI SDK native")
    real_time_thinking: Dict[str, Any] = PydanticField(default_factory=dict, description="Pillar 10: Real-Time Thinking")
    
    # Existing fields
    context_data: Optional[Dict[str, Any]] = PydanticField(default_factory=dict)
    estimated_effort_hours: Optional[int] = PydanticField(default=None)
    deadline: Optional[datetime] = PydanticField(default=None)
    created_at: datetime = PydanticField(default_factory=datetime.now)
    updated_at: datetime = PydanticField(default_factory=datetime.now)
    completed_at: Optional[datetime] = PydanticField(default=None)
    
    model_config = ConfigDict(from_attributes=True)

class GoalProgressLog(BaseModel):
    """Goal progress tracking with AI analysis - Pillar 5 & 6"""
    id: Optional[UUID] = PydanticField(default=None)
    goal_id: UUID = PydanticField(...)
    
    # Progress tracking (Pillar 5: Goal-Driven tracking)
    previous_value: Optional[float] = PydanticField(default=None)
    new_value: Optional[float] = PydanticField(default=None)
    previous_asset_rate: Optional[float] = PydanticField(default=None)
    new_asset_rate: Optional[float] = PydanticField(default=None)
    previous_quality_score: Optional[float] = PydanticField(default=None)
    new_quality_score: Optional[float] = PydanticField(default=None)
    
    # Change context (Pillar 13: Course-Correction)
    change_reason: str = PydanticField(..., description="artifact_approved, artifact_rejected, quality_improved, etc.")
    
    # AI-driven insights (Pillar 2: AI-Driven)
    ai_analysis: Dict[str, Any] = PydanticField(default_factory=dict)
    course_correction_suggested: Dict[str, Any] = PydanticField(default_factory=dict)
    
    # Memory integration (Pillar 6: Memory System)
    memory_insights_applied: Dict[str, Any] = PydanticField(default_factory=dict)
    learning_captured: Dict[str, Any] = PydanticField(default_factory=dict)
    
    # Triggering events
    triggering_artifact_id: Optional[UUID] = PydanticField(default=None)
    triggering_task_id: Optional[UUID] = PydanticField(default=None)
    triggering_user_id: Optional[UUID] = PydanticField(default=None)
    
    # Real-time tracking (Pillar 10: Real-Time Thinking)
    real_time_reasoning: Dict[str, Any] = PydanticField(default_factory=dict)
    
    changed_at: datetime = PydanticField(default_factory=datetime.now)
    metadata: Dict[str, Any] = PydanticField(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)