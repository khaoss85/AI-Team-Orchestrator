#!/usr/bin/env python3
"""
🔄 GOAL SYNC API ROUTES

API endpoints for deliverable-goal synchronization service.
Provides real-time sync capabilities and monitoring.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Optional
import logging

from services.deliverable_goal_sync import deliverable_goal_sync

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/goal-sync", tags=["Goal Sync"])

@router.post("/deliverable/{deliverable_id}")
async def sync_deliverable(
    deliverable_id: str,
    workspace_id: str,
    background_tasks: BackgroundTasks,
    new_status: Optional[str] = None
) -> Dict:
    """
    🔄 Sync goal progress when a deliverable is updated
    
    This endpoint should be called whenever a deliverable status changes
    to ensure goal progress stays in sync.
    """
    try:
        # Run sync in background for better performance
        background_tasks.add_task(
            deliverable_goal_sync.sync_deliverable_completion,
            deliverable_id,
            workspace_id,
            new_status
        )
        
        return {
            "status": "accepted",
            "message": f"Sync initiated for deliverable {deliverable_id}",
            "background_processing": True
        }
        
    except Exception as e:
        logger.error(f"Error initiating deliverable sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workspace/{workspace_id}/bulk-sync")
async def bulk_sync_workspace(
    workspace_id: str,
    background_tasks: BackgroundTasks
) -> Dict:
    """
    🔄 Bulk sync all goals in a workspace
    
    Useful for periodic reconciliation or recovery scenarios.
    """
    try:
        # Run bulk sync in background
        background_tasks.add_task(
            deliverable_goal_sync.sync_workspace_goals,
            workspace_id
        )
        
        return {
            "status": "accepted",
            "message": f"Bulk sync initiated for workspace {workspace_id}",
            "background_processing": True
        }
        
    except Exception as e:
        logger.error(f"Error initiating bulk sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_sync_status(workspace_id: Optional[str] = None) -> Dict:
    """
    📊 Get sync service status and statistics
    """
    try:
        status = await deliverable_goal_sync.get_sync_status(workspace_id)
        return {
            "status": "success",
            "data": status
        }
        
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workspace/{workspace_id}/reconcile")
async def reconcile_workspace_progress(workspace_id: str) -> Dict:
    """
    🔧 Reconcile goal progress with actual deliverable completion
    
    This performs an immediate (not background) sync and returns results.
    """
    try:
        result = await deliverable_goal_sync.sync_workspace_goals(workspace_id)
        
        return {
            "status": "success",
            "operation": result.operation.value,
            "sync_status": result.status.value,
            "goals_updated": result.goals_updated,
            "progress_changes": {
                goal_id: {
                    "before": result.progress_before.get(goal_id, 0),
                    "after": result.progress_after.get(goal_id, 0),
                    "change": result.progress_after.get(goal_id, 0) - result.progress_before.get(goal_id, 0)
                }
                for goal_id in result.progress_after.keys()
            },
            "errors": result.errors,
            "timestamp": result.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error reconciling workspace progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))