import sys
import types
import json
from uuid import uuid4

import pytest

from pathlib import Path
root_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_path))
sys.path.insert(0, str(root_path / "backend"))
print('ROOT_PATH', root_path)
print('SYS_PATH', sys.path[:4])

# Prepare minimal stubs so specialist module can be imported
stub_db = types.ModuleType("database")
for name in [
    "update_agent_status",
    "update_task_status",
    "create_task",
    "list_agents",
    "list_tasks",
    "get_agent",
]:
    setattr(stub_db, name, lambda *a, **k: None)

sys.modules["database"] = stub_db

import os
os.environ.setdefault("OPENAI_API_KEY", "x")
os.environ.setdefault("SUPABASE_URL", "http://example.com")
os.environ.setdefault("SUPABASE_KEY", "key")

import importlib


def test_json_loads_missing_task_id_parsed():
    specialist = importlib.import_module("backend.ai_agents.specialist")
    task_id = uuid4()
    raw = '{"status": "completed", "summary": "done"}'
    data = json.loads(raw)
    data.setdefault("task_id", str(task_id))
    result = specialist.TaskExecutionOutput.model_validate(data)
    assert result.task_id == str(task_id)


def test_json_fix_missing_task_id_parsed():
    specialist = importlib.import_module("backend.ai_agents.specialist")
    task_id = uuid4()
    raw = '{"status": "completed", "summary": "done"'
    with pytest.raises(json.JSONDecodeError):
        json.loads(raw)
    fixed, _, _ = specialist.parse_llm_json_robust(raw, str(task_id))
    fixed.setdefault("task_id", str(task_id))
    result = specialist.TaskExecutionOutput.model_validate(fixed)
    assert result.task_id == str(task_id)
