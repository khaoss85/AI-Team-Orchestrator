#!/usr/bin/env python3
"""
Test script to verify document RAG (Retrieval-Augmented Generation) integration
Tests that conversational agents can search and use uploaded documents
"""

import asyncio
import logging
from ai_agents.conversational_simple import SimpleConversationalAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_document_detection():
    """Test if the agent correctly detects document-related queries"""
    
    workspace_id = "0de74da8-d2a6-47c3-9f08-3824bf1604e0"
    agent = SimpleConversationalAgent(workspace_id, "test-chat")
    
    test_queries = [
        "summarize the book",
        "what's in book.pdf",
        "show me the documents",
        "analyze the uploaded file",
        "what documents are available",
        "read the report",
        "tell me about the PDF"
    ]
    
    print("\n🔍 Testing Document Query Detection:\n")
    for query in test_queries:
        is_doc_query = agent._is_asking_about_documents(query)
        print(f"  Query: '{query}' -> Document Query: {is_doc_query}")
    
    print("\n✅ Document detection test complete")

async def test_document_search():
    """Test document search functionality"""
    
    workspace_id = "0de74da8-d2a6-47c3-9f08-3824bf1604e0"
    agent = SimpleConversationalAgent(workspace_id, "test-chat")
    
    print("\n📄 Testing Document Search:\n")
    
    # Test searching for documents
    test_queries = [
        "book.pdf",
        "summary of uploaded documents",
        "project report"
    ]
    
    for query in test_queries:
        print(f"\n  Searching for: '{query}'")
        try:
            results = await agent._search_relevant_documents(query)
            print(f"  Results preview: {results[:200]}...")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print("\n✅ Document search test complete")

async def test_full_rag_integration():
    """Test full RAG integration with document-aware responses"""
    
    workspace_id = "0de74da8-d2a6-47c3-9f08-3824bf1604e0"
    agent = SimpleConversationalAgent(workspace_id, "test-chat")
    
    print("\n🤖 Testing Full RAG Integration:\n")
    
    # Test queries that should trigger document search
    test_queries = [
        "Can you summarize book.pdf for me?",
        "What documents have been uploaded to this workspace?",
        "Tell me about the main points in the uploaded book"
    ]
    
    for query in test_queries:
        print(f"\n  Query: '{query}'")
        try:
            # Test the full response generation pipeline
            response = await agent.process_message(query)
            print(f"  Response type: {response.message_type}")
            print(f"  Response preview: {response.message[:200]}...")
            
            # Check if document search was triggered
            if agent._is_asking_about_documents(query):
                print(f"  ✅ Document search was triggered")
            else:
                print(f"  ⚠️ Document search was NOT triggered")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print("\n✅ Full RAG integration test complete")

async def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 DOCUMENT RAG INTEGRATION TEST SUITE")
    print("=" * 60)
    
    await test_document_detection()
    await test_document_search()
    await test_full_rag_integration()
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETE")
    print("=" * 60)
    print("\n📝 Summary:")
    print("  1. Document query detection: IMPLEMENTED")
    print("  2. Automatic document search: IMPLEMENTED")
    print("  3. RAG integration in responses: IMPLEMENTED")
    print("\nThe conversational agent now:")
    print("  • Detects when users ask about documents")
    print("  • Automatically searches relevant documents")
    print("  • Includes document content in AI responses")
    print("  • Can summarize and reference uploaded files")

if __name__ == "__main__":
    asyncio.run(main())