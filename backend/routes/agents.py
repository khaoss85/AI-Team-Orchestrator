from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging
import json

from models import (
    AgentCreate,
    AgentUpdate,
    Agent,
    TaskCreate,
    Task,
    Handoff
)
from database import (
    create_agent,
    update_agent,
    list_agents as db_list_agents,
    update_agent_status,
    create_task,
    update_task_status,
    list_handoffs as db_list_handoffs
)
from ai_agents.manager import AgentManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agents", tags=["agents"])

@router.post("/{workspace_id}", response_model=Agent, status_code=status.HTTP_201_CREATED)
async def create_new_agent(workspace_id: UUID, agent: AgentCreate):
    """Create a new agent in a workspace"""
    try:
        # Ensure the agent's workspace_id matches the path parameter
        if agent.workspace_id != workspace_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent workspace_id does not match URL workspace_id"
            )
            
        agent_data = await create_agent(
            workspace_id=str(agent.workspace_id),
            name=agent.name,
            role=agent.role,
            seniority=agent.seniority.value,
            description=agent.description
        )
        
        return Agent.model_validate(agent_data)
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create agent: {str(e)}"
        )

@router.get("/{workspace_id}", response_model=List[Agent])
async def get_workspace_agents(workspace_id: UUID):
    """Get all agents in a workspace"""
    try:
        agents_data = await db_list_agents(str(workspace_id))
        
        # Deserializza i campi JSON prima della validazione Pydantic
        for agent in agents_data:
            # Deserializza llm_config se è una stringa
            if isinstance(agent.get('llm_config'), str):
                try:
                    agent['llm_config'] = json.loads(agent['llm_config'])
                except (json.JSONDecodeError, TypeError):
                    agent['llm_config'] = None
            
            # Deserializza tools se è una stringa
            if isinstance(agent.get('tools'), str):
                try:
                    agent['tools'] = json.loads(agent['tools'])
                except (json.JSONDecodeError, TypeError):
                    agent['tools'] = []
            
            # Deserializza health se è una stringa
            if isinstance(agent.get('health'), str):
                try:
                    agent['health'] = json.loads(agent['health'])
                except (json.JSONDecodeError, TypeError):
                    agent['health'] = {"status": "unknown", "last_update": None}
        
        return [Agent.model_validate(agent) for agent in agents_data]
    except Exception as e:
        logger.error(f"Error getting agents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agents: {str(e)}"
        )

@router.get("/{workspace_id}/handoffs", response_model=List[Handoff], tags=["agents", "handoffs"])
async def get_workspace_handoffs(workspace_id: UUID):
    """Get all handoffs for a workspace"""
    try:
        handoffs_data = await db_list_handoffs(str(workspace_id))
        # Il modello Handoff dovrebbe gestire la validazione se i dati dal DB sono corretti
        return handoffs_data # Pydantic convertirà automaticamente i dict in istanze di Handoff
    except Exception as e:
        logger.error(f"Error getting handoffs for workspace {workspace_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get handoffs: {str(e)}"
        )

        
@router.put("/{workspace_id}/{agent_id}", response_model=Agent)
async def update_agent_data(workspace_id: UUID, agent_id: UUID, agent_update: AgentUpdate):
    """Update an agent's configuration"""
    try:
        # Verifica che l'agente esista e appartenga al workspace
        agents = await db_list_agents(str(workspace_id))  # Use the alias here
        agent = next((a for a in agents if a["id"] == str(agent_id)), None)
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        # Prepara i dati per l'update (solo i campi forniti)
        update_data = {}
        for field, value in agent_update.model_dump(exclude_unset=True).items():
            if value is not None:
                if field == "seniority" and hasattr(value, "value"):
                    update_data[field] = value.value
                elif field in ["personality_traits", "hard_skills", "soft_skills"] and isinstance(value, list):
                    # Properly handle list fields that might contain enum values
                    if field == "personality_traits":
                        update_data[field] = [trait.value if hasattr(trait, "value") else trait for trait in value]
                    else:
                        # For skills, which are objects with potential enum values
                        processed_skills = []
                        for skill in value:
                            if isinstance(skill, dict) and "level" in skill and hasattr(skill["level"], "value"):
                                skill["level"] = skill["level"].value
                            processed_skills.append(skill)
                        update_data[field] = processed_skills
                else:
                    update_data[field] = value
        
        # Aggiorna l'agente
        updated_agent = await update_agent(str(agent_id), update_data)
        
        if not updated_agent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update agent"
            )
        
        return Agent.model_validate(updated_agent)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent: {e}", exc_info=True)  # Added exc_info=True for better error logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update agent: {str(e)}"
        )

@router.post("/{workspace_id}/verify", status_code=status.HTTP_200_OK)
async def verify_agents(workspace_id: UUID):
    """Verify all agents in a workspace have required capabilities"""
    try:
        manager = AgentManager(workspace_id)
        await manager.initialize()
        results = await manager.verify_all_agents()
        
        return {
            "workspace_id": workspace_id,
            "results": results,
            "status": "success" if all(results.values()) else "partial"
        }
    except Exception as e:
        logger.error(f"Error verifying agents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify agents: {str(e)}"
        )

@router.post("/{workspace_id}/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_new_task(workspace_id: UUID, task: TaskCreate):
    """Create a new task for an agent"""
    try:
        # Ensure the task's workspace_id matches the path parameter
        if task.workspace_id != workspace_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task workspace_id does not match URL workspace_id"
            )
            
        task_data = await create_task(
            workspace_id=str(task.workspace_id),
            agent_id=str(task.agent_id),
            name=task.name,
            description=task.description,
            status=task.status.value,

            # TRACKING AUTOMATICO
            creation_type="manual_api",  # Creato via API manuale

            # CONTEXT DATA
            context_data={
                "created_via": "agents_api_endpoint",
                "api_timestamp": datetime.now().isoformat()
            }
        )
        
        return Task.model_validate(task_data)
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}"
        )

@router.post("/{workspace_id}/execute/{task_id}", status_code=status.HTTP_200_OK)
async def execute_task(workspace_id: UUID, task_id: UUID):
    """Execute a specific task"""
    try:
        manager = AgentManager(workspace_id)
        await manager.initialize()
        result = await manager.execute_task(task_id)
        
        return {
            "workspace_id": workspace_id,
            "task_id": task_id,
            "result": result
        }
    except Exception as e:
        logger.error(f"Error executing task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute task: {str(e)}"
        )