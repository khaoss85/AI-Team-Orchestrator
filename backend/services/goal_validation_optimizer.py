#!/usr/bin/env python3
"""
🎯 GOAL VALIDATION OPTIMIZER

Intelligent optimization system for goal validation to prevent excessive corrective task generation.
This addresses the root cause of overly aggressive goal validation that creates too many
corrective tasks without considering progress velocity and temporal context.

Features:
- Grace period for recently created tasks
- Progress velocity tracking and analysis
- Adaptive validation thresholds based on workspace characteristics
- Temporal context awareness for validation decisions
- Smart filtering of false positive validation failures
- Pillars compliant (AI-driven decisions)
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

from database import supabase
from models import GoalStatus

logger = logging.getLogger(__name__)

class ValidationDecision(Enum):
    """Goal validation decision outcomes"""
    PROCEED_NORMAL = "proceed_normal"           # Normal validation
    APPLY_GRACE_PERIOD = "apply_grace_period"   # Skip due to grace period
    VELOCITY_ACCEPTABLE = "velocity_acceptable" # Progress velocity is good
    THRESHOLD_ADJUSTED = "threshold_adjusted"   # Adaptive threshold applied
    SKIP_VALIDATION = "skip_validation"         # Skip completely

class ProgressVelocity(Enum):
    """Progress velocity classifications"""
    EXCELLENT = "excellent"  # >80% progress rate
    GOOD = "good"           # 50-80% progress rate  
    MODERATE = "moderate"   # 20-50% progress rate
    SLOW = "slow"          # 5-20% progress rate
    STALLED = "stalled"    # <5% progress rate

@dataclass
class TaskProgressMetrics:
    """Metrics for task progress analysis"""
    task_id: str
    workspace_id: str
    created_at: datetime
    last_activity: Optional[datetime]
    age_hours: float
    completion_percentage: float
    velocity_score: float
    has_recent_activity: bool
    progress_trend: str

@dataclass
class WorkspaceProgressAnalysis:
    """Comprehensive workspace progress analysis"""
    workspace_id: str
    total_tasks: int
    active_tasks: int
    completed_tasks: int
    overall_completion_rate: float
    velocity_classification: ProgressVelocity
    average_task_age_hours: float
    recent_completions_24h: int
    progress_trend: str
    recommended_action: ValidationDecision

@dataclass
class ValidationOptimizationResult:
    """Result of validation optimization"""
    should_proceed: bool
    decision: ValidationDecision
    reason: str
    confidence: float
    grace_period_remaining_hours: Optional[float] = None
    velocity_score: Optional[float] = None
    adaptive_threshold: Optional[float] = None

class GoalValidationOptimizer:
    """
    🎯 DEFINITIVE SOLUTION for overly aggressive goal validation
    
    Prevents excessive corrective task creation through intelligent temporal
    analysis and adaptive thresholds.
    """
    
    def __init__(self):
        # Configuration
        self.enable_optimization = os.getenv("ENABLE_GOAL_VALIDATION_OPTIMIZATION", "true").lower() == "true"
        self.default_grace_period_hours = float(os.getenv("GOAL_VALIDATION_GRACE_PERIOD_HOURS", "2"))  # 2 hours - optimized from 4h
        self.velocity_tracking_window_hours = float(os.getenv("VELOCITY_TRACKING_WINDOW_HOURS", "24"))  # 24 hours
        self.adaptive_threshold_enabled = os.getenv("ENABLE_ADAPTIVE_VALIDATION_THRESHOLDS", "true").lower() == "true"
        
        # Velocity thresholds
        self.excellent_velocity_threshold = 0.8  # 80%+ progress rate
        self.good_velocity_threshold = 0.5       # 50%+ progress rate
        self.moderate_velocity_threshold = 0.2   # 20%+ progress rate
        self.slow_velocity_threshold = 0.05      # 5%+ progress rate
        
        # Adaptive thresholds
        self.base_validation_threshold = 0.7     # 70% base threshold
        self.max_threshold_adjustment = 0.3      # Max 30% adjustment
        
        # Cache for performance
        self.workspace_analysis_cache: Dict[str, Tuple[float, WorkspaceProgressAnalysis]] = {}
        self.cache_duration = 300  # 5 minutes
        
        logger.info(f"GoalValidationOptimizer initialized - optimization: {self.enable_optimization}, "
                   f"grace_period: {self.default_grace_period_hours}h, velocity_window: {self.velocity_tracking_window_hours}h")
    
    async def should_proceed_with_validation(
        self, 
        workspace_id: str, 
        goal_data: Dict,
        recent_tasks: Optional[List[Dict]] = None
    ) -> ValidationOptimizationResult:
        """
        🔍 CORE FUNCTION: Determine if goal validation should proceed
        
        Returns optimization decision with reasoning and confidence
        """
        try:
            if not self.enable_optimization:
                return ValidationOptimizationResult(
                    should_proceed=True,
                    decision=ValidationDecision.PROCEED_NORMAL,
                    reason="Optimization disabled",
                    confidence=1.0
                )
            
            logger.debug(f"🔍 Analyzing validation need for goal {goal_data.get('id')} in workspace {workspace_id}")
            
            # 1. Check grace period for recently created goals/tasks
            grace_period_result = await self._check_grace_period(workspace_id, goal_data, recent_tasks)
            if not grace_period_result.should_proceed:
                return grace_period_result
            
            # 2. Analyze workspace progress velocity
            velocity_result = await self._analyze_progress_velocity(workspace_id, goal_data)
            if not velocity_result.should_proceed:
                return velocity_result
            
            # 3. Apply adaptive thresholds based on workspace characteristics
            if self.adaptive_threshold_enabled:
                adaptive_result = await self._apply_adaptive_thresholds(workspace_id, goal_data)
                if not adaptive_result.should_proceed:
                    return adaptive_result
            
            # 4. All checks passed - proceed with normal validation
            return ValidationOptimizationResult(
                should_proceed=True,
                decision=ValidationDecision.PROCEED_NORMAL,
                reason="All optimization checks passed",
                confidence=0.9
            )
            
        except Exception as e:
            logger.error(f"Error in validation optimization for workspace {workspace_id}: {e}")
            # Fail safe - allow validation to proceed
            return ValidationOptimizationResult(
                should_proceed=True,
                decision=ValidationDecision.PROCEED_NORMAL,
                reason=f"Optimization error: {e}",
                confidence=0.5
            )
    
    async def _check_grace_period(
        self, 
        workspace_id: str, 
        goal_data: Dict,
        recent_tasks: Optional[List[Dict]] = None
    ) -> ValidationOptimizationResult:
        """
        🕒 GRACE PERIOD CHECK: Skip validation for recently created tasks/goals
        """
        try:
            # Check goal creation time
            goal_created_at = goal_data.get("created_at")
            if goal_created_at:
                goal_age = self._calculate_age_hours(goal_created_at)
                if goal_age < self.default_grace_period_hours:
                    remaining_hours = self.default_grace_period_hours - goal_age
                    return ValidationOptimizationResult(
                        should_proceed=False,
                        decision=ValidationDecision.APPLY_GRACE_PERIOD,
                        reason=f"Goal created {goal_age:.1f}h ago, within grace period",
                        confidence=0.95,
                        grace_period_remaining_hours=remaining_hours
                    )
            
            # Check recent task creation for this goal
            if recent_tasks is None:
                recent_tasks = await self._get_recent_tasks_for_goal(workspace_id, goal_data.get("id"))
            
            recent_task_count = len([
                task for task in recent_tasks 
                if self._calculate_age_hours(task.get("created_at", "")) < self.default_grace_period_hours
            ])
            
            if recent_task_count > 0:
                return ValidationOptimizationResult(
                    should_proceed=False,
                    decision=ValidationDecision.APPLY_GRACE_PERIOD,
                    reason=f"{recent_task_count} tasks created within grace period",
                    confidence=0.9,
                    grace_period_remaining_hours=self.default_grace_period_hours
                )
            
            # Grace period check passed
            return ValidationOptimizationResult(
                should_proceed=True,
                decision=ValidationDecision.PROCEED_NORMAL,
                reason="Grace period check passed",
                confidence=0.8
            )
            
        except Exception as e:
            logger.error(f"Error in grace period check: {e}")
            return ValidationOptimizationResult(
                should_proceed=True,
                decision=ValidationDecision.PROCEED_NORMAL,
                reason=f"Grace period check error: {e}",
                confidence=0.5
            )
    
    async def _analyze_progress_velocity(
        self, 
        workspace_id: str, 
        goal_data: Dict
    ) -> ValidationOptimizationResult:
        """
        📈 VELOCITY ANALYSIS: Check if workspace is making acceptable progress
        """
        try:
            # Get workspace progress analysis (cached)
            workspace_analysis = await self._get_workspace_progress_analysis(workspace_id)
            
            velocity_score = self._calculate_velocity_score(workspace_analysis)
            
            # Determine if velocity is acceptable
            if workspace_analysis.velocity_classification == ProgressVelocity.EXCELLENT:
                return ValidationOptimizationResult(
                    should_proceed=False,
                    decision=ValidationDecision.VELOCITY_ACCEPTABLE,
                    reason=f"Excellent progress velocity: {velocity_score:.2f}",
                    confidence=0.95,
                    velocity_score=velocity_score
                )
            elif workspace_analysis.velocity_classification == ProgressVelocity.GOOD:
                return ValidationOptimizationResult(
                    should_proceed=False,
                    decision=ValidationDecision.VELOCITY_ACCEPTABLE,
                    reason=f"Good progress velocity: {velocity_score:.2f}",
                    confidence=0.85,
                    velocity_score=velocity_score
                )
            elif workspace_analysis.velocity_classification == ProgressVelocity.MODERATE:
                # Moderate velocity - proceed with caution
                return ValidationOptimizationResult(
                    should_proceed=True,
                    decision=ValidationDecision.PROCEED_NORMAL,
                    reason=f"Moderate velocity: {velocity_score:.2f} - proceed with validation",
                    confidence=0.7,
                    velocity_score=velocity_score
                )
            else:
                # Slow or stalled - definitely need validation
                return ValidationOptimizationResult(
                    should_proceed=True,
                    decision=ValidationDecision.PROCEED_NORMAL,
                    reason=f"Slow/stalled velocity: {velocity_score:.2f} - validation needed",
                    confidence=0.9,
                    velocity_score=velocity_score
                )
                
        except Exception as e:
            logger.error(f"Error in velocity analysis: {e}")
            return ValidationOptimizationResult(
                should_proceed=True,
                decision=ValidationDecision.PROCEED_NORMAL,
                reason=f"Velocity analysis error: {e}",
                confidence=0.5
            )
    
    async def _apply_adaptive_thresholds(
        self, 
        workspace_id: str, 
        goal_data: Dict
    ) -> ValidationOptimizationResult:
        """
        🎯 ADAPTIVE THRESHOLDS: Adjust validation strictness based on workspace context
        """
        try:
            workspace_analysis = await self._get_workspace_progress_analysis(workspace_id)
            
            # Calculate adaptive threshold based on workspace characteristics
            base_threshold = self.base_validation_threshold
            
            # Adjustments based on workspace state
            adjustments = 0.0
            
            # Recent activity adjustment
            if workspace_analysis.recent_completions_24h > 0:
                adjustments += 0.1  # More lenient if recent completions
            
            # Task age adjustment
            if workspace_analysis.average_task_age_hours < 24:
                adjustments += 0.1  # More lenient for newer workspaces
            
            # Progress trend adjustment
            if workspace_analysis.progress_trend == "improving":
                adjustments += 0.15  # More lenient if improving
            elif workspace_analysis.progress_trend == "declining":
                adjustments -= 0.1   # More strict if declining
            
            # Apply bounds
            adjustments = max(-self.max_threshold_adjustment, min(self.max_threshold_adjustment, adjustments))
            adaptive_threshold = base_threshold + adjustments
            
            # Check if adaptive threshold suggests skipping validation
            current_completion_rate = workspace_analysis.overall_completion_rate
            
            if current_completion_rate >= adaptive_threshold:
                return ValidationOptimizationResult(
                    should_proceed=False,
                    decision=ValidationDecision.THRESHOLD_ADJUSTED,
                    reason=f"Adaptive threshold met: {current_completion_rate:.2f} >= {adaptive_threshold:.2f}",
                    confidence=0.8,
                    adaptive_threshold=adaptive_threshold
                )
            else:
                return ValidationOptimizationResult(
                    should_proceed=True,
                    decision=ValidationDecision.PROCEED_NORMAL,
                    reason=f"Below adaptive threshold: {current_completion_rate:.2f} < {adaptive_threshold:.2f}",
                    confidence=0.8,
                    adaptive_threshold=adaptive_threshold
                )
                
        except Exception as e:
            logger.error(f"Error in adaptive threshold calculation: {e}")
            return ValidationOptimizationResult(
                should_proceed=True,
                decision=ValidationDecision.PROCEED_NORMAL,
                reason=f"Adaptive threshold error: {e}",
                confidence=0.5
            )
    
    async def _get_workspace_progress_analysis(self, workspace_id: str) -> WorkspaceProgressAnalysis:
        """Get comprehensive workspace progress analysis (with caching)"""
        current_time = datetime.now().timestamp()
        
        # Check cache
        if workspace_id in self.workspace_analysis_cache:
            cache_time, cached_analysis = self.workspace_analysis_cache[workspace_id]
            if current_time - cache_time < self.cache_duration:
                return cached_analysis
        
        # Generate new analysis
        analysis = await self._generate_workspace_progress_analysis(workspace_id)
        
        # Cache result
        self.workspace_analysis_cache[workspace_id] = (current_time, analysis)
        
        return analysis
    
    async def _generate_workspace_progress_analysis(self, workspace_id: str) -> WorkspaceProgressAnalysis:
        """Generate comprehensive workspace progress analysis"""
        try:
            # Get all tasks for workspace
            tasks_response = supabase.table("tasks").select("*").eq(
                "workspace_id", workspace_id
            ).execute()
            
            tasks = tasks_response.data or []
            
            # Basic metrics
            total_tasks = len(tasks)
            completed_tasks = len([t for t in tasks if t.get("status") == "completed"])
            active_tasks = len([t for t in tasks if t.get("status") in ["pending", "in_progress"]])
            
            overall_completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0.0
            
            # Calculate task ages and recent activity
            current_time = datetime.now()
            task_ages = []
            recent_completions = 0
            
            for task in tasks:
                if task.get("created_at"):
                    age_hours = self._calculate_age_hours(task["created_at"])
                    task_ages.append(age_hours)
                    
                    # Check for recent completions
                    if (task.get("status") == "completed" and 
                        task.get("updated_at") and 
                        self._calculate_age_hours(task["updated_at"]) < 24):
                        recent_completions += 1
            
            average_task_age = sum(task_ages) / len(task_ages) if task_ages else 0
            
            # Calculate velocity score
            velocity_score = self._calculate_workspace_velocity_score(
                total_tasks, completed_tasks, recent_completions, average_task_age
            )
            
            # Classify velocity
            velocity_classification = self._classify_velocity(velocity_score)
            
            # Determine progress trend
            progress_trend = self._determine_progress_trend(tasks)
            
            # Recommend action
            recommended_action = self._recommend_validation_action(
                velocity_classification, overall_completion_rate, recent_completions
            )
            
            return WorkspaceProgressAnalysis(
                workspace_id=workspace_id,
                total_tasks=total_tasks,
                active_tasks=active_tasks,
                completed_tasks=completed_tasks,
                overall_completion_rate=overall_completion_rate,
                velocity_classification=velocity_classification,
                average_task_age_hours=average_task_age,
                recent_completions_24h=recent_completions,
                progress_trend=progress_trend,
                recommended_action=recommended_action
            )
            
        except Exception as e:
            logger.error(f"Error generating workspace analysis for {workspace_id}: {e}")
            # Return minimal analysis
            return WorkspaceProgressAnalysis(
                workspace_id=workspace_id,
                total_tasks=0,
                active_tasks=0,
                completed_tasks=0,
                overall_completion_rate=0.0,
                velocity_classification=ProgressVelocity.STALLED,
                average_task_age_hours=0.0,
                recent_completions_24h=0,
                progress_trend="unknown",
                recommended_action=ValidationDecision.PROCEED_NORMAL
            )
    
    def _calculate_workspace_velocity_score(
        self, 
        total_tasks: int, 
        completed_tasks: int, 
        recent_completions: int, 
        average_age: float
    ) -> float:
        """Calculate overall workspace velocity score (0.0 - 1.0)"""
        if total_tasks == 0:
            return 0.0
        
        # Base completion rate
        completion_rate = completed_tasks / total_tasks
        
        # Recent activity bonus
        recent_activity_bonus = min(recent_completions / max(total_tasks, 1), 0.3)
        
        # Age penalty (older workspaces with low completion get penalty)
        age_penalty = 0.0
        if average_age > 48:  # More than 2 days
            age_penalty = min((average_age - 48) / 168, 0.2)  # Max 20% penalty after a week
        
        velocity_score = completion_rate + recent_activity_bonus - age_penalty
        return max(0.0, min(1.0, velocity_score))
    
    def _classify_velocity(self, velocity_score: float) -> ProgressVelocity:
        """Classify velocity score into categories"""
        if velocity_score >= self.excellent_velocity_threshold:
            return ProgressVelocity.EXCELLENT
        elif velocity_score >= self.good_velocity_threshold:
            return ProgressVelocity.GOOD
        elif velocity_score >= self.moderate_velocity_threshold:
            return ProgressVelocity.MODERATE
        elif velocity_score >= self.slow_velocity_threshold:
            return ProgressVelocity.SLOW
        else:
            return ProgressVelocity.STALLED
    
    def _calculate_velocity_score(self, analysis: WorkspaceProgressAnalysis) -> float:
        """Calculate velocity score from analysis"""
        return self._calculate_workspace_velocity_score(
            analysis.total_tasks,
            analysis.completed_tasks,
            analysis.recent_completions_24h,
            analysis.average_task_age_hours
        )
    
    def _determine_progress_trend(self, tasks: List[Dict]) -> str:
        """Determine if workspace progress is improving, stable, or declining"""
        try:
            current_time = datetime.now()
            
            # Get completions in last 24h vs previous 24h
            completions_last_24h = 0
            completions_prev_24h = 0
            
            for task in tasks:
                if task.get("status") == "completed" and task.get("updated_at"):
                    age_hours = self._calculate_age_hours(task["updated_at"])
                    if age_hours < 24:
                        completions_last_24h += 1
                    elif 24 <= age_hours < 48:
                        completions_prev_24h += 1
            
            if completions_last_24h > completions_prev_24h:
                return "improving"
            elif completions_last_24h < completions_prev_24h:
                return "declining"
            else:
                return "stable"
                
        except Exception:
            return "unknown"
    
    def _recommend_validation_action(
        self, 
        velocity: ProgressVelocity, 
        completion_rate: float, 
        recent_completions: int
    ) -> ValidationDecision:
        """Recommend validation action based on metrics"""
        if velocity in [ProgressVelocity.EXCELLENT, ProgressVelocity.GOOD]:
            return ValidationDecision.VELOCITY_ACCEPTABLE
        elif velocity == ProgressVelocity.MODERATE and recent_completions > 0:
            return ValidationDecision.THRESHOLD_ADJUSTED
        else:
            return ValidationDecision.PROCEED_NORMAL
    
    async def _get_recent_tasks_for_goal(self, workspace_id: str, goal_id: str) -> List[Dict]:
        """Get recent tasks related to a specific goal"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=self.velocity_tracking_window_hours)
            
            response = supabase.table("tasks").select("*").eq(
                "workspace_id", workspace_id
            ).eq(
                "goal_id", goal_id
            ).gte(
                "created_at", cutoff_time.isoformat()
            ).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error getting recent tasks for goal {goal_id}: {e}")
            return []
    
    def _calculate_age_hours(self, timestamp_str: str) -> float:
        """Calculate age in hours from timestamp string"""
        try:
            if not timestamp_str:
                return 0.0
            
            # Handle various timestamp formats
            timestamp_str = timestamp_str.replace('Z', '+00:00')
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            
            # Remove timezone info for calculation
            if timestamp.tzinfo:
                timestamp = timestamp.replace(tzinfo=None)
            
            age = datetime.now() - timestamp
            return age.total_seconds() / 3600
            
        except Exception as e:
            logger.error(f"Error calculating age from timestamp {timestamp_str}: {e}")
            return 0.0
    
    async def get_optimization_stats(self, workspace_id: Optional[str] = None) -> Dict:
        """Get optimization statistics"""
        try:
            stats = {
                "optimization_enabled": self.enable_optimization,
                "grace_period_hours": self.default_grace_period_hours,
                "velocity_window_hours": self.velocity_tracking_window_hours,
                "adaptive_thresholds_enabled": self.adaptive_threshold_enabled,
                "cached_analyses": len(self.workspace_analysis_cache)
            }
            
            if workspace_id:
                analysis = await self._get_workspace_progress_analysis(workspace_id)
                stats["workspace_analysis"] = {
                    "total_tasks": analysis.total_tasks,
                    "completion_rate": analysis.overall_completion_rate,
                    "velocity_classification": analysis.velocity_classification.value,
                    "recent_completions": analysis.recent_completions_24h,
                    "progress_trend": analysis.progress_trend,
                    "recommended_action": analysis.recommended_action.value
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting optimization stats: {e}")
            return {"error": str(e)}

# Global instance
goal_validation_optimizer = GoalValidationOptimizer()