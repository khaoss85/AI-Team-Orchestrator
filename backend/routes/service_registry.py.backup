"""
Service Registry API Routes

Provides REST endpoints for service discovery, health monitoring, and management.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/services", tags=["service-registry"])

# Create a secondary router for backward compatibility
registry_router = APIRouter(prefix="/service-registry", tags=["service-registry"])

@router.get("/list")
async def list_services(detailed: bool = Query(False, description="Include detailed service information")):
    """List all registered services"""
    try:
        from services.service_registry import service_registry
        return {
            "services": service_registry.list_services(detailed=detailed),
            "total_count": len(service_registry.services)
        }
    except Exception as e:
        logger.error(f"Error listing services: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_service_stats():
    """Get service registry statistics"""
    try:
        from services.service_registry import get_service_stats
        return get_service_stats()
    except Exception as e:
        logger.error(f"Error getting service stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def service_health_check():
    """Run health check on all services"""
    try:
        from services.service_registry import run_health_check
        
        health_results = run_health_check()
        
        # Count healthy vs unhealthy services
        healthy_count = sum(1 for result in health_results.values() if result["healthy"])
        total_count = len(health_results)
        unhealthy_count = total_count - healthy_count
        
        overall_status = "healthy" if unhealthy_count == 0 else "degraded" if unhealthy_count < total_count / 2 else "unhealthy"
        
        return {
            "overall_status": overall_status,
            "healthy_services": healthy_count,
            "unhealthy_services": unhealthy_count,
            "total_services": total_count,
            "services": health_results
        }
    except Exception as e:
        logger.error(f"Error running health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/service/{service_name}")
async def get_service_info(service_name: str):
    """Get detailed information about a specific service"""
    try:
        from services.service_registry import get_service_info
        
        service_info = get_service_info(service_name)
        if not service_info:
            raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
        
        return {
            "name": service_info.name,
            "module_path": service_info.module_path,
            "category": service_info.category.value,
            "status": service_info.status.value,
            "description": service_info.description,
            "dependencies": service_info.dependencies,
            "dependent_modules": service_info.dependent_modules,
            "owner": service_info.owner,
            "health_status": service_info.health_status,
            "error_count": service_info.error_count,
            "last_health_check": service_info.last_health_check.isoformat() if service_info.last_health_check else None,
            "metadata": service_info.metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting service info for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/service/{service_name}/health")
async def check_service_health(service_name: str):
    """Check health of a specific service"""
    try:
        from services.service_registry import check_service_health
        
        healthy, message = check_service_health(service_name)
        
        return {
            "service_name": service_name,
            "healthy": healthy,
            "message": message,
            "checked_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error checking health for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories/{category}")
async def get_services_by_category(category: str):
    """Get all services in a specific category"""
    try:
        from services.service_registry import service_registry, ServiceCategory
        
        # Validate category
        try:
            service_category = ServiceCategory(category)
        except ValueError:
            valid_categories = [cat.value for cat in ServiceCategory]
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid category '{category}'. Valid categories: {valid_categories}"
            )
        
        services = service_registry.get_services_by_category(service_category)
        
        return {
            "category": category,
            "service_count": len(services),
            "services": [
                {
                    "name": service.name,
                    "status": service.status.value,
                    "description": service.description,
                    "owner": service.owner
                }
                for service in services
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting services by category {category}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{status}")
async def get_services_by_status(status: str):
    """Get all services with a specific status"""
    try:
        from services.service_registry import service_registry, ServiceStatus
        
        # Validate status
        try:
            service_status = ServiceStatus(status)
        except ValueError:
            valid_statuses = [stat.value for stat in ServiceStatus]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status '{status}'. Valid statuses: {valid_statuses}"
            )
        
        services = service_registry.get_services_by_status(service_status)
        
        return {
            "status": status,
            "service_count": len(services),
            "services": [
                {
                    "name": service.name,
                    "category": service.category.value,
                    "description": service.description,
                    "owner": service.owner
                }
                for service in services
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting services by status {status}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/discover")
async def discover_unregistered_services():
    """Auto-discover services that exist but are not registered"""
    try:
        from services.service_registry import service_registry
        
        discovered = service_registry.discover_services()
        
        return {
            "discovered_services": discovered,
            "count": len(discovered),
            "recommendation": "Consider registering these services in the service registry"
        }
    except Exception as e:
        logger.error(f"Error discovering services: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Add required imports
from datetime import datetime

# Add backward compatibility endpoint
@registry_router.get("/")
async def get_service_registry_compat():
    """Backward compatibility endpoint for service registry"""
    try:
        from services.service_registry import service_registry
        
        services = service_registry.list_services(detailed=True)
        active_services = [s for s in services if s.get("status") == "active"]
        
        return {
            "status": "success",
            "active_services": active_services,
            "total_services": len(services),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting service registry: {e}")
        return {
            "status": "error",
            "active_services": [],
            "total_services": 0,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }