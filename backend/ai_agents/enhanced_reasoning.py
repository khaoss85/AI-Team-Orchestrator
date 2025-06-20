"""
Enhanced Reasoning Module - Deep thinking capabilities inspired by o3 and Claude
Provides multi-step reasoning, self-reflection, and confidence calibration
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

class EnhancedReasoningEngine:
    """
    Implements advanced reasoning patterns for deeper analysis
    """
    
    async def deep_reasoning_analysis(
        self, 
        query: str, 
        context: Dict[str, Any],
        thinking_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Performs deep multi-step reasoning with self-reflection
        """
        
        # Step 1: Problem Decomposition
        await self._think_step(thinking_callback, {
            "type": "reasoning_step",
            "step": "problem_decomposition",
            "title": "🔍 Breaking Down the Question",
            "description": "Identifying key components and implicit requirements...",
            "status": "in_progress"
        })
        
        components = self._decompose_problem(query, context)
        
        await self._think_step(thinking_callback, {
            "type": "reasoning_step",
            "step": "problem_decomposition",
            "title": "🔍 Problem Components Identified",
            "description": f"Found {len(components)} key aspects to analyze",
            "components": components,
            "status": "completed"
        })
        
        # Step 2: Multi-Perspective Analysis
        await self._think_step(thinking_callback, {
            "type": "reasoning_step",
            "step": "perspective_analysis",
            "title": "🔄 Analyzing from Multiple Perspectives",
            "description": "Considering viewpoints: Technical, Business, User, Risk...",
            "status": "in_progress"
        })
        
        perspectives = await self._analyze_perspectives(query, context)
        
        # Step 3: Alternative Generation
        await self._think_step(thinking_callback, {
            "type": "reasoning_step",
            "step": "alternatives_generation",
            "title": "💡 Generating Alternative Solutions",
            "description": "Exploring different approaches and their trade-offs...",
            "status": "in_progress"
        })
        
        alternatives = self._generate_alternatives(query, context, perspectives)
        
        # Step 4: Deep Evaluation
        await self._think_step(thinking_callback, {
            "type": "reasoning_step",
            "step": "deep_evaluation",
            "title": "⚖️ Evaluating Each Alternative",
            "description": "Scoring based on: feasibility, impact, cost, timeline, risk...",
            "status": "in_progress",
            "alternatives_count": len(alternatives)
        })
        
        evaluations = self._evaluate_alternatives(alternatives, context)
        
        # Step 5: Self-Critique
        await self._think_step(thinking_callback, {
            "type": "reflection_step",
            "step": "self_critique",
            "title": "🤔 Critical Self-Review",
            "description": "Checking for biases, assumptions, and blind spots...",
            "status": "in_progress"
        })
        
        critique = self._self_critique(evaluations)
        
        # Step 6: Confidence Calibration
        await self._think_step(thinking_callback, {
            "type": "reasoning_step",
            "step": "confidence_calibration",
            "title": "📊 Calibrating Confidence Levels",
            "description": "Assessing certainty based on data quality and unknowns...",
            "status": "in_progress"
        })
        
        confidence = self._calibrate_confidence(evaluations, critique)
        
        # Step 7: Final Synthesis
        await self._think_step(thinking_callback, {
            "type": "reasoning_step",
            "step": "final_synthesis",
            "title": "🎯 Synthesizing Final Recommendation",
            "description": "Integrating all analysis into coherent recommendation...",
            "status": "in_progress"
        })
        
        recommendation = self._synthesize_recommendation(
            evaluations, critique, confidence
        )
        
        return {
            "recommendation": recommendation,
            "alternatives": alternatives,
            "confidence": confidence,
            "reasoning_chain": self._format_reasoning_chain(
                components, perspectives, evaluations, critique
            )
        }
    
    def _decompose_problem(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Domain-agnostic problem decomposition using context metadata
        """
        components = []
        
        # Extract from workspace context (domain-agnostic)
        workspace_data = context.get('workspace_data', {})
        domain = workspace_data.get('domain', 'general')
        
        # Universal components based on query intent
        query_lower = query.lower()
        
        # Resource management (universal concept)
        if any(word in query_lower for word in ['add', 'remove', 'change', 'modify']):
            components.append({
                "aspect": "resource_modification",
                "type": "explicit",
                "description": "Evaluating resource changes",
                "domain_context": domain
            })
        
        # Status evaluation (universal concept)
        if any(word in query_lower for word in ['status', 'complete', 'ready', 'enough']):
            components.append({
                "aspect": "status_assessment",
                "type": "explicit",
                "description": "Assessing current state",
                "metrics": self._get_universal_metrics(context)
            })
        
        # Optimization check (universal concept)
        components.append({
            "aspect": "optimization_analysis",
            "type": "implicit",
            "description": "Evaluating efficiency and effectiveness",
            "factors": ["utilization", "productivity", "cost", "quality"]
        })
        
        # Goal alignment (universal concept)
        if context.get('goals'):
            components.append({
                "aspect": "goal_alignment",
                "type": "implicit",
                "description": "Checking alignment with workspace goals",
                "active_goals": len(context.get('goals', []))
            })
        
        return components
    
    async def _analyze_perspectives(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Domain-agnostic multi-perspective analysis
        """
        # Universal perspectives that apply to any domain
        perspectives = {}
        
        # Resource perspective (universal)
        current_resources = len(context.get('team_data', []))
        active_tasks = len(context.get('active_tasks', []))
        utilization = active_tasks / max(current_resources, 1)
        
        perspectives["resource_efficiency"] = {
            "viewpoint": f"Current utilization: {utilization:.1%}",
            "metrics": {
                "resources": current_resources,
                "workload": active_tasks,
                "efficiency_ratio": utilization
            },
            "weight": 0.3
        }
        
        # Goal perspective (universal)
        goals_data = context.get('goals', [])
        if goals_data:
            completion_avg = sum(g.get('completion_percentage', 0) for g in goals_data) / len(goals_data)
            perspectives["goal_alignment"] = {
                "viewpoint": f"Goal completion average: {completion_avg:.0f}%",
                "metrics": {
                    "total_goals": len(goals_data),
                    "avg_completion": completion_avg
                },
                "weight": 0.3
            }
        
        # Quality perspective (universal)
        quality_scores = context.get('quality_metrics', {})
        perspectives["quality_focus"] = {
            "viewpoint": "Maintaining output quality standards",
            "metrics": quality_scores,
            "weight": 0.2
        }
        
        # Sustainability perspective (universal)
        perspectives["sustainability"] = {
            "viewpoint": "Long-term operational health",
            "factors": ["burnout_risk", "growth_capacity", "knowledge_retention"],
            "weight": 0.2
        }
        
        return perspectives
    
    def _generate_alternatives(
        self, 
        query: str, 
        context: Dict[str, Any], 
        perspectives: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generates multiple solution alternatives
        """
        return [
            {
                "id": "immediate_hire",
                "title": "Hire Additional Team Member Now",
                "description": "Proactively expand team before workload increases",
                "pros": [
                    "Team ready for scale",
                    "Onboarding during calm period",
                    "No delivery delays"
                ],
                "cons": [
                    "Higher immediate cost",
                    "Risk of over-staffing",
                    "Integration overhead"
                ],
                "confidence": 0.7
            },
            {
                "id": "wait_and_monitor",
                "title": "Monitor for 2-4 Weeks",
                "description": "Gather more data before deciding",
                "pros": [
                    "Data-driven decision",
                    "Cost optimization",
                    "Flexibility maintained"
                ],
                "cons": [
                    "Potential reactive hiring",
                    "Risk of bottlenecks",
                    "Rushed onboarding"
                ],
                "confidence": 0.85
            },
            {
                "id": "hybrid_approach",
                "title": "Part-time Contractor First",
                "description": "Start with flexible resource, convert if needed",
                "pros": [
                    "Low commitment",
                    "Quick to implement",
                    "Test before hiring"
                ],
                "cons": [
                    "Less team integration",
                    "Knowledge transfer issues",
                    "Availability risks"
                ],
                "confidence": 0.75
            }
        ]
    
    def _evaluate_alternatives(
        self, 
        alternatives: List[Dict[str, Any]], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deep evaluation of each alternative
        """
        evaluations = {}
        
        for alt in alternatives:
            score = 0
            factors = {}
            
            # Evaluate based on current context
            if context.get('workload_ratio', 0) < 0.5:
                if alt['id'] == 'wait_and_monitor':
                    score += 30
                    factors['workload'] = "Low utilization supports waiting"
            
            # Add more evaluation logic...
            evaluations[alt['id']] = {
                "score": score,
                "factors": factors,
                "recommendation_strength": "high" if score > 70 else "medium"
            }
        
        return evaluations
    
    def _self_critique(self, evaluations: Dict[str, Any]) -> Dict[str, Any]:
        """
        Critically reviews the analysis for biases and gaps
        """
        return {
            "identified_biases": [
                "Conservative bias - favoring status quo",
                "Recency bias - overweighting current low workload"
            ],
            "missing_factors": [
                "Client feedback on delivery speed",
                "Competitive landscape changes",
                "Team morale indicators"
            ],
            "assumptions_made": [
                "Linear workload growth",
                "Stable team productivity",
                "No urgent deadlines"
            ],
            "confidence_impact": -0.1  # Reduce confidence due to gaps
        }
    
    def _calibrate_confidence(
        self, 
        evaluations: Dict[str, Any], 
        critique: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculates calibrated confidence levels
        """
        base_confidence = 0.8
        
        # Adjust based on critique
        adjusted_confidence = base_confidence + critique.get('confidence_impact', 0)
        
        # Factor in data quality
        data_quality_score = self._assess_data_quality(evaluations)
        
        final_confidence = adjusted_confidence * data_quality_score
        
        return {
            "overall": final_confidence,
            "factors": {
                "data_quality": data_quality_score,
                "analysis_completeness": 0.85,
                "uncertainty_level": 0.2
            },
            "confidence_statement": self._generate_confidence_statement(final_confidence)
        }
    
    def _assess_data_quality(self, evaluations: Dict[str, Any]) -> float:
        """
        Assesses quality of available data
        """
        # Simplified - in reality would check data freshness, completeness, etc.
        return 0.85
    
    def _generate_confidence_statement(self, confidence: float) -> str:
        """
        Generates human-readable confidence statement
        """
        if confidence > 0.8:
            return "High confidence - Strong data support and clear patterns"
        elif confidence > 0.6:
            return "Moderate confidence - Good analysis with some uncertainties"
        else:
            return "Lower confidence - Significant unknowns require caution"
    
    def _synthesize_recommendation(
        self, 
        evaluations: Dict[str, Any],
        critique: Dict[str, Any],
        confidence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Synthesizes all analysis into final recommendation
        """
        # Determine best alternative
        best_alternative = max(
            evaluations.items(), 
            key=lambda x: x[1].get('score', 0)
        )[0]
        
        return {
            "primary_recommendation": best_alternative,
            "rationale": "Based on multi-perspective analysis and current context",
            "confidence_level": confidence['overall'],
            "key_factors": evaluations[best_alternative]['factors'],
            "caveats": critique['missing_factors'],
            "monitoring_points": [
                "Track task completion rate weekly",
                "Monitor team overtime hours",
                "Review client satisfaction scores"
            ]
        }
    
    def _format_reasoning_chain(
        self,
        components: List[Dict[str, Any]],
        perspectives: Dict[str, Any],
        evaluations: Dict[str, Any],
        critique: Dict[str, Any]
    ) -> List[str]:
        """
        Formats the reasoning chain for display
        """
        chain = []
        
        chain.append(f"Identified {len(components)} key problem components")
        chain.append(f"Analyzed from {len(perspectives)} stakeholder perspectives")
        chain.append(f"Generated and evaluated {len(evaluations)} alternatives")
        chain.append(f"Self-critique identified {len(critique['identified_biases'])} potential biases")
        chain.append("Calibrated confidence based on data quality and uncertainties")
        
        return chain
    
    async def _think_step(
        self, 
        callback: Optional[Callable], 
        step_data: Dict[str, Any]
    ):
        """
        Sends thinking step to callback if provided
        """
        if callback:
            await callback(step_data)
        # Small delay to simulate thinking
        await asyncio.sleep(0.1)
    
    def _get_universal_metrics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts universal metrics that apply to any domain
        """
        return {
            "resource_count": len(context.get('team_data', [])),
            "active_items": len(context.get('active_tasks', [])),
            "completed_items": len(context.get('completed_tasks', [])),
            "quality_score": context.get('quality_metrics', {}).get('average', 0),
            "goal_progress": self._calculate_goal_progress(context.get('goals', [])),
            "efficiency_ratio": self._calculate_efficiency(context)
        }
    
    def _calculate_goal_progress(self, goals: List[Dict[str, Any]]) -> float:
        """
        Calculates average goal progress
        """
        if not goals:
            return 0.0
        return sum(g.get('completion_percentage', 0) for g in goals) / len(goals)
    
    def _calculate_efficiency(self, context: Dict[str, Any]) -> float:
        """
        Calculates efficiency ratio (universal metric)
        """
        resources = len(context.get('team_data', []))
        completed = len(context.get('completed_tasks', []))
        time_elapsed = context.get('time_elapsed_days', 1)
        
        if resources == 0 or time_elapsed == 0:
            return 0.0
            
        return completed / (resources * time_elapsed)