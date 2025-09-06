#!/usr/bin/env python3
"""
🔄 SYSTEMATIC LEARNING FEEDBACK LOOPS SERVICE

Automatically captures task execution outcomes and updates workspace memory
with success patterns, failure lessons, and best practices.

Creates a continuous improvement cycle:
Task Execution → Outcome Analysis → Pattern Extraction → Memory Update → Future Enhancement

Part of the Goal-Driven Intelligent Integration:
Memory → Enhanced Task Generation → RAG-Enhanced Execution → Quality Gates → Learning Feedback
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import os
import json
from enum import Enum

from models import Task, TaskStatus, TaskExecutionOutput
from database import get_supabase_client

logger = logging.getLogger(__name__)
supabase = get_supabase_client()

class LearningOutcome(Enum):
    """Types of learning outcomes from task execution"""
    SUCCESS_PATTERN = "success_pattern"
    FAILURE_LESSON = "failure_lesson"
    BEST_PRACTICE = "best_practice"
    OPTIMIZATION_OPPORTUNITY = "optimization_opportunity"
    ANTI_PATTERN = "anti_pattern"

class SystematicLearningLoops:
    """
    🔄 Systematic learning feedback loop system
    
    Automatically analyzes task execution outcomes and updates workspace memory
    to continuously improve future task generation and execution.
    """
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = None
        self.learning_enabled = os.getenv("ENABLE_SYSTEMATIC_LEARNING", "true").lower() == "true"
        self.batch_size = int(os.getenv("LEARNING_BATCH_SIZE", "5"))
        
        if self.openai_api_key:
            try:
                from openai import AsyncOpenAI
                self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
                self.ai_available = True
                logger.info("✅ Systematic Learning Loops initialized with AI")
            except ImportError:
                self.ai_available = False
                logger.warning("⚠️ OpenAI not available for AI learning analysis")
        else:
            self.ai_available = False
            logger.info("ℹ️ Learning Loops operating in rule-based mode")
    
    async def capture_task_outcome(
        self,
        task: Task,
        execution_result: TaskExecutionOutput,
        execution_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Capture and analyze task execution outcome for learning
        
        Args:
            task: The executed task
            execution_result: The execution outcome
            execution_metadata: Additional metadata (duration, resources used, etc.)
        
        Returns:
            Dictionary containing extracted learnings
        """
        
        if not self.learning_enabled:
            logger.debug("Learning loops disabled")
            return {}
        
        logger.info(f"🔄 Capturing learning from task: {task.name} (status: {execution_result.status})")
        
        # Extract basic outcome data
        outcome_data = {
            "task_id": str(task.id),
            "task_name": task.name,
            "task_description": task.description,
            "task_type": task.task_type,
            "execution_status": execution_result.status,
            "execution_summary": execution_result.summary,
            "error_message": execution_result.error_message,
            "execution_time": execution_metadata.get("duration") if execution_metadata else None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Analyze outcome to extract learnings
        if self.ai_available:
            learnings = await self._ai_analyze_outcome(outcome_data, task, execution_result)
        else:
            learnings = await self._rule_based_analysis(outcome_data, execution_result)
        
        # Store learnings in workspace memory
        if learnings:
            await self._update_workspace_memory(task.workspace_id, learnings)
        
        return learnings
    
    async def _ai_analyze_outcome(
        self,
        outcome_data: Dict[str, Any],
        task: Task,
        execution_result: TaskExecutionOutput
    ) -> Dict[str, Any]:
        """Use AI to analyze task outcome and extract learnings"""
        
        try:
            # Prepare detailed context for AI analysis
            context = {
                "task": {
                    "name": task.name,
                    "description": task.description,
                    "priority": task.priority,
                    "context": task.context
                },
                "execution": {
                    "status": execution_result.status,
                    "summary": execution_result.summary,
                    "error": execution_result.error_message,
                    "output": str(execution_result.output)[:500] if execution_result.output else None
                },
                "metadata": outcome_data
            }
            
            prompt = f"""
            Analyze this task execution outcome and extract learnings for future improvements.
            
            Context: {json.dumps(context, indent=2)}
            
            Extract:
            1. What patterns led to success or failure?
            2. What can be learned from this execution?
            3. What best practices emerged?
            4. What anti-patterns were observed?
            5. How can similar tasks be improved in the future?
            
            Respond with JSON:
            {{
                "outcome_type": "success/failure/partial",
                "confidence": 0.0-1.0,
                "patterns": [
                    {{
                        "type": "success_pattern/failure_lesson/best_practice/anti_pattern",
                        "pattern": "description of the pattern",
                        "keywords": ["keyword1", "keyword2"],
                        "recommendation": "how to apply or avoid this pattern"
                    }}
                ],
                "optimization_opportunities": ["opportunity1", "opportunity2"],
                "memory_update": {{
                    "should_remember": true/false,
                    "importance": "high/medium/low",
                    "retention_days": 30
                }}
            }}
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a task execution analyst extracting learnings."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            analysis = eval(response.choices[0].message.content)
            
            # Structure learnings for memory storage
            learnings = {
                "outcome_type": analysis["outcome_type"],
                "confidence": analysis["confidence"],
                "patterns": analysis["patterns"],
                "optimization_opportunities": analysis["optimization_opportunities"],
                "task_context": {
                    "task_name": task.name,
                    "task_type": task.task_type,
                    "execution_status": execution_result.status
                },
                "memory_metadata": analysis["memory_update"]
            }
            
            logger.info(f"🧠 AI extracted {len(analysis['patterns'])} patterns from task execution")
            return learnings
            
        except Exception as e:
            logger.error(f"Error in AI outcome analysis: {e}")
            # Fallback to rule-based
            return await self._rule_based_analysis(outcome_data, execution_result)
    
    async def _rule_based_analysis(
        self,
        outcome_data: Dict[str, Any],
        execution_result: TaskExecutionOutput
    ) -> Dict[str, Any]:
        """Rule-based analysis of task outcomes"""
        
        patterns = []
        
        # Success pattern detection
        if execution_result.status == TaskStatus.COMPLETED:
            pattern = {
                "type": LearningOutcome.SUCCESS_PATTERN.value,
                "pattern": f"Task '{outcome_data['task_name']}' completed successfully",
                "keywords": outcome_data["task_name"].lower().split()[:3],
                "recommendation": "Replicate this approach for similar tasks"
            }
            
            # Check for fast execution
            if outcome_data.get("execution_time") and outcome_data["execution_time"] < 30:
                pattern["pattern"] += " with fast execution time"
                pattern["recommendation"] = "This approach is efficient, prioritize for similar tasks"
            
            patterns.append(pattern)
        
        # Failure lesson detection
        elif execution_result.status == TaskStatus.FAILED:
            pattern = {
                "type": LearningOutcome.FAILURE_LESSON.value,
                "pattern": f"Task failed: {execution_result.error_message or 'Unknown error'}",
                "keywords": ["failure"] + outcome_data["task_name"].lower().split()[:2],
                "recommendation": "Avoid this approach or add better error handling"
            }
            
            # Analyze common failure patterns
            if execution_result.error_message:
                error_lower = execution_result.error_message.lower()
                if "timeout" in error_lower:
                    pattern["recommendation"] = "Increase timeout or optimize execution"
                elif "not found" in error_lower:
                    pattern["recommendation"] = "Verify resources exist before execution"
                elif "permission" in error_lower or "unauthorized" in error_lower:
                    pattern["recommendation"] = "Check permissions and credentials"
            
            patterns.append(pattern)
        
        # Best practice detection
        if execution_result.output and len(str(execution_result.output)) > 100:
            patterns.append({
                "type": LearningOutcome.BEST_PRACTICE.value,
                "pattern": "Task produced substantial output",
                "keywords": ["productive", "output"],
                "recommendation": "This task type generates good deliverables"
            })
        
        return {
            "outcome_type": "success" if execution_result.status == TaskStatus.COMPLETED else "failure",
            "confidence": 0.7,  # Rule-based has moderate confidence
            "patterns": patterns,
            "optimization_opportunities": [],
            "task_context": {
                "task_name": outcome_data["task_name"],
                "execution_status": execution_result.status
            },
            "memory_metadata": {
                "should_remember": len(patterns) > 0,
                "importance": "medium",
                "retention_days": 30
            }
        }
    
    async def _update_workspace_memory(
        self,
        workspace_id: str,
        learnings: Dict[str, Any]
    ) -> None:
        """Update workspace memory with extracted learnings"""
        
        if not learnings.get("memory_metadata", {}).get("should_remember", False):
            logger.debug("Learning not significant enough to store")
            return
        
        try:
            from services.workspace_memory_system import workspace_memory_system
            
            # Separate patterns by type
            success_patterns = []
            failure_lessons = []
            best_practices = []
            
            for pattern in learnings.get("patterns", []):
                pattern_data = {
                    "pattern": pattern["pattern"],
                    "keywords": pattern.get("keywords", []),
                    "recommendation": pattern.get("recommendation", ""),
                    "timestamp": datetime.utcnow().isoformat(),
                    "confidence": learnings.get("confidence", 0.5)
                }
                
                if pattern["type"] == LearningOutcome.SUCCESS_PATTERN.value:
                    success_patterns.append(pattern_data)
                elif pattern["type"] == LearningOutcome.FAILURE_LESSON.value:
                    failure_lessons.append(pattern_data)
                elif pattern["type"] == LearningOutcome.BEST_PRACTICE.value:
                    best_practices.append(pattern_data)
            
            # Store in workspace memory
            memory_entry = {
                "workspace_id": workspace_id,
                "memory_type": "task_execution_learning",
                "content": {
                    "outcome_type": learnings["outcome_type"],
                    "task_context": learnings.get("task_context", {}),
                    "success_patterns": success_patterns,
                    "failure_lessons": failure_lessons,
                    "best_practices": best_practices,
                    "optimization_opportunities": learnings.get("optimization_opportunities", [])
                },
                "metadata": {
                    "importance": learnings["memory_metadata"]["importance"],
                    "retention_days": learnings["memory_metadata"]["retention_days"],
                    "created_at": datetime.utcnow().isoformat()
                }
            }
            
            await workspace_memory_system.store_memory(memory_entry)
            
            logger.info(f"📝 Stored {len(success_patterns)} success patterns, "
                       f"{len(failure_lessons)} failure lessons, "
                       f"{len(best_practices)} best practices in workspace memory")
            
        except Exception as e:
            logger.error(f"Failed to update workspace memory: {e}")
    
    async def batch_learn_from_recent_tasks(
        self,
        workspace_id: str,
        hours_back: int = 24
    ) -> Dict[str, Any]:
        """
        Batch learning from recent task executions in a workspace
        
        Analyzes multiple recent tasks to identify trends and patterns
        """
        
        try:
            # Get recent completed/failed tasks
            since_time = (datetime.utcnow() - timedelta(hours=hours_back)).isoformat()
            
            tasks_response = supabase.table("tasks") \
                .select("*") \
                .eq("workspace_id", workspace_id) \
                .in_("status", [TaskStatus.COMPLETED, TaskStatus.FAILED]) \
                .gte("updated_at", since_time) \
                .limit(self.batch_size) \
                .execute()
            
            if not tasks_response.data:
                logger.info(f"No recent tasks to learn from in workspace {workspace_id}")
                return {}
            
            logger.info(f"🔄 Batch learning from {len(tasks_response.data)} recent tasks")
            
            # Analyze each task
            all_learnings = []
            for task_data in tasks_response.data:
                try:
                    # Create Task and TaskExecutionOutput objects
                    from models import Task
                    task = Task.model_validate(task_data)
                    
                    execution_result = TaskExecutionOutput(
                        task_id=task.id,
                        status=task.status,
                        summary=task_data.get("execution_summary", ""),
                        error_message=task_data.get("error_message"),
                        output=task_data.get("output")
                    )
                    
                    learnings = await self.capture_task_outcome(task, execution_result)
                    if learnings:
                        all_learnings.append(learnings)
                        
                except Exception as e:
                    logger.warning(f"Failed to learn from task {task_data.get('id')}: {e}")
            
            # Aggregate learnings
            if all_learnings:
                aggregated = await self._aggregate_learnings(all_learnings)
                logger.info(f"✅ Batch learning completed: {len(aggregated.get('patterns', []))} patterns identified")
                return aggregated
            
            return {}
            
        except Exception as e:
            logger.error(f"Error in batch learning: {e}")
            return {}
    
    async def _aggregate_learnings(self, learnings_list: List[Dict]) -> Dict[str, Any]:
        """Aggregate multiple learnings into consolidated insights"""
        
        all_patterns = []
        all_opportunities = []
        
        for learning in learnings_list:
            all_patterns.extend(learning.get("patterns", []))
            all_opportunities.extend(learning.get("optimization_opportunities", []))
        
        # Deduplicate and count frequency
        pattern_frequency = {}
        for pattern in all_patterns:
            key = f"{pattern['type']}:{pattern['pattern'][:50]}"
            if key not in pattern_frequency:
                pattern_frequency[key] = {
                    "pattern": pattern,
                    "count": 0
                }
            pattern_frequency[key]["count"] += 1
        
        # Sort by frequency
        top_patterns = sorted(
            pattern_frequency.values(),
            key=lambda x: x["count"],
            reverse=True
        )[:10]  # Top 10 patterns
        
        return {
            "patterns": [p["pattern"] for p in top_patterns],
            "pattern_frequency": {p["pattern"]["pattern"][:50]: p["count"] for p in top_patterns},
            "optimization_opportunities": list(set(all_opportunities))[:5],
            "total_tasks_analyzed": len(learnings_list)
        }
    
    async def get_learning_recommendations(
        self,
        workspace_id: str,
        task_type: Optional[str] = None
    ) -> List[str]:
        """
        Get learning-based recommendations for a workspace or task type
        
        Returns actionable recommendations based on accumulated learnings
        """
        
        try:
            from services.workspace_memory_system import workspace_memory_system
            
            # Query relevant memories
            memories = await workspace_memory_system.get_relevant_insights(
                workspace_id=workspace_id,
                context_type="task_execution_learning",
                limit=20
            )
            
            if not memories:
                return ["No learning history available yet"]
            
            recommendations = []
            
            # Extract recommendations from patterns
            for memory in memories.get("success_patterns", []):
                if memory.get("recommendation"):
                    recommendations.append(f"✅ {memory['recommendation']}")
            
            for memory in memories.get("failure_lessons", []):
                if memory.get("recommendation"):
                    recommendations.append(f"⚠️ {memory['recommendation']}")
            
            for memory in memories.get("best_practices", []):
                if memory.get("recommendation"):
                    recommendations.append(f"💡 {memory['recommendation']}")
            
            # Deduplicate and limit
            unique_recommendations = list(dict.fromkeys(recommendations))[:10]
            
            if not unique_recommendations:
                unique_recommendations = ["Continue current practices, no specific improvements identified"]
            
            return unique_recommendations
            
        except Exception as e:
            logger.error(f"Error getting learning recommendations: {e}")
            return ["Unable to retrieve recommendations at this time"]

# Global instance
systematic_learning_loops = SystematicLearningLoops()