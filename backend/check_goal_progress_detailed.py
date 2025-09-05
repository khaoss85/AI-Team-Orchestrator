#!/usr/bin/env python3
"""
Detailed diagnostic for goal progress pipeline using correct table names
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
print("🔍 DETAILED GOAL PROGRESS PIPELINE DIAGNOSTIC")
print("="*80)
print(f"Workspace ID: {workspace_id}")
print(f"Timestamp: {datetime.now().isoformat()}")
print("="*80)

# 1. Check workspace
print("\n📊 1. WORKSPACE STATUS:")
workspace_result = supabase.table("workspaces").select("*").eq("id", workspace_id).execute()
if workspace_result.data:
    workspace = workspace_result.data[0]
    print(f"   - Name: {workspace.get('name', 'N/A')}")
    print(f"   - Status: {workspace.get('status', 'N/A')}")
    print(f"   - Project Understanding: {workspace.get('project_understanding', 'N/A')}")
else:
    print("   ❌ Workspace not found!")
    sys.exit(1)

# 2. Check workspace_goals (the actual goals table)
print("\n🎯 2. WORKSPACE GOALS STATUS:")
goals_result = supabase.table("workspace_goals").select("*").eq("workspace_id", workspace_id).execute()
if goals_result.data:
    print(f"   Total goals: {len(goals_result.data)}")
    for goal in goals_result.data:
        print(f"\n   Goal ID: {goal['id']}")
        print(f"   - Description: {goal.get('description', 'N/A')}")
        print(f"   - Goal Type: {goal.get('goal_type', 'N/A')}")
        print(f"   - Metric Type: {goal.get('metric_type', 'N/A')}")
        print(f"   - Status: {goal.get('status', 'N/A')}")
        print(f"   - Target Value: {goal.get('target_value', 0)}")
        print(f"   - Current Value: {goal.get('current_value', 0)}")
        
        # Calculate progress percentage
        if goal.get('target_value', 0) > 0:
            progress_pct = (goal.get('current_value', 0) / goal.get('target_value', 1)) * 100
        else:
            progress_pct = 0
        print(f"   - Calculated Progress: {progress_pct:.1f}%")
        
        print(f"   - Asset Completion Rate: {goal.get('asset_completion_rate', 0)}%")
        print(f"   - Assets Required: {goal.get('asset_requirements_count', 0)}")
        print(f"   - Assets Completed: {goal.get('assets_completed_count', 0)}")
        print(f"   - Quality Score: {goal.get('quality_score', 0)}")
        print(f"   - Last Progress Update: {goal.get('last_progress_update', 'Never')}")
        print(f"   - AI Validation Enabled: {goal.get('ai_validation_enabled', False)}")
else:
    print("   ⚠️ No goals found for this workspace")

# 3. Check tasks and their goal mapping
print("\n📝 3. TASKS STATUS & GOAL MAPPING:")
tasks_result = supabase.table("tasks").select("*").eq("workspace_id", workspace_id).execute()
if tasks_result.data:
    print(f"   Total tasks: {len(tasks_result.data)}")
    
    # Group by status
    status_count = {}
    goal_task_mapping = {}
    
    for task in tasks_result.data:
        status = task.get('status', 'unknown')
        status_count[status] = status_count.get(status, 0) + 1
        
        # Check for goal_id field
        goal_id = task.get('goal_id') or task.get('workspace_goal_id')
        if goal_id:
            if goal_id not in goal_task_mapping:
                goal_task_mapping[goal_id] = []
            goal_task_mapping[goal_id].append(task)
    
    print("\n   Tasks by status:")
    for status, count in status_count.items():
        print(f"   - {status}: {count}")
    
    print("\n   Tasks mapped to goals:")
    if goal_task_mapping:
        for goal_id, tasks in goal_task_mapping.items():
            print(f"\n   Goal {goal_id[:8]}... has {len(tasks)} tasks:")
            for task in tasks[:3]:
                print(f"     • Task: {task.get('title', task['id'][:8])}")
                print(f"       Status: {task.get('status', 'N/A')}, Agent: {task.get('assigned_agent_id', 'None')[:8] if task.get('assigned_agent_id') else 'None'}")
    else:
        print("   ⚠️ No tasks are mapped to any goals!")
    
    # Check for orphaned tasks
    orphaned_tasks = [t for t in tasks_result.data if not (t.get('goal_id') or t.get('workspace_goal_id'))]
    if orphaned_tasks:
        print(f"\n   ⚠️ ORPHANED TASKS (not linked to goals): {len(orphaned_tasks)}")
        for task in orphaned_tasks[:5]:
            print(f"     - {task.get('title', task['id'])}: Status={task.get('status', 'N/A')}")

# 4. Check if goals have the necessary task linkage
print("\n🔗 4. GOAL-TASK LINKAGE ANALYSIS:")
if goals_result.data and tasks_result.data:
    for goal in goals_result.data:
        goal_id = goal['id']
        linked_tasks = [t for t in tasks_result.data if (t.get('goal_id') == goal_id or t.get('workspace_goal_id') == goal_id)]
        
        print(f"\n   Goal: {goal.get('description', goal_id)[:50]}...")
        print(f"   - Has {len(linked_tasks)} linked tasks")
        
        if len(linked_tasks) == 0:
            print(f"   ⚠️ This goal has NO tasks - cannot make progress!")
        else:
            completed_tasks = [t for t in linked_tasks if t.get('status') == 'completed']
            print(f"   - Completed tasks: {len(completed_tasks)}/{len(linked_tasks)}")

# 5. Check agents
print("\n🤖 5. AGENTS STATUS:")
agents_result = supabase.table("agents").select("*").eq("workspace_id", workspace_id).execute()
if agents_result.data:
    print(f"   Total agents: {len(agents_result.data)}")
    
    # Count by status
    agent_status_count = {}
    for agent in agents_result.data:
        status = agent.get('status', 'unknown')
        agent_status_count[status] = agent_status_count.get(status, 0) + 1
    
    print("   Agents by status:")
    for status, count in agent_status_count.items():
        print(f"   - {status}: {count}")
    
    # Show sample agents
    for agent in agents_result.data[:3]:
        print(f"\n   Agent: {agent.get('role', 'N/A')} ({agent.get('seniority_level', 'N/A')})")
        print(f"   - Status: {agent.get('status', 'N/A')}")
        print(f"   - ID: {agent['id'][:8]}...")
else:
    print("   ❌ No agents found - CRITICAL: Cannot execute tasks without agents!")

# 6. Check deliverables
print("\n📦 6. DELIVERABLES STATUS:")
deliverables_result = supabase.table("deliverables").select("*").eq("workspace_id", workspace_id).execute()
if deliverables_result.data:
    print(f"   Total deliverables: {len(deliverables_result.data)}")
    for deliverable in deliverables_result.data[:3]:
        print(f"   - {deliverable.get('title', 'N/A')}")
        print(f"     Status: {deliverable.get('status', 'N/A')}, Type: {deliverable.get('type', 'N/A')}")
else:
    print("   ⚠️ No deliverables found")

# 7. DIAGNOSIS
print("\n" + "="*80)
print("🔴 DIAGNOSTIC SUMMARY - ROOT CAUSE ANALYSIS")
print("="*80)

issues = []
recommendations = []

# Check 1: Goals without tasks
if goals_result.data:
    for goal in goals_result.data:
        goal_id = goal['id']
        linked_tasks = [t for t in tasks_result.data if (t.get('goal_id') == goal_id or t.get('workspace_goal_id') == goal_id)]
        if not linked_tasks:
            issues.append(f"Goal '{goal.get('description', goal_id)[:30]}...' has NO tasks")
            recommendations.append(f"Generate tasks for goal {goal_id[:8]}")

# Check 2: Tasks without agents
if tasks_result.data:
    unassigned = [t for t in tasks_result.data if not t.get('assigned_agent_id')]
    if unassigned:
        issues.append(f"{len(unassigned)} tasks have no assigned agents")
        recommendations.append("Assign agents to unassigned tasks")

# Check 3: All tasks pending
    pending_tasks = [t for t in tasks_result.data if t.get('status') == 'pending']
    if len(pending_tasks) == len(tasks_result.data):
        issues.append("ALL tasks are in 'pending' status - nothing is executing!")
        recommendations.append("Trigger task execution to move tasks from pending to in_progress")

# Check 4: No agents available
if not agents_result.data:
    issues.append("NO AGENTS in workspace - critical blocker!")
    recommendations.append("Create agents for the workspace immediately")

# Check 5: Goal progress not updating
if goals_result.data:
    stuck_goals = [g for g in goals_result.data if g.get('current_value', 0) == 0 and g.get('assets_completed_count', 0) == 0]
    if stuck_goals:
        issues.append(f"{len(stuck_goals)} goals showing 0 progress despite having tasks")
        recommendations.append("Check progress calculation logic and asset tracking")

print("\n🚨 ISSUES FOUND:")
if issues:
    for i, issue in enumerate(issues, 1):
        print(f"   {i}. {issue}")
else:
    print("   No major issues detected")

print("\n💡 RECOMMENDATIONS:")
if recommendations:
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec}")
else:
    print("   System appears to be functioning correctly")

print("\n" + "="*80)
print("DIAGNOSTIC COMPLETE")
print("="*80)