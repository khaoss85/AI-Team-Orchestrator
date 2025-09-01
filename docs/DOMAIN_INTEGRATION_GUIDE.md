# Domain Integration Guide: Adding New Business Domains

## Overview

This guide provides comprehensive instructions for integrating new business domains into the Content-Aware Learning System. The system currently supports 8 specialized domains and is designed to easily accommodate new business areas with minimal code changes.

## Current Supported Domains

```python
class DomainType(str, Enum):
    INSTAGRAM_MARKETING = "instagram_marketing"
    EMAIL_MARKETING = "email_marketing"
    CONTENT_STRATEGY = "content_strategy"
    LEAD_GENERATION = "lead_generation"
    DATA_ANALYSIS = "data_analysis"
    BUSINESS_STRATEGY = "business_strategy"
    TECHNICAL_DOCUMENTATION = "technical_documentation"
    PRODUCT_DEVELOPMENT = "product_development"
    GENERAL = "general"
```

## Integration Steps Overview

1. **Define Domain Enum**: Add new domain to `DomainType`
2. **Create Pattern Library**: Define domain-specific regex patterns
3. **Implement Extractor**: Create domain-specific insight extraction logic
4. **Add Detection Patterns**: Enable automatic domain classification
5. **Configure Quality Criteria**: Set domain-specific quality thresholds
6. **Create API Documentation**: Document new domain capabilities
7. **Add Tests**: Ensure comprehensive testing coverage

## Step-by-Step Integration

### Step 1: Define New Domain

**File**: `backend/services/content_aware_learning_engine.py`

```python
class DomainType(str, Enum):
    # ... existing domains
    AFFILIATE_MARKETING = "affiliate_marketing"  # New domain
    ECOMMERCE_ANALYTICS = "ecommerce_analytics"  # New domain
    PODCAST_MARKETING = "podcast_marketing"      # New domain
```

### Step 2: Create Pattern Library

Add domain-specific patterns for content analysis:

```python
# In ContentAwareLearningEngine.__init__()
self.affiliate_patterns = {
    'conversion_metrics': [
        r'conversion\s+rate[:\s]+(\d+\.?\d*)%',
        r'ctr[:\s]+(\d+\.?\d*)%',
        r'epc[:\s]+\$?(\d+\.?\d*)',  # earnings per click
        r'commission[:\s]+(\d+\.?\d*)%'
    ],
    'traffic_sources': [
        r'organic\s+traffic',
        r'paid\s+traffic', 
        r'social\s+media\s+referral',
        r'email\s+referral',
        r'direct\s+traffic'
    ],
    'performance_indicators': [
        r'revenue[:\s]+\$(\d+\.?\d*)',
        r'roi[:\s]+(\d+\.?\d*)%',
        r'lifetime\s+value[:\s]+\$(\d+\.?\d*)',
        r'churn\s+rate[:\s]+(\d+\.?\d*)%'
    ]
}

self.ecommerce_patterns = {
    'sales_metrics': [
        r'cart\s+abandonment[:\s]+(\d+\.?\d*)%',
        r'average\s+order\s+value[:\s]+\$(\d+\.?\d*)',
        r'repeat\s+purchase\s+rate[:\s]+(\d+\.?\d*)%',
        r'inventory\s+turnover[:\s]+(\d+\.?\d*)'
    ],
    'customer_behavior': [
        r'time\s+on\s+site[:\s]+(\d+)\s*(?:min|minutes)',
        r'bounce\s+rate[:\s]+(\d+\.?\d*)%',
        r'pages\s+per\s+session[:\s]+(\d+\.?\d*)',
        r'session\s+duration[:\s]+(\d+)\s*(?:min|minutes)'
    ]
}
```

### Step 3: Implement Domain Extractor

Create specialized extraction logic for your domain:

```python
async def _extract_affiliate_insights(self, deliverables: List[Dict[str, Any]]) -> List[BusinessInsight]:
    """Extract affiliate marketing specific insights"""
    insights = []
    
    try:
        combined_content = self._combine_deliverable_content(deliverables)
        
        # Extract conversion rate insights
        conversion_rates = re.findall(r'conversion\s+rate[:\s]+(\d+\.?\d*)%', combined_content.lower())
        if conversion_rates:
            avg_conversion = sum(float(r) for r in conversion_rates) / len(conversion_rates)
            
            # Industry benchmark comparison (example: 2.35% average for affiliates)
            industry_avg = 2.35
            if avg_conversion > industry_avg:
                improvement = ((avg_conversion - industry_avg) / industry_avg) * 100
                insights.append(BusinessInsight(
                    insight_type="conversion_performance",
                    domain=DomainType.AFFILIATE_MARKETING,
                    metric_name="conversion_rate_performance", 
                    metric_value=avg_conversion / 100,
                    comparison_baseline="industry_average",
                    actionable_recommendation=f"Affiliate campaigns achieving {avg_conversion:.2f}% conversion rate, {improvement:.0f}% above industry average",
                    confidence_score=0.85,
                    evidence_sources=[d['id'] for d in deliverables[:3]],
                    extraction_method="metric_aggregation"
                ))
        
        # Extract top performing traffic sources
        traffic_sources = {}
        for pattern in self.affiliate_patterns['traffic_sources']:
            matches = re.findall(pattern, combined_content.lower())
            for match in matches:
                traffic_sources[match] = traffic_sources.get(match, 0) + 1
        
        if traffic_sources:
            best_source = max(traffic_sources, key=traffic_sources.get)
            insights.append(BusinessInsight(
                insight_type="traffic_source_effectiveness",
                domain=DomainType.AFFILIATE_MARKETING,
                actionable_recommendation=f"{best_source.title()} identified as most effective traffic source for affiliate conversions",
                confidence_score=0.8,
                evidence_sources=[d['id'] for d in deliverables[:2]],
                extraction_method="pattern_frequency"
            ))
        
        # Extract ROI insights
        roi_matches = re.findall(r'roi[:\s]+(\d+\.?\d*)%', combined_content.lower())
        if roi_matches:
            avg_roi = sum(float(r) for r in roi_matches) / len(roi_matches)
            if avg_roi > 200:  # 200% ROI threshold for high performance
                insights.append(BusinessInsight(
                    insight_type="roi_performance",
                    domain=DomainType.AFFILIATE_MARKETING,
                    metric_name="average_roi",
                    metric_value=avg_roi / 100,
                    actionable_recommendation=f"High-performing campaigns achieve {avg_roi:.0f}% ROI - replicate successful strategies",
                    confidence_score=0.9,
                    evidence_sources=[d['id'] for d in deliverables[:2]],
                    extraction_method="performance_threshold"
                ))
        
        return insights
        
    except Exception as e:
        logger.error(f"Error extracting affiliate insights: {e}")
        return insights

async def _extract_ecommerce_insights(self, deliverables: List[Dict[str, Any]]) -> List[BusinessInsight]:
    """Extract e-commerce analytics insights"""
    insights = []
    
    try:
        combined_content = self._combine_deliverable_content(deliverables)
        
        # Cart abandonment analysis
        abandonment_rates = re.findall(r'cart\s+abandonment[:\s]+(\d+\.?\d*)%', combined_content.lower())
        if abandonment_rates:
            avg_abandonment = sum(float(r) for r in abandonment_rates) / len(abandonment_rates)
            
            # Industry average is ~70%
            if avg_abandonment < 65:  # Better than average
                improvement = ((70 - avg_abandonment) / 70) * 100
                insights.append(BusinessInsight(
                    insight_type="cart_optimization",
                    domain=DomainType.ECOMMERCE_ANALYTICS,
                    metric_name="cart_abandonment_rate",
                    metric_value=avg_abandonment / 100,
                    comparison_baseline="industry_average_70_percent", 
                    actionable_recommendation=f"Cart abandonment rate of {avg_abandonment:.1f}% is {improvement:.0f}% better than industry average - maintain current checkout optimization",
                    confidence_score=0.85,
                    evidence_sources=[d['id'] for d in deliverables[:2]],
                    extraction_method="benchmark_comparison"
                ))
        
        # Average order value insights
        aov_matches = re.findall(r'average\s+order\s+value[:\s]+\$(\d+\.?\d*)', combined_content.lower())
        if aov_matches:
            avg_aov = sum(float(v) for v in aov_matches) / len(aov_matches)
            insights.append(BusinessInsight(
                insight_type="revenue_optimization",
                domain=DomainType.ECOMMERCE_ANALYTICS,
                metric_name="average_order_value",
                metric_value=avg_aov,
                actionable_recommendation=f"Average order value of ${avg_aov:.2f} - consider upselling strategies to increase",
                confidence_score=0.8,
                evidence_sources=[d['id'] for d in deliverables[:2]],
                extraction_method="value_analysis"
            ))
        
        return insights
        
    except Exception as e:
        logger.error(f"Error extracting e-commerce insights: {e}")
        return insights
```

### Step 4: Register Domain Extractor

Add your extractor to the domain extractors dictionary:

```python
# In ContentAwareLearningEngine.__init__()
self.domain_extractors = {
    # ... existing extractors
    DomainType.AFFILIATE_MARKETING: self._extract_affiliate_insights,
    DomainType.ECOMMERCE_ANALYTICS: self._extract_ecommerce_insights,
}
```

### Step 5: Add Domain Detection Patterns

Enable automatic domain classification:

```python
# In _detect_deliverable_domain method
domain_patterns = {
    # ... existing patterns
    DomainType.AFFILIATE_MARKETING: [
        'affiliate', 'commission', 'referral', 'conversion rate', 'ctr', 'epc',
        'affiliate link', 'partner program', 'revenue share'
    ],
    DomainType.ECOMMERCE_ANALYTICS: [
        'ecommerce', 'cart abandonment', 'checkout', 'order value', 'inventory',
        'product page', 'add to cart', 'purchase funnel', 'shopify', 'woocommerce'
    ],
}
```

### Step 6: Configure Quality Criteria

Set domain-specific quality thresholds and criteria:

```python
# In LearningQualityFeedbackLoop.__init__()
self.domain_quality_criteria = {
    # ... existing criteria
    DomainType.AFFILIATE_MARKETING: {
        "base_threshold": 0.75,  # Higher threshold for financial data
        "learned_criteria": [],
        "performance_multiplier": 1.0
    },
    DomainType.ECOMMERCE_ANALYTICS: {
        "base_threshold": 0.7,
        "learned_criteria": [],
        "performance_multiplier": 1.0
    }
}
```

### Step 7: Add Agent Role Mapping

Enable automatic domain detection from agent roles:

```python
# In _infer_domain_from_agent method
def _infer_domain_from_agent(self, agent_role: str) -> DomainType:
    agent_lower = agent_role.lower()
    
    # ... existing mappings
    if 'affiliate' in agent_lower or 'partner' in agent_lower:
        return DomainType.AFFILIATE_MARKETING
    elif 'ecommerce' in agent_lower or 'shopify' in agent_lower:
        return DomainType.ECOMMERCE_ANALYTICS
    else:
        return DomainType.GENERAL
```

### Step 8: Update API Documentation

Add domain descriptions for API discovery:

```python
# In routes/content_learning.py - get_domain_description function
def get_domain_description(domain: DomainType) -> str:
    descriptions = {
        # ... existing descriptions
        DomainType.AFFILIATE_MARKETING: "Affiliate conversions, commissions, traffic sources, ROI analysis",
        DomainType.ECOMMERCE_ANALYTICS: "Cart abandonment, order value, customer behavior, sales funnels",
    }
    return descriptions.get(domain, "General business domain")
```

## Advanced Integration Features

### Custom AI Analysis Integration

For complex domains requiring AI analysis:

```python
async def _extract_custom_domain_insights(self, deliverables: List[Dict[str, Any]]) -> List[BusinessInsight]:
    """Use AI for complex domain analysis"""
    try:
        combined_content = self._combine_deliverable_content(deliverables)
        
        if combined_content:
            prompt = f"""Analyze this {domain.value} content and extract specific insights:

{combined_content[:3000]}

Extract insights about:
1. Performance metrics and KPIs specific to {domain.value}
2. Best practices and optimization opportunities
3. Competitive advantages or market insights
4. Quantifiable improvements and recommendations

Return as JSON with specific metrics where available."""

            agent = {
                "name": f"{domain.value.replace('_', '').title()}Analyzer",
                "model": "gpt-4o-mini",
                "instructions": f"You are an expert at analyzing {domain.value} data and extracting actionable business insights."
            }
            
            response = await ai_provider_manager.call_ai(
                provider_type='openai_sdk',
                agent=agent,
                prompt=prompt,
                max_tokens=1000,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            # Parse AI response into BusinessInsight objects
            if response and isinstance(response, dict):
                # Implementation specific to your domain
                return parse_ai_insights(response, domain, deliverables)
        
        return []
        
    except Exception as e:
        logger.error(f"Error extracting {domain} insights: {e}")
        return []
```

### Multi-Pattern Analysis

For domains with complex pattern interactions:

```python
def _analyze_cross_pattern_insights(self, content: str, domain: DomainType) -> List[BusinessInsight]:
    """Analyze interactions between different patterns"""
    insights = []
    
    # Example: Affiliate marketing conversion flow analysis
    if domain == DomainType.AFFILIATE_MARKETING:
        # Find traffic source + conversion rate correlations
        traffic_conversions = {}
        
        for source_pattern in self.affiliate_patterns['traffic_sources']:
            source_matches = re.finditer(source_pattern, content.lower())
            for match in source_matches:
                # Look for nearby conversion metrics
                context = content[max(0, match.start()-200):match.end()+200]
                conv_match = re.search(r'conversion\s+rate[:\s]+(\d+\.?\d*)%', context.lower())
                if conv_match:
                    source = match.group(0)
                    conversion = float(conv_match.group(1))
                    traffic_conversions[source] = traffic_conversions.get(source, []) + [conversion]
        
        # Generate insights from correlations
        for source, conversions in traffic_conversions.items():
            if len(conversions) >= 2:
                avg_conversion = sum(conversions) / len(conversions)
                insights.append(BusinessInsight(
                    insight_type="traffic_conversion_correlation",
                    domain=domain,
                    metric_name=f"{source}_conversion_rate",
                    metric_value=avg_conversion / 100,
                    actionable_recommendation=f"{source.title()} traffic converts at {avg_conversion:.1f}% average rate",
                    confidence_score=0.8,
                    extraction_method="cross_pattern_analysis"
                ))
    
    return insights
```

## Testing Your Domain Integration

### Unit Tests

Create comprehensive tests for your domain:

```python
# tests/test_domain_integration.py
import pytest
from services.content_aware_learning_engine import content_aware_learning_engine, DomainType

class TestAffiliateMarketingDomain:
    
    @pytest.fixture
    def affiliate_deliverable(self):
        return {
            'id': 'test-id',
            'title': 'Affiliate Campaign Results',
            'description': 'Q3 affiliate marketing performance analysis',
            'content': '''
            Our affiliate campaign achieved remarkable results this quarter:
            - Conversion rate: 3.2% (industry average: 2.35%)
            - Organic traffic generated 45% of conversions
            - ROI: 285% on total campaign spend
            - Average commission: 15% per sale
            - EPC: $2.40 across all partners
            '''
        }
    
    async def test_domain_detection(self, affiliate_deliverable):
        domain = await content_aware_learning_engine._detect_deliverable_domain(affiliate_deliverable)
        assert domain == DomainType.AFFILIATE_MARKETING
    
    async def test_insight_extraction(self, affiliate_deliverable):
        insights = await content_aware_learning_engine._extract_affiliate_insights([affiliate_deliverable])
        
        assert len(insights) > 0
        
        # Test conversion rate insight
        conversion_insight = next((i for i in insights if i.insight_type == "conversion_performance"), None)
        assert conversion_insight is not None
        assert conversion_insight.metric_value > 0.03  # >3%
        assert "above industry average" in conversion_insight.actionable_recommendation
        
        # Test traffic source insight  
        traffic_insight = next((i for i in insights if i.insight_type == "traffic_source_effectiveness"), None)
        assert traffic_insight is not None
        assert "organic" in traffic_insight.actionable_recommendation.lower()
    
    async def test_business_value_scoring(self, affiliate_deliverable):
        insights = await content_aware_learning_engine._extract_affiliate_insights([affiliate_deliverable])
        
        for insight in insights:
            assert insight.confidence_score >= 0.5
            assert insight.confidence_score <= 1.0
            if insight.metric_value:
                assert insight.metric_value > 0
```

### Integration Tests

Test the complete workflow:

```python
async def test_complete_affiliate_workflow():
    workspace_id = "test-workspace"
    
    # Simulate deliverable processing
    result = await content_aware_learning_engine.analyze_workspace_content(workspace_id)
    
    assert result['status'] == 'completed'
    assert 'affiliate_marketing' in result.get('domains_analyzed', [])
    assert result['insights_generated'] > 0
    
    # Test insight retrieval
    insights = await content_aware_learning_engine.get_actionable_learnings(
        workspace_id,
        DomainType.AFFILIATE_MARKETING
    )
    
    assert len(insights) > 0
    assert any("conversion rate" in insight.lower() for insight in insights)
```

## Performance Considerations

### Pattern Optimization

**Efficient Regex Patterns:**
```python
# Good: Compiled patterns for better performance
import re

class DomainPatterns:
    def __init__(self):
        self.affiliate_conversion = re.compile(r'conversion\s+rate[:\s]+(\d+\.?\d*)%', re.IGNORECASE)
        self.affiliate_roi = re.compile(r'roi[:\s]+(\d+\.?\d*)%', re.IGNORECASE)
    
    def extract_conversion_rate(self, content):
        matches = self.affiliate_conversion.findall(content)
        return [float(m) for m in matches]
```

**Content Processing Limits:**
```python
# Limit content analysis to prevent performance issues
def _combine_deliverable_content(self, deliverables: List[Dict[str, Any]], max_chars: int = 10000) -> str:
    combined = []
    total_chars = 0
    
    for deliverable in deliverables:
        content = str(deliverable.get('content', ''))
        if total_chars + len(content) > max_chars:
            content = content[:max_chars - total_chars]
        combined.append(content)
        total_chars += len(content)
        
        if total_chars >= max_chars:
            break
    
    return ' '.join(combined)
```

### Memory Management

**Efficient Insight Storage:**
```python
# Batch insight storage for better performance
async def _store_domain_insights_batch(self, workspace_id: str, insights: List[BusinessInsight]) -> int:
    stored_count = 0
    batch_size = 10
    
    for i in range(0, len(insights), batch_size):
        batch = insights[i:i + batch_size]
        try:
            # Process batch
            for insight in batch:
                success = await self._store_insight(workspace_id, insight)
                if success:
                    stored_count += 1
        except Exception as e:
            logger.error(f"Error storing insight batch: {e}")
            continue
    
    return stored_count
```

## Troubleshooting Common Issues

### Domain Detection Issues

**Problem**: New domain not being detected automatically
**Solution**: Check detection patterns and content analysis

```python
# Debug domain detection
async def debug_domain_detection(self, deliverable):
    analysis_text = f"{deliverable.get('title', '')} {deliverable.get('description', '')}"
    content = str(deliverable.get('content', ''))[:1000]
    analysis_text += f" {content}"
    
    logger.info(f"Analysis text: {analysis_text}")
    
    for domain, keywords in domain_patterns.items():
        matches = [keyword for keyword in keywords if keyword in analysis_text.lower()]
        if matches:
            logger.info(f"Domain {domain}: matched keywords {matches}")
```

### Pattern Matching Issues

**Problem**: Patterns not extracting expected values
**Solution**: Test patterns individually and validate regex

```python
# Test pattern extraction
def test_pattern_extraction(self, content, pattern):
    import re
    matches = re.findall(pattern, content, re.IGNORECASE)
    logger.info(f"Pattern '{pattern}' found matches: {matches}")
    return matches
```

### Performance Issues

**Problem**: Slow insight extraction
**Solution**: Optimize patterns and limit content analysis

```python
# Profile extraction performance
import time

async def profile_extraction(self, deliverables):
    start_time = time.time()
    insights = await self._extract_domain_insights(domain, deliverables)
    end_time = time.time()
    
    logger.info(f"Extraction took {end_time - start_time:.2f}s for {len(deliverables)} deliverables")
    logger.info(f"Generated {len(insights)} insights")
    
    return insights
```

## Domain Integration Checklist

- [ ] **Domain Enum**: Added to `DomainType` 
- [ ] **Pattern Library**: Created domain-specific patterns
- [ ] **Extractor Method**: Implemented `_extract_[domain]_insights`
- [ ] **Extractor Registration**: Added to `domain_extractors` dict
- [ ] **Detection Patterns**: Added to `domain_patterns` dict  
- [ ] **Quality Criteria**: Configured in `domain_quality_criteria`
- [ ] **Agent Mapping**: Added to `_infer_domain_from_agent`
- [ ] **API Documentation**: Updated `get_domain_description`
- [ ] **Unit Tests**: Created comprehensive test suite
- [ ] **Integration Tests**: Tested complete workflow
- [ ] **Performance Testing**: Validated extraction performance
- [ ] **Documentation**: Updated domain integration guide

## Best Practices

### Pattern Design
1. **Be Specific**: Create patterns that match your domain's unique terminology
2. **Handle Variations**: Account for different formatting and language variations
3. **Avoid Overlaps**: Ensure patterns don't conflict with other domains
4. **Test Thoroughly**: Validate patterns against real content samples

### Insight Quality
1. **Quantifiable Metrics**: Prefer insights with specific numbers and comparisons
2. **Actionable Recommendations**: Ensure insights provide clear next steps
3. **Business Value**: Focus on insights that directly impact business outcomes
4. **Confidence Scoring**: Accurately assess confidence based on evidence quality

### Performance Optimization
1. **Limit Content Size**: Process only relevant portions of large content
2. **Batch Operations**: Group database operations for efficiency
3. **Cache Patterns**: Compile regex patterns for reuse
4. **Monitor Performance**: Track extraction times and optimize bottlenecks

This integration guide enables developers to seamlessly add new business domains to the Content-Aware Learning System, expanding its intelligence and business value across diverse industries and use cases.