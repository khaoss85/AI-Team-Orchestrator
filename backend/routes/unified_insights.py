"""
Unified Insights API Routes
Single API surface for all insight operations across AI, user, and memory systems
"""

from fastapi import APIRouter, HTTPException, Query, Body, Depends, status, Request, BackgroundTasks
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

from unified_insight import (
    UnifiedInsight,
    UnifiedInsightResponse,
    InsightOrigin,
    InsightConfidenceLevel,
    InsightCategory,
    InsightSyncStatus
)
from services.unified_insights_orchestrator import unified_insights_orchestrator
from database import get_workspace
from middleware.trace_middleware import get_trace_id, create_traced_logger

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/insights", tags=["unified-insights"])

# Request/Response models
from pydantic import BaseModel, Field

class CreateInsightRequest(BaseModel):
    """Request model for creating a new insight"""
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    category: InsightCategory = Field(default=InsightCategory.GENERAL)
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.5)
    tags: Optional[List[str]] = None
    action_recommendations: Optional[List[str]] = None
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    comparison_baseline: Optional[str] = None
    related_goals: Optional[List[UUID]] = None
    metadata: Optional[Dict[str, Any]] = None

class UpdateInsightRequest(BaseModel):
    """Request model for updating an insight"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    category: Optional[InsightCategory] = None
    tags: Optional[List[str]] = None
    action_recommendations: Optional[List[str]] = None
    is_verified: Optional[bool] = None
    is_important: Optional[bool] = None
    is_outdated: Optional[bool] = None
    needs_review: Optional[bool] = None
    user_rating: Optional[float] = Field(None, ge=1.0, le=5.0)

class BulkUpdateRequest(BaseModel):
    """Request for bulk operations on insights"""
    insight_ids: List[UUID] = Field(..., min_items=1)
    operation: str = Field(..., description="Operation: verify, flag_important, flag_outdated, delete")
    value: Optional[bool] = Field(default=True)


# API Endpoints

@router.get("/{workspace_id}", response_model=UnifiedInsightResponse)
async def get_insights(
    workspace_id: UUID,
    request: Request,
    category: Optional[InsightCategory] = Query(None, description="Filter by category"),
    confidence_level: Optional[InsightConfidenceLevel] = Query(None, description="Filter by confidence level"),
    origin: Optional[InsightOrigin] = Query(None, description="Filter by origin"),
    search: Optional[str] = Query(None, description="Search in content and title"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    is_verified: Optional[bool] = Query(None, description="Filter verified insights"),
    is_important: Optional[bool] = Query(None, description="Filter important insights"),
    needs_review: Optional[bool] = Query(None, description="Filter insights needing review"),
    include_deleted: bool = Query(False, description="Include deleted insights"),
    force_refresh: bool = Query(False, description="Force cache refresh"),
    limit: int = Query(100, ge=1, le=500, description="Maximum insights to return"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """
    Get unified insights from all sources with intelligent aggregation.
    
    This endpoint:
    - Fetches from AI extraction, user management, and workspace memory
    - Deduplicates and merges insights
    - Applies filters and search
    - Returns paginated results with caching
    """
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Getting unified insights for workspace {workspace_id}", trace_id=trace_id)
    
    try:
        # Verify workspace exists
        workspace = await get_workspace(str(workspace_id))
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace {workspace_id} not found"
            )
        
        # Get unified insights
        response = await unified_insights_orchestrator.get_unified_insights(
            workspace_id=str(workspace_id),
            category=category.value if category else None,
            confidence_level=confidence_level.value if confidence_level else None,
            origin=origin.value if origin else None,
            include_deleted=include_deleted,
            force_refresh=force_refresh,
            limit=limit,
            offset=offset
        )
        
        # Apply additional filters if needed
        if search:
            # Filter by search term
            filtered_insights = [
                i for i in response.insights
                if search.lower() in i.content.lower() or search.lower() in i.title.lower()
            ]
            response.insights = filtered_insights
            response.total = len(filtered_insights)
        
        if tags:
            # Filter by tags
            filtered_insights = [
                i for i in response.insights
                if any(tag in i.tags for tag in tags)
            ]
            response.insights = filtered_insights
            response.total = len(filtered_insights)
        
        if is_verified is not None:
            filtered_insights = [i for i in response.insights if i.is_verified == is_verified]
            response.insights = filtered_insights
            response.total = len(filtered_insights)
        
        if is_important is not None:
            filtered_insights = [i for i in response.insights if i.is_important == is_important]
            response.insights = filtered_insights
            response.total = len(filtered_insights)
        
        if needs_review is not None:
            filtered_insights = [i for i in response.insights if i.needs_review == needs_review]
            response.insights = filtered_insights
            response.total = len(filtered_insights)
        
        # Update filters applied
        response.filters_applied.update({
            "search": search,
            "tags": tags,
            "is_verified": is_verified,
            "is_important": is_important,
            "needs_review": needs_review
        })
        
        logger.info(f"Returning {len(response.insights)} insights from {len(response.source_systems)} sources")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting insights: {e}", trace_id=trace_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get insights: {str(e)}"
        )


@router.post("/{workspace_id}", response_model=UnifiedInsight, status_code=status.HTTP_201_CREATED)
async def create_insight(
    workspace_id: UUID,
    request: Request,
    insight_data: CreateInsightRequest
):
    """Create a new user-managed insight"""
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
        
        # Get user ID from headers (in production, from JWT)
        user_id = request.headers.get("X-User-Id", "default_user")
        
        # Create unified insight
        insight = UnifiedInsight(
            workspace_id=workspace_id,
            origin=InsightOrigin.USER_CREATED,
            title=insight_data.title,
            content=insight_data.content,
            category=insight_data.category,
            confidence_score=insight_data.confidence_score,
            confidence_level=UnifiedInsight(
                workspace_id=workspace_id,
                origin=InsightOrigin.USER_CREATED,
                title="temp",
                content="temp",
                category=InsightCategory.GENERAL,
                confidence_level=InsightConfidenceLevel.MODERATE,
                confidence_score=insight_data.confidence_score
            ).calculate_confidence_level(),
            created_by=user_id,
            tags=insight_data.tags or [],
            action_recommendations=insight_data.action_recommendations or [],
            metric_name=insight_data.metric_name,
            metric_value=insight_data.metric_value,
            comparison_baseline=insight_data.comparison_baseline,
            related_goals=insight_data.related_goals or [],
            metadata=insight_data.metadata or {},
            business_value_score=insight_data.confidence_score * 0.8,
            actionability_score=0.7 if insight_data.action_recommendations else 0.5
        )
        
        # Persist to database
        from database import get_supabase_client
        client = get_supabase_client()
        
        record = {
            'id': str(insight.id),
            'workspace_id': str(insight.workspace_id),
            'title': insight.title,
            'content': insight.content,
            'category': insight.category.value,
            'domain_type': insight.domain_context or 'general',
            'confidence_score': insight.confidence_score,
            'business_value_score': insight.business_value_score,
            'created_by': insight.created_by,
            'created_at': insight.created_at.isoformat(),
            'updated_at': insight.updated_at.isoformat(),
            'is_user_created': True,
            'is_user_modified': False,
            'is_deleted': False,
            'version_number': 1,
            'user_flags': {
                'verified': False,
                'important': False,
                'outdated': False,
                'needs_review': False
            },
            'tags': insight.tags,
            'recommendations': insight.action_recommendations,
            'metadata': {
                **insight.metadata,
                'metric_name': insight.metric_name,
                'metric_value': insight.metric_value,
                'comparison_baseline': insight.comparison_baseline,
                'related_goals': [str(g) for g in insight.related_goals]
            }
        }
        
        result = client.table('workspace_insights').insert(record).execute()
        
        # Invalidate cache
        if str(workspace_id) in unified_insights_orchestrator.workspace_caches:
            unified_insights_orchestrator.workspace_caches[str(workspace_id)].invalidate()
        
        logger.info(f"Created insight {insight.id} for workspace {workspace_id}")
        return insight
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating insight: {e}", trace_id=trace_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create insight: {str(e)}"
        )


@router.put("/{workspace_id}/{insight_id}", response_model=UnifiedInsight)
async def update_insight(
    workspace_id: UUID,
    insight_id: UUID,
    request: Request,
    updates: UpdateInsightRequest
):
    """Update an existing insight"""
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Updating insight {insight_id} in workspace {workspace_id}", trace_id=trace_id)
    
    try:
        # Get user ID
        user_id = request.headers.get("X-User-Id", "default_user")
        
        # Fetch existing insight
        from database import get_supabase_client
        client = get_supabase_client()
        
        existing = client.table('workspace_insights').select('*').eq(
            'id', str(insight_id)
        ).eq('workspace_id', str(workspace_id)).execute()
        
        if not existing.data:
            # Check if it's an AI insight that needs to be persisted first
            unified_response = await unified_insights_orchestrator.get_unified_insights(
                str(workspace_id), force_refresh=True
            )
            
            ai_insight = next((i for i in unified_response.insights if str(i.id) == str(insight_id)), None)
            
            if not ai_insight:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Insight {insight_id} not found"
                )
            
            # Persist AI insight first
            record = {
                'id': str(ai_insight.id),
                'workspace_id': str(workspace_id),
                'title': updates.title or ai_insight.title,
                'content': updates.content or ai_insight.content,
                'category': updates.category.value if updates.category else ai_insight.category.value,
                'confidence_score': ai_insight.confidence_score,
                'business_value_score': ai_insight.business_value_score,
                'created_by': 'ai_system',
                'created_at': ai_insight.created_at.isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'updated_by': user_id,
                'is_user_created': False,
                'is_user_modified': True,
                'is_deleted': False,
                'version_number': 1,
                'user_flags': {
                    'verified': updates.is_verified or False,
                    'important': updates.is_important or False,
                    'outdated': updates.is_outdated or False,
                    'needs_review': updates.needs_review or False
                },
                'tags': updates.tags or ai_insight.tags,
                'recommendations': updates.action_recommendations or ai_insight.action_recommendations,
                'metadata': ai_insight.metadata
            }
            
            result = client.table('workspace_insights').insert(record).execute()
        else:
            # Update existing record
            record = existing.data[0]
            
            update_data = {
                'updated_at': datetime.utcnow().isoformat(),
                'updated_by': user_id,
                'is_user_modified': True,
                'version_number': record['version_number'] + 1
            }
            
            if updates.title:
                update_data['title'] = updates.title
            if updates.content:
                update_data['content'] = updates.content
            if updates.category:
                update_data['category'] = updates.category.value
            if updates.tags is not None:
                update_data['tags'] = updates.tags
            if updates.action_recommendations is not None:
                update_data['recommendations'] = updates.action_recommendations
            
            # Update flags
            user_flags = record.get('user_flags', {})
            if updates.is_verified is not None:
                user_flags['verified'] = updates.is_verified
            if updates.is_important is not None:
                user_flags['important'] = updates.is_important
            if updates.is_outdated is not None:
                user_flags['outdated'] = updates.is_outdated
            if updates.needs_review is not None:
                user_flags['needs_review'] = updates.needs_review
            update_data['user_flags'] = user_flags
            
            if updates.user_rating is not None:
                metadata = record.get('metadata', {})
                metadata['user_rating'] = updates.user_rating
                update_data['metadata'] = metadata
            
            result = client.table('workspace_insights').update(update_data).eq(
                'id', str(insight_id)
            ).execute()
        
        # Invalidate cache
        if str(workspace_id) in unified_insights_orchestrator.workspace_caches:
            unified_insights_orchestrator.workspace_caches[str(workspace_id)].invalidate()
        
        # Return updated insight
        updated_record = result.data[0]
        return unified_insights_orchestrator._convert_user_insight(updated_record)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating insight: {e}", trace_id=trace_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update insight: {str(e)}"
        )


@router.delete("/{workspace_id}/{insight_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_insight(
    workspace_id: UUID,
    insight_id: UUID,
    request: Request,
    permanent: bool = Query(False, description="Permanently delete (no soft delete)")
):
    """Delete an insight (soft delete by default)"""
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Deleting insight {insight_id} from workspace {workspace_id}", trace_id=trace_id)
    
    try:
        from database import get_supabase_client
        client = get_supabase_client()
        
        if permanent:
            # Hard delete
            result = client.table('workspace_insights').delete().eq(
                'id', str(insight_id)
            ).eq('workspace_id', str(workspace_id)).execute()
        else:
            # Soft delete
            result = client.table('workspace_insights').update({
                'is_deleted': True,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', str(insight_id)).eq('workspace_id', str(workspace_id)).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Insight {insight_id} not found"
            )
        
        # Invalidate cache
        if str(workspace_id) in unified_insights_orchestrator.workspace_caches:
            unified_insights_orchestrator.workspace_caches[str(workspace_id)].invalidate()
        
        logger.info(f"Deleted insight {insight_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting insight: {e}", trace_id=trace_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete insight: {str(e)}"
        )


@router.post("/{workspace_id}/bulk", status_code=status.HTTP_200_OK)
async def bulk_update_insights(
    workspace_id: UUID,
    request: Request,
    bulk_request: BulkUpdateRequest
):
    """Perform bulk operations on multiple insights"""
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Bulk {bulk_request.operation} on {len(bulk_request.insight_ids)} insights", trace_id=trace_id)
    
    try:
        from database import get_supabase_client
        client = get_supabase_client()
        
        user_id = request.headers.get("X-User-Id", "default_user")
        updated_count = 0
        
        for insight_id in bulk_request.insight_ids:
            try:
                if bulk_request.operation == "delete":
                    result = client.table('workspace_insights').update({
                        'is_deleted': bulk_request.value,
                        'updated_at': datetime.utcnow().isoformat()
                    }).eq('id', str(insight_id)).eq('workspace_id', str(workspace_id)).execute()
                    
                elif bulk_request.operation == "verify":
                    result = client.table('workspace_insights').select('user_flags').eq(
                        'id', str(insight_id)
                    ).execute()
                    
                    if result.data:
                        flags = result.data[0].get('user_flags', {})
                        flags['verified'] = bulk_request.value
                        
                        client.table('workspace_insights').update({
                            'user_flags': flags,
                            'updated_at': datetime.utcnow().isoformat(),
                            'updated_by': user_id
                        }).eq('id', str(insight_id)).execute()
                
                elif bulk_request.operation == "flag_important":
                    result = client.table('workspace_insights').select('user_flags').eq(
                        'id', str(insight_id)
                    ).execute()
                    
                    if result.data:
                        flags = result.data[0].get('user_flags', {})
                        flags['important'] = bulk_request.value
                        
                        client.table('workspace_insights').update({
                            'user_flags': flags,
                            'updated_at': datetime.utcnow().isoformat(),
                            'updated_by': user_id
                        }).eq('id', str(insight_id)).execute()
                
                elif bulk_request.operation == "flag_outdated":
                    result = client.table('workspace_insights').select('user_flags').eq(
                        'id', str(insight_id)
                    ).execute()
                    
                    if result.data:
                        flags = result.data[0].get('user_flags', {})
                        flags['outdated'] = bulk_request.value
                        
                        client.table('workspace_insights').update({
                            'user_flags': flags,
                            'updated_at': datetime.utcnow().isoformat(),
                            'updated_by': user_id
                        }).eq('id', str(insight_id)).execute()
                
                updated_count += 1
                
            except Exception as e:
                logger.error(f"Failed to update insight {insight_id}: {e}")
        
        # Invalidate cache
        if str(workspace_id) in unified_insights_orchestrator.workspace_caches:
            unified_insights_orchestrator.workspace_caches[str(workspace_id)].invalidate()
        
        return {
            "status": "success",
            "updated_count": updated_count,
            "total_requested": len(bulk_request.insight_ids)
        }
        
    except Exception as e:
        logger.error(f"Error in bulk update: {e}", trace_id=trace_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk update: {str(e)}"
        )


@router.get("/{workspace_id}/sync-status", response_model=InsightSyncStatus)
async def get_sync_status(
    workspace_id: UUID,
    request: Request
):
    """Get synchronization status between all insight systems"""
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Getting sync status for workspace {workspace_id}", trace_id=trace_id)
    
    try:
        status = await unified_insights_orchestrator.get_sync_status(str(workspace_id))
        return status
        
    except Exception as e:
        logger.error(f"Error getting sync status: {e}", trace_id=trace_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync status: {str(e)}"
        )


@router.post("/{workspace_id}/persist-ai-insights", status_code=status.HTTP_202_ACCEPTED)
async def persist_ai_insights(
    workspace_id: UUID,
    request: Request,
    background_tasks: BackgroundTasks
):
    """Trigger background job to persist valuable AI insights"""
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Triggering AI insight persistence for workspace {workspace_id}", trace_id=trace_id)
    
    try:
        # Add background task
        background_tasks.add_task(
            unified_insights_orchestrator.persist_valuable_insights,
            str(workspace_id)
        )
        
        return {
            "status": "accepted",
            "message": "Background job triggered to persist valuable AI insights"
        }
        
    except Exception as e:
        logger.error(f"Error triggering persistence: {e}", trace_id=trace_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger persistence: {str(e)}"
        )