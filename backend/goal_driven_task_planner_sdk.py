# backend/goal_driven_task_planner_sdk.py
"""
Goal-Driven Task Planner - SDK-Based Implementation
"""

import logging
from typing import Dict, List, Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field

# Import from our new foundation layer
from config.migration_config import is_sdk_migrated
from services.ai_provider_abstraction import ai_provider_manager

# Placeholder for the real Agent SDK
# from agents import Agent, Runner, AgentOutputSchema

logger = logging.getLogger(__name__)

# --- Pydantic Models for Structured Output ---

class TaskDefinition(BaseModel):
    name: str = Field(..., description="A short, actionable name for the task.")
    description: str = Field(..., description="A detailed description of the task and its purpose.")
    asset_type: str = Field(..., description="The type of asset this task will produce (e.g., document, list, code).")
    deliverable_format: str = Field(..., description="The format of the deliverable (e.g., markdown, csv, json).")

class TaskGenerationOutput(BaseModel):
    # Defines the structured output we expect from the AI
    tasks: List[TaskDefinition]
    reasoning: str = Field(..., description="The reasoning behind why these tasks were generated.")

# --- Agent Definition ---

# This is a placeholder for the real Agent SDK class
class Agent:
    def __init__(self, name, model, system_prompt, response_format):
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.response_format = response_format

class TaskGenerationAgent(Agent):
    """
    An agent specialized in generating tasks from goals using the Agent SDK.
    """
    def __init__(self):
        super().__init__(
            name="task_generator",
            model="gpt-4o-mini",
            system_prompt="You are an expert project manager who creates specific, actionable tasks for any industry, focusing on tangible assets.",
            response_format=TaskGenerationOutput
        )

# --- New SDK-Based Task Planner ---

class GoalDrivenTaskPlannerSDK:
    """
    A new version of the task planner that uses the Agent SDK for AI calls.
    """
    def __init__(self):
        self.task_generation_agent = TaskGenerationAgent()
        logger.info("SDK-Based Goal-Driven Task Planner initialized.")

    async def _generate_ai_driven_tasks(
        self,
        goal: Any, # Using Any for compatibility with old WorkspaceGoal
        gap: float,
        workspace_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generates tasks using the new TaskGenerationAgent and the AIProviderManager.
        """
        prompt = self._build_prompt(goal, gap, workspace_context)

        # Use the AIProviderManager to make the call
        # This will be routed to the SDK provider once the flag is enabled
        provider_type = 'openai_sdk' if is_sdk_migrated('task_generation_sdk') else 'openai_direct'
        
        # Real SDK call through the abstraction layer
        result_data = await ai_provider_manager.call_ai(
            provider_type=provider_type,
            agent=self.task_generation_agent,
            prompt=prompt,
            # Pass any other necessary parameters for the actual SDK call
        )

        # Use the compatibility shim to ensure the output is a dict
        output = TaskGenerationOutput(**result_data)
        
        return output.get('tasks', [])

    def _build_prompt(self, goal: Any, gap: float, workspace_context: Dict[str, Any]) -> str:
        """Builds the prompt for the AI task generation."""
        return f"""
        Generate tasks for the following goal:
        - Goal: {goal.description}
        - Metric: {goal.metric_type}
        - Gap: {gap} {goal.unit}
        - Workspace: {workspace_context.get('name')}
        - Industry: {workspace_context.get('description')}
        """

# Singleton instance
goal_driven_task_planner_sdk = GoalDrivenTaskPlannerSDK()
