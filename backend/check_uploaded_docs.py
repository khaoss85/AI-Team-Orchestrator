#!/usr/bin/env python3
"""
Check uploaded documents in database
"""

import sys
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

from dotenv import load_dotenv
load_dotenv()

from database import get_supabase_client

def check_documents():
    print("📋 Checking uploaded documents in database...\n")
    
    try:
        supabase = get_supabase_client()
        
        # Get all documents
        result = supabase.table("workspace_documents").select("*").execute()
        
        if result.data:
            print(f"Found {len(result.data)} documents:")
            for doc in result.data:
                print(f"📄 {doc['filename']}")
                print(f"   ID: {doc['id']}")
                print(f"   Size: {doc['file_size']} bytes")
                print(f"   Scope: {doc['sharing_scope']}")
                print(f"   Upload date: {doc['upload_date']}")
                print(f"   Description: {doc.get('description', 'None')}")
                print(f"   Tags: {doc.get('tags', [])}")
                print()
        else:
            print("No documents found in database")
            
        # Check vector stores
        vs_result = supabase.table("workspace_vector_stores").select("*").execute()
        
        if vs_result.data:
            print(f"Found {len(vs_result.data)} vector stores:")
            for vs in vs_result.data:
                print(f"🗃️ {vs['name']}")
                print(f"   ID: {vs['openai_vector_store_id']}")
                print(f"   Scope: {vs['scope']}")
                print(f"   File count: {vs['file_count']}")
                print()
        else:
            print("No vector stores found in database")
            
    except Exception as e:
        print(f"Error checking documents: {e}")

if __name__ == "__main__":
    check_documents()