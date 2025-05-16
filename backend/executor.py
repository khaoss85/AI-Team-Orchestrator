# backend/executor.py - Versione fusa e rivista
import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set # Union rimossa se non strettamente necessaria
from uuid import UUID, uuid4
import json
import time
from collections import defaultdict, Counter
import difflib

# Import da moduli del progetto
from models import TaskStatus, Task, AgentStatus, WorkspaceStatus, Agent as AgentModelPydantic
# update_agent_status rimosso perché non utilizzato in questa classe
from database import (
    list_tasks,
    update_task_status,
    # update_agent_status,
    get_workspace,
    get_agent,
    list_agents as db_list_agents,
    create_task,
    get_active_workspaces,
    get_workspaces_with_pending_tasks,
    update_workspace_status
)
from ai_agents.manager import AgentManager
from task_analyzer import EnhancedTaskExecutor
from task_analyzer import get_enhanced_task_executor  # serve per disattivare/controllare l’analizzatore



logger = logging.getLogger(__name__)

# TODO: Considerare di spostare le costanti di configurazione (es. timeouts, limiti)
# in un file settings.py dedicato o gestirle tramite variabili d'ambiente documentate
# per una migliore manutenibilità e configurabilità.

# Simulata aggiunta a models.TaskStatus per la code review.
# In un progetto reale, questo andrebbe aggiunto all'effettivo Enum TaskStatus.
class TaskStatusPlaceholder: # Usato solo se TaskStatus non ha TIMED_OUT
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out" # Nuovo stato suggerito

    @classmethod
    def get_value(cls, status_member):
        """
        Ritorna sempre una stringa valida di stato.

        • Se riceve già una stringa, la restituisce.
        • Se riceve un Enum di `TaskStatus`, restituisce il suo `.value`.
        • Se riceve un attributo della stessa Placeholder, restituisce la stringa corrispondente.
        """
        # 1️⃣ Già stringa
        if isinstance(status_member, str):
            return status_member

        # 2️⃣ Enum vero proveniente da models.TaskStatus (ha .name e .value)
        if hasattr(status_member, "value"):
            return status_member.value

        # 3️⃣ Attributo della Placeholder (ha .name, ma non .value)
        return getattr(cls, status_member.name)


class BudgetTracker:
    """Tracks budget usage for agents with detailed cost monitoring"""

    def __init__(self):
        """Initialize the budget tracker."""
        self.usage_log: Dict[str, List[Dict[str, Any]]] = {}
        self.token_costs = {
            "gpt-4.1": {"input": 0.03, "output": 0.06},
            "gpt-4.1-mini": {"input": 0.015, "output": 0.03},
            "gpt-4.1-nano": {"input": 0.01, "output": 0.02},
            "gpt-4-turbo": {"input": 0.02, "output": 0.04},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002}
        }
        self.default_model = "gpt-4.1-mini"
        self.default_costs = self.token_costs[self.default_model]

    def log_usage(self, agent_id: str, model: str, input_tokens: int, output_tokens: int, task_id: Optional[str] = None) -> Dict[str, Any]:
        """Log token usage and associated costs"""
        if agent_id not in self.usage_log:
            self.usage_log[agent_id] = []

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
        """Calculate total cost for agent"""
        if agent_id not in self.usage_log:
            return 0.0
        return sum(record["total_cost"] for record in self.usage_log[agent_id])

    def get_workspace_total_cost(self, workspace_id: str, agent_ids: List[str]) -> Dict[str, Any]:
        """Calculate workspace total cost. Il calcolo dei total_tokens è mantenuto poiché restituito."""
        total_cost = 0.0
        agent_costs = {}
        total_tokens = {"input": 0, "output": 0} # Mantenuto

        for agent_id in agent_ids:
            agent_total_cost = self.get_agent_total_cost(agent_id)
            agent_costs[agent_id] = round(agent_total_cost, 6)
            total_cost += agent_total_cost

            if agent_id in self.usage_log:
                for record in self.usage_log[agent_id]:
                    total_tokens["input"] += record["input_tokens"]
                    total_tokens["output"] += record["output_tokens"]

        return {
            "workspace_id": workspace_id,
            "total_cost": round(total_cost, 6),
            "agent_costs": agent_costs,
            "total_tokens": total_tokens, # Mantenuto
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
    """Enhanced Task Executor with anti-loop protection and runaway monitoring"""

    def __init__(self):
        """Initialize the task executor."""
        self.running = False
        self.paused = False
        self.pause_event = asyncio.Event()
        self.pause_event.set()

        self.workspace_managers: Dict[UUID, AgentManager] = {}
        self.budget_tracker = BudgetTracker()
        self.execution_log: List[Dict[str, Any]] = []

        # ANTI-LOOP CONFIGURATIONS
        self.max_concurrent_tasks: int = 1
        self.max_tasks_per_workspace_anti_loop: int = 10
        self.task_timeout: int = 120  # seconds
        self.max_delegation_depth: int = 2

        # Tracking per anti-loop
        self.task_completion_tracker: Dict[str, Set[str]] = defaultdict(set)
        self.delegation_chain_tracker: Dict[str, List[str]] = defaultdict(list)
        self.workspace_anti_loop_task_counts: Dict[str, int] = defaultdict(int)

        self.last_cleanup: datetime = datetime.now()

        # Queue configuration
        self.max_queue_size: int = self.max_concurrent_tasks * 5
        self.active_tasks_count: int = 0
        self.task_queue: asyncio.Queue = asyncio.Queue(maxsize=self.max_queue_size)
        self.worker_tasks: List[asyncio.Task] = []

        self.enhanced_handler = EnhancedTaskExecutor()
        self.auto_generation_enabled: bool = False # Non persiste tra riavvii

        # RUNAWAY PROTECTION CONFIGURATIONS
        self.workspace_auto_generation_paused: Set[str] = set()
        self.last_runaway_check: Optional[datetime] = None
        self.max_pending_tasks_per_workspace: int = int(os.getenv("MAX_PENDING_TASKS_PER_WORKSPACE", 50))
        self.runaway_check_interval: int = 300  # seconds

    async def start(self):
        if self.running:
            logger.warning("Task executor already running")
            return
        self.running = True
        self.paused = False
        self.pause_event.set()
        self.execution_log = []

        logger.info(f"Starting task executor (anti-loop & runaway protection mode)")
        logger.info(f"Max concurrent anti-loop tasks: {self.max_concurrent_tasks}")
        logger.info(f"Task timeout: {self.task_timeout}s")
        logger.info(f"Global auto-generation: {'ENABLED' if self.auto_generation_enabled else 'DISABLED'}")
        logger.info(f"Runaway check interval: {self.runaway_check_interval}s")

        self.worker_tasks = [asyncio.create_task(self._anti_loop_worker()) for _ in range(self.max_concurrent_tasks)]
        asyncio.create_task(self.execution_loop())
        logger.info("Task executor started successfully.")

    async def stop(self):
        if not self.running:
            logger.warning("Task executor is not running.")
            return
        logger.info("Stopping task executor...")
        self.running = False
        self.paused = True
        self.pause_event.set()

        for _ in range(len(self.worker_tasks)):
            try:
                await asyncio.wait_for(self.task_queue.put(None), timeout=2.0)
            except asyncio.TimeoutError:
                logger.warning("Timeout sending stop signal to anti-loop task queue")
            except asyncio.QueueFull:
                logger.warning("Anti-loop task queue full while sending stop signal.")

        if self.worker_tasks:
            results = await asyncio.gather(*self.worker_tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception) and not isinstance(result, asyncio.CancelledError):
                    logger.error(f"Anti-loop worker task {i} finished with error during stop: {result}", exc_info=result)
        self.worker_tasks = []
        logger.info("Task executor stopped.")

    async def pause(self):
        if not self.running:
            logger.warning("Cannot pause: Task executor is not running.")
            return
        if self.paused:
            logger.info("Task executor is already paused.")
            return
        self.paused = True
        self.pause_event.clear()
        logger.info("Task executor paused.")

    async def resume(self):
        if not self.running:
            logger.warning("Cannot resume: Task executor is not running.")
            return
        if not self.paused:
            logger.info("Task executor is already running (not paused).")
            return
        self.paused = False
        self.pause_event.set()
        logger.info("Task executor resumed.")

    async def _anti_loop_worker(self):
        worker_id = uuid4()
        logger.info(f"Anti-loop worker {worker_id} started")
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
                    logger.info(f"Anti-loop worker {worker_id} received termination signal.")
                    break

                task_id = task_dict.get("id", "UnknownID")
                workspace_id = task_dict.get("workspace_id", "UnknownWS")
                logger.info(f"Worker {worker_id} picking up task: {task_id} from W: {workspace_id} (Q: {self.task_queue.qsize()})")

                if not await self._validate_task_execution(task_dict):
                    logger.warning(f"Worker {worker_id} skipping task {task_id} - failed anti-loop validation.")
                    self.task_queue.task_done()
                    await asyncio.sleep(0.05) # Piccolo sleep per evitare tight-loop su task invalidi
                    continue

                self.active_tasks_count += 1
                try:
                    if manager is None:
                        raise ValueError(f"Task {task_id} with null manager for worker {worker_id}.")
                    await self._execute_task_with_anti_loop_and_tracking(manager, task_dict)
                except Exception as e_exec:
                    logger.error(f"Worker {worker_id} critical error for task {task_id}: {e_exec}", exc_info=True)
                    await self._force_complete_task(task_dict, f"Critical worker error: {str(e_exec)[:200]}",
                                                    status_to_set=TaskStatusPlaceholder.get_value(TaskStatusPlaceholder.FAILED)) # Fallito
                finally:
                    self.active_tasks_count -= 1
                    self.task_queue.task_done()
                    logger.info(f"Worker {worker_id} finished task: {task_id}. Active: {self.active_tasks_count}")
                    if workspace_id and task_id: # Assicura validità
                        self.task_completion_tracker[workspace_id].add(task_id)
            except asyncio.CancelledError:
                logger.info(f"Anti-loop worker {worker_id} cancelled.")
                break
            except Exception as e_worker:
                logger.error(f"Unhandled error in anti-loop worker {worker_id}: {e_worker}", exc_info=True)
                await asyncio.sleep(5)
        logger.info(f"Anti-loop worker {worker_id} exiting.")

    async def _validate_task_execution(self, task_dict: Dict[str, Any]) -> bool:
        task_id = task_dict.get("id")
        workspace_id = task_dict.get("workspace_id")
        # task_name = task_dict.get("name", "") # loop_indicators rimossa

        if not task_id or not workspace_id:
            logger.error(f"Invalid task data for validation: id={task_id}, ws={workspace_id}")
            return False

        if task_id in self.task_completion_tracker.get(workspace_id, set()):
            logger.warning(f"Anti-loop: Task {task_id} in W:{workspace_id} already completed. Skipping.")
            current_status = task_dict.get("status")
            if current_status == TaskStatusPlaceholder.get_value(TaskStatusPlaceholder.PENDING):
                 await self._force_complete_task(task_dict, "Skipped: Already completed (tracker)",
                                                 status_to_set=TaskStatusPlaceholder.get_value(TaskStatusPlaceholder.COMPLETED))
            return False

        current_anti_loop_count = self.workspace_anti_loop_task_counts.get(workspace_id, 0)
        if current_anti_loop_count >= self.max_tasks_per_workspace_anti_loop:
            logger.warning(f"Anti-loop: W:{workspace_id} task limit ({current_anti_loop_count}/{self.max_tasks_per_workspace_anti_loop}). Task {task_id} skip.")
            return False

        if task_id in self.delegation_chain_tracker:
            depth = len(self.delegation_chain_tracker[task_id])
            if depth > self.max_delegation_depth:
                logger.warning(f"Anti-loop: Task {task_id} exceeded delegation depth ({depth}/{self.max_delegation_depth}). Forcing completion.")
                await self._force_complete_task(task_dict, "Delegation depth exceeded",
                                                status_to_set=TaskStatusPlaceholder.get_value(TaskStatusPlaceholder.FAILED)) # Fallito per depth
                return False
        return True

    async def _force_complete_task(self, task_dict: Dict[str, Any], reason: str, status_to_set: str = TaskStatusPlaceholder.get_value(TaskStatusPlaceholder.COMPLETED)):
        task_id = task_dict.get("id")
        workspace_id = task_dict.get("workspace_id")

        if not task_id:
            logger.error(f"Cannot force complete task: ID missing. Reason: {reason}")
            return

        completion_result = {
            "output": f"Task forcibly finalized: {reason}",
            "status_detail": f"forced_{status_to_set.lower()}",
            "force_completed": True,
            "completion_reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        try:
            await update_task_status(task_id, status_to_set, completion_result)
            logger.info(f"Forcibly finalized task {task_id} as {status_to_set}: {reason}")
            if workspace_id:
                self.task_completion_tracker[workspace_id].add(task_id)
        except Exception as e:
            logger.error(f"Error force finalizing task {task_id}: {e}")

    async def _execute_task_with_anti_loop_and_tracking(self, manager: AgentManager, task_dict: Dict[str, Any]):
        task_id = task_dict.get("id")
        workspace_id = task_dict.get("workspace_id")
        agent_id = task_dict.get("agent_id")
        task_name = task_dict.get("name", "N/A")

        if not all([task_id, agent_id, workspace_id]):
            missing = [k for k,v in {'task_id':task_id, 'agent_id':agent_id, 'workspace_id':workspace_id}.items() if not v]
            error_msg = f"Task data incomplete for execution: missing {', '.join(missing)}."
            logger.error(error_msg)
            if task_id:
                await self._force_complete_task({"id": task_id, "workspace_id": workspace_id}, error_msg,
                                                status_to_set=TaskStatusPlaceholder.get_value(TaskStatusPlaceholder.FAILED))
            return

        start_time_tracking = time.time()
        model_for_budget = self.budget_tracker.default_model
        estimated_input_tokens = 0

        self.workspace_anti_loop_task_counts[workspace_id] = self.workspace_anti_loop_task_counts.get(workspace_id, 0) + 1

        try:
            execution_start_log = {
                "timestamp": datetime.now().isoformat(), "event": "task_execution_started",
                "task_id": task_id, "agent_id": agent_id, "workspace_id": workspace_id, "task_name": task_name
            }
            self.execution_log.append(execution_start_log)
            await update_task_status(task_id, TaskStatusPlaceholder.get_value(TaskStatusPlaceholder.IN_PROGRESS), {"detail": "Execution started by anti-loop worker"})

            agent_data_db = await get_agent(agent_id)
            if not agent_data_db:
                raise ValueError(f"Agent {agent_id} not found for task {task_id}.")

            llm_config = agent_data_db.get("llm_config", {})
            config_model = llm_config.get("model")
            if config_model and config_model in self.budget_tracker.token_costs:
                model_for_budget = config_model
            else:
                seniority_map = {"junior":"gpt-4.1-nano", "senior":"gpt-4.1-mini", "expert":"gpt-4.1"}
                model_for_budget = seniority_map.get(agent_data_db.get("seniority","senior"), self.budget_tracker.default_model)

            logger.info(f"Executing task {task_id} ('{task_name}') with agent {agent_id} (Role: {agent_data_db.get('role', 'N/A')}) using model {model_for_budget}")
            task_input_text = f"{task_name} {task_dict.get('description', '')}"
            estimated_input_tokens = max(1, len(task_input_text) // 4)

            task_obj_pydantic = Task(
                id=UUID(task_id), workspace_id=UUID(workspace_id), agent_id=UUID(agent_id),
                name=task_name, description=task_dict.get("description", ""),
                status=TaskStatusPlaceholder.get_value(TaskStatusPlaceholder.IN_PROGRESS),
                created_at=datetime.fromisoformat(task_dict["created_at"]) if task_dict.get("created_at") else datetime.now(),
                updated_at=datetime.now(), result=task_dict.get("result")
            )

            result_from_agent: Dict[str, Any] = {}
            task_final_status_val = TaskStatusPlaceholder.get_value(TaskStatusPlaceholder.COMPLETED) # Default
            try:
                result_from_agent = await asyncio.wait_for(
                    manager.execute_task(task_obj_pydantic.id), timeout=self.task_timeout
                )
                if not isinstance(result_from_agent, dict):
                    logger.warning(f"Task {task_id} returned non-dict: {type(result_from_agent)}. Wrapping.")
                    result_from_agent = {"output": str(result_from_agent), "status_detail": "wrapped_non_dict_result"}

            except asyncio.TimeoutError:
                execution_time = time.time() - start_time_tracking
                logger.warning(f"Task {task_id} timed out after {self.task_timeout}s. Finalizing as TIMED_OUT.")
                task_final_status_val = TaskStatusPlaceholder.get_value(TaskStatusPlaceholder.TIMED_OUT)
                timeout_result_payload = {
                    "output": f"Task forcibly finalized as TIMED_OUT after {self.task_timeout}s.",
                    "status_detail": "timed_out_by_executor",
                    "execution_time_seconds": round(execution_time, 2), "model_used": model_for_budget,
                    "tokens_used": {"input": estimated_input_tokens, "output": 0, "estimated": True},
                    "cost_estimated": self.budget_tracker.log_usage(agent_id, model_for_budget, estimated_input_tokens, 0, task_id)["total_cost"],
                    "timeout": True, "partial_result": True
                }
                await update_task_status(task_id, task_final_status_val, timeout_result_payload)
                self.execution_log.append({
                    "timestamp": datetime.now().isoformat(), "event": "task_execution_timeout",
                    "task_id": task_id, "agent_id": agent_id, "workspace_id": workspace_id, "task_name": task_name,
                    "execution_time": round(execution_time, 2), "cost": timeout_result_payload["cost_estimated"],
                    "reason": "timeout", "status_returned": task_final_status_val
                })
                return

            execution_time = time.time() - start_time_tracking
            result_output = result_from_agent.get("output", "Task completed by agent without explicit output.")
            actual_output_tokens = result_from_agent.get("usage", {}).get("output_tokens")
            estimated_output_tokens = actual_output_tokens if actual_output_tokens is not None else max(1, len(str(result_output)) // 4)
            actual_input_tokens = result_from_agent.get("usage", {}).get("input_tokens")
            final_input_tokens = actual_input_tokens if actual_input_tokens is not None else estimated_input_tokens

            usage_record = self.budget_tracker.log_usage(
                agent_id=agent_id, model=model_for_budget,
                input_tokens=final_input_tokens, output_tokens=estimated_output_tokens, task_id=task_id
            )

            agent_returned_status = result_from_agent.get("status", TaskStatusPlaceholder.get_value(TaskStatusPlaceholder.COMPLETED))
            if agent_returned_status not in [TaskStatusPlaceholder.get_value(TaskStatusPlaceholder.COMPLETED), TaskStatusPlaceholder.get_value(TaskStatusPlaceholder.FAILED)]:
                logger.warning(f"Agent for task {task_id} returned unconventional status '{agent_returned_status}'. Defaulting to COMPLETED.")
                task_final_status_val = TaskStatusPlaceholder.get_value(TaskStatusPlaceholder.COMPLETED)
            else:
                task_final_status_val = agent_returned_status

            task_result_payload_for_db = {
                "output": result_output,
                "status_detail": result_from_agent.get("status_detail", "completed_by_agent"),
                "execution_time_seconds": round(execution_time, 2), "model_used": model_for_budget,
                "tokens_used": {"input": final_input_tokens, "output": estimated_output_tokens, "estimated": actual_input_tokens is None or actual_output_tokens is None},
                "cost_estimated": usage_record["total_cost"], "agent_metadata": result_from_agent.get("metadata"),
                "force_completed": result_from_agent.get("force_completed", False),
                "completion_reason": result_from_agent.get("completion_reason")
            }
            await update_task_status(task_id, task_final_status_val, task_result_payload_for_db)

            result_summary = (str(result_output)[:150] + "...") if len(str(result_output)) > 150 else str(result_output)
            execution_end_log = {
                "timestamp": datetime.now().isoformat(), "event": "task_execution_completed",
                "task_id": task_id, "agent_id": agent_id, "workspace_id": workspace_id, "task_name": task_name,
                "status_returned": task_final_status_val, "execution_time": round(execution_time, 2),
                "cost": usage_record["total_cost"], "model": model_for_budget,
                "tokens_used": {"input": usage_record["input_tokens"], "output": usage_record["output_tokens"]},
                "result_summary": result_summary
            }
            self.execution_log.append(execution_end_log)
            logger.info(f"Task {task_id} finished (status: {task_final_status_val}). Cost: ${usage_record['total_cost']:.6f}, Time: {execution_time:.2f}s")

            if task_final_status_val == TaskStatusPlaceholder.get_value(TaskStatusPlaceholder.COMPLETED) and self.auto_generation_enabled and workspace_id not in self.workspace_auto_generation_paused:
                try:
                    completed_task_pydantic_obj = Task(
                        id=UUID(task_id), workspace_id=UUID(workspace_id), agent_id=UUID(agent_id),
                        name=task_name, description=task_dict.get("description", ""), status=TaskStatusPlaceholder.get_value(TaskStatusPlaceholder.COMPLETED),
                        result=task_result_payload_for_db, created_at=task_obj_pydantic.created_at, updated_at=datetime.now(),
                    )
                    logger.info(f"Calling enhanced_handler.handle_task_completion for task {task_id}")
                    await self.enhanced_handler.handle_task_completion(
                        completed_task=completed_task_pydantic_obj, task_result=task_result_payload_for_db, workspace_id=workspace_id
                    )
                    logger.info(f"Post-completion handler triggered for task {task_id}")
                except Exception as auto_error:
                    logger.error(f"Error in post-completion handler for task {task_id}: {auto_error}", exc_info=True)
            elif not self.auto_generation_enabled: logger.info(f"Skipping post-completion: global auto-gen disabled for {task_id}.")
            elif workspace_id in self.workspace_auto_generation_paused: logger.info(f"Skipping post-completion: auto-gen paused for W:{workspace_id} on task {task_id}.")

        except Exception as e:
            logger.error(f"Critical error processing task {task_id} ('{task_name}'): {e}", exc_info=True)
            execution_time_failed = time.time() - start_time_tracking
            input_tokens_failed = estimated_input_tokens if estimated_input_tokens > 0 else 10
            usage_record_failed = self.budget_tracker.log_usage(
                agent_id=agent_id if agent_id else "unknown_agent", model=model_for_budget,
                input_tokens=input_tokens_failed, output_tokens=0, task_id=task_id
            )
            error_payload_for_db = {
                "error": str(e)[:1000], "status_detail": "failed_during_execution_phase",
                "execution_time_seconds": round(execution_time_failed, 2), "cost_estimated": usage_record_failed["total_cost"]
            }
            final_fail_status = TaskStatusPlaceholder.get_value(TaskStatusPlaceholder.FAILED)
            try:
                await update_task_status(task_id, final_fail_status, error_payload_for_db)
                logger.info(f"Task {task_id} marked as FAILED due to execution error.")
            except Exception as db_update_err:
                logger.error(f"Failed to update task {task_id} to FAILED: {db_update_err}")

            self.execution_log.append({
                "timestamp": datetime.now().isoformat(), "event": "task_execution_failed",
                "task_id": task_id, "agent_id": agent_id, "workspace_id": workspace_id, "task_name": task_name,
                "execution_time": round(execution_time_failed, 2), "cost": usage_record_failed["total_cost"],
                "error": str(e)[:200], "model": model_for_budget, "status_returned": final_fail_status
            })
            if workspace_id: self.task_completion_tracker[workspace_id].add(task_id)


    async def execution_loop(self):
        while self.running:
            try:
                await self.pause_event.wait()
                if not self.running: break
                logger.debug("Main exec loop: processing pending, checking workspaces, runaway status.")
                await self.process_pending_tasks_anti_loop()
                if self.auto_generation_enabled: await self.check_for_new_workspaces()
                else: logger.debug("Skipping check_for_new_workspaces: global auto-gen disabled.")

                if (self.last_runaway_check is None or
                        (datetime.now() - self.last_runaway_check).total_seconds() > self.runaway_check_interval):
                    logger.info("Performing periodic runaway check...")
                    await self.periodic_runaway_check() # Questo metodo logga già internamente
                    self.last_runaway_check = datetime.now()

                if datetime.now() - self.last_cleanup > timedelta(minutes=5):
                    await self._cleanup_tracking_data()
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                logger.info("Main execution loop cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in main execution_loop: {e}", exc_info=True)
                await asyncio.sleep(30)
        logger.info("Main execution loop finished.")

    async def process_pending_tasks_anti_loop(self):
        if self.paused: return
        try:
            workspaces_with_pending = await get_workspaces_with_pending_tasks()
            if workspaces_with_pending:
                 logger.debug(f"Found {len(workspaces_with_pending)} Ws with pending tasks. Checking queue/health.")
            for workspace_id in workspaces_with_pending[:3]:
                if self.task_queue.full():
                    logger.warning(f"Anti-loop Q full ({self.task_queue.qsize()}/{self.max_queue_size}). Skip W processing.")
                    break
                await self.process_workspace_tasks_anti_loop_with_health_check(workspace_id)
        except Exception as e:
            logger.error(f"Error processing pending tasks for anti-loop Q: {e}", exc_info=True)

    async def process_workspace_tasks_anti_loop_with_health_check(self, workspace_id: str):
        if self.paused: return
        try:
            health_status = await self.check_workspace_health(workspace_id)
            if not health_status.get('is_healthy', True):
                health_issues = health_status.get('health_issues', ["Unknown health issue"])
                logger.warning(f"W:{workspace_id} health issues: {health_issues}. Auto-gen may be paused.")
                critical_issues = [iss for iss in health_issues if any(k in iss.lower() for k in ['excessive pending', 'high task creation', 'delegation loops'])]
                if critical_issues and workspace_id not in self.workspace_auto_generation_paused:
                    await self._pause_auto_generation_for_workspace(workspace_id, reason=f"Critical health: {'; '.join(critical_issues)}")
                    return

            if workspace_id in self.workspace_auto_generation_paused:
                if health_status.get('is_healthy') and health_status.get('task_counts', {}).get('pending', self.max_pending_tasks_per_workspace) < 10:
                    await self._resume_auto_generation_for_workspace(workspace_id)
                    logger.info(f"Auto-gen resumed for healthy W:{workspace_id}.")
                else:
                    logger.info(f"Auto-gen remains paused for W:{workspace_id}. Pending: {health_status.get('task_counts', {}).get('pending', 'N/A')}, Healthy: {health_status.get('is_healthy', False)}")
                    return

            current_anti_loop_proc_count = self.workspace_anti_loop_task_counts.get(workspace_id, 0)
            if current_anti_loop_proc_count >= self.max_tasks_per_workspace_anti_loop:
                logger.warning(f"W:{workspace_id} at anti-loop limit ({current_anti_loop_proc_count}/{self.max_tasks_per_workspace_anti_loop}). Skip queueing.")
                return

            manager = await self.get_agent_manager(workspace_id)
            if not manager:
                logger.error(f"No agent manager for W:{workspace_id}. Cannot queue tasks.")
                return

            tasks_from_db = await list_tasks(workspace_id)
            pending_tasks_dicts = [t for t in tasks_from_db if t.get("status") == TaskStatusPlaceholder.get_value(TaskStatusPlaceholder.PENDING)]
            if not pending_tasks_dicts: return

            task_to_queue_dict = pending_tasks_dicts[0] # FIFO based on DB order for now
            task_id_to_queue = task_to_queue_dict.get("id")

            if not await self._validate_task_execution(task_to_queue_dict): # Pre-queue validation
                logger.warning(f"Pre-queue validation failed for task {task_id_to_queue} in W:{workspace_id}. Not queueing.")
                return
            try:
                self.task_queue.put_nowait((manager, task_to_queue_dict))
                logger.info(f"Queued task {task_id_to_queue} from W:{workspace_id}. Q size: {self.task_queue.qsize()}")
            except asyncio.QueueFull:
                logger.warning(f"Anti-loop Q full. Could not queue task {task_id_to_queue} from W:{workspace_id}.")
        except Exception as e:
            logger.error(f"Error processing W:{workspace_id} tasks (with health check): {e}", exc_info=True)

    async def _cleanup_tracking_data(self):
        logger.info("Performing cleanup of executor tracking data...")
        self.last_cleanup = datetime.now() # Marcatore di inizio cleanup

        max_log_entries = 200
        if len(self.execution_log) > max_log_entries:
            self.execution_log = self.execution_log[-max_log_entries:]
            logger.debug(f"Cleaned execution_log, kept last {max_log_entries}.")

        max_completed_per_ws = 100
        for workspace_id in list(self.task_completion_tracker.keys()):
            if len(self.task_completion_tracker[workspace_id]) > max_completed_per_ws * 2: # Soglia per reset drastico
                logger.warning(f"Task completion tracker for W:{workspace_id} has {len(self.task_completion_tracker[workspace_id])} (>{max_completed_per_ws*2}). Resetting.")
                self.task_completion_tracker[workspace_id] = set() # Reset
            elif len(self.task_completion_tracker[workspace_id]) > max_completed_per_ws :
                 logger.info(f"Task completion tracker for W:{workspace_id} has {len(self.task_completion_tracker[workspace_id])} entries. Consider more granular cleanup if grows further.")


        for task_id in list(self.delegation_chain_tracker.keys()):
            if len(self.delegation_chain_tracker[task_id]) > self.max_delegation_depth * 2:
                del self.delegation_chain_tracker[task_id]
                logger.debug(f"Removed long delegation chain for task {task_id}.")

        if not hasattr(self, "_cleanup_cycle_count"): self._cleanup_cycle_count = 0
        self._cleanup_cycle_count +=1
        if self._cleanup_cycle_count % 12 == 0: # Circa ogni ora
            logger.info("Periodic reset of workspace_anti_loop_task_counts.")
            self.workspace_anti_loop_task_counts = defaultdict(int)
        logger.info("Tracking data cleanup finished.")

    async def get_agent_manager(self, workspace_id: str) -> Optional[AgentManager]:
        try: workspace_uuid = UUID(workspace_id)
        except ValueError:
            logger.error(f"Invalid workspace ID format: {workspace_id}. Cannot get/create manager.")
            return None
        if workspace_uuid in self.workspace_managers: return self.workspace_managers[workspace_uuid]
        logger.info(f"Creating new AgentManager for workspace {workspace_id}.")
        try:
            manager = AgentManager(workspace_uuid)
            if await manager.initialize():
                self.workspace_managers[workspace_uuid] = manager
                logger.info(f"Initialized agent manager for workspace {workspace_id}")
                return manager
            else:
                logger.error(f"Failed to initialize agent manager for workspace {workspace_id}.")
                return None
        except Exception as e:
            logger.error(f"Exception creating agent manager for W:{workspace_id}: {e}", exc_info=True)
            return None

    async def check_workspace_health(self, workspace_id: str) -> Dict[str, Any]:
        try:
            all_tasks_db = await list_tasks(workspace_id)
            agents_db = await db_list_agents(workspace_id)
            task_counts = Counter(t.get("status") for t in all_tasks_db)
            task_counts['total'] = len(all_tasks_db)

            pattern_analysis = self._analyze_task_patterns(all_tasks_db, workspace_id)
            health_issues = []
            if task_counts[TaskStatusPlaceholder.get_value(TaskStatusPlaceholder.PENDING)] > self.max_pending_tasks_per_workspace:
                health_issues.append(f"Excessive pending: {task_counts[TaskStatusPlaceholder.get_value(TaskStatusPlaceholder.PENDING)]}/{self.max_pending_tasks_per_workspace}")
            creation_velocity = self._calculate_task_creation_velocity(all_tasks_db)
            if creation_velocity > 5.0: health_issues.append(f"High task creation: {creation_velocity:.1f}/min")
            if pattern_analysis['repeated_patterns']: health_issues.append(f"Repeated task names: {pattern_analysis['repeated_patterns']}")
            if pattern_analysis['delegation_loops']: health_issues.append(f"Delegation loops: {pattern_analysis['delegation_loops']}")
            if pattern_analysis['failed_handoffs'] > 3: health_issues.append(f"High handoff failures: {pattern_analysis['failed_handoffs']}")
            if pattern_analysis['same_role_recursion']: health_issues.append(f"Same-role recursion: {pattern_analysis['same_role_recursion']}")

            active_agent_ids = {agent['id'] for agent in agents_db}
            orphaned_tasks_count = sum(1 for t in all_tasks_db if not t.get('agent_id') or t.get('agent_id') not in active_agent_ids)
            if orphaned_tasks_count > 0: health_issues.append(f"Orphaned tasks: {orphaned_tasks_count}")

            health_score = self._calculate_improved_health_score(task_counts, health_issues, creation_velocity, pattern_analysis)
            return {'workspace_id': workspace_id, 'task_counts': dict(task_counts), 'health_issues': health_issues,
                    'health_score': round(health_score, 2), 'is_healthy': not health_issues and health_score > 70,
                    'auto_generation_paused': workspace_id in self.workspace_auto_generation_paused,
                    'pattern_analysis': pattern_analysis, 'creation_velocity': round(creation_velocity, 2)}
        except Exception as e:
            logger.error(f"Error checking W:{workspace_id} health: {e}", exc_info=True)
            return {'workspace_id': workspace_id, 'error': str(e), 'is_healthy': False, 'health_score': 0}

    def _analyze_task_patterns(self, tasks_db: List[Dict], workspace_id_for_logs: str) -> Dict[str, Any]:
        task_names = [t.get("name", "") for t in tasks_db]
        name_counts = Counter(task_names)
        repeated_patterns = {name: count for name, count in name_counts.items() if count > 3 and name}
        delegation_graph, delegation_loops_details = defaultdict(list), []
        recent_activity = self.get_recent_activity(workspace_id=workspace_id_for_logs, limit=100)

        for activity in recent_activity:
            if activity.get('event') == 'subtask_delegated':
                details = activity.get('details', {})
                source = details.get('delegated_by_agent_name', '')
                target = details.get('assigned_agent_name', '')
                if source and target: delegation_graph[source].append(target)
        for source, targets in delegation_graph.items():
            for target in targets:
                if source in delegation_graph.get(target, []):
                    loop_desc = f"{source} <-> {target}"
                    if loop_desc not in delegation_loops_details: delegation_loops_details.append(loop_desc)

        failed_handoffs_count = sum(1 for act in recent_activity if act.get('event') == 'handoff_failed' or (act.get('event') == 'task_failed' and "handoff" in act.get('task_name', '').lower()))
        same_role_recursion_details = []
        for act in recent_activity:
             if act.get('event') == 'subtask_delegated':
                details = act.get('details', {})
                s_role, t_role = details.get('source_agent_role','').lower(), details.get('target_agent_role_or_request','').lower()
                if s_role and t_role and s_role == t_role :
                    desc = f"Role '{s_role}' to same role"
                    if desc not in same_role_recursion_details: same_role_recursion_details.append(desc)
        description_clusters = self._find_similar_task_descriptions(tasks_db)
        return {'repeated_patterns': repeated_patterns, 'delegation_loops': delegation_loops_details,
                'failed_handoffs': failed_handoffs_count, 'same_role_recursion': same_role_recursion_details,
                'description_clusters': description_clusters}

    def _find_similar_task_descriptions(self, tasks_db: List[Dict], threshold=0.8) -> List[Dict]:
        if not difflib: return []
        clusters, processed_indices = [], set()
        for i, task1_dict in enumerate(tasks_db):
            if i in processed_indices: continue
            desc1 = task1_dict.get('description', '')[:250].lower()
            if not desc1 or len(desc1) < 20: processed_indices.add(i); continue
            #current_cluster, processed_indices.add(i) = [task1_dict], None #Python trick
            current_cluster = [task1_dict]
            processed_indices.add(i)
            for j, task2_dict in enumerate(tasks_db[i+1:], start=i+1):
                if j in processed_indices: continue
                desc2 = task2_dict.get('description', '')[:250].lower()
                if not desc2 or len(desc2) < 20: processed_indices.add(j); continue
                if difflib.SequenceMatcher(None, desc1, desc2).ratio() >= threshold:
                    current_cluster.append(task2_dict); processed_indices.add(j)
            if len(current_cluster) > 1:
                clusters.append({'count': len(current_cluster), 'sample_names': [t.get('name','N/A') for t in current_cluster[:3]],
                                 'snippet': desc1[:100]+"...", 'threshold': threshold})
        return clusters

    def _calculate_task_creation_velocity(self, tasks_db: List[Dict], window_min=30) -> float:
        # Nota: per una gestione più robusta dei fusi orari e formati ISO complessi,
        # la libreria dateutil.parser.isoparse è raccomandata.
        if not tasks_db: return 0.0
        now_utc, recent_creations = datetime.utcnow(), []
        for task_dict in tasks_db:
            created_at_str = task_dict.get('created_at')
            if created_at_str:
                try:
                    dt = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    # Assicurati che dt sia offset-aware (UTC) se now_utc è offset-aware
                    if dt.tzinfo is None: dt = dt.replace(tzinfo=timedelta(0)) # Assume UTC se naive
                    if now_utc - dt < timedelta(minutes=window_min): recent_creations.append(dt)
                except ValueError: logger.warning(f"Parse error: {created_at_str} for task {task_dict.get('id')}")
        if len(recent_creations) < 2: return 0.0
        recent_creations.sort()
        span_sec = (recent_creations[-1] - recent_creations[0]).total_seconds()
        return (len(recent_creations) / (span_sec / 60.0)) if span_sec > 0 else 0.0

    def _calculate_improved_health_score( self, tc: Dict, hi: List[str], cv: float, pa: Dict ) -> float:
        s = 100.0; s -= len(hi) * 15
        if tc.get('total',0)>0:
            pr = tc.get(TaskStatusPlaceholder.get_value(TaskStatusPlaceholder.PENDING),0)/tc['total']
            if pr > 0.75: s -= (pr-0.75)*100
            elif pr > 0.5: s -= (pr-0.5)*50
            cr = tc.get(TaskStatusPlaceholder.get_value(TaskStatusPlaceholder.COMPLETED),0)/tc['total']
            if cr > 0.7: s += cr*10
        if cv > 10.0: s -= min((cv-10.0)*5,25)
        elif cv > 5.0: s -= min((cv-5.0)*3,15)
        if pa.get('repeated_patterns'): s -= min(len(pa['repeated_patterns'])*3,10)
        if pa.get('delegation_loops'): s -= min(len(pa['delegation_loops'])*10,30)
        if pa.get('description_clusters'): s -= min(len(pa['description_clusters'])*2,10)
        if pa.get('failed_handoffs',0)>2 : s -= min(pa['failed_handoffs']*2,10)
        return max(0.0, min(100.0, s))

    async def periodic_runaway_check(self):
        logger.info("Starting periodic runaway check...")
        try:
            active_ws_ids = await get_active_workspaces()
            if not active_ws_ids: logger.info("No active Ws for runaway check."); return {'status': 'no_active_workspaces'}
            actions, warnings = [], []
            for ws_id in active_ws_ids:
                hs = await self.check_workspace_health(ws_id)
                h_score, is_healthy, issues, pending = hs.get('health_score',100), hs.get('is_healthy',True), hs.get('health_issues',[]), hs.get('task_counts',{}).get(TaskStatusPlaceholder.get_value(TaskStatusPlaceholder.PENDING),0)
                critical = (h_score < 30 or pending > (self.max_pending_tasks_per_workspace*1.5) or any('high task creation rate' in i.lower() and float(i.split(':')[-1].replace('/min','').strip()) > 7.0 for i in issues if 'high task creation rate' in i.lower()))

                if critical and ws_id not in self.workspace_auto_generation_paused:
                    reason = f"Runaway: Score={h_score}, Pending={pending}, Issues:{issues[:2]}"
                    await self._pause_auto_generation_for_workspace(ws_id, reason=reason)
                    actions.append({'workspace_id': ws_id, 'action': 'paused_auto_gen', 'reason': reason})
                elif not is_healthy and h_score < 60 : warnings.append({'workspace_id': ws_id, 'health_score': h_score, 'issues': issues[:2]})
            if actions: logger.critical(f"RUNAWAY CHECK: {len(actions)} Ws paused: {actions}")
            if warnings: logger.warning(f"RUNAWAY CHECK: {len(warnings)} Ws warning: {warnings}")
            if not actions and not warnings: logger.info(f"Runaway check: All {len(active_ws_ids)} Ws stable.")
            return {'timestamp':datetime.now().isoformat(), 'checked':len(active_ws_ids),'actions':actions,'warnings':warnings,'paused_list':list(self.workspace_auto_generation_paused)}
        except Exception as e: logger.error(f"Error in periodic_runaway_check: {e}", exc_info=True); return {'error':str(e)}

    async def _pause_auto_generation_for_workspace(self, workspace_id: str, reason: str = "Runaway detected"):
        if workspace_id in self.workspace_auto_generation_paused: logger.info(f"Auto-gen for W:{workspace_id} already paused."); return
        self.workspace_auto_generation_paused.add(workspace_id)
        logger.critical(f"AUTO-GENERATION PAUSED for W:{workspace_id}. Reason: {reason}")
        try:
            ws_data = await get_workspace(workspace_id)
            if ws_data and ws_data.get("status") == WorkspaceStatus.ACTIVE.value: # Usa Enum.value
                await update_workspace_status(workspace_id, WorkspaceStatus.NEEDS_INTERVENTION.value)
                logger.info(f"W:{workspace_id} status to 'needs_intervention'.")
        except Exception as e: logger.error(f"Failed to update W:{workspace_id} status after pause: {e}")
        self.execution_log.append({"timestamp":datetime.now().isoformat(), "event":"workspace_auto_generation_paused", "workspace_id":workspace_id, "reason":reason})

    async def _resume_auto_generation_for_workspace(self, workspace_id: str):
        if workspace_id not in self.workspace_auto_generation_paused: logger.info(f"Auto-gen for W:{workspace_id} not paused."); return
        self.workspace_auto_generation_paused.remove(workspace_id)
        logger.info(f"AUTO-GENERATION RESUMED for W:{workspace_id}.")
        try:
            ws_data = await get_workspace(workspace_id)
            if ws_data and ws_data.get("status") == WorkspaceStatus.NEEDS_INTERVENTION.value:
                await update_workspace_status(workspace_id, WorkspaceStatus.ACTIVE.value)
                logger.info(f"W:{workspace_id} status back to 'active'.")
        except Exception as e: logger.error(f"Failed to update W:{workspace_id} status after resume: {e}")
        self.execution_log.append({"timestamp":datetime.now().isoformat(), "event":"workspace_auto_generation_resumed", "workspace_id":workspace_id})

    async def check_for_new_workspaces(self):
        if self.paused or not self.auto_generation_enabled:
            logger.debug("Skip check_for_new_workspaces: Paused or global auto-gen disabled."); return
        try:
            logger.debug("Checking for active Ws needing initial tasks...")
            active_ws_ids = await get_active_workspaces()
            for ws_id in active_ws_ids:
                if ws_id in self.workspace_auto_generation_paused:
                    logger.info(f"Skip initial task for W:{ws_id}: auto-gen paused for this W."); continue
                if not await list_tasks(ws_id):
                    ws_data = await get_workspace(ws_id)
                    if ws_data and ws_data.get("status") == WorkspaceStatus.ACTIVE.value:
                        logger.info(f"W:{ws_id} ('{ws_data.get('name')}') active, no tasks. Creating initial task.")
                        await self.create_initial_workspace_task(ws_id)
        except Exception as e: logger.error(f"Error in check_for_new_workspaces: {e}", exc_info=True)

    async def create_initial_workspace_task(self, workspace_id: str) -> Optional[str]:
        if not self.auto_generation_enabled: logger.info(f"Global auto-gen disabled. No initial task for W:{workspace_id}."); return None
        if workspace_id in self.workspace_auto_generation_paused: logger.info(f"Auto-gen paused for W:{workspace_id}. No initial task."); return None
        try:
            workspace = await get_workspace(workspace_id)
            if not workspace: logger.error(f"W:{workspace_id} not found for initial task."); return None
            agents = await db_list_agents(workspace_id)
            if not agents: logger.warning(f"No agents in W:{workspace_id}. No initial task."); return None
            team_analysis = self._analyze_team_composition(agents)
            lead_agent = self._select_project_lead(agents, team_analysis)
            if not lead_agent: logger.error(f"No suitable lead in W:{workspace_id} for initial task."); return None
            logger.info(f"Selected {lead_agent['name']} ({lead_agent['role']}) as lead for W:{workspace_id}.")
            desc = self._create_structured_initial_task_description(workspace, lead_agent, team_analysis)
            task_name = "Project Setup & Strategic Planning Kick-off"
            created_task = await create_task(workspace_id=str(workspace['id']), agent_id=str(lead_agent['id']), name=task_name, description=desc, status=TaskStatusPlaceholder.get_value(TaskStatusPlaceholder.PENDING))
            if created_task and created_task.get("id"):
                task_id = created_task["id"]
                logger.info(f"Created initial task {task_id} ('{task_name}') for W:{workspace_id}, to {lead_agent['name']}.")
                self.execution_log.append({"timestamp":datetime.now().isoformat(), "event":"initial_workspace_task_created", "task_id":task_id, "agent_id":lead_agent["id"], "workspace_id":workspace_id, "task_name":task_name, "assigned_role":lead_agent["role"]})
                return task_id
            else: logger.error(f"Failed to create initial task in DB for W:{workspace_id}. Resp: {created_task}"); return None
        except Exception as e: logger.error(f"Error creating initial task for W:{workspace_id}: {e}", exc_info=True); return None

    def _analyze_team_composition(self, agents_list: List[Dict]) -> Dict[str, Any]:
        comp = {'total_agents':len(agents_list), 'by_seniority':Counter(), 'by_role_type':Counter(), 'available_domains':set(), 'leadership_candidates':[], 'specialists':[]}
        s_lvls = ['junior','senior','expert']
        for ag in agents_list:
            sen = ag.get('seniority','junior').lower()
            if sen in s_lvls: comp['by_seniority'][sen]+=1
            role, r_type_assigned = ag.get('role','').lower(), False
            if any(t in role for t in ['manager','coordinator','lead','director','project head']): comp['by_role_type']['leadership']+=1; comp['leadership_candidates'].append(ag); r_type_assigned=True
            if 'analyst' in role: comp['by_role_type']['analyst']+=1; comp['specialists'].append(ag); r_type_assigned=True
            if 'researcher' in role: comp['by_role_type']['researcher']+=1; comp['specialists'].append(ag); r_type_assigned=True
            if 'developer' in role or 'engineer' in role: comp['by_role_type']['technical']+=1; comp['specialists'].append(ag); r_type_assigned=True
            if 'writer' in role or 'content' in role: comp['by_role_type']['content_creation']+=1; comp['specialists'].append(ag); r_type_assigned=True
            if not r_type_assigned and 'specialist' in role: comp['by_role_type']['specialist']+=1; comp['specialists'].append(ag)
            elif not r_type_assigned: comp['by_role_type']['other']+=1
            domain = self._extract_domain_from_role(role)
            if domain: comp['available_domains'].add(domain)
        comp['available_domains'] = sorted(list(comp['available_domains']))
        comp['leadership_candidates'].sort(key=lambda a: s_lvls.index(a.get('seniority','junior').lower()) if a.get('seniority','junior').lower() in s_lvls else -1, reverse=True)
        return comp

    def _select_project_lead(self, agents_list: List[Dict], team_analysis: Dict) -> Optional[Dict]:
        if team_analysis['leadership_candidates']: return team_analysis['leadership_candidates'][0]
        pot_leads = [ag for ag in team_analysis.get('specialists',[]) if ag.get('seniority') in ['expert','senior']]
        if pot_leads: pot_leads.sort(key=lambda a:['junior','senior','expert'].index(a.get('seniority','junior').lower()), reverse=True); return pot_leads[0]
        all_sen_exp = [ag for ag in agents_list if ag.get('seniority') in ['expert','senior']]
        if all_sen_exp: all_sen_exp.sort(key=lambda a:['junior','senior','expert'].index(a.get('seniority','junior').lower()), reverse=True); return all_sen_exp[0]
        return agents_list[0] if agents_list else None

    def _create_structured_initial_task_description(self, ws_dict: Dict, lead_ag_dict: Dict, team_an: Dict) -> str:
        ws_g, ws_b = ws_dict.get('goal','No goal provided.'), ws_dict.get('budget',{})
        b_str = f"{ws_b.get('max_amount','N/A')} {ws_b.get('currency','')} (Strategy: {ws_b.get('strategy','standard')})"
        desc = f"""**PROJECT KICK-OFF: STRATEGIC PLANNING & TASK DEFINITION**\n\n**Workspace Goal:** {ws_g}\n**Budget Overview:** {b_str}\n**Assigned Project Lead:** You ({lead_ag_dict.get('name','N/A')} - {lead_ag_dict.get('role','N/A')})\n\n**Core Responsibilities (Initial Task):**\n1. Analyze Workspace Goal: Break into 3-5 actionable phases/milestones.\n2. Define Key Deliverables: For each phase, specify measurable deliverables.\n3. Team & Resource Assessment: Review team comp; map skills to phases; ID gaps.\n4. High-Level Execution Plan: Outline phase sequence, dependencies, rough timelines.\n5. Define Initial Sub-Tasks: Create 2-3 specific, actionable sub-tasks for Phase 1.\n6. Communication Protocol: Briefly outline progress tracking & handoffs.\n\n**Team Composition Overview:**\n{self._format_team_composition_for_task_description(team_an)}\n\n**Expected Output (Submit as result):**\n* Document with: Phase breakdown, resource allocation ideas, 2-3 specific sub-tasks for Phase 1, coordination strategy notes.\n\n**CRITICAL GUIDELINES:**\n* Focus on planning & a few well-defined starter tasks.\n* Empower team: Delegate effectively post-planning.\n* This is planning; subsequent tasks execute the plan."""
        return desc.strip()

    def _format_team_composition_for_task_description(self, team_an: Dict) -> str:
        lines = [f"- Total Agents: {team_an['total_agents']}"]
        sen_str = ", ".join(f"{c} {lvl}" for lvl,c in team_an['by_seniority'].items() if c>0)
        if sen_str: lines.append(f"- Seniority Mix: {sen_str}")
        role_str = ", ".join(f"{c} {rt.replace('_',' ').title()}" for rt,c in team_an['by_role_type'].items() if c>0)
        if role_str: lines.append(f"- Role Types: {role_str}")
        if team_an['available_domains']: lines.append(f"- Key Domains: {', '.join(team_an['available_domains'])}")
        if team_an.get('specialists'):
            spec_samp = [f"{sp['name']} ({sp['role']})" for sp in team_an['specialists'][:3]]
            if spec_samp: lines.append(f"- Sample Specialists: {'; '.join(spec_samp)}")
        return "\n".join(lines)

    def _extract_domain_from_role(self, role_str: str) -> Optional[str]:
        rl = role_str.lower()
        dm = {'finance':['finance','financial','accountant','investment'], 'marketing':['marketing','seo','social media','campaign'],
              'sales':['sales','business development','client acquisition'], 'product':['product manage','ux design','ui design'],
              'technology':['software engineer','developer','it support','data scientist','cybersecurity'],
              'hr':['human resource','recruitment','talent acquisition'], 'legal':['legal counsel','lawyer','compliance'],
              'research':['researcher','analyst']}
        for domain, kws in dm.items():
            if any(kw in rl for kw in kws): return domain
        return None

    def get_recent_activity(self, workspace_id: Optional[str]=None, limit: int=50) -> List[Dict[str,Any]]:
        logs = [log for log in self.execution_log if not workspace_id or log.get("workspace_id") == workspace_id]
        return sorted(logs, key=lambda x: x.get("timestamp",""), reverse=True)[:limit]

    def get_detailed_stats(self) -> Dict[str, Any]:
        status = "running" if self.running and not self.paused else "paused" if self.paused else "stopped"
        base_stats = {"executor_status":status, "anti_loop_mode_active":True, "tasks_in_anti_loop_queue":self.task_queue.qsize(),
                      "active_tasks_in_anti_loop_workers":self.active_tasks_count, "max_concurrent_anti_loop_tasks":self.max_concurrent_tasks,
                      "anti_loop_task_timeout_seconds":self.task_timeout, "global_auto_generation_enabled":self.auto_generation_enabled,
                      "anti_loop_workspace_task_processing_counts":dict(self.workspace_anti_loop_task_counts),
                      "anti_loop_total_workspaces_tracked_completion":len(self.task_completion_tracker),
                      "anti_loop_total_delegation_chains_tracked":len(self.delegation_chain_tracker),
                      "total_execution_log_entries":len(self.execution_log)}

        completed_session = sum(1 for log in self.execution_log if log.get("event")=="task_execution_completed" and log.get("status_returned")==TaskStatusPlaceholder.get_value(TaskStatusPlaceholder.COMPLETED))
        failed_session = sum(1 for log in self.execution_log if log.get("event")=="task_execution_failed" or (log.get("event")=="task_execution_completed" and log.get("status_returned")==TaskStatusPlaceholder.get_value(TaskStatusPlaceholder.FAILED)))
        timeout_session = sum(1 for log in self.execution_log if log.get("event")=="task_execution_timeout")

        agent_activity = defaultdict(lambda: {"completed":0, "failed":0, "timed_out":0, "total_cost":0.0})
        for log in self.execution_log:
            aid = log.get("agent_id")
            if aid:
                if log.get("event")=="task_execution_completed" and log.get("status_returned")==TaskStatusPlaceholder.get_value(TaskStatusPlaceholder.COMPLETED): agent_activity[aid]["completed"]+=1
                elif log.get("event")=="task_execution_failed" or (log.get("event")=="task_execution_completed" and log.get("status_returned")==TaskStatusPlaceholder.get_value(TaskStatusPlaceholder.FAILED)): agent_activity[aid]["failed"]+=1
                elif log.get("event")=="task_execution_timeout": agent_activity[aid]["timed_out"]+=1
        for aid in agent_activity: agent_activity[aid]["total_cost"] = self.budget_tracker.get_agent_total_cost(aid)

        base_stats["session_task_summary"] = {"tasks_completed_successfully":completed_session, "tasks_failed":failed_session, "tasks_timed_out": timeout_session, "agent_activity_summary":dict(agent_activity)}
        base_stats["budget_tracker_summary"] = {"tracked_agents_count":len(self.budget_tracker.usage_log)}
        base_stats["runaway_protection_status"] = {"paused_workspaces_for_auto_generation":list(self.workspace_auto_generation_paused),
                                               "last_runaway_check_timestamp":self.last_runaway_check.isoformat() if self.last_runaway_check else None,
                                               "runaway_check_interval_seconds":self.runaway_check_interval, "max_pending_tasks_per_workspace_limit":self.max_pending_tasks_per_workspace}
        auto_gen_event_types = {"initial_workspace_task_created","subtask_delegated","follow_up_generated"}
        base_stats["auto_generation_activity"] = {"related_events_in_log":sum(1 for log in self.execution_log if log.get("event") in auto_gen_event_types)}
        return base_stats

task_executor = TaskExecutor()

async def start_task_executor(): await task_executor.start()
async def stop_task_executor(): await task_executor.stop()
async def pause_task_executor(): await task_executor.pause()
async def resume_task_executor(): await task_executor.resume()
def get_executor_stats() -> Dict[str, Any]: return task_executor.get_detailed_stats()
def get_recent_executor_activity(workspace_id:Optional[str]=None, limit:int=50) -> List[Dict[str,Any]]: return task_executor.get_recent_activity(workspace_id=workspace_id, limit=limit)

async def trigger_initial_workspace_task(workspace_id: str) -> Optional[str]:
    logger.info(f"Manual trigger for initial task in W:{workspace_id}.")
    if not task_executor.running: logger.warning("Executor not running. Initial task creation might be limited.")
    return await task_executor.create_initial_workspace_task(workspace_id)

async def trigger_runaway_check() -> Dict[str, Any]:
    logger.info("Manual trigger for runaway check.")
    if not task_executor.running: return {"success":False, "message":"Executor not running."}
    results = await task_executor.periodic_runaway_check()
    task_executor.last_runaway_check = datetime.now()
    return {"success":True, "message":"Runaway check manually triggered.", "check_results":results,
            "current_runaway_status":{"paused_workspaces":list(task_executor.workspace_auto_generation_paused),
                                     "last_check":task_executor.last_runaway_check.isoformat()}}

async def reset_workspace_auto_generation(workspace_id: str) -> Dict[str, Any]:
    logger.info(f"Manual trigger to reset auto-gen for W:{workspace_id}.")
    if not task_executor.running: return {"success":False, "message":f"Executor not running for W:{workspace_id}."}
    if workspace_id in task_executor.workspace_auto_generation_paused:
        await task_executor._resume_auto_generation_for_workspace(workspace_id)
        health = await task_executor.check_workspace_health(workspace_id)
        return {"success":True, "message":f"Auto-gen resumed for W:{workspace_id}. Health score: {health.get('health_score','N/A')}.",
                "workspace_unpaused":workspace_id not in task_executor.workspace_auto_generation_paused}
    else: return {"success":False, "message":f"Auto-gen not paused for W:{workspace_id}."}

def set_global_auto_generation(enabled: bool) -> Dict[str, Any]:
    # Nota: Questa impostazione non persiste tra i riavvii dell'executor.
    # Per la persistenza, considerare la memorizzazione in un DB o file di configurazione.
    task_executor.auto_generation_enabled = enabled
    status_msg = "ENABLED" if enabled else "DISABLED"
    logger.info(f"Global auto-generation is now {status_msg}.")
    return {"success":True, "message":f"Global auto-generation is {status_msg}.", "current_status":task_executor.auto_generation_enabled}

# -----------------------------------------------------------------
# Back-compatibility wrappers (richiamati da altri moduli legacy)
# -----------------------------------------------------------------
def get_auto_generation_stats() -> Dict[str, Any]:
    """
    Compat: restituisce solo la sezione auto_generation_activity
    del dict completo prodotto da get_detailed_stats().
    """
    return task_executor.get_detailed_stats().get("auto_generation_activity", {})

def get_runaway_protection_status() -> Dict[str, Any]:
    """
    Compat: restituisce solo la sezione runaway_protection_status.
    """
    return task_executor.get_detailed_stats().get("runaway_protection_status", {})

# ======================================================
# ⚙️  ANTI-LOOP CONFIGURAZIONE GLOBALE  + UTILITIES
# ======================================================

ANTI_LOOP_CONFIG = {
    "max_pending_per_workspace": 8,       # ↓ da 50
    "max_delegation_attempts": 1,         # ↓ da 3
    "task_timeout_seconds": 120,          # 2 minuti
    "auto_generation_disabled": True,     # disabilita auto-gen
    "forced_completion": True,            # forza completion su errori
    "single_task_processing": True,       # un task per workspace
    "max_concurrent_global": 2,           # max 2 task globali
}

async def apply_anti_loop_config() -> None:
    """
    Applica i parametri ANTI_LOOP_CONFIG all’istanza globale task_executor.
    Può essere richiamata quante volte vuoi (idempotente).
    """
    global task_executor
    logger.info("Applying anti-loop configuration ...")

    # 1.  Limiti generali -----------------------------------------------
    task_executor.max_pending_tasks_per_workspace = ANTI_LOOP_CONFIG["max_pending_per_workspace"]
    task_executor.max_concurrent_tasks           = ANTI_LOOP_CONFIG["max_concurrent_global"]
    task_executor.task_timeout                   = ANTI_LOOP_CONFIG["task_timeout_seconds"]

    # 2.  Disabilita auto-generation su tutti i workspace attivi ---------
    if ANTI_LOOP_CONFIG["auto_generation_disabled"]:
        try:
            active_ws = await get_active_workspaces()
            task_executor.workspace_auto_generation_paused.update(active_ws)
            logger.info(f"Auto-generation DISABLED for {len(active_ws)} workspace(s)")
        except Exception as e:
            logger.error(f"Failed disabling auto-generation: {e}")

    # 3.  Sincronizza l’EnhancedTaskExecutor (se esiste) -----------------
    try:
        enhanced_exec = get_enhanced_task_executor()
        enhanced_exec.disable_auto_generation()
    except Exception as e:
        logger.warning(f"Could not sync enhanced task executor: {e}")

    # 4.  Log riepilogo --------------------------------------------------
    summary = {
        "max_pending_per_workspace": task_executor.max_pending_tasks_per_workspace,
        "max_concurrent_tasks":      task_executor.max_concurrent_tasks,
        "task_timeout":              task_executor.task_timeout,
        "paused_workspaces":         len(task_executor.workspace_auto_generation_paused),
        "auto_generation":           "DISABLED" if ANTI_LOOP_CONFIG["auto_generation_disabled"] else "ENABLED",
    }
    logger.info(f"✅ Anti-loop config applied: {json.dumps(summary)}")

# ----------------------------------------------------------------------
# Boostrapping: avvio executor + anti-loop + monitor ricorrente
# ----------------------------------------------------------------------

# Salviamo la reference alla start originale
_original_start_task_executor = start_task_executor   # <- quella definita poche righe sotto

async def start_task_executor() -> None:              # ⚠️ override
    """
    Avvia il TaskExecutor **e** applica subito la configurazione anti-loop.
    Resta compatibile con chi importava `start_task_executor` dal modulo.
    """
    await _original_start_task_executor()
    await apply_anti_loop_config()
    # parte anche il monitor periodico
    asyncio.create_task(_periodic_anti_loop_monitor())

# Funzione di monitoraggio periodico (ogni 10 min)
async def _periodic_anti_loop_monitor() -> None:
    while task_executor.running:
        try:
            await asyncio.sleep(600)  # 10 min
            # Se per qualunque ragione un workspace “sfugge”, lo ri-mettiamo in pausa
            if ANTI_LOOP_CONFIG["auto_generation_disabled"]:
                active_ws = await get_active_workspaces()
                missing   = set(active_ws) - task_executor.workspace_auto_generation_paused
                if missing:
                    task_executor.workspace_auto_generation_paused.update(missing)
                    logger.warning(f"Re-applied auto-gen pause to {len(missing)} workspace(s)")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in anti-loop monitor: {e}")
