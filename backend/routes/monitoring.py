from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging
from collections import Counter

# Assicurati che task_executor sia importato correttamente
# Se executor.py è nella stessa directory o nel path Python:
from executor import task_executor
# Altrimenti, aggiusta l'import in base alla tua struttura effettiva, es:
# from ..executor import task_executor 

from database import get_workspace, list_agents as db_list_agents, list_tasks

logger = logging.getLogger(__name__)
# Aggiunto "executor-control" ai tag per separare logicamente gli endpoint
router = APIRouter(prefix="/monitoring", tags=["monitoring", "executor-control"])

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
        logger.error(f"Error getting workspace activity for {workspace_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workspace activity: {str(e)}"
        )

@router.get("/workspace/{workspace_id}/budget", response_model=Dict[str, Any])
async def get_workspace_budget(workspace_id: UUID):
    """Get budget summary for a workspace"""
    try:
        agents_db = await db_list_agents(str(workspace_id))
        agent_ids = [str(agent["id"]) for agent in agents_db]

        budget_summary = task_executor.budget_tracker.get_workspace_total_cost(
            str(workspace_id), 
            agent_ids
        )

        workspace_db = await get_workspace(str(workspace_id))
        if workspace_db:
            budget_limit = workspace_db.get("budget", {}).get("max_amount", 0)
            currency = workspace_db.get("budget", {}).get("currency", "EUR")
            budget_summary["budget_limit"] = budget_limit
            budget_summary["currency"] = currency # Assicura che la valuta sia quella del workspace
            budget_summary["budget_percentage"] = (
                (budget_summary["total_cost"] / budget_limit * 100) 
                if budget_limit and budget_limit > 0 else 0
            )
        else: # Fallback se il workspace non viene trovato (improbabile se l'ID è valido)
            budget_summary["budget_limit"] = 0
            budget_summary["budget_percentage"] = 0
            budget_summary["currency"] = "N/A"

        return budget_summary
    except Exception as e:
        logger.error(f"Error getting workspace budget for {workspace_id}: {e}", exc_info=True)
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
        logger.error(f"Error getting workspace tasks for {workspace_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workspace tasks: {str(e)}"
        )

@router.get("/agent/{agent_id}/budget", response_model=Dict[str, Any])
async def get_agent_budget(agent_id: UUID):
    """Get budget details for a specific agent"""
    try:
        total_cost = task_executor.budget_tracker.get_agent_total_cost(str(agent_id))
        usage_log_agent = task_executor.budget_tracker.usage_log.get(str(agent_id), [])

        total_tokens_agent = {
            "input": sum(record.get("input_tokens", 0) for record in usage_log_agent),
            "output": sum(record.get("output_tokens", 0) for record in usage_log_agent)
        }

        return {
            "agent_id": str(agent_id),
            "total_cost": total_cost,
            "total_tokens": total_tokens_agent,
            "usage_count": len(usage_log_agent),
            "recent_usage": usage_log_agent[-10:] 
        }
    except Exception as e:
        logger.error(f"Error getting agent budget for {agent_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent budget: {str(e)}"
        )

@router.post("/workspace/{workspace_id}/start", status_code=status.HTTP_200_OK)
async def start_workspace_team(workspace_id: UUID):
    """Start the team by creating an initial task if none exist or workspace is idle"""
    try:
        from executor import trigger_initial_workspace_task 

        task_id = await trigger_initial_workspace_task(str(workspace_id))

        if task_id:
            return {"success": True, "message": "Initial task created or already present. Team processes initiated.", "initial_task_id": task_id}
        else:
            # Questo potrebbe accadere se non ci sono agenti o il workspace non è in uno stato appropriato.
            # La logica in trigger_initial_workspace_task dovrebbe gestire questi casi e loggare.
            logger.warning(f"Could not trigger initial task for workspace {workspace_id}. It might already have tasks or no agents configured.")
            # Potresti voler restituire un messaggio più specifico qui, ma un 400 potrebbe essere troppo generico.
            # Un 200 con un messaggio potrebbe essere più appropriato se l'azione non è "errata" ma semplicemente non necessaria.
            return {"success": False, "message": "Could not trigger initial task. Workspace might already have tasks or requires agent configuration."}

    except Exception as e:
        logger.error(f"Error starting workspace team for {workspace_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to start team: {str(e)}")

@router.get("/workspace/{workspace_id}/status", response_model=Dict[str, Any])
async def get_workspace_status_endpoint(workspace_id: UUID):
    """Get overall status of a workspace including agents and tasks"""
    try:
        workspace = await get_workspace(str(workspace_id))
        if not workspace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        agents_db = await db_list_agents(str(workspace_id))
        agent_status_counts = Counter(agent.get("status", "unknown") for agent in agents_db)

        recent_activity = task_executor.get_recent_activity(str(workspace_id), 5)
        agent_ids = [str(agent["id"]) for agent in agents_db]
        budget_info = task_executor.budget_tracker.get_workspace_total_cost(str(workspace_id), agent_ids)

        return {
            "workspace_id": str(workspace_id), "workspace_name": workspace.get("name"),
            "workspace_status": workspace.get("status"),
            "agents": {"total": len(agents_db), "by_status": dict(agent_status_counts)},
            "budget": budget_info, "recent_activity": recent_activity
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workspace status for {workspace_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get workspace status: {str(e)}")

@router.get("/global/activity", response_model=List[Dict[str, Any]])
async def get_global_activity(limit: int = Query(default=50, le=200)):
    """Get recent activity across all workspaces"""
    try:
        activity = task_executor.get_recent_activity(None, limit)
        return activity
    except Exception as e:
        logger.error(f"Error getting global activity: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get global activity: {str(e)}")

# --- ENDPOINT PER CONTROLLO E STATISTICHE ESECUTORE ---

@router.post("/executor/pause", status_code=status.HTTP_200_OK)
async def pause_executor_endpoint(): # Nome funzione univoco
    """Pause the task executor."""
    if not task_executor.running:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task executor is not running.")
    if task_executor.paused:
        return {"message": "Task executor is already paused."}
    await task_executor.pause()
    return {"message": "Task executor pause requested."}

@router.post("/executor/resume", status_code=status.HTTP_200_OK)
async def resume_executor_endpoint(): # Nome funzione univoco
    """Resume the task executor."""
    if not task_executor.running:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task executor is not running. Cannot resume a stopped executor.")
    if not task_executor.paused:
        return {"message": "Task executor is already running (not paused)."}
    await task_executor.resume()
    return {"message": "Task executor resumed."}

@router.get("/executor/status", response_model=Dict[str, Any])
async def get_executor_runtime_status_endpoint(): # Nome funzione univoco
    """Get the current running and paused status of the task executor."""
    return {
        "is_running": task_executor.running,
        "is_paused": task_executor.paused,
        "status_string": "running" if task_executor.running and not task_executor.paused else \
                         "paused" if task_executor.paused else \
                         "stopped"
    }

@router.get("/executor/detailed-stats", response_model=Dict[str, Any])
async def get_executor_detailed_stats_endpoint():
    """Get detailed statistics from the task executor."""
    try:
        stats = task_executor.get_detailed_stats()
        
        # FIX: Mappa session_task_stats a session_stats per compatibilità frontend
        if "session_task_stats" in stats and "session_stats" not in stats:
            stats["session_stats"] = stats.pop("session_task_stats")
        
        return stats
    except Exception as e:
        logger.error(f"Error getting detailed executor stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get detailed executor stats: {str(e)}"
        )