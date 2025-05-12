import logging
import os
from typing import List, Dict, Any, Optional, Union, Literal
from uuid import UUID
import json

# Importazione dal pacchetto installato
from agents import Agent as OpenAIAgent
from agents import Runner, ModelSettings, function_tool
from agents import Handoff, handoff, WebSearchTool, FileSearchTool
from agents import input_guardrail, output_guardrail, GuardrailFunctionOutput
from agents import TResponseInputItem, RunContextWrapper
from pydantic import BaseModel, Field

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

# ==============================================================================
# OUTPUT STRUTTURATI
# ==============================================================================

class TaskExecutionOutput(BaseModel):
    """Output strutturato per l'esecuzione di task"""
    task_id: str
    status: Literal["completed", "failed", "requires_handoff"]
    summary: str
    detailed_results: Dict[str, Any]
    next_steps: Optional[List[str]] = None
    suggested_handoff: Optional[str] = None
    resources_consumed: Optional[Dict[str, Union[int, float]]] = None

class CapabilityVerificationOutput(BaseModel):
    """Output strutturato per la verifica delle capacità"""
    verification_status: Literal["passed", "failed"]
    available_tools: List[str]
    missing_requirements: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None

class ToolCreationOutput(BaseModel):
    """Output strutturato per la creazione di tool"""
    success: bool
    tool_name: str
    tool_id: Optional[str] = None
    error_message: Optional[str] = None
    validation_results: Optional[Dict[str, Any]] = None

# ==============================================================================
# GUARDRAIL
# ==============================================================================

class BudgetMonitoringData(BaseModel):
    """Dati per il monitoraggio del budget"""
    estimated_cost: float
    budget_warning_threshold: float

@input_guardrail
async def budget_monitoring_guardrail(
    ctx: RunContextWrapper,
    agent: OpenAIAgent,
    input: Union[str, List[TResponseInputItem]]
) -> GuardrailFunctionOutput:
    """Guardrail per monitorare l'uso del budget"""
    try:
        # Stima il costo basato sulla lunghezza dell'input
        input_text = input if isinstance(input, str) else str(input)
        estimated_tokens = len(input_text.split()) * 1.3  # Stima approssimativa
        estimated_cost = estimated_tokens * 0.00003  # Costo per token (esempio)
        
        # Controlla se supera la soglia
        budget_limit = 10.0  # EUR - dovrebbe essere configurabile
        warning_threshold = budget_limit * 0.8
        
        return GuardrailFunctionOutput(
            output_info={
                "estimated_cost": estimated_cost,
                "budget_usage": (estimated_cost / budget_limit) * 100
            },
            tripwire_triggered=estimated_cost > warning_threshold
        )
    except Exception as e:
        logger.error(f"Error in budget guardrail: {e}")
        return GuardrailFunctionOutput(
            output_info={"error": str(e)},
            tripwire_triggered=False
        )

@output_guardrail
async def quality_assurance_guardrail(
    ctx: RunContextWrapper,
    agent: OpenAIAgent,
    output: Any
) -> GuardrailFunctionOutput:
    """Guardrail per verifica qualità output"""
    try:
        # Verifica la qualità dell'output
        quality_score = 1.0
        issues = []
        
        if hasattr(output, 'status') and output.status == "failed":
            quality_score -= 0.5
            issues.append("Task marked as failed")
        
        if hasattr(output, 'summary') and len(output.summary) < 20:
            quality_score -= 0.2
            issues.append("Summary too short")
        
        return GuardrailFunctionOutput(
            output_info={
                "quality_score": quality_score,
                "issues_found": issues
            },
            tripwire_triggered=quality_score < 0.6
        )
    except Exception as e:
        logger.error(f"Error in quality guardrail: {e}")
        return GuardrailFunctionOutput(
            output_info={"error": str(e)},
            tripwire_triggered=False
        )

# ==============================================================================
# SPECIALIST AGENT
# ==============================================================================

class SpecialistAgent:
    """Advanced Specialist Agent with structured outputs and guardrails"""
    
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
        
        # Mapping of seniority to model (aggiornato per GPT-4.1)
        self.seniority_model_map = {
            "junior": "gpt-4-turbo",      # Più economico per attività base
            "senior": "gpt-4.1-mini",     # Buon compromesso costo/prestazioni
            "expert": "gpt-4.1"           # Migliore per attività complesse
        }
        
        # Initialize tools based on agent configuration
        self.tools = self._initialize_tools()
        
        # Initialize handoffs
        self.handoffs = self._initialize_handoffs()
        
        # Create OpenAI Agent
        self.agent = self._create_agent()
    
    def _initialize_tools(self) -> List[Any]:
        """Initialize the tools for this agent based on its configuration"""
        # Base tools
        tools = [
            self.log_execution,
            self.update_health_status,
            self.report_progress,
        ]
        
        # Add tool creation if agent has permission
        if self.agent_data.can_create_tools:
            tools.append(self.create_custom_tool)
        
        # Add native OpenAI tools
        tools.extend([
            WebSearchTool(),  # Tool nativo per ricerca web
        ])
        
        # Add FileSearchTool if agent has vector store access
        if hasattr(self.agent_data, 'vector_store_ids') and self.agent_data.vector_store_ids:
            tools.append(FileSearchTool(
                max_num_results=5,
                vector_store_ids=self.agent_data.vector_store_ids
            ))
        
        # Add tools from agent configuration
        if self.agent_data.tools:
            # Convert tools configuration to actual function tools
            for tool_config in self.agent_data.tools:
                if isinstance(tool_config, dict) and 'name' in tool_config:
                    # Qui potresti implementare la logica per creare tool dinamici
                    # basati sulla configurazione
                    pass
        
        return tools
    
    def _initialize_handoffs(self) -> List[Handoff]:
        """Initialize handoffs for this agent"""
        handoffs = []
        
        # Example: Create a handoff to a senior agent for escalation
        if self.agent_data.seniority == "junior":
            escalation_handoff = handoff(
                agent=None,  # Will be set dynamically
                on_handoff=self._on_escalation_handoff,
                input_type=BudgetMonitoringData,
                tool_name_override="escalate_to_senior",
                tool_description_override="Escalate complex issues to a senior agent"
            )
            handoffs.append(escalation_handoff)
        
        return handoffs
    
    async def _on_escalation_handoff(
        self,
        ctx: RunContextWrapper,
        input_data: BudgetMonitoringData
    ):
        """Callback per gestire l'escalation handoff"""
        logger.info(f"Agent {self.agent_data.id} escalating: {input_data}")
        # Implementa logica di escalation (notifiche, logging, ecc.)
    
    def _create_agent(self) -> OpenAIAgent:
        """Create the OpenAI Agent with the appropriate configuration"""
        # Determine model based on seniority
        model = self.agent_data.llm_config.get("model") if self.agent_data.llm_config else None
        if not model:
            model = self.seniority_model_map.get(self.agent_data.seniority, "gpt-4.1-mini")
        
        # Get other model settings
        temperature = self.agent_data.llm_config.get("temperature", 0.7) if self.agent_data.llm_config else 0.7
        
        # Create enhanced system prompt
        system_prompt = self._create_system_prompt()
        
        # Configure guardrails
        input_guardrails = [budget_monitoring_guardrail]
        output_guardrails = [quality_assurance_guardrail]
        
        # Create the agent with advanced features
        return OpenAIAgent(
            name=self.agent_data.name,
            instructions=system_prompt,
            model=model,
            model_settings=ModelSettings(
                temperature=temperature,
                top_p=self.agent_data.llm_config.get("top_p", 1.0) if self.agent_data.llm_config else 1.0,
                max_tokens=self.agent_data.llm_config.get("max_tokens", 4000) if self.agent_data.llm_config else 4000
            ),
            tools=self.tools,
            handoffs=self.handoffs,
            input_guardrails=input_guardrails,
            output_guardrails=output_guardrails,
            output_type=TaskExecutionOutput  # Output strutturato
        )
    
    def _create_system_prompt(self) -> str:
        """Create an enhanced system prompt"""
        base_prompt = self.agent_data.system_prompt if self.agent_data.system_prompt else f"""
        You are a {self.agent_data.seniority} AI agent specializing in {self.agent_data.role}.
        
        Your core responsibilities:
        - {self.agent_data.description}
        - Execute assigned tasks with precision and efficiency
        - Monitor your resource usage and budget constraints
        - Collaborate effectively with other agents
        - Maintain high-quality standards in all outputs
        
        When executing tasks:
        1. Always think step by step
        2. Use available tools effectively
        3. Log your progress regularly
        4. Provide clear, actionable results
        5. Recommend next steps when appropriate
        """
        
        # Add tool creation guidance
        if self.agent_data.can_create_tools:
            base_prompt += """
            
            You can create custom tools when needed:
            1. Assess if existing tools are sufficient
            2. Design new tools with clear interfaces
            3. Implement with proper error handling
            4. Test thoroughly before deployment
            5. Document usage and limitations
            """
        
        # Add handoff guidance
        base_prompt += """
        
        When collaborating with other agents:
        - Use handoffs for specialized expertise
        - Provide clear context and requirements
        - Escalate when tasks exceed your capabilities
        - Maintain conversation continuity
        """
        
        return base_prompt
    
    # ==============================================================================
    # FUNCTION TOOLS
    # ==============================================================================
    
    @function_tool
    async def create_custom_tool(
        self,
        name: str,
        description: str,
        code: str,
        test_input: Optional[str] = None
    ) -> str:
        """
        Create a custom tool with validation and testing.
        
        Args:
            name: The name of the tool function
            description: A description of what the tool does
            code: Python code implementing the tool (must be an async function)
            test_input: Optional test input to validate the tool
            
        Returns:
            Information about the created tool (JSON string)
        """
        from tools.registry import tool_registry
        
        logger.info(f"Agent {self.agent_data.id} creating custom tool: {name}")
        
        try:
            # Validate the tool code
            validation_results = await self._validate_tool_code(code, test_input)
            
            if not validation_results["valid"]:
                return json.dumps(ToolCreationOutput(
                    success=False,
                    tool_name=name,
                    error_message=f"Validation failed: {validation_results['error']}",
                    validation_results=validation_results
                ).model_dump())
            
            # Register the tool with the registry
            tool_info = await tool_registry.register_tool(
                name=name,
                description=description,
                code=code,
                workspace_id=str(self.agent_data.workspace_id),
                created_by="agent"
            )
            
            # Save to database
            from database import create_custom_tool
            tool_db_record = await create_custom_tool(
                name=name,
                description=description,
                code=code,
                workspace_id=str(self.agent_data.workspace_id),
                created_by="agent"
            )
            
            return json.dumps(ToolCreationOutput(
                success=True,
                tool_name=name,
                tool_id=tool_db_record.get("id") if tool_db_record else None,
                validation_results=validation_results
            ).model_dump())
            
        except Exception as e:
            logger.error(f"Failed to create custom tool: {e}")
            return json.dumps(ToolCreationOutput(
                success=False,
                tool_name=name,
                error_message=str(e)
            ).model_dump())
    
    async def _validate_tool_code(self, code: str, test_input: Optional[str] = None) -> Dict[str, Any]:
        """Validate tool code for security and correctness"""
        try:
            # Basic syntax check
            compile(code, '<string>', 'exec')
            
            # Check for dangerous operations
            dangerous_patterns = [
                'import os', 'import sys', 'import subprocess',
                'eval(', 'exec(', '__import__'
            ]
            
            for pattern in dangerous_patterns:
                if pattern in code:
                    return {
                        "valid": False,
                        "error": f"Dangerous operation detected: {pattern}",
                        "security_check": False
                    }
            
            # TODO: Add more sophisticated validation
            # - Runtime testing in sandbox
            # - Security analysis
            # - Performance checks
            
            return {
                "valid": True,
                "security_check": True,
                "syntax_check": True
            }
            
        except SyntaxError as e:
            return {
                "valid": False,
                "error": f"Syntax error: {str(e)}",
                "syntax_check": False
            }
    
    @function_tool
    async def log_execution(self, step: str, details: str) -> bool:
        """
        Log the execution of a step with structured data.
        
        Args:
            step: The name/description of the execution step
            details: Details about the execution (JSON string)
            
        Returns:
            Boolean indicating success
        """
        try:
            # Parse details string to dictionary
            details_dict = {}
            if isinstance(details, str):
                try:
                    details_dict = json.loads(details)
                except json.JSONDecodeError:
                    details_dict = {"raw_message": details}
            else:
                details_dict = {"raw_message": str(details)}
            
            # Enhanced logging with metadata
            log_entry = {
                "agent_id": str(self.agent_data.id),
                "agent_name": self.agent_data.name,
                "step": step,
                "timestamp": None,  # Will be set by database
                "details": details_dict,
                "seniority": self.agent_data.seniority,
                "workspace_id": str(self.agent_data.workspace_id)
            }
            
            logger.info(f"Agent execution log: {json.dumps(log_entry)}")
            
            # TODO: Save to execution_logs table in database
            # await save_execution_log(log_entry)
            
            return True
        except Exception as e:
            logger.error(f"Error in log_execution: {e}")
            return False
    
    @function_tool
    async def update_health_status(self, status: str, details: Optional[str] = None) -> bool:
        """
        Update the health status of the agent with enhanced monitoring.
        
        Args:
            status: The health status (healthy, degraded, unhealthy)
            details: Optional details about the health status (JSON string)
            
        Returns:
            Boolean indicating success
        """
        try:
            # Parse details
            details_dict = {}
            if details:
                try:
                    details_dict = json.loads(details)
                except json.JSONDecodeError:
                    details_dict = {"raw_message": details}
            
            # Add system metrics
            details_dict.update({
                "model_used": self.agent.model,
                "tools_count": len(self.tools),
                "check_timestamp": None  # Will be set by database
            })
            
            health = AgentHealth(
                status=HealthStatus(status),
                details=details_dict
            )
            
            await update_agent_status(
                agent_id=str(self.agent_data.id),
                status=self.agent_data.status,
                health=health.model_dump()
            )
            
            # Log health update
            logger.info(f"Agent {self.agent_data.id} health updated to {status}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to update agent health status: {e}")
            return False
    
    @function_tool
    async def report_progress(
        self,
        task_id: str,
        progress_percentage: int,
        current_stage: str,
        notes: Optional[str] = None
    ) -> bool:
        """
        Report progress on a task.
        
        Args:
            task_id: ID of the task being worked on
            progress_percentage: Progress as percentage (0-100)
            current_stage: Description of current stage
            notes: Optional additional notes
            
        Returns:
            Boolean indicating success
        """
        try:
            progress_data = {
                "task_id": task_id,
                "agent_id": str(self.agent_data.id),
                "progress_percentage": min(100, max(0, progress_percentage)),
                "current_stage": current_stage,
                "notes": notes,
                "timestamp": None  # Will be set by database
            }
            
            logger.info(f"Progress update: {json.dumps(progress_data)}")
            
            # TODO: Save to task_progress table
            # await save_task_progress(progress_data)
            
            return True
        except Exception as e:
            logger.error(f"Error reporting progress: {e}")
            return False
    
    # ==============================================================================
    # CORE METHODS
    # ==============================================================================
    
    async def verify_capabilities(self) -> bool:
        """
        Verify that the agent has all the capabilities it needs.
        
        Returns:
            Boolean indicating if all capabilities are available
        """
        try:
            # Create verification prompt
            verification_prompt = """
            Perform a comprehensive capability verification:
            1. List all available tools and their status
            2. Check system connectivity and resources
            3. Verify model configuration and access
            4. Test basic functionality if possible
            5. Report any missing requirements or limitations
            
            Provide a structured assessment of your capabilities.
            """
            
            result = await Runner.run(
                self.agent,
                verification_prompt
            )
            
            # Process the structured output
            verification_output = result.final_output
            if isinstance(verification_output, CapabilityVerificationOutput):
                verification_passed = verification_output.verification_status == "passed"
            else:
                # Fallback parsing for unstructured output
                verification_passed = "verification_status: passed" in str(verification_output)
            
            # Update agent status based on verification
            if verification_passed:
                await update_agent_status(
                    agent_id=str(self.agent_data.id),
                    status=AgentStatus.ACTIVE.value,
                    health={
                        "status": HealthStatus.HEALTHY.value,
                        "last_update": None,
                        "details": {
                            "verification": "passed",
                            "tools_verified": len(self.tools),
                            "model": self.agent.model
                        }
                    }
                )
            else:
                await update_agent_status(
                    agent_id=str(self.agent_data.id),
                    status=AgentStatus.ERROR.value,
                    health={
                        "status": HealthStatus.DEGRADED.value,
                        "last_update": None,
                        "details": {
                            "verification": "failed",
                            "output": str(verification_output)
                        }
                    }
                )
            
            return verification_passed
            
        except Exception as e:
            logger.error(f"Failed to verify agent capabilities: {e}")
            
            await update_agent_status(
                agent_id=str(self.agent_data.id),
                status=AgentStatus.ERROR.value,
                health={
                    "status": HealthStatus.UNHEALTHY.value,
                    "last_update": None,
                    "details": {
                        "verification": "error",
                        "error": str(e)
                    }
                }
            )
            
            return False
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute a task assigned to this agent with structured output.
        
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
            
            # Log task start
            await self.log_execution(
                "task_started",
                json.dumps({
                    "task_id": str(task.id),
                    "task_name": task.name,
                    "description": task.description
                })
            )
            
            # Create enhanced task prompt
            task_prompt = f"""
            Execute the following task with precision and efficiency:
            
            Task: {task.name}
            Description: {task.description}
            
            Requirements:
            1. Provide a clear summary of what was accomplished
            2. Include detailed results with relevant data
            3. Suggest logical next steps
            4. Report any issues or limitations encountered
            5. Estimate resources used
            
            Use your tools effectively and maintain high quality standards.
            """
            
            # Execute the task
            result = await Runner.run(self.agent, task_prompt)
            
            # Process the structured output
            if isinstance(result.final_output, TaskExecutionOutput):
                task_output = result.final_output
                task_result = {
                    "task_id": task_output.task_id,
                    "status": task_output.status,
                    "summary": task_output.summary,
                    "detailed_results": task_output.detailed_results,
                    "next_steps": task_output.next_steps,
                    "suggested_handoff": task_output.suggested_handoff,
                    "resources_consumed": task_output.resources_consumed
                }
            else:
                # Fallback for unstructured output
                task_result = {
                    "output": result.final_output,
                    "status": "completed"
                }
            
            # Update task status with structured result
            await update_task_status(
                task_id=str(task.id),
                status=TaskStatus.COMPLETED.value,
                result=task_result
            )
            
            # Log completion
            await self.log_execution(
                "task_completed",
                json.dumps({
                    "task_id": str(task.id),
                    "status": task_result.get("status"),
                    "summary": task_result.get("summary", "")
                })
            )
            
            return task_result
            
        except Exception as e:
            logger.error(f"Failed to execute task: {e}")
            
            error_result = {
                "error": str(e),
                "status": "failed",
                "task_id": str(task.id)
            }
            
            await update_task_status(
                task_id=str(task.id),
                status=TaskStatus.FAILED.value,
                result=error_result
            )
            
            # Log error
            await self.log_execution(
                "task_failed",
                json.dumps({
                    "task_id": str(task.id),
                    "error": str(e)
                })
            )
            
            return error_result
    
    # ==============================================================================
    # UTILITY METHODS
    # ==============================================================================
    
    def as_tool(self, tool_name: Optional[str] = None, tool_description: Optional[str] = None):
        """
        Convert this agent into a tool that can be used by other agents.
        
        Args:
            tool_name: Custom name for the tool
            tool_description: Custom description for the tool
            
        Returns:
            Agent tool
        """
        return self.agent.as_tool(
            tool_name=tool_name or f"consult_{self.agent_data.name.lower().replace(' ', '_')}",
            tool_description=tool_description or f"Consult {self.agent_data.name} for {self.agent_data.role} expertise"
        )
    
    def get_capabilities_summary(self) -> Dict[str, Any]:
        """Get a summary of this agent's capabilities"""
        return {
            "name": self.agent_data.name,
            "role": self.agent_data.role,
            "seniority": self.agent_data.seniority,
            "model": self.agent.model,
            "tools_count": len(self.tools),
            "can_create_tools": self.agent_data.can_create_tools,
            "handoffs_configured": len(self.handoffs),
            "guardrails_active": {
                "input": len(self.agent.input_guardrails) > 0,
                "output": len(self.agent.output_guardrails) > 0
            }
        }