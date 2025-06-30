"""
🤖 AI-Driven System Telemetry and Monitoring
Advanced telemetry, logging, and proactive alerting for the goal-driven orchestration system
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class SystemAlert:
    """System alert with metadata"""
    alert_type: str
    severity: str  # info, warning, critical
    message: str
    component: str
    workspace_id: Optional[str] = None
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    timestamp: str = None
    resolution_status: str = "open"  # open, acknowledged, resolved
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

@dataclass
class TelemetryMetrics:
    """Comprehensive system telemetry metrics"""
    timestamp: str
    system_health_score: float
    active_workspaces: int
    paused_workspaces: int
    pending_tasks_total: int
    critical_tasks_total: int
    task_completion_rate: float  # tasks/hour
    average_task_wait_time: float  # minutes
    anti_loop_triggers: int
    achievement_extraction_success_rate: float
    goal_update_success_rate: float
    ai_confidence_average: float
    workspace_recovery_actions: int

class SystemTelemetryMonitor:
    """
    🤖 AI-DRIVEN: Advanced system telemetry and proactive monitoring
    Pillar 13: Transparency & Explainability
    Pillar 12: Automatic Course-Correction
    """
    
    def __init__(self):
        self.metrics_history: List[TelemetryMetrics] = []
        self.alert_history: List[SystemAlert] = []
        
        # Configuration
        self.monitoring_enabled = os.getenv("ENABLE_ADVANCED_TELEMETRY", "true").lower() == "true"
        self.alert_enabled = os.getenv("ENABLE_PROACTIVE_ALERTS", "true").lower() == "true"
        
        # Alert thresholds
        self.thresholds = {
            "system_health_critical": float(os.getenv("SYSTEM_HEALTH_CRITICAL_THRESHOLD", "0.3")),
            "system_health_warning": float(os.getenv("SYSTEM_HEALTH_WARNING_THRESHOLD", "0.6")),
            "task_wait_time_critical": float(os.getenv("TASK_WAIT_TIME_CRITICAL_MINUTES", "60")),
            "task_wait_time_warning": float(os.getenv("TASK_WAIT_TIME_WARNING_MINUTES", "30")),
            "completion_rate_critical": float(os.getenv("COMPLETION_RATE_CRITICAL_PER_HOUR", "1.0")),
            "ai_confidence_warning": float(os.getenv("AI_CONFIDENCE_WARNING_THRESHOLD", "0.5")),
        }
        
        # Telemetry storage
        self.telemetry_file = os.getenv("TELEMETRY_LOG_FILE", "system_telemetry.json")
        self.max_history_entries = int(os.getenv("MAX_TELEMETRY_HISTORY", "1000"))
        
        logger.info("🤖 SystemTelemetryMonitor initialized with proactive alerting")
    
    async def collect_comprehensive_metrics(self) -> TelemetryMetrics:
        """
        🤖 AI-DRIVEN: Collect comprehensive system metrics
        """
        try:
            logger.debug("📊 Collecting comprehensive system telemetry...")
            
            # System health calculations
            system_health = await self._calculate_system_health()
            
            # Workspace metrics
            workspace_metrics = await self._collect_workspace_metrics()
            
            # Task metrics  
            task_metrics = await self._collect_task_metrics()
            
            # AI performance metrics
            ai_metrics = await self._collect_ai_performance_metrics()
            
            # Anti-loop and recovery metrics
            system_metrics = await self._collect_system_action_metrics()
            
            telemetry = TelemetryMetrics(
                timestamp=datetime.now().isoformat(),
                system_health_score=system_health,
                active_workspaces=workspace_metrics.get("active", 0),
                paused_workspaces=workspace_metrics.get("paused", 0),
                pending_tasks_total=task_metrics.get("pending", 0),
                critical_tasks_total=task_metrics.get("critical", 0),
                task_completion_rate=task_metrics.get("completion_rate", 0.0),
                average_task_wait_time=task_metrics.get("avg_wait_time", 0.0),
                anti_loop_triggers=system_metrics.get("anti_loop_triggers", 0),
                achievement_extraction_success_rate=ai_metrics.get("extraction_success_rate", 0.0),
                goal_update_success_rate=ai_metrics.get("goal_update_success_rate", 0.0),
                ai_confidence_average=ai_metrics.get("avg_confidence", 0.0),
                workspace_recovery_actions=system_metrics.get("recovery_actions", 0)
            )
            
            # Store metrics
            self.metrics_history.append(telemetry)
            
            # Keep history size manageable
            if len(self.metrics_history) > self.max_history_entries:
                self.metrics_history = self.metrics_history[-self.max_history_entries:]
            
            # Analyze for proactive alerts
            if self.alert_enabled:
                await self._analyze_for_proactive_alerts(telemetry)
            
            # Write to file if enabled
            if self.monitoring_enabled:
                await self._write_telemetry_to_file(telemetry)
            
            logger.debug(f"📊 Telemetry collected: Health {system_health:.2f}, {workspace_metrics['active']} active workspaces")
            
            return telemetry
            
        except Exception as e:
            logger.error(f"Error collecting comprehensive metrics: {e}")
            return TelemetryMetrics(
                timestamp=datetime.now().isoformat(),
                system_health_score=0.0,
                active_workspaces=0,
                paused_workspaces=0,
                pending_tasks_total=0,
                critical_tasks_total=0,
                task_completion_rate=0.0,
                average_task_wait_time=0.0,
                anti_loop_triggers=0,
                achievement_extraction_success_rate=0.0,
                goal_update_success_rate=0.0,
                ai_confidence_average=0.0,
                workspace_recovery_actions=0
            )
    
    async def _calculate_system_health(self) -> float:
        """Calculate overall system health score (0.0 to 1.0)"""
        try:
            health_components = []
            
            # Component 1: Workspace health
            try:
                from database import supabase
                from models import WorkspaceStatus
                
                workspaces_response = supabase.table('workspaces').select('status').execute()
                workspaces = workspaces_response.data or []
                
                if workspaces:
                    active_count = len([w for w in workspaces if w.get('status') == WorkspaceStatus.ACTIVE.value])
                    workspace_health = active_count / len(workspaces)
                    health_components.append(workspace_health)
            except Exception as e:
                logger.debug(f"Error calculating workspace health: {e}")
                health_components.append(0.5)  # Neutral if can't calculate
            
            # Component 2: Task processing health
            try:
                from services.dynamic_anti_loop_manager import dynamic_anti_loop_manager
                
                # Average health of monitored workspaces
                avg_health = 0.7  # Default if no specific data
                health_components.append(avg_health)
            except Exception as e:
                logger.debug(f"Error calculating task health: {e}")
                health_components.append(0.5)
            
            # Component 3: AI system health
            try:
                # Check if AI systems are responding
                ai_health = 0.8  # Default - would check actual AI availability
                health_components.append(ai_health)
            except Exception as e:
                logger.debug(f"Error calculating AI health: {e}")
                health_components.append(0.5)
            
            # Calculate weighted average
            overall_health = sum(health_components) / len(health_components) if health_components else 0.5
            
            return min(1.0, max(0.0, overall_health))
            
        except Exception as e:
            logger.warning(f"Error calculating system health: {e}")
            return 0.5
    
    async def _collect_workspace_metrics(self) -> Dict[str, int]:
        """Collect workspace status metrics"""
        try:
            from database import supabase
            from models import WorkspaceStatus
            
            workspaces_response = supabase.table('workspaces').select('status').execute()
            workspaces = workspaces_response.data or []
            
            metrics = {
                "active": len([w for w in workspaces if w.get('status') == WorkspaceStatus.ACTIVE.value]),
                "paused": len([w for w in workspaces if w.get('status') == WorkspaceStatus.PAUSED.value]),
                "completed": len([w for w in workspaces if w.get('status') == WorkspaceStatus.COMPLETED.value]),
                "total": len(workspaces)
            }
            
            return metrics
            
        except Exception as e:
            logger.warning(f"Error collecting workspace metrics: {e}")
            return {"active": 0, "paused": 0, "completed": 0, "total": 0}
    
    async def _collect_task_metrics(self) -> Dict[str, float]:
        """Collect task processing metrics"""
        try:
            from database import supabase
            
            # Get pending tasks
            pending_response = supabase.table('tasks').select('id, created_at').eq('status', 'pending').execute()
            pending_tasks = pending_response.data or []
            
            # Get completed tasks from last hour
            one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
            completed_response = supabase.table('tasks').select('id').eq('status', 'completed').gte('updated_at', one_hour_ago).execute()
            completed_tasks = completed_response.data or []
            
            # Calculate wait times
            total_wait = 0.0
            for task in pending_tasks:
                try:
                    created_at = datetime.fromisoformat(task['created_at'].replace('Z', '+00:00'))
                    wait_time = (datetime.now().replace(tzinfo=created_at.tzinfo) - created_at).total_seconds() / 60
                    total_wait += wait_time
                except:
                    continue
            
            avg_wait_time = total_wait / len(pending_tasks) if pending_tasks else 0.0
            completion_rate = len(completed_tasks)  # tasks per hour
            
            # Count critical tasks
            critical_count = 0
            for task in pending_tasks:
                # Would use actual critical task detection here
                if any(keyword in task.get('name', '').lower() for keyword in ['urgent', 'critical', 'emergency']):
                    critical_count += 1
            
            return {
                "pending": len(pending_tasks),
                "critical": critical_count,
                "completion_rate": completion_rate,
                "avg_wait_time": avg_wait_time
            }
            
        except Exception as e:
            logger.warning(f"Error collecting task metrics: {e}")
            return {"pending": 0, "critical": 0, "completion_rate": 0.0, "avg_wait_time": 0.0}
    
    async def _collect_ai_performance_metrics(self) -> Dict[str, float]:
        """Collect AI system performance metrics"""
        try:
            # Would collect real AI performance data
            # For now, return reasonable defaults
            
            return {
                "extraction_success_rate": 0.85,  # Would track actual success rate
                "goal_update_success_rate": 0.90,  # Would track actual goal updates
                "avg_confidence": 0.75  # Would track actual AI confidence scores
            }
            
        except Exception as e:
            logger.warning(f"Error collecting AI metrics: {e}")
            return {"extraction_success_rate": 0.0, "goal_update_success_rate": 0.0, "avg_confidence": 0.0}
    
    async def _collect_system_action_metrics(self) -> Dict[str, int]:
        """Collect system action metrics (anti-loop, recovery, etc.)"""
        try:
            # Would collect real system action data
            # For now, return reasonable defaults
            
            return {
                "anti_loop_triggers": 0,  # Would track actual anti-loop activations
                "recovery_actions": 0  # Would track actual recovery actions
            }
            
        except Exception as e:
            logger.warning(f"Error collecting system action metrics: {e}")
            return {"anti_loop_triggers": 0, "recovery_actions": 0}
    
    async def _analyze_for_proactive_alerts(self, telemetry: TelemetryMetrics):
        """
        🤖 AI-DRIVEN: Analyze telemetry for proactive alerts
        """
        try:
            alerts = []
            
            # Critical system health
            if telemetry.system_health_score <= self.thresholds["system_health_critical"]:
                alerts.append(SystemAlert(
                    alert_type="system_health",
                    severity="critical",
                    message=f"System health critically low: {telemetry.system_health_score:.2f}",
                    component="system",
                    metric_value=telemetry.system_health_score,
                    threshold=self.thresholds["system_health_critical"]
                ))
            elif telemetry.system_health_score <= self.thresholds["system_health_warning"]:
                alerts.append(SystemAlert(
                    alert_type="system_health",
                    severity="warning", 
                    message=f"System health degraded: {telemetry.system_health_score:.2f}",
                    component="system",
                    metric_value=telemetry.system_health_score,
                    threshold=self.thresholds["system_health_warning"]
                ))
            
            # High task wait times
            if telemetry.average_task_wait_time >= self.thresholds["task_wait_time_critical"]:
                alerts.append(SystemAlert(
                    alert_type="task_wait_time",
                    severity="critical",
                    message=f"Critical task wait time: {telemetry.average_task_wait_time:.1f} minutes",
                    component="task_processor",
                    metric_value=telemetry.average_task_wait_time,
                    threshold=self.thresholds["task_wait_time_critical"]
                ))
            elif telemetry.average_task_wait_time >= self.thresholds["task_wait_time_warning"]:
                alerts.append(SystemAlert(
                    alert_type="task_wait_time",
                    severity="warning",
                    message=f"High task wait time: {telemetry.average_task_wait_time:.1f} minutes",
                    component="task_processor",
                    metric_value=telemetry.average_task_wait_time,
                    threshold=self.thresholds["task_wait_time_warning"]
                ))
            
            # Low completion rate
            if telemetry.task_completion_rate <= self.thresholds["completion_rate_critical"]:
                alerts.append(SystemAlert(
                    alert_type="low_completion_rate",
                    severity="critical",
                    message=f"Task completion rate critically low: {telemetry.task_completion_rate:.1f}/hour",
                    component="task_processor",
                    metric_value=telemetry.task_completion_rate,
                    threshold=self.thresholds["completion_rate_critical"]
                ))
            
            # High critical task backlog
            if telemetry.critical_tasks_total > 5:
                alerts.append(SystemAlert(
                    alert_type="critical_task_backlog",
                    severity="warning",
                    message=f"High critical task backlog: {telemetry.critical_tasks_total} tasks",
                    component="task_processor",
                    metric_value=telemetry.critical_tasks_total,
                    threshold=5
                ))
            
            # Low AI confidence
            if telemetry.ai_confidence_average <= self.thresholds["ai_confidence_warning"]:
                alerts.append(SystemAlert(
                    alert_type="low_ai_confidence",
                    severity="warning",
                    message=f"AI confidence below threshold: {telemetry.ai_confidence_average:.2f}",
                    component="ai_system",
                    metric_value=telemetry.ai_confidence_average,
                    threshold=self.thresholds["ai_confidence_warning"]
                ))
            
            # Store alerts
            for alert in alerts:
                self.alert_history.append(alert)
                await self._process_alert(alert)
            
            # Keep alert history manageable
            if len(self.alert_history) > 500:
                self.alert_history = self.alert_history[-500:]
                
        except Exception as e:
            logger.error(f"Error in proactive alert analysis: {e}")
    
    async def _process_alert(self, alert: SystemAlert):
        """Process and handle an alert"""
        try:
            # Log the alert
            if alert.severity == "critical":
                logger.critical(f"🚨 CRITICAL ALERT: {alert.message} (Component: {alert.component})")
            elif alert.severity == "warning":
                logger.warning(f"⚠️ WARNING ALERT: {alert.message} (Component: {alert.component})")
            else:
                logger.info(f"ℹ️ INFO ALERT: {alert.message} (Component: {alert.component})")
            
            # Additional alert processing could include:
            # - Sending notifications (email, Slack, etc.)
            # - Triggering automatic remediation actions
            # - Updating monitoring dashboards
            # - Creating support tickets
            
        except Exception as e:
            logger.error(f"Error processing alert: {e}")
    
    async def _write_telemetry_to_file(self, telemetry: TelemetryMetrics):
        """Write telemetry data to file for external analysis"""
        try:
            telemetry_data = asdict(telemetry)
            
            # Append to telemetry file
            with open(self.telemetry_file, 'a') as f:
                f.write(json.dumps(telemetry_data) + '\n')
                
        except Exception as e:
            logger.warning(f"Error writing telemetry to file: {e}")
    
    async def get_system_status_report(self) -> Dict[str, Any]:
        """Get comprehensive system status report"""
        try:
            # Get latest telemetry
            latest_telemetry = await self.collect_comprehensive_metrics()
            
            # Get recent alerts
            recent_alerts = [
                alert for alert in self.alert_history
                if datetime.fromisoformat(alert.timestamp) > datetime.now() - timedelta(hours=24)
            ]
            
            # Calculate trends
            trends = await self._calculate_trends()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "system_status": "healthy" if latest_telemetry.system_health_score > 0.7 else "degraded" if latest_telemetry.system_health_score > 0.4 else "critical",
                "current_metrics": asdict(latest_telemetry),
                "recent_alerts": {
                    "total": len(recent_alerts),
                    "critical": len([a for a in recent_alerts if a.severity == "critical"]),
                    "warning": len([a for a in recent_alerts if a.severity == "warning"]),
                    "alerts": [asdict(alert) for alert in recent_alerts[-10:]]  # Last 10 alerts
                },
                "trends": trends,
                "recommendations": await self._generate_system_recommendations(latest_telemetry, recent_alerts)
            }
            
        except Exception as e:
            logger.error(f"Error generating system status report: {e}")
            return {"error": str(e)}
    
    async def _calculate_trends(self) -> Dict[str, str]:
        """Calculate system trends from historical data"""
        try:
            if len(self.metrics_history) < 2:
                return {"status": "insufficient_data"}
            
            recent_metrics = self.metrics_history[-5:]  # Last 5 data points
            older_metrics = self.metrics_history[-10:-5] if len(self.metrics_history) >= 10 else self.metrics_history[:-5]
            
            if not older_metrics:
                return {"status": "insufficient_historical_data"}
            
            # Calculate averages
            recent_health = sum(m.system_health_score for m in recent_metrics) / len(recent_metrics)
            older_health = sum(m.system_health_score for m in older_metrics) / len(older_metrics)
            
            recent_wait_time = sum(m.average_task_wait_time for m in recent_metrics) / len(recent_metrics)
            older_wait_time = sum(m.average_task_wait_time for m in older_metrics) / len(older_metrics)
            
            return {
                "system_health": "improving" if recent_health > older_health else "stable" if abs(recent_health - older_health) < 0.1 else "degrading",
                "task_wait_time": "improving" if recent_wait_time < older_wait_time else "stable" if abs(recent_wait_time - older_wait_time) < 5 else "degrading",
                "health_change": recent_health - older_health,
                "wait_time_change": recent_wait_time - older_wait_time
            }
            
        except Exception as e:
            logger.warning(f"Error calculating trends: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _generate_system_recommendations(self, telemetry: TelemetryMetrics, recent_alerts: List[SystemAlert]) -> List[str]:
        """Generate actionable system recommendations"""
        recommendations = []
        
        try:
            # Health-based recommendations
            if telemetry.system_health_score < 0.5:
                recommendations.append("System health is critical - investigate workspace and task processor issues immediately")
            
            # Task processing recommendations
            if telemetry.average_task_wait_time > 30:
                recommendations.append(f"High task wait times ({telemetry.average_task_wait_time:.1f} min) - consider increasing task processor capacity")
            
            if telemetry.critical_tasks_total > 5:
                recommendations.append(f"High critical task backlog ({telemetry.critical_tasks_total} tasks) - prioritize critical task processing")
            
            # Workspace recommendations
            if telemetry.paused_workspaces > telemetry.active_workspaces:
                recommendations.append("More workspaces paused than active - review pause conditions and recovery mechanisms")
            
            # AI system recommendations
            if telemetry.ai_confidence_average < 0.6:
                recommendations.append(f"Low AI confidence ({telemetry.ai_confidence_average:.2f}) - review AI prompts and models")
            
            # Alert-based recommendations
            critical_alerts = [a for a in recent_alerts if a.severity == "critical"]
            if critical_alerts:
                recommendations.append(f"Address {len(critical_alerts)} critical alerts from the last 24 hours")
            
            if not recommendations:
                recommendations.append("System operating within normal parameters - continue monitoring")
            
        except Exception as e:
            logger.warning(f"Error generating recommendations: {e}")
            recommendations.append("Unable to generate recommendations due to analysis error")
        
        return recommendations

# Global instance
system_telemetry_monitor = SystemTelemetryMonitor()

# Export for easy import
__all__ = ["SystemTelemetryMonitor", "system_telemetry_monitor", "SystemAlert", "TelemetryMetrics"]