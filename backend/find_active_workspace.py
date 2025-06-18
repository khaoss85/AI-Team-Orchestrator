#!/usr/bin/env python3
"""
Find a workspace with both goals and tasks to test goal updates
"""

import asyncio
import logging
import json
from database import supabase, get_workspace_goals

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def find_active_workspace():
    """Find workspace with both goals and tasks"""
    
    print("🔍 Searching for workspaces with goals and tasks...")
    
    # Get all workspaces with active goals
    response = supabase.table("workspace_goals").select("workspace_id").eq("status", "active").execute()
    workspace_ids = list(set(row["workspace_id"] for row in response.data))
    
    print(f"Found {len(workspace_ids)} workspaces with active goals")
    
    for workspace_id in workspace_ids:
        print(f"\n📋 Checking workspace: {workspace_id}")
        
        # Get goals
        goals = await get_workspace_goals(workspace_id, status="active")
        print(f"  Goals: {len(goals)}")
        
        # Get all tasks (any status)
        response = supabase.table("tasks").select("id, name, status").eq("workspace_id", workspace_id).execute()
        tasks = response.data
        
        task_counts = {}
        for task in tasks:
            status = task.get("status", "unknown")
            task_counts[status] = task_counts.get(status, 0) + 1
        
        print(f"  Tasks: {dict(task_counts)} (total: {len(tasks)})")
        
        if len(tasks) > 0:
            print(f"  📌 WORKSPACE WITH TASKS FOUND: {workspace_id}")
            
            # Show some task details
            for task in tasks[:3]:
                print(f"    - {task.get('name', 'Unknown')} ({task.get('status')})")
            
            # Show goal details
            print(f"  📊 Goals in this workspace:")
            for goal in goals:
                completion_pct = (goal['current_value'] / goal['target_value'] * 100) if goal['target_value'] > 0 else 0
                print(f"    - {goal['metric_type']}: {goal['current_value']}/{goal['target_value']} {goal['unit']} ({completion_pct:.1f}%)")
            
            # Test completing a task if there are any pending
            pending_tasks = [t for t in tasks if t.get("status") == "pending"]
            completed_tasks = [t for t in tasks if t.get("status") == "completed"]
            
            if pending_tasks:
                print(f"\n🧪 Testing goal update with pending task...")
                await test_goal_update(workspace_id, pending_tasks[0], goals)
            elif completed_tasks:
                print(f"\n📋 Found {len(completed_tasks)} completed tasks - checking if goal updates worked")
                # Check if any goals have been updated
                for goal in goals:
                    if goal['current_value'] > 0:
                        print(f"  ✅ Goal '{goal['metric_type']}' has progress: {goal['current_value']}")
                    else:
                        print(f"  ❌ Goal '{goal['metric_type']}' has no progress")
            break
    else:
        print("❌ No workspaces found with tasks!")

async def test_goal_update(workspace_id, task, goals):
    """Test completing a task to trigger goal updates"""
    from database import update_task_status
    
    task_id = task["id"]
    task_name = task.get("name", "Unknown")
    
    print(f"  🧪 Completing task: {task_name}")
    
    # Create result with achievements that should map to goals
    result_payload = {
        "status": "completed",
        "content": f"Task '{task_name}' completed successfully",
        "achievements": {
            "items_created": 5,
            "data_processed": 10,
            "deliverables_completed": 1,
            "contacts_generated": 3
        },
        "deliverables": ["Test deliverable created"],
        "metrics": {
            "contacts": 3,
            "deliverables": 1,
            "engagement_rate": 15
        }
    }
    
    try:
        # Complete the task
        await update_task_status(task_id, "completed", result_payload=result_payload)
        print(f"  ✅ Task completed")
        
        # Wait for processing
        await asyncio.sleep(1)
        
        # Check goals again
        from database import get_workspace_goals
        updated_goals = await get_workspace_goals(workspace_id, status="active")
        
        print(f"  📊 Checking goal updates:")
        for goal in updated_goals:
            completion_pct = (goal['current_value'] / goal['target_value'] * 100) if goal['target_value'] > 0 else 0
            if goal['current_value'] > 0:
                print(f"    ✅ {goal['metric_type']}: {goal['current_value']}/{goal['target_value']} ({completion_pct:.1f}%)")
            else:
                print(f"    ❌ {goal['metric_type']}: {goal['current_value']}/{goal['target_value']} (0.0%)")
                
    except Exception as e:
        print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(find_active_workspace())