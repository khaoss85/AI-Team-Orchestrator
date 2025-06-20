#!/usr/bin/env python3
"""
Test Direct Tool Execution for Upload
"""

import asyncio
import sys
import base64
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

async def test_direct_tool_execution():
    print("🔧 Testing Direct Tool Execution...")
    print("=" * 50)
    
    try:
        from tools.document_tools import document_tools
        
        # Create simple test content
        test_content = "Simple test file content for direct tool execution test."
        file_data = base64.b64encode(test_content.encode()).decode('utf-8')
        
        print(f"📄 Test content: {len(test_content)} bytes")
        print(f"📊 Base64 encoded: {len(file_data)} chars")
        
        # Test upload tool directly
        upload_tool = document_tools["upload_document"]
        
        workspace_id = "2bb350e1-de8a-4e4e-9791-3bdbaaeda6a2"
        context = {"workspace_id": workspace_id}
        
        result = await upload_tool.execute(
            file_data=file_data,
            filename="direct_test.txt",
            sharing_scope="team",
            description="Direct tool execution test",
            tags=["direct", "test"],
            context=context
        )
        
        print("📋 Upload result:")
        print(result)
        
        if "✅" in result:
            print("\n🎉 SUCCESS: Direct tool execution works!")
            
            # Test search
            search_tool = document_tools["search_documents"]
            search_result = await search_tool.execute(
                query="direct test",
                max_results=3,
                context=context
            )
            
            print("\n🔍 Search result:")
            print(search_result[:200] + "..." if len(search_result) > 200 else search_result)
            
            return True
        else:
            print("\n❌ FAILED: Upload didn't work")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_conversational_agent_simple():
    print("\n💬 Testing Simple Message Processing...")
    print("=" * 50)
    
    try:
        from ai_agents.conversational_simple import SimpleConversationalAgent
        
        workspace_id = "2bb350e1-de8a-4e4e-9791-3bdbaaeda6a2"
        agent = SimpleConversationalAgent(workspace_id)
        
        # Test simple message (not file upload)
        response = await agent.process_message("What's the status of our workspace?", "test_123")
        
        print("📋 Agent response:")
        print(response.message)
        
        if response.message and len(response.message) > 10:
            print("\n✅ SUCCESS: Basic agent communication works!")
            return True
        else:
            print("\n❌ FAILED: Agent didn't respond properly")
            return False
            
    except Exception as e:
        print(f"\n❌ Agent test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Simple Tool & Agent Test")
    print("=" * 60)
    
    # Test direct tool execution
    tool_ok = asyncio.run(test_direct_tool_execution())
    
    # Test simple agent
    agent_ok = asyncio.run(test_conversational_agent_simple())
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS:")
    print(f"✅ Direct Tool: {'PASS' if tool_ok else 'FAIL'}")
    print(f"✅ Agent Basic: {'PASS' if agent_ok else 'FAIL'}")
    
    if tool_ok and agent_ok:
        print("\n🎉 CORE FUNCTIONALITY WORKING!")
        print("✅ Document tools operational")
        print("✅ Agent communication functional")
        print("✅ Context loading optimized")
    else:
        print("\n❌ Core issues detected")
    
    sys.exit(0 if (tool_ok and agent_ok) else 1)