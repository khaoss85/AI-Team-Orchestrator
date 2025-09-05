# OpenAI Quota Tracking Violations Report

## Total Violations Found: 124


### agents/ (4 violations)

- **venv/lib/python3.13/site-packages/agents/__init__.py** (line 5)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **venv/lib/python3.13/site-packages/agents/_config.py** (line 1)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **.venv/lib/python3.13/site-packages/agents/__init__.py** (line 5)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **.venv/lib/python3.13/site-packages/agents/_config.py** (line 1)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```

### ai_agents/ (7 violations)

- **ai_agents/specialist_sdk_complete.py** (line 675)
  ```python
  client = openai.OpenAI()
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```
- **ai_agents/specialist_pydantic_refactored.py** (line 424)
  ```python
  from openai import OpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```
- **ai_agents/specialist_pydantic_refactored.py** (line 425)
  ```python
  client = OpenAI()
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```
- **ai_agents/conversational_simple.py** (line 1028)
  ```python
  # Create a summarized message for OpenAI (without the large file content)
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```
- **ai_agents/specialist_enhanced.py** (line 524)
  ```python
  client = openai.AsyncOpenAI()
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **ai_agents/director.py** (line 589)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **ai_agents/director.py** (line 590)
  ```python
  openai_client = AsyncOpenAI()
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```

### ai_quality_assurance/ (5 violations)

- **ai_quality_assurance/ai_adaptive_quality_engine.py** (line 28)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **ai_quality_assurance/ai_adaptive_quality_engine.py** (line 42)
  ```python
  self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **ai_quality_assurance/ai_quality_gate_engine.py** (line 13)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **ai_quality_assurance/ai_quality_gate_engine.py** (line 30)
  ```python
  self.openai_client = openai_client or AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **ai_quality_assurance/unified_quality_engine.py** (line 14)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```

### backend/ (15 violations)

- **task_analyzer.py** (line 215)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **task_analyzer.py** (line 216)
  ```python
  openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **task_analyzer.py** (line 2598)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **task_analyzer.py** (line 2599)
  ```python
  openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **AISemanticMapper.py** (line 7)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **AISemanticMapper.py** (line 31)
  ```python
  self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **ai_driven_task_intent_analyzer.py** (line 39)
  ```python
  self.client = openai.AsyncOpenAI()
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **real_task_executor.py** (line 29)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **real_task_executor.py** (line 30)
  ```python
  self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **goal_driven_task_planner.py** (line 49)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **goal_driven_task_planner.py** (line 50)
  ```python
  self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **goal_driven_task_planner.py** (line 743)
  ```python
  client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```
- **goal_driven_task_planner.py** (line 843)
  ```python
  openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```
- **auto_agent_provisioner.py** (line 43)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **auto_agent_provisioner.py** (line 44)
  ```python
  self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```

### chat/ (4 violations)

- **.venv/lib/python3.13/site-packages/openai/resources/beta/chat/completions.py** (line 115)
  ```python
  from openai import OpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```
- **.venv/lib/python3.13/site-packages/openai/resources/beta/chat/completions.py** (line 128)
  ```python
  client = OpenAI()
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```
- **.venv/lib/python3.13/site-packages/openai/resources/beta/chat/completions.py** (line 394)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **.venv/lib/python3.13/site-packages/openai/resources/beta/chat/completions.py** (line 407)
  ```python
  client = AsyncOpenAI()
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```

### completions/ (4 violations)

- **venv/lib/python3.13/site-packages/openai/resources/chat/completions/completions.py** (line 137)
  ```python
  from openai import OpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```
- **venv/lib/python3.13/site-packages/openai/resources/chat/completions/completions.py** (line 150)
  ```python
  client = OpenAI()
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```
- **venv/lib/python3.13/site-packages/openai/resources/chat/completions/completions.py** (line 1504)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **venv/lib/python3.13/site-packages/openai/resources/chat/completions/completions.py** (line 1517)
  ```python
  client = AsyncOpenAI()
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```

### config/ (2 violations)

- **config/quality_system_config.py** (line 133)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **config/quality_system_config.py** (line 134)
  ```python
  openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```

### lib/ (4 violations)

- **venv/lib/python3.13/site-packages/openai/lib/azure.py** (line 89)
  ```python
  class AzureOpenAI(BaseAzureClient[httpx.Client, Stream[Any]], OpenAI):
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```
- **venv/lib/python3.13/site-packages/openai/lib/azure.py** (line 367)
  ```python
  class AsyncAzureOpenAI(BaseAzureClient[httpx.AsyncClient, AsyncStream[Any]], AsyncOpenAI):
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **.venv/lib/python3.13/site-packages/openai/lib/azure.py** (line 89)
  ```python
  class AzureOpenAI(BaseAzureClient[httpx.Client, Stream[Any]], OpenAI):
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```
- **.venv/lib/python3.13/site-packages/openai/lib/azure.py** (line 360)
  ```python
  class AsyncAzureOpenAI(BaseAzureClient[httpx.AsyncClient, AsyncStream[Any]], AsyncOpenAI):
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```

### models/ (26 violations)

- **venv/lib/python3.13/site-packages/agents/models/chatcmpl_helpers.py** (line 3)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **venv/lib/python3.13/site-packages/agents/models/openai_responses.py** (line 294)
  ```python
  self._client = AsyncOpenAI()
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **venv/lib/python3.13/site-packages/agents/models/openai_chatcompletions.py** (line 318)
  ```python
  self._client = AsyncOpenAI()
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **venv/lib/python3.13/site-packages/agents/models/multi_provider.py** (line 3)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **venv/lib/python3.13/site-packages/agents/models/openai_provider.py** (line 4)
  ```python
  from openai import AsyncOpenAI, DefaultAsyncHttpxClient
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **venv/lib/python3.13/site-packages/agents/models/openai_provider.py** (line 68)
  ```python
  # AsyncOpenAI() raises an error if you don't have an API key set.
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **venv/lib/python3.13/site-packages/agents/models/openai_provider.py** (line 71)
  ```python
  self._client = _openai_shared.get_default_openai_client() or AsyncOpenAI(
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **venv/lib/python3.13/site-packages/agents/models/_openai_shared.py** (line 3)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **venv/lib/python3.13/site-packages/agents/voice/models/openai_model_provider.py** (line 4)
  ```python
  from openai import AsyncOpenAI, DefaultAsyncHttpxClient
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **venv/lib/python3.13/site-packages/agents/voice/models/openai_model_provider.py** (line 64)
  ```python
  # AsyncOpenAI() raises an error if you don't have an API key set.
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **venv/lib/python3.13/site-packages/agents/voice/models/openai_model_provider.py** (line 67)
  ```python
  self._client = _openai_shared.get_default_openai_client() or AsyncOpenAI(
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **venv/lib/python3.13/site-packages/agents/voice/models/openai_tts.py** (line 4)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **venv/lib/python3.13/site-packages/agents/voice/models/openai_stt.py** (line 11)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **.venv/lib/python3.13/site-packages/agents/models/chatcmpl_helpers.py** (line 3)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **.venv/lib/python3.13/site-packages/agents/models/openai_responses.py** (line 273)
  ```python
  self._client = AsyncOpenAI()
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **.venv/lib/python3.13/site-packages/agents/models/openai_chatcompletions.py** (line 308)
  ```python
  self._client = AsyncOpenAI()
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **.venv/lib/python3.13/site-packages/agents/models/multi_provider.py** (line 3)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **.venv/lib/python3.13/site-packages/agents/models/openai_provider.py** (line 4)
  ```python
  from openai import AsyncOpenAI, DefaultAsyncHttpxClient
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **.venv/lib/python3.13/site-packages/agents/models/openai_provider.py** (line 68)
  ```python
  # AsyncOpenAI() raises an error if you don't have an API key set.
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **.venv/lib/python3.13/site-packages/agents/models/openai_provider.py** (line 71)
  ```python
  self._client = _openai_shared.get_default_openai_client() or AsyncOpenAI(
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **.venv/lib/python3.13/site-packages/agents/models/_openai_shared.py** (line 3)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **.venv/lib/python3.13/site-packages/agents/voice/models/openai_model_provider.py** (line 4)
  ```python
  from openai import AsyncOpenAI, DefaultAsyncHttpxClient
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **.venv/lib/python3.13/site-packages/agents/voice/models/openai_model_provider.py** (line 64)
  ```python
  # AsyncOpenAI() raises an error if you don't have an API key set.
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **.venv/lib/python3.13/site-packages/agents/voice/models/openai_model_provider.py** (line 67)
  ```python
  self._client = _openai_shared.get_default_openai_client() or AsyncOpenAI(
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **.venv/lib/python3.13/site-packages/agents/voice/models/openai_tts.py** (line 4)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **.venv/lib/python3.13/site-packages/agents/voice/models/openai_stt.py** (line 11)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```

### openai/ (4 violations)

- **venv/lib/python3.13/site-packages/openai/_client.py** (line 77)
  ```python
  class OpenAI(SyncAPIClient):
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```
- **venv/lib/python3.13/site-packages/openai/_client.py** (line 396)
  ```python
  class AsyncOpenAI(AsyncAPIClient):
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **.venv/lib/python3.13/site-packages/openai/_client.py** (line 76)
  ```python
  class OpenAI(SyncAPIClient):
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```
- **.venv/lib/python3.13/site-packages/openai/_client.py** (line 377)
  ```python
  class AsyncOpenAI(AsyncAPIClient):
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```

### resources/ (2 violations)

- **venv/lib/python3.13/site-packages/openai/resources/webhooks.py** (line 66)
  ```python
  "on the client class, OpenAI(webhook_secret='123'), or passed to this function"
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```
- **venv/lib/python3.13/site-packages/openai/resources/webhooks.py** (line 163)
  ```python
  "on the client class, OpenAI(webhook_secret='123'), or passed to this function"
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```

### routes/ (2 violations)

- **routes/business_value_analyzer.py** (line 43)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **routes/business_value_analyzer.py** (line 46)
  ```python
  client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```

### services/ (28 violations)

- **services/enhanced_goal_driven_planner.py** (line 13)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **services/recovery_analysis_engine.py** (line 472)
  ```python
  self.client = openai.AsyncOpenAI()
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **services/constraint_violation_preventer.py** (line 54)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **services/constraint_violation_preventer.py** (line 55)
  ```python
  ai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **services/universal_ai_pipeline_engine.py** (line 25)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **services/unified_memory_engine.py** (line 26)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **services/unified_memory_engine.py** (line 124)
  ```python
  self.openai_client = AsyncOpenAI()
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **services/pure_ai_domain_classifier.py** (line 23)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **services/pure_ai_domain_classifier.py** (line 62)
  ```python
  self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **services/ai_resilient_similarity_engine.py** (line 37)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **services/ai_resilient_similarity_engine.py** (line 38)
  ```python
  ai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **services/ai_driven_director_enhancer.py** (line 73)
  ```python
  client = openai.AsyncOpenAI()
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **services/recovery_explanation_engine.py** (line 417)
  ```python
  self.client = openai.AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY')) if AI_CLIENT_AVAILABLE else None
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **services/workspace_cleanup_service.py** (line 12)
  ```python
  from openai import OpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```
- **services/workspace_cleanup_service.py** (line 23)
  ```python
  self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```
- **services/workspace_cleanup_service.py** (line 122)
  ```python
  # Delete from OpenAI (correct API path)
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```
- **services/semantic_domain_memory.py** (line 21)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **services/semantic_domain_memory.py** (line 64)
  ```python
  self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **services/ai_domain_classifier.py** (line 13)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **services/ai_domain_classifier.py** (line 21)
  ```python
  self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **services/universal_ai_content_extractor.py** (line 121)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **services/universal_ai_content_extractor.py** (line 123)
  ```python
  client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **services/unified_progress_manager.py** (line 178)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **services/unified_progress_manager.py** (line 179)
  ```python
  client = AsyncOpenAI(api_key=openai_api_key)
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **services/ai_task_execution_classifier.py** (line 51)
  ```python
  self.client = openai.AsyncOpenAI()
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **services/pdf_content_extractor.py** (line 262)
  ```python
  from openai import OpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```
- **services/document_manager.py** (line 18)
  ```python
  from openai import OpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```
- **services/document_manager.py** (line 86)
  ```python
  self.openai_client = OpenAI()
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```

### tools/ (6 violations)

- **tools/openai_sdk_tools.py** (line 12)
  ```python
  from openai import OpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```
- **tools/openai_sdk_tools.py** (line 147)
  ```python
  self.openai_client = OpenAI()
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```
- **tools/openai_sdk_tools.py** (line 200)
  ```python
  from openai import OpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```
- **tools/openai_sdk_tools.py** (line 201)
  ```python
  self.openai_client = OpenAI()
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```
- **tools/enhanced_document_search.py** (line 358)
  ```python
  from openai import OpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```
- **tools/enhanced_document_search.py** (line 359)
  ```python
  client = OpenAI()
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```

### utils/ (11 violations)

- **utils/ai_utils.py** (line 7)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **utils/ai_utils.py** (line 17)
  ```python
  client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **utils/ambiguity_resolver.py** (line 12)
  ```python
  from openai import OpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```
- **utils/ambiguity_resolver.py** (line 44)
  ```python
  self.openai_client = OpenAI()
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```
- **utils/ai_json_parser.py** (line 6)
  ```python
  from openai import AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **utils/ai_json_parser.py** (line 14)
  ```python
  self.client = client or AsyncOpenAI()
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **utils/openai_client_factory_enhanced.py** (line 12)
  ```python
  from openai import OpenAI, AsyncOpenAI
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **utils/openai_client_factory_enhanced.py** (line 391)
  ```python
  client = OpenAI(api_key=api_key)
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```
- **utils/openai_client_factory_enhanced.py** (line 392)
  ```python
  return EnhancedQuotaTrackedOpenAI(client, workspace_id)
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```
- **utils/openai_client_factory_enhanced.py** (line 403)
  ```python
  client = AsyncOpenAI(api_key=api_key)
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_async_openai_client`
  ```python
  client = get_async_openai_client()
  ```
- **utils/openai_client_factory_enhanced.py** (line 404)
  ```python
  return EnhancedQuotaTrackedOpenAI(client, workspace_id)
  ```
  **Fix**: Replace with `from utils.openai_client_factory import get_openai_client`
  ```python
  client = get_openai_client()
  ```

## Remediation Steps

1. **Immediate**: Fix all direct instantiations
2. **Extend Factory**: Add tracking for embeddings, assistants, threads, images
3. **Validation**: Run integration tests to verify tracking
4. **Prevention**: Add pre-commit hook to catch violations

## Untracked OpenAI API Methods in Use
- **embeddings.create**: Used in 7 files
  - test_enhanced_quota_tracking.py
  - fix_openai_quota_coverage.py
  - tools/openai_sdk_tools.py
  - ... and 4 more files
- **images.generate**: Used in 6 files
  - fix_openai_quota_coverage.py
  - tools/openai_sdk_tools.py
  - venv/lib/python3.13/site-packages/openai/resources/images.py
  - ... and 3 more files
- **audio.transcriptions.create**: Used in 5 files
  - fix_openai_quota_coverage.py
  - venv/lib/python3.13/site-packages/openai/cli/_api/audio.py
  - venv/lib/python3.13/site-packages/agents/voice/models/openai_stt.py
  - ... and 2 more files
- **audio.translations.create**: Used in 3 files
  - fix_openai_quota_coverage.py
  - venv/lib/python3.13/site-packages/openai/cli/_api/audio.py
  - .venv/lib/python3.13/site-packages/openai/cli/_api/audio.py
- **assistants.create**: Used in 4 files
  - fix_openai_quota_coverage.py
  - services/openai_assistant_manager.py
  - venv/lib/python3.13/site-packages/openai/resources/beta/assistants.py
  - ... and 1 more files
- **threads.create**: Used in 8 files
  - fix_openai_quota_coverage.py
  - ai_agents/specialist_enhanced.py
  - ai_agents/specialist.py
  - ... and 5 more files
- **files.create**: Used in 12 files
  - fix_openai_quota_coverage.py
  - services/document_manager.py
  - venv/lib/python3.13/site-packages/openai/resources/files.py
  - ... and 9 more files
- **vector_stores.create**: Used in 4 files
  - fix_openai_quota_coverage.py
  - services/document_manager.py
  - venv/lib/python3.13/site-packages/openai/resources/vector_stores/vector_stores.py
  - ... and 1 more files
- **moderations.create**: Used in 3 files
  - fix_openai_quota_coverage.py
  - venv/lib/python3.13/site-packages/openai/resources/moderations.py
  - .venv/lib/python3.13/site-packages/openai/resources/moderations.py