#!/usr/bin/env python3
"""
Workspace Health Recovery System
AI-driven system to diagnose and recover workspaces marked as 'needs_intervention'
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta

from database import supabase
from models import WorkspaceStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorkspaceHealthRecovery:
    """AI-driven workspace health recovery system"""
    
    def __init__(self):
        self.recovery_actions = []
    
    async def diagnose_and_recover_workspaces(self) -> Dict[str, Any]:
        """
        🤖 AI-DRIVEN: Diagnose and recover all workspaces marked as needs_intervention
        """
        logger.info("🏥 Starting workspace health recovery process...")
        
        # Get all workspaces that need intervention
        try:
            workspaces_response = supabase.table('workspaces').select('*').eq('status', WorkspaceStatus.AUTO_RECOVERING.value).execute()
            
            if not workspaces_response.data:
                logger.info("✅ No workspaces need intervention")
                return {"healthy_workspaces": 0, "recovered_workspaces": 0}
            
            workspaces = workspaces_response.data
            logger.info(f"🔍 Found {len(workspaces)} workspaces needing intervention")
            
            recovered_count = 0
            for workspace in workspaces:
                workspace_id = workspace['id']
                workspace_name = workspace.get('name', 'Unnamed')
                
                logger.info(f"🔧 Diagnosing workspace: {workspace_name} ({workspace_id})")
                
                # AI-driven health diagnosis
                health_status = await self._diagnose_workspace_health(workspace)
                
                if health_status['can_recover']:
                    recovery_success = await self._recover_workspace(workspace, health_status)
                    if recovery_success:
                        recovered_count += 1
                        logger.info(f"✅ Recovered workspace: {workspace_name}")
                    else:
                        logger.warning(f"⚠️ Failed to recover workspace: {workspace_name}")
                else:
                    logger.warning(f"❌ Workspace cannot be auto-recovered: {workspace_name} - {health_status['reason']}")
            
            logger.info(f"🏁 Recovery complete: {recovered_count}/{len(workspaces)} workspaces recovered")
            
            return {
                "total_intervention_workspaces": len(workspaces),
                "recovered_workspaces": recovered_count,
                "recovery_rate": recovered_count / len(workspaces) if workspaces else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Error in workspace health recovery: {e}")
            return {"error": str(e)}
    
    async def _diagnose_workspace_health(self, workspace: Dict[str, Any]) -> Dict[str, Any]:
        """
        🤖 AI-DRIVEN: Comprehensive workspace health diagnosis
        """
        workspace_id = workspace['id']
        diagnosis = {
            "can_recover": False,
            "issues": [],
            "recovery_actions": [],
            "reason": ""
        }
        
        try:
            # Check 1: Verify workspace has goals
            goals_response = supabase.table('workspace_goals').select('*').eq('workspace_id', workspace_id).execute()
            goals = goals_response.data or []
            
            if not goals:
                diagnosis["issues"].append("no_goals")
                diagnosis["reason"] = "Workspace has no goals defined"
                return diagnosis
            
            # Check 2: Verify workspace has agents
            agents_response = supabase.table('agents').select('*').eq('workspace_id', workspace_id).execute()
            agents = agents_response.data or []
            
            if not agents:
                diagnosis["issues"].append("no_agents")
                diagnosis["recovery_actions"].append("create_basic_agents")
            
            # Check 3: Check for stuck tasks
            tasks_response = supabase.table('tasks').select('*').eq('workspace_id', workspace_id).eq('status', 'in_progress').execute()
            stuck_tasks = []
            
            if tasks_response.data:
                for task in tasks_response.data:
                    # Task stuck if in_progress for more than 2 hours
                    created_at = datetime.fromisoformat(task['created_at'].replace('Z', '+00:00'))
                    if datetime.now().replace(tzinfo=created_at.tzinfo) - created_at > timedelta(hours=2):
                        stuck_tasks.append(task)
            
            if stuck_tasks:
                diagnosis["issues"].append("stuck_tasks")
                diagnosis["recovery_actions"].append("reset_stuck_tasks")
            
            # Check 4: Check goal completion status
            completed_goals = [g for g in goals if g.get('current_value', 0) >= g.get('target_value', 1)]
            if len(completed_goals) == len(goals):
                diagnosis["issues"].append("all_goals_completed")
                diagnosis["recovery_actions"].append("mark_completed")
            
            # Check 5: Check for recent activity
            recent_tasks_response = supabase.table('tasks').select('*').eq('workspace_id', workspace_id).gte('created_at', (datetime.now() - timedelta(days=1)).isoformat()).execute()
            recent_activity = len(recent_tasks_response.data or [])
            
            if recent_activity == 0:
                diagnosis["issues"].append("no_recent_activity")
                diagnosis["recovery_actions"].append("restart_goal_monitoring")
            
            # Determine if we can recover
            recoverable_issues = ["no_agents", "stuck_tasks", "all_goals_completed", "no_recent_activity"]
            if any(issue in recoverable_issues for issue in diagnosis["issues"]):
                diagnosis["can_recover"] = True
            else:
                diagnosis["reason"] = f"Non-recoverable issues: {diagnosis['issues']}"
            
            logger.info(f"   Diagnosis: {len(diagnosis['issues'])} issues, recovery: {diagnosis['can_recover']}")
            return diagnosis
            
        except Exception as e:
            logger.error(f"Error diagnosing workspace {workspace_id}: {e}")
            diagnosis["reason"] = f"Diagnosis failed: {str(e)}"
            return diagnosis
    
    async def _recover_workspace(self, workspace: Dict[str, Any], health_status: Dict[str, Any]) -> bool:
        """
        🤖 AI-DRIVEN: Execute recovery actions for the workspace
        """
        workspace_id = workspace['id']
        recovery_actions = health_status.get("recovery_actions", [])
        
        try:
            success_count = 0
            
            for action in recovery_actions:
                if action == "create_basic_agents":
                    if await self._create_basic_agents(workspace_id):
                        success_count += 1
                        logger.info(f"     ✅ Created basic agents for workspace")
                    
                elif action == "reset_stuck_tasks":
                    if await self._reset_stuck_tasks(workspace_id):
                        success_count += 1
                        logger.info(f"     ✅ Reset stuck tasks")
                    
                elif action == "mark_completed":
                    if await self._mark_workspace_completed(workspace_id):
                        success_count += 1
                        logger.info(f"     ✅ Marked workspace as completed")
                    
                elif action == "restart_goal_monitoring":
                    if await self._restart_goal_monitoring(workspace_id):
                        success_count += 1
                        logger.info(f"     ✅ Restarted goal monitoring")
            
            # If all actions succeeded, mark workspace as active
            if success_count == len(recovery_actions):
                await self._mark_workspace_healthy(workspace_id)
                return True
            else:
                logger.warning(f"     ⚠️ Only {success_count}/{len(recovery_actions)} recovery actions succeeded")
                return False
            
        except Exception as e:
            logger.error(f"Error recovering workspace {workspace_id}: {e}")
            return False
    
    async def _create_basic_agents(self, workspace_id: str) -> bool:
        """Create basic agent setup for the workspace"""
        try:
            # Import Director to create basic team
            from ai_agents.director import DirectorAgent
            
            director = DirectorAgent()
            
            # Get workspace info
            workspace_response = supabase.table('workspaces').select('*').eq('id', workspace_id).execute()
            workspace = workspace_response.data[0] if workspace_response.data else {}
            
            # Create basic team proposal
            result = await director.propose_specialized_team({
                "workspace_id": workspace_id,
                "project_description": workspace.get('goal', 'Business project requiring team collaboration'),
                "objectives": ["Complete project objectives", "Deliver quality results"]
            })
            
            return result and result.get('success', False)
            
        except Exception as e:
            logger.error(f"Error creating basic agents: {e}")
            return False
    
    async def _reset_stuck_tasks(self, workspace_id: str) -> bool:
        """Reset tasks that are stuck in in_progress status"""
        try:
            # Find stuck tasks (in_progress for > 2 hours)
            tasks_response = supabase.table('tasks').select('*').eq('workspace_id', workspace_id).eq('status', 'in_progress').execute()
            
            reset_count = 0
            for task in tasks_response.data or []:
                created_at = datetime.fromisoformat(task['created_at'].replace('Z', '+00:00'))
                if datetime.now().replace(tzinfo=created_at.tzinfo) - created_at > timedelta(hours=2):
                    # Reset to pending
                    supabase.table('tasks').update({
                        'status': 'pending',
                        'updated_at': datetime.now().isoformat()
                    }).eq('id', task['id']).execute()
                    reset_count += 1
            
            logger.info(f"     Reset {reset_count} stuck tasks")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting stuck tasks: {e}")
            return False
    
    async def _mark_workspace_completed(self, workspace_id: str) -> bool:
        """Mark workspace as completed if all goals are done"""
        try:
            supabase.table('workspaces').update({
                'status': WorkspaceStatus.COMPLETED.value,
                'updated_at': datetime.now().isoformat()
            }).eq('id', workspace_id).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error marking workspace completed: {e}")
            return False
    
    async def _restart_goal_monitoring(self, workspace_id: str) -> bool:
        """Restart goal monitoring for the workspace"""
        try:
            # Simply mark workspace as active to restart monitoring
            supabase.table('workspaces').update({
                'status': WorkspaceStatus.ACTIVE.value,
                'updated_at': datetime.now().isoformat()
            }).eq('id', workspace_id).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error restarting goal monitoring: {e}")
            return False
    
    async def _mark_workspace_healthy(self, workspace_id: str) -> bool:
        """Mark workspace as healthy (active status)"""
        try:
            supabase.table('workspaces').update({
                'status': WorkspaceStatus.ACTIVE.value,
                'updated_at': datetime.now().isoformat()
            }).eq('id', workspace_id).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error marking workspace healthy: {e}")
            return False

async def main():
    """Main recovery function"""
    recovery_system = WorkspaceHealthRecovery()
    result = await recovery_system.diagnose_and_recover_workspaces()
    
    print("🏥 Workspace Health Recovery Complete!")
    print(f"Results: {result}")

if __name__ == "__main__":
    asyncio.run(main())