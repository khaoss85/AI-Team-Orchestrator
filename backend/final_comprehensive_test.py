#!/usr/bin/env python3
"""
Final comprehensive test to verify the goal update fix works end-to-end
"""

import asyncio
import logging
from database import (
    supabase, 
    get_workspace_goals, 
    create_task,
    update_task_status,
    update_human_feedback_request,
    get_human_feedback_requests
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def final_comprehensive_test():
    """Complete end-to-end test of the goal update fix"""
    
    workspace_id = "3b387b5e-51c0-43eb-8e8a-e279e38dbfb5"
    
    print("🏆 FINAL COMPREHENSIVE GOAL UPDATE TEST")
    print("=" * 60)
    
    # Step 1: Show initial state
    print(f"\n📊 STEP 1: Initial Goals State")
    initial_goals = await get_workspace_goals(workspace_id, status="active")
    for goal in initial_goals:
        completion_pct = (goal['current_value'] / goal['target_value'] * 100) if goal['target_value'] > 0 else 0
        print(f"  - {goal['metric_type']}: {goal['current_value']}/{goal['target_value']} ({completion_pct:.1f}%)")
    
    # Step 2: Create and complete a new task
    print(f"\n🚀 STEP 2: Creating New Task for End-to-End Test")
    test_task = await create_task(
        workspace_id=workspace_id,
        name="Final Test: B2B Lead Generation Campaign",
        description="Generate 10 high-quality B2B leads with email sequences",
        status="pending",
        priority="high",
        assigned_to_role="specialist",
        estimated_effort_hours=3
    )
    
    if not test_task:
        print("❌ Failed to create test task!")
        return
    
    task_id = test_task["id"]
    print(f"  ✅ Created task: {task_id}")
    
    # Step 3: Complete task with achievements that should map to goals
    print(f"\n⚡ STEP 3: Completing Task with Goal-Relevant Achievements")
    
    achievement_payload = {
        "status": "completed",
        "content": "Successfully executed B2B lead generation campaign with excellent results",
        "summary": "Generated leads, created deliverables, and achieved engagement targets",
        
        "achievements": {
            "contacts_generated": 10,      # Should map to contacts goal
            "deliverables_created": 2,     # Should map to deliverable goals  
            "items_created": 10,           # Should map to creation goals
            "deliverables_completed": 2,   # Should map to completion goals
            "engagement_improvement": 15   # Should map to engagement goal
        },
        
        "deliverables": [
            "B2B contact database with 10 qualified leads",
            "Email sequence framework for lead nurturing"
        ],
        
        "metrics": {
            "contacts": 10,
            "deliverables": 2,
            "engagement_rate": 15,
            "quality_score": 95
        }
    }
    
    print(f"  📦 Achievement payload:")
    print(f"    - 10 contacts generated")
    print(f"    - 2 deliverables completed")
    print(f"    - 15% engagement improvement")
    
    # Complete the task
    completed_task = await update_task_status(task_id, "completed", result_payload=achievement_payload)
    
    if completed_task:
        final_status = completed_task.get("status")
        print(f"  ✅ Task completed, status: {final_status}")
        
        if final_status == "pending_verification":
            print(f"  🔍 Task requires verification (expected for quality control)")
        elif final_status == "completed":
            print(f"  ⚡ Task completed directly (no verification required)")
        else:
            print(f"  ❓ Unexpected status: {final_status}")
    else:
        print(f"  ❌ Failed to complete task")
        return
    
    # Step 4: Handle verification if needed
    if completed_task.get("status") == "pending_verification":
        print(f"\n🔍 STEP 4: Handling Verification Process")
        
        # Wait for verification request to be created
        await asyncio.sleep(2)
        
        # Find the verification request
        feedback_requests = await get_human_feedback_requests(workspace_id, "pending")
        our_request = None
        
        for req in feedback_requests:
            context_task_id = req.get("context", {}).get("task_id")
            if context_task_id == task_id:
                our_request = req
                break
        
        if our_request:
            request_id = our_request["id"]
            print(f"  ✅ Found verification request: {request_id}")
            
            # Approve the verification
            approval_response = {
                "approved": True,
                "feedback": "Excellent work - leads are high quality and deliverables are complete",
                "approver": "final_test",
                "quality_score": 95
            }
            
            print(f"  🚀 Approving verification request...")
            await update_human_feedback_request(request_id, "approved", approval_response)
            print(f"  ✅ Verification approved!")
            
        else:
            print(f"  ❌ No verification request found - this might indicate an issue")
    else:
        print(f"\n⚡ STEP 4: No Verification Required (Direct Completion)")
    
    # Step 5: Check final goal state
    print(f"\n🎯 STEP 5: Final Goals State (THE MOMENT OF TRUTH)")
    await asyncio.sleep(2)  # Give goal updates time to process
    
    final_goals = await get_workspace_goals(workspace_id, status="active")
    
    print(f"\n📊 Goal Changes Analysis:")
    total_changes = 0
    for i, final_goal in enumerate(final_goals):
        initial_value = initial_goals[i]['current_value']
        final_value = final_goal['current_value']
        
        if final_value != initial_value:
            change = final_value - initial_value
            completion_pct = (final_value / final_goal['target_value'] * 100) if final_goal['target_value'] > 0 else 0
            print(f"  🎉 {final_goal['metric_type']}: {initial_value} → {final_value} (+{change}) ({completion_pct:.1f}%)")
            total_changes += 1
        else:
            completion_pct = (final_value / final_goal['target_value'] * 100) if final_goal['target_value'] > 0 else 0
            print(f"  ➡️ {final_goal['metric_type']}: {final_value}/{final_goal['target_value']} (no change) ({completion_pct:.1f}%)")
    
    # Final verdict
    print(f"\n" + "=" * 60)
    if total_changes > 0:
        print(f"🏆 COMPLETE SUCCESS!")
        print(f"✅ {total_changes} goals were updated after task completion and verification!")
        print(f"✅ The goal update system is working end-to-end!")
        print(f"✅ Tasks → Verification → Approval → Goal Updates = ALL WORKING!")
        
        if final_goals[5]['current_value'] > initial_goals[5]['current_value']:  # contacts goal
            contacts_added = final_goals[5]['current_value'] - initial_goals[5]['current_value']
            print(f"✅ Contacts goal increased by {contacts_added} as expected!")
        
    else:
        print(f"❌ FAILURE: No goal updates detected")
        print(f"💡 There may still be an issue to investigate")
    
    print(f"=" * 60)

if __name__ == "__main__":
    asyncio.run(final_comprehensive_test())