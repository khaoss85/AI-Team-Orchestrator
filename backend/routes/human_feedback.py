from fastapi import Request, APIRouter, HTTPException, status
from typing import List, Dict, Any, Optional
from middleware.trace_middleware import get_trace_id, create_traced_logger, TracedDatabaseOperation
from uuid import UUID

from human_feedback_manager import human_feedback_manager, FeedbackStatus

router = APIRouter(prefix="/human-feedback", tags=["human-feedback"])

@router.get("/pending", response_model=List[Dict[str, Any]])
async def get_pending_feedback_requests(workspace_id: Optional[str] = None, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_pending_feedback_requests called", endpoint="get_pending_feedback_requests", trace_id=trace_id)

    """Get all pending human feedback requests"""
    try:
        requests = await human_feedback_manager.get_pending_requests(workspace_id)
        return requests
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pending requests: {str(e)}"
        )

@router.get("/{request_id}", response_model=Dict[str, Any])
async def get_feedback_request(request_id: str, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_feedback_request called", endpoint="get_feedback_request", trace_id=trace_id)

    """Get a specific feedback request"""
    from database import get_human_feedback_requests
    
    try:
        db_requests = await get_human_feedback_requests()
        request = next((r for r in db_requests if r["id"] == request_id), None)
        
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback request not found"
            )
        return request
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get request: {str(e)}"
        )

@router.post("/{request_id}/respond", status_code=status.HTTP_200_OK)
async def respond_to_feedback_request(
    request_id: str,
    response: Dict[str, Any]
):
    """Respond to a feedback request"""
    status_value = response.get("status", "approved")
    try:
        feedback_status = FeedbackStatus(status_value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {status_value}"
        )
    
    success = await human_feedback_manager.respond_to_request(
        request_id=request_id,
        response=response,
        status=feedback_status
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to respond to request (not found or expired)"
        )
    
    return {"success": True, "message": "Response recorded successfully"}

@router.post("/auto-approval-rule", status_code=status.HTTP_201_CREATED)
async def create_auto_approval_rule(rule: Dict[str, Any], request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route create_auto_approval_rule called", endpoint="create_auto_approval_rule", trace_id=trace_id)

    """Create an auto-approval rule"""
    criteria = rule.get("criteria", {})
    action = rule.get("action", "approve")
    
    rule_id = human_feedback_manager.set_auto_approval_rule(criteria, action)
    return {"rule_id": rule_id, "message": "Auto-approval rule created"}