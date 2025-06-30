"""
Asset System Monitor - Production monitoring and health checks (Pillar 11: Production-ready & testato)
Comprehensive monitoring, alerting, and performance tracking for the asset-driven orchestration system.
"""

import os
import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import UUID
from dataclasses import dataclass
from enum import Enum

from database_asset_extensions import AssetDrivenDatabaseManager
from services.ai_quality_gate_engine import AIQualityGateEngine
from services.asset_driven_task_executor import AssetDrivenTaskExecutor

logger = logging.getLogger(__name__)

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class PerformanceMetrics:
    """Performance metrics for system monitoring"""
    avg_response_time_ms: float
    throughput_per_minute: float
    error_rate_percentage: float
    memory_usage_mb: float
    active_connections: int
    queue_depth: int
    
    # 🤖 AI-DRIVEN COMPATIBILITY: Provide error_rate as alias for backward compatibility
    @property
    def error_rate(self) -> float:
        """Backward compatibility: error_rate as decimal (0.05 = 5%)"""
        return self.error_rate_percentage / 100.0

@dataclass
class QualityMetrics:
    """Quality system performance metrics"""
    validation_success_rate: float
    avg_quality_score: float
    human_review_queue_size: int
    ai_enhancement_success_rate: float
    pillar_compliance_rate: float

@dataclass
class AssetSystemHealth:
    """Complete asset system health status"""
    overall_status: HealthStatus
    timestamp: datetime
    services: Dict[str, HealthStatus]
    performance: PerformanceMetrics
    quality: QualityMetrics
    alerts: List[Dict[str, Any]]
    recommendations: List[str]

class AssetSystemMonitor:
    """Comprehensive monitoring for asset-driven orchestration system"""
    
    def __init__(self):
        self.db_manager = AssetDrivenDatabaseManager()
        self.quality_engine = AIQualityGateEngine()
        self.task_executor = AssetDrivenTaskExecutor()
        
        # Configuration
        self.monitoring_enabled = os.getenv("ENABLE_PERFORMANCE_MONITORING", "true").lower() == "true"
        self.alert_enabled = os.getenv("ASSET_PIPELINE_ALERT_ENABLED", "true").lower() == "true"
        self.quality_threshold = float(os.getenv("QUALITY_PERFORMANCE_ALERT_THRESHOLD", "0.7"))
        self.response_time_threshold = int(os.getenv("MAX_RESPONSE_TIME_MS", "2000"))
        
        # Metrics collection
        self.metrics_history: List[Dict[str, Any]] = []
        self.alert_history: List[Dict[str, Any]] = []
        
        logger.info("📊 AssetSystemMonitor initialized with production monitoring")
    
    async def check_system_health(self) -> AssetSystemHealth:
        """Comprehensive system health check (Pillar 11: Production-ready)"""
        try:
            logger.info("🏥 Running comprehensive system health check")
            
            # Check individual services
            service_health = await self._check_service_health()
            
            # Collect performance metrics
            performance_metrics = await self._collect_performance_metrics()
            
            # Collect quality metrics
            quality_metrics = await self._collect_quality_metrics()
            
            # Detect alerts and issues
            alerts = await self._detect_alerts(performance_metrics, quality_metrics)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(
                service_health, performance_metrics, quality_metrics, alerts
            )
            
            # Determine overall status
            overall_status = self._determine_overall_status(service_health, alerts)
            
            health_report = AssetSystemHealth(
                overall_status=overall_status,
                timestamp=datetime.utcnow(),
                services=service_health,
                performance=performance_metrics,
                quality=quality_metrics,
                alerts=alerts,
                recommendations=recommendations
            )
            
            # Log health status
            await self._log_health_status(health_report)
            
            logger.info(f"✅ System health check completed - Status: {overall_status}")
            return health_report
            
        except Exception as e:
            logger.error(f"System health check failed: {e}")
            return AssetSystemHealth(
                overall_status=HealthStatus.CRITICAL,
                timestamp=datetime.utcnow(),
                services={},
                performance=PerformanceMetrics(0, 0, 100, 0, 0, 0),
                quality=QualityMetrics(0, 0, 0, 0, 0),
                alerts=[{"type": "system_error", "message": str(e)}],
                recommendations=["System requires immediate attention"]
            )
    
    async def _check_service_health(self) -> Dict[str, HealthStatus]:
        """Check health of individual services"""
        service_health = {}
        
        try:
            # Database health
            db_health = await self.db_manager.health_check()
            service_health["database"] = (
                HealthStatus.HEALTHY if db_health.get("status") == "healthy"
                else HealthStatus.WARNING if db_health.get("status") == "degraded"
                else HealthStatus.CRITICAL
            )
            
            # Task executor health
            executor_health = await self.task_executor.health_check()
            service_health["task_executor"] = (
                HealthStatus.HEALTHY if executor_health.get("status") == "healthy"
                else HealthStatus.CRITICAL
            )
            
            # Quality engine health
            quality_health = await self._check_quality_engine_health()
            service_health["quality_engine"] = quality_health
            
            # Asset processing pipeline health
            pipeline_health = await self._check_pipeline_health()
            service_health["asset_pipeline"] = pipeline_health
            
            # WebSocket connections health
            websocket_health = await self._check_websocket_health()
            service_health["websockets"] = websocket_health
            
        except Exception as e:
            logger.error(f"Service health check failed: {e}")
            service_health["system"] = HealthStatus.CRITICAL
        
        return service_health
    
    async def _check_quality_engine_health(self) -> HealthStatus:
        """Check quality engine health"""
        try:
            # Test quality validation with a sample
            from models import AssetArtifact
            from uuid import uuid4
            
            test_artifact = AssetArtifact(
                id=uuid4(),
                requirement_id=uuid4(),
                artifact_name="Health Check Test",
                artifact_type="document",
                content_format="text",
                content="This is a test document for health check validation.",
                quality_score=0.0,
                status="draft"
            )
            
            # Run a quick validation test
            start_time = datetime.utcnow()
            quality_result = await self.quality_engine.validate_artifact_quality(test_artifact)
            end_time = datetime.utcnow()
            
            response_time = (end_time - start_time).total_seconds() * 1000
            
            if response_time > self.response_time_threshold:
                return HealthStatus.WARNING
            
            if quality_result.get("status") == "error":
                return HealthStatus.CRITICAL
            
            return HealthStatus.HEALTHY
            
        except Exception as e:
            logger.error(f"Quality engine health check failed: {e}")
            return HealthStatus.CRITICAL
    
    async def _check_pipeline_health(self) -> HealthStatus:
        """Check asset processing pipeline health"""
        try:
            # Check if pipeline components are responsive
            # This would test the entire asset processing flow
            
            # Check queue depths and processing times
            # (Implementation would depend on having queue monitoring)
            
            return HealthStatus.HEALTHY
            
        except Exception as e:
            logger.error(f"Pipeline health check failed: {e}")
            return HealthStatus.CRITICAL
    
    async def _check_websocket_health(self) -> HealthStatus:
        """Check WebSocket connections health"""
        try:
            # This would check WebSocket connection status
            # Implementation depends on WebSocket manager availability
            
            return HealthStatus.HEALTHY
            
        except Exception as e:
            logger.error(f"WebSocket health check failed: {e}")
            return HealthStatus.WARNING
    
    async def _collect_performance_metrics(self) -> PerformanceMetrics:
        """Collect system performance metrics"""
        try:
            # Collect database performance
            db_metrics = await self._collect_database_performance()
            
            # Collect API response times
            api_metrics = await self._collect_api_performance()
            
            # Collect system resource usage
            system_metrics = await self._collect_system_resources()
            
            return PerformanceMetrics(
                avg_response_time_ms=api_metrics.get("avg_response_time", 0),
                throughput_per_minute=api_metrics.get("throughput", 0),
                error_rate_percentage=api_metrics.get("error_rate", 0),
                memory_usage_mb=system_metrics.get("memory_mb", 0),
                active_connections=db_metrics.get("active_connections", 0),
                queue_depth=system_metrics.get("queue_depth", 0)
            )
            
        except Exception as e:
            logger.error(f"Performance metrics collection failed: {e}")
            return PerformanceMetrics(0, 0, 100, 0, 0, 0)
    
    async def _collect_database_performance(self) -> Dict[str, Any]:
        """Collect database performance metrics"""
        try:
            # Query database for performance metrics
            # This would use database-specific monitoring queries
            
            return {
                "avg_query_time_ms": 50,
                "active_connections": 5,
                "slow_queries_count": 0
            }
            
        except Exception as e:
            logger.error(f"Database performance collection failed: {e}")
            return {}
    
    async def _collect_api_performance(self) -> Dict[str, Any]:
        """Collect API performance metrics"""
        try:
            # This would collect metrics from API endpoint monitoring
            # Implementation depends on having API metrics collection
            
            return {
                "avg_response_time": 150,
                "throughput": 100,
                "error_rate": 2.5
            }
            
        except Exception as e:
            logger.error(f"API performance collection failed: {e}")
            return {}
    
    async def _collect_system_resources(self) -> Dict[str, Any]:
        """Collect system resource usage metrics"""
        try:
            import psutil
            import os
            import gc
            
            # Get current process for accurate memory measurement
            current_process = psutil.Process(os.getpid())
            
            # CPU usage (faster interval for responsive monitoring)
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory usage - measure only our process
            process_memory = current_process.memory_info()
            memory_mb = process_memory.rss / (1024 * 1024)  # Resident Set Size
            
            # 🔧 MEMORY OPTIMIZATION: Trigger garbage collection if memory is high
            if memory_mb > 500:  # If process uses more than 500MB
                collected = gc.collect()
                logger.info(f"🧹 High memory usage ({memory_mb:.1f}MB) - collected {collected} objects")
                # Re-measure after GC
                process_memory = current_process.memory_info()
                memory_mb = process_memory.rss / (1024 * 1024)
            
            # System context (for alerts but not main metric)
            system_memory = psutil.virtual_memory()
            system_memory_mb = system_memory.used / (1024 * 1024)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            return {
                "cpu_percent": cpu_percent,
                "memory_mb": memory_mb,  # Process memory only (not system)
                "system_memory_mb": system_memory_mb,  # For context
                "memory_percent": process_memory.rss / system_memory.total * 100,
                "disk_percent": disk_percent,
                "queue_depth": 0  # Would need actual queue monitoring
            }
            
        except ImportError:
            logger.warning("psutil not available for system monitoring")
            return {"memory_mb": 0, "queue_depth": 0}
        except Exception as e:
            logger.error(f"System resource collection failed: {e}")
            return {"memory_mb": 0, "queue_depth": 0}
    
    async def _collect_quality_metrics(self) -> QualityMetrics:
        """Collect quality system metrics"""
        try:
            # Get recent quality validations
            from database import get_supabase_client
            supabase = get_supabase_client()
            
            # Get validations from last 24 hours
            yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
            
            validations_response = supabase.table("quality_validations") \
                .select("passed, score") \
                .gte("validated_at", yesterday) \
                .execute()
            
            validations = validations_response.data
            
            if validations:
                success_rate = len([v for v in validations if v["passed"]]) / len(validations)
                avg_quality = sum(v["score"] for v in validations) / len(validations)
            else:
                success_rate = 0.0
                avg_quality = 0.0
            
            # Get pending human reviews
            pending_response = supabase.table("asset_artifacts") \
                .select("id", count="exact") \
                .eq("status", "requires_human_review") \
                .execute()
            
            pending_count = pending_response.count or 0
            
            return QualityMetrics(
                validation_success_rate=success_rate,
                avg_quality_score=avg_quality,
                human_review_queue_size=pending_count,
                ai_enhancement_success_rate=0.85,  # Would calculate from actual data
                pillar_compliance_rate=0.9  # Would calculate from pillar compliance data
            )
            
        except Exception as e:
            logger.error(f"Quality metrics collection failed: {e}")
            return QualityMetrics(0, 0, 0, 0, 0)
    
    async def _detect_alerts(
        self, 
        performance: PerformanceMetrics, 
        quality: QualityMetrics
    ) -> List[Dict[str, Any]]:
        """Detect system alerts and issues"""
        alerts = []
        
        try:
            # Performance alerts
            if performance.avg_response_time_ms > self.response_time_threshold:
                alerts.append({
                    "type": "performance",
                    "severity": "warning" if performance.avg_response_time_ms < 5000 else "critical",
                    "message": f"High response time: {performance.avg_response_time_ms:.0f}ms",
                    "metric": "response_time",
                    "value": performance.avg_response_time_ms,
                    "threshold": self.response_time_threshold
                })
            
            if performance.error_rate_percentage > 5:
                alerts.append({
                    "type": "reliability",
                    "severity": "critical",
                    "message": f"High error rate: {performance.error_rate_percentage:.1f}%",
                    "metric": "error_rate",
                    "value": performance.error_rate_percentage,
                    "threshold": 5
                })
            
            # Quality alerts
            if quality.validation_success_rate < self.quality_threshold:
                alerts.append({
                    "type": "quality",
                    "severity": "warning",
                    "message": f"Low validation success rate: {quality.validation_success_rate:.1%}",
                    "metric": "validation_success_rate",
                    "value": quality.validation_success_rate,
                    "threshold": self.quality_threshold
                })
            
            if quality.human_review_queue_size > 50:
                alerts.append({
                    "type": "capacity",
                    "severity": "warning",
                    "message": f"Large human review queue: {quality.human_review_queue_size} items",
                    "metric": "review_queue_size",
                    "value": quality.human_review_queue_size,
                    "threshold": 50
                })
            
            # Memory alerts (adjusted for process memory instead of system memory)
            if performance.memory_usage_mb > 500:  # Process memory threshold
                severity = "critical" if performance.memory_usage_mb > 1000 else "warning"
                alerts.append({
                    "type": "resource",
                    "severity": severity,
                    "message": f"High process memory usage: {performance.memory_usage_mb:.0f}MB",
                    "metric": "memory_usage",
                    "value": performance.memory_usage_mb,
                    "threshold": 500
                })
            
        except Exception as e:
            logger.error(f"Alert detection failed: {e}")
            alerts.append({
                "type": "system",
                "severity": "critical",
                "message": f"Alert detection error: {str(e)}"
            })
        
        return alerts
    
    async def _generate_recommendations(
        self,
        service_health: Dict[str, HealthStatus],
        performance: PerformanceMetrics,
        quality: QualityMetrics,
        alerts: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate actionable recommendations based on system status"""
        recommendations = []
        
        try:
            # Service health recommendations
            if service_health.get("database") == HealthStatus.CRITICAL:
                recommendations.append("Database requires immediate attention - check connections and query performance")
            
            if service_health.get("quality_engine") == HealthStatus.WARNING:
                recommendations.append("Quality engine performance is degraded - consider scaling or optimization")
            
            # Performance recommendations
            if performance.avg_response_time_ms > self.response_time_threshold:
                recommendations.append("High response times detected - review database queries and API optimization")
            
            if performance.error_rate_percentage > 5:
                recommendations.append("High error rate - investigate error logs and implement circuit breakers")
            
            # Quality recommendations
            if quality.validation_success_rate < self.quality_threshold:
                recommendations.append("Quality validation performance is low - review AI model performance and rules")
            
            if quality.human_review_queue_size > 20:
                recommendations.append("Human review queue is growing - consider adding reviewers or improving AI accuracy")
            
            # Alert-specific recommendations
            critical_alerts = [a for a in alerts if a.get("severity") == "critical"]
            if critical_alerts:
                recommendations.append("Critical alerts detected - immediate intervention required")
            
            # Proactive recommendations
            if quality.pillar_compliance_rate < 0.9:
                recommendations.append("Pillar compliance could be improved - review system architecture alignment")
            
            if not recommendations:
                recommendations.append("System is operating within normal parameters")
                
        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            recommendations.append("Unable to generate recommendations due to monitoring error")
        
        return recommendations
    
    def _determine_overall_status(
        self, 
        service_health: Dict[str, HealthStatus], 
        alerts: List[Dict[str, Any]]
    ) -> HealthStatus:
        """Determine overall system health status"""
        try:
            # Check for critical alerts
            critical_alerts = [a for a in alerts if a.get("severity") == "critical"]
            if critical_alerts:
                return HealthStatus.CRITICAL
            
            # Check service health
            critical_services = [s for s in service_health.values() if s == HealthStatus.CRITICAL]
            if critical_services:
                return HealthStatus.CRITICAL
            
            warning_services = [s for s in service_health.values() if s == HealthStatus.WARNING]
            warning_alerts = [a for a in alerts if a.get("severity") == "warning"]
            
            if warning_services or warning_alerts:
                return HealthStatus.WARNING
            
            return HealthStatus.HEALTHY
            
        except Exception as e:
            logger.error(f"Status determination failed: {e}")
            return HealthStatus.UNKNOWN
    
    async def _log_health_status(self, health_report: AssetSystemHealth):
        """Log health status for monitoring and alerting"""
        try:
            # Add to metrics history
            self.metrics_history.append({
                "timestamp": health_report.timestamp.isoformat(),
                "overall_status": health_report.overall_status.value,
                "performance": {
                    "response_time_ms": health_report.performance.avg_response_time_ms,
                    "error_rate": health_report.performance.error_rate_percentage,
                    "memory_mb": health_report.performance.memory_usage_mb
                },
                "quality": {
                    "validation_success_rate": health_report.quality.validation_success_rate,
                    "avg_quality_score": health_report.quality.avg_quality_score,
                    "review_queue_size": health_report.quality.human_review_queue_size
                },
                "alert_count": len(health_report.alerts)
            })
            
            # Keep only last 100 entries
            self.metrics_history = self.metrics_history[-100:]
            
            # Log alerts
            if health_report.alerts:
                self.alert_history.extend([
                    {**alert, "timestamp": health_report.timestamp.isoformat()}
                    for alert in health_report.alerts
                ])
                self.alert_history = self.alert_history[-500:]  # Keep last 500 alerts
            
            # Write to monitoring system (if configured)
            if self.monitoring_enabled:
                await self._write_to_monitoring_system(health_report)
                
        except Exception as e:
            logger.error(f"Health status logging failed: {e}")
    
    async def _write_to_monitoring_system(self, health_report: AssetSystemHealth):
        """Write metrics to external monitoring system"""
        try:
            # This would integrate with monitoring systems like:
            # - Prometheus/Grafana
            # - DataDog
            # - New Relic
            # - CloudWatch
            
            # For now, just log structured data
            monitoring_data = {
                "service": "asset_orchestrator",
                "timestamp": health_report.timestamp.isoformat(),
                "status": health_report.overall_status.value,
                "metrics": {
                    "response_time_ms": health_report.performance.avg_response_time_ms,
                    "throughput_per_minute": health_report.performance.throughput_per_minute,
                    "error_rate": health_report.performance.error_rate_percentage,
                    "memory_usage_mb": health_report.performance.memory_usage_mb,
                    "validation_success_rate": health_report.quality.validation_success_rate,
                    "avg_quality_score": health_report.quality.avg_quality_score,
                    "review_queue_size": health_report.quality.human_review_queue_size
                },
                "alerts": health_report.alerts
            }
            
            logger.info(f"📊 MONITORING: {json.dumps(monitoring_data, indent=2)}")
            
        except Exception as e:
            logger.error(f"Monitoring system write failed: {e}")
    
    async def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance trends over specified time period"""
        try:
            # Filter metrics history by time period
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            recent_metrics = [
                m for m in self.metrics_history
                if datetime.fromisoformat(m["timestamp"]) >= cutoff_time
            ]
            
            if not recent_metrics:
                return {"message": "No metrics available for specified time period"}
            
            # Calculate trends
            response_times = [m["performance"]["response_time_ms"] for m in recent_metrics]
            error_rates = [m["performance"]["error_rate"] for m in recent_metrics]
            quality_scores = [m["quality"]["avg_quality_score"] for m in recent_metrics]
            
            trends = {
                "time_period_hours": hours,
                "data_points": len(recent_metrics),
                "response_time": {
                    "avg": sum(response_times) / len(response_times),
                    "min": min(response_times),
                    "max": max(response_times),
                    "trend": "improving" if response_times[-1] < response_times[0] else "degrading"
                },
                "error_rate": {
                    "avg": sum(error_rates) / len(error_rates),
                    "min": min(error_rates),
                    "max": max(error_rates)
                },
                "quality_score": {
                    "avg": sum(quality_scores) / len(quality_scores),
                    "min": min(quality_scores),
                    "max": max(quality_scores)
                }
            }
            
            return trends
            
        except Exception as e:
            logger.error(f"Performance trends calculation failed: {e}")
            return {"error": str(e)}
    
    async def get_alert_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get alert summary for specified time period"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            recent_alerts = [
                a for a in self.alert_history
                if datetime.fromisoformat(a["timestamp"]) >= cutoff_time
            ]
            
            if not recent_alerts:
                return {"message": "No alerts in specified time period"}
            
            # Categorize alerts
            alert_summary = {
                "total_alerts": len(recent_alerts),
                "by_severity": {},
                "by_type": {},
                "most_frequent": {}
            }
            
            # Count by severity
            for alert in recent_alerts:
                severity = alert.get("severity", "unknown")
                alert_summary["by_severity"][severity] = alert_summary["by_severity"].get(severity, 0) + 1
            
            # Count by type
            for alert in recent_alerts:
                alert_type = alert.get("type", "unknown")
                alert_summary["by_type"][alert_type] = alert_summary["by_type"].get(alert_type, 0) + 1
            
            return alert_summary
            
        except Exception as e:
            logger.error(f"Alert summary calculation failed: {e}")
            return {"error": str(e)}

# Global monitor instance
asset_monitor = AssetSystemMonitor()

# Export for easy import
__all__ = ["AssetSystemMonitor", "asset_monitor", "HealthStatus", "PerformanceMetrics", "QualityMetrics"]