"""
🤖 AI-Driven System Monitoring API Routes
Provides real-time system metrics, alerts, and health monitoring endpoints
"""

from fastapi import Request, APIRouter, HTTPException, Query
from typing import Optional, Dict, Any, List
from middleware.trace_middleware import get_trace_id, create_traced_logger, TracedDatabaseOperation
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monitoring", tags=["system-monitoring"])

@router.get("/status")
async def get_system_status(request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_system_status called", endpoint="get_system_status", trace_id=trace_id)

    """
    🤖 AI-DRIVEN: Get comprehensive system status report
    Returns current health, metrics, alerts, and recommendations
    """
    try:
        from services.system_telemetry_monitor import system_telemetry_monitor
        
        status_report = await system_telemetry_monitor.get_system_status_report()
        
        return {
            "success": True,
            "data": status_report,
            "timestamp": datetime.now().isoformat()
        }
        
    except ImportError:
        logger.warning("System telemetry monitor not available")
        return {
            "success": False,
            "error": "System monitoring not available",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/current")
async def get_current_metrics(request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_current_metrics called", endpoint="get_current_metrics", trace_id=trace_id)

    """
    🤖 AI-DRIVEN: Get current system metrics
    Returns latest telemetry data
    """
    try:
        from services.system_telemetry_monitor import system_telemetry_monitor
        
        metrics = await system_telemetry_monitor.collect_comprehensive_metrics()
        
        return {
            "success": True,
            "metrics": {
                "timestamp": metrics.timestamp,
                "system_health_score": metrics.system_health_score,
                "active_workspaces": metrics.active_workspaces,
                "paused_workspaces": metrics.paused_workspaces,
                "pending_tasks_total": metrics.pending_tasks_total,
                "critical_tasks_total": metrics.critical_tasks_total,
                "task_completion_rate": metrics.task_completion_rate,
                "average_task_wait_time": metrics.average_task_wait_time,
                "ai_confidence_average": metrics.ai_confidence_average,
                "workspace_recovery_actions": metrics.workspace_recovery_actions
            }
        }
        
    except ImportError:
        return {
            "success": False,
            "error": "System monitoring not available"
        }
    except Exception as e:
        logger.error(f"Error getting current metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts")
async def get_system_alerts(
    hours: Optional[int] = Query(24, description="Hours of alert history to retrieve"),
    severity: Optional[str] = Query(None, description="Filter by severity: info, warning, critical")
):
    """
    🤖 AI-DRIVEN: Get system alerts
    Returns recent alerts with optional filtering
    """
    try:
        from services.system_telemetry_monitor import system_telemetry_monitor
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Get alerts from history
        recent_alerts = [
            {
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "message": alert.message,
                "component": alert.component,
                "workspace_id": alert.workspace_id,
                "metric_value": alert.metric_value,
                "threshold": alert.threshold,
                "timestamp": alert.timestamp,
                "resolution_status": alert.resolution_status
            }
            for alert in system_telemetry_monitor.alert_history
            if datetime.fromisoformat(alert.timestamp) >= cutoff_time
            and (not severity or alert.severity == severity)
        ]
        
        # Sort by timestamp (newest first)
        recent_alerts.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "success": True,
            "alerts": recent_alerts,
            "total_count": len(recent_alerts),
            "filter": {
                "hours": hours,
                "severity": severity
            },
            "summary": {
                "critical": len([a for a in recent_alerts if a["severity"] == "critical"]),
                "warning": len([a for a in recent_alerts if a["severity"] == "warning"]),
                "info": len([a for a in recent_alerts if a["severity"] == "info"])
            }
        }
        
    except ImportError:
        return {
            "success": False,
            "error": "System monitoring not available"
        }
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health/workspace/{workspace_id}")
async def get_workspace_health(workspace_id: str, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_workspace_health called", endpoint="get_workspace_health", trace_id=trace_id)

    """
    🤖 AI-DRIVEN: Get specific workspace health metrics
    """
    try:
        from services.dynamic_anti_loop_manager import dynamic_anti_loop_manager
        from services.workspace_pause_manager import workspace_pause_manager
        
        # Get dynamic anti-loop metrics
        metrics = await dynamic_anti_loop_manager.collect_workspace_metrics(workspace_id)
        
        # Check if workspace should allow critical bypass
        critical_bypass = await workspace_pause_manager.should_allow_critical_bypass(workspace_id)
        
        return {
            "success": True,
            "workspace_id": workspace_id,
            "health": {
                "health_score": metrics.health_score,
                "pending_tasks": metrics.pending_tasks_count,
                "critical_tasks": metrics.critical_tasks_count,
                "average_wait_time_minutes": metrics.average_wait_time_minutes,
                "task_generation_rate": metrics.task_generation_rate,
                "completion_rate": metrics.completion_rate,
                "current_limit": metrics.current_limit,
                "recommended_limit": metrics.recommended_limit,
                "critical_bypass_enabled": critical_bypass
            },
            "recommendations": [
                f"Current limit: {metrics.current_limit}, recommended: {metrics.recommended_limit}",
                f"Health score: {metrics.health_score:.2f}",
                f"Critical tasks: {metrics.critical_tasks_count}"
            ]
        }
        
    except ImportError:
        return {
            "success": False,
            "error": "Workspace health monitoring not available"
        }
    except Exception as e:
        logger.error(f"Error getting workspace health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance/trends")
async def get_performance_trends(
    hours: Optional[int] = Query(24, description="Hours of trend data to analyze")
):
    """
    🤖 AI-DRIVEN: Get performance trends analysis
    """
    try:
        from services.system_telemetry_monitor import system_telemetry_monitor
        
        # Calculate trends from metrics history
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        relevant_metrics = [
            m for m in system_telemetry_monitor.metrics_history
            if datetime.fromisoformat(m.timestamp) >= cutoff_time
        ]
        
        if len(relevant_metrics) < 2:
            return {
                "success": True,
                "message": "Insufficient data for trend analysis",
                "data_points": len(relevant_metrics)
            }
        
        # Calculate trends
        latest = relevant_metrics[-1]
        earliest = relevant_metrics[0]
        
        trends = {
            "system_health": {
                "current": latest.system_health_score,
                "change": latest.system_health_score - earliest.system_health_score,
                "trend": "improving" if latest.system_health_score > earliest.system_health_score else "degrading"
            },
            "task_wait_time": {
                "current": latest.average_task_wait_time,
                "change": latest.average_task_wait_time - earliest.average_task_wait_time,
                "trend": "improving" if latest.average_task_wait_time < earliest.average_task_wait_time else "degrading"
            },
            "completion_rate": {
                "current": latest.task_completion_rate,
                "change": latest.task_completion_rate - earliest.task_completion_rate,
                "trend": "improving" if latest.task_completion_rate > earliest.task_completion_rate else "degrading"
            },
            "active_workspaces": {
                "current": latest.active_workspaces,
                "change": latest.active_workspaces - earliest.active_workspaces,
                "trend": "growing" if latest.active_workspaces > earliest.active_workspaces else "stable" if latest.active_workspaces == earliest.active_workspaces else "shrinking"
            }
        }
        
        return {
            "success": True,
            "trends": trends,
            "analysis_period_hours": hours,
            "data_points": len(relevant_metrics),
            "first_measurement": earliest.timestamp,
            "latest_measurement": latest.timestamp
        }
        
    except ImportError:
        return {
            "success": False,
            "error": "System monitoring not available"
        }
    except Exception as e:
        logger.error(f"Error getting performance trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route acknowledge_alert called", endpoint="acknowledge_alert", trace_id=trace_id)

    """
    🤖 AI-DRIVEN: Acknowledge a system alert
    """
    try:
        from services.system_telemetry_monitor import system_telemetry_monitor
        
        # Find and acknowledge the alert
        for alert in system_telemetry_monitor.alert_history:
            if str(hash(f"{alert.timestamp}-{alert.alert_type}")) == alert_id:
                alert.resolution_status = "acknowledged"
                
                return {
                    "success": True,
                    "message": f"Alert acknowledged: {alert.message}",
                    "alert_id": alert_id
                }
        
        raise HTTPException(status_code=404, detail="Alert not found")
        
    except ImportError:
        return {
            "success": False,
            "error": "System monitoring not available"
        }
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/diagnostics")
async def get_system_diagnostics(request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_system_diagnostics called", endpoint="get_system_diagnostics", trace_id=trace_id)

    """
    🤖 AI-DRIVEN: Get comprehensive system diagnostics
    Returns detailed diagnostic information for troubleshooting
    """
    try:
        diagnostics = {
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "integrations": {},
            "configuration": {}
        }
        
        # Check Dynamic Anti-Loop Manager
        try:
            from services.dynamic_anti_loop_manager import dynamic_anti_loop_manager
            diagnostics["components"]["dynamic_anti_loop"] = {
                "status": "available",
                "base_limit": 15,  # Would get from actual config
                "workspaces_monitored": len(dynamic_anti_loop_manager.workspace_metrics)
            }
        except ImportError:
            diagnostics["components"]["dynamic_anti_loop"] = {"status": "not_available"}
        
        # Check Workspace Pause Manager
        try:
            from services.workspace_pause_manager import workspace_pause_manager
            diagnostics["components"]["workspace_pause_manager"] = {
                "status": "available",
                "auto_recovery_enabled": workspace_pause_manager.auto_recovery_enabled
            }
        except ImportError:
            diagnostics["components"]["workspace_pause_manager"] = {"status": "not_available"}
        
        # Check Achievement Mapper
        try:
            from services.deliverable_achievement_mapper import deliverable_achievement_mapper
            diagnostics["components"]["achievement_mapper"] = {
                "status": "available",
                "extraction_methods": deliverable_achievement_mapper.extraction_methods
            }
        except ImportError:
            diagnostics["components"]["achievement_mapper"] = {"status": "not_available"}
        
        # Check Telemetry Monitor
        try:
            from services.system_telemetry_monitor import system_telemetry_monitor
            diagnostics["components"]["telemetry_monitor"] = {
                "status": "available",
                "monitoring_enabled": system_telemetry_monitor.monitoring_enabled,
                "alert_enabled": system_telemetry_monitor.alert_enabled,
                "metrics_history_size": len(system_telemetry_monitor.metrics_history),
                "alert_history_size": len(system_telemetry_monitor.alert_history)
            }
        except ImportError:
            diagnostics["components"]["telemetry_monitor"] = {"status": "not_available"}
        
        # Check Executor Integration
        try:
            from executor import DYNAMIC_ANTI_LOOP_AVAILABLE, TELEMETRY_MONITOR_AVAILABLE
            diagnostics["integrations"]["executor"] = {
                "dynamic_anti_loop_integrated": DYNAMIC_ANTI_LOOP_AVAILABLE,
                "telemetry_monitor_integrated": TELEMETRY_MONITOR_AVAILABLE
            }
        except ImportError:
            diagnostics["integrations"]["executor"] = {"status": "not_available"}
        
        # Configuration check
        import os
        diagnostics["configuration"] = {
            "max_tasks_per_workspace": os.getenv("MAX_TASKS_PER_WORKSPACE_ANTI_LOOP", "15"),
            "max_absolute_limit": os.getenv("MAX_ABSOLUTE_ANTI_LOOP_LIMIT", "50"),
            "enable_telemetry": os.getenv("ENABLE_ADVANCED_TELEMETRY", "true"),
            "enable_alerts": os.getenv("ENABLE_PROACTIVE_ALERTS", "true")
        }
        
        return {
            "success": True,
            "diagnostics": diagnostics
        }
        
    except Exception as e:
        logger.error(f"Error getting system diagnostics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@router.get("/health")
async def health_check(request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route health_check called", endpoint="health_check", trace_id=trace_id)

    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "system_monitoring"
    }