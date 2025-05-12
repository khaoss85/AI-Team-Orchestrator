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

logger = logging.getLogger(__name__)

class BudgetTracker:
    """Tracks budget usage for agents with detailed cost monitoring"""
    
    def __init__(self):
        self.usage_log = {}  # agent_id -> list of usage records
        
        # Token costs per model (per 1K tokens) in USD
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
            },
            "gpt-3.5-turbo": {
                "input": 0.001,
                "output": 0.002
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
    
    def get_agent_usage_details(self, agent_id: str) -> Dict[str, Any]:
        """Get detailed usage information for an agent"""
        if agent_id not in self.usage_log:
            return {
                "total_cost": 0.0,
                "total_tokens": {"input": 0, "output": 0},
                "usage_count": 0,
                "models_used": []
            }
        
        records = self.usage_log[agent_id]
        total_cost = sum(record["total_cost"] for record in records)
        total_input_tokens = sum(record["input_tokens"] for record in records)
        total_output_tokens = sum(record["output_tokens"] for record in records)
        models_used = list(set(record["model"] for record in records))
        
        return {
            "total_cost": round(total_cost, 6),
            "total_tokens": {
                "input": total_input_tokens,
                "output": total_output_tokens
            },
            "usage_count": len(records),
            "models_used": models_used,
            "recent_usage": records[-10:] if records else []
        }
    
    def get_workspace_total_cost(self, workspace_id: str, agent_ids: List[str]) -> Dict[str, Any]:
        """Get total cost for a workspace"""
        total_cost = 0.0
        agent_costs = {}
        total_tokens = {"input": 0, "output": 0}
        models_used = set()
        
        for agent_id in agent_ids:
            details = self.get_agent_usage_details(agent_id)
            agent_costs[agent_id] = details["total_cost"]
            total_cost += details["total_cost"]
            total_tokens["input"] += details["total_tokens"]["input"]
            total_tokens["output"] += details["total_tokens"]["output"]
            models_used.update(details["models_used"])
        
        return {
            "total_cost": round(total_cost, 6),
            "agent_costs": agent_costs,
            "total_tokens": total_tokens,
            "models_used": list(models_used),
            "currency": "USD"
        }

class TaskExecutor:
    """Enhanced Task Executor with budget tracking and automatic execution"""
    
    def __init__(self):
        """Initialize the task executor"""
        self.running = False
        self.workspace_managers = {}
        self.budget_tracker = BudgetTracker()
        self.execution_log = []  # Store execution history
        self.max_concurrent_tasks = 3  # Limit concurrent task executions
        self.active_tasks = set()  # Track currently executing tasks
    
    async def start(self):
        """Start the task executor"""
        if self.running:
            logger.warning("Task executor is already running")
            return
        
        self.running = True
        logger.info("Starting task executor")
        
        # Start the main execution loop
        asyncio.create_task(self.execution_loop())
        logger.info("Task executor started successfully")
    
    async def stop(self):
        """Stop the task executor"""
        if not self.running:
            logger.warning("Task executor is not running")
            return
        
        self.running = False
        logger.info("Stopping task executor...")
        
        # Wait for active tasks to complete
        while self.active_tasks:
            logger.info(f"Waiting for {len(self.active_tasks)} active tasks to complete...")
            await asyncio.sleep(1)
        
        logger.info("Task executor stopped")
    
    async def execution_loop(self):
        """Main execution loop for processing tasks"""
        loop_count = 0
        while self.running:
            try:
                loop_count += 1
                logger.debug(f"Execution loop iteration {loop_count}")
                
                # Process pending tasks from all workspaces
                await self.process_all_pending_tasks()
                
                # Check for workspaces that need initial task creation
                await self.check_for_new_workspaces()
                
                # Wait before next cycle
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in execution loop: {e}", exc_info=True)
                await asyncio.sleep(5)
    
    async def check_for_new_workspaces(self):
        """Check for workspaces that need initial tasks"""
        try:
            # Get active workspaces
            active_workspaces = await get_active_workspaces()
            logger.debug(f"Found {len(active_workspaces)} active workspaces")
            
            for workspace_id in active_workspaces:
                try:
                    # Check if workspace has any tasks
                    tasks = await list_tasks(workspace_id)
                    if not tasks:
                        logger.info(f"Creating initial task for workspace {workspace_id}")
                        await self.create_initial_workspace_task(workspace_id)
                except Exception as e:
                    logger.error(f"Error checking workspace {workspace_id} for initial tasks: {e}")
                    
        except Exception as e:
            logger.error(f"Error checking for new workspaces: {e}")
    
    async def process_all_pending_tasks(self):
        """Process all pending tasks across workspaces"""
        try:
            # Get workspace IDs that have pending tasks
            workspaces_with_tasks = await get_workspaces_with_pending_tasks()
            
            if not workspaces_with_tasks:
                # Also check active workspaces if no pending tasks found
                active_workspaces = await get_active_workspaces()
                logger.debug(f"No pending tasks found, checking {len(active_workspaces)} active workspaces")
                
                # Check for tasks in active workspaces too
                for workspace_id in active_workspaces:
                    try:
                        tasks = await list_tasks(workspace_id)
                        pending_tasks = [task for task in tasks if task["status"] == TaskStatus.PENDING.value]
                        if pending_tasks:
                            workspaces_with_tasks.append(workspace_id)
                            logger.debug(f"Found {len(pending_tasks)} pending tasks in workspace {workspace_id}")
                    except Exception as e:
                        logger.error(f"Error checking tasks for workspace {workspace_id}: {e}")
                        continue
            
            if workspaces_with_tasks:
                logger.info(f"Processing {len(workspaces_with_tasks)} workspaces with pending tasks")
                
                # Process each workspace with pending tasks
                for workspace_id in workspaces_with_tasks:
                    await self.process_workspace_tasks(workspace_id)
            else:
                logger.debug("No workspaces with pending tasks found")
                
        except Exception as e:
            logger.error(f"Error processing pending tasks: {e}", exc_info=True)
    
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
            
            logger.info(f"Workspace {workspace_id}: Found {len(pending_tasks)} pending tasks out of {len(tasks)} total tasks")
            
            # Limit concurrent executions
            for task in pending_tasks:
                if len(self.active_tasks) >= self.max_concurrent_tasks:
                    logger.info(f"Max concurrent tasks ({self.max_concurrent_tasks}) reached. Skipping remaining tasks.")
                    break
                
                task_id = task['id']
                if task_id not in self.active_tasks:
                    self.active_tasks.add(task_id)
                    logger.info(f"Starting execution of task {task_id} ({task['name']}) for agent {task.get('agent_id', 'None')}")
                    
                    # Execute task in background
                    asyncio.create_task(self._execute_task_wrapper(manager, task))
                
        except Exception as e:
            logger.error(f"Error processing tasks for workspace {workspace_id}: {e}", exc_info=True)
    
    async def _execute_task_wrapper(self, manager: AgentManager, task: dict):
        """Wrapper for task execution to handle cleanup"""
        try:
            await self.execute_task_with_tracking(manager, task)
        finally:
            # Ensure task is removed from active tasks
            task_id = task['id']
            if task_id in self.active_tasks:
                self.active_tasks.remove(task_id)
    
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
            logger.error(f"Error creating agent manager for workspace {workspace_id}: {e}", exc_info=True)
            return None
    
    async def execute_task_with_tracking(self, manager: AgentManager, task: dict):
        """Execute a task with comprehensive budget tracking"""
        task_id = task["id"]
        agent_id = task.get("agent_id")
        workspace_id = task["workspace_id"]
        
        if not agent_id:
            logger.warning(f"Task {task_id} has no assigned agent, skipping execution")
            return
        
        try:
            # Log task start
            execution_start = {
                "timestamp": datetime.now().isoformat(),
                "event": "task_started",
                "task_id": task_id,
                "agent_id": agent_id,
                "workspace_id": workspace_id,
                "task_name": task.get("name", "Unknown")
            }
            self.execution_log.append(execution_start)
            
            # Get agent details for budget tracking
            agent_data = await get_agent(agent_id)
            if not agent_data:
                logger.error(f"Agent {agent_id} not found")
                return
            
            # Determine model from agent configuration
            model = "gpt-4.1-mini"  # Default
            if agent_data.get("llm_config"):
                model = agent_data["llm_config"].get("model", model)
            else:
                # Use seniority mapping as fallback
                seniority = agent_data.get("seniority", "senior")
                seniority_model_map = {
                    "junior": "gpt-4.1-nano",
                    "senior": "gpt-4.1-mini",
                    "expert": "gpt-4.1"
                }
                model = seniority_model_map.get(seniority, model)
            
            logger.info(f"Executing task {task_id} with agent {agent_id} using model {model}")
            
            # Execute the task
            start_time = time.time()
            
            # Estimate token usage (would be replaced with actual usage from OpenAI)
            task_description = task.get("description", "")
            task_name = task.get("name", "")
            estimated_input_tokens = len(f"{task_name} {task_description}".split()) * 1.3
            
            try:
                # Execute the task through the manager
                result = await manager.execute_task(UUID(task_id))
                
                # Estimate output tokens from result
                result_text = str(result) if result else "Task completed"
                estimated_output_tokens = len(result_text.split()) * 1.0
                
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
                    "workspace_id": workspace_id,
                    "execution_time": round(execution_time, 2),
                    "cost": usage_record["total_cost"],
                    "model": model,
                    "tokens_used": {
                        "input": usage_record["input_tokens"],
                        "output": usage_record["output_tokens"]
                    },
                    "result_summary": (str(result).split('\n')[0][:100] + "...") if result else "No result"
                }
                self.execution_log.append(execution_end)
                
                logger.info(f"Task {task_id} completed successfully. Cost: ${usage_record['total_cost']:.6f}, Time: {execution_time:.2f}s")
                
            except Exception as execution_error:
                # Handle execution errors
                execution_time = time.time() - start_time
                
                # Still log usage even for failed tasks (partial execution)
                estimated_output_tokens = 50  # Minimal tokens for error response
                
                usage_record = self.budget_tracker.log_usage(
                    agent_id=agent_id,
                    model=model,
                    input_tokens=int(estimated_input_tokens),
                    output_tokens=int(estimated_output_tokens),
                    task_id=task_id
                )
                
                # Log task failure
                execution_error_log = {
                    "timestamp": datetime.now().isoformat(),
                    "event": "task_failed",
                    "task_id": task_id,
                    "agent_id": agent_id,
                    "workspace_id": workspace_id,
                    "execution_time": round(execution_time, 2),
                    "cost": usage_record["total_cost"],
                    "error": str(execution_error),
                    "model": model
                }
                self.execution_log.append(execution_error_log)
                
                logger.error(f"Task {task_id} failed after {execution_time:.2f}s: {execution_error}")
                raise
            
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {e}", exc_info=True)
            
            # Log task error
            execution_error = {
                "timestamp": datetime.now().isoformat(),
                "event": "task_error",
                "task_id": task_id,
                "agent_id": agent_id,
                "workspace_id": workspace_id,
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
            
            # Get the project manager agent or the first available agent
            agents = await db_list_agents(workspace_id)
            
            if not agents:
                logger.error(f"No agents found for workspace {workspace_id}")
                return None
            
            # Find project manager or coordinator agent
            pm_agent = None
            for agent in agents:
                role_lower = agent["role"].lower()
                if any(keyword in role_lower for keyword in ["project", "coordinator", "manager"]):
                    pm_agent = agent
                    break
            
            # Use first agent if no PM found
            pm_agent = pm_agent or agents[0]
            
            # Create initial task with detailed description
            task_description = f"""
            Initialize the project: {workspace.get('name', 'Untitled Project')}
            
            Project Goal: {workspace.get('goal', 'No goal specified')}
            Budget: {workspace.get('budget', {}).get('max_amount', 'Not specified')} EUR
            
            Your tasks as the {pm_agent['role']}:
            1. Analyze the project goal and break it down into actionable phases
            2. Create a detailed project plan with timelines and milestones
            3. Identify which specialized agents should handle which tasks
            4. Delegate initial tasks to other team members
            5. Set up regular progress check-ins and reporting
            6. Establish communication protocols with other agents
            
            Begin by:
            - Understanding the project scope and requirements
            - Coordinating with your team to assign roles and responsibilities
            - Creating the first set of actionable tasks for team members
            - Setting up monitoring and evaluation criteria
            
            Use your tools effectively to research, plan, and coordinate the project start.
            """
            
            initial_task = await create_task(
                workspace_id=workspace_id,
                agent_id=pm_agent["id"],
                name="Project Initialization and Planning",
                description=task_description,
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
            logger.error(f"Error creating initial task for workspace {workspace_id}: {e}", exc_info=True)
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
            # This is a placeholder - in real implementation, you'd get agent IDs from database
            # For now, return a basic summary
            logger.warning("get_budget_summary called with placeholder implementation")
            return {
                "total_cost": 0.0,
                "agent_costs": {},
                "total_tokens": {"input": 0, "output": 0},
                "currency": "USD",
                "models_used": []
            }
            
        except Exception as e:
            logger.error(f"Error getting budget summary: {e}")
            return {"total_cost": 0, "agent_costs": {}, "error": str(e)}
    
    def get_executor_stats(self) -> Dict[str, Any]:
        """Get executor statistics"""
        return {
            "running": self.running,
            "active_workspaces": len(self.workspace_managers),
            "active_tasks": len(self.active_tasks),
            "total_execution_logs": len(self.execution_log),
            "tracked_agents": len(self.budget_tracker.usage_log),
            "max_concurrent_tasks": self.max_concurrent_tasks
        }

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