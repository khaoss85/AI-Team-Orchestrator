---
title: Sub-Agent Cache Optimization Guidelines
description: Cost-effective quality gates through intelligent caching and pattern recognition
---

# Cache-Aware Quality Gates

## Pattern Caching Strategy

### 🎯 **High-Cache Scenarios (Skip AI calls)**
- **Identical file modifications**: Hash-based deduplication
- **Known safe patterns**: Pre-approved code templates
- **Documentation-only changes**: Syntax validation vs full AI review
- **Minor formatting changes**: Code style vs architectural impact

### ⚡ **Smart Skip Conditions**
```yaml
Skip sdk-guardian if:
  - No import changes in Python files
  - No OpenAI API calls modified
  - Only comments/docstrings changed

Skip db-steward if:
  - No database.py, models.py modifications
  - No migration files touched
  - No SQL queries in changes

Skip api-contract-guardian if:
  - No routes/ directory changes
  - No API client modifications
  - No endpoint additions/removals
```

### 💰 **Cost Optimization Metrics**
```
Target Reduction: 70% fewer API calls
Method: Conditional triggering + batching + caching
Monthly Budget: $30-50 vs $150-200
Acceptable Quality Trade-off: <5% missed issues
```

### 🔍 **Progressive Analysis Depth**
1. **Level 1 (Free)**: Static pattern matching, file type analysis
2. **Level 2 (Low cost)**: Simple AI classification (100-500 tokens)
3. **Level 3 (Full review)**: Complete architectural analysis (2,000-4,000 tokens)

Only escalate to Level 3 for high-impact changes.

## Implementation Priority

### **P0 - Immediate (This Week)**
- Conditional triggering based on file patterns
- Basic batching for related agents
- Skip agents for non-relevant changes

### **P1 - Short Term (Next Month)**  
- Hash-based change deduplication
- Pattern recognition for safe modifications
- Token budget enforcement per review

### **P2 - Long Term (Optional)**
- ML-based change impact prediction
- Historical success rate optimization
- Adaptive token allocation

## Quality vs Cost Balance

**Non-Negotiable Quality**: 
- Security violations must always trigger full review
- Database schema changes always trigger db-steward
- New API endpoints always trigger contract validation

**Cost-Optimizable**:
- Documentation updates (lightweight validation)
- Code formatting changes (syntax-only checks)
- Test file modifications (pattern-based review)