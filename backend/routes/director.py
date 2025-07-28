from fastapi import Request
from middleware.trace_middleware import get_trace_id, create_traced_logger, TracedDatabaseOperation
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

# Compatibility endpoints for E2E tests
@router.post("/generate-team-proposal")
async def generate_team_proposal(proposal_request: DirectorTeamProposal, request: Request):
    """Generate team proposal - compatibility endpoint"""
    return await create_team_proposal(proposal_request, request)

@router.post("/approve-team-proposal")
async def approve_team_proposal_compat(data: Dict[str, Any], request: Request):
    """Approve team proposal - compatibility endpoint"""
    proposal_id = data.get("proposal_id")
    if not proposal_id:
        raise HTTPException(status_code=400, detail="proposal_id required")
    
    # Import the approve function from proposals route
    from routes.proposals import approve_proposal
    return await approve_proposal(UUID(proposal_id), request)

@router.post("/proposal", response_model=DirectorTeamProposalResponse) 
async def create_team_proposal(proposal_request: DirectorTeamProposal, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route create_team_proposal called", endpoint="create_team_proposal", trace_id=trace_id)
    
    """
    Create a team proposal for a workspace based on goals and constraints
    Enhanced to use strategic goals when available
    """
    try:
        # Check if enhanced director is enabled and workspace has strategic goals
        use_enhanced_director = os.getenv("ENABLE_ENHANCED_DIRECTOR", "true").lower() == "true"
        strategic_goals = await _get_strategic_goals(str(proposal_request.workspace_id)) if use_enhanced_director else None
        
        # Check if we have extracted_goals from frontend (user-confirmed goals)
        frontend_goals = getattr(proposal_request, 'extracted_goals', None)
        
        if use_enhanced_director and (strategic_goals or frontend_goals):
            logger.info(f"🎯 Using enhanced director for workspace {proposal_request.workspace_id}")
            
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
            proposal = await director.create_proposal_with_goals(proposal_request, goals_to_use)
        else:
            reason = "enhanced director disabled" if not use_enhanced_director else "no strategic goals available"
            logger.info(f"Using standard director for workspace {proposal_request.workspace_id} ({reason})")
            director = DirectorAgent()
            proposal = await director.create_team_proposal(proposal_request)
        
        # Salva la proposta nel database
        proposal_data_for_db = proposal.model_dump(mode='json')

        saved_proposal_db = await save_team_proposal(
            workspace_id=str(proposal.workspace_id),
            proposal_data=proposal_data_for_db
        )
        
        # Map DirectorTeamProposal to DirectorTeamProposalResponse with correct fields
        team_members = []
        for agent in proposal.agents:
            team_members.append({
                "name": agent.name,
                "role": agent.role,
                "seniority": agent.seniority.value if hasattr(agent.seniority, 'value') else str(agent.seniority),
                "description": getattr(agent, 'description', ''),
                "tools": getattr(agent, 'tools', [])
            })
        
        # Extract estimated cost value
        estimated_cost = 0.0
        if hasattr(proposal, 'estimated_cost') and proposal.estimated_cost:
            if isinstance(proposal.estimated_cost, dict):
                estimated_cost = proposal.estimated_cost.get('total_estimated_cost', 0.0)
            else:
                estimated_cost = float(proposal.estimated_cost)
        
        if not saved_proposal_db or "id" not in saved_proposal_db:
            raise HTTPException(status_code=500, detail="Failed to save team proposal and retrieve its ID.")

        return DirectorTeamProposalResponse(
            proposal_id=saved_proposal_db["id"],
            team_members=team_members,
            estimated_cost=estimated_cost,
            timeline="30 days"  # Default timeline
        )
    except Exception as e:
        logger.error(f"Error creating team proposal: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create team proposal: {str(e)}"
        )

async def _process_team_creation_background(
    workspace_id: UUID, 
    proposal_id: UUID, 
    proposal: DirectorTeamProposal, 
    logger
):
    """
    Background task that handles the heavy lifting of team creation:
    - Create agents
    - Process handoffs  
    - Activate workspace
    - Trigger goal analysis and task generation
    """
    try:
        logger.info(f"🔄 BACKGROUND: Starting team creation for workspace {workspace_id}")
        
        created_agents_db = []
        agent_name_to_id_map: Dict[str, str] = {} 
        
        # Create agents
        for i, agent_create_data in enumerate(proposal.agents):
            logger.info(f"📋 Creating agent {i+1}/{len(proposal.agents)}: {agent_create_data.name}")

            # Build agent creation payload using model_dump for proper serialization
            agent_data_for_creation = agent_create_data.model_dump(mode='json')
            
            # Ensure workspace_id is a string
            agent_data_for_creation["workspace_id"] = str(workspace_id)

            # Ensure seniority is the string value
            if hasattr(agent_create_data.seniority, 'value'):
                agent_data_for_creation["seniority"] = agent_create_data.seniority.value
            
            # CRITICAL FIX: Remove 'status' before calling create_agent
            agent_data_for_creation.pop('status', None)

            # Create agent in database - expand dict as keyword arguments
            created_agent_db = await create_agent(**agent_data_for_creation)
            if created_agent_db:
                created_agents_db.append(created_agent_db)
                agent_name_to_id_map[agent_create_data.name] = str(created_agent_db['id'])
                logger.info(f"✅ Agent created: {agent_create_data.name} -> {created_agent_db['id']}")
            else:
                logger.error(f"❌ Failed to create agent: {agent_create_data.name}")

        # Refresh AgentManager cache
        if created_agents_db:
            try:
                from executor import task_executor
                refresh_success = await task_executor.refresh_agent_manager_cache(str(workspace_id))
                logger.info(f"✅ AgentManager cache refreshed: {refresh_success}")
            except Exception as e:
                logger.error(f"❌ Failed to refresh AgentManager cache: {e}")

        # Activate workspace
        from database import update_workspace_status
        await update_workspace_status(str(workspace_id), "active")
        logger.info(f"✅ Workspace {workspace_id} activated")

        # Process handoffs
        created_handoffs_db = []
        for handoff_proposal in proposal.handoffs: 
            source_agent_name = handoff_proposal.from_agent
            target_agent_names_prop = handoff_proposal.to_agents
            source_agent_id_str = agent_name_to_id_map.get(source_agent_name)
            
            if not source_agent_id_str:
                logger.error(f"❌ Source agent {source_agent_name} not found in created agents")
                continue

            for target_agent_name in target_agent_names_prop:
                target_agent_id_str = agent_name_to_id_map.get(target_agent_name)
                if not target_agent_id_str:
                    logger.error(f"❌ Target agent {target_agent_name} not found in created agents")
                    continue

                try:
                    handoff_data = {
                        "source_agent_id": source_agent_id_str,
                        "target_agent_id": target_agent_id_str,
                        "description": handoff_proposal.description or f"Handoff from {source_agent_name} to {target_agent_name}",
                        "workspace_id": str(workspace_id)
                    }
                    created_handoff_db = await create_handoff(
                        source_agent_id=UUID(handoff_data["source_agent_id"]),
                        target_agent_id=UUID(handoff_data["target_agent_id"]),
                        description=handoff_data["description"]
                    )
                    if created_handoff_db:
                        created_handoffs_db.append(created_handoff_db)
                        logger.info(f"✅ Handoff created: {source_agent_name} -> {target_agent_name}")
                except Exception as e_handoff:
                    logger.error(f"❌ Error creating handoff from {source_agent_name} to {target_agent_name}: {e_handoff}")

        # Trigger goal analysis and task generation
        try:
            goals_response = supabase.table("workspace_goals").select("id").eq(
                "workspace_id", str(workspace_id)
            ).eq("status", "active").execute()
            
            if goals_response.data and len(goals_response.data) > 0:
                logger.info(f"✅ Found {len(goals_response.data)} active goals, triggering auto-start")
                from automated_goal_monitor import automated_goal_monitor
                await automated_goal_monitor._trigger_immediate_goal_analysis(str(workspace_id))
                logger.info("✅ Auto-start triggered successfully")
            else:
                # Auto-extract goals from workspace.goal
                logger.info(f"🎯 No active goals found, attempting auto-extraction...")
                from database import get_workspace, _auto_create_workspace_goals
                
                workspace = await get_workspace(str(workspace_id))
                if workspace and workspace.get("goal"):
                    created_goals = await _auto_create_workspace_goals(str(workspace_id), workspace["goal"])
                    if created_goals and len(created_goals) > 0:
                        logger.info(f"✅ Auto-extracted {len(created_goals)} goals")
                        from automated_goal_monitor import automated_goal_monitor
                        await automated_goal_monitor._trigger_immediate_goal_analysis(str(workspace_id))
                        logger.info("✅ Goal extraction and auto-start completed")
                    else:
                        await _create_fallback_planning_task(workspace_id, created_agents_db)
                        logger.info("⚠️ Created fallback planning task")
                else:
                    await _create_fallback_planning_task(workspace_id, created_agents_db)
                    logger.info("⚠️ Created fallback planning task (no goal text)")
                        
        except Exception as e:
            logger.error(f"❌ Failed to trigger auto-start: {e}")
            # Don't fail the whole process, just log the error

        logger.info(f"✅ BACKGROUND: Team creation completed for workspace {workspace_id}")
        logger.info(f"📊 Created: {len(created_agents_db)} agents, {len(created_handoffs_db)} handoffs")
        
    except Exception as e:
        logger.error(f"��� BACKGROUND: Team creation failed for workspace {workspace_id}: {e}", exc_info=True)


@router.post("/approve/{workspace_id}", status_code=status.HTTP_200_OK)
async def approve_team_proposal_endpoint(workspace_id: UUID, proposal_id: UUID, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route approve_team_proposal_endpoint called", endpoint="approve_team_proposal_endpoint", trace_id=trace_id)
    
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
        
        # 🚀 IMMEDIATE RESPONSE: Return immediately and process team creation in background
        logger.info(f"🚀 PROPOSAL APPROVAL: Starting background team creation for {len(proposal.agents)} agents")
        
        # Start background task for team creation
        import asyncio
        asyncio.create_task(_process_team_creation_background(
            workspace_id=workspace_id,
            proposal_id=proposal_id, 
            proposal=proposal,
            logger=logger
        ))
        
        # Return immediately to prevent frontend blocking
        return {
            "status": "success", 
            "message": "Team approval started. Agents are being created in background.",
            "workspace_id": str(workspace_id),
            "proposal_id": str(proposal_id),
            "background_processing": True,
            "estimated_completion_seconds": 30
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

# Alias endpoint for compatibility with frontend expectations
@router.post("/analyze-and-propose", response_model=DirectorTeamProposalResponse)
async def analyze_and_propose_team(proposal_request: DirectorTeamProposal, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route analyze_and_propose_team called", endpoint="analyze_and_propose_team", trace_id=trace_id)
    
    """
    Alias for create_team_proposal endpoint
    Analyzes workspace and proposes a team configuration
    """
    return await create_team_proposal(proposal_request, request)

async def _get_strategic_goals(workspace_id: str) -> Optional[Dict[str, Any]]:
    """Get strategic goals and deliverables for workspace"""
    try:
        # Get workspace goals with semantic context
        goals_response = supabase.table("workspace_goals").select("*").eq(
            "workspace_id", workspace_id
        ).execute()
        
        if not goals_response.data:
            return None
        
        # Filter out None/null values from the response
        goals = [goal for goal in goals_response.data if goal is not None]
        
        if not goals:
            return None
        
        # Separate final metrics from strategic deliverables
        final_metrics = []
        strategic_deliverables = []
        
        for goal in goals:
            # Safety check for None goals
            if not goal or not isinstance(goal, dict):
                continue
                
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

async def _create_fallback_planning_task(workspace_id: UUID, created_agents_db: List[Dict[str, Any]]):
    """Create a default planning task when goal extraction fails"""
    logger.warning(f"⚠️ Creating fallback planning task for workspace {workspace_id}")
    from database import create_task
    
    assignee_agent_id = None
    if created_agents_db:
        pm_agent = next((agent for agent in created_agents_db if agent.get("role") == "Project Manager"), None)
        assignee_agent_id = pm_agent["id"] if pm_agent else created_agents_db[0]["id"]

    if assignee_agent_id:
        # Create default planning task
        await create_task(
            workspace_id=str(workspace_id),
            name="Project Setup & Strategic Planning Kick-off",
            status="pending",
            description="Define project phases, key deliverables, assess team skills, and create initial sub-tasks for Phase 1.",
            priority="high",
            agent_id=assignee_agent_id
        )
        logger.info("✅ Created default planning task to ensure workflow starts.")
    else:
        logger.error("🚨 Cannot create initial task because no agents were successfully created.")

