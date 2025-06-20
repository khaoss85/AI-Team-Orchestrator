#!/usr/bin/env python3
"""
Quick import test to verify all conversational AI components load correctly
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the path properly
backend_dir = Path(__file__).parent.absolute()
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))
os.chdir(backend_dir)

def test_imports():
    """Test that all conversational AI components can be imported"""
    
    print("🔍 Testing Conversational AI Component Imports...")
    
    try:
        print("   ✓ Testing ConversationalAgent...")
        from ai_agents.conversational import ConversationalAgent, ConversationResponse, ConversationContext
        print("   ✅ ConversationalAgent imported successfully")
        
        print("   ✓ Testing ConversationalTools...")
        from ai_agents.conversational_tools import ConversationalToolRegistry
        print("   ✅ ConversationalTools imported successfully")
        
        print("   ✓ Testing ContextManager...")
        from utils.context_manager import ConversationContextManager, get_workspace_context
        print("   ✅ ContextManager imported successfully")
        
        print("   ✓ Testing ConfirmationManager...")
        from utils.confirmation_manager import ConfirmationManager, RiskLevel, ActionType
        print("   ✅ ConfirmationManager imported successfully")
        
        print("   ✓ Testing AmbiguityResolver...")
        from utils.ambiguity_resolver import AmbiguityResolver, AmbiguityType, ClarificationStrategy
        print("   ✅ AmbiguityResolver imported successfully")
        
        print("   ✓ Testing VersioningManager...")
        from utils.versioning_manager import VersioningManager, VersionCompatibility, ComponentType
        print("   ✅ VersioningManager imported successfully")
        
        print("   ✓ Testing Conversation Routes...")
        from routes.conversation import router, ChatMessageRequest, ChatMessageResponse
        print("   ✅ Conversation Routes imported successfully")
        
        print("\n🎉 ALL IMPORTS SUCCESSFUL!")
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality without database"""
    
    print("\n🧪 Testing Basic Functionality (No DB)...")
    
    try:
        # Test creating agent instance
        from ai_agents.conversational import ConversationalAgent
        agent = ConversationalAgent("test-workspace", "test-chat")
        print("   ✅ ConversationalAgent instance created")
        
        # Test tool registry
        tools_count = len(agent.available_tools)
        print(f"   ✅ Tool registry loaded: {tools_count} tools available")
        
        # Test context manager
        from utils.context_manager import ConversationContextManager
        context_manager = ConversationContextManager("test-workspace")
        print("   ✅ ContextManager instance created")
        
        # Test ambiguity resolver
        from utils.ambiguity_resolver import AmbiguityResolver
        resolver = AmbiguityResolver("test-workspace")
        print("   ✅ AmbiguityResolver instance created")
        
        # Test confirmation manager
        from utils.confirmation_manager import ConfirmationManager
        confirmation_mgr = ConfirmationManager("test-workspace")
        print("   ✅ ConfirmationManager instance created")
        
        # Test versioning manager
        from utils.versioning_manager import VersioningManager
        version_mgr = VersioningManager("test-workspace")
        print("   ✅ VersioningManager instance created")
        
        print("\n🎯 BASIC FUNCTIONALITY TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Functionality Test Error: {e}")
        return False

def test_sdk_integration():
    """Test SDK integration and fallbacks"""
    
    print("\n🔌 Testing SDK Integration...")
    
    try:
        from ai_agents.conversational_tools import SDK_AVAILABLE
        print(f"   SDK Available: {SDK_AVAILABLE}")
        
        if SDK_AVAILABLE:
            print("   ✅ OpenAI Agents SDK detected")
        else:
            print("   ⚠️ SDK not available - using fallback mode")
        
        # Test that function_tool decorator works regardless
        from ai_agents.conversational_tools import function_tool
        
        @function_tool
        def test_tool():
            return "test"
        
        result = test_tool()
        print("   ✅ Function tool decorator working")
        
        return True
        
    except Exception as e:
        print(f"❌ SDK Integration Error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Conversational AI Import Tests\n")
    
    tests = [
        ("Component Imports", test_imports),
        ("Basic Functionality", test_basic_functionality), 
        ("SDK Integration", test_sdk_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Conversational AI is ready.")
    else:
        print("⚠️ Some tests failed. Check errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)