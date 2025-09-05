"""
Unified Insight Model - Single source of truth for all insight types
Compliant with 15 Pillars - AI-first, domain-agnostic, multi-tenant
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

class InsightOrigin(str, Enum):
    """Origin of the insight for tracking and filtering"""
    AI_GENERATED = "ai_generated"  # From universal_learning_engine
    USER_CREATED = "user_created"  # Created by user in management interface
    USER_MODIFIED = "user_modified"  # AI insight modified by user
    WORKSPACE_MEMORY = "workspace_memory"  # From workspace memory system
    EXTERNAL_IMPORT = "external_import"  # Imported from external source

class InsightConfidenceLevel(str, Enum):
    """Standardized confidence levels across all systems"""
    HIGH = "high"  # >= 0.8 confidence score
    MODERATE = "moderate"  # 0.6 - 0.8 confidence score  
    LOW = "low"  # < 0.6 confidence score
    EXPLORATORY = "exploratory"  # Experimental or unvalidated

class InsightCategory(str, Enum):
    """Universal categories - domain agnostic"""
    PERFORMANCE = "performance"  # Performance metrics and improvements
    STRATEGY = "strategy"  # Strategic recommendations
    OPERATIONAL = "operational"  # Operational insights
    DISCOVERY = "discovery"  # New findings or patterns
    CONSTRAINT = "constraint"  # Limitations or blockers
    OPTIMIZATION = "optimization"  # Efficiency improvements
    RISK = "risk"  # Risk factors and mitigation
    OPPORTUNITY = "opportunity"  # Growth or improvement opportunities
    GENERAL = "general"  # Uncategorized insights

class UnifiedInsight(BaseModel):
    """
    Unified insight model that bridges all three systems:
    1. AI-generated insights (dynamic)
    2. User-managed insights (persistent)
    3. Workspace memory insights (hybrid)
    """
    
    # Core Identity Fields
    id: UUID = Field(default_factory=uuid4)
    workspace_id: UUID
    origin: InsightOrigin
    
    # Content Fields (Required)
    title: str = Field(..., min_length=1, max_length=500, description="Concise insight title")
    content: str = Field(..., min_length=1, description="Full insight content")
    
    # Classification Fields
    category: InsightCategory = Field(default=InsightCategory.GENERAL)
    confidence_level: InsightConfidenceLevel
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.5)
    
    # AI Extraction Fields (Optional for AI insights)
    domain_context: Optional[str] = None  # AI-detected domain
    language: str = Field(default="en")  # Support multi-language
    metric_name: Optional[str] = None  # For quantifiable insights
    metric_value: Optional[float] = None  # Actual metric value
    comparison_baseline: Optional[str] = None  # What it's compared against
    
    # User Management Fields
    created_by: str = Field(default="system")  # User ID or "system" for AI
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = None
    
    # User Interaction Fields
    is_verified: bool = Field(default=False)
    is_important: bool = Field(default=False)
    is_outdated: bool = Field(default=False)
    needs_review: bool = Field(default=False)
    user_rating: Optional[float] = None  # 1-5 star rating
    
    # Metadata Fields
    tags: List[str] = Field(default_factory=list)
    evidence_sources: List[str] = Field(default_factory=list)  # Source deliverables/tasks
    related_goals: List[UUID] = Field(default_factory=list)  # Related goal IDs
    action_recommendations: List[str] = Field(default_factory=list)
    
    # Business Value Fields
    business_value_score: float = Field(ge=0.0, le=1.0, default=0.5)
    actionability_score: float = Field(ge=0.0, le=1.0, default=0.5)
    
    # System Fields
    version: int = Field(default=1)  # For optimistic locking
    is_deleted: bool = Field(default=False)  # Soft delete
    ttl_seconds: Optional[int] = None  # For AI insights caching
    last_accessed_at: Optional[datetime] = None  # For cache management
    sync_status: Optional[str] = None  # 'pending', 'synced', 'conflict'
    
    # Additional Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
    
    def to_display_format(self) -> str:
        """Convert to human-readable display format"""
        if self.metric_value and self.metric_name and self.comparison_baseline:
            percentage = f"{self.metric_value * 100:.0f}%" if self.metric_value < 1 else f"{self.metric_value:.1f}"
            confidence_emoji = "✅" if self.confidence_level == InsightConfidenceLevel.HIGH else "📊" if self.confidence_level == InsightConfidenceLevel.MODERATE else "🔍"
            return f"{confidence_emoji} {self.confidence_level.value.upper()}: {self.metric_name} shows {percentage} better performance than {self.comparison_baseline}"
        else:
            return self.content
    
    def to_management_format(self) -> Dict[str, Any]:
        """Convert to format expected by management interface"""
        return {
            "id": str(self.id),
            "workspace_id": str(self.workspace_id),
            "title": self.title,
            "content": self.content,
            "category": self.category.value,
            "domain_type": self.domain_context or "general",
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_user_created": self.origin == InsightOrigin.USER_CREATED,
            "is_user_modified": self.origin == InsightOrigin.USER_MODIFIED,
            "is_deleted": self.is_deleted,
            "version_number": self.version,
            "user_flags": {
                "verified": self.is_verified,
                "important": self.is_important,
                "outdated": self.is_outdated,
                "needs_review": self.needs_review
            },
            "metrics": {
                "name": self.metric_name,
                "value": self.metric_value,
                "baseline": self.comparison_baseline
            } if self.metric_name else None,
            "recommendations": self.action_recommendations,
            "business_value_score": self.business_value_score,
            "confidence_score": self.confidence_score
        }
    
    def to_artifact_format(self) -> Dict[str, Any]:
        """Convert to format expected by knowledge artifacts"""
        return {
            "id": str(self.id),
            "type": self.category.value,
            "content": self.to_display_format(),
            "confidence": self.confidence_score,
            "created_at": self.created_at.isoformat(),
            "tags": self.tags
        }
    
    def calculate_confidence_level(self) -> InsightConfidenceLevel:
        """Calculate confidence level from score"""
        if self.confidence_score >= 0.8:
            return InsightConfidenceLevel.HIGH
        elif self.confidence_score >= 0.6:
            return InsightConfidenceLevel.MODERATE
        elif self.confidence_score >= 0.3:
            return InsightConfidenceLevel.LOW
        else:
            return InsightConfidenceLevel.EXPLORATORY
    
    def should_persist(self) -> bool:
        """Determine if AI insight should be persisted to database"""
        # Persist high-value insights
        if self.confidence_score >= 0.7 or self.business_value_score >= 0.7:
            return True
        # Persist user-interacted insights
        if any([self.is_verified, self.is_important, self.user_rating]):
            return True
        # Don't persist low-value ephemeral insights
        return False
    
    def merge_with_user_changes(self, user_updates: Dict[str, Any]) -> 'UnifiedInsight':
        """Merge user modifications while preserving AI origin"""
        updated = self.copy()
        
        # Update allowed user fields
        if 'title' in user_updates:
            updated.title = user_updates['title']
        if 'content' in user_updates:
            updated.content = user_updates['content']
        if 'category' in user_updates:
            updated.category = InsightCategory(user_updates['category'])
        if 'tags' in user_updates:
            updated.tags = user_updates['tags']
        if 'action_recommendations' in user_updates:
            updated.action_recommendations = user_updates['action_recommendations']
        
        # Update metadata
        updated.origin = InsightOrigin.USER_MODIFIED
        updated.updated_at = datetime.utcnow()
        updated.updated_by = user_updates.get('user_id', 'unknown')
        updated.version += 1
        
        return updated


class UnifiedInsightResponse(BaseModel):
    """Response model for unified insight API"""
    insights: List[UnifiedInsight]
    total: int
    offset: int
    limit: int
    filters_applied: Dict[str, Any]
    source_systems: List[str]  # Which systems contributed data
    cache_status: Optional[str]  # 'hit', 'miss', 'partial'
    
class InsightSyncStatus(BaseModel):
    """Track synchronization between systems"""
    workspace_id: UUID
    ai_insights_count: int
    user_insights_count: int  
    memory_insights_count: int
    total_unified: int
    last_sync: datetime
    sync_errors: List[str]
    pending_syncs: int