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
    """
    🤖 PILLAR 2 & 3 COMPLIANCE: Universal ModelSettings with intelligent defaults
    Creates ModelSettings that work across all environments and use cases
    """
    # 🌍 PILLAR 2: Universal defaults that work for any industry/domain
    default_model = kwargs.get('model', 'gpt-4o-mini')  # Fast, cost-effective default
    default_temperature = kwargs.get('temperature', 0.1)  # Consistent outputs
    default_max_tokens = kwargs.get('max_tokens', 150)  # Reasonable limit
    
    try:
        # Try to create with provided kwargs
        settings = ModelSettings(**kwargs)
        
        # 🔧 PILLAR 3: Ensure critical attributes exist
        if not hasattr(settings, 'model'):
            settings.model = default_model
        if not hasattr(settings, 'temperature'):
            settings.temperature = default_temperature
        if not hasattr(settings, 'max_tokens'):
            settings.max_tokens = default_max_tokens
            
        return settings
        
    except TypeError:
        # Fallback: create instance and set attributes manually
        instance = ModelSettings()
        
        # Set provided kwargs
        for key, value in kwargs.items():
            setattr(instance, key, value)
        
        # 🌍 PILLAR 2 & 3: Ensure critical attributes with universal defaults
        if not hasattr(instance, 'model') or not instance.model:
            instance.model = default_model
        if not hasattr(instance, 'temperature'):
            instance.temperature = default_temperature  
        if not hasattr(instance, 'max_tokens'):
            instance.max_tokens = default_max_tokens
            
        return instance
