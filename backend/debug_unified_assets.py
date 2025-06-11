#!/usr/bin/env python3
"""Debug script to check unified assets API for a specific workspace."""

import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from database import supabase, list_tasks
from deliverable_system.concrete_asset_extractor import ConcreteAssetExtractor
from models import TaskStatus

WORKSPACE_ID = "2d8d4059-aaee-4980-80c8-aa11269aa85d"

async def debug_unified_assets():
    """Debug why unified assets API returns 0 assets."""
    
    print(f"\n=== Debugging Unified Assets for Workspace {WORKSPACE_ID} ===\n")
    
    # 1. Check all tasks in workspace
    print("1. Fetching all tasks in workspace...")
    all_tasks = await list_tasks(WORKSPACE_ID)
    print(f"   Total tasks found: {len(all_tasks)}")
    
    # 2. Check completed tasks
    completed_tasks = [t for t in all_tasks if t.get('status') == TaskStatus.COMPLETED.value]
    print(f"\n2. Completed tasks: {len(completed_tasks)}")
    
    if completed_tasks:
        for i, task in enumerate(completed_tasks[:5]):  # Show first 5
            print(f"\n   Task {i+1}:")
            print(f"   - ID: {task.get('id')}")
            print(f"   - Name: {task.get('name')}")
            print(f"   - Status: {task.get('status')}")
            print(f"   - Has result: {'result' in task and task['result'] is not None}")
            if 'result' in task and task['result']:
                result_type = type(task['result']).__name__
                print(f"   - Result type: {result_type}")
                if isinstance(task['result'], dict):
                    print(f"   - Result keys: {list(task['result'].keys())}")
    
    # 3. Test ConcreteAssetExtractor directly
    print("\n3. Testing ConcreteAssetExtractor...")
    extractor = ConcreteAssetExtractor()
    
    # Extract assets from completed tasks
    all_assets = {}
    for task in completed_tasks:
        try:
            assets = extractor.extract_assets_from_task(task)
            if assets:
                print(f"\n   Task '{task.get('name')}' produced {len(assets)} assets:")
                for asset_key, asset_data in assets.items():
                    print(f"   - {asset_key}: {asset_data.get('type', 'unknown')}")
                all_assets.update(assets)
        except Exception as e:
            print(f"\n   ERROR extracting from task '{task.get('name')}': {e}")
    
    print(f"\n   Total assets extracted: {len(all_assets)}")
    
    # 4. Check the specific SQL query used by the API
    print("\n4. Running API query directly...")
    try:
        # This mimics what the API does
        query = supabase.table("tasks").select("*").eq("workspace_id", WORKSPACE_ID)
        query = query.in_("status", [TaskStatus.COMPLETED.value, TaskStatus.APPROVED.value])
        query = query.order("created_at", desc=True)
        
        result = query.execute()
        api_tasks = result.data if result.data else []
        print(f"   API query returned: {len(api_tasks)} tasks")
        
        # Check if any have rich content
        rich_content_tasks = [t for t in api_tasks if t.get('result') and isinstance(t['result'], dict) and 'rich_content' in t['result']]
        print(f"   Tasks with rich_content: {len(rich_content_tasks)}")
        
    except Exception as e:
        print(f"   ERROR running API query: {e}")
    
    # 5. Check for any issues with task filtering
    print("\n5. Checking task filtering logic...")
    
    # Check different status values
    for status in [TaskStatus.COMPLETED.value, TaskStatus.APPROVED.value, TaskStatus.IN_PROGRESS.value]:
        status_tasks = [t for t in all_tasks if t.get('status') == status]
        print(f"   Tasks with status '{status}': {len(status_tasks)}")
    
    # 6. Sample task result structure
    if completed_tasks:
        print("\n6. Sample completed task result structure:")
        sample_task = completed_tasks[0]
        if sample_task.get('result'):
            print(json.dumps(sample_task['result'], indent=2)[:500])  # First 500 chars

if __name__ == "__main__":
    asyncio.run(debug_unified_assets())