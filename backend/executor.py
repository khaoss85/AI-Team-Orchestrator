import asyncio
import logging
import os
from typing import List, Dict, Any, Optional, Union
from uuid import UUID, uuid4
import json
from datetime import datetime, timedelta
import time

from models import TaskStatus, Task, AgentStatus, WorkspaceStatus
from database import (
    list_tasks,
    update_task_status,
    update_agent_status,
    get_workspace,
    get_agent,
    list_agents as db_list_agents,
    create_task,
    get_active_workspaces,
    get_workspaces_with_pending_tasks,
    update_workspace_status
)
from ai_agents.manager import AgentManager
from task_analyzer import AutoTaskGenerator, EnhancedTaskExecutor, TaskAnalysisResult

logger = logging.getLogger(__name__)

class BudgetTracker:
    """Tracks budget usage for agents"""
    
    def __init__(self):
        self.usage_log = {}  # agent_id -> list of usage records
        
        # Token costs per model (per 1K tokens)
        self.token_costs = {
            "gpt-4.1": {
                "input": 0.03,
                "output": 0.06
            },
            "gpt-4.1-mini": {
                "input": 0.015,
                "output": 0.03
            },
            "gpt-4.1-nano": {
                "input": 0.01,
                "output": 0.02
            },
            "gpt-4-turbo": {
                "input": 0.02,
                "output": 0.04
            }
        }
    
    def log_usage(self, agent_id: str, model: str, input_tokens: int, output_tokens: int, task_id: Optional[str] = None):
        """Log token usage for an agent"""
        if agent_id not in self.usage_log:
            self.usage_log[agent_id] = []
        
        costs = self.token_costs.get(model, self.token_costs["gpt-4.1-mini"])
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]
        total_cost = input_cost + output_cost
        
        usage_record = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(total_cost, 6)
        }
        
        self.usage_log[agent_id].append(usage_record)
        logger.info(f"Budget usage - Agent {agent_id}: ${total_cost:.6f} ({input_tokens} in + {output_tokens} out tokens)")
        
        return usage_record
    
    def get_agent_total_cost(self, agent_id: str) -> float:
        """Get total cost for an agent"""
        if agent_id not in self.usage_log:
            return 0.0
        return sum(record["total_cost"] for record in self.usage_log[agent_id])
    
    def get_workspace_total_cost(self, workspace_id: str, agent_ids: List[str]) -> Dict[str, Any]:
        """Get total cost for a workspace"""
        total_cost = 0.0
        agent_costs = {}
        total_tokens = {"input": 0, "output": 0}
        
        for agent_id in agent_ids:
            agent_cost = self.get_agent_total_cost(agent_id)
            agent_costs[agent_id] = agent_cost
            total_cost += agent_cost
            
            if agent_id in self.usage_log:
                for record in self.usage_log[agent_id]:
                    total_tokens["input"] += record["input_tokens"]
                    total_tokens["output"] += record["output_tokens"]
        
        return {
            "total_cost": round(total_cost, 6),
            "agent_costs": agent_costs,
            "total_tokens": total_tokens,
            "currency": "USD"
        }

class TaskExecutor:
    """Enhanced Task Executor with budget tracking and auto-start"""
    
    def __init__(self):
        """Initialize the task executor"""
        self.running = False
        self.workspace_managers = {}
        self.budget_tracker = BudgetTracker()
        self.execution_log = []  # Store execution history
    
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
                # Process pending tasks from all workspaces
                await self.process_all_pending_tasks()
                
                # Check for workspaces that need initial task creation
                await self.check_for_new_workspaces()
                
                # Wait before next cycle
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in execution loop: {e}")
                await asyncio.sleep(5)
    
    async def check_for_new_workspaces(self):
        """Check for workspaces that need initial tasks"""
        try:
            # Get workspaces that are active but have no tasks
            # This would need a proper database query
            logger.info("Checking for workspaces needing initial tasks")
            
            # Placeholder implementation
            # In a real system, you'd query for workspaces with status='active' 
            # that don't have any tasks yet
            
        except Exception as e:
            logger.error(f"Error checking new workspaces: {e}")
    
    async def process_all_pending_tasks(self):
        """Process all pending tasks across workspaces"""
        try:
            # Get all pending tasks from database
            # This is a simplified approach - in production you'd want pagination
            pending_workspaces = set()
            
            # For now, we'll check a few known workspace IDs
            # In production, this would query all active workspaces
            test_workspace_ids = [
                "123e4567-e89b-12d3-a456-426614174000",
                # Add more workspace IDs as needed
            ]
            
            for workspace_id in test_workspace_ids:
                tasks = await list_tasks(workspace_id)
                pending_tasks = [task for task in tasks if task["status"] == TaskStatus.PENDING.value]
                
                if pending_tasks:
                    pending_workspaces.add(workspace_id)
            
            # Process each workspace with pending tasks
            for workspace_id in pending_workspaces:
                await self.process_workspace_tasks(workspace_id)
                
        except Exception as e:
            logger.error(f"Error processing pending tasks: {e}")
    
    async def process_workspace_tasks(self, workspace_id: str):
        """Process tasks for a specific workspace"""
        try:
            # Get or create agent manager for this workspace
            manager = await self.get_agent_manager(workspace_id)
            if not manager:
                logger.error(f"Failed to get agent manager for workspace {workspace_id}")
                return
            
            # Get pending tasks for this workspace
            tasks = await list_tasks(workspace_id)
            pending_tasks = [task for task in tasks if task["status"] == TaskStatus.PENDING.value]
            
            logger.info(f"Processing {len(pending_tasks)} pending tasks for workspace {workspace_id}")
            
            # Process each pending task
            for task in pending_tasks:
                await self.execute_task_with_tracking(manager, task)
                
        except Exception as e:
            logger.error(f"Error processing tasks for workspace {workspace_id}: {e}")
    
    async def get_agent_manager(self, workspace_id: str) -> Optional[AgentManager]:
        """Get or create an agent manager for a workspace"""
        workspace_uuid = UUID(workspace_id)
        
        # Check if we already have a manager for this workspace
        if workspace_uuid in self.workspace_managers:
            return self.workspace_managers[workspace_uuid]
        
        try:
            # Create a new manager
            manager = AgentManager(workspace_uuid)
            success = await manager.initialize()
            
            if success:
                self.workspace_managers[workspace_uuid] = manager
                logger.info(f"Initialized agent manager for workspace {workspace_id}")
                return manager
            else:
                logger.error(f"Failed to initialize agent manager for workspace {workspace_id}")
                return None
        except Exception as e:
            logger.error(f"Error creating agent manager for workspace {workspace_id}: {e}")
            return None
    
    async def execute_task_with_tracking(self, manager: AgentManager, task: dict):
        """Execute a task with budget tracking"""
        task_id = task["id"]
        agent_id = task.get("agent_id")
        
        if not agent_id:
            logger.warning(f"Task {task_id} has no assigned agent")
            return
        
        try:
            # Log task start
            execution_start = {
                "timestamp": datetime.now().isoformat(),
                "event": "task_started",
                "task_id": task_id,
                "agent_id": agent_id,
                "workspace_id": task["workspace_id"]
            }
            self.execution_log.append(execution_start)
            
            # Get agent details for budget tracking
            agent_data = await get_agent(agent_id)
            if not agent_data:
                logger.error(f"Agent {agent_id} not found")
                return
            
            model = agent_data.get("llm_config", {}).get("model", "gpt-4.1-mini")
            
            logger.info(f"Executing task {task_id} with agent {agent_id}")
            
            # Execute the task (this would be the actual implementation)
            start_time = time.time()
            
            # Simulate token usage (in real implementation, get from OpenAI response)
            # These would come from the actual API calls
            estimated_input_tokens = len(str(task.get("description", ""))) * 1.3
            estimated_output_tokens = estimated_input_tokens * 0.5  # Rough estimate
            
            # Execute the task through the manager
            result = await manager.execute_task(UUID(task_id))
            
            execution_time = time.time() - start_time
            
            # Log token usage
            usage_record = self.budget_tracker.log_usage(
                agent_id=agent_id,
                model=model,
                input_tokens=int(estimated_input_tokens),
                output_tokens=int(estimated_output_tokens),
                task_id=task_id
            )
            
            # Log task completion
            execution_end = {
                "timestamp": datetime.now().isoformat(),
                "event": "task_completed",
                "task_id": task_id,
                "agent_id": agent_id,
                "workspace_id": task["workspace_id"],
                "execution_time": round(execution_time, 2),
                "cost": usage_record["total_cost"],
                "result_summary": str(result).split('\n')[0][:100] + "..." if result else "No result"
            }
            self.execution_log.append(execution_end)
            
            logger.info(f"Task {task_id} completed. Cost: ${usage_record['total_cost']:.6f}")
            
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {e}")
            
            # Log task error
            execution_error = {
                "timestamp": datetime.now().isoformat(),
                "event": "task_failed",
                "task_id": task_id,
                "agent_id": agent_id,
                "workspace_id": task["workspace_id"],
                "error": str(e)
            }
            self.execution_log.append(execution_error)
    
    async def create_initial_workspace_task(self, workspace_id: str) -> Optional[str]:
        """Create an initial task for a newly approved workspace"""
        try:
            workspace = await get_workspace(workspace_id)
            if not workspace:
                logger.error(f"Workspace {workspace_id} not found")
                return None
            
            # Get the project manager agent
            agents = await db_list_agents(workspace_id)
            pm_agent = None
            
            for agent in agents:
                if "project" in agent["role"].lower() and "coordinator" in agent["role"].lower():
                    pm_agent = agent
                    break
            
            if not pm_agent:
                # If no PM, use the first agent
                pm_agent = agents[0] if agents else None
            
            if not pm_agent:
                logger.error(f"No agents found for workspace {workspace_id}")
                return None
            
            # Create initial task
            initial_task = await create_task(
                workspace_id=workspace_id,
                agent_id=pm_agent["id"],
                name="Project Initialization",
                description=f"""
                Initialize the project: {workspace.get('name', 'Untitled Project')}
                
                Goal: {workspace.get('goal', 'No goal specified')}
                Budget: {workspace.get('budget', {}).get('max_amount', 'Not specified')} EUR
                
                Your tasks:
                1. Analyze the project goal and break it down into actionable phases
                2. Create a project plan with timelines
                3. Identify which specialized agents should handle which tasks
                4. Create tasks for other team members
                5. Set up regular progress check-ins
                
                Begin by coordinating with your team and creating the first set of tasks.
                """,
                status=TaskStatus.PENDING.value
            )
            
            if initial_task:
                logger.info(f"Created initial task {initial_task['id']} for workspace {workspace_id}")
                
                # Log the task creation
                creation_log = {
                    "timestamp": datetime.now().isoformat(),
                    "event": "initial_task_created",
                    "task_id": initial_task["id"],
                    "agent_id": pm_agent["id"],
                    "workspace_id": workspace_id
                }
                self.execution_log.append(creation_log)
                
                return initial_task["id"]
            
        except Exception as e:
            logger.error(f"Error creating initial task for workspace {workspace_id}: {e}")
            return None
    
    def get_recent_activity(self, workspace_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent activity log"""
        logs = self.execution_log
        
        if workspace_id:
            logs = [log for log in logs if log.get("workspace_id") == workspace_id]
        
        # Sort by timestamp (newest first) and limit
        logs.sort(key=lambda x: x["timestamp"], reverse=True)
        return logs[:limit]
    
    def get_budget_summary(self, workspace_id: str) -> Dict[str, Any]:
        """Get budget summary for a workspace"""
        try:
            # Get all agents for the workspace
            async def get_agents():
                return await db_list_agents(workspace_id)
            
            # This is a sync method, so we need to handle async calls carefully
            # In a real implementation, you'd make this async or use a different approach
            
            agent_ids = ["agent1", "agent2"]  # Placeholder
            return self.budget_tracker.get_workspace_total_cost(workspace_id, agent_ids)
            
        except Exception as e:
            logger.error(f"Error getting budget summary: {e}")
            return {"total_cost": 0, "agent_costs": {}, "error": str(e)}

# Global instance
task_executor = TaskExecutor()

# Function to start the executor
async def start_task_executor():
    """Start the task executor"""
    await task_executor.start()

# Function to stop the executor
async def stop_task_executor():
    """Stop the task executor"""
    await task_executor.stop()

# Function to trigger initial task creation
async def trigger_initial_workspace_task(workspace_id: str) -> Optional[str]:
    """Trigger creation of initial task for a workspace"""
    return await task_executor.create_initial_workspace_task(workspace_id)