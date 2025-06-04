import logging
import os
import json
import asyncio
import contextlib # Per il dummy async context manager
from typing import List, Dict, Any, Optional, Union, Literal, TypeVar, Generic, Type
from uuid import UUID # Tipo comune per ID, anche se non generati qui
from datetime import datetime
from enum import Enum
import time

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

# FIXED: Import centralizzato Quality System con fallback
try:
    from backend.utils.quality_config_loader import load_quality_system_config
except ImportError:
    try:
        from utils.quality_config_loader import load_quality_system_config  # type: ignore
    except ImportError as e:
        logger.warning(f"⚠️ Quality System loader not available: {e}")
        QUALITY_SYSTEM_AVAILABLE = False
        QualitySystemConfig = None
        DynamicPromptEnhancer = None
    else:
        QualitySystemConfig, QUALITY_SYSTEM_AVAILABLE = load_quality_system_config()
else:
    QualitySystemConfig, QUALITY_SYSTEM_AVAILABLE = load_quality_system_config()
    
    # Prova a importare DynamicPromptEnhancer
    try:
        from ai_quality_assurance.quality_integration import DynamicPromptEnhancer
    except ImportError:
        try:
            from backend.ai_quality_assurance.quality_integration import DynamicPromptEnhancer
        except ImportError:
            logger.warning("DynamicPromptEnhancer not available")
            DynamicPromptEnhancer = None
            QUALITY_SYSTEM_AVAILABLE = False
    
    logger.info(f"✅ Quality System for SpecialistAgent: Available={QUALITY_SYSTEM_AVAILABLE}")

# NUOVO: Import per JSON parsing robusto
try:
    from backend.utils.robust_json_parser import parse_llm_json_robust, robust_json_parser
    from backend.utils.output_length_manager import optimize_agent_output
    ROBUST_JSON_AVAILABLE = True
    logger.info("✅ Robust JSON parser available")
except ImportError:
    logger.warning("⚠️ Robust JSON parser not available - using fallback")
    ROBUST_JSON_AVAILABLE = False
    
    # Fallback function
    def parse_llm_json_robust(raw_output: str, task_id: str = None, expected_schema: dict = None):
        try:
            import json
            return json.loads(raw_output), True, "fallback_parse"
        except:
            return {
                "task_id": task_id or "unknown",
                "status": "failed", 
                "summary": "JSON parsing failed with fallback"
            }, False, "fallback_error"
    def optimize_agent_output(output, task_id=None): 
        return output, False, []
            
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
    task_id: str = Field(..., description="ID of the task")  # Required, no default
    status: Literal["completed", "failed", "requires_handoff"] = Field(default="completed", description="Task completion status")
    summary: str = Field(..., description="Summary of work performed")  # Required, no default
    detailed_results_json: Optional[str] = Field(default=None, description="Detailed structured results as JSON string")
    next_steps: Optional[List[str]] = Field(default=None, description="Suggested next actions")
    suggested_handoff_target_role: Optional[str] = Field(default=None, description="Role to hand off to if required")
    resources_consumed_json: Optional[str] = Field(default=None, description="Resource usage as JSON string")
    
    model_config = ConfigDict(extra="forbid")

class CapabilityVerificationOutput(BaseModel):
    verification_status: Literal["passed", "failed"] = Field(..., description="Verification result")
    available_tools: List[str] = Field(default_factory=list, description="List of available tools")
    model_being_used: str = Field(..., description="Model being used")
    missing_requirements: Optional[List[str]] = Field(default=None, description="Missing requirements")
    recommendations: Optional[List[str]] = Field(default=None, description="Recommendations")
    notes: Optional[str] = Field(default=None, description="Additional notes")
    
    model_config = ConfigDict(extra="forbid")

class TaskCreationOutput(BaseModel):
    success: bool = Field(..., description="Whether task creation succeeded")
    task_id: Optional[str] = Field(default=None, description="Created task ID")
    task_name: str = Field(..., description="Task name")
    assigned_agent_name: Optional[str] = Field(default=None, description="Agent assigned to task")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    
    model_config = ConfigDict(extra="forbid")

class HandoffRequestOutput(BaseModel):
    success: bool = Field(..., description="Whether handoff succeeded")
    message: str = Field(..., description="Status message")
    handoff_task_id: Optional[str] = Field(default=None, description="Created handoff task ID")
    assigned_to_agent_name: Optional[str] = Field(default=None, description="Agent receiving handoff")
    
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
        
    def _determine_asset_type_from_task(self, task: Task) -> Optional[str]:
        """Determina il tipo di asset dal task corrente"""
        
        if not task:
            return None
        
        # Metodo 1: Context data esplicito
        if isinstance(task.context_data, dict):
            asset_type = task.context_data.get('asset_type') or task.context_data.get('target_schema')
            if asset_type:
                return asset_type
        
        # Metodo 2: Analisi nome task
        task_name = (task.name or "").lower()
        asset_type_mapping = {
            "contact": "contact_database",
            "content": "content_calendar", 
            "calendar": "content_calendar",
            "training": "training_program",
            "workout": "training_program",
            "financial": "financial_model",
            "budget": "financial_model",
            "research": "research_database",
            "strategy": "strategy_framework"
        }
        
        for keyword, asset_type in asset_type_mapping.items():
            if keyword in task_name:
                return asset_type
        
        return None

    def _create_agent(self) -> OpenAIAgent:
        """
        MODIFICATA: Usa prompt asset-oriented per specialist agents
        Mantiene logica esistente per Project Manager
        """
        llm_config = self.agent_data.llm_config or {}
        model_name = llm_config.get("model") or self.seniority_model_map.get(self.agent_data.seniority.value, "gpt-4.1-nano")
        temperature = llm_config.get("temperature", 0.3)

        is_manager_type_role = any(keyword in self.agent_data.role.lower() 
                                for keyword in ['manager', 'coordinator', 'director', 'lead'])

        # ENHANCED: Usa prompt appropriato basato sul ruolo
        if is_manager_type_role:
            # Per i Project Manager: usa il prompt esistente
            instructions = self._create_project_manager_prompt()
        else:
            # Per i Specialist: usa il NUOVO prompt asset-oriented
            instructions = self._create_asset_oriented_specialist_prompt()

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

        # Handoffs SDK per Project Manager (logica esistente)
        if SDK_AVAILABLE and is_manager_type_role and self.direct_sdk_handoffs:
            agent_config["handoffs"] = self.direct_sdk_handoffs
            logger.info(f"Agent {self.agent_data.name} (Manager type) configured with {len(self.direct_sdk_handoffs)} SDK handoffs.")

        return OpenAIAgent(**agent_config)

    def _create_project_manager_prompt(self) -> str:
        """Prompt specifico per Project Manager con validazione fasi OBBLIGATORIA"""

        # Import delle fasi
        try:
            from models import ProjectPhase, PHASE_DESCRIPTIONS
            phase_list = "\n".join([f"- {phase.value}: {desc}" for phase, desc in PHASE_DESCRIPTIONS.items()])
        except ImportError:
            # Fallback se le nuove fasi non sono ancora disponibili
            phase_list = "- ANALYSIS: Research and analysis tasks\n- IMPLEMENTATION: Strategy and planning\n- FINALIZATION: Content creation and execution"

        base_prompt_prefix = handoff_prompt.RECOMMENDED_PROMPT_PREFIX if SDK_AVAILABLE else ""

        available_tool_names = []
        for tool in self.tools:
            tool_name_attr = getattr(tool, 'name', getattr(tool, '__name__', None))
            if tool_name_attr: available_tool_names.append(tool_name_attr)

        return f"""
    {base_prompt_prefix}
    You are a highly efficient AI Project Manager. Your name is {self.agent_data.name}.

    CRITICAL PROJECT PHASE MANAGEMENT:
    You MUST work with these EXACT project phases:
    {phase_list}

    MANDATORY PHASE VALIDATION RULES:
    1. ALWAYS specify "current_project_phase" in your detailed_results_json
    2. EVERY sub-task MUST have a "project_phase" field
    3. Use ONLY the exact phase values: ANALYSIS, IMPLEMENTATION, FINALIZATION
    4. You cannot skip phases - they must progress linearly
    
    MANDATORY JSON OUTPUT STRUCTURE:
    Your `detailed_results_json` output field MUST be a VALID JSON STRING containing the following keys:
    1.  `current_project_phase` (STRING, MANDATORY): This indicates the primary project phase you are currently planning tasks FOR or operating WITHIN. Example: "ANALYSIS", "IMPLEMENTATION", "FINALIZATION".
    2.  `phase_rationale` (STRING): Your reasoning for the current phase and the sub-tasks defined.
    3.  `defined_sub_tasks` (ARRAY of OBJECTS): A list of sub-tasks. Each sub-task object in this array MUST include:
        * `name` (STRING): Specific name for the sub-task.
        * `description` (STRING): Detailed description for the sub-task.
        * `target_agent_role` (STRING): The EXACT agent NAME (obtained from `get_team_roles_and_status` tool) to assign this task to.
        * `priority` (STRING: "low", "medium", or "high").
        * `project_phase` (STRING, MANDATORY): The specific phase this sub-task belongs to (e.g., "ANALYSIS").
        * `task_id` (STRING, OPTIONAL): If you ALREADY CALLED `create_and_assign_sub_task` for this conceptual task during your execution, include the `task_id` you received from the tool's JSON response (even if success was false due to duplication, use the `task_id` of the existing duplicate if provided by the tool). Otherwise, omit this field.
    4.  `phase_completion_criteria` (ARRAY of STRINGS): Criteria for completing the current phase.
    5.  `next_phase_trigger` (STRING): Trigger for moving to the next phase.

    WORKFLOW FOR TASK DELEGATION:
    1.  **FIRST: Call `get_team_roles_and_status` to get the EXACT names and roles of your active team members.** This is crucial for correct assignment.
    2.  **ASSESS CURRENT STATE & EXISTING TASKS:**
        * Determine the current project phase based on work completed so far.
        * Review the output of previously completed tasks in the current or preceding phases.
        * **CRITICAL: Before creating a new sub-task, consider if its objective is already covered by an existing 'pending' or 'in_progress' task for the target agent/role. Avoid creating duplicate tasks.**
        * If a similar task was 'completed' but the output was unsatisfactory, create a new task with a name like "REVISE: [Original Task Name]" or "ENHANCE: [Original Task Name]", clearly stating what needs to be improved or added based on the previous output.
    3.  **Define Sub-Tasks:** Based on your assessment, define specific, actionable sub-tasks for the *current* or *next logical* phase. Each sub-task should have a clear deliverable.
    4.  **Assign Tasks:** Use the `create_and_assign_sub_task` tool.
        * **Use EXACT agent names** from `get_team_roles_and_status` for the `target_agent_role` parameter.
        * Provide a comprehensive `task_description` including all necessary context, inputs, and expected deliverables.
        * Specify the correct `project_phase` for each sub-task.

    CRITICAL OUTPUT FORMAT for detailed_results_json:
    {{
        "current_project_phase": "ANALYSIS", // Current phase you are planning FOR or CURRENTLY IN
        "phase_rationale": "Rationale for this phase and the sub-tasks defined.",
        "defined_sub_tasks": [ // List of sub-tasks you intend to create OR have ALREADY actioned using tools
            {{
                // If you ALREADY CALLED 'create_and_assign_sub_task' for this conceptual task during your execution,
                // you MUST include the 'task_id' you received from the tool's JSON response (even if success was false due to duplication).
                // If the tool indicated success:false and provided an existing task_id (duplicate found), use THAT task_id.
                // If the tool call failed critically and no task_id was returned, DO NOT include this task_id field for this entry.
                "task_id": "OPTIONAL_EXISTING_OR_NEWLY_CREATED_TASK_ID_FROM_TOOL", 
                "name": "Specific Sub-Task Name", // This MUST match the name you used in the tool call
                "description": "Detailed description used in the tool call...",
                "target_agent_role": "ExactAgentNameFromToolUsed", // Exact agent NAME used in tool
                "priority": "high", // Priority used in tool
                "project_phase": "ANALYSIS" // Phase used in tool
            }}
            // ... more sub-tasks, each reflecting a tool call you made
        ],
        "phase_completion_criteria": ["All sub-tasks for this phase completed", "Deliverables for this phase reviewed"],
        "next_phase_trigger": "When all [Current Phase Name] tasks are completed and reviewed."
    }}
    
    EXAMPLE SCENARIO (Avoiding Duplication):
    - Goal: Create marketing content.
    - Phase: ANALYSIS. PM delegates "Research Target Audience" to AnalysisSpecialist.
    - AnalysisSpecialist completes "Research Target Audience". Output: "Audience is X, Y, Z."
    - PM reviews. If output is good, PM proceeds to plan IMPLEMENTATION tasks (e.g., "Create Content Plan for X, Y, Z").
    - If "Research Target Audience" output was insufficient (e.g., missing Z), PM creates:
      "REVISE: Research Target Audience - Add details for Z" OR
      "New Task: Deep Dive Research on Audience Z", assigning it to AnalysisSpecialist.
      PM does NOT simply re-create "Research Target Audience".

    PHASE-SPECIFIC TASK EXAMPLES:

    ANALYSIS Phase Tasks:
    - Competitor analysis, audience research, market studies
    - Target role: "AnalysisSpecialist" or "ResearchSpecialist"

    IMPLEMENTATION Phase Tasks:
    - Strategy creation, planning frameworks, templates, workflows
    - Target role: "ContentSpecialist" or "StrategySpecialist"

    FINALIZATION Phase Tasks:
    - Content creation, publishing, execution, final deliverables
    - Target role: "ContentSpecialist" or "PublishingSpecialist"

    ERROR PREVENTION:
    - If you don't specify project_phase, the task will fail
    - If you use invalid phase names, they will be auto-corrected to ANALYSIS
    - If you skip phases, the system will reject the transition

    Available tools: {', '.join(available_tool_names)}

    YOUR FINAL JSON MUST INCLUDE current_project_phase AND project_phase FOR EACH SUB-TASK!
    Prioritize completing all tasks of the current phase before extensively planning for subsequent phases unless a task has explicit cross-phase dependencies.
    """.strip()

    def _create_specialist_anti_loop_prompt(self) -> str:
        """Prompt specifico per specialist agents (non-manager) con JSON migliorato"""
        available_tool_names = []
        for tool in self.tools:
            tool_name_attr = getattr(tool, 'name', getattr(tool, '__name__', None))
            if tool_name_attr: 
                available_tool_names.append(tool_name_attr)

        # Creazione delle sezioni personalità (rimane uguale)
        personality_section = ""
        if self.agent_data.personality_traits:
            traits = [trait.value for trait in self.agent_data.personality_traits]
            personality_section = f"Your personality traits are: {', '.join(traits)}.\n"

        communication_section = ""
        if self.agent_data.communication_style:
            communication_section = f"Your communication style is: {self.agent_data.communication_style}.\n"

        hard_skills_section = ""
        if self.agent_data.hard_skills:
            skills = [f"{skill.name} ({skill.level.value})" for skill in self.agent_data.hard_skills]
            hard_skills_section = f"Your technical skills include: {', '.join(skills)}.\n"

        soft_skills_section = ""
        if self.agent_data.soft_skills:
            skills = [f"{skill.name} ({skill.level.value})" for skill in self.agent_data.soft_skills]
            soft_skills_section = f"Your interpersonal skills include: {', '.join(skills)}.\n"

        background_section = ""
        if self.agent_data.background_story:
            background_section = f"Background: {self.agent_data.background_story}\n"

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

    🚨 CRITICAL JSON OUTPUT REQUIREMENTS:
    7.  If your task requires detailed_results_json, it MUST be valid JSON:
        * NO trailing commas
        * Use double quotes for strings
        * Escape special characters properly (\\" for quotes, \\\\ for backslashes)
        * Test your JSON mentally before outputting
        * If unsure about JSON validity, keep it simple with basic strings and arrays

    8.  For FINAL DELIVERABLE tasks specifically:
        * The detailed_results_json is CRITICAL for project success
        * It must include "executive_summary" field with comprehensive content
        * Follow the exact JSON template provided in the task description
        * Double-check JSON syntax - invalid JSON will break the deliverable

    OUTPUT REQUIREMENTS:
    Your final output for EACH task execution MUST be a single, valid JSON object matching the 'TaskExecutionOutput' schema:
    - "task_id": (string) ID of the current task being processed (e.g., "{self._current_task_being_processed_id or 'CURRENT_TASK_ID'}").
    - "status": (string) Must be one of: "completed", "failed", "requires_handoff". Default to "completed" if substantial work is done.
    - "summary": (string) Concise summary of the work performed and the outcome. THIS IS MANDATORY.
    - "detailed_results_json": (string, optional) A VALID JSON STRING containing detailed, structured results. NULL if not applicable. MUST be valid JSON if provided.
    - "next_steps": (array of strings, optional) Only if you completed the task and have suggestions for the PM or for future work based on your findings.
    - "suggested_handoff_target_role": (string, optional) ONLY if status is "requires_handoff". Specify the different specialist role to hand off to.
    - "resources_consumed_json": (string, optional) A JSON string for any notable resource usage.

    JSON VALIDATION CHECKLIST (for detailed_results_json):
    ✅ All strings use double quotes (not single quotes)
    ✅ No trailing commas after last items in objects/arrays
    ✅ Special characters are properly escaped
    ✅ Numbers don't have leading/trailing spaces
    ✅ Boolean values are lowercase (true/false, not True/False)
    ✅ No undefined or null values (use "null" if needed)

    Example of a 'completed' task with VALID JSON:
    {{
      "task_id": "{self._current_task_being_processed_id or 'CURRENT_TASK_ID'}",
      "status": "completed",
      "summary": "Analyzed competitor X's Instagram strategy, identifying 3 key content pillars and an average engagement rate of 2.5%.",
      "detailed_results_json": "{{\\"competitor_analysis\\": {{\\"name\\": \\"Competitor X\\", \\"content_pillars\\": [\\"Pillar A\\", \\"Pillar B\\", \\"Pillar C\\"], \\"engagement_rate\\": 0.025}}}}",
      "next_steps": ["Recommend PM to review findings for strategic adjustments."],
      "suggested_handoff_target_role": null,
      "resources_consumed_json": null
    }}

    ⚠️ FINAL VALIDATION: Before outputting your response, mentally check that any JSON string in detailed_results_json is valid!

    Do NOT add any text before or after this final JSON object. Your entire response must be this JSON.
    """.strip()
    
    
    def _create_asset_oriented_specialist_prompt(self) -> str:
        """
        Prompt enhancer per specialist agents quando devono produrre asset azionabili
        ENHANCED: Con integrazione AI Quality Assurance
        """

        base_prompt = self._create_specialist_anti_loop_prompt()

        # Asset-oriented enhancement (codice esistente)
        asset_enhancement = """

    🎯 **ENHANCED ASSET PRODUCTION MODE**

    When your task is marked as "asset production" (check context_data.asset_production or task name contains "PRODUCE ASSET:"), 
    you must focus on creating IMMEDIATELY ACTIONABLE business assets instead of strategic reports.

    **ASSET PRODUCTION REQUIREMENTS**:
    1. **Structured Output**: Your detailed_results_json MUST contain structured, ready-to-use data
    2. **No Placeholders**: Replace ALL placeholder text with real, actionable content
    3. **Business Ready**: Output should be copy-paste ready for business use
    4. **Validation Ready**: Follow exact schema if provided in task description

    **EXAMPLES OF ASSET-ORIENTED OUTPUT**:

    For Contact Database Task:
    ```json
    {
      "contacts": [
        {
          "name": "Mario Rossi",
          "company": "TechCorp Italia", 
          "email": "mario.rossi@techcorp.it",
          "phone": "+39 02 1234567",
          "title": "Marketing Director",
          "qualification_score": 8,
          "next_action": "send_introduction_email",
          "notes": "Interested in B2B marketing automation"
        }
      ],
      "total_contacts": 25,
      "data_sources": ["LinkedIn Sales Navigator", "Industry Events"],
      "quality_metrics": {"email_verified": 0.95, "phone_verified": 0.80}
    }
    ```

    🚨 CRITICAL FOR ASSET PRODUCTION:
    - Replace generic examples with specific, real content
    - Ensure data is structured for immediate business use
    - Include usage instructions and implementation guidance
    - Validate output against provided schema if available
    - Focus on business value and actionability over strategic insights

    If your task is NOT asset production, continue with standard analytical/strategic approach.
    """

        enhanced_prompt = base_prompt + asset_enhancement

        # === NUOVA INTEGRAZIONE AI QUALITY ASSURANCE ===
        if QUALITY_SYSTEM_AVAILABLE and QualitySystemConfig.ENABLE_AI_QUALITY_EVALUATION:
            try:
                # Determina asset type dal task corrente se possibile
                asset_type = None
                if (self._current_task_being_processed_id and 
                    hasattr(self, '_current_task_context')):
                    task_context = getattr(self, '_current_task_context', {})
                    if isinstance(task_context, dict):
                        asset_type = task_context.get('asset_type') or task_context.get('target_schema')

                # Applica enhancement per qualità
                quality_enhanced_prompt = DynamicPromptEnhancer.enhance_specialist_prompt_for_quality(
                    enhanced_prompt,
                    asset_type=asset_type
                )

                logger.info(f"🔧 QUALITY: Agent {self.agent_data.name} using quality-enhanced prompt (target: {QualitySystemConfig.QUALITY_SCORE_THRESHOLD})")
                return quality_enhanced_prompt

            except Exception as e:
                logger.warning(f"Quality prompt enhancement failed for {self.agent_data.name}: {e}")
                return enhanced_prompt

        return enhanced_prompt


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
            # FIX PRINCIPALE: Tool specifici per Project Manager
            try:
                # Crea istanza PMOrchestrationTools con workspace_id corretto
                pm_tools = PMOrchestrationTools(str(self.agent_data.workspace_id))

                # Aggiungi i tool chiamando i metodi di istanza (non più statici)
                tools_list.append(pm_tools.create_and_assign_sub_task_tool())
                tools_list.append(pm_tools.get_team_roles_and_status_tool())

                logger.info(f"Agent {self.agent_data.name} ({self.agent_data.role}) equipped with PMOrchestrationTools for workspace {self.agent_data.workspace_id}.")
            except Exception as e:
                logger.error(f"Error initializing PMOrchestrationTools for {self.agent_data.name}: {e}", exc_info=True)
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
            except ImportError: 
                logger.warning("InstagramTools not available or path is incorrect (tools.social_media).")
            except AttributeError: 
                logger.warning("InstagramTools found, but some specific tools are missing.")

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

    def _calculate_token_costs(
        self, 
        run_result: Any, 
        model_name: str, 
        estimated_input_tokens: int,
        execution_time: float
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Calcola token usage e costi dal run result"""
        try:
            # Tenta di estrarre token usage dal run_result
            input_tokens = estimated_input_tokens
            output_tokens = 0
            
            # Metodi per estrarre token usage (dipende dalla versione SDK)
            if hasattr(run_result, 'usage'):
                usage = run_result.usage
                input_tokens = getattr(usage, 'input_tokens', estimated_input_tokens)
                output_tokens = getattr(usage, 'output_tokens', 0)
            elif hasattr(run_result, 'token_usage'):
                usage = run_result.token_usage
                input_tokens = usage.get('input_tokens', estimated_input_tokens)
                output_tokens = usage.get('output_tokens', 0)
            elif hasattr(run_result, '_response_data'):
                # Fallback per accesso ai dati raw
                response_data = run_result._response_data
                if isinstance(response_data, dict) and 'usage' in response_data:
                    usage = response_data['usage']
                    input_tokens = usage.get('prompt_tokens', estimated_input_tokens)
                    output_tokens = usage.get('completion_tokens', 0)
            else:
                # Stima basata su output length se no token data disponibili
                if hasattr(run_result, 'final_output'):
                    output_text = str(run_result.final_output)
                    output_tokens = max(1, len(output_text.split()) * 1.3)
            
            # Calcola costi
            costs = TOKEN_COSTS.get(model_name, TOKEN_COSTS.get("gpt-4.1-mini", {}))
            if costs:
                input_cost = (input_tokens / 1000) * costs.get("input", 0)
                output_cost = (output_tokens / 1000) * costs.get("output", 0)
                total_cost = input_cost + output_cost
            else:
                input_cost = output_cost = total_cost = 0.0
            
            token_usage = {
                "input_tokens": int(input_tokens),
                "output_tokens": int(output_tokens),
                "total_tokens": int(input_tokens + output_tokens)
            }
            
            cost_data = {
                "input_cost": round(input_cost, 6),
                "output_cost": round(output_cost, 6),
                "total_cost": round(total_cost, 6),
                "currency": "USD",
                "cost_per_hour": round(total_cost * 3600 / execution_time, 6) if execution_time > 0 else 0
            }
            
            return token_usage, cost_data
            
        except Exception as e:
            logger.warning(f"Error calculating token costs: {e}")
            return {}, {}
    
    async def _register_usage_in_budget_tracker(
        self, 
        task_id: str, 
        model_name: str, 
        token_usage: Dict[str, Any], 
        cost_data: Dict[str, Any]
    ):
        """Registra l'usage nel BudgetTracker globale"""
        try:
            # Import del task_executor globale
            from executor import task_executor
            
            if token_usage and cost_data:
                task_executor.budget_tracker.log_usage(
                    agent_id=str(self.agent_data.id),
                    model=model_name,
                    input_tokens=token_usage.get("input_tokens", 0),
                    output_tokens=token_usage.get("output_tokens", 0),
                    task_id=task_id
                )
                
                logger.info(f"Registered usage in BudgetTracker: Agent {self.agent_data.name}, "
                           f"Task {task_id}, Cost: ${cost_data.get('total_cost', 0):.6f}")
        except Exception as e:
            logger.error(f"Error registering usage in BudgetTracker: {e}")

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
        
        start_time = time.time()

        try:
            if SDK_AVAILABLE:
                _trace_cm = trace(workflow_name=workflow_name, trace_id=trace_id_val, group_id=str(task.id))
                if hasattr(_trace_cm, "__aenter__"):
                    trace_context_manager = _trace_cm
                else:
                    @contextlib.asynccontextmanager
                    async def _wrap():
                        with _trace_cm:
                            yield
                    trace_context_manager = _wrap()
            else:
                trace_context_manager = _dummy_async_context_manager()
        except (AttributeError, TypeError) as e:
            logger.warning(f"SDK trace failed ({e}), using dummy context manager")
            trace_context_manager = _dummy_async_context_manager()
        
        async with trace_context_manager: # type: ignore
            try:
                await self._log_execution_internal(
                    "task_execution_started",
                    {"task_id": str(task.id), "task_name": task.name, "trace_id": trace_id_val, "assigned_role": task.assigned_to_role}
                )
                await update_task_status(task_id=str(task.id), status=TaskStatus.IN_PROGRESS.value, result_payload={"status_detail": "Execution started by agent"})
                
                task_context_info = ""
                if task.context_data:
                    try:
                        context_json_str = json.dumps(task.context_data)
                        task_context_info = f"\nADDITIONAL CONTEXT FOR THIS TASK (JSON):\n{context_json_str}"
                    except Exception as e:
                        logger.warning(f"Could not serialize context_data for task {task.id}: {e}. Passing as string.")
                        task_context_info = f"\nADDITIONAL CONTEXT FOR THIS TASK (Raw String):\n{str(task.context_data)}"

                task_prompt_content = f"Current Task ID: {task.id}\nTask Name: {task.name}\nTask Priority: {task.priority}\nTask Description:\n{task.description}{task_context_info}\n---\nRemember to use your tools and expertise as per your system instructions. Your final output MUST be a single JSON object matching the 'TaskExecutionOutput' schema."
                
                # NUOVO: Stima token di input per calcolo costi
                input_text = f"{task.name} {task.description or ''}"
                estimated_input_tokens = max(1, len(input_text.split()) * 1.3)  # Stima approssimativa
                
                # Ottieni il modello usato
                model_name = self.agent.model
                
                max_turns_for_agent = 10
                if isinstance(self.agent_data.llm_config, dict) and "max_turns_override" in self.agent_data.llm_config:
                    max_turns_for_agent = self.agent_data.llm_config["max_turns_override"]

                agent_run_result = await asyncio.wait_for(
                    Runner.run(self.agent, task_prompt_content, max_turns=max_turns_for_agent, context=context),
                    timeout=self.execution_timeout
                )
                
                elapsed_time = time.time() - start_time
                
                # NUOVO: Calcolo automatico dei costi/token
                token_usage, cost_data = self._calculate_token_costs(
                    agent_run_result, model_name, estimated_input_tokens, elapsed_time
                )

                final_llm_output = agent_run_result.final_output
                # ENHANCED: Parsing robusto dell'output dell'agente
                execution_result_obj: TaskExecutionOutput
                parsing_method = "unknown"
                
                if isinstance(final_llm_output, TaskExecutionOutput):
                    # Output già nel formato corretto
                    execution_result_obj = final_llm_output
                    parsing_method = "direct_taskexecutionoutput"
                    logger.info(f"Task {task.id}: Direct TaskExecutionOutput received")
                    
                elif isinstance(final_llm_output, dict):
                    # Output dict - prova validazione diretta
                    try:
                        final_llm_output.setdefault('task_id', str(task.id))
                        final_llm_output.setdefault('status', 'completed')
                        final_llm_output.setdefault('summary', 'Task processing completed by agent.')
                        execution_result_obj = TaskExecutionOutput.model_validate(final_llm_output)
                        parsing_method = "direct_dict_validation"
                        logger.info(f"Task {task.id}: Direct dict validation successful")
                    except Exception as val_err:
                        logger.warning(f"Task {task.id}: Dict validation failed: {val_err}")
                        # Fallback a parsing robusto del dict serializzato
                        if ROBUST_JSON_AVAILABLE:
                            try:
                                dict_as_json = json.dumps(final_llm_output)
                                parsed_data, is_complete, method = parse_llm_json_robust(
                                    dict_as_json, str(task.id)
                                )
                                parsed_data.setdefault('task_id', str(task.id))
                                execution_result_obj = TaskExecutionOutput.model_validate(parsed_data)
                                parsing_method = f"robust_dict_recovery_{method}"
                                logger.info(f"Task {task.id}: Robust dict recovery successful ({method})")
                            except Exception as robust_err:
                                logger.error(f"Task {task.id}: Robust dict recovery failed: {robust_err}")
                                execution_result_obj = TaskExecutionOutput(
                                    task_id=str(task.id), status="failed", 
                                    summary=f"Dict validation and recovery failed: {val_err}",
                                    detailed_results_json=json.dumps({
                                        "error": "validation_and_recovery_failed",
                                        "original_validation_error": str(val_err),
                                        "robust_recovery_error": str(robust_err),
                                        "raw_output": str(final_llm_output)[:1000]
                                    })
                                )
                                parsing_method = "error_fallback_dict"
                        else:
                            # Fallback senza robust parser
                            execution_result_obj = TaskExecutionOutput(
                                task_id=str(task.id), status="failed", 
                                summary=f"Output validation error: {val_err}",
                                detailed_results_json=json.dumps({
                                    "error": "Agent output validation failed", 
                                    "raw_output": str(final_llm_output)[:1000]
                                })
                            )
                            parsing_method = "basic_fallback_dict"
                
                else:
                    # Output string - usa parsing robusto
                    logger.info(f"Task {task.id}: Processing string output with robust parser")
                    
                    if ROBUST_JSON_AVAILABLE:
                        try:
                            parsed_data, is_complete, method = parse_llm_json_robust(
                                str(final_llm_output), str(task.id)
                            )
                            
                            # Assicura campi minimi
                            parsed_data.setdefault('task_id', str(task.id))
                            parsed_data.setdefault('status', 'completed' if is_complete else 'failed')
                            
                            if not is_complete:
                                # Aggiungi nota sul parsing incompleto
                                original_summary = parsed_data.get('summary', '')
                                parsed_data['summary'] = f"{original_summary} [Note: Output was truncated/incomplete, recovery applied]"
                            
                            execution_result_obj = TaskExecutionOutput.model_validate(parsed_data)
                            parsing_method = f"robust_string_{method}"
                            
                            completion_status = "✅ Complete" if is_complete else "⚠️ Incomplete/Recovered"
                            logger.info(f"Task {task.id}: Robust string parsing successful - {completion_status} ({method})")
                            
                        except Exception as robust_err:
                            logger.error(f"Task {task.id}: Robust string parsing failed: {robust_err}")
                            # Create error fallback
                            execution_result_obj = TaskExecutionOutput(
                                task_id=str(task.id), status="failed",
                                summary=f"String output parsing failed: {str(robust_err)[:100]}",
                                detailed_results_json=json.dumps({
                                    "error": "robust_string_parsing_failed",
                                    "parsing_error": str(robust_err),
                                    "raw_output_length": len(str(final_llm_output)),
                                    "raw_output_preview": str(final_llm_output)[:500]
                                })
                            )
                            parsing_method = "error_fallback_string"
                    else:
                        # Fallback senza robust parser - usa logica originale semplificata
                        logger.warning(f"Task {task.id}: Using basic string parsing (robust parser unavailable)")
                        try:
                            # Prova estrazione JSON semplice
                            json_match = re.search(r'\{.*\}', str(final_llm_output), re.DOTALL)
                            if json_match:
                                basic_json = json.loads(json_match.group())
                                basic_json.setdefault('task_id', str(task.id))
                                basic_json.setdefault('status', 'completed')
                                basic_json.setdefault('summary', f"Basic extraction from string output")
                                execution_result_obj = TaskExecutionOutput.model_validate(basic_json)
                                parsing_method = "basic_string_extraction"
                            else:
                                raise ValueError("No JSON found in string output")
                        except Exception:
                            execution_result_obj = TaskExecutionOutput(
                                task_id=str(task.id), status="failed",
                                summary=f"Basic string parsing failed. Raw output: {str(final_llm_output)[:200]}...",
                                detailed_results_json=json.dumps({
                                    "error": "basic_string_parsing_failed",
                                    "raw_output_snippet": str(final_llm_output)[:1000]
                                })
                            )
                            parsing_method = "basic_fallback"
                
                # Log del metodo di parsing utilizzato per monitoring
                logger.info(f"Task {task.id}: Final parsing method: {parsing_method}")
                await self._log_execution_internal(
                    "output_parsing_completed",
                    {
                        "task_id": str(task.id),
                        "parsing_method": parsing_method,
                        "final_status": execution_result_obj.status,
                        "output_type": type(final_llm_output).__name__
                    }
                )
                
                execution_result_obj.task_id = str(task.id) 
                
                if token_usage or cost_data:
                    resources_consumed = {
                        "model": model_name,
                        "execution_time_seconds": round(elapsed_time, 2),
                        **token_usage,
                        **cost_data,
                        "timestamp": datetime.now().isoformat()
                    }
                    # Assicura che detailed_results_json sia una stringa valida
                    if not isinstance(execution_result_obj.detailed_results_json, (str, type(None))):
                        logger.warning(f"detailed_results_json is not a string or None for task {task.id}, attempting to stringify. Type: {type(execution_result_obj.detailed_results_json)}")
                        try:
                            execution_result_obj.detailed_results_json = json.dumps(execution_result_obj.detailed_results_json)
                        except Exception: # Non dovrebbe succedere se Pydantic fa il suo lavoro
                            execution_result_obj.detailed_results_json = json.dumps({"error": "Failed to stringify detailed_results_json"})
                    
                    execution_result_obj.resources_consumed_json = json.dumps(resources_consumed)
                
                result_dict_to_save = execution_result_obj.model_dump(exclude_none=True) # exclude_none=True per pulizia
                
                result_dict_to_save["execution_time_seconds"] = round(elapsed_time, 2)
                result_dict_to_save["model_used"] = model_name
                result_dict_to_save["status_detail"] = f"{execution_result_obj.status}_by_agent"

                # Estrazione di costi e token da resources_consumed_json, se presenti
                if execution_result_obj.resources_consumed_json:
                    try:
                        resources = json.loads(execution_result_obj.resources_consumed_json)
                        if isinstance(resources, dict):
                            result_dict_to_save["cost_estimated"] = resources.get("total_cost") # Già total_cost in resources
                            
                            input_tokens = resources.get("input_tokens")
                            output_tokens = resources.get("output_tokens")
                            if input_tokens is not None and output_tokens is not None:
                                result_dict_to_save["tokens_used"] = {"input": input_tokens, "output": output_tokens}
                            elif "total_tokens" in resources:
                                result_dict_to_save["tokens_used"] = {"input": resources["total_tokens"], "output": 0} # Stima grezza
                    except Exception as e:
                        logger.warning(f"Error extracting cost/tokens from resources_consumed_json for task {task.id}: {e}")
                
                result_dict_to_save["trace_id_for_run"] = trace_id_val
                
                # NUOVO: Ottimizza output prima del salvataggio per prevenire problemi di lunghezza
                if ROBUST_JSON_AVAILABLE:
                    result_dict_to_save, was_optimized, optimizations = optimize_agent_output(
                        result_dict_to_save, str(task.id)
                    )
                    if was_optimized:
                        logger.info(f"Task {task.id}: Output optimized to prevent length issues - Applied: {optimizations}")
                        # Aggiungi metadata sull'ottimizzazione
                        if "status_detail" in result_dict_to_save:
                            result_dict_to_save["status_detail"] += f" | Output optimized: {len(optimizations)} modifications"

                await self._register_usage_in_budget_tracker(
                    str(task.id), model_name, token_usage, cost_data
                )

                final_db_status = TaskStatus.COMPLETED.value
                if execution_result_obj.status == "failed":
                    final_db_status = TaskStatus.FAILED.value
                elif execution_result_obj.status == "requires_handoff":
                    final_db_status = TaskStatus.COMPLETED.value 
                    logger.info(f"Task {task.id} by {self.agent_data.name} resulted in 'requires_handoff' to role '{execution_result_obj.suggested_handoff_target_role}'. This task is marked COMPLETED.")
                
                # === INTEGRAZIONE AI QUALITY ASSURANCE ===
                if (QUALITY_SYSTEM_AVAILABLE and 
                    QualitySystemConfig.ENABLE_AI_QUALITY_EVALUATION):
                    try:
                        # Verifica se è un task di produzione asset
                        task_context = task.context_data if isinstance(task.context_data, dict) else {}
                        is_asset_task = (
                            task_context.get("asset_production") or 
                            task_context.get("asset_oriented_task") or
                            "PRODUCE ASSET:" in task.name.upper()
                        )
                        
                        if is_asset_task and execution_result_obj.status == "completed":
                            # Aggiungi nota qualità al risultato
                            quality_note = (
                                f"🔧 QUALITY ASSURANCE: This asset will be automatically evaluated "
                                f"(target: {QualitySystemConfig.QUALITY_SCORE_THRESHOLD}/1.0). "
                                f"Outputs below threshold will trigger enhancement tasks."
                            )
                            
                            # Aggiungi la nota al payload del database
                            if "status_detail" not in result_dict_to_save:
                                result_dict_to_save["status_detail"] = quality_note
                            else:
                                result_dict_to_save["status_detail"] += f" | {quality_note}"
                            
                            # Aggiungi flag per identificare asset tasks nel DB
                            result_dict_to_save["ai_quality_evaluation_pending"] = True
                            result_dict_to_save["asset_production_task"] = True
                            
                            logger.info(f"🔧 QUALITY: Added quality evaluation note to task {task.id}")
                    
                    except Exception as e:
                        logger.debug(f"Error adding quality note to task {task.id}: {e}")

                # Continua con update_task_status come nel codice originale...
                await update_task_status(task_id=str(task.id), status=final_db_status, result_payload=result_dict_to_save)
                
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
                elapsed_time = time.time() - start_time
                timeout_summary = f"Task forcibly marked as TIMED_OUT after {self.execution_timeout}s."
                logger.warning(f"Task {task.id} (Trace: {trace_id_val}) timed out ({self.execution_timeout}s).")
                timeout_result_obj = TaskExecutionOutput(
                    task_id=str(task.id), status="failed",
                    summary=timeout_summary,
                    detailed_results_json=json.dumps({"error": "TimeoutError", "reason": "Task execution exceeded timeout limit."})
                )
                timeout_result = timeout_result_obj.model_dump()
                timeout_result["trace_id_for_run"] = trace_id_val
                timeout_result["execution_time_seconds"] = round(elapsed_time, 2)
                timeout_result["model_used"] = self.agent.model
                timeout_result["status_detail"] = "timed_out_by_agent_system"
                await update_task_status(task_id=str(task.id), status=TaskStatus.TIMED_OUT.value, result_payload=timeout_result)
                await self._log_execution_internal("task_execution_timeout", {"task_id": str(task.id), "summary": timeout_summary})
                return timeout_result
            
            except MaxTurnsExceeded as e: 
                elapsed_time = time.time() - start_time
                max_turns_summary = "Task forcibly marked as FAILED due to exceeding max interaction turns with LLM."
                logger.warning(f"Task {task.id} (Trace: {trace_id_val}) exceeded max turns. Last output: {str(getattr(e, 'last_output', 'N/A'))[:200]}")
                max_turns_result_obj = TaskExecutionOutput(
                    task_id=str(task.id), status="failed",
                    summary=max_turns_summary,
                    detailed_results_json=json.dumps({"error": "MaxTurnsExceeded", "reason": str(e)})
                )
                max_turns_result = max_turns_result_obj.model_dump()
                max_turns_result["trace_id_for_run"] = trace_id_val
                max_turns_result["execution_time_seconds"] = round(elapsed_time, 2)
                max_turns_result["model_used"] = self.agent.model
                max_turns_result["status_detail"] = "failed_max_turns"
                await update_task_status(task_id=str(task.id), status=TaskStatus.FAILED.value, result_payload=max_turns_result)
                await self._log_execution_internal("task_execution_max_turns", {"task_id": str(task.id), "summary": max_turns_summary})
                return max_turns_result

            except Exception as e: 
                elapsed_time = time.time() - start_time
                unhandled_error_summary = f"Task failed due to an unexpected error: {str(e)[:100]}..."
                logger.error(f"Unhandled error executing task {task.id} (Trace: {trace_id_val}): {e}", exc_info=True)
                unhandled_error_result_obj = TaskExecutionOutput(
                    task_id=str(task.id), status="failed",
                    summary=unhandled_error_summary,
                    detailed_results_json=json.dumps({"error": str(e), "type": type(e).__name__})
                )
                unhandled_error_result = unhandled_error_result_obj.model_dump()
                unhandled_error_result["trace_id_for_run"] = trace_id_val
                unhandled_error_result["execution_time_seconds"] = round(elapsed_time, 2)
                unhandled_error_result["model_used"] = self.agent.model
                unhandled_error_result["status_detail"] = "failed_unhandled_exception"
                await update_task_status(task_id=str(task.id), status=TaskStatus.FAILED.value, result_payload=unhandled_error_result)
                await self._log_execution_internal("task_execution_unhandled_error", {"task_id": str(task.id), "error": str(e)[:100]})
                return unhandled_error_result
            finally:
                self._current_task_being_processed_id = None
                self._handoff_attempts_for_current_task = set()