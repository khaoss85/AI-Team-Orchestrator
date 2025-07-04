"""
Real-time Progress Validation System

Validates that the Goal-Task-Deliverable pipeline works correctly in real-time.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from database import supabase, get_task
from models import TaskStatus

logger = logging.getLogger(__name__)

class ProgressValidationEngine:
    """
    🎯 PRIORITY 2: Real-time validation engine for goal progress updates
    
    Ensures that task completion actually triggers goal progress updates
    and that deliverables are created when appropriate.
    """
    
    def __init__(self):
        self.validation_history = {}
        self.failed_validations = []
        
    async def validate_task_completion_flow(
        self, 
        task_id: str, 
        expected_goal_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate that task completion triggers the complete flow:
        Task Completion → Goal Progress → Deliverable Check
        """
        validation_start = datetime.now()
        validation_result = {
            "task_id": task_id,
            "timestamp": validation_start.isoformat(),
            "steps_validated": [],
            "failures": [],
            "overall_success": False
        }
        
        try:
            # Step 1: Verify task exists and is completed
            task_data = await get_task(task_id)
            if not task_data:
                validation_result["failures"].append("Task not found in database")
                return validation_result
            
            if task_data.get("status") != TaskStatus.COMPLETED.value:
                validation_result["failures"].append(f"Task status is {task_data.get('status')}, not completed")
                return validation_result
            
            validation_result["steps_validated"].append("task_completion_verified")
            
            # Step 2: Verify goal association
            goal_id = task_data.get("goal_id") or expected_goal_id
            if not goal_id:
                validation_result["failures"].append("Task has no goal_id association")
                return validation_result
            
            validation_result["steps_validated"].append("goal_association_verified")
            validation_result["goal_id"] = goal_id
            
            # Step 3: Check if goal progress was updated recently
            workspace_id = task_data.get("workspace_id")
            goal_progress_updated = await self._check_goal_progress_update(
                goal_id, validation_start - timedelta(minutes=5)
            )
            
            if goal_progress_updated:
                validation_result["steps_validated"].append("goal_progress_updated")
            else:
                validation_result["failures"].append("Goal progress not updated after task completion")
            
            # Step 4: Check achievement extraction
            achievements_extracted = await self._check_achievement_extraction(task_id)
            if achievements_extracted:
                validation_result["steps_validated"].append("achievements_extracted")
            else:
                validation_result["failures"].append("No achievements extracted from task")
            
            # Step 5: Check deliverable creation trigger (if goal progress high enough)
            current_goal = await self._get_goal_status(goal_id)
            if current_goal:
                progress_percent = (current_goal.get("current_value", 0) / 
                                  max(current_goal.get("target_value", 1), 1)) * 100
                validation_result["goal_progress_percent"] = progress_percent
                
                if progress_percent >= 70:  # Immediate deliverable threshold
                    deliverable_triggered = await self._check_deliverable_creation_trigger(
                        workspace_id, validation_start - timedelta(minutes=5)
                    )
                    if deliverable_triggered:
                        validation_result["steps_validated"].append("deliverable_creation_triggered")
                    else:
                        validation_result["failures"].append("Deliverable creation not triggered despite high goal progress")
            
            # Overall success assessment
            validation_result["overall_success"] = (
                len(validation_result["failures"]) == 0 and
                len(validation_result["steps_validated"]) >= 3
            )
            
            # Store validation history
            self.validation_history[task_id] = validation_result
            
            if not validation_result["overall_success"]:
                self.failed_validations.append(validation_result)
                logger.warning(f"❌ Progress validation FAILED for task {task_id}: {validation_result['failures']}")
            else:
                logger.info(f"✅ Progress validation SUCCESS for task {task_id}: {len(validation_result['steps_validated'])} steps")
            
            return validation_result
            
        except Exception as e:
            validation_result["failures"].append(f"Validation exception: {str(e)}")
            logger.error(f"Error in progress validation for task {task_id}: {e}")
            return validation_result
    
    async def _check_goal_progress_update(self, goal_id: str, since: datetime) -> bool:
        """Check if goal was updated recently"""
        try:
            response = supabase.table("workspace_goals").select("updated_at").eq(
                "id", goal_id
            ).gte("updated_at", since.isoformat()).execute()
            
            return len(response.data or []) > 0
        except Exception as e:
            logger.error(f"Error checking goal progress update: {e}")
            return False
    
    async def _check_achievement_extraction(self, task_id: str) -> bool:
        """Check if achievements were extracted from task (via logs or database)"""
        try:
            # Check workspace_insights for achievement records
            task_data = await get_task(task_id)
            if not task_data:
                return False
            
            workspace_id = task_data.get("workspace_id")
            since = datetime.now() - timedelta(minutes=5)
            
            response = supabase.table("workspace_insights").select("*").eq(
                "workspace_id", workspace_id
            ).eq("insight_type", "achievement").gte(
                "created_at", since.isoformat()
            ).execute()
            
            return len(response.data or []) > 0
        except Exception as e:
            logger.error(f"Error checking achievement extraction: {e}")
            return False
    
    async def _get_goal_status(self, goal_id: str) -> Optional[Dict[str, Any]]:
        """Get current goal status"""
        try:
            response = supabase.table("workspace_goals").select("*").eq("id", goal_id).single().execute()
            return response.data
        except Exception as e:
            logger.error(f"Error getting goal status: {e}")
            return None
    
    async def _check_deliverable_creation_trigger(self, workspace_id: str, since: datetime) -> bool:
        """Check if deliverable creation was triggered recently"""
        try:
            # Check for deliverable creation logs or database records
            response = supabase.table("workspace_insights").select("*").eq(
                "workspace_id", workspace_id
            ).like("content", "%deliverable%").gte(
                "created_at", since.isoformat()
            ).execute()
            
            return len(response.data or []) > 0
        except Exception as e:
            logger.error(f"Error checking deliverable creation trigger: {e}")
            return False
    
    async def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of all validations performed"""
        total_validations = len(self.validation_history)
        failed_validations = len(self.failed_validations)
        success_rate = ((total_validations - failed_validations) / max(total_validations, 1)) * 100
        
        return {
            "total_validations": total_validations,
            "successful_validations": total_validations - failed_validations,
            "failed_validations": failed_validations,
            "success_rate_percent": success_rate,
            "recent_failures": self.failed_validations[-5:] if self.failed_validations else []
        }

# Singleton instance
progress_validation_engine = ProgressValidationEngine()