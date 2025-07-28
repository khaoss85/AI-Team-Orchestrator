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

# Import SDK components
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
    SDK_AVAILABLE = True
    logger.info("✅ OpenAI Agents SDK loaded successfully with trace configuration")
except ImportError:
    SDK_AVAILABLE = False
    logger.warning("OpenAI Agents SDK not available - using minimal fallback")

from models import Agent as AgentModel, Task, TaskStatus, TaskExecutionOutput, AgentStatus
from pydantic import BaseModel
from typing import Any

# Orchestration Context Model
class OrchestrationContext(BaseModel):
    """Pydantic model for orchestration context with SDK RunContextWrapper"""
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

# Enhanced TaskExecutionOutput with additional fields for compatibility
class EnhancedTaskExecutionOutput(TaskExecutionOutput):
    summary: Optional[str] = None
    structured_content: Optional[str] = None

from database import update_agent_status

# Import orchestrators for pillar compliance
try:
    from services.unified_memory_engine import unified_memory_engine
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    logger.warning("Memory system not available")

try:
    from ai_quality_assurance.unified_quality_engine import unified_quality_engine
    QUALITY_AVAILABLE = True
except ImportError:
    QUALITY_AVAILABLE = False
    logger.warning("Quality engine not available")


class SpecialistAgent:
    """
    Enhanced SpecialistAgent that combines stability with advanced features
    
    Key improvements:
    1. Asset-oriented output (Pillar 12)
    2. Tool integration (Pillar 14)
    3. Memory system hooks (Pillar 6)
    4. Quality validation (Pillar 8)
    5. Simple, focused prompts (prevent hanging)
    """
    
    def __init__(self, agent_data: AgentModel, all_workspace_agents_data: List[AgentModel] = None):
        logger.info(f"🔍 SpecialistAgent __init__ called with agent_data type: {type(agent_data)}")
        logger.info(f"🔍 all_workspace_agents_data type: {type(all_workspace_agents_data)}")
        self.agent_data = agent_data
        self.all_workspace_agents_data = all_workspace_agents_data or []
        logger.info(f"🔍 About to call _initialize_tools()")
        self.tools = self._initialize_tools()
        logger.info(f"🔍 _initialize_tools() completed")
        
        # Initialize handoffs separately from tools
        if SDK_AVAILABLE and self.all_workspace_agents_data:
            self.handoffs = self._create_native_handoff_tools()
            logger.info(f"🔍 Created {len(self.handoffs)} handoff tools")
        else:
            self.handoffs = []
        
        # Initialize guardrails - temporarily disabled due to API changes
        # if SDK_AVAILABLE:
        #     self.input_guardrail = self._create_input_guardrail()
        #     self.output_guardrail = self._create_output_guardrail()
        # else:
        self.input_guardrail = None
        self.output_guardrail = None
        
    def _initialize_tools(self) -> List[Any]:
        """Initialize real tools for authentic content (Pillar 14)"""
        tools = []
        
        if SDK_AVAILABLE:
            # Add web search for real-time data
            try:
                tools.append(WebSearchTool())
            except Exception as e:
                logger.warning(f"WebSearchTool not available: {e}")
            
            # FileSearchTool requires vector_store_ids
            # Only add if workspace has vector stores configured
            if hasattr(self.agent_data, 'vector_store_ids') and self.agent_data.vector_store_ids:
                try:
                    tools.append(FileSearchTool(vector_store_ids=self.agent_data.vector_store_ids))
                except Exception as e:
                    logger.warning(f"FileSearchTool not available: {e}")
            
            # NOTE: Handoffs are now handled separately in self.handoffs
            # Do NOT add handoffs to regular tools to avoid SDK type errors
            
        return tools
    
    def _create_input_guardrail(self):
        """Create input guardrail for task validation"""
        @input_guardrail
        def validate_task_input(ctx: RunContextWrapper, agent, input_content) -> str:
            """Validate task input for safety and completeness"""
            # Convert input to string for validation
            if isinstance(input_content, list):
                task_input = str(input_content)
            else:
                task_input = str(input_content)
            
            # Check for potentially harmful content
            harmful_patterns = [
                "delete", "remove", "destroy", "malicious", "hack", "exploit",
                "password", "secret", "key", "token", "credentials"
            ]
            
            task_lower = task_input.lower()
            for pattern in harmful_patterns:
                if pattern in task_lower:
                    from agents import GuardrailFunctionOutput
                    return GuardrailFunctionOutput(
                        blocked=True,
                        message=f"Input contains potentially harmful content: {pattern}"
                    )
            
            # Check for minimum content length
            if len(task_input.strip()) < 10:
                from agents import GuardrailFunctionOutput
                return GuardrailFunctionOutput(
                    blocked=True,
                    message="Task input too short - please provide more details"
                )
            
            # Check for placeholder content
            placeholder_patterns = ["todo", "placeholder", "example", "sample"]
            for pattern in placeholder_patterns:
                if pattern in task_lower and len(task_input) < 50:
                    from agents import GuardrailFunctionOutput
                    return GuardrailFunctionOutput(
                        blocked=True,
                        message=f"Task appears to contain placeholder content: {pattern}"
                    )
            
            from agents import GuardrailFunctionOutput
            return GuardrailFunctionOutput(
                blocked=False,
                transformed_input=input_content
            )
        
        return validate_task_input
    
    def _create_output_guardrail(self):
        """Create output guardrail for quality validation"""
        @output_guardrail
        def validate_task_output(ctx: RunContextWrapper, agent, output) -> str:
            """Validate task output for quality and completeness"""
            # Convert output to string for validation
            task_output = str(output)
            
            # Check for minimum output length
            if len(task_output.strip()) < 20:
                from agents import GuardrailFunctionOutput
                return GuardrailFunctionOutput(
                    blocked=True,
                    message="Output too short - please provide more detailed results"
                )
            
            # Check for placeholder content
            placeholder_indicators = [
                "lorem ipsum", "placeholder", "todo", "tbd", "to be determined",
                "example", "sample", "dummy", "test", "[insert", "<insert"
            ]
            
            output_lower = task_output.lower()
            for indicator in placeholder_indicators:
                if indicator in output_lower:
                    from agents import GuardrailFunctionOutput
                    return GuardrailFunctionOutput(
                        blocked=True,
                        message=f"Output contains placeholder content: {indicator}"
                    )
            
            # Check for proper completion indicators
            completion_indicators = ["completed", "finished", "done", "result", "output", "analysis"]
            has_completion_indicator = any(indicator in output_lower for indicator in completion_indicators)
            
            if not has_completion_indicator and len(task_output) < 100:
                from agents import GuardrailFunctionOutput
                return GuardrailFunctionOutput(
                    blocked=True,
                    message="Output lacks clear completion indicators"
                )
            
            from agents import GuardrailFunctionOutput
            return GuardrailFunctionOutput(
                blocked=False,
                transformed_output=output
            )
        
        return validate_task_output
    
    def _create_native_handoff_tools(self):
        """Create native SDK handoff tools for each workspace agent"""
        handoff_tools = []
        
        for agent_data in self.all_workspace_agents_data:
            # Skip self
            if agent_data.id == self.agent_data.id:
                continue
                
            # Create handoff function with correct SDK signature
            # Sanitize role name to match OpenAI API pattern: ^[a-zA-Z0-9_-]+$
            sanitized_role = agent_data.role.lower().replace(' ', '_').replace('/', '_').replace('-', '_')
            # Remove any invalid characters
            sanitized_role = ''.join(c for c in sanitized_role if c.isalnum() or c in '_-')
            
            agent_handoff = handoff(
                agent=self._create_agent_for_handoff(agent_data),
                tool_name_override=f"handoff_to_{sanitized_role}",
                tool_description_override=f"Hand off task to {agent_data.role} ({agent_data.seniority}) - {agent_data.name}. Use when task requires {agent_data.role} expertise or {agent_data.seniority} level guidance.",
                on_handoff=self._create_handoff_callback(agent_data),
            )
            
            handoff_tools.append(agent_handoff)
            
        return handoff_tools
    
    def _create_agent_for_handoff(self, agent_data: AgentModel) -> OpenAIAgent:
        """Create agent instance for handoff target"""
        # Parse skills safely - they may be JSON strings or lists
        hard_skills = self._parse_skills_safely(agent_data.hard_skills)
        personality_traits = self._parse_skills_safely(agent_data.personality_traits)
        
        return OpenAIAgent(
            name=agent_data.name,
            instructions=f"""You are a {agent_data.seniority} {agent_data.role}.
            
Skills: {', '.join(hard_skills)}
Specialization: {personality_traits[0] if personality_traits else 'General'}
Execute tasks using your expertise. Provide concrete, actionable output.""",
            model="gpt-4o-mini"
        )
    
    def _create_handoff_callback(self, target_agent: AgentModel):
        """Create callback for handoff events"""
        async def on_handoff(ctx: RunContextWrapper):
            logger.info(f"🔄 Handoff from {self.agent_data.role} to {target_agent.role}")
            # Add any custom handoff logic here (logging, notifications, etc.)
            if hasattr(ctx.context, 'orchestration_state'):
                ctx.context.orchestration_state['last_handoff'] = {
                    'from': self.agent_data.role,
                    'to': target_agent.role,
                    'timestamp': datetime.now().isoformat()
                }
        return on_handoff
    
    def _parse_skills_safely(self, skills_data) -> List[str]:
        """Parse skills data safely - handles both JSON strings and lists"""
        if not skills_data:
            return []
            
        try:
            # If it's a string, try to parse as JSON
            if isinstance(skills_data, str):
                import json
                parsed = json.loads(skills_data)
                if isinstance(parsed, list):
                    # Extract names from skill objects
                    return [skill.get('name', str(skill)) if isinstance(skill, dict) else str(skill) for skill in parsed]
                else:
                    return [str(parsed)]
            
            # If it's already a list
            elif isinstance(skills_data, list):
                return [skill.get('name', str(skill)) if isinstance(skill, dict) else str(skill) for skill in skills_data]
            
            # Fallback for any other type
            else:
                return [str(skills_data)]
                
        except Exception as e:
            logger.warning(f"Failed to parse skills data: {e}")
            return []
    
    def _create_enhanced_prompt(self, task: Task) -> str:
        """
        Create focused prompt that includes asset formatting
        but stays simple to prevent hanging
        """
        # Detect if this is an asset production task
        is_asset_task = (
            "asset" in task.name.lower() or 
            "create" in task.name.lower() or
            task.context_data and task.context_data.get("asset_production")
        )
        
        base_prompt = f"""
# System context
You are part of a multi-agent system called the Agents SDK, designed to make agent coordination and execution easy. Agents uses two primary abstraction: **Agents** and **Handoffs**. An agent encompasses instructions and tools and can hand off a conversation to another agent when appropriate. Handoffs are achieved by calling a handoff function, generally named `handoff_to_<agent_name>`. Transfers between agents are handled seamlessly in the background; do not mention or draw attention to these transfers in your conversation with the user.

You are a {self.agent_data.seniority} {self.agent_data.role}.
Task: {task.name}
Description: {task.description}

EXECUTION RULES - HIERARCHICAL DECISION MAKING:

🎯 **STEP 1: ANALYZE TASK SCOPE**
- If task requires CURRENT/REAL-TIME data → Use WebSearchTool FIRST
- If task requires document analysis → Use FileSearchTool FIRST  
- If task is within your core expertise → Complete it yourself with tools
- Only consider handoff after exhausting your tools and expertise

🛠️ **STEP 2: TOOL USAGE PRIORITY**
1. **WebSearchTool**: For ANY current information, market data, recent news, pricing, company info
2. **FileSearchTool**: For document analysis, internal knowledge bases
3. **Your expertise**: Apply your role knowledge to interpret and synthesize tool results
4. **Handoff**: ONLY when task fundamentally requires different professional role

❌ **NEVER HANDOFF FOR:**
- Market research (use WebSearchTool)
- Current data lookup (use WebSearchTool)  
- Technical documentation search (use WebSearchTool)
- Price/company/trend research (use WebSearchTool)
- Any information that can be searched online

✅ **HANDOFF ONLY FOR:**
- Tasks requiring fundamentally different professional expertise
- Creative work outside your domain (e.g., developer asked to design logos)
- Specialized analysis requiring different educational background

🔧 **STEP 3: EXECUTION APPROACH**
1. Use tools to gather information FIRST
2. Apply your expertise to analyze and synthesize
3. Provide concrete, actionable output with NO placeholders
4. Include sources and data from tool usage

Available handoff functions: {', '.join([f"handoff_to_{''.join(c for c in agent.role.lower().replace(' ', '_').replace('/', '_').replace('-', '_') if c.isalnum() or c in '_-')}" for agent in self.all_workspace_agents_data if agent.id != self.agent_data.id])}
"""

        if is_asset_task:
            base_prompt += """
4. Format output using these patterns for better readability:

For Tables: ## TABLE: name
| Column1 | Column2 | Column3 |
|---------|---------|---------|
| Data    | Data    | Data    |
## END_TABLE

For Cards: ## CARD: type
TITLE: Main Title
CONTENT: Details
ACTION: Call to action
## END_CARD

5. Include both structured_content and rendered output
"""

        base_prompt += """
🏁 **FINAL OUTPUT REQUIREMENTS:**
{
    "task_id": "TASK_ID",
    "status": "completed", 
    "summary": "What you accomplished",
    "result": "Your concrete output with sources",
    "tools_used": ["WebSearchTool", "FileSearchTool", etc.],
    "structured_content": "Optional: formatted content"
}

⚠️ **VALIDATION CHECKLIST:**
- [ ] Did I use appropriate tools for data gathering?
- [ ] Did I provide sources/URLs when using WebSearchTool?
- [ ] Is my output based on real data, not assumptions?
- [ ] Did I avoid unnecessary handoffs for tasks within my capability?
"""
        
        return base_prompt.strip()
        
    async def execute(self, task: Task, session: Optional[Any] = None) -> TaskExecutionOutput:
        """Execute task with all pillar integrations"""
        logger.info(f"🚀 Enhanced execution for task {task.id}")
        
        try:
            # Update agent status
            await update_agent_status(str(self.agent_data.id), AgentStatus.BUSY.value)
            
            if not SDK_AVAILABLE:
                raise Exception("OpenAI Agents SDK required for enhanced execution")
            
            # Create orchestration context
            orchestration_context = OrchestrationContext(
                workspace_id=str(task.workspace_id),
                task_id=str(task.id),
                agent_id=str(self.agent_data.id),
                agent_role=self.agent_data.role,
                agent_seniority=self.agent_data.seniority,
                task_name=task.name,
                task_description=task.description,
                execution_metadata={
                    "started_at": datetime.now().isoformat(),
                    "agent_name": self.agent_data.name,
                    "model": "gpt-4o-mini"
                },
                available_agents=[
                    {
                        "id": str(agent.id),
                        "name": agent.name,
                        "role": agent.role,
                        "seniority": agent.seniority,
                        "skills": [skill.get('name', '') for skill in (agent.hard_skills or [])]
                    }
                    for agent in self.all_workspace_agents_data
                ],
                orchestration_state={"execution_phase": "starting"}
            )
            
            # Create agent with enhanced prompt and guardrails
            agent_config = {
                "name": self.agent_data.name,
                "instructions": self._create_enhanced_prompt(task),
                "model": "gpt-4o-mini",  # Faster model for better performance
                "tools": self.tools
            }
            
            # Add handoffs separately (SDK requires separate parameter)
            if hasattr(self, 'handoffs') and self.handoffs:
                agent_config["handoffs"] = self.handoffs
                logger.info(f"🔄 Adding {len(self.handoffs)} handoffs to agent configuration")
            
            # Add guardrails if available
            if self.input_guardrail:
                agent_config["input_guardrails"] = [self.input_guardrail]
            if self.output_guardrail:
                agent_config["output_guardrails"] = [self.output_guardrail]
            
            agent = OpenAIAgent(**agent_config)
            
            # Configure OpenAI Trace if enabled
            trace_enabled = os.getenv('OPENAI_TRACE', 'false').lower() == 'true'
            if trace_enabled:
                logger.info(f"🔍 OpenAI Trace enabled for specialist task execution - Task ID: {task.id}")
                logger.info(f"🔍 Trace config: SAMPLE_RATE={os.getenv('OPENAI_TRACE_SAMPLE_RATE', '1.0')}, INCLUDE_SYSTEM={os.getenv('OPENAI_TRACE_INCLUDE_SYSTEM', 'true')}, INCLUDE_TOOLS={os.getenv('OPENAI_TRACE_INCLUDE_TOOLS', 'true')}")
            else:
                logger.warning(f"⚠️ OpenAI Trace NOT enabled for task {task.id} - OPENAI_TRACE={os.getenv('OPENAI_TRACE', 'false')}")
            
            # Execute with Runner.run (with trace enabled)
            start_time = time.time()
            logger.info(f"🚀 Starting Runner.run for task {task.id} with trace_enabled={trace_enabled}")
            
            # Run agent with OpenAI SDK and trace - pass context properly
            run_result = await Runner.run(
                starting_agent=agent,
                input=str(task.model_dump()),
                context=orchestration_context,
                max_turns=5
            )
            
            execution_time = time.time() - start_time
            logger.info(f"✅ Runner.run completed for task {task.id} in {execution_time:.2f}s")
            
            if not run_result.final_output:
                raise ValueError("No output from agent")
            
            # Use RunResult.new_items instead of manual parsing
            result_content = str(run_result.final_output)
            structured_content = None
            summary = "Task completed"
            
            # Process new_items from RunResult for enhanced output
            if hasattr(run_result, 'new_items') and run_result.new_items:
                # Extract structured data from new_items
                items_data = []
                for item in run_result.new_items:
                    if hasattr(item, 'content'):
                        items_data.append(str(item.content))
                    elif hasattr(item, 'data'):
                        items_data.append(str(item.data))
                    else:
                        items_data.append(str(item))
                
                if items_data:
                    structured_content = json.dumps({
                        "items": items_data,
                        "item_count": len(items_data),
                        "execution_context": {
                            "agent_role": self.agent_data.role,
                            "task_name": task.name
                        }
                    }, indent=2)
                    summary = f"Task completed with {len(items_data)} output items"
            
            # Fallback to JSON parsing if needed
            try:
                result_data = json.loads(result_content)
                if isinstance(result_data, dict):
                    result_content = result_data.get("result", result_content)
                    summary = result_data.get("summary", summary)
                    if not structured_content:
                        structured_content = json.dumps(result_data, indent=2)
            except:
                # Keep original content if not JSON
                pass
            
            # Ensure result_content is always a string
            if isinstance(result_content, (dict, list)):
                result_content = json.dumps(result_content, indent=2)
            elif not isinstance(result_content, str):
                result_content = str(result_content)
                
            output = EnhancedTaskExecutionOutput(
                task_id=task.id,
                status=TaskStatus.COMPLETED,
                result=result_content,
                execution_time=execution_time,
                summary=summary,
                structured_content=structured_content
            )
            
            # PILLAR 6: Save to memory system
            await self._save_to_memory(task, output)
            
            # PILLAR 8: Quality validation
            await self._validate_quality(task, output)
            
            logger.info(f"✅ Task {task.id} completed in {execution_time:.2f}s")
            return output
            
        except Exception as e:
            logger.error(f"❌ Task {task.id} failed: {e}")
            
            # Save failure to memory
            if MEMORY_AVAILABLE:
                await self._save_failure_lesson(task, str(e))
            
            return EnhancedTaskExecutionOutput(
                task_id=task.id,
                status=TaskStatus.FAILED,
                error_message=str(e),
                execution_time=0,
                summary=f"Task failed: {str(e)}"
            )
        finally:
            try:
                await update_agent_status(str(self.agent_data.id), AgentStatus.AVAILABLE.value)
            except:
                pass
    
    async def _save_to_memory(self, task: Task, output: TaskExecutionOutput):
        """Save execution insights to memory (Pillar 6)"""
        if not MEMORY_AVAILABLE:
            return
            
        try:
            # Extract insight based on result
            insight_type = "success_pattern" if output.status == TaskStatus.COMPLETED else "failure_lesson"
            
            # Use correct API parameters
            await unified_memory_engine.store_insight(
                workspace_id=str(task.workspace_id),
                insight_type=insight_type,
                content=output.summary or 'Task processed',
                relevance_tags=[self.agent_data.role, task.name],
                metadata={
                    "task_name": task.name,
                    "agent_role": self.agent_data.role,
                    "execution_time": output.execution_time
                }
            )
            
            logger.info(f"💾 Saved {insight_type} to memory")
            
        except Exception as e:
            logger.warning(f"Failed to save to memory: {e}")
    
    async def _validate_quality(self, task: Task, output: TaskExecutionOutput):
        """Validate output quality (Pillar 8)"""
        if not QUALITY_AVAILABLE or output.status != TaskStatus.COMPLETED:
            return
            
        try:
            # Use correct API - validate_asset_quality instead of validate_output
            validation_result = await unified_quality_engine.validate_asset_quality(
                asset_content=output.result,
                asset_type="task_output",
                workspace_id=str(task.workspace_id),
                domain_context=task.name
            )
            
            if hasattr(validation_result, 'needs_enhancement') and validation_result.needs_enhancement:
                logger.warning(f"⚠️ Output needs quality enhancement: {getattr(validation_result, 'reason', 'Quality check failed')}")
            elif isinstance(validation_result, dict) and validation_result.get("needs_enhancement"):
                logger.warning(f"⚠️ Output needs quality enhancement: {validation_result.get('reason')}")
            else:
                logger.info("✅ Quality validation passed")
                # Quality engine will handle enhancement automatically
                
        except Exception as e:
            logger.warning(f"Quality validation failed: {e}")
    
    async def _save_failure_lesson(self, task: Task, error: str):
        """Save failure lesson to prevent repetition"""
        if not MEMORY_AVAILABLE:
            return
            
        try:
            # Use correct API parameters
            await unified_memory_engine.store_insight(
                workspace_id=str(task.workspace_id),
                insight_type="failure_lesson",
                content=f"Task failed with error: {error}",
                relevance_tags=[self.agent_data.role, "error"],
                metadata={
                    "task_name": task.name,
                    "agent_role": self.agent_data.role,
                    "error": error
                }
            )
            
        except Exception as e:
            logger.warning(f"Failed to save failure lesson: {e}")