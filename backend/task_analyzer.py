# backend/task_analyzer.py - Fixed version with lazy imports

import logging
import json
import re
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
import asyncio

from agents import Agent as OpenAIAgent
from agents import Runner, ModelSettings, function_tool
from agents import AgentOutputSchema
from pydantic import BaseModel

from models import Task, TaskStatus, Agent as AgentModel
from database import create_task, list_agents, list_tasks

logger = logging.getLogger(__name__)

# Remove the import from top - we'll import it when needed
# from human_feedback_manager import human_feedback_manager, FeedbackRequestType, FeedbackStatus

class TaskAnalysisResult(BaseModel):
    """Results from analyzing a completed task"""
    requires_follow_up: bool
    suggested_tasks: List[Dict[str, Any]]
    handoffs_needed: List[Dict[str, Any]]
    project_status: str
    next_phase: Optional[str] = None

class WorkflowStep(BaseModel):
    """Represents a step in the workflow"""
    step_name: str
    target_role: str
    description: str
    dependencies: List[str]
    priority: str = "medium"

class AutoTaskGenerator:
    """
    Analyzes completed tasks and automatically generates follow-up tasks
    based on the results and project goals.
    """
    
    def __init__(self):
        self.analysis_agent = self._create_analysis_agent()
    
    def _create_analysis_agent(self) -> OpenAIAgent:
        """Create a specialized agent for analyzing task results"""
        
        # Create AgentOutputSchema for TaskAnalysisResult
        task_analysis_output_schema = AgentOutputSchema(
            output_type=TaskAnalysisResult,
            strict_json_schema=False
        )
        
        return OpenAIAgent(
            name="TaskResultAnalyzer",
            instructions="""
            You are a specialized AI agent whose job is to analyze completed tasks and determine what should happen next in a project.
            
            Your responsibilities:
            1. Analyze the results of completed tasks
            2. Determine if follow-up tasks are needed
            3. Identify which specialists should handle subsequent work
            4. Suggest specific, actionable next steps
            5. Maintain the overall project timeline and goals
            
            When analyzing a task result:
            - Look for explicit mentions of next steps or delegations
            - Identify gaps that need to be filled
            - Consider the overall project flow
            - Determine priorities and dependencies
            
            Always provide structured output with specific recommendations.
            """, 
            model="gpt-4.1",
            model_settings=ModelSettings(temperature=0.2),
            output_type=task_analysis_output_schema
        )
    
    async def analyze_task_result(
        self, 
        completed_task: Task,
        task_result: Dict[str, Any],
        workspace_id: str,
        project_context: Optional[str] = None
    ) -> TaskAnalysisResult:
        """
        Analyze the result of a completed task and determine next steps.
        """
        try:
            # Get current task list for context
            all_tasks = await list_tasks(workspace_id)
            
            # Get available agents for delegation
            agents = await list_agents(workspace_id)
            
            # Create analysis prompt
            analysis_prompt = f"""
            Analyze the following completed task and determine what should happen next:
            
            COMPLETED TASK:
            Name: {completed_task.name}
            Description: {completed_task.description}
            
            TASK RESULT:
            {json.dumps(task_result, indent=2)}
            
            PROJECT CONTEXT:
            {project_context or "No additional context provided"}
            
            AVAILABLE AGENTS:
            {json.dumps([{"name": a["name"], "role": a["role"]} for a in agents], indent=2)}
            
            EXISTING TASKS:
            {json.dumps([{"name": t["name"], "status": t["status"], "agent_id": t.get("agent_id")} for t in all_tasks], indent=2)}
            
            Based on this information:
            1. Determine if follow-up tasks are needed
            2. Identify specific tasks that should be created
            3. Assign each task to the most appropriate agent role
            4. Indicate any handoffs that are required
            5. Assess the overall project status
            
            Focus on extracting actionable next steps from the completed task's output.
            """
            
            result = await Runner.run(self.analysis_agent, analysis_prompt)
            
            # Ensure we got a structured result
            if isinstance(result.final_output, TaskAnalysisResult):
                return result.final_output
            else:
                # Fallback parsing if structured output failed
                return self._parse_analysis_result(result.final_output)
            
        except Exception as e:
            logger.error(f"Error analyzing task result: {e}")
            # Return minimal result on error
            return TaskAnalysisResult(
                requires_follow_up=False,
                suggested_tasks=[],
                handoffs_needed=[],
                project_status="unknown"
            )
    
    def _parse_analysis_result(self, raw_output: str) -> TaskAnalysisResult:
        """Parse unstructured analysis output as fallback"""
        try:
            # Try to extract JSON if present
            json_match = re.search(r'(\{.*\})', raw_output, re.DOTALL)
            if json_match:
                return TaskAnalysisResult.model_validate_json(json_match.group(1))
            
            # Otherwise create minimal result
            return TaskAnalysisResult(
                requires_follow_up="follow" in raw_output.lower(),
                suggested_tasks=[],
                handoffs_needed=[],
                project_status="analysis_failed"
            )
        except Exception as e:
            logger.error(f"Failed to parse analysis result: {e}")
            return TaskAnalysisResult(
                requires_follow_up=False,
                suggested_tasks=[],
                handoffs_needed=[],
                project_status="parse_error"
            )
    
    async def create_follow_up_tasks(
        self,
        analysis_result: TaskAnalysisResult,
        workspace_id: str,
        completed_task_id: str
    ) -> List[str]:
        """
        Create the follow-up tasks based on the analysis result.
        
        Returns:
            List of created task IDs
        """
        created_tasks = []
        
        try:
            # Get available agents for assignment
            agents = await list_agents(workspace_id)
            agent_by_role = {agent["role"]: agent for agent in agents}
            
            # Create suggested tasks
            for task_info in analysis_result.suggested_tasks:
                target_role = task_info.get("target_role", "")
                
                # Find appropriate agent
                target_agent = None
                for role, agent in agent_by_role.items():
                    if target_role.lower() in role.lower():
                        target_agent = agent
                        break
                
                if target_agent:
                    # Create the task
                    task_data = await create_task(
                        workspace_id=workspace_id,
                        agent_id=target_agent["id"],
                        name=task_info.get("name", "Follow-up Task"),
                        description=f"""
                        AUTO-GENERATED FOLLOW-UP TASK
                        
                        {task_info.get("description", "")}
                        
                        Created based on results from task: {completed_task_id}
                        Priority: {task_info.get("priority", "medium")}
                        Dependencies: {task_info.get("dependencies", [])}
                        """,
                        status=TaskStatus.PENDING.value
                    )
                    
                    if task_data:
                        created_tasks.append(task_data["id"])
                        logger.info(f"Created follow-up task {task_data['id']} for agent {target_agent['name']}")
                else:
                    logger.warning(f"No agent found for role '{target_role}' when creating follow-up task")
            
            # Handle handoffs
            for handoff_info in analysis_result.handoffs_needed:
                # Create task with handoff context
                target_role = handoff_info.get("target_role", "")
                target_agent = None
                
                for role, agent in agent_by_role.items():
                    if target_role.lower() in role.lower():
                        target_agent = agent
                        break
                
                if target_agent:
                    handoff_task = await create_task(
                        workspace_id=workspace_id,
                        agent_id=target_agent["id"],
                        name=f"Handoff: {handoff_info.get('name', 'Continuation Task')}",
                        description=f"""
                        HANDOFF TASK
                        
                        {handoff_info.get("description", "")}
                        
                        Context from previous task: {completed_task_id}
                        Priority: {handoff_info.get("priority", "medium")}
                        """,
                        status=TaskStatus.PENDING.value
                    )
                    
                    if handoff_task:
                        created_tasks.append(handoff_task["id"])
                        logger.info(f"Created handoff task {handoff_task['id']} for agent {target_agent['name']}")
            
            return created_tasks
            
        except Exception as e:
            logger.error(f"Error creating follow-up tasks: {e}")
            return created_tasks
    
    async def extract_project_plan(self, task_result: Dict[str, Any]) -> List[WorkflowStep]:
        """
        Extract a structured project plan from a planning task result.
        Useful for project management tasks.
        """
        try:
            # Create a specialized extraction prompt
            extraction_prompt = f"""
            Extract a structured workflow from the following task result:
            
            {json.dumps(task_result, indent=2)}
            
            Look for:
            1. Phases or steps mentioned
            2. Specific roles or specialists needed
            3. Task dependencies
            4. Priorities and timelines
            
            Return a list of workflow steps with:
            - step_name: Clear name for the step
            - target_role: Role/specialist needed
            - description: What needs to be done
            - dependencies: List of prerequisite steps
            - priority: low/medium/high
            """
            
            extractor_agent = OpenAIAgent(
                name="WorkflowExtractor",
                instructions="Extract structured workflow steps from project planning outputs.",
                model="gpt-4.1-mini",
                output_type=List[WorkflowStep]
            )
            
            result = await Runner.run(extractor_agent, extraction_prompt)
            
            if isinstance(result.final_output, list):
                return result.final_output
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error extracting project plan: {e}")
            return []

# Integration with TaskExecutor
class EnhancedTaskExecutor:
    """
    Enhanced task executor that automatically creates follow-up tasks
    based on completed task results.
    """
    
    def __init__(self):
        self.task_generator = AutoTaskGenerator()
    
    async def handle_task_completion(
        self,
        completed_task: Task,
        task_result: Dict[str, Any],
        workspace_id: str
    ):
        """
        Handle task completion with automatic follow-up generation and human feedback.
        """
        try:
            # Skip auto-generation for handoff tasks to avoid loops
            if "handoff" in completed_task.name.lower():
                logger.info(f"Skipping auto-generation for handoff task {completed_task.id}")
                return
            
            # Get project context if this is a planning task
            project_context = None
            if "planning" in completed_task.name.lower() or "initialization" in completed_task.name.lower():
                project_context = f"""
                This is a project planning/initialization task.
                The results likely contain a project plan that should be broken down into specific tasks.
                Look for phases, delegations, and actionable items that need to be assigned to specialists.
                """
            
            # Analyze the completed task
            analysis_result = await self.task_generator.analyze_task_result(
                completed_task=completed_task,
                task_result=task_result,
                workspace_id=workspace_id,
                project_context=project_context
            )
            
            logger.info(f"Analysis result for task {completed_task.id}: {analysis_result.project_status}")
            
            # Check if human feedback is needed - use lazy import
            if await self._requires_human_feedback(analysis_result, workspace_id):
                await self._request_human_feedback_for_analysis(
                    analysis_result, completed_task, workspace_id
                )
                return
            
            # Create follow-up tasks if needed
            if analysis_result.requires_follow_up:
                created_tasks = await self.task_generator.create_follow_up_tasks(
                    analysis_result=analysis_result,
                    workspace_id=workspace_id,
                    completed_task_id=str(completed_task.id)
                )
                
                if created_tasks:
                    logger.info(f"Created {len(created_tasks)} follow-up tasks for workspace {workspace_id}")
                else:
                    logger.warning(f"No follow-up tasks created despite analysis indicating they were needed")
            else:
                logger.info(f"No follow-up tasks needed for task {completed_task.id}")
            
        except Exception as e:
            logger.error(f"Error handling task completion: {e}")
    
    async def _requires_human_feedback(
        self, 
        analysis_result: TaskAnalysisResult,
        workspace_id: str
    ) -> bool:
        """Determine if human feedback is required"""
        # Conditions that require human feedback
        if "manual intervention" in analysis_result.project_status.lower():
            return True
        if "at risk" in analysis_result.project_status.lower():
            return True
        if analysis_result.requires_follow_up and len(analysis_result.suggested_tasks) > 3:
            return True
        if any(task.get("priority") == "high" for task in analysis_result.suggested_tasks):
            return True
        
        return False
    
    async def _request_human_feedback_for_analysis(
        self,
        analysis_result: TaskAnalysisResult,
        completed_task: Task,
        workspace_id: str
    ):
        """Request human feedback for task analysis results - with lazy import"""
        # Lazy import to avoid circular dependency
        from human_feedback_manager import human_feedback_manager, FeedbackRequestType, FeedbackStatus
        
        proposed_actions = []
        
        for task_suggestion in analysis_result.suggested_tasks:
            proposed_actions.append({
                "type": "create_task",
                "task_name": task_suggestion.get("name"),
                "description": task_suggestion.get("description"),
                "target_role": task_suggestion.get("target_role"),
                "priority": task_suggestion.get("priority")
            })
        
        for handoff in analysis_result.handoffs_needed:
            proposed_actions.append({
                "type": "handoff",
                "description": handoff.get("description"),
                "target_role": handoff.get("target_role")
            })
        
        context = {
            "completed_task_id": str(completed_task.id),
            "completed_task_name": completed_task.name,
            "analysis_status": analysis_result.project_status,
            "next_phase": analysis_result.next_phase
        }
        
        async def response_callback(request, response):
            return await self._handle_feedback_response(
                request, response, analysis_result, workspace_id
            )
        
        await human_feedback_manager.request_feedback(
            workspace_id=workspace_id,
            request_type=FeedbackRequestType.TASK_APPROVAL,
            title=f"Approve Follow-up Actions for {completed_task.name}",
            description=f"""
            Task "{completed_task.name}" has been completed with status: {analysis_result.project_status}
            
            The system suggests the following follow-up actions:
            - {len(analysis_result.suggested_tasks)} new tasks
            - {len(analysis_result.handoffs_needed)} handoffs
            
            Please review and approve or modify these suggestions.
            """,
            proposed_actions=proposed_actions,
            context=context,
            priority="high" if "at risk" in analysis_result.project_status.lower() else "medium",
            timeout_hours=6,  # Shorter timeout for critical decisions
            response_callback=response_callback
        )
    
    async def _handle_feedback_response(
        self,
        request,  # FeedbackRequest type - avoid import
        response: Dict[str, Any],
        analysis_result: TaskAnalysisResult,
        workspace_id: str
    ):
        """Handle human feedback response"""
        if response.get("approved", False):
            logger.info(f"Human approved follow-up actions for request {request.id}")
            
            # Apply any modifications from human feedback
            modified_actions = response.get("modifications", [])
            if modified_actions:
                await self._apply_action_modifications(modified_actions, analysis_result)
            
            # Execute the approved actions
            await self._execute_follow_up_with_tracking(
                analysis_result, None, workspace_id
            )
        else:
            logger.info(f"Human rejected follow-up actions for request {request.id}")
            # Handle rejection - maybe create a different set of tasks based on feedback
            rejection_reason = response.get("reason", "No reason provided")
            await self._handle_action_rejection(rejection_reason, analysis_result, workspace_id)
    
    async def _apply_action_modifications(
        self,
        modifications: List[Dict[str, Any]],
        analysis_result: TaskAnalysisResult
    ):
        """Apply human modifications to the suggested actions"""
        for mod in modifications:
            action_id = mod.get("action_id")
            changes = mod.get("changes", {})
            
            if action_id < len(analysis_result.suggested_tasks):
                task_suggestion = analysis_result.suggested_tasks[action_id]
                task_suggestion.update(changes)
    
    async def _execute_follow_up_with_tracking(
        self,
        analysis_result: TaskAnalysisResult,
        completed_task: Optional[Task],
        workspace_id: str
    ):
        """Execute follow-up actions with tracking"""
        created_tasks = await self.task_generator.create_follow_up_tasks(
            analysis_result=analysis_result,
            workspace_id=workspace_id,
            completed_task_id=str(completed_task.id) if completed_task else ""
        )
        
        if created_tasks:
            logger.info(f"Created {len(created_tasks)} follow-up tasks for workspace {workspace_id}")
    
    async def _handle_action_rejection(
        self,
        rejection_reason: str,
        analysis_result: TaskAnalysisResult,
        workspace_id: str
    ):
        """Handle when human rejects suggested actions"""
        logger.info(f"Handling action rejection: {rejection_reason}")
        # Could implement alternative logic based on rejection reason
        # For example, create a simpler set of tasks or escalate to different agents

# Usage example in the main task executor
async def integrate_auto_generation():
    """Example of how to integrate this with the existing TaskExecutor"""
    # This would be added to the TaskExecutor.execute_task_with_tracking method
    
    # After task completion:
    if task_result.get("status") == "completed":
        enhanced_executor = EnhancedTaskExecutor()
        await enhanced_executor.handle_task_completion(
            completed_task=task_object,
            task_result=task_result,
            workspace_id=workspace_id
        )