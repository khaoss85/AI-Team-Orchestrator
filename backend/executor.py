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

# Import the new auto-generation components
from task_analyzer import AutoTaskGenerator, EnhancedTaskExecutor, TaskAnalysisResult

logger = logging.getLogger(__name__)

class BudgetTracker:
    """Tracks budget usage for agents with detailed cost monitoring"""
    # [Previous BudgetTracker implementation remains the same]
    
    def __init__(self):
        self.usage_log = {}
        
        # Token costs per model
        self.token_costs = {
            "gpt-4.1": {"input": 0.03, "output": 0.06},
            "gpt-4.1-mini": {"input": 0.015, "output": 0.03},
            "gpt-4.1-nano": {"input": 0.01, "output": 0.02},
            "gpt-4-turbo": {"input": 0.02, "output": 0.04},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002}
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
    """Enhanced Task Executor with automatic task generation"""
    
    def __init__(self):
        """Initialize the enhanced task executor"""
        self.running = False
        self.workspace_managers = {}
        self.budget_tracker = BudgetTracker()
        self.execution_log = []
        self.max_concurrent_tasks = 3 # Limite per il numero di task concorrenti (esempio)
        self.active_tasks_count = 0 # Contatore task attivi
        self.task_queue = asyncio.Queue() # Coda per gestire i task in attesa
    
        # New components for automation
        self.auto_generator = AutoTaskGenerator()
        self.enhanced_handler = EnhancedTaskExecutor() # Istanza dell'handler potenziato
    
    async def start(self):
        """Start the task executor"""
        if self.running:
            logger.warning("Task executor is already running")
            return
        
        self.running = True
        logger.info("Starting enhanced task executor with auto-generation capabilities")
        
        # Avvia i worker per processare la coda dei task
        self.worker_tasks = [asyncio.create_task(self._task_worker()) for _ in range(self.max_concurrent_tasks)]
        
        # Start the main execution loop
        asyncio.create_task(self.execution_loop())
        logger.info("Enhanced task executor started successfully")

    async def stop(self):
        """Stop the task executor"""
        if not self.running:
            logger.warning("Task executor is not running")
            return
        
        self.running = False
        logger.info("Stopping task executor...")

        # Segnala ai worker di terminare
        for _ in range(len(self.worker_tasks)):
            await self.task_queue.put(None) # Segnale di terminazione

        # Attendi che tutti i worker completino
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        logger.info("Task executor stopped.")

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
                
            except asyncio.CancelledError:
                logger.info("Execution loop cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in execution loop: {e}", exc_info=True)
                await asyncio.sleep(30) # Longer sleep on error

    async def _task_worker(self):
        """Worker che processa i task dalla coda."""
        while self.running:
            try:
                manager, task_dict = await self.task_queue.get()
                if task_dict is None: # Segnale di terminazione
                    self.task_queue.task_done()
                    break
                
                task_id = task_dict.get("id", "UnknownID")
                logger.info(f"Worker picking up task: {task_id}")
                self.active_tasks_count +=1
                try:
                    await self.execute_task_with_tracking(manager, task_dict)
                except Exception as e_exec:
                    logger.error(f"Error executing task {task_id} in worker: {e_exec}", exc_info=True)
                finally:
                    self.active_tasks_count -=1
                    self.task_queue.task_done()
                    logger.info(f"Worker finished task: {task_id}. Active tasks: {self.active_tasks_count}")
            except asyncio.CancelledError:
                logger.info("Task worker cancelled.")
                break
            except Exception as e_worker:
                logger.error(f"Error in task worker: {e_worker}", exc_info=True)
                # Se c'è un errore nel worker stesso (non nell'esecuzione del task), attendi un po'
                await asyncio.sleep(5)

    async def check_for_new_workspaces(self):
        """Check for workspaces that need initial tasks"""
        try:
            logger.info("Checking for workspaces needing initial tasks")
            active_ws_ids = await get_active_workspaces() # Prende solo ID
            
            for ws_id in active_ws_ids:
                tasks = await list_tasks(ws_id)
                if not tasks: # Se non ci sono task
                    workspace = await get_workspace(ws_id)
                    if workspace and workspace.get("status") == WorkspaceStatus.ACTIVE.value:
                        logger.info(f"Workspace {ws_id} is active and has no tasks. Attempting to create initial task.")
                        await self.create_initial_workspace_task(ws_id)
        except Exception as e:
            logger.error(f"Error checking new workspaces: {e}", exc_info=True)
    
    async def process_all_pending_tasks(self):
        """Process all pending tasks across workspaces"""
        try:
            logger.info("Processing all pending tasks")
            # Get workspace IDs that have pending tasks
            workspaces_with_pending = await get_workspaces_with_pending_tasks()
            
            logger.info(f"Found {len(workspaces_with_pending)} workspaces with pending tasks.")
            
            for workspace_id in workspaces_with_pending:
                if self.task_queue.qsize() < self.max_concurrent_tasks * 2: # Non sovraccaricare la coda
                    await self.process_workspace_tasks(workspace_id)
                else:
                    logger.warning(f"Task queue full for workspace {workspace_id}, skipping for now.")
        except Exception as e:
            logger.error(f"Error processing pending tasks: {e}", exc_info=True)
    
    async def process_workspace_tasks(self, workspace_id: str):
        """Process tasks for a specific workspace"""
        try:
            manager = await self.get_agent_manager(workspace_id)
            if not manager:
                logger.error(f"Failed to get agent manager for workspace {workspace_id}")
                return
            
            tasks = await list_tasks(workspace_id)
            pending_tasks = [task for task in tasks if task["status"] == TaskStatus.PENDING.value]
            
            if pending_tasks:
                logger.info(f"Queueing {len(pending_tasks)} pending tasks for workspace {workspace_id}")
                for task_dict in pending_tasks:
                    if self.task_queue.qsize() < self.max_concurrent_tasks * 5: # Limite più generoso per la coda
                        await self.task_queue.put((manager, task_dict))
                        # Aggiorna lo stato del task a "queued" o simile se necessario
                        # await update_task_status(task_dict["id"], "queued") # Esempio
                    else:
                        logger.warning(f"Task queue is getting large ({self.task_queue.qsize()}). Holding off on adding more tasks for workspace {workspace_id}.")
                        break 
        except Exception as e:
            logger.error(f"Error processing tasks for workspace {workspace_id}: {e}", exc_info=True)
    
    async def get_agent_manager(self, workspace_id: str) -> Optional[AgentManager]:
        """Get or create an agent manager for a workspace"""
        workspace_uuid = UUID(workspace_id)
        
        if workspace_uuid in self.workspace_managers:
            return self.workspace_managers[workspace_uuid]
        
        try:
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
        """Enhanced task execution with automatic follow-up generation"""
        task_id = task["id"]
        agent_id = task.get("agent_id")
        workspace_id = task["workspace_id"]
        
        if not agent_id:
            logger.warning(f"Task {task_id} has no assigned agent, skipping execution")
            await update_task_status(task_id, TaskStatus.FAILED.value, {"error": "No agent assigned"})
            return
        
        try:
            # Log task start and update status
            execution_start_log = {
                "timestamp": datetime.now().isoformat(), "event": "task_started",
                "task_id": task_id, "agent_id": agent_id, "workspace_id": workspace_id,
                "task_name": task.get("name", "Unknown")
            }
            self.execution_log.append(execution_start_log)
            await update_task_status(task_id, TaskStatus.IN_PROGRESS.value)
            
            agent_data = await get_agent(agent_id)
            if not agent_data:
                logger.error(f"Agent {agent_id} not found for task {task_id}")
                await update_task_status(task_id, TaskStatus.FAILED.value, {"error": f"Agent {agent_id} not found"})
                return
            
            model = "gpt-4.1-mini" # Default
            if agent_data.get("llm_config") and agent_data["llm_config"].get("model"):
                model = agent_data["llm_config"]["model"]
            else: # Fallback to seniority if no llm_config
                seniority_map = {"junior": "gpt-4.1-nano", "senior": "gpt-4.1-mini", "expert": "gpt-4.1"}
                model = seniority_map.get(agent_data.get("seniority", "senior"), model)

            logger.info(f"Executing task {task_id} ({task.get('name')}) with agent {agent_id} using model {model}")
            
            start_time = time.time()
            task_description = task.get("description", "")
            task_name = task.get("name", "")
            # Più precisa stima dei token (considera circa 4 caratteri per token)
            estimated_input_tokens = len(f"{task_name} {task_description}") / 4 
            
            # Converti il dizionario del task in un oggetto Task Pydantic
            # Assicurati che tutti i campi richiesti da Task (in models.py) siano presenti nel dizionario 'task'
            # o forniti con valori di default.
            try:
                task_obj_for_execution = Task(
                    id=UUID(task_id),
                    workspace_id=UUID(workspace_id),
                    agent_id=UUID(agent_id) if agent_id else None,
                    name=task.get("name", "N/A"),
                    description=task.get("description", ""),
                    status=TaskStatus.IN_PROGRESS, # Lo stato attuale
                    created_at=datetime.fromisoformat(task.get("created_at")) if task.get("created_at") else datetime.now(),
                    updated_at=datetime.fromisoformat(task.get("updated_at")) if task.get("updated_at") else datetime.now(),
                    result=task.get("result") # opzionale
                )
            except Exception as pydantic_error:
                logger.error(f"Error creating Pydantic Task object for task {task_id}: {pydantic_error}", exc_info=True)
                await update_task_status(task_id, TaskStatus.FAILED.value, {"error": "Internal error preparing task execution."})
                return

            # Usa l'oggetto Task Pydantic per l'esecuzione
            # result = await manager.execute_task(task_obj_for_execution)
            # Se manager.execute_task si aspetta un UUID:
            result = await manager.execute_task(UUID(task_id))


            execution_time = time.time() - start_time
            result_text = str(result.get("output") if isinstance(result, dict) else result) if result else "Task completed without explicit output"
            estimated_output_tokens = len(result_text) / 4

            usage_record = self.budget_tracker.log_usage(
                agent_id=agent_id, model=model,
                input_tokens=int(estimated_input_tokens),
                output_tokens=int(estimated_output_tokens), task_id=task_id
            )
            
            task_result_payload = {
                "output": result, "status": "completed", "execution_time": execution_time,
                "model_used": model, 
                "tokens_used": {"input": usage_record["input_tokens"], "output": usage_record["output_tokens"]},
                "cost": usage_record["total_cost"]
            }
            await update_task_status(task_id, TaskStatus.COMPLETED.value, task_result_payload)

            execution_end_log = {
                "timestamp": datetime.now().isoformat(), "event": "task_completed",
                "task_id": task_id, "agent_id": agent_id, "workspace_id": workspace_id,
                "execution_time": round(execution_time, 2), "cost": usage_record["total_cost"], "model": model,
                "tokens_used": {"input": usage_record["input_tokens"], "output": usage_record["output_tokens"]},
                "result_summary": (result_text[:100] + "...") if len(result_text) > 100 else result_text
            }
            self.execution_log.append(execution_end_log)
            logger.info(f"Task {task_id} completed successfully. Cost: ${usage_record['total_cost']:.6f}, Time: {execution_time:.2f}s")

            # Auto-generate follow-up tasks
            try:
                # Ricostruisci l'oggetto Task Pydantic con lo stato aggiornato e il risultato
                completed_task_obj = Task(
                    id=UUID(task_id), workspace_id=UUID(workspace_id), agent_id=UUID(agent_id) if agent_id else None,
                    name=task.get("name", ""), description=task.get("description", ""),
                    status=TaskStatus.COMPLETED, # Ora è completato
                    result=task_result_payload, # Include i risultati dell'esecuzione
                    created_at=datetime.fromisoformat(task.get("created_at")) if task.get("created_at") else datetime.now(), # Mantieni originale
                    updated_at=datetime.now() # Ora dell'aggiornamento
                )
                await self.enhanced_handler.handle_task_completion(
                    completed_task=completed_task_obj,
                    task_result=task_result_payload, # Passa il payload completo dei risultati
                    workspace_id=workspace_id
                )
                logger.info(f"Auto-generation analysis completed for task {task_id}")
            except Exception as auto_error:
                logger.error(f"Error in auto-generation for task {task_id}: {auto_error}", exc_info=True)
            
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {e}", exc_info=True)
            execution_time_failed = time.time() - start_time if 'start_time' in locals() else 0
            estimated_output_tokens_failed = 50 # Stima conservativa per errori
            
            model_for_error = model if 'model' in locals() else "unknown"
            usage_record_failed = self.budget_tracker.log_usage(
                agent_id=agent_id, model=model_for_error,
                input_tokens=int(estimated_input_tokens) if 'estimated_input_tokens' in locals() else 0,
                output_tokens=int(estimated_output_tokens_failed), task_id=task_id
            )
            
            await update_task_status(task_id, TaskStatus.FAILED.value, {"error": str(e), "cost": usage_record_failed["total_cost"]})
            
            execution_error_log = {
                "timestamp": datetime.now().isoformat(), "event": "task_failed",
                "task_id": task_id, "agent_id": agent_id, "workspace_id": workspace_id,
                "execution_time": round(execution_time_failed, 2),
                "cost": usage_record_failed["total_cost"], "error": str(e), "model": model_for_error
            }
            self.execution_log.append(execution_error_log)
    
    async def create_initial_workspace_task(self, workspace_id: str) -> Optional[str]:
        """Create initial task with enhanced context for auto-generation"""
        try:
            workspace = await get_workspace(workspace_id)
            if not workspace:
                logger.error(f"Workspace {workspace_id} not found for initial task creation.")
                return None
            
            agents = await db_list_agents(workspace_id)
            if not agents:
                logger.error(f"No agents found for workspace {workspace_id}, cannot create initial task.")
                return None
            
            pm_agent = next((agent for agent in agents if any(keyword in agent["role"].lower() for keyword in ["project", "coordinator", "manager"])), agents[0])
            
            task_description = f"""
            Initialize the project: {workspace.get('name', 'Untitled Project')}
            
            Project Goal: {workspace.get('goal', 'No goal specified')}
            Budget: {workspace.get('budget', {}).get('max_amount', 'Not specified')} {workspace.get('budget', {}).get('currency', 'EUR')}
            
            Your tasks as the {pm_agent['role']}:
            1. Analyze the project goal and break it down into actionable phases and sub-tasks.
            2. Create a detailed project plan with timelines, milestones, and dependencies.
            3. Identify which specialized agents from the team should handle which tasks or phases.
            4. Delegate initial tasks to other team members using the 'create_task_for_agent' tool.
            5. Set up regular progress check-ins and reporting mechanisms.
            6. Establish communication protocols with other agents.
            
            IMPORTANT: You MUST use the 'create_task_for_agent' tool to delegate work.
            When you identify specific work for specialists, create those tasks immediately.
            
            Begin by:
            - Deeply understanding the project scope, requirements, and deliverables.
            - Coordinating with your team (if other agents are already defined for complex handoffs) to assign roles and responsibilities for the initial phase.
            - Creating the first set of actionable tasks for yourself and other team members.
            - Defining monitoring and evaluation criteria for the project's success.
            
            Use your auto-task creation tools effectively.
            Remember: You MUST create specific tasks for other agents when their expertise is needed.
            Provide a summary of your plan and the initial tasks you have created/delegated as your output.
            """
            
            initial_task = await create_task(
                workspace_id=workspace_id, agent_id=pm_agent["id"],
                name="Project Initialization and Strategic Planning",
                description=task_description, status=TaskStatus.PENDING.value
            )
            
            if initial_task:
                logger.info(f"Created enhanced initial task {initial_task['id']} for workspace {workspace_id}")
                creation_log = {
                    "timestamp": datetime.now().isoformat(), "event": "initial_task_created",
                    "task_id": initial_task["id"], "agent_id": pm_agent["id"], "workspace_id": workspace_id,
                    "enhanced_with_auto_generation": True
                }
                self.execution_log.append(creation_log)
                return initial_task["id"]
            else:
                logger.error(f"DB call to create_task returned None for initial task in workspace {workspace_id}")
                return None
        except Exception as e:
            logger.error(f"Error creating initial task for workspace {workspace_id}: {e}", exc_info=True)
            return None
    
    def get_recent_activity(self, workspace_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent activity log with auto-generation events"""
        logs_to_filter = self.execution_log
        
        if workspace_id:
            logs_to_filter = [log for log in logs_to_filter if log.get("workspace_id") == workspace_id]
        
        logs_to_filter.sort(key=lambda x: x["timestamp"], reverse=True)
        return logs_to_filter[:limit]
    
    def get_auto_generation_stats(self) -> Dict[str, Any]:
        """Get statistics about auto-generated tasks"""
        auto_gen_events = [
            log for log in self.execution_log 
            if log.get("event") in ["task_created", "handoff_requested", "follow_up_generated"] 
            # Aggiungi altri eventi se necessario, es. "auto_task_generated"
        ]
        
        return {
            "total_auto_generated_tasks": len(auto_gen_events), # Questo potrebbe contare più del dovuto se "task_created" è generico
            "recent_auto_generation_events": auto_gen_events[-10:] if auto_gen_events else [],
            "auto_generation_enabled": True # Assumendo che sia sempre attivo
        }

# Global instance
task_executor = TaskExecutor()

# Functions to start/stop
async def start_task_executor():
    """Start the enhanced task executor"""
    await task_executor.start()

async def stop_task_executor():
    """Stop the task executor"""
    await task_executor.stop()

async def trigger_initial_workspace_task(workspace_id: str) -> Optional[str]:
    """Trigger creation of initial task with auto-generation capabilities"""
    return await task_executor.create_initial_workspace_task(workspace_id)