#!/usr/bin/env python3
"""
Inspect deliverable content to understand why they're all grouped as 'business_document'
"""

import asyncio
import logging
import os
import sys
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def inspect_deliverable_content():
    """Inspect the actual content of deliverables to understand grouping issue"""
    
    workspace_id = "5975922e-c943-4d99-ad1d-25c01a81da7d"
    
    print(f"\n🔍 INSPECTING DELIVERABLE CONTENT")
    print(f"Workspace ID: {workspace_id}")
    print("=" * 60)
    
    try:
        # Import database functions
        from database import get_deliverables
        from routes.unified_assets import unified_asset_manager
        
        # Get all deliverables
        deliverables = await get_deliverables(workspace_id)
        print(f"✓ Found {len(deliverables)} deliverables")
        
        for i, deliverable in enumerate(deliverables, 1):
            print(f"\n📦 DELIVERABLE {i}:")
            print(f"   Title: {deliverable.get('title', 'No title')}")
            print(f"   Type: {deliverable.get('type', 'No type')}")
            print(f"   ID: {deliverable.get('id', 'No ID')}")
            
            # Content analysis
            content = deliverable.get('content', {})
            print(f"   Content type: {type(content)}")
            
            if isinstance(content, dict):
                print(f"   Content keys: {list(content.keys())}")
                
                # Show first few values to understand structure
                for key, value in list(content.items())[:3]:
                    if isinstance(value, str):
                        preview = value[:100] + "..." if len(value) > 100 else value
                        print(f"     {key}: {preview}")
                    elif isinstance(value, list):
                        print(f"     {key}: [list with {len(value)} items]")
                        if value and isinstance(value[0], dict):
                            print(f"       First item keys: {list(value[0].keys())}")
                    elif isinstance(value, dict):
                        print(f"     {key}: [dict with keys: {list(value.keys())}]")
                    else:
                        print(f"     {key}: {type(value)} - {str(value)[:50]}")
                
                # Test asset extraction for this specific deliverable
                print(f"   \n🔧 TESTING ASSET EXTRACTION:")
                try:
                    extracted_assets = unified_asset_manager._extract_assets_from_deliverable_content(
                        content, deliverable.get('type', 'unknown'), deliverable.get('title', 'Unknown')
                    )
                    
                    print(f"     Extracted {len(extracted_assets)} assets:")
                    for j, asset in enumerate(extracted_assets):
                        asset_type = asset.get('type', 'unknown')
                        asset_source = asset.get('source', 'unknown')
                        asset_name = asset.get('asset_name', 'unknown')
                        
                        print(f"       Asset {j+1}: type='{asset_type}', source='{asset_source}', name='{asset_name}'")
                        
                        # Test semantic grouping for this asset
                        group_key = unified_asset_manager._create_semantic_group_key(asset_type, deliverable.get('title', ''))
                        display_name = unified_asset_manager._create_display_name(asset_type, deliverable.get('title', ''))
                        
                        print(f"                  group_key='{group_key}', display_name='{display_name}'")
                        
                except Exception as e:
                    print(f"     ❌ Asset extraction failed: {e}")
            
            print(f"   ---")
        
        print(f"\n📊 ANALYSIS SUMMARY:")
        print(f"   Total deliverables: {len(deliverables)}")
        print(f"   All seem to get grouped as 'business_document' because:")
        print(f"   1. Asset type from _infer_asset_type_from_name() defaults to 'business_document' or 'business_asset'")
        print(f"   2. Titles don't match specific patterns in _create_semantic_group_key()")
        
        # Show the titles for pattern analysis
        print(f"\n📝 TITLES FOR PATTERN ANALYSIS:")
        for i, deliverable in enumerate(deliverables, 1):
            title = deliverable.get('title', 'No title')
            print(f"   {i}. '{title}'")
            
            # Test what _create_semantic_group_key would return for this title
            test_group_key = unified_asset_manager._create_semantic_group_key('business_document', title)
            print(f"      → Would group as: '{test_group_key}'")
        
    except Exception as e:
        print(f"❌ Inspection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(inspect_deliverable_content())