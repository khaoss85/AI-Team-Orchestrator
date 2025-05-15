import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set

from agents import Agent as OpenAIAgent, Runner
from pydantic import BaseModel

from models import Task, TaskStatus
from database import create_task, list_agents, list_tasks, get_workspace

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Structured outputs --------------------------------------------------------
# ---------------------------------------------------------------------------
class TaskAnalysisOutput(BaseModel):
    """Structured output for task completion analysis"""

    requires_follow_up: bool
    confidence_score: float  # 0–1
    suggested_handoffs: List[Dict[str, str]]
    project_status: str
    reasoning: str
    next_phase: Optional[str] = None


# ---------------------------------------------------------------------------
# Main executor -------------------------------------------------------------
# ---------------------------------------------------------------------------
class EnhancedTaskExecutor:
    """
    Conservative task executor that analyses completed tasks and, only when
    strictly necessary and with >80 % confidence, creates a *single* essential
    hand‑off to an existing agent. Designed to limit auto‑generation loops.
    """

    def __init__(self):
        self.analysis_agent = self._create_analysis_agent()
        # Idempotency & spam‑prevention helpers
        self.analyzed_tasks: Set[str] = set()
        self.handoff_cache: Dict[str, datetime] = {}

    # ---------------------------------------------------------------------
    # Agent factory -------------------------------------------------------
    # ---------------------------------------------------------------------
    def _create_analysis_agent(self) -> OpenAIAgent:
        """Return a *conservative* GPT‑4 agent for task‑completion review."""

        return OpenAIAgent(
            name="ConservativeTaskAnalyst",
            instructions="""
You are a **highly conservative** completion analyst. Default to **NO
FOLLOW‑UP** unless it is crystal‑clear that more work is *critical* to project
success.

• VALUE *completion* over continuation.
• Require >80 % confidence to suggest follow‑up.
• Prefer **handoffs** to *existing* agents; **never** propose new tasks.
• Recognise sufficiency; avoid perfectionism.
• Follow‑up only for blockers, explicit partials, or genuine errors.
""",
            model="gpt-4.1",
            output_type=TaskAnalysisOutput,
        )

    # ---------------------------------------------------------------------
    # Entry point ----------------------------------------------------------
    # ---------------------------------------------------------------------
    async def handle_task_completion(
        self,
        completed_task: Task,
        task_result: Dict[str, Any],
        workspace_id: str,
    ) -> None:
        """Analyse a completed task and, if essential, create a hand‑off."""

        # 0. Respect manual pause flag -------------------------------------------------
        from executor import task_executor  # local import to avoid cycles
        if workspace_id in task_executor.workspace_auto_generation_paused:
            logger.info("Auto‑generation paused for workspace %s", workspace_id)
            return

        task_id = str(completed_task.id)

        # 1. Skip if already analysed -----------------------------------------------
        if task_id in self.analyzed_tasks:
            logger.info("Task %s already analysed — skipping", task_id)
            return
        self.analyzed_tasks.add(task_id)

        # 2. Conservative pre‑filter -------------------------------------------------
        if not self._should_analyze_task_conservative(completed_task, task_result):
            logger.info("Task %s filtered out (pre‑filter)", task_id)
            return

        # 3. Gather context ----------------------------------------------------------
        workspace_ctx = await self._gather_workspace_context(workspace_id)

        # 4. Prevent duplicate hand‑offs --------------------------------------------
        if self._is_handoff_duplicate(completed_task, workspace_ctx):
            logger.warning("Duplicate hand‑off prevented for %s", task_id)
            return

        # 5. AI analysis -------------------------------------------------------------
        analysis = await self._analyze_task_with_ai_conservative(
            completed_task, task_result, workspace_ctx
        )

        # 6. Act on result (threshold > 0.80) ----------------------------------------
        if (
            analysis.requires_follow_up
            and analysis.confidence_score > 0.8
            and analysis.suggested_handoffs
        ):
            logger.info(
                "Essential follow‑up required for %s (%.2f)",
                task_id,
                analysis.confidence_score,
            )
            await self._execute_conservative_handoffs(
                analysis, completed_task, workspace_id
            )
        else:
            logger.info(
                "Task %s marked complete (confidence %.2f)",
                task_id,
                analysis.confidence_score,
            )
            await self._log_completion_decision(completed_task, analysis, "no_followup")

    # ---------------------------------------------------------------------
    # Conservative filters -------------------------------------------------
    # ---------------------------------------------------------------------
    def _should_analyze_task_conservative(self, task: Task, result: Dict[str, Any]) -> bool:
        """Stringent gatekeeper to avoid unnecessary AI calls."""

        if result.get("status") != "completed":
            return False

        name_lc = task.name.lower()
        handoff_words = [
            "handoff",
            "follow‑up",
            "escalation",
            "coordination",
            "review",
            "feedback",
        ]
        if any(w in name_lc for w in handoff_words):
            return False

        output = str(result.get("output", ""))
        if len(output) > 2_000:
            return False  # likely already thorough

        complete_markers = [
            "task complete",
            "completed successfully",
            "objective achieved",
            "deliverable ready",
            "no further action",
        ]
        output_lc = output.lower()
        if any(m in output_lc for m in complete_markers):
            return False

        # Ignore tasks that themselves propose next steps
        if result.get("next_steps"):
            return False

        # Focus only on tasks that *could* benefit from follow‑up
        key_words = [
            "research",
            "analysis",
            "planning",
            "design",
            "development",
            "implementation",
        ]
        return any(w in name_lc for w in key_words)

    # ---------------------------------------------------------------------
    # Duplicate‑handoff protection ----------------------------------------
    # ---------------------------------------------------------------------
    def _is_handoff_duplicate(self, task: Task, ctx: Dict[str, Any]) -> bool:
        cache_key = f"{task.workspace_id}_{task.agent_id}"
        recent = self.handoff_cache.get(cache_key)
        if recent and datetime.now() - recent < timedelta(minutes=30):
            return True

        for recent_task in ctx.get("recent_completions", []):
            if recent_task["name"].lower().startswith("handoff") and task.name.lower() in recent_task["name"].lower():
                return True
        return False

    # ---------------------------------------------------------------------
    # Context helpers ------------------------------------------------------
    # ---------------------------------------------------------------------
    async def _gather_workspace_context(self, workspace_id: str) -> Dict[str, Any]:
        workspace = await get_workspace(workspace_id)
        agents = await list_agents(workspace_id)
        tasks = await list_tasks(workspace_id)

        completed = [t for t in tasks if t.get("status") == "completed"]
        return {
            "workspace_goal": workspace.get("goal", ""),
            "total_tasks": len(tasks),
            "completed_tasks": len(completed),
            "pending_tasks": len([t for t in tasks if t.get("status") == "pending"]),
            "available_agents": [
                {
                    "id": a["id"],
                    "name": a["name"],
                    "role": a["role"],
                    "seniority": a["seniority"],
                }
                for a in agents
                if a.get("status") == "active"
            ],
            "recent_completions": [
                {"name": t["name"], "result": t.get("result", {})} for t in completed[-5:]
            ],
        }

    # ---------------------------------------------------------------------
    # AI call --------------------------------------------------------------
    # ---------------------------------------------------------------------
    async def _analyze_task_with_ai_conservative(
        self,
        task: Task,
        result: Dict[str, Any],
        ctx: Dict[str, Any],
    ) -> TaskAnalysisOutput:
        output_excerpt = str(result.get("output", ""))[:1_500]
        prompt = f"""
Analyse the following COMPLETED task. **Default to NO FOLLOW‑UP.** ‑ Suggest a hand‑off only if it is *critical* to project progress and you are >80 % confident.

TASK ⇒ {task.name}\n{task.description}\n
OUTPUT ⇒\n{output_excerpt}...\n
GOAL: {ctx.get('workspace_goal', 'N/A')}\nPROGRESS: {ctx.get('completed_tasks')}/{ctx.get('total_tasks')} completed\n
Remember: avoid perfectionism; completion is often good enough.
"""
        ai_result = await Runner.run(self.analysis_agent, prompt)
        return ai_result.final_output  # type: ignore

    # ---------------------------------------------------------------------
    # Handoff creation -----------------------------------------------------
    # ---------------------------------------------------------------------
    async def _execute_conservative_handoffs(
        self,
        analysis: TaskAnalysisOutput,
        task: Task,
        workspace_id: str,
    ) -> None:
        handoff = analysis.suggested_handoffs[0]  # Only first, essential
        role = handoff.get("target_agent_role", "")
        htype = handoff.get("handoff_type", "delegation")

        if htype not in {"escalation", "critical_delegation"}:
            logger.info("Skipping non‑essential hand‑off type %s", htype)
            return

        agents = await list_agents(workspace_id)
        target = self._find_agent_by_role_conservative(agents, role)
        if not target:
            logger.warning("No suitable agent found for role '%s'", role)
            return

        # Cache to avoid duplicates
        cache_key = f"{workspace_id}_{task.agent_id}"
        self.handoff_cache[cache_key] = datetime.now()

        description = self._create_conservative_handoff_description(task, handoff, analysis)
        new_task = await create_task(
            workspace_id=workspace_id,
            agent_id=target["id"],
            name=f"Essential Follow‑up: {handoff.get('expected_outcome', 'Continue Work')}",
            description=description,
            status=TaskStatus.PENDING.value,
        )
        if new_task:
            logger.info("Created hand‑off %s for agent %s", new_task["id"], target["name"])
            await self._log_completion_decision(task, analysis, "essential_handoff")

    # ---------------------------------------------------------------------
    # Agent matching -------------------------------------------------------
    # ---------------------------------------------------------------------
    def _find_agent_by_role_conservative(self, agents: List[Dict[str, Any]], role: str) -> Optional[Dict[str, Any]]:
        role_lc = role.lower()
        best: Optional[Dict[str, Any]] = None
        best_score = 0
        for a in agents:
            if a.get("status") != "active":
                continue
            a_role = a.get("role", "").lower()
            score = 0
            if a_role == role_lc:
                score = 10
            elif role_lc in a_role or a_role in role_lc:
                score = 8
            else:
                overlap = len(set(role_lc.split()) & set(a_role.split()))
                if overlap:
                    score = overlap * 2
                    if a.get("seniority") == "expert":
                        score += 1
            if score > best_score:
                best_score, best = score, a
        return best if best_score >= 8 else None

    # ---------------------------------------------------------------------
    # Helpers --------------------------------------------------------------
    # ---------------------------------------------------------------------
    def _create_conservative_handoff_description(
        self,
        task: Task,
        handoff: Dict[str, str],
        analysis: TaskAnalysisOutput,
    ) -> str:
        return f"""
ESSENTIAL FOLLOW‑UP (created by conservative analyser)

ORIGINAL TASK: {task.name}
CONFIDENCE: {analysis.confidence_score:.0%}

WHAT'S DONE ⇒\n{str(task.result.get('output', ''))[:300]}...

ESSENTIAL NEXT STEP ⇒ {handoff.get('expected_outcome', '')}
CONTEXT ⇒ {handoff.get('context_summary', '')}

INSTRUCTIONS:
1. Focus *only* on the essential outcome above.
2. Do **not** expand scope or create further hand‑offs unless strictly required.
3. Mark this task **COMPLETED** once the essential outcome is achieved.
"""

    async def _log_completion_decision(self, task: Task, analysis: TaskAnalysisOutput, decision: str) -> None:
        data = {
            "task_id": str(task.id),
            "task_name": task.name,
            "decision": decision,
            "confidence": analysis.confidence_score,
            "requires_followup": analysis.requires_follow_up,
            "reasoning": analysis.reasoning[:200],
            "timestamp": datetime.now().isoformat(),
        }
        logger.info("COMPLETION_DECISION %s", json.dumps(data))

    # ---------------------------------------------------------------------
    # Cache housekeeping ---------------------------------------------------
    # ---------------------------------------------------------------------
    def cleanup_handoff_cache(self) -> None:
        cutoff = datetime.now() - timedelta(hours=1)
        self.handoff_cache = {k: v for k, v in self.handoff_cache.items() if v > cutoff}
        if len(self.analyzed_tasks) > 1_000:
            # Remove approx. oldest half
            self.analyzed_tasks = set(list(self.analyzed_tasks)[-500:])
