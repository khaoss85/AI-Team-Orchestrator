#!/usr/bin/env python3
"""
Manually complete a task and verify goal updates work
"""

import asyncio
import logging
import json
from database import supabase, get_workspace_goals, update_task_status

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_manual_completion():
    """Manually complete a task and check goal updates"""
    
    workspace_id = "3b387b5e-51c0-43eb-8e8a-e279e38dbfb5"
    
    print(f"🔍 Working with workspace: {workspace_id}")
    
    # Get current goals
    goals = await get_workspace_goals(workspace_id, status="active")
    print(f"\n📊 CURRENT GOALS:")
    for goal in goals:
        completion_pct = (goal['current_value'] / goal['target_value'] * 100) if goal['target_value'] > 0 else 0
        print(f"  - {goal['metric_type']}: {goal['current_value']}/{goal['target_value']} {goal['unit']} ({completion_pct:.1f}%)")
    
    # Get tasks
    response = supabase.table("tasks").select("*").eq("workspace_id", workspace_id).execute()
    tasks = response.data
    
    print(f"\n📋 TASKS in workspace:")
    for task in tasks:
        print(f"  - {task.get('name', 'Unknown')} ({task.get('status')}) - ID: {task['id']}")
    
    # Find a task that's not completed to test with
    task_to_complete = None
    for task in tasks:
        if task.get("status") != "completed":
            task_to_complete = task
            break
    
    if not task_to_complete:
        print("❌ No non-completed tasks found!")
        return
    
    task_id = task_to_complete["id"]
    task_name = task_to_complete.get("name", "Unknown")
    current_status = task_to_complete.get("status")
    
    print(f"\n🧪 TESTING: Complete task '{task_name}' (current status: {current_status})")
    
    # Create a comprehensive result payload with multiple types of achievements
    result_payload = {
        "status": "completed",
        "content": f"Task '{task_name}' completed successfully with measurable achievements",
        "summary": "Task generated contacts, created deliverables, and improved engagement",
        
        # Multiple ways to express achievements for robust matching
        "achievements": {
            "contacts_generated": 10,
            "deliverables_created": 2,
            "engagement_improvement": 15,
            "items_created": 10,
            "data_processed": 25,
            "deliverables_completed": 2
        },
        
        "deliverables": [
            "Email validation system prototype",
            "Contact research report with 10 qualified leads"
        ],
        
        "metrics": {
            "contacts": 10,
            "deliverables": 2,
            "engagement_rate": 15,
            "quality_score": 85
        },
        
        "output": {
            "new_contacts": 10,
            "deliverable_count": 2,
            "engagement_percentage": "15%",
            "completed_deliverables": ["email_validation", "contact_analysis"]
        },
        
        # Specific goal-targeted achievements
        "goal_contributions": {
            "contacts": 10,  # Should map to contacts goal
            "deliverable_create_email_validation": 1,  # Should map to email validation deliverable
            "deliverable_analisi_completa_del": 1,  # Should map to analysis deliverable
            "engagement_rate": 15  # Should map to engagement rate goal
        }
    }
    
    print(f"📦 Result payload contains:")
    print(f"  - 10 contacts generated")
    print(f"  - 2 deliverables completed")
    print(f"  - 15% engagement improvement")
    print(f"  - Multiple achievement categories")
    
    try:
        # Complete the task
        print(f"\n⚡ Updating task status to 'completed'...")
        updated_task = await update_task_status(task_id, "completed", result_payload=result_payload)
        print(f"✅ Task status updated successfully!")
        
        # Wait for async goal processing
        print("⏳ Waiting for goal processing...")
        await asyncio.sleep(2)
        
        # Check updated goals
        print(f"\n📊 GOALS AFTER TASK COMPLETION:")
        updated_goals = await get_workspace_goals(workspace_id, status="active")
        
        any_changes = False
        for goal in updated_goals:
            old_goal = next((g for g in goals if g['id'] == goal['id']), None)
            old_value = old_goal['current_value'] if old_goal else 0
            current_value = goal['current_value']
            
            completion_pct = (current_value / goal['target_value'] * 100) if goal['target_value'] > 0 else 0
            
            if current_value != old_value:
                change = current_value - old_value
                print(f"  ✅ {goal['metric_type']}: {old_value} → {current_value}/{goal['target_value']} (+{change}) ({completion_pct:.1f}%)")
                any_changes = True
            else:
                print(f"  ❌ {goal['metric_type']}: {current_value}/{goal['target_value']} (no change) ({completion_pct:.1f}%)")
        
        if any_changes:
            print(f"\n🎉 SUCCESS! Goal updates detected!")
        else:
            print(f"\n❌ PROBLEM: No goal updates detected!")
            print(f"💡 The goal update system may not be working correctly.")
            
            # Check if the task result was stored
            response = supabase.table("tasks").select("result").eq("id", task_id).execute()
            if response.data and response.data[0].get("result"):
                print(f"✅ Task result was stored in database")
            else:
                print(f"❌ Task result was NOT stored in database")
        
    except Exception as e:
        print(f"❌ Error completing task: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_manual_completion())