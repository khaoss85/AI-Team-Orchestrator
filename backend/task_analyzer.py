import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID

from agents import Agent as OpenAIAgent, Runner, handoff, Handoff
from agents.exceptions import MaxTurnsExceeded
from pydantic import BaseModel

from models import Task, TaskStatus, Agent as AgentModel
from database import (
    create_task, list_agents, list_tasks,
    update_task_status, get_workspace
)

logger = logging.getLogger(__name__)

# Structured output per l'analisi
class TaskAnalysisOutput(BaseModel):
    """Structured output for task completion analysis"""
    requires_follow_up: bool
    confidence_score: float  # 0-1, quanto è sicuro che serve follow-up
    suggested_handoffs: List[Dict[str, str]]  # handoffs instead of tasks
    project_status: str
    reasoning: str
    next_phase: Optional[str] = None

class HandoffRecommendation(BaseModel):
    """Recommendation for a handoff to another agent"""
    target_agent_role: str
    context_summary: str
    expected_outcome: str
    priority: str = "medium"
    handoff_type: str  # "escalation", "delegation", "coordination"

class EnhancedTaskExecutor:
    """
    Enhanced task executor aligned with OpenAI Agents SDK best practices.
    Uses AI-driven analysis with structured outputs and handoffs.
    """
    
    def __init__(self):
        self.analysis_agent = self._create_analysis_agent()
        
    def _create_analysis_agent(self) -> OpenAIAgent:
        """Create a specialized agent for analyzing task results using SDK patterns"""
        
        return OpenAIAgent(
            name="TaskAnalysisExpert",
            instructions="""
            You are an expert AI project analyst specializing in determining logical next steps after task completion.
            
            Your primary job is to analyze completed tasks and determine IF and HOW work should continue.
            
            CRITICAL ANALYSIS PRINCIPLES:
            1. Not every completed task needs follow-up work
            2. Prefer HANDOFFS to existing agents over creating new tasks
            3. Consider the overall project goal and current state
            4. High confidence threshold - only suggest follow-ups when truly necessary
            
            HANDOFF vs TASK CREATION:
            - Use HANDOFFS when: passing work to existing specialists, escalating issues, coordinating results
            - Avoid creating new tasks unless absolutely critical for project completion
            
            COMPLETION RECOGNITION:
            - If a task has achieved its objective, mark requires_follow_up = false
            - Not every question or suggestion in the output means more work is needed
            - Value project completion over endless iteration
            """,
            model="gpt-4.1",  # Use most capable model for analysis
            output_type=TaskAnalysisOutput,  # Structured output
        )
    
    async def handle_task_completion(
        self,
        completed_task: Task,
        task_result: Dict[str, Any],
        workspace_id: str
    ):
        """
        Handle task completion with AI-driven analysis and handoff recommendations.
        Follows OpenAI Agents SDK best practices.
        """
        
        from executor import task_executor
        if workspace_id in task_executor.workspace_auto_generation_paused:
            logger.info(f"Auto-generation paused for workspace {workspace_id}, skipping task analysis")
            return
    
        try:
            # STEP 1: Pre-filter for obviously failed or problematic tasks
            if not self._should_analyze_task(completed_task, task_result):
                logger.info(f"Task {completed_task.id} filtered out from auto-analysis")
                return
            
            # STEP 2: Get current workspace and agent context
            workspace_context = await self._gather_workspace_context(workspace_id)
            
            # STEP 3: Perform AI-driven analysis with structured output
            analysis_result = await self._analyze_task_with_ai(
                completed_task=completed_task,
                task_result=task_result,
                workspace_context=workspace_context
            )
            
            # STEP 4: Act on analysis results using handoffs (not task creation)
            if analysis_result.requires_follow_up and analysis_result.confidence_score > 0.7:
                await self._execute_handoff_recommendations(
                    analysis_result=analysis_result,
                    completed_task=completed_task,
                    workspace_id=workspace_id
                )
            else:
                logger.info(f"Task {completed_task.id} analysis: no follow-up needed (confidence: {analysis_result.confidence_score})")
                
        except Exception as e:
            logger.error(f"Error in enhanced task completion handling: {e}")
    
    def _should_analyze_task(self, completed_task: Task, task_result: Dict[str, Any]) -> bool:
        """Pre-filter to avoid analyzing tasks that shouldn't trigger follow-ups"""
        
         # FILTER 1: Only analyze successfully completed tasks
        if task_result.get("status") != "completed":
            return False

        # FILTER 2: Skip handoff tasks to prevent infinite loops
        if "handoff" in completed_task.name.lower():
            return False

        # FILTER 3: Skip initialization tasks to prevent loops
        if "initialization" in completed_task.name.lower():
            return False

        # FILTER 4: Skip analysis tasks to prevent loops
        if "analysis" in completed_task.name.lower():
            return False

        # FILTER 5: Skip data collection tasks
        if "data collection" in completed_task.name.lower():
            return False
        
            
        # FILTER 3: Check for execution success flag
        if not task_result.get("execution_success", True):
            return False
        
        # FILTER 4: Skip if max_turns reached without meaningful output
        if task_result.get("max_turns_reached", False):
            output_length = len(str(task_result.get("output", "")))
            if output_length < 200:  # Too short output suggests incomplete work
                return False
        
        # FILTER 5: Avoid analyzing trivial or administrative tasks
        trivial_keywords = ["update", "log", "record", "note", "acknowledge"]
        if any(keyword in completed_task.name.lower() for keyword in trivial_keywords):
            return False
        
        return True
    
    async def _gather_workspace_context(self, workspace_id: str) -> Dict[str, Any]:
        """Gather comprehensive workspace context for analysis"""
        
        workspace = await get_workspace(workspace_id)
        agents = await list_agents(workspace_id)
        all_tasks = await list_tasks(workspace_id)
        
        # Calculate project statistics
        completed_tasks = [t for t in all_tasks if t.get("status") == "completed"]
        pending_tasks = [t for t in all_tasks if t.get("status") == "pending"]
        
        return {
            "workspace_goal": workspace.get("goal", ""),
            "total_tasks": len(all_tasks),
            "completed_tasks": len(completed_tasks), 
            "pending_tasks": len(pending_tasks),
            "available_agents": [
                {"id": a["id"], "name": a["name"], "role": a["role"], "seniority": a["seniority"]}
                for a in agents if a.get("status") == "active"
            ],
            "recent_completions": [
                {"name": t["name"], "result": t.get("result", {})}
                for t in completed_tasks[-5:]
            ]
        }
    
    async def _analyze_task_with_ai(
        self,
        completed_task: Task,
        task_result: Dict[str, Any],
        workspace_context: Dict[str, Any]
    ) -> TaskAnalysisOutput:
        """Use AI to analyze task completion and determine next steps"""
        
        # Construct comprehensive analysis prompt
        analysis_prompt = f"""
        Analyze this completed task and determine if follow-up work is needed:
        
        COMPLETED TASK:
        Name: {completed_task.name}
        Description: {completed_task.description}
        
        TASK OUTPUT:
        {task_result.get('output', 'No output available')}
        
        WORKSPACE CONTEXT:
        Goal: {workspace_context.get('workspace_goal', 'Not specified')}
        Progress: {workspace_context.get('completed_tasks', 0)}/{workspace_context.get('total_tasks', 0)} tasks completed
        Pending Tasks: {workspace_context.get('pending_tasks', 0)}
        
        AVAILABLE AGENTS:
        {self._format_available_agents(workspace_context.get('available_agents', []))}
        
        RECENT COMPLETIONS:
        {self._format_recent_completions(workspace_context.get('recent_completions', []))}
        
        ANALYSIS INSTRUCTIONS:
        1. Determine if this task truly needs follow-up (be conservative)
        2. If follow-up is needed, recommend HANDOFFS to existing agents, not new tasks
        3. Consider the overall project goal and current progress
        4. Provide a confidence score (0-1) for your recommendation
        5. Focus on project completion rather than endless iteration
        
        Remember: Not every completed task needs follow-up. Value completion over continuation.
        """
        
        try:
            result = await Runner.run(self.analysis_agent, analysis_prompt)
            
            # The agent returns structured TaskAnalysisOutput
            if isinstance(result.final_output, TaskAnalysisOutput):
                return result.final_output
            else:
                # Fallback if structured output fails
                logger.warning("AI analysis didn't return structured output, using conservative fallback")
                return TaskAnalysisOutput(
                    requires_follow_up=False,
                    confidence_score=0.0,
                    suggested_handoffs=[],
                    project_status="analysis_failed",
                    reasoning="Failed to produce structured analysis"
                )
        except Exception as e:
            logger.error(f"Error in AI task analysis: {e}")
            return TaskAnalysisOutput(
                requires_follow_up=False,
                confidence_score=0.0,
                suggested_handoffs=[],
                project_status="analysis_error",
                reasoning=f"Analysis failed: {str(e)}"
            )
    
    def _format_available_agents(self, agents: List[Dict]) -> str:
        """Format agent list for analysis prompt"""
        if not agents:
            return "No active agents available"
        
        formatted = []
        for agent in agents:
            formatted.append(f"- {agent['name']} ({agent['role']}, {agent['seniority']})")
        return "\n".join(formatted)
    
    def _format_recent_completions(self, completions: List[Dict]) -> str:
        """Format recent completions for context"""
        if not completions:
            return "No recent completions"
        
        formatted = []
        for comp in completions:
            output_summary = str(comp.get('result', {}).get('output', ''))[:100] + "..."
            formatted.append(f"- {comp['name']}: {output_summary}")
        return "\n".join(formatted)
    
    async def _execute_handoff_recommendations(
        self,
        analysis_result: TaskAnalysisOutput,
        completed_task: Task,
        workspace_id: str
    ):
        """Execute handoff recommendations instead of creating new tasks"""
        
        logger.info(f"Executing handoff recommendations for task {completed_task.id}")
        logger.info(f"Analysis reasoning: {analysis_result.reasoning}")
        
        agents = await list_agents(workspace_id)
        agent_by_role = {agent["role"]: agent for agent in agents}
        
        executed_handoffs = 0
        
        for handoff_rec in analysis_result.suggested_handoffs:
            target_role = handoff_rec.get("target_agent_role", "")
            context = handoff_rec.get("context_summary", "")
            expected_outcome = handoff_rec.get("expected_outcome", "")
            handoff_type = handoff_rec.get("handoff_type", "delegation")
            
            # Find the target agent
            target_agent = self._find_agent_by_role(agents, target_role)
            
            if target_agent:
                # Create a handoff task (this is the bridge until we fully implement SDK handoffs)
                handoff_description = f"""
                HANDOFF FROM COMPLETED TASK: {completed_task.name}
                TYPE: {handoff_type}
                
                CONTEXT:
                {context}
                
                EXPECTED OUTCOME:
                {expected_outcome}
                
                ORIGINAL TASK OUTPUT:
                {str(completed_task.result)[:500] if hasattr(completed_task, 'result') else 'No output available'}
                
                INSTRUCTIONS:
                Based on the context above, {expected_outcome.lower()}
                This is a handoff, not a new task creation. Focus on the specific expected outcome.
                """
                
                # Create the handoff task
                handoff_task = await create_task(
                    workspace_id=workspace_id,
                    agent_id=target_agent["id"],
                    name=f"Handoff: {handoff_rec.get('expected_outcome', 'Follow-up')}",
                    description=handoff_description,
                    status=TaskStatus.PENDING.value
                )
                
                if handoff_task:
                    executed_handoffs += 1
                    logger.info(f"Created handoff task {handoff_task['id']} for agent {target_agent['name']}")
                else:
                    logger.error(f"Failed to create handoff task for {target_agent['name']}")
            else:
                logger.warning(f"No agent found for role '{target_role}' in handoff recommendation")
        
        logger.info(f"Executed {executed_handoffs}/{len(analysis_result.suggested_handoffs)} handoff recommendations")
    
    def _find_agent_by_role(self, agents: List[Dict], target_role: str) -> Optional[Dict]:
        """Find agent by role with fuzzy matching"""
        target_role_lower = target_role.lower()
        
        # Exact role match
        for agent in agents:
            if agent.get("role", "").lower() == target_role_lower:
                return agent
        
        # Fuzzy match - role contains target or vice versa
        for agent in agents:
            agent_role = agent.get("role", "").lower()
            if target_role_lower in agent_role or agent_role in target_role_lower:
                return agent
        
        # Fuzzy match by keywords
        target_keywords = target_role_lower.split()
        for agent in agents:
            agent_role = agent.get("role", "").lower()
            if any(keyword in agent_role for keyword in target_keywords):
                return agent
        
        return None