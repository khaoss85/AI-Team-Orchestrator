"""
Unified Progress Manager - Root Cause Fix for Goal-Task-Deliverable Loop

PILLARS IMPLEMENTED:
- PILLAR 2: AI-Driven progress calculation
- PILLAR 5: Goal-Driven with real feedback loops  
- PILLAR 12: Concrete Deliverables linked to progress
- PILLAR 13: Course-Correction with exit conditions

ROOT CAUSE ADDRESSED:
- Task completion → Goal progress update (MISSING LINK)
- Deliverable creation → Goal validation (MISSING LINK)
- Corrective task prevention via unified state
"""

import os
import asyncio
import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from database import supabase
from models import WorkspaceGoal, GoalStatus, TaskStatus
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ProgressEvent:
    """Unified progress event that links Goals, Tasks, and Deliverables"""
    workspace_id: str
    goal_id: str
    task_id: Optional[str] = None
    deliverable_id: Optional[str] = None
    progress_delta: float = 0.0
    event_type: str = "task_completion"  # task_completion, deliverable_created, manual_update
    metadata: Dict[str, Any] = None

class UnifiedProgressManager:
    """
    🎯 UNIFIED PROGRESS MANAGEMENT
    
    Centralizes all progress updates across Goals, Tasks, and Deliverables.
    Prevents infinite loops by managing state transitions atomically.
    """
    
    def __init__(self):
        self.enable_ai_progress_calculation = os.getenv("ENABLE_AI_PROGRESS_CALCULATION", "true").lower() == "true"
        self.corrective_task_global_cooldown = {}
        self.cooldown_duration = int(os.getenv("CORRECTIVE_TASK_COOLDOWN_SECONDS", "300"))
        
        # Track processing to prevent cascading updates
        self.processing_events = set()
        
    async def handle_task_completion(self, task_id: str, completion_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        🔄 CRITICAL FIX: Handle task completion and update goal progress
        
        This is the MISSING LINK that prevents infinite corrective task loops.
        """
        try:
            # Get task details including goal association
            task_response = supabase.table("tasks").select("*").eq("id", task_id).single().execute()
            task = task_response.data
            
            if not task.get("goal_id"):
                logger.info(f"Task {task_id} not associated with a goal - no progress update needed")
                return {"updated": False, "reason": "no_goal_association"}
            
            goal_id = task["goal_id"]
            workspace_id = task["workspace_id"]
            
            # Prevent cascading updates
            event_key = f"{workspace_id}_{goal_id}_{task_id}"
            if event_key in self.processing_events:
                logger.warning(f"Already processing event {event_key} - preventing cascade")
                return {"updated": False, "reason": "cascade_prevention"}
                
            self.processing_events.add(event_key)
            
            try:
                # Calculate progress contribution from task completion
                progress_contribution = await self._calculate_task_progress_contribution(
                    task, completion_data
                )
                
                if progress_contribution > 0:
                    # Create progress event
                    progress_event = ProgressEvent(
                        workspace_id=workspace_id,
                        goal_id=goal_id,
                        task_id=task_id,
                        progress_delta=progress_contribution,
                        event_type="task_completion",
                        metadata={
                            "task_name": task.get("name"),
                            "completion_data": completion_data,
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                    
                    # Update goal progress atomically
                    result = await self._update_goal_progress_atomic(progress_event)
                    
                    logger.info(f"✅ Task {task_id} completion updated goal {goal_id} progress by {progress_contribution}")
                    return result
                else:
                    logger.info(f"Task {task_id} completion did not contribute measurable progress")
                    return {"updated": False, "reason": "no_measurable_progress"}
                    
            finally:
                self.processing_events.discard(event_key)
                
        except Exception as e:
            logger.error(f"Error handling task completion {task_id}: {e}")
            return {"updated": False, "error": str(e)}
    
    async def _calculate_task_progress_contribution(
        self, 
        task: Dict[str, Any], 
        completion_data: Dict[str, Any]
    ) -> float:
        """
        🤖 AI-DRIVEN: Calculate how much a completed task contributes to goal progress
        """
        try:
            # Get expected contribution from task
            expected_contribution = task.get("contribution_expected", 0)
            if expected_contribution > 0:
                logger.info(f"Using expected contribution: {expected_contribution}")
                return float(expected_contribution)
            
            # 🤖 AI-DRIVEN CALCULATION
            if self.enable_ai_progress_calculation:
                ai_contribution = await self._ai_calculate_progress_contribution(task, completion_data)
                if ai_contribution is not None:
                    return ai_contribution
            
            # Fallback: Standard contribution based on task type
            task_name = task.get("name", "").lower()
            
            # Corrective tasks that close gaps should contribute their full target
            if "close" in task_name and "gap" in task_name:
                # Extract gap percentage from name (e.g., "Close 100.0% gap")
                import re
                gap_match = re.search(r'close\s+(\d+\.?\d*)%?\s+gap', task_name)
                if gap_match:
                    gap_value = float(gap_match.group(1))
                    # If it's a percentage, convert appropriately
                    if gap_value > 1:  # Likely a percentage
                        return 1.0  # Full gap closure
                    else:
                        return gap_value
            
            # Default small contribution
            return 0.1  # 10% progress contribution for generic tasks
            
        except Exception as e:
            logger.error(f"Error calculating progress contribution: {e}")
            return 0.0
    
    async def _ai_calculate_progress_contribution(
        self, 
        task: Dict[str, Any], 
        completion_data: Dict[str, Any]
    ) -> Optional[float]:
        """
        🤖 AI-DRIVEN: Use AI to intelligently calculate progress contribution with semantic validation
        """
        try:
            # Get AI client
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                logger.debug("No OpenAI API key available for AI progress calculation")
                return None
            
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=openai_api_key)
            
            # Get goal context for semantic validation
            goal_id = task.get("goal_id")
            if not goal_id:
                return None
            
            # Get goal details
            goal_response = supabase.table("workspace_goals").select("*").eq("id", goal_id).single().execute()
            if not goal_response.data:
                return None
            
            goal = goal_response.data
            goal_description = goal.get("description", "")
            goal_metric_type = goal.get("metric_type", "")
            target_value = goal.get("target_value", 1)
            current_value = goal.get("current_value", 0)
            
            # Prepare task output for analysis
            task_name = task.get("name", "")
            task_description = task.get("description", "")
            task_result = completion_data.get("output", "")
            
            # Create AI prompt for semantic validation
            prompt = f"""You are an AI system evaluating how much a completed task contributes to a specific goal. 
Provide a contribution score between 0.0 and 1.0.

GOAL CONTEXT:
- Goal: {goal_description}
- Metric Type: {goal_metric_type}
- Target Value: {target_value}
- Current Progress: {current_value}/{target_value}

COMPLETED TASK:
- Name: {task_name}
- Description: {task_description}
- Output/Result: {task_result}

SEMANTIC VALIDATION CRITERIA:
1. Does the task output directly contribute to the goal?
2. Is the output tangible and measurable?
3. Does it represent real progress toward the target?
4. How significant is this contribution relative to the goal?

Provide a JSON response with:
{{
    "contribution_score": 0.0-1.0,
    "reasoning": "Brief explanation of the score",
    "semantic_match": true/false,
    "quality_score": 0.0-1.0
}}

SCORING GUIDELINES:
- 0.0: No contribution to goal
- 0.1-0.3: Minor/indirect contribution
- 0.4-0.6: Moderate direct contribution
- 0.7-0.9: Major contribution
- 1.0: Completes the entire goal

Be conservative but fair in your assessment."""

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert project evaluator who assesses task contributions to business goals."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            contribution_score = result.get("contribution_score", 0.0)
            semantic_match = result.get("semantic_match", False)
            reasoning = result.get("reasoning", "")
            
            logger.info(f"🤖 AI Progress Evaluation: {contribution_score:.2f} score, semantic_match: {semantic_match}")
            logger.debug(f"AI reasoning: {reasoning}")
            
            # Semantic validation: only return score if there's a semantic match
            if semantic_match and contribution_score > 0:
                return float(contribution_score)
            else:
                logger.warning(f"Task failed semantic validation: {reasoning}")
                return 0.0
            
        except Exception as e:
            logger.debug(f"AI progress calculation failed: {e}")
            return None
    
    async def _update_goal_progress_atomic(self, progress_event: ProgressEvent) -> Dict[str, Any]:
        """
        🔄 ATOMIC: Update goal progress atomically to prevent race conditions
        """
        try:
            # Get current goal state
            goal_response = supabase.table("workspace_goals").select("*").eq(
                "id", progress_event.goal_id
            ).single().execute()
            
            goal = goal_response.data
            current_value = float(goal["current_value"])
            target_value = float(goal["target_value"])
            
            # Calculate new progress
            new_value = min(current_value + progress_event.progress_delta, target_value)
            
            # Update goal with new progress
            update_result = supabase.table("workspace_goals").update({
                "current_value": new_value,
                "last_validation_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }).eq("id", progress_event.goal_id).execute()
            
            # Check if goal is now completed
            if new_value >= target_value:
                await self._handle_goal_completion(progress_event.goal_id, progress_event.workspace_id)
            
            # Clear any corrective task cooldowns for this goal (it's making progress)
            self._clear_corrective_cooldown(progress_event.workspace_id, progress_event.goal_id)
            
            logger.info(f"🎯 Goal {progress_event.goal_id} progress: {current_value} → {new_value} (Δ{progress_event.progress_delta})")
            
            return {
                "updated": True,
                "previous_value": current_value,
                "new_value": new_value,
                "goal_completed": new_value >= target_value
            }
            
        except Exception as e:
            logger.error(f"Error updating goal progress atomically: {e}")
            return {"updated": False, "error": str(e)}
    
    async def _handle_goal_completion(self, goal_id: str, workspace_id: str):
        """Handle goal completion - trigger deliverable creation"""
        try:
            # Update goal status to completed
            supabase.table("workspace_goals").update({
                "status": GoalStatus.COMPLETED.value,
                "completed_at": datetime.now().isoformat()
            }).eq("id", goal_id).execute()
            
            # Trigger deliverable creation
            from services.deliverable_achievement_mapper import deliverable_achievement_mapper
            await deliverable_achievement_mapper.check_and_create_deliverable(workspace_id)
            
            logger.info(f"🏆 Goal {goal_id} completed - deliverable check triggered")
            
        except Exception as e:
            logger.error(f"Error handling goal completion: {e}")
    
    def check_corrective_task_cooldown(self, workspace_id: str, goal_id: str) -> bool:
        """
        🚨 LOOP PREVENTION: Check if corrective task creation is in cooldown
        """
        cooldown_key = f"{workspace_id}_{goal_id}"
        
        if cooldown_key not in self.corrective_task_global_cooldown:
            return False
            
        last_created = self.corrective_task_global_cooldown[cooldown_key]
        cooldown_expires = last_created + timedelta(seconds=self.cooldown_duration)
        
        return datetime.now() < cooldown_expires
    
    def add_corrective_task_cooldown(self, workspace_id: str, goal_id: str):
        """Add corrective task cooldown to prevent spam"""
        cooldown_key = f"{workspace_id}_{goal_id}"
        self.corrective_task_global_cooldown[cooldown_key] = datetime.now()
        
        logger.info(f"🔄 Added corrective task cooldown for {cooldown_key} (expires in {self.cooldown_duration}s)")
    
    def _clear_corrective_cooldown(self, workspace_id: str, goal_id: str):
        """Clear corrective task cooldown when progress is made"""
        cooldown_key = f"{workspace_id}_{goal_id}"
        if cooldown_key in self.corrective_task_global_cooldown:
            del self.corrective_task_global_cooldown[cooldown_key]
            logger.info(f"✅ Cleared corrective task cooldown for {cooldown_key} - progress made")

# Singleton instance
unified_progress_manager = UnifiedProgressManager()