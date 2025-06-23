#!/usr/bin/env python3
"""
Debug asset enhancement issue
"""
import asyncio
import sys
import json
sys.path.append('.')

from deliverable_system.concrete_asset_extractor import ConcreteAssetExtractor
from deliverable_system.markup_processor import markup_processor
from database import supabase

async def debug_enhancement_issue():
    print('🔍 Debugging asset enhancement issue...')
    
    # Get the raw asset
    workspace_id = '06a6e9f1-ca46-4fcc-b0aa-a1ea6d8e73d7'
    all_tasks_response = supabase.table('tasks').select('*').eq('workspace_id', workspace_id).execute()
    
    if all_tasks_response.data:
        all_tasks = all_tasks_response.data
        completed_tasks = []
        
        for task in all_tasks:
            if task['id'] == 'b63e525b-231e-4bec-98e8-80b30a476c48':
                task_copy = task.copy()
                task_copy['status'] = 'completed'
                completed_tasks.append(task_copy)
            elif task.get('status') == 'completed':
                completed_tasks.append(task)
        
        if completed_tasks:
            extractor = ConcreteAssetExtractor()
            workspace_goal = 'Collect 25 high-quality leads from SaaS companies in Europe with 30% email open rate'
            
            raw_assets = await extractor.extract_concrete_assets(
                completed_tasks, workspace_goal, 'business_leads'
            )
            
            # Filter out metadata
            filtered_assets = {k: v for k, v in raw_assets.items() if not k.startswith('_')}
            
            # Find the email sequences asset
            email_asset = None
            for asset_id, asset in filtered_assets.items():
                if asset.get('asset_name') == 'business_email_sequences':
                    email_asset = asset
                    break
            
            if email_asset:
                print(f'✅ Found email asset: {email_asset.get("asset_name")}')
                print(f'📊 Asset structure: {list(email_asset.keys())}')
                
                # Test the enhancement logic step by step
                asset_data = email_asset.get("data", {})
                print(f'📊 Asset data keys: {list(asset_data.keys())}')
                
                # Step 1: Check rendered_html
                rendered_html = email_asset.get("rendered_html") or asset_data.get("rendered_html")
                print(f'🎨 Step 1 - Rendered HTML check: {bool(rendered_html)}')
                if rendered_html:
                    print(f'   HTML length: {len(rendered_html)}')
                    print('   ✅ Should return pre_rendered enhancement')
                    return
                
                # Step 2: Check structured content with markup processor
                if asset_data and isinstance(asset_data, dict):
                    print(f'📊 Step 2 - Processing with markup processor...')
                    processed_markup = markup_processor.process_deliverable_content(asset_data)
                    print(f'   Processed markup keys: {list(processed_markup.keys())}')
                    print(f'   has_structured_content: {processed_markup.get("has_structured_content")}')
                    
                    if processed_markup.get("has_structured_content"):
                        print('   ✅ Should return markup_processor enhancement')
                        return
                
                print('❌ Neither condition met - will use raw_fallback')
            else:
                print('❌ Email asset not found')

if __name__ == "__main__":
    asyncio.run(debug_enhancement_issue())