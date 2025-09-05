#!/usr/bin/env python3
"""
Test script for AI Insight Classification System
Verifies that insights are correctly categorized based on content
"""

import sys
import os
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

from services.ai_insight_classifier import insight_classifier
from unified_insight import InsightCategory
import json


def test_classification():
    """Test classification with actual insight content"""
    
    # Real insights from the system
    test_insights = [
        {
            "title": "recovery_success_rate shows 1.0 better performance than manual_intervention",
            "content": "recovery_success_rate shows 1.0 better performance than manual_intervention",
            "expected": InsightCategory.PERFORMANCE
        },
        {
            "title": "Develop or enhance vertical SaaS applications to cater to specific industries",
            "content": "Develop or enhance vertical SaaS applications to cater to specific industries.",
            "expected": InsightCategory.STRATEGY
        },
        {
            "title": "Percentage of GenAI Native Unicorns shows 45% better performance",
            "content": "Percentage of GenAI Native Unicorns shows 45% better performance than Proportion from previous years",
            "expected": InsightCategory.PERFORMANCE
        },
        {
            "title": "Annual Recurring Revenue per FTE shows 124.0 better performance",
            "content": "Annual Recurring Revenue per FTE shows 124.0 better performance than Previous year figures",
            "expected": InsightCategory.PERFORMANCE
        },
        {
            "title": "Market Volume shows 76.3 better performance",
            "content": "Market Volume shows 76.3 better performance than 2023 market volume",
            "expected": InsightCategory.PERFORMANCE
        },
        {
            "title": "Develop specialized SaaS applications targeting specific industries",
            "content": "Develop specialized SaaS applications targeting specific industries.",
            "expected": InsightCategory.STRATEGY
        },
        {
            "title": "Process bottleneck identified in deployment pipeline",
            "content": "A significant bottleneck has been identified in the deployment pipeline causing delays",
            "expected": InsightCategory.CONSTRAINT
        },
        {
            "title": "Optimize database queries for better performance",
            "content": "Optimize database queries to reduce latency and improve overall system performance",
            "expected": InsightCategory.OPTIMIZATION
        },
        {
            "title": "Security vulnerability in authentication system",
            "content": "Potential security risk identified in the authentication system that needs immediate attention",
            "expected": InsightCategory.RISK
        },
        {
            "title": "New market opportunity in emerging regions",
            "content": "Untapped market opportunity identified in emerging regions with high growth potential",
            "expected": InsightCategory.OPPORTUNITY
        }
    ]
    
    print("=" * 80)
    print("AI INSIGHT CLASSIFICATION TEST RESULTS")
    print("=" * 80)
    
    correct = 0
    total = len(test_insights)
    
    # Track category distribution
    category_counts = {}
    
    for idx, test_case in enumerate(test_insights, 1):
        # Classify the insight
        classified_category = insight_classifier.classify_insight(
            test_case["content"],
            test_case["title"]
        )
        
        # Get insight_type for database
        insight_type = insight_classifier.get_insight_type_from_category(classified_category)
        
        # Check if correct
        is_correct = classified_category == test_case["expected"]
        if is_correct:
            correct += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        # Track distribution
        category_counts[classified_category.value] = category_counts.get(classified_category.value, 0) + 1
        
        print(f"\nTest {idx}: {status}")
        print(f"  Title: {test_case['title'][:60]}...")
        print(f"  Expected: {test_case['expected'].value}")
        print(f"  Classified: {classified_category.value}")
        print(f"  DB Type: {insight_type}")
    
    print("\n" + "=" * 80)
    print(f"RESULTS: {correct}/{total} tests passed ({correct/total*100:.1f}% accuracy)")
    print("\nCATEGORY DISTRIBUTION:")
    for category, count in sorted(category_counts.items()):
        print(f"  {category}: {count} insights")
    
    print("\n" + "=" * 80)
    
    # Test batch classification
    print("\nTESTING BATCH CLASSIFICATION:")
    batch_insights = [
        {"content": i["content"], "title": i["title"]} 
        for i in test_insights
    ]
    
    batch_results = insight_classifier.classify_batch(batch_insights)
    print(f"Batch classified {len(batch_results)} insights")
    
    # Show distribution for realistic data
    print("\nREALISTIC DISTRIBUTION (Expected vs Actual):")
    expected_dist = {
        "performance": 5,
        "strategy": 2,
        "constraint": 1,
        "optimization": 1,
        "risk": 1,
        "opportunity": 1
    }
    
    actual_dist = {}
    for cat in batch_results:
        actual_dist[cat.value] = actual_dist.get(cat.value, 0) + 1
    
    for cat in expected_dist:
        exp = expected_dist.get(cat, 0)
        act = actual_dist.get(cat, 0)
        match = "✅" if exp == act else "⚠️"
        print(f"  {cat}: Expected {exp}, Got {act} {match}")
    
    return correct == total


def test_insight_type_mapping():
    """Test the mapping from category to database insight_type"""
    print("\n" + "=" * 80)
    print("DATABASE INSIGHT_TYPE MAPPING TEST")
    print("=" * 80)
    
    mappings = [
        (InsightCategory.PERFORMANCE, 'success_pattern'),
        (InsightCategory.STRATEGY, 'optimization'),
        (InsightCategory.OPERATIONAL, 'optimization'),
        (InsightCategory.DISCOVERY, 'discovery'),
        (InsightCategory.CONSTRAINT, 'constraint'),
        (InsightCategory.OPTIMIZATION, 'optimization'),
        (InsightCategory.RISK, 'risk'),
        (InsightCategory.OPPORTUNITY, 'opportunity'),
        (InsightCategory.GENERAL, 'discovery')
    ]
    
    for category, expected_type in mappings:
        actual_type = insight_classifier.get_insight_type_from_category(category)
        status = "✅" if actual_type == expected_type else "❌"
        print(f"  {category.value:15} → {actual_type:15} {status}")
    
    print("\nFRONTEND FILTER MAPPING (based on insight_type):")
    print("  📊 Performance  → success_pattern insights")
    print("  ⭐ Optimizations → optimization insights (strategy, operational)")
    print("  📚 Learnings    → failure_lesson, constraint, risk insights")
    print("  🔍 Discoveries  → discovery, opportunity insights")


if __name__ == "__main__":
    try:
        # Run classification tests
        success = test_classification()
        
        # Run mapping tests
        test_insight_type_mapping()
        
        if success:
            print("\n✅ All tests passed! Classification system is working correctly.")
            sys.exit(0)
        else:
            print("\n⚠️ Some tests failed. Please review the classification logic.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)