#!/usr/bin/env python3
"""
🔍 DATABASE CONNECTION TEST
Quick test to identify database connection issues
"""

import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

async def test_database_connection():
    """Test basic database connectivity"""
    print("🔍 TESTING DATABASE CONNECTION")
    print("=" * 50)
    
    try:
        # Create client
        supabase = create_client(supabase_url, supabase_key)
        print("✅ Supabase client created successfully")
        
        # Test 1: Simple ping-like query
        print("\n📡 Testing basic connectivity...")
        result = supabase.table("workspaces").select("count", count="exact").limit(1).execute()
        print(f"✅ Basic query successful. Result count: {result.count}")
        
        # Test 2: Check if workspaces table exists and has data
        print("\n📋 Testing workspaces table...")
        result = supabase.table("workspaces").select("id, name, user_id").limit(5).execute()
        print(f"✅ Workspaces query successful. Found {len(result.data) if result.data else 0} workspaces")
        
        if result.data:
            print("Sample workspace IDs:")
            for ws in result.data[:3]:
                print(f"  - {ws.get('id')} | {ws.get('name', 'Unnamed')}")
        
        # Test 3: Test with specific user_id query
        test_user_id = "123e4567-e89b-12d3-a456-426614174000"
        print(f"\n👤 Testing user-specific query for user: {test_user_id}")
        result = supabase.table("workspaces").select("*").eq("user_id", test_user_id).execute()
        print(f"✅ User workspaces query successful. Found {len(result.data) if result.data else 0} workspaces for user")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print(f"🌐 Connecting to: {supabase_url}")
    success = await test_database_connection()
    
    if success:
        print("\n🎉 All database tests passed!")
        print("The issue is likely in the API request handling, not database connectivity.")
    else:
        print("\n💥 Database connection failed!")
        print("This explains why the API calls are hanging.")

if __name__ == "__main__":
    asyncio.run(main())