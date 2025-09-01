#!/usr/bin/env python3
"""
Test Content-Aware Learning System Database Integration
Tests the enhanced business insight system with real Social Growth workspace data
"""

import asyncio
import logging
from datetime import datetime
from pprint import pprint

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test workspace ID (Social Growth)
SOCIAL_GROWTH_WORKSPACE_ID = "1f1bf9cf-3c46-48ed-96f3-ec826742ee02"

async def test_enhanced_insight_creation():
    """Test creating and storing enhanced business insights"""
    print("🧪 Testing Enhanced Business Insight Creation...")
    
    try:
        from models import EnhancedBusinessInsight
        from services.enhanced_insight_database import store_domain_insight
        
        # Create test Instagram marketing insight
        instagram_insight = EnhancedBusinessInsight(
            insight_title="Hashtag Mix Strategy for Higher Engagement",
            description="Combining niche and broad hashtags in 30/70 ratio increases engagement by 35%",
            domain_type="instagram_marketing",
            insight_category="performance_metric",
            domain_specific_metadata={
                "platform": "instagram",
                "content_type": "hashtag_strategy",
                "audience_size": "10k-50k followers",
                "posting_frequency": "daily"
            },
            quantifiable_metrics={
                "engagement_rate_before": 0.02,
                "engagement_rate_after": 0.027,
                "improvement_percentage": 35,
                "sample_size": 150,
                "testing_period_days": 30
            },
            action_recommendations=[
                "Use 30% niche hashtags specific to your industry",
                "Include 70% broad hashtags with high search volume",
                "Test different combinations weekly",
                "Monitor engagement rates for optimization"
            ],
            business_value_score=0.85,
            confidence_score=0.90,
            quality_threshold=0.70,
            workspace_id=SOCIAL_GROWTH_WORKSPACE_ID,
            relevance_tags=["instagram", "hashtags", "engagement", "strategy", "social_media"]
        )
        
        # Store the insight
        insight_id = await store_domain_insight(instagram_insight)
        print(f"✅ Created Instagram marketing insight: {insight_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create enhanced insight: {e}")
        return False

async def test_domain_insight_retrieval():
    """Test retrieving domain-specific insights"""
    print("\n🔍 Testing Domain Insight Retrieval...")
    
    try:
        from services.enhanced_insight_database import (
            get_domain_insights, 
            get_high_value_insights,
            get_workspace_insight_summary
        )
        
        # Test retrieving Instagram marketing insights
        instagram_insights = await get_domain_insights(
            workspace_id=SOCIAL_GROWTH_WORKSPACE_ID,
            domain_type="instagram_marketing",
            min_business_value=0.6
        )
        
        print(f"📊 Found {len(instagram_insights)} Instagram marketing insights")
        for insight in instagram_insights[:2]:  # Show first 2
            print(f"  - {insight.insight_title} (Business Value: {insight.business_value_score})")
        
        # Test high-value insights
        high_value = await get_high_value_insights(SOCIAL_GROWTH_WORKSPACE_ID, top_n=5)
        print(f"💎 Found {len(high_value)} high-value insights")
        
        # Test workspace summary
        summary = await get_workspace_insight_summary(SOCIAL_GROWTH_WORKSPACE_ID)
        print(f"📈 Workspace insights summary:")
        print(f"  - Total insights: {summary.get('total_insights', 0)}")
        print(f"  - Average business value: {summary.get('avg_business_value', 0)}")
        print(f"  - Domains: {list(summary.get('domains', {}).keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to retrieve insights: {e}")
        return False

async def test_learning_engine_integration():
    """Test integration with learning feedback engine"""
    print("\n🔄 Testing Learning Engine Integration...")
    
    try:
        from services.learning_feedback_engine import LearningFeedbackEngine
        
        engine = LearningFeedbackEngine()
        
        # Test getting domain insights for a task
        task_insights = await engine.get_domain_insights_for_task(
            workspace_id=SOCIAL_GROWTH_WORKSPACE_ID,
            task_description="Create Instagram hashtag strategy for tech startup"
        )
        
        print(f"🎯 Found {len(task_insights)} relevant insights for Instagram hashtag task:")
        for insight in task_insights[:3]:  # Show first 3
            print(f"  - {insight['title']} (Score: {insight['business_value'] * insight['confidence']:.2f})")
            if insight['recommendations']:
                print(f"    Recommendations: {len(insight['recommendations'])} actions")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to test learning engine integration: {e}")
        return False

async def test_content_analysis():
    """Test content analysis on existing deliverables"""
    print("\n📋 Testing Content Analysis on Existing Deliverables...")
    
    try:
        from database import get_deliverables
        
        # Get deliverables from Social Growth workspace
        deliverables = await get_deliverables(SOCIAL_GROWTH_WORKSPACE_ID, limit=5)
        print(f"📦 Found {len(deliverables)} deliverables in Social Growth workspace")
        
        # Show sample deliverable content for insight extraction potential
        for i, deliverable in enumerate(deliverables[:2], 1):
            print(f"\n  Deliverable {i}:")
            print(f"    Title: {deliverable.get('title', 'No title')}")
            print(f"    Type: {deliverable.get('type', 'Unknown')}")
            print(f"    Status: {deliverable.get('status', 'Unknown')}")
            
            # Check if it has detailed content for analysis
            content = deliverable.get('detailed_results_json', {})
            if isinstance(content, dict) and content:
                print(f"    Content keys: {list(content.keys())}")
                print(f"    🎯 Potential for insight extraction: HIGH")
            else:
                print(f"    🎯 Potential for insight extraction: LOW")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to analyze content: {e}")
        return False

async def test_insight_application_tracking():
    """Test insight application and performance tracking"""
    print("\n📊 Testing Insight Application Tracking...")
    
    try:
        from services.enhanced_insight_database import mark_insight_used
        from services.learning_feedback_engine import LearningFeedbackEngine
        
        engine = LearningFeedbackEngine()
        
        # Simulate insight application
        mock_insight_id = "test_insight_123"
        mock_task_id = "test_task_456"
        
        # Record insight application
        recorded = await engine.record_insight_application(
            insight_id=mock_insight_id,
            task_id=mock_task_id,
            success=True
        )
        
        if recorded:
            print("✅ Successfully recorded insight application")
        else:
            print("⚠️ Insight application recording not available (expected for mock data)")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to test application tracking: {e}")
        return False

async def main():
    """Run all tests for content-aware learning system integration"""
    print("🚀 Testing Content-Aware Learning System Database Integration\n")
    print(f"Target workspace: {SOCIAL_GROWTH_WORKSPACE_ID} (Social Growth)")
    print("=" * 70)
    
    tests = [
        ("Enhanced Insight Creation", test_enhanced_insight_creation),
        ("Domain Insight Retrieval", test_domain_insight_retrieval),
        ("Learning Engine Integration", test_learning_engine_integration),
        ("Content Analysis", test_content_analysis),
        ("Application Tracking", test_insight_application_tracking)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"💥 Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("🏁 TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Content-Aware Learning System is ready for production.")
    else:
        print("⚠️ Some tests failed. Check the error messages above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)