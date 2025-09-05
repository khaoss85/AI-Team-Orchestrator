#!/usr/bin/env python3
"""
Update existing insight categories in database using AI classifier
One-time migration script to fix miscategorized insights
"""

import sys
import os
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

from database import get_supabase_client
from services.ai_insight_classifier import insight_classifier
from unified_insight import InsightCategory
import json


def update_insight_categories():
    """Update database insights with proper categories"""
    
    print("=" * 80)
    print("UPDATING INSIGHT CATEGORIES IN DATABASE")
    print("=" * 80)
    
    client = get_supabase_client()
    
    # Fetch all insights where insight_type is 'discovery' but could be something else
    print("\n1. Fetching insights with 'discovery' type that may need updating...")
    response = client.table('workspace_insights').select('*').eq(
        'insight_type', 'discovery'
    ).execute()
    
    insights = response.data
    print(f"Found {len(insights)} insights to update")
    
    if not insights:
        print("No insights to update!")
        return
    
    # Classify and update each insight
    updated_count = 0
    category_distribution = {}
    
    print("\n2. Classifying and updating insights...")
    print("-" * 40)
    
    for idx, insight in enumerate(insights, 1):
        # Classify based on content
        category = insight_classifier.classify_insight(
            insight['content'],
            insight['title']
        )
        
        # Get proper insight_type for database
        insight_type = insight_classifier.get_insight_type_from_category(category)
        
        # Track distribution
        category_distribution[category.value] = category_distribution.get(category.value, 0) + 1
        
        # Update in database - only update insight_type to match category
        # Keep existing category if it's already set correctly
        update_data = {
            'insight_type': insight_type
        }
        
        # Also update category if it doesn't match
        if insight.get('insight_category') != category.value:
            update_data['insight_category'] = category.value
        
        try:
            client.table('workspace_insights').update(update_data).eq(
                'id', insight['id']
            ).execute()
            
            updated_count += 1
            
            # Show progress
            if idx <= 5 or idx % 5 == 0:
                print(f"  [{idx:3}/{len(insights)}] Updated: {insight['title'][:50]}...")
                print(f"         Category: {insight.get('insight_category', 'unknown')} → {category.value}")
                print(f"         Type: discovery → {insight_type}")
                
        except Exception as e:
            print(f"  Error updating insight {insight['id']}: {e}")
    
    print(f"\n3. Update Complete!")
    print("-" * 40)
    print(f"Successfully updated {updated_count}/{len(insights)} insights")
    
    print("\n4. New Category Distribution:")
    print("-" * 40)
    for cat, count in sorted(category_distribution.items()):
        percentage = (count / len(insights)) * 100
        print(f"  {cat:15}: {count:2} insights ({percentage:5.1f}%)")
    
    # Map to frontend filters
    print("\n5. Frontend Filter Distribution:")
    print("-" * 40)
    
    filter_counts = {
        'performance': 0,
        'best_practice': 0,
        'learning': 0,
        'discovery': 0
    }
    
    for cat_name, count in category_distribution.items():
        category = InsightCategory(cat_name)
        insight_type = insight_classifier.get_insight_type_from_category(category)
        filter_counts[insight_type] = filter_counts.get(insight_type, 0) + count
    
    for filter_type, count in filter_counts.items():
        if count > 0:
            percentage = (count / len(insights)) * 100
            if filter_type == 'performance':
                icon = '📊'
            elif filter_type == 'best_practice':
                icon = '⭐'
            elif filter_type == 'learning':
                icon = '📚'
            else:
                icon = '🔍'
            print(f"  {icon} {filter_type:15}: {count:2} insights ({percentage:5.1f}%)")
    
    return updated_count > 0


if __name__ == "__main__":
    try:
        success = update_insight_categories()
        
        if success:
            print("\n✅ Categories updated successfully!")
            print("\n📝 Next steps:")
            print("  1. Clear frontend cache or refresh the page")
            print("  2. Check that filter counts are now correct")
            print("  3. Verify insights appear in appropriate categories")
        else:
            print("\n⚠️ No updates were made")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()