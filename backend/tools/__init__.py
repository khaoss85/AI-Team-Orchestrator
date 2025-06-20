# Conditional imports to handle dependencies gracefully
try:
    from .registry import tool_registry, ToolRegistry
except ImportError:
    # Fallback if agents SDK not available
    tool_registry = None
    ToolRegistry = None

try:
    from .social_media import InstagramTools
except ImportError:
    InstagramTools = None

# Always available
from .workspace_service import get_workspace_service, WorkspaceServiceInterface
from .openai_sdk_tools import openai_tools_manager