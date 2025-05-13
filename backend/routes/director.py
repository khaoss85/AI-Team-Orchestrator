from fastapi import APIRouter, Depends, HTTPException, status
from database import (
    save_team_proposal, 
    get_team_proposal, 
    approve_team_proposal,
    create_agent,
    create_handoff
)
from typing import List, Dict, Any, Optional, Union 
from uuid import UUID
import logging
import json

from models import (
    DirectorConfig,
    DirectorTeamProposal,
    DirectorTeamProposalResponse, 
    AgentCreate, 
    HandoffProposalCreate 
)
from ai_agents.director import DirectorAgent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/director", tags=["director"])

@router.post("/proposal", response_model=DirectorTeamProposalResponse) 
async def create_team_proposal(config: DirectorConfig):
    """
    Create a team proposal for a workspace based on goals and constraints
    """
    try:
        director = DirectorAgent()
        proposal = await director.create_team_proposal(config)
        
        # Salva la proposta nel database
        # proposal.model_dump(mode='json', by_alias=True) per assicurare che gli alias "from"/"to" siano usati
        # se il modello HandoffProposalCreate li definisce per la serializzazione.
        # Tuttavia, HandoffProposalCreate usa alias per la *deserializzazione*.
        # Per il salvataggio in DB, i nomi dei campi sono generalmente preferiti.
        # Se il DB si aspetta 'source_agent_name', model_dump() senza by_alias è corretto.
        # La cosa importante è che la logica che *legge* dal DB e popola i modelli Pydantic
        # sia consapevole di come i dati sono strutturati nel DB.
        
        # Per coerenza e per evitare problemi con Supabase che potrebbe non gradire chiavi come "from",
        # usiamo i nomi dei campi per salvare nel DB.
        proposal_data_for_db = proposal.model_dump(mode='json')


        saved_proposal_db = await save_team_proposal(
            workspace_id=str(proposal.workspace_id),
            proposal_data=proposal_data_for_db
        )
        
        # Costruisci la risposta. Qui `proposal.model_dump(mode='json', by_alias=True)`
        # assicura che l'output JSON della API usi "from" e "to" se così definito negli alias
        # di HandoffProposalCreate per la serializzazione.
        # Dato che DirectorTeamProposalResponse usa HandoffProposalCreate,
        # e HandoffProposalCreate definisce alias "from" e "to" per la *deserializzazione*,
        # quando Pydantic costruisce DirectorTeamProposalResponse da un dict, si aspetterà
        # le chiavi "from" e "to" se `populate_by_name=False` (default) o se l'input dict
        # ha effettivamente quelle chiavi.
        
        # Per costruire `response_data` che sarà usato per istanziare `DirectorTeamProposalResponse`,
        # dobbiamo assicurarci che i nomi dei campi per gli handoff siano quelli attesi da `HandoffProposalCreate`
        # (cioè, "from" e "to" a causa degli alias).
        response_data_dict = proposal.model_dump(mode='json', by_alias=True)
        response_data_dict["id"] = saved_proposal_db["id"] 
        response_data_dict["created_at"] = saved_proposal_db.get("created_at")
        response_data_dict["status"] = saved_proposal_db.get("status", "pending")
        
        return DirectorTeamProposalResponse(**response_data_dict)
    except Exception as e:
        logger.error(f"Error creating team proposal: {e}", exc_info=True)
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
        proposal_db_data = await get_team_proposal(str(proposal_id))
        if not proposal_db_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team proposal not found"
            )
        
        if proposal_db_data["workspace_id"] != str(workspace_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Proposal doesn't belong to this workspace"
            )
        
        try:
            # proposal_db_data["proposal_data"] contiene i dati della proposta come dict.
            # HandoffProposalCreate si aspetta 'from' e 'to' a causa degli alias.
            # Assicuriamoci che proposal_data_raw abbia 'from' e 'to'.
            # Se save_team_proposal ha salvato con `model_dump(by_alias=True)`, allora è corretto.
            # Se ha salvato con nomi di campo, dobbiamo trasformare qui o usare `populate_by_name=True`
            # nel modello HandoffProposalCreate (già aggiunto).
            proposal_data_raw = proposal_db_data["proposal_data"]
            proposal = DirectorTeamProposal(**proposal_data_raw)

        except Exception as pydantic_error:
            logger.error(f"Error parsing proposal_data from DB: {pydantic_error}. Data: {proposal_db_data['proposal_data']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error parsing stored team proposal: {str(pydantic_error)}"
            )

        await approve_team_proposal(str(proposal_id))
        
        created_agents_db = []
        agent_name_to_id_map: Dict[str, str] = {} 
        
        for agent_create_data in proposal.agents:
            logger.info(f"Creating agent: {agent_create_data.name}")
            logger.info(f"Tools configuration: {agent_create_data.tools}") 

            tools_for_db = [t for t in (agent_create_data.tools or []) if isinstance(t, dict)]
            
            agent_payload_for_db = agent_create_data.model_dump()
            agent_payload_for_db["workspace_id"] = str(workspace_id) 
            agent_payload_for_db["seniority"] = agent_create_data.seniority.value
            agent_payload_for_db["tools"] = tools_for_db 

            valid_agent_keys = ["workspace_id", "name", "role", "seniority", "description", "system_prompt", "llm_config", "tools", "can_create_tools"]
            agent_data_for_creation = {k: v for k, v in agent_payload_for_db.items() if k in valid_agent_keys}

            created_agent_db = await create_agent(**agent_data_for_creation)
            if created_agent_db:
                created_agents_db.append(created_agent_db)
                agent_name_to_id_map[created_agent_db['name']] = str(created_agent_db['id']) # Assicura che l'ID sia una stringa
                logger.info(f"Created agent {created_agent_db['id']}: {created_agent_db['name']}")
            else:
                logger.error(f"Failed to create agent in DB: {agent_create_data.name}")
        
        logger.info(f"Processing {len(proposal.handoffs)} handoff proposals for actual creation...")
        created_handoffs_db = []
        
        for handoff_proposal in proposal.handoffs: 
            # Accedi tramite i nomi dei campi definiti in HandoffProposalCreate
            source_agent_name = handoff_proposal.source_agent_name 
            target_agent_names_prop = handoff_proposal.target_agent_names
            
            source_agent_id_str = agent_name_to_id_map.get(source_agent_name)
            
            if not source_agent_id_str:
                logger.warning(f"Could not find source agent ID for name: '{source_agent_name}' in handoff: {handoff_proposal.description}. Skipping handoff.")
                continue

            targets_to_process_names = []
            if isinstance(target_agent_names_prop, str):
                targets_to_process_names.append(target_agent_names_prop)
            elif isinstance(target_agent_names_prop, list):
                targets_to_process_names.extend(target_agent_names_prop)

            for target_agent_name in targets_to_process_names:
                target_agent_id_str = agent_name_to_id_map.get(target_agent_name)
                
                if not target_agent_id_str:
                    logger.warning(f"Could not find target agent ID for name: '{target_agent_name}' in handoff: {handoff_proposal.description}. Skipping this target.")
                    continue
                
                try:
                    logger.info(f"Attempting to create handoff from {source_agent_name} ({source_agent_id_str}) to {target_agent_name} ({target_agent_id_str})")
                    created_handoff_db = await create_handoff(
                        source_agent_id=UUID(source_agent_id_str), # Converti in UUID per la funzione create_handoff
                        target_agent_id=UUID(target_agent_id_str), # Converti in UUID
                        description=handoff_proposal.description
                    )
                    if created_handoff_db:
                        created_handoffs_db.append(created_handoff_db)
                        logger.info(f"Successfully created handoff from {source_agent_name} to {target_agent_name}")
                    else:
                        logger.error(f"DB call to create_handoff returned None for handoff from {source_agent_name} to {target_agent_name}")
                except Exception as e_handoff:
                    logger.error(f"Error during DB creation of handoff from {source_agent_name} to {target_agent_name}: {e_handoff}", exc_info=True)
        
        return {
            "status": "success",
            "message": "Team approved and agents created. Handoffs processed.",
            "workspace_id": str(workspace_id),
            "proposal_id": str(proposal_id),
            "created_agent_ids": [str(agent['id']) for agent in created_agents_db], # Assicura stringhe
            "created_handoff_ids": [str(handoff['id']) for handoff in created_handoffs_db if handoff and 'id' in handoff] # Assicura stringhe e che id esista
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving team proposal: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve team proposal: {str(e)}"
        )