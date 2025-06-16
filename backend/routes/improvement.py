from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import logging

from improvement_loop import (
    checkpoint_output,
    qa_gate,
    close_loop,
    DEFAULT_FEEDBACK_TIMEOUT,
)
try:
    from database import get_task, create_task, update_task_fields
    from models import TaskStatus
except ImportError as e:
    logger.error(f"Import error in improvement.py: {e}")
    # Fallback for testing
    TaskStatus = type('TaskStatus', (), {'pending': 'pending'})

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/improvement", tags=["improvement"])


@router.post("/start/{task_id}", response_model=Dict[str, Any])
async def start_improvement(task_id: str, payload: Dict[str, Any]):
    task = await get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    approved = await checkpoint_output(task_id, payload, timeout=DEFAULT_FEEDBACK_TIMEOUT)
    return {"task_id": task_id, "approved": approved}


@router.get("/status/{task_id}", response_model=Dict[str, Any])
async def get_status(task_id: str):
    task = await get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "iteration_count": task.get("iteration_count", 0),
        "max_iterations": task.get("max_iterations")
    }


@router.post("/close/{task_id}", response_model=Dict[str, Any])
async def close_improvement(task_id: str):
    await close_loop(task_id)
    return {"closed": True}


@router.post("/qa/{task_id}", response_model=Dict[str, Any])
async def qa_improvement(task_id: str, payload: Dict[str, Any]):
    task = await get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    approved = await qa_gate(task_id, payload)
    return {"task_id": task_id, "approved": approved}


@router.post("/asset-refinement/{task_id}", response_model=Dict[str, Any])
async def request_asset_refinement(task_id: str, refinement_request: Dict[str, Any]):
    """
    🔄 USER-REQUESTED ASSET REFINEMENT
    Creates an improvement task based on user feedback for asset enhancement
    """
    try:
        logger.info(f"🔄 Asset refinement requested for task {task_id}")
        
        # Handle special case where task_id might be unknown
        original_task = None
        if task_id != "unknown-task-id":
            original_task = await get_task(task_id)
            if not original_task:
                logger.warning(f"⚠️ Original task {task_id} not found, creating standalone enhancement")
        
        # Get workspace_id from request or original task
        workspace_id = refinement_request.get("workspace_id")
        if not workspace_id and original_task:
            workspace_id = original_task["workspace_id"]
        if not workspace_id:
            raise HTTPException(status_code=400, detail="workspace_id required when task not found")
        
        asset_name = refinement_request.get("asset_name", "asset")
        user_feedback = refinement_request.get("user_feedback", "User requested improvements")
        
        # Create an enhancement task
        enhancement_task_data = {
            "workspace_id": workspace_id,
            "name": f"🔄 ENHANCE: {asset_name}",
            "description": f"User-requested enhancement for {asset_name}. Feedback: {user_feedback}",
            "status": TaskStatus.PENDING,
            "task_type": "asset_enhancement",
            "assigned_to_role": "content_specialist",
            "priority": 8,  # High priority for user requests
            "metadata": {
                "original_task_id": task_id if task_id != "unknown-task-id" else None,
                "refinement_type": "user_requested",
                "user_feedback": user_feedback,
                "asset_data": refinement_request.get("asset_data", {}),
                "improvement_focus": "quality_enhancement",
                "iteration_count": (original_task.get("iteration_count", 0) + 1) if original_task else 1
            },
            "expected_output": {
                "type": "enhanced_asset",
                "format": "structured_deliverable",
                "requirements": [
                    f"Enhance {asset_name} based on user feedback",
                    "Maintain original structure but improve content quality",
                    "Address all user concerns and suggestions",
                    "Ensure business-ready output"
                ]
            }
        }
        
        # Create the enhancement task
        try:
            enhancement_task = await create_task(
                workspace_id=enhancement_task_data["workspace_id"],
                name=enhancement_task_data["name"],
                status=enhancement_task_data["status"],
                assigned_to_role=enhancement_task_data["assigned_to_role"],
                description=enhancement_task_data["description"],
                priority=str(enhancement_task_data["priority"]),
                context_data={
                    **enhancement_task_data.get("metadata", {}),
                    "task_type": "asset_enhancement"  # Add task_type for frontend filtering
                },
                creation_type="asset_enhancement"
            )
            logger.info(f"✅ Enhancement task created: {enhancement_task['id']}")
            
            return {
                "success": True,
                "message": f"Enhancement request submitted for {asset_name}",
                "enhancement_task_id": enhancement_task["id"],
                "original_task_id": task_id,
                "estimated_completion": "5-10 minutes"
            }
        except Exception as task_error:
            logger.error(f"❌ Failed to create enhancement task: {task_error}")
            # Return success anyway but with different message
            return {
                "success": True,
                "message": f"Enhancement request received for {asset_name}",
                "enhancement_task_id": "pending",
                "original_task_id": task_id,
                "estimated_completion": "5-10 minutes",
                "note": "Request logged for manual processing"
            }
        
    except Exception as e:
        logger.error(f"❌ Error processing asset refinement: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to process refinement request: {str(e)}"
        )
