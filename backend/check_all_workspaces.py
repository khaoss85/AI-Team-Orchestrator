#!/usr/bin/env python3
"""Check all workspaces regardless of status"""

import os
import sys
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import supabase

# Get all workspaces
workspaces = supabase.table('workspaces').select('*').execute()

print(f"Total workspaces found: {len(workspaces.data)}\n")

for workspace in workspaces.data:
    created_at = datetime.fromisoformat(workspace['created_at'].replace('Z', '+00:00'))
    hours_active = (datetime.now(created_at.tzinfo) - created_at).total_seconds() / 3600
    
    print(f"Workspace: {workspace['name']}")
    print(f"  ID: {workspace['id']}")
    print(f"  Status: {workspace['status']}")
    print(f"  Created: {workspace['created_at']} ({hours_active:.1f} hours ago)")
    
    # Get task counts
    tasks = supabase.table('tasks').select('status').eq('workspace_id', workspace['id']).execute()
    task_counts = {}
    for task in tasks.data:
        status = task['status']
        task_counts[status] = task_counts.get(status, 0) + 1
    
    print(f"  Tasks: {task_counts}")
    
    # Get deliverables
    deliverables = supabase.table('deliverables').select('id, type, created_at').eq('workspace_id', workspace['id']).execute()
    print(f"  Deliverables: {len(deliverables.data)}")
    for d in deliverables.data:
        print(f"    - {d['type']} ({d['created_at']})")
    
    print()