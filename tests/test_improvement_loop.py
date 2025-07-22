import types
import asyncio

# Stub database functions
stub_db = types.SimpleNamespace()
async def _get_task(tid):
    return {"id": tid, "workspace_id": "ws1", "iteration_count": 0, "name": "t"}

async def _update_fields(tid, fields):
    return fields

async def _update_status(*a, **k):
    return None

async def _list_tasks(ws):
    # Simula la nuova struttura di dipendenze
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {'depends_on_task_id': '1'}
        ]
        return [{"id": "2"}]

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
import importlib
import pathlib
root_dir = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))
sys.modules['models'] = importlib.import_module('backend.models')

import improvement_loop
from improvement_loop import (
    controlled_iteration,
    refresh_dependencies,
    checkpoint_output,
    qa_gate,
    TaskStatus,
)


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


def test_checkpoint_output_timeout(monkeypatch):
    calls = []

    async def no_response_request(*a, **k):
        # Do not invoke callback to simulate missing feedback
        return "1"

    async def fake_update_status(task_id, status):
        calls.append((task_id, status))

    monkeypatch.setattr(improvement_loop.human_feedback_manager, 'request_feedback', no_response_request)
    monkeypatch.setattr(improvement_loop, 'update_task_status', fake_update_status)
    result = asyncio.run(checkpoint_output('1', {}, timeout=0.01))
    assert result is False
    assert calls and calls[0][1] == TaskStatus.TIMED_OUT.value


def test_qa_gate_timeout(monkeypatch):
    calls = []

    async def no_response_request(*a, **k):
        return "1"

    async def fake_update_status(task_id, status):
        calls.append((task_id, status))

    monkeypatch.setattr(improvement_loop.human_feedback_manager, 'request_feedback', no_response_request)
    monkeypatch.setattr(improvement_loop, 'update_task_status', fake_update_status)
    result = asyncio.run(qa_gate('1', {}, timeout=0.01))
    assert result is False
    assert calls and calls[0][1] == TaskStatus.TIMED_OUT.value
