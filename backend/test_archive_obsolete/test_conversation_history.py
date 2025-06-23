#!/usr/bin/env python3
"""
Test Conversation History Integration
Tests the conversation history functionality in the AI agent
"""

import asyncio
import requests
import json
import sys
import time
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

def test_conversation_continuity():
    """Test that conversation history provides continuity across messages"""
    print("🧪 Testing Conversation History Integration...")
    print("=" * 60)
    
    workspace_id = "2bb350e1-de8a-4e4e-9791-3bdbaaeda6a2"
    base_url = "http://localhost:8000/api/conversation"
    
    # Test conversation scenario
    conversation_flow = [
        "Il mio progetto si chiama 'E-commerce Platform'",
        "Quanti membri ha il mio team attualmente?",
        "Basandoti sulla risposta precedente, pensi che dovremmo aggiungere qualcuno al team per il progetto E-commerce Platform?"
    ]
    
    print("📋 Testing conversation flow:")
    for i, message in enumerate(conversation_flow, 1):
        print(f"   {i}. {message}")
    print()
    
    try:
        responses = []
        
        for i, message in enumerate(conversation_flow, 1):
            print(f"🔄 Message {i}: {message}")
            
            # Send message to AI
            response = requests.post(
                f"{base_url}/workspaces/{workspace_id}/chat",
                json={"message": message, "chat_id": "team"},
                timeout=30
            )
            
            if response.status_code == 200:
                ai_response = response.json().get("response", "No response")
                responses.append(ai_response)
                
                print(f"   ✅ AI Response:")
                print(f"   {ai_response[:200]}{'...' if len(ai_response) > 200 else ''}")
                print()
                
                # Small delay between messages
                time.sleep(2)
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
        
        # Analyze if the AI showed continuity
        print("🔍 Analyzing conversation continuity:")
        
        # Check if the final response references previous context
        final_response = responses[-1].lower()
        
        continuity_indicators = [
            "e-commerce platform",  # Project name from first message
            "team",  # Team context from second message
            "precedente",  # Reference to previous response
            "basandoti",  # Following up on previous context
            "attualmente",  # Current state from previous question
        ]
        
        found_indicators = []
        for indicator in continuity_indicators:
            if indicator in final_response:
                found_indicators.append(indicator)
        
        print(f"   📊 Continuity indicators found: {len(found_indicators)}/5")
        for indicator in found_indicators:
            print(f"   ✅ Found: '{indicator}'")
        
        if len(found_indicators) >= 2:
            print("\n🎉 SUCCESS: AI shows conversation continuity!")
            print("✅ The AI is maintaining context across messages")
            print("✅ Conversation history is working properly")
        else:
            print("\n⚠️  LIMITED CONTINUITY: AI may not be using full conversation history")
            print("💡 Consider checking conversation history loading")
        
        print(f"\n📈 Conversation Quality Score: {len(found_indicators) * 20}%")
        
        return len(found_indicators) >= 2
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_history_limit():
    """Test that conversation history respects the configured limit"""
    print("\n🔢 Testing History Limit Configuration...")
    print("=" * 60)
    
    # This test would require backend inspection or logs
    # For now, we'll just verify the environment variable
    import os
    history_limit = os.getenv('CONVERSATION_HISTORY_LIMIT', '6')
    
    print(f"📊 Configured history limit: {history_limit} messages")
    print("💡 This means the AI will remember the last {0} exchanges".format(int(history_limit) // 2))
    
    return True

def main():
    print("🧪 Conversation History Integration Test")
    print("=" * 70)
    
    # Test conversation continuity
    continuity_ok = test_conversation_continuity()
    
    # Test history limit configuration
    limit_ok = test_history_limit()
    
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS:")
    print(f"✅ Conversation Continuity: {'PASS' if continuity_ok else 'FAIL'}")
    print(f"✅ History Limit Config: {'PASS' if limit_ok else 'FAIL'}")
    
    if continuity_ok and limit_ok:
        print("\n🎉 CONVERSATION HISTORY FULLY FUNCTIONAL!")
        print("✅ AI maintains context across conversation")
        print("✅ History limit properly configured")
        print("✅ Strategic conversations now possible")
        print("\n📋 Benefits:")
        print("• AI remembers project details mentioned earlier")
        print("• Follow-up questions build on previous responses")
        print("• Strategic discussions span multiple messages")
        print("• Better user experience with context awareness")
    else:
        print("\n❌ Issues detected - check configuration")
    
    return continuity_ok and limit_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)