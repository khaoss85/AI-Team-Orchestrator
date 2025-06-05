from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any

import importlib

_improvement = importlib.import_module("improvement_loop")

checkpoint_output = getattr(_improvement, "checkpoint_output")
qa_gate = getattr(_improvement, "qa_gate")
close_loop = getattr(_improvement, "close_loop")
DEFAULT_FEEDBACK_TIMEOUT = getattr(_improvement, "DEFAULT_FEEDBACK_TIMEOUT", 60 * 60 * 24)
from database import get_task

router = APIRouter(prefix="/improvement", tags=["improvement"])


@router.post("/start/{task_id}", response_model=Dict[str, Any])
async def start_improvement(task_id: str, payload: Dict[str, Any]):
    task = await get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    approved = await checkpoint_output(task_id, payload, timeout=DEFAULT_FEEDBACK_TIMEOUT)
    return {"task_id": task_id, "approved": approved}


@router.get("/status/{task_id}", response_model=Dict[str, Any])
async def get_status(task_id: str):
    task = await get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "iteration_count": task.get("iteration_count", 0),
        "max_iterations": task.get("max_iterations")
    }


@router.post("/close/{task_id}", response_model=Dict[str, Any])
async def close_improvement(task_id: str):
    await close_loop(task_id)
    return {"closed": True}


@router.post("/qa/{task_id}", response_model=Dict[str, Any])
async def qa_improvement(task_id: str, payload: Dict[str, Any]):
    task = await get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    approved = await qa_gate(task_id, payload)
    return {"task_id": task_id, "approved": approved}
