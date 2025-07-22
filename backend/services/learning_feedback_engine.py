"""
Learning Feedback Engine - Continuous Learning from Task Execution Results
Analyzes task execution patterns and creates actionable insights for future improvement
"""

import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter

from database import (
    get_memory_insights, 
    add_memory_insight, 
    get_task_execution_stats_python,
    get_workspace_execution_stats
)
from services.ai_provider_abstraction import ai_provider_manager

logger = logging.getLogger(__name__)

class LearningFeedbackEngine:
    """
    Analyzes task execution patterns to create actionable insights.
    Implements Pillar 6: Memory System (continuous learning and improvement)
    """
    
    def __init__(self):
        self.analysis_window_days = 7  # Look back 7 days for patterns
        self.minimum_executions_for_pattern = 3
        self.success_rate_threshold = 0.7  # 70% success rate threshold
        
    async def analyze_workspace_performance(self, workspace_id: str) -> Dict[str, Any]:
        """Comprehensive analysis of workspace performance patterns"""
        try:
            logger.info(f"🔍 Analyzing workspace {workspace_id} performance patterns")
            
            # Get execution statistics
            execution_stats = await get_workspace_execution_stats(workspace_id)
            
            if not execution_stats or execution_stats.get('total_executions', 0) < 3:
                logger.info("Not enough execution data for meaningful analysis")
                return {"status": "insufficient_data", "insights_generated": 0}
            
            # Analyze different aspects
            analyses = await asyncio.gather(
                self._analyze_task_success_patterns(workspace_id),
                self._analyze_failure_patterns(workspace_id),
                self._analyze_agent_performance_patterns(workspace_id),
                self._analyze_execution_timing_patterns(workspace_id),
                return_exceptions=True
            )
            
            insights_generated = 0
            for analysis in analyses:
                if isinstance(analysis, Exception):
                    logger.error(f"Analysis failed: {analysis}")
                    continue
                insights_generated += analysis.get('insights_generated', 0)
            
            logger.info(f"✅ Generated {insights_generated} insights from performance analysis")
            return {
                "status": "completed",
                "insights_generated": insights_generated,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing workspace performance: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _analyze_task_success_patterns(self, workspace_id: str) -> Dict[str, Any]:
        """Analyze patterns in successful task execution"""
        try:
            # Get recent successful executions
            cutoff_date = datetime.now() - timedelta(days=self.analysis_window_days)
            
            # This would normally query task executions, but we'll simulate with task data
            from database import list_tasks
            tasks = await list_tasks(workspace_id, status="completed")
            
            if len(tasks) < self.minimum_executions_for_pattern:
                return {"insights_generated": 0}
            
            # Group tasks by similarity
            task_groups = await self._group_similar_tasks(tasks)
            insights_generated = 0
            
            for group_name, group_tasks in task_groups.items():
                if len(group_tasks) >= self.minimum_executions_for_pattern:
                    # Create success pattern insight
                    success_pattern = await self._create_success_pattern_insight(group_tasks)
                    
                    if success_pattern:
                        await add_memory_insight(
                            workspace_id=workspace_id,
                            insight_type="task_success_pattern",
                            content=json.dumps(success_pattern, indent=2),
                            agent_role="learning_system"
                        )
                        insights_generated += 1
            
            logger.info(f"✅ Generated {insights_generated} task success pattern insights")
            return {"insights_generated": insights_generated}
            
        except Exception as e:
            logger.error(f"Error analyzing task success patterns: {e}")
            return {"insights_generated": 0}
    
    async def _analyze_failure_patterns(self, workspace_id: str) -> Dict[str, Any]:
        """Analyze patterns in task failures to create prevention insights"""
        try:
            # Get recent failed tasks
            from database import list_tasks
            failed_tasks = await list_tasks(workspace_id, status="failed")
            
            if len(failed_tasks) < 2:  # Need at least 2 failures to see patterns
                return {"insights_generated": 0}
            
            # Analyze failure patterns
            failure_insights = await self._analyze_failure_commonalities(failed_tasks)
            insights_generated = 0
            
            for insight in failure_insights:
                await add_memory_insight(
                    workspace_id=workspace_id,
                    insight_type="task_failure_lesson",
                    content=json.dumps(insight, indent=2),
                    agent_role="learning_system"
                )
                insights_generated += 1
            
            logger.info(f"✅ Generated {insights_generated} failure pattern insights")
            return {"insights_generated": insights_generated}
            
        except Exception as e:
            logger.error(f"Error analyzing failure patterns: {e}")
            return {"insights_generated": 0}
    
    async def _analyze_agent_performance_patterns(self, workspace_id: str) -> Dict[str, Any]:
        """Analyze individual agent performance patterns"""
        try:
            # Get agent performance data
            from database import list_tasks
            all_tasks = await list_tasks(workspace_id)
            
            if not all_tasks:
                return {"insights_generated": 0}
            
            # Group by agent
            agent_performance = defaultdict(lambda: {"completed": 0, "failed": 0, "total": 0})
            
            for task in all_tasks:
                agent_id = task.get('agent_id')
                if not agent_id:
                    continue
                
                agent_performance[agent_id]["total"] += 1
                if task.get('status') == 'completed':
                    agent_performance[agent_id]["completed"] += 1
                elif task.get('status') == 'failed':
                    agent_performance[agent_id]["failed"] += 1
            
            # Create insights for agents with significant performance data
            insights_generated = 0
            
            for agent_id, stats in agent_performance.items():
                if stats["total"] >= self.minimum_executions_for_pattern:
                    success_rate = stats["completed"] / stats["total"]
                    
                    insight = await self._create_agent_performance_insight(
                        agent_id, stats, success_rate
                    )
                    
                    if insight:
                        await add_memory_insight(
                            workspace_id=workspace_id,
                            insight_type="agent_performance_insight",
                            content=json.dumps(insight, indent=2),
                            agent_role="learning_system"
                        )
                        insights_generated += 1
            
            logger.info(f"✅ Generated {insights_generated} agent performance insights")
            return {"insights_generated": insights_generated}
            
        except Exception as e:
            logger.error(f"Error analyzing agent performance: {e}")
            return {"insights_generated": 0}
    
    async def _analyze_execution_timing_patterns(self, workspace_id: str) -> Dict[str, Any]:
        """Analyze execution timing patterns to optimize scheduling"""
        try:
            from database import list_tasks
            all_tasks = await list_tasks(workspace_id)
            
            if not all_tasks:
                return {"insights_generated": 0}
            
            # Analyze task timing patterns
            timing_insights = await self._analyze_task_timing_patterns(all_tasks)
            insights_generated = 0
            
            for insight in timing_insights:
                await add_memory_insight(
                    workspace_id=workspace_id,
                    insight_type="OPPORTUNITY",
                    content=json.dumps(insight, indent=2),
                    agent_role="learning_system"
                )
                insights_generated += 1
            
            logger.info(f"✅ Generated {insights_generated} timing optimization insights")
            return {"insights_generated": insights_generated}
            
        except Exception as e:
            logger.error(f"Error analyzing timing patterns: {e}")
            return {"insights_generated": 0}
    
    async def _group_similar_tasks(self, tasks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group similar tasks together for pattern analysis"""
        try:
            # Use AI to group similar tasks
            task_summaries = []
            for task in tasks:
                summary = f"{task.get('name', 'unnamed')}: {task.get('description', 'no description')[:100]}"
                task_summaries.append(summary)
            
            if not task_summaries:
                return {}
            
            prompt = f"""Group these tasks by similarity. Look for common patterns in task types, objectives, or domains.

Tasks:
{chr(10).join(f"{i+1}. {summary}" for i, summary in enumerate(task_summaries))}

Return JSON with groups:
{{
    "group_name_1": [1, 3, 5],  // Task indices in this group
    "group_name_2": [2, 4],
    "group_name_3": [6, 7, 8]
}}"""

            agent = {
                "name": "TaskGroupingAgent",
                "model": "gpt-4o-mini",
                "instructions": "You are an expert at identifying patterns and grouping similar tasks."
            }
            
            response = await ai_provider_manager.call_ai(
                provider_type='openai_sdk',
                agent=agent,
                prompt=prompt,
                max_tokens=1000,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            if response and isinstance(response, dict):
                groups = response.get('groups', {})
                
                # Convert indices to actual tasks
                task_groups = {}
                for group_name, indices in groups.items():
                    group_tasks = []
                    for idx in indices:
                        if 0 <= idx-1 < len(tasks):  # Convert 1-based to 0-based indexing
                            group_tasks.append(tasks[idx-1])
                    if group_tasks:
                        task_groups[group_name] = group_tasks
                
                return task_groups
            
            # Fallback: group all tasks together
            return {"all_tasks": tasks}
            
        except Exception as e:
            logger.error(f"Error grouping similar tasks: {e}")
            return {"all_tasks": tasks}
    
    async def _create_success_pattern_insight(self, tasks: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Create insight from successful task patterns"""
        try:
            # Extract common elements from successful tasks
            task_names = [task.get('name', 'unnamed') for task in tasks]
            task_descriptions = [task.get('description', '') for task in tasks]
            
            # Use AI to analyze success patterns
            prompt = f"""Analyze these successful tasks and identify the key success patterns.

Successful Tasks:
{chr(10).join(f"- {name}: {desc[:200]}" for name, desc in zip(task_names, task_descriptions))}

Identify:
1. Common characteristics that led to success
2. Patterns in task structure or approach
3. Key success factors
4. Recommendations for similar future tasks

Return JSON:
{{
    "pattern_name": "descriptive name",
    "success_factors": ["factor1", "factor2", "factor3"],
    "task_characteristics": ["characteristic1", "characteristic2"],
    "recommendations": ["recommendation1", "recommendation2"],
    "confidence_score": 0.85
}}"""

            agent = {
                "name": "SuccessPatternAnalyzer",
                "model": "gpt-4o-mini",
                "instructions": "You are an expert at identifying success patterns in task execution."
            }
            
            response = await ai_provider_manager.call_ai(
                provider_type='openai_sdk',
                agent=agent,
                prompt=prompt,
                max_tokens=800,
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            if response and isinstance(response, dict):
                pattern_data = response.copy()
                pattern_data['task_count'] = len(tasks)
                pattern_data['analysis_timestamp'] = datetime.now().isoformat()
                return pattern_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating success pattern insight: {e}")
            return None
    
    async def _analyze_failure_commonalities(self, failed_tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze common factors in task failures"""
        try:
            if not failed_tasks:
                return []
            
            # Group failure reasons
            failure_reasons = []
            for task in failed_tasks:
                result = task.get('result', {})
                if isinstance(result, dict):
                    error_message = result.get('error_message', 'Unknown error')
                    failure_reasons.append(f"{task.get('name', 'unnamed')}: {error_message}")
                else:
                    failure_reasons.append(f"{task.get('name', 'unnamed')}: No error details")
            
            # Use AI to analyze failure patterns
            prompt = f"""Analyze these task failures and identify common patterns to prevent future failures.

Failed Tasks:
{chr(10).join(f"- {reason}" for reason in failure_reasons)}

Identify:
1. Common failure patterns
2. Root causes
3. Prevention strategies
4. Warning signs to watch for

Return JSON array of insights:
[
    {{
        "failure_pattern": "description of pattern",
        "root_causes": ["cause1", "cause2"],
        "prevention_strategies": ["strategy1", "strategy2"],
        "warning_signs": ["sign1", "sign2"],
        "affected_task_count": 3
    }}
]"""

            agent = {
                "name": "FailurePatternAnalyzer",
                "model": "gpt-4o-mini",
                "instructions": "You are an expert at analyzing failure patterns and creating prevention strategies."
            }
            
            response = await ai_provider_manager.call_ai(
                provider_type='openai_sdk',
                agent=agent,
                prompt=prompt,
                max_tokens=1000,
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            if response and isinstance(response, dict) and 'insights' in response:
                insights = response['insights']
                if isinstance(insights, list):
                    # Add metadata to each insight
                    for insight in insights:
                        insight['analysis_timestamp'] = datetime.now().isoformat()
                        insight['total_failures_analyzed'] = len(failed_tasks)
                    return insights
            
            return []
            
        except Exception as e:
            logger.error(f"Error analyzing failure commonalities: {e}")
            return []
    
    async def _create_agent_performance_insight(
        self, 
        agent_id: str, 
        stats: Dict[str, int], 
        success_rate: float
    ) -> Optional[Dict[str, Any]]:
        """Create insight about agent performance"""
        try:
            performance_category = (
                "high_performer" if success_rate >= 0.8 else
                "average_performer" if success_rate >= 0.6 else
                "needs_improvement"
            )
            
            insight = {
                "agent_id": agent_id,
                "performance_category": performance_category,
                "success_rate": success_rate,
                "total_tasks": stats["total"],
                "completed_tasks": stats["completed"],
                "failed_tasks": stats["failed"],
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            # Add recommendations based on performance
            if performance_category == "high_performer":
                insight["recommendations"] = [
                    "Consider assigning more complex tasks to this agent",
                    "Use this agent as a model for similar task types",
                    "Monitor for any performance degradation"
                ]
            elif performance_category == "needs_improvement":
                insight["recommendations"] = [
                    "Review recent failures for patterns",
                    "Consider additional training or different task types",
                    "Monitor closely for improvement"
                ]
            else:
                insight["recommendations"] = [
                    "Maintain current performance level",
                    "Look for optimization opportunities"
                ]
            
            return insight
            
        except Exception as e:
            logger.error(f"Error creating agent performance insight: {e}")
            return None
    
    async def _analyze_task_timing_patterns(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze task execution timing patterns"""
        try:
            # Extract timing data
            timing_data = []
            for task in tasks:
                created_at = task.get('created_at')
                updated_at = task.get('updated_at')
                
                if created_at and updated_at:
                    # Simple duration calculation (would be more sophisticated in real implementation)
                    timing_data.append({
                        'task_name': task.get('name', 'unnamed'),
                        'status': task.get('status'),
                        'created_at': created_at,
                        'updated_at': updated_at
                    })
            
            if len(timing_data) < 3:
                return []
            
            # Create basic timing insights
            insights = []
            
            # Quick tasks vs slow tasks
            completed_tasks = [t for t in timing_data if t['status'] == 'completed']
            if len(completed_tasks) >= 3:
                insight = {
                    "pattern_type": "execution_timing",
                    "total_completed_tasks": len(completed_tasks),
                    "recommendations": [
                        "Monitor task complexity vs execution time",
                        "Consider task breakdown for long-running tasks",
                        "Optimize resource allocation based on timing patterns"
                    ],
                    "analysis_timestamp": datetime.now().isoformat()
                }
                insights.append(insight)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error analyzing task timing patterns: {e}")
            return []
    
    async def generate_periodic_insights(self, workspace_id: str) -> Dict[str, Any]:
        """Generate periodic insights for workspace (to be called by scheduler)"""
        try:
            logger.info(f"🔄 Generating periodic insights for workspace {workspace_id}")
            
            # Check if enough time has passed since last analysis
            recent_insights = await get_memory_insights(workspace_id, limit=5)
            
            if recent_insights:
                last_analysis = recent_insights[0].get('created_at')
                if last_analysis:
                    from datetime import datetime
                    last_time = datetime.fromisoformat(last_analysis.replace('Z', '+00:00'))
                    if datetime.now() - last_time < timedelta(hours=6):
                        logger.info("Recent analysis already exists, skipping")
                        return {"status": "skipped", "reason": "recent_analysis_exists"}
            
            # Run comprehensive analysis
            analysis_result = await self.analyze_workspace_performance(workspace_id)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error generating periodic insights: {e}")
            return {"status": "error", "error": str(e)}


# Create singleton instance
learning_feedback_engine = LearningFeedbackEngine()