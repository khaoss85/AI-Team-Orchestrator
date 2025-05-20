# backend/task_analyzer.py
import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set

# IMPORT AGGIORNATI per compatibilità con i nuovi models
from models import Task, TaskStatus
from database import create_task, list_agents, list_tasks, get_workspace

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Structured outputs per task analysis
# ---------------------------------------------------------------------------
class TaskAnalysisOutput:
    """Structured output for task completion analysis - usando dict invece di BaseModel"""
    def __init__(
        self,
        requires_follow_up: bool = False,
        confidence_score: float = 0.0,
        suggested_handoffs: List[Dict[str, str]] = None,
        project_status: str = "completed",
        reasoning: str = "",
        next_phase: Optional[str] = None
    ):
        self.requires_follow_up = requires_follow_up
        self.confidence_score = confidence_score
        self.suggested_handoffs = suggested_handoffs or []
        self.project_status = project_status
        self.reasoning = reasoning
        self.next_phase = next_phase

    def __dict__(self):
        return {
            "requires_follow_up": self.requires_follow_up,
            "confidence_score": self.confidence_score,
            "suggested_handoffs": self.suggested_handoffs,
            "project_status": self.project_status,
            "reasoning": self.reasoning,
            "next_phase": self.next_phase
        }

# ---------------------------------------------------------------------------
# Main task completion analyzer (STRICT ANTI-LOOP VERSION)
# ---------------------------------------------------------------------------
class EnhancedTaskExecutor:
    """
    Enhanced task executor with STRICT anti-loop protection.
    
    Key principles:
    1. Auto-generation is DISABLED by default
    2. PM handles task creation, not this analyzer
    3. Only logs completion without creating new tasks
    """

    def __init__(self):
        # STRICT ANTI-LOOP CONFIGURATION
        self.auto_generation_enabled = True  # CRITICO: Disabilitato di default
        self.analysis_enabled = True         # NO analisi LLM automatica
        self.handoff_creation_enabled = True # NO handoff automatici
        
        # Cache per tracking (solo per monitoring)
        self.analyzed_tasks: Set[str] = set()
        self.handoff_cache: Dict[str, datetime] = {}
        
        # Configurazioni ultra-conservative
        self.confidence_threshold = 0.70  
        self.max_auto_tasks_per_workspace = 5  
        self.cooldown_minutes = 60  
        
        # Monitoring
        self.initialization_time = datetime.now()
        self.last_cleanup = datetime.now()
        
        logger.info("EnhancedTaskExecutor initialized with STRICT ANTI-LOOP protection")
        logger.info(f"Config: auto_gen={self.auto_generation_enabled}, analysis={self.analysis_enabled}, handoffs={self.handoff_creation_enabled}")

    # ---------------------------------------------------------------------
    # MAIN ENTRY POINT - Handle task completion
    # ---------------------------------------------------------------------
    async def handle_task_completion(
        self,
        completed_task: Task,
        task_result: Dict[str, Any],
        workspace_id: str,
    ) -> None:
        """
        Handle task completion with SELETTIVA per PM.
        PM task: crea sempre sub-task automaticamente
        Altri task: solo se auto-generation abilitata
        """
        
        task_id_str = str(completed_task.id)
        
        # Determina se è un PM task
        is_pm_task = await self._is_project_manager_task(completed_task, task_result)
        
        # PM auto-generation: sempre abilitata
        if is_pm_task:
            logger.info(f"Project Manager task detected {task_id_str} - executing auto-generation")
            pm_created_tasks = await self.handle_project_manager_completion(
                completed_task, task_result, workspace_id
            )
            
            if pm_created_tasks:
                return  # Task PM completato con successo
        
        # Per non-PM: usa la logica esistente solo se auto-generation è abilitata
        if not self.auto_generation_enabled:
            logger.info(f"Non-PM task {task_id_str}: auto-generation globally disabled")
            await self._log_completion_analysis(
                task=completed_task, 
                result_or_analysis=task_result, 
                decision="auto_generation_globally_disabled",
                extra_info="Analyzer configured for safety - no auto tasks created"
            )
            return
        
        # Resto della logica esistente per task non-PM...
        if task_id_str in self.analyzed_tasks:
            logger.info(f"Task {task_id_str} already processed - skipping")
            return
        
        self.analyzed_tasks.add(task_id_str)

        try:
            # Ultra-conservative filtering per non-PM
            if not self._should_analyze_task_ultra_conservative(completed_task, task_result):
                await self._log_completion_analysis(completed_task, task_result, "filtered_out_conservative")
                return

            # Minimal context gathering (evita operazioni costose)
            workspace_ctx = await self._gather_minimal_context(workspace_id)

            # Strict limits check
            if not self._check_strict_workspace_limits(workspace_ctx):
                logger.info(f"Workspace {workspace_id} at strict limits - no auto-generation")
                await self._log_completion_analysis(completed_task, task_result, "workspace_limits_exceeded")
                return

            # Duplicate prevention
            if self._is_handoff_duplicate_strict(completed_task, workspace_ctx):
                logger.warning(f"Duplicate handoff prevented for task {task_id_str}")
                await self._log_completion_analysis(completed_task, task_result, "duplicate_prevented")
                return

            # Analysis (deterministic only - no LLM)
            analysis = self._analyze_task_deterministic(completed_task, task_result, workspace_ctx)

            # Action ONLY if all conditions met AND explicitly enabled
            if (self.handoff_creation_enabled and 
                analysis.requires_follow_up and 
                analysis.confidence_score >= self.confidence_threshold and 
                analysis.suggested_handoffs):
                
                logger.warning(f"CREATING AUTO-TASK for {task_id_str} (confidence: {analysis.confidence_score:.3f})")
                await self._execute_minimal_handoff(analysis, completed_task, workspace_id)
            else:
                logger.info(f"Task {task_id_str} analysis complete - no follow-up (confidence: {analysis.confidence_score:.3f})")
                await self._log_completion_analysis(completed_task, analysis.__dict__(), "analysis_complete_no_action")

        except Exception as e:
            logger.error(f"Error in handle_task_completion for {task_id_str}: {e}", exc_info=True)
            await self._log_completion_analysis(completed_task, task_result, "analysis_error", str(e))

    # ---------------------------------------------------------------------
    # PROJECT MANAGER SPECIFIC HANDLING
    # ---------------------------------------------------------------------
    async def handle_project_manager_completion(
        self,
        task: Task, # Assumendo che Task sia il tipo corretto importato da models
        result: Dict[str, Any],
        workspace_id: str
    ) -> bool:
        """
        Gestisce specificamente il completamento di task del Project Manager
        creando automaticamente i sub-task definiti nel risultato.

        Returns:
            bool: True se ha creato sub-task, False altrimenti
        """

        logger.info(f"Handling PM task completion: {task.id} ('{task.name}')")

        # --- DEBUGGING LOGS INIZIO ---
        logger.info(f"PM_HANDLER_DEBUG --- Task ID: {task.id} --- Received result dictionary keys: {list(result.keys())}")
        detailed_results_json_content = result.get("detailed_results_json")

        if detailed_results_json_content is not None:
            logger.info(f"PM_HANDLER_DEBUG --- detailed_results_json IS PRESENT. Type: {type(detailed_results_json_content)}. Content snippet: {str(detailed_results_json_content)[:500]}")
        else:
            # Logga l'intero 'result' se 'detailed_results_json' è mancante o None per un debug completo
            try:
                result_dump_for_log = json.dumps(result)
            except TypeError: # In caso 'result' non sia serializzabile direttamente
                result_dump_for_log = str(result)
            logger.error(f"PM_HANDLER_CRITICAL_DEBUG --- detailed_results_json IS MISSING or None in result for task {task.id}. Full result for debugging: {result_dump_for_log}")
            return False # Esce se manca il campo fondamentale
        # --- DEBUGGING LOGS FINE ---

        # Rinomina la variabile per chiarezza, ora sappiamo che non è None
        detailed_results_str = detailed_results_json_content

        # Il log originale per "No detailed_results_json" non dovrebbe più essere raggiunto se il controllo sopra ritorna False.
        # Se si raggiunge questo punto, detailed_results_str è una stringa (o qualcosa che si comporta come tale).
        if not isinstance(detailed_results_str, str) or not detailed_results_str.strip():
            logger.error(f"PM task {task.id}: detailed_results_json is present but is not a non-empty string. Type: {type(detailed_results_str)}. Content: '{detailed_results_str}'")
            return False

        try:
            # Parse del JSON dei risultati
            try:
                results_data = json.loads(detailed_results_str)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse detailed_results_json string for task {task.id}: {e}. Content was: {detailed_results_str}")
                return False

            # Cerca i sub-task definiti
            defined_subtasks = results_data.get("defined_sub_tasks", [])
            if not defined_subtasks:
                logger.info(f"No defined_sub_tasks found in the parsed JSON for PM task {task.id}")
                return False

            if not isinstance(defined_subtasks, list):
                logger.error(f"PM task {task.id}: 'defined_sub_tasks' is not a list. Found: {type(defined_subtasks)}")
                return False

            logger.info(f"Found {len(defined_subtasks)} sub-tasks to create for PM task {task.id}")

            # Importa create_task qui per evitare circular imports se necessario, o assicurati sia importato a livello di modulo
            from database import create_task

            created_count = 0
            created_tasks_details = [] # Per un log più dettagliato

            for subtask_def in defined_subtasks:
                if not isinstance(subtask_def, dict):
                    logger.warning(f"Skipping invalid subtask definition (not a dict): {subtask_def}")
                    continue

                try:
                    required_fields = ["name", "description", "target_agent_role"]
                    if not all(field in subtask_def for field in required_fields):
                        logger.warning(f"Skipping subtask definition with missing required fields: {subtask_def}. Missing: {[f for f in required_fields if f not in subtask_def]}")
                        continue

                    target_role = subtask_def["target_agent_role"]
                    target_agent = await self._find_agent_by_role(workspace_id, target_role)

                    if not target_agent:
                        logger.warning(f"No active agent found for role '{target_role}' - skipping subtask creation for '{subtask_def['name']}'")
                        continue

                    # Crea il sub-task
                    created_task = await create_task(
                        workspace_id=workspace_id,
                        agent_id=str(target_agent["id"]), # Assicurati che l'ID sia una stringa
                        assigned_to_role=target_role,
                        name=subtask_def["name"],
                        description=subtask_def["description"],
                        status="pending", # Uso diretto di TaskStatus.PENDING.value se TaskStatus è un Enum
                        priority=subtask_def.get("priority", "medium"),
                        parent_task_id=str(task.id), # Assicurati che l'ID sia una stringa
                        context_data={
                            "created_by_pm_task_id": str(task.id),
                            "auto_generated_by_pm": True,
                            "source_pm_agent_id": str(task.agent_id) if task.agent_id else None
                        }
                    )

                    if created_task and created_task.get("id"):
                        created_count += 1
                        task_detail_for_log = {"id": created_task['id'], "name": subtask_def['name'], "assigned_to": target_agent.get('name')}
                        created_tasks_details.append(task_detail_for_log)
                        logger.info(f"Successfully created sub-task '{subtask_def['name']}' (ID: {created_task['id']}) and assigned to {target_agent.get('name', 'Unknown Agent')}")
                    else:
                        logger.error(f"Failed to create sub-task '{subtask_def['name']}' in database or no ID returned.")

                except Exception as e_subtask: # Catching more specific errors might be better
                    logger.error(f"Error processing subtask definition '{subtask_def.get('name', 'Unknown name')}': {e_subtask}", exc_info=True)
                    continue

            if created_count > 0:
                logger.info(f"PM auto-generation: Successfully created {created_count}/{len(defined_subtasks)} sub-tasks for PM task {task.id}. Details: {created_tasks_details}")
                # Questo log ora avviene dentro EnhancedTaskExecutor.handle_task_completion
                # await self._log_completion_analysis(
                # task,
                # {"created_subtasks_count": created_count, "details": created_tasks_details},
                # "pm_subtasks_created",
                # f"Created {created_count} sub-tasks."
                # )
                return True
            else:
                logger.info(f"PM auto-generation: No sub-tasks were created for PM task {task.id} out of {len(defined_subtasks)} defined.")
                return False

        except Exception as e_main:
            logger.error(f"Critical error in handle_project_manager_completion for task {task.id}: {e_main}", exc_info=True)
            # Anche qui, il logging dell'errore di analisi avviene in EnhancedTaskExecutor.handle_task_completion
            # await self._log_completion_analysis(
            # task,
            # {"error": str(e_main)},
            # "pm_handling_error",
            # str(e_main)
            # )
            return False


    async def _find_agent_by_role(self, workspace_id: str, role: str) -> Optional[Dict]:
        try:
            from database import list_agents as db_list_agents

            logger.info(f"PM_SUBTASK_AGENT_FINDER --- Attempting to find agent for role '{role}' in workspace '{workspace_id}'")
            agents_from_db = await db_list_agents(workspace_id)

            if not agents_from_db:
                logger.warning(f"PM_SUBTASK_AGENT_FINDER --- No agents returned from DB for workspace {workspace_id}.")
                return None

            logger.info(f"PM_SUBTASK_AGENT_FINDER --- Workspace: {workspace_id}, Target Role: '{role}'. Agents retrieved: {len(agents_from_db)}")
            for idx, agent_in_db in enumerate(agents_from_db):
                logger.info(f"PM_SUBTASK_AGENT_FINDER --- DB Agent {idx+1}: ID={agent_in_db.get('id')}, Name='{agent_in_db.get('name')}', Role='{agent_in_db.get('role')}', Status='{agent_in_db.get('status')}'")

            # INIZIO MODIFICHE: Normalizza i ruoli in modo più aggressivo
            # Rimuovi spazi e converti in lowercase per un matching più flessibile
            target_role_normalized = role.lower().replace(" ", "").strip()

            # Salva versione con spazi per logging
            target_role_lower = role.lower().strip()

            # Flag speciali per tipi di ruolo comuni
            is_target_manager = any(keyword in target_role_normalized for keyword in ["manager", "director", "lead", "coordinator"])

            candidate_agents = []
            for agent in agents_from_db:
                agent_role_db = agent.get("role", "")
                agent_name_db = agent.get("name", "")
                agent_status_db = agent.get("status")

                # Normalizza ruolo agente nello stesso modo
                agent_role_normalized = agent_role_db.lower().replace(" ", "").strip()

                # Per logging
                agent_role_db_lower = agent_role_db.lower().strip()

                logger.debug(f"PM_SUBTASK_AGENT_FINDER --- Comparing: DB Role='{agent_role_db_lower}' (Status='{agent_status_db}') vs Target Role='{target_role_lower}'")

                if agent_status_db == "active":  # Considera solo agenti attivi
                    match_score = 0

                    # === NUOVA EURISTICA DI MATCHING ===

                    # 1. Exact match con normalizzazione (senza spazi)
                    if agent_role_normalized == target_role_normalized:
                        match_score = 10

                    # 2. Il nome dell'agente corrisponde esattamente al ruolo richiesto
                    elif agent_name_db.lower() == target_role_lower or agent_name_db.lower().replace(" ", "") == target_role_normalized:
                        match_score = 9.5

                    # 3. Matching convenzionale (contenimento)
                    elif target_role_lower in agent_role_db_lower:
                        match_score = 8
                    elif agent_role_db_lower in target_role_lower:
                        match_score = 5

                    # 4. Matching speciale per ruoli di Project Manager
                    elif is_target_manager and any(keyword in agent_role_normalized for keyword in ["manager", "director", "lead", "coordinator"]):
                        match_score = 7
                        logger.info(f"PM_SUBTASK_AGENT_FINDER --- Manager role match: '{agent_role_db}' for target '{role}'")

                    # 5. Matching per subset di parole
                    if match_score < 5:
                        # Rimuovi parole comuni come "specialist" prima di confrontare
                        common_words = ["specialist", "the", "and", "of", "for"]

                        # Filtra le parole chiave del target
                        target_keywords = set([
                            word for word in target_role_lower.split() 
                            if word.lower() not in common_words
                        ])

                        # Filtra le parole chiave dell'agente
                        agent_role_keywords = set([
                            word for word in agent_role_db_lower.split() 
                            if word.lower() not in common_words
                        ])

                        # Calcola la sovrapposizione
                        if target_keywords and agent_role_keywords:
                            intersection = target_keywords.intersection(agent_role_keywords)
                            if len(intersection) > 0:
                                # Calcola il rapporto di sovrapposizione
                                overlap_ratio = len(intersection) / max(len(target_keywords), 1)
                                if overlap_ratio >= 0.5:  # Se almeno metà delle parole chiave corrispondono
                                    match_score = 6 + (overlap_ratio * 2)  # Punteggio tra 6 e 8 in base alla sovrapposizione

                    # Aggiunge bonus per seniority
                    seniority_bonus = {"expert": 0.3, "senior": 0.2, "junior": 0.1}
                    match_score += seniority_bonus.get(agent.get("seniority", "junior").lower(), 0)

                    # Soglia più bassa (4) per aumentare le possibilità di match
                    if match_score >= 4:
                        candidate_agents.append({"agent_dict": agent, "score": match_score})

            if not candidate_agents:
                logger.warning(f"PM_SUBTASK_AGENT_FINDER --- No suitable active agent found for role '{role}' in workspace {workspace_id} after checking {len(agents_from_db)} agents.")

                # NUOVO: Fallback per ruoli di management se PM non trovato
                if is_target_manager:
                    logger.info(f"PM_SUBTASK_AGENT_FINDER --- Attempting fallback for manager role '{role}'")
                    for agent in agents_from_db:
                        if agent.get("status") == "active" and any(kw in agent.get("role", "").lower() for kw in ["manager", "director", "lead"]):
                            logger.info(f"PM_SUBTASK_AGENT_FINDER --- Found manager fallback: {agent.get('name')} with role '{agent.get('role')}'")
                            return agent

                return None

            # Ordina i candidati per score (decrescente)
            candidate_agents.sort(key=lambda x: x["score"], reverse=True)

            best_match_agent_dict = candidate_agents[0]["agent_dict"]
            best_match_score = candidate_agents[0]["score"]
            logger.info(f"PM_SUBTASK_AGENT_FINDER --- Best match for role '{role}': Agent '{best_match_agent_dict.get('name')}' (Role: '{best_match_agent_dict.get('role')}', Score: {best_match_score})")
            return best_match_agent_dict

        except Exception as e:
            logger.error(f"PM_SUBTASK_AGENT_FINDER --- Error in _find_agent_by_role for role '{role}', workspace '{workspace_id}': {e}", exc_info=True)
            return None

    async def _is_project_manager_task(self, task: Task, result: Dict[str, Any]) -> bool:
        """Determina se un task è stato completato da un Project Manager"""
        
        try:
            # Metodo 1: Controlla l'agent_id se disponibile
            if task.agent_id:
                from database import get_agent
                agent_data = await get_agent(str(task.agent_id))
                if agent_data:
                    role = agent_data.get('role', '').lower()
                    if any(kw in role for kw in ['manager', 'coordinator', 'director', 'lead']):
                        return True
        except Exception as e:
            logger.warning(f"Could not check agent role for task {task.id}: {e}")
        
        # Metodo 2: Euristiche basate sul contenuto del task
        task_name = task.name.lower()
        task_desc = (task.description or "").lower()
        
        # Indicatori di task di PM
        pm_indicators = [
            "project setup", "strategic planning", "kick-off",
            "planning", "coordination", "project manager",
            "team assessment", "phase breakdown", "delegate"
        ]
        
        return any(indicator in task_name or indicator in task_desc for indicator in pm_indicators)

    # ---------------------------------------------------------------------
    # Ultra-conservative analysis filters
    # ---------------------------------------------------------------------
    def _should_analyze_task_ultra_conservative(self, task: Task, result: Dict[str, Any]) -> bool:
        """
        ULTRA-STRICT filter - rejects 99%+ of tasks.
        Only allows analysis in very specific, controlled scenarios.
        """
        
        # ONLY completed tasks
        if result.get("status") != "completed":
            return False

        # REJECT if any completion indicators in name
        task_name_lower = task.name.lower()
        completion_words = [
            "handoff", "follow-up", "continuation", "escalation", 
            "coordination", "review", "feedback", "completed", 
            "done", "finished", "delivered", "final", "wrap-up",
            "summary", "report", "status", "update"
        ]
        
        if any(word in task_name_lower for word in completion_words):
            return False

        # REJECT if output suggests completion
        output = str(result.get("summary", "") + " " + result.get("detailed_results_json", ""))
        output_lower = output.lower()
        completion_phrases = [
            "task complete", "objective achieved", "deliverable ready",
            "no further action", "project finished", "all requirements met",
            "final result", "conclusion", "successfully completed",
            "ready for review", "handed off", "escalated"
        ]
        
        if any(phrase in output_lower for phrase in completion_phrases):
            return False

        # REJECT if has explicit next_steps (PM should handle planning)
        #if result.get("next_steps"):
        #    return False

        # REJECT if output too long (probably comprehensive)
        if len(output) > 800:
            return False

        # REJECT if task has parent (likely already part of a workflow)
        if task.parent_task_id:
            return False

        # ONLY allow very specific research/planning patterns
        allowed_patterns = [
            "initial research",
            "preliminary analysis", 
            "feasibility assessment",
            "requirement gathering"
        ]
        
        if not any(pattern in task_name_lower for pattern in allowed_patterns):
            return False

        logger.debug(f"Task {task.id} passed ultra-conservative filter")
        return True

    def _check_strict_workspace_limits(self, ctx: Dict[str, Any]) -> bool:
        """Extremely strict limits for workspace auto-generation"""
        
        # NO auto-generation if ANY pending tasks
        if ctx.get("pending_tasks", 1) > 3:
            return False
        
        # Require 95%+ completion rate
        total_tasks = ctx.get("total_tasks", 1)
        completed_tasks = ctx.get("completed_tasks", 0)
        completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
        
        if completion_rate < 0.70:
            return False
        
        # Minimum task count to establish pattern
        if total_tasks < 3:
            return False
        
        return True

    def _is_handoff_duplicate_strict(self, task: Task, ctx: Dict[str, Any]) -> bool:
        """Absolute duplicate prevention"""
        
        # Check recent cache
        cache_key = f"{task.workspace_id}_{task.agent_id}_handoff"
        recent_handoff = self.handoff_cache.get(cache_key)
        if recent_handoff and datetime.now() - recent_handoff < timedelta(hours=24):
            return True

        # Check ANY recent tasks with handoff/follow-up patterns
        recent_tasks = ctx.get("recent_completions", [])
        task_words = set(task.name.lower().split())
        
        for recent_task in recent_tasks[-10:]:  # Check last 10
            recent_name = recent_task.get("name", "").lower()
            
            # If ANY recent task mentions handoff/follow-up
            if any(word in recent_name for word in ["handoff", "follow-up", "continuation", "next"]):
                return True
                
            # If task name overlap > 50%
            recent_words = set(recent_name.split())
            overlap = len(task_words & recent_words) / len(task_words | recent_words)
            if overlap > 0.5:
                return True

        return False

    # ---------------------------------------------------------------------
    # Minimal context gathering (avoid expensive operations)
    # ---------------------------------------------------------------------
    async def _gather_minimal_context(self, workspace_id: str) -> Dict[str, Any]:
        """Gather only essential context data without expensive operations"""
        try:
            # Get basic workspace info
            workspace = await get_workspace(workspace_id)
            tasks = await list_tasks(workspace_id)

            # Simple categorization
            completed = [t for t in tasks if t.get("status") == TaskStatus.COMPLETED.value]
            pending = [t for t in tasks if t.get("status") == TaskStatus.PENDING.value]
            
            return {
                "workspace_goal": workspace.get("goal", "") if workspace else "",
                "total_tasks": len(tasks),
                "completed_tasks": len(completed),
                "pending_tasks": len(pending),
                "recent_completions": [
                    {"name": t.get("name", ""), "id": t.get("id", "")}
                    for t in completed[-5:]  # Only last 5
                ],
            }
        except Exception as e:
            logger.error(f"Error gathering minimal context: {e}")
            return {
                "workspace_goal": "",
                "total_tasks": 0,
                "completed_tasks": 0,
                "pending_tasks": 0,
                "recent_completions": [],
            }

    # ---------------------------------------------------------------------
    # Deterministic analysis (NO AI/LLM)
    # ---------------------------------------------------------------------
    def _analyze_task_deterministic(
        self,
        task: Task,
        result: Dict[str, Any],
        ctx: Dict[str, Any],
    ) -> TaskAnalysisOutput:
        """
        Pure rule-based analysis without any LLM calls.
        Extremely conservative - designed to almost never trigger.
        """
        
        # Default: NO follow-up
        analysis = TaskAnalysisOutput(
            requires_follow_up=False,
            confidence_score=0.0,
            suggested_handoffs=[],
            project_status="completed",
            reasoning="Deterministic analysis - no follow-up detected"
        )

        try:
            output_text = str(result.get("summary", ""))
            output_lower = output_text.lower()
            
            # Rule-based detection (very specific patterns)
            follow_up_patterns = [
                "analysis indicates need for",
                "research suggests next step",
                "preliminary findings require",
                "initial assessment shows need"
            ]
            
            pattern_matches = sum(1 for pattern in follow_up_patterns if pattern in output_lower)
            
            # Must have multiple strong indicators
            if pattern_matches >= 2 and len(output_text) > 100:
                confidence = 0.7  # Still below threshold
                
                analysis.confidence_score = confidence
                analysis.reasoning = f"Matched {pattern_matches} follow-up patterns"
                
                # Even with patterns, don't suggest follow-up unless explicitly requested
                # This is intentionally restrictive
                logger.debug(f"Task {task.id} analysis: confidence {confidence}, but no auto-generation")
            
            analysis.reasoning += f" | Output: {len(output_text)}chars, Pending: {ctx['pending_tasks']}"
            
        except Exception as e:
            logger.error(f"Error in deterministic analysis: {e}")
            analysis.reasoning = f"Analysis error: {str(e)}"
        
        return analysis

    # ---------------------------------------------------------------------
    # Minimal handoff execution (if ever enabled)
    # ---------------------------------------------------------------------
    async def _execute_minimal_handoff(
        self,
        analysis: TaskAnalysisOutput,
        task: Task,
        workspace_id: str,
    ) -> None:
        """
        Execute handoff with absolute minimal scope.
        This should rarely/never be called given our strict thresholds.
        """
        
        logger.warning(f"EXECUTING AUTO-HANDOFF for task {task.id} - This should be rare!")
        
        if not analysis.suggested_handoffs:
            return
        
        try:
            # Set cache immediately to prevent duplicates
            cache_key = f"{workspace_id}_handoff"
            self.handoff_cache[cache_key] = datetime.now()
            
            # Create minimal follow-up task
            description = f"""AUTOMATED FOLLOW-UP (Generated from: {task.name})

ORIGINAL TASK OUTPUT SUMMARY:
{str(task.description)[:200]}...

INSTRUCTION: 
- Review the original task output
- Complete any explicitly mentioned next step
- MARK AS COMPLETED when done
- DO NOT create additional tasks

NOTE: This is an experimental auto-generated task. 
If unclear, escalate to Project Manager immediately.
"""
            
            # Create with PENDING status for PM to review
            new_task = await create_task(
                workspace_id=workspace_id,
                name=f"AUTO: Follow-up for {task.name[:30]}...",
                description=description,
                status=TaskStatus.PENDING.value,
                parent_task_id=task.id  # Link to original
            )
            
            if new_task:
                logger.warning(f"Created auto-task {new_task.get('id')} - Notify PM for review!")
                await self._log_completion_analysis(
                    task, 
                    analysis.__dict__(), 
                    "auto_task_created", 
                    f"Task ID: {new_task.get('id')}"
                )
            
        except Exception as e:
            logger.error(f"Error executing minimal handoff: {e}", exc_info=True)
            await self._log_completion_analysis(task, analysis.__dict__(), "handoff_error", str(e))

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
        """Comprehensive logging for monitoring and debugging"""
        
        # Extract confidence and reasoning if available
        confidence = 0.0
        reasoning = ""
        
        if isinstance(result_or_analysis, dict):
            if "confidence_score" in result_or_analysis:
                confidence = result_or_analysis.get("confidence_score", 0.0)
                reasoning = result_or_analysis.get("reasoning", "")
            elif hasattr(result_or_analysis, '__dict__'):
                # Handle TaskAnalysisOutput objects
                analysis_dict = result_or_analysis.__dict__()
                confidence = analysis_dict.get("confidence_score", 0.0)
                reasoning = analysis_dict.get("reasoning", "")
        
        log_data = {
            "task_id": str(task.id),
            "task_name": task.name,
            "workspace_id": str(task.workspace_id),
            "agent_id": str(task.agent_id) if task.agent_id else None,
            "assigned_to_role": task.assigned_to_role,
            "task_priority": task.priority,
            "decision": decision,
            "confidence": confidence,
            "reasoning": reasoning[:200] + "..." if len(reasoning) > 200 else reasoning,
            "extra_info": extra_info,
            "timestamp": datetime.now().isoformat(),
            "analyzer_config": {
                "auto_generation_enabled": self.auto_generation_enabled,
                "analysis_enabled": self.analysis_enabled,
                "handoff_creation_enabled": self.handoff_creation_enabled,
                "confidence_threshold": self.confidence_threshold
            }
        }
        
        logger.info(f"TASK_COMPLETION_ANALYSIS: {json.dumps(log_data)}")

    # ---------------------------------------------------------------------
    # Cache management and maintenance
    # ---------------------------------------------------------------------
    def cleanup_caches(self) -> None:
        """Periodic cache cleanup to prevent memory leaks"""
        try:
            current_time = datetime.now()
            
            # Remove old handoff cache entries (older than 24 hours)
            expired_keys = [
                key for key, timestamp in self.handoff_cache.items()
                if current_time - timestamp > timedelta(hours=24)
            ]
            
            for key in expired_keys:
                del self.handoff_cache[key]
            
            # Limit analyzed tasks cache size
            if len(self.analyzed_tasks) > 1000:
                # Keep only recent half
                analyzed_list = list(self.analyzed_tasks)
                self.analyzed_tasks = set(analyzed_list[-500:])
            
            self.last_cleanup = current_time
            logger.info(f"Cache cleanup completed: removed {len(expired_keys)} expired entries")
            
        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")

    # ---------------------------------------------------------------------
    # Configuration and status methods
    # ---------------------------------------------------------------------
    def enable_auto_generation(
        self, 
        enable_analysis: bool = True, 
        enable_handoffs: bool = True,
        confidence_threshold: float = 0.95
    ):
        """
        Enable auto-generation - USE WITH EXTREME CAUTION!
        Only for testing or very controlled environments.
        """
        logger.critical("⚠️  ENABLING AUTO-GENERATION! This may cause task loops. Monitor carefully!")
        self.auto_generation_enabled = True
        self.analysis_enabled = enable_analysis
        self.handoff_creation_enabled = enable_handoffs
        self.confidence_threshold = confidence_threshold
        
        logger.warning(f"Auto-generation config: analysis={enable_analysis}, handoffs={enable_handoffs}, threshold={confidence_threshold}")

    def disable_auto_generation(self):
        """
        Disable auto-generation completely (recommended default)
        """
        logger.info("Auto-generation disabled - system returned to safe state")
        self.auto_generation_enabled = False  
        self.analysis_enabled = False
        self.handoff_creation_enabled = False
        self.confidence_threshold = 0.99  # Reset to ultra-high

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status for monitoring dashboard"""
        return {
            "auto_generation_enabled": self.auto_generation_enabled,
            "analysis_enabled": self.analysis_enabled,
            "handoff_creation_enabled": self.handoff_creation_enabled,
            "confidence_threshold": self.confidence_threshold,
            "cooldown_minutes": self.cooldown_minutes,
            "max_auto_tasks_per_workspace": self.max_auto_tasks_per_workspace,
            
            # Cache stats
            "analyzed_tasks_count": len(self.analyzed_tasks),
            "handoff_cache_size": len(self.handoff_cache),
            
            # Timing
            "initialization_time": self.initialization_time.isoformat(),
            "last_cleanup": self.last_cleanup.isoformat(),
            "uptime_hours": (datetime.now() - self.initialization_time).total_seconds() / 3600,
            
            # Safety status
            "safety_mode": "STRICT" if not self.auto_generation_enabled else "PERMISSIVE",
            "risk_level": "LOW" if not self.auto_generation_enabled else "HIGH"
        }

    def force_cleanup(self):
        """Manual cleanup trigger for maintenance"""
        self.cleanup_caches()
        logger.info("Manual cache cleanup completed")
        
        
# ---------------------------------------------------------------------
# Global instance management
# ---------------------------------------------------------------------
_enhanced_executor_instance = None

def get_enhanced_task_executor() -> EnhancedTaskExecutor:
    """Get singleton instance of enhanced task executor"""
    global _enhanced_executor_instance
    if _enhanced_executor_instance is None:
        _enhanced_executor_instance = EnhancedTaskExecutor()
    return _enhanced_executor_instance

def reset_enhanced_task_executor():
    """Reset singleton instance (for testing)"""
    global _enhanced_executor_instance
    _enhanced_executor_instance = None
    logger.info("Enhanced task executor instance reset")