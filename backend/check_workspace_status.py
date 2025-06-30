#!/usr/bin/env python3
"""
Check current workspace status
"""

import asyncio
from database import supabase

async def check_workspace_status():
    """Check the current status of all workspaces"""
    
    print("🔍 Checking workspace status...")
    
    # Get all workspaces
    workspaces_response = supabase.table('workspaces').select('id, name, status, goal').execute()
    
    if not workspaces_response.data:
        print("No workspaces found")
        return
    
    workspaces = workspaces_response.data
    print(f"\nFound {len(workspaces)} workspaces:")
    
    status_counts = {}
    for workspace in workspaces:
        status = workspace.get('status', 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"  📁 {workspace.get('name', 'Unnamed')} ({workspace['id'][:8]}...)")
        print(f"     Status: {status}")
        print(f"     Goal: {workspace.get('goal', 'No goal set')[:100]}...")
        print()
    
    print("📊 Status Summary:")
    for status, count in status_counts.items():
        print(f"  {status}: {count} workspaces")

if __name__ == "__main__":
    asyncio.run(check_workspace_status())