# backend/routes/goal_validation.py

from fastapi import Request, APIRouter, HTTPException, status, Query
from typing import List, Dict, Any, Optional
from middleware.trace_middleware import get_trace_id, create_traced_logger, TracedDatabaseOperation
from uuid import UUID
import logging
from datetime import datetime

from ai_quality_assurance.unified_quality_engine import goal_validator, ValidationSeverity
from ai_quality_assurance.unified_quality_engine import quality_gates, GateStatus
from database import get_workspace, list_tasks
from models import TaskStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/goal-validation", tags=["goal-validation"])

# Compatibility endpoint for E2E tests
@router.post("/trigger-quality-check")
async def trigger_quality_check(data: Dict[str, Any], request: Request):
    """Trigger quality check - compatibility endpoint"""
    workspace_id = data.get("workspace_id")
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id required")
    
    # Trigger quality validation
    try:
        result = await validate_workspace_goals(UUID(workspace_id), use_database_goals=True)
        return {
            "success": True,
            "workspace_id": workspace_id,
            "quality_check_triggered": True,
            "validation_result": result
        }
    except Exception as e:
        logger.error(f"Quality check failed: {e}")
        return {
            "success": False,
            "workspace_id": workspace_id,
            "quality_check_triggered": False,
            "error": str(e)
        }

@router.get("/{workspace_id}/validate", response_model=Dict[str, Any])
async def validate_workspace_goals(
    workspace_id: UUID, 
    use_database_goals: bool = Query(True, description="Use database goals for validation (includes goal_id)")
):
    """
    AI-driven validation of workspace goal achievement
    Cross-domain scalable validation system
    """
    try:
        # Get workspace details
        workspace = await get_workspace(str(workspace_id))
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        workspace_goal = workspace.get("goal", "")
        if not workspace_goal:
            raise HTTPException(status_code=400, detail="Workspace has no defined goal")
        
        # Get completed tasks
        all_tasks = await list_tasks(str(workspace_id))
        completed_tasks = [t for t in all_tasks if t.get("status") == "completed"]
        
        if not completed_tasks:
            return {
                "workspace_id": str(workspace_id),
                "workspace_goal": workspace_goal,
                "validation_status": "no_completed_tasks",
                "validations": [],
                "overall_achievement": 0.0,
                "recommendations": ["Complete tasks to enable goal validation"],
                "validation_timestamp": datetime.now().isoformat()
            }
        
        # Perform AI-driven goal validation - ALWAYS prioritize database goals
        database_goals = await _get_workspace_database_goals(str(workspace_id))
        
        if database_goals:
            logger.info(f"🎯 Using database goals validation for {len(database_goals)} goals")
            validations = await goal_validator.validate_database_goals_achievement(
                database_goals, completed_tasks, str(workspace_id)
            )
        elif use_database_goals:
            # Try to create database goals from workspace text if they don't exist
            logger.info("🔄 No database goals found, attempting to create from workspace text")
            try:
                from database import auto_create_workspace_goals
                created_goals = await auto_create_workspace_goals(str(workspace_id), workspace_goal)
                if created_goals:
                    logger.info(f"✅ Created {len(created_goals)} database goals, re-running validation")
                    validations = await goal_validator.validate_database_goals_achievement(
                        created_goals, completed_tasks, str(workspace_id)
                    )
                else:
                    # Final fallback to workspace text
                    logger.warning("⚠️ Falling back to workspace text validation")
                    validations = await goal_validator.validate_workspace_goal_achievement(
                        workspace_goal, completed_tasks, str(workspace_id)
                    )
            except Exception as e:
                logger.error(f"Failed to create database goals: {e}")
                validations = await goal_validator.validate_workspace_goal_achievement(
                    workspace_goal, completed_tasks, str(workspace_id)
                )
        else:
            # Use original method with workspace goal text (deprecated path)
            logger.warning("⚠️ Using deprecated workspace text validation - consider upgrading to database goals")
            validations = await goal_validator.validate_workspace_goal_achievement(
                workspace_goal, completed_tasks, str(workspace_id)
            )
        
        # Calculate overall metrics
        overall_achievement = _calculate_overall_achievement(validations)
        critical_issues = [v for v in validations if v.severity == ValidationSeverity.CRITICAL]
        high_issues = [v for v in validations if v.severity == ValidationSeverity.HIGH]
        
        # Generate summary recommendations
        summary_recommendations = []
        for validation in validations:
            if validation.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.HIGH]:
                summary_recommendations.extend(validation.recommendations[:2])  # Top 2 per validation
        
        # Determine validation status
        if len(critical_issues) > 0:
            validation_status = "critical_issues"
        elif len(high_issues) > 0:
            validation_status = "high_priority_issues"
        elif overall_achievement >= 0.9:
            validation_status = "goals_achieved"
        elif overall_achievement >= 0.7:
            validation_status = "mostly_achieved"
        else:
            validation_status = "significant_gaps"
        
        return {
            "workspace_id": str(workspace_id),
            "workspace_goal": workspace_goal,
            "validation_status": validation_status,
            "overall_achievement": round(overall_achievement * 100, 1),  # As percentage
            "total_validations": len(validations),
            "critical_issues": len(critical_issues),
            "high_priority_issues": len(high_issues),
            # Frontend expects 'validation_results' not 'validations'
            "validation_results": [
                {
                    # Frontend field name mappings
                    "target_requirement": v.target_requirement,
                    "actual_achievement": v.actual_achievement,
                    "achievement_percentage": round(100 - v.gap_percentage, 1),  # Calculate achievement percentage
                    "gap_percentage": round(v.gap_percentage, 1),
                    "severity": v.severity.value,
                    "is_valid": v.is_valid,
                    "confidence": round(v.confidence, 2),
                    "message": v.validation_message,
                    "recommendations": v.recommendations[:3],  # Top 3 recommendations
                    "validation_details": v.extracted_metrics,  # Frontend expects this field
                    "extracted_metrics": v.extracted_metrics
                }
                for v in validations
            ],
            # Keep original field for backward compatibility
            "validations": [
                {
                    "requirement": v.target_requirement,
                    "achievement": v.actual_achievement,
                    "gap_percentage": round(v.gap_percentage, 1),
                    "severity": v.severity.value,
                    "is_valid": v.is_valid,
                    "confidence": round(v.confidence, 2),
                    "message": v.validation_message,
                    "recommendations": v.recommendations[:3],  # Top 3 recommendations
                    "extracted_metrics": v.extracted_metrics
                }
                for v in validations
            ],
            "summary_recommendations": list(set(summary_recommendations))[:5],  # Deduplicate and limit
            "completed_tasks_analyzed": len(completed_tasks),
            "validation_timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating workspace goals: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Goal validation failed: {str(e)}"
        )

@router.get("/{workspace_id}/quality-gate/{target_phase}", response_model=Dict[str, Any])
async def evaluate_quality_gate(request: Request, workspace_id: UUID, target_phase: str, current_phase: Optional[str] = None):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route evaluate_quality_gate called", endpoint="evaluate_quality_gate", trace_id=trace_id)

    """
    Evaluate quality gate for phase transition
    AI-driven gate evaluation with blocking capability
    """
    try:
        # Get workspace details
        workspace = await get_workspace(str(workspace_id))
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        workspace_goal = workspace.get("goal", "")
        
        # Get tasks
        all_tasks = await list_tasks(str(workspace_id))
        completed_tasks = [t for t in all_tasks if t.get("status") == "completed"]
        pending_tasks = [t for t in all_tasks if t.get("status") in ["pending", "in_progress"]]
        
        # Determine current phase if not provided
        if not current_phase:
            current_phase = _infer_current_phase(all_tasks)
        
        # Evaluate quality gate
        gate_result = await quality_gates.evaluate_phase_transition_readiness(
            current_phase, target_phase, str(workspace_id), workspace_goal, completed_tasks, pending_tasks
        )
        
        return {
            "workspace_id": str(workspace_id),
            "current_phase": current_phase,
            "target_phase": target_phase,
            "gate_status": gate_result.gate_status.value,
            # Frontend field mappings for quality gate
            "can_transition": gate_result.can_proceed,
            "readiness_score": round(gate_result.gate_confidence * 100, 1),  # Convert to percentage
            "missing_requirements": gate_result.blocking_issues,
            "quality_issues": gate_result.warnings,
            "recommendations": gate_result.recommendations,
            # Keep original fields for backward compatibility
            "can_proceed": gate_result.can_proceed,
            "gate_confidence": round(gate_result.gate_confidence, 2),
            "blocking_issues": gate_result.blocking_issues,
            "warnings": gate_result.warnings,
            "next_actions": gate_result.next_actions,
            "validation_details": [
                {
                    "requirement": v.target_requirement,
                    "achievement": v.actual_achievement,
                    "gap_percentage": round(v.gap_percentage, 1),
                    "severity": v.severity.value,
                    "is_valid": v.is_valid,
                    "message": v.validation_message
                }
                for v in gate_result.validation_results
            ],
            "evaluation_timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error evaluating quality gate: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quality gate evaluation failed: {str(e)}"
        )

@router.post("/{workspace_id}/completion-readiness", response_model=Dict[str, Any])
async def check_project_completion_readiness(workspace_id: UUID, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route check_project_completion_readiness called", endpoint="check_project_completion_readiness", trace_id=trace_id)

    """
    Comprehensive check for project completion readiness
    """
    try:
        # Get workspace details
        workspace = await get_workspace(str(workspace_id))
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        workspace_goal = workspace.get("goal", "")
        all_tasks = await list_tasks(str(workspace_id))
        
        # Check completion readiness
        readiness_result = await quality_gates.check_project_completion_readiness(
            str(workspace_id), workspace_goal, all_tasks
        )
        
        # Calculate additional metrics
        total_tasks = len(all_tasks)
        completed_tasks = len([t for t in all_tasks if t.get("status") == "completed"])
        pending_tasks = len([t for t in all_tasks if t.get("status") in ["pending", "in_progress"]])
        failed_tasks = len([t for t in all_tasks if t.get("status") == "failed"])
        
        completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            "workspace_id": str(workspace_id),
            "workspace_goal": workspace_goal,
            # Frontend field mappings for completion readiness
            "ready_for_completion": readiness_result.can_proceed,
            "completion_score": round(readiness_result.gate_confidence * 100, 1),  # Convert to percentage
            "missing_deliverables": readiness_result.blocking_issues,
            "quality_concerns": readiness_result.warnings,
            "final_recommendations": readiness_result.recommendations,
            # Keep original structure for backward compatibility
            "completion_readiness": {
                "status": readiness_result.gate_status.value,
                "can_complete": readiness_result.can_proceed,
                "confidence": round(readiness_result.gate_confidence, 2),
                "blocking_issues": readiness_result.blocking_issues,
                "warnings": readiness_result.warnings,
                "recommendations": readiness_result.recommendations
            },
            "project_metrics": {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "pending_tasks": pending_tasks,
                "failed_tasks": failed_tasks,
                "completion_percentage": round(completion_percentage, 1)
            },
            "goal_validation": [
                {
                    "requirement": v.target_requirement,
                    "achievement": v.actual_achievement,
                    "gap_percentage": round(v.gap_percentage, 1),
                    "severity": v.severity.value,
                    "is_valid": v.is_valid
                }
                for v in readiness_result.validation_results
            ],
            "next_actions": readiness_result.next_actions,
            "evaluation_timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking completion readiness: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Completion readiness check failed: {str(e)}"
        )

@router.post("/{workspace_id}/validate-task/{task_id}", response_model=Dict[str, Any])
async def validate_task_against_goals(workspace_id: UUID, task_id: UUID, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route validate_task_against_goals called", endpoint="validate_task_against_goals", trace_id=trace_id)

    """
    Validate a specific task's contribution to workspace goals
    """
    try:
        # Get workspace and task details
        workspace = await get_workspace(str(workspace_id))
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        workspace_goal = workspace.get("goal", "")
        all_tasks = await list_tasks(str(workspace_id))
        
        # Find the specific task
        target_task = None
        for task in all_tasks:
            if str(task.get("id")) == str(task_id):
                target_task = task
                break
        
        if not target_task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Validate task contribution
        is_adequate, issues = await quality_gates.validate_task_completion_against_goals(
            target_task, workspace_goal, all_tasks
        )
        
        # Get single-task validation
        task_validations = await goal_validator.validate_workspace_goal_achievement(
            workspace_goal, [target_task], str(workspace_id)
        )
        
        return {
            "workspace_id": str(workspace_id),
            "task_id": str(task_id),
            "task_name": target_task.get("name", ""),
            "task_status": target_task.get("status", ""),
            "is_adequate": is_adequate,
            "adequacy_issues": issues,
            "goal_validations": [
                {
                    "requirement": v.target_requirement,
                    "achievement": v.actual_achievement,
                    "gap_percentage": round(v.gap_percentage, 1),
                    "severity": v.severity.value,
                    "is_valid": v.is_valid,
                    "message": v.validation_message,
                    "recommendations": v.recommendations[:3]
                }
                for v in task_validations
            ],
            "validation_timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating task: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Task validation failed: {str(e)}"
        )

def _calculate_overall_achievement(validations: List) -> float:
    """Calculate overall achievement percentage"""
    if not validations:
        return 1.0
    
    achievement_scores = [1.0 - (v.gap_percentage / 100) for v in validations]
    return sum(achievement_scores) / len(achievement_scores)

async def _get_workspace_database_goals(workspace_id: str) -> List[Dict]:
    """Get database goals for validation (includes goal_id)"""
    try:
        from database import supabase
        from models import GoalStatus
        
        response = supabase.table("workspace_goals").select("*").eq(
            "workspace_id", workspace_id
        ).in_(
            "status", [GoalStatus.ACTIVE.value, GoalStatus.COMPLETED.value]
        ).execute()
        
        goals = response.data or []
        logger.info(f"📋 Found {len(goals)} active database goals for workspace {workspace_id}")
        return goals
        
    except Exception as e:
        logger.error(f"Error getting database goals: {e}")
        return []

def _infer_current_phase(tasks: List[Dict]) -> str:
    """Infer current phase from task patterns"""
    completed_tasks = [t for t in tasks if t.get("status") == "completed"]
    total_tasks = len(tasks)
    
    if not completed_tasks:
        return "analysis"
    
    completion_rate = len(completed_tasks) / total_tasks if total_tasks > 0 else 0
    
    # Simple phase inference based on completion rate and task names
    recent_task_names = [t.get("name", "").lower() for t in tasks[-5:]]
    
    if any("finalization" in name or "completion" in name for name in recent_task_names):
        return "finalization"
    elif any("implementation" in name or "develop" in name for name in recent_task_names):
        return "implementation"
    elif completion_rate > 0.8:
        return "finalization"
    elif completion_rate > 0.4:
        return "implementation"
    else:
        return "analysis"