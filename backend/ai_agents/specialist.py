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


# --- SpecialistAgent ---
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
            # wrappo il Pydantic model per disabilitare lo strict JSON dello SDK
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
- detailed_results_json: JSON string or null
- resources_consumed_json: JSON string or null

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
                agents_db = await db_list_agents(str(self.agent_data.workspace_id))
                candidates = [
                    a for a in agents_db
                    if target_agent_role.lower() in a.get("role","").lower()
                    and a.get("status") == AgentStatus.ACTIVE.value
                    and a.get("id") != str(self.agent_data.id)
                ]
                if candidates:
                    # pick most senior
                    senior = {AgentSeniority.EXPERT.value:3, AgentSeniority.SENIOR.value:2, AgentSeniority.JUNIOR.value:1}
                    candidates.sort(key=lambda x: senior.get(x.get("seniority"),0), reverse=True)
                    tgt = candidates[0]
                else:
                    # fallback to any coordinator
                    coords = [
                        a for a in agents_db
                        if any(k in a.get("role","").lower() for k in ["coordinator","manager"])
                        and a.get("status") == AgentStatus.ACTIVE.value
                        and a.get("id") != str(self.agent_data.id)
                    ]
                    tgt = coords[0] if coords else None
                if not tgt:
                    out = TaskCreationOutput(
                        success=False,
                        task_name=task_name,
                        error_message=f"No active agent for '{target_agent_role}'"
                    )
                    return json.dumps(out.model_dump())
                desc = (
                    f"{task_description}\n---\n"
                    f"Priority: {priority.upper()}\n"
                    f"Assigned by: {self.agent_data.name}"
                )
                created = await db_create_task(
                    str(self.agent_data.workspace_id),
                    tgt["id"],
                    task_name,
                    desc,
                    TaskStatus.PENDING.value
                )
                if not created:
                    out = TaskCreationOutput(success=False, task_name=task_name, error_message="DB failed")
                else:
                    out = TaskCreationOutput(success=True, task_id=created["id"], task_name=task_name, assigned_agent_name=tgt["name"])
                await self._log_execution_internal("subtask_created", out.model_dump())
                return json.dumps(out.model_dump())
            except Exception as e:
                out = TaskCreationOutput(success=False, task_name=task_name, error_message=str(e))
                return json.dumps(out.model_dump())
        return impl

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
                result = await Runner.run(self.agent, inp, max_turns=10, context=ctx)

                # Result processing
                fo = result.final_output
                if isinstance(fo, TaskExecutionOutput):
                    out_obj = fo
                elif isinstance(fo, dict):
                    try:
                        out_obj = TaskExecutionOutput.model_validate(fo)
                    except:
                        out_obj = TaskExecutionOutput(
                            task_id=str(task.id),
                            status="completed",
                            summary=str(fo)[:200],
                            detailed_results_json=json.dumps(fo)
                        )
                elif isinstance(fo, str):
                    out_obj = TaskExecutionOutput(
                        task_id=str(task.id),
                        status="completed",
                        summary=fo[:200],
                        detailed_results_json=json.dumps({"raw": fo})
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
