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
import os

from models import (
    DirectorConfig,
    DirectorTeamProposal,
    DirectorTeamProposalResponse, 
    AgentCreate, 
    HandoffProposalCreate 
)
from ai_agents.director import DirectorAgent
from ai_agents.director_enhanced import EnhancedDirectorAgent
from database import supabase

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/director", tags=["director"])

@router.post("/proposal", response_model=DirectorTeamProposalResponse) 
async def create_team_proposal(config: DirectorConfig):
    """
    Create a team proposal for a workspace based on goals and constraints
    Enhanced to use strategic goals when available
    """
    try:
        # Check if enhanced director is enabled and workspace has strategic goals
        use_enhanced_director = os.getenv("ENABLE_ENHANCED_DIRECTOR", "true").lower() == "true"
        strategic_goals = await _get_strategic_goals(str(config.workspace_id)) if use_enhanced_director else None
        
        # Check if we have extracted_goals from frontend (user-confirmed goals)
        frontend_goals = getattr(config, 'extracted_goals', None)
        
        if use_enhanced_director and (strategic_goals or frontend_goals):
            logger.info(f"🎯 Using enhanced director for workspace {config.workspace_id}")
            
            # If we have frontend goals (user-confirmed), prioritize them over database goals
            goals_to_use = strategic_goals
            if frontend_goals:
                logger.info(f"✅ Using {len(frontend_goals)} user-confirmed goals from frontend")
                logger.info(f"Frontend goals sample: {[g.get('description', g.get('type', 'Unknown'))[:50] for g in frontend_goals[:2]]}")
                goals_to_use = await _convert_frontend_goals_to_strategic_format(frontend_goals)
                logger.info(f"Converted to: {goals_to_use.get('total_deliverables', 0)} deliverables, {goals_to_use.get('total_metrics', 0)} metrics")
            elif strategic_goals:
                logger.info(f"📊 Using {len(strategic_goals.get('strategic_deliverables', []))} strategic goals from database")
            
            director = EnhancedDirectorAgent()
            proposal = await director.create_proposal_with_goals(config, goals_to_use)
        else:
            reason = "enhanced director disabled" if not use_enhanced_director else "no strategic goals available"
            logger.info(f"Using standard director for workspace {config.workspace_id} ({reason})")
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

            #valid_agent_keys = ["workspace_id", "name", "role", "seniority", "description", "system_prompt", "llm_config", "tools", "can_create_tools"]
            valid_agent_keys = list(AgentCreate.__annotations__.keys())
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
        
        # 🚀 ACTIVATE WORKSPACE: Update workspace status to active before processing handoffs
        from database import update_workspace_status
        await update_workspace_status(str(workspace_id), "active")
        logger.info(f"✅ Workspace {workspace_id} activated successfully")
        
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
        
        # 🚀 AUTO-START: When team is approved, check if goals exist and trigger task generation
        # This mirrors the behavior in routes/proposals.py to ensure consistency
        logger.info(f"🎯 Team approved for workspace {workspace_id}, checking for goals...")
        
        auto_start_message = "Team approved and agents created. Handoffs processed."
        try:
            # Check if workspace has confirmed goals
            goals_response = supabase.table("workspace_goals").select("id").eq(
                "workspace_id", str(workspace_id)
            ).eq("status", "active").execute()
            
            if goals_response.data and len(goals_response.data) > 0:
                logger.info(f"✅ Found {len(goals_response.data)} active goals, triggering auto-start")
                
                from automated_goal_monitor import automated_goal_monitor
                import asyncio
                
                # Trigger immediate goal analysis and task creation
                asyncio.create_task(automated_goal_monitor._trigger_immediate_goal_analysis(str(workspace_id)))
                
                auto_start_message = f"Team approved and auto-start triggered for {len(goals_response.data)} goals!"
                logger.info("✅ Auto-start triggered after team approval via director endpoint")
            else:
                logger.warning(f"⚠️ No active goals found for workspace {workspace_id}")
                auto_start_message = "Team approved. Please confirm goals to start task execution."
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to trigger auto-start after team approval: {e}")
            # Don't fail the approval, just log the warning
            auto_start_message = "Team approved (auto-start check failed, see logs)"

        return {
            "status": "success",
            "message": auto_start_message,
            "workspace_id": str(workspace_id),
            "proposal_id": str(proposal_id),
            "created_agent_ids": [str(agent['id']) for agent in created_agents_db], # Assicura stringhe
            "created_handoff_ids": [str(handoff['id']) for handoff in created_handoffs_db if handoff and 'id' in handoff], # Assicura stringhe e che id esista
            "auto_start_triggered": len(goals_response.data) > 0 if 'goals_response' in locals() else False
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving team proposal: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve team proposal: {str(e)}"
        )

async def _convert_frontend_goals_to_strategic_format(frontend_goals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convert frontend extracted_goals to strategic goals format"""
    try:
        final_metrics = []
        strategic_deliverables = []
        
        for goal in frontend_goals:
            goal_data = {
                "metric_type": goal.get("type", ""),
                "target_value": goal.get("value", 0),
                "unit": goal.get("unit", ""),
                "description": goal.get("description", ""),
                "priority": 1,  # Default priority for frontend goals
                "confidence": goal.get("confidence", 0.9)
            }
            
            # Check if this is a strategic deliverable
            if goal.get("deliverable_type") or goal.get("semantic_context", {}).get("is_strategic_deliverable"):
                deliverable_data = {
                    "name": goal.get("description", ""),
                    "deliverable_type": goal.get("deliverable_type", goal.get("type", "")),
                    "business_value": goal.get("business_value", ""),
                    "acceptance_criteria": goal.get("acceptance_criteria", []),
                    "execution_phase": goal.get("execution_phase", "Implementation"),
                    "autonomy_level": goal.get("autonomy_level", "autonomous"),
                    "autonomy_reason": goal.get("autonomy_reason", ""),
                    "available_tools": goal.get("available_tools", []),
                    "human_input_required": goal.get("human_input_required", []),
                    "priority": 1,
                    "target_value": goal.get("value", 1),
                    "unit": goal.get("unit", "deliverable")
                }
                strategic_deliverables.append(deliverable_data)
            else:
                final_metrics.append(goal_data)
        
        # Extract execution phases
        execution_phases = list(set([
            d.get("execution_phase", "Implementation") 
            for d in strategic_deliverables 
            if d.get("execution_phase")
        ]))
        
        if not execution_phases:
            execution_phases = ["Implementation"]
        
        return {
            "final_metrics": final_metrics,
            "strategic_deliverables": strategic_deliverables,
            "execution_phases": execution_phases,
            "total_deliverables": len(strategic_deliverables),
            "total_metrics": len(final_metrics),
            "source": "frontend_confirmed"  # Marker to indicate source
        }
        
    except Exception as e:
        logger.error(f"Error converting frontend goals to strategic format: {e}")
        return {
            "final_metrics": [],
            "strategic_deliverables": [],
            "execution_phases": ["Implementation"],
            "total_deliverables": 0,
            "total_metrics": 0,
            "source": "frontend_error"
        }

async def _get_strategic_goals(workspace_id: str) -> Optional[Dict[str, Any]]:
    """Get strategic goals and deliverables for workspace"""
    try:
        # Get workspace goals with semantic context
        goals_response = supabase.table("workspace_goals").select("*").eq(
            "workspace_id", workspace_id
        ).execute()
        
        if not goals_response.data:
            return None
        
        goals = goals_response.data
        
        # Separate final metrics from strategic deliverables
        final_metrics = []
        strategic_deliverables = []
        
        for goal in goals:
            metadata = goal.get("metadata", {})
            if metadata.get("semantic_context", {}).get("is_strategic_deliverable"):
                # This is a strategic deliverable
                semantic_context = metadata.get("semantic_context", {})
                strategic_deliverables.append({
                    "name": goal.get("description", ""),
                    "deliverable_type": semantic_context.get("deliverable_type", ""),
                    "business_value": semantic_context.get("business_value", ""),
                    "acceptance_criteria": semantic_context.get("acceptance_criteria", []),
                    "execution_phase": semantic_context.get("execution_phase", ""),
                    "autonomy_level": semantic_context.get("autonomy_level", "autonomous"),
                    "autonomy_reason": semantic_context.get("autonomy_reason", ""),
                    "available_tools": semantic_context.get("available_tools", []),
                    "human_input_required": semantic_context.get("human_input_required", []),
                    "priority": goal.get("priority", 1),
                    "target_value": goal.get("target_value", 1),
                    "unit": goal.get("unit", "deliverable")
                })
            else:
                # This is a final metric
                final_metrics.append({
                    "metric_type": goal.get("metric_type", ""),
                    "target_value": goal.get("target_value", 0),
                    "unit": goal.get("unit", ""),
                    "description": goal.get("description", ""),
                    "priority": goal.get("priority", 1)
                })
        
        if not strategic_deliverables and not final_metrics:
            return None
        
        # Extract execution phases from deliverables
        execution_phases = list(set([
            d.get("execution_phase", "Implementation") 
            for d in strategic_deliverables 
            if d.get("execution_phase")
        ]))
        
        return {
            "final_metrics": final_metrics,
            "strategic_deliverables": strategic_deliverables,
            "execution_phases": execution_phases,
            "total_deliverables": len(strategic_deliverables),
            "total_metrics": len(final_metrics)
        }
        
    except Exception as e:
        logger.error(f"Error getting strategic goals for workspace {workspace_id}: {e}")
        return None