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

# IMPORT PMOrchestrationTools
from ai_agents.tools import PMOrchestrationTools

from models import (
    Agent as AgentModelPydantic,
    AgentStatus,
    AgentHealth,
    HealthStatus,
    Task,
    TaskStatus,
    AgentSeniority
)
from database import (
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

        # Nomi dei tool per coerenza - aggiornati per il PM
        self._create_task_tool_name = "create_and_assign_sub_task"  # AGGIORNATO per PM
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

        # USA PROMPT SPECIFICO BASATO SUL RUOLO
        if is_manager_type_role:
            instructions = self._create_project_manager_prompt()
        else:
            instructions = self._create_specialist_anti_loop_prompt()

        agent_config = {
            "name": self.agent_data.name,
            "instructions": instructions,
            "model": model_name,
            "model_settings": ModelSettings(
                temperature=temperature,
                top_p=llm_config.get("top_p", 1.0),
                max_tokens=llm_config.get("max_tokens", 3000),  # Aumentato per PM
            ),
            "tools": self.tools,
            "output_type": AgentOutputSchema(TaskExecutionOutput, strict_json_schema=False),
        }

        if SDK_AVAILABLE and is_manager_type_role and self.direct_sdk_handoffs:
            agent_config["handoffs"] = self.direct_sdk_handoffs
            logger.info(f"Agent {self.agent_data.name} (Manager type) configured with {len(self.direct_sdk_handoffs)} SDK handoffs.")
        return OpenAIAgent(**agent_config)

    def _create_project_manager_prompt(self) -> str:
        """Prompt specifico per Project Manager agents con output strutturato"""
        base_prompt_prefix = handoff_prompt.RECOMMENDED_PROMPT_PREFIX if SDK_AVAILABLE else ""

        available_tool_names = []
        for tool in self.tools:
            tool_name_attr = getattr(tool, 'name', getattr(tool, '__name__', None))
            if tool_name_attr: available_tool_names.append(tool_name_attr)

        sdk_handoff_tool_names = [h.name for h in self.direct_sdk_handoffs if hasattr(h, 'name')] if SDK_AVAILABLE else []

        return f"""
        {base_prompt_prefix}
        You are a highly efficient AI Project Manager. Your name is {self.agent_data.name}.
        Your primary responsibility is to orchestrate the work of a team of specialist agents to achieve the project goal.

        CRITICAL WORKFLOW FOR TASK DELEGATION:
        1. **ALWAYS start by calling `get_team_roles_and_status` to see your available team members**
        2. **Use the EXACT `agent_name` from that response as your `target_agent_role`**
        3. **Then create sub-tasks using the exact names**

        You are equipped with the following tools: {', '.join(available_tool_names)}.
        {"You can also directly handoff to other agents using: " + ", ".join(sdk_handoff_tool_names) + "." if sdk_handoff_tool_names else ""}

        CURRENT TASK TYPE: PLANNING OR DELEGATION

        IF THE CURRENT TASK IS A PLANNING TASK (e.g., "Project Setup & Strategic Planning Kick-off"):
        1.  **FIRST STEP: Call `get_team_roles_and_status` to understand your team**
        2.  Thoroughly analyze the project goal and requirements.
        3.  Break down the project into logical phases and milestones.
        4.  For each phase, define key deliverables.
        5.  Identify the necessary sub-tasks for the *immediate next phase* (usually Phase 1 after initial planning).
        6.  For each sub-task, clearly define:
            * A unique and descriptive `name`.
            * A comprehensive `description` with all context, inputs, and expected outputs for the specialist.
            * The `target_agent_role` using the EXACT `agent_name` from get_team_roles_and_status (e.g., "ContentSpecialist", NOT "Content Creation Specialist").
            * A `priority` ("high", "medium", "low").
        7.  Your final output for a planning task MUST be a JSON object matching 'TaskExecutionOutput'.
            * The `summary` should state that planning is complete and sub-tasks for the next phase are defined.
            * The `detailed_results_json` MUST contain a JSON string with a list of the sub-tasks you've defined:

            CRITICAL FORMAT for detailed_results_json:
            Each subtask MUST have the following fields:
            - name: Clear descriptive name
            - description: Detailed task description
            - target_agent_role: EXACT agent_name from get_team_roles_and_status
            - priority: "high", "medium", or "low"

            {{"defined_sub_tasks": [
                {{
                    "name": "Competitor Analysis",
                    "description": "Analyze top 5 competitors' Instagram strategies, content themes, posting frequency, and engagement rates.",
                    "target_agent_role": "AnalysisSpecialist",
                    "priority": "high"
                }},
                {{
                    "name": "Audience Profiling", 
                    "description": "Define target audience demographics, interests, and content preferences for bodybuilding niche.",
                    "target_agent_role": "ContentSpecialist",
                    "priority": "high"
                }}
            ], "overall_plan_summary": "..."}}

            FAILING TO PROVIDE THIS STRUCTURE WILL CAUSE PROJECT FAILURE

            * `next_steps` should include: ["Sub-tasks will be automatically created for the defined roles."]

        EXAMPLE WORKFLOW:
        ```
        Step 1: Call get_team_roles_and_status()
        Response shows: {{"active_team_members": [{{"agent_name": "ContentSpecialist"}}, {{"agent_name": "AnalysisSpecialist"}}]}}

        Step 2: In your detailed_results_json, use EXACT names:
        {{"defined_sub_tasks": [
            {{
                "name": "Create Content Strategy",
                "description": "...",
                "target_agent_role": "ContentSpecialist",  ← EXACT name from response
                "priority": "high"
            }}
        ]}}
        ```

        IF THE CURRENT TASK IS A DELEGATION TASK:
        1.  **FIRST: Call `get_team_roles_and_status` to refresh team info**
        2.  You have access to the '{self._create_task_tool_name}' tool.
        3.  Use it to create and assign sub-tasks to appropriate specialists using EXACT agent names.
        4.  Your final output MUST be a JSON object with delegation results.
        5.  When calling this tool, you MUST provide the correct `workspace_id` for the current project.
        For the current task you are processing (Task ID: {self._current_task_being_processed_id or 'UNKNOWN_TASK_ID'}),
        the workspace ID you MUST use is: '{str(self.agent_data.workspace_id)}'.
        DO NOT use "default" or any other placeholder for `workspace_id`.

        CRITICAL GUIDELINES:
        * **NEVER guess agent names** - always check first with get_team_roles_and_status
        * **Use EXACT agent_name values** from the team status response
        * Focus on planning & defining clear sub-tasks.
        * NEVER delegate coordination tasks - those are YOUR responsibility.
        * Provide complete context in sub-task descriptions.
        * Always aim for "completed" status once your planning is finished.
        * Your detailed_results_json must be VALID JSON - no trailing commas, proper escaping.

        OUTPUT FORMAT REMINDER:
        Your final response for *every* interaction MUST be a single JSON object conforming to the 'TaskExecutionOutput' schema.

        Example for PLANNING task completion:
        {{
          "task_id": "{self._current_task_being_processed_id or 'CURRENT_TASK_ID'}",
          "status": "completed",
          "summary": "Project planning completed. Team verified and 3 sub-tasks defined for Phase 1.",
          "detailed_results_json": "{{\\"defined_sub_tasks\\": [...]}}",
          "next_steps": ["Sub-tasks will be automatically created for the defined roles."]
        }}

        Do NOT add any text before or after this final JSON object.
        """.strip()

    def _create_specialist_anti_loop_prompt(self) -> str:
        """Prompt specifico per specialist agents (non-manager)"""
        available_tool_names = []
        for tool in self.tools:
            tool_name_attr = getattr(tool, 'name', getattr(tool, '__name__', None))
            if tool_name_attr: available_tool_names.append(tool_name_attr)

        # Creazione della sezione personalità
        personality_section = ""
        if self.agent_data.personality_traits:
            traits = [trait.value for trait in self.agent_data.personality_traits]
            personality_section = f"Your personality traits are: {', '.join(traits)}.\n"

        # Creazione della sezione communication style
        communication_section = ""
        if self.agent_data.communication_style:
            communication_section = f"Your communication style is: {self.agent_data.communication_style}.\n"

        # Creazione della sezione hard skills
        hard_skills_section = ""
        if self.agent_data.hard_skills:
            skills = [f"{skill.name} ({skill.level.value})" for skill in self.agent_data.hard_skills]
            hard_skills_section = f"Your technical skills include: {', '.join(skills)}.\n"

        # Creazione della sezione soft skills
        soft_skills_section = ""
        if self.agent_data.soft_skills:
            skills = [f"{skill.name} ({skill.level.value})" for skill in self.agent_data.soft_skills]
            soft_skills_section = f"Your interpersonal skills include: {', '.join(skills)}.\n"

        # Creazione della sezione background
        background_section = ""
        if self.agent_data.background_story:
            background_section = f"Background: {self.agent_data.background_story}\n"

        # Nome completo
        full_name = ""
        if self.agent_data.first_name and self.agent_data.last_name:
            full_name = f"Your name is {self.agent_data.first_name} {self.agent_data.last_name}.\n"
        elif self.agent_data.first_name:
            full_name = f"Your name is {self.agent_data.first_name}.\n"

        return f"""
    You are a '{self.agent_data.seniority.value}' AI specialist in the role of: '{self.agent_data.role}'.
    {full_name}
    Your specific expertise is: {self.agent_data.description or 'Not specified, assume general capabilities for your role.'}
    {personality_section}{communication_section}{hard_skills_section}{soft_skills_section}{background_section}
    Your primary goal is to complete the assigned task efficiently and produce a final, concrete output.
    You are equipped with the following tools: {', '.join(available_tool_names) if available_tool_names else "No specific tools beyond core capabilities."}.

    CRITICAL EXECUTION RULES:
    1.  COMPLETE THE ASSIGNED TASK YOURSELF. Your focus is on execution using your expertise and tools.
    2.  If the task is partially outside your expertise but you can make significant progress on a component that IS within your expertise, complete that component thoroughly. Document what you did and what remains.
    3.  If the *entire* task is outside your expertise, OR if you have fully completed your part and the remaining work requires a *different* specialist (NOT your own role type):
        * Use the '{self._request_handoff_tool_name}' tool.
        * Clearly state the `target_agent_role` needed.
        * Provide a `reason_for_handoff`.
        * Give a `summary_of_work_done` by you (if any).
        * Write a `specific_request_for_target` detailing what the next agent should do.
    4.  DO NOT create new general tasks or delegate work that you should be doing. The Project Manager handles task breakdown and assignment.
    5.  Always provide a comprehensive final summary of the work you performed and a clear status ('completed', 'failed', or 'requires_handoff') as per the TaskExecutionOutput schema.
    6.  If a task is too complex or leads to multiple turns without clear resolution, simplify your approach, provide the best partial but concrete result you can, and mark the task as 'completed' with notes on limitations.
    7.  Ensure your 'detailed_results_json' (if used) is a VALID JSON string. Null is acceptable if no structured data.

    OUTPUT REQUIREMENTS:
    Your final output for EACH task execution MUST be a single, valid JSON object matching the 'TaskExecutionOutput' schema:
    -   "task_id": (string) ID of the current task being processed (e.g., "{self._current_task_being_processed_id or 'CURRENT_TASK_ID'}").
    -   "status": (string) Must be one of: "completed", "failed", "requires_handoff". Default to "completed" if substantial work is done.
    -   "summary": (string) Concise summary of the work performed and the outcome. THIS IS MANDATORY.
    -   "detailed_results_json": (string, optional) A valid JSON string containing detailed, structured results. Null if not applicable.
    -   "next_steps": (array of strings, optional) Only if you completed the task and have suggestions for the PM or for future work based on your findings.
    -   "suggested_handoff_target_role": (string, optional) ONLY if status is "requires_handoff". Specify the different specialist role to hand off to.
    -   "resources_consumed_json": (string, optional) A JSON string for any notable resource usage (e.g., API calls made by a tool you used).

    Example of a 'completed' task by a specialist:
    {{
      "task_id": "{self._current_task_being_processed_id or 'CURRENT_TASK_ID'}",
      "status": "completed",
      "summary": "Analyzed competitor X's Instagram strategy, identifying 3 key content pillars and an average engagement rate of 2.5%.",
      "detailed_results_json": "{{ \\"competitor_analysis\\": {{ \\"name\\": \\"Competitor X\\", \\"content_pillars\\": [\\"Pillar A\\", \\"Pillar B\\", \\"Pillar C\\"], \\"engagement_rate\\": 0.025 }} }}",
      "next_steps": ["Recommend PM to review findings for strategic adjustments."],
      "suggested_handoff_target_role": null,
      "resources_consumed_json": null
    }}

    Example of a task requiring handoff by a specialist:
    {{
      "task_id": "{self._current_task_being_processed_id or 'CURRENT_TASK_ID'}",
      "status": "requires_handoff",
      "summary": "Completed initial data extraction for market trends. Further statistical modeling is required, which is outside my data collection expertise.",
      "detailed_results_json": "{{ \\"extracted_data_preview\\": [...] }}",
      "next_steps": null,
      "suggested_handoff_target_role": "Data Analyst",
      "resources_consumed_json": null
    }}

    Do NOT add any text before or after this final JSON object. Your entire response must be this JSON.
    """.strip()

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
        """Inizializza tools basati sul ruolo dell'agente"""
        tools_list: List[Any] = []

        # Tool comuni a tutti
        tools_list.extend([
            self._create_log_execution_tool(),
            self._create_update_health_status_tool(),
            self._create_report_progress_tool(),
        ])

        # Aggiungi tool specifici per ruolo
        current_agent_role_lower = self.agent_data.role.lower()

        is_manager_type_role = any(keyword in current_agent_role_lower
                                for keyword in ['manager', 'coordinator', 'director', 'lead'])

        if is_manager_type_role:
            # Tool specifici per Project Manager
            tools_list.append(PMOrchestrationTools.create_and_assign_sub_task_tool)
            tools_list.append(PMOrchestrationTools.get_team_roles_and_status_tool)
            logger.info(f"Agent {self.agent_data.name} ({self.agent_data.role}) equipped with PMOrchestrationTools.")
        else:
            # Tool per specialisti (handoff)
            tools_list.append(self._create_request_handoff_tool())

        # Tool configurati nel database
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

        # Tool per ruoli social/instagram
        if "social" in current_agent_role_lower or "instagram" in current_agent_role_lower:
            try:
                from tools.social_media import InstagramTools
                tools_list.extend([
                    InstagramTools.analyze_hashtags, InstagramTools.analyze_account,
                    InstagramTools.generate_content_ideas,
                ])
                logger.info(f"Agent {self.agent_data.name} equipped with InstagramTools.")
            except ImportError: logger.warning("InstagramTools not available or path is incorrect (tools.social_media).")
            except AttributeError: logger.warning("InstagramTools found, but some specific tools are missing.")

        # Tool per creazione custom tools
        if self.agent_data.can_create_tools:
            tools_list.append(self._create_custom_tool_creator_tool())
            logger.info(f"Agent {self.agent_data.name} equipped with CustomToolCreatorTool.")

        # FIX: Gestione più robusta del logging dei tool names
        tool_names = []
        for t in tools_list:
            # Prova diversi modi per ottenere il nome del tool
            if hasattr(t, 'name'):
                tool_names.append(t.name)
            elif hasattr(t, '__name__'):
                tool_names.append(t.__name__)
            elif hasattr(t, '_name'):
                tool_names.append(t._name)
            elif hasattr(t, '__class__'):
                tool_names.append(t.__class__.__name__)
            else:
                tool_names.append(str(type(t).__name__))

        logger.debug(f"Final tools for agent {self.agent_data.name}: {tool_names}")
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
                    compatible_agents = self._find_compatible_agents_anti_loop(agents_in_db, "Project Manager")
                    if compatible_agents: 
                        target_role_for_description = "Project Manager"
                        reason_for_handoff = f"[ESCALATED to PM] Original Target: {original_target_role_for_log}. Reason: {reason_for_handoff}"
                    else:
                         logger.error(f"Handoff failed: No suitable agent for '{original_target_role_for_log}' or Project Manager.")
                         return json.dumps(HandoffRequestOutput(success=False, message=f"No suitable agent for handoff to '{original_target_role_for_log}' or fallback.").model_dump())
                else:
                    target_role_for_description = target_role

                target_agent_dict = compatible_agents[0]
                handoff_task_name = f"HANDOFF from {self.agent_data.name} for Task ID: {self._current_task_being_processed_id}"
                handoff_task_description = f"!!! HANDOFF TASK !!!\nPriority: {priority.upper()}\nOriginal Task ID: {self._current_task_being_processed_id}\nFrom: {self.agent_data.name} ({self.agent_data.role})\nTo (Intended): {target_role_for_description} (Assigned: {target_agent_dict.get('name')} - {target_agent_dict.get('role')})\nReason: {reason_for_handoff}\nWork Done by {self.agent_data.name}:\n{summary_of_work_done}\nSpecific Request for {target_agent_dict.get('role', target_role_for_description)}:\n{specific_request_for_target}\nInstructions: Review, continue progress. Avoid further delegation without manager approval."
                
                created_task = await db_create_task(
                    workspace_id=str(self.agent_data.workspace_id), 
                    agent_id=str(target_agent_dict["id"]),
                    name=handoff_task_name, 
                    description=handoff_task_description,
                    status=TaskStatus.PENDING.value,
                    priority=priority
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

    def _find_compatible_agents_anti_loop(self, agents_db_list: List[Dict[str, Any]], target_role: str) -> List[Dict[str, Any]]:
        # Normalizzazione migliorata
        target_lower = target_role.lower().strip()
        target_normalized = target_lower.replace(" ", "")
        candidates = []
        my_current_role_lower = self.agent_data.role.lower()

        # Flag per ruoli speciali
        is_target_manager = any(keyword in target_normalized for keyword in ["manager", "director", "lead", "coordinator"])

        for agent_dict in agents_db_list:
            if not isinstance(agent_dict, dict):
                logger.warning(f"Skipping non-dict item in agents_db_list: {agent_dict}")
                continue
            agent_id = agent_dict.get("id"); agent_status = agent_dict.get("status")
            agent_role = agent_dict.get("role", "").lower().strip()
            agent_role_normalized = agent_role.replace(" ", "")
            agent_name = agent_dict.get("name", "").lower()
            agent_seniority = agent_dict.get("seniority", AgentSeniority.JUNIOR.value)

            if (agent_status == AgentStatus.ACTIVE.value and str(agent_id) != str(self.agent_data.id)):
                score = 0

                # Exact match (with and without spaces)
                if target_lower == agent_role:
                    score = 10
                elif target_normalized == agent_role_normalized:
                    score = 9.5
                # Match by agent name
                elif target_lower == agent_name or target_normalized == agent_name.replace(" ", ""):
                    score = 9
                # Containment matches
                elif target_lower in agent_role or agent_role in target_lower:
                    score = 8
                # Special manager role matching
                elif is_target_manager and any(keyword in agent_role_normalized for keyword in ["manager", "director", "lead", "coordinator"]):
                    score = 7
                # Word overlap scoring
                else:
                    # Filter out common words
                    common_words = ["specialist", "the", "and", "of", "for"]
                    target_words = set([w for w in target_lower.split() if w not in common_words])
                    agent_words = set([w for w in agent_role.split() if w not in common_words])

                    if target_words and agent_words:
                        intersection = len(target_words.intersection(agent_words))
                        if intersection > 0:
                            # Calculate overlap ratio
                            overlap_ratio = intersection / max(len(target_words), 1)
                            score = intersection * 2 * (1 + overlap_ratio)  # Improved word match scoring

                # Apply seniority boost
                seniority_boost = {AgentSeniority.EXPERT.value: 1.5, AgentSeniority.SENIOR.value: 1.2, AgentSeniority.JUNIOR.value: 1.0}
                score *= seniority_boost.get(agent_seniority, 1.0)

                # Lower threshold to 4 for better inclusivity
                if score >= 4: 
                    agent_dict['match_score'] = round(score, 1)
                    candidates.append(agent_dict)

        seniority_order = {AgentSeniority.EXPERT.value: 3, AgentSeniority.SENIOR.value: 2, AgentSeniority.JUNIOR.value: 1}
        candidates.sort(key=lambda x: (x.get('match_score', 0), seniority_order.get(x.get('seniority'), 0)), reverse=True)

        if candidates: logger.info(f"Found {len(candidates)} compatible agents for '{target_role}'. Top: {candidates[0].get('name')} (Score: {candidates[0].get('match_score')})")
        else: logger.warning(f"No compatible agents found for role '{target_role}'.")
        return candidates

    def _create_log_execution_tool(self):
        @function_tool(name_override=self._log_execution_tool_name)
        async def impl(step_name: str = Field(...), details_json: str = Field(...)):
            return await self._log_execution_internal(step_name, details_json)
        return impl

    def _create_update_health_status_tool(self):
        @function_tool(name_override=self._update_health_tool_name)
        async def impl(status: Literal["healthy","degraded","unhealthy"] = Field(...), details_message: Optional[str] = Field(None)):
            try:
                health_payload = {
                    "status": status,
                    "last_update": datetime.now().isoformat(),
                    "details": {"message": details_message}
                }
                await update_agent_status(str(self.agent_data.id), status=None, health=health_payload)
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

        trace_id_val = gen_trace_id() if SDK_AVAILABLE else f"fallback_trace_{task.id}"
        workflow_name = f"TaskExec-{task.name[:25]}-{self.agent_data.name[:15]}"
        
        try:
            if SDK_AVAILABLE:
                trace_context_manager = trace(workflow_name=workflow_name, trace_id=trace_id_val, group_id=str(task.id))
                if not hasattr(trace_context_manager, '__aenter__'):
                    raise AttributeError("TraceImpl doesn't support async context manager")
            else:
                trace_context_manager = _dummy_async_context_manager()
        except (AttributeError, TypeError) as e:
            logger.warning(f"SDK trace failed ({e}), using dummy context manager")
            trace_context_manager = _dummy_async_context_manager()
        
        async with trace_context_manager:
            try:
                await self._log_execution_internal(
                    "task_execution_started",
                    {"task_id": str(task.id), "task_name": task.name, "trace_id": trace_id_val, "assigned_role": task.assigned_to_role}
                )
                await update_task_status(task_id=str(task.id), status=TaskStatus.IN_PROGRESS.value, result_payload={"status_detail": "Execution started by agent"})
                
                # Costruisci il prompt per l'agente, includendo il context_data se presente
                task_context_info = ""
                if task.context_data:  # CAMBIATO da context_data_json a context_data
                    try:
                        # task.context_data è già un dict, quindi serializza in JSON per il prompt
                        context_json_str = json.dumps(task.context_data)
                        task_context_info = f"\nADDITIONAL CONTEXT FOR THIS TASK (JSON):\n{context_json_str}"
                    except Exception as e:
                        logger.warning(f"Could not serialize context_data for task {task.id}: {e}. Passing as string.")
                        task_context_info = f"\nADDITIONAL CONTEXT FOR THIS TASK (Raw String):\n{str(task.context_data)}"

                task_prompt_content = f"Current Task ID: {task.id}\nTask Name: {task.name}\nTask Priority: {task.priority}\nTask Description:\n{task.description}{task_context_info}\n---\nRemember to use your tools and expertise as per your system instructions. Your final output MUST be a single JSON object matching the 'TaskExecutionOutput' schema."
                
                # Esegui l'agente
                max_turns_for_agent = 10
                if isinstance(self.agent_data.llm_config, dict) and "max_turns_override" in self.agent_data.llm_config:
                    max_turns_for_agent = self.agent_data.llm_config["max_turns_override"]

                agent_run_result = await asyncio.wait_for(
                    Runner.run(self.agent, task_prompt_content, max_turns=max_turns_for_agent, context=context),
                    timeout=self.execution_timeout
                )
                
                final_llm_output = agent_run_result.final_output
                execution_result_obj: TaskExecutionOutput

                if isinstance(final_llm_output, TaskExecutionOutput):
                    execution_result_obj = final_llm_output
                elif isinstance(final_llm_output, dict):
                    # Assicurati che i campi obbligatori ci siano prima di validare
                    final_llm_output.setdefault('task_id', str(task.id))
                    final_llm_output.setdefault('status', 'completed')
                    final_llm_output.setdefault('summary', 'Task processing completed by agent.')
                    try:
                        execution_result_obj = TaskExecutionOutput.model_validate(final_llm_output)
                    except Exception as val_err:
                        logger.error(f"Pydantic validation error for agent's dict output: {val_err}. Raw output: {str(final_llm_output)[:500]}")
                        execution_result_obj = TaskExecutionOutput(
                            task_id=str(task.id), status="failed", summary=f"Output validation error: {val_err}.",
                            detailed_results_json=json.dumps({"error": "Agent output validation failed", "raw_output": str(final_llm_output)[:1000]})
                        )
                else: 
                    logger.warning(f"Agent returned unexpected final_output type: {type(final_llm_output)}. Output: {str(final_llm_output)[:500]}")
                    execution_result_obj = TaskExecutionOutput(
                        task_id=str(task.id), status="completed",
                        summary=str(final_llm_output)[:500] or "Completed with non-standard or empty output.",
                        detailed_results_json=json.dumps({"raw_output": str(final_llm_output)})
                    )
                
                # Sovrascrivi task_id per sicurezza, e aggiungi trace_id
                execution_result_obj.task_id = str(task.id)
                result_dict_to_save = execution_result_obj.model_dump()
                result_dict_to_save["trace_id_for_run"] = trace_id_val
                
                # Determina lo stato finale del DB basato sullo status dell'output dell'agente
                final_db_status = TaskStatus.COMPLETED.value
                if execution_result_obj.status == "failed":
                    final_db_status = TaskStatus.FAILED.value
                elif execution_result_obj.status == "requires_handoff":
                    final_db_status = TaskStatus.COMPLETED.value
                    logger.info(f"Task {task.id} by {self.agent_data.name} resulted in 'requires_handoff' to role '{execution_result_obj.suggested_handoff_target_role}'. This task is marked COMPLETED.")
                
                await update_task_status(task_id=str(task.id), status=final_db_status, result_payload=result_dict_to_save)
                
                # Log dettagliato dell'output
                logger.info(f"TASK OUTPUT for {task.id}:")
                logger.info(f"Summary: {execution_result_obj.summary}")
                if execution_result_obj.detailed_results_json:
                    logger.info(f"Detailed Results: {execution_result_obj.detailed_results_json}")
                if execution_result_obj.next_steps:
                    logger.info(f"Next Steps: {execution_result_obj.next_steps}")
                if execution_result_obj.suggested_handoff_target_role:
                    logger.info(f"Handoff Target Role: {execution_result_obj.suggested_handoff_target_role}")

                await self._log_execution_internal(
                    "task_execution_finished",
                    {"task_id": str(task.id), "final_status_in_db": final_db_status, "agent_reported_status": execution_result_obj.status, "summary": execution_result_obj.summary}
                )
                return result_dict_to_save

            except asyncio.TimeoutError:
                timeout_summary = f"Task forcibly marked as TIMED_OUT after {self.execution_timeout}s."
                logger.warning(f"Task {task.id} (Trace: {trace_id_val}) timed out ({self.execution_timeout}s).")
                timeout_result = TaskExecutionOutput(
                    task_id=str(task.id), status="failed",
                    summary=timeout_summary,
                    detailed_results_json=json.dumps({"error": "TimeoutError", "reason": "Task execution exceeded timeout limit."})
                ).model_dump()
                timeout_result["trace_id_for_run"] = trace_id_val
                await update_task_status(task_id=str(task.id), status=TaskStatus.TIMED_OUT.value, result_payload=timeout_result)
                await self._log_execution_internal("task_execution_timeout", {"task_id": str(task.id), "summary": timeout_summary})
                return timeout_result
            
            except MaxTurnsExceeded as e: 
                max_turns_summary = "Task forcibly marked as FAILED due to exceeding max interaction turns with LLM."
                logger.warning(f"Task {task.id} (Trace: {trace_id_val}) exceeded max turns. Last output: {str(getattr(e, 'last_output', 'N/A'))[:200]}")
                max_turns_result = TaskExecutionOutput(
                    task_id=str(task.id), status="failed",
                    summary=max_turns_summary,
                    detailed_results_json=json.dumps({"error": "MaxTurnsExceeded", "reason": str(e)})
                ).model_dump()
                max_turns_result["trace_id_for_run"] = trace_id_val
                await update_task_status(task_id=str(task.id), status=TaskStatus.FAILED.value, result_payload=max_turns_result)
                await self._log_execution_internal("task_execution_max_turns", {"task_id": str(task.id), "summary": max_turns_summary})
                return max_turns_result

            except Exception as e: 
                unhandled_error_summary = f"Task failed due to an unexpected error: {str(e)[:100]}..."
                logger.error(f"Unhandled error executing task {task.id} (Trace: {trace_id_val}): {e}", exc_info=True)
                unhandled_error_result = TaskExecutionOutput(
                    task_id=str(task.id), status="failed",
                    summary=unhandled_error_summary,
                    detailed_results_json=json.dumps({"error": str(e), "type": type(e).__name__})
                ).model_dump()
                unhandled_error_result["trace_id_for_run"] = trace_id_val
                await update_task_status(task_id=str(task.id), status=TaskStatus.FAILED.value, result_payload=unhandled_error_result)
                await self._log_execution_internal("task_execution_unhandled_error", {"task_id": str(task.id), "error": str(e)[:100]})
                return unhandled_error_result
            finally:
                self._current_task_being_processed_id = None
                self._handoff_attempts_for_current_task = set()