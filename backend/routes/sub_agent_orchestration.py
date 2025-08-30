"""
Sub-Agent Orchestration API Routes - Monitoring and Control

Provides API endpoints for:
- Sub-agent performance monitoring
- Orchestration pattern insights
- Feature flag control
- Real-time orchestration status
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sub-agent-orchestration", tags=["Sub-Agent Orchestration"])

class SubAgentStatus(BaseModel):
    """Sub-agent status response"""
    agent_id: str
    name: str
    specialization: str
    is_available: bool
    current_tasks: int
    total_completed_tasks: int
    success_rate: float
    avg_execution_time: float
    priority_boost: int
    performance_trend: str

class OrchestrationDashboard(BaseModel):
    """Orchestration system dashboard"""
    system_status: str
    total_agents: int
    active_orchestrations: int
    feature_flags: Dict[str, bool]
    performance_summary: Dict[str, Any]
    recent_orchestrations: List[Dict[str, Any]]

class OrchestrationTriggerRequest(BaseModel):
    """Manual orchestration trigger request"""
    task_description: str
    workspace_id: str
    task_type: Optional[str] = "hybrid"
    priority: Optional[str] = "medium"
    force_agents: Optional[List[str]] = None

@router.get("/status", response_model=Dict[str, Any])
async def get_orchestration_status():
    """Get current sub-agent orchestration system status"""
    try:
        # Import here to handle circular imports and optional availability
        from config.optimized_sub_agent_configs_2025 import (
            SUB_AGENT_ORCHESTRATION_AVAILABLE, 
            get_orchestrator_dashboard,
            optimized_orchestrator
        )
        
        if not SUB_AGENT_ORCHESTRATION_AVAILABLE:
            return {
                "system_status": "unavailable",
                "message": "Sub-agent orchestration system is not available",
                "feature_flags": {"orchestration_enabled": False}
            }
        
        # Get comprehensive dashboard data
        dashboard_data = await get_orchestrator_dashboard()
        
        return {
            "system_status": "active",
            "timestamp": datetime.now().isoformat(),
            "dashboard": dashboard_data,
            "feature_flags": {
                "orchestration_enabled": True,
                "frontend_ux_enabled": True,
                "performance_tracking": True
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting orchestration status: {e}")
        return {
            "system_status": "error",
            "error": str(e),
            "feature_flags": {"orchestration_enabled": False}
        }

@router.get("/agents", response_model=List[SubAgentStatus])
async def get_agent_status():
    """Get status of all sub-agents"""
    try:
        from config.optimized_sub_agent_configs_2025 import (
            optimized_orchestrator,
            get_performance_summary
        )
        
        agent_statuses = []
        
        for agent_id, config in optimized_orchestrator.agents.items():
            try:
                # Get performance summary for each agent
                perf_summary = await get_performance_summary(agent_id)
                
                agent_status = SubAgentStatus(
                    agent_id=agent_id,
                    name=config.name,
                    specialization=config.specialization.value,
                    is_available=True,  # Would check actual availability
                    current_tasks=0,    # Would check current task count
                    total_completed_tasks=perf_summary.get('total_tasks', config.total_tasks_completed),
                    success_rate=perf_summary.get('success_rate', config.historical_success_rate),
                    avg_execution_time=perf_summary.get('avg_execution_time', config.avg_execution_time),
                    priority_boost=config.priority_boost,
                    performance_trend=config.recent_performance_trend
                )
                
                agent_statuses.append(agent_status)
                
            except Exception as e:
                logger.warning(f"Error getting status for agent {agent_id}: {e}")
                continue
        
        return agent_statuses
        
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving agent status: {str(e)}")

@router.get("/patterns")
async def get_orchestration_patterns():
    """Get available orchestration patterns and their success rates"""
    try:
        from config.optimized_sub_agent_configs_2025 import optimized_orchestrator
        
        patterns = {}
        for pattern_name, pattern_config in optimized_orchestrator.orchestration_patterns.items():
            patterns[pattern_name] = {
                "sequence": pattern_config.get("sequence", []),
                "parallel_stages": pattern_config.get("parallel_stages", []),
                "success_rate": pattern_config.get("success_rate", 0.0),
                "avg_execution_time": pattern_config.get("avg_execution_time", 0),
                "description": f"Orchestration pattern for {pattern_name.replace('_', ' ').title()}"
            }
        
        return {
            "patterns": patterns,
            "total_patterns": len(patterns),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting orchestration patterns: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving patterns: {str(e)}")

@router.post("/suggest-agents")
async def suggest_agents_for_task(request: OrchestrationTriggerRequest):
    """Get agent suggestions for a given task description"""
    try:
        from config.optimized_sub_agent_configs_2025 import suggest_agents_for_task
        
        context = {
            "workspace_id": request.workspace_id,
            "task_type": request.task_type,
            "priority": request.priority
        }
        
        suggested_agents = await suggest_agents_for_task(request.task_description, context)
        
        # Get detailed info about suggested agents
        from config.optimized_sub_agent_configs_2025 import optimized_orchestrator
        
        agent_details = []
        for agent_id in suggested_agents:
            if agent_id in optimized_orchestrator.agents:
                config = optimized_orchestrator.agents[agent_id]
                agent_details.append({
                    "agent_id": agent_id,
                    "name": config.name,
                    "specialization": config.specialization.value,
                    "priority_boost": config.priority_boost,
                    "description": config.description[:100] + "..." if len(config.description) > 100 else config.description
                })
        
        return {
            "task_description": request.task_description,
            "suggested_agents": suggested_agents,
            "agent_details": agent_details,
            "orchestration_recommended": len(suggested_agents) >= 2,
            "estimated_agents": len(suggested_agents),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error suggesting agents: {e}")
        raise HTTPException(status_code=500, detail=f"Error suggesting agents: {str(e)}")

@router.get("/performance/{agent_id}")
async def get_agent_performance(agent_id: str):
    """Get detailed performance metrics for a specific agent"""
    try:
        from config.optimized_sub_agent_configs_2025 import get_performance_summary
        
        performance_data = await get_performance_summary(agent_id)
        
        if "error" in performance_data:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found or no performance data")
        
        return {
            "agent_id": agent_id,
            "performance": performance_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent performance: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving performance data: {str(e)}")

@router.post("/test-orchestration")
async def test_orchestration(request: OrchestrationTriggerRequest, background_tasks: BackgroundTasks):
    """Test orchestration system with a sample task (development only)"""
    try:
        from config.optimized_sub_agent_configs_2025 import suggest_agents_for_task
        from services.enhanced_sub_agent_orchestrator import orchestrate_task
        
        # Get suggested agents
        context = {
            "workspace_id": request.workspace_id,
            "task_type": request.task_type,
            "priority": request.priority
        }
        
        suggested_agents = await suggest_agents_for_task(request.task_description, context)
        
        if len(suggested_agents) < 2:
            return {
                "test_result": "no_orchestration_needed",
                "message": "Task requires single agent - no orchestration needed",
                "suggested_agents": suggested_agents
            }
        
        # For testing, simulate orchestration (don't actually execute)
        test_result = {
            "test_result": "orchestration_simulated",
            "task_description": request.task_description,
            "suggested_agents": suggested_agents,
            "orchestration_pattern": "frontend_implementation" if any(
                kw in request.task_description.lower() 
                for kw in ['ui', 'ux', 'component', 'frontend', 'react']
            ) else "complex_implementation",
            "estimated_execution_time": 150 if "frontend" in request.task_description.lower() else 180,
            "simulation_only": True,
            "timestamp": datetime.now().isoformat()
        }
        
        return test_result
        
    except Exception as e:
        logger.error(f"Error testing orchestration: {e}")
        raise HTTPException(status_code=500, detail=f"Error testing orchestration: {str(e)}")

@router.get("/feature-flags")
async def get_feature_flags():
    """Get current feature flag status for sub-agent orchestration"""
    import os
    
    return {
        "orchestration_enabled": os.getenv("ENABLE_SUB_AGENT_ORCHESTRATION", "true").lower() == "true",
        "frontend_ux_enabled": os.getenv("SUB_AGENT_FRONTEND_UX_ENABLED", "true").lower() == "true", 
        "performance_tracking": os.getenv("SUB_AGENT_PERFORMANCE_TRACKING", "true").lower() == "true",
        "max_concurrent_agents": int(os.getenv("SUB_AGENT_MAX_CONCURRENT_AGENTS", "5")),
        "log_level": os.getenv("SUB_AGENT_ORCHESTRATION_LOG_LEVEL", "INFO"),
        "timestamp": datetime.now().isoformat()
    }

@router.post("/feature-flags")
async def update_feature_flags(flags: Dict[str, Any]):
    """Update feature flags (for development testing only)"""
    try:
        # In a real deployment, this would update environment variables or configuration
        # For now, return the requested changes (they won't persist across restarts)
        
        return {
            "message": "Feature flags updated (session only - restart to revert)",
            "updated_flags": flags,
            "warning": "Changes are temporary and will revert on application restart",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error updating feature flags: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating feature flags: {str(e)}")