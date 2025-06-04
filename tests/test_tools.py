import asyncio
import json
import sys
import types

# Stub out the database module before importing PMOrchestrationTools
database_stub = types.ModuleType("database")
database_stub.create_task = lambda **k: None
database_stub.list_tasks = lambda *a, **k: []
database_stub.list_agents = lambda *a, **k: []
database_stub.get_agent = lambda *a, **k: {}
sys.modules["database"] = database_stub

sys.path.insert(0, "backend")
import importlib.util
import pathlib

spec = importlib.util.spec_from_file_location(
    "ai_agents.tools", pathlib.Path("backend/ai_agents/tools.py")
)
tools_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools_module)
PMOrchestrationTools = tools_module.PMOrchestrationTools


def test_list_agents_called_once(monkeypatch):
    call_counter = {"count": 0}

    async def fake_list_tasks(*args, **kwargs):
        # Return one parent PM task
        return [
            {
                "id": "pm_task",
                "agent_id": "pm_agent_1",
                "status": "IN_PROGRESS",
                "name": "PM root",
                "context_data": {"project_phase": "PLANNING"},
            }
        ]

    async def fake_list_agents(*args, **kwargs):
        call_counter["count"] += 1
        return [
            {"id": "a1", "name": "TargetBot", "role": "bot", "status": "active"}
        ]

    async def fake_create_task(**kwargs):
        return {"id": "new"}

    async def fake_get_agent(agent_id):
        return {"name": "PM Agent"}

    tools = tools_module
    monkeypatch.setattr(tools, "db_list_tasks", fake_list_tasks)
    monkeypatch.setattr(tools, "db_list_agents", fake_list_agents)
    monkeypatch.setattr(tools, "db_create_task", fake_create_task)
    monkeypatch.setattr(tools, "get_agent", fake_get_agent)

    async def run_tool():
        pm = PMOrchestrationTools("ws1")
        tool = pm.create_and_assign_sub_task_tool()
        params = {
            "task_name": "Task 1",
            "task_description": "a" * 60,
            "target_agent_role": "TargetBot",
            "project_phase": "ANALYSIS",
            "parent_task_id": "pm_task",
        }
        res = await tool.on_invoke_tool(None, json.dumps(params))
        data = json.loads(res)
        assert data["success"]

    asyncio.run(run_tool())
    assert call_counter["count"] == 1

