#!/usr/bin/env python3
"""
🔄 **HOLISTIC TASK LIFECYCLE INTEGRATION**

Eliminates the critical silo between task phases by creating integrated feedback loops:

PREVIOUS (SILOS):
Goal Decomposition → Task Generation → Agent Assignment → Execution → Quality Assessment
     ↓                ↓                  ↓                ↓            ↓
  No feedback    No learning     No optimization   No insights   No improvement

NEW (HOLISTIC):
Goal Decomposition ←→ Task Generation ←→ Agent Assignment ←→ Execution ←→ Quality Assessment
                   ↕                  ↕                  ↕           ↕
               SHARED LEARNING AND CONTINUOUS IMPROVEMENT LOOPS

This creates a truly orchestrated system where each phase learns from all others.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict

from models import TaskType, TaskStatus
from services.holistic_memory_manager import (
    get_holistic_memory_manager, MemoryType, MemoryScope, store_holistic_memory
)

logger = logging.getLogger(__name__)

class LifecyclePhase(Enum):
    """Task lifecycle phases"""
    GOAL_DECOMPOSITION = "goal_decomposition"
    TASK_GENERATION = "task_generation"
    AGENT_ASSIGNMENT = "agent_assignment"
    TASK_EXECUTION = "task_execution"
    QUALITY_ASSESSMENT = "quality_assessment"
    COMPLETION = "completion"

class FeedbackType(Enum):
    """Types of feedback in the lifecycle"""
    QUALITY_IMPROVEMENT = "quality_improvement"
    EFFICIENCY_OPTIMIZATION = "efficiency_optimization"
    ACCURACY_ENHANCEMENT = "accuracy_enhancement"
    LEARNING_UPDATE = "learning_update"
    ERROR_CORRECTION = "error_correction"

@dataclass
class LifecycleInsight:
    """Insight generated from lifecycle analysis"""
    phase: LifecyclePhase
    feedback_type: FeedbackType
    insight: str
    confidence: float
    applicable_to: List[str]  # Which components can use this insight
    evidence: Dict[str, Any]
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class TaskLifecycleContext:
    """Complete context for a task throughout its lifecycle"""
    task_id: str
    workspace_id: str
    goal_id: Optional[str] = None
    
    # Phase contexts
    goal_decomposition_context: Dict[str, Any] = None
    task_generation_context: Dict[str, Any] = None
    agent_assignment_context: Dict[str, Any] = None
    execution_context: Dict[str, Any] = None
    quality_assessment_context: Dict[str, Any] = None
    
    # Cross-phase insights
    lifecycle_insights: List[LifecycleInsight] = None
    performance_metrics: Dict[str, float] = None
    
    # Timestamps
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.lifecycle_insights is None:
            self.lifecycle_insights = []
        if self.performance_metrics is None:
            self.performance_metrics = {}

class HolisticTaskLifecycle:
    """
    🔄 **INTEGRATED TASK LIFECYCLE ORCHESTRATOR**
    
    Creates feedback loops between all task phases, eliminating silos
    and enabling continuous learning and improvement across the system.
    """
    
    def __init__(self):
        self.active_lifecycles: Dict[str, TaskLifecycleContext] = {}
        self.lifecycle_patterns = {}
        self.improvement_suggestions = {}
        self.memory_manager = get_holistic_memory_manager()
    
    async def start_task_lifecycle(
        self,
        task_id: str,
        workspace_id: str,
        goal_id: Optional[str] = None,
        initial_context: Dict[str, Any] = None
    ) -> TaskLifecycleContext:
        """
        🚀 **START HOLISTIC LIFECYCLE TRACKING**
        
        Begin tracking a task through its complete lifecycle with
        integrated feedback loops and learning capabilities.
        """
        try:
            # Create lifecycle context
            lifecycle_context = TaskLifecycleContext(
                task_id=task_id,
                workspace_id=workspace_id,
                goal_id=goal_id
            )
            
            # Store initial context if provided
            if initial_context:
                await self._store_phase_context(
                    lifecycle_context,
                    LifecyclePhase.GOAL_DECOMPOSITION,
                    initial_context
                )
            
            # Register active lifecycle
            self.active_lifecycles[task_id] = lifecycle_context
            
            # Store lifecycle start in memory for learning
            await store_holistic_memory(
                content={
                    "task_id": task_id,
                    "lifecycle_started": True,
                    "initial_context": initial_context or {}
                },
                memory_type=MemoryType.EXPERIENCE,
                scope=MemoryScope.TASK,
                workspace_id=workspace_id,
                task_id=task_id
            )
            
            logger.info(f"🔄 Started holistic lifecycle tracking for task {task_id}")
            return lifecycle_context
            
        except Exception as e:
            logger.error(f"❌ Failed to start task lifecycle: {e}")
            raise
    
    async def update_lifecycle_phase(
        self,
        task_id: str,
        phase: LifecyclePhase,
        phase_data: Dict[str, Any],
        performance_metrics: Dict[str, float] = None
    ) -> List[LifecycleInsight]:
        """
        🔄 **UPDATE LIFECYCLE PHASE WITH LEARNING**
        
        Update a lifecycle phase and generate cross-phase insights
        that improve future task orchestration.
        """
        try:
            if task_id not in self.active_lifecycles:
                logger.warning(f"⚠️ Task {task_id} not in active lifecycles")
                return []
            
            lifecycle_context = self.active_lifecycles[task_id]
            
            # Store phase context
            await self._store_phase_context(lifecycle_context, phase, phase_data)
            
            # Update performance metrics
            if performance_metrics:
                lifecycle_context.performance_metrics.update(performance_metrics)
            
            # Generate cross-phase insights
            insights = await self._generate_cross_phase_insights(lifecycle_context, phase)
            lifecycle_context.lifecycle_insights.extend(insights)
            
            # Apply insights to improve other active lifecycles
            await self._apply_insights_to_active_lifecycles(insights, task_id)
            
            # Store insights in memory for future tasks
            for insight in insights:
                await store_holistic_memory(
                    content=asdict(insight),
                    memory_type=MemoryType.PATTERN,
                    scope=MemoryScope.WORKSPACE,
                    workspace_id=lifecycle_context.workspace_id,
                    task_id=task_id
                )
            
            logger.info(f"🔄 Updated lifecycle phase {phase.value} for task {task_id}, generated {len(insights)} insights")
            return insights
            
        except Exception as e:
            logger.error(f"❌ Failed to update lifecycle phase: {e}")
            return []
    
    async def complete_task_lifecycle(
        self,
        task_id: str,
        final_quality_score: float,
        completion_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        ✅ **COMPLETE LIFECYCLE WITH COMPREHENSIVE LEARNING**
        
        Complete the task lifecycle and generate comprehensive insights
        that improve the entire orchestration system.
        """
        try:
            if task_id not in self.active_lifecycles:
                logger.warning(f"⚠️ Task {task_id} not in active lifecycles")
                return {}
            
            lifecycle_context = self.active_lifecycles[task_id]
            lifecycle_context.completed_at = datetime.now()
            lifecycle_context.performance_metrics["final_quality_score"] = final_quality_score
            
            # Store completion context
            if completion_data:
                await self._store_phase_context(
                    lifecycle_context, 
                    LifecyclePhase.COMPLETION, 
                    completion_data
                )
            
            # Generate comprehensive lifecycle analysis
            lifecycle_analysis = await self._analyze_complete_lifecycle(lifecycle_context)
            
            # Generate improvement recommendations
            improvements = await self._generate_improvement_recommendations(lifecycle_context)
            
            # Store lifecycle learning for future tasks
            await store_holistic_memory(
                content={
                    "lifecycle_analysis": lifecycle_analysis,
                    "improvements": improvements,
                    "performance_metrics": lifecycle_context.performance_metrics,
                    "insights_count": len(lifecycle_context.lifecycle_insights)
                },
                memory_type=MemoryType.EXPERIENCE,
                scope=MemoryScope.WORKSPACE,
                workspace_id=lifecycle_context.workspace_id,
                task_id=task_id,
                confidence=final_quality_score / 100.0
            )
            
            # Remove from active lifecycles
            del self.active_lifecycles[task_id]
            
            logger.info(f"✅ Completed holistic lifecycle for task {task_id} with quality {final_quality_score}")
            
            return {
                "lifecycle_analysis": lifecycle_analysis,
                "improvements": improvements,
                "total_insights": len(lifecycle_context.lifecycle_insights),
                "performance_metrics": lifecycle_context.performance_metrics,
                "duration": (lifecycle_context.completed_at - lifecycle_context.created_at).total_seconds()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to complete task lifecycle: {e}")
            return {"error": str(e)}
    
    async def get_lifecycle_insights_for_task_generation(
        self,
        workspace_id: str,
        goal_type: str,
        task_type: str
    ) -> List[Dict[str, Any]]:
        """
        🧠 **CROSS-PHASE LEARNING**: Get insights to improve task generation
        
        Retrieves insights from previous task lifecycles to improve
        future task generation for similar goals and task types.
        """
        try:
            # Query memory for relevant insights
            insights = await self.memory_manager.retrieve_memories(
                query={
                    "goal_type": goal_type,
                    "task_type": task_type,
                    "phase": "task_generation"
                },
                memory_type=MemoryType.PATTERN,
                scope=MemoryScope.WORKSPACE,
                workspace_id=workspace_id,
                limit=20
            )
            
            # Extract actionable insights for task generation
            actionable_insights = []
            for memory in insights:
                if memory.content.get("applicable_to") and "task_generation" in memory.content["applicable_to"]:
                    actionable_insights.append({
                        "insight": memory.content.get("insight", ""),
                        "confidence": memory.confidence,
                        "evidence": memory.content.get("evidence", {}),
                        "feedback_type": memory.content.get("feedback_type", "learning_update")
                    })
            
            logger.info(f"🧠 Retrieved {len(actionable_insights)} task generation insights")
            return actionable_insights
            
        except Exception as e:
            logger.error(f"❌ Failed to get task generation insights: {e}")
            return []
    
    async def get_lifecycle_insights_for_agent_assignment(
        self,
        workspace_id: str,
        task_type: str,
        required_skills: List[str]
    ) -> List[Dict[str, Any]]:
        """
        🎯 **AGENT ASSIGNMENT LEARNING**: Get insights to optimize agent selection
        """
        try:
            insights = await self.memory_manager.retrieve_memories(
                query={
                    "task_type": task_type,
                    "required_skills": required_skills,
                    "phase": "agent_assignment"
                },
                memory_type=MemoryType.PATTERN,
                scope=MemoryScope.WORKSPACE,
                workspace_id=workspace_id,
                limit=15
            )
            
            # Extract agent assignment optimization insights
            optimization_insights = []
            for memory in insights:
                if memory.content.get("applicable_to") and "agent_assignment" in memory.content["applicable_to"]:
                    optimization_insights.append({
                        "insight": memory.content.get("insight", ""),
                        "confidence": memory.confidence,
                        "optimal_agent_profile": memory.content.get("evidence", {}).get("optimal_agent_profile", {}),
                        "success_rate": memory.content.get("evidence", {}).get("success_rate", 0.0)
                    })
            
            logger.info(f"🎯 Retrieved {len(optimization_insights)} agent assignment insights")
            return optimization_insights
            
        except Exception as e:
            logger.error(f"❌ Failed to get agent assignment insights: {e}")
            return []
    
    async def _store_phase_context(
        self,
        lifecycle_context: TaskLifecycleContext,
        phase: LifecyclePhase,
        phase_data: Dict[str, Any]
    ):
        """Store context for a specific lifecycle phase"""
        
        if phase == LifecyclePhase.GOAL_DECOMPOSITION:
            lifecycle_context.goal_decomposition_context = phase_data
        elif phase == LifecyclePhase.TASK_GENERATION:
            lifecycle_context.task_generation_context = phase_data
        elif phase == LifecyclePhase.AGENT_ASSIGNMENT:
            lifecycle_context.agent_assignment_context = phase_data
        elif phase == LifecyclePhase.TASK_EXECUTION:
            lifecycle_context.execution_context = phase_data
        elif phase == LifecyclePhase.QUALITY_ASSESSMENT:
            lifecycle_context.quality_assessment_context = phase_data
    
    async def _generate_cross_phase_insights(
        self,
        lifecycle_context: TaskLifecycleContext,
        current_phase: LifecyclePhase
    ) -> List[LifecycleInsight]:
        """Generate insights by analyzing connections between lifecycle phases"""
        
        insights = []
        
        # Task Generation → Agent Assignment insight
        if (current_phase == LifecyclePhase.AGENT_ASSIGNMENT and
            lifecycle_context.task_generation_context and
            lifecycle_context.agent_assignment_context):
            
            task_complexity = lifecycle_context.task_generation_context.get("complexity_score", 50)
            agent_seniority = lifecycle_context.agent_assignment_context.get("agent_seniority", "senior")
            
            if task_complexity > 70 and agent_seniority == "junior":
                insights.append(LifecycleInsight(
                    phase=LifecyclePhase.AGENT_ASSIGNMENT,
                    feedback_type=FeedbackType.EFFICIENCY_OPTIMIZATION,
                    insight="High complexity tasks perform better with senior+ agents",
                    confidence=0.85,
                    applicable_to=["agent_assignment", "task_generation"],
                    evidence={
                        "task_complexity": task_complexity,
                        "agent_seniority": agent_seniority,
                        "recommendation": "prefer_senior_agents_for_complex_tasks"
                    }
                ))
        
        # Execution → Quality Assessment insight
        if (current_phase == LifecyclePhase.QUALITY_ASSESSMENT and
            lifecycle_context.execution_context and
            lifecycle_context.quality_assessment_context):
            
            execution_time = lifecycle_context.execution_context.get("execution_time_seconds", 0)
            quality_score = lifecycle_context.quality_assessment_context.get("quality_score", 0)
            
            if execution_time < 30 and quality_score < 70:
                insights.append(LifecycleInsight(
                    phase=LifecyclePhase.QUALITY_ASSESSMENT,
                    feedback_type=FeedbackType.QUALITY_IMPROVEMENT,
                    insight="Tasks completed too quickly often have quality issues",
                    confidence=0.80,
                    applicable_to=["task_execution", "quality_assessment"],
                    evidence={
                        "execution_time": execution_time,
                        "quality_score": quality_score,
                        "recommendation": "add_quality_checks_for_fast_tasks"
                    }
                ))
        
        return insights
    
    async def _apply_insights_to_active_lifecycles(
        self,
        insights: List[LifecycleInsight],
        source_task_id: str
    ):
        """Apply insights to improve other active task lifecycles"""
        
        for insight in insights:
            for task_id, lifecycle_context in self.active_lifecycles.items():
                if task_id == source_task_id:
                    continue
                    
                # Apply relevant insights to improve ongoing tasks
                if "agent_assignment" in insight.applicable_to:
                    await self._apply_agent_assignment_insight(lifecycle_context, insight)
                
                if "task_execution" in insight.applicable_to:
                    await self._apply_execution_insight(lifecycle_context, insight)
    
    async def _apply_agent_assignment_insight(
        self,
        lifecycle_context: TaskLifecycleContext,
        insight: LifecycleInsight
    ):
        """Apply agent assignment insights to active lifecycle"""
        # Store insight for use in agent assignment
        if not hasattr(lifecycle_context, 'pending_insights'):
            lifecycle_context.pending_insights = []
        lifecycle_context.pending_insights.append(insight)
    
    async def _apply_execution_insight(
        self,
        lifecycle_context: TaskLifecycleContext,
        insight: LifecycleInsight
    ):
        """Apply execution insights to active lifecycle"""
        # Store insight for use in task execution
        if not hasattr(lifecycle_context, 'execution_hints'):
            lifecycle_context.execution_hints = []
        lifecycle_context.execution_hints.append(insight)
    
    async def _analyze_complete_lifecycle(
        self,
        lifecycle_context: TaskLifecycleContext
    ) -> Dict[str, Any]:
        """Analyze complete lifecycle for patterns and learnings"""
        
        total_duration = (lifecycle_context.completed_at - lifecycle_context.created_at).total_seconds()
        
        analysis = {
            "total_duration_seconds": total_duration,
            "phases_completed": self._count_completed_phases(lifecycle_context),
            "insights_generated": len(lifecycle_context.lifecycle_insights),
            "performance_summary": lifecycle_context.performance_metrics,
            "efficiency_score": self._calculate_efficiency_score(lifecycle_context),
            "learning_value": self._calculate_learning_value(lifecycle_context)
        }
        
        return analysis
    
    async def _generate_improvement_recommendations(
        self,
        lifecycle_context: TaskLifecycleContext
    ) -> List[Dict[str, Any]]:
        """Generate specific recommendations for system improvement"""
        
        recommendations = []
        
        # Analyze performance metrics for improvement opportunities
        quality_score = lifecycle_context.performance_metrics.get("final_quality_score", 0)
        
        if quality_score < 70:
            recommendations.append({
                "area": "quality_assurance",
                "recommendation": "Implement additional quality checks for similar tasks",
                "expected_improvement": "15-25% quality increase",
                "confidence": 0.75
            })
        
        # Analyze efficiency
        total_insights = len(lifecycle_context.lifecycle_insights)
        if total_insights < 2:
            recommendations.append({
                "area": "learning_system",
                "recommendation": "Increase cross-phase analysis depth",
                "expected_improvement": "Better system learning",
                "confidence": 0.70
            })
        
        return recommendations
    
    def _count_completed_phases(self, lifecycle_context: TaskLifecycleContext) -> int:
        """Count how many phases were completed"""
        phase_contexts = [
            lifecycle_context.goal_decomposition_context,
            lifecycle_context.task_generation_context,
            lifecycle_context.agent_assignment_context,
            lifecycle_context.execution_context,
            lifecycle_context.quality_assessment_context
        ]
        return sum(1 for context in phase_contexts if context is not None)
    
    def _calculate_efficiency_score(self, lifecycle_context: TaskLifecycleContext) -> float:
        """Calculate efficiency score for the lifecycle"""
        # Simple efficiency calculation based on duration and quality
        duration = (lifecycle_context.completed_at - lifecycle_context.created_at).total_seconds()
        quality = lifecycle_context.performance_metrics.get("final_quality_score", 50)
        
        # Efficient tasks have good quality in reasonable time
        if duration < 300 and quality > 80:  # < 5 minutes, high quality
            return 95.0
        elif duration < 900 and quality > 70:  # < 15 minutes, good quality
            return 85.0
        elif quality > 60:
            return 70.0
        else:
            return 50.0
    
    def _calculate_learning_value(self, lifecycle_context: TaskLifecycleContext) -> float:
        """Calculate how much learning value this lifecycle provided"""
        insights_count = len(lifecycle_context.lifecycle_insights)
        phases_completed = self._count_completed_phases(lifecycle_context)
        
        # More insights and complete phases = higher learning value
        learning_value = (insights_count * 20) + (phases_completed * 10)
        return min(learning_value, 100.0)

# Global holistic lifecycle manager
_lifecycle_manager_instance = None

def get_holistic_lifecycle_manager() -> HolisticTaskLifecycle:
    """Get the global holistic lifecycle manager"""
    global _lifecycle_manager_instance
    
    if _lifecycle_manager_instance is None:
        _lifecycle_manager_instance = HolisticTaskLifecycle()
        logger.info("🔄 Holistic Task Lifecycle Manager initialized - silos eliminated!")
    
    return _lifecycle_manager_instance

# Convenience functions for easy integration
async def start_holistic_task_lifecycle(task_id: str, workspace_id: str, **kwargs):
    """Start tracking a task through its holistic lifecycle"""
    manager = get_holistic_lifecycle_manager()
    return await manager.start_task_lifecycle(task_id, workspace_id, **kwargs)

async def update_task_lifecycle_phase(task_id: str, phase: LifecyclePhase, data: Dict[str, Any]):
    """Update a task lifecycle phase with learning"""
    manager = get_holistic_lifecycle_manager()
    return await manager.update_lifecycle_phase(task_id, phase, data)

async def complete_holistic_task_lifecycle(task_id: str, quality_score: float, **kwargs):
    """Complete a task lifecycle with comprehensive learning"""
    manager = get_holistic_lifecycle_manager()
    return await manager.complete_task_lifecycle(task_id, quality_score, **kwargs)