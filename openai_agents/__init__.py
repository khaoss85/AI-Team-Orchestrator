class Agent:
    pass


class Runner:
    pass


class AgentOutputSchema:
    pass


class ModelSettings:
    pass


class WebSearchTool:
    pass


class FileSearchTool:
    pass


def function_tool(*args, **kwargs):
    def decorator(func):
        async def on_invoke_tool(_self, param_json):
            if isinstance(param_json, str):
                import json
                params = json.loads(param_json)
            else:
                params = param_json
            return await func(**params)
        wrapper = type(
            "StubTool",
            (),
            {"on_invoke_tool": staticmethod(on_invoke_tool)},
        )
        return wrapper
    return decorator
