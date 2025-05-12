import asyncio
import logging
import os
from typing import List, Dict, Any, Optional, Union
from uuid import UUID, uuid4
import json
from datetime import datetime, timedelta
import time
# from collections import Counter # Importato nel secondo file ma non usato nel codice fornito, lo lascio commentato

# Import da moduli del progetto
from models import TaskStatus, Task, AgentStatus, WorkspaceStatus, Agent as AgentModelPydantic # Rinomina per chiarezza
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
from task_analyzer import AutoTaskGenerator, EnhancedTaskExecutor, TaskAnalysisResult

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
            "gpt-4-turbo": {"input": 0.02, "output": 0.04}, # Esempio di altro modello
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002} # Esempio di altro modello
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
            "agent_id": agent_id, # Aggiunto per facilitare il filtro
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(total_cost, 6),
            "currency": "USD" # Esplicita la valuta
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
            agent_costs[agent_id] = {"total_cost": round(agent_total_cost, 6)}
            total_cost += agent_total_cost

            # Accumula i token per l'agente
            agent_input_tokens = 0
            agent_output_tokens = 0
            if agent_id in self.usage_log:
                for record in self.usage_log[agent_id]:
                    # Assumiamo che i record appartengano a questo workspace
                    # In un sistema complesso, potremmo dover filtrare per workspace_id qui se il tracker fosse globale
                    agent_input_tokens += record["input_tokens"]
                    agent_output_tokens += record["output_tokens"]
            agent_costs[agent_id]["total_input_tokens"] = agent_input_tokens
            agent_costs[agent_id]["total_output_tokens"] = agent_output_tokens
            total_tokens["input"] += agent_input_tokens
            total_tokens["output"] += agent_output_tokens


        return {
            "workspace_id": workspace_id,
            "total_cost": round(total_cost, 6),
            "agent_costs": agent_costs, # Dettaglio per agente
            "total_tokens": total_tokens, # Totale workspace
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
    """Enhanced Task Executor with automatic task generation, pause/resume, and detailed stats."""

    def __init__(self):
        """Initialize the enhanced task executor."""
        self.running = False
        self.paused = False # Stato di pausa
        self.pause_event = asyncio.Event() # Evento per sincronizzare la pausa
        self.pause_event.set() # Inizializza come non in pausa (l'evento è 'set')

        self.workspace_managers: Dict[UUID, AgentManager] = {}
        self.budget_tracker = BudgetTracker()
        self.execution_log: List[Dict[str, Any]] = [] # Log degli eventi di esecuzione

        # Configurazione concorrenza e coda
        self.max_concurrent_tasks = int(os.getenv("MAX_CONCURRENT_TASKS", 3)) # Limite task concorrenti
        self.max_queue_size = self.max_concurrent_tasks * 10 # Dimensione massima coda
        self.active_tasks_count = 0 # Contatore task attivi
        self.task_queue: asyncio.Queue = asyncio.Queue(maxsize=self.max_queue_size)
        self.worker_tasks: List[asyncio.Task] = [] # Riferimenti ai task worker

        # Componenti per automazione
        self.auto_generator = AutoTaskGenerator() # Potrebbe non essere usato direttamente qui ma nell'handler
        self.enhanced_handler = EnhancedTaskExecutor() # Handler per post-esecuzione (auto-generazione)

    async def start(self):
        """Start the task executor service."""
        if self.running:
            logger.warning("Task executor is already running.")
            return

        self.running = True
        self.paused = False
        self.pause_event.set() # Assicura che non sia in pausa
        self.execution_log = [] # Resetta il log all'avvio (o caricalo se persistente)
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
        self.paused = True # Considera lo stop come una pausa definitiva
        self.pause_event.set() # Sblocca eventuali attese sull'evento per permettere l'uscita dai loop

        # Invia segnali di terminazione ai worker (mettendo None nella coda)
        for i in range(len(self.worker_tasks)):
            try:
                # Usa timeout per evitare blocco se la coda è piena e i worker sono lenti a terminare
                await asyncio.wait_for(self.task_queue.put(None), timeout=2.0)
            except asyncio.TimeoutError:
                logger.warning(f"Timeout putting None signal in task_queue during stop (worker {i+1}/{len(self.worker_tasks)}).")
            except asyncio.QueueFull:
                 logger.warning(f"Queue full trying to put None signal during stop (worker {i+1}/{len(self.worker_tasks)}). May cause delay.")
                 # Potresti provare a cancellare i worker direttamente se la coda è bloccata
                 # for task in self.worker_tasks: task.cancel()

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
        self.pause_event.clear() # Blocca i wait() sull'evento
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
        self.pause_event.set() # Sblocca i wait() sull'evento
        logger.info("Task executor resumed.")

    async def execution_loop(self):
        """Main loop to periodically check for pending tasks and new workspaces."""
        while self.running:
            try:
                await self.pause_event.wait() # Attende qui se in pausa
                if not self.running: break # Esce se è stato fermato mentre era in pausa

                # Logica principale del loop
                logger.debug("Execution loop running: checking for tasks and workspaces.")
                await self.process_all_pending_tasks()
                await self.check_for_new_workspaces()

                # Intervallo di attesa
                await asyncio.sleep(10) # Controlla ogni 10 secondi

            except asyncio.CancelledError:
                logger.info("Execution loop cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in execution_loop: {e}", exc_info=True)
                # Attendi di più in caso di errore per evitare cicli rapidi di fallimenti
                await asyncio.sleep(30)
        logger.info("Execution loop finished.")


    async def _task_worker(self):
        """Worker process that takes tasks from the queue and executes them."""
        worker_id = uuid4() # ID univoco per il logging del worker
        logger.info(f"Task worker {worker_id} started.")
        while self.running:
            try:
                await self.pause_event.wait() # Attende qui se l'executor è in pausa
                if not self.running: break # Esce se è stato fermato mentre era in pausa

                manager: Optional[AgentManager] = None
                task_dict: Optional[Dict] = None
                try:
                    # Attendi un task dalla coda con timeout per poter controllare self.running
                    # e self.pause_event periodicamente anche se la coda è vuota
                    manager, task_dict = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue # Nessun task, torna all'inizio del loop per ricontrollare lo stato

                if task_dict is None: # Segnale di terminazione ricevuto
                    self.task_queue.task_done()
                    logger.info(f"Worker {worker_id} received termination signal.")
                    break # Esce dal loop del worker

                task_id = task_dict.get("id", "UnknownID")
                workspace_id = task_dict.get("workspace_id", "UnknownWS")
                logger.info(f"Worker {worker_id} picking up task: {task_id} from Workspace {workspace_id} (Queue size: {self.task_queue.qsize()})")

                # Incrementa contatore task attivi e esegui
                self.active_tasks_count += 1
                try:
                    # Assicurati che il manager sia valido prima di procedere
                    if manager is None:
                         raise ValueError(f"Received task {task_id} with a null manager.")
                    await self.execute_task_with_tracking(manager, task_dict)
                except Exception as e_exec:
                    # Logga l'errore specifico dell'esecuzione del task
                    logger.error(f"Worker {worker_id} failed executing task {task_id}: {e_exec}", exc_info=True)
                    # Lo stato del task dovrebbe essere già stato aggiornato a FAILED dentro execute_task_with_tracking
                finally:
                    # Decrementa contatore e segna il task come completato nella coda
                    self.active_tasks_count -= 1
                    self.task_queue.task_done()
                    logger.info(f"Worker {worker_id} finished processing task: {task_id}. Active tasks: {self.active_tasks_count}")

            except asyncio.CancelledError:
                logger.info(f"Task worker {worker_id} cancelled.")
                break # Esce dal loop del worker
            except Exception as e_worker:
                # Cattura errori imprevisti nel loop del worker stesso (non nell'esecuzione del task)
                logger.error(f"Unhandled error in task worker {worker_id}: {e_worker}", exc_info=True)
                # Attendi un po' prima di continuare per evitare cicli di errore veloci
                await asyncio.sleep(5)

        logger.info(f"Task worker {worker_id} exiting.")


    async def check_for_new_workspaces(self):
        """Check for active workspaces without any tasks and create an initial one."""
        if self.paused: return # Non fare nulla se in pausa

        try:
            logger.debug("Checking for workspaces needing initial tasks")
            active_ws_ids = await get_active_workspaces() # Prende solo ID di workspace attivi

            for ws_id in active_ws_ids:
                tasks = await list_tasks(ws_id)
                if not tasks: # Se non ci sono task per questo workspace attivo
                    workspace_data = await get_workspace(ws_id) # Prendi i dati completi del workspace
                    # Controlla di nuovo lo stato perché potrebbe essere cambiato
                    if workspace_data and workspace_data.get("status") == WorkspaceStatus.ACTIVE.value:
                        logger.info(f"Workspace {ws_id} ('{workspace_data.get('name')}') is active and has no tasks. Attempting to create initial task.")
                        await self.create_initial_workspace_task(ws_id)
                    elif not workspace_data:
                         logger.warning(f"Could not retrieve data for supposedly active workspace {ws_id} during initial task check.")
                    # else: logger.debug(f"Workspace {ws_id} is no longer active or check returned no data.")

        except Exception as e:
            logger.error(f"Error checking for new workspaces: {e}", exc_info=True)

    async def process_all_pending_tasks(self):
        """Find workspaces with pending tasks and queue them for processing."""
        if self.paused: return # Non fare nulla se in pausa

        try:
            logger.debug("Processing all pending tasks")
            # Ottieni gli ID dei workspace che hanno task PENDING
            workspaces_with_pending = await get_workspaces_with_pending_tasks()

            if workspaces_with_pending:
                 logger.info(f"Found {len(workspaces_with_pending)} workspaces with pending tasks. Checking queue status.")

            for workspace_id in workspaces_with_pending:
                # Controlla se la coda è piena prima di processare il workspace
                if self.task_queue.full():
                    logger.warning(f"Task queue is full (Size: {self.task_queue.qsize()}/{self.max_queue_size}). Skipping adding tasks from workspace {workspace_id} for now.")
                    continue # Passa al prossimo workspace se la coda è piena

                # Se c'è spazio, processa i task di questo workspace
                await self.process_workspace_tasks(workspace_id)

        except Exception as e:
            logger.error(f"Error processing all pending tasks: {e}", exc_info=True)

    async def process_workspace_tasks(self, workspace_id: str):
        """Fetch pending tasks for a specific workspace and add them to the queue."""
        if self.paused: return # Non fare nulla se in pausa

        try:
            manager = await self.get_agent_manager(workspace_id)
            if not manager:
                logger.error(f"Failed to get or initialize agent manager for workspace {workspace_id}. Cannot queue tasks.")
                # Considera se aggiornare lo stato del workspace a 'error' o simile
                return

            # Recupera i task PENDING dal DB per questo workspace
            tasks_db = await list_tasks(workspace_id)
            pending_tasks_dicts = [task for task in tasks_db if task.get("status") == TaskStatus.PENDING.value]

            if not pending_tasks_dicts:
                # logger.debug(f"No pending tasks found for workspace {workspace_id}.")
                return

            logger.info(f"Found {len(pending_tasks_dicts)} pending tasks for workspace {workspace_id}. Attempting to queue...")
            queued_count = 0
            for task_dict in pending_tasks_dicts:
                if self.task_queue.full():
                    logger.warning(f"Task queue became full while processing workspace {workspace_id}. Task {task_dict.get('id')} and subsequent tasks not added in this cycle.")
                    break # Esce dal loop for per questo workspace

                # Metti la tupla (manager, task_dict) nella coda
                try:
                    # Usiamo put_nowait perché abbiamo già controllato .full()
                    # Se ci fosse una race condition rara, catturerebbe l'eccezione
                    self.task_queue.put_nowait((manager, task_dict))
                    queued_count += 1
                    # Potresti opzionalmente aggiornare lo stato del task nel DB a "QUEUED" qui
                    # await update_task_status(task_dict["id"], "queued", {"detail": "Added to execution queue"})
                except asyncio.QueueFull:
                     logger.warning(f"QueueFull exception hit unexpectedly for task {task_dict.get('id')} in workspace {workspace_id}. Race condition?")
                     break # Interrompi l'aggiunta per questo workspace

            if queued_count > 0:
                logger.info(f"Successfully queued {queued_count}/{len(pending_tasks_dicts)} pending tasks for workspace {workspace_id}. Queue size: {self.task_queue.qsize()}")

        except Exception as e:
            logger.error(f"Error processing tasks for workspace {workspace_id}: {e}", exc_info=True)

    async def get_agent_manager(self, workspace_id: str) -> Optional[AgentManager]:
        """Get or create an AgentManager instance for a given workspace ID."""
        try:
            workspace_uuid = UUID(workspace_id)
        except ValueError:
            logger.error(f"Invalid workspace ID format: {workspace_id}. Cannot get/create manager.")
            return None

        # Controlla se esiste già nella cache in memoria
        if workspace_uuid in self.workspace_managers:
            # Potrebbe essere utile verificare se il manager è ancora 'valido' o reinizializzarlo periodicamente
            return self.workspace_managers[workspace_uuid]

        # Se non esiste, crealo e inizializzalo
        logger.info(f"Creating new AgentManager instance for workspace {workspace_id}.")
        try:
            manager = AgentManager(workspace_uuid) # Passa l'UUID
            success = await manager.initialize() # L'inizializzazione carica agenti, workspace, ecc.

            if success:
                self.workspace_managers[workspace_uuid] = manager
                logger.info(f"Initialized agent manager for workspace {workspace_id}")
                return manager
            else:
                # L'inizializzazione ha fallito (es. workspace non trovato nel DB, nessun agente)
                logger.error(f"Failed to initialize agent manager for workspace {workspace_id}. Check logs for details from AgentManager.")
                # Non memorizzare un manager non inizializzato
                return None
        except Exception as e:
            logger.error(f"Exception creating or initializing agent manager for workspace {workspace_id}: {e}", exc_info=True)
            return None

    async def execute_task_with_tracking(self, manager: AgentManager, task_dict: dict):
        """Executes a single task, tracks budget, logs events, and triggers post-processing."""
        task_id = task_dict.get("id")
        agent_id = task_dict.get("agent_id")
        workspace_id = task_dict.get("workspace_id")

        # Validazione preliminare
        if not all([task_id, agent_id, workspace_id]):
             missing = [k for k, v in {'task_id': task_id, 'agent_id': agent_id, 'workspace_id': workspace_id}.items() if not v]
             error_msg = f"Task data incomplete: missing {', '.join(missing)}. Cannot execute."
             logger.error(error_msg)
             if task_id: # Se almeno l'ID c'è, prova ad aggiornare lo stato
                 try:
                     await update_task_status(task_id, TaskStatus.FAILED.value, {"error": error_msg, "status_detail": "invalid_task_data"})
                 except Exception as db_err:
                      logger.error(f"Failed to update status for invalid task {task_id}: {db_err}")
             return # Non procedere

        start_time_tracking = time.time() # Tempo inizio esecuzione funzione
        model_for_budget = "unknown" # Default, verrà aggiornato dopo aver caricato l'agente
        estimated_input_tokens = 0 # Default

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
            agent_data_db = await get_agent(agent_id) # Assume che get_agent ritorni un dict o None
            if not agent_data_db:
                raise ValueError(f"Agent {agent_id} not found in database.") # Causa un FAILED controllato

            # Determina il modello LLM da usare (e per il budget)
            llm_config = agent_data_db.get("llm_config", {})
            model_for_budget = llm_config.get("model") # Prova a prenderlo dalla config specifica
            if not model_for_budget: # Fallback basato su seniority se non c'è config->model
                seniority_map = {"junior": "gpt-4.1-nano", "senior": "gpt-4.1-mini", "expert": "gpt-4.1"}
                model_for_budget = seniority_map.get(agent_data_db.get("seniority", "senior"), self.budget_tracker.default_model)
            logger.info(f"Executing task {task_id} ('{task_dict.get('name')}') with agent {agent_id} (Role: {agent_data_db.get('role', 'N/A')}) using model {model_for_budget}")

            # Stima input tokens (molto approssimativa, l'agente dovrebbe fornire dati reali)
            task_input_text = f"{task_dict.get('name', '')} {task_dict.get('description', '')}"
            estimated_input_tokens = max(1, len(task_input_text) // 4) # Evita 0 tokens, usa 4 char/token approx

            # Costruisci l'oggetto Task Pydantic per passarlo all'esecuzione
            # Assicurati che i campi obbligatori del modello Pydantic `Task` siano presenti
            try:
                task_pydantic_obj = Task(
                    id=UUID(task_id),
                    workspace_id=UUID(workspace_id),
                    agent_id=UUID(agent_id), # Già validato che non sia None
                    name=task_dict.get("name", "N/A"),
                    description=task_dict.get("description", ""),
                    status=TaskStatus.IN_PROGRESS, # Stato attuale
                    # Gestione date: usa quelle dal DB se presenti e valide, altrimenti now()
                    created_at=datetime.fromisoformat(task_dict["created_at"]) if task_dict.get("created_at") else datetime.now(),
                    updated_at=datetime.now(), # Aggiorna sempre l'updated_at all'inizio dell'esecuzione
                    result=task_dict.get("result"), # Include risultati precedenti se presenti
                    # Aggiungi altri campi se il modello Task li richiede (es. priority, dependencies)
                    # priority=task_dict.get("priority", 0),
                    # dependencies=task_dict.get("dependencies", []),
                )
            except (ValueError, TypeError, KeyError) as pydantic_error:
                logger.error(f"Error creating Pydantic Task object for task {task_id}: {pydantic_error}", exc_info=True)
                raise ValueError("Internal error preparing task object.") from pydantic_error

            # --- ESECUZIONE EFFETTIVA DEL TASK ---
            # Chiama il metodo execute_task del manager, passando l'oggetto Pydantic
            # Assumiamo che `manager.execute_task` ritorni un dizionario con l'output e potenzialmente i token usati
            # Se `execute_task` si aspetta solo l'UUID, cambia la chiamata in:
            # result_from_agent = await manager.execute_task(UUID(task_id))
            result_from_agent: Dict[str, Any] = await manager.execute_task(task_pydantic_obj)
            # ------------------------------------

            execution_time = time.time() - start_time_tracking # Tempo impiegato dall'agente

            # Estrai/stima output tokens e gestisci il risultato
            result_output = result_from_agent.get("output", "Task completed without explicit output.") if isinstance(result_from_agent, dict) else str(result_from_agent)
            # Stima output tokens (se non forniti dall'agente)
            actual_output_tokens = result_from_agent.get("usage", {}).get("output_tokens")
            estimated_output_tokens = actual_output_tokens if actual_output_tokens is not None else max(1, len(str(result_output)) // 4)
            # Usa i token reali se forniti dall'agente per il budget
            actual_input_tokens = result_from_agent.get("usage", {}).get("input_tokens")
            final_input_tokens = actual_input_tokens if actual_input_tokens is not None else estimated_input_tokens

            # Log budget usage
            usage_record = self.budget_tracker.log_usage(
                agent_id=agent_id, model=model_for_budget,
                input_tokens=final_input_tokens,
                output_tokens=estimated_output_tokens, # Usa la stima/valore reale ottenuto
                task_id=task_id
            )

            # Prepara il payload del risultato da salvare nel DB
            task_result_payload_for_db = {
                "output": result_output, # Salva l'output principale
                "status_detail": "completed_successfully",
                "execution_time_seconds": round(execution_time, 2),
                "model_used": model_for_budget,
                 # Salva i token usati (reali se disponibili, altrimenti stime)
                "tokens_used": {
                     "input": final_input_tokens,
                     "output": estimated_output_tokens,
                     "estimated": actual_input_tokens is None or actual_output_tokens is None # Flag per indicare se sono stime
                 },
                "cost_estimated": usage_record["total_cost"],
                 # Potresti voler includere altri metadati restituiti dall'agente
                "agent_metadata": result_from_agent.get("metadata") # Esempio
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
                    status=TaskStatus.COMPLETED, # Stato finale
                    result=task_result_payload_for_db, # Risultato completo salvato
                    created_at=task_pydantic_obj.created_at, # Mantieni l'originale
                    updated_at=datetime.now(), # Ora del completamento
                    # priority=task_pydantic_obj.priority, # Mantieni altri campi
                    # dependencies=task_pydantic_obj.dependencies,
                )
                # Chiama l'handler passando l'oggetto Task completato e il workspace ID
                await self.enhanced_handler.handle_task_completion(
                    completed_task=completed_task_pydantic_obj_for_handler,
                    task_result=task_result_payload_for_db, # Passa anche il payload per contesto
                    workspace_id=workspace_id # Passa il workspace ID esplicitamente
                )
                logger.info(f"Post-completion handler (e.g., auto-generation analysis) triggered for task {task_id}")
            except Exception as auto_error:
                # Logga errore nella fase di post-completamento ma non fallire il task principale
                logger.error(f"Error in post-completion handler for task {task_id}: {auto_error}", exc_info=True)
            # -----------------------------------------------------

        except Exception as e:
            # Gestione centralizzata degli errori durante l'esecuzione
            logger.error(f"Critical error executing task {task_id}: {e}", exc_info=True)
            execution_time_failed = time.time() - start_time_tracking

            # Stima conservativa dei token per il budget in caso di fallimento
            # Usa l'input stimato se disponibile, altrimenti 0
            input_tokens_failed = estimated_input_tokens if estimated_input_tokens > 0 else 0
            output_tokens_failed = 50 # Un piccolo numero per rappresentare un output di errore o interrotto

            # Logga comunque il costo stimato del tentativo fallito
            usage_record_failed = self.budget_tracker.log_usage(
                agent_id=agent_id, model=model_for_budget, # Usa il modello determinato, se disponibile
                input_tokens=input_tokens_failed,
                output_tokens=output_tokens_failed, task_id=task_id
            )

            # Prepara payload di errore per il DB
            error_payload_for_db = {
                "error": str(e), # Messaggio di errore
                "status_detail": "failed_during_execution",
                "execution_time_seconds": round(execution_time_failed, 2),
                "cost_estimated": usage_record_failed["total_cost"] # Costo del tentativo
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
                # Considera di aggiornare lo stato del workspace a "needs_agents" o simile
                # await update_workspace_status(workspace_id, WorkspaceStatus.NEEDS_SETUP.value, {"reason": "No agents found"})
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
                description=task_description.strip(), # Rimuovi spazi bianchi extra
                status=TaskStatus.PENDING.value, # Inizia come pending
                # Potresti aggiungere priorità qui se il modello la supporta
                # priority=10
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
                 # Assicura che il filtro usi UUID se gli ID nel log sono UUID
                 # workspace_uuid_filter = UUID(workspace_id) # Se usi UUID
                 logs_to_filter = [log for log in logs_to_filter if log.get("workspace_id") == workspace_id]
            except ValueError:
                 logger.warning(f"Invalid workspace_id format '{workspace_id}' for filtering recent activity.")
                 return [] # Ritorna lista vuota se l'ID non è valido per il filtro

        # Ordina dal più recente al meno recente e limita
        logs_to_filter.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return logs_to_filter[:limit]

    def get_auto_generation_stats(self) -> Dict[str, Any]:
        """Get statistics specifically about auto-generated tasks or related events."""
        # Definisci gli eventi che indicano auto-generazione o handoff
        auto_gen_event_types = {
            "auto_task_generated", # Assumendo che l'handler logghi questo evento
            "follow_up_generated",
            "handoff_requested",
            "subtask_created_by_agent" # Se l'agente stesso logga quando crea un task
            # Aggiungere altri tipi di eventi rilevanti qui
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
            "recent_auto_generation_events": auto_gen_events[:10], # Mostra i 10 più recenti
            "auto_generation_enabled": True # Assumendo sia sempre attivo in questa versione
        }

    def get_detailed_stats(self) -> Dict[str, Any]:
            """Gathers detailed operational statistics about the executor."""
            tasks_completed = 0
            tasks_failed = 0
            # Usa un dizionario per tracciare le statistiche per agente
            # agent_id -> {"completed": count, "failed": count, "total_cost": float, "name": str, "role": str}
            agent_activity: Dict[str, Dict[str, Any]] = {}

            # Processa il log di esecuzione per contare successi e fallimenti
            for log_entry in self.execution_log:
                event = log_entry.get("event")
                agent_id = log_entry.get("agent_id")
                task_id = log_entry.get("task_id") # Utile per debug

                # Ignora eventi senza agent_id per le statistiche per agente
                if not agent_id:
                    if event == "task_completed": tasks_completed += 1
                    elif event == "task_failed": tasks_failed += 1
                    continue

                # Inizializza le statistiche per l'agente se non già presenti
                if agent_id not in agent_activity:
                    agent_activity[agent_id] = {
                        "completed": 0,
                        "failed": 0,
                        "total_cost": 0.0, # Verrà aggiornato dal budget tracker
                        "name": "Unknown", # Placeholder, idealmente arricchito dopo
                        "role": "Unknown"   # Placeholder
                    }

                # Aggiorna i conteggi
                if event == "task_completed":
                    tasks_completed += 1
                    agent_activity[agent_id]["completed"] += 1
                elif event == "task_failed":
                    tasks_failed += 1
                    agent_activity[agent_id]["failed"] += 1

            # Arricchisci le statistiche degli agenti con il costo totale dal BudgetTracker
            # e potenzialmente nome/ruolo (anche se recuperare qui può essere lento)
            all_agent_ids_in_stats = list(agent_activity.keys())
            # Potrebbe essere necessario un loop async qui se get_agent è async e vogliamo i nomi/ruoli aggiornati
            # Ma per ora, usiamo solo i dati del budget tracker che sono sincroni
            for agent_id in all_agent_ids_in_stats:
                 agent_total_cost = self.budget_tracker.get_agent_total_cost(agent_id)
                 agent_activity[agent_id]["total_cost"] = round(agent_total_cost, 6)
                 # Recuperare nome/ruolo qui richiederebbe chiamate al DB (potenzialmente async)
                 # Sarebbe meglio se il log contenesse già queste info o avere una cache agent_id -> details
                 # agent_db_data = await get_agent(agent_id) # Non si può fare await qui direttamente
                 # if agent_db_data:
                 #    agent_activity[agent_id]["name"] = agent_db_data.get("name", "N/A")
                 #    agent_activity[agent_id]["role"] = agent_db_data.get("role", "N/A")


            # Stato attuale dell'executor
            current_status = "stopped"
            if self.running:
                current_status = "paused" if self.paused else "running"


            return {
                "executor_status": current_status,
                "tasks_in_queue": self.task_queue.qsize(),
                "queue_capacity": self.max_queue_size,
                "tasks_actively_processing": self.active_tasks_count,
                "max_concurrent_tasks": self.max_concurrent_tasks,
                "total_execution_log_entries": len(self.execution_log),
                "session_task_stats": { # Statistiche dall'inizio dell'istanza corrente
                    "tasks_completed_successfully": tasks_completed,
                    "tasks_failed": tasks_failed,
                },
                 "agent_activity_summary": agent_activity, # Dettaglio per agente
                 "budget_tracker_summary": {
                     "tracked_agents_count": len(self.budget_tracker.usage_log),
                     # Potresti aggiungere un costo totale aggregato qui se utile
                     # "total_session_cost": sum(agent_stats["total_cost"] for agent_stats in agent_activity.values())
                 },
                 "auto_generation_summary": self.get_auto_generation_stats() # Include le stats specifiche di auto-gen
            }


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
     # Nota: questa funzione è sincrona, chiama un metodo sincrono dell'executor
     return task_executor.get_detailed_stats()

def get_recent_executor_activity(workspace_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
     """Get recent activity logs, optionally filtered by workspace."""
     # Nota: questa funzione è sincrona
     return task_executor.get_recent_activity(workspace_id=workspace_id, limit=limit)

async def trigger_initial_workspace_task(workspace_id: str) -> Optional[str]:
    """Manually trigger the creation of an initial task for a specific workspace."""
    # Nota: questa funzione è asincrona perché create_initial_workspace_task lo è
    return await task_executor.create_initial_workspace_task(workspace_id)

# Esempio di come potresti avviare e fermare l'executor in un'applicazione principale
# async def main():
#     print("Starting executor...")
#     await start_task_executor()
#     try:
#         # Tieni l'applicazione in esecuzione (es. un server web o un loop infinito)
#         while True:
#             # Ogni tanto stampa le statistiche
#             stats = get_executor_stats()
#             print(f"Executor Status: {stats['executor_status']}, Queue: {stats['tasks_in_queue']}, Active: {stats['tasks_actively_processing']}")
#             await asyncio.sleep(60)
#     except KeyboardInterrupt:
#         print("Shutdown signal received.")
#     finally:
#         print("Stopping executor...")
#         await stop_task_executor()
#         print("Executor stopped.")

# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#     # Configura il logger specifico per questo modulo se necessario
#     # logger = logging.getLogger(__name__)
#     # logger.setLevel(logging.DEBUG) # Imposta a DEBUG per vedere più dettagli
#     asyncio.run(main())