# backend/ai_agents/specialist.py
import logging
import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Union, Literal, TypeVar, Generic, Type
from uuid import UUID
from datetime import datetime
from enum import Enum

from agents import (
    Agent as OpenAIAgent,
    Runner,
    AgentOutputSchema,
    ModelSettings,
    function_tool,
    WebSearchTool,
    FileSearchTool,
    RunContextWrapper,
    GuardrailFunctionOutput,
    TResponseInputItem,
    input_guardrail,
    output_guardrail,
)
from agents.extensions import handoff_prompt
from agents import trace, custom_span, gen_trace_id
from agents.exceptions import MaxTurnsExceeded, AgentsException, UserError
from pydantic import BaseModel, Field, ConfigDict

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
)

logger = logging.getLogger(__name__)

# --- Configurazioni generali ---
TOKEN_COSTS = {
    "gpt-4.1":       {"input": 0.03   / 1000, "output": 0.06   / 1000},
    "gpt-4.1-mini":  {"input": 0.015  / 1000, "output": 0.03   / 1000},
    "gpt-4.1-nano":  {"input": 0.01   / 1000, "output": 0.02   / 1000},
    "gpt-4-turbo":   {"input": 0.01   / 1000, "output": 0.03   / 1000},
    "gpt-3.5-turbo": {"input": 0.0005 / 1000, "output": 0.0015 / 1000},
}
DEFAULT_TOKEN_COST_MODEL = "gpt-4.1-mini"
DEFAULT_BUDGET_CALL_WARN_THRESHOLD = float(os.getenv("BUDGET_CALL_WARN_THRESHOLD", "0.05"))
DEFAULT_QUALITY_ASSURANCE_THRESHOLD = float(os.getenv("QUALITY_ASSURANCE_THRESHOLD", "0.6"))

# --- Modelli Pydantic per gli output (extra forbidden) ---
class TaskExecutionOutput(BaseModel):
    task_id: str
    status: Literal["completed", "failed", "requires_handoff"] = "completed"
    summary: str
    detailed_results_json: Optional[str] = Field(
        None,
        description="Detailed structured results serialized as JSON string."
    )
    next_steps: Optional[List[str]] = Field(
        None,
        description="Suggested next actions or follow-up tasks."
    )
    suggested_handoff_target_role: Optional[str] = Field(
        None,
        description="Role to hand off to if required."
    )
    resources_consumed_json: Optional[str] = Field(
        None,
        description="Resource usage serialized as JSON string (e.g. tokens)."
    )

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


class BudgetMonitoringGuardrailOutput(BaseModel):
    estimated_cost: float
    currency: str = "USD"
    threshold_breached: bool = False
    notes: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class QualityAssuranceGuardrailOutput(BaseModel):
    quality_score: float
    issues_found: List[str] = Field(default_factory=list)
    meets_threshold: bool

    model_config = ConfigDict(extra="forbid")


class CompletionReport(BaseModel):
    task_summary: str
    next_steps: Optional[List[str]] = None
    recommendations: Optional[str] = None
    requires_followup: bool
    handoff_target_role: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class ConversationSummary(BaseModel):
    key_points: List[str]
    user_requests: List[str]
    current_status: str
    relevant_context: Dict[str, Any]

    model_config = ConfigDict(extra="forbid")


T = TypeVar('T')

# --- Conversation Optimizer per handoff summaries ---
class ConversationOptimizer:
    def __init__(self):
        self.summarizer_agent: Optional[OpenAIAgent] = None

    async def _get_summarizer_agent(self) -> OpenAIAgent:
        if self.summarizer_agent is None:
            self.summarizer_agent = OpenAIAgent(
                name="ConversationSummarizer",
                instructions=(
                    "Summarize conversation for AI handoffs: key points, "
                    "user requests, status, relevant context."
                ),
                model="gpt-4.1-nano",
                output_type=AgentOutputSchema(ConversationSummary, strict_json_schema=False),
            )
        return self.summarizer_agent

    async def optimize_with_ai_summary(self, history: List[Dict]) -> List[Dict]:
        if len(history) <= 5:
            return history
        try:
            text = "\n".join(
                f"{m.get('role','N/A').upper()}: {m.get('content','')}" if isinstance(m, dict) else str(m)
                for m in history
            )
            summarizer = await self._get_summarizer_agent()
            res = await Runner.run(
                summarizer,
                f"Summarize this conversation history for next AI agent:\n\n{text}",
                max_turns=1
            )
            data = res.final_output
            if isinstance(data, dict):
                summary = ConversationSummary.model_validate(data)
            elif isinstance(data, ConversationSummary):
                summary = data
            else:
                raise ValueError("Unexpected summary type")
            optimized = [{
                "role": "system",
                "content": (
                    f"Summary:\n"
                    f"Key Points: {'; '.join(summary.key_points)}\n"
                    f"User Requests: {'; '.join(summary.user_requests)}\n"
                    f"Status: {summary.current_status}\n"
                    f"Context: {json.dumps(summary.relevant_context)}"
                )
            }]
            # aggiungi ultimi messaggi
            if len(history) >= 2 and history[-2].get("role") == "assistant":
                optimized.append(history[-2])
            optimized.append(history[-1])
            return optimized
        except Exception:
            # fallback: ultimi 3
            return history[-3:] if len(history) > 3 else history


# --- Guardrails ---
@input_guardrail
async def budget_monitoring_guardrail(
    ctx: RunContextWrapper,
    agent: OpenAIAgent,
    input_data: Union[str, List[TResponseInputItem]]
) -> GuardrailFunctionOutput:
    try:
        text = str(input_data)
        tokens = len(text) / 4
        model_name = getattr(agent, "model", DEFAULT_TOKEN_COST_MODEL)
        costs = TOKEN_COSTS.get(model_name, TOKEN_COSTS[DEFAULT_TOKEN_COST_MODEL])
        cost = tokens * costs["input"]
        threshold = DEFAULT_BUDGET_CALL_WARN_THRESHOLD
        breached = cost > threshold
        notes = (
            f"Est. {tokens:.0f} tokens @ {model_name} → ${cost:.6f} "
            f"(threshold ${threshold:.2f})"
        )
        if breached:
            logger.warning(f"BudgetGuardrail TRIGGERED for {agent.name}: {notes}")
        output = BudgetMonitoringGuardrailOutput(
            estimated_cost=cost,
            threshold_breached=breached,
            notes=notes
        )
        return GuardrailFunctionOutput(
            output_info=output.model_dump(),
            tripwire_triggered=breached
        )
    except Exception as e:
        logger.error(f"Error in budget guardrail: {e}", exc_info=True)
        output = BudgetMonitoringGuardrailOutput(
            estimated_cost=0.0,
            threshold_breached=False,
            notes=f"Guardrail error: {e}"
        )
        return GuardrailFunctionOutput(
            output_info=output.model_dump(),
            tripwire_triggered=False
        )


@output_guardrail
async def quality_assurance_guardrail(
    ctx: RunContextWrapper,
    agent: OpenAIAgent,
    output: Any
) -> GuardrailFunctionOutput:
    try:
        score = 1.0
        issues: List[str] = []
        threshold = DEFAULT_QUALITY_ASSURANCE_THRESHOLD

        validated: Optional[TaskExecutionOutput] = None
        if isinstance(output, dict):
            try:
                validated = TaskExecutionOutput.model_validate(output)
            except Exception:
                pass
        elif isinstance(output, TaskExecutionOutput):
            validated = output  # type: ignore

        if validated:
            if validated.status == "failed":
                score -= 0.7
                issues.append("Agent reported failure")
            if len(validated.summary) < 10:
                score -= 0.3
                issues.append("Summary too short")
            if validated.status == "completed" and (
                  validated.next_steps or validated.resources_consumed_json
               ) and not validated.detailed_results_json:
                score -= 0.2
                issues.append("Missing detailed_results_json")
        elif isinstance(output, str):
            if len(output) < 20:
                score -= 0.4
                issues.append("Text output <20 chars")
            if any(k in output.lower() for k in ["error", "failed"]):
                score -= 0.6
                issues.append("Contains error keywords")
        else:
            score -= 0.1
            issues.append(f"Unhandled type {type(output).__name__}")

        score = max(0.0, min(1.0, score))
        trip = score < threshold
        if trip:
            logger.warning(f"QualityGuardrail TRIGGERED for {agent.name}: score={score:.2f}, issues={issues}")
        info = QualityAssuranceGuardrailOutput(
            quality_score=score,
            issues_found=issues,
            meets_threshold=not trip
        )
        return GuardrailFunctionOutput(
            output_info=info.model_dump(),
            tripwire_triggered=trip
        )
    except Exception as e:
        logger.error(f"Error in quality guardrail: {e}", exc_info=True)
        info = QualityAssuranceGuardrailOutput(
            quality_score=0.0,
            issues_found=[f"Guardrail error: {e}"],
            meets_threshold=False
        )
        return GuardrailFunctionOutput(
            output_info=info.model_dump(),
            tripwire_triggered=True
        )


class SpecialistAgent(Generic[T]):
    def __init__(
        self,
        agent_data: AgentModelPydantic,
        context_type: Optional[Type[T]] = None,
        all_workspace_agents_data: Optional[List[AgentModelPydantic]] = None
    ):
        self.agent_data = agent_data
        self.context_type = context_type or dict  # type: ignore
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY not set")

        self.conversation_optimizer = ConversationOptimizer()
        self.seniority_model_map = {
            AgentSeniority.JUNIOR.value:  "gpt-4.1-nano",
            AgentSeniority.SENIOR.value:  "gpt-4.1-mini",
            AgentSeniority.EXPERT.value:  "gpt-4.1",
        }
        self.all_workspace_agents_data = all_workspace_agents_data or []

        # nomi tool
        self._task_creation_tool_name = "create_task_for_agent_tool"
        self._request_handoff_tool_name = "request_handoff_to_role_via_task"
        self._log_execution_step_tool_name = "log_execution_step"
        self._update_health_status_tool_name = "update_own_health_status"
        self._report_task_progress_tool_name = "report_task_progress"
        self._propose_custom_tool_tool_name = "propose_custom_tool_creation"

        self.tools = self._initialize_tools()
        self.direct_sdk_handoffs: List[Any] = []
        self.agent = self._create_agent()
        
        self.delegation_attempts_cache: Dict[str, int] = {}
        self.max_delegation_attempts = 3

    def _validate_and_truncate_json(self, json_str: Optional[str], max_length: int = 5000) -> Optional[str]:
        """Valida e tronca JSON se necessario per evitare errori di parsing"""
        if not json_str:
            return None
        if len(json_str) > max_length:
            logger.warning(f"JSON too long ({len(json_str)} chars), truncating to {max_length}")
            json_str = json_str[:max_length-20] + '..."truncated"}'
        try:
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON generated by agent: {e}")
            safe_content = json_str.replace('"', '\\"').replace('\n', '\\n')[:1000]
            return json.dumps({
                "raw_content": safe_content,
                "warning": "Original JSON was malformed and has been sanitized",
                "error": str(e)
            })
    
    def _initialize_tools(self) -> List[Any]:
        tools: List[Any] = [
            self._create_task_for_agent_tool(),
            self._create_request_handoff_tool(),
            self._create_log_execution_tool(),
            self._create_update_health_status_tool(),
            self._create_report_progress_tool(),
        ]

        # web_search / file_search da config
        explicit_file_search = False
        if self.agent_data.tools:
            for cfg in self.agent_data.tools:
                if not isinstance(cfg, dict):
                    continue
                ttype = cfg.get("type", "")
                if ttype == "web_search":
                    tools.append(WebSearchTool(search_context_size=cfg.get("search_context_size", "medium")))
                elif ttype == "file_search":
                    explicit_file_search = True
                    vs = getattr(self.agent_data, "vector_store_ids", [])
                    if isinstance(vs, list) and vs:
                        tools.append(FileSearchTool(
                            max_num_results=cfg.get("max_num_results", 5),
                            include_search_results=cfg.get("include_search_results", True),
                            vector_store_ids=vs
                        ))
                    else:
                        logger.warning(f"{self.agent_data.name}: skipped file_search, no vector_store_ids.")
        # fallback file_search
        if not explicit_file_search and not any(isinstance(t, FileSearchTool) for t in tools):
            vs = getattr(self.agent_data, "vector_store_ids", [])
            if isinstance(vs, list) and vs:
                logger.info(f"{self.agent_data.name}: adding FileSearchTool via fallback.")
                tools.append(FileSearchTool(
                    vector_store_ids=vs,
                    max_num_results=3,
                    include_search_results=True
                ))

        # instagram
        if "social media" in self.agent_data.role.lower() or "instagram" in self.agent_data.role.lower():
            try:
                from tools.social_media import InstagramTools
                tools.extend([
                    InstagramTools.analyze_hashtags,
                    InstagramTools.analyze_account,
                    InstagramTools.generate_content_ideas,
                    InstagramTools.analyze_competitors,
                ])
            except ImportError:
                logger.warning("InstagramTools not available.")

        # custom tool
        if self.agent_data.can_create_tools:
            tools.append(self._create_custom_tool_creator_tool())

        # log nomi
        names = []
        for t in tools:
            if hasattr(t, "name"):
                names.append(t.name)
            elif hasattr(t, "TYPE"):
                names.append(t.TYPE)
            elif callable(t):
                names.append(t.__name__)
            else:
                names.append(str(type(t)))
        logger.debug(f"{self.agent_data.name} tools: {names}")
        return tools

    def _create_agent(self) -> OpenAIAgent:
        llm_config = self.agent_data.llm_config or {}
        model_name = llm_config.get("model") or self.seniority_model_map[self.agent_data.seniority.value]
        temperature = llm_config.get("temperature", 0.3)

        return OpenAIAgent(
            name=self.agent_data.name,
            instructions=self._create_system_prompt(),
            model=model_name,
            model_settings=ModelSettings(
                temperature=temperature,
                top_p=llm_config.get("top_p", 1.0),
                max_tokens=llm_config.get("max_tokens", 4096),
            ),
            tools=self.tools,
            handoffs=self.direct_sdk_handoffs,
            input_guardrails=[budget_monitoring_guardrail],
            #output_guardrails=[quality_assurance_guardrail],
            output_guardrails=[],
            output_type=AgentOutputSchema(TaskExecutionOutput, strict_json_schema=False),
        )

    def _create_system_prompt(self) -> str:
        sdk_txt = handoff_prompt.RECOMMENDED_PROMPT_PREFIX if self.direct_sdk_handoffs else ""
        prompt = f"""
{sdk_txt}
You are a {self.agent_data.seniority.value} AI specialist in {self.agent_data.role}.
Core Responsibilities: {self.agent_data.description or f'Expert in {self.agent_data.role}'}.

Your final output MUST be a JSON matching the '{TaskExecutionOutput.__name__}' schema:
- task_id, status, summary
- detailed_results_json: Valid JSON string or null (keep concise, max 5000 chars)
- resources_consumed_json: Valid JSON string or null (for token/cost tracking)

IMPORTANT JSON GUIDELINES:
- If providing detailed_results_json, ensure it's valid JSON
- Keep JSON concise and avoid excessive repetition
- Truncate large datasets to key insights only
- Use null for optional fields if not needed

TOOLS (use these exact names):
1. {self._task_creation_tool_name}
2. {self._request_handoff_tool_name}
3. {self._log_execution_step_tool_name}
4. {self._update_health_status_tool_name}
5. {self._report_task_progress_tool_name}
{"6. " + self._propose_custom_tool_tool_name if self.agent_data.can_create_tools else ""}

General:
- Use tools to create subtasks or delegate.
- Return a single valid JSON per schema above.
"""
        if "coordinator" in self.agent_data.role.lower() or "manager" in self.agent_data.role.lower():
            prompt += """
COORDINATOR INSTRUCTIONS:
- Orchestrate specialists with create_task_for_agent_tool.
- Escalate via request_handoff_to_role_via_task.
"""
        return prompt.strip()

    async def verify_capabilities(self) -> bool:
        logger.info(f"Verifying capabilities for {self.agent_data.name}")
        prompt = (
            f"You are '{self.agent_data.name}'. Self-check: list your tools, model, "
            f"role, limitations. Return JSON '{CapabilityVerificationOutput.__name__}'."
        )
        health = HealthStatus.UNKNOWN
        details: Dict[str, Any] = {"attempted": datetime.now().isoformat()}
        passed = False

        verifier = OpenAIAgent(
            name=f"{self.agent_data.name}_Verifier",
            instructions=self.agent.instructions,
            model=self.agent.model,
            model_settings=self.agent.model_settings,
            tools=self.agent.tools,
            output_type=AgentOutputSchema(CapabilityVerificationOutput, strict_json_schema=False)
        )
        try:
            res = await Runner.run(verifier, prompt, max_turns=2)
            out = res.final_output
            if isinstance(out, dict):
                v = CapabilityVerificationOutput.model_validate(out)
            elif isinstance(out, CapabilityVerificationOutput):
                v = out
            else:
                v = CapabilityVerificationOutput.model_validate_json(out)
            details["output"] = v.model_dump()
            if v.verification_status == "passed":
                health = HealthStatus.HEALTHY
                passed = True
            else:
                health = HealthStatus.DEGRADED
        except Exception as e:
            logger.error(f"verify_capabilities error: {e}", exc_info=True)
            health = HealthStatus.UNHEALTHY
            details["error"] = str(e)

        await update_agent_status(
            str(self.agent_data.id),
            None,
            AgentHealth(status=health, last_update=datetime.now(), details=details).model_dump(),
        )
        return passed

    # --- Tool creators e _log_execution_internal, execute_task, ecc. ---
    def _create_task_for_agent_tool(self):
        @function_tool(name_override=self._task_creation_tool_name)
        async def impl(
            task_name: str = Field(...),
            task_description: str = Field(...),
            target_agent_role: str = Field(...),
            priority: Literal["low","medium","high"] = Field("medium"),
        ) -> str:
            try:
                # PREVENZIONE LOOP: check delegation attempts
                cache_key = f"{target_agent_role.lower()}_{hash(task_description)}"
                current_attempts = self.delegation_attempts_cache.get(cache_key, 0)
                
                if current_attempts >= self.max_delegation_attempts:
                    logger.warning(f"Too many delegation attempts for {target_agent_role}, forcing self-execution")
                    return await self._force_self_execution(task_name, task_description, target_agent_role, priority)
                
                # Incrementa tentativi
                self.delegation_attempts_cache[cache_key] = current_attempts + 1
                
                agents_db = await db_list_agents(str(self.agent_data.workspace_id))
                
                # STEP 1: FUZZY MATCHING MIGLIORATO
                compatible_agents = self._find_compatible_agents(agents_db, target_agent_role)
                
                if compatible_agents:
                    target_agent = compatible_agents[0]  # Già ordinati per score + seniority
                    
                    # Reset cache on successful delegation
                    self.delegation_attempts_cache[cache_key] = 0
                    
                    # Crea il task con descrizione arricchita
                    enhanced_description = self._create_enhanced_task_description(
                        task_description, target_agent_role, target_agent, priority
                    )
                    
                    created = await db_create_task(
                        str(self.agent_data.workspace_id),
                        target_agent["id"],
                        task_name,
                        enhanced_description,
                        TaskStatus.PENDING.value
                    )
                    
                    if created:
                        out = TaskCreationOutput(
                            success=True,
                            task_id=created["id"],
                            task_name=task_name,
                            assigned_agent_name=target_agent["name"]
                        )
                        await self._log_execution_internal("subtask_delegated", {
                            **out.model_dump(),
                            "match_score": target_agent.get("match_score", 0),
                            "match_type": "exact" if target_agent_role.lower() == target_agent["role"].lower() else "fuzzy"
                        })
                        return json.dumps(out.model_dump())
                
                # STEP 2: SELF-EXECUTION CHECK
                if self._can_handle_task_myself(task_description, target_agent_role):
                    return await self._handle_self_execution(task_name, task_description, target_agent_role, priority)
                
                # STEP 3: HUMAN ESCALATION (Semplificata)
                escalation_task = await self._create_escalation_task(
                    task_name, task_description, target_agent_role, priority
                )
                
                if escalation_task:
                    out = TaskCreationOutput(
                        success=True,
                        task_id=escalation_task["id"],
                        task_name="Human Review Required",
                        assigned_agent_name="HUMAN_REVIEW",
                        error_message=f"No suitable agent for '{target_agent_role}' - human review requested"
                    )
                    await self._log_execution_internal("escalation_created", out.model_dump())
                    return json.dumps(out.model_dump())
                
                # STEP 4: FALLBACK FAILURE
                out = TaskCreationOutput(
                    success=False,
                    task_name=task_name,
                    error_message=f"Cannot find suitable agent for '{target_agent_role}' and unable to escalate"
                )
                await self._log_execution_internal("delegation_failed", out.model_dump())
                return json.dumps(out.model_dump())
                
            except Exception as e:
                logger.error(f"Error in task delegation: {e}", exc_info=True)
                out = TaskCreationOutput(
                    success=False,
                    task_name=task_name,
                    error_message=f"Delegation error: {str(e)}"
                )
                return json.dumps(out.model_dump())
        
        return impl

    def _find_compatible_agents(self, agents_db: List[Dict], target_role: str) -> List[Dict]:
        """Trova agenti compatibili usando fuzzy matching intelligente"""
        target_lower = target_role.lower()
        candidates = []
        
        # Matrice di compatibilità role-based (domain-agnostic)
        role_compatibility = {
            'analyst': ['analysis', 'research', 'investigation', 'data', 'brand', 'market', 'financial', 'business'],
            'researcher': ['research', 'investigation', 'data', 'analysis', 'collection', 'study'],
            'manager': ['management', 'coordination', 'planning', 'oversight', 'project', 'operations'],
            'coordinator': ['coordination', 'management', 'planning', 'organization', 'orchestration'],
            'specialist': ['expert', 'specialization', 'focused', 'technical', 'domain'],
            'lead': ['leadership', 'direction', 'guidance', 'team', 'head'],
            'advisor': ['advisory', 'consultation', 'guidance', 'recommendation', 'counsel'],
            'strategist': ['strategy', 'planning', 'vision', 'roadmap', 'direction'],
            'consultant': ['consulting', 'advisory', 'expert', 'guidance', 'solution']
        }
        
        for agent in agents_db:
            if (agent.get("status") == AgentStatus.ACTIVE.value and 
                agent.get("id") != str(self.agent_data.id)):
                
                agent_role = agent.get("role", "").lower()
                
                # 1. Exact match (highest priority)
                if target_lower == agent_role:
                    agent['match_score'] = 10
                    candidates.append(agent)
                    continue
                
                # 2. Substring match
                if target_lower in agent_role or agent_role in target_lower:
                    agent['match_score'] = 8
                    candidates.append(agent)
                    continue
                
                # 3. Keyword compatibility
                score = 0
                for keyword, related_terms in role_compatibility.items():
                    if keyword in target_lower:
                        for term in related_terms:
                            if term in agent_role:
                                score += 2
                                break
                    if keyword in agent_role:
                        for term in related_terms:
                            if term in target_lower:
                                score += 2
                                break
                
                # 4. Word overlap
                target_words = set(target_lower.split())
                agent_words = set(agent_role.split())
                overlap = len(target_words & agent_words)
                score += overlap * 3
                
                # 5. Bonus for generic roles that can handle many tasks
                if any(generic in agent_role for generic in ['manager', 'coordinator', 'lead', 'generalist']):
                    score += 1
                
                if score >= 4:  # Threshold per compatibilità
                    agent['match_score'] = score
                    candidates.append(agent)
        
        # Ordina per score e poi per seniority
        candidates.sort(key=lambda x: (
            x.get('match_score', 0), 
            {'expert': 3, 'senior': 2, 'junior': 1}.get(x.get('seniority', 'junior'), 1)
        ), reverse=True)
        
        top3 = [f"{a['name']}({a.get('match_score', 0)})" for a in candidates[:3]]
        logger.info(f"Found {len(candidates)} compatible agents for '{target_role}': {top3}")
        return candidates

    def _can_handle_task_myself(self, task_description: str, target_role: str) -> bool:
        """Valuta se l'agente può gestire il task espandendo il suo scope"""
        my_role = self.agent_data.role.lower()
        target_lower = target_role.lower()
        task_lower = task_description.lower()
        
        # 1. Coordinatori e manager possono gestire molti tipi di task
        if any(role in my_role for role in ['coordinator', 'manager', 'lead', 'project']):
            return True
        
        # 2. Analisti possono spesso gestire diversi tipi di analisi
        if 'analyst' in my_role and any(word in target_lower for word in ['analysis', 'research', 'investigation']):
            return True
        
        # 3. Specialists possono espandere il loro dominio
        if 'specialist' in my_role and any(word in task_lower for word in my_role.split()):
            return True
        
        # 4. Keyword overlap significativo
        my_keywords = set(my_role.split())
        target_keywords = set(target_lower.split())
        task_keywords = set(task_lower.split())
        
        # Almeno 1 keyword condivisa con il target role O 2+ con il task
        keyword_overlap_target = len(my_keywords & target_keywords)
        keyword_overlap_task = len(my_keywords & task_keywords)
        
        can_handle = keyword_overlap_target >= 1 or keyword_overlap_task >= 2
        
        logger.info(f"Self-execution check for '{target_role}': "
                   f"my_role='{my_role}', overlap_target={keyword_overlap_target}, "
                   f"overlap_task={keyword_overlap_task}, can_handle={can_handle}")
        
        return can_handle

    async def _handle_self_execution(
        self, 
        task_name: str, 
        task_description: str, 
        target_role: str, 
        priority: str
    ) -> str:
        """Gestisce l'esecuzione diretta del task da parte dell'agente stesso"""
        self_task_description = self._create_self_execution_description(
            task_description, target_role, priority
        )
        
        created = await db_create_task(
            str(self.agent_data.workspace_id),
            str(self.agent_data.id),
            f"[EXPANDED] {task_name}",
            self_task_description,
            TaskStatus.PENDING.value
        )
        
        if created:
            out = TaskCreationOutput(
                success=True,
                task_id=created["id"],
                task_name=f"[EXPANDED] {task_name}",
                assigned_agent_name=self.agent_data.name
            )
            await self._log_execution_internal("self_execution", {
                **out.model_dump(),
                "original_target_role": target_role,
                "expansion_reason": "No suitable specialist available"
            })
            return json.dumps(out.model_dump())
        else:
            raise Exception("Failed to create self-execution task")

    async def _force_self_execution(
        self, 
        task_name: str, 
        task_description: str, 
        target_role: str, 
        priority: str
    ) -> str:
        """Forza self-execution per prevenire loop di delegazione"""
        logger.warning(f"Forcing self-execution due to delegation loop prevention")
        
        forced_description = f"""
[LOOP PREVENTION FORCED EXECUTION]

{task_description}

---
EXECUTION CONTEXT:
• Priority: {priority.upper()}
• Originally Intended For: {target_role}
• Forced to: {self.agent_data.role}
• Reason: Too many delegation attempts - preventing infinite loop

APPROACH:
Execute this task to the best of my capabilities within {self.agent_data.role} expertise.
May not be optimal but ensures task completion and prevents system gridlock.
"""
        
        created = await db_create_task(
            str(self.agent_data.workspace_id),
            str(self.agent_data.id),
            f"[FORCED] {task_name}",
            forced_description,
            TaskStatus.PENDING.value
        )
        
        if created:
            out = TaskCreationOutput(
                success=True,
                task_id=created["id"],
                task_name=f"[FORCED] {task_name}",
                assigned_agent_name=self.agent_data.name
            )
            await self._log_execution_internal("forced_execution", {
                **out.model_dump(),
                "original_target_role": target_role,
                "reason": "loop_prevention"
            })
            return json.dumps(out.model_dump())
        else:
            raise Exception("Failed to create forced execution task")

    def _create_enhanced_task_description(
        self, 
        original_description: str, 
        target_role: str, 
        assigned_agent: Dict, 
        priority: str
    ) -> str:
        """Crea descrizione arricchita per task delegato"""
        match_score = assigned_agent.get('match_score', 0)
        if target_role.lower() == assigned_agent["role"].lower():
            match_type = "EXACT MATCH"
        elif match_score >= 8:
            match_type = "HIGH COMPATIBILITY"
        elif match_score >= 6:
            match_type = "GOOD COMPATIBILITY"
        else:
            match_type = "BEST AVAILABLE"
        
        return f"""
{original_description}

---
DELEGATION CONTEXT:
• Priority: {priority.upper()}
• Requested Role: {target_role}
• Assigned To: {assigned_agent['name']} ({assigned_agent['role']})
• Assignment Type: {match_type} (Score: {match_score}/10)
• Delegated By: {self.agent_data.name} ({self.agent_data.role})

EXECUTION GUIDANCE:
1. Execute this task leveraging your {assigned_agent['role']} expertise
2. If the task requires capabilities outside your domain, clearly document the limitation
3. Provide the best possible outcome within your expertise scope
4. If you need specialized expertise not available in current team, create a handoff task to Project Manager

Note: This delegation was made based on compatibility analysis. Focus on delivering value within your expertise area.
"""

    def _create_self_execution_description(
        self, 
        original_description: str, 
        intended_role: str, 
        priority: str
    ) -> str:
        """Crea descrizione per self-execution task"""
        return f"""
EXPANDED SCOPE EXECUTION

{original_description}

---
EXECUTION CONTEXT:
• Priority: {priority.upper()}
• Originally Intended For: {intended_role}
• Executing As: {self.agent_data.role}
• Reason: No specialized agent available, expanding scope to cover this task

APPROACH:
1. Execute this task leveraging my {self.agent_data.role} expertise
2. Apply best practices and knowledge from my domain to this adjacent area
3. Clearly distinguish between tasks within my core competency vs. expanded scope
4. Document any limitations or gaps encountered for future team planning
5. Provide recommendations for future similar tasks (in-house capability vs. external expertise)

QUALITY STANDARDS:
- Deliver the best possible outcome within my expanded capabilities
- Be transparent about confidence levels for different aspects of the work
- Suggest follow-up actions if specialized expertise becomes available

Note: This represents capability expansion rather than core expertise application.
"""

    async def _create_escalation_task(
        self, 
        original_task_name: str, 
        task_description: str, 
        required_role: str, 
        priority: str
    ) -> Optional[Dict]:
        """Crea task di escalation per human review (semplificato)"""
        
        # Trova un Project Manager o Coordinator per gestire l'escalation
        agents_db = await db_list_agents(str(self.agent_data.workspace_id))
        
        # Preferenza: Project Manager > Coordinator > Senior Agent
        escalation_targets = []
        
        # Prima cerca project managers
        project_managers = [
            agent for agent in agents_db
            if "project" in agent.get("role", "").lower() and "manager" in agent.get("role", "").lower()
            and agent.get("status") == AgentStatus.ACTIVE.value
            and agent.get("id") != str(self.agent_data.id)
        ]
        
        if project_managers:
            escalation_targets = project_managers
        else:
            # Poi coordinatori
            coordinators = [
                agent for agent in agents_db
                if "coordinator" in agent.get("role", "").lower()
                and agent.get("status") == AgentStatus.ACTIVE.value
                and agent.get("id") != str(self.agent_data.id)
            ]
            
            if coordinators:
                escalation_targets = coordinators
            else:
                # Infine qualsiasi senior/expert agent
                senior_agents = [
                    agent for agent in agents_db
                    if agent.get("seniority") in [AgentSeniority.SENIOR.value, AgentSeniority.EXPERT.value]
                    and agent.get("status") == AgentStatus.ACTIVE.value
                    and agent.get("id") != str(self.agent_data.id)
                ]
                escalation_targets = senior_agents
        
        if not escalation_targets:
            logger.warning("No suitable escalation target found")
            return None
        
        # Prendi il più senior
        seniority_score = {'expert': 3, 'senior': 2, 'junior': 1}
        escalation_target = max(escalation_targets, 
                               key=lambda x: seniority_score.get(x.get('seniority', 'junior'), 1))
        
        # Crea summary del tentativo di delegazione
        delegation_summary = self._create_delegation_attempt_summary(agents_db, required_role)
        
        escalation_description = f"""
ESCALATION REQUIRED: Missing Team Capability

ORIGINAL REQUEST:
• Task: {original_task_name}
• Description: {task_description}
• Required Role: {required_role}
• Priority: {priority.upper()}
• Requested By: {self.agent_data.name} ({self.agent_data.role})

SITUATION:
After thorough analysis, no current team member can adequately handle tasks requiring '{required_role}' expertise.

DELEGATION ATTEMPTS:
{delegation_summary}

ANALYSIS NEEDED:
1. **Capability Gap Assessment**: Is this a one-off need or recurring requirement?
2. **Team Expansion Decision**: Does this justify adding a new specialized agent?
3. **Alternative Solutions**: Could existing agents be upskilled or processes adjusted?
4. **Cost-Benefit Analysis**: New agent cost vs. external consultation vs. capability gap

CURRENT TEAM COMPOSITION:
{self._get_team_summary(agents_db)}

RECOMMENDATIONS:
Please evaluate and decide on the best approach:
- [APPROVE NEW AGENT] If recurring need and team capacity allows
- [EXPAND EXISTING ROLE] If current agent can be upskilled
- [EXTERNAL SOLUTION] If one-off or highly specialized need
- [PROCESS REDESIGN] If requirement can be eliminated/simplified

If approving new agent, please specify:
- Exact role definition and responsibilities
- Seniority level and capabilities required
- Integration plan with existing team
"""
        
        try:
            escalation_task = await db_create_task(
                str(self.agent_data.workspace_id),
                escalation_target["id"],
                f"[ESCALATION] Team Capability Review: {required_role}",
                escalation_description,
                TaskStatus.PENDING.value
            )
            
            await self._log_execution_internal("escalation_created", {
                "escalation_target": escalation_target["name"],
                "required_role": required_role,
                "escalation_type": "capability_gap"
            })
            
            return escalation_task
        except Exception as e:
            logger.error(f"Failed to create escalation task: {e}")
            return None

    def _create_delegation_attempt_summary(self, agents_db: List[Dict], required_role: str) -> str:
        """Crea summary dei tentativi di delegazione per il report di escalation"""
        compatible_agents = self._find_compatible_agents(agents_db, required_role)
        
        if not compatible_agents:
            return f"• No compatible agents found for '{required_role}'"
        
        summary_lines = []
        summary_lines.append(f"• Analyzed {len(agents_db)} active agents")
        summary_lines.append(f"• Found {len(compatible_agents)} potentially compatible agents:")
        
        for agent in compatible_agents[:3]:  # Top 3
            score = agent.get('match_score', 0)
            summary_lines.append(
                f"  - {agent['name']} ({agent['role']}) - Compatibility: {score}/10"
            )
        
        if len(compatible_agents) > 3:
            summary_lines.append(f"  - ... and {len(compatible_agents) - 3} others")
        
        # Aggiungi info su self-execution attempt
        if self._can_handle_task_myself("", required_role):
            summary_lines.append(f"• Self-execution evaluated: POSSIBLE (but suboptimal)")
        else:
            summary_lines.append(f"• Self-execution evaluated: NOT FEASIBLE")
        
        return "\n".join(summary_lines)

    def _get_team_summary(self, agents_db: List[Dict]) -> str:
        """Crea riassunto dettagliato del team per escalation"""
        active_agents = [a for a in agents_db if a.get("status") == AgentStatus.ACTIVE.value]
        
        if not active_agents:
            return "• No active agents found"
        
        # Raggruppa per seniority
        by_seniority = {
            AgentSeniority.EXPERT.value: [],
            AgentSeniority.SENIOR.value: [],
            AgentSeniority.JUNIOR.value: []
        }
        
        for agent in active_agents:
            seniority = agent.get("seniority", AgentSeniority.JUNIOR.value)
            by_seniority[seniority].append(agent)
        
        summary_lines = []
        total_count = len(active_agents)
        summary_lines.append(f"Total Active Agents: {total_count}")
        
        for seniority in [AgentSeniority.EXPERT.value, AgentSeniority.SENIOR.value, AgentSeniority.JUNIOR.value]:
            agents = by_seniority[seniority]
            if agents:
                summary_lines.append(f"\n{seniority.upper()} ({len(agents)}):")
                for agent in agents:
                    summary_lines.append(f"  • {agent.get('name', 'Unknown')} - {agent.get('role', 'Unknown')}")
        
        return "\n".join(summary_lines)

    # Reset del cache di delegazione periodicamente
    async def reset_delegation_cache(self):
        """Reset del cache di delegazione per prevenire accumulo infinito"""
        self.delegation_attempts_cache.clear()
        await self._log_execution_internal("delegation_cache_reset", {"reason": "periodic_maintenance"})   

    def _create_request_handoff_tool(self):
        @function_tool(name_override=self._request_handoff_tool_name)
        async def impl(
            target_role: str = Field(...),
            reason_for_handoff: str = Field(...),
            summary_of_work_done: str = Field(...),
            specific_request_for_target: str = Field(...),
            priority: Literal["low","medium","high"] = Field("medium"),
        ) -> str:
            try:
                agents_db = await db_list_agents(str(self.agent_data.workspace_id))
                senior = {AgentSeniority.EXPERT.value:3, AgentSeniority.SENIOR.value:2, AgentSeniority.JUNIOR.value:1}
                candidates = [
                    a for a in agents_db
                    if target_role.lower() in a.get("role","").lower()
                    and a.get("status") == AgentStatus.ACTIVE.value
                    and a.get("id") != str(self.agent_data.id)
                ]
                if candidates:
                    candidates.sort(key=lambda x: senior.get(x.get("seniority"),0), reverse=True)
                    tgt = candidates[0]
                else:
                    coords = [
                        a for a in agents_db
                        if any(k in a.get("role","").lower() for k in ["coordinator","manager"])
                        and a.get("status") == AgentStatus.ACTIVE.value
                        and a.get("id") != str(self.agent_data.id)
                    ]
                    tgt = coords[0] if coords else None
                if not tgt:
                    out = HandoffRequestOutput(success=False, message=f"No active agent for '{target_role}'")
                    return json.dumps(out.model_dump())
                name = f"Handoff from {self.agent_data.name}: {specific_request_for_target[:40]}..."
                desc = (
                    f"HANDOFF TASK (Priority {priority.upper()})\n"
                    f"From: {self.agent_data.name}\n"
                    f"To Role: {target_role}\n"
                    f"Assigned: {tgt['name']}\n"
                    f"Reason: {reason_for_handoff}\n"
                    f"Work Done: {summary_of_work_done}\n"
                    f"Request: {specific_request_for_target}"
                )
                created = await db_create_task(
                    str(self.agent_data.workspace_id),
                    tgt["id"],
                    name,
                    desc,
                    TaskStatus.PENDING.value
                )
                if not created:
                    out = HandoffRequestOutput(success=False, message="DB failed")
                else:
                    out = HandoffRequestOutput(success=True, message="Handoff created", handoff_task_id=created["id"], assigned_to_agent_name=tgt["name"])
                await self._log_execution_internal("handoff_created", out.model_dump())
                return json.dumps(out.model_dump())
            except Exception as e:
                out = HandoffRequestOutput(success=False, message=str(e))
                return json.dumps(out.model_dump())
        return impl

    async def _log_execution_internal(self, step: str, details: Union[str, Dict]) -> bool:
        try:
            if isinstance(details, str):
                try:
                    details = json.loads(details)
                except json.JSONDecodeError:
                    details = {"raw": details}
            log = {
                "agent_id": str(self.agent_data.id),
                "agent_name": self.agent_data.name,
                "step": step,
                "timestamp": datetime.now().isoformat(),
                "details": details,
                "workspace_id": str(self.agent_data.workspace_id),
                "seniority": self.agent_data.seniority.value
            }
            logger.info(f"AgentLog: {json.dumps(log)}")
            return True
        except Exception:
            return False

    def _create_log_execution_tool(self):
        @function_tool(name_override=self._log_execution_step_tool_name)
        async def impl(
            step_name: str = Field(...),
            details_json: str = Field(...)
        ):
            return await self._log_execution_internal(step_name, details_json)
        return impl

    def _create_update_health_status_tool(self):
        @function_tool(name_override=self._update_health_status_tool_name)
        async def impl(
            status: Literal["healthy","degraded","unhealthy"] = Field(...),
            details_message: Optional[str] = Field(None)
        ):
            try:
                await update_agent_status(
                    str(self.agent_data.id),
                    None,
                    {
                        "status": status,
                        "last_update": datetime.now().isoformat(),
                        "details": {"message": details_message}
                    }
                )
                return True
            except Exception as e:
                logger.error(f"update_health error: {e}", exc_info=True)
                return False
        return impl

    def _create_report_progress_tool(self):
        @function_tool(name_override=self._report_task_progress_tool_name)
        async def impl(
            task_id_being_processed: str = Field(...),
            progress_percentage: int = Field(..., ge=0, le=100),
            current_stage_summary: str = Field(...),
            next_action_planned: Optional[str] = Field(None),
            blockers_or_issues: Optional[str] = Field(None)
        ):
            details = {
                "task_id": task_id_being_processed,
                "progress": progress_percentage,
                "stage": current_stage_summary,
                "next": next_action_planned,
                "issues": blockers_or_issues
            }
            await self._log_execution_internal("task_progress", details)
            return True
        return impl

    def _create_custom_tool_creator_tool(self):
        @function_tool(name_override=self._propose_custom_tool_tool_name)
        async def impl(
            name: str = Field(...),
            description: str = Field(...),
            python_code: str = Field(...)
        ):
            await self._log_execution_internal("custom_tool_proposed", {
                "name": name,
                "description": description,
                "code_snippet": python_code[:200] + "..."
            })
            return json.dumps({"success": True, "message": f"Tool '{name}' proposed for review."})
        return impl

    async def test_conversation_optimization(self, sample_history: List[Dict]) -> Dict[str, Any]:
        orig = len(sample_history)
        opt = await self.conversation_optimizer.optimize_with_ai_summary(sample_history)
        return {"original": orig, "optimized": len(opt), "sample": opt[:3]}

    async def test_tool_based_handoff_logic(
        self,
        target_role: str, reason: str,
        summary: str, request: str,
        priority: Literal["low","medium","high"] = "medium"
    ) -> Dict[str, Any]:
        fn = self._create_request_handoff_tool()
        out = await fn(
            target_role=target_role,
            reason_for_handoff=reason,
            summary_of_work_done=summary,
            specific_request_for_target=request,
            priority=priority
        )
        try:
            return json.loads(out)
        except:
            return {"raw": out}
        
    

    async def execute_task(self, task: Task, context: Optional[T] = None) -> Dict[str, Any]:
        trace_id = gen_trace_id()
        workflow = f"Task-{task.name[:30]}-{self.agent_data.name}"
        with trace(workflow_name=workflow, trace_id=trace_id, group_id=str(task.id)):
            try:
                # Log dettagliato per debug
                logger.info(f"[DEBUG] Starting task execution for {self.agent_data.name}")
                logger.info(f"[DEBUG] Agent seniority: {self.agent_data.seniority}")
                logger.info(f"[DEBUG] Model: {getattr(self.agent, 'model', 'unknown')}")
                logger.info(f"[DEBUG] Output type: {getattr(self.agent, 'output_type', 'none')}")
            
                # Initialization
                await update_task_status(str(task.id), TaskStatus.IN_PROGRESS.value)
                await self._log_execution_internal("task_started", {
                    "task_id": str(task.id),
                    "task_name": task.name
                })

                # Execution
                prompt = (
                    f"Current Task: {task.name}\n"
                    f"{task.description}\n"
                    f"Use tools as instructed in system prompt."
                )
                inp = [{"role": "user", "content": prompt}]
                ctx = {} if self.context_type is dict else self.context_type()  # type: ignore
                if context and isinstance(ctx, dict):
                    ctx.update(context)
                    
                logger.info(f"[DEBUG] About to run agent with prompt length: {len(prompt)}")
                result = await Runner.run(self.agent, inp, max_turns=10, context=ctx)

                # Log dopo l'esecuzione
                logger.info(f"[DEBUG] Agent run completed")
                logger.info(f"[DEBUG] Final output type: {type(result.final_output)}")
                logger.info(f"[DEBUG] Final output: {str(result.final_output)[:200]}...")
            
                # Result processing
                fo = result.final_output
                if isinstance(fo, TaskExecutionOutput):
                    out_obj = fo
                    # Valida e tronca i JSON se necessario
                    if out_obj.detailed_results_json:
                        out_obj.detailed_results_json = self._validate_and_truncate_json(
                            out_obj.detailed_results_json
                        )
                    if out_obj.resources_consumed_json:
                        out_obj.resources_consumed_json = self._validate_and_truncate_json(
                            out_obj.resources_consumed_json
                        )

                elif isinstance(fo, dict):
                    try:
                        # Valida i campi JSON se presenti
                        if "detailed_results_json" in fo:
                            fo["detailed_results_json"] = self._validate_and_truncate_json(
                                fo.get("detailed_results_json")
                            )
                        if "resources_consumed_json" in fo:
                            fo["resources_consumed_json"] = self._validate_and_truncate_json(
                                fo.get("resources_consumed_json")
                            )
                        out_obj = TaskExecutionOutput.model_validate(fo)
                    except:
                        out_obj = TaskExecutionOutput(
                            task_id=str(task.id),
                            status="completed",
                            summary=str(fo)[:200],
                            detailed_results_json=self._validate_and_truncate_json(
                                json.dumps(fo) if isinstance(fo, dict) else str(fo)
                            )
                        )
                else:
                    out_obj = TaskExecutionOutput(
                        task_id=str(task.id),
                        status="failed",
                        summary=f"Unexpected type: {type(fo).__name__}",
                        detailed_results_json=json.dumps({"raw": str(fo)})
                    )

                res = out_obj.model_dump()
                res["trace_id"] = trace_id
                db_status = (
                    TaskStatus.FAILED.value
                    if out_obj.status == "failed"
                    else TaskStatus.COMPLETED.value
                )
                await update_task_status(str(task.id), db_status, result=res)
                await self._log_execution_internal("task_completed", {
                    "task_id": str(task.id),
                    "status": out_obj.status
                })
                return res

            except MaxTurnsExceeded as e:
                err = {
                    "error": str(e),
                    "status": "failed",
                    "reason": "max_turns",
                    "trace_id": trace_id,
                    "last_output": getattr(e, "last_output", None)
                }
                await update_task_status(str(task.id), TaskStatus.FAILED.value, result=err)
                await self._log_execution_internal("task_failed", err)
                return err

            except (AgentsException, UserError) as e:
                err = {
                    "error": str(e),
                    "status": "failed",
                    "reason": type(e).__name__,
                    "trace_id": trace_id
                }
                await update_task_status(str(task.id), TaskStatus.FAILED.value, result=err)
                await self._log_execution_internal("task_failed", err)
                return err

            except Exception as e:
                err = {
                    "error": str(e),
                    "status": "failed",
                    "reason": "execution_error",
                    "trace_id": trace_id
                }
                await update_task_status(str(task.id), TaskStatus.FAILED.value, result=err)
                await self._log_execution_internal("task_failed", err)
                return err
