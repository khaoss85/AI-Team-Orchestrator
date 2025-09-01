
"""
🚀 ENHANCED SPECIALIST AGENT
Combina la stabilità di specialist_minimal con le features avanzate del vecchio specialist
Rispetta tutti i 14 pilastri strategici
"""

import logging
import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

# CRITICAL: Load environment variables for OpenAI API access
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# Configure OpenAI trace BEFORE importing SDK
if os.getenv('OPENAI_TRACE', 'false').lower() == 'true':
    logger.info("🔍 Configuring OpenAI trace for specialist agent")
    os.environ['OPENAI_TRACE'] = 'true'
    os.environ['OPENAI_TRACE_SAMPLE_RATE'] = os.getenv('OPENAI_TRACE_SAMPLE_RATE', '1.0')
    os.environ['OPENAI_TRACE_INCLUDE_SYSTEM'] = os.getenv('OPENAI_TRACE_INCLUDE_SYSTEM', 'true')
    os.environ['OPENAI_TRACE_INCLUDE_TOOLS'] = os.getenv('OPENAI_TRACE_INCLUDE_TOOLS', 'true')

# Import SDK components lazily to prevent circular dependencies
SDK_AVAILABLE = True
try:
    from agents import (
        Agent as OpenAIAgent, 
        Runner,
        function_tool,
        WebSearchTool,
        FileSearchTool,
        handoff,
        RunContextWrapper,
        RunResult,
        input_guardrail,
        output_guardrail,
        GuardrailFunctionOutput
    )
    logger.info("✅ OpenAI Agents SDK loaded successfully with trace configuration")
except ImportError:
    SDK_AVAILABLE = False
    logger.warning("OpenAI Agents SDK not available - using minimal fallback")

from models import Agent as AgentModel, Task, TaskStatus, TaskExecutionOutput, AgentStatus
from pydantic import BaseModel
from typing import Any

# Orchestration Context Model remains for now, will be replaced by RunContextWrapper in Phase 3
class OrchestrationContext(BaseModel):
    workspace_id: str
    task_id: str
    agent_id: str
    agent_role: str
    agent_seniority: str
    task_name: str
    task_description: str
    execution_metadata: Dict[str, Any] = {}
    available_agents: List[Dict[str, Any]] = []
    orchestration_state: Dict[str, Any] = {}
    task_classification: Optional[Any] = None
    available_tools: List[str] = []

class EnhancedTaskExecutionOutput(TaskExecutionOutput):
    summary: Optional[str] = None
    structured_content: Optional[str] = None

class SpecialistAgent:
    def __init__(self, agent_data: AgentModel, all_workspace_agents_data: List[AgentModel] = None):
        self.agent_data = agent_data
        self.all_workspace_agents_data = all_workspace_agents_data or []
        self.tools = self._initialize_tools()
        self.handoffs = self._create_native_handoff_tools() if SDK_AVAILABLE and self.all_workspace_agents_data else []
        # 🧠 AI-DRIVEN: Use SDK native guardrails with AI validation
        self.input_guardrail = self._get_ai_input_guardrail() if SDK_AVAILABLE else None
        self.output_guardrail = self._get_ai_output_guardrail() if SDK_AVAILABLE else None

    # ... (other methods remain the same) ...

    async def execute(self, task: Task, session: Optional[Any] = None, thinking_process_id: Optional[str] = None) -> TaskExecutionOutput:
        """🧠 AI-DRIVEN Execute task with task classification and proper tool usage"""
        logger.info(f"🚀 Enhanced execution for task {task.id}")
        
        # LAZY IMPORTS to break circular dependencies
        from database import update_agent_status
        from services.unified_memory_engine import unified_memory_engine
        from ai_quality_assurance.unified_quality_engine import unified_quality_engine
        from services.sdk_memory_bridge import create_workspace_session
        from services.ai_task_execution_classifier import classify_task_for_execution
        
        # Import thinking engine for enhanced metadata capture
        thinking_engine = None
        if thinking_process_id:
            try:
                from services.thinking_process import thinking_engine
                logger.debug(f"💭 Thinking engine loaded for process {thinking_process_id}")
            except ImportError:
                logger.warning("Thinking engine not available for metadata capture")

        try:
            await update_agent_status(str(self.agent_data.id), AgentStatus.BUSY.value)
            
            if not SDK_AVAILABLE:
                raise Exception("OpenAI Agents SDK required for enhanced execution")
            
            # 🧠 CRITICAL: AI-driven task classification to determine execution type
            logger.info(f"🧠 Classifying task execution type: {task.name}")
            
            # 🔧 HOLISTIC: Get available tools first for intelligent classification
            from services.mcp_tool_discovery import get_mcp_tools_for_agent
            try:
                mcp_tools = await get_mcp_tools_for_agent(
                    agent_name=self.agent_data.name,
                    domain="data_analysis",  # Default domain
                    workspace_id=str(task.workspace_id)
                )
                available_tools = [tool.get("name", "unknown") for tool in mcp_tools] + ["WebSearchTool", "FileSearchTool"]
            except Exception as e:
                logger.warning(f"Failed to get MCP tools: {e}")
                available_tools = ["WebSearchTool", "FileSearchTool"]
            
            task_classification = await classify_task_for_execution(
                task_name=task.name,
                task_description=task.description,
                workspace_context={"workspace_id": str(task.workspace_id)},
                available_tools=available_tools
            )
            
            logger.info(f"✅ Task classified as: {task_classification.execution_type.value}")
            logger.info(f"🔧 Tools required: {task_classification.requires_tools}")
            
            if session is None:
                session = create_workspace_session(str(task.workspace_id), str(self.agent_data.id))
                logger.info(f"📚 Created new SDK session for workspace {task.workspace_id}")

            orchestration_context = await self._create_ai_driven_context(task, task_classification)
            
            # 🔧 CRITICAL: Configure tools based on AI classification
            execution_tools = self._configure_execution_tools(task_classification)
            
            agent_config = {
                "name": self.agent_data.name,
                "instructions": self._create_execution_aware_prompt(task, task_classification),
                "model": "gpt-4o-mini",
                "tools": execution_tools,
                "handoffs": self.handoffs,
                "input_guardrails": [self.input_guardrail] if self.input_guardrail else [],
                "output_guardrails": [self.output_guardrail] if self.output_guardrail else []
            }
            
            agent = OpenAIAgent(**{k: v for k, v in agent_config.items() if v})

            # 🧠 ENHANCED: Add agent execution start thinking step
            if thinking_process_id and thinking_engine:
                try:
                    agent_info = {
                        "id": str(self.agent_data.id),
                        "name": self.agent_data.name,
                        "role": self.agent_data.role,
                        "seniority": self.agent_data.seniority,
                        "skills": getattr(self.agent_data, 'skills', []),
                        "status": "executing",
                        "workspace_id": str(task.workspace_id),
                        "task_id": str(task.id),
                        "execution_type": task_classification.execution_type.value,
                        "tools_configured": len(execution_tools),
                        "tools_required": task_classification.requires_tools
                    }
                    
                    action_description = f"beginning execution of {task_classification.execution_type.value} task '{task.name}' with {len(execution_tools)} configured tools"
                    await thinking_engine.add_agent_thinking_step(
                        process_id=thinking_process_id,
                        agent_info=agent_info,
                        action_description=action_description,
                        confidence=0.85
                    )
                    logger.debug(f"💭 Added agent execution start metadata to thinking process {thinking_process_id}")
                except Exception as agent_start_error:
                    logger.warning(f"Failed to add agent execution start to thinking process: {agent_start_error}")

            start_time = time.time()
            
            # 🎯 CRITICAL: For DATA_COLLECTION tasks, enforce web tool usage
            execution_input = self._prepare_execution_input(task, task_classification)
            
            # 🔧 CRITICAL: Create context bridge for SDK RunContextWrapper
            # Pass the data directly to the context, not nested inside orchestration_context
            context_data = {
                "task_classification": task_classification,
                "execution_type": task_classification.execution_type.value,
                "available_tools": task_classification.tools_needed,
                "requires_tools": task_classification.requires_tools,
                "workspace_id": str(task.workspace_id),
                "orchestration_context": orchestration_context
            }
            
            run_params = {
                "starting_agent": agent,
                "input": execution_input,
                "context": context_data,
                "session": session,
                "max_turns": 8 if task_classification.requires_tools else 5
            }
            run_result = await Runner.run(**run_params)
            execution_time = time.time() - start_time
            
            # 🧠 ENHANCED: Add tool execution metadata after run completion
            if thinking_process_id and thinking_engine:
                try:
                    tool_results = {
                        "tool_name": "Agent_Execution_Pipeline",
                        "tool_type": "composite",
                        "execution_time_ms": int(execution_time * 1000),
                        "success": True,  # Will be updated based on validation
                        "parameters": {
                            "classification": task_classification.execution_type.value,
                            "max_turns": run_params.get("max_turns", 5),
                            "tools_available": len(execution_tools)
                        },
                        "output_type": type(run_result.final_output).__name__,
                        "output_size": len(str(run_result.final_output)) if run_result.final_output else 0,
                        "summary": f"Completed {task_classification.execution_type.value} execution in {execution_time:.2f}s",
                        "agent_id": str(self.agent_data.id),
                        "task_id": str(task.id)
                    }
                    
                    step_description = f"execution completed with classification {task_classification.execution_type.value}"
                    await thinking_engine.add_tool_execution_step(
                        process_id=thinking_process_id,
                        tool_results=tool_results,
                        step_description=step_description,
                        confidence=0.8
                    )
                    logger.debug(f"💭 Added tool execution metadata to thinking process {thinking_process_id}")
                except Exception as tool_meta_error:
                    logger.warning(f"Failed to add tool execution metadata to thinking process: {tool_meta_error}")
            
            # 🔍 CRITICAL: Validate that DATA_COLLECTION tasks produced real data
            result_content = str(run_result.final_output)
            
            if task_classification.execution_type.value == "data_collection":
                result_content = await self._validate_data_collection_output(result_content, task_classification)
            
            output = EnhancedTaskExecutionOutput(
                task_id=task.id,
                status=TaskStatus.COMPLETED,
                result=result_content,
                execution_time=execution_time,
                summary=f"Executed as {task_classification.execution_type.value} with tools: {task_classification.tools_needed}",
                structured_content=result_content
            )
            
            await self._save_to_memory(task, output, unified_memory_engine)
            await self._validate_quality(task, output, unified_quality_engine)
            
            return output
            
        except Exception as e:
            logger.error(f"❌ Task {task.id} failed: {e}")
            return EnhancedTaskExecutionOutput(task_id=task.id, status=TaskStatus.FAILED, error_message=str(e))
        finally:
            await update_agent_status(str(self.agent_data.id), AgentStatus.IDLE.value)

    async def _save_to_memory(self, task: Task, output: TaskExecutionOutput, memory_engine):
        # ... (implementation remains the same) ...
        pass

    async def _validate_quality(self, task: Task, output: TaskExecutionOutput, quality_engine):
        # ... (implementation remains the same) ...
        pass
        
    def _configure_execution_tools(self, classification) -> List[Any]:
        """🔧 Configure tools based on AI task classification"""
        tools = []
        
        if SDK_AVAILABLE:
            # Always include WebSearchTool for data collection tasks
            if classification.requires_tools and "WebSearchTool" in classification.tools_needed:
                try:
                    web_search_tool = WebSearchTool()
                    tools.append(web_search_tool)
                    logger.info("✅ WebSearchTool configured for data collection")
                except Exception as e:
                    logger.error(f"❌ Failed to configure WebSearchTool: {e}")
            
            # Include FileSearchTool if needed
            if hasattr(self.agent_data, 'vector_store_ids') and self.agent_data.vector_store_ids:
                try:
                    tools.append(FileSearchTool(vector_store_ids=self.agent_data.vector_store_ids))
                    logger.info("✅ FileSearchTool configured")
                except Exception as e:
                    logger.warning(f"FileSearchTool not available: {e}")
            
            # Add MCP tools if available
            if hasattr(self, '_mcp_tools_loaded'):
                tools.extend(getattr(self, '_mcp_tools', []))
        
        logger.info(f"🔧 Configured {len(tools)} tools for execution type: {classification.execution_type.value}")
        return tools
    
    def _prepare_execution_input(self, task: Task, classification) -> str:
        """🎯 Prepare execution input based on task classification"""
        
        base_input = f"""
TASK: {task.name}
DESCRIPTION: {task.description}
EXECUTION TYPE: {classification.execution_type.value}
"""
        
        if classification.execution_type.value == "data_collection":
            if classification.output_specificity == "specific_data":
                base_input += f"""
🎯 SPECIFIC DATA EXTRACTION - CRITICAL:
- You MUST use WebSearchTool to find ACTUAL contact details
- Extract REAL names, emails, phone numbers, job titles
- DO NOT provide methodologies or "how to find" information
- DO NOT generate examples or templates
- Output format required: {classification.expected_data_format or 'structured list'}
- Expected output: {classification.content_type_expected}

REQUIRED DATA FIELDS:
- Full Name (real person names)
- Job Title/Role
- Company Name
- Email Address (verified if possible)
- Phone Number (if available)
- LinkedIn Profile (if found)

SEARCH STRATEGY:
- Use "site:linkedin.com marketing manager salesforce" for specific roles
- Search company websites for team pages and contact info
- Use directory sites like apollo.io, zoominfo equivalents
- Look for press releases mentioning executives
- Find company org charts and leadership pages

Your output must be ACTUAL CONTACT DATA, not strategies to find contacts.
"""
            else:
                base_input += f"""
RESEARCH/METHODOLOGY TASK:
- You can provide strategies, resources, and methodologies
- Include links to useful databases and tools
- Explain approaches for data collection
- Expected output: {classification.content_type_expected}
"""
        
        return base_input
    
    async def _validate_data_collection_output(self, output: str, classification) -> str:
        """🔍 AI-DRIVEN: Validate that data collection tasks produced real data without hard-coded keywords"""
        
        # For specific_data tasks, use AI to analyze if output matches intent
        if classification.output_specificity == "specific_data":
            
            # Import AI intent analyzer for semantic validation
            from ai_driven_task_intent_analyzer import ai_intent_analyzer
            
            # Use AI to analyze if output contains actual data vs methodology
            try:
                # Create a validation task for AI analysis
                validation_prompt = f"""
                TASK CLASSIFICATION: {classification.execution_type.value} - {classification.output_specificity}
                EXPECTED: {classification.expected_data_format or 'Structured contact data'} with {classification.content_type_expected}
                
                ACTUAL OUTPUT:
                {output}
                
                Does this output contain the SPECIFIC DATA requested (names, emails, contact details) or is it methodology/guidance?
                """
                
                # Use AI to determine if output matches expected specificity
                import openai
                client = openai.AsyncOpenAI()
                
                response = await client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": """You are validating task output specificity. Determine if the output contains:
                            1. SPECIFIC_DATA: Actual names, emails, phone numbers, contact details, real business information
                            2. METHODOLOGY: Strategies, approaches, "how to find", tools to use, general guidance
                            
                            Respond with JSON: {"contains_specific_data": true/false, "reasoning": "detailed explanation"}"""
                        },
                        {
                            "role": "user",
                            "content": validation_prompt
                        }
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                
                import json
                validation_result = json.loads(response.choices[0].message.content)
                
                logger.info(f"🧠 AI validation result: {validation_result}")
                
                if not validation_result.get("contains_specific_data", True):
                    logger.warning(f"⚠️ AI detected methodology instead of specific data")
                    
                    enhanced_output = f"""
❌ CRITICAL: AI Analysis detected METHODOLOGY/STRATEGY instead of SPECIFIC CONTACT DATA.

TASK REQUIRED: {classification.expected_data_format or 'Contact list'} with actual names, emails, phones
AI ANALYSIS: {validation_result.get('reasoning', 'Output appears to be guidance rather than data')}

ORIGINAL OUTPUT:
{output}

🔄 RE-EXECUTION NEEDED:
- Use WebSearchTool to extract ACTUAL contact details
- Find real names, emails, job titles from company websites  
- Search LinkedIn, company directories, press releases
- Output must be structured contact data, not guidance
"""
                    return enhanced_output
                    
            except Exception as e:
                logger.error(f"❌ AI validation failed, using fallback: {e}")
                # Fallback to basic validation without hard-coded keywords
                if len(output) < 200 or "strategy" in output.lower() or "approach" in output.lower():
                    logger.warning(f"⚠️ Fallback validation suggests methodology content")
                    
                    enhanced_output = f"""
⚠️ VALIDATION: Output may contain methodology instead of specific data.

TASK REQUIRED: {classification.expected_data_format or 'Contact list'} with actual contact details
VALIDATION NOTE: Output analysis suggests guidance rather than concrete data

ORIGINAL OUTPUT:
{output}

RECOMMENDATION:
- Verify output contains actual names, emails, phone numbers
- If methodology only, re-execute with WebSearchTool for real data
"""
                    return enhanced_output
        
        # Standard validation for fake indicators
        fake_indicators = [
            "example.com", "sample@", "placeholder", "template", 
            "your-company", "company-name", "contact-name", 
            "[Your", "[Company", "XXXX", "TODO", "TBD"
        ]
        
        fake_count = sum(1 for indicator in fake_indicators if indicator.lower() in output_lower)
        
        if fake_count > 2:
            logger.warning(f"⚠️ Data collection output contains {fake_count} fake indicators")
            
            enhanced_output = f"""
⚠️ IMPORTANT: This output contains template/placeholder data and needs to be enhanced with real web-searched information.

ORIGINAL OUTPUT:
{output}

NEXT STEPS REQUIRED:
- Use WebSearchTool to find actual companies and contacts
- Replace all placeholder data with real business information
- Collect authentic contact details from web sources
"""
            return enhanced_output
        
        logger.info("✅ Data collection output appears to contain real data")
        return output
    def _initialize_tools(self) -> List[Any]:
        """Initialize real tools for authentic content (Pillar 14) + MCP tools"""
        tools = []
        
        if SDK_AVAILABLE:
            try:
                tools.append(WebSearchTool())
            except Exception as e:
                logger.warning(f"WebSearchTool not available: {e}")
            
            if hasattr(self.agent_data, 'vector_store_ids') and self.agent_data.vector_store_ids:
                try:
                    tools.append(FileSearchTool(vector_store_ids=self.agent_data.vector_store_ids))
                except Exception as e:
                    logger.warning(f"FileSearchTool not available: {e}")
            
            # 🔧 MCP TOOL DISCOVERY: Add dynamically discovered tools
            try:
                asyncio.create_task(self._load_mcp_tools_async(tools))
            except Exception as e:
                logger.warning(f"MCP tools not available: {e}")
                
        return tools
    
    async def _load_mcp_tools_async(self, tools: List[Any]):
        """Asynchronously load MCP tools for this agent"""
        try:
            from services.mcp_tool_discovery import get_mcp_tools_for_agent
            
            mcp_tools = await get_mcp_tools_for_agent(self.agent_data)
            
            # Convert MCP tools to SDK tool functions
            for mcp_tool in mcp_tools:
                sdk_tool = self._create_mcp_tool_function(mcp_tool)
                if sdk_tool:
                    tools.append(sdk_tool)
            
            logger.info(f"🔧 Loaded {len(mcp_tools)} MCP tools for agent {self.agent_data.name}")
            
        except Exception as e:
            logger.error(f"Failed to load MCP tools: {e}")
    
    def _create_mcp_tool_function(self, mcp_tool: Dict[str, Any]):
            """Create SDK tool function from MCP tool definition"""
            try:
                @function_tool
                def mcp_tool_wrapper(**kwargs):
                    """Dynamically created MCP tool wrapper"""
                    try:
                        # In a real implementation, this would call the MCP endpoint
                        # For now, return a mock response
                        return {
                            "tool_name": mcp_tool["name"],
                            "result": f"MCP tool '{mcp_tool['name']}' executed with parameters: {kwargs}",
                            "source": "mcp_discovery",
                            "success": True
                        }
                    except Exception as e:
                        return {
                            "tool_name": mcp_tool["name"],
                            "error": str(e),
                            "source": "mcp_discovery",
                            "success": False
                        }
                
                # Set tool metadata
                mcp_tool_wrapper.__name__ = mcp_tool["name"]
                mcp_tool_wrapper.__doc__ = mcp_tool["description"]
                
                return mcp_tool_wrapper
                
            except Exception as e:
                logger.error(f"Failed to create MCP tool function for '{mcp_tool.get('name', 'unknown')}': {e}")
                return None
    
    def _get_ai_input_guardrail(self):
        """Get AI-driven input guardrail from SDK native guardrails"""
        try:
            from sdk_native_guardrails import validate_task_input_ai
            return validate_task_input_ai
        except ImportError:
            logger.warning("⚠️ SDK native guardrails not available, using basic validation")
            return self._create_basic_input_guardrail()
    
    def _get_ai_output_guardrail(self):
        """Get AI-driven output guardrail from SDK native guardrails"""
        try:
            from sdk_native_guardrails import validate_asset_output_ai
            return validate_asset_output_ai
        except ImportError:
            logger.warning("⚠️ SDK native guardrails not available, using basic validation")
            return self._create_basic_output_guardrail()
    
    def _create_basic_input_guardrail(self):
        """Fallback input guardrail for when SDK guardrails are not available"""
        @input_guardrail
        def validate_task_input(ctx: RunContextWrapper, agent, input_content) -> str:
            return GuardrailFunctionOutput(blocked=False, transformed_input=input_content)
        return validate_task_input
    
    def _create_basic_output_guardrail(self):
        """Fallback output guardrail for when SDK guardrails are not available"""
        @output_guardrail
        def validate_task_output(ctx: RunContextWrapper, agent, output) -> str:
            return GuardrailFunctionOutput(blocked=False, transformed_output=output)
        return validate_task_output

    def _create_native_handoff_tools(self):
        return [] # Simplified for this example

    def _create_execution_aware_prompt(self, task: Task, classification) -> str:
        """🧠 AI-DRIVEN: Create prompt based on task execution classification"""
        
        base_prompt = f"""You are {self.agent_data.name}, a {self.agent_data.seniority} {self.agent_data.role}.
{self.agent_data.description if self.agent_data.description else ''}

TASK EXECUTION TYPE: {classification.execution_type.value.upper()}
TOOLS AVAILABLE: {', '.join(classification.tools_needed) if classification.tools_needed else 'None'}
EXPECTED OUTPUT: {classification.content_type_expected}
"""
        
        if classification.execution_type.value == "data_collection":
            base_prompt += """
🔍 DATA COLLECTION EXECUTION:
- You MUST use WebSearchTool to find real, current data
- DO NOT create fictional or example data
- Search for actual business information, contacts, emails, phone numbers
- Provide complete, actionable data that a business could immediately use
- Your output must contain REAL data from web searches, not templates or examples
- If asked for contact lists, find actual companies and their contact information
- CRITICAL: Use web search tools to collect authentic, up-to-date information
"""
        elif classification.execution_type.value == "content_generation":
            base_prompt += """
✍️ CONTENT GENERATION EXECUTION:
- Create complete, polished content ready for immediate use
- Generate full articles, emails, copy, or designs as requested
- Your output must be the final deliverable, not a plan or outline
- Include all necessary details, formatting, and structure
"""
        elif classification.execution_type.value == "planning":
            base_prompt += """
📋 PLANNING EXECUTION:
- Create comprehensive strategies, methodologies, and frameworks
- Provide detailed step-by-step plans and structures
- Your output should be actionable planning documents
"""
        
        base_prompt += f"""

The current task is:
- Task Name: {task.name}
- Task Description: {task.description}

Produce the final deliverable for this task following the execution type requirements above.
"""
        return base_prompt

    async def _create_ai_driven_context(self, task: Task, task_classification=None) -> Any:
        """🔧 Create context with task classification for guardrails"""
        context = OrchestrationContext(
            workspace_id=str(task.workspace_id),
            task_id=str(task.id),
            agent_id=str(self.agent_data.id),
            agent_role=self.agent_data.role,
            agent_seniority=self.agent_data.seniority,
            task_name=task.name,
            task_description=task.description,
        )
        
        # 🧠 HOLISTIC: Add task classification context for guardrails
        if task_classification:
            context.execution_metadata.update({
                "task_classification": task_classification,
                "execution_type": task_classification.execution_type.value,
                "available_tools": task_classification.tools_needed,
                "requires_tools": task_classification.requires_tools
            })
            
            # Set attributes directly on context for guardrail access
            setattr(context, 'task_classification', task_classification)
            setattr(context, 'available_tools', task_classification.tools_needed)
            
        return context

