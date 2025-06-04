import sys
import types
import pytest
import asyncio

# Create stub modules before importing the router
executor_stub = types.ModuleType('executor')
executor_stub.task_executor = object()
sys.modules['executor'] = executor_stub

# Minimal database stub with async list_tasks
async def _dummy_list_tasks(*args, **kwargs):
    return []

database_stub = types.ModuleType('database')
database_stub.list_tasks = _dummy_list_tasks
database_stub.get_workspace = lambda x: {}
database_stub.list_agents = lambda x: []
database_stub.update_task_status = lambda *a, **k: None
sys.modules['database'] = database_stub

sys.path.insert(0, 'backend')
from routes import monitoring


def test_get_workspace_tasks_counts(monkeypatch):
    async def fake_list_tasks(workspace_id, status=None, agent_id=None, asset_only=False, limit=None, offset=0):
        return [
            {"id": "1", "status": "completed", "name": "task", "context_data": {"asset_production": True}},
            {"id": "2", "status": "pending", "name": "task2"},
            {"id": "3", "status": "failed", "name": "produce asset", "context_data": {"asset_oriented_task": True}},
        ]

    monkeypatch.setattr(monitoring, "list_tasks", fake_list_tasks)
    from uuid import UUID
    resp = asyncio.run(monitoring.get_workspace_tasks(UUID("12345678-1234-5678-1234-567812345678")))
    assert resp.total_count == 3
    assert resp.completed_count == 1
    assert resp.pending_count == 1
    assert resp.failed_count == 1
    assert resp.asset_tasks_count == 2
    assert isinstance(resp.tasks, list)


def test_get_workspace_tasks_query_params(monkeypatch):
    captured = {}

    async def fake_list_tasks(workspace_id, status=None, agent_id=None, asset_only=False, limit=None, offset=0):
        captured.update({
            "workspace_id": workspace_id,
            "status": status,
            "agent_id": agent_id,
            "asset_only": asset_only,
            "limit": limit,
            "offset": offset,
        })
        return []

    monkeypatch.setattr(monitoring, "list_tasks", fake_list_tasks)
    from uuid import UUID
    asyncio.run(monitoring.get_workspace_tasks(
        UUID("12345678-1234-5678-1234-567812345678"),
        status="completed",
        agent_id="42",
        asset_only=True,
        limit=5,
        offset=2,
    ))
    assert captured["status"] == "completed"
    assert captured["agent_id"] == "42"
    assert captured["asset_only"] is True
    assert captured["limit"] == 5
    assert captured["offset"] == 2
