"""
Content-Aware Learning Engine - Extract Business-Valuable Insights from Deliverable Content
Evolves learning extraction from generic statistics to domain-specific, actionable insights
"""

import logging
import json
import re
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from enum import Enum

from database import (
    get_memory_insights, 
    add_memory_insight, 
    get_supabase_client,
    get_deliverables
)
from services.ai_provider_abstraction import ai_provider_manager
from config.quality_system_config import QualitySystemConfig

logger = logging.getLogger(__name__)

class DomainType(str, Enum):
    """Business domains for specialized learning extraction"""
    INSTAGRAM_MARKETING = "instagram_marketing"
    EMAIL_MARKETING = "email_marketing"
    CONTENT_STRATEGY = "content_strategy"
    LEAD_GENERATION = "lead_generation"
    DATA_ANALYSIS = "data_analysis"
    BUSINESS_STRATEGY = "business_strategy"
    TECHNICAL_DOCUMENTATION = "technical_documentation"
    PRODUCT_DEVELOPMENT = "product_development"
    GENERAL = "general"

@dataclass
class BusinessInsight:
    """Represents a business-valuable insight extracted from content"""
    insight_type: str  # e.g., "engagement_pattern", "conversion_rate", "best_practice"
    domain: DomainType
    metric_name: Optional[str] = None  # e.g., "carousel_engagement_rate"
    metric_value: Optional[float] = None  # e.g., 0.25 (25%)
    comparison_baseline: Optional[str] = None  # e.g., "single_image_posts"
    actionable_recommendation: str = ""  # What to do with this insight
    confidence_score: float = 0.5
    evidence_sources: List[str] = field(default_factory=list)  # Which deliverables support this
    extraction_method: str = "unknown"
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_learning_format(self) -> str:
        """Convert to human-readable learning format"""
        if self.metric_value and self.metric_name and self.comparison_baseline:
            # Quantitative insight with comparison
            percentage = f"{self.metric_value * 100:.0f}%" if self.metric_value < 1 else f"{self.metric_value:.1f}"
            return f"{self.metric_name.replace('_', ' ').title()} shows {percentage} better performance than {self.comparison_baseline}"
        elif self.actionable_recommendation:
            # Qualitative insight with recommendation
            return self.actionable_recommendation
        else:
            # Fallback to simple format
            return f"{self.insight_type.replace('_', ' ').title()} identified in {self.domain.value}"

class ContentAwareLearningEngine:
    """
    Analyzes deliverable content to extract business-valuable insights.
    Replaces generic statistics with domain-specific, actionable learnings.
    """
    
    def __init__(self):
        self.analysis_window_days = 30  # Look back 30 days for patterns
        self.minimum_deliverables_for_pattern = 2  # Need at least 2 similar deliverables
        self.quality_threshold = 0.7  # Only learn from high-quality content
        
        # Domain-specific extractors
        self.domain_extractors = {
            DomainType.INSTAGRAM_MARKETING: self._extract_instagram_insights,
            DomainType.EMAIL_MARKETING: self._extract_email_insights,
            DomainType.CONTENT_STRATEGY: self._extract_content_strategy_insights,
            DomainType.LEAD_GENERATION: self._extract_lead_gen_insights,
            DomainType.DATA_ANALYSIS: self._extract_data_analysis_insights,
            DomainType.BUSINESS_STRATEGY: self._extract_business_strategy_insights,
        }
        
        # Pattern libraries for each domain
        self.instagram_patterns = {
            'engagement_metrics': [
                r'engagement\s+rate[:\s]+(\d+\.?\d*)%',
                r'(\d+\.?\d*)%\s+engagement',
                r'likes[:\s]+(\d+)',
                r'comments[:\s]+(\d+)',
                r'shares[:\s]+(\d+)',
                r'reach[:\s]+(\d+)',
            ],
            'content_types': [
                r'carousel\s+posts?',
                r'reels?',
                r'stories',
                r'IGTV',
                r'single\s+image',
                r'video\s+content',
            ],
            'posting_patterns': [
                r'post\s+at\s+(\d{1,2}[:\s]?\d{2}\s*[AP]M)',
                r'best\s+time[:\s]+(\d{1,2}[:\s]?\d{2})',
                r'(\d+)\s+times?\s+per\s+week',
                r'daily\s+posting',
                r'weekly\s+schedule',
            ],
            'hashtag_insights': [
                r'(\d+)\s+hashtags?\s+perform',
                r'hashtag\s+reach[:\s]+(\d+)',
                r'trending\s+hashtags?',
                r'niche\s+hashtags?',
            ]
        }
        
        self.email_patterns = {
            'performance_metrics': [
                r'open\s+rate[:\s]+(\d+\.?\d*)%',
                r'click\s+rate[:\s]+(\d+\.?\d*)%',
                r'conversion\s+rate[:\s]+(\d+\.?\d*)%',
                r'bounce\s+rate[:\s]+(\d+\.?\d*)%',
                r'unsubscribe\s+rate[:\s]+(\d+\.?\d*)%',
            ],
            'subject_line_insights': [
                r'subject\s+line\s+length[:\s]+(\d+)',
                r'personalization\s+increases?\s+opens?\s+by\s+(\d+\.?\d*)%',
                r'emoji\s+in\s+subject',
                r'urgency\s+words?',
            ],
            'timing_insights': [
                r'send\s+at\s+(\d{1,2}[:\s]?\d{2}\s*[AP]M)',
                r'best\s+day[:\s]+(\w+day)',
                r'time\s+zone\s+optimization',
            ],
            'sequence_patterns': [
                r'(\d+)\s+email\s+sequence',
                r'follow-up\s+after\s+(\d+)\s+days?',
                r'drip\s+campaign',
                r'nurture\s+sequence',
            ]
        }
    
    async def analyze_workspace_content(self, workspace_id: str) -> Dict[str, Any]:
        """Comprehensive content analysis for business insights extraction"""
        try:
            logger.info(f"🔍 Analyzing workspace {workspace_id} deliverable content for business insights")
            
            # Get deliverables from the workspace
            deliverables = await self._get_quality_deliverables(workspace_id)
            
            if not deliverables or len(deliverables) < self.minimum_deliverables_for_pattern:
                logger.info("Not enough quality deliverables for meaningful content analysis")
                return {"status": "insufficient_data", "insights_generated": 0}
            
            # Detect domain and group deliverables
            domain_groups = await self._group_deliverables_by_domain(deliverables)
            
            # Extract insights for each domain
            all_insights = []
            for domain, domain_deliverables in domain_groups.items():
                if len(domain_deliverables) >= self.minimum_deliverables_for_pattern:
                    domain_insights = await self._extract_domain_insights(domain, domain_deliverables)
                    all_insights.extend(domain_insights)
            
            # Store valuable insights
            insights_stored = await self._store_business_insights(workspace_id, all_insights)
            
            # Generate comparative insights across domains
            comparative_insights = await self._generate_comparative_insights(all_insights)
            for insight in comparative_insights:
                await self._store_insight(workspace_id, insight)
                insights_stored += 1
            
            logger.info(f"✅ Generated {insights_stored} business-valuable insights from content analysis")
            return {
                "status": "completed",
                "insights_generated": insights_stored,
                "domains_analyzed": list(domain_groups.keys()),
                "deliverables_analyzed": len(deliverables),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing workspace content: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _get_quality_deliverables(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Get deliverables that meet quality threshold"""
        try:
            supabase = get_supabase_client()
            
            # Get deliverables with quality scores
            cutoff_date = datetime.now() - timedelta(days=self.analysis_window_days)
            
            response = supabase.table('deliverables')\
                .select('*')\
                .eq('workspace_id', workspace_id)\
                .gte('created_at', cutoff_date.isoformat())\
                .execute()
            
            if not response.data:
                return []
            
            # Filter by quality (using various quality indicators)
            quality_deliverables = []
            for deliverable in response.data:
                quality_score = self._calculate_deliverable_quality(deliverable)
                if quality_score >= self.quality_threshold:
                    quality_deliverables.append(deliverable)
            
            return quality_deliverables
            
        except Exception as e:
            logger.error(f"Error fetching quality deliverables: {e}")
            return []
    
    def _calculate_deliverable_quality(self, deliverable: Dict[str, Any]) -> float:
        """Calculate overall quality score for a deliverable"""
        scores = []
        
        # Check various quality indicators
        if deliverable.get('content_quality_score'):
            scores.append(deliverable['content_quality_score'])
        if deliverable.get('business_specificity_score'):
            scores.append(deliverable['business_specificity_score'])
        if deliverable.get('tool_usage_score'):
            scores.append(deliverable['tool_usage_score'])
        if deliverable.get('creation_confidence'):
            scores.append(deliverable['creation_confidence'])
        
        # If no quality scores, check content presence
        if not scores:
            content = deliverable.get('content')
            if content:
                # Basic quality: has substantial content
                if isinstance(content, str) and len(content) > 500:
                    scores.append(0.7)
                elif isinstance(content, dict) and len(json.dumps(content)) > 200:
                    scores.append(0.7)
                else:
                    scores.append(0.3)
            else:
                return 0.0
        
        return sum(scores) / len(scores) if scores else 0.0
    
    async def _group_deliverables_by_domain(self, deliverables: List[Dict[str, Any]]) -> Dict[DomainType, List[Dict[str, Any]]]:
        """Group deliverables by their business domain using AI classification"""
        try:
            domain_groups = defaultdict(list)
            
            for deliverable in deliverables:
                domain = await self._detect_deliverable_domain(deliverable)
                domain_groups[domain].append(deliverable)
            
            return dict(domain_groups)
            
        except Exception as e:
            logger.error(f"Error grouping deliverables by domain: {e}")
            return {DomainType.GENERAL: deliverables}
    
    async def _detect_deliverable_domain(self, deliverable: Dict[str, Any]) -> DomainType:
        """Detect the business domain of a deliverable"""
        try:
            # Combine title, description, and content for analysis
            analysis_text = f"{deliverable.get('title', '')} {deliverable.get('description', '')}"
            
            content = deliverable.get('content', '')
            if isinstance(content, str):
                analysis_text += f" {content[:1000]}"  # First 1000 chars
            elif isinstance(content, dict):
                analysis_text += f" {json.dumps(content)[:1000]}"
            
            analysis_text = analysis_text.lower()
            
            # Domain detection patterns
            domain_patterns = {
                DomainType.INSTAGRAM_MARKETING: ['instagram', 'ig', 'stories', 'reels', 'hashtag', 'followers', 'engagement rate'],
                DomainType.EMAIL_MARKETING: ['email', 'campaign', 'subject line', 'open rate', 'click rate', 'newsletter', 'drip'],
                DomainType.CONTENT_STRATEGY: ['content calendar', 'editorial', 'blog', 'social media', 'content plan'],
                DomainType.LEAD_GENERATION: ['leads', 'contacts', 'prospects', 'icp', 'qualified', 'cmo', 'cto', 'outreach'],
                DomainType.DATA_ANALYSIS: ['analysis', 'metrics', 'kpi', 'dashboard', 'report', 'analytics', 'data'],
                DomainType.BUSINESS_STRATEGY: ['strategy', 'business plan', 'market', 'competitive', 'swot', 'roadmap'],
            }
            
            # Score each domain
            domain_scores = {}
            for domain, keywords in domain_patterns.items():
                score = sum(1 for keyword in keywords if keyword in analysis_text)
                if score > 0:
                    domain_scores[domain] = score
            
            # Return domain with highest score, or GENERAL if no matches
            if domain_scores:
                return max(domain_scores, key=domain_scores.get)
            else:
                return DomainType.GENERAL
                
        except Exception as e:
            logger.error(f"Error detecting deliverable domain: {e}")
            return DomainType.GENERAL
    
    async def _extract_domain_insights(self, domain: DomainType, deliverables: List[Dict[str, Any]]) -> List[BusinessInsight]:
        """Extract domain-specific insights from deliverables"""
        try:
            # Use domain-specific extractor if available
            if domain in self.domain_extractors:
                return await self.domain_extractors[domain](deliverables)
            else:
                return await self._extract_general_insights(deliverables)
                
        except Exception as e:
            logger.error(f"Error extracting domain insights for {domain}: {e}")
            return []
    
    async def _extract_instagram_insights(self, deliverables: List[Dict[str, Any]]) -> List[BusinessInsight]:
        """Extract Instagram marketing specific insights"""
        insights = []
        
        try:
            # Aggregate content from all deliverables
            combined_content = self._combine_deliverable_content(deliverables)
            
            # Extract engagement patterns
            engagement_insights = self._extract_pattern_insights(
                combined_content,
                self.instagram_patterns['engagement_metrics'],
                'engagement_pattern',
                DomainType.INSTAGRAM_MARKETING
            )
            
            # Analyze content type performance
            if 'carousel' in combined_content.lower() and 'single' in combined_content.lower():
                # Look for comparative data
                carousel_match = re.search(r'carousel.*?(\d+\.?\d*)%\s*engagement', combined_content.lower())
                single_match = re.search(r'single\s+image.*?(\d+\.?\d*)%\s*engagement', combined_content.lower())
                
                if carousel_match and single_match:
                    carousel_rate = float(carousel_match.group(1))
                    single_rate = float(single_match.group(1))
                    
                    if carousel_rate > single_rate:
                        improvement = ((carousel_rate - single_rate) / single_rate) * 100
                        insights.append(BusinessInsight(
                            insight_type="content_type_performance",
                            domain=DomainType.INSTAGRAM_MARKETING,
                            metric_name="carousel_engagement_improvement",
                            metric_value=improvement / 100,  # Store as decimal
                            comparison_baseline="single_image_posts",
                            actionable_recommendation=f"Prioritize carousel posts which show {improvement:.0f}% higher engagement than single images",
                            confidence_score=0.85,
                            evidence_sources=[d['id'] for d in deliverables[:3]],
                            extraction_method="pattern_analysis"
                        ))
            
            # Extract posting time insights
            time_matches = re.findall(r'post\s+at\s+(\d{1,2}[:\s]?\d{2}\s*[AP]M)', combined_content, re.IGNORECASE)
            if time_matches:
                most_common_time = Counter(time_matches).most_common(1)[0][0]
                insights.append(BusinessInsight(
                    insight_type="optimal_posting_time",
                    domain=DomainType.INSTAGRAM_MARKETING,
                    actionable_recommendation=f"Optimal posting time identified: {most_common_time} based on engagement data",
                    confidence_score=0.75,
                    evidence_sources=[d['id'] for d in deliverables[:2]],
                    extraction_method="pattern_frequency"
                ))
            
            # Extract hashtag insights
            hashtag_numbers = re.findall(r'(\d+)\s+hashtags?\s+perform', combined_content.lower())
            if hashtag_numbers:
                optimal_count = int(sum(int(n) for n in hashtag_numbers) / len(hashtag_numbers))
                insights.append(BusinessInsight(
                    insight_type="hashtag_optimization",
                    domain=DomainType.INSTAGRAM_MARKETING,
                    metric_name="optimal_hashtag_count",
                    metric_value=float(optimal_count),
                    actionable_recommendation=f"Use {optimal_count} hashtags per post for optimal reach",
                    confidence_score=0.7,
                    evidence_sources=[d['id'] for d in deliverables[:2]],
                    extraction_method="statistical_average"
                ))
            
            return insights
            
        except Exception as e:
            logger.error(f"Error extracting Instagram insights: {e}")
            return insights
    
    async def _extract_email_insights(self, deliverables: List[Dict[str, Any]]) -> List[BusinessInsight]:
        """Extract email marketing specific insights"""
        insights = []
        
        try:
            combined_content = self._combine_deliverable_content(deliverables)
            
            # Extract performance metrics
            open_rates = re.findall(r'open\s+rate[:\s]+(\d+\.?\d*)%', combined_content.lower())
            if open_rates:
                avg_open_rate = sum(float(r) for r in open_rates) / len(open_rates)
                
                # Industry benchmark comparison (example: 21.33% average)
                industry_avg = 21.33
                if avg_open_rate > industry_avg:
                    improvement = ((avg_open_rate - industry_avg) / industry_avg) * 100
                    insights.append(BusinessInsight(
                        insight_type="email_performance",
                        domain=DomainType.EMAIL_MARKETING,
                        metric_name="open_rate_performance",
                        metric_value=avg_open_rate / 100,
                        comparison_baseline="industry_average",
                        actionable_recommendation=f"Email campaigns achieving {avg_open_rate:.1f}% open rate, {improvement:.0f}% above industry average",
                        confidence_score=0.8,
                        evidence_sources=[d['id'] for d in deliverables[:3]],
                        extraction_method="metric_aggregation"
                    ))
            
            # Subject line insights
            personalization_impact = re.search(r'personalization\s+increases?\s+opens?\s+by\s+(\d+\.?\d*)%', combined_content.lower())
            if personalization_impact:
                impact_value = float(personalization_impact.group(1))
                insights.append(BusinessInsight(
                    insight_type="subject_line_optimization",
                    domain=DomainType.EMAIL_MARKETING,
                    metric_name="personalization_impact",
                    metric_value=impact_value / 100,
                    actionable_recommendation=f"Add personalization to subject lines for {impact_value:.0f}% increase in open rates",
                    confidence_score=0.85,
                    evidence_sources=[d['id'] for d in deliverables[:2]],
                    extraction_method="impact_analysis"
                ))
            
            # Timing insights
            best_days = re.findall(r'best\s+day[:\s]+(\w+day)', combined_content.lower())
            if best_days:
                most_common_day = Counter(best_days).most_common(1)[0][0]
                insights.append(BusinessInsight(
                    insight_type="send_timing_optimization",
                    domain=DomainType.EMAIL_MARKETING,
                    actionable_recommendation=f"Schedule email sends for {most_common_day.capitalize()} for highest engagement",
                    confidence_score=0.75,
                    evidence_sources=[d['id'] for d in deliverables[:2]],
                    extraction_method="pattern_consensus"
                ))
            
            return insights
            
        except Exception as e:
            logger.error(f"Error extracting email insights: {e}")
            return insights
    
    async def _extract_content_strategy_insights(self, deliverables: List[Dict[str, Any]]) -> List[BusinessInsight]:
        """Extract content strategy insights"""
        insights = []
        
        try:
            combined_content = self._combine_deliverable_content(deliverables)
            
            # Use AI to extract strategic insights
            if combined_content:
                prompt = f"""Analyze this content strategy data and extract specific, quantifiable business insights:

{combined_content[:3000]}

Extract insights about:
1. Content frequency and consistency patterns
2. Content mix recommendations (video vs text vs images)
3. Audience engagement patterns
4. Content performance metrics

Return as JSON with specific metrics where available."""

                agent = {
                    "name": "ContentStrategyAnalyzer",
                    "model": "gpt-4o-mini",
                    "instructions": "You are an expert at analyzing content strategy data and extracting actionable business insights."
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
                    # Convert AI insights to BusinessInsight objects
                    for key, value in response.items():
                        if isinstance(value, dict) and 'recommendation' in value:
                            insights.append(BusinessInsight(
                                insight_type="content_strategy",
                                domain=DomainType.CONTENT_STRATEGY,
                                actionable_recommendation=value['recommendation'],
                                confidence_score=value.get('confidence', 0.7),
                                evidence_sources=[d['id'] for d in deliverables[:2]],
                                extraction_method="ai_analysis"
                            ))
            
            return insights
            
        except Exception as e:
            logger.error(f"Error extracting content strategy insights: {e}")
            return insights
    
    async def _extract_lead_gen_insights(self, deliverables: List[Dict[str, Any]]) -> List[BusinessInsight]:
        """Extract lead generation insights"""
        insights = []
        
        try:
            # Count total leads across deliverables
            total_leads = 0
            lead_sources = defaultdict(int)
            
            for deliverable in deliverables:
                content = deliverable.get('content', '')
                
                # Count email addresses as proxy for leads
                if isinstance(content, str):
                    emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', content)
                    total_leads += len(emails)
                    
                    # Identify lead sources
                    if 'linkedin' in content.lower():
                        lead_sources['LinkedIn'] += len(emails)
                    if 'conference' in content.lower() or 'event' in content.lower():
                        lead_sources['Events'] += len(emails) // 2
                    if 'referral' in content.lower():
                        lead_sources['Referrals'] += len(emails) // 3
            
            if total_leads > 0:
                insights.append(BusinessInsight(
                    insight_type="lead_generation_volume",
                    domain=DomainType.LEAD_GENERATION,
                    metric_name="total_qualified_leads",
                    metric_value=float(total_leads),
                    actionable_recommendation=f"Generated {total_leads} qualified leads across {len(deliverables)} campaigns",
                    confidence_score=0.9,
                    evidence_sources=[d['id'] for d in deliverables],
                    extraction_method="direct_count"
                ))
                
                # Best lead source
                if lead_sources:
                    best_source = max(lead_sources, key=lead_sources.get)
                    source_percentage = (lead_sources[best_source] / total_leads) * 100
                    insights.append(BusinessInsight(
                        insight_type="lead_source_effectiveness",
                        domain=DomainType.LEAD_GENERATION,
                        metric_name="top_lead_source",
                        metric_value=source_percentage / 100,
                        actionable_recommendation=f"{best_source} generates {source_percentage:.0f}% of qualified leads - increase investment",
                        confidence_score=0.75,
                        evidence_sources=[d['id'] for d in deliverables[:3]],
                        extraction_method="source_analysis"
                    ))
            
            return insights
            
        except Exception as e:
            logger.error(f"Error extracting lead generation insights: {e}")
            return insights
    
    async def _extract_data_analysis_insights(self, deliverables: List[Dict[str, Any]]) -> List[BusinessInsight]:
        """Extract data analysis insights"""
        insights = []
        
        try:
            combined_content = self._combine_deliverable_content(deliverables)
            
            # Look for KPI improvements
            kpi_improvements = re.findall(r'(\w+)\s+improved\s+by\s+(\d+\.?\d*)%', combined_content.lower())
            for kpi_name, improvement in kpi_improvements:
                insights.append(BusinessInsight(
                    insight_type="kpi_improvement",
                    domain=DomainType.DATA_ANALYSIS,
                    metric_name=f"{kpi_name}_improvement",
                    metric_value=float(improvement) / 100,
                    actionable_recommendation=f"{kpi_name.capitalize()} improved by {improvement}% - continue current strategy",
                    confidence_score=0.8,
                    evidence_sources=[d['id'] for d in deliverables[:2]],
                    extraction_method="metric_extraction"
                ))
            
            return insights
            
        except Exception as e:
            logger.error(f"Error extracting data analysis insights: {e}")
            return insights
    
    async def _extract_business_strategy_insights(self, deliverables: List[Dict[str, Any]]) -> List[BusinessInsight]:
        """Extract business strategy insights"""
        insights = []
        
        try:
            # Use AI for strategic insight extraction
            combined_content = self._combine_deliverable_content(deliverables)
            
            if combined_content:
                prompt = f"""Analyze this business strategy content and extract specific, actionable insights:

{combined_content[:3000]}

Focus on:
1. Market opportunities with potential value
2. Competitive advantages identified
3. Risk mitigation strategies
4. Growth projections and targets

Return specific, quantified insights where possible."""

                agent = {
                    "name": "BusinessStrategyAnalyzer",
                    "model": "gpt-4o-mini",
                    "instructions": "You are an expert at analyzing business strategy and extracting actionable insights."
                }
                
                response = await ai_provider_manager.call_ai(
                    provider_type='openai_sdk',
                    agent=agent,
                    prompt=prompt,
                    max_tokens=1000,
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                
                if response and isinstance(response, dict) and 'insights' in response:
                    for insight_data in response['insights']:
                        insights.append(BusinessInsight(
                            insight_type="strategic_insight",
                            domain=DomainType.BUSINESS_STRATEGY,
                            actionable_recommendation=insight_data.get('recommendation', ''),
                            confidence_score=insight_data.get('confidence', 0.7),
                            evidence_sources=[d['id'] for d in deliverables[:2]],
                            extraction_method="ai_strategic_analysis"
                        ))
            
            return insights
            
        except Exception as e:
            logger.error(f"Error extracting business strategy insights: {e}")
            return insights
    
    async def _extract_general_insights(self, deliverables: List[Dict[str, Any]]) -> List[BusinessInsight]:
        """Extract general insights when domain is unknown"""
        insights = []
        
        try:
            # Basic pattern extraction
            combined_content = self._combine_deliverable_content(deliverables)
            
            # Look for any percentage improvements
            improvements = re.findall(r'(\w+)\s+(?:increased?|improved?|grew)\s+by\s+(\d+\.?\d*)%', combined_content.lower())
            for metric, value in improvements[:3]:  # Top 3 improvements
                insights.append(BusinessInsight(
                    insight_type="performance_improvement",
                    domain=DomainType.GENERAL,
                    metric_name=metric,
                    metric_value=float(value) / 100,
                    actionable_recommendation=f"{metric.capitalize()} showed {value}% improvement",
                    confidence_score=0.6,
                    evidence_sources=[d['id'] for d in deliverables[:2]],
                    extraction_method="general_pattern"
                ))
            
            return insights
            
        except Exception as e:
            logger.error(f"Error extracting general insights: {e}")
            return insights
    
    def _combine_deliverable_content(self, deliverables: List[Dict[str, Any]]) -> str:
        """Combine content from multiple deliverables for analysis"""
        combined = []
        
        for deliverable in deliverables:
            # Add title and description
            title = deliverable.get('title', '')
            if title:
                combined.append(str(title))
            
            description = deliverable.get('description', '')
            if description:
                combined.append(str(description))
            
            # Add content
            content = deliverable.get('content', '')
            if isinstance(content, str):
                combined.append(content)
            elif isinstance(content, dict):
                combined.append(json.dumps(content))
            elif isinstance(content, list):
                combined.append(str(content))
        
        # Filter out None values and join
        return ' '.join(str(item) for item in combined if item)
    
    def _extract_pattern_insights(self, content: str, patterns: List[str], insight_type: str, domain: DomainType) -> List[BusinessInsight]:
        """Extract insights using regex patterns"""
        insights = []
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                # Aggregate matches
                if all(m.replace('.', '').isdigit() for m in matches):
                    # Numeric matches - calculate average
                    values = [float(m) for m in matches]
                    avg_value = sum(values) / len(values)
                    
                    insights.append(BusinessInsight(
                        insight_type=insight_type,
                        domain=domain,
                        metric_value=avg_value / 100 if avg_value > 1 else avg_value,
                        confidence_score=0.7,
                        extraction_method="pattern_matching"
                    ))
        
        return insights
    
    async def _generate_comparative_insights(self, all_insights: List[BusinessInsight]) -> List[BusinessInsight]:
        """Generate insights by comparing across domains"""
        comparative_insights = []
        
        try:
            # Group insights by type
            type_groups = defaultdict(list)
            for insight in all_insights:
                type_groups[insight.insight_type].append(insight)
            
            # Find cross-domain patterns
            for insight_type, insights in type_groups.items():
                if len(insights) > 1:
                    # Compare performance across domains
                    domains = [i.domain for i in insights]
                    if len(set(domains)) > 1:
                        # Multiple domains have similar insights
                        avg_confidence = sum(i.confidence_score for i in insights) / len(insights)
                        comparative_insights.append(BusinessInsight(
                            insight_type="cross_domain_pattern",
                            domain=DomainType.GENERAL,
                            actionable_recommendation=f"{insight_type.replace('_', ' ').title()} pattern observed across {len(set(domains))} business areas",
                            confidence_score=avg_confidence,
                            evidence_sources=[i.evidence_sources[0] for i in insights[:3] if i.evidence_sources],
                            extraction_method="comparative_analysis"
                        ))
            
            return comparative_insights
            
        except Exception as e:
            logger.error(f"Error generating comparative insights: {e}")
            return comparative_insights
    
    async def _store_business_insights(self, workspace_id: str, insights: List[BusinessInsight]) -> int:
        """Store business insights in the database"""
        stored_count = 0
        
        for insight in insights:
            success = await self._store_insight(workspace_id, insight)
            if success:
                stored_count += 1
        
        return stored_count
    
    async def _store_insight(self, workspace_id: str, insight: BusinessInsight) -> bool:
        """Store a single insight in the database"""
        try:
            # Convert to learning format
            learning_text = insight.to_learning_format()
            
            # Create structured content for storage
            insight_content = {
                "learning": learning_text,
                "insight_type": insight.insight_type,
                "domain": insight.domain.value,
                "confidence_score": insight.confidence_score,
                "extraction_method": insight.extraction_method,
                "evidence_sources": insight.evidence_sources,
                "created_at": insight.created_at.isoformat()
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
            
            # Store in workspace_insights
            await add_memory_insight(
                workspace_id=workspace_id,
                insight_type="business_learning",
                content=json.dumps(insight_content, indent=2),
                agent_role="content_learning_engine",
                confidence_score=insight.confidence_score,
                relevance_tags=[insight.domain.value, insight.insight_type]
            )
            
            logger.info(f"✅ Stored business insight: {learning_text}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing business insight: {e}")
            return False
    
    async def get_actionable_learnings(self, workspace_id: str, domain: Optional[DomainType] = None) -> List[str]:
        """Get actionable learnings for a workspace, optionally filtered by domain"""
        try:
            # Get recent insights
            insights = await get_memory_insights(workspace_id, limit=20)
            
            actionable_learnings = []
            for insight in insights:
                if insight.get('insight_type') == 'business_learning':
                    try:
                        content = json.loads(insight.get('content', '{}'))
                        
                        # Filter by domain if specified
                        if domain and content.get('domain') != domain.value:
                            continue
                        
                        learning = content.get('learning')
                        if learning:
                            # Format with confidence indicator
                            confidence = content.get('confidence_score', 0.5)
                            if confidence >= 0.8:
                                prefix = "✅ HIGH CONFIDENCE: "
                            elif confidence >= 0.6:
                                prefix = "📊 MODERATE CONFIDENCE: "
                            else:
                                prefix = "🔍 EXPLORATORY: "
                            
                            actionable_learnings.append(f"{prefix}{learning}")
                    except:
                        continue
            
            return actionable_learnings
            
        except Exception as e:
            logger.error(f"Error getting actionable learnings: {e}")
            return []
    
    async def integrate_with_quality_validation(self, workspace_id: str, deliverable_id: str) -> Dict[str, Any]:
        """Integration point with quality validation engine"""
        try:
            # Get deliverable
            supabase = get_supabase_client()
            response = supabase.table('deliverables').select('*').eq('id', deliverable_id).single().execute()
            
            if not response.data:
                return {"status": "not_found"}
            
            deliverable = response.data
            
            # Check quality with QualitySystemConfig
            quality_score = self._calculate_deliverable_quality(deliverable)
            
            if QualitySystemConfig.is_quality_system_enabled() and quality_score < QualitySystemConfig.QUALITY_SCORE_THRESHOLD:
                logger.warning(f"Deliverable {deliverable_id} below quality threshold for learning extraction")
                return {"status": "below_quality_threshold", "quality_score": quality_score}
            
            # Extract domain-specific insights from this deliverable
            domain = await self._detect_deliverable_domain(deliverable)
            insights = await self._extract_domain_insights(domain, [deliverable])
            
            # Store insights
            stored_count = await self._store_business_insights(workspace_id, insights)
            
            return {
                "status": "completed",
                "domain": domain.value,
                "insights_extracted": len(insights),
                "insights_stored": stored_count,
                "quality_score": quality_score
            }
            
        except Exception as e:
            logger.error(f"Error integrating with quality validation: {e}")
            return {"status": "error", "error": str(e)}

# Create singleton instance
content_aware_learning_engine = ContentAwareLearningEngine()

# Export for easy import
__all__ = ["ContentAwareLearningEngine", "content_aware_learning_engine", "BusinessInsight", "DomainType"]