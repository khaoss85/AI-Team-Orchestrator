#!/usr/bin/env python3
"""
Test script to verify the goal update fix works correctly
"""

import asyncio
import logging
import json
from database import (
    supabase, 
    get_workspace_goals, 
    update_task_status, 
    update_human_feedback_request,
    get_human_feedback_requests
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_goal_update_fix():
    """Test the complete flow: task completion -> verification -> approval -> goal updates"""
    
    workspace_id = "3b387b5e-51c0-43eb-8e8a-e279e38dbfb5"
    
    print("🔍 Testing Goal Update Fix")
    print("=" * 50)
    
    # Step 1: Show current state
    print(f"\n📊 STEP 1: Current Goals State")
    goals = await get_workspace_goals(workspace_id, status="active")
    for goal in goals:
        completion_pct = (goal['current_value'] / goal['target_value'] * 100) if goal['target_value'] > 0 else 0
        print(f"  - {goal['metric_type']}: {goal['current_value']}/{goal['target_value']} ({completion_pct:.1f}%)")
    
    # Step 2: Find tasks in pending_verification status
    print(f"\n📋 STEP 2: Finding Tasks in Pending Verification")
    response = supabase.table("tasks").select("*").eq("workspace_id", workspace_id).eq("status", "pending_verification").execute()
    
    if not response.data:
        print("❌ No tasks in pending_verification status!")
        print("Let me create one by completing a failed task...")
        
        # Find a failed task to re-complete
        response = supabase.table("tasks").select("*").eq("workspace_id", workspace_id).eq("status", "failed").limit(1).execute()
        
        if response.data:
            task = response.data[0]
            task_id = task["id"]
            task_name = task.get("name", "Unknown")
            
            print(f"  📝 Re-completing failed task: {task_name}")
            
            # Create a rich result payload
            result_payload = {
                "status": "completed",
                "content": f"Task '{task_name}' completed successfully",
                "achievements": {
                    "contacts_generated": 15,
                    "deliverables_created": 2,
                    "items_created": 15,
                    "deliverables_completed": 2
                },
                "deliverables": ["Contact research completed", "Email validation system"],
                "metrics": {
                    "contacts": 15,
                    "deliverables": 2,
                    "engagement_rate": 20
                }
            }
            
            # Complete the task - this should put it in pending_verification
            await update_task_status(task_id, "completed", result_payload=result_payload)
            print(f"  ✅ Task re-completed, should now be in pending_verification")
            
            # Check the new status
            response = supabase.table("tasks").select("*").eq("id", task_id).execute()
            if response.data:
                new_status = response.data[0].get("status")
                print(f"  📊 Task status after completion: {new_status}")
        else:
            print("❌ No failed tasks found either!")
            return
    
    # Get pending verification tasks
    response = supabase.table("tasks").select("*").eq("workspace_id", workspace_id).eq("status", "pending_verification").execute()
    pending_tasks = response.data
    
    if not pending_tasks:
        print("❌ Still no tasks in pending_verification status!")
        return
    
    task_to_approve = pending_tasks[0]
    task_id = task_to_approve["id"]
    task_name = task_to_approve.get("name", "Unknown")
    
    print(f"  ✅ Found task in pending_verification: {task_name} (ID: {task_id})")
    
    # Step 3: Find the corresponding human feedback request
    print(f"\n🔍 STEP 3: Finding Human Feedback Request")
    feedback_requests = await get_human_feedback_requests(workspace_id, "pending")
    
    corresponding_request = None
    for req in feedback_requests:
        if req.get("task_id") == task_id:
            corresponding_request = req
            break
    
    if not corresponding_request:
        print(f"❌ No human feedback request found for task {task_id}")
        print("Available feedback requests:")
        for req in feedback_requests:
            print(f"  - Request {req.get('id')} for task {req.get('task_id')}")
        return
    
    request_id = corresponding_request["id"]
    print(f"  ✅ Found feedback request: {request_id}")
    
    # Step 4: Show goals before approval
    print(f"\n📊 STEP 4: Goals Before Approval")
    goals_before = await get_workspace_goals(workspace_id, status="active")
    for goal in goals_before:
        completion_pct = (goal['current_value'] / goal['target_value'] * 100) if goal['target_value'] > 0 else 0
        print(f"  - {goal['metric_type']}: {goal['current_value']}/{goal['target_value']} ({completion_pct:.1f}%)")
    
    # Step 5: Approve the verification request (this should trigger the fix)
    print(f"\n🚀 STEP 5: Approving Verification Request")
    approval_response = {
        "approved": True,
        "feedback": "Task output looks good, approved for completion",
        "approver": "test_script",
        "timestamp": "2025-06-18T10:00:00Z"
    }
    
    print(f"  📝 Approving request {request_id}...")
    result = await update_human_feedback_request(request_id, "approved", approval_response)
    
    if result:
        print(f"  ✅ Verification request approved successfully!")
    else:
        print(f"  ❌ Failed to approve verification request")
        return
    
    # Step 6: Wait and check task status
    print(f"\n⏳ STEP 6: Checking Task Status After Approval")
    await asyncio.sleep(1)  # Give it a moment to process
    
    response = supabase.table("tasks").select("*").eq("id", task_id).execute()
    if response.data:
        updated_task = response.data[0]
        new_status = updated_task.get("status")
        print(f"  📊 Task status after approval: {new_status}")
        
        if new_status == "completed":
            print(f"  ✅ SUCCESS: Task moved to completed status!")
        else:
            print(f"  ❌ ISSUE: Task is still in '{new_status}' status")
    
    # Step 7: Check goals after approval (the critical test)
    print(f"\n🎯 STEP 7: Goals After Approval (THE BIG TEST)")
    goals_after = await get_workspace_goals(workspace_id, status="active")
    
    changes_detected = False
    for i, goal in enumerate(goals_after):
        old_value = goals_before[i]['current_value']
        new_value = goal['current_value']
        completion_pct = (new_value / goal['target_value'] * 100) if goal['target_value'] > 0 else 0
        
        if new_value != old_value:
            change = new_value - old_value
            print(f"  🎉 {goal['metric_type']}: {old_value} → {new_value} (+{change}) ({completion_pct:.1f}%)")
            changes_detected = True
        else:
            print(f"  ➡️ {goal['metric_type']}: {new_value}/{goal['target_value']} (no change) ({completion_pct:.1f}%)")
    
    # Final verdict
    print(f"\n" + "=" * 50)
    if changes_detected:
        print(f"🎉 SUCCESS: Goal updates detected after verification approval!")
        print(f"✅ The fix is working correctly!")
    else:
        print(f"❌ FAILURE: No goal updates detected")
        print(f"💡 The fix may need additional investigation")
    print(f"=" * 50)

if __name__ == "__main__":
    asyncio.run(test_goal_update_fix())