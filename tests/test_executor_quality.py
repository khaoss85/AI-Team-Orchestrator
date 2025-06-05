import sys
import types
import asyncio
import importlib


def _setup_executor_with_stubs():
    # --- stub models module ---
    class _EnumMember:
        def __init__(self, value):
            self.value = value

    class TaskStatus:
        PENDING = _EnumMember("pending")
        IN_PROGRESS = _EnumMember("in_progress")
        COMPLETED = _EnumMember("completed")
        FAILED = _EnumMember("failed")
        CANCELED = _EnumMember("canceled")
        TIMED_OUT = _EnumMember("timed_out")
        STALE = _EnumMember("stale")

    class AgentStatus:
        ACTIVE = _EnumMember("active")

    class WorkspaceStatus:
        CREATED = _EnumMember("created")
        ACTIVE = _EnumMember("active")
        NEEDS_INTERVENTION = _EnumMember("needs_intervention")
        ERROR = _EnumMember("error")

    models = types.ModuleType("models")
    models.TaskStatus = TaskStatus
    models.Task = dict
    models.AgentStatus = AgentStatus
    models.WorkspaceStatus = WorkspaceStatus
    models.Agent = dict
    sys.modules["models"] = models

    # --- stub database module ---
    async def _get_active_workspaces():
        return ["ws1"]

    async def _dummy_async(*args, **kwargs):
        return []

    async def _dummy_dict(*args, **kwargs):
        return {}

    db = types.ModuleType("database")
    db.list_tasks = _dummy_async
    db.update_task_status = _dummy_async
    db.get_workspace = _dummy_dict
    db.get_agent = _dummy_dict
    db.list_agents = _dummy_async
    db.create_task = _dummy_dict
    db.get_active_workspaces = _get_active_workspaces
    db.get_workspaces_with_pending_tasks = _dummy_async
    db.update_workspace_status = _dummy_async
    db.get_task = _dummy_dict
    sys.modules["database"] = db

    # --- stub improvement_loop module ---
    improvement = types.ModuleType("improvement_loop")
    improvement.controlled_iteration = _dummy_async
    improvement.refresh_dependencies = _dummy_async
    sys.modules["improvement_loop"] = improvement

    # --- stub ai_agents.manager module ---
    agents_manager = types.ModuleType("ai_agents.manager")
    class AgentManager:
        pass
    agents_manager.AgentManager = AgentManager
    sys.modules["ai_agents.manager"] = agents_manager

    # --- stub task_analyzer module ---
    task_analyzer = types.ModuleType("task_analyzer")
    class EnhancedTaskExecutor:
        pass
    def get_enhanced_task_executor():
        return EnhancedTaskExecutor()
    task_analyzer.EnhancedTaskExecutor = EnhancedTaskExecutor
    task_analyzer.get_enhanced_task_executor = get_enhanced_task_executor
    sys.modules["task_analyzer"] = task_analyzer

    # --- stub quality system config module ---
    quality_config = types.ModuleType("config.quality_system_config")
    class QualitySystemConfig:
        ENABLE_QUALITY_METRICS_COLLECTION = False
        INTEGRATE_WITH_EXISTING_DELIVERABLE_SYSTEM = True
        FALLBACK_TO_STANDARD_SYSTEM_ON_ERROR = True
    quality_config.QualitySystemConfig = QualitySystemConfig
    sys.modules["config.quality_system_config"] = quality_config

    # --- stub deliverable_aggregator module ---
    deliverable = types.ModuleType("deliverable_aggregator")
    calls = []
    async def check_and_create_final_deliverable(workspace_id):
        calls.append(workspace_id)
        return "d1"
    deliverable.check_and_create_final_deliverable = check_and_create_final_deliverable
    sys.modules["deliverable_aggregator"] = deliverable
    sys.modules["backend.deliverable_aggregator"] = deliverable

    sys.path.insert(0, "backend")
    if "executor" in sys.modules:
        del sys.modules["executor"]
    executor = importlib.import_module("executor")
    return executor, calls


def test_quality_deliverable_no_unboundlocal():
    executor, calls = _setup_executor_with_stubs()

    class Dummy:
        def __init__(self):
            self.last_quality_check = {}
            self.quality_check_interval = 0
        def _should_check_workspace_for_quality(self, ws):
            return True

    asyncio.run(executor.QualityEnhancedTaskExecutor._check_quality_enhanced_deliverables(Dummy()))
    assert calls == ["ws1"]
