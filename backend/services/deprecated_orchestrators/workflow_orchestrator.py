"""
Workflow Orchestrator - Sistema di Orchestrazione Integrata

🎯 INTEGRATION: Sistema come 'collante' - Workflow Orchestrator per unificare componenti

Il "collante" mancante che unisce tutti i componenti in un flusso end-to-end coerente:
- Goal → Task Generation → Execution → Quality Gates → Progress → Deliverables
- Orchestrazione intelligente con logica di business integrata
- Gestione completa del ciclo di vita da goal a deliverable concreto
- Auto-recovery e adaptive workflow management

Responsabilità:
1. Monitorare Goals attivi e gestire il loro ciclo di vita completo
2. Invocare Goal-Driven Task Planner per generare task asset-focused
3. Coordinare Task Executor con quality gates integrati
4. Gestire Asset First Deliverable System per output concreti
5. Implementare feedback loops e auto-recovery mechanisms
6. Fornire visibilità completa dello stato del workflow
"""

import asyncio
import logging
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from uuid import uuid4, UUID

from database import (
    supabase, get_supabase_service_client,
    list_tasks, get_workspace, get_active_workspaces,
    update_task_status, create_task
)
from models import TaskStatus, WorkspaceStatus, GoalStatus, WorkspaceGoal

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

class WorkflowOrchestrator:
    """
    Production-Ready Workflow Orchestrator
    
    Features:
    - End-to-end workflow management: Goal → Assets → Tasks → Execution → Quality → Deliverables
    - Automatic rollback on failure with transaction-like guarantees
    - Real-time progress tracking and monitoring
    - Integration with Universal AI Pipeline Engine
    - Comprehensive error handling and recovery
    - Performance monitoring and optimization
    """

    def __init__(self, ai_pipeline_engine = None):
        if AI_PIPELINE_AVAILABLE and universal_ai_pipeline_engine:
            self.ai_pipeline_engine = ai_pipeline_engine or universal_ai_pipeline_engine
        else:
            self.ai_pipeline_engine = None
            logger.warning("🤖 AI Pipeline not available - WorkflowOrchestrator will use fallback strategies")
        self.active_workflows: Dict[str, WorkflowProgress] = {}
        self.workflow_history: List[WorkflowResult] = []
        
        # Performance tracking
        self.total_workflows = 0
        self.successful_workflows = 0
        self.failed_workflows = 0
        self.average_execution_time = 0.0
        
        logger.info("🔧 Advanced WorkflowOrchestrator initialized with production features")

    async def execute_complete_workflow(
        self, 
        workspace_id: str,
        goal_id: str,
        timeout_minutes: int = 30,
        enable_rollback: bool = True,
        quality_threshold: float = 70.0
    ) -> WorkflowResult:
        """
        Execute complete end-to-end workflow with production guarantees
        
        Args:
            workspace_id: Target workspace
            goal_id: Goal to process
            timeout_minutes: Maximum execution time
            enable_rollback: Whether to rollback on failure
            quality_threshold: Minimum quality score required
            
        Returns:
            WorkflowResult with comprehensive execution details
        """
        workflow_id = str(uuid4())
        start_time = time.time()
        self.total_workflows += 1
        
        logger.info(f"🚀 Starting workflow {workflow_id} for workspace {workspace_id}, goal {goal_id}")
        
        # Initialize workflow progress
        progress = WorkflowProgress(
            stage=WorkflowStage.INITIALIZING,
            progress_percentage=0.0,
            current_operation="Initializing workflow",
            stage_start_time=datetime.now()
        )
        
        self.active_workflows[workflow_id] = progress
        
        result = WorkflowResult(
            success=False,
            message="Workflow initialization",
            workspace_id=workspace_id,
            goal_id=goal_id,
            workflow_id=workflow_id,
            progress=progress
        )
        
        try:
            # Set timeout
            return await asyncio.wait_for(
                self._execute_workflow_stages(result, quality_threshold, enable_rollback),
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
            # Cleanup active workflow tracking
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]

    async def _execute_workflow_stages(
        self, 
        result: WorkflowResult, 
        quality_threshold: float,
        enable_rollback: bool
    ) -> WorkflowResult:
        """Execute all workflow stages sequentially"""
        start_time = time.time()
        
        try:
            # Stage 1: Goal Analysis
            await self._update_progress(result, WorkflowStage.ANALYZING_GOAL, 10.0, "Analyzing goal requirements")
            goal = await self._analyze_goal(result.workspace_id, result.goal_id)
            if not goal:
                raise Exception("Goal not found or invalid")
            result.stage_results["goal_analysis"] = goal.__dict__ if hasattr(goal, '__dict__') else str(goal)
            
            # Stage 2: Asset Requirements Generation
            await self._update_progress(result, WorkflowStage.GENERATING_ASSETS, 25.0, "Generating asset requirements")
            assets_generated = await self._generate_asset_requirements(goal, result)
            result.assets_generated = assets_generated
            if assets_generated == 0:
                raise Exception("Failed to generate any asset requirements")
            
            # Stage 3: Task Generation
            await self._update_progress(result, WorkflowStage.CREATING_TASKS, 40.0, "Creating tasks from assets")
            tasks_generated = await self._generate_tasks_from_assets(goal, result)
            result.tasks_generated = tasks_generated
            if tasks_generated == 0:
                raise Exception("Failed to generate any tasks")
            
            # Stage 4: Task Execution Monitoring
            await self._update_progress(result, WorkflowStage.EXECUTING_TASKS, 60.0, "Monitoring task execution")
            execution_success = await self._monitor_task_execution(result)
            if not execution_success:
                raise Exception("Task execution failed or timed out")
            
            # Stage 5: Quality Validation
            await self._update_progress(result, WorkflowStage.QUALITY_VALIDATION, 75.0, "Validating quality")
            quality_score = await self._validate_quality(result)
            result.quality_score = quality_score
            if quality_score < quality_threshold:
                raise Exception(f"Quality score {quality_score:.1f} below threshold {quality_threshold}")
            
            # Stage 6: Deliverable Creation
            await self._update_progress(result, WorkflowStage.CREATING_DELIVERABLES, 90.0, "Creating deliverables")
            deliverables_created = await self._create_deliverables(result)
            result.deliverables_created = deliverables_created
            if deliverables_created == 0:
                raise Exception("Failed to create any deliverables")
            
            # Stage 7: Finalization
            await self._update_progress(result, WorkflowStage.FINALIZING, 95.0, "Finalizing workflow")
            await self._finalize_workflow(result)
            
            # Stage 8: Completion
            await self._update_progress(result, WorkflowStage.COMPLETED, 100.0, "Workflow completed successfully")
            result.success = True
            result.message = "Workflow completed successfully"
            result.final_status = WorkflowStatus.COMPLETED
            result.final_stage = WorkflowStage.COMPLETED
            
            self.successful_workflows += 1
            logger.info(f"✅ Workflow {result.workflow_id} completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Workflow stage failed: {str(e)}")
            result.error = str(e)
            result.final_status = WorkflowStatus.FAILED
            result.final_stage = result.progress.stage if result.progress else WorkflowStage.FAILED
            
            if enable_rollback:
                await self._perform_rollback(result)
                
            self.failed_workflows += 1
            
        return await self._finalize_workflow_result(result, start_time)

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
            result.progress.completed_stages = int(percentage / 12.5)  # 8 stages total
            
            # Update active workflow tracking
            if result.workflow_id in self.active_workflows:
                self.active_workflows[result.workflow_id] = result.progress
                
        logger.info(f"🔄 Workflow {result.workflow_id}: {stage.value} ({percentage:.1f}%) - {operation}")

    async def _analyze_goal(self, workspace_id: str, goal_id: str) -> Optional[WorkspaceGoal]:
        """Analyze and validate goal"""
        try:
            # Get goal from database
            response = supabase.table("workspace_goals").select("*").eq("id", str(goal_id)).eq("workspace_id", str(workspace_id)).single().execute()
            if not response.data:
                return None
                
            goal = WorkspaceGoal(**response.data)
            
            # Use AI to analyze goal feasibility and requirements if available
            if self.ai_pipeline_engine:
                try:
                    context = PipelineContext(workspace_id=str(workspace_id), goal_id=str(goal_id))
                    analysis_result = await self.ai_pipeline_engine.execute_pipeline_step(
                        PipelineStepType.GOAL_DECOMPOSITION,
                        {"goal": goal.description, "workspace_context": goal.title},
                        context
                    )
                    
                    if analysis_result.success:
                        logger.info(f"📊 AI goal analysis completed for goal {goal_id}")
                except Exception as e:
                    logger.warning(f"AI goal analysis failed, using fallback: {e}")
            else:
                logger.info(f"📊 Basic goal analysis completed for goal {goal_id} (AI not available)")
                
            return goal
            
        except Exception as e:
            logger.error(f"Goal analysis failed: {str(e)}")
            return None

    async def _generate_asset_requirements(self, goal: WorkspaceGoal, result: WorkflowResult) -> int:
        """Generate asset requirements using AI pipeline or fallback"""
        requirements = []
        
        # Try AI pipeline first
        if self.ai_pipeline_engine:
            try:
                context = PipelineContext(
                    workspace_id=str(goal.workspace_id), 
                    goal_id=str(goal.id),
                    user_context={"goal_title": goal.title, "goal_description": goal.description}
                )
                
                ai_result = await self.ai_pipeline_engine.execute_pipeline_step(
                    PipelineStepType.ASSET_REQUIREMENTS_GENERATION,
                    {
                        "title": goal.title,
                        "description": goal.description,
                        "success_criteria": goal.success_criteria or [],
                        "target_completion": goal.target_completion_date
                    },
                    context
                )
                
                if ai_result.success and ai_result.data:
                    requirements = ai_result.data.get("requirements", [])
                    logger.info(f"📋 AI generated {len(requirements)} asset requirements")
                else:
                    logger.warning("AI asset requirements generation failed, using fallback")
                    requirements = self._generate_fallback_asset_requirements(goal)
                    
            except Exception as e:
                logger.warning(f"AI asset requirements generation error: {e}, using fallback")
                requirements = self._generate_fallback_asset_requirements(goal)
        else:
            # Use fallback strategy
            requirements = self._generate_fallback_asset_requirements(goal)
        
        # Store asset requirements in database
        stored_count = 0
        for req in requirements:
            try:
                supabase.table("goal_asset_requirements").insert({
                    "workspace_id": str(goal.workspace_id),
                    "goal_id": str(goal.id),
                    "requirement_type": req.get("type", "analysis"),
                    "name": req.get("title", "Asset Requirement"),
                    "description": req.get("description", ""),
                    "priority": req.get("priority", "medium"),
                    "complexity": req.get("complexity", "medium"),
                    "gap": f"Requirements: {json.dumps(req.get('acceptance_criteria', []))}"
                }).execute()
                stored_count += 1
            except Exception as e:
                logger.warning(f"Failed to store asset requirement: {str(e)}")
                
        result.stage_results["asset_requirements"] = {"requirements": requirements, "ai_generated": self.ai_pipeline_engine is not None}
        logger.info(f"📋 Generated and stored {stored_count} asset requirements")
        return stored_count
        
    def _generate_fallback_asset_requirements(self, goal: WorkspaceGoal) -> List[Dict[str, Any]]:
        """Generate basic asset requirements without AI"""
        fallback_requirements = [
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
        logger.info(f"📋 Generated {len(fallback_requirements)} fallback asset requirements")
        return fallback_requirements
        
    def _generate_fallback_tasks(self, asset_req: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate basic tasks without AI"""
        req_type = asset_req.get("requirement_type", "analysis")
        req_name = asset_req.get("name", "Asset Requirement")
        req_description = asset_req.get("description", "")
        
        fallback_tasks = [
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
        logger.info(f"📝 Generated {len(fallback_tasks)} fallback tasks for {req_name}")
        return fallback_tasks
        
    def _calculate_fallback_quality_score(self, task: Dict[str, Any]) -> float:
        """Calculate basic quality score without AI"""
        score = 0.0
        
        # Basic quality indicators
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

    async def _generate_tasks_from_assets(self, goal: WorkspaceGoal, result: WorkflowResult) -> int:
        """Generate tasks from asset requirements"""
        # Get asset requirements from database
        try:
            response = supabase.table("goal_asset_requirements").select("*").eq("goal_id", str(goal.id)).execute()
            asset_requirements = response.data or []
            
            if not asset_requirements:
                logger.warning("No asset requirements found for task generation")
                return 0
            
            total_tasks = 0
            
            for asset_req in asset_requirements:
                context = PipelineContext(
                    workspace_id=str(goal.workspace_id),
                    goal_id=str(goal.id),
                    user_context={"asset_requirement": asset_req}
                )
                
                # Try AI task generation
                if self.ai_pipeline_engine:
                    try:
                        ai_result = await self.ai_pipeline_engine.execute_pipeline_step(
                            PipelineStepType.TASK_GENERATION,
                            {
                                "requirement_name": asset_req.get("name"),
                                "requirement_description": asset_req.get("description"),
                                "requirement_type": asset_req.get("requirement_type"),
                                "priority": asset_req.get("priority"),
                                "gap": asset_req.get("gap")
                            },
                            context
                        )
                        
                        if ai_result.success and ai_result.data:
                            tasks = ai_result.data.get("tasks", [])
                        else:
                            tasks = self._generate_fallback_tasks(asset_req)
                    except Exception as e:
                        logger.warning(f"AI task generation failed for {asset_req.get('name')}: {e}")
                        tasks = self._generate_fallback_tasks(asset_req)
                else:
                    tasks = self._generate_fallback_tasks(asset_req)
                    
                    # Create tasks in database
                    for task in tasks:
                        try:
                            supabase.table("tasks").insert({
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
                            }).execute()
                            total_tasks += 1
                        except Exception as e:
                            logger.warning(f"Failed to create task: {str(e)}")
            
            result.stage_results["task_generation"] = {"tasks_created": total_tasks}
            logger.info(f"📝 Generated {total_tasks} tasks from {len(asset_requirements)} asset requirements")
            return total_tasks
            
        except Exception as e:
            logger.error(f"Task generation failed: {str(e)}")
            return 0

    async def _monitor_task_execution(self, result: WorkflowResult) -> bool:
        """Monitor task execution with timeout"""
        max_wait_time = 300  # 5 minutes max wait
        check_interval = 10  # Check every 10 seconds
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                # Check task status in database
                response = supabase.table("tasks").select("status").eq("workspace_id", str(result.workspace_id)).execute()
                tasks = response.data or []
                
                if not tasks:
                    logger.warning("No tasks found for execution monitoring")
                    return False
                
                # Count task statuses
                status_counts = {}
                for task in tasks:
                    status = task.get("status", "pending")
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                total_tasks = len(tasks)
                completed_tasks = status_counts.get("completed", 0)
                failed_tasks = status_counts.get("failed", 0)
                
                # Calculate progress
                progress = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
                
                logger.info(f"📈 Task execution progress: {completed_tasks}/{total_tasks} completed ({progress:.1f}%)")
                
                # Check if all tasks are done (completed or failed)
                if completed_tasks + failed_tasks >= total_tasks:
                    success_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
                    
                    result.stage_results["task_execution"] = {
                        "total_tasks": total_tasks,
                        "completed_tasks": completed_tasks,
                        "failed_tasks": failed_tasks,
                        "success_rate": success_rate
                    }
                    
                    # Consider successful if > 80% of tasks completed
                    return success_rate >= 80.0
                
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Task monitoring error: {str(e)}")
                await asyncio.sleep(check_interval)
        
        logger.warning("Task execution monitoring timed out")
        return False

    async def _validate_quality(self, result: WorkflowResult) -> float:
        """Validate overall workflow quality"""
        try:
            # Get completed tasks and their outputs
            response = supabase.table("tasks").select("*").eq("workspace_id", str(result.workspace_id)).eq("status", "completed").execute()
            completed_tasks = response.data or []
            
            if not completed_tasks:
                logger.warning("No completed tasks found for quality validation")
                return 0.0
            
            total_quality_score = 0.0
            valid_scores = 0
            
            for task in completed_tasks:
                context = PipelineContext(
                    workspace_id=str(result.workspace_id),
                    goal_id=str(result.goal_id),
                    task_id=task.get("id")
                )
                
                # Try AI quality validation
                if self.ai_pipeline_engine:
                    try:
                        ai_result = await self.ai_pipeline_engine.execute_pipeline_step(
                            PipelineStepType.QUALITY_VALIDATION,
                            {
                                "task_title": task.get("title"),
                                "task_description": task.get("description"),
                                "task_deliverables": task.get("deliverables"),
                                "task_output": task.get("output", "")
                            },
                            context
                        )
                        
                        if ai_result.success and ai_result.data:
                            quality_metrics = ai_result.data.get("quality_metrics", {})
                            overall_score = ai_result.data.get("overall_score", 0)
                        else:
                            overall_score = self._calculate_fallback_quality_score(task)
                    except Exception as e:
                        logger.warning(f"AI quality validation failed for {task.get('title')}: {e}")
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
                "average_quality": average_quality
            }
            
            logger.info(f"📊 Quality validation: {average_quality:.1f}% average score")
            return average_quality
            
        except Exception as e:
            logger.error(f"Quality validation failed: {str(e)}")
            return 0.0

    async def _create_deliverables(self, result: WorkflowResult) -> int:
        """Create final deliverables"""
        try:
            # Get workspace and goal information
            workspace_response = supabase.table("workspaces").select("*").eq("id", str(result.workspace_id)).single().execute()
            workspace = workspace_response.data
            
            goal_response = supabase.table("workspace_goals").select("*").eq("id", str(result.goal_id)).single().execute()
            goal = goal_response.data
            
            if not workspace or not goal:
                logger.error("Workspace or goal not found for deliverable creation")
                return 0
            
            # Create comprehensive deliverable
            deliverable_content = {
                "workflow_summary": {
                    "goal_title": goal.get("title"),
                    "goal_description": goal.get("description"),
                    "execution_time": result.execution_time,
                    "tasks_generated": result.tasks_generated,
                    "assets_generated": result.assets_generated,
                    "quality_score": result.quality_score
                },
                "stage_results": result.stage_results,
                "performance_metrics": result.performance_metrics,
                "timestamp": datetime.now().isoformat()
            }
            
            # Insert deliverable into database
            supabase.table("deliverables").insert({
                "workspace_id": str(result.workspace_id),
                "goal_id": str(result.goal_id),
                "title": f"Workflow Completion Report - {goal.get('title')}",
                "content": json.dumps(deliverable_content, indent=2),
                "type": "workflow_report",
                "format": "json",
                "quality_score": result.quality_score,
                "approval_status": "approved" if result.quality_score >= 80 else "needs_review"
            }).execute()
            
            result.stage_results["deliverable_creation"] = deliverable_content
            logger.info(f"📦 Created workflow completion deliverable")
            return 1
            
        except Exception as e:
            logger.error(f"Deliverable creation failed: {str(e)}")
            return 0

    async def _finalize_workflow(self, result: WorkflowResult):
        """Finalize workflow and update workspace status"""
        try:
            # Update workspace status to completed
            supabase.table("workspaces").update({
                "status": "completed",
                "updated_at": datetime.now().isoformat()
            }).eq("id", str(result.workspace_id)).execute()
            
            # Update goal status
            supabase.table("workspace_goals").update({
                "status": "completed",
                "completion_percentage": 100,
                "updated_at": datetime.now().isoformat()
            }).eq("id", str(result.goal_id)).execute()
            
            logger.info(f"🎯 Finalized workflow for workspace {result.workspace_id}")
            
        except Exception as e:
            logger.error(f"Workflow finalization failed: {str(e)}")

    async def _perform_rollback(self, result: WorkflowResult):
        """Perform rollback operations on failure"""
        logger.warning(f"🔄 Performing rollback for workflow {result.workflow_id}")
        result.rollback_performed = True
        
        try:
            await self._update_progress(result, WorkflowStage.ROLLBACK, 0.0, "Rolling back changes")
            
            # Rollback tasks
            if result.tasks_generated > 0:
                supabase.table("tasks").delete().eq("workspace_id", str(result.workspace_id)).eq("goal_id", str(result.goal_id)).execute()
                logger.info(f"🗑️ Rolled back {result.tasks_generated} tasks")
            
            # Rollback asset requirements
            if result.assets_generated > 0:
                supabase.table("goal_asset_requirements").delete().eq("goal_id", str(result.goal_id)).execute()
                logger.info(f"🗑️ Rolled back {result.assets_generated} asset requirements")
            
            # Reset goal status
            supabase.table("workspace_goals").update({
                "status": "pending",
                "completion_percentage": 0,
                "updated_at": datetime.now().isoformat()
            }).eq("id", str(result.goal_id)).execute()
            
            # Reset workspace status
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
        
        # Update performance metrics
        result.performance_metrics = {
            "execution_time": result.execution_time,
            "stages_completed": result.progress.completed_stages if result.progress else 0,
            "total_stages": result.progress.total_stages if result.progress else 8
        }
        
        # Add AI pipeline stats if available
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
        
        # Update average execution time
        total_time = self.average_execution_time * (self.total_workflows - 1) + result.execution_time
        self.average_execution_time = total_time / self.total_workflows
        
        # Add to history
        self.workflow_history.append(result)
        
        # Keep only last 100 workflows in history
        if len(self.workflow_history) > 100:
            self.workflow_history = self.workflow_history[-100:]
        
        logger.info(f"🏁 Workflow {result.workflow_id} finalized: {result.final_status.value} in {result.execution_time:.2f}s")
        return result

    def get_workflow_progress(self, workflow_id: str) -> Optional[WorkflowProgress]:
        """Get real-time progress for a workflow"""
        return self.active_workflows.get(workflow_id)

    def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get orchestrator statistics"""
        stats = {
            "total_workflows": self.total_workflows,
            "successful_workflows": self.successful_workflows,
            "failed_workflows": self.failed_workflows,
            "success_rate": self.successful_workflows / max(self.total_workflows, 1),
            "average_execution_time": self.average_execution_time,
            "active_workflows": len(self.active_workflows),
        }
        
        # Add AI pipeline stats if available
        if self.ai_pipeline_engine:
            try:
                stats["ai_pipeline_stats"] = self.ai_pipeline_engine.get_statistics()
            except Exception as e:
                stats["ai_pipeline_stats"] = {"error": str(e)}
        else:
            stats["ai_pipeline_stats"] = {"status": "unavailable"}
            
        return stats

    def get_statistics(self) -> Dict[str, Any]:
        """Alias for get_workflow_statistics() for compatibility"""
        return self.get_workflow_statistics()

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            if self.ai_pipeline_engine:
                ai_health = await self.ai_pipeline_engine.health_check()
                return {
                    "status": "healthy" if ai_health["status"] == "healthy" else "degraded",
                    "ai_pipeline_status": ai_health["status"],
                    "active_workflows": len(self.active_workflows),
                    "statistics": self.get_workflow_statistics()
                }
            else:
                return {
                    "status": "degraded",
                    "ai_pipeline_status": "unavailable",
                    "active_workflows": len(self.active_workflows),
                    "statistics": self.get_workflow_statistics(),
                    "message": "AI Pipeline not available, using fallback strategies"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "active_workflows": len(self.active_workflows),
                "statistics": self.get_workflow_statistics()
            }

# Singleton instance for backward compatibility  
workflow_orchestrator = WorkflowOrchestrator()
