import asyncio
import logging
import os
from typing import List, Dict, Any, Optional, Union
from uuid import UUID
import json

from models import TaskStatus, Task, AgentStatus
from database import (
    list_tasks,
    update_task_status,
    update_agent_status,
    get_workspace,
    get_agent
)
from ai_agents.manager import AgentManager

logger = logging.getLogger(__name__)

class TaskExecutor:
    """Task Executor for running agent tasks asynchronously"""
    
    def __init__(self):
        """Initialize the task executor"""
        self.running = False
        self.workspace_managers = {}
    
    async def start(self):
        """Start the task executor"""
        if self.running:
            logger.warning("Task executor is already running")
            return
        
        self.running = True
        logger.info("Starting task executor")
        
        # Start the main execution loop
        asyncio.create_task(self.execution_loop())
    
    async def stop(self):
        """Stop the task executor"""
        if not self.running:
            logger.warning("Task executor is not running")
            return
        
        self.running = False
        logger.info("Stopping task executor")
    
    async def execution_loop(self):
        """Main execution loop for processing tasks"""
        while self.running:
            try:
                # Get pending tasks
                # In a real implementation, this would be more efficient
                # For example, using database subscriptions or message queues
                
                # For simplicity, we'll periodically check for pending tasks
                await self.process_pending_tasks()
                
                # Wait a bit before checking again
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Error in execution loop: {e}")
                # Wait a bit before retrying
                await asyncio.sleep(5)
    
    async def process_pending_tasks(self):
        """Process all pending tasks"""
        try:
            # In a real implementation, we would query the database for pending tasks
            # For now, we'll just log a message
            logger.info("Checking for pending tasks")
            
            # Placeholder implementation
            # In a real system, we would:
            # 1. Get all workspaces with pending tasks
            # 2. For each workspace, get or create an AgentManager
            # 3. Process tasks for that workspace
            
            # Placeholder for testing
            test_workspace_id = "00000000-0000-0000-0000-000000000000"
            test_task_id = "00000000-0000-0000-0000-000000000001"
            
            logger.info(f"Would process task {test_task_id} in workspace {test_workspace_id}")
            
            # In a real implementation, we would do something like:
            # await self.process_workspace_tasks(test_workspace_id)
        except Exception as e:
            logger.error(f"Error processing pending tasks: {e}")
    
    async def process_workspace_tasks(self, workspace_id: UUID):
        """
        Process tasks for a specific workspace.
        
        Args:
            workspace_id: The workspace ID
        """
        try:
            # Get or create agent manager for this workspace
            manager = await self.get_agent_manager(workspace_id)
            if not manager:
                logger.error(f"Failed to get agent manager for workspace {workspace_id}")
                return
            
            # Get pending tasks for this workspace
            tasks = await list_tasks(str(workspace_id))
            pending_tasks = [task for task in tasks if task["status"] == TaskStatus.PENDING.value]
            
            logger.info(f"Found {len(pending_tasks)} pending tasks for workspace {workspace_id}")
            
            # Process each pending task
            for task in pending_tasks:
                task_id = UUID(task["id"])
                await self.execute_task(manager, task_id)
        except Exception as e:
            logger.error(f"Error processing tasks for workspace {workspace_id}: {e}")
    
    async def get_agent_manager(self, workspace_id: UUID) -> Optional[AgentManager]:
        """
        Get or create an agent manager for a workspace.
        
        Args:
            workspace_id: The workspace ID
            
        Returns:
            AgentManager instance, or None if failed
        """
        # Check if we already have a manager for this workspace
        if workspace_id in self.workspace_managers:
            return self.workspace_managers[workspace_id]
        
        try:
            # Create a new manager
            manager = AgentManager(workspace_id)
            success = await manager.initialize()
            
            if success:
                self.workspace_managers[workspace_id] = manager
                return manager
            else:
                logger.error(f"Failed to initialize agent manager for workspace {workspace_id}")
                return None
        except Exception as e:
            logger.error(f"Error creating agent manager for workspace {workspace_id}: {e}")
            return None
    
    async def execute_task(self, manager: AgentManager, task_id: UUID):
        """
        Execute a specific task.
        
        Args:
            manager: The agent manager
            task_id: The task ID
        """
        try:
            logger.info(f"Executing task {task_id}")
            
            # Execute the task
            result = await manager.execute_task(task_id)
            
            logger.info(f"Task {task_id} completed with result: {json.dumps(result)}")
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {e}")

# Singleton instance
task_executor = TaskExecutor()

# Function to start the executor
async def start_task_executor():
    await task_executor.start()

# Function to stop the executor
async def stop_task_executor():
    await task_executor.stop()