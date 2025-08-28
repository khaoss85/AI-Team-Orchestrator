#!/usr/bin/env python3
"""
Direct test for the unified assets fix
Tests that assets are returned even when AI processing fails
"""
import asyncio
import sys
import json

# Add the backend path to sys.path
sys.path.insert(0, '/Users/pelleri/Documents/ai-team-orchestrator/backend')

from routes.unified_assets import unified_asset_manager

async def test_unified_assets_fix():
    """Test the unified assets endpoint fix"""
    print("🔍 Testing unified assets fix...")
    
    # Test workspace ID from the logs
    workspace_id = "5975922e-c943-4d99-ad1d-25c01a81da7d"
    
    try:
        print(f"📡 Calling get_workspace_assets for workspace: {workspace_id}")
        result = await unified_asset_manager.get_workspace_assets(workspace_id)
        
        print(f"✅ Success! Got response:")
        print(f"   - Workspace ID: {result.get('workspace_id')}")
        print(f"   - Asset count: {result.get('asset_count', 0)}")
        print(f"   - Data source: {result.get('data_source')}")
        print(f"   - AI processing failed: {result.get('ai_processing_failed', False)}")
        
        if result.get('assets'):
            print(f"   - Asset keys: {list(result['assets'].keys())[:3]}...")  # Show first 3
        
        # Check if this is our fallback response
        if result.get('ai_processing_failed') or result.get('data_source') == 'concrete_extraction_fallback':
            print("🎯 SUCCESS: Fallback mechanism worked! Assets returned despite AI failures.")
        elif result.get('asset_count', 0) > 0:
            print("🎯 SUCCESS: Assets returned successfully!")
        else:
            print("⚠️  Got empty response")
            
        return result
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    result = asyncio.run(test_unified_assets_fix())
    if result and result.get('asset_count', 0) > 0:
        print(f"\n🎉 FIX VERIFIED: {result['asset_count']} assets would be shown to frontend!")
        sys.exit(0)
    else:
        print(f"\n❌ FIX FAILED: No assets returned")
        sys.exit(1)