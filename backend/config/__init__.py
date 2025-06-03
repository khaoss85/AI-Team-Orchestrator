# backend/config/__init__.py
"""
Configuration System
"""

try:
    from .quality_system_config import QualitySystemConfig
    __all__ = ['QualitySystemConfig']
except ImportError:
    __all__ = []