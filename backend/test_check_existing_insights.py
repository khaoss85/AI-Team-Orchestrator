#!/usr/bin/env python3
"""
Check existing insights to understand the format
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(__file__))

from database import get_memory_insights, supabase

async def check_existing_insights():
    """Check existing insights format"""
    print("🔍 Checking existing insights format...")
    
    try:
        # Get a sample of existing insights
        result = supabase.table("workspace_insights").select("*").limit(5).execute()
        
        if result.data:
            print(f"✅ Found {len(result.data)} existing insights:")
            for i, insight in enumerate(result.data):
                print(f"\n--- Insight {i+1} ---")
                print(f"ID: {insight.get('id')}")
                print(f"Workspace ID: {insight.get('workspace_id')}")
                print(f"Insight Type: {insight.get('insight_type')}")
                print(f"Agent Role: {insight.get('agent_role')}")
                print(f"Content: {insight.get('content')}")
                print(f"Created: {insight.get('created_at')}")
        else:
            print("❌ No existing insights found")
            
        # Check the table structure
        print("\n🏗️ Checking table structure...")
        
        # Try to get the insight_type constraint info
        try:
            # This might not work due to permissions, but let's try
            result = supabase.rpc("get_table_constraints", {"table_name": "workspace_insights"}).execute()
            if result.data:
                print(f"Constraints: {result.data}")
            else:
                print("No constraint info available")
        except Exception as e:
            print(f"Cannot get constraint info: {e}")
            
    except Exception as e:
        print(f"❌ Error checking insights: {e}")

async def main():
    await check_existing_insights()

if __name__ == "__main__":
    asyncio.run(main())