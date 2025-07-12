"""
Memory API Routes - Pillar 6: Memory System
RESTful endpoints for memory context, learning patterns, and insights.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from uuid import UUID
from fastapi import Request, APIRouter, HTTPException
from middleware.trace_middleware import get_trace_id, create_traced_logger, TracedDatabaseOperation
from pydantic import BaseModel, Field

from backend.services.unified_memory_engine import memory_system

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/memory", tags=["memory"])

# Request/Response Models
class ContextCreate(BaseModel):
    workspace_id: UUID
    context: str
    importance: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    context_type: str = "general"
    metadata: Optional[Dict[str, Any]] = {}

class ContextQuery(BaseModel):
    workspace_id: UUID
    query: str
    limit: int = Field(default=10, ge=1, le=50)

class ContextResponse(BaseModel):
    id: str
    workspace_id: str
    context: str
    context_type: str
    importance: str
    importance_score: float
    created_at: str
    relevance_score: Optional[float] = None

class MemoryInsightsResponse(BaseModel):
    total_context_entries: int
    high_importance_entries: int
    learning_patterns: List[Dict[str, Any]]
    context_types: Dict[str, int]
    memory_health: Dict[str, Any]
    retention_rate: float

# === MEMORY CONTEXT ENDPOINTS ===

@router.post("/context", response_model=str)
async def store_memory_context(context_data: ContextCreate, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route store_memory_context called", endpoint="store_memory_context", trace_id=trace_id)

    """Store context in memory system"""
    try:
        logger.info(f"💾 Storing context for workspace: {context_data.workspace_id}")
        
        context_id = await memory_system.store_context(
            workspace_id=context_data.workspace_id,
            context=context_data.context,
            importance=context_data.importance,
            context_type=context_data.context_type,
            metadata=context_data.metadata
        )
        
        logger.info(f"✅ Context stored with ID: {context_id}")
        return context_id
        
    except Exception as e:
        logger.error(f"Failed to store context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/context/search", response_model=List[ContextResponse])
async def search_memory_context(query_data: ContextQuery, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route search_memory_context called", endpoint="search_memory_context", trace_id=trace_id)

    """Search memory context with semantic matching"""
    try:
        logger.info(f"🔍 Searching context for workspace: {query_data.workspace_id}")
        
        contexts = await memory_system.retrieve_context(
            workspace_id=query_data.workspace_id,
            query=query_data.query,
            limit=query_data.limit
        )
        
        # Convert to response format
        response_contexts = []
        for context in contexts:
            response_contexts.append(ContextResponse(
                id=context["id"],
                workspace_id=context["workspace_id"],
                context=context["context"],
                context_type=context["context_type"],
                importance=context["importance"],
                importance_score=context["importance_score"],
                created_at=context["created_at"],
                relevance_score=context.get("relevance_score")
            ))
        
        logger.info(f"✅ Found {len(response_contexts)} relevant contexts")
        return response_contexts
        
    except Exception as e:
        logger.error(f"Failed to search context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/context/{workspace_id}", response_model=List[ContextResponse])
async def get_workspace_memory_context(request: Request, workspace_id: UUID, limit: int = 20):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_workspace_memory_context called", endpoint="get_workspace_memory_context", trace_id=trace_id)

    """Get recent memory context for workspace"""
    try:
        logger.info(f"📋 Getting memory context for workspace: {workspace_id}")
        
        # Use empty query to get recent contexts by importance
        contexts = await memory_system.retrieve_context(
            workspace_id=workspace_id,
            query="",  # Empty query returns by importance
            limit=limit
        )
        
        response_contexts = []
        for context in contexts:
            response_contexts.append(ContextResponse(
                id=context["id"],
                workspace_id=context["workspace_id"],
                context=context["context"],
                context_type=context["context_type"],
                importance=context["importance"],
                importance_score=context["importance_score"],
                created_at=context["created_at"]
            ))
        
        logger.info(f"✅ Retrieved {len(response_contexts)} contexts")
        return response_contexts
        
    except Exception as e:
        logger.error(f"Failed to get workspace context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === MEMORY INSIGHTS ENDPOINTS ===

@router.get("/insights/{workspace_id}", response_model=MemoryInsightsResponse)
async def get_workspace_memory_insights(workspace_id: UUID, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_workspace_memory_insights called", endpoint="get_workspace_memory_insights", trace_id=trace_id)

    """Get comprehensive memory insights for workspace"""
    try:
        logger.info(f"🧠 Getting memory insights for workspace: {workspace_id}")
        
        insights = await memory_system.get_memory_insights(workspace_id)
        
        if not insights:
            # Return empty insights if none available
            insights = {
                "total_context_entries": 0,
                "high_importance_entries": 0,
                "learning_patterns": [],
                "context_types": {},
                "memory_health": {"score": 0.0, "status": "empty"},
                "retention_rate": 0.0
            }
        
        logger.info(f"✅ Generated memory insights")
        return MemoryInsightsResponse(**insights)
        
    except Exception as e:
        logger.error(f"Failed to get memory insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === LEARNING PATTERNS ENDPOINTS ===

@router.get("/learning-patterns/{workspace_id}")
async def get_workspace_learning_patterns(workspace_id: UUID, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_workspace_learning_patterns called", endpoint="get_workspace_learning_patterns", trace_id=trace_id)

    """Get learning patterns for workspace"""
    try:
        logger.info(f"📊 Getting learning patterns for workspace: {workspace_id}")
        
        insights = await memory_system.get_memory_insights(workspace_id)
        patterns = insights.get("learning_patterns", [])
        
        # Enhance patterns with analysis
        enhanced_patterns = []
        for pattern in patterns:
            enhanced_patterns.append({
                **pattern,
                "strength_level": _get_strength_level(pattern.get("pattern_strength", 0)),
                "trend": _calculate_pattern_trend(pattern),
                "actionable_insights": _generate_pattern_insights(pattern)
            })
        
        logger.info(f"✅ Retrieved {len(enhanced_patterns)} learning patterns")
        return {
            "workspace_id": str(workspace_id),
            "patterns": enhanced_patterns,
            "pattern_summary": _summarize_patterns(enhanced_patterns)
        }
        
    except Exception as e:
        logger.error(f"Failed to get learning patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === MEMORY HEALTH ENDPOINTS ===

@router.get("/health/{workspace_id}")
async def get_memory_system_health(workspace_id: UUID, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_memory_system_health called", endpoint="get_memory_system_health", trace_id=trace_id)

    """Get memory system health status"""
    try:
        logger.info(f"🏥 Checking memory health for workspace: {workspace_id}")
        
        insights = await memory_system.get_memory_insights(workspace_id)
        
        health_data = {
            "workspace_id": str(workspace_id),
            "timestamp": datetime.utcnow().isoformat(),
            "memory_health": insights.get("memory_health", {"score": 0.0, "status": "unknown"}),
            "retention_rate": insights.get("retention_rate", 0.0),
            "context_count": insights.get("total_context_entries", 0),
            "high_value_contexts": insights.get("high_importance_entries", 0),
            "recommendations": _generate_health_recommendations(insights)
        }
        
        logger.info(f"✅ Memory health check completed")
        return health_data
        
    except Exception as e:
        logger.error(f"Failed to check memory health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === HELPER FUNCTIONS ===

def _get_strength_level(strength: float) -> str:
    """Convert numeric strength to descriptive level"""
    if strength >= 0.8:
        return "very_strong"
    elif strength >= 0.6:
        return "strong"
    elif strength >= 0.4:
        return "moderate"
    elif strength >= 0.2:
        return "weak"
    else:
        return "very_weak"

def _calculate_pattern_trend(pattern: Dict[str, Any]) -> str:
    """Calculate pattern trend (simplified)"""
    # This would be more sophisticated with time series data
    strength = pattern.get("pattern_strength", 0)
    count = pattern.get("occurrence_count", 0)
    
    if count > 10 and strength > 0.6:
        return "increasing"
    elif count > 5 and strength > 0.3:
        return "stable"
    else:
        return "emerging"

def _generate_pattern_insights(pattern: Dict[str, Any]) -> List[str]:
    """Generate actionable insights from pattern"""
    insights = []
    
    pattern_type = pattern.get("pattern_type", "")
    strength = pattern.get("pattern_strength", 0)
    
    if "frequency" in pattern_type and strength > 0.7:
        insights.append(f"High frequency pattern detected - consider optimization")
    
    if strength > 0.8:
        insights.append("Strong pattern - leverage for automation opportunities")
    
    if strength < 0.3:
        insights.append("Weak pattern - may need more data or different approach")
    
    return insights

def _summarize_patterns(patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Summarize pattern analysis"""
    if not patterns:
        return {"status": "no_patterns", "summary": "No patterns detected yet"}
    
    strong_patterns = len([p for p in patterns if p.get("pattern_strength", 0) > 0.6])
    total_patterns = len(patterns)
    
    return {
        "total_patterns": total_patterns,
        "strong_patterns": strong_patterns,
        "pattern_strength_avg": sum(p.get("pattern_strength", 0) for p in patterns) / total_patterns,
        "status": "healthy" if strong_patterns > 0 else "developing"
    }

def _generate_health_recommendations(insights: Dict[str, Any]) -> List[str]:
    """Generate memory health recommendations"""
    recommendations = []
    
    health = insights.get("memory_health", {})
    status = health.get("status", "unknown")
    score = health.get("score", 0.0)
    
    if status == "empty":
        recommendations.append("Start storing context to build memory foundation")
    elif status == "poor":
        recommendations.append("Increase context diversity and importance scoring")
    elif score < 0.5:
        recommendations.append("Focus on storing high-value, actionable context")
    
    retention_rate = insights.get("retention_rate", 0.0)
    if retention_rate < 0.7:
        recommendations.append("Consider extending memory retention period")
    
    context_count = insights.get("total_context_entries", 0)
    if context_count > 100:
        recommendations.append("Memory system is well-populated - focus on quality")
    
    return recommendations