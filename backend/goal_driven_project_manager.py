# backend/goal_driven_project_manager.py

import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from models import WorkspaceGoal, Task, TaskStatus, GoalStatus
from database import supabase
from goal_driven_task_planner import goal_driven_task_planner
from automated_goal_monitor import automated_goal_monitor

logger = logging.getLogger(__name__)

class GoalDrivenProjectManager:
    """
    🎯 STEP 4: Transformed Project Manager (Reviewer, not Author)
    
    OLD: PM creates theoretical analytical tasks manually
    NEW: PM reviews and approves goal-driven tasks from Task Planner
    
    Key changes:
    1. Task generation delegated to Goal-Driven Task Planner
    2. PM focuses on task review, quality, and approval
    3. Goal alignment validation before task approval
    4. Memory-guided task refinement
    5. Automatic course correction integration
    """
    
    def __init__(self, workspace_id: UUID):
        self.workspace_id = workspace_id
        self.task_approval_threshold = 0.8  # Quality threshold for auto-approval
        self.manual_review_required_types = ["corrective_action", "critical_gap"]
        
    async def orchestrate_workspace_goals(self) -> Dict[str, Any]:
        """
        🎯 NEW ORCHESTRATION: Goal-driven approach
        
        1. Generate goal-driven tasks using Task Planner
        2. Review and approve/refine tasks
        3. Monitor goal progress and trigger corrections
        4. Focus on goal achievement, not task creation
        """
        try:
            logger.info(f"🎯 Starting goal-driven orchestration for workspace {self.workspace_id}")
            
            # 1. 📊 ANALYZE CURRENT GOAL STATUS
            goal_analysis = await self._analyze_current_goals()
            
            if not goal_analysis["active_goals"]:
                logger.warning(f"No active goals found for workspace {self.workspace_id}")
                return {"status": "no_goals", "message": "No active goals to orchestrate"}
            
            # 2. 🎯 GENERATE GOAL-DRIVEN TASKS
            generated_tasks = await goal_driven_task_planner.generate_tasks_for_unmet_goals(
                workspace_id=self.workspace_id,
                context=goal_analysis
            )
            
            if not generated_tasks:
                logger.info(f"✅ All goals met for workspace {self.workspace_id}")
                return {"status": "goals_met", "message": "All workspace goals achieved"}
            
            # 3. 🔍 REVIEW AND APPROVE TASKS (PM as Reviewer)
            approved_tasks, refinement_needed = await self._review_generated_tasks(generated_tasks)
            
            # 4. 📋 CREATE APPROVED TASKS
            created_tasks = await self._create_approved_tasks(approved_tasks)
            
            # 5. 🔄 HANDLE TASKS NEEDING REFINEMENT
            refined_tasks = await self._handle_task_refinement(refinement_needed)
            
            # 6. 🚨 TRIGGER IMMEDIATE VALIDATION if corrective tasks created
            if any(task.get("is_corrective") for task in created_tasks + refined_tasks):
                await automated_goal_monitor.trigger_immediate_validation(str(self.workspace_id))
            
            # 7. 📊 SUMMARY REPORT
            orchestration_summary = {
                "status": "success",
                "workspace_id": str(self.workspace_id),
                "goal_analysis": goal_analysis,
                "tasks_generated": len(generated_tasks),
                "tasks_approved": len(approved_tasks),
                "tasks_created": len(created_tasks),
                "tasks_refined": len(refined_tasks),
                "requires_refinement": len(refinement_needed),
                "next_actions": self._generate_next_actions(goal_analysis, created_tasks)
            }
            
            logger.info(
                f"🎯 Goal-driven orchestration completed: "
                f"{len(created_tasks)} tasks created, {len(refined_tasks)} refined"
            )
            
            return orchestration_summary
            
        except Exception as e:
            logger.error(f"Error in goal-driven orchestration: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _analyze_current_goals(self) -> Dict[str, Any]:
        """Analyze current goal status and progress"""
        try:
            # Get active goals for workspace
            response = supabase.table("workspace_goals").select("*").eq(
                "workspace_id", str(self.workspace_id)
            ).eq(
                "status", GoalStatus.ACTIVE.value
            ).execute()
            
            active_goals = []
            total_completion = 0
            unmet_goals = []
            
            for goal_data in response.data:
                goal = WorkspaceGoal(**goal_data)
                active_goals.append(goal)
                total_completion += goal.completion_percentage
                
                if not goal.is_completed:
                    unmet_goals.append(goal)
            
            # Calculate overall progress
            overall_progress = (total_completion / len(active_goals)) if active_goals else 0
            
            # Get recent task performance
            task_performance = await self._get_task_performance_metrics()
            
            analysis = {
                "active_goals": len(active_goals),
                "unmet_goals": len(unmet_goals),
                "overall_progress_pct": round(overall_progress, 1),
                "goals_data": [
                    {
                        "id": str(goal.id),
                        "metric_type": goal.metric_type,
                        "target": goal.target_value,
                        "current": goal.current_value,
                        "completion_pct": goal.completion_percentage,
                        "remaining": goal.remaining_value,
                        "needs_attention": goal.completion_percentage < 50
                    }
                    for goal in active_goals
                ],
                "task_performance": task_performance,
                "priority_goals": [
                    goal for goal in unmet_goals 
                    if goal.priority <= 2 and goal.completion_percentage < 50
                ]
            }
            
            logger.info(
                f"📊 Goal analysis: {len(active_goals)} active, "
                f"{len(unmet_goals)} unmet, {overall_progress:.1f}% complete"
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing current goals: {e}")
            return {"active_goals": 0, "error": str(e)}
    
    async def _get_task_performance_metrics(self) -> Dict[str, Any]:
        """Get recent task performance for goal-driven decisions"""
        try:
            # Get tasks from last 7 days
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            
            response = supabase.table("tasks").select("*").eq(
                "workspace_id", str(self.workspace_id)
            ).gte(
                "created_at", week_ago
            ).execute()
            
            tasks = response.data
            total_tasks = len(tasks)
            completed_tasks = sum(1 for t in tasks if t["status"] == "completed")
            goal_driven_tasks = sum(1 for t in tasks if t.get("goal_id"))
            corrective_tasks = sum(1 for t in tasks if t.get("is_corrective"))
            
            return {
                "total_tasks_7d": total_tasks,
                "completed_tasks_7d": completed_tasks,
                "completion_rate_pct": round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0,
                "goal_driven_tasks": goal_driven_tasks,
                "corrective_tasks": corrective_tasks,
                "avg_task_completion_hours": self._calculate_avg_completion_time(tasks)
            }
            
        except Exception as e:
            logger.error(f"Error getting task performance: {e}")
            return {}
    
    def _calculate_avg_completion_time(self, tasks: List[Dict]) -> float:
        """Calculate average task completion time"""
        completed_tasks = [t for t in tasks if t["status"] == "completed"]
        
        if not completed_tasks:
            return 0
        
        total_hours = 0
        count = 0
        
        for task in completed_tasks:
            try:
                created = datetime.fromisoformat(task["created_at"].replace("Z", "+00:00"))
                updated = datetime.fromisoformat(task["updated_at"].replace("Z", "+00:00"))
                duration_hours = (updated - created).total_seconds() / 3600
                total_hours += duration_hours
                count += 1
            except:
                continue
        
        return round(total_hours / count, 1) if count > 0 else 0
    
    async def _review_generated_tasks(
        self, 
        generated_tasks: List[Dict[str, Any]]
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        🔍 PM AS REVIEWER: Review and approve/refine generated tasks
        
        This is the core transformation - PM doesn't create tasks,
        but evaluates quality and goal alignment
        """
        approved_tasks = []
        refinement_needed = []
        
        for task in generated_tasks:
            try:
                # 1. 🎯 VALIDATE GOAL ALIGNMENT
                goal_alignment_score = await self._validate_goal_alignment(task)
                
                # 2. 📋 ASSESS TASK QUALITY
                quality_score = await self._assess_task_quality(task)
                
                # 3. 🔍 CHECK FOR MANUAL REVIEW REQUIREMENTS
                requires_manual_review = self._requires_manual_review(task)
                
                # 4. 🎯 MAKE APPROVAL DECISION
                overall_score = (goal_alignment_score + quality_score) / 2
                
                task_review = {
                    **task,
                    "review_scores": {
                        "goal_alignment": goal_alignment_score,
                        "quality": quality_score,
                        "overall": overall_score
                    },
                    "requires_manual_review": requires_manual_review,
                    "reviewed_by": "goal_driven_project_manager",
                    "reviewed_at": datetime.now().isoformat()
                }
                
                # 5. 📊 APPROVAL DECISION
                if overall_score >= self.task_approval_threshold and not requires_manual_review:
                    approved_tasks.append(task_review)
                    logger.info(
                        f"✅ AUTO-APPROVED task: {task['name']} "
                        f"(score: {overall_score:.2f})"
                    )
                else:
                    task_review["refinement_reasons"] = self._generate_refinement_feedback(
                        task, goal_alignment_score, quality_score
                    )
                    refinement_needed.append(task_review)
                    logger.warning(
                        f"🔄 NEEDS REFINEMENT: {task['name']} "
                        f"(score: {overall_score:.2f})"
                    )
                
            except Exception as e:
                logger.error(f"Error reviewing task {task.get('name')}: {e}")
                # Default to refinement needed for safety
                refinement_needed.append({
                    **task,
                    "refinement_reasons": [f"Review error: {str(e)}"]
                })
        
        logger.info(
            f"🔍 Task review completed: {len(approved_tasks)} approved, "
            f"{len(refinement_needed)} need refinement"
        )
        
        return approved_tasks, refinement_needed
    
    async def _validate_goal_alignment(self, task: Dict[str, Any]) -> float:
        """Validate how well task aligns with workspace goals"""
        try:
            # Check if task has goal_id and numerical target
            if not task.get("goal_id"):
                return 0.3  # Low score for non-goal-driven tasks
            
            # Check if numerical target is specific and measurable
            numerical_target = task.get("numerical_target", {})
            if not numerical_target.get("target") or not numerical_target.get("metric"):
                return 0.5  # Medium score for vague targets
            
            # Check if success criteria are concrete
            success_criteria = task.get("success_criteria", [])
            concrete_criteria = sum(
                1 for criteria in success_criteria
                if any(word in criteria.lower() for word in ["specific", "real", "complete", "exact"])
            )
            
            criteria_score = min(1.0, concrete_criteria / len(success_criteria)) if success_criteria else 0.5
            
            # Check contribution expected vs goal remaining
            contribution = task.get("contribution_expected", 0)
            if contribution > 0:
                # Higher score for tasks that make significant progress
                contribution_score = min(1.0, contribution / 10)  # Normalize to reasonable scale
            else:
                contribution_score = 0.3
            
            # Combine scores
            alignment_score = (0.4 * 1.0 +  # Has goal_id
                             0.3 * criteria_score +
                             0.3 * contribution_score)
            
            return round(alignment_score, 2)
            
        except Exception as e:
            logger.error(f"Error validating goal alignment: {e}")
            return 0.5
    
    async def _assess_task_quality(self, task: Dict[str, Any]) -> float:
        """Assess overall task quality and actionability"""
        try:
            quality_factors = []
            
            # 1. Name clarity and specificity
            name = task.get("name", "")
            if len(name) > 20 and any(word in name.lower() for word in ["collect", "create", "find", "generate"]):
                quality_factors.append(0.9)  # Action-oriented name
            elif len(name) > 10:
                quality_factors.append(0.7)  # Decent name
            else:
                quality_factors.append(0.3)  # Poor name
            
            # 2. Description completeness
            description = task.get("description", "")
            if len(description) > 100 and "specific" in description.lower():
                quality_factors.append(0.9)
            elif len(description) > 50:
                quality_factors.append(0.7)
            else:
                quality_factors.append(0.4)
            
            # 3. Success criteria clarity
            success_criteria = task.get("success_criteria", [])
            if len(success_criteria) >= 3:
                quality_factors.append(0.9)
            elif len(success_criteria) >= 1:
                quality_factors.append(0.7)
            else:
                quality_factors.append(0.3)
            
            # 4. Agent requirements specificity
            agent_reqs = task.get("agent_requirements", {})
            if agent_reqs.get("role") and agent_reqs.get("skills"):
                quality_factors.append(0.8)
            elif agent_reqs.get("role"):
                quality_factors.append(0.6)
            else:
                quality_factors.append(0.4)
            
            # 5. Estimated effort reasonableness
            effort = task.get("estimated_duration_hours", 0)
            if 0.5 <= effort <= 8:  # Reasonable effort range
                quality_factors.append(0.8)
            elif effort > 0:
                quality_factors.append(0.6)
            else:
                quality_factors.append(0.3)
            
            # Calculate overall quality score
            quality_score = sum(quality_factors) / len(quality_factors)
            return round(quality_score, 2)
            
        except Exception as e:
            logger.error(f"Error assessing task quality: {e}")
            return 0.5
    
    def _requires_manual_review(self, task: Dict[str, Any]) -> bool:
        """Determine if task requires manual PM review"""
        # Check for high-risk task types
        task_type = task.get("type", "")
        if task_type in self.manual_review_required_types:
            return True
        
        # Check for corrective tasks
        if task.get("is_corrective"):
            return True
        
        # Check for high effort tasks
        effort = task.get("estimated_duration_hours", 0)
        if effort > 6:  # More than 6 hours
            return True
        
        # Check for high contribution expectations
        contribution = task.get("contribution_expected", 0)
        if contribution > 20:  # Large numerical contribution
            return True
        
        return False
    
    def _generate_refinement_feedback(
        self, 
        task: Dict[str, Any], 
        goal_alignment: float, 
        quality: float
    ) -> List[str]:
        """Generate specific feedback for task refinement"""
        feedback = []
        
        if goal_alignment < 0.7:
            feedback.append("Improve goal alignment: Add specific numerical targets and clearer connection to workspace goals")
        
        if quality < 0.7:
            feedback.append("Enhance task quality: Add more specific success criteria and clearer deliverables")
        
        if not task.get("numerical_target"):
            feedback.append("Add numerical validation criteria for measurable completion")
        
        if len(task.get("success_criteria", [])) < 3:
            feedback.append("Add more detailed success criteria (minimum 3 required)")
        
        if not task.get("agent_requirements", {}).get("skills"):
            feedback.append("Specify required agent skills for optimal task assignment")
        
        return feedback
    
    async def _create_approved_tasks(self, approved_tasks: List[Dict]) -> List[Dict]:
        """Create approved tasks in database"""
        created_tasks = []
        
        for task_data in approved_tasks:
            try:
                # Prepare task for database
                db_task = self._prepare_task_for_db(task_data)
                
                # Insert task
                response = supabase.table("tasks").insert(db_task).execute()
                
                if response.data:
                    created_task = response.data[0]
                    created_tasks.append(created_task)
                    
                    logger.info(
                        f"✅ CREATED APPROVED TASK: {created_task['name']} "
                        f"(ID: {created_task['id']})"
                    )
                
            except Exception as e:
                logger.error(f"Error creating approved task: {e}")
        
        return created_tasks
    
    async def _handle_task_refinement(self, refinement_needed: List[Dict]) -> List[Dict]:
        """Handle tasks that need refinement"""
        refined_tasks = []
        
        for task_data in refinement_needed:
            try:
                # For now, log refinement needs
                # In future versions, could trigger AI-powered refinement
                logger.warning(
                    f"🔄 TASK REFINEMENT NEEDED: {task_data['name']} - "
                    f"Reasons: {'; '.join(task_data.get('refinement_reasons', []))}"
                )
                
                # TODO: Implement automatic refinement or human review workflow
                # For now, create refined task with feedback incorporated
                
            except Exception as e:
                logger.error(f"Error handling task refinement: {e}")
        
        return refined_tasks
    
    def _prepare_task_for_db(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare task data for database insertion"""
        return {
            "workspace_id": str(self.workspace_id),
            "name": task_data["name"],
            "description": task_data["description"],
            "status": TaskStatus.PENDING.value,
            "priority": self._map_priority(task_data.get("priority", 2)),
            "assigned_to_role": task_data.get("agent_requirements", {}).get("role", "specialist"),
            "estimated_effort_hours": task_data.get("estimated_duration_hours", 2),
            "deadline": (datetime.now() + timedelta(hours=task_data.get("deadline_hours", 48))).isoformat(),
            
            # Goal-driven fields
            "goal_id": task_data.get("goal_id"),
            "metric_type": task_data.get("metric_type"),
            "contribution_expected": task_data.get("contribution_expected"),
            "numerical_target": task_data.get("numerical_target"),
            "is_corrective": task_data.get("is_corrective", False),
            "success_criteria": task_data.get("success_criteria", []),
            
            # Context and metadata
            "context_data": {
                "generated_by": "goal_driven_task_planner",
                "approved_by": "goal_driven_project_manager",
                "review_scores": task_data.get("review_scores"),
                "agent_requirements": task_data.get("agent_requirements"),
                "completion_requirements": task_data.get("completion_requirements"),
                "research_sources": task_data.get("research_sources"),
                "validation_criteria": task_data.get("validation_criteria")
            }
        }
    
    def _map_priority(self, numeric_priority: int) -> str:
        """Map numeric priority to string"""
        if numeric_priority == 1:
            return "high"
        elif numeric_priority == 2:
            return "medium"
        else:
            return "low"
    
    def _generate_next_actions(
        self, 
        goal_analysis: Dict[str, Any], 
        created_tasks: List[Dict]
    ) -> List[str]:
        """Generate recommended next actions"""
        next_actions = []
        
        # Check for unmet high-priority goals
        priority_goals = goal_analysis.get("priority_goals", [])
        if priority_goals:
            next_actions.append(f"Monitor {len(priority_goals)} high-priority goals requiring attention")
        
        # Check for corrective tasks
        corrective_tasks = [t for t in created_tasks if t.get("is_corrective")]
        if corrective_tasks:
            next_actions.append(f"Immediate attention: {len(corrective_tasks)} corrective tasks created")
        
        # Overall progress check
        overall_progress = goal_analysis.get("overall_progress_pct", 0)
        if overall_progress < 50:
            next_actions.append("Accelerate goal achievement - overall progress below 50%")
        elif overall_progress > 80:
            next_actions.append("Consider setting stretch goals - nearing completion")
        
        # Task performance
        task_perf = goal_analysis.get("task_performance", {})
        completion_rate = task_perf.get("completion_rate_pct", 0)
        if completion_rate < 70:
            next_actions.append("Improve task completion rate - currently below 70%")
        
        return next_actions

# Singleton-style factory function
def create_goal_driven_pm(workspace_id: UUID) -> GoalDrivenProjectManager:
    """Create a Goal-Driven Project Manager for a workspace"""
    return GoalDrivenProjectManager(workspace_id)