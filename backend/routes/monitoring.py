from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging
from collections import Counter
from datetime import datetime, timedelta
from pydantic import BaseModel

# Import task_executor
from executor import task_executor

# Import database functions
from database import (
    get_workspace, 
    list_agents as db_list_agents, 
    list_tasks,
    update_task_status
)

# Import models for task status
from models import TaskStatus

logger = logging.getLogger(__name__)
# Tag separati per organizzazione logica
router = APIRouter(prefix="/monitoring", tags=["monitoring", "executor-control"])

# Modelli Pydantic per Task Analysis
class FailureAnalysis(BaseModel):
    total_failures: int
    max_turns_failures: int
    execution_errors: int
    failure_reasons: Dict[str, int]
    average_failure_time: float

class HandoffAnalysis(BaseModel):
    total_handoff_tasks: int
    handoff_success_rate: float
    recent_handoff_pattern: List[Dict[str, str]]
    most_common_handoff_types: Dict[str, int]

class PotentialIssues(BaseModel):
    runaway_detected: bool
    excessive_handoffs: bool
    high_failure_rate: bool
    stuck_agents: List[str]
    queue_overflow_risk: bool

class TaskAnalysisResponse(BaseModel):
    task_counts: Dict[str, int]
    failure_analysis: FailureAnalysis
    handoff_analysis: HandoffAnalysis
    potential_issues: PotentialIssues
    recommendations: List[str]
    analysis_timestamp: str


class WorkspaceTasksResponse(BaseModel):
    workspace_id: str
    tasks: List[Dict[str, Any]]
    total_count: int
    completed_count: int
    pending_count: int
    failed_count: int
    asset_tasks_count: int
    last_updated: str

# ENDPOINT BASE - DA V1
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
            budget_summary["currency"] = currency
            budget_summary["budget_percentage"] = (
                (budget_summary["total_cost"] / budget_limit * 100) 
                if budget_limit and budget_limit > 0 else 0
            )
        else:
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

@router.get("/workspace/{workspace_id}/tasks", response_model=WorkspaceTasksResponse)
async def get_workspace_tasks(
    workspace_id: UUID,
    status: Optional[str] = Query(default=None),
    agent_id: Optional[str] = Query(default=None),
    asset_only: bool = Query(default=False),
    limit: Optional[int] = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
):
    """Get tasks for a workspace with optional filtering."""
    try:
        tasks = await list_tasks(
            str(workspace_id),
            status=status,
            agent_id=agent_id,
            asset_only=asset_only,
            limit=limit,
            offset=offset,
        )

        asset_count = len([t for t in tasks if _is_asset_task(t)])
        response = WorkspaceTasksResponse(
            workspace_id=str(workspace_id),
            tasks=tasks,
            total_count=len(tasks),
            completed_count=len([t for t in tasks if t.get("status") == "completed"]),
            pending_count=len([t for t in tasks if t.get("status") == "pending"]),
            failed_count=len([t for t in tasks if t.get("status") == "failed"]),
            asset_tasks_count=asset_count,
            last_updated=datetime.now().isoformat(),
        )
        return response
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
            logger.warning(f"Could not trigger initial task for workspace {workspace_id}. It might already have tasks or no agents configured.")
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

# ENDPOINT CONTROLLO EXECUTOR - DA V1
@router.post("/executor/pause", status_code=status.HTTP_200_OK)
async def pause_executor_endpoint():
    """Pause the task executor."""
    if not task_executor.running:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task executor is not running.")
    if task_executor.paused:
        return {"message": "Task executor is already paused."}
    await task_executor.pause()
    return {"message": "Task executor pause requested."}

@router.post("/executor/resume", status_code=status.HTTP_200_OK)
async def resume_executor_endpoint():
    """Resume the task executor."""
    if not task_executor.running:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task executor is not running. Cannot resume a stopped executor.")
    if not task_executor.paused:
        return {"message": "Task executor is already running (not paused)."}
    await task_executor.resume()
    return {"message": "Task executor resumed."}

@router.get("/executor/status", response_model=Dict[str, Any])
async def get_executor_runtime_status_endpoint():
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
    """Get detailed statistics from the task executor with asset tracking"""
    try:
        stats = task_executor.get_detailed_stats()
        
        # FIX: Mappa session_task_stats a session_stats per compatibilità frontend
        if "session_task_stats" in stats and "session_stats" not in stats:
            stats["session_stats"] = stats.pop("session_task_stats")
        
        # NUOVO: Aggiungi asset-oriented statistics
        recent_activity = task_executor.get_recent_activity(None, 100)
        
        asset_activity = {
            "asset_tasks_processed": 0,
            "asset_completion_events": 0,
            "deliverable_triggers": 0,
            "asset_enhancement_events": 0
        }
        
        for activity in recent_activity:
            event_type = activity.get("event", "")
            
            if "asset" in event_type:
                if "completed" in event_type:
                    asset_activity["asset_completion_events"] += 1
                elif "processed" in event_type:
                    asset_activity["asset_tasks_processed"] += 1
                elif "enhancement" in event_type:
                    asset_activity["asset_enhancement_events"] += 1
            
            if "deliverable" in event_type:
                asset_activity["deliverable_triggers"] += 1
        
        stats["asset_tracking"] = asset_activity
        
        return stats
    except Exception as e:
        logger.error(f"Error getting detailed executor stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get detailed executor stats: {str(e)}"
        )

# ENDPOINT RUNAWAY PROTECTION - DA V1
@router.get("/runaway-protection/status", response_model=Dict[str, Any])
async def get_runaway_protection_status():
    """Get runaway protection status"""
    return task_executor.get_runaway_protection_status()

@router.post("/runaway-protection/check", status_code=status.HTTP_200_OK)
async def trigger_manual_runaway_check():
    """Manually trigger runaway check"""
    from executor import trigger_runaway_check
    return await trigger_runaway_check()

@router.post("/workspace/{workspace_id}/resume-auto-generation", status_code=status.HTTP_200_OK)
async def resume_workspace_auto_generation(workspace_id: UUID):
    """Manually resume auto-generation for a workspace"""
    from executor import reset_workspace_auto_generation
    return await reset_workspace_auto_generation(str(workspace_id))

@router.get("/workspace/{workspace_id}/health", response_model=Dict[str, Any])
async def get_workspace_health(workspace_id: UUID):
    """Get detailed health status for a workspace"""
    health_status = await task_executor.check_workspace_health(str(workspace_id))
    return health_status

# ENDPOINT TASK ANALYSIS - DA V2 (CORRETTO)
@router.get("/workspace/{workspace_id}/task-analysis", response_model=TaskAnalysisResponse)
async def get_task_failure_analysis(workspace_id: UUID):
    """Get comprehensive analysis of task failures, patterns, and system health"""
    try:
        # Fetch data from multiple sources
        tasks = await list_tasks(str(workspace_id))
        agents_db = await db_list_agents(str(workspace_id))
        
        # Get runtime data from executor
        recent_activity = task_executor.get_recent_activity(str(workspace_id), 100)
        agent_ids = [str(agent["id"]) for agent in agents_db]
        
        # Handle empty task list
        if not tasks:
            return TaskAnalysisResponse(
                task_counts={"total": 0},
                failure_analysis=FailureAnalysis(
                    total_failures=0,
                    max_turns_failures=0,
                    execution_errors=0,
                    failure_reasons={},
                    average_failure_time=0.0
                ),
                handoff_analysis=HandoffAnalysis(
                    total_handoff_tasks=0,
                    handoff_success_rate=0.0,
                    recent_handoff_pattern=[],
                    most_common_handoff_types={}
                ),
                potential_issues=PotentialIssues(
                    runaway_detected=False,
                    excessive_handoffs=False,
                    high_failure_rate=False,
                    stuck_agents=[],
                    queue_overflow_risk=False
                ),
                recommendations=["No tasks found. Consider creating initial tasks."],
                analysis_timestamp=datetime.now().isoformat()
            )
        
        # 1. Analyze task status distribution
        status_counts = Counter()
        failure_reasons = Counter()
        max_turns_failures = 0
        execution_errors = 0
        failure_times = []
        
        for task in tasks:
            status = task.get("status", "unknown")
            status_counts[status] += 1
            
            # Detailed failure analysis
            if status == "failed" and task.get("result"):
                result = task["result"]
                
                # Track failure reasons
                if result.get("max_turns_reached"):
                    max_turns_failures += 1
                    failure_reasons["max_turns_exceeded"] += 1
                else:
                    execution_errors += 1
                    failure_reasons["execution_error"] += 1
                
                # Specific failure reason from result
                specific_reason = result.get("failure_reason", "unknown")
                failure_reasons[specific_reason] += 1
                
                # Track failure timing
                if result.get("execution_time_seconds"):
                    failure_times.append(result["execution_time_seconds"])
        
        # Calculate average failure time
        avg_failure_time = sum(failure_times) / len(failure_times) if failure_times else 0.0
        
        # 2. Comprehensive handoff analysis
        handoff_tasks = [t for t in tasks if _is_handoff_task(t)]
        completed_handoffs = [t for t in handoff_tasks if t.get("status") == "completed"]
        handoff_success_rate = len(completed_handoffs) / len(handoff_tasks) if handoff_tasks else 0.0
        
        # Analyze handoff patterns from recent activity
        handoff_events = [
            event for event in recent_activity 
            if event.get("event") in ["handoff_requested", "initial_task_created"]
        ]
        
        # Recent handoff patterns (last 10)
        recent_handoffs = sorted(handoff_tasks, key=lambda x: x.get("created_at", ""), reverse=True)[:10]
        recent_handoff_pattern = [
            {
                "name": t.get("name", "Unknown"),
                "created_at": t.get("created_at", ""),
                "status": t.get("status", "unknown"),
                "agent_id": t.get("agent_id", "")[:8] + "..." if t.get("agent_id") else "Unknown"
            }
            for t in recent_handoffs
        ]
        
        # Most common handoff types
        handoff_types = Counter()
        for task in handoff_tasks:
            task_name = task.get("name", "").lower()
            if "continuation" in task_name:
                handoff_types["continuation_handoff"] += 1
            elif "escalation" in task_name:
                handoff_types["escalation_handoff"] += 1
            elif "delegation" in task_name:
                handoff_types["delegation_handoff"] += 1
            else:
                handoff_types["other_handoff"] += 1
        
        # 3. Detect potential issues
        total_tasks = len(tasks)
        pending_tasks = status_counts.get("pending", 0)
        failed_tasks = status_counts.get("failed", 0)
        
        # Runaway detection
        runaway_detected = pending_tasks > 50
        
        # Excessive handoffs (more than 30% of tasks)
        excessive_handoffs = len(handoff_tasks) > total_tasks * 0.3
        
        # High failure rate (more than 20%)
        high_failure_rate = (failed_tasks / total_tasks) > 0.2 if total_tasks > 0 else False
        
        # Stuck agents detection
        stuck_agents = _detect_stuck_agents(agents_db, recent_activity)
        
        # Queue overflow risk
        queue_overflow_risk = (
            task_executor.task_queue.qsize() > task_executor.max_queue_size * 0.8
            if hasattr(task_executor, 'task_queue') else False
        )
        
        # 4. Generate recommendations
        recommendations = _generate_recommendations(
            status_counts, len(handoff_tasks), total_tasks, 
            max_turns_failures, stuck_agents, runaway_detected
        )
        
        # 5. Build response
        return TaskAnalysisResponse(
            task_counts=dict(status_counts),
            failure_analysis=FailureAnalysis(
                total_failures=failed_tasks,
                max_turns_failures=max_turns_failures,
                execution_errors=execution_errors,
                failure_reasons=dict(failure_reasons),
                average_failure_time=round(avg_failure_time, 2)
            ),
            handoff_analysis=HandoffAnalysis(
                total_handoff_tasks=len(handoff_tasks),
                handoff_success_rate=round(handoff_success_rate, 3),
                recent_handoff_pattern=recent_handoff_pattern,
                most_common_handoff_types=dict(handoff_types)
            ),
            potential_issues=PotentialIssues(
                runaway_detected=runaway_detected,
                excessive_handoffs=excessive_handoffs,
                high_failure_rate=high_failure_rate,
                stuck_agents=stuck_agents,
                queue_overflow_risk=queue_overflow_risk
            ),
            recommendations=recommendations,
            analysis_timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error in task failure analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze tasks: {str(e)}"
        )

# ENDPOINT EMERGENCY RESET - DA V2
@router.post("/workspace/{workspace_id}/reset-runaway", status_code=status.HTTP_200_OK)
async def reset_runaway_tasks(workspace_id: UUID):
    """Emergency reset for workspaces with runaway task generation"""
    try:
        # Get all pending tasks
        tasks = await list_tasks(str(workspace_id))
        pending_tasks = [t for t in tasks if t.get("status") == "pending"]
        
        if len(pending_tasks) < 50:
            return {
                "message": f"No runaway detected. Only {len(pending_tasks)} pending tasks.",
                "action_taken": "none"
            }
        
        # Cancel excessive handoff tasks (keep only non-handoff pending tasks)
        handoff_tasks_to_cancel = [
            t for t in pending_tasks 
            if _is_handoff_task(t)
        ]
        
        cancelled_count = 0
        for task in handoff_tasks_to_cancel:
            try:
                await update_task_status(
                    task["id"], 
                    TaskStatus.CANCELED.value,
                    {"reason": "Emergency runaway reset", "cancelled_at": datetime.now().isoformat()}
                )
                cancelled_count += 1
            except Exception as e:
                logger.error(f"Failed to cancel task {task['id']}: {e}")
        
        logger.warning(f"Emergency reset: Cancelled {cancelled_count} handoff tasks in workspace {workspace_id}")
        
        return {
            "message": f"Emergency reset completed. Cancelled {cancelled_count} handoff tasks.",
            "remaining_pending": len(pending_tasks) - cancelled_count,
            "action_taken": "runaway_reset"
        }
        
    except Exception as e:
        logger.error(f"Error in emergency reset: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
@router.post("/tasks/{task_id}/reset", status_code=status.HTTP_200_OK)
async def reset_failed_task(task_id: UUID):
    """Reset un task fallito a pending"""
    try:
        from database import update_task_status
        from models import TaskStatus
        
        # Reset del task a pending
        updated = await update_task_status(
            str(task_id), 
            TaskStatus.PENDING.value,
            {"reset_at": datetime.now().isoformat(), "reason": "Manual reset"}
        )
        
        if updated:
            return {
                "success": True,
                "message": f"Task {task_id} reset to pending"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
    except Exception as e:
        logger.error(f"Error resetting task: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset task: {str(e)}"
        )
        
@router.get("/workspace/{workspace_id}/finalization-status", response_model=Dict[str, Any])
async def get_workspace_finalization_status(workspace_id: UUID):
    """
    CRITICAL: Monitoring specifico per stato FINALIZATION
    """
    try:
        all_tasks = await list_tasks(str(workspace_id))
        
        # Count FINALIZATION tasks
        finalization_tasks = [
            task for task in all_tasks
            if isinstance(task.get("context_data"), dict) and 
            task.get("context_data", {}).get("project_phase", "").upper() == "FINALIZATION"
        ]
        
        finalization_pending = [
            task for task in finalization_tasks
            if task.get("status") == "pending"
        ]
        
        finalization_completed = [
            task for task in finalization_tasks
            if task.get("status") == "completed"
        ]
        
        # Check deliverables finali (cerca nei task)
        final_deliverable_tasks = [
            task for task in all_tasks
            if (isinstance(task.get("context_data"), dict) and
                (task.get("context_data", {}).get("is_final_deliverable") or
                 task.get("context_data", {}).get("deliverable_aggregation") or
                 "🎯" in task.get("name", "")))
        ]
        
        completed_final_deliverables = [
            task for task in final_deliverable_tasks
            if task.get("status") == "completed"
        ]
        
        status = {
            "workspace_id": str(workspace_id),
            "finalization_phase_active": len(finalization_tasks) > 0,
            "finalization_tasks_total": len(finalization_tasks),
            "finalization_tasks_pending": len(finalization_pending),
            "finalization_tasks_completed": len(finalization_completed),
            "final_deliverables_total": len(final_deliverable_tasks),
            "final_deliverables_completed": len(completed_final_deliverables),
            "project_completion_percentage": 0,
            "next_action_needed": "UNKNOWN",
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        # Calculate completion percentage
        if final_deliverable_tasks:
            status["project_completion_percentage"] = (
                len(completed_final_deliverables) / len(final_deliverable_tasks) * 100
            )
        elif len(finalization_completed) > 0 and len(finalization_pending) == 0:
            status["project_completion_percentage"] = 85  # High completion if FINALIZATION done
        
        # Determine next action
        if len(finalization_pending) > 0:
            status["next_action_needed"] = "EXECUTE_FINALIZATION_TASKS"
        elif len(final_deliverable_tasks) == 0 and len(finalization_completed) >= 2:
            status["next_action_needed"] = "CREATE_FINAL_DELIVERABLES"
        elif len(completed_final_deliverables) < len(final_deliverable_tasks):
            status["next_action_needed"] = "COMPLETE_DELIVERABLES"
        else:
            status["next_action_needed"] = "PROJECT_READY_FOR_HANDOFF"
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting finalization status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get finalization status: {str(e)}"
        )

@router.post("/workspace/{workspace_id}/force-finalization", status_code=status.HTTP_200_OK)
async def force_finalization_if_stuck(workspace_id: UUID):
    """
    EMERGENCY: Forza completamento se stuck in FINALIZATION
    """
    try:
        # Get current status
        all_tasks = await list_tasks(str(workspace_id))
        
        finalization_pending = [
            task for task in all_tasks
            if (isinstance(task.get("context_data"), dict) and 
                task.get("context_data", {}).get("project_phase", "").upper() == "FINALIZATION" and
                task.get("status") == "pending")
        ]
        
        # Check se è stuck (troppi pending, nessun completed)
        finalization_completed = [
            task for task in all_tasks
            if (isinstance(task.get("context_data"), dict) and 
                task.get("context_data", {}).get("project_phase", "").upper() == "FINALIZATION" and
                task.get("status") == "completed")
        ]
        
        if len(finalization_pending) > 3 and len(finalization_completed) == 0:
            logger.critical(f"🚨 FINALIZATION STUCK DETECTED in W:{workspace_id}")
            
            # Trigger deliverable creation with circuit breaker protection
            try:
                async def _safe_deliverable_creation():
                    from deliverable_aggregator import check_and_create_final_deliverable
                    return await check_and_create_final_deliverable(str(workspace_id))
                
                deliverable_id = await task_executor._execute_with_circuit_breaker(_safe_deliverable_creation)
                
                return {
                    "forced": True, 
                    "reason": "stuck_finalization", 
                    "action_taken": "triggered_deliverable_creation",
                    "deliverable_task_id": deliverable_id
                }
            except Exception as e:
                logger.error(f"Error forcing deliverable creation: {e}")
                return {
                    "forced": False, 
                    "reason": "deliverable_creation_failed",
                    "error": str(e)
                }
        
        return {
            "forced": False, 
            "status": "healthy",
            "finalization_pending": len(finalization_pending),
            "finalization_completed": len(finalization_completed)
        }
        
    except Exception as e:
        logger.error(f"Error in force finalization: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to force finalization: {str(e)}"
        )

@router.post("/workspace/{workspace_id}/clear-stuck-tasks", status_code=status.HTTP_200_OK)
async def clear_stuck_tasks_emergency(workspace_id: UUID):
    """
    EMERGENCY: Clear stuck tasks that might be blocking progress
    """
    try:
        all_tasks = await list_tasks(str(workspace_id))
        
        # Identify potentially stuck tasks
        stuck_candidates = []
        current_time = datetime.now()
        
        for task in all_tasks:
            if task.get("status") not in ["pending", "in_progress"]:
                continue
                
            # Check age
            created_at = task.get("created_at")
            if created_at:
                try:
                    created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    age_hours = (current_time - created_time.replace(tzinfo=None)).total_seconds() / 3600
                    
                    # Tasks pending for more than 2 hours might be stuck
                    if age_hours > 2:
                        stuck_candidates.append({
                            "task_id": task.get("id"),
                            "name": task.get("name", ""),
                            "age_hours": round(age_hours, 1),
                            "status": task.get("status")
                        })
                except Exception as e:
                    logger.debug(f"Error parsing task date: {e}")
        
        logger.warning(f"🧹 Found {len(stuck_candidates)} potentially stuck tasks in W:{workspace_id}")
        
        return {
            "success": True,
            "stuck_tasks_found": len(stuck_candidates),
            "stuck_tasks": stuck_candidates[:10],  # Limit response size
            "message": f"Identified {len(stuck_candidates)} potentially stuck tasks"
        }
        
    except Exception as e:
        logger.error(f"Error clearing stuck tasks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear stuck tasks: {str(e)}"
        )

async def get_workspace_finalization_status(workspace_id: str):
    """
    CRITICAL: Monitoring specifico per stato FINALIZATION
    """
    try:
        all_tasks = await list_tasks(workspace_id)
        deliverables = await get_workspace_deliverables(workspace_id)
        
        # Count FINALIZATION tasks
        finalization_tasks = [
            task for task in all_tasks
            if task.get("context_data", {}).get("project_phase", "").upper() == "FINALIZATION"
        ]
        
        finalization_pending = [
            task for task in finalization_tasks
            if task.get("status") == "PENDING"
        ]
        
        finalization_completed = [
            task for task in finalization_tasks
            if task.get("status") == "COMPLETED"
        ]
        
        # Check deliverables finali
        final_deliverables = [
            d for d in deliverables
            if d.get("phase", "").upper() == "FINALIZATION" or d.get("is_final", False)
        ]
        
        completed_final_deliverables = [
            d for d in final_deliverables
            if d.get("status") == "COMPLETED"
        ]
        
        status = {
            "workspace_id": workspace_id,
            "finalization_phase_active": len(finalization_tasks) > 0,
            "finalization_tasks_total": len(finalization_tasks),
            "finalization_tasks_pending": len(finalization_pending),
            "finalization_tasks_completed": len(finalization_completed),
            "final_deliverables_total": len(final_deliverables),
            "final_deliverables_completed": len(completed_final_deliverables),
            "project_completion_percentage": 0,
            "next_action_needed": "UNKNOWN"
        }
        
        # Calculate completion percentage
        if final_deliverables:
            status["project_completion_percentage"] = (
                len(completed_final_deliverables) / len(final_deliverables) * 100
            )
        
        # Determine next action
        if len(finalization_pending) > 0:
            status["next_action_needed"] = "EXECUTE_FINALIZATION_TASKS"
        elif len(final_deliverables) == 0:
            status["next_action_needed"] = "CREATE_FINAL_DELIVERABLES"
        elif len(completed_final_deliverables) < len(final_deliverables):
            status["next_action_needed"] = "COMPLETE_DELIVERABLES"
        else:
            status["next_action_needed"] = "PROJECT_READY_FOR_HANDOFF"
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting finalization status: {e}")
        return {"error": str(e)}
    
    
# METODI HELPER - CORRETTI SENZA SELF
def _is_handoff_task(task: Dict) -> bool:
    """Determine if a task is a handoff task"""
    task_name = task.get("name", "").lower()
    handoff_indicators = [
        "handoff", "continuation", "transfer", "delegate",
        "escalation", "coordinate", "follow-up"
    ]
    return any(indicator in task_name for indicator in handoff_indicators)


def _is_asset_task(task: Dict) -> bool:
    """Return True if the task appears to be asset-oriented."""
    context_data = task.get("context_data", {}) or {}
    if not isinstance(context_data, dict):
        return False
    return (
        context_data.get("asset_production")
        or context_data.get("asset_oriented_task")
        or "PRODUCE ASSET:" in task.get("name", "").upper()
    )

def _detect_stuck_agents(agents: List[Dict], recent_activity: List[Dict]) -> List[str]:
    """Detect agents that might be stuck (no activity in recent time)"""
    stuck_agents = []
    
    # Get agent activity from recent logs
    agent_activity = {}
    cutoff_time = datetime.now() - timedelta(hours=2)
    
    for event in recent_activity:
        agent_id = event.get("agent_id")
        if agent_id:
            event_time_str = event.get("timestamp")
            if event_time_str:
                try:
                    event_time = datetime.fromisoformat(event_time_str.replace('Z', '+00:00'))
                    if event_time > cutoff_time:
                        agent_activity[agent_id] = max(
                            agent_activity.get(agent_id, event_time), 
                            event_time
                        )
                except ValueError:
                    continue
    
    # Check for agents with no recent activity
    for agent in agents:
        agent_id = agent["id"]
        agent_name = agent.get("name", "Unknown")
        
        if agent_id not in agent_activity and agent.get("status") == "active":
            stuck_agents.append(f"{agent_name} ({agent_id[:8]}...)")
    
    return stuck_agents

def _generate_recommendations(
    status_counts: Counter, 
    handoff_count: int, 
    total_tasks: int,
    max_turns_failures: int,
    stuck_agents: List[str],
    runaway_detected: bool
) -> List[str]:
    """Generate actionable recommendations based on analysis"""
    recommendations = []
    
    # Runaway detection
    if runaway_detected:
        recommendations.append("🚨 CRITICAL: Runaway task generation detected. Consider pausing auto-generation and reviewing task creation logic.")
    
    # High max turns failures
    if max_turns_failures > 5:
        recommendations.append(f"⚠️ High max_turns failures ({max_turns_failures}). Review task complexity and agent prompts.")
    
    # Excessive handoffs
    if handoff_count > total_tasks * 0.3:
        recommendations.append("📄 High handoff ratio. Consider reducing unnecessary handoffs or improving task completion rates.")
    
    # Stuck agents
    if stuck_agents:
        recommendations.append(f"🔄 {len(stuck_agents)} agents appear inactive. Check: {', '.join(stuck_agents[:3])}")
    
    # High failure rate
    failed_rate = status_counts.get("failed", 0) / total_tasks if total_tasks > 0 else 0
    if failed_rate > 0.2:
        recommendations.append(f"❌ High failure rate ({failed_rate:.1%}). Review error patterns and improve error handling.")
    
    # Pending tasks buildup
    pending_ratio = status_counts.get("pending", 0) / total_tasks if total_tasks > 0 else 0
    if pending_ratio > 0.5:
        recommendations.append("⏳ Large number of pending tasks. Consider increasing processing capacity.")
    
    # General health check
    if not recommendations:
        recommendations.append("✅ System appears healthy. Continue monitoring.")
    
    return recommendations

@router.get("/workspace/{workspace_id}/asset-tracking", response_model=Dict[str, Any])
async def get_workspace_asset_tracking(workspace_id: UUID):
    """Get asset-oriented task tracking for a workspace"""
    try:
        tasks = await list_tasks(str(workspace_id))
        
        # Identifica asset tasks
        asset_tasks = []
        completed_asset_tasks = []
        pending_asset_tasks = []
        
        for task in tasks:
            context_data = task.get("context_data", {}) or {}
            if isinstance(context_data, dict):
                if (context_data.get("asset_production") or 
                    context_data.get("asset_oriented_task") or
                    "PRODUCE ASSET:" in task.get("name", "").upper()):
                    
                    asset_info = {
                        "task_id": task.get("id"),
                        "task_name": task.get("name"),
                        "asset_type": context_data.get("detected_asset_type") or context_data.get("asset_type"),
                        "status": task.get("status"),
                        "agent_role": task.get("assigned_to_role"),
                        "created_at": task.get("created_at"),
                        "updated_at": task.get("updated_at")
                    }
                    
                    asset_tasks.append(asset_info)
                    
                    if task.get("status") == "completed":
                        completed_asset_tasks.append(asset_info)
                    elif task.get("status") in ["pending", "in_progress"]:
                        pending_asset_tasks.append(asset_info)
        
        # Calcola statistiche
        total_assets = len(asset_tasks)
        completion_rate = len(completed_asset_tasks) / total_assets if total_assets > 0 else 0
        
        # Asset types breakdown
        asset_types = {}
        for task in asset_tasks:
            asset_type = task.get("asset_type", "unknown")
            if asset_type not in asset_types:
                asset_types[asset_type] = {"total": 0, "completed": 0}
            asset_types[asset_type]["total"] += 1
            if task.get("status") == "completed":
                asset_types[asset_type]["completed"] += 1
        
        return {
            "workspace_id": str(workspace_id),
            "asset_summary": {
                "total_asset_tasks": total_assets,
                "completed_asset_tasks": len(completed_asset_tasks),
                "pending_asset_tasks": len(pending_asset_tasks),
                "completion_rate": round(completion_rate * 100, 1),
                "deliverable_ready": completion_rate >= 0.7  # 70% threshold
            },
            "asset_types_breakdown": asset_types,
            "completed_assets": completed_asset_tasks,
            "pending_assets": pending_asset_tasks,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting asset tracking for {workspace_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get asset tracking: {str(e)}"
        )

@router.get("/workspace/{workspace_id}/deliverable-readiness", response_model=Dict[str, Any])
async def get_deliverable_readiness_status(workspace_id: UUID):
    """Check if workspace is ready for deliverable creation - FIXED VERSION"""
    try:
        # Get basic data
        tasks = await list_tasks(str(workspace_id))
        agents = await db_list_agents(str(workspace_id))
        
        if not tasks:
            return {
                "workspace_id": str(workspace_id),
                "is_ready_for_deliverable": False,
                "has_existing_deliverable": False,
                "readiness_details": {
                    "total_tasks": 0,
                    "completed_tasks": 0,
                    "pending_tasks": 0,
                    "completion_rate": 0,
                    "asset_tasks": 0,
                    "completed_assets": 0,
                    "asset_completion_rate": 0
                },
                "next_action": "create_tasks",
                "checked_at": datetime.now().isoformat()
            }
        
        # Calculate task completion statistics
        completed_tasks = [t for t in tasks if t.get("status") == "completed"]
        pending_tasks = [t for t in tasks if t.get("status") == "pending"]
        completion_rate = len(completed_tasks) / len(tasks) if tasks else 0
        
        # Identify asset tasks
        asset_tasks = []
        completed_asset_tasks = []
        
        for task in tasks:
            context_data = task.get("context_data", {}) or {}
            if isinstance(context_data, dict):
                if (context_data.get("asset_production") or 
                    context_data.get("asset_oriented_task") or
                    "PRODUCE ASSET:" in task.get("name", "").upper()):
                    
                    asset_tasks.append(task)
                    if task.get("status") == "completed":
                        completed_asset_tasks.append(task)
        
        asset_completion_rate = len(completed_asset_tasks) / len(asset_tasks) if asset_tasks else 0
        
        # Check for existing final deliverables
        final_deliverable_tasks = [
            task for task in completed_tasks
            if (isinstance(task.get("context_data"), dict) and 
                (task.get("context_data", {}).get("is_final_deliverable") or
                 task.get("context_data", {}).get("deliverable_aggregation") or
                 "🎯" in task.get("name", "")))
        ]
        
        has_existing_deliverable = len(final_deliverable_tasks) > 0
        
        # SIMPLIFIED readiness logic - no complex aggregator calls
        is_ready_for_deliverable = (
            len(completed_tasks) >= 3 and  # At least 3 completed tasks
            completion_rate >= 0.6 and    # At least 60% completion
            (len(completed_asset_tasks) >= 2 or asset_completion_rate >= 0.7)  # Good asset progress
        )
        
        # Determine next action
        if has_existing_deliverable:
            next_action = "deliverable_exists"
        elif is_ready_for_deliverable:
            next_action = "create_deliverable"
        elif len(pending_tasks) > len(completed_tasks):
            next_action = "continue_tasks"
        else:
            next_action = "wait_for_completion"
        
        return {
            "workspace_id": str(workspace_id),
            "is_ready_for_deliverable": is_ready_for_deliverable,
            "has_existing_deliverable": has_existing_deliverable,
            "readiness_details": {
                "total_tasks": len(tasks),
                "completed_tasks": len(completed_tasks),
                "pending_tasks": len(pending_tasks),
                "completion_rate": round(completion_rate, 3),
                "asset_tasks": len(asset_tasks),
                "completed_assets": len(completed_asset_tasks),
                "asset_completion_rate": round(asset_completion_rate, 3)
            },
            "next_action": next_action,
            "checked_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error checking deliverable readiness: {e}", exc_info=True)
        
        # Return safe fallback instead of raising exception
        return {
            "workspace_id": str(workspace_id),
            "is_ready_for_deliverable": False,
            "has_existing_deliverable": False,
            "readiness_details": {
                "total_tasks": 0,
                "completed_tasks": 0,
                "pending_tasks": 0,
                "completion_rate": 0,
                "asset_tasks": 0,
                "completed_assets": 0,
                "asset_completion_rate": 0
            },
            "next_action": "error_occurred",
            "error": str(e),
            "checked_at": datetime.now().isoformat()
        }
