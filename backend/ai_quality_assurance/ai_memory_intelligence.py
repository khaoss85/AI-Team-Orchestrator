# backend/ai_quality_assurance/ai_memory_intelligence.py

import logging
import json
import os
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)

class AIMemoryIntelligence:
    """
    🤖 AI-DRIVEN MEMORY INTELLIGENCE SYSTEM
    
    Extracts actionable insights from task completion patterns and workspace memory
    to drive automatic course correction and intelligent decision making.
    """
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = None
        
        if self.openai_api_key:
            try:
                from openai import AsyncOpenAI
                self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
                self.ai_available = True
            except ImportError:
                self.ai_available = False
                logger.warning("OpenAI not available for memory intelligence")
        else:
            self.ai_available = False
    
    async def extract_actionable_insights(
        self, 
        completed_task: Dict[str, Any], 
        task_result: Dict[str, Any], 
        workspace_context: Dict[str, Any],
        historical_insights: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        🤖 AI-DRIVEN ACTIONABLE INSIGHT EXTRACTION
        
        Analyzes task completion to extract specific, actionable insights
        that can guide future decisions and improvements.
        """
        try:
            # 1. Get task performance metrics
            performance_data = self._extract_performance_metrics(completed_task, task_result)
            
            # 2. Use AI to extract strategic insights
            if self.ai_available:
                ai_insights = await self._ai_extract_strategic_insights(
                    completed_task, task_result, performance_data, workspace_context
                )
                if ai_insights:
                    logger.info(f"🧠 AI INSIGHTS: Extracted {len(ai_insights)} actionable insights")
                    return ai_insights
            
            # 3. Fallback: Pattern-based insight extraction
            pattern_insights = self._pattern_based_insights(
                completed_task, task_result, performance_data, workspace_context
            )
            
            if pattern_insights:
                logger.info(f"🔄 PATTERN INSIGHTS: Extracted {len(pattern_insights)} insights")
                return pattern_insights
            
            return []
            
        except Exception as e:
            logger.error(f"Insight extraction failed: {e}")
            return []
    
    def _extract_performance_metrics(
        self, 
        completed_task: Dict[str, Any], 
        task_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract concrete performance metrics from task completion"""
        
        metrics = {
            'task_id': completed_task.get('id'),
            'task_name': completed_task.get('name', ''),
            'agent_role': completed_task.get('assigned_to_role', ''),
            'priority': completed_task.get('priority', 'medium'),
            'creation_type': completed_task.get('creation_type', ''),
            'execution_time': task_result.get('execution_time_seconds', 0),
            'model_used': task_result.get('model_used', ''),
            'tokens_used': task_result.get('tokens_used', {}),
            'cost_estimated': task_result.get('cost_estimated', 0),
            'quality_score': 0.0,
            'enhancement_applied': False,
            'verification_required': False
        }
        
        # Extract quality metrics
        quality_validation = task_result.get('quality_validation', {})
        if quality_validation:
            metrics['quality_score'] = quality_validation.get('overall_score', 0.0)
            metrics['quality_issues'] = quality_validation.get('quality_issues', [])
            metrics['ready_for_use'] = quality_validation.get('ready_for_use', False)
        
        # Extract enhancement metrics
        content_enhancement = task_result.get('content_enhancement', {})
        if content_enhancement:
            metrics['enhancement_applied'] = content_enhancement.get('enhanced', False)
        
        # Extract verification metrics
        verification_required = task_result.get('verification_required', {})
        if verification_required:
            metrics['verification_required'] = True
            metrics['verification_priority'] = verification_required.get('priority', 'medium')
        
        return metrics
    
    async def _ai_extract_strategic_insights(
        self, 
        completed_task: Dict[str, Any], 
        task_result: Dict[str, Any], 
        performance_data: Dict[str, Any],
        workspace_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """🤖 AI-powered strategic insight extraction"""
        
        try:
            analysis_prompt = f"""Analyze this completed task and extract actionable insights for future improvements:

TASK COMPLETION DATA:
- Task: {performance_data['task_name']}
- Agent Role: {performance_data['agent_role']}  
- Execution Time: {performance_data['execution_time']} seconds
- Quality Score: {performance_data['quality_score']:.2f}
- Cost: ${performance_data['cost_estimated']:.6f}
- Enhancement Applied: {performance_data['enhancement_applied']}
- Verification Required: {performance_data['verification_required']}

WORKSPACE CONTEXT:
- Goal: {workspace_context.get('goal', '')[:200]}
- Industry: {workspace_context.get('industry', 'Business')}

TASK RESULT SUMMARY:
{task_result.get('summary', '')[:300]}

Extract 2-4 SPECIFIC, ACTIONABLE insights that can improve future task performance. Focus on:
1. Process optimizations (what worked well/poorly)
2. Quality improvement patterns (how to avoid issues)
3. Cost/efficiency insights (resource optimization)
4. Strategic guidance (better task sequencing/agent assignment)

For each insight, provide:
- A specific, measurable pattern or rule
- Why this insight is valuable
- How to apply it in future tasks

Return ONLY a JSON array:
[
  {{
    "insight_type": "process_optimization|quality_improvement|cost_efficiency|strategic_guidance",
    "content": "Specific, actionable insight statement",
    "pattern_rule": "Concrete rule or pattern to apply",
    "business_impact": "immediate|short_term|strategic",
    "confidence_score": 0.85,
    "relevance_tags": ["specific", "actionable", "tags"],
    "application_guidance": "How to apply this insight in practice"
  }}
]"""

            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a strategic business intelligence analyst. Extract specific, actionable insights that drive measurable improvements."
                    },
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ],
                temperature=0.2,
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content.strip()
            insights = json.loads(result_text)
            
            # Validate and enhance insights
            validated_insights = []
            for insight in insights:
                if self._validate_insight(insight):
                    # Add metadata
                    insight.update({
                        'extracted_at': datetime.now().isoformat(),
                        'source_task_id': completed_task.get('id'),
                        'source_agent_role': performance_data['agent_role'],
                        'extraction_method': 'ai_driven'
                    })
                    validated_insights.append(insight)
            
            return validated_insights
            
        except Exception as e:
            logger.error(f"AI insight extraction error: {e}")
            return []
    
    def _validate_insight(self, insight: Dict[str, Any]) -> bool:
        """Validate that insight is actionable and specific"""
        
        required_fields = ['insight_type', 'content', 'pattern_rule', 'confidence_score']
        
        # Check required fields
        for field in required_fields:
            if field not in insight or not insight[field]:
                return False
        
        # Check confidence threshold
        if insight.get('confidence_score', 0) < 0.5:
            return False
        
        # Check content quality
        content = insight.get('content', '').lower()
        if any(word in content for word in ['generic', 'general', 'placeholder', 'example']):
            return False
        
        # Check for actionability
        pattern_rule = insight.get('pattern_rule', '').lower()
        if not any(word in pattern_rule for word in ['when', 'if', 'use', 'apply', 'increase', 'decrease', 'optimize']):
            return False
        
        return True
    
    def _pattern_based_insights(
        self, 
        completed_task: Dict[str, Any], 
        task_result: Dict[str, Any], 
        performance_data: Dict[str, Any],
        workspace_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """🔄 Pattern-based insight extraction (fallback)"""
        
        insights = []
        
        # Quality pattern insights
        quality_score = performance_data['quality_score']
        enhancement_applied = performance_data['enhancement_applied']
        
        if quality_score >= 0.8 and not enhancement_applied:
            insights.append({
                'insight_type': 'quality_improvement',
                'content': f'High-quality output achieved without enhancement for {performance_data["agent_role"]} tasks',
                'pattern_rule': f'Agent role {performance_data["agent_role"]} consistently produces high-quality output',
                'business_impact': 'immediate',
                'confidence_score': 0.7,
                'relevance_tags': ['quality', 'agent_performance', performance_data['agent_role'].lower()],
                'application_guidance': f'Prioritize {performance_data["agent_role"]} for similar tasks to maintain quality',
                'extracted_at': datetime.now().isoformat(),
                'source_task_id': completed_task.get('id'),
                'extraction_method': 'pattern_based'
            })
        
        if quality_score < 0.6 and enhancement_applied:
            insights.append({
                'insight_type': 'process_optimization',
                'content': f'Enhancement significantly improved output quality for {performance_data["task_name"]} type tasks',
                'pattern_rule': 'Always apply AI enhancement for similar task types to improve quality',
                'business_impact': 'immediate',
                'confidence_score': 0.6,
                'relevance_tags': ['enhancement', 'quality_improvement', 'process'],
                'application_guidance': 'Enable automatic enhancement for similar task patterns',
                'extracted_at': datetime.now().isoformat(),
                'source_task_id': completed_task.get('id'),
                'extraction_method': 'pattern_based'
            })
        
        # Cost efficiency insights
        execution_time = performance_data['execution_time']
        cost = performance_data['cost_estimated']
        
        if execution_time > 60 and cost > 0.001:  # Over 1 minute and expensive
            insights.append({
                'insight_type': 'cost_efficiency',
                'content': f'Task type "{performance_data["task_name"]}" requires optimization for time and cost',
                'pattern_rule': 'Break down complex tasks into smaller chunks for better efficiency',
                'business_impact': 'short_term',
                'confidence_score': 0.6,
                'relevance_tags': ['cost_optimization', 'time_efficiency', 'task_breakdown'],
                'application_guidance': 'Split similar complex tasks into 2-3 smaller subtasks',
                'extracted_at': datetime.now().isoformat(),
                'source_task_id': completed_task.get('id'),
                'extraction_method': 'pattern_based'
            })
        
        return insights
    
    async def generate_corrective_actions(
        self, 
        workspace_id: str, 
        current_insights: List[Dict[str, Any]], 
        workspace_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        🔄 AUTO COURSE CORRECTION: Generate corrective actions based on insights
        """
        try:
            # Analyze insights for patterns requiring correction
            correction_needed = self._analyze_correction_needs(current_insights, workspace_context)
            
            if not correction_needed:
                logger.debug(f"No course correction needed for workspace {workspace_id}")
                return []
            
            # Generate corrective actions
            if self.ai_available:
                ai_actions = await self._ai_generate_corrective_actions(
                    correction_needed, workspace_context
                )
                if ai_actions:
                    logger.info(f"🤖 AUTO CORRECTION: Generated {len(ai_actions)} corrective actions")
                    return ai_actions
            
            # Fallback: Pattern-based corrective actions
            pattern_actions = self._pattern_based_corrective_actions(
                correction_needed, workspace_context
            )
            
            if pattern_actions:
                logger.info(f"🔄 PATTERN CORRECTION: Generated {len(pattern_actions)} corrective actions")
                return pattern_actions
            
            return []
            
        except Exception as e:
            logger.error(f"Corrective action generation failed: {e}")
            return []
    
    def _analyze_correction_needs(
        self, 
        insights: List[Dict[str, Any]], 
        workspace_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Analyze insights to identify areas needing correction"""
        
        correction_patterns = []
        
        # Group insights by type
        insight_groups = {}
        for insight in insights:
            insight_type = insight.get('insight_type', 'unknown')
            if insight_type not in insight_groups:
                insight_groups[insight_type] = []
            insight_groups[insight_type].append(insight)
        
        # Analyze quality issues
        quality_insights = insight_groups.get('quality_improvement', [])
        low_quality_count = sum(1 for i in quality_insights if 'low' in i.get('content', '').lower())
        
        if low_quality_count >= 2:
            correction_patterns.append({
                'pattern_type': 'quality_degradation',
                'severity': 'high',
                'evidence': f'{low_quality_count} tasks with quality issues',
                'recommended_action': 'Implement stricter quality gates and agent training'
            })
        
        # Analyze cost efficiency
        cost_insights = insight_groups.get('cost_efficiency', [])
        if len(cost_insights) >= 2:
            correction_patterns.append({
                'pattern_type': 'cost_inefficiency',
                'severity': 'medium',
                'evidence': f'{len(cost_insights)} tasks with cost/time issues',
                'recommended_action': 'Optimize task breakdown and agent allocation'
            })
        
        # Analyze process issues
        process_insights = insight_groups.get('process_optimization', [])
        if len(process_insights) >= 3:
            correction_patterns.append({
                'pattern_type': 'process_bottlenecks',
                'severity': 'medium',
                'evidence': f'{len(process_insights)} process optimization opportunities',
                'recommended_action': 'Streamline workflows and eliminate bottlenecks'
            })
        
        return correction_patterns
    
    async def _ai_generate_corrective_actions(
        self, 
        correction_patterns: List[Dict[str, Any]], 
        workspace_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """🤖 AI-powered corrective action generation"""
        
        try:
            patterns_summary = '\n'.join([
                f"- {p['pattern_type']}: {p['evidence']} (Severity: {p['severity']})"
                for p in correction_patterns
            ])
            
            action_prompt = f"""Generate specific corrective actions to address these workspace performance patterns:

IDENTIFIED PATTERNS:
{patterns_summary}

WORKSPACE CONTEXT:
- Goal: {workspace_context.get('goal', '')[:200]}
- Industry: {workspace_context.get('industry', 'Business')}

Generate 2-4 SPECIFIC, ACTIONABLE corrective tasks that will address these patterns. Each action should:
1. Be implementable immediately
2. Address root causes, not just symptoms  
3. Have measurable success criteria
4. Be appropriate for the workspace context

Return ONLY a JSON array:
[
  {{
    "action_type": "quality_improvement|process_optimization|cost_reduction|workflow_enhancement",
    "task_name": "Specific task name",
    "task_description": "Detailed description of what needs to be done",
    "priority": "high|medium|low",
    "estimated_effort": "1-4 hours",
    "success_criteria": "Measurable outcome expected",
    "target_metric": "specific metric to improve",
    "urgency": "immediate|next_week|within_month"
  }}
]"""

            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a workflow optimization specialist. Generate specific, actionable corrective tasks."
                    },
                    {
                        "role": "user",
                        "content": action_prompt
                    }
                ],
                temperature=0.2,
                max_tokens=600,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content.strip()
            actions = json.loads(result_text)
            
            # Validate and enhance actions
            validated_actions = []
            for action in actions:
                if self._validate_corrective_action(action):
                    action.update({
                        'generated_at': datetime.now().isoformat(),
                        'generation_method': 'ai_driven',
                        'workspace_patterns': [p['pattern_type'] for p in correction_patterns]
                    })
                    validated_actions.append(action)
            
            return validated_actions
            
        except Exception as e:
            logger.error(f"AI corrective action generation error: {e}")
            return []
    
    def _validate_corrective_action(self, action: Dict[str, Any]) -> bool:
        """Validate corrective action quality and actionability"""
        
        required_fields = ['action_type', 'task_name', 'task_description', 'priority']
        
        for field in required_fields:
            if field not in action or not action[field]:
                return False
        
        # Check for specificity
        description = action.get('task_description', '').lower()
        if any(word in description for word in ['general', 'improve', 'optimize', 'enhance']) and len(description) < 50:
            return False  # Too generic
        
        return True
    
    def _pattern_based_corrective_actions(
        self, 
        correction_patterns: List[Dict[str, Any]], 
        workspace_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """🔄 Pattern-based corrective action generation (fallback)"""
        
        actions = []
        
        for pattern in correction_patterns:
            if pattern['pattern_type'] == 'quality_degradation':
                actions.append({
                    'action_type': 'quality_improvement',
                    'task_name': 'Implement Enhanced Quality Gates',
                    'task_description': 'Review and strengthen quality validation criteria to prevent low-quality outputs from reaching completion',
                    'priority': 'high',
                    'estimated_effort': '2-3 hours',
                    'success_criteria': 'Quality scores above 0.7 for all completed tasks',
                    'target_metric': 'average_quality_score',
                    'urgency': 'immediate',
                    'generated_at': datetime.now().isoformat(),
                    'generation_method': 'pattern_based'
                })
            
            elif pattern['pattern_type'] == 'cost_inefficiency':
                actions.append({
                    'action_type': 'cost_reduction',
                    'task_name': 'Optimize Task Breakdown Strategy',
                    'task_description': 'Analyze current task complexity and implement systematic breakdown of complex tasks into smaller, more efficient subtasks',
                    'priority': 'medium',
                    'estimated_effort': '1-2 hours',
                    'success_criteria': 'Average task execution time reduced by 25%',
                    'target_metric': 'average_execution_time',
                    'urgency': 'next_week',
                    'generated_at': datetime.now().isoformat(),
                    'generation_method': 'pattern_based'
                })
        
        return actions