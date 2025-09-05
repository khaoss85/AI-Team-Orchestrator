"""
AI Insight Classifier Service
Intelligent content-based classification for insights compliant with 15 Pillars
Uses semantic analysis to categorize insights into appropriate types
"""

import logging
import re
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

from unified_insight import InsightCategory

logger = logging.getLogger(__name__)


class InsightClassifier:
    """
    AI-driven insight classification using content analysis.
    
    Replaces hardcoded 'discovery' with intelligent categorization based on:
    - Semantic analysis of content
    - Pattern matching for specific insight types
    - Metric detection for performance insights
    - Action verb detection for recommendations
    """
    
    def __init__(self):
        # Pattern definitions for each category
        self.performance_patterns = [
            r'\d+(?:\.\d+)?%?\s*(?:better|worse|improvement|increase|decrease|growth)',
            r'performance\s+(?:than|vs|versus|compared)',
            r'shows?\s+\d+(?:\.\d+)?',
            r'(?:increased?|decreased?|improved?|grew)\s+by\s+\d+',
            r'(?:efficiency|speed|throughput|latency)\s+(?:gain|improvement)',
            r'recovery_success_rate',
            r'Annual Recurring Revenue',
            r'Revenue Multiple',
            r'EBITDA'
        ]
        
        self.strategy_patterns = [
            r'(?:develop|create|build|establish|implement)\s+(?:vertical|horizontal|specialized)',
            r'(?:develop|create|build)\s+.*\s+(?:applications?|solutions?|platforms?)',
            r'(?:strategy|strategic|approach|plan)\s+(?:for|to|towards)',
            r'(?:focus on|concentrate on|prioritize|target)',
            r'cater\s+to\s+(?:specific|particular|certain)',
            r'targeting\s+specific',
            r'market\s+(?:positioning|strategy|approach)',
            r'competitive\s+advantage',
            r'go-to-market',
            r'expansion\s+(?:strategy|plan)'
        ]
        
        self.operational_patterns = [
            r'(?:process|workflow|operation|procedure)\s+(?:improvement|optimization)',
            r'(?:automate|streamline|optimize)\s+(?:process|workflow)',
            r'operational\s+(?:efficiency|excellence)',
            r'(?:reduce|minimize|eliminate)\s+(?:manual|overhead|redundancy)',
            r'standard operating procedure',
            r'day-to-day\s+(?:operations|activities)'
        ]
        
        self.discovery_patterns = [
            r'(?:found|discovered|identified|detected|uncovered)',
            r'new\s+(?:pattern|trend|insight|finding)',
            r'(?:reveals?|shows?)\s+(?:that|how)',
            r'(?:analysis|research)\s+(?:indicates|suggests|reveals)',
            r'(?:interesting|notable|significant)\s+(?:finding|discovery)',
            r'GenAI Native (?:Unicorns|Startups)',
            r'market\s+(?:trend|shift|movement)'
        ]
        
        self.constraint_patterns = [
            r'(?:limitation|constraint|restriction|bottleneck)',
            r'bottleneck\s+(?:identified|detected|found|discovered)',
            r'(?:cannot|unable|impossible|prevented)',
            r'(?:blocked|blocking|blocker)',
            r'(?:issue|problem|challenge)\s+(?:with|in|preventing)',
            r'(?:lack of|missing|absent|unavailable)',
            r'insufficient\s+(?:resources|capacity|bandwidth)',
            r'causing\s+(?:delays|issues|problems)'
        ]
        
        self.optimization_patterns = [
            r'(?:optimize|optimization|optimizing)\s+',
            r'(?:improve|improvement|improving)\s+(?:efficiency|performance)',
            r'(?:reduce|reduction|reducing)\s+(?:cost|time|effort)',
            r'(?:maximize|maximizing|minimization|minimizing)',
            r'enhance\s+.*\s+(?:applications?|solutions?)',
            r'(?:enhance|enhancement|enhancing)',
            r'best\s+practice'
        ]
        
        self.risk_patterns = [
            r'(?:risk|threat|vulnerability|exposure)',
            r'(?:potential|possible)\s+(?:issue|problem|failure)',
            r'(?:warning|caution|alert|concern)',
            r'(?:mitigation|prevention|protection)',
            r'(?:security|compliance|regulatory)\s+(?:risk|concern)',
            r'failure\s+(?:rate|risk|probability)'
        ]
        
        self.opportunity_patterns = [
            r'(?:opportunity|potential|possibility)',
            r'(?:could|should|would)\s+(?:benefit|improve|enhance)',
            r'(?:untapped|unexplored|new)\s+(?:market|segment|area)',
            r'growth\s+(?:opportunity|potential|area)',
            r'(?:leverage|utilize|exploit|capitalize)',
            r'competitive\s+(?:edge|advantage|differentiation)'
        ]
        
        # Action keywords for distinguishing recommendations
        self.action_keywords = [
            'develop', 'implement', 'create', 'build', 'establish',
            'improve', 'enhance', 'optimize', 'streamline', 'automate',
            'focus', 'prioritize', 'concentrate', 'target', 'pursue',
            'leverage', 'utilize', 'adopt', 'integrate', 'deploy'
        ]
        
        # Metric keywords for performance insights
        self.metric_keywords = [
            'rate', 'percentage', 'ratio', 'score', 'metric',
            'kpi', 'measure', 'index', 'coefficient', 'factor',
            'revenue', 'cost', 'profit', 'margin', 'roi',
            'efficiency', 'productivity', 'throughput', 'latency'
        ]
    
    def classify_insight(self, content: str, title: Optional[str] = None) -> InsightCategory:
        """
        Classify an insight based on its content using pattern matching and semantic analysis.
        
        Args:
            content: The insight content to analyze
            title: Optional title for additional context
            
        Returns:
            InsightCategory enum value
        """
        try:
            # Combine title and content for analysis
            text_to_analyze = f"{title or ''} {content}".lower()
            
            # Calculate match scores for each category
            scores = self._calculate_category_scores(text_to_analyze)
            
            # Special handling for actionable recommendations
            if self._is_actionable_recommendation(text_to_analyze):
                # If it's a strategic recommendation
                if scores.get(InsightCategory.STRATEGY, 0) > 0:
                    return InsightCategory.STRATEGY
                # If it's about optimization
                elif scores.get(InsightCategory.OPTIMIZATION, 0) > 0:
                    return InsightCategory.OPTIMIZATION
                # Default actionable to strategy
                else:
                    return InsightCategory.STRATEGY
            
            # Special handling for performance metrics
            if self._contains_performance_metric(text_to_analyze):
                return InsightCategory.PERFORMANCE
            
            # Return category with highest score
            if scores:
                best_category = max(scores, key=scores.get)
                if scores[best_category] > 0:
                    return best_category
            
            # Default to discovery for new findings
            if self._is_new_finding(text_to_analyze):
                return InsightCategory.DISCOVERY
            
            # Final fallback to general
            return InsightCategory.GENERAL
            
        except Exception as e:
            logger.error(f"Error classifying insight: {e}")
            return InsightCategory.GENERAL
    
    def _calculate_category_scores(self, text: str) -> Dict[InsightCategory, int]:
        """Calculate pattern match scores for each category"""
        scores = {}
        
        # Check each category's patterns
        category_patterns = {
            InsightCategory.PERFORMANCE: self.performance_patterns,
            InsightCategory.STRATEGY: self.strategy_patterns,
            InsightCategory.OPERATIONAL: self.operational_patterns,
            InsightCategory.DISCOVERY: self.discovery_patterns,
            InsightCategory.CONSTRAINT: self.constraint_patterns,
            InsightCategory.OPTIMIZATION: self.optimization_patterns,
            InsightCategory.RISK: self.risk_patterns,
            InsightCategory.OPPORTUNITY: self.opportunity_patterns
        }
        
        for category, patterns in category_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    score += 1
            if score > 0:
                scores[category] = score
        
        return scores
    
    def _is_actionable_recommendation(self, text: str) -> bool:
        """Check if the insight is an actionable recommendation"""
        # Check for action verbs at the beginning or after common starters
        for keyword in self.action_keywords:
            if re.search(rf'\b{keyword}\b', text[:100], re.IGNORECASE):
                return True
        return False
    
    def _contains_performance_metric(self, text: str) -> bool:
        """Check if the insight contains performance metrics"""
        # Check for percentage improvements
        if re.search(r'\d+(?:\.\d+)?%?\s*better\s+performance', text):
            return True
        
        # Check for metric keywords with values
        for keyword in self.metric_keywords:
            if re.search(rf'{keyword}\s+shows?\s+\d+', text, re.IGNORECASE):
                return True
        
        # Check for comparison patterns
        if re.search(r'shows?\s+\d+(?:\.\d+)?.*(?:than|vs|versus)', text):
            return True
        
        return False
    
    def _is_new_finding(self, text: str) -> bool:
        """Check if the insight represents a new finding or discovery"""
        discovery_indicators = [
            'new', 'novel', 'emerging', 'trend', 'pattern',
            'finding', 'discovery', 'insight', 'observation'
        ]
        
        for indicator in discovery_indicators:
            if indicator in text:
                return True
        
        return False
    
    def classify_batch(self, insights: List[Dict[str, Any]]) -> List[InsightCategory]:
        """
        Classify multiple insights in batch.
        
        Args:
            insights: List of insight dictionaries with 'content' and optional 'title'
            
        Returns:
            List of InsightCategory values
        """
        classifications = []
        
        for insight in insights:
            content = insight.get('content', '')
            title = insight.get('title', '')
            category = self.classify_insight(content, title)
            classifications.append(category)
            
            logger.debug(f"Classified '{title[:50]}...' as {category.value}")
        
        return classifications
    
    def get_insight_type_from_category(self, category: InsightCategory) -> str:
        """
        Map category to insight_type for database compatibility.
        
        The database uses InsightType enum from models.py with values:
        SUCCESS_PATTERN, FAILURE_LESSON, CONSTRAINT, DISCOVERY, OPTIMIZATION,
        PROGRESS, RISK, OPPORTUNITY, RESOURCE
        """
        # Map categories to database insight_type enum values
        type_mapping = {
            InsightCategory.PERFORMANCE: 'success_pattern',  # Performance metrics are success patterns
            InsightCategory.STRATEGY: 'optimization',  # Strategic recommendations are optimizations
            InsightCategory.OPERATIONAL: 'optimization',  # Operational improvements are optimizations
            InsightCategory.DISCOVERY: 'discovery',  # Direct mapping
            InsightCategory.CONSTRAINT: 'constraint',  # Direct mapping
            InsightCategory.OPTIMIZATION: 'optimization',  # Direct mapping
            InsightCategory.RISK: 'risk',  # Direct mapping
            InsightCategory.OPPORTUNITY: 'opportunity',  # Direct mapping
            InsightCategory.GENERAL: 'discovery'  # Default to discovery
        }
        
        return type_mapping.get(category, 'discovery')


# Singleton instance
insight_classifier = InsightClassifier()