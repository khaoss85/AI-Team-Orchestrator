# backend/workspace_recovery_system.py
"""
🚨 WORKSPACE AUTO-RECOVERY SYSTEM
=====================================

Automatically recovers workspaces stuck in 'needs_intervention' status
by analyzing the root cause and applying appropriate fixes.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID

from models import WorkspaceStatus, TaskStatus, AgentStatus
from database import supabase, update_workspace_status

logger = logging.getLogger(__name__)

class WorkspaceRecoverySystem:
    """
    🔧 AUTO-RECOVERY: Diagnoses and fixes workspaces stuck in intervention status
    """
    
    def __init__(self):
        self.recovery_timeout_minutes = 30  # Recovery attempt timeout
        self.max_recovery_attempts = 3
        self.recovery_cooldown_hours = 2
        
    async def scan_and_recover_stuck_workspaces(self) -> Dict[str, Any]:
        """
        🔍 SCAN: Find and recover all workspaces stuck in needs_intervention
        """
        try:
            logger.info("🔍 Scanning for workspaces needing recovery...")
            
            # Find workspaces stuck in needs_intervention for more than 10 minutes
            cutoff_time = (datetime.now() - timedelta(minutes=10)).isoformat()
            
            response = supabase.table("workspaces").select("*").eq(
                "status", WorkspaceStatus.NEEDS_INTERVENTION.value
            ).lt(
                "updated_at", cutoff_time
            ).execute()
            
            stuck_workspaces = response.data or []
            
            if not stuck_workspaces:
                logger.info("✅ No workspaces stuck in intervention status")
                return {"success": True, "stuck_workspaces": 0, "recovered": 0}
            
            logger.warning(f"🚨 Found {len(stuck_workspaces)} workspaces stuck in intervention status")
            
            recovery_results = []
            successful_recoveries = 0
            
            for workspace in stuck_workspaces:
                workspace_id = workspace["id"]
                
                # Check recovery cooldown
                if await self._is_in_recovery_cooldown(workspace_id):
                    logger.info(f"⏳ Workspace {workspace_id} in recovery cooldown - skipping")
                    continue
                
                logger.info(f"🔧 Attempting recovery for workspace {workspace_id}")
                
                recovery_result = await self._recover_workspace(workspace_id, workspace)
                recovery_results.append(recovery_result)
                
                if recovery_result["success"]:
                    successful_recoveries += 1
            
            return {
                "success": True,
                "stuck_workspaces": len(stuck_workspaces),
                "recovered": successful_recoveries,
                "recovery_results": recovery_results
            }
            
        except Exception as e:
            logger.error(f"Error in workspace recovery scan: {e}")
            return {"success": False, "error": str(e)}
    
    async def _recover_workspace(self, workspace_id: str, workspace_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        🔧 RECOVER: Attempt to recover a specific workspace
        """
        try:
            # Log recovery attempt
            await self._log_recovery_attempt(workspace_id)
            
            # Diagnose the root cause
            diagnosis = await self._diagnose_workspace_issues(workspace_id)
            
            logger.info(f"🔍 Diagnosis for workspace {workspace_id}: {diagnosis['primary_issue']}")
            
            # Apply appropriate recovery strategy
            recovery_success = False
            
            if diagnosis["primary_issue"] == "no_active_agents":
                recovery_success = await self._recover_no_agents(workspace_id)
            elif diagnosis["primary_issue"] == "stuck_tasks":
                recovery_success = await self._recover_stuck_tasks(workspace_id)
            elif diagnosis["primary_issue"] == "goal_validation_failed":
                recovery_success = await self._recover_goal_validation(workspace_id)
            elif diagnosis["primary_issue"] == "task_creation_loop":
                recovery_success = await self._recover_task_loops(workspace_id)
            else:
                # Generic recovery: reset to active and trigger validation
                recovery_success = await self._generic_recovery(workspace_id)
            
            if recovery_success:
                logger.info(f"✅ Successfully recovered workspace {workspace_id}")
                return {
                    "workspace_id": workspace_id,
                    "success": True,
                    "recovery_strategy": diagnosis["primary_issue"],
                    "actions_taken": diagnosis.get("actions_taken", [])
                }
            else:
                logger.error(f"❌ Failed to recover workspace {workspace_id}")
                return {
                    "workspace_id": workspace_id,
                    "success": False,
                    "recovery_strategy": diagnosis["primary_issue"],
                    "reason": "Recovery strategy failed"
                }
            
        except Exception as e:
            logger.error(f"Error recovering workspace {workspace_id}: {e}")
            return {
                "workspace_id": workspace_id,
                "success": False,
                "error": str(e)
            }
    
    async def _diagnose_workspace_issues(self, workspace_id: str) -> Dict[str, Any]:
        """
        🔍 DIAGNOSE: Analyze workspace to identify root cause of intervention status
        """
        try:
            diagnosis = {
                "primary_issue": "unknown",
                "secondary_issues": [],
                "actions_taken": []
            }
            
            # Check 1: Active agents
            agents_response = supabase.table("agents").select("*").eq(
                "workspace_id", workspace_id
            ).execute()
            
            agents = agents_response.data or []
            active_agents = [a for a in agents if a.get("status") == AgentStatus.ACTIVE.value]
            
            if not active_agents:
                diagnosis["primary_issue"] = "no_active_agents"
                diagnosis["secondary_issues"].append(f"Found {len(agents)} total agents, 0 active")
                return diagnosis
            
            # Check 2: Stuck tasks
            tasks_response = supabase.table("tasks").select("*").eq(
                "workspace_id", workspace_id
            ).execute()
            
            tasks = tasks_response.data or []
            stuck_tasks = [
                t for t in tasks 
                if t.get("status") == TaskStatus.IN_PROGRESS.value and 
                self._is_task_stuck(t)
            ]
            
            if len(stuck_tasks) > 2:
                diagnosis["primary_issue"] = "stuck_tasks"
                diagnosis["secondary_issues"].append(f"Found {len(stuck_tasks)} stuck tasks")
                return diagnosis
            
            # Check 3: Task creation loops
            recent_tasks = [
                t for t in tasks 
                if self._is_recent_task(t, hours=1)
            ]
            
            if len(recent_tasks) > 20:  # Too many tasks created recently
                diagnosis["primary_issue"] = "task_creation_loop"
                diagnosis["secondary_issues"].append(f"Created {len(recent_tasks)} tasks in last hour")
                return diagnosis
            
            # Check 4: Goal validation issues
            goals_response = supabase.table("workspace_goals").select("*").eq(
                "workspace_id", workspace_id
            ).execute()
            
            goals = goals_response.data or []
            if not goals:
                diagnosis["primary_issue"] = "goal_validation_failed"
                diagnosis["secondary_issues"].append("No goals found in workspace")
                return diagnosis
            
            # Default: generic recovery needed
            diagnosis["primary_issue"] = "generic_recovery_needed"
            diagnosis["secondary_issues"].append("No specific issue identified")
            
            return diagnosis
            
        except Exception as e:
            logger.error(f"Error diagnosing workspace {workspace_id}: {e}")
            return {
                "primary_issue": "diagnosis_failed",
                "secondary_issues": [f"Diagnosis error: {str(e)}"],
                "actions_taken": []
            }
    
    async def _recover_no_agents(self, workspace_id: str) -> bool:
        """🔧 RECOVERY: Fix workspaces with no active agents"""
        try:
            # Reactivate existing agents if any
            update_result = supabase.table("agents").update({
                "status": AgentStatus.ACTIVE.value,
                "updated_at": datetime.now().isoformat()
            }).eq(
                "workspace_id", workspace_id
            ).neq(
                "status", AgentStatus.TERMINATED.value
            ).execute()
            
            reactivated_count = len(update_result.data) if update_result.data else 0
            
            if reactivated_count > 0:
                logger.info(f"✅ Reactivated {reactivated_count} agents for workspace {workspace_id}")
                
                # Set workspace to active
                await update_workspace_status(workspace_id, WorkspaceStatus.ACTIVE.value)
                return True
            else:
                logger.warning(f"❌ No agents to reactivate for workspace {workspace_id}")
                # Could trigger auto-provisioning here
                return False
                
        except Exception as e:
            logger.error(f"Error recovering agents for workspace {workspace_id}: {e}")
            return False
    
    async def _recover_stuck_tasks(self, workspace_id: str) -> bool:
        """🔧 RECOVERY: Fix workspaces with stuck tasks"""
        try:
            # Reset stuck tasks to pending
            cutoff_time = (datetime.now() - timedelta(hours=2)).isoformat()
            
            update_result = supabase.table("tasks").update({
                "status": TaskStatus.PENDING.value,
                "updated_at": datetime.now().isoformat()
            }).eq(
                "workspace_id", workspace_id
            ).eq(
                "status", TaskStatus.IN_PROGRESS.value
            ).lt(
                "updated_at", cutoff_time
            ).execute()
            
            reset_count = len(update_result.data) if update_result.data else 0
            
            if reset_count > 0:
                logger.info(f"✅ Reset {reset_count} stuck tasks for workspace {workspace_id}")
                
                # Set workspace to active
                await update_workspace_status(workspace_id, WorkspaceStatus.ACTIVE.value)
                return True
            else:
                return await self._generic_recovery(workspace_id)
                
        except Exception as e:
            logger.error(f"Error recovering stuck tasks for workspace {workspace_id}: {e}")
            return False
    
    async def _recover_goal_validation(self, workspace_id: str) -> bool:
        """🔧 RECOVERY: Fix goal validation issues"""
        try:
            # Trigger immediate goal validation
            from automated_goal_monitor import automated_goal_monitor
            
            validation_result = await automated_goal_monitor.trigger_immediate_validation(workspace_id)
            
            if validation_result.get("success"):
                logger.info(f"✅ Goal validation triggered for workspace {workspace_id}")
                
                # Set workspace to active
                await update_workspace_status(workspace_id, WorkspaceStatus.ACTIVE.value)
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error recovering goal validation for workspace {workspace_id}: {e}")
            return False
    
    async def _recover_task_loops(self, workspace_id: str) -> bool:
        """🔧 RECOVERY: Fix task creation loops"""
        try:
            # Cancel duplicate/loop tasks created in last hour
            cutoff_time = (datetime.now() - timedelta(hours=1)).isoformat()
            
            # Get recent tasks
            recent_response = supabase.table("tasks").select("*").eq(
                "workspace_id", workspace_id
            ).gte(
                "created_at", cutoff_time
            ).execute()
            
            recent_tasks = recent_response.data or []
            
            # Find duplicates by name similarity
            duplicate_task_ids = []
            seen_names = set()
            
            for task in recent_tasks:
                task_name = task.get("name", "").lower().strip()
                if task_name in seen_names:
                    duplicate_task_ids.append(task["id"])
                else:
                    seen_names.add(task_name)
            
            # Cancel duplicates
            if duplicate_task_ids:
                cancel_result = supabase.table("tasks").update({
                    "status": TaskStatus.CANCELED.value,
                    "updated_at": datetime.now().isoformat()
                }).in_(
                    "id", duplicate_task_ids
                ).execute()
                
                canceled_count = len(cancel_result.data) if cancel_result.data else 0
                logger.info(f"✅ Canceled {canceled_count} duplicate tasks for workspace {workspace_id}")
            
            # Set workspace to active
            await update_workspace_status(workspace_id, WorkspaceStatus.ACTIVE.value)
            return True
            
        except Exception as e:
            logger.error(f"Error recovering task loops for workspace {workspace_id}: {e}")
            return False
    
    async def _generic_recovery(self, workspace_id: str) -> bool:
        """🔧 RECOVERY: Generic recovery strategy"""
        try:
            # Simply reset workspace to active and log recovery
            await update_workspace_status(workspace_id, WorkspaceStatus.ACTIVE.value)
            
            logger.info(f"✅ Generic recovery applied to workspace {workspace_id} - reset to active")
            return True
            
        except Exception as e:
            logger.error(f"Error in generic recovery for workspace {workspace_id}: {e}")
            return False
    
    async def _is_in_recovery_cooldown(self, workspace_id: str) -> bool:
        """Check if workspace is in recovery cooldown period"""
        try:
            # Check for recent recovery attempts in logs
            cutoff_time = (datetime.now() - timedelta(hours=self.recovery_cooldown_hours)).isoformat()
            
            logs_response = supabase.table("logs").select("created_at").eq(
                "workspace_id", workspace_id
            ).like(
                "message", f"Recovery attempt for workspace {workspace_id}%"
            ).gte(
                "created_at", cutoff_time
            ).execute()
            
            return len(logs_response.data or []) > 0
            
        except Exception:
            return False
    
    async def _log_recovery_attempt(self, workspace_id: str):
        """Log recovery attempt for tracking"""
        try:
            supabase.table("logs").insert({
                "workspace_id": workspace_id,
                "type": "system",
                "message": f"Recovery attempt for workspace {workspace_id} - auto-recovery system engaged",
                "metadata": {
                    "recovery_system": "workspace_auto_recovery",
                    "timestamp": datetime.now().isoformat()
                }
            }).execute()
        except Exception as e:
            logger.warning(f"Failed to log recovery attempt: {e}")
    
    def _is_task_stuck(self, task: Dict[str, Any]) -> bool:
        """Check if a task is stuck (in_progress for too long)"""
        try:
            updated_at = task.get("updated_at")
            if not updated_at:
                return False
            
            updated_time = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            time_diff = datetime.now() - updated_time.replace(tzinfo=None)
            
            # Consider stuck if in_progress for more than 2 hours
            return time_diff.total_seconds() > 7200
            
        except Exception:
            return False
    
    def _is_recent_task(self, task: Dict[str, Any], hours: int = 1) -> bool:
        """Check if task was created recently"""
        try:
            created_at = task.get("created_at")
            if not created_at:
                return False
            
            created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            time_diff = datetime.now() - created_time.replace(tzinfo=None)
            
            return time_diff.total_seconds() < (hours * 3600)
            
        except Exception:
            return False

# Singleton instance
workspace_recovery_system = WorkspaceRecoverySystem()