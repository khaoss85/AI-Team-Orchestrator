#!/usr/bin/env python3

import asyncio
import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Add the backend directory to Python path
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

# Load environment variables
load_dotenv('/Users/pelleri/Documents/ai-team-orchestrator/backend/.env')

async def check_database_status():
    """Check the overall database status"""
    
    # Initialize Supabase client
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("ERROR: Missing Supabase credentials in .env file")
        return
        
    supabase: Client = create_client(supabase_url, supabase_key)
    
    try:
        # Check workspaces
        print("🔍 Checking workspaces...")
        workspaces_result = supabase.table("workspaces")\
            .select("id, name, description, created_at")\
            .order("created_at", desc=True)\
            .limit(5)\
            .execute()
        
        print(f"📊 Found {len(workspaces_result.data)} workspaces")
        for workspace in workspaces_result.data:
            print(f"  - {workspace.get('name', 'N/A')} (ID: {workspace.get('id')})")
        
        # Check agents
        print("\n🤖 Checking agents...")
        agents_result = supabase.table("agents")\
            .select("id, name, role, seniority, personality_traits, hard_skills, soft_skills, workspace_id, created_at")\
            .order("created_at", desc=True)\
            .limit(5)\
            .execute()
        
        print(f"📊 Found {len(agents_result.data)} agents")
        for agent in agents_result.data:
            print(f"  - {agent.get('name', 'N/A')} ({agent.get('role', 'N/A')}) - Workspace: {agent.get('workspace_id')}")
            print(f"    Personality: {type(agent.get('personality_traits'))}: {agent.get('personality_traits')}")
            print(f"    Hard Skills: {type(agent.get('hard_skills'))}: {agent.get('hard_skills')}")
            print(f"    Soft Skills: {type(agent.get('soft_skills'))}: {agent.get('soft_skills')}")
        
        # Check team_proposals table structure
        print("\n📋 Checking team proposals...")
        proposals_result = supabase.table("team_proposals")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(5)\
            .execute()
        
        print(f"📊 Found {len(proposals_result.data)} team proposals")
        
        # Check tasks
        print("\n📋 Checking tasks...")
        tasks_result = supabase.table("tasks")\
            .select("id, title, status, workspace_id, created_at")\
            .order("created_at", desc=True)\
            .limit(5)\
            .execute()
        
        print(f"📊 Found {len(tasks_result.data)} tasks")
        for task in tasks_result.data:
            print(f"  - {task.get('title', 'N/A')} ({task.get('status')}) - Workspace: {task.get('workspace_id')}")
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_database_status())