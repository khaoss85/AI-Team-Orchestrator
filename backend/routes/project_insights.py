from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging
from datetime import datetime, timedelta
from collections import Counter

from database import (
    get_workspace,
    list_agents as db_list_agents,
    list_tasks,
)
from executor import task_executor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["project-insights"])

@router.get("/{workspace_id}/insights", response_model=Dict[str, Any])
async def get_project_insights(workspace_id: UUID):
    """Get comprehensive project insights including progress, timing, and predictions"""
    try:
        # Get workspace details
        workspace = await get_workspace(str(workspace_id))
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        # Get agents and tasks
        agents = await db_list_agents(str(workspace_id))
        tasks = await list_tasks(str(workspace_id))
        
        # Get execution history from task executor
        recent_activity = task_executor.get_recent_activity(str(workspace_id), 100)
        budget_info = task_executor.budget_tracker.get_workspace_total_cost(
            str(workspace_id), 
            [str(agent["id"]) for agent in agents]
        )
        
        # Calculate insights
        insights = await _calculate_project_insights(
            workspace, agents, tasks, recent_activity, budget_info
        )
        
        return insights
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project insights: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project insights: {str(e)}"
        )

@router.get("/{workspace_id}/major-milestones", response_model=List[Dict[str, Any]])
async def get_major_milestones(workspace_id: UUID):
    """Get major milestones and phases completed in the project"""
    try:
        tasks = await list_tasks(str(workspace_id))
        agents = await db_list_agents(str(workspace_id))
        
        # Get recent activity to identify major events
        recent_activity = task_executor.get_recent_activity(str(workspace_id), 50)
        
        milestones = _extract_major_milestones(tasks, agents, recent_activity)
        return milestones
        
    except Exception as e:
        logger.error(f"Error getting major milestones: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get major milestones: {str(e)}"
        )

async def _calculate_project_insights(
    workspace: Dict,
    agents: List[Dict],
    tasks: List[Dict],
    recent_activity: List[Dict],
    budget_info: Dict
) -> Dict[str, Any]:
    """Calculate comprehensive project insights"""
    
    # Task statistics
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t["status"] == "completed"])
    in_progress_tasks = len([t for t in tasks if t["status"] == "in_progress"])
    pending_tasks = len([t for t in tasks if t["status"] == "pending"])
    failed_tasks = len([t for t in tasks if t["status"] == "failed"])
    
    # Calculate progress percentage
    progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Time analysis
    workspace_created = datetime.fromisoformat(workspace["created_at"].replace('Z', '+00:00'))
    time_elapsed = datetime.now(workspace_created.tzinfo) - workspace_created
    time_elapsed_days = time_elapsed.days + (time_elapsed.seconds / 86400)
    
    # Calculate average task completion time
    completed_task_times = []
    for task in tasks:
        if task["status"] == "completed" and task.get("created_at") and task.get("updated_at"):
            created = datetime.fromisoformat(task["created_at"].replace('Z', '+00:00'))
            updated = datetime.fromisoformat(task["updated_at"].replace('Z', '+00:00'))
            duration = (updated - created).total_seconds() / 3600  # in hours
            completed_task_times.append(duration)
    
    avg_task_completion_hours = sum(completed_task_times) / len(completed_task_times) if completed_task_times else 24
    
    # Project phase detection
    current_phase = _detect_current_phase(tasks, recent_activity)
    
    # Prediction calculations
    if completed_tasks > 0 and pending_tasks > 0:
        estimated_completion_days = (pending_tasks * avg_task_completion_hours / 24) * 1.2  # Add 20% buffer
        estimated_completion_date = datetime.now() + timedelta(days=estimated_completion_days)
    else:
        estimated_completion_days = None
        estimated_completion_date = None
    
    # Agent activity summary
    agent_activity = _analyze_agent_activity(agents, recent_activity)
    
    # Budget efficiency
    cost_per_completed_task = budget_info["total_cost"] / completed_tasks if completed_tasks > 0 else 0
    
    # Project health score (0-100)
    health_score = _calculate_project_health_score(
        progress_percentage, 
        failed_tasks / total_tasks * 100 if total_tasks > 0 else 0,
        agent_activity,
        time_elapsed_days
    )
    
    # Recent major events
    major_events = _get_recent_major_events(recent_activity, 5)
    
    return {
        "overview": {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "pending_tasks": pending_tasks,
            "failed_tasks": failed_tasks,
            "progress_percentage": round(progress_percentage, 1),
            "health_score": round(health_score, 0)
        },
        "timing": {
            "time_elapsed_days": round(time_elapsed_days, 1),
            "avg_task_completion_hours": round(avg_task_completion_hours, 1),
            "estimated_completion_days": round(estimated_completion_days, 1) if estimated_completion_days else None,
            "estimated_completion_date": estimated_completion_date.isoformat() if estimated_completion_date else None
        },
        "current_state": {
            "phase": current_phase,
            "status": workspace.get("status", "active"),
            "active_agents": len([a for a in agents if a.get("status") == "active"]),
            "total_agents": len(agents)
        },
        "performance": {
            "cost_per_completed_task": round(cost_per_completed_task, 2),
            "total_cost": budget_info["total_cost"],
            "budget_utilization": budget_info.get("budget_percentage", 0),
            "agent_activity": agent_activity
        },
        "recent_highlights": major_events
    }

def _detect_current_phase(tasks: List[Dict], recent_activity: List[Dict]) -> str:
    """Detect the current phase of the project based on tasks and activity"""
    
    # Check for initialization keywords
    recent_task_names = [t.get("name", "").lower() for t in tasks[-5:]]
    recent_activity_content = [a.get("task_name", "").lower() for a in recent_activity[:10]]
    
    all_recent_text = " ".join(recent_task_names + recent_activity_content)
    
    if any(keyword in all_recent_text for keyword in ["initialization", "planning", "setup"]):
        return "Initialization & Planning"
    elif any(keyword in all_recent_text for keyword in ["analysis", "research", "investigation"]):
        return "Analysis & Research"
    elif any(keyword in all_recent_text for keyword in ["implementation", "development", "creation"]):
        return "Implementation"
    elif any(keyword in all_recent_text for keyword in ["testing", "validation", "review"]):
        return "Testing & Validation"
    elif any(keyword in all_recent_text for keyword in ["optimization", "refinement", "improvement"]):
        return "Optimization"
    elif any(keyword in all_recent_text for keyword in ["finalization", "deployment", "completion"]):
        return "Finalization"
    else:
        # Determine by task completion ratio
        completed_ratio = len([t for t in tasks if t["status"] == "completed"]) / len(tasks) if tasks else 0
        if completed_ratio < 0.2:
            return "Early Stage"
        elif completed_ratio < 0.5:
            return "Development Phase"
        elif completed_ratio < 0.8:
            return "Implementation Phase"
        else:
            return "Completion Phase"

def _analyze_agent_activity(agents: List[Dict], recent_activity: List[Dict]) -> Dict[str, Any]:
    """Analyze agent activity patterns"""
    
    agent_names = {agent["id"]: agent["name"] for agent in agents}
    
    # Count activities per agent
    agent_activity_count = Counter()
    agent_recent_activity = {}
    
    for activity in recent_activity[-20:]:  # Last 20 activities
        agent_id = activity.get("agent_id")
        if agent_id and agent_id in agent_names:
            agent_activity_count[agent_id] += 1
            if agent_id not in agent_recent_activity:
                agent_recent_activity[agent_id] = activity.get("timestamp")
    
    # Most active agent
    most_active_agent_id = agent_activity_count.most_common(1)[0][0] if agent_activity_count else None
    most_active_agent = agent_names.get(most_active_agent_id) if most_active_agent_id else None
    
    # Recently active agents
    recently_active = len(agent_activity_count)
    
    return {
        "most_active_agent": most_active_agent,
        "recently_active_agents": recently_active,
        "total_agents": len(agents),
        "activity_distribution": dict(agent_activity_count)
    }

def _calculate_project_health_score(
    progress_percentage: float,
    failure_rate: float,
    agent_activity: Dict,
    time_elapsed_days: float
) -> float:
    """Calculate an overall project health score (0-100)"""
    
    # Progress component (40% weight)
    progress_score = min(progress_percentage * 1.2, 100)  # Slight boost for progress
    
    # Failure rate component (20% weight) - inverted
    failure_score = max(0, 100 - failure_rate * 5)  # 5% failure = 75 points
    
    # Agent activity component (20% weight)
    active_ratio = agent_activity["recently_active_agents"] / agent_activity["total_agents"]
    activity_score = active_ratio * 100
    
    # Time efficiency component (20% weight)
    # Projects shouldn't take too long
    expected_duration = 30  # days
    if time_elapsed_days <= expected_duration:
        time_score = 100
    else:
        time_score = max(0, 100 - (time_elapsed_days - expected_duration) * 2)
    
    # Calculate weighted average
    health_score = (
        progress_score * 0.4 +
        failure_score * 0.2 +
        activity_score * 0.2 +
        time_score * 0.2
    )
    
    return max(0, min(100, health_score))

def _get_recent_major_events(recent_activity: List[Dict], limit: int) -> List[Dict[str, Any]]:
    """Extract recent major events from activity log"""
    
    major_event_types = [
        "task_completed", 
        "task_failed", 
        "initial_task_created",
        "handoff_requested"
    ]
    
    major_events = []
    for activity in recent_activity:
        if activity.get("event") in major_event_types:
            major_events.append({
                "timestamp": activity.get("timestamp"),
                "event": activity.get("event"),
                "description": _format_event_description(activity),
                "task_name": activity.get("task_name"),
                "agent_id": activity.get("agent_id")
            })
    
    return major_events[:limit]

def _format_event_description(activity: Dict) -> str:
    """Format activity into human-readable description"""
    event = activity.get("event", "")
    task_name = activity.get("task_name", "")
    
    if event == "task_completed":
        return f"Completed: {task_name}"
    elif event == "task_failed":
        return f"Failed: {task_name}"
    elif event == "initial_task_created":
        return f"Project started with: {task_name}"
    elif event == "handoff_requested":
        return f"Handoff requested for: {task_name}"
    else:
        return f"{event}: {task_name}"

def _extract_major_milestones(
    tasks: List[Dict], 
    agents: List[Dict], 
    recent_activity: List[Dict]
) -> List[Dict[str, Any]]:
    """Extract major milestones from project history"""
    
    milestones = []
    
    # Add initialization milestone
    initial_tasks = [t for t in tasks if "initialization" in t.get("name", "").lower()]
    if initial_tasks:
        earliest_task = min(initial_tasks, key=lambda x: x.get("created_at", ""))
        milestones.append({
            "title": "Project Initialization",
            "description": f"Project setup and initial planning",
            "date": earliest_task.get("created_at"),
            "status": "completed",
            "type": "initialization"
        })
    
    # Add phase completion milestones
    completed_tasks = [t for t in tasks if t["status"] == "completed"]
    task_count_by_phase = {}
    
    for task in completed_tasks:
        # Simple phase detection based on task names
        task_name = task.get("name", "").lower()
        if any(keyword in task_name for keyword in ["plan", "design", "architecture"]):
            phase = "Planning Phase"
        elif any(keyword in task_name for keyword in ["implement", "develop", "create"]):
            phase = "Implementation Phase"
        elif any(keyword in task_name for keyword in ["test", "validate", "verify"]):
            phase = "Testing Phase"
        else:
            phase = "Development Phase"
        
        task_count_by_phase[phase] = task_count_by_phase.get(phase, 0) + 1
    
    # Convert to milestones
    for phase, count in task_count_by_phase.items():
        if count >= 2:  # Only add phases with multiple completed tasks
            milestones.append({
                "title": f"{phase} Completed",
                "description": f"{count} tasks completed in this phase",
                "date": datetime.now().isoformat(),  # Approximate
                "status": "completed",
                "type": "phase",
                "task_count": count
            })
    
    # Sort by date
    milestones.sort(key=lambda x: x.get("date", ""))
    
    return milestones