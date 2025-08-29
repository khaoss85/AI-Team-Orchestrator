"""
Production API endpoints for thinking system
Provides real thinking data from workspace task execution
"""

import logging
from fastapi import APIRouter, HTTPException
from uuid import UUID
from services.thinking_process import thinking_engine
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/thinking", tags=["thinking"])

@router.get("/workspace/{workspace_id}")
async def get_workspace_thinking(
    workspace_id: UUID, 
    limit: int = 10,
    include_completed: bool = True,
    include_active: bool = True
):
    """
    Get real thinking processes for a workspace
    This endpoint provides actual thinking data from task execution, not demo data
    """
    try:
        logger.info(f"🧠 Fetching thinking processes for workspace: {workspace_id}")
        
        # Get thinking processes from the engine
        processes = await thinking_engine.get_workspace_thinking(workspace_id, limit)
        
        # Filter based on parameters
        filtered_processes = []
        for process in processes:
            is_completed = process.completed_at is not None
            if (include_completed and is_completed) or (include_active and not is_completed):
                filtered_processes.append(process)
        
        # Transform to API response format
        response_data = []
        for process in filtered_processes:
            process_data = {
                "process_id": process.process_id,
                "workspace_id": process.workspace_id,
                "context": process.context,
                "steps": [
                    {
                        "step_id": step.step_id,
                        "step_type": step.step_type,
                        "content": step.content,
                        "confidence": step.confidence,
                        "timestamp": step.timestamp,
                        "metadata": step.metadata
                    }
                    for step in process.steps
                ],
                "final_conclusion": process.final_conclusion,
                "overall_confidence": process.overall_confidence,
                "started_at": process.started_at,
                "completed_at": process.completed_at,
                "step_count": len(process.steps),
                "duration_seconds": _calculate_duration(process.started_at, process.completed_at)
            }
            response_data.append(process_data)
        
        logger.info(f"🧠 Retrieved {len(response_data)} thinking processes for workspace {workspace_id}")
        
        return {
            "workspace_id": str(workspace_id),
            "processes": response_data,
            "total_count": len(response_data),
            "active_count": len([p for p in response_data if not p["completed_at"]]),
            "completed_count": len([p for p in response_data if p["completed_at"]]),
            "retrieved_at": thinking_engine.get_current_time()
        }
        
    except Exception as e:
        logger.error(f"Failed to get workspace thinking: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/process/{process_id}")
async def get_thinking_process_details(process_id: str):
    """Get detailed information about a specific thinking process"""
    try:
        process = await thinking_engine.get_thinking_process(process_id)
        
        if not process:
            raise HTTPException(status_code=404, detail=f"Thinking process {process_id} not found")
        
        return {
            "process_id": process.process_id,
            "workspace_id": process.workspace_id,
            "context": process.context,
            "steps": [
                {
                    "step_id": step.step_id,
                    "step_type": step.step_type,
                    "content": step.content,
                    "confidence": step.confidence,
                    "timestamp": step.timestamp,
                    "metadata": step.metadata
                }
                for step in process.steps
            ],
            "final_conclusion": process.final_conclusion,
            "overall_confidence": process.overall_confidence,
            "started_at": process.started_at,
            "completed_at": process.completed_at,
            "step_count": len(process.steps),
            "duration_seconds": _calculate_duration(process.started_at, process.completed_at)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get thinking process {process_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workspace/{workspace_id}/summary")
async def get_workspace_thinking_summary(workspace_id: UUID):
    """Get a summary of thinking activity for a workspace"""
    try:
        processes = await thinking_engine.get_workspace_thinking(workspace_id, 50)  # Get more for summary
        
        total_processes = len(processes)
        active_processes = len([p for p in processes if not p.completed_at])
        completed_processes = total_processes - active_processes
        
        total_steps = sum(len(p.steps) for p in processes)
        avg_confidence = sum(p.overall_confidence for p in processes) / total_processes if total_processes > 0 else 0
        
        # Recent activity (last 24 hours)
        from datetime import datetime, timedelta
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_processes = [
            p for p in processes 
            if datetime.fromisoformat(p.started_at.replace('Z', '+00:00')) > recent_cutoff
        ]
        
        return {
            "workspace_id": str(workspace_id),
            "summary": {
                "total_processes": total_processes,
                "active_processes": active_processes,
                "completed_processes": completed_processes,
                "total_thinking_steps": total_steps,
                "average_confidence": round(avg_confidence, 2),
                "recent_activity_24h": len(recent_processes)
            },
            "activity_status": "active" if active_processes > 0 else "quiet",
            "last_activity": processes[0].started_at if processes else None,
            "generated_at": thinking_engine.get_current_time()
        }
        
    except Exception as e:
        logger.error(f"Failed to get workspace thinking summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _calculate_duration(started_at: str, completed_at: Optional[str] = None) -> Optional[float]:
    """Calculate duration in seconds between start and completion"""
    try:
        from datetime import datetime
        
        start_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
        
        if completed_at:
            end_time = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
        else:
            end_time = datetime.utcnow().replace(tzinfo=start_time.tzinfo)
            
        duration = (end_time - start_time).total_seconds()
        return round(duration, 2)
    except Exception:
        return None