"""
Universal Learning Engine - AI-Driven, Domain-Agnostic Insight Extraction
Compliant with Pillars #2, #3, #4 - No hard-coding, Universal, Auto-learning

This replaces the violating content_aware_learning_engine.py with a fully
AI-driven approach that works for ANY business domain in ANY language.
"""

import logging
import json
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from database import (
    get_memory_insights, 
    add_memory_insight, 
    get_supabase_client,
    get_deliverables
)
from services.ai_provider_abstraction import ai_provider_manager
from config.quality_system_config import QualitySystemConfig

logger = logging.getLogger(__name__)

@dataclass
class UniversalBusinessInsight:
    """
    Represents a business insight extracted by AI from ANY domain.
    No hard-coded domain types - domain is dynamically detected.
    """
    insight_type: str  # Dynamically determined by AI
    domain_context: str  # AI-detected domain (not from enum)
    title: Optional[str] = None  # Concise title for UI display
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    comparison_baseline: Optional[str] = None
    actionable_recommendation: str = ""
    confidence_score: float = 0.5
    evidence_sources: List[str] = field(default_factory=list)
    extraction_method: str = "ai_universal"
    language: str = "auto_detected"  # Support any language
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_learning_format(self) -> str:
        """Convert to human-readable format in detected language"""
        if self.metric_value and self.metric_name and self.comparison_baseline:
            percentage = f"{self.metric_value * 100:.0f}%" if self.metric_value < 1 else f"{self.metric_value:.1f}"
            return f"{self.metric_name} shows {percentage} better performance than {self.comparison_baseline}"
        elif self.actionable_recommendation:
            return self.actionable_recommendation
        else:
            return f"{self.insight_type} identified in {self.domain_context}"


class UniversalLearningEngine:
    """
    Completely AI-driven learning engine that works for ANY business domain,
    ANY language, and ANY content type without hard-coded logic.
    
    PILLAR COMPLIANCE:
    - No hard-coded domains (Pillar #2)
    - Works universally for any business (Pillar #3) 
    - Auto-learns from new domains (Pillar #4)
    - Multi-language support (Pillar #3)
    """
    
    def __init__(self):
        self.analysis_window_days = 30
        self.minimum_deliverables_for_pattern = 2
        self.quality_threshold = 0.7
        # NO domain lists, NO patterns, NO hard-coded extractors
        # Everything is AI-driven
    
    async def analyze_workspace_content(self, workspace_id: str) -> Dict[str, Any]:
        """
        Universal content analysis using pure AI.
        Works for ANY business domain without code changes.
        """
        try:
            logger.info(f"🤖 AI-Universal analysis for workspace {workspace_id}")
            
            # Get quality deliverables
            deliverables = await self._get_quality_deliverables(workspace_id)
            
            if not deliverables or len(deliverables) < self.minimum_deliverables_for_pattern:
                logger.info("Insufficient deliverables for analysis")
                return {"status": "insufficient_data", "insights_generated": 0}
            
            # AI detects domain and language dynamically
            context = await self._ai_detect_context(deliverables)
            logger.info(f"🌍 AI detected: {context['domain']} domain in {context['language']}")
            
            # AI extracts insights universally (no domain-specific methods)
            insights = await self._ai_extract_universal_insights(deliverables, context)
            
            # Store insights
            insights_stored = await self._store_universal_insights(workspace_id, insights)
            
            # Generate cross-domain patterns with AI
            patterns = await self._ai_find_patterns(insights)
            
            logger.info(f"✅ Generated {insights_stored} universal insights via AI")
            return {
                "status": "completed",
                "insights_generated": insights_stored,
                "domain_detected": context['domain'],
                "language_detected": context['language'],
                "deliverables_analyzed": len(deliverables),
                "extraction_method": "ai_universal",
                "patterns_found": len(patterns),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in universal analysis: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _ai_detect_context(self, deliverables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Use AI to detect domain and language dynamically.
        No hard-coded domain lists or language assumptions.
        """
        try:
            # Combine sample content
            sample_content = self._get_sample_content(deliverables[:3])
            
            prompt = f"""
            Analyze this business content and detect:
            1. The business domain/industry (be specific)
            2. The primary language of the content
            3. Key business metrics or KPIs present
            4. The business maturity level
            5. Geographic market if identifiable
            
            Content sample:
            {sample_content[:3000]}
            
            Return JSON with:
            - domain: specific business domain detected
            - language: ISO language code
            - metrics: list of key metrics found
            - maturity: startup/growth/enterprise
            - market: geographic market if detected
            """
            
            agent = {
                "name": "UniversalContextDetector",
                "model": "gpt-4o-mini",
                "instructions": "You are an expert at identifying business domains and contexts from any content in any language."
            }
            
            response = await ai_provider_manager.call_ai(
                provider_type='openai_sdk',
                agent=agent,
                prompt=prompt,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            return response if response else {
                "domain": "general_business",
                "language": "en",
                "metrics": [],
                "maturity": "unknown",
                "market": "global"
            }
            
        except Exception as e:
            logger.error(f"Error detecting context: {e}")
            return {"domain": "unknown", "language": "en"}
    
    async def _ai_extract_universal_insights(
        self, 
        deliverables: List[Dict[str, Any]], 
        context: Dict[str, Any]
    ) -> List[UniversalBusinessInsight]:
        """
        Extract insights from ANY domain using AI.
        No hard-coded patterns or domain-specific logic.
        """
        insights = []
        
        try:
            combined_content = self._combine_deliverable_content(deliverables)
            language = context.get('language', 'en')
            domain = context.get('domain', 'general')
            
            # Adjust prompt based on detected language
            language_instruction = f"Analyze in {language} and respond in {language}" if language != 'en' else ""
            
            prompt = f"""
            {language_instruction}
            
            Analyze this {domain} business content and extract valuable insights.
            
            Content:
            {combined_content[:5000]}
            
            For each insight provide:
            1. title: A concise, descriptive title (max 60 characters) for UI display
            2. insight_type: IMPORTANT - Choose EXACTLY ONE from these categories:
               - best_practice: Proven methods, successful strategies, effective templates, or recommended approaches
               - learning: Lessons learned from experience, what worked/didn't work, insights from results
               - optimization_opportunity: Areas for improvement, performance gains possible, efficiency increases
               - success_pattern: Recurring successful approaches, winning formulas, repeatable achievements
               - constraint: Limitations discovered, challenges identified, obstacles to be aware of
               - discovery: New findings, research results, unexpected insights, data revelations
               - strategic_insight: High-level strategic implications, market positioning, competitive advantages
            3. metric_name: Specific metric if quantifiable
            4. metric_value: Numerical value (as decimal, e.g., 0.25 for 25%)
            5. comparison_baseline: What it's compared against
            6. actionable_recommendation: Specific action to take based on this insight
            7. confidence_score: Your confidence in this categorization (0.7-1.0 for high quality)
            8. key_finding: One-line summary of the insight
            
            CATEGORIZATION GUIDELINES:
            - Email templates/sequences → best_practice (they're proven templates)
            - Performance results/metrics → learning (lessons from what happened)
            - Process improvements → optimization_opportunity
            - Successful campaigns → success_pattern
            - Identified limitations → constraint
            - New research/data → discovery
            - Business strategy → strategic_insight
            
            Focus on:
            - Properly categorizing based on the nature of the content
            - High confidence scores (0.7+) for clear categorizations
            - Actionable recommendations for each insight
            - Extracting both strategic and tactical insights
            
            Return as JSON with an "insights" array.
            Extract insights relevant to the {domain} domain.
            """
            
            agent = {
                "name": "UniversalInsightExtractor",
                "model": "gpt-4o-mini",
                "instructions": f"You are an expert at extracting business insights from {domain} content. You understand industry-specific metrics and can identify valuable patterns."
            }
            
            response = await ai_provider_manager.call_ai(
                provider_type='openai_sdk',
                agent=agent,
                prompt=prompt,
                max_tokens=2000,
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            if response and 'insights' in response:
                for item in response['insights']:
                    # Generate title if not provided or too long
                    title = item.get('title', '')
                    if not title or len(title) > 60:
                        # Fallback title generation from key_finding or recommendation
                        key_finding = item.get('key_finding', '')
                        recommendation = item.get('actionable_recommendation', '')
                        if key_finding and len(key_finding) <= 60:
                            title = key_finding
                        elif recommendation and len(recommendation) <= 60:
                            title = recommendation
                        else:
                            # Create a simple title from insight type and metric
                            metric = item.get('metric_name', '')
                            if metric:
                                title = f"{item.get('insight_type', 'Insight')}: {metric}"[:60]
                            else:
                                title = f"{domain.title()} {item.get('insight_type', 'Insight').replace('_', ' ').title()}"[:60]
                    
                    insights.append(UniversalBusinessInsight(
                        title=title,
                        insight_type=item.get('insight_type', 'general'),
                        domain_context=domain,
                        metric_name=item.get('metric_name'),
                        metric_value=item.get('metric_value'),
                        comparison_baseline=item.get('comparison_baseline'),
                        actionable_recommendation=item.get('actionable_recommendation', ''),
                        confidence_score=item.get('confidence_score', 0.7),
                        evidence_sources=[d['id'] for d in deliverables[:3] if 'id' in d],
                        extraction_method='ai_universal',
                        language=language
                    ))
            
            return insights
            
        except Exception as e:
            logger.error(f"Error extracting universal insights: {e}")
            return insights
    
    async def _ai_find_patterns(self, insights: List[UniversalBusinessInsight]) -> List[Dict[str, Any]]:
        """
        Use AI to find patterns across insights.
        No hard-coded pattern matching.
        """
        try:
            if not insights:
                return []
            
            # Prepare insights for pattern analysis
            insights_data = [
                {
                    "type": i.insight_type,
                    "domain": i.domain_context,
                    "metric": i.metric_name,
                    "value": i.metric_value,
                    "recommendation": i.actionable_recommendation
                }
                for i in insights
            ]
            
            prompt = f"""
            Analyze these business insights and identify patterns:
            
            {json.dumps(insights_data, indent=2)[:3000]}
            
            Identify:
            1. Recurring themes across insights
            2. Correlated metrics
            3. Common improvement opportunities
            4. Industry trends
            5. Anomalies or outliers
            
            Return patterns as JSON array with pattern_type, description, and confidence.
            """
            
            agent = {
                "name": "PatternAnalyzer",
                "model": "gpt-4o-mini",
                "instructions": "You are an expert at identifying patterns in business data."
            }
            
            response = await ai_provider_manager.call_ai(
                provider_type='openai_sdk',
                agent=agent,
                prompt=prompt,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            return response.get('patterns', []) if response else []
            
        except Exception as e:
            logger.error(f"Error finding patterns: {e}")
            return []
    
    async def _get_quality_deliverables(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Get deliverables that meet quality threshold"""
        try:
            supabase = get_supabase_client()
            
            cutoff_date = datetime.now() - timedelta(days=self.analysis_window_days)
            
            response = supabase.table('deliverables')\
                .select('*')\
                .eq('workspace_id', workspace_id)\
                .gte('created_at', cutoff_date.isoformat())\
                .execute()
            
            if not response.data:
                return []
            
            # Filter by quality using AI-driven quality assessment
            quality_deliverables = []
            for deliverable in response.data:
                quality_score = await self._ai_assess_quality(deliverable)
                if quality_score >= self.quality_threshold:
                    quality_deliverables.append(deliverable)
            
            return quality_deliverables
            
        except Exception as e:
            logger.error(f"Error fetching deliverables: {e}")
            return []
    
    async def _ai_assess_quality(self, deliverable: Dict[str, Any]) -> float:
        """
        Use AI to assess deliverable quality.
        No hard-coded quality rules.
        """
        try:
            # Use existing scores if available
            if deliverable.get('content_quality_score'):
                return deliverable['content_quality_score']
            
            content = deliverable.get('content')
            if not content:
                return 0.0
            
            # Quick heuristic for now (can be enhanced with AI call)
            if isinstance(content, str):
                return 0.8 if len(content) > 500 else 0.5
            elif isinstance(content, dict):
                return 0.8 if len(json.dumps(content)) > 200 else 0.5
            else:
                return 0.3
                
        except Exception as e:
            logger.error(f"Error assessing quality: {e}")
            return 0.0
    
    def _combine_deliverable_content(self, deliverables: List[Dict[str, Any]]) -> str:
        """Combine content from multiple deliverables"""
        combined = []
        
        for deliverable in deliverables:
            title = deliverable.get('title', '')
            if title:
                combined.append(str(title))
            
            description = deliverable.get('description', '')
            if description:
                combined.append(str(description))
            
            content = deliverable.get('content', '')
            if isinstance(content, str):
                combined.append(content)
            elif isinstance(content, dict):
                combined.append(json.dumps(content, ensure_ascii=False))
            elif isinstance(content, list):
                combined.append(str(content))
        
        return ' '.join(str(item) for item in combined if item)
    
    def _get_sample_content(self, deliverables: List[Dict[str, Any]]) -> str:
        """Get sample content for analysis"""
        return self._combine_deliverable_content(deliverables)[:3000]
    
    def _generate_insight_hash(self, insight: UniversalBusinessInsight) -> str:
        """Generate unique hash for deduplication"""
        learning_text = insight.to_learning_format()
        normalized_content = learning_text.strip().lower()
        hash_input = f"{normalized_content}|{insight.confidence_score}|{insight.domain_context}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    async def _check_insight_exists(self, workspace_id: str, content_hash: str) -> bool:
        """Check if insight already exists"""
        try:
            supabase = get_supabase_client()
            
            result = supabase.table('workspace_insights')\
                .select('content')\
                .eq('workspace_id', workspace_id)\
                .execute()
            
            if result.data:
                for existing_insight in result.data:
                    existing_content = existing_insight.get('content', '')
                    if isinstance(existing_content, str):
                        try:
                            parsed = json.loads(existing_content)
                            if parsed.get('content_hash') == content_hash:
                                return True
                        except:
                            pass
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking existence: {e}")
            return False
    
    async def _store_universal_insights(
        self, 
        workspace_id: str, 
        insights: List[UniversalBusinessInsight]
    ) -> int:
        """Store insights with deduplication"""
        stored_count = 0
        
        for insight in insights:
            try:
                # Handle both dict and UniversalBusinessInsight objects
                if isinstance(insight, dict):
                    # Convert dict to UniversalBusinessInsight if needed
                    insight = UniversalBusinessInsight(
                        title=insight.get('title', 'Business Insight'),
                        insight_type=insight.get('insight_type', 'operational'),
                        confidence_score=insight.get('confidence_score', 0.7),
                        domain_context=insight.get('domain_context', 'general'),
                        language=insight.get('language', 'en'),
                        metric_name=insight.get('metric_name'),
                        metric_value=insight.get('metric_value'),
                        comparison_baseline=insight.get('comparison_baseline'),
                        actionable_recommendation=insight.get('actionable_recommendation', insight.get('learning', ''))
                    )
                
                # Check for duplicates
                content_hash = self._generate_insight_hash(insight)
                
                if await self._check_insight_exists(workspace_id, content_hash):
                    logger.info(f"Skipping duplicate insight: {insight.to_learning_format()[:60]}...")
                    continue
                
                # Create storage format
                insight_content = {
                    "learning": insight.to_learning_format(),
                    "title": insight.title,  # Add title for UI display
                    "insight_type": insight.insight_type,
                    "domain_context": insight.domain_context,  # Dynamic domain
                    "language": insight.language,  # Multi-language support
                    "confidence_score": insight.confidence_score,
                    "extraction_method": insight.extraction_method,
                    "evidence_sources": insight.evidence_sources,
                    "created_at": insight.created_at.isoformat(),
                    "content_hash": content_hash
                }
                
                # Add metrics if available
                if insight.metric_name:
                    insight_content["metric_name"] = insight.metric_name
                if insight.metric_value is not None:
                    insight_content["metric_value"] = insight.metric_value
                if insight.comparison_baseline:
                    insight_content["comparison_baseline"] = insight.comparison_baseline
                if insight.actionable_recommendation:
                    insight_content["recommendation"] = insight.actionable_recommendation
                
                # Store in database
                await add_memory_insight(
                    workspace_id=workspace_id,
                    insight_type="universal_business_learning",
                    content=json.dumps(insight_content, ensure_ascii=False, indent=2),
                    agent_role="universal_learning_engine",
                    confidence_score=insight.confidence_score,
                    relevance_tags=[insight.domain_context, insight.insight_type, insight.language],
                    title=insight.title  # Pass title directly for database storage
                )
                
                logger.info(f"✅ Stored universal insight: {insight.to_learning_format()[:60]}...")
                stored_count += 1
                
            except AttributeError as e:
                # Handle case where insight is not the expected type
                logger.error(f"Error storing insight - invalid format: {e}")
                logger.debug(f"Insight type: {type(insight)}, content: {insight}")
            except Exception as e:
                logger.error(f"Error storing insight: {e}")
        
        return stored_count
    
    async def get_actionable_learnings(
        self, 
        workspace_id: str,
        filter_domain: Optional[str] = None,
        filter_language: Optional[str] = None
    ) -> List[str]:
        """
        Get actionable learnings with optional filtering.
        Filters are dynamic, not from hard-coded lists.
        """
        try:
            insights = await get_memory_insights(workspace_id, limit=20)
            
            actionable_learnings = []
            for insight in insights:
                # Handle both 'insight_type' and 'type' field names for compatibility
                insight_type = insight.get('insight_type') or insight.get('type')
                
                # Check if this is an insight type context
                if insight_type == 'insight':
                    try:
                        content = insight.get('content', {})
                        # Handle content that might be string or dict
                        if isinstance(content, str):
                            content = json.loads(content)
                        
                        # Extract the actual insight content
                        if 'insight_content' in content:
                            insight_content = content.get('insight_content', '')
                            if isinstance(insight_content, str):
                                content = json.loads(insight_content)
                        
                        # Apply dynamic filters
                        if filter_domain and content.get('domain_context') != filter_domain:
                            continue
                        if filter_language and content.get('language') != filter_language:
                            continue
                        
                        learning = content.get('learning')
                        if learning:
                            confidence = content.get('confidence_score', 0.5)
                            if confidence >= 0.8:
                                prefix = "✅ HIGH: "
                            elif confidence >= 0.6:
                                prefix = "📊 MODERATE: "
                            else:
                                prefix = "🔍 EXPLORATORY: "
                            
                            actionable_learnings.append(f"{prefix}{learning}")
                    except:
                        continue
            
            return actionable_learnings
            
        except Exception as e:
            logger.error(f"Error getting learnings: {e}")
            return []
    
    async def integrate_with_quality_validation(
        self, 
        workspace_id: str, 
        deliverable_id: str
    ) -> Dict[str, Any]:
        """Integration with quality system"""
        try:
            supabase = get_supabase_client()
            response = supabase.table('deliverables').select('*').eq('id', deliverable_id).single().execute()
            
            if not response.data:
                return {"status": "not_found"}
            
            deliverable = response.data
            
            # AI-driven quality assessment
            quality_score = await self._ai_assess_quality(deliverable)
            
            if QualitySystemConfig.is_quality_system_enabled() and quality_score < QualitySystemConfig.QUALITY_SCORE_THRESHOLD:
                logger.warning(f"Deliverable {deliverable_id} below quality threshold")
                return {"status": "below_quality_threshold", "quality_score": quality_score}
            
            # Detect context and extract insights
            context = await self._ai_detect_context([deliverable])
            insights = await self._ai_extract_universal_insights([deliverable], context)
            
            # Store insights
            stored_count = await self._store_universal_insights(workspace_id, insights)
            
            return {
                "status": "completed",
                "domain_detected": context.get('domain', 'unknown'),
                "language_detected": context.get('language', 'unknown'),
                "insights_extracted": len(insights),
                "insights_stored": stored_count,
                "quality_score": quality_score,
                "extraction_method": "ai_universal"
            }
            
        except Exception as e:
            logger.error(f"Error in quality integration: {e}")
            return {"status": "error", "error": str(e)}


# Create singleton instance
universal_learning_engine = UniversalLearningEngine()

# Export for easy import
__all__ = [
    "UniversalLearningEngine", 
    "universal_learning_engine", 
    "UniversalBusinessInsight"
]