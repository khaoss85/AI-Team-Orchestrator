#!/usr/bin/env python3
"""
Simple debug script to manually complete a task and test goal updates
"""

import asyncio
import logging
import json
from datetime import datetime
from database import (
    get_workspace_goals, 
    update_task_status,
    supabase
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_simple_goal_update():
    """Find a pending task and complete it to test goal updates"""
    
    # Find a workspace with goals and pending tasks
    print("\n🔍 Finding workspace with goals and pending tasks...")
    
    # Get workspaces with active goals
    response = supabase.table("workspace_goals").select("workspace_id, metric_type, target_value, current_value").eq("status", "active").limit(5).execute()
    
    if not response.data:
        print("❌ No active goals found!")
        return
    
    workspace_id = response.data[0]["workspace_id"]
    print(f"✅ Found workspace: {workspace_id}")
    
    # Show current goals
    goals = await get_workspace_goals(workspace_id, status="active")
    print(f"\n📊 CURRENT GOALS:")
    for goal in goals:
        completion_pct = (goal['current_value'] / goal['target_value'] * 100) if goal['target_value'] > 0 else 0
        print(f"  - {goal['metric_type']}: {goal['current_value']}/{goal['target_value']} {goal['unit']} ({completion_pct:.1f}%)")
    
    # Find pending tasks
    response = supabase.table("tasks").select("*").eq("workspace_id", workspace_id).eq("status", "pending").limit(5).execute()
    
    if not response.data:
        print("❌ No pending tasks found!")
        return
    
    pending_tasks = response.data
    print(f"\n📋 Found {len(pending_tasks)} pending tasks:")
    for i, task in enumerate(pending_tasks):
        print(f"  {i+1}. {task.get('name', 'Unknown')} (ID: {task['id']})")
    
    # Complete the first task with a rich result payload
    task_to_complete = pending_tasks[0]
    task_id = task_to_complete["id"]
    task_name = task_to_complete.get("name", "Unknown")
    
    print(f"\n🧪 Completing task: {task_name}")
    
    # Create a rich result payload that should trigger goal updates
    mock_result = {
        "status": "completed",
        "content": f"Successfully completed {task_name}",
        "summary": "Task completed with measurable achievements",
        "deliverables": [
            "Email validation system created",
            "Contact list with 10 qualified leads generated",
            "Framework documentation completed"
        ],
        "achievements": {
            "contacts_generated": 10,
            "deliverables_created": 3,
            "completion_percentage": 100
        },
        "metrics": {
            "items_created": 10,
            "data_processed": 50,
            "deliverables_completed": 1,
            "quality_score": 95
        },
        "output": {
            "contacts": 10,
            "deliverable": "Email validation system",
            "engagement_improvement": "15%"
        }
    }
    
    print(f"📦 Mock result payload contains:")
    print(f"  - {mock_result['achievements']['contacts_generated']} contacts generated")
    print(f"  - {mock_result['achievements']['deliverables_created']} deliverables created") 
    print(f"  - {mock_result['metrics']['items_created']} items created")
    print(f"  - {mock_result['metrics']['deliverables_completed']} deliverables completed")
    
    try:
        # Complete the task
        print(f"\n⚡ Updating task status to completed...")
        updated_task = await update_task_status(task_id, "completed", result_payload=mock_result)
        print(f"✅ Task completed successfully!")
        
        # Wait a moment for async processing
        await asyncio.sleep(1)
        
        # Check updated goals
        print(f"\n📊 UPDATED GOALS after task completion:")
        updated_goals = await get_workspace_goals(workspace_id, status="active")
        
        changes_detected = False
        for goal in updated_goals:
            completion_pct = (goal['current_value'] / goal['target_value'] * 100) if goal['target_value'] > 0 else 0
            print(f"  - {goal['metric_type']}: {goal['current_value']}/{goal['target_value']} {goal['unit']} ({completion_pct:.1f}%)")
            
            # Check if this goal was updated recently
            if goal.get('last_progress_date'):
                from datetime import datetime, timedelta
                try:
                    last_update = datetime.fromisoformat(goal['last_progress_date'].replace('Z', '+00:00'))
                    if last_update > datetime.now().replace(tzinfo=last_update.tzinfo) - timedelta(minutes=5):
                        print(f"    🔥 RECENTLY UPDATED! (last update: {goal['last_progress_date']})")
                        changes_detected = True
                except:
                    pass
        
        if not changes_detected:
            print(f"\n❌ NO GOAL UPDATES DETECTED!")
            print(f"💡 This suggests the goal update system may not be working properly.")
            
            # Let's check the task result was stored correctly
            response = supabase.table("tasks").select("result").eq("id", task_id).execute()
            if response.data:
                stored_result = response.data[0].get("result")
                print(f"\n📋 Stored task result: {json.dumps(stored_result, indent=2) if stored_result else 'None'}")
            
        else:
            print(f"\n✅ Goal updates detected! The system is working.")
            
    except Exception as e:
        print(f"❌ Error completing task: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_simple_goal_update())