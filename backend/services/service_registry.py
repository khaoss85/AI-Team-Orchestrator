"""
Service Registry - Programmatic service management for AI Team Orchestrator

Provides centralized service discovery, health monitoring, and dependency tracking.
"""

import os
import importlib
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    """Service status levels"""
    ACTIVE = "active"
    LIMITED_USE = "limited_use"
    NEEDS_REVIEW = "needs_review"
    DEPRECATED = "deprecated"
    FAILED = "failed"

class ServiceCategory(Enum):
    """Service categories"""
    CORE_SYSTEM = "core_system"
    QUALITY_VALIDATION = "quality_validation"
    ASSET_PROCESSING = "asset_processing"
    MEMORY_INTELLIGENCE = "memory_intelligence"
    ORCHESTRATION = "orchestration"
    MONITORING = "monitoring"
    EXPERIMENTAL = "experimental"

@dataclass
class ServiceInfo:
    """Information about a registered service"""
    name: str
    module_path: str
    category: ServiceCategory
    status: ServiceStatus
    description: str
    dependencies: List[str] = field(default_factory=list)
    dependent_modules: List[str] = field(default_factory=list)
    owner: str = "unknown"
    last_health_check: Optional[datetime] = None
    health_status: str = "unknown"
    import_count: int = 0
    error_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

class ServiceRegistry:
    """Central registry for managing services"""
    
    def __init__(self):
        self.services: Dict[str, ServiceInfo] = {}
        self.services_dir = Path(__file__).parent
        self._initialize_core_services()
        
    def _initialize_core_services(self):
        """Initialize registry with known core services"""
        
        # Core System Services
        self.register_service(
            "adaptive_task_orchestration_engine",
            ServiceCategory.ORCHESTRATION,
            ServiceStatus.ACTIVE,
            "Task optimization and skip rate management",
            dependencies=["executor", "task_analyzer"],
            owner="Core System"
        )
        
        self.register_service(
            "workflow_orchestrator", 
            ServiceCategory.ORCHESTRATION,
            ServiceStatus.ACTIVE,
            "Workflow coordination and management",
            dependencies=["executor", "automated_goal_monitor"],
            owner="Orchestration"
        )
        
        self.register_service(
            "memory_system",
            ServiceCategory.MEMORY_INTELLIGENCE,
            ServiceStatus.ACTIVE,
            "Context storage, retrieval, and insights",
            dependencies=["multiple"],
            owner="Memory"
        )
        
        self.register_service(
            "universal_ai_pipeline_engine",
            ServiceCategory.CORE_SYSTEM,
            ServiceStatus.ACTIVE,
            "Central AI operations hub",
            dependencies=["multiple_services"],
            owner="AI Core"
        )
        
        self.register_service(
            "automatic_quality_trigger",
            ServiceCategory.QUALITY_VALIDATION,
            ServiceStatus.ACTIVE,
            "Automated quality validation triggers",
            dependencies=["unified_orchestrator", "deliverable_pipeline", "main"],
            owner="Quality System"
        )
        
        # Asset Processing Services
        self.register_service(
            "asset_requirements_generator",
            ServiceCategory.ASSET_PROCESSING,
            ServiceStatus.ACTIVE,
            "Asset requirement generation from goals",
            dependencies=["multiple_routes", "asset_system"],
            owner="Asset System"
        )
        
        self.register_service(
            "asset_artifact_processor",
            ServiceCategory.ASSET_PROCESSING,
            ServiceStatus.ACTIVE,
            "Asset artifact processing and management",
            dependencies=["asset_system_integration", "tests"],
            owner="Asset System"
        )
        
        # Quality Services
        self.register_service(
            "ai_quality_gate_engine",
            ServiceCategory.QUALITY_VALIDATION,
            ServiceStatus.ACTIVE,
            "AI-driven quality gates and validation",
            dependencies=["asset_system", "optimization", "tests"],
            owner="Quality System"
        )
        
        # Monitoring Services
        self.register_service(
            "system_telemetry_monitor",
            ServiceCategory.MONITORING,
            ServiceStatus.ACTIVE,
            "System-wide monitoring and telemetry",
            dependencies=["executor", "routes"],
            owner="Monitoring"
        )
        
        self.register_service(
            "workspace_health_manager",
            ServiceCategory.MONITORING,
            ServiceStatus.ACTIVE,
            "Workspace health monitoring",
            dependencies=["executor", "automated_goal_monitor"],
            owner="Monitoring"
        )
        
        # Limited Use Services
        self.register_service(
            "memory_enhanced_ai_asset_generator",
            ServiceCategory.ASSET_PROCESSING,
            ServiceStatus.LIMITED_USE,
            "Memory-aware asset content generation",
            dependencies=["database", "real_tool_integration_pipeline"],
            owner="Asset System"
        )
        
        self.register_service(
            "real_tool_integration_pipeline",
            ServiceCategory.CORE_SYSTEM,
            ServiceStatus.LIMITED_USE,
            "Real tool integration for AI content generation",
            dependencies=["database"],
            owner="Tool Integration"
        )
        
        # Services Needing Review
        self.register_service(
            "ai_tool_aware_validator",
            ServiceCategory.QUALITY_VALIDATION,
            ServiceStatus.NEEDS_REVIEW,
            "Tool-aware validation logic",
            dependencies=["unknown"],
            owner="Validation"
        )
        
        self.register_service(
            "task_deduplication_manager",
            ServiceCategory.CORE_SYSTEM,
            ServiceStatus.NEEDS_REVIEW,
            "Task deduplication and management",
            dependencies=["unknown"],
            owner="Task Management"
        )
    
    def register_service(self, name: str, category: ServiceCategory, status: ServiceStatus,
                        description: str, dependencies: List[str] = None, 
                        owner: str = "unknown") -> None:
        """Register a new service"""
        
        module_path = f"services.{name}"
        
        service_info = ServiceInfo(
            name=name,
            module_path=module_path,
            category=category,
            status=status,
            description=description,
            dependencies=dependencies or [],
            owner=owner
        )
        
        self.services[name] = service_info
        logger.debug(f"Registered service: {name}")
    
    def get_service(self, name: str) -> Optional[ServiceInfo]:
        """Get service information"""
        return self.services.get(name)
    
    def get_services_by_category(self, category: ServiceCategory) -> List[ServiceInfo]:
        """Get all services in a category"""
        return [service for service in self.services.values() 
                if service.category == category]
    
    def get_services_by_status(self, status: ServiceStatus) -> List[ServiceInfo]:
        """Get all services with a specific status"""
        return [service for service in self.services.values() 
                if service.status == status]
    
    def get_active_services(self) -> List[ServiceInfo]:
        """Get all active services"""
        return self.get_services_by_status(ServiceStatus.ACTIVE)
    
    def get_service_dependencies(self, name: str) -> List[str]:
        """Get dependencies for a service"""
        service = self.get_service(name)
        return service.dependencies if service else []
    
    def check_service_health(self, name: str) -> Tuple[bool, str]:
        """Check if a service can be imported and is healthy"""
        try:
            service = self.get_service(name)
            if not service:
                return False, f"Service {name} not registered"
            
            # Try to import the service
            module = importlib.import_module(service.module_path)
            
            # Update health status
            service.last_health_check = datetime.now()
            service.health_status = "healthy"
            
            return True, "Service is healthy"
            
        except ImportError as e:
            if service:
                service.health_status = "import_error"
                service.error_count += 1
            return False, f"Import error: {e}"
        except Exception as e:
            if service:
                service.health_status = "error"
                service.error_count += 1
            return False, f"Error: {e}"
    
    def run_health_check(self) -> Dict[str, Dict[str, Any]]:
        """Run health check on all services"""
        results = {}
        
        for name in self.services:
            healthy, message = self.check_service_health(name)
            results[name] = {
                "healthy": healthy,
                "message": message,
                "status": self.services[name].status.value,
                "category": self.services[name].category.value
            }
        
        return results
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service registry statistics"""
        total_services = len(self.services)
        
        status_counts = {}
        category_counts = {}
        
        for service in self.services.values():
            status_counts[service.status.value] = status_counts.get(service.status.value, 0) + 1
            category_counts[service.category.value] = category_counts.get(service.category.value, 0) + 1
        
        return {
            "total_services": total_services,
            "status_distribution": status_counts,
            "category_distribution": category_counts,
            "last_updated": datetime.now().isoformat()
        }
    
    def list_services(self, detailed: bool = False) -> List[Dict[str, Any]]:
        """List all services"""
        services_list = []
        
        for service in self.services.values():
            service_data = {
                "name": service.name,
                "category": service.category.value,
                "status": service.status.value,
                "description": service.description,
                "owner": service.owner
            }
            
            if detailed:
                service_data.update({
                    "dependencies": service.dependencies,
                    "health_status": service.health_status,
                    "error_count": service.error_count,
                    "last_health_check": service.last_health_check.isoformat() if service.last_health_check else None
                })
            
            services_list.append(service_data)
        
        return sorted(services_list, key=lambda x: x["name"])
    
    def discover_services(self) -> List[str]:
        """Auto-discover services in the services directory"""
        discovered = []
        
        for file_path in self.services_dir.glob("*.py"):
            if file_path.name.startswith("_") or file_path.name == "service_registry.py":
                continue
                
            service_name = file_path.stem
            if service_name not in self.services:
                discovered.append(service_name)
        
        return discovered

# Global registry instance
service_registry = ServiceRegistry()

# Convenience functions
def get_service_info(name: str) -> Optional[ServiceInfo]:
    """Get information about a service"""
    return service_registry.get_service(name)

def check_service_health(name: str) -> Tuple[bool, str]:
    """Check if a service is healthy"""
    return service_registry.check_service_health(name)

def get_active_services() -> List[ServiceInfo]:
    """Get all active services"""
    return service_registry.get_active_services()

def run_health_check() -> Dict[str, Dict[str, Any]]:
    """Run health check on all services"""
    return service_registry.run_health_check()

def get_service_stats() -> Dict[str, Any]:
    """Get service registry statistics"""
    return service_registry.get_service_stats()

if __name__ == "__main__":
    # Test the service registry
    print("AI Team Orchestrator - Service Registry")
    print("=" * 50)
    
    stats = get_service_stats()
    print(f"Total Services: {stats['total_services']}")
    print(f"Status Distribution: {stats['status_distribution']}")
    
    print("\n📋 Service Health Check:")
    health_results = run_health_check()
    
    for service_name, result in health_results.items():
        status = "✅" if result["healthy"] else "❌"
        print(f"{status} {service_name}: {result['message']}")
    
    print("\n🔍 Auto-discovered services:")
    discovered = service_registry.discover_services()
    for service in discovered:
        print(f"  - {service} (not registered)")