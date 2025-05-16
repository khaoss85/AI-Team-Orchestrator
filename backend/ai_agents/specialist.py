# backend/ai_agents/specialist.py
import logging
import os
import json
import asyncio
import contextlib # Per il dummy async context manager
from typing import List, Dict, Any, Optional, Union, Literal, TypeVar, Generic, Type
from uuid import UUID # Tipo comune per ID, anche se non generati qui
from datetime import datetime
from enum import Enum

# IMPORT COMPATIBILI SDK v0.0.15 + Fallback
try:
    from agents import (
        Agent as OpenAIAgent,
        Runner,
        AgentOutputSchema,
        ModelSettings,
        function_tool,
        WebSearchTool,
        FileSearchTool,
        RunContextWrapper,
        handoff,
        trace,
        gen_trace_id
    )
    from agents.extensions import handoff_filters, handoff_prompt
    from agents.exceptions import MaxTurnsExceeded, AgentsException, UserError
    SDK_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("Using 'agents' SDK v0.0.15+ features.")
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("Failed to import from 'agents' SDK. Attempting fallback to 'openai_agents'. Some features like native handoffs might be unavailable.")
    SDK_AVAILABLE = False
    # Fallback per funzionalità SDK mancanti
    from openai_agents import (
        Agent as OpenAIAgent, Runner, AgentOutputSchema, ModelSettings,
        function_tool, WebSearchTool, FileSearchTool
    )
    MaxTurnsExceeded = Exception 
    AgentsException = Exception
    UserError = Exception
    handoff_filters = None 
    handoff_prompt = type('HandoffPrompt', (), {'RECOMMENDED_PROMPT_PREFIX': ''})()
    def handoff(target_agent, tool_description_override=None, input_filter=None):
        logger.warning("SDK handoff called but SDK not fully available. This handoff will not function.")
        return None
    def gen_trace_id(): return f"fallback_trace_id_{datetime.now().timestamp()}"
    # Dummy trace context manager definito sotto

from pydantic import BaseModel, Field, ConfigDict

from models import (
    Agent as AgentModelPydantic,
    AgentStatus,
    AgentHealth, # Definisce la struttura per health updates
    HealthStatus, # Definisce la struttura per health updates
    Task,
    TaskStatus,
    AgentSeniority
)
from database import ( # Assicurarsi che queste funzioni di DB accettino keyword arguments come usate
    update_agent_status,
    update_task_status,
    create_task as db_create_task,
    list_agents as db_list_agents,
    list_tasks as db_list_tasks,
)

# Dummy async context manager per il fallback di 'trace'
@contextlib.asynccontextmanager
async def _dummy_async_context_manager():
    """A dummy asynchronous context manager that does nothing."""
    yield

if not SDK_AVAILABLE:
    def trace(workflow_name, trace_id, group_id=None):
        logger.warning("SDK trace called but SDK not fully available. Using dummy context manager.")
        return _dummy_async_context_manager()

TOKEN_COSTS = {
    "gpt-4.1":       {"input": 0.03   / 1000, "output": 0.06   / 1000},
    "gpt-4.1-mini":  {"input": 0.015  / 1000, "output": 0.03   / 1000},
    "gpt-4.1-nano":  {"input": 0.01   / 1000, "output": 0.02   / 1000},
    "gpt-4-turbo":   {"input": 0.01   / 1000, "output": 0.03   / 1000},
    "gpt-3.5-turbo": {"input": 0.0005 / 1000, "output": 0.0015 / 1000},
}

class TaskExecutionOutput(BaseModel):
    task_id: str
    status: Literal["completed", "failed", "requires_handoff"] = "completed"
    summary: str
    detailed_results_json: Optional[str] = Field(None, description="Detailed structured results serialized as JSON string. Should be valid JSON.")
    next_steps: Optional[List[str]] = Field(None, description="Suggested next actions or follow-up tasks.")
    suggested_handoff_target_role: Optional[str] = Field(None, description="Role to hand off to if required (used if status is 'requires_handoff').")
    resources_consumed_json: Optional[str] = Field(None, description="Resource usage serialized as JSON string (e.g. tokens). Should be valid JSON.")
    model_config = ConfigDict(extra="forbid")

class CapabilityVerificationOutput(BaseModel):
    verification_status: Literal["passed", "failed"]
    available_tools: List[str]
    model_being_used: str
    missing_requirements: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    notes: Optional[str] = None
    model_config = ConfigDict(extra="forbid")

class TaskCreationOutput(BaseModel):
    success: bool
    task_id: Optional[str] = None
    task_name: str
    assigned_agent_name: Optional[str] = None
    error_message: Optional[str] = None
    model_config = ConfigDict(extra="forbid")

class HandoffRequestOutput(BaseModel):
    success: bool
    message: str
    handoff_task_id: Optional[str] = None
    assigned_to_agent_name: Optional[str] = None
    model_config = ConfigDict(extra="forbid")

T = TypeVar('T')

class SpecialistAgent(Generic[T]):
    def __init__(
        self,
        agent_data: AgentModelPydantic,
        context_type: Optional[Type[T]] = None,
        all_workspace_agents_data: Optional[List[AgentModelPydantic]] = None
    ):
        self.agent_data = agent_data
        self.context_type = context_type or dict # type: ignore
        self.all_workspace_agents_data = all_workspace_agents_data or []
        
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY not set")

        # Nomi dei tool per coerenza
        self._create_task_tool_name = "create_task_for_agent_tool"
        self._request_handoff_tool_name = "request_handoff_to_role_via_task"
        self._log_execution_tool_name = "log_execution_step"
        self._update_health_tool_name = "update_own_health_status"
        self._report_progress_tool_name = "report_task_progress"
        self._propose_custom_tool_name = "propose_custom_tool_creation"

        # Configurazioni anti-loop
        self.max_self_delegations_per_tool_call = 1 
        self.self_delegation_tool_call_count = 0 
        self.execution_timeout = 120 
        
        self.seniority_model_map = {
            AgentSeniority.JUNIOR.value:  "gpt-4.1-nano",
            AgentSeniority.SENIOR.value:  "gpt-4.1-mini", 
            AgentSeniority.EXPERT.value:  "gpt-4.1",
        }

        self.delegation_attempts_cache: Dict[str, int] = {} 
        self.max_delegation_attempts_per_task_desc = 2 
        # Nota: delegation_attempts_cache non viene resettata per ogni execute_task principale
        # per prevenire loop su sub-task identici ricorrenti.
        # Considerare una strategia di eviction (es. LRU, pulizia periodica) se la cache cresce troppo.

        self._current_task_being_processed_id: Optional[str] = None
        self._handoff_attempts_for_current_task: set = set()

        self.tools = self._initialize_tools()
        self.direct_sdk_handoffs = self._create_sdk_handoffs() if SDK_AVAILABLE else []
        self.agent = self._create_agent()

    def _create_agent(self) -> OpenAIAgent:
        llm_config = self.agent_data.llm_config or {}
        model_name = llm_config.get("model") or self.seniority_model_map.get(self.agent_data.seniority.value, "gpt-4.1-nano")
        temperature = llm_config.get("temperature", 0.3)

        is_manager_type_role = any(keyword in self.agent_data.role.lower() 
                                for keyword in ['manager', 'coordinator', 'director', 'lead'])

        instructions = self._create_anti_loop_prompt(is_manager_type_role)

        agent_config = {
            "name": self.agent_data.name,
            "instructions": instructions,
            "model": model_name,
            "model_settings": ModelSettings(
                temperature=temperature,
                top_p=llm_config.get("top_p", 1.0),
                max_tokens=llm_config.get("max_tokens", 2000),
            ),
            "tools": self.tools,
            "output_type": AgentOutputSchema(TaskExecutionOutput, strict_json_schema=False),
        }

        if SDK_AVAILABLE and is_manager_type_role and self.direct_sdk_handoffs:
            agent_config["handoffs"] = self.direct_sdk_handoffs
            logger.info(f"Agent {self.agent_data.name} (Manager type) configured with {len(self.direct_sdk_handoffs)} SDK handoffs.")
        elif is_manager_type_role and not SDK_AVAILABLE:
             logger.warning(f"Agent {self.agent_data.name} (Manager type) could use SDK handoffs, but SDK is not fully available.")
        return OpenAIAgent(**agent_config)

    def _create_anti_loop_prompt(self, is_manager: bool) -> str:
        base_prompt_prefix = handoff_prompt.RECOMMENDED_PROMPT_PREFIX if SDK_AVAILABLE and is_manager else ""
        core_prompt = f"""
{base_prompt_prefix}

You are a '{self.agent_data.seniority.value}' AI specialist: '{self.agent_data.role}'.
Your primary goal is to complete tasks efficiently and produce a final, concrete output.

CRITICAL ANTI-LOOP & EXECUTION RULES:
1. COMPLETE TASKS YOURSELF WHENEVER POSSIBLE. Prioritize direct execution over delegation.
2. NEVER delegate tasks back to your own specific role ('{self.agent_data.role}') or to an identical role type if you are a specialist.
3. If delegation is ABSOLUTELY necessary (e.g., task requires completely different expertise), be very specific about the sub-task and the required expertise for the target agent.
4. AVOID CREATING TASKS THAT DUPLICATE EXISTING OR SIMILAR WORK.
5. ALWAYS provide a comprehensive final summary of the work done and a clear status ('completed', 'failed', or 'requires_handoff') as per the schema.
6. If a task is too complex or leads to multiple turns without resolution, simplify your approach or provide a partial but concrete result and mark as 'completed'.
7. Ensure your 'detailed_results_json' and 'resources_consumed_json' are VALID JSON strings if provided.

OUTPUT REQUIREMENTS:
Your final output for EACH task execution MUST be a single, valid JSON object matching the 'TaskExecutionOutput' schema:
- "task_id": (string) ID of the current task being processed.
- "status": (string) Must be one of: "completed", "failed", "requires_handoff". Default to "completed" if substantial work is done.
- "summary": (string) Concise summary of the work performed and the outcome. THIS IS MANDATORY.
- "detailed_results_json": (string, optional) A valid JSON string containing detailed, structured results. Null if not applicable.
- "next_steps": (array of strings, optional) Suggested next actions or follow-up tasks.
- "suggested_handoff_target_role": (string, optional) ONLY if status is "requires_handoff". Specify the role to hand off to.
- "resources_consumed_json": (string, optional) A valid JSON string for tracking resource usage (e.g., tokens, API calls). Null if not applicable.

EXECUTION APPROACH:
"""
        available_tool_names = []
        for tool in self.tools:
            if hasattr(tool, 'name'): available_tool_names.append(tool.name)
            elif hasattr(tool, '__name__'): available_tool_names.append(tool.__name__)

        if is_manager:
            core_prompt += f"""
AS A MANAGER/COORDINATOR ({self.agent_data.role}):
1. Analyze the incoming task thoroughly.
2. Attempt to complete planning, coordination, or strategic tasks yourself.
3. If sub-tasks require specialized expertise you don't possess, you can delegate.
   - For direct, conversational handoff to another available agent: Use the SDK handoff tools (e.g., 'transfer_to_<AgentName>_<Role>'). These are for immediate continuation by another agent.
   - To create a new, separate task for another agent to pick up: Use the '{self._create_task_tool_name}' tool.
4. Ensure any delegation clearly defines the sub-task, expected outcome, and provides all necessary context.
5. Always provide a comprehensive summary of what *you* achieved, even if delegating parts.
6. Your primary role is to ensure the overall goal is met, through your own work or effective delegation.

DELEGATION GUIDELINES (using '{self._create_task_tool_name}'):
- Delegate only specific, well-defined sub-tasks.
- Avoid delegating back to other manager/coordinator roles unless it's for a different management aspect.
- Include all necessary context and clearly define expected outcomes.
"""
        else: # Specialist Agent
            core_prompt += f"""
AS A SPECIALIST IN {self.agent_data.role.upper()}:
1. Focus on your specific area of expertise: {self.agent_data.description or f'Specialist in {self.agent_data.role}'}.
2. Utilize your available tools effectively to complete tasks within your domain.
3. If a task is partially outside your expertise but you can make significant progress, do so and document limitations.
4. If a task is entirely outside your expertise OR you've completed your part and require another specialist:
   - Use the '{self._request_handoff_tool_name}' to request a handoff. Provide a clear reason, summary of your work, and what the target role needs to do. This will create a new task for the appropriate agent.
5. ALWAYS provide concrete deliverables and a final summary of your contribution.

YOUR EXPERTISE: {self.agent_data.description or f'Specialist in {self.agent_data.role}'}
"""

        if available_tool_names:
            core_prompt += f"\n\nAVAILABLE CUSTOM TOOLS (use these exact names when calling tools):\n- {', '.join(available_tool_names)}\n"
        if SDK_AVAILABLE and is_manager and self.direct_sdk_handoffs:
            sdk_handoff_tool_names = [h.name for h in self.direct_sdk_handoffs if hasattr(h, 'name')]
            if sdk_handoff_tool_names:
                 core_prompt += f"\nAVAILABLE SDK HANDOFF TOOLS (for direct conversational transfer):\n- {', '.join(sdk_handoff_tool_names)}\n"
        core_prompt += """
REMEMBER:
- Prioritize task completion.
- Avoid delegation loops by following the rules above.
- Structure your final response strictly according to the 'TaskExecutionOutput' JSON schema.
- Be clear, concise, and action-oriented in your summaries and results.
"""
        return core_prompt.strip()

    def _create_sdk_handoffs(self) -> List[Any]:
        if not SDK_AVAILABLE or not handoff_filters:
            return []
        
        handoffs_list = []
        my_role_lower = self.agent_data.role.lower()
        
        for other_agent_data in self.all_workspace_agents_data:
            if (other_agent_data.id != self.agent_data.id and 
                other_agent_data.status == AgentStatus.ACTIVE):
                
                other_role_lower = other_agent_data.role.lower()
                is_my_role_manager_type = any(keyword in my_role_lower for keyword in ['manager', 'coordinator', 'director', 'lead'])
                
                if not is_my_role_manager_type and self._is_same_role_type(my_role_lower, other_role_lower):
                    logger.debug(f"Skipping SDK handoff from {self.agent_data.name} to {other_agent_data.name} (same role type and not manager).")
                    continue
                
                try:
                    target_agent_for_tool_def = OpenAIAgent(
                        name=other_agent_data.name,
                        instructions=f"You are {other_agent_data.role}. You are receiving a handoff.",
                        model=self.seniority_model_map.get(other_agent_data.seniority.value, "gpt-4.1-nano")
                    )
                    agent_handoff_tool = handoff(
                        target_agent_for_tool_def,
                        tool_description_override=f"Transfer current task progress and control to {other_agent_data.role} ({other_agent_data.name}) for specialized handling or continuation.",
                        input_filter=handoff_filters.remove_all_tools
                    )
                    handoffs_list.append(agent_handoff_tool)
                except Exception as e:
                    logger.warning(f"Failed to create SDK handoff tool for {other_agent_data.name}: {e}")
        
        logger.info(f"Agent {self.agent_data.name} created {len(handoffs_list)} SDK handoff tools.")
        return handoffs_list

    def _is_same_role_type(self, role1_lower: str, role2_lower: str) -> bool:
        manager_keywords = ['manager', 'coordinator', 'director', 'lead']
        analyst_keywords = ['analyst', 'analysis', 'researcher']
        
        role1_type = "specialist" 
        if any(kw in role1_lower for kw in manager_keywords): role1_type = "manager"
        elif any(kw in role1_lower for kw in analyst_keywords): role1_type = "analyst"
            
        role2_type = "specialist"
        if any(kw in role2_lower for kw in manager_keywords): role2_type = "manager"
        elif any(kw in role2_lower for kw in analyst_keywords): role2_type = "analyst"
        
        if role1_type == "manager" and role2_type == "manager":
            return False 
        
        if role1_type == role2_type:
            set1 = set(role1_lower.split())
            set2 = set(role2_lower.split())
            intersection = len(set1.intersection(set2))
            union = len(set1.union(set2))
            if union == 0: return True 
            jaccard_similarity = intersection / union
            return jaccard_similarity >= 0.8
        return False

    def _initialize_tools(self) -> List[Any]:
        tools_list: List[Any] = []
        tools_list.extend([
            self._create_task_for_agent_tool(),
            self._create_request_handoff_tool(),
            self._create_log_execution_tool(),
            self._create_update_health_status_tool(),
            self._create_report_progress_tool(),
        ])

        if self.agent_data.tools:
            for tool_config in self.agent_data.tools:
                if isinstance(tool_config, dict):
                    tool_type = tool_config.get("type", "").lower()
                    if tool_type == "web_search":
                        tools_list.append(WebSearchTool())
                        logger.info(f"Agent {self.agent_data.name} equipped with WebSearchTool.")
                    elif tool_type == "file_search":
                        vs_ids = getattr(self.agent_data, 'vector_store_ids', [])
                        if vs_ids:
                            tools_list.append(FileSearchTool(vector_store_ids=vs_ids))
                            logger.info(f"Agent {self.agent_data.name} equipped with FileSearchTool for VS IDs: {vs_ids}.")
                        else:
                            logger.warning(f"Agent {self.agent_data.name}: file_search tool configured but no vector_store_ids found.")
        
        if "social" in self.agent_data.role.lower() or "instagram" in self.agent_data.role.lower():
            try:
                from tools.social_media import InstagramTools
                tools_list.extend([
                    InstagramTools.analyze_hashtags, InstagramTools.analyze_account,
                    InstagramTools.generate_content_ideas,
                ])
                logger.info(f"Agent {self.agent_data.name} equipped with InstagramTools.")
            except ImportError: logger.warning("InstagramTools not available or path is incorrect (tools.social_media).")
            except AttributeError: logger.warning("InstagramTools found, but some specific tools are missing.")

        if self.agent_data.can_create_tools:
            tools_list.append(self._create_custom_tool_creator_tool())
            logger.info(f"Agent {self.agent_data.name} equipped with CustomToolCreatorTool.")
        return tools_list

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        if not text1 or not text2: return 0.0
        tokens1 = set(text1.lower().split())
        tokens2 = set(text2.lower().split())
        if not tokens1 or not tokens2: return 0.0
        intersection = len(tokens1.intersection(tokens2))
        union = len(tokens1.union(tokens2))
        return intersection / union if union > 0 else 0.0

    async def _check_similar_tasks_exist(
        self, workspace_id: str, task_name: str, task_description: str
    ) -> Optional[Dict]:
        try:
            # Nota: Assicurarsi che db_list_tasks accetti workspace_id come keyword argument.
            all_tasks = await db_list_tasks(workspace_id=workspace_id) 
            pending_or_in_progress_tasks = [
                t for t in all_tasks 
                if t.get("status") in [TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value]
            ]
            norm_name = task_name.lower().strip()
            norm_desc = task_description.lower().strip()
            for existing_task in pending_or_in_progress_tasks:
                existing_norm_name = existing_task.get("name", "").lower().strip()
                existing_norm_desc = existing_task.get("description", "").lower().strip()
                name_similarity = self._calculate_text_similarity(norm_name, existing_norm_name)
                desc_similarity = self._calculate_text_similarity(norm_desc, existing_norm_desc)
                if name_similarity > 0.9 or desc_similarity > 0.85:
                    logger.warning(f"Found existing similar task (Name sim: {name_similarity:.2f}, Desc sim: {desc_similarity:.2f}): {existing_task.get('id')} - '{existing_task.get('name')}'")
                    return existing_task
            return None
        except Exception as e:
            logger.error(f"Error checking for similar tasks: {e}", exc_info=True)
            return None

    def _create_task_for_agent_tool(self):
        @function_tool(name_override=self._create_task_tool_name)
        async def impl(
            task_name: str = Field(..., description="Clear and concise name for the new task."),
            task_description: str = Field(..., description="Detailed description of what needs to be done for the new task."),
            target_agent_role: str = Field(..., description="The role of the agent best suited to perform this new task (e.g., 'Data Analyst', 'Copywriter')."),
            priority: Literal["low","medium","high"] = Field("medium", description="Priority of the new task."),
        ) -> str:
            try:
                existing_similar_task = await self._check_similar_tasks_exist(
                    str(self.agent_data.workspace_id), task_name, task_description
                )
                if existing_similar_task:
                    return json.dumps(TaskCreationOutput(
                        success=True, task_id=existing_similar_task["id"],
                        task_name=existing_similar_task["name"], assigned_agent_name="EXISTING_TASK",
                        error_message="Reusing existing similar task."
                    ).model_dump())

                if self._is_same_role_type(self.agent_data.role.lower(), target_agent_role.lower()):
                    self.self_delegation_tool_call_count += 1
                    if self.self_delegation_tool_call_count > self.max_self_delegations_per_tool_call:
                        logger.warning(f"Agent {self.agent_data.name} attempting excessive self-delegation to role type similar to '{target_agent_role}'.")
                        self.self_delegation_tool_call_count = 0 
                        return json.dumps(TaskCreationOutput(
                            success=False, task_name=task_name,
                            error_message=f"Self-delegation loop to role {target_agent_role} prevented. Re-evaluate."
                        ).model_dump())
                else:
                    self.self_delegation_tool_call_count = 0

                desc_hash = str(hash(task_description.lower().strip()))
                current_attempts = self.delegation_attempts_cache.get(desc_hash, 0)
                if current_attempts >= self.max_delegation_attempts_per_task_desc:
                    logger.warning(f"Max delegation attempts reached for task description hash {desc_hash} to target role '{target_agent_role}'.")
                    return json.dumps(TaskCreationOutput(
                        success=False, task_name=task_name,
                        error_message=f"Max delegation attempts reached for this sub-task to role {target_agent_role}."
                    ).model_dump())
                
                agents_in_db = await db_list_agents(str(self.agent_data.workspace_id))
                compatible_agents = self._find_compatible_agents_anti_loop(agents_in_db, target_agent_role)
                
                if compatible_agents:
                    target_agent = compatible_agents[0]
                    enhanced_description = f"Original Task Request by {self.agent_data.name} ({self.agent_data.role}):\n{task_description}\n---\nContext: This task was created by {self.agent_data.name} for a specialist in '{target_agent_role}'.\nPriority: {priority.upper()}"
                    # Nota: Assicurarsi che db_create_task accetti questi come keyword arguments.
                    created_task = await db_create_task(
                        workspace_id=str(self.agent_data.workspace_id),
                        agent_id=str(target_agent["id"]), 
                        name=task_name, description=enhanced_description,
                        status=TaskStatus.PENDING.value,
                    )
                    if created_task:
                        self.delegation_attempts_cache[desc_hash] = 0
                        return json.dumps(TaskCreationOutput(
                            success=True, task_id=created_task["id"], task_name=task_name,
                            assigned_agent_name=target_agent["name"]
                        ).model_dump())
                    else: error_msg = "Failed to create task in database."
                else: error_msg = f"No suitable active agent found for role '{target_agent_role}'."

                self.delegation_attempts_cache[desc_hash] = current_attempts + 1
                logger.warning(f"{error_msg} Task creation for '{task_name}' failed. Attempt {self.delegation_attempts_cache[desc_hash]}/{self.max_delegation_attempts_per_task_desc}.")
                return json.dumps(TaskCreationOutput(success=False, task_name=task_name, error_message=error_msg).model_dump())
            except Exception as e:
                logger.error(f"Error in '{self._create_task_tool_name}': {e}", exc_info=True)
                return json.dumps(TaskCreationOutput(success=False, task_name=task_name, error_message=str(e)).model_dump())
        return impl

    def _find_compatible_agents_anti_loop(self, agents_db_list: List[Dict[str, Any]], target_role: str) -> List[Dict[str, Any]]:
        target_lower = target_role.lower().strip()
        candidates = []
        my_current_role_lower = self.agent_data.role.lower()

        for agent_dict in agents_db_list:
            if not isinstance(agent_dict, dict):
                logger.warning(f"Skipping non-dict item in agents_db_list: {agent_dict}")
                continue
            agent_id = agent_dict.get("id"); agent_status = agent_dict.get("status")
            agent_role = agent_dict.get("role", "").lower().strip()
            agent_seniority = agent_dict.get("seniority", AgentSeniority.JUNIOR.value)

            if (agent_status == AgentStatus.ACTIVE.value and str(agent_id) != str(self.agent_data.id)):
                score = 0
                if target_lower == agent_role: score = 10
                elif target_lower in agent_role or agent_role in target_lower: score = 8
                else:
                    target_words = set(target_lower.split()); agent_words = set(agent_role.split())
                    score = len(target_words.intersection(agent_words)) * 2
                
                seniority_boost = {AgentSeniority.EXPERT.value: 1.5, AgentSeniority.SENIOR.value: 1.2, AgentSeniority.JUNIOR.value: 1.0}
                score *= seniority_boost.get(agent_seniority, 1.0)
                
                if self._is_same_role_type(my_current_role_lower, agent_role):
                    score *= 0.3 
                    logger.debug(f"Applying same-role-type penalty for {agent_dict.get('name')} ({agent_role}). Score: {score:.2f}.")

                if score >= 5: 
                    agent_dict['match_score'] = round(score, 1)
                    candidates.append(agent_dict)
        
        seniority_order = {AgentSeniority.EXPERT.value: 3, AgentSeniority.SENIOR.value: 2, AgentSeniority.JUNIOR.value: 1}
        candidates.sort(key=lambda x: (x.get('match_score', 0), seniority_order.get(x.get('seniority'), 0)), reverse=True)
        
        if candidates: logger.info(f"Found {len(candidates)} compatible agents for '{target_role}'. Top: {candidates[0].get('name')} (Score: {candidates[0].get('match_score')})")
        else: logger.warning(f"No compatible agents found for role '{target_role}'.")
        return candidates

    def _create_request_handoff_tool(self):
        @function_tool(name_override=self._request_handoff_tool_name)
        async def impl(
            target_role: str = Field(..., description="The role of the agent you need to handoff to."),
            reason_for_handoff: str = Field(..., description="Clear reason why this handoff is necessary."),
            summary_of_work_done: str = Field(..., description="Detailed summary of work you completed."),
            specific_request_for_target: str = Field(..., description="What exactly the target agent needs to do."),
            priority: Literal["low","medium","high"] = Field("medium", description="Priority of the handoff request."),
        ) -> str:
            try:
                if not self._current_task_being_processed_id:
                    logger.error("Cannot request handoff: _current_task_being_processed_id is not set.")
                    return json.dumps(HandoffRequestOutput(success=False, message="Error: Current task context not found.").model_dump())

                if self._is_same_role_type(self.agent_data.role.lower(), target_role.lower()):
                    logger.warning(f"Handoff request from {self.agent_data.role} to similar role type {target_role} blocked.")
                    return json.dumps(HandoffRequestOutput(success=False, message=f"Cannot handoff to similar role type ('{target_role}').").model_dump())

                handoff_attempt_key = target_role.lower()
                if handoff_attempt_key in self._handoff_attempts_for_current_task:
                    logger.warning(f"Duplicate handoff request for task '{self._current_task_being_processed_id}' to role '{target_role}' blocked.")
                    return json.dumps(HandoffRequestOutput(success=False, message=f"Handoff to '{target_role}' already attempted for this task.").model_dump())

                agents_in_db = await db_list_agents(str(self.agent_data.workspace_id))
                compatible_agents = self._find_compatible_agents_anti_loop(agents_in_db, target_role)
                original_target_role_for_log = target_role

                if not compatible_agents:
                    logger.warning(f"No direct agent for handoff target role '{target_role}'. Attempting PM fallback.")
                    compatible_agents = self._find_compatible_agents_anti_loop(agents_in_db, "Project Manager") # Specific role name
                    if compatible_agents: 
                        target_role_for_description = "Project Manager"
                        reason_for_handoff = f"[ESCALATED to PM] Original Target: {original_target_role_for_log}. Reason: {reason_for_handoff}"
                    else:
                         logger.error(f"Handoff failed: No suitable agent for '{original_target_role_for_log}' or Project Manager.")
                         return json.dumps(HandoffRequestOutput(success=False, message=f"No suitable agent for handoff to '{original_target_role_for_log}' or fallback.").model_dump())
                else:
                    target_role_for_description = target_role # Use original if direct match found

                target_agent_dict = compatible_agents[0]
                handoff_task_name = f"HANDOFF from {self.agent_data.name} for Task ID: {self._current_task_being_processed_id}"
                handoff_task_description = f"!!! HANDOFF TASK !!!\nPriority: {priority.upper()}\nOriginal Task ID: {self._current_task_being_processed_id}\nFrom: {self.agent_data.name} ({self.agent_data.role})\nTo (Intended): {target_role_for_description} (Assigned: {target_agent_dict.get('name')} - {target_agent_dict.get('role')})\nReason: {reason_for_handoff}\nWork Done by {self.agent_data.name}:\n{summary_of_work_done}\nSpecific Request for {target_agent_dict.get('role', target_role_for_description)}:\n{specific_request_for_target}\nInstructions: Review, continue progress. Avoid further delegation without manager approval."
                
                # Nota: Assicurarsi che db_create_task accetti questi come keyword arguments.
                created_task = await db_create_task(
                    workspace_id=str(self.agent_data.workspace_id), agent_id=str(target_agent_dict["id"]),
                    name=handoff_task_name, description=handoff_task_description,
                    status=TaskStatus.PENDING.value,
                )

                if created_task:
                    self._handoff_attempts_for_current_task.add(handoff_attempt_key)
                    logger.info(f"Handoff task '{created_task['id']}' created for '{target_agent_dict.get('name')}' re: original task '{self._current_task_being_processed_id}'.")
                    return json.dumps(HandoffRequestOutput(
                        success=True, message=f"Handoff task created for {target_agent_dict.get('name')}.",
                        handoff_task_id=created_task["id"], assigned_to_agent_name=target_agent_dict.get("name")
                    ).model_dump())
                else:
                    logger.error("Failed to create handoff task in database.")
                    return json.dumps(HandoffRequestOutput(success=False, message="Database error: Failed to create handoff task.").model_dump())
            except Exception as e:
                logger.error(f"Error in '{self._request_handoff_tool_name}': {e}", exc_info=True)
                return json.dumps(HandoffRequestOutput(success=False, message=str(e)).model_dump())
        return impl

    def _create_log_execution_tool(self):
        @function_tool(name_override=self._log_execution_tool_name)
        async def impl(step_name: str = Field(...), details_json: str = Field(...)):
            return await self._log_execution_internal(step_name, details_json)
        return impl

    def _create_update_health_status_tool(self):
        @function_tool(name_override=self._update_health_tool_name)
        async def impl(status: Literal["healthy","degraded","unhealthy"] = Field(...), details_message: Optional[str] = Field(None)):
            try:
                # La struttura di health_payload deve corrispondere a AgentHealth Pydantic model
                health_payload = {
                    "status": status, # Questo dovrebbe corrispondere a HealthStatus enum
                    "last_update": datetime.now().isoformat(),
                    "details": {"message": details_message}
                }
                # Nota: Assicurarsi che update_agent_status accetti il payload di health in questo formato.
                await update_agent_status(str(self.agent_data.id), health_info=health_payload)
                return json.dumps({"success": True, "message": f"Health status updated to {status}."})
            except Exception as e:
                logger.error(f"Error in {self._update_health_tool_name} tool: {e}", exc_info=True)
                return json.dumps({"success": False, "message": str(e)})
        return impl

    def _create_report_progress_tool(self):
        @function_tool(name_override=self._report_progress_tool_name)
        async def impl(
            task_id_being_processed: str = Field(...), progress_percentage: int = Field(..., ge=0, le=100),
            current_stage_summary: str = Field(...), next_action_planned: Optional[str] = Field(None),
            blockers_or_issues: Optional[str] = Field(None)
        ):
            details = {
                "task_id": task_id_being_processed, "progress_reported": progress_percentage,
                "current_stage": current_stage_summary, "next_action": next_action_planned,
                "blockers": blockers_or_issues
            }
            await self._log_execution_internal("task_progress_reported", details)
            return json.dumps({"success": True, "message": "Progress reported."})
        return impl

    def _create_custom_tool_creator_tool(self):
        @function_tool(name_override=self._propose_custom_tool_name)
        async def impl(name: str = Field(...), description: str = Field(...), python_code: str = Field(...)):
            log_details = {
                "proposed_tool_name": name, "proposed_tool_description": description,
                "code_snippet_preview": python_code[:200] + "..." if len(python_code) > 200 else python_code,
                "status": "proposed_for_review"
            }
            await self._log_execution_internal("custom_tool_proposed", log_details)
            return json.dumps({"success": True, "message": f"Tool '{name}' proposed for review."})
        return impl

    async def _log_execution_internal(self, step: str, details: Union[str, Dict]) -> bool:
        try:
            if isinstance(details, str):
                try: details = json.loads(details)
                except json.JSONDecodeError: details = {"raw_details": details}
            log_entry = {
                "timestamp": datetime.now().isoformat(), "agent_id": str(self.agent_data.id),
                "agent_name": self.agent_data.name, "agent_role": self.agent_data.role,
                "event_step": step, "details": details, "workspace_id": str(self.agent_data.workspace_id),
                "current_task_id_context": self._current_task_being_processed_id,
            }
            logger.info(json.dumps(log_entry))
            return True
        except Exception as e:
            logger.error(f"Internal logging failed: {e}", exc_info=True)
            return False

    async def verify_capabilities(self) -> bool:
        logger.info(f"Capability verification for {self.agent_data.name} (Simplified: always True).")
        return True

    async def execute_task(self, task: Task, context: Optional[T] = None) -> Dict[str, Any]:
        self._current_task_being_processed_id = str(task.id)
        self._handoff_attempts_for_current_task = set()
        self.self_delegation_tool_call_count = 0 
        # self.delegation_attempts_cache non viene resettata qui intenzionalmente (vedi __init__)

        trace_id_val = gen_trace_id() if SDK_AVAILABLE else f"fallback_trace_{task.id}"
        workflow_name = f"TaskExec-{task.name[:25]}-{self.agent_data.name[:15]}"
        trace_context_manager = trace(workflow_name=workflow_name, trace_id=trace_id_val, group_id=str(task.id)) if SDK_AVAILABLE else _dummy_async_context_manager() # type: ignore

        async with trace_context_manager:
            try:
                await self._log_execution_internal("task_execution_started", {"task_id": str(task.id), "task_name": task.name, "trace_id": trace_id_val})
                # Nota: Assicurarsi che update_task_status accetti questi come keyword arguments.
                await update_task_status(task_id=str(task.id), status=TaskStatus.IN_PROGRESS.value)
                
                task_prompt_content = f"Current Task ID: {task.id}\nTask Name: {task.name}\nTask Description:\n{task.description}\n---\nRemember to use your tools and expertise as per your system instructions. Your final output MUST be a single JSON object matching the 'TaskExecutionOutput' schema."
                
                agent_run_result = await asyncio.wait_for(
                    Runner.run(self.agent, task_prompt_content, max_turns=3, context=context),
                    timeout=self.execution_timeout
                )
                
                final_llm_output = agent_run_result.final_output
                execution_result_obj: TaskExecutionOutput

                if isinstance(final_llm_output, TaskExecutionOutput): execution_result_obj = final_llm_output
                elif isinstance(final_llm_output, dict):
                    if 'task_id' not in final_llm_output: final_llm_output['task_id'] = str(task.id)
                    if 'status' not in final_llm_output: final_llm_output['status'] = 'completed'
                    if 'summary' not in final_llm_output: final_llm_output['summary'] = "Task processing completed."
                    try: execution_result_obj = TaskExecutionOutput.model_validate(final_llm_output)
                    except Exception as val_err:
                        logger.error(f"Pydantic validation error for dict output: {val_err}. Raw: {str(final_llm_output)[:500]}")
                        execution_result_obj = TaskExecutionOutput(
                            task_id=str(task.id), status="failed", summary=f"Output validation error: {val_err}.",
                            detailed_results_json=json.dumps({"error": "Output validation failed", "raw_output": str(final_llm_output)[:1000]})
                        )
                else: 
                    logger.warning(f"Unexpected final_output type: {type(final_llm_output)}. Raw: {str(final_llm_output)[:500]}")
                    execution_result_obj = TaskExecutionOutput(
                        task_id=str(task.id), status="completed", summary=str(final_llm_output)[:500] or "Completed with non-standard output.",
                        detailed_results_json=json.dumps({"raw_output": str(final_llm_output)})
                    )
                
                execution_result_obj.task_id = str(task.id)
                result_dict_to_save = execution_result_obj.model_dump()
                result_dict_to_save["trace_id"] = trace_id_val
                
                final_task_status_val = TaskStatus.COMPLETED.value
                if execution_result_obj.status == "failed": final_task_status_val = TaskStatus.FAILED.value
                elif execution_result_obj.status == "requires_handoff":
                    logger.info(f"Task {task.id} resulted in 'requires_handoff' to role '{execution_result_obj.suggested_handoff_target_role}'.")
                    # La task corrente è considerata completata dal punto di vista di questo agente.
                
                # Nota: Assicurarsi che update_task_status accetti questi come keyword arguments.
                await update_task_status(task_id=str(task.id), status=final_task_status_val, result=result_dict_to_save)
                await self._log_execution_internal("task_execution_finished", {"task_id": str(task.id), "final_status": final_task_status_val, "summary": execution_result_obj.summary})
                return result_dict_to_save

            except asyncio.TimeoutError:
                logger.warning(f"Task {task.id} (Trace: {trace_id_val}) timed out. Forcing completion.")
                err_summary = f"Task forcibly completed due to timeout ({self.execution_timeout}s)."
                err_res = TaskExecutionOutput(task_id=str(task.id), status="completed", summary=err_summary, detailed_results_json=json.dumps({"error": "TimeoutError", "reason": "forced_timeout_completion"})).model_dump()
                err_res["trace_id"] = trace_id_val
                await update_task_status(task_id=str(task.id), status=TaskStatus.COMPLETED.value, result=err_res)
                await self._log_execution_internal("task_execution_timeout", err_res)
                return err_res
            
            except MaxTurnsExceeded as e: 
                logger.warning(f"Task {task.id} (Trace: {trace_id_val}) exceeded max turns. Forcing completion. Last: {str(getattr(e, 'last_output', 'N/A'))[:200]}")
                err_summary = "Task forcibly completed due to exceeding max interaction turns."
                err_res = TaskExecutionOutput(task_id=str(task.id), status="completed", summary=err_summary, detailed_results_json=json.dumps({"error": "MaxTurnsExceeded", "reason": "forced_max_turns_completion"})).model_dump()
                err_res["trace_id"] = trace_id_val
                await update_task_status(task_id=str(task.id), status=TaskStatus.COMPLETED.value, result=err_res)
                await self._log_execution_internal("task_execution_max_turns", err_res)
                return err_res

            except Exception as e: 
                logger.error(f"Unhandled error executing task {task.id} (Trace: {trace_id_val}): {e}", exc_info=True)
                err_summary = f"Task failed due to an unexpected error: {str(e)[:100]}..."
                err_res = TaskExecutionOutput(task_id=str(task.id), status="failed", summary=err_summary, detailed_results_json=json.dumps({"error": str(e), "type": type(e).__name__, "reason": "unhandled_exception"})).model_dump()
                err_res["trace_id"] = trace_id_val
                await update_task_status(task_id=str(task.id), status=TaskStatus.FAILED.value, result=err_res)
                await self._log_execution_internal("task_execution_unhandled_error", err_res)
                return err_res
            finally:
                self._current_task_being_processed_id = None
                self._handoff_attempts_for_current_task = set()