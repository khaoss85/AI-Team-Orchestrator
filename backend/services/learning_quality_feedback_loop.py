"""
Learning-Quality Feedback Loop Integration - Performance Boost System
Integrates Content-Aware Learning with Quality Validation for continuous improvement
"""

import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum

from services.universal_learning_engine import (
    universal_learning_engine,
    UniversalBusinessInsight as BusinessInsight
)
# Note: str enum removed as Universal Learning Engine is domain-agnostic
from ai_quality_assurance.unified_quality_engine import unified_quality_engine
from database import (
    get_supabase_client,
    get_deliverables,
    get_memory_insights,
    add_memory_insight,
    update_task_fields
)
from services.ai_provider_abstraction import ai_provider_manager
from config.quality_system_config import QualitySystemConfig

logger = logging.getLogger(__name__)

class FeedbackLoopMode(str, Enum):
    """Feedback loop operation modes"""
    LEARNING_DRIVEN = "learning_driven"  # Insights drive quality criteria
    QUALITY_DRIVEN = "quality_driven"    # Quality drives learning extraction
    BIDIRECTIONAL = "bidirectional"      # Both influence each other
    PERFORMANCE_BOOST = "performance_boost"  # Maximum optimization mode

@dataclass
class QualityLearningFeedback:
    """Represents a feedback connection between quality and learning"""
    feedback_type: str  # e.g., "quality_improvement", "insight_validation"
    source_system: str  # "learning_engine" or "quality_engine"
    target_system: str  # "learning_engine" or "quality_engine"
    insight_applied: Optional[BusinessInsight] = None
    quality_impact: Optional[float] = None  # Change in quality score
    performance_boost: Optional[float] = None  # Improvement percentage
    domain: Optional[str] = None  # Dynamic domain string instead of enum
    confidence: float = 0.5
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "feedback_type": self.feedback_type,
            "source_system": self.source_system,
            "target_system": self.target_system,
            "quality_impact": self.quality_impact,
            "performance_boost": self.performance_boost,
            "domain": self.domain.value if self.domain else None,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat()
        }

class LearningQualityFeedbackLoop:
    """
    Integrates Content-Aware Learning with Quality Validation Engine
    Creates a performance-boosting feedback loop for continuous improvement
    """
    
    def __init__(self):
        self.learning_engine = universal_learning_engine
        self.quality_engine = unified_quality_engine
        self.mode = FeedbackLoopMode.PERFORMANCE_BOOST
        
        # Performance tracking
        self.baseline_quality_scores = defaultdict(float)
        self.quality_improvements = defaultdict(list)
        self.applied_insights_count = 0
        self.performance_boost_percentage = 0.0
        
        # Domain-specific quality criteria enhanced by learning
        self.domain_quality_criteria = {
            'instagram_marketing': {
                "base_threshold": 0.7,
                "learned_criteria": [],
                "performance_multiplier": 1.0
            },
            'email_marketing': {
                "base_threshold": 0.7,
                "learned_criteria": [],
                "performance_multiplier": 1.0
            },
            'content_strategy': {
                "base_threshold": 0.65,
                "learned_criteria": [],
                "performance_multiplier": 1.0
            },
            'lead_generation': {
                "base_threshold": 0.75,
                "learned_criteria": [],
                "performance_multiplier": 1.0
            }
        }
        
        logger.info("🔄 Learning-Quality Feedback Loop initialized in PERFORMANCE_BOOST mode")
    
    async def process_deliverable_with_feedback_loop(
        self, 
        workspace_id: str, 
        deliverable_id: str,
        force_learning: bool = False
    ) -> Dict[str, Any]:
        """
        Process a deliverable through the complete feedback loop
        1. Quality validation with learned criteria
        2. Learning extraction from high-quality content
        3. Update quality criteria with new insights
        4. Measure performance boost
        """
        try:
            logger.info(f"🔄 Processing deliverable {deliverable_id} through feedback loop")
            
            # Get deliverable data
            supabase = get_supabase_client()
            response = supabase.table('deliverables').select('*').eq('id', deliverable_id).single().execute()
            
            if not response.data:
                return {"status": "not_found", "error": "Deliverable not found"}
            
            deliverable = response.data
            
            # Step 1: Detect domain for specialized processing
            domain = await self.learning_engine._detect_deliverable_domain(deliverable)
            logger.info(f"📊 Domain detected: {domain.value}")
            
            # Step 2: Get domain-specific learned insights
            learned_insights = await self._get_domain_insights(workspace_id, domain)
            
            # Step 3: Enhanced quality validation using learned insights
            quality_result = await self._quality_validation_with_insights(
                deliverable, 
                domain, 
                learned_insights
            )
            
            # Step 4: Learning extraction if quality is high enough
            learning_result = None
            if quality_result['quality_score'] >= 0.7 or force_learning:
                learning_result = await self._extract_and_store_learnings(
                    workspace_id,
                    deliverable,
                    domain,
                    quality_result['quality_score']
                )
            
            # Step 5: Update domain quality criteria with new learnings
            if learning_result and learning_result.get('insights_stored', 0) > 0:
                await self._update_quality_criteria_from_learnings(
                    domain,
                    learning_result.get('insights', [])
                )
            
            # Step 6: Calculate performance boost
            performance_metrics = await self._calculate_performance_boost(
                workspace_id,
                domain,
                quality_result['quality_score']
            )
            
            # Step 7: Store feedback loop metrics
            feedback = QualityLearningFeedback(
                feedback_type="bidirectional_optimization",
                source_system="feedback_loop",
                target_system="both",
                quality_impact=quality_result['quality_score'] - self.baseline_quality_scores[domain],
                performance_boost=performance_metrics['boost_percentage'],
                domain=domain,
                confidence=0.9
            )
            
            await self._store_feedback_metrics(workspace_id, feedback)
            
            return {
                "status": "success",
                "deliverable_id": deliverable_id,
                "domain": domain.value,
                "quality_validation": quality_result,
                "learning_extraction": learning_result,
                "performance_metrics": performance_metrics,
                "feedback_loop_active": True,
                "mode": self.mode.value,
                "insights_applied": len(learned_insights),
                "quality_criteria_updated": learning_result is not None,
                "performance_boost": f"{performance_metrics['boost_percentage']:.1f}%"
            }
            
        except Exception as e:
            logger.error(f"Error in feedback loop processing: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _quality_validation_with_insights(
        self,
        deliverable: Dict[str, Any],
        domain: str,
        learned_insights: List[BusinessInsight]
    ) -> Dict[str, Any]:
        """Enhanced quality validation using learned business insights"""
        try:
            logger.info(f"🎯 Quality validation with {len(learned_insights)} learned insights")
            
            # Base quality validation
            content = deliverable.get('content', '')
            if isinstance(content, dict):
                content = json.dumps(content)
            
            base_result = await self.quality_engine.validate_asset_quality(
                asset_content=content,
                asset_type=deliverable.get('title', 'deliverable'),
                workspace_id=deliverable.get('workspace_id', ''),
                domain_context=domain.value
            )
            
            # Enhance with learned insights
            if learned_insights and base_result['quality_score'] > 0:
                # Apply insight-based quality adjustments
                quality_adjustments = []
                
                for insight in learned_insights:
                    # Check if deliverable follows learned best practices
                    if insight.actionable_recommendation:
                        adjustment = await self._check_insight_compliance(
                            content,
                            insight.actionable_recommendation,
                            insight.confidence_score
                        )
                        quality_adjustments.append(adjustment)
                
                # Calculate adjusted quality score
                if quality_adjustments:
                    avg_adjustment = sum(quality_adjustments) / len(quality_adjustments)
                    adjusted_score = base_result['quality_score'] * (1 + avg_adjustment)
                    adjusted_score = min(1.0, adjusted_score)  # Cap at 1.0
                    
                    logger.info(f"✅ Quality score adjusted from {base_result['quality_score']:.2f} to {adjusted_score:.2f}")
                    
                    base_result['quality_score'] = adjusted_score
                    base_result['insights_applied'] = len(learned_insights)
                    base_result['learning_enhanced'] = True
            
            # Add domain-specific quality criteria
            domain_criteria = self.domain_quality_criteria.get(domain, {})
            if domain_criteria.get('learned_criteria'):
                base_result['domain_criteria_applied'] = len(domain_criteria['learned_criteria'])
                base_result['performance_multiplier'] = domain_criteria.get('performance_multiplier', 1.0)
            
            return base_result
            
        except Exception as e:
            logger.error(f"Error in quality validation with insights: {e}")
            return {
                'quality_score': 0.5,
                'needs_enhancement': True,
                'reason': f'Validation error: {str(e)}',
                'learning_enhanced': False
            }
    
    async def _check_insight_compliance(
        self,
        content: str,
        recommendation: str,
        confidence: float
    ) -> float:
        """Check if content follows a learned recommendation"""
        try:
            # Use AI to check compliance
            prompt = f"""Analyze if this content follows the recommendation.

RECOMMENDATION: {recommendation}

CONTENT (first 1000 chars): {content[:1000]}

Does the content follow the recommendation? Return a compliance score from -0.2 to +0.2 where:
- Negative values mean it violates the recommendation
- 0 means neutral/unclear
- Positive values mean it follows the recommendation

Return JSON: {{"compliance_score": float, "reasoning": "brief explanation"}}"""

            agent = {
                "name": "ComplianceChecker",
                "model": "gpt-4o-mini",
                "instructions": "Check if content follows business best practices."
            }
            
            response = await ai_provider_manager.call_ai(
                provider_type='openai_sdk',
                agent=agent,
                prompt=prompt,
                max_tokens=200,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            if response and isinstance(response, dict):
                compliance = response.get('compliance_score', 0.0)
                # Weight by confidence in the original insight
                return compliance * confidence
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error checking insight compliance: {e}")
            return 0.0
    
    async def _extract_and_store_learnings(
        self,
        workspace_id: str,
        deliverable: Dict[str, Any],
        domain: str,
        quality_score: float
    ) -> Dict[str, Any]:
        """Extract learnings from high-quality deliverables"""
        try:
            logger.info(f"📚 Extracting learnings from deliverable (quality: {quality_score:.2f})")
            
            # Use content-aware learning engine for extraction
            insights = await self.learning_engine._extract_domain_insights(
                domain,
                [deliverable]
            )
            
            if insights:
                # Filter insights by confidence and quality
                high_value_insights = [
                    i for i in insights 
                    if i.confidence_score >= 0.7 and quality_score >= 0.7
                ]
                
                # Store the high-value insights
                stored_count = 0
                for insight in high_value_insights:
                    success = await self.learning_engine._store_insight(
                        workspace_id,
                        insight
                    )
                    if success:
                        stored_count += 1
                        self.applied_insights_count += 1
                
                logger.info(f"✅ Stored {stored_count} high-value insights from quality content")
                
                return {
                    "insights_extracted": len(insights),
                    "insights_stored": stored_count,
                    "insights": high_value_insights,
                    "quality_filter_applied": True
                }
            
            return {
                "insights_extracted": 0,
                "insights_stored": 0,
                "insights": []
            }
            
        except Exception as e:
            logger.error(f"Error extracting learnings: {e}")
            return {"insights_extracted": 0, "insights_stored": 0, "error": str(e)}
    
    async def _update_quality_criteria_from_learnings(
        self,
        domain: str,
        new_insights: List[BusinessInsight]
    ) -> None:
        """Update domain-specific quality criteria based on new learnings"""
        try:
            if not new_insights:
                return
            
            logger.info(f"🔧 Updating quality criteria for {domain.value} with {len(new_insights)} insights")
            
            domain_criteria = self.domain_quality_criteria.get(domain, {})
            learned_criteria = domain_criteria.get('learned_criteria', [])
            
            for insight in new_insights:
                # Convert insight to quality criterion
                criterion = {
                    "type": insight.insight_type,
                    "requirement": insight.actionable_recommendation,
                    "importance": insight.confidence_score,
                    "metric": insight.metric_name,
                    "target_value": insight.metric_value,
                    "added_at": datetime.now().isoformat()
                }
                
                # Avoid duplicates
                if not any(c['requirement'] == criterion['requirement'] for c in learned_criteria):
                    learned_criteria.append(criterion)
            
            # Update performance multiplier based on accumulated learnings
            if len(learned_criteria) > 5:
                domain_criteria['performance_multiplier'] = 1.1  # 10% boost
            if len(learned_criteria) > 10:
                domain_criteria['performance_multiplier'] = 1.2  # 20% boost
            if len(learned_criteria) > 20:
                domain_criteria['performance_multiplier'] = 1.3  # 30% boost
            
            domain_criteria['learned_criteria'] = learned_criteria
            self.domain_quality_criteria[domain] = domain_criteria
            
            logger.info(f"✅ Quality criteria updated. Performance multiplier: {domain_criteria['performance_multiplier']}")
            
        except Exception as e:
            logger.error(f"Error updating quality criteria: {e}")
    
    async def _get_domain_insights(
        self,
        workspace_id: str,
        domain: str
    ) -> List[BusinessInsight]:
        """Get relevant learned insights for a domain"""
        try:
            # Get insights from database
            insights_data = await get_memory_insights(workspace_id, limit=50)
            
            domain_insights = []
            for insight_record in insights_data:
                if insight_record.get('insight_type') == 'business_learning':
                    try:
                        content = json.loads(insight_record.get('content', '{}'))
                        if content.get('domain') == domain.value:
                            # Reconstruct BusinessInsight
                            insight = BusinessInsight(
                                insight_type=content.get('insight_type', 'unknown'),
                                domain=domain,
                                metric_name=content.get('metric_name'),
                                metric_value=content.get('metric_value'),
                                comparison_baseline=content.get('comparison_baseline'),
                                actionable_recommendation=content.get('recommendation', ''),
                                confidence_score=content.get('confidence_score', 0.5),
                                evidence_sources=content.get('evidence_sources', []),
                                extraction_method=content.get('extraction_method', 'unknown')
                            )
                            domain_insights.append(insight)
                    except Exception as e:
                        logger.warning(f"Error parsing insight: {e}")
                        continue
            
            # Sort by confidence score
            domain_insights.sort(key=lambda x: x.confidence_score, reverse=True)
            
            # Return top insights
            return domain_insights[:10]
            
        except Exception as e:
            logger.error(f"Error getting domain insights: {e}")
            return []
    
    async def _calculate_performance_boost(
        self,
        workspace_id: str,
        domain: str,
        current_quality: float
    ) -> Dict[str, Any]:
        """Calculate the performance boost from the feedback loop"""
        try:
            # Track baseline if not set
            if domain not in self.baseline_quality_scores:
                self.baseline_quality_scores[domain] = current_quality
                return {
                    "boost_percentage": 0.0,
                    "baseline_set": True,
                    "current_quality": current_quality,
                    "trend": "establishing_baseline"
                }
            
            # Calculate improvement
            baseline = self.baseline_quality_scores[domain]
            improvement = current_quality - baseline
            boost_percentage = (improvement / baseline) * 100 if baseline > 0 else 0
            
            # Track improvement history
            self.quality_improvements[domain].append({
                "timestamp": datetime.now().isoformat(),
                "quality": current_quality,
                "improvement": improvement,
                "boost": boost_percentage
            })
            
            # Calculate trend
            recent_improvements = self.quality_improvements[domain][-5:]
            if len(recent_improvements) >= 2:
                trend = "improving" if recent_improvements[-1]['quality'] > recent_improvements[0]['quality'] else "stable"
            else:
                trend = "measuring"
            
            # Update overall performance boost
            all_boosts = [imp['boost'] for improvements in self.quality_improvements.values() 
                         for imp in improvements if 'boost' in imp]
            if all_boosts:
                self.performance_boost_percentage = sum(all_boosts) / len(all_boosts)
            
            metrics = {
                "boost_percentage": boost_percentage,
                "baseline_quality": baseline,
                "current_quality": current_quality,
                "improvement": improvement,
                "trend": trend,
                "insights_applied": self.applied_insights_count,
                "domain_multiplier": self.domain_quality_criteria[domain].get('performance_multiplier', 1.0),
                "overall_boost": self.performance_boost_percentage
            }
            
            logger.info(f"📈 Performance boost: {boost_percentage:.1f}% for {domain.value}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating performance boost: {e}")
            return {
                "boost_percentage": 0.0,
                "error": str(e)
            }
    
    async def _store_feedback_metrics(
        self,
        workspace_id: str,
        feedback: QualityLearningFeedback
    ) -> None:
        """Store feedback loop metrics for analysis"""
        try:
            await add_memory_insight(
                workspace_id=workspace_id,
                insight_type="feedback_loop_metrics",
                content=json.dumps(feedback.to_dict(), indent=2),
                agent_role="feedback_loop_system",
                confidence_score=feedback.confidence,
                relevance_tags=["performance_boost", "quality_learning", feedback.domain.value if feedback.domain else "general"]
            )
            
            logger.info(f"✅ Stored feedback metrics: {feedback.feedback_type}")
            
        except Exception as e:
            logger.error(f"Error storing feedback metrics: {e}")
    
    async def enhance_task_execution_with_learnings(
        self,
        workspace_id: str,
        task_id: str,
        agent_role: str
    ) -> Dict[str, Any]:
        """
        Enhance task execution by providing relevant learned insights to the agent
        This enables agents to produce higher quality deliverables based on past learnings
        """
        try:
            logger.info(f"🚀 Enhancing task {task_id} execution with learned insights")
            
            # Detect likely domain from agent role
            domain = await self._infer_domain_from_agent(agent_role)
            
            # Get relevant insights for this domain
            insights = await self._get_domain_insights(workspace_id, domain)
            
            if not insights:
                return {
                    "enhanced": False,
                    "reason": "No relevant insights available yet"
                }
            
            # Format insights as execution hints
            execution_hints = []
            for insight in insights[:5]:  # Top 5 most relevant
                hint = {
                    "type": "learned_best_practice",
                    "recommendation": insight.actionable_recommendation,
                    "confidence": insight.confidence_score,
                    "evidence": f"Based on {len(insight.evidence_sources)} successful deliverables"
                }
                
                if insight.metric_name and insight.metric_value:
                    hint["metric"] = {
                        "name": insight.metric_name,
                        "target": insight.metric_value,
                        "baseline": insight.comparison_baseline
                    }
                
                execution_hints.append(hint)
            
            # Store hints in task metadata for agent to use
            supabase = get_supabase_client()
            
            # Get current task data
            task_response = supabase.table('tasks').select('*').eq('id', task_id).single().execute()
            if not task_response.data:
                return {"enhanced": False, "error": "Task not found"}
            
            task = task_response.data
            metadata = task.get('metadata', {})
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            
            # Add execution hints to metadata
            metadata['execution_hints'] = execution_hints
            metadata['learning_enhanced'] = True
            metadata['domain_context'] = domain.value
            metadata['quality_boost_expected'] = self.domain_quality_criteria[domain].get('performance_multiplier', 1.0)
            
            # Update task with enhanced metadata
            await update_task_fields(
                task_id,
                {"metadata": json.dumps(metadata)}
            )
            
            logger.info(f"✅ Task enhanced with {len(execution_hints)} learned insights")
            
            return {
                "enhanced": True,
                "insights_provided": len(execution_hints),
                "domain": domain.value,
                "expected_quality_boost": f"{(metadata['quality_boost_expected'] - 1) * 100:.0f}%",
                "hints": execution_hints
            }
            
        except Exception as e:
            logger.error(f"Error enhancing task execution: {e}")
            return {"enhanced": False, "error": str(e)}
    
    async def _infer_domain_from_agent(self, agent_role: str) -> str:
        """🤖 AI-DRIVEN: Infer business domain from agent role using semantic understanding"""
        try:
            domain_classification = await self._classify_agent_domain_ai(agent_role)
            return domain_classification if domain_classification else 'general'
        except Exception as e:
            logger.warning(f"AI agent domain classification failed: {e}, using fallback")
            return 'general'
    
    async def _classify_agent_domain_ai(self, agent_role: str) -> Optional[str]:
        """🤖 AI-DRIVEN: Classify agent role into business domain using semantic analysis"""
        # 🤖 SELF-CONTAINED: Create agent domain classifier config internally
        AGENT_DOMAIN_CLASSIFIER_CONFIG = {
            "name": "AgentDomainClassifier",
            "instructions": """
                You are a business domain classification specialist.
                Classify AI agent roles into business domains for performance optimization.
                Focus on the primary business function, not just keywords.
            """,
            "model": "gpt-4o-mini"
        }
        
        # Define valid domain types for classification
        valid_domains = [
            'instagram_marketing', 'email_marketing', 'content_strategy', 
            'lead_generation', 'data_analysis', 'business_strategy',
            'general'
        ]
        
        domains_str = ", ".join(valid_domains)
        
        prompt = f"""Classify this AI agent role into a business domain:

AGENT ROLE: {agent_role}

Choose the most appropriate domain from:
{domains_str}

Consider the primary business function and purpose of this role.
Return only the exact domain name from the list above.

Domain:"""
        
        try:
            result = await ai_provider_manager.call_ai(
                provider_type='openai_sdk',
                agent=AGENT_DOMAIN_CLASSIFIER_CONFIG,
                prompt=prompt
            )
            
            classification = result.get('content', '').strip().lower() if result else None
            return classification if classification in valid_domains else None
        except Exception as e:
            logger.warning(f"AI agent domain classification error: {e}")
            return None
    
    async def get_performance_report(self, workspace_id: str) -> Dict[str, Any]:
        """Generate a comprehensive performance report showing feedback loop effectiveness"""
        try:
            report = {
                "overall_performance_boost": f"{self.performance_boost_percentage:.1f}%",
                "insights_applied_total": self.applied_insights_count,
                "feedback_loop_mode": self.mode.value,
                "domain_performance": {},
                "quality_trends": {},
                "top_insights": [],
                "recommendations": []
            }
            
            # Domain-specific performance
            for domain, improvements in self.quality_improvements.items():
                if improvements:
                    latest = improvements[-1]
                    report["domain_performance"][domain.value] = {
                        "current_quality": latest.get('quality', 0),
                        "boost_percentage": latest.get('boost', 0),
                        "trend": "improving" if len(improvements) > 1 and improvements[-1]['quality'] > improvements[0]['quality'] else "stable",
                        "samples": len(improvements)
                    }
            
            # Quality criteria evolution
            for domain, criteria in self.domain_quality_criteria.items():
                if criteria.get('learned_criteria'):
                    report["quality_trends"][domain.value] = {
                        "learned_criteria_count": len(criteria['learned_criteria']),
                        "performance_multiplier": criteria.get('performance_multiplier', 1.0),
                        "maturity": "advanced" if len(criteria['learned_criteria']) > 10 else "developing"
                    }
            
            # Top performing insights
            insights = await get_memory_insights(workspace_id, limit=100)
            business_insights = [
                i for i in insights 
                if i.get('insight_type') == 'business_learning'
            ]
            
            if business_insights:
                # Sort by confidence
                business_insights.sort(
                    key=lambda x: json.loads(x.get('content', '{}')).get('confidence_score', 0),
                    reverse=True
                )
                
                for insight_data in business_insights[:5]:
                    content = json.loads(insight_data.get('content', '{}'))
                    report["top_insights"].append({
                        "learning": content.get('learning', ''),
                        "domain": content.get('domain', 'general'),
                        "confidence": content.get('confidence_score', 0),
                        "type": content.get('insight_type', 'unknown')
                    })
            
            # Generate recommendations
            if self.performance_boost_percentage < 10:
                report["recommendations"].append(
                    "Continue collecting high-quality deliverables to build insight database"
                )
            elif self.performance_boost_percentage < 20:
                report["recommendations"].append(
                    "Focus on domains with lower performance to maximize improvement potential"
                )
            else:
                report["recommendations"].append(
                    "Excellent performance! Consider sharing insights across workspaces"
                )
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {"error": str(e)}

# Create singleton instance
learning_quality_feedback_loop = LearningQualityFeedbackLoop()

# Export for easy import
__all__ = [
    "LearningQualityFeedbackLoop",
    "learning_quality_feedback_loop",
    "QualityLearningFeedback",
    "FeedbackLoopMode"
]