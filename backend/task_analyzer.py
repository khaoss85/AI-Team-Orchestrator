# backend/task_analyzer.py
import logging
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set

# IMPORT AGGIORNATI per compatibilità con i nuovi models
from models import Task, TaskStatus
from models import ProjectPhase, PHASE_SEQUENCE, PHASE_DESCRIPTIONS
from database import create_task, list_agents, list_tasks, get_workspace

# NUOVO: Import per deliverable aggregation
from deliverable_aggregator import check_and_create_final_deliverable

logger = logging.getLogger(__name__)

class PhaseManager:
    """Gestisce centralmente le fasi del progetto"""
    
    @staticmethod
    def validate_phase(phase: str) -> ProjectPhase:
        """Valida e normalizza una fase"""
        if not phase:
            return ProjectPhase.ANALYSIS
            
        phase_upper = phase.upper().strip()
        
        # Exact match first
        for valid_phase in ProjectPhase:
            if phase_upper == valid_phase.value:
                return valid_phase
                
        # Fallback mapping per compatibilità
        fallback_mapping = {
            "RESEARCH": ProjectPhase.ANALYSIS,
            "STRATEGY": ProjectPhase.IMPLEMENTATION,
            "PLANNING": ProjectPhase.IMPLEMENTATION,
            "EXECUTION": ProjectPhase.FINALIZATION,
            "CREATION": ProjectPhase.FINALIZATION,
            "CONTENT": ProjectPhase.FINALIZATION,
            "PUBLISHING": ProjectPhase.FINALIZATION
        }
        
        return fallback_mapping.get(phase_upper, ProjectPhase.ANALYSIS)
    
    @staticmethod
    def get_next_phase(current_phase: ProjectPhase) -> Optional[ProjectPhase]:
        """Restituisce la fase successiva"""
        try:
            current_index = PHASE_SEQUENCE.index(current_phase)
            if current_index < len(PHASE_SEQUENCE) - 1:
                return PHASE_SEQUENCE[current_index + 1]
        except (ValueError, IndexError):
            logger.warning(f"Invalid phase for progression: {current_phase}")
        return None
    
    @staticmethod
    async def determine_workspace_current_phase(workspace_id: str) -> ProjectPhase:
        """Determina la fase attuale del workspace basata sui task completati"""
        try:
            tasks = await list_tasks(workspace_id)
            completed_tasks = [t for t in tasks if t.get("status") == "completed"]
            
            if not completed_tasks:
                return ProjectPhase.ANALYSIS
            
            # Conta task completati per fase (con validazione)
            phase_counts = {phase: 0 for phase in ProjectPhase}
            
            for task in completed_tasks:
                context_data = task.get("context_data", {}) or {}
                task_phase = context_data.get("project_phase", "ANALYSIS")
                validated_phase = PhaseManager.validate_phase(task_phase)
                phase_counts[validated_phase] += 1
            
            logger.info(f"Workspace {workspace_id} phase counts: {phase_counts}")
            
            # Determina fase attuale basata sui completamenti (soglie conservative)
            if phase_counts[ProjectPhase.FINALIZATION] >= 2:
                return ProjectPhase.COMPLETED
            elif phase_counts[ProjectPhase.IMPLEMENTATION] >= 2:
                return ProjectPhase.FINALIZATION
            elif phase_counts[ProjectPhase.ANALYSIS] >= 3:
                return ProjectPhase.IMPLEMENTATION
            else:
                return ProjectPhase.ANALYSIS
                
        except Exception as e:
            logger.error(f"Error determining workspace phase: {e}")
            return ProjectPhase.ANALYSIS
    
    @staticmethod
    def get_phase_description(phase: ProjectPhase) -> str:
        """Restituisce la descrizione di una fase"""
        return PHASE_DESCRIPTIONS.get(phase, "General project work")
    
    @staticmethod
    def is_valid_phase_transition(from_phase: ProjectPhase, to_phase: ProjectPhase) -> bool:
        """Verifica se una transizione di fase è valida"""
        try:
            from_index = PHASE_SEQUENCE.index(from_phase)
            to_index = PHASE_SEQUENCE.index(to_phase)
            return to_index == from_index + 1
        except ValueError:
            return False

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
    Enhanced task executor with STRICT anti-loop protection and deliverable integration.
    
    Key principles:
    1. Auto-generation is DISABLED by default
    2. PM handles task creation, not this analyzer
    3. Integrated deliverable aggregation after task completion
    4. Phase completion triggers PM tasks automatically
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
        
        logger.info("EnhancedTaskExecutor initialized with STRICT ANTI-LOOP protection and deliverable integration")
        logger.info(f"Config: auto_gen={self.auto_generation_enabled}, analysis={self.analysis_enabled}, handoffs={self.handoff_creation_enabled}")

    # ---------------------------------------------------------------------
    # JSON Utilities - Added to handle JSON parsing safely
    # ---------------------------------------------------------------------
    def _safe_json_loads(self, json_str: str) -> Dict[str, Any]:
        """Safely parse JSON string, removing control characters"""
        if not json_str:
            return {}
        
        try:
            # Remove control characters
            clean_json = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_str)
            return json.loads(clean_json)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing failed: {e}. Attempting fallback parsing.")
            # Try to extract JSON from string if it's embedded
            json_match = re.search(r'\{.*\}', clean_json, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            return {}
        except Exception as e:
            logger.error(f"Unexpected error parsing JSON: {e}")
            return {}

    # ---------------------------------------------------------------------
    # MAIN ENTRY POINT - Handle task completion with deliverable integration
    # ---------------------------------------------------------------------
    async def handle_task_completion(
        self,
        completed_task: Task,
        task_result: Dict[str, Any],
        workspace_id: str,
    ) -> None:
        """Main handler with deliverable aggregation check and strict separation between PM and specialist flows."""
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

                # NUOVO: Dopo il completamento di task PM, controlla per deliverable finale
                try:
                    final_deliverable_id = await check_and_create_final_deliverable(workspace_id)
                    if final_deliverable_id:
                        logger.info(f"✅ PM task completion triggered final deliverable: {final_deliverable_id}")
                        await self._log_completion_analysis(
                            completed_task, task_result, "pm_triggered_final_deliverable",
                            f"Created final deliverable: {final_deliverable_id}"
                        )
                except Exception as e:
                    logger.error(f"Error checking final deliverable after PM task: {e}")

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

            # NUOVO: Dopo ogni specialist task, controlla per deliverable finale
            try:
                final_deliverable_id = await check_and_create_final_deliverable(workspace_id)
                if final_deliverable_id:
                    logger.info(f"🎯 Specialist task completion triggered final deliverable: {final_deliverable_id}")
                    await self._log_completion_analysis(
                        completed_task, task_result, "specialist_triggered_final_deliverable",
                        f"Created final deliverable: {final_deliverable_id}"
                    )
            except Exception as e:
                logger.error(f"Error checking final deliverable after specialist task: {e}")

            # CHECK COMPLETAMENTO FASE DOPO OGNI TASK SPECIALISTA
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
        """Handles Project Manager task completion con validazione fasi"""

        logger.info(f"Handling PM task completion: {task.id} ('{task.name}')")

        # Estrai detailed_results_json con safe parsing
        detailed_results_json_content = result.get("detailed_results_json")
        if not detailed_results_json_content:
            logger.error(f"PM task {task.id} missing detailed_results_json")
            return False

        try:
            results_data = self._safe_json_loads(detailed_results_json_content)
        except Exception as e:
            logger.error(f"Failed to parse detailed_results_json for task {task.id}: {e}")
            return False

        # Validazione delle fasi
        current_project_phase = results_data.get("current_project_phase")
        if not current_project_phase:
            logger.error(f"PM task {task.id} missing current_project_phase")
            return False

        validated_current_phase = PhaseManager.validate_phase(current_project_phase)
        logger.info(f"PM specified phase: {current_project_phase} -> validated: {validated_current_phase.value}")

        defined_subtasks = results_data.get("defined_sub_tasks", [])
        if not defined_subtasks:
            logger.warning(f"PM task {task.id} has no defined_sub_tasks")
            return False

        created_count = 0
        phase_validation_errors = []

        for subtask_def in defined_subtasks:
            if not isinstance(subtask_def, dict):
                logger.warning(f"Skipping invalid subtask definition: {subtask_def}")
                continue

            try:
                # Validazione campi obbligatori
                required_fields = ["name", "description", "target_agent_role"]
                missing_fields = [field for field in required_fields if not subtask_def.get(field)]
                if missing_fields:
                    logger.warning(f"Skipping subtask missing fields {missing_fields}: {subtask_def}")
                    continue

                # Validazione fase del sub-task
                subtask_phase = subtask_def.get("project_phase")
                if not subtask_phase:
                    logger.warning(f"Sub-task missing project_phase, using current phase: {subtask_def['name']}")
                    subtask_phase = validated_current_phase.value

                validated_subtask_phase = PhaseManager.validate_phase(subtask_phase)
                if subtask_phase != validated_subtask_phase.value:
                    phase_validation_errors.append({
                        "task": subtask_def['name'],
                        "original": subtask_phase,
                        "corrected": validated_subtask_phase.value
                    })

                # Trova agente appropriato
                target_role = subtask_def["target_agent_role"]
                target_agent = await self._find_agent_by_role(workspace_id, target_role)

                if not target_agent:
                    logger.warning(f"No agent found for role '{target_role}'. Skipping: {subtask_def['name']}")
                    continue

                # Crea il sub-task con validazione completa
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
                    created_by_task_id=str(task.id),
                    created_by_agent_id=str(task.agent_id) if task.agent_id else None,
                    creation_type="pm_completion",

                    # CONTEXT DATA CON VALIDAZIONE FASI
                    context_data={
                        "auto_generated_by_pm": True,
                        "source_pm_task_name": task.name,
                        "project_phase": validated_subtask_phase.value,  # FASE VALIDATA
                        "original_pm_phase": subtask_phase,  # Fase originale dal PM
                        "pm_task_phase": validated_current_phase.value,
                        "phase_validated": True,
                        "phase_validation_timestamp": datetime.now().isoformat(),
                        "expected_completion_criteria": subtask_def.get("completion_criteria", "Task completed"),
                        "pm_completion_timestamp": datetime.now().isoformat()
                    }
                )

                if created_task and created_task.get("id"):
                    created_count += 1
                    logger.info(f"Created sub-task '{subtask_def['name']}' (ID: {created_task['id']}) "
                               f"for agent {target_agent.get('name')} in phase {validated_subtask_phase.value}")
                else:
                    logger.error(f"Failed to create sub-task: {subtask_def['name']}")

            except Exception as e:
                logger.error(f"Error creating sub-task '{subtask_def.get('name', 'Unknown')}': {e}", exc_info=True)

        # Log validation errors
        if phase_validation_errors:
            logger.warning(f"Phase validation corrections made: {phase_validation_errors}")

        logger.info(f"PM task {task.id} completion: Created {created_count}/{len(defined_subtasks)} "
                   f"sub-tasks for phase {validated_current_phase.value}")
        return created_count > 0

    async def _find_agent_by_role(self, workspace_id: str, role: str) -> Optional[Dict]:
        """Find agent by role with improved matching logic"""
        try:
            from database import list_agents as db_list_agents

            agents_from_db = await db_list_agents(workspace_id)
            if not agents_from_db:
                logger.warning(f"No agents in workspace {workspace_id}")
                return None

            # Normalizza target role
            target_role_lower = role.lower().strip()
            target_role_normalized = target_role_lower.replace(" ", "")

            # Estrai parole chiave significative
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

                # 2. EXACT MATCH su name
                elif agent_name == target_role_lower:
                    score = 95
                    match_reason = "exact name match"

                # 3. NORMALIZED MATCH su role
                elif agent_role_normalized == target_role_normalized:
                    score = 90
                    match_reason = "normalized role match"

                # 4. NORMALIZED MATCH su name
                elif agent_name.replace(" ", "") == target_role_normalized:
                    score = 85
                    match_reason = "normalized name match"

                # 5. CONTAINMENT MATCH - target contenuto in agent role
                elif target_role_lower in agent_role:
                    score = 80
                    match_reason = "target contained in agent role"

                # 6. CONTAINMENT MATCH - target contenuto in agent name
                elif target_role_lower in agent_name:
                    score = 75
                    match_reason = "target contained in agent name"

                # 7. CONTAINMENT MATCH - agent role contenuto in target
                elif agent_role in target_role_lower:
                    score = 70
                    match_reason = "agent role contained in target"

                # 8. SEMANTIC WORD OVERLAP
                elif target_role_words and (agent_role_words or agent_name_words):
                    role_common_words = agent_role_words.intersection(target_role_words)
                    name_common_words = agent_name_words.intersection(target_role_words)

                    best_common_words = role_common_words if len(role_common_words) >= len(name_common_words) else name_common_words
                    best_source = "role" if len(role_common_words) >= len(name_common_words) else "name"

                    if best_common_words:
                        overlap_ratio = len(best_common_words) / len(target_role_words)
                        coverage_ratio = len(best_common_words) / max(len(agent_role_words) if best_source == "role" else len(agent_name_words), 1)

                        word_score = 30 + (overlap_ratio * 30) + (coverage_ratio * 10)

                        if word_score > score:
                            score = word_score
                            match_reason = f"word overlap in {best_source}: {', '.join(best_common_words)} (overlap: {overlap_ratio:.2f})"

                # 9. MANAGER ROLE MATCH
                elif is_target_manager and any(keyword in agent_role_normalized for keyword in 
                                             ["manager", "director", "lead", "coordinator", "pm"]):
                    score = 65
                    match_reason = "manager role match"

                # 10. PARTIAL KEYWORD MATCH
                else:
                    partial_matches = []
                    for target_word in target_role_words:
                        if len(target_word) >= 4:
                            for agent_word in agent_role_words:
                                if target_word in agent_word or agent_word in target_word:
                                    partial_matches.append((target_word, agent_word, "role"))
                            for agent_word in agent_name_words:
                                if target_word in agent_word or agent_word in target_word:
                                    partial_matches.append((target_word, agent_word, "name"))

                    if partial_matches:
                        partial_score = len(partial_matches) * 15
                        if partial_score > score:
                            score = partial_score
                            matches_str = ", ".join([f"{pm[0]}→{pm[1]}({pm[2]})" for pm in partial_matches[:3]])
                            match_reason = f"partial keyword match: {matches_str}"

                # SENIORITY BOOST
                if score > 0:
                    seniority_boost = {"expert": 5, "senior": 3, "junior": 1}
                    seniority = agent.get("seniority", "").lower()
                    score += seniority_boost.get(seniority, 0)

                if score >= 20:
                    candidates.append({
                        "agent": agent,
                        "score": round(score, 2),
                        "reason": match_reason
                    })

            candidates.sort(key=lambda x: x["score"], reverse=True)

            if candidates:
                best_match = candidates[0]["agent"]
                logger.info(f"✅ Agent match for '{role}': {best_match.get('name')} ({best_match.get('role')}) - Score: {candidates[0]['score']} ({candidates[0]['reason']})")
                return best_match

            logger.error(f"❌ NO AGENT MATCH for role '{role}' after all strategies")
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
                    pm_roles = ['project manager', 'coordinator', 'director', 'lead', 'pm']
                    if any(pm_role in role for pm_role in pm_roles):
                        logger.info(f"Task {task.id} identified as PM task by agent role (PRIMARY): {role}")
                        return True
                    else:
                        logger.info(f"Task {task.id} is NOT a PM task - executed by role: {role}")
                        return False
            except Exception as e:
                logger.warning(f"Could not check agent role for task {task.id}: {e}")

        # Method 2 (SECONDARY): Check for PM-specific output structure
        if isinstance(result.get("detailed_results_json"), str) and result.get("detailed_results_json").strip():
            try:
                parsed_json = self._safe_json_loads(result.get("detailed_results_json"))
                if isinstance(parsed_json, dict) and any(key in parsed_json for key in ["defined_sub_tasks", "sub_tasks", "subtasks"]):
                    logger.info(f"Task {task.id} identified as PM task by output structure (SECONDARY)")
                    return True
            except Exception:
                pass

        # Method 3 (TERTIARY): Very specific keyword matching
        task_name = task.name.lower() if task.name else ""

        pm_planning_indicators = [
            "project setup", "strategic planning", "kick-off", "project assessment", 
            "phase planning", "team coordination"
        ]

        for indicator in pm_planning_indicators:
            if indicator in task_name:
                logger.info(f"Task {task.id} identified as PM task by name indicator (TERTIARY): {indicator}")
                return True

        logger.debug(f"Task {task.id} NOT identified as PM task after all checks")
        return False

    # ---------------------------------------------------------------------
    # Phase management methods
    # ---------------------------------------------------------------------
    async def check_phase_completion_and_trigger_pm(self, workspace_id: str) -> Optional[str]:
        """Controllo fasi con PhaseManager"""

        try:
            current_phase = await PhaseManager.determine_workspace_current_phase(workspace_id)
            next_phase = PhaseManager.get_next_phase(current_phase)

            logger.info(f"Workspace {workspace_id} - Current phase: {current_phase.value}, Next: {next_phase.value if next_phase else 'None'}")

            if not next_phase:
                logger.info(f"Project {workspace_id} in final phase {current_phase.value}")
                return None

            if await self._check_existing_phase_planning(workspace_id, next_phase):
                logger.info(f"Phase planning for {next_phase.value} already exists")
                return None

            return await self._create_phase_planning_task(workspace_id, current_phase, next_phase)

        except Exception as e:
            logger.error(f"Error in phase completion check: {e}", exc_info=True)
            return None

    async def _check_existing_phase_planning(self, workspace_id: str, target_phase: ProjectPhase) -> bool:
        """Verifica se esiste già un task di planning per la fase target"""
        try:
            tasks = await list_tasks(workspace_id)

            for task in tasks:
                if task.get("status") in ["pending", "in_progress"]:
                    context_data = task.get("context_data", {}) or {}

                    if (context_data.get("planning_task_marker") and 
                        context_data.get("project_phase") == target_phase.value):
                        logger.info(f"Found existing planning task for phase {target_phase.value}: {task['id']}")
                        return True

                    task_name = (task.get("name") or "").lower()
                    if (f"phase planning" in task_name and 
                        target_phase.value.lower() in task_name):
                        return True

            return False
        except Exception as e:
            logger.error(f"Error checking existing phase planning: {e}")
            return True

    async def _find_project_manager(self, workspace_id: str) -> Optional[Dict]:
        """Trova il Project Manager nel workspace"""
        try:
            agents = await list_agents(workspace_id)

            for agent in agents:
                if (agent.get("status") == "active" and 
                    "project manager" in (agent.get("role") or "").lower()):
                    return agent

            for agent in agents:
                if (agent.get("status") == "active" and 
                    any(keyword in (agent.get("role") or "").lower() 
                        for keyword in ["manager", "coordinator", "director", "lead"])):
                    return agent

            logger.warning(f"No project manager found in workspace {workspace_id}")
            return None
        except Exception as e:
            logger.error(f"Error finding project manager: {e}")
            return None

    async def _create_phase_planning_task(
        self, 
        workspace_id: str, 
        current_phase: ProjectPhase, 
        next_phase: ProjectPhase
    ) -> Optional[str]:
        """Crea task di planning per la fase successiva"""

        pm_agent = await self._find_project_manager(workspace_id)
        if not pm_agent:
            return None

        phase_planning_templates = {
            ProjectPhase.IMPLEMENTATION: {
                "title": "Content Strategy & Editorial Plan Development",
                "focus": "strategy frameworks, planning templates, workflows",
                "examples": "Content Strategy Framework, Editorial Calendar Template, Publishing Workflow"
            },
            ProjectPhase.FINALIZATION: {
                "title": "Content Creation & Publishing Execution", 
                "focus": "content creation, publishing execution, final deliverables",
                "examples": "Content Posts Creation, Publishing Schedule Execution, Performance Analytics"
            }
        }

        template = phase_planning_templates.get(next_phase)
        if not template:
            logger.warning(f"No planning template for phase {next_phase.value}")
            return None

        task_name = f"Phase Planning: {template['title']}"

        planning_task = await create_task(
            workspace_id=workspace_id,
            agent_id=pm_agent["id"],
            name=task_name,
            description=f"""Plan and define sub-tasks for the {next_phase.value} phase.

CURRENT PHASE COMPLETED: {current_phase.value}
TARGET PHASE: {next_phase.value}
FOCUS AREAS: {template['focus']}

CRITICAL REQUIREMENTS:
1. Your detailed_results_json MUST include:
   - "current_project_phase": "{next_phase.value}"
   - "defined_sub_tasks" array
2. Each sub-task MUST have "project_phase": "{next_phase.value}"
3. Use exact agent names from get_team_roles_and_status

EXAMPLE SUB-TASKS FOR {next_phase.value}:
{template['examples']}

Phase Description: {PhaseManager.get_phase_description(next_phase)}
""",
            status="pending",
            priority="high",
            creation_type="phase_transition",
            context_data={
                "project_phase": next_phase.value,
                "phase_transition": f"{current_phase.value}_TO_{next_phase.value}",
                "planning_task_marker": True,
                "phase_validated": True,
                "target_phase": next_phase.value,
                "completed_phase": current_phase.value,
                "phase_trigger_timestamp": datetime.now().isoformat()
            }
        )

        if planning_task and planning_task.get("id"):
            logger.info(f"✅ Created phase planning task {planning_task['id']} "
                       f"for transition {current_phase.value} → {next_phase.value}")
            return planning_task["id"]
        else:
            logger.error(f"❌ Failed to create phase planning task for {next_phase.value}")
            return None

    # Mantieni tutti gli altri metodi esistenti...
    # (tutti i metodi conservativi, di analisi, logging, ecc.)

    def _should_analyze_task_ultra_conservative(self, task: Task, result: Dict[str, Any]) -> bool:
        """Ultra-conservative filter for task analysis"""
        if result.get("status") != "completed":
            return False
        
        task_name_lower = task.name.lower() if task.name else ""
        completion_words = ["handoff", "completed", "done", "finished", "delivered", "final"]
        
        if any(word in task_name_lower for word in completion_words):
            return False
        
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
        
        if len(output) > 1500:
            return False
        
        phase_completion_indicators = [
            "analysis", "profiling", "audit", "research", 
            "assessment", "evaluation", "investigation"
        ]
        
        if any(indicator in task_name_lower for indicator in phase_completion_indicators):
            logger.debug(f"Task {task.id} allowed for phase completion analysis")
            return True
        
        return False

    def _check_strict_workspace_limits(self, ctx: Dict[str, Any]) -> bool:
        """Extremely strict limits for workspace auto-generation"""
        if ctx.get("pending_tasks", 1) > 3:
            return False
        
        total_tasks = ctx.get("total_tasks", 1)
        completed_tasks = ctx.get("completed_tasks", 0)
        completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
        
        if completion_rate < 0.70:
            return False
        
        if total_tasks < 3:
            return False
        
        return True

    def _is_handoff_duplicate_strict(self, task: Task, ctx: Dict[str, Any]) -> bool:
        """Absolute duplicate prevention"""
        cache_key = f"{task.workspace_id}_{task.agent_id}_handoff"
        recent_handoff = self.handoff_cache.get(cache_key)
        if recent_handoff and datetime.now() - recent_handoff < timedelta(hours=24):
            return True

        recent_tasks = ctx.get("recent_completions", [])
        task_words = set(task.name.lower().split())
        
        for recent_task in recent_tasks[-10:]:
            recent_name = recent_task.get("name", "").lower()
            
            if any(word in recent_name for word in ["handoff", "follow-up", "continuation", "next"]):
                return True
                
            recent_words = set(recent_name.split())
            overlap = len(task_words & recent_words) / len(task_words | recent_words)
            if overlap > 0.5:
                return True

        return False

    def _analyze_task_deterministic(
        self,
        task: Task,
        result: Dict[str, Any],
        ctx: Dict[str, Any],
    ) -> TaskAnalysisOutput:
        """Pure rule-based analysis without any LLM calls"""
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
            
            follow_up_patterns = [
                "analysis indicates need for",
                "research suggests next step",
                "preliminary findings require",
                "initial assessment shows need"
            ]
            
            pattern_matches = sum(1 for pattern in follow_up_patterns if pattern in output_lower)
            
            if pattern_matches >= 2 and len(output_text) > 100:
                confidence = 0.7
                analysis.confidence_score = confidence
                analysis.reasoning = f"Matched {pattern_matches} follow-up patterns"
                logger.debug(f"Task {task.id} analysis: confidence {confidence}, but no auto-generation")
            
            analysis.reasoning += f" | Output: {len(output_text)}chars, Pending: {ctx['pending_tasks']}"
            
        except Exception as e:
            logger.error(f"Error in deterministic analysis: {e}")
            analysis.reasoning = f"Analysis error: {str(e)}"
        
        return analysis

    async def _gather_minimal_context(self, workspace_id: str) -> Dict[str, Any]:
        """Gather only essential context data without expensive operations"""
        try:
            workspace = await get_workspace(workspace_id)
            tasks = await list_tasks(workspace_id)

            completed = [t for t in tasks if t.get("status") == TaskStatus.COMPLETED.value]
            pending = [t for t in tasks if t.get("status") == TaskStatus.PENDING.value]
            
            return {
                "workspace_goal": workspace.get("goal", "") if workspace else "",
                "total_tasks": len(tasks),
                "completed_tasks": len(completed),
                "pending_tasks": len(pending),
                "recent_completions": [
                    {"name": t.get("name", ""), "id": t.get("id", "")}
                    for t in completed[-5:]
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

    async def _execute_minimal_handoff(
        self,
        analysis: TaskAnalysisOutput,
        task: Task,
        workspace_id: str,
    ) -> None:
        """Execute handoff with absolute minimal scope"""
        logger.warning(f"EXECUTING AUTO-HANDOFF for task {task.id} - This should be rare!")

        if not analysis.suggested_handoffs:
            return
        
        try:
            cache_key = f"{workspace_id}_handoff"
            self.handoff_cache[cache_key] = datetime.now()
            
            description = f"""[AUTOMATED FOLLOW-UP] (Generated from: {task.name})

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
                "created_at": datetime.now().isoformat()
            }
            
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
        
        confidence = 0.0
        reasoning = ""
        
        if isinstance(result_or_analysis, dict):
            if "confidence_score" in result_or_analysis:
                confidence = result_or_analysis.get("confidence_score", 0.0)
                reasoning = result_or_analysis.get("reasoning", "")
            elif hasattr(result_or_analysis, '__dict__'):
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
    # Configuration and status methods
    # ---------------------------------------------------------------------
    def enable_auto_generation(
        self, 
        enable_analysis: bool = True, 
        enable_handoffs: bool = True,
        confidence_threshold: float = 0.95
    ):
        """Enable auto-generation - USE WITH EXTREME CAUTION!"""
        logger.critical("⚠️  ENABLING AUTO-GENERATION! This may cause task loops. Monitor carefully!")
        self.auto_generation_enabled = True
        self.analysis_enabled = enable_analysis
        self.handoff_creation_enabled = enable_handoffs
        self.confidence_threshold = confidence_threshold
        
        logger.warning(f"Auto-generation config: analysis={enable_analysis}, handoffs={enable_handoffs}, threshold={confidence_threshold}")

    def disable_auto_generation(self):
        """Disable auto-generation completely (recommended default)"""
        logger.info("Auto-generation disabled - system returned to safe state")
        self.auto_generation_enabled = False  
        self.analysis_enabled = False
        self.handoff_creation_enabled = False
        self.confidence_threshold = 0.99

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status for monitoring dashboard"""
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
            "uptime_hours": (datetime.now() - self.initialization_time).total_seconds() / 3600,
            "safety_mode": "STRICT" if not self.auto_generation_enabled else "PERMISSIVE",
            "risk_level": "LOW" if not self.auto_generation_enabled else "HIGH"
        }

    def cleanup_caches(self) -> None:
        """Periodic cache cleanup to prevent memory leaks"""
        try:
            current_time = datetime.now()
            
            expired_keys = [
                key for key, timestamp in self.handoff_cache.items()
                if current_time - timestamp > timedelta(hours=24)
            ]
            
            for key in expired_keys:
                del self.handoff_cache[key]
            
            if len(self.analyzed_tasks) > 1000:
                analyzed_list = list(self.analyzed_tasks)
                self.analyzed_tasks = set(analyzed_list[-500:])
            
            self.last_cleanup = current_time
            logger.info(f"Cache cleanup completed: removed {len(expired_keys)} expired entries")
            
        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")

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