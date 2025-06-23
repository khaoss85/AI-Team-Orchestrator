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
            
            # 🚨 HEALTH CHECK: Filter out orphaned/incomplete workspaces
            healthy_workspace_ids = []
            for workspace_id in workspace_ids:
                # First check if workspace still exists (prevent orphaned goals issue)
                workspace_exists = await self._verify_workspace_exists(workspace_id)
                if not workspace_exists:
                    logger.warning(f"🗑️ Orphaned goals detected - workspace {workspace_id} doesn't exist, cleaning up goals")
                    await self._cleanup_orphaned_goals(workspace_id)
                    continue
                    
                is_healthy = await self._check_workspace_health(workspace_id)
                if is_healthy:
                    healthy_workspace_ids.append(workspace_id)
                else:
                    logger.warning(f"🚨 Skipping unhealthy workspace {workspace_id} from goal monitoring")
            
            logger.info(f"📋 Found {len(healthy_workspace_ids)}/{len(workspace_ids)} healthy workspaces needing validation")
            return healthy_workspace_ids
            
        except Exception as e:
            logger.error(f"Error getting workspaces for validation: {e}")
            return []
    
    async def _verify_workspace_exists(self, workspace_id: str) -> bool:
        """Verify that a workspace still exists in the database"""
        try:
            response = supabase.table("workspaces").select("id").eq("id", workspace_id).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error checking workspace existence for {workspace_id}: {e}")
            return False
    
    async def _cleanup_orphaned_goals(self, workspace_id: str) -> None:
        """Clean up goals for non-existent workspaces"""
        try:
            # Delete orphaned goals
            result = supabase.table("workspace_goals").delete().eq("workspace_id", workspace_id).execute()
            deleted_count = len(result.data) if result.data else 0
            
            logger.warning(f"🗑️ Cleaned up {deleted_count} orphaned goals for deleted workspace {workspace_id}")
            
            # Log cleanup action
            supabase.table("logs").insert({
                "workspace_id": None,  # No workspace reference since it's deleted
                "type": "system",
                "message": f"Cleaned up orphaned goals for deleted workspace {workspace_id}",
                "metadata": {
                    "action": "orphaned_goals_cleanup",
                    "deleted_workspace_id": workspace_id,
                    "goals_deleted": deleted_count,
                    "component": "automated_goal_monitor"
                },
                "created_at": datetime.now().isoformat()
            }).execute()
            
        except Exception as e:
            logger.error(f"Error cleaning up orphaned goals for workspace {workspace_id}: {e}")
    
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
    
    async def _classify_metric_type_ai(self, universal_metric_type: str) -> str:
        """
        🌍 PILLAR 2 & 3 COMPLIANCE: AI-driven metric type classification
        Uses the same resilient multi-layered system as goal_driven_task_planner
        """
        # Delegate to the task planner's robust classification system
        from goal_driven_task_planner import goal_driven_task_planner
        return await goal_driven_task_planner._classify_metric_type_ai(universal_metric_type)
    
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
                
                # ⚠️ NOTE: Auto-provisioning removed - orphaned workspaces should be fixed at the source
                # Healthy workspaces should always have agents. If we reach this point, it's an error.
                if not agent_requirements or not agent_requirements.get("agent_id"):
                    logger.error(f"❌ No agent assignment for corrective task in workspace {workspace_id} - this should not happen after health checks")
                    await self._alert_workspace_issue(
                        workspace_id, 
                        "CORRECTIVE_TASK_NO_AGENT", 
                        "Corrective task creation failed due to missing agent assignment despite health checks"
                    )
                    continue
                
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
                
                # 🌍 PILLAR 2 & 3 COMPLIANCE: AI-driven metric type classification (universal)
                original_metric_type = task_data.get("metric_type")
                compatible_metric_type = await self._classify_metric_type_ai(original_metric_type) if original_metric_type else None
                
                # Prepare task for database insertion - defensive programming
                task_name = task_data.get("name", f"Corrective action for {task_data.get('goal_id', 'unknown goal')}")
                task_description = task_data.get("description", f"Automated corrective action to address goal validation failure")
                
                db_task = {
                    "workspace_id": workspace_id,
                    "name": task_name,
                    "description": task_description,
                    "status": "pending",
                    "priority": "high",  # All corrective tasks are high priority
                    "assigned_to_role": assigned_role,
                    "agent_id": assigned_agent_id,  # Direct assignment if available
                    "estimated_effort_hours": task_data.get("estimated_duration_hours", 2),
                    "deadline": (datetime.now() + timedelta(hours=24)).isoformat(),  # 24hr deadline
                    
                    # Goal-driven fields
                    "goal_id": task_data.get("goal_id"),
                    "metric_type": compatible_metric_type,  # Use mapped value for DB compatibility
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
                        "completion_requirements": task_data.get("completion_requirements"),
                        "original_metric_type": original_metric_type  # Preserve original for future use
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
    
    async def _check_workspace_health(self, workspace_id: str) -> bool:
        """
        🏥 WORKSPACE HEALTH CHECK: Detect orphaned/incomplete workspaces
        
        Returns False for workspaces that shouldn't be processed by goal monitoring
        """
        try:
            # 1. Check workspace status
            workspace_response = supabase.table("workspaces").select("*").eq(
                "id", workspace_id
            ).single().execute()
            
            if not workspace_response.data:
                await self._alert_workspace_issue(workspace_id, "WORKSPACE_NOT_FOUND", "Workspace does not exist in database")
                return False
            
            workspace = workspace_response.data
            workspace_status = workspace.get("status")
            workspace_name = workspace.get("name", "Unknown")
            
            # 2. Check if workspace is in problematic states
            if workspace_status == "created":
                await self._alert_workspace_issue(
                    workspace_id, 
                    "ORPHANED_WORKSPACE", 
                    f"Workspace '{workspace_name}' has goals but is still in 'created' status - likely from incomplete E2E test or failed initialization"
                )
                return False
            
            if workspace_status == "needs_intervention":
                logger.info(f"🔧 Skipping workspace {workspace_id} - marked as needs_intervention")
                return False
            
            # 3. Check if workspace has ANY agents (active or inactive)
            agents_response = supabase.table("agents").select("id, status").eq(
                "workspace_id", workspace_id
            ).execute()
            
            agents = agents_response.data or []
            available_agents = [a for a in agents if a.get("status") == "available"]
            
            if not agents:
                await self._alert_workspace_issue(
                    workspace_id,
                    "NO_AGENTS_AT_ALL",
                    f"Workspace '{workspace_name}' has goals but ZERO agents - this should never happen in a properly initialized workspace"
                )
                return False
            
            if not available_agents:
                await self._alert_workspace_issue(
                    workspace_id,
                    "NO_AVAILABLE_AGENTS", 
                    f"Workspace '{workspace_name}' has {len(agents)} agents but NONE are available - agents may have failed or been terminated"
                )
                return False
            
            # 4. Check for other anomalies
            if len(available_agents) < 2:
                logger.warning(f"⚠️ Workspace {workspace_id} has only {len(available_agents)} available agent(s) - may need attention")
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking workspace health for {workspace_id}: {e}")
            await self._alert_workspace_issue(workspace_id, "HEALTH_CHECK_ERROR", f"Failed to check workspace health: {e}")
            return False
    
    async def _alert_workspace_issue(self, workspace_id: str, issue_type: str, description: str) -> None:
        """
        🚨 ALERT SYSTEM: Log critical workspace issues for monitoring
        """
        try:
            # Log to system logs table for monitoring
            alert_data = {
                "workspace_id": workspace_id,
                "type": "system",
                "message": f"WORKSPACE HEALTH ALERT: {issue_type}",
                "metadata": {
                    "alert_type": "workspace_health",
                    "issue_type": issue_type,
                    "description": description,
                    "severity": "critical" if issue_type in ["NO_AGENTS_AT_ALL", "ORPHANED_WORKSPACE"] else "warning",
                    "requires_intervention": True,
                    "detected_at": datetime.now().isoformat(),
                    "monitoring_component": "automated_goal_monitor"
                },
                "created_at": datetime.now().isoformat()
            }
            
            supabase.table("logs").insert(alert_data).execute()
            
            # Also log to console for immediate visibility
            logger.error(f"🚨 WORKSPACE ALERT [{issue_type}]: {description} (Workspace: {workspace_id})")
            
            # Update workspace status if it's orphaned
            if issue_type == "ORPHANED_WORKSPACE":
                supabase.table("workspaces").update({
                    "status": "needs_intervention",
                    "updated_at": datetime.now().isoformat()
                }).eq("id", workspace_id).execute()
                
                logger.info(f"📝 Updated workspace {workspace_id} status to 'needs_intervention'")
            
        except Exception as e:
            logger.error(f"Failed to create workspace alert: {e}")
    
    async def _auto_provision_workspace_agents(self, workspace_id: str) -> bool:
        """
        🚀 PILLAR 4 & 7 COMPLIANCE: Auto-provision essential agents for workspace with goals but no agents
        
        This ensures scalability and autonomous pipeline operation
        """
        try:
            logger.info(f"🤖 Auto-provisioning agents for workspace {workspace_id} (Pillar 4 & 7 compliance)")
            
            # Get workspace details for context
            workspace_response = supabase.table("workspaces").select("*").eq(
                "id", workspace_id
            ).single().execute()
            
            if not workspace_response.data:
                logger.error(f"❌ Workspace {workspace_id} not found, cannot auto-provision")
                return False
            
            workspace_data = workspace_response.data
            workspace_name = workspace_data.get("name", "Auto-provisioned Workspace")
            workspace_goal = workspace_data.get("goal", "Universal project goals")
            
            # 🎯 Create essential agent team for goal achievement
            essential_agents = [
                {
                    "workspace_id": workspace_id,
                    "name": "Project Manager",
                    "role": "project_manager",
                    "seniority": "senior",
                    "description": f"Senior project manager for {workspace_name} - coordinates task execution and goal achievement",
                    "system_prompt": f"You are a senior project manager for '{workspace_name}'. Your goal is: {workspace_goal}. Focus on concrete deliverables and measurable outcomes. Always prioritize task completion and goal achievement.",
                    "status": "active",
                    "health": {"status": "healthy", "last_update": datetime.now().isoformat()},
                    "personality_traits": ["proactive", "analytical", "decisive"],
                    "communication_style": "concise",
                    "hard_skills": [
                        {"name": "project_management", "level": "expert"},
                        {"name": "goal_achievement", "level": "expert"},
                        {"name": "task_coordination", "level": "expert"}
                    ],
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                },
                {
                    "workspace_id": workspace_id,
                    "name": "Senior Specialist",
                    "role": "senior_specialist",
                    "seniority": "expert",
                    "description": f"Expert specialist for {workspace_name} - executes complex tasks and delivers high-quality results",
                    "system_prompt": f"You are an expert specialist for '{workspace_name}'. Your goal is: {workspace_goal}. You excel at executing complex tasks with precision and delivering concrete, measurable results. Always focus on actionable deliverables.",
                    "status": "active",
                    "health": {"status": "healthy", "last_update": datetime.now().isoformat()},
                    "personality_traits": ["analytical", "detail_oriented", "innovative"],
                    "communication_style": "technical",
                    "hard_skills": [
                        {"name": "problem_solving", "level": "expert"},
                        {"name": "execution", "level": "expert"},
                        {"name": "quality_assurance", "level": "expert"}
                    ],
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            ]
            
            # Insert agents into database
            provisioned_count = 0
            for agent_data in essential_agents:
                try:
                    response = supabase.table("agents").insert(agent_data).execute()
                    if response.data:
                        provisioned_count += 1
                        agent_name = agent_data["name"]
                        agent_role = agent_data["role"]
                        logger.info(f"✅ Auto-provisioned agent: {agent_name} ({agent_role})")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to provision agent {agent_data['name']}: {e}")
            
            if provisioned_count > 0:
                logger.info(f"🎉 Successfully auto-provisioned {provisioned_count} agents for workspace {workspace_id}")
                
                # Log this action for audit trail
                supabase.table("logs").insert({
                    "workspace_id": workspace_id,
                    "type": "system",
                    "message": f"Auto-provisioned {provisioned_count} essential agents (Pillar 4 & 7 compliance)",
                    "metadata": {
                        "action": "auto_provision_agents",
                        "agents_created": provisioned_count,
                        "trigger": "goal_monitoring_no_agents",
                        "workspace_name": workspace_name
                    },
                    "created_at": datetime.now().isoformat()
                }).execute()
                
                return True
            else:
                logger.error(f"❌ Failed to provision any agents for workspace {workspace_id}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Error in auto-provisioning agents for workspace {workspace_id}: {e}")
            return False
    
    async def _select_best_available_agent_after_provisioning(self, workspace_id: str) -> Dict[str, Any]:
        """
        Select best agent after auto-provisioning
        """
        try:
            # Get newly provisioned agents
            response = supabase.table("agents").select("*").eq(
                "workspace_id", workspace_id
            ).eq(
                "status", "active"
            ).order("created_at", desc=True).execute()
            
            available_agents = response.data or []
            
            if not available_agents:
                logger.warning(f"⚠️ No agents found even after auto-provisioning for workspace {workspace_id}")
                return {"role": "auto_provision_failed", "strategy": "fallback"}
            
            # Prefer project manager for corrective tasks
            for agent in available_agents:
                if "manager" in agent.get("role", "").lower():
                    logger.info(f"✅ Selected auto-provisioned manager: {agent.get('name')}")
                    return {
                        "role": agent["role"],
                        "agent_id": agent["id"],
                        "seniority": agent.get("seniority", "senior"),
                        "strategy": "auto_provisioned_manager",
                        "agent_name": agent.get("name")
                    }
            
            # Otherwise use the first available agent
            selected_agent = available_agents[0]
            logger.info(f"✅ Selected auto-provisioned agent: {selected_agent.get('name')}")
            return {
                "role": selected_agent["role"],
                "agent_id": selected_agent["id"],
                "seniority": selected_agent.get("seniority", "senior"),
                "strategy": "auto_provisioned_first_available",
                "agent_name": selected_agent.get("name")
            }
            
        except Exception as e:
            logger.error(f"Error selecting agent after auto-provisioning: {e}")
            return {"role": "auto_provision_error", "strategy": "error_fallback"}
    
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
            # 🛡️ ENHANCED DUPLICATE PREVENTION: Use workspace status as a lock
            workspace_response = supabase.table("workspaces").select("status").eq(
                "id", workspace_id
            ).single().execute()
            
            if not workspace_response.data:
                logger.error(f"❌ Workspace {workspace_id} not found")
                return {"success": False, "reason": "workspace_not_found"}
            
            current_status = workspace_response.data.get("status")
            
            # If workspace is already processing tasks, skip
            if current_status == "processing_tasks":
                logger.info(f"🔄 Workspace {workspace_id} is already processing tasks - skipping duplicate analysis")
                return {
                    "success": True,
                    "workspace_id": workspace_id,
                    "reason": "already_processing",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Set workspace status to processing to prevent concurrent task creation
            supabase.table("workspaces").update({
                "status": "processing_tasks",
                "updated_at": datetime.now().isoformat()
            }).eq("id", workspace_id).execute()
            
            logger.info(f"🔒 Locked workspace {workspace_id} for task generation")
            
            # 🛡️ DUPLICATE PREVENTION: Check if tasks already exist for this workspace
            existing_tasks_response = supabase.table("tasks").select("id").eq(
                "workspace_id", workspace_id
            ).neq(
                "status", "completed"
            ).execute()
            
            existing_tasks = existing_tasks_response.data or []
            if len(existing_tasks) > 0:
                logger.info(f"🔄 Workspace {workspace_id} already has {len(existing_tasks)} active tasks - skipping immediate goal analysis")
                
                # Reset workspace status
                supabase.table("workspaces").update({
                    "status": "active",
                    "updated_at": datetime.now().isoformat()
                }).eq("id", workspace_id).execute()
                
                return {
                    "success": True,
                    "workspace_id": workspace_id,
                    "reason": "tasks_already_exist",
                    "existing_tasks_count": len(existing_tasks),
                    "timestamp": datetime.now().isoformat()
                }
            
            # 1. Get newly created goals from the workspace
            response = supabase.table("workspace_goals").select("*").eq(
                "workspace_id", workspace_id
            ).eq(
                "status", GoalStatus.ACTIVE.value
            ).execute()
            
            workspace_goals = response.data
            if not workspace_goals:
                logger.warning(f"No active goals found for immediate analysis in workspace {workspace_id}")
                
                # Reset workspace status
                supabase.table("workspaces").update({
                    "status": "active",
                    "updated_at": datetime.now().isoformat()
                }).eq("id", workspace_id).execute()
                
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
            
            # 3. Reset workspace status to active after task creation
            supabase.table("workspaces").update({
                "status": "active",
                "updated_at": datetime.now().isoformat()
            }).eq("id", workspace_id).execute()
            
            logger.info(f"🔓 Unlocked workspace {workspace_id} after task generation")
            
            # 4. Log success
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
            
            # Always reset workspace status on error
            try:
                supabase.table("workspaces").update({
                    "status": "active",
                    "updated_at": datetime.now().isoformat()
                }).eq("id", workspace_id).execute()
                logger.info(f"🔓 Reset workspace {workspace_id} status after error")
            except:
                pass
            
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