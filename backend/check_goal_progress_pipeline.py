#!/usr/bin/env python3
"""
Diagnostic script to check the goal progress pipeline for a specific workspace
"""
import os
import sys
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

workspace_id = "f79d87cc-b61f-491d-9226-4220e39e71ad"

print("\n" + "="*80)
print("🔍 GOAL PROGRESS PIPELINE DIAGNOSTIC")
print("="*80)
print(f"Workspace ID: {workspace_id}")
print(f"Timestamp: {datetime.now().isoformat()}")
print("="*80)

# 1. Check workspace status
print("\n📊 1. WORKSPACE STATUS:")
workspace_result = supabase.table("workspaces").select("*").eq("id", workspace_id).execute()
if workspace_result.data:
    workspace = workspace_result.data[0]
    print(f"   - Status: {workspace.get('status', 'N/A')}")
    print(f"   - Created: {workspace.get('created_at', 'N/A')}")
    print(f"   - Name: {workspace.get('name', 'N/A')}")
else:
    print("   ❌ Workspace not found!")
    sys.exit(1)

# 2. Check goals
print("\n🎯 2. GOALS STATUS:")
goals_result = supabase.table("goals").select("*").eq("workspace_id", workspace_id).execute()
if goals_result.data:
    print(f"   Total goals: {len(goals_result.data)}")
    for goal in goals_result.data:
        print(f"\n   Goal ID: {goal['id']}")
        print(f"   - Title: {goal.get('title', 'N/A')}")
        print(f"   - Status: {goal.get('status', 'N/A')}")
        print(f"   - Progress: {goal.get('progress', 0)}%")
        print(f"   - Type: {goal.get('type', 'N/A')}")
        print(f"   - Created: {goal.get('created_at', 'N/A')}")
else:
    print("   ⚠️ No goals found for this workspace")

# 3. Check tasks
print("\n📝 3. TASKS STATUS:")
tasks_result = supabase.table("tasks").select("*").eq("workspace_id", workspace_id).execute()
if tasks_result.data:
    print(f"   Total tasks: {len(tasks_result.data)}")
    
    # Group by status
    status_count = {}
    goal_task_mapping = {}
    for task in tasks_result.data:
        status = task.get('status', 'unknown')
        status_count[status] = status_count.get(status, 0) + 1
        
        goal_id = task.get('goal_id')
        if goal_id:
            if goal_id not in goal_task_mapping:
                goal_task_mapping[goal_id] = []
            goal_task_mapping[goal_id].append(task)
    
    print("\n   Tasks by status:")
    for status, count in status_count.items():
        print(f"   - {status}: {count}")
    
    print("\n   Tasks per goal:")
    for goal_id, tasks in goal_task_mapping.items():
        print(f"   - Goal {goal_id}: {len(tasks)} tasks")
        for task in tasks[:3]:  # Show first 3 tasks
            print(f"     • Task {task['id'][:8]}... - Status: {task.get('status', 'N/A')} - Agent: {task.get('assigned_agent_id', 'None')}")
    
    # Check for orphaned tasks (no goal_id)
    orphaned_tasks = [t for t in tasks_result.data if not t.get('goal_id')]
    if orphaned_tasks:
        print(f"\n   ⚠️ Orphaned tasks (no goal): {len(orphaned_tasks)}")
else:
    print("   ⚠️ No tasks found for this workspace")

# 4. Check task-agent assignments
print("\n👥 4. AGENT ASSIGNMENTS:")
if tasks_result.data:
    assigned_count = len([t for t in tasks_result.data if t.get('assigned_agent_id')])
    unassigned_count = len([t for t in tasks_result.data if not t.get('assigned_agent_id')])
    print(f"   - Tasks with agents: {assigned_count}")
    print(f"   - Tasks without agents: {unassigned_count}")
    
    if unassigned_count > 0:
        print(f"   ⚠️ {unassigned_count} tasks have no assigned agent!")

# 5. Check agents in workspace
print("\n🤖 5. AGENTS STATUS:")
agents_result = supabase.table("agents").select("*").eq("workspace_id", workspace_id).execute()
if agents_result.data:
    print(f"   Total agents: {len(agents_result.data)}")
    for agent in agents_result.data[:5]:  # Show first 5 agents
        print(f"   - {agent.get('role', 'N/A')} ({agent.get('seniority_level', 'N/A')}): Status={agent.get('status', 'N/A')}")
else:
    print("   ⚠️ No agents found for this workspace")

# 6. Check deliverables
print("\n📦 6. DELIVERABLES STATUS:")
deliverables_result = supabase.table("deliverables").select("*").eq("workspace_id", workspace_id).execute()
if deliverables_result.data:
    print(f"   Total deliverables: {len(deliverables_result.data)}")
    for deliverable in deliverables_result.data[:3]:  # Show first 3
        print(f"   - {deliverable.get('title', 'N/A')}: Status={deliverable.get('status', 'N/A')}")
else:
    print("   ⚠️ No deliverables found")

# 7. Check recent task updates
print("\n🕐 7. RECENT TASK ACTIVITY (last 5):")
if tasks_result.data:
    sorted_tasks = sorted(tasks_result.data, key=lambda x: x.get('updated_at', ''), reverse=True)[:5]
    for task in sorted_tasks:
        print(f"   - Task {task['id'][:8]}...")
        print(f"     Updated: {task.get('updated_at', 'N/A')}")
        print(f"     Status: {task.get('status', 'N/A')}")
        print(f"     Progress: {task.get('progress', 0)}%")

# 8. Diagnose issues
print("\n🔴 8. DIAGNOSTIC SUMMARY:")
issues_found = []

if goals_result.data:
    # Check for goals with 0% progress
    stuck_goals = [g for g in goals_result.data if g.get('progress', 0) == 0]
    if stuck_goals:
        issues_found.append(f"⚠️ {len(stuck_goals)} goals have 0% progress")
    
    # Check for goals without tasks
    goals_with_no_tasks = []
    for goal in goals_result.data:
        goal_id = goal['id']
        if goal_id not in goal_task_mapping or len(goal_task_mapping[goal_id]) == 0:
            goals_with_no_tasks.append(goal)
    
    if goals_with_no_tasks:
        issues_found.append(f"⚠️ {len(goals_with_no_tasks)} goals have no tasks")
        for goal in goals_with_no_tasks:
            print(f"     - Goal: {goal.get('title', goal['id'])}")

if tasks_result.data:
    # Check for blocked tasks
    blocked_tasks = [t for t in tasks_result.data if t.get('status') in ['blocked', 'failed']]
    if blocked_tasks:
        issues_found.append(f"⚠️ {len(blocked_tasks)} tasks are blocked/failed")
    
    # Check for tasks not started
    not_started = [t for t in tasks_result.data if t.get('status') == 'pending']
    if not_started:
        issues_found.append(f"⚠️ {len(not_started)} tasks are pending (not started)")

if not agents_result.data:
    issues_found.append("❌ No agents in workspace - cannot execute tasks!")

if issues_found:
    print("\n   ISSUES DETECTED:")
    for issue in issues_found:
        print(f"   {issue}")
else:
    print("   ✅ No major issues detected")

print("\n" + "="*80)
print("DIAGNOSTIC COMPLETE")
print("="*80)