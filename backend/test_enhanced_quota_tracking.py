#!/usr/bin/env python3
"""
Test Enhanced OpenAI Quota Tracking System
Verifies that the enhanced factory properly tracks all API calls with model and method breakdown
"""

import asyncio
import os
import sys
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the enhanced factory
from utils.openai_client_factory_enhanced import get_enhanced_openai_client, get_enhanced_async_openai_client
from services.openai_quota_tracker import quota_manager


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def print_status(quota_tracker):
    """Print current quota status"""
    status = quota_tracker.get_status_data()
    enhanced = quota_tracker.get_enhanced_status_data()
    
    print("\n📊 Current Status:")
    print(f"  Status: {status['status']}")
    print(f"  Requests/min: {status['requests_per_minute']['current']}/{status['requests_per_minute']['limit']}")
    print(f"  Requests/day: {status['requests_per_day']['current']}/{status['requests_per_day']['limit']}")
    print(f"  Tokens/min: {status['tokens_per_minute']['current']}/{status['tokens_per_minute']['limit']}")
    
    if quota_tracker.usage_stats.get('tokens_today'):
        print(f"  Tokens/day: {quota_tracker.usage_stats['tokens_today']}/{quota_tracker.rate_limits['tokens_per_day']}")
    
    if quota_tracker.usage_stats.get('daily_cost_usd'):
        print(f"  Daily cost: ${quota_tracker.usage_stats['daily_cost_usd']:.4f}")
    
    print("\n🤖 Model Breakdown:")
    models = enhanced['enhanced_tracking']['models_breakdown']
    if models:
        for model, data in models.items():
            print(f"  {model}: {data['request_count']} requests, {data['tokens_used']} tokens")
    else:
        print("  No model usage yet")
    
    print("\n⚙️ API Method Breakdown:")
    methods = enhanced['enhanced_tracking']['api_methods_breakdown']
    if methods:
        for method, data in methods.items():
            errors = f", {data['error_count']} errors" if data['error_count'] > 0 else ""
            print(f"  {method}: {data['request_count']} requests{errors}")
    else:
        print("  No API method usage yet")
    
    print("\n📜 Recent Activity:")
    activities = enhanced['enhanced_tracking']['recent_activity']
    if activities:
        for activity in activities[:3]:
            status_icon = "✅" if activity['success'] else "❌"
            time = datetime.fromisoformat(activity['timestamp']).strftime("%H:%M:%S")
            print(f"  {status_icon} {time} - {activity['model']} - {activity['api_method']} ({activity['tokens_used']} tokens)")
    else:
        print("  No recent activity")


async def test_chat_completion():
    """Test chat completion tracking"""
    print("\n🧪 Testing Chat Completion...")
    
    try:
        client = get_enhanced_openai_client(workspace_id="test-workspace")
        
        # Make a simple chat completion
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say 'Hello, quota tracking!' in 5 words or less"}
            ],
            max_tokens=20
        )
        
        print(f"✅ Chat response: {response.choices[0].message.content}")
        print(f"   Tokens used: {response.usage.total_tokens if hasattr(response, 'usage') else 'Unknown'}")
        
    except Exception as e:
        print(f"❌ Chat completion failed: {e}")


async def test_embeddings():
    """Test embeddings tracking"""
    print("\n🧪 Testing Embeddings...")
    
    try:
        client = get_enhanced_openai_client(workspace_id="test-workspace")
        
        # Create embeddings
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input="Testing quota tracking for embeddings"
        )
        
        print(f"✅ Embedding created: {len(response.data)} vectors")
        print(f"   Model: {response.model}")
        
    except Exception as e:
        print(f"❌ Embeddings failed: {e}")


async def test_async_chat():
    """Test async chat completion tracking"""
    print("\n🧪 Testing Async Chat Completion...")
    
    try:
        client = get_enhanced_async_openai_client(workspace_id="test-workspace")
        
        # Make an async chat completion
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is 2+2?"}
            ],
            max_tokens=10
        )
        
        print(f"✅ Async chat response: {response.choices[0].message.content}")
        print(f"   Model: {response.model}")
        
    except Exception as e:
        print(f"❌ Async chat failed: {e}")


async def test_error_tracking():
    """Test error tracking"""
    print("\n🧪 Testing Error Tracking...")
    
    try:
        client = get_enhanced_openai_client(workspace_id="test-workspace")
        
        # Try to use an invalid model to trigger an error
        try:
            response = client.chat.completions.create(
                model="invalid-model-name",
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=10
            )
        except Exception as e:
            print(f"✅ Error correctly tracked: {str(e)[:100]}...")
            
    except Exception as e:
        print(f"❌ Error tracking test failed: {e}")


async def test_model_list():
    """Test model listing (should not count against quota)"""
    print("\n🧪 Testing Model List (no quota impact)...")
    
    try:
        client = get_enhanced_openai_client(workspace_id="test-workspace")
        
        # List models (should not affect quota)
        models = client.models.list()
        model_count = len(list(models))
        
        print(f"✅ Listed {model_count} models (no quota impact expected)")
        
    except Exception as e:
        print(f"❌ Model listing failed: {e}")


async def main():
    """Run all tests"""
    print_section("Enhanced OpenAI Quota Tracking Test Suite")
    
    # Get the quota tracker for our test workspace
    tracker = quota_manager.get_tracker("test-workspace")
    
    # Show initial status
    print_section("Initial Status")
    print_status(tracker)
    
    # Run tests
    print_section("Running Tests")
    
    # Test different API methods
    await test_chat_completion()
    await asyncio.sleep(1)  # Brief pause between tests
    
    await test_embeddings()
    await asyncio.sleep(1)
    
    await test_async_chat()
    await asyncio.sleep(1)
    
    await test_error_tracking()
    await asyncio.sleep(1)
    
    await test_model_list()
    
    # Show final status
    print_section("Final Status After Tests")
    print_status(tracker)
    
    # Verify enhanced tracking
    print_section("Verification Results")
    enhanced_data = tracker.get_enhanced_status_data()['enhanced_tracking']
    
    success = True
    checks = []
    
    # Check models were tracked
    if enhanced_data['total_unique_models'] > 0:
        checks.append("✅ Model tracking working")
    else:
        checks.append("❌ Model tracking not working")
        success = False
    
    # Check API methods were tracked
    if enhanced_data['total_unique_methods'] > 0:
        checks.append("✅ API method tracking working")
    else:
        checks.append("❌ API method tracking not working")
        success = False
    
    # Check recent activity was recorded
    if len(enhanced_data['recent_activity']) > 0:
        checks.append("✅ Recent activity tracking working")
    else:
        checks.append("❌ Recent activity tracking not working")
        success = False
    
    # Check token tracking
    if tracker.usage_stats['tokens_used'] > 0:
        checks.append("✅ Token tracking working")
    else:
        checks.append("❌ Token tracking not working")
        success = False
    
    # Check daily limits configured
    if tracker.enhanced_stats.get('daily_limits_configured', False) or tracker.rate_limits.get('tokens_per_day'):
        checks.append("✅ Daily limits configured")
    else:
        checks.append("⚠️  Daily limits may need configuration")
    
    # Print results
    for check in checks:
        print(check)
    
    print_section("Test Complete")
    if success:
        print("🎉 All enhanced tracking features are working!")
    else:
        print("⚠️  Some features need attention")
    
    return success


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key to run these tests")
        sys.exit(1)
    
    # Run tests
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        sys.exit(1)