
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
from pydantic import BaseModel

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

# Import shared document manager for specialist assistant integration
try:
    from services.shared_document_manager import shared_document_manager
    SHARED_DOCUMENTS_AVAILABLE = True
    logger.info("✅ Shared Document Manager available for specialist agents")
except ImportError:
    SHARED_DOCUMENTS_AVAILABLE = False
    logger.warning("⚠️ Shared Document Manager not available - specialists will not have document access")

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
        
        # Initialize document access
        self._specialist_assistant_id = None
        if SHARED_DOCUMENTS_AVAILABLE:
            asyncio.create_task(self._initialize_document_assistant())

    async def _initialize_document_assistant(self):
        """Initialize OpenAI Assistant for document access"""
        try:
            if not SHARED_DOCUMENTS_AVAILABLE:
                return
            
            # Create specialist assistant with document access
            workspace_id = str(self.agent_data.workspace_id)
            agent_id = str(self.agent_data.id)
            
            # Build agent config for assistant creation
            agent_config = {
                'role': self.agent_data.role,
                'name': self.agent_data.name,
                'skills': getattr(self.agent_data, 'skills', []),
                'seniority': self.agent_data.seniority,
                'preferred_model': 'gpt-4-turbo-preview',
                'temperature': 0.3
            }
            
            # Create or get existing specialist assistant
            assistant_id = await shared_document_manager.get_specialist_assistant_id(workspace_id, agent_id)
            
            if not assistant_id:
                # Create new specialist assistant
                assistant_id = await shared_document_manager.create_specialist_assistant(
                    workspace_id, agent_id, agent_config
                )
                
                if assistant_id:
                    logger.info(f"✅ Created document assistant {assistant_id} for specialist {self.agent_data.name}")
                    self._specialist_assistant_id = assistant_id
                else:
                    logger.warning(f"Could not create document assistant for specialist {self.agent_data.name}")
            else:
                logger.info(f"✅ Retrieved existing assistant {assistant_id} for specialist {self.agent_data.name}")
                self._specialist_assistant_id = assistant_id
                
        except Exception as e:
            logger.error(f"Failed to initialize document assistant: {e}")
            self._specialist_assistant_id = None
    
    def has_document_access(self) -> bool:
        """Check if this specialist has access to workspace documents"""
        return SHARED_DOCUMENTS_AVAILABLE and self._specialist_assistant_id is not None
    
    async def search_workspace_documents(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search workspace documents using the specialist's assistant
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of search results with content and metadata
        """
        if not self.has_document_access():
            return []
        
        try:
            # Use the shared document manager to search via assistant
            from services.openai_assistant_manager import OpenAIAssistantManager
            assistant_mgr = OpenAIAssistantManager()
            
            # Create temporary thread for search
            thread = assistant_mgr.client.beta.threads.create()
            
            # Add search message
            assistant_mgr.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"Search for: {query}"
            )
            
            # Run the search
            run = assistant_mgr.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self._specialist_assistant_id,
                tools=[{"type": "file_search"}],
                tool_resources={
                    "file_search": {
                        "max_num_results": max_results
                    }
                }
            )
            
            # Wait for completion
            import time
            while run.status in ["queued", "in_progress", "requires_action"]:
                time.sleep(0.5)
                run = assistant_mgr.client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
            
            if run.status == "completed":
                # Get messages
                messages = assistant_mgr.client.beta.threads.messages.list(
                    thread_id=thread.id
                )
                
                # Extract search results
                results = []
                for message in messages:
                    if message.role == "assistant":
                        for content in message.content:
                            if content.type == "text":
                                # Parse citations if present
                                annotations = getattr(content.text, 'annotations', [])
                                for annotation in annotations:
                                    if annotation.type == "file_citation":
                                        results.append({
                                            "content": annotation.text,
                                            "file_id": annotation.file_citation.file_id,
                                            "quote": annotation.file_citation.quote
                                        })
                                
                                # Also include the main response
                                if not results and content.text.value:
                                    results.append({
                                        "content": content.text.value,
                                        "source": "assistant_response"
                                    })
                
                return results[:max_results]
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to search workspace documents: {e}")
            return []

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
            
            # 🔧 CRITICAL FIX: Add tools to Runner.run() for OpenAI Dashboard tracing
            # Generate unique trace ID for this execution
            import uuid
            trace_id = f"task_{task.id}_{uuid.uuid4().hex[:8]}"
            
            run_params = {
                "starting_agent": agent,
                "input": execution_input,
                "context": context_data,
                "session": session,
                "max_turns": 8 if task_classification.requires_tools else 5,
                "tools": execution_tools,  # CRITICAL: Tools must be passed to Runner for tracing
                "metadata": {
                    "trace_id": trace_id,
                    "task_id": str(task.id),
                    "workspace_id": str(task.workspace_id),
                    "agent_name": self.agent_data.name,
                    "agent_role": self.agent_data.role,
                    "execution_type": task_classification.execution_type.value,
                    "tools_count": len(execution_tools),
                    "handoffs_available": len(self.handoffs)
                }
            }
            
            logger.info(f"🔧 Runner configured with {len(execution_tools)} tools for OpenAI tracing")
            logger.info(f"📊 Trace ID: {trace_id}")
            if execution_tools:
                tool_names = [getattr(tool, '__name__', type(tool).__name__) for tool in execution_tools]
                logger.info(f"   Tools available: {', '.join(tool_names)}")
            if self.handoffs:
                logger.info(f"   Handoffs available: {len(self.handoffs)} agents")
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
        """Save task execution results to workspace memory for learning"""
        try:
            if memory_engine:
                memory_data = {
                    "task_id": str(task.id),
                    "task_name": task.name,
                    "task_description": task.description,
                    "agent_role": self.agent_data.role,
                    "agent_seniority": self.agent_data.seniority,
                    "execution_time": getattr(output, 'execution_time', 0),
                    "status": output.status.value if hasattr(output.status, 'value') else str(output.status),
                    "result_summary": getattr(output, 'summary', ''),
                    "workspace_id": str(task.workspace_id)
                }
                
                await memory_engine.store_task_execution_memory(memory_data)
                logger.info(f"✅ Saved task {task.id} execution to workspace memory")
        except Exception as e:
            logger.warning(f"Failed to save task execution to memory: {e}")

    async def _validate_quality(self, task: Task, output: TaskExecutionOutput, quality_engine):
        """Validate task output quality using AI-driven quality engine"""
        try:
            if quality_engine:
                quality_criteria = {
                    "task_type": "task_execution",
                    "expected_format": "structured_output",
                    "content_requirements": {
                        "min_length": 50,
                        "should_be_actionable": True,
                        "should_contain_real_data": True
                    },
                    "agent_context": {
                        "role": self.agent_data.role,
                        "seniority": self.agent_data.seniority
                    }
                }
                
                quality_result = await quality_engine.validate_task_output(
                    output.result, quality_criteria
                )
                
                if hasattr(quality_result, 'quality_score') and quality_result.quality_score < 0.7:
                    logger.warning(f"Task {task.id} quality score: {quality_result.quality_score}")
                else:
                    logger.info(f"✅ Task {task.id} passed quality validation")
                    
        except Exception as e:
            logger.warning(f"Failed to validate task quality: {e}")
        
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
                from utils.openai_client_factory_enhanced import get_enhanced_async_openai_client
                workspace_id = str(getattr(self, 'agent_data', {}).workspace_id or getattr(self, 'workspace_id', ''))
                client = get_enhanced_async_openai_client(workspace_id=workspace_id)
                
                response = await client.chat.completions.create(
                    model="gpt-4o-mini",
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
        
        # AI-driven placeholder detection instead of hardcoded keywords
        try:
            from utils.openai_client_factory_enhanced import get_enhanced_async_openai_client
            workspace_id = str(getattr(self, 'agent_data', {}).workspace_id or getattr(self, 'workspace_id', ''))
            client = get_enhanced_async_openai_client(workspace_id=workspace_id)
            
            placeholder_detection_prompt = f"""
            Analyze this output for placeholder or template content:
            
            OUTPUT TO ANALYZE:
            {output}
            
            Determine if this contains:
            1. Real, specific business data (actual company names, real email addresses, phone numbers)
            2. Placeholder/template data (generic examples, template text, fake data)
            
            Respond with JSON: {{"contains_placeholders": true/false, "placeholder_examples": ["list", "of", "examples"], "confidence": 0.0-1.0, "reasoning": "explanation"}}
            """
            
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at detecting placeholder, template, or fake data in business content. Analyze carefully for real vs. example data."
                    },
                    {
                        "role": "user", 
                        "content": placeholder_detection_prompt
                    }
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            import json
            placeholder_result = json.loads(response.choices[0].message.content)
            
            if placeholder_result.get("contains_placeholders", False) and placeholder_result.get("confidence", 0) > 0.7:
                logger.warning(f"🤖 AI detected placeholder content (confidence: {placeholder_result.get('confidence', 0):.2f})")
                
                enhanced_output = f"""
⚠️ AI ANALYSIS: This output contains placeholder/template data and needs enhancement with real data.

AI CONFIDENCE: {placeholder_result.get('confidence', 0):.2f}
PLACEHOLDER EXAMPLES: {', '.join(placeholder_result.get('placeholder_examples', []))}
REASONING: {placeholder_result.get('reasoning', 'Content appears to contain template data')}

ORIGINAL OUTPUT:
{output}

NEXT STEPS REQUIRED:
- Use WebSearchTool to find actual companies and contacts
- Replace all placeholder data with real business information
- Collect authentic contact details from web sources
"""
                return enhanced_output
                
        except Exception as e:
            logger.warning(f"AI placeholder detection failed, using basic validation: {e}")
            # Basic fallback check for obvious placeholders
            output_lower = output.lower()
            basic_indicators = ["example", "placeholder", "template", "xxx", "todo", "tbd", "sample"]
            basic_count = sum(1 for indicator in basic_indicators if indicator in output_lower)
            
            if basic_count > 2:
                logger.warning(f"⚠️ Basic validation detected {basic_count} placeholder indicators")
                return f"""
⚠️ VALIDATION: Output may contain placeholder data.

ORIGINAL OUTPUT:
{output}

RECOMMENDATION: Verify output contains real business data instead of examples or templates.
"""
        
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
                    """Dynamically created MCP tool wrapper with real endpoint calls"""
                    try:
                        # Import MCP client for real endpoint calls
                        from services.mcp_client import MCPClient
                        
                        # Create MCP client instance
                        mcp_client = MCPClient()
                        
                        # Call the actual MCP endpoint
                        result = mcp_client.call_tool(
                            tool_name=mcp_tool["name"],
                            parameters=kwargs,
                            endpoint=mcp_tool.get("endpoint"),
                            method=mcp_tool.get("method", "POST")
                        )
                        
                        return {
                            "tool_name": mcp_tool["name"],
                            "result": result,
                            "source": "mcp_endpoint",
                            "success": True,
                            "endpoint": mcp_tool.get("endpoint"),
                            "parameters_sent": kwargs
                        }
                    except ImportError:
                        # Fallback for when MCP client is not available
                        logger.warning(f"MCP client not available for tool '{mcp_tool['name']}' - using fallback")
                        return {
                            "tool_name": mcp_tool["name"],
                            "result": f"Tool '{mcp_tool['name']}' requires MCP client integration",
                            "source": "fallback_unavailable",
                            "success": False,
                            "error": "MCP client not configured"
                        }
                    except Exception as e:
                        return {
                            "tool_name": mcp_tool["name"],
                            "error": str(e),
                            "source": "mcp_endpoint_error",
                            "success": False,
                            "endpoint": mcp_tool.get("endpoint")
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

    class HandoffInput(BaseModel):
        """Structured input for handoff operations"""
        reason: str
        task_context: str = ""
        priority: str = "normal"

    def _get_or_create_agent_instance(self, agent_data):
        """Get or create Agent instance for handoffs with proper caching"""
        agent_key = f"{agent_data.id}_{agent_data.name}"
        
        if not hasattr(self, '_agent_cache'):
            self._agent_cache = {}
        
        if agent_key not in self._agent_cache:
            self._agent_cache[agent_key] = OpenAIAgent(
                name=agent_data.name,
                instructions=f"You are {agent_data.name}, a {agent_data.seniority} {agent_data.role}. "
                            f"{agent_data.description if agent_data.description else ''}",
                model="gpt-4o-mini"
            )
        
        return self._agent_cache[agent_key]

    def _create_native_handoff_tools(self):
        """Create SDK-native handoff tools for agent collaboration"""
        if not SDK_AVAILABLE:
            return []
            
        handoffs = []
        
        # Get available agents for this workspace (excluding self)
        try:
            available_agents = getattr(self, 'all_workspace_agents_data', [])
            if not available_agents:
                logger.warning(f"No workspace agents available for handoffs for agent {self.agent_data.name}")
                return []
            
            for agent_data in available_agents:
                if str(agent_data.id) != str(self.agent_data.id):  # Don't handoff to self
                    agent_name_safe = agent_data.name.replace(' ', '_').lower().replace('-', '_')
                    
                    # Create proper Agent instance for handoff
                    target_agent = self._get_or_create_agent_instance(agent_data)
                    
                    # Create handoff callback with comprehensive tracing and error handling
                    def create_handoff_callback(agent_data=agent_data):
                        async def on_handoff(ctx: RunContextWrapper, input_data: Optional['SpecialistAgent.HandoffInput'] = None):
                            """Production-ready handoff callback with comprehensive tracing"""
                            try:
                                workspace_id = str(getattr(self.agent_data, 'workspace_id', '') or getattr(self, 'workspace_id', ''))
                                
                                handoff_metadata = {
                                    "handoff_id": f"handoff_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{agent_data.id[:8]}",
                                    "source_agent_id": str(self.agent_data.id),
                                    "source_agent_name": self.agent_data.name,
                                    "source_agent_role": self.agent_data.role,
                                    "source_agent_seniority": self.agent_data.seniority,
                                    "target_agent_id": str(agent_data.id),
                                    "target_agent_name": agent_data.name,
                                    "target_agent_role": agent_data.role,
                                    "target_agent_seniority": agent_data.seniority,
                                    "handoff_reason": getattr(input_data, 'reason', 'Task delegation') if input_data else "Task delegation",
                                    "task_context": getattr(input_data, 'task_context', '') if input_data else "",
                                    "priority": getattr(input_data, 'priority', 'normal') if input_data else "normal",
                                    "timestamp": datetime.now().isoformat(),
                                    "workspace_id": workspace_id,
                                    "handoff_type": "specialist_to_specialist",
                                    "trace_context": {
                                        "run_id": getattr(ctx, 'run_id', None) if ctx else None,
                                        "session_id": getattr(ctx, 'session_id', None) if ctx else None
                                    }
                                }
                                
                                logger.info(f"🤝 HANDOFF INITIATED: {agent_data.name} ({agent_data.role})")
                                logger.info(f"   Handoff ID: {handoff_metadata['handoff_id']}")
                                logger.info(f"   Reason: {handoff_metadata['handoff_reason']}")
                                logger.info(f"   Context: {handoff_metadata.get('task_context', 'None')[:100]}...")
                                
                                # Enhanced context metadata for OpenAI Dashboard tracing
                                if ctx:
                                    try:
                                        # Add handoff metadata to context
                                        if hasattr(ctx, 'add_metadata'):
                                            ctx.add_metadata("handoff_details", handoff_metadata)
                                        
                                        # Add handoff event to context data
                                        if hasattr(ctx, 'data') and isinstance(ctx.data, dict):
                                            if 'handoff_history' not in ctx.data:
                                                ctx.data['handoff_history'] = []
                                            ctx.data['handoff_history'].append(handoff_metadata)
                                            
                                        # Set handoff flags for tracing
                                        if hasattr(ctx, 'set_flag'):
                                            ctx.set_flag('handoff_active', True)
                                            ctx.set_flag('handoff_target', agent_data.name)
                                            
                                    except Exception as ctx_error:
                                        logger.warning(f"Failed to add handoff metadata to context: {ctx_error}")
                                
                                # Store handoff in workspace memory for analytics
                                try:
                                    from services.unified_memory_engine import unified_memory_engine
                                    if unified_memory_engine:
                                        await unified_memory_engine.store_handoff_event(handoff_metadata)
                                        logger.debug(f"📝 Handoff event stored in memory: {handoff_metadata['handoff_id']}")
                                except Exception as memory_error:
                                    logger.warning(f"Failed to store handoff in memory: {memory_error}")
                                    
                                return handoff_metadata
                                
                            except Exception as e:
                                logger.error(f"Handoff callback failed: {e}")
                                # Return basic metadata even on failure
                                return {
                                    "handoff_id": f"failed_handoff_{datetime.now().timestamp()}",
                                    "error": str(e),
                                    "target_agent_name": agent_data.name,
                                    "source_agent_name": self.agent_data.name
                                }
                        
                        return on_handoff
                    
                    # Create SDK-compliant handoff
                    handoff_obj = handoff(
                        agent=target_agent,
                        tool_name_override=f"handoff_to_{agent_name_safe}",
                        tool_description_override=f"Hand off current task to {agent_data.name} ({agent_data.role}) - {agent_data.seniority} level specialist. Use this when the task requires expertise outside your domain.",
                        on_handoff=create_handoff_callback(),
                        input_type=self.HandoffInput
                    )
                    
                    handoffs.append(handoff_obj)
                    
            logger.info(f"✅ Created {len(handoffs)} SDK-compliant handoff tools for agent {self.agent_data.name}")
            return handoffs
            
        except Exception as e:
            logger.error(f"Failed to create handoff tools: {e}")
            return []

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

