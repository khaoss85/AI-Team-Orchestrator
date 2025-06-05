"""Utility to instantiate ModelSettings compatibly across SDK versions."""

from typing import Any

try:
    from agents import ModelSettings  # type: ignore
except Exception:  # pragma: no cover - fallback
    try:
        from openai_agents import ModelSettings  # type: ignore
    except Exception:  # pragma: no cover

        class ModelSettings:  # type: ignore
            def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
                pass


def create_model_settings(**kwargs: Any) -> ModelSettings:
    """Create a ModelSettings object even if the class has no kwargs support."""
    try:
        return ModelSettings(**kwargs)
    except TypeError:
        instance = ModelSettings()
        for key, value in kwargs.items():
            setattr(instance, key, value)
        return instance
