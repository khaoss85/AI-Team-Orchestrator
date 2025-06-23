# backend/ai_agents/manager.py
import logging
import os
import asyncio
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta

from database import (
    list_agents as db_list_agents_from_db,
    list_tasks as db_list_tasks_from_db,
    get_workspace,
    update_task_status,
    update_agent_status
)
from models import (
    Agent as AgentModelPydantic,
    Task,
    TaskStatus,
    AgentStatus,
    AgentHealth,
    HealthStatus
)
from ai_agents.specialist import SpecialistAgent

logger = logging.getLogger(__name__)

class AgentManager:
    def __init__(self, workspace_id: UUID):
        self.workspace_id = workspace_id
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY not set")
        
        self.agents: Dict[UUID, SpecialistAgent] = {}
        
        # ANTI-LOOP CONFIGURATIONS
        self.execution_timeout = 180  # 3 minuti timeout per task
        self.max_retries = 1  # Massimo 1 retry per task
        self.task_execution_cache: Dict[str, datetime] = {}
        self.failed_tasks_cache: Dict[str, int] = {}
        
        # Monitoring
        self.initialization_time: Optional[datetime] = None
        self.last_health_check: Optional[datetime] = None

    async def initialize(self) -> bool:
        """
        Carica il workspace e inizializza tutti i SpecialistAgent.
        Versione migliorata con gestione errori completa e anti-loop.
        """
        try:
            start_time = datetime.now()
            
            # Verifica workspace esistente
            workspace = await get_workspace(str(self.workspace_id))
            if not workspace:
                logger.error(f"Workspace {self.workspace_id} non trovato. Impossibile inizializzare.")
                return False

            logger.info(f"Initializing AgentManager for workspace {self.workspace_id} "
                        f"(name={workspace.get('name','N/A')})")

            # Recupera agenti dal database con retry
            raw_agents = await self._safe_fetch_agents()
            if raw_agents is None:
                logger.error(f"Failed to fetch agents for workspace {self.workspace_id}")
                return False

            if not raw_agents:
                logger.info(f"Nessun agente per workspace {self.workspace_id}. Manager pronto comunque.")
                self.initialization_time = datetime.now()
                return True

            # Validazione e creazione SpecialistAgent
            valid_agents = await self._validate_and_create_agents(raw_agents)
            
            # Verifica che almeno un agente sia stato creato correttamente
            if not valid_agents:
                logger.warning(f"Nessun agente valido creato per workspace {self.workspace_id}.")
                # Return True comunque per permettere funzionamento base
                self.initialization_time = datetime.now()
                return True

            logger.info(f"Inizializzati {len(valid_agents)}/{len(raw_agents)} SpecialistAgent "
                       f"in {(datetime.now() - start_time).total_seconds():.2f}s")
            
            # Health check iniziale (opzionale)
            await self._initial_health_check()
            
            self.initialization_time = datetime.now()
            return True

        except Exception as e:
            logger.error(
                f"Errore critico inizializzazione AgentManager per workspace {self.workspace_id}: {e}",
                exc_info=True
            )
            return False

    async def _safe_fetch_agents(self, max_retries: int = 3) -> Optional[List[Dict]]:
        """Fetch agenti con retry logic"""
        for attempt in range(max_retries):
            try:
                agents = await db_list_agents_from_db(str(self.workspace_id))
                return agents
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed to fetch agents: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                else:
                    logger.error(f"All attempts failed to fetch agents: {e}")
                    return None

    async def _validate_and_create_agents(self, raw_agents: List[Dict]) -> List[AgentModelPydantic]:
        """Valida e crea SpecialistAgent con gestione errori robusta"""
        logger.info(f"Starting validation of {len(raw_agents)} raw agents")
        valid_agents: List[AgentModelPydantic] = []
        
        for i, agent_data in enumerate(raw_agents):
            try:
                logger.debug(f"Validating agent {i+1}/{len(raw_agents)}: {agent_data.get('name', 'Unknown')} (ID: {agent_data.get('id', '?')})")
                # Validazione Pydantic
                agent_model = AgentModelPydantic.model_validate(agent_data)
                valid_agents.append(agent_model)
                logger.debug(f"✅ Successfully validated agent: {agent_model.name}")
            except Exception as e:
                logger.error(
                    f"❌ Validazione fallita per agent ID {agent_data.get('id','?')}, name: {agent_data.get('name', 'Unknown')}: {e}",
                    exc_info=True
                )
                # Continua con gli altri agenti invece di fallire completamente

        if not valid_agents:
            logger.warning("No valid agents after Pydantic validation")
            return []

        logger.info(f"Successfully validated {len(valid_agents)}/{len(raw_agents)} agents")

        # Creazione SpecialistAgent con gestione errori
        successful_agents = []
        for i, agent_model in enumerate(valid_agents):
            try:
                logger.debug(f"Creating SpecialistAgent {i+1}/{len(valid_agents)}: {agent_model.name} (ID: {agent_model.id})")
                # Crea SpecialistAgent passando tutti gli agenti per handoff
                specialist = SpecialistAgent(
                    agent_data=agent_model,
                    all_workspace_agents_data=valid_agents  # Passa tutti per handoff
                )
                self.agents[agent_model.id] = specialist
                successful_agents.append(agent_model)
                logger.info(f"✅ Creato SpecialistAgent per {agent_model.name} (ID: {agent_model.id})")
            except Exception as e:
                logger.error(
                    f"❌ Errore creazione SpecialistAgent {agent_model.id} ({agent_model.name}): {e}",
                    exc_info=True
                )
                # Continua comunque con altri agenti

        logger.info(f"Successfully created {len(successful_agents)}/{len(valid_agents)} SpecialistAgents")
        logger.info(f"Initialized agent IDs: {[str(aid) for aid in self.agents.keys()]}")
        return successful_agents

    async def _initial_health_check(self):
        """Health check iniziale opzionale"""
        try:
            healthy_count = 0
            for agent_id, specialist in self.agents.items():
                try:
                    # FIX: Serializza datetime per JSON
                    health_dict = {
                        "status": HealthStatus.HEALTHY.value,  # Usa .value per enum
                        "last_update": datetime.now().isoformat(),  # Converti a string
                        "details": {"initialization": "completed"}
                    }

                    await update_agent_status(
                        str(agent_id),
                        None,
                        health_dict  # Ora è un dict serializzabile
                    )
                    healthy_count += 1
                except Exception as e:
                    logger.warning(f"Health check failed for agent {agent_id}: {e}")

            logger.info(f"Initial health check completed: {healthy_count}/{len(self.agents)} agents healthy")
            self.last_health_check = datetime.now()
        except Exception as e:
            logger.warning(f"Initial health check failed: {e}")

    async def verify_all_agents(self) -> Dict[UUID, bool]:
        """
        Esegue verify_capabilities() su tutti gli agenti caricati.
        Versione migliorata con timeout e gestione errori.
        """
        results: Dict[UUID, bool] = {}
        
        if not self.agents:
            logger.warning(f"Nessun agente da verificare in manager per workspace {self.workspace_id}.")
            return results

        verification_tasks = []
        for agent_id, specialist in self.agents.items():
            verification_tasks.append(
                self._verify_single_agent(agent_id, specialist)
            )

        # Esegui verifiche in parallelo con timeout
        try:
            verification_results = await asyncio.wait_for(
                asyncio.gather(*verification_tasks, return_exceptions=True),
                timeout=30.0  # 30 secondi timeout totale
            )
            
            for i, (agent_id, _) in enumerate(self.agents.items()):
                result = verification_results[i]
                if isinstance(result, Exception):
                    logger.error(f"Verification failed for agent {agent_id}: {result}")
                    results[agent_id] = False
                else:
                    results[agent_id] = result

        except asyncio.TimeoutError:
            logger.warning("Agent verification timed out, marking all as failed")
            for agent_id in self.agents.keys():
                results[agent_id] = False

        success_count = sum(1 for success in results.values() if success)
        logger.info(f"Agent verification completed: {success_count}/{len(results)} successful")
        return results

    async def _verify_single_agent(self, agent_id: UUID, specialist: SpecialistAgent) -> bool:
        """Verifica singolo agente con timeout"""
        try:
            return await asyncio.wait_for(
                specialist.verify_capabilities(),
                timeout=10.0  # 10 secondi per agente
            )
        except asyncio.TimeoutError:
            logger.warning(f"Verification timeout for agent {agent_id}")
            return False
        except Exception as e:
            logger.error(f"Verification error for agent {agent_id}: {e}")
            return False

    async def execute_task(self, task_id: UUID) -> Dict[str, Any]:
        """
        Recupera il Task dal DB e lo invia all'agente assegnato.
        Versione migliorata con anti-loop, timeout e retry logic.
        """
        task_id_str = str(task_id)
        
        # ANTI-LOOP: Controlla se task è già in esecuzione
        if task_id_str in self.task_execution_cache:
            last_execution = self.task_execution_cache[task_id_str]
            if datetime.now() - last_execution < timedelta(minutes=5):
                error_msg = f"Task {task_id} already executing or recently executed"
                logger.warning(error_msg)
                raise ValueError(error_msg)
        
        # Registra esecuzione
        self.task_execution_cache[task_id_str] = datetime.now()
        
        try:
            # 1. Recupera task con retry
            task = await self._safe_fetch_task(task_id)
            if not task:
                raise ValueError(f"Task {task_id} non trovato in workspace {self.workspace_id}")

            # 2. Verifica agent_id
            if not task.agent_id:
                await self._handle_task_failure(
                    task_id_str, 
                    "Task privo di agent_id", 
                    {"detail": "missing_agent_id"}
                )
                raise ValueError(f"Task {task_id} privo di agent_id")

            # 3. Verifica agente esiste e è inizializzato
            agent_uuid = UUID(str(task.agent_id))
            specialist = self.agents.get(agent_uuid)
            
            if not specialist:
                available_agent_list = list(str(aid) for aid in self.agents.keys())
                error_detail = {
                    "detail": "agent_not_found",
                    "available_agents": available_agent_list,
                    "requested_agent": str(agent_uuid),
                    "total_initialized_agents": len(self.agents),
                    "initialization_time": self.initialization_time.isoformat() if self.initialization_time else None
                }
                
                logger.error(f"🚨 AGENT NOT FOUND - Task {task_id} requires agent {agent_uuid} but it's not initialized")
                logger.error(f"   Available agents ({len(self.agents)}): {available_agent_list}")
                logger.error(f"   Manager initialized at: {self.initialization_time}")
                logger.error(f"   Task details - Name: {task.name}, Status: {task.status}")
                
                await self._handle_task_failure(
                    task_id_str,
                    f"Agent {agent_uuid} non inizializzato nel manager",
                    error_detail
                )
                raise ValueError(f"Agent {agent_uuid} non inizializzato nel manager per task {task_id}")

            # 4. Controlla failures precedenti
            failure_count = self.failed_tasks_cache.get(task_id_str, 0)
            if failure_count >= self.max_retries:
                logger.warning(f"Task {task_id} exceeded max retries ({self.max_retries})")
                await self._handle_task_failure(
                    task_id_str,
                    f"Task exceeded max retries ({self.max_retries})",
                    {"detail": "max_retries_exceeded", "retry_count": failure_count}
                )
                raise ValueError(f"Task {task_id} exceeded maximum retries")

            # 5. Esecuzione con timeout
            logger.info(f"Dispatching task {task_id} -> agent {specialist.agent_data.name}")
            
            try:
                result = await asyncio.wait_for(
                    specialist.execute_task(task),
                    timeout=self.execution_timeout
                )
                
                # Cleanup cache su successo
                self.failed_tasks_cache.pop(task_id_str, None)
                
                return result

            except asyncio.TimeoutError:
                error_msg = f"Task {task_id} execution timed out after {self.execution_timeout}s"
                logger.error(error_msg)
                await self._handle_task_failure(
                    task_id_str,
                    error_msg,
                    {"detail": "execution_timeout", "timeout_seconds": self.execution_timeout}
                )
                raise ValueError(error_msg)

        except ValueError:
            # Re-raise ValueError (già loggati)
            raise
        except Exception as e:
            # Increment failure count per retry logic
            self.failed_tasks_cache[task_id_str] = failure_count + 1
            
            error_msg = f"Unexpected error executing task {task_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            await self._handle_task_failure(
                task_id_str,
                error_msg,
                {"detail": "unexpected_error", "error_type": type(e).__name__}
            )
            raise ValueError(error_msg)
        
        finally:
            # Cleanup execution cache dopo un po'
            asyncio.create_task(self._cleanup_execution_cache(task_id_str))

    async def _safe_fetch_task(self, task_id: UUID, max_retries: int = 3) -> Optional[Task]:
        """Recupera task con retry logic"""
        for attempt in range(max_retries):
            try:
                all_tasks = await db_list_tasks_from_db(str(self.workspace_id))
                task_record = next((t for t in all_tasks if UUID(t["id"]) == task_id), None)
                
                if task_record:
                    return Task.model_validate(task_record)
                else:
                    return None
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retries} to fetch task {task_id} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))
                else:
                    logger.error(f"All attempts to fetch task {task_id} failed")
                    return None

    async def _handle_task_failure(self, task_id_str: str, error_msg: str, error_detail: Dict[str, Any]):
        """Gestisce il fallimento di un task con logging e update DB"""
        try:
            await update_task_status(
                task_id_str, 
                TaskStatus.FAILED.value,
                {"error": error_msg, **error_detail}
            )
        except Exception as e:
            logger.error(f"Failed to update task status for {task_id_str}: {e}")

    async def _cleanup_execution_cache(self, task_id_str: str):
        """Cleanup della cache di esecuzione dopo un delay"""
        await asyncio.sleep(300)  # 5 minuti delay
        self.task_execution_cache.pop(task_id_str, None)

    # Metodi di utilità e monitoring
    def get_health_status(self) -> Dict[str, Any]:
        """Ritorna lo stato di salute del manager"""
        return {
            "workspace_id": str(self.workspace_id),
            "agents_count": len(self.agents),
            "agents_ids": [str(aid) for aid in self.agents.keys()],
            "initialization_time": self.initialization_time.isoformat() if self.initialization_time else None,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "cached_executions": len(self.task_execution_cache),
            "failed_tasks_cache": len(self.failed_tasks_cache)
        }

    async def cleanup_caches(self):
        """Cleanup delle cache periodico"""
        try:
            # Cleanup execution cache
            current_time = datetime.now()
            expired_executions = [
                task_id for task_id, exec_time in self.task_execution_cache.items()
                if current_time - exec_time > timedelta(hours=1)
            ]
            
            for task_id in expired_executions:
                self.task_execution_cache.pop(task_id, None)
            
            # Cleanup failed tasks cache (mantieni solo ultimi)
            if len(self.failed_tasks_cache) > 100:
                # Mantieni solo gli ultimi 50
                sorted_items = sorted(self.failed_tasks_cache.items(), key=lambda x: x[1], reverse=True)
                self.failed_tasks_cache = dict(sorted_items[:50])
            
            logger.info(f"Cache cleanup completed for workspace {self.workspace_id}")
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}", exc_info=True)

    async def shutdown(self):
        """Shutdown graceful del manager"""
        try:
            logger.info(f"Shutting down AgentManager for workspace {self.workspace_id}")
            
            # Cleanup final delle cache
            await self.cleanup_caches()
            
            # Tentativo di health check finale per agenti
            for agent_id in self.agents.keys():
                try:
                    await update_agent_status(
                        str(agent_id),
                        None,
                        AgentHealth(
                            status=HealthStatus.UNKNOWN,
                            last_update=datetime.now(),
                            details={"manager_shutdown": True}
                        ).model_dump()
                    )
                except Exception as e:
                    logger.warning(f"Failed final health update for agent {agent_id}: {e}")
            
            # Clear references
            self.agents.clear()
            self.task_execution_cache.clear()
            self.failed_tasks_cache.clear()
            
            logger.info(f"AgentManager shutdown completed for workspace {self.workspace_id}")
        except Exception as e:
            logger.error(f"Error during manager shutdown: {e}", exc_info=True)