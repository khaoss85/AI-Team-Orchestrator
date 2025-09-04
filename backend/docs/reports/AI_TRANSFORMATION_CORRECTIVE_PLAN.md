# 🔧 AI TRANSFORMATION CORRECTIVE ACTION PLAN

## Overview
This document provides the specific code changes required to achieve 90+ compliance score and eliminate all hard-coded business logic violations.

## File 1: simple_tool_orchestrator.py

### Current Violation (Lines 187-219):
```python
def _create_search_query(self, task_objective: str, business_context: Dict[str, Any]) -> str:
    # HARD-CODED PATTERN MATCHING
    if "contact" in task_objective.lower():
        query_parts.append("lead generation contact database")
    elif "email" in task_objective.lower():
        query_parts.append("email marketing campaigns templates")
    # etc...
```

### AI-Driven Solution:
```python
async def _create_search_query(self, task_objective: str, business_context: Dict[str, Any]) -> str:
    """AI-driven semantic query generation"""
    from services.ai_provider_abstraction import ai_provider_manager
    
    prompt = f"""
    Generate an effective web search query for this task objective.
    Be specific and include relevant industry terms.
    
    Task Objective: {task_objective}
    Business Context: {json.dumps(business_context, default=str)[:500]}
    
    Return ONLY the search query string, nothing else.
    """
    
    try:
        query = await ai_provider_manager.call_ai(
            provider_type='openai_sdk',
            agent_config={"name": "QueryGenerator", "model": "gpt-4o-mini"},
            messages=[{"role": "user", "content": prompt}],
            use_json_format=False
        )
        
        # Add current year for recency
        return f"{query.strip()} 2024"
    except Exception as e:
        logger.warning(f"AI query generation failed, using fallback: {e}")
        # Simple fallback without hard-coded patterns
        clean_objective = task_objective.replace("🎯", "").replace("🤖", "").strip()
        return f"{clean_objective} best practices 2024"
```

### Remove _extract_domain_keywords() entirely:
```python
# DELETE LINES 221-240 - This entire method should be removed
```

## File 2: missing_deliverable_auto_completion.py

### Current Violation (Lines 138-154):
```python
def _get_expected_deliverables_for_goal(self, goal_title: str) -> List[str]:
    # HARD-CODED KEYWORD MATCHING
    if any(keyword in goal_title_lower for keyword in ['email', 'newsletter']):
        return self.expected_deliverables_per_goal.get('email_marketing', ...)
```

### AI-Driven Solution:
```python
async def _get_expected_deliverables_for_goal(self, goal_title: str) -> List[str]:
    """AI-driven deliverable expectation generation"""
    from services.ai_provider_abstraction import ai_provider_manager
    
    prompt = f"""
    Based on this goal, suggest 3-5 specific deliverables that would demonstrate achievement.
    Be concrete and actionable.
    
    Goal: {goal_title}
    
    Return a JSON array of deliverable names.
    Example: ["strategic_plan", "implementation_guide", "performance_metrics"]
    """
    
    try:
        result = await ai_provider_manager.call_ai(
            provider_type='openai_sdk',
            agent_config={"name": "DeliverableGenerator", "model": "gpt-4o-mini"},
            messages=[{"role": "user", "content": prompt}],
            use_json_format=True
        )
        
        if isinstance(result, list):
            return result
        elif isinstance(result, dict) and 'deliverables' in result:
            return result['deliverables']
        else:
            raise ValueError("Invalid AI response format")
            
    except Exception as e:
        logger.warning(f"AI deliverable generation failed: {e}")
        # Generic fallback without domain assumptions
        default_count = int(os.getenv('DEFAULT_DELIVERABLES_COUNT', '3'))
        return [f'deliverable_{i+1}' for i in range(default_count)]
```

## File 3: learning_quality_feedback_loop.py

### Current Violation (Lines 84-104):
```python
self.domain_quality_criteria = {
    'instagram_marketing': {...},
    'email_marketing': {...},
    # HARD-CODED DOMAIN LIST
}
```

### AI-Driven Solution:
```python
async def _get_domain_quality_criteria(self, domain_context: str) -> Dict[str, Any]:
    """AI-driven quality criteria generation for any domain"""
    from services.ai_provider_abstraction import ai_provider_manager
    
    # Check cache first
    if domain_context in self.domain_quality_criteria_cache:
        return self.domain_quality_criteria_cache[domain_context]
    
    prompt = f"""
    Generate quality criteria for this business domain.
    Consider industry standards and best practices.
    
    Domain Context: {domain_context}
    
    Return JSON with:
    - base_threshold: float between 0.5 and 0.9
    - key_quality_indicators: list of important metrics
    - performance_multiplier: float for quality boost
    """
    
    try:
        criteria = await ai_provider_manager.call_ai(
            provider_type='openai_sdk',
            agent_config={"name": "QualityCriteriaGenerator", "model": "gpt-4o-mini"},
            messages=[{"role": "user", "content": prompt}],
            use_json_format=True
        )
        
        # Validate and cache
        if isinstance(criteria, dict):
            criteria.setdefault('base_threshold', 0.7)
            criteria.setdefault('learned_criteria', [])
            criteria.setdefault('performance_multiplier', 1.0)
            
            self.domain_quality_criteria_cache[domain_context] = criteria
            return criteria
            
    except Exception as e:
        logger.warning(f"AI quality criteria generation failed: {e}")
        
    # Generic fallback
    return {
        "base_threshold": 0.7,
        "learned_criteria": [],
        "performance_multiplier": 1.0
    }

def __init__(self):
    # Replace hard-coded dictionary with dynamic cache
    self.domain_quality_criteria_cache = {}
```

## File 4: deliverable_achievement_mapper.py

### Current Violation (Lines 44-84):
```python
self.quantity_patterns = [
    r'(\d+)\s*(?:contacts?|leads?|prospects?)',  # HARD-CODED PATTERNS
]
self.deliverable_patterns = {
    'items_created': [r'contact.*list', ...],  # DOMAIN-SPECIFIC
}
```

### AI-Driven Solution:
```python
async def _extract_achievements_with_ai(self, content: str, context: str) -> Dict[str, int]:
    """AI-driven achievement extraction for any domain"""
    from services.ai_provider_abstraction import ai_provider_manager
    
    prompt = f"""
    Extract quantifiable achievements from this content.
    Look for any measurable outputs, completed items, or metrics.
    
    Context: {context}
    Content: {content[:1500]}
    
    Return JSON with categories and counts:
    {{
        "items_created": <number>,
        "deliverables_completed": <number>,
        "data_processed": <number>,
        "metrics_achieved": <number>,
        "other_achievements": <number>
    }}
    
    Be conservative - only include what you can clearly identify.
    """
    
    try:
        achievements = await ai_provider_manager.call_ai(
            provider_type='openai_sdk',
            agent_config={"name": "AchievementExtractor", "model": "gpt-4o-mini"},
            messages=[{"role": "user", "content": prompt}],
            use_json_format=True
        )
        
        if isinstance(achievements, dict):
            return achievements
            
    except Exception as e:
        logger.warning(f"AI achievement extraction failed: {e}")
    
    # Minimal fallback - just count numbers mentioned
    import re
    numbers = re.findall(r'\b(\d+)\b', content)
    total = sum(int(n) for n in numbers if int(n) < 10000)  # Reasonable limit
    
    return {
        "items_created": min(total, 100),
        "deliverables_completed": 1 if content else 0,
        "data_processed": 0,
        "metrics_achieved": 0
    }

def __init__(self):
    # Remove all hard-coded patterns
    self.extraction_methods = ["ai_semantic_analysis"]
    # No pattern libraries needed
```

## Implementation Strategy

### Phase 1: Immediate Changes (2-3 hours)
1. Update all 4 files with AI-driven methods
2. Remove all hard-coded patterns and domain lists
3. Add proper error handling and fallbacks

### Phase 2: Testing (1-2 hours)
1. Test with existing domains (marketing, email)
2. Test with NEW domains (finance, healthcare, education)
3. Verify fallback mechanisms work

### Phase 3: Validation (1 hour)
1. Run quality gates again
2. Verify 90+ compliance score
3. Document any remaining issues

## Expected Outcomes

After implementing these changes:
- **Compliance Score**: 90-95/100 ✅
- **Domain Agnostic**: TRUE ✅
- **Hard-coded Patterns**: 0 ✅
- **AI-Driven**: 100% ✅
- **Production Ready**: YES ✅

## Success Criteria

The transformation is complete when:
1. All 4 files use AI for classification/extraction
2. System works with ANY business domain without code changes
3. Compliance score exceeds 90/100
4. No hard-coded business logic remains
5. All quality gates pass

## Risk Mitigation

1. **AI Service Unavailability**: Generic fallbacks that don't assume domain
2. **Performance Impact**: Cache AI responses for repeated queries
3. **Cost Management**: Use gpt-4o-mini for these simple classifications
4. **Testing Coverage**: Create test suite with 10+ different domains