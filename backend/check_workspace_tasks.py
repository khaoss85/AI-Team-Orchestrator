#!/usr/bin/env python3
"""Quick check of workspace tasks without dependencies."""

import os
from supabase import create_client, Client

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

WORKSPACE_ID = "2d8d4059-aaee-4980-80c8-aa11269aa85d"

# Get all tasks for workspace
result = supabase.table("tasks").select("*").eq("workspace_id", WORKSPACE_ID).execute()
tasks = result.data if result.data else []

print(f"\n=== Workspace {WORKSPACE_ID} Tasks ===")
print(f"Total tasks: {len(tasks)}")

# Group by status
status_groups = {}
for task in tasks:
    status = task.get('status', 'unknown')
    if status not in status_groups:
        status_groups[status] = []
    status_groups[status].append(task)

print("\nTasks by status:")
for status, task_list in status_groups.items():
    print(f"  {status}: {len(task_list)}")
    
# Show completed tasks details
if 'completed' in status_groups:
    print(f"\nCompleted tasks ({len(status_groups['completed'])}):")
    for i, task in enumerate(status_groups['completed'][:5]):  # Show first 5
        print(f"\n  Task {i+1}:")
        print(f"    ID: {task.get('id')}")
        print(f"    Name: {task.get('name')}")
        print(f"    Has result: {'result' in task and task['result'] is not None}")
        if task.get('result'):
            print(f"    Result type: {type(task['result']).__name__}")
            if isinstance(task['result'], dict):
                print(f"    Result keys: {list(task['result'].keys())[:5]}")  # First 5 keys
                if 'rich_content' in task['result']:
                    print(f"    Has rich_content: Yes")
                if 'detailed_results_json' in task['result']:
                    print(f"    Has detailed_results_json: Yes")
else:
    print("\nNo completed tasks found!")

# Check for approved tasks (which don't exist in the enum)
approved_count = len([t for t in tasks if t.get('status') == 'approved'])
if approved_count > 0:
    print(f"\nWARNING: Found {approved_count} tasks with 'approved' status - this is not a valid TaskStatus enum value!")