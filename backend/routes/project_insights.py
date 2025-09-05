from fastapi import Request, APIRouter, HTTPException, status
from typing import List, Dict, Any, Optional
from middleware.trace_middleware import get_trace_id, create_traced_logger, TracedDatabaseOperation
from uuid import UUID
import logging
import json  # NUOVO: Aggiunto import json
from datetime import datetime, timedelta
import os
from collections import Counter
from deliverable_system.unified_deliverable_engine import unified_deliverable_engine
from models import (
    ProjectDeliverables,
    ProjectOutput,
    DeliverableFeedback,
    ProjectDeliverableCard,
    Task,
    TaskStatus,
)
from ai_agents.director import DirectorAgent

from database import (
    get_workspace,
    list_agents,
    list_tasks,
    create_task,
)
from executor import task_executor
from deliverable_system.unified_deliverable_engine import unified_deliverable_engine
from deliverable_system.unified_deliverable_engine import unified_deliverable_engine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["project-insights"])

# Simple in-memory cache for deliverables
ENABLE_DELIVERABLE_CACHE = os.getenv("ENABLE_DELIVERABLE_CACHE", "true").lower() == "true"
DELIVERABLE_CACHE: Dict[str, Dict[str, Any]] = {}


@router.get("/{workspace_id}/insights", response_model=Dict[str, Any])
async def get_project_insights(workspace_id: UUID, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_project_insights called", endpoint="get_project_insights", trace_id=trace_id)

    """Get comprehensive project insights including progress, timing, and predictions"""
    try:
        # Get workspace details - handle gracefully if workspace doesn't exist yet
        workspace = await get_workspace(str(workspace_id))
        if not workspace:
            # Return empty insights instead of 404 for better UX
            logger.info(f"🔍 [Insights] Workspace {workspace_id} not found, returning empty insights")
            return {
                "workspace_id": str(workspace_id),
                "workspace_goal": "",
                "project_status": "not_started",
                "agents": [],
                "tasks": [],
                "activity": [],
                "progress": 0.0,
                "completion_prediction": "N/A - workspace not started",
                "generation_timestamp": datetime.now().isoformat()
            }
        
        # Get agents and tasks
        agents = await list_agents(str(workspace_id))
        tasks = await list_tasks(str(workspace_id))
        
        # Get execution history from task executor
        recent_activity = task_executor.get_recent_activity(str(workspace_id), 100)
        budget_info = task_executor.budget_tracker.get_workspace_total_cost(
            str(workspace_id), 
            [str(agent["id"]) for agent in agents]
        )
        
        # Calculate insights
        insights = await _calculate_project_insights(
            workspace, agents, tasks, recent_activity, budget_info
        )
        
        return insights
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project insights: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project insights: {str(e)}"
        )

@router.get("/{workspace_id}/major-milestones", response_model=List[Dict[str, Any]])
async def get_major_milestones(workspace_id: UUID, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_major_milestones called", endpoint="get_major_milestones", trace_id=trace_id)

    """Get major milestones and phases completed in the project"""
    try:
        tasks = await list_tasks(str(workspace_id))
        agents = await list_agents(str(workspace_id))
        
        # Get recent activity to identify major events
        recent_activity = task_executor.get_recent_activity(str(workspace_id), 50)
        
        milestones = _extract_major_milestones(tasks, agents, recent_activity)
        return milestones
        
    except Exception as e:
        logger.error(f"Error getting major milestones: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get major milestones: {str(e)}"
        )

async def _calculate_project_insights(
    workspace: Dict,
    agents: List[Dict],
    tasks: List[Dict],
    recent_activity: List[Dict],
    budget_info: Dict
) -> Dict[str, Any]:
    """Calculate comprehensive project insights"""
    
    # Task statistics
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t["status"] == "completed"])
    in_progress_tasks = len([t for t in tasks if t["status"] == "in_progress"])
    pending_tasks = len([t for t in tasks if t["status"] == "pending"])
    failed_tasks = len([t for t in tasks if t["status"] == "failed"])
    
    # Calculate progress percentage
    progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Time analysis
    workspace_created = datetime.fromisoformat(workspace["created_at"].replace('Z', '+00:00'))
    time_elapsed = datetime.now(workspace_created.tzinfo) - workspace_created
    time_elapsed_days = time_elapsed.days + (time_elapsed.seconds / 86400)
    
    # Calculate average task completion time
    completed_task_times = []
    for task in tasks:
        if task["status"] == "completed" and task.get("created_at") and task.get("updated_at"):
            created = datetime.fromisoformat(task["created_at"].replace('Z', '+00:00'))
            updated = datetime.fromisoformat(task["updated_at"].replace('Z', '+00:00'))
            duration = (updated - created).total_seconds() / 3600  # in hours
            completed_task_times.append(duration)
    
    avg_task_completion_hours = sum(completed_task_times) / len(completed_task_times) if completed_task_times else 24
    
    # Project phase detection
    current_phase = _detect_current_phase(tasks, recent_activity)
    
    # Prediction calculations
    if completed_tasks > 0 and pending_tasks > 0:
        estimated_completion_days = (pending_tasks * avg_task_completion_hours / 24) * 1.2  # Add 20% buffer
        estimated_completion_date = datetime.now() + timedelta(days=estimated_completion_days)
    else:
        estimated_completion_days = None
        estimated_completion_date = None
    
    # Agent activity summary
    agent_activity = _analyze_agent_activity(agents, recent_activity)
    
    # Budget efficiency
    cost_per_completed_task = budget_info["total_cost"] / completed_tasks if completed_tasks > 0 else 0
    
    # Project health score (0-100)
    health_score = _calculate_project_health_score(
        progress_percentage, 
        failed_tasks / total_tasks * 100 if total_tasks > 0 else 0,
        agent_activity,
        time_elapsed_days
    )
    
    # Recent major events
    major_events = _get_recent_major_events(recent_activity, 5)
    
    return {
        "overview": {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "pending_tasks": pending_tasks,
            "failed_tasks": failed_tasks,
            "progress_percentage": round(progress_percentage, 1),
            "health_score": round(health_score, 0)
        },
        "timing": {
            "time_elapsed_days": round(time_elapsed_days, 1),
            "avg_task_completion_hours": round(avg_task_completion_hours, 1),
            "estimated_completion_days": round(estimated_completion_days, 1) if estimated_completion_days else None,
            "estimated_completion_date": estimated_completion_date.isoformat() if estimated_completion_date else None
        },
        "current_state": {
            "phase": current_phase,
            "status": workspace.get("status", "active"),
            "active_agents": len([a for a in agents if a.get("status") == "active"]),
            "total_agents": len(agents)
        },
        "performance": {
            "cost_per_completed_task": round(cost_per_completed_task, 2),
            "total_cost": budget_info["total_cost"],
            "budget_utilization": budget_info.get("budget_percentage", 0),
            "agent_activity": agent_activity
        },
        "recent_highlights": major_events
    }

def _detect_current_phase(tasks: List[Dict], recent_activity: List[Dict]) -> str:
    """Detect the current phase of the project based on tasks and activity"""
    
    # Check for initialization keywords
    recent_task_names = [t.get("name", "").lower() for t in tasks[-5:]]
    recent_activity_content = [a.get("task_name", "").lower() for a in recent_activity[:10]]
    
    all_recent_text = " ".join(recent_task_names + recent_activity_content)
    
    if any(keyword in all_recent_text for keyword in ["initialization", "planning", "setup"]):
        return "Initialization & Planning"
    elif any(keyword in all_recent_text for keyword in ["analysis", "research", "investigation"]):
        return "Analysis & Research"
    elif any(keyword in all_recent_text for keyword in ["implementation", "development", "creation"]):
        return "Implementation"
    elif any(keyword in all_recent_text for keyword in ["testing", "validation", "review"]):
        return "Testing & Validation"
    elif any(keyword in all_recent_text for keyword in ["optimization", "refinement", "improvement"]):
        return "Optimization"
    elif any(keyword in all_recent_text for keyword in ["finalization", "deployment", "completion"]):
        return "Finalization"
    else:
        # Determine by task completion ratio
        completed_ratio = len([t for t in tasks if t["status"] == "completed"]) / len(tasks) if tasks else 0
        if completed_ratio < 0.2:
            return "Early Stage"
        elif completed_ratio < 0.5:
            return "Development Phase"
        elif completed_ratio < 0.8:
            return "Implementation Phase"
        else:
            return "Completion Phase"

def _analyze_agent_activity(agents: List[Dict], recent_activity: List[Dict]) -> Dict[str, Any]:
    """Analyze agent activity patterns"""
    
    agent_names = {agent["id"]: agent["name"] for agent in agents}
    
    # Count activities per agent
    agent_activity_count = Counter()
    agent_recent_activity = {}
    
    for activity in recent_activity[-20:]:  # Last 20 activities
        agent_id = activity.get("agent_id")
        if agent_id and agent_id in agent_names:
            agent_activity_count[agent_id] += 1
            if agent_id not in agent_recent_activity:
                agent_recent_activity[agent_id] = activity.get("timestamp")
    
    # Most active agent
    most_active_agent_id = agent_activity_count.most_common(1)[0][0] if agent_activity_count else None
    most_active_agent = agent_names.get(most_active_agent_id) if most_active_agent_id else None
    
    # Recently active agents
    recently_active = len(agent_activity_count)
    
    return {
        "most_active_agent": most_active_agent,
        "recently_active_agents": recently_active,
        "total_agents": len(agents),
        "activity_distribution": dict(agent_activity_count)
    }

def _calculate_project_health_score(
    progress_percentage: float,
    failure_rate: float,
    agent_activity: Dict,
    time_elapsed_days: float
) -> float:
    """Calculate an overall project health score (0-100)"""
    
    # Progress component (40% weight)
    progress_score = min(progress_percentage * 1.2, 100)  # Slight boost for progress
    
    # Failure rate component (20% weight) - inverted
    failure_score = max(0, 100 - failure_rate * 5)  # 5% failure = 75 points
    
    # Agent activity component (20% weight)
    active_ratio = agent_activity["recently_active_agents"] / agent_activity["total_agents"]
    activity_score = active_ratio * 100
    
    # Time efficiency component (20% weight)
    # Projects shouldn't take too long
    expected_duration = 30  # days
    if time_elapsed_days <= expected_duration:
        time_score = 100
    else:
        time_score = max(0, 100 - (time_elapsed_days - expected_duration) * 2)
    
    # Calculate weighted average
    health_score = (
        progress_score * 0.4 +
        failure_score * 0.2 +
        activity_score * 0.2 +
        time_score * 0.2
    )
    
    return max(0, min(100, health_score))

def _get_recent_major_events(recent_activity: List[Dict], limit: int) -> List[Dict[str, Any]]:
    """Extract recent major events from activity log"""
    
    major_event_types = [
        "task_completed", 
        "task_failed", 
        "initial_task_created",
        "handoff_requested"
    ]
    
    major_events = []
    for activity in recent_activity:
        if activity.get("event") in major_event_types:
            major_events.append({
                "timestamp": activity.get("timestamp"),
                "event": activity.get("event"),
                "description": _format_event_description(activity),
                "task_name": activity.get("task_name"),
                "agent_id": activity.get("agent_id")
            })
    
    return major_events[:limit]

def _format_event_description(activity: Dict) -> str:
    """Format activity into human-readable description"""
    event = activity.get("event", "")
    task_name = activity.get("task_name", "")
    
    if event == "task_completed":
        return f"Completed: {task_name}"
    elif event == "task_failed":
        return f"Failed: {task_name}"
    elif event == "initial_task_created":
        return f"Project started with: {task_name}"
    elif event == "handoff_requested":
        return f"Handoff requested for: {task_name}"
    else:
        return f"{event}: {task_name}"

def _extract_major_milestones(
    tasks: List[Dict], 
    agents: List[Dict], 
    recent_activity: List[Dict]
) -> List[Dict[str, Any]]:
    """Extract major milestones from project history"""
    
    milestones = []
    
    # Add initialization milestone
    initial_tasks = [t for t in tasks if "initialization" in t.get("name", "").lower()]
    if initial_tasks:
        earliest_task = min(initial_tasks, key=lambda x: x.get("created_at", ""))
        milestones.append({
            "title": "Project Initialization",
            "description": f"Project setup and initial planning",
            "date": earliest_task.get("created_at"),
            "status": "completed",
            "type": "initialization"
        })
    
    # Add phase completion milestones
    completed_tasks = [t for t in tasks if t["status"] == "completed"]
    task_count_by_phase = {}
    
    for task in completed_tasks:
        # Simple phase detection based on task names
        task_name = task.get("name", "").lower()
        if any(keyword in task_name for keyword in ["plan", "design", "architecture"]):
            phase = "Planning Phase"
        elif any(keyword in task_name for keyword in ["implement", "develop", "create"]):
            phase = "Implementation Phase"
        elif any(keyword in task_name for keyword in ["test", "validate", "verify"]):
            phase = "Testing Phase"
        else:
            phase = "Development Phase"
        
        task_count_by_phase[phase] = task_count_by_phase.get(phase, 0) + 1
    
    # Convert to milestones
    for phase, count in task_count_by_phase.items():
        if count >= 2:  # Only add phases with multiple completed tasks
            milestones.append({
                "title": f"{phase} Completed",
                "description": f"{count} tasks completed in this phase",
                "date": datetime.now().isoformat(),  # Approximate
                "status": "completed",
                "type": "phase",
                "task_count": count
            })
    
    # Sort by date
    milestones.sort(key=lambda x: x.get("date", ""))
    
    return milestones

@router.get("/{workspace_id}/deliverables", response_model=ProjectDeliverables)
async def get_project_deliverables(request: Request, workspace_id: UUID, goal_id: Optional[str] = None):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_project_deliverables called", endpoint="get_project_deliverables", trace_id=trace_id)

    """Get aggregated project deliverables including final aggregated deliverable - ENHANCED"""
    try:
        # Get workspace details - handle gracefully if workspace doesn't exist yet
        workspace = await get_workspace(str(workspace_id))
        if not workspace:
            # Return empty deliverables instead of 404 for better UX
            logger.info(f"🔍 [Deliverables] Workspace {workspace_id} not found, returning empty deliverables")
            return ProjectDeliverables(
                workspace_id=str(workspace_id),
                workspace_goal="",
                outputs=[],
                key_outputs=[],
                final_recommendations=[],
                next_steps=[],
                completion_status="not_started",
                total_tasks=0,
                completed_tasks=0,
                summary="No deliverables available yet - workspace not started",
                aggregated_result="",
                generation_timestamp=datetime.now().isoformat(),
                generated_at=datetime.now().isoformat()
            )
        
        # Get all tasks
        tasks = await list_tasks(str(workspace_id))
        completed_tasks = [t for t in tasks if t.get("status") == "completed"]

        # Cache check based on latest task update and content hash
        last_updated = _get_latest_update_timestamp(tasks)
        content_hash = _calculate_content_hash(completed_tasks)
        cache_entry = DELIVERABLE_CACHE.get(str(workspace_id)) if ENABLE_DELIVERABLE_CACHE else None
        
        if (cache_entry and 
            cache_entry.get("last_updated") == last_updated and 
            cache_entry.get("content_hash") == content_hash):
            logger.info(f"📦 Using cached deliverable for {workspace_id} (content unchanged)")
            return cache_entry["data"]
        
        # Get agents info for names/roles
        agents = await list_agents(str(workspace_id))
        agent_map = {a["id"]: a for a in agents}
        
        # Extract outputs from completed tasks - FILTER FOR USER-FACING DELIVERABLES
        key_outputs = []
        for task in completed_tasks:
            result = task.get("result", {}) or {}
            context_data = task.get("context_data", {}) or {}
            output_text = result.get("summary", "")
            task_name = task.get("name", "")
            
            # Skip system/coordination tasks that are not user-facing deliverables
            if _is_system_task(task_name, context_data):
                continue
                
            if output_text and len(output_text.strip()) > 10:  # Skip trivial outputs
                agent_info = agent_map.get(task.get("agent_id"), {})
                
                # Classify output type
                output_type = _classify_output_type(task.get("name", ""), output_text)
                
                # Create user-friendly task name
                user_friendly_name = _get_user_friendly_task_name(task_name, context_data)
                
                # Extract structured content from detailed_results_json
                structured_content = None
                visual_summary = None
                key_insights = []
                metrics = {}
                
                if result.get("detailed_results_json"):
                    try:
                        detailed_data = json.loads(result["detailed_results_json"]) if isinstance(result["detailed_results_json"], str) else result["detailed_results_json"]
                        
                        # Check if HTML is already rendered (avoid re-processing)
                        if isinstance(detailed_data, dict) and detailed_data.get("rendered_html"):
                            # HTML already exists, use it directly
                            logger.debug(f"📦 Using pre-rendered HTML for task {task.get('id', 'unknown')}")
                            processed = {
                                "has_structured_content": bool(detailed_data.get("structured_content")),
                                "has_markup": True,
                                "rendered_html": detailed_data["rendered_html"],
                                "visual_summary": detailed_data.get("visual_summary", ""),
                                "actionable_insights": detailed_data.get("actionable_insights", [])
                            }
                        else:
                            # Process with markup processor (fallback for legacy content)
                            logger.debug(f"🔄 Processing markup for task {task.get('id', 'unknown')}")
                            processed = markup_processor.process_deliverable_content(detailed_data)
                        
                        if processed.get("has_structured_content") or processed.get("has_markup"):
                            # Use pre-existing visual summary if available
                            if processed.get("visual_summary"):
                                visual_summary = processed["visual_summary"]
                            else:
                                # Create visual summary from processed content (legacy fallback)
                                visual_parts = []
                                
                                # Add tables summary
                                if processed.get("tables"):
                                    for table in processed["tables"][:2]:  # First 2 tables
                                        visual_parts.append(f"📊 {table['display_name']}: {table['row_count']} rows")
                                
                                # Add cards summary  
                                if processed.get("cards"):
                                    for card in processed["cards"][:2]:  # First 2 cards
                                        if card['fields'].get('title'):
                                            visual_parts.append(f"{card['icon']} {card['fields']['title']}")
                                
                                # Add metrics summary
                                if processed.get("metrics"):
                                    for metric in processed["metrics"][:2]:  # First 2 metrics
                                        visual_parts.append(f"📈 {metric['display_name']}: {metric.get('value', 'N/A')} {metric.get('unit', '')}")
                                
                                if visual_parts:
                                    visual_summary = "\n".join(visual_parts)
                            
                            # Store processed content for frontend
                            structured_content = processed
                        
                        # Extract key insights from detailed data
                        if isinstance(detailed_data, dict):
                            # First check if pre-rendered insights are available
                            if detailed_data.get("actionable_insights"):
                                key_insights = detailed_data["actionable_insights"][:3]  # Limit to 3
                            else:
                                # Fallback to legacy insight extraction
                                insights_fields = ["key_insights", "key_findings", "insights", "recommendations", "key_points"]
                                for field in insights_fields:
                                    if field in detailed_data and isinstance(detailed_data[field], list):
                                        key_insights.extend(detailed_data[field][:3])  # Limit to 3 per field
                                        break
                            
                            # Extract metrics
                            metrics_fields = ["metrics", "performance_metrics", "project_metrics", "kpis"]
                            for field in metrics_fields:
                                if field in detailed_data and isinstance(detailed_data[field], dict):
                                    metrics = detailed_data[field]
                                    break
                    
                    except Exception as e:
                        logger.debug(f"Could not parse detailed results: {e}")
                
                # Use visual summary for display if available, otherwise use original output
                display_output = visual_summary if visual_summary else output_text
                if len(display_output) > 1000:
                    display_output = display_output[:1000] + "..."
                
                # Create the output with enhanced data
                key_outputs.append(ProjectOutput(
                    task_id=task["id"],
                    task_name=user_friendly_name,
                    output=display_output,
                    agent_name=agent_info.get("name", "Unknown Agent"),
                    agent_role=agent_info.get("role", "Unknown Role"),
                    created_at=datetime.fromisoformat(task.get("updated_at", task.get("created_at", datetime.now().isoformat())).replace('Z', '+00:00')),
                    type=output_type,
                    execution_time_seconds=result.get("execution_time_seconds") or context_data.get("execution_time_seconds"),
                    cost_estimated=result.get("cost_estimated") or context_data.get("cost_estimated"),
                    tokens_used=result.get("tokens_used") or context_data.get("tokens_used"),
                    model_used=result.get("model_used") or context_data.get("model_used"),
                    rationale=result.get("rationale") or context_data.get("rationale") or result.get("phase_rationale") or context_data.get("phase_rationale"),
                    # Enhanced fields for rich content
                    key_insights=key_insights[:5],  # Limit total to 5
                    metrics=metrics,
                    visual_summary=visual_summary,
                    structured_content=structured_content
                ))
        
        # Sort outputs by importance (most important deliverables first)
        key_outputs.sort(key=lambda x: _get_deliverable_importance_score(x.task_name, x.type), reverse=True)
        
        # ENHANCED: Find best final deliverable (prioritize user-facing over AI-generated)
        final_deliverable_task = None
        best_deliverable_score = 0
        
        for task in tasks:  # Cerca in TUTTI i task, non solo completed
            context_data = task.get("context_data", {}) or {}
            if (context_data.get("is_final_deliverable") or 
                context_data.get("deliverable_aggregation") or
                context_data.get("triggers_project_completion")):
                
                # Score deliverables - prefer user-facing over system-generated
                score = 1
                task_name = task.get("name", "")
                
                # BOOST for AI-generated deliverables - these are what users need!
                if "🤖 AI INTELLIGENT DELIVERABLE" in task_name:
                    score += 1.0
                
                # Boost for completed tasks
                if task.get("status") == "completed":
                    score += 1
                
                # Boost for non-system tasks
                if not _is_system_task(task_name, context_data):
                    score += 1
                
                logger.info(f"🎯 EVALUATING deliverable task {task.get('id')} with score: {score}")
                
                if score > best_deliverable_score:
                    best_deliverable_score = score
                    final_deliverable_task = task
                    logger.info(f"🎯 NEW BEST final deliverable task {task.get('id')} with status: {task.get('status')}")
        
        # ENHANCED: Se esiste un deliverable finale, processalo con logica robusta
        if final_deliverable_task:
            task_status = final_deliverable_task.get("status", "unknown")
            logger.info(f"🎯 PROCESSING final deliverable task: {final_deliverable_task['id']} (status: {task_status})")
            result = final_deliverable_task.get("result", {}) or {}
            fd_context = final_deliverable_task.get("context_data", {}) or {}
            
            # SPECIAL HANDLING: Se il task è failed, prova comunque a estrarre contenuto utile
            if task_status == "failed":
                logger.warning(f"🎯 WARNING: Final deliverable task {final_deliverable_task['id']} has FAILED status - attempting content recovery")
            
            # ENHANCED: Multiple fallback strategies for getting executive summary
            executive_summary = ""
            detailed_json_data = {}
            
            # Strategy 1: Try detailed_results_json parsing
            detailed_json = result.get("detailed_results_json")
            if detailed_json and isinstance(detailed_json, str) and detailed_json.strip():
                try:
                    detailed_json_data = json.loads(detailed_json)
                    executive_summary = detailed_json_data.get("executive_summary", "")
                    logger.info(f"🎯 SUCCESS: Parsed detailed_results_json for executive summary")
                except json.JSONDecodeError as e:
                    logger.warning(f"🎯 WARNING: Failed to parse detailed_results_json: {e}")
                    # Strategy 2: Try to extract partial data from malformed JSON
                    try:
                        # Look for executive_summary in the raw string
                        import re
                        exec_match = re.search(r'"executive_summary":\s*"([^"]*)"', detailed_json)
                        if exec_match:
                            executive_summary = exec_match.group(1)
                            logger.info(f"🎯 RECOVERY: Extracted executive_summary from malformed JSON")
                    except Exception as e2:
                        logger.warning(f"🎯 RECOVERY FAILED: {e2}")
            
            # Strategy 3: Fallback to task summary if no executive_summary found
            if not executive_summary:
                executive_summary = result.get("summary", "")
                if executive_summary:
                    logger.info(f"🎯 FALLBACK: Using task summary as executive summary")
            
            # Strategy 4: Generate basic summary if still empty
            if not executive_summary:
                workspace_goal = workspace.get("goal", "")
                if task_status == "failed":
                    executive_summary = f"Final deliverable attempted but failed during generation. Project goal: {workspace_goal}. Check task logs for details."
                    logger.warning(f"🎯 FAILED TASK FALLBACK: Generated recovery executive summary")
                else:
                    executive_summary = f"Project deliverable completed for: {workspace_goal}"
                    logger.warning(f"🎯 EMERGENCY FALLBACK: Generated basic executive summary")
            
            # ENHANCED: Create comprehensive final output with robust data
            try:
                # Customize display based on task status
                task_name_prefix = "🎯 " if task_status != "failed" else "⚠️ 🎯 "
                agent_role_display = "Final Deliverable" if task_status != "failed" else "Final Deliverable (Failed)"
                
                final_output = ProjectOutput(
                    task_id=final_deliverable_task["id"],
                    task_name=task_name_prefix + final_deliverable_task.get("name", "Final Deliverable"),
                    output=executive_summary,  # This will now always have content
                    agent_name=agent_map.get(final_deliverable_task.get("agent_id"), {}).get("name", "Project Manager"),
                    agent_role=agent_role_display,
                    created_at=datetime.fromisoformat(final_deliverable_task.get("updated_at", datetime.now().isoformat()).replace('Z', '+00:00')),
                    type="final_deliverable",
                    # ENHANCED: Robust field extraction with fallbacks
                    title=detailed_json_data.get("deliverable_type", 
                        "Final Project Deliverable (Recovery Mode)" if task_status == "failed" 
                        else "Final Project Deliverable").replace("_", " ").title(),
                    description=executive_summary,  # Use the robust executive_summary
                    key_insights=detailed_json_data.get("key_findings", detailed_json_data.get("key_insights", [])),
                    metrics=detailed_json_data.get("project_metrics", detailed_json_data.get("project_success_metrics", {})),
                    category="final_deliverable",
                    execution_time_seconds=result.get("execution_time_seconds") or fd_context.get("execution_time_seconds"),
                    cost_estimated=result.get("cost_estimated") or fd_context.get("cost_estimated"),
                    tokens_used=result.get("tokens_used") or fd_context.get("tokens_used"),
                    model_used=result.get("model_used") or fd_context.get("model_used"),
                    rationale=result.get("rationale") or fd_context.get("rationale") or result.get("phase_rationale") or fd_context.get("phase_rationale")
                )
                
                # Add the final deliverable at the beginning of the list
                key_outputs.insert(0, final_output)
                if task_status == "failed":
                    logger.info(f"🎯 RECOVERY SUCCESS: Added FAILED final deliverable to outputs with recovery data")
                else:
                    logger.info(f"🎯 SUCCESS: Added final deliverable to outputs with robust data")
                
            except Exception as e:
                logger.error(f"🎯 ERROR: Failed to create final ProjectOutput: {e}")
                # Don't fail the whole request, just continue without final deliverable
        
        # ENHANCED: Generate insight cards with error handling
        insight_cards = []
        try:
            if key_outputs:
                insight_cards = await _generate_deliverable_insights([
                    {
                        "task_id": output.task_id,
                        "task_name": output.task_name,
                        "output": output.output,
                        "agent_name": output.agent_name,
                        "agent_role": output.agent_role,
                        "created_at": output.created_at.isoformat(),
                        "type": output.type
                    }
                    for output in key_outputs
                ])
        except Exception as e:
            logger.error(f"🎯 ERROR: Failed to generate insight cards: {e}")
            insight_cards = []  # Continue without insight cards
        
        # Generate AI summary with fallback
        summary = ""
        try:
            if key_outputs:
                summary = await _generate_project_summary(workspace, key_outputs)
            else:
                summary = f"Project completed for workspace: {workspace.get('name', 'Unknown')}"
        except Exception as e:
            logger.error(f"🎯 ERROR: Failed to generate AI summary: {e}")
            summary = f"Project deliverables generated for: {workspace.get('goal', 'project objectives')}"
        
        # Extract recommendations and next steps with error handling
        recommendations = []
        next_steps = []
        try:
            recommendations = _extract_recommendations(key_outputs)
            next_steps = _extract_next_steps(key_outputs)
        except Exception as e:
            logger.error(f"🎯 ERROR: Failed to extract recommendations/next_steps: {e}")
        
        # Determine completion status
        completion_status = _determine_completion_status(tasks, key_outputs)
        
        logger.info(f"🎯 DELIVERABLE RESPONSE: {len(key_outputs)} outputs, "
                   f"summary length: {len(summary)}, cards: {len(insight_cards)}")

        response = ProjectDeliverables(
            workspace_id=str(workspace_id),
            summary=summary,
            key_outputs=key_outputs,
            insight_cards=insight_cards,
            final_recommendations=recommendations,
            next_steps=next_steps,
            completion_status=completion_status,
            total_tasks=len(tasks),
            completed_tasks=len(completed_tasks),
            generated_at=datetime.now()
        )

        if ENABLE_DELIVERABLE_CACHE:
            DELIVERABLE_CACHE[str(workspace_id)] = {
                "last_updated": last_updated,
                "content_hash": content_hash,
                "data": response,
            }
            logger.debug(f"📦 Cached deliverable for {workspace_id} with hash {content_hash[:8]}")

        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🎯 CRITICAL ERROR in get_project_deliverables: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project deliverables: {str(e)}"
        )

@router.get("/{workspace_id}/task/{task_id}/enhanced-result", response_model=Dict[str, Any])
async def get_enhanced_task_result(workspace_id: UUID, task_id: UUID, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_enhanced_task_result called", endpoint="get_enhanced_task_result", trace_id=trace_id)

    """Get enhanced task result with processed structured content"""
    try:
        # Get task details
        task = await get_task(str(task_id))
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if task.get("workspace_id") != str(workspace_id):
            raise HTTPException(status_code=403, detail="Task does not belong to workspace")
        
        result = task.get("result", {})
        if not result:
            return {
                "task_id": str(task_id),
                "task_name": task.get("name", ""),
                "status": task.get("status", ""),
                "enhanced_content": None,
                "has_structured_content": False
            }
        
        # Extract and process detailed results
        enhanced_content = None
        structured_elements = {
            "tables": [],
            "cards": [],
            "timelines": [],
            "metrics": [],
            "raw_data": {}
        }
        
        if result.get("detailed_results_json"):
            try:
                detailed_data = json.loads(result["detailed_results_json"]) if isinstance(result["detailed_results_json"], str) else result["detailed_results_json"]
                
                # Process with markup processor
                processed = markup_processor.process_deliverable_content(detailed_data)
                
                if processed.get("has_structured_content") or processed.get("has_markup"):
                    # Extract structured elements
                    if processed.get("combined_elements"):
                        structured_elements = processed["combined_elements"]
                    else:
                        # Fallback to individual elements
                        structured_elements["tables"] = processed.get("tables", [])
                        structured_elements["cards"] = processed.get("cards", [])
                        structured_elements["timelines"] = processed.get("timelines", [])
                        structured_elements["metrics"] = processed.get("metrics", [])
                    
                    enhanced_content = processed
                
                # Store raw data for reference
                structured_elements["raw_data"] = detailed_data
                
            except Exception as e:
                logger.error(f"Error processing task result: {e}")
        
        # Get agent info
        agent = None
        if task.get("agent_id"):
            agent = await get_agent(task["agent_id"])
        
        return {
            "task_id": str(task_id),
            "task_name": task.get("name", ""),
            "status": task.get("status", ""),
            "agent": {
                "name": agent.get("name", "Unknown") if agent else "Unknown",
                "role": agent.get("role", "Unknown") if agent else "Unknown"
            },
            "summary": result.get("summary", ""),
            "enhanced_content": enhanced_content,
            "structured_elements": structured_elements,
            "has_structured_content": bool(enhanced_content and (enhanced_content.get("has_structured_content") or enhanced_content.get("has_markup"))),
            "execution_metadata": {
                "execution_time_seconds": result.get("execution_time_seconds"),
                "cost_estimated": result.get("cost_estimated"),
                "tokens_used": result.get("tokens_used"),
                "model_used": result.get("model_used")
            },
            "created_at": task.get("created_at"),
            "updated_at": task.get("updated_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting enhanced task result: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get enhanced task result: {str(e)}"
        )

@router.post("/{workspace_id}/deliverables/feedback", status_code=status.HTTP_200_OK)
async def submit_deliverable_feedback(
    workspace_id: UUID,
    feedback: DeliverableFeedback
):
    """Submit feedback on project deliverables"""
    try:
        # Create a new task for handling the feedback
        agents = await list_agents(str(workspace_id))
        
        # Find a coordinator/manager to handle feedback
        coordinator = None
        for agent in agents:
            if any(role in agent.get("role", "").lower() for role in ["coordinator", "manager", "lead"]):
                coordinator = agent
                break
        
        if not coordinator and agents:
            coordinator = agents[0]  # Fallback to first agent
        
        if coordinator:
            task_name = f"User Feedback: {feedback.feedback_type.title()}"
            task_description = f"""
USER FEEDBACK ON PROJECT DELIVERABLES
Type: {feedback.feedback_type.upper()}
Priority: {feedback.priority.upper()}

Message:
{feedback.message}

{"Specific tasks mentioned: " + ", ".join(feedback.specific_tasks) if feedback.specific_tasks else ""}

Please review this feedback and take appropriate action:
1. If approved, mark the project as completed
2. If changes requested, create specific tasks to address the feedback
3. If general feedback, incorporate into project improvements
"""
            
            # Create the feedback task
            await create_task(
                workspace_id=str(workspace_id),
                agent_id=coordinator["id"],
                name=task_name,
                description=task_description,
                status=TaskStatus.PENDING.value,
                priority="high",  # Feedback è sempre alta priorità

                # TRACKING AUTOMATICO
                creation_type="user_feedback",  # Creato da feedback utente

                # CONTEXT DATA SPECIFICO
                context_data={
                    "feedback_type": feedback.feedback_type,
                    "feedback_priority": feedback.priority,
                    "user_feedback": True,
                    "feedback_timestamp": datetime.now().isoformat(),
                    "specific_tasks_mentioned": feedback.specific_tasks or [],
                    "original_feedback_message": feedback.message[:500]  # Primi 500 caratteri
                }
            )
        
        return {
            "success": True,
            "message": "Feedback received and task created for handling",
            "feedback_type": feedback.feedback_type
        }
        
    except Exception as e:
        logger.error(f"Error submitting deliverable feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )

# NEW: Endpoint to manually trigger deliverable asset analysis
@router.post("/{workspace_id}/trigger-asset-analysis", status_code=status.HTTP_200_OK)
async def trigger_asset_analysis(workspace_id: UUID, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route trigger_asset_analysis called", endpoint="trigger_asset_analysis", trace_id=trace_id)

    """Run the deliverable requirements analyzer and return a summary"""
    try:
        analyzer = DeliverableRequirementsAnalyzer()
        analysis = await analyzer.analyze_deliverable_requirements(
            str(workspace_id), force_refresh=True
        )

        return {
            "success": True,
            "message": "Asset requirements analysis completed",
            "workspace_id": str(workspace_id),
            "analysis_results": {
                "deliverable_category": analysis.deliverable_category,
                "assets_needed": len(analysis.primary_assets_needed),
                "asset_types": [a.asset_type for a in analysis.primary_assets_needed],
            },
            "triggered_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error triggering asset analysis for {workspace_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger asset analysis: {str(e)}",
        )

@router.get("/{workspace_id}/asset-insights", response_model=Dict[str, Any])
async def get_asset_insights(workspace_id: UUID, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_asset_insights called", endpoint="get_asset_insights", trace_id=trace_id)

    """Return insight data about actionable assets for this workspace."""
    try:
        analyzer = DeliverableRequirementsAnalyzer()
        schemas_generator = AssetSchemaGenerator()

        requirements = await analyzer.analyze_deliverable_requirements(str(workspace_id))
        schemas = await schemas_generator.generate_asset_schemas(requirements)

        tasks = await list_tasks(str(workspace_id))

        asset_tasks = []
        produced_assets = set()
        for t in tasks:
            ctx = t.get("context_data", {}) or {}
            if isinstance(ctx, dict) and (
                ctx.get("asset_production")
                or ctx.get("asset_oriented_task")
                or "PRODUCE ASSET:" in t.get("name", "")
            ):
                asset_type = ctx.get("asset_type") or ctx.get("detected_asset_type")
                produced_assets.add(asset_type)
                asset_tasks.append(
                    {
                        "task_id": t.get("id"),
                        "name": t.get("name"),
                        "status": t.get("status"),
                        "asset_type": asset_type,
                        "agent_role": t.get("agent_role"),
                    }
                )

        required_types = [a.asset_type for a in requirements.primary_assets_needed]
        covered_assets = [a for a in required_types if a in produced_assets]
        missing_assets = [a for a in required_types if a not in produced_assets]

        insights = {
            "workspace_id": str(workspace_id),
            "deliverable_category": requirements.deliverable_category,
            "requirements_analysis": {
                "total_assets_needed": len(required_types),
                "required_asset_types": required_types,
                "asset_coverage_rate": round(len(covered_assets) / len(required_types) * 100, 1)
                if required_types
                else 0,
                "covered_assets": covered_assets,
                "missing_assets": missing_assets,
            },
            "asset_schemas_available": {
                name: {
                    "automation_ready": schema.automation_ready,
                    "validation_rules_count": len(schema.validation_rules),
                    "main_fields": list(schema.schema_definition.keys())[:3],
                }
                for name, schema in schemas.items()
            },
            "current_asset_tasks": asset_tasks,
            "recommendations": [f"Create {a} production task" for a in missing_assets],
        }

        return insights

    except Exception as e:
        logger.error(f"Error generating asset insights for {workspace_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get asset insights: {str(e)}",
        )

# New endpoint: return full task record for a specific output
@router.get("/{workspace_id}/output/{task_id}", response_model=Task)
async def get_output_detail(workspace_id: UUID, task_id: UUID, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_output_detail called", endpoint="get_output_detail", trace_id=trace_id)

    """Fetch a single task from the workspace and return its details."""
    try:
        tasks = await list_tasks(str(workspace_id))
        for task in tasks:
            if str(task.get("id")) == str(task_id):
                return task
        raise HTTPException(status_code=404, detail="Task not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving output detail for {task_id} in {workspace_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get output detail: {str(e)}",
        )

@router.get("/{workspace_id}/task/{task_id}/enhanced-result")
async def get_enhanced_task_result(workspace_id: UUID, task_id: UUID, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_enhanced_task_result called", endpoint="get_enhanced_task_result", trace_id=trace_id)

    """Get enhanced, processed task result with rich markup content"""
    try:
        tasks = await list_tasks(str(workspace_id))
        task = None
        for t in tasks:
            if str(t.get("id")) == str(task_id):
                task = t
                break
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        result = task.get("result", {}) or {}
        
        # Process detailed results if available
        enhanced_result = {
            "task_id": str(task_id),
            "task_name": task.get("name", ""),
            "summary": result.get("summary", ""),
            "has_rich_content": False,
            "structured_content": None,
            "visual_summary": None,
            "key_insights": [],
            "metrics": {}
        }
        
        if result.get("detailed_results_json"):
            try:
                detailed_data = json.loads(result["detailed_results_json"]) if isinstance(result["detailed_results_json"], str) else result["detailed_results_json"]
                
                # Process with markup processor
                processed = markup_processor.process_deliverable_content(detailed_data)
                
                if processed.get("has_structured_content") or processed.get("has_markup"):
                    enhanced_result["has_rich_content"] = True
                    enhanced_result["structured_content"] = processed
                    
                    # Create visual summary
                    visual_parts = []
                    if processed.get("tables"):
                        for table in processed["tables"]:
                            visual_parts.append(f"📊 {table['display_name']}: {table['row_count']} rows")
                    
                    if processed.get("cards"):
                        for card in processed["cards"]:
                            if card['fields'].get('title'):
                                visual_parts.append(f"{card['icon']} {card['fields']['title']}")
                    
                    if visual_parts:
                        enhanced_result["visual_summary"] = "\n".join(visual_parts)
                
                # Extract insights and metrics
                if isinstance(detailed_data, dict):
                    insights_fields = ["key_insights", "key_findings", "insights", "recommendations"]
                    for field in insights_fields:
                        if field in detailed_data and isinstance(detailed_data[field], list):
                            enhanced_result["key_insights"] = detailed_data[field][:5]
                            break
                    
                    metrics_fields = ["metrics", "performance_metrics", "project_metrics"]
                    for field in metrics_fields:
                        if field in detailed_data and isinstance(detailed_data[field], dict):
                            enhanced_result["metrics"] = detailed_data[field]
                            break
                            
            except Exception as e:
                logger.debug(f"Could not process enhanced result for task {task_id}: {e}")
        
        return enhanced_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting enhanced task result: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get enhanced task result: {str(e)}"
        )

# Helper functions
def _is_system_task(task_name: str, context_data: Dict) -> bool:
    """Filter out system/coordination tasks that shouldn't be shown to users"""
    
    # Skip system task patterns by name
    system_name_patterns = [
        "📋 IMPLEMENTATION:",
        "🚨 ENHANCE:",
        "🚨 URGENT Asset Quality Enhancement:",
        "🤖 AI INTELLIGENT DELIVERABLE:",
        "📋 FINALIZATION:",
        "📋 ANALYSIS:",
        "Project Setup & Strategic Planning",
        "PHASE PLANNING",
        "Asset Quality Enhancement",
        "Enhancement Coordination"
    ]
    
    for pattern in system_name_patterns:
        if pattern in task_name:
            return True
    
    # Skip system task types by context
    if isinstance(context_data, dict):
        creation_type = context_data.get("creation_type", "")
        system_creation_types = [
            "phase_transition",
            "ai_quality_enhancement_coordination", 
            "ai_asset_enhancement_specialist",
            "intelligent_ai_deliverable",
            "enhancement_coordination"
        ]
        
        if creation_type in system_creation_types:
            return True
            
        # Skip only PM coordination/planning tasks, NOT final deliverables
        if (context_data.get("planning_task_marker") or 
            context_data.get("pm_coordination_task") or
            context_data.get("is_implementation_planning")):
            return True
            
        # NEVER skip final deliverables - these are what users need!
        if context_data.get("is_final_deliverable"):
            return False
    
    return False

def _get_user_friendly_task_name(task_name: str, context_data: Dict) -> str:
    """Convert technical task names to user-friendly names"""
    
    # Mapping for common patterns
    friendly_name_mappings = {
        "Design Campaign Automation Workflow": "🚀 Campaign Automation Strategy",
        "Create Editorial Calendar Template": "📅 Content Calendar Template", 
        "Develop Content Strategy Framework": "📝 Content Strategy Framework",
        "Create Editorial Calendar for Instagram Posts and Reels": "📱 3-Month Instagram Content Plan",
        "Develop Initial Instagram Content Strategy Framework": "🎯 Instagram Growth Strategy",
        "Conduct Competitor and Audience Analysis for Instagram Growth": "🔍 Market & Audience Analysis",
        "Enhance 3-month Editorial Calendar Asset": "📅 Enhanced Content Calendar"
    }
    
    # Check for direct mapping
    if task_name in friendly_name_mappings:
        return friendly_name_mappings[task_name]
    
    # Remove technical prefixes but keep meaningful parts
    clean_name = task_name
    prefixes_to_remove = ["📋 IMPLEMENTATION:", "📋 ANALYSIS:", "📋 FINALIZATION:"]
    for prefix in prefixes_to_remove:
        if clean_name.startswith(prefix):
            clean_name = clean_name.replace(prefix, "").strip()
    
    # Add appropriate emoji based on content type
    if "calendar" in clean_name.lower():
        return f"📅 {clean_name}"
    elif "strategy" in clean_name.lower():
        return f"🎯 {clean_name}"
    elif "analysis" in clean_name.lower():
        return f"🔍 {clean_name}"
    elif "content" in clean_name.lower():
        return f"📝 {clean_name}"
    elif "campaign" in clean_name.lower():
        return f"🚀 {clean_name}"
    else:
        return clean_name

def _get_deliverable_importance_score(task_name: str, output_type: str) -> int:
    """Score deliverables by importance for user-facing ordering"""
    score = 10  # Base score
    
    # High priority deliverables
    high_priority_patterns = [
        "content plan", "editorial calendar", "instagram", "strategy", "framework"
    ]
    
    medium_priority_patterns = [
        "analysis", "research", "template", "workflow"
    ]
    
    task_lower = task_name.lower()
    
    # Boost for high priority content
    for pattern in high_priority_patterns:
        if pattern in task_lower:
            score += 20
            break
    
    # Medium boost for medium priority
    for pattern in medium_priority_patterns:
        if pattern in task_lower:
            score += 10
            break
    
    # Boost by output type
    type_scores = {
        "final_deliverable": 50,
        "document": 15,
        "recommendation": 12,
        "analysis": 8,
        "general": 5
    }
    
    score += type_scores.get(output_type, 0)
    
    # Extra boost for calendar/content related deliverables
    if any(keyword in task_lower for keyword in ["calendar", "content", "posts", "reels"]):
        score += 25
    
    return score

def _classify_output_type(task_name: str, output: str) -> str:
    """Classify the type of output based on task name and content"""
    task_lower = task_name.lower()
    output_lower = output.lower()
    
    if any(keyword in task_lower for keyword in ["analysis", "analyze", "research", "study"]):
        return "analysis"
    elif any(keyword in task_lower for keyword in ["recommend", "suggest", "strategy", "plan"]):
        return "recommendation"
    elif any(keyword in task_lower for keyword in ["document", "report", "write", "create"]):
        return "document"
    elif any(keyword in output_lower for keyword in ["recommend", "suggest", "should", "next steps"]):
        return "recommendation"
    else:
        return "general"

async def _generate_project_summary(workspace: Dict, outputs: List[ProjectOutput]) -> str:
    """Generate AI summary of project deliverables"""
    try:
        director = DirectorAgent()
        
        # Create a simplified agent for summarization
        from agents import Agent as OpenAIAgent
        
        summarizer = OpenAIAgent(
            name="ProjectSummarizer",
            instructions="""
            You are an executive assistant summarizing project deliverables.
            Create a concise, professional summary of what was accomplished.
            Focus on key outcomes, deliverables, and overall project success.
            """,
            model="gpt-4o-mini"
        )
        
        # Prepare context
        context = f"""
        Project: {workspace.get('name', 'Unknown')}
        Goal: {workspace.get('goal', 'Not specified')}
        
        Deliverables completed:
        """
        
        for output in outputs[:10]:  # Limit to avoid token limits
            context += f"\n- {output.task_name} (by {output.agent_name}): {output.output[:200]}..."
        
        from agents import Runner
        result = await Runner.run(
            summarizer,
            f"Summarize these project deliverables:\n\n{context}",
            max_turns=1
        )
        
        return result.final_output if isinstance(result.final_output, str) else str(result.final_output)
        
    except Exception as e:
        logger.error(f"Error generating AI summary: {e}")
        # Fallback summary
        return f"Project completed {len(outputs)} deliverables including {', '.join(set(o.type for o in outputs))}."

def _extract_recommendations(outputs: List[ProjectOutput]) -> List[str]:
    """Extract recommendations from outputs"""
    recommendations = []
    
    for output in outputs:
        if output.type == "recommendation":
            # Extract bullet points or numbered lists from the output
            lines = output.output.split('\n')
            for line in lines:
                line = line.strip()
                if (line.startswith('-') or line.startswith('•') or 
                    any(line.startswith(f"{i}.") for i in range(1, 10)) or
                    "recommend" in line.lower() or "suggest" in line.lower()):
                    clean_line = line.lstrip('-•0123456789. ').strip()
                    if len(clean_line) > 10:
                        recommendations.append(clean_line)
    
    # Deduplicate and limit
    unique_recommendations = list(dict.fromkeys(recommendations))
    return unique_recommendations[:10]

def _extract_next_steps(outputs: List[ProjectOutput]) -> List[str]:
    """Extract next steps from outputs"""
    next_steps = []
    
    for output in outputs:
        text_lower = output.output.lower()
        if "next step" in text_lower or "follow up" in text_lower or "next action" in text_lower:
            lines = output.output.split('\n')
            for line in lines:
                if any(phrase in line.lower() for phrase in ["next step", "follow up", "next action", "should", "need to"]):
                    clean_line = line.strip().lstrip('-•0123456789. ')
                    if len(clean_line) > 10 and clean_line not in next_steps:
                        next_steps.append(clean_line)
    
    return next_steps[:5]

def _determine_completion_status(tasks: List[Dict], outputs: List[ProjectOutput]) -> str:
    """Determine project completion status"""
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.get("status") == "completed"])
    pending_tasks = len([t for t in tasks if t.get("status") == "pending"])
    
    # If significant outputs and no pending tasks, awaiting review
    if len(outputs) >= 3 and pending_tasks == 0:
        return "awaiting_review"
    # If high completion rate, awaiting review
    elif completed_tasks / total_tasks > 0.8 if total_tasks > 0 else False:
        return "awaiting_review"
    # Otherwise in progress
    else:
        return "in_progress"

def _get_latest_update_timestamp(tasks: List[Dict]) -> str:
    """Return ISO timestamp of the most recently updated task"""
    latest = None
    for task in tasks:
        ts = task.get("updated_at") or task.get("created_at")
        if not ts:
            continue
        try:
            dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        except Exception:
            continue
        if not latest or dt > latest:
            latest = dt
    return latest.isoformat() if latest else ""

def _calculate_content_hash(tasks: List[Dict]) -> str:
    """Calculate a hash of the task content to detect changes beyond timestamp"""
    import hashlib
    
    # Create a string from key content fields
    content_parts = []
    for task in tasks:
        result = task.get("result", {}) or {}
        content_parts.extend([
            task.get("id", ""),
            task.get("name", ""),
            result.get("summary", ""),
            str(result.get("detailed_results_json", ""))[:500]  # First 500 chars to avoid huge hashes
        ])
    
    content_string = "|".join(content_parts)
    return hashlib.md5(content_string.encode('utf-8')).hexdigest()[:12]  # Short hash

async def _generate_deliverable_insights(outputs: List[Dict]) -> List[ProjectDeliverableCard]:
    """Generate user-friendly insights cards from task outputs"""
    cards = []
    
    try:
        # Raggruppa output per categoria
        categorized_outputs = _categorize_outputs(outputs)
        
        for category, items in categorized_outputs.items():
            if not items:
                continue
                
            # Genera insight per ogni categoria
            card = await _create_insight_card(category, items)
            if card:
                cards.append(card)
        
        return cards
    except Exception as e:
        logger.error(f"Error generating deliverable insights: {e}", exc_info=True)
        # Return empty list if insight generation fails
        return []

def _categorize_outputs(outputs: List[Dict]) -> Dict[str, List[Dict]]:
    """Categorize outputs into logical groups"""
    categories = {
        "research": [],
        "planning": [],
        "execution": [],
        "analysis": [],
        "review": []
    }
    
    for output in outputs:
        task_name = output.get("task_name", "").lower()
        content = output.get("output", "").lower()
        output_type = output.get("type", "general")
        
        # Intelligent categorization based on task name, content, and type
        if (any(keyword in task_name for keyword in ["research", "investigate", "study", "explore", "gather"]) or
            any(keyword in content[:200] for keyword in ["research", "investigate", "study", "explore"])):
            categories["research"].append(output)
        elif (any(keyword in task_name for keyword in ["plan", "strategy", "roadmap", "timeline", "milestone"]) or
              any(keyword in content[:200] for keyword in ["plan", "strategy", "roadmap", "timeline"])):
            categories["planning"].append(output)
        elif (any(keyword in task_name for keyword in ["implement", "create", "build", "develop", "execute"]) or
              any(keyword in content[:200] for keyword in ["implement", "create", "build", "develop"])):
            categories["execution"].append(output)
        elif (output_type == "analysis" or
              any(keyword in task_name for keyword in ["analyze", "assessment", "evaluation", "metrics", "performance"]) or
              any(keyword in content[:200] for keyword in ["analyze", "assessment", "evaluation", "metrics"])):
            categories["analysis"].append(output)
        elif (any(keyword in task_name for keyword in ["review", "feedback", "quality", "validation", "check"]) or
              any(keyword in content[:200] for keyword in ["review", "feedback", "quality", "validation"])):
            categories["review"].append(output)
        else:
            # Default categorization based on output type and length
            if output_type == "recommendation":
                categories["planning"].append(output)
            elif len(content) > 500:
                categories["analysis"].append(output)
            else:
                categories["execution"].append(output)
    
    return categories

async def _create_insight_card(category: str, items: List[Dict]) -> Optional[ProjectDeliverableCard]:
    """Create a user-friendly insight card for a category"""
    try:
        # Prepare content for AI analysis
        combined_content = ""
        task_names = []
        
        for item in items:
            task_names.append(item.get("task_name", ""))
            content = item.get("output", "")
            # Limit content length to prevent token overuse
            combined_content += f"\nTask: {item.get('task_name', '')}\nOutput: {content[:300]}...\n"
        
        # Create AI agent for insight generation
        from agents import Agent as OpenAIAgent, Runner
        
        insight_generator = OpenAIAgent(
            name="DeliverableInsightGenerator",
            instructions=f"""
            You are an expert at creating executive summaries from AI agent outputs.
            
            For this {category} category, create a concise, business-focused summary that:
            1. Highlights KEY BUSINESS VALUE and outcomes
            2. Extracts 2-4 concrete insights or learnings
            3. Mentions any quantitative results (numbers, percentages, metrics)
            4. Focuses on WHAT WAS ACHIEVED, not technical details
            
            Keep it professional but accessible. Write in present tense.
            Example insights format:
            • Market research identified 3 key customer segments
            • Cost analysis shows 15% potential savings
            • Implementation plan covers 6-month timeline
            """,
            model="gpt-4o-mini"
        )
        
        # Generate insights with retry logic
        prompt = f"""
        Category: {category.upper()}
        Number of tasks: {len(items)}
        
        Summary of completed work:
        {combined_content}
        
        Create a compelling 2-sentence summary and 2-4 key insights about what was accomplished.
        """
        
        try:
            result = await Runner.run(insight_generator, prompt, max_turns=1)
            ai_summary = str(result.final_output)
        except Exception as ai_error:
            logger.warning(f"AI insight generation failed for {category}: {ai_error}")
            # Fallback to simple summary
            ai_summary = f"Completed {len(items)} {category} tasks including {', '.join(task_names[:2])}."
        
        # Extract insights from AI response
        insights = _extract_insights_from_summary(ai_summary)
        
        # If no insights extracted, create fallback insights
        if not insights:
            insights = [f"Completed {len(items)} {category} deliverables"]
            if len(items) > 1:
                insights.append(f"Covered {len(set(task_names))} different areas")
        
        # Get category metadata
        category_config = {
            "research": {
                "icon": "🔍",
                "title": "Research & Discovery",
                "description_template": "Market research and data gathering completed"
            },
            "planning": {
                "icon": "📋",
                "title": "Strategic Planning",
                "description_template": "Project strategy and planning finalized"
            },
            "execution": {
                "icon": "⚡",
                "title": "Implementation",
                "description_template": "Core deliverables implemented successfully"
            },
            "analysis": {
                "icon": "📊",
                "title": "Analysis & Insights",
                "description_template": "Data analysis and insights generated"
            },
            "review": {
                "icon": "✅",
                "title": "Quality Assurance",
                "description_template": "Quality review and validation completed"
            }
        }
        
        config = category_config.get(category, {
            "icon": "📁",
            "title": category.title(),
            "description_template": f"{category.title()} deliverables completed"
        })
        
        # Extract metrics if any
        metrics = _extract_metrics_from_content(combined_content)
        
        # Calculate completeness score
        completeness_score = min(100, len(items) * 20 + len(insights) * 15)
        
        # Get the primary creator
        creators = [item.get("agent_name", "Unknown") for item in items]
        primary_creator = max(set(creators), key=creators.count) if creators else "AI Team"
        
        # Get latest creation time
        latest_time = max(
            (datetime.fromisoformat(item.get("created_at", datetime.now().isoformat()).replace('Z', '+00:00')) 
             for item in items if item.get("created_at")),
            default=datetime.now()
        )
        
        # Create clean description from AI summary
        description = ai_summary.split('.')[0] + '.' if '.' in ai_summary else ai_summary[:150]
        
        return ProjectDeliverableCard(
            id=f"{category}_{len(items)}_{int(latest_time.timestamp())}",
            title=config["title"],
            description=description,
            category=category,
            icon=config["icon"],
            key_insights=insights[:4],  # Limit to 4 insights
            metrics=metrics,
            created_by=primary_creator,
            created_at=latest_time,
            completeness_score=min(100, completeness_score)
        )
        
    except Exception as e:
        logger.error(f"Error creating insight card for {category}: {e}", exc_info=True)
        # Return a simple fallback card instead of None
        return ProjectDeliverableCard(
            id=f"{category}_fallback",
            title=category.title(),
            description=f"Completed {len(items)} {category} tasks successfully",
            category=category,
            icon="📁",
            key_insights=[f"{len(items)} tasks completed in {category}"],
            metrics=None,
            created_by="AI Team",
            created_at=datetime.now(),
            completeness_score=80
        )

def _extract_insights_from_summary(summary: str) -> List[str]:
    """Extract key insights from AI-generated summary"""
    insights = []
    
    # Look for bullet points
    lines = summary.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith(('•', '-', '*')) or any(line.startswith(f"{i}.") for i in range(1, 10)):
            clean_insight = line.lstrip('•-*0123456789. ').strip()
            if len(clean_insight) > 10 and len(clean_insight) < 100:
                insights.append(clean_insight)
    
    # If no bullet points found, try to split by sentences and look for key phrases
    if not insights:
        sentences = [s.strip() for s in summary.split('.') if s.strip()]
        for sentence in sentences:
            if (len(sentence) > 10 and 
                any(keyword in sentence.lower() for keyword in 
                    ['completed', 'achieved', 'identified', 'analyzed', 'developed', 'created', 'found'])):
                insights.append(sentence.strip())
                if len(insights) >= 4:
                    break
    
    return insights[:4]  # Always limit to 4 insights

def _extract_metrics_from_content(content: str) -> Optional[Dict[str, Any]]:
    """Extract any metrics, numbers, or quantitative data from content"""
    import re
    
    metrics = {}
    
    try:
        # Look for percentages
        percentages = re.findall(r'(\d+(?:\.\d+)?)\s*%', content)
        if percentages:
            metrics['percentages'] = [f"{p}%" for p in percentages[:3]]
        
        # Look for currency amounts (more flexible pattern)
        currency = re.findall(r'[\$€£¥]\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', content)
        if currency:
            metrics['amounts'] = [f"${amount}" for amount in currency[:3]]
        
        # Look for large numbers (simplified)
        numbers = re.findall(r'\b(\d{1,3}(?:,\d{3})+|\d{4,})\b', content)
        if numbers:
            metrics['quantities'] = numbers[:3]
        
        # Look for time periods
        time_periods = re.findall(r'(\d+)\s+(days?|weeks?|months?|years?)', content, re.IGNORECASE)
        if time_periods:
            metrics['timeframes'] = [f"{num} {unit}" for num, unit in time_periods[:2]]
        
        return metrics if metrics else None
        
    except Exception as e:
        logger.warning(f"Error extracting metrics: {e}")
        return None