class Agent:
    """Very small fallback Agent implementation.

    It simply stores any provided arguments so code expecting an SDK class
    can instantiate it without errors when the real package is missing.
    """

    def __init__(self, *args, **kwargs):
        self.args = args
        for key, value in kwargs.items():
            setattr(self, key, value)


class Runner:
    """Trivial async runner used as a fallback when the real SDK is absent."""

    @staticmethod
    async def run(*_a, **_k):
        class Dummy:
            final_output = "{}"

        return Dummy()

class AgentOutputSchema:
    def __init__(self, *a, **k):
        pass


class ModelSettings:
    """Simple container for LLM configuration settings."""

    def __init__(self, temperature=None, top_p=None, max_tokens=None, **kwargs):
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        for k, v in kwargs.items():
            setattr(self, k, v)


import asyncio
import json

def function_tool(name_override=None):
    """Fallback implementation returning a minimal tool wrapper."""

    def decorator(func):
        class Tool:
            async def on_invoke_tool(self, _ctx, params_json):
                data = json.loads(params_json) if isinstance(params_json, str) else params_json
                if asyncio.iscoroutinefunction(func):
                    return await func(**(data or {}))
                return func(**(data or {}))

        return Tool()

    return decorator

class WebSearchTool:
    pass

class FileSearchTool:
    pass

def RunContextWrapper(*a, **k):
    return None

def handoff(*a, **k):
    return None

def trace(*a, **k):
    class Dummy:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            pass
    return Dummy()

def gen_trace_id():
    return "id"