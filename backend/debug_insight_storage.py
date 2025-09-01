#!/usr/bin/env python3
"""
Debug script to find exact error when storing insights
"""

import os
import asyncio
from dotenv import load_dotenv
from datetime import datetime
from uuid import UUID, uuid4
import logging
import traceback

# Configure logging to see all debug messages
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

async def debug_insight_storage():
    """Debug exactly why insight storage is failing"""
    
    workspace_id = UUID("f5c4f1e0-a887-4431-b43e-aea6d62f2d4a")
    
    print("\n🔍 DEBUG: Direct Database Insert Test")
    print("=" * 80)
    
    try:
        from supabase import create_client, Client
        from models import InsightType
        
        # Get service client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        print(f"URL exists: {bool(supabase_url)}")
        print(f"Service key exists: {bool(supabase_service_key)}")
        
        supabase_service: Client = create_client(supabase_url, supabase_service_key)
        print("✅ Service client created")
        
        # Create minimal insight data
        insight_id = uuid4()
        insight_data = {
            "id": str(insight_id),
            "workspace_id": str(workspace_id),
            "agent_role": "debug_test",
            "insight_type": InsightType.DISCOVERY.value,
            "content": "DEBUG TEST: Direct insert to verify database permissions",
            "relevance_tags": ["debug", "test"],
            "confidence_score": 0.9,
            "created_at": datetime.now().isoformat(),
            "metadata": {}
        }
        
        print(f"\nInserting insight with ID: {insight_id}")
        print(f"Data: {insight_data}")
        
        # Try to insert
        result = supabase_service.table("workspace_insights").insert(insight_data).execute()
        
        if result.data:
            print(f"✅ SUCCESS! Insight inserted: {result.data}")
        else:
            print(f"❌ No data returned from insert")
            
    except Exception as e:
        print(f"\n❌ ERROR during insert: {e}")
        print(f"Error type: {type(e).__name__}")
        traceback.print_exc()
        
        # Check if it's a specific database error
        if hasattr(e, 'message'):
            print(f"Error message: {e.message}")
        if hasattr(e, 'details'):
            print(f"Error details: {e.details}")
    
    print("\n🔍 DEBUG: Query to verify if insert worked")
    print("=" * 80)
    
    try:
        # Query back to see if it was inserted
        query_result = supabase_service.table("workspace_insights").select("*").eq("agent_role", "debug_test").execute()
        
        if query_result.data:
            print(f"✅ Found {len(query_result.data)} debug test insights in database!")
            for insight in query_result.data:
                print(f"  - ID: {insight['id']}")
                print(f"    Content: {insight['content']}")
                print(f"    Created: {insight['created_at']}")
        else:
            print("❌ No debug test insights found")
            
    except Exception as e:
        print(f"❌ Error querying: {e}")
    
    print("\n🔍 DEBUG: Test WorkspaceMemory store_insight method")
    print("=" * 80)
    
    try:
        from workspace_memory import workspace_memory
        from models import InsightType
        
        # Try storing through WorkspaceMemory
        print("Testing WorkspaceMemory.store_insight()...")
        
        # Patch the store method to see what's happening
        original_insert = workspace_memory._insert_insight_to_db
        
        async def debug_insert(insight):
            print(f"  _insert_insight_to_db called with: {insight.id}")
            print(f"  Content: {insight.content}")
            print(f"  Confidence: {insight.confidence_score}")
            try:
                result = await original_insert(insight)
                print(f"  ✅ Insert successful")
                return result
            except Exception as e:
                print(f"  ❌ Insert failed: {e}")
                raise
        
        workspace_memory._insert_insight_to_db = debug_insert
        
        # Try to store
        result = await workspace_memory.store_insight(
            workspace_id=workspace_id,
            agent_role="workspace_memory_test",
            insight_type=InsightType.SUCCESS_PATTERN,
            content="WORKSPACE MEMORY TEST: This should pass all filters",
            relevance_tags=["test", "debug"],
            confidence_score=0.9  # High confidence to pass filters
        )
        
        if result:
            print(f"✅ WorkspaceMemory returned insight: {result.id}")
        else:
            print("❌ WorkspaceMemory returned None (filtered out)")
            
            # Check thresholds
            count = await workspace_memory._get_workspace_insight_count(workspace_id)
            print(f"\nFilter analysis:")
            print(f"  Current insights in workspace: {count}")
            print(f"  Max allowed: {workspace_memory.max_insights_per_workspace}")
            print(f"  Min confidence threshold: {workspace_memory.min_confidence_threshold}")
            print(f"  Content length requirement: 5 chars (early) or 10 chars (normal)")
            
    except Exception as e:
        print(f"❌ Error in WorkspaceMemory test: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_insight_storage())