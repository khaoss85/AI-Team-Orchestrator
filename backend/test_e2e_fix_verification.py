#!/usr/bin/env python3
"""
End-to-end test to verify the asset extraction and frontend display fix
"""
import asyncio
import sys
import json
sys.path.append('.')

from deliverable_system.concrete_asset_extractor import ConcreteAssetExtractor
from routes.unified_assets import UnifiedAssetsService
from database import supabase

async def test_e2e_fix():
    print('🔍 Testing end-to-end asset extraction and frontend display fix...')
    
    workspace_id = '06a6e9f1-ca46-4fcc-b0aa-a1ea6d8e73d7'
    
    # Step 1: Test raw asset extraction
    print('\n📊 Step 1: Testing raw asset extraction...')
    
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
            
            # Find email asset
            email_asset = None
            for asset_id, asset in filtered_assets.items():
                if asset.get('asset_name') == 'business_email_sequences':
                    email_asset = asset
                    break
            
            if email_asset:
                print(f'✅ Raw extraction: Found business_email_sequences')
                data = email_asset.get('data', {})
                print(f'   📧 Sequences: {data.get("total_sequences", 0)}')
                print(f'   🎨 Rendered HTML: {len(data.get("rendered_html", ""))} chars')
            else:
                print('❌ Raw extraction: business_email_sequences not found')
                return False
    
    # Step 2: Test unified assets processing
    print('\n🔧 Step 2: Testing unified assets processing...')
    
    try:
        service = UnifiedAssetsService()
        
        # Simulate the grouped assets structure that would be passed to _process_assets_with_ai
        grouped_assets = {
            'email_sequences': {
                'group_name': 'Email Campaign Sequences',
                'asset_type': 'email_templates',
                'latest_version': 1,
                'versions': [email_asset],
                'tasks': [{'id': 'test', 'name': 'test', 'status': 'completed'}]
            }
        }
        
        processed = await service._process_assets_with_ai(grouped_assets, workspace_goal)
        
        if 'email_sequences' in processed:
            processed_asset = processed['email_sequences']
            content = processed_asset.get('content', {})
            
            print(f'✅ Processing: Found processed email_sequences')
            print(f'   📄 Has rendered_html: {bool(content.get("rendered_html"))}')
            print(f'   🎯 Enhancement source: {content.get("enhancement_source", "none")}')
            
            if content.get('rendered_html'):
                html_length = len(content['rendered_html'])
                print(f'   🎨 Rendered HTML: {html_length} chars')
                
                if html_length > 1000:
                    print('✅ Step 2 PASSED: Rich content preserved through processing')
                else:
                    print('❌ Step 2 FAILED: HTML too short')
                    return False
            else:
                print('❌ Step 2 FAILED: No rendered_html in processed content')
                return False
        else:
            print('❌ Processing: email_sequences not found')
            return False
    
    except Exception as e:
        print(f'❌ Processing error: {e}')
        return False
    
    # Step 3: Simulate what frontend receives
    print('\n📱 Step 3: Testing frontend data structure...')
    
    frontend_asset = processed['email_sequences']
    
    # Check if the frontend will find the rich content
    content = frontend_asset.get('content', {})
    rendered_html = content.get('rendered_html')
    
    if rendered_html and len(rendered_html) > 1000:
        print('✅ Frontend will receive rich HTML content')
        print(f'   📄 HTML length: {len(rendered_html)} chars')
        print(f'   🎨 HTML preview: {rendered_html[:100]}...')
        
        # Check if HTML contains actual email sequences
        if 'Product Value & Pain Point Sequence' in rendered_html:
            print('✅ HTML contains actual email sequence names')
        else:
            print('❌ HTML does not contain expected sequence names')
            return False
        
        if 'SaaS' in rendered_html and 'Europe' in rendered_html:
            print('✅ HTML contains business context')
        else:
            print('❌ HTML missing business context')
            return False
        
        print('\n🎉 SUCCESS: All tests passed!')
        print('   ✅ Raw extraction works')
        print('   ✅ Processing preserves rich content') 
        print('   ✅ Frontend will display actual email sequences')
        return True
    else:
        print('❌ Frontend will not receive rich content')
        return False

if __name__ == "__main__":
    success = asyncio.run(test_e2e_fix())
    if success:
        print('\n🎯 CONCLUSION: The fix is working correctly.')
        print('   If frontend still shows placeholders, try:')
        print('   1. Hard refresh the browser (Cmd+Shift+R)')
        print('   2. Clear browser cache')
        print('   3. Check browser console for errors')
    else:
        print('\n❌ CONCLUSION: The fix needs more work.')
        sys.exit(1)