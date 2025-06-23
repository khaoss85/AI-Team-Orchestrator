#!/usr/bin/env python3
"""
Test Conversational Agent with Document Tools
"""

import asyncio
import sys
import base64
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

from dotenv import load_dotenv
load_dotenv()

async def test_conversational_agent():
    print("🤖 Testing Conversational Agent with Document Tools...\n")
    
    try:
        from ai_agents.conversational_simple import SimpleConversationalAgent
        
        # Create agent
        workspace_id = "2bb350e1-de8a-4e4e-9791-3bdbaaeda6a2"
        agent = SimpleConversationalAgent(workspace_id, "knowledge")
        
        print("1️⃣ Testing agent initialization...")
        print(f"✅ Agent created for workspace: {workspace_id}")
        print(f"✅ Agent has {len(agent.tools_available)} tools available")
        
        # Check if document tools are available
        document_tools = ["upload_document", "list_documents", "delete_document", "search_documents"]
        for tool in document_tools:
            if tool in agent.tools_available:
                print(f"✅ Document tool available: {tool}")
            else:
                print(f"❌ Document tool missing: {tool}")
        
        print("\n2️⃣ Testing list documents message...")
        response = await agent.process_message("List all documents")
        print(f"📋 Response: {response.message[:200]}...")
        
        print("\n3️⃣ Testing search documents message...")
        response = await agent.process_message("Search for 'test' in documents")
        print(f"🔍 Response: {response.message[:200]}...")
        
        print("\n4️⃣ Testing document upload simulation...")
        test_content = "This is another test document uploaded via chat agent."
        file_data = base64.b64encode(test_content.encode()).decode('utf-8')
        
        upload_message = f'EXECUTE_TOOL: upload_document {{"file_data": "{file_data}", "filename": "agent_test.txt", "sharing_scope": "team", "description": "Uploaded via conversational agent"}}'
        response = await agent.process_message(upload_message)
        print(f"📤 Upload response: {response.message[:200]}...")
        
        print("\n✅ Conversational agent test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_conversational_agent())