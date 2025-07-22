# backend/services/task_deduplication_manager.py
import logging
import asyncio
from typing import Dict, Any, Optional
from uuid import UUID
from asyncpg.exceptions import UniqueViolationError

from database import supabase
from models import Task, TaskCreate
from utils.hashing import generate_semantic_hash

logger = logging.getLogger(__name__)

class TaskDeduplicationManager:
    """
    Manages task creation with a robust, database-first deduplication strategy.
    
    This system relies on a 'semantic_hash' generated from the task's core
    content (name, description, goal_id). A unique constraint in the database
    on (workspace_id, semantic_hash) prevents the creation of duplicate tasks
    at the lowest level, ensuring data integrity and system robustness.
    """

    async def create_task_with_deduplication(
        self,
        task_data: TaskCreate
    ) -> Optional[Task]:
        """
        Creates a new task while ensuring it is not a semantic duplicate.

        This is the primary entry point for creating tasks in the system.

        Args:
            task_data: The Pydantic model containing the data for the new task.

        Returns:
            The created or existing Task object if successful, otherwise None.
        """
        try:
            # 1. Generate the AI-driven semantic hash from the task's content
            try:
                from utils.ai_semantic_hash import generate_ai_semantic_hash
                task_data.semantic_hash = await generate_ai_semantic_hash(
                    name=task_data.name,
                    description=task_data.description,
                    goal_id=task_data.goal_id,
                    context={"agent_role": getattr(task_data, 'agent_role', None)}
                )
                logger.info(f"✅ Generated AI semantic hash for task: {task_data.name}")
            except Exception as e:
                logger.warning(f"⚠️ AI semantic hash failed, using fallback: {e}")
                # Fallback to original method
                from utils.hashing import generate_semantic_hash
                task_data.semantic_hash = generate_semantic_hash(
                    name=task_data.name,
                    description=task_data.description,
                    goal_id=task_data.goal_id,
                # context_data can be added here if it becomes part of the uniqueness check
            )

            # 2. Attempt to insert the new task into the database
            # Convert UUIDs to strings for database compatibility
            task_dict = task_data.model_dump(exclude_unset=True)
            
            # Convert UUID fields to strings for Supabase compatibility
            for field in ['workspace_id', 'goal_id', 'agent_id']:
                if field in task_dict and task_dict[field] is not None:
                    task_dict[field] = str(task_dict[field])
            
            response = supabase.table("tasks").insert(task_dict).execute()
            
            if response.data:
                created_task = Task.model_validate(response.data[0])
                logger.info(f"✅ Task '{created_task.name}' created successfully with ID: {created_task.id}")
                return created_task
            else:
                logger.error(f"Failed to create task '{task_data.name}': No data returned from insert.")
                return None

        except Exception as e:
            if "duplicate key value violates unique constraint" in str(e):
                logger.warning(
                    f"️️️⚠️ Duplicate task detected by database constraint for hash: {task_data.semantic_hash}. "
                    f"Fetching existing task for workspace {task_data.workspace_id}."
                )
                
                # Retrieve the existing task that caused the violation
                existing_task = await self.get_task_by_semantic_hash(
                    task_data.workspace_id,
                    task_data.semantic_hash
                )
                
                if existing_task:
                    logger.info(f"Returning existing task ID: {existing_task.id} for duplicate '{task_data.name}'.")
                    return existing_task
                else:
                    # This case is unlikely but handled for robustness
                    logger.error(
                        f"Integrity error for hash {task_data.semantic_hash}, but could not retrieve the existing task."
                    )
                    return None
            else:
                logger.exception(
                    f"An unexpected error occurred in create_task_with_deduplication for task '{task_data.name}': {e}",
                    exc_info=True
                )
                return None

    async def get_task_by_semantic_hash(
        self,
        workspace_id: UUID,
        semantic_hash: str
    ) -> Optional[Task]:
        """
        Retrieves a task by its semantic hash within a specific workspace.

        Args:
            workspace_id: The ID of the workspace.
            semantic_hash: The semantic hash of the task.

        Returns:
            The Task object if found, otherwise None.
        """
        try:
            response = supabase.table("tasks").select("*").eq(
                "workspace_id", str(workspace_id)
            ).eq("semantic_hash", semantic_hash).limit(1).execute()

            if response.data:
                return Task.model_validate(response.data[0])
            return None
        except Exception as e:
            logger.error(f"Error retrieving task by semantic hash {semantic_hash}: {e}")
            return None

# Global instance for easy access across the application
task_deduplication_manager = TaskDeduplicationManager()
