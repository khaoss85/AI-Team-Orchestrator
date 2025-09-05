#!/usr/bin/env python3
"""
Test Frontend Filter Mapping for Insights
Shows how the frontend filters should map to the classified insights
"""

import sys
import os
import httpx
import asyncio
import json
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

from services.ai_insight_classifier import insight_classifier
from unified_insight import InsightCategory


async def test_frontend_filters():
    """Test how frontend filters should work with classified insights"""
    
    workspace_id = 'e29a33af-b473-4d9c-b983-f5c1aa70a830'
    
    print("=" * 80)
    print("FRONTEND FILTER MAPPING TEST")
    print("=" * 80)
    
    # Fetch insights from API
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f'http://localhost:8000/api/insights/{workspace_id}?force_refresh=true'
        )
        
        if response.status_code != 200:
            print(f"Error fetching insights: {response.status_code}")
            return
        
        data = response.json()
    
    insights = data['insights']
    print(f"\nTotal Insights: {len(insights)}")
    
    # Map insights to frontend filter categories based on the insight category
    # The frontend typically shows: All, Best Practices, Learnings, Discoveries
    
    filter_mapping = {
        'all': [],
        'best_practices': [],  # Strategy, Operational, Optimization
        'learnings': [],       # Constraint, Risk, Failure lessons
        'discoveries': [],     # Discovery, Opportunity
        'performance': []      # Performance metrics
    }
    
    for insight in insights:
        category = insight.get('category', 'general')
        
        # Add to 'all' filter
        filter_mapping['all'].append(insight)
        
        # Map to specific filters based on category
        if category == 'performance':
            filter_mapping['performance'].append(insight)
        elif category in ['strategy', 'operational', 'optimization']:
            filter_mapping['best_practices'].append(insight)
        elif category in ['constraint', 'risk']:
            filter_mapping['learnings'].append(insight)
        elif category in ['discovery', 'opportunity', 'general']:
            filter_mapping['discoveries'].append(insight)
    
    # Display filter counts and samples
    print("\n" + "=" * 80)
    print("FRONTEND FILTER DISTRIBUTION:")
    print("-" * 80)
    
    for filter_name, insights_list in filter_mapping.items():
        if filter_name == 'all':
            icon = '📋'
            label = 'All Insights'
        elif filter_name == 'performance':
            icon = '📊'
            label = 'Performance'
        elif filter_name == 'best_practices':
            icon = '⭐'
            label = 'Best Practices'
        elif filter_name == 'learnings':
            icon = '📚'
            label = 'Learnings'
        elif filter_name == 'discoveries':
            icon = '🔍'
            label = 'Discoveries'
        else:
            icon = '❓'
            label = filter_name
        
        count = len(insights_list)
        print(f"\n{icon} {label}: {count} insights")
        
        if filter_name != 'all' and insights_list:
            print("  Sample insights:")
            for i, insight in enumerate(insights_list[:2], 1):
                print(f"    {i}. {insight['title'][:60]}...")
    
    # Show category distribution
    print("\n" + "=" * 80)
    print("ACTUAL CATEGORY DISTRIBUTION:")
    print("-" * 80)
    
    category_counts = {}
    for insight in insights:
        cat = insight.get('category', 'unknown')
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    for cat, count in sorted(category_counts.items()):
        percentage = (count / len(insights)) * 100
        print(f"  {cat:15}: {count:2} insights ({percentage:5.1f}%)")
    
    # Show how the database insight_type maps to filters
    print("\n" + "=" * 80)
    print("DATABASE INSIGHT_TYPE TO FRONTEND FILTER MAPPING:")
    print("-" * 80)
    
    type_to_filter = {
        'success_pattern': 'Performance metrics (📊)',
        'optimization': 'Best Practices (⭐)',
        'failure_lesson': 'Learnings (📚)',
        'constraint': 'Learnings (📚)',
        'risk': 'Learnings (📚)',
        'discovery': 'Discoveries (🔍)',
        'opportunity': 'Discoveries (🔍)'
    }
    
    for db_type, frontend_filter in type_to_filter.items():
        print(f"  {db_type:15} → {frontend_filter}")
    
    # Success criteria
    print("\n" + "=" * 80)
    print("✅ SUCCESS CRITERIA:")
    print("-" * 80)
    
    success_checks = [
        ("Multiple categories detected", len(category_counts) > 1),
        ("Performance insights present", filter_mapping['performance']),
        ("Best practices present", filter_mapping['best_practices']),
        ("No 'general' category dominance", category_counts.get('general', 0) < len(insights) / 2)
    ]
    
    all_success = True
    for check_name, check_result in success_checks:
        status = "✅" if check_result else "❌"
        print(f"  {status} {check_name}")
        all_success = all_success and bool(check_result)
    
    if all_success:
        print("\n🎉 All success criteria met! Classification system is working correctly.")
    else:
        print("\n⚠️ Some criteria not met. Review the classification logic.")
    
    return all_success


if __name__ == "__main__":
    try:
        success = asyncio.run(test_frontend_filters())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)