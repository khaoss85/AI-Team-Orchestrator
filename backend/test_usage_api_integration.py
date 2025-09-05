#!/usr/bin/env python3
"""
Test script for OpenAI Usage API v1 Integration
Tests all components of the new real cost tracking system
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

async def test_usage_api_client():
    """Test the OpenAI Usage API Client"""
    print("\n" + "="*60)
    print("🔌 TESTING OPENAI USAGE API CLIENT")
    print("="*60)
    
    try:
        from services.openai_usage_api_client import get_usage_client
        client = get_usage_client()
        
        # Test 1: Today's usage
        print("\n📊 Test 1: Fetching today's usage...")
        today_usage = await client.get_today_usage()
        print(f"✅ Today's Usage:")
        print(f"   Total Cost: ${today_usage.total_cost:.4f}")
        print(f"   Total Tokens: {today_usage.total_tokens:,}")
        print(f"   Total Requests: {today_usage.total_requests}")
        if today_usage.hourly_breakdown:
            print(f"   Hourly data points: {len(today_usage.hourly_breakdown)}")
        
        # Test 2: Current month usage
        print("\n📊 Test 2: Fetching current month usage...")
        month_usage = await client.get_current_month_usage()
        print(f"✅ Current Month Usage:")
        print(f"   Total Cost: ${month_usage.total_cost:.2f}")
        print(f"   Total Tokens: {month_usage.total_tokens:,}")
        print(f"   Total Requests: {month_usage.total_requests}")
        print(f"   Days tracked: {len(month_usage.daily_breakdown)}")
        
        # Test 3: Budget status
        print("\n📊 Test 3: Checking budget status...")
        budget_status = await client.check_budget_status()
        print(f"✅ Budget Status:")
        print(f"   Status: {budget_status['status'].upper()}")
        print(f"   Monthly Budget: ${budget_status['monthly_budget']:.2f}")
        print(f"   Current Spend: ${budget_status['current_spend']:.2f}")
        print(f"   Budget Used: {budget_status['budget_used_percent']:.1f}%")
        print(f"   Projected Monthly: ${budget_status['projected_monthly']:.2f}")
        print(f"   Days Remaining: {budget_status['days_remaining']}")
        
        if budget_status['projected_overage'] > 0:
            print(f"   ⚠️ Projected Overage: ${budget_status['projected_overage']:.2f}")
        else:
            print(f"   ✅ Within budget (${budget_status['monthly_budget'] - budget_status['projected_monthly']:.2f} projected surplus)")
        
        # Test 4: Model comparison
        print("\n📊 Test 4: Comparing model costs...")
        comparison = await client.get_model_comparison(days=7)
        print(f"✅ Model Comparison (Last 7 Days):")
        for model, data in sorted(comparison.items(), key=lambda x: x[1]['total_cost'], reverse=True):
            print(f"   {model}:")
            print(f"      Total Cost: ${data['total_cost']:.2f} ({data['cost_percentage']:.1f}%)")
            print(f"      Total Requests: {data['total_requests']}")
            print(f"      Cost per 1K tokens: ${data['cost_per_1k_tokens']:.4f}")
        
        # Test 5: Cost trend
        print("\n📊 Test 5: Analyzing cost trends...")
        trend = await client.get_cost_trend(days=7)
        print(f"✅ Cost Trend (Last 7 Days):")
        print(f"   Total Cost: ${trend['total_cost']:.2f}")
        print(f"   Average Daily: ${trend['avg_daily_cost']:.2f}")
        print(f"   Data Points: {len(trend['daily'])}")
        
        # Show last 3 days
        if trend['daily']:
            print("   Recent days:")
            for day_data in trend['daily'][-3:]:
                print(f"      {day_data['date']}: ${day_data['cost']:.2f} ({day_data['requests']} requests)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Usage API Client: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_cost_intelligence():
    """Test the enhanced AI Cost Intelligence"""
    print("\n" + "="*60)
    print("🧠 TESTING AI COST INTELLIGENCE")
    print("="*60)
    
    try:
        from services.ai_cost_intelligence import get_cost_intelligence
        
        workspace_id = "test_workspace"
        cost_intel = get_cost_intelligence(workspace_id)
        
        # Test 1: Update with real costs
        print("\n🧠 Test 1: Updating with real cost data...")
        await cost_intel.update_real_costs()
        print(f"✅ Real costs updated")
        print(f"   Calibration ratio: {cost_intel.real_vs_estimated_ratio:.2f}")
        
        # Test 2: Analyze sample API calls
        print("\n🧠 Test 2: Analyzing API calls for inefficiencies...")
        
        # Simulate duplicate calls
        test_call = {
            "model": "gpt-4",
            "tokens_used": 500,
            "completion_tokens": 100,
            "api_method": "chat.completions",
            "success": True,
            "messages": [{"role": "user", "content": "Test prompt for duplicate detection"}]
        }
        
        # First call
        alerts1 = await cost_intel.analyze_api_call(test_call)
        print(f"   First call: {len(alerts1)} alerts")
        
        # Duplicate calls
        alerts2 = await cost_intel.analyze_api_call(test_call)
        alerts3 = await cost_intel.analyze_api_call(test_call)
        alerts4 = await cost_intel.analyze_api_call(test_call)
        
        print(f"   After duplicates: {len(alerts4)} alerts")
        
        # Test 3: Get cost summary
        print("\n🧠 Test 3: Getting cost intelligence summary...")
        summary = cost_intel.get_cost_summary()
        print(f"✅ Cost Intelligence Summary:")
        print(f"   Efficiency Score: {summary['efficiency_score']}/100")
        print(f"   Duplicate Rate: {summary['duplicate_rate_percent']:.1f}%")
        print(f"   Unique Patterns: {summary['unique_call_patterns']}")
        print(f"   Potential Daily Savings: ${summary['potential_daily_savings_usd']:.2f}")
        print(f"   Real Data Calibrated: {summary.get('real_data_calibrated', False)}")
        
        # Test 4: Get recent alerts
        print("\n🧠 Test 4: Retrieving optimization alerts...")
        alerts = cost_intel.get_recent_alerts(limit=5)
        if alerts:
            print(f"✅ Recent Alerts ({len(alerts)}):")
            for alert in alerts:
                print(f"   [{alert.severity.value.upper()}] {alert.title}")
                print(f"      Savings: ${alert.potential_savings:.2f}/day")
                print(f"      Recommendation: {alert.recommendation}")
        else:
            print("   No alerts generated yet")
        
        # Test 5: Real vs Estimated comparison
        print("\n🧠 Test 5: Comparing real vs estimated costs...")
        comparison = await cost_intel.get_real_vs_estimated_comparison()
        print(f"✅ Real vs Estimated:")
        print(f"   Real Cost Today: ${comparison['real_cost_today']:.4f}")
        print(f"   Estimated Cost Today: ${comparison['estimated_cost_today']:.4f}")
        print(f"   Accuracy: {comparison['accuracy_percent']:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Cost Intelligence: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_quota_tracker():
    """Test the enhanced Quota Tracker with real data"""
    print("\n" + "="*60)
    print("📊 TESTING ENHANCED QUOTA TRACKER")
    print("="*60)
    
    try:
        from services.openai_quota_tracker import quota_manager
        
        workspace_id = "test_workspace"
        tracker = quota_manager.get_tracker(workspace_id)
        
        # Test 1: Fetch real usage data
        print("\n📊 Test 1: Fetching real usage data for quota tracker...")
        real_data = await tracker.fetch_real_usage_data()
        
        if real_data:
            print(f"✅ Real Usage Data Fetched:")
            print(f"   Today's Cost: ${real_data['today']['total_cost']:.4f}")
            print(f"   Today's Tokens: {real_data['today']['total_tokens']:,}")
            print(f"   Budget Status: {real_data['budget']['status'].upper()}")
            print(f"   Budget Used: {real_data['budget']['budget_used_percent']:.1f}%")
        else:
            print("⚠️ Could not fetch real usage data (API key may be missing)")
        
        # Test 2: Get enhanced status
        print("\n📊 Test 2: Getting enhanced status with real data...")
        enhanced = tracker.get_enhanced_status_data()
        print(f"✅ Enhanced Status:")
        
        if 'real_usage' in enhanced:
            print("   Real usage data integrated ✅")
        else:
            print("   Real usage data not available ⚠️")
            
        print(f"   Models tracked: {enhanced['enhanced_tracking']['total_unique_models']}")
        print(f"   API methods tracked: {enhanced['enhanced_tracking']['total_unique_methods']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Quota Tracker: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_endpoints():
    """Test the new Usage Analytics API endpoints"""
    print("\n" + "="*60)
    print("🌐 TESTING USAGE ANALYTICS API ENDPOINTS")
    print("="*60)
    
    try:
        import httpx
        
        base_url = "http://localhost:8000/api"
        workspace_id = "test_workspace"
        
        # Note: These tests require the server to be running
        print("\n⚠️ Note: API endpoint tests require the server to be running")
        print("  Start the server with: python backend/main.py")
        
        async with httpx.AsyncClient() as client:
            # Test 1: Current month endpoint
            print("\n🌐 Test 1: Testing /usage/current-month endpoint...")
            try:
                response = await client.get(f"{base_url}/usage/current-month", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        print(f"✅ Current month endpoint working")
                        print(f"   Total cost: ${data['data']['total_cost']:.2f}")
                else:
                    print(f"⚠️ Endpoint returned status {response.status_code}")
            except httpx.ConnectError:
                print("⚠️ Could not connect to server (is it running?)")
            except Exception as e:
                print(f"⚠️ Error: {e}")
            
            # Test 2: Dashboard endpoint
            print("\n🌐 Test 2: Testing /usage/dashboard endpoint...")
            try:
                response = await client.get(f"{base_url}/usage/dashboard/{workspace_id}", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        print(f"✅ Dashboard endpoint working")
                        print(f"   Today's cost: ${data['today']['cost']:.4f}")
                        print(f"   Month's cost: ${data['month']['cost']:.2f}")
                        print(f"   Efficiency score: {data['intelligence']['efficiency_score']}/100")
                else:
                    print(f"⚠️ Endpoint returned status {response.status_code}")
            except httpx.ConnectError:
                print("⚠️ Could not connect to server")
            except Exception as e:
                print(f"⚠️ Error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing API endpoints: {e}")
        return False

async def main():
    """Run all integration tests"""
    print("\n" + "="*60)
    print("🚀 OPENAI USAGE API V1 INTEGRATION TEST SUITE")
    print("="*60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check for API key
    if not os.getenv('OPENAI_API_KEY'):
        print("\n⚠️ WARNING: OPENAI_API_KEY not found in environment")
        print("  Some tests may fail without a valid API key")
        print("  Set it in backend/.env file")
    
    results = []
    
    # Run tests
    print("\n🧪 Running integration tests...")
    
    # Test 1: Usage API Client
    results.append(("Usage API Client", await test_usage_api_client()))
    
    # Test 2: Cost Intelligence
    results.append(("Cost Intelligence", await test_cost_intelligence()))
    
    # Test 3: Quota Tracker
    results.append(("Quota Tracker", await test_quota_tracker()))
    
    # Test 4: API Endpoints (optional, requires server)
    # results.append(("API Endpoints", await test_api_endpoints()))
    
    # Summary
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The OpenAI Usage API integration is working correctly.")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please check the errors above.")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())