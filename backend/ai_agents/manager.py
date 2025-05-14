# backend/ai_agents/manager.py
import logging
import os
from typing import List, Dict, Any
from uuid import UUID

from database import (
    list_agents  as db_list_agents_from_db,
    list_tasks   as db_list_tasks_from_db,
    get_workspace,
    update_task_status
)
from models import (
    Agent       as AgentModelPydantic,
    Task,
    TaskStatus
)
from ai_agents.specialist import SpecialistAgent

logger = logging.getLogger(__name__)

class AgentManager:
    def __init__(self, workspace_id: UUID):
        self.workspace_id = workspace_id
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY not set")
        self.agents: Dict[UUID, SpecialistAgent] = {}

    async def initialize(self) -> bool:
        """
        Carica il workspace e inizializza tutti i SpecialistAgent.
        Ritorna True se il manager è pronto (anche se non ci sono agenti),
        False solo se fallisce il recupero del workspace.
        """
        try:
            workspace = await get_workspace(str(self.workspace_id))
            if not workspace:
                logger.error(f"Workspace {self.workspace_id} non trovato. Impossibile inizializzare.")
                return False

            logger.info(f"Initializing AgentManager for workspace {self.workspace_id} "
                        f"(name={workspace.get('name','N/A')})")
            raw_agents = await db_list_agents_from_db(str(self.workspace_id))
            if not raw_agents:
                logger.info(f"Nessun agente per workspace {self.workspace_id}. Manager pronto comunque.")
                return True

            # Validazione Pydantic
            valid_agents: List[AgentModelPydantic] = []
            for data in raw_agents:
                try:
                    valid_agents.append(AgentModelPydantic.model_validate(data))
                except Exception as e:
                    logger.error(
                        f"Validazione fallita per agent ID {data.get('id','?')}: {e}",
                        exc_info=True
                    )

            if not valid_agents:
                logger.warning(f"Nessun dato agente valido dopo validazione per workspace {self.workspace_id}.")
                return True

            # Creazione SpecialistAgent
            count = 0
            for agent_model in valid_agents:
                try:
                    inst = SpecialistAgent(
                        agent_data=agent_model,
                        all_workspace_agents_data=valid_agents
                    )
                    self.agents[agent_model.id] = inst
                    logger.info(f"Creato SpecialistAgent per {agent_model.name} (ID: {agent_model.id})")
                    count += 1
                except Exception as e:
                    logger.error(
                        f"Errore creazione SpecialistAgent {agent_model.id}: {e}",
                        exc_info=True
                    )

            logger.info(f"Inizializzati {count}/{len(valid_agents)} SpecialistAgent.")
            return True

        except Exception as e:
            logger.error(
                f"Errore critico inizializzazione AgentManager per workspace {self.workspace_id}: {e}",
                exc_info=True
            )
            return False

    async def verify_all_agents(self) -> Dict[UUID, bool]:
        """
        Esegue verify_capabilities() su tutti gli agenti caricati.
        Ritorna un dict {agent_id: esito_bool}.
        """
        results: Dict[UUID, bool] = {}
        if not self.agents:
            logger.warning(f"Nessun agente da verificare in manager per workspace {self.workspace_id}.")
            return results

        for aid, spec in self.agents.items():
            logger.info(f"Verifica capacità agente {spec.agent_data.name} (ID: {aid})")
            try:
                results[aid] = await spec.verify_capabilities()
            except Exception as e:
                logger.error(f"Errore verifica agente {aid}: {e}", exc_info=True)
                results[aid] = False

        return results

    async def execute_task(self, task_id: UUID) -> Dict[str, Any]:
        """
        Recupera il Task dal DB e lo invia all'agente assegnato.
        Lancia ValueError se task o agent_id mancano, aggiornando lo stato su DB.
        """
        all_tasks = await db_list_tasks_from_db(str(self.workspace_id))
        record = next((t for t in all_tasks if UUID(t["id"]) == task_id), None)
        if not record:
            msg = f"Task {task_id} non trovato in workspace {self.workspace_id}"
            logger.error(msg)
            raise ValueError(msg)

        task = Task.model_validate(record)
        if not task.agent_id:
            msg = f"Task {task_id} privo di agent_id"
            logger.error(msg)
            await update_task_status(str(task_id), TaskStatus.FAILED.value,
                                     {"error": msg, "detail": "missing_agent_id"})
            raise ValueError(msg)

        agent_uuid = UUID(str(task.agent_id))
        specialist = self.agents.get(agent_uuid)
        if not specialist:
            msg = f"Agent {agent_uuid} non inizializzato nel manager per task {task_id}"
            logger.error(msg + f"  Agenti disponibili: {list(self.agents.keys())}")
            await update_task_status(str(task_id), TaskStatus.FAILED.value,
                                     {"error": msg, "detail": "agent_not_found"})
            raise ValueError(msg)

        logger.info(f"Dispatching task {task_id} -> agent {specialist.agent_data.name}")
        return await specialist.execute_task(task)
