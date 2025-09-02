#!/usr/bin/env python3
"""
Test script for Learning-Quality Feedback Loop Integration
Demonstrates the performance-boosting feedback loop in action
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test configuration
TEST_WORKSPACE_ID = "550e8400-e29b-41d4-a716-446655440010"  # Social Growth workspace
TEST_DELIVERABLE_ID = None  # Will be fetched dynamically

async def test_feedback_loop():
    """Test the complete learning-quality feedback loop"""
    
    print("\n" + "="*80)
    print("🔄 LEARNING-QUALITY FEEDBACK LOOP TEST")
    print("="*80 + "\n")
    
    try:
        from services.learning_quality_feedback_loop import learning_quality_feedback_loop
        from services.universal_learning_engine import universal_learning_engine
        from database import get_supabase_client, get_deliverables
        
        # Step 1: Get a deliverable from the workspace
        print("📋 Step 1: Fetching deliverables from workspace...")
        deliverables = await get_deliverables(TEST_WORKSPACE_ID)
        
        if not deliverables:
            print("❌ No deliverables found in workspace")
            return
        
        # Find a high-quality Instagram marketing deliverable
        instagram_deliverable = None
        for d in deliverables:
            if 'instagram' in str(d.get('title', '')).lower() or 'social' in str(d.get('title', '')).lower():
                instagram_deliverable = d
                break
        
        if not instagram_deliverable:
            instagram_deliverable = deliverables[0]  # Fallback to first deliverable
        
        TEST_DELIVERABLE_ID = instagram_deliverable['id']
        print(f"✅ Found deliverable: {instagram_deliverable.get('title', 'Unknown')}")
        print(f"   ID: {TEST_DELIVERABLE_ID}")
        
        # Step 2: Process through feedback loop
        print("\n📊 Step 2: Processing deliverable through feedback loop...")
        result = await learning_quality_feedback_loop.process_deliverable_with_feedback_loop(
            workspace_id=TEST_WORKSPACE_ID,
            deliverable_id=TEST_DELIVERABLE_ID,
            force_learning=True  # Force learning even from lower quality
        )
        
        if result.get('status') == 'success':
            print("✅ Feedback loop processing successful!")
            
            # Display results
            print("\n🎯 RESULTS:")
            print("-" * 40)
            
            # Domain detection
            print(f"📌 Domain Detected: {result.get('domain', 'Unknown')}")
            
            # Quality validation results
            quality = result.get('quality_validation', {})
            print(f"\n📊 Quality Validation:")
            print(f"   - Quality Score: {quality.get('quality_score', 0):.2%}")
            print(f"   - Learning Enhanced: {quality.get('learning_enhanced', False)}")
            print(f"   - Insights Applied: {quality.get('insights_applied', 0)}")
            
            # Learning extraction results
            learning = result.get('learning_extraction', {})
            if learning:
                print(f"\n📚 Learning Extraction:")
                print(f"   - Insights Extracted: {learning.get('insights_extracted', 0)}")
                print(f"   - Insights Stored: {learning.get('insights_stored', 0)}")
                
                # Show extracted insights
                insights = learning.get('insights', [])
                if insights:
                    print(f"\n   🔍 Extracted Insights:")
                    for i, insight in enumerate(insights[:3], 1):
                        print(f"      {i}. {insight.actionable_recommendation}")
                        if insight.metric_name and insight.metric_value:
                            print(f"         Metric: {insight.metric_name} = {insight.metric_value:.1%}")
            
            # Performance metrics
            performance = result.get('performance_metrics', {})
            if performance:
                print(f"\n📈 Performance Metrics:")
                print(f"   - Performance Boost: {performance.get('boost_percentage', 0):.1f}%")
                print(f"   - Quality Trend: {performance.get('trend', 'Unknown')}")
                print(f"   - Domain Multiplier: {performance.get('domain_multiplier', 1.0):.1f}x")
                print(f"   - Overall System Boost: {performance.get('overall_boost', 0):.1f}%")
            
            # Feedback loop status
            print(f"\n🔄 Feedback Loop Status:")
            print(f"   - Mode: {result.get('mode', 'Unknown')}")
            print(f"   - Active: {result.get('feedback_loop_active', False)}")
            print(f"   - Quality Criteria Updated: {result.get('quality_criteria_updated', False)}")
            
        else:
            print(f"❌ Feedback loop processing failed: {result.get('error', 'Unknown error')}")
        
        # Step 3: Test task enhancement
        print("\n" + "="*80)
        print("🚀 Step 3: Testing Task Enhancement with Learnings")
        print("-" * 40)
        
        # Create a test task
        from database import get_supabase_client
        supabase = get_supabase_client()
        
        # Get or create a test task
        tasks_response = supabase.table('tasks')\
            .select('id')\
            .eq('workspace_id', TEST_WORKSPACE_ID)\
            .limit(1)\
            .execute()
        
        if tasks_response.data:
            test_task_id = tasks_response.data[0]['id']
            print(f"✅ Using existing task: {test_task_id}")
            
            # Enhance the task with learnings
            enhancement_result = await learning_quality_feedback_loop.enhance_task_execution_with_learnings(
                workspace_id=TEST_WORKSPACE_ID,
                task_id=test_task_id,
                agent_role="instagram-marketing-specialist"
            )
            
            if enhancement_result.get('enhanced'):
                print(f"✅ Task enhanced successfully!")
                print(f"   - Insights Provided: {enhancement_result.get('insights_provided', 0)}")
                print(f"   - Domain: {enhancement_result.get('domain', 'Unknown')}")
                print(f"   - Expected Quality Boost: {enhancement_result.get('expected_quality_boost', '0%')}")
                
                # Show execution hints
                hints = enhancement_result.get('hints', [])
                if hints:
                    print(f"\n   💡 Execution Hints Provided:")
                    for i, hint in enumerate(hints[:3], 1):
                        print(f"      {i}. {hint.get('recommendation', 'No recommendation')}")
                        if hint.get('metric'):
                            metric = hint['metric']
                            print(f"         Target: {metric.get('name', 'Unknown')} = {metric.get('target', 'N/A')}")
            else:
                print(f"⚠️ Task enhancement not applied: {enhancement_result.get('reason', 'Unknown')}")
        
        # Step 4: Generate performance report
        print("\n" + "="*80)
        print("📈 Step 4: Generating Performance Report")
        print("-" * 40)
        
        report = await learning_quality_feedback_loop.get_performance_report(TEST_WORKSPACE_ID)
        
        print(f"\n🎯 PERFORMANCE REPORT:")
        print(f"   - Overall Performance Boost: {report.get('overall_performance_boost', '0%')}")
        print(f"   - Total Insights Applied: {report.get('insights_applied_total', 0)}")
        print(f"   - Feedback Loop Mode: {report.get('feedback_loop_mode', 'Unknown')}")
        
        # Domain performance
        domain_perf = report.get('domain_performance', {})
        if domain_perf:
            print(f"\n   📊 Domain Performance:")
            for domain, metrics in domain_perf.items():
                print(f"      • {domain}:")
                print(f"        - Quality: {metrics.get('current_quality', 0):.2f}")
                print(f"        - Boost: {metrics.get('boost_percentage', 0):.1f}%")
                print(f"        - Trend: {metrics.get('trend', 'Unknown')}")
        
        # Top insights
        top_insights = report.get('top_insights', [])
        if top_insights:
            print(f"\n   🏆 Top Performing Insights:")
            for i, insight in enumerate(top_insights[:3], 1):
                print(f"      {i}. {insight.get('learning', 'No learning')}")
                print(f"         Domain: {insight.get('domain', 'Unknown')} | Confidence: {insight.get('confidence', 0):.2f}")
        
        # Recommendations
        recommendations = report.get('recommendations', [])
        if recommendations:
            print(f"\n   💡 Recommendations:")
            for rec in recommendations:
                print(f"      • {rec}")
        
        print("\n" + "="*80)
        print("✅ FEEDBACK LOOP TEST COMPLETE!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

async def test_api_endpoints():
    """Test the API endpoints for the feedback loop"""
    import aiohttp
    
    print("\n" + "="*80)
    print("🌐 TESTING API ENDPOINTS")
    print("="*80 + "\n")
    
    base_url = "http://localhost:8000/api/learning-feedback"
    
    async with aiohttp.ClientSession() as session:
        try:
            # Test performance report endpoint
            print("📊 Testing performance report endpoint...")
            async with session.get(f"{base_url}/performance-report/{TEST_WORKSPACE_ID}") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Performance report retrieved successfully")
                    print(f"   Overall boost: {data.get('overall_performance_boost', '0%')}")
                else:
                    print(f"❌ Failed to get performance report: {response.status}")
            
            # Test domain insights endpoint
            print("\n📚 Testing domain insights endpoint...")
            async with session.get(
                f"{base_url}/domain-insights/{TEST_WORKSPACE_ID}",
                params={"domain": "instagram_marketing"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Domain insights retrieved successfully")
                    print(f"   Total learnings: {data.get('total_learnings', 0)}")
                else:
                    print(f"❌ Failed to get domain insights: {response.status}")
            
            # Test feedback metrics endpoint
            print("\n📈 Testing feedback metrics endpoint...")
            async with session.get(
                f"{base_url}/feedback-metrics/{TEST_WORKSPACE_ID}",
                params={"limit": 5}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    summary = data.get('summary', {})
                    print(f"✅ Feedback metrics retrieved successfully")
                    print(f"   Average quality impact: {summary.get('average_quality_impact', 0):.2f}")
                    print(f"   Average performance boost: {summary.get('average_performance_boost', 0):.1f}%")
                else:
                    print(f"❌ Failed to get feedback metrics: {response.status}")
            
        except aiohttp.ClientError as e:
            print(f"❌ API test failed: {e}")
            print("   Make sure the backend server is running on port 8000")

async def main():
    """Main test function"""
    print("\n" + "🚀" * 40)
    print("LEARNING-QUALITY FEEDBACK LOOP INTEGRATION TEST")
    print("Performance Boost System Demonstration")
    print("🚀" * 40 + "\n")
    
    # Run the feedback loop test
    await test_feedback_loop()
    
    # Test API endpoints if server is running
    print("\nTesting API endpoints...")
    try:
        await test_api_endpoints()
    except Exception as e:
        print(f"⚠️ API tests skipped (server might not be running): {e}")
    
    print("\n✨ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())