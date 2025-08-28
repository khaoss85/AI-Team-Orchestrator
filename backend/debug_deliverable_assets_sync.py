#!/usr/bin/env python3
"""
Debug script per identificare il problema di sincronizzazione tra deliverables e assets.
Analizza il database e le funzioni di estrazione per identificare la root cause.
"""

import asyncio
import logging
import json
import os
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add current directory to path for imports
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def debug_deliverable_assets_sync():
    """Debug the sync issue between deliverables and assets"""
    
    workspace_id = "5975922e-c943-4d99-ad1d-25c01a81da7d"
    
    print(f"\n🔍 DEBUG: Deliverable-Asset Sync Issue Analysis")
    print(f"Workspace ID: {workspace_id}")
    print("=" * 80)
    
    try:
        # Import database functions
        from database import get_deliverables, list_tasks
        
        # 1. Check deliverables in database
        print("\n1️⃣ CHECKING DELIVERABLES TABLE:")
        deliverables = await get_deliverables(workspace_id)
        print(f"   Found {len(deliverables)} deliverables")
        
        for i, deliverable in enumerate(deliverables, 1):
            print(f"   Deliverable {i}:")
            print(f"     - ID: {deliverable.get('id')}")
            print(f"     - Title: {deliverable.get('title')}")
            print(f"     - Type: {deliverable.get('type')}")
            print(f"     - Status: {deliverable.get('status')}")
            print(f"     - Goal ID: {deliverable.get('goal_id')}")
            print(f"     - Content type: {type(deliverable.get('content'))}")
            
            if isinstance(deliverable.get('content'), dict):
                content_keys = list(deliverable['content'].keys())[:5]  # First 5 keys
                print(f"     - Content keys: {content_keys}")
            elif isinstance(deliverable.get('content'), str):
                content_preview = deliverable['content'][:100]
                print(f"     - Content preview: {content_preview}...")
            print()
        
        # 2. Check completed tasks
        print("\n2️⃣ CHECKING COMPLETED TASKS:")
        tasks = await list_tasks(workspace_id)
        completed_tasks = [t for t in tasks if t.get("status") == "completed"]
        print(f"   Found {len(completed_tasks)} completed tasks")
        
        for i, task in enumerate(completed_tasks, 1):
            print(f"   Task {i}:")
            print(f"     - ID: {task.get('id')}")
            print(f"     - Name: {task.get('name')}")
            print(f"     - Goal ID: {task.get('goal_id')}")
            print(f"     - Result type: {type(task.get('result'))}")
            
            if task.get('result'):
                if isinstance(task['result'], dict):
                    result_keys = list(task['result'].keys())[:5]
                    print(f"     - Result keys: {result_keys}")
                elif isinstance(task['result'], str):
                    result_preview = task['result'][:100]
                    print(f"     - Result preview: {result_preview}...")
            print()
        
        # 3. Test ConcreteAssetExtractor directly
        print("\n3️⃣ TESTING CONCRETE ASSET EXTRACTOR:")
        try:
            from deliverable_system.concrete_asset_extractor import concrete_asset_extractor
            
            # Test batch extraction on completed tasks
            assets_dict = await concrete_asset_extractor.extract_assets_from_task_batch(completed_tasks)
            print(f"   ConcreteAssetExtractor returned: {len(assets_dict)} task-asset mappings")
            
            total_assets = 0
            for task_id, task_assets in assets_dict.items():
                print(f"   Task {task_id}: {len(task_assets)} assets")
                total_assets += len(task_assets)
                
                for j, asset in enumerate(task_assets):
                    print(f"     Asset {j+1}: Type={asset.get('type')}, Source={asset.get('source')}")
            
            print(f"   Total assets extracted: {total_assets}")
            
        except Exception as e:
            print(f"   ❌ Error testing ConcreteAssetExtractor: {e}")
        
        # 4. Test UnifiedAssetManager directly  
        print("\n4️⃣ TESTING UNIFIED ASSET MANAGER:")
        try:
            from routes.unified_assets import unified_asset_manager
            
            # Test the main method
            result = await unified_asset_manager.get_workspace_assets(workspace_id)
            print(f"   UnifiedAssetManager returned:")
            print(f"     - Asset count: {result.get('asset_count')}")
            print(f"     - Data source: {result.get('data_source')}")
            print(f"     - Assets keys: {list(result.get('assets', {}).keys())}")
            
            # Detailed asset analysis
            for asset_key, asset_data in result.get('assets', {}).items():
                print(f"     Asset '{asset_key}':")
                print(f"       - Name: {asset_data.get('name')}")
                print(f"       - Type: {asset_data.get('type')}")
                print(f"       - Versions: {asset_data.get('versions')}")
                print(f"       - Content keys: {list(asset_data.get('content', {}).keys())}")
                
        except Exception as e:
            print(f"   ❌ Error testing UnifiedAssetManager: {e}")
            import traceback
            traceback.print_exc()
        
        # 5. Test individual deliverable asset extraction
        print("\n5️⃣ TESTING DELIVERABLE CONTENT EXTRACTION:")
        if deliverables:
            for deliverable in deliverables[:2]:  # Test first 2 deliverables
                print(f"   Testing deliverable: {deliverable.get('title')}")
                
                try:
                    # Test the extraction method used in UnifiedAssetManager
                    content = deliverable.get('content', {})
                    deliverable_type = deliverable.get('type', 'unknown')
                    title = deliverable.get('title', 'Unknown')
                    
                    if isinstance(content, dict):
                        extracted_assets = unified_asset_manager._extract_assets_from_deliverable_content(
                            content, deliverable_type, title
                        )
                        print(f"     Extracted {len(extracted_assets)} assets from deliverable content")
                        
                        for asset in extracted_assets:
                            print(f"       - Type: {asset.get('type')}, Source: {asset.get('source')}")
                    else:
                        print(f"     Content is not dict, type: {type(content)}")
                        
                except Exception as e:
                    print(f"     ❌ Error extracting from deliverable: {e}")
        
        print("\n" + "=" * 80)
        print("🔍 DEBUG ANALYSIS COMPLETE")
        
        # Summary analysis
        print(f"\n📊 SUMMARY:")
        print(f"   Deliverables in DB: {len(deliverables)}")
        print(f"   Completed tasks: {len(completed_tasks)}")
        print(f"   Assets returned by API: {result.get('asset_count', 'Unknown')}")
        
        # Identify potential issues
        if len(deliverables) > 0 and result.get('asset_count', 0) <= 1:
            print(f"\n🚨 ROOT CAUSE IDENTIFIED:")
            print(f"   - Database has {len(deliverables)} deliverables")
            print(f"   - But unified assets API returns only {result.get('asset_count', 0)} assets")
            print(f"   - Issue likely in:")
            print(f"     1. ConcreteAssetExtractor not processing deliverable content properly")
            print(f"     2. Deliverable content format not matching expected structure")
            print(f"     3. Fallback extraction from deliverables table not working")
        
    except Exception as e:
        print(f"❌ Critical error in debug analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_deliverable_assets_sync())