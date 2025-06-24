#!/usr/bin/env python3
"""
🧠 Authentic Thinking Process API Routes

Endpoints per gestire il thinking process autentico basato sulla vera todo list
derivata dal goal decomposition. NON genera contenuto fake.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
import logging
from uuid import UUID
from datetime import datetime

from database import supabase

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/workspace/{workspace_id}/thinking/goals")
async def get_workspace_thinking_goals(workspace_id: str):
    """🎯 Get all goals with thinking process data for a workspace"""
    try:
        # Get goals for the workspace
        goals_result = supabase.table("workspace_goals").select("*").eq("workspace_id", workspace_id).execute()
        
        goals_thinking = []
        for goal in goals_result.data:
            # Get decomposition for this goal
            decomp_result = supabase.table("workspace_goal_decompositions").select("*").eq("goal_id", goal["id"]).execute()
            decomp = decomp_result.data[0] if decomp_result.data else None
            
            # Get todos for this goal
            todos_result = supabase.table("goal_todos").select("*").eq("goal_id", goal["id"]).execute()
            todos = todos_result.data if todos_result.data else []
            
            # Get thinking steps count
            thinking_result = supabase.table("thinking_process_steps").select("id").eq("workspace_id", workspace_id).execute()
            thinking_count = len(thinking_result.data) if thinking_result.data else 0
            
            goal_thinking = {
                "goal_id": goal["id"],
                "goal_description": goal["description"],
                "goal_progress": goal.get("progress", 0),
                "goal_status": goal["status"],
                "user_value_score": decomp["user_value_score"] if decomp else 0,
                "complexity_level": decomp["complexity_level"] if decomp else "simple",
                "total_todos": len(todos),
                "asset_todos_count": len([t for t in todos if t["todo_type"] == "asset"]),
                "thinking_todos_count": len([t for t in todos if t["todo_type"] == "thinking"]),
                "completed_todos": len([t for t in todos if t["status"] == "completed"]),
                "thinking_steps_count": thinking_count,
                "has_decomposition": decomp is not None,
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
async def get_goal_thinking_process(goal_id: str, workspace_id: str):
    """🧠 Get complete thinking process for a specific goal"""
    try:
        # Get goal basic info
        goal_result = supabase.table("workspace_goals").select("*").eq("id", goal_id).eq("workspace_id", workspace_id).execute()
        
        if not goal_result.data:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        goal = goal_result.data[0]
        
        # Get goal decomposition
        decomposition_result = supabase.table("workspace_goal_decompositions").select("*").eq("goal_id", goal_id).execute()
        decomposition = decomposition_result.data[0] if decomposition_result.data else None
        
        # Get todo list
        todos_result = supabase.table("goal_todos").select("*").eq("goal_id", goal_id).order("created_at").execute()
        todos_data = todos_result.data if todos_result.data else []
        
        # Get thinking steps for this workspace
        thinking_steps_result = supabase.table("thinking_process_steps").select("*").eq("workspace_id", workspace_id).order("created_at").execute()
        thinking_steps_data = thinking_steps_result.data if thinking_steps_result.data else []
        
        # Format todo list
        todo_list = []
        for todo in todos_data:
            formatted_todo = {
                "id": str(todo["id"]),
                "type": todo["todo_type"],
                "internal_id": todo["internal_id"],
                "name": todo["name"],
                "description": todo["description"],
                "priority": todo["priority"],
                "status": todo.get("status", "pending"),
                "progress_percentage": todo.get("progress_percentage", 0),
                "estimated_effort": todo.get("estimated_effort"),
                "user_impact": todo.get("user_impact"),
                "complexity": todo.get("complexity"),
                "value_proposition": todo.get("value_proposition"),
                "completion_criteria": todo.get("completion_criteria"),
                "supports_assets": todo.get("supports_assets", []),
                "linked_task_id": str(todo["linked_task_id"]) if todo.get("linked_task_id") else None,
                "created_at": todo["created_at"] if todo.get("created_at") else None,
                "updated_at": todo["updated_at"] if todo.get("updated_at") else None,
                "completed_at": todo["completed_at"] if todo.get("completed_at") else None
            }
            todo_list.append(formatted_todo)
        
        # Format thinking steps
        thinking_steps = []
        for step in thinking_steps_data:
            formatted_step = {
                "id": str(step["id"]),
                "session_id": str(step["thinking_session_id"]),
                "step_sequence": step["step_sequence"],
                "step_type": step["step_type"],
                "step_title": step["step_title"],
                "thinking_content": step["thinking_content"],
                "inputs_considered": step.get("inputs_considered", []),
                "conclusions_reached": step.get("conclusions_reached", []),
                "decisions_made": step.get("decisions_made", []),
                "next_steps_identified": step.get("next_steps_identified", []),
                "agent_role": step["agent_role"],
                "model_used": step.get("model_used"),
                "confidence_level": step["confidence_level"],
                "reasoning_quality": step["reasoning_quality"],
                "completion_status": step.get("completion_status"),
                "timestamp": step["created_at"] if step.get("created_at") else None
            }
            thinking_steps.append(formatted_step)
        
        # Determine execution order
        execution_order = []
        thinking_todos = [t for t in todo_list if t["type"] == "thinking"]
        asset_todos = [t for t in todo_list if t["type"] == "asset"]
        
        # Add thinking todos first
        for todo in thinking_todos:
            execution_order.append({
                "type": "thinking",
                "item": todo,
                "rationale": f"Thinking component per supportare: {', '.join(todo['supports_assets'])}" if todo['supports_assets'] else "Thinking strategico di supporto"
            })
        
        # Add asset todos by priority
        priority_order = {"high": 3, "medium": 2, "low": 1}
        sorted_assets = sorted(asset_todos, key=lambda x: priority_order.get(x.get('priority', 'medium'), 2), reverse=True)
        
        for todo in sorted_assets:
            execution_order.append({
                "type": "asset",
                "item": todo,
                "rationale": f"Asset deliverable priorità {todo['priority']}, impact {todo.get('user_impact', 'unknown')}"
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
        
        goal_thinking = {
            "goal_id": goal_id,
            "goal_description": goal["description"],
            "goal_progress": goal.get("progress", 0),
            "goal_status": goal["status"],
            "todo_list": todo_list,
            "thinking_steps": thinking_steps,
            "execution_order": execution_order,
            "current_step": current_step,
            "completion_status": completion_status,
            "decomposition_available": decomposition is not None,
            "user_value_score": decomposition["user_value_score"] if decomposition else 0,
            "complexity_level": decomposition["complexity_level"] if decomposition else "simple"
        }
        
        return {
            "success": True,
            "goal_thinking": goal_thinking
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting goal thinking process: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get thinking process: {str(e)}")

@router.get("/workspace/{workspace_id}/thinking/latest")
async def get_latest_thinking_steps(workspace_id: str, limit: int = 10):
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
async def thinking_api_health():
    """🏥 Health check for thinking API"""
    return {
        "service": "Authentic Thinking Process API",
        "status": "healthy",
        "database_connected": True,
        "timestamp": datetime.now().isoformat()
    }