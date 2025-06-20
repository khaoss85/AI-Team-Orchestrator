#!/usr/bin/env python3
"""
Cleanup mock data from previous tests
"""

import sys
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

from dotenv import load_dotenv
load_dotenv()

def cleanup_mock_data():
    print("🧹 Cleaning up mock data...")
    
    try:
        from database import get_supabase_client
        supabase = get_supabase_client()
        
        # Delete mock vector stores (those with vs_ prefix that are mock)
        vs_result = supabase.table("workspace_vector_stores").select("*").execute()
        
        for vs in vs_result.data:
            vs_id = vs['openai_vector_store_id']
            if vs_id.startswith("vs_") and len(vs_id) == 27:  # Mock format
                print(f"🗑️ Deleting mock vector store: {vs_id}")
                supabase.table("workspace_vector_stores").delete().eq("id", vs['id']).execute()
        
        # Delete test documents
        doc_result = supabase.table("workspace_documents").select("*").execute()
        
        for doc in doc_result.data:
            if "test" in doc['filename'].lower():
                print(f"🗑️ Deleting test document: {doc['filename']}")
                supabase.table("workspace_documents").delete().eq("id", doc['id']).execute()
        
        print("✅ Cleanup completed!")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")

if __name__ == "__main__":
    cleanup_mock_data()