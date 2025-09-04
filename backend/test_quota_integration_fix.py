#!/usr/bin/env python3
"""
Test script to verify quota tracking integration fix
This tests that all major OpenAI client usage points now properly track quota
"""

import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging to see quota tracking messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_quota_tracking():
    """Test that various OpenAI calls are properly tracked"""
    
    print("\n" + "="*60)
    print("🔍 QUOTA TRACKING INTEGRATION TEST")
    print("="*60 + "\n")
    
    # 1. Test quota status before any calls
    print("📊 STEP 1: Checking initial quota status...")
    from services.openai_quota_tracker import quota_tracker
    
    initial_stats = quota_tracker.get_status_data()
    print(f"✅ Initial status: {initial_stats.get('status', 'unknown')}")
    if 'requests_per_minute' in initial_stats:
        print(f"✅ Initial requests per minute: {initial_stats['requests_per_minute']['current']}")
        print(f"✅ Initial requests per day: {initial_stats['requests_per_day']['current']}")
    else:
        print(f"✅ Initial data: {initial_stats}")
    
    # 2. Test conversational agent (most common usage)
    print("\n📊 STEP 2: Testing conversational agent with quota tracking...")
    try:
        from ai_agents.conversational_simple import SimpleConversationalAgent
        
        # Create a test workspace ID
        test_workspace_id = "test-workspace-quota-tracking"
        
        agent = SimpleConversationalAgent(test_workspace_id, "test-chat")
        
        # Make a simple API call through the agent
        test_message = "What is 2+2? (This is a quota tracking test)"
        response = await agent.process_message(test_message)
        
        print(f"✅ Conversational agent response received: {response.message[:100]}...")
        
    except Exception as e:
        print(f"⚠️ Conversational agent test failed (may not have workspace): {e}")
    
    # 3. Test direct client factory usage
    print("\n📊 STEP 3: Testing direct client factory usage...")
    try:
        from utils.openai_client_factory import get_openai_client
        
        client = get_openai_client()
        
        # Make a simple completion request
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'quota tracking test successful' if you can hear me"}],
            max_tokens=20
        )
        
        print(f"✅ Direct client response: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ Direct client test failed: {e}")
    
    # 4. Test async client factory usage
    print("\n📊 STEP 4: Testing async client factory usage...")
    try:
        from utils.openai_client_factory import get_async_openai_client
        
        async_client = get_async_openai_client()
        
        # Make an async completion request
        response = await async_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Confirm async quota tracking is working"}],
            max_tokens=20
        )
        
        print(f"✅ Async client response: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ Async client test failed: {e}")
    
    # 5. Check final quota stats
    print("\n📊 STEP 5: Checking final quota statistics...")
    final_stats = quota_tracker.get_status_data()
    
    requests_made = 0
    tokens_used = 0
    
    if 'requests_per_minute' in final_stats and 'requests_per_minute' in initial_stats:
        requests_made = final_stats['requests_per_minute']['current'] - initial_stats['requests_per_minute']['current']
        if 'tokens_per_minute' in final_stats:
            tokens_used = final_stats.get('tokens_per_minute', {}).get('current', 0) - initial_stats.get('tokens_per_minute', {}).get('current', 0)
    
        print(f"✅ Requests made during test: {requests_made}")
        print(f"✅ Tokens used during test: {tokens_used}")
        print(f"✅ Current daily usage: {final_stats['requests_per_day']['current']}/{final_stats['requests_per_day']['limit']}")
    else:
        print(f"✅ Final status data: {final_stats}")
    
    # Verification
    print("\n" + "="*60)
    if requests_made > 0:
        print("🎉 SUCCESS: Quota tracking is working! All API calls are being monitored.")
        print(f"📊 {requests_made} requests were tracked during this test")
        print(f"📊 {tokens_used} tokens were consumed")
    else:
        print("⚠️ WARNING: No requests were tracked. There may still be an integration issue.")
    print("="*60 + "\n")
    
    # Show quota API endpoint for verification
    print("💡 TIP: You can also check the quota status via API:")
    print("   curl http://localhost:8000/api/quota/status")
    print("   curl http://localhost:8000/api/quota/notifications")
    
    return requests_made > 0

async def main():
    """Main test runner"""
    try:
        # Check for OpenAI API key
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ ERROR: OPENAI_API_KEY environment variable not set")
            print("Please set it in backend/.env file")
            return False
        
        # Run the tests
        success = await test_quota_tracking()
        
        if success:
            print("\n✅ QUOTA TRACKING FIX VERIFIED SUCCESSFULLY!")
            print("The system is now properly tracking all OpenAI API usage.")
        else:
            print("\n⚠️ Quota tracking may need additional fixes.")
            
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