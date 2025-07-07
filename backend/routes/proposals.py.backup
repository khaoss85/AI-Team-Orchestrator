from fastapi import APIRouter, HTTPException, status, Body
from typing import Optional, Dict, Any
from uuid import UUID
import logging

from database import (
    get_team_proposal,
    update_team_proposal_status,
    log_proposal_decision,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/proposals", tags=["proposals"])


@router.post("/{proposal_id}/approve", status_code=status.HTTP_200_OK)
async def approve_proposal(proposal_id: UUID) -> Dict[str, Any]:
    """Approve a stored proposal."""
    try:
        proposal = await get_team_proposal(str(proposal_id))
        if not proposal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")

        await update_team_proposal_status(str(proposal_id), "approved")
        await log_proposal_decision(proposal["workspace_id"], str(proposal_id), "approved")
        
        # 🚀 AUTO-START: When team is approved, check if goals exist and trigger task generation
        workspace_id = proposal["workspace_id"]
        logger.info(f"🎯 Team approved for workspace {workspace_id}, checking for goals...")
        
        try:
            # First check if workspace has confirmed goals
            from database import supabase
            goals_response = supabase.table("workspace_goals").select("id").eq(
                "workspace_id", str(workspace_id)
            ).eq("status", "active").execute()
            
            if goals_response.data and len(goals_response.data) > 0:
                logger.info(f"✅ Found {len(goals_response.data)} active goals, triggering auto-start")
                
                from automated_goal_monitor import automated_goal_monitor
                import asyncio
                
                # Trigger immediate goal analysis and task creation
                asyncio.create_task(automated_goal_monitor._trigger_immediate_goal_analysis(str(workspace_id)))
                
                return {"success": True, "message": f"Team approved and auto-start triggered for {len(goals_response.data)} goals!"}
            else:
                logger.warning(f"⚠️ No active goals found for workspace {workspace_id}")
                return {"success": True, "message": "Team approved. Please confirm goals to start task execution."}
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to trigger auto-start after team approval: {e}")
            # Don't fail the approval, just log the warning
            return {"success": True, "message": "Team approved (auto-start check failed)"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving proposal {proposal_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to approve proposal")


@router.post("/{proposal_id}/reject", status_code=status.HTTP_200_OK)
async def reject_proposal(
    proposal_id: UUID,
    payload: Optional[Dict[str, Any]] = Body(default=None),
) -> Dict[str, Any]:
    """Reject a stored proposal."""
    reason = payload.get("reason") if payload else None
    try:
        proposal = await get_team_proposal(str(proposal_id))
        if not proposal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")

        await update_team_proposal_status(str(proposal_id), "rejected")
        await log_proposal_decision(proposal["workspace_id"], str(proposal_id), "rejected", reason)
        return {"success": True, "message": "Proposal rejected"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting proposal {proposal_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reject proposal")
