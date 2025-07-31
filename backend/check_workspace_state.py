#!/usr/bin/env python3
"""
Check workspace state after test
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(__file__))

from database import supabase

async def check_workspace_state():
    workspace_id = "1a10ddbe-335d-46b2-be1d-02981043d58c"  # From test output
    
    print(f"🔍 CHECKING WORKSPACE STATE: {workspace_id}")
    print("="*80)
    
    # Check workspace
    workspace_response = supabase.table("workspaces").select("*").eq("id", workspace_id).execute()
    if workspace_response.data:
        workspace = workspace_response.data[0]
        print(f"📋 WORKSPACE:")
        print(f"   Name: {workspace.get('name')}")
        print(f"   Status: {workspace.get('status')}")
        print(f"   Goal: {workspace.get('goal', '')[:100]}...")
    
    # Check agents
    agents_response = supabase.table("agents").select("*").eq("workspace_id", workspace_id).execute()
    print(f"\n👥 AGENTS: {len(agents_response.data) if agents_response.data else 0}")
    if agents_response.data:
        for agent in agents_response.data:
            print(f"   - {agent.get('name')} ({agent.get('role')}) - {agent.get('status')}")
    
    # Check team proposals
    proposals_response = supabase.table("team_proposals").select("*").eq("workspace_id", workspace_id).execute()
    print(f"\n📝 TEAM PROPOSALS: {len(proposals_response.data) if proposals_response.data else 0}")
    if proposals_response.data:
        for proposal in proposals_response.data:
            print(f"   - ID: {proposal.get('id')} - Status: {proposal.get('status')}")
    
    # Check goals
    goals_response = supabase.table("workspace_goals").select("*").eq("workspace_id", workspace_id).execute()
    print(f"\n🎯 GOALS: {len(goals_response.data) if goals_response.data else 0}")
    if goals_response.data:
        for goal in goals_response.data:
            print(f"   - {goal.get('description', 'No description')[:50]}... - {goal.get('status')}")
    
    # Check tasks
    tasks_response = supabase.table("tasks").select("*").eq("workspace_id", workspace_id).execute()
    print(f"\n📋 TASKS: {len(tasks_response.data) if tasks_response.data else 0}")
    if tasks_response.data:
        for task in tasks_response.data:
            print(f"   - {task.get('name', 'No name')[:50]}... - {task.get('status')}")
    
    # Check deliverables
    deliverables_response = supabase.table("deliverables").select("*").eq("workspace_id", workspace_id).execute()
    print(f"\n📦 DELIVERABLES: {len(deliverables_response.data) if deliverables_response.data else 0}")
    if deliverables_response.data:
        for deliverable in deliverables_response.data:
            content_length = len(deliverable.get('content', ''))
            print(f"   - {deliverable.get('type', 'No type')} - {content_length} chars - {deliverable.get('status')}")
            
            # Show content preview if exists
            content = deliverable.get('content', '')
            if content:
                print(f"     Preview: {content[:200]}...")
                
                # Analyze content
                content_lower = content.lower()
                has_emails = '@' in content and '.com' in content
                has_names = any(name in content_lower for name in ['john', 'sarah', 'mike', 'lisa'])
                has_methodology = any(word in content_lower for word in ['strategy', 'approach', 'how to'])
                
                print(f"     Analysis: emails={has_emails}, names={has_names}, methodology={has_methodology}")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    asyncio.run(check_workspace_state())