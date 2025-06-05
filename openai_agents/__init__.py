import asyncio
import json


class Agent:
    """Minimal stub mimicking the OpenAI Agents SDK `Agent` interface."""

    def __init__(self, *args, **kwargs):
        # The real SDK accepts various keyword arguments. We simply store them so
        # that object creation with arbitrary parameters does not raise errors
        # when the real package is unavailable.
        for key, value in kwargs.items():
            setattr(self, key, value)


class Runner:
    """Simplified stand-in for the SDK `Runner` class."""

    @staticmethod
    async def run(*_args, **_kwargs):
        """Return an object with a `final_output` attribute.

        This allows calling code to proceed without raising `AttributeError`
        when the real SDK is not available. The returned output is always an
        empty JSON object encoded as a string.
        """

        class DummyRunResult:
            final_output: str = "{}"

        return DummyRunResult()


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
