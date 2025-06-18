#!/usr/bin/env python3
"""
Test verification approval with task_id stored in context
"""

import asyncio
import logging
import json
from database import (
    supabase, 
    get_workspace_goals, 
    update_human_feedback_request,
    get_human_feedback_requests
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_verification_with_context():
    """Test approving existing verification requests with task_id in context"""
    
    workspace_id = "3b387b5e-51c0-43eb-8e8a-e279e38dbfb5"
    
    print("🔍 Testing Verification Approval with Context Fix")
    print("=" * 50)
    
    # Step 1: Show current goals
    print(f"\n📊 STEP 1: Current Goals State")
    goals_before = await get_workspace_goals(workspace_id, status="active")
    for goal in goals_before:
        completion_pct = (goal['current_value'] / goal['target_value'] * 100) if goal['target_value'] > 0 else 0
        print(f"  - {goal['metric_type']}: {goal['current_value']}/{goal['target_value']} ({completion_pct:.1f}%)")
    
    # Step 2: Get pending feedback requests
    print(f"\n🔍 STEP 2: Finding Pending Verification Requests")
    feedback_requests = await get_human_feedback_requests(workspace_id, "pending")
    
    if not feedback_requests:
        print("❌ No pending feedback requests found!")
        return
    
    print(f"📋 Found {len(feedback_requests)} pending requests:")
    for req in feedback_requests:
        request_id = req.get('id')
        context = req.get('context', {})
        task_id_in_context = context.get('task_id')
        direct_task_id = req.get('task_id')
        
        print(f"\n  Request: {request_id}")
        print(f"    Direct task_id: {direct_task_id}")
        print(f"    Context task_id: {task_id_in_context}")
        print(f"    Type: {req.get('request_type')}")
        print(f"    Status: {req.get('status')}")
    
    # Choose the first request to approve
    request_to_approve = feedback_requests[0]
    request_id = request_to_approve.get('id')
    context = request_to_approve.get('context', {})
    task_id = context.get('task_id')
    
    if not task_id:
        print(f"❌ No task_id found in context for request {request_id}")
        return
    
    print(f"\n✅ STEP 3: Approving Request {request_id} for Task {task_id}")
    
    # Check task status before approval
    response = supabase.table("tasks").select("*").eq("id", task_id).execute()
    if response.data:
        task = response.data[0]
        print(f"  📊 Task status before approval: {task.get('status')}")
        print(f"  📝 Task name: {task.get('name')}")
    else:
        print(f"  ❌ Task {task_id} not found!")
        return
    
    # Approve the verification request
    approval_response = {
        "approved": True,
        "feedback": "Task output verified and approved for goal updates",
        "approver": "test_script_context_fix",
        "quality_check": "passed",
        "timestamp": "2025-06-18T12:30:00Z"
    }
    
    print(f"  🚀 Approving verification request...")
    result = await update_human_feedback_request(request_id, "approved", approval_response)
    
    if result:
        print(f"  ✅ Verification request approved!")
    else:
        print(f"  ❌ Failed to approve verification request")
        return
    
    # Step 4: Check task status after approval
    print(f"\n⏳ STEP 4: Checking Task Status After Approval")
    await asyncio.sleep(2)  # Give it time to process
    
    response = supabase.table("tasks").select("*").eq("id", task_id).execute()
    if response.data:
        updated_task = response.data[0]
        final_status = updated_task.get("status")
        print(f"  📊 Task status after approval: {final_status}")
        
        if final_status == "completed":
            print(f"  🎉 SUCCESS: Task moved to completed status!")
        else:
            print(f"  ❌ ISSUE: Task is still in '{final_status}' status")
            return
    
    # Step 5: Check goals after approval (THE CRITICAL TEST)
    print(f"\n🎯 STEP 5: Goals After Verification Approval")
    await asyncio.sleep(1)  # Give goal updates time to process
    
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
    print(f"\n" + "=" * 50)
    if changes_detected:
        print(f"🏆 COMPLETE SUCCESS!")
        print(f"✅ Goals updated after verification approval!")
        print(f"✅ The fix is working end-to-end!")
    else:
        print(f"❌ FAILURE: No goal updates detected")
        print(f"💡 Need to investigate why goal updates aren't triggering")
    print(f"=" * 50)

if __name__ == "__main__":
    asyncio.run(test_verification_with_context())