#!/usr/bin/env python3
"""
Check current system state to understand where we are in the E2E flow
"""

import asyncio
import os
from dotenv import load_dotenv
from database import supabase
from datetime import datetime

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

async def check_system_state():
    print("🔍 CHECKING CURRENT SYSTEM STATE")
    print("=" * 50)
    
    # Check environment
    print("🔑 Environment:")
    print(f"  OPENAI_API_KEY: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Missing'}")
    print(f"  SUPABASE_URL: {'✅ Set' if os.getenv('SUPABASE_URL') else '❌ Missing'}")
    print()
    
    # Check recent workspaces
    print("🏢 Recent Workspaces:")
    try:
        response = await asyncio.to_thread(
            supabase.table("workspaces").select("*").order("created_at", desc=True).limit(3).execute
        )
        
        for i, workspace in enumerate(response.data):
            print(f"  {i+1}. {workspace['name']} (ID: {workspace['id']})")
            print(f"     Created: {workspace['created_at']}")
            print(f"     Status: {workspace.get('status', 'N/A')}")
            print()
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Check tasks by status
    print("📋 Tasks by Status:")
    try:
        statuses = ['pending', 'in_progress', 'completed', 'failed']
        for status in statuses:
            response = await asyncio.to_thread(
                supabase.table("tasks").select("*").eq("status", status).execute
            )
            count = len(response.data)
            print(f"  {status.upper()}: {count} tasks")
            
            if count > 0 and status in ['in_progress', 'completed']:
                # Show recent tasks of this status
                recent_tasks = response.data[:2]  # Show first 2
                for task in recent_tasks:
                    print(f"    - {task['name']} (Agent: {task.get('agent_id', 'None')})")
        print()
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Check active agents
    print("👥 Active Agents:")
    try:
        response = await asyncio.to_thread(
            supabase.table("agents").select("*").eq("status", "active").execute
        )
        
        print(f"  Total active agents: {len(response.data)}")
        
        # Group by workspace
        workspaces = {}
        for agent in response.data:
            ws_id = agent['workspace_id']
            if ws_id not in workspaces:
                workspaces[ws_id] = []
            workspaces[ws_id].append(agent)
        
        for ws_id, agents in list(workspaces.items())[:3]:  # Show first 3 workspaces
            print(f"  Workspace {ws_id}: {len(agents)} agents")
            for agent in agents[:2]:  # Show first 2 agents
                print(f"    - {agent['name']} ({agent['role']})")
        print()
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Check deliverables/assets
    print("📦 Deliverables/Assets:")
    try:
        # Check deliverables
        response = await asyncio.to_thread(
            supabase.table("deliverables").select("*").execute
        )
        print(f"  Deliverables: {len(response.data)}")
        
        # Check assets
        response = await asyncio.to_thread(
            supabase.table("assets").select("*").execute
        )
        print(f"  Assets: {len(response.data)}")
        
        # Check asset artifacts
        response = await asyncio.to_thread(
            supabase.table("asset_artifacts").select("*").execute
        )
        print(f"  Asset Artifacts: {len(response.data)}")
        
        if response.data:
            print("  Recent artifacts:")
            for artifact in response.data[:2]:
                print(f"    - {artifact.get('name', 'Unnamed')} ({artifact.get('status', 'N/A')})")
        print()
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    print("💡 RECOMMENDATIONS:")
    
    # Check if we have tasks that should be executed
    try:
        response = await asyncio.to_thread(
            supabase.table("tasks").select("*").eq("status", "in_progress").execute
        )
        
        if response.data:
            print(f"  ⚠️  Found {len(response.data)} tasks in_progress - these should be executing")
            print("  🔧 Recommend: Force task execution or check TaskExecutor")
        else:
            print("  ✅ No tasks stuck in_progress")
    except Exception as e:
        print(f"  ❌ Error checking tasks: {e}")
    
    # Check if we have any completed tasks
    try:
        response = await asyncio.to_thread(
            supabase.table("tasks").select("*").eq("status", "completed").execute
        )
        
        if response.data:
            print(f"  ✅ Found {len(response.data)} completed tasks - system is working!")
        else:
            print("  ❌ No completed tasks found - execution may be blocked")
    except Exception as e:
        print(f"  ❌ Error checking completed tasks: {e}")

if __name__ == "__main__":
    asyncio.run(check_system_state())