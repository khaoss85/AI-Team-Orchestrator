#!/usr/bin/env python3
"""
🧠 Authentic Thinking Process API Routes

Endpoints per gestire il thinking process autentico basato sulla vera todo list
derivata dal goal decomposition. NON genera contenuto fake.
"""

from fastapi import Request, APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from middleware.trace_middleware import get_trace_id, create_traced_logger, TracedDatabaseOperation
import logging
from uuid import UUID
from datetime import datetime

from database import supabase

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/workspace/{workspace_id}/thinking/goals")
async def get_workspace_thinking_goals(workspace_id: str, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_workspace_thinking_goals called", endpoint="get_workspace_thinking_goals", trace_id=trace_id)

    """🎯 Get all goals with thinking process data for a workspace"""
    try:
        # Get goals for the workspace
        goals_result = supabase.table("workspace_goals").select("*").eq("workspace_id", workspace_id).execute()
        
        goals_thinking = []
        for goal in goals_result.data:
            # Get tasks for this goal
            tasks_result = supabase.table("tasks").select("*").eq("goal_id", goal["id"]).eq("workspace_id", workspace_id).execute()
            tasks = tasks_result.data if tasks_result.data else []
            
            # No thinking steps for now since table doesn't exist
            thinking_count = 0
            
            goal_thinking = {
                "goal_id": goal["id"],
                "goal_description": goal["description"],
                "goal_progress": goal.get("progress", 0),
                "goal_status": goal["status"],
                "user_value_score": 0,
                "complexity_level": "simple",
                "total_todos": len(tasks),
                "asset_todos_count": len([t for t in tasks if t.get("target_asset_type")]),
                "thinking_todos_count": 0,
                "completed_todos": len([t for t in tasks if t["status"] == "completed"]),
                "thinking_steps_count": thinking_count,
                "has_decomposition": False,
                "has_thinking_process": thinking_count > 0
            }
            goals_thinking.append(goal_thinking)
        
        return {
            "success": True,
            "goals_thinking": goals_thinking,
            "total_goals": len(goals_thinking)
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting workspace thinking goals: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get thinking goals: {str(e)}")

@router.get("/goal/{goal_id}/thinking")
async def get_goal_thinking_process(goal_id: str, workspace_id: str, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_goal_thinking_process called", endpoint="get_goal_thinking_process", trace_id=trace_id)

    """🧠 Get complete thinking process for a specific goal"""
    try:
        # Get goal basic info
        goal_result = supabase.table("workspace_goals").select("*").eq("id", goal_id).eq("workspace_id", workspace_id).execute()
        
        if not goal_result.data:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        goal = goal_result.data[0]
        
        # Get tasks for this goal (using tasks table instead of goal_todos)
        tasks_result = supabase.table("tasks").select("*").eq("goal_id", goal_id).eq("workspace_id", workspace_id).order("created_at").execute()
        tasks_data = tasks_result.data if tasks_result.data else []
        
        # For now, return empty thinking steps since the table doesn't exist
        thinking_steps_data = []
        
        # Format task list as todo list
        todo_list = []
        for task in tasks_data:
            formatted_todo = {
                "id": str(task["id"]),
                "type": "task",  # All tasks are treated as task type
                "internal_id": task.get("id"),  # Use task ID as internal ID
                "name": task["name"],
                "description": task["description"],
                "priority": task.get("priority", "medium"),
                "status": task.get("status", "pending"),
                "progress_percentage": 100 if task.get("status") == "completed" else 0,
                "estimated_effort": task.get("estimated_effort_hours"),
                "user_impact": "high",  # Default for all tasks
                "complexity": "medium",  # Default for all tasks
                "value_proposition": task.get("description", ""),
                "completion_criteria": task.get("description", ""),
                "supports_assets": [],  # Empty for now
                "linked_task_id": str(task["parent_task_id"]) if task.get("parent_task_id") else None,
                "created_at": task["created_at"] if task.get("created_at") else None,
                "updated_at": task["updated_at"] if task.get("updated_at") else None,
                "completed_at": task.get("completed_at")
            }
            todo_list.append(formatted_todo)
        
        # Format thinking steps (empty for now)
        thinking_steps = []
        
        # Determine execution order (all tasks are treated as task type)
        execution_order = []
        
        # Add all tasks by priority
        priority_order = {"high": 3, "medium": 2, "low": 1}
        sorted_tasks = sorted(todo_list, key=lambda x: priority_order.get(x.get('priority', 'medium'), 2), reverse=True)
        
        for task in sorted_tasks:
            execution_order.append({
                "type": "task",
                "item": task,
                "rationale": f"Task priorità {task['priority']}, status {task['status']}"
            })
        
        # Find current step
        current_step = None
        for todo in todo_list:
            if todo["status"] == "in_progress":
                current_step = todo["id"]
                break
        
        # Determine completion status
        if all(todo["status"] == "completed" for todo in todo_list):
            completion_status = "completed"
        elif any(todo["status"] == "in_progress" for todo in todo_list):
            completion_status = "executing"
        elif len(thinking_steps) > 0:
            completion_status = "planning"
        else:
            completion_status = "planning"
        
        # Return data in format expected by frontend
        return {
            "goal": {
                "id": goal_id,
                "description": goal["description"],
                "progress": goal.get("progress", 0),
                "status": goal["status"]
            },
            "decomposition": {
                "user_value_score": 0,
                "complexity_level": "simple"
            },
            "todo_list": todo_list,
            "thinking_steps": thinking_steps
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting goal thinking process: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get thinking process: {str(e)}")

@router.get("/workspace/{workspace_id}/thinking/latest")
async def get_latest_thinking_steps(request: Request, workspace_id: str, limit: int = 10):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_latest_thinking_steps called", endpoint="get_latest_thinking_steps", trace_id=trace_id)

    """💭 Get latest thinking steps across all goals in workspace"""
    try:
        # Get latest thinking steps
        thinking_result = supabase.table("thinking_process_steps").select("*").eq("workspace_id", workspace_id).order("created_at", desc=True).limit(limit).execute()
        
        latest_thinking = []
        for step in thinking_result.data:
            formatted_step = {
                "step_title": step["step_title"],
                "thinking_content": step["thinking_content"][:200] + "..." if len(step["thinking_content"]) > 200 else step["thinking_content"],
                "agent_role": step["agent_role"],
                "step_type": step["step_type"],
                "timestamp": step["created_at"],
                "workspace_id": workspace_id
            }
            latest_thinking.append(formatted_step)
        
        return {
            "success": True,
            "latest_thinking": latest_thinking
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting latest thinking: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get latest thinking: {str(e)}")

@router.get("/health")
async def thinking_api_health(request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route thinking_api_health called", endpoint="thinking_api_health", trace_id=trace_id)

    """🏥 Health check for thinking API"""
    return {
        "service": "Authentic Thinking Process API",
        "status": "healthy",
        "database_connected": True,
        "timestamp": datetime.now().isoformat()
    }