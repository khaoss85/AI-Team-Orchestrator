#!/usr/bin/env python3
"""
Quick script to check if asset_artifacts were created for workspace
"""
import asyncio
from database import AssetDrivenDatabaseManager

async def check_asset_artifacts():
    db_manager = AssetDrivenDatabaseManager()
    workspace_id = "5975922e-c943-4d99-ad1d-25c01a81da7d"
    
    print(f"🔍 Checking asset_artifacts for workspace: {workspace_id}")
    
    try:
        # Check asset_artifacts table
        result = db_manager.supabase.table("asset_artifacts").select("*").eq("workspace_id", workspace_id).execute()
        
        if result.data:
            print(f"✅ Found {len(result.data)} asset_artifacts:")
            for artifact in result.data:
                print(f"   📦 {artifact['artifact_name']} ({artifact['artifact_type']})")
                print(f"      ID: {artifact['id']}")
                print(f"      Created: {artifact['created_at']}")
                print(f"      Quality: {artifact.get('quality_score', 'N/A')}")
                print(f"      Content length: {len(str(artifact.get('content', '')))}")
                print()
        else:
            print("❌ No asset_artifacts found")
            
        # Check deliverables for comparison
        result = db_manager.supabase.table("deliverables").select("*").eq("workspace_id", workspace_id).execute()
        print(f"📋 For comparison, found {len(result.data)} deliverables")
        
    except Exception as e:
        print(f"❌ Error checking asset_artifacts: {e}")

if __name__ == "__main__":
    asyncio.run(check_asset_artifacts())