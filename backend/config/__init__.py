# backend/config/__init__.py
"""
Configuration System
"""

__all__ = []

try:
    from .quality_system_config import QualitySystemConfig
    __all__.append('QualitySystemConfig')
except ImportError:
    pass

try:
    from .agent_system_config import AgentSystemConfig
    __all__.append('AgentSystemConfig')
except ImportError:
    pass
