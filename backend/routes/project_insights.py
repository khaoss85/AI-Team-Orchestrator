from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging
import json  # NUOVO: Aggiunto import json
from datetime import datetime, timedelta
import os
from collections import Counter
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
    list_agents as db_list_agents,
    list_tasks,
    create_task,
)
from executor import task_executor
from deliverable_system.requirements_analyzer import DeliverableRequirementsAnalyzer
from deliverable_system.schema_generator import AssetSchemaGenerator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["project-insights"])

# Simple in-memory cache for deliverables
ENABLE_DELIVERABLE_CACHE = os.getenv("ENABLE_DELIVERABLE_CACHE", "true").lower() == "true"
DELIVERABLE_CACHE: Dict[str, Dict[str, Any]] = {}


@router.get("/{workspace_id}/insights", response_model=Dict[str, Any])
async def get_project_insights(workspace_id: UUID):
    """Get comprehensive project insights including progress, timing, and predictions"""
    try:
        # Get workspace details
        workspace = await get_workspace(str(workspace_id))
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        # Get agents and tasks
        agents = await db_list_agents(str(workspace_id))
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
async def get_major_milestones(workspace_id: UUID):
    """Get major milestones and phases completed in the project"""
    try:
        tasks = await list_tasks(str(workspace_id))
        agents = await db_list_agents(str(workspace_id))
        
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
async def get_project_deliverables(workspace_id: UUID):
    """Get aggregated project deliverables including final aggregated deliverable - ENHANCED"""
    try:
        # Get workspace details
        workspace = await get_workspace(str(workspace_id))
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        # Get all tasks
        tasks = await list_tasks(str(workspace_id))
        completed_tasks = [t for t in tasks if t.get("status") == "completed"]

        # Cache check based on latest task update
        last_updated = _get_latest_update_timestamp(tasks)
        cache_entry = DELIVERABLE_CACHE.get(str(workspace_id)) if ENABLE_DELIVERABLE_CACHE else None
        if cache_entry and cache_entry.get("last_updated") == last_updated:
            logger.info(f"\U0001F4E6 Using cached deliverable for {workspace_id}")
            return cache_entry["data"]
        
        # Get agents info for names/roles
        agents = await db_list_agents(str(workspace_id))
        agent_map = {a["id"]: a for a in agents}
        
        # Extract outputs from completed tasks
        key_outputs = []
        for task in completed_tasks:
            result = task.get("result", {}) or {}
            context_data = task.get("context_data", {}) or {}
            output_text = result.get("summary", "")
            
            if output_text and len(output_text.strip()) > 10:  # Skip trivial outputs
                agent_info = agent_map.get(task.get("agent_id"), {})
                
                # Classify output type
                output_type = _classify_output_type(task.get("name", ""), output_text)
                
                key_outputs.append(ProjectOutput(
                    task_id=task["id"],
                    task_name=task.get("name", "Unnamed Task"),
                    output=output_text[:1000] + "..." if len(output_text) > 1000 else output_text,
                    agent_name=agent_info.get("name", "Unknown Agent"),
                    agent_role=agent_info.get("role", "Unknown Role"),
                    created_at=datetime.fromisoformat(task.get("updated_at", task.get("created_at", datetime.now().isoformat())).replace('Z', '+00:00')),
                    type=output_type,
                    execution_time_seconds=result.get("execution_time_seconds") or context_data.get("execution_time_seconds"),
                    cost_estimated=result.get("cost_estimated") or context_data.get("cost_estimated"),
                    tokens_used=result.get("tokens_used") or context_data.get("tokens_used"),
                    model_used=result.get("model_used") or context_data.get("model_used"),
                    rationale=result.get("rationale") or context_data.get("rationale") or result.get("phase_rationale") or context_data.get("phase_rationale")
                ))
        
        # ENHANCED: Controlla se esiste un deliverable finale aggregato
        final_deliverable_task = None
        for task in completed_tasks:
            context_data = task.get("context_data", {}) or {}
            if (context_data.get("is_final_deliverable") or 
                context_data.get("deliverable_aggregation") or
                context_data.get("triggers_project_completion")):
                final_deliverable_task = task
                break
        
        # ENHANCED: Se esiste un deliverable finale, processalo con logica robusta
        if final_deliverable_task:
            logger.info(f"🎯 PROCESSING final deliverable task: {final_deliverable_task['id']}")
            result = final_deliverable_task.get("result", {}) or {}
            fd_context = final_deliverable_task.get("context_data", {}) or {}
            
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
                executive_summary = f"Project deliverable completed for: {workspace_goal}"
                logger.warning(f"🎯 EMERGENCY FALLBACK: Generated basic executive summary")
            
            # ENHANCED: Create comprehensive final output with robust data
            try:
                final_output = ProjectOutput(
                    task_id=final_deliverable_task["id"],
                    task_name="🎯 " + final_deliverable_task.get("name", "Final Deliverable"),
                    output=executive_summary,  # This will now always have content
                    agent_name=agent_map.get(final_deliverable_task.get("agent_id"), {}).get("name", "Project Manager"),
                    agent_role="Final Deliverable",
                    created_at=datetime.fromisoformat(final_deliverable_task.get("updated_at", datetime.now().isoformat()).replace('Z', '+00:00')),
                    type="final_deliverable",
                    # ENHANCED: Robust field extraction with fallbacks
                    title=detailed_json_data.get("deliverable_type", "Final Project Deliverable").replace("_", " ").title(),
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
                "data": response,
            }

        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🎯 CRITICAL ERROR in get_project_deliverables: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project deliverables: {str(e)}"
        )

@router.post("/{workspace_id}/deliverables/feedback", status_code=status.HTTP_200_OK)
async def submit_deliverable_feedback(
    workspace_id: UUID,
    feedback: DeliverableFeedback
):
    """Submit feedback on project deliverables"""
    try:
        # Create a new task for handling the feedback
        agents = await db_list_agents(str(workspace_id))
        
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
async def trigger_asset_analysis(workspace_id: UUID):
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
async def get_asset_insights(workspace_id: UUID):
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
async def get_output_detail(workspace_id: UUID, task_id: UUID):
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

# Helper functions
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
            model="gpt-4.1-mini"
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
            model="gpt-4.1-mini"
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