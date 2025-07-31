#!/usr/bin/env python3
"""
🎯 **HOLISTIC ORCHESTRATOR**

Unified orchestration interface that eliminates silos between different orchestrator systems.
Provides a single, coherent orchestration layer that coordinates:
- Tool orchestration (SimpleToolOrchestrator)
- Workflow orchestration (UnifiedOrchestrator) 
- Task lifecycle management
- Quality feedback loops

This addresses the architectural fragmentation identified in the integration analysis.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class OrchestrationMode(Enum):
    """Orchestration execution modes"""
    SIMPLE = "simple"      # Basic tool orchestration
    UNIFIED = "unified"    # Advanced workflow orchestration  
    HYBRID = "hybrid"      # Intelligent mode selection
    AUTO = "auto"          # Automatic mode detection

class HolisticOrchestrator:
    """
    🎯 **UNIFIED ORCHESTRATION INTERFACE**
    
    Single point of orchestration that eliminates architectural silos
    and provides coherent coordination across all system components.
    """
    
    def __init__(self):
        self.simple_orchestrator = None
        self.unified_orchestrator = None
        self.orchestration_history = []
        self.mode_preferences = {}
        
        # Initialize available orchestrators
        self._initialize_orchestrators()
    
    def _initialize_orchestrators(self):
        """Initialize available orchestration systems"""
        try:
            # Initialize SimpleToolOrchestrator
            from services.simple_tool_orchestrator import SimpleToolOrchestrator
            self.simple_orchestrator = SimpleToolOrchestrator()
            logger.info("✅ SimpleToolOrchestrator initialized")
        except Exception as e:
            logger.warning(f"⚠️ SimpleToolOrchestrator not available: {e}")
        
        try:
            # Initialize UnifiedOrchestrator
            from services.unified_orchestrator import get_unified_orchestrator
            self.unified_orchestrator = get_unified_orchestrator()
            logger.info("✅ UnifiedOrchestrator initialized")
        except Exception as e:
            logger.warning(f"⚠️ UnifiedOrchestrator not available: {e}")
    
    async def orchestrate_task_execution(
        self,
        task_data: Dict[str, Any],
        agent_data: Dict[str, Any],
        workspace_context: Dict[str, Any],
        mode: OrchestrationMode = OrchestrationMode.AUTO
    ) -> Dict[str, Any]:
        """
        🎯 **UNIFIED TASK ORCHESTRATION**
        
        Single interface for all task orchestration needs.
        Automatically selects optimal orchestration strategy.
        """
        try:
            task_id = task_data.get("id")
            task_type = task_data.get("task_type", "hybrid")
            
            logger.info(f"🎯 Orchestrating task {task_id} (type: {task_type}, mode: {mode.value})")
            
            # Determine optimal orchestration mode
            selected_mode = await self._determine_orchestration_mode(
                task_data, agent_data, workspace_context, mode
            )
            
            # Execute orchestration using selected mode
            if selected_mode == OrchestrationMode.SIMPLE:
                result = await self._execute_simple_orchestration(task_data, agent_data, workspace_context)
            elif selected_mode == OrchestrationMode.UNIFIED:
                result = await self._execute_unified_orchestration(task_data, agent_data, workspace_context)
            else:  # HYBRID
                result = await self._execute_hybrid_orchestration(task_data, agent_data, workspace_context)
            
            # Record orchestration for learning
            await self._record_orchestration_result(task_data, selected_mode, result)
            
            return {
                **result,
                "orchestration_mode": selected_mode.value,
                "orchestration_quality": self._assess_orchestration_quality(result),
                "orchestrated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Holistic orchestration failed for task {task_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "orchestration_mode": "error",
                "orchestrated_at": datetime.now().isoformat()
            }
    
    async def _determine_orchestration_mode(
        self,
        task_data: Dict[str, Any],
        agent_data: Dict[str, Any], 
        workspace_context: Dict[str, Any],
        requested_mode: OrchestrationMode
    ) -> OrchestrationMode:
        """🧠 AI-driven orchestration mode selection"""
        
        if requested_mode != OrchestrationMode.AUTO:
            return requested_mode
        
        task_type = task_data.get("task_type", "hybrid")
        complexity = task_data.get("complexity_score", 50)
        workspace_agents = workspace_context.get("active_agents", 0)
        
        # Simple mode criteria
        if (task_type in ["data_gathering", "quality_assurance"] and 
            complexity < 30 and 
            self.simple_orchestrator):
            return OrchestrationMode.SIMPLE
        
        # Unified mode criteria  
        if (task_type in ["content_creation", "strategy_planning"] and
            complexity > 70 and
            workspace_agents > 3 and
            self.unified_orchestrator):
            return OrchestrationMode.UNIFIED
        
        # Hybrid mode (default)
        return OrchestrationMode.HYBRID
    
    async def _execute_simple_orchestration(
        self,
        task_data: Dict[str, Any],
        agent_data: Dict[str, Any],
        workspace_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute using SimpleToolOrchestrator"""
        try:
            if not self.simple_orchestrator:
                raise Exception("SimpleToolOrchestrator not available")
            
            # Execute simple orchestration
            result = await self.simple_orchestrator.execute_task(
                task_data, agent_data, workspace_context
            )
            
            return {
                "success": True,
                "result": result,
                "orchestration_method": "simple_tool_orchestration"
            }
            
        except Exception as e:
            logger.error(f"❌ Simple orchestration failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_unified_orchestration(
        self,
        task_data: Dict[str, Any],
        agent_data: Dict[str, Any],
        workspace_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute using UnifiedOrchestrator"""
        try:
            if not self.unified_orchestrator:
                raise Exception("UnifiedOrchestrator not available")
            
            # Execute unified orchestration
            result = await self.unified_orchestrator.orchestrate_task(
                task_data, agent_data, workspace_context
            )
            
            return {
                "success": True,
                "result": result,
                "orchestration_method": "unified_workflow_orchestration"
            }
            
        except Exception as e:
            logger.error(f"❌ Unified orchestration failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_hybrid_orchestration(
        self,
        task_data: Dict[str, Any],
        agent_data: Dict[str, Any],
        workspace_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute hybrid orchestration combining both approaches"""
        try:
            # Try unified first, fallback to simple
            if self.unified_orchestrator:
                unified_result = await self._execute_unified_orchestration(
                    task_data, agent_data, workspace_context
                )
                if unified_result.get("success"):
                    return {
                        **unified_result,
                        "orchestration_method": "hybrid_unified_primary"
                    }
            
            # Fallback to simple orchestration
            if self.simple_orchestrator:
                simple_result = await self._execute_simple_orchestration(
                    task_data, agent_data, workspace_context
                )
                return {
                    **simple_result,
                    "orchestration_method": "hybrid_simple_fallback"
                }
            
            raise Exception("No orchestrators available")
            
        except Exception as e:
            logger.error(f"❌ Hybrid orchestration failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _assess_orchestration_quality(self, result: Dict[str, Any]) -> float:
        """Assess the quality of orchestration results"""
        if not result.get("success"):
            return 0.0
        
        quality_score = 50.0  # Base score
        
        # Factors that increase quality
        if result.get("result"):
            quality_score += 20.0
        
        if result.get("orchestration_method"):
            quality_score += 10.0
        
        if "error" not in result:
            quality_score += 20.0
        
        return min(quality_score, 100.0)
    
    async def _record_orchestration_result(
        self,
        task_data: Dict[str, Any],
        mode: OrchestrationMode,
        result: Dict[str, Any]
    ):
        """Record orchestration results for learning"""
        record = {
            "task_id": task_data.get("id"),
            "task_type": task_data.get("task_type"),
            "orchestration_mode": mode.value,
            "success": result.get("success", False),
            "quality_score": self._assess_orchestration_quality(result),
            "timestamp": datetime.now().isoformat()
        }
        
        self.orchestration_history.append(record)
        
        # Keep only recent history (last 100 orchestrations)
        if len(self.orchestration_history) > 100:
            self.orchestration_history = self.orchestration_history[-100:]
    
    async def get_orchestration_insights(self, workspace_id: str) -> Dict[str, Any]:
        """Get insights about orchestration performance"""
        if not self.orchestration_history:
            return {"message": "No orchestration history available"}
        
        total_orchestrations = len(self.orchestration_history)
        successful_orchestrations = sum(1 for r in self.orchestration_history if r["success"])
        success_rate = (successful_orchestrations / total_orchestrations) * 100
        
        # Mode usage statistics
        mode_usage = {}
        for record in self.orchestration_history:
            mode = record["orchestration_mode"]
            mode_usage[mode] = mode_usage.get(mode, 0) + 1
        
        # Average quality by mode
        quality_by_mode = {}
        for mode in mode_usage.keys():
            mode_records = [r for r in self.orchestration_history if r["orchestration_mode"] == mode]
            avg_quality = sum(r["quality_score"] for r in mode_records) / len(mode_records)
            quality_by_mode[mode] = round(avg_quality, 2)
        
        return {
            "total_orchestrations": total_orchestrations,
            "success_rate": round(success_rate, 2),
            "mode_usage": mode_usage,
            "quality_by_mode": quality_by_mode,
            "optimal_mode_recommendation": max(quality_by_mode, key=quality_by_mode.get) if quality_by_mode else "hybrid"
        }

# Global holistic orchestrator instance
_holistic_orchestrator_instance = None

def get_holistic_orchestrator() -> HolisticOrchestrator:
    """Get the global holistic orchestrator instance"""
    global _holistic_orchestrator_instance
    
    if _holistic_orchestrator_instance is None:
        _holistic_orchestrator_instance = HolisticOrchestrator()
        logger.info("🎯 Holistic Orchestrator initialized - silos eliminated!")
    
    return _holistic_orchestrator_instance

async def orchestrate_task_holistically(
    task_data: Dict[str, Any],
    agent_data: Dict[str, Any],
    workspace_context: Dict[str, Any],
    mode: OrchestrationMode = OrchestrationMode.AUTO
) -> Dict[str, Any]:
    """
    🎯 **CONVENIENCE FUNCTION**: Orchestrate a task using the holistic approach
    
    Single entry point for all task orchestration needs.
    """
    orchestrator = get_holistic_orchestrator()
    return await orchestrator.orchestrate_task_execution(
        task_data, agent_data, workspace_context, mode
    )