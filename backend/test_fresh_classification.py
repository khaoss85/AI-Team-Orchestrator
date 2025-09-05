#!/usr/bin/env python3
"""
Test fresh AI insight classification without cached database entries
"""

import sys
import os
import asyncio
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

from services.unified_insights_orchestrator import unified_insights_orchestrator
import json


async def test_fresh_classification():
    """Test classification of fresh AI insights"""
    
    workspace_id = 'e29a33af-b473-4d9c-b983-f5c1aa70a830'
    
    print("=" * 80)
    print("TESTING FRESH AI INSIGHT CLASSIFICATION")
    print("=" * 80)
    
    # Fetch AI insights directly
    print("\n1. Fetching AI insights directly...")
    ai_insights = await unified_insights_orchestrator._fetch_ai_insights(workspace_id)
    
    print(f"Found {len(ai_insights)} AI insights")
    
    # Count categories
    category_counts = {}
    insight_samples = {}
    
    for insight in ai_insights:
        cat = insight.category.value
        category_counts[cat] = category_counts.get(cat, 0) + 1
        
        # Store sample for each category
        if cat not in insight_samples:
            insight_samples[cat] = {
                'title': insight.title,
                'content': insight.content,
                'confidence': insight.confidence_score,
                'metric_name': insight.metric_name,
                'metric_value': insight.metric_value
            }
    
    print("\n2. Category Distribution:")
    print("-" * 40)
    for cat, count in sorted(category_counts.items()):
        percentage = (count / len(ai_insights)) * 100
        print(f"  {cat:15}: {count:2} insights ({percentage:5.1f}%)")
    
    print("\n3. Sample Insights by Category:")
    print("-" * 40)
    for cat, sample in sorted(insight_samples.items()):
        print(f"\n{cat.upper()}:")
        print(f"  Title: {sample['title'][:60]}...")
        if sample['metric_name']:
            print(f"  Metric: {sample['metric_name']} = {sample['metric_value']}")
    
    # Check database insight type mapping
    print("\n4. Database Insight Type Mapping:")
    print("-" * 40)
    
    type_counts = {}
    for insight in ai_insights:
        insight_type = unified_insights_orchestrator.classifier.get_insight_type_from_category(insight.category)
        type_counts[insight_type] = type_counts.get(insight_type, 0) + 1
    
    print("Frontend Filter Distribution:")
    for insight_type, count in sorted(type_counts.items()):
        percentage = (count / len(ai_insights)) * 100
        if insight_type == 'performance':
            icon = '📊'
            label = 'Performance'
        elif insight_type == 'best_practice':
            icon = '⭐'
            label = 'Best Practices'
        elif insight_type == 'learning':
            icon = '📚'
            label = 'Learnings'
        elif insight_type == 'discovery':
            icon = '🔍'
            label = 'Discoveries'
        else:
            icon = '❓'
            label = insight_type
        
        print(f"  {icon} {label:15}: {count:2} insights ({percentage:5.1f}%)")
    
    # Test unified endpoint
    print("\n5. Testing Unified Endpoint (with force refresh):")
    print("-" * 40)
    
    response = await unified_insights_orchestrator.get_unified_insights(
        workspace_id=workspace_id,
        force_refresh=True
    )
    
    print(f"Total insights from unified endpoint: {response.total}")
    print(f"Cache status: {response.cache_status}")
    print(f"Source systems: {', '.join(response.source_systems)}")
    
    # Count categories in unified response
    unified_cats = {}
    for insight in response.insights:
        cat = insight.category.value
        unified_cats[cat] = unified_cats.get(cat, 0) + 1
    
    print("\nUnified Category Distribution:")
    for cat, count in sorted(unified_cats.items()):
        print(f"  {cat:15}: {count:2} insights")
    
    return len(ai_insights) > 0 and len(category_counts) > 1


if __name__ == "__main__":
    try:
        success = asyncio.run(test_fresh_classification())
        
        if success:
            print("\n✅ Fresh classification is working! Multiple categories detected.")
        else:
            print("\n⚠️ Classification may need adjustment.")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()