# backend/task_analyzer.py
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
# Structured outputs (MANTIENE STRUTTURA ORIGINALE)
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
# Main executor (VERSIONE ANTI-LOOP) 
# ---------------------------------------------------------------------------
class EnhancedTaskExecutor:
    """
    Enhanced task executor with ANTI-LOOP protection.
    Maintains original interface but prevents auto-generation by default.
    """

    def __init__(self):
        # ANTI-LOOP CONFIGURATION
        self.auto_generation_enabled = False  # DISABILITATO di default
        self.analysis_enabled = False         # DISABILITATA analisi LLM
        self.handoff_creation_enabled = False # DISABILITATI handoff automatici
        
        # Mantiene cache originali per compatibilità
        self.analyzed_tasks: Set[str] = set()
        self.handoff_cache: Dict[str, datetime] = {}
        
        # Configurazioni conservative
        self.confidence_threshold = 0.95  # Soglia molto alta
        self.max_auto_tasks_per_workspace = 1  # Massimo 1 task automatico
        self.cooldown_minutes = 60  # 1 ora di cooldown tra auto-generation
        
        # Monitoring
        self.initialization_time = datetime.now()
        self.last_cleanup = datetime.now()
        
        # NO agent creation per evitare costi LLM
        self.analysis_agent = None
        
        logger.info("EnhancedTaskExecutor initialized with ANTI-LOOP protection")

    # ---------------------------------------------------------------------
    # Entry point (VERSIONE SICURA)
    # ---------------------------------------------------------------------
    async def handle_task_completion(
        self,
        completed_task: Task,
        task_result: Dict[str, Any],
        workspace_id: str,
    ) -> None:
        """
        Handle task completion with STRICT anti-loop protection.
        Auto-generation is disabled by default for safety.
        """
        
        task_id = str(completed_task.id)
        
        # LOG sempre per monitoring
        await self._log_completion_analysis(completed_task, task_result, "auto_generation_disabled")
        
        # Early exit se auto-generation disabilitato
        if not self.auto_generation_enabled:
            logger.info(f"Auto-generation disabled - task {task_id} marked complete without analysis")
            return

        # Verifica manual pause flag da executor 
        try:
            from executor import task_executor
            if workspace_id in task_executor.workspace_auto_generation_paused:
                logger.info(f"Auto-generation paused for workspace {workspace_id} - skipping task {task_id}")
                return
        except Exception as e:
            logger.warning(f"Could not check executor pause status: {e}")
            # Assume paused per sicurezza
            return

        # Anti-loop: cooldown check
        if not self._check_cooldown(workspace_id):
            logger.info(f"Cooldown active for workspace {workspace_id} - skipping auto-analysis")
            return

        # Skip se già analizzato
        if task_id in self.analyzed_tasks:
            logger.info(f"Task {task_id} already analyzed - skipping")
            return
        
        # Aggiungi a analyzed per prevenire duplicati
        self.analyzed_tasks.add(task_id)

        try:
            # Pre-filter conservativo
            if not self._should_analyze_task_ultra_conservative(completed_task, task_result):
                await self._log_completion_analysis(completed_task, task_result, "filtered_out")
                return

            # Gather minimal context (senza LLM calls)
            workspace_ctx = await self._gather_workspace_context_safe(workspace_id)

            # Verifica limiti workspace
            if not self._check_workspace_limits(workspace_ctx):
                logger.info(f"Workspace {workspace_id} reached auto-generation limits")
                return

            # Duplicate handoff prevention
            if self._is_handoff_duplicate_strict(completed_task, workspace_ctx):
                logger.warning(f"Duplicate handoff prevented for task {task_id}")
                return

            # Qui normalmente ci sarebbe analisi LLM, ma è disabilitata
            # Invece usiamo regole deterministiche conservative
            analysis = self._analyze_task_deterministic(completed_task, task_result, workspace_ctx)

            # Action only se confidence altissima E handoff creation abilitata
            if (self.handoff_creation_enabled and 
                analysis.requires_follow_up and 
                analysis.confidence_score > self.confidence_threshold and 
                analysis.suggested_handoffs):
                
                logger.info(f"High-confidence follow-up for {task_id} (confidence: {analysis.confidence_score:.3f})")
                await self._execute_safe_handoffs(analysis, completed_task, workspace_id)
            else:
                logger.info(f"Task {task_id} completed without follow-up (confidence: {analysis.confidence_score:.3f})")
                await self._log_completion_analysis(completed_task, task_result, "no_followup_needed")

        except Exception as e:
            logger.error(f"Error in handle_task_completion for {task_id}: {e}", exc_info=True)
            await self._log_completion_analysis(completed_task, task_result, "analysis_error", str(e))

    # ---------------------------------------------------------------------
    # Ultra-conservative filters
    # ---------------------------------------------------------------------
    def _should_analyze_task_ultra_conservative(self, task: Task, result: Dict[str, Any]) -> bool:
        """Ultra-strict filter - most tasks will be skipped"""
        
        # Solo task completed
        if result.get("status") != "completed":
            return False

        # Skip tutti i task che contengono parole di completion
        task_name_lower = task.name.lower()
        completion_indicators = [
            "handoff", "follow-up", "escalation", "coordination", "review", 
            "feedback", "completed", "done", "finished", "delivered"
        ]
        
        if any(indicator in task_name_lower for indicator in completion_indicators):
            return False

        # Skip se output troppo lungo (probabilmente già completo)
        output = str(result.get("output", ""))
        if len(output) > 1500:  # Ridotto da 2000
            return False

        # Skip se contiene markers di completamento
        output_lower = output.lower()
        completion_markers = [
            "task complete", "completed successfully", "objective achieved",
            "deliverable ready", "no further action", "project finished",
            "all requirements met", "final result", "conclusion"
        ]
        
        if any(marker in output_lower for marker in completion_markers):
            return False

        # Skip se ha next_steps (già prevede follow-up)
        if result.get("next_steps"):
            return False

        # ULTRA CONSERVATIVE: Analizza solo task research/planning molto specifici
        research_keywords = ["initial research", "preliminary analysis", "feasibility study"]
        if not any(keyword in task_name_lower for keyword in research_keywords):
            return False

        return True

    def _check_cooldown(self, workspace_id: str) -> bool:
        """Verifica cooldown per workspace"""
        cache_key = f"cooldown_{workspace_id}"
        last_generation = self.handoff_cache.get(cache_key)
        
        if last_generation:
            time_diff = datetime.now() - last_generation
            if time_diff < timedelta(minutes=self.cooldown_minutes):
                return False
        
        return True

    def _check_workspace_limits(self, ctx: Dict[str, Any]) -> bool:
        """Verifica limiti workspace per auto-generation"""
        
        # Limita auto-generation se troppi task pending
        pending_tasks = ctx.get("pending_tasks", 0)
        if pending_tasks > 5:  # Max 5 pending
            return False
        
        # Limita se ratio completion troppo basso
        total_tasks = ctx.get("total_tasks", 1)
        completed_tasks = ctx.get("completed_tasks", 0)
        completion_ratio = completed_tasks / total_tasks
        
        if completion_ratio < 0.7:  # 70% completion richiesto
            return False
        
        return True

    def _is_handoff_duplicate_strict(self, task: Task, ctx: Dict[str, Any]) -> bool:
        """Strict duplicate detection"""
        
        # Check cache temporale
        cache_key = f"{task.workspace_id}_{task.agent_id}"
        recent = self.handoff_cache.get(cache_key)
        if recent and datetime.now() - recent < timedelta(minutes=30):
            return True

        # Check task names simili negli ultimi completamenti
        recent_tasks = ctx.get("recent_completions", [])
        task_name_lower = task.name.lower()
        
        for recent_task in recent_tasks[-5:]:  # Ultimi 5
            recent_name = recent_task.get("name", "").lower()
            
            # Se handoff task contiene nome del task corrente
            if ("handoff" in recent_name and 
                any(word in recent_name for word in task_name_lower.split() if len(word) > 3)):
                return True
                
            # Se task molto simili
            similarity = self._calculate_name_similarity(task_name_lower, recent_name)
            if similarity > 0.8:
                return True

        return False

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calcola similarità tra nomi task"""
        if not name1 or not name2:
            return 0.0
        
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0

    # ---------------------------------------------------------------------
    # Context gathering (SAFE version senza LLM calls)
    # ---------------------------------------------------------------------
    async def _gather_workspace_context_safe(self, workspace_id: str) -> Dict[str, Any]:
        """Gather workspace context senza costose operazioni"""
        try:
            workspace = await get_workspace(workspace_id)
            agents = await list_agents(workspace_id)
            tasks = await list_tasks(workspace_id)

            completed = [t for t in tasks if t.get("status") == "completed"]
            pending = [t for t in tasks if t.get("status") == "pending"]
            
            return {
                "workspace_goal": workspace.get("goal", "") if workspace else "",
                "total_tasks": len(tasks),
                "completed_tasks": len(completed),
                "pending_tasks": len(pending),
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
                    {
                        "name": t["name"], 
                        "id": t["id"],
                        "result": t.get("result", {})
                    } 
                    for t in completed[-10:]  # Ultimi 10
                ],
            }
        except Exception as e:
            logger.error(f"Error gathering workspace context: {e}")
            return self._get_empty_context()

    def _get_empty_context(self) -> Dict[str, Any]:
        """Context vuoto fallback"""
        return {
            "workspace_goal": "",
            "total_tasks": 0,
            "completed_tasks": 0,
            "pending_tasks": 0,
            "available_agents": [],
            "recent_completions": [],
        }

    # ---------------------------------------------------------------------
    # Deterministic analysis (NO LLM)
    # ---------------------------------------------------------------------
    def _analyze_task_deterministic(
        self,
        task: Task,
        result: Dict[str, Any],
        ctx: Dict[str, Any],
    ) -> TaskAnalysisOutput:
        """
        Deterministic analysis senza LLM calls.
        Usa regole hard-coded ultra-conservative.
        """
        
        # Default: no follow-up
        analysis = TaskAnalysisOutput(
            requires_follow_up=False,
            confidence_score=0.0,
            suggested_handoffs=[],
            project_status="completed",
            reasoning="Deterministic analysis - no follow-up needed",
            next_phase=None
        )

        try:
            # Analisi deterministiche ultra-conservative
            output = str(result.get("output", ""))
            output_lower = output.lower()
            
            # Rule 1: Trova explicit recommendations per follow-up
            follow_up_indicators = [
                "requires further", "needs additional", "recommend next",
                "should be followed", "next step should", "further investigation"
            ]
            
            has_follow_up_indicator = any(indicator in output_lower for indicator in follow_up_indicators)
            
            # Rule 2: Verifica se menziona altri agenti/ruoli
            mentioned_roles = self._extract_mentioned_roles(output, ctx["available_agents"])
            
            # Rule 3: Output length analysis
            is_substantial_output = len(output) > 200 and len(output) < 1000
            
            # ULTRA CONSERVATIVE DECISION LOGIC
            if (has_follow_up_indicator and 
                mentioned_roles and 
                is_substantial_output and
                ctx["pending_tasks"] < 3):  # Max 3 pending
                
                # Confidence dipende da quanti indicatori matchano
                confidence = 0.0
                if has_follow_up_indicator: confidence += 0.3
                if mentioned_roles: confidence += 0.3  
                if is_substantial_output: confidence += 0.2
                if ctx["pending_tasks"] == 0: confidence += 0.2  # Bonus se nessun pending
                
                # Solo se confidence molto alta
                if confidence >= 0.8:
                    analysis.requires_follow_up = True
                    analysis.confidence_score = confidence
                    analysis.reasoning = f"Deterministic rules matched (confidence: {confidence:.2f})"
                    
                    # Crea suggested handoff per primo ruolo menzionato  
                    if mentioned_roles:
                        analysis.suggested_handoffs = [{
                            "target_agent_role": mentioned_roles[0],
                            "expected_outcome": f"Continue work from {task.name}",
                            "context_summary": output[:200] + "...",
                            "handoff_type": "continuation"
                        }]
            
            analysis.reasoning += f" | Indicators: {len(follow_up_indicators)}, Roles: {len(mentioned_roles)}, Output: {len(output)}chars"
            
        except Exception as e:
            logger.error(f"Error in deterministic analysis: {e}")
            analysis.reasoning = f"Analysis error: {str(e)}"
        
        return analysis

    def _extract_mentioned_roles(self, text: str, available_agents: List[Dict]) -> List[str]:
        """Estrae ruoli menzionati nel testo"""
        mentioned = []
        text_lower = text.lower()
        
        # Estrai ruoli da agenti disponibili
        for agent in available_agents:
            role = agent.get("role", "").lower()
            role_keywords = role.split()
            
            # Verifica se ruolo è menzionato
            if role in text_lower:
                mentioned.append(agent["role"])
            else:
                # Check keyword parziali
                for keyword in role_keywords:
                    if len(keyword) > 3 and keyword in text_lower:
                        mentioned.append(agent["role"])
                        break
        
        # Rimuovi duplicati preservando ordine
        return list(dict.fromkeys(mentioned))

    # ---------------------------------------------------------------------
    # Safe handoff execution
    # ---------------------------------------------------------------------
    async def _execute_safe_handoffs(
        self,
        analysis: TaskAnalysisOutput,
        task: Task,
        workspace_id: str,
    ) -> None:
        """Execute handoffs con massima sicurezza"""
        
        if not analysis.suggested_handoffs:
            return
        
        # Solo primo handoff per sicurezza
        handoff = analysis.suggested_handoffs[0]
        target_role = handoff.get("target_agent_role", "")
        
        if not target_role:
            logger.warning("No target role in handoff suggestion")
            return
        
        try:
            # Trova agente target
            agents = await list_agents(workspace_id)
            target_agent = self._find_agent_by_role_exact(agents, target_role)
            
            if not target_agent:
                logger.warning(f"No exact match found for role '{target_role}'")
                return
            
            # Set cooldown PRIMA della creazione task
            cache_key = f"cooldown_{workspace_id}"
            self.handoff_cache[cache_key] = datetime.now()
            
            # Crea handoff task con descrizione limitata
            description = self._create_minimal_handoff_description(task, handoff, analysis)
            
            new_task = await create_task(
                workspace_id=workspace_id,
                agent_id=target_agent["id"],
                name=f"Follow-up: {handoff.get('expected_outcome', 'Continue work')[:40]}...",
                description=description,
                status=TaskStatus.PENDING.value,
            )
            
            if new_task:
                logger.info(f"Created safe handoff {new_task['id']} to {target_agent['name']}")
                await self._log_completion_analysis(task, analysis.__dict__, "handoff_created", str(new_task["id"]))
            
        except Exception as e:
            logger.error(f"Error executing safe handoff: {e}", exc_info=True)

    def _find_agent_by_role_exact(self, agents: List[Dict[str, Any]], role: str) -> Optional[Dict[str, Any]]:
        """Trova agente con match esatto del ruolo"""
        role_lower = role.lower()
        
        # Prima exact match
        for agent in agents:
            if (agent.get("status") == "active" and 
                agent.get("role", "").lower() == role_lower):
                return agent
        
        # Poi substring match
        for agent in agents:
            if (agent.get("status") == "active" and 
                role_lower in agent.get("role", "").lower()):
                return agent
        
        return None

    def _create_minimal_handoff_description(
        self,
        task: Task,
        handoff: Dict[str, str],
        analysis: TaskAnalysisOutput,
    ) -> str:
        """Crea descrizione handoff minimale per evitare confusione"""
        return f"""
FOLLOW-UP TASK (Auto-generated with {analysis.confidence_score:.1%} confidence)

PREVIOUS TASK: {task.name}
EXPECTED OUTCOME: {handoff.get('expected_outcome', 'Continue previous work')}

CONTEXT: {handoff.get('context_summary', 'See previous task output')[:200]}...

INSTRUCTIONS:
1. Review the previous task output
2. Complete the specific outcome mentioned above
3. MARK AS COMPLETED when done - do not create further tasks
4. If unclear, escalate to Project Manager

NOTE: This is an automatically generated follow-up. Focus on completion, not expansion.
"""

    # ---------------------------------------------------------------------
    # Logging and monitoring
    # ---------------------------------------------------------------------
    async def _log_completion_analysis(
        self, 
        task: Task, 
        result_or_analysis: Any, 
        decision: str, 
        extra_info: str = ""
    ) -> None:
        """Log delle decisioni per monitoring"""
        
        if isinstance(result_or_analysis, dict) and "confidence_score" in result_or_analysis:
            # È un'analisi
            confidence = result_or_analysis.get("confidence_score", 0.0)
            reasoning = result_or_analysis.get("reasoning", "")
        else:
            # È un result
            confidence = 0.0
            reasoning = ""
        
        log_data = {
            "task_id": str(task.id),
            "task_name": task.name,
            "workspace_id": str(task.workspace_id),
            "decision": decision,
            "confidence": confidence,
            "reasoning": reasoning[:100] + "..." if len(reasoning) > 100 else reasoning,
            "extra_info": extra_info,
            "timestamp": datetime.now().isoformat(),
            "analyzer_config": {
                "auto_generation_enabled": self.auto_generation_enabled,
                "analysis_enabled": self.analysis_enabled,
                "handoff_creation_enabled": self.handoff_creation_enabled
            }
        }
        
        logger.info(f"TASK_COMPLETION_ANALYSIS: {json.dumps(log_data)}")

    # ---------------------------------------------------------------------
    # Cache management
    # ---------------------------------------------------------------------
    def cleanup_handoff_cache(self) -> None:
        """Cleanup cache periodico"""
        try:
            current_time = datetime.now()
            
            # Remove old entries
            expired_keys = [
                key for key, timestamp in self.handoff_cache.items()
                if current_time - timestamp > timedelta(hours=2)
            ]
            
            for key in expired_keys:
                del self.handoff_cache[key]
            
            # Limit analyzed tasks cache
            if len(self.analyzed_tasks) > 1000:
                # Keep only recent half
                analyzed_list = list(self.analyzed_tasks)
                self.analyzed_tasks = set(analyzed_list[-500:])
            
            self.last_cleanup = current_time
            logger.info(f"Cache cleanup: removed {len(expired_keys)} expired entries")
            
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")

    # ---------------------------------------------------------------------
    # Configuration methods
    # ---------------------------------------------------------------------
    def enable_auto_generation(self, enable_analysis: bool = True, enable_handoffs: bool = True):
        """Abilita auto-generation (SCONSIGLIATO)"""
        logger.warning("ENABLING AUTO-GENERATION - This may cause loops! Use with caution.")
        self.auto_generation_enabled = True
        self.analysis_enabled = enable_analysis
        self.handoff_creation_enabled = enable_handoffs

    def disable_auto_generation(self):
        """Disabilita auto-generation (DEFAULT SICURO)"""
        logger.info("Auto-generation disabled for safety")
        self.auto_generation_enabled = False
        self.analysis_enabled = False
        self.handoff_creation_enabled = False

    def get_status(self) -> Dict[str, Any]:
        """Status per monitoring"""
        return {
            "auto_generation_enabled": self.auto_generation_enabled,
            "analysis_enabled": self.analysis_enabled,
            "handoff_creation_enabled": self.handoff_creation_enabled,
            "confidence_threshold": self.confidence_threshold,
            "cooldown_minutes": self.cooldown_minutes,
            "max_auto_tasks_per_workspace": self.max_auto_tasks_per_workspace,
            "analyzed_tasks_count": len(self.analyzed_tasks),
            "handoff_cache_size": len(self.handoff_cache),
            "initialization_time": self.initialization_time.isoformat(),
            "last_cleanup": self.last_cleanup.isoformat(),
        }

    # Metodi per compatibility con vecchie versioni
    def _should_analyze_task_conservative(self, task: Task, result: Dict[str, Any]) -> bool:
        """Alias per backward compatibility"""
        return self._should_analyze_task_ultra_conservative(task, result)

    def _is_handoff_duplicate(self, task: Task, ctx: Dict[str, Any]) -> bool:
        """Alias per backward compatibility"""
        return self._is_handoff_duplicate_strict(task, ctx)

# Funzione per inizializzazione globale
def get_enhanced_task_executor() -> EnhancedTaskExecutor:
    """Get singleton instance"""
    if not hasattr(get_enhanced_task_executor, '_instance'):
        get_enhanced_task_executor._instance = EnhancedTaskExecutor()
    return get_enhanced_task_executor._instance