# backend/models.py

from pydantic import BaseModel, Field, ConfigDict, validator
from typing import List, Dict, Any, Optional, Union, Literal
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum
import json
import warnings

# Suppress Pydantic JSON schema warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic._internal._generate_schema")
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic.json_schema")

# --- Enums ---
class WorkspaceStatus(str, Enum):
    CREATED = "created"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"
    PROCESSING_TASKS = "processing_tasks"  # Temporary state during task generation
    NEEDS_INTERVENTION = "needs_intervention"  # State requiring human intervention

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskType(str, Enum):
    """🤖 **AI-DRIVEN Task Classification System**
    
    Semantic classification of tasks based on their intent and deliverable type.
    Used by the AI Intent Recognition System to ensure proper content creation.
    """
    CONTENT_CREATION = "content_creation"     # Writing actual content (emails, documents, scripts)
    DATA_GATHERING = "data_gathering"         # Collecting information, research, lists
    STRATEGY_PLANNING = "strategy_planning"   # Strategic thinking, analysis, planning
    IMPLEMENTATION = "implementation"         # Building, setup, technical implementation  
    QUALITY_ASSURANCE = "quality_assurance"  # Review, testing, validation
    COORDINATION = "coordination"             # Team coordination, communication
    HYBRID = "hybrid"                         # Mixed task requiring multiple types

class AgentStatus(str, Enum):
    ACTIVE = "active"
    IDLE = "idle" 
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"

class BookLeadRole(str, Enum):
    CEO = "ceo"
    CTO = "cto"
    DEVELOPER = "developer"
    MANAGER = "manager"
    CONSULTANT = "consultant"
    STUDENT = "student"
    OTHER = "other"

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class AgentSeniority(str, Enum):
    JUNIOR = "junior"
    SENIOR = "senior"
    EXPERT = "expert"

class ProjectPhase(str, Enum):
    PLANNING = "planning"
    RESEARCH = "research"
    DEVELOPMENT = "development"
    TESTING = "testing"
    REVIEW = "review"
    FINALIZATION = "finalization"
    COMPLETED = "completed"

class GoalStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

# Phase sequences and descriptions for project management
PHASE_SEQUENCE = [
    ProjectPhase.PLANNING,
    ProjectPhase.RESEARCH, 
    ProjectPhase.DEVELOPMENT,
    ProjectPhase.TESTING,
    ProjectPhase.REVIEW,
    ProjectPhase.FINALIZATION,
    ProjectPhase.COMPLETED
]

PHASE_DESCRIPTIONS = {
    ProjectPhase.PLANNING: "Initial planning and goal setting",
    ProjectPhase.RESEARCH: "Research and information gathering", 
    ProjectPhase.DEVELOPMENT: "Core development and implementation",
    ProjectPhase.TESTING: "Testing and validation",
    ProjectPhase.REVIEW: "Review and quality assurance",
    ProjectPhase.FINALIZATION: "Final touches and preparation",
    ProjectPhase.COMPLETED: "Project completed"
}

# --- Main Models ---

class BudgetInfo(BaseModel):
    max_amount: float
    currency: str = "EUR"

class Workspace(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    user_id: UUID
    status: WorkspaceStatus
    created_at: datetime
    updated_at: datetime
    goal: Optional[str] = None
    budget: Optional[Union[float, BudgetInfo]] = None
    model_config = ConfigDict(from_attributes=True)

class WorkspaceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    user_id: Optional[UUID] = None
    goal: Optional[str] = None
    budget: Optional[Union[float, BudgetInfo]] = None

class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[WorkspaceStatus] = None
    goal: Optional[str] = None
    budget: Optional[Union[float, BudgetInfo]] = None

class Agent(BaseModel):
    id: UUID
    workspace_id: UUID
    name: str
    role: str
    seniority: str
    status: str
    tools: Optional[List[Dict[str, Any]]] = None
    can_create_tools: Optional[bool] = False
    vector_store_ids: Optional[List[str]] = None
    description: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    personality_traits: Optional[List[str]] = None
    communication_style: Optional[str] = None
    hard_skills: Optional[List[Dict[str, Any]]] = None
    soft_skills: Optional[List[Dict[str, Any]]] = None
    background_story: Optional[str] = None
    llm_config: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class Task(BaseModel):
    id: UUID
    workspace_id: UUID
    goal_id: Optional[UUID] = None
    agent_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    status: TaskStatus
    task_type: Optional[TaskType] = TaskType.HYBRID  # 🤖 AI-driven task classification
    priority: Optional[str] = "medium"
    context_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TaskCreate(BaseModel):
    workspace_id: UUID
    goal_id: Optional[UUID] = None
    agent_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    status: Optional[TaskStatus] = TaskStatus.PENDING
    task_type: Optional[TaskType] = TaskType.HYBRID  # 🤖 AI-driven task classification
    priority: Optional[str] = "medium"
    semantic_hash: Optional[str] = None

class EnhancedTask(Task):
    result: Optional[str] = None

class WorkspaceGoal(BaseModel):
    id: UUID
    workspace_id: UUID
    metric_type: str
    target_value: float
    current_value: float = 0
    priority: int
    description: Optional[str] = None # Added field
    unit: Optional[str] = "units"  # Added field for unit of measurement
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
    
    @property
    def remaining_value(self) -> float:
        """Calculate the remaining value to reach the target"""
        return max(0, self.target_value - self.current_value)
    
    @property
    def is_completed(self) -> bool:
        """Check if the goal is completed"""
        return self.current_value >= self.target_value

# --- Models from deliverable_standards.py ---

class DeliverableType(str, Enum):
    CONTACT_DATABASE = "contact_database"
    EMAIL_SEQUENCE = "email_sequence"
    CONTENT_CALENDAR = "content_calendar"
    BUSINESS_ANALYSIS = "business_analysis"
    STRATEGIC_PLAN = "strategic_plan"
    FINANCIAL_PLAN = "financial_plan"
    TECHNICAL_DELIVERABLE = "technical_deliverable"
    GENERIC_DELIVERABLE = "generic_deliverable"

class ContactRecord(BaseModel):
    name: str = Field(..., min_length=2)
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    company: str = Field(..., min_length=2)
    role: Optional[str] = None

class ContactDatabase(BaseModel):
    contacts: List[ContactRecord]
    total_contacts: int

class EmailMessage(BaseModel):
    subject_line: str
    email_body: str

class EmailSequence(BaseModel):
    sequence_name: str
    emails: List[EmailMessage]

class ContentPiece(BaseModel):
    title: str
    content_body: str

class ContentCalendar(BaseModel):
    calendar_name: str
    content_pieces: List[ContentPiece]

class BusinessInsight(BaseModel):
    insight_title: str
    description: str

class BusinessAnalysis(BaseModel):
    analysis_title: str
    key_insights: List[BusinessInsight]

class StrategicPlan(BaseModel):
    plan_title: str
    objectives: List[str]

class FinancialPlan(BaseModel):
    plan_title: str
    revenue_projections: Dict[str, Any]


class AssetRequirement(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    goal_id: UUID
    workspace_id: UUID
    asset_name: str
    asset_type: str
    description: str
    asset_format: Optional[str] = "text"
    business_value_score: Optional[float] = 0.5
    ai_generated: Optional[bool] = True

class AssetArtifact(BaseModel):
    id: Optional[UUID] = Field(default_factory=uuid4)
    requirement_id: UUID
    task_id: Optional[UUID] = None
    workspace_id: Optional[UUID] = None
    
    # Database-aligned fields (primary)
    name: str = Field(..., description="Database 'name' field")
    type: str = Field(..., description="Database 'type' field")
    
    # Backward compatibility fields
    artifact_name: Optional[str] = Field(default="", description="Legacy field for compatibility")
    artifact_type: Optional[str] = Field(default="", description="Legacy field for compatibility")
    
    # Content and metadata
    content: Optional[Dict[str, Any]] = Field(default_factory=dict, description="JSONB content")
    content_format: str = "json"
    category: Optional[str] = "general"
    
    # Quality scores (database-aligned)
    quality_score: float = 0.0
    completeness_score: Optional[float] = 0.0
    authenticity_score: Optional[float] = 0.0
    actionability_score: Optional[float] = 0.0
    
    # Status and validation
    status: str = "draft"
    validation_status: Optional[str] = "pending"
    validation_passed: bool = False
    
    # AI enhancement
    ai_enhanced: bool = False
    generation_method: Optional[str] = "manual"
    ai_confidence: Optional[float] = 0.0
    source_tools: Optional[List[str]] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)
    
    @validator('artifact_name', pre=True, always=True)
    def set_artifact_name(cls, v, values):
        """Auto-populate artifact_name from name for backward compatibility"""
        return v or values.get('name', '')
    
    @validator('artifact_type', pre=True, always=True)
    def set_artifact_type(cls, v, values):
        """Auto-populate artifact_type from type for backward compatibility"""
        return v or values.get('type', '')

class QualityRule(BaseModel):
    id: Optional[UUID] = None
    rule_name: str
    rule_type: Optional[str] = None  # Make optional for backward compatibility
    asset_type: str
    validation_logic: Dict[str, Any] = Field(default_factory=dict)
    ai_validation_prompt: str
    threshold_score: float = 0.7
    severity: Optional[str] = "medium"  # Make optional for backward compatibility
    rule_order: int = 1
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
class QualityValidation(BaseModel):
    id: Optional[UUID] = None
    artifact_id: UUID
    rule_id: Optional[UUID] = None
    passed: bool
    score: float

class EnhancedWorkspaceGoal(WorkspaceGoal):
    pass

class WorkspaceGoalCreate(BaseModel):
    workspace_id: UUID
    metric_type: str
    target_value: float
    current_value: float = 0
    priority: int = 1
    description: Optional[str] = None
    unit: Optional[str] = "units"

class WorkspaceGoalUpdate(BaseModel):
    metric_type: Optional[str] = None
    target_value: Optional[float] = None
    current_value: Optional[float] = None
    priority: Optional[int] = None
    description: Optional[str] = None
    status: Optional[GoalStatus] = None
    unit: Optional[str] = None

class GoalProgressLog(BaseModel):
    """Model that exactly matches the goal_progress_logs database table schema"""
    id: UUID = Field(default_factory=uuid4)
    goal_id: UUID
    task_id: Optional[UUID] = None
    progress_percentage: float
    quality_score: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    calculation_method: Optional[str] = "manual"
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
class BudgetConstraint(BaseModel):
    max_cost: float
    currency: str = "USD"

class DirectorConfig(BaseModel):
    max_agents: int = 5
    budget_limit: Optional[float] = None
    specialized_roles: List[str] = []
    
class DirectorTeamProposal(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    workspace_id: UUID
    workspace_goal: Optional[str] = None
    user_feedback: Optional[str] = None
    budget_constraint: Optional["BudgetConstraint"] = None
    extracted_goals: Optional[List[Dict[str, Any]]] = None
    budget_limit: Optional[float] = None  # Backward compatibility
    requirements: Optional[str] = None     # Backward compatibility
    # Fields for response from DirectorAgent
    agents: Optional[List["AgentCreate"]] = None
    handoffs: Optional[List["DirectorHandoffProposal"]] = None
    estimated_cost: Optional[Dict[str, Any]] = None
    rationale: Optional[str] = None

class DirectorTeamProposalResponse(BaseModel):
    proposal_id: UUID
    team_members: List[Dict[str, Any]]
    estimated_cost: Optional[float] = None
    timeline: Optional[str] = None

class AgentCreate(BaseModel):
    workspace_id: UUID
    name: str
    role: str
    seniority: str = "junior"
    status: str = "active"
    # Extended fields for Director Agent
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    llm_config: Optional[Dict[str, Any]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    personality_traits: Optional[List[str]] = None
    communication_style: Optional[str] = None
    hard_skills: Optional[List[Dict[str, Any]]] = None
    soft_skills: Optional[List[Dict[str, Any]]] = None
    background_story: Optional[str] = None

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    seniority: Optional[AgentSeniority] = None
    status: Optional[AgentStatus] = None

class HandoffProposalCreate(BaseModel):
    from_agent_id: UUID
    to_agent_id: UUID
    task_id: UUID
    handoff_reason: Optional[str] = None

class DirectorHandoffProposal(BaseModel):
    """Handoff proposal from Director for team structure"""
    from_agent: str = Field(..., alias='from')
    to_agents: List[str] = Field(..., alias='to')
    description: Optional[str] = None
    
    model_config = ConfigDict(
        populate_by_name=True,
    )

class Handoff(BaseModel):
    id: UUID
    from_agent_id: UUID = Field(alias="source_agent_id")
    to_agent_id: UUID = Field(alias="target_agent_id")
    task_id: Optional[UUID] = None  # Make optional as not all handoffs have tasks
    handoff_reason: Optional[str] = Field(default=None, alias="description")  # Map to DB field
    status: str = "pending"
    created_at: datetime
    updated_at: Optional[datetime] = None  # Make optional as not all handoffs have this field
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True  # Allow both original field names and aliases
    )

class AgentHealth(BaseModel):
    agent_id: UUID
    health_score: float = 1.0
    last_activity: Optional[datetime] = None
    error_count: int = 0
    task_completion_rate: float = 1.0

class TaskExecutionOutput(BaseModel):
    task_id: UUID
    result: Optional[str] = None
    status: TaskStatus
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    summary: Optional[str] = None  # Added for holistic pipeline validation
    artifacts: Optional[List[Dict[str, Any]]] = []

# --- AI-Driven Models for Robust Parsing ---

class AIAgentTool(BaseModel):
    type: str
    name: str
    description: Optional[str] = None

class AIAgentLLMConfig(BaseModel):
    model: str
    temperature: float = 0.3

class AIHandoff(BaseModel):
    from_agent: str = Field(..., alias='from')
    to_agents: List[str] = Field(..., alias='to')
    description: Optional[str] = None

class AIAgent(BaseModel):
    name: str
    role: str
    seniority: AgentSeniority
    description: str
    system_prompt: str
    llm_config: AIAgentLLMConfig
    tools: List[AIAgentTool] = []
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    personality_traits: List[str] = []
    communication_style: Optional[str] = None
    hard_skills: List[Dict[str, Any]] = []
    soft_skills: List[Dict[str, Any]] = []
    background_story: Optional[str] = None

class AITeamProposal(BaseModel):
    agents: List[AIAgent]
    handoffs: List[AIHandoff] = []
    estimated_cost: Dict[str, Any]
    rationale: str


# Project insight models
class ProjectDeliverables(BaseModel):
    workspace_id: UUID
    total_deliverables: int = 0
    completed_deliverables: int = 0
    in_progress_deliverables: int = 0
    deliverable_items: List[Dict[str, Any]] = []

class ProjectOutput(BaseModel):
    workspace_id: UUID
    output_type: str
    content: Dict[str, Any]
    quality_score: Optional[float] = None
    created_at: datetime
    status: str = "draft"

class DeliverableFeedback(BaseModel):
    id: UUID
    deliverable_id: UUID
    feedback_text: str
    rating: Optional[int] = None
    created_at: datetime
    status: str = "pending"

class ProjectDeliverableCard(BaseModel):
    id: UUID
    workspace_id: UUID
    title: str
    description: Optional[str] = None
    status: str = "draft"
    completion_percentage: float = 0.0
    created_at: datetime
    updated_at: datetime

class InsightType(str, Enum):
    PROGRESS = "progress"
    RISK = "risk"
    OPPORTUNITY = "opportunity"
    RESOURCE = "resource"

class WorkspaceInsight(BaseModel):
    id: UUID
    workspace_id: UUID
    insight_type: str
    insight_data: Dict[str, Any]
    confidence_score: float = 0.0
    created_at: datetime
    updated_at: datetime

class MemoryQueryRequest(BaseModel):
    workspace_id: Optional[UUID] = None
    query_text: str
    context_types: Optional[List[str]] = None
    limit: int = 10

# --- Book Lead Models ---
class BookLeadCreate(BaseModel):
    """Model for creating a new book lead"""
    name: str = Field(..., min_length=1, max_length=255, description="Nome completo del lead")
    email: str = Field(..., description="Email del lead")
    role: Optional[BookLeadRole] = Field(None, description="Ruolo professionale")
    challenge: Optional[str] = Field(None, max_length=2000, description="Sfida principale con AI")
    gdpr_consent: bool = Field(..., description="Consenso GDPR obbligatorio")
    marketing_consent: bool = Field(default=False, description="Consenso opzionale per newsletter")
    book_chapter: str = Field(default="chapter-2", description="Capitolo dove è apparso il popup")
    user_agent: Optional[str] = Field(None, description="Browser info per analytics")
    referrer_url: Optional[str] = Field(None, description="URL di provenienza")

    @validator('email')
    def validate_email(cls, v):
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Email format not valid')
        return v.lower()

class BookLead(BaseModel):
    """Complete book lead model with database fields"""
    id: UUID
    name: str
    email: str
    role: Optional[BookLeadRole] = None
    challenge: Optional[str] = None
    gdpr_consent: bool
    marketing_consent: bool
    book_chapter: str
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    referrer_url: Optional[str] = None
    confirmation_status: str = "pending"
    confirmation_token_hash: Optional[str] = None
    confirmation_expires_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class BookLeadResponse(BaseModel):
    """Response model for book lead operations"""
    success: bool
    message: str
    lead_id: Optional[UUID] = None

# Helper function for backward compatibility
async def create_model_with_harmonization(model_class, data_dict):
    """Create a model instance with data harmonization"""
    try:
        return model_class(**data_dict)
    except Exception as e:
        # Fallback to creating with available fields only
        valid_fields = {k: v for k, v in data_dict.items() if k in model_class.__fields__}
        return model_class(**valid_fields)

