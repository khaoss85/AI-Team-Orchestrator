"""
AI Decision Tracker - Tracks AI-driven decisions for analytics and improvement

Integrates with Phase 2 AI-driven features to log:
- Context analysis decisions
- Handoff filtering optimizations  
- Agent selection choices
- Performance metrics
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID
from database import get_supabase_client

logger = logging.getLogger(__name__)

class AIDecisionTracker:
    """Tracks AI decisions for analytics and system improvement"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        
    async def log_context_analysis(self, 
                                 workspace_id: str,
                                 task_id: str, 
                                 agent_id: str,
                                 analysis_result: Dict[str, Any],
                                 execution_time_ms: int = None) -> bool:
        """Log AI context analysis decision"""
        try:
            decision_data = {
                "task_complexity": analysis_result.get("task_complexity"),
                "collaboration_mode": analysis_result.get("collaboration_mode"),
                "required_skills": analysis_result.get("required_skills", []),
                "execution_phase": analysis_result.get("execution_phase"),
                "ai_confidence": analysis_result.get("confidence", 0.8)
            }
            
            # Log to decision table
            await self._log_decision(
                workspace_id=workspace_id,
                decision_type="context_analysis",
                source_agent_id=agent_id,
                task_id=task_id,
                decision_data=decision_data,
                execution_time_ms=execution_time_ms
            )
            
            # Update task with AI analysis
            await self._update_task_ai_data(task_id, analysis_result)
            
            logger.debug(f"🧠 Logged context analysis for task {task_id[:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log context analysis: {e}")
            return False
    
    async def log_handoff_optimization(self,
                                     workspace_id: str,
                                     source_agent_id: str,
                                     target_agent_id: str, 
                                     optimization_result: Dict[str, Any],
                                     task_id: str = None,
                                     execution_time_ms: int = None) -> bool:
        """Log AI handoff filtering decision"""
        try:
            decision_data = {
                "optimization_summary": optimization_result.get("optimization_summary"),
                "essential_info": optimization_result.get("essential_info", []),
                "removed_info": optimization_result.get("remove_info", []),
                "preserved_context": optimization_result.get("preserve_context", []),
                "context_size_reduction": optimization_result.get("size_reduction", 0)
            }
            
            # Log to decision table
            await self._log_decision(
                workspace_id=workspace_id,
                decision_type="handoff_filter",
                source_agent_id=source_agent_id,
                target_agent_id=target_agent_id,
                task_id=task_id,
                decision_data=decision_data,
                execution_time_ms=execution_time_ms
            )
            
            logger.debug(f"🔧 Logged handoff optimization {source_agent_id[:8]}...→{target_agent_id[:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log handoff optimization: {e}")
            return False
    
    async def log_agent_selection(self,
                                workspace_id: str,
                                selected_agents: list,
                                selection_criteria: Dict[str, Any],
                                task_id: str = None) -> bool:
        """Log AI agent selection decision"""
        try:
            decision_data = {
                "selected_agents": [{"id": str(agent.get("id", "")), "role": agent.get("role", ""), "relevance_reason": agent.get("relevance_reason", "")} for agent in selected_agents],
                "selection_criteria": selection_criteria,
                "total_agents_available": selection_criteria.get("total_available", 0),
                "agents_selected": len(selected_agents)
            }
            
            await self._log_decision(
                workspace_id=workspace_id,
                decision_type="agent_selection", 
                task_id=task_id,
                decision_data=decision_data
            )
            
            logger.debug(f"👥 Logged agent selection: {len(selected_agents)} selected")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log agent selection: {e}")
            return False
    
    async def _log_decision(self,
                          workspace_id: str,
                          decision_type: str,
                          decision_data: Dict[str, Any],
                          source_agent_id: str = None,
                          target_agent_id: str = None,
                          task_id: str = None,
                          execution_time_ms: int = None) -> bool:
        """Internal method to log decision to database"""
        try:
            record = {
                "workspace_id": workspace_id,
                "decision_type": decision_type,
                "decision_data": decision_data,
                "execution_time_ms": execution_time_ms,
                "success": True,
                "created_at": datetime.now().isoformat()
            }
            
            # Add optional foreign keys
            if source_agent_id:
                record["source_agent_id"] = source_agent_id
            if target_agent_id:
                record["target_agent_id"] = target_agent_id  
            if task_id:
                record["task_id"] = task_id
            
            result = self.supabase.table("ai_decision_log").insert(record).execute()
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Failed to log decision to database: {e}")
            return False
    
    async def _update_task_ai_data(self, task_id: str, analysis_result: Dict[str, Any]):
        """Update task with AI analysis results"""
        try:
            update_data = {
                "ai_context_analysis": analysis_result,
                "ai_collaboration_mode": analysis_result.get("collaboration_mode"),
                "ai_complexity_level": analysis_result.get("task_complexity")
            }
            
            self.supabase.table("tasks").update(update_data).eq("id", task_id).execute()
            
        except Exception as e:
            logger.warning(f"Failed to update task AI data: {e}")

# Global instance
ai_decision_tracker = AIDecisionTracker()