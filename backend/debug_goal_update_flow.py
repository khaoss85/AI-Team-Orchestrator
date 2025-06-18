#!/usr/bin/env python3
"""
Debug script to trace the goal update flow when tasks are completed
"""

import asyncio
import logging
import json
from datetime import datetime
from database import (
    get_workspace_goals, 
    get_task, 
    update_task_status,
    _update_goal_progress_from_task_completion,
    _extract_task_achievements,
    _calculate_goal_increment
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_goal_update_flow():
    """Debug the complete goal update flow"""
    
    # Find a workspace with goals
    print("\n🔍 STEP 1: Finding workspace with active goals...")
    from database import supabase
    
    # Get workspaces with active goals
    response = supabase.table("workspace_goals").select("workspace_id, metric_type, target_value, current_value").eq("status", "active").limit(5).execute()
    
    if not response.data:
        print("❌ No active goals found!")
        return
    
    workspace_id = response.data[0]["workspace_id"]
    print(f"✅ Found workspace: {workspace_id}")
    
    # Show current goals
    goals = await get_workspace_goals(workspace_id, status="active")
    print(f"\n📊 CURRENT GOALS in workspace {workspace_id}:")
    for goal in goals:
        print(f"  - {goal['metric_type']}: {goal['current_value']}/{goal['target_value']} {goal['unit']}")
    
    # Find completed tasks
    print(f"\n🔍 STEP 2: Finding completed tasks...")
    response = supabase.table("tasks").select("*").eq("workspace_id", workspace_id).eq("status", "completed").limit(10).execute()
    
    if not response.data:
        print("❌ No completed tasks found!")
        return
    
    completed_tasks = response.data
    print(f"✅ Found {len(completed_tasks)} completed tasks")
    
    # Test achievement extraction for each task
    print(f"\n🤖 STEP 3: Testing achievement extraction...")
    for i, task in enumerate(completed_tasks[:3]):  # Test first 3 tasks
        task_id = task["id"]
        task_name = task.get("name", "Unknown")
        result_payload = task.get("result", {})
        
        print(f"\n  📋 Task {i+1}: {task_name}")
        print(f"     Task ID: {task_id}")
        print(f"     Result keys: {list(result_payload.keys()) if result_payload else 'None'}")
        
        # Extract achievements
        achievements = await _extract_task_achievements(result_payload, task_name)
        print(f"     🎯 Extracted achievements: {achievements}")
        
        # Test goal increment calculation for each goal
        for goal in goals:
            metric_type = goal.get("metric_type", "")
            increment = _calculate_goal_increment(achievements, metric_type)
            print(f"     📈 Goal '{metric_type}' increment: {increment}")
    
    # Test the full goal update flow with the first completed task
    print(f"\n🔧 STEP 4: Testing full goal update flow...")
    test_task = completed_tasks[0]
    task_id = test_task["id"]
    task_name = test_task.get("name", "Unknown")
    result_payload = test_task.get("result", {})
    
    print(f"  Testing with task: {task_name} (ID: {task_id})")
    
    # Manually run the goal progress update function
    try:
        await _update_goal_progress_from_task_completion(task_id, result_payload)
        print("  ✅ Goal progress update completed successfully")
    except Exception as e:
        print(f"  ❌ Goal progress update failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Check if goals were updated
    print(f"\n📊 STEP 5: Checking updated goals...")
    updated_goals = await get_workspace_goals(workspace_id, status="active")
    print(f"UPDATED GOALS in workspace {workspace_id}:")
    for goal in updated_goals:
        print(f"  - {goal['metric_type']}: {goal['current_value']}/{goal['target_value']} {goal['unit']}")
    
    # Find a pending task and simulate its completion
    print(f"\n🧪 STEP 6: Simulating task completion...")
    response = supabase.table("tasks").select("*").eq("workspace_id", workspace_id).eq("status", "pending").limit(1).execute()
    
    if response.data:
        pending_task = response.data[0]
        task_id = pending_task["id"]
        task_name = pending_task.get("name", "Unknown")
        
        print(f"  Found pending task: {task_name} (ID: {task_id})")
        
        # Create a mock result payload with achievements
        mock_result = {
            "content": f"Task {task_name} completed successfully",
            "summary": "Generated 5 new items for the workspace",
            "achievements": {
                "items_created": 5,
                "deliverables_completed": 1
            },
            "status": "success"
        }
        
        print(f"  📋 Mock result: {json.dumps(mock_result, indent=2)}")
        
        # Update task status to completed with the mock result
        try:
            updated_task = await update_task_status(task_id, "completed", result_payload=mock_result)
            print(f"  ✅ Task marked as completed")
            
            # Check goals again
            print(f"\n📊 FINAL GOALS after simulated completion:")
            final_goals = await get_workspace_goals(workspace_id, status="active")
            for goal in final_goals:
                print(f"  - {goal['metric_type']}: {goal['current_value']}/{goal['target_value']} {goal['unit']}")
                
        except Exception as e:
            print(f"  ❌ Task completion simulation failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("  ❌ No pending tasks found to simulate")

if __name__ == "__main__":
    asyncio.run(debug_goal_update_flow())