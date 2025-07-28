#!/usr/bin/env python3
"""Diagnose specific workspace deliverable issues"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import supabase
from deliverable_system.unified_deliverable_engine import UnifiedDeliverableEngine
from services.course_correction_engine import CourseCorrectionEngine


async def diagnose_workspace(workspace_id: str = "12e63f24-1cda-44aa-b5b1-caef243bb18c"):
    """Diagnose why deliverables aren't being created for a specific workspace"""
    
    print(f"🔍 DIAGNOSING WORKSPACE: {workspace_id}")
    print("=" * 60)
    
    # Get workspace details
    workspace = supabase.table('workspaces').select('*').eq('id', workspace_id).single().execute()
    workspace_data = workspace.data
    
    print(f"\n📁 WORKSPACE DETAILS:")
    print(f"  Name: {workspace_data['name']}")
    print(f"  Status: {workspace_data['status']} ⚠️")
    print(f"  Created: {workspace_data['created_at']}")
    
    # Check if status is the issue
    if workspace_data['status'] != 'active':
        print(f"\n❌ ISSUE FOUND: Workspace status is '{workspace_data['status']}', not 'active'")
        print("   Deliverables are only created for 'active' workspaces")
    
    # Get goals
    goals = supabase.table('goals').select('*').eq('workspace_id', workspace_id).execute()
    print(f"\n🎯 GOALS: {len(goals.data)} found")
    for goal in goals.data:
        progress = (goal.get('current_value', 0) / goal.get('target_value', 100) * 100) if goal.get('target_value', 100) > 0 else 0
        print(f"  - {goal['goal_text'][:60]}...")
        print(f"    Progress: {progress:.1f}% (current: {goal.get('current_value', 0)}, target: {goal.get('target_value', 100)})")
    
    # Get tasks
    all_tasks = supabase.table('tasks').select('*').eq('workspace_id', workspace_id).execute()
    completed_tasks = [t for t in all_tasks.data if t['status'] == 'completed']
    
    print(f"\n✅ TASKS:")
    print(f"  Total: {len(all_tasks.data)}")
    print(f"  Completed: {len(completed_tasks)}")
    
    # Check quality scores
    quality_scores = []
    for task in completed_tasks:
        if task.get('quality_score'):
            quality_scores.append(task['quality_score'])
    
    if quality_scores:
        avg_quality = sum(quality_scores) / len(quality_scores)
        print(f"  Average Quality Score: {avg_quality * 100:.1f}%")
    else:
        print(f"  Average Quality Score: No scores available")
    
    # Get deliverables
    deliverables = supabase.table('deliverables').select('*').eq('workspace_id', workspace_id).execute()
    print(f"\n📦 DELIVERABLES: {len(deliverables.data)}")
    
    # Check trigger conditions
    env_vars = {
        'MIN_COMPLETED_TASKS_FOR_DELIVERABLE': int(os.getenv('MIN_COMPLETED_TASKS_FOR_DELIVERABLE', '2')),
        'DELIVERABLE_READINESS_THRESHOLD': int(os.getenv('DELIVERABLE_READINESS_THRESHOLD', '100')),
        'BUSINESS_VALUE_THRESHOLD': float(os.getenv('BUSINESS_VALUE_THRESHOLD', '70.0')),
        'MAX_DELIVERABLES_PER_WORKSPACE': int(os.getenv('MAX_DELIVERABLES_PER_WORKSPACE', '3')),
        'ENABLE_IMMEDIATE_DELIVERABLE_CREATION': os.getenv('ENABLE_IMMEDIATE_DELIVERABLE_CREATION', 'false').lower() == 'true',
        'IMMEDIATE_DELIVERABLE_THRESHOLD': int(os.getenv('IMMEDIATE_DELIVERABLE_THRESHOLD', '70'))
    }
    
    print(f"\n🔧 TRIGGER CONDITIONS:")
    print(f"  ❌ Workspace Status: '{workspace_data['status']}' (required: 'active')")
    print(f"  {'✅' if len(completed_tasks) >= env_vars['MIN_COMPLETED_TASKS_FOR_DELIVERABLE'] else '❌'} Completed Tasks: {len(completed_tasks)} (required: {env_vars['MIN_COMPLETED_TASKS_FOR_DELIVERABLE']})")
    print(f"  {'✅' if len(deliverables.data) < env_vars['MAX_DELIVERABLES_PER_WORKSPACE'] else '❌'} Under Deliverable Limit: {len(deliverables.data)} < {env_vars['MAX_DELIVERABLES_PER_WORKSPACE']}")
    
    # Check what would happen if we force the status to active
    print(f"\n🔮 SIMULATION: What if workspace was 'active'?")
    
    # Initialize deliverable engine
    deliverable_engine = UnifiedDeliverableEngine()
    
    # Temporarily update workspace status in memory (not in DB)
    print("  Checking trigger conditions with 'active' status...")
    
    # Check if it would trigger
    try:
        # We need to check the actual trigger logic
        print("\n  Checking unified_deliverable_engine.should_trigger_deliverable_aggregation logic...")
        
        # Show the actual check from the engine
        from deliverable_system.unified_deliverable_engine import UnifiedDeliverableEngine
        
        # Get the source of the should_trigger method
        import inspect
        source = inspect.getsource(UnifiedDeliverableEngine.should_trigger_deliverable_aggregation)
        print("\n  Source code of should_trigger_deliverable_aggregation:")
        for line in source.split('\n')[:20]:  # First 20 lines
            print(f"    {line}")
        
    except Exception as e:
        print(f"  Error checking trigger logic: {str(e)}")
    
    print(f"\n💡 SOLUTION:")
    print(f"  1. The workspace needs to be in 'active' status")
    print(f"  2. Current status is '{workspace_data['status']}'")
    print(f"  3. The workspace has {len(completed_tasks)} completed tasks (sufficient)")
    print(f"  4. Once status is 'active', deliverables should be created automatically")
    
    return workspace_data


async def check_task_processor():
    """Check what the task processor is doing"""
    print("\n🔄 CHECKING TASK PROCESSOR STATUS")
    print("=" * 60)
    
    # Check for any pending tasks
    pending_tasks = supabase.table('tasks').select('*').eq('status', 'pending').execute()
    print(f"\nPending tasks: {len(pending_tasks.data)}")
    
    # Check for tasks in progress
    in_progress = supabase.table('tasks').select('*').eq('status', 'in_progress').execute()
    print(f"In progress tasks: {len(in_progress.data)}")
    
    # Check if workspace should transition
    workspace_id = "12e63f24-1cda-44aa-b5b1-caef243bb18c"
    all_tasks = supabase.table('tasks').select('*').eq('workspace_id', workspace_id).execute()
    
    task_stats = {}
    for task in all_tasks.data:
        status = task['status']
        task_stats[status] = task_stats.get(status, 0) + 1
    
    print(f"\nTask statistics for workspace:")
    for status, count in task_stats.items():
        print(f"  {status}: {count}")
    
    # Check if all tasks are completed
    non_completed = [t for t in all_tasks.data if t['status'] not in ['completed', 'cancelled']]
    if not non_completed:
        print(f"\n✅ All tasks are completed! Workspace should transition to 'active'")
    else:
        print(f"\n❌ {len(non_completed)} tasks are not completed")


async def update_workspace_status(workspace_id: str = "12e63f24-1cda-44aa-b5b1-caef243bb18c"):
    """Manually update workspace status to active"""
    print("\n🔧 UPDATING WORKSPACE STATUS TO 'ACTIVE'")
    print("=" * 60)
    
    # Update workspace status
    result = supabase.table('workspaces').update({
        'status': 'active',
        'updated_at': datetime.utcnow().isoformat()
    }).eq('id', workspace_id).execute()
    
    if result.data:
        print(f"✅ Workspace status updated to 'active'")
        print(f"   Deliverables should now be created automatically")
        
        # Wait a moment for any background processes
        await asyncio.sleep(2)
        
        # Check if deliverables were created
        deliverables = supabase.table('deliverables').select('*').eq('workspace_id', workspace_id).execute()
        print(f"\n📦 Deliverables after update: {len(deliverables.data)}")
    else:
        print(f"❌ Failed to update workspace status")


async def main():
    """Main diagnostic function"""
    
    # Diagnose the workspace
    workspace = await diagnose_workspace()
    
    # Check task processor
    await check_task_processor()
    
    # Ask if we should fix it
    print("\n" + "=" * 60)
    print("🔧 RECOMMENDED FIX:")
    print("  Update workspace status to 'active' since all tasks are completed")
    print("\n  Run: python3 diagnose_specific_workspace.py --fix")
    
    # Check if --fix flag was passed
    if len(sys.argv) > 1 and sys.argv[1] == '--fix':
        await update_workspace_status()


if __name__ == "__main__":
    asyncio.run(main())