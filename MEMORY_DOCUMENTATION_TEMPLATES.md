# Memory Documentation Templates
## Standardized Templates for Capturing Memory-Worthy Patterns

> **Purpose**: Provide consistent, reusable templates for documenting architectural improvements, UX enhancements, and technical solutions in `TROUBLESHOOTING_MEMORY.md`.

---

## 🎯 Template Selection Guide

### Quick Decision Matrix

| **Change Type** | **Use Template** | **Auto-Trigger Score** |
|---|---|---|
| New React component with professional styling | UX_IMPROVEMENT | 75 |
| API response time improvement >50% | PERFORMANCE_FIX | 80 |
| Bug fix for recurring 404/sync issues | BUG_PATTERN | 70 |
| New integration between systems | ARCHITECTURE_PATTERN | 85 |
| Agent workflow enhancement | WORKFLOW_ENHANCEMENT | 65 |

### Template Selection Algorithm

```python
def select_template(change_data):
    """Select appropriate template based on change characteristics"""
    
    if change_data.affects_user_interface and change_data.improves_experience:
        return 'UX_IMPROVEMENT'
    
    if change_data.performance_improvement > 50:
        return 'PERFORMANCE_FIX'
    
    if change_data.fixes_recurring_issue:
        return 'BUG_PATTERN'
    
    if change_data.spans_multiple_systems:
        return 'ARCHITECTURE_PATTERN'
    
    if 'ai_agents' in change_data.affected_paths:
        return 'WORKFLOW_ENHANCEMENT'
    
    return 'GENERAL_PATTERN'
```

---

## 📋 Template Definitions

### Template 1: UX_IMPROVEMENT

**When to Use**: New components, improved user experience, better content presentation

```markdown
### N. [Component Name] UX Enhancement - USER_EXPERIENCE

**User Experience Problem**: [Describe the poor UX that users encountered]

**Previous State**: 
- [How content was displayed before]
- [User friction points]
- [Usability issues]

**UX Solution Strategy**: [High-level approach to improvement]

**Implementation Architecture**:
```typescript
// Key component patterns with explanations
// Focus on reusable design patterns
// Include styling and interaction patterns
```

**User Experience Improvements**:
- [Specific UX enhancements achieved]
- [Accessibility improvements]
- [Mobile/responsive considerations]

**Reusable Design Patterns**:
```typescript
// Extractable components for future use
// Consistent styling approaches  
// Standard interaction patterns
```

**Integration Guide**: 
- [How to apply this pattern to other components]
- [Props interface and customization options]
- [Dependencies and requirements]

**Before/After Metrics**:
- User task completion: [Before] → [After]
- User satisfaction: [Feedback]
- Accessibility score: [Before] → [After]

**Files Affected**:
- [List of component files with brief description of changes]

**Future Applications**: [Where this pattern could be used next]

**Sub-Agent Usage**:
- Use **ui-designer** for similar component enhancements
- Use **accessibility-expert** for inclusive design validation
```

### Template 2: PERFORMANCE_FIX  

**When to Use**: Speed improvements, loading optimizations, API performance enhancements

```markdown
### N. [System Component] Performance Optimization - PERFORMANCE

**Performance Problem**: [Specific bottleneck causing slowdown]

**Impact on Users**:
- [How performance issue affected user experience]
- [Business impact of slowdown]

**Baseline Metrics**: 
- Load time: [Before measurement]
- API response: [Before measurement]
- User perception: [Before feedback]

**Performance Strategy**: [Technical approach to optimization]

**Implementation Pattern**:
```typescript
// Progressive loading patterns
// Caching strategies
// Optimization techniques
```

**Optimization Results**: 
- Load time: [Before] → [After] ([% improvement])
- API response: [Before] → [After] ([% improvement])  
- User satisfaction: [Before] → [After]

**Scaling Considerations**:
- [How pattern handles increased load]
- [Memory usage implications]
- [Network impact analysis]

**Monitoring Setup**:
```typescript
// Performance tracking code
// Metrics collection patterns
// Alert thresholds
```

**Prevention Guidelines**:
- [Code review checklist for performance]
- [Architecture decisions that prevent slowdowns]
- [Load testing recommendations]

**Files Affected**:
- [List of optimized files with performance impact]

**Sub-Agent Usage**:
- Use **performance-optimizer** for similar bottlenecks
- Use **monitoring-specialist** for metrics tracking
```

### Template 3: BUG_PATTERN

**When to Use**: Recurring issues, systematic bug fixes, prevention strategies

```markdown
### N. [Issue Type] Recurring Pattern Fix - BUG_PREVENTION

**Bug Pattern**: [Description of the recurring issue type]

**Symptoms**:
- [Observable signs of the problem]
- [Error messages or behaviors]
- [User impact when bug occurs]

**Root Cause Analysis**: [Why this pattern keeps happening]

**Detection Signatures**:
- [Log patterns that indicate this issue]
- [UI behaviors that signal the problem]
- [API responses that reveal the bug]

**Fix Implementation**:
```python
# Specific code fix patterns
# Validation approaches
# Error handling improvements
```

**Prevention Strategy**:
```python
# Defensive coding patterns
# Input validation
# State management safeguards
```

**Diagnostic Workflow**:
1. [Step-by-step troubleshooting process]
2. [Verification steps]
3. [Resolution confirmation]

**Automated Detection**:
```python
# Code patterns or checks that catch this early
# Monitoring alerts for early warning
# Test patterns that prevent regression
```

**Testing Strategy**:
- [Unit tests that catch this pattern]
- [Integration tests for prevention]
- [Manual verification steps]

**Files Affected**:
- [List of files with bug fixes]

**Sub-Agent Usage**:
- Use **bug-hunter** for similar pattern detection
- Use **test-specialist** for prevention test creation
```

### Template 4: ARCHITECTURE_PATTERN

**When to Use**: System integration improvements, cross-component solutions, architectural decisions

```markdown
### N. [Integration Name] Architecture Pattern - SYSTEM_INTEGRATION

**Integration Challenge**: [System coordination problem being solved]

**Architecture Before**: 
- [Previous system interaction patterns]
- [Limitations and friction points]
- [Scalability concerns]

**Solution Architecture**: [High-level design approach]

**Implementation Strategy**:
```python
# Key architectural patterns
# Service coordination approaches
# Data flow improvements
```

**Integration Benefits**:
- [System coordination improvements]
- [Maintainability enhancements]  
- [Scalability improvements]

**Pattern Abstractions**:
```python
# Reusable architectural components
# Standard integration interfaces
# Common coordination patterns
```

**Cross-System Impact**:
- [Database schema implications]
- [API contract changes]
- [Frontend integration requirements]

**Migration Strategy**: [How to apply this pattern to existing code]

**Monitoring and Health Checks**:
```python
// Health monitoring for integrated systems
// Performance tracking across boundaries
// Error detection and recovery
```

**Files Affected**:
- [List of system files modified across components]

**Sub-Agent Usage**:
- Use **system-architect** for similar integration challenges
- Use **api-contract-guardian** for interface design
- Use **db-steward** for data layer coordination
```

### Template 5: WORKFLOW_ENHANCEMENT

**When to Use**: Agent coordination improvements, task execution enhancements, tool integrations

```markdown
### N. [Workflow Name] Enhancement - AGENT_COORDINATION  

**Workflow Problem**: [Agent coordination or task execution challenge]

**Agent Interaction Before**:
- [Previous coordination patterns]
- [Communication breakdowns]  
- [Task handoff issues]

**Enhancement Strategy**: [Approach to improving workflow]

**Implementation Pattern**:
```python
# Agent coordination improvements
# Task delegation patterns
# Tool integration enhancements
```

**Workflow Improvements**:
- [Task completion rate improvements]
- [Agent utilization optimization]
- [Communication clarity enhancements]

**Reusable Coordination Patterns**:
```python
# Standard agent handoff patterns
# Task prioritization algorithms
# Resource coordination approaches
```

**Tool Integration Guide**: [How new tools are incorporated]

**Performance Impact**: 
- Task completion: [Before] → [After]
- Agent efficiency: [Metrics]
- User satisfaction: [Feedback]

**Sub-Agent Orchestration**:
- [When to trigger specific sub-agents]
- [Expected interaction patterns]
- [Coordination protocols]

**Files Affected**:
- [List of agent and coordination files]

**Future Workflow Applications**: [Where this pattern applies next]

**Sub-Agent Usage**:
- Use **workflow-optimizer** for similar coordination challenges
- Use **agent-coordinator** for handoff improvements
```

---

## 🔧 Template Population Guidelines

### Auto-Population Fields

These fields can be automatically filled by pattern detection:

```python
AUTO_FILLABLE_FIELDS = {
    'files_affected': 'git_diff_analysis',
    'performance_metrics': 'benchmark_comparison',
    'before_after_code': 'git_diff_extraction',
    'change_scope': 'impact_analysis',
    'pattern_keywords': 'semantic_analysis'
}
```

### Manual Review Required

These fields need human validation:

- **Problem description**: Ensure accuracy and clarity
- **Solution strategy**: Verify technical correctness
- **Prevention guidelines**: Validate actionability
- **Sub-agent usage**: Confirm workflow patterns
- **Future applications**: Assess reusability scope

### Quality Validation Checklist

Before adding to memory:

- [ ] **Problem-Solution Clarity**: Clear mapping between problem and solution
- [ ] **Actionable Steps**: Concrete implementation guidance
- [ ] **Reusability**: Pattern can be applied to other contexts
- [ ] **Code Examples**: Working, tested code snippets
- [ ] **Sub-Agent Integration**: Clear guidance for specialized agents
- [ ] **Prevention Focus**: Proactive measures to avoid recurrence
- [ ] **Metrics Included**: Measurable improvement indicators

---

## 📊 Template Usage Analytics

### Tracking Template Effectiveness

```python
def track_template_usage():
    """Monitor how often each template type is used and referenced"""
    return {
        'template_popularity': {
            'UX_IMPROVEMENT': count_entries_by_type('UX_IMPROVEMENT'),
            'PERFORMANCE_FIX': count_entries_by_type('PERFORMANCE_FIX'),
            'BUG_PATTERN': count_entries_by_type('BUG_PATTERN'),
            'ARCHITECTURE_PATTERN': count_entries_by_type('ARCHITECTURE_PATTERN'),
            'WORKFLOW_ENHANCEMENT': count_entries_by_type('WORKFLOW_ENHANCEMENT')
        },
        'reference_frequency': count_memory_lookups_by_template(),
        'success_rate': measure_solution_effectiveness_by_template(),
        'time_saved': calculate_time_saved_per_template()
    }
```

### Template Evolution

Templates should evolve based on usage:

- **High-frequency templates**: Add more detailed sections
- **Low-reference templates**: Simplify or merge with others  
- **High-success templates**: Use as models for new templates
- **Low-success templates**: Improve guidance and examples

---

## 🎯 Integration with Proactive System

### Template Recommendation Engine

```python
def recommend_template(pattern_analysis):
    """AI-powered template recommendation based on change patterns"""
    
    recommendations = []
    confidence_scores = {}
    
    # Analyze change characteristics
    if pattern_analysis.ui_component_changes:
        confidence_scores['UX_IMPROVEMENT'] = calculate_ui_confidence(pattern_analysis)
    
    if pattern_analysis.performance_improvements:
        confidence_scores['PERFORMANCE_FIX'] = calculate_performance_confidence(pattern_analysis)
    
    # Return top recommendation with confidence
    return max(confidence_scores.items(), key=lambda x: x[1])
```

### Automated Template Population

```python
def populate_template_automatically(template_type, change_context):
    """Use AI to pre-populate template fields"""
    
    template = load_template(template_type)
    
    auto_fields = {
        'files_affected': extract_files_from_diff(change_context.git_diff),
        'before_after_metrics': compare_performance_metrics(change_context),
        'code_examples': extract_key_code_patterns(change_context),
        'impact_analysis': analyze_change_impact(change_context)
    }
    
    return populate_template_fields(template, auto_fields)
```

This template system ensures consistent, high-quality documentation of memory-worthy patterns while making it easy for docs-scribe to automatically suggest relevant templates based on detected changes.