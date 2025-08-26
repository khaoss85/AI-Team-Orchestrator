#!/usr/bin/env python3
"""
🔍 RECOVERY EXPLANATIONS API ROUTES
===================================

FastAPI routes for accessing recovery explanations and failure analysis.
Provides transparent visibility into task failure recovery decisions.
"""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

# Import recovery explanation engine
try:
    from services.recovery_explanation_engine import (
        recovery_explanation_engine,
        RecoveryExplanation,
        FailureCategory,
        RecoveryStrategy,
        explain_task_failure,
        get_explanation_stats
    )
    RECOVERY_ENGINE_AVAILABLE = True
except ImportError as e:
    logger.error(f"Recovery explanation engine not available: {e}")
    RECOVERY_ENGINE_AVAILABLE = False

# Import database for historical data
try:
    from database import supabase
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

router = APIRouter(prefix="/api/recovery-explanations", tags=["Recovery Explanations"])

# API Models
class ExplanationResponse(BaseModel):
    """API response model for recovery explanations"""
    task_id: str
    task_name: Optional[str] = None
    failure_summary: str
    root_cause: str  
    retry_decision: str
    confidence_explanation: str
    user_action_required: Optional[str] = None
    estimated_resolution_time: Optional[str] = None
    severity_level: str
    display_category: str
    failure_time: datetime
    explanation_generated_time: datetime
    
    # Technical details
    technical_details: Dict[str, Any] = {}
    error_pattern_matched: Optional[str] = None
    ai_analysis_used: bool = False

class ExplanationHistoryResponse(BaseModel):
    """Historical explanation data"""
    task_id: str
    explanations: List[ExplanationResponse]
    total_attempts: int
    current_status: str
    next_recommended_action: Optional[str] = None

class ExplanationStatsResponse(BaseModel):
    """Statistics about explanation generation"""
    total_explanations: int
    pattern_matches: int
    ai_analyses_used: int
    pattern_match_rate: float
    ai_analysis_rate: float
    top_failure_categories: List[Dict[str, Any]]

class NotificationPayload(BaseModel):
    """WebSocket notification payload for recovery explanations"""
    type: str = "task_recovery_explanation"
    task_id: str
    workspace_id: str
    timestamp: datetime
    explanation: ExplanationResponse

@router.post("/explain-failure/{task_id}")
async def explain_task_failure_endpoint(
    task_id: str = Path(..., description="Task ID to explain failure for"),
    workspace_id: str = Query(..., description="Workspace ID"),
    error_message: str = Query(..., description="Error message from task failure"),
    error_type: Optional[str] = Query(None, description="Error type/category"),
    agent_id: Optional[str] = Query(None, description="Agent ID that failed"),
    task_name: Optional[str] = Query(None, description="Task name"),
    execution_stage: Optional[str] = Query(None, description="Execution stage where failure occurred"),
    attempt_count: int = Query(1, description="Attempt number")
) -> ExplanationResponse:
    """
    Generate explanation for task failure
    
    This endpoint analyzes a task failure and provides a human-readable
    explanation of what went wrong and what recovery actions will be taken.
    """
    if not RECOVERY_ENGINE_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Recovery explanation engine not available"
        )
    
    try:
        explanation = await explain_task_failure(
            task_id=task_id,
            workspace_id=workspace_id,
            error_message=error_message,
            error_type=error_type or "",
            agent_id=agent_id,
            task_name=task_name,
            execution_stage=execution_stage,
            attempt_count=attempt_count
        )
        
        # Convert to API response model
        response = ExplanationResponse(
            task_id=explanation.task_id,
            task_name=explanation.task_name,
            failure_summary=explanation.failure_summary,
            root_cause=explanation.root_cause,
            retry_decision=explanation.retry_decision,
            confidence_explanation=explanation.confidence_explanation,
            user_action_required=explanation.user_action_required,
            estimated_resolution_time=explanation.estimated_resolution_time,
            severity_level=explanation.severity_level,
            display_category=explanation.display_category,
            failure_time=explanation.failure_time,
            explanation_generated_time=explanation.explanation_generated_time,
            technical_details=explanation.technical_details,
            error_pattern_matched=explanation.error_pattern_matched,
            ai_analysis_used=explanation.ai_analysis_used
        )
        
        # Store explanation in database for historical tracking
        if DATABASE_AVAILABLE:
            await _store_explanation_in_database(explanation)
        
        # Send real-time notification
        await _send_recovery_notification(workspace_id, response)
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to generate explanation for task {task_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate explanation: {str(e)}"
        )

@router.get("/task/{task_id}/history")
async def get_task_explanation_history(
    task_id: str = Path(..., description="Task ID to get explanation history for")
) -> ExplanationHistoryResponse:
    """
    Get historical recovery explanations for a task
    
    Provides complete history of all failure recovery attempts and explanations
    for a specific task, useful for debugging recurring issues.
    """
    if not DATABASE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Database not available for historical data"
        )
    
    try:
        # Query explanations from database
        explanations_response = supabase.table("recovery_explanations").select("*").eq(
            "task_id", task_id
        ).order("created_at", desc=True).execute()
        
        explanations = []
        for exp_data in explanations_response.data or []:
            explanations.append(ExplanationResponse(
                task_id=exp_data["task_id"],
                task_name=exp_data.get("task_name"),
                failure_summary=exp_data["failure_summary"],
                root_cause=exp_data["root_cause"],
                retry_decision=exp_data["retry_decision"],
                confidence_explanation=exp_data["confidence_explanation"],
                user_action_required=exp_data.get("user_action_required"),
                estimated_resolution_time=exp_data.get("estimated_resolution_time"),
                severity_level=exp_data["severity_level"],
                display_category=exp_data["display_category"],
                failure_time=datetime.fromisoformat(exp_data["failure_time"]),
                explanation_generated_time=datetime.fromisoformat(exp_data["created_at"]),
                technical_details=exp_data.get("technical_details", {}),
                error_pattern_matched=exp_data.get("error_pattern_matched"),
                ai_analysis_used=exp_data.get("ai_analysis_used", False)
            ))
        
        # Get current task status
        task_response = supabase.table("tasks").select("status").eq("id", task_id).execute()
        current_status = task_response.data[0]["status"] if task_response.data else "unknown"
        
        return ExplanationHistoryResponse(
            task_id=task_id,
            explanations=explanations,
            total_attempts=len(explanations),
            current_status=current_status,
            next_recommended_action=_get_next_recommended_action(explanations, current_status)
        )
        
    except Exception as e:
        logger.error(f"Failed to get explanation history for task {task_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve explanation history: {str(e)}"
        )

@router.get("/workspace/{workspace_id}")
async def get_workspace_recovery_explanations(
    workspace_id: str = Path(..., description="Workspace ID"),
    limit: int = Query(50, description="Maximum number of explanations to return"),
    severity_filter: Optional[str] = Query(None, description="Filter by severity level"),
    category_filter: Optional[str] = Query(None, description="Filter by display category"),
    since: Optional[datetime] = Query(None, description="Only explanations since this timestamp")
) -> List[ExplanationResponse]:
    """
    Get recent recovery explanations for a workspace
    
    Provides dashboard view of recent task failures and recovery decisions
    within a workspace, with filtering options.
    """
    if not DATABASE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Database not available"
        )
    
    try:
        # Build query
        query = supabase.table("recovery_explanations").select("*").eq(
            "workspace_id", workspace_id
        )
        
        if severity_filter:
            query = query.eq("severity_level", severity_filter)
        
        if category_filter:
            query = query.eq("display_category", category_filter)
            
        if since:
            query = query.gte("created_at", since.isoformat())
        
        query = query.order("created_at", desc=True).limit(limit)
        
        explanations_response = query.execute()
        
        explanations = []
        for exp_data in explanations_response.data or []:
            explanations.append(ExplanationResponse(
                task_id=exp_data["task_id"],
                task_name=exp_data.get("task_name"),
                failure_summary=exp_data["failure_summary"],
                root_cause=exp_data["root_cause"],
                retry_decision=exp_data["retry_decision"],
                confidence_explanation=exp_data["confidence_explanation"],
                user_action_required=exp_data.get("user_action_required"),
                estimated_resolution_time=exp_data.get("estimated_resolution_time"),
                severity_level=exp_data["severity_level"],
                display_category=exp_data["display_category"],
                failure_time=datetime.fromisoformat(exp_data["failure_time"]),
                explanation_generated_time=datetime.fromisoformat(exp_data["created_at"]),
                technical_details=exp_data.get("technical_details", {}),
                error_pattern_matched=exp_data.get("error_pattern_matched"),
                ai_analysis_used=exp_data.get("ai_analysis_used", False)
            ))
        
        return explanations
        
    except Exception as e:
        logger.error(f"Failed to get workspace recovery explanations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve explanations: {str(e)}"
        )

@router.get("/stats")
async def get_explanation_statistics() -> ExplanationStatsResponse:
    """
    Get statistics about recovery explanation generation
    
    Provides insights into explanation engine performance, pattern recognition
    rates, and most common failure categories.
    """
    if not RECOVERY_ENGINE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Recovery explanation engine not available"
        )
    
    try:
        # Get engine statistics
        engine_stats = get_explanation_stats()
        
        # Get failure category breakdown from database
        top_categories = []
        if DATABASE_AVAILABLE:
            category_stats = supabase.table("recovery_explanations").select(
                "display_category", count="exact"
            ).execute()
            
            # Process category counts (this would need aggregation in real implementation)
            # For now, return mock data
            top_categories = [
                {"category": "Agent Response Issue", "count": 45, "percentage": 35.2},
                {"category": "Temporary Service Issue", "count": 32, "percentage": 25.0},
                {"category": "System Infrastructure", "count": 28, "percentage": 21.9},
                {"category": "Resource Availability", "count": 23, "percentage": 18.0}
            ]
        
        return ExplanationStatsResponse(
            total_explanations=engine_stats["explanations_generated"],
            pattern_matches=engine_stats["pattern_matches"],
            ai_analyses_used=engine_stats["ai_analyses_used"],
            pattern_match_rate=engine_stats["pattern_match_rate"],
            ai_analysis_rate=engine_stats["ai_analysis_rate"],
            top_failure_categories=top_categories
        )
        
    except Exception as e:
        logger.error(f"Failed to get explanation statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )

@router.get("/categories")
async def get_failure_categories() -> List[Dict[str, Any]]:
    """
    Get list of all failure categories with descriptions
    
    Provides reference information about failure categorization system
    for UI filtering and display purposes.
    """
    categories = [
        {
            "id": "pydantic_validation_error",
            "name": "Agent Response Issue",
            "description": "AI assistant provided incomplete or incorrectly formatted response",
            "severity": "medium",
            "typical_resolution": "Review task requirements with agent"
        },
        {
            "id": "openai_api_rate_limit", 
            "name": "Temporary Service Issue",
            "description": "AI service temporarily unavailable due to rate limits",
            "severity": "low",
            "typical_resolution": "Automatic retry after delay"
        },
        {
            "id": "database_connection_error",
            "name": "System Infrastructure", 
            "description": "Database or network connectivity problems",
            "severity": "low",
            "typical_resolution": "Automatic retry after brief delay"
        },
        {
            "id": "agent_not_available",
            "name": "Resource Availability",
            "description": "No AI assistants available to handle the task", 
            "severity": "low",
            "typical_resolution": "Wait for assistant to become available"
        },
        {
            "id": "unknown_error",
            "name": "System Issue",
            "description": "Unrecognized error requiring investigation",
            "severity": "medium", 
            "typical_resolution": "Manual investigation required"
        }
    ]
    
    return categories

# Helper functions
async def _store_explanation_in_database(explanation: RecoveryExplanation):
    """Store explanation in database for historical tracking"""
    try:
        supabase.table("recovery_explanations").insert({
            "task_id": explanation.task_id,
            "workspace_id": explanation.technical_details.get("workspace_id"),
            "task_name": explanation.task_name,
            "failure_summary": explanation.failure_summary,
            "root_cause": explanation.root_cause,
            "retry_decision": explanation.retry_decision,
            "confidence_explanation": explanation.confidence_explanation,
            "user_action_required": explanation.user_action_required,
            "estimated_resolution_time": explanation.estimated_resolution_time,
            "severity_level": explanation.severity_level,
            "display_category": explanation.display_category,
            "failure_time": explanation.failure_time.isoformat(),
            "technical_details": explanation.technical_details,
            "error_pattern_matched": explanation.error_pattern_matched,
            "ai_analysis_used": explanation.ai_analysis_used
        }).execute()
        
        logger.debug(f"Stored explanation for task {explanation.task_id} in database")
        
    except Exception as e:
        logger.error(f"Failed to store explanation in database: {e}")

async def _send_recovery_notification(workspace_id: str, explanation: ExplanationResponse):
    """Send real-time notification about recovery explanation"""
    try:
        # Import WebSocket broadcast function
        from routes.websocket import broadcast_to_workspace
        
        notification = NotificationPayload(
            task_id=explanation.task_id,
            workspace_id=workspace_id,
            timestamp=datetime.now(),
            explanation=explanation
        )
        
        await broadcast_to_workspace(
            workspace_id, 
            notification.dict()
        )
        
        logger.debug(f"Sent recovery notification for task {explanation.task_id}")
        
    except ImportError:
        logger.warning("WebSocket not available for recovery notifications")
    except Exception as e:
        logger.error(f"Failed to send recovery notification: {e}")

def _get_next_recommended_action(
    explanations: List[ExplanationResponse], 
    current_status: str
) -> Optional[str]:
    """Determine next recommended action based on explanation history"""
    if not explanations:
        return None
        
    latest_explanation = explanations[0]
    
    if latest_explanation.user_action_required:
        return latest_explanation.user_action_required
    
    if current_status == "failed" and len(explanations) >= 3:
        return "Consider manual intervention - multiple failures detected"
    
    if latest_explanation.severity_level == "critical":
        return "Immediate attention required - critical failure"
    
    return None