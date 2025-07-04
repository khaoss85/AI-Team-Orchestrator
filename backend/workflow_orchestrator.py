"""
Compatibility Bridge for Workflow Orchestrator
================================================================================
This file provides backward compatibility for imports of the legacy workflow_orchestrator
while redirecting all functionality to the new unified_orchestrator.

This ensures existing code continues to work while the system uses the new
consolidated orchestration engine.
"""

import logging
from services.unified_orchestrator import get_unified_orchestrator

logger = logging.getLogger(__name__)

# Backward compatibility: provide the old interface through the unified orchestrator
workflow_orchestrator = get_unified_orchestrator()

# Legacy class for backward compatibility
class WorkflowOrchestrator:
    """Legacy WorkflowOrchestrator class - redirects to UnifiedOrchestrator"""
    
    def __init__(self):
        self._unified_orchestrator = get_unified_orchestrator()
        logger.info("🔗 Legacy WorkflowOrchestrator using UnifiedOrchestrator backend")
    
    async def process_workspace(self, workspace_id: str):
        """Legacy method - redirects to unified orchestrator"""
        logger.info(f"🔗 Legacy process_workspace redirecting to unified orchestrator for {workspace_id}")
        # This was the old simple method - we'll enhance it with goal discovery
        try:
            # Get workspace goals
            goals_response = self._unified_orchestrator.supabase.table("workspace_goals")\
                .select("*")\
                .eq("workspace_id", workspace_id)\
                .eq("status", "active")\
                .execute()
            
            goals = goals_response.data or []
            
            if not goals:
                logger.warning(f"No active goals found for workspace {workspace_id}")
                return
            
            # Process each goal through the unified workflow
            for goal in goals:
                try:
                    result = await self._unified_orchestrator.execute_complete_workflow(
                        workspace_id=workspace_id,
                        goal_id=goal["id"],
                        enable_adaptive_optimization=True
                    )
                    
                    if result.success:
                        logger.info(f"✅ Goal {goal['id']} processed successfully")
                    else:
                        logger.warning(f"⚠️ Goal {goal['id']} processing failed: {result.error}")
                        
                except Exception as e:
                    logger.error(f"❌ Failed to process goal {goal['id']}: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Legacy process_workspace failed for {workspace_id}: {e}")
    
    async def execute_complete_workflow(self, workspace_id: str, goal_id: str, **kwargs):
        """Legacy method - redirects to unified orchestrator"""
        return await self._unified_orchestrator.execute_complete_workflow(workspace_id, goal_id, **kwargs)
    
    def get_workflow_progress(self, workflow_id: str):
        """Legacy method - redirects to unified orchestrator"""
        return self._unified_orchestrator.get_workflow_progress(workflow_id)
    
    def get_statistics(self):
        """Legacy method - redirects to unified orchestrator"""
        return self._unified_orchestrator.get_system_statistics()
    
    async def health_check(self):
        """Legacy method - redirects to unified orchestrator"""
        return await self._unified_orchestrator.health_check()

# Provide the legacy instance for backward compatibility
legacy_workflow_orchestrator = WorkflowOrchestrator()

logger.info("🔗 Workflow Orchestrator compatibility bridge loaded - using UnifiedOrchestrator backend")