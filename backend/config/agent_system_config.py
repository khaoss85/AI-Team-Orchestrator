# backend/config/agent_system_config.py
"""General configuration for agent behaviour."""
import os

class AgentSystemConfig:
    """Centralized agent configuration loaded from environment variables."""

    # Timeout in seconds for SpecialistAgent task execution
    SPECIALIST_EXECUTION_TIMEOUT: int = int(os.getenv("SPECIALIST_EXECUTION_TIMEOUT", "120"))

    @classmethod
    def get_all_settings(cls):
        return {
            attr: getattr(cls, attr)
            for attr in dir(cls)
            if not attr.startswith('_') and not callable(getattr(cls, attr))
        }
