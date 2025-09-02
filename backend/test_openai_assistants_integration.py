#!/usr/bin/env python3
"""
Test OpenAI Assistants API integration for RAG functionality
"""

import asyncio
import os
import sys
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

from ai_agents.conversational_factory import get_conversational_agent
from services.document_manager import document_manager

async def test_openai_assistants_rag():
    """Test the new OpenAI Assistants RAG implementation"""
    
    workspace_id = "f35639dc-12ae-4720-882d-3e35a70a79b8"
    
    print("=" * 80)
    print("🤖 TEST OPENAI ASSISTANTS API - RAG FUNCTIONALITY")
    print("=" * 80)
    
    # Check environment configuration
    print("\n🔧 STEP 1: Check configuration")
    print("-" * 50)
    use_assistants = os.getenv("USE_OPENAI_ASSISTANTS", "false").lower() == "true"
    openai_key = os.getenv("OPENAI_API_KEY", "")
    print(f"USE_OPENAI_ASSISTANTS: {use_assistants}")
    print(f"OPENAI_API_KEY configured: {'✅ Yes' if openai_key.startswith('sk-') else '❌ No'}")
    
    # Check documents in workspace
    print("\n📂 STEP 2: Verify documents and vector stores")
    print("-" * 50)
    try:
        docs = await document_manager.list_documents(workspace_id)
        print(f"Documents found: {len(docs)}")
        
        for doc in docs:
            print(f"  - {doc.filename}")
            print(f"    Vector Store ID: {doc.vector_store_id}")
            print(f"    Extracted content: {'✅ Yes' if doc.extracted_text else '❌ No'}")
            if doc.extracted_text:
                print(f"    Content preview: {doc.extracted_text[:100]}...")
                
    except Exception as e:
        print(f"❌ Error checking documents: {e}")
        return
    
    # Test conversational agent factory
    print("\n🤖 STEP 3: Initialize conversational agent")
    print("-" * 50)
    
    try:
        agent = get_conversational_agent(workspace_id, "test-assistants-rag")
        agent_type = type(agent).__name__
        print(f"Agent type: {agent_type}")
        
        if agent_type == "ConversationalAssistant":
            print("✅ Using OpenAI Assistants API")
        else:
            print("⚠️  Using fallback SimpleConversationalAgent")
            
    except Exception as e:
        print(f"❌ Error initializing agent: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test RAG query about the 15 pillars
    print("\n🔍 STEP 4: Test RAG query - 15 pillars")
    print("-" * 50)
    
    query = "Quali sono i 15 pilastri del nostro framework AI descritti nel documento book.pdf?"
    print(f"Query: {query}")
    print()
    
    try:
        response = await agent.process_message(query)
        print("Response:")
        print("-" * 30)
        print(response.message[:800])
        if len(response.message) > 800:
            print("... [truncated]")
        
        # Show citations if available
        if hasattr(response, 'citations') and response.citations:
            print(f"\n📖 Citations found: {len(response.citations)}")
            for i, citation in enumerate(response.citations, 1):
                print(f"  {i}. {citation}")
                
        # Show thread/run info if available
        if hasattr(response, 'thread_id') and response.thread_id:
            print(f"\n🧵 Thread ID: {response.thread_id}")
        if hasattr(response, 'run_id') and response.run_id:
            print(f"🏃 Run ID: {response.run_id}")
            
    except Exception as e:
        print(f"❌ Error processing query: {e}")
        import traceback
        traceback.print_exc()
    
    # Test specific search
    print("\n🎯 STEP 5: Test specific concept search")
    print("-" * 50)
    
    query2 = "Cerca informazioni su 'Goal Decomposition' nel book.pdf"
    print(f"Query: {query2}")
    print()
    
    try:
        response2 = await agent.process_message(query2)
        print("Response:")
        print("-" * 30)
        print(response2.message[:500])
        if len(response2.message) > 500:
            print("... [truncated]")
            
    except Exception as e:
        print(f"❌ Error processing second query: {e}")
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETATO")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_openai_assistants_rag())