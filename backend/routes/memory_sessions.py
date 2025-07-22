# backend/routes/memory_sessions.py
"""
Memory Sessions API Routes
Provides endpoints to monitor and manage SDK session integration
"""

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any, Optional
from uuid import UUID
import logging

from services.orchestrator_session_adapter import orchestrator_session_adapter
from middleware.trace_middleware import get_trace_id, create_traced_logger

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/memory/sessions", tags=["memory-sessions"])

@router.get("/workspace/{workspace_id}/summary")
async def get_workspace_memory_summary(workspace_id: UUID, request: Request):
    """
    📊 Get memory session summary for a workspace
    
    Returns:
    - Active agent sessions
    - Conversation summaries
    - Cross-session insights
    - Memory synchronization status
    """
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_workspace_memory_summary called", endpoint="get_workspace_memory_summary", trace_id=trace_id)
    
    try:
        summary = await orchestrator_session_adapter.get_workspace_conversation_summary(
            str(workspace_id)
        )
        
        return {
            "success": True,
            "workspace_id": str(workspace_id),
            "memory_summary": summary
        }
        
    except Exception as e:
        logger.error(f"Error getting workspace memory summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get memory summary: {str(e)}"
        )

@router.post("/workspace/{workspace_id}/sync")
async def sync_workspace_sessions(workspace_id: UUID, request: Request):
    """
    🔄 Manually trigger synchronization of all workspace sessions
    """
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route sync_workspace_sessions called", endpoint="sync_workspace_sessions", trace_id=trace_id)
    
    try:
        # Get all sessions for workspace
        sessions_synced = 0
        
        for session_id, workspace_id_mapped in orchestrator_session_adapter.session_workspace_mapping.items():
            if workspace_id_mapped == str(workspace_id):
                agent_id = session_id.replace("agent_", "").split("_task_")[0]
                success = await orchestrator_session_adapter.sync_session_to_unified_memory(
                    session_id=session_id,
                    agent_id=agent_id,
                    workspace_id=str(workspace_id)
                )
                if success:
                    sessions_synced += 1
        
        return {
            "success": True,
            "workspace_id": str(workspace_id),
            "sessions_synced": sessions_synced,
            "message": f"Synchronized {sessions_synced} sessions to unified memory"
        }
        
    except Exception as e:
        logger.error(f"Error syncing workspace sessions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync sessions: {str(e)}"
        )

@router.get("/stats")
async def get_session_stats(request: Request):
    """
    📈 Get global session statistics
    """
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_session_stats called", endpoint="get_session_stats", trace_id=trace_id)
    
    try:
        stats = {
            "total_active_sessions": len(orchestrator_session_adapter.agent_sessions),
            "workspaces_with_sessions": len(set(orchestrator_session_adapter.session_workspace_mapping.values())),
            "session_details": {}
        }
        
        # Group sessions by workspace
        for session_id, workspace_id in orchestrator_session_adapter.session_workspace_mapping.items():
            if workspace_id not in stats["session_details"]:
                stats["session_details"][workspace_id] = []
            
            stats["session_details"][workspace_id].append({
                "session_id": session_id,
                "agent_id": session_id.replace("agent_", "").split("_task_")[0]
            })
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting session stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session stats: {str(e)}"
        )

@router.post("/cleanup")
async def cleanup_old_sessions(days_old: int = 7, request: Request = None):
    """
    🧹 Cleanup old sessions
    """
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route cleanup_old_sessions called", endpoint="cleanup_old_sessions", trace_id=trace_id)
    
    try:
        await orchestrator_session_adapter.cleanup_old_sessions(days_old)
        
        return {
            "success": True,
            "message": f"Cleaned up sessions older than {days_old} days"
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up sessions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cleanup sessions: {str(e)}"
        )