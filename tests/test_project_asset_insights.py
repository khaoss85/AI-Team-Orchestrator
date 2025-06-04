import sys
import types
import asyncio

# Stub modules before import

# executor stub
executor_stub = types.ModuleType('executor')
executor_stub.task_executor = object()
sys.modules['executor'] = executor_stub

# director stub
director_stub = types.ModuleType('ai_agents.director')
director_stub.DirectorAgent = object
sys.modules['ai_agents.director'] = director_stub

# database stub
async def fake_list_tasks(workspace_id):
    return [
        {
            'id': '1',
            'name': 'Create Instagram Content Calendar',
            'status': 'completed',
            'context_data': {'asset_production': True, 'asset_type': 'content_calendar'},
            'agent_role': 'Content Specialist',
        }
    ]

database_stub = types.ModuleType('database')
database_stub.list_tasks = fake_list_tasks
database_stub.get_workspace = lambda x: {}
database_stub.list_agents = lambda x: []
database_stub.get_agent = lambda x: {}
database_stub.update_agent_status = lambda *a, **k: None
database_stub.update_task_status = lambda *a, **k: None
database_stub.create_task = lambda *a, **k: None
sys.modules['database'] = database_stub

# requirement analyzer stub
class DummyReq:
    deliverable_category = 'marketing'
    primary_assets_needed = [
        types.SimpleNamespace(asset_type='content_calendar'),
        types.SimpleNamespace(asset_type='audience_analysis'),
        types.SimpleNamespace(asset_type='contact_database'),
    ]

class DummyAnalyzer:
    async def analyze_deliverable_requirements(self, workspace_id, force_refresh=False):
        return DummyReq()

req_mod = types.ModuleType('deliverable_system.requirements_analyzer')
req_mod.DeliverableRequirementsAnalyzer = DummyAnalyzer
sys.modules['deliverable_system.requirements_analyzer'] = req_mod

# schema generator stub
class DummySchema:
    automation_ready = True
    validation_rules = ['a', 'b', 'c']
    schema_definition = {'posts': [], 'posting_schedule': {}, 'performance_targets': {}}

class DummyGenerator:
    async def generate_asset_schemas(self, requirements):
        return {'content_calendar': DummySchema()}

schema_mod = types.ModuleType('deliverable_system.schema_generator')
schema_mod.AssetSchemaGenerator = DummyGenerator
sys.modules['deliverable_system.schema_generator'] = schema_mod

import importlib, os
base_dir = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(base_dir, '..'))
sys.path.insert(0, os.path.join(base_dir, '..', 'backend'))
sys.modules['models'] = importlib.import_module('backend.models')
from routes import project_insights


def test_get_asset_insights():
    from uuid import UUID
    import importlib
    sys.modules['models'] = importlib.import_module('backend.models')
    result = asyncio.run(project_insights.get_asset_insights(UUID('12345678-1234-5678-1234-567812345678')))
    assert result['deliverable_category'] == 'marketing'
    assert result['requirements_analysis']['total_assets_needed'] == 3
    assert result['asset_schemas_available']['content_calendar']['validation_rules_count'] == 3
    assert result['current_asset_tasks'][0]['asset_type'] == 'content_calendar'
    assert 'Create audience_analysis production task' in result['recommendations']
