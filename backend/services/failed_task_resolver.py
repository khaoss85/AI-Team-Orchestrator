#!/usr/bin/env python3
"""
🔧 FAILED TASK RESOLVER INTEGRATION
Integrates AutonomousTaskRecovery with the TaskExecutor system
to provide seamless automatic recovery of failed tasks
"""

import logging
import asyncio
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum

from database import (
    list_tasks,
    get_task,
    update_task_fields,
    update_workspace_status,
    get_workspace
)
from models import TaskStatus, WorkspaceStatus
from services.autonomous_task_recovery import (
    autonomous_task_recovery,
    auto_recover_workspace_tasks,
    auto_recover_single_task,
    RecoveryStrategy
)

logger = logging.getLogger(__name__)

class FailedTaskResolver:
    """
    🎯 MAIN CLASS: Integrates autonomous task recovery with executor system
    Provides seamless recovery of failed tasks without human intervention
    """
    
    def __init__(self):
        self.enable_auto_recovery = os.getenv('ENABLE_AUTO_TASK_RECOVERY', 'true').lower() == 'true'
        self.recovery_batch_size = int(os.getenv('RECOVERY_BATCH_SIZE', '5'))
        self.recovery_check_interval = int(os.getenv('RECOVERY_CHECK_INTERVAL_SECONDS', '60'))
        
        logger.info(f"✅ FailedTaskResolver initialized - Auto-recovery: {self.enable_auto_recovery}")
    
    async def handle_task_failure(self, task_id: str, error_message: str) -> Dict[str, Any]:
        """
        🚨 HOOK: Called by executor when a task fails
        Immediately attempts autonomous recovery
        """
        if not self.enable_auto_recovery:
            logger.info(f"Auto-recovery disabled for task {task_id}")
            return {'recovery_attempted': False, 'reason': 'auto_recovery_disabled'}
        
        try:
            logger.info(f"🔧 TASK FAILURE HANDLER: Processing failed task {task_id}")
            
            # Get task details for analysis
            task = await get_task(task_id)
            if not task:
                logger.error(f"❌ Failed task {task_id} not found in database")
                return {'recovery_attempted': False, 'error': 'task_not_found'}
            
            workspace_id = task.get('workspace_id')
            retry_count = task.get('retry_count', 0)
            
            # Check if task qualifies for immediate recovery
            if await self._should_attempt_immediate_recovery(task, error_message):
                logger.info(f"🤖 IMMEDIATE RECOVERY: Attempting autonomous recovery for task {task_id}")
                
                recovery_result = await auto_recover_single_task(task_id)
                
                if recovery_result.get('success'):
                    logger.info(f"✅ IMMEDIATE RECOVERY: Successfully recovered task {task_id}")
                    
                    # Update workspace status to reflect recovery
                    await self._update_workspace_recovery_status(workspace_id, 'task_recovered')
                    
                    return {
                        'recovery_attempted': True,
                        'immediate_recovery': True,
                        'success': True,
                        'recovery_strategy': recovery_result.get('strategy'),
                        'action_taken': recovery_result.get('action')
                    }
                else:
                    logger.warning(f"⚠️ IMMEDIATE RECOVERY: Failed to recover task {task_id}, will try batch recovery")
                    
                    # Schedule for batch recovery
                    await self._schedule_for_batch_recovery(task_id, workspace_id)
                    
                    return {
                        'recovery_attempted': True,
                        'immediate_recovery': False,
                        'scheduled_for_batch': True,
                        'error': recovery_result.get('error')
                    }
            else:
                logger.info(f"🕒 DELAYED RECOVERY: Scheduling task {task_id} for batch recovery")
                
                await self._schedule_for_batch_recovery(task_id, workspace_id)
                
                return {
                    'recovery_attempted': True,
                    'immediate_recovery': False,
                    'scheduled_for_batch': True,
                    'reason': 'delayed_recovery_strategy'
                }
                
        except Exception as e:
            logger.error(f"❌ Error in task failure handler for {task_id}: {e}")
            return {'recovery_attempted': False, 'error': str(e)}
    
    async def process_workspace_recovery_batch(self, workspace_id: str) -> Dict[str, Any]:
        """
        🔄 BATCH PROCESSING: Process all failed tasks in a workspace
        Called by scheduler or manual trigger
        """
        try:
            logger.info(f"🔄 BATCH RECOVERY: Processing workspace {workspace_id}")
            
            # Trigger comprehensive workspace recovery
            recovery_result = await auto_recover_workspace_tasks(workspace_id)
            
            if recovery_result.get('success'):
                successful_recoveries = recovery_result.get('successful_recoveries', 0)
                total_failed = recovery_result.get('total_failed_tasks', 0)
                
                logger.info(f"✅ BATCH RECOVERY: Completed {successful_recoveries}/{total_failed} recoveries in workspace {workspace_id}")
                
                # Update workspace status based on recovery success
                if successful_recoveries == total_failed and total_failed > 0:
                    await update_workspace_status(workspace_id, WorkspaceStatus.ACTIVE.value)
                elif successful_recoveries > 0:
                    await update_workspace_status(workspace_id, WorkspaceStatus.DEGRADED_MODE.value)
                else:
                    await update_workspace_status(workspace_id, WorkspaceStatus.AUTO_RECOVERING.value)
                
                return {
                    'success': True,
                    'workspace_id': workspace_id,
                    'total_processed': total_failed,
                    'successful_recoveries': successful_recoveries,
                    'recovery_rate': recovery_result.get('recovery_rate', 0.0),
                    'batch_processing': True
                }
            else:
                logger.error(f"❌ BATCH RECOVERY: Failed for workspace {workspace_id}")
                return {
                    'success': False,
                    'workspace_id': workspace_id,
                    'error': recovery_result.get('error'),
                    'batch_processing': True
                }
                
        except Exception as e:
            logger.error(f"❌ Error in batch recovery for workspace {workspace_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def start_recovery_scheduler(self):
        """
        🕐 SCHEDULER: Background task to periodically check for failed tasks
        Runs autonomous recovery on a schedule
        """
        if not self.enable_auto_recovery:
            logger.info("Recovery scheduler disabled")
            return
        
        logger.info(f"🕐 RECOVERY SCHEDULER: Starting with {self.recovery_check_interval}s interval")
        
        while True:
            try:
                await asyncio.sleep(self.recovery_check_interval)
                await self._periodic_recovery_check()
                
            except asyncio.CancelledError:
                logger.info("Recovery scheduler cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Error in recovery scheduler: {e}")
                await asyncio.sleep(30)  # Short delay before retry
    
    async def _periodic_recovery_check(self):
        """
        🔍 PERIODIC CHECK: Find workspaces with failed tasks and recover them
        """
        try:
            # Find workspaces that need recovery
            workspaces_needing_recovery = await self._find_workspaces_needing_recovery()
            
            if not workspaces_needing_recovery:
                logger.debug("🔍 PERIODIC CHECK: No workspaces need recovery")
                return
            
            logger.info(f"🔍 PERIODIC CHECK: Found {len(workspaces_needing_recovery)} workspaces needing recovery")
            
            # Process each workspace
            recovery_tasks = []
            for workspace_id in workspaces_needing_recovery:
                recovery_tasks.append(self.process_workspace_recovery_batch(workspace_id))
            
            # Execute recoveries concurrently
            results = await asyncio.gather(*recovery_tasks, return_exceptions=True)
            
            successful_workspaces = 0
            for i, result in enumerate(results):
                workspace_id = workspaces_needing_recovery[i]
                
                if isinstance(result, Exception):
                    logger.error(f"❌ Recovery failed for workspace {workspace_id}: {result}")
                elif result.get('success'):
                    successful_workspaces += 1
                    logger.info(f"✅ Recovery completed for workspace {workspace_id}")
            
            logger.info(f"🎊 PERIODIC RECOVERY: Completed {successful_workspaces}/{len(workspaces_needing_recovery)} workspace recoveries")
            
        except Exception as e:
            logger.error(f"❌ Error in periodic recovery check: {e}")
    
    async def _should_attempt_immediate_recovery(self, task: Dict[str, Any], error_message: str) -> bool:
        """
        🤔 DECISION: Determine if task should be immediately recovered or batched
        """
        try:
            retry_count = task.get('retry_count', 0)
            error_lower = error_message.lower()
            
            # Immediate recovery conditions
            if retry_count == 0:  # First failure
                return True
            
            if any(keyword in error_lower for keyword in ['timeout', 'connection', 'rate_limit']):
                return True
            
            # Guardrail failures should be immediately retried with different approach
            if any(keyword in error_lower for keyword in ['guardrail', 'tripwire', 'validation']):
                logger.info(f"🛡️ Guardrail failure detected for task {task.get('id')} - triggering immediate recovery")
                return True
            
            if 'agent' in error_lower and retry_count < 2:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error determining recovery strategy: {e}")
            return False  # Default to batch processing
    
    async def _schedule_for_batch_recovery(self, task_id: str, workspace_id: str):
        """
        📅 SCHEDULE: Mark task for batch recovery processing
        """
        try:
            await update_task_fields(task_id, {
                'metadata': {
                    'scheduled_for_recovery': True,
                    'recovery_scheduled_at': datetime.utcnow().isoformat(),
                    'recovery_method': 'batch_processing'
                }
            })
            
            logger.info(f"📅 SCHEDULED: Task {task_id} marked for batch recovery")
            
        except Exception as e:
            logger.error(f"❌ Error scheduling task {task_id} for recovery: {e}")
    
    async def _find_workspaces_needing_recovery(self) -> List[str]:
        """
        🔎 DISCOVERY: Find workspaces with failed tasks that need recovery
        """
        try:
            # 🔧 FIXED: Import function and handle database response properly
            from database import get_active_workspaces
            
            workspaces_result = await get_active_workspaces()
            
            # Handle both dict and list responses from database
            if isinstance(workspaces_result, dict):
                workspaces = workspaces_result.get('workspaces', [])
            elif isinstance(workspaces_result, list):
                workspaces = workspaces_result
            else:
                logger.warning(f"⚠️ Unexpected workspace result type: {type(workspaces_result)}")
                return []
            
            workspaces_with_failures = []
            
            for workspace in workspaces:
                # 🔧 FIXED: Ensure workspace is a dict before accessing attributes
                if isinstance(workspace, str):
                    # If workspace is just an ID string, use it directly
                    workspace_id = workspace
                    status = None
                elif isinstance(workspace, dict):
                    workspace_id = workspace.get('id')
                    status = workspace.get('status')
                else:
                    logger.warning(f"⚠️ Unexpected workspace type: {type(workspace)}")
                    continue
                
                if not workspace_id:
                    continue
                
                # Check if workspace needs recovery based on status
                if status and status in [WorkspaceStatus.AUTO_RECOVERING.value, WorkspaceStatus.DEGRADED_MODE.value]:
                    workspaces_with_failures.append(workspace_id)
                elif not status or status == WorkspaceStatus.ACTIVE.value:
                    # Check if there are failed tasks - this is the main check
                    try:
                        tasks = await list_tasks(workspace_id)
                        failed_tasks = [t for t in tasks if isinstance(t, dict) and t.get('status') == TaskStatus.FAILED.value]
                        
                        if failed_tasks:
                            workspaces_with_failures.append(workspace_id)
                            logger.info(f"🔍 Found {len(failed_tasks)} failed tasks in workspace {workspace_id}")
                    except Exception as task_error:
                        logger.error(f"❌ Error checking tasks for workspace {workspace_id}: {task_error}")
                        continue
            
            logger.info(f"🔍 DISCOVERY: Found {len(workspaces_with_failures)} workspaces needing recovery")
            return workspaces_with_failures
            
        except Exception as e:
            logger.error(f"❌ Error finding workspaces needing recovery: {e}")
            # 🔧 GRACEFUL FALLBACK: Return empty list instead of crashing
            return []
    
    async def _update_workspace_recovery_status(self, workspace_id: str, recovery_event: str):
        """
        📊 STATUS UPDATE: Update workspace status based on recovery events
        """
        try:
            workspace = await get_workspace(workspace_id)
            if not workspace:
                return
            
            current_status = workspace.get('status')
            
            # Determine new status based on recovery event
            if recovery_event == 'task_recovered' and current_status == WorkspaceStatus.DEGRADED_MODE.value:
                # Check if all tasks are now healthy
                tasks = await list_tasks(workspace_id)
                failed_tasks = [t for t in tasks if t.get('status') == TaskStatus.FAILED.value]
                
                if not failed_tasks:
                    await update_workspace_status(workspace_id, WorkspaceStatus.ACTIVE.value)
                    logger.info(f"✅ WORKSPACE RECOVERED: {workspace_id} restored to ACTIVE status")
            
        except Exception as e:
            logger.error(f"❌ Error updating workspace recovery status: {e}")

# Global singleton instance
failed_task_resolver = FailedTaskResolver()

# Convenience functions for executor integration
async def handle_executor_task_failure(task_id: str, error_message: str) -> Dict[str, Any]:
    """Main function called by executor when a task fails"""
    return await failed_task_resolver.handle_task_failure(task_id, error_message)

async def process_workspace_failed_tasks(workspace_id: str) -> Dict[str, Any]:
    """Process all failed tasks in a workspace"""
    return await failed_task_resolver.process_workspace_recovery_batch(workspace_id)

async def start_autonomous_recovery_scheduler():
    """Start the background recovery scheduler"""
    return await failed_task_resolver.start_recovery_scheduler()

# Export
__all__ = [
    "FailedTaskResolver",
    "failed_task_resolver",
    "handle_executor_task_failure",
    "process_workspace_failed_tasks", 
    "start_autonomous_recovery_scheduler"
]