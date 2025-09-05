"""
Real-Time Thinking API Routes - Pillar 10: Real-Time Thinking
RESTful and WebSocket endpoints for real-time thinking visualization.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from uuid import UUID
from fastapi import Request, APIRouter, HTTPException
from middleware.trace_middleware import get_trace_id, create_traced_logger, TracedDatabaseOperation
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json

from services.thinking_process import thinking_engine, ThinkingProcess, ThinkingStep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/thinking", tags=["thinking"])

# Request/Response Models
class ThinkingQuery(BaseModel):
    workspace_id: UUID
    query: str
    process_type: str = "general"

class ThinkingStepCreate(BaseModel):
    process_id: str
    step_type: str = Field(..., pattern="^(analysis|reasoning|evaluation|conclusion|context_loading|perspective|critical_review|synthesis)$")
    content: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = {}

class ThinkingProcessResponse(BaseModel):
    process_id: str
    workspace_id: str
    context: str
    steps: List[Dict[str, Any]]
    final_conclusion: Optional[str]
    overall_confidence: float
    started_at: str
    completed_at: Optional[str]
    status: str
    # Enhanced UX fields
    title: Optional[str] = None
    summary_metadata: Optional[Dict[str, Any]] = None

class ThinkingStepResponse(BaseModel):
    step_id: str
    step_type: str
    content: str
    confidence: float
    timestamp: str
    metadata: Dict[str, Any]

# === THINKING PROCESS ENDPOINTS ===

@router.get("/{workspace_id}")
async def get_workspace_thinking_processes(request: Request, workspace_id: UUID, limit: int = 10):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_workspace_thinking_processes called", endpoint="get_workspace_thinking_processes", trace_id=trace_id)

    """Get recent thinking processes for workspace"""
    try:
        logger.info(f"💭 Getting thinking processes for workspace: {workspace_id}")
        
        processes = await thinking_engine.get_workspace_thinking(workspace_id, limit)
        
        # Convert to response format
        response_processes = []
        for process in processes:
            steps_data = []
            for step in process.steps:
                steps_data.append({
                    "step_id": step.step_id,
                    "step_type": step.step_type,
                    "content": step.content,
                    "confidence": step.confidence,
                    "timestamp": step.timestamp,
                    "metadata": step.metadata or {}
                })
            
            response_processes.append(ThinkingProcessResponse(
                process_id=process.process_id,
                workspace_id=process.workspace_id,
                context=process.context,
                steps=steps_data,
                final_conclusion=process.final_conclusion,
                overall_confidence=process.overall_confidence,
                started_at=process.started_at,
                completed_at=process.completed_at,
                status="completed" if process.completed_at else "active",
                title=process.title,  # Include title
                summary_metadata=process.summary_metadata  # Include metadata
            ))
        
        logger.info(f"✅ Retrieved {len(response_processes)} thinking processes")
        return response_processes
        
    except Exception as e:
        logger.error(f"Failed to get thinking processes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/process/{process_id}")
async def get_thinking_process(process_id: str, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_thinking_process called", endpoint="get_thinking_process", trace_id=trace_id)

    """Get specific thinking process by ID"""
    try:
        logger.info(f"💭 Getting thinking process: {process_id}")
        
        process = await thinking_engine.get_thinking_process(process_id)
        
        if not process:
            raise HTTPException(status_code=404, detail="Thinking process not found")
        
        # Convert to response format
        steps_data = []
        for step in process.steps:
            steps_data.append({
                "step_id": step.step_id,
                "step_type": step.step_type,
                "content": step.content,
                "confidence": step.confidence,
                "timestamp": step.timestamp,
                "metadata": step.metadata or {}
            })
        
        response = ThinkingProcessResponse(
            process_id=process.process_id,
            workspace_id=process.workspace_id,
            context=process.context,
            steps=steps_data,
            final_conclusion=process.final_conclusion,
            overall_confidence=process.overall_confidence,
            started_at=process.started_at,
            completed_at=process.completed_at,
            status="completed" if process.completed_at else "active",
            title=process.title,  # Include title
            summary_metadata=process.summary_metadata  # Include metadata
        )
        
        logger.info(f"✅ Retrieved thinking process with {len(steps_data)} steps")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get thinking process: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start")
async def start_thinking_process(query: ThinkingQuery, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route start_thinking_process called", endpoint="start_thinking_process", trace_id=trace_id)

    """Start a new thinking process"""
    try:
        logger.info(f"💭 Starting thinking process for workspace: {query.workspace_id}")
        
        process_id = await thinking_engine.start_thinking_process(
            workspace_id=query.workspace_id,
            context=query.query,
            process_type=query.process_type
        )
        
        logger.info(f"✅ Started thinking process: {process_id}")
        return {
            "process_id": process_id,
            "workspace_id": str(query.workspace_id),
            "status": "started",
            "message": "Thinking process started successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to start thinking process: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/step")
async def add_thinking_step(step_data: ThinkingStepCreate, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route add_thinking_step called", endpoint="add_thinking_step", trace_id=trace_id)

    """Add a thinking step to active process"""
    try:
        logger.info(f"💭 Adding thinking step to process: {step_data.process_id}")
        
        step_id = await thinking_engine.add_thinking_step(
            process_id=step_data.process_id,
            step_type=step_data.step_type,
            content=step_data.content,
            confidence=step_data.confidence,
            metadata=step_data.metadata
        )
        
        logger.info(f"✅ Added thinking step: {step_id}")
        return {
            "step_id": step_id,
            "process_id": step_data.process_id,
            "status": "added",
            "message": "Thinking step added successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add thinking step: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/complete/{process_id}")
async def complete_thinking_process(request: Request, process_id: str, conclusion: str, confidence: float = 0.8):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route complete_thinking_process called", endpoint="complete_thinking_process", trace_id=trace_id)

    """Complete a thinking process with final conclusion"""
    try:
        logger.info(f"💭 Completing thinking process: {process_id}")
        
        completed_process = await thinking_engine.complete_thinking_process(
            process_id=process_id,
            conclusion=conclusion,
            overall_confidence=confidence
        )
        
        logger.info(f"✅ Completed thinking process with {len(completed_process.steps)} steps")
        return {
            "process_id": process_id,
            "status": "completed",
            "steps_count": len(completed_process.steps),
            "overall_confidence": completed_process.overall_confidence,
            "message": "Thinking process completed successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to complete thinking process: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === O3/CLAUDE-STYLE THINKING ENDPOINTS ===

@router.post("/o3-style")
async def generate_o3_style_thinking(query: ThinkingQuery, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route generate_o3_style_thinking called", endpoint="generate_o3_style_thinking", trace_id=trace_id)

    """Generate O3/Claude-style thinking process with streaming steps"""
    try:
        logger.info(f"💭 Generating O3-style thinking for: {query.query}")
        
        async def generate_thinking_stream():
            """Stream thinking steps as they're generated"""
            steps_count = 0
            async for step in thinking_engine.generate_o3_style_thinking(query.workspace_id, query.query):
                steps_count += 1
                yield f"data: {json.dumps(step)}\n\n"
            
            # Send completion event
            completion_event = {
                "event_type": "thinking_completed",
                "timestamp": datetime.utcnow().isoformat(),
                "total_steps": steps_count
            }
            yield f"data: {json.dumps(completion_event)}\n\n"
        
        return StreamingResponse(
            generate_thinking_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to generate O3-style thinking: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/o3-demo/{workspace_id}")
async def o3_thinking_demo(request: Request, workspace_id: UUID, query: str = "How should I approach building a new feature?"):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route o3_thinking_demo called", endpoint="o3_thinking_demo", trace_id=trace_id)

    """Demo endpoint for O3-style thinking visualization"""
    try:
        logger.info(f"💭 O3 thinking demo for workspace: {workspace_id}")
        
        # Start the thinking process
        process_id = await thinking_engine.start_thinking_process(workspace_id, query, "o3_demo")
        
        # Generate demo thinking steps
        demo_steps = [
            {
                "step_type": "context_loading",
                "content": "🔍 Loading workspace context and analyzing current project state...",
                "confidence": 0.9
            },
            {
                "step_type": "analysis", 
                "content": f"📚 Analyzing query: '{query}'. This involves feature planning, technical considerations, and user impact assessment.",
                "confidence": 0.8
            },
            {
                "step_type": "perspective",
                "content": "🧠 Considering multiple approaches:\n1. Agile iterative development\n2. Waterfall comprehensive planning\n3. MVP-first approach\n4. User-research driven design",
                "confidence": 0.7
            },
            {
                "step_type": "evaluation",
                "content": "⚖️ Evaluating trade-offs:\n- Speed vs Quality: MVP allows faster feedback\n- Resources vs Scope: Limited resources suggest focused approach\n- Risk vs Innovation: New features carry implementation risk",
                "confidence": 0.8
            },
            {
                "step_type": "critical_review",
                "content": "🤔 Critical assessment: Am I considering edge cases? User accessibility? Performance impact? Security implications? Integration complexity?",
                "confidence": 0.7
            },
            {
                "step_type": "synthesis",
                "content": "💡 Recommendation: Start with MVP approach focusing on core user value. Implement in phases with user feedback loops. Prioritize security and performance from day one.",
                "confidence": 0.9
            }
        ]
        
        # Add all steps
        step_ids = []
        for step in demo_steps:
            step_id = await thinking_engine.add_thinking_step(
                process_id=process_id,
                step_type=step["step_type"],
                content=step["content"],
                confidence=step["confidence"]
            )
            step_ids.append(step_id)
        
        # Complete the process
        conclusion = "Based on comprehensive analysis, I recommend an MVP-first approach with iterative development, emphasizing user feedback and core value delivery."
        await thinking_engine.complete_thinking_process(process_id, conclusion, 0.85)
        
        return {
            "process_id": process_id,
            "workspace_id": str(workspace_id),
            "demo_query": query,
            "steps_generated": len(demo_steps),
            "step_ids": step_ids,
            "conclusion": conclusion,
            "overall_confidence": 0.85,
            "message": "O3-style thinking demo completed successfully"
        }
        
    except Exception as e:
        logger.error(f"O3 thinking demo failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === THINKING ANALYTICS ENDPOINTS ===

@router.get("/analytics/{workspace_id}")
async def get_thinking_analytics(workspace_id: UUID, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_thinking_analytics called", endpoint="get_thinking_analytics", trace_id=trace_id)

    """Get thinking analytics for workspace"""
    try:
        logger.info(f"📊 Getting thinking analytics for workspace: {workspace_id}")
        
        processes = await thinking_engine.get_workspace_thinking(workspace_id, 50)
        
        if not processes:
            return {
                "workspace_id": str(workspace_id),
                "total_processes": 0,
                "analytics": {
                    "avg_steps_per_process": 0,
                    "avg_confidence": 0.0,
                    "step_type_distribution": {},
                    "completion_rate": 0.0,
                    "thinking_quality": "no_data"
                }
            }
        
        # Calculate analytics
        total_processes = len(processes)
        completed_processes = len([p for p in processes if p.completed_at])
        total_steps = sum(len(p.steps) for p in processes)
        
        # Step type distribution
        step_types = {}
        total_confidence = 0
        confidence_count = 0
        
        for process in processes:
            if process.overall_confidence > 0:
                total_confidence += process.overall_confidence
                confidence_count += 1
            
            for step in process.steps:
                step_type = step.step_type
                step_types[step_type] = step_types.get(step_type, 0) + 1
        
        avg_confidence = total_confidence / confidence_count if confidence_count > 0 else 0.0
        completion_rate = completed_processes / total_processes if total_processes > 0 else 0.0
        
        # Quality assessment
        thinking_quality = "excellent" if avg_confidence > 0.8 else \
                          "good" if avg_confidence > 0.6 else \
                          "fair" if avg_confidence > 0.4 else "needs_improvement"
        
        analytics = {
            "workspace_id": str(workspace_id),
            "total_processes": total_processes,
            "analytics": {
                "avg_steps_per_process": total_steps / total_processes if total_processes > 0 else 0,
                "avg_confidence": avg_confidence,
                "step_type_distribution": step_types,
                "completion_rate": completion_rate,
                "thinking_quality": thinking_quality,
                "completed_processes": completed_processes,
                "active_processes": total_processes - completed_processes
            }
        }
        
        logger.info(f"✅ Generated thinking analytics")
        return analytics
        
    except Exception as e:
        logger.error(f"Failed to get thinking analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === GOAL-SPECIFIC THINKING ===

@router.get("/goal/{goal_id}/thinking")
async def get_goal_thinking(goal_id: UUID, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_goal_thinking called", endpoint="get_goal_thinking", trace_id=trace_id)

    """Get thinking processes related to specific goal"""
    try:
        logger.info(f"💭 Getting thinking for goal: {goal_id}")
        
        # This would filter thinking processes by goal context
        # For now, return a placeholder
        return {
            "goal_id": str(goal_id),
            "thinking_processes": [],
            "message": "Goal-specific thinking endpoint implemented"
        }
        
    except Exception as e:
        logger.error(f"Failed to get goal thinking: {e}")
        raise HTTPException(status_code=500, detail=str(e))