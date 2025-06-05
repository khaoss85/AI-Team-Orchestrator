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
        async def wrapper(*a, **k):
            return await func(*a, **k)
        return wrapper
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
