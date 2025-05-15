import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union, Set
from uuid import UUID, uuid4
import json
import time

# Import da moduli del progetto
from models import TaskStatus, Task, AgentStatus, WorkspaceStatus, Agent as AgentModelPydantic
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

# Import componenti per auto-generazione
from task_analyzer import EnhancedTaskExecutor

logger = logging.getLogger(__name__)

class BudgetTracker:
    """Tracks budget usage for agents with detailed cost monitoring"""

    def __init__(self):
        """Initialize the budget tracker."""
        self.usage_log: Dict[str, List[Dict[str, Any]]] = {}
        # Costi aggiornati per token per diversi modelli (valori ipotetici)
        self.token_costs = {
            "gpt-4.1": {"input": 0.03, "output": 0.06},
            "gpt-4.1-mini": {"input": 0.015, "output": 0.03},
            "gpt-4.1-nano": {"input": 0.01, "output": 0.02},
            "gpt-4-turbo": {"input": 0.02, "output": 0.04},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002}
        }
        # Modello di fallback se non specificato o non trovato
        self.default_model = "gpt-4.1-mini"
        self.default_costs = self.token_costs[self.default_model]

    def log_usage(self, agent_id: str, model: str, input_tokens: int, output_tokens: int, task_id: Optional[str] = None) -> Dict[str, Any]:
        """Log token usage and associated costs for an agent and task."""
        if agent_id not in self.usage_log:
            self.usage_log[agent_id] = []

        # Ottieni i costi per il modello specificato, altrimenti usa il default
        costs = self.token_costs.get(model, self.default_costs)
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]
        total_cost = input_cost + output_cost

        usage_record = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "agent_id": agent_id,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(total_cost, 6),
            "currency": "USD"
        }

        self.usage_log[agent_id].append(usage_record)
        logger.info(f"Budget usage - Agent {agent_id}, Task {task_id}: ${total_cost:.6f} (Model: {model}, Tokens: {input_tokens} in + {output_tokens} out)")
        return usage_record

    def get_agent_total_cost(self, agent_id: str) -> float:
        """Calculate the total cost incurred by a specific agent."""
        if agent_id not in self.usage_log:
            return 0.0
        return sum(record["total_cost"] for record in self.usage_log[agent_id])

    def get_workspace_total_cost(self, workspace_id: str, agent_ids: List[str]) -> Dict[str, Any]:
        """Calculate the total cost incurred within a workspace, broken down by agent."""
        total_cost = 0.0
        agent_costs = {}
        total_tokens = {"input": 0, "output": 0}

        for agent_id in agent_ids:
            agent_total_cost = self.get_agent_total_cost(agent_id)
            agent_costs[agent_id] = round(agent_total_cost, 6)
            total_cost += agent_total_cost

            # Accumula i token per l'agente
            agent_input_tokens = 0
            agent_output_tokens = 0
            if agent_id in self.usage_log:
                for record in self.usage_log[agent_id]:
                    agent_input_tokens += record["input_tokens"]
                    agent_output_tokens += record["output_tokens"]
            total_tokens["input"] += agent_input_tokens
            total_tokens["output"] += agent_output_tokens

        return {
            "workspace_id": workspace_id,
            "total_cost": round(total_cost, 6),
            "agent_costs": agent_costs,
            "total_tokens": total_tokens,
            "currency": "USD"
        }

    def get_all_usage_logs(self, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return all usage logs, optionally filtered by agent."""
        if agent_id:
            return self.usage_log.get(agent_id, [])
        else:
            all_logs = []
            for logs in self.usage_log.values():
                all_logs.extend(logs)
            return all_logs


class TaskExecutor:
    """Enhanced Task Executor with runaway protection and better monitoring"""

    def __init__(self):
        """Initialize the enhanced task executor."""
        self.running = False
        self.paused = False
        self.pause_event = asyncio.Event()
        self.pause_event.set()

        self.workspace_managers: Dict[UUID, AgentManager] = {}
        self.budget_tracker = BudgetTracker()
        self.execution_log: List[Dict[str, Any]] = []

        # Configurazione concorrenza e coda
        self.max_concurrent_tasks = int(os.getenv("MAX_CONCURRENT_TASKS", 3))
        self.max_queue_size = self.max_concurrent_tasks * 10
        self.active_tasks_count = 0
        self.task_queue: asyncio.Queue = asyncio.Queue(maxsize=self.max_queue_size)
        self.worker_tasks: List[asyncio.Task] = []

        # Componenti per automazione
        self.enhanced_handler = EnhancedTaskExecutor()

        # AGGIUNTE per runaway protection
        self.workspace_auto_generation_paused: Set[str] = set()
        self.workspace_task_counts: Dict[str, Dict[str, int]] = {}
        self.last_runaway_check: Optional[datetime] = None
        
        # Configurazione runaway protection
        self.max_pending_tasks_per_workspace = int(os.getenv("MAX_PENDING_TASKS", 50))
        self.max_handoff_percentage = float(os.getenv("MAX_HANDOFF_PERCENTAGE", 0.3))
        self.runaway_check_interval = 300  # 5 minuti

    async def check_workspace_health(self, workspace_id: str) -> Dict[str, Any]:
        """Controlla la salute di un workspace e rileva possibili runaway"""
        try:
            all_tasks = await list_tasks(workspace_id)
            
            # Conta task per status
            task_counts = {
                'total': len(all_tasks),
                'pending': len([t for t in all_tasks if t.get("status") == TaskStatus.PENDING.value]),
                'completed': len([t for t in all_tasks if t.get("status") == TaskStatus.COMPLETED.value]),
                'failed': len([t for t in all_tasks if t.get("status") == TaskStatus.FAILED.value]),
                'in_progress': len([t for t in all_tasks if t.get("status") == TaskStatus.IN_PROGRESS.value])
            }
            
            # Analizza pattern handoff
            handoff_tasks = [t for t in all_tasks if "handoff" in t.get("name", "").lower()]
            handoff_percentage = len(handoff_tasks) / len(all_tasks) if all_tasks else 0
            
            # Rileva runaway patterns
            health_issues = []
            
            if task_counts['pending'] > self.max_pending_tasks_per_workspace:
                health_issues.append(f"Excessive pending tasks: {task_counts['pending']}")
            
            if handoff_percentage > self.max_handoff_percentage:
                health_issues.append(f"Excessive handoffs: {handoff_percentage:.1%}")
            
            # Check per task loop (stesso nome ripetuto)
            task_names = [t.get("name", "") for t in all_tasks[-20:]]  # Ultimi 20 task
            name_counts = {}
            for name in task_names:
                if name:
                    name_counts[name] = name_counts.get(name, 0) + 1
            
            repeated_tasks = {name: count for name, count in name_counts.items() if count > 3}
            if repeated_tasks:
                health_issues.append(f"Repeated task patterns: {repeated_tasks}")
            
            # Check per task creation velocity
            if len(all_tasks) > 10:
                recent_tasks = sorted(all_tasks, key=lambda x: x.get("created_at", ""), reverse=True)[:10]
                first_time = datetime.fromisoformat(recent_tasks[-1]["created_at"].replace('Z', '+00:00'))
                last_time = datetime.fromisoformat(recent_tasks[0]["created_at"].replace('Z', '+00:00'))
                time_diff = (last_time - first_time).total_seconds()
                
                if time_diff > 0:
                    tasks_per_minute = (len(recent_tasks) / time_diff) * 60
                    if tasks_per_minute > 5:  # Più di 5 task al minuto è sospetto
                        health_issues.append(f"High task creation rate: {tasks_per_minute:.1f}/min")
            
            return {
                'workspace_id': workspace_id,
                'task_counts': task_counts,
                'handoff_percentage': handoff_percentage,
                'health_issues': health_issues,
                'is_healthy': len(health_issues) == 0,
                'auto_generation_paused': workspace_id in self.workspace_auto_generation_paused
            }
            
        except Exception as e:
            logger.error(f"Error checking workspace health for {workspace_id}: {e}")
            return {
                'workspace_id': workspace_id,
                'error': str(e),
                'is_healthy': False
            }

    async def _pause_auto_generation_for_workspace(self, workspace_id: str, reason: str = "runaway_detected"):
        """Mette in pausa l'auto-generazione per un workspace"""
        self.workspace_auto_generation_paused.add(workspace_id)
        
        # Log critico
        logger.critical(f"AUTO-GENERATION PAUSED for workspace {workspace_id}. Reason: {reason}")
        
        # Aggiorna stato workspace se necessario
        try:
            workspace = await get_workspace(workspace_id)
            if workspace and workspace.get("status") == "active":
                await update_workspace_status(workspace_id, "needs_intervention")
                logger.info(f"Updated workspace {workspace_id} status to 'needs_intervention'")
        except Exception as e:
            logger.error(f"Failed to update workspace status for {workspace_id}: {e}")
        
        # Notifica via log evento speciale per monitoring
        self.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "event": "auto_generation_paused", 
            "workspace_id": workspace_id,
            "reason": reason,
            "pending_tasks_count": len(await list_tasks(workspace_id))
        })

    async def _resume_auto_generation_for_workspace(self, workspace_id: str):
        """Riprende l'auto-generazione per un workspace"""
        if workspace_id in self.workspace_auto_generation_paused:
            self.workspace_auto_generation_paused.remove(workspace_id)
            logger.info(f"AUTO-GENERATION RESUMED for workspace {workspace_id}")
            
            # Log dell'evento
            self.execution_log.append({
                "timestamp": datetime.now().isoformat(),
                "event": "auto_generation_resumed",
                "workspace_id": workspace_id
            })

    async def start(self):
        """Start the task executor service."""
        if self.running:
            logger.warning("Task executor is already running.")
            return

        self.running = True
        self.paused = False
        self.pause_event.set()
        self.execution_log = []
        logger.info(f"Starting enhanced task executor. Max concurrent tasks: {self.max_concurrent_tasks}, Max queue size: {self.max_queue_size}")

        # Avvia i worker per processare la coda
        self.worker_tasks = [asyncio.create_task(self._task_worker()) for _ in range(self.max_concurrent_tasks)]

        # Avvia il loop principale di gestione
        asyncio.create_task(self.execution_loop())
        logger.info("Enhanced task executor started successfully.")

    async def stop(self):
        """Stop the task executor service gracefully."""
        if not self.running:
            logger.warning("Task executor is not running.")
            return

        logger.info("Stopping task executor...")
        self.running = False
        self.paused = True
        self.pause_event.set()

        # Invia segnali di terminazione ai worker
        for i in range(len(self.worker_tasks)):
            try:
                await asyncio.wait_for(self.task_queue.put(None), timeout=2.0)
            except asyncio.TimeoutError:
                logger.warning(f"Timeout putting None signal in task_queue during stop (worker {i+1}/{len(self.worker_tasks)}).")
            except asyncio.QueueFull:
                 logger.warning(f"Queue full trying to put None signal during stop (worker {i+1}/{len(self.worker_tasks)}). May cause delay.")

        # Attendi il completamento dei worker
        if self.worker_tasks:
            results = await asyncio.gather(*self.worker_tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception) and not isinstance(result, asyncio.CancelledError):
                    logger.error(f"Worker task {i} finished with error during stop: {result}", exc_info=result)
        self.worker_tasks = []
        logger.info("Task executor stopped.")

    async def pause(self):
        """Pause task processing. Workers finish current tasks but don't pick new ones."""
        if not self.running:
            logger.warning("Cannot pause: Task executor is not running.")
            return
        if self.paused:
            logger.info("Task executor is already paused.")
            return
        self.paused = True
        self.pause_event.clear()
        logger.info("Task executor paused. New task processing suspended. Workers will finish current tasks.")

    async def resume(self):
        """Resume task processing if paused."""
        if not self.running:
            logger.warning("Cannot resume: Task executor is not running. Start it first.")
            return
        if not self.paused:
            logger.info("Task executor is already running (not paused).")
            return
        self.paused = False
        self.pause_event.set()
        logger.info("Task executor resumed.")

    async def execution_loop(self):
        """Main loop with periodic runaway checks"""
        while self.running:
            try:
                await self.pause_event.wait()
                if not self.running: 
                    break
                
                # Main execution logic
                logger.debug("Execution loop running: checking for tasks and workspaces.")
                await self.process_all_pending_tasks()
                await self.check_for_new_workspaces()
                
                # AGGIUNTA: Periodic runaway check ogni 5 minuti
                if (self.last_runaway_check is None or 
                    (datetime.now() - self.last_runaway_check).total_seconds() > self.runaway_check_interval):
                    await self.periodic_runaway_check()
                
                # Attesa normale
                await asyncio.sleep(10)
                
            except asyncio.CancelledError:
                logger.info("Execution loop cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in execution_loop: {e}", exc_info=True)
                await asyncio.sleep(30)
        
        logger.info("Execution loop finished.")

    async def periodic_runaway_check(self):
        """Check periodico per rilevare e gestire runaway task generation"""
        try:
            # Get all active workspaces
            active_workspaces = await get_active_workspaces()
            
            runaway_detected = []
            
            for workspace_id in active_workspaces:
                health_status = await self.check_workspace_health(workspace_id)
                
                if not health_status['is_healthy']:
                    health_issues = health_status['health_issues']
                    logger.warning(f"Runaway check - Workspace {workspace_id}: {health_issues}")
                    
                    # Se ci sono problemi critici e non è già pausato
                    if (health_status['task_counts']['pending'] > 30 and 
                        workspace_id not in self.workspace_auto_generation_paused):
                        runaway_detected.append(workspace_id)
                        await self._pause_auto_generation_for_workspace(workspace_id, 
                            reason="Periodic runaway check detected excessive tasks")
            
            # Log summary
            if runaway_detected:
                logger.critical(f"Runaway check detected issues in {len(runaway_detected)} workspaces: {runaway_detected}")
            else:
                logger.debug(f"Runaway check completed - {len(active_workspaces)} workspaces healthy")
            
            self.last_runaway_check = datetime.now()
            
        except Exception as e:
            logger.error(f"Error in periodic runaway check: {e}", exc_info=True)

    async def _task_worker(self):
        """Worker process that takes tasks from the queue and executes them."""
        worker_id = uuid4()
        logger.info(f"Task worker {worker_id} started.")
        while self.running:
            try:
                await self.pause_event.wait()
                if not self.running: break

                manager: Optional[AgentManager] = None
                task_dict: Optional[Dict] = None
                try:
                    manager, task_dict = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                if task_dict is None:
                    self.task_queue.task_done()
                    logger.info(f"Worker {worker_id} received termination signal.")
                    break

                task_id = task_dict.get("id", "UnknownID")
                workspace_id = task_dict.get("workspace_id", "UnknownWS")
                logger.info(f"Worker {worker_id} picking up task: {task_id} from Workspace {workspace_id} (Queue size: {self.task_queue.qsize()})")

                # Incrementa contatore task attivi e esegui
                self.active_tasks_count += 1
                try:
                    if manager is None:
                         raise ValueError(f"Received task {task_id} with a null manager.")
                    await self.execute_task_with_tracking(manager, task_dict)
                except Exception as e_exec:
                    logger.error(f"Worker {worker_id} failed executing task {task_id}: {e_exec}", exc_info=True)
                finally:
                    self.active_tasks_count -= 1
                    self.task_queue.task_done()
                    logger.info(f"Worker {worker_id} finished processing task: {task_id}. Active tasks: {self.active_tasks_count}")

            except asyncio.CancelledError:
                logger.info(f"Task worker {worker_id} cancelled.")
                break
            except Exception as e_worker:
                logger.error(f"Unhandled error in task worker {worker_id}: {e_worker}", exc_info=True)
                await asyncio.sleep(5)

        logger.info(f"Task worker {worker_id} exiting.")

    async def check_for_new_workspaces(self):
        """Check for active workspaces without any tasks and create an initial one."""
        if self.paused: return

        try:
            logger.debug("Checking for workspaces needing initial tasks")
            active_ws_ids = await get_active_workspaces()

            for ws_id in active_ws_ids:
                tasks = await list_tasks(ws_id)
                if not tasks:
                    workspace_data = await get_workspace(ws_id)
                    if workspace_data and workspace_data.get("status") == WorkspaceStatus.ACTIVE.value:
                        logger.info(f"Workspace {ws_id} ('{workspace_data.get('name')}') is active and has no tasks. Attempting to create initial task.")
                        await self.create_initial_workspace_task(ws_id)
                    elif not workspace_data:
                         logger.warning(f"Could not retrieve data for supposedly active workspace {ws_id} during initial task check.")

        except Exception as e:
            logger.error(f"Error checking for new workspaces: {e}", exc_info=True)

    async def process_all_pending_tasks(self):
        """Find workspaces with pending tasks and queue them for processing."""
        if self.paused: return

        try:
            logger.debug("Processing all pending tasks")
            workspaces_with_pending = await get_workspaces_with_pending_tasks()

            if workspaces_with_pending:
                 logger.info(f"Found {len(workspaces_with_pending)} workspaces with pending tasks. Checking queue status.")

            for workspace_id in workspaces_with_pending:
                if self.task_queue.full():
                    logger.warning(f"Task queue is full (Size: {self.task_queue.qsize()}/{self.max_queue_size}). Skipping adding tasks from workspace {workspace_id} for now.")
                    continue

                await self.process_workspace_tasks(workspace_id)

        except Exception as e:
            logger.error(f"Error processing all pending tasks: {e}", exc_info=True)

    async def process_workspace_tasks(self, workspace_id: str):
        """Fetch pending tasks with enhanced runaway protection"""
        if self.paused: 
            return
        
        try:
            # STEP 1: Health check completo
            health_status = await self.check_workspace_health(workspace_id)
            
            # Se workspace non è healthy, gestisci
            if not health_status['is_healthy']:
                health_issues = health_status['health_issues']
                logger.warning(f"Workspace {workspace_id} health issues: {health_issues}")
                
                # Se ci sono problemi gravi, pausa auto-generazione
                critical_issues = [issue for issue in health_issues if any(keyword in issue.lower() 
                    for keyword in ['excessive pending', 'excessive handoffs', 'high task creation'])]
                
                if critical_issues and workspace_id not in self.workspace_auto_generation_paused:
                    await self._pause_auto_generation_for_workspace(workspace_id, 
                        reason=f"Health issues: {'; '.join(critical_issues)}")
                    return
            
            # STEP 2: Se auto-generation è pausata, controlla se si può riprendere
            if workspace_id in self.workspace_auto_generation_paused:
                # Controlla se i problemi sono risolti
                if health_status['is_healthy'] and health_status['task_counts']['pending'] < 10:
                    await self._resume_auto_generation_for_workspace(workspace_id)
                else:
                    logger.info(f"Auto-generation still paused for {workspace_id}. "
                               f"Pending: {health_status['task_counts']['pending']}")
                    return
            
            # STEP 3: Processa task normalmente
            manager = await self.get_agent_manager(workspace_id)
            if not manager:
                logger.error(f"Failed to get agent manager for workspace {workspace_id}")
                return
            
            # Get pending tasks
            tasks_db = await list_tasks(workspace_id)
            pending_tasks_dicts = [task for task in tasks_db if task.get("status") == TaskStatus.PENDING.value]
            
            if not pending_tasks_dicts:
                return
            
            # STEP 4: Batch processing per evitare sovraccarico
            batch_size = min(3, len(pending_tasks_dicts))  # Ridotto da 5 a 3 per maggiore controllo
            tasks_to_process = pending_tasks_dicts[:batch_size]
            
            logger.info(f"Processing {len(tasks_to_process)}/{len(pending_tasks_dicts)} tasks for workspace {workspace_id}")
            
            queued_count = 0
            for task_dict in tasks_to_process:
                if self.task_queue.full():
                    logger.warning(f"Queue full, stopping task processing for workspace {workspace_id}")
                    break
                
                try:
                    self.task_queue.put_nowait((manager, task_dict))
                    queued_count += 1
                except asyncio.QueueFull:
                    logger.warning(f"Queue full during processing for workspace {workspace_id}")
                    break
            
            if queued_count > 0:
                logger.info(f"Successfully queued {queued_count} tasks for workspace {workspace_id}")
            
            # STEP 5: Update workspace task counts per tracking
            self.workspace_task_counts[workspace_id] = health_status['task_counts']
            
        except Exception as e:
            logger.error(f"Error processing tasks for workspace {workspace_id}: {e}", exc_info=True)

    async def get_agent_manager(self, workspace_id: str) -> Optional[AgentManager]:
        """Get or create an AgentManager instance for a given workspace ID."""
        try:
            workspace_uuid = UUID(workspace_id)
        except ValueError:
            logger.error(f"Invalid workspace ID format: {workspace_id}. Cannot get/create manager.")
            return None

        if workspace_uuid in self.workspace_managers:
            return self.workspace_managers[workspace_uuid]

        logger.info(f"Creating new AgentManager instance for workspace {workspace_id}.")
        try:
            manager = AgentManager(workspace_uuid)
            success = await manager.initialize()

            if success:
                self.workspace_managers[workspace_uuid] = manager
                logger.info(f"Initialized agent manager for workspace {workspace_id}")
                return manager
            else:
                logger.error(f"Failed to initialize agent manager for workspace {workspace_id}. Check logs for details from AgentManager.")
                return None
        except Exception as e:
            logger.error(f"Exception creating or initializing agent manager for workspace {workspace_id}: {e}", exc_info=True)
            return None

    async def execute_task_with_tracking(self, manager: AgentManager, task_dict: dict):
        """Executes a single task, tracks budget, logs events, and triggers post-processing."""
        task_id = task_dict.get("id")

        # Aggiungi controllo per task duplicati PER WORKSPACE
        workspace_id = task_dict.get("workspace_id")

        # Inizializza il tracking per workspace se non esiste
        if not hasattr(self, '_processed_tasks_by_workspace'):
            self._processed_tasks_by_workspace = {}

        # Inizializza set per questo workspace
        if workspace_id not in self._processed_tasks_by_workspace:
            self._processed_tasks_by_workspace[workspace_id] = set()

        # Controlla se task già processato in questo workspace
        if task_id in self._processed_tasks_by_workspace[workspace_id]:
            logger.warning(f"Task {task_id} already processed in workspace {workspace_id}, skipping")
            return

        # Aggiungi task al set di quelli processati
        self._processed_tasks_by_workspace[workspace_id].add(task_id)

        agent_id = task_dict.get("agent_id")

        # Validazione preliminare
        if not all([task_id, agent_id, workspace_id]):
            missing = [k for k, v in {'task_id': task_id, 'agent_id': agent_id, 'workspace_id': workspace_id}.items() if not v]
            error_msg = f"Task data incomplete: missing {', '.join(missing)}. Cannot execute."
            logger.error(error_msg)
            if task_id:
                try:
                    await update_task_status(task_id, TaskStatus.FAILED.value, {"error": error_msg, "status_detail": "invalid_task_data"})
                except Exception as db_err:
                    logger.error(f"Failed to update status for invalid task {task_id}: {db_err}")
            return

        start_time_tracking = time.time()
        model_for_budget = "unknown"
        estimated_input_tokens = 0

        try:
            # Log inizio esecuzione
            execution_start_log = {
                "timestamp": datetime.now().isoformat(), "event": "task_started",
                "task_id": task_id, "agent_id": agent_id, "workspace_id": workspace_id,
                "task_name": task_dict.get("name", "N/A")
            }
            self.execution_log.append(execution_start_log)
            await update_task_status(task_id, TaskStatus.IN_PROGRESS.value, {"detail": "Execution started by worker"})

            # Recupera dati agente per determinare il modello
            agent_data_db = await get_agent(agent_id)
            if not agent_data_db:
                raise ValueError(f"Agent {agent_id} not found in database.")

            # Determina il modello LLM da usare (e per il budget)
            llm_config = agent_data_db.get("llm_config", {})
            model_for_budget = llm_config.get("model")
            if not model_for_budget:
                seniority_map = {"junior": "gpt-4.1-nano", "senior": "gpt-4.1-mini", "expert": "gpt-4.1"}
                model_for_budget = seniority_map.get(agent_data_db.get("seniority", "senior"), self.budget_tracker.default_model)
            logger.info(f"Executing task {task_id} ('{task_dict.get('name')}') with agent {agent_id} (Role: {agent_data_db.get('role', 'N/A')}) using model {model_for_budget}")

            # Stima input tokens
            task_input_text = f"{task_dict.get('name', '')} {task_dict.get('description', '')}"
            estimated_input_tokens = max(1, len(task_input_text) // 4)

            # Costruisci l'oggetto Task Pydantic
            try:
                task_pydantic_obj = Task(
                    id=UUID(task_id),
                    workspace_id=UUID(workspace_id),
                    agent_id=UUID(agent_id),
                    name=task_dict.get("name", "N/A"),
                    description=task_dict.get("description", ""),
                    status=TaskStatus.IN_PROGRESS,
                    created_at=datetime.fromisoformat(task_dict["created_at"]) if task_dict.get("created_at") else datetime.now(),
                    updated_at=datetime.now(),
                    result=task_dict.get("result"),
                )
            except (ValueError, TypeError, KeyError) as pydantic_error:
                logger.error(f"Error creating Pydantic Task object for task {task_id}: {pydantic_error}", exc_info=True)
                raise ValueError("Internal error preparing task object.") from pydantic_error

            # --- ESECUZIONE EFFETTIVA DEL TASK ---
            result_from_agent: Dict[str, Any] = await manager.execute_task(task_pydantic_obj.id)
            # ------------------------------------

            execution_time = time.time() - start_time_tracking

            # Estrai/stima output tokens e gestisci il risultato
            result_output = result_from_agent.get("output", "Task completed without explicit output.") if isinstance(result_from_agent, dict) else str(result_from_agent)
            actual_output_tokens = result_from_agent.get("usage", {}).get("output_tokens")
            estimated_output_tokens = actual_output_tokens if actual_output_tokens is not None else max(1, len(str(result_output)) // 4)
            actual_input_tokens = result_from_agent.get("usage", {}).get("input_tokens")
            final_input_tokens = actual_input_tokens if actual_input_tokens is not None else estimated_input_tokens

            # Log budget usage
            usage_record = self.budget_tracker.log_usage(
                agent_id=agent_id, model=model_for_budget,
                input_tokens=final_input_tokens,
                output_tokens=estimated_output_tokens,
                task_id=task_id
            )

            # Prepara il payload del risultato da salvare nel DB
            task_result_payload_for_db = {
                "output": result_output,
                "status_detail": "completed_successfully",
                "execution_time_seconds": round(execution_time, 2),
                "model_used": model_for_budget,
                "tokens_used": {
                     "input": final_input_tokens,
                     "output": estimated_output_tokens,
                     "estimated": actual_input_tokens is None or actual_output_tokens is None
                 },
                "cost_estimated": usage_record["total_cost"],
                "agent_metadata": result_from_agent.get("metadata")
            }
            await update_task_status(task_id, TaskStatus.COMPLETED.value, task_result_payload_for_db)

            # Log fine esecuzione
            result_summary = (str(result_output)[:150] + "...") if len(str(result_output)) > 150 else str(result_output)
            execution_end_log = {
                "timestamp": datetime.now().isoformat(), "event": "task_completed",
                "task_id": task_id, "agent_id": agent_id, "workspace_id": workspace_id,
                "task_name": task_dict.get("name", "N/A"),
                "execution_time": round(execution_time, 2),
                "cost": usage_record["total_cost"], "model": model_for_budget,
                "tokens_used": {"input": usage_record["input_tokens"], "output": usage_record["output_tokens"]},
                "result_summary": result_summary
            }
            self.execution_log.append(execution_end_log)
            logger.info(f"Task {task_id} completed. Cost: ${usage_record['total_cost']:.6f}, Time: {execution_time:.2f}s")

            # --- Trigger post-esecuzione (es. auto-generazione) ---
            try:
                # Crea un oggetto Task Pydantic aggiornato con lo stato COMPLETED e il risultato
                completed_task_pydantic_obj_for_handler = Task(
                    id=UUID(task_id), workspace_id=UUID(workspace_id), agent_id=UUID(agent_id),
                    name=task_dict.get("name", "N/A"), description=task_dict.get("description", ""),
                    status=TaskStatus.COMPLETED,
                    result=task_result_payload_for_db,
                    created_at=task_pydantic_obj.created_at,
                    updated_at=datetime.now(),
                )
                # Chiama l'handler passando l'oggetto Task completato e il workspace ID
                await self.enhanced_handler.handle_task_completion(
                    completed_task=completed_task_pydantic_obj_for_handler,
                    task_result=task_result_payload_for_db,
                    workspace_id=workspace_id
                )
                logger.info(f"Post-completion handler (e.g., auto-generation analysis) triggered for task {task_id}")
            except Exception as auto_error:
                logger.error(f"Error in post-completion handler for task {task_id}: {auto_error}", exc_info=True)
            # -----------------------------------------------------

        except Exception as e:
            # Gestione centralizzata degli errori durante l'esecuzione
            logger.error(f"Critical error executing task {task_id}: {e}", exc_info=True)
            execution_time_failed = time.time() - start_time_tracking

            # Stima conservativa dei token per il budget in caso di fallimento
            input_tokens_failed = estimated_input_tokens if estimated_input_tokens > 0 else 0
            output_tokens_failed = 50

            # Logga comunque il costo stimato del tentativo fallito
            usage_record_failed = self.budget_tracker.log_usage(
                agent_id=agent_id, model=model_for_budget,
                input_tokens=input_tokens_failed,
                output_tokens=output_tokens_failed, task_id=task_id
            )

            # Prepara payload di errore per il DB
            error_payload_for_db = {
                "error": str(e),
                "status_detail": "failed_during_execution",
                "execution_time_seconds": round(execution_time_failed, 2),
                "cost_estimated": usage_record_failed["total_cost"]
            }
            # Aggiorna lo stato del task a FAILED nel DB
            try:
                 await update_task_status(task_id, TaskStatus.FAILED.value, error_payload_for_db)
            except Exception as db_update_err:
                 logger.error(f"Failed to update task status to FAILED for task {task_id} after execution error: {db_update_err}")

            # Log dell'evento di fallimento
            execution_error_log = {
                "timestamp": datetime.now().isoformat(), "event": "task_failed",
                "task_id": task_id, "agent_id": agent_id, "workspace_id": workspace_id,
                "task_name": task_dict.get("name", "N/A"),
                "execution_time": round(execution_time_failed, 2),
                "cost": usage_record_failed["total_cost"], "error": str(e), "model": model_for_budget
            }
            self.execution_log.append(execution_error_log)

    async def create_initial_workspace_task(self, workspace_id: str) -> Optional[str]:
        """Creates the very first task for a workspace, typically assigning it to a project manager role."""
        try:
            workspace = await get_workspace(workspace_id)
            if not workspace:
                logger.error(f"Workspace {workspace_id} not found when trying to create initial task.")
                return None

            agents = await db_list_agents(workspace_id)
            if not agents:
                logger.warning(f"No agents found for workspace {workspace_id}. Cannot create initial task. Workspace might need agent setup.")
                return None

            # Identifica l'agente "manager" o prendi il primo
            pm_agent = next((agent for agent in agents if any(keyword in agent.get("role", "").lower() for keyword in ["project", "coordinator", "manager", "lead"])), agents[0])
            pm_agent_id = pm_agent["id"]
            pm_agent_role = pm_agent.get("role", "Agent")

            logger.info(f"Selected agent {pm_agent_id} ({pm_agent_role}) to receive the initial task for workspace {workspace_id}.")

            # Descrizione dettagliata per il task iniziale, incoraggiando la pianificazione e delega
            task_description = f"""
            **Project Initialization: {workspace.get('name', 'Untitled Project')}**

            **Workspace Goal:** {workspace.get('goal', 'No goal specified.')}
            **Budget Info:** Max Amount: {workspace.get('budget', {}).get('max_amount', 'N/A')} {workspace.get('budget', {}).get('currency', '')}, Strategy: {workspace.get('budget', {}).get('strategy', 'N/A')}

            **Your Role:** {pm_agent_role}

            **Initial Objectives:**
            1.  **Analyze:** Deeply understand the project goal, requirements, constraints, and deliverables based on the workspace information.
            2.  **Plan:** Develop a high-level project plan. Break down the goal into major phases or milestones. Identify key sub-tasks within the initial phase.
            3.  **Identify Resources:** Review the available team members (other agents in this workspace, if any) and their potential roles.
            4.  **Delegate:** Using the appropriate tools/functions (e.g., 'create_task_for_agent'), create and assign the first set of specific, actionable tasks to yourself and/or other relevant agents based on your plan. *This is crucial for starting the workflow.*
            5.  **Setup Communication:** Define basic communication or handoff protocols if multiple agents need to collaborate soon.
            6.  **Report:** As the output of this task, provide a concise summary of your initial plan, the first set of tasks you have created/delegated, and any immediate questions or roadblocks.

            **Team Agents Overview:**
            """
            # Aggiungi un riepilogo degli altri agenti se presenti
            other_agents = [a for a in agents if a["id"] != pm_agent_id]
            if other_agents:
                task_description += "\n".join([f"- Agent ID: {a['id']}, Role: {a.get('role', 'N/A')}, Seniority: {a.get('seniority', 'N/A')}" for a in other_agents])
            else:
                task_description += "- You are currently the only agent assigned."

            task_description += """

            **Action Required:** Proceed with planning and delegation. Remember to use tools to create new tasks for others.
            """

            # Crea il task nel database
            initial_task_dict = await create_task(
                workspace_id=workspace_id,
                agent_id=pm_agent_id,
                name="Project Initialization and Planning",
                description=task_description.strip(),
                status=TaskStatus.PENDING.value,
            )

            if initial_task_dict and initial_task_dict.get("id"):
                task_id = initial_task_dict["id"]
                logger.info(f"Created initial task {task_id} for workspace {workspace_id}, assigned to agent {pm_agent_id}.")
                # Log evento di creazione
                creation_log = {
                    "timestamp": datetime.now().isoformat(), "event": "initial_task_created",
                    "task_id": task_id, "agent_id": pm_agent_id, "workspace_id": workspace_id,
                    "task_name": initial_task_dict.get("name"),
                    "assigned_role": pm_agent_role
                }
                self.execution_log.append(creation_log)
                return task_id
            else:
                logger.error(f"Database call create_task seemed to fail or returned invalid data for initial task in workspace {workspace_id}.")
                return None
        except Exception as e:
            logger.error(f"Error creating initial task for workspace {workspace_id}: {e}", exc_info=True)
            return None

    def get_recent_activity(self, workspace_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent execution log events, optionally filtered by workspace."""
        logs_to_filter = self.execution_log

        if workspace_id:
            try:
                 logs_to_filter = [log for log in logs_to_filter if log.get("workspace_id") == workspace_id]
            except ValueError:
                 logger.warning(f"Invalid workspace_id format '{workspace_id}' for filtering recent activity.")
                 return []

        # Ordina dal più recente al meno recente e limita
        logs_to_filter.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return logs_to_filter[:limit]

    def get_auto_generation_stats(self) -> Dict[str, Any]:
        """Get statistics specifically about auto-generated tasks or related events."""
        # Definisci gli eventi che indicano auto-generazione o handoff
        auto_gen_event_types = {
            "auto_task_generated",
            "follow_up_generated",
            "handoff_requested",
            "subtask_created_by_agent"
        }

        auto_gen_events = [
            log for log in self.execution_log
            if log.get("event") in auto_gen_event_types
        ]
        auto_gen_events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        # Conta per tipo di evento
        event_counts = {}
        for event_type in auto_gen_event_types:
            event_counts[event_type] = sum(1 for log in auto_gen_events if log.get("event") == event_type)

        return {
            "total_auto_generation_related_events": len(auto_gen_events),
            "event_type_counts": event_counts,
            "recent_auto_generation_events": auto_gen_events[:10],
            "auto_generation_enabled": True
        }

    def get_runaway_protection_status(self) -> Dict[str, Any]:
        """Ritorna lo stato della runaway protection"""
        return {
            "paused_workspaces": list(self.workspace_auto_generation_paused),
            "workspace_task_counts": self.workspace_task_counts,
            "last_runaway_check": self.last_runaway_check.isoformat() if self.last_runaway_check else None,
            "protection_enabled": True,
            "max_pending_tasks": self.max_pending_tasks_per_workspace,
            "max_handoff_percentage": self.max_handoff_percentage
        }

    def get_detailed_stats(self) -> Dict[str, Any]:
        """Gathers detailed operational statistics including runaway protection"""
        tasks_completed = 0
        tasks_failed = 0
        agent_activity: Dict[str, Dict[str, Any]] = {}

        # Processa il log di esecuzione per contare successi e fallimenti
        for log_entry in self.execution_log:
            event = log_entry.get("event")
            agent_id = log_entry.get("agent_id")
            task_id = log_entry.get("task_id")

            # Conta TUTTI i task completati/falliti, non solo quelli senza agent_id
            if event == "task_completed":
                tasks_completed += 1
            elif event == "task_failed":
                tasks_failed += 1

            # Continua solo se c'è un agent_id per le statistiche per agente
            if not agent_id:
                continue

            # Inizializza le statistiche per l'agente se non già presenti
            if agent_id not in agent_activity:
                agent_activity[agent_id] = {
                    "completed": 0,
                    "failed": 0,
                    "total_cost": 0.0,
                    "name": "Unknown",
                    "role": "Unknown"
                }

            # Aggiorna i conteggi per agente
            if event == "task_completed":
                agent_activity[agent_id]["completed"] += 1
            elif event == "task_failed":
                agent_activity[agent_id]["failed"] += 1

        # Arricchisci le statistiche degli agenti con il costo totale dal BudgetTracker
        all_agent_ids_in_stats = list(agent_activity.keys())
        for agent_id in all_agent_ids_in_stats:
             agent_total_cost = self.budget_tracker.get_agent_total_cost(agent_id)
             agent_activity[agent_id]["total_cost"] = round(agent_total_cost, 6)

        # Stato attuale dell'executor
        current_status = "stopped"
        if self.running:
            current_status = "paused" if self.paused else "running"

        base_stats = {
            "executor_status": current_status,
            "tasks_in_queue": self.task_queue.qsize(),
            "tasks_actively_processing": self.active_tasks_count,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "total_execution_log_entries": len(self.execution_log),
            "session_stats": { 
                "tasks_completed_successfully": tasks_completed,
                "tasks_failed": tasks_failed,
                "agent_activity": agent_activity
            },
            "budget_tracker_stats": {
                "tracked_agents_count": len(self.budget_tracker.usage_log),
            },
            "auto_generation_summary": self.get_auto_generation_stats()
        }
        
        # Aggiungi stats runaway protection
        base_stats.update({
            "runaway_protection": self.get_runaway_protection_status(),
            "workspace_health": {
                workspace_id: counts for workspace_id, counts in self.workspace_task_counts.items()
            }
        })
        
        return base_stats


# --- Global Instance ---
task_executor = TaskExecutor()

# --- Control Functions ---
async def start_task_executor():
    """Start the global task executor service."""
    await task_executor.start()

async def stop_task_executor():
    """Stop the global task executor service."""
    await task_executor.stop()

async def pause_task_executor():
    """Pause the global task executor."""
    await task_executor.pause()

async def resume_task_executor():
    """Resume the global task executor."""
    await task_executor.resume()

def get_executor_stats() -> Dict[str, Any]:
     """Get detailed statistics from the global task executor."""
     return task_executor.get_detailed_stats()

def get_recent_executor_activity(workspace_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
     """Get recent activity logs, optionally filtered by workspace."""
     return task_executor.get_recent_activity(workspace_id=workspace_id, limit=limit)

async def trigger_initial_workspace_task(workspace_id: str) -> Optional[str]:
    """Manually trigger the creation of an initial task for a specific workspace."""
    return await task_executor.create_initial_workspace_task(workspace_id)

# NUOVO: Endpoint per controllo manuale runaway
async def trigger_runaway_check() -> Dict[str, Any]:
    """Trigger manuale del check runaway protection"""
    await task_executor.periodic_runaway_check()
    return {
        "success": True,
        "message": "Runaway check completed",
        "protection_status": task_executor.get_runaway_protection_status()
    }

# NUOVO: Funzione per reset manuale di workspace pausato
async def reset_workspace_auto_generation(workspace_id: str) -> Dict[str, Any]:
    """Reset manuale dell'auto-generation per un workspace"""
    if workspace_id in task_executor.workspace_auto_generation_paused:
        await task_executor._resume_auto_generation_for_workspace(workspace_id)
        return {
            "success": True,
            "message": f"Auto-generation resumed for workspace {workspace_id}"
        }
    else:
        return {
            "success": False,
            "message": f"Auto-generation was not paused for workspace {workspace_id}"
        }