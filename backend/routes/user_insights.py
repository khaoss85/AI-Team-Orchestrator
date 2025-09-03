"""
User Insights Management API Routes
RESTful endpoints for creating, reading, updating, and deleting user-managed insights
"""

from fastapi import APIRouter, HTTPException, Query, Body, Depends, status, Request
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

from models import (
    WorkspaceInsight,
    InsightType
)
from services.user_insight_manager import (
    user_insight_manager,
    UserManagedInsight,
    BulkOperation,
    UserInsightFlag
)
from database import get_workspace
from middleware.trace_middleware import get_trace_id, create_traced_logger

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/user-insights", tags=["user-insights"])

# Request/Response models
from pydantic import BaseModel, Field

class CreateInsightRequest(BaseModel):
    """Request model for creating a new user insight"""
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    category: str = Field(default="general")
    domain_type: str = Field(default="general")
    metrics: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class UpdateInsightRequest(BaseModel):
    """Request model for updating an insight"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = None
    domain_type: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class FlagInsightRequest(BaseModel):
    """Request model for flagging an insight"""
    flag_type: str = Field(..., description="Type of flag: verified, important, outdated, needs_review")
    flag_value: bool = Field(..., description="True to set flag, False to remove")

class BulkOperationRequest(BaseModel):
    """Request model for bulk operations"""
    insight_ids: List[str] = Field(..., min_items=1)
    operation: str = Field(..., description="Operation type: delete, categorize, flag, restore")
    operation_data: Optional[Dict[str, Any]] = None

class InsightResponse(BaseModel):
    """Response model for insight data"""
    id: str
    workspace_id: str
    title: str
    content: str
    category: str
    domain_type: str
    created_by: str
    created_at: str
    updated_at: str
    is_user_created: bool
    is_user_modified: bool
    is_deleted: bool
    version_number: int
    user_flags: Dict[str, Any]
    metrics: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None
    business_value_score: float
    confidence_score: float
    
    @classmethod
    def from_user_insight(cls, insight: UserManagedInsight) -> 'InsightResponse':
        return cls(
            id=str(insight.id),
            workspace_id=str(insight.workspace_id),
            title=insight.title,
            content=insight.content,
            category=insight.category,
            domain_type=insight.domain_type,
            created_by=insight.created_by,
            created_at=insight.created_at.isoformat() if isinstance(insight.created_at, datetime) else insight.created_at,
            updated_at=insight.updated_at.isoformat() if isinstance(insight.updated_at, datetime) else insight.updated_at,
            is_user_created=insight.is_user_created,
            is_user_modified=insight.is_user_modified,
            is_deleted=insight.is_deleted,
            version_number=insight.version_number,
            user_flags=insight.user_flags,
            metrics=insight.quantifiable_metrics,
            recommendations=insight.action_recommendations,
            business_value_score=insight.business_value_score,
            confidence_score=insight.confidence_score
        )

class InsightListResponse(BaseModel):
    """Response model for listing insights"""
    insights: List[InsightResponse]
    total: int
    offset: int
    limit: int

# Helper function to get user ID from request (simplified - replace with actual auth)
async def get_current_user_id(request: Request) -> str:
    """Get current user ID from request context"""
    # In production, extract from JWT token or session
    # For now, use a placeholder or header value
    user_id = request.headers.get("X-User-Id", "default_user")
    return user_id

# API Endpoints

@router.post("/{workspace_id}/insights", response_model=InsightResponse, status_code=status.HTTP_201_CREATED)
async def create_user_insight(
    workspace_id: UUID,
    request: Request,
    insight_data: CreateInsightRequest
):
    """Create a new user-generated insight"""
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Creating user insight for workspace {workspace_id}", trace_id=trace_id)
    
    try:
        # Verify workspace exists
        workspace = await get_workspace(str(workspace_id))
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace {workspace_id} not found"
            )
        
        # Get user ID
        user_id = await get_current_user_id(request)
        
        # Create insight
        insight = await user_insight_manager.create_user_insight(
            workspace_id=str(workspace_id),
            title=insight_data.title,
            content=insight_data.content,
            category=insight_data.category,
            created_by=user_id,
            domain_type=insight_data.domain_type,
            metrics=insight_data.metrics,
            recommendations=insight_data.recommendations,
            tags=insight_data.tags,
            metadata=insight_data.metadata
        )
        
        logger.info(f"✅ Created user insight {insight.id} in workspace {workspace_id}")
        return InsightResponse.from_user_insight(insight)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to create user insight: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create insight: {str(e)}"
        )

@router.get("/{workspace_id}/insights", response_model=InsightListResponse)
async def list_insights(
    workspace_id: UUID,
    request: Request,
    include_ai: bool = Query(True, description="Include AI-generated insights"),
    include_user: bool = Query(True, description="Include user-created insights"),
    include_deleted: bool = Query(False, description="Include deleted insights"),
    category: Optional[str] = Query(None, description="Filter by category"),
    flags: Optional[List[str]] = Query(None, description="Filter by flags"),
    search: Optional[str] = Query(None, description="Search in title and content"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """List insights with filtering options"""
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Listing insights for workspace {workspace_id}", trace_id=trace_id)
    
    try:
        insights, total = await user_insight_manager.list_insights(
            workspace_id=str(workspace_id),
            include_ai=include_ai,
            include_user=include_user,
            include_deleted=include_deleted,
            category=category,
            flags=flags,
            search_query=search,
            limit=limit,
            offset=offset
        )
        
        response_insights = [InsightResponse.from_user_insight(i) for i in insights]
        
        logger.info(f"✅ Listed {len(insights)} insights for workspace {workspace_id}")
        return InsightListResponse(
            insights=response_insights,
            total=total,
            offset=offset,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to list insights: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list insights: {str(e)}"
        )

@router.get("/insights/{insight_id}", response_model=InsightResponse)
async def get_insight(
    insight_id: UUID,
    request: Request
):
    """Get a specific insight by ID"""
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Getting insight {insight_id}", trace_id=trace_id)
    
    try:
        # For now, query directly from database
        from database import supabase
        result = supabase.table('workspace_insights').select('*').eq('id', str(insight_id)).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Insight {insight_id} not found"
            )
        
        insight = UserManagedInsight.from_dict(result.data[0])
        return InsightResponse.from_user_insight(insight)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get insight: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get insight: {str(e)}"
        )

@router.put("/insights/{insight_id}", response_model=InsightResponse)
async def update_insight(
    insight_id: UUID,
    request: Request,
    update_data: UpdateInsightRequest
):
    """Update an existing insight"""
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Updating insight {insight_id}", trace_id=trace_id)
    
    try:
        # Get user ID
        user_id = await get_current_user_id(request)
        
        # Prepare updates dictionary (exclude None values)
        updates = {k: v for k, v in update_data.dict().items() if v is not None}
        
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No updates provided"
            )
        
        # Update insight
        insight = await user_insight_manager.update_insight(
            insight_id=str(insight_id),
            updates=updates,
            modified_by=user_id
        )
        
        logger.info(f"✅ Updated insight {insight_id}")
        return InsightResponse.from_user_insight(insight)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Failed to update insight: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update insight: {str(e)}"
        )

@router.delete("/insights/{insight_id}")
async def delete_insight(
    insight_id: UUID,
    request: Request,
    hard_delete: bool = Query(False, description="Permanently delete (cannot be undone)")
):
    """Delete an insight (soft delete by default)"""
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"{'Hard' if hard_delete else 'Soft'} deleting insight {insight_id}", trace_id=trace_id)
    
    try:
        # Get user ID
        user_id = await get_current_user_id(request)
        
        # Delete insight
        success = await user_insight_manager.delete_insight(
            insight_id=str(insight_id),
            deleted_by=user_id,
            hard_delete=hard_delete
        )
        
        if success:
            logger.info(f"✅ {'Hard' if hard_delete else 'Soft'} deleted insight {insight_id}")
            return {"message": f"Insight {'permanently' if hard_delete else ''} deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Insight {insight_id} not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete insight: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete insight: {str(e)}"
        )

@router.post("/insights/{insight_id}/restore", response_model=InsightResponse)
async def restore_insight(
    insight_id: UUID,
    request: Request
):
    """Restore a soft-deleted insight"""
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Restoring insight {insight_id}", trace_id=trace_id)
    
    try:
        # Get user ID
        user_id = await get_current_user_id(request)
        
        # Restore insight
        insight = await user_insight_manager.restore_insight(
            insight_id=str(insight_id),
            restored_by=user_id
        )
        
        logger.info(f"✅ Restored insight {insight_id}")
        return InsightResponse.from_user_insight(insight)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Failed to restore insight: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore insight: {str(e)}"
        )

@router.patch("/insights/{insight_id}/category", response_model=InsightResponse)
async def recategorize_insight(
    insight_id: UUID,
    request: Request,
    category: str = Body(..., embed=True)
):
    """Change the category of an insight"""
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Recategorizing insight {insight_id} to {category}", trace_id=trace_id)
    
    try:
        # Get user ID
        user_id = await get_current_user_id(request)
        
        # Recategorize insight
        insight = await user_insight_manager.recategorize_insight(
            insight_id=str(insight_id),
            new_category=category,
            modified_by=user_id
        )
        
        logger.info(f"✅ Recategorized insight {insight_id} to {category}")
        return InsightResponse.from_user_insight(insight)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Failed to recategorize insight: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to recategorize insight: {str(e)}"
        )

@router.post("/insights/{insight_id}/flags", response_model=InsightResponse)
async def flag_insight(
    insight_id: UUID,
    request: Request,
    flag_data: FlagInsightRequest
):
    """Add or remove a flag on an insight"""
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"{'Setting' if flag_data.flag_value else 'Removing'} flag {flag_data.flag_type} on insight {insight_id}", trace_id=trace_id)
    
    try:
        # Get user ID
        user_id = await get_current_user_id(request)
        
        # Flag insight
        insight = await user_insight_manager.flag_insight(
            insight_id=str(insight_id),
            flag_type=flag_data.flag_type,
            flag_value=flag_data.flag_value,
            flagged_by=user_id
        )
        
        logger.info(f"✅ {'Set' if flag_data.flag_value else 'Removed'} flag {flag_data.flag_type} on insight {insight_id}")
        return InsightResponse.from_user_insight(insight)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Failed to flag insight: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to flag insight: {str(e)}"
        )

@router.post("/{workspace_id}/insights/bulk")
async def bulk_operation(
    workspace_id: UUID,
    request: Request,
    bulk_request: BulkOperationRequest
):
    """Perform bulk operations on multiple insights"""
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Performing bulk {bulk_request.operation} on {len(bulk_request.insight_ids)} insights", trace_id=trace_id)
    
    try:
        # Get user ID
        user_id = await get_current_user_id(request)
        
        # Map string operation to enum
        operation_map = {
            'delete': BulkOperation.DELETE,
            'categorize': BulkOperation.CATEGORIZE,
            'flag': BulkOperation.FLAG,
            'unflag': BulkOperation.UNFLAG,
            'restore': BulkOperation.RESTORE
        }
        
        operation = operation_map.get(bulk_request.operation.lower())
        if not operation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid operation: {bulk_request.operation}"
            )
        
        # Perform bulk operation
        result = await user_insight_manager.bulk_operation(
            insight_ids=bulk_request.insight_ids,
            operation=operation,
            performed_by=user_id,
            operation_data=bulk_request.operation_data
        )
        
        logger.info(f"✅ Bulk operation completed: {result['succeeded']}/{result['total']} succeeded")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed bulk operation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed bulk operation: {str(e)}"
        )

@router.get("/insights/{insight_id}/history")
async def get_insight_history(
    insight_id: UUID,
    request: Request,
    limit: int = Query(20, ge=1, le=100)
):
    """Get audit trail history for an insight"""
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Getting history for insight {insight_id}", trace_id=trace_id)
    
    try:
        history = await user_insight_manager.get_insight_history(
            insight_id=str(insight_id),
            limit=limit
        )
        
        logger.info(f"✅ Retrieved {len(history)} history entries for insight {insight_id}")
        return {"insight_id": str(insight_id), "history": history}
        
    except Exception as e:
        logger.error(f"❌ Failed to get insight history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get insight history: {str(e)}"
        )

@router.post("/insights/{insight_id}/undo", response_model=InsightResponse)
async def undo_last_change(
    insight_id: UUID,
    request: Request
):
    """Undo the last modification to an insight"""
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Undoing last change to insight {insight_id}", trace_id=trace_id)
    
    try:
        # Get user ID
        user_id = await get_current_user_id(request)
        
        # Undo last change
        insight = await user_insight_manager.undo_last_change(
            insight_id=str(insight_id),
            user_id=user_id
        )
        
        logger.info(f"✅ Undone last change to insight {insight_id}")
        return InsightResponse.from_user_insight(insight)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Failed to undo changes: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to undo changes: {str(e)}"
        )

# Export router for main app
__all__ = ['router']