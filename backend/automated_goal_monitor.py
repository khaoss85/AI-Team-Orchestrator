# backend/automated_goal_monitor.py

import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from models import WorkspaceGoal, GoalStatus
from database import supabase
from ai_quality_assurance.goal_validator import goal_validator
from goal_driven_task_planner import goal_driven_task_planner

logger = logging.getLogger(__name__)

class AutomatedGoalMonitor:
    """
    🎯 STEP 6: Automated Feedback Loop (20-minute intervals)
    
    Monitors workspace goals continuously and triggers:
    1. Goal validation every 20 minutes
    2. Immediate corrective action on critical gaps
    3. Memory-driven course correction
    4. Automatic task generation
    
    This prevents strategic drift and ensures rapid gap closure.
    """
    
    def __init__(self):
        self.monitor_interval_minutes = 20
        self.is_running = False
        self.active_workspaces_cache = {}
        self.last_validation_cache = {}
        
    async def start_monitoring(self):
        """Start the automated monitoring loop"""
        if self.is_running:
            logger.warning("Goal monitor already running")
            return
        
        self.is_running = True
        logger.info(f"🤖 Starting automated goal monitoring (every {self.monitor_interval_minutes} minutes)")
        
        while self.is_running:
            try:
                await self._run_monitoring_cycle()
                
                # Wait for next cycle
                await asyncio.sleep(self.monitor_interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"Error in monitoring cycle: {e}")
                # Continue monitoring even if one cycle fails
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    def stop_monitoring(self):
        """Stop the automated monitoring"""
        self.is_running = False
        logger.info("🛑 Stopped automated goal monitoring")
    
    async def _run_monitoring_cycle(self):
        """Execute one complete monitoring cycle"""
        cycle_start = datetime.now()
        logger.info(f"🔄 Starting goal monitoring cycle at {cycle_start}")
        
        try:
            # 1. Get active workspaces that need validation
            workspaces_to_validate = await self._get_workspaces_needing_validation()
            
            if not workspaces_to_validate:
                logger.info("✅ No workspaces need validation this cycle")
                return
            
            logger.info(f"📊 Validating {len(workspaces_to_validate)} workspaces")
            
            # 2. Process each workspace
            total_corrective_tasks = 0
            for workspace_id in workspaces_to_validate:
                corrective_tasks = await self._process_workspace_validation(workspace_id)
                total_corrective_tasks += len(corrective_tasks)
            
            # 3. Log cycle summary
            cycle_duration = datetime.now() - cycle_start
            logger.info(
                f"✅ Monitoring cycle completed in {cycle_duration.total_seconds():.1f}s. "
                f"Processed {len(workspaces_to_validate)} workspaces, "
                f"generated {total_corrective_tasks} corrective tasks"
            )
            
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")
    
    async def _get_workspaces_needing_validation(self) -> List[str]:
        """Get workspaces with active goals needing validation"""
        try:
            # Query workspace_goals for active goals that need validation
            cutoff_time = datetime.now() - timedelta(minutes=self.monitor_interval_minutes)
            
            response = supabase.table("workspace_goals").select(
                "workspace_id"
            ).eq(
                "status", GoalStatus.ACTIVE.value
            ).or_(
                f"last_validation_at.is.null,last_validation_at.lt.{cutoff_time.isoformat()}"
            ).execute()
            
            # Get unique workspace IDs
            workspace_ids = list(set(row["workspace_id"] for row in response.data))
            
            logger.info(f"📋 Found {len(workspace_ids)} workspaces needing validation")
            return workspace_ids
            
        except Exception as e:
            logger.error(f"Error getting workspaces for validation: {e}")
            return []
    
    async def _process_workspace_validation(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Process goal validation for a single workspace"""
        try:
            logger.info(f"🔍 Validating workspace {workspace_id}")
            
            # 1. Get completed tasks for validation
            completed_tasks = await self._get_completed_tasks(workspace_id)
            
            # 2. Get database goals for validation (includes goal_id)
            workspace_goals = await self._get_workspace_database_goals(workspace_id)
            
            if not workspace_goals:
                logger.warning(f"No database goals found for workspace {workspace_id}")
                return []
            
            # 3. 🎯 RUN DATABASE GOAL VALIDATION (includes goal_id in results)
            validation_results = await goal_validator.validate_database_goals_achievement(
                workspace_goals=workspace_goals,
                completed_tasks=completed_tasks,
                workspace_id=workspace_id
            )
            
            # 4. Update last_validation_at for all goals in workspace
            await self._update_validation_timestamps(workspace_id)
            
            # 5. 🚨 TRIGGER CORRECTIVE ACTIONS if needed
            corrective_tasks = await goal_validator.trigger_corrective_actions(
                validation_results=validation_results,
                workspace_id=workspace_id
            )
            
            # 6. 📋 CREATE CORRECTIVE TASKS in database
            created_tasks = await self._create_corrective_tasks(corrective_tasks, workspace_id)
            
            # 7. Log validation summary
            critical_issues = [v for v in validation_results if v.severity.value in ['critical', 'high']]
            logger.info(
                f"📊 Workspace {workspace_id}: {len(validation_results)} validations, "
                f"{len(critical_issues)} critical issues, {len(created_tasks)} corrective tasks created"
            )
            
            return created_tasks
            
        except Exception as e:
            logger.error(f"Error processing workspace {workspace_id}: {e}")
            return []
    
    async def _get_completed_tasks(self, workspace_id: str) -> List[Dict]:
        """Get completed tasks for workspace validation"""
        try:
            response = supabase.table("tasks").select("*").eq(
                "workspace_id", workspace_id
            ).eq(
                "status", "completed"
            ).order("updated_at", desc=True).limit(50).execute()
            
            return response.data
            
        except Exception as e:
            logger.error(f"Error getting completed tasks: {e}")
            return []
    
    async def _get_workspace_goal_text(self, workspace_id: str) -> str:
        """Get workspace goal text for validation"""
        try:
            response = supabase.table("workspaces").select("goal").eq(
                "id", workspace_id
            ).single().execute()
            
            return response.data.get("goal", "") if response.data else ""
            
        except Exception as e:
            logger.error(f"Error getting workspace goal: {e}")
            return ""
    
    async def _get_workspace_database_goals(self, workspace_id: str) -> List[Dict]:
        """Get database goals for validation (includes goal_id)"""
        try:
            response = supabase.table("workspace_goals").select("*").eq(
                "workspace_id", workspace_id
            ).eq(
                "status", GoalStatus.ACTIVE.value
            ).execute()
            
            goals = response.data or []
            logger.info(f"📋 Found {len(goals)} active database goals for workspace {workspace_id}")
            return goals
            
        except Exception as e:
            logger.error(f"Error getting database goals: {e}")
            return []
    
    async def _update_validation_timestamps(self, workspace_id: str):
        """Update last_validation_at for all active goals in workspace"""
        try:
            supabase.table("workspace_goals").update({
                "last_validation_at": datetime.now().isoformat()
            }).eq(
                "workspace_id", workspace_id
            ).eq(
                "status", GoalStatus.ACTIVE.value
            ).execute()
            
        except Exception as e:
            logger.error(f"Error updating validation timestamps: {e}")
    
    async def _create_corrective_tasks(
        self, 
        corrective_tasks: List[Dict[str, Any]], 
        workspace_id: str
    ) -> List[Dict[str, Any]]:
        """Create corrective tasks in database"""
        created_tasks = []
        
        for task_data in corrective_tasks:
            try:
                agent_requirements = task_data.get("agent_requirements", {})
                
                # Handle intelligent agent assignment
                assigned_agent_id = agent_requirements.get("agent_id")
                raw_role = agent_requirements.get("role", "specialist")
                # Handle enum values safely
                assigned_role = str(raw_role) if hasattr(raw_role, 'value') else raw_role
                selection_strategy = agent_requirements.get("selection_strategy", "fallback")
                
                # Log agent assignment strategy
                if assigned_agent_id:
                    logger.info(f"🎯 Direct agent assignment: {assigned_agent_id} ({assigned_role}) via {selection_strategy}")
                else:
                    logger.info(f"🎭 Role-based assignment: {assigned_role} via {selection_strategy}")
                
                # Prepare task for database insertion
                db_task = {
                    "workspace_id": workspace_id,
                    "name": task_data["name"],
                    "description": task_data["description"],
                    "status": "pending",
                    "priority": "high",  # All corrective tasks are high priority
                    "assigned_to_role": assigned_role,
                    "agent_id": assigned_agent_id,  # Direct assignment if available
                    "estimated_effort_hours": task_data.get("estimated_duration_hours", 2),
                    "deadline": (datetime.now() + timedelta(hours=24)).isoformat(),  # 24hr deadline
                    
                    # Goal-driven fields
                    "goal_id": task_data.get("goal_id"),
                    "metric_type": task_data.get("metric_type"),
                    "contribution_expected": task_data.get("contribution_expected"),
                    "numerical_target": task_data.get("numerical_target"),
                    "is_corrective": task_data.get("is_corrective", True),
                    "success_criteria": task_data.get("success_criteria", []),
                    
                    # Context data
                    "context_data": {
                        "created_by": "automated_goal_monitor",
                        "urgency_reason": task_data.get("urgency_reason"),
                        "memory_context": task_data.get("memory_context"),
                        "agent_requirements": agent_requirements,
                        "agent_selection_strategy": selection_strategy,
                        "completion_requirements": task_data.get("completion_requirements")
                    }
                }
                
                # Insert task
                response = supabase.table("tasks").insert(db_task).execute()
                
                if response.data:
                    created_task = response.data[0]
                    created_tasks.append(created_task)
                    
                    # Enhanced logging with agent assignment details
                    assignment_info = f"agent_id={assigned_agent_id}" if assigned_agent_id else f"role={assigned_role}"
                    logger.warning(
                        f"🚨 CORRECTIVE TASK CREATED: {created_task['name']} "
                        f"(ID: {created_task['id']}) -> {assignment_info} "
                        f"(strategy: {selection_strategy}) for workspace {workspace_id}"
                    )
                
            except Exception as e:
                logger.error(f"Error creating corrective task: {e}")
        
        return created_tasks
    
    async def trigger_immediate_validation(self, workspace_id: str) -> Dict[str, Any]:
        """
        Trigger immediate validation for a workspace (called externally)
        """
        logger.info(f"🚨 IMMEDIATE validation triggered for workspace {workspace_id}")
        
        try:
            corrective_tasks = await self._process_workspace_validation(workspace_id)
            
            return {
                "success": True,
                "workspace_id": workspace_id,
                "corrective_tasks_created": len(corrective_tasks),
                "tasks": corrective_tasks,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in immediate validation: {e}")
            return {
                "success": False,
                "workspace_id": workspace_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _trigger_immediate_goal_analysis(self, workspace_id: str) -> Dict[str, Any]:
        """
        🚀 IMMEDIATE GOAL ANALYSIS & TASK GENERATION
        
        This is called when goals are confirmed to immediately start the team.
        Creates initial tasks based on confirmed goals without waiting for the 20-minute cycle.
        """
        logger.info(f"🎯 IMMEDIATE goal analysis triggered for workspace {workspace_id}")
        
        try:
            # 1. Get newly created goals from the workspace
            response = supabase.table("workspace_goals").select("*").eq(
                "workspace_id", workspace_id
            ).eq(
                "status", GoalStatus.ACTIVE.value
            ).execute()
            
            workspace_goals = response.data
            if not workspace_goals:
                logger.warning(f"No active goals found for immediate analysis in workspace {workspace_id}")
                return {"success": False, "reason": "no_active_goals"}
            
            # 2. Use goal-driven task planner to create initial tasks
            from goal_driven_task_planner import goal_driven_task_planner
            
            initial_tasks = []
            for goal in workspace_goals:
                logger.info(f"🎯 Creating tasks for goal: {goal['metric_type']} (target: {goal['target_value']})")
                
                # Generate tasks for this specific goal
                goal_tasks = await goal_driven_task_planner.plan_tasks_for_goal(
                    workspace_goal=goal,
                    workspace_id=workspace_id
                )
                
                initial_tasks.extend(goal_tasks)
            
            # 3. Log success
            logger.info(f"✅ Immediate analysis complete: {len(initial_tasks)} tasks created for {len(workspace_goals)} goals")
            
            return {
                "success": True,
                "workspace_id": workspace_id,
                "goals_processed": len(workspace_goals),
                "tasks_created": len(initial_tasks),
                "tasks": initial_tasks,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error in immediate goal analysis for workspace {workspace_id}: {e}")
            return {
                "success": False,
                "workspace_id": workspace_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status and statistics"""
        try:
            # Get active workspaces count
            response = supabase.table("workspace_goals").select(
                "workspace_id"
            ).eq(
                "status", GoalStatus.ACTIVE.value
            ).execute()
            
            unique_workspaces = len(set(row["workspace_id"] for row in response.data))
            
            # Get corrective tasks created today
            today = datetime.now().date()
            response = supabase.table("tasks").select("id").eq(
                "is_corrective", True
            ).gte(
                "created_at", today.isoformat()
            ).execute()
            
            corrective_tasks_today = len(response.data)
            
            return {
                "is_running": self.is_running,
                "monitor_interval_minutes": self.monitor_interval_minutes,
                "active_workspaces": unique_workspaces,
                "corrective_tasks_today": corrective_tasks_today,
                "last_cycle": self.last_validation_cache.get("last_cycle"),
                "next_cycle_in_minutes": self.monitor_interval_minutes if self.is_running else None
            }
            
        except Exception as e:
            logger.error(f"Error getting monitoring status: {e}")
            return {
                "is_running": self.is_running,
                "error": str(e)
            }

# Singleton instance
automated_goal_monitor = AutomatedGoalMonitor()

# Optional: Auto-start monitoring when module is imported
# Uncomment the line below to enable automatic monitoring
# asyncio.create_task(automated_goal_monitor.start_monitoring())