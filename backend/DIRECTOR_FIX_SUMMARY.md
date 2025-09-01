# Director Agent Budget-Aware Team Generation Fix

## Problem Statement
The system was generating only 1 agent (Project Manager) for high-budget projects (e.g., 10,000 EUR) instead of appropriately scaling the team size based on budget.

## Root Cause Analysis

### Primary Issue: NameError in Validation
**Location**: `backend/ai_agents/director.py`, line 1473 in `_validate_and_sanitize_proposal` method

**Bug**: Reference to undefined variable `max_team_for_performance`
```python
# BROKEN CODE (before fix)
performance_max = max_team_for_performance  # NameError: name 'max_team_for_performance' is not defined
```

This caused the validation method to fail with a NameError, triggering the fallback logic which was incorrectly configured to create minimal teams.

### Secondary Issue: Field Name Mismatch
**Location**: Multiple places in `director.py`

**Bug**: Inconsistent field naming between `BudgetConstraint` model and code
- Model uses: `max_cost`
- Code looked for: `max_amount`

## Fixes Applied

### 1. Fixed NameError in Validation (Lines 1473-1475)
```python
# FIXED CODE
budget_amount = proposal_request.budget_limit or 5000
performance_max = min(8, max(3, int(budget_amount / 1500)))  # Dynamic sizing based on budget
```

### 2. Enhanced Budget Field Compatibility (Lines 200-207, 1187, 1701)
```python
# Support both field names for compatibility
budget = (
    constraints_dict.get("max_amount")
    or constraints_dict.get("max_cost")  # Support both field names
    # ... additional fallbacks
)
```

### 3. Fixed Tool Format in Fallback Agents (Lines 1758-1834)
Changed from string array to proper dictionary format:
```python
# Before: "tools": ["web_search", "data_analysis"]
# After:
"tools": [
    {"type": "web_search", "name": "web_search", "description": "Web search capability"},
    {"type": "function", "name": "data_analysis", "description": "Data analysis capability"}
]
```

## Budget-Based Team Sizing Formula
```python
optimal_team_size = min(8, max(3, int(budget / 1500)))
```

### Results:
- **< 1,500 EUR**: 3 agents (minimum team)
- **1,500 - 3,000 EUR**: 3 agents
- **3,000 - 4,500 EUR**: 3 agents
- **4,500 - 6,000 EUR**: 4 agents
- **6,000 - 7,500 EUR**: 5 agents
- **7,500 - 9,000 EUR**: 6 agents
- **9,000 - 10,500 EUR**: 7 agents
- **≥ 12,000 EUR**: 8 agents (maximum cap)

## Test Results

### Before Fix
- 10,000 EUR budget → 1 agent (Project Manager only)
- Cost: 1,140 EUR (severe under-utilization)

### After Fix
- 10,000 EUR budget → 6 agents (full team)
- Roles: Project Manager, Business Research Specialist, Email Marketing, Content Marketing, Social Media Manager, Task Executor
- Cost: 2,280 EUR (appropriate utilization)

## Verification
Test scripts created:
1. `test_director_fix.py` - Unit tests for fallback logic
2. `test_director_api_flow.py` - End-to-end API flow tests

Both tests confirm:
✅ Fallback correctly generates 6 agents for 10K budget
✅ Validation no longer crashes with NameError
✅ Budget-aware team sizing formula working correctly

## Impact
- Users now get appropriately sized teams for their budget
- B2B projects with high budgets receive specialized agents (Business Research, Email Marketing, etc.)
- System properly utilizes available budget for team composition
- Fallback logic provides robust teams even when AI times out

## Files Modified
- `/Users/pelleri/Documents/ai-team-orchestrator/backend/ai_agents/director.py`

## Deployment Notes
No database changes required. The fix is backward compatible and will immediately improve team generation for new projects.