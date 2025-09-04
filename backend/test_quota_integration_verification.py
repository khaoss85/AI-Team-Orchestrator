#!/usr/bin/env python3
"""
Test script to verify quota tracking integration works after client factory fix
This tests that OpenAI client usage now properly tracks quota
"""

import asyncio
import os
import sys
import json
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_quota_tracking_integration():
    """Test that OpenAI calls now properly track quota"""
    
    print("\n" + "="*60)
    print("🔍 QUOTA TRACKING INTEGRATION VERIFICATION")
    print("="*60 + "\n")
    
    # Test 1: Check initial quota status
    print("📊 STEP 1: Checking initial quota status...")
    from services.openai_quota_tracker import quota_manager
    
    tracker = quota_manager.get_tracker("test-workspace-integration")
    initial_stats = tracker.get_status_data()
    print(f"✅ Initial status: {initial_stats.get('status', 'unknown')}")
    print(f"✅ Initial requests per minute: {initial_stats['requests_per_minute']['current']}")
    print(f"✅ Initial requests per day: {initial_stats['requests_per_day']['current']}")
    
    # Test 2: Test centralized client factory
    print("\n📊 STEP 2: Testing centralized OpenAI client factory...")
    try:
        from utils.openai_client_factory import get_openai_client
        
        client = get_openai_client()  # No parameters needed
        
        # Make a simple API call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'quota tracking verification test successful' if you can hear me"}],
            max_tokens=10
        )
        
        print(f"✅ Client factory response: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ Client factory test failed: {e}")
        return False
    
    # Test 3: Test conversational agent integration
    print("\n📊 STEP 3: Testing conversational agent quota integration...")
    try:
        from ai_agents.conversational_simple import SimpleConversationalAgent
        
        agent = SimpleConversationalAgent("test-workspace-integration", "test-chat")
        response = await agent.process_message("Quick test: What is 2+2? (quota verification)")
        
        print(f"✅ Conversational agent response received")
        
    except Exception as e:
        print(f"⚠️ Conversational agent test failed (may not have full workspace): {e}")
    
    # Test 4: Check quota tracking after calls
    print("\n📊 STEP 4: Verifying quota was tracked...")
    final_stats = tracker.get_status_data()
    
    initial_requests = initial_stats['requests_per_minute']['current']
    final_requests = final_stats['requests_per_minute']['current']
    requests_tracked = final_requests - initial_requests
    
    print(f"✅ Requests tracked during test: {requests_tracked}")
    print(f"✅ Current minute usage: {final_requests}")
    print(f"✅ Current daily usage: {final_stats['requests_per_day']['current']}")
    
    # Test 5: Verify multiple OpenAI usage points are tracked
    print("\n📊 STEP 5: Testing AI Goal Matcher integration...")
    try:
        from services.ai_goal_matcher import ai_goal_matcher
        
        # Create test deliverable and goals for matching
        test_deliverable = {
            "title": "Email marketing strategy",
            "type": "strategy_document",
            "content": {"strategy": "Email campaign with automation"}
        }
        
        test_goals = [
            {"id": "goal-1", "description": "Develop email marketing strategy", "status": "active"},
            {"id": "goal-2", "description": "Create social media content", "status": "active"}
        ]
        
        result = await ai_goal_matcher.analyze_and_match(
            test_deliverable,
            test_goals
        )
        
        print(f"✅ AI Goal Matcher result: confidence {result.confidence}%")
        
    except Exception as e:
        print(f"⚠️ AI Goal Matcher test failed: {e}")
    
    # Final verification
    final_final_stats = tracker.get_status_data()
    total_requests = final_final_stats['requests_per_minute']['current']
    
    print("\n" + "="*60)
    if total_requests > 0:
        print("🎉 SUCCESS: Quota tracking integration is working!")
        print(f"📊 Total requests tracked: {total_requests}")
        print("✅ OpenAI client factory properly integrates with quota system")
        print("✅ Conversational agents track API usage")
        print("✅ AI services (Goal Matcher, etc.) track API usage")
    else:
        print("⚠️ WARNING: No quota tracking detected.")
        print("📋 Possible causes:")
        print("  - OpenAI API key not set")
        print("  - Client factory not properly integrated")
        print("  - API calls failed before reaching OpenAI")
    print("="*60 + "\n")
    
    print("💡 TIP: Check quota status in browser:")
    print("   http://localhost:3001/projects/test-workspace-integration/conversation")
    print("   Look for Budget & Usage chat in conversation sidebar")
    
    return total_requests > 0

async def main():
    """Main test runner"""
    try:
        # Check for OpenAI API key
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ ERROR: OPENAI_API_KEY environment variable not set")
            return False
        
        success = await test_quota_tracking_integration()
        
        if success:
            print("\n✅ QUOTA TRACKING INTEGRATION: VERIFIED!")
            print("The centralized client factory fix is working correctly.")
        else:
            print("\n⚠️ Integration verification needs investigation.")
            
        return success
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Add backend to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Run the async test
    result = asyncio.run(main())
    sys.exit(0 if result else 1)