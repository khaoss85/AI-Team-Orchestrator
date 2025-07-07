"""
Component Health API Routes

Endpoints per monitoraggio salute componenti e metriche sistema.
"""

from fastapi import Request, APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from middleware.trace_middleware import get_trace_id, create_traced_logger, TracedDatabaseOperation
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/health", tags=["component-health"])

# Create a secondary router for backward compatibility
health_router = APIRouter(prefix="/component-health", tags=["component-health"])

@router.get("/system")
async def get_system_health(request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_system_health called", endpoint="get_system_health", trace_id=trace_id)

    """Ottieni riassunto salute complessiva del sistema"""
    try:
        from services.component_health_monitor import get_system_health
        
        health_summary = await get_system_health()
        
        return {
            "status": "success",
            "data": health_summary,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/components")
async def get_all_components_health(include_metrics: bool = Query(False, description="Include detailed metrics"), request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_all_components_health called", endpoint="get_all_components_health", trace_id=trace_id)

    """Ottieni stato di salute di tutti i componenti"""
    try:
        from database import get_supabase_client
        supabase = get_supabase_client()
        
        # Query component health data
        query = supabase.table('component_health').select('*').order('component_name')
        result = query.execute()
        
        if not result.data:
            return {
                "status": "success",
                "components": [],
                "total_count": 0,
                "message": "No component health data available"
            }
        
        components = result.data
        
        # Process components data
        processed_components = []
        for component in components:
            component_info = {
                "name": component["component_name"],
                "status": component["status"],
                "health_score": component.get("health_score", 0.0),
                "last_heartbeat": component.get("last_heartbeat"),
                "consecutive_failures": component.get("consecutive_failures", 0),
                "last_error": component.get("last_error"),
                "updated_at": component.get("updated_at")
            }
            
            if include_metrics:
                component_info.update({
                    "avg_response_time_ms": component.get("avg_response_time_ms"),
                    "error_rate": component.get("error_rate", 0.0),
                    "throughput_per_minute": component.get("throughput_per_minute", 0.0),
                    "metadata": component.get("metadata", {}),
                    "dependencies": component.get("dependencies", []),
                    "dependent_components": component.get("dependent_components", [])
                })
            
            processed_components.append(component_info)
        
        # Calculate summary stats
        healthy_count = sum(1 for c in components if c["status"] == "healthy")
        degraded_count = sum(1 for c in components if c["status"] == "degraded")
        unhealthy_count = sum(1 for c in components if c["status"] == "unhealthy")
        
        return {
            "status": "success",
            "components": processed_components,
            "total_count": len(components),
            "summary": {
                "healthy": healthy_count,
                "degraded": degraded_count,
                "unhealthy": unhealthy_count,
                "overall_health": "healthy" if unhealthy_count == 0 else "degraded" if unhealthy_count <= 1 else "critical"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting components health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/component/{component_name}")
async def get_component_health(component_name: str, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_component_health called", endpoint="get_component_health", trace_id=trace_id)

    """Ottieni stato dettagliato di un componente specifico"""
    try:
        from database import get_supabase_client
        supabase = get_supabase_client()
        
        # Query specific component
        result = supabase.table('component_health').select('*').eq('component_name', component_name).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail=f"Component '{component_name}' not found")
        
        component = result.data
        
        # Calculate heartbeat status
        heartbeat_status = "unknown"
        if component.get("last_heartbeat"):
            from datetime import datetime, timedelta
            last_heartbeat = datetime.fromisoformat(component["last_heartbeat"].replace("Z", "+00:00"))
            now = datetime.now(last_heartbeat.tzinfo)
            
            if (now - last_heartbeat).total_seconds() < 60:
                heartbeat_status = "current"
            elif (now - last_heartbeat).total_seconds() < 300:
                heartbeat_status = "recent"
            else:
                heartbeat_status = "stale"
        
        return {
            "status": "success",
            "component": {
                "name": component["component_name"],
                "status": component["status"],
                "health_score": component.get("health_score", 0.0),
                "heartbeat_status": heartbeat_status,
                "last_heartbeat": component.get("last_heartbeat"),
                "last_success_at": component.get("last_success_at"),
                "consecutive_failures": component.get("consecutive_failures", 0),
                "last_error": component.get("last_error"),
                "performance_metrics": {
                    "avg_response_time_ms": component.get("avg_response_time_ms"),
                    "error_rate": component.get("error_rate", 0.0),
                    "throughput_per_minute": component.get("throughput_per_minute", 0.0)
                },
                "configuration": component.get("configuration", {}),
                "metadata": component.get("metadata", {}),
                "dependencies": component.get("dependencies", []),
                "dependent_components": component.get("dependent_components", []),
                "created_at": component.get("created_at"),
                "updated_at": component.get("updated_at")
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting component health for {component_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events/recent")
async def get_recent_health_events(limit: int = Query(50, description="Number of recent events to retrieve"), request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_recent_health_events called", endpoint="get_recent_health_events", trace_id=trace_id)

    """Ottieni eventi di salute recenti"""
    try:
        from database import get_supabase_client
        supabase = get_supabase_client()
        
        # Get recent integration events related to health
        result = supabase.table('integration_events').select('*')\
            .in_('event_type', ['component_health_updated', 'component_failed', 'component_recovered'])\
            .order('created_at', desc=True)\
            .limit(limit).execute()
        
        events = result.data if result.data else []
        
        return {
            "status": "success",
            "events": events,
            "count": len(events),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting recent health events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/summary")
async def get_health_metrics_summary(request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_health_metrics_summary called", endpoint="get_health_metrics_summary", trace_id=trace_id)

    """Ottieni riassunto metriche di salute sistema"""
    try:
        from database import get_supabase_client
        supabase = get_supabase_client()
        
        # Get all components with metrics
        result = supabase.table('component_health').select('*').execute()
        
        if not result.data:
            return {
                "status": "success",
                "metrics": {
                    "avg_response_time_ms": 0.0,
                    "avg_error_rate": 0.0,
                    "total_throughput": 0.0,
                    "avg_health_score": 0.0
                },
                "component_count": 0
            }
        
        components = result.data
        
        # Calculate aggregate metrics
        valid_response_times = [c["avg_response_time_ms"] for c in components if c.get("avg_response_time_ms") is not None]
        error_rates = [c.get("error_rate", 0.0) for c in components]
        throughputs = [c.get("throughput_per_minute", 0.0) for c in components]
        health_scores = [c.get("health_score", 0.0) for c in components]
        
        metrics = {
            "avg_response_time_ms": sum(valid_response_times) / len(valid_response_times) if valid_response_times else 0.0,
            "avg_error_rate": sum(error_rates) / len(error_rates) if error_rates else 0.0,
            "total_throughput": sum(throughputs),
            "avg_health_score": sum(health_scores) / len(health_scores) if health_scores else 0.0,
            "components_with_errors": sum(1 for c in components if c.get("last_error")),
            "components_with_recent_heartbeat": sum(1 for c in components if c.get("last_heartbeat") and 
                (datetime.now() - datetime.fromisoformat(c["last_heartbeat"].replace("Z", "+00:00"))).total_seconds() < 300)
        }
        
        return {
            "status": "success",
            "metrics": metrics,
            "component_count": len(components),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting health metrics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/component/{component_name}/heartbeat")
async def manual_heartbeat(component_name: str, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route manual_heartbeat called", endpoint="manual_heartbeat", trace_id=trace_id)

    """Invia heartbeat manuale per un componente"""
    try:
        from database import get_supabase_client
        supabase = get_supabase_client()
        
        # Update heartbeat manually
        now = datetime.now()
        
        health_data = {
            "last_heartbeat": now.isoformat(),
            "last_success_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "consecutive_failures": 0
        }
        
        result = supabase.table('component_health').update(health_data)\
            .eq('component_name', component_name).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail=f"Component '{component_name}' not found")
        
        return {
            "status": "success",
            "message": f"Manual heartbeat sent for component '{component_name}'",
            "timestamp": now.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending manual heartbeat for {component_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard")
async def get_health_dashboard(request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_health_dashboard called", endpoint="get_health_dashboard", trace_id=trace_id)

    """Ottieni dati completi per dashboard di monitoraggio"""
    try:
        from services.component_health_monitor import get_system_health
        from database import get_supabase_client
        
        supabase = get_supabase_client()
        
        # Get system health summary
        system_health = await get_system_health()
        
        # Get recent events
        events_result = supabase.table('integration_events').select('*')\
            .order('created_at', desc=True).limit(20).execute()
        
        # Get orchestration flows status
        flows_result = supabase.table('orchestration_flows').select('*')\
            .in_('status', ['active', 'paused']).execute()
        
        active_flows = flows_result.data if flows_result.data else []
        recent_events = events_result.data if events_result.data else []
        
        return {
            "status": "success",
            "dashboard": {
                "system_health": system_health,
                "active_flows": len(active_flows),
                "recent_events_count": len(recent_events),
                "flows": active_flows[:5],  # Last 5 active flows
                "events": recent_events[:10]  # Last 10 events
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting health dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Add backward compatibility endpoints to the secondary router
@health_router.get("/")
async def get_components_health_compat():
    """Backward compatibility endpoint for component health"""
    try:
        from database import get_supabase_client
        supabase = get_supabase_client()
        
        # Query component health data
        result = supabase.table('component_health').select('*').order('component_name').execute()
        
        components = result.data if result.data else []
        
        return {
            "status": "success",
            "components": components,
            "total_count": len(components),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting component health: {e}")
        return {
            "status": "error",
            "components": [],
            "total_count": 0,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }