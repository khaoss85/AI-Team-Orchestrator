# backend/executor.py - Enhanced with FINALIZATION priority boost
import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set, Callable
from uuid import UUID, uuid4
import json
import time
from collections import defaultdict, Counter
import difflib

# Import da modelli del progetto
from models import TaskStatus, Task, AgentStatus, WorkspaceStatus, Agent as AgentModelPydantic, TaskExecutionOutput
from database import (
    list_tasks,
    update_task_status,
    get_workspace,
    get_agent,
    list_agents as db_list_agents,
    create_task,
    get_active_workspaces,
    get_workspaces_with_pending_tasks,
    update_workspace_status,
    get_task,
    update_agent_status,
    supabase
)

from improvement_loop import controlled_iteration, refresh_dependencies
from ai_agents.manager import AgentManager
from task_analyzer import EnhancedTaskExecutor, get_enhanced_task_executor
from utils.project_settings import get_project_settings
from services.unified_memory_engine import unified_memory_engine

logger = logging.getLogger(__name__)

# 🎯 HOLISTIC INTEGRATION: Import pipeline esistente senza creare silos
try:
    from services.holistic_task_deliverable_pipeline import HolisticTaskDeliverablePipeline
    HOLISTIC_PIPELINE_AVAILABLE = True
    logger.info("✅ Holistic Task-Deliverable Pipeline available for content transfer")
except ImportError as e:
    logger.warning(f"⚠️ Holistic Pipeline not available: {e}")
    HOLISTIC_PIPELINE_AVAILABLE = False

# 🚦 Import API Rate Limiter for external API call management
try:
    from services.api_rate_limiter import api_rate_limiter, execute_with_rate_limit
    API_RATE_LIMITER_AVAILABLE = True
    logger.info("✅ API Rate Limiter available for external API management")
except ImportError as e:
    logger.warning(f"⚠️ API Rate Limiter not available: {e}")
    API_RATE_LIMITER_AVAILABLE = False
    api_rate_limiter = None

# Import WebSocket functions for real-time updates
try:
    from routes.websocket import broadcast_task_status_update
    WEBSOCKET_AVAILABLE = True
    logger.info("✅ WebSocket real-time updates available in TaskExecutor")
except ImportError as e:
    logger.warning(f"⚠️ WebSocket not available in TaskExecutor: {e}")
    WEBSOCKET_AVAILABLE = False
    broadcast_task_status_update = None

# 🧠 Import Thinking Process Engine for Real-Time Reasoning (Pillar 10)
try:
    from services.thinking_process import thinking_engine
    THINKING_PROCESS_AVAILABLE = True
    logger.info("✅ Thinking Process Engine available for real-time reasoning")
except ImportError as e:
    logger.warning(f"⚠️ Thinking Process Engine not available: {e}")
    THINKING_PROCESS_AVAILABLE = False
    thinking_engine = None

# 🏥 Import Workspace Health Manager for intelligent health checks
try:
    from services.workspace_health_manager import workspace_health_manager
    WORKSPACE_HEALTH_AVAILABLE = True
    logger.info("✅ WorkspaceHealthManager available for intelligent health checks")
except ImportError as e:
    logger.warning(f"⚠️ WorkspaceHealthManager not available: {e}")
    WORKSPACE_HEALTH_AVAILABLE = False
    workspace_health_manager = None

# 👥 Import Agent Status Manager for unified agent management
try:
    from services.agent_status_manager import agent_status_manager
    AGENT_STATUS_MANAGER_AVAILABLE = True
    logger.info("✅ AgentStatusManager available for unified agent management")
except ImportError as e:
    logger.warning(f"⚠️ AgentStatusManager not available: {e}")
    AGENT_STATUS_MANAGER_AVAILABLE = False
    agent_status_manager = None

# 🤖 AI-DRIVEN: Import Dynamic Anti-Loop Manager for intelligent limit management
try:
    from services.dynamic_anti_loop_manager import dynamic_anti_loop_manager
    DYNAMIC_ANTI_LOOP_AVAILABLE = True
    logger.info("✅ DynamicAntiLoopManager available for AI-driven limit management")
except ImportError as e:
    logger.warning(f"⚠️ DynamicAntiLoopManager not available: {e}")
    DYNAMIC_ANTI_LOOP_AVAILABLE = False
    dynamic_anti_loop_manager = None

# 🔧 Import FailedTaskResolver for autonomous task recovery
try:
    from services.failed_task_resolver import failed_task_resolver, start_autonomous_recovery_scheduler
    FAILED_TASK_RESOLVER_AVAILABLE = True
    logger.info("✅ FailedTaskResolver available for autonomous task recovery")
except ImportError as e:
    logger.warning(f"⚠️ FailedTaskResolver not available: {e}")
    FAILED_TASK_RESOLVER_AVAILABLE = False
    failed_task_resolver = None
    start_autonomous_recovery_scheduler = None

# 🎼 Import Unified Orchestrator for complete orchestration capabilities
try:
    from services.unified_orchestrator import get_unified_orchestrator
except ImportError:
    logger.warning("⚠️ Unified Orchestrator not available")
    get_unified_orchestrator = None

try:
    from services.holistic_orchestrator import get_holistic_orchestrator, OrchestrationMode
except ImportError:
    logger.warning("⚠️ Holistic Orchestrator not available")
    get_holistic_orchestrator = None
    OrchestrationMode = None

try:
    from services.holistic_task_lifecycle import (
        get_holistic_lifecycle_manager, start_holistic_task_lifecycle, 
        update_task_lifecycle_phase, complete_holistic_task_lifecycle, LifecyclePhase
    )
    UNIFIED_ORCHESTRATOR_AVAILABLE = True
    logger.info("✅ Unified Orchestrator available for complete orchestration capabilities")
except ImportError as e:
    logger.warning(f"⚠️ Unified Orchestrator not available: {e}")
    UNIFIED_ORCHESTRATOR_AVAILABLE = False
    get_holistic_lifecycle_manager = None
    start_holistic_task_lifecycle = None
    update_task_lifecycle_phase = None
    complete_holistic_task_lifecycle = None
    LifecyclePhase = None
    UNIFIED_ORCHESTRATOR_AVAILABLE = False
    get_unified_orchestrator = None

# 🧠 Import Recovery Analysis Engine for intelligent failure recovery
try:
    from services.recovery_analysis_engine import recovery_analysis_engine, should_attempt_recovery
    RECOVERY_ANALYSIS_AVAILABLE = True
    logger.info("✅ RecoveryAnalysisEngine available for intelligent failure recovery")
except ImportError as e:
    logger.warning(f"⚠️ RecoveryAnalysisEngine not available: {e}")
    RECOVERY_ANALYSIS_AVAILABLE = False
    recovery_analysis_engine = None
    should_attempt_recovery = None

# 🎭 Import Optimized Sub-Agent Orchestration System
try:
    from config.optimized_sub_agent_configs_2025 import (
        optimized_orchestrator,
        suggest_agents_for_task as suggest_optimized_agents,
        get_orchestration_pattern as get_optimized_pattern,
        track_agent_performance,
        get_orchestrator_dashboard
    )
    from services.enhanced_sub_agent_orchestrator import (
        enhanced_orchestrator,
        orchestrate_task as orchestrate_sub_agents
    )
    SUB_AGENT_ORCHESTRATION_AVAILABLE = True
    logger.info("🎭 Optimized Sub-Agent Orchestration System available")
except ImportError as e:
    logger.warning(f"⚠️ Sub-Agent Orchestration System not available: {e}")
    SUB_AGENT_ORCHESTRATION_AVAILABLE = False
    optimized_orchestrator = None
    suggest_optimized_agents = None
    get_optimized_pattern = None
    track_agent_performance = None
    get_orchestrator_dashboard = None
    enhanced_orchestrator = None
    orchestrate_sub_agents = None

# 📊 Import System Telemetry Monitor for comprehensive monitoring
try:
    from services.system_telemetry_monitor import system_telemetry_monitor
    TELEMETRY_MONITOR_AVAILABLE = True
    logger.info("✅ SystemTelemetryMonitor available for proactive monitoring")
except ImportError as e:
    logger.warning(f"⚠️ SystemTelemetryMonitor not available: {e}")
    TELEMETRY_MONITOR_AVAILABLE = False
    system_telemetry_monitor = None

# 🔍 Import Task Execution Monitor for hang detection
try:
    from task_execution_monitor import task_monitor, ExecutionStage, trace_task_start, trace_stage, trace_error, trace_task_complete, start_monitoring
    TASK_MONITOR_AVAILABLE = True
    logger.info("✅ TaskExecutionMonitor available for hang detection")
except ImportError as e:
    logger.warning(f"⚠️ TaskExecutionMonitor not available: {e}")
    TASK_MONITOR_AVAILABLE = False
    task_monitor = None

# 🚀 CRITICAL FIX: Lazy Load Asset System to Break Circular Imports
ASSET_SYSTEM_AVAILABLE = False
asset_processor = None
asset_quality_engine = None  
asset_db_manager = None

def _initialize_asset_system():
    """Lazy initialization of asset system to break circular imports"""
    global ASSET_SYSTEM_AVAILABLE, asset_processor, asset_quality_engine, asset_db_manager
    
    if ASSET_SYSTEM_AVAILABLE:
        return True
        
    try:
        from backend.deliverable_system.unified_deliverable_engine import unified_deliverable_engine
        from backend.ai_quality_assurance.unified_quality_engine import unified_quality_engine
        from database_asset_extensions import AssetDrivenDatabaseManager
        from services import AssetArtifactProcessor
        
        # Initialize asset system components
        asset_processor = AssetArtifactProcessor  # This is already an instance, not a class
        asset_quality_engine = unified_quality_engine
        asset_db_manager = AssetDrivenDatabaseManager()
        
        ASSET_SYSTEM_AVAILABLE = True
        logger.info("✅ Asset System integration loaded on-demand for TaskExecutor")
        return True
        
    except ImportError as e:
        logger.warning(f"⚠️ Asset System not available in TaskExecutor: {e}")
        ASSET_SYSTEM_AVAILABLE = False
        return False

try:
    from config.quality_system_config import QualitySystemConfig
    from backend.deliverable_system.unified_deliverable_engine import check_and_create_final_deliverable
    QUALITY_SYSTEM_AVAILABLE = True
    logger.info("✅ Quality System integration available for TaskExecutor")
except ImportError as e:
    logger.warning(f"⚠️ Quality System not available in TaskExecutor: {e}")
    QUALITY_SYSTEM_AVAILABLE = False
    QualitySystemConfig = None
    check_and_create_final_deliverable = None  # Define as None to avoid NameError


# === ENHANCED FINALIZATION PRIORITY CONFIGURATIONS ===
FINALIZATION_TASK_PRIORITY_BOOST = int(os.getenv("FINALIZATION_TASK_PRIORITY_BOOST", "1000"))
ENABLE_SMART_PRIORITIZATION = os.getenv("ENABLE_SMART_PRIORITIZATION", "true").lower() == "true"

# === WEBSOCKET NOTIFICATION HELPER ===
async def notify_task_status_change(task_id: str, new_status: str, task_data: Optional[Dict] = None):
    """Send real-time notification of task status change via WebSocket"""
    if WEBSOCKET_AVAILABLE and broadcast_task_status_update:
        try:
            # Get fresh task data if not provided
            if not task_data:
                task_data = await get_task(task_id)
            
            if task_data:
                # Prepare notification payload
                notification_data = {
                    "id": task_id,
                    "status": new_status,
                    "name": task_data.get("name", "Unknown Task"),
                    "updated_at": datetime.now().isoformat(),
                    "workspace_id": task_data.get("workspace_id"),
                    "agent_id": task_data.get("agent_id"),
                    "result": task_data.get("result")
                }
                
                # Send WebSocket notification
                await broadcast_task_status_update(task_id, notification_data)
                logger.debug(f"📡 WebSocket notification sent for task {task_id}: {new_status}")
        except Exception as e:
            logger.error(f"❌ Failed to send WebSocket notification for task {task_id}: {e}")

# === ENHANCED PRIORITY SCORING FUNCTION ===
def get_task_priority_score_enhanced(task_data, workspace_id):
    """
    🤖 AI-DRIVEN: Enhanced prioritization with URGENT corrective task absolute priority
    Pillar 5: Goal-Driven with automatic tracking
    Pillar 12: Automatic Course-Correction
    """
    try:
        # 🚨 ABSOLUTE PRIORITY: URGENT corrective tasks (Phase 1 implementation)
        task_name = task_data.get("name", "").upper()
        task_description = task_data.get("description", "").upper()
        
        # Check for URGENT gap closure patterns
        urgent_patterns = [
            "URGENT: CLOSE",
            "URGENT:",
            "% GAP",
            "CRITICAL GAP",
            "EMERGENCY:",
            "IMMEDIATE:"
        ]
        
        is_urgent_corrective = False
        for pattern in urgent_patterns:
            if pattern in task_name or pattern in task_description:
                is_urgent_corrective = True
                logger.critical(f"🚨 URGENT CORRECTIVE DETECTED: '{task_name[:50]}' - ABSOLUTE PRIORITY")
                break
        
        # ABSOLUTE PRIORITY: 10000+ for URGENT corrective tasks
        if is_urgent_corrective:
            return 10000 + FINALIZATION_TASK_PRIORITY_BOOST
        
        # Check if it's a goal-driven corrective task
        context_data = task_data.get("context_data", {}) or {}
        is_goal_driven = context_data.get("is_goal_driven_task", False)
        task_type = context_data.get("task_type", "").lower()
        
        if is_goal_driven and "corrective" in task_type:
            logger.warning(f"🎯 GOAL-DRIVEN CORRECTIVE: '{task_name[:50]}' - HIGH PRIORITY")
            return 8000 + FINALIZATION_TASK_PRIORITY_BOOST
        
        # Base priority score for regular tasks
        base_priority = 0
        
        # === CRITICAL: FINALIZATION PHASE BOOST ===
        project_phase = ""
        
        if isinstance(context_data, dict):
            project_phase = context_data.get("project_phase", "").upper()
        
        # MASSIVE boost for FINALIZATION tasks
        if project_phase == "FINALIZATION":
            base_priority = FINALIZATION_TASK_PRIORITY_BOOST
            logger.critical(f"🎯 FINALIZATION BOOST: Task {task_data.get('id', 'unknown')} priority = {base_priority}")
        
        # High boost for phase planning tasks
        elif context_data.get("planning_task_marker"):
            target_phase = context_data.get("target_phase", "")
            if target_phase == "FINALIZATION":
                base_priority = FINALIZATION_TASK_PRIORITY_BOOST - 100  # Slightly lower than execution
                logger.warning(f"🎯 FINALIZATION PLANNING BOOST: Task {task_data.get('id', 'unknown')} priority = {base_priority}")
            else:
                base_priority = 500  # High priority for any phase planning
                logger.info(f"📋 PLANNING BOOST: Task {task_data.get('id', 'unknown')} priority = {base_priority}")
        
        # Enhanced priority based on task priority field
        else:
            # 🤖 AI-DRIVEN PRIORITY: Use fallback for now since we're in sync context
            # TODO: Make this function async to properly use AI-driven priority
            priority_field = task_data.get("priority", "medium").lower()
            priority_mapping = {"high": 300, "medium": 100, "low": 50}
            base_priority = priority_mapping.get(priority_field, 100)
        
        # Time-based priority boost
        created_at = task_data.get("created_at", "")
        if created_at:
            try:
                created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                task_age_hours = (datetime.now(timezone.utc) - created_dt).total_seconds() / 3600
                
                # Progressive boost for aging tasks
                if task_age_hours > 2:
                    time_boost = min(int(task_age_hours * 5), 100)
                    base_priority += time_boost
            except Exception:
                pass
        
        # Final priority is base priority with all boosts applied
        final_priority = base_priority
        
        # Ensure minimum priority
        final_priority = max(final_priority, 1)
        
        # Log detailed calculation for FINALIZATION tasks
        if project_phase == "FINALIZATION" or final_priority > 500:
            logger.warning(f"🔥 HIGH PRIORITY TASK: {task_data.get('name', 'Unknown')[:50]} "
                          f"Final Priority: {final_priority} "
                          f"(Phase: {project_phase})")
        
        return final_priority
        
    except Exception as e:
        logger.error(f"Error calculating enhanced task priority: {e}")
        return 1  # Minimum priority fallback


class BudgetTracker:
    """Tracks budget usage for agents with detailed cost monitoring"""

    def __init__(self):
        """Initialize the budget tracker."""
        self.usage_log: Dict[str, List[Dict[str, Any]]] = {}
        self.token_costs = {
            "gpt-4.1": {"input": 0.002, "output": 0.008},           # $2.00/$8.00 per 1K tokens
            "gpt-4.1-mini": {"input": 0.0004, "output": 0.0016},    # $0.40/$1.60 per 1K tokens  
            "gpt-4.1-nano": {"input": 0.0001, "output": 0.0004},    # $0.10/$0.40 per 1K tokens
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},         # Legacy model costs
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015}    # Legacy model costs
        }
        self.default_model = "gpt-4.1-mini"

    def log_usage(self, agent_id: str, model: str, input_tokens: int, output_tokens: int, task_id: Optional[str] = None) -> Dict[str, Any]:
        """Log token usage and associated costs"""
        if agent_id not in self.usage_log:
            self.usage_log[agent_id] = []

        costs = self.token_costs.get(model, self.token_costs[self.default_model])
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]
        total_cost = input_cost + output_cost

        usage_record = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "agent_id": agent_id,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(total_cost, 6),
            "currency": "USD"
        }

        self.usage_log[agent_id].append(usage_record)
        logger.info(f"Budget usage - Agent {agent_id}, Task {task_id}: ${total_cost:.6f} (Model: {model}, Tokens: {input_tokens} in + {output_tokens} out)")
        return usage_record

    def get_agent_total_cost(self, agent_id: str) -> float:
        """Calculate total cost for agent"""
        if agent_id not in self.usage_log:
            return 0.0
        return sum(record["total_cost"] for record in self.usage_log[agent_id])

    def get_workspace_total_cost(self, workspace_id: str, agent_ids: List[str]) -> Dict[str, Any]:
        """Calculate workspace total cost"""
        total_cost = 0.0
        agent_costs = {}
        total_tokens = {"input": 0, "output": 0}

        for agent_id in agent_ids:
            agent_total_cost = self.get_agent_total_cost(agent_id)
            agent_costs[agent_id] = round(agent_total_cost, 6)
            total_cost += agent_total_cost

            if agent_id in self.usage_log:
                for record in self.usage_log[agent_id]:
                    total_tokens["input"] += record["input_tokens"]
                    total_tokens["output"] += record["output_tokens"]

        return {
            "workspace_id": workspace_id,
            "total_cost": round(total_cost, 6),
            "agent_costs": agent_costs,
            "total_tokens": total_tokens,
            "currency": "USD"
        }

    def get_all_usage_logs(self, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return all usage logs, optionally filtered by agent"""
        if agent_id:
            return self.usage_log.get(agent_id, [])
        else:
            all_logs = []
            for logs in self.usage_log.values():
                all_logs.extend(logs)
            return all_logs

class AssetCoordinationMixin:
    """
    Mixin per coordinamento asset-oriented nel TaskExecutor esistente
    Estende funzionalità senza modificare l'architettura base
    """
    
    async def coordinate_asset_oriented_workflow(self, workspace_id: str):
        """
        Coordina il workflow asset-oriented per un workspace
        """
        
        try:
            # Verifica se il workspace ha task asset-oriented in corso
            asset_tasks = await self._get_asset_oriented_tasks(workspace_id)
            
            if asset_tasks:
                logger.info(f"🎯 ASSET COORDINATION: {len(asset_tasks)} asset tasks in workspace {workspace_id}")
                
                # Prioritizza task asset-oriented
                await self._prioritize_asset_tasks(asset_tasks)
                
                # Monitora completamento per deliverable triggering
                completed_asset_tasks = [t for t in asset_tasks if t.get("status") == "completed"]
                
                if len(completed_asset_tasks) >= len(asset_tasks) * 0.8:  # 80% asset tasks completed
                    logger.info(f"🎯 ASSET THRESHOLD: 80% asset tasks completed, checking deliverable readiness")
                    
                    # Initialize deliverable_id to None
                    deliverable_id = None
                    
                    # Check if last completed task was enhancement task to prevent loops
                    last_task = completed_asset_tasks[-1] if completed_asset_tasks else None
                    if last_task and not self._is_enhancement_task(last_task):
                        # Trigger enhanced deliverable check with circuit breaker protection
                        async def _safe_deliverable_creation():
                            from backend.deliverable_system.unified_deliverable_engine import check_and_create_final_deliverable
                            return await check_and_create_final_deliverable(workspace_id)
                        
                        deliverable_id = await self._execute_with_circuit_breaker(_safe_deliverable_creation)
                    else:
                        logger.info(f"🔧 ENHANCEMENT LOOP PREVENTION: Skipping deliverable trigger - last task was enhancement")
                    
                    if deliverable_id:
                        logger.critical(f"🎯 ASSET-TRIGGERED DELIVERABLE: {deliverable_id} created for {workspace_id}")
            
        except Exception as e:
            logger.error(f"Error in asset-oriented workflow coordination: {e}")
    
    async def _get_asset_oriented_tasks(self, workspace_id: str) -> List[Dict]:
        """Ottieni task asset-oriented per un workspace"""
        
        try:
            all_tasks = await self._cached_list_tasks(workspace_id)
            
            asset_tasks = []
            for task in all_tasks:
                context_data = task.get("context_data", {}) or {}
                
                if isinstance(context_data, dict):
                    if (context_data.get("asset_production") or 
                        context_data.get("asset_oriented_task") or
                        "PRODUCE ASSET:" in task.get("name", "")):
                        asset_tasks.append(task)
            
            return asset_tasks
            
        except Exception as e:
            logger.error(f"Error getting asset-oriented tasks: {e}")
            return []
    
    async def _prioritize_asset_tasks(self, asset_tasks: List[Dict]):
        """Prioritizza task asset-oriented nel sistema"""
        
        for task in asset_tasks:
            if task.get("status") == "pending":
                # Boost priority per asset tasks
                try:
                    await update_task_status(
                        task["id"], 
                        "pending",
                        {"priority_boost": "asset_oriented", "boosted_at": datetime.now().isoformat()}
                    )
                    # Send WebSocket notification
                    await notify_task_status_change(task["id"], "pending", task)
                except Exception as e:
                    logger.warning(f"Failed to boost priority for asset task {task['id']}: {e}")

class TaskExecutor(AssetCoordinationMixin):
    """Enhanced Task Executor with anti-loop protection and role-based task assignment"""

    def __init__(self):
        """Initialize the task executor"""
        self.running = False
        self.paused = False
        self.pause_event = asyncio.Event()
        self.pause_event.set()

        self.workspace_managers: Dict[UUID, AgentManager] = {}
        self.budget_tracker = BudgetTracker()
        self.execution_log: List[Dict[str, Any]] = []

        # ANTI-LOOP CONFIGURATIONS (these can be overridden per workspace)
        self.default_max_concurrent_tasks: int = 3  # Numero di worker paralleli
        self.max_tasks_per_workspace_anti_loop: int = int(os.getenv("MAX_TASKS_PER_WORKSPACE_ANTI_LOOP", "15"))  # 🤖 AI-DRIVEN: Increased from 10 to 15, configurable
        self.default_execution_timeout: int = 300  # secondi per task
        self.max_delegation_depth: int = 2

        # Tracking per anti-loop
        self.task_completion_tracker: Dict[str, Set[str]] = defaultdict(set)
        self.delegation_chain_tracker: Dict[str, List[str]] = defaultdict(list)
        
        # 🔍 Initialize task execution monitoring (will be started when executor starts)
        self.monitoring_started = False
        if TASK_MONITOR_AVAILABLE:
            logger.info("✅ Task execution monitoring ready (will start with executor)")
        self.workspace_anti_loop_task_counts: Dict[str, int] = defaultdict(int)
        
        # 🎯 HOLISTIC INTEGRATION: Initialize pipeline esistente
        self.holistic_pipeline = None
        if HOLISTIC_PIPELINE_AVAILABLE:
            try:
                self.holistic_pipeline = HolisticTaskDeliverablePipeline()
                logger.info("✅ Holistic Task-Deliverable Pipeline initialized in executor")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize holistic pipeline: {e}")
                self.holistic_pipeline = None

        # Track task IDs currently queued or running to avoid duplicates
        self.queued_task_ids: Set[str] = set()
        self.active_task_ids: Set[str] = set()

        self.last_cleanup: datetime = datetime.now()

        # Queue configuration
        self.max_queue_size: int = self.max_concurrent_tasks * 5
        self.active_tasks_count: int = 0
        self.task_queue: asyncio.Queue = asyncio.Queue(maxsize=self.max_queue_size)
        self.worker_tasks: List[asyncio.Task] = []

        # Enhanced task handler (con auto-generation disabilitata)
        self.enhanced_handler = get_enhanced_task_executor()
        self.auto_generation_enabled: bool = True  # DISABILITATO per sicurezza

        # RUNAWAY PROTECTION CONFIGURATIONS
        self.workspace_auto_generation_paused: Set[str] = set()
        self.last_runaway_check: Optional[datetime] = None
        self.max_pending_tasks_per_workspace: int = int(os.getenv("MAX_PENDING_TASKS_PER_WORKSPACE", "200"))  # 🔧 ENHANCED: Increased from 50 to 200
        self.runaway_check_interval: int = 300  # secondi

        # === QUERY CACHING CONFIGURATION ===
        # Minimum seconds before repeating the same DB query for a workspace
        self.min_db_query_interval: int = int(os.getenv("MIN_DB_QUERY_INTERVAL", "60"))  # Increased from 30 to 60
        self._tasks_query_cache: Dict[str, Tuple[float, List[Dict]]] = {}
        self._agents_query_cache: Dict[str, Tuple[float, List[Dict]]] = {}
        self._active_ws_cache: Tuple[float, List[str]] = (0, [])
        
        # === DEBOUNCING CONFIGURATION ===
        self._pending_queries: Dict[str, asyncio.Future] = {}
        self._debounce_window: float = 2.0  # 2 second debounce window
        self._query_debounce_cache: Dict[str, float] = {}  # Track last query times
        
        # === CIRCUIT BREAKER CONFIGURATION ===
        self._quality_circuit_breaker = {
            'failure_count': 0,
            'last_failure_time': 0,
            'state': 'closed',  # closed, open, half_open
            'failure_threshold': 5,  # trips after 5 consecutive failures
            'recovery_timeout': 300,  # 5 minutes before allowing retry
            'half_open_max_calls': 3  # max calls in half-open state
        }
        
        # 🎯 HOLISTIC ORCHESTRATOR: Initialize unified orchestration system  
        self.holistic_orchestrator = None
        try:
            self.holistic_orchestrator = get_holistic_orchestrator()
            logger.info("🎯 Holistic Orchestrator initialized - all orchestration silos eliminated")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize Holistic Orchestrator: {e}")
        
        # 🔄 HOLISTIC LIFECYCLE: Initialize integrated task lifecycle management
        self.lifecycle_manager = None
        try:
            self.lifecycle_manager = get_holistic_lifecycle_manager()
            logger.info("🔄 Holistic Task Lifecycle Manager initialized - lifecycle silos eliminated")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize Holistic Task Lifecycle: {e}")
        
        # 🚀 ATOE: Maintain backward compatibility
        self.atoe = None
        if UNIFIED_ORCHESTRATOR_AVAILABLE and get_unified_orchestrator:
            try:
                self.atoe = get_unified_orchestrator()
                logger.info("🚀 ATOE initialized for legacy compatibility")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize ATOE: {e}")
                self.atoe = None

        # 🎭 SUB-AGENT ORCHESTRATION: Initialize optimized sub-agent system
        self.sub_agent_orchestrator = None
        self.sub_agent_performance_tracker = None
        if SUB_AGENT_ORCHESTRATION_AVAILABLE:
            try:
                self.sub_agent_orchestrator = optimized_orchestrator
                self.sub_agent_performance_tracker = track_agent_performance
                # Feature flag for gradual rollout
                self.sub_agent_orchestration_enabled = os.getenv("ENABLE_SUB_AGENT_ORCHESTRATION", "true").lower() == "true"
                if self.sub_agent_orchestration_enabled:
                    logger.info("🎭 Optimized Sub-Agent Orchestration System initialized - ready for intelligent agent coordination")
                else:
                    logger.info("🎭 Sub-Agent Orchestration System loaded but disabled via feature flag")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize Sub-Agent Orchestration System: {e}")
                self.sub_agent_orchestrator = None
                self.sub_agent_performance_tracker = None
                self.sub_agent_orchestration_enabled = False
        
        # 🔍 CRITICAL FIX: Adaptive Performance Metrics (Must be initialized in __init__)
        self.executor_metrics = {
            'loop_count': 0,
            'avg_loop_time': 0.0,
            'last_activity': datetime.now(),
            'load_level': 'medium'  # Start with medium load assumption
        }
        
        # Adaptive intervals based on system load - prevents infinite loops!
        self.adaptive_intervals = {
            "idle": 60,      # No activity - check every minute (prevents resource exhaustion)
            "low": 30,       # Some activity - every 30s
            "medium": 15,    # Active - every 15s  
            "high": 10,      # High activity - every 10s
            "overload": 5    # System stress - every 5s but limited operations
        }
        
        # Cache TTL for system metrics (avoid hammering database)
        self.cache_ttl = 10  # seconds
        self.operation_cache = {}

    async def get_workspace_settings(self, workspace_id: str):
        """Get workspace-specific settings with fallback to defaults"""
        try:
            project_settings = get_project_settings(workspace_id)
            return {
                'max_concurrent_tasks': await project_settings.get_max_concurrent_tasks(),
                'task_timeout': await project_settings.get_task_timeout(),
                'quality_threshold': await project_settings.get_quality_threshold(),
                'max_iterations': await project_settings.get_max_iterations(),
                'enable_quality_assurance': await project_settings.is_quality_assurance_enabled(),
                'deliverable_threshold': await project_settings.get_deliverable_threshold(),
                'max_deliverables': await project_settings.get_max_deliverables(),
                'max_budget': await project_settings.get_max_budget()
            }
        except Exception as e:
            logger.warning(f"Failed to load workspace settings for {workspace_id}, using defaults: {e}")
            return {
                'max_concurrent_tasks': self.default_max_concurrent_tasks,
                'task_timeout': self.default_execution_timeout,
                'quality_threshold': 85.0,
                'max_iterations': 3,
                'enable_quality_assurance': True,
                'deliverable_threshold': 50.0,
                'max_deliverables': 3,
                'max_budget': 10.0
            }

    @property
    def max_concurrent_tasks(self) -> int:
        """Get max concurrent tasks (workspace-aware when possible)"""
        return getattr(self, '_current_max_concurrent_tasks', self.default_max_concurrent_tasks)

    @property
    def execution_timeout(self) -> int:
        """Get execution timeout (workspace-aware when possible)"""
        return getattr(self, '_current_execution_timeout', self.default_execution_timeout)

    async def _debounced_query(self, query_key: str, query_func: Callable, *args, **kwargs):
        """Execute query with debouncing to prevent rapid repeated calls"""
        import asyncio
        from time import time
        
        current_time = time()
        
        # Check if there's already a pending query for this key
        if query_key in self._pending_queries:
            # Wait for the existing query to complete
            try:
                return await self._pending_queries[query_key]
            except asyncio.CancelledError:
                # If cancelled, proceed with new query
                pass
        
        # Check if we need to debounce this query
        last_query_time = self._query_debounce_cache.get(query_key, 0)
        time_since_last = current_time - last_query_time
        
        if time_since_last < self._debounce_window:
            # Wait for the debounce window to pass
            wait_time = self._debounce_window - time_since_last
            await asyncio.sleep(wait_time)
        
        # Create and store the query future
        async def _execute_query():
            try:
                self._query_debounce_cache[query_key] = time()
                result = await query_func(*args, **kwargs)
                return result
            finally:
                # Clean up the pending query
                if query_key in self._pending_queries:
                    del self._pending_queries[query_key]
        
        query_future = asyncio.create_task(_execute_query())
        self._pending_queries[query_key] = query_future
        
        return await query_future

    async def _debounced_get_workspace_tasks(self, workspace_id: str, limit: int = 50):
        """Get workspace tasks with debouncing"""
        return await self._debounced_query(
            f"tasks_{workspace_id}_{limit}",
            list_tasks,
            workspace_id, 
            limit=limit
        )

    async def _debounced_get_workspace_agents(self, workspace_id: str):
        """Get workspace agents with debouncing"""
        return await self._debounced_query(
            f"agents_{workspace_id}",
            list_agents,
            workspace_id
        )

    def _check_circuit_breaker_state(self, circuit_name: str = 'quality') -> str:
        """Check and update circuit breaker state"""
        circuit = self._quality_circuit_breaker
        current_time = time.time()
        
        if circuit['state'] == 'open':
            # Check if we should move to half-open
            if current_time - circuit['last_failure_time'] >= circuit['recovery_timeout']:
                circuit['state'] = 'half_open'
                circuit['failure_count'] = 0
                logger.info(f"🔌 Circuit breaker {circuit_name} moved to HALF-OPEN state")
                return 'half_open'
            return 'open'
        
        return circuit['state']

    async def _execute_with_circuit_breaker(self, operation_func: Callable, *args, **kwargs):
        """Execute operation with circuit breaker protection"""
        circuit = self._quality_circuit_breaker
        current_time = time.time()
        
        # Check circuit state
        state = self._check_circuit_breaker_state()
        
        if state == 'open':
            logger.warning("🔌 Circuit breaker OPEN - skipping quality validation")
            return None
            
        try:
            # Execute the operation
            result = await operation_func(*args, **kwargs)
            
            # Success - reset failure count
            circuit['failure_count'] = 0
            if circuit['state'] == 'half_open':
                circuit['state'] = 'closed'
                logger.info("🔌 Circuit breaker returned to CLOSED state")
            
            return result
            
        except Exception as e:
            # Failure - increment counter
            circuit['failure_count'] += 1
            circuit['last_failure_time'] = current_time
            
            logger.warning(f"🔌 Circuit breaker failure {circuit['failure_count']}/{circuit['failure_threshold']}: {e}")
            
            # Check if we should trip the circuit
            if circuit['failure_count'] >= circuit['failure_threshold']:
                circuit['state'] = 'open'
                logger.error(f"🔌 Circuit breaker TRIPPED - quality validation disabled for {circuit['recovery_timeout']}s")
            
            # Don't re-raise the exception, just return None to indicate failure
            return None

    async def _safe_quality_validation(self, *args, **kwargs):
        """Quality validation with circuit breaker protection"""
        return await self._execute_with_circuit_breaker(
            self._original_quality_validation, *args, **kwargs
        )

    async def start(self):
        """Start the task executor"""
        if self.running:
            logger.warning("Task executor already running")
            return
            
        self.running = True
        self.paused = False
        self.pause_event.set()
        self.execution_log = []

        # 🔍 Start task execution monitoring
        if TASK_MONITOR_AVAILABLE and not self.monitoring_started:
            try:
                await start_monitoring()
                self.monitoring_started = True
                logger.info("✅ Task execution monitoring started")
            except Exception as e:
                logger.warning(f"⚠️ Failed to start task monitoring: {e}")

        logger.info("Starting task executor with anti-loop protection")
        logger.info(f"Max concurrent tasks: {self.max_concurrent_tasks}")
        logger.info(f"Task timeout: {self.execution_timeout}s")
        logger.info(f"Auto-generation: {'ENABLED' if self.auto_generation_enabled else 'DISABLED'}")
        logger.info(f"Runaway check interval: {self.runaway_check_interval}s")
        logger.info(f"FINALIZATION priority boost: {FINALIZATION_TASK_PRIORITY_BOOST}")
        logger.info(f"Smart prioritization: {'ENABLED' if ENABLE_SMART_PRIORITIZATION else 'DISABLED'}")
        
        # 🚦 Check rate limiting availability
        if API_RATE_LIMITER_AVAILABLE:
            logger.info("🚦 API Rate Limiter: ENABLED - Managing external API calls")
            # Log initial rate limit stats
            stats = api_rate_limiter.get_stats()
            for provider, provider_stats in stats.items():
                logger.info(f"  {provider}: {provider_stats['available_tokens']} tokens available")

        # Avvia worker per processare la queue
        self.worker_tasks = [
            asyncio.create_task(self._anti_loop_worker()) 
            for _ in range(self.max_concurrent_tasks)
        ]
        
        # 🔧 Start autonomous recovery scheduler
        if FAILED_TASK_RESOLVER_AVAILABLE and start_autonomous_recovery_scheduler:
            try:
                asyncio.create_task(start_autonomous_recovery_scheduler())
                logger.info("🔧 Autonomous task recovery scheduler started")
            except Exception as e:
                logger.warning(f"⚠️ Failed to start recovery scheduler: {e}")
        
        # Avvia il main execution loop
        asyncio.create_task(self.execution_loop())
        logger.info("Task executor started successfully")

    async def stop(self):
        """Stop the task executor"""
        if not self.running:
            logger.warning("Task executor is not running")
            return
            
        logger.info("Stopping task executor...")
        self.running = False
        self.paused = True
        self.pause_event.set()

        # Invia segnali di stop ai worker
        for _ in range(len(self.worker_tasks)):
            try:
                await asyncio.wait_for(self.task_queue.put(None), timeout=2.0)
            except asyncio.TimeoutError:
                logger.warning("Timeout sending stop signal to task queue")
            except asyncio.QueueFull:
                logger.warning("Task queue full while sending stop signal")

        # Aspetta che i worker terminino
        if self.worker_tasks:
            results = await asyncio.gather(*self.worker_tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception) and not isinstance(result, asyncio.CancelledError):
                    logger.error(f"Worker task {i} finished with error: {result}", exc_info=result)
        
        self.worker_tasks = []
        logger.info("Task executor stopped")

    async def pause(self):
        """Pause the task executor"""
        if not self.running:
            logger.warning("Cannot pause: Task executor is not running")
            return
        if self.paused:
            logger.info("Task executor is already paused")
            return
            
        self.paused = True
        self.pause_event.clear()
        logger.info("Task executor paused")

    async def resume(self):
        """Resume the task executor"""
        if not self.running:
            logger.warning("Cannot resume: Task executor is not running")
            return
        if not self.paused:
            logger.info("Task executor is already running")
            return
            
        self.paused = False
        self.pause_event.set()
        
        # 🔧 FIX: Resume auto-paused workspaces
        await self._resume_all_paused_workspaces()
        
        logger.info("Task executor resumed")

    async def add_task_to_queue(self, task_dict: Dict[str, Any]) -> bool:
        """
        🚀 IMMEDIATE TASK EXECUTION: Add task directly to executor queue
        
        This bypasses normal polling and immediately queues task for execution.
        Used by goal monitor for corrective tasks that need immediate action.
        """
        try:
            if not self.running:
                logger.warning("Cannot add task to queue: executor not running")
                return False
            
            if self.paused:
                logger.warning("Cannot add task to queue: executor is paused")
                return False
            
            task_id = task_dict.get("id")
            task_name = task_dict.get("name", "Unknown Task")
            
            # Prevent duplicate queueing
            if task_id in self.queued_task_ids or task_id in self.active_task_ids:
                logger.warning(f"Task {task_id} already queued or active, skipping")
                return False
            
            # Add to queue with priority handling
            priority = task_dict.get("priority", "medium")
            is_corrective = task_dict.get("is_corrective", False)
            
            current_agent_id = task_dict.get("agent_id")
            assigned_role = task_dict.get("assigned_to_role")
            workspace_id = task_dict.get("workspace_id") # Ensure workspace_id is available

            if not current_agent_id and assigned_role and workspace_id:
                logger.info(f"Task {task_id} needs agent assignment for role '{assigned_role}' before queuing.")
                assigned_agent_info = await self._assign_agent_to_task_by_role(
                    task_dict, workspace_id, assigned_role
                )
                
                if assigned_agent_info and "id" in assigned_agent_info:
                    task_dict["agent_id"] = str(assigned_agent_info["id"])
                    logger.info(f"Task {task_id} assigned to agent {assigned_agent_info['name']} (ID: {task_dict['agent_id']}) for role '{assigned_role}' before queuing.")
                else:
                    logger.warning(
                        f"Could not assign agent for role '{assigned_role}' to task {task_id}. Skipping task."
                    )
                    return False # Do not queue if agent assignment fails
            
            # Log immediate queueing
            logger.warning(f"⚡ IMMEDIATE QUEUE: {task_name} (ID: {task_id}) - Priority: {priority}, Corrective: {is_corrective}")
            
            # Add to task queue
            await self.task_queue.put(task_dict)
            self.queued_task_ids.add(task_id)
            
            # Log execution tracking
            self.execution_log.append({
                "event": "task_immediate_queue",
                "task_id": task_id,
                "task_name": task_name,
                "workspace_id": task_dict.get("workspace_id"),
                "priority": priority,
                "is_corrective": is_corrective,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"✅ Task {task_id} added to queue immediately. Queue size: {self.task_queue.qsize()}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding task to queue: {e}")
            return False

    async def _anti_loop_worker(self):
        """Worker thread che processa task dalla queue con protezione anti-loop"""
        worker_id = uuid4()
        logger.info(f"Anti-loop worker {worker_id} started")
        
        while self.running:
            try:
                await self.pause_event.wait()
                if not self.running:
                    break

                manager: Optional[AgentManager] = None
                task_dict_from_queue: Optional[Dict] = None
                
                try:
                    # Get item from queue
                    queue_item = await asyncio.wait_for(
                        self.task_queue.get(), timeout=1.0
                    )
                    
                    # Handle shutdown sentinel
                    if queue_item is None:
                        self.task_queue.task_done()
                        logger.info(f"Anti-loop worker {worker_id} received termination signal")
                        break
                    
                    # 🔧 FIX: Handle both tuple and single dict formats in queue
                    if isinstance(queue_item, tuple) and len(queue_item) == 2:
                        manager, task_dict_from_queue = queue_item
                    elif isinstance(queue_item, dict):
                        # Handle legacy format where only task dict was queued
                        manager = None
                        task_dict_from_queue = queue_item
                    else:
                        logger.error(f"Invalid queue item format: {type(queue_item)}, items: {len(queue_item) if hasattr(queue_item, '__len__') else 'N/A'}")
                        self.task_queue.task_done()
                        continue
                    
                except asyncio.TimeoutError:
                    continue

                if task_dict_from_queue is None:  # Additional safety check
                    self.task_queue.task_done()
                    logger.info(f"Anti-loop worker {worker_id} received empty task dict")
                    continue
                
                task_id = task_dict_from_queue.get("id", "UnknownID")
                task_name = task_dict_from_queue.get("name", "Unnamed Task")
                workspace_id = task_dict_from_queue.get("workspace_id", "UnknownWS")

                # Ensure created_at and updated_at are present for Pydantic validation
                if "created_at" not in task_dict_from_queue:
                    task_dict_from_queue["created_at"] = datetime.now().isoformat()
                if "updated_at" not in task_dict_from_queue:
                    task_dict_from_queue["updated_at"] = datetime.now().isoformat()

                # Update queued/active trackers
                self.queued_task_ids.discard(task_id)
                if task_id in self.active_task_ids:
                    logger.warning(f"Worker {worker_id} received already active task {task_id}. Skipping")
                    self.task_queue.task_done()
                    continue
                self.active_task_ids.add(task_id)

                logger.info(f"WORKER {worker_id}: Picking up task: '{task_name}' (ID: {task_id}) from W: {workspace_id}. Q size: {self.task_queue.qsize()}")
                
                # 🔧 FIX: Ensure manager is initialized if not present (legacy task format or lost reference)
                if manager is None:
                    logger.info(f"WORKER {worker_id}: Attempting to initialize manager for task: {task_id}")
                    try:
                        from ai_agents.manager import AgentManager
                        manager = AgentManager(workspace_id=UUID(workspace_id))
                        if not await manager.initialize(): # CRITICAL: Call initialize()
                            logger.error(f"WORKER {worker_id}: ❌ Failed to initialize manager for task {task_id}. Skipping task.")
                            await self._force_complete_task(
                                task_dict_from_queue, 
                                f"Failed to initialize manager: {str(e)[:200]}",
                                status_to_set=TaskStatus.FAILED.value
                            )
                            self.task_queue.task_done()
                            self.active_task_ids.discard(task_id)
                            continue
                        logger.debug(f"WORKER {worker_id}: ✅ Manager initialized successfully for task {task_id}")
                    except Exception as e:
                        logger.error(f"WORKER {worker_id}: ❌ Exception during manager initialization for task {task_id}: {e}")
                        await self._force_complete_task(
                            task_dict_from_queue, 
                            f"Exception initializing manager: {str(e)[:200]}",
                            status_to_set=TaskStatus.FAILED.value
                        )
                        self.task_queue.task_done()
                        self.active_task_ids.discard(task_id)
                        continue

                # 🤖 AI-DRIVEN BACKUP AGENT ASSIGNMENT (Pillar 1: Domain Agnostic, Pillar 8: AI-Driven)
                # If agent_id is missing, attempt backup assignment before failing
                current_agent_id = task_dict_from_queue.get("agent_id")
                assigned_role = task_dict_from_queue.get("assigned_to_role")
                
                if not current_agent_id and assigned_role:
                    logger.warning(f"WORKER {worker_id}: ⚠️ Task {task_id} reached execution without agent_id. Attempting backup assignment for role '{assigned_role}'")
                    try:
                        assigned_agent_info = await self._assign_agent_to_task_by_role(
                            task_dict_from_queue, workspace_id, assigned_role
                        )
                        
                        if assigned_agent_info and "id" in assigned_agent_info:
                            # Update the task dict for execution
                            task_dict_from_queue["agent_id"] = str(assigned_agent_info["id"])
                            current_agent_id = str(assigned_agent_info["id"])
                            logger.info(f"WORKER {worker_id}: ✅ Backup assignment successful: Task {task_id} assigned to agent {assigned_agent_info['name']} (ID: {current_agent_id})")
                        else:
                            logger.error(f"WORKER {worker_id}: ❌ Backup agent assignment failed for role '{assigned_role}' in task {task_id}")
                    except Exception as e:
                        logger.error(f"WORKER {worker_id}: ❌ Exception during backup agent assignment for task {task_id}: {e}")

                # CRITICAL CHECK: Ensure agent_id is present after backup assignment attempts
                if not task_dict_from_queue.get("agent_id"):
                    error_msg = f"Task {task_id} ('{task_name}') cannot execute: no agent_id after all assignment attempts (role: {assigned_role})"
                    logger.error(f"WORKER {worker_id}: {error_msg}")
                    await self._force_complete_task(
                        task_dict_from_queue, 
                        error_msg,
                        status_to_set=TaskStatus.FAILED.value
                    )
                    self.task_queue.task_done()
                    self.active_task_ids.discard(task_id)
                    continue
                
                # Validazione anti-loop
                logger.info(f"WORKER {worker_id}: Validating task {task_id} for anti-loop.")
                if not await self._validate_task_execution(task_dict_from_queue):
                    logger.warning(f"Worker {worker_id} skipping task {task_id} - failed anti-loop validation")
                    self.task_queue.task_done()
                    self.active_task_ids.discard(task_id)
                    await asyncio.sleep(0.05)
                    continue
                
                # Esecuzione del task
                self.active_tasks_count += 1
                execution_result = None  # Inizializza a None
                try:
                    logger.info(f"WORKER {worker_id}: Preparing to execute task {task_id}.")
                    logger.info(f"WORKER {worker_id}: Task data: {task_dict_from_queue}")
                    if manager is None:
                        raise ValueError(f"Manager is None for task {task_id}")
                    
                    # LOGGING DETTAGLIATO
                    logger.info(f"--- TASK LIFECYCLE START: {task_id} ---")
                    logger.info(f"Task Name: {task_name}")
                    logger.info(f"Assigned Agent ID: {task_dict_from_queue.get('agent_id')}")
                    
                    # Execute task with anti-loop and tracking
                    execution_result = await self._execute_task_with_anti_loop_and_tracking(manager, task_dict_from_queue)

                    # 🚀 ASYNCHRONOUS FINALIZATION: Schedule post-execution logic to run in the background
                    # This prevents the worker from being blocked by DB updates and trigger logic, resolving hanging tasks.
                    # Add timeout to prevent indefinite hanging
                    finalization_task = asyncio.create_task(self._finalize_task_completion(task_id, execution_result))
                    
                    # Monitor finalization with timeout (30 seconds should be more than enough)
                    try:
                        await asyncio.wait_for(finalization_task, timeout=30.0)
                    except asyncio.TimeoutError:
                        logger.error(f"⏰ Task finalization for {task_id} timed out after 30s. Forcing completion.")
                        # Force update task status to prevent hanging
                        try:
                            if execution_result and hasattr(execution_result, 'status'):
                                await update_task_status(task_id, execution_result.status.value, {"timeout": "finalization_timeout"})
                            else:
                                await update_task_status(task_id, TaskStatus.FAILED.value, {"error": "finalization_timeout"})
                        except Exception as force_update_error:
                            logger.error(f"Failed to force update task {task_id} after timeout: {force_update_error}")

                except (AttributeError, TypeError) as e_specific:
                    logger.error(f"WORKER {worker_id}: SPECIFIC ERROR executing task {task_id}: {e_specific}", exc_info=True)
                    await self._force_complete_task(
                        task_dict_from_queue, 
                        f"Specific execution error: {str(e_specific)[:250]}",
                        status_to_set=TaskStatus.FAILED.value
                    )
                except Exception as e_exec:
                    logger.error(f"WORKER {worker_id}: CRITICAL error executing task {task_id}: {e_exec}", exc_info=True)
                    await self._force_complete_task(
                        task_dict_from_queue, 
                        f"Critical worker error: {str(e_exec)[:250]}",
                        status_to_set=TaskStatus.FAILED.value
                    )
                finally:
                    self.active_tasks_count -= 1
                    self.task_queue.task_done()
                    self.active_task_ids.discard(task_id)
                    
                    # Decrementa il counter anti-loop per permettere l'esecuzione di altre task
                    if workspace_id:
                        current_count = self.workspace_anti_loop_task_counts.get(workspace_id, 0)
                        if current_count > 0:
                            self.workspace_anti_loop_task_counts[workspace_id] = current_count - 1
                            logger.debug(f"WORKER {worker_id}: Decremented anti-loop counter for W:{workspace_id[:8]} to {current_count - 1}")
                    
                    logger.info(f"WORKER {worker_id}: Finished processing task {task_id}. Active tasks: {self.active_tasks_count}")
                    
                    # Marca come completato nel tracker per anti-loop
                    if workspace_id and task_id:
                        self.task_completion_tracker[workspace_id].add(task_id)

            except asyncio.CancelledError:
                logger.info(f"Anti-loop worker {worker_id} cancelled")
                break
            except Exception as e_worker_loop:
                logger.error(f"Unhandled error in anti-loop worker {worker_id} main loop: {e_worker_loop}", exc_info=True)
                await asyncio.sleep(5)  # Pausa prima di ritentare
        
        logger.info(f"Anti-loop worker {worker_id} exiting")

    async def _finalize_task_completion(self, task_id: str, execution_result: Optional[TaskExecutionOutput]):
        """
        Handles all post-execution logic for a task in a non-blocking way.
        This includes updating the database, logging, and triggering subsequent actions.
        """
        start_time = asyncio.get_event_loop().time()
        try:
            logger.info(f"--- TASK FINALIZATION START: {task_id} ---")
            logger.info(f"Agent Execution Result: {execution_result}")

            if execution_result and hasattr(execution_result, 'status'):
                final_status = execution_result.status.value
                logger.info(f"Final Status from ExecutionResult: {final_status}")

                try:
                    import uuid
                    from datetime import datetime
                    result_dict = execution_result.model_dump()

                    def convert_uuids(obj):
                        if isinstance(obj, uuid.UUID):
                            return str(obj)
                        elif isinstance(obj, dict):
                            return {k: convert_uuids(v) for k, v in obj.items()}
                        elif isinstance(obj, list):
                            return [convert_uuids(item) for item in obj]
                        else:
                            return obj
                    
                    serializable_result = convert_uuids(result_dict)
                    await update_task_status(task_id, final_status, serializable_result)
                except Exception as serialize_error:
                    logger.error(f"Failed to serialize execution result for task {task_id}: {serialize_error}")
                    from datetime import datetime
                    basic_result = {
                        "status": final_status,
                        "output": str(execution_result)[:1000],
                        "timestamp": datetime.now().isoformat(),
                        "serialization_error": str(serialize_error)
                    }
                    await update_task_status(task_id, final_status, basic_result)
                
                logger.info(f"Task {task_id} status updated to {final_status} in database.")
            else:
                logger.error(f"Execution result for task {task_id} was invalid or missing status. Forcing to FAILED.")
                task_dict = await get_task(task_id)
                if task_dict:
                    await self._force_complete_task(task_dict, "Invalid execution result", status_to_set=TaskStatus.FAILED.value)

            logger.info(f"--- TASK FINALIZATION END: {task_id} ---")

        except Exception as e:
            logger.error(f"CRITICAL error during task finalization for {task_id}: {e}", exc_info=True)
            # Attempt to mark the task as failed as a last resort
            try:
                task_dict = await get_task(task_id)
                if task_dict:
                    await self._force_complete_task(task_dict, f"Finalization failed: {e}", status_to_set=TaskStatus.FAILED.value)
            except Exception as finalization_fail_error:
                logger.error(f"Could not even force-fail task {task_id} after finalization error: {finalization_fail_error}")
        finally:
            duration = asyncio.get_event_loop().time() - start_time
            logger.info(f"--- TASK FINALIZATION END: {task_id} in {duration:.2f}s ---")

    async def _assign_agent_to_task_by_role(self, task_dict: Dict, workspace_id: str, role: str) -> Optional[Dict]:
        """
        🎯 ENHANCED: Find agent using unified AgentStatusManager for consistent status handling
        Trova un agente attivo per il ruolo specificato e aggiorna il task nel DB.
        Restituisce le info dell'agente assegnato o None.
        """
        try:
            # 🎯 UNIFIED AGENT MANAGEMENT: Use AgentStatusManager if available
            if AGENT_STATUS_MANAGER_AVAILABLE and agent_status_manager:
                try:
                    # 🎯 **HOLISTIC INTEGRATION**: Use full AI classification for optimal agent matching
                    classification_result = None
                    
                    # Get AI classification if not already available
                    if task_dict.get("task_type") and not task_dict.get("classification_result"):
                        try:
                            from services.ai_task_classifier import classify_task_ai
                            classification_result = await classify_task_ai(
                                task_dict, 
                                {"description": task_dict.get("description", "")}
                            )
                            # Store classification for future use
                            task_dict["classification_result"] = classification_result
                            logger.info(f"🎯 Task classification completed for holistic agent matching")
                        except Exception as e:
                            logger.warning(f"⚠️ Task classification failed, using basic matching: {e}")
                    else:
                        classification_result = task_dict.get("classification_result")
                    
                    match_result = await agent_status_manager.find_best_agent_for_task(
                        workspace_id=workspace_id,
                        required_role=role,
                        task_name=task_dict.get("name"),
                        task_description=task_dict.get("description"),
                        task_type=task_dict.get("task_type"),
                        classification_result=classification_result  # 🎯 Pass full classification data
                    )
                    
                    if match_result.agent:
                        selected_agent_info = match_result.agent
                        
                        # Convert AgentInfo to dict format for compatibility
                        selected_agent = {
                            "id": selected_agent_info.id,
                            "name": selected_agent_info.name,
                            "role": selected_agent_info.role,
                            "status": selected_agent_info.status.value,
                            "seniority": selected_agent_info.seniority,
                            "workspace_id": selected_agent_info.workspace_id
                        }
                        
                        logger.info(f"🎯 UNIFIED AGENT MATCH: {match_result.match_method} - "
                                   f"confidence: {match_result.match_confidence:.2f} - "
                                   f"agent: {selected_agent['name']} ({selected_agent['role']}) - "
                                   f"fallback: {match_result.fallback_used}")
                        
                        # 🔄 HOLISTIC LIFECYCLE: Update agent assignment phase
                        if self.lifecycle_manager:
                            try:
                                await update_task_lifecycle_phase(
                                    task_id=task_dict.get("id", "unknown"),
                                    phase=LifecyclePhase.AGENT_ASSIGNMENT,
                                    data={
                                        "agent_id": selected_agent["id"],
                                        "agent_name": selected_agent["name"],
                                        "agent_role": selected_agent["role"],
                                        "agent_seniority": selected_agent["seniority"],
                                        "match_method": match_result.match_method,
                                        "match_confidence": match_result.match_confidence,
                                        "classification_used": classification_result is not None
                                    }
                                )
                            except Exception as e:
                                logger.warning(f"⚠️ Failed to update agent assignment lifecycle: {e}")
                        
                    else:
                        # No suitable agent found through unified system
                        logger.error(f"❌ UNIFIED AGENT MATCHING: {match_result.reason} for role '{role}' in workspace {workspace_id}")
                        
                        # Try auto-creation as fallback
                        auto_created_agent = await self._auto_create_basic_agent(workspace_id, role)
                        if auto_created_agent:
                            logger.info(f"✅ Auto-created agent {auto_created_agent['name']} for role '{role}' in workspace {workspace_id}")
                            selected_agent = auto_created_agent
                        else:
                            logger.error(f"❌ Failed to auto-create agent for role '{role}' in workspace {workspace_id}")
                            return None
                        
                except Exception as asm_error:
                    logger.warning(f"⚠️ AgentStatusManager error, falling back to legacy logic: {asm_error}")
                    # Fall through to legacy logic
                    selected_agent = None
                    
            else:
                logger.debug("AgentStatusManager not available, using legacy agent assignment")
                selected_agent = None
            
            # 🔄 FALLBACK: Legacy agent assignment logic if unified system not available or failed
            if not selected_agent:
                agents_in_db = await self._cached_list_agents(workspace_id)
                
                # CRITICAL FIX: Check for "available" status instead of "active" 
                # Agents are created with "available" status in database.py:494
                compatible_agents = [
                    agent for agent in agents_in_db
                    if agent.get("role", "").lower() == role.lower()
                    and agent.get("status") in ["available", "active"]  # Accept both statuses
                ]

                # If no exact role match, try fallback strategies
                if not compatible_agents:
                    logger.warning(f"No exact role match for '{role}' in workspace {workspace_id}. Trying fallback strategies...")
                    
                    # Strategy 1: If role is 'expert', find any expert-level agent
                    if role.lower() == "expert":
                        compatible_agents = [
                            agent for agent in agents_in_db
                            if agent.get("seniority", "").lower() == "expert"
                            and agent.get("status") in ["available", "active"]
                        ]
                        if compatible_agents:
                            logger.info(f"Found expert agent by seniority: {compatible_agents[0].get('name')} ({compatible_agents[0].get('role')})")
                    
                    # Strategy 2: If role contains 'specialist', find any specialist
                    elif "specialist" in role.lower():
                        compatible_agents = [
                            agent for agent in agents_in_db
                            if "specialist" in agent.get("role", "").lower()
                            and agent.get("status") in ["available", "active"]
                        ]
                        if compatible_agents:
                            logger.info(f"Found specialist agent: {compatible_agents[0].get('name')} ({compatible_agents[0].get('role')})")
                    
                    # Strategy 3: Find any high-seniority active agent
                    if not compatible_agents:
                        for seniority in ["expert", "senior"]:
                            compatible_agents = [
                                agent for agent in agents_in_db
                                if agent.get("seniority", "").lower() == seniority
                                and agent.get("status") in ["available", "active"]
                            ]
                            if compatible_agents:
                                logger.info(f"Found {seniority} agent as fallback: {compatible_agents[0].get('name')} ({compatible_agents[0].get('role')})")
                                break

                if not compatible_agents:
                    # Check if this is a special error role from intelligent agent selection
                    if role in ["no_agents_available", "task_assignment_failed"]:
                        logger.error(f"❌ Agent selection failed for task {task_dict.get('id')} in workspace {workspace_id}: {role}")
                        return None
                    
                    # ENHANCED FIX: Try to auto-create a basic agent for this role if none exist
                    logger.warning(f"❌ No agent found for role '{role}' in workspace {workspace_id}. Attempting auto-provisioning...")
                    auto_created_agent = await self._auto_create_basic_agent(workspace_id, role)
                    if auto_created_agent:
                        logger.info(f"✅ Auto-created agent {auto_created_agent['name']} for role '{role}' in workspace {workspace_id}")
                        selected_agent = auto_created_agent
                    else:
                        logger.error(f"❌ Failed to auto-create agent for role '{role}' in workspace {workspace_id}. Task will be skipped.")
                        return None
                else:
                    # Logica di selezione: per ora il primo, ma potrebbe essere più complessa
                    selected_agent = compatible_agents[0]

            # Final assignment and database update
            agent_id_to_assign = str(selected_agent["id"])

            # Aggiorna il task nel DB con l'agent_id assegnato
            update_payload = {
                "agent_id": agent_id_to_assign, 
                "status_detail": f"Assigned to agent {selected_agent['name']}"
            }
            
            # Aggiornamento diretto tramite update_task_status
            updated_task = await update_task_status(
                task_id=task_dict["id"], 
                status=task_dict.get("status", TaskStatus.PENDING.value),
                result_payload=update_payload
            )
            # Send WebSocket notification
            await notify_task_status_change(task_dict["id"], task_dict.get("status", TaskStatus.PENDING.value), updated_task)
            
            if updated_task:
                logger.info(f"Task {task_dict['id']} DB record updated with agent_id {agent_id_to_assign}")
                return selected_agent
            else:
                logger.error(f"Failed to update task {task_dict['id']} with agent_id {agent_id_to_assign} in DB")
                return None

        except Exception as e:
            logger.error(f"Error assigning agent to task by role '{role}' for task {task_dict.get('id')}: {e}", exc_info=True)
            return None
    
    async def _auto_create_basic_agent(self, workspace_id: str, role: str) -> Optional[Dict[str, Any]]:
        """
        🚀 AUTO-PROVISIONING: Create a basic agent for a role when none exist
        
        Prevents workspace deadlock when no agents are available for critical roles.
        """
        try:
            from database import create_agent
            import random
            
            # Basic agent configuration based on role
            agent_config = {
                "workspace_id": workspace_id,
                "name": f"Auto_{role.replace(' ', '_')}_{random.randint(1000, 9999)}",
                "role": role,
                "seniority": "senior",  # Default to senior for reliability
                "description": f"Auto-provisioned agent for {role} tasks. Created when no agents were available for this role.",
                "system_prompt": f"""You are a {role} specialist. Your primary responsibility is to execute {role.lower()} tasks efficiently and accurately.

🚫 **ZERO-PLANNING RULE: CRITICAL**
- **DO NOT** output a plan, an outline, or a description of the work to be done.
- **DO** produce the final, complete, and ready-to-use asset itself.
- **Example of what NOT to do**: "To create the report, I will first analyze the data, then structure the sections..."
- **Example of what TO DO**: Directly output the full, formatted report.

🏁 **FINAL OUTPUT REQUIREMENTS:**
- The `result` field MUST contain the complete, final, and ready-to-use asset.
- DO NOT put a summary or description in the `result` field.

Use your tools and expertise to complete assigned tasks. Always provide structured outputs in the required JSON format.
Focus on delivering practical, actionable results that move the project forward.""",
                "llm_config": {
                    "model": "gpt-4o-mini",
                    "temperature": 0.3
                },
                "tools": [
                    {"type": "web_search", "name": "web_search", "description": "Search the web for current information"},
                    {"type": "file_search", "name": "file_search", "description": "Search through uploaded files and documents"}
                ]
            }
            
            logger.info(f"🚀 Auto-creating basic agent for role '{role}' in workspace {workspace_id}")
            
            # Create the agent in database
            created_agent = await create_agent(**agent_config)
            if created_agent:
                logger.info(f"✅ Successfully auto-created agent {created_agent['id']}: {created_agent['name']}")
                
                # Refresh the agent manager's cache to include the new agent
                if workspace_id in self.workspace_managers:
                    # Re-initialize the agent manager to pick up the new agent
                    try:
                        await self.workspace_managers[workspace_id].initialize()
                        logger.info(f"🔄 Refreshed agent manager cache for workspace {workspace_id}")
                    except Exception as refresh_error:
                        logger.warning(f"⚠️ Failed to refresh agent manager cache: {refresh_error}")
                
                return created_agent
            else:
                logger.error(f"❌ Database failed to create agent for role '{role}'")
                return None
                
        except Exception as e:
            logger.error(f"❌ Exception during auto-agent creation for role '{role}': {e}", exc_info=True)
            return None

    async def _validate_task_execution(self, task_dict: Dict[str, Any]) -> bool:
        """
        🤖 AI-DRIVEN: Valida che un task possa essere eseguito (anti-loop protection)
        Enhanced with smart bypassing for critical corrective tasks
        """
        task_id = task_dict.get("id")
        workspace_id = task_dict.get("workspace_id")

        if not task_id or not workspace_id:
            logger.error(f"Invalid task data for validation: id={task_id}, ws={workspace_id}")
            return False

        # CIRCUIT BREAKER: Prevent infinite loops
        total_workspace_tasks = self.workspace_anti_loop_task_counts.get(workspace_id, 0)
        if total_workspace_tasks > 50: # Max 50 tasks per workspace
            logger.critical(f"CIRCUIT BREAKER TRIPPED: Workspace {workspace_id} exceeded 50 tasks. Forcing completion as error.")
            await update_workspace_status(workspace_id, WorkspaceStatus.ERROR.value)
            return False

        # Check se il task è già stato completato
        if task_id in self.task_completion_tracker.get(workspace_id, set()):
            logger.warning(f"Anti-loop: Task {task_id} in W:{workspace_id} already completed. Skipping")
            current_status = task_dict.get("status")
            if current_status == TaskStatus.PENDING.value:
                await self._force_complete_task(
                    task_dict, 
                    "Skipped: Already completed (tracker)",
                    status_to_set=TaskStatus.COMPLETED.value
                )
            return False

        # 🚀 ATOE: Dynamic workspace task limit with AI-driven skip prevention
        current_anti_loop_count = self.workspace_anti_loop_task_counts.get(workspace_id, 0)
        
        # Get dynamic limit recommendation with ATOE integration
        effective_limit = self.max_tasks_per_workspace_anti_loop
        atoe_recommendation = None
        
        # 🎯 PRIMARY: Holistic orchestration for unified decision making
        if self.holistic_orchestrator:
            try:
                # Get holistic orchestration insights
                workspace_context = {
                    "workspace_id": workspace_id,
                    "current_pending_count": current_anti_loop_count,
                    "max_limit": self.max_tasks_per_workspace_anti_loop,
                    "active_agents": await self._count_active_agents(workspace_id)
                }
                
                orchestration_insights = await self.holistic_orchestrator.get_orchestration_insights(workspace_id)
                optimal_mode = orchestration_insights.get("optimal_mode_recommendation", "hybrid")
                
                logger.info(f"🎯 HOLISTIC ORCHESTRATION: Using {optimal_mode} mode for task {task_id}")
                
                # Holistic orchestrators make integrated decisions
                # For now, maintain the same logic but with holistic context awareness
                effective_limit = self.max_tasks_per_workspace_anti_loop
                
            except Exception as e:
                logger.warning(f"⚠️ Holistic orchestration analysis failed: {e}")

        # 🎭 SUB-AGENT ORCHESTRATION: Intelligent agent coordination
        sub_agent_coordination_attempted = False
        if (self.sub_agent_orchestrator and self.sub_agent_orchestration_enabled and 
            SUB_AGENT_ORCHESTRATION_AVAILABLE):
            try:
                task_description = task_dict.get("name", "") + " " + task_dict.get("description", "")
                task_context = {
                    "workspace_id": workspace_id,
                    "task_id": task_id,
                    "task_type": task_dict.get("task_type", "hybrid"),
                    "priority": task_dict.get("priority", "medium"),
                    "agent_id": task_dict.get("agent_id"),
                    "current_agent_count": await self._count_active_agents(workspace_id)
                }
                
                # Check if task requires sub-agent coordination
                suggested_agents = await suggest_optimized_agents(task_description, task_context)
                
                # Only orchestrate if multiple specialized agents are suggested
                if len(suggested_agents) >= 2:
                    logger.info(f"🎭 SUB-AGENT ORCHESTRATION: Task {task_id} requires {len(suggested_agents)} agents: {', '.join(suggested_agents)}")
                    
                    # This would orchestrate the task through specialized agents
                    # For now, we track the recommendation and let normal execution proceed
                    sub_agent_coordination_attempted = True
                    
                    # Track this for performance metrics
                    if self.sub_agent_performance_tracker:
                        await self.sub_agent_performance_tracker("orchestration_trigger", {
                            "task_id": task_id,
                            "agents_suggested": suggested_agents,
                            "task_complexity": len(suggested_agents),
                            "timestamp": datetime.now().isoformat(),
                            "status": "triggered"
                        })
                else:
                    logger.debug(f"🎭 SUB-AGENT ORCHESTRATION: Task {task_id} uses single agent - no coordination needed")
                    
            except Exception as e:
                logger.warning(f"⚠️ Sub-agent orchestration analysis failed: {e}")
                sub_agent_coordination_attempted = False
        
        # 🚀 FALLBACK: ATOE for backward compatibility  
        elif self.atoe:
            try:
                # Get comprehensive ATOE recommendations
                atoe_recommendation = await self.atoe.get_orchestration_recommendation(
                    workspace_id=workspace_id,
                    current_pending_count=current_anti_loop_count,
                    task_metadata={
                        "task_id": task_id,
                        "task_name": task_dict.get("name", "Unknown"),
                        "task_priority": task_dict.get("priority", "medium"),
                        "is_critical": await self._is_critical_corrective_task(task_dict)
                    }
                )
                
                if atoe_recommendation.should_proceed:
                    effective_limit = atoe_recommendation.recommended_limit
                    logger.info(f"🚀 ATOE FALLBACK: Proceed with limit {effective_limit}")
                    
                    # Update ATOE metrics for continuous improvement
                    await self.atoe.update_workspace_metrics(
                        workspace_id=workspace_id,
                        task_completion_data={
                            "task_id": task_id,
                            "pending_tasks": current_anti_loop_count,
                            "task_skip_count": 0,  # Will be updated if skipped
                            "task_execution_count": 1,
                            "status": "approved"
                        }
                    )
                else:
                    logger.warning(f"🚀 ATOE RECOMMENDATION: Skip task {task_id} "
                                 f"(reasoning: {atoe_recommendation.reasoning[:100]})")
                    
                    # Update skip metrics for ATOE learning
                    await self.atoe.update_workspace_metrics(
                        workspace_id=workspace_id,
                        task_completion_data={
                            "task_id": task_id,
                            "pending_tasks": current_anti_loop_count,
                            "task_skip_count": 1,
                            "task_execution_count": 0,
                            "status": "skipped"
                        }
                    )
                    return False
                    
            except Exception as e:
                logger.warning(f"ATOE orchestration error, falling back to dynamic anti-loop: {e}")
                atoe_recommendation = None
        
        # Fallback: Use dynamic anti-loop manager if ATOE not available
        if not atoe_recommendation and DYNAMIC_ANTI_LOOP_AVAILABLE and dynamic_anti_loop_manager:
            try:
                # Get AI-recommended limit based on real-time metrics
                effective_limit = await dynamic_anti_loop_manager.get_recommended_limit(workspace_id)
                
                # Update skip percentage feedback for learning
                if current_anti_loop_count > 0:
                    skip_percentage = current_anti_loop_count / (current_anti_loop_count + 1)  # Approximate
                    await dynamic_anti_loop_manager.update_skip_percentage(workspace_id, skip_percentage)
                
                logger.debug(f"🤖 Dynamic limit for W:{workspace_id[:8]}: {effective_limit} (base: {self.max_tasks_per_workspace_anti_loop})")
                
            except Exception as e:
                logger.warning(f"Dynamic anti-loop manager error, using base limit: {e}")
                effective_limit = self.max_tasks_per_workspace_anti_loop
        
        # Final validation check
        if current_anti_loop_count >= effective_limit:
            # Check if this is a critical corrective task that should bypass the limit
            if await self._is_critical_corrective_task(task_dict):
                logger.info(f"🚨 CRITICAL BYPASS: Task {task_id} bypassing anti-loop limit ({current_anti_loop_count}/{effective_limit}) - critical corrective task")
                return True  # Allow execution despite limit
            else:
                # Log the skip with improved context
                skip_rate = current_anti_loop_count / effective_limit * 100 if effective_limit > 0 else 0
                logger.warning(f"Anti-loop: W:{workspace_id} task limit ({current_anti_loop_count}/{effective_limit}, {skip_rate:.1f}% skip rate). Task {task_id} skip")
                return False

        # Check delegation depth
        if task_id in self.delegation_chain_tracker:
            depth = len(self.delegation_chain_tracker[task_id])
            if depth > self.max_delegation_depth:
                logger.warning(f"Anti-loop: Task {task_id} exceeded delegation depth ({depth}/{self.max_delegation_depth}). Forcing completion")
                await self._force_complete_task(
                    task_dict, 
                    "Delegation depth exceeded",
                    status_to_set=TaskStatus.FAILED.value
                )
                return False

        return True

    async def get_completed_tasks(self, workspace_id: str) -> List[str]:
        """Returns a list of task IDs that have been completed for a given workspace."""
        completed_tasks = list(self.task_completion_tracker.get(workspace_id, set()))
        # Clear the tracker for these tasks to avoid reprocessing
        if workspace_id in self.task_completion_tracker:
            self.task_completion_tracker[workspace_id].clear()
        return completed_tasks

    async def _count_active_agents(self, workspace_id: str) -> int:
        """Count active agents in workspace for orchestration context"""
        try:
            from database import list_agents
            agents = await list_agents(workspace_id)
            active_agents = [a for a in agents if a.get("status") in ["active", "available"]]
            return len(active_agents)
        except Exception as e:
            logger.warning(f"⚠️ Could not count active agents: {e}")
            return 1  # Default assumption
    
    async def _is_critical_corrective_task(self, task_dict: Dict[str, Any]) -> bool:
        """
        🤖 AI-DRIVEN: Determine if a task is critical and should bypass anti-loop limits
        Uses semantic analysis to identify goal-driven corrective tasks
        """
        try:
            task_name = task_dict.get("name", "").lower()
            task_description = task_dict.get("description", "").lower()
            context_data = task_dict.get("context_data", {}) or {}
            
            # 1. Check if it's a goal-driven corrective task
            is_goal_driven = context_data.get("is_goal_driven_task", False)
            task_type = context_data.get("task_type", "").lower()
            
            if is_goal_driven and "corrective" in task_type:
                logger.info(f"Task {task_dict.get('id')} identified as goal-driven corrective task")
                return True
            
            # 2. Check for critical keywords in task name/description
            critical_indicators = [
                "critical", "urgent", "emergency", "fix", "repair", "restore",
                "goal completion", "deliverable creation", "deliverable", "quality assurance",
                "workspace recovery", "error correction", "system repair", "create final",
                "generate deliverable", "package", "final output"
            ]
            
            combined_text = f"{task_name} {task_description}"
            for indicator in critical_indicators:
                if indicator in combined_text:
                    logger.info(f"Task {task_dict.get('id')} identified as critical by keyword: '{indicator}'")
                    return True
            
            # 3. Check task priority
            priority = task_dict.get("priority", "medium").lower()
            if priority == "high":
                # High priority tasks created in the last hour are considered critical
                created_at = task_dict.get("created_at")
                if created_at:
                    try:
                        from datetime import datetime, timedelta
                        created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        if datetime.now().replace(tzinfo=created_time.tzinfo) - created_time < timedelta(hours=1):
                            logger.info(f"Task {task_dict.get('id')} identified as critical - recent high priority task")
                            return True
                    except Exception as e:
                        logger.warning(f"Failed to parse created_at for task {task_dict.get('id')}: {e}")
            
            # 4. Check if workspace has completed goals but no deliverables (critical gap)
            workspace_id = task_dict.get("workspace_id")
            if workspace_id and "deliverable" in combined_text:
                try:
                    # Check if workspace has completed goals
                    goals_response = supabase.table('workspace_goals').select('*').eq('workspace_id', workspace_id).execute()
                    goals = goals_response.data or []
                    
                    completed_goals = [g for g in goals if g.get('current_value', 0) >= g.get('target_value', 1)]
                    if completed_goals:
                        # Check if there are any deliverables
                        deliverables_response = supabase.table('asset_artifacts').select('id').eq('workspace_id', workspace_id).execute()
                        deliverables = deliverables_response.data or []
                        
                        if not deliverables:
                            logger.info(f"Task {task_dict.get('id')} identified as critical - completed goals but no deliverables")
                            return True
                            
                except Exception as e:
                    logger.warning(f"Failed to check goal/deliverable status for task {task_dict.get('id')}: {e}")
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking if task {task_dict.get('id')} is critical: {e}")
            return False  # Fail safe - don't bypass if we can't determine

    async def _force_complete_task(self, task_dict: Dict[str, Any], reason: str, status_to_set: str = TaskStatus.COMPLETED.value):
        """Forza il completamento di un task con uno specifico reason"""
        task_id = task_dict.get("id")
        workspace_id = task_dict.get("workspace_id")

        if not task_id:
            logger.error(f"Cannot force complete task: ID missing. Reason: {reason}")
            return

        # Check for agent inactivity reason
        if "inactive" in reason.lower() or "no active team members" in reason.lower():
            try:
                # Use unified memory engine instead of old memory_system
                await unified_memory_engine.store_context(
                    workspace_id=workspace_id,
                    context_type="constraint",
                    content={
                        "message": "Operational Block: Task assignment is blocked because all agents are inactive. Pausing corrective actions for 10 minutes.",
                        "constraint_type": "agent_inactive",
                        "impact": "task_assignment_blocked"
                    },
                    importance_score=1.0,
                    metadata={
                        "tags": ["agent_status", "operational_block"],
                        "expires_at": (datetime.now() + timedelta(minutes=10)).isoformat()
                    }
                )
                logger.warning(f"Stored operational constraint for workspace {workspace_id} due to inactive agents.")
            except Exception as e:
                logger.error(f"Failed to store operational constraint: {e}")

        completion_result = {
            "output": f"Task forcibly finalized: {reason}",
            "status_detail": f"forced_{status_to_set.lower().replace('.', '_')}",
            "force_completed": True,
            "completion_reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            await update_task_status(task_id, status_to_set, completion_result)
            # Send WebSocket notification
            await notify_task_status_change(task_id, status_to_set)
            logger.info(f"Forcibly finalized task {task_id} as {status_to_set}: {reason}")
            
            # Decrementa il counter anti-loop per permettere l'esecuzione di altre task
            if workspace_id:
                current_count = self.workspace_anti_loop_task_counts.get(workspace_id, 0)
                if current_count > 0:
                    self.workspace_anti_loop_task_counts[workspace_id] = current_count - 1
                    logger.debug(f"Force complete: Decremented anti-loop counter for W:{workspace_id[:8]} to {current_count - 1}")
                
                self.task_completion_tracker[workspace_id].add(task_id)
            self.active_task_ids.discard(task_id)
            self.queued_task_ids.discard(task_id)

            # --- LINKING: Store Agent Performance and Failure/Success Patterns ---
            agent_id = task_dict.get("agent_id")
            if agent_id:
                # Store performance for completed tasks
                if status_to_set == TaskStatus.COMPLETED.value:
                    quality_assessment = completion_result.get("quality_assessment", {})
                    quality_score = quality_assessment.get("score", 0.0) if isinstance(quality_assessment, dict) else 0.0
                    
                    start_time_iso = next((log['timestamp'] for log in reversed(self.execution_log) if log.get('task_id') == task_id and log.get('event') == 'task_execution_started'), None)
                    duration_seconds = (datetime.now() - datetime.fromisoformat(start_time_iso)).total_seconds() if start_time_iso else 0.0

                    await unified_memory_engine.store_agent_performance_metric(
                        agent_id=agent_id,
                        workspace_id=workspace_id,
                        quality_score=quality_score,
                        duration_seconds=duration_seconds
                    )
                
                # Store failure patterns for failed tasks
                elif status_to_set == TaskStatus.FAILED.value:
                    await unified_memory_engine.store_context(
                        workspace_id=workspace_id,
                        context_type="failure_pattern",
                        content={
                            "task_name": task_dict.get("name"),
                            "failure_reason": reason,
                            "agent_role": task_dict.get("assigned_to_role", "unknown"),
                            "severity": "high"
                        },
                        importance_score=0.9 # Failures are important lessons
                    )
                    
                    # 🤖 AUTONOMOUS RECOVERY: Trigger immediate task recovery
                    try:
                        from services.failed_task_resolver import handle_executor_task_failure
                        
                        recovery_result = await handle_executor_task_failure(task_id, reason)
                        
                        if recovery_result.get('recovery_attempted'):
                            if recovery_result.get('success'):
                                logger.info(f"🤖 AUTONOMOUS RECOVERY: Task {task_id} recovery initiated successfully")
                            else:
                                logger.info(f"🤖 AUTONOMOUS RECOVERY: Task {task_id} scheduled for batch recovery")
                        
                    except Exception as recovery_error:
                        logger.error(f"❌ Failed to trigger autonomous recovery for task {task_id}: {recovery_error}")
                        # Don't fail the task completion due to recovery trigger errors
            # --- END LINKING ---
            
            # 🧠 THINKING PROCESS COMPLETION: Complete any incomplete thinking processes for this task
            if workspace_id and THINKING_PROCESS_AVAILABLE and thinking_engine:
                try:
                    await complete_thinking_processes_for_task(workspace_id, task_id, status_to_set, reason)
                except Exception as thinking_error:
                    logger.error(f"Failed to complete thinking processes for task {task_id}: {thinking_error}")
            
            # 🚀 CRITICAL FIX: Trigger deliverable creation check when task is completed
            if status_to_set == TaskStatus.COMPLETED.value and workspace_id:
                await self._check_and_trigger_deliverable_creation(workspace_id, task_id)
                
                # 🧠 WORKSPACE MEMORY: Generate insights from completed task
                try:
                    from workspace_memory import workspace_memory
                    from models import InsightType
                    from uuid import UUID
                    
                    task_name = task_dict.get("name", "Unknown task")
                    task_output = completion_result.get("output", "")
                    task_type = task_dict.get("task_type", "general")
                    agent_role = task_dict.get("assigned_to_role", "specialist")
                    
                    # Generate insight based on task completion
                    insight_content = f"Completed {task_type} task: {task_name}"
                    if task_output and len(str(task_output)) > 50:
                        output_preview = str(task_output)[:150] + "..." if len(str(task_output)) > 150 else str(task_output)
                        insight_content += f" - Output: {output_preview}"
                    
                    # Determine insight type based on task characteristics
                    insight_type = InsightType.SUCCESS_PATTERN
                    confidence = 0.8
                    
                    # Store the insight
                    await workspace_memory.store_insight(
                        workspace_id=UUID(workspace_id),
                        task_id=UUID(task_id) if task_id else None,
                        agent_role=agent_role,
                        insight_type=insight_type,
                        content=insight_content,
                        relevance_tags=[
                            f"task_{task_type}",
                            f"agent_{agent_role}",
                            "task_completed",
                            "execution_success"
                        ],
                        confidence_score=confidence,
                        metadata={
                            "task_name": task_name,
                            "task_type": task_type,
                            "completion_reason": reason,
                            "forced_completion": True
                        }
                    )
                    logger.info(f"✅ Stored workspace insight for completed task {task_id}")
                    
                except Exception as insight_error:
                    logger.error(f"Failed to store workspace insight for task {task_id}: {insight_error}")
                    # Don't fail task completion due to insight storage errors
                
                # EVENT-DRIVEN: Create task completion event
                await self._create_integration_event(
                    workspace_id=workspace_id,
                    event_type='task_completed',
                    source_component='executor',
                    target_component='unified_orchestrator',
                    event_data={
                        'task_id': task_id,
                        'completion_result': completion_result,
                        'status': status_to_set
                    }
                )
                
                # 🛡️ AUTOMATIC QUALITY TRIGGER: Trigger quality validation on task completion
                try:
                    from backend.ai_quality_assurance.unified_quality_engine import unified_quality_engine
                    quality_trigger = unified_quality_engine.get_automatic_quality_trigger()
                    
                    # Trigger immediate quality check for the workspace
                    quality_result = await quality_trigger.trigger_immediate_quality_check(workspace_id)
                    
                    if quality_result.get("status") == "completed":
                        logger.info(f"✅ Automatic quality validation triggered for task {task_id}: {quality_result.get('new_validations', 0)} validations created")
                    else:
                        logger.warning(f"⚠️ Automatic quality validation failed for task {task_id}: {quality_result.get('error', 'Unknown error')}")
                        
                except Exception as quality_error:
                    logger.error(f"Error triggering automatic quality validation for task {task_id}: {quality_error}")
                    # Don't fail the task completion due to quality trigger errors
        except Exception as e:
            logger.error(f"Error force finalizing task {task_id}: {e}")
    
    async def _retrieve_quality_patterns_for_task(self, task_data: Dict[str, Any], workspace_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve learned quality patterns for task type and agent to guide execution"""
        try:
            from uuid import UUID
            from workspace_memory import workspace_memory
            
            # Extract task context
            task_type = task_data.get('task_type', task_data.get('type', 'unknown'))
            agent_id = task_data.get('agent_id', 'unknown')
            
            if task_type == 'unknown':
                logger.debug("No specific task type found - skipping quality pattern retrieval")
                return None
            
            # Get quality patterns from workspace memory
            quality_patterns = await workspace_memory.get_quality_patterns_for_task_type(
                workspace_id=UUID(workspace_id),
                task_type=task_type,
                agent_id=agent_id
            )
            
            # Return only if we have meaningful patterns
            if quality_patterns and quality_patterns.get('quality_statistics', {}).get('total_validations', 0) > 0:
                logger.debug(f"Found quality patterns for {task_type}: {quality_patterns['quality_statistics']['total_validations']} validations")
                return quality_patterns
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving quality patterns: {e}")
            return None
    
    async def _inject_quality_guidance(self, task_id: str, quality_patterns: Dict[str, Any]):
        """Inject quality guidance into task for agent access"""
        try:
            # Update task with quality guidance in the database
            quality_guidance = {
                "best_practices": quality_patterns.get('best_practices', [])[:3],  # Top 3
                "success_patterns": quality_patterns.get('success_patterns', [])[:3],  # Top 3
                "failure_patterns": quality_patterns.get('failure_patterns', [])[:2],  # Top 2 to avoid
                "recommendations": quality_patterns.get('recommendations', []),
                "quality_statistics": quality_patterns.get('quality_statistics', {}),
                "injected_at": datetime.now().isoformat()
            }
            
            # Update task metadata with quality guidance
            from database import update_task_metadata
            
            metadata_update = {
                "quality_guidance": quality_guidance,
                "quality_guidance_source": "workspace_memory_learning"
            }
            
            await update_task_metadata(task_id, metadata_update)
            
            logger.debug(f"✅ Quality guidance injected into task {task_id}")
            
        except Exception as e:
            logger.error(f"Error injecting quality guidance for task {task_id}: {e}")

    async def _execute_task_with_anti_loop_and_tracking(self, manager: AgentManager, task_dict: Dict[str, Any]):
        """
        Esegue un task convertendo prima il dict in oggetto Pydantic Task
        e gestendo tutti gli aspetti di tracking, budget, e post-completion
        """
        task_id = task_dict.get("id", "unknown")
        workspace_id = task_dict.get("workspace_id", "unknown")
        agent_id = task_dict.get("agent_id")
        
        # 🔍 Start task execution monitoring
        if TASK_MONITOR_AVAILABLE:
            trace_task_start(task_id, workspace_id, agent_id)
            trace_stage(task_id, ExecutionStage.TASK_RECEIVED, "Task received for execution")
        
        # 🔄 HOLISTIC LIFECYCLE: Start integrated lifecycle tracking
        if self.lifecycle_manager:
            try:
                await start_holistic_task_lifecycle(
                    task_id=task_id,
                    workspace_id=workspace_id,
                    goal_id=task_dict.get("goal_id"),
                    initial_context={
                        "task_name": task_dict.get("name", "Unknown"),
                        "task_type": task_dict.get("task_type", "hybrid"),
                        "priority": task_dict.get("priority", "medium"),
                        "agent_assignment_started": True
                    }
                )
                logger.info(f"🔄 Started holistic lifecycle tracking for task {task_id}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to start lifecycle tracking: {e}")
        
        # Prima converte il dict in un oggetto Pydantic Task
        try:
            # FIXED: Validate and sanitize priority before Pydantic validation
            task_priority = task_dict.get("priority", "medium")
            valid_priorities = ["low", "medium", "high"]

            if task_priority not in valid_priorities:
                logger.warning(f"Invalid priority '{task_priority}' for task {task_dict.get('id')}. Using 'high' instead.")
                task_priority = "high"

            # Assicura che tutti i campi necessari siano presenti
            task_dict_validated = {
                "id": task_dict["id"],
                "workspace_id": task_dict["workspace_id"],
                "agent_id": task_dict.get("agent_id"),
                "assigned_to_role": task_dict.get("assigned_to_role"),
                "name": task_dict["name"],
                "description": task_dict.get("description", ""),
                "status": task_dict.get("status", TaskStatus.PENDING.value),
                "priority": task_priority,  # FIXED: Use validated priority
                "parent_task_id": task_dict.get("parent_task_id"),
                
                "estimated_effort_hours": task_dict.get("estimated_effort_hours"),
                "deadline": task_dict.get("deadline"),
                "context_data": task_dict.get("context_data"),  # Già dict, non JSON string
                "result": task_dict.get("result"),
                "created_at": datetime.fromisoformat(task_dict["created_at"]) if task_dict.get("created_at") else datetime.now(),
                "updated_at": datetime.fromisoformat(task_dict["updated_at"]) if task_dict.get("updated_at") else datetime.now() 
            }
            task_pydantic_obj = Task.model_validate(task_dict_validated)
        except Exception as p_exc:
            logger.error(f"Failed to validate task_dict into Pydantic Task model for task ID {task_dict.get('id')}: {p_exc}", exc_info=True)
            await self._force_complete_task(
                task_dict, 
                f"Invalid task data structure: {p_exc}",
                status_to_set=TaskStatus.FAILED.value
            )
            return
        
        task_id = str(task_pydantic_obj.id)
        workspace_id = str(task_pydantic_obj.workspace_id)
        agent_id = str(task_pydantic_obj.agent_id) if task_pydantic_obj.agent_id else None
        task_name = task_pydantic_obj.name

        if not agent_id:  # Dovrebbe essere stato assegnato da _assign_agent_to_task_by_role
            error_msg = f"Task {task_id} ('{task_name}') reached execution stage without an assigned agent_id"
            logger.error(error_msg)
            await self._force_complete_task(task_dict, error_msg, status_to_set=TaskStatus.FAILED.value)
            return

        allowed = await controlled_iteration(task_id, workspace_id, task_dict.get("max_iterations"))
        if not allowed:
            await self._force_complete_task(
                task_dict,
                "iteration limit reached",
                status_to_set=TaskStatus.FAILED.value
            )
            return
            
        # Tracking e preparazione
        start_time_tracking = time.time()
        model_for_budget = self.budget_tracker.default_model
        estimated_input_tokens = 0

        self.workspace_anti_loop_task_counts[workspace_id] = self.workspace_anti_loop_task_counts.get(workspace_id, 0) + 1

        try:
            # Log inizio esecuzione
            execution_start_log = {
                "timestamp": datetime.now().isoformat(),
                "event": "task_execution_started",
                "task_id": task_id,
                "agent_id": agent_id,
                "workspace_id": workspace_id,
                "task_name": task_name,
                "assigned_role": task_dict.get("assigned_to_role"),
                "priority": task_dict.get("priority")
            }
            self.execution_log.append(execution_start_log)
            
            # Aggiorna status nel DB
            await update_task_status(
                task_id, 
                TaskStatus.IN_PROGRESS.value,
                result_payload={"status_detail": "Execution started by anti-loop worker"}
            )
            # Send WebSocket notification
            await notify_task_status_change(task_id, TaskStatus.IN_PROGRESS.value)

            # Recupera dati agente dal DB
            agent_data_db = await get_agent(agent_id)
            if not agent_data_db:
                raise ValueError(f"Agent {agent_id} not found for task {task_id}")

            # Determina il modello LLM da usare
            llm_config_db = agent_data_db.get("llm_config")
            if isinstance(llm_config_db, str):
                llm_config = json.loads(llm_config_db)
            elif isinstance(llm_config_db, dict):
                llm_config = llm_config_db
            else:
                llm_config = {}

            config_model = llm_config.get("model")
            if config_model and config_model in self.budget_tracker.token_costs:
                model_for_budget = config_model
            else:
                # Mapping seniority -> model
                seniority_map = {
                    "junior": "gpt-4.1-nano",
                    "senior": "gpt-4.1-mini", 
                    "expert": "gpt-4.1"
                }
                model_for_budget = seniority_map.get(
                    agent_data_db.get("seniority", "senior"), 
                    self.budget_tracker.default_model
                )

            # Retrieve learned patterns from memory
            success_patterns = await unified_memory_engine.get_relevant_context(workspace_id, task_name, context_types=["success_pattern"], max_results=2)
            failure_patterns = await unified_memory_engine.get_relevant_context(workspace_id, task_name, context_types=["failure_pattern"], max_results=2)

            learned_patterns_text = ""
            if success_patterns:
                learned_patterns_text += "## Relevant Success Patterns (apply these):\n"
                for pattern in success_patterns:
                    learned_patterns_text += f"- {pattern.content}\n"
            
            if failure_patterns:
                learned_patterns_text += "\n## Relevant Failure Patterns (avoid these):\n"
                for pattern in failure_patterns:
                    learned_patterns_text += f"- {pattern.content}\n"

            if learned_patterns_text:
                task_pydantic_obj.description = f"""Leverage these insights to improve your performance:
{learned_patterns_text}
---
Original Task:
{task_pydantic_obj.description}"""

            logger.info(f"Executing task {task_id} ('{task_name}') with agent {agent_id} (Role: {agent_data_db.get('role', 'N/A')}) using model {model_for_budget}")
            
            # 🧠 THINKING PROCESS INTEGRATION (Pillar 10: Real-Time Thinking)
            thinking_process_id = None
            if THINKING_PROCESS_AVAILABLE and thinking_engine:
                try:
                    # Start Codex-style thinking process for this task
                    thinking_context = f"Analyzing task: {task_name}\nDescription: {task_pydantic_obj.description or 'No description provided'}\nAgent: {agent_data_db.get('role', 'AI Agent')}\nWorkspace: {workspace_id}"
                    thinking_process_id = await thinking_engine.start_thinking_process(
                        workspace_id=UUID(workspace_id),
                        context=thinking_context,
                        process_type="task_execution"
                    )
                    
                    # Add initial analysis step
                    await thinking_engine.add_thinking_step(
                        process_id=thinking_process_id,
                        step_type="analysis",
                        content=f"✦ Starting task execution: '{task_name}'. I need to analyze the requirements and determine the best approach to complete this task efficiently.",
                        confidence=0.8,
                        metadata={"task_id": task_id, "agent_role": agent_data_db.get('role', 'AI Agent')}
                    )
                    
                    # Add context loading step
                    await thinking_engine.add_thinking_step(
                        process_id=thinking_process_id,
                        step_type="context_loading",
                        content=f"🔍 Loading task context and workspace environment. Task assigned to {agent_data_db.get('role', 'AI Agent')} with priority: {task_pydantic_obj.priority}. Estimated complexity: {model_for_budget}.",
                        confidence=0.9,
                        metadata={"task_context": task_pydantic_obj.description, "model": model_for_budget}
                    )
                    
                    logger.info(f"🧠 Started thinking process {thinking_process_id} for task {task_id}")
                    
                except Exception as thinking_error:
                    logger.warning(f"Failed to start thinking process for task {task_id}: {thinking_error}")
            
            # Stima token input
            task_input_text = f"{task_name} {task_pydantic_obj.description or ''}"
            estimated_input_tokens = max(1, len(task_input_text) // 4)

            # 🔍 Trace agent assignment
            if TASK_MONITOR_AVAILABLE:
                trace_stage(task_id, ExecutionStage.AGENT_ASSIGNED, f"Agent {agent_id} assigned")

            agent = await manager.get_agent(agent_id)
            if not agent:
                if TASK_MONITOR_AVAILABLE:
                    trace_error(task_id, f"Agent {agent_id} not found in manager", ExecutionStage.AGENT_ASSIGNED)
                raise ValueError(f"Agent {agent_id} not found in manager for task {task_id}")

            # 🔍 Trace agent initialization
            if TASK_MONITOR_AVAILABLE:
                trace_stage(task_id, ExecutionStage.AGENT_INITIALIZED, f"Agent {agent.agent_data.name} initialized")
            
            # 🧠 ENHANCED: Add agent assignment thinking step with metadata
            if thinking_process_id and THINKING_PROCESS_AVAILABLE and thinking_engine:
                try:
                    agent_info = {
                        "id": str(agent_id),
                        "name": agent.agent_data.name if hasattr(agent.agent_data, 'name') else "Unknown Agent",
                        "role": agent.agent_data.role,
                        "seniority": agent.agent_data.seniority,
                        "skills": agent.agent_data.skills if hasattr(agent.agent_data, 'skills') else [],
                        "status": "assigned",
                        "workspace_id": workspace_id,
                        "task_id": task_id
                    }
                    
                    action_description = f"assigned to execute task '{task_name}' with priority {task_pydantic_obj.priority}"
                    await thinking_engine.add_agent_thinking_step(
                        process_id=thinking_process_id,
                        agent_info=agent_info,
                        action_description=action_description,
                        confidence=0.9
                    )
                    logger.debug(f"💭 Added agent assignment metadata to thinking process {thinking_process_id}")
                except Exception as agent_meta_error:
                    logger.warning(f"Failed to add agent metadata to thinking process: {agent_meta_error}")

            # 🧠 SDK Session integration (handled in specialist.py now)
            session = None  # Session creation is now handled in SpecialistAgent.execute()

            # ESECUZIONE DEL TASK CON TIMEOUT
            logger.info(f"Before agent.execute for task {task_id}")
            if not agent:
                raise ValueError(f"Agent {agent_id} not found in manager for task {task_id}")
            
            # 🔍 Trace runner start
            if TASK_MONITOR_AVAILABLE:
                trace_stage(task_id, ExecutionStage.RUNNER_START, "Starting agent execution with timeout")
            
            # 🎯 HOLISTIC TASK-TO-DELIVERABLE PIPELINE: Task execution with classification and validation
            try:
                # Get all workspace agents for holistic execution
                workspace_agents_data = []
                try:
                    workspace_agents_raw = await db_list_agents(workspace_id)
                    workspace_agents_data = workspace_agents_raw if workspace_agents_raw else []
                except Exception as e:
                    logger.warning(f"Failed to get workspace agents: {e}")
                
                # 🎯 CRITICAL: Use holistic pipeline instead of direct agent execution
                from services.holistic_task_deliverable_pipeline import execute_task_holistically
                
                logger.info(f"🎯 Executing task {task_id} through holistic task-to-deliverable pipeline")
                
                # 🧠 ENHANCED: Add holistic execution start thinking step
                if thinking_process_id and THINKING_PROCESS_AVAILABLE and thinking_engine:
                    try:
                        execution_info = {
                            "execution_type": "holistic_pipeline",
                            "workspace_agents_count": len(workspace_agents_data),
                            "pipeline_mode": "task_to_deliverable",
                            "rate_limited": API_RATE_LIMITER_AVAILABLE
                        }
                        
                        await thinking_engine.add_thinking_step(
                            process_id=thinking_process_id,
                            step_type="reasoning",
                            content=f"🎯 Starting holistic task-to-deliverable pipeline execution. Available workspace agents: {len(workspace_agents_data)}. This approach will ensure the task produces real business content and creates deliverables if appropriate.",
                            confidence=0.8,
                            metadata={"execution_context": execution_info, "task_id": task_id}
                        )
                        logger.debug(f"💭 Added holistic execution start to thinking process {thinking_process_id}")
                    except Exception as exec_meta_error:
                        logger.warning(f"Failed to add execution metadata to thinking process: {exec_meta_error}")
                
                # 🚦 Apply rate limiting if available
                if API_RATE_LIMITER_AVAILABLE:
                    # Determine provider based on agent seniority
                    agent_seniority = agent.agent_data.seniority.lower() if hasattr(agent.agent_data, 'seniority') else 'senior'
                    provider = "openai_gpt4" if agent_seniority == "expert" else "openai_gpt35"
                    
                    # Determine priority based on task priority
                    task_priority = task_dict.get("priority", "medium").lower()
                    api_priority = "high" if task_priority == "high" or task_dict.get("is_corrective", False) else "normal"
                    
                    logger.info(f"🚦 Applying rate limiting for holistic task {task_id}: provider={provider}, priority={api_priority}")
                    
                    # Execute with rate limiting through holistic pipeline
                    execution_result = await execute_with_rate_limit(
                        lambda: asyncio.wait_for(
                            execute_task_holistically(task_pydantic_obj, workspace_agents_data, session, thinking_process_id), 
                            timeout=300.0
                        ),
                        provider=provider,
                        priority=api_priority
                    )
                else:
                    # Direct holistic execution without rate limiting
                    execution_result = await asyncio.wait_for(
                        execute_task_holistically(task_pydantic_obj, workspace_agents_data, session, thinking_process_id), 
                        timeout=300.0
                    )
                
                logger.info(f"✅ Task {task_id} execution finished. Result: {execution_result}")
                # 🔍 Trace successful completion
                if TASK_MONITOR_AVAILABLE:
                    trace_stage(task_id, ExecutionStage.RUNNER_COMPLETED, "Agent execution completed successfully")
                
                # Ensure we have a valid result object
                if not isinstance(execution_result, TaskExecutionOutput):
                    raise TypeError(f"Agent returned invalid type: {type(execution_result)}")

            except asyncio.TimeoutError:
                logger.error(f"⏰ Task {task_id} exceeded 5 minutes, forcing completion")
                # 🔍 Trace timeout error
                if TASK_MONITOR_AVAILABLE:
                    trace_error(task_id, "Task execution timeout (5 minutes exceeded)", ExecutionStage.RUNNER_EXECUTING)
                execution_result = TaskExecutionOutput(
                    task_id=task_pydantic_obj.id,
                    status=TaskStatus.FAILED,
                    error_message="Task execution timeout (5 minutes exceeded)",
                    summary="Task was terminated due to timeout. Agent may be stuck in infinite loop."
                )
                # Reset agent status  
                try:
                    await update_agent_status(str(agent_id), AgentStatus.IDLE.value)
                except:
                    pass
            except Exception as e:
                # 🚦 Check if it's a rate limit error that wasn't handled
                error_str = str(e).lower()
                if any(code in error_str for code in ["429", "529", "rate_limit", "overloaded"]):
                    logger.error(f"🚫 Rate limit error for task {task_id}: {e}")
                    if TASK_MONITOR_AVAILABLE:
                        trace_error(task_id, "API rate limit exceeded", ExecutionStage.RUNNER_EXECUTING)
                    execution_result = TaskExecutionOutput(
                        task_id=task_pydantic_obj.id,
                        status=TaskStatus.FAILED,
                        error_message=f"API rate limit exceeded: {str(e)[:100]}",
                        summary="Task failed due to API rate limiting. Will be retried later."
                    )
                    # Don't mark as permanently failed - it can be retried
                    await update_task_status(task_id, TaskStatus.PENDING.value)
                else:
                    raise  # Re-raise non-rate-limit errors
            
            return execution_result
        except Exception as e:
            # 🧠 RECOVERY ANALYSIS: Intelligent failure recovery decision
            error_message = str(e)
            error_type = type(e).__name__
            
            logger.error(f"Unhandled error in coordination layer for task {task_dict.get('id')}: {e}", exc_info=True)
            
            # 🔍 Trace unhandled error
            if TASK_MONITOR_AVAILABLE:
                trace_error(task_id, f"Unhandled coordination layer error: {str(e)[:100]}")
                trace_task_complete(task_id, success=False)
            
            # 🧠 RECOVERY ANALYSIS: Determine if recovery should be attempted
            should_recover = False
            recovery_analysis = None
            
            if RECOVERY_ANALYSIS_AVAILABLE and should_attempt_recovery:
                try:
                    logger.info(f"🧠 Analyzing recovery options for failed task {task_id}")
                    
                    should_recover, recovery_analysis = await should_attempt_recovery(
                        task_id=task_id,
                        workspace_id=workspace_id,
                        error_message=error_message,
                        error_type=error_type,
                        agent_id=agent_id,
                        task_name=task_name,
                        task_description=task_dict.get('description', ''),
                        execution_stage='coordination_layer',
                        metadata={
                            'execution_time_ms': (time.time() - start_time_tracking) * 1000,
                            'workspace_health_score': getattr(self, '_last_workspace_health_score', 100.0),
                            'system_load': getattr(self, '_current_system_load', 0.5)
                        }
                    )
                    
                    if recovery_analysis:
                        logger.info(f"🎯 Recovery analysis complete for task {task_id}: "
                                   f"{recovery_analysis.recovery_strategy.value} "
                                   f"(confidence: {recovery_analysis.confidence_score:.2f})")
                    
                except Exception as recovery_error:
                    logger.warning(f"Recovery analysis failed for task {task_id}: {recovery_error}")
                    should_recover = False
            
            # Apply recovery decision or fail the task
            if should_recover and recovery_analysis:
                # RECOVERY: Reset task for retry based on analysis
                if recovery_analysis.recovery_strategy.value in ['immediate_retry', 'exponential_backoff', 'linear_backoff']:
                    # Update task with recovery information
                    recovery_metadata = {
                        'recovery_attempt': True,
                        'recovery_strategy': recovery_analysis.recovery_strategy.value,
                        'recovery_confidence': recovery_analysis.confidence_score,
                        'recovery_delay_seconds': recovery_analysis.recommended_delay_seconds,
                        'original_error': error_message,
                        'recovery_reasoning': recovery_analysis.analysis_reasoning
                    }
                    
                    # Schedule retry with appropriate delay
                    if recovery_analysis.recommended_delay_seconds > 0:
                        # For delayed recovery, mark as pending with delay metadata
                        await update_task_status(
                            task_id, 
                            TaskStatus.PENDING.value, 
                            recovery_metadata
                        )
                        logger.info(f"🔄 Task {task_id} scheduled for recovery retry in "
                                   f"{recovery_analysis.recommended_delay_seconds:.1f}s")
                    else:
                        # For immediate retry, mark as pending
                        await update_task_status(task_id, TaskStatus.PENDING.value, recovery_metadata)
                        logger.info(f"🔄 Task {task_id} scheduled for immediate recovery retry")
                    
                    return None
                    
                elif recovery_analysis.recovery_strategy.value in ['escalate_to_human', 'escalate_to_different_agent']:
                    # ESCALATION: Mark for human intervention or agent reassignment
                    escalation_metadata = {
                        'escalation_required': True,
                        'escalation_type': recovery_analysis.recovery_strategy.value,
                        'escalation_reason': recovery_analysis.analysis_reasoning,
                        'original_error': error_message,
                        'requires_different_agent': recovery_analysis.requires_different_agent,
                        'requires_enhanced_context': recovery_analysis.requires_enhanced_context
                    }
                    
                    await update_task_status(
                        task_id,
                        TaskStatus.NEEDS_REVIEW.value if 'human' in recovery_analysis.recovery_strategy.value else TaskStatus.PENDING.value,
                        escalation_metadata
                    )
                    
                    logger.warning(f"🚨 Task {task_id} escalated: {recovery_analysis.recovery_strategy.value}")
                    return None
            
            # FALLBACK: Traditional failure handling if no recovery or recovery not recommended
            await self._force_complete_task(
                task_dict,
                f"Coordination layer error: {str(e)[:200]}" + 
                (f" | Recovery not viable (confidence: {recovery_analysis.confidence_score:.2f})" if recovery_analysis else ""),
                status_to_set=TaskStatus.FAILED.value
            )
            return None
        
        # Return the execution result
        return execution_result

    async def check_project_completion_after_task(self, completed_task_id: str, workspace_id: str):
        """Verifica se il progetto è completato dopo un task importante"""
        try:
            # Verifica se il task è un task di completamento
            tasks = await self._cached_list_tasks(workspace_id)
            completed_task = next((t for t in tasks if t.get("id") == completed_task_id), None)
            
            if not completed_task:
                return
                
            context_data = completed_task.get("context_data", {}) or {}
            is_final_task = context_data.get("is_final_task", False)
            project_phase = context_data.get("project_phase", "")
            
            # Se è un task di fase FINALIZATION completato, verifica completamento progetto
            if (is_final_task or project_phase == "FINALIZATION") and completed_task.get("status") == "completed":
                # Usa l'EnhancedTaskExecutor per verificare completamento
                from task_analyzer import get_enhanced_task_executor
                task_executor = get_enhanced_task_executor()
                
                is_completed = await task_executor.check_project_completion_criteria(workspace_id)
                
                if is_completed:
                    if workspace_id in self.completed_workspaces:
                        logger.debug(f"Workspace {workspace_id} already processed as completed")
                        return

                    # Aggiorna stato workspace
                    workspace = await get_workspace(workspace_id)
                    if workspace and workspace.get("status") != "completed":
                        await update_workspace_status(workspace_id, "completed")
                        logger.info(f"Project {workspace_id} automatically marked as COMPLETED")

                    # Mark as processed regardless of DB status to avoid redundant checks
                    self.completed_workspaces.add(workspace_id)
                    self.execution_log.append({
                        "timestamp": datetime.now().isoformat(),
                        "event": "project_completed",
                        "workspace_id": workspace_id,
                        "trigger_task_id": completed_task_id
                    })
        except Exception as e:
            logger.error(f"Error checking project completion after task {completed_task_id}: {e}", exc_info=True)

    async def _is_project_manager_task(self, task: Task, result: Dict[str, Any]) -> bool:
        """Determina se un task è stato completato da un Project Manager"""
        
        try:
            # Metodo 1: Controlla l'agent_id se disponibile
            if task.agent_id:
                agent_data = await get_agent(str(task.agent_id))
                if agent_data:
                    role = agent_data.get('role', '').lower()
                    pm_keywords = ['manager', 'coordinator', 'director', 'lead', 'pm', 'project']
                    if any(kw in role for kw in pm_keywords):
                        logger.info(f"Task {task.id} identified as PM task by agent role: {role}")
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
        
        for indicator in pm_indicators:
            if indicator in task_name or indicator in task_desc:
                logger.info(f"Task {task.id} identified as PM task by content indicator: {indicator}")
                return True
        
        return False

    async def execution_loop(self):
        """🚀 INTELLIGENT EXECUTION LOOP with adaptive performance optimization"""
        
        logger.info("🧠 Intelligent execution loop started with adaptive performance optimization")
        logger.info(f"📊 Initial load level: {self.executor_metrics['load_level']}, sleep interval: {self.adaptive_intervals[self.executor_metrics['load_level']]}s")
        
        while self.running:
            try:
                loop_start = time.time()  # Track loop start time for performance metrics
                
                await self.pause_event.wait()
                if not self.running:
                    break
                    
                # Circuit breaker check (esistente)
                if await self.check_global_circuit_breaker():
                    logger.critical("⚠️ CIRCUIT BREAKER ACTIVATED - System paused. Manual restart required.")
                    self.execution_log.append({
                        "timestamp": datetime.now().isoformat(),
                        "event": "circuit_breaker_activated",
                        "reason": "Abnormal behavior detected"
                    })
                    await asyncio.sleep(60)
                    continue

                # 🔍 STEP 1: ASSESS SYSTEM LOAD (holistic approach)
                await self._assess_adaptive_system_load()
                
                # Log the main loop iteration for visibility
                if self.executor_metrics['load_level'] != "idle":
                    logger.info("🔄 MAIN LOOP: Processing pending tasks, asset coordination, checking workspaces")
                
                # 🎯 STEP 2: DETERMINE OPERATIONS BASED ON LOAD
                operations = self._determine_operations_for_current_load()
                
                # ⚡ STEP 3: EXECUTE SELECTED OPERATIONS EFFICIENTLY
                await self._execute_adaptive_operations(operations)
                
                # === NUOVA: Asset coordination ===
                try:
                    active_workspaces = await get_active_workspaces()
                    for ws_id in active_workspaces:
                        await self.coordinate_asset_oriented_workflow(ws_id)
                except Exception as e:
                    logger.error(f"Error in asset coordination: {e}")
                
                # Controlla nuovi workspace (esistente)
                if self.auto_generation_enabled:
                    await self.check_for_new_workspaces()

                # Controllo runaway periodico (esistente)
                if (self.last_runaway_check is None or
                    (datetime.now() - self.last_runaway_check).total_seconds() > self.runaway_check_interval):
                    await self.periodic_runaway_check()
                    self.last_runaway_check = datetime.now()
                
                # 📊 ENHANCED: Telemetry and proactive monitoring
                if TELEMETRY_MONITOR_AVAILABLE and system_telemetry_monitor:
                    try:
                        # Collect telemetry every 5 minutes
                        if (not hasattr(self, 'last_telemetry_check') or 
                            (datetime.now() - self.last_telemetry_check).total_seconds() > 300):
                            
                            await system_telemetry_monitor.collect_comprehensive_metrics()
                            self.last_telemetry_check = datetime.now()
                            logger.debug("📊 System telemetry collected successfully")
                            
                    except Exception as telemetry_error:
                        logger.warning(f"Telemetry collection error: {telemetry_error}")

                # 🚦 Check and adjust rate limiting status
                if API_RATE_LIMITER_AVAILABLE:
                    try:
                        # Check rate limit stats every minute
                        if (not hasattr(self, 'last_rate_limit_check') or 
                            (datetime.now() - self.last_rate_limit_check).total_seconds() > 60):
                            
                            stats = api_rate_limiter.get_stats()
                            
                            # Log warnings if approaching limits
                            for provider, provider_stats in stats.items():
                                if provider_stats['in_cooldown']:
                                    logger.warning(f"🚦 {provider} is in rate limit cooldown")
                                elif provider_stats['calls_last_minute'] > 0:
                                    config = api_rate_limiter.configs.get(provider)
                                    if config and provider_stats['calls_last_minute'] > config.requests_per_minute * 0.8:
                                        logger.warning(f"🚦 {provider} approaching rate limit: "
                                                     f"{provider_stats['calls_last_minute']}/{config.requests_per_minute} calls/min")
                            
                            self.last_rate_limit_check = datetime.now()
                            
                    except Exception as rate_limit_error:
                        logger.warning(f"Rate limit status check error: {rate_limit_error}")
                
                # Cleanup periodico (esistente)
                if datetime.now() - self.last_cleanup > timedelta(minutes=5):
                    await self._cleanup_tracking_data()

                # 📊 STEP 4: UPDATE PERFORMANCE METRICS
                loop_time = time.time() - loop_start  # Calculate actual loop duration
                await self._update_executor_metrics(loop_time)
                
                # 🛌 STEP 5: ADAPTIVE SLEEP BASED ON LOAD
                sleep_interval = self.adaptive_intervals[self.executor_metrics['load_level']]
                logger.debug(f"🛌 Adaptive sleep: {sleep_interval}s (load: {self.executor_metrics['load_level']})")
                await asyncio.sleep(sleep_interval)

            except asyncio.CancelledError:
                logger.info("Main execution loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in main execution_loop: {e}", exc_info=True)
                await asyncio.sleep(30)
        
        logger.info("Main execution loop finished")

    async def process_pending_tasks_anti_loop(self):
        """Processa task pendenti da tutti i workspace attivi"""
        if self.paused:
            return
            
        try:
            # Ottieni workspace con task pendenti
            workspaces_with_pending = await get_workspaces_with_pending_tasks()
            
            if workspaces_with_pending:
                logger.info(f"🔍 POLLING: Found {len(workspaces_with_pending)} workspaces with pending tasks: {workspaces_with_pending}")
            else:
                logger.info(f"🔍 POLLING: No workspaces with pending tasks found")
            
            # Limita il numero di workspace processati per ciclo
            for workspace_id in workspaces_with_pending[:self.max_concurrent_tasks * 2]:
                logger.info(f"🔍 POLLING: Processing workspace {workspace_id}")
                
                if self.task_queue.full():
                    logger.warning(f"Anti-loop Task Queue is full ({self.task_queue.qsize()}/{self.max_queue_size}). Skipping further workspace processing in this cycle")
                    break
                
                # Load workspace-specific settings before processing
                try:
                    workspace_settings = await self.get_workspace_settings(workspace_id)
                    # Apply workspace-specific settings for this cycle
                    self._current_max_concurrent_tasks = workspace_settings['max_concurrent_tasks']
                    self._current_execution_timeout = workspace_settings['task_timeout']
                    logger.debug(f"Loaded settings for workspace {workspace_id}: "
                               f"concurrent_tasks={workspace_settings['max_concurrent_tasks']}, "
                               f"timeout={workspace_settings['task_timeout']}s")
                except Exception as e:
                    logger.warning(f"Failed to load workspace settings for {workspace_id}, using defaults: {e}")
                    # Reset to defaults on error
                    self._current_max_concurrent_tasks = self.default_max_concurrent_tasks
                    self._current_execution_timeout = self.default_execution_timeout
                
                # Pre-warm caches to avoid repeated DB hits in quick succession
                tasks_count = len(await self._cached_list_tasks(workspace_id))
                agents_count = len(await self._cached_list_agents(workspace_id))
                logger.info(f"🔍 POLLING: Workspace {workspace_id} has {tasks_count} tasks, {agents_count} agents")
                
                logger.info(f"🔍 POLLING: Calling process_workspace_tasks_anti_loop_with_health_check_enhanced for {workspace_id}")
                await self.process_workspace_tasks_anti_loop_with_health_check_enhanced(workspace_id)
                logger.info(f"🔍 POLLING: Finished processing workspace {workspace_id}")
                
        except Exception as e:
            logger.error(f"Error in process_pending_tasks_anti_loop: {e}", exc_info=True)

    async def process_workspace_tasks_anti_loop_with_health_check_enhanced(self, workspace_id: str):
        """
        ENHANCED VERSION: Processa task con prioritizzazione intelligente FINALIZATION
        Sostituisce il metodo esistente process_workspace_tasks_anti_loop_with_health_check
        """
        if self.paused:
            return

        try:
            # Check for operational constraints
            try:
                # Use unified memory engine instead of old memory_system
                constraints = await unified_memory_engine.get_relevant_context(
                    workspace_id=workspace_id,
                    query="operational constraints"
                )
                # 🔧 FIX: Handle ContextEntry objects from unified memory engine
                if constraints:
                    has_operational_block = False
                    for context_entry in constraints:
                        # ContextEntry objects have content and metadata attributes
                        content = ""
                        if hasattr(context_entry, 'content'):
                            if isinstance(context_entry.content, dict):
                                content = str(context_entry.content.get("message", ""))
                            elif isinstance(context_entry.content, list):
                                content = str(context_entry.content)
                            else:
                                content = str(context_entry.content)
                        
                        # Ensure content is always a string before calling .lower()
                        content_str = str(content) if content else ""
                        if "operational block" in content_str.lower():
                            has_operational_block = True
                            break
                    
                    if has_operational_block:
                        logger.warning(f"W:{workspace_id} is under an operational block. Skipping task processing.")
                        return
            except Exception as e:
                logger.error(f"Failed to check operational constraints: {e}")

            # 🏥 ENHANCED: Health check with intelligent auto-recovery
            health_status = None  # Initialize to avoid None errors later
            if WORKSPACE_HEALTH_AVAILABLE and workspace_health_manager:
                try:
                    # Use comprehensive health check with auto-recovery
                    health_report = await workspace_health_manager.check_workspace_health_with_recovery(
                        workspace_id, attempt_auto_recovery=True
                    )
                    
                    # Convert health_report to health_status format for compatibility
                    health_status = {
                        'is_healthy': health_report.is_healthy,
                        'task_counts': {'pending': len([t for t in await self._cached_list_tasks(workspace_id) if t.get('status') == 'pending'])},
                        'health_score': health_report.overall_score
                    }
                    
                    if not health_report.is_healthy:
                        critical_issues = [
                            issue.description for issue in health_report.issues 
                            if issue.level.value in ['critical', 'emergency'] and not issue.auto_recoverable
                        ]
                        
                        if critical_issues and workspace_id not in self.workspace_auto_generation_paused:
                            logger.warning(f"W:{workspace_id} critical unrecoverable issues: {critical_issues}")
                            await self._pause_auto_generation_for_workspace(
                                workspace_id, 
                                reason=f"Unrecoverable issues after auto-recovery attempt: {'; '.join(critical_issues[:2])}"
                            )
                        elif health_report.can_auto_recover:
                            logger.info(f"W:{workspace_id} has recoverable issues - auto-recovery attempted")
                        else:
                            logger.info(f"W:{workspace_id} health score: {health_report.overall_score:.1f}% - monitoring")
                    
                except Exception as health_err:
                    logger.error(f"Error in enhanced health check for {workspace_id}: {health_err}")
                    # Fall back to basic health check
                    health_status = await self.check_workspace_health(workspace_id)
                    
                    if not health_status or not health_status.get('is_healthy', True):
                        health_issues = health_status.get('health_issues', []) if health_status else []
                        logger.warning(f"W:{workspace_id} health issues (fallback): {health_issues}")
                        
                        critical_issues = [
                            issue for issue in health_issues 
                            if any(keyword in issue.lower() for keyword in ['excessive pending', 'high task creation', 'delegation loops'])
                        ]
                        
                        if critical_issues and workspace_id not in self.workspace_auto_generation_paused:
                            await self._pause_auto_generation_for_workspace(
                                workspace_id, 
                                reason=f"Critical health (fallback): {'; '.join(critical_issues)}"
                            )
            else:
                # Fallback to original logic if WorkspaceHealthManager not available
                health_status = await self.check_workspace_health(workspace_id)
                
                if not health_status or not health_status.get('is_healthy', True):
                    health_issues = health_status.get('health_issues', []) if health_status else []
                    logger.warning(f"W:{workspace_id} health issues: {health_issues}")
                    
                    critical_issues = [
                        issue for issue in health_issues 
                        if any(keyword in issue.lower() for keyword in ['excessive pending', 'high task creation', 'delegation loops'])
                    ]
                    
                    if critical_issues and workspace_id not in self.workspace_auto_generation_paused:
                        await self._pause_auto_generation_for_workspace(
                            workspace_id, 
                            reason=f"Critical health: {'; '.join(critical_issues)}"
                        )
                    return

            # Auto-generation resume check (mantieni logica esistente)
            if workspace_id in self.workspace_auto_generation_paused:
                if (health_status and health_status.get('is_healthy') and 
                    health_status.get('task_counts', {}).get('pending', self.max_pending_tasks_per_workspace) < 10):
                    await self._resume_auto_generation_for_workspace(workspace_id)
                    logger.info(f"Auto-gen resumed for healthy W:{workspace_id}")
                else:
                    return

            # 🤖 AI-DRIVEN: Dynamic task limit check with intelligent adaptation and bypass
            current_anti_loop_proc_count = self.workspace_anti_loop_task_counts.get(workspace_id, 0)
            
            # Get dynamic limit recommendation
            effective_proc_limit = self.max_tasks_per_workspace_anti_loop
            if DYNAMIC_ANTI_LOOP_AVAILABLE and dynamic_anti_loop_manager:
                try:
                    effective_proc_limit = await dynamic_anti_loop_manager.get_recommended_limit(workspace_id)
                    logger.debug(f"🤖 Dynamic processing limit for W:{workspace_id[:8]}: {effective_proc_limit}")
                except Exception as e:
                    logger.warning(f"Dynamic limit error in processing, using base: {e}")
            
            if current_anti_loop_proc_count >= effective_proc_limit:
                # Check if we have any critical corrective tasks that should bypass the limit
                all_tasks_for_workspace = await self._cached_list_tasks(workspace_id)
                pending_tasks = [
                    t for t in all_tasks_for_workspace
                    if t.get("status") == TaskStatus.PENDING.value and
                       not (t.get("id") and t.get("id") in self.task_completion_tracker.get(workspace_id, set()))
                ]
                
                # Check if any pending task is critical and should bypass
                has_critical_task = False
                for task in pending_tasks:
                    if await self._is_critical_corrective_task(task):
                        has_critical_task = True
                        logger.info(f"🚨 BYPASS ENABLED: W:{workspace_id} has critical corrective task '{task.get('name', 'Unknown')[:50]}' - proceeding despite limit ({current_anti_loop_proc_count}/{effective_proc_limit})")
                        break
                
                if not has_critical_task:
                    logger.warning(f"Anti-loop limit reached for W:{workspace_id} ({current_anti_loop_proc_count}/{effective_proc_limit}) - no critical tasks to bypass")
                    return

            # Ottieni agent manager
            manager = await self.get_agent_manager(workspace_id)
            if not manager:
                logger.error(f"No agent manager for W:{workspace_id}")
                return

            # === ENHANCED: Ottieni TUTTI i task e applica prioritizzazione intelligente ===
            all_tasks_for_workspace = await self._cached_list_tasks(workspace_id)
            
            # Filtra per task PENDING non già completati
            pending_eligible_tasks = [
                t_dict for t_dict in all_tasks_for_workspace
                if t_dict.get("status") == TaskStatus.PENDING.value and
                   not (t_dict.get("id") and t_dict.get("id") in self.task_completion_tracker.get(workspace_id, set()))
            ]

            if not pending_eligible_tasks:
                return

            # === ENHANCED PRIORITIZATION LOGIC ===
            if ENABLE_SMART_PRIORITIZATION:
                # Usa la nuova funzione di prioritizzazione
                pending_eligible_tasks.sort(
                    key=lambda t: (
                        get_task_priority_score_enhanced(t, workspace_id),  # Primary: Enhanced priority score
                        datetime.fromisoformat(t.get("created_at", "2020-01-01").replace("Z", "+00:00"))  # Secondary: FIFO
                    ),
                    reverse=True  # Higher priority first, then older tasks
                )
                
                # Log the top priority task for monitoring
                if pending_eligible_tasks:
                    top_task = pending_eligible_tasks[0]
                    top_priority = get_task_priority_score_enhanced(top_task, workspace_id)
                    top_context_data = top_task.get('context_data') or {}
                    top_phase = top_context_data.get('project_phase', 'N/A') if isinstance(top_context_data, dict) else 'N/A'
                    logger.info(f"🔥 TOP PRIORITY: '{top_task.get('name', 'Unknown')[:50]}' "
                               f"Priority: {top_priority}, Phase: {top_phase}")
            else:
                # Fallback: uso prioritizzazione standard
                pending_eligible_tasks.sort(
                    key=lambda t: (
                        self._get_task_priority_score_standard(t),
                        datetime.fromisoformat(t.get("created_at", "2020-01-01").replace("Z", "+00:00"))
                    ),
                    reverse=True
                )
            
            # Prendi il task con massima priorità
            task_to_queue_dict = pending_eligible_tasks[0]
            task_id_to_queue = task_to_queue_dict.get("id")

            # Validazione finale e controllo duplicati
            if not await self._validate_task_execution(task_to_queue_dict):
                logger.warning(f"Pre-queue validation FAILED for task {task_id_to_queue}")
                return

            if task_id_to_queue in self.queued_task_ids or task_id_to_queue in self.active_task_ids:
                logger.debug(f"Task {task_id_to_queue} already queued or running. Skipping")
                return

            # Check status from DB to avoid queuing task already in progress
            latest = await get_task(task_id_to_queue)
            if latest and latest.get("status") != TaskStatus.PENDING.value:
                logger.debug(f"Task {task_id_to_queue} status changed to {latest.get('status')}. Skip queue")
                return

            # Aggiungi alla queue con log migliorato
            try:
                self.task_queue.put_nowait((manager, task_to_queue_dict))
                self.queued_task_ids.add(task_id_to_queue)
                
                context_data = task_to_queue_dict.get('context_data') or {}
                task_phase = context_data.get('project_phase', 'N/A') if isinstance(context_data, dict) else 'N/A'
                needs_assign = not task_to_queue_dict.get('agent_id') and task_to_queue_dict.get('assigned_to_role')
                priority_score = get_task_priority_score_enhanced(task_to_queue_dict, workspace_id) if ENABLE_SMART_PRIORITIZATION else "standard"
                
                logger.info(f"🚀 QUEUED: '{task_to_queue_dict.get('name', 'Unknown')[:40]}' "
                           f"(ID: {task_id_to_queue[:8]}) Priority: {priority_score}, "
                           f"Phase: {task_phase}, Assign: {needs_assign}, Q: {self.task_queue.qsize()}")
                
            except asyncio.QueueFull:
                logger.warning(f"Task Queue FULL. Could not queue task {task_id_to_queue}")
        
        except Exception as e:
            logger.error(f"Error in enhanced workspace task processing for W:{workspace_id}: {e}", exc_info=True)

    def _is_enhancement_task(self, task_data: Dict) -> bool:
        """Check if this is an enhancement task that shouldn't trigger new deliverables"""
        if not isinstance(task_data, dict):
            return False
            
        context_data = task_data.get("context_data", {}) or {}
        if isinstance(context_data, dict):
            # Check for enhancement markers in context_data
            if (context_data.get("asset_enhancement_task") or
                context_data.get("enhancement_coordination") or
                context_data.get("ai_guided_enhancement")):
                return True
        
        # Check task name for enhancement keywords
        task_name = (task_data.get("name") or "").lower()
        return (
            "enhance:" in task_name or
            "enhancement" in task_name or
            ("quality" in task_name and "enhancement" in task_name)
        )

    def _get_task_priority_score_standard(self, task_data):
        """Funzione standard di prioritizzazione (fallback)"""
        delegation_depth = 0
        context_data = task_data.get("context_data", {}) or {}
        if isinstance(context_data, dict):
            delegation_depth = context_data.get("delegation_depth", 0)

        depth_penalty = min(delegation_depth * 2, 8)
        base_priority = 0

        if not task_data.get("agent_id") and task_data.get("assigned_to_role"):
            base_priority = 10
        
        p = task_data.get("priority", "medium").lower()
        if p == "high": base_priority = 8
        elif p == "medium": base_priority = 5
        elif p == "low": base_priority = 3

        return max(1, base_priority - depth_penalty)

    async def _cleanup_tracking_data(self):
        """Cleanup periodico dei dati di tracking per evitare memory leak"""
        logger.info("Performing cleanup of executor tracking data...")
        self.last_cleanup = datetime.now()

        # Cleanup execution log
        max_log_entries = 500
        if len(self.execution_log) > max_log_entries:
            self.execution_log = self.execution_log[-max_log_entries:]
            logger.debug(f"Cleaned execution_log, kept last {max_log_entries}")

        # Cleanup task completion tracker
        max_completed_per_ws = 100
        for workspace_id in list(self.task_completion_tracker.keys()):
            if len(self.task_completion_tracker[workspace_id]) > max_completed_per_ws * 2:
                logger.warning(f"Task completion tracker for W:{workspace_id} has {len(self.task_completion_tracker[workspace_id])} entries (>{max_completed_per_ws*2}). Resetting")
                self.task_completion_tracker[workspace_id] = set()  # Reset completo
            elif len(self.task_completion_tracker[workspace_id]) > max_completed_per_ws:
                logger.info(f"Task completion tracker for W:{workspace_id} has {len(self.task_completion_tracker[workspace_id])} entries. Consider more granular cleanup if grows further")

        # Cleanup delegation chain tracker
        for task_id in list(self.delegation_chain_tracker.keys()):
            if len(self.delegation_chain_tracker[task_id]) > self.max_delegation_depth * 2:
                del self.delegation_chain_tracker[task_id]
                logger.debug(f"Removed long delegation chain for task {task_id}")

        # Reset workspace anti-loop counts periodicamente (circa ogni ora)
        if not hasattr(self, "_cleanup_cycle_count"):
            self._cleanup_cycle_count = 0
        self._cleanup_cycle_count += 1
        
        if self._cleanup_cycle_count % 12 == 0:  # Ogni ~1 ora
            logger.info("Periodic reset of workspace_anti_loop_task_counts")
            self.workspace_anti_loop_task_counts = defaultdict(int)
        
        logger.info("Tracking data cleanup finished")

    # === CACHED DATABASE ACCESS HELPERS ===
    async def _cached_list_tasks(self, workspace_id: str) -> List[Dict]:
        now = time.time()
        ts, data = self._tasks_query_cache.get(workspace_id, (0, None))
        if data is not None and now - ts < self.min_db_query_interval:
            return data
        # Use debounced query for database call
        data = await self._debounced_query(f"tasks_{workspace_id}", list_tasks, workspace_id)
        self._tasks_query_cache[workspace_id] = (now, data)
        return data

    async def _cached_list_agents(self, workspace_id: str) -> List[Dict]:
        now = time.time()
        ts, data = self._agents_query_cache.get(workspace_id, (0, None))
        if data is not None and now - ts < self.min_db_query_interval:
            return data
        # Use debounced query for database call
        data = await self._debounced_query(f"agents_{workspace_id}", db_list_agents, workspace_id)
        self._agents_query_cache[workspace_id] = (now, data)
        return data

    async def _cached_active_workspaces(self) -> List[str]:
        now = time.time()
        ts, data = self._active_ws_cache
        if data and now - ts < self.min_db_query_interval:
            return data
        data = await get_active_workspaces()
        self._active_ws_cache = (now, data)
        return data

    async def get_agent_manager(self, workspace_id: str) -> Optional[AgentManager]:
        """Ottieni o crea un AgentManager per il workspace specificato"""
        try:
            workspace_uuid = UUID(workspace_id)
        except ValueError:
            logger.error(f"Invalid workspace ID format: {workspace_id}. Cannot get/create manager")
            return None
        
        # Se esiste già, restituiscilo
        if workspace_uuid in self.workspace_managers:
            return self.workspace_managers[workspace_uuid]
        
        # Crea nuovo manager
        logger.info(f"Creating new AgentManager for workspace {workspace_id}")
        try:
            manager = AgentManager(workspace_uuid)
            if await manager.initialize():
                self.workspace_managers[workspace_uuid] = manager
                logger.info(f"Initialized agent manager for workspace {workspace_id}")
                return manager
            else:
                logger.error(f"Failed to initialize agent manager for workspace {workspace_id}")
                return None
        except Exception as e:
            logger.error(f"Exception creating agent manager for W:{workspace_id}: {e}", exc_info=True)
            return None

    async def check_workspace_health(self, workspace_id: str) -> Dict[str, Any]:
        """Controlla lo stato di salute di un workspace"""
        try:
            all_tasks_db = await self._cached_list_tasks(workspace_id)
            agents_db = await self._cached_list_agents(workspace_id)
            
            # Conteggio task per status
            task_counts = Counter(t.get("status") for t in all_tasks_db)
            task_counts['total'] = len(all_tasks_db)

            # Analisi pattern problematici
            pattern_analysis = self._analyze_task_patterns(all_tasks_db, workspace_id)
            
            # Identificazione problemi di salute
            health_issues = []
            
            # 🏥 ENHANCED: Check pending eccessivi with dynamic threshold
            dynamic_task_limit = self.max_pending_tasks_per_workspace  # Default fallback
            
            if WORKSPACE_HEALTH_AVAILABLE and workspace_health_manager:
                try:
                    dynamic_task_limit = await workspace_health_manager.get_dynamic_task_limit(workspace_id)
                except Exception as e:
                    logger.warning(f"Failed to get dynamic task limit for {workspace_id}: {e}")
            
            if task_counts[TaskStatus.PENDING.value] > dynamic_task_limit:
                health_issues.append(f"Excessive pending: {task_counts[TaskStatus.PENDING.value]}/{dynamic_task_limit} (dynamic)")
            
            # 🎯 PILLAR 7: Intelligent task creation velocity monitoring
            creation_velocity = self._calculate_task_creation_velocity(all_tasks_db)
            velocity_context = self._analyze_velocity_context(workspace_id, all_tasks_db, creation_velocity)
            
            # 🧠 Smart thresholds based on context
            if velocity_context['is_legitimate_burst']:
                # Allow legitimate initial task generation (team approval, goal analysis)
                # Ultra-high velocities (1000+ tasks/min) are normal during team initialization
                velocity_threshold = 2000.0  # Very high threshold for legitimate bursts (2000 tasks/min)
                logger.info(f"🎯 Legitimate task burst detected for workspace {workspace_id}: {creation_velocity:.1f}/min (context: {velocity_context['context']})")
            else:
                # Normal operations - stricter threshold
                velocity_threshold = 15.0  # Increased from 10.0 to be less sensitive for normal ops
            
            if creation_velocity > velocity_threshold:
                if velocity_context['is_legitimate_burst']:
                    # Don't log warnings for legitimate bursts, just info
                    logger.info(f"🎯 Legitimate task burst: {creation_velocity:.1f}/min (context: {velocity_context['context']}) - no health issue logged")
                else:
                    health_issues.append(f"High task creation: {creation_velocity:.1f}/min")
            
            # Check pattern ripetuti
            if pattern_analysis['repeated_patterns']:
                health_issues.append(f"Repeated task names: {pattern_analysis['repeated_patterns']}")
            
            # Check delegation loop
            if pattern_analysis['delegation_loops']:
                health_issues.append(f"Delegation loops: {pattern_analysis['delegation_loops']}")
            
            # Check handoff falliti
            if pattern_analysis['failed_handoffs'] > 3:
                health_issues.append(f"High handoff failures: {pattern_analysis['failed_handoffs']}")
            
            # Check same-role recursion
            if pattern_analysis['same_role_recursion']:
                health_issues.append(f"Same-role recursion: {pattern_analysis['same_role_recursion']}")

            # Check task orfani (senza agente attivo) - escludendo task già completati o failed
            # CRITICAL FIX: Include both "available" and "active" agents
            active_agent_ids = {agent['id'] for agent in agents_db if agent.get('status') in ['available', 'active']}
            pending_or_active_tasks = [t for t in all_tasks_db if t.get('status') in ['pending', 'in_progress', 'needs_verification']]
            orphaned_tasks_count = sum(1 for t in pending_or_active_tasks if not t.get('agent_id') or t.get('agent_id') not in active_agent_ids)
            if orphaned_tasks_count > 0:
                health_issues.append(f"Orphaned tasks: {orphaned_tasks_count}")

            # Calcola health score
            health_score = self._calculate_improved_health_score(task_counts, health_issues, creation_velocity, pattern_analysis)
            
            return {
                'workspace_id': workspace_id,
                'task_counts': dict(task_counts),
                'health_issues': health_issues,
                'health_score': round(health_score, 2),
                'is_healthy': not health_issues and health_score > 70,
                'auto_generation_paused': workspace_id in self.workspace_auto_generation_paused,
                'pattern_analysis': pattern_analysis,
                'creation_velocity': round(creation_velocity, 2)
            }
            
        except Exception as e:
            logger.error(f"Error checking W:{workspace_id} health: {e}", exc_info=True)
            return {
                'workspace_id': workspace_id, 
                'error': str(e), 
                'is_healthy': False, 
                'health_score': 0
            }

    def _analyze_task_patterns(self, tasks_db: List[Dict], workspace_id_for_logs: str) -> Dict[str, Any]:
        """Analizza pattern problematici nei task"""
        # Analisi nomi ripetuti
        task_names = [t.get("name", "") for t in tasks_db]
        name_counts = Counter(task_names)
        repeated_patterns = {name: count for name, count in name_counts.items() if count > 3 and name}
        
        # Analisi delegation loops
        delegation_graph = defaultdict(list)
        delegation_loops_details = []
        
        # Ottieni attività recente per analizzare delegation
        recent_activity = self.get_recent_activity(workspace_id=workspace_id_for_logs, limit=100)
        
        for activity in recent_activity:
            if activity.get('event') == 'subtask_delegated':
                details = activity.get('details', {})
                source = details.get('delegated_by_agent_name', '')
                target = details.get('assigned_agent_name', '')
                if source and target:
                    delegation_graph[source].append(target)
        
        # Trova loop bidirezionali
        for source, targets in delegation_graph.items():
            for target in targets:
                if source in delegation_graph.get(target, []):
                    loop_desc = f"{source} <-> {target}"
                    if loop_desc not in delegation_loops_details:
                        delegation_loops_details.append(loop_desc)

        # Conta handoff falliti
        failed_handoffs_count = sum(1 for act in recent_activity 
                                   if act.get('event') == 'handoff_failed' or 
                                   (act.get('event') == 'task_failed' and "handoff" in act.get('task_name', '').lower()))
        
        # Trova same-role recursion
        same_role_recursion_details = []
        for act in recent_activity:
            if act.get('event') == 'subtask_delegated':
                details = act.get('details', {})
                source_role = details.get('source_agent_role', '').lower()
                target_role = details.get('target_agent_role_or_request', '').lower()
                if source_role and target_role and source_role == target_role:
                    desc = f"Role '{source_role}' to same role"
                    if desc not in same_role_recursion_details:
                        same_role_recursion_details.append(desc)
        
        # Trova cluster di descrizioni simili
        description_clusters = self._find_similar_task_descriptions(tasks_db)
        
        return {
            'repeated_patterns': repeated_patterns,
            'delegation_loops': delegation_loops_details,
            'failed_handoffs': failed_handoffs_count,
            'same_role_recursion': same_role_recursion_details,
            'description_clusters': description_clusters
        }

    def _find_similar_task_descriptions(self, tasks_db: List[Dict], threshold=0.8) -> List[Dict]:
        """Trova cluster di task con descrizioni simili"""
        if not difflib:
            return []
        
        clusters = []
        processed_indices = set()
        
        for i, task1_dict in enumerate(tasks_db):
            if i in processed_indices:
                continue
                
            desc1 = task1_dict.get('description', '')[:250].lower()
            if not desc1 or len(desc1) < 20:
                processed_indices.add(i)
                continue
            
            current_cluster = [task1_dict]
            processed_indices.add(i)
            
            for j, task2_dict in enumerate(tasks_db[i+1:], start=i+1):
                if j in processed_indices:
                    continue
                    
                desc2 = task2_dict.get('description', '')[:250].lower()
                if not desc2 or len(desc2) < 20:
                    processed_indices.add(j)
                    continue
                
                similarity = difflib.SequenceMatcher(None, desc1, desc2).ratio()
                if similarity >= threshold:
                    current_cluster.append(task2_dict)
                    processed_indices.add(j)
            
            if len(current_cluster) > 1:
                clusters.append({
                    'count': len(current_cluster),
                    'sample_names': [t.get('name', 'N/A') for t in current_cluster[:3]],
                    'snippet': desc1[:100] + "...",
                    'threshold': threshold
                })
        
        return clusters

    def _calculate_task_creation_velocity(self, tasks_db: List[Dict], window_min=30) -> float:
        """Calcola velocità di creazione task (task/minuto)"""
        if not tasks_db:
            return 0.0
        
        now = datetime.now()
        recent_creations = []
        
        for task_dict in tasks_db:
            created_at_str = task_dict.get('created_at')
            if created_at_str:
                try:
                    # Parse datetime con gestione timezone
                    dt = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    # Rimuovi timezone info per compatibility
                    if dt.tzinfo is not None:
                        dt = dt.replace(tzinfo=None)

                    if now - dt < timedelta(minutes=window_min):
                        recent_creations.append(dt)
                except ValueError:
                    logger.warning(f"Parse error: {created_at_str} for task {task_dict.get('id')}")

        if len(recent_creations) < 2:
            return 0.0
        
        # Calcola velocità
        recent_creations.sort()
        span_sec = (recent_creations[-1] - recent_creations[0]).total_seconds()
        return (len(recent_creations) / (span_sec / 60.0)) if span_sec > 0 else 0.0

    def _calculate_improved_health_score(
        self, 
        task_counts: Dict, 
        health_issues: List[str], 
        creation_velocity: float, 
        pattern_analysis: Dict
    ) -> float:
        """Calcola uno score di salute del workspace (0-100)"""
        score = 100.0
        
        # Penalità per health issues
        score -= len(health_issues) * 15
        
        # Penalità per ratio task pending elevato
        if task_counts.get('total', 0) > 0:
            pending_ratio = task_counts.get(TaskStatus.PENDING.value, 0) / task_counts['total']
            if pending_ratio > 0.75:
                score -= (pending_ratio - 0.75) * 100
            elif pending_ratio > 0.5:
                score -= (pending_ratio - 0.5) * 50
            
            # Bonus per completion rate alto
            completion_ratio = task_counts.get(TaskStatus.COMPLETED.value, 0) / task_counts['total']
            if completion_ratio > 0.7:
                score += completion_ratio * 10
        
        # Penalità per alta velocità di creazione
        if creation_velocity > 10.0:
            score -= min((creation_velocity - 10.0) * 5, 25)
        elif creation_velocity > 5.0:
            score -= min((creation_velocity - 5.0) * 3, 15)
        
        # Penalità per pattern problematici
        if pattern_analysis.get('repeated_patterns'):
            score -= min(len(pattern_analysis['repeated_patterns']) * 3, 10)
        
        if pattern_analysis.get('delegation_loops'):
            score -= min(len(pattern_analysis['delegation_loops']) * 10, 30)
        
        if pattern_analysis.get('description_clusters'):
            score -= min(len(pattern_analysis['description_clusters']) * 2, 10)
        
        if pattern_analysis.get('failed_handoffs', 0) > 2:
            score -= min(pattern_analysis['failed_handoffs'] * 2, 10)
        
        return max(0.0, min(100.0, score))
    
    def _analyze_velocity_context(self, workspace_id: str, all_tasks_db: List[Dict], velocity: float) -> Dict[str, Any]:
        """
        🧠 PILLAR 7: Intelligent velocity context analysis
        Distinguishes between legitimate task bursts and problematic runaway generation
        """
        if not all_tasks_db or velocity <= 10.0:
            return {"is_legitimate_burst": False, "context": "normal_velocity"}
        
        # Analyze task creation pattern in the last 10 minutes
        from datetime import datetime, timedelta
        now = datetime.now()
        recent_cutoff = now - timedelta(minutes=10)
        
        recent_tasks = []
        for task in all_tasks_db:
            try:
                created_at_str = task.get("created_at", "")
                if created_at_str:
                    # Handle both ISO format and timezone-aware formats
                    if created_at_str.endswith('Z'):
                        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    elif '+' in created_at_str or created_at_str.endswith('UTC'):
                        created_at = datetime.fromisoformat(created_at_str.replace('UTC', '').strip())
                    else:
                        created_at = datetime.fromisoformat(created_at_str)
                    
                    if created_at >= recent_cutoff:
                        recent_tasks.append(task)
            except (ValueError, TypeError):
                continue
        
        if not recent_tasks:
            return {"is_legitimate_burst": False, "context": "no_recent_tasks"}
        
        # 🎯 LEGITIMATE BURST INDICATORS
        
        # 1. Initial Goal Analysis Pattern (multiple goals processed simultaneously)
        goal_driven_tasks = [t for t in recent_tasks if t.get("context_data", {}).get("is_goal_driven")]
        different_goals = set(t.get("goal_id") for t in goal_driven_tasks if t.get("goal_id"))
        
        if len(different_goals) >= 3 and len(goal_driven_tasks) >= 10:
            return {
                "is_legitimate_burst": True, 
                "context": f"initial_goal_analysis_{len(different_goals)}_goals_{len(goal_driven_tasks)}_tasks"
            }
        
        # 2. Team Approval Pattern (tasks created immediately after team approval)
        auto_generated = [t for t in recent_tasks if t.get("context_data", {}).get("auto_generated")]
        if len(auto_generated) >= 10 and len(recent_tasks) == len(auto_generated):
            return {
                "is_legitimate_burst": True,
                "context": f"team_approval_burst_{len(auto_generated)}_auto_tasks"
            }
        
        # 3. Strategic Decomposition Pattern (tasks with strategic context)
        strategic_tasks = [t for t in recent_tasks if 
                          t.get("context_data", {}).get("is_strategic_deliverable") or
                          "strategic" in str(t.get("context_data", {})).lower()]
        
        if len(strategic_tasks) >= 8:
            return {
                "is_legitimate_burst": True,
                "context": f"strategic_decomposition_{len(strategic_tasks)}_strategic_tasks"
            }
        
        # 3a. Ultra-High Velocity Team Initialization (1000+ tasks/min is legitimate during startup)
        if velocity > 500:  # Very high velocity threshold
            # Check for patterns that indicate legitimate team initialization
            
            # Pattern: Multiple goals with assigned agents (proper initialization)
            goal_driven_with_agents = [t for t in recent_tasks if 
                                     t.get("goal_id") and t.get("agent_id")]
            
            if len(goal_driven_with_agents) >= 15:  # Lots of goal-driven tasks with agents
                return {
                    "is_legitimate_burst": True,
                    "context": f"ultra_high_velocity_initialization_{len(goal_driven_with_agents)}_assigned_goal_tasks"
                }
            
            # Pattern: Tasks from same workspace in short timeframe (bulk generation)
            workspace_consistency = len(set(t.get("workspace_id") for t in recent_tasks)) == 1
            if workspace_consistency and len(recent_tasks) >= 20:
                return {
                    "is_legitimate_burst": True,
                    "context": f"bulk_workspace_initialization_{len(recent_tasks)}_tasks_single_workspace"
                }
        
        # 4. Check for agent assignment (legitimate tasks should have agents)
        assigned_tasks = [t for t in recent_tasks if t.get("agent_id")]
        assignment_ratio = len(assigned_tasks) / len(recent_tasks) if recent_tasks else 0
        
        if assignment_ratio >= 0.8:  # 80% of tasks have agents assigned
            return {
                "is_legitimate_burst": True,
                "context": f"proper_assignment_{assignment_ratio:.1%}_assigned"
            }
        
        # 🚨 RUNAWAY INDICATORS
        
        # 1. Duplicate task names
        task_names = [t.get("name", "") for t in recent_tasks]
        unique_names = set(task_names)
        if len(unique_names) < len(task_names) * 0.5:  # Less than 50% unique names
            return {
                "is_legitimate_burst": False,
                "context": f"duplicate_names_{len(unique_names)}_unique_of_{len(task_names)}_total"
            }
        
        # 2. Too many orphaned tasks
        orphaned_ratio = (len(recent_tasks) - len(assigned_tasks)) / len(recent_tasks)
        if orphaned_ratio > 0.3:  # More than 30% orphaned
            return {
                "is_legitimate_burst": False,
                "context": f"high_orphaned_{orphaned_ratio:.1%}_orphaned"
            }
        
        # 3. No context data (may indicate template/fallback generation)
        no_context_tasks = [t for t in recent_tasks if not t.get("context_data")]
        if len(no_context_tasks) > len(recent_tasks) * 0.5:
            return {
                "is_legitimate_burst": False,
                "context": f"missing_context_{len(no_context_tasks)}_of_{len(recent_tasks)}_no_context"
            }
        
        # Default: not clearly legitimate
        return {
            "is_legitimate_burst": False,
            "context": f"unclear_pattern_{len(recent_tasks)}_recent_tasks"
        }

    async def periodic_runaway_check(self):
        """Controllo periodico per rilevare workspace in runaway"""
        logger.info("Starting periodic runaway check...")
        
        try:
            active_ws_ids = await get_active_workspaces()
            if not active_ws_ids:
                logger.info("No active workspaces for runaway check")
                return {'status': 'no_active_workspaces'}
            
            actions = []
            warnings = []
            
            for ws_id in active_ws_ids:
                health_status = await self.check_workspace_health(ws_id)
                
                health_score = health_status.get('health_score', 100)
                is_healthy = health_status.get('is_healthy', True)
                issues = health_status.get('health_issues', [])
                pending = health_status.get('task_counts', {}).get(TaskStatus.PENDING.value, 0)
                
                # 🧠 PILLAR 7: Intelligent critical condition detection
                # Only pause for truly problematic patterns, not legitimate bursts
                critical = False
                
                if health_score < 30:
                    critical = True
                elif pending > (self.max_pending_tasks_per_workspace * 2.0):  # Increased tolerance
                    critical = True
                else:
                    # Check for runaway task creation (not legitimate bursts)
                    for issue in issues:
                        if 'high task creation' in issue.lower():
                            try:
                                # Extract velocity from issue like "High task creation: 1113.8/min"
                                velocity_str = issue.split(':')[-1].replace('/min', '').strip()
                                velocity = float(velocity_str)
                                
                                # Only critical if velocity is extreme AND no legitimate context found
                                if velocity > 50.0:  # Much higher threshold
                                    # Get velocity context for this workspace
                                    all_tasks_response = supabase.table("tasks").select("*").eq(
                                        "workspace_id", ws_id
                                    ).order("created_at", desc=True).limit(100).execute()
                                    
                                    velocity_context = self._analyze_velocity_context(
                                        ws_id, all_tasks_response.data or [], velocity
                                    )
                                    
                                    if not velocity_context.get('is_legitimate_burst', False):
                                        logger.warning(f"🚨 Runaway detected for {ws_id}: {velocity}/min, context: {velocity_context['context']}")
                                        critical = True
                                    else:
                                        logger.info(f"🎯 Legitimate burst for {ws_id}: {velocity}/min, context: {velocity_context['context']}")
                                        
                            except (ValueError, IndexError, AttributeError):
                                continue

                if critical and ws_id not in self.workspace_auto_generation_paused:
                    reason = f"Runaway: Score={health_score}, Pending={pending}, Issues:{issues[:2]}"
                    await self._pause_auto_generation_for_workspace(ws_id, reason=reason)
                    actions.append({
                        'workspace_id': ws_id,
                        'action': 'paused_auto_gen',
                        'reason': reason
                    })
                elif not is_healthy and health_score < 60:
                    warnings.append({
                        'workspace_id': ws_id,
                        'health_score': health_score,
                        'issues': issues[:2]
                    })
            
            # Log risultati
            if actions:
                logger.critical(f"RUNAWAY CHECK: {len(actions)} workspaces paused: {actions}")
            if warnings:
                logger.warning(f"RUNAWAY CHECK: {len(warnings)} workspaces warning: {warnings}")
            if not actions and not warnings:
                logger.info(f"Runaway check: All {len(active_ws_ids)} workspaces stable")
            
            return {
                'timestamp': datetime.now().isoformat(),
                'checked': len(active_ws_ids),
                'actions': actions,
                'warnings': warnings,
                'paused_list': list(self.workspace_auto_generation_paused)
            }
            
        except Exception as e:
            logger.error(f"Error in periodic_runaway_check: {e}", exc_info=True)
            return {'error': str(e)}

    async def _pause_auto_generation_for_workspace(self, workspace_id: str, reason: str = "Runaway detected"):
        """Pausa auto-generation per un workspace specifico"""
        if workspace_id in self.workspace_auto_generation_paused:
            logger.info(f"Auto-gen for W:{workspace_id} already paused")
            return
        
        self.workspace_auto_generation_paused.add(workspace_id)
        logger.critical(f"AUTO-GENERATION PAUSED for W:{workspace_id}. Reason: {reason}")
        
        # Aggiorna status workspace nel DB se possibile
        try:
            ws_data = await get_workspace(workspace_id)
            if ws_data and ws_data.get("status") == WorkspaceStatus.ACTIVE.value:
                await update_workspace_status(workspace_id, WorkspaceStatus.AUTO_RECOVERING.value)
                logger.info(f"W:{workspace_id} status updated to 'auto_recovering'")
        except Exception as e:
            logger.error(f"Failed to update W:{workspace_id} status after pause: {e}")
        
        # Log l'evento
        self.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "event": "workspace_auto_generation_paused",
            "workspace_id": workspace_id,
            "reason": reason
        })

    async def _resume_auto_generation_for_workspace(self, workspace_id: str):
        """Riprende auto-generation per un workspace specifico"""
        if workspace_id not in self.workspace_auto_generation_paused:
            logger.info(f"Auto-gen for W:{workspace_id} not paused")
            return
        
        self.workspace_auto_generation_paused.remove(workspace_id)
        logger.info(f"AUTO-GENERATION RESUMED for W:{workspace_id}")
        
        # Aggiorna status workspace nel DB se possibile
        try:
            ws_data = await get_workspace(workspace_id)
            if ws_data and ws_data.get("status") == WorkspaceStatus.AUTO_RECOVERING.value:
                await update_workspace_status(workspace_id, WorkspaceStatus.ACTIVE.value)
                logger.info(f"W:{workspace_id} status restored to 'active'")
        except Exception as e:
            logger.error(f"Failed to update W:{workspace_id} status after resume: {e}")
        
        # Log l'evento
        self.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "event": "workspace_auto_generation_resumed",
            "workspace_id": workspace_id
        })

    async def check_for_new_workspaces(self):
        """Controlla workspace attivi che necessitano task iniziali"""
        # RIMUOVI questo check per permettere task iniziali sempre  
        # if self.paused or not self.auto_generation_enabled:
        #     logger.debug("Skip check_for_new_workspaces: Paused or global auto-gen disabled")
        #     return
        
        if self.paused:
            logger.debug("Skip check_for_new_workspaces: Executor paused")
            return

        try:
            logger.debug("Checking for active workspaces needing initial tasks...")
            active_ws_ids = await self._cached_active_workspaces()

            for ws_id in active_ws_ids:
                if ws_id in self.workspace_auto_generation_paused:
                    logger.info(f"Skip initial task for W:{ws_id}: auto-gen paused for this workspace")
                    continue

                # Se il workspace non ha task, crea task iniziale
                tasks = await self._cached_list_tasks(ws_id)
                if not tasks:
                    ws_data = await get_workspace(ws_id)
                    if ws_data and ws_data.get("status") == WorkspaceStatus.ACTIVE.value:
                        logger.info(f"W:{ws_id} ('{ws_data.get('name')}') active, no tasks. Creating initial task")
                        await self.create_initial_workspace_task(ws_id)
        except Exception as e:
            logger.error(f"Error in check_for_new_workspaces: {e}", exc_info=True)

    async def create_initial_workspace_task(self, workspace_id: str) -> Optional[str]:
        """Crea task iniziale per un workspace"""
        # RIMUOVI questo check per permettere task iniziali sempre
        # if not self.auto_generation_enabled:
        #     logger.info(f"Global auto-gen disabled. No initial task for W:{workspace_id}")
        #     return None
        if workspace_id in self.workspace_auto_generation_paused:
            logger.info(f"Auto-gen paused for W:{workspace_id}. No initial task")
            return None
        
        try:
            workspace = await get_workspace(workspace_id)
            if not workspace:
                logger.error(f"W:{workspace_id} not found for initial task")
                return None

            # Verifica se lo stato è 'created' prima di procedere
            if workspace.get("status") != WorkspaceStatus.CREATED.value:
                logger.info(f"W:{workspace_id} is not in 'created' state (current: {workspace.get('status')}). Initial task likely already created or process started.")
                # Potresti voler controllare se ci sono già task per decidere se procedere
                existing_tasks_check = await self._cached_list_tasks(workspace_id)
                if existing_tasks_check:
                    logger.info(f"W:{workspace_id} already has tasks. Skipping initial task creation.")
                    return None # O l'ID del primo task se vuoi che il flusso continui
            
            agents = await self._cached_list_agents(workspace_id)
            if not agents:
                logger.warning(f"No agents in W:{workspace_id}. No initial task")
                return None
            
            # Verifica se esistono già task
            existing_tasks = await self._cached_list_tasks(workspace_id)
            if existing_tasks:
                logger.info(f"W:{workspace_id} already has {len(existing_tasks)} tasks. No initial task creation needed.")
                return None
            
            # Analizza composizione team e seleziona lead
            team_analysis = self._analyze_team_composition(agents)
            lead_agent = self._select_project_lead(agents, team_analysis)
            
            if not lead_agent:
                logger.error(f"No suitable lead in W:{workspace_id} for initial task")
                return None
            
            logger.info(f"Selected {lead_agent['name']} ({lead_agent['role']}) as lead for W:{workspace_id}")
            
            # Crea descrizione task strutturata
            description = self._create_structured_initial_task_description(workspace, lead_agent, team_analysis)
            task_name = "Project Setup & Strategic Planning Kick-off"
            
            # Crea task iniziale
            created_task = await create_task(
                workspace_id=str(workspace['id']),
                agent_id=str(lead_agent['id']),
                name=task_name,
                description=description,
                status=TaskStatus.PENDING.value,
                priority="high",

                # TRACKING AUTOMATICO
                creation_type="initial_workspace_setup",  # Task iniziale del workspace

                # CONTEXT DATA SPECIFICO
                context_data={
                    "workspace_initialization": True,
                    "selected_lead_agent": lead_agent['name'],
                    "selected_lead_role": lead_agent['role'],
                    "team_composition": {
                        "total_agents": team_analysis['total_agents'],
                        "leadership_candidates": len(team_analysis['leadership_candidates']),
                        "specialists_count": len(team_analysis['specialists']),
                        "available_domains": list(team_analysis['available_domains'])
                    },
                    "workspace_goal": workspace.get('goal', ''),
                    "workspace_budget": workspace.get('budget', {}),
                    "auto_generated": True,
                    "is_project_kickoff": True
                }
            )
            
            if created_task and created_task.get("id"):
                task_id = created_task["id"]
                logger.info(f"Created initial task {task_id} ('{task_name}') for W:{workspace_id}, assigned to {lead_agent['name']}")

                # AGGIORNAMENTO STATO WORKSPACE
                try:
                    if workspace.get("status") == WorkspaceStatus.CREATED.value:
                        await update_workspace_status(workspace_id, WorkspaceStatus.ACTIVE.value)
                        logger.info(f"Workspace {workspace_id} status updated to ACTIVE after initial task creation.")
                except Exception as e_ws_update:
                    logger.error(f"Failed to update workspace {workspace_id} status to active: {e_ws_update}")

                self.execution_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "event": "initial_workspace_task_created",
                    "task_id": task_id,
                    "agent_id": lead_agent["id"],
                    "workspace_id": workspace_id,
                    "task_name": task_name,
                    "assigned_role": lead_agent["role"]
                })
                return task_id
            else:
                logger.error(f"Failed to create initial task in DB for W:{workspace_id}. Response: {created_task}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating initial task for W:{workspace_id}: {e}", exc_info=True)
            # Se fallisce la creazione del task iniziale, il workspace potrebbe rimanere in 'created'
            # o passare a 'error'
            try:
                await update_workspace_status(workspace_id, WorkspaceStatus.ERROR.value)
                logger.info(f"Workspace {workspace_id} status set to ERROR due to failure in initial task creation.")
            except Exception as e_ws_status:
                logger.error(f"Additionally failed to set workspace {workspace_id} to ERROR: {e_ws_status}")
            return None

    def _analyze_team_composition(self, agents_list: List[Dict]) -> Dict[str, Any]:
        """Analizza la composizione del team"""
        composition = {
            'total_agents': len(agents_list),
            'by_seniority': Counter(),
            'by_role_type': Counter(),
            'available_domains': set(),
            'leadership_candidates': [],
            'specialists': []
        }
        
        seniority_levels = ['junior', 'senior', 'expert']
        
        for agent in agents_list:
            # Analisi seniority
            seniority = agent.get('seniority', 'junior').lower()
            if seniority in seniority_levels:
                composition['by_seniority'][seniority] += 1
            
            # Analisi ruolo
            role = agent.get('role', '').lower()
            role_type_assigned = False
            
            # Leadership roles
            if any(keyword in role for keyword in ['manager', 'coordinator', 'lead', 'director', 'project head']):
                composition['by_role_type']['leadership'] += 1
                composition['leadership_candidates'].append(agent)
                role_type_assigned = True
            
            # Specialist roles
            if 'analyst' in role:
                composition['by_role_type']['analyst'] += 1
                composition['specialists'].append(agent)
                role_type_assigned = True
            
            if 'researcher' in role:
                composition['by_role_type']['researcher'] += 1
                composition['specialists'].append(agent)
                role_type_assigned = True
            
            if 'developer' in role or 'engineer' in role:
                composition['by_role_type']['technical'] += 1
                composition['specialists'].append(agent)
                role_type_assigned = True
            
            if 'writer' in role or 'content' in role:
                composition['by_role_type']['content_creation'] += 1
                composition['specialists'].append(agent)
                role_type_assigned = True
            
            if not role_type_assigned and 'specialist' in role:
                composition['by_role_type']['specialist'] += 1
                composition['specialists'].append(agent)
            elif not role_type_assigned:
                composition['by_role_type']['other'] += 1
            
            # Estrai dominio dal ruolo
            domain = self._extract_domain_from_role(role)
            if domain:
                composition['available_domains'].add(domain)
        
        # Ordina candidati leadership per seniority
        composition['available_domains'] = sorted(list(composition['available_domains']))
        composition['leadership_candidates'].sort(
            key=lambda a: seniority_levels.index(a.get('seniority', 'junior').lower()) 
            if a.get('seniority', 'junior').lower() in seniority_levels else -1,
            reverse=True
        )
        
        return composition

    def _select_project_lead(self, agents_list: List[Dict], team_analysis: Dict) -> Optional[Dict]:
        """Seleziona l'agente più adatto come project lead"""
        # Prima scelta: agenti con ruolo di leadership
        if team_analysis['leadership_candidates']:
            return team_analysis['leadership_candidates'][0]
        
        # Seconda scelta: specialist senior/expert
        potential_leads = [
            agent for agent in team_analysis.get('specialists', [])
            if agent.get('seniority') in ['expert', 'senior']
        ]
        if potential_leads:
            potential_leads.sort(
                key=lambda a: ['junior', 'senior', 'expert'].index(a.get('seniority', 'junior').lower()),
                reverse=True
            )
            return potential_leads[0]
        
        # Terza scelta: qualsiasi agente senior/expert
        experienced_agents = [
            agent for agent in agents_list
            if agent.get('seniority') in ['expert', 'senior']
        ]
        if experienced_agents:
            experienced_agents.sort(
                key=lambda a: ['junior', 'senior', 'expert'].index(a.get('seniority', 'junior').lower()),
                reverse=True
            )
            return experienced_agents[0]
        
        # Ultima scelta: primo agente disponibile
        return agents_list[0] if agents_list else None

    def _create_structured_initial_task_description(
        self, 
        workspace_dict: Dict, 
        lead_agent_dict: Dict, 
        team_analysis: Dict
    ) -> str:
        """Crea descrizione strutturata per il task iniziale"""
        workspace_goal = workspace_dict.get('goal', 'No goal provided.')
        workspace_budget = workspace_dict.get('budget') or {}
        
        if workspace_budget:
            budget_str = f"{workspace_budget.get('max_amount', 'N/A')} {workspace_budget.get('currency', '')} (Strategy: {workspace_budget.get('strategy', 'standard')})"
        else:
            budget_str = "Not specified"
        
        description = f"""**PROJECT KICK-OFF: STRATEGIC PLANNING & TASK DEFINITION**

**Workspace Goal:** {workspace_goal}
**Budget Overview:** {budget_str}
**Assigned Project Lead:** You ({lead_agent_dict.get('name', 'N/A')} - {lead_agent_dict.get('role', 'N/A')})

**Core Responsibilities (Initial Task):**
1. **Analyze Workspace Goal**: Break into 3-5 actionable phases/milestones.
2. **Define Key Deliverables**: For each phase, specify measurable deliverables.
3. **Team & Resource Assessment**: Review team composition; map skills to phases; identify gaps.
4. **High-Level Execution Plan**: Outline phase sequence, dependencies, rough timelines.
5. **Define Initial Sub-Tasks**: Create 2-3 specific, actionable sub-tasks for Phase 1.
6. **Communication Protocol**: Briefly outline progress tracking & handoffs.

**Team Composition Overview:**
{self._format_team_composition_for_task_description(team_analysis)}

**Expected Output (Submit as result):**
* Document with: Phase breakdown, resource allocation ideas, 2-3 specific sub-tasks for Phase 1, coordination strategy notes.

**CRITICAL GUIDELINES:**
* Focus on planning & a few well-defined starter tasks.
* Empower team: Delegate effectively post-planning.
* This is planning; subsequent tasks execute the plan."""
        
        return description.strip()

    def _format_team_composition_for_task_description(self, team_analysis: Dict) -> str:
        """Formatta la composizione del team per la descrizione del task"""
        lines = [f"- Total Agents: {team_analysis['total_agents']}"]
        
        # Seniority mix
        seniority_str = ", ".join(f"{count} {level}" for level, count in team_analysis['by_seniority'].items() if count > 0)
        if seniority_str:
            lines.append(f"- Seniority Mix: {seniority_str}")
        
        # Role types
        role_str = ", ".join(f"{count} {role_type.replace('_', ' ').title()}" for role_type, count in team_analysis['by_role_type'].items() if count > 0)
        if role_str:
            lines.append(f"- Role Types: {role_str}")
        
        # Key domains
        if team_analysis['available_domains']:
            lines.append(f"- Key Domains: {', '.join(team_analysis['available_domains'])}")
        
        # Sample specialists
        if team_analysis.get('specialists'):
            specialist_sample = [f"{specialist['name']} ({specialist['role']})" for specialist in team_analysis['specialists'][:3]]
            if specialist_sample:
                lines.append(f"- Sample Specialists: {'; '.join(specialist_sample)}")
        
        return "\n".join(lines)

    def _extract_domain_from_role(self, role_str: str) -> Optional[str]:
        """Estrae il dominio di expertise da un ruolo"""
        role_lower = role_str.lower()
        
        domain_mapping = {
            'finance': ['finance', 'financial', 'accountant', 'investment'],
            'marketing': ['marketing', 'seo', 'social media', 'campaign'],
            'sales': ['sales', 'business development', 'client acquisition'],
            'product': ['product manager', 'ux design', 'ui design'],
            'technology': ['software engineer', 'developer', 'it support', 'data scientist', 'cybersecurity'],
            'hr': ['human resource', 'recruitment', 'talent acquisition'],
            'legal': ['legal counsel', 'lawyer', 'compliance'],
            'research': ['researcher', 'analyst']
        }
        
        for domain, keywords in domain_mapping.items():
            if any(keyword in role_lower for keyword in keywords):
                return domain
        
        return None

    def get_recent_activity(self, workspace_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Ottieni attività recente del sistema"""
        # Filtra per workspace se specificato
        logs = [log for log in self.execution_log if not workspace_id or log.get("workspace_id") == workspace_id]
        # Ordina per timestamp decrescente e limita
        return sorted(logs, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]
    
    async def _pause_all_active_workspaces(self, reason: str):
        """
        🔧 WORKSPACE STATUS FIX: Pause all active workspaces in database
        
        This ensures consistency between executor state and workspace status.
        Called when circuit breaker trips to prevent the system from
        continuing to process tasks from 'active' workspaces.
        """
        try:
            logger.info(f"🔧 Pausing all active workspaces due to: {reason}")
            
            # Get all active workspaces
            active_workspaces = await get_active_workspaces()
            
            if not active_workspaces:
                logger.info("No active workspaces to pause")
                return
            
            # Update each workspace to paused status
            from models import WorkspaceStatus
            
            # Import supabase if not already imported
            from database import supabase
            paused_count = 0
            
            for workspace_id in active_workspaces:
                try:
                    # Update workspace status to paused
                    update_data = {
                        "status": WorkspaceStatus.PAUSED.value,
                        "updated_at": datetime.now().isoformat()
                    }
                    
                    # Try to add status_reason, but don't fail if column doesn't exist
                    try:
                        update_data["status_reason"] = f"Auto-paused by circuit breaker: {reason}"
                    except:
                        pass
                    
                    update_result = supabase.table("workspaces").update(update_data).eq("id", workspace_id).execute()
                    
                    if update_result.data:
                        paused_count += 1
                        logger.info(f"✅ Paused workspace {workspace_id}")
                        
                        # Log the pause event
                        self.execution_log.append({
                            "event": "workspace_auto_paused",
                            "workspace_id": workspace_id,
                            "reason": reason,
                            "timestamp": datetime.now().isoformat()
                        })
                    
                except Exception as e:
                    logger.error(f"Failed to pause workspace {workspace_id}: {e}")
            
            logger.info(f"🔧 Paused {paused_count}/{len(active_workspaces)} workspaces")
            
        except Exception as e:
            logger.error(f"Error pausing workspaces: {e}")
    
    async def _resume_all_paused_workspaces(self):
        """
        🔧 WORKSPACE STATUS FIX: Resume workspaces that were auto-paused
        
        Called when executor resumes to restore workspace states.
        """
        try:
            logger.info("🔧 Resuming auto-paused workspaces")
            
            from models import WorkspaceStatus
            from database import supabase
            
            # Find workspaces that were auto-paused by circuit breaker
            # First try with status_reason, then fallback to all paused
            try:
                result = supabase.table("workspaces").select("id, status_reason").eq(
                    "status", WorkspaceStatus.PAUSED.value
                ).like(
                    "status_reason", "Auto-paused by circuit breaker%"
                ).execute()
                
                # Filter by status_reason if field exists
                auto_paused_workspaces = [
                    ws for ws in result.data 
                    if ws.get("status_reason", "").startswith("Auto-paused by circuit breaker")
                ]
            except:
                # Fallback: if status_reason doesn't exist, resume ALL paused workspaces
                logger.warning("status_reason field not available, resuming all paused workspaces")
                result = supabase.table("workspaces").select("id").eq(
                    "status", WorkspaceStatus.PAUSED.value
                ).execute()
                auto_paused_workspaces = result.data if result.data else []
            
            if not auto_paused_workspaces:
                logger.info("No auto-paused workspaces to resume")
                return
            
            resumed_count = 0
            for workspace in auto_paused_workspaces:
                try:
                    # Update workspace status back to active
                    update_data = {
                        "status": WorkspaceStatus.ACTIVE.value,
                        "updated_at": datetime.now().isoformat()
                    }
                    
                    # Try to add status_reason, but don't fail if column doesn't exist
                    try:
                        update_data["status_reason"] = "Auto-resumed after circuit breaker recovery"
                    except:
                        pass
                    
                    update_result = supabase.table("workspaces").update(update_data).eq("id", workspace["id"]).execute()
                    
                    if update_result.data:
                        resumed_count += 1
                        logger.info(f"✅ Resumed workspace {workspace['id']}")
                        
                        # Log the resume event
                        self.execution_log.append({
                            "event": "workspace_auto_resumed",
                            "workspace_id": workspace["id"],
                            "timestamp": datetime.now().isoformat()
                        })
                    
                except Exception as e:
                    logger.error(f"Failed to resume workspace {workspace['id']}: {e}")
            
            logger.info(f"🔧 Resumed {resumed_count}/{len(auto_paused_workspaces)} workspaces")
            
        except Exception as e:
            logger.error(f"Error resuming workspaces: {e}")
    
    async def check_global_circuit_breaker(self) -> bool:
        """Verifica condizioni anomale e attiva circuit breaker se necessario"""
        try:
            # 1. Controllo task creation rate (troppi task/min)
            recent_task_creations = [
                log for log in self.execution_log 
                if log.get("event") in ["task_execution_started", "initial_task_created"]
                and (datetime.now() - datetime.fromisoformat(log.get("timestamp", "2020-01-01"))).total_seconds() < 60
            ]

            if len(recent_task_creations) > 20:  # >20 task al minuto
                logger.critical(f"🚨 CIRCUIT BREAKER: Task creation rate too high ({len(recent_task_creations)}/min)")
                self.paused = True
                self.pause_event.clear()
                self.auto_generation_enabled = False
                
                # 🔧 FIX: Update workspace status to prevent inconsistency
                await self._pause_all_active_workspaces("circuit_breaker_task_rate")
                
                # 🚨 TRIGGER IMMEDIATE GOAL VALIDATION for all affected workspaces
                await self._trigger_goal_validation_for_issues("circuit_breaker_task_rate")
                
                return True

            # 2. Controllo fallimenti consecutivi
            recent_failures = [
                log for log in self.execution_log 
                if log.get("event") in ["task_execution_failed", "task_execution_timeout"]
                and (datetime.now() - datetime.fromisoformat(log.get("timestamp", "2020-01-01"))).total_seconds() < 300
            ]

            if len(recent_failures) > 10:  # >10 fallimenti in 5 min
                logger.critical(f"🚨 CIRCUIT BREAKER: Failure rate too high ({len(recent_failures)}/5min)")
                self.paused = True
                self.pause_event.clear()
                
                # 🔧 FIX: Update workspace status to prevent inconsistency
                await self._pause_all_active_workspaces("circuit_breaker_failure_rate")
                
                return True

            return False

        except Exception as e:
            logger.error(f"Error in circuit breaker check: {e}")
            return False

    def get_detailed_stats(self) -> Dict[str, Any]:
        """Ottieni statistiche dettagliate dell'executor"""
        status = "running" if self.running and not self.paused else "paused" if self.paused else "stopped"
        
        # Statistiche base
        base_stats = {
            "executor_status": status,
            "anti_loop_mode_active": True,
            "tasks_in_queue": self.task_queue.qsize(),
            "active_tasks": self.active_tasks_count,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "task_timeout_seconds": self.execution_timeout,
            "global_auto_generation_enabled": self.auto_generation_enabled,
            "workspace_task_counts": dict(self.workspace_anti_loop_task_counts),
            "total_workspaces_tracked": len(self.task_completion_tracker),
            "total_delegation_chains": len(self.delegation_chain_tracker),
            "total_execution_log_entries": len(self.execution_log),
            # ENHANCED FINALIZATION PRIORITY STATS
            "finalization_priority_boost": FINALIZATION_TASK_PRIORITY_BOOST,
            "smart_prioritization_enabled": ENABLE_SMART_PRIORITIZATION
        }

        # Statistiche sessione
        completed_session = sum(1 for log in self.execution_log 
                               if log.get("event") == "task_execution_completed" and 
                               log.get("status_returned") == TaskStatus.COMPLETED.value)
        failed_session = sum(1 for log in self.execution_log 
                            if log.get("event") == "task_execution_failed" or 
                            (log.get("event") == "task_execution_completed" and 
                             log.get("status_returned") == TaskStatus.FAILED.value))
        timeout_session = sum(1 for log in self.execution_log 
                             if log.get("event") == "task_execution_timeout")

        # Attività per agente
        agent_activity = defaultdict(lambda: {"completed": 0, "failed": 0, "timed_out": 0, "total_cost": 0.0})
        for log in self.execution_log:
            agent_id = log.get("agent_id")
            if agent_id:
                if (log.get("event") == "task_execution_completed" and 
                    log.get("status_returned") == TaskStatus.COMPLETED.value):
                    agent_activity[agent_id]["completed"] += 1
                elif (log.get("event") == "task_execution_failed" or 
                      (log.get("event") == "task_execution_completed" and 
                       log.get("status_returned") == TaskStatus.FAILED.value)):
                    agent_activity[agent_id]["failed"] += 1
                elif log.get("event") == "task_execution_timeout":
                    agent_activity[agent_id]["timed_out"] += 1
        
        # Aggiorna con costi per agente
        for agent_id in agent_activity:
            agent_activity[agent_id]["total_cost"] = self.budget_tracker.get_agent_total_cost(agent_id)

        base_stats["session_task_summary"] = {
            "tasks_completed_successfully": completed_session,
            "tasks_failed": failed_session,
            "tasks_timed_out": timeout_session,
            "agent_activity_summary": dict(agent_activity)
        }

        # Statistiche budget
        base_stats["budget_tracker_summary"] = {
            "tracked_agents_count": len(self.budget_tracker.usage_log)
        }

        # Stato runaway protection
        base_stats["runaway_protection_status"] = {
            "paused_workspaces_for_auto_generation": list(self.workspace_auto_generation_paused),
            "last_runaway_check_timestamp": self.last_runaway_check.isoformat() if self.last_runaway_check else None,
            "runaway_check_interval_seconds": self.runaway_check_interval,
            "max_pending_tasks_per_workspace_limit": self.max_pending_tasks_per_workspace
        }

        # Attività auto-generation
        auto_gen_event_types = {"initial_workspace_task_created", "subtask_delegated", "follow_up_generated"}
        base_stats["auto_generation_activity"] = {
            "related_events_in_log": sum(1 for log in self.execution_log 
                                        if log.get("event") in auto_gen_event_types)
        }

        return base_stats
    
    async def process_task_with_coordination(self, task_dict: Dict[str, Any], manager: AgentManager, thinking_process_id: Optional[str] = None) -> None:
        """
        Metodo unificato per processare task con coordinamento completo tra tutti i moduli.
        Garantisce consistenza nel tracking e anti-loop logic.
        """
        task_id = task_dict.get("id")
        workspace_id = task_dict.get("workspace_id")
        task_name = task_dict.get("name", "Unnamed Task")

        # 1. Track centralmente task processing prima di iniziare
        self.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "event": "coordinated_task_processing_started",
            "task_id": task_id,
            "workspace_id": workspace_id,
            "task_name": task_name
        })

        # 2. Estrai attributi di delegation dal DB o context_data
        delegation_depth = task_dict.get("delegation_depth", 0)  # Nuovo campo DB

        # Fallback al context_data se delegation_depth non è nel record principale
        if delegation_depth == 0 and isinstance(task_dict.get("context_data"), dict):
            delegation_depth = task_dict.get("context_data", {}).get("delegation_depth", 0)

        # Ottieni delegation chain dal context_data
        delegation_chain = []
        if isinstance(task_dict.get("context_data"), dict):
            delegation_chain = task_dict.get("context_data", {}).get("delegation_chain", [])

        # 3. Verifica anti-loop centralmente PRIMA dell'esecuzione
        if delegation_depth > self.max_delegation_depth:
            logger.warning(f"Task {task_id} exceeds max delegation depth ({delegation_depth} > {self.max_delegation_depth})")
            await self._force_complete_task(
                task_dict,
                f"Maximum delegation depth exceeded ({delegation_depth}/{self.max_delegation_depth})",
                status_to_set=TaskStatus.FAILED.value
            )
            return

        # Verifica lunghezza chain (doppio controllo)
        if len(delegation_chain) > self.max_delegation_depth:
            logger.warning(f"Task {task_id} has delegation chain too long ({len(delegation_chain)} > {self.max_delegation_depth})")
            await self._force_complete_task(
                task_dict,
                f"Delegation chain too long ({len(delegation_chain)} steps)",
                status_to_set=TaskStatus.FAILED.value
            )
            return

        # 4. Esecuzione coordinata con timeout unificato
        try:
            logger.info(f"Coordinated execution: Task {task_id} (depth: {delegation_depth}, chain: {len(delegation_chain)})")

            # 🧠 Add reasoning step before execution (Codex-style)
            if thinking_process_id and THINKING_PROCESS_AVAILABLE and thinking_engine:
                await thinking_engine.add_thinking_step(
                    process_id=thinking_process_id,
                    step_type="reasoning",
                    content=f"✦ Beginning task execution with delegation depth {delegation_depth}. I will now coordinate with the assigned agent to complete this task efficiently while monitoring for potential issues.",
                    confidence=0.8,
                    metadata={"delegation_depth": delegation_depth, "chain_length": len(delegation_chain)}
                )

            # 🔧 QUALITY PATTERN INJECTION: Retrieve learned quality patterns for task guidance
            try:
                quality_patterns = await self._retrieve_quality_patterns_for_task(task_dict, workspace_id)
                if quality_patterns:
                    # Inject quality guidance into task data for agent access
                    await self._inject_quality_guidance(task_id, quality_patterns)
                    logger.info(f"✅ Quality patterns injected for task {task_id}: {len(quality_patterns.get('best_practices', []))} best practices")
                else:
                    logger.debug(f"ℹ️ No quality patterns found for task {task_id}")
            except Exception as pattern_error:
                logger.warning(f"⚠️ Failed to retrieve quality patterns for task {task_id}: {pattern_error}")
            
            # Esegui con timeout unificato tramite AgentManager
            logger.info(f"Attempting to execute task {task_id} via AgentManager...")
            result = await asyncio.wait_for(
                manager.execute_task(UUID(task_id)), 
                timeout=self.execution_timeout
            )
            logger.info(f"AgentManager.execute_task for {task_id} returned: {result}")

            # 🎯 HOLISTIC CONTENT TRANSFER: Create deliverable from task result content
            if self.holistic_pipeline and result and result.get('result'):
                try:
                    logger.info(f"🎯 Creating deliverable from task {task_id} result content...")
                    
                    # Extract actual content from result
                    task_result_content = result.get('result', '')
                    
                    # Only create deliverable if we have substantial content
                    if isinstance(task_result_content, str) and len(task_result_content) > 100:
                        deliverable_data = {
                            "task_id": task_id,
                            "goal_id": task_dict.get("goal_id"),
                            "title": f"{task_name} - AI-Generated Deliverable", 
                            "description": task_pydantic_obj.description,
                            "content": task_result_content,  # Use actual task result content
                            "type": "real_business_asset",
                            "status": "completed",
                            "business_value_score": 75.0,
                            "quality_level": "acceptable",
                            "metadata": {
                                "created_via": "holistic_executor_integration",
                                "agent_id": agent_id,
                                "execution_successful": True,
                                "content_length": len(task_result_content)
                            }
                        }
                        
                        # Import create_deliverable function
                        from database import create_deliverable
                        deliverable_response = await create_deliverable(workspace_id, deliverable_data)
                        
                        if deliverable_response:
                            logger.info(f"✅ Deliverable created with {len(task_result_content)} chars content: {deliverable_response.get('id')}")
                            result['deliverable_created'] = deliverable_response.get('id')
                        else:
                            logger.warning(f"⚠️ Failed to create deliverable for task {task_id}")
                    else:
                        logger.info(f"ℹ️ Task {task_id} result content too short for deliverable ({len(str(task_result_content))} chars)")
                        
                except Exception as pipeline_error:
                    logger.error(f"❌ Deliverable creation failed for task {task_id}: {pipeline_error}")
                    # Continue execution - deliverable error should not fail the task

            # 5. Log risultato intermedio
            self.execution_log.append({
                "timestamp": datetime.now().isoformat(),
                "event": "coordinated_task_executed",
                "task_id": task_id,
                "workspace_id": workspace_id,
                "delegation_depth": delegation_depth,
                "execution_successful": True,
                "holistic_pipeline_processed": self.holistic_pipeline is not None
            })

            # 🧠 Add evaluation step after execution (Codex-style)
            if thinking_process_id and THINKING_PROCESS_AVAILABLE and thinking_engine:
                success_indicator = "✅" if result and result.get("success", True) else "❌"
                await thinking_engine.add_thinking_step(
                    process_id=thinking_process_id,
                    step_type="evaluation",
                    content=f"{success_indicator} Task execution completed. Result received from agent manager. Now proceeding with post-processing and quality validation to ensure deliverable standards are met.",
                    confidence=0.9,
                    metadata={"execution_result": bool(result), "has_result_data": bool(result and result.get("data"))}
                )

            # 6. Post-processing coordinato con EnhancedTaskExecutor
            # Questo garantisce che post-processing sia soggetto alle stesse regole anti-loop
            try:
                # Crea oggetto Task per EnhancedTaskExecutor
                task_obj = Task.model_validate(task_dict)

                # Ottieni enhanced executor e processa
                from task_analyzer import get_enhanced_task_executor
                enhanced_executor = get_enhanced_task_executor()

                # Passa result e coordination context
                await enhanced_executor.handle_task_completion(
                    task_obj, 
                    result, 
                    workspace_id
                )

                logger.info(f"Coordinated task processing completed successfully for {task_id}")

                # 🧠 ENHANCED: Add final completion step with performance metadata
                if thinking_process_id and THINKING_PROCESS_AVAILABLE and thinking_engine:
                    try:
                        # Get execution performance data if available
                        execution_duration = time.time() - loop_start if 'loop_start' in locals() else None
                        
                        completion_metadata = {
                            "completion_status": "success", 
                            "post_processing": "completed",
                            "task_id": task_id,
                            "workspace_id": workspace_id,
                            "execution_duration_seconds": execution_duration,
                            "agent_delegation_depth": delegation_depth,
                            "holistic_pipeline_used": self.holistic_pipeline is not None,
                            "result_has_data": bool(result and result.get("data")),
                            "completion_timestamp": datetime.now().isoformat()
                        }
                        
                        await thinking_engine.add_thinking_step(
                            process_id=thinking_process_id,
                            step_type="conclusion",
                            content=f"✅ Task '{task_name}' completed successfully. Post-processing finished, all quality gates passed. The task result has been validated and stored for deliverable generation. Execution duration: {execution_duration:.2f}s",
                            confidence=0.95,
                            metadata=completion_metadata
                        )
                        logger.debug(f"💭 Added enhanced completion metadata to thinking process {thinking_process_id}")
                    except Exception as completion_meta_error:
                        logger.warning(f"Failed to add enhanced completion metadata: {completion_meta_error}")
                        # Fallback to simple completion
                        await thinking_engine.add_thinking_step(
                            process_id=thinking_process_id,
                            step_type="conclusion",
                            content=f"✅ Task '{task_name}' completed successfully. Post-processing finished, all quality gates passed.",
                            confidence=0.95,
                            metadata={"completion_status": "success", "post_processing": "completed"}
                        )
                    
                    # Complete the thinking process
                    await thinking_engine.complete_thinking_process(
                        process_id=thinking_process_id,
                        conclusion=f"Successfully completed task '{task_name}' with full coordination and quality validation.",
                        overall_confidence=0.9
                    )

            except Exception as post_error:
                logger.error(f"Error in post-processing for task {task_id}: {post_error}", exc_info=True)
                
                # 🧠 Add error analysis step (Codex-style)
                if thinking_process_id and THINKING_PROCESS_AVAILABLE and thinking_engine:
                    await thinking_engine.add_thinking_step(
                        process_id=thinking_process_id,
                        step_type="critical_review",
                        content=f"❌ Post-processing error encountered: {str(post_error)[:200]}. The main task execution was successful, but quality validation failed. This needs investigation.",
                        confidence=0.7,
                        metadata={"error_type": "post_processing", "error_message": str(post_error)}
                    )
                # Non fallire il task principale per errori di post-processing
                self.execution_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "event": "coordinated_post_processing_error",
                    "task_id": task_id,
                    "error": str(post_error)
                })

        except asyncio.TimeoutError:
            logger.error(f"Coordinated execution timeout for task {task_id} after {self.execution_timeout}s")
            
            # 🧠 Add timeout analysis (Codex-style)
            if thinking_process_id and THINKING_PROCESS_AVAILABLE and thinking_engine:
                await thinking_engine.add_thinking_step(
                    process_id=thinking_process_id,
                    step_type="critical_review",
                    content=f"❌ Task execution timed out after {self.execution_timeout}s. This indicates either a complex task requiring more time or a potential infinite loop. The task will be marked as timed out.",
                    confidence=0.8,
                    metadata={"timeout_duration": self.execution_timeout, "failure_reason": "timeout"}
                )
                
                await thinking_engine.complete_thinking_process(
                    process_id=thinking_process_id,
                    conclusion=f"Task '{task_name}' failed due to execution timeout after {self.execution_timeout} seconds.",
                    overall_confidence=0.6
                )
            
            await self._force_complete_task(
                task_dict,
                f"Coordinated execution timeout after {self.execution_timeout}s",
                status_to_set=TaskStatus.TIMED_OUT.value
            )

        except Exception as e:
            logger.error(f"Coordinated task processing error for {task_id}: {e}", exc_info=True)
            
            # 🧠 Add error analysis (Codex-style)
            if thinking_process_id and THINKING_PROCESS_AVAILABLE and thinking_engine:
                await thinking_engine.add_thinking_step(
                    process_id=thinking_process_id,
                    step_type="critical_review",
                    content=f"❌ Critical error during task execution: {str(e)[:200]}. This prevented the task from completing successfully. I will analyze the error and mark the task as failed.",
                    confidence=0.7,
                    metadata={"error_type": "execution_failure", "error_message": str(e)}
                )
                
                await thinking_engine.complete_thinking_process(
                    process_id=thinking_process_id,
                    conclusion=f"Task '{task_name}' failed due to execution error: {str(e)[:100]}",
                    overall_confidence=0.5
                )
            
            await self._force_complete_task(
                task_dict,
                f"Coordinated execution error: {str(e)[:200]}",
                status_to_set=TaskStatus.FAILED.value
            )

        finally:
            # 7. Log finale
            self.execution_log.append({
                "timestamp": datetime.now().isoformat(),
                "event": "coordinated_task_processing_finished",
                "task_id": task_id,
                "workspace_id": workspace_id
            })

    async def _process_task_into_assets(self, workspace_id: str, completed_task_id: str):
        """
        🚀 NEW AI-DRIVEN: Process completed task using complete AI pipeline
        
        Uses the new real tool integration pipeline to validate, enhance, and convert
        task outputs into real business assets with tool usage and quality validation.
        """
        try:
            logger.info(f"🎯 NEW AI-DRIVEN: Processing completed task {completed_task_id} with complete pipeline")
            
            # Get the completed task
            task_data = await get_task(completed_task_id)
            if not task_data:
                logger.warning(f"Task {completed_task_id} not found for asset processing")
                return
            
            # Check if task has any output (even if minimal - pipeline will enhance it)
            task_output = task_data.get("result") or task_data.get("output")
            if not task_output:
                logger.debug(f"Task {completed_task_id} has no output - skipping asset processing")
                return
            
            try:
                # 🚀 Use new AI-driven pipeline for task validation and enhancement
                from services.real_tool_integration_pipeline import real_tool_integration_pipeline
                
                # Get workspace context for business personalization
                workspace_context = await get_workspace(workspace_id)
                
                # Build business context
                business_context = {
                    "workspace_id": workspace_id,
                    "workspace_name": workspace_context.get("name", "") if workspace_context else "",
                    "industry": workspace_context.get("industry", "") if workspace_context else "",
                    "company_name": workspace_context.get("company_name", "") if workspace_context else ""
                }
                
                # Extract task objective from task data
                task_name = task_data.get("name", "Unknown Task")
                task_description = task_data.get("description", "")
                task_objective = f"Complete {task_name}: {task_description}" if task_description else task_name
                
                logger.info(f"🤖 Executing AI pipeline for task: {task_name}")
                
                # Execute complete AI-driven pipeline
                pipeline_result = await real_tool_integration_pipeline.execute_complete_pipeline(
                    task_id=completed_task_id,
                    task_name=task_name,
                    task_objective=task_objective,
                    business_context=business_context,
                    existing_task_result=task_data
                )
                
                logger.info(f"✅ AI Pipeline completed: Success={pipeline_result.execution_successful}, Quality={pipeline_result.content_quality_score:.1f}")
                
                # If pipeline enhanced the content, update the task with new results
                if (pipeline_result.execution_successful and 
                    pipeline_result.content_quality_score > 50 and
                    pipeline_result.final_content and
                    pipeline_result.final_content != {"error": "Content generation failed"}):
                    
                    # Update task with enhanced content from pipeline
                    enhanced_result = {
                        "original_result": task_output,
                        "ai_enhanced_content": pipeline_result.final_content,
                        "quality_score": pipeline_result.content_quality_score,
                        "tool_usage_score": pipeline_result.tool_usage_score,
                        "business_readiness_score": pipeline_result.business_readiness_score,
                        "pipeline_reasoning": pipeline_result.pipeline_reasoning,
                        "stages_completed": pipeline_result.stages_completed,
                        "learning_patterns_created": pipeline_result.learning_patterns_created,
                        "auto_improvements": pipeline_result.auto_improvements,
                        "enhanced_by": "ai_driven_pipeline",
                        "enhanced_at": datetime.now().isoformat()
                    }
                    
                    # Update the task with enhanced results
                    await update_task_status(
                        completed_task_id,
                        "completed",
                        enhanced_result
                    )
                    
                    # 🎯 CRITICAL FIX: Update goal progress via Unified Progress Manager
                    try:
                        from services.unified_progress_manager import unified_progress_manager
                        progress_result = await unified_progress_manager.handle_task_completion(
                            completed_task_id, enhanced_result
                        )
                        if progress_result.get("updated"):
                            logger.info(f"✅ Enhanced task {completed_task_id} updated goal progress: {progress_result}")
                    except Exception as e:
                        logger.error(f"Error updating goal progress for enhanced task {completed_task_id}: {e}")
                    
                    logger.info(f"🎁 Task {completed_task_id} enhanced with AI pipeline: Quality {pipeline_result.content_quality_score:.1f}/100")
                    
                    # 🎯 Goal Progress Update: Use enhanced content for goal progress
                    from database import get_workspace_goals
                    workspace_goals = await get_workspace_goals(workspace_id, status="active")
                    
                    if workspace_goals:
                        # Calculate progress increment based on content quality
                        progress_increment = min(25.0, pipeline_result.content_quality_score / 4.0)
                        
                        for goal in workspace_goals:
                            try:
                                await update_goal_progress(
                                    goal["id"], 
                                    progress_increment,
                                    task_id=completed_task_id,
                                    task_business_context=business_context
                                )
                                logger.info(f"📈 Updated goal {goal.get('title', 'Unknown')} progress by {progress_increment:.1f}%")
                            except Exception as goal_error:
                                logger.warning(f"Failed to update goal progress: {goal_error}")
                
                else:
                    logger.warning(f"⚠️ AI Pipeline did not improve task {completed_task_id}: Success={pipeline_result.execution_successful}, Quality={pipeline_result.content_quality_score}")
                    
                    # Still try to update goal progress with original content
                    from database import get_workspace_goals
                    workspace_goals = await get_workspace_goals(workspace_id, status="active")
                    
                    if workspace_goals and len(workspace_goals) > 0:
                        # Smaller increment for non-enhanced content
                        progress_increment = 10.0
                        
                        goal = workspace_goals[0]  # Update first active goal
                        try:
                            await update_goal_progress(
                                goal["id"], 
                                progress_increment,
                                task_id=completed_task_id,
                                task_business_context=business_context
                            )
                            logger.info(f"📈 Updated goal {goal.get('title', 'Unknown')} progress by {progress_increment:.1f}% (original content)")
                        except Exception as goal_error:
                            logger.warning(f"Failed to update goal progress: {goal_error}")
                
            except ImportError:
                logger.warning("⚠️ AI-driven pipeline not available, falling back to basic asset processing")
                # Fallback to basic goal progress update
                from database import get_workspace_goals
                workspace_goals = await get_workspace_goals(workspace_id, status="active")
                
                if workspace_goals and len(workspace_goals) > 0:
                    goal = workspace_goals[0]
                    try:
                        await update_goal_progress(goal["id"], 5.0, task_id=completed_task_id)
                        logger.info(f"📈 Updated goal {goal.get('title', 'Unknown')} progress by 5.0% (fallback)")
                    except Exception as goal_error:
                        logger.warning(f"Failed to update goal progress: {goal_error}")
                
        except Exception as e:
            logger.error(f"❌ AI-driven asset processing failed for task {completed_task_id}: {e}")
            # Don't raise - asset processing failure shouldn't break task completion

    async def _trigger_workflow_orchestrator_if_needed(self, workspace_id: str, completed_task_id: str):
        """
        🎼 WORKFLOW ORCHESTRATOR INTEGRATION
        
        Trigger complete end-to-end workflow when significant task completion occurs
        """
        try:
            # Import WorkflowOrchestrator
            try:
                from services.workflow_orchestrator import workflow_orchestrator
                WORKFLOW_ORCHESTRATOR_AVAILABLE = True
            except ImportError as e:
                logger.warning(f"WorkflowOrchestrator not available: {e}")
                return
            
            # Get task details to determine workflow trigger criteria
            task_data = await get_task(completed_task_id)
            if not task_data:
                return
            
            # Check if this task completion should trigger a complete workflow
            should_trigger_workflow = await self._should_trigger_complete_workflow(
                workspace_id, completed_task_id, task_data
            )
            
            if should_trigger_workflow:
                # Get goal associated with this task
                goal_id = task_data.get("goal_id")
                if goal_id:
                    logger.info(f"🎼 TRIGGERING WORKFLOW ORCHESTRATOR: Task {completed_task_id} completed, starting complete workflow for goal {goal_id}")
                    
                    try:
                        # Execute complete workflow with timeout and quality gates
                        workflow_result = await workflow_orchestrator.execute_complete_workflow(
                            workspace_id=workspace_id,
                            goal_id=goal_id,
                            timeout_minutes=30,
                            enable_rollback=True,
                            quality_threshold=75.0
                        )
                        
                        if workflow_result.success:
                            logger.info(f"✅ WORKFLOW ORCHESTRATOR: Complete workflow successful for goal {goal_id}")
                            logger.info(f"📊 Workflow Results: {workflow_result.tasks_generated} tasks, {workflow_result.deliverables_created} deliverables, {workflow_result.quality_score:.1f}% quality")
                        else:
                            logger.warning(f"❌ WORKFLOW ORCHESTRATOR: Complete workflow failed for goal {goal_id}: {workflow_result.error}")
                            
                            # If rollback was performed, log the details
                            if workflow_result.rollback_performed:
                                rollback_status = "successful" if workflow_result.rollback_success else "failed"
                                logger.warning(f"🔄 WORKFLOW ROLLBACK: {rollback_status}")
                                
                    except Exception as workflow_error:
                        logger.error(f"❌ WORKFLOW ORCHESTRATOR: Critical error executing workflow for goal {goal_id}: {workflow_error}")
                        logger.info("🔄 Task execution will continue normally despite workflow orchestrator error")
                else:
                    logger.debug(f"Task {completed_task_id} has no associated goal - no workflow orchestration needed")
            else:
                logger.debug(f"Task {completed_task_id} completion does not meet workflow trigger criteria")
                
        except Exception as e:
            logger.error(f"Error in WorkflowOrchestrator integration: {e}")

    async def _should_trigger_complete_workflow(self, workspace_id: str, completed_task_id: str, task_data: dict) -> bool:
        """
        Determine if completing this task should trigger a complete workflow orchestration
        """
        try:
            # Trigger criteria:
            # 1. Task is associated with a goal
            # 2. Task represents significant progress towards goal completion
            # 3. Workspace is ready for deliverable generation
            
            goal_id = task_data.get("goal_id")
            if not goal_id:
                return False
            
            # Check if this task represents significant progress (high priority/critical task)
            task_priority = task_data.get("priority", "medium")
            context_data = task_data.get("context_data", {}) or {}
            project_phase = context_data.get("project_phase", "").upper()
            is_finalization = project_phase == "FINALIZATION"
            is_high_priority = task_priority == "high"
            
            # Always trigger for finalization tasks
            if is_finalization:
                logger.info(f"🎯 FINALIZATION TASK COMPLETED: Triggering complete workflow for task {completed_task_id}")
                return True
            
            # Check if enough tasks are completed for this goal to warrant workflow orchestration
            tasks = await list_tasks(workspace_id)
            goal_tasks = [t for t in tasks if t.get("goal_id") == goal_id]
            completed_goal_tasks = [t for t in goal_tasks if t.get("status") == "completed"]
            
            # Trigger if we've completed at least 50% of tasks for this goal
            if len(goal_tasks) > 0:
                completion_rate = len(completed_goal_tasks) / len(goal_tasks)
                if completion_rate >= 0.5:
                    logger.info(f"🎯 GOAL PROGRESS THRESHOLD: {completion_rate:.1%} tasks completed for goal {goal_id}, triggering workflow")
                    return True
            
            # Trigger for high-priority tasks that might represent major milestones
            if is_high_priority and len(completed_goal_tasks) >= 2:
                logger.info(f"🎯 HIGH-PRIORITY MILESTONE: High priority task completed with sufficient goal progress, triggering workflow")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error determining workflow trigger criteria: {e}")
            return False
    
    async def _create_integration_event(self, workspace_id: str, event_type: str, 
                                      source_component: str, target_component: str = None,
                                      event_data: Dict[str, Any] = None):
        """Create an integration event for event-driven coordination"""
        try:
            from database import get_supabase_client
            supabase = get_supabase_client()
            
            event = {
                'workspace_id': workspace_id,
                'event_type': event_type,
                'source_component': source_component,
                'target_component': target_component,
                'event_data': event_data or {},
                'status': 'pending'
            }
            
            result = supabase.table('integration_events').insert(event).execute()
            logger.debug(f"Created integration event: {event_type} from {source_component}")
            
        except Exception as e:
            logger.error(f"Failed to create integration event: {e}")

    async def refresh_agent_manager_cache(self, workspace_id: str) -> bool:
        """Refresh AgentManager cache after new agents are created"""
        try:
            workspace_uuid = UUID(workspace_id)
            if workspace_uuid in self.workspace_managers:
                # Re-initialize the existing agent manager to pick up new agents
                await self.workspace_managers[workspace_uuid].initialize()
                logger.info(f"🔄 Successfully refreshed existing agent manager cache for workspace {workspace_id}")
                return True
            else:
                # 🚨 CRITICAL FIX: Create AgentManager immediately instead of deferring
                logger.info(f"No existing agent manager found for workspace {workspace_id}, creating one now...")
                manager = await self.get_agent_manager(workspace_id)
                if manager:
                    logger.info(f"✅ Successfully created and initialized agent manager for workspace {workspace_id}")
                    return True
                else:
                    logger.error(f"❌ Failed to create agent manager for workspace {workspace_id}")
                    return False
        except Exception as e:
            logger.error(f"⚠️ Failed to refresh agent manager cache for workspace {workspace_id}: {e}")
            return False

    async def _assess_adaptive_system_load(self):
        """🔍 INTELLIGENT LOAD ASSESSMENT: Determine current system activity level"""
        try:
            # BATCH QUERY: Get all metrics with smart caching
            system_metrics = await self._get_cached_system_metrics()
            
            pending_tasks = system_metrics.get('pending_tasks', 0)
            active_workspaces = system_metrics.get('active_workspaces', 0) 
            recent_activity = system_metrics.get('recent_activity', False)
            
            # INTELLIGENT LOAD CLASSIFICATION
            if pending_tasks == 0 and not recent_activity:
                self.executor_metrics['load_level'] = "idle"
            elif pending_tasks <= 3 and active_workspaces <= 1:
                self.executor_metrics['load_level'] = "low"  
            elif pending_tasks <= 10 and active_workspaces <= 3:
                self.executor_metrics['load_level'] = "medium"
            elif pending_tasks <= 20:
                self.executor_metrics['load_level'] = "high"
            else:
                self.executor_metrics['load_level'] = "overload"
                
            logger.debug(f"🔍 Load assessment: {self.executor_metrics['load_level']} "
                        f"(tasks: {pending_tasks}, workspaces: {active_workspaces})")
            
        except Exception as e:
            logger.warning(f"Load assessment failed, using medium load: {e}")
            self.executor_metrics['load_level'] = "medium"
    
    async def _get_cached_system_metrics(self):
        """📊 SMART CACHING: Get system metrics with intelligent caching"""
        cache_key = "system_metrics"
        
        # Check cache validity
        if (cache_key in self.operation_cache and 
            (datetime.now() - self.operation_cache[cache_key]['timestamp']).total_seconds() < self.cache_ttl):
            return self.operation_cache[cache_key]['data']
        
        try:
            # BATCH DATABASE QUERY (instead of multiple separate queries)
            from database import get_pending_tasks_count, get_active_workspaces
            
            pending_tasks = await get_pending_tasks_count() or 0
            active_workspaces_list = await get_active_workspaces() or []
            active_workspaces = len(active_workspaces_list)
            recent_activity = pending_tasks > 0 or active_workspaces > 0
            
            metrics = {
                'pending_tasks': pending_tasks,
                'active_workspaces': active_workspaces,
                'recent_activity': recent_activity,
                'timestamp': datetime.now()
            }
            
            # Cache the result
            self.operation_cache[cache_key] = {
                'data': metrics,
                'timestamp': datetime.now()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {'pending_tasks': 0, 'active_workspaces': 0, 'recent_activity': False}
    
    def _determine_operations_for_current_load(self):
        """🎯 INTELLIGENT OPERATION SELECTION: Choose operations based on current load"""
        load = self.executor_metrics['load_level']
        
        if load == "idle":
            return ["health_check", "cleanup", "telemetry"]
        elif load == "low": 
            return ["circuit_breaker", "process_tasks", "health_check", "telemetry"]
        elif load == "medium":
            return ["circuit_breaker", "process_tasks", "asset_coordination", "runaway_check", "telemetry"]  
        elif load == "high":
            return ["circuit_breaker", "process_tasks", "asset_coordination", "quality_check", "workspace_check", "telemetry"]
        else:  # overload
            return ["circuit_breaker", "process_tasks"]  # Only essential operations
    
    async def _execute_adaptive_operations(self, operations):
        """⚡ INTELLIGENT BATCH EXECUTION: Execute selected operations efficiently"""
        for operation in operations:
            try:
                if operation == "circuit_breaker":
                    if await self.check_global_circuit_breaker():
                        logger.critical("⚠️ CIRCUIT BREAKER ACTIVATED - System paused")
                        await asyncio.sleep(60)
                        return  # Skip other operations when circuit breaker is active
                        
                elif operation == "process_tasks":
                    await self.process_pending_tasks_anti_loop()
                    
                elif operation == "asset_coordination":
                    try:
                        active_workspaces = await get_active_workspaces()
                        for ws_id in active_workspaces:
                            await self.coordinate_asset_oriented_workflow(ws_id)
                    except Exception as e:
                        logger.error(f"Error in asset coordination: {e}")
                        
                elif operation == "quality_check":
                    if self.quality_integration_enabled:
                        try:
                            await self._check_quality_enhanced_deliverables()
                        except Exception as e:
                            logger.error(f"Error in quality deliverable check: {e}")
                            
                elif operation == "workspace_check":
                    if self.auto_generation_enabled:
                        await self.check_for_new_workspaces()
                        
                elif operation == "runaway_check":
                    if (self.last_runaway_check is None or
                        (datetime.now() - self.last_runaway_check).total_seconds() > self.runaway_check_interval):
                        await self.periodic_runaway_check()
                        self.last_runaway_check = datetime.now()
                        
                elif operation == "cleanup":
                    if datetime.now() - self.last_cleanup > timedelta(minutes=5):
                        await self._cleanup_tracking_data()
                        
                elif operation == "health_check":
                    logger.debug("💚 System health check completed")
                    
                elif operation == "telemetry":
                    # 📊 ENHANCED: Telemetry collection (from old loop)
                    if TELEMETRY_MONITOR_AVAILABLE and system_telemetry_monitor:
                        try:
                            if (not hasattr(self, 'last_telemetry_check') or 
                                (datetime.now() - self.last_telemetry_check).total_seconds() > 300):
                                
                                await system_telemetry_monitor.collect_comprehensive_metrics()
                                self.last_telemetry_check = datetime.now()
                                logger.debug("📊 System telemetry collected successfully")
                        except Exception as telemetry_error:
                            logger.warning(f"Telemetry collection error: {telemetry_error}")
                    
            except Exception as e:
                logger.error(f"Operation {operation} failed: {e}")
    
    async def _update_executor_metrics(self, loop_time):
        """📊 PERFORMANCE TRACKING: Update executor performance metrics"""
        self.executor_metrics['loop_count'] += 1
        
        # Running average of loop time
        if self.executor_metrics['avg_loop_time'] == 0:
            self.executor_metrics['avg_loop_time'] = loop_time
        else:
            self.executor_metrics['avg_loop_time'] = (
                self.executor_metrics['avg_loop_time'] * 0.9 + loop_time * 0.1
            )
            
        self.executor_metrics['last_activity'] = datetime.now()
        
        # Log performance every 10 loops with load-based frequency
        log_frequency = 10 if self.executor_metrics['load_level'] in ['medium', 'high'] else 5
        if self.executor_metrics['loop_count'] % log_frequency == 0:
            logger.info(f"📊 Executor metrics: "
                       f"loops: {self.executor_metrics['loop_count']}, "
                       f"avg_time: {self.executor_metrics['avg_loop_time']:.2f}s, "
                       f"load: {self.executor_metrics['load_level']}")

    async def _check_quality_enhanced_deliverables(self):
        """Check for deliverables needing quality enhancement"""
        # This method can be overridden by QualityEnhancedTaskExecutor
        pass


# Aggiungi queste funzioni helper:

async def enable_quality_integration() -> Dict[str, Any]:
    """Abilita quality integration runtime"""
    
    if not QUALITY_SYSTEM_AVAILABLE:
        return {"success": False, "message": "Quality system not available"}
    
    if isinstance(task_executor, QualityEnhancedTaskExecutor):
        task_executor.quality_integration_enabled = True
        return {
            "success": True, 
            "message": "Quality integration enabled",
            "executor_type": "QualityEnhancedTaskExecutor"
        }
    else:
        return {
            "success": False, 
            "message": "Standard TaskExecutor in use, restart required for quality integration"
        }

async def disable_quality_integration() -> Dict[str, Any]:
    """Disabilita quality integration runtime"""
    
    if isinstance(task_executor, QualityEnhancedTaskExecutor):
        task_executor.quality_integration_enabled = False
        return {"success": True, "message": "Quality integration disabled"}
    else:
        return {"success": True, "message": "Quality integration not active"}

def get_quality_integration_status() -> Dict[str, Any]:
    """Ottieni stato quality integration"""
    
    return {
        "quality_system_available": QUALITY_SYSTEM_AVAILABLE,
        "executor_type": type(task_executor).__name__,
        "integration_enabled": (
            isinstance(task_executor, QualityEnhancedTaskExecutor) and 
            getattr(task_executor, 'quality_integration_enabled', False)
        ),
        "configuration": QualitySystemConfig.get_all_settings() if (QUALITY_SYSTEM_AVAILABLE and QualitySystemConfig) else None
    }

class QualityEnhancedTaskExecutor(TaskExecutor):
    """
    Enhanced TaskExecutor con integrazione AI Quality Assurance
    """
    
    def __init__(self):
        super().__init__()
        self.quality_integration_enabled = (
            QUALITY_SYSTEM_AVAILABLE and 
            QualitySystemConfig and
            QualitySystemConfig.INTEGRATE_WITH_EXISTING_DELIVERABLE_SYSTEM
        )
        
        if self.quality_integration_enabled:
            logger.info("🔍 EXECUTOR: Quality assurance integration enabled")
            self.last_quality_check = {}  # workspace_id -> datetime
            self.quality_check_interval = 300  # 5 minuti
        else:
            logger.info("🔄 EXECUTOR: Standard mode without quality integration")
    
    async def execution_loop(self):
        """🚀 INTELLIGENT EXECUTION LOOP with adaptive performance optimization"""
        
        logger.info("🧠 Intelligent execution loop started with adaptive performance optimization")
        logger.info(f"📊 Initial load level: {self.executor_metrics['load_level']}, sleep interval: {self.adaptive_intervals[self.executor_metrics['load_level']]}s")
        
        # Metrics are now initialized in __init__ to prevent AttributeError
        
        while self.running:
            try:
                loop_start = time.time()
                
                await self.pause_event.wait()
                if not self.running:
                    break
                
                # 🔍 STEP 1: ASSESS SYSTEM LOAD (holistic approach)
                await self._assess_adaptive_system_load()
                
                # Log the main loop iteration for visibility
                if self.executor_metrics['load_level'] != "idle":
                    logger.info("🔄 MAIN LOOP: Processing pending tasks, asset coordination, checking workspaces")
                
                # 🎯 STEP 2: DETERMINE OPERATIONS BASED ON LOAD
                operations = self._determine_operations_for_current_load()
                
                # ⚡ STEP 3: EXECUTE SELECTED OPERATIONS EFFICIENTLY
                await self._execute_adaptive_operations(operations)
                
                # 📊 STEP 4: UPDATE PERFORMANCE METRICS
                loop_time = time.time() - loop_start
                await self._update_executor_metrics(loop_time)
                
                # 🛌 STEP 5: ADAPTIVE SLEEP BASED ON LOAD
                sleep_interval = self.adaptive_intervals[self.executor_metrics['load_level']]
                logger.debug(f"🛌 Adaptive sleep: {sleep_interval}s (load: {self.executor_metrics['load_level']})")
                await asyncio.sleep(sleep_interval)
                
            except asyncio.CancelledError:
                logger.info("Enhanced execution loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in enhanced execution loop: {e}", exc_info=True)
                await asyncio.sleep(30)
        
        logger.info("Enhanced execution loop finished")
    
    async def _assess_adaptive_system_load(self):
        """🔍 INTELLIGENT LOAD ASSESSMENT: Determine current system activity level"""
        try:
            # BATCH QUERY: Get all metrics with smart caching
            system_metrics = await self._get_cached_system_metrics()
            
            pending_tasks = system_metrics.get('pending_tasks', 0)
            active_workspaces = system_metrics.get('active_workspaces', 0) 
            recent_activity = system_metrics.get('recent_activity', False)
            
            # INTELLIGENT LOAD CLASSIFICATION
            if pending_tasks == 0 and not recent_activity:
                self.executor_metrics['load_level'] = "idle"
            elif pending_tasks <= 3 and active_workspaces <= 1:
                self.executor_metrics['load_level'] = "low"  
            elif pending_tasks <= 10 and active_workspaces <= 3:
                self.executor_metrics['load_level'] = "medium"
            elif pending_tasks <= 20:
                self.executor_metrics['load_level'] = "high"
            else:
                self.executor_metrics['load_level'] = "overload"
                
            logger.debug(f"🔍 Load assessment: {self.executor_metrics['load_level']} "
                        f"(tasks: {pending_tasks}, workspaces: {active_workspaces})")
            
        except Exception as e:
            logger.warning(f"Load assessment failed, using medium load: {e}")
            self.executor_metrics['load_level'] = "medium"
    
    async def _get_cached_system_metrics(self):
        """📊 SMART CACHING: Get system metrics with intelligent caching"""
        cache_key = "system_metrics"
        
        # Check cache validity
        if (cache_key in self.operation_cache and 
            (datetime.now() - self.operation_cache[cache_key]['timestamp']).total_seconds() < self.cache_ttl):
            return self.operation_cache[cache_key]['data']
        
        try:
            # BATCH DATABASE QUERY (instead of multiple separate queries)
            from database import get_pending_tasks_count, get_active_workspaces
            
            pending_tasks = await get_pending_tasks_count() or 0
            active_workspaces_list = await get_active_workspaces() or []
            active_workspaces = len(active_workspaces_list)
            recent_activity = pending_tasks > 0 or active_workspaces > 0
            
            metrics = {
                'pending_tasks': pending_tasks,
                'active_workspaces': active_workspaces,
                'recent_activity': recent_activity,
                'timestamp': datetime.now()
            }
            
            # Cache the result
            self.operation_cache[cache_key] = {
                'data': metrics,
                'timestamp': datetime.now()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {'pending_tasks': 0, 'active_workspaces': 0, 'recent_activity': False}
    
    def _determine_operations_for_current_load(self):
        """🎯 INTELLIGENT OPERATION SELECTION: Choose operations based on current load"""
        load = self.executor_metrics['load_level']
        
        if load == "idle":
            return ["health_check", "cleanup", "telemetry"]
        elif load == "low": 
            return ["circuit_breaker", "process_tasks", "health_check", "telemetry"]
        elif load == "medium":
            return ["circuit_breaker", "process_tasks", "asset_coordination", "runaway_check", "telemetry"]  
        elif load == "high":
            return ["circuit_breaker", "process_tasks", "asset_coordination", "quality_check", "workspace_check", "telemetry"]
        else:  # overload
            return ["circuit_breaker", "process_tasks"]  # Only essential operations
    
    async def _execute_adaptive_operations(self, operations):
        """⚡ INTELLIGENT BATCH EXECUTION: Execute selected operations efficiently"""
        for operation in operations:
            try:
                if operation == "circuit_breaker":
                    if await self.check_global_circuit_breaker():
                        logger.critical("⚠️ CIRCUIT BREAKER ACTIVATED - System paused")
                        await asyncio.sleep(60)
                        return  # Skip other operations when circuit breaker is active
                        
                elif operation == "process_tasks":
                    await self.process_pending_tasks_anti_loop()
                    
                elif operation == "asset_coordination":
                    try:
                        active_workspaces = await get_active_workspaces()
                        for ws_id in active_workspaces:
                            await self.coordinate_asset_oriented_workflow(ws_id)
                    except Exception as e:
                        logger.error(f"Error in asset coordination: {e}")
                        
                elif operation == "quality_check":
                    if self.quality_integration_enabled:
                        try:
                            await self._check_quality_enhanced_deliverables()
                        except Exception as e:
                            logger.error(f"Error in quality deliverable check: {e}")
                            
                elif operation == "workspace_check":
                    if self.auto_generation_enabled:
                        await self.check_for_new_workspaces()
                        
                elif operation == "runaway_check":
                    if (self.last_runaway_check is None or
                        (datetime.now() - self.last_runaway_check).total_seconds() > self.runaway_check_interval):
                        await self.periodic_runaway_check()
                        self.last_runaway_check = datetime.now()
                        
                elif operation == "cleanup":
                    if datetime.now() - self.last_cleanup > timedelta(minutes=5):
                        await self._cleanup_tracking_data()
                        
                elif operation == "health_check":
                    logger.debug("💚 System health check completed")
                    
                elif operation == "telemetry":
                    # 📊 ENHANCED: Telemetry collection (from old loop)
                    if TELEMETRY_MONITOR_AVAILABLE and system_telemetry_monitor:
                        try:
                            if (not hasattr(self, 'last_telemetry_check') or 
                                (datetime.now() - self.last_telemetry_check).total_seconds() > 300):
                                
                                await system_telemetry_monitor.collect_comprehensive_metrics()
                                self.last_telemetry_check = datetime.now()
                                logger.debug("📊 System telemetry collected successfully")
                        except Exception as telemetry_error:
                            logger.warning(f"Telemetry collection error: {telemetry_error}")
                    
            except Exception as e:
                logger.error(f"Operation {operation} failed: {e}")
    
    async def _update_executor_metrics(self, loop_time):
        """📊 PERFORMANCE TRACKING: Update executor performance metrics"""
        self.executor_metrics['loop_count'] += 1
        
        # Running average of loop time
        if self.executor_metrics['avg_loop_time'] == 0:
            self.executor_metrics['avg_loop_time'] = loop_time
        else:
            self.executor_metrics['avg_loop_time'] = (
                self.executor_metrics['avg_loop_time'] * 0.9 + loop_time * 0.1
            )
            
        self.executor_metrics['last_activity'] = datetime.now()
        
        # Log performance every 10 loops with load-based frequency
        log_frequency = 10 if self.executor_metrics['load_level'] in ['medium', 'high'] else 5
        if self.executor_metrics['loop_count'] % log_frequency == 0:
            logger.info(f"📊 Executor metrics: "
                       f"loops: {self.executor_metrics['loop_count']}, "
                       f"avg_time: {self.executor_metrics['avg_loop_time']:.2f}s, "
                       f"load: {self.executor_metrics['load_level']}")

    async def _check_quality_enhanced_deliverables(self):
        """
        Controlla workspace pronti per deliverable con quality assurance
        """
        
        try:
            # Ottieni workspace attivi che potrebbero aver bisogno di deliverable
            active_workspaces = await get_active_workspaces()
            
            for workspace_id in active_workspaces:
                try:
                    # Controlla se è tempo di verificare questo workspace
                    if not self._should_check_workspace_for_quality(workspace_id):
                        continue
                    
                    # Tentativo di creare deliverable quality-enhanced con circuit breaker protection
                    async def _safe_quality_deliverable_creation():
                        if QUALITY_SYSTEM_AVAILABLE and check_and_create_final_deliverable is not None:
                            return await check_and_create_final_deliverable(workspace_id)
                        else:
                            # Fallback se quality system non disponibile
                            from backend.deliverable_system.unified_deliverable_engine import check_and_create_final_deliverable as fallback_func
                            return await fallback_func(workspace_id)
                    
                    deliverable_id = await self._execute_with_circuit_breaker(_safe_quality_deliverable_creation)
                    
                    if deliverable_id:
                        logger.info(f"🔍 QUALITY DELIVERABLE: Created {deliverable_id} for {workspace_id}")
                        
                        # Registra metriche se abilitato
                        if QualitySystemConfig and QualitySystemConfig.ENABLE_QUALITY_METRICS_COLLECTION:
                            try:
                                from backend.ai_quality_assurance.quality_integration import quality_metrics_collector
                                quality_metrics_collector.record_enhancement_activity(
                                    workspace_id, 
                                    deliverable_id, 
                                    "quality_enhanced_deliverable_creation", 
                                    True
                                )
                            except Exception as e:
                                logger.debug(f"Error recording quality metrics: {e}")
                        
                        # Aggiorna timestamp ultimo check
                        self.last_quality_check[workspace_id] = datetime.now()
                    
                except Exception as e_ws:
                    logger.error(f"Error creating quality deliverable for {workspace_id}: {e_ws}")
                    
                    # Fallback al sistema standard se abilitato
                    if QualitySystemConfig and QualitySystemConfig.FALLBACK_TO_STANDARD_SYSTEM_ON_ERROR:
                        try:
                            async def _safe_fallback_deliverable():
                                from backend.deliverable_system.unified_deliverable_engine import check_and_create_final_deliverable
                                return await check_and_create_final_deliverable(workspace_id)
                            
                            fallback_id = await self._execute_with_circuit_breaker(_safe_fallback_deliverable)
                            
                            if fallback_id:
                                logger.info(f"📦 FALLBACK DELIVERABLE: Created {fallback_id} for {workspace_id}")
                                
                        except ImportError as import_error:
                            logger.error(f"Cannot import unified_deliverable_engine for fallback: {import_error}")
                        except Exception as fallback_error:
                            logger.error(f"Fallback deliverable also failed for {workspace_id}: {fallback_error}")
                    
        except Exception as e:
            logger.error(f"Error in _check_quality_enhanced_deliverables: {e}")
    
    def _should_check_workspace_for_quality(self, workspace_id: str) -> bool:
        """Determina se è tempo di controllare un workspace per deliverable di qualità"""
        
        last_check = self.last_quality_check.get(workspace_id)
        if not last_check:
            return True  # Mai controllato prima
        
        # Controlla solo ogni X minuti
        time_since_check = (datetime.now() - last_check).total_seconds()
        return time_since_check >= self.quality_check_interval
    
    def get_detailed_stats(self) -> Dict[str, Any]:
        """Override per includere statistiche quality integration"""
        
        base_stats = super().get_detailed_stats()
        
        if self.quality_integration_enabled:
            base_stats["quality_integration"] = {
                "enabled": True,
                "workspaces_monitored": len(self.last_quality_check),
                "last_quality_checks": {
                    ws_id: timestamp.isoformat() 
                    for ws_id, timestamp in self.last_quality_check.items()
                },
                "check_interval_seconds": self.quality_check_interval
            }
        else:
            base_stats["quality_integration"] = {"enabled": False}
        
        return base_stats

# Istanza globale del TaskExecutor

if QUALITY_SYSTEM_AVAILABLE and QualitySystemConfig and QualitySystemConfig.INTEGRATE_WITH_EXISTING_DELIVERABLE_SYSTEM:
    task_executor = QualityEnhancedTaskExecutor()
    logger.info("🔍 TASK EXECUTOR INITIALIZED: Quality-enhanced version")
else:
    task_executor = TaskExecutor()
    logger.info("📦 TASK EXECUTOR INITIALIZED: Standard version")

# Funzioni di controllo executor
async def start_task_executor():
    """Avvia il TaskExecutor"""
    await task_executor.start()

async def stop_task_executor():
    """Ferma il TaskExecutor"""
    await task_executor.stop()

async def pause_task_executor():
    """Pausa il TaskExecutor"""
    await task_executor.pause()

async def resume_task_executor():
    """Riprende il TaskExecutor"""
    await task_executor.resume()

def get_executor_stats() -> Dict[str, Any]:
    """Ottieni statistiche dell'executor"""
    return task_executor.get_detailed_stats()

def get_recent_executor_activity(workspace_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Ottieni attività recente dell'executor"""
    return task_executor.get_recent_activity(workspace_id=workspace_id, limit=limit)

# Funzioni di controllo manuale
async def trigger_initial_workspace_task(workspace_id: str) -> Optional[str]:
    """Trigger manuale per creare task iniziale in un workspace"""
    logger.info(f"Manual trigger for initial task in W:{workspace_id}")
    if not task_executor.running:
        logger.warning("Executor not running. Initial task creation might be limited")
    return await task_executor.create_initial_workspace_task(workspace_id)

async def trigger_runaway_check() -> Dict[str, Any]:
    """Trigger manuale per runaway check"""
    logger.info("Manual trigger for runaway check")
    if not task_executor.running:
        return {"success": False, "message": "Executor not running"}
    
    results = await task_executor.periodic_runaway_check()
    task_executor.last_runaway_check = datetime.now()
    
    return {
        "success": True,
        "message": "Runaway check manually triggered",
        "check_results": results,
        "current_runaway_status": {
            "paused_workspaces": list(task_executor.workspace_auto_generation_paused),
            "last_check": task_executor.last_runaway_check.isoformat()
        }
    }

async def reset_workspace_auto_generation(workspace_id: str) -> Dict[str, Any]:
    """Reset auto-generation per un workspace specifico"""
    logger.info(f"Manual trigger to reset auto-gen for W:{workspace_id}")
    if not task_executor.running:
        return {"success": False, "message": f"Executor not running for W:{workspace_id}"}
    
    if workspace_id in task_executor.workspace_auto_generation_paused:
        await task_executor._resume_auto_generation_for_workspace(workspace_id)
        health = await task_executor.check_workspace_health(workspace_id)
        return {
            "success": True,
            "message": f"Auto-gen resumed for W:{workspace_id}. Health score: {health.get('health_score', 'N/A')}",
            "workspace_unpaused": workspace_id not in task_executor.workspace_auto_generation_paused
        }
    else:
        return {"success": False, "message": f"Auto-gen not paused for W:{workspace_id}"}

async def complete_thinking_processes_for_task(workspace_id: str, task_id: str, status: str, reason: str):
    """
    🧠 Complete any incomplete thinking processes for a completed task
    
    This function finds recent thinking processes in the workspace that are incomplete
    and completes them with appropriate conclusions based on task outcome.
    """
    try:
        # Get recent incomplete thinking processes from this workspace (last 10 minutes)
        from datetime import datetime, timedelta
        recent_cutoff = (datetime.utcnow() - timedelta(minutes=10)).isoformat()
        
        # Query the database directly since thinking_engine.get_workspace_thinking might not include incomplete ones
        from database import get_supabase_client
        supabase = get_supabase_client()
        
        recent_processes = supabase.table("thinking_processes") \
            .select("process_id,started_at,context") \
            .eq("workspace_id", workspace_id) \
            .is_("completed_at", "null") \
            .gte("started_at", recent_cutoff) \
            .execute()
        
        logger.info(f"🧠 Found {len(recent_processes.data)} incomplete thinking processes in workspace {workspace_id}")
        
        for process_data in recent_processes.data:
            process_id = process_data["process_id"]
            context = process_data.get("context", "")
            
            # Check if this thinking process is related to our task
            if task_id in context or any(keyword in context.lower() for keyword in ["task", "execution", "analysis"]):
                
                # Create appropriate conclusion based on task status
                if status == TaskStatus.COMPLETED.value:
                    conclusion = f"✅ Task execution completed successfully. The task has been finalized with status: {status}. Reason: {reason}"
                    confidence = 0.9
                    
                    # Add a final step before completion
                    await thinking_engine.add_thinking_step(
                        process_id=process_id,
                        step_type="conclusion",
                        content=f"🎯 Task finalization successful: {reason}. All requirements have been met and the task is now complete.",
                        confidence=confidence
                    )
                    
                elif status == TaskStatus.FAILED.value:
                    conclusion = f"❌ Task execution failed. Status: {status}. Reason: {reason}"
                    confidence = 0.6
                    
                    # Add a final step before completion
                    await thinking_engine.add_thinking_step(
                        process_id=process_id,
                        step_type="error_analysis",
                        content=f"💥 Task failed during execution: {reason}. This requires investigation to prevent similar failures.",
                        confidence=confidence
                    )
                    
                elif status == TaskStatus.TIMED_OUT.value:
                    conclusion = f"⏱️ Task execution timed out. Status: {status}. Reason: {reason}"
                    confidence = 0.7
                    
                    # Add a final step before completion
                    await thinking_engine.add_thinking_step(
                        process_id=process_id,
                        step_type="timeout_analysis", 
                        content=f"⏰ Task exceeded time limits: {reason}. Consider optimizing execution strategy or increasing timeout thresholds.",
                        confidence=confidence
                    )
                else:
                    conclusion = f"Task completed with status: {status}. Reason: {reason}"
                    confidence = 0.8
                    
                    # Add a final step before completion
                    await thinking_engine.add_thinking_step(
                        process_id=process_id,
                        step_type="completion",
                        content=f"🔄 Task finished with final status: {status}. Processing reason: {reason}",
                        confidence=confidence
                    )
                
                # Complete the thinking process
                await thinking_engine.complete_thinking_process(
                    process_id=process_id,
                    conclusion=conclusion,
                    overall_confidence=confidence
                )
                
                logger.info(f"🧠 Completed thinking process {process_id} for task {task_id} with status {status}")
                
    except Exception as e:
        logger.error(f"🧠 Error completing thinking processes for task {task_id}: {e}", exc_info=True)
        # Don't fail the task completion due to thinking process errors

    async def _check_and_trigger_deliverable_creation(self, workspace_id: str, completed_task_id: str):
        """
        🎯 ENHANCED: Business Value-Aware Deliverable Creation System
        
        Rispetta PILLAR 7 (Intelligent Decision Making) - solo deliverable con vero business value.
        """
        try:
            logger.info(f"🔍 Enhanced deliverable check for workspace {workspace_id} after task {completed_task_id}")
            
            # 🚀 CRITICAL FIX: Asset System Integration - Process completed task into asset artifacts
            await self._process_task_into_assets(workspace_id, completed_task_id)
            
            # 🎯 PRIORITY 1 FIX: Extract achievements using DeliverableAchievementMapper
            await self._extract_and_map_task_achievements(workspace_id, completed_task_id)
            
            # 🎼 WORKFLOW ORCHESTRATOR INTEGRATION: Trigger complete workflow validation
            await self._trigger_workflow_orchestrator_if_needed(workspace_id, completed_task_id)
            
            # Get environment thresholds
            from os import getenv
            min_completed_tasks = int(getenv("MIN_COMPLETED_TASKS_FOR_DELIVERABLE", "2"))
            business_value_threshold = float(getenv("BUSINESS_VALUE_THRESHOLD", "70.0"))
            
            # 🎯 ENHANCED: Check both task count AND business content quality
            from database import list_tasks, get_supabase_client
            supabase = get_supabase_client()
            
            # Get all completed tasks and analyze their business value
            tasks = await list_tasks(workspace_id, status="completed")
            completed_count = len(tasks)
            
            if completed_count < min_completed_tasks:
                logger.debug(f"⏳ Not enough completed tasks ({completed_count}/{min_completed_tasks}) for workspace {workspace_id}")
                return
            
            # 🧠 PILLAR 7: Analyze business content quality across all tasks
            business_content_tasks = await self._analyze_tasks_business_content(tasks)
            high_value_tasks_count = len([t for t in business_content_tasks if t.get("business_value_score", 0) >= 40.0])
            
            if high_value_tasks_count < min_completed_tasks:
                logger.debug(f"⏳ Not enough high-value business tasks ({high_value_tasks_count}/{min_completed_tasks}) for workspace {workspace_id}")
                return
            
            # 🎯 ENHANCED: Goal Completion Guarantee System - Ensure ALL goals get deliverables
            goals_response = supabase.table("workspace_goals")\
                .select("*")\
                .eq("workspace_id", workspace_id)\
                .execute()
            
            business_ready_goals = []
            completion_guaranteed_goals = []
            
            for goal in goals_response.data or []:
                goal_metadata = goal.get("metadata", {}) or {}
                business_score = goal_metadata.get("business_content_score", 0.0)
                progress = goal.get("current_value", 0) / max(goal.get("target_value", 1), 1) * 100
                goal_description = goal.get('description', 'Unknown')
                
                # 🎯 HIGH-VALUE GOALS: Both high progress AND high business value
                if progress >= 80.0 and business_score >= business_value_threshold:
                    business_ready_goals.append(goal)
                    logger.info(f"🎯 HIGH-VALUE Goal '{goal_description}': {progress:.1f}% progress, {business_score:.1f} business score - READY")
                
                # 🔒 COMPLETION GUARANTEE: Goals at 90%+ get deliverable regardless of business score
                elif progress >= 90.0:
                    completion_guaranteed_goals.append(goal)
                    logger.warning(f"🔒 GUARANTEED Goal '{goal_description}': {progress:.1f}% progress, {business_score:.1f} business score - FORCED COMPLETION")
                    
                    # Update goal status to indicate completion guarantee was triggered
                    try:
                        goal_update = {
                            "metadata": {
                                **goal_metadata,
                                "completion_guaranteed": True,
                                "completion_guarantee_timestamp": datetime.now().isoformat(),
                                "original_business_score": business_score,
                                "completion_reason": "progress_threshold_met"
                            }
                        }
                        supabase.table("workspace_goals")\
                            .update(goal_update)\
                            .eq("id", goal.get("id"))\
                            .execute()
                    except Exception as meta_update_error:
                        logger.error(f"Could not update completion guarantee metadata for goal {goal.get('id')}: {meta_update_error}")
                else:
                    logger.debug(f"⏳ PENDING Goal '{goal_description}': {progress:.1f}% progress, {business_score:.1f} business score - NOT READY")
            
            # Combine both categories for deliverable creation
            all_deliverable_goals = business_ready_goals + completion_guaranteed_goals
            
            if not all_deliverable_goals:
                logger.info(f"⏳ No goals ready for deliverable creation in workspace {workspace_id}")
                return
            
            logger.info(f"✅ Found {len(business_ready_goals)} high-value goals + {len(completion_guaranteed_goals)} completion-guaranteed goals = {len(all_deliverable_goals)} total goals for deliverable creation")
            
            # 🎯 ENHANCED: Pass comprehensive context to deliverable creation
            deliverable_context = {
                "business_content_tasks": business_content_tasks,
                "business_ready_goals": business_ready_goals,
                "completion_guaranteed_goals": completion_guaranteed_goals,
                "all_deliverable_goals": all_deliverable_goals,
                "high_value_tasks_count": high_value_tasks_count,
                "business_value_threshold": business_value_threshold,
                "completion_guarantee_count": len(completion_guaranteed_goals),
                "content_analysis_timestamp": datetime.now().isoformat(),
                "guarantee_policy": "90_percent_progress_threshold"
            }
            
            # Import and call enhanced deliverable creation
            try:
                if check_and_create_final_deliverable:
                    # Call with enhanced context
                    result = await check_and_create_final_deliverable(workspace_id, deliverable_context)
                    logger.info(f"📦 Enhanced deliverable result for workspace {workspace_id}: {result}")
                else:
                    logger.warning("⚠️ check_and_create_final_deliverable function not available")
            except Exception as deliverable_error:
                logger.error(f"❌ Error creating enhanced deliverable for workspace {workspace_id}: {deliverable_error}")
                
        except Exception as e:
            logger.error(f"❌ Error in enhanced deliverable creation check for workspace {workspace_id}: {e}")
    
    async def _extract_and_map_task_achievements(self, workspace_id: str, completed_task_id: str):
        """
        🎯 PRIORITY 1: Extract achievements from completed task and map to goals
        
        This is the MISSING LINK between task completion and goal progress updates.
        """
        try:
            logger.info(f"🎯 Extracting achievements from completed task {completed_task_id}")
            
            # Import DeliverableAchievementMapper
            from services.deliverable_achievement_mapper import deliverable_achievement_mapper
            
            # Get task details
            task_data = await get_task(completed_task_id)
            if not task_data:
                logger.warning(f"Task {completed_task_id} not found for achievement extraction")
                return
            
            # Extract achievements from task result
            task_result = task_data.get("result", {}) or {}
            task_name = task_data.get("name", "Unknown Task")
            task_output = task_result.get("output", "") or str(task_result)
            
            logger.debug(f"Task result for achievement extraction: {task_result}")
            
            # 🎯 CHECK QUALITY ASSESSMENT FROM DATABASE
            # Use quality assessment from task completion in database.py instead of re-validating
            result_payload = task_data.get("result_payload", {})
            quality_assessment = result_payload.get("quality_assessment", {})
            
            if quality_assessment:
                passes_quality = quality_assessment.get("passes_quality_gate", True)
                quality_score = quality_assessment.get("score", 100)
                quality_reasoning = quality_assessment.get("reasoning", "No reasoning provided")
                
                if not passes_quality:
                    logger.warning(f"🚫 Task {completed_task_id} failed quality validation - blocking goal progress update")
                    logger.debug(f"Quality failure reason: {quality_reasoning} (score: {quality_score})")
                    
                    # Store quality gate failure in insights for tracking  
                    try:
                        from workspace_memory import workspace_memory
                        from models import InsightType
                        await workspace_memory.store_insight(
                            workspace_id=workspace_id,
                            insight_type=InsightType.CONSTRAINT,  # Quality failures are constraints
                            content=f"Task {task_name} failed quality assessment: {quality_reasoning}",
                            relevance_tags=["quality", "task_completion", "validation", "quality_gate_failure"],
                            confidence_score=0.9,
                            metadata=quality_assessment
                        )
                    except Exception as insight_error:
                        logger.error(f"Error storing quality gate failure insight: {insight_error}")
                    
                    # QUALITY LEARNING: Store detailed learning for future improvement
                    try:
                        from uuid import UUID
                        task_context = {
                            'task_type': task_data.get('task_type', 'unknown'),
                            'agent_id': task_data.get('agent_id', 'unknown'),
                            'goal_id': task_data.get('goal_id'),
                            'task_name': task_name
                        }
                        
                        await workspace_memory.store_quality_validation_learning(
                            workspace_id=UUID(workspace_id),
                            task_id=completed_task_id,
                            quality_assessment=quality_assessment,
                            task_context=task_context
                        )
                    except Exception as learning_error:
                        logger.error(f"Error storing quality learning: {learning_error}")
                    
                    return  # Block achievement extraction and goal progress
                else:
                    logger.info(f"✅ Task {completed_task_id} passed quality assessment (score: {quality_score}) - proceeding with achievement extraction")
            else:
                # No quality assessment available - proceed with warning
                logger.warning(f"⚠️ No quality assessment found for task {completed_task_id} - proceeding with achievement extraction")
            
            # Use robust achievement extraction (only if quality gates passed)
            achievements = await deliverable_achievement_mapper.extract_achievements_robust(
                task_result, task_name
            )
            
            if not achievements:
                logger.debug(f"No achievements extracted from task {completed_task_id}")
                return
            
            logger.info(f"✅ Extracted {len(achievements)} achievements from task {completed_task_id}: {achievements}")
            
            # Map achievements to goals and update progress
            goal_updates = await deliverable_achievement_mapper.map_achievements_to_goals(
                workspace_id, achievements
            )
            
            if goal_updates:
                logger.info(f"🎯 Achievement mapping resulted in {len(goal_updates)} goal updates: {goal_updates}")
                
                # Check if any goals are now ready for deliverable creation
                for goal_update in goal_updates:
                    goal_id = goal_update.get("goal_id")
                    new_progress = goal_update.get("new_progress", 0)
                    
                    # 🎯 PRIORITY 3.2: Real-time goal achievement validation
                    try:
                        from utils.goal_achievement_monitor import goal_achievement_monitor
                        achievement_validation = await goal_achievement_monitor.validate_goal_achievement_post_completion(
                            workspace_id, goal_id, completed_task_id
                        )
                        logger.info(f"🎯 Goal achievement validation: {achievement_validation['overall_status']} for goal {goal_id}")
                    except Exception as monitor_error:
                        logger.error(f"Error in goal achievement monitoring: {monitor_error}")
                    
                    # If goal reached high completion, trigger immediate deliverable check
                    if new_progress >= 70:  # 70% threshold for immediate deliverable creation
                        logger.info(f"🚀 Goal {goal_id} reached {new_progress}% - triggering immediate deliverable creation")
                        
                        # Check if deliverable should be created immediately
                        await self._check_immediate_deliverable_creation(workspace_id, goal_id, new_progress)
            else:
                logger.debug(f"No goal updates from achievement mapping for task {completed_task_id}")
                
        except Exception as e:
            logger.error(f"Error extracting achievements from task {completed_task_id}: {e}")
    
    async def _check_immediate_deliverable_creation(self, workspace_id: str, goal_id: str, progress: float):
        """Check if a specific goal should trigger immediate deliverable creation"""
        try:
            # Lower threshold for immediate deliverable creation
            immediate_threshold = float(os.getenv("IMMEDIATE_DELIVERABLE_THRESHOLD", "70"))
            
            if progress >= immediate_threshold:
                logger.info(f"🎯 Goal {goal_id} at {progress}% triggers immediate deliverable creation")
                
                # Import and trigger deliverable creation for this specific goal
                try:
                    from deliverable_system.unified_deliverable_engine import IntelligentDeliverableAggregator
                    aggregator = IntelligentDeliverableAggregator()
                    
                    # Create deliverable context for this specific goal
                    deliverable_context = {
                        "trigger_goal_id": goal_id,
                        "trigger_progress": progress,
                        "immediate_creation": True,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    result = await aggregator.check_and_create_final_deliverable(workspace_id)
                    logger.info(f"📦 Immediate deliverable creation result: {result}")
                    
                except Exception as deliverable_error:
                    logger.error(f"Error in immediate deliverable creation: {deliverable_error}")
                    
        except Exception as e:
            logger.error(f"Error checking immediate deliverable creation: {e}")
    
    async def _analyze_tasks_business_content(self, tasks: List[Dict]) -> List[Dict]:
        """
        🎯 Analyze business content quality across completed tasks
        
        Rispetta PILLAR 2 (Universal Business Domains) - works across all industries.
        """
        try:
            business_content_tasks = []
            
            for task in tasks:
                task_analysis = {
                    "task_id": task.get("id"),
                    "task_name": task.get("name", ""),
                    "business_value_score": 0.0,
                    "content_type": "unknown",
                    "has_business_content": False,
                    "content_summary": ""
                }
                
                result = task.get("result", {}) or {}
                
                # Analyze detailed results for business content
                if result.get("detailed_results_json"):
                    try:
                        detailed = json.loads(result["detailed_results_json"]) if isinstance(result["detailed_results_json"], str) else result["detailed_results_json"]
                        
                        # Check for rendered content (high business value)
                        if detailed.get("rendered_html"):
                            task_analysis["business_value_score"] += 40.0
                            task_analysis["content_type"] = "rendered_html"
                            task_analysis["has_business_content"] = True
                            task_analysis["content_summary"] = f"Rendered HTML content ({len(detailed['rendered_html'])} chars)"
                        
                        # Check for structured content
                        if detailed.get("structured_content"):
                            task_analysis["business_value_score"] += 30.0
                            if task_analysis["content_type"] == "unknown":
                                task_analysis["content_type"] = "structured_content"
                            task_analysis["has_business_content"] = True
                            
                        # Check for business deliverables
                        if detailed.get("deliverable_content") or detailed.get("business_content"):
                            task_analysis["business_value_score"] += 25.0
                            task_analysis["has_business_content"] = True
                            
                    except (json.JSONDecodeError, TypeError):
                        pass
                
                # Analyze task result summary
                summary = result.get("summary", "")
                if summary:
                    if any(phrase in summary.lower() for phrase in [
                        "document created", "content generated", "strategy developed",
                        "analysis completed", "deliverable produced", "template created"
                    ]):
                        task_analysis["business_value_score"] += 20.0
                        task_analysis["has_business_content"] = True
                    elif "sub-task" in summary.lower():
                        task_analysis["business_value_score"] = max(5.0, task_analysis["business_value_score"])
                        task_analysis["content_summary"] = "Sub-task creation (low business value)"
                
                # Cap the score at 100
                task_analysis["business_value_score"] = min(100.0, task_analysis["business_value_score"])
                
                business_content_tasks.append(task_analysis)
            
            # Sort by business value score
            business_content_tasks.sort(key=lambda x: x["business_value_score"], reverse=True)
            
            logger.debug(f"📊 Business content analysis: {len([t for t in business_content_tasks if t['has_business_content']])} high-value tasks out of {len(tasks)} total")
            
            return business_content_tasks
            
        except Exception as e:
            logger.error(f"Error analyzing tasks business content: {e}")
            return []

    # 🤖 AI-DRIVEN PRIORITY METHODS

    async def _calculate_ai_driven_base_priority(self, task_data: Dict, context_data: Dict, workspace_id: str) -> int:
        """
        🤖 FULLY AI-DRIVEN: Calculate base priority using AI understanding of task context
        """
        try:
            import openai
            import os
            import json
            
            # Check if AI priority is enabled
            enable_ai_priority = os.getenv("ENABLE_AI_TASK_PRIORITY", "true").lower() == "true"
            if not enable_ai_priority:
                # Fallback to simple mapping
                priority_field = task_data.get("priority", "medium").lower()
                return {"high": 300, "medium": 100, "low": 50}.get(priority_field, 100)
            
            # Prepare context for AI analysis
            task_context = {
                "name": task_data.get("name", ""),
                "description": task_data.get("description", ""),
                "priority_field": task_data.get("priority", "medium"),
                "goal_id": task_data.get("goal_id"),
                "creation_type": context_data.get("creation_type", "") if context_data else "",
                "delegation_depth": context_data.get("delegation_depth", 0) if context_data else 0,
                "project_phase": context_data.get("project_phase", "") if context_data else "",
                "has_agent_assignment": bool(task_data.get("agent_id")),
                "needs_role_assignment": bool(task_data.get("assigned_to_role") and not task_data.get("agent_id"))
            }
            
            prompt = f"""
Analyze this task and determine its priority score (1-1000):

Task Context:
{json.dumps(task_context, indent=2)}

Consider:
1. Business impact and urgency of the task
2. Dependencies and blocking potential
3. Project phase criticality (FINALIZATION = highest)
4. Resource assignment urgency
5. Task complexity and effort required

Priority Guidelines:
- 1-100: Low priority, routine tasks
- 101-300: Medium priority, standard work
- 301-500: High priority, important business impact
- 501-800: Critical priority, blocking/urgent
- 801-1000: Emergency priority, project-critical

Return ONLY a JSON object:
{{"priority_score": <number>, "reasoning": "<brief explanation>"}}
"""

            openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert project manager who understands task prioritization in business contexts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=300
            )
            
            ai_response = json.loads(response.choices[0].message.content.strip())
            priority_score = int(ai_response.get("priority_score", 100))
            reasoning = ai_response.get("reasoning", "AI analysis")
            
            # Ensure reasonable bounds
            priority_score = max(1, min(priority_score, 1000))
            
            logger.info(f"🤖 AI Priority: {priority_score} for '{task_data.get('name', 'Unknown')[:30]}' - {reasoning}")
            
            return priority_score
            
        except Exception as e:
            logger.error(f"Error in AI priority calculation: {e}")
            # Fallback to original logic
            priority_field = task_data.get("priority", "medium").lower()
            return {"high": 300, "medium": 100, "low": 50}.get(priority_field, 100)

    async def _calculate_ai_priority_enhancements(self, base_priority: int, task_data: Dict, context_data: Dict, workspace_id: str) -> int:
        """
        🤖 AI-DRIVEN: Calculate priority enhancements using AI analysis
        """
        try:
            import os
            from datetime import datetime
            
            # Simple enhancements that don't need AI
            final_priority = base_priority
            
            # Time-based boost (keep simple logic for performance)
            created_at = task_data.get("created_at")
            if created_at:
                try:
                    if isinstance(created_at, str):
                        created_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    else:
                        created_time = created_at
                    
                    task_age_hours = (datetime.now(created_time.tzinfo) - created_time).total_seconds() / 3600
                    
                    # AI-driven time boost calculation
                    if task_age_hours > 1:  # Reduced threshold
                        # Dynamic time boost based on urgency
                        enable_ai_urgency = os.getenv("ENABLE_AI_URGENCY_BOOST", "true").lower() == "true"
                        if enable_ai_urgency:
                            urgency_boost = await self._calculate_ai_urgency_boost(task_data, task_age_hours)
                        else:
                            urgency_boost = min(int(task_age_hours * 3), 80)  # Reduced multiplier
                        
                        final_priority += urgency_boost
                
                except Exception as e:
                    logger.debug(f"Error calculating task age: {e}")
            
            # Assignment boost (simple logic)
            if not task_data.get("agent_id") and task_data.get("assigned_to_role"):
                final_priority += 150  # Reduced from 200
            elif task_data.get("agent_id"):
                final_priority += 30  # Reduced from 50
            
            return final_priority
            
        except Exception as e:
            logger.error(f"Error in AI priority enhancements: {e}")
            return base_priority

    async def _calculate_ai_urgency_boost(self, task_data: Dict, task_age_hours: float) -> int:
        """
        🤖 AI-DRIVEN: Calculate urgency boost based on task aging and context
        """
        try:
            import openai
            import os
            import json
            
            task_name = task_data.get("name", "")
            task_description = task_data.get("description", "")
            
            prompt = f"""
Analyze this aging task and determine urgency boost (0-200):

Task: "{task_name}"
Description: "{task_description}"
Age: {task_age_hours:.1f} hours

Consider:
1. Is this task time-sensitive by nature?
2. Does aging significantly impact business value?
3. Could this task be blocking other work?
4. Is the delay acceptable for this type of task?

Return ONLY a number between 0-200 representing urgency boost.
"""

            openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You understand task urgency patterns in business projects."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=50
            )
            
            urgency_boost = int(response.choices[0].message.content.strip())
            urgency_boost = max(0, min(urgency_boost, 200))
            
            return urgency_boost
            
        except Exception as e:
            logger.debug(f"Error in AI urgency calculation: {e}")
            # Fallback to simple calculation
            return min(int(task_age_hours * 3), 80)

    async def _find_matching_asset_requirement(self, task_data: Dict[str, Any], asset_requirements: List[Any]) -> Optional[Any]:
        """Find the best matching asset requirement for a completed task"""
        try:
            task_description = task_data.get("description", "")
            task_name = task_data.get("name", "")
            task_context = f"{task_name} {task_description}".lower()
            
            best_match = None
            best_score = 0
            
            for requirement in asset_requirements:
                # Simple keyword matching - could be enhanced with AI
                requirement_text = f"{requirement.asset_name} {requirement.description}".lower()
                
                # Calculate similarity score
                score = 0
                requirement_words = set(requirement_text.split())
                task_words = set(task_context.split())
                
                common_words = requirement_words.intersection(task_words)
                if common_words:
                    score = len(common_words) / max(len(requirement_words), len(task_words))
                
                if score > best_score and score > 0.2:  # Minimum similarity threshold
                    best_score = score
                    best_match = requirement
            
            return best_match
            
        except Exception as e:
            logger.error(f"Error finding matching asset requirement: {e}")
            return None
    
    def _convert_task_to_enhanced_model(self, task_data: Dict[str, Any]):
        """Convert task dict to enhanced task model for asset processing"""
        try:
            # This is a simplified conversion - might need enhancement based on models
            from models import EnhancedTask
            
            enhanced_data = {
                "id": task_data.get("id"),
                "workspace_id": task_data.get("workspace_id"),
                "name": task_data.get("name", ""),
                "description": task_data.get("description", ""),
                "output": task_data.get("result") or task_data.get("output"),
                "status": task_data.get("status"),
                "created_at": task_data.get("created_at"),
                "updated_at": task_data.get("updated_at")
            }
            
            return EnhancedTask(**enhanced_data)
            
        except Exception as e:
            logger.error(f"Error converting task to enhanced model: {e}")
            return None
    
    async def _trigger_asset_quality_validation(self, artifact):
        """Trigger AI quality validation for the created artifact"""
        try:
            if asset_quality_engine:
                logger.info(f"🛡️ Triggering quality validation for artifact: {artifact.artifact_name}")
                
                # Trigger asynchronous quality validation
                validation_result = await asset_quality_engine.validate_artifact_quality(artifact)
                
                logger.info(f"✅ Quality validation completed with score: {validation_result.get('score', 0)}")
                
        except Exception as e:
            logger.error(f"Asset quality validation failed: {e}")
    
    async def _update_goal_progress_from_asset(self, workspace_id: str, artifact, requirement):
        """Update goal progress based on asset completion"""
        try:
            # Get the goal associated with this requirement
            goal_id = requirement.goal_id
            
            # Get current goal data
            supabase = get_supabase_client()
            goal_response = supabase.table("workspace_goals").select("*").eq("id", str(goal_id)).execute()
            
            if goal_response.data:
                goal_data = goal_response.data[0]
                
                # Recalculate asset completion rate for this goal
                if _initialize_asset_system():
                    goal_requirements = await asset_db_manager.get_workspace_asset_requirements(workspace_id)
                    goal_artifacts = []
                    
                    for req in goal_requirements:
                        req_artifacts = await asset_db_manager.get_artifacts_for_requirement(req.id)
                        goal_artifacts.extend(req_artifacts)
                else:
                    goal_requirements = []
                    goal_artifacts = []
                
                total_requirements = len(goal_requirements)
                approved_artifacts = len([a for a in goal_artifacts if a.status == "approved"])
                
                asset_completion_rate = (approved_artifacts / total_requirements) if total_requirements > 0 else 0.0
                
                # Update goal with new asset completion rate
                supabase.table("workspace_goals").update({
                    "asset_completion_rate": asset_completion_rate,
                    "updated_at": datetime.now().isoformat()
                }).eq("id", str(goal_id)).execute()
                
                logger.info(f"📊 Updated goal {goal_id} asset completion rate to {asset_completion_rate:.2%}")
                
        except Exception as e:
            logger.error(f"Failed to update goal progress from asset: {e}")

    async def _trigger_goal_validation_for_issues(self, issue_type: str):
        """
        🚨 TRIGGER IMMEDIATE GOAL VALIDATION: Activate goal validation when circuit breaker detects issues
        
        This method integrates with the automated goal monitor to create corrective tasks
        when the executor detects system-wide problems (like task creation runaway, failure spikes, etc.)
        """
        try:
            logger.warning(f"🚨 TRIGGERING GOAL VALIDATION due to issue: {issue_type}")
            
            # Import goal monitor
            try:
                from automated_goal_monitor import AutomatedGoalMonitor
                goal_monitor = AutomatedGoalMonitor()
            except ImportError:
                logger.error("❌ AutomatedGoalMonitor not available for validation trigger")
                return
            
            # Get all active workspaces affected by the issue
            try:
                active_workspace_ids = await get_active_workspaces()
                if not active_workspace_ids:
                    logger.info("No active workspaces found for goal validation trigger")
                    return
                
                validation_results = []
                
                for workspace_id in active_workspace_ids:
                    try:
                        # Trigger immediate validation for each workspace
                        result = await goal_monitor.trigger_immediate_validation(
                            workspace_id, 
                            reason=f"executor_issue_{issue_type}"
                        )
                        
                        if result and result.get("success"):
                            validation_results.append({
                                "workspace_id": workspace_id,
                                "corrective_tasks_created": result.get("corrective_tasks_created", 0),
                                "corrective_tasks_executed": result.get("corrective_tasks_executed", 0)
                            })
                            
                            logger.warning(f"⚡ Goal validation triggered for {workspace_id}: "
                                        f"{result.get('corrective_tasks_created', 0)} tasks created, "
                                        f"{result.get('corrective_tasks_executed', 0)} tasks executed")
                        else:
                            logger.info(f"✅ No corrective action needed for workspace {workspace_id}")
                            
                    except Exception as ws_error:
                        logger.error(f"Failed to trigger goal validation for workspace {workspace_id}: {ws_error}")
                        continue
                
                # Log summary
                total_corrective_tasks = sum(r["corrective_tasks_created"] for r in validation_results)
                total_executed_tasks = sum(r["corrective_tasks_executed"] for r in validation_results)
                
                if validation_results:
                    logger.warning(f"🎯 GOAL VALIDATION SUMMARY ({issue_type}): "
                                f"{len(validation_results)} workspaces processed, "
                                f"{total_corrective_tasks} corrective tasks created, "
                                f"{total_executed_tasks} tasks executed immediately")
                else:
                    logger.info(f"🎯 GOAL VALIDATION COMPLETE ({issue_type}): No corrective actions needed")
                
                # Log the trigger event
                self.execution_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "event": "goal_validation_triggered",
                    "issue_type": issue_type,
                    "workspaces_processed": len(active_workspace_ids),
                    "corrective_tasks_created": total_corrective_tasks,
                    "corrective_tasks_executed": total_executed_tasks
                })
                
            except Exception as e:
                logger.error(f"Failed to get active workspaces for goal validation: {e}")
                
        except Exception as e:
            logger.error(f"Critical error in _trigger_goal_validation_for_issues: {e}")
    
    async def _retrieve_quality_patterns_for_task(self, task_dict: Dict[str, Any], workspace_id: str) -> Optional[Dict[str, Any]]:
        """
        🎯 QUALITY PATTERN RETRIEVAL: Get learned quality patterns for specific task
        
        Retrieves quality patterns from workspace memory to guide task execution
        and prevent known quality issues.
        """
        try:
            from uuid import UUID
            from workspace_memory import workspace_memory
            
            # Extract task type and agent info for pattern matching
            task_type = task_dict.get('task_type', 'unknown')
            agent_id = task_dict.get('agent_id', 'unknown')
            
            # Retrieve quality patterns for this task type
            quality_patterns = await workspace_memory.get_quality_patterns_for_task_type(
                workspace_id=UUID(workspace_id),
                task_type=task_type,
                agent_id=str(agent_id) if agent_id else None
            )
            
            return quality_patterns
            
        except Exception as e:
            logger.error(f"Failed to retrieve quality patterns for task: {e}")
            return None
    
    async def _inject_quality_guidance(self, task_id: str, quality_patterns: Dict[str, Any]) -> None:
        """
        🎯 QUALITY GUIDANCE INJECTION: Inject quality patterns into task metadata
        
        Updates task metadata with quality guidance so agents can access
        learned patterns during task execution.
        """
        try:
            from database import supabase
            
            # Build quality guidance context
            guidance_context = {
                "quality_guidance": {
                    "best_practices": quality_patterns.get("best_practices", []),
                    "success_patterns": quality_patterns.get("success_patterns", []),
                    "failure_patterns": quality_patterns.get("failure_patterns", []),
                    "common_issues": quality_patterns.get("common_issues", []),
                    "recommendations": quality_patterns.get("recommendations", []),
                    "quality_statistics": quality_patterns.get("quality_statistics", {}),
                    "injected_at": datetime.now().isoformat()
                }
            }
            
            # Update task metadata with quality guidance
            update_result = supabase.table("tasks").update({
                "metadata": guidance_context
            }).eq("id", task_id).execute()
            
            if update_result.data:
                logger.debug(f"✅ Quality guidance injected into task {task_id} metadata")
            else:
                logger.warning(f"⚠️ Failed to inject quality guidance into task {task_id}")
                
        except Exception as e:
            logger.error(f"Failed to inject quality guidance for task {task_id}: {e}")

def set_global_auto_generation(enabled: bool) -> Dict[str, Any]:
    """Abilita/disabilita auto-generation globalmente"""
    task_executor.auto_generation_enabled = enabled
    status_msg = "ENABLED" if enabled else "DISABLED"
    logger.info(f"Global auto-generation is now {status_msg}")
    return {
        "success": True,
        "message": f"Global auto-generation is {status_msg}",
        "current_status": task_executor.auto_generation_enabled
    }

# Funzioni di backward compatibility
def get_auto_generation_stats() -> Dict[str, Any]:
    """Backward compatibility: restituisce solo la sezione auto_generation_activity"""
    return task_executor.get_detailed_stats().get("auto_generation_activity", {})

def get_runaway_protection_status() -> Dict[str, Any]:
    """Backward compatibility: restituisce solo la sezione runaway_protection_status"""
    return task_executor.get_detailed_stats().get("runaway_protection_status", {})


# Helper function to get workspace settings
async def get_workspace_execution_settings(workspace_id: str) -> Dict[str, Any]:
    """Get workspace-specific execution settings with fallbacks"""
    try:
        project_settings = get_project_settings(workspace_id)
        return await project_settings.get_all_settings()
    except Exception as e:
        logger.warning(f"Failed to load workspace settings for {workspace_id}: {e}")
        # Return default settings
        return {
            'quality_threshold': 85.0,
            'max_iterations': 3,
            'max_concurrent_tasks': 3,
            'task_timeout': 150,
            'enable_quality_assurance': True,
            'deliverable_threshold': 50.0,
            'max_deliverables': 3,
            'max_budget': 10.0
        }