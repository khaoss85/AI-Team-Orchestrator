from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging

from models import (
    WorkspaceCreate,
    WorkspaceUpdate,
    Workspace,
    WorkspaceStatus,
    TaskCreate,
    Task
)
from database import (
    create_workspace,
    get_workspace,
    list_workspaces,
    delete_workspace,
    update_workspace,
    update_workspace_status
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/workspaces", tags=["workspaces"])

@router.post("/", response_model=Workspace, status_code=status.HTTP_201_CREATED)
async def create_new_workspace(workspace: WorkspaceCreate):
    try:
        created_workspace = await create_workspace(
            name=workspace.name,
            description=workspace.description,
            user_id=str(workspace.user_id),
            goal=workspace.goal,
            budget=workspace.budget
        )
        return created_workspace
    except Exception as e:
        logger.error(f"Error creating workspace: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workspace: {str(e)}"
        )

@router.get("/{workspace_id}", response_model=Workspace)
async def get_workspace_by_id(workspace_id: UUID):
    workspace = await get_workspace(str(workspace_id))
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    return workspace

@router.get("/user/{user_id}", response_model=List[Workspace])
async def get_user_workspaces(user_id: UUID):
    workspaces = await list_workspaces(str(user_id))
    return workspaces

@router.delete("/{workspace_id}", status_code=status.HTTP_200_OK)
async def delete_workspace_by_id(workspace_id: UUID):
    """Delete a workspace and all its associated data"""
    try:
        # Verifica se il workspace esiste
        workspace = await get_workspace(str(workspace_id))
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )
        
        # Clean up human feedback requests first
        from human_feedback_manager import human_feedback_manager
        await human_feedback_manager.cleanup_workspace_requests(str(workspace_id))
        
        # Elimina il workspace (cascading delete will handle related records)
        await delete_workspace(str(workspace_id))
        
        return {
            "success": True,
            "message": f"Workspace {workspace_id} deleted successfully",
            "workspace_id": str(workspace_id)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting workspace: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete workspace: {str(e)}"
        )


@router.put("/{workspace_id}", status_code=status.HTTP_200_OK)
async def update_workspace_by_id(workspace_id: UUID, workspace_update: WorkspaceUpdate):
    """Update workspace fields"""
    try:
        workspace = await get_workspace(str(workspace_id))
        if not workspace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        update_data = {}
        for field, value in workspace_update.model_dump(exclude_unset=True).items():
            if value is None:
                continue
            update_data[field] = value.value if hasattr(value, "value") else value

        if not update_data:
            return {"success": True, "message": "No fields updated"}

        await update_workspace(str(workspace_id), update_data)
        return {"success": True, "message": "Workspace updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating workspace: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update workspace: {str(e)}")


@router.post("/{workspace_id}/pause", status_code=status.HTTP_200_OK)
async def pause_workspace(workspace_id: UUID):
    """Pause a workspace"""
    try:
        workspace = await get_workspace(str(workspace_id))
        if not workspace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        if workspace.get("status") == WorkspaceStatus.PAUSED.value:
            return {"success": True, "message": "Workspace already paused"}

        await update_workspace_status(str(workspace_id), WorkspaceStatus.PAUSED.value)
        return {"success": True, "message": "Workspace paused"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing workspace: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to pause workspace: {str(e)}")


@router.post("/{workspace_id}/resume", status_code=status.HTTP_200_OK)
async def resume_workspace(workspace_id: UUID):
    """Resume a paused workspace"""
    try:
        workspace = await get_workspace(str(workspace_id))
        if not workspace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        if workspace.get("status") != WorkspaceStatus.PAUSED.value:
            return {"success": True, "message": "Workspace is not paused"}

        await update_workspace_status(str(workspace_id), WorkspaceStatus.ACTIVE.value)
        return {"success": True, "message": "Workspace resumed"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming workspace: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to resume workspace: {str(e)}")

@router.get("/{workspace_id}/settings", status_code=status.HTTP_200_OK)
async def get_workspace_settings(workspace_id: UUID):
    """Get workspace-specific settings"""
    try:
        from utils.project_settings import get_project_settings
        
        workspace = await get_workspace(str(workspace_id))
        if not workspace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        project_settings = get_project_settings(str(workspace_id))
        settings = await project_settings.get_all_settings()
        
        return {
            "success": True,
            "workspace_id": str(workspace_id),
            "settings": settings
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workspace settings: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get workspace settings: {str(e)}")
