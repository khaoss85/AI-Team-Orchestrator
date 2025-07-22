# backend/routes/task_monitoring.py
"""
🔍 Task Execution Monitoring API
================================================================================
Endpoints per monitoraggio real-time dell'esecuzione dei task e hang detection.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Import monitoring system
try:
    from task_execution_monitor import task_monitor
    MONITOR_AVAILABLE = True
except ImportError:
    MONITOR_AVAILABLE = False
    task_monitor = None

router = APIRouter(prefix="/api/monitoring", tags=["Task Monitoring"])

@router.get("/task_traces")
async def get_all_task_traces() -> Dict[str, Any]:
    """
    📊 Get all active task execution traces
    
    Returns comprehensive monitoring data for all currently tracked tasks.
    """
    if not MONITOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Task monitoring not available")
    
    try:
        traces = task_monitor.get_all_active_traces()
        
        # Add summary statistics
        summary = {
            "total_active_tasks": len(traces),
            "hanging_tasks": len([t for t in traces.values() if t.get("is_hanging", False)]),
            "avg_execution_time": sum(t.get("execution_time", 0) for t in traces.values()) / max(len(traces), 1),
            "stages_distribution": {}
        }
        
        # Count stages
        for trace in traces.values():
            stage = trace.get("current_stage", "unknown")
            summary["stages_distribution"][stage] = summary["stages_distribution"].get(stage, 0) + 1
        
        return {
            "summary": summary,
            "traces": traces,
            "timestamp": "2025-01-13T12:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Failed to get task traces: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get traces: {str(e)}")

@router.get("/task_traces/{task_id}")
async def get_task_trace(task_id: str) -> Dict[str, Any]:
    """
    🔍 Get detailed execution trace for a specific task
    """
    if not MONITOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Task monitoring not available")
    
    try:
        trace = task_monitor.get_trace_summary(task_id)
        
        if not trace:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found in monitoring")
        
        return trace
        
    except Exception as e:
        logger.error(f"Failed to get trace for task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get trace: {str(e)}")

@router.get("/hanging_tasks")
async def get_hanging_tasks() -> Dict[str, Any]:
    """
    🚨 Get all tasks currently detected as hanging
    
    Returns tasks that have been stuck in the same execution stage
    for longer than the configured threshold.
    """
    if not MONITOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Task monitoring not available")
    
    try:
        hanging_tasks = task_monitor.get_hanging_tasks()
        
        # Group by stage for pattern analysis
        patterns = {}
        for task in hanging_tasks:
            stage = task.get("current_stage", "unknown")
            if stage not in patterns:
                patterns[stage] = []
            patterns[stage].append({
                "task_id": task["task_id"],
                "workspace_id": task["workspace_id"],
                "execution_time": task["execution_time"],
                "stage_count": task["stage_count"]
            })
        
        return {
            "hanging_tasks": hanging_tasks,
            "patterns": patterns,
            "total_hanging": len(hanging_tasks),
            "timestamp": "2025-01-13T12:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Failed to get hanging tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get hanging tasks: {str(e)}")

@router.get("/execution_patterns")
async def get_execution_patterns(
    workspace_id: Optional[str] = Query(None, description="Filter by workspace")
) -> Dict[str, Any]:
    """
    📈 Analyze execution patterns across tasks
    
    Provides insights into:
    - Common hanging stages
    - Average execution times per stage
    - Success/failure patterns
    """
    if not MONITOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Task monitoring not available")
    
    try:
        all_traces = task_monitor.get_all_active_traces()
        
        # Filter by workspace if specified
        if workspace_id:
            all_traces = {
                task_id: trace for task_id, trace in all_traces.items()
                if trace.get("workspace_id") == workspace_id
            }
        
        # Analyze patterns
        stage_times = {}
        stage_failures = {}
        total_by_stage = {}
        
        for trace in all_traces.values():
            stages = trace.get("stages", [])
            errors = trace.get("errors", [])
            
            # Calculate time spent in each stage
            for i, stage_data in enumerate(stages):
                stage = stage_data["stage"]
                if stage not in stage_times:
                    stage_times[stage] = []
                    stage_failures[stage] = 0
                    total_by_stage[stage] = 0
                
                total_by_stage[stage] += 1
                
                # Calculate stage duration
                if i + 1 < len(stages):
                    # Time to next stage
                    from datetime import datetime
                    start_time = datetime.fromisoformat(stage_data["timestamp"])
                    end_time = datetime.fromisoformat(stages[i + 1]["timestamp"])
                    duration = (end_time - start_time).total_seconds()
                    stage_times[stage].append(duration)
                
                # Check for errors in this stage
                if any(stage in error for error in errors):
                    stage_failures[stage] += 1
        
        # Calculate averages and failure rates
        patterns = {}
        for stage in stage_times:
            times = stage_times[stage]
            patterns[stage] = {
                "total_occurrences": total_by_stage[stage],
                "avg_duration_seconds": sum(times) / max(len(times), 1),
                "max_duration_seconds": max(times) if times else 0,
                "failure_count": stage_failures[stage],
                "failure_rate": stage_failures[stage] / max(total_by_stage[stage], 1)
            }
        
        return {
            "patterns": patterns,
            "total_analyzed_tasks": len(all_traces),
            "workspace_filter": workspace_id,
            "timestamp": "2025-01-13T12:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze execution patterns: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze patterns: {str(e)}")

@router.post("/force_task_completion/{task_id}")
async def force_task_completion(task_id: str) -> Dict[str, Any]:
    """
    🛠️ Force completion of a hanging task
    
    Emergency endpoint to manually complete a task that appears to be stuck.
    """
    if not MONITOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Task monitoring not available")
    
    try:
        # Check if task is actually hanging
        trace = task_monitor.get_trace_summary(task_id)
        if not trace:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found in monitoring")
        
        if not trace.get("is_hanging", False):
            return {
                "message": f"Task {task_id} is not hanging",
                "current_stage": trace.get("current_stage"),
                "execution_time": trace.get("execution_time")
            }
        
        # Force completion in monitoring system
        from task_execution_monitor import trace_error, trace_task_complete
        trace_error(task_id, "Manually forced completion due to hanging", None)
        trace_task_complete(task_id, success=False)
        
        logger.warning(f"🛠️ Manually forced completion of hanging task {task_id}")
        
        return {
            "message": f"Task {task_id} forced to completion",
            "was_hanging_in_stage": trace.get("current_stage"),
            "execution_time": trace.get("execution_time")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to force task completion for {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to force completion: {str(e)}")

@router.get("/health")
async def monitoring_health() -> Dict[str, Any]:
    """
    🏥 Health check for task monitoring system
    """
    return {
        "monitoring_available": MONITOR_AVAILABLE,
        "active_traces": len(task_monitor.get_all_active_traces()) if MONITOR_AVAILABLE else 0,
        "hanging_tasks": len(task_monitor.get_hanging_tasks()) if MONITOR_AVAILABLE else 0,
        "status": "healthy" if MONITOR_AVAILABLE else "monitoring_disabled"
    }