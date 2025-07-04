
import logging
import asyncio
from typing import Dict, Any, List, Optional
from uuid import UUID
from database import (
    get_workspace_goals, update_task_status, update_goal_progress, get_task, 
    get_active_workspaces, supabase, create_task
)
from goal_driven_task_planner import goal_driven_task_planner
from quality_gate import QualityGate
from datetime import datetime

logger = logging.getLogger(__name__)

class WorkflowOrchestrator:
    def __init__(self):
        self.quality_gate = QualityGate()
        self.supabase = supabase
        self._running = False

    async def process_workspace(self, workspace_id: str):
        """Orchestrates the entire workflow for a workspace."""
        logger.info(f"Orchestrating workflow for workspace {workspace_id}")
        goals = await get_workspace_goals(workspace_id)
        for goal in goals:
            if goal['status'] == 'completed':
                continue

            tasks_to_execute = await goal_driven_task_planner.plan_tasks_for_goal(goal, workspace_id)
            for task_data in tasks_to_execute:
                # Create task in database
                await create_task(
                    workspace_id=workspace_id,
                    goal_id=goal['id'],
                    **task_data
                )
                
                # Create integration event for task creation
                await self._create_integration_event(
                    workspace_id=workspace_id,
                    event_type='task_created',
                    source_component='workflow_orchestrator',
                    target_component='executor',
                    event_data={'task_data': task_data, 'goal_id': str(goal['id'])}
                )

        # Monitor task completion and update goals
        await self._monitor_and_update_goals(workspace_id, goals)

    async def _monitor_and_update_goals(self, workspace_id: str, goals: List[Dict[str, Any]]):
        logger.info(f"Monitoring task completion for workspace {workspace_id}")
        while True:
            all_goals_completed = True
            for goal in goals:
                # Refresh goal status from DB to ensure up-to-date info
                updated_goal = await get_task(goal['id']) # Assuming get_task can get goal by ID
                if updated_goal and updated_goal.get('status') != 'completed':
                    all_goals_completed = False
                    break
            if all_goals_completed:
                logger.info(f"All goals completed for workspace {workspace_id}")
                break

            # Check for task completion events
            events = await self._get_pending_events(workspace_id, 'task_completed')
            completed_tasks_ids = [event['event_data'].get('task_id') for event in events if event['event_data'].get('task_id')]
            for task_id in completed_tasks_ids:
                task = await get_task(task_id)
                if task and task['status'] == 'completed': # Ensure task is actually completed by executor
                    asset = task.get('result', {})
                    goal = next((g for g in goals if g['id'] == task['goal_id']), None)
                    if goal:
                        assessment = await self.quality_gate.validate_asset(asset, goal)
                        if assessment.passes_quality_gate:
                            # Task status already updated by executor, just update goal progress
                            await update_goal_progress(goal['id'], task['contribution_expected'])
                            logger.info(f"Task {task['name']} completed and goal progress updated.")
                        else:
                            # If quality fails, mark task for revision (executor might have marked it completed)
                            await update_task_status(task['id'], 'needs_revision', {'quality_assessment': assessment.dict()})
                            logger.warning(f"Task {task['name']} failed quality gate and marked for revision.")
            await asyncio.sleep(10) # Poll every 10 seconds

    async def _create_integration_event(self, workspace_id: str, event_type: str, 
                                       source_component: str, target_component: str = None,
                                       event_data: Dict[str, Any] = None):
        """Create an integration event for event-driven coordination"""
        try:
            event = {
                'workspace_id': workspace_id,
                'event_type': event_type,
                'source_component': source_component,
                'target_component': target_component,
                'event_data': event_data or {}
            }
            
            result = self.supabase.table('integration_events').insert(event).execute()
            logger.info(f"Created integration event: {event_type} from {source_component}")
            
            # Update component health
            await self._update_component_health('workflow_orchestrator', 'healthy')
            
        except Exception as e:
            logger.error(f"Failed to create integration event: {e}")
            await self._update_component_health('workflow_orchestrator', 'degraded', str(e))
    
    async def _get_pending_events(self, workspace_id: str, event_type: str = None) -> List[Dict]:
        """Get pending events for a workspace"""
        try:
            query = self.supabase.table('integration_events').select('*').eq('workspace_id', workspace_id).eq('status', 'pending')
            if event_type:
                query = query.eq('event_type', event_type)
            
            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Failed to fetch pending events: {e}")
            return []
    
    async def _update_component_health(self, component_name: str, status: str, error: str = None):
        """Update component health status"""
        try:
            health_data = {
                'status': status,
                'last_heartbeat': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            if error:
                health_data['last_error'] = error
                health_data['error_count'] = self.supabase.table('component_health').select('error_count').eq('component_name', component_name).execute().data[0]['error_count'] + 1
            
            self.supabase.table('component_health').update(health_data).eq('component_name', component_name).execute()
        except Exception as e:
            logger.error(f"Failed to update component health: {e}")
    
    async def start(self):
        """Start the workflow orchestrator"""
        self._running = True
        logger.info("Starting Workflow Orchestrator...")
        
        # Update component health
        await self._update_component_health('workflow_orchestrator', 'healthy')
        
        while self._running:
            try:
                # Get active workspaces
                active_workspaces = await get_active_workspaces()
                
                for workspace_id in active_workspaces:
                    await self.process_workspace(str(workspace_id))
                
                await asyncio.sleep(30)  # Process every 30 seconds
                
            except Exception as e:
                logger.error(f"Orchestrator error: {e}")
                await self._update_component_health('workflow_orchestrator', 'error', str(e))
                await asyncio.sleep(60)  # Wait longer on error
    
    async def stop(self):
        """Stop the workflow orchestrator"""
        self._running = False
        await self._update_component_health('workflow_orchestrator', 'stopped')

workflow_orchestrator = WorkflowOrchestrator()
