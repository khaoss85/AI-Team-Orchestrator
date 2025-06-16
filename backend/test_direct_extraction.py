#!/usr/bin/env python3
"""
Test diretto dell'estrazione assets dal final deliverable task
"""
import asyncio
import sys
import json
sys.path.append('.')

from deliverable_system.concrete_asset_extractor import ConcreteAssetExtractor
from database import supabase

async def test_direct_extraction():
    print('🔍 Testing direct asset extraction from final deliverable...')
    
    # Get the final deliverable task
    workspace_id = '06a6e9f1-ca46-4fcc-b0aa-a1ea6d8e73d7'
    tasks_response = supabase.table('tasks').select('*').eq('workspace_id', workspace_id).eq('name', '📦 Final Deliverable - B2B Outbound Sales Lists').execute()
    
    if not tasks_response.data:
        print('❌ Final deliverable task not found')
        return
    
    task = tasks_response.data[0]
    task['status'] = 'completed'  # Ensure it's treated as completed
    
    workspace_goal = 'Raccogliere 50 contatti ICP (CMO/CTO di aziende SaaS europee) e suggerire almeno 3 sequenze email da impostare su Hubspot'
    
    # Test the extraction
    extractor = ConcreteAssetExtractor()
    
    try:
        assets = await extractor.extract_concrete_assets(
            [task], workspace_goal, 'business_leads'
        )
        
        print(f'✅ Extraction completed: {type(assets)}')
        print(f'📊 Assets returned: {list(assets.keys())}')
        
        # Filter out metadata
        filtered_assets = {k: v for k, v in assets.items() if not k.startswith('_')}
        print(f'📋 Actual assets: {len(filtered_assets)}')
        
        for asset_id, asset in filtered_assets.items():
            if isinstance(asset, dict):
                print(f'   🎯 {asset_id}: {asset.get("asset_name", "Unknown")} (type: {asset.get("type", "Unknown")})')
            else:
                print(f'   ❌ {asset_id}: Invalid asset type {type(asset)}')
        
        if len(filtered_assets) == 0:
            print('❌ No assets extracted - there is still an issue')
        else:
            print(f'🎉 Success: {len(filtered_assets)} assets extracted!')
            
    except Exception as e:
        print(f'❌ Extraction failed: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct_extraction())