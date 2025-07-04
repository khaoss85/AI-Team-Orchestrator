"""
🤖 AI-Driven Dynamic Anti-Loop Manager
Implements intelligent, adaptive task limit management based on real-time workspace metrics
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

from database import supabase

logger = logging.getLogger(__name__)

@dataclass
class WorkspaceMetrics:
    """Real-time metrics for a workspace"""
    workspace_id: str
    pending_tasks_count: int
    critical_tasks_count: int
    skip_percentage: float
    average_wait_time_minutes: float
    task_generation_rate: float  # tasks/hour
    completion_rate: float       # tasks/hour
    current_limit: int
    recommended_limit: int
    health_score: float         # 0.0 to 1.0

@dataclass
class AdaptationRule:
    """Rule for dynamic limit adjustment"""
    condition: str
    threshold_value: float
    adjustment_factor: float
    max_limit: int
    min_limit: int

class DynamicAntiLoopManager:
    """
    🤖 AI-DRIVEN: Intelligent anti-loop limit management
    Pillar 4: Scalable & auto-apprendente
    Pillar 12: Automatic Course-Correction
    """
    
    def __init__(self):
        self.workspace_metrics: Dict[str, WorkspaceMetrics] = {}
        self.metrics_history: Dict[str, List[Dict]] = defaultdict(list)
        
        # Configuration
        self.base_limit = int(os.getenv("MAX_TASKS_PER_WORKSPACE_ANTI_LOOP", "15"))
        self.max_absolute_limit = int(os.getenv("MAX_ABSOLUTE_ANTI_LOOP_LIMIT", "50"))
        self.min_absolute_limit = int(os.getenv("MIN_ABSOLUTE_ANTI_LOOP_LIMIT", "5"))
        
        # Monitoring intervals
        self.metrics_update_interval = 60  # seconds
        self.adaptation_interval = 300     # seconds (5 minutes)
        
        # AI-driven adaptation rules  
        self.adaptation_rules = [
            AdaptationRule(
                condition="high_skip_rate",
                threshold_value=0.10,  # 10% skip rate (more aggressive)
                adjustment_factor=2.0,  # More aggressive adjustment
                max_limit=self.max_absolute_limit,
                min_limit=self.base_limit
            ),
            AdaptationRule(
                condition="critical_backlog", 
                threshold_value=5,     # 5+ critical tasks pending
                adjustment_factor=2.0,
                max_limit=self.max_absolute_limit,
                min_limit=self.base_limit
            ),
            AdaptationRule(
                condition="high_wait_time",
                threshold_value=30,    # 30+ minutes average wait
                adjustment_factor=1.3,
                max_limit=self.max_absolute_limit,
                min_limit=self.base_limit
            ),
            AdaptationRule(
                condition="generation_overflow",
                threshold_value=2.0,   # generation > completion rate ratio
                adjustment_factor=1.4,
                max_limit=self.max_absolute_limit,
                min_limit=self.base_limit
            )
        ]
        
        logger.info("🤖 DynamicAntiLoopManager initialized with AI-driven adaptation")
    
    async def collect_workspace_metrics(self, workspace_id: str) -> WorkspaceMetrics:
        """
        🤖 AI-DRIVEN: Collect comprehensive real-time metrics for a workspace
        """
        try:
            # Get pending tasks
            pending_response = supabase.table('tasks').select('*').eq('workspace_id', workspace_id).eq('status', 'pending').execute()
            pending_tasks = pending_response.data or []
            
            # Analyze critical tasks
            critical_tasks = []
            for task in pending_tasks:
                # Check if task is critical based on various indicators
                is_critical = await self._is_task_critical(task)
                if is_critical:
                    critical_tasks.append(task)
            
            # Calculate skip percentage (last hour)
            one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
            
            # Get task completion metrics
            completed_response = supabase.table('tasks').select('*').eq('workspace_id', workspace_id).eq('status', 'completed').gte('updated_at', one_hour_ago).execute()
            completed_tasks = completed_response.data or []
            
            # Calculate rates
            task_generation_rate = len([t for t in pending_tasks if t.get('created_at', '') > one_hour_ago]) 
            completion_rate = len(completed_tasks)
            
            # Calculate average wait time
            avg_wait_time = await self._calculate_average_wait_time(pending_tasks)
            
            # Get current limit from executor (if available)
            current_limit = self.base_limit  # Will be updated by executor
            
            # Calculate health score
            health_score = await self._calculate_health_score(
                len(pending_tasks), len(critical_tasks), avg_wait_time, task_generation_rate, completion_rate
            )
            
            # Determine recommended limit using AI-driven rules
            recommended_limit = await self._calculate_recommended_limit(
                workspace_id, len(pending_tasks), len(critical_tasks), 
                avg_wait_time, task_generation_rate, completion_rate
            )
            
            metrics = WorkspaceMetrics(
                workspace_id=workspace_id,
                pending_tasks_count=len(pending_tasks),
                critical_tasks_count=len(critical_tasks),
                skip_percentage=0.0,  # Will be calculated from executor feedback
                average_wait_time_minutes=avg_wait_time,
                task_generation_rate=task_generation_rate,
                completion_rate=completion_rate,
                current_limit=current_limit,
                recommended_limit=recommended_limit,
                health_score=health_score
            )
            
            # Store metrics
            self.workspace_metrics[workspace_id] = metrics
            self._add_to_history(workspace_id, metrics)
            
            logger.info(f"📊 Metrics for W:{workspace_id[:8]}: {len(pending_tasks)} pending, {len(critical_tasks)} critical, health: {health_score:.2f}, recommended limit: {recommended_limit}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting metrics for workspace {workspace_id}: {e}")
            return WorkspaceMetrics(
                workspace_id=workspace_id,
                pending_tasks_count=0,
                critical_tasks_count=0,
                skip_percentage=0.0,
                average_wait_time_minutes=0.0,
                task_generation_rate=0.0,
                completion_rate=0.0,
                current_limit=self.base_limit,
                recommended_limit=self.base_limit,
                health_score=0.5
            )
    
    async def _is_task_critical(self, task: Dict) -> bool:
        """Determine if a task is critical (matches our existing logic)"""
        try:
            task_name = task.get("name", "").lower()
            task_description = task.get("description", "").lower()
            context_data = task.get("context_data", {}) or {}
            
            # Check goal-driven corrective tasks
            is_goal_driven = context_data.get("is_goal_driven_task", False)
            task_type = context_data.get("task_type", "").lower()
            
            if is_goal_driven and "corrective" in task_type:
                return True
            
            # Check critical keywords
            critical_indicators = [
                "critical", "urgent", "emergency", "fix", "repair", "restore",
                "goal completion", "deliverable creation", "deliverable", "quality assurance",
                "workspace recovery", "error correction", "system repair", "create final",
                "generate deliverable", "package", "final output"
            ]
            
            combined_text = f"{task_name} {task_description}"
            for indicator in critical_indicators:
                if indicator in combined_text:
                    return True
            
            # Check priority and recency
            priority = task.get("priority", "medium").lower()
            if priority == "high":
                created_at = task.get("created_at")
                if created_at:
                    try:
                        created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        if datetime.now().replace(tzinfo=created_time.tzinfo) - created_time < timedelta(hours=2):
                            return True
                    except:
                        pass
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking if task is critical: {e}")
            return False
    
    async def _calculate_average_wait_time(self, pending_tasks: List[Dict]) -> float:
        """Calculate average wait time for pending tasks in minutes"""
        if not pending_tasks:
            return 0.0
        
        total_wait = 0.0
        valid_tasks = 0
        
        for task in pending_tasks:
            created_at = task.get("created_at")
            if created_at:
                try:
                    created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    wait_time = (datetime.now().replace(tzinfo=created_time.tzinfo) - created_time).total_seconds() / 60
                    total_wait += wait_time
                    valid_tasks += 1
                except:
                    continue
        
        return total_wait / valid_tasks if valid_tasks > 0 else 0.0
    
    async def _calculate_health_score(self, pending_count: int, critical_count: int, 
                                    avg_wait: float, gen_rate: float, comp_rate: float) -> float:
        """Calculate workspace health score (0.0 to 1.0)"""
        try:
            # Base score
            score = 1.0
            
            # Penalty for high pending count
            if pending_count > 20:
                score -= min(0.3, (pending_count - 20) * 0.01)
            
            # Penalty for critical backlog
            if critical_count > 0:
                score -= min(0.4, critical_count * 0.08)
            
            # Penalty for high wait times
            if avg_wait > 15:
                score -= min(0.2, (avg_wait - 15) * 0.01)
            
            # Penalty for generation/completion imbalance
            if comp_rate > 0 and gen_rate > comp_rate * 1.5:
                score -= min(0.3, (gen_rate / comp_rate - 1.5) * 0.2)
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.warning(f"Error calculating health score: {e}")
            return 0.5
    
    async def _calculate_recommended_limit(self, workspace_id: str, pending_count: int, 
                                         critical_count: int, avg_wait: float, 
                                         gen_rate: float, comp_rate: float) -> int:
        """
        🤖 AI-DRIVEN: Calculate recommended limit based on adaptation rules
        """
        try:
            current_limit = self.workspace_metrics.get(workspace_id, {}).get('current_limit', self.base_limit)
            recommended = current_limit
            
            # Apply adaptation rules
            for rule in self.adaptation_rules:
                should_adjust = False
                
                if rule.condition == "high_skip_rate":
                    # This will be updated by executor feedback
                    continue
                    
                elif rule.condition == "critical_backlog":
                    if critical_count >= rule.threshold_value:
                        should_adjust = True
                        
                elif rule.condition == "high_wait_time":
                    if avg_wait >= rule.threshold_value:
                        should_adjust = True
                        
                elif rule.condition == "generation_overflow":
                    if comp_rate > 0 and (gen_rate / comp_rate) >= rule.threshold_value:
                        should_adjust = True
                
                if should_adjust:
                    new_limit = int(current_limit * rule.adjustment_factor)
                    recommended = max(recommended, min(new_limit, rule.max_limit))
                    logger.info(f"🤖 AI Rule '{rule.condition}' triggered for W:{workspace_id[:8]} - recommending limit: {recommended}")
            
            # Ensure within bounds
            recommended = max(self.min_absolute_limit, min(recommended, self.max_absolute_limit))
            
            # Conservative adjustment - don't jump too drastically
            if recommended > current_limit:
                recommended = min(recommended, current_limit + 10)
            elif recommended < current_limit:
                recommended = max(recommended, current_limit - 5)
            
            return recommended
            
        except Exception as e:
            logger.error(f"Error calculating recommended limit: {e}")
            return self.base_limit
    
    def _add_to_history(self, workspace_id: str, metrics: WorkspaceMetrics):
        """Add metrics to history for trend analysis"""
        try:
            history_entry = {
                "timestamp": datetime.now().isoformat(),
                "pending_count": metrics.pending_tasks_count,
                "critical_count": metrics.critical_tasks_count,
                "avg_wait": metrics.average_wait_time_minutes,
                "health_score": metrics.health_score,
                "recommended_limit": metrics.recommended_limit
            }
            
            self.metrics_history[workspace_id].append(history_entry)
            
            # Keep only last 24 hours of history
            cutoff = datetime.now() - timedelta(hours=24)
            self.metrics_history[workspace_id] = [
                entry for entry in self.metrics_history[workspace_id]
                if datetime.fromisoformat(entry["timestamp"]) > cutoff
            ]
            
        except Exception as e:
            logger.warning(f"Error adding metrics to history: {e}")
    
    async def update_skip_percentage(self, workspace_id: str, skip_percentage: float):
        """Update skip percentage from executor feedback"""
        try:
            if workspace_id in self.workspace_metrics:
                self.workspace_metrics[workspace_id].skip_percentage = skip_percentage
                
                # Check if we need to adjust based on skip rate
                if skip_percentage >= 0.10:  # 10% threshold (more aggressive)
                    current_limit = self.workspace_metrics[workspace_id].current_limit
                    # More aggressive limit increase based on skip percentage
                    if skip_percentage >= 0.70:  # 70%+ skip rate
                        increment = 15  # Very aggressive increase
                    elif skip_percentage >= 0.50:  # 50%+ skip rate
                        increment = 10
                    elif skip_percentage >= 0.30:  # 30%+ skip rate
                        increment = 7
                    else:  # 10-30% skip rate
                        increment = 5
                    new_limit = min(current_limit + increment, self.max_absolute_limit)
                    self.workspace_metrics[workspace_id].recommended_limit = max(
                        self.workspace_metrics[workspace_id].recommended_limit, new_limit
                    )
                    logger.warning(f"🚨 High skip rate ({skip_percentage:.1%}) for W:{workspace_id[:8]} - recommending limit increase to {new_limit}")
            else:
                # Initialize metrics if not present
                logger.info(f"🔄 Initializing metrics for W:{workspace_id[:8]} due to skip percentage update")
                await self.collect_workspace_metrics(workspace_id)
                # Retry the update
                if workspace_id in self.workspace_metrics:
                    await self.update_skip_percentage(workspace_id, skip_percentage)
        except Exception as e:
            logger.error(f"Dynamic anti-loop manager error, using base limit: {e}")
            # Create minimal metrics with base limit as fallback
            if workspace_id not in self.workspace_metrics:
                self.workspace_metrics[workspace_id] = WorkspaceMetrics(
                    workspace_id=workspace_id,
                    pending_tasks_count=0,
                    critical_tasks_count=0,
                    skip_percentage=skip_percentage,
                    average_wait_time_minutes=0.0,
                    task_generation_rate=0.0,
                    completion_rate=0.0,
                    current_limit=self.base_limit,
                    recommended_limit=self.base_limit,
                    health_score=0.5
                )
    
    async def get_recommended_limit(self, workspace_id: str) -> int:
        """Get current recommended limit for a workspace"""
        if workspace_id in self.workspace_metrics:
            return self.workspace_metrics[workspace_id].recommended_limit
        else:
            # Collect fresh metrics
            metrics = await self.collect_workspace_metrics(workspace_id)
            return metrics.recommended_limit
    
    async def get_workspace_health_report(self, workspace_id: str) -> Dict:
        """Get comprehensive health report for a workspace"""
        try:
            metrics = await self.collect_workspace_metrics(workspace_id)
            
            # Get trend analysis
            history = self.metrics_history.get(workspace_id, [])
            trend_analysis = self._analyze_trends(history)
            
            return {
                "workspace_id": workspace_id,
                "current_metrics": {
                    "pending_tasks": metrics.pending_tasks_count,
                    "critical_tasks": metrics.critical_tasks_count,
                    "skip_percentage": metrics.skip_percentage,
                    "avg_wait_minutes": metrics.average_wait_time_minutes,
                    "generation_rate": metrics.task_generation_rate,
                    "completion_rate": metrics.completion_rate,
                    "health_score": metrics.health_score
                },
                "limits": {
                    "current": metrics.current_limit,
                    "recommended": metrics.recommended_limit,
                    "base": self.base_limit
                },
                "trend_analysis": trend_analysis,
                "recommendations": self._generate_recommendations(metrics)
            }
            
        except Exception as e:
            logger.error(f"Error generating health report for {workspace_id}: {e}")
            return {"error": str(e)}
    
    def _analyze_trends(self, history: List[Dict]) -> Dict:
        """Analyze trends from metrics history"""
        if len(history) < 2:
            return {"status": "insufficient_data"}
        
        try:
            recent = history[-3:]  # Last 3 entries
            old = history[-6:-3] if len(history) >= 6 else history[:-3]
            
            if not old:
                return {"status": "insufficient_data"}
            
            # Calculate averages
            recent_avg_pending = sum(h["pending_count"] for h in recent) / len(recent)
            old_avg_pending = sum(h["pending_count"] for h in old) / len(old)
            
            recent_avg_health = sum(h["health_score"] for h in recent) / len(recent)
            old_avg_health = sum(h["health_score"] for h in old) / len(old)
            
            return {
                "status": "analyzed",
                "pending_trend": "improving" if recent_avg_pending < old_avg_pending else "degrading",
                "health_trend": "improving" if recent_avg_health > old_avg_health else "degrading",
                "pending_change": recent_avg_pending - old_avg_pending,
                "health_change": recent_avg_health - old_avg_health
            }
            
        except Exception as e:
            logger.warning(f"Error analyzing trends: {e}")
            return {"status": "error", "message": str(e)}
    
    def _generate_recommendations(self, metrics: WorkspaceMetrics) -> List[str]:
        """Generate actionable recommendations based on metrics"""
        recommendations = []
        
        try:
            if metrics.critical_tasks_count > 5:
                recommendations.append(f"High critical task backlog ({metrics.critical_tasks_count} tasks) - consider increasing task limit or priority")
            
            if metrics.average_wait_time_minutes > 30:
                recommendations.append(f"High average wait time ({metrics.average_wait_time_minutes:.1f} min) - recommend limit increase")
            
            if metrics.health_score < 0.5:
                recommendations.append("Poor workspace health - requires immediate attention")
            
            if metrics.task_generation_rate > metrics.completion_rate * 2:
                recommendations.append("Task generation outpacing completion - system overload detected")
            
            if metrics.recommended_limit > metrics.current_limit:
                recommendations.append(f"Recommend increasing task limit from {metrics.current_limit} to {metrics.recommended_limit}")
            
            if not recommendations:
                recommendations.append("Workspace operating within normal parameters")
            
        except Exception as e:
            logger.warning(f"Error generating recommendations: {e}")
            recommendations.append("Unable to generate recommendations due to analysis error")
        
        return recommendations

# Global instance
dynamic_anti_loop_manager = DynamicAntiLoopManager()

# Export for easy import
__all__ = ["DynamicAntiLoopManager", "dynamic_anti_loop_manager", "WorkspaceMetrics"]