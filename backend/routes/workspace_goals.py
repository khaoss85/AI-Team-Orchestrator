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

# Track goal extraction progress in memory
goal_extraction_progress = {}

@router.get("/workspaces/{workspace_id}/goals/progress")
async def get_goal_extraction_progress(workspace_id: str) -> Dict[str, Any]:
    """Get real-time progress of goal extraction process"""
    try:
        # Check if we have progress tracking for this workspace
        if workspace_id in goal_extraction_progress:
            progress_data = goal_extraction_progress[workspace_id]
            
            # Clean up completed progress after 5 minutes
            if progress_data.get("status") == "completed":
                elapsed = (datetime.now() - progress_data.get("completed_at", datetime.now())).seconds
                if elapsed > 300:  # 5 minutes
                    del goal_extraction_progress[workspace_id]
            
            return progress_data
        
        # Check if goals already exist (previously extracted)
        goals_response = supabase.table("workspace_goals").select("*").eq("workspace_id", workspace_id).execute()
        
        if goals_response.data:
            return {
                "status": "completed",
                "progress": 100,
                "message": "Analisi completata",
                "goals_count": len(goals_response.data),
                "phase": "done"
            }
        else:
            # No active extraction and no existing goals
            return {
                "status": "idle", 
                "progress": 0,
                "message": "In attesa di avviare l'analisi...",
                "goals_count": 0,
                "phase": "waiting"
            }
    except Exception as e:
        return {
            "status": "error",
            "progress": 0,
            "message": f"Errore durante l'analisi: {str(e)}",
            "goals_count": 0,
            "phase": "error"
        }

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
        
        # Initialize progress tracking
        goal_extraction_progress[workspace_id] = {
            "status": "in_progress",
            "progress": 10,
            "message": "Inizializzazione analisi AI...",
            "goals_count": 0,
            "phase": "initializing",
            "started_at": datetime.now()
        }
        
        # Update progress: Getting workspace context
        goal_extraction_progress[workspace_id].update({
            "progress": 20,
            "message": "Analisi del contesto del workspace...",
            "phase": "context_analysis"
        })
        
        # Get workspace context for strategic decomposition
        workspace_context = await _get_workspace_context(workspace_id)
        
        # Update progress: Starting AI extraction
        goal_extraction_progress[workspace_id].update({
            "progress": 35,
            "message": "Decomposizione strategica in corso...",
            "phase": "strategic_decomposition"
        })
        
        # Extract goals using AI with strategic decomposition
        extracted_goals = await goal_extractor.extract_goals_from_text(goal_text, workspace_context)
        
        # Update progress: Processing results
        goal_extraction_progress[workspace_id].update({
            "progress": 70,
            "message": f"Elaborazione di {len(extracted_goals)} obiettivi identificati...",
            "phase": "processing_goals",
            "goals_count": len(extracted_goals)
        })
        
        logger.info(f"🔍 Extracted {len(extracted_goals)} goals. First goal type: {type(extracted_goals[0]) if extracted_goals else 'None'}")
        
        # Separate final metrics from strategic deliverables for better UX
        final_metrics = []
        strategic_deliverables = []
        
        # Update progress: Categorizing goals
        goal_extraction_progress[workspace_id].update({
            "progress": 85,
            "message": "Categorizzazione obiettivi e deliverable...",
            "phase": "categorizing"
        })
        
        for goal in extracted_goals:
            # Handle both dict and dataclass objects
            if hasattr(goal, '__dict__'):  # dataclass
                goal_data = {
                    "id": f"preview_{len(final_metrics) + len(strategic_deliverables)}",
                    "value": goal.target_value,
                    "unit": goal.unit,
                    "type": goal.metric_type,
                    "description": _generate_simple_description_from_dataclass(goal),
                    "confidence": goal.confidence,
                    "editable": True,
                    "semantic_context": goal.semantic_context or {}
                }
                
                # Check if this is a strategic deliverable or final metric
                if hasattr(goal, 'semantic_context') and goal.semantic_context and goal.semantic_context.get('is_strategic_deliverable'):
                    goal_data["deliverable_type"] = goal.semantic_context.get('deliverable_type', '')
                    goal_data["business_value"] = goal.semantic_context.get('business_value', '')
                    goal_data["acceptance_criteria"] = goal.semantic_context.get('acceptance_criteria', [])
                    goal_data["execution_phase"] = goal.semantic_context.get('execution_phase', '')
                    # AI Autonomy fields
                    goal_data["autonomy_level"] = goal.semantic_context.get('autonomy_level', 'autonomous')
                    goal_data["autonomy_reason"] = goal.semantic_context.get('autonomy_reason', '')
                    goal_data["available_tools"] = goal.semantic_context.get('available_tools', [])
                    goal_data["human_input_required"] = goal.semantic_context.get('human_input_required', [])
                    strategic_deliverables.append(goal_data)
                else:
                    final_metrics.append(goal_data)
            else:  # dict
                goal_data = {
                    "id": f"preview_{len(final_metrics) + len(strategic_deliverables)}",
                    "value": goal.get("target_value", 0),
                    "unit": goal.get("unit", ""),
                    "type": goal.get("metric_type", "deliverables"),
                    "description": _generate_simple_description(goal),
                    "confidence": goal.get("confidence", 0.9),
                    "editable": True,
                    "semantic_context": goal.get("semantic_context", {})
                }
                
                # Check semantic context for strategic deliverable markers
                context = goal.get("semantic_context", {})
                if context.get('is_strategic_deliverable'):
                    goal_data["deliverable_type"] = context.get('deliverable_type', '')
                    goal_data["business_value"] = context.get('business_value', '')
                    goal_data["acceptance_criteria"] = context.get('acceptance_criteria', [])
                    goal_data["execution_phase"] = context.get('execution_phase', '')
                    # AI Autonomy fields
                    goal_data["autonomy_level"] = context.get('autonomy_level', 'autonomous')
                    goal_data["autonomy_reason"] = context.get('autonomy_reason', '')
                    goal_data["available_tools"] = context.get('available_tools', [])
                    goal_data["human_input_required"] = context.get('human_input_required', [])
                    strategic_deliverables.append(goal_data)
                else:
                    final_metrics.append(goal_data)
        
        total_goals = len(final_metrics) + len(strategic_deliverables)
        
        # Update progress: Completed
        goal_extraction_progress[workspace_id].update({
            "status": "preview_ready",
            "progress": 95,
            "message": "Analisi completata! Pronto per la conferma.",
            "phase": "preview_ready",
            "goals_count": total_goals,
            "final_metrics_count": len(final_metrics),
            "strategic_deliverables_count": len(strategic_deliverables)
        })
        
        return {
            "success": True,
            "original_goal": goal_text,
            "final_metrics": final_metrics,
            "strategic_deliverables": strategic_deliverables,
            "extracted_goals": final_metrics + strategic_deliverables,  # For backward compatibility
            "summary": {
                "total_goals": total_goals,
                "final_metrics_count": len(final_metrics),
                "strategic_deliverables_count": len(strategic_deliverables)
            },
            "message": f"Ho identificato {len(final_metrics)} metriche finali e {len(strategic_deliverables)} deliverable strategici"
        }
        
    except HTTPException:
        # Update progress with error
        if workspace_id in goal_extraction_progress:
            goal_extraction_progress[workspace_id].update({
                "status": "error",
                "progress": 0,
                "phase": "error"
            })
        raise
    except Exception as e:
        logger.error(f"Error previewing goals: {e}")
        # Update progress with error
        if workspace_id in goal_extraction_progress:
            goal_extraction_progress[workspace_id].update({
                "status": "error",
                "progress": 0,
                "message": f"Errore: {str(e)}",
                "phase": "error"
            })
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
            # 🎯 IMPROVED: Create unique metric_type for each deliverable/goal
            base_metric_type = goal.get("type", "deliverables")
            goal_description = goal.get("description", "")
            
            # Generate unique metric_type based on content for deliverables
            if base_metric_type == "deliverables":
                # Create semantic identifier from description for uniqueness
                import re
                clean_desc = re.sub(r'[^a-zA-Z0-9\s]', '', goal_description.lower())
                words = clean_desc.split()[:3]  # First 3 significant words
                if words:
                    semantic_id = "_".join(words)
                    metric_type = f"deliverable_{semantic_id}"
                else:
                    # Fallback to index-based if no good words
                    metric_type = f"deliverable_{len(saved_goals) + 1}"
            else:
                # Keep original metric_type for non-deliverable goals (metrics, timelines, etc.)
                metric_type = base_metric_type
            
            # Check if goal with this EXACT metric_type already exists
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
                    "confidence": float(goal.get("confidence", 0.9)),
                    "base_type": base_metric_type,  # Keep track of original type
                    "semantic_context": goal.get("semantic_context", {}),
                    # Store deliverable-specific metadata if available
                    "deliverable_type": goal.get("deliverable_type", ""),
                    "business_value": goal.get("business_value", ""),
                    "acceptance_criteria": goal.get("acceptance_criteria", []),
                    "execution_phase": goal.get("execution_phase", ""),
                    "autonomy_level": goal.get("autonomy_level", "autonomous"),
                    "autonomy_reason": goal.get("autonomy_reason", ""),
                    "available_tools": goal.get("available_tools", []),
                    "human_input_required": goal.get("human_input_required", [])
                }
            }
            
            if existing_response.data:
                # Update existing goal (should be rare now with unique metric_types)
                result = supabase.table("workspace_goals").update(goal_data).eq(
                    "workspace_id", str(workspace_id)
                ).eq("metric_type", metric_type).execute()
                logger.info(f"✅ Updated existing goal: {metric_type}")
            else:
                # Create new goal (most common case now)
                goal_data.update({
                    "workspace_id": str(workspace_id),
                    "metric_type": metric_type
                })
                result = supabase.table("workspace_goals").insert(goal_data).execute()
                logger.info(f"✅ Created new goal: {metric_type} -> {goal_description[:50]}...")
            
            if result.data:
                saved_goals.append(result.data[0])
        
        # Mark progress as completed
        if workspace_id in goal_extraction_progress:
            goal_extraction_progress[workspace_id] = {
                "status": "completed",
                "progress": 100,
                "message": f"✅ {len(saved_goals)} obiettivi salvati con successo!",
                "phase": "done",
                "goals_count": len(saved_goals),
                "completed_at": datetime.now()
            }
        
        # 🚨 NOTE: We do NOT trigger task generation here!
        # Tasks can only be executed AFTER the team is approved.
        # The auto-start will happen when the team proposal is approved.
        logger.info(f"✅ {len(saved_goals)} goals confirmed. Waiting for team approval before task generation.")
        
        # 📋 CREATE PROJECT DESCRIPTION ARTIFACT
        # Save comprehensive project description for easy reference
        try:
            await _create_project_description_artifact(str(workspace_id), saved_goals, confirmed_goals)
            logger.info("✅ Project description artifact created successfully")
        except Exception as e:
            logger.warning(f"⚠️ Failed to create project description artifact: {e}")
            # Don't fail the goal confirmation, just log the warning
        
        return {
            "success": True,
            "saved_goals": len(saved_goals),
            "message": f"✅ {len(saved_goals)} obiettivi confermati e team avviato automaticamente!"
        }
        
    except HTTPException:
        # Update progress with error
        if workspace_id in goal_extraction_progress:
            goal_extraction_progress[workspace_id].update({
                "status": "error",
                "progress": 0,
                "message": "Errore nel salvataggio degli obiettivi",
                "phase": "error"
            })
        raise
    except Exception as e:
        logger.error(f"Error confirming goals: {e}")
        # Update progress with error
        if workspace_id in goal_extraction_progress:
            goal_extraction_progress[workspace_id].update({
                "status": "error",
                "progress": 0,
                "message": f"Errore: {str(e)}",
                "phase": "error"
            })
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
    metric_type: Optional[str] = Query(None, description="Filter by metric type"),
    deliverables_only: Optional[bool] = Query(False, description="Return only deliverable goals")
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
        
        # Filter for deliverables only if requested
        if deliverables_only:
            goals = [g for g in goals if g["metric_type"].startswith("deliverable_") or g["metric_type"] == "deliverables"]
        
        # Separate deliverables from other metrics for better organization
        deliverable_goals = []
        metric_goals = []
        
        for goal in goals:
            # Check if this is a deliverable based on metric_type or metadata
            if (goal["metric_type"].startswith("deliverable_") or 
                goal["metric_type"] == "deliverables" or
                (goal.get("metadata", {}).get("base_type") == "deliverables")):
                deliverable_goals.append(goal)
            else:
                metric_goals.append(goal)
        
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
            "deliverable_goals": deliverable_goals,
            "metric_goals": metric_goals,
            "summary": {
                "total_goals": total_goals,
                "deliverable_goals_count": len(deliverable_goals),
                "metric_goals_count": len(metric_goals),
                "active_goals": active_goals,
                "completed_goals": completed_goals,
                "overall_progress_pct": round(overall_progress, 1)
            },
            "message": f"Found {len(deliverable_goals)} deliverables and {len(metric_goals)} metrics"
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

@router.post("/workspaces/{workspace_id}/goals/{goal_id}/reactivate")
async def reactivate_blocked_goal(
    workspace_id: str,
    goal_id: str
) -> Dict[str, Any]:
    """
    🔄 Reactivate a blocked/failed goal and analyze blockers
    
    This endpoint:
    1. Changes goal status from BLOCKED/FAILED -> ACTIVE
    2. Analyzes what's blocking the goal 
    3. Creates corrective tasks to unblock it
    4. Triggers immediate task generation
    """
    try:
        # Verify goal exists and is in a reactivatable state
        goal_response = supabase.table("workspace_goals").select("*").eq(
            "id", goal_id
        ).eq("workspace_id", workspace_id).execute()
        
        if not goal_response.data:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        goal = goal_response.data[0]
        current_status = goal.get("status")
        
        if current_status not in [GoalStatus.BLOCKED.value, GoalStatus.FAILED.value, GoalStatus.NEEDS_ATTENTION.value]:
            raise HTTPException(
                status_code=400, 
                detail=f"Goal is {current_status} and cannot be reactivated. Only blocked/failed goals can be reactivated."
            )
        
        # 1. Reactivate the goal
        update_data = {
            "status": GoalStatus.ACTIVE.value,
            "updated_at": datetime.now().isoformat(),
            "metadata": {
                **goal.get("metadata", {}),
                "reactivated_at": datetime.now().isoformat(),
                "previous_status": current_status,
                "reactivation_count": goal.get("metadata", {}).get("reactivation_count", 0) + 1
            }
        }
        
        result = supabase.table("workspace_goals").update(update_data).eq(
            "id", goal_id
        ).eq("workspace_id", workspace_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to reactivate goal")
        
        # 2. Analyze blockers and create corrective tasks
        blocker_analysis = await _analyze_goal_blockers(workspace_id, goal)
        
        # 3. Trigger immediate task generation for the reactivated goal
        logger.info(f"🔄 Goal {goal_id} reactivated, triggering immediate task generation")
        try:
            from automated_goal_monitor import automated_goal_monitor
            import asyncio
            
            # Trigger focused analysis for this specific goal
            asyncio.create_task(automated_goal_monitor._trigger_immediate_goal_analysis(workspace_id))
            logger.info("✅ Immediate task generation triggered for reactivated goal")
        except Exception as e:
            logger.warning(f"⚠️ Failed to trigger immediate task generation: {e}")
        
        return {
            "success": True,
            "goal_id": goal_id,
            "previous_status": current_status,
            "new_status": "active",
            "blockers_found": len(blocker_analysis.get("blockers", [])),
            "corrective_actions": blocker_analysis.get("corrective_actions", []),
            "message": f"✅ Goal reactivated successfully. {len(blocker_analysis.get('blockers', []))} blockers identified."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reactivating goal {goal_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error reactivating goal: {str(e)}")

async def _analyze_goal_blockers(workspace_id: str, goal: Dict[str, Any]) -> Dict[str, Any]:
    """
    🔍 Analyze what's blocking a goal and suggest corrective actions
    """
    try:
        blockers = []
        corrective_actions = []
        
        # 1. Check for failed/incomplete tasks
        failed_tasks_response = supabase.table("tasks").select("*").eq(
            "workspace_id", workspace_id
        ).in_("status", ["failed", "stale", "timed_out"]).execute()
        
        if failed_tasks_response.data:
            blockers.append({
                "type": "failed_tasks",
                "count": len(failed_tasks_response.data),
                "description": f"{len(failed_tasks_response.data)} tasks have failed or timed out"
            })
            corrective_actions.append("Retry failed tasks with updated parameters")
        
        # 2. Check for low completion rate
        all_tasks_response = supabase.table("tasks").select("status").eq(
            "workspace_id", workspace_id
        ).execute()
        
        if all_tasks_response.data:
            total_tasks = len(all_tasks_response.data)
            completed_tasks = len([t for t in all_tasks_response.data if t["status"] == "completed"])
            completion_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
            
            if completion_rate < 50:
                blockers.append({
                    "type": "low_completion_rate",
                    "completion_rate": completion_rate,
                    "description": f"Only {completion_rate:.1f}% of tasks completed"
                })
                corrective_actions.append("Create more focused, achievable tasks")
        
        # 3. Check for resource constraints
        current_value = goal.get("current_value", 0)
        target_value = goal.get("target_value", 1)
        progress_pct = (current_value / target_value) * 100 if target_value > 0 else 0
        
        if progress_pct < 10:
            blockers.append({
                "type": "no_progress",
                "progress_pct": progress_pct,
                "description": f"No significant progress made ({progress_pct:.1f}% complete)"
            })
            corrective_actions.append("Break down goal into smaller, more achievable milestones")
        
        return {
            "blockers": blockers,
            "corrective_actions": corrective_actions,
            "total_blockers": len(blockers)
        }
        
    except Exception as e:
        logger.error(f"Error analyzing goal blockers: {e}")
        return {"blockers": [], "corrective_actions": [], "error": str(e)}

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
    
    # Check if it's a strategic deliverable
    if hasattr(goal, 'semantic_context') and goal.semantic_context and goal.semantic_context.get('is_strategic_deliverable'):
        deliverable_type = goal.semantic_context.get('deliverable_type', '')
        if deliverable_type == 'contact_list':
            return f"Lista di {int(target_value)} contatti ICP qualificati"
        elif deliverable_type == 'email_sequence':
            return f"Sequenza email per nurturing e conversioni"
        elif deliverable_type == 'email_performance_monitoring':
            return f"Framework di monitoraggio performance email"
        elif deliverable_type == 'audience_analysis':
            return f"Analisi completa del target audience"
        else:
            return goal.description if hasattr(goal, 'description') else f"Creare {deliverable_type.replace('_', ' ')}"
    
    # Final metrics descriptions
    if metric_type == "contacts":
        return f"Raccogliere {int(target_value)} contatti ICP qualificati"
    elif metric_type == "conversion_rate":
        if "open" in unit.lower():
            return f"Raggiungere {target_value}% di open rate nelle email"
        else:
            return f"Raggiungere {target_value}% di tasso di conversione"
    elif metric_type == "engagement_rate":
        return f"Raggiungere {target_value}% di click-through rate"
    elif "email" in unit.lower() or "sequence" in unit.lower():
        return f"Creare {int(target_value)} sequenze email"
    elif "%" in unit or "percentage" in unit.lower():
        return f"Raggiungere {target_value}% di {metric_type}"
    elif "day" in unit.lower() or "week" in unit.lower() or "giorni" in unit.lower():
        return f"Completare in {target_value} {unit}"
    else:
        return f"Raggiungere {target_value} {unit}"

async def _get_workspace_context(workspace_id: str) -> Dict[str, Any]:
    """
    🏢 Recupera contesto del workspace per la decomposizione strategica
    """
    try:
        # Get workspace basic info
        workspace_response = supabase.table("workspaces").select("*").eq("id", workspace_id).execute()
        
        workspace_context = {}
        
        if workspace_response.data:
            workspace = workspace_response.data[0]
            workspace_context.update({
                "workspace_name": workspace.get("name", ""),
                "workspace_description": workspace.get("description", ""),
                "original_goal": workspace.get("goal", ""),
                "workspace_status": workspace.get("status", ""),
                "created_at": workspace.get("created_at", "")
            })
        
        # Get existing agents for capability context
        agents_response = supabase.table("agents").select("role, seniority, description").eq("workspace_id", workspace_id).execute()
        
        if agents_response.data:
            workspace_context["existing_agents"] = [
                {
                    "role": agent.get("role", ""),
                    "seniority": agent.get("seniority", ""),
                    "description": agent.get("description", "")
                }
                for agent in agents_response.data
            ]
        
        # Get existing tasks for current work context
        tasks_response = supabase.table("tasks").select("name, description, status").eq("workspace_id", workspace_id).limit(10).execute()
        
        if tasks_response.data:
            workspace_context["recent_tasks"] = [
                {
                    "name": task.get("name", ""),
                    "description": task.get("description", ""),
                    "status": task.get("status", "")
                }
                for task in tasks_response.data
            ]
        
        # Get existing goals to avoid duplication
        goals_response = supabase.table("workspace_goals").select("metric_type, target_value, description").eq("workspace_id", workspace_id).execute()
        
        if goals_response.data:
            workspace_context["existing_goals"] = [
                {
                    "metric_type": goal.get("metric_type", ""),
                    "target_value": goal.get("target_value", 0),
                    "description": goal.get("description", "")
                }
                for goal in goals_response.data
            ]
        
        logger.info(f"🏢 Workspace context for {workspace_id}: {len(workspace_context.get('existing_agents', []))} agents, {len(workspace_context.get('existing_goals', []))} goals")
        return workspace_context
        
    except Exception as e:
        logger.error(f"Failed to get workspace context: {e}")
        return {}

async def _create_project_description_artifact(
    workspace_id: str, 
    saved_goals: List[Dict], 
    original_goals_data: List[Dict]
) -> Dict[str, Any]:
    """
    📋 Create a comprehensive project description artifact
    
    This saves the full project description, goals, and context for easy reference
    in the conversational interface.
    """
    try:
        # Get workspace details
        workspace_response = supabase.table("workspaces").select("*").eq("id", workspace_id).execute()
        if not workspace_response.data:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        workspace = workspace_response.data[0]
        
        # Prepare comprehensive project description
        project_description = {
            "workspace_id": workspace_id,
            "project_name": workspace.get("name", "Unnamed Project"),
            "project_description": workspace.get("description", ""),
            "original_goal": workspace.get("goal", ""),
            "confirmed_goals": saved_goals,
            "total_goals": len(saved_goals),
            "strategic_deliverables": [g for g in saved_goals if g.get("metadata", {}).get("base_type") == "deliverables"],
            "metrics_goals": [g for g in saved_goals if g.get("metadata", {}).get("base_type") != "deliverables"],
            "estimated_budget": workspace.get("budget", {}).get("max_budget", 10),
            "max_iterations": workspace.get("budget", {}).get("max_iterations", 3),
            "quality_threshold": workspace.get("budget", {}).get("settings", {}).get("quality_threshold", 85),
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        # Calculate project metrics
        total_target_value = sum(goal.get("target_value", 0) for goal in saved_goals)
        project_description["total_target_value"] = total_target_value
        project_description["avg_confidence"] = sum(
            goal.get("metadata", {}).get("confidence", 0.9) for goal in saved_goals
        ) / len(saved_goals) if saved_goals else 0.9
        
        # Create formatted description for display
        formatted_description = f"""# {project_description['project_name']}

## Project Overview
{project_description['project_description']}

## Original Goal Statement
{project_description['original_goal']}

## Confirmed Objectives ({len(saved_goals)} total)

### Strategic Deliverables ({len(project_description['strategic_deliverables'])})
"""
        
        for goal in project_description['strategic_deliverables']:
            formatted_description += f"- **{goal.get('metric_type', 'Unknown')}**: {goal.get('description', '')} (Target: {goal.get('target_value', 0)} {goal.get('unit', '')})\n"
        
        formatted_description += f"""
### Metrics & KPIs ({len(project_description['metrics_goals'])})
"""
        
        for goal in project_description['metrics_goals']:
            formatted_description += f"- **{goal.get('metric_type', 'Unknown')}**: {goal.get('description', '')} (Target: {goal.get('target_value', 0)} {goal.get('unit', '')})\n"
        
        formatted_description += f"""
## Project Configuration
- **Budget**: ${project_description['estimated_budget']}
- **Max Iterations**: {project_description['max_iterations']} per task
- **Quality Threshold**: {project_description['quality_threshold']}%
- **Total Target Value**: {total_target_value} units
- **Average Confidence**: {project_description['avg_confidence']:.1%}

## Next Steps
✅ Goals confirmed and saved to database
🚀 Team automatically triggered for task execution
📊 Progress tracking active across all objectives

*Generated on {datetime.now().strftime("%Y-%m-%d at %H:%M:%S")}*
"""
        
        # Save to database - we can use the existing conversations table for artifacts
        artifact_data = {
            "workspace_id": workspace_id,
            "content": formatted_description,
            "metadata": project_description,
            "type": "project_description_artifact",
            "created_at": datetime.now().isoformat()
        }
        
        # Store in conversations table as an AI message with special type
        conversation_data = {
            "workspace_id": workspace_id,
            "message_type": "ai_response",
            "content": formatted_description,
            "metadata": {
                "artifact_type": "project_description",
                "project_data": project_description,
                "auto_generated": True,
                "goals_count": len(saved_goals)
            },
            "created_at": datetime.now().isoformat()
        }
        
        response = supabase.table("conversations").insert(conversation_data).execute()
        
        if response.data:
            logger.info(f"✅ Project description artifact created with ID: {response.data[0]['id']}")
            return {
                "success": True,
                "artifact_id": response.data[0]["id"],
                "description_length": len(formatted_description),
                "goals_included": len(saved_goals)
            }
        else:
            raise Exception("Failed to insert project description artifact")
            
    except Exception as e:
        logger.error(f"Error creating project description artifact: {e}")
        raise e