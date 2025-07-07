"""
Real-time Goal Achievement Monitoring System

Monitors goal progress in real-time and triggers corrective actions
when goals are not progressing as expected.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from database import supabase
from models import GoalStatus

logger = logging.getLogger(__name__)

class GoalAchievementMonitor:
    """
    🎯 PRIORITY 3.2: Real-time goal achievement validation
    
    Monitors goals to ensure they are progressing toward completion
    and triggers corrective actions when progress stalls.
    """
    
    def __init__(self):
        self.monitoring_active = False
        self.stalled_goals = {}
        self.achievement_history = {}
        
    async def validate_goal_achievement_post_completion(
        self, 
        workspace_id: str, 
        goal_id: str, 
        task_id: str
    ) -> Dict[str, Any]:
        """
        Validate that goal achievement is progressing after task completion
        """
        validation_start = datetime.now()
        validation_result = {
            "workspace_id": workspace_id,
            "goal_id": goal_id,
            "task_id": task_id,
            "timestamp": validation_start.isoformat(),
            "validations": [],
            "issues_found": [],
            "corrective_actions": [],
            "overall_status": "unknown"
        }
        
        try:
            # Get current goal status
            goal_data = await self._get_goal_data(goal_id)
            if not goal_data:
                validation_result["issues_found"].append("Goal not found in database")
                validation_result["overall_status"] = "error"
                return validation_result
            
            current_value = goal_data.get("current_value", 0)
            target_value = goal_data.get("target_value", 1)
            progress_percent = (current_value / max(target_value, 1)) * 100
            
            validation_result["current_progress"] = {
                "current_value": current_value,
                "target_value": target_value,
                "progress_percent": progress_percent
            }
            
            # Validation 1: Check if progress was actually updated
            progress_updated = await self._check_recent_progress_update(goal_id)
            if progress_updated:
                validation_result["validations"].append("progress_updated_recently")
            else:
                validation_result["issues_found"].append("Goal progress not updated despite task completion")
            
            # Validation 2: Check if progress is meaningful (not just token updates)
            meaningful_progress = await self._check_meaningful_progress(goal_id)
            if meaningful_progress:
                validation_result["validations"].append("meaningful_progress_detected")
            else:
                validation_result["issues_found"].append("Progress updates are too small or insignificant")
            
            # Validation 3: Check goal trajectory (is it trending toward completion?)
            positive_trajectory = await self._check_goal_trajectory(goal_id)
            if positive_trajectory:
                validation_result["validations"].append("positive_trajectory")
            else:
                validation_result["issues_found"].append("Goal progress trajectory is stagnant or declining")
            
            # Validation 4: Check for goal completion readiness
            completion_readiness = await self._assess_completion_readiness(goal_data, workspace_id)
            validation_result["completion_readiness"] = completion_readiness
            
            if completion_readiness["ready_for_completion"]:
                validation_result["validations"].append("ready_for_completion")
                validation_result["corrective_actions"].append("trigger_immediate_completion")
            elif completion_readiness["needs_intervention"]:
                validation_result["issues_found"].append("Goal requires intervention to reach completion")
                validation_result["corrective_actions"].append("create_completion_strategy")
            
            # Determine overall status
            if len(validation_result["issues_found"]) == 0:
                validation_result["overall_status"] = "healthy"
            elif len(validation_result["validations"]) >= 2:
                validation_result["overall_status"] = "warning"
            else:
                validation_result["overall_status"] = "critical"
            
            # Execute corrective actions if needed
            if validation_result["corrective_actions"]:
                await self._execute_corrective_actions(
                    workspace_id, goal_id, validation_result["corrective_actions"]
                )
            
            logger.info(f"🎯 Goal achievement validation for {goal_id}: {validation_result['overall_status']} "
                       f"({len(validation_result['validations'])} validations, {len(validation_result['issues_found'])} issues)")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error in goal achievement validation: {e}")
            validation_result["overall_status"] = "error"
            validation_result["issues_found"].append(f"Validation error: {str(e)}")
            return validation_result
    
    async def _get_goal_data(self, goal_id: str) -> Optional[Dict[str, Any]]:
        """Get current goal data from database"""
        try:
            response = supabase.table("workspace_goals").select("*").eq("id", goal_id).single().execute()
            return response.data
        except Exception as e:
            logger.error(f"Error getting goal data: {e}")
            return None
    
    async def _check_recent_progress_update(self, goal_id: str, minutes: int = 10) -> bool:
        """Check if goal progress was updated recently"""
        try:
            since = datetime.now() - timedelta(minutes=minutes)
            response = supabase.table("workspace_goals").select("updated_at").eq(
                "id", goal_id
            ).gte("updated_at", since.isoformat()).execute()
            
            return len(response.data or []) > 0
        except Exception as e:
            logger.error(f"Error checking recent progress update: {e}")
            return False
    
    async def _check_meaningful_progress(self, goal_id: str, threshold: float = 0.05) -> bool:
        """Check if recent progress updates are meaningful (not just token changes)"""
        try:
            # Get goal history from the last hour
            since = datetime.now() - timedelta(hours=1)
            response = supabase.table("workspace_goals").select("current_value, updated_at").eq(
                "id", goal_id
            ).gte("updated_at", since.isoformat()).order("updated_at", desc=True).limit(5).execute()
            
            if not response.data or len(response.data) < 2:
                return False
            
            # Calculate progress change
            recent_value = response.data[0]["current_value"]
            older_value = response.data[-1]["current_value"]
            progress_change = abs(recent_value - older_value)
            
            return progress_change >= threshold
        except Exception as e:
            logger.error(f"Error checking meaningful progress: {e}")
            return False
    
    async def _check_goal_trajectory(self, goal_id: str) -> bool:
        """Check if goal is on a positive trajectory toward completion"""
        try:
            # Get goal progress over the last 24 hours
            since = datetime.now() - timedelta(hours=24)
            response = supabase.table("workspace_goals").select("current_value, updated_at").eq(
                "id", goal_id
            ).gte("updated_at", since.isoformat()).order("updated_at", desc=False).execute()
            
            if not response.data or len(response.data) < 3:
                return True  # Insufficient data, assume positive
            
            # Calculate trend
            values = [float(row["current_value"]) for row in response.data]
            trend = sum(values[i+1] - values[i] for i in range(len(values)-1))
            
            return trend > 0  # Positive trend
        except Exception as e:
            logger.error(f"Error checking goal trajectory: {e}")
            return True  # Assume positive on error
    
    async def _assess_completion_readiness(
        self, 
        goal_data: Dict[str, Any], 
        workspace_id: str
    ) -> Dict[str, Any]:
        """Assess if goal is ready for completion or needs intervention"""
        try:
            current_value = goal_data.get("current_value", 0)
            target_value = goal_data.get("target_value", 1)
            progress_percent = (current_value / max(target_value, 1)) * 100
            
            # Get completed tasks for this goal
            from database import list_tasks
            tasks = await list_tasks(workspace_id, status="completed")
            goal_tasks = [t for t in tasks if t.get("goal_id") == goal_data["id"]]
            
            readiness_assessment = {
                "progress_percent": progress_percent,
                "completed_tasks": len(goal_tasks),
                "ready_for_completion": False,
                "needs_intervention": False,
                "recommendations": []
            }
            
            # Completion criteria
            if progress_percent >= 90:
                readiness_assessment["ready_for_completion"] = True
                readiness_assessment["recommendations"].append("Trigger immediate goal completion")
            elif progress_percent >= 70 and len(goal_tasks) >= 3:
                readiness_assessment["ready_for_completion"] = True
                readiness_assessment["recommendations"].append("Goal has sufficient progress and tasks - ready for completion")
            elif progress_percent < 30 and len(goal_tasks) >= 2:
                readiness_assessment["needs_intervention"] = True
                readiness_assessment["recommendations"].append("Low progress despite completed tasks - review task quality")
            elif len(goal_tasks) == 0:
                readiness_assessment["needs_intervention"] = True
                readiness_assessment["recommendations"].append("No completed tasks for this goal - generate new tasks")
            
            return readiness_assessment
            
        except Exception as e:
            logger.error(f"Error assessing completion readiness: {e}")
            return {"error": str(e), "ready_for_completion": False, "needs_intervention": False}
    
    async def _execute_corrective_actions(
        self, 
        workspace_id: str, 
        goal_id: str, 
        actions: List[str]
    ):
        """Execute corrective actions for underperforming goals"""
        try:
            for action in actions:
                if action == "trigger_immediate_completion":
                    await self._trigger_goal_completion(workspace_id, goal_id)
                elif action == "create_completion_strategy":
                    await self._create_completion_strategy_task(workspace_id, goal_id)
                
                logger.info(f"✅ Executed corrective action '{action}' for goal {goal_id}")
                
        except Exception as e:
            logger.error(f"Error executing corrective actions: {e}")
    
    async def _trigger_goal_completion(self, workspace_id: str, goal_id: str):
        """Trigger immediate goal completion"""
        try:
            # Update goal status to completed
            supabase.table("workspace_goals").update({
                "status": GoalStatus.COMPLETED.value,
                "completed_at": datetime.now().isoformat(),
                "current_value": supabase.table("workspace_goals").select("target_value").eq("id", goal_id).single().execute().data["target_value"]
            }).eq("id", goal_id).execute()
            
            # Trigger deliverable creation
            from deliverable_system.unified_deliverable_engine import IntelligentDeliverableAggregator
            aggregator = IntelligentDeliverableAggregator()
            await aggregator.check_and_create_final_deliverable(workspace_id)
            
            logger.info(f"🏆 Goal {goal_id} marked as completed and deliverable creation triggered")
            
        except Exception as e:
            logger.error(f"Error triggering goal completion: {e}")
    
    async def _create_completion_strategy_task(self, workspace_id: str, goal_id: str):
        """Create a strategic task to help complete the goal"""
        try:
            from database import create_task
            
            # Get goal details
            goal_data = await self._get_goal_data(goal_id)
            if not goal_data:
                return
            
            strategy_task = {
                "workspace_id": workspace_id,
                "goal_id": goal_id,
                "name": f"Complete Goal: {goal_data.get('description', 'Unknown Goal')}",
                "description": f"Strategic task to complete goal {goal_data.get('description')} (current progress: {goal_data.get('current_value', 0)}/{goal_data.get('target_value', 1)})",
                "priority": "high",
                "status": "pending",
                "context_data": {
                    "is_completion_strategy": True,
                    "generated_by": "goal_achievement_monitor",
                    "goal_progress": goal_data.get("current_value", 0),
                    "goal_target": goal_data.get("target_value", 1)
                }
            }
            
            task_id = await create_task(strategy_task)
            logger.info(f"📋 Created completion strategy task {task_id} for goal {goal_id}")
            
        except Exception as e:
            logger.error(f"Error creating completion strategy task: {e}")

# Singleton instance
goal_achievement_monitor = GoalAchievementMonitor()