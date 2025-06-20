"""
Specialist Agent Deep Reasoning - Extends deep reasoning to all specialist agents
Provides domain-agnostic reasoning capabilities for any specialist role
"""

import os
from typing import Dict, List, Any, Optional
from ai_agents.enhanced_reasoning import EnhancedReasoningEngine

class SpecialistReasoningMixin:
    """
    Mixin class to add deep reasoning capabilities to any specialist agent
    """
    
    def __init__(self):
        self.reasoning_engine = EnhancedReasoningEngine()
        self.enable_deep_reasoning = os.getenv('ENABLE_DEEP_REASONING', 'true').lower() == 'true'
        self.reasoning_threshold = float(os.getenv('DEEP_REASONING_THRESHOLD', '0.7'))
    
    async def should_use_deep_reasoning(self, task: Dict[str, Any]) -> bool:
        """
        Determines if a task requires deep reasoning based on complexity
        """
        if not self.enable_deep_reasoning:
            return False
            
        # Check task complexity indicators (domain-agnostic)
        complexity_score = 0.0
        
        # Multiple dependencies
        if task.get('dependencies', []):
            complexity_score += 0.2 * len(task.get('dependencies', []))
        
        # High priority
        if task.get('priority', 0) > 7:
            complexity_score += 0.3
        
        # Strategic importance
        if any(keyword in task.get('description', '').lower() 
               for keyword in ['strategic', 'critical', 'important', 'key', 'major']):
            complexity_score += 0.3
        
        # Multiple outputs required
        if task.get('expected_outputs', []) and len(task.get('expected_outputs', [])) > 2:
            complexity_score += 0.2
        
        # Quality requirements
        if task.get('quality_requirements', {}).get('min_score', 0) > 80:
            complexity_score += 0.2
            
        return complexity_score >= self.reasoning_threshold
    
    async def apply_specialist_reasoning(
        self, 
        task: Dict[str, Any],
        specialist_context: Dict[str, Any],
        thinking_callback: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Applies deep reasoning to specialist task execution
        """
        # Prepare universal context
        reasoning_context = {
            'task_data': task,
            'specialist_role': specialist_context.get('role', 'specialist'),
            'workspace_data': specialist_context.get('workspace', {}),
            'available_tools': specialist_context.get('tools', []),
            'quality_requirements': task.get('quality_requirements', {}),
            'constraints': task.get('constraints', []),
            'historical_performance': specialist_context.get('performance_metrics', {})
        }
        
        # Convert task to reasoning query
        query = self._task_to_reasoning_query(task)
        
        # Apply deep reasoning
        deep_analysis = await self.reasoning_engine.deep_reasoning_analysis(
            query,
            reasoning_context,
            thinking_callback
        )
        
        return deep_analysis
    
    def _task_to_reasoning_query(self, task: Dict[str, Any]) -> str:
        """
        Converts a task into a reasoning query
        """
        query_parts = []
        
        # Main objective
        query_parts.append(f"How to best complete: {task.get('description', 'this task')}")
        
        # Add constraints if any
        if task.get('constraints'):
            query_parts.append(f"Constraints: {', '.join(task['constraints'])}")
        
        # Add quality requirements
        if task.get('quality_requirements'):
            min_score = task['quality_requirements'].get('min_score', 0)
            query_parts.append(f"Must achieve quality score of {min_score}%")
        
        # Add deadline if present
        if task.get('deadline'):
            query_parts.append(f"Deadline: {task['deadline']}")
        
        return " ".join(query_parts)
    
    async def enhance_task_output_with_reasoning(
        self,
        task: Dict[str, Any],
        initial_output: Any,
        reasoning_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhances task output with reasoning insights
        """
        enhanced_output = {
            'primary_output': initial_output,
            'reasoning_applied': True,
            'confidence_level': reasoning_analysis.get('confidence', {}).get('overall', 0),
            'alternatives_considered': len(reasoning_analysis.get('alternatives', [])),
            'approach_rationale': reasoning_analysis.get('recommendation', {}).get('rationale', ''),
            'quality_factors': self._extract_quality_factors(reasoning_analysis),
            'optimization_opportunities': self._identify_optimizations(reasoning_analysis)
        }
        
        # Add monitoring points for continuous improvement
        if reasoning_analysis.get('recommendation', {}).get('monitoring_points'):
            enhanced_output['monitoring_points'] = reasoning_analysis['recommendation']['monitoring_points']
        
        return enhanced_output
    
    def _extract_quality_factors(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Extracts quality-related factors from reasoning
        """
        factors = []
        
        # From confidence factors
        confidence_factors = analysis.get('confidence', {}).get('factors', {})
        if confidence_factors.get('data_quality', 0) > 0.8:
            factors.append("High data quality")
        
        # From alternatives evaluation
        for alt_id, evaluation in analysis.get('evaluations', {}).items():
            if evaluation.get('recommendation_strength') == 'high':
                factors.extend(evaluation.get('factors', {}).values())
        
        return list(set(factors))  # Remove duplicates
    
    def _identify_optimizations(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Identifies optimization opportunities from reasoning
        """
        optimizations = []
        
        # From critique
        critique = analysis.get('critique', {})
        for missing in critique.get('missing_factors', []):
            optimizations.append(f"Consider: {missing}")
        
        # From alternatives not chosen
        chosen = analysis.get('recommendation', {}).get('primary_recommendation')
        for alt in analysis.get('alternatives', []):
            if alt['id'] != chosen and alt.get('confidence', 0) > 0.7:
                optimizations.append(f"Alternative approach: {alt['title']}")
        
        return optimizations[:3]  # Limit to top 3


class EnhancedSpecialistAgent:
    """
    Base class for specialist agents with deep reasoning
    """
    
    def __init__(self, agent_config: Dict[str, Any]):
        self.config = agent_config
        self.reasoning_mixin = SpecialistReasoningMixin()
    
    async def execute_task_with_reasoning(
        self, 
        task: Dict[str, Any],
        thinking_callback: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Executes task with optional deep reasoning
        """
        # Check if deep reasoning should be applied
        use_reasoning = await self.reasoning_mixin.should_use_deep_reasoning(task)
        
        if use_reasoning and thinking_callback:
            await thinking_callback({
                "type": "specialist_reasoning",
                "title": f"🧠 {self.config['role']} applying deep reasoning",
                "description": "Analyzing task complexity and approach options...",
                "status": "in_progress"
            })
        
        # Prepare specialist context
        specialist_context = {
            'role': self.config.get('role', 'specialist'),
            'seniority': self.config.get('seniority', 'senior'),
            'workspace': self.config.get('workspace_context', {}),
            'tools': self._get_available_tools(),
            'performance_metrics': await self._get_performance_metrics()
        }
        
        if use_reasoning:
            # Apply deep reasoning
            reasoning_analysis = await self.reasoning_mixin.apply_specialist_reasoning(
                task,
                specialist_context,
                thinking_callback
            )
            
            # Execute task with reasoning insights
            initial_output = await self._execute_core_task(task, reasoning_analysis)
            
            # Enhance output with reasoning
            return await self.reasoning_mixin.enhance_task_output_with_reasoning(
                task,
                initial_output,
                reasoning_analysis
            )
        else:
            # Standard execution without deep reasoning
            return await self._execute_core_task(task)
    
    async def _execute_core_task(
        self, 
        task: Dict[str, Any], 
        reasoning_analysis: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Core task execution logic (to be implemented by specific specialists)
        """
        raise NotImplementedError("Specialist must implement _execute_core_task")
    
    def _get_available_tools(self) -> List[str]:
        """
        Returns tools available to this specialist
        """
        # Domain-agnostic tool categories
        return [
            "analysis_tools",
            "creation_tools", 
            "validation_tools",
            "optimization_tools"
        ]
    
    async def _get_performance_metrics(self) -> Dict[str, float]:
        """
        Gets historical performance metrics for this specialist
        """
        # Simplified metrics - in production would query from database
        return {
            'avg_quality_score': 0.85,
            'avg_completion_time': 0.75,
            'success_rate': 0.92
        }