# backend/utils/project_settings.py

import os
import logging
from typing import Dict, Any, Optional
from database import get_workspace

logger = logging.getLogger(__name__)

class ProjectSettings:
    """
    Utility class to retrieve project-specific settings with fallback to environment defaults
    """
    
    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self._settings_cache = None
        
    async def _load_workspace_settings(self) -> Dict[str, Any]:
        """Load workspace settings from database"""
        if self._settings_cache is not None:
            return self._settings_cache
            
        try:
            workspace = await get_workspace(self.workspace_id)
            if workspace and workspace.get('budget'):
                budget_data = workspace['budget']
                if isinstance(budget_data, dict):
                    self._settings_cache = budget_data.get('settings', {})
                    return self._settings_cache
        except Exception as e:
            logger.warning(f"Failed to load workspace settings for {self.workspace_id}: {e}")
            
        self._settings_cache = {}
        return self._settings_cache
    
    async def get(self, setting_name: str, default_value: Any = None, env_var: str = None) -> Any:
        """
        Get a setting value with fallback priority:
        1. Project-specific setting from database
        2. Environment variable
        3. Default value
        """
        # Load project settings
        project_settings = await self._load_workspace_settings()
        
        # Check project-specific setting first
        if setting_name in project_settings:
            return project_settings[setting_name]
            
        # Check environment variable if provided
        if env_var:
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Convert string env vars to appropriate types
                if isinstance(default_value, bool):
                    return env_value.lower() in ('true', '1', 'yes', 'on')
                elif isinstance(default_value, int):
                    try:
                        return int(env_value)
                    except ValueError:
                        pass
                elif isinstance(default_value, float):
                    try:
                        return float(env_value)
                    except ValueError:
                        pass
                return env_value
                
        # Return default value
        return default_value
    
    async def get_quality_threshold(self) -> float:
        """Get quality threshold (0-100)"""
        return await self.get('quality_threshold', 85.0, 'QUALITY_SCORE_THRESHOLD')
    
    async def get_max_iterations(self) -> int:
        """Get max iterations per task"""
        return await self.get('max_iterations', 3, 'MAX_ENHANCEMENT_ATTEMPTS')
    
    async def get_max_concurrent_tasks(self) -> int:
        """Get max concurrent tasks"""
        return await self.get('max_concurrent_tasks', 3, 'MAX_CONCURRENT_TASKS')
    
    async def get_task_timeout(self) -> int:
        """Get task timeout in seconds"""
        return await self.get('task_timeout', 150, 'TASK_TIMEOUT_SECONDS')
    
    async def is_quality_assurance_enabled(self) -> bool:
        """Check if quality assurance is enabled"""
        return await self.get('enable_quality_assurance', True, 'ENABLE_AI_QUALITY_ASSURANCE')
    
    async def get_deliverable_threshold(self) -> float:
        """Get deliverable threshold (0-100)"""
        return await self.get('deliverable_threshold', 50.0, 'DELIVERABLE_READINESS_THRESHOLD')
    
    async def get_max_deliverables(self) -> int:
        """Get max deliverables per project"""
        return await self.get('max_deliverables', 3, 'MAX_DELIVERABLES_PER_WORKSPACE')
    
    async def get_max_budget(self) -> float:
        """Get max budget for the project"""
        project_settings = await self._load_workspace_settings()
        return project_settings.get('max_budget', 10.0)
    
    async def get_all_settings(self) -> Dict[str, Any]:
        """Get all project settings as a dictionary"""
        return {
            'quality_threshold': await self.get_quality_threshold(),
            'max_iterations': await self.get_max_iterations(),
            'max_concurrent_tasks': await self.get_max_concurrent_tasks(),
            'task_timeout': await self.get_task_timeout(),
            'enable_quality_assurance': await self.is_quality_assurance_enabled(),
            'deliverable_threshold': await self.get_deliverable_threshold(),
            'max_deliverables': await self.get_max_deliverables(),
            'max_budget': await self.get_max_budget()
        }

def get_project_settings(workspace_id: str) -> ProjectSettings:
    """Factory function to create ProjectSettings instance"""
    return ProjectSettings(workspace_id)