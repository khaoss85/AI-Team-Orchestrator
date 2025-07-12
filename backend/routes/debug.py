from fastapi import APIRouter, HTTPException
from uuid import UUID
from typing import List, Dict, Any
import logging
from database import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/api/debug/workspace-status/{workspace_id}", tags=["Debug"])
async def get_workspace_completion_status(workspace_id: UUID):
    """
    Debug endpoint to get the calculated completion status from the database view.
    """
    try:
        supabase = get_supabase_client()
        result = supabase.table("v_workspace_completion_status").select("*").eq("workspace_id", workspace_id).single().execute()
        if result.data:
            return result.data
        raise HTTPException(status_code=404, detail="Workspace not found in completion view.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/debug/failed-tasks/{workspace_id}", tags=["Debug"])
async def get_failed_tasks(workspace_id: str) -> Dict[str, Any]:
    """Get all failed tasks for a workspace with detailed error info"""
    try:
        supabase = get_supabase_client()
        # Get failed tasks
        result = supabase.from_("tasks")\
            .select("*")\
            .eq("workspace_id", workspace_id)\
            .eq("status", "failed")\
            .execute()
        
        tasks = result.data if result.data else []
        
        # Extract error details
        failed_task_details = []
        for task in tasks:
            details = {
                "id": task.get("id"),
                "title": task.get("title"),
                "description": task.get("description"),
                "assigned_to": task.get("assigned_to"),
                "status": task.get("status"),
                "result": task.get("result", {}),
                "error": task.get("result", {}).get("error") if isinstance(task.get("result"), dict) else str(task.get("result")),
                "created_at": task.get("created_at"),
                "updated_at": task.get("updated_at")
            }
            failed_task_details.append(details)
        
        return {
            "workspace_id": workspace_id,
            "total_failed": len(failed_task_details),
            "failed_tasks": failed_task_details
        }
        
    except Exception as e:
        logger.error(f"Error getting failed tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/debug/task-details/{task_id}", tags=["Debug"])
async def get_task_execution_details(task_id: str) -> Dict[str, Any]:
    """Get detailed execution info for a specific task"""
    try:
        supabase = get_supabase_client()
        # Get task details
        result = supabase.from_("tasks")\
            .select("*")\
            .eq("id", task_id)\
            .single()\
            .execute()
        
        task = result.data if result.data else {}
        
        # Get related agent info
        agent_result = None
        if task.get("assigned_to"):
            agent_result = supabase.from_("agents")\
                .select("*")\
                .eq("id", task.get("assigned_to"))\
                .single()\
                .execute()
        
        return {
            "task": task,
            "agent": agent_result.data if agent_result and agent_result.data else None,
            "execution_details": {
                "status": task.get("status"),
                "result": task.get("result"),
                "metadata": task.get("metadata", {}),
                "error_details": task.get("result", {}).get("error") if isinstance(task.get("result"), dict) else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting task execution details: {e}")
        raise HTTPException(status_code=500, detail=str(e))
