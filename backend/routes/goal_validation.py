# backend/routes/goal_validation.py

from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging
from datetime import datetime

from ai_quality_assurance.goal_validator import goal_validator, ValidationSeverity
from ai_quality_assurance.quality_gates import quality_gates, GateStatus
from database import get_workspace, list_tasks
from models import TaskStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/goal-validation", tags=["goal-validation"])

@router.get("/{workspace_id}/validate", response_model=Dict[str, Any])
async def validate_workspace_goals(workspace_id: UUID):
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
        
        # Perform AI-driven goal validation
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
async def evaluate_quality_gate(workspace_id: UUID, target_phase: str, current_phase: Optional[str] = None):
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
            "can_proceed": gate_result.can_proceed,
            "gate_confidence": round(gate_result.gate_confidence, 2),
            "blocking_issues": gate_result.blocking_issues,
            "warnings": gate_result.warnings,
            "recommendations": gate_result.recommendations,
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
async def check_project_completion_readiness(workspace_id: UUID):
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
async def validate_task_against_goals(workspace_id: UUID, task_id: UUID):
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