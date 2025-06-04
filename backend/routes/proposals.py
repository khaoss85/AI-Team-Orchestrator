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
        return {"success": True, "message": "Proposal approved"}
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
