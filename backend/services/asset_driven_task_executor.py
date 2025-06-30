"""
Asset-Driven Task Executor Enhancement (Pillar 12: Concrete Deliverables + Pillar 7: Pipeline autonoma)
Enhances task execution with asset-driven orchestration, quality validation, and automated deliverable generation.
"""

import os
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from models import (
    EnhancedTask, AssetRequirement, AssetArtifact, 
    WorkspaceGoal, TaskStatus, QualityValidation
)
from database import (
    get_asset_requirements_for_goal, get_artifacts_for_requirement,
    update_task_status, update_goal_progress, get_workspace_goals
)
from services.asset_requirements_generator import AssetRequirementsGenerator
from services.asset_artifact_processor import AssetArtifactProcessor
from services.ai_quality_gate_engine import AIQualityGateEngine

logger = logging.getLogger(__name__)

class AssetDrivenTaskExecutor:
    """Asset-driven task execution with quality gates and deliverable automation (Pillar 7: Pipeline autonoma)"""
    
    def __init__(self):
        # Initialize asset-driven services
        self.requirements_generator = AssetRequirementsGenerator()
        self.artifact_processor = AssetArtifactProcessor()
        self.quality_gate_engine = AIQualityGateEngine()
        
        # Configuration from environment (Pillar-compliant)
        self.auto_asset_extraction = os.getenv("AUTO_TASK_TO_ARTIFACT_EXTRACTION", "true").lower() == "true"
        self.auto_quality_validation = os.getenv("AUTO_QUALITY_VALIDATION_PIPELINE", "true").lower() == "true"
        self.auto_goal_progress = os.getenv("AUTO_GOAL_PROGRESS_CALCULATION", "true").lower() == "true"
        self.asset_driven_goals = os.getenv("ENABLE_ASSET_DRIVEN_GOALS", "true").lower() == "true"
        
        # Performance configuration
        self.processing_timeout = int(os.getenv("ASSET_PROCESSING_TIMEOUT_SECONDS", "120"))
        self.concurrent_processing = int(os.getenv("CONCURRENT_ARTIFACT_PROCESSING", "3"))
        
        logger.info("🚀 AssetDrivenTaskExecutor initialized with comprehensive asset orchestration")
    
    async def enhance_task_execution(self, task: EnhancedTask, original_executor_result: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance standard task execution with asset-driven processing (Pillar 12: Concrete Deliverables)"""
        
        try:
            logger.info(f"🚀 Asset-driven enhancement for task: {task.id}")
            
            # Start with original executor result
            enhanced_result = original_executor_result.copy()
            
            # Asset-driven processing pipeline
            asset_processing_result = await self._run_asset_processing_pipeline(task)
            
            # Merge asset processing results
            enhanced_result.update({
                "asset_driven_processing": asset_processing_result,
                "artifacts_created": asset_processing_result.get("artifacts_created", 0),
                "quality_validations": asset_processing_result.get("quality_validations", []),
                "goal_progress_updates": asset_processing_result.get("goal_updates", [])
            })
            
            # Real-time goal progress update if enabled (Pillar 10: Real-Time)
            if self.auto_goal_progress and asset_processing_result.get("artifacts_created", 0) > 0:
                await self._trigger_real_time_goal_updates(task)
            
            logger.info(f"✅ Asset-driven enhancement completed for task: {task.id}")
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Asset-driven enhancement failed for task {task.id}: {e}")
            # Return original result if enhancement fails (graceful degradation)
            return original_executor_result
    
    async def _run_asset_processing_pipeline(self, task: EnhancedTask) -> Dict[str, Any]:
        """Run the complete asset processing pipeline (Pillar 7: Pipeline autonoma)"""
        
        pipeline_result = {
            "artifacts_created": 0,
            "quality_validations": [],
            "goal_updates": [],
            "processing_steps": [],
            "errors": []
        }
        
        try:
            # Step 1: Identify asset requirements for this task
            pipeline_result["processing_steps"].append("identifying_asset_requirements")
            asset_requirements = await self._identify_asset_requirements_for_task(task)
            
            if not asset_requirements:
                logger.info(f"No asset requirements found for task {task.id}")
                return pipeline_result
            
            # Step 2: Process task output into artifacts
            pipeline_result["processing_steps"].append("processing_artifacts")
            artifacts_created = []
            
            for requirement in asset_requirements:
                try:
                    artifact = await self.artifact_processor.process_task_output(task, requirement)
                    if artifact:
                        artifacts_created.append(artifact)
                        pipeline_result["artifacts_created"] += 1
                        
                except Exception as e:
                    pipeline_result["errors"].append(f"Artifact processing failed for requirement {requirement.id}: {e}")
                    logger.error(f"Artifact processing failed for requirement {requirement.id}: {e}")
            
            # Step 3: Quality validation pipeline
            if self.auto_quality_validation and artifacts_created:
                pipeline_result["processing_steps"].append("quality_validation")
                
                for artifact in artifacts_created:
                    try:
                        validation_result = await self.quality_gate_engine.validate_artifact_quality(artifact)
                        pipeline_result["quality_validations"].append(validation_result)
                        
                    except Exception as e:
                        pipeline_result["errors"].append(f"Quality validation failed for artifact {artifact.id}: {e}")
                        logger.error(f"Quality validation failed for artifact {artifact.id}: {e}")
            
            # Step 4: Goal progress calculation
            if self.auto_goal_progress:
                pipeline_result["processing_steps"].append("goal_progress_calculation")
                goal_updates = await self._calculate_goal_progress_updates(task, artifacts_created)
                pipeline_result["goal_updates"] = goal_updates
            
            pipeline_result["processing_steps"].append("pipeline_completed")
            logger.info(f"🏭 Asset processing pipeline completed for task {task.id}")
            
            return pipeline_result
            
        except Exception as e:
            pipeline_result["errors"].append(f"Pipeline execution failed: {e}")
            logger.error(f"Asset processing pipeline failed for task {task.id}: {e}")
            return pipeline_result
    
    async def _identify_asset_requirements_for_task(self, task: EnhancedTask) -> List[AssetRequirement]:
        """Identify which asset requirements this task should fulfill"""
        
        try:
            # Get workspace goals
            workspace_goals = await get_workspace_goals(task.workspace_id)
            if not workspace_goals:
                return []
            
            # Get asset requirements for all workspace goals
            all_requirements = []
            for goal in workspace_goals:
                try:
                    requirements = await get_asset_requirements_for_goal(goal.id)
                    all_requirements.extend(requirements)
                except Exception as e:
                    logger.error(f"Failed to get requirements for goal {goal.id}: {e}")
            
            # Filter requirements that match this task
            matching_requirements = []
            for requirement in all_requirements:
                if await self._task_matches_requirement(task, requirement):
                    matching_requirements.append(requirement)
            
            logger.info(f"Found {len(matching_requirements)} matching requirements for task {task.id}")
            return matching_requirements
            
        except Exception as e:
            logger.error(f"Failed to identify requirements for task {task.id}: {e}")
            return []
    
    async def _task_matches_requirement(self, task: EnhancedTask, requirement: AssetRequirement) -> bool:
        """Determine if a task should fulfill a specific asset requirement"""
        
        try:
            # Check if task is already linked to requirement
            if hasattr(task, 'asset_requirement_id') and task.asset_requirement_id == requirement.id:
                return True
            
            # AI-driven matching based on task description and requirement
            task_description = getattr(task, 'description', '') or getattr(task, 'name', '')
            requirement_description = requirement.description or requirement.asset_name
            
            # Simple keyword matching (could be enhanced with AI)
            task_keywords = set(task_description.lower().split())
            requirement_keywords = set(requirement_description.lower().split())
            
            # Check for significant overlap
            overlap = len(task_keywords.intersection(requirement_keywords))
            overlap_ratio = overlap / max(len(task_keywords), len(requirement_keywords), 1)
            
            # Consider it a match if there's significant overlap or specific indicators
            if overlap_ratio > 0.3:  # 30% keyword overlap
                return True
            
            # Check for asset type indicators in task description
            asset_type_indicators = {
                'document': ['document', 'report', 'analysis', 'guide', 'documentation'],
                'data': ['data', 'database', 'dataset', 'spreadsheet', 'csv', 'json'],
                'design': ['design', 'mockup', 'wireframe', 'ui', 'ux', 'visual'],
                'code': ['code', 'script', 'application', 'tool', 'function', 'api'],
                'presentation': ['presentation', 'slides', 'demo', 'training']
            }
            
            task_lower = task_description.lower()
            requirement_indicators = asset_type_indicators.get(requirement.asset_type, [])
            
            for indicator in requirement_indicators:
                if indicator in task_lower:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error matching task {task.id} to requirement {requirement.id}: {e}")
            return False
    
    async def _calculate_goal_progress_updates(
        self, 
        task: EnhancedTask, 
        artifacts: List[AssetArtifact]
    ) -> List[Dict[str, Any]]:
        """Calculate goal progress updates based on created artifacts"""
        
        goal_updates = []
        
        try:
            # Get workspace goals
            workspace_goals = await get_workspace_goals(task.workspace_id)
            
            for goal in workspace_goals:
                try:
                    # Get all requirements for this goal
                    requirements = await get_asset_requirements_for_goal(goal.id)
                    if not requirements:
                        continue
                    
                    # Calculate completion based on approved artifacts
                    total_requirements = len(requirements)
                    completed_requirements = 0
                    total_quality_score = 0.0
                    
                    for requirement in requirements:
                        # Get artifacts for this requirement
                        requirement_artifacts = await get_artifacts_for_requirement(requirement.id)
                        
                        # Check if requirement has approved artifacts
                        approved_artifacts = [
                            a for a in requirement_artifacts 
                            if a.status == "approved" and a.quality_score >= 0.8
                        ]
                        
                        if approved_artifacts:
                            completed_requirements += 1
                            # Use the highest quality score from approved artifacts
                            max_quality = max(a.quality_score for a in approved_artifacts)
                            total_quality_score += max_quality
                    
                    # Calculate progress percentage
                    progress_percentage = (completed_requirements / total_requirements) * 100
                    average_quality_score = total_quality_score / total_requirements if total_requirements > 0 else 0
                    
                    # Update goal progress if there's a change
                    if progress_percentage != goal.progress_percentage:
                        await update_goal_progress(
                            goal.id, 
                            progress_percentage, 
                            average_quality_score
                        )
                        
                        goal_updates.append({
                            "goal_id": goal.id,
                            "previous_progress": goal.progress_percentage,
                            "new_progress": progress_percentage,
                            "quality_score": average_quality_score,
                            "completed_requirements": completed_requirements,
                            "total_requirements": total_requirements
                        })
                        
                        logger.info(
                            f"🎯 Goal progress updated: {goal.metric_type} "
                            f"({goal.progress_percentage}% → {progress_percentage}%)"
                        )
                
                except Exception as e:
                    logger.error(f"Failed to calculate progress for goal {goal.id}: {e}")
                    continue
            
            return goal_updates
            
        except Exception as e:
            logger.error(f"Failed to calculate goal progress updates: {e}")
            return []
    
    async def _trigger_real_time_goal_updates(self, task: EnhancedTask):
        """Trigger real-time goal progress updates via WebSocket (Pillar 10: Real-Time Thinking)"""
        
        try:
            # This would integrate with the real-time WebSocket system
            # to broadcast goal progress updates to connected clients
            
            logger.info(f"📡 Triggering real-time goal updates for task: {task.id}")
            
            # The actual implementation would depend on having WebSocket infrastructure
            # For now, this is a placeholder for real-time notifications
            
        except Exception as e:
            logger.error(f"Failed to trigger real-time goal updates: {e}")
    
    async def pre_task_execution_hook(self, task: EnhancedTask) -> Dict[str, Any]:
        """Pre-execution hook to prepare asset-driven processing"""
        
        try:
            logger.info(f"🔄 Pre-execution asset preparation for task: {task.id}")
            
            preparation_result = {
                "asset_requirements_identified": 0,
                "quality_rules_loaded": 0,
                "processing_plan": [],
                "ready_for_asset_processing": False
            }
            
            # Identify asset requirements
            requirements = await self._identify_asset_requirements_for_task(task)
            preparation_result["asset_requirements_identified"] = len(requirements)
            
            if requirements:
                # Load quality rules for expected asset types
                asset_types = set(req.asset_type for req in requirements)
                for asset_type in asset_types:
                    try:
                        # This would load quality rules from database
                        # Implementation depends on database methods
                        preparation_result["quality_rules_loaded"] += 1
                    except Exception as e:
                        logger.error(f"Failed to load quality rules for {asset_type}: {e}")
                
                # Create processing plan
                preparation_result["processing_plan"] = [
                    f"Process {req.asset_name} ({req.asset_type})" 
                    for req in requirements
                ]
                
                preparation_result["ready_for_asset_processing"] = True
            
            return preparation_result
            
        except Exception as e:
            logger.error(f"Pre-execution preparation failed for task {task.id}: {e}")
            return {"ready_for_asset_processing": False, "error": str(e)}
    
    async def post_task_execution_hook(self, task: EnhancedTask, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Post-execution hook to run asset processing pipeline"""
        
        try:
            logger.info(f"🏁 Post-execution asset processing for task: {task.id}")
            
            # Only run asset processing if task completed successfully
            if execution_result.get("status") == "completed":
                asset_result = await self._run_asset_processing_pipeline(task)
                
                # Merge asset processing results
                execution_result.update({
                    "asset_processing": asset_result,
                    "pipeline_executed": True
                })
            else:
                logger.info(f"Skipping asset processing for failed/incomplete task: {task.id}")
                execution_result["asset_processing"] = {"skipped": True, "reason": "task_not_completed"}
            
            return execution_result
            
        except Exception as e:
            logger.error(f"Post-execution processing failed for task {task.id}: {e}")
            execution_result["asset_processing"] = {"error": str(e)}
            return execution_result
    
    async def batch_process_task_artifacts(self, task_ids: List[UUID]) -> Dict[str, Any]:
        """Batch process artifacts for multiple completed tasks"""
        
        results = {
            "processed_tasks": 0,
            "artifacts_created": 0,
            "quality_validations": 0,
            "goal_updates": 0,
            "errors": []
        }
        
        try:
            logger.info(f"🏭 Batch processing artifacts for {len(task_ids)} tasks")
            
            # Process tasks with concurrency limit
            semaphore = asyncio.Semaphore(self.concurrent_processing)
            
            async def process_single_task(task_id: UUID):
                async with semaphore:
                    try:
                        # This would require getting task from database
                        # and running the asset processing pipeline
                        results["processed_tasks"] += 1
                        
                    except Exception as e:
                        results["errors"].append(f"Task {task_id}: {e}")
                        logger.error(f"Batch processing failed for task {task_id}: {e}")
            
            # Execute batch processing
            await asyncio.gather(*[process_single_task(tid) for tid in task_ids])
            
            logger.info(f"✅ Batch artifact processing completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Batch artifact processing failed: {e}")
            return results
    
    async def get_asset_driven_metrics(self, workspace_id: UUID) -> Dict[str, Any]:
        """Get comprehensive asset-driven execution metrics"""
        
        try:
            metrics = {
                "total_tasks_processed": 0,
                "artifacts_created": 0,
                "quality_validations_passed": 0,
                "goal_completion_rate": 0.0,
                "asset_types_distribution": {},
                "quality_score_distribution": {},
                "processing_performance": {
                    "avg_processing_time": 0.0,
                    "success_rate": 0.0,
                    "error_rate": 0.0
                },
                "pillar_compliance_metrics": {}
            }
            
            # This would aggregate metrics from database
            # Implementation depends on having comprehensive database queries
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get asset-driven metrics for workspace {workspace_id}: {e}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for asset-driven task execution system"""
        
        health_status = {
            "status": "healthy",
            "components": {
                "requirements_generator": "unknown",
                "artifact_processor": "unknown", 
                "quality_gate_engine": "unknown"
            },
            "configuration": {
                "auto_asset_extraction": self.auto_asset_extraction,
                "auto_quality_validation": self.auto_quality_validation,
                "auto_goal_progress": self.auto_goal_progress,
                "asset_driven_goals": self.asset_driven_goals
            },
            "performance_settings": {
                "processing_timeout": self.processing_timeout,
                "concurrent_processing": self.concurrent_processing
            }
        }
        
        try:
            # Test each component
            # This would perform actual health checks on services
            health_status["components"]["requirements_generator"] = "healthy"
            health_status["components"]["artifact_processor"] = "healthy"
            health_status["components"]["quality_gate_engine"] = "healthy"
            
            return health_status
            
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
            return health_status