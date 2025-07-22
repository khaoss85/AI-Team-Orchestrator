#!/usr/bin/env python3
"""
Quick check of the most recent task status
"""

import asyncio
import logging
from database import supabase

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

async def quick_check():
    # Get most recent workspace
    response = await asyncio.to_thread(
        supabase.table("workspaces").select("*").order("created_at", desc=True).limit(1).execute
    )
    
    if not response.data:
        print("No workspaces found")
        return
        
    workspace = response.data[0]
    workspace_id = workspace['id']
    print(f"Latest workspace: {workspace['name']} ({workspace_id})")
    
    # Get tasks for this workspace
    response = await asyncio.to_thread(
        supabase.table("tasks").select("*").eq("workspace_id", workspace_id).execute
    )
    
    tasks = response.data
    print(f"Tasks in workspace: {len(tasks)}")
    
    for task in tasks:
        print(f"  Task: {task['name']} | Status: {task['status']} | Agent: {task.get('agent_id', 'None')}")
    
    # Get agents for this workspace  
    response = await asyncio.to_thread(
        supabase.table("agents").select("*").eq("workspace_id", workspace_id).execute
    )
    
    agents = response.data
    print(f"Agents in workspace: {len(agents)}")
    
    for agent in agents:
        print(f"  Agent: {agent['name']} | Status: {agent['status']} | Role: {agent['role']}")

if __name__ == "__main__":
    asyncio.run(quick_check())