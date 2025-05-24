# backend/task_analyzer.py - COMPLETE ENHANCED VERSION
# Sostituisce completamente il file esistente

import logging
import json
import re
import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from collections import defaultdict

from models import Task, TaskStatus, ProjectPhase, PHASE_SEQUENCE, PHASE_DESCRIPTIONS
from database import (
    create_task, list_agents, list_tasks, get_workspace, get_task,
    update_workspace_status, get_agent
)

logger = logging.getLogger(__name__)

# Configuration from environment
PHASE_PLANNING_COOLDOWN_MINUTES = int(os.getenv("PHASE_PLANNING_COOLDOWN_MINUTES", "5"))
MAX_PENDING_TASKS_FOR_TRANSITION = int(os.getenv("MAX_PENDING_TASKS_FOR_TRANSITION", "8"))
ENABLE_ENHANCED_PHASE_TRACKING = os.getenv("ENABLE_ENHANCED_PHASE_TRACKING", "true").lower() == "true"

class PhaseManagerError(Exception):
    """Custom exception for phase management errors"""
    pass

class PhaseManager:
    """Enhanced Phase Manager with robust planning detection"""
    
    @staticmethod
    def validate_phase(phase: str) -> ProjectPhase:
        """Validate and normalize a phase"""
        try:
            if not phase:
                return ProjectPhase.ANALYSIS
                
            phase_upper = str(phase).upper().strip()
            
            # Exact match first
            for valid_phase in ProjectPhase:
                if phase_upper == valid_phase.value:
                    return valid_phase
                    
            # Fallback mapping for compatibility
            fallback_mapping = {
                "RESEARCH": ProjectPhase.ANALYSIS,
                "STRATEGY": ProjectPhase.IMPLEMENTATION,
                "PLANNING": ProjectPhase.IMPLEMENTATION,
                "EXECUTION": ProjectPhase.FINALIZATION,
                "CREATION": ProjectPhase.FINALIZATION,
                "CONTENT": ProjectPhase.FINALIZATION,
                "PUBLISHING": ProjectPhase.FINALIZATION,
                "DELIVER": ProjectPhase.FINALIZATION,
                "FINAL": ProjectPhase.FINALIZATION
            }
            
            return fallback_mapping.get(phase_upper, ProjectPhase.ANALYSIS)
            
        except Exception as e:
            logger.warning(f"Error validating phase '{phase}': {e}")
            return ProjectPhase.ANALYSIS

    @staticmethod
    async def should_transition_to_next_phase(workspace_id: str) -> tuple[ProjectPhase, Optional[ProjectPhase]]:
        """
        ENHANCED: Determine phase transition with robust planning detection
        """
        try:
            tasks = await list_tasks(workspace_id)
            if not tasks:
                return ProjectPhase.ANALYSIS, None
                
            completed_tasks = [t for t in tasks if t.get("status") == "completed"]
            pending_tasks = [t for t in tasks if t.get("status") in ["pending", "in_progress"]]
            
            # Count completed tasks per phase
            phase_counts = {phase: 0 for phase in ProjectPhase}
            planning_phases_executed = set()
            
            for task in completed_tasks:
                try:
                    context_data = task.get("context_data") or {}
                    if isinstance(context_data, dict):
                        task_phase = context_data.get("project_phase", "ANALYSIS")
                        validated_phase = PhaseManager.validate_phase(task_phase)
                        phase_counts[validated_phase] += 1
                        
                        # Track executed planning tasks
                        if context_data.get("planning_task_marker"):
                            target_phase = context_data.get("target_phase")
                            if target_phase:
                                planning_phases_executed.add(target_phase)
                                
                except Exception as e:
                    logger.debug(f"Error processing completed task: {e}")
                    continue
            
            # Count pending tasks per phase
            pending_phase_counts = {phase: 0 for phase in ProjectPhase}
            pending_planning_phases = set()
            
            for task in pending_tasks:
                try:
                    context_data = task.get("context_data") or {}
                    if isinstance(context_data, dict):
                        task_phase = context_data.get("project_phase", "ANALYSIS")
                        validated_phase = PhaseManager.validate_phase(task_phase)
                        pending_phase_counts[validated_phase] += 1
                        
                        # Track pending planning tasks
                        if context_data.get("planning_task_marker"):
                            target_phase = context_data.get("target_phase")
                            if target_phase:
                                pending_planning_phases.add(target_phase)
                                
                except Exception as e:
                    logger.debug(f"Error processing pending task: {e}")
                    continue
            
            logger.info(f"🚀 PHASE CHECK {workspace_id}: Completed={dict(phase_counts)}, "
                       f"Planning executed={planning_phases_executed}, pending={pending_planning_phases}")
            
            # ENHANCED TRANSITION LOGIC
            
            # If FINALIZATION completed -> project finished
            if phase_counts[ProjectPhase.FINALIZATION] >= 2:
                return ProjectPhase.COMPLETED, None
            
            # For FINALIZATION: need IMPLEMENTATION + no conflicts
            if (phase_counts[ProjectPhase.IMPLEMENTATION] >= 2 and 
                pending_phase_counts[ProjectPhase.FINALIZATION] == 0 and
                "FINALIZATION" not in planning_phases_executed and
                "FINALIZATION" not in pending_planning_phases):
                
                logger.info(f"🚀 READY FOR FINALIZATION: {workspace_id}")
                return ProjectPhase.IMPLEMENTATION, ProjectPhase.FINALIZATION
            
            # For IMPLEMENTATION: need ANALYSIS + no conflicts
            if (phase_counts[ProjectPhase.ANALYSIS] >= 2 and 
                pending_phase_counts[ProjectPhase.IMPLEMENTATION] == 0 and
                "IMPLEMENTATION" not in planning_phases_executed and
                "IMPLEMENTATION" not in pending_planning_phases):
                
                logger.info(f"🚀 READY FOR IMPLEMENTATION: {workspace_id}")
                return ProjectPhase.ANALYSIS, ProjectPhase.IMPLEMENTATION
            
            # No transition needed
            current_phase = await PhaseManager.determine_workspace_current_phase(workspace_id)
            return current_phase, None
            
        except Exception as e:
            logger.error(f"Error in phase transition check: {e}", exc_info=True)
            return ProjectPhase.ANALYSIS, None

    @staticmethod
    async def determine_workspace_current_phase(workspace_id: str) -> ProjectPhase:
        """Determine current workspace phase"""
        try:
            tasks = await list_tasks(workspace_id)
            completed_tasks = [t for t in tasks if t.get("status") == "completed"]
            
            if not completed_tasks:
                return ProjectPhase.ANALYSIS
            
            # Count with error handling
            phase_counts = {phase: 0 for phase in ProjectPhase}
            
            for task in completed_tasks:
                try:
                    context_data = task.get("context_data") or {}
                    if isinstance(context_data, dict):
                        task_phase = context_data.get("project_phase", "ANALYSIS")
                        validated_phase = PhaseManager.validate_phase(task_phase)
                        phase_counts[validated_phase] += 1
                except Exception:
                    continue
            
            # Enhanced logic
            if phase_counts[ProjectPhase.FINALIZATION] >= 2:
                return ProjectPhase.COMPLETED
            elif phase_counts[ProjectPhase.FINALIZATION] >= 1:
                return ProjectPhase.FINALIZATION
            elif phase_counts[ProjectPhase.IMPLEMENTATION] >= 1:
                return ProjectPhase.IMPLEMENTATION
            else:
                return ProjectPhase.ANALYSIS
                
        except Exception as e:
            logger.error(f"Error determining current phase: {e}")
            return ProjectPhase.ANALYSIS

    @staticmethod
    async def check_existing_phase_planning_enhanced(
        workspace_id: str, 
        target_phase: ProjectPhase
    ) -> bool:
        """
        ENHANCED: Check for existing planning with multiple detection methods
        """
        try:
            tasks = await list_tasks(workspace_id)
            
            for task in tasks:
                try:
                    # Check all active statuses
                    if task.get("status") in ["pending", "in_progress", "completed"]:
                        context_data = task.get("context_data") or {}
                        
                        if not isinstance(context_data, dict):
                            continue
                        
                        # Method 1: Explicit planning marker
                        if (context_data.get("planning_task_marker") and 
                            context_data.get("target_phase") == target_phase.value):
                            logger.info(f"🔍 EXISTING: Planning task {task['id']} for {target_phase.value}")
                            return True
                        
                        # Method 2: Creation type check
                        if (context_data.get("creation_type") == "phase_transition" and
                            context_data.get("target_phase") == target_phase.value):
                            logger.info(f"🔍 EXISTING: Phase transition task {task['id']} for {target_phase.value}")
                            return True
                        
                        # Method 3: Name pattern matching
                        task_name = (task.get("name") or "").lower()
                        planning_indicators = ["phase planning", "planning", "setup"]
                        phase_indicators = [target_phase.value.lower()]
                        
                        if target_phase == ProjectPhase.FINALIZATION:
                            phase_indicators.extend(["final", "deliverable", "completion"])
                        elif target_phase == ProjectPhase.IMPLEMENTATION:
                            phase_indicators.extend(["implementation", "strategy", "framework"])
                        
                        has_planning = any(indicator in task_name for indicator in planning_indicators)
                        has_phase = any(indicator in task_name for indicator in phase_indicators)
                        
                        if has_planning and has_phase:
                            logger.info(f"🔍 EXISTING: Pattern match task {task['id']} for {target_phase.value}")
                            return True
                        
                except Exception as e:
                    logger.debug(f"Error checking task {task.get('id')}: {e}")
                    continue

            return False

        except Exception as e:
            logger.error(f"Error checking existing phase planning: {e}")
            return True  # Safe default

# ---------------------------------------------------------------------------
# Structured outputs per task analysis
# ---------------------------------------------------------------------------
class TaskAnalysisOutput:
    """Structured output for task completion analysis"""
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

class EnhancedTaskExecutor:
    """Enhanced task executor with comprehensive fix"""

    def __init__(self):
        # Configuration
        self.auto_generation_enabled = True
        self.analysis_enabled = True         
        self.handoff_creation_enabled = True
        
        # Enhanced tracking with thread safety
        self._tracking_lock = asyncio.Lock()
        self.phase_planning_tracker: Dict[str, Set[str]] = defaultdict(set)
        self.last_planning_time: Dict[str, datetime] = {}
        self.workspace_health_cache: Dict[str, tuple[datetime, Dict]] = {}
        
        # Existing tracking
        self.analyzed_tasks: Set[str] = set()
        self.handoff_cache: Dict[str, datetime] = {}
        
        # Configuration
        self.confidence_threshold = 0.70  
        self.max_auto_tasks_per_workspace = 5  
        self.cooldown_minutes = PHASE_PLANNING_COOLDOWN_MINUTES
        
        # Monitoring
        self.initialization_time = datetime.now()
        self.last_cleanup = datetime.now()
        self.performance_metrics = defaultdict(int)
        
        logger.info("EnhancedTaskExecutor initialized with complete fixes")

    # ---------------------------------------------------------------------
    # JSON Utilities
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

    async def handle_task_completion(
        self,
        completed_task: Task,
        task_result: Dict[str, Any],
        workspace_id: str,
    ) -> None:
        """Main handler with complete integration"""
        task_id_str = str(completed_task.id)

        # Thread-safe duplicate check
        async with self._tracking_lock:
            if task_id_str in self.analyzed_tasks:
                return
            self.analyzed_tasks.add(task_id_str)

        try:
            # Determine task type
            is_pm_task = await self._is_project_manager_task(completed_task, task_result)

            if is_pm_task:
                logger.info(f"Processing PM task: {task_id_str}")
                await self.handle_project_manager_completion(completed_task, task_result, workspace_id)
            else:
                logger.info(f"Processing specialist task: {task_id_str}")
                # Specialist tasks can trigger deliverable checks
                try:
                    from deliverable_aggregator import check_and_create_final_deliverable
                    deliverable_id = await check_and_create_final_deliverable(workspace_id)
                    if deliverable_id:
                        logger.critical(f"🎯 FINAL DELIVERABLE CREATED: {deliverable_id}")
                except Exception as e:
                    logger.error(f"Error checking final deliverable: {e}")

            # Phase completion check (after any task)
            try:
                pm_task_id = await self.check_phase_completion_and_trigger_pm(workspace_id)
                if pm_task_id:
                    logger.info(f"✅ Phase transition triggered: {pm_task_id}")
            except Exception as e:
                logger.error(f"Error in phase completion check: {e}")

        except Exception as e:
            logger.error(f"Error in task completion handling: {e}", exc_info=True)

    async def check_phase_completion_and_trigger_pm(self, workspace_id: str) -> Optional[str]:
        """
        ENHANCED: Phase completion check with robust duplicate prevention
        """
        try:
            logger.debug(f"🔍 PHASE CHECK: Starting for {workspace_id}")

            # Thread-safe cooldown check
            async with self._tracking_lock:
                last_planning = self.last_planning_time.get(workspace_id)
                if last_planning and datetime.now() - last_planning < timedelta(minutes=self.cooldown_minutes):
                    logger.debug(f"🔍 COOLDOWN: Active for {workspace_id}")
                    return None

            # Use enhanced phase manager
            current_phase, should_create_for_phase = await PhaseManager.should_transition_to_next_phase(workspace_id)

            if not should_create_for_phase:
                logger.debug(f"🔍 NO TRANSITION: {workspace_id}")
                return None

            # Enhanced existing planning check
            if await PhaseManager.check_existing_phase_planning_enhanced(workspace_id, should_create_for_phase):
                logger.info(f"🔍 EXISTING: Planning for {should_create_for_phase.value} found")
                return None

            # Thread-safe internal tracker check
            async with self._tracking_lock:
                workspace_planned = self.phase_planning_tracker.get(workspace_id, set())
                if should_create_for_phase.value in workspace_planned:
                    logger.info(f"🔍 TRACKED: {should_create_for_phase.value} in internal tracker")
                    return None

            # Workspace limits check
            workspace_ctx = await self._gather_minimal_context(workspace_id)
            if workspace_ctx.get("pending_tasks", 0) > MAX_PENDING_TASKS_FOR_TRANSITION:
                logger.warning(f"🔍 LIMITS: Too many pending tasks for {workspace_id}")
                return None

            logger.info(f"🚀 CREATING: Planning task for {should_create_for_phase.value}")

            # Thread-safe tracker update
            async with self._tracking_lock:
                if workspace_id not in self.phase_planning_tracker:
                    self.phase_planning_tracker[workspace_id] = set()
                self.phase_planning_tracker[workspace_id].add(should_create_for_phase.value)
                self.last_planning_time[workspace_id] = datetime.now()

            # Create planning task
            task_id = await self._create_phase_planning_task(
                workspace_id, current_phase, should_create_for_phase
            )
            
            if task_id:
                logger.info(f"✅ PLANNING CREATED: {task_id}")
            else:
                # Rollback tracker if creation failed
                async with self._tracking_lock:
                    self.phase_planning_tracker[workspace_id].discard(should_create_for_phase.value)
                
            return task_id

        except Exception as e:
            logger.error(f"Error in phase completion check: {e}", exc_info=True)
            return None

    async def _create_phase_planning_task(
        self, 
        workspace_id: str, 
        current_phase: ProjectPhase, 
        target_phase: ProjectPhase
    ) -> Optional[str]:
        """Create phase planning task with enhanced tracking"""
        try:
            # Find project manager
            pm_agent = await self._find_project_manager(workspace_id)
            if not pm_agent:
                logger.error(f"❌ No project manager found in workspace {workspace_id}")
                return None

            # Generate unique identifiers to prevent duplicates
            unique_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Enhanced context data
            context_data = {
                "project_phase": target_phase.value,
                "phase_transition": f"{current_phase.value}_TO_{target_phase.value}",
                "planning_task_marker": True,
                "target_phase": target_phase.value,
                "completed_phase": current_phase.value,
                "phase_trigger_timestamp": datetime.now().isoformat(),
                "creation_type": "phase_transition",
                "unique_planning_id": unique_timestamp,
                "enhanced_planning_version": "2.0"
            }

            # Phase-specific task creation
            if target_phase == ProjectPhase.FINALIZATION:
                task_name = f"🎯 CRITICAL: Create Final Deliverables ({unique_timestamp})"
                description = f"""🎯 **FINAL PHASE PLANNING: PROJECT DELIVERABLES**

**CRITICAL PHASE TRANSITION:** {current_phase.value} → FINALIZATION

⚠️ **THIS IS THE PROJECT COMPLETION PHASE**
Create tasks that will produce the final project deliverables.

**🔴 MANDATORY REQUIREMENTS:**
1. **detailed_results_json MUST include:**
   - "current_project_phase": "FINALIZATION" 
   - "defined_sub_tasks": [array with 3+ deliverable tasks]

2. **Each sub-task MUST have:**
   - "project_phase": "FINALIZATION"
   - Clear deliverable outcome
   - Specific agent assignment

**📋 FINALIZATION TASK EXAMPLES:**
- "Create Final Instagram Content Calendar" → ContentSpecialist
- "Generate Complete Lead Contact Database" → AnalysisSpecialist
- "Compile Campaign Performance Dashboard" → MarketingSpecialist
- "Create Executive Summary Report" → ProjectManager

**Planning Session ID:** {unique_timestamp}
"""
                context_data["is_finalization_planning"] = True
                
            elif target_phase == ProjectPhase.IMPLEMENTATION:
                task_name = f"📋 IMPLEMENTATION: Strategy & Framework ({unique_timestamp})"
                description = f"""📋 **IMPLEMENTATION PHASE PLANNING**

**PHASE TRANSITION:** {current_phase.value} → IMPLEMENTATION

**🔧 FOCUS: Strategy, Frameworks, Templates & Workflows**

**📋 MANDATORY REQUIREMENTS:**
1. **detailed_results_json MUST include:**
   - "current_project_phase": "IMPLEMENTATION"
   - "defined_sub_tasks": [array with implementation tasks]

2. **Each sub-task MUST have:**
   - "project_phase": "IMPLEMENTATION"

**🛠️ IMPLEMENTATION TASK EXAMPLES:**
- "Develop Content Strategy Framework" → ContentSpecialist
- "Create Editorial Calendar Template" → ContentSpecialist
- "Design Campaign Automation Workflow" → MarketingSpecialist

**Planning Session ID:** {unique_timestamp}
"""
                context_data["is_implementation_planning"] = True
                
            else:
                logger.warning(f"No template for phase {target_phase.value}")
                return None

            # Create task
            planning_task = await create_task(
                workspace_id=workspace_id,
                agent_id=pm_agent["id"],
                name=task_name,
                description=description,
                status="pending",
                priority="high",
                creation_type="phase_transition",
                context_data=context_data
            )

            if planning_task and planning_task.get("id"):
                logger.info(f"✅ PLANNING CREATED: {planning_task['id']} for {target_phase.value}")
                return planning_task["id"]
            else:
                logger.error(f"❌ PLANNING FAILED for {target_phase.value}")
                return None

        except Exception as e:
            logger.error(f"Error creating phase planning task: {e}", exc_info=True)
            return None

    async def _find_project_manager(self, workspace_id: str) -> Optional[Dict]:
        """Find project manager with fallback logic"""
        try:
            agents = await list_agents(workspace_id)
            
            # Primary: Look for explicit Project Manager
            for agent in agents:
                if (agent.get("status") == "active" and 
                    "project manager" in (agent.get("role") or "").lower()):
                    return agent

            # Secondary: Look for management roles
            management_keywords = ["manager", "coordinator", "director", "lead", "pm"]
            for agent in agents:
                if agent.get("status") == "active":
                    role_lower = (agent.get("role") or "").lower()
                    if any(keyword in role_lower for keyword in management_keywords):
                        return agent

            # Tertiary: Senior agents
            senior_agents = [a for a in agents if a.get("status") == "active" and 
                           a.get("seniority") in ["expert", "senior"]]
            if senior_agents:
                return senior_agents[0]

            # Last resort: Any active agent
            active_agents = [a for a in agents if a.get("status") == "active"]
            if active_agents:
                return active_agents[0]

            logger.error(f"No suitable PM found in workspace {workspace_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding project manager: {e}")
            return None

    async def handle_project_manager_completion(
        self,
        task: Task, 
        result: Dict[str, Any],
        workspace_id: str
    ) -> bool:
        """
        Gestisce il completamento di task del Project Manager con validazione fasi integrata.
        """
        task_id_str = str(task.id)
        logger.info(f"TaskAnalyzer: Handling PM task completion: {task_id_str} ('{task.name}') for workspace {workspace_id}")

        # Extract and parse detailed_results_json
        detailed_results_json_str = result.get("detailed_results_json")
        if not detailed_results_json_str:
            logger.error(f"TaskAnalyzer: PM task {task_id_str} missing detailed_results_json in its result.")
            return False

        results_data = self._safe_json_loads(detailed_results_json_str)
        if not results_data:
            logger.error(f"TaskAnalyzer: PM task {task_id_str} failed to parse detailed_results_json.")
            return False

        # Validate current project phase
        current_project_phase_from_pm_str = results_data.get("current_project_phase")
        if not current_project_phase_from_pm_str:
            logger.error(f"TaskAnalyzer: PM task {task_id_str} output missing 'current_project_phase' key.")
            return False

        try:
            validated_phase_enum = PhaseManager.validate_phase(current_project_phase_from_pm_str)
            validated_phase_value = validated_phase_enum.value
            logger.info(f"PM specified phase: {current_project_phase_from_pm_str} -> validated: {validated_phase_value}")
        except Exception as e:
            logger.error(f"TaskAnalyzer: PM task {task_id_str} phase validation failed: {e}")
            return False

        # Extract and validate sub-tasks
        defined_sub_tasks_list = results_data.get("defined_sub_tasks", [])
        if not isinstance(defined_sub_tasks_list, list):
            logger.error(f"TaskAnalyzer: PM task {task_id_str} 'defined_sub_tasks' is not a list.")
            return False

        if not defined_sub_tasks_list:
            logger.info(f"TaskAnalyzer: PM task {task_id_str} did not define any sub-tasks.")
            return True 

        logger.info(f"TaskAnalyzer: PM task {task_id_str} defined {len(defined_sub_tasks_list)} sub-tasks for phase '{validated_phase_value}'.")

        # Prepare context for task creation
        agents_in_workspace = await list_agents(workspace_id)
        if not agents_in_workspace:
            logger.error(f"TaskAnalyzer: No agents found in workspace {workspace_id}.")
            return False

        # Pre-fetch all tasks for duplicate check
        all_tasks_in_db_for_dedup = await list_tasks(workspace_id=workspace_id)

        # Prepare delegation chain
        delegation_chain_from_pm_task = task.context_data.get("delegation_chain", []) if task.context_data else []
        if not isinstance(delegation_chain_from_pm_task, list):
            delegation_chain_from_pm_task = []

        # Counters and tracking
        created_by_analyzer_count = 0
        skipped_by_analyzer_count = 0
        phase_validation_errors = []

        # Process sub-tasks
        for sub_task_def in defined_sub_tasks_list:
            if not isinstance(sub_task_def, dict):
                logger.warning(f"TaskAnalyzer: Invalid sub_task_def format in PM output for task {task_id_str}.")
                continue

            # Extract base fields
            task_name = sub_task_def.get("name")
            task_description = sub_task_def.get("description")
            target_agent_name_from_pm = sub_task_def.get("target_agent_role") or ""
            priority = sub_task_def.get("priority", "medium").lower()

            # Validate required fields
            required_fields = ["name", "description", "target_agent_role"]
            missing_fields = [field for field in required_fields if not sub_task_def.get(field)]
            if missing_fields:
                logger.warning(f"TaskAnalyzer: Sub-task definition missing fields {missing_fields}. Skipping.")
                continue

            # Validate sub-task phase
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

            # Handle task_id provided by PM tool
            tool_created_task_id = sub_task_def.get("task_id")
            if tool_created_task_id:
                try:
                    existing_task = await get_task(tool_created_task_id)
                    if existing_task:
                        existing_task_name = existing_task.get("name")
                        current_task_name = sub_task_def.get("name")

                        if existing_task_name and current_task_name and existing_task_name.lower() == current_task_name.lower():
                            logger.info(f"TaskAnalyzer: PM task {task_id_str} correctly referenced sub-task ID '{tool_created_task_id}'.")
                            skipped_by_analyzer_count += 1
                            continue 
                        else:
                            logger.warning(f"TaskAnalyzer: Task ID '{tool_created_task_id}' name mismatch.")
                    else:
                        logger.warning(f"TaskAnalyzer: Task ID '{tool_created_task_id}' not found in database.")
                except Exception as e:
                    logger.warning(f"Error checking tool-created task {tool_created_task_id}: {e}")

            # Find target agent
            agent_to_assign = await self._find_agent_by_role(workspace_id, target_agent_name_from_pm)
            if not agent_to_assign:
                logger.warning(f"TaskAnalyzer: No suitable agent found for role '{target_agent_name_from_pm}'.")
                continue

            # Duplicate check
            is_duplicate_found_by_analyzer = False
            for t_db_dict in all_tasks_in_db_for_dedup:
                name_match = t_db_dict.get("name", "").lower() == task_name.lower()
                phase_match = (t_db_dict.get("context_data", {}).get("project_phase", "").upper() == sub_task_project_phase_value)

                target_agent_name_safe = (target_agent_name_from_pm or "").lower()
                assigned_role_db_safe = (t_db_dict.get("assigned_to_role") or "").lower()

                agent_match = (
                    t_db_dict.get("agent_id") == agent_to_assign["id"] or 
                    (target_agent_name_from_pm is not None and assigned_role_db_safe == target_agent_name_safe)
                )

                status_match = t_db_dict.get("status") in [TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value]
                origin_match = (
                    t_db_dict.get("parent_task_id") == task_id_str or 
                    t_db_dict.get("context_data", {}).get("source_pm_task_id") == task_id_str
                )

                if name_match and phase_match and agent_match and status_match and origin_match:
                    logger.warning(f"TaskAnalyzer: Sub-task '{task_name}' appears to be duplicate. Skipping.")
                    is_duplicate_found_by_analyzer = True
                    skipped_by_analyzer_count += 1
                    break

            if is_duplicate_found_by_analyzer:
                continue

            # Create sub-task
            logger.info(f"TaskAnalyzer: Creating sub-task '{task_name}' for agent '{agent_to_assign['name']}'.")

            # Context data for tracking
            sub_task_context = {
                "project_phase": sub_task_project_phase_value,
                "original_pm_phase_planner": validated_phase_value,
                "phase_validated": True,
                "phase_validation_timestamp": datetime.now().isoformat(),
                "source_pm_task_id": task_id_str,
                "source_pm_task_name": task.name,
                "created_by_task_analyzer": True,
                "auto_generated_by_pm_output": True,
                "pm_completion_timestamp": datetime.now().isoformat(),
                "creation_method": "pm_completion_analyzer",
                "delegation_chain": delegation_chain_from_pm_task + [task_id_str],
                "expected_completion_criteria": sub_task_def.get("completion_criteria", "Task completed successfully"),
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
                    logger.info(f"TaskAnalyzer: ✅ Successfully created sub-task '{created_db_task_dict['name']}' (ID: {created_db_task_dict['id']})")
                else:
                    logger.error(f"TaskAnalyzer: ❌ Failed to create sub-task '{task_name}' in DB.")

            except Exception as e:
                logger.error(f"TaskAnalyzer: Error creating sub-task '{task_name}': {e}", exc_info=True)

        # Final logging
        if phase_validation_errors:
            logger.warning(f"TaskAnalyzer: Phase validation corrections made for PM task {task_id_str}: {phase_validation_errors}")

        logger.info(f"TaskAnalyzer: PM task {task_id_str} completion processing finished.")
        logger.info(f"  └─ Definitions processed: {len(defined_sub_tasks_list)}")
        logger.info(f"  └─ Tasks created by analyzer: {created_by_analyzer_count}")
        logger.info(f"  └─ Tasks skipped: {skipped_by_analyzer_count}")
        logger.info(f"  └─ Phase corrections: {len(phase_validation_errors)}")
        logger.info(f"  └─ Target phase: {validated_phase_value}")

        # Structured logging for monitoring
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
            agents_from_db = await list_agents(workspace_id)
            if not agents_from_db:
                logger.warning(f"No agents in workspace {workspace_id}")
                return None

            # Normalize target role
            target_role_lower = role.lower().strip()
            target_role_normalized = target_role_lower.replace(" ", "")

            # Extract significant keywords
            common_words = {"specialist", "the", "and", "of", "for", "in", "a", "an"}
            target_role_words = set(word for word in target_role_lower.split() if word not in common_words)

            # Special flags
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

                # Exact matches
                if agent_role == target_role_lower:
                    score = 100
                    match_reason = "exact role match"
                elif agent_name == target_role_lower:
                    score = 95
                    match_reason = "exact name match"
                elif agent_role_normalized == target_role_normalized:
                    score = 90
                    match_reason = "normalized role match"
                elif agent_name.replace(" ", "") == target_role_normalized:
                    score = 85
                    match_reason = "normalized name match"
                elif target_role_lower in agent_role:
                    score = 80
                    match_reason = "target contained in agent role"
                elif target_role_lower in agent_name:
                    score = 75
                    match_reason = "target contained in agent name"
                elif agent_role in target_role_lower:
                    score = 70
                    match_reason = "agent role contained in target"
                elif target_role_words and (agent_role_words or agent_name_words):
                    # Semantic word overlap
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
                            match_reason = f"word overlap in {best_source}: {', '.join(best_common_words)}"

                elif is_target_manager and any(keyword in agent_role_normalized for keyword in 
                                             ["manager", "director", "lead", "coordinator", "pm"]):
                    score = 65
                    match_reason = "manager role match"
                else:
                    # Partial keyword matching
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

                # Seniority boost
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
                logger.info(f"✅ Agent match for '{role}': {best_match.get('name')} ({best_match.get('role')}) - Score: {candidates[0]['score']}")
                return best_match

            logger.error(f"❌ NO AGENT MATCH for role '{role}' after all strategies")
            return None

        except Exception as e:
            logger.error(f"Error finding agent by role: {e}", exc_info=True)
            return None

    async def _is_project_manager_task(self, task: Task, result: Dict[str, Any]) -> bool:
        """Determines if a task was completed by a Project Manager agent."""
        # Method 1: Check the actual agent role
        if task.agent_id:
            try:
                agent_data = await get_agent(str(task.agent_id))
                if agent_data:
                    role = agent_data.get('role', '').lower()
                    pm_roles = ['project manager', 'coordinator', 'director', 'lead', 'pm']
                    if any(pm_role in role for pm_role in pm_roles):
                        logger.info(f"Task {task.id} identified as PM task by agent role: {role}")
                        return True
                    else:
                        logger.info(f"Task {task.id} is NOT a PM task - executed by role: {role}")
                        return False
            except Exception as e:
                logger.warning(f"Could not check agent role for task {task.id}: {e}")

        # Method 2: Check for PM-specific output structure
        if isinstance(result.get("detailed_results_json"), str) and result.get("detailed_results_json").strip():
            try:
                parsed_json = self._safe_json_loads(result.get("detailed_results_json"))
                if isinstance(parsed_json, dict) and any(key in parsed_json for key in ["defined_sub_tasks", "sub_tasks", "subtasks"]):
                    logger.info(f"Task {task.id} identified as PM task by output structure")
                    return True
            except Exception:
                pass

        # Method 3: Specific keyword matching
        task_name = task.name.lower() if task.name else ""
        pm_planning_indicators = [
            "project setup", "strategic planning", "kick-off", "project assessment", 
            "phase planning", "team coordination"
        ]

        for indicator in pm_planning_indicators:
            if indicator in task_name:
                logger.info(f"Task {task.id} identified as PM task by name indicator: {indicator}")
                return True

        logger.debug(f"Task {task.id} NOT identified as PM task after all checks")
        return False

    async def _gather_minimal_context(self, workspace_id: str) -> Dict[str, Any]:
        """Gather minimal workspace context"""
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
                "completion_rate": len(completed) / len(tasks) if tasks else 0,
                "recent_completions": [
                    {"name": t.get("name", ""), "id": t.get("id", "")}
                    for t in completed[-5:]
                ],
            }
            
        except Exception as e:
            logger.error(f"Error gathering context: {e}")
            return {"total_tasks": 0, "completed_tasks": 0, "pending_tasks": 0}

    # ---------------------------------------------------------------------
    # Additional methods from comprehensive version
    # ---------------------------------------------------------------------
    
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

    def get_status(self) -> Dict[str, Any]:
        """Get enhanced status"""
        return {
            "enhanced_version": "2.0",
            "auto_generation_enabled": self.auto_generation_enabled,
            "phase_tracking_enabled": ENABLE_ENHANCED_PHASE_TRACKING,
            "tracking_state": {
                "phase_planning_tracker_size": len(self.phase_planning_tracker),
                "last_planning_times": len(self.last_planning_time),
                "analyzed_tasks_count": len(self.analyzed_tasks)
            },
            "configuration": {
                "cooldown_minutes": self.cooldown_minutes,
                "max_pending_for_transition": MAX_PENDING_TASKS_FOR_TRANSITION,
                "confidence_threshold": self.confidence_threshold
            },
            "uptime_hours": (datetime.now() - self.initialization_time).total_seconds() / 3600
        }

    async def cleanup_enhanced_tracking(self):
        """Enhanced cleanup"""
        try:
            async with self._tracking_lock:
                current_time = datetime.now()
                
                # Cleanup old planning times
                expired_planning = [
                    ws_id for ws_id, timestamp in self.last_planning_time.items()
                    if current_time - timestamp > timedelta(hours=24)
                ]
                
                for ws_id in expired_planning:
                    del self.last_planning_time[ws_id]
                    if ws_id in self.phase_planning_tracker:
                        del self.phase_planning_tracker[ws_id]
                
                # Cleanup analyzed tasks
                if len(self.analyzed_tasks) > 1000:
                    self.analyzed_tasks = set(list(self.analyzed_tasks)[-500:])
                
                self.last_cleanup = current_time
                logger.info(f"Enhanced cleanup completed")
        
        except Exception as e:
            logger.error(f"Error in enhanced cleanup: {e}")

# Global instance management
_enhanced_executor_instance = None

def get_enhanced_task_executor() -> EnhancedTaskExecutor:
    """Get singleton instance"""
    global _enhanced_executor_instance
    if _enhanced_executor_instance is None:
        _enhanced_executor_instance = EnhancedTaskExecutor()
    return _enhanced_executor_instance

def reset_enhanced_task_executor():
    """Reset singleton instance"""
    global _enhanced_executor_instance
    _enhanced_executor_instance = None
    logger.info("Enhanced task executor instance reset")

# Export all necessary classes and functions
__all__ = [
    'PhaseManager', 'EnhancedTaskExecutor', 'PhaseManagerError',
    'get_enhanced_task_executor', 'reset_enhanced_task_executor'
]