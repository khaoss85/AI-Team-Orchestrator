#!/usr/bin/env python3
"""
Quick status check to verify E2E completion
"""

import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from database import supabase
from dotenv import load_dotenv

load_dotenv()

async def main():
    print("🔍 QUICK STATUS CHECK")
    print("=" * 30)
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"API Key: {'✅ Available' if api_key else '❌ Missing'}")
    
    # Check task counts
    print("\n📊 TASK STATUS:")
    for status in ['pending', 'in_progress', 'completed', 'failed']:
        try:
            response = await asyncio.to_thread(
                supabase.table("tasks").select("id").eq("status", status).execute
            )
            count = len(response.data)
            print(f"  {status.upper()}: {count}")
        except Exception as e:
            print(f"  {status.upper()}: Error - {e}")
    
    # Check assets
    print("\n📦 ASSETS:")
    try:
        response = await asyncio.to_thread(
            supabase.table("asset_artifacts").select("id,name,status").execute
        )
        count = len(response.data)
        print(f"  Total artifacts: {count}")
        
        if response.data:
            print("  Recent artifacts:")
            for artifact in response.data[:3]:
                print(f"    - {artifact.get('name', 'Unnamed')} ({artifact.get('status', 'N/A')})")
    except Exception as e:
        print(f"  Error checking assets: {e}")
    
    # Check agents
    print("\n👥 AGENTS:")
    try:
        response = await asyncio.to_thread(
            supabase.table("agents").select("id,name,status").execute
        )
        active_count = len([a for a in response.data if a.get('status') == 'active'])
        print(f"  Active agents: {active_count}")
    except Exception as e:
        print(f"  Error checking agents: {e}")
    
    print("\n✅ Quick check completed!")

if __name__ == "__main__":
    asyncio.run(main())