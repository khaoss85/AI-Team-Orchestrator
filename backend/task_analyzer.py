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
        """Main handler with strict separation between PM and specialist flows."""
        task_id_str = str(completed_task.id)

        # Skip already-analyzed tasks
        if task_id_str in self.analyzed_tasks:
            logger.info(f"Task {task_id_str} already processed - skipping")
            return
        self.analyzed_tasks.add(task_id_str)

        try:
            # --- PM VS SPECIALIST DISPATCH ----------------------------------
            is_pm_task = await self._is_project_manager_task(completed_task, task_result)

            # --------------------- PM FLOW -----------------------------------
            if is_pm_task:
                logger.info(f"Processing task {task_id_str} as PM TASK")

                # PM tasks always create sub-tasks
                pm_created_tasks = await self.handle_project_manager_completion(
                    completed_task, task_result, workspace_id
                )

                await self._log_completion_analysis(
                    completed_task,
                    task_result,
                    "pm_task_processed",
                    f"Sub-tasks created: {pm_created_tasks}",
                )
                return

            # ----------------- SPECIALIST FLOW ------------------------------
            logger.info(f"Processing task {task_id_str} as SPECIALIST TASK")

            # Process specialist task based on auto-generation settings
            if not self.auto_generation_enabled:
                logger.info(f"Task {task_id_str}: auto-generation disabled for specialist tasks")
                await self._log_completion_analysis(
                    completed_task, task_result, "specialist_task_completed_no_auto_gen"
                )
            else:
                # Ultra-conservative filtering (cheap checks first)
                if not self._should_analyze_task_ultra_conservative(completed_task, task_result):
                    await self._log_completion_analysis(
                        completed_task, task_result, "filtered_out_conservative"
                    )
                else:
                    # Minimal workspace context (cheap)
                    workspace_ctx = await self._gather_minimal_context(workspace_id)

                    # Strict quota / limits
                    if not self._check_strict_workspace_limits(workspace_ctx):
                        logger.info(f"Workspace {workspace_id} at strict limits - no auto-generation")
                        await self._log_completion_analysis(
                            completed_task, task_result, "workspace_limits_exceeded"
                        )
                    else:
                        # Duplicate prevention
                        if self._is_handoff_duplicate_strict(completed_task, workspace_ctx):
                            logger.warning(f"Duplicate handoff prevented for task {task_id_str}")
                            await self._log_completion_analysis(
                                completed_task, task_result, "duplicate_prevented"
                            )
                        else:
                            # Deterministic (no-LLM) analysis
                            analysis = self._analyze_task_deterministic(
                                completed_task, task_result, workspace_ctx
                            )

                            # Create follow-up task only if every hard gate passes
                            if (
                                self.handoff_creation_enabled
                                and analysis.requires_follow_up
                                and analysis.confidence_score >= self.confidence_threshold
                                and analysis.suggested_handoffs
                            ):
                                logger.warning(
                                    f"CREATING AUTO-TASK for {task_id_str} (confidence: {analysis.confidence_score:.3f})"
                                )
                                await self._execute_minimal_handoff(analysis, completed_task, workspace_id)
                            else:
                                logger.info(
                                    f"Task {task_id_str} analysis complete - no follow-up "
                                    f"(confidence: {analysis.confidence_score:.3f})"
                                )
                                await self._log_completion_analysis(
                                    completed_task, analysis.__dict__(), "analysis_complete_no_action"
                                )

            # ----- NUOVO: CHECK COMPLETAMENTO FASE DOPO OGNI TASK SPECIALISTA -----
            # Questo viene eseguito sempre dopo aver processato un task specialista,
            # indipendentemente dalle impostazioni di auto-generation
            try:
                pm_task_id = await self.check_phase_completion_and_trigger_pm(workspace_id)
                if pm_task_id:
                    logger.info(f"Phase completion detected - created PM task {pm_task_id}")
                    await self._log_completion_analysis(
                        completed_task, task_result, "phase_transition_triggered", 
                        f"Created PM task: {pm_task_id}"
                    )
            except Exception as e:
                logger.error(f"Error in phase completion check: {e}")

        except Exception as e:
            logger.error(f"Error in handle_task_completion for {task_id_str}: {e}", exc_info=True)
            await self._log_completion_analysis(
                completed_task, task_result, "error_processing_task", str(e)
            )

    # ---------------------------------------------------------------------
    # PROJECT MANAGER SPECIFIC HANDLING
    # ---------------------------------------------------------------------
    async def handle_project_manager_completion(
        self,
        task: Task, 
        result: Dict[str, Any],
        workspace_id: str
    ) -> bool:
        """Handles Project Manager task completion by creating defined sub-tasks."""

        logger.info(f"Handling PM task completion: {task.id} ('{task.name}')")

        # Extract detailed_results_json with proper validation
        detailed_results_json_content = result.get("detailed_results_json")

        # Log detailed debugging info
        logger.info(f"PM_HANDLER_DEBUG - Task {task.id} - Result keys: {list(result.keys())}")
        if detailed_results_json_content is not None:
            logger.info(f"PM_HANDLER_DEBUG - detailed_results_json type: {type(detailed_results_json_content)}")
        else:
            logger.error(f"PM_HANDLER_CRITICAL - detailed_results_json IS MISSING for task {task.id}")

        # Parse the detailed_results_json to extract sub-tasks
        defined_subtasks = []

        # Source 1: Parse detailed_results_json if it exists and is valid
        if isinstance(detailed_results_json_content, str) and detailed_results_json_content.strip():
            try:
                results_data = json.loads(detailed_results_json_content)

                # Try multiple possible keys for sub-tasks
                if isinstance(results_data, dict):
                    for key in ["defined_sub_tasks", "sub_tasks", "subtasks", "tasks", "next_tasks"]:
                        if key in results_data and isinstance(results_data[key], list):
                            defined_subtasks.extend(results_data[key])
                            logger.info(f"Found {len(results_data[key])} sub-tasks in key '{key}'")
                            break  # Only use the first valid key found
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse detailed_results_json for task {task.id}: {e}")

        # Source 2: Try next_steps as fallback
        if not defined_subtasks:
            logger.info(f"No sub-tasks found in detailed_results_json for task {task.id}. Trying next_steps.")
            next_steps = result.get("next_steps", [])

            if isinstance(next_steps, list) and next_steps:
                for step in next_steps:
                    if not isinstance(step, str) or not step.strip():
                        continue

                    # Infer target_role from step content
                    step_lower = step.lower()
                    target_role = "Specialist"  # Default

                    if any(kw in step_lower for kw in ["analy", "data", "research"]):
                        target_role = "AnalysisSpecialist"
                    elif any(kw in step_lower for kw in ["content", "write", "text"]):
                        target_role = "ContentSpecialist"
                    elif any(kw in step_lower for kw in ["develop", "implement", "code"]):
                        target_role = "TechnicalSpecialist"

                    subtask = {
                        "name": f"Follow-up: {step[:50]}..." if len(step) > 50 else f"Follow-up: {step}",
                        "description": f"Complete the following task defined by the Project Manager:\n\n{step}",
                        "target_agent_role": target_role,
                        "priority": "medium"
                    }
                    defined_subtasks.append(subtask)

                if defined_subtasks:
                    logger.info(f"Created {len(defined_subtasks)} sub-tasks from next_steps")

        # Create the sub-tasks in the database
        from database import create_task
        
        try:
            all_workspace_tasks = await list_tasks(workspace_id)
            completed_tasks_count = len([t for t in all_workspace_tasks if t.get("status") == "completed"])
        except Exception as e:
            logger.warning(f"Could not count completed tasks for workspace {workspace_id}: {e}")
            completed_tasks_count = 0

        created_count = 0
        created_tasks_ids = []

        for subtask_def in defined_subtasks:
            if not isinstance(subtask_def, dict):
                logger.warning(f"Skipping invalid subtask definition (not a dict): {subtask_def}")
                continue

            try:
                # Validate required fields
                required_fields = ["name", "description", "target_agent_role"]
                if not all(field in subtask_def for field in required_fields):
                    logger.warning(f"Skipping subtask missing required fields: {subtask_def}")
                    continue

                # Find appropriate agent by role with improved logging
                target_role = subtask_def["target_agent_role"]
                target_agent = await self._find_agent_by_role(workspace_id, target_role)

                if not target_agent:
                    logger.warning(f"No agent found for role '{target_role}'. Skipping subtask: {subtask_def['name']}")
                    continue

                # Create the sub-task with explicit attribution tracking
                created_task = await create_task(
                    workspace_id=workspace_id,
                    agent_id=str(target_agent["id"]),
                    assigned_to_role=target_role,
                    name=subtask_def["name"],
                    description=subtask_def["description"],
                    status="pending",
                    priority=subtask_def.get("priority", "medium"),
                    parent_task_id=str(task.id),

                    # TRACKING AUTOMATICO
                    created_by_task_id=str(task.id),  # Il PM task che ha creato questo subtask
                    created_by_agent_id=str(task.agent_id) if task.agent_id else None,
                    creation_type="pm_completion",  # Creato dal completamento di un task PM

                    # CONTEXT DATA SPECIFICO
                    context_data={
                        "auto_generated_by_pm": True,
                        "source_pm_task_name": task.name,
                        "project_phase": self._determine_project_phase(subtask_def["name"], subtask_def["description"], completed_tasks_count),
                        "failure_count": 0,
                        "expected_completion_criteria": subtask_def.get("completion_criteria", "Task completed by agent"),
                        "subtask_definition_source": "pm_detailed_results_json",
                        "pm_completion_timestamp": datetime.now().isoformat()
                    }
                )

                if created_task and created_task.get("id"):
                    created_count += 1
                    created_tasks_ids.append(created_task["id"])
                    logger.info(f"Created sub-task '{subtask_def['name']}' (ID: {created_task['id']}) for agent {target_agent.get('name')}")
                else:
                    logger.error(f"Failed to create sub-task in database: {subtask_def['name']}")

            except Exception as e:
                logger.error(f"Error creating sub-task '{subtask_def.get('name', 'Unknown')}': {e}", exc_info=True)

        logger.info(f"PM task {task.id} completion: Created {created_count}/{len(defined_subtasks)} sub-tasks")
        return created_count > 0

    async def _find_agent_by_role(self, workspace_id: str, role: str) -> Optional[Dict]:
        """Find agent by role with improved matching logic that prioritizes exact and semantic matches"""
        try:
            from database import list_agents as db_list_agents

            agents_from_db = await db_list_agents(workspace_id)
            if not agents_from_db:
                logger.warning(f"No agents in workspace {workspace_id}")
                return None

            # Normalizza target role
            target_role_lower = role.lower().strip()
            target_role_normalized = target_role_lower.replace(" ", "")

            # Estrai parole chiave significative (rimuovi parole comuni)
            common_words = {"specialist", "the", "and", "of", "for", "in", "a", "an"}
            target_role_words = set(word for word in target_role_lower.split() if word not in common_words)

            # Flag speciali
            is_target_manager = any(keyword in target_role_normalized for keyword in 
                                   ["manager", "coordinator", "director", "lead", "pm"])

            candidates = []

            for agent in agents_from_db:
                if agent.get("status") != "active":
                    continue

                agent_role = agent.get("role", "").lower().strip()
                agent_name = agent.get("name", "").lower().strip()
                agent_role_normalized = agent_role.replace(" ", "")
                agent_role_words = set(word for word in agent_role.split() if word not in common_words)
                agent_name_words = set(word for word in agent_name.split() if word not in common_words)

                score = 0
                match_reason = ""

                # 1. EXACT MATCH su role
                if agent_role == target_role_lower:
                    score = 100
                    match_reason = "exact role match"

                # 2. EXACT MATCH su name (nuovo!)
                elif agent_name == target_role_lower:
                    score = 95
                    match_reason = "exact name match"

                # 3. NORMALIZED MATCH su role
                elif agent_role_normalized == target_role_normalized:
                    score = 90
                    match_reason = "normalized role match"

                # 4. NORMALIZED MATCH su name (nuovo!)
                elif agent_name.replace(" ", "") == target_role_normalized:
                    score = 85
                    match_reason = "normalized name match"

                # 5. CONTAINMENT MATCH - target contenuto in agent role
                elif target_role_lower in agent_role:
                    score = 80
                    match_reason = "target contained in agent role"

                # 6. CONTAINMENT MATCH - target contenuto in agent name (nuovo!)
                elif target_role_lower in agent_name:
                    score = 75
                    match_reason = "target contained in agent name"

                # 7. CONTAINMENT MATCH - agent role contenuto in target
                elif agent_role in target_role_lower:
                    score = 70
                    match_reason = "agent role contained in target"

                # 8. SEMANTIC WORD OVERLAP - migliore logica (migliorato!)
                elif target_role_words and (agent_role_words or agent_name_words):
                    # Controlla overlap con role words
                    role_common_words = agent_role_words.intersection(target_role_words)
                    # Controlla overlap con name words  
                    name_common_words = agent_name_words.intersection(target_role_words)

                    # Usa il migliore dei due
                    best_common_words = role_common_words if len(role_common_words) >= len(name_common_words) else name_common_words
                    best_source = "role" if len(role_common_words) >= len(name_common_words) else "name"

                    if best_common_words:
                        # Calcola overlap ratio più sofisticato
                        overlap_ratio = len(best_common_words) / len(target_role_words)
                        coverage_ratio = len(best_common_words) / max(len(agent_role_words) if best_source == "role" else len(agent_name_words), 1)

                        # Score basato su overlap quality
                        word_score = 30 + (overlap_ratio * 30) + (coverage_ratio * 10)

                        if word_score > score:
                            score = word_score
                            match_reason = f"word overlap in {best_source}: {', '.join(best_common_words)} (overlap: {overlap_ratio:.2f})"

                # 9. MANAGER ROLE MATCH
                elif is_target_manager and any(keyword in agent_role_normalized for keyword in 
                                             ["manager", "director", "lead", "coordinator", "pm"]):
                    score = 65
                    match_reason = "manager role match"

                # 10. PARTIAL KEYWORD MATCH - nuovo! Per catturare "Community" in "CommunitySpecialist"
                else:
                    partial_matches = []
                    for target_word in target_role_words:
                        if len(target_word) >= 4:  # Solo parole significative
                            # Cerca in agent role
                            for agent_word in agent_role_words:
                                if target_word in agent_word or agent_word in target_word:
                                    partial_matches.append((target_word, agent_word, "role"))
                            # Cerca in agent name
                            for agent_word in agent_name_words:
                                if target_word in agent_word or agent_word in target_word:
                                    partial_matches.append((target_word, agent_word, "name"))

                    if partial_matches:
                        # Score basato su qualità dei partial match
                        partial_score = len(partial_matches) * 15
                        if partial_score > score:
                            score = partial_score
                            matches_str = ", ".join([f"{pm[0]}→{pm[1]}({pm[2]})" for pm in partial_matches[:3]])
                            match_reason = f"partial keyword match: {matches_str}"

                # SENIORITY BOOST (solo per match con score > 0)
                if score > 0:
                    seniority_boost = {"expert": 5, "senior": 3, "junior": 1}
                    seniority = agent.get("seniority", "").lower()
                    score += seniority_boost.get(seniority, 0)

                # SOGLIA PIÙ ALTA per evitare match spuri
                if score >= 20:  # Aumentata da 4 a 20
                    candidates.append({
                        "agent": agent,
                        "score": round(score, 2),
                        "reason": match_reason
                    })

            # Sort by score
            candidates.sort(key=lambda x: x["score"], reverse=True)

            if candidates:
                best_match = candidates[0]["agent"]
                logger.info(f"✅ Agent match for '{role}': {best_match.get('name')} ({best_match.get('role')}) - Score: {candidates[0]['score']} ({candidates[0]['reason']})")
                return best_match

            # FALLBACK MIGLIORATI - Solo se veramente necessario e con logica più stretta

            # Fallback 1: Solo per ruoli manager specifici
            if is_target_manager:
                manager_agents = [agent for agent in agents_from_db 
                                if agent.get("status") == "active" 
                                and any(keyword in agent.get("role", "").lower() for keyword in ["manager", "coordinator", "director", "lead"])]
                if manager_agents:
                    # Preferisci "Project Manager" se disponibile
                    pm_agents = [a for a in manager_agents if "project" in a.get("role", "").lower()]
                    fallback_agent = pm_agents[0] if pm_agents else manager_agents[0]
                    logger.warning(f"⚠️ Manager fallback for '{role}': {fallback_agent.get('name')} ({fallback_agent.get('role')})")
                    return fallback_agent

            # Fallback 2: MOLTO restrittivo per specialist - solo se target contiene parole chiave specifiche
            if "specialist" in target_role_lower:
                # Estrai la specializzazione (es: "Community" da "CommunitySpecialist")
                specialization = target_role_lower.replace("specialist", "").strip()

                if specialization and len(specialization) >= 3:  # Deve avere una specializzazione valida
                    # Cerca specialist che hanno la specializzazione nel nome o ruolo
                    matching_specialists = []
                    for agent in agents_from_db:
                        if (agent.get("status") == "active" and 
                            "specialist" in agent.get("role", "").lower()):

                            agent_text = f"{agent.get('name', '')} {agent.get('role', '')}".lower()
                            if specialization in agent_text:
                                matching_specialists.append(agent)

                    if matching_specialists:
                        # Prendi il primo specialist che matcha la specializzazione
                        fallback_agent = matching_specialists[0]
                        logger.warning(f"⚠️ Specialist fallback for '{role}': {fallback_agent.get('name')} (specialization: {specialization})")
                        return fallback_agent

                    # Se ancora non trova nulla, LOG ERROR invece di fallback generico
                    logger.error(f"❌ NO SUITABLE AGENT for specialist role '{role}' with specialization '{specialization}'")
                    logger.error(f"Available agents: {[(a.get('name'), a.get('role')) for a in agents_from_db if a.get('status') == 'active']}")
                    return None  # Invece di fallback generico

            # Nessun fallback generico - se non trova match specifici, ritorna None
            logger.error(f"❌ NO AGENT MATCH for role '{role}' after all strategies")
            logger.error(f"Available active agents: {[(a.get('name'), a.get('role')) for a in agents_from_db if a.get('status') == 'active']}")

            # Suggerisci azioni correttive
            if agents_from_db:
                logger.error(f"💡 SUGGESTION: Check if '{role}' matches any of these agent names or roles exactly")

            return None

        except Exception as e:
            logger.error(f"Error finding agent by role: {e}", exc_info=True)
            return None

    async def _is_project_manager_task(self, task: Task, result: Dict[str, Any]) -> bool:
        """Determines if a task was completed by a Project Manager agent."""

        # Method 1 (PRIMARY): Check the actual agent role - most reliable
        if task.agent_id:
            try:
                from database import get_agent
                agent_data = await get_agent(str(task.agent_id))
                if agent_data:
                    role = agent_data.get('role', '').lower()
                    # Explicit PM role checks
                    pm_roles = ['project manager', 'coordinator', 'director', 'lead', 'pm']
                    if any(pm_role in role for pm_role in pm_roles):
                        logger.info(f"Task {task.id} identified as PM task by agent role (PRIMARY): {role}")
                        return True
                    else:
                        # If we have agent role data and it's NOT a PM role, log and return False immediately
                        logger.info(f"Task {task.id} is NOT a PM task - executed by role: {role}")
                        return False
            except Exception as e:
                logger.warning(f"Could not check agent role for task {task.id}: {e}")

        # Method 2 (SECONDARY): Check for PM-specific output structure
        if isinstance(result.get("detailed_results_json"), str) and result.get("detailed_results_json").strip():
            try:
                parsed_json = json.loads(result.get("detailed_results_json"))
                if isinstance(parsed_json, dict) and any(key in parsed_json for key in ["defined_sub_tasks", "sub_tasks", "subtasks"]):
                    logger.info(f"Task {task.id} identified as PM task by output structure (SECONDARY)")
                    return True
            except (json.JSONDecodeError, AttributeError, TypeError):
                # Ignore parsing errors - this just means it's not a properly structured PM output
                pass

        # Method 3 (TERTIARY): Very specific keyword matching - highly restricted
        task_name = task.name.lower() if task.name else ""

        # Very specific PM planning task indicators - only in task name, not description
        pm_planning_indicators = [
            "project setup", "strategic planning", "kick-off", "project assessment", 
            "phase planning", "team coordination"
        ]

        for indicator in pm_planning_indicators:
            if indicator in task_name:  # Only check name, not description
                logger.info(f"Task {task.id} identified as PM task by name indicator (TERTIARY): {indicator}")
                return True

        # Default assumption: Not a PM task
        logger.debug(f"Task {task.id} NOT identified as PM task after all checks")
        return False

    # ---------------------------------------------------------------------
    # Nuove funzioni per il fix anti-loop
    # ---------------------------------------------------------------------
    def _determine_project_phase(self, task_name: str, task_desc: str, completed_tasks_count: int) -> str:
        """MIGLIORATO: Determina la fase del progetto con logica più accurata"""
        task_lower = task_name.lower() + " " + task_desc.lower()

        # Pattern specifici per Fase 2 (IMPLEMENTATION) - AGGIUNTO
        if any(kw in task_lower for kw in 
            ["content strategy", "editorial calendar", "publishing schedule", "content templates", 
             "workflow", "guidelines", "framework", "calendar planning"]):
            return "IMPLEMENTATION"

        # Pattern di fase iniziale/analisi
        elif completed_tasks_count < 5 or any(kw in task_lower for kw in 
            ["analys", "research", "initial", "assess", "plan", "investigate", "explore", "discover", "competitor", "audience"]):
            return "ANALYSIS"

        # Pattern di fase finale
        elif any(kw in task_lower for kw in 
            ["finaliz", "review", "evaluat", "test", "valida", "conclude", "complete", "finish", "publish", "launch"]):
            return "FINALIZATION"

        # Default - progresso in base al conteggio dei task
        elif completed_tasks_count > 15:
            return "FINALIZATION"
        elif completed_tasks_count > 8:
            return "IMPLEMENTATION"
        else:
            return "ANALYSIS"

    async def _is_delegation_loop(self, source_agent_id: str, target_agent_id: str, workspace_id: str, parent_task_id: Optional[str] = None) -> bool:
        """Verifica se esiste già un ciclo di delegazione nella catena dei task"""
        if source_agent_id == target_agent_id:
            return True  # Non delegare a sé stessi
            
        # Se non c'è parent task, non c'è loop
        if not parent_task_id:
            return False
            
        # Ricostruisci la catena di delegazione
        delegation_chain = []
        current_task_id = parent_task_id
        max_depth = 0
        
        # Recupera task del workspace per costruire la genealogia
        all_tasks = await list_tasks(workspace_id)
        task_dict = {t.get("id"): t for t in all_tasks if t.get("id")}
        
        while current_task_id and max_depth < 10:  # Limite di sicurezza
            parent_task = task_dict.get(current_task_id)
            if not parent_task:
                break
                
            delegator_id = parent_task.get("agent_id")
            if delegator_id:
                delegation_chain.append(delegator_id)
                
            # Passa al parent
            current_task_id = parent_task.get("parent_task_id")
            max_depth += 1
        
        # Verifica se il target ha già delegato al source
        if target_agent_id in delegation_chain:
            logger.warning(f"Detected delegation loop: {source_agent_id} -> {target_agent_id} (chain: {delegation_chain})")
            return True
            
        # Verifica profondità massima delegazione
        if len(delegation_chain) >= 3:  # Limite a 3 livelli di delegazione
            logger.warning(f"Max delegation depth reached: {len(delegation_chain)} > 3")
            return True
            
        return False

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calcola la similarità tra due testi"""
        if not text1 or not text2:
            return 0.0
            
        # Normalizza i testi
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
            
        # Calcola coefficiente Jaccard
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0

    async def _detect_duplicate_task(self, new_task_name: str, new_task_description: str, workspace_id: str) -> Optional[Dict]:
        """Rileva se un task simile è già stato creato"""
        existing_tasks = await list_tasks(workspace_id)
        
        # Normalizza il testo per confronto
        new_name_normalized = new_task_name.lower()
        new_desc_normalized = new_task_description.lower()
        combined_new = f"{new_name_normalized} {new_desc_normalized}"
        
        for task in existing_tasks:
            if task.get("status") in ["pending", "in_progress"]:
                existing_name = task.get("name", "").lower()
                existing_desc = task.get("description", "").lower()
                combined_existing = f"{existing_name} {existing_desc}"
                
                # Calcola similarità
                similarity = self._calculate_text_similarity(combined_new, combined_existing)
                
                if similarity > 0.75:  # 75% di somiglianza
                    logger.warning(f"Detected potential duplicate task: {similarity*100:.1f}% similarity")
                    return task
        
        return None

    async def handle_failed_task(self, task_id: str, error_details: str, workspace_id: str) -> Optional[str]:
        """Gestisce un task fallito decidendo se riassegnarlo o escalarlo"""
        from database import get_task, update_task_status, list_agents, create_task
        
        # Recupera il task
        tasks = await list_tasks(workspace_id)
        task = next((t for t in tasks if t.get("id") == task_id), None)
        
        if not task:
            logger.error(f"Cannot handle failed task {task_id} - not found")
            return None
        
        # Incrementa contatore fallimenti
        context_data = task.get("context_data", {}) or {}
        failure_count = context_data.get("failure_count", 0) + 1
        context_data["failure_count"] = failure_count
        
        # Se il task ha fallito troppe volte, escalation al PM
        if failure_count >= 3:
            # Trova il PM
            agents = await list_agents(workspace_id)
            pm_agent = next((a for a in agents if "project manager" in (a.get("role") or "").lower()), None)
            
            if pm_agent:
                # Crea task di intervento per il PM
                intervention_task = await create_task(
                    workspace_id=workspace_id,
                    agent_id=pm_agent["id"],
                    name=f"INTERVENTION: Handle Failed Task - {task.get('name')}",
                    description=(
                        f"The following task has failed {failure_count} times and needs intervention:\n\n"
                        f"Task: {task.get('name')}\n"
                        f"Error: {error_details}\n\n"
                        "Please decide whether to:\n"
                        "1. Modify and retry the task\n"
                        "2. Skip this task and proceed with alternatives\n"
                        "3. Update the project plan accordingly"
                    ),
                    status="pending",
                    priority="high",
                    # TRACKING AUTOMATICO
                    created_by_task_id=task_id,  # Creato a causa del fallimento di questo task
                    creation_type="failure_intervention",  # Intervento per fallimento

                    # CONTEXT DATA SPECIFICO
                    context_data={
                        "intervention_type": "failed_task",
                        "original_task_id": task_id,
                        "original_task_name": task.get('name'),
                        "failure_count": failure_count,
                        "error_details": error_details,
                        "requires_human_attention": True,
                        "intervention_timestamp": datetime.now().isoformat(),
                        "auto_escalated": True
                    }
                )
                return intervention_task["id"]
        else:
            # Aggiorna il task con il conteggio fallimenti e riprova
            await update_task_status(
                task_id=task_id,
                status="pending",  # Rimetti in pending per riprovare
                result_payload={
                    "failure_count": failure_count,
                    "last_error": error_details,
                    "retry_scheduled": True
                }
            )
            return task_id
        
        return None
    
    async def evaluate_project_phase_transition(self, workspace_id: str) -> str:
        """Determina se il progetto dovrebbe passare alla fase successiva"""
        tasks = await list_tasks(workspace_id)
        
        # Conta task per fase
        phase_counts = {
            "ANALYSIS": 0,
            "IMPLEMENTATION": 0,
            "FINALIZATION": 0
        }
        
        completed_phase_counts = {
            "ANALYSIS": 0,
            "IMPLEMENTATION": 0,
            "FINALIZATION": 0
        }
        
        # Conteggio task per fase
        for task in tasks:
            context_data = task.get("context_data", {}) or {}
            phase = context_data.get("project_phase", "ANALYSIS")
            if phase in phase_counts:
                phase_counts[phase] += 1
                
                if task.get("status") == "completed":
                    completed_phase_counts[phase] += 1
        
        # Determina la fase attuale
        current_phase = "ANALYSIS"
        if completed_phase_counts["ANALYSIS"] > 0 and phase_counts["IMPLEMENTATION"] > 0:
            current_phase = "IMPLEMENTATION"
        if completed_phase_counts["IMPLEMENTATION"] > 0 and phase_counts["FINALIZATION"] > 0:
            current_phase = "FINALIZATION"
        
        # Calcola il completamento della fase
        phase_completion = {
            phase: completed_phase_counts[phase] / phase_counts[phase] if phase_counts[phase] > 0 else 0
            for phase in phase_counts.keys()
        }
        
        # Regole di transizione
        if current_phase == "ANALYSIS" and phase_completion["ANALYSIS"] > 0.8:
            logger.info(f"Project {workspace_id} ready to transition from ANALYSIS to IMPLEMENTATION phase")
            return "IMPLEMENTATION"
        elif current_phase == "IMPLEMENTATION" and phase_completion["IMPLEMENTATION"] > 0.7:
            logger.info(f"Project {workspace_id} ready to transition from IMPLEMENTATION to FINALIZATION phase")
            return "FINALIZATION"
        elif current_phase == "FINALIZATION" and phase_completion["FINALIZATION"] > 0.9:
            logger.info(f"Project {workspace_id} ready to be marked as COMPLETED")
            return "COMPLETED"
        
        return current_phase

    async def create_periodic_assessment_task(self, workspace_id: str) -> Optional[str]:
        """Crea un task di valutazione periodica per il PM"""
        from database import list_agents, list_tasks, create_task
        
        # Trova il Project Manager
        agents = await list_agents(workspace_id)
        pm_agent = next((a for a in agents if "project manager" in (a.get("role") or "").lower()), None)
        
        if not pm_agent:
            logger.warning(f"No PM found for workspace {workspace_id}")
            return None
        
        # Crea un task di valutazione ogni N task completati
        tasks = await list_tasks(workspace_id)
        completed_count = len([t for t in tasks if t.get("status") == "completed"])
        
        if completed_count > 0 and completed_count % 5 == 0:  # Ogni 5 task completati
            # Verifica la fase attuale
            current_phase = await self.evaluate_project_phase_transition(workspace_id)
            
            assessment_task = await create_task(
                workspace_id=workspace_id,
                agent_id=pm_agent["id"],
                name=f"Project Progress Assessment #{completed_count // 5}",
                description=(
                    f"Review the current project status. {completed_count} tasks have been completed.\n\n"
                    f"Current project phase: {current_phase}\n\n"
                    "1. Evaluate progress toward overall goal\n"
                    "2. Identify any bottlenecks or issues\n"
                    "3. Determine if project is ready to move to next phase\n"
                    "4. Create appropriate follow-up tasks based on current project phase"
                ),
                status="pending",
                priority="high",
                
                # TRACKING AUTOMATICO
                creation_type="periodic_assessment",  # Assessment periodico automatico

                # CONTEXT DATA SPECIFICO
                context_data={
                    "assessment_type": "periodic",
                    "assessment_number": completed_count // 5,
                    "completed_tasks_count": completed_count,
                    "current_phase": current_phase,
                    "auto_generated": True,
                    "assessment_trigger": f"every_5_completions",
                    "assessment_timestamp": datetime.now().isoformat(),
                    "is_milestone_check": True
                }
            )
            
            if assessment_task and assessment_task.get("id"):
                return assessment_task["id"]
        
        return None

    async def check_project_completion_criteria(self, workspace_id: str) -> bool:
        """Verifica criteri multipli per stabilire se un progetto è completato"""
        
        tasks = await list_tasks(workspace_id)
        completed_tasks = [t for t in tasks if t.get("status") == "completed"]
        
        if not tasks:
            return False
        
        # Criterio 1: Percentuale di completamento
        completion_ratio = len(completed_tasks) / len(tasks) if tasks else 0
        
        # Criterio 2: Completamento delle fasi
        phases_completed = {
            "ANALYSIS": False,
            "IMPLEMENTATION": False,
            "FINALIZATION": False
        }
        
        for task in completed_tasks:
            context_data = task.get("context_data", {}) or {}
            phase = context_data.get("project_phase")
            if phase in phases_completed:
                phases_completed[phase] = True
        
        # Criterio 3: Presenza di deliverable finali
        has_final_deliverables = False
        for task in completed_tasks:
            if any(keyword in (task.get("name", "") or "").lower() for keyword in 
                  ["final", "deliverable", "complete", "finished"]):
                has_final_deliverables = True
                break
        
        # Decisione di completamento basata su tutti i criteri
        if completion_ratio > 0.85 and phases_completed["IMPLEMENTATION"] and has_final_deliverables:
            # PROGETTO COMPLETO
            return True
        
        # Se la fase di IMPLEMENTATION è completa ma mancano deliverable finali
        if phases_completed["IMPLEMENTATION"] and not has_final_deliverables:
            # Crea task per generare il deliverable finale
            await self.create_final_deliverable_task(workspace_id)
        
        return False

    async def create_final_deliverable_task(self, workspace_id: str) -> Optional[str]:
        """Crea un task per il deliverable finale"""
        from database import list_agents, create_task, get_workspace
        
        # Ottieni informazioni workspace
        workspace = await get_workspace(workspace_id)
        workspace_goal = workspace.get("goal", "Complete the project") if workspace else "Complete the project"
        
        # Trova il PM
        agents = await list_agents(workspace_id)
        pm_agent = next((a for a in agents if "project manager" in (a.get("role") or "").lower()), None)
        
        if not pm_agent:
            logger.warning(f"No PM found for workspace {workspace_id}")
            return None
        
        # Crea task finale
        final_task = await create_task(
            workspace_id=workspace_id,
            agent_id=pm_agent["id"],
            name="FINAL: Project Deliverable Creation",
            description=(
                "Create the final project deliverable based on all completed work.\n\n"
                f"PROJECT GOAL: {workspace_goal}\n\n"
                "1. Review all completed tasks and collect key outputs\n"
                "2. Synthesize findings into a cohesive final deliverable\n"
                "3. Include executive summary, key findings, and recommendations\n"
                "4. Ensure the deliverable completely addresses the original project goal\n\n"
                "This is the final task for this project. Upon completion, the project will be marked as complete."
            ),
            status="pending",
            priority="high",
            # TRACKING AUTOMATICO
            creation_type="final_deliverable",  # Task finale del progetto

            # CONTEXT DATA SPECIFICO
            context_data={
                "task_type": "final_deliverable",
                "project_phase": "FINALIZATION",
                "auto_generated": True,
                "is_final_task": True,
                "project_goal": workspace_goal,
                "deliverable_creation_timestamp": datetime.now().isoformat(),
                "triggers_project_completion": True,
                "requires_synthesis": True
            }
        )
        
        if final_task and final_task.get("id"):
            return final_task["id"]
        
        return None
    
    async def check_phase_completion_and_trigger_pm(self, workspace_id: str) -> Optional[str]:
        """Verifica se una fase è completata e crea task per il PM per la fase successiva"""

        try:
            tasks = await list_tasks(workspace_id)
            agents = await list_agents(workspace_id)

            # Trova il PM
            pm_agent = next((a for a in agents if "project manager" in (a.get("role") or "").lower()), None)
            if not pm_agent:
                logger.warning(f"No PM found in workspace {workspace_id}")
                return None

            # Analizza task per fase basandosi sui nomi e context_data
            analysis_tasks = []
            implementation_tasks = []

            for task in tasks:
                if task.get("status") == "completed":
                    # Identifica task di analisi
                    task_name = (task.get("name") or "").lower()
                    context_data = task.get("context_data", {}) or {}
                    project_phase = context_data.get("project_phase", "")

                    # Task di analisi: per nome o fase
                    if (any(keyword in task_name for keyword in ["analysis", "profiling", "audit", "research"]) or
                        project_phase == "ANALYSIS"):
                        analysis_tasks.append(task)

                    # Task di implementazione: per fase
                    elif project_phase == "IMPLEMENTATION":
                        implementation_tasks.append(task)
                        
                    if ("phase 2 planning" in task_name and 
                        task.get("agent_id") == pm_agent["id"]):
                        phase_2_planning_completed = True

            logger.info(f"Phase check - Analysis tasks: {len(analysis_tasks)}, Implementation tasks: {len(implementation_tasks)}")

            # Verifica se la fase ANALYSIS è completata (almeno 3 task) e IMPLEMENTATION non è iniziata
            if len(analysis_tasks) >= 3 and len(implementation_tasks) == 0:
                logger.info(f"Phase 1 (ANALYSIS) completed with {len(analysis_tasks)} tasks. Triggering Phase 2 planning.")

                # Crea riassunto dei risultati di analisi
                analysis_summary = self._summarize_completed_analysis(analysis_tasks)

                # Crea task di pianificazione per la fase successiva
                next_phase_task = await create_task(
                    workspace_id=workspace_id,
                    agent_id=pm_agent["id"],
                    name="Phase 2 Planning: Content Strategy & Editorial Plan Development",
                    description=f"""Based on the completed Phase 1 analysis, develop the comprehensive content strategy and editorial plan.

    COMPLETED PHASE 1 ANALYSIS RESULTS:
    {analysis_summary}

    YOUR TASKS FOR PHASE 2:
    1. **Content Strategy Framework**: Define content pillars, themes, and messaging strategy based on analysis
    2. **Editorial Calendar Planning**: Create a detailed content calendar structure 
    3. **Content Creation Workflow**: Define specific content creation tasks for ContentSpecialist
    4. **Performance Metrics**: Define KPIs and measurement framework

    CRITICAL OUTPUT REQUIREMENTS:
    - Your detailed_results_json MUST contain "defined_sub_tasks" array
    - Create specific, actionable sub-tasks for ContentSpecialist
    - Focus on deliverables: Editorial Calendar, Content Templates, Publishing Schedule
    - Each sub-task must have: name, description, target_agent_role, priority

    Expected sub-tasks examples:
    - "Create Monthly Editorial Calendar" → ContentSpecialist  
    - "Develop Content Templates & Guidelines" → ContentSpecialist
    - "Design Publishing Schedule & Workflow" → ContentSpecialist
    """,
                    status="pending",
                    priority="high",
                    creation_type="phase_transition",
                    context_data={
                        "project_phase": "IMPLEMENTATION",
                        "phase_transition": "ANALYSIS_TO_IMPLEMENTATION", 
                        "auto_generated": True,
                        "triggers_next_phase": True,
                        "previous_phase_tasks": [t["id"] for t in analysis_tasks],
                        "phase_trigger_timestamp": datetime.now().isoformat()
                    }
                )

                if next_phase_task and next_phase_task.get("id"):
                    logger.info(f"✅ Created Phase 2 planning task {next_phase_task['id']} for PM {pm_agent['name']}")
                    return next_phase_task["id"]
                else:
                    logger.error("❌ Failed to create Phase 2 planning task")

            else:
                logger.debug(f"Phase transition conditions not met: Analysis={len(analysis_tasks)}, Implementation={len(implementation_tasks)}")

            return None

        except Exception as e:
            logger.error(f"Error checking phase completion: {e}", exc_info=True)
            return None

    def _summarize_completed_analysis(self, completed_tasks: List[Dict]) -> str:
        """Crea un riassunto dei task di analisi completati"""
        if not completed_tasks:
            return "No analysis tasks completed."

        summary_parts = []

        for task in completed_tasks:
            task_name = task.get("name", "Unknown Task")
            result = task.get("result", {})

            # Estrai summary dal result
            summary = result.get("summary", "")
            detailed_json = result.get("detailed_results_json", "")

            # Usa summary se disponibile, altrimenti detailed_results_json
            content = summary if summary else detailed_json

            if content:
                # Tronca a 150 caratteri per mantenere il riassunto gestibile
                truncated = content[:150] + "..." if len(content) > 150 else content
                summary_parts.append(f"• {task_name}: {truncated}")
            else:
                summary_parts.append(f"• {task_name}: Completed successfully")

        return "\n".join(summary_parts)
    
    # ---------------------------------------------------------------------
    # Ultra-conservative analysis filters
    # ---------------------------------------------------------------------
    def _should_analyze_task_ultra_conservative(self, task: Task, result: Dict[str, Any]) -> bool:
        """Ultra-conservative filter for task analysis"""

        # ONLY completed tasks
        if result.get("status") != "completed":
            return False

        # REJECT if any completion indicators in name
        task_name_lower = task.name.lower() if task.name else ""
        completion_words = ["handoff", "completed", "done", "finished", "delivered", "final"]

        if any(word in task_name_lower for word in completion_words):
            return False

        # REJECT if output suggests completion
        output_parts = []
        if result.get("summary"):
            output_parts.append(str(result.get("summary", "")))
        if result.get("detailed_results_json"):
            if isinstance(result.get("detailed_results_json"), str):
                output_parts.append(result.get("detailed_results_json"))
            else:
                output_parts.append(str(result.get("detailed_results_json")))

        output = " ".join(output_parts)
        output_lower = output.lower()

        completion_phrases = ["task complete", "objective achieved", "deliverable ready"]
        if any(phrase in output_lower for phrase in completion_phrases):
            return False

        # REJECT if output too long (probably comprehensive)
        if len(output) > 1500:
            return False

        # NUOVO: Permetti analisi per task che completano una fase
        phase_completion_indicators = [
            "analysis", "profiling", "audit", "research", 
            "assessment", "evaluation", "investigation"
        ]

        # Se il task contiene indicatori di completamento di fase, permettilo
        if any(indicator in task_name_lower for indicator in phase_completion_indicators):
            logger.debug(f"Task {task.id} allowed for phase completion analysis")
            return True

        # ALLENTATO: Pattern permessi più ampi
        allowed_patterns = [
            "initial research", "preliminary analysis", "feasibility assessment",
            "requirement gathering",
            # AGGIUNTI per permettere progressione:
            "analysis", "profiling", "audit", "research", "assessment"
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

        delegation_depth = 0
        if hasattr(task, 'context_data') and task.context_data:
            if isinstance(task.context_data, dict):
                delegation_depth = task.context_data.get('delegation_depth', 0)

        if delegation_depth >= 2:  # Limite rigido a 2 livelli di delega
            logger.warning(f"Handoff bloccato per task {task.id}: max delegation depth ({delegation_depth})")
            await self._log_completion_analysis(
                task, analysis.__dict__(), "handoff_blocked_max_depth", 
                f"Delegation depth: {delegation_depth}"
            )
            return
        
        if not analysis.suggested_handoffs:
            return
        
        try:
            # Set cache immediately to prevent duplicates
            cache_key = f"{workspace_id}_handoff"
            self.handoff_cache[cache_key] = datetime.now()
            
            # Create minimal follow-up task
            description = f"""[AUTOMATED FOLLOW-UP] [Delegation Depth: {delegation_depth + 1}] (Generated from: {task.name})

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
            context_data = {
                "created_by_task_id": str(task.id),
                "created_by_agent_id": str(task.agent_id) if task.agent_id else None,
                "creation_method": "automated_handoff",
                "delegation_depth": delegation_depth + 1,
                "created_at": datetime.now().isoformat()
            }
            
            # Create with PENDING status for PM to review
            new_task = await create_task(
                workspace_id=workspace_id,
                name=f"AUTO: Follow-up for {task.name[:30]}...",
                description=description,
                status=TaskStatus.PENDING.value,
                parent_task_id=str(task.id),
                context_data=context_data

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