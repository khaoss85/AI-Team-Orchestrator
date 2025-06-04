# backend/executor.py - Enhanced with FINALIZATION priority boost
import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from uuid import UUID, uuid4
import json
import time
from collections import defaultdict, Counter
import difflib

# Import da modelli del progetto
from models import TaskStatus, Task, AgentStatus, WorkspaceStatus, Agent as AgentModelPydantic
from database import (
    list_tasks,
    update_task_status,
    get_workspace,
    get_agent,
    list_agents as db_list_agents,
    create_task,
    get_active_workspaces,
    get_workspaces_with_pending_tasks,
    update_workspace_status
)
from ai_agents.manager import AgentManager
from task_analyzer import EnhancedTaskExecutor, get_enhanced_task_executor
logger = logging.getLogger(__name__)

try:
    from config.quality_system_config import QualitySystemConfig
    from deliverable_aggregator import check_and_create_final_deliverable
    QUALITY_SYSTEM_AVAILABLE = True
    logger.info("✅ Quality System integration available for TaskExecutor")
except ImportError as e:
    logger.warning(f"⚠️ Quality System not available in TaskExecutor: {e}")
    QUALITY_SYSTEM_AVAILABLE = False
    QualitySystemConfig = None


# === ENHANCED FINALIZATION PRIORITY CONFIGURATIONS ===
FINALIZATION_TASK_PRIORITY_BOOST = int(os.getenv("FINALIZATION_TASK_PRIORITY_BOOST", "1000"))
ENABLE_SMART_PRIORITIZATION = os.getenv("ENABLE_SMART_PRIORITIZATION", "true").lower() == "true"

# === ENHANCED PRIORITY SCORING FUNCTION ===
def get_task_priority_score_enhanced(task_data):
    """
    ENHANCED: Smart prioritization with FINALIZATION boost and comprehensive scoring
    """
    try:
        # Base priority score
        base_priority = 0
        
        # === CRITICAL: FINALIZATION PHASE BOOST ===
        context_data = task_data.get("context_data", {}) or {}
        project_phase = ""
        
        if isinstance(context_data, dict):
            project_phase = context_data.get("project_phase", "").upper()
        
        # MASSIVE boost for FINALIZATION tasks
        if project_phase == "FINALIZATION":
            base_priority = FINALIZATION_TASK_PRIORITY_BOOST
            logger.critical(f"🎯 FINALIZATION BOOST: Task {task_data.get('id', 'unknown')} priority = {base_priority}")
        
        # High boost for phase planning tasks
        elif context_data.get("planning_task_marker"):
            target_phase = context_data.get("target_phase", "")
            if target_phase == "FINALIZATION":
                base_priority = FINALIZATION_TASK_PRIORITY_BOOST - 100  # Slightly lower than execution
                logger.warning(f"🎯 FINALIZATION PLANNING BOOST: Task {task_data.get('id', 'unknown')} priority = {base_priority}")
            else:
                base_priority = 500  # High priority for any phase planning
                logger.info(f"📋 PLANNING BOOST: Task {task_data.get('id', 'unknown')} priority = {base_priority}")
        
        # Enhanced priority based on task priority field
        else:
            priority_field = task_data.get("priority", "medium").lower()
            priority_mapping = {
                "high": 300,
                "medium": 100,
                "low": 50
            }
            base_priority = priority_mapping.get(priority_field, 100)
        
        # === DELEGATION DEPTH PENALTY ===
        delegation_depth = 0
        if isinstance(context_data, dict):
            delegation_depth = context_data.get("delegation_depth", 0)
        
        # Progressive penalty for deep delegation
        if delegation_depth > 0:
            depth_penalty = min(delegation_depth * 50, 300)  # Max 300 penalty
            base_priority = max(base_priority - depth_penalty, 10)  # Min 10 priority
        
        # === AGENT ASSIGNMENT BOOST ===
        assignment_boost = 0
        
        # 1. Tasks without agent_id but with assigned_to_role (need assignment)
        if not task_data.get("agent_id") and task_data.get("assigned_to_role"):
            assignment_boost = 200  # High boost for assignment needed
            logger.info(f"🎭 ASSIGNMENT NEEDED: Task {task_data.get('id', 'unknown')} +{assignment_boost}")
        
        # 2. Tasks with specific agent assignment
        elif task_data.get("agent_id"):
            assignment_boost = 50  # Small boost for already assigned
        
        # === TIME-BASED FACTORS ===
        time_boost = 0
        created_at = task_data.get("created_at")
        if created_at:
            try:
                # Parse creation time
                if isinstance(created_at, str):
                    created_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                else:
                    created_time = created_at
                
                # Age boost: older tasks get higher priority
                task_age_hours = (datetime.now(created_time.tzinfo) - created_time).total_seconds() / 3600
                
                if task_age_hours > 2:  # Tasks older than 2 hours
                    time_boost = min(int(task_age_hours * 5), 100)  # Max 100 boost
                    
            except Exception as e:
                logger.debug(f"Error calculating task age: {e}")
        
        # === TASK TYPE ANALYSIS ===
        task_name = task_data.get("name", "").lower()
        name_boost = 0
        
        # High priority keywords
        high_priority_keywords = [
            "critical", "urgent", "final", "deliverable", "completion", 
            "escalation", "handoff", "important"
        ]
        
        medium_priority_keywords = [
            "follow-up", "continuation", "review", "analysis"
        ]
        
        if any(keyword in task_name for keyword in high_priority_keywords):
            name_boost = 150
        elif any(keyword in task_name for keyword in medium_priority_keywords):
            name_boost = 75
        
        # === CREATION TYPE ANALYSIS ===
        creation_type = context_data.get("creation_type", "") if isinstance(context_data, dict) else ""
        creation_boost = 0
        
        creation_priority_map = {
            "phase_transition": 400,        # Phase transitions are critical
            "final_deliverable_aggregation": 800,  # Final deliverables critical
            "pm_completion_analyzer": 200,  # PM-generated tasks important
            "handoff": 150,                # Handoffs important
            "escalation": 300,             # Escalations very important
            "user_feedback": 250           # User feedback important
        }
        
        creation_boost = creation_priority_map.get(creation_type, 0)
        
        # === FINAL CALCULATION ===
        final_priority = (
            base_priority +           # Base priority (includes FINALIZATION boost)
            assignment_boost +        # Assignment status
            time_boost +             # Age-based boost
            name_boost +             # Name-based boost
            creation_boost           # Creation type boost
        )
        
        # Ensure minimum priority
        final_priority = max(final_priority, 1)
        
        # Log detailed calculation for FINALIZATION tasks
        if project_phase == "FINALIZATION" or final_priority > 500:
            logger.warning(f"🔥 HIGH PRIORITY TASK: {task_data.get('name', 'Unknown')[:50]} "
                          f"Final Priority: {final_priority} "
                          f"(base:{base_priority}, assignment:{assignment_boost}, "
                          f"time:{time_boost}, name:{name_boost}, creation:{creation_boost})")
        
        return final_priority
        
    except Exception as e:
        logger.error(f"Error calculating enhanced task priority: {e}")
        return 1  # Minimum priority fallback


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

    def log_usage(self, agent_id: str, model: str, input_tokens: int, output_tokens: int, task_id: Optional[str] = None) -> Dict[str, Any]:
        """Log token usage and associated costs"""
        if agent_id not in self.usage_log:
            self.usage_log[agent_id] = []

        costs = self.token_costs.get(model, self.token_costs[self.default_model])
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
        """Calculate workspace total cost"""
        total_cost = 0.0
        agent_costs = {}
        total_tokens = {"input": 0, "output": 0}

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
            "total_tokens": total_tokens,
            "currency": "USD"
        }

    def get_all_usage_logs(self, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return all usage logs, optionally filtered by agent"""
        if agent_id:
            return self.usage_log.get(agent_id, [])
        else:
            all_logs = []
            for logs in self.usage_log.values():
                all_logs.extend(logs)
            return all_logs

class AssetCoordinationMixin:
    """
    Mixin per coordinamento asset-oriented nel TaskExecutor esistente
    Estende funzionalità senza modificare l'architettura base
    """
    
    async def coordinate_asset_oriented_workflow(self, workspace_id: str):
        """
        Coordina il workflow asset-oriented per un workspace
        """
        
        try:
            # Verifica se il workspace ha task asset-oriented in corso
            asset_tasks = await self._get_asset_oriented_tasks(workspace_id)
            
            if asset_tasks:
                logger.info(f"🎯 ASSET COORDINATION: {len(asset_tasks)} asset tasks in workspace {workspace_id}")
                
                # Prioritizza task asset-oriented
                await self._prioritize_asset_tasks(asset_tasks)
                
                # Monitora completamento per deliverable triggering
                completed_asset_tasks = [t for t in asset_tasks if t.get("status") == "completed"]
                
                if len(completed_asset_tasks) >= len(asset_tasks) * 0.8:  # 80% asset tasks completed
                    logger.info(f"🎯 ASSET THRESHOLD: 80% asset tasks completed, checking deliverable readiness")
                    
                    # Trigger enhanced deliverable check
                    from deliverable_aggregator import check_and_create_final_deliverable
                    deliverable_id = await check_and_create_final_deliverable(workspace_id)
                    
                    if deliverable_id:
                        logger.critical(f"🎯 ASSET-TRIGGERED DELIVERABLE: {deliverable_id} created for {workspace_id}")
            
        except Exception as e:
            logger.error(f"Error in asset-oriented workflow coordination: {e}")
    
    async def _get_asset_oriented_tasks(self, workspace_id: str) -> List[Dict]:
        """Ottieni task asset-oriented per un workspace"""
        
        try:
            all_tasks = await list_tasks(workspace_id)
            
            asset_tasks = []
            for task in all_tasks:
                context_data = task.get("context_data", {}) or {}
                
                if isinstance(context_data, dict):
                    if (context_data.get("asset_production") or 
                        context_data.get("asset_oriented_task") or
                        "PRODUCE ASSET:" in task.get("name", "")):
                        asset_tasks.append(task)
            
            return asset_tasks
            
        except Exception as e:
            logger.error(f"Error getting asset-oriented tasks: {e}")
            return []
    
    async def _prioritize_asset_tasks(self, asset_tasks: List[Dict]):
        """Prioritizza task asset-oriented nel sistema"""
        
        for task in asset_tasks:
            if task.get("status") == "pending":
                # Boost priority per asset tasks
                try:
                    await update_task_status(
                        task["id"], 
                        "pending",
                        {"priority_boost": "asset_oriented", "boosted_at": datetime.now().isoformat()}
                    )
                except Exception as e:
                    logger.warning(f"Failed to boost priority for asset task {task['id']}: {e}")

class TaskExecutor(AssetCoordinationMixin):
    """Enhanced Task Executor with anti-loop protection and role-based task assignment"""

    def __init__(self):
        """Initialize the task executor"""
        self.running = False
        self.paused = False
        self.pause_event = asyncio.Event()
        self.pause_event.set()

        self.workspace_managers: Dict[UUID, AgentManager] = {}
        self.budget_tracker = BudgetTracker()
        self.execution_log: List[Dict[str, Any]] = []

        # ANTI-LOOP CONFIGURATIONS
        self.max_concurrent_tasks: int = 3  # Numero di worker paralleli
        self.max_tasks_per_workspace_anti_loop: int = 10
        self.execution_timeout: int = 150  # secondi per task
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

        # Enhanced task handler (con auto-generation disabilitata)
        self.enhanced_handler = get_enhanced_task_executor()
        self.auto_generation_enabled: bool = True  # DISABILITATO per sicurezza

        # RUNAWAY PROTECTION CONFIGURATIONS
        self.workspace_auto_generation_paused: Set[str] = set()
        self.last_runaway_check: Optional[datetime] = None
        self.max_pending_tasks_per_workspace: int = int(os.getenv("MAX_PENDING_TASKS_PER_WORKSPACE", "50"))
        self.runaway_check_interval: int = 300  # secondi

        # === QUERY CACHING CONFIGURATION ===
        # Minimum seconds before repeating the same DB query for a workspace
        self.min_db_query_interval: int = int(os.getenv("MIN_DB_QUERY_INTERVAL", "30"))
        self._tasks_query_cache: Dict[str, Tuple[float, List[Dict]]] = {}
        self._agents_query_cache: Dict[str, Tuple[float, List[Dict]]] = {}
        self._active_ws_cache: Tuple[float, List[str]] = (0, [])

    async def start(self):
        """Start the task executor"""
        if self.running:
            logger.warning("Task executor already running")
            return
            
        self.running = True
        self.paused = False
        self.pause_event.set()
        self.execution_log = []

        logger.info("Starting task executor with anti-loop protection")
        logger.info(f"Max concurrent tasks: {self.max_concurrent_tasks}")
        logger.info(f"Task timeout: {self.execution_timeout}s")
        logger.info(f"Auto-generation: {'ENABLED' if self.auto_generation_enabled else 'DISABLED'}")
        logger.info(f"Runaway check interval: {self.runaway_check_interval}s")
        logger.info(f"FINALIZATION priority boost: {FINALIZATION_TASK_PRIORITY_BOOST}")
        logger.info(f"Smart prioritization: {'ENABLED' if ENABLE_SMART_PRIORITIZATION else 'DISABLED'}")

        # Avvia worker per processare la queue
        self.worker_tasks = [
            asyncio.create_task(self._anti_loop_worker()) 
            for _ in range(self.max_concurrent_tasks)
        ]
        
        # Avvia il main execution loop
        asyncio.create_task(self.execution_loop())
        logger.info("Task executor started successfully")

    async def stop(self):
        """Stop the task executor"""
        if not self.running:
            logger.warning("Task executor is not running")
            return
            
        logger.info("Stopping task executor...")
        self.running = False
        self.paused = True
        self.pause_event.set()

        # Invia segnali di stop ai worker
        for _ in range(len(self.worker_tasks)):
            try:
                await asyncio.wait_for(self.task_queue.put(None), timeout=2.0)
            except asyncio.TimeoutError:
                logger.warning("Timeout sending stop signal to task queue")
            except asyncio.QueueFull:
                logger.warning("Task queue full while sending stop signal")

        # Aspetta che i worker terminino
        if self.worker_tasks:
            results = await asyncio.gather(*self.worker_tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception) and not isinstance(result, asyncio.CancelledError):
                    logger.error(f"Worker task {i} finished with error: {result}", exc_info=result)
        
        self.worker_tasks = []
        logger.info("Task executor stopped")

    async def pause(self):
        """Pause the task executor"""
        if not self.running:
            logger.warning("Cannot pause: Task executor is not running")
            return
        if self.paused:
            logger.info("Task executor is already paused")
            return
            
        self.paused = True
        self.pause_event.clear()
        logger.info("Task executor paused")

    async def resume(self):
        """Resume the task executor"""
        if not self.running:
            logger.warning("Cannot resume: Task executor is not running")
            return
        if not self.paused:
            logger.info("Task executor is already running")
            return
            
        self.paused = False
        self.pause_event.set()
        logger.info("Task executor resumed")

    async def _anti_loop_worker(self):
        """Worker thread che processa task dalla queue con protezione anti-loop"""
        worker_id = uuid4()
        logger.info(f"Anti-loop worker {worker_id} started")
        
        while self.running:
            try:
                await self.pause_event.wait()
                if not self.running:
                    break

                manager: Optional[AgentManager] = None
                task_dict_from_queue: Optional[Dict] = None
                
                try:
                    # La coda contiene tuple (AgentManager, dict del task)
                    manager, task_dict_from_queue = await asyncio.wait_for(
                        self.task_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                if task_dict_from_queue is None:  # Segnale di terminazione
                    self.task_queue.task_done()
                    logger.info(f"Anti-loop worker {worker_id} received termination signal")
                    break
                
                task_id = task_dict_from_queue.get("id", "UnknownID")
                task_name = task_dict_from_queue.get("name", "Unnamed Task")
                workspace_id = task_dict_from_queue.get("workspace_id", "UnknownWS")

                logger.info(f"Worker {worker_id} picking up task: '{task_name}' (ID: {task_id}) from W: {workspace_id}. Q size: {self.task_queue.qsize()}")

                # --- LOGICA DI ASSEGNAZIONE AGENTE SE NON PRESENTE ---
                current_agent_id = task_dict_from_queue.get("agent_id")
                assigned_role = task_dict_from_queue.get("assigned_to_role")

                if not current_agent_id and assigned_role:
                    logger.info(f"Task {task_id} needs agent assignment for role '{assigned_role}'")
                    assigned_agent_info = await self._assign_agent_to_task_by_role(
                        task_dict_from_queue, workspace_id, assigned_role
                    )
                    
                    if assigned_agent_info and "id" in assigned_agent_info:
                        # Aggiorna il dict per l'esecuzione
                        task_dict_from_queue["agent_id"] = str(assigned_agent_info["id"])
                        current_agent_id = str(assigned_agent_info["id"])
                        logger.info(f"Task {task_id} assigned to agent {assigned_agent_info['name']} (ID: {current_agent_id}) for role '{assigned_role}'")
                    else:
                        logger.warning(f"Could not assign agent for role '{assigned_role}' to task {task_id}. Skipping task.")
                        self.task_queue.task_done()
                        continue
                
                # Validazione anti-loop
                if not await self._validate_task_execution(task_dict_from_queue):
                    logger.warning(f"Worker {worker_id} skipping task {task_id} - failed anti-loop validation")
                    self.task_queue.task_done()
                    await asyncio.sleep(0.05)
                    continue
                
                # Esecuzione del task
                self.active_tasks_count += 1
                try:
                    if manager is None:
                        raise ValueError(f"Task {task_id} with null manager for worker {worker_id}")
                    await self._execute_task_with_anti_loop_and_tracking(manager, task_dict_from_queue)
                except Exception as e_exec:
                    logger.error(f"Worker {worker_id} critical error for task {task_id}: {e_exec}", exc_info=True)
                    await self._force_complete_task(
                        task_dict_from_queue, 
                        f"Critical worker error: {str(e_exec)[:200]}",
                        status_to_set=TaskStatus.FAILED.value
                    )
                finally:
                    self.active_tasks_count -= 1
                    self.task_queue.task_done()
                    logger.info(f"Worker {worker_id} finished task: {task_id}. Active: {self.active_tasks_count}")
                    
                    # Marca come completato nel tracker
                    if workspace_id and task_id:
                        self.task_completion_tracker[workspace_id].add(task_id)

            except asyncio.CancelledError:
                logger.info(f"Anti-loop worker {worker_id} cancelled")
                break
            except Exception as e_worker_loop:
                logger.error(f"Unhandled error in anti-loop worker {worker_id} main loop: {e_worker_loop}", exc_info=True)
                await asyncio.sleep(5)  # Pausa prima di ritentare
        
        logger.info(f"Anti-loop worker {worker_id} exiting")

    async def _assign_agent_to_task_by_role(self, task_dict: Dict, workspace_id: str, role: str) -> Optional[Dict]:
        """
        Trova un agente attivo per il ruolo specificato e aggiorna il task nel DB.
        Restituisce le info dell'agente assegnato o None.
        """
        try:
            agents_in_db = await db_list_agents(workspace_id=workspace_id)
            
            compatible_agents = [
                agent for agent in agents_in_db
                if agent.get("role", "").lower() == role.lower()
                and agent.get("status") == "active"
            ]

            if not compatible_agents:
                logger.warning(f"No active agent found for role '{role}' in workspace {workspace_id} to assign task {task_dict.get('id')}")
                return None

            # Logica di selezione: per ora il primo, ma potrebbe essere più complessa
            # (es. round-robin, bilanciamento del carico, skill matching)
            selected_agent = compatible_agents[0]
            agent_id_to_assign = str(selected_agent["id"])

            # Aggiorna il task nel DB con l'agent_id assegnato
            # Usiamo update_task_status con un payload che include agent_id
            update_payload = {
                "agent_id": agent_id_to_assign, 
                "status_detail": f"Assigned to agent {selected_agent['name']}"
            }
            
            # Aggiornamento diretto tramite update_task_status
            # Il database.py dovrebbe essere modificato per gestire questo caso
            updated_task = await update_task_status(
                task_id=task_dict["id"], 
                status=task_dict.get("status", TaskStatus.PENDING.value),
                result_payload=update_payload
            )
            
            if updated_task:
                logger.info(f"Task {task_dict['id']} DB record updated with agent_id {agent_id_to_assign}")
                return selected_agent
            else:
                logger.error(f"Failed to update task {task_dict['id']} with agent_id {agent_id_to_assign} in DB")
                return None

        except Exception as e:
            logger.error(f"Error assigning agent to task by role '{role}' for task {task_dict.get('id')}: {e}", exc_info=True)
            return None

    async def _validate_task_execution(self, task_dict: Dict[str, Any]) -> bool:
        """Valida che un task possa essere eseguito (anti-loop protection)"""
        task_id = task_dict.get("id")
        workspace_id = task_dict.get("workspace_id")

        if not task_id or not workspace_id:
            logger.error(f"Invalid task data for validation: id={task_id}, ws={workspace_id}")
            return False

        # Check se il task è già stato completato
        if task_id in self.task_completion_tracker.get(workspace_id, set()):
            logger.warning(f"Anti-loop: Task {task_id} in W:{workspace_id} already completed. Skipping")
            current_status = task_dict.get("status")
            if current_status == TaskStatus.PENDING.value:
                await self._force_complete_task(
                    task_dict, 
                    "Skipped: Already completed (tracker)",
                    status_to_set=TaskStatus.COMPLETED.value
                )
            return False

        # Check workspace task limit
        current_anti_loop_count = self.workspace_anti_loop_task_counts.get(workspace_id, 0)
        if current_anti_loop_count >= self.max_tasks_per_workspace_anti_loop:
            logger.warning(f"Anti-loop: W:{workspace_id} task limit ({current_anti_loop_count}/{self.max_tasks_per_workspace_anti_loop}). Task {task_id} skip")
            return False

        # Check delegation depth
        if task_id in self.delegation_chain_tracker:
            depth = len(self.delegation_chain_tracker[task_id])
            if depth > self.max_delegation_depth:
                logger.warning(f"Anti-loop: Task {task_id} exceeded delegation depth ({depth}/{self.max_delegation_depth}). Forcing completion")
                await self._force_complete_task(
                    task_dict, 
                    "Delegation depth exceeded",
                    status_to_set=TaskStatus.FAILED.value
                )
                return False

        return True

    async def _force_complete_task(self, task_dict: Dict[str, Any], reason: str, status_to_set: str = TaskStatus.COMPLETED.value):
        """Forza il completamento di un task con uno specifico reason"""
        task_id = task_dict.get("id")
        workspace_id = task_dict.get("workspace_id")

        if not task_id:
            logger.error(f"Cannot force complete task: ID missing. Reason: {reason}")
            return

        completion_result = {
            "output": f"Task forcibly finalized: {reason}",
            "status_detail": f"forced_{status_to_set.lower().replace('.', '_')}",
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
        """
        Esegue un task convertendo prima il dict in oggetto Pydantic Task
        e gestendo tutti gli aspetti di tracking, budget, e post-completion
        """
        # Prima converte il dict in un oggetto Pydantic Task
        try:
            # FIXED: Validate and sanitize priority before Pydantic validation
            task_priority = task_dict.get("priority", "medium")
            valid_priorities = ["low", "medium", "high"]

            if task_priority not in valid_priorities:
                logger.warning(f"Invalid priority '{task_priority}' for task {task_dict.get('id')}. Using 'high' instead.")
                task_priority = "high"

            # Assicura che tutti i campi necessari siano presenti
            task_dict_validated = {
                "id": task_dict["id"],
                "workspace_id": task_dict["workspace_id"],
                "agent_id": task_dict.get("agent_id"),
                "assigned_to_role": task_dict.get("assigned_to_role"),
                "name": task_dict["name"],
                "description": task_dict.get("description", ""),
                "status": task_dict.get("status", TaskStatus.PENDING.value),
                "priority": task_priority,  # FIXED: Use validated priority
                "parent_task_id": task_dict.get("parent_task_id"),
                "depends_on_task_ids": task_dict.get("depends_on_task_ids"),
                "estimated_effort_hours": task_dict.get("estimated_effort_hours"),
                "deadline": task_dict.get("deadline"),
                "context_data": task_dict.get("context_data"),  # Già dict, non JSON string
                "result": task_dict.get("result"),
                "created_at": datetime.fromisoformat(task_dict["created_at"]) if task_dict.get("created_at") else datetime.now(),
                "updated_at": datetime.fromisoformat(task_dict["updated_at"]) if task_dict.get("updated_at") else datetime.now() 
            }
            task_pydantic_obj = Task.model_validate(task_dict_validated)
        except Exception as p_exc:
            logger.error(f"Failed to validate task_dict into Pydantic Task model for task ID {task_dict.get('id')}: {p_exc}", exc_info=True)
            await self._force_complete_task(
                task_dict, 
                f"Invalid task data structure: {p_exc}",
                status_to_set=TaskStatus.FAILED.value
            )
            return
        
        task_id = str(task_pydantic_obj.id)
        workspace_id = str(task_pydantic_obj.workspace_id)
        agent_id = str(task_pydantic_obj.agent_id) if task_pydantic_obj.agent_id else None
        task_name = task_pydantic_obj.name

        if not agent_id:  # Dovrebbe essere stato assegnato da _assign_agent_to_task_by_role
            error_msg = f"Task {task_id} ('{task_name}') reached execution stage without an assigned agent_id"
            logger.error(error_msg)
            await self._force_complete_task(task_dict, error_msg, status_to_set=TaskStatus.FAILED.value)
            return
            
        # Tracking e preparazione
        start_time_tracking = time.time()
        model_for_budget = self.budget_tracker.default_model
        estimated_input_tokens = 0

        self.workspace_anti_loop_task_counts[workspace_id] = self.workspace_anti_loop_task_counts.get(workspace_id, 0) + 1

        try:
            # Log inizio esecuzione
            execution_start_log = {
                "timestamp": datetime.now().isoformat(),
                "event": "task_execution_started",
                "task_id": task_id,
                "agent_id": agent_id,
                "workspace_id": workspace_id,
                "task_name": task_name,
                "assigned_role": task_pydantic_obj.assigned_to_role,
                "priority": task_pydantic_obj.priority
            }
            self.execution_log.append(execution_start_log)
            
            # Aggiorna status nel DB
            await update_task_status(
                task_id, 
                TaskStatus.IN_PROGRESS.value,
                result_payload={"status_detail": "Execution started by anti-loop worker"}
            )

            # Recupera dati agente dal DB
            agent_data_db = await get_agent(agent_id)
            if not agent_data_db:
                raise ValueError(f"Agent {agent_id} not found for task {task_id}")

            # Determina il modello LLM da usare
            llm_config_db = agent_data_db.get("llm_config")
            if isinstance(llm_config_db, str):
                llm_config = json.loads(llm_config_db)
            elif isinstance(llm_config_db, dict):
                llm_config = llm_config_db
            else:
                llm_config = {}

            config_model = llm_config.get("model")
            if config_model and config_model in self.budget_tracker.token_costs:
                model_for_budget = config_model
            else:
                # Mapping seniority -> model
                seniority_map = {
                    "junior": "gpt-4.1-nano",
                    "senior": "gpt-4.1-mini", 
                    "expert": "gpt-4.1"
                }
                model_for_budget = seniority_map.get(
                    agent_data_db.get("seniority", "senior"), 
                    self.budget_tracker.default_model
                )

            logger.info(f"Executing task {task_id} ('{task_name}') with agent {agent_id} (Role: {agent_data_db.get('role', 'N/A')}) using model {model_for_budget}")
            
            # Stima token input
            task_input_text = f"{task_name} {task_pydantic_obj.description or ''}"
            estimated_input_tokens = max(1, len(task_input_text) // 4)

            # ESECUZIONE DEL TASK
            await self.process_task_with_coordination(task_dict, manager)
            return
        except Exception as e:
            # Gestione errori che non sono stati catturati dal coordination layer
            logger.error(f"Unhandled error in coordination layer for task {task_dict.get('id')}: {e}", exc_info=True)
            await self._force_complete_task(
                task_dict,
                f"Coordination layer error: {str(e)[:200]}",
                status_to_set=TaskStatus.FAILED.value
            )

    async def check_project_completion_after_task(self, completed_task_id: str, workspace_id: str):
        """Verifica se il progetto è completato dopo un task importante"""
        try:
            # Verifica se il task è un task di completamento
            tasks = await list_tasks(workspace_id)
            completed_task = next((t for t in tasks if t.get("id") == completed_task_id), None)
            
            if not completed_task:
                return
                
            context_data = completed_task.get("context_data", {}) or {}
            is_final_task = context_data.get("is_final_task", False)
            project_phase = context_data.get("project_phase", "")
            
            # Se è un task di fase FINALIZATION completato, verifica completamento progetto
            if (is_final_task or project_phase == "FINALIZATION") and completed_task.get("status") == "completed":
                # Usa l'EnhancedTaskExecutor per verificare completamento
                from task_analyzer import get_enhanced_task_executor
                task_executor = get_enhanced_task_executor()
                
                is_completed = await task_executor.check_project_completion_criteria(workspace_id)
                
                if is_completed:
                    if workspace_id in self.completed_workspaces:
                        logger.debug(f"Workspace {workspace_id} already processed as completed")
                        return

                    # Aggiorna stato workspace
                    workspace = await get_workspace(workspace_id)
                    if workspace and workspace.get("status") != "completed":
                        await update_workspace_status(workspace_id, "completed")
                        logger.info(f"Project {workspace_id} automatically marked as COMPLETED")

                    # Mark as processed regardless of DB status to avoid redundant checks
                    self.completed_workspaces.add(workspace_id)
                    self.execution_log.append({
                        "timestamp": datetime.now().isoformat(),
                        "event": "project_completed",
                        "workspace_id": workspace_id,
                        "trigger_task_id": completed_task_id
                    })
        except Exception as e:
            logger.error(f"Error checking project completion after task {completed_task_id}: {e}", exc_info=True)

    async def _is_project_manager_task(self, task: Task, result: Dict[str, Any]) -> bool:
        """Determina se un task è stato completato da un Project Manager"""
        
        try:
            # Metodo 1: Controlla l'agent_id se disponibile
            if task.agent_id:
                agent_data = await get_agent(str(task.agent_id))
                if agent_data:
                    role = agent_data.get('role', '').lower()
                    pm_keywords = ['manager', 'coordinator', 'director', 'lead', 'pm', 'project']
                    if any(kw in role for kw in pm_keywords):
                        logger.info(f"Task {task.id} identified as PM task by agent role: {role}")
                        return True
        except Exception as e:
            logger.warning(f"Could not check agent role for task {task.id}: {e}")
        
        # Metodo 2: Euristiche basate sul contenuto del task
        task_name = task.name.lower()
        task_desc = (task.description or "").lower()
        
        # Indicatori di task di PM
        pm_indicators = [
            "project setup", "strategic planning", "kick-off",
            "planning", "coordination", "project manager",
            "team assessment", "phase breakdown", "delegate"
        ]
        
        for indicator in pm_indicators:
            if indicator in task_name or indicator in task_desc:
                logger.info(f"Task {task.id} identified as PM task by content indicator: {indicator}")
                return True
        
        return False

    async def execution_loop(self):
        """Main execution loop del TaskExecutor con asset coordination"""
        logger.info("Main execution loop started with asset coordination")
        
        while self.running:
            try:
                await self.pause_event.wait()
                if not self.running:
                    break
                    
                # Circuit breaker check (esistente)
                if self.check_global_circuit_breaker():
                    logger.critical("⚠️ CIRCUIT BREAKER ACTIVATED - System paused. Manual restart required.")
                    self.execution_log.append({
                        "timestamp": datetime.now().isoformat(),
                        "event": "circuit_breaker_activated",
                        "reason": "Abnormal behavior detected"
                    })
                    await asyncio.sleep(60)
                    continue

                logger.debug("Main exec loop: processing pending tasks, asset coordination, checking workspaces")
                
                # Processa task pendenti (esistente)
                await self.process_pending_tasks_anti_loop()
                
                # === NUOVA: Asset coordination ===
                try:
                    active_workspaces = await get_active_workspaces()
                    for ws_id in active_workspaces:
                        await self.coordinate_asset_oriented_workflow(ws_id)
                except Exception as e:
                    logger.error(f"Error in asset coordination: {e}")
                
                # Controlla nuovi workspace (esistente)
                if self.auto_generation_enabled:
                    await self.check_for_new_workspaces()

                # Controllo runaway periodico (esistente)
                if (self.last_runaway_check is None or
                    (datetime.now() - self.last_runaway_check).total_seconds() > self.runaway_check_interval):
                    await self.periodic_runaway_check()
                    self.last_runaway_check = datetime.now()

                # Cleanup periodico (esistente)
                if datetime.now() - self.last_cleanup > timedelta(minutes=5):
                    await self._cleanup_tracking_data()

                await asyncio.sleep(10)

            except asyncio.CancelledError:
                logger.info("Main execution loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in main execution_loop: {e}", exc_info=True)
                await asyncio.sleep(30)
        
        logger.info("Main execution loop finished")

    async def process_pending_tasks_anti_loop(self):
        """Processa task pendenti da tutti i workspace attivi"""
        if self.paused:
            return
            
        try:
            # Ottieni workspace con task pendenti
            workspaces_with_pending = await get_workspaces_with_pending_tasks()
            
            if workspaces_with_pending:
                logger.debug(f"Found {len(workspaces_with_pending)} workspaces with pending tasks. Checking queue/health")
            
            # Limita il numero di workspace processati per ciclo
            for workspace_id in workspaces_with_pending[:self.max_concurrent_tasks * 2]:
                if self.task_queue.full():
                    logger.warning(f"Anti-loop Task Queue is full ({self.task_queue.qsize()}/{self.max_queue_size}). Skipping further workspace processing in this cycle")
                    break
                # Pre-warm caches to avoid repeated DB hits in quick succession
                await self._cached_list_tasks(workspace_id)
                await self._cached_list_agents(workspace_id)
                await self.process_workspace_tasks_anti_loop_with_health_check_enhanced(workspace_id)
                
        except Exception as e:
            logger.error(f"Error in process_pending_tasks_anti_loop: {e}", exc_info=True)

    async def process_workspace_tasks_anti_loop_with_health_check_enhanced(self, workspace_id: str):
        """
        ENHANCED VERSION: Processa task con prioritizzazione intelligente FINALIZATION
        Sostituisce il metodo esistente process_workspace_tasks_anti_loop_with_health_check
        """
        if self.paused:
            return
            
        try:
            # Health check del workspace (mantieni logica esistente)
            health_status = await self.check_workspace_health(workspace_id)
            
            if not health_status.get('is_healthy', True):
                health_issues = health_status.get('health_issues', [])
                logger.warning(f"W:{workspace_id} health issues: {health_issues}")
                
                critical_issues = [
                    issue for issue in health_issues 
                    if any(keyword in issue.lower() for keyword in ['excessive pending', 'high task creation', 'delegation loops'])
                ]
                
                if critical_issues and workspace_id not in self.workspace_auto_generation_paused:
                    await self._pause_auto_generation_for_workspace(
                        workspace_id, 
                        reason=f"Critical health: {'; '.join(critical_issues)}"
                    )
                    return

            # Auto-generation resume check (mantieni logica esistente)
            if workspace_id in self.workspace_auto_generation_paused:
                if (health_status.get('is_healthy') and 
                    health_status.get('task_counts', {}).get('pending', self.max_pending_tasks_per_workspace) < 10):
                    await self._resume_auto_generation_for_workspace(workspace_id)
                    logger.info(f"Auto-gen resumed for healthy W:{workspace_id}")
                else:
                    return

            # Check limite task per workspace (mantieni logica esistente)
            current_anti_loop_proc_count = self.workspace_anti_loop_task_counts.get(workspace_id, 0)
            if current_anti_loop_proc_count >= self.max_tasks_per_workspace_anti_loop:
                return

            # Ottieni agent manager
            manager = await self.get_agent_manager(workspace_id)
            if not manager:
                logger.error(f"No agent manager for W:{workspace_id}")
                return

            # === ENHANCED: Ottieni TUTTI i task e applica prioritizzazione intelligente ===
            all_tasks_for_workspace = await self._cached_list_tasks(workspace_id)
            
            # Filtra per task PENDING non già completati
            pending_eligible_tasks = [
                t_dict for t_dict in all_tasks_for_workspace
                if t_dict.get("status") == TaskStatus.PENDING.value and
                   not (t_dict.get("id") and t_dict.get("id") in self.task_completion_tracker.get(workspace_id, set()))
            ]

            if not pending_eligible_tasks:
                return

            # === ENHANCED PRIORITIZATION LOGIC ===
            if ENABLE_SMART_PRIORITIZATION:
                # Usa la nuova funzione di prioritizzazione
                pending_eligible_tasks.sort(
                    key=lambda t: (
                        get_task_priority_score_enhanced(t),  # Primary: Enhanced priority score
                        datetime.fromisoformat(t.get("created_at", "2020-01-01").replace("Z", "+00:00"))  # Secondary: FIFO
                    ),
                    reverse=True  # Higher priority first, then older tasks
                )
                
                # Log the top priority task for monitoring
                if pending_eligible_tasks:
                    top_task = pending_eligible_tasks[0]
                    top_priority = get_task_priority_score_enhanced(top_task)
                    logger.info(f"🔥 TOP PRIORITY: '{top_task.get('name', 'Unknown')[:50]}' "
                               f"Priority: {top_priority}, Phase: {top_task.get('context_data', {}).get('project_phase', 'N/A')}")
            else:
                # Fallback: uso prioritizzazione standard
                pending_eligible_tasks.sort(
                    key=lambda t: (
                        self._get_task_priority_score_standard(t),
                        datetime.fromisoformat(t.get("created_at", "2020-01-01").replace("Z", "+00:00"))
                    ),
                    reverse=True
                )
            
            # Prendi il task con massima priorità
            task_to_queue_dict = pending_eligible_tasks[0]
            task_id_to_queue = task_to_queue_dict.get("id")

            # Validazione finale (mantieni logica esistente)
            if not await self._validate_task_execution(task_to_queue_dict):
                logger.warning(f"Pre-queue validation FAILED for task {task_id_to_queue}")
                return
                    
            # Aggiungi alla queue con log migliorato
            try:
                self.task_queue.put_nowait((manager, task_to_queue_dict))
                
                task_phase = task_to_queue_dict.get('context_data', {}).get('project_phase', 'N/A')
                needs_assign = not task_to_queue_dict.get('agent_id') and task_to_queue_dict.get('assigned_to_role')
                priority_score = get_task_priority_score_enhanced(task_to_queue_dict) if ENABLE_SMART_PRIORITIZATION else "standard"
                
                logger.info(f"🚀 QUEUED: '{task_to_queue_dict.get('name', 'Unknown')[:40]}' "
                           f"(ID: {task_id_to_queue[:8]}) Priority: {priority_score}, "
                           f"Phase: {task_phase}, Assign: {needs_assign}, Q: {self.task_queue.qsize()}")
                
            except asyncio.QueueFull:
                logger.warning(f"Task Queue FULL. Could not queue task {task_id_to_queue}")
        
        except Exception as e:
            logger.error(f"Error in enhanced workspace task processing for W:{workspace_id}: {e}", exc_info=True)

    def _get_task_priority_score_standard(self, task_data):
        """Funzione standard di prioritizzazione (fallback)"""
        delegation_depth = 0
        context_data = task_data.get("context_data", {}) or {}
        if isinstance(context_data, dict):
            delegation_depth = context_data.get("delegation_depth", 0)

        depth_penalty = min(delegation_depth * 2, 8)
        base_priority = 0

        if not task_data.get("agent_id") and task_data.get("assigned_to_role"):
            base_priority = 10
        
        p = task_data.get("priority", "medium").lower()
        if p == "high": base_priority = 8
        elif p == "medium": base_priority = 5
        elif p == "low": base_priority = 3

        return max(1, base_priority - depth_penalty)

    async def _cleanup_tracking_data(self):
        """Cleanup periodico dei dati di tracking per evitare memory leak"""
        logger.info("Performing cleanup of executor tracking data...")
        self.last_cleanup = datetime.now()

        # Cleanup execution log
        max_log_entries = 500
        if len(self.execution_log) > max_log_entries:
            self.execution_log = self.execution_log[-max_log_entries:]
            logger.debug(f"Cleaned execution_log, kept last {max_log_entries}")

        # Cleanup task completion tracker
        max_completed_per_ws = 100
        for workspace_id in list(self.task_completion_tracker.keys()):
            if len(self.task_completion_tracker[workspace_id]) > max_completed_per_ws * 2:
                logger.warning(f"Task completion tracker for W:{workspace_id} has {len(self.task_completion_tracker[workspace_id])} entries (>{max_completed_per_ws*2}). Resetting")
                self.task_completion_tracker[workspace_id] = set()  # Reset completo
            elif len(self.task_completion_tracker[workspace_id]) > max_completed_per_ws:
                logger.info(f"Task completion tracker for W:{workspace_id} has {len(self.task_completion_tracker[workspace_id])} entries. Consider more granular cleanup if grows further")

        # Cleanup delegation chain tracker
        for task_id in list(self.delegation_chain_tracker.keys()):
            if len(self.delegation_chain_tracker[task_id]) > self.max_delegation_depth * 2:
                del self.delegation_chain_tracker[task_id]
                logger.debug(f"Removed long delegation chain for task {task_id}")

        # Reset workspace anti-loop counts periodicamente (circa ogni ora)
        if not hasattr(self, "_cleanup_cycle_count"):
            self._cleanup_cycle_count = 0
        self._cleanup_cycle_count += 1
        
        if self._cleanup_cycle_count % 12 == 0:  # Ogni ~1 ora
            logger.info("Periodic reset of workspace_anti_loop_task_counts")
            self.workspace_anti_loop_task_counts = defaultdict(int)
        
        logger.info("Tracking data cleanup finished")

    # === CACHED DATABASE ACCESS HELPERS ===
    async def _cached_list_tasks(self, workspace_id: str) -> List[Dict]:
        now = time.time()
        ts, data = self._tasks_query_cache.get(workspace_id, (0, None))
        if data is not None and now - ts < self.min_db_query_interval:
            return data
        data = await list_tasks(workspace_id)
        self._tasks_query_cache[workspace_id] = (now, data)
        return data

    async def _cached_list_agents(self, workspace_id: str) -> List[Dict]:
        now = time.time()
        ts, data = self._agents_query_cache.get(workspace_id, (0, None))
        if data is not None and now - ts < self.min_db_query_interval:
            return data
        data = await db_list_agents(workspace_id)
        self._agents_query_cache[workspace_id] = (now, data)
        return data

    async def _cached_active_workspaces(self) -> List[str]:
        now = time.time()
        ts, data = self._active_ws_cache
        if data and now - ts < self.min_db_query_interval:
            return data
        data = await get_active_workspaces()
        self._active_ws_cache = (now, data)
        return data

    async def get_agent_manager(self, workspace_id: str) -> Optional[AgentManager]:
        """Ottieni o crea un AgentManager per il workspace specificato"""
        try:
            workspace_uuid = UUID(workspace_id)
        except ValueError:
            logger.error(f"Invalid workspace ID format: {workspace_id}. Cannot get/create manager")
            return None
        
        # Se esiste già, restituiscilo
        if workspace_uuid in self.workspace_managers:
            return self.workspace_managers[workspace_uuid]
        
        # Crea nuovo manager
        logger.info(f"Creating new AgentManager for workspace {workspace_id}")
        try:
            manager = AgentManager(workspace_uuid)
            if await manager.initialize():
                self.workspace_managers[workspace_uuid] = manager
                logger.info(f"Initialized agent manager for workspace {workspace_id}")
                return manager
            else:
                logger.error(f"Failed to initialize agent manager for workspace {workspace_id}")
                return None
        except Exception as e:
            logger.error(f"Exception creating agent manager for W:{workspace_id}: {e}", exc_info=True)
            return None

    async def check_workspace_health(self, workspace_id: str) -> Dict[str, Any]:
        """Controlla lo stato di salute di un workspace"""
        try:
            all_tasks_db = await self._cached_list_tasks(workspace_id)
            agents_db = await self._cached_list_agents(workspace_id)
            
            # Conteggio task per status
            task_counts = Counter(t.get("status") for t in all_tasks_db)
            task_counts['total'] = len(all_tasks_db)

            # Analisi pattern problematici
            pattern_analysis = self._analyze_task_patterns(all_tasks_db, workspace_id)
            
            # Identificazione problemi di salute
            health_issues = []
            
            # Check pending eccessivi
            if task_counts[TaskStatus.PENDING.value] > self.max_pending_tasks_per_workspace:
                health_issues.append(f"Excessive pending: {task_counts[TaskStatus.PENDING.value]}/{self.max_pending_tasks_per_workspace}")
            
            # Check velocità di creazione task
            creation_velocity = self._calculate_task_creation_velocity(all_tasks_db)
            if creation_velocity > 5.0:
                health_issues.append(f"High task creation: {creation_velocity:.1f}/min")
            
            # Check pattern ripetuti
            if pattern_analysis['repeated_patterns']:
                health_issues.append(f"Repeated task names: {pattern_analysis['repeated_patterns']}")
            
            # Check delegation loop
            if pattern_analysis['delegation_loops']:
                health_issues.append(f"Delegation loops: {pattern_analysis['delegation_loops']}")
            
            # Check handoff falliti
            if pattern_analysis['failed_handoffs'] > 3:
                health_issues.append(f"High handoff failures: {pattern_analysis['failed_handoffs']}")
            
            # Check same-role recursion
            if pattern_analysis['same_role_recursion']:
                health_issues.append(f"Same-role recursion: {pattern_analysis['same_role_recursion']}")

            # Check task orfani (senza agente attivo)
            active_agent_ids = {agent['id'] for agent in agents_db if agent.get('status') == 'active'}
            orphaned_tasks_count = sum(1 for t in all_tasks_db if not t.get('agent_id') or t.get('agent_id') not in active_agent_ids)
            if orphaned_tasks_count > 0:
                health_issues.append(f"Orphaned tasks: {orphaned_tasks_count}")

            # Calcola health score
            health_score = self._calculate_improved_health_score(task_counts, health_issues, creation_velocity, pattern_analysis)
            
            return {
                'workspace_id': workspace_id,
                'task_counts': dict(task_counts),
                'health_issues': health_issues,
                'health_score': round(health_score, 2),
                'is_healthy': not health_issues and health_score > 70,
                'auto_generation_paused': workspace_id in self.workspace_auto_generation_paused,
                'pattern_analysis': pattern_analysis,
                'creation_velocity': round(creation_velocity, 2)
            }
            
        except Exception as e:
            logger.error(f"Error checking W:{workspace_id} health: {e}", exc_info=True)
            return {
                'workspace_id': workspace_id, 
                'error': str(e), 
                'is_healthy': False, 
                'health_score': 0
            }

    def _analyze_task_patterns(self, tasks_db: List[Dict], workspace_id_for_logs: str) -> Dict[str, Any]:
        """Analizza pattern problematici nei task"""
        # Analisi nomi ripetuti
        task_names = [t.get("name", "") for t in tasks_db]
        name_counts = Counter(task_names)
        repeated_patterns = {name: count for name, count in name_counts.items() if count > 3 and name}
        
        # Analisi delegation loops
        delegation_graph = defaultdict(list)
        delegation_loops_details = []
        
        # Ottieni attività recente per analizzare delegation
        recent_activity = self.get_recent_activity(workspace_id=workspace_id_for_logs, limit=100)
        
        for activity in recent_activity:
            if activity.get('event') == 'subtask_delegated':
                details = activity.get('details', {})
                source = details.get('delegated_by_agent_name', '')
                target = details.get('assigned_agent_name', '')
                if source and target:
                    delegation_graph[source].append(target)
        
        # Trova loop bidirezionali
        for source, targets in delegation_graph.items():
            for target in targets:
                if source in delegation_graph.get(target, []):
                    loop_desc = f"{source} <-> {target}"
                    if loop_desc not in delegation_loops_details:
                        delegation_loops_details.append(loop_desc)

        # Conta handoff falliti
        failed_handoffs_count = sum(1 for act in recent_activity 
                                   if act.get('event') == 'handoff_failed' or 
                                   (act.get('event') == 'task_failed' and "handoff" in act.get('task_name', '').lower()))
        
        # Trova same-role recursion
        same_role_recursion_details = []
        for act in recent_activity:
            if act.get('event') == 'subtask_delegated':
                details = act.get('details', {})
                source_role = details.get('source_agent_role', '').lower()
                target_role = details.get('target_agent_role_or_request', '').lower()
                if source_role and target_role and source_role == target_role:
                    desc = f"Role '{source_role}' to same role"
                    if desc not in same_role_recursion_details:
                        same_role_recursion_details.append(desc)
        
        # Trova cluster di descrizioni simili
        description_clusters = self._find_similar_task_descriptions(tasks_db)
        
        return {
            'repeated_patterns': repeated_patterns,
            'delegation_loops': delegation_loops_details,
            'failed_handoffs': failed_handoffs_count,
            'same_role_recursion': same_role_recursion_details,
            'description_clusters': description_clusters
        }

    def _find_similar_task_descriptions(self, tasks_db: List[Dict], threshold=0.8) -> List[Dict]:
        """Trova cluster di task con descrizioni simili"""
        if not difflib:
            return []
        
        clusters = []
        processed_indices = set()
        
        for i, task1_dict in enumerate(tasks_db):
            if i in processed_indices:
                continue
                
            desc1 = task1_dict.get('description', '')[:250].lower()
            if not desc1 or len(desc1) < 20:
                processed_indices.add(i)
                continue
            
            current_cluster = [task1_dict]
            processed_indices.add(i)
            
            for j, task2_dict in enumerate(tasks_db[i+1:], start=i+1):
                if j in processed_indices:
                    continue
                    
                desc2 = task2_dict.get('description', '')[:250].lower()
                if not desc2 or len(desc2) < 20:
                    processed_indices.add(j)
                    continue
                
                similarity = difflib.SequenceMatcher(None, desc1, desc2).ratio()
                if similarity >= threshold:
                    current_cluster.append(task2_dict)
                    processed_indices.add(j)
            
            if len(current_cluster) > 1:
                clusters.append({
                    'count': len(current_cluster),
                    'sample_names': [t.get('name', 'N/A') for t in current_cluster[:3]],
                    'snippet': desc1[:100] + "...",
                    'threshold': threshold
                })
        
        return clusters

    def _calculate_task_creation_velocity(self, tasks_db: List[Dict], window_min=30) -> float:
        """Calcola velocità di creazione task (task/minuto)"""
        if not tasks_db:
            return 0.0
        
        now = datetime.now()
        recent_creations = []
        
        for task_dict in tasks_db:
            created_at_str = task_dict.get('created_at')
            if created_at_str:
                try:
                    # Parse datetime con gestione timezone
                    dt = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    # Rimuovi timezone info per compatibility
                    if dt.tzinfo is not None:
                        dt = dt.replace(tzinfo=None)

                    if now - dt < timedelta(minutes=window_min):
                        recent_creations.append(dt)
                except ValueError:
                    logger.warning(f"Parse error: {created_at_str} for task {task_dict.get('id')}")

        if len(recent_creations) < 2:
            return 0.0
        
        # Calcola velocità
        recent_creations.sort()
        span_sec = (recent_creations[-1] - recent_creations[0]).total_seconds()
        return (len(recent_creations) / (span_sec / 60.0)) if span_sec > 0 else 0.0

    def _calculate_improved_health_score(
        self, 
        task_counts: Dict, 
        health_issues: List[str], 
        creation_velocity: float, 
        pattern_analysis: Dict
    ) -> float:
        """Calcola uno score di salute del workspace (0-100)"""
        score = 100.0
        
        # Penalità per health issues
        score -= len(health_issues) * 15
        
        # Penalità per ratio task pending elevato
        if task_counts.get('total', 0) > 0:
            pending_ratio = task_counts.get(TaskStatus.PENDING.value, 0) / task_counts['total']
            if pending_ratio > 0.75:
                score -= (pending_ratio - 0.75) * 100
            elif pending_ratio > 0.5:
                score -= (pending_ratio - 0.5) * 50
            
            # Bonus per completion rate alto
            completion_ratio = task_counts.get(TaskStatus.COMPLETED.value, 0) / task_counts['total']
            if completion_ratio > 0.7:
                score += completion_ratio * 10
        
        # Penalità per alta velocità di creazione
        if creation_velocity > 10.0:
            score -= min((creation_velocity - 10.0) * 5, 25)
        elif creation_velocity > 5.0:
            score -= min((creation_velocity - 5.0) * 3, 15)
        
        # Penalità per pattern problematici
        if pattern_analysis.get('repeated_patterns'):
            score -= min(len(pattern_analysis['repeated_patterns']) * 3, 10)
        
        if pattern_analysis.get('delegation_loops'):
            score -= min(len(pattern_analysis['delegation_loops']) * 10, 30)
        
        if pattern_analysis.get('description_clusters'):
            score -= min(len(pattern_analysis['description_clusters']) * 2, 10)
        
        if pattern_analysis.get('failed_handoffs', 0) > 2:
            score -= min(pattern_analysis['failed_handoffs'] * 2, 10)
        
        return max(0.0, min(100.0, score))

    async def periodic_runaway_check(self):
        """Controllo periodico per rilevare workspace in runaway"""
        logger.info("Starting periodic runaway check...")
        
        try:
            active_ws_ids = await get_active_workspaces()
            if not active_ws_ids:
                logger.info("No active workspaces for runaway check")
                return {'status': 'no_active_workspaces'}
            
            actions = []
            warnings = []
            
            for ws_id in active_ws_ids:
                health_status = await self.check_workspace_health(ws_id)
                
                health_score = health_status.get('health_score', 100)
                is_healthy = health_status.get('is_healthy', True)
                issues = health_status.get('health_issues', [])
                pending = health_status.get('task_counts', {}).get(TaskStatus.PENDING.value, 0)
                
                # Condizioni critiche che richiedono pausa automatica
                critical = (
                    health_score < 30 or
                    pending > (self.max_pending_tasks_per_workspace * 1.5) or
                    any('high task creation rate' in i.lower() and 
                        float(i.split(':')[-1].replace('/min', '').strip()) > 7.0 
                        for i in issues if 'high task creation rate' in i.lower())
                )

                if critical and ws_id not in self.workspace_auto_generation_paused:
                    reason = f"Runaway: Score={health_score}, Pending={pending}, Issues:{issues[:2]}"
                    await self._pause_auto_generation_for_workspace(ws_id, reason=reason)
                    actions.append({
                        'workspace_id': ws_id,
                        'action': 'paused_auto_gen',
                        'reason': reason
                    })
                elif not is_healthy and health_score < 60:
                    warnings.append({
                        'workspace_id': ws_id,
                        'health_score': health_score,
                        'issues': issues[:2]
                    })
            
            # Log risultati
            if actions:
                logger.critical(f"RUNAWAY CHECK: {len(actions)} workspaces paused: {actions}")
            if warnings:
                logger.warning(f"RUNAWAY CHECK: {len(warnings)} workspaces warning: {warnings}")
            if not actions and not warnings:
                logger.info(f"Runaway check: All {len(active_ws_ids)} workspaces stable")
            
            return {
                'timestamp': datetime.now().isoformat(),
                'checked': len(active_ws_ids),
                'actions': actions,
                'warnings': warnings,
                'paused_list': list(self.workspace_auto_generation_paused)
            }
            
        except Exception as e:
            logger.error(f"Error in periodic_runaway_check: {e}", exc_info=True)
            return {'error': str(e)}

    async def _pause_auto_generation_for_workspace(self, workspace_id: str, reason: str = "Runaway detected"):
        """Pausa auto-generation per un workspace specifico"""
        if workspace_id in self.workspace_auto_generation_paused:
            logger.info(f"Auto-gen for W:{workspace_id} already paused")
            return
        
        self.workspace_auto_generation_paused.add(workspace_id)
        logger.critical(f"AUTO-GENERATION PAUSED for W:{workspace_id}. Reason: {reason}")
        
        # Aggiorna status workspace nel DB se possibile
        try:
            ws_data = await get_workspace(workspace_id)
            if ws_data and ws_data.get("status") == WorkspaceStatus.ACTIVE.value:
                await update_workspace_status(workspace_id, WorkspaceStatus.NEEDS_INTERVENTION.value)
                logger.info(f"W:{workspace_id} status updated to 'needs_intervention'")
        except Exception as e:
            logger.error(f"Failed to update W:{workspace_id} status after pause: {e}")
        
        # Log l'evento
        self.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "event": "workspace_auto_generation_paused",
            "workspace_id": workspace_id,
            "reason": reason
        })

    async def _resume_auto_generation_for_workspace(self, workspace_id: str):
        """Riprende auto-generation per un workspace specifico"""
        if workspace_id not in self.workspace_auto_generation_paused:
            logger.info(f"Auto-gen for W:{workspace_id} not paused")
            return
        
        self.workspace_auto_generation_paused.remove(workspace_id)
        logger.info(f"AUTO-GENERATION RESUMED for W:{workspace_id}")
        
        # Aggiorna status workspace nel DB se possibile
        try:
            ws_data = await get_workspace(workspace_id)
            if ws_data and ws_data.get("status") == WorkspaceStatus.NEEDS_INTERVENTION.value:
                await update_workspace_status(workspace_id, WorkspaceStatus.ACTIVE.value)
                logger.info(f"W:{workspace_id} status restored to 'active'")
        except Exception as e:
            logger.error(f"Failed to update W:{workspace_id} status after resume: {e}")
        
        # Log l'evento
        self.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "event": "workspace_auto_generation_resumed",
            "workspace_id": workspace_id
        })

    async def check_for_new_workspaces(self):
        """Controlla workspace attivi che necessitano task iniziali"""
        # RIMUOVI questo check per permettere task iniziali sempre  
        # if self.paused or not self.auto_generation_enabled:
        #     logger.debug("Skip check_for_new_workspaces: Paused or global auto-gen disabled")
        #     return
        
        if self.paused:
            logger.debug("Skip check_for_new_workspaces: Executor paused")
            return

        try:
            logger.debug("Checking for active workspaces needing initial tasks...")
            active_ws_ids = await self._cached_active_workspaces()

            for ws_id in active_ws_ids:
                if ws_id in self.workspace_auto_generation_paused:
                    logger.info(f"Skip initial task for W:{ws_id}: auto-gen paused for this workspace")
                    continue

                # Se il workspace non ha task, crea task iniziale
                tasks = await self._cached_list_tasks(ws_id)
                if not tasks:
                    ws_data = await get_workspace(ws_id)
                    if ws_data and ws_data.get("status") == WorkspaceStatus.ACTIVE.value:
                        logger.info(f"W:{ws_id} ('{ws_data.get('name')}') active, no tasks. Creating initial task")
                        await self.create_initial_workspace_task(ws_id)
        except Exception as e:
            logger.error(f"Error in check_for_new_workspaces: {e}", exc_info=True)

    async def create_initial_workspace_task(self, workspace_id: str) -> Optional[str]:
        """Crea task iniziale per un workspace"""
        # RIMUOVI questo check per permettere task iniziali sempre
        # if not self.auto_generation_enabled:
        #     logger.info(f"Global auto-gen disabled. No initial task for W:{workspace_id}")
        #     return None
        if workspace_id in self.workspace_auto_generation_paused:
            logger.info(f"Auto-gen paused for W:{workspace_id}. No initial task")
            return None
        
        try:
            workspace = await get_workspace(workspace_id)
            if not workspace:
                logger.error(f"W:{workspace_id} not found for initial task")
                return None

            # Verifica se lo stato è 'created' prima di procedere
            if workspace.get("status") != WorkspaceStatus.CREATED.value:
                logger.info(f"W:{workspace_id} is not in 'created' state (current: {workspace.get('status')}). Initial task likely already created or process started.")
                # Potresti voler controllare se ci sono già task per decidere se procedere
                existing_tasks_check = await list_tasks(workspace_id)
                if existing_tasks_check:
                    logger.info(f"W:{workspace_id} already has tasks. Skipping initial task creation.")
                    return None # O l'ID del primo task se vuoi che il flusso continui
            
            agents = await db_list_agents(workspace_id)
            if not agents:
                logger.warning(f"No agents in W:{workspace_id}. No initial task")
                return None
            
            # Verifica se esistono già task
            existing_tasks = await list_tasks(workspace_id)
            if existing_tasks:
                logger.info(f"W:{workspace_id} already has {len(existing_tasks)} tasks. No initial task creation needed.")
                return None
            
            # Analizza composizione team e seleziona lead
            team_analysis = self._analyze_team_composition(agents)
            lead_agent = self._select_project_lead(agents, team_analysis)
            
            if not lead_agent:
                logger.error(f"No suitable lead in W:{workspace_id} for initial task")
                return None
            
            logger.info(f"Selected {lead_agent['name']} ({lead_agent['role']}) as lead for W:{workspace_id}")
            
            # Crea descrizione task strutturata
            description = self._create_structured_initial_task_description(workspace, lead_agent, team_analysis)
            task_name = "Project Setup & Strategic Planning Kick-off"
            
            # Crea task iniziale
            created_task = await create_task(
                workspace_id=str(workspace['id']),
                agent_id=str(lead_agent['id']),
                name=task_name,
                description=description,
                status=TaskStatus.PENDING.value,
                priority="high",

                # TRACKING AUTOMATICO
                creation_type="initial_workspace_setup",  # Task iniziale del workspace

                # CONTEXT DATA SPECIFICO
                context_data={
                    "workspace_initialization": True,
                    "selected_lead_agent": lead_agent['name'],
                    "selected_lead_role": lead_agent['role'],
                    "team_composition": {
                        "total_agents": team_analysis['total_agents'],
                        "leadership_candidates": len(team_analysis['leadership_candidates']),
                        "specialists_count": len(team_analysis['specialists']),
                        "available_domains": list(team_analysis['available_domains'])
                    },
                    "workspace_goal": workspace.get('goal', ''),
                    "workspace_budget": workspace.get('budget', {}),
                    "auto_generated": True,
                    "is_project_kickoff": True
                }
            )
            
            if created_task and created_task.get("id"):
                task_id = created_task["id"]
                logger.info(f"Created initial task {task_id} ('{task_name}') for W:{workspace_id}, assigned to {lead_agent['name']}")

                # AGGIORNAMENTO STATO WORKSPACE
                try:
                    if workspace.get("status") == WorkspaceStatus.CREATED.value:
                        await update_workspace_status(workspace_id, WorkspaceStatus.ACTIVE.value)
                        logger.info(f"Workspace {workspace_id} status updated to ACTIVE after initial task creation.")
                except Exception as e_ws_update:
                    logger.error(f"Failed to update workspace {workspace_id} status to active: {e_ws_update}")

                self.execution_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "event": "initial_workspace_task_created",
                    "task_id": task_id,
                    "agent_id": lead_agent["id"],
                    "workspace_id": workspace_id,
                    "task_name": task_name,
                    "assigned_role": lead_agent["role"]
                })
                return task_id
            else:
                logger.error(f"Failed to create initial task in DB for W:{workspace_id}. Response: {created_task}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating initial task for W:{workspace_id}: {e}", exc_info=True)
            # Se fallisce la creazione del task iniziale, il workspace potrebbe rimanere in 'created'
            # o passare a 'error'
            try:
                await update_workspace_status(workspace_id, WorkspaceStatus.ERROR.value)
                logger.info(f"Workspace {workspace_id} status set to ERROR due to failure in initial task creation.")
            except Exception as e_ws_status:
                logger.error(f"Additionally failed to set workspace {workspace_id} to ERROR: {e_ws_status}")
            return None

    def _analyze_team_composition(self, agents_list: List[Dict]) -> Dict[str, Any]:
        """Analizza la composizione del team"""
        composition = {
            'total_agents': len(agents_list),
            'by_seniority': Counter(),
            'by_role_type': Counter(),
            'available_domains': set(),
            'leadership_candidates': [],
            'specialists': []
        }
        
        seniority_levels = ['junior', 'senior', 'expert']
        
        for agent in agents_list:
            # Analisi seniority
            seniority = agent.get('seniority', 'junior').lower()
            if seniority in seniority_levels:
                composition['by_seniority'][seniority] += 1
            
            # Analisi ruolo
            role = agent.get('role', '').lower()
            role_type_assigned = False
            
            # Leadership roles
            if any(keyword in role for keyword in ['manager', 'coordinator', 'lead', 'director', 'project head']):
                composition['by_role_type']['leadership'] += 1
                composition['leadership_candidates'].append(agent)
                role_type_assigned = True
            
            # Specialist roles
            if 'analyst' in role:
                composition['by_role_type']['analyst'] += 1
                composition['specialists'].append(agent)
                role_type_assigned = True
            
            if 'researcher' in role:
                composition['by_role_type']['researcher'] += 1
                composition['specialists'].append(agent)
                role_type_assigned = True
            
            if 'developer' in role or 'engineer' in role:
                composition['by_role_type']['technical'] += 1
                composition['specialists'].append(agent)
                role_type_assigned = True
            
            if 'writer' in role or 'content' in role:
                composition['by_role_type']['content_creation'] += 1
                composition['specialists'].append(agent)
                role_type_assigned = True
            
            if not role_type_assigned and 'specialist' in role:
                composition['by_role_type']['specialist'] += 1
                composition['specialists'].append(agent)
            elif not role_type_assigned:
                composition['by_role_type']['other'] += 1
            
            # Estrai dominio dal ruolo
            domain = self._extract_domain_from_role(role)
            if domain:
                composition['available_domains'].add(domain)
        
        # Ordina candidati leadership per seniority
        composition['available_domains'] = sorted(list(composition['available_domains']))
        composition['leadership_candidates'].sort(
            key=lambda a: seniority_levels.index(a.get('seniority', 'junior').lower()) 
            if a.get('seniority', 'junior').lower() in seniority_levels else -1,
            reverse=True
        )
        
        return composition

    def _select_project_lead(self, agents_list: List[Dict], team_analysis: Dict) -> Optional[Dict]:
        """Seleziona l'agente più adatto come project lead"""
        # Prima scelta: agenti con ruolo di leadership
        if team_analysis['leadership_candidates']:
            return team_analysis['leadership_candidates'][0]
        
        # Seconda scelta: specialist senior/expert
        potential_leads = [
            agent for agent in team_analysis.get('specialists', [])
            if agent.get('seniority') in ['expert', 'senior']
        ]
        if potential_leads:
            potential_leads.sort(
                key=lambda a: ['junior', 'senior', 'expert'].index(a.get('seniority', 'junior').lower()),
                reverse=True
            )
            return potential_leads[0]
        
        # Terza scelta: qualsiasi agente senior/expert
        experienced_agents = [
            agent for agent in agents_list
            if agent.get('seniority') in ['expert', 'senior']
        ]
        if experienced_agents:
            experienced_agents.sort(
                key=lambda a: ['junior', 'senior', 'expert'].index(a.get('seniority', 'junior').lower()),
                reverse=True
            )
            return experienced_agents[0]
        
        # Ultima scelta: primo agente disponibile
        return agents_list[0] if agents_list else None

    def _create_structured_initial_task_description(
        self, 
        workspace_dict: Dict, 
        lead_agent_dict: Dict, 
        team_analysis: Dict
    ) -> str:
        """Crea descrizione strutturata per il task iniziale"""
        workspace_goal = workspace_dict.get('goal', 'No goal provided.')
        workspace_budget = workspace_dict.get('budget', {})
        
        budget_str = f"{workspace_budget.get('max_amount', 'N/A')} {workspace_budget.get('currency', '')} (Strategy: {workspace_budget.get('strategy', 'standard')})"
        
        description = f"""**PROJECT KICK-OFF: STRATEGIC PLANNING & TASK DEFINITION**

**Workspace Goal:** {workspace_goal}
**Budget Overview:** {budget_str}
**Assigned Project Lead:** You ({lead_agent_dict.get('name', 'N/A')} - {lead_agent_dict.get('role', 'N/A')})

**Core Responsibilities (Initial Task):**
1. **Analyze Workspace Goal**: Break into 3-5 actionable phases/milestones.
2. **Define Key Deliverables**: For each phase, specify measurable deliverables.
3. **Team & Resource Assessment**: Review team composition; map skills to phases; identify gaps.
4. **High-Level Execution Plan**: Outline phase sequence, dependencies, rough timelines.
5. **Define Initial Sub-Tasks**: Create 2-3 specific, actionable sub-tasks for Phase 1.
6. **Communication Protocol**: Briefly outline progress tracking & handoffs.

**Team Composition Overview:**
{self._format_team_composition_for_task_description(team_analysis)}

**Expected Output (Submit as result):**
* Document with: Phase breakdown, resource allocation ideas, 2-3 specific sub-tasks for Phase 1, coordination strategy notes.

**CRITICAL GUIDELINES:**
* Focus on planning & a few well-defined starter tasks.
* Empower team: Delegate effectively post-planning.
* This is planning; subsequent tasks execute the plan."""
        
        return description.strip()

    def _format_team_composition_for_task_description(self, team_analysis: Dict) -> str:
        """Formatta la composizione del team per la descrizione del task"""
        lines = [f"- Total Agents: {team_analysis['total_agents']}"]
        
        # Seniority mix
        seniority_str = ", ".join(f"{count} {level}" for level, count in team_analysis['by_seniority'].items() if count > 0)
        if seniority_str:
            lines.append(f"- Seniority Mix: {seniority_str}")
        
        # Role types
        role_str = ", ".join(f"{count} {role_type.replace('_', ' ').title()}" for role_type, count in team_analysis['by_role_type'].items() if count > 0)
        if role_str:
            lines.append(f"- Role Types: {role_str}")
        
        # Key domains
        if team_analysis['available_domains']:
            lines.append(f"- Key Domains: {', '.join(team_analysis['available_domains'])}")
        
        # Sample specialists
        if team_analysis.get('specialists'):
            specialist_sample = [f"{specialist['name']} ({specialist['role']})" for specialist in team_analysis['specialists'][:3]]
            if specialist_sample:
                lines.append(f"- Sample Specialists: {'; '.join(specialist_sample)}")
        
        return "\n".join(lines)

    def _extract_domain_from_role(self, role_str: str) -> Optional[str]:
        """Estrae il dominio di expertise da un ruolo"""
        role_lower = role_str.lower()
        
        domain_mapping = {
            'finance': ['finance', 'financial', 'accountant', 'investment'],
            'marketing': ['marketing', 'seo', 'social media', 'campaign'],
            'sales': ['sales', 'business development', 'client acquisition'],
            'product': ['product manager', 'ux design', 'ui design'],
            'technology': ['software engineer', 'developer', 'it support', 'data scientist', 'cybersecurity'],
            'hr': ['human resource', 'recruitment', 'talent acquisition'],
            'legal': ['legal counsel', 'lawyer', 'compliance'],
            'research': ['researcher', 'analyst']
        }
        
        for domain, keywords in domain_mapping.items():
            if any(keyword in role_lower for keyword in keywords):
                return domain
        
        return None

    def get_recent_activity(self, workspace_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Ottieni attività recente del sistema"""
        # Filtra per workspace se specificato
        logs = [log for log in self.execution_log if not workspace_id or log.get("workspace_id") == workspace_id]
        # Ordina per timestamp decrescente e limita
        return sorted(logs, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]
    
    def check_global_circuit_breaker(self) -> bool:
        """Verifica condizioni anomale e attiva circuit breaker se necessario"""
        try:
            # 1. Controllo task creation rate (troppi task/min)
            recent_task_creations = [
                log for log in self.execution_log 
                if log.get("event") in ["task_execution_started", "initial_task_created"]
                and (datetime.now() - datetime.fromisoformat(log.get("timestamp", "2020-01-01"))).total_seconds() < 60
            ]

            if len(recent_task_creations) > 20:  # >20 task al minuto
                logger.critical(f"🚨 CIRCUIT BREAKER: Task creation rate too high ({len(recent_task_creations)}/min)")
                self.paused = True
                self.pause_event.clear()
                self.auto_generation_enabled = False
                return True

            # 2. Controllo fallimenti consecutivi
            recent_failures = [
                log for log in self.execution_log 
                if log.get("event") in ["task_execution_failed", "task_execution_timeout"]
                and (datetime.now() - datetime.fromisoformat(log.get("timestamp", "2020-01-01"))).total_seconds() < 300
            ]

            if len(recent_failures) > 10:  # >10 fallimenti in 5 min
                logger.critical(f"🚨 CIRCUIT BREAKER: Failure rate too high ({len(recent_failures)}/5min)")
                self.paused = True
                self.pause_event.clear()
                return True

            return False

        except Exception as e:
            logger.error(f"Error in circuit breaker check: {e}")
            return False

    def get_detailed_stats(self) -> Dict[str, Any]:
        """Ottieni statistiche dettagliate dell'executor"""
        status = "running" if self.running and not self.paused else "paused" if self.paused else "stopped"
        
        # Statistiche base
        base_stats = {
            "executor_status": status,
            "anti_loop_mode_active": True,
            "tasks_in_queue": self.task_queue.qsize(),
            "active_tasks": self.active_tasks_count,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "task_timeout_seconds": self.execution_timeout,
            "global_auto_generation_enabled": self.auto_generation_enabled,
            "workspace_task_counts": dict(self.workspace_anti_loop_task_counts),
            "total_workspaces_tracked": len(self.task_completion_tracker),
            "total_delegation_chains": len(self.delegation_chain_tracker),
            "total_execution_log_entries": len(self.execution_log),
            # ENHANCED FINALIZATION PRIORITY STATS
            "finalization_priority_boost": FINALIZATION_TASK_PRIORITY_BOOST,
            "smart_prioritization_enabled": ENABLE_SMART_PRIORITIZATION
        }

        # Statistiche sessione
        completed_session = sum(1 for log in self.execution_log 
                               if log.get("event") == "task_execution_completed" and 
                               log.get("status_returned") == TaskStatus.COMPLETED.value)
        failed_session = sum(1 for log in self.execution_log 
                            if log.get("event") == "task_execution_failed" or 
                            (log.get("event") == "task_execution_completed" and 
                             log.get("status_returned") == TaskStatus.FAILED.value))
        timeout_session = sum(1 for log in self.execution_log 
                             if log.get("event") == "task_execution_timeout")

        # Attività per agente
        agent_activity = defaultdict(lambda: {"completed": 0, "failed": 0, "timed_out": 0, "total_cost": 0.0})
        for log in self.execution_log:
            agent_id = log.get("agent_id")
            if agent_id:
                if (log.get("event") == "task_execution_completed" and 
                    log.get("status_returned") == TaskStatus.COMPLETED.value):
                    agent_activity[agent_id]["completed"] += 1
                elif (log.get("event") == "task_execution_failed" or 
                      (log.get("event") == "task_execution_completed" and 
                       log.get("status_returned") == TaskStatus.FAILED.value)):
                    agent_activity[agent_id]["failed"] += 1
                elif log.get("event") == "task_execution_timeout":
                    agent_activity[agent_id]["timed_out"] += 1
        
        # Aggiorna con costi per agente
        for agent_id in agent_activity:
            agent_activity[agent_id]["total_cost"] = self.budget_tracker.get_agent_total_cost(agent_id)

        base_stats["session_task_summary"] = {
            "tasks_completed_successfully": completed_session,
            "tasks_failed": failed_session,
            "tasks_timed_out": timeout_session,
            "agent_activity_summary": dict(agent_activity)
        }

        # Statistiche budget
        base_stats["budget_tracker_summary"] = {
            "tracked_agents_count": len(self.budget_tracker.usage_log)
        }

        # Stato runaway protection
        base_stats["runaway_protection_status"] = {
            "paused_workspaces_for_auto_generation": list(self.workspace_auto_generation_paused),
            "last_runaway_check_timestamp": self.last_runaway_check.isoformat() if self.last_runaway_check else None,
            "runaway_check_interval_seconds": self.runaway_check_interval,
            "max_pending_tasks_per_workspace_limit": self.max_pending_tasks_per_workspace
        }

        # Attività auto-generation
        auto_gen_event_types = {"initial_workspace_task_created", "subtask_delegated", "follow_up_generated"}
        base_stats["auto_generation_activity"] = {
            "related_events_in_log": sum(1 for log in self.execution_log 
                                        if log.get("event") in auto_gen_event_types)
        }

        return base_stats
    
    async def process_task_with_coordination(self, task_dict: Dict[str, Any], manager: AgentManager) -> None:
        """
        Metodo unificato per processare task con coordinamento completo tra tutti i moduli.
        Garantisce consistenza nel tracking e anti-loop logic.
        """
        task_id = task_dict.get("id")
        workspace_id = task_dict.get("workspace_id")
        task_name = task_dict.get("name", "Unnamed Task")

        # 1. Track centralmente task processing prima di iniziare
        self.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "event": "coordinated_task_processing_started",
            "task_id": task_id,
            "workspace_id": workspace_id,
            "task_name": task_name
        })

        # 2. Estrai attributi di delegation dal DB o context_data
        delegation_depth = task_dict.get("delegation_depth", 0)  # Nuovo campo DB

        # Fallback al context_data se delegation_depth non è nel record principale
        if delegation_depth == 0 and isinstance(task_dict.get("context_data"), dict):
            delegation_depth = task_dict.get("context_data", {}).get("delegation_depth", 0)

        # Ottieni delegation chain dal context_data
        delegation_chain = []
        if isinstance(task_dict.get("context_data"), dict):
            delegation_chain = task_dict.get("context_data", {}).get("delegation_chain", [])

        # 3. Verifica anti-loop centralmente PRIMA dell'esecuzione
        if delegation_depth > self.max_delegation_depth:
            logger.warning(f"Task {task_id} exceeds max delegation depth ({delegation_depth} > {self.max_delegation_depth})")
            await self._force_complete_task(
                task_dict,
                f"Maximum delegation depth exceeded ({delegation_depth}/{self.max_delegation_depth})",
                status_to_set=TaskStatus.FAILED.value
            )
            return

        # Verifica lunghezza chain (doppio controllo)
        if len(delegation_chain) > self.max_delegation_depth:
            logger.warning(f"Task {task_id} has delegation chain too long ({len(delegation_chain)} > {self.max_delegation_depth})")
            await self._force_complete_task(
                task_dict,
                f"Delegation chain too long ({len(delegation_chain)} steps)",
                status_to_set=TaskStatus.FAILED.value
            )
            return

        # 4. Esecuzione coordinata con timeout unificato
        try:
            logger.info(f"Coordinated execution: Task {task_id} (depth: {delegation_depth}, chain: {len(delegation_chain)})")

            # Esegui con timeout unificato tramite AgentManager
            result = await asyncio.wait_for(
                manager.execute_task(UUID(task_id)), 
                timeout=self.execution_timeout
            )

            # 5. Log risultato intermedio
            self.execution_log.append({
                "timestamp": datetime.now().isoformat(),
                "event": "coordinated_task_executed",
                "task_id": task_id,
                "workspace_id": workspace_id,
                "delegation_depth": delegation_depth,
                "execution_successful": True
            })

            # 6. Post-processing coordinato con EnhancedTaskExecutor
            # Questo garantisce che post-processing sia soggetto alle stesse regole anti-loop
            try:
                # Crea oggetto Task per EnhancedTaskExecutor
                task_obj = Task.model_validate(task_dict)

                # Ottieni enhanced executor e processa
                from task_analyzer import get_enhanced_task_executor
                enhanced_executor = get_enhanced_task_executor()

                # Passa result e coordination context
                await enhanced_executor.handle_task_completion(
                    task_obj, 
                    result, 
                    workspace_id
                )

                logger.info(f"Coordinated task processing completed successfully for {task_id}")

            except Exception as post_error:
                logger.error(f"Error in post-processing for task {task_id}: {post_error}", exc_info=True)
                # Non fallire il task principale per errori di post-processing
                self.execution_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "event": "coordinated_post_processing_error",
                    "task_id": task_id,
                    "error": str(post_error)
                })

        except asyncio.TimeoutError:
            logger.error(f"Coordinated execution timeout for task {task_id} after {self.execution_timeout}s")
            await self._force_complete_task(
                task_dict,
                f"Coordinated execution timeout after {self.execution_timeout}s",
                status_to_set=TaskStatus.TIMED_OUT.value
            )

        except Exception as e:
            logger.error(f"Coordinated task processing error for {task_id}: {e}", exc_info=True)
            await self._force_complete_task(
                task_dict,
                f"Coordinated execution error: {str(e)[:200]}",
                status_to_set=TaskStatus.FAILED.value
            )

        finally:
            # 7. Log finale
            self.execution_log.append({
                "timestamp": datetime.now().isoformat(),
                "event": "coordinated_task_processing_finished",
                "task_id": task_id,
                "workspace_id": workspace_id
            })


# Aggiungi queste funzioni helper:

async def enable_quality_integration() -> Dict[str, Any]:
    """Abilita quality integration runtime"""
    
    if not QUALITY_SYSTEM_AVAILABLE:
        return {"success": False, "message": "Quality system not available"}
    
    if isinstance(task_executor, QualityEnhancedTaskExecutor):
        task_executor.quality_integration_enabled = True
        return {
            "success": True, 
            "message": "Quality integration enabled",
            "executor_type": "QualityEnhancedTaskExecutor"
        }
    else:
        return {
            "success": False, 
            "message": "Standard TaskExecutor in use, restart required for quality integration"
        }

async def disable_quality_integration() -> Dict[str, Any]:
    """Disabilita quality integration runtime"""
    
    if isinstance(task_executor, QualityEnhancedTaskExecutor):
        task_executor.quality_integration_enabled = False
        return {"success": True, "message": "Quality integration disabled"}
    else:
        return {"success": True, "message": "Quality integration not active"}

def get_quality_integration_status() -> Dict[str, Any]:
    """Ottieni stato quality integration"""
    
    return {
        "quality_system_available": QUALITY_SYSTEM_AVAILABLE,
        "executor_type": type(task_executor).__name__,
        "integration_enabled": (
            isinstance(task_executor, QualityEnhancedTaskExecutor) and 
            getattr(task_executor, 'quality_integration_enabled', False)
        ),
        "configuration": QualitySystemConfig.get_all_settings() if QUALITY_SYSTEM_AVAILABLE else None
    }

class QualityEnhancedTaskExecutor(TaskExecutor):
    """
    Enhanced TaskExecutor con integrazione AI Quality Assurance
    """
    
    def __init__(self):
        super().__init__()
        self.quality_integration_enabled = (
            QUALITY_SYSTEM_AVAILABLE and 
            QualitySystemConfig.INTEGRATE_WITH_EXISTING_DELIVERABLE_SYSTEM
        )
        
        if self.quality_integration_enabled:
            logger.info("🔍 EXECUTOR: Quality assurance integration enabled")
            self.last_quality_check = {}  # workspace_id -> datetime
            self.quality_check_interval = 300  # 5 minuti
        else:
            logger.info("🔄 EXECUTOR: Standard mode without quality integration")
    
    async def execution_loop(self):
        """Enhanced execution loop con quality assurance"""
        
        logger.info("Enhanced execution loop started with quality assurance integration")
        
        while self.running:
            try:
                await self.pause_event.wait()
                if not self.running:
                    break
                
                # Circuit breaker check (mantieni logica esistente)
                if self.check_global_circuit_breaker():
                    logger.critical("⚠️ CIRCUIT BREAKER ACTIVATED - System paused")
                    await asyncio.sleep(60)
                    continue
                
                # Process pending tasks (mantieni logica esistente)
                await self.process_pending_tasks_anti_loop()
                
                # Asset coordination (mantieni logica esistente)
                try:
                    active_workspaces = await get_active_workspaces()
                    for ws_id in active_workspaces:
                        await self.coordinate_asset_oriented_workflow(ws_id)
                except Exception as e:
                    logger.error(f"Error in asset coordination: {e}")
                
                # === NUOVA: Quality-enhanced deliverable check ===
                if self.quality_integration_enabled:
                    try:
                        await self._check_quality_enhanced_deliverables()
                    except Exception as e:
                        logger.error(f"Error in quality deliverable check: {e}")
                
                # Controlla nuovi workspace (mantieni logica esistente)
                if self.auto_generation_enabled:
                    await self.check_for_new_workspaces()
                
                # Controllo runaway periodico (mantieni logica esistente)  
                if (self.last_runaway_check is None or
                    (datetime.now() - self.last_runaway_check).total_seconds() > self.runaway_check_interval):
                    await self.periodic_runaway_check()
                    self.last_runaway_check = datetime.now()
                
                # Cleanup periodico (mantieni logica esistente)
                if datetime.now() - self.last_cleanup > timedelta(minutes=5):
                    await self._cleanup_tracking_data()
                
                await asyncio.sleep(10)
                
            except asyncio.CancelledError:
                logger.info("Enhanced execution loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in enhanced execution loop: {e}", exc_info=True)
                await asyncio.sleep(30)
        
        logger.info("Enhanced execution loop finished")
    
    async def _check_quality_enhanced_deliverables(self):
        """
        Controlla workspace pronti per deliverable con quality assurance
        """
        
        try:
            # Ottieni workspace attivi che potrebbero aver bisogno di deliverable
            active_workspaces = await get_active_workspaces()
            
            for workspace_id in active_workspaces:
                try:
                    # Controlla se è tempo di verificare questo workspace
                    if not self._should_check_workspace_for_quality(workspace_id):
                        continue
                    
                    # Tentativo di creare deliverable quality-enhanced
                    deliverable_id = await check_and_create_final_deliverable(workspace_id)
                    
                    if deliverable_id:
                        logger.info(f"🔍 QUALITY DELIVERABLE: Created {deliverable_id} for {workspace_id}")
                        
                        # Registra metriche se abilitato
                        if QualitySystemConfig.ENABLE_QUALITY_METRICS_COLLECTION:
                            try:
                                from backend.ai_quality_assurance.quality_integration import quality_metrics_collector
                                quality_metrics_collector.record_enhancement_activity(
                                    workspace_id, 
                                    deliverable_id, 
                                    "quality_enhanced_deliverable_creation", 
                                    True
                                )
                            except Exception as e:
                                logger.debug(f"Error recording quality metrics: {e}")
                        
                        # Aggiorna timestamp ultimo check
                        self.last_quality_check[workspace_id] = datetime.now()
                    
                except Exception as e_ws:
                    logger.error(f"Error creating quality deliverable for {workspace_id}: {e_ws}")
                    
                    # Fallback al sistema standard se abilitato
                    if QualitySystemConfig.FALLBACK_TO_STANDARD_SYSTEM_ON_ERROR:
                        try:
                            from backend.deliverable_aggregator import check_and_create_final_deliverable
                            fallback_id = await check_and_create_final_deliverable(workspace_id)
                            
                            if fallback_id:
                                logger.info(f"📦 FALLBACK DELIVERABLE: Created {fallback_id} for {workspace_id}")
                                
                        except Exception as fallback_error:
                            logger.error(f"Fallback deliverable also failed for {workspace_id}: {fallback_error}")
                    
        except Exception as e:
            logger.error(f"Error in _check_quality_enhanced_deliverables: {e}")
    
    def _should_check_workspace_for_quality(self, workspace_id: str) -> bool:
        """Determina se è tempo di controllare un workspace per deliverable di qualità"""
        
        last_check = self.last_quality_check.get(workspace_id)
        if not last_check:
            return True  # Mai controllato prima
        
        # Controlla solo ogni X minuti
        time_since_check = (datetime.now() - last_check).total_seconds()
        return time_since_check >= self.quality_check_interval
    
    def get_detailed_stats(self) -> Dict[str, Any]:
        """Override per includere statistiche quality integration"""
        
        base_stats = super().get_detailed_stats()
        
        if self.quality_integration_enabled:
            base_stats["quality_integration"] = {
                "enabled": True,
                "workspaces_monitored": len(self.last_quality_check),
                "last_quality_checks": {
                    ws_id: timestamp.isoformat() 
                    for ws_id, timestamp in self.last_quality_check.items()
                },
                "check_interval_seconds": self.quality_check_interval
            }
        else:
            base_stats["quality_integration"] = {"enabled": False}
        
        return base_stats

# Istanza globale del TaskExecutor

if QUALITY_SYSTEM_AVAILABLE and QualitySystemConfig.INTEGRATE_WITH_EXISTING_DELIVERABLE_SYSTEM:
    task_executor = QualityEnhancedTaskExecutor()
    logger.info("🔍 TASK EXECUTOR INITIALIZED: Quality-enhanced version")
else:
    task_executor = TaskExecutor()
    logger.info("📦 TASK EXECUTOR INITIALIZED: Standard version")

# Funzioni di controllo executor
async def start_task_executor():
    """Avvia il TaskExecutor"""
    await task_executor.start()

async def stop_task_executor():
    """Ferma il TaskExecutor"""
    await task_executor.stop()

async def pause_task_executor():
    """Pausa il TaskExecutor"""
    await task_executor.pause()

async def resume_task_executor():
    """Riprende il TaskExecutor"""
    await task_executor.resume()

def get_executor_stats() -> Dict[str, Any]:
    """Ottieni statistiche dell'executor"""
    return task_executor.get_detailed_stats()

def get_recent_executor_activity(workspace_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Ottieni attività recente dell'executor"""
    return task_executor.get_recent_activity(workspace_id=workspace_id, limit=limit)

# Funzioni di controllo manuale
async def trigger_initial_workspace_task(workspace_id: str) -> Optional[str]:
    """Trigger manuale per creare task iniziale in un workspace"""
    logger.info(f"Manual trigger for initial task in W:{workspace_id}")
    if not task_executor.running:
        logger.warning("Executor not running. Initial task creation might be limited")
    return await task_executor.create_initial_workspace_task(workspace_id)

async def trigger_runaway_check() -> Dict[str, Any]:
    """Trigger manuale per runaway check"""
    logger.info("Manual trigger for runaway check")
    if not task_executor.running:
        return {"success": False, "message": "Executor not running"}
    
    results = await task_executor.periodic_runaway_check()
    task_executor.last_runaway_check = datetime.now()
    
    return {
        "success": True,
        "message": "Runaway check manually triggered",
        "check_results": results,
        "current_runaway_status": {
            "paused_workspaces": list(task_executor.workspace_auto_generation_paused),
            "last_check": task_executor.last_runaway_check.isoformat()
        }
    }

async def reset_workspace_auto_generation(workspace_id: str) -> Dict[str, Any]:
    """Reset auto-generation per un workspace specifico"""
    logger.info(f"Manual trigger to reset auto-gen for W:{workspace_id}")
    if not task_executor.running:
        return {"success": False, "message": f"Executor not running for W:{workspace_id}"}
    
    if workspace_id in task_executor.workspace_auto_generation_paused:
        await task_executor._resume_auto_generation_for_workspace(workspace_id)
        health = await task_executor.check_workspace_health(workspace_id)
        return {
            "success": True,
            "message": f"Auto-gen resumed for W:{workspace_id}. Health score: {health.get('health_score', 'N/A')}",
            "workspace_unpaused": workspace_id not in task_executor.workspace_auto_generation_paused
        }
    else:
        return {"success": False, "message": f"Auto-gen not paused for W:{workspace_id}"}

def set_global_auto_generation(enabled: bool) -> Dict[str, Any]:
    """Abilita/disabilita auto-generation globalmente"""
    task_executor.auto_generation_enabled = enabled
    status_msg = "ENABLED" if enabled else "DISABLED"
    logger.info(f"Global auto-generation is now {status_msg}")
    return {
        "success": True,
        "message": f"Global auto-generation is {status_msg}",
        "current_status": task_executor.auto_generation_enabled
    }

# Funzioni di backward compatibility
def get_auto_generation_stats() -> Dict[str, Any]:
    """Backward compatibility: restituisce solo la sezione auto_generation_activity"""
    return task_executor.get_detailed_stats().get("auto_generation_activity", {})

def get_runaway_protection_status() -> Dict[str, Any]:
    """Backward compatibility: restituisce solo la sezione runaway_protection_status"""
    return task_executor.get_detailed_stats().get("runaway_protection_status", {})