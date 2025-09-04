#!/usr/bin/env python3
"""
Test script to verify the AI Goal Matcher architectural fix
Ensures the "first active goal" anti-pattern is eliminated
"""

import asyncio
import json
from datetime import datetime
from services.ai_goal_matcher import AIGoalMatcher

async def test_goal_matcher():
    """Test the enhanced AI Goal Matcher with various scenarios"""
    
    print("=" * 70)
    print("🧪 TESTING AI GOAL MATCHER ARCHITECTURAL FIX")
    print("=" * 70)
    
    # Initialize matcher
    matcher = AIGoalMatcher()
    
    # Test data: Multiple goals with different types
    test_goals = [
        {
            "id": "goal-001",
            "description": "Piano editoriale mensile con contenuti settimanali",
            "status": "active",
            "metric_type": "deliverable_calendar"
        },
        {
            "id": "goal-002", 
            "description": "Strategia di interazione con community e social media",
            "status": "active",
            "metric_type": "deliverable_strategy"
        },
        {
            "id": "goal-003",
            "description": "Email sequence for customer onboarding",
            "status": "active",
            "metric_type": "deliverable_emails"
        },
        {
            "id": "goal-004",
            "description": "Contact list and CRM setup",
            "status": "inactive",
            "metric_type": "deliverable_contacts"
        }
    ]
    
    # Test cases with expected matches
    test_cases = [
        {
            "deliverable": {
                "title": "Email sequence 2 - Case studies and social proof",
                "type": "email_sequence",
                "content": {"emails": ["Welcome email", "Case study 1", "Case study 2"]}
            },
            "expected_goal": "goal-003",
            "scenario": "Email deliverable should match email goal"
        },
        {
            "deliverable": {
                "title": "Piano editoriale dettagliato per Marzo",
                "type": "editorial_calendar",
                "content": {"weeks": ["Week 1", "Week 2", "Week 3", "Week 4"]}
            },
            "expected_goal": "goal-001",
            "scenario": "Italian editorial calendar should match piano editoriale goal"
        },
        {
            "deliverable": {
                "title": "Strategia completa di engagement sociale",
                "type": "strategy_document",
                "content": {"platforms": ["Instagram", "LinkedIn", "Twitter"]}
            },
            "expected_goal": "goal-002",
            "scenario": "Strategy document should match strategia goal"
        },
        {
            "deliverable": {
                "title": "Random business report Q1 2025",
                "type": "report",
                "content": {"quarter": "Q1", "year": 2025}
            },
            "expected_goal": "ANY_ACTIVE",
            "scenario": "Unrelated deliverable should use smart fallback (NOT first active)"
        }
    ]
    
    print("\n🔬 Running Test Cases:\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['scenario']}")
        print(f"  Deliverable: {test_case['deliverable']['title']}")
        
        # Test with AI matcher (will use fallback if OpenAI not available)
        try:
            result = await matcher.analyze_and_match(
                deliverable_content=test_case['deliverable'],
                available_goals=test_goals
            )
            
            print(f"  ✅ Matched to: Goal {result.goal_id[-3:]}")
            print(f"  📊 Confidence: {result.confidence:.0f}%")
            print(f"  💭 Reasoning: {result.reasoning}")
            
            # Verify it's not always the first active goal
            if test_case['expected_goal'] != "ANY_ACTIVE":
                if result.goal_id == test_case['expected_goal']:
                    print(f"  ✨ PASS: Correct goal matched!")
                else:
                    print(f"  ⚠️  WARNING: Expected {test_case['expected_goal']}, got {result.goal_id}")
            else:
                # For unrelated deliverables, verify it's NOT always goal-001
                if result.goal_id != "goal-001" or result.confidence < 50:
                    print(f"  ✨ PASS: Smart fallback used (not first active goal)")
                else:
                    print(f"  ⚠️  WARNING: Might still be using first active goal pattern")
                    
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
        
        print()
    
    # Test fallback logic directly
    print("\n🔧 Testing Fallback Rule Matching Directly:\n")
    
    # Filter active goals
    active_goals = [g for g in test_goals if g.get("status") == "active"]
    
    # Test with no keyword matches
    fallback_result = matcher._fallback_rule_match(
        title="Generic business document XYZ123",
        deliverable_type="unknown",
        available_goals=active_goals
    )
    
    print(f"Fallback test (no matches):")
    print(f"  Goal selected: {fallback_result.goal_id}")
    print(f"  Confidence: {fallback_result.confidence}%")
    print(f"  Reasoning: {fallback_result.reasoning}")
    
    # Run multiple times to verify it's not always the same goal
    print("\n🎲 Testing fallback distribution (10 different titles):")
    selected_goals = []
    test_titles = [
        "Project Alpha Documentation",
        "Beta Testing Results",
        "Gamma Analysis Report", 
        "Delta Strategy Plan",
        "Epsilon Market Research",
        "Zeta Financial Report",
        "Eta Customer Feedback",
        "Theta Implementation Guide",
        "Iota Performance Metrics",
        "Kappa Risk Assessment"
    ]
    
    for title in test_titles:
        result = matcher._fallback_rule_match(
            title=title,
            deliverable_type="generic",
            available_goals=active_goals
        )
        selected_goals.append(result.goal_id)
        print(f"  - {title:30s} → Goal {result.goal_id[-3:]}")
    
    # Check distribution
    unique_goals = set(selected_goals)
    if len(unique_goals) > 1:
        print(f"\n✅ ARCHITECTURAL FIX VERIFIED: Using {len(unique_goals)} different goals")
        print("   The 'first active goal' anti-pattern has been eliminated!")
    else:
        print(f"\n⚠️  WARNING: All fallbacks selected the same goal: {unique_goals}")
        print("   This might indicate the anti-pattern still exists")
    
    print("\n" + "=" * 70)
    print("🏁 TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_goal_matcher())