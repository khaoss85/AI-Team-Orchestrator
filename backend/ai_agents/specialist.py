import logging
import os
from typing import List, Dict, Any, Optional, Union, Literal
from uuid import UUID
import json

# Importazione dal pacchetto installato
from agents import Agent as OpenAIAgent
from agents import Runner, ModelSettings, function_tool
# Rimuovi l'import HandoffConfig che non esiste
from agents import Handoff  # Usa Handoff invece di HandoffConfig

from models import (
    Agent as AgentModel,
    AgentStatus,
    AgentHealth,
    HealthStatus,
    Task,
    TaskStatus
)
from database import update_agent_status, update_task_status

logger = logging.getLogger(__name__)

class SpecialistAgent:
    """Specialist Agent that performs tasks in its area of expertise"""
    
    def __init__(self, agent_data: AgentModel):
        """
        Initialize a specialist agent with its configuration.
        
        Args:
            agent_data: The agent configuration from the database
        """
        self.agent_data = agent_data
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
            
        # Mapping of seniority to model
        self.seniority_model_map = {
            "junior": "gpt-4-turbo",
            "senior": "gpt-4.1-mini",
            "expert": "gpt-4.1"
        }
        
        # Initialize tools based on agent configuration
        self.tools = self._initialize_tools()
        
        # Create OpenAI Agent
        self.agent = self._create_agent()
        
    def _initialize_tools(self) -> List[Any]:
        """Initialize the tools for this agent based on its configuration"""
        # Base tools
        tools = [
            self.log_execution,
            self.update_health_status
        ]
        
        # Add tool creation if agent has permission
        if self.agent_data.can_create_tools:
            tools.append(self.create_custom_tool)
        
        # Add tools from agent configuration if any
        if self.agent_data.tools:
            # In a real implementation, we would dynamically create tools
            # based on the agent's configuration
            pass
            
        return tools
        
    def _create_agent(self) -> OpenAIAgent:
        """Create the OpenAI Agent with the appropriate configuration"""
        # Determine model based on seniority
        model = self.agent_data.llm_config.get("model") if self.agent_data.llm_config else None
        if not model:
            # Aggiornare questa mappatura per usare i nuovi modelli GPT-4.1
            self.seniority_model_map = {
                "junior": "gpt-4.1-nano",    # Il più economico per attività semplici
                "senior": "gpt-4.1-mini",    # Buon compromesso costo/prestazioni
                "expert": "gpt-4.1"          # Il migliore per attività complesse
            }
            model = self.seniority_model_map.get(self.agent_data.seniority, "gpt-4.1-mini")
            
        # Get other model settings
        temperature = self.agent_data.llm_config.get("temperature", 0.7) if self.agent_data.llm_config else 0.7
        
        # Create system prompt
        system_prompt = self.agent_data.system_prompt if self.agent_data.system_prompt else f"""
        You are a {self.agent_data.seniority} specialist in {self.agent_data.role}.
        
        Your responsibilities include:
        - {self.agent_data.description}
        - Working autonomously to complete tasks
        - Using available tools efficiently
        - Logging your progress
        
        Always think step by step and explain your reasoning.
        """
        
        # Add information about tool creation if agent has permission
        if self.agent_data.can_create_tools:
            system_prompt += """
            
            You can create custom tools when needed to accomplish your tasks more efficiently.
            When creating a tool:
            1. Think about what functionality would be most helpful
            2. Design the tool with a clear interface and purpose
            3. Implement it using Python code
            4. Test thoroughly before deploying
            """
        
        # Create the agent
        return OpenAIAgent(
            name=self.agent_data.name,
            instructions=system_prompt,
            model=model,
            model_settings=ModelSettings(
                temperature=temperature,
            ),
            tools=self.tools
        )
    
    @function_tool
    async def create_custom_tool(self, name: str, description: str, code: str) -> str:
        """
        Create a custom tool that can be used by agents.
        
        Args:
            name: The name of the tool function
            description: A description of what the tool does
            code: Python code implementing the tool (must be an async function)
            
        Returns:
            Information about the created tool (JSON string)
        """
        from tools.registry import tool_registry
        
        logger.info(f"Agent {self.agent_data.id} creating custom tool: {name}")
        
        try:
            # Register the tool with the registry
            tool_info = await tool_registry.register_tool(
                name=name,
                description=description,
                code=code,
                workspace_id=str(self.agent_data.workspace_id),
                created_by="agent"
            )
            
            # In a real implementation, we'd save this to the database
            from database import create_custom_tool
            await create_custom_tool(
                name=name,
                description=description,
                code=code,
                workspace_id=str(self.agent_data.workspace_id),
                created_by="agent"
            )
            
            result = {
                "success": True,
                "message": f"Tool {name} created successfully",
                "tool": tool_info
            }
            
            # Convertire il risultato in una stringa JSON
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Failed to create custom tool: {e}")
            result = {
                "success": False,
                "message": f"Failed to create tool: {str(e)}"
            }
            return json.dumps(result)
    
    @function_tool
    async def log_execution(self, step: str, details: str) -> bool:
        """
        Log the execution of a step.
        
        Args:
            step: The name/description of the execution step
            details: Details about the execution (JSON string)
            
        Returns:
            Boolean indicating success
        """
        try:
            # Parse details string to dictionary if it's a JSON string
            if isinstance(details, str):
                try:
                    details_dict = json.loads(details)
                except json.JSONDecodeError:
                    details_dict = {"raw_message": details}
            else:
                details_dict = {"raw_message": str(details)}
                
            logger.info(f"Agent {self.agent_data.id} - {step}: {json.dumps(details_dict)}")
            # In a real implementation, we would save this to the database
            return True
        except Exception as e:
            logger.error(f"Error in log_execution: {e}")
            return False
    
    @function_tool
    async def update_health_status(self, status: str, details: Optional[str] = None) -> bool:
        """
        Update the health status of the agent.
        
        Args:
            status: The health status (healthy, degraded, unhealthy)
            details: Optional details about the health status (JSON string)
            
        Returns:
            Boolean indicating success
        """
        try:
            # Parse details string to dictionary if provided
            details_dict = {}
            if details:
                try:
                    details_dict = json.loads(details)
                except json.JSONDecodeError:
                    details_dict = {"raw_message": details}
            
            health = AgentHealth(
                status=HealthStatus(status),
                details=details_dict
            )
            
            await update_agent_status(
                agent_id=str(self.agent_data.id),
                status=self.agent_data.status,
                health=health.model_dump()
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update agent health status: {e}")
            return False
    
    async def verify_capabilities(self) -> bool:
        """
        Verify that the agent has all the capabilities it needs.
        
        Returns:
            Boolean indicating if all capabilities are available
        """
        try:
            result = await Runner.run(
                self.agent,
                "Verify your capabilities and ensure you have all the tools you need."
            )
            
            # Update agent status to active if verification is successful
            await update_agent_status(
                agent_id=str(self.agent_data.id),
                status=AgentStatus.ACTIVE.value,
                health={
                    "status": HealthStatus.HEALTHY.value,
                    "last_update": None,
                    "details": {"verification": "passed"}
                }
            )
            
            return True
        except Exception as e:
            logger.error(f"Failed to verify agent capabilities: {e}")
            
            # Update agent status to error if verification fails
            await update_agent_status(
                agent_id=str(self.agent_data.id),
                status=AgentStatus.ERROR.value,
                health={
                    "status": HealthStatus.UNHEALTHY.value,
                    "last_update": None,
                    "details": {"verification": "failed", "error": str(e)}
                }
            )
            
            return False
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute a task assigned to this agent.
        
        Args:
            task: The task to execute
            
        Returns:
            Task result dictionary
        """
        try:
            # Update task status to in progress
            await update_task_status(
                task_id=str(task.id),
                status=TaskStatus.IN_PROGRESS.value
            )
            
            # Execute the task with the agent
            result = await Runner.run(
                self.agent,
                f"Execute the following task: {task.name}\n\nDetails: {task.description}"
            )
            
            # Process the result
            task_result = {
                "output": result.final_output,
                "status": "completed"
            }
            
            # Update task status to completed with result
            await update_task_status(
                task_id=str(task.id),
                status=TaskStatus.COMPLETED.value,
                result=task_result
            )
            
            return task_result
        except Exception as e:
            logger.error(f"Failed to execute task: {e}")
            
            # Update task status to failed
            error_result = {
                "error": str(e),
                "status": "failed"
            }
            
            await update_task_status(
                task_id=str(task.id),
                status=TaskStatus.FAILED.value,
                result=error_result
            )
            
            return error_result