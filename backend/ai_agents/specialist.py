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
from database import update_agent_status, update_task_status, create_task, list_agents

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

class TaskCreationOutput(BaseModel):
    """Output strutturato per la creazione di task"""
    success: bool
    task_id: Optional[str] = None
    task_name: str
    assigned_agent: Optional[str] = None
    error_message: Optional[str] = None

class HandoffRequest(BaseModel):
    """Richiesta di handoff strutturata"""
    target_agent_role: str
    context: str
    priority: Literal["low", "medium", "high"] = "medium"
    expected_output: Optional[str] = None

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
    """Advanced Specialist Agent with automated task creation and handoffs"""
    
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
        tools = [
            # automation di base
            self._create_auto_task_tool(),
            self._create_request_handoff_tool(),
            self._create_log_execution_tool(),
            self._create_update_health_status_tool(),
            self._create_report_progress_tool(),
        ]

        # tool "nativi" in base a self.agent_data.tools (impostati dal Director)
        if self.agent_data.tools:
            for cfg in self.agent_data.tools:
                if not isinstance(cfg, dict):
                    continue
                t = cfg.get("type", "")
                if t == "web_search":
                    tools.append(WebSearchTool(search_context_size="medium"))
                elif t == "file_search":
                    tools.append(
                        FileSearchTool(
                            max_num_results=5,
                            include_search_results=True,
                            vector_store_ids=getattr(self.agent_data, "vector_store_ids", None),
                        )
                    )
                # eventuali custom function restano da gestire

        # fallback: se l'agente ha vector_store_ids ma manca file_search
        if getattr(self.agent_data, "vector_store_ids", None) and not any(
            isinstance(x, FileSearchTool) for x in tools
        ):
            tools.append(
                FileSearchTool(
                    max_num_results=5,
                    vector_store_ids=self.agent_data.vector_store_ids,
                )
            )

        # strumenti Instagram per ruoli social
        if any(k in self.agent_data.role.lower() for k in ("social media", "instagram", "content")):
            tools.extend(self._get_instagram_function_tools())

        # permesso di creare nuovi tool
        if self.agent_data.can_create_tools:
            tools.append(self._create_custom_tool_tool())

        return tools
    
    def _get_instagram_function_tools(self) -> List[Any]:
        """Get Instagram-specific function tools"""
        # Import Instagram tools from social_media module
        from tools.social_media import InstagramTools
        
        return [
            InstagramTools.analyze_hashtags,
            InstagramTools.analyze_account,
            InstagramTools.generate_content_ideas,
            InstagramTools.analyze_competitors
        ]
    
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
        # Implement escalation logic
    
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
        )
    
    def _create_system_prompt(self) -> str:
        """Create an enhanced system prompt with automation + tool guidance"""
        base = self.agent_data.system_prompt or f"""
    You are a {self.agent_data.seniority} AI agent specializing in {self.agent_data.role}.

    CORE RESPONSIBILITIES
    - {self.agent_data.description}
    - Execute tasks with precision and efficiency
    - Monitor resource usage and budget constraints
    - Collaborate effectively with other agents
    - Maintain high-quality standards in all outputs
    """

        # ── automation guidance (valido per tutti) ──────────────────────────────
        base += """
    AUTOMATION CAPABILITIES
    1. create_task_for_agent – delegate work with clear context, priority, deadline
    2. request_handoff – transfer work/data to another agent, include expected output
    Be proactive: when you finish a task, create follow-ups or handoffs as needed.
    """

        # ── tool usage guidance (solo se tool presenti) ────────────────────────
        if self.agent_data.tools:
            ws = any(t.get("type") == "web_search" for t in self.agent_data.tools)
            fs = any(t.get("type") == "file_search" for t in self.agent_data.tools)

            base += "\nAVAILABLE TOOLS\n"
            if ws:
                base += "- WebSearch : research trends, market insights, competitor data\n"
            if fs:
                base += "- FileSearch : locate docs, templates, prior work in KB\n"

            if any(k in self.agent_data.role.lower() for k in ("social media", "instagram")):
                base += "- Instagram Tools : hashtags, account analysis, content ideas\n"

            base += """
        TOOL USAGE BEST PRACTICES:
        1. Always explain why you're using a tool
        2. Summarize key findings from tool results
        3. Use multiple tools together for comprehensive analysis
        4. Report progress using log_execution and report_progress
    """

        # ── extra guidance per coordinatori/manager ────────────────────────────
        if any(k in self.agent_data.role.lower() for k in ("coordinator", "manager")):
            base += """
        COORDINATION RESPONSIBILITIES:
        - Use create_task_for_agent to delegate specific work to specialists
        - Use request_handoff to transfer complex work with context
        - Always create clear, actionable tasks for other agents
        - Monitor team progress and adjust plans as needed
    """

        # ── collaboration blocco comune ────────────────────────────────────────
        base += """
    COLLABORATION
    - Delegate efficiently via automation tools
    - Provide clear context & requirements
    - Escalate when tasks exceed your scope
    - Keep conversation continuity through proper handoffs
    """

        return base
    
    # ==============================================================================
    # AUTOMATION TOOLS
    # ==============================================================================
    
    def _create_auto_task_tool(self):
        """Create a tool for automatic task creation"""
        @function_tool
        async def create_task_for_agent(
            task_name: str,
            task_description: str,
            target_agent_role: str,
            priority: str
        ) -> str:
            """
            Create a new task and assign it to a specific agent role.
            
            Args:
                task_name: Name of the task to create
                task_description: Detailed description of the task
                target_agent_role: Role of the agent who should handle this task
                priority: Priority of the task (low, medium, high)
            
            Returns:
                JSON string with creation result
            """
            try:
                # Find the target agent by role
                agents = await list_agents(str(self.agent_data.workspace_id))
                target_agent = None
                
                for agent in agents:
                    if target_agent_role.lower() in agent["role"].lower():
                        target_agent = agent
                        break
                
                if not target_agent:
                    return json.dumps(TaskCreationOutput(
                        success=False,
                        task_name=task_name,
                        error_message=f"No agent found with role matching '{target_agent_role}'"
                    ).model_dump())
                
                # Create the task
                task_data = await create_task(
                    workspace_id=str(self.agent_data.workspace_id),
                    agent_id=target_agent["id"],
                    name=task_name,
                    description=f"{task_description}\n\nPriority: {priority}\nCreated by: {self.agent_data.name}",
                    status=TaskStatus.PENDING.value
                )
                
                if task_data:
                    # Log the task creation
                    await self._log_execution_internal(
                        "task_created",
                        json.dumps({
                            "created_task_id": task_data["id"],
                            "task_name": task_name,
                            "assigned_to": target_agent["name"],
                            "priority": priority
                        })
                    )
                    
                    return json.dumps(TaskCreationOutput(
                        success=True,
                        task_id=task_data["id"],
                        task_name=task_name,
                        assigned_agent=target_agent["name"]
                    ).model_dump())
                else:
                    return json.dumps(TaskCreationOutput(
                        success=False,
                        task_name=task_name,
                        error_message="Failed to create task in database"
                    ).model_dump())
                
            except Exception as e:
                logger.error(f"Error creating task: {e}")
                return json.dumps(TaskCreationOutput(
                    success=False,
                    task_name=task_name,
                    error_message=str(e)
                ).model_dump())
        
        return create_task_for_agent
    
    def _create_request_handoff_tool(self):
        """Create a tool for requesting handoffs to other agents"""
        @function_tool
        async def request_handoff(
            target_role: str,
            context: str,
            data_to_transfer: str,
            priority: str
        ) -> str:
            """
            Request a handoff to another agent with specific context and data.
            
            Args:
                target_role: Role of the target agent for handoff
                context: Context and reason for the handoff
                data_to_transfer: Information to pass to the target agent
                priority: Priority of the handoff (low, medium, high)
            
            Returns:
                JSON string with handoff result
            """
            try:
                # Log the handoff request
                await self._log_execution_internal(
                    "handoff_requested",
                    json.dumps({
                        "target_role": target_role,
                        "context": context,
                        "priority": priority,
                        "requesting_agent": self.agent_data.name
                    })
                )
                
                # Create a task for the target agent with handoff context
                task_description = f"""
                HANDOFF FROM: {self.agent_data.name} ({self.agent_data.role})
                
                CONTEXT: {context}
                
                DATA/INFORMATION TRANSFERRED:
                {data_to_transfer}
                
                PRIORITY: {priority}
                
                Please continue the work based on the information provided above.
                """
                
                # Use the auto task creation
                agents = await list_agents(str(self.agent_data.workspace_id))
                target_agent = None
                
                for agent in agents:
                    if target_role.lower() in agent["role"].lower():
                        target_agent = agent
                        break
                
                if not target_agent:
                    return json.dumps({
                        "success": False,
                        "error": f"No agent found with role matching '{target_role}'"
                    })
                
                # Create the handoff task
                task_data = await create_task(
                    workspace_id=str(self.agent_data.workspace_id),
                    agent_id=target_agent["id"],
                    name=f"Handoff from {self.agent_data.name}",
                    description=task_description,
                    status=TaskStatus.PENDING.value
                )
                
                if task_data:
                    return json.dumps({
                        "success": True,
                        "task_id": task_data["id"],
                        "target_agent": target_agent["name"],
                        "handoff_type": "task_creation"
                    })
                else:
                    return json.dumps({
                        "success": False,
                        "error": "Failed to create handoff task"
                    })
                
            except Exception as e:
                logger.error(f"Error requesting handoff: {e}")
                return json.dumps({
                    "success": False,
                    "error": str(e)
                })
        
        return request_handoff
    
    # ==============================================================================
    # INTERNAL METHODS
    # ==============================================================================
    
    async def _log_execution_internal(self, step: str, details: str) -> bool:
        """Internal method for logging execution"""
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
    
    async def _update_health_status_internal(self, status: str, details: Optional[str] = None) -> bool:
        """Internal method for updating health status"""
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
    
    async def _report_progress_internal(
        self,
        task_id: str,
        progress_percentage: int,
        current_stage: str,
        notes: Optional[str] = None
    ) -> bool:
        """Internal method for reporting progress"""
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
    # TOOL CREATORS
    # ==============================================================================
    
    def _create_log_execution_tool(self):
        """Create a function tool for log execution"""
        @function_tool
        async def log_execution(step: str, details: str) -> bool:
            """
            Log the execution of a step with structured data.
            
            Args:
                step: The name/description of the execution step
                details: Details about the execution (JSON string)
                
            Returns:
                Boolean indicating success
            """
            return await self._log_execution_internal(step, details)
        
        return log_execution
    
    def _create_update_health_status_tool(self):
        """Create a function tool for updating health status"""
        @function_tool
        async def update_health_status(status: str, details: Optional[str] = None) -> bool:
            """
            Update the health status of the agent with enhanced monitoring.
            
            Args:
                status: The health status (healthy, degraded, unhealthy)
                details: Optional details about the health status (JSON string)
                
            Returns:
                Boolean indicating success
            """
            return await self._update_health_status_internal(status, details)
        
        return update_health_status
    
    def _create_report_progress_tool(self):
        """Create a function tool for reporting progress"""
        @function_tool
        async def report_progress(
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
            return await self._report_progress_internal(task_id, progress_percentage, current_stage, notes)
        
        return report_progress
    
    def _create_custom_tool_tool(self):
        """Create a function tool for creating custom tools"""
        @function_tool
        async def create_custom_tool(
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
        
        return create_custom_tool
    
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
        Execute a task with enhanced automation capabilities.
        
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
            
            # Log task start using internal method
            await self._log_execution_internal(
                "task_started",
                json.dumps({
                    "task_id": str(task.id),
                    "task_name": task.name,
                    "description": task.description
                })
            )
            
            # Enhanced task prompt with automation capabilities
            task_prompt = f"""
            Execute the following task with full automation capabilities:
            
            Task: {task.name}
            Description: {task.description}
            
            AUTOMATION TOOLS AVAILABLE:
            1. create_task_for_agent: Create new tasks for specialists
            2. request_handoff: Hand off work to other agents
            3. log_execution: Log your progress
            4. report_progress: Report detailed progress
            
            IMPORTANT INSTRUCTIONS:
            - If this task involves multiple phases, create specific tasks for each phase
            - If you identify work that needs specific expertise, delegate it immediately
            - If you complete your part but need follow-up, create those tasks now
            - Use handoffs when you need to transfer context and data to others
            - Be proactive - don't wait for manual intervention
            
            After completing your work:
            1. Analyze what needs to happen next
            2. Create specific tasks for other specialists if needed
            3. Use handoffs to transfer work with proper context
            4. Provide a comprehensive summary of actions taken
            
            Execute the task and handle all automation proactively.
            """
            
            # Execute the task
            result = await Runner.run(self.agent, task_prompt, max_turns=15)
            
            # Process the result
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
                    "status": "completed",
                    "automation_actions": {
                        "tasks_created": [],
                        "handoffs_requested": [],
                        "next_steps_identified": []
                    }
                }
            
            # Update task status with structured result
            await update_task_status(
                task_id=str(task.id),
                status=TaskStatus.COMPLETED.value,
                result=task_result
            )
            
            # Log completion using internal method
            await self._log_execution_internal(
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
                "task_id": str(task.id),
                "recoverable": True  # Indica che si può riprovare
            }
            
            await update_task_status(
                task_id=str(task.id),
                status=TaskStatus.FAILED.value,
                result=error_result
            )
            
            # Log error using internal method
            await self._log_execution_internal(
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
            },
            "automation_enabled": True
        }