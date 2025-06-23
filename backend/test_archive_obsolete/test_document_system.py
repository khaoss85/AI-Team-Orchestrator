#!/usr/bin/env python3
"""
Test Document Management System
"""

import asyncio
import sys
import os
import base64
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

async def test_document_system():
    print("🧪 Testing Document Management System...\n")
    
    # Test 1: Import modules
    print("1️⃣ Testing imports...")
    try:
        from services.document_manager import document_manager
        print("✅ document_manager imported")
        
        from tools.document_tools import document_tools
        print("✅ document_tools imported")
        
        from database import get_supabase_client
        print("✅ database connection imported")
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test 2: Check OpenAI API key
    print("\n2️⃣ Checking OpenAI API key...")
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and api_key.startswith("sk-"):
        print(f"✅ OpenAI API key found: sk-...{api_key[-4:]}")
    else:
        print("❌ OpenAI API key not found or invalid")
    
    # Test 3: Check if tables exist
    print("\n3️⃣ Checking database tables...")
    try:
        supabase = get_supabase_client()
        
        # Try to query the tables
        try:
            result = supabase.table("workspace_documents").select("id").limit(1).execute()
            print("✅ workspace_documents table exists")
        except Exception as e:
            print(f"❌ workspace_documents table not found: {e}")
            print("   Run the SQL migration to create it")
        
        try:
            result = supabase.table("workspace_vector_stores").select("id").limit(1).execute()
            print("✅ workspace_vector_stores table exists")
        except Exception as e:
            print(f"❌ workspace_vector_stores table not found: {e}")
            print("   Run the SQL migration to create it")
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
    
    # Test 4: Test document manager initialization
    print("\n4️⃣ Testing DocumentManager initialization...")
    try:
        if document_manager.openai_client:
            print("✅ OpenAI client initialized in DocumentManager")
        else:
            print("❌ OpenAI client not initialized")
    except Exception as e:
        print(f"❌ DocumentManager test failed: {e}")
    
    # Test 5: Test a simple document upload (mock)
    print("\n5️⃣ Testing document upload logic (dry run)...")
    try:
        # Create a test file content
        test_content = b"This is a test document for the AI Team Orchestrator."
        test_base64 = base64.b64encode(test_content).decode('utf-8')
        
        # Test the document tool
        upload_tool = document_tools["upload_document"]
        print(f"✅ Document upload tool available: {upload_tool.name}")
        
        # Test the list tool
        list_tool = document_tools["list_documents"]
        print(f"✅ Document list tool available: {list_tool.name}")
        
        # Test the search tool
        search_tool = document_tools["search_documents"]
        print(f"✅ Document search tool available: {search_tool.name}")
        
    except Exception as e:
        print(f"❌ Document tools test failed: {e}")
    
    print("\n✅ All tests completed!")
    print("\n📋 Next steps:")
    print("1. If tables don't exist, run the SQL migration")
    print("2. Ensure OpenAI API key is valid and has proper permissions")
    print("3. Test with a real workspace ID through the UI")

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(test_document_system())