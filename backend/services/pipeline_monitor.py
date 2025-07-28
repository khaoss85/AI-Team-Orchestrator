#!/usr/bin/env python3
"""
Pipeline Monitoring System

Proactive monitoring to prevent future pipeline blocks and ensure
system health across all components.
"""

import asyncio
import logging
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from database import supabase
from services.workspace_health_manager import workspace_health_manager

logger = logging.getLogger(__name__)

@dataclass
class PipelineAlert:
    """Pipeline monitoring alert"""
    level: str  # info, warning, critical
    component: str
    message: str
    workspace_id: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class PipelineMonitor:
    """
    🚨 PIPELINE MONITORING SYSTEM
    
    Prevents future pipeline blocks through proactive monitoring
    and automated recovery based on lessons learned from Phases 1-3.
    """
    
    def __init__(self):
        self.monitoring_enabled = os.getenv("ENABLE_PIPELINE_MONITORING", "true").lower() == "true"
        self.check_interval = int(os.getenv("PIPELINE_MONITOR_INTERVAL", "300"))  # 5 minutes
        self.alerts: List[PipelineAlert] = []
        self.max_alerts = 100
        
        logger.info(f"🚨 Pipeline Monitor initialized - enabled: {self.monitoring_enabled}")
    
    async def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """
        🔍 COMPREHENSIVE HEALTH CHECK
        
        Monitors all aspects of the pipeline for potential issues
        """
        if not self.monitoring_enabled:
            return {"status": "disabled"}
        
        logger.info("🔍 Starting comprehensive pipeline health check...")
        
        health_report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "components": {},
            "alerts": [],
            "recommendations": []
        }
        
        # 1. Workspace Health Check (Phase 1 prevention)
        workspace_health = await self._check_workspace_health()
        health_report["components"]["workspace_health"] = workspace_health
        
        # 2. Quality System Check (Phase 2 prevention)  
        quality_health = await self._check_quality_system()
        health_report["components"]["quality_system"] = quality_health
        
        # 3. Goal System Check (Phase 3 prevention)
        goal_health = await self._check_goal_system()
        health_report["components"]["goal_system"] = goal_health
        
        # 4. Deliverable Pipeline Check
        deliverable_health = await self._check_deliverable_pipeline()
        health_report["components"]["deliverable_pipeline"] = deliverable_health
        
        # 5. Database Performance Check
        db_health = await self._check_database_performance()
        health_report["components"]["database"] = db_health
        
        # Calculate overall status
        component_scores = [
            comp.get("score", 0) for comp in health_report["components"].values()
        ]
        overall_score = sum(component_scores) / len(component_scores) if component_scores else 0
        
        if overall_score >= 80:
            health_report["overall_status"] = "healthy"
        elif overall_score >= 60:
            health_report["overall_status"] = "warning"
        else:
            health_report["overall_status"] = "critical"
        
        # Generate alerts and recommendations
        health_report["alerts"] = [alert.__dict__ for alert in self.alerts[-10:]]  # Last 10 alerts
        health_report["recommendations"] = self._generate_recommendations(health_report)
        
        logger.info(f"🔍 Health check complete - Overall: {health_report['overall_status']} ({overall_score:.1f}%)")
        
        return health_report
    
    async def _check_workspace_health(self) -> Dict[str, Any]:
        """Check workspace health (Phase 1 issue prevention)"""
        try:
            # Use our existing workspace health manager
            system_check = await workspace_health_manager.monitor_all_workspaces_for_stuck_processing()
            
            stuck_workspaces = system_check.get("stuck_workspaces", 0)
            recovered = system_check.get("recovered", 0)
            
            if stuck_workspaces > 0:
                self.alerts.append(PipelineAlert(
                    level="warning",
                    component="workspace_health",
                    message=f"Found {stuck_workspaces} stuck workspaces, {recovered} recovered"
                ))
            
            # Calculate health score
            if stuck_workspaces == 0:
                score = 100
            elif recovered >= stuck_workspaces:
                score = 80  # Good recovery
            else:
                score = 50  # Issues with recovery
            
            return {
                "status": "healthy" if score >= 80 else "warning" if score >= 60 else "critical",
                "score": score,
                "stuck_workspaces": stuck_workspaces,
                "recovered_workspaces": recovered,
                "details": "Workspace status transition monitoring"
            }
            
        except Exception as e:
            logger.error(f"Error checking workspace health: {e}")
            return {"status": "error", "score": 0, "error": str(e)}
    
    async def _check_quality_system(self) -> Dict[str, Any]:
        """Check quality scoring system (Phase 2 issue prevention)"""
        try:
            # Test quality scoring with sample data
            from deliverable_system.concrete_asset_extractor import concrete_asset_extractor
            
            sample_asset = {
                'asset_type': 'document',
                'asset_name': 'monitoring_test',
                'content': 'Sample content for quality testing with reasonable length',
                'byte_size': 60,
                'confidence': 0.8
            }
            
            quality_score = concrete_asset_extractor._calculate_asset_quality(sample_asset)
            
            if quality_score >= 0.6:
                score = 100
                status = "healthy"
            elif quality_score >= 0.4:
                score = 70
                status = "warning"
                self.alerts.append(PipelineAlert(
                    level="warning",
                    component="quality_system",
                    message=f"Quality scores lower than expected: {quality_score:.2f}"
                ))
            else:
                score = 30
                status = "critical"
                self.alerts.append(PipelineAlert(
                    level="critical",
                    component="quality_system",
                    message=f"Quality scoring system returning low scores: {quality_score:.2f}"
                ))
            
            return {
                "status": status,
                "score": score,
                "sample_quality_score": quality_score,
                "details": "Quality scoring system validation"
            }
            
        except Exception as e:
            logger.error(f"Error checking quality system: {e}")
            return {"status": "error", "score": 0, "error": str(e)}
    
    async def _check_goal_system(self) -> Dict[str, Any]:
        """Check goal creation and progress system (Phase 3 issue prevention)"""
        try:
            # Check for workspaces with goals but no workspace_goals entries
            workspaces_response = supabase.table("workspaces").select("id, goal").execute()
            workspaces_with_goals = [
                ws for ws in (workspaces_response.data or []) 
                if ws.get("goal") and len(ws["goal"].strip()) > 10
            ]
            
            goal_creation_issues = 0
            
            for workspace in workspaces_with_goals[:5]:  # Check first 5
                workspace_id = workspace["id"]
                
                # Check if workspace_goals exist
                goals_response = supabase.table("workspace_goals").select("id").eq(
                    "workspace_id", workspace_id
                ).execute()
                
                if not goals_response.data:
                    goal_creation_issues += 1
            
            if goal_creation_issues > 0:
                self.alerts.append(PipelineAlert(
                    level="warning",
                    component="goal_system",
                    message=f"Found {goal_creation_issues} workspaces with goals but no workspace_goals entries"
                ))
                score = 70
                status = "warning"
            else:
                score = 100
                status = "healthy"
            
            return {
                "status": status,
                "score": score,
                "workspaces_checked": len(workspaces_with_goals),
                "goal_creation_issues": goal_creation_issues,
                "details": "Goal creation and progress system validation"
            }
            
        except Exception as e:
            logger.error(f"Error checking goal system: {e}")
            return {"status": "error", "score": 0, "error": str(e)}
    
    async def _check_deliverable_pipeline(self) -> Dict[str, Any]:
        """Check deliverable creation pipeline"""
        try:
            # Check for workspaces with completed tasks but no deliverables
            tasks_response = supabase.table("tasks").select("workspace_id").eq("status", "completed").execute()
            workspaces_with_completed_tasks = set(
                task["workspace_id"] for task in (tasks_response.data or [])
            )
            
            deliverable_issues = 0
            
            for workspace_id in list(workspaces_with_completed_tasks)[:5]:  # Check first 5
                # Count completed tasks
                completed_tasks = supabase.table("tasks").select("id").eq(
                    "workspace_id", workspace_id
                ).eq("status", "completed").execute()
                
                completed_count = len(completed_tasks.data) if completed_tasks.data else 0
                
                # Count deliverables
                deliverables = supabase.table("deliverables").select("id").eq(
                    "workspace_id", workspace_id
                ).execute()
                
                deliverable_count = len(deliverables.data) if deliverables.data else 0
                
                # If we have 3+ completed tasks but no deliverables, flag it
                if completed_count >= 3 and deliverable_count == 0:
                    deliverable_issues += 1
            
            if deliverable_issues > 0:
                self.alerts.append(PipelineAlert(
                    level="warning",
                    component="deliverable_pipeline",
                    message=f"Found {deliverable_issues} workspaces with completed tasks but no deliverables"
                ))
                score = 70
                status = "warning"
            else:
                score = 100
                status = "healthy"
            
            return {
                "status": status,
                "score": score,
                "workspaces_checked": len(workspaces_with_completed_tasks),
                "deliverable_issues": deliverable_issues,
                "details": "Deliverable creation pipeline validation"
            }
            
        except Exception as e:
            logger.error(f"Error checking deliverable pipeline: {e}")
            return {"status": "error", "score": 0, "error": str(e)}
    
    async def _check_database_performance(self) -> Dict[str, Any]:
        """Check database performance and connectivity"""
        try:
            start_time = datetime.now()
            
            # Simple performance test
            test_response = supabase.table("workspaces").select("id").limit(1).execute()
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            if response_time <= 100:  # Under 100ms
                score = 100
                status = "healthy"
            elif response_time <= 500:  # Under 500ms
                score = 80
                status = "healthy"
            elif response_time <= 1000:  # Under 1s
                score = 60
                status = "warning"
                self.alerts.append(PipelineAlert(
                    level="warning",
                    component="database",
                    message=f"Database response time elevated: {response_time:.1f}ms"
                ))
            else:
                score = 30
                status = "critical"
                self.alerts.append(PipelineAlert(
                    level="critical",
                    component="database",
                    message=f"Database response time critical: {response_time:.1f}ms"
                ))
            
            return {
                "status": status,
                "score": score,
                "response_time_ms": response_time,
                "details": "Database connectivity and performance"
            }
            
        except Exception as e:
            logger.error(f"Error checking database performance: {e}")
            return {"status": "error", "score": 0, "error": str(e)}
    
    def _generate_recommendations(self, health_report: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on health report"""
        recommendations = []
        
        for component, health in health_report["components"].items():
            if health.get("status") == "critical":
                if component == "workspace_health":
                    recommendations.append("🔧 Run workspace recovery: Use workspace_health_manager to recover stuck workspaces")
                elif component == "quality_system":
                    recommendations.append("🎯 Check quality scoring: Verify concrete_asset_extractor quality calculation")
                elif component == "goal_system":
                    recommendations.append("🎯 Fix goal creation: Run goal decomposition for workspaces missing workspace_goals")
                elif component == "deliverable_pipeline":
                    recommendations.append("📦 Trigger deliverable creation: Force deliverable generation for eligible workspaces")
                elif component == "database":
                    recommendations.append("🗄️ Database maintenance: Check database performance and connections")
                    
            elif health.get("status") == "warning":
                recommendations.append(f"⚠️ Monitor {component}: {health.get('details', 'Requires attention')}")
        
        if not recommendations:
            recommendations.append("✅ System healthy: No immediate action required")
        
        return recommendations
    
    async def save_health_report(self, report: Dict[str, Any]) -> bool:
        """Save health report to database"""
        try:
            # FIXED: Create JSON serializer that handles datetime objects
            def json_serializer(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            report_data = {
                'timestamp': report['timestamp'],
                'overall_status': report['overall_status'],
                'report_data': json.dumps(report, default=json_serializer),
                'alert_count': len(report.get('alerts', [])),
                'recommendation_count': len(report.get('recommendations', []))
            }
            
            # Save to a monitoring table (if it exists)
            supabase.table("pipeline_health_reports").insert(report_data).execute()
            return True
            
        except Exception as e:
            logger.debug(f"Could not save health report to database: {e}")
            # Save to file as fallback
            try:
                def json_serializer(obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
                
                filename = f"pipeline_health_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w') as f:
                    json.dump(report, f, indent=2, default=json_serializer)
                logger.info(f"Health report saved to {filename}")
                return True
            except Exception as e2:
                logger.error(f"Failed to save health report: {e2}")
                return False

# Global instance
pipeline_monitor = PipelineMonitor()

async def run_monitoring_cycle():
    """Run a single monitoring cycle"""
    try:
        report = await pipeline_monitor.run_comprehensive_health_check()
        await pipeline_monitor.save_health_report(report)
        
        logger.info(f"🚨 Monitoring cycle completed - Status: {report['overall_status']}")
        
        return report
        
    except Exception as e:
        logger.error(f"Error in monitoring cycle: {e}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    # Run monitoring once for testing
    asyncio.run(run_monitoring_cycle())