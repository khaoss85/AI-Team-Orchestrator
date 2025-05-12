from fastapi import APIRouter, Depends, HTTPException, status
from database import (
    save_team_proposal, 
    get_team_proposal, 
    approve_team_proposal,
    create_agent,
    create_handoff
)
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging
import json

from models import (
    DirectorConfig,
    DirectorTeamProposal
)
from ai_agents.director import DirectorAgent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/director", tags=["director"])

@router.post("/proposal", response_model=Dict[str, Any])
async def create_team_proposal(config: DirectorConfig):
    """
    Create a team proposal for a workspace based on goals and constraints
    """
    try:
        director = DirectorAgent()
        proposal = await director.create_team_proposal(config)
        
        # Salva la proposta nel database usando mode='json' per serializzare correttamente gli UUID
        saved_proposal = await save_team_proposal(
            workspace_id=str(proposal.workspace_id),
            proposal_data=proposal.model_dump(mode='json')  # Questo risolve il problema UUID
        )
        
        # Aggiungi l'ID della proposta alla risposta
        proposal_dict = proposal.model_dump(mode='json')  # Anche qui usa mode='json'
        proposal_dict["id"] = saved_proposal["id"]
        
        return proposal_dict
    except Exception as e:
        logger.error(f"Error creating team proposal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create team proposal: {str(e)}"
        )

@router.post("/approve/{workspace_id}", status_code=status.HTTP_200_OK)
async def approve_team_proposal_endpoint(workspace_id: UUID, proposal_id: UUID):
    """
    Approve a team proposal and create the agent team
    """
    try:
        # Retrieve and validate the proposal
        proposal_data = await get_team_proposal(str(proposal_id))
        if not proposal_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team proposal not found"
            )
        
        if proposal_data["workspace_id"] != str(workspace_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Proposal doesn't belong to this workspace"
            )
        
        # Mark as approved
        await approve_team_proposal(str(proposal_id))
        
        # Create actual agents from the proposal
        proposal = DirectorTeamProposal(**proposal_data["proposal_data"])
        
        # Create agents in the database
        created_agents = []
        agent_name_to_id = {}  # Mappa nome -> ID per risolvere gli handoffs
        
        for agent_create in proposal.agents:
            logger.info(f"Creating agent: {agent_create.name}")
            
            # Convertire tutti i dati in formato serializzabile
            agent_data = {
                "workspace_id": str(agent_create.workspace_id),
                "name": agent_create.name,
                "role": agent_create.role,
                "seniority": agent_create.seniority.value,
                "description": agent_create.description,
                "system_prompt": agent_create.system_prompt,
                "llm_config": agent_create.llm_config,
                "tools": agent_create.tools
            }
            
            created_agent = await create_agent(**agent_data)
            created_agents.append(created_agent)
            agent_name_to_id[agent_create.name] = created_agent['id']
            logger.info(f"Created agent {created_agent['id']}: {created_agent['name']}")
        
        # Create handoffs in the database
        logger.info(f"Creating {len(proposal.handoffs)} handoffs...")
        created_handoffs = []
        
        for handoff in proposal.handoffs:
            try:
                # Gli handoffs nel proposal usano source_agent_name e target_agent_name
                # dobbiamo convertirli in ID degli agenti creati
                source_agent_id = None
                target_agent_id = None
                
                # Cerca l'ID basato sul nome dell'agente
                if hasattr(handoff, 'source_agent_name'):
                    source_agent_id = agent_name_to_id.get(handoff.source_agent_name)
                if hasattr(handoff, 'target_agent_name'):  
                    target_agent_id = agent_name_to_id.get(handoff.target_agent_name)
                
                # Se non abbiamo nomi, prova con gli UUID (fallback)
                if not source_agent_id and hasattr(handoff, 'source_agent_id'):
                    source_agent_id = str(handoff.source_agent_id)
                if not target_agent_id and hasattr(handoff, 'target_agent_id'):
                    target_agent_id = str(handoff.target_agent_id)
                
                if source_agent_id and target_agent_id:
                    created_handoff = await create_handoff(
                        source_agent_id=source_agent_id,
                        target_agent_id=target_agent_id,
                        description=handoff.description
                    )
                    created_handoffs.append(created_handoff)
                    logger.info(f"Created handoff from {source_agent_id} to {target_agent_id}")
                else:
                    logger.warning(f"Could not resolve agent IDs for handoff: {handoff.description}")
            except Exception as e:
                logger.error(f"Error creating handoff: {e}")
        
        return {
            "status": "success",
            "message": "Team approved and created",
            "workspace_id": str(workspace_id),
            "proposal_id": str(proposal_id),
            "created_agents": [agent['id'] for agent in created_agents],
            "created_handoffs": [handoff['id'] for handoff in created_handoffs if handoff]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving team proposal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve team proposal: {str(e)}"
        )