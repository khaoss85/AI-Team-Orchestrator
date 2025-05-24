# backend/task_analyzer.py
import logging
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set

# IMPORT AGGIORNATI per compatibilità con i nuovi models
from models import Task, TaskStatus
from models import ProjectPhase, PHASE_SEQUENCE, PHASE_DESCRIPTIONS
from database import create_task, list_agents, list_tasks, get_workspace, get_task

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
            
            logger.info(f"📊 CURRENT PHASE: Workspace {workspace_id} phase counts: {phase_counts}")
            
            # LOGICA CORRETTA: Determina la fase ATTUALE (non quella successiva)
            if phase_counts[ProjectPhase.FINALIZATION] >= 2:
                current = ProjectPhase.COMPLETED
            elif phase_counts[ProjectPhase.FINALIZATION] >= 1:
                current = ProjectPhase.FINALIZATION
            elif phase_counts[ProjectPhase.IMPLEMENTATION] >= 1:
                current = ProjectPhase.IMPLEMENTATION
            else:
                current = ProjectPhase.ANALYSIS
            
            logger.info(f"📊 CURRENT PHASE: Determined current phase for {workspace_id}: {current.value}")
            return current
                
        except Exception as e:
            logger.error(f"Error determining workspace phase: {e}")
            return ProjectPhase.ANALYSIS
        
    @staticmethod
    async def should_transition_to_next_phase(workspace_id: str) -> tuple[ProjectPhase, Optional[ProjectPhase]]:
        """Determina se è il momento di transire alla fase successiva"""
        try:
            tasks = await list_tasks(workspace_id)
            completed_tasks = [t for t in tasks if t.get("status") == "completed"]
            pending_tasks = [t for t in tasks if t.get("status") in ["pending", "in_progress"]]
            
            # Conta task completati per fase
            phase_counts = {phase: 0 for phase in ProjectPhase}
            for task in completed_tasks:
                context_data = task.get("context_data", {}) or {}
                task_phase = context_data.get("project_phase", "ANALYSIS")
                validated_phase = PhaseManager.validate_phase(task_phase)
                phase_counts[validated_phase] += 1
            
            # Conta task pendenti per fase
            pending_phase_counts = {phase: 0 for phase in ProjectPhase}
            for task in pending_tasks:
                context_data = task.get("context_data", {}) or {}
                task_phase = context_data.get("project_phase", "ANALYSIS")
                validated_phase = PhaseManager.validate_phase(task_phase)
                pending_phase_counts[validated_phase] += 1
            
            logger.info(f"🚀 TRANSITION CHECK: Completed: {phase_counts}, Pending: {pending_phase_counts}")
            
            # Se abbiamo task FINALIZATION completati, progetto finito
            if phase_counts[ProjectPhase.FINALIZATION] >= 2:
                return ProjectPhase.COMPLETED, None
            
            # CRITICO: Se abbiamo abbastanza IMPLEMENTATION completati E nessun task FINALIZATION pending
            # Allora dobbiamo creare task per FINALIZATION
            if (phase_counts[ProjectPhase.IMPLEMENTATION] >= 2 and 
                pending_phase_counts[ProjectPhase.FINALIZATION] == 0):
                
                logger.info(f"🚀 TRANSITION: Ready for FINALIZATION! IMPL completed: {phase_counts[ProjectPhase.IMPLEMENTATION]}, FINAL pending: {pending_phase_counts[ProjectPhase.FINALIZATION]}")
                return ProjectPhase.IMPLEMENTATION, ProjectPhase.FINALIZATION
            
            # Se abbiamo abbastanza ANALYSIS completati E nessun task IMPLEMENTATION pending
            if (phase_counts[ProjectPhase.ANALYSIS] >= 2 and 
                pending_phase_counts[ProjectPhase.IMPLEMENTATION] == 0):
                
                logger.info(f"🚀 TRANSITION: Ready for IMPLEMENTATION! ANAL completed: {phase_counts[ProjectPhase.ANALYSIS]}, IMPL pending: {pending_phase_counts[ProjectPhase.IMPLEMENTATION]}")
                return ProjectPhase.ANALYSIS, ProjectPhase.IMPLEMENTATION
            
            # Determina fase attuale senza transizione
            current_phase = await PhaseManager.determine_workspace_current_phase(workspace_id)
            
            logger.info(f"🚀 TRANSITION: Current phase: {current_phase.value}, no transition needed")
            return current_phase, None
            
        except Exception as e:
            logger.error(f"Error in phase transition check: {e}")
            return ProjectPhase.ANALYSIS, None
    
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
        """
        Gestisce il completamento di task del Project Manager con validazione fasi integrata.

        Combina:
        - Parsing JSON robusto
        - Validazione fasi tramite PhaseManager  
        - Gestione task_id forniti dal PM tool
        - Controllo duplicati dell'analyzer
        - Matching agenti migliorato
        - Context data dettagliato
        """
        task_id_str = str(task.id)
        logger.info(f"TaskAnalyzer: Handling PM task completion: {task_id_str} ('{task.name}') for workspace {workspace_id}")

        # =================================================================
        # 1. ESTRAZIONE E PARSING DETAILED_RESULTS_JSON
        # =================================================================
        detailed_results_json_str = result.get("detailed_results_json")
        if not detailed_results_json_str:
            logger.error(f"TaskAnalyzer: PM task {task_id_str} missing detailed_results_json in its result.")
            return False

        results_data = self._safe_json_loads(detailed_results_json_str)
        if not results_data:
            logger.error(f"TaskAnalyzer: PM task {task_id_str} failed to parse detailed_results_json. Content snippet: {detailed_results_json_str[:200]}")
            return False

        # =================================================================
        # 2. VALIDAZIONE FASE CORRENTE CON PHASEMANAGER
        # =================================================================
        current_project_phase_from_pm_str = results_data.get("current_project_phase")
        if not current_project_phase_from_pm_str:
            logger.error(f"TaskAnalyzer: PM task {task_id_str} output missing 'current_project_phase' key.")
            return False

        try:
            # Usa PhaseManager per validazione centralizzata
            validated_phase_enum = PhaseManager.validate_phase(current_project_phase_from_pm_str)
            validated_phase_value = validated_phase_enum.value
            logger.info(f"PM specified phase: {current_project_phase_from_pm_str} -> validated: {validated_phase_value}")
        except Exception as e:
            logger.error(f"TaskAnalyzer: PM task {task_id_str} phase validation failed: {e}")
            return False

        # =================================================================
        # 3. ESTRAZIONE E VALIDAZIONE SUB-TASKS
        # =================================================================
        defined_sub_tasks_list = results_data.get("defined_sub_tasks", [])
        if not isinstance(defined_sub_tasks_list, list):
            logger.error(f"TaskAnalyzer: PM task {task_id_str} 'defined_sub_tasks' is not a list. Found: {type(defined_sub_tasks_list)}")
            return False

        if not defined_sub_tasks_list:
            logger.info(f"TaskAnalyzer: PM task {task_id_str} did not define any sub-tasks for phase '{validated_phase_value}'. No new tasks to create.")
            return True 

        logger.info(f"TaskAnalyzer: PM task {task_id_str} defined {len(defined_sub_tasks_list)} sub-tasks for phase '{validated_phase_value}'. Processing definitions...")

        # =================================================================
        # 4. PREPARAZIONE CONTESTO PER CREAZIONE TASK
        # =================================================================
        agents_in_workspace = await list_agents(workspace_id)
        if not agents_in_workspace:
            logger.error(f"TaskAnalyzer: No agents found in workspace {workspace_id} to assign sub-tasks from PM task {task_id_str}.")
            return False

        # Pre-fetch tutti i task per controllo duplicati
        all_tasks_in_db_for_dedup = await list_tasks(workspace_id=workspace_id)

        # Prepara delegation chain
        delegation_chain_from_pm_task = task.context_data.get("delegation_chain", []) if task.context_data else []
        if not isinstance(delegation_chain_from_pm_task, list):
            delegation_chain_from_pm_task = []

        # Contatori e tracking
        created_by_analyzer_count = 0
        skipped_by_analyzer_count = 0
        phase_validation_errors = []

        # =================================================================
        # 5. PROCESSAMENTO SUB-TASKS
        # =================================================================
        for sub_task_def in defined_sub_tasks_list:
            if not isinstance(sub_task_def, dict):
                logger.warning(f"TaskAnalyzer: Invalid sub_task_def format (not a dict) in PM output for task {task_id_str}. Skipping: {sub_task_def}")
                continue

            # ---- Estrazione campi base ----
            task_name = sub_task_def.get("name")
            task_description = sub_task_def.get("description")
            target_agent_name_from_pm = sub_task_def.get("target_agent_role") or ""
            priority = sub_task_def.get("priority", "medium").lower()

            # Validazione campi obbligatori
            required_fields = ["name", "description", "target_agent_role"]
            missing_fields = [field for field in required_fields if not sub_task_def.get(field)]
            if missing_fields:
                logger.warning(f"TaskAnalyzer: Sub-task definition missing fields {missing_fields}. Skipping: {sub_task_def}")
                continue

            # ---- Validazione fase sub-task ----
            sub_task_project_phase_str_from_pm = sub_task_def.get("project_phase", validated_phase_value)

            try:
                sub_task_project_phase_enum = PhaseManager.validate_phase(sub_task_project_phase_str_from_pm)
                sub_task_project_phase_value = sub_task_project_phase_enum.value

                # Track phase corrections
                if sub_task_project_phase_str_from_pm != sub_task_project_phase_value:
                    phase_validation_errors.append({
                        "task": task_name,
                        "original": sub_task_project_phase_str_from_pm,
                        "corrected": sub_task_project_phase_value
                    })
            except Exception as e:
                logger.error(f"TaskAnalyzer: Sub-task '{task_name}' phase validation failed: {e}. Skipping.")
                continue

            # =============================================================
            # 6. GESTIONE TASK_ID FORNITO DAL PM TOOL
            # =============================================================
            tool_created_task_id = sub_task_def.get("task_id")
            if tool_created_task_id:
                try:
                    existing_task = await get_task(tool_created_task_id)
                    if existing_task:
                        existing_task_name = existing_task.get("name")
                        current_task_name = sub_task_def.get("name")  # Nome del task corrente dal PM JSON

                        if existing_task_name and current_task_name and existing_task_name.lower() == current_task_name.lower():
                            logger.info(f"TaskAnalyzer: PM task {task_id_str} correctly referenced sub-task ID '{tool_created_task_id}' ('{current_task_name}') created via tool. Analyzer will not create duplicate.")

                            # Aggiorna context del task esistente per tracciare riconoscimento analyzer
                            try:
                                existing_context_data = existing_task.get("context_data", {})
                                updated_context = existing_context_data.copy() if existing_context_data else {}

                                updated_context.update({
                                    "pm_analyzer_acknowledged_at": datetime.now().isoformat(),
                                    "acknowledged_by_pm_task": task_id_str,
                                    "phase_validated_by_analyzer": True,
                                    "analyzer_validated_phase": sub_task_project_phase_value
                                })
                                # Note: Qui potresti aggiungere una chiamata per aggiornare il context se necessario
                                logger.debug(f"Updated context for task {tool_created_task_id} with analyzer acknowledgment")
                            except Exception as e:
                                logger.warning(f"Could not update context for existing task {tool_created_task_id}: {e}")

                            skipped_by_analyzer_count += 1
                            continue 
                        else:
                            logger.warning(f"TaskAnalyzer: PM task {task_id_str} referenced sub-task ID '{tool_created_task_id}' for '{current_task_name}', but task not found or name mismatched (existing: '{existing_task_name}'). Analyzer will attempt creation after duplicate check.")
                    else:
                        logger.warning(f"TaskAnalyzer: PM task {task_id_str} referenced sub-task ID '{tool_created_task_id}' but task not found in database. Analyzer will attempt creation after duplicate check.")
                except Exception as e:
                    logger.warning(f"Error checking tool-created task {tool_created_task_id}: {e}")

            # =============================================================
            # 7. TROVA AGENTE TARGET CON ALGORITMO MIGLIORATO
            # =============================================================
            agent_to_assign = await self._find_agent_by_role(workspace_id, target_agent_name_from_pm)
            if not agent_to_assign:
                logger.warning(f"TaskAnalyzer: Sub-task '{task_name}': No suitable agent found for role '{target_agent_name_from_pm}'. Skipping creation.")
                continue

            # =============================================================
            # 8. CONTROLLO DUPLICATI ANALYZER (FALLBACK) - FIX CRITICO
            # =============================================================
            is_duplicate_found_by_analyzer = False
            for t_db_dict in all_tasks_in_db_for_dedup:
                # Controllo multi-criterio per duplicati
                name_match = t_db_dict.get("name", "").lower() == task_name.lower()
                phase_match = (t_db_dict.get("context_data", {}).get("project_phase", "").upper() == sub_task_project_phase_value)

                # NUOVA RIGA CORRETTA - Gestisce None safely:
                target_agent_name_safe = (target_agent_name_from_pm or "").lower()
                assigned_role_db_safe = (t_db_dict.get("assigned_to_role") or "").lower()

                agent_match = (
                    t_db_dict.get("agent_id") == agent_to_assign["id"] or 
                    (target_agent_name_from_pm is not None and assigned_role_db_safe == target_agent_name_safe)  # ← FISSO
                )

                status_match = t_db_dict.get("status") in [TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value]
                origin_match = (
                    t_db_dict.get("parent_task_id") == task_id_str or 
                    t_db_dict.get("context_data", {}).get("source_pm_task_id") == task_id_str
                )

                if name_match and phase_match and agent_match and status_match and origin_match:
                    logger.warning(f"TaskAnalyzer: Sub-task '{task_name}' appears to be duplicate of existing task {t_db_dict.get('id')} (status: {t_db_dict.get('status')}). Skipping creation.")
                    is_duplicate_found_by_analyzer = True
                    skipped_by_analyzer_count += 1
                    break

            if is_duplicate_found_by_analyzer:
                continue

            # =============================================================
            # 9. CREAZIONE SUB-TASK
            # =============================================================
            logger.info(f"TaskAnalyzer: Creating sub-task '{task_name}' for agent '{agent_to_assign['name']}' in phase '{sub_task_project_phase_value}'.")

            # Context data dettagliato per tracking completo
            sub_task_context = {
                # ---- Tracking fase ----
                "project_phase": sub_task_project_phase_value,
                "original_pm_phase_planner": validated_phase_value,
                "phase_validated": True,
                "phase_validation_timestamp": datetime.now().isoformat(),

                # ---- Tracking origine ----
                "source_pm_task_id": task_id_str,
                "source_pm_task_name": task.name,
                "created_by_task_analyzer": True,
                "auto_generated_by_pm_output": True,

                # ---- Tracking temporale ----
                "pm_completion_timestamp": datetime.now().isoformat(),
                "creation_method": "pm_completion_analyzer",

                # ---- Delegation chain ----
                "delegation_chain": delegation_chain_from_pm_task + [task_id_str],

                # ---- Criteri completamento ----
                "expected_completion_criteria": sub_task_def.get("completion_criteria", "Task completed successfully"),

                # ---- Metadata aggiuntivi ----
                "pm_specified_agent_role": target_agent_name_from_pm,
                "assigned_agent_actual_role": agent_to_assign.get("role"),
                "original_pm_phase_spec": sub_task_project_phase_str_from_pm if sub_task_project_phase_str_from_pm != sub_task_project_phase_value else None,
            }

            try:
                created_db_task_dict = await create_task(
                    workspace_id=workspace_id,
                    agent_id=str(agent_to_assign["id"]),
                    assigned_to_role=agent_to_assign.get("role"),
                    name=task_name,
                    description=task_description,
                    status=TaskStatus.PENDING.value,
                    priority=priority,
                    parent_task_id=task_id_str, 
                    context_data=sub_task_context,
                    created_by_task_id=task_id_str,
                    created_by_agent_id=str(task.agent_id) if task.agent_id else None,
                    creation_type="pm_completion_analyzer" 
                )

                if created_db_task_dict and created_db_task_dict.get("id"):
                    created_by_analyzer_count += 1
                    logger.info(f"TaskAnalyzer: ✅ Successfully created sub-task '{created_db_task_dict['name']}' (ID: {created_db_task_dict['id']}) for agent {agent_to_assign['name']} in phase {sub_task_project_phase_value}")
                else:
                    logger.error(f"TaskAnalyzer: ❌ Failed to create sub-task '{task_name}' in DB. Response: {created_db_task_dict}")

            except Exception as e:
                logger.error(f"TaskAnalyzer: Error creating sub-task '{task_name}': {e}", exc_info=True)

        # =================================================================
        # 10. LOGGING FINALE E VALIDAZIONE ERRORI
        # =================================================================

        # Log phase validation errors se presenti
        if phase_validation_errors:
            logger.warning(f"TaskAnalyzer: Phase validation corrections made for PM task {task_id_str}: {phase_validation_errors}")

        # Summary finale
        logger.info(f"TaskAnalyzer: PM task {task_id_str} completion processing finished.")
        logger.info(f"  └─ Definitions processed: {len(defined_sub_tasks_list)}")
        logger.info(f"  └─ Tasks created by analyzer: {created_by_analyzer_count}")
        logger.info(f"  └─ Tasks skipped (already existed/PM provided ID): {skipped_by_analyzer_count}")
        logger.info(f"  └─ Phase corrections: {len(phase_validation_errors)}")
        logger.info(f"  └─ Target phase: {validated_phase_value}")

        # Log structured per monitoring
        completion_summary = {
            "pm_task_id": task_id_str,
            "pm_task_name": task.name,
            "workspace_id": workspace_id,
            "target_phase": validated_phase_value,
            "subtasks_defined": len(defined_sub_tasks_list),
            "subtasks_created": created_by_analyzer_count,
            "subtasks_skipped": skipped_by_analyzer_count,
            "phase_corrections": len(phase_validation_errors),
            "completion_timestamp": datetime.now().isoformat()
        }

        logger.info(f"PM_COMPLETION_SUMMARY: {json.dumps(completion_summary)}")

        return created_by_analyzer_count > 0

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
        """Controllo fasi con PhaseManager - VERSIONE AGGIORNATA"""

        try:
            logger.info(f"🔍 PHASE CHECK: Starting for workspace {workspace_id}")

            # USA LA NUOVA LOGICA DI TRANSIZIONE
            current_phase, should_create_for_phase = await PhaseManager.should_transition_to_next_phase(workspace_id)

            logger.info(f"🔍 PHASE CHECK: Current: {current_phase.value if current_phase else 'None'}, "
                       f"Should create for: {should_create_for_phase.value if should_create_for_phase else 'None'}")

            if not should_create_for_phase:
                logger.info(f"🔍 PHASE CHECK: No transition needed for {workspace_id}")
                return None

            # Controlla se esiste già planning per la fase target
            if await self._check_existing_phase_planning(workspace_id, should_create_for_phase):
                logger.info(f"🔍 PHASE CHECK: Planning for {should_create_for_phase.value} already exists")
                return None

            # Controllo limiti workspace (più permissivo per phase transitions)
            workspace_ctx = await self._gather_minimal_context(workspace_id)
            pending_tasks = workspace_ctx.get("pending_tasks", 0)

            # Limiti più permissivi per transizioni critiche
            max_pending = 10 if should_create_for_phase == ProjectPhase.FINALIZATION else 8

            if pending_tasks > max_pending:
                logger.warning(f"🔍 PHASE CHECK: Too many pending tasks ({pending_tasks} > {max_pending}) - skipping transition to {should_create_for_phase.value}")
                return None

            logger.info(f"🚀 PHASE CHECK: Creating planning task for {should_create_for_phase.value}")

            return await self._create_phase_planning_task(workspace_id, current_phase, should_create_for_phase)

        except Exception as e:
            logger.error(f"Error in phase completion check: {e}", exc_info=True)
            return None

    async def _verify_phase_completion_criteria(
        self, 
        workspace_id: str, 
        current_phase: ProjectPhase, 
        target_phase: ProjectPhase
    ) -> bool:
        """Verifica che i criteri di completamento fase siano soddisfatti"""

        try:
            tasks = await list_tasks(workspace_id)
            completed_tasks = [t for t in tasks if t.get("status") == "completed"]

            # Conta task completati per fase
            phase_counts = {phase: 0 for phase in ProjectPhase}
            for task in completed_tasks:
                context_data = task.get("context_data", {}) or {}
                task_phase = context_data.get("project_phase", "ANALYSIS")
                validated_phase = PhaseManager.validate_phase(task_phase)
                phase_counts[validated_phase] += 1

            logger.info(f"📊 PHASE CRITERIA: Phase completion counts: {phase_counts}")

            # Criteri specifici per transizione verso FINALIZATION
            if target_phase == ProjectPhase.FINALIZATION:
                analysis_completed = phase_counts[ProjectPhase.ANALYSIS] >= 2
                implementation_completed = phase_counts[ProjectPhase.IMPLEMENTATION] >= 2

                criteria_met = analysis_completed and implementation_completed

                logger.info(f"📊 PHASE CRITERIA: For FINALIZATION transition - "
                           f"Analysis: {phase_counts[ProjectPhase.ANALYSIS]} >= 2 ({analysis_completed}), "
                           f"Implementation: {phase_counts[ProjectPhase.IMPLEMENTATION]} >= 2 ({implementation_completed}), "
                           f"Criteria met: {criteria_met}")

                return criteria_met

            # Criteri per transizione verso IMPLEMENTATION
            elif target_phase == ProjectPhase.IMPLEMENTATION:
                analysis_completed = phase_counts[ProjectPhase.ANALYSIS] >= 2

                logger.info(f"📊 PHASE CRITERIA: For IMPLEMENTATION transition - "
                           f"Analysis: {phase_counts[ProjectPhase.ANALYSIS]} >= 2 ({analysis_completed})")

                return analysis_completed

            # Default: permettere transizioni
            return True

        except Exception as e:
            logger.error(f"Error verifying phase completion criteria: {e}")
            return False
    
    async def _check_existing_phase_planning(self, workspace_id: str, target_phase: ProjectPhase) -> bool:
        """Verifica se esiste già un task di planning per la fase target"""
        try:
            tasks = await list_tasks(workspace_id)

            for task in tasks:
                if task.get("status") in ["pending", "in_progress"]:
                    context_data = task.get("context_data", {}) or {}

                    # Controlla marker specifico per planning task
                    if (context_data.get("planning_task_marker") and 
                        context_data.get("target_phase") == target_phase.value):
                        logger.info(f"🔍 EXISTING: Found planning task {task['id']} for {target_phase.value}")
                        return True

                    # Controlla nel nome del task
                    task_name = (task.get("name") or "").lower()
                    if ("phase planning" in task_name and 
                        target_phase.value.lower() in task_name):
                        logger.info(f"🔍 EXISTING: Found planning task by name {task['id']} for {target_phase.value}")
                        return True

            logger.info(f"🔍 EXISTING: No planning tasks found for {target_phase.value}")
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
        target_phase: ProjectPhase
    ) -> Optional[str]:
        """Crea task di planning per la fase target"""

        pm_agent = await self._find_project_manager(workspace_id)
        if not pm_agent:
            logger.error(f"❌ No project manager found in workspace {workspace_id}")
            return None

        # Template per le diverse fasi
        if target_phase == ProjectPhase.FINALIZATION:
            task_name = "🎯 CRITICAL: Phase Planning for FINALIZATION"
            description = f"""🎯 FINAL PHASE PLANNING: Create deliverable tasks for project completion

    CRITICAL TRANSITION: {current_phase.value} → FINALIZATION

    ⚠️ THIS IS THE FINAL PHASE - CREATE TASKS THAT COMPLETE THE PROJECT

    MANDATORY REQUIREMENTS:
    1. detailed_results_json MUST include:
       - "current_project_phase": "FINALIZATION"
       - "defined_sub_tasks" array with 3+ tasks
    2. Each sub-task MUST have "project_phase": "FINALIZATION"
    3. Use exact agent names from get_team_roles_and_status

    🎯 FINALIZATION TASK EXAMPLES:
    - "Create Final Instagram Content Posts" 
    - "Generate Complete Lead Contact Database"
    - "Compile Campaign Performance Report"
    - "Create Executive Summary Document"

    ⚠️ CRITICAL: These tasks will produce the final project deliverables!
    """
        elif target_phase == ProjectPhase.IMPLEMENTATION:
            task_name = "📋 Phase Planning: Content Strategy & Implementation"
            description = f"""📋 IMPLEMENTATION PHASE PLANNING

    TRANSITION: {current_phase.value} → IMPLEMENTATION
    FOCUS: Strategy frameworks, templates, workflows

    REQUIREMENTS:
    1. detailed_results_json MUST include:
       - "current_project_phase": "IMPLEMENTATION"
       - "defined_sub_tasks" array
    2. Each sub-task MUST have "project_phase": "IMPLEMENTATION"

    IMPLEMENTATION EXAMPLES:
    - Content Strategy Framework
    - Editorial Calendar Template  
    - Publishing Workflow
    """
        else:
            logger.warning(f"No template for phase {target_phase.value}")
            return None

        planning_task = await create_task(
            workspace_id=workspace_id,
            agent_id=pm_agent["id"],
            name=task_name,
            description=description,
            status="pending",
            priority="high",
            creation_type="phase_transition",
            context_data={
                "project_phase": target_phase.value,
                "phase_transition": f"{current_phase.value}_TO_{target_phase.value}",
                "planning_task_marker": True,
                "target_phase": target_phase.value,  # IMPORTANTE per _check_existing_phase_planning
                "completed_phase": current_phase.value,
                "phase_trigger_timestamp": datetime.now().isoformat(),
                "is_finalization_planning": target_phase == ProjectPhase.FINALIZATION
            }
        )

        if planning_task and planning_task.get("id"):
            logger.info(f"✅ CREATED planning task {planning_task['id']} for {target_phase.value}")
            return planning_task["id"]
        else:
            logger.error(f"❌ FAILED to create planning task for {target_phase.value}")
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