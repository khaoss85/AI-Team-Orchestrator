from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging

from models import (
    WorkspaceCreate, 
    WorkspaceUpdate, 
    Workspace,
    TaskCreate,
    Task
)
from database import (
    create_workspace,
    get_workspace,
    list_workspaces,
    delete_workspace
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
            
        # Elimina il workspace
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