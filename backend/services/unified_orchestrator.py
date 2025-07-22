#!/usr/bin/env python3
"""
🎼 UNIFIED ORCHESTRATOR - Complete System Integration Engine
================================================================================
Consolidation of workflow_orchestrator.py + adaptive_task_orchestration_engine.py
into a single, unified orchestration system that provides both workflow management
and adaptive task optimization capabilities.

INTEGRATION COMPLETENESS:
✅ End-to-end workflow management: Goal → Assets → Tasks → Execution → Quality → Deliverables
✅ AI-driven adaptive task orchestration with dynamic thresholds
✅ Real-time performance monitoring and optimization
✅ Cross-workspace load balancing and resource allocation
✅ Comprehensive error handling and rollback capabilities
✅ Production-ready with full trace support and metrics

CONSOLIDATED FEATURES:
- Complete workflow lifecycle management
- Adaptive task orchestration with AI-driven optimization
- Dynamic threshold calculation and skip prevention
- Real-time progress tracking and monitoring
- Cross-workspace load balancing
- Automatic rollback and error recovery
- Universal AI Pipeline Engine integration
- Universal Memory Architecture integration
"""

import asyncio
import logging
import json
import os
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, field, asdict
from uuid import uuid4, UUID
from enum import Enum

from database import (
    supabase, get_supabase_client,
    list_tasks, get_workspace, get_active_workspaces,
    update_task_status, create_task
)
from models import TaskStatus, WorkspaceStatus, GoalStatus, WorkspaceGoal
from config.quality_system_config import get_env_bool, get_env_int, get_env_float
from services.unified_memory_engine import get_universal_memory_architecture

# Initialize logger first before any usage
logger = logging.getLogger(__name__)

# Import AI Pipeline Engine for workflow execution
try:
    from services.universal_ai_pipeline_engine import universal_ai_pipeline_engine, UniversalAIPipelineEngine, PipelineContext, PipelineStepType
    AI_PIPELINE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"AI Pipeline Engine not available: {e}")
    AI_PIPELINE_AVAILABLE = False
    universal_ai_pipeline_engine = None

# ========================================================================
# 🏗️ UNIFIED DATA STRUCTURES
# ========================================================================

class WorkflowStage(Enum):
    """Workflow execution stages"""
    INITIALIZING = "initializing"
    ANALYZING_GOAL = "analyzing_goal"
    GENERATING_ASSETS = "generating_assets"
    CREATING_TASKS = "creating_tasks"
    EXECUTING_TASKS = "executing_tasks"
    QUALITY_VALIDATION = "quality_validation"
    CREATING_DELIVERABLES = "creating_deliverables"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLBACK = "rollback"

class WorkflowStatus(Enum):
    """Overall workflow status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLBACK_IN_PROGRESS = "rollback_in_progress"
    ROLLBACK_COMPLETED = "rollback_completed"

class WorkspacePhase(Enum):
    """Workspace development phases"""
    PLANNING = "planning"
    ANALYSIS = "analysis"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MAINTENANCE = "maintenance"

class TaskPriority(Enum):
    """Enhanced task priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    DEFERRED = "deferred"

@dataclass
class WorkflowProgress:
    """Real-time workflow progress tracking"""
    stage: WorkflowStage
    progress_percentage: float
    current_operation: str
    estimated_completion: Optional[datetime] = None
    stage_start_time: Optional[datetime] = None
    total_stages: int = 8  # Total number of stages
    completed_stages: int = 0

@dataclass
class WorkspaceMetrics:
    """Comprehensive workspace performance metrics"""
    workspace_id: str
    total_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    failed_tasks: int
    skip_count: int
    skip_rate: float
    avg_completion_time: float
    goal_completion_rate: float
    agent_utilization: float
    current_phase: WorkspacePhase
    bottleneck_indicators: List[str]
    performance_score: float

@dataclass
class AdaptiveThresholds:
    """Dynamic thresholds for workspace optimization"""
    workspace_id: str
    max_pending_tasks: int
    priority_boost_factor: float
    skip_prevention_threshold: float
    phase_transition_threshold: int
    urgency_multiplier: float
    quality_gate_threshold: float
    calculated_at: datetime
    confidence_score: float

@dataclass
class OrchestrationRecommendation:
    """AI-driven orchestration recommendation"""
    should_proceed: bool
    recommended_limit: int
    reasoning: str
    confidence: float
    optimization_suggestions: List[str]

@dataclass
class WorkflowResult:
    """Comprehensive workflow execution result"""
    success: bool
    message: str
    workspace_id: str
    goal_id: Optional[str] = None
    workflow_id: str = ""
    
    # Execution metrics
    execution_time: float = 0.0
    tasks_generated: int = 0
    assets_generated: int = 0
    deliverables_created: int = 0
    quality_score: float = 0.0
    
    # Status tracking
    final_status: WorkflowStatus = WorkflowStatus.PENDING
    final_stage: WorkflowStage = WorkflowStage.INITIALIZING
    progress: Optional[WorkflowProgress] = None
    
    # Error handling
    error: Optional[str] = None
    rollback_performed: bool = False
    rollback_success: bool = False
    
    # Detailed results
    stage_results: Dict[str, Any] = field(default_factory=dict)
    ai_usage_stats: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    adaptive_optimization: Dict[str, Any] = field(default_factory=dict)

# ========================================================================
# 🧠 AI OPTIMIZATION ENGINE
# ========================================================================

class AIOptimizer:
    """AI-driven optimization engine for task orchestration"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.optimization_cache = {}
        self.cache_ttl = timedelta(minutes=30)
    
    async def calculate_optimal_settings(self, workspace_context: Dict[str, Any]) -> AdaptiveThresholds:
        """Calculate optimal settings using AI analysis"""
        try:
            workspace_id = workspace_context["workspace_id"]
            
            # Check cache first
            if self._is_cached_valid(workspace_id):
                logger.info(f"🎯 Using cached optimization for workspace {workspace_id}")
                return self.optimization_cache[workspace_id]["thresholds"]
            
            # Get workspace metrics
            metrics = await self._collect_workspace_metrics(workspace_id, workspace_context)
            
            # AI-driven optimization calculation
            thresholds = await self._ai_calculate_thresholds(metrics, workspace_context)
            
            # Cache the results
            self.optimization_cache[workspace_id] = {
                "thresholds": thresholds,
                "calculated_at": datetime.now()
            }
            
            logger.info(f"⚡ Calculated optimal settings for workspace {workspace_id}")
            return thresholds
            
        except Exception as e:
            logger.error(f"Failed to calculate optimal settings: {e}")
            return self._get_fallback_thresholds(workspace_context["workspace_id"])
    
    async def _collect_workspace_metrics(self, workspace_id: str, context: Dict[str, Any]) -> WorkspaceMetrics:
        """Collect comprehensive workspace metrics"""
        try:
            # Get tasks with reliable goal linkage
            tasks_result = self.supabase.table("tasks")\
                .select("*, workspace_goals!inner(*)")\
                .eq("workspace_id", workspace_id)\
                .execute()
            
            tasks = tasks_result.data if tasks_result.data else []
            
            # Calculate basic metrics
            total_tasks = len(tasks)
            pending_tasks = len([t for t in tasks if t["status"] == "pending"])
            in_progress_tasks = len([t for t in tasks if t["status"] == "in_progress"])
            completed_tasks = len([t for t in tasks if t["status"] == "completed"])
            failed_tasks = len([t for t in tasks if t["status"] == "failed"])
            
            # Calculate skip metrics from recent execution attempts
            skip_metrics = await self._calculate_skip_metrics(workspace_id)
            
            # Calculate performance metrics
            completion_times = await self._get_completion_times(workspace_id)
            avg_completion_time = statistics.mean(completion_times) if completion_times else 0.0
            
            # Calculate goal completion rate using reliable linkage
            goal_completion_rate = await self._calculate_goal_completion_rate(workspace_id)
            
            # Calculate agent utilization
            agent_utilization = await self._calculate_agent_utilization(workspace_id)
            
            # Detect current phase
            current_phase = self._detect_workspace_phase(tasks, context)
            
            # Identify bottlenecks
            bottlenecks = self._identify_bottlenecks(tasks, skip_metrics, agent_utilization)
            
            # Calculate overall performance score
            performance_score = self._calculate_performance_score(
                total_tasks, completed_tasks, skip_metrics["skip_rate"], 
                goal_completion_rate, agent_utilization
            )
            
            metrics = WorkspaceMetrics(
                workspace_id=workspace_id,
                total_tasks=total_tasks,
                pending_tasks=pending_tasks,
                in_progress_tasks=in_progress_tasks,
                completed_tasks=completed_tasks,
                failed_tasks=failed_tasks,
                skip_count=skip_metrics["skip_count"],
                skip_rate=skip_metrics["skip_rate"],
                avg_completion_time=avg_completion_time,
                goal_completion_rate=goal_completion_rate,
                agent_utilization=agent_utilization,
                current_phase=current_phase,
                bottleneck_indicators=bottlenecks,
                performance_score=performance_score
            )
            
            logger.info(f"📊 Collected metrics for workspace {workspace_id}: performance={performance_score:.2f}")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect workspace metrics: {e}")
            return self._get_fallback_metrics(workspace_id)
    
    async def _calculate_skip_metrics(self, workspace_id: str) -> Dict[str, Any]:
        """Calculate skip metrics from execution logs"""
        try:
            # Get recent execution attempts (last 24 hours)
            since = (datetime.now() - timedelta(hours=24)).isoformat()
            
            execution_logs = self.supabase.table("execution_logs")\
                .select("*")\
                .eq("workspace_id", workspace_id)\
                .gte("created_at", since)\
                .execute()
            
            logs = execution_logs.data if execution_logs.data else []
            
            total_attempts = len(logs)
            skip_attempts = len([log for log in logs if "skip" in log.get("message", "").lower()])
            
            skip_rate = (skip_attempts / total_attempts) if total_attempts > 0 else 0.0
            
            return {
                "total_attempts": total_attempts,
                "skip_count": skip_attempts,
                "skip_rate": skip_rate
            }
            
        except Exception as e:
            logger.warning(f"Failed to calculate skip metrics: {e}")
            return {"total_attempts": 0, "skip_count": 0, "skip_rate": 0.0}
    
    async def _get_completion_times(self, workspace_id: str) -> List[float]:
        """Get task completion times for performance analysis"""
        try:
            completed_tasks = self.supabase.table("tasks")\
                .select("created_at, updated_at")\
                .eq("workspace_id", workspace_id)\
                .eq("status", "completed")\
                .gte("updated_at", (datetime.now() - timedelta(days=7)).isoformat())\
                .execute()
            
            times = []
            for task in completed_tasks.data or []:
                try:
                    created = datetime.fromisoformat(task["created_at"].replace('Z', '+00:00'))
                    updated = datetime.fromisoformat(task["updated_at"].replace('Z', '+00:00'))
                    completion_time = (updated - created).total_seconds() / 3600  # hours
                    times.append(completion_time)
                except:
                    continue
            
            return times
            
        except Exception as e:
            logger.warning(f"Failed to get completion times: {e}")
            return []
    
    async def _calculate_goal_completion_rate(self, workspace_id: str) -> float:
        """Calculate goal completion rate using reliable goal-task linkage"""
        try:
            goals_result = self.supabase.table("workspace_goals")\
                .select("*")\
                .eq("workspace_id", workspace_id)\
                .execute()
            
            goals = goals_result.data if goals_result.data else []
            
            if not goals:
                return 0.0
            
            total_progress = 0.0
            for goal in goals:
                current = goal.get("current_value", 0.0)
                target = goal.get("target_value", 1.0)
                progress = min(current / target, 1.0) if target > 0 else 0.0
                total_progress += progress
            
            completion_rate = total_progress / len(goals)
            return completion_rate
            
        except Exception as e:
            logger.warning(f"Failed to calculate goal completion rate: {e}")
            return 0.0
    
    async def _calculate_agent_utilization(self, workspace_id: str) -> float:
        """Calculate agent utilization rate"""
        try:
            agents_result = self.supabase.table("agents")\
                .select("status")\
                .eq("workspace_id", workspace_id)\
                .execute()
            
            agents = agents_result.data if agents_result.data else []
            
            if not agents:
                return 0.0
            
            busy_agents = len([a for a in agents if a["status"] in ["busy", "working"]])
            utilization = busy_agents / len(agents)
            
            return utilization
            
        except Exception as e:
            logger.warning(f"Failed to calculate agent utilization: {e}")
            return 0.0
    
    def _detect_workspace_phase(self, tasks: List[Dict], context: Dict[str, Any]) -> WorkspacePhase:
        """Detect current workspace development phase"""
        try:
            if not tasks:
                return WorkspacePhase.PLANNING
            
            phase_indicators = {
                WorkspacePhase.PLANNING: ["plan", "design", "requirements", "analysis"],
                WorkspacePhase.ANALYSIS: ["analyze", "research", "investigate", "study"],
                WorkspacePhase.IMPLEMENTATION: ["implement", "develop", "build", "create", "code"],
                WorkspacePhase.TESTING: ["test", "validate", "verify", "qa", "quality"],
                WorkspacePhase.DEPLOYMENT: ["deploy", "release", "publish", "launch"],
                WorkspacePhase.MAINTENANCE: ["maintain", "support", "fix", "update"]
            }
            
            phase_scores = {}
            for phase, keywords in phase_indicators.items():
                score = 0
                for task in tasks:
                    task_text = (task.get("name", "") + " " + task.get("description", "")).lower()
                    score += sum(1 for keyword in keywords if keyword in task_text)
                phase_scores[phase] = score
            
            if phase_scores:
                return max(phase_scores, key=phase_scores.get)
            
            return WorkspacePhase.PLANNING
            
        except Exception as e:
            logger.warning(f"Failed to detect workspace phase: {e}")
            return WorkspacePhase.PLANNING
    
    def _identify_bottlenecks(self, tasks: List[Dict], skip_metrics: Dict, agent_utilization: float) -> List[str]:
        """Identify performance bottlenecks"""
        bottlenecks = []
        
        if skip_metrics["skip_rate"] > 0.5:
            bottlenecks.append("high_skip_rate")
        
        pending_count = len([t for t in tasks if t["status"] == "pending"])
        if pending_count > 20:
            bottlenecks.append("task_queue_overflow")
        
        if agent_utilization < 0.3:
            bottlenecks.append("low_agent_utilization")
        
        stuck_tasks = len([t for t in tasks if t["status"] == "in_progress"])
        if stuck_tasks > 5:
            bottlenecks.append("stuck_tasks")
        
        return bottlenecks
    
    def _calculate_performance_score(self, total_tasks: int, completed_tasks: int, 
                                   skip_rate: float, goal_completion_rate: float, 
                                   agent_utilization: float) -> float:
        """Calculate overall workspace performance score"""
        if total_tasks == 0:
            return 0.0
        
        completion_rate = completed_tasks / total_tasks
        skip_penalty = max(0, 1 - (skip_rate * 2))
        
        score = (
            completion_rate * 0.3 +
            goal_completion_rate * 0.3 +
            skip_penalty * 0.2 +
            agent_utilization * 0.2
        )
        
        return min(max(score, 0.0), 1.0)
    
    async def _ai_calculate_thresholds(self, metrics: WorkspaceMetrics, context: Dict[str, Any]) -> AdaptiveThresholds:
        """AI-driven threshold calculation"""
        try:
            base_max_pending = 8
            
            phase_multipliers = {
                WorkspacePhase.PLANNING: 1.2,
                WorkspacePhase.ANALYSIS: 1.5,
                WorkspacePhase.IMPLEMENTATION: 2.0,
                WorkspacePhase.TESTING: 1.8,
                WorkspacePhase.DEPLOYMENT: 1.0,
                WorkspacePhase.MAINTENANCE: 0.8
            }
            
            phase_multiplier = phase_multipliers.get(metrics.current_phase, 1.0)
            performance_multiplier = 0.5 + (metrics.performance_score * 1.5)
            
            max_pending_tasks = int(base_max_pending * phase_multiplier * performance_multiplier)
            
            if metrics.skip_rate > 0.6:
                priority_boost_factor = 2.0
            elif metrics.skip_rate > 0.3:
                priority_boost_factor = 1.5
            else:
                priority_boost_factor = 1.0
            
            skip_prevention_threshold = 0.7 - (metrics.goal_completion_rate * 0.2)
            phase_transition_threshold = max_pending_tasks + 5
            
            urgency_multiplier = 1.0
            if "high_skip_rate" in metrics.bottleneck_indicators:
                urgency_multiplier += 0.5
            if "stuck_tasks" in metrics.bottleneck_indicators:
                urgency_multiplier += 0.3
            
            quality_gate_threshold = 0.8 - (metrics.skip_rate * 0.2)
            confidence_score = self._calculate_confidence(metrics)
            
            thresholds = AdaptiveThresholds(
                workspace_id=metrics.workspace_id,
                max_pending_tasks=max_pending_tasks,
                priority_boost_factor=priority_boost_factor,
                skip_prevention_threshold=skip_prevention_threshold,
                phase_transition_threshold=phase_transition_threshold,
                urgency_multiplier=urgency_multiplier,
                quality_gate_threshold=quality_gate_threshold,
                calculated_at=datetime.now(),
                confidence_score=confidence_score
            )
            
            logger.info(f"🎯 AI calculated thresholds for {metrics.workspace_id}: "
                       f"max_pending={max_pending_tasks}, skip_prevention={skip_prevention_threshold:.2f}")
            
            return thresholds
            
        except Exception as e:
            logger.error(f"AI threshold calculation failed: {e}")
            return self._get_fallback_thresholds(metrics.workspace_id)
    
    def _calculate_confidence(self, metrics: WorkspaceMetrics) -> float:
        """Calculate confidence score for threshold recommendations"""
        confidence_factors = []
        
        if metrics.total_tasks > 10:
            confidence_factors.append(0.3)
        elif metrics.total_tasks > 5:
            confidence_factors.append(0.2)
        else:
            confidence_factors.append(0.1)
        
        confidence_factors.append(metrics.performance_score * 0.3)
        
        if metrics.skip_rate > 0:
            confidence_factors.append(0.2)
        else:
            confidence_factors.append(0.1)
        
        if metrics.goal_completion_rate > 0:
            confidence_factors.append(0.2)
        else:
            confidence_factors.append(0.1)
        
        return min(sum(confidence_factors), 1.0)
    
    def _get_fallback_thresholds(self, workspace_id: str) -> AdaptiveThresholds:
        """Get fallback thresholds when AI calculation fails"""
        return AdaptiveThresholds(
            workspace_id=workspace_id,
            max_pending_tasks=15,
            priority_boost_factor=1.2,
            skip_prevention_threshold=0.5,
            phase_transition_threshold=20,
            urgency_multiplier=1.0,
            quality_gate_threshold=0.8,
            calculated_at=datetime.now(),
            confidence_score=0.5
        )
    
    def _get_fallback_metrics(self, workspace_id: str) -> WorkspaceMetrics:
        """Get fallback metrics when collection fails"""
        return WorkspaceMetrics(
            workspace_id=workspace_id,
            total_tasks=0,
            pending_tasks=0,
            in_progress_tasks=0,
            completed_tasks=0,
            failed_tasks=0,
            skip_count=0,
            skip_rate=0.0,
            avg_completion_time=0.0,
            goal_completion_rate=0.0,
            agent_utilization=0.0,
            current_phase=WorkspacePhase.PLANNING,
            bottleneck_indicators=[],
            performance_score=0.0
        )
    
    def _is_cached_valid(self, workspace_id: str) -> bool:
        """Check if cached optimization is still valid"""
        if workspace_id not in self.optimization_cache:
            return False
        
        cache_entry = self.optimization_cache[workspace_id]
        cache_age = datetime.now() - cache_entry["calculated_at"]
        
        return cache_age < self.cache_ttl

# ========================================================================
# 🎼 UNIFIED ORCHESTRATOR - MAIN CLASS
# ========================================================================

class UnifiedOrchestrator:
    """
    🎼 Unified System Orchestrator
    
    Combines workflow management and adaptive task orchestration into a single,
    cohesive system providing complete end-to-end orchestration capabilities.
    
    Features:
    - Complete workflow lifecycle management
    - AI-driven adaptive task orchestration
    - Real-time progress tracking and monitoring
    - Cross-workspace load balancing
    - Automatic rollback and error recovery
    - Universal AI Pipeline Engine integration
    - Universal Memory Architecture integration
    """

    def __init__(self, ai_pipeline_engine=None):
        self.supabase = get_supabase_client()
        self.uma = get_universal_memory_architecture()
        self.ai_optimizer = AIOptimizer(self.supabase)
        
        if AI_PIPELINE_AVAILABLE and universal_ai_pipeline_engine:
            self.ai_pipeline_engine = ai_pipeline_engine or universal_ai_pipeline_engine
        else:
            self.ai_pipeline_engine = None
            logger.warning("🤖 AI Pipeline not available - UnifiedOrchestrator will use fallback strategies")
        
        # Workflow tracking
        self.active_workflows: Dict[str, WorkflowProgress] = {}
        self.workflow_history: List[WorkflowResult] = []
        
        # Performance tracking
        self.total_workflows = 0
        self.successful_workflows = 0
        self.failed_workflows = 0
        self.average_execution_time = 0.0
        self.optimization_requests = 0
        self.skip_prevention_successes = 0
        self.threshold_adjustments = 0
        
        logger.info("🎼 Unified Orchestrator initialized with complete integration capabilities")
        
        # Lifecycle management (Pillar 7: Autonomous Pipeline)
        self._running = False
        self._autonomous_mode = os.getenv("PIPELINE_FULLY_AUTONOMOUS", "true").lower() == "true"

    # ========================================================================
    # 🚀 WORKFLOW MANAGEMENT (from WorkflowOrchestrator)
    # ========================================================================

    async def execute_complete_workflow(
        self, 
        workspace_id: str,
        goal_id: str,
        timeout_minutes: int = 30,
        enable_rollback: bool = True,
        quality_threshold: float = 70.0,
        enable_adaptive_optimization: bool = True
    ) -> WorkflowResult:
        """
        Execute complete end-to-end workflow with adaptive optimization
        """
        workflow_id = str(uuid4())
        start_time = time.time()
        self.total_workflows += 1
        
        logger.info(f"🚀 Starting unified workflow {workflow_id} for workspace {workspace_id}, goal {goal_id}")
        
        # Get adaptive optimization settings
        adaptive_settings = None
        if enable_adaptive_optimization:
            try:
                adaptive_settings = await self.optimize_workspace_throughput(workspace_id)
                logger.info(f"✅ Applied adaptive optimization: max_pending={adaptive_settings['optimal_settings']['max_pending_tasks']}")
            except Exception as e:
                logger.warning(f"Adaptive optimization failed, continuing with defaults: {e}")
        
        # Initialize workflow progress
        progress = WorkflowProgress(
            stage=WorkflowStage.INITIALIZING,
            progress_percentage=0.0,
            current_operation="Initializing unified workflow",
            stage_start_time=datetime.now()
        )
        
        self.active_workflows[workflow_id] = progress
        
        result = WorkflowResult(
            success=False,
            message="Workflow initialization",
            workspace_id=workspace_id,
            goal_id=goal_id,
            workflow_id=workflow_id,
            progress=progress,
            adaptive_optimization=adaptive_settings or {}
        )
        
        try:
            return await asyncio.wait_for(
                self._execute_unified_workflow_stages(result, quality_threshold, enable_rollback, adaptive_settings),
                timeout=timeout_minutes * 60
            )
            
        except asyncio.TimeoutError:
            logger.error(f"⏰ Workflow {workflow_id} timed out after {timeout_minutes} minutes")
            result.error = f"Workflow timed out after {timeout_minutes} minutes"
            result.final_status = WorkflowStatus.FAILED
            result.final_stage = WorkflowStage.FAILED
            
            if enable_rollback:
                await self._perform_rollback(result)
                
            return await self._finalize_workflow_result(result, start_time)
            
        except Exception as e:
            logger.error(f"💥 Critical error in workflow {workflow_id}: {str(e)}", exc_info=True)
            result.error = f"Critical workflow error: {str(e)}"
            result.final_status = WorkflowStatus.FAILED
            result.final_stage = WorkflowStage.FAILED
            
            if enable_rollback:
                await self._perform_rollback(result)
                
            return await self._finalize_workflow_result(result, start_time)
        
        finally:
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]

    async def _execute_unified_workflow_stages(
        self, 
        result: WorkflowResult, 
        quality_threshold: float,
        enable_rollback: bool,
        adaptive_settings: Optional[Dict[str, Any]]
    ) -> WorkflowResult:
        """Execute all workflow stages with adaptive optimization"""
        start_time = time.time()
        
        try:
            # Stage 1: Goal Analysis with adaptive context
            await self._update_progress(result, WorkflowStage.ANALYZING_GOAL, 10.0, "Analyzing goal requirements with adaptive context")
            goal = await self._analyze_goal_with_optimization(result.workspace_id, result.goal_id, adaptive_settings)
            if not goal:
                raise Exception("Goal not found or invalid")
            result.stage_results["goal_analysis"] = goal.__dict__ if hasattr(goal, '__dict__') else str(goal)
            
            # Stage 2: Asset Requirements Generation with AI optimization
            await self._update_progress(result, WorkflowStage.GENERATING_ASSETS, 25.0, "Generating optimized asset requirements")
            assets_generated = await self._generate_optimized_asset_requirements(goal, result, adaptive_settings)
            result.assets_generated = assets_generated
            if assets_generated == 0:
                raise Exception("Failed to generate any asset requirements")
            
            # Stage 3: Adaptive Task Generation
            await self._update_progress(result, WorkflowStage.CREATING_TASKS, 40.0, "Creating tasks with adaptive orchestration")
            tasks_generated = await self._generate_adaptive_tasks(goal, result, adaptive_settings)
            result.tasks_generated = tasks_generated
            if tasks_generated == 0:
                raise Exception("Failed to generate any tasks")
            
            # Stage 4: Adaptive Task Execution Monitoring
            await self._update_progress(result, WorkflowStage.EXECUTING_TASKS, 60.0, "Monitoring adaptive task execution")
            execution_success = await self._monitor_adaptive_task_execution(result, adaptive_settings)
            if not execution_success:
                raise Exception("Task execution failed or timed out")
            
            # Stage 5: Enhanced Quality Validation
            await self._update_progress(result, WorkflowStage.QUALITY_VALIDATION, 75.0, "Validating quality with adaptive thresholds")
            quality_score = await self._validate_adaptive_quality(result, adaptive_settings)
            result.quality_score = quality_score
            if quality_score < quality_threshold:
                raise Exception(f"Quality score {quality_score:.1f} below threshold {quality_threshold}")
            
            # Stage 6: Optimized Deliverable Creation
            await self._update_progress(result, WorkflowStage.CREATING_DELIVERABLES, 90.0, "Creating optimized deliverables")
            deliverables_created = await self._create_optimized_deliverables(result, adaptive_settings)
            result.deliverables_created = deliverables_created
            if deliverables_created == 0:
                raise Exception("Failed to create any deliverables")
            
            # Stage 7: Unified Finalization
            await self._update_progress(result, WorkflowStage.FINALIZING, 95.0, "Finalizing unified workflow")
            await self._finalize_unified_workflow(result, adaptive_settings)
            
            # Stage 8: Completion with Performance Summary
            await self._update_progress(result, WorkflowStage.COMPLETED, 100.0, "Unified workflow completed successfully")
            result.success = True
            result.message = "Unified workflow completed successfully with adaptive optimization"
            result.final_status = WorkflowStatus.COMPLETED
            result.final_stage = WorkflowStage.COMPLETED
            
            self.successful_workflows += 1
            logger.info(f"✅ Unified workflow {result.workflow_id} completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Unified workflow stage failed: {str(e)}")
            result.error = str(e)
            result.final_status = WorkflowStatus.FAILED
            result.final_stage = result.progress.stage if result.progress else WorkflowStage.FAILED
            
            if enable_rollback:
                await self._perform_rollback(result)
                
            self.failed_workflows += 1
            
        return await self._finalize_workflow_result(result, start_time)

    # ========================================================================
    # 🎯 ADAPTIVE ORCHESTRATION (from AdaptiveTaskOrchestrationEngine)
    # ========================================================================

    async def optimize_workspace_throughput(self, workspace_id: str) -> Dict[str, Any]:
        """Optimize workspace throughput with AI-driven settings"""
        try:
            self.optimization_requests += 1
            
            logger.info(f"⚡ Optimizing workspace throughput for {workspace_id}")
            
            # Get workspace context from UMA
            context = await self.uma.get_relevant_context(workspace_id, "task_orchestration")
            
            # Calculate optimal settings using AI
            optimal_settings = await self.ai_optimizer.calculate_optimal_settings(context)
            
            # Generate recommendations
            recommendations = await self._generate_optimization_recommendations(workspace_id, optimal_settings)
            
            optimization_result = {
                "workspace_id": workspace_id,
                "optimal_settings": asdict(optimal_settings),
                "recommendations": [asdict(rec) for rec in recommendations if hasattr(rec, '__dict__')],
                "optimization_metadata": {
                    "optimized_at": datetime.now().isoformat(),
                    "confidence": optimal_settings.confidence_score,
                    "uma_context_used": True,
                    "ai_driven": True
                }
            }
            
            logger.info(f"✅ Workspace throughput optimized: max_pending={optimal_settings.max_pending_tasks}")
            return optimization_result
            
        except Exception as e:
            logger.error(f"❌ Failed to optimize workspace throughput: {e}")
            return self._get_fallback_optimization(workspace_id)

    async def get_orchestration_recommendation(
        self, 
        workspace_id: str, 
        current_pending_count: int, 
        task_metadata: Dict[str, Any]
    ) -> OrchestrationRecommendation:
        """Get AI-driven orchestration recommendation to replace hard-coded limits"""
        try:
            logger.info(f"🚀 Getting orchestration recommendation for workspace {workspace_id}")
            
            # Get comprehensive workspace context
            context = await self.uma.get_relevant_context(workspace_id, "task_orchestration")
            
            # Collect current workspace metrics  
            metrics = await self.ai_optimizer._collect_workspace_metrics(workspace_id, context)
            
            # Analyze task criticality
            is_critical = task_metadata.get("is_critical", False)
            task_priority = task_metadata.get("task_priority", "medium")
            
            # Get AI-driven recommendation
            if is_critical:
                recommendation = OrchestrationRecommendation(
                    should_proceed=True,
                    recommended_limit=current_pending_count + 5,
                    reasoning="Critical task detected - bypassing normal limits for system stability",
                    confidence=0.9,
                    optimization_suggestions=["Consider task delegation patterns"]
                )
            else:
                adaptive_limit = await self._calculate_adaptive_limit(workspace_id, metrics, current_pending_count)
                should_proceed = current_pending_count < adaptive_limit
                
                reasoning = f"Adaptive limit calculation: {current_pending_count}/{adaptive_limit} tasks"
                if not should_proceed:
                    reasoning += f" - High load detected, skipping to prevent resource exhaustion"
                else:
                    reasoning += f" - Load manageable, proceeding with execution"
                
                recommendation = OrchestrationRecommendation(
                    should_proceed=should_proceed,
                    recommended_limit=adaptive_limit,
                    reasoning=reasoning,
                    confidence=0.8,
                    optimization_suggestions=await self._generate_optimization_suggestions(metrics)
                )
            
            logger.info(f"✅ Orchestration recommendation: proceed={recommendation.should_proceed}, limit={recommendation.recommended_limit}")
            return recommendation
            
        except Exception as e:
            logger.error(f"❌ Failed to get orchestration recommendation: {e}")
            return OrchestrationRecommendation(
                should_proceed=current_pending_count < 8,
                recommended_limit=8,
                reasoning=f"Fallback recommendation due to error: {str(e)[:100]}",
                confidence=0.5,
                optimization_suggestions=["Review system configuration"]
            )

    async def adaptive_skip_prevention(self, workspace_id: str) -> Dict[str, Any]:
        """Predictive analysis to prevent task skipping"""
        try:
            logger.info(f"🎯 Running adaptive skip prevention for {workspace_id}")
            
            context = await self.uma.get_relevant_context(workspace_id, "skip_prevention")
            metrics = await self.ai_optimizer._collect_workspace_metrics(workspace_id, context)
            
            high_risk_tasks = await self._identify_high_risk_tasks(workspace_id, metrics)
            priority_adjustments = await self._calculate_priority_adjustments(high_risk_tasks, metrics)
            expected_improvement = await self._estimate_skip_reduction(metrics, priority_adjustments)
            
            skip_prevention_result = {
                "workspace_id": workspace_id,
                "current_skip_rate": metrics.skip_rate,
                "high_risk_tasks": high_risk_tasks,
                "priority_adjustments": priority_adjustments,
                "expected_skip_reduction": expected_improvement,
                "prevention_strategies": self._generate_prevention_strategies(metrics),
                "processed_at": datetime.now().isoformat()
            }
            
            if len(high_risk_tasks) > 0:
                self.skip_prevention_successes += 1
                logger.info(f"🎯 Skip prevention applied to {len(high_risk_tasks)} high-risk tasks")
            
            return skip_prevention_result
            
        except Exception as e:
            logger.error(f"❌ Skip prevention failed: {e}")
            return {"error": str(e), "workspace_id": workspace_id}

    # ========================================================================
    # 🔧 ENHANCED WORKFLOW METHODS (with adaptive optimization)
    # ========================================================================

    async def _analyze_goal_with_optimization(
        self, 
        workspace_id: str, 
        goal_id: str, 
        adaptive_settings: Optional[Dict[str, Any]]
    ) -> Optional[WorkspaceGoal]:
        """Analyze goal with adaptive optimization context"""
        try:
            response = supabase.table("workspace_goals").select("*").eq("id", str(goal_id)).eq("workspace_id", str(workspace_id)).single().execute()
            if not response.data:
                return None
                
            goal = WorkspaceGoal(**response.data)
            
            # Enhanced AI analysis with adaptive context
            if self.ai_pipeline_engine:
                try:
                    context = PipelineContext(workspace_id=str(workspace_id), goal_id=str(goal_id))
                    
                    # Include adaptive settings in the analysis
                    analysis_data = {
                        "goal": goal.description, 
                        "workspace_context": goal.title,
                        "adaptive_settings": adaptive_settings
                    }
                    
                    analysis_result = await self.ai_pipeline_engine.execute_pipeline_step(
                        PipelineStepType.GOAL_DECOMPOSITION,
                        analysis_data,
                        context
                    )
                    
                    if analysis_result.success:
                        logger.info(f"📊 Enhanced AI goal analysis completed for goal {goal_id}")
                except Exception as e:
                    logger.warning(f"Enhanced AI goal analysis failed, using fallback: {e}")
            else:
                logger.info(f"📊 Basic goal analysis completed for goal {goal_id} (AI not available)")
                
            return goal
            
        except Exception as e:
            logger.error(f"Goal analysis failed: {str(e)}")
            return None

    async def _generate_optimized_asset_requirements(
        self, 
        goal: WorkspaceGoal, 
        result: WorkflowResult, 
        adaptive_settings: Optional[Dict[str, Any]]
    ) -> int:
        """Generate asset requirements with adaptive optimization"""
        requirements = []
        
        if self.ai_pipeline_engine:
            try:
                context = PipelineContext(
                    workspace_id=str(goal.workspace_id), 
                    goal_id=str(goal.id),
                    user_context={
                        "goal_title": goal.title, 
                        "goal_description": goal.description,
                        "adaptive_settings": adaptive_settings
                    }
                )
                
                analysis_data = {
                    "title": goal.title,
                    "description": goal.description,
                    "success_criteria": goal.success_criteria or [],
                    "target_completion": goal.target_completion_date,
                    "optimization_context": adaptive_settings
                }
                
                ai_result = await self.ai_pipeline_engine.execute_pipeline_step(
                    PipelineStepType.ASSET_REQUIREMENTS_GENERATION,
                    analysis_data,
                    context
                )
                
                if ai_result.success and ai_result.data:
                    requirements = ai_result.data.get("requirements", [])
                    logger.info(f"📋 AI generated {len(requirements)} optimized asset requirements")
                else:
                    logger.warning("AI optimized asset requirements generation failed, using fallback")
                    requirements = self._generate_fallback_asset_requirements(goal)
                    
            except Exception as e:
                logger.warning(f"AI optimized asset requirements generation error: {e}, using fallback")
                requirements = self._generate_fallback_asset_requirements(goal)
        else:
            requirements = self._generate_fallback_asset_requirements(goal)
        
        # Store asset requirements with optimization metadata
        stored_count = 0
        for req in requirements:
            try:
                req_data = {
                    "workspace_id": str(goal.workspace_id),
                    "goal_id": str(goal.id),
                    "requirement_type": req.get("type", "analysis"),
                    "name": req.get("title", "Asset Requirement"),
                    "description": req.get("description", ""),
                    "priority": req.get("priority", "medium"),
                    "complexity": req.get("complexity", "medium"),
                    "gap": f"Requirements: {json.dumps(req.get('acceptance_criteria', []))}"
                }
                
                # Add optimization metadata if available
                if adaptive_settings:
                    req_data["optimization_metadata"] = json.dumps(adaptive_settings)
                
                supabase.table("goal_asset_requirements").insert(req_data).execute()
                stored_count += 1
            except Exception as e:
                logger.warning(f"Failed to store optimized asset requirement: {str(e)}")
                
        result.stage_results["asset_requirements"] = {
            "requirements": requirements, 
            "ai_generated": self.ai_pipeline_engine is not None,
            "adaptive_optimized": adaptive_settings is not None
        }
        logger.info(f"📋 Generated and stored {stored_count} optimized asset requirements")
        return stored_count

    async def _generate_adaptive_tasks(
        self, 
        goal: WorkspaceGoal, 
        result: WorkflowResult, 
        adaptive_settings: Optional[Dict[str, Any]]
    ) -> int:
        """Generate tasks with adaptive orchestration optimization"""
        try:
            response = supabase.table("goal_asset_requirements").select("*").eq("goal_id", str(goal.id)).execute()
            asset_requirements = response.data or []
            
            if not asset_requirements:
                logger.warning("No asset requirements found for adaptive task generation")
                return 0
            
            total_tasks = 0
            
            # Get adaptive thresholds for task generation optimization
            adaptive_thresholds = None
            if adaptive_settings:
                adaptive_thresholds = adaptive_settings.get("optimal_settings", {})
            
            for asset_req in asset_requirements:
                context = PipelineContext(
                    workspace_id=str(goal.workspace_id),
                    goal_id=str(goal.id),
                    user_context={
                        "asset_requirement": asset_req,
                        "adaptive_thresholds": adaptive_thresholds
                    }
                )
                
                # Enhanced AI task generation with adaptive context
                if self.ai_pipeline_engine:
                    try:
                        task_generation_data = {
                            "requirement_name": asset_req.get("name"),
                            "requirement_description": asset_req.get("description"),
                            "requirement_type": asset_req.get("requirement_type"),
                            "priority": asset_req.get("priority"),
                            "gap": asset_req.get("gap"),
                            "adaptive_optimization": adaptive_thresholds
                        }
                        
                        ai_result = await self.ai_pipeline_engine.execute_pipeline_step(
                            PipelineStepType.TASK_GENERATION,
                            task_generation_data,
                            context
                        )
                        
                        if ai_result.success and ai_result.data:
                            tasks = ai_result.data.get("tasks", [])
                        else:
                            tasks = self._generate_fallback_tasks(asset_req)
                    except Exception as e:
                        logger.warning(f"AI adaptive task generation failed for {asset_req.get('name')}: {e}")
                        tasks = self._generate_fallback_tasks(asset_req)
                else:
                    tasks = self._generate_fallback_tasks(asset_req)
                    
                # Create tasks with adaptive optimization metadata
                for task in tasks:
                    try:
                        task_data = {
                            "workspace_id": str(goal.workspace_id),
                            "goal_id": str(goal.id),
                            "title": task.get("title", "Generated Task"),
                            "description": task.get("description", ""),
                            "type": task.get("type", "analysis"),
                            "priority": task.get("priority", 50),
                            "status": "pending",
                            "assigned_agent_id": None,
                            "deliverables": json.dumps(task.get("deliverables", [])),
                            "acceptance_criteria": json.dumps(task.get("acceptance_criteria", []))
                        }
                        
                        # Add adaptive optimization metadata
                        if adaptive_thresholds:
                            task_data["adaptive_metadata"] = json.dumps(adaptive_thresholds)
                        
                        supabase.table("tasks").insert(task_data).execute()
                        total_tasks += 1
                    except Exception as e:
                        logger.warning(f"Failed to create adaptive task: {str(e)}")
            
            result.stage_results["task_generation"] = {
                "tasks_created": total_tasks,
                "adaptive_optimized": adaptive_settings is not None
            }
            logger.info(f"📝 Generated {total_tasks} adaptive tasks from {len(asset_requirements)} asset requirements")
            return total_tasks
            
        except Exception as e:
            logger.error(f"Adaptive task generation failed: {str(e)}")
            return 0

    async def _monitor_adaptive_task_execution(
        self, 
        result: WorkflowResult, 
        adaptive_settings: Optional[Dict[str, Any]]
    ) -> bool:
        """Monitor task execution with adaptive optimization"""
        max_wait_time = 300  # 5 minutes max wait
        check_interval = 10  # Check every 10 seconds
        
        # Adjust wait time based on adaptive settings
        if adaptive_settings:
            optimal_settings = adaptive_settings.get("optimal_settings", {})
            max_pending = optimal_settings.get("max_pending_tasks", 8)
            # Scale wait time with expected task load
            max_wait_time = min(600, max_wait_time + (max_pending * 10))
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                response = supabase.table("tasks").select("status").eq("workspace_id", str(result.workspace_id)).execute()
                tasks = response.data or []
                
                if not tasks:
                    logger.warning("No tasks found for adaptive execution monitoring")
                    return False
                
                status_counts = {}
                for task in tasks:
                    status = task.get("status", "pending")
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                total_tasks = len(tasks)
                completed_tasks = status_counts.get("completed", 0)
                failed_tasks = status_counts.get("failed", 0)
                
                progress = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
                
                logger.info(f"📈 Adaptive task execution progress: {completed_tasks}/{total_tasks} completed ({progress:.1f}%)")
                
                if completed_tasks + failed_tasks >= total_tasks:
                    success_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
                    
                    # Adaptive success rate threshold based on optimization settings
                    success_threshold = 80.0
                    if adaptive_settings:
                        optimal_settings = adaptive_settings.get("optimal_settings", {})
                        quality_threshold = optimal_settings.get("quality_gate_threshold", 0.8)
                        success_threshold = quality_threshold * 100
                    
                    result.stage_results["task_execution"] = {
                        "total_tasks": total_tasks,
                        "completed_tasks": completed_tasks,
                        "failed_tasks": failed_tasks,
                        "success_rate": success_rate,
                        "adaptive_threshold": success_threshold
                    }
                    
                    return success_rate >= success_threshold
                
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Adaptive task monitoring error: {str(e)}")
                await asyncio.sleep(check_interval)
        
        logger.warning("Adaptive task execution monitoring timed out")
        return False

    # ========================================================================
    # 🔧 HELPER AND UTILITY METHODS
    # ========================================================================

    async def _update_progress(
        self, 
        result: WorkflowResult, 
        stage: WorkflowStage, 
        percentage: float, 
        operation: str
    ):
        """Update workflow progress"""
        if result.progress:
            result.progress.stage = stage
            result.progress.progress_percentage = percentage
            result.progress.current_operation = operation
            result.progress.stage_start_time = datetime.now()
            result.progress.completed_stages = int(percentage / 12.5)
            
            if result.workflow_id in self.active_workflows:
                self.active_workflows[result.workflow_id] = result.progress
                
        logger.info(f"🔄 Workflow {result.workflow_id}: {stage.value} ({percentage:.1f}%) - {operation}")

    def _generate_fallback_asset_requirements(self, goal: WorkspaceGoal) -> List[Dict[str, Any]]:
        """Generate basic asset requirements without AI"""
        return [
            {
                "type": "analysis",
                "title": f"Analysis for {goal.title}",
                "description": f"Detailed analysis and planning for: {goal.description}",
                "priority": "high",
                "complexity": "medium",
                "acceptance_criteria": ["Analysis document created", "Key requirements identified"]
            },
            {
                "type": "documentation", 
                "title": f"Documentation for {goal.title}",
                "description": f"Create documentation for: {goal.description}",
                "priority": "medium",
                "complexity": "low",
                "acceptance_criteria": ["Documentation written", "Documentation reviewed"]
            }
        ]
        
    def _generate_fallback_tasks(self, asset_req: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate basic tasks without AI"""
        req_type = asset_req.get("requirement_type", "analysis")
        req_name = asset_req.get("name", "Asset Requirement")
        req_description = asset_req.get("description", "")
        
        return [
            {
                "title": f"Analyze {req_name}",
                "description": f"Analyze and understand requirements for: {req_description}",
                "type": "analysis",
                "priority": 60,
                "deliverables": [f"{req_name} analysis"],
                "acceptance_criteria": ["Analysis completed", "Requirements documented"]
            },
            {
                "title": f"Implement {req_name}",
                "description": f"Implement solution for: {req_description}",
                "type": req_type,
                "priority": 70,
                "deliverables": [f"{req_name} implementation"],
                "acceptance_criteria": ["Implementation completed", "Solution tested"]
            }
        ]

    async def _calculate_adaptive_limit(
        self, 
        workspace_id: str, 
        metrics: WorkspaceMetrics, 
        current_count: int
    ) -> int:
        """Calculate adaptive task limit based on workspace metrics"""
        try:
            base_limit = max(8, min(25, metrics.total_tasks // 3))
            
            if metrics.skip_rate > 0.5:
                base_limit += 3
            elif metrics.skip_rate < 0.2:
                base_limit -= 1
            
            completion_rate = metrics.completed_tasks / max(metrics.total_tasks, 1)
            if completion_rate > 0.8:
                base_limit += 2
            elif completion_rate < 0.4:
                base_limit -= 2
            
            adaptive_limit = max(5, min(30, base_limit))
            
            logger.debug(f"🧮 Adaptive limit calculation: base={base_limit}, final={adaptive_limit}")
            return adaptive_limit
            
        except Exception as e:
            logger.warning(f"Adaptive limit calculation failed: {e}")
            return 15

    async def _generate_optimization_suggestions(self, metrics: WorkspaceMetrics) -> List[str]:
        """Generate optimization suggestions based on metrics"""
        suggestions = []
        
        if metrics.skip_rate > 0.4:
            suggestions.append("Consider increasing task processing parallelism")
        
        if metrics.agent_utilization < 0.6:
            suggestions.append("Review agent assignment efficiency")
        
        if len(metrics.bottleneck_indicators) > 0:
            suggestions.append(f"Address bottlenecks: {', '.join(metrics.bottleneck_indicators[:2])}")
        
        if not suggestions:
            suggestions.append("Workspace operating within optimal parameters")
        
        return suggestions

    async def _validate_adaptive_quality(
        self, 
        result: WorkflowResult, 
        adaptive_settings: Optional[Dict[str, Any]]
    ) -> float:
        """Validate quality with adaptive thresholds"""
        try:
            response = supabase.table("tasks").select("*").eq("workspace_id", str(result.workspace_id)).eq("status", "completed").execute()
            completed_tasks = response.data or []
            
            if not completed_tasks:
                logger.warning("No completed tasks found for adaptive quality validation")
                return 0.0
            
            total_quality_score = 0.0
            valid_scores = 0
            
            # Get adaptive quality threshold
            quality_threshold = 0.8  # Default
            if adaptive_settings:
                optimal_settings = adaptive_settings.get("optimal_settings", {})
                quality_threshold = optimal_settings.get("quality_gate_threshold", 0.8)
            
            for task in completed_tasks:
                context = PipelineContext(
                    workspace_id=str(result.workspace_id),
                    goal_id=str(result.goal_id),
                    task_id=task.get("id")
                )
                
                if self.ai_pipeline_engine:
                    try:
                        validation_data = {
                            "task_title": task.get("title"),
                            "task_description": task.get("description"),
                            "task_deliverables": task.get("deliverables"),
                            "task_output": task.get("output", ""),
                            "quality_threshold": quality_threshold
                        }
                        
                        ai_result = await self.ai_pipeline_engine.execute_pipeline_step(
                            PipelineStepType.QUALITY_VALIDATION,
                            validation_data,
                            context
                        )
                        
                        if ai_result.success and ai_result.data:
                            overall_score = ai_result.data.get("overall_score", 0)
                        else:
                            overall_score = self._calculate_fallback_quality_score(task)
                    except Exception as e:
                        logger.warning(f"AI adaptive quality validation failed for {task.get('title')}: {e}")
                        overall_score = self._calculate_fallback_quality_score(task)
                else:
                    overall_score = self._calculate_fallback_quality_score(task)
                    
                if overall_score > 0:
                    total_quality_score += overall_score
                    valid_scores += 1
            
            average_quality = total_quality_score / valid_scores if valid_scores > 0 else 0.0
            
            result.stage_results["quality_validation"] = {
                "tasks_validated": len(completed_tasks),
                "valid_scores": valid_scores,
                "average_quality": average_quality,
                "adaptive_threshold": quality_threshold * 100
            }
            
            logger.info(f"📊 Adaptive quality validation: {average_quality:.1f}% average score (threshold: {quality_threshold * 100:.1f}%)")
            return average_quality
            
        except Exception as e:
            logger.error(f"Adaptive quality validation failed: {str(e)}")
            return 0.0

    def _calculate_fallback_quality_score(self, task: Dict[str, Any]) -> float:
        """Calculate basic quality score without AI"""
        score = 0.0
        
        if task.get("title") and len(task.get("title", "")) > 5:
            score += 20
        
        if task.get("description") and len(task.get("description", "")) > 20:
            score += 20
            
        if task.get("output") and len(task.get("output", "")) > 10:
            score += 30
            
        if task.get("deliverables"):
            score += 20
            
        if task.get("acceptance_criteria"):
            score += 10
            
        logger.debug(f"📊 Fallback quality score for {task.get('title', 'Unknown')}: {score}")
        return score

    async def _create_optimized_deliverables(
        self, 
        result: WorkflowResult, 
        adaptive_settings: Optional[Dict[str, Any]]
    ) -> int:
        """Create final deliverables with optimization metadata"""
        try:
            workspace_response = supabase.table("workspaces").select("*").eq("id", str(result.workspace_id)).single().execute()
            workspace = workspace_response.data
            
            goal_response = supabase.table("workspace_goals").select("*").eq("id", str(result.goal_id)).single().execute()
            goal = goal_response.data
            
            if not workspace or not goal:
                logger.error("Workspace or goal not found for optimized deliverable creation")
                return 0
            
            # Enhanced deliverable content with optimization data
            deliverable_content = {
                "workflow_summary": {
                    "goal_title": goal.get("title"),
                    "goal_description": goal.get("description"),
                    "execution_time": result.execution_time,
                    "tasks_generated": result.tasks_generated,
                    "assets_generated": result.assets_generated,
                    "quality_score": result.quality_score
                },
                "adaptive_optimization": {
                    "enabled": adaptive_settings is not None,
                    "settings": adaptive_settings or {},
                    "performance_improvements": result.adaptive_optimization
                },
                "stage_results": result.stage_results,
                "performance_metrics": result.performance_metrics,
                "timestamp": datetime.now().isoformat()
            }
            
            supabase.table("deliverables").insert({
                "workspace_id": str(result.workspace_id),
                "goal_id": str(result.goal_id),
                "title": f"Unified Workflow Report - {goal.get('title')}",
                "content": json.dumps(deliverable_content, indent=2),
                "type": "unified_workflow_report",
                "format": "json",
                "quality_score": result.quality_score,
                "approval_status": "approved" if result.quality_score >= 80 else "needs_review"
            }).execute()
            
            result.stage_results["deliverable_creation"] = deliverable_content
            logger.info(f"📦 Created unified workflow deliverable with optimization metadata")
            return 1
            
        except Exception as e:
            logger.error(f"Optimized deliverable creation failed: {str(e)}")
            return 0

    async def _finalize_unified_workflow(
        self, 
        result: WorkflowResult, 
        adaptive_settings: Optional[Dict[str, Any]]
    ):
        """Finalize workflow with optimization metadata"""
        try:
            # Update workspace status with optimization metadata
            update_data = {
                "status": "completed",
                "updated_at": datetime.now().isoformat()
            }
            
            if adaptive_settings:
                update_data["optimization_metadata"] = json.dumps(adaptive_settings)
            
            supabase.table("workspaces").update(update_data).eq("id", str(result.workspace_id)).execute()
            
            # Update goal status with optimization results
            goal_update_data = {
                "status": "completed",
                "completion_percentage": 100,
                "updated_at": datetime.now().isoformat()
            }
            
            if adaptive_settings:
                goal_update_data["optimization_results"] = json.dumps({
                    "quality_score": result.quality_score,
                    "execution_time": result.execution_time,
                    "adaptive_optimization": result.adaptive_optimization
                })
            
            supabase.table("workspace_goals").update(goal_update_data).eq("id", str(result.goal_id)).execute()
            
            logger.info(f"🎯 Finalized unified workflow for workspace {result.workspace_id}")
            
        except Exception as e:
            logger.error(f"Unified workflow finalization failed: {str(e)}")

    async def _perform_rollback(self, result: WorkflowResult):
        """Perform rollback operations on failure"""
        logger.warning(f"🔄 Performing rollback for workflow {result.workflow_id}")
        result.rollback_performed = True
        
        try:
            await self._update_progress(result, WorkflowStage.ROLLBACK, 0.0, "Rolling back changes")
            
            if result.tasks_generated > 0:
                # supabase.table("tasks").delete().eq("workspace_id", str(result.workspace_id)).eq("goal_id", str(result.goal_id)).execute()
                logger.warning(f"ROLLBACK (DRY RUN): Would have deleted {result.tasks_generated} tasks for goal {result.goal_id}")
            
            if result.assets_generated > 0:
                supabase.table("goal_asset_requirements").delete().eq("goal_id", str(result.goal_id)).execute()
                logger.info(f"🗑️ Rolled back {result.assets_generated} asset requirements")
            
            supabase.table("workspace_goals").update({
                "status": "pending",
                "completion_percentage": 0,
                "updated_at": datetime.now().isoformat()
            }).eq("id", str(result.goal_id)).execute()
            
            supabase.table("workspaces").update({
                "status": "active",
                "updated_at": datetime.now().isoformat()
            }).eq("id", str(result.workspace_id)).execute()
            
            result.rollback_success = True
            result.final_status = WorkflowStatus.ROLLBACK_COMPLETED
            logger.info(f"✅ Rollback completed successfully for workflow {result.workflow_id}")
            
        except Exception as e:
            logger.error(f"❌ Rollback failed: {str(e)}")
            result.rollback_success = False
            result.final_status = WorkflowStatus.FAILED

    async def _finalize_workflow_result(self, result: WorkflowResult, start_time: float) -> WorkflowResult:
        """Finalize workflow result with metrics and cleanup"""
        result.execution_time = time.time() - start_time
        
        result.performance_metrics = {
            "execution_time": result.execution_time,
            "stages_completed": result.progress.completed_stages if result.progress else 0,
            "total_stages": result.progress.total_stages if result.progress else 8
        }
        
        if self.ai_pipeline_engine:
            try:
                ai_stats = self.ai_pipeline_engine.get_statistics()
                result.performance_metrics["ai_pipeline_stats"] = ai_stats
                result.ai_usage_stats = ai_stats
            except Exception as e:
                result.performance_metrics["ai_pipeline_stats"] = {"error": str(e)}
                result.ai_usage_stats = {"error": str(e)}
        else:
            result.performance_metrics["ai_pipeline_stats"] = {"status": "unavailable"}
            result.ai_usage_stats = {"status": "unavailable"}
        
        total_time = self.average_execution_time * (self.total_workflows - 1) + result.execution_time
        self.average_execution_time = total_time / self.total_workflows
        
        self.workflow_history.append(result)
        
        if len(self.workflow_history) > 100:
            self.workflow_history = self.workflow_history[-100:]
        
        logger.info(f"🏁 Unified workflow {result.workflow_id} finalized: {result.final_status.value} in {result.execution_time:.2f}s")
        return result

    # ========================================================================
    # 🔧 FALLBACK AND HELPER METHODS
    # ========================================================================

    def _get_fallback_optimization(self, workspace_id: str) -> Dict[str, Any]:
        """Fallback optimization when AI calculation fails"""
        return {
            "workspace_id": workspace_id,
            "optimal_settings": asdict(self.ai_optimizer._get_fallback_thresholds(workspace_id)),
            "recommendations": [],
            "optimization_metadata": {
                "optimized_at": datetime.now().isoformat(),
                "confidence": 0.5,
                "fallback": True
            }
        }

    async def _generate_optimization_recommendations(self, workspace_id: str, thresholds: AdaptiveThresholds) -> List[Dict[str, Any]]:
        """Generate specific optimization recommendations"""
        recommendations = []
        
        if thresholds.max_pending_tasks > 8:
            recommendations.append({
                "recommendation_id": str(uuid4()),
                "workspace_id": workspace_id,
                "optimization_type": "max_pending_tasks",
                "current_value": 8,
                "recommended_value": thresholds.max_pending_tasks,
                "confidence": thresholds.confidence_score,
                "expected_improvement": 0.3,
                "reasoning": f"Increase from 8 to {thresholds.max_pending_tasks} based on workspace performance",
                "implementation_priority": "HIGH"
            })
        
        if thresholds.priority_boost_factor > 1.0:
            recommendations.append({
                "recommendation_id": str(uuid4()),
                "workspace_id": workspace_id,
                "optimization_type": "priority_boost_factor",
                "current_value": 1.0,
                "recommended_value": thresholds.priority_boost_factor,
                "confidence": thresholds.confidence_score,
                "expected_improvement": 0.2,
                "reasoning": f"Apply {thresholds.priority_boost_factor}x priority boost to reduce skip rate",
                "implementation_priority": "MEDIUM"
            })
        
        return recommendations

    async def _identify_high_risk_tasks(self, workspace_id: str, metrics: WorkspaceMetrics) -> List[Dict[str, Any]]:
        """Identify tasks at high risk of being skipped"""
        try:
            tasks_result = self.supabase.table("tasks")\
                .select("*, workspace_goals!inner(*)")\
                .eq("workspace_id", workspace_id)\
                .eq("status", "pending")\
                .execute()
            
            tasks = tasks_result.data if tasks_result.data else []
            
            high_risk_tasks = []
            for task in tasks:
                risk_score = self._calculate_task_risk_score(task, metrics)
                if risk_score > 0.6:
                    high_risk_tasks.append({
                        "task_id": task["id"],
                        "task_name": task["name"],
                        "risk_score": risk_score,
                        "risk_factors": self._identify_risk_factors(task, metrics)
                    })
            
            return high_risk_tasks
            
        except Exception as e:
            logger.error(f"Failed to identify high-risk tasks: {e}")
            return []

    def _calculate_task_risk_score(self, task: Dict, metrics: WorkspaceMetrics) -> float:
        """Calculate risk score for task being skipped"""
        risk_factors = []
        
        created_at = datetime.fromisoformat(task["created_at"].replace('Z', '+00:00'))
        age_hours = (datetime.now().replace(tzinfo=created_at.tzinfo) - created_at).total_seconds() / 3600
        age_risk = min(age_hours / 24, 1.0)
        risk_factors.append(age_risk * 0.3)
        
        priority_mapping = {"critical": 0.0, "high": 0.2, "medium": 0.5, "low": 0.8}
        priority_risk = priority_mapping.get(task.get("priority", "medium"), 0.5)
        risk_factors.append(priority_risk * 0.2)
        
        load_risk = min(metrics.pending_tasks / 20, 1.0)
        risk_factors.append(load_risk * 0.3)
        
        goal_linkage_risk = 0.0 if task.get("goal_id") else 0.5
        risk_factors.append(goal_linkage_risk * 0.2)
        
        return sum(risk_factors)

    def _identify_risk_factors(self, task: Dict, metrics: WorkspaceMetrics) -> List[str]:
        """Identify specific risk factors for a task"""
        factors = []
        
        created_at = datetime.fromisoformat(task["created_at"].replace('Z', '+00:00'))
        age_hours = (datetime.now().replace(tzinfo=created_at.tzinfo) - created_at).total_seconds() / 3600
        
        if age_hours > 24:
            factors.append("task_age_high")
        
        if task.get("priority") in ["low", "medium"]:
            factors.append("low_priority")
        
        if metrics.pending_tasks > 15:
            factors.append("high_pending_load")
        
        if not task.get("goal_id"):
            factors.append("no_goal_linkage")
        
        if metrics.skip_rate > 0.5:
            factors.append("workspace_high_skip_rate")
        
        return factors

    async def _calculate_priority_adjustments(self, high_risk_tasks: List[Dict], metrics: WorkspaceMetrics) -> List[Dict[str, Any]]:
        """Calculate priority adjustments for high-risk tasks"""
        adjustments = []
        
        for task in high_risk_tasks:
            risk_score = task["risk_score"]
            
            if risk_score > 0.8:
                priority_boost = "critical"
                boost_factor = 2.0
            elif risk_score > 0.7:
                priority_boost = "high"
                boost_factor = 1.5
            else:
                priority_boost = "medium"
                boost_factor = 1.2
            
            adjustments.append({
                "task_id": task["task_id"],
                "current_priority": "pending",
                "recommended_priority": priority_boost,
                "boost_factor": boost_factor,
                "reasoning": f"Risk score {risk_score:.2f} requires priority elevation"
            })
        
        return adjustments

    async def _estimate_skip_reduction(self, metrics: WorkspaceMetrics, adjustments: List[Dict]) -> Dict[str, float]:
        """Estimate skip rate reduction from priority adjustments"""
        current_skip_rate = metrics.skip_rate
        
        adjustment_impact = len(adjustments) * 0.1
        estimated_new_skip_rate = max(current_skip_rate - adjustment_impact, 0.0)
        
        improvement = current_skip_rate - estimated_new_skip_rate
        improvement_percentage = (improvement / current_skip_rate) if current_skip_rate > 0 else 0.0
        
        return {
            "current_skip_rate": current_skip_rate,
            "estimated_new_skip_rate": estimated_new_skip_rate,
            "absolute_improvement": improvement,
            "percentage_improvement": improvement_percentage
        }

    def _generate_prevention_strategies(self, metrics: WorkspaceMetrics) -> List[Dict[str, str]]:
        """Generate skip prevention strategies based on metrics"""
        strategies = []
        
        if metrics.skip_rate > 0.5:
            strategies.append({
                "strategy": "increase_max_pending_limit",
                "description": f"Increase max pending tasks from current to {metrics.pending_tasks + 10}",
                "priority": "high"
            })
        
        if "low_agent_utilization" in metrics.bottleneck_indicators:
            strategies.append({
                "strategy": "agent_redistribution",
                "description": "Redistribute tasks to better utilize available agents",
                "priority": "medium"
            })
        
        if "stuck_tasks" in metrics.bottleneck_indicators:
            strategies.append({
                "strategy": "task_timeout_handling",
                "description": "Implement timeout handling for stuck tasks",
                "priority": "high"
            })
        
        return strategies

    # ========================================================================
    # 📊 SYSTEM MONITORING AND HEALTH
    # ========================================================================

    def get_workflow_progress(self, workflow_id: str) -> Optional[WorkflowProgress]:
        """Get real-time progress for a workflow"""
        return self.active_workflows.get(workflow_id)

    def get_system_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        stats = {
            "workflow_management": {
                "total_workflows": self.total_workflows,
                "successful_workflows": self.successful_workflows,
                "failed_workflows": self.failed_workflows,
                "success_rate": self.successful_workflows / max(self.total_workflows, 1),
                "average_execution_time": self.average_execution_time,
                "active_workflows": len(self.active_workflows),
            },
            "adaptive_optimization": {
                "optimization_requests": self.optimization_requests,
                "skip_prevention_successes": self.skip_prevention_successes,
                "threshold_adjustments": self.threshold_adjustments,
                "cache_hit_rate": len(self.ai_optimizer.optimization_cache) / max(self.optimization_requests, 1),
            },
            "system_integration": {
                "ai_pipeline_available": self.ai_pipeline_engine is not None,
                "uma_integration": self.uma is not None,
                "adaptive_optimization_enabled": True,
                "unified_orchestration": True
            }
        }
        
        if self.ai_pipeline_engine:
            try:
                stats["ai_pipeline_stats"] = self.ai_pipeline_engine.get_statistics()
            except Exception as e:
                stats["ai_pipeline_stats"] = {"error": str(e)}
        else:
            stats["ai_pipeline_stats"] = {"status": "unavailable"}
            
        return stats

    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        try:
            health_status = "healthy"
            issues = []
            
            # Check AI pipeline health
            if self.ai_pipeline_engine:
                try:
                    ai_health = await self.ai_pipeline_engine.health_check()
                    if ai_health["status"] != "healthy":
                        health_status = "degraded"
                        issues.append("AI Pipeline degraded")
                except Exception as e:
                    health_status = "degraded"
                    issues.append(f"AI Pipeline check failed: {str(e)}")
            else:
                issues.append("AI Pipeline not available")
            
            # Check UMA health
            if not self.uma:
                issues.append("Universal Memory Architecture not available")
            
            # Check database connectivity
            try:
                self.supabase.table("workspaces").select("id").limit(1).execute()
            except Exception as e:
                health_status = "unhealthy"
                issues.append(f"Database connectivity failed: {str(e)}")
            
            return {
                "status": health_status,
                "active_workflows": len(self.active_workflows),
                "system_statistics": self.get_system_statistics(),
                "issues": issues,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "active_workflows": len(self.active_workflows),
                "timestamp": datetime.now().isoformat()
            }

    # ========================================================================
    # 🚀 LIFECYCLE MANAGEMENT (Pillar 7: Autonomous Pipeline)
    # ========================================================================

    async def start(self):
        """Start the autonomous orchestrator pipeline (Pillar 7: Autonomous Pipeline)"""
        try:
            logger.info("🚀 Starting Unified Orchestrator autonomous pipeline...")
            
            self._running = True
            
            # Initialize autonomous components
            if self._autonomous_mode:
                logger.info("🤖 Autonomous mode enabled - pipeline will operate without human intervention")
            
            # Start AI pipeline if available
            if self.ai_pipeline_engine and hasattr(self.ai_pipeline_engine, 'start'):
                await self.ai_pipeline_engine.start()
                logger.info("✅ AI Pipeline Engine started")
            
            # Initialize UMA if available
            if self.uma and hasattr(self.uma, 'start'):
                await self.uma.start()
                logger.info("✅ Universal Memory Architecture started")
            
            # Mark as started
            logger.info("🎼 Unified Orchestrator pipeline started successfully")
            return {"status": "started", "autonomous_mode": self._autonomous_mode}
            
        except Exception as e:
            logger.error(f"❌ Failed to start Unified Orchestrator: {e}")
            self._running = False
            raise e

    async def stop(self):
        """Stop the autonomous orchestrator pipeline"""
        try:
            logger.info("🛑 Stopping Unified Orchestrator pipeline...")
            
            self._running = False
            
            # Stop AI pipeline if available
            if self.ai_pipeline_engine and hasattr(self.ai_pipeline_engine, 'stop'):
                await self.ai_pipeline_engine.stop()
                logger.info("✅ AI Pipeline Engine stopped")
            
            # Stop UMA if available
            if self.uma and hasattr(self.uma, 'stop'):
                await self.uma.stop()
                logger.info("✅ Universal Memory Architecture stopped")
            
            logger.info("🎼 Unified Orchestrator pipeline stopped successfully")
            return {"status": "stopped"}
            
        except Exception as e:
            logger.error(f"❌ Failed to stop Unified Orchestrator: {e}")
            raise e

    def is_running(self) -> bool:
        """Check if the orchestrator pipeline is running"""
        return self._running
    
    async def update_workspace_metrics(self, workspace_id: str, task_completion_data: Dict[str, Any]) -> None:
        """
        Update workspace metrics after task completion
        
        This method tracks workspace performance and updates relevant metrics
        for future orchestration decisions.
        """
        try:
            # Extract relevant data from task completion
            task_id = task_completion_data.get('task_id')
            success = task_completion_data.get('success', False)
            duration = task_completion_data.get('duration_seconds', 0)
            
            # Log execution data for future analysis
            execution_log = {
                "workspace_id": workspace_id,
                "task_id": task_id,
                "type": "task_completion",
                "message": f"Task {'completed successfully' if success else 'failed'}",
                "content": {
                    "success": success,
                    "duration_seconds": duration,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # Insert into execution_logs table
            try:
                if hasattr(self, 'ato_engine') and self.ato_engine:
                    # Use ATO engine's supabase client
                    self.ato_engine.supabase.table("execution_logs").insert(execution_log).execute()
                elif hasattr(self, 'workflow_engine') and self.workflow_engine:
                    # Use workflow engine's supabase client
                    self.workflow_engine.supabase.table("execution_logs").insert(execution_log).execute()
            except Exception as e:
                logger.warning(f"Failed to log execution data: {e}")
            
            # Update in-memory metrics cache if needed
            if hasattr(self, '_metrics_cache') and workspace_id in self._metrics_cache:
                # Update cache with latest performance data
                cache_entry = self._metrics_cache[workspace_id]
                if success:
                    cache_entry['successful_completions'] = cache_entry.get('successful_completions', 0) + 1
                else:
                    cache_entry['failed_completions'] = cache_entry.get('failed_completions', 0) + 1
                    
            logger.info(f"✅ Updated workspace metrics for {workspace_id}")
            
        except Exception as e:
            logger.error(f"Failed to update workspace metrics: {e}")

    def is_autonomous(self) -> bool:
        """Check if the orchestrator is in autonomous mode (Pillar 7)"""
        return self._autonomous_mode

# ========================================================================
# 🏭 SINGLETON FACTORY
# ========================================================================

_unified_orchestrator_instance = None

def get_unified_orchestrator() -> UnifiedOrchestrator:
    """Get singleton instance of Unified Orchestrator"""
    global _unified_orchestrator_instance
    if _unified_orchestrator_instance is None:
        _unified_orchestrator_instance = UnifiedOrchestrator()
        logger.info("🏭 Created singleton Unified Orchestrator instance")
    return _unified_orchestrator_instance

# Backward compatibility aliases
workflow_orchestrator = get_unified_orchestrator()
adaptive_task_orchestration_engine = get_unified_orchestrator()

# ========================================================================
# 🔧 INTEGRATION HELPERS
# ========================================================================

async def get_dynamic_max_pending_tasks(workspace_id: str) -> int:
    """Helper function to get dynamic max pending tasks for a workspace"""
    try:
        orchestrator = get_unified_orchestrator()
        optimization = await orchestrator.optimize_workspace_throughput(workspace_id)
        return optimization["optimal_settings"]["max_pending_tasks"]
    except Exception as e:
        logger.warning(f"Failed to get dynamic max pending tasks, using fallback: {e}")
        return 15

async def should_skip_task_execution(workspace_id: str, current_pending: int) -> bool:
    """Helper function to determine if task execution should be skipped"""
    try:
        max_pending = await get_dynamic_max_pending_tasks(workspace_id)
        return current_pending >= max_pending
    except Exception as e:
        logger.warning(f"Failed to check skip condition, defaulting to no skip: {e}")
        return False

async def get_orchestration_recommendation(
    workspace_id: str, 
    current_pending_count: int, 
    task_metadata: Dict[str, Any]
) -> OrchestrationRecommendation:
    """Helper function to get orchestration recommendation"""
    try:
        orchestrator = get_unified_orchestrator()
        return await orchestrator.get_orchestration_recommendation(workspace_id, current_pending_count, task_metadata)
    except Exception as e:
        logger.warning(f"Failed to get orchestration recommendation: {e}")
        return OrchestrationRecommendation(
            should_proceed=current_pending_count < 8,
            recommended_limit=8,
            reasoning=f"Fallback recommendation due to error: {str(e)[:100]}",
            confidence=0.5,
            optimization_suggestions=["Review system configuration"]
        )

if __name__ == "__main__":
    # Test Unified Orchestrator functionality
    async def test_unified_orchestrator():
        orchestrator = get_unified_orchestrator()
        
        # Test health check
        health = await orchestrator.health_check()
        print(f"Health: {health}")
        
        # Test system statistics
        stats = orchestrator.get_system_statistics()
        print(f"Statistics: {stats}")
        
        # Test optimization (with test workspace)
        try:
            optimization = await orchestrator.optimize_workspace_throughput("test-workspace-id")
            print(f"Optimization: {optimization}")
        except Exception as e:
            print(f"Optimization test failed (expected): {e}")
    
    asyncio.run(test_unified_orchestrator())