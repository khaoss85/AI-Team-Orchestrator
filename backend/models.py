# backend/models.py

from pydantic import BaseModel, Field, ConfigDict, validator
from typing import List, Dict, Any, Optional, Union, Literal
from datetime import datetime, timedelta
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
    NEEDS_INTERVENTION = "needs_intervention"  # DEPRECATED: Use AUTO_RECOVERING instead
    AUTO_RECOVERING = "auto_recovering"  # AI-driven autonomous recovery in progress
    DEGRADED_MODE = "degraded_mode"      # Operating with reduced functionality but autonomous

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

# Legacy model (from deliverable_standards.py)
class BusinessInsight(BaseModel):
    insight_title: str
    description: str

# Enhanced BusinessInsight for Content-Aware Learning System
class EnhancedBusinessInsight(BaseModel):
    """Enhanced Business Insight model for Content-Aware Learning System
    
    This model represents domain-specific insights extracted from deliverable content
    with quantifiable metrics and actionable recommendations.
    """
    # Core insight information
    insight_title: str
    description: str
    
    # Domain specificity  
    domain_type: str = "general"  # instagram_marketing, email_marketing, etc.
    insight_category: str = "general"  # performance_metric, best_practice, etc.
    
    # Domain-specific metadata (flexible JSON structure)
    domain_specific_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Quantifiable metrics with before/after comparisons
    quantifiable_metrics: Dict[str, Any] = Field(default_factory=dict)
    
    # Actionable recommendations for future tasks
    action_recommendations: List[str] = Field(default_factory=list)
    
    # Business value and quality scoring
    business_value_score: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    quality_threshold: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Content analysis metadata
    content_source_type: str = "deliverable_content"  # task_result, user_feedback, etc.
    extraction_method: str = "ai_analysis"  # manual, pattern_recognition, etc.
    
    # Validation and application tracking
    validation_status: str = "pending"  # validated, rejected, needs_review, applied
    learning_priority: int = Field(default=1, ge=1, le=5)  # 1=highest, 5=lowest
    
    # Performance tracking
    performance_impact_score: float = Field(default=0.0, ge=0.0, le=1.0)
    application_count: int = Field(default=0, ge=0)
    last_applied_at: Optional[datetime] = None
    
    # Workspace context
    workspace_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    agent_role: str = "content_aware_learning_engine"
    
    # Standard insight fields (for compatibility with WorkspaceInsight)
    relevance_tags: List[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def to_workspace_insight(self) -> "WorkspaceInsight":
        """Convert to WorkspaceInsight model for database storage"""
        # Prepare enhanced metadata with domain-specific information
        enhanced_metadata = {
            **self.metadata,
            "domain_type": self.domain_type,
            "insight_category": self.insight_category,
            "domain_specific_metadata": self.domain_specific_metadata,
            "quantifiable_metrics": self.quantifiable_metrics,
            "action_recommendations": self.action_recommendations,
            "business_value_score": self.business_value_score,
            "quality_threshold": self.quality_threshold,
            "content_source_type": self.content_source_type,
            "extraction_method": self.extraction_method,
            "validation_status": self.validation_status,
            "learning_priority": self.learning_priority,
            "performance_impact_score": self.performance_impact_score,
            "application_count": self.application_count,
            "last_applied_at": self.last_applied_at.isoformat() if self.last_applied_at else None
        }
        
        # Create content that combines title and description
        content = f"{self.insight_title}: {self.description}"
        if self.action_recommendations:
            content += f" Recommendations: {'; '.join(self.action_recommendations)}"
        
        return WorkspaceInsight(
            id=uuid4(),
            workspace_id=self.workspace_id or uuid4(),
            task_id=self.task_id,
            agent_role=self.agent_role,
            insight_type=InsightType.SUCCESS_PATTERN,  # Default to success pattern
            content=content,
            relevance_tags=self.relevance_tags,
            confidence_score=self.confidence_score,
            expires_at=self.expires_at,
            created_at=self.created_at,
            metadata=enhanced_metadata
        )
    
    @classmethod
    def from_workspace_insight(cls, insight: "WorkspaceInsight") -> "EnhancedBusinessInsight":
        """Create from existing WorkspaceInsight"""
        # Extract enhanced metadata
        metadata = insight.metadata or {}
        
        # Parse title and description from content
        parts = insight.content.split(": ", 1)
        title = parts[0] if len(parts) > 1 else "Insight"
        description = parts[1].split(" Recommendations:")[0] if len(parts) > 1 else insight.content
        
        # Extract recommendations if present
        recommendations = []
        if "Recommendations:" in insight.content:
            rec_part = insight.content.split("Recommendations:", 1)[1].strip()
            recommendations = [r.strip() for r in rec_part.split(";") if r.strip()]
        
        return cls(
            insight_title=title,
            description=description,
            domain_type=metadata.get("domain_type", "general"),
            insight_category=metadata.get("insight_category", "general"),
            domain_specific_metadata=metadata.get("domain_specific_metadata", {}),
            quantifiable_metrics=metadata.get("quantifiable_metrics", {}),
            action_recommendations=recommendations or metadata.get("action_recommendations", []),
            business_value_score=metadata.get("business_value_score", 0.0),
            confidence_score=insight.confidence_score,
            quality_threshold=metadata.get("quality_threshold", 0.0),
            content_source_type=metadata.get("content_source_type", "deliverable_content"),
            extraction_method=metadata.get("extraction_method", "ai_analysis"),
            validation_status=metadata.get("validation_status", "pending"),
            learning_priority=metadata.get("learning_priority", 1),
            performance_impact_score=metadata.get("performance_impact_score", 0.0),
            application_count=metadata.get("application_count", 0),
            last_applied_at=datetime.fromisoformat(metadata["last_applied_at"]) if metadata.get("last_applied_at") else None,
            workspace_id=insight.workspace_id,
            task_id=insight.task_id,
            agent_role=insight.agent_role,
            relevance_tags=insight.relevance_tags,
            expires_at=insight.expires_at,
            metadata=metadata,
            created_at=insight.created_at,
            updated_at=insight.updated_at or insight.created_at
        )

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
    
    # Database-aligned fields (match actual column names)
    artifact_name: str = Field(..., description="Database 'artifact_name' field")
    artifact_type: str = Field(..., description="Database 'artifact_type' field")
    
    # Backward compatibility properties  
    @property
    def name(self) -> str:
        """Legacy property mapping to artifact_name"""
        return self.artifact_name
    
    @property 
    def type(self) -> str:
        """Legacy property mapping to artifact_type"""
        return self.artifact_type
    
    # 🚀 AI-DRIVEN DUAL-FORMAT CONTENT FIELDS
    # Execution format (structured JSON for processing)
    content: Optional[Dict[str, Any]] = Field(default_factory=dict, description="JSONB execution content")
    content_format: str = "json"
    
    # Display format (user-friendly HTML/Markdown for presentation)
    display_content: Optional[str] = Field(default=None, description="AI-transformed display content")
    display_format: Optional[str] = Field(default="html", description="Display format: html, markdown, or text")
    display_summary: Optional[str] = Field(default=None, description="Brief summary for UI cards")
    display_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Display-specific metadata")
    
    # Dual-format tracking
    content_transformation_status: Optional[str] = Field(default="pending", description="Status: pending, success, failed")
    content_transformation_error: Optional[str] = Field(default=None, description="Error message if transformation failed")
    transformation_timestamp: Optional[datetime] = Field(default=None, description="When transformation was performed")
    transformation_method: Optional[str] = Field(default="ai", description="Transformation method: ai, manual, fallback")
    auto_display_generated: Optional[bool] = Field(default=False, description="Whether display content was auto-generated")
    display_content_updated_at: Optional[datetime] = Field(default=None, description="When display content was last updated")
    
    # Content quality and validation
    display_quality_score: Optional[float] = Field(default=0.0, description="Quality score for display content")
    user_friendliness_score: Optional[float] = Field(default=0.0, description="How user-friendly the display is")
    readability_score: Optional[float] = Field(default=0.0, description="Text readability score")
    
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
    
    # Timestamps (database-aligned)
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)
    
    model_config = ConfigDict(from_attributes=True)

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
    SUCCESS_PATTERN = "success_pattern"
    FAILURE_LESSON = "failure_lesson"
    CONSTRAINT = "constraint"
    DISCOVERY = "discovery"
    OPTIMIZATION = "optimization"
    # Legacy values for backward compatibility
    PROGRESS = "progress"
    RISK = "risk"
    OPPORTUNITY = "opportunity"
    RESOURCE = "resource"

class WorkspaceInsight(BaseModel):
    id: UUID
    workspace_id: UUID
    task_id: Optional[UUID] = None
    agent_role: str = "system"
    insight_type: InsightType
    content: str
    relevance_tags: List[str] = Field(default_factory=list)
    confidence_score: float = 0.5
    expires_at: Optional[datetime] = None
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    # Legacy fields for backward compatibility
    insight_data: Optional[Dict[str, Any]] = None
    updated_at: Optional[datetime] = None

class MemoryQueryRequest(BaseModel):
    query: str = ""
    insight_types: Optional[List[InsightType]] = None
    relevance_tags: Optional[List[str]] = None
    tags: Optional[List[str]] = None  # Alias for relevance_tags
    min_confidence: float = 0.0
    exclude_expired: bool = True
    max_results: int = 10
    limit: int = 10  # Alias for max_results
    # Legacy fields for backward compatibility
    workspace_id: Optional[UUID] = None
    query_text: Optional[str] = None
    context_types: Optional[List[str]] = None

class MemoryQueryResponse(BaseModel):
    insights: List[WorkspaceInsight]
    total_found: int
    query_context: str = ""

class WorkspaceMemorySummary(BaseModel):
    workspace_id: UUID
    total_insights: int = 0
    insights_by_type: Dict[str, int] = Field(default_factory=dict)
    top_tags: List[str] = Field(default_factory=list)
    recent_discoveries: List[str] = Field(default_factory=list)
    key_constraints: List[str] = Field(default_factory=list)
    success_patterns: List[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)

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

# --- Recovery System Models ---

class FailurePatternModel(BaseModel):
    """Model for failure pattern detection and tracking"""
    id: UUID = Field(default_factory=uuid4)
    workspace_id: UUID
    task_id: Optional[UUID] = None
    
    # Pattern identification
    pattern_signature: str
    failure_type: str
    error_message_hash: str
    
    # Pattern details  
    error_message: str
    error_type: Optional[str] = None
    root_cause_category: Optional[str] = None
    
    # Frequency tracking
    occurrence_count: int = 1
    first_detected_at: datetime = Field(default_factory=datetime.now)
    last_detected_at: datetime = Field(default_factory=datetime.now)
    
    # Pattern metadata
    is_transient: bool = True
    confidence_score: float = 0.0
    pattern_source: str = "failure_detection_engine"
    
    # Context
    execution_stage: Optional[str] = None
    agent_id: Optional[UUID] = None
    context_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    model_config = ConfigDict(from_attributes=True)

class RecoveryAttemptModel(BaseModel):
    """Model for tracking recovery attempts"""
    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    workspace_id: UUID
    
    # Recovery details
    recovery_strategy: str
    failure_pattern_id: Optional[UUID] = None
    
    # Attempt information
    attempt_number: int = 1
    triggered_by: str
    recovery_reason: Optional[str] = None
    
    # Execution tracking
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    status: str = "in_progress"
    
    # Results
    success: Optional[bool] = None
    recovery_outcome: Optional[str] = None
    error_message: Optional[str] = None
    
    # Metadata
    recovery_context: Dict[str, Any] = Field(default_factory=dict)
    agent_id: Optional[UUID] = None
    estimated_resolution_time: Optional[timedelta] = None
    actual_resolution_time: Optional[timedelta] = None
    
    # AI analysis
    confidence_score: Optional[float] = None
    ai_reasoning: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    model_config = ConfigDict(from_attributes=True)

class RecoveryExplanationModel(BaseModel):
    """Model for recovery explanations"""
    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    workspace_id: UUID
    recovery_attempt_id: Optional[UUID] = None
    
    # Core explanation
    failure_summary: str
    root_cause: str
    retry_decision: str
    confidence_explanation: str
    
    # User-facing information
    user_action_required: Optional[str] = None
    estimated_resolution_time: Optional[str] = None
    severity_level: str = "medium"
    display_category: str = "System Issue"
    
    # Technical details
    technical_details: Dict[str, Any] = Field(default_factory=dict)
    error_pattern_matched: Optional[str] = None
    failure_category: Optional[str] = None
    recovery_strategy: Optional[str] = None
    
    # Generation metadata
    ai_analysis_used: bool = False
    explanation_source: str = "recovery_explanation_engine"
    generation_model: Optional[str] = None
    generation_confidence: Optional[float] = None
    
    # Timestamps
    failure_time: datetime = Field(default_factory=datetime.now)
    explanation_generated_at: datetime = Field(default_factory=datetime.now)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    model_config = ConfigDict(from_attributes=True)

class RecoveryStats(BaseModel):
    """Model for recovery statistics"""
    total_recovery_attempts: int = 0
    successful_recoveries: int = 0
    failure_patterns_count: int = 0
    most_common_failure_type: Optional[str] = None
    recovery_success_rate: float = 0.0
    avg_resolution_time: Optional[timedelta] = None
    
    model_config = ConfigDict(from_attributes=True)

# Enhanced Task model with recovery fields
class TaskWithRecovery(Task):
    """Enhanced Task model with recovery tracking"""
    recovery_count: int = 0
    last_failure_type: Optional[str] = None
    last_recovery_attempt_at: Optional[datetime] = None
    auto_recovery_enabled: bool = True
    
    model_config = ConfigDict(from_attributes=True)

# Enhanced Workspace model with recovery metrics
class WorkspaceWithRecovery(Workspace):
    """Enhanced Workspace model with recovery metrics"""
    total_recovery_attempts: int = 0
    successful_recoveries: int = 0
    last_recovery_check_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

# --- AI-DRIVEN DUAL-FORMAT ARCHITECTURE CONTRACTS ---

class ContentTransformationRequest(BaseModel):
    """Request model for AI content transformation"""
    asset_id: UUID
    execution_content: Dict[str, Any]
    content_type: str
    target_format: str = "html"  # html, markdown, text
    transformation_context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    user_preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)
    quality_requirements: Optional[Dict[str, str]] = Field(default_factory=dict)

class ContentTransformationResponse(BaseModel):
    """Response model for AI content transformation"""
    success: bool
    asset_id: UUID
    display_content: Optional[str] = None
    display_format: str
    display_summary: Optional[str] = None
    display_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Quality metrics
    display_quality_score: float = 0.0
    user_friendliness_score: float = 0.0
    readability_score: float = 0.0
    
    # Transformation details
    transformation_method: str = "ai"
    transformation_timestamp: datetime = Field(default_factory=datetime.now)
    ai_confidence: float = 0.0
    
    # Error handling
    error_message: Optional[str] = None
    fallback_used: bool = False
    retry_suggestions: List[str] = Field(default_factory=list)

class AIContentDisplayTransformer(BaseModel):
    """Service interface contract for AI content display transformation"""
    
    class Config:
        """Configuration for the transformer service"""
        transformation_timeout: int = 30  # seconds
        max_content_length: int = 50000  # characters
        fallback_enabled: bool = True
        quality_threshold: float = 0.6
        
    # Service methods interface (for documentation)
    supported_input_formats: List[str] = ["json", "dict", "text"]
    supported_output_formats: List[str] = ["html", "markdown", "text"]
    transformation_capabilities: List[str] = [
        "structured_data_to_html",
        "json_to_markdown", 
        "content_summarization",
        "user_friendly_formatting",
        "quality_enhancement"
    ]

class EnhancedDeliverableResponse(BaseModel):
    """Enhanced API response model for deliverables with dual-format support"""
    id: str
    title: str
    type: str
    status: str
    created_at: str
    updated_at: str
    
    # Execution content (for system processing)
    execution_content: Dict[str, Any] = Field(default_factory=dict)
    execution_format: str = "json"
    
    # Display content (for user presentation)
    display_content: Optional[str] = None
    display_format: str = "html"
    display_summary: Optional[str] = None
    display_preview: Optional[str] = None  # First 200 chars for cards
    
    # Quality and transformation metadata
    display_quality_score: float = 0.0
    user_friendliness_score: float = 0.0
    content_transformation_status: str = "pending"
    transformation_error: Optional[str] = None
    
    # Business metadata
    business_value_score: float = 0.0
    category: str = "general"
    quality_score: float = 0.0
    
    # User actions
    can_retry_transformation: bool = False
    available_formats: List[str] = Field(default_factory=lambda: ["html"])
    
    # Backward compatibility
    content: Optional[Union[str, Dict[str, Any]]] = None  # Deprecated, use display_content

class DeliverableListResponse(BaseModel):
    """Response model for deliverable list endpoints with enhanced format support"""
    deliverables: List[EnhancedDeliverableResponse]
    total_count: int
    transformation_status: Dict[str, int] = Field(default_factory=dict)  # pending: 2, success: 5, failed: 1
    quality_overview: Dict[str, float] = Field(default_factory=dict)  # avg_display_quality: 0.8, avg_user_friendliness: 0.7
    
    # Pagination and filtering
    page: int = 1
    page_size: int = 20
    has_next: bool = False
    has_previous: bool = False
    
    # System capabilities
    supports_dual_format: bool = True
    available_transformations: List[str] = Field(default_factory=lambda: ["html", "markdown", "text"])

class ContentTransformationError(BaseModel):
    """Error model for content transformation failures"""
    error_code: str
    error_message: str
    asset_id: UUID
    retry_count: int = 0
    max_retries: int = 3
    last_attempt: datetime = Field(default_factory=datetime.now)
    suggested_actions: List[str] = Field(default_factory=list)
    fallback_content: Optional[str] = None
    technical_details: Dict[str, Any] = Field(default_factory=dict)

class TransformationBatchRequest(BaseModel):
    """Batch transformation request for multiple deliverables"""
    asset_ids: List[UUID]
    target_format: str = "html"
    priority: str = "normal"  # low, normal, high
    transformation_context: Dict[str, Any] = Field(default_factory=dict)
    
class TransformationBatchResponse(BaseModel):
    """Batch transformation response"""
    batch_id: str
    total_assets: int
    successful_transformations: int
    failed_transformations: int
    pending_transformations: int
    
    # Results per asset
    results: List[ContentTransformationResponse]
    
    # Batch metadata
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None

# --- MIGRATION AND COMPATIBILITY MODELS ---

class ContentMigrationPlan(BaseModel):
    """Migration plan for existing content to dual-format"""
    migration_id: str = Field(default_factory=lambda: str(uuid4()))
    total_assets: int
    assets_to_migrate: List[UUID]
    
    # Migration strategy
    migration_strategy: str = "incremental"  # incremental, bulk, on_demand
    batch_size: int = 100
    priority_order: str = "newest_first"  # newest_first, oldest_first, high_quality_first
    
    # Quality requirements
    min_quality_threshold: float = 0.5
    skip_failed_assets: bool = True
    create_backups: bool = True
    
    # Timeline
    estimated_duration: timedelta = Field(default=timedelta(hours=1))
    scheduled_start: Optional[datetime] = None

class MigrationStatus(BaseModel):
    """Status model for content migration process"""
    migration_id: str
    status: str  # pending, running, completed, failed, paused
    progress_percentage: float = 0.0
    
    # Progress details
    processed_count: int = 0
    successful_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_remaining: Optional[timedelta] = None
    
    # Error tracking
    recent_errors: List[str] = Field(default_factory=list)
    retry_queue: List[UUID] = Field(default_factory=list)

# Helper function for backward compatibility
async def create_model_with_harmonization(model_class, data_dict):
    """Create a model instance with data harmonization"""
    try:
        return model_class(**data_dict)
    except Exception as e:
        # Fallback to creating with available fields only
        valid_fields = {k: v for k, v in data_dict.items() if k in model_class.__fields__}
        return model_class(**valid_fields)

