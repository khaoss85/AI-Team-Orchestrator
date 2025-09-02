#!/usr/bin/env python3
"""
Quick test to verify SDK compliance and fallback functionality
"""

import asyncio
import os
import sys
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

# Test environment switching
async def test_rag_implementations():
    print("=" * 60)
    print("🧪 TEST IMPLEMENTATION SWITCHING")
    print("=" * 60)
    
    workspace_id = "f35639dc-12ae-4720-882d-3e35a70a79b8"
    
    # Test 1: OpenAI Assistants API (current setting)
    print("\n🤖 TEST 1: OpenAI Assistants API")
    print("-" * 40)
    try:
        from ai_agents.conversational_factory import get_conversational_agent
        agent = get_conversational_agent(workspace_id, "test")
        agent_type = type(agent).__name__
        print(f"✅ Agent Type: {agent_type}")
        
        if agent_type == "ConversationalAssistant":
            print("✅ Using OpenAI Assistants API (Native SDK)")
        else:
            print("✅ Using SimpleConversationalAgent (Fallback)")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Temporarily switch to fallback
    print("\n🔄 TEST 2: Fallback Implementation")
    print("-" * 40)
    original_setting = os.getenv("USE_OPENAI_ASSISTANTS")
    os.environ["USE_OPENAI_ASSISTANTS"] = "false"
    
    try:
        # Reimport to pick up new setting
        import importlib
        import ai_agents.conversational_factory
        importlib.reload(ai_agents.conversational_factory)
        
        from ai_agents.conversational_factory import get_conversational_agent
        fallback_agent = get_conversational_agent(workspace_id, "test-fallback")
        fallback_type = type(fallback_agent).__name__
        print(f"✅ Agent Type: {fallback_type}")
        
        if fallback_type == "SimpleConversationalAgent":
            print("✅ Fallback working correctly")
        else:
            print("⚠️  Expected SimpleConversationalAgent")
            
    except Exception as e:
        print(f"❌ Fallback Error: {e}")
    finally:
        # Restore original setting
        if original_setting:
            os.environ["USE_OPENAI_ASSISTANTS"] = original_setting
    
    # Test 3: Document Manager SDK Compliance
    print("\n🔧 TEST 3: Document Manager SDK Compliance")
    print("-" * 40)
    try:
        from services.document_manager import document_manager
        
        # Check that HTTP-related attributes are gone
        if hasattr(document_manager, 'headers'):
            print("❌ VIOLATION: Still has HTTP headers")
        else:
            print("✅ SDK COMPLIANT: No HTTP headers")
        
        if hasattr(document_manager, 'base_url'):
            print("❌ VIOLATION: Still has base_url")
        else:
            print("✅ SDK COMPLIANT: No base_url")
            
        if hasattr(document_manager, 'openai_client'):
            print("✅ SDK COMPLIANT: Uses OpenAI client")
        else:
            print("❌ Missing OpenAI client")
            
    except Exception as e:
        print(f"❌ Document Manager Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ QUICK TESTS COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_rag_implementations())