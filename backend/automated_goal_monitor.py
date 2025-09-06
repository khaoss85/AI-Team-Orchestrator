# backend/automated_goal_monitor.py

import asyncio
import logging
import time
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID

from models import WorkspaceGoal, GoalStatus
from database import supabase
from ai_quality_assurance.unified_quality_engine import goal_validator
from goal_driven_task_planner import goal_driven_task_planner

logger = logging.getLogger(__name__)

# Import asset system for automatic asset requirements generation
asset_requirements_generator = None
try:
    from deliverable_system.unified_deliverable_engine import unified_deliverable_engine as AssetRequirementsGenerator
    asset_requirements_generator = AssetRequirementsGenerator
    logger.info("✅ Asset Requirements Generator initialized for goal monitoring")
except Exception as e:
    logger.error(f"Failed to initialize Asset Requirements Generator in monitoring: {e}")

# 👥 Import Agent Status Manager for unified agent management
try:
    from services.agent_status_manager import agent_status_manager
    AGENT_STATUS_MANAGER_AVAILABLE = True
    logger.info("✅ AgentStatusManager available for goal monitoring")
except ImportError as e:
    logger.warning(f"⚠️ AgentStatusManager not available in goal monitoring: {e}")
    AGENT_STATUS_MANAGER_AVAILABLE = False
    agent_status_manager = None

# 🎯 Import Goal Validation Optimizer for intelligent validation
try:
    from services.goal_validation_optimizer import goal_validation_optimizer
    GOAL_VALIDATION_OPTIMIZER_AVAILABLE = True
    logger.info("✅ GoalValidationOptimizer available for intelligent validation")
except ImportError as e:
    logger.warning(f"⚠️ GoalValidationOptimizer not available in goal monitoring: {e}")
    GOAL_VALIDATION_OPTIMIZER_AVAILABLE = False
    goal_validation_optimizer = None

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
        # Read from environment or use default
        self.monitor_interval_minutes = int(os.getenv("GOAL_VALIDATION_INTERVAL_MINUTES", "20"))
        self.is_running = False
        
        # 🔧 FIX: Add cache size limits to prevent memory bloat
        self.max_cache_entries = int(os.getenv("GOAL_MONITOR_CACHE_MAX_ENTRIES", "100"))
        self.cache_ttl_seconds = int(os.getenv("GOAL_MONITOR_CACHE_TTL_SECONDS", "1800"))  # 30 minutes
        
        self.active_workspaces_cache = {}
        self.last_validation_cache = {}
        
        # Track background tasks to prevent leaks
        self._background_tasks: set = set()
        
        # 🚨 CRITICAL FIX: Add global corrective task cooldown to prevent infinite loops
        self.global_corrective_cooldown = {}  # workspace_id + goal_type -> last_created_time
        self.corrective_cooldown_seconds = int(os.getenv("CORRECTIVE_TASK_COOLDOWN_SECONDS", "300"))  # 5 minutes
        
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
    
    async def stop_monitoring(self):
        """Stop the automated monitoring"""
        self.is_running = False
        
        # 🔧 FIX: Cancel all background tasks to prevent memory leaks
        await self._cleanup_background_tasks()
        
        # Clear caches to free memory
        self.active_workspaces_cache.clear()
        self.last_validation_cache.clear()
        
        logger.info("🛑 Stopped automated goal monitoring and cleaned up resources")
    
    async def trigger_immediate_validation(self, workspace_id: str, reason: str = "external_trigger"):
        """
        🚨 IMMEDIATE VALIDATION: Trigger validation for specific workspace outside normal cycle
        
        This can be called by other components (executor, quality gates, etc.) when they
        detect issues that need immediate goal validation and corrective action.
        """
        try:
            logger.warning(f"🚨 IMMEDIATE VALIDATION triggered for workspace {workspace_id} - Reason: {reason}")
            
            # Run validation for this specific workspace
            corrective_tasks = await self._process_workspace_validation(workspace_id)
            
            if corrective_tasks:
                executed_count = await self._execute_corrective_tasks_immediately(corrective_tasks, workspace_id)
                logger.warning(f"⚡ IMMEDIATE VALIDATION result: {executed_count}/{len(corrective_tasks)} corrective tasks executed")
                
                # Schedule priority recheck
                await self._schedule_priority_recheck(workspace_id, minutes=3)  # Faster recheck for triggered validations
                
                return {
                    "success": True,
                    "corrective_tasks_created": len(corrective_tasks),
                    "corrective_tasks_executed": executed_count,
                    "priority_recheck_scheduled": True
                }
            else:
                logger.info(f"✅ IMMEDIATE VALIDATION: No corrective tasks needed for workspace {workspace_id}")
                return {
                    "success": True,
                    "corrective_tasks_created": 0,
                    "corrective_tasks_executed": 0,
                    "priority_recheck_scheduled": False
                }
                
        except Exception as e:
            logger.error(f"Error in immediate validation for workspace {workspace_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _run_monitoring_cycle(self):
        """Execute one complete monitoring cycle"""
        cycle_start = datetime.now()
        logger.info(f"🔄 Starting goal monitoring cycle at {cycle_start}")
        
        try:
            # 🚨 CRITICAL FIX: Auto-recovery for stuck workspaces
            from workspace_recovery_system import workspace_recovery_system
            
            recovery_result = await workspace_recovery_system.scan_and_recover_stuck_workspaces()
            if recovery_result["recovered"] > 0:
                logger.info(f"🔧 Auto-recovered {recovery_result['recovered']} workspaces from intervention status")
            
            # 👥 UNIFIED AGENT STATUS: Run synchronization if available
            if AGENT_STATUS_MANAGER_AVAILABLE and agent_status_manager:
                try:
                    sync_result = await agent_status_manager.synchronize_agent_statuses()
                    if sync_result.agents_updated > 0:
                        logger.info(f"🎯 AGENT SYNC: Updated {sync_result.agents_updated} agents, "
                                   f"fixed {sync_result.inconsistencies_fixed}/{sync_result.inconsistencies_found} inconsistencies")
                except Exception as sync_error:
                    logger.warning(f"⚠️ Agent status synchronization failed: {sync_error}")
            
            # 1. Get active workspaces that need validation
            workspaces_to_validate = await self._get_workspaces_needing_validation()
            
            if not workspaces_to_validate:
                logger.info("✅ No workspaces need validation this cycle")
                return
            
            logger.info(f"📊 Validating {len(workspaces_to_validate)} workspaces")
            
            # 🚀 PERFORMANCE OPTIMIZATION: Batch load all goals for all workspaces
            from utils.workspace_goals_cache import batch_get_workspace_goals_cached
            
            logger.info(f"🚀 Batch loading goals for {len(workspaces_to_validate)} workspaces")
            all_workspace_goals = await batch_get_workspace_goals_cached(
                workspaces_to_validate, 
                status_filter=GoalStatus.ACTIVE.value
            )
            
            # 2. Process each workspace with pre-loaded goals
            total_corrective_tasks = 0
            for workspace_id in workspaces_to_validate:
                # Pass pre-loaded goals to avoid individual database queries
                workspace_goals = all_workspace_goals.get(workspace_id, [])
                corrective_tasks = await self._process_workspace_validation(workspace_id, preloaded_goals=workspace_goals)
                total_corrective_tasks += len(corrective_tasks)
            
            # 2.5. Check for completed goals without deliverables
            # await self._check_and_create_missing_deliverables()
            
            # 3. Cleanup caches to prevent memory bloat
            await self._cleanup_caches_if_needed()
            
            # 4. Log cycle summary
            cycle_duration = datetime.now() - cycle_start
            cache_stats = self.get_cache_stats()
            logger.info(
                f"✅ Monitoring cycle completed in {cycle_duration.total_seconds():.1f}s. "
                f"Processed {len(workspaces_to_validate)} workspaces, "
                f"generated {total_corrective_tasks} corrective tasks, "
                f"recovered {recovery_result['recovered']} stuck workspaces. "
                f"Cache: {cache_stats['active_workspaces_cache_size']}/{cache_stats['max_cache_entries']} workspaces, "
                f"{cache_stats['background_tasks_count']} background tasks"
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
    
    async def _process_workspace_validation(self, workspace_id: str, preloaded_goals: Optional[List[Dict]] = None) -> List[Dict[str, Any]]:
        """Process goal validation for a single workspace - OPTIMIZED with preloaded goals"""
        try:
            logger.info(f"🔍 Validating workspace {workspace_id}")
            
            # 🔧 CRITICAL FIX: Check if team proposal has been approved before validation
            # Skip validation if no team has been approved to prevent premature workspace activation
            try:
                # First check if there's an approved team proposal for this workspace
                proposal_response = supabase.table("team_proposals").select("*").eq(
                    "workspace_id", workspace_id
                ).eq("status", "approved").execute()
                
                approved_proposals = proposal_response.data if proposal_response.data else []
                
                if not approved_proposals:
                    logger.warning(f"⚠️ Skipping goal validation for workspace {workspace_id} - no approved team proposal found")
                    logger.info(f"💡 Tip: Approve the team proposal first before automatic goal validation starts")
                    return []
                
                # Then check if agents are available (they should be created after approval)
                agents_response = supabase.table("agents").select("*").eq(
                    "workspace_id", workspace_id
                ).eq("status", "available").execute()
                
                available_agents = agents_response.data if agents_response.data else []
                
                if not available_agents:
                    logger.warning(f"⚠️ Skipping goal validation for workspace {workspace_id} - no available agents found")
                    logger.info(f"💡 Tip: Team approved but agents not yet created - please wait for agent provisioning")
                    return []
                    
                logger.info(f"✅ Found approved team proposal and {len(available_agents)} available agents in workspace {workspace_id} - proceeding with validation")
            except Exception as approval_check_error:
                logger.error(f"Error checking team approval for workspace {workspace_id}: {approval_check_error}")
                logger.warning(f"⚠️ Skipping goal validation due to approval check error")
                return []
            
            # 1. Get completed tasks for validation
            completed_tasks = await self._get_completed_tasks(workspace_id)
            
            # 2. Use preloaded goals if available, otherwise fetch from cache/database
            if preloaded_goals is not None:
                workspace_goals = preloaded_goals
                logger.debug(f"🚀 Using preloaded goals for workspace {workspace_id} ({len(workspace_goals)} goals)")
            else:
                workspace_goals = await self._get_workspace_database_goals(workspace_id)
            
            if not workspace_goals:
                logger.warning(f"No database goals found for workspace {workspace_id}")
                return []
            
            # 3. 🎯 INTELLIGENT VALIDATION OPTIMIZATION: Check if validation should proceed
            all_corrective_tasks = []
            validation_results = []
            optimization_decisions = []
            
            for goal_data in workspace_goals:
                try:
                    goal_id = goal_data.get("id")
                    metric_type = goal_data.get("metric_type", "Unknown Goal")
                    
                    # Check if this goal should be validated (optimization)
                    if GOAL_VALIDATION_OPTIMIZER_AVAILABLE and goal_validation_optimizer:
                        optimization_result = await goal_validation_optimizer.should_proceed_with_validation(
                            workspace_id=workspace_id,
                            goal_data=goal_data,
                            recent_tasks=completed_tasks  # Use completed tasks as recent tasks context
                        )
                        
                        optimization_decisions.append({
                            "goal_id": goal_id,
                            "metric_type": metric_type,
                            "decision": optimization_result.decision.value,
                            "reason": optimization_result.reason,
                            "confidence": optimization_result.confidence
                        })
                        
                        if not optimization_result.should_proceed:
                            logger.info(f"🎯 OPTIMIZATION SKIP: Goal '{metric_type}' ({goal_id}) - "
                                       f"{optimization_result.decision.value}: {optimization_result.reason}")
                            continue
                        else:
                            logger.debug(f"🎯 OPTIMIZATION PROCEED: Goal '{metric_type}' ({goal_id}) - "
                                        f"{optimization_result.reason}")
                    
                    # Run validation for this specific goal
                    goal_validation_results = [goal_validator.validate_goal(goal_data)]
                    
                    validation_results.extend(goal_validation_results)
                    
                    # 🚀 CRITICAL FIX: Generate tasks for goals at 0% progress (not just corrective tasks)
                    current_value = goal_data.get("current_value", 0)
                    target_value = goal_data.get("target_value", 1)
                    progress = (current_value / max(target_value, 1)) * 100
                    
                    if progress == 0:
                        # Goal has 0% progress - needs initial tasks
                        logger.warning(f"🎯 Goal '{metric_type}' ({goal_id}) at 0% progress - generating initial tasks")
                        
                        # Generate initial tasks for this goal using goal-driven task planner
                        initial_tasks = await goal_driven_task_planner.plan_tasks_for_goal(
                            workspace_goal=goal_data,
                            workspace_id=workspace_id
                        )
                        
                        if initial_tasks:
                            logger.info(f"✅ Generated {len(initial_tasks)} initial tasks for goal '{metric_type}'")
                            # Add generated tasks to the corrective tasks list (they will be executed immediately)
                            for task in initial_tasks:
                                task_to_add = {
                                    "goal_id": goal_id,
                                    "name": task.get("name", f"Task for {metric_type}"),
                                    "description": task.get("description", f"Work on achieving {metric_type}"),
                                    "priority": "high",
                                    "metric_type": metric_type,
                                    "contribution_expected": task.get("contribution_expected", 1),
                                    "numerical_target": task.get("numerical_target", 1),
                                    "is_corrective": False,  # These are initial tasks, not corrective
                                    "is_goal_driven": True,
                                    "agent_requirements": task.get("agent_requirements", {"role": "specialist"}),
                                    "urgency_reason": f"Goal at 0% progress - needs immediate action"
                                }
                                all_corrective_tasks.append(task_to_add)
                        else:
                            logger.error(f"❌ Failed to generate initial tasks for goal '{metric_type}' at 0% progress")
                    
                    # Also check for validation failures (original logic)
                    if goal_validation_results:
                        for res in goal_validation_results:
                            if not res.get("valid", True):
                                logger.warning(f"Goal {goal_id} failed validation: {res.get('issues')}")
                                # Future: Add corrective action logic here if validation actually fails
                    
                except Exception as goal_error:
                    logger.error(f"❌ Error validating goal {goal_data.get('id', 'unknown')}: {goal_error}")
                    continue
            
            # Log optimization summary
            if optimization_decisions:
                skipped_count = len([d for d in optimization_decisions if not d.get("should_proceed", True)])
                total_goals = len(workspace_goals)
                logger.info(f"🎯 VALIDATION OPTIMIZATION: {skipped_count}/{total_goals} goals skipped, "
                           f"{len(validation_results)} validations performed")
            
            # 4. Update last_validation_at for all goals in workspace
            await self._update_validation_timestamps(workspace_id)
            
            # 5. 🚀 CRITICAL FIX: Asset Requirements Generation Check & Trigger
            asset_requirements_generated = await self._ensure_asset_requirements_exist(workspace_goals, workspace_id)
            
            # 6. Use aggregated corrective tasks
            corrective_tasks = all_corrective_tasks
            
            # 7. 📋 CREATE CORRECTIVE TASKS in database
            created_tasks = await self._create_corrective_tasks(corrective_tasks, workspace_id)
            
            # 8. 🚀 CRITICAL FIX: EXECUTE CORRECTIVE TASKS IMMEDIATELY
            if created_tasks:
                executed_count = await self._execute_corrective_tasks_immediately(created_tasks, workspace_id)
                logger.warning(f"⚡ IMMEDIATE EXECUTION: {executed_count}/{len(created_tasks)} corrective tasks queued for execution")
                
                # 🔥 ENHANCED: Trigger immediate re-monitoring for critical workspaces
                if executed_count > 0:
                    await self._schedule_priority_recheck(workspace_id, minutes=5)
                    logger.warning(f"🔄 PRIORITY RECHECK scheduled for workspace {workspace_id} in 5 minutes")
                    
                    # 🎼 WORKFLOW ORCHESTRATOR: Trigger complete workflow if significant progress
                    await self._trigger_workflow_orchestrator_for_goals(workspace_id, workspace_goals)
            
            # 9. Log validation summary
            critical_issues = [v for v in validation_results if not v.get("valid", True)]
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
        """Get database goals for validation (includes goal_id) - OPTIMIZED with caching"""
        try:
            # 🚀 PERFORMANCE OPTIMIZATION: Use cached query instead of direct database call
            from utils.workspace_goals_cache import get_workspace_goals_cached
            
            goals = await get_workspace_goals_cached(
                workspace_id, 
                force_refresh=False,  # Use cache for better performance
                status_filter=GoalStatus.ACTIVE.value
            )
            
            logger.info(f"📋 Found {len(goals)} active database goals for workspace {workspace_id} (cached)")
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
                goal_id = task_data.get("goal_id")
                if not goal_id:
                    logger.warning("Skipping corrective task creation: goal_id is missing.")
                    continue

                # 🚨 IDEMPOTENCY FIX: Check if a corrective task for this goal already exists
                existing_task_response = supabase.table("tasks").select("id").eq("goal_id", goal_id).eq("is_corrective", True).in_("status", ["pending", "in_progress"]).execute()
                
                if existing_task_response.data:
                    logger.warning(f"Skipping corrective task for goal {goal_id}: an active corrective task already exists.")
                    continue

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
                    "goal_id": task_data.get("goal_id"),
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
    
    async def _execute_corrective_tasks_immediately(
        self, 
        created_tasks: List[Dict[str, Any]], 
        workspace_id: str
    ) -> int:
        """
        🚀 CRITICAL FIX: Execute corrective tasks immediately instead of waiting for polling
        
        This ensures that when the goal monitor detects issues, corrective actions
        are taken immediately rather than waiting for the next executor polling cycle.
        """
        executed_count = 0
        
        try:
            # Import task executor
            from executor import task_executor
            
            logger.info(f"⚡ Executing {len(created_tasks)} corrective tasks immediately for workspace {workspace_id}")
            
            for task_data in created_tasks:
                try:
                    task_id = task_data.get("id")
                    task_name = task_data.get("name", "Unknown Task")
                    
                    if not task_id:
                        logger.error(f"Cannot execute task without ID: {task_name}")
                        continue
                    
                    # 🎯 PRIORITY EXECUTION: Add to executor queue with high priority
                    # Convert task to format expected by executor
                    executor_task = {
                        "id": task_id,
                        "workspace_id": workspace_id,
                        "name": task_name,
                        "description": task_data.get("description", ""),
                        "status": "pending",
                        "priority": "high",
                        "agent_id": task_data.get("agent_id"),
                        "assigned_to_role": task_data.get("assigned_to_role"),
                        "is_corrective": True,  # Mark as corrective task
                        "created_by": "automated_goal_monitor"
                    }
                    
                    # Add to executor queue immediately
                    await task_executor.add_task_to_queue(executor_task)
                    
                    executed_count += 1
                    logger.warning(f"⚡ QUEUED CORRECTIVE TASK: {task_name} (ID: {task_id}) for immediate execution")
                    
                except Exception as e:
                    logger.error(f"Failed to queue corrective task {task_data.get('name', 'unknown')}: {e}")
            
            return executed_count
            
        except Exception as e:
            logger.error(f"Error executing corrective tasks immediately: {e}")
            return 0
    
    async def _schedule_priority_recheck(self, workspace_id: str, minutes: int = 5):
        """
        🔥 PRIORITY RECHECK: Schedule immediate re-monitoring for critical workspaces
        
        When corrective tasks are executed, we want to quickly verify if they
        resolved the issues instead of waiting for the normal 20-minute cycle.
        """
        try:
            import asyncio
            
            async def priority_recheck():
                try:
                    await asyncio.sleep(minutes * 60)  # Wait specified minutes
                    
                    logger.info(f"🔄 PRIORITY RECHECK: Re-validating workspace {workspace_id}")
                    
                    # Re-run validation for this specific workspace
                    corrective_tasks = await self._process_workspace_validation(workspace_id)
                    
                    if corrective_tasks:
                        logger.warning(f"🚨 PRIORITY RECHECK: {len(corrective_tasks)} additional corrective tasks needed for {workspace_id}")
                        # Execute immediately again
                        await self._execute_corrective_tasks_immediately(corrective_tasks, workspace_id)
                    else:
                        logger.info(f"✅ PRIORITY RECHECK: Workspace {workspace_id} issues resolved")
                        
                except Exception as e:
                    logger.error(f"Error in priority recheck for workspace {workspace_id}: {e}")
            
            # Schedule as background task
            asyncio.create_task(priority_recheck())
            
        except Exception as e:
            logger.error(f"Error scheduling priority recheck: {e}")
    
    async def _check_workspace_health(self, workspace_id: str) -> bool:
        """
        🏥 ENHANCED WORKSPACE HEALTH CHECK with Auto-Recovery
        
        Returns False for workspaces that shouldn't be processed by goal monitoring
        Uses WorkspaceHealthManager for intelligent health assessment and recovery
        """
        try:
            # 🏥 ENHANCED: Try to use WorkspaceHealthManager first
            try:
                from services.workspace_health_manager import workspace_health_manager
                
                # Get comprehensive health report with auto-recovery
                health_report = await workspace_health_manager.check_workspace_health_with_recovery(
                    workspace_id, attempt_auto_recovery=True
                )
                
                # CRITICAL FIX: Ensure health_report.issues is always a list of dicts
                if not hasattr(health_report, 'issues') or not isinstance(health_report.issues, list):
                    logger.error(f"❌ Health report issues is not a list: {type(health_report.issues)}")
                    health_report.issues = [] # Default to empty list to prevent errors

                # CRITICAL FIX: Ensure each issue in health_report.issues is a dict and has 'level' attribute
                cleaned_issues = []
                for issue in health_report.issues:
                    if isinstance(issue, dict) and 'level' in issue:
                        cleaned_issues.append(issue)
                    elif hasattr(issue, '__dict__') and 'level' in issue.__dict__:
                        cleaned_issues.append(issue.__dict__)
                    else:
                        logger.warning(f"Malformed issue in health report: {issue}")
                health_report.issues = cleaned_issues

                if health_report.is_healthy:
                    logger.debug(f"✅ Workspace {workspace_id} health score: {health_report.overall_score:.1f}%")
                    return True
                else:
                    # Check if issues are auto-recoverable
                    recoverable_issues = [issue for issue in health_report.issues if issue.get('auto_recoverable', False)]
                    unrecoverable_issues = [issue for issue in health_report.issues if not issue.get('auto_recoverable', False)]
                    
                    if unrecoverable_issues:
                        # Log critical unrecoverable issues
                        critical_descriptions = [issue.get('description', 'Unknown') for issue in unrecoverable_issues 
                                               if issue.get('level', '').lower() in ['critical', 'emergency']]
                        
                        if critical_descriptions:
                            await self._alert_workspace_issue(
                                workspace_id,
                                "CRITICAL_UNRECOVERABLE_ISSUES",
                                f"Critical issues requiring manual intervention: {'; '.join(critical_descriptions[:2])}"
                            )
                            return False
                    
                    if recoverable_issues:
                        logger.info(f"🔧 Workspace {workspace_id} has recoverable issues - auto-recovery attempted")
                        # Continue processing as recovery was attempted
                        return True
                    
                    # No critical unrecoverable issues, continue processing
                    logger.info(f"⚠️ Workspace {workspace_id} health score low ({health_report.overall_score:.1f}%) but continuing")
                    return True
                    
            except ImportError:
                logger.debug("WorkspaceHealthManager not available, falling back to basic health check")
                
                # FALLBACK: Original basic health check logic
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
                    # 🔧 ENHANCED: Try auto-recovery for needs_intervention status
                    logger.info(f"🔧 Attempting auto-recovery for workspace {workspace_id} marked as needs_intervention")
                    
                    try:
                        # Reset status to active
                        supabase.table("workspaces").update({
                            "status": "active"
                        }).eq("id", workspace_id).execute()
                        
                        logger.info(f"✅ Auto-recovered workspace {workspace_id} from needs_intervention to active")
                        return True  # Continue processing after recovery
                        
                    except Exception as recovery_err:
                        logger.error(f"❌ Failed to auto-recover workspace {workspace_id}: {recovery_err}")
                        return False
                
                # 3. 🎯 UNIFIED AGENT STATUS CHECK: Use AgentStatusManager if available
                if AGENT_STATUS_MANAGER_AVAILABLE and agent_status_manager:
                    try:
                        # Get available agents using unified logic
                        available_agents_info = await agent_status_manager.get_available_agents(workspace_id)
                        available_agents = [
                            {
                                "id": agent.id,
                                "status": agent.status.value
                            }
                            for agent in available_agents_info
                        ]
                        
                        # Get all agents count for health reporting
                        agents_response = supabase.table("agents").select("id, status").eq(
                            "workspace_id", workspace_id
                        ).execute()
                        agents = agents_response.data or []
                        
                        logger.debug(f"🎯 UNIFIED AGENT STATUS: {len(available_agents)} available agents from AgentStatusManager")
                        
                    except Exception as asm_error:
                        logger.warning(f"⚠️ AgentStatusManager error in health check, falling back: {asm_error}")
                        # Fallback to legacy logic
                        agents_response = supabase.table("agents").select("id, status").eq(
                            "workspace_id", workspace_id
                        ).execute()
                        
                        agents = agents_response.data or []
                        # CRITICAL FIX: Accept both "available" and "active" agents (matching executor.py logic)
                        available_agents = [a for a in agents if a.get("status") in ["available", "active"]]
                else:
                    # FALLBACK: Legacy agent status checking
                    agents_response = supabase.table("agents").select("id, status").eq(
                        "workspace_id", workspace_id
                    ).execute()
                    
                    agents = agents_response.data or []
                    # CRITICAL FIX: Accept both "available" and "active" agents (matching executor.py logic)
                    available_agents = [a for a in agents if a.get("status") in ["available", "active"]]
                
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
                    "system_prompt": f"""You are an expert specialist for '{workspace_name}'. Your goal is: {workspace_goal}. You excel at executing complex tasks with precision and delivering concrete, measurable results.

🚫 **ZERO-PLANNING RULE: CRITICAL**
- **DO NOT** output a plan, an outline, or a description of the work to be done.
- **DO** produce the final, complete, and ready-to-use asset itself.
- **Example of what NOT to do**: "To create the report, I will first analyze the data, then structure the sections..."
- **Example of what TO DO**: Directly output the full, formatted report.

🏁 **FINAL OUTPUT REQUIREMENTS:**
- The `result` field MUST contain the complete, final, and ready-to-use asset.
- DO NOT put a summary or description in the `result` field.

Always focus on actionable deliverables.""",
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
                
                # FIXED: Try to create goals from workspace goal text
                workspace_goal_text = await self._get_workspace_goal_text(workspace_id)
                if workspace_goal_text:
                    logger.info(f"🔧 Creating workspace goals from goal text: {workspace_goal_text[:100]}...")
                    
                    try:
                        from database import _auto_create_workspace_goals
                        created_goals = await _auto_create_workspace_goals(workspace_id, workspace_goal_text)
                        
                        if created_goals:
                            logger.info(f"✅ Created {len(created_goals)} workspace goals from goal text")
                            
                            # Re-fetch the newly created goals
                            response = supabase.table("workspace_goals").select("*").eq(
                                "workspace_id", workspace_id
                            ).eq(
                                "status", GoalStatus.ACTIVE.value
                            ).execute()
                            workspace_goals = response.data
                        else:
                            logger.warning(f"Failed to create goals from workspace goal text")
                    except Exception as e:
                        logger.error(f"Error creating goals from workspace text: {e}")
                
                # If still no goals, return failure
                if not workspace_goals:
                    # Reset workspace status
                    supabase.table("workspaces").update({
                        "status": "active",
                        "updated_at": datetime.now().isoformat()
                    }).eq("id", workspace_id).execute()
                    
                    return {"success": False, "reason": "no_active_goals_and_failed_to_create"}
            
            # 🧠 AI-DRIVEN: Use UnifiedOrchestrator with SDK Guardrails integration
            # SDK Pipeline integration is available through enhanced specialist agents with native guardrails

            else:
                logger.info("Legacy Orchestrator: Using goal_driven_task_planner for task generation.")
                from goal_driven_task_planner import goal_driven_task_planner
                
                initial_tasks = []
                for goal in workspace_goals:
                    logger.info(f"🎯 Creating tasks for goal: {goal['metric_type']} (target: {goal['target_value']})")
                    
                    goal_tasks = await goal_driven_task_planner.plan_tasks_for_goal(
                        workspace_goal=goal,
                        workspace_id=workspace_id
                    )
                    
                    # 🛡️ STRATEGIC MONITORING: Alert if no tasks created for a goal
                    if not goal_tasks:
                        logger.error(f"❌ CRITICAL: No tasks created for goal {goal['metric_type']} (ID: {goal.get('id')})")
                        await self._alert_workspace_issue(
                            workspace_id,
                            "NO_TASKS_FOR_GOAL",
                            f"Goal '{goal['metric_type']}' has no tasks - may block progress"
                        )
                    else:
                        # Check if tasks have agent assignments
                        unassigned_tasks = [t for t in goal_tasks if not t.get('agent_id')]
                        if unassigned_tasks:
                            logger.warning(f"⚠️ {len(unassigned_tasks)}/{len(goal_tasks)} tasks for goal '{goal['metric_type']}' have no agent assigned")
                    
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
    
    async def _ensure_asset_requirements_exist(self, workspace_goals: List[Dict[str, Any]], workspace_id: str) -> int:
        """
        🚀 CRITICAL FIX: Ensure all goals have asset requirements
        
        This function checks each goal and generates asset requirements if they don't exist.
        Implements Pillar 12: Concrete Deliverables enforcement.
        """
        try:
            if not asset_requirements_generator:
                logger.warning("⚠️ Asset Requirements Generator not available - skipping asset check")
                return 0
            
            total_generated = 0
            
            for goal_data in workspace_goals:
                try:
                    goal_id = goal_data.get("id")
                    metric_type = goal_data.get("metric_type", "Unknown Goal")
                    
                    # Check if this goal already has asset requirements
                    # This is a simplified check. A real implementation would query the asset_requirements table.
                    existing_requirements = goal_data.get("asset_requirements_count", 0) > 0
                    
                    if not existing_requirements:
                        logger.info(f"🎯 Goal '{metric_type}' has no asset requirements - generating automatically")
                        
                        # Convert to WorkspaceGoal model
                        from models import WorkspaceGoal
                        goal_model = WorkspaceGoal(**goal_data)
                        
                        # Generate asset requirements
                        asset_requirements = await asset_requirements_generator.generate_requirements_from_goal(goal_model)
                        requirements_count = len(asset_requirements)
                        total_generated += requirements_count
                        
                        # Update goal with asset requirements count
                        supabase.table("workspace_goals").update({
                            "asset_requirements_count": requirements_count,
                            "ai_validation_enabled": True,
                            "updated_at": datetime.now().isoformat()
                        }).eq("id", goal_id).execute()
                        
                        logger.info(f"✅ Generated {requirements_count} asset requirements for goal '{metric_type}'")
                        
                        # Log the generation
                        supabase.table("logs").insert({
                            "workspace_id": workspace_id,
                            "type": "asset_generation",
                            "message": f"Auto-generated {requirements_count} asset requirements for goal: {metric_type}",
                            "metadata": {
                                "goal_id": goal_id,
                                "asset_requirements_count": requirements_count,
                                "trigger": "automated_goal_monitoring",
                                "timestamp": datetime.now().isoformat()
                            }
                        }).execute()
                        
                    else:
                        logger.debug(f"✅ Goal '{metric_type}' already has {goal_data.get('asset_requirements_count', 0)} asset requirements")
                        
                except Exception as e:
                    logger.error(f"❌ Failed to ensure asset requirements for goal {goal_data.get('id', 'unknown')}: {e}")
                    continue
            
            if total_generated > 0:
                logger.info(f"🚀 ASSET GENERATION SUMMARY: Generated {total_generated} total asset requirements for workspace {workspace_id}")
            
            return total_generated
            
        except Exception as e:
            logger.error(f"❌ Critical error in asset requirements generation: {e}")
            return 0
    
    async def _cleanup_background_tasks(self):
        """🔧 FIX: Cleanup background tasks to prevent memory leaks"""
        try:
            if not self._background_tasks:
                return
            
            logger.info(f"🧹 Cleaning up {len(self._background_tasks)} background tasks")
            
            # Cancel all tracked background tasks
            for task in list(self._background_tasks):
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                    except Exception as e:
                        logger.debug(f"Background task cleanup error: {e}")
                
                self._background_tasks.discard(task)
            
            logger.info("✅ All background tasks cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up background tasks: {e}")
    
    def _add_background_task(self, task: asyncio.Task):
        """Track a background task to prevent leaks"""
        self._background_tasks.add(task)
        
        # Clean up completed tasks automatically
        def cleanup_completed(task):
            self._background_tasks.discard(task)
        
        task.add_done_callback(cleanup_completed)
    
    async def _cleanup_caches_if_needed(self):
        """🔧 FIX: Cleanup caches if they exceed size/TTL limits"""
        current_time = time.time()
        
        # Cleanup active workspaces cache
        expired_workspaces = [
            ws_id for ws_id, (timestamp, _) in self.active_workspaces_cache.items()
            if current_time - timestamp > self.cache_ttl_seconds
        ]
        
        for ws_id in expired_workspaces:
            del self.active_workspaces_cache[ws_id]
        
        # Cleanup last validation cache  
        expired_validations = [
            ws_id for ws_id, timestamp in self.last_validation_cache.items()
            if current_time - timestamp > self.cache_ttl_seconds
        ]
        
        for ws_id in expired_validations:
            del self.last_validation_cache[ws_id]
        
        # If still too many entries, remove oldest
        if len(self.active_workspaces_cache) > self.max_cache_entries:
            # Sort by timestamp and remove oldest
            sorted_entries = sorted(
                self.active_workspaces_cache.items(),
                key=lambda x: x[1][0]  # Sort by timestamp
            )
            
            excess_count = len(self.active_workspaces_cache) - self.max_cache_entries
            for ws_id, _ in sorted_entries[:excess_count]:
                del self.active_workspaces_cache[ws_id]
        
        if len(self.last_validation_cache) > self.max_cache_entries:
            sorted_entries = sorted(
                self.last_validation_cache.items(),
                key=lambda x: x[1]  # Sort by timestamp
            )
            
            excess_count = len(self.last_validation_cache) - self.max_cache_entries
            for ws_id, _ in sorted_entries[:excess_count]:
                del self.last_validation_cache[ws_id]
        
        if expired_workspaces or expired_validations:
            logger.info(f"🧹 Cache cleanup: removed {len(expired_workspaces)} workspace entries, {len(expired_validations)} validation entries")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """🔧 FIX: Get cache statistics for monitoring"""
        return {
            "active_workspaces_cache_size": len(self.active_workspaces_cache),
            "last_validation_cache_size": len(self.last_validation_cache),
            "max_cache_entries": self.max_cache_entries,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "background_tasks_count": len(self._background_tasks)
        }
    
    async def _check_and_create_missing_deliverables(self):
        """Check for completed goals without deliverables and create them"""
        try:
            logger.info("📦 Checking for completed goals without deliverables...")
            
            # Import the deliverable creation logic
            # from fix_deliverable_creation import check_and_fix_deliverable_creation
            
            # Run the deliverable creation check
            # await check_and_fix_deliverable_creation()
            logger.info("🚀 Deliverable creation check temporarily disabled - pipeline should handle this automatically")
            
        except Exception as e:
            logger.error(f"Error checking for missing deliverables: {e}")

    async def _trigger_workflow_orchestrator_for_goals(self, workspace_id: str, workspace_goals: List[Dict[str, Any]]):
        """
        🎼 WORKFLOW ORCHESTRATOR INTEGRATION
        
        Trigger complete workflows for goals that are ready for end-to-end processing
        """
        try:
            # Import WorkflowOrchestrator
            try:
                from services.unified_orchestrator import get_unified_orchestrator
                workflow_orchestrator = get_unified_orchestrator()
                WORKFLOW_ORCHESTRATOR_AVAILABLE = True
            except ImportError as e:
                logger.warning(f"WorkflowOrchestrator not available: {e}")
                return
            
            # Analyze which goals are ready for complete workflow orchestration
            goals_for_workflow = []
            
            for goal in workspace_goals:
                goal_id = goal.get("id")
                goal_status = goal.get("status", "")
                current_value = goal.get("current_value", 0)
                target_value = goal.get("target_value", 1)
                
                # Skip completed goals
                if goal_status == "completed":
                    continue
                
                # Check if goal has enough progress to warrant workflow orchestration
                progress_ratio = current_value / max(target_value, 1)
                
                # Trigger workflow for goals with 30%+ progress but not yet completed
                if progress_ratio >= 0.3 and progress_ratio < 1.0:
                    goals_for_workflow.append(goal)
                    logger.info(f"🎯 Goal {goal_id} ready for workflow orchestration: {progress_ratio:.1%} progress")
                
                # Also trigger for completely new goals (0% progress) to kick-start them
                elif progress_ratio == 0.0:
                    goals_for_workflow.append(goal)
                    logger.info(f"🚀 New goal {goal_id} ready for initial workflow orchestration")
            
            # Execute workflows for selected goals
            successful_workflows = 0
            for goal in goals_for_workflow:
                goal_id = goal.get("id")
                try:
                    logger.info(f"🎼 TRIGGERING WORKFLOW ORCHESTRATOR: Starting complete workflow for goal {goal_id}")
                    
                    # Execute complete workflow with conservative settings
                    workflow_result = await workflow_orchestrator.execute_complete_workflow(
                        workspace_id=workspace_id,
                        goal_id=goal_id,
                        timeout_minutes=20,  # Shorter timeout for goal monitor context
                        enable_rollback=True,
                        quality_threshold=70.0  # Slightly lower threshold for goal validation context
                    )
                    
                    if workflow_result.success:
                        successful_workflows += 1
                        logger.info(f"✅ WORKFLOW SUCCESS: Goal {goal_id} workflow completed successfully")
                        logger.info(f"📊 Results: {workflow_result.tasks_generated} tasks, {workflow_result.deliverables_created} deliverables, {workflow_result.quality_score:.1f}% quality")
                    else:
                        logger.warning(f"❌ WORKFLOW FAILED: Goal {goal_id} workflow failed: {workflow_result.error}")
                        
                        # Log rollback information if applicable
                        if workflow_result.rollback_performed:
                            rollback_status = "successful" if workflow_result.rollback_success else "failed"
                            logger.warning(f"🔄 ROLLBACK: {rollback_status} for goal {goal_id}")
                
                except Exception as goal_workflow_error:
                    logger.error(f"❌ WORKFLOW ORCHESTRATOR: Critical error executing workflow for goal {goal_id}: {goal_workflow_error}")
                    logger.info("🔄 Goal monitoring will continue normally despite workflow orchestrator error")
            
            if goals_for_workflow:
                logger.info(f"🎼 WORKFLOW ORCHESTRATOR SUMMARY: {successful_workflows}/{len(goals_for_workflow)} workflows successful for workspace {workspace_id}")
            else:
                logger.debug(f"No goals ready for workflow orchestration in workspace {workspace_id}")
                
        except Exception as e:
            logger.error(f"Error in WorkflowOrchestrator integration for workspace {workspace_id}: {e}")

# Singleton instance
automated_goal_monitor = AutomatedGoalMonitor()

# Optional: Auto-start monitoring when module is imported
# Uncomment the line below to enable automatic monitoring
# asyncio.create_task(automated_goal_monitor.start_monitoring())