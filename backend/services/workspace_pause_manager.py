"""
🤖 AI-Driven Workspace Pause Manager
Intelligent management of workspace pause/resume logic to prevent task stalls
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

from database import supabase, get_workspaces_with_pending_tasks, get_active_workspaces
from models import WorkspaceStatus

logger = logging.getLogger(__name__)

@dataclass
class WorkspacePauseInfo:
    """Information about a paused workspace"""
    workspace_id: str
    pause_reason: str
    paused_at: datetime
    pending_tasks_count: int
    critical_tasks_count: int
    auto_recovery_eligible: bool
    recovery_score: float

class WorkspacePauseManager:
    """
    🤖 AI-DRIVEN: Intelligent workspace pause/resume management
    Pillar 4: Scalable & auto-apprendente
    Pillar 12: Automatic Course-Correction
    """
    
    def __init__(self):
        self.paused_workspaces: Dict[str, WorkspacePauseInfo] = {}
        self.auto_recovery_enabled = True
        self.recovery_check_interval = 300  # 5 minutes
        self.last_recovery_check = None
        
        # Recovery thresholds
        self.max_pause_duration_hours = 2.0  # Auto-recovery after 2 hours max
        self.critical_task_recovery_threshold = 3  # Recovery if 3+ critical tasks
        self.pending_task_recovery_threshold = 10  # Recovery if 10+ pending tasks
        
        logger.info("🤖 WorkspacePauseManager initialized with AI-driven recovery")
    
    async def should_allow_critical_bypass(self, workspace_id: str) -> bool:
        """
        🤖 AI-DRIVEN: Determine if critical tasks should bypass workspace pause
        """
        try:
            # Always allow critical task bypass for paused workspaces
            if await self._is_workspace_paused(workspace_id):
                # Check if there are critical corrective tasks
                critical_count = await self._count_critical_tasks(workspace_id)
                if critical_count > 0:
                    logger.info(f"🚨 CRITICAL BYPASS: W:{workspace_id[:8]} has {critical_count} critical tasks - allowing bypass of pause")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking critical bypass for workspace {workspace_id}: {e}")
            return False
    
    async def _is_workspace_paused(self, workspace_id: str) -> bool:
        """Check if workspace is currently paused"""
        try:
            result = supabase.table('workspaces').select('status').eq('id', workspace_id).execute()
            if result.data:
                return result.data[0].get('status') == WorkspaceStatus.PAUSED.value
            return False
        except Exception as e:
            logger.warning(f"Error checking workspace pause status: {e}")
            return False
    
    async def _count_critical_tasks(self, workspace_id: str) -> int:
        """Count critical tasks in a workspace"""
        try:
            # Get pending tasks
            pending_response = supabase.table('tasks').select('*').eq('workspace_id', workspace_id).eq('status', 'pending').execute()
            pending_tasks = pending_response.data or []
            
            critical_count = 0
            for task in pending_tasks:
                if await self._is_task_critical(task):
                    critical_count += 1
            
            return critical_count
            
        except Exception as e:
            logger.warning(f"Error counting critical tasks: {e}")
            return 0
    
    async def _is_task_critical(self, task: Dict) -> bool:
        """Determine if a task is critical (reuse logic from executor)"""
        try:
            task_name = task.get("name", "").lower()
            task_description = task.get("description", "").lower()
            context_data = task.get("context_data", {}) or {}
            
            # Check goal-driven corrective tasks
            is_goal_driven = context_data.get("is_goal_driven_task", False)
            task_type = context_data.get("task_type", "").lower()
            
            if is_goal_driven and "corrective" in task_type:
                return True
            
            # Check URGENT patterns
            urgent_patterns = [
                "urgent: close", "urgent:", "% gap", "critical gap",
                "emergency:", "immediate:", "critical", "urgent",
                "deliverable creation", "deliverable", "fix", "repair"
            ]
            
            combined_text = f"{task_name} {task_description}"
            for pattern in urgent_patterns:
                if pattern in combined_text:
                    return True
            
            # Check priority and recency
            priority = task.get("priority", "medium").lower()
            if priority == "high":
                created_at = task.get("created_at")
                if created_at:
                    try:
                        created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        if datetime.now().replace(tzinfo=created_time.tzinfo) - created_time < timedelta(hours=2):
                            return True
                    except:
                        pass
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking if task is critical: {e}")
            return False
    
    async def get_intelligent_workspaces_with_pending_tasks(self) -> List[str]:
        """
        🤖 AI-DRIVEN: Enhanced version of get_workspaces_with_pending_tasks 
        that allows critical task bypass for paused workspaces
        """
        try:
            # Get all workspaces with pending tasks (including paused ones)
            result = supabase.table("tasks").select("workspace_id, workspaces!inner(id, status)").eq("status", "pending").execute()
            
            if not result.data:
                return []
            
            # Analyze each workspace
            active_workspace_ids = []
            paused_with_critical = []
            total_paused_count = 0
            
            workspace_groups = {}
            for task in result.data:
                workspace_id = task["workspace_id"]
                workspace = task.get("workspaces")
                
                if workspace_id not in workspace_groups:
                    workspace_groups[workspace_id] = {
                        "status": workspace.get("status") if workspace else "unknown",
                        "task_count": 0
                    }
                workspace_groups[workspace_id]["task_count"] += 1
            
            # Process each workspace
            for workspace_id, info in workspace_groups.items():
                if info["status"] != "paused":
                    # Normal active workspace
                    active_workspace_ids.append(workspace_id)
                else:
                    # Paused workspace - check if it has critical tasks
                    total_paused_count += info["task_count"]
                    
                    if await self.should_allow_critical_bypass(workspace_id):
                        active_workspace_ids.append(workspace_id)
                        paused_with_critical.append(workspace_id)
                        logger.info(f"🚨 CRITICAL BYPASS: Allowing paused workspace W:{workspace_id[:8]} due to critical tasks")
            
            # Remove duplicates
            unique_workspace_ids = list(set(active_workspace_ids))
            
            # Enhanced logging
            if total_paused_count > 0:
                bypassed_count = len(paused_with_critical)
                actual_skipped = total_paused_count - bypassed_count
                
                if actual_skipped > 0:
                    logger.warning(f"⏸️ Skipped {actual_skipped} tasks from paused workspaces (bypassed {bypassed_count} critical)")
                
                if bypassed_count > 0:
                    logger.info(f"🚨 CRITICAL BYPASS: Allowed {bypassed_count} paused workspaces with critical tasks: {[ws[:8] for ws in paused_with_critical]}")
            
            # Trigger recovery check for paused workspaces
            if total_paused_count > 50:  # Many paused tasks - trigger recovery
                asyncio.create_task(self.check_and_recover_paused_workspaces())
            
            return unique_workspace_ids
            
        except Exception as e:
            logger.error(f"Error getting intelligent workspaces with pending tasks: {e}")
            # Fallback to original logic
            return await get_workspaces_with_pending_tasks()
    
    async def check_and_recover_paused_workspaces(self):
        """
        🤖 AI-DRIVEN: Intelligent recovery of paused workspaces
        """
        try:
            logger.info("🔄 Starting intelligent workspace recovery check...")
            
            # Get all paused workspaces
            result = supabase.table('workspaces').select('*').eq('status', WorkspaceStatus.PAUSED.value).execute()
            paused_workspaces = result.data or []
            
            if not paused_workspaces:
                logger.info("No paused workspaces found")
                return
            
            recovery_candidates = []
            
            for workspace in paused_workspaces:
                workspace_id = workspace['id']
                
                # Analyze workspace for recovery eligibility
                recovery_info = await self._analyze_workspace_recovery(workspace)
                
                if recovery_info.auto_recovery_eligible:
                    recovery_candidates.append(recovery_info)
            
            # Sort by recovery score (highest first)
            recovery_candidates.sort(key=lambda x: x.recovery_score, reverse=True)
            
            # Recover top candidates
            recovered_count = 0
            for candidate in recovery_candidates[:5]:  # Max 5 at once
                success = await self._recover_workspace(candidate)
                if success:
                    recovered_count += 1
            
            if recovered_count > 0:
                logger.info(f"✅ Recovered {recovered_count} paused workspaces intelligently")
            else:
                logger.info("No workspaces qualified for auto-recovery")
            
        except Exception as e:
            logger.error(f"Error in intelligent workspace recovery: {e}")
    
    async def _analyze_workspace_recovery(self, workspace: Dict) -> WorkspacePauseInfo:
        """Analyze if a workspace is eligible for auto-recovery"""
        try:
            workspace_id = workspace['id']
            
            # Get pause information
            paused_at_str = workspace.get('updated_at', datetime.now().isoformat())
            try:
                paused_at = datetime.fromisoformat(paused_at_str.replace('Z', '+00:00'))
            except:
                paused_at = datetime.now().replace(tzinfo=None)
            
            pause_duration = datetime.now().replace(tzinfo=paused_at.tzinfo) - paused_at
            
            # Count pending and critical tasks
            pending_count = await self._count_pending_tasks(workspace_id)
            critical_count = await self._count_critical_tasks(workspace_id)
            
            # Determine recovery eligibility
            auto_recovery_eligible = False
            recovery_score = 0.0
            
            # Rule 1: Max pause duration exceeded
            if pause_duration.total_seconds() > (self.max_pause_duration_hours * 3600):
                auto_recovery_eligible = True
                recovery_score += 50.0
                logger.info(f"Recovery candidate W:{workspace_id[:8]}: Max pause duration exceeded ({pause_duration.total_seconds()/3600:.1f}h)")
            
            # Rule 2: Critical tasks present
            if critical_count >= self.critical_task_recovery_threshold:
                auto_recovery_eligible = True
                recovery_score += 40.0 + (critical_count * 5)
                logger.info(f"Recovery candidate W:{workspace_id[:8]}: {critical_count} critical tasks")
            
            # Rule 3: High pending task count
            if pending_count >= self.pending_task_recovery_threshold:
                auto_recovery_eligible = True
                recovery_score += 30.0 + min(pending_count, 50)
                logger.info(f"Recovery candidate W:{workspace_id[:8]}: {pending_count} pending tasks")
            
            # Rule 4: Goal completion potential
            completed_goals = await self._count_completed_goals(workspace_id)
            if completed_goals > 0 and pending_count > 0:
                auto_recovery_eligible = True
                recovery_score += 25.0
                logger.info(f"Recovery candidate W:{workspace_id[:8]}: {completed_goals} completed goals with pending work")
            
            pause_reason = workspace.get('status_reason', 'Unknown pause reason')
            
            return WorkspacePauseInfo(
                workspace_id=workspace_id,
                pause_reason=pause_reason,
                paused_at=paused_at,
                pending_tasks_count=pending_count,
                critical_tasks_count=critical_count,
                auto_recovery_eligible=auto_recovery_eligible,
                recovery_score=recovery_score
            )
            
        except Exception as e:
            logger.error(f"Error analyzing workspace recovery for {workspace.get('id', 'unknown')}: {e}")
            return WorkspacePauseInfo(
                workspace_id=workspace.get('id', 'unknown'),
                pause_reason="Analysis error",
                paused_at=datetime.now(),
                pending_tasks_count=0,
                critical_tasks_count=0,
                auto_recovery_eligible=False,
                recovery_score=0.0
            )
    
    async def _count_pending_tasks(self, workspace_id: str) -> int:
        """Count pending tasks in workspace"""
        try:
            result = supabase.table('tasks').select('id', count='exact').eq('workspace_id', workspace_id).eq('status', 'pending').execute()
            return result.count or 0
        except Exception as e:
            logger.warning(f"Error counting pending tasks: {e}")
            return 0
    
    async def _count_completed_goals(self, workspace_id: str) -> int:
        """Count completed goals in workspace"""
        try:
            result = supabase.table('workspace_goals').select('*').eq('workspace_id', workspace_id).execute()
            goals = result.data or []
            
            completed_count = 0
            for goal in goals:
                current_value = goal.get('current_value', 0)
                target_value = goal.get('target_value', 1)
                if current_value >= target_value:
                    completed_count += 1
            
            return completed_count
        except Exception as e:
            logger.warning(f"Error counting completed goals: {e}")
            return 0
    
    async def _recover_workspace(self, recovery_info: WorkspacePauseInfo) -> bool:
        """Recover a paused workspace"""
        try:
            workspace_id = recovery_info.workspace_id
            
            # Update workspace status to active
            update_data = {
                "status": WorkspaceStatus.ACTIVE.value,
                "updated_at": datetime.now().isoformat()
            }
            
            # Add recovery reason if possible
            try:
                update_data["status_reason"] = f"Auto-recovered: {recovery_info.critical_tasks_count} critical, {recovery_info.pending_tasks_count} pending (score: {recovery_info.recovery_score:.1f})"
            except:
                pass
            
            result = supabase.table('workspaces').update(update_data).eq('id', workspace_id).execute()
            
            if result.data:
                logger.info(f"✅ Recovered workspace W:{workspace_id[:8]} - Score: {recovery_info.recovery_score:.1f}, Critical: {recovery_info.critical_tasks_count}, Pending: {recovery_info.pending_tasks_count}")
                return True
            else:
                logger.warning(f"Failed to recover workspace {workspace_id} - no data returned")
                return False
            
        except Exception as e:
            logger.error(f"Error recovering workspace {recovery_info.workspace_id}: {e}")
            return False
    
    async def get_pause_status_report(self) -> Dict:
        """Get comprehensive pause status report"""
        try:
            # Get paused workspaces
            result = supabase.table('workspaces').select('*').eq('status', WorkspaceStatus.PAUSED.value).execute()
            paused_workspaces = result.data or []
            
            # Analyze each
            report = {
                "total_paused": len(paused_workspaces),
                "recovery_candidates": [],
                "high_priority_recoveries": [],
                "total_paused_tasks": 0,
                "total_critical_tasks_paused": 0
            }
            
            for workspace in paused_workspaces:
                analysis = await self._analyze_workspace_recovery(workspace)
                
                report["total_paused_tasks"] += analysis.pending_tasks_count
                report["total_critical_tasks_paused"] += analysis.critical_tasks_count
                
                if analysis.auto_recovery_eligible:
                    report["recovery_candidates"].append({
                        "workspace_id": analysis.workspace_id,
                        "recovery_score": analysis.recovery_score,
                        "critical_tasks": analysis.critical_tasks_count,
                        "pending_tasks": analysis.pending_tasks_count,
                        "pause_reason": analysis.pause_reason
                    })
                    
                    if analysis.recovery_score > 70:
                        report["high_priority_recoveries"].append(analysis.workspace_id)
            
            # Sort recovery candidates by score
            report["recovery_candidates"].sort(key=lambda x: x["recovery_score"], reverse=True)
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating pause status report: {e}")
            return {"error": str(e)}

# Global instance
workspace_pause_manager = WorkspacePauseManager()

# Export for easy import
__all__ = ["WorkspacePauseManager", "workspace_pause_manager", "WorkspacePauseInfo"]