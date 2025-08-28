#!/usr/bin/env python3
"""
Test script per verificare se il bug in unified_assets.py è stato risolto.
Test veloce senza chiamate AI.
"""

import asyncio
import logging
import os
import sys

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_assets_fix():
    """Test il fix del bug unified_assets rapidamente"""
    
    workspace_id = "5975922e-c943-4d99-ad1d-25c01a81da7d"
    
    print(f"\n🔧 TESTING ASSETS FIX")
    print(f"Workspace ID: {workspace_id}")
    print("=" * 50)
    
    try:
        # Import database functions
        from database import get_deliverables, list_tasks
        from models import TaskStatus
        
        # 1. Quick check: deliverables count
        deliverables = await get_deliverables(workspace_id)
        print(f"✓ Deliverables in DB: {len(deliverables)}")
        
        # 2. Quick check: completed tasks
        tasks = await list_tasks(workspace_id)
        completed_tasks = [t for t in tasks if t.get("status") == TaskStatus.COMPLETED.value]
        print(f"✓ Completed tasks: {len(completed_tasks)}")
        
        # 3. Test the fixed UnifiedAssetManager logic WITHOUT AI calls
        print(f"\n🧪 TESTING FIXED LOGIC (without AI):")
        
        # Import the fixed UnifiedAssetManager
        from routes.unified_assets import unified_asset_manager
        
        # Mock the AI-heavy concrete_extractor to avoid timeouts
        class MockExtractor:
            async def extract_assets_from_task_batch(self, tasks):
                # Return empty dict to trigger the deliverables fallback
                return {}
        
        # Temporarily replace the concrete extractor
        original_extractor = unified_asset_manager.concrete_extractor
        unified_asset_manager.concrete_extractor = MockExtractor()
        
        try:
            # This should now use the deliverable extraction fallback
            print("   → Calling get_workspace_assets with mocked extractor...")
            result = await unified_asset_manager.get_workspace_assets(workspace_id)
            
            print(f"✓ Assets returned: {result.get('asset_count', 0)}")
            print(f"✓ Data source: {result.get('data_source', 'unknown')}")
            print(f"✓ Asset keys: {list(result.get('assets', {}).keys())}")
            
            if result.get('asset_count', 0) > 1:
                print(f"🎉 SUCCESS: Fix worked! Now returning {result.get('asset_count')} assets instead of 1.")
            elif result.get('asset_count', 0) == 1:
                print(f"⚠️ PARTIAL: Still returning only 1 asset. May need further investigation.")
            else:
                print(f"❌ ISSUE: No assets returned.")
                
        finally:
            # Restore original extractor
            unified_asset_manager.concrete_extractor = original_extractor
        
        # 4. Test direct deliverable extraction logic
        print(f"\n🔍 TESTING DELIVERABLE EXTRACTION DIRECTLY:")
        if deliverables:
            for i, deliverable in enumerate(deliverables[:2]):  # Test first 2
                content = deliverable.get('content', {})
                deliverable_type = deliverable.get('type', 'unknown')
                title = deliverable.get('title', 'Unknown')
                
                print(f"   Deliverable {i+1}: {title}")
                print(f"     - Type: {deliverable_type}")
                print(f"     - Content type: {type(content)}")
                print(f"     - Content is dict: {isinstance(content, dict)}")
                
                if isinstance(content, dict):
                    print(f"     - Content keys: {list(content.keys())[:5]}")
                    
                    # Test the extraction method
                    try:
                        extracted = unified_asset_manager._extract_assets_from_deliverable_content(
                            content, deliverable_type, title
                        )
                        print(f"     - Extracted assets: {len(extracted)}")
                        for j, asset in enumerate(extracted):
                            print(f"       Asset {j+1}: Type={asset.get('type')}, Source={asset.get('source')}")
                    except Exception as e:
                        print(f"     - ❌ Extraction failed: {e}")
                print()
        
        print("=" * 50)
        print("🔧 ASSET FIX TEST COMPLETE")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_assets_fix())