#!/usr/bin/env python3
"""
Debug script to inspect the actual deliverable structure and task results
"""
import json
import sys
sys.path.append('.')

from database import supabase

def inspect_task_results():
    print('🔍 Inspecting task detailed results...')
    
    # Get the final deliverable task
    workspace_id = '06a6e9f1-ca46-4fcc-b0aa-a1ea6d8e73d7'
    tasks_response = supabase.table('tasks').select('*').eq('workspace_id', workspace_id).eq('name', '📦 Final Deliverable - B2B Outbound Sales Lists').execute()
    
    if not tasks_response.data:
        print('❌ Final deliverable task not found')
        return
    
    task = tasks_response.data[0]
    print(f'📋 Task status: {task["status"]}')
    
    # Check detailed results
    detailed_results = task.get('detailed_results_json')
    if detailed_results:
        try:
            if isinstance(detailed_results, str):
                parsed = json.loads(detailed_results)
            else:
                parsed = detailed_results
            
            print(f'📊 Detailed results keys: {list(parsed.keys())}')
            
            # Check for deliverable_assets
            if 'deliverable_assets' in parsed:
                assets = parsed['deliverable_assets']
                print(f'📦 Found {len(assets)} deliverable assets:')
                
                for i, asset in enumerate(assets):
                    print(f'  Asset {i+1}: {asset.get("task_name", "Unknown")}')
                    
                    # Check if this asset has detailed results
                    asset_detailed = asset.get('detailed_results_json')
                    if asset_detailed:
                        print(f'    📝 Has detailed_results_json: {type(asset_detailed)}')
                        if isinstance(asset_detailed, str) and len(asset_detailed) > 100:
                            try:
                                asset_data = json.loads(asset_detailed)
                                print(f'    📊 Asset data keys: {list(asset_data.keys())}')
                                
                                # Look for contact/sequence data
                                if 'contacts' in asset_data:
                                    contacts = asset_data['contacts']
                                    print(f'    👥 Found {len(contacts)} contacts')
                                    if contacts:
                                        print(f'    📋 First contact keys: {list(contacts[0].keys()) if isinstance(contacts[0], dict) else "Not dict"}')
                                
                                if 'email_sequences' in asset_data:
                                    sequences = asset_data['email_sequences']
                                    print(f'    📧 Found {len(sequences)} email sequences')
                                    if sequences:
                                        print(f'    📋 First sequence keys: {list(sequences[0].keys()) if isinstance(sequences[0], dict) else "Not dict"}')
                                        
                                if 'sequences' in asset_data:
                                    sequences = asset_data['sequences']
                                    print(f'    📧 Found {len(sequences)} sequences (alt key)')
                                    
                                if 'structured_content' in asset_data:
                                    structured = asset_data['structured_content']
                                    print(f'    🏗️ Structured content keys: {list(structured.keys()) if isinstance(structured, dict) else "Not dict"}')
                                    
                            except json.JSONDecodeError as e:
                                print(f'    ❌ JSON decode error: {e}')
                        else:
                            print(f'    📝 Raw detailed results: {asset_detailed[:200]}...')
                    else:
                        print(f'    ❌ No detailed_results_json')
                        
        except json.JSONDecodeError as e:
            print(f'❌ Error parsing task detailed results: {e}')
    else:
        print('❌ No detailed_results_json in final deliverable task')
    
    # Also check all completed tasks for any with contact/sequence data
    print('\n🔍 Checking all completed tasks for contact/sequence data...')
    all_tasks = supabase.table('tasks').select('*').eq('workspace_id', workspace_id).execute()
    
    print(f'📊 Total tasks in workspace: {len(all_tasks.data)}')
    completed_tasks = [t for t in all_tasks.data if t.get('status') == 'completed']
    print(f'📊 Completed tasks: {len(completed_tasks)}')
    
    # Check each task
    for task in all_tasks.data:
        task_name = task.get('name', 'Unknown')
        task_status = task.get('status', 'Unknown')
        detailed = task.get('detailed_results_json')
        
        print(f'\n📋 Task: {task_name} ({task_status})')
        
        if detailed:
            try:
                if isinstance(detailed, str):
                    task_data = json.loads(detailed)
                else:
                    task_data = detailed
                    
                print(f'  📊 Task data keys: {list(task_data.keys())}')
                
                if 'contacts' in task_data:
                    contacts = task_data['contacts']
                    print(f'  👥 {len(contacts)} contacts found')
                    
                if 'email_sequences' in task_data or 'sequences' in task_data:
                    sequences = task_data.get('email_sequences') or task_data.get('sequences', [])
                    print(f'  📧 {len(sequences)} sequences found')
                    
                if 'structured_content' in task_data:
                    structured = task_data['structured_content']
                    if isinstance(structured, dict):
                        print(f'  🏗️ Structured content keys: {list(structured.keys())}')
                        if 'sequences' in structured:
                            print(f'  📧 {len(structured["sequences"])} sequences in structured content')
                    
            except json.JSONDecodeError:
                print(f'  ❌ Invalid JSON in detailed_results_json')
        else:
            print(f'  ❌ No detailed_results_json')

if __name__ == "__main__":
    inspect_task_results()