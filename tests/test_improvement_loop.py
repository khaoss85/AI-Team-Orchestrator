import types
import asyncio

# Stub database functions
stub_db = types.SimpleNamespace()
async def _get_task(tid):
    return {"id": tid, "workspace_id": "ws1", "iteration_count": 0}

async def _update_fields(tid, fields):
    return fields

async def _update_status(*a, **k):
    return None

async def _list_tasks(ws):
    return [{"id": "2", "depends_on_task_ids": ["1"]}]

async def _create_task(**k):
    return {"id": "new"}

stub_db.get_task = _get_task
stub_db.update_task_fields = _update_fields
stub_db.update_task_status = _update_status
stub_db.list_tasks = _list_tasks
stub_db.create_task = _create_task

# Stub feedback manager
stub_hfm = types.SimpleNamespace()
async def dummy_request(*a, **k):
    cb = k.get("response_callback")
    if cb:
        await cb({}, {"approved": True})
    return "1"
stub_hfm.request_feedback = dummy_request

import sys
sys.modules['database'] = stub_db
sys.modules['human_feedback_manager'] = types.ModuleType('human_feedback_manager')
sys.modules['human_feedback_manager'].human_feedback_manager = stub_hfm
sys.modules['human_feedback_manager'].FeedbackRequestType = types.SimpleNamespace(TASK_APPROVAL='task_approval')

import improvement_loop
from improvement_loop import controlled_iteration, refresh_dependencies


def test_controlled_iteration_limit(monkeypatch):
    async def fake_get_task(tid):
        return {"id": tid, "workspace_id": "ws1", "iteration_count": 1}
    monkeypatch.setattr(improvement_loop, 'get_task', fake_get_task)
    monkeypatch.setattr(improvement_loop, 'update_task_fields', _update_fields)
    result = asyncio.run(controlled_iteration('1', 'ws1', 2))
    assert result

    result2 = asyncio.run(controlled_iteration('1', 'ws1', 1))
    assert not result2


def test_refresh_dependencies(monkeypatch):
    captured = []
    async def fake_update(task_id, status):
        captured.append((task_id, status))
    monkeypatch.setattr(improvement_loop, 'update_task_status', fake_update)
    monkeypatch.setattr(improvement_loop, 'list_tasks', _list_tasks)
    asyncio.run(refresh_dependencies('1'))
    assert captured[0][0] == '2'
