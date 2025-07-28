#!/usr/bin/env python3
"""
Examine the actual content of completed tasks
"""
import asyncio
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import supabase

async def examine_task_content():
    workspace_id = '10aca193-3ca9-4200-ae19-6d430b64b3b0'
    
    print(f"Examining task content for workspace: {workspace_id}")
    print("=" * 80)
    
    # Get one specific completed task
    task_id = 'cede729a-599c-4f02-9f1d-3822d0be09ed'  # Case Study Document
    
    result = supabase.table('tasks').select('*').eq('id', task_id).execute()
    
    if not result.data:
        print("Task not found!")
        return
    
    task = result.data[0]
    print(f"Task: {task['name']}")
    print(f"Status: {task['status']}")
    print()
    
    task_result = task.get('result', {})
    
    print("TASK RESULT STRUCTURE:")
    print("-" * 40)
    
    if isinstance(task_result, dict):
        for key, value in task_result.items():
            print(f"{key}: {type(value)}")
            if key == 'structured_content':
                print(f"  Content preview: {str(value)[:500]}...")
                print()
                
                # Try to parse structured_content as JSON if it's a string
                if isinstance(value, str):
                    try:
                        parsed_content = json.loads(value)
                        print("  Parsed structured_content as JSON:")
                        print(f"    Type: {type(parsed_content)}")
                        if isinstance(parsed_content, dict):
                            print(f"    Keys: {list(parsed_content.keys())}")
                            if 'assets' in parsed_content:
                                assets = parsed_content['assets']
                                print(f"    Assets found: {len(assets) if isinstance(assets, list) else 'Not a list'}")
                                if isinstance(assets, list):
                                    for i, asset in enumerate(assets[:2]):  # Show first 2
                                        if isinstance(asset, dict):
                                            print(f"      Asset {i+1}:")
                                            print(f"        Type: {asset.get('type', 'Unknown')}")
                                            print(f"        Name: {asset.get('name', 'Unknown')}")
                                            content = asset.get('content', '')
                                            print(f"        Content length: {len(str(content))}")
                                            print(f"        Content preview: {str(content)[:200]}...")
                        print()
                    except json.JSONDecodeError:
                        print("  Not valid JSON")
            elif key == 'result':
                print(f"  Result content: {str(value)[:300]}...")
                print()
    
    # Check if there are deliverables for this workspace
    print("CHECKING DELIVERABLES TABLE:")
    print("-" * 40)
    
    try:
        deliverables_result = supabase.table('deliverables').select('*').eq('workspace_id', workspace_id).execute()
        deliverables = deliverables_result.data
        
        print(f"Found {len(deliverables)} deliverables")
        if deliverables:
            for i, deliverable in enumerate(deliverables, 1):
                print(f"{i}. Deliverable: {deliverable.get('name', 'Unnamed')}")
                print(f"   Type: {deliverable.get('type', 'Unknown')}")
                print(f"   Content length: {len(str(deliverable.get('content', '')))}")
                print(f"   Created: {deliverable.get('created_at', 'Unknown')}")
                print()
    except Exception as e:
        print(f"Error checking deliverables: {e}")

if __name__ == "__main__":
    asyncio.run(examine_task_content())