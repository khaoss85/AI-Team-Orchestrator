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
    update_workspace_status,
    _auto_create_workspace_goals
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/workspaces", tags=["workspaces"])

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "service": "workspaces"}

@router.get("/", response_model=List[Workspace])
async def get_all_workspaces(limit: Optional[int] = 50, user_id: Optional[str] = None):
    """Get all workspaces with optional limit and user filter"""
    try:
        from database import supabase
        
        # If user_id provided, filter by user, otherwise get all
        if user_id:
            result = supabase.table("workspaces").select("*").eq("user_id", user_id).limit(limit).execute()
        else:
            result = supabase.table("workspaces").select("*").limit(limit).execute()
        
        workspaces = result.data or []
        return workspaces
    except Exception as e:
        logger.error(f"Error fetching workspaces: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch workspaces: {str(e)}"
        )

@router.post("/", response_model=Workspace, status_code=status.HTTP_201_CREATED)
async def create_new_workspace(workspace: WorkspaceCreate):
    try:
        # Generate default user_id if not provided (must be valid UUID)
        from uuid import uuid4
        user_id = str(workspace.user_id) if workspace.user_id else str(uuid4())
        
        created_workspace = await create_workspace(
            name=workspace.name,
            description=workspace.description,
            user_id=user_id,
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
    try:
        logger.info(f"Fetching workspaces for user: {user_id}")
        workspaces = await list_workspaces(str(user_id))
        logger.info(f"Successfully fetched {len(workspaces) if workspaces else 0} workspaces for user {user_id}")
        return workspaces or []
    except Exception as e:
        logger.error(f"Error fetching workspaces for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch workspaces: {str(e)}"
        )

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

# Human Interaction Endpoints for Human-in-the-Loop Workflow

@router.post("/{workspace_id}/ask-question", status_code=status.HTTP_200_OK)
async def ask_question_to_team(workspace_id: UUID, request: Dict[str, Any]):
    """Ask a question to the AI team"""
    try:
        workspace = await get_workspace(str(workspace_id))
        if not workspace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        question = request.get("question", "")
        target_agent = request.get("target_agent")
        
        if not question.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question cannot be empty")

        # Create a task for answering the question
        from database import create_task
        
        task_name = "Answer Human Question"
        task_description = f"Human Question: {question}"
        if target_agent:
            task_description += f"\n\nDirected to: {target_agent}"
        
        task = await create_task(
            workspace_id=str(workspace_id),
            name=task_name,
            status="pending",
            description=task_description,
            priority="medium"
        )
        
        logger.info(f"Created question task {task['id']} for workspace {workspace_id}")
        
        return {
            "success": True,
            "message": "Question sent to AI team",
            "task_id": task["id"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending question: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to send question: {str(e)}")

@router.post("/{workspace_id}/provide-feedback", status_code=status.HTTP_200_OK)
async def provide_feedback_to_team(workspace_id: UUID, request: Dict[str, Any]):
    """Provide general feedback to the AI team"""
    try:
        workspace = await get_workspace(str(workspace_id))
        if not workspace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        feedback = request.get("feedback", "")
        context = request.get("context", {})
        
        if not feedback.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Feedback cannot be empty")

        # Create a human feedback request
        from human_feedback_manager import get_human_feedback_manager
        
        feedback_manager = await get_human_feedback_manager()
        
        feedback_request = await feedback_manager.create_feedback_request(
            workspace_id=str(workspace_id),
            request_type="general_feedback",
            title="Human Feedback Provided",
            description=feedback,
            context={"feedback": feedback, "additional_context": context},
            priority="medium"
        )
        
        logger.info(f"Created feedback request {feedback_request['id']} for workspace {workspace_id}")
        
        return {
            "success": True,
            "message": "Feedback sent to AI team",
            "feedback_request_id": feedback_request["id"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error providing feedback: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to provide feedback: {str(e)}")

@router.post("/{workspace_id}/request-iteration", status_code=status.HTTP_200_OK)
async def request_iteration(workspace_id: UUID, request: Dict[str, Any]):
    """Request an iteration with specific changes"""
    try:
        workspace = await get_workspace(str(workspace_id))
        if not workspace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        changes = request.get("changes", [])
        
        if not changes or (isinstance(changes, list) and not any(changes)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Changes list cannot be empty")

        # Create iteration tasks
        from database import create_task
        
        tasks_created = []
        for i, change in enumerate(changes):
            if isinstance(change, str) and change.strip():
                task_name = f"Iteration Request {i+1}"
                task_description = f"Requested Change: {change}"
                
                task = await create_task(
                    workspace_id=str(workspace_id),
                    name=task_name,
                    status="pending",
                    description=task_description,
                    priority="high"
                )
                tasks_created.append(task["id"])
        
        logger.info(f"Created {len(tasks_created)} iteration tasks for workspace {workspace_id}")
        
        return {
            "success": True,
            "message": f"Iteration request created with {len(tasks_created)} change tasks",
            "task_ids": tasks_created
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error requesting iteration: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to request iteration: {str(e)}")

@router.post("/{workspace_id}/approve-completion", status_code=status.HTTP_200_OK)
async def approve_project_completion(workspace_id: UUID):
    """Approve the completion of the project"""
    try:
        workspace = await get_workspace(str(workspace_id))
        if not workspace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        # Update workspace status to completed
        await update_workspace_status(str(workspace_id), "completed")
        
        # Log approval
        logger.info(f"Project {workspace_id} approved by human reviewer")
        
        return {
            "success": True,
            "message": "Project completion approved",
            "status": "completed"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving completion: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to approve completion: {str(e)}")

@router.post("/{workspace_id}/request-changes", status_code=status.HTTP_200_OK)
async def request_changes_to_completion(workspace_id: UUID, request: Dict[str, Any]):
    """Request changes to the completed project"""
    try:
        workspace = await get_workspace(str(workspace_id))
        if not workspace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        changes = request.get("changes", "")
        priority = request.get("priority", "medium")
        
        if not changes.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Changes description cannot be empty")

        # Create a high-priority task for the requested changes
        from database import create_task
        
        task = await create_task(
            workspace_id=str(workspace_id),
            name="Final Changes Requested",
            status="pending",
            description=f"Human-requested changes to final deliverables:\n\n{changes}",
            priority=priority
        )
        
        # Also create a human feedback request for tracking
        from human_feedback_manager import get_human_feedback_manager
        
        feedback_manager = await get_human_feedback_manager()
        
        feedback_request = await feedback_manager.create_feedback_request(
            workspace_id=str(workspace_id),
            request_type="change_request",
            title="Final Changes Requested",
            description=changes,
            context={"priority": priority, "task_id": task["id"]},
            priority=priority
        )
        
        logger.info(f"Created change request task {task['id']} and feedback request {feedback_request['id']} for workspace {workspace_id}")
        
        return {
            "success": True,
            "message": "Change request submitted",
            "task_id": task["id"],
            "feedback_request_id": feedback_request["id"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error requesting changes: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to request changes: {str(e)}")

@router.post("/{workspace_id}/create-goals", status_code=status.HTTP_200_OK)
async def create_workspace_goals(workspace_id: UUID):
    """
    🎯 Create workspace goals from workspace goal text
    
    This endpoint retroactively creates workspace_goals records from the 
    workspace's goal text for workspaces that don't have numerical goals yet.
    """
    try:
        workspace = await get_workspace(str(workspace_id))
        if not workspace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
        
        goal_text = workspace.get("goal")
        if not goal_text:
            return {"success": False, "message": "Workspace has no goal text"}
        
        # Create workspace goals from goal text
        created_goals = await _auto_create_workspace_goals(str(workspace_id), goal_text)
        
        return {
            "success": True,
            "message": f"Created {len(created_goals)} workspace goals",
            "goals_created": len(created_goals),
            "goals": created_goals
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating workspace goals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to create workspace goals: {str(e)}"
        )

@router.get("/{workspace_id}/tasks", status_code=status.HTTP_200_OK)
async def get_workspace_tasks(workspace_id: UUID, task_type: Optional[str] = None):
    """Get tasks for a workspace, optionally filtered by task type"""
    try:
        from database import list_tasks
        
        workspace = await get_workspace(str(workspace_id))
        if not workspace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        # Get all tasks for the workspace
        all_tasks = await list_tasks(str(workspace_id))
        
        # Filter by task_type if provided
        if task_type:
            filtered_tasks = [
                task for task in all_tasks 
                if (task.get("task_type") == task_type or 
                    task.get("context_data", {}).get("task_type") == task_type or
                    task.get("creation_type") == task_type)
            ]
        else:
            filtered_tasks = all_tasks
        
        logger.info(f"📋 Retrieved {len(filtered_tasks)} tasks for workspace {workspace_id} (filter: {task_type})")
        
        return filtered_tasks
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workspace tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to get workspace tasks: {str(e)}"
        )
