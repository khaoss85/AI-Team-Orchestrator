"""
🤖 Autonomous Learning Memory System
Self-improving memory system that learns from successful patterns and continuously enhances

Pillar 11: Self-Enhancement - Automatically learns from successful patterns
Pillar 12: Course Correction - Auto-detects and corrects low-performing approaches
Pillar 8: No Hardcode - AI-driven pattern recognition and adaptation
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)

class LearningType(Enum):
    """Types of learning patterns"""
    TOOL_USAGE = "tool_usage"
    CONTENT_GENERATION = "content_generation"
    BUSINESS_ADAPTATION = "business_adaptation"
    QUALITY_IMPROVEMENT = "quality_improvement"

@dataclass
class LearningPattern:
    """Learning pattern from successful executions"""
    pattern_id: str
    learning_type: LearningType
    context_conditions: Dict[str, Any]
    successful_approach: Dict[str, Any]
    performance_metrics: Dict[str, float]
    confidence_score: float
    usage_count: int
    success_rate: float
    last_used: datetime
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        result = asdict(self)
        result['learning_type'] = self.learning_type.value
        result['last_used'] = self.last_used.isoformat()
        result['created_at'] = self.created_at.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LearningPattern':
        """Create from dictionary"""
        data['learning_type'] = LearningType(data['learning_type'])
        data['last_used'] = datetime.fromisoformat(data['last_used'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)

@dataclass
class LearningInsight:
    """Insight generated from learning patterns"""
    insight_type: str
    description: str
    confidence: float
    applicable_contexts: List[str]
    recommended_actions: List[str]
    supporting_patterns: List[str]

class AutonomousLearningMemorySystem:
    """
    🤖 AI-Driven Autonomous Learning System
    Continuously learns from executions and improves system performance
    """
    
    def __init__(self):
        self.learning_patterns: List[LearningPattern] = []
        self.insights_cache: List[LearningInsight] = []
        self.performance_metrics = defaultdict(list)
        self.last_learning_cycle = datetime.now()
        
    async def learn_from_successful_execution(
        self,
        execution_type: str,
        context: Dict[str, Any],
        approach_used: Dict[str, Any],
        performance_metrics: Dict[str, float],
        outcome_quality: float
    ):
        """
        🤖 Learn from successful execution and store pattern
        
        Args:
            execution_type: Type of execution (e.g., "asset_generation", "task_execution")
            context: Context conditions when execution was successful
            approach_used: The approach/method that led to success
            performance_metrics: Metrics from the execution
            outcome_quality: Quality score of the outcome (0-100)
        """
        try:
            logger.info(f"📚 Learning from successful {execution_type}: Quality={outcome_quality:.1f}")
            
            # Only learn from high-quality outcomes
            if outcome_quality < 70:
                logger.debug(f"Skipping learning - quality too low: {outcome_quality}")
                return
            
            # Determine learning type
            learning_type = self._classify_learning_type(execution_type, approach_used)
            
            # Check if similar pattern already exists
            existing_pattern = await self._find_similar_pattern(
                learning_type, 
                context, 
                approach_used
            )
            
            if existing_pattern:
                # Update existing pattern
                await self._update_existing_pattern(
                    existing_pattern, 
                    performance_metrics, 
                    outcome_quality
                )
            else:
                # Create new learning pattern
                await self._create_new_learning_pattern(
                    learning_type,
                    context,
                    approach_used,
                    performance_metrics,
                    outcome_quality
                )
            
            # Trigger learning cycle if needed
            await self._trigger_learning_cycle_if_needed()
            
        except Exception as e:
            logger.error(f"Error in autonomous learning: {e}")
    
    async def get_recommendations_for_context(
        self,
        execution_type: str,
        context: Dict[str, Any],
        current_approach: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        🤖 Get AI-driven recommendations based on learned patterns
        
        Args:
            execution_type: Type of execution needing recommendations
            context: Current context
            current_approach: Current approach being considered
            
        Returns:
            List of recommendations with confidence scores
        """
        try:
            # Find relevant learning patterns
            relevant_patterns = await self._find_relevant_patterns(
                execution_type, 
                context
            )
            
            if not relevant_patterns:
                return []
            
            # Generate AI recommendations
            recommendations = await self._ai_generate_recommendations(
                relevant_patterns,
                context,
                current_approach
            )
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    async def analyze_performance_trends(self) -> List[LearningInsight]:
        """
        🤖 Analyze performance trends and generate insights
        """
        try:
            logger.info("🔍 Analyzing performance trends for insights...")
            
            # Generate insights from patterns
            insights = []
            
            # Tool usage insights
            tool_insights = await self._analyze_tool_usage_patterns()
            insights.extend(tool_insights)
            
            # Content generation insights
            content_insights = await self._analyze_content_generation_patterns()
            insights.extend(content_insights)
            
            # Business adaptation insights
            business_insights = await self._analyze_business_adaptation_patterns()
            insights.extend(business_insights)
            
            # Cache insights
            self.insights_cache = insights
            
            logger.info(f"✅ Generated {len(insights)} learning insights")
            
            return insights
            
        except Exception as e:
            logger.error(f"Error analyzing performance trends: {e}")
            return []
    
    async def auto_optimize_system_parameters(self) -> Dict[str, Any]:
        """
        🤖 Automatically optimize system parameters based on learning
        """
        try:
            logger.info("⚡ Auto-optimizing system parameters based on learning...")
            
            optimizations = {}
            
            # Analyze tool usage effectiveness
            tool_optimizations = await self._optimize_tool_usage_parameters()
            optimizations.update(tool_optimizations)
            
            # Analyze content generation parameters
            content_optimizations = await self._optimize_content_generation_parameters()
            optimizations.update(content_optimizations)
            
            # Analyze quality thresholds
            quality_optimizations = await self._optimize_quality_thresholds()
            optimizations.update(quality_optimizations)
            
            logger.info(f"✅ Generated {len(optimizations)} parameter optimizations")
            
            return optimizations
            
        except Exception as e:
            logger.error(f"Error in auto-optimization: {e}")
            return {}
    
    def _classify_learning_type(self, execution_type: str, approach: Dict[str, Any]) -> LearningType:
        """Classify the type of learning based on execution"""
        if "tool" in execution_type.lower() or "tools" in str(approach).lower():
            return LearningType.TOOL_USAGE
        elif "content" in execution_type.lower() or "asset" in execution_type.lower():
            return LearningType.CONTENT_GENERATION
        elif "business" in str(approach).lower() or "context" in str(approach).lower():
            return LearningType.BUSINESS_ADAPTATION
        else:
            return LearningType.QUALITY_IMPROVEMENT
    
    async def _find_similar_pattern(
        self,
        learning_type: LearningType,
        context: Dict[str, Any],
        approach: Dict[str, Any]
    ) -> Optional[LearningPattern]:
        """Find existing similar pattern"""
        for pattern in self.learning_patterns:
            if pattern.learning_type != learning_type:
                continue
            
            # Simple similarity check (can be enhanced with AI)
            context_similarity = self._calculate_context_similarity(
                pattern.context_conditions, 
                context
            )
            approach_similarity = self._calculate_approach_similarity(
                pattern.successful_approach, 
                approach
            )
            
            # Patterns are similar if both context and approach have high similarity
            if context_similarity > 0.7 and approach_similarity > 0.6:
                return pattern
        
        return None
    
    async def _update_existing_pattern(
        self,
        pattern: LearningPattern,
        new_metrics: Dict[str, float],
        outcome_quality: float
    ):
        """Update existing learning pattern with new data"""
        pattern.usage_count += 1
        pattern.last_used = datetime.now()
        
        # Update success rate (weighted average)
        old_weight = pattern.usage_count - 1
        new_weight = 1
        total_weight = old_weight + new_weight
        
        pattern.success_rate = (
            (pattern.success_rate * old_weight + outcome_quality * new_weight) / total_weight
        )
        
        # Update performance metrics (weighted average)
        for metric, value in new_metrics.items():
            if metric in pattern.performance_metrics:
                pattern.performance_metrics[metric] = (
                    (pattern.performance_metrics[metric] * old_weight + value * new_weight) / total_weight
                )
            else:
                pattern.performance_metrics[metric] = value
        
        # Update confidence based on usage count and success rate
        pattern.confidence_score = min(95, pattern.success_rate * (1 + pattern.usage_count * 0.05))
    
    async def _create_new_learning_pattern(
        self,
        learning_type: LearningType,
        context: Dict[str, Any],
        approach: Dict[str, Any],
        metrics: Dict[str, float],
        outcome_quality: float
    ):
        """Create new learning pattern"""
        pattern_id = f"{learning_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        pattern = LearningPattern(
            pattern_id=pattern_id,
            learning_type=learning_type,
            context_conditions=context,
            successful_approach=approach,
            performance_metrics=metrics,
            confidence_score=outcome_quality,
            usage_count=1,
            success_rate=outcome_quality,
            last_used=datetime.now(),
            created_at=datetime.now()
        )
        
        self.learning_patterns.append(pattern)
        
        # Memory management - keep only best patterns
        if len(self.learning_patterns) > 100:
            self._cleanup_patterns()
        
        logger.info(f"💾 Created new learning pattern: {pattern_id}")
    
    async def _find_relevant_patterns(
        self,
        execution_type: str,
        context: Dict[str, Any]
    ) -> List[LearningPattern]:
        """Find patterns relevant to current context"""
        relevant_patterns = []
        
        for pattern in self.learning_patterns:
            # Basic relevance scoring
            relevance_score = 0
            
            # Type matching
            if pattern.learning_type.value in execution_type.lower():
                relevance_score += 0.4
            
            # Context similarity
            context_similarity = self._calculate_context_similarity(
                pattern.context_conditions, 
                context
            )
            relevance_score += context_similarity * 0.6
            
            # Success rate bonus
            if pattern.success_rate > 80:
                relevance_score += 0.2
            
            # Recent usage bonus
            days_since_used = (datetime.now() - pattern.last_used).days
            if days_since_used < 7:
                relevance_score += 0.1
            
            # Add if relevant enough
            if relevance_score > 0.5:
                relevant_patterns.append(pattern)
        
        # Sort by relevance and success rate
        relevant_patterns.sort(
            key=lambda p: (p.success_rate, p.confidence_score), 
            reverse=True
        )
        
        return relevant_patterns[:5]  # Top 5 most relevant
    
    async def _ai_generate_recommendations(
        self,
        patterns: List[LearningPattern],
        context: Dict[str, Any],
        current_approach: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate AI-driven recommendations from patterns"""
        try:
            import os
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            if not client.api_key:
                return self._fallback_recommendations(patterns)
            
            # Prepare pattern data
            pattern_data = []
            for pattern in patterns:
                pattern_data.append({
                    "learning_type": pattern.learning_type.value,
                    "success_rate": pattern.success_rate,
                    "approach": pattern.successful_approach,
                    "performance": pattern.performance_metrics,
                    "confidence": pattern.confidence_score
                })
            
            prompt = f"""
Genera raccomandazioni basate sui pattern di successo appresi.

CURRENT CONTEXT:
{json.dumps(context, indent=2)}

CURRENT APPROACH:
{json.dumps(current_approach or {}, indent=2)}

SUCCESSFUL PATTERNS LEARNED:
{json.dumps(pattern_data, indent=2, default=str)}

GENERA RACCOMANDAZIONI:
1. Quali approcci hanno funzionato meglio in contesti simili?
2. Cosa dovrebbe essere modificato nell'approccio corrente?
3. Quali sono i fattori chiave di successo dai pattern?
4. Che rischi dovrebbero essere evitati?

Rispondi in JSON:
{{
    "recommendations": [
        {{
            "title": "titolo raccomandazione",
            "description": "descrizione dettagliata",
            "confidence": 0-100,
            "expected_improvement": "percentuale miglioramento atteso",
            "supporting_patterns": ["pattern_id1", "pattern_id2"]
        }}
    ],
    "key_success_factors": ["fattore1", "fattore2"],
    "risks_to_avoid": ["rischio1", "rischio2"]
}}
"""
            
            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert learning system analyst. Generate actionable recommendations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.2
            )
            
            ai_response = response.choices[0].message.content
            
            try:
                result = json.loads(ai_response)
                return result.get("recommendations", [])
            except json.JSONDecodeError:
                logger.error(f"Failed to parse AI recommendations: {ai_response}")
                return self._fallback_recommendations(patterns)
                
        except Exception as e:
            logger.error(f"Error in AI recommendation generation: {e}")
            return self._fallback_recommendations(patterns)
    
    async def _analyze_tool_usage_patterns(self) -> List[LearningInsight]:
        """Analyze tool usage patterns for insights"""
        tool_patterns = [p for p in self.learning_patterns if p.learning_type == LearningType.TOOL_USAGE]
        
        if not tool_patterns:
            return []
        
        insights = []
        
        # Find most successful tool combinations
        tool_combinations = defaultdict(list)
        for pattern in tool_patterns:
            tools_used = pattern.successful_approach.get("tools_used", [])
            if tools_used:
                key = ",".join(sorted(tools_used))
                tool_combinations[key].append(pattern.success_rate)
        
        # Best combinations
        best_combinations = []
        for combo, rates in tool_combinations.items():
            if len(rates) >= 2:  # At least 2 uses
                avg_rate = sum(rates) / len(rates)
                if avg_rate > 75:
                    best_combinations.append((combo, avg_rate, len(rates)))
        
        if best_combinations:
            best_combinations.sort(key=lambda x: x[1], reverse=True)
            top_combo = best_combinations[0]
            
            insights.append(LearningInsight(
                insight_type="tool_usage_optimization",
                description=f"Tool combination '{top_combo[0]}' shows {top_combo[1]:.1f}% success rate across {top_combo[2]} executions",
                confidence=min(90, top_combo[1]),
                applicable_contexts=["asset_generation", "task_execution"],
                recommended_actions=[f"Prioritize using tools: {top_combo[0]}"],
                supporting_patterns=[p.pattern_id for p in tool_patterns if ",".join(sorted(p.successful_approach.get("tools_used", []))) == top_combo[0]]
            ))
        
        return insights
    
    async def _analyze_content_generation_patterns(self) -> List[LearningInsight]:
        """Analyze content generation patterns"""
        content_patterns = [p for p in self.learning_patterns if p.learning_type == LearningType.CONTENT_GENERATION]
        
        if not content_patterns:
            return []
        
        insights = []
        
        # Find patterns with high business specificity
        high_specificity_patterns = [p for p in content_patterns 
                                   if p.performance_metrics.get("business_specificity_score", 0) > 80]
        
        if high_specificity_patterns:
            avg_success = sum(p.success_rate for p in high_specificity_patterns) / len(high_specificity_patterns)
            
            insights.append(LearningInsight(
                insight_type="content_specificity",
                description=f"High business specificity (>80) correlates with {avg_success:.1f}% success rate in content generation",
                confidence=75,
                applicable_contexts=["asset_generation"],
                recommended_actions=["Focus on business-specific content generation", "Use real business data in content"],
                supporting_patterns=[p.pattern_id for p in high_specificity_patterns]
            ))
        
        return insights
    
    async def _analyze_business_adaptation_patterns(self) -> List[LearningInsight]:
        """Analyze business adaptation patterns"""
        business_patterns = [p for p in self.learning_patterns if p.learning_type == LearningType.BUSINESS_ADAPTATION]
        
        if not business_patterns:
            return []
        
        insights = []
        
        # Find industry-specific patterns
        industry_performance = defaultdict(list)
        for pattern in business_patterns:
            industry = pattern.context_conditions.get("industry", "unknown")
            if industry != "unknown":
                industry_performance[industry].append(pattern.success_rate)
        
        for industry, rates in industry_performance.items():
            if len(rates) >= 2:
                avg_rate = sum(rates) / len(rates)
                if avg_rate > 70:
                    insights.append(LearningInsight(
                        insight_type="industry_adaptation",
                        description=f"Business adaptation for {industry} shows {avg_rate:.1f}% success rate",
                        confidence=60,
                        applicable_contexts=[industry],
                        recommended_actions=[f"Apply industry-specific adaptations for {industry}"],
                        supporting_patterns=[p.pattern_id for p in business_patterns 
                                           if p.context_conditions.get("industry") == industry]
                    ))
        
        return insights
    
    async def _optimize_tool_usage_parameters(self) -> Dict[str, Any]:
        """Optimize tool usage parameters based on learning"""
        optimizations = {}
        
        tool_patterns = [p for p in self.learning_patterns if p.learning_type == LearningType.TOOL_USAGE]
        
        if tool_patterns:
            # Find optimal tool sequence lengths
            sequence_lengths = []
            for pattern in tool_patterns:
                tools_used = pattern.successful_approach.get("tools_used", [])
                if len(tools_used) > 0:
                    sequence_lengths.append((len(tools_used), pattern.success_rate))
            
            if sequence_lengths:
                # Find length with highest average success rate
                length_performance = defaultdict(list)
                for length, rate in sequence_lengths:
                    length_performance[length].append(rate)
                
                best_length = max(length_performance.items(), 
                                key=lambda x: sum(x[1])/len(x[1]))[0]
                
                optimizations["optimal_tool_sequence_length"] = best_length
        
        return optimizations
    
    async def _optimize_content_generation_parameters(self) -> Dict[str, Any]:
        """Optimize content generation parameters"""
        optimizations = {}
        
        content_patterns = [p for p in self.learning_patterns if p.learning_type == LearningType.CONTENT_GENERATION]
        
        if content_patterns:
            # Find optimal specificity threshold
            specificity_scores = []
            for pattern in content_patterns:
                score = pattern.performance_metrics.get("business_specificity_score", 0)
                if score > 0:
                    specificity_scores.append((score, pattern.success_rate))
            
            if specificity_scores:
                # Find threshold that maximizes success rate
                high_success_patterns = [s for s, r in specificity_scores if r > 80]
                if high_success_patterns:
                    optimal_threshold = min(high_success_patterns)
                    optimizations["optimal_specificity_threshold"] = optimal_threshold
        
        return optimizations
    
    async def _optimize_quality_thresholds(self) -> Dict[str, Any]:
        """Optimize quality thresholds based on learning"""
        optimizations = {}
        
        # Analyze quality thresholds across all patterns
        quality_data = []
        for pattern in self.learning_patterns:
            for metric, value in pattern.performance_metrics.items():
                if "score" in metric and value > 0:
                    quality_data.append((metric, value, pattern.success_rate))
        
        if quality_data:
            # Group by metric type
            metric_groups = defaultdict(list)
            for metric, value, success in quality_data:
                metric_groups[metric].append((value, success))
            
            # Find optimal thresholds for each metric
            for metric, data in metric_groups.items():
                if len(data) >= 5:  # Need sufficient data
                    # Find threshold that maximizes success rate
                    sorted_data = sorted(data, key=lambda x: x[0])  # Sort by value
                    
                    best_threshold = 50  # Default
                    best_success_rate = 0
                    
                    for i in range(len(sorted_data)):
                        threshold = sorted_data[i][0]
                        above_threshold = [d for d in sorted_data if d[0] >= threshold]
                        if len(above_threshold) >= 3:  # Need minimum sample
                            avg_success = sum(d[1] for d in above_threshold) / len(above_threshold)
                            if avg_success > best_success_rate:
                                best_success_rate = avg_success
                                best_threshold = threshold
                    
                    optimizations[f"optimal_{metric}_threshold"] = best_threshold
        
        return optimizations
    
    async def _trigger_learning_cycle_if_needed(self):
        """Trigger learning cycle if enough time has passed"""
        hours_since_last_cycle = (datetime.now() - self.last_learning_cycle).total_seconds() / 3600
        
        if hours_since_last_cycle >= 24:  # Daily learning cycle
            await self.analyze_performance_trends()
            await self.auto_optimize_system_parameters()
            self.last_learning_cycle = datetime.now()
    
    def _calculate_context_similarity(self, context1: Dict[str, Any], context2: Dict[str, Any]) -> float:
        """Calculate similarity between two contexts"""
        if not context1 or not context2:
            return 0.0
        
        # Simple key-based similarity
        keys1 = set(context1.keys())
        keys2 = set(context2.keys())
        
        if not keys1 or not keys2:
            return 0.0
        
        common_keys = keys1.intersection(keys2)
        all_keys = keys1.union(keys2)
        
        key_similarity = len(common_keys) / len(all_keys)
        
        # Value similarity for common keys
        value_similarity = 0.0
        if common_keys:
            matches = 0
            for key in common_keys:
                val1 = str(context1[key]).lower()
                val2 = str(context2[key]).lower()
                if val1 == val2:
                    matches += 1
                elif val1 in val2 or val2 in val1:
                    matches += 0.5
            
            value_similarity = matches / len(common_keys)
        
        return (key_similarity + value_similarity) / 2
    
    def _calculate_approach_similarity(self, approach1: Dict[str, Any], approach2: Dict[str, Any]) -> float:
        """Calculate similarity between two approaches"""
        if not approach1 or not approach2:
            return 0.0
        
        # Convert to strings for simple comparison
        str1 = json.dumps(approach1, sort_keys=True, default=str).lower()
        str2 = json.dumps(approach2, sort_keys=True, default=str).lower()
        
        # Simple substring similarity
        if str1 == str2:
            return 1.0
        elif len(str1) > 0 and len(str2) > 0:
            # Check for common substrings
            common_chars = sum(1 for c1, c2 in zip(str1, str2) if c1 == c2)
            max_len = max(len(str1), len(str2))
            return common_chars / max_len if max_len > 0 else 0.0
        else:
            return 0.0
    
    def _cleanup_patterns(self):
        """Clean up old or low-performing patterns"""
        # Sort patterns by success rate and recency
        self.learning_patterns.sort(key=lambda p: (p.success_rate, p.last_used), reverse=True)
        
        # Keep top 100 patterns
        self.learning_patterns = self.learning_patterns[:100]
        
        logger.info(f"🧹 Cleaned up patterns, kept {len(self.learning_patterns)} best patterns")
    
    def _fallback_recommendations(self, patterns: List[LearningPattern]) -> List[Dict[str, Any]]:
        """Fallback recommendations when AI is not available"""
        if not patterns:
            return []
        
        # Simple recommendations based on best patterns
        best_pattern = max(patterns, key=lambda p: p.success_rate)
        
        return [{
            "title": "Use successful approach",
            "description": f"Apply approach from pattern {best_pattern.pattern_id} with {best_pattern.success_rate:.1f}% success rate",
            "confidence": best_pattern.confidence_score,
            "expected_improvement": f"{best_pattern.success_rate - 50:.1f}%",
            "supporting_patterns": [best_pattern.pattern_id]
        }]

# Global instance
autonomous_learning_memory_system = AutonomousLearningMemorySystem()

# Export for easy import
__all__ = ["AutonomousLearningMemorySystem", "autonomous_learning_memory_system", "LearningPattern", "LearningInsight"]