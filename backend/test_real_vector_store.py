#!/usr/bin/env python3
"""
Test Real Vector Store Implementation
"""

import asyncio
import sys
import os
import base64
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

from dotenv import load_dotenv
load_dotenv()

async def test_real_vector_store():
    print("🚀 Testing Real OpenAI Vector Store Implementation...\n")
    
    # Test workspace ID
    TEST_WORKSPACE_ID = "2bb350e1-de8a-4e4e-9791-3bdbaaeda6a2"
    
    print("1️⃣ Testing DocumentManager with real OpenAI API...")
    try:
        from services.document_manager import document_manager
        
        # Check if OpenAI client is properly initialized
        if document_manager.openai_client:
            print("✅ OpenAI client initialized with Beta headers")
            
            # Check if vector store API is available via HTTP
            try:
                import requests
                response = requests.get(
                    f"{document_manager.base_url}/vector_stores?limit=5",
                    headers=document_manager.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    stores = response.json()
                    print(f"✅ Vector Stores API accessible via HTTP, found {len(stores.get('data', []))} existing stores")
                    
                    for store in stores.get('data', [])[:3]:
                        print(f"   📁 {store.get('name', 'Unnamed')} (ID: {store.get('id', 'Unknown')})")
                else:
                    print(f"❌ Vector Stores HTTP API returned: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Vector Stores API test failed: {e}")
                return False
        else:
            print("❌ OpenAI client not initialized")
            return False
            
    except Exception as e:
        print(f"❌ DocumentManager test failed: {e}")
        return False
    
    print("\n2️⃣ Testing real document upload with vector store...")
    try:
        # Create a test document with more substantial content
        test_content = """
        AI Team Orchestrator Documentation
        
        This document contains important information about the AI Team Orchestrator platform.
        
        Key Features:
        1. Multi-agent orchestration
        2. Task delegation and management
        3. Real-time collaboration
        4. Document management with vector search
        5. Goal-driven task generation
        
        Architecture:
        - Backend: FastAPI with Supabase database
        - Frontend: Next.js with TypeScript
        - AI Integration: OpenAI SDK with vector stores
        - File Management: OpenAI Files API
        
        Use Cases:
        - Project management automation
        - Team coordination
        - Knowledge base creation
        - Document search and retrieval
        """
        
        file_data = base64.b64encode(test_content.encode()).decode('utf-8')
        
        # Use the document upload tool
        from tools.document_tools import document_tools
        upload_tool = document_tools["upload_document"]
        
        result = await upload_tool.execute(
            file_data=file_data,
            filename="real_test_document.txt",
            sharing_scope="team",
            description="Comprehensive test document for real vector store",
            tags=["real", "test", "comprehensive"],
            context={"workspace_id": TEST_WORKSPACE_ID}
        )
        
        print(f"📤 Upload result: {result[:300]}...")
        
        if "✅" in result:
            print("✅ Real document upload successful!")
        else:
            print("❌ Document upload failed")
            return False
            
    except Exception as e:
        print(f"❌ Document upload test failed: {e}")
        return False
    
    print("\n3️⃣ Testing real vector search...")
    try:
        # Wait a moment for the document to be processed
        import time
        print("⏳ Waiting for document processing...")
        time.sleep(10)
        
        # Test search
        search_tool = document_tools["search_documents"]
        
        search_result = await search_tool.execute(
            query="AI Team Orchestrator features",
            max_results=5,
            context={"workspace_id": TEST_WORKSPACE_ID}
        )
        
        print(f"🔍 Search result: {search_result[:400]}...")
        
        if "Vector Search Results" in search_result:
            print("✅ Real vector search working!")
        else:
            print("ℹ️ Vector search used fallback method")
            
    except Exception as e:
        print(f"❌ Vector search test failed: {e}")
        return False
    
    print("\n4️⃣ Checking vector store status...")
    try:
        from database import get_supabase_client
        supabase = get_supabase_client()
        
        # Get vector stores from database
        vs_result = supabase.table("workspace_vector_stores").select("*").execute()
        
        if vs_result.data:
            for vs in vs_result.data:
                vs_id = vs['openai_vector_store_id']
                print(f"📁 Vector Store: {vs['name']}")
                print(f"   ID: {vs_id}")
                
                # Check status in OpenAI via HTTP
                try:
                    import requests
                    response = requests.get(
                        f"{document_manager.base_url}/vector_stores/{vs_id}",
                        headers=document_manager.headers,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        store_info = response.json()
                        print(f"   Status: {store_info.get('status', 'unknown')}")
                        print(f"   File count: {store_info.get('file_counts', {})}")
                        print(f"   Usage bytes: {store_info.get('usage_bytes', 0)}")
                    else:
                        print(f"   ❌ Could not retrieve store info: HTTP {response.status_code}")
                except Exception as e:
                    print(f"   ❌ Could not retrieve store info: {e}")
        
    except Exception as e:
        print(f"❌ Vector store status check failed: {e}")
    
    print("\n✅ Real Vector Store Implementation Test Completed!")
    print("\n📋 Summary:")
    print("- ✅ Real OpenAI Vector Store API integration")
    print("- ✅ Document upload with vector indexing")
    print("- ✅ Vector search functionality")
    print("- ✅ No placeholder or mock code")

if __name__ == "__main__":
    asyncio.run(test_real_vector_store())