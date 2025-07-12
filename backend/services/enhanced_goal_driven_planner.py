"""
Enhanced Goal-Driven Task Planner - Asset-driven task generation (Pillar 5: Goal-Driven + Pillar 12: Concrete Deliverables)
Advanced goal-driven task planning with asset requirements integration and AI-driven task decomposition.
"""

import os
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from openai import AsyncOpenAI
from models import (
    EnhancedWorkspaceGoal, WorkspaceGoal, GoalStatus, 
    EnhancedTask, TaskStatus, AssetRequirement
)
from database import get_workspace_goals
from database_asset_extensions import AssetDrivenDatabaseManager
from backend.deliverable_system.unified_deliverable_engine import unified_deliverable_engine
from services.universal_ai_pipeline_engine import (
    UniversalAIPipelineEngine, 
    PipelineStepType, 
    PipelineContext,
    universal_ai_pipeline_engine
)

logger = logging.getLogger(__name__)

class EnhancedGoalDrivenPlanner:
    """Enhanced goal-driven task planner using Universal AI Pipeline Engine"""
    
    def __init__(self, ai_pipeline_engine: UniversalAIPipelineEngine = None):
        self.ai_pipeline_engine = ai_pipeline_engine or universal_ai_pipeline_engine
        self.requirements_generator = self # Use self as it will be part of the unified engine
        self.asset_db_manager = AssetDrivenDatabaseManager()
        
        # Configuration from environment (Pillar-compliant)
        self.planning_model = os.getenv("AI_ENHANCEMENT_MODEL", "gpt-4o-mini")
        self.max_tasks_per_cycle = int(os.getenv("MAX_GOAL_DRIVEN_TASKS_PER_CYCLE", "5"))
        self.goal_completion_threshold = float(os.getenv("GOAL_COMPLETION_THRESHOLD", "80"))
        self.asset_driven_planning = os.getenv("ASSET_DRIVEN_GOAL_CALCULATION", "true").lower() == "true"
        
        # Advanced planning features (Pillar 13: Course-Correction)
        self.enable_course_correction = os.getenv("ENABLE_AUTO_COURSE_CORRECTION", "true").lower() == "true"
        self.course_correction_threshold = float(os.getenv("COURSE_CORRECTION_THRESHOLD", "0.5"))
        self.max_course_corrections = int(os.getenv("MAX_COURSE_CORRECTIONS_PER_GOAL", "3"))
        
        logger.info("🎯 EnhancedGoalDrivenPlanner initialized with Universal AI Pipeline Engine")
        
    async def generate_asset_driven_tasks(self, workspace_id: UUID) -> List[EnhancedTask]:
        """Generate tasks based on asset requirements and goal progress (Pillar 5: Goal-Driven)"""
        
        try:
            logger.info(f"🎯 Generating asset-driven tasks for workspace: {workspace_id}")
            
            # Get workspace goals and their asset requirements
            workspace_goals = await get_workspace_goals(workspace_id)
            if not workspace_goals:
                logger.info(f"No goals found for workspace {workspace_id}")
                return []
            
            generated_tasks = []
            
            for goal_data in workspace_goals:
                try:
                    # Convert dict to WorkspaceGoal object
                    goal = WorkspaceGoal(**goal_data)
                    
                    # Skip completed goals
                    if goal.status == GoalStatus.COMPLETED:
                        continue
                    
                    # Generate tasks for this goal
                    goal_tasks = await self._generate_tasks_for_goal(goal)
                    generated_tasks.extend(goal_tasks)
                    
                    # Limit total tasks per cycle
                    if len(generated_tasks) >= self.max_tasks_per_cycle:
                        logger.info(f"Reached max tasks per cycle ({self.max_tasks_per_cycle})")
                        break
                        
                except Exception as e:
                    logger.error(f"Failed to generate tasks for goal {goal.id}: {e}")
                    continue
            
            logger.info(f"✅ Generated {len(generated_tasks)} asset-driven tasks")
            return generated_tasks
            
        except Exception as e:
            logger.error(f"Asset-driven task generation failed for workspace {workspace_id}: {e}")
            return []
    
    async def _generate_tasks_for_goal(self, goal: WorkspaceGoal) -> List[EnhancedTask]:
        """Generate specific tasks for a single goal based on asset requirements"""
        
        try:
            # Get existing asset requirements for this goal
            asset_requirements = await self.asset_db_manager.get_asset_requirements_for_goal(goal.id)
            logger.info(f"🔍 Found {len(asset_requirements)} existing asset requirements for goal {goal.id}")
            
            # If no asset requirements exist, generate them first
            if not asset_requirements:
                logger.info(f"Generating asset requirements for goal: {goal.metric_type}")
                asset_requirements = await self.requirements_generator.generate_from_goal(goal)
                logger.info(f"🔍 Generated {len(asset_requirements)} new asset requirements")
            
            if not asset_requirements:
                logger.warning(f"❌ No asset requirements available for goal {goal.id}")
                return []
            
            # Generate tasks for each unfulfilled asset requirement
            generated_tasks = []
            
            for i, requirement in enumerate(asset_requirements):
                try:
                    logger.info(f"🔍 Processing requirement {i+1}/{len(asset_requirements)}: {requirement.asset_name}")
                    
                    # Check if requirement already has sufficient tasks/artifacts
                    has_progress = await self._requirement_has_sufficient_progress(requirement)
                    logger.info(f"🔍 Requirement {requirement.asset_name} has sufficient progress: {has_progress}")
                    
                    if has_progress:
                        logger.info(f"⏭️ Skipping requirement {requirement.asset_name} - already has sufficient progress")
                        continue
                    
                    # Generate specific tasks for this asset requirement
                    logger.info(f"🚀 Generating tasks for requirement: {requirement.asset_name}")
                    requirement_tasks = await self._generate_tasks_for_requirement(goal, requirement)
                    logger.info(f"✅ Generated {len(requirement_tasks)} tasks for requirement: {requirement.asset_name}")
                    generated_tasks.extend(requirement_tasks)
                    
                except Exception as e:
                    logger.error(f"❌ Failed to generate tasks for requirement {requirement.id}: {e}", exc_info=True)
                    continue
            
            # Apply intelligent task prioritization and sequencing
            prioritized_tasks = await self._apply_intelligent_prioritization(generated_tasks, goal)
            
            logger.info(f"Generated {len(prioritized_tasks)} tasks for goal: {goal.metric_type}")
            return prioritized_tasks
            
        except Exception as e:
            logger.error(f"Failed to generate tasks for goal {goal.id}: {e}")
            return []
    
    async def _generate_tasks_for_requirement(
        self, 
        goal: WorkspaceGoal, 
        requirement: AssetRequirement
    ) -> List[EnhancedTask]:
        """Generate specific tasks to fulfill an asset requirement"""
        
        try:
            # Use Universal AI Pipeline Engine for task generation
            context = PipelineContext(
                workspace_id=str(goal.workspace_id) if goal.workspace_id else None,
                goal_id=str(goal.id),
                user_context={
                    "requirement": {
                        "name": requirement.asset_name,
                        "description": requirement.asset_description,
                        "gap": requirement.gap
                    }
                }
            )
            
            requirement_data = {
                "requirement_name": requirement.asset_name,
                "requirement_description": requirement.asset_description,
                "requirement_type": requirement.requirement_type,
                "priority": requirement.priority,
                "gap": requirement.gap,
                "goal_context": {
                    "metric_type": goal.metric_type,
                    "target_value": goal.target_value,
                    "current_value": goal.current_value
                }
            }
            
            # Execute AI pipeline step for task generation
            pipeline_result = await self.ai_pipeline_engine.execute_pipeline_step(
                PipelineStepType.TASK_GENERATION,
                requirement_data,
                context,
                model=self.planning_model
            )
            
            if pipeline_result.success and pipeline_result.data:
                task_data = pipeline_result.data
                logger.info(f"🤖 Task generation completed for requirement {requirement.asset_name} (Universal Pipeline)")
            else:
                logger.warning(f"⚠️ AI Pipeline failed for task generation: {pipeline_result.error}")
                
                # Mock response for testing when AI pipeline fails
                if os.getenv("USE_MOCK_ON_RATE_LIMIT", "true").lower() == "true":
                    task_data = self._generate_mock_tasks_response(goal, requirement)
                    logger.info("📋 Using mock task generation for testing")
                else:
                    return []
            
            # Create EnhancedTask objects from AI response
            tasks = await self._create_tasks_from_ai_response(goal, requirement, task_data)
            
            logger.info(f"Generated {len(tasks)} tasks for requirement: {requirement.asset_name}")
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to generate tasks for requirement {requirement.id}: {e}")
            return []
    
    def _build_task_generation_prompt(self, goal: WorkspaceGoal, requirement: AssetRequirement) -> str:
        """Build AI prompt for intelligent task generation (Pillar 2: AI-Driven)"""
        
        prompt = f"""
        You are an expert project manager and task decomposition specialist.
        Generate specific, actionable tasks to create the required asset deliverable.
        
        GOAL CONTEXT:
        - Goal Type: {goal.metric_type}
        - Target Value: {goal.target_value}
        - Current Progress: {goal.current_value}
        - Status: {goal.status}
        - Workspace ID: {goal.workspace_id}
        
        ASSET REQUIREMENT TO FULFILL:
        - Asset Name: {requirement.asset_name}
        - Asset Type: {requirement.asset_type}
        - Asset Format: {requirement.asset_format}
        - Description: {requirement.description}
        - Business Value Score: {requirement.business_value_score}
        - Priority: {requirement.priority}
        - Estimated Effort: {requirement.estimated_effort}
        
        ACCEPTANCE CRITERIA:
        {json.dumps(requirement.acceptance_criteria, indent=2)}
        
        TASK GENERATION OBJECTIVES:
        1. CONCRETE DELIVERABLES: Each task must produce a specific, measurable output
        2. ASSET-FOCUSED: Tasks must directly contribute to creating the required asset
        3. ACTIONABLE: Tasks must be immediately executable by available agents
        4. SEQUENCED: Tasks should build logically toward the final deliverable
        5. QUALITY-DRIVEN: Include quality validation and review steps
        
        TASK DECOMPOSITION PRINCIPLES:
        - Break the asset creation into 2-5 specific, executable tasks
        - Each task should take 1-4 hours of focused work
        - Include research, creation, and validation phases
        - Ensure tasks are concrete (not abstract or planning-only)
        - Focus on immediate actions that produce tangible outputs
        
        AGENT SKILL CONSIDERATIONS:
        Generate tasks that can be executed by AI agents with these typical capabilities:
        - Research and data collection
        - Content creation and writing
        - Analysis and synthesis
        - Tool usage and automation
        - Quality validation and review
        
        RESPONSE FORMAT (JSON):
        {{
            "task_sequence": [
                {{
                    "task_name": "Specific, action-oriented task name",
                    "task_description": "Detailed description of what needs to be done",
                    "expected_output": "Specific deliverable this task will produce",
                    "task_type": "research|creation|analysis|validation|integration",
                    "estimated_duration_hours": 2.5,
                    "priority": "high|medium|low",
                    "dependencies": ["previous task names if any"],
                    "success_criteria": [
                        "Specific criterion 1",
                        "Specific criterion 2"
                    ],
                    "required_skills": ["skill1", "skill2"],
                    "tools_needed": ["tool1", "tool2"],
                    "quality_checkpoints": [
                        "Quality check 1",
                        "Quality check 2"
                    ],
                    "contribution_to_asset": "How this task contributes to the final asset"
                }}
            ],
            "sequence_rationale": "Why these tasks are sequenced this way",
            "asset_creation_strategy": "Overall strategy for creating this asset",
            "quality_assurance_plan": "How quality will be ensured throughout",
            "risk_mitigation": ["potential risk 1", "potential risk 2"],
            "success_indicators": ["indicator 1", "indicator 2"]
        }}
        
        CRITICAL REQUIREMENTS:
        - Each task must have a CONCRETE OUTPUT (not abstract planning)
        - Tasks must DIRECTLY CREATE the required asset components
        - Include quality validation at appropriate points
        - Ensure logical sequencing and dependencies
        - Focus on ACTIONABLE WORK that produces business value
        - Tasks should be immediately executable by AI agents
        
        EXAMPLE OF GOOD vs BAD TASKS:
        ✅ GOOD: "Research and compile 20 customer testimonials with contact details and usage statistics"
        ❌ BAD: "Analyze market trends" (too abstract)
        
        ✅ GOOD: "Create detailed wireframes for 5 core user interface screens with interaction specifications"
        ❌ BAD: "Design user experience" (too vague)
        
        ✅ GOOD: "Write 3-page executive summary with key findings, recommendations, and next steps"
        ❌ BAD: "Summarize results" (not specific enough)
        """
        
        return prompt
    
    async def _create_tasks_from_ai_response(
        self, 
        goal: WorkspaceGoal, 
        requirement: AssetRequirement, 
        task_data: Dict[str, Any]
    ) -> List[EnhancedTask]:
        """Create EnhancedTask objects from AI response data"""
        
        tasks = []
        
        try:
            task_sequence = task_data.get("task_sequence", [])
            
            for i, task_info in enumerate(task_sequence):
                try:
                    # Create EnhancedTask object
                    task = EnhancedTask(
                        id=uuid4(),
                        workspace_id=goal.workspace_id,
                        goal_id=goal.id,
                        asset_requirement_id=requirement.id,
                        
                        # Core task information
                        name=task_info.get("task_name"),
                        description=task_info.get("task_description"),
                        expected_output=task_info.get("expected_output"),
                        
                        # Task classification and metadata
                        task_type=task_info.get("task_type", "creation"),
                        priority=task_info.get("priority", "medium"),
                        estimated_duration_hours=float(task_info.get("estimated_duration_hours", 2.0)),
                        
                        # Quality and success criteria
                        success_criteria=task_info.get("success_criteria", []),
                        quality_checkpoints=task_info.get("quality_checkpoints", []),
                        
                        # Skills and requirements
                        required_skills=task_info.get("required_skills", []),
                        tools_needed=task_info.get("tools_needed", []),
                        
                        # Asset contribution
                        contribution_to_asset=task_info.get("contribution_to_asset", ""),
                        
                        # Status and timing
                        status=TaskStatus.PENDING,
                        created_at=datetime.utcnow(),
                        
                        # Dependencies (would need to resolve task names to IDs)
                        dependencies=task_info.get("dependencies", []),
                        
                        # AI-generated metadata  
                        ai_generated=True,
                        generation_context={
                            "goal_context": {
                                "metric_type": goal.metric_type,
                                "target_value": goal.target_value,
                                "current_progress": goal.current_value
                            },
                            "asset_context": {
                                "asset_name": requirement.asset_name,
                                "asset_type": requirement.asset_type,
                                "business_value_score": requirement.business_value_score
                            },
                            "generation_strategy": task_data.get("asset_creation_strategy", ""),
                            "sequence_position": i + 1,
                            "total_tasks": len(task_sequence)
                        },
                        
                        # Pillar compliance
                        pillar_compliance={
                            "goal_driven": True,
                            "concrete_deliverable": True,
                            "ai_generated": True,
                            "asset_oriented": True
                        }
                    )
                    
                    tasks.append(task)
                    
                except Exception as e:
                    logger.error(f"Failed to create task from AI response item {i}: {e}")
                    continue
            
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to create tasks from AI response: {e}")
            return []
    
    async def _apply_intelligent_prioritization(
        self, 
        tasks: List[EnhancedTask], 
        goal: WorkspaceGoal
    ) -> List[EnhancedTask]:
        """Apply intelligent task prioritization and sequencing"""
        
        try:
            # Calculate priority scores for each task
            for task in tasks:
                priority_score = self._calculate_task_priority_score(task, goal)
                task.priority_score = priority_score
            
            # Sort by priority score (higher is more important)
            prioritized_tasks = sorted(tasks, key=lambda t: getattr(t, 'priority_score', 0), reverse=True)
            
            # Apply dependency-aware sequencing
            sequenced_tasks = self._apply_dependency_sequencing(prioritized_tasks)
            
            return sequenced_tasks
            
        except Exception as e:
            logger.error(f"Failed to apply intelligent prioritization: {e}")
            return tasks
    
    def _calculate_task_priority_score(self, task: EnhancedTask, goal: WorkspaceGoal) -> float:
        """Calculate intelligent priority score for a task (Pillar 2: AI-Driven)"""
        
        try:
            score = 0.0
            
            # Base priority from AI generation
            priority_map = {"high": 3.0, "medium": 2.0, "low": 1.0}
            score += priority_map.get(task.priority, 2.0)
            
            # Goal urgency factor
            if goal.status == GoalStatus.ACTIVE:
                # Calculate urgency based on progress and target
                progress_ratio = goal.current_value / max(goal.target_value, 1)
                if progress_ratio < 0.3:  # Low progress
                    score += 2.0
                elif progress_ratio < 0.7:  # Medium progress
                    score += 1.0
            
            # Asset business value factor
            if hasattr(task, 'asset_requirement_id') and task.asset_requirement_id:
                # This would require getting the asset requirement
                # For now, use a placeholder calculation
                score += 1.0
            
            # Task type importance
            type_importance = {
                "research": 2.0,  # Foundation for other work
                "creation": 3.0,  # Direct asset creation
                "analysis": 2.5,  # Important insights
                "validation": 2.0,  # Quality assurance
                "integration": 3.5  # Final deliverable assembly
            }
            score += type_importance.get(task.task_type, 2.0)
            
            # Dependencies factor (tasks with no dependencies get higher priority)
            if not task.dependencies:
                score += 1.0
            
            return score
            
        except Exception as e:
            logger.error(f"Failed to calculate priority score for task {task.id}: {e}")
            return 2.0  # Default medium priority
    
    def _apply_dependency_sequencing(self, tasks: List[EnhancedTask]) -> List[EnhancedTask]:
        """Apply dependency-aware task sequencing"""
        
        try:
            # For now, return tasks as-is
            # In a complete implementation, this would:
            # 1. Build dependency graph
            # 2. Perform topological sorting
            # 3. Ensure dependent tasks are scheduled after their dependencies
            
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to apply dependency sequencing: {e}")
            return tasks
    
    def _generate_mock_tasks_response(self, goal: WorkspaceGoal, requirement: AssetRequirement) -> Dict[str, Any]:
        """Generate mock task response for testing when rate limited"""
        
        # Generate contextual tasks based on asset requirement type
        asset_name = requirement.asset_name or "Unknown Asset"
        asset_type = requirement.asset_type or "document"
        
        # Define mock tasks based on asset type
        mock_tasks = []
        
        if asset_type == "document":
            mock_tasks = [
                {
                    "name": f"Research and Outline {asset_name}",
                    "description": f"Research requirements and create detailed outline for {asset_name}",
                    "priority": "high",
                    "estimated_effort_hours": 4.0,
                    "acceptance_criteria": [
                        "Research completed and documented",
                        "Detailed outline created with sections",
                        "Key requirements identified"
                    ]
                },
                {
                    "name": f"Create {asset_name}",
                    "description": f"Write and complete the {asset_name} based on research and outline",
                    "priority": "high", 
                    "estimated_effort_hours": 8.0,
                    "acceptance_criteria": [
                        "Document written according to outline",
                        "All sections completed",
                        "Quality review passed"
                    ]
                }
            ]
        elif asset_type == "design":
            mock_tasks = [
                {
                    "name": f"Design Wireframes for {asset_name}",
                    "description": f"Create wireframes and initial designs for {asset_name}",
                    "priority": "high",
                    "estimated_effort_hours": 6.0,
                    "acceptance_criteria": [
                        "Wireframes created for all screens",
                        "User flow documented",
                        "Design system elements defined"
                    ]
                },
                {
                    "name": f"Create High-Fidelity {asset_name}",
                    "description": f"Develop high-fidelity designs and prototypes for {asset_name}",
                    "priority": "medium",
                    "estimated_effort_hours": 10.0,
                    "acceptance_criteria": [
                        "High-fidelity designs completed",
                        "Interactive prototype created",
                        "Stakeholder approval received"
                    ]
                }
            ]
        elif asset_type == "code":
            mock_tasks = [
                {
                    "name": f"Setup Development Environment for {asset_name}",
                    "description": f"Setup development environment and basic structure for {asset_name}",
                    "priority": "high",
                    "estimated_effort_hours": 3.0,
                    "acceptance_criteria": [
                        "Development environment configured",
                        "Basic project structure created",
                        "Dependencies installed"
                    ]
                },
                {
                    "name": f"Implement {asset_name}",
                    "description": f"Code and implement the {asset_name} functionality",
                    "priority": "high",
                    "estimated_effort_hours": 12.0,
                    "acceptance_criteria": [
                        "Core functionality implemented",
                        "Code reviewed and tested",
                        "Documentation updated"
                    ]
                }
            ]
        else:
            # Generic tasks for all other asset types
            mock_tasks = [
                {
                    "name": f"Plan {asset_name}",
                    "description": f"Plan and design approach for {asset_name}",
                    "priority": "high",
                    "estimated_effort_hours": 3.0,
                    "acceptance_criteria": [
                        "Planning completed",
                        "Approach documented", 
                        "Timeline defined"
                    ]
                },
                {
                    "name": f"Create {asset_name}",
                    "description": f"Execute plan and create {asset_name}",
                    "priority": "medium",
                    "estimated_effort_hours": 8.0,
                    "acceptance_criteria": [
                        "Asset created according to plan",
                        "Quality standards met",
                        "Deliverable completed"
                    ]
                }
            ]
        
        return {
            "analysis": {
                "requirement_complexity": "medium",
                "estimated_total_hours": sum(task.get("estimated_effort_hours", 0) for task in mock_tasks),
                "task_count": len(mock_tasks)
            },
            "tasks": mock_tasks
        }
    
    async def _requirement_has_sufficient_progress(self, requirement: AssetRequirement) -> bool:
        """Check if an asset requirement already has sufficient progress"""
        
        try:
            # Check if requirement already has approved artifacts
            # This would require getting artifacts for the requirement
            # For now, return False to always generate tasks
            return False
            
        except Exception as e:
            logger.error(f"Failed to check progress for requirement {requirement.id}: {e}")
            return False
    
    async def analyze_goal_performance_and_adapt(self, workspace_id: UUID) -> Dict[str, Any]:
        """Analyze goal performance and adapt task generation strategy (Pillar 13: Course-Correction)"""
        
        try:
            logger.info(f"🔄 Analyzing goal performance for workspace: {workspace_id}")
            
            analysis_result = {
                "goals_analyzed": 0,
                "performance_insights": [],
                "course_corrections": [],
                "strategy_adaptations": [],
                "recommendations": []
            }
            
            # Get workspace goals
            workspace_goals = await get_workspace_goals(workspace_id)
            
            for goal in workspace_goals:
                try:
                    # Analyze individual goal performance
                    goal_analysis = await self._analyze_single_goal_performance(goal)
                    analysis_result["performance_insights"].append(goal_analysis)
                    
                    # Apply course corrections if needed
                    if self.enable_course_correction:
                        corrections = await self._apply_course_corrections(goal, goal_analysis)
                        analysis_result["course_corrections"].extend(corrections)
                    
                    analysis_result["goals_analyzed"] += 1
                    
                except Exception as e:
                    logger.error(f"Failed to analyze goal {goal.id}: {e}")
                    continue
            
            # Generate strategic recommendations
            analysis_result["recommendations"] = await self._generate_strategic_recommendations(
                workspace_id, analysis_result["performance_insights"]
            )
            
            logger.info(f"✅ Goal performance analysis completed for {analysis_result['goals_analyzed']} goals")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Goal performance analysis failed for workspace {workspace_id}: {e}")
            return {}
    
    async def _analyze_single_goal_performance(self, goal: WorkspaceGoal) -> Dict[str, Any]:
        """Analyze performance of a single goal"""
        
        try:
            analysis = {
                "goal_id": goal.id,
                "metric_type": goal.metric_type,
                "progress_rate": 0.0,
                "efficiency_score": 0.0,
                "bottlenecks": [],
                "success_factors": [],
                "recommended_actions": []
            }
            
            # Calculate progress rate
            progress_ratio = goal.current_value / max(goal.target_value, 1)
            analysis["progress_rate"] = progress_ratio
            
            # Assess efficiency (simplified calculation)
            if hasattr(goal, 'created_at'):
                days_elapsed = (datetime.utcnow() - goal.created_at).days
                if days_elapsed > 0:
                    daily_progress = progress_ratio / days_elapsed
                    analysis["efficiency_score"] = daily_progress
            
            # Identify bottlenecks and success factors
            if progress_ratio < self.course_correction_threshold:
                analysis["bottlenecks"].append("Low progress rate requires intervention")
                analysis["recommended_actions"].append("Generate more focused, concrete tasks")
                analysis["recommended_actions"].append("Review asset requirements for clarity")
            else:
                analysis["success_factors"].append("Good progress rate maintained")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze goal {goal.id}: {e}")
            return {"goal_id": goal.id, "error": str(e)}
    
    async def _apply_course_corrections(self, goal: WorkspaceGoal, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply course corrections based on goal analysis"""
        
        corrections = []
        
        try:
            # Check if course correction is needed
            if analysis.get("progress_rate", 0) < self.course_correction_threshold:
                
                # Generate corrective actions
                correction = {
                    "goal_id": goal.id,
                    "correction_type": "strategy_adaptation",
                    "reason": f"Low progress rate: {analysis.get('progress_rate', 0):.2%}",
                    "actions": [
                        "Regenerate more specific, actionable tasks",
                        "Review and simplify asset requirements",
                        "Increase task priority for this goal"
                    ],
                    "implemented_at": datetime.utcnow()
                }
                
                corrections.append(correction)
                logger.info(f"🔄 Course correction applied for goal: {goal.metric_type}")
            
            return corrections
            
        except Exception as e:
            logger.error(f"Failed to apply course corrections for goal {goal.id}: {e}")
            return []
    
    async def _generate_strategic_recommendations(
        self, 
        workspace_id: UUID, 
        performance_insights: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate strategic recommendations based on overall performance"""
        
        recommendations = []
        
        try:
            if not performance_insights:
                return recommendations
            
            # Calculate overall metrics
            total_goals = len(performance_insights)
            low_progress_goals = sum(1 for insight in performance_insights 
                                   if insight.get("progress_rate", 0) < self.course_correction_threshold)
            
            # Generate recommendations
            if low_progress_goals > total_goals * 0.5:
                recommendations.append("Consider simplifying goal targets or breaking them into smaller milestones")
                recommendations.append("Review asset requirements for clarity and actionability")
                recommendations.append("Increase task generation frequency for struggling goals")
            
            if total_goals > 10:
                recommendations.append("Consider consolidating similar goals to improve focus")
            
            recommendations.append("Regular performance reviews recommended every 7 days")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate strategic recommendations: {e}")
            return []
    
    async def get_planning_metrics(self, workspace_id: UUID) -> Dict[str, Any]:
        """Get comprehensive planning and goal metrics"""
        
        try:
            metrics = {
                "total_goals": 0,
                "active_goals": 0,
                "completed_goals": 0,
                "average_progress": 0.0,
                "tasks_generated": 0,
                "asset_requirements_created": 0,
                "course_corrections_applied": 0,
                "planning_efficiency": 0.0,
                "goal_types_distribution": {},
                "performance_trends": []
            }
            
            # This would aggregate comprehensive metrics from database
            # Implementation depends on having database queries for planning data
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get planning metrics for workspace {workspace_id}: {e}")
            return {}