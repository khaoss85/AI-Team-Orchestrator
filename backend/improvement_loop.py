import asyncio
import logging
from typing import Dict, Any, Optional, List

from human_feedback_manager import human_feedback_manager, FeedbackRequestType
from database import (
    get_task,
    list_tasks,
    update_task_status,
    create_task,
    update_task_fields
)
from models import TaskStatus

logger = logging.getLogger(__name__)


async def checkpoint_output(task_id: str, output: Dict[str, Any]) -> bool:
    """Ask for human feedback on a task output."""
    task = await get_task(task_id)
    if not task:
        return False

    workspace_id = task["workspace_id"]
    result: Dict[str, Any] = {"approved": True, "comments": ""}
    event = asyncio.Event()

    async def _on_response(_, response: Dict[str, Any]):
        result.update({
            "approved": response.get("approved", True),
            "comments": response.get("comments", "")
        })
        event.set()

    await human_feedback_manager.request_feedback(
        workspace_id=workspace_id,
        request_type=FeedbackRequestType.TASK_APPROVAL,
        title=f"Review output for task {task['name']}",
        description="Please review the generated output and provide comments.",
        proposed_actions=[{"label": "approve", "value": "approve"}, {"label": "changes", "value": "changes"}],
        context={"task_id": task_id, "output": output},
        response_callback=_on_response
    )

    await event.wait()

    if not result["approved"]:
        await feedback_to_task(result["comments"], workspace_id, task_id)
        await update_task_status(task_id, TaskStatus.STALE.value)
        return False
    return True


async def feedback_to_task(comments: str, workspace_id: str, original_task_id: str) -> Optional[Dict[str, Any]]:
    """Convert human feedback comments into a follow up task."""
    try:
        new_task = await create_task(
            workspace_id=workspace_id,
            name=f"Address feedback for {original_task_id}",
            description=comments,
            status=TaskStatus.PENDING.value,
            parent_task_id=original_task_id,
            creation_type="feedback",
        )
        return new_task
    except Exception as e:
        logger.error(f"Failed creating feedback task: {e}")
        return None


async def controlled_iteration(task_id: str, workspace_id: str, max_iterations: Optional[int]) -> bool:
    """Increment iteration count and check against max."""
    task = await get_task(task_id)
    if not task:
        return False
    iteration = task.get("iteration_count", 0) + 1
    await update_task_fields(task_id, {"iteration_count": iteration})
    if max_iterations is not None and iteration > max_iterations:
        await update_task_status(task_id, TaskStatus.FAILED.value, {"detail": "max_iterations_exceeded"})
        return False
    return True


async def refresh_dependencies(task_id: str) -> None:
    """Mark tasks depending on the given task as stale."""
    task = await get_task(task_id)
    if not task:
        return
    workspace_id = task["workspace_id"]
    tasks = await list_tasks(workspace_id)
    for t in tasks:
        deps = t.get("depends_on_task_ids") or []
        if task_id in deps:
            try:
                await update_task_status(t["id"], TaskStatus.STALE.value)
            except Exception as e:
                logger.error(f"Failed refreshing dependency {t['id']}: {e}")


async def qa_gate(task_id: str, output: Dict[str, Any]) -> bool:
    """Final QA approval for a task."""
    task = await get_task(task_id)
    if not task:
        return False
    workspace_id = task["workspace_id"]
    result: Dict[str, Any] = {"approved": True, "comments": ""}
    event = asyncio.Event()

    async def _on_response(_, response: Dict[str, Any]):
        result.update({
            "approved": response.get("approved", True),
            "comments": response.get("comments", "")
        })
        event.set()

    await human_feedback_manager.request_feedback(
        workspace_id=workspace_id,
        request_type=FeedbackRequestType.TASK_APPROVAL,
        title=f"QA approval for task {task['name']}",
        description="Approve final output or request changes.",
        proposed_actions=[{"label": "approve", "value": "approve"}, {"label": "changes", "value": "changes"}],
        context={"task_id": task_id, "output": output},
        response_callback=_on_response
    )

    await event.wait()

    if not result["approved"]:
        await feedback_to_task(result["comments"], workspace_id, task_id)
        await update_task_status(task_id, TaskStatus.STALE.value)
        return False
    return True


async def close_loop(task_id: str) -> None:
    """Mark improvement loop closed for the given task."""
    try:
        await update_task_fields(task_id, {"iteration_count": 0})
    except Exception as e:
        logger.error(f"Failed closing improvement loop for {task_id}: {e}")
