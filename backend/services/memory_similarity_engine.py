"""
Memory Similarity Engine - AI-Powered Insight Retrieval
Implements semantic similarity search for relevant insights based on task context
"""

import logging
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import asyncio

from services.ai_provider_abstraction import ai_provider_manager
from database import get_memory_insights, add_memory_insight

logger = logging.getLogger(__name__)

class MemorySimilarityEngine:
    """
    Retrieves relevant insights from memory based on semantic similarity.
    Implements Pillar 6: Memory System (learning and applying past knowledge)
    """
    
    def __init__(self):
        self.similarity_threshold = 0.7
        self.max_insights_per_query = 5
        self.insight_cache = {}
        self.cache_expiry_minutes = 30
    
    async def get_relevant_insights(
        self, 
        workspace_id: str, 
        task_context: Dict[str, Any],
        insight_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get insights that are semantically similar to the current task context.
        
        Args:
            workspace_id: Workspace to search in
            task_context: Context about the current task (name, description, type, etc.)
            insight_types: Optional filter for specific insight types
            
        Returns:
            List of relevant insights with similarity scores
        """
        try:
            logger.info(f"🧠 Searching for relevant insights in workspace {workspace_id}")
            
            # Get all insights from workspace
            all_insights = await get_memory_insights(workspace_id, limit=50)
            
            if not all_insights:
                logger.info("No insights found in workspace memory")
                return []
            
            # Filter by insight types if specified
            if insight_types:
                all_insights = [
                    insight for insight in all_insights 
                    if insight.get('insight_type') in insight_types
                ]
            
            # Calculate similarity scores using AI
            relevant_insights = await self._calculate_similarity_scores(
                task_context, all_insights
            )
            
            # Filter by similarity threshold and limit results
            filtered_insights = [
                insight for insight in relevant_insights
                if insight.get('similarity_score', 0) >= self.similarity_threshold
            ]
            
            # Sort by similarity score and limit
            filtered_insights.sort(
                key=lambda x: x.get('similarity_score', 0), 
                reverse=True
            )
            
            results = filtered_insights[:self.max_insights_per_query]
            
            logger.info(f"✅ Found {len(results)} relevant insights (threshold: {self.similarity_threshold})")
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving relevant insights: {e}")
            return []
    
    async def _calculate_similarity_scores(
        self, 
        task_context: Dict[str, Any], 
        insights: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Calculate semantic similarity between task context and insights"""
        try:
            # Prepare context summary for AI comparison
            context_summary = self._create_context_summary(task_context)
            
            # Create batches for efficient processing
            batch_size = 10
            scored_insights = []
            
            for i in range(0, len(insights), batch_size):
                batch = insights[i:i + batch_size]
                batch_scores = await self._score_insight_batch(context_summary, batch)
                scored_insights.extend(batch_scores)
            
            return scored_insights
            
        except Exception as e:
            logger.error(f"Error calculating similarity scores: {e}")
            return insights  # Return original insights without scores
    
    def _create_context_summary(self, task_context: Dict[str, Any]) -> str:
        """Create a concise summary of task context for AI comparison"""
        summary_parts = []
        
        # Task name and description
        if task_context.get('name'):
            summary_parts.append(f"Task: {task_context['name']}")
        
        if task_context.get('description'):
            summary_parts.append(f"Description: {task_context['description']}")
        
        # Task type/category
        if task_context.get('type'):
            summary_parts.append(f"Type: {task_context['type']}")
        
        # Domain/skills
        if task_context.get('skills'):
            summary_parts.append(f"Skills: {', '.join(task_context['skills'])}")
        
        # Agent assignment
        if task_context.get('agent_role'):
            summary_parts.append(f"Agent Role: {task_context['agent_role']}")
        
        return " | ".join(summary_parts)
    
    async def _score_insight_batch(
        self, 
        context_summary: str, 
        insights: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Score a batch of insights for similarity to task context"""
        try:
            # Prepare insights for AI evaluation
            insights_summary = []
            for i, insight in enumerate(insights):
                insight_text = f"{i}: {insight.get('insight_type', 'unknown')} - {insight.get('content', '')[:200]}"
                insights_summary.append(insight_text)
            
            prompt = f"""Compare this task context with the following insights and rate their relevance.

Task Context: {context_summary}

Insights to evaluate:
{chr(10).join(insights_summary)}

For each insight, provide a relevance score from 0.0 to 1.0 where:
- 1.0 = Extremely relevant, directly applicable
- 0.8 = Highly relevant, similar task/domain
- 0.6 = Moderately relevant, some overlap
- 0.4 = Slightly relevant, tangential connection
- 0.2 = Barely relevant, minimal connection
- 0.0 = Not relevant, no connection

Return JSON:
{{
    "scores": [
        {{"insight_index": 0, "score": 0.8, "reason": "why relevant"}},
        {{"insight_index": 1, "score": 0.3, "reason": "why not very relevant"}}
    ]
}}"""

            agent = {
                "name": "MemorySimilarityAgent",
                "model": "gpt-4o-mini",
                "instructions": "You are an expert at identifying semantic similarity between task contexts and historical insights."
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
                scores_data = response.get('scores', [])
                
                # Apply scores to insights
                for score_entry in scores_data:
                    idx = score_entry.get('insight_index')
                    score = score_entry.get('score', 0.0)
                    reason = score_entry.get('reason', '')
                    
                    if 0 <= idx < len(insights):
                        insights[idx]['similarity_score'] = score
                        insights[idx]['similarity_reason'] = reason
            
            return insights
            
        except Exception as e:
            logger.error(f"Error scoring insight batch: {e}")
            # Return with default low scores
            for insight in insights:
                insight['similarity_score'] = 0.1
                insight['similarity_reason'] = 'Error during scoring'
            return insights
    
    async def find_similar_task_patterns(
        self, 
        workspace_id: str, 
        task_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find insights from similar tasks that succeeded or failed"""
        try:
            # Look for specific insight types related to task patterns
            relevant_types = [
                'SUCCESS_PATTERN',
                'FAILURE_LESSON',
                'OPPORTUNITY',
                'CONSTRAINT'
            ]
            
            pattern_insights = await self.get_relevant_insights(
                workspace_id, 
                task_context, 
                insight_types=relevant_types
            )
            
            return pattern_insights
            
        except Exception as e:
            logger.error(f"Error finding similar task patterns: {e}")
            return []
    
    async def get_agent_specific_insights(
        self, 
        workspace_id: str, 
        agent_id: str,
        task_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get insights specific to an agent's past performance"""
        try:
            # Get all insights and filter for agent-specific ones
            all_insights = await get_memory_insights(workspace_id, limit=50)
            
            agent_insights = []
            for insight in all_insights:
                insight_content = insight.get('content', '')
                if (agent_id in insight_content or 
                    'agent_id' in insight.get('metadata', {}) and 
                    insight['metadata']['agent_id'] == agent_id):
                    agent_insights.append(insight)
            
            # Score for relevance to current task
            if agent_insights:
                relevant_insights = await self._calculate_similarity_scores(
                    task_context, agent_insights
                )
                
                # Filter and sort
                filtered = [
                    insight for insight in relevant_insights
                    if insight.get('similarity_score', 0) >= 0.5  # Lower threshold for agent-specific
                ]
                
                filtered.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
                return filtered[:3]  # Top 3 agent-specific insights
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting agent-specific insights: {e}")
            return []
    
    async def store_task_execution_insight(
        self, 
        workspace_id: str, 
        task_context: Dict[str, Any],
        execution_result: Dict[str, Any],
        agent_id: Optional[str] = None
    ) -> bool:
        """Store insight from task execution for future learning"""
        try:
            # Determine insight type based on execution result
            success = execution_result.get('success', False)
            
            if success:
                insight_type = 'SUCCESS_PATTERN'
                insight_content = self._create_success_insight(task_context, execution_result)
            else:
                insight_type = 'FAILURE_LESSON'
                insight_content = self._create_failure_insight(task_context, execution_result)
            
            # Store insight
            await add_memory_insight(
                workspace_id=workspace_id,
                insight_type=insight_type,
                content=insight_content,
                task_id=task_context.get('task_id')
            )
            
            logger.info(f"✅ Stored {insight_type} insight for future learning")
            return True
            
        except Exception as e:
            logger.error(f"Error storing task execution insight: {e}")
            return False
    
    def _create_success_insight(
        self, 
        task_context: Dict[str, Any], 
        execution_result: Dict[str, Any]
    ) -> str:
        """Create insight from successful task execution."""
        insight_data = {
            'pattern_type': 'success',
            'task_name': task_context.get('name'),
            'task_type': task_context.get('type'),
            'agent_role': task_context.get('agent_role'),
            'execution_time': execution_result.get('execution_time'),
            'tools_used': execution_result.get('tools_used', []),
            'success_factors': execution_result.get('success_factors', ['Completed successfully']),
            'key_insights': execution_result.get('key_insights', [str(execution_result.get('result'))[:100]]),
            'timestamp': datetime.now().isoformat()
        }
        
        return json.dumps(insight_data, indent=2)
    
    def _create_failure_insight(
        self, 
        task_context: Dict[str, Any], 
        execution_result: Dict[str, Any]
    ) -> str:
        """Create insight from failed task execution."""
        insight_data = {
            'pattern_type': 'failure',
            'task_name': task_context.get('name'),
            'task_type': task_context.get('type'),
            'agent_role': task_context.get('agent_role'),
            'error_type': execution_result.get('error_type'),
            'error_message': execution_result.get('error_message'),
            'failure_reasons': execution_result.get('failure_reasons', ['Execution failed']),
            'lessons_learned': execution_result.get('lessons_learned', ['Check error logs for details']),
            'prevention_strategies': execution_result.get('prevention_strategies', ['Review task logic and inputs']),
            'timestamp': datetime.now().isoformat()
        }
        
        return json.dumps(insight_data, indent=2)


# Create singleton instance
memory_similarity_engine = MemorySimilarityEngine()
