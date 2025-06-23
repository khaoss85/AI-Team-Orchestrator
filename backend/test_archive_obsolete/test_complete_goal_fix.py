#!/usr/bin/env python3
"""
Test the complete goal update fix by creating a new task and going through the verification flow
"""

import asyncio
import logging
import json
from database import (
    supabase, 
    get_workspace_goals, 
    update_task_status, 
    update_human_feedback_request,
    get_human_feedback_requests,
    create_task
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_complete_goal_fix():
    """Test the complete fix end-to-end"""
    
    workspace_id = "3b387b5e-51c0-43eb-8e8a-e279e38dbfb5"
    
    print("🔬 TESTING COMPLETE GOAL UPDATE FIX")
    print("=" * 60)
    
    # Step 1: Show current goals
    print(f"\n📊 STEP 1: Current Goals State")
    goals_before = await get_workspace_goals(workspace_id, status="active")
    for goal in goals_before:
        completion_pct = (goal['current_value'] / goal['target_value'] * 100) if goal['target_value'] > 0 else 0
        print(f"  - {goal['metric_type']}: {goal['current_value']}/{goal['target_value']} ({completion_pct:.1f}%)")
    
    # Step 2: Create a new task to test with
    print(f"\n🚀 STEP 2: Creating New Test Task")
    test_task = await create_task(
        workspace_id=workspace_id,
        name="Test Contact Generation Task",
        description="Generate 20 qualified contacts for testing goal updates",
        status="pending",
        priority="high",
        assigned_to_role="specialist",
        estimated_effort_hours=2
    )
    
    if not test_task:
        print("❌ Failed to create test task!")
        return
    
    task_id = test_task["id"]
    print(f"  ✅ Created test task: {task_id}")
    
    # Step 3: Complete the task with rich achievements
    print(f"\n⚡ STEP 3: Completing Task (should trigger verification)")
    
    rich_result = {
        "status": "completed",
        "content": "Successfully generated 20 qualified contacts for SaaS CMO/CTO outreach",
        "summary": "Task completed with significant achievements for goal progress",
        
        # Multiple achievement formats for robust detection
        "achievements": {
            "contacts_generated": 20,
            "deliverables_created": 3,
            "items_created": 20,
            "deliverables_completed": 3,
            "engagement_improvement": 25
        },
        
        "deliverables": [
            "Qualified contact database with 20 CMO/CTO contacts",
            "Email validation framework",
            "Target audience analysis report"
        ],
        
        "metrics": {
            "contacts": 20,
            "deliverables": 3,
            "engagement_rate": 25,
            "quality_score": 90
        },
        
        "output": {
            "new_contacts": 20,
            "deliverable_count": 3,
            "engagement_percentage": "25%"
        },
        
        "goal_contributions": {
            "contacts": 20,
            "deliverable_create_email_validation": 1,
            "deliverable_analisi_completa_del": 1,
            "engagement_rate": 25
        }
    }
    
    # Complete the task
    updated_task = await update_task_status(task_id, "completed", result_payload=rich_result)
    
    if updated_task:
        final_status = updated_task.get("status")
        print(f"  ✅ Task completed, final status: {final_status}")
        
        if final_status == "pending_verification":
            print(f"  🔍 Task moved to pending_verification as expected")
        elif final_status == "completed":
            print(f"  ⚡ Task completed directly (no verification needed)")
        else:
            print(f"  ❓ Unexpected status: {final_status}")
    else:
        print(f"  ❌ Failed to complete task")
        return
    
    # Step 4: Check for verification request with task_id
    print(f"\n🔍 STEP 4: Looking for Verification Request")
    await asyncio.sleep(1)  # Give it a moment to create the request
    
    # Get all pending feedback requests
    feedback_requests = await get_human_feedback_requests(workspace_id, "pending")
    
    # Find the request for our task
    our_request = None
    for req in feedback_requests:
        if req.get("task_id") == task_id:
            our_request = req
            break
    
    if our_request:
        request_id = our_request["id"]
        print(f"  ✅ Found verification request: {request_id}")
        print(f"      Task ID: {our_request.get('task_id')}")
        print(f"      Status: {our_request.get('status')}")
        print(f"      Type: {our_request.get('request_type')}")
    else:
        print(f"  ❌ No verification request found for task {task_id}")
        print(f"  Available requests:")
        for req in feedback_requests:
            print(f"    - Request {req.get('id')} for task {req.get('task_id')}")
        
        # If no verification was triggered, check if goals updated directly
        print(f"\n📊 Checking if goals updated directly...")
        goals_after_direct = await get_workspace_goals(workspace_id, status="active")
        
        changes_detected = False
        for i, goal in enumerate(goals_after_direct):
            old_value = goals_before[i]['current_value']
            new_value = goal['current_value']
            
            if new_value != old_value:
                change = new_value - old_value
                completion_pct = (new_value / goal['target_value'] * 100) if goal['target_value'] > 0 else 0
                print(f"    🎉 {goal['metric_type']}: {old_value} → {new_value} (+{change}) ({completion_pct:.1f}%)")
                changes_detected = True
        
        if changes_detected:
            print(f"  🎉 SUCCESS: Goals updated directly (no verification required)!")
            return
        else:
            print(f"  ❌ No goals updated and no verification request created")
            return
    
    # Step 5: Approve the verification request
    print(f"\n✅ STEP 5: Approving Verification Request")
    
    approval_response = {
        "approved": True,
        "feedback": "Test task output is excellent, approved for goal updates",
        "approver": "test_script",
        "quality_check": "passed",
        "timestamp": "2025-06-18T12:00:00Z"
    }
    
    # Approve the request (this should trigger our fix)
    result = await update_human_feedback_request(request_id, "approved", approval_response)
    
    if result:
        print(f"  ✅ Verification request approved!")
    else:
        print(f"  ❌ Failed to approve verification request")
        return
    
    # Step 6: Wait and check task status
    print(f"\n⏳ STEP 6: Checking Task Status After Approval")
    await asyncio.sleep(2)  # Give it time to process
    
    # Check task status
    response = supabase.table("tasks").select("*").eq("id", task_id).execute()
    if response.data:
        final_task = response.data[0]
        final_status = final_task.get("status")
        print(f"  📊 Final task status: {final_status}")
        
        if final_status == "completed":
            print(f"  ✅ SUCCESS: Task moved from pending_verification to completed!")
        else:
            print(f"  ❌ ISSUE: Task is still in '{final_status}' status")
    
    # Step 7: Check goals after approval (THE ULTIMATE TEST)
    print(f"\n🎯 STEP 7: Goals After Verification Approval")
    goals_after = await get_workspace_goals(workspace_id, status="active")
    
    print(f"🔍 Comparing goals before and after:")
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
    print(f"\n" + "=" * 60)
    if changes_detected:
        print(f"🏆 COMPLETE SUCCESS!")
        print(f"✅ Goal updates triggered after verification approval!")
        print(f"✅ The entire fix is working end-to-end!")
    else:
        print(f"❌ FAILURE: No goal updates detected")
        print(f"💡 The fix may still have issues to resolve")
    print(f"=" * 60)

if __name__ == "__main__":
    asyncio.run(test_complete_goal_fix())