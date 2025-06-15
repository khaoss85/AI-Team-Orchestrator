# routes/workspace_goals.py
"""
🎯 Workspace Goals Management API
Gestisce CRUD operations per workspace goals e integrazione con goal-driven system
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

from database import supabase
from models import (
    WorkspaceGoal, 
    WorkspaceGoalCreate, 
    WorkspaceGoalUpdate,
    GoalMetricType,
    GoalStatus
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["workspace-goals"])

# Initialize AI Goal Extractor
goal_extractor = None
try:
    from ai_quality_assurance.ai_goal_extractor import AIGoalExtractor
    goal_extractor = AIGoalExtractor()
    logger.info("✅ AI Goal Extractor initialized in routes")
except Exception as e:
    logger.error(f"Failed to initialize AI Goal Extractor: {e}")

@router.post("/workspaces/{workspace_id}/goals/preview")
async def preview_goals(
    workspace_id: str,
    request: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Preview AI-extracted goals without saving to database
    Returns simplified goal breakdown for user confirmation
    """
    try:
        goal_text = request.get("goal", "")
        if not goal_text:
            raise HTTPException(
                status_code=400,
                detail="Goal text is required"
            )
        
        if not goal_extractor:
            raise HTTPException(
                status_code=503,
                detail="AI Goal Extractor not available"
            )
        
        # Extract goals using AI
        extracted_goals = await goal_extractor.extract_goals_from_text(goal_text)
        
        logger.info(f"🔍 Extracted {len(extracted_goals)} goals. First goal type: {type(extracted_goals[0]) if extracted_goals else 'None'}")
        
        # Simplify for frontend display
        simplified_goals = []
        for goal in extracted_goals:
            # Handle both dict and dataclass objects
            if hasattr(goal, '__dict__'):  # dataclass
                simplified_goals.append({
                    "id": f"preview_{len(simplified_goals)}",  # Temporary ID
                    "value": goal.target_value,
                    "unit": goal.unit,
                    "type": goal.metric_type,
                    "description": _generate_simple_description_from_dataclass(goal),
                    "confidence": goal.confidence,
                    "editable": True
                })
            else:  # dict
                simplified_goals.append({
                    "id": f"preview_{len(simplified_goals)}",  # Temporary ID
                    "value": goal.get("target_value", 0),
                    "unit": goal.get("unit", ""),
                    "type": goal.get("metric_type", "deliverables"),
                    "description": _generate_simple_description(goal),
                    "confidence": goal.get("confidence", 0.9),
                    "editable": True
                })
        
        return {
            "success": True,
            "original_goal": goal_text,
            "extracted_goals": simplified_goals,
            "message": f"Ho identificato {len(simplified_goals)} obiettivi"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing goals: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error extracting goals: {str(e)}"
        )

@router.post("/workspaces/{workspace_id}/goals/confirm")
async def confirm_goals(
    workspace_id: str,
    request: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Confirm and save user-approved goals to database
    """
    try:
        confirmed_goals = request.get("goals", [])
        
        if not confirmed_goals:
            raise HTTPException(
                status_code=400,
                detail="At least one goal is required"
            )
        
        # Save confirmed goals to database (update existing or create new)
        saved_goals = []
        
        for goal in confirmed_goals:
            metric_type = goal.get("type", "deliverables")
            
            # Check if goal with this metric_type already exists
            existing_response = supabase.table("workspace_goals").select("*").eq(
                "workspace_id", str(workspace_id)
            ).eq("metric_type", metric_type).execute()
            
            goal_data = {
                "target_value": float(goal.get("value", 0)),
                "unit": goal.get("unit", ""),
                "description": goal.get("description", ""),
                "priority": 1,  # Default priority
                "metadata": {
                    "user_confirmed": True,
                    "original_extraction": goal.get("id", "").startswith("preview_"),
                    "confidence": float(goal.get("confidence", 0.9))
                }
            }
            
            if existing_response.data:
                # Update existing goal
                result = supabase.table("workspace_goals").update(goal_data).eq(
                    "workspace_id", str(workspace_id)
                ).eq("metric_type", metric_type).execute()
                logger.info(f"✅ Updated existing goal: {metric_type}")
            else:
                # Create new goal
                goal_data.update({
                    "workspace_id": str(workspace_id),
                    "metric_type": metric_type
                })
                result = supabase.table("workspace_goals").insert(goal_data).execute()
                logger.info(f"✅ Created new goal: {metric_type}")
            
            if result.data:
                saved_goals.append(result.data[0])
        
        return {
            "success": True,
            "saved_goals": len(saved_goals),
            "message": f"✅ {len(saved_goals)} obiettivi confermati"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming goals: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error saving goals: {str(e)}"
        )

@router.post("/workspaces/{workspace_id}/goals")
async def create_workspace_goal(
    workspace_id: str,
    goal_data: WorkspaceGoalCreate
) -> Dict[str, Any]:
    """Create a new workspace goal"""
    try:
        # Validate workspace exists
        workspace_response = supabase.table("workspaces").select("id").eq("id", workspace_id).execute()
        if not workspace_response.data:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        # Create goal
        goal_insert_data = {
            **goal_data.dict(),
            "workspace_id": workspace_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        response = supabase.table("workspace_goals").insert(goal_insert_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create goal")
        
        created_goal = response.data[0]
        
        # Log goal creation
        await _log_goal_event(workspace_id, created_goal["id"], "goal_created", {
            "metric_type": created_goal["metric_type"],
            "target_value": created_goal["target_value"]
        })
        
        return {
            "success": True,
            "goal": created_goal,
            "message": f"Goal created: {created_goal['metric_type']} target {created_goal['target_value']}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating goal: {str(e)}")

@router.get("/workspaces/{workspace_id}/goals")
async def get_workspace_goals(
    workspace_id: str,
    status: Optional[str] = Query(None, description="Filter by status"),
    metric_type: Optional[str] = Query(None, description="Filter by metric type")
) -> Dict[str, Any]:
    """Get all goals for a workspace with optional filtering"""
    try:
        query = supabase.table("workspace_goals").select("*").eq("workspace_id", workspace_id)
        
        # Apply filters
        if status:
            query = query.eq("status", status)
        if metric_type:
            query = query.eq("metric_type", metric_type)
        
        # Order by priority and creation date
        query = query.order("priority").order("created_at", desc=True)
        
        response = query.execute()
        goals = response.data or []
        
        # Calculate summary statistics
        total_goals = len(goals)
        active_goals = len([g for g in goals if g["status"] == "active"])
        completed_goals = len([g for g in goals if g["status"] == "completed"])
        
        # Calculate overall progress
        overall_progress = 0.0
        if active_goals > 0:
            progress_sum = sum(
                (g["current_value"] / g["target_value"] * 100) if g["target_value"] > 0 else 0
                for g in goals if g["status"] == "active"
            )
            overall_progress = progress_sum / active_goals
        
        return {
            "success": True,
            "goals": goals,
            "summary": {
                "total_goals": total_goals,
                "active_goals": active_goals,
                "completed_goals": completed_goals,
                "overall_progress_pct": round(overall_progress, 1)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching goals: {str(e)}")

@router.put("/workspaces/{workspace_id}/goals/{goal_id}/progress")
async def update_goal_progress(
    workspace_id: str,
    goal_id: str,
    progress_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Update goal progress (usually called when tasks complete)"""
    try:
        increment = progress_data.get("increment", 0)
        task_id = progress_data.get("task_id")
        contribution_type = progress_data.get("contribution_type", "task_completion")
        
        # Get current goal
        goal_response = supabase.table("workspace_goals").select("*").eq(
            "id", goal_id
        ).eq("workspace_id", workspace_id).execute()
        
        if not goal_response.data:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        goal = goal_response.data[0]
        old_value = goal["current_value"]
        new_value = old_value + increment
        
        # Ensure we don't exceed target
        new_value = min(new_value, goal["target_value"])
        
        # Update goal progress
        update_response = supabase.table("workspace_goals").update({
            "current_value": new_value,
            "updated_at": datetime.now().isoformat(),
            "last_progress_date": datetime.now().isoformat()
        }).eq("id", goal_id).execute()
        
        if not update_response.data:
            raise HTTPException(status_code=500, detail="Failed to update goal progress")
        
        updated_goal = update_response.data[0]
        completion_pct = (new_value / goal["target_value"] * 100) if goal["target_value"] > 0 else 0
        
        # Log progress update
        await _log_goal_event(workspace_id, goal_id, "progress_updated", {
            "old_value": old_value,
            "new_value": new_value,
            "increment": increment,
            "completion_pct": completion_pct,
            "task_id": task_id,
            "contribution_type": contribution_type
        })
        
        # Check if goal is completed
        if new_value >= goal["target_value"] and goal["status"] != "completed":
            supabase.table("workspace_goals").update({
                "status": "completed",
                "completed_at": datetime.now().isoformat()
            }).eq("id", goal_id).execute()
            
            await _log_goal_event(workspace_id, goal_id, "goal_completed", {
                "final_value": new_value,
                "target_value": goal["target_value"]
            })
        
        return {
            "success": True,
            "goal": updated_goal,
            "progress": {
                "old_value": old_value,
                "new_value": new_value,
                "increment": increment,
                "completion_pct": round(completion_pct, 1),
                "is_completed": new_value >= goal["target_value"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating goal progress: {str(e)}")

@router.put("/workspaces/{workspace_id}/goals/{goal_id}")
async def update_workspace_goal(
    workspace_id: str,
    goal_id: str,
    goal_update: WorkspaceGoalUpdate
) -> Dict[str, Any]:
    """Update a workspace goal"""
    try:
        # Verify goal exists and belongs to workspace
        existing_response = supabase.table("workspace_goals").select("*").eq(
            "id", goal_id
        ).eq("workspace_id", workspace_id).execute()
        
        if not existing_response.data:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        # Prepare update data
        update_data = {
            **goal_update.dict(exclude_unset=True),
            "updated_at": datetime.now().isoformat()
        }
        
        # Update goal
        response = supabase.table("workspace_goals").update(update_data).eq("id", goal_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to update goal")
        
        updated_goal = response.data[0]
        
        return {
            "success": True,
            "goal": updated_goal,
            "message": "Goal updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating goal: {str(e)}")

@router.delete("/workspaces/{workspace_id}/goals/{goal_id}")
async def delete_workspace_goal(
    workspace_id: str,
    goal_id: str
) -> Dict[str, Any]:
    """Delete a workspace goal"""
    try:
        # Verify goal exists and belongs to workspace
        existing_response = supabase.table("workspace_goals").select("*").eq(
            "id", goal_id
        ).eq("workspace_id", workspace_id).execute()
        
        if not existing_response.data:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        goal = existing_response.data[0]
        
        # Check if goal has active tasks
        tasks_response = supabase.table("tasks").select("id").eq(
            "goal_id", goal_id
        ).eq("status", "pending").execute()
        
        if tasks_response.data:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot delete goal with {len(tasks_response.data)} active tasks"
            )
        
        # Delete goal
        delete_response = supabase.table("workspace_goals").delete().eq("id", goal_id).execute()
        
        if not delete_response.data:
            raise HTTPException(status_code=500, detail="Failed to delete goal")
        
        # Log deletion
        await _log_goal_event(workspace_id, goal_id, "goal_deleted", {
            "metric_type": goal["metric_type"],
            "progress_at_deletion": f"{goal['current_value']}/{goal['target_value']}"
        })
        
        return {
            "success": True,
            "message": f"Goal '{goal['metric_type']}' deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting goal: {str(e)}")

@router.get("/workspaces/{workspace_id}/goals/unmet")
async def get_unmet_goals(
    workspace_id: str,
    threshold_pct: float = Query(80.0, description="Completion threshold for 'unmet' classification")
) -> Dict[str, Any]:
    """Get goals that haven't met their targets (used by goal-driven task planner)"""
    try:
        response = supabase.table("workspace_goals").select("*").eq(
            "workspace_id", workspace_id
        ).eq("status", "active").execute()
        
        goals = response.data or []
        unmet_goals = []
        
        for goal in goals:
            completion_pct = (goal["current_value"] / goal["target_value"] * 100) if goal["target_value"] > 0 else 0
            
            if completion_pct < threshold_pct:
                gap = goal["target_value"] - goal["current_value"]
                unmet_goals.append({
                    **goal,
                    "completion_pct": round(completion_pct, 1),
                    "gap_value": gap,
                    "urgency_score": _calculate_urgency_score(goal, completion_pct)
                })
        
        # Sort by urgency score
        unmet_goals.sort(key=lambda g: g["urgency_score"], reverse=True)
        
        return {
            "success": True,
            "unmet_goals": unmet_goals,
            "summary": {
                "total_unmet": len(unmet_goals),
                "avg_completion_pct": round(
                    sum(g["completion_pct"] for g in unmet_goals) / len(unmet_goals), 1
                ) if unmet_goals else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching unmet goals: {str(e)}")

# Helper functions

async def _log_goal_event(workspace_id: str, goal_id: str, event_type: str, metadata: Dict[str, Any]):
    """Log goal-related events for monitoring and analytics"""
    try:
        log_data = {
            "workspace_id": workspace_id,
            "type": f"goal_{event_type}",
            "message": f"Goal {event_type}: {goal_id}",
            "metadata": {
                "goal_id": goal_id,
                "event_type": event_type,
                **metadata
            }
        }
        
        supabase.table("logs").insert(log_data).execute()
    except Exception as e:
        # Don't fail the main operation if logging fails
        print(f"Warning: Failed to log goal event: {e}")

def _calculate_urgency_score(goal: Dict[str, Any], completion_pct: float) -> float:
    """Calculate urgency score for unmet goals (higher = more urgent)"""
    base_urgency = 100 - completion_pct  # Lower completion = higher urgency
    
    # Priority multiplier
    priority_multiplier = goal.get("priority", 1)
    
    # Time-based urgency (if goal has deadline)
    time_urgency = 1.0
    if goal.get("target_date"):
        # Could add deadline-based urgency calculation here
        pass
    
    return base_urgency * priority_multiplier * time_urgency

def _generate_simple_description(goal: Dict[str, Any]) -> str:
    """Generate simple Italian description for goal"""
    metric_type = goal.get("metric_type", "")
    target_value = goal.get("target_value", 0)
    unit = goal.get("unit", "")
    
    # Simple descriptions in Italian
    if "contact" in unit.lower() or "contatti" in unit.lower():
        return f"Raccogliere {int(target_value)} contatti qualificati"
    elif "email" in unit.lower() or "sequence" in unit.lower():
        return f"Creare {int(target_value)} sequenze email"
    elif "%" in unit:
        return f"Raggiungere {target_value}% di {metric_type}"
    elif "day" in unit.lower() or "week" in unit.lower() or "giorni" in unit.lower():
        return f"Completare in {target_value} {unit}"
    else:
        return f"Raggiungere {target_value} {unit}"

def _generate_simple_description_from_dataclass(goal) -> str:
    """Generate simple Italian description for goal from dataclass"""
    metric_type = goal.metric_type
    target_value = goal.target_value
    unit = goal.unit
    
    # Simple descriptions in Italian
    if "contact" in unit.lower() or "contatti" in unit.lower():
        return f"Raccogliere {int(target_value)} contatti qualificati"
    elif "email" in unit.lower() or "sequence" in unit.lower():
        return f"Creare {int(target_value)} sequenze email"
    elif "%" in unit:
        return f"Raggiungere {target_value}% di {metric_type}"
    elif "day" in unit.lower() or "week" in unit.lower() or "giorni" in unit.lower():
        return f"Completare in {target_value} {unit}"
    else:
        return f"Raggiungere {target_value} {unit}"