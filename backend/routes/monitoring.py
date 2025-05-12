from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging

from executor import task_executor
from database import get_workspace, list_agents as db_list_agents, list_tasks

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/workspace/{workspace_id}/activity", response_model=List[Dict[str, Any]])
async def get_workspace_activity(
    workspace_id: UUID,
    limit: int = Query(default=20, le=100)
):
    """Get recent activity for a workspace"""
    try:
        activity = task_executor.get_recent_activity(str(workspace_id), limit)
        return activity
    except Exception as e:
        logger.error(f"Error getting workspace activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workspace activity: {str(e)}"
        )

@router.get("/workspace/{workspace_id}/budget", response_model=Dict[str, Any])
async def get_workspace_budget(workspace_id: UUID):
    """Get budget summary for a workspace"""
    try:
        # Get agent IDs for the workspace
        agents = await db_list_agents(str(workspace_id))
        agent_ids = [agent["id"] for agent in agents]
        
        budget_summary = task_executor.budget_tracker.get_workspace_total_cost(
            str(workspace_id), 
            agent_ids
        )
        
        # Add workspace info
        workspace = await get_workspace(str(workspace_id))
        if workspace:
            budget_limit = workspace.get("budget", {}).get("max_amount", 0)
            budget_summary["budget_limit"] = budget_limit
            budget_summary["budget_percentage"] = (
                (budget_summary["total_cost"] / budget_limit * 100) 
                if budget_limit > 0 else 0
            )
        
        return budget_summary
    except Exception as e:
        logger.error(f"Error getting workspace budget: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workspace budget: {str(e)}"
        )

@router.get("/workspace/{workspace_id}/tasks", response_model=List[Dict[str, Any]])
async def get_workspace_tasks(workspace_id: UUID):
    """Get all tasks for a workspace"""
    try:
        tasks = await list_tasks(str(workspace_id))
        return tasks
    except Exception as e:
        logger.error(f"Error getting workspace tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workspace tasks: {str(e)}"
        )

@router.get("/agent/{agent_id}/budget", response_model=Dict[str, Any])
async def get_agent_budget(agent_id: UUID):
    """Get budget details for a specific agent"""
    try:
        total_cost = task_executor.budget_tracker.get_agent_total_cost(str(agent_id))
        usage_log = task_executor.budget_tracker.usage_log.get(str(agent_id), [])
        
        # Calculate additional metrics
        total_tokens = {
            "input": sum(record["input_tokens"] for record in usage_log),
            "output": sum(record["output_tokens"] for record in usage_log)
        }
        
        return {
            "agent_id": str(agent_id),
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "usage_count": len(usage_log),
            "recent_usage": usage_log[-10:] if usage_log else []  # Last 10 records
        }
    except Exception as e:
        logger.error(f"Error getting agent budget: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent budget: {str(e)}"
        )

@router.post("/workspace/{workspace_id}/start", status_code=status.HTTP_200_OK)
async def start_workspace_team(workspace_id: UUID):
    """Start the team by creating an initial task"""
    try:
        # Trigger creation of initial task
        from executor import trigger_initial_workspace_task
        
        task_id = await trigger_initial_workspace_task(str(workspace_id))
        
        if task_id:
            return {
                "success": True,
                "message": "Team started successfully",
                "initial_task_id": task_id
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create initial task"
            )
    except Exception as e:
        logger.error(f"Error starting workspace team: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start team: {str(e)}"
        )

@router.get("/workspace/{workspace_id}/status", response_model=Dict[str, Any])
async def get_workspace_status(workspace_id: UUID):
    """Get overall status of a workspace including agents and tasks"""
    try:
        # Get workspace info
        workspace = await get_workspace(str(workspace_id))
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )
        
        # Get agents
        agents = await db_list_agents(str(workspace_id))
        
        # Count agents by status
        agent_status_counts = {}
        for agent in agents:
            status = agent.get("status", "unknown")
            agent_status_counts[status] = agent_status_counts.get(status, 0) + 1
        
        # Get recent activity
        recent_activity = task_executor.get_recent_activity(str(workspace_id), 5)
        
        # Get budget info
        agent_ids = [agent["id"] for agent in agents]
        budget_info = task_executor.budget_tracker.get_workspace_total_cost(
            str(workspace_id), 
            agent_ids
        )
        
        return {
            "workspace_id": str(workspace_id),
            "workspace_name": workspace.get("name"),
            "workspace_status": workspace.get("status"),
            "agents": {
                "total": len(agents),
                "by_status": agent_status_counts
            },
            "budget": budget_info,
            "recent_activity": recent_activity
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workspace status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workspace status: {str(e)}"
        )

@router.get("/global/activity", response_model=List[Dict[str, Any]])
async def get_global_activity(limit: int = Query(default=50, le=200)):
    """Get recent activity across all workspaces"""
    try:
        activity = task_executor.get_recent_activity(None, limit)
        return activity
    except Exception as e:
        logger.error(f"Error getting global activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get global activity: {str(e)}"
        )

@router.get("/executor/stats", response_model=Dict[str, Any])
async def get_executor_stats():
    """Get task executor statistics"""
    try:
        return {
            "running": task_executor.running,
            "active_workspaces": len(task_executor.workspace_managers),
            "total_execution_logs": len(task_executor.execution_log),
            "tracked_agents": len(task_executor.budget_tracker.usage_log)
        }
    except Exception as e:
        logger.error(f"Error getting executor stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get executor stats: {str(e)}"
        )