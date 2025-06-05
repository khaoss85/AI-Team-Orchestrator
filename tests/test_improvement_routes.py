import sys
import types
import asyncio
import pytest

# Create stub modules before importing the router
improvement_loop_stub = types.ModuleType("improvement_loop")


async def _checkpoint_output(tid, payload):
    return True


async def _qa_gate(tid, payload):
    return True


async def _close_loop(tid):
    pass


improvement_loop_stub.checkpoint_output = _checkpoint_output
improvement_loop_stub.qa_gate = _qa_gate
improvement_loop_stub.close_loop = _close_loop
improvement_loop_stub.DEFAULT_FEEDBACK_TIMEOUT = 10
sys.modules["improvement_loop"] = improvement_loop_stub

# database stub
database_stub = types.ModuleType("database")


async def _get_task(tid):
    return {"id": tid}


database_stub.get_task = _get_task
sys.modules["database"] = database_stub

sys.path.insert(0, "backend")
from routes import improvement


def test_qa_route_forwarding(monkeypatch):
    captured = {}

    async def fake_gate(tid, payload):
        captured["tid"] = tid
        captured["payload"] = payload
        return False

    monkeypatch.setattr(improvement, "qa_gate", fake_gate)
    res = asyncio.run(improvement.qa_improvement("1", {"foo": "bar"}))
    assert captured["tid"] == "1"
    assert captured["payload"] == {"foo": "bar"}
    assert res["approved"] is False


def test_qa_route_not_found(monkeypatch):
    async def no_task(tid):
        return None

    monkeypatch.setattr(improvement, "get_task", no_task)
    with pytest.raises(improvement.HTTPException) as exc:
        asyncio.run(improvement.qa_improvement("missing", {}))
    assert exc.value.status_code == 404
