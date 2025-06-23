#!/usr/bin/env python3
"""
Test del nuovo sistema di estrazione multi-source
"""
import asyncio
import sys
import json
sys.path.append('.')

from concrete_asset_extractor_refactored import multi_source_extractor

async def test_refactored_extraction():
    print('🎯 Testing REFACTORED multi-source asset extraction...')
    
    workspace_id = '06a6e9f1-ca46-4fcc-b0aa-a1ea6d8e73d7'
    workspace_goal = 'Raccogliere 50 contatti ICP (CMO/CTO di aziende SaaS europee) e suggerire almeno 3 sequenze email da impostare su Hubspot'
    
    try:
        assets = await multi_source_extractor.extract_assets(workspace_id, workspace_goal)
        
        print(f'✅ Extraction completed: {type(assets)}')
        print(f'📊 Assets returned: {list(assets.keys())}')
        
        # Filter out metadata
        filtered_assets = {k: v for k, v in assets.items() if not k.startswith('_')}
        print(f'📋 Actual assets: {len(filtered_assets)}')
        
        for asset_id, asset in filtered_assets.items():
            if isinstance(asset, dict):
                asset_data = asset.get("data", {})
                print(f'   🎯 {asset_id}: {asset.get("asset_name", "Unknown")} (type: {asset.get("type", "Unknown")})')
                print(f'      - Source: {asset.get("source", "Unknown")}')
                print(f'      - Has contacts: {asset_data.get("has_detailed_contacts", False)}')
                print(f'      - Contact count: {len(asset_data.get("contacts", []))}')
                print(f'      - Has sequences: {asset_data.get("has_detailed_sequences", False)}')
                print(f'      - Sequence count: {len(asset_data.get("sequences", []))}')
                
                if asset_data.get('contacts'):
                    sample_contact = asset_data['contacts'][0]
                    print(f'      - Sample contact: {sample_contact.get("name")} at {sample_contact.get("company")}')
                    
                if asset_data.get('sequences'):
                    sample_sequence = asset_data['sequences'][0]
                    print(f'      - Sample sequence: {sample_sequence.get("name")}')
            else:
                print(f'   ❌ {asset_id}: Invalid asset type {type(asset)}')
        
        # Show metadata
        metadata = assets.get('_metadata', {})
        print(f'\n📊 Metadata:')
        print(f'   - Sources used: {metadata.get("extraction_sources", [])}')
        print(f'   - Task analysis: {metadata.get("workspace_analysis", {})}')
        print(f'   - Architectural compliance: {metadata.get("architectural_compliance", {})}')
        
        if len(filtered_assets) == 0:
            print('❌ No assets extracted - there is still an issue')
        else:
            print(f'🎉 Success: {len(filtered_assets)} assets extracted!')
            
    except Exception as e:
        print(f'❌ Extraction failed: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_refactored_extraction())