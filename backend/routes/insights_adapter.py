"""
Insights API Adapter
Provides backward compatibility for existing frontend components while they migrate to unified API
Maps legacy endpoints to unified insights orchestrator
"""

from fastapi import APIRouter, HTTPException, Query, Request, status
from typing import Dict, Any, List, Optional
from uuid import UUID
import logging

from services.unified_insights_orchestrator import unified_insights_orchestrator
from unified_insight import InsightOrigin, InsightCategory
from middleware.trace_middleware import get_trace_id, create_traced_logger

logger = logging.getLogger(__name__)
router = APIRouter(tags=["insights-adapter"])


@router.get("/content-learning/insights/{workspace_id}")
async def get_content_learning_insights_adapter(
    workspace_id: str,
    request: Request
) -> Dict[str, Any]:
    """
    Adapter for legacy /api/content-learning/insights/ endpoint.
    Maps to unified insights with AI origin filter.
    """
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Legacy content-learning adapter called for {workspace_id}", trace_id=trace_id)
    
    try:
        # Get AI-generated insights from unified orchestrator
        response = await unified_insights_orchestrator.get_unified_insights(
            workspace_id=workspace_id,
            origin=InsightOrigin.AI_GENERATED.value,
            force_refresh=True,  # Always refresh for AI insights
            limit=100
        )
        
        # Convert to legacy format
        actionable_insights = []
        for insight in response.insights:
            # Format as legacy string format
            formatted = insight.to_display_format()
            actionable_insights.append(formatted)
        
        # Calculate category counts (though they're not properly used in legacy)
        high_count = len([i for i in response.insights if i.confidence_score >= 0.8])
        moderate_count = len([i for i in response.insights if 0.6 <= i.confidence_score < 0.8])
        exploratory_count = len([i for i in response.insights if i.confidence_score < 0.6])
        
        legacy_response = {
            "workspace_id": workspace_id,
            "domain_filter": None,
            "insights_count": len(actionable_insights),
            "actionable_insights": actionable_insights,
            "insight_categories": {
                "high_confidence": high_count,
                "moderate_confidence": moderate_count,
                "exploratory": exploratory_count
            }
        }
        
        logger.info(f"Returning {len(actionable_insights)} insights in legacy format")
        return legacy_response
        
    except Exception as e:
        logger.error(f"Error in content-learning adapter: {e}", trace_id=trace_id)
        # Return empty response to maintain compatibility
        return {
            "workspace_id": workspace_id,
            "domain_filter": None,
            "insights_count": 0,
            "actionable_insights": [],
            "insight_categories": {
                "high_confidence": 0,
                "moderate_confidence": 0,
                "exploratory": 0
            }
        }


@router.get("/user-insights/{workspace_id}/insights")
async def get_user_insights_adapter(
    workspace_id: str,
    request: Request,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    Adapter for legacy /api/user-insights/{workspace_id}/insights endpoint.
    Maps to unified insights with user origin filter.
    """
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Legacy user-insights adapter called for {workspace_id}", trace_id=trace_id)
    
    try:
        # Get all insights from unified orchestrator
        response = await unified_insights_orchestrator.get_unified_insights(
            workspace_id=workspace_id,
            category=category,
            limit=limit,
            offset=offset,
            force_refresh=False  # Use cache for user insights
        )
        
        # Convert to legacy user insights format
        legacy_insights = []
        for insight in response.insights:
            # Convert to management format
            legacy_insight = insight.to_management_format()
            legacy_insights.append(legacy_insight)
        
        legacy_response = {
            "insights": legacy_insights,
            "total": response.total,
            "offset": offset,
            "limit": limit
        }
        
        logger.info(f"Returning {len(legacy_insights)} insights in legacy user format")
        return legacy_response
        
    except Exception as e:
        logger.error(f"Error in user-insights adapter: {e}", trace_id=trace_id)
        # Return empty response to maintain compatibility
        return {
            "insights": [],
            "total": 0,
            "offset": offset,
            "limit": limit
        }


@router.get("/conversation/workspaces/{workspace_id}/knowledge-insights")
async def get_conversation_knowledge_adapter(
    workspace_id: str,
    request: Request
) -> Dict[str, Any]:
    """
    Adapter for legacy /api/conversation/workspaces/{workspace_id}/knowledge-insights endpoint.
    Maps to unified insights with artifact formatting.
    """
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Legacy conversation knowledge adapter called for {workspace_id}", trace_id=trace_id)
    
    try:
        # Get all insights from unified orchestrator
        response = await unified_insights_orchestrator.get_unified_insights(
            workspace_id=workspace_id,
            limit=100,
            force_refresh=False
        )
        
        # Categorize insights for artifact display
        discoveries = []
        best_practices = []
        learnings = []
        
        for insight in response.insights:
            artifact_format = insight.to_artifact_format()
            
            if insight.category in [InsightCategory.DISCOVERY, InsightCategory.OPPORTUNITY]:
                discoveries.append(artifact_format)
            elif insight.category in [InsightCategory.PERFORMANCE, InsightCategory.OPTIMIZATION]:
                best_practices.append(artifact_format)
            elif insight.category in [InsightCategory.CONSTRAINT, InsightCategory.RISK]:
                learnings.append(artifact_format)
            else:
                # Default to discoveries for general insights
                discoveries.append(artifact_format)
        
        # Create summary data
        summary = {
            "recent_discoveries": [i['content'][:100] for i in discoveries[:5]],
            "key_constraints": [i['content'][:100] for i in learnings[:5]],
            "success_patterns": [i['content'][:100] for i in best_practices[:5]],
            "top_tags": []  # Extract unique tags from all insights
        }
        
        # Collect all tags
        all_tags = []
        for insight in response.insights:
            all_tags.extend(insight.tags)
        
        # Get unique tags
        unique_tags = list(set(all_tags))[:10]
        summary["top_tags"] = unique_tags
        
        legacy_response = {
            "workspace_id": workspace_id,
            "total_insights": response.total,
            "insights": discoveries,
            "bestPractices": best_practices,
            "learnings": learnings,
            "summary": summary
        }
        
        logger.info(f"Returning knowledge insights in legacy artifact format")
        return legacy_response
        
    except Exception as e:
        logger.error(f"Error in conversation knowledge adapter: {e}", trace_id=trace_id)
        # Return empty response to maintain compatibility
        return {
            "workspace_id": workspace_id,
            "total_insights": 0,
            "insights": [],
            "bestPractices": [],
            "learnings": [],
            "summary": {
                "recent_discoveries": [],
                "key_constraints": [],
                "success_patterns": [],
                "top_tags": []
            }
        }


# Register adapters for smooth transition
def register_legacy_adapters(app):
    """Register all legacy adapters on the FastAPI app"""
    app.include_router(router, prefix="/api")
    logger.info("Legacy insights adapters registered for backward compatibility")