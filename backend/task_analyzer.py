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
    update_workspace_status, get_agent, update_task_status,
    # 🎯 Goal-driven database functions
    update_goal_progress, get_workspace_goals
)
# from UniversalAIContentExtractor import UniversalAIContentExtractor  # Module removed
# from AISemanticMapper import AISemanticMapper  # Module removed

logger = logging.getLogger(__name__)

# Configuration from environment
# 🤖 AI-DRIVEN: These values can now be adaptive based on workspace context
ENABLE_AI_ADAPTIVE_PHASE_MANAGEMENT = os.getenv("ENABLE_AI_ADAPTIVE_PHASE_MANAGEMENT", "true").lower() == "true"

# Fallback static values
PHASE_PLANNING_COOLDOWN_MINUTES = int(os.getenv("PHASE_PLANNING_COOLDOWN_MINUTES", "5"))
MAX_PENDING_TASKS_FOR_TRANSITION = int(os.getenv("MAX_PENDING_TASKS_FOR_TRANSITION", "15"))
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

    async def should_transition_to_next_phase(self, workspace_id: str) -> tuple[ProjectPhase, Optional[ProjectPhase]]:
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
            
            # 🚀 ATOE: Use Adaptive Task Orchestration Engine for phase transition thresholds
            transition_thresholds = await self._get_adaptive_phase_transition_thresholds(workspace_id, phase_counts, pending_phase_counts)
            
            # If FINALIZATION completed -> project finished
            if phase_counts[ProjectPhase.FINALIZATION] >= transition_thresholds["finalization_completion_min"]:
                return ProjectPhase.COMPLETED, None

            # For FINALIZATION: need IMPLEMENTATION + reasonable completion
            if (phase_counts[ProjectPhase.IMPLEMENTATION] >= transition_thresholds["implementation_for_finalization"] and 
                phase_counts[ProjectPhase.ANALYSIS] >= transition_thresholds["analysis_for_finalization"] and
                pending_phase_counts[ProjectPhase.FINALIZATION] <= transition_thresholds["max_pending_finalization"] and
                "FINALIZATION" not in planning_phases_executed and
                "FINALIZATION" not in pending_planning_phases):

                logger.info(f"🚀 READY FOR FINALIZATION: {workspace_id}")
                return ProjectPhase.IMPLEMENTATION, ProjectPhase.FINALIZATION

            # For IMPLEMENTATION: need ANALYSIS + no conflicts
            if (phase_counts[ProjectPhase.ANALYSIS] >= transition_thresholds["analysis_for_implementation"] and 
                pending_phase_counts[ProjectPhase.IMPLEMENTATION] <= transition_thresholds["max_pending_implementation"] and
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
    async def _get_adaptive_phase_transition_thresholds(
        workspace_id: str, 
        phase_counts: Dict, 
        pending_phase_counts: Dict
    ) -> Dict[str, int]:
        """🚀 ATOE: Get adaptive phase transition thresholds with AI-driven orchestration"""
        
        # Fallback static thresholds
        static_thresholds = {
            "finalization_completion_min": 2,
            "implementation_for_finalization": 1,
            "analysis_for_finalization": 1,
            "max_pending_finalization": 3,
            "analysis_for_implementation": 1,
            "max_pending_implementation": 3
        }
        
        if not ENABLE_AI_ADAPTIVE_PHASE_MANAGEMENT:
            return static_thresholds
        
        # 🚀 ATOE: Try Adaptive Task Orchestration Engine first
        try:
            from services.unified_orchestrator import get_unified_orchestrator
            atoe = get_unified_orchestrator()
            
            if atoe:
                # Get ATOE-based adaptive thresholds
                atoe_thresholds = await atoe.get_adaptive_phase_thresholds(
                    workspace_id=workspace_id,
                    current_phase_counts=phase_counts,
                    pending_phase_counts=pending_phase_counts
                )
                
                if atoe_thresholds:
                    logger.info(f"🚀 ATOE phase thresholds for W:{workspace_id[:8]}: {atoe_thresholds}")
                    return atoe_thresholds
                    
        except Exception as e:
            logger.warning(f"ATOE phase threshold calculation failed, using AI fallback: {e}")
        
        try:
            # Initialize OpenAI client if available
            openai_client = None
            if os.getenv("OPENAI_API_KEY"):
                try:
                    from openai import AsyncOpenAI
                    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                except ImportError:
                    pass
            
            if not openai_client:
                return static_thresholds
            
            # Get workspace context
            try:
                from database import get_workspace
                workspace = await get_workspace(workspace_id)
                project_description = workspace.get("description", "" if workspace else "")
                
                # Calculate workspace complexity indicators
                total_completed = sum(phase_counts.values())
                total_pending = sum(pending_phase_counts.values())
                complexity_score = total_completed + total_pending
                
            except Exception:
                project_description = ""
                complexity_score = 5  # Default medium complexity
            
            ai_prompt = f"""
            Determine appropriate phase transition thresholds for this project:
            
            Project Description: {project_description[:200]}...
            Total Completed Tasks: {sum(phase_counts.values())}
            Total Pending Tasks: {sum(pending_phase_counts.values())}
            Complexity Score: {complexity_score}
            
            Current Phase Distribution:
            - Analysis: {phase_counts.get('ANALYSIS', 0)} completed, {pending_phase_counts.get('ANALYSIS', 0)} pending
            - Implementation: {phase_counts.get('IMPLEMENTATION', 0)} completed, {pending_phase_counts.get('IMPLEMENTATION', 0)} pending
            - Finalization: {phase_counts.get('FINALIZATION', 0)} completed, {pending_phase_counts.get('FINALIZATION', 0)} pending
            
            Return JSON with adaptive thresholds:
            - finalization_completion_min: Min finalization tasks to consider project complete (1-4)
            - implementation_for_finalization: Min implementation tasks needed before finalization (1-3)
            - analysis_for_finalization: Min analysis tasks needed before finalization (1-2)
            - max_pending_finalization: Max pending finalization tasks to allow new ones (2-6)
            - analysis_for_implementation: Min analysis tasks needed before implementation (1-2)
            - max_pending_implementation: Max pending implementation tasks to allow new ones (2-6)
            
            Consider:
            - Complex projects need higher thresholds
            - Small projects can have lower requirements
            - If many tasks are pending, be more conservative
            
            Format: {{"finalization_completion_min": 2, "implementation_for_finalization": 1, ...}}
            """
            
            response = await openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at project phase management and adaptive thresholds. Provide only valid JSON output."},
                    {"role": "user", "content": ai_prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            ai_result = response.choices[0].message.content.strip()
            import json
            adaptive_thresholds = json.loads(ai_result)
            
            # Validate and bound the values
            for key, fallback_value in static_thresholds.items():
                if key not in adaptive_thresholds:
                    adaptive_thresholds[key] = fallback_value
                else:
                    # Ensure values are within reasonable bounds
                    if "completion_min" in key or "for_" in key:
                        adaptive_thresholds[key] = max(1, min(4, adaptive_thresholds[key]))
                    elif "max_pending" in key:
                        adaptive_thresholds[key] = max(2, min(10, adaptive_thresholds[key]))
            
            logger.info(f"✅ AI-adaptive phase thresholds calculated for workspace {workspace_id}")
            return adaptive_thresholds
            
        except Exception as e:
            logger.warning(f"AI adaptive phase thresholds failed: {e}")
            return static_thresholds

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
        """Return dictionary representation of the analysis output"""
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

        # Instantiate PhaseManager
        self.phase_manager = PhaseManager()
        
        logger.critical("🔧 ENHANCED TASK EXECUTOR CONFIGURATION")
        logger.critical(f"auto_generation_enabled: {self.auto_generation_enabled}")
        logger.critical(f"analysis_enabled: {self.analysis_enabled}")
        
        # Force enable se env variable settata
        if os.getenv("FORCE_DEBUG_AUTO_GENERATION", "false").lower() == "true":
            self.auto_generation_enabled = True
            self.analysis_enabled = True
        
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
        
    def _should_analyze_task_for_assets(self, task: Task, result: Dict[str, Any]) -> bool:
        """
        Determina se un task completato dovrebbe essere analizzato per asset extraction
        """

        if result.get("status") != "completed":
            return False

        # Controlla marker di asset production
        context_data = task.context_data or {}
        if isinstance(context_data, dict):
            if (context_data.get("asset_production") or 
                context_data.get("asset_oriented_task")):
                return True

        # Controlla nome del task
        task_name = task.name.lower() if task.name else ""
        if "produce asset:" in task_name or "asset production:" in task_name:
            return True

        # Controlla se ha structured output significativo
        detailed_json = result.get("detailed_results_json", "")
        if detailed_json and len(detailed_json) > 200:
            try:
                data = json.loads(detailed_json)
                if isinstance(data, dict) and len(data) >= 3:
                    # Ha structured data, potenzialmente asset
                    return True
            except json.JSONDecodeError:
                pass

        return False

    def _is_enhancement_task(self, task: Task) -> bool:
        """Check if this is an enhancement task that shouldn't trigger new deliverables"""
        context_data = task.context_data or {}
        if isinstance(context_data, dict):
            # Check for enhancement markers in context_data
            if (context_data.get("asset_enhancement_task") or
                context_data.get("enhancement_coordination") or
                context_data.get("ai_guided_enhancement")):
                return True
        
        # Check task name for enhancement keywords
        task_name = (task.name or "").lower()
        return (
            "enhance:" in task_name or
            "enhancement" in task_name or
            "quality" in task_name and "enhancement" in task_name
        )

    async def _handle_goal_progress_update(
        self, 
        completed_task: Task, 
        task_result: Dict[str, Any], 
        workspace_id: str
    ) -> None:
        """
        🎯 GOAL-DRIVEN: Handle automatic goal progress update when goal-driven tasks complete
        
        This is called FIRST when any task completes to update goal progress
        if the task contributes to a workspace goal.
        """
        try:
            # Check if this is a goal-driven task
            goal_id = getattr(completed_task, 'goal_id', None)
            metric_type = getattr(completed_task, 'metric_type', None)
            contribution_expected = getattr(completed_task, 'contribution_expected', None)
            
            # Also check context_data for goal information
            context_data = getattr(completed_task, 'context_data', {}) or {}
            if isinstance(context_data, dict):
                goal_id = goal_id or context_data.get('goal_id')
                metric_type = metric_type or context_data.get('metric_type')
                contribution_expected = contribution_expected or context_data.get('contribution_expected')
            
            if not goal_id:
                # Not a goal-driven task, skip
                logger.debug(f"Task {completed_task.id} is not goal-driven, skipping goal progress update")
                return
            
            # Determine actual contribution from task result
            actual_contribution = self._calculate_actual_contribution(
                completed_task, task_result, metric_type, contribution_expected
            )
            
            if actual_contribution <= 0:
                logger.warning(f"Goal-driven task {completed_task.id} completed but no measurable contribution detected")
                return
            
            # 🎯 ENHANCED: Create business context for goal progress update
            task_business_context = await self._create_task_business_context(
                completed_task, task_result, actual_contribution
            )
            
            # Update goal progress with business context
            updated_goal = await update_goal_progress(
                goal_id=str(goal_id),
                increment=actual_contribution,
                task_id=str(completed_task.id),
                task_business_context=task_business_context
            )
            
            if updated_goal:
                completion_pct = (updated_goal['current_value'] / updated_goal['target_value'] * 100) if updated_goal['target_value'] > 0 else 0
                
                logger.info(
                    f"🎯 GOAL UPDATE: Task {completed_task.id} contributed {actual_contribution} to "
                    f"goal {metric_type} ({updated_goal['current_value']}/{updated_goal['target_value']} - {completion_pct:.1f}%)"
                )
                
                # Log goal achievement if completed
                if updated_goal.get('status') == 'completed':
                    logger.info(f"🎯 GOAL ACHIEVED: {metric_type} goal completed with task {completed_task.id}!")
                    
                    # Store achievement insight in workspace memory
                    try:
                        from workspace_memory import workspace_memory
                        from models import InsightType
                        from uuid import UUID
                        
                        await workspace_memory.store_insight(
                            workspace_id=UUID(workspace_id),
                            task_id=completed_task.id,
                            agent_role="goal_tracker",
                            insight_type=InsightType.SUCCESS_PATTERN,
                            content=f"Goal {metric_type} achieved: {updated_goal['current_value']} {updated_goal.get('unit', 'units')} completed",
                            relevance_tags=[f"goal_{goal_id}", f"metric_{metric_type}", "goal_achievement"],
                            confidence_score=1.0
                        )
                    except Exception as e:
                        logger.warning(f"Failed to store goal achievement insight: {e}")
            else:
                logger.error(f"Failed to update goal progress for task {completed_task.id}")
                
        except Exception as e:
            logger.error(f"Error handling goal progress update for task {completed_task.id}: {e}", exc_info=True)
    
    async def _create_task_business_context(
        self, 
        completed_task: Task, 
        task_result: Dict[str, Any], 
        contribution: float
    ) -> Dict[str, Any]:
        """
        🎯 ENHANCED: Create business context for goal progress calculation
        
        Rispetta PILLAR 2 (Universal Business Domains) - analyzes business value universally.
        """
        try:
            context = {
                "task_id": str(completed_task.id),
                "has_business_content": False,
                "content_type": "unknown",
                "task_result_summary": "",
                "business_value_indicators": []
            }
            
            # Analyze task result for business content
            result_summary = task_result.get("summary", "")
            context["task_result_summary"] = result_summary
            
            # Check for high-value business content indicators
            if task_result.get("detailed_results_json"):
                try:
                    detailed = json.loads(task_result["detailed_results_json"]) if isinstance(task_result["detailed_results_json"], str) else task_result["detailed_results_json"]
                    
                    # Rendered content indicates high business value
                    if detailed.get("rendered_html"):
                        context["has_business_content"] = True
                        context["content_type"] = "rendered_html"
                        context["business_value_indicators"].append("rendered_html_content")
                        
                    # Structured content indicates medium-high business value  
                    if detailed.get("structured_content"):
                        context["has_business_content"] = True
                        if context["content_type"] == "unknown":
                            context["content_type"] = "structured_content"
                        context["business_value_indicators"].append("structured_content")
                        
                    # Deliverable content indicates direct business value
                    if detailed.get("deliverable_content") or detailed.get("business_content"):
                        context["has_business_content"] = True
                        context["content_type"] = "business_document"
                        context["business_value_indicators"].append("deliverable_content")
                        
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Analyze summary for business value keywords
            if result_summary:
                business_keywords = [
                    "document created", "content generated", "strategy developed",
                    "analysis completed", "deliverable produced", "template created",
                    "plan finalized", "framework established", "content delivered"
                ]
                
                low_value_keywords = [
                    "sub-task has been created", "task has been assigned",
                    "analysis will be conducted", "plan has been created"
                ]
                
                for keyword in business_keywords:
                    if keyword in result_summary.lower():
                        context["has_business_content"] = True
                        context["business_value_indicators"].append(f"keyword:{keyword}")
                        break
                
                for keyword in low_value_keywords:
                    if keyword in result_summary.lower():
                        context["business_value_indicators"].append(f"low_value:{keyword}")
                        break
            
            # Additional context from task metadata
            task_context_data = getattr(completed_task, 'context_data', {}) or {}
            if isinstance(task_context_data, dict):
                # Check if task was marked as deliverable-producing
                if task_context_data.get("deliverable_type"):
                    context["has_business_content"] = True
                    context["business_value_indicators"].append(f"deliverable_type:{task_context_data['deliverable_type']}")
                
                # Check success criteria for business indicators
                success_criteria = task_context_data.get("success_criteria", [])
                if success_criteria:
                    for criterion in success_criteria:
                        if any(word in str(criterion).lower() for word in ["deliver", "create", "produce", "generate"]):
                            context["business_value_indicators"].append("success_criteria_business_focused")
                            break
            
            logger.debug(f"📊 Task {completed_task.id} business context: {context['has_business_content']}, type: {context['content_type']}, indicators: {len(context['business_value_indicators'])}")
            
            return context
            
        except Exception as e:
            logger.error(f"Error creating task business context: {e}")
            return {
                "task_id": str(completed_task.id),
                "has_business_content": False,
                "content_type": "error",
                "task_result_summary": "",
                "business_value_indicators": ["context_creation_error"]
            }

    def _calculate_actual_contribution(
        self, 
        completed_task: Task, 
        task_result: Dict[str, Any], 
        metric_type: Optional[str], 
        expected_contribution: Optional[float]
    ) -> float:
        """
        Calculate actual contribution from task result based on metric type
        
        This analyzes the task result to determine how much the task actually
        contributed to the goal (which may differ from expected_contribution).
        """
        try:
            if not metric_type:
                return expected_contribution or 0
            
            # For contacts metric: count actual contacts found
            if metric_type == "contacts":
                contacts_found = self._count_contacts_in_result(task_result)
                if contacts_found > 0:
                    logger.info(f"Task {completed_task.id} found {contacts_found} contacts")
                    return contacts_found
            
            # For email_sequences metric: count sequences created
            elif metric_type == "email_sequences":
                sequences_found = self._count_email_sequences_in_result(task_result)
                if sequences_found > 0:
                    logger.info(f"Task {completed_task.id} created {sequences_found} email sequences")
                    return sequences_found
            
            # For content metric: count content pieces
            elif metric_type == "content":
                content_pieces = self._count_content_pieces_in_result(task_result)
                if content_pieces > 0:
                    logger.info(f"Task {completed_task.id} created {content_pieces} content pieces")
                    return content_pieces
            
            # For campaigns metric: count campaigns
            elif metric_type == "campaigns":
                campaigns_found = self._count_campaigns_in_result(task_result)
                if campaigns_found > 0:
                    logger.info(f"Task {completed_task.id} created {campaigns_found} campaigns")
                    return campaigns_found
            
            # Default: use expected contribution if no specific analysis possible
            logger.debug(f"Using expected contribution {expected_contribution} for metric {metric_type}")
            return expected_contribution or 0
            
        except Exception as e:
            logger.error(f"Error calculating actual contribution: {e}")
            return expected_contribution or 0

    def _count_contacts_in_result(self, task_result: Dict[str, Any]) -> int:
        """Count actual contacts in task result"""
        try:
            # Look in actionable_assets for contacts
            actionable_assets = task_result.get('actionable_assets', {})
            if isinstance(actionable_assets, dict):
                for asset_name, asset_data in actionable_assets.items():
                    if 'contact' in asset_name.lower():
                        if isinstance(asset_data, dict) and 'data' in asset_data:
                            data = asset_data['data']
                            if isinstance(data, dict) and 'contacts' in data:
                                contacts = data['contacts']
                                if isinstance(contacts, list):
                                    # Count contacts with email addresses
                                    valid_contacts = 0
                                    for contact in contacts:
                                        if isinstance(contact, dict) and contact.get('email'):
                                            valid_contacts += 1
                                    return valid_contacts
            
            # Look in detailed_results_json
            detailed_json = task_result.get('detailed_results_json', '')
            if detailed_json:
                try:
                    data = json.loads(detailed_json)
                    if isinstance(data, dict) and 'contacts' in data:
                        contacts = data['contacts']
                        if isinstance(contacts, list):
                            return len([c for c in contacts if isinstance(c, dict) and c.get('email')])
                except json.JSONDecodeError:
                    pass
            
            return 0
        except Exception as e:
            logger.error(f"Error counting contacts: {e}")
            return 0

    def _count_email_sequences_in_result(self, task_result: Dict[str, Any]) -> int:
        """Count email sequences in task result"""
        try:
            # Look for email sequences in actionable_assets
            actionable_assets = task_result.get('actionable_assets', {})
            if isinstance(actionable_assets, dict):
                sequence_count = 0
                for asset_name, asset_data in actionable_assets.items():
                    if 'email' in asset_name.lower() and 'sequence' in asset_name.lower():
                        sequence_count += 1
                
                if sequence_count > 0:
                    return sequence_count
            
            # Look in detailed results for sequences
            detailed_json = task_result.get('detailed_results_json', '')
            if detailed_json:
                try:
                    data = json.loads(detailed_json)
                    if isinstance(data, dict):
                        if 'email_sequences' in data:
                            sequences = data['email_sequences']
                            if isinstance(sequences, list):
                                return len(sequences)
                        elif 'sequences' in data:
                            sequences = data['sequences']
                            if isinstance(sequences, list):
                                return len(sequences)
                except json.JSONDecodeError:
                    pass
            
            return 0
        except Exception as e:
            logger.error(f"Error counting email sequences: {e}")
            return 0

    def _count_content_pieces_in_result(self, task_result: Dict[str, Any]) -> int:
        """Count content pieces in task result"""
        try:
            actionable_assets = task_result.get('actionable_assets', {})
            if isinstance(actionable_assets, dict):
                content_count = 0
                for asset_name in actionable_assets.keys():
                    if 'content' in asset_name.lower() or 'blog' in asset_name.lower() or 'article' in asset_name.lower():
                        content_count += 1
                return content_count
            return 0
        except Exception as e:
            logger.error(f"Error counting content pieces: {e}")
            return 0

    def _count_campaigns_in_result(self, task_result: Dict[str, Any]) -> int:
        """Count campaigns in task result"""
        try:
            actionable_assets = task_result.get('actionable_assets', {})
            if isinstance(actionable_assets, dict):
                campaign_count = 0
                for asset_name in actionable_assets.keys():
                    if 'campaign' in asset_name.lower():
                        campaign_count += 1
                return campaign_count
            return 0
        except Exception as e:
            logger.error(f"Error counting campaigns: {e}")
            return 0

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
            # 🎯 GOAL-DRIVEN: Handle goal progress update first
            await self._handle_goal_progress_update(completed_task, task_result, workspace_id)
            
            # 🧠 MEMORY-DRIVEN: Extract actionable insights from task completion
            await self._handle_memory_intelligence_extraction(completed_task, task_result, workspace_id)
            
            # Determine task type
            is_pm_task = await self._is_project_manager_task(completed_task, task_result)

            if is_pm_task:
                logger.info(f"Processing PM task: {task_id_str}")
                # PM tasks always create sub-tasks
                pm_created_tasks = await self.handle_project_manager_completion(completed_task, task_result, workspace_id)

                # After PM task completion, check for final deliverable with circuit breaker protection
                try:
                    async def _safe_deliverable_creation():
                        from deliverable_system.unified_deliverable_engine import check_and_create_final_deliverable
                        return await check_and_create_final_deliverable(workspace_id)
                    
                    # Use circuit breaker if available
                    try:
                        from executor import task_executor
                        final_deliverable_id = await task_executor._execute_with_circuit_breaker(_safe_deliverable_creation)
                    except ImportError:
                        # Fallback without circuit breaker
                        final_deliverable_id = await _safe_deliverable_creation()
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

            # SPECIALIST FLOW
            logger.info(f"Processing specialist task: {task_id_str}")

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
            # === ASSET ANALYSIS (AI-DRIVEN) ===
            try:
                if self._should_analyze_task_for_assets(completed_task, task_result):
                    logger.info(f"🎯 AI ASSET ANALYSIS: Analyzing task {completed_task.id} for concrete content and goal mapping")

                    # Initialize AI content extractor and semantic mapper
                    content_extractor = UniversalAIContentExtractor()
                    semantic_mapper = AISemanticMapper()

                    # 1. Extract concrete content
                    extracted_content = await content_extractor.extract_content(task_result)

                    if extracted_content:
                        logger.info(f"🎯 AI ASSET ANALYSIS: Extracted concrete content from task {completed_task.id}")

                        # 2. Fetch workspace goals
                        workspace_goals = await get_workspace_goals(workspace_id)
                        
                        if workspace_goals:
                            # 3. Map extracted content to goals
                            mapped_contributions = await semantic_mapper.map_content_to_goals(
                                extracted_content,
                                workspace_goals
                            )

                            if mapped_contributions:
                                logger.info(f"🎯 AI ASSET ANALYSIS: Mapped content to {len(mapped_contributions)} goals for task {completed_task.id}")
                                # 4. Update goal progress based on AI-driven contributions
                                for contribution_data in mapped_contributions:
                                    goal_id = contribution_data.get("goal_id")
                                    contribution_percentage = contribution_data.get("contribution_percentage", 0)
                                    reasoning = contribution_data.get("reasoning", "AI-driven contribution")

                                    # Convert percentage to an increment value based on target_value
                                    # Find the actual goal object to get its target_value
                                    target_goal = next((g for g in workspace_goals if str(g.get("id")) == goal_id), None)
                                    
                                    if target_goal and target_goal.get("target_value") > 0:
                                        increment_value = (contribution_percentage / 100.0) * target_goal["target_value"]
                                        
                                        # Ensure increment is positive and meaningful
                                        if increment_value > 0:
                                            updated_goal = await update_goal_progress(
                                                goal_id=goal_id,
                                                increment=increment_value,
                                                task_id=str(completed_task.id),
                                                task_business_context={
                                                    "ai_extracted_content": extracted_content,
                                                    "ai_mapped_contribution": contribution_data,
                                                    "reasoning": reasoning
                                                }
                                            )
                                            if updated_goal:
                                                logger.info(f"🎯 GOAL PROGRESS: Updated goal {goal_id} by {increment_value} based on AI analysis. New value: {updated_goal.get('current_value')}")
                                            else:
                                                logger.warning(f"Failed to update goal {goal_id} progress for task {completed_task.id}")
                                        else:
                                            logger.debug(f"AI suggested 0 or negative increment for goal {goal_id}. Skipping update.")
                                    else:
                                        logger.warning(f"Could not find target goal {goal_id} or target_value is zero for task {completed_task.id}")
                            else:
                                logger.info(f"🎯 AI ASSET ANALYSIS: No significant contributions mapped to goals for task {completed_task.id}")
                        else:
                            logger.info(f"🎯 AI ASSET ANALYSIS: No workspace goals defined for workspace {workspace_id}. Skipping goal mapping.")
                    else:
                        logger.info(f"🎯 AI ASSET ANALYSIS: No concrete content extracted from task {completed_task.id}")

                    # Log asset task completion for monitoring
                    await self._log_completion_analysis(
                        completed_task, 
                        task_result, 
                        "asset_task_completed_ai_analyzed",
                        f"Asset-oriented task completed. AI extracted: {bool(extracted_content)}, AI mapped: {bool(mapped_contributions)}"
                    )

                    # Check if this completes the requirements for deliverable
                    asset_completion_triggered = await self._check_asset_completion_trigger(workspace_id)
                    if asset_completion_triggered:
                        logger.info(f"🎯 ASSET TRIGGER: Asset completion may trigger deliverable for {workspace_id}")

            except Exception as e:
                logger.error(f"Error in AI asset analysis for task {completed_task.id}: {e}", exc_info=True)           
            
            # After every specialist task, check for final deliverable (but not for enhancement tasks)
            if not self._is_enhancement_task(completed_task):
                try:
                    async def _safe_deliverable_creation():
                        from deliverable_system.unified_deliverable_engine import check_and_create_final_deliverable
                        return await check_and_create_final_deliverable(workspace_id)
                    
                    # Use circuit breaker if available
                    try:
                        from executor import task_executor
                        final_deliverable_id = await task_executor._execute_with_circuit_breaker(_safe_deliverable_creation)
                    except ImportError:
                        # Fallback without circuit breaker
                        final_deliverable_id = await _safe_deliverable_creation()
                    if final_deliverable_id:
                        logger.info(f"🎯 Specialist task completion triggered final deliverable: {final_deliverable_id}")
                        await self._log_completion_analysis(
                            completed_task, task_result, "specialist_triggered_final_deliverable",
                            f"Created final deliverable: {final_deliverable_id}"
                        )
                except Exception as e:
                    logger.error(f"Error checking final deliverable after specialist task: {e}")
            else:
                logger.info(f"🔧 ENHANCEMENT TASK: Skipping deliverable check for enhancement task: {completed_task.name}")

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
            current_phase, should_create_for_phase = await self.phase_manager.should_transition_to_next_phase(workspace_id)

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

            # FIXED: Phase-specific task creation with valid priorities
            if target_phase == ProjectPhase.FINALIZATION:
                # FIXED: Remove "CRITICAL" from task name to avoid priority validation issues
                task_name = f"🎯 FINALIZATION: Create Final Deliverables ({unique_timestamp})"
                task_priority = "high"  # FIXED: Use valid priority instead of "critical"

                description = f"""🎯 **FINAL PHASE PLANNING: PROJECT DELIVERABLES**

    **PHASE TRANSITION:** {current_phase.value} → FINALIZATION

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
                task_priority = "high"  # FIXED: Use valid priority

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

            # FIXED: Create task with explicit valid priority
            planning_task = await create_task(
                workspace_id=workspace_id,
                agent_id=pm_agent["id"],
                name=task_name,
                description=description,
                status="pending",
                priority=task_priority, 
                creation_type="phase_transition",
                context_data=context_data
            )

            if planning_task and planning_task.get("id"):
                logger.info(f"✅ PLANNING CREATED: {planning_task['id']} for {target_phase.value} with priority '{task_priority}'")
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

    def _validate_task_id(self, task_id: str) -> bool:
        """Valida formato UUID del task ID"""
        try:
            from uuid import UUID
            UUID(task_id)
            return True
        except (ValueError, TypeError):
            logger.error(f"Invalid task ID format: {task_id}")
            return False
    
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
            logger.warning(
                f"TaskAnalyzer: PM task {task_id_str} missing detailed_results_json in its result."
            )
            results_data = {}
        else:
            results_data = self._safe_json_loads(detailed_results_json_str)
            if not results_data:
                logger.warning(
                    f"TaskAnalyzer: PM task {task_id_str} failed to parse detailed_results_json."
                )
                results_data = {}

        # Validate current project phase
        current_project_phase_from_pm_str = results_data.get("current_project_phase")
        if not current_project_phase_from_pm_str:
            # Fallback: dedurre dalla fase del task corrente
            task_context = task.context_data or {}
            if isinstance(task_context, dict):
                fallback_phase = task_context.get("project_phase", "IMPLEMENTATION")
                logger.warning(f"PM task {task_id_str} missing current_project_phase, using fallback: {fallback_phase}")
                current_project_phase_from_pm_str = fallback_phase
            else:
                logger.error(f"PM task {task_id_str} missing current_project_phase and no fallback available")
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
                    if not self._validate_task_id(tool_created_task_id):
                        logger.warning(f"Skipping invalid task ID: {tool_created_task_id}")
                        continue
                        
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
        await self._post_pm_completion_asset_check(task, result, workspace_id)

        return created_by_analyzer_count > 0

    async def _post_pm_completion_asset_check(
        self, 
        task: Task, 
        result: Dict[str, Any], 
        workspace_id: str
    ):
        """
        Post-processing dopo PM completion per verificare necessità di asset-oriented tasks
        """

        try:
            # Controlla se il PM ha creato task che potrebbero beneficiare di asset orientation
            recent_tasks = await list_tasks(workspace_id)

            # Filtra task creati dal PM recentemente
            pm_created_tasks = [
                t for t in recent_tasks 
                if (t.get("created_by_task_id") == str(task.id) or 
                    t.get("parent_task_id") == str(task.id)) and
                    t.get("status") in ["pending", "in_progress"]
            ]

            if pm_created_tasks:
                logger.info(f"🎯 POST-PM CHECK: Analyzing {len(pm_created_tasks)} PM-created tasks for asset potential")

                # Analizza e marca task che dovrebbero produrre asset
                for pm_task in pm_created_tasks:
                    await self._enhance_task_for_asset_production(pm_task, workspace_id)

        except Exception as e:
            logger.warning(f"Post-PM asset check failed: {e}")

    async def _enhance_task_for_asset_production(self, task_dict: Dict, workspace_id: str):
        """
        Analizza un task e lo marca per asset production se appropriato
        """

        task_name = (task_dict.get("name") or "").lower()
        task_description = (task_dict.get("description") or "").lower()

        # ENHANCED: Pattern che indicano necessità di asset production con focus concreto
        asset_patterns = {
            "contact_database": [
                r"find.*contact", r"generate.*lead", r"prospect.*list", 
                r"contact.*database", r"lead.*generation", r"client.*list"
            ],
            "content_calendar": [
                r"content.*calendar", r"post.*schedule", r"social.*media.*plan",
                r"content.*strategy", r"editorial.*calendar", r"instagram.*plan",
                r"social.*post", r"content.*creation"
            ],
            "editorial_plan": [
                r"editorial.*plan", r"piano.*editoriale", r"content.*plan", 
                r"instagram.*editorial", r"social.*editorial", r"post.*planning",
                r"content.*scheduling", r"social.*content.*plan"
            ],
            "training_program": [
                r"training.*program", r"workout.*plan", r"exercise.*routine",
                r"fitness.*program", r"training.*schedule", r"workout.*schedule"
            ],
            "financial_model": [
                r"financial.*model", r"budget.*plan", r"cost.*analysis",
                r"revenue.*projection", r"financial.*planning"
            ]
        }

        # Cerca pattern nei task
        detected_asset_type = None
        for asset_type, patterns in asset_patterns.items():
            for pattern in patterns:
                if re.search(pattern, task_name) or re.search(pattern, task_description):
                    detected_asset_type = asset_type
                    break
            if detected_asset_type:
                break

        if detected_asset_type:
            try:
                # ENHANCED: Aggiorna il task con asset orientation markers + quality requirements
                enhanced_context = task_dict.get("context_data", {}) or {}
                enhanced_context.update({
                    "asset_oriented_task": True,
                    "asset_production": True,
                    "detected_asset_type": detected_asset_type,
                    "asset_enhancement_timestamp": datetime.now().isoformat(),
                    "enhanced_by": "asset_aware_analyzer",
                    # NUOVO: Quality requirements per asset concreti
                    "require_concrete_content": True,
                    "prohibit_theoretical_output": True,
                    "mandatory_quality_check": True,
                    "expected_output_type": "concrete_deliverable"
                })

                # Update nel database
                await update_task_status(
                    task_dict["id"],
                    task_dict.get("status", "pending"),
                    {"context_data": enhanced_context}
                )

                logger.info(f"🎯 ENHANCED: Task {task_dict['id']} marked for {detected_asset_type} production")

            except Exception as e:
                logger.error(f"Failed to enhance task {task_dict['id']} for asset production: {e}")
    
    async def _check_asset_completion_trigger(self, workspace_id: str) -> bool:
        """
        Verifica se il completamento di asset task dovrebbe triggerare deliverable
        """

        try:
            tasks = await list_tasks(workspace_id)

            # Conta asset tasks
            asset_tasks = []
            completed_asset_tasks = []

            for task in tasks:
                context_data = task.get("context_data", {}) or {}
                if isinstance(context_data, dict):
                    if (context_data.get("asset_production") or 
                        context_data.get("asset_oriented_task")):
                        asset_tasks.append(task)
                        if task.get("status") == "completed":
                            completed_asset_tasks.append(task)

            # Se ci sono asset tasks e la maggior parte è completata
            if len(asset_tasks) >= 2 and len(completed_asset_tasks) >= len(asset_tasks) * 0.7:
                logger.info(f"🎯 ASSET COMPLETION: {len(completed_asset_tasks)}/{len(asset_tasks)} asset tasks completed")
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking asset completion trigger: {e}")
            return False
    
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

    async def check_project_completion_criteria(self, workspace_id: str) -> bool:
        """
        Checks if all completion criteria for a workspace have been met
        by querying the v_workspace_completion_status view.
        """
        try:
            # Query the single source of truth view
            result = supabase.table("v_workspace_completion_status").select("calculated_status").eq("workspace_id", workspace_id).single().execute()

            if result.data and result.data.get("calculated_status") == "completed":
                logger.info(f"✅ DB view confirms completion for workspace {workspace_id}. Marking as completed.")
                return True
            
            # Log a detailed reason if not completed
            if result.data:
                logger.info(f"Workspace {workspace_id}: Not yet complete. Reason from DB view: {result.data}")
            else:
                logger.warning(f"Could not retrieve completion status for workspace {workspace_id} from view.")

            return False

        except Exception as e:
            logger.error(f"Error checking project completion criteria for workspace {workspace_id}: {e}", exc_info=True)
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
        if ctx.get("pending_tasks", 1) > 5: # Increased from 3 to 5
            return False
        
        total_tasks = ctx.get("total_tasks", 1)
        completed_tasks = ctx.get("completed_tasks", 0)
        completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
        
        if completion_rate < 0.50: # Lowered from 0.70 to 0.50
            return False
        
        if total_tasks < 1: # Lowered from 3 to 1
            return False
        
        return True

    def _is_handoff_duplicate_strict(self, task: Task, ctx: Dict[str, Any]) -> bool:
        """Absolute duplicate prevention"""
        cache_key = f"{task.workspace_id}_{task.agent_id}_handoff"
        recent_handoff = self.handoff_cache.get(cache_key)
        if recent_handoff and datetime.now() - recent_handoff < timedelta(hours=24):
            return True

        recent_completions = ctx.get("recent_completions", [])
        task_words = set(task.name.lower().split())
        
        for recent_task in recent_tasks[-10:]:
            recent_name = recent_task.get("name", "").lower()
            
            if any(word in recent_name for word in ["handoff", "follow-up", "continuation", "next"]):
                return True
                
            recent_words = set(recent_name.split())
            union_len = len(task_words | recent_words)
            overlap = len(task_words & recent_words) / union_len if union_len > 0 else 0.0
            if overlap > 0.4: # Reduced from 0.5 to 0.4 to be less strict
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
        """Get enhanced status con asset tracking"""

        # Ottieni status base esistente
        base_status = {
            "enhanced_version": "2.0_with_assets",
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

        # Aggiungi asset tracking info
        base_status["asset_support"] = {
            "asset_analysis_enabled": True,
            "asset_enhancement_active": True,
            "supported_asset_types": [
                "contact_database", "content_calendar", 
                "training_program", "financial_model"
            ]
        }

        return base_status

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

    async def _handle_memory_intelligence_extraction(
        self, 
        completed_task: Task, 
        task_result: Dict[str, Any], 
        workspace_id: str
    ) -> None:
        """
        🧠 MEMORY-DRIVEN INTELLIGENCE: Extract actionable insights and generate course corrections
        
        This is called for every completed task to:
        1. Extract actionable insights from task completion patterns
        2. Generate automatic corrective actions when needed
        3. Store insights in workspace memory for future reference
        """
        try:
            # Import memory intelligence system
            from backend.ai_quality_assurance.unified_quality_engine import AIMemoryIntelligence
            
            memory_intelligence = AIMemoryIntelligence()
            
            # Get workspace context for analysis
            workspace_context = await self._get_workspace_context_for_memory(workspace_id)
            
            # Extract actionable insights from this task completion
            insights = await memory_intelligence.extract_actionable_insights(
                completed_task={
                    'id': str(completed_task.id),
                    'name': completed_task.name or '',
                    'assigned_to_role': completed_task.assigned_to_role or '',
                    'priority': completed_task.priority or 'medium',
                    'creation_type': getattr(completed_task, 'creation_type', ''),
                    'context_data': completed_task.context_data or {}
                },
                task_result=task_result,
                workspace_context=workspace_context
            )
            
            if insights:
                logger.info(f"🧠 MEMORY INSIGHTS: Extracted {len(insights)} actionable insights from task {completed_task.id}")
                
                # Store insights in workspace memory
                await self._store_insights_in_workspace_memory(insights, workspace_id, completed_task)
                
                # Generate corrective actions if patterns indicate issues
                corrective_actions = await memory_intelligence.generate_corrective_actions(
                    workspace_id=workspace_id,
                    current_insights=insights,
                    workspace_context=workspace_context
                )
                
                if corrective_actions:
                    logger.info(f"🔄 AUTO CORRECTION: Generated {len(corrective_actions)} corrective actions for workspace {workspace_id}")
                    
                    # Create corrective tasks to address identified issues
                    await self._create_corrective_tasks(corrective_actions, workspace_id, completed_task)
                else:
                    logger.debug(f"🧠 MEMORY: No corrective actions needed for workspace {workspace_id}")
            else:
                logger.debug(f"🧠 MEMORY: No actionable insights extracted from task {completed_task.id}")
                
        except Exception as e:
            logger.error(f"Error in memory intelligence extraction for task {completed_task.id}: {e}", exc_info=True)
    
    async def _get_workspace_context_for_memory(self, workspace_id: str) -> Dict[str, Any]:
        """Get enhanced workspace context for memory intelligence analysis"""
        try:
            # Get basic workspace context
            workspace = await get_workspace(workspace_id)
            tasks = await list_tasks(workspace_id)
            
            # Get workspace goals for context
            try:
                workspace_goals = await get_workspace_goals(workspace_id)
            except Exception:
                workspace_goals = []
            
            # Build comprehensive context
            return {
                'workspace_id': workspace_id,
                'goal': workspace.get('goal', '') if workspace else '',
                'industry': workspace.get('industry', 'Business') if workspace else 'Business',
                'status': workspace.get('status', '') if workspace else '',
                'total_tasks': len(tasks),
                'completed_tasks': len([t for t in tasks if t.get('status') == 'completed']),
                'pending_tasks': len([t for t in tasks if t.get('status') in ['pending', 'in_progress']]),
                'goals_count': len(workspace_goals),
                'goals_active': len([g for g in workspace_goals if g.get('status') == 'active']),
                'created_at': workspace.get('created_at', '') if workspace else ''
            }
        except Exception as e:
            logger.error(f"Error getting workspace context for memory: {e}")
            return {
                'workspace_id': workspace_id,
                'goal': '',
                'industry': 'Business',
                'total_tasks': 0,
                'completed_tasks': 0,
                'pending_tasks': 0
            }
    
    async def _store_insights_in_workspace_memory(
        self, 
        insights: List[Dict[str, Any]], 
        workspace_id: str, 
        completed_task: Task
    ) -> None:
        """Store extracted insights in workspace memory system"""
        try:
            from workspace_memory import workspace_memory
            from models import InsightType
            from uuid import UUID
            
            for insight in insights:
                # Map insight type to enum
                insight_type_mapping = {
                    'process_optimization': InsightType.OPTIMIZATION,
                    'quality_improvement': InsightType.SUCCESS_PATTERN,
                    'cost_efficiency': InsightType.OPTIMIZATION,
                    'strategic_guidance': InsightType.SUCCESS_PATTERN
                }
                
                insight_type = insight_type_mapping.get(
                    insight.get('insight_type', 'optimization'), 
                    InsightType.OPTIMIZATION
                )
                
                # Prepare relevance tags
                relevance_tags = insight.get('relevance_tags', [])
                if completed_task.assigned_to_role:
                    relevance_tags.append(f"role_{completed_task.assigned_to_role.lower()}")
                if insight.get('source_agent_role'):
                    relevance_tags.append(f"agent_{insight['source_agent_role'].lower()}")
                
                # Store insight
                await workspace_memory.store_insight(
                    workspace_id=UUID(workspace_id),
                    task_id=completed_task.id,
                    agent_role=insight.get('source_agent_role', 'memory_intelligence'),
                    insight_type=insight_type,
                    content=insight.get('content', ''),
                    relevance_tags=relevance_tags,
                    confidence_score=insight.get('confidence_score', 0.8)
                )
                
                logger.debug(f"🧠 STORED: Insight '{insight.get('content', '')[:50]}...' in workspace memory")
                
        except Exception as e:
            logger.error(f"Error storing insights in workspace memory: {e}")
    
    async def _create_corrective_tasks(
        self, 
        corrective_actions: List[Dict[str, Any]], 
        workspace_id: str, 
        source_task: Task
    ) -> None:
        """Create corrective tasks based on memory intelligence analysis"""
        try:
            # Find appropriate agent for corrective tasks (prefer PM)
            pm_agent = await self._find_project_manager(workspace_id)
            if not pm_agent:
                logger.warning(f"No PM found for corrective tasks in workspace {workspace_id}")
                return
            
            for action in corrective_actions:
                try:
                    # Prepare context data for tracking
                    context_data = {
                        'project_phase': 'IMPLEMENTATION',  # Corrective actions are usually implementation-focused
                        'corrective_action': True,
                        'memory_driven': True,
                        'source_task_id': str(source_task.id),
                        'action_type': action.get('action_type', 'process_optimization'),
                        'target_metric': action.get('target_metric', ''),
                        'urgency': action.get('urgency', 'medium'),
                        'workspace_patterns': action.get('workspace_patterns', []),
                        'generated_at': action.get('generated_at', ''),
                        'generation_method': action.get('generation_method', 'ai_driven'),
                        'creation_type': 'memory_intelligence_correction'
                    }
                    
                    # Map urgency to priority
                    urgency_to_priority = {
                        'immediate': 'high',
                        'next_week': 'medium',
                        'within_month': 'low'
                    }
                    task_priority = urgency_to_priority.get(action.get('urgency', 'medium'), 'medium')
                    
                    # Create corrective task
                    created_task = await create_task(
                        workspace_id=workspace_id,
                        agent_id=pm_agent['id'],
                        name=action.get('task_name', 'Memory-Driven Improvement Task'),
                        description=action.get('task_description', 'Implement improvements based on workspace memory analysis'),
                        status=TaskStatus.PENDING.value,
                        priority=task_priority,
                        context_data=context_data,
                        creation_type='memory_intelligence_correction',
                        parent_task_id=str(source_task.id)
                    )
                    
                    if created_task and created_task.get('id'):
                        logger.info(
                            f"🔄 CORRECTIVE TASK: Created {created_task['id']} - {action.get('task_name', 'Improvement Task')} "
                            f"(Priority: {task_priority}, Target: {action.get('target_metric', 'general')})"
                        )
                    else:
                        logger.error(f"Failed to create corrective task for action: {action.get('task_name', 'Unknown')}")
                        
                except Exception as e:
                    logger.error(f"Error creating corrective task: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error creating corrective tasks: {e}", exc_info=True)
    
    # =====================================================================
    # AI-DRIVEN PRIORITY METHODS
    # =====================================================================
    
    async def _calculate_ai_driven_base_priority(
        self, 
        task_data: Dict[str, Any], 
        context_data: Dict[str, Any],
        workspace_id: str
    ) -> int:
        """🤖 AI-DRIVEN: Calculate task priority based on semantic understanding"""
        try:
            # Check if AI is enabled
            if not os.getenv("ENABLE_AI_TASK_PRIORITY", "true").lower() == "true":
                # Fallback to static priority
                priority_field = task_data.get("priority", "medium").lower()
                priority_mapping = {"high": 300, "medium": 100, "low": 50}
                return priority_mapping.get(priority_field, 100)
            
            # Initialize OpenAI client if available
            openai_client = None
            if os.getenv("OPENAI_API_KEY"):
                try:
                    from openai import AsyncOpenAI
                    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                except ImportError:
                    pass
            
            if not openai_client:
                # Fallback to static priority
                priority_field = task_data.get("priority", "medium").lower()
                priority_mapping = {"high": 300, "medium": 100, "low": 50}
                return priority_mapping.get(priority_field, 100)
            
            # Get workspace context
            try:
                from database import get_workspace
                workspace = await get_workspace(workspace_id)
                project_description = workspace.get("description", "")
            except Exception:
                project_description = ""
            
            task_name = task_data.get("name", "")
            task_description = task_data.get("description", "")
            task_priority = task_data.get("priority", "medium")
            
            ai_prompt = f"""
            Calculate appropriate priority score for this task:
            
            Task: {task_name}
            Description: {task_description}
            Current Priority: {task_priority}
            Project: {project_description[:200]}...
            
            Consider:
            - Business impact and urgency
            - Task dependencies and blockers
            - Project phase and timeline
            - Resource availability
            
            Return ONLY a number between 0-500 representing the priority score.
            Guidelines: 0-50 (low), 50-150 (medium), 150-300 (high), 300+ (critical)
            """
            
            response = await openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at project task prioritization. Return only a numeric priority score."},
                    {"role": "user", "content": ai_prompt}
                ],
                temperature=0.1,
                max_tokens=10
            )
            
            ai_result = response.choices[0].message.content.strip()
            try:
                priority_score = int(float(ai_result))
                # Bound the score
                priority_score = max(0, min(500, priority_score))
                logger.info(f"✅ AI-driven priority calculated: {priority_score} for task {task_name}")
                return priority_score
            except ValueError:
                logger.warning(f"AI returned non-numeric priority: {ai_result}")
                # Fallback
                priority_field = task_data.get("priority", "medium").lower()
                priority_mapping = {"high": 300, "medium": 100, "low": 50}
                return priority_mapping.get(priority_field, 100)
                
        except Exception as e:
            logger.warning(f"AI priority calculation failed: {e}")
            # Fallback to static priority
            priority_field = task_data.get("priority", "medium").lower()
            priority_mapping = {"high": 300, "medium": 100, "low": 50}
            return priority_mapping.get(priority_field, 100)
    
    async def _calculate_ai_priority_enhancements(
        self,
        base_priority: int,
        task_data: Dict[str, Any],
        context_data: Dict[str, Any],
        workspace_id: str
    ) -> int:
        """🤖 AI-DRIVEN: Calculate priority enhancements based on context"""
        try:
            # Check if AI enhancement is enabled
            if not os.getenv("ENABLE_AI_URGENCY_BOOST", "true").lower() == "true":
                return base_priority
            
            # Calculate age boost
            created_at = task_data.get("created_at", "")
            if created_at:
                try:
                    from datetime import datetime, timezone
                    created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    age_hours = (datetime.now(timezone.utc) - created_dt).total_seconds() / 3600
                    
                    # AI-driven urgency boost
                    urgency_boost = await self._calculate_ai_urgency_boost(age_hours, task_data, context_data)
                    base_priority += urgency_boost
                except Exception as e:
                    logger.debug(f"Error calculating age boost: {e}")
            
            return base_priority
            
        except Exception as e:
            logger.warning(f"AI priority enhancements failed: {e}")
            return base_priority
    
    async def _calculate_ai_urgency_boost(
        self,
        age_hours: float,
        task_data: Dict[str, Any],
        context_data: Dict[str, Any]
    ) -> int:
        """🤖 AI-DRIVEN: Calculate urgency boost based on task age and context"""
        try:
            # Simple adaptive urgency calculation
            if age_hours < 1:
                return 0
            elif age_hours < 4:
                return int(age_hours * 10)  # Gradual increase
            elif age_hours < 24:
                return int(age_hours * 5) + 20  # Moderate increase
            else:
                return min(150, int(age_hours * 2) + 50)  # Capped increase
                
        except Exception as e:
            logger.warning(f"AI urgency boost calculation failed: {e}")
            # Simple fallback
            return min(100, int(age_hours * 5)) if age_hours > 2 else 0

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