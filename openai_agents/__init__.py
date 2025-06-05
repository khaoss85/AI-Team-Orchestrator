import asyncio
import json


class Agent:
    pass


class Runner:
    pass


class AgentOutputSchema:
    def __init__(self, *a, **k):
        pass


class ModelSettings:
    """Lightweight container for model configuration settings."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def function_tool(name_override=None):
    def decorator(func):
        class Tool:
            async def on_invoke_tool(self, _ctx, params_json):
                data = (
                    json.loads(params_json)
                    if isinstance(params_json, str)
                    else params_json
                )
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
