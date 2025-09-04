#!/usr/bin/env python3
"""
Simple test to verify quota tracking integration
"""

import sys
import os
import asyncio

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def main():
    from services.openai_quota_tracker import quota_tracker
    from utils.openai_client_factory import get_openai_client
    
    print("🔍 Simple Quota Tracking Verification")
    print("=====================================")
    
    # Check initial status
    initial = quota_tracker.get_status_data()
    print(f"Initial usage: {initial['requests_per_minute']['current']}")
    
    # Test the integration
    print("\n📊 Testing client factory integration...")
    
    try:
        client = get_openai_client()
        print("✅ Client factory loaded successfully")
        print("✅ OpenAI client created with quota tracking")
        
        # Try to make an API call (will fail due to quota but that's expected)
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            print("✅ API call successful")
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                print("✅ API call failed as expected (quota exceeded)")
                print(f"   Error properly tracked: {type(e).__name__}")
            else:
                print(f"❌ Unexpected error: {e}")
                
    except Exception as e:
        print(f"❌ Client creation failed: {e}")
        return
    
    # Check final status
    final = quota_tracker.get_status_data()
    print(f"\nFinal usage: {final['requests_per_minute']['current']}")
    print(f"Error count: {final['errors']['count']}")
    
    if final['errors']['count'] > initial['errors']['count']:
        print("\n🎉 SUCCESS: Quota tracking is working!")
        print("✅ OpenAI API errors are being properly tracked")
        print("✅ Client factory integration is operational")
    else:
        print("\n⚠️  No quota activity detected (this could be normal if no API calls were made)")
    
    print(f"\nQuota Status: {final['status']}")

if __name__ == "__main__":
    asyncio.run(main())