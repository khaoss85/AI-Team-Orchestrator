#!/usr/bin/env python3
"""
Test script to trace why insights aren't being generated despite code being called
"""

import os
import asyncio
from dotenv import load_dotenv
from datetime import datetime
from uuid import UUID
import logging

# Configure logging to see all debug messages
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

async def test_direct_insight_storage():
    """Test storing an insight directly to see if it works"""
    
    workspace_id = UUID("f5c4f1e0-a887-4431-b43e-aea6d62f2d4a")
    
    print("\n🧪 TEST 1: Direct WorkspaceMemory Storage Test")
    print("=" * 80)
    
    try:
        from workspace_memory import workspace_memory
        from models import InsightType
        
        # Test with minimum viable insight
        test_insight = await workspace_memory.store_insight(
            workspace_id=workspace_id,
            agent_role="test_script",
            insight_type=InsightType.DISCOVERY,
            content="TEST INSIGHT: This is a test insight to verify storage is working",
            relevance_tags=["test", "debug", "verification"],
            confidence_score=0.8
        )
        
        if test_insight:
            print(f"✅ SUCCESS! Insight stored with ID: {test_insight.id}")
            print(f"   Content: {test_insight.content}")
            print(f"   Type: {test_insight.insight_type}")
            print(f"   Tags: {test_insight.relevance_tags}")
        else:
            print("❌ FAILED! store_insight returned None")
            
    except Exception as e:
        print(f"❌ ERROR during insight storage: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🧪 TEST 2: Check if insight was saved to database")
    print("=" * 80)
    
    try:
        from supabase import create_client, Client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Query for our test insight
        result = supabase.table("workspace_insights").select("*").eq("workspace_id", str(workspace_id)).eq("agent_role", "test_script").execute()
        
        if result.data:
            print(f"✅ Found {len(result.data)} test insights in database!")
            for insight in result.data:
                print(f"   - {insight['content'][:50]}... (created: {insight['created_at']})")
        else:
            print("❌ No test insights found in database")
            
    except Exception as e:
        print(f"❌ ERROR querying database: {e}")
    
    print("\n🧪 TEST 3: Test insight generation from task completion simulation")
    print("=" * 80)
    
    try:
        # Simulate what executor does on task completion
        print("Simulating task completion with insight generation...")
        
        # Create a more realistic insight like executor would
        task_output = "Successfully analyzed workspace configuration and identified optimization opportunities"
        
        # Test with very low thresholds since this is early in workspace
        insight_content = f"Task completion insight: {task_output}"
        
        insight = await workspace_memory.store_insight(
            workspace_id=workspace_id,
            agent_role="executor_simulation",
            insight_type=InsightType.SUCCESS_PATTERN,
            content=insight_content[:200],  # Truncate like executor does
            relevance_tags=["task_completion", "success"],
            confidence_score=0.5  # Lower confidence to pass threshold
        )
        
        if insight:
            print(f"✅ Task completion insight stored: {insight.id}")
        else:
            print("❌ Task completion insight was not stored (returned None)")
            print("   This suggests the insight was filtered out by anti-pollution controls")
            
    except Exception as e:
        print(f"❌ ERROR during task completion simulation: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🧪 TEST 4: Check WorkspaceMemory thresholds and limits")
    print("=" * 80)
    
    print(f"Configuration:")
    print(f"  - ENABLE_WORKSPACE_MEMORY: {os.getenv('ENABLE_WORKSPACE_MEMORY', 'not set')}")
    print(f"  - Max insights per workspace: {workspace_memory.max_insights_per_workspace}")
    print(f"  - Min confidence threshold: {workspace_memory.min_confidence_threshold}")
    print(f"  - Default TTL days: {workspace_memory.default_insight_ttl_days}")
    
    # Check current insight count
    current_count = await workspace_memory._get_workspace_insight_count(workspace_id)
    print(f"\nCurrent insight count for workspace: {current_count}")
    print(f"Space available: {workspace_memory.max_insights_per_workspace - current_count}")
    
    if current_count < 5:
        print("\n💡 EARLY WORKSPACE DETECTED: Thresholds are lowered for first 5 insights")
        print(f"   - Min content length: 5 chars (vs normal 10)")
        print(f"   - Min confidence: 0.1 (vs normal {workspace_memory.min_confidence_threshold})")
    
    print("\n" + "=" * 80)
    print("🔍 INVESTIGATION COMPLETE!")
    print("\nKey findings:")
    print("1. Check if insights are being stored successfully")
    print("2. Verify database permissions (service key)")
    print("3. Check anti-pollution thresholds")
    print("4. Look for early workspace threshold adjustments")

if __name__ == "__main__":
    asyncio.run(test_direct_insight_storage())