# backend/utils/hashing.py
import hashlib
import json
from typing import Dict, Any, Optional
from uuid import UUID

def generate_semantic_hash(
    name: str,
    description: Optional[str],
    goal_id: Optional[UUID],
    context_data: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generates a deterministic SHA-256 hash for a task based on its
    semantic content. This ensures that tasks with the same intent
    are treated as identical.

    Args:
        name: The name of the task.
        description: The description of the task.
        goal_id: The optional ID of the goal the task is associated with.
        context_data: Additional context data for the task.

    Returns:
        A SHA-256 hash string representing the task's semantic content.
    """
    # Create a stable string representation of the task's content.
    # Sorting the keys of context_data ensures the JSON string is deterministic.
    context_str = json.dumps(context_data, sort_keys=True) if context_data else ""
    
    # Normalize and concatenate key fields to create the hash input.
    # Using a pipe separator to prevent collisions between fields.
    hash_input = (
        f"{name.strip().lower()}|"
        f"{description.strip().lower() if description else ''}|"
        f"{str(goal_id)}|"
        f"{context_str}"
    )
    
    return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
