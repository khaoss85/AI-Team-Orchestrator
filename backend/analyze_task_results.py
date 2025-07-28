#!/usr/bin/env python3
"""
Analyze what the completed tasks actually produced
"""
import asyncio
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import supabase

async def analyze_task_results():
    workspace_id = '10aca193-3ca9-4200-ae19-6d430b64b3b0'
    
    print(f"Analyzing task results for workspace: {workspace_id}")
    print("=" * 80)
    
    # Get completed tasks
    result = supabase.table('tasks').select('id, name, result, status').eq('workspace_id', workspace_id).eq('status', 'completed').execute()
    
    completed_tasks = result.data
    print(f'Found {len(completed_tasks)} completed tasks\n')
    
    for i, task in enumerate(completed_tasks, 1):
        print(f"{i}. Task: {task['name']}")
        print(f"   ID: {task['id']}")
        print(f"   Status: {task['status']}")
        
        result = task.get('result', {})
        if isinstance(result, dict):
            print(f"   Result structure:")
            for key, value in result.items():
                if key == 'structured_content':
                    print(f"     - {key}: {type(value)} (len: {len(str(value))})")
                    if isinstance(value, dict):
                        print(f"       Keys: {list(value.keys())}")
                        # Check if it has assets
                        if 'assets' in value:
                            assets = value['assets']
                            print(f"       Assets: {len(assets) if isinstance(assets, list) else 'Not a list'}")
                            if isinstance(assets, list) and assets:
                                for j, asset in enumerate(assets[:3]):  # Show first 3 assets
                                    if isinstance(asset, dict):
                                        print(f"         Asset {j+1}: type={asset.get('type', 'Unknown')}, content_len={len(str(asset.get('content', '')))}")
                elif key == 'artifacts':
                    print(f"     - {key}: {type(value)} (len: {len(value) if isinstance(value, list) else 'N/A'})")
                    if isinstance(value, list) and value:
                        for j, artifact in enumerate(value[:3]):  # Show first 3 artifacts
                            if isinstance(artifact, dict):
                                print(f"         Artifact {j+1}: {list(artifact.keys())}")
                else:
                    print(f"     - {key}: {type(value)} (len: {len(str(value)) if isinstance(value, str) else 'N/A'})")
        
        print()
    
    # Check if there are any assets in the assets table
    print("CHECKING ASSETS TABLE:")
    print("-" * 40)
    
    assets_result = supabase.table('assets').select('*').eq('workspace_id', workspace_id).execute()
    assets = assets_result.data
    
    print(f"Found {len(assets)} assets in assets table")
    if assets:
        for i, asset in enumerate(assets, 1):
            print(f"{i}. Asset: {asset.get('name', 'Unnamed')}")
            print(f"   Type: {asset.get('type', 'Unknown')}")
            print(f"   Content length: {len(str(asset.get('content', '')))}")
            print(f"   Created: {asset.get('created_at', 'Unknown')}")
            print()
    
    # Let's examine one specific completed task result in detail
    if completed_tasks:
        print("DETAILED EXAMINATION OF FIRST COMPLETED TASK:")
        print("-" * 40)
        first_task = completed_tasks[0]
        result = first_task.get('result', {})
        print(f"Task: {first_task['name']}")
        print(f"Full result structure:")
        print(json.dumps(result, indent=2, default=str)[:2000] + "..." if len(json.dumps(result, indent=2, default=str)) > 2000 else json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(analyze_task_results())