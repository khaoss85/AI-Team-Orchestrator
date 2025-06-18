#!/usr/bin/env python3
"""
Check if the goal update fix worked by examining the final state
"""

import asyncio
import logging
from database import supabase, get_workspace_goals

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_final_results():
    """Check the final state after our fixes"""
    
    workspace_id = "3b387b5e-51c0-43eb-8e8a-e279e38dbfb5"
    
    print("🔍 Checking Final Results After Goal Update Fix")
    print("=" * 50)
    
    # Check our test task
    test_task_id = "625ee706-427d-4589-b70d-e58f35d94fd8"
    
    print(f"\n📋 STEP 1: Checking Test Task Status")
    response = supabase.table("tasks").select("*").eq("id", test_task_id).execute()
    
    if response.data:
        task = response.data[0]
        print(f"  Task ID: {test_task_id}")
        print(f"  Name: {task.get('name')}")
        print(f"  Status: {task.get('status')}")
        print(f"  Updated: {task.get('updated_at')}")
        
        result = task.get('result', {})
        if result:
            print(f"  Result contains verification approval: {bool(result.get('verification_approved_at'))}")
            if result.get('achievements'):
                print(f"  Achievements: {result.get('achievements')}")
    else:
        print(f"  ❌ Test task not found!")
    
    # Check current goals
    print(f"\n🎯 STEP 2: Checking Current Goals State")
    goals = await get_workspace_goals(workspace_id, status="active")
    
    any_progress = False
    for goal in goals:
        completion_pct = (goal['current_value'] / goal['target_value'] * 100) if goal['target_value'] > 0 else 0
        print(f"  - {goal['metric_type']}: {goal['current_value']}/{goal['target_value']} ({completion_pct:.1f}%)")
        
        if goal['current_value'] > 0:
            any_progress = True
            if goal.get('last_progress_date'):
                print(f"    📅 Last updated: {goal.get('last_progress_date')}")
    
    # Check all completed tasks in this workspace
    print(f"\n📊 STEP 3: Checking All Completed Tasks")
    response = supabase.table("tasks").select("id, name, status, updated_at").eq("workspace_id", workspace_id).eq("status", "completed").execute()
    
    completed_tasks = response.data or []
    print(f"  Found {len(completed_tasks)} completed tasks:")
    
    for task in completed_tasks:
        print(f"    - {task.get('name')} ({task.get('id')}) - {task.get('updated_at')}")
    
    # Check all feedback requests
    print(f"\n📝 STEP 4: Checking All Feedback Requests")
    response = supabase.table("human_feedback_requests").select("*").eq("workspace_id", workspace_id).execute()
    
    all_requests = response.data or []
    print(f"  Found {len(all_requests)} total feedback requests:")
    
    for req in all_requests:
        context = req.get('context', {})
        task_id = context.get('task_id') or req.get('task_id')
        print(f"    - {req.get('id')} ({req.get('status')}) for task {task_id}")
    
    # Final assessment
    print(f"\n" + "=" * 50)
    if any_progress:
        print(f"🎉 SUCCESS: Goals have progress!")
        print(f"✅ The goal update system is working!")
    elif completed_tasks:
        print(f"⚠️ PARTIAL: Tasks are completing but goals aren't updating")
        print(f"💡 There may still be an issue with goal progress calculation")
    else:
        print(f"❌ ISSUE: No completed tasks and no goal progress")
        print(f"💡 The verification approval may not be working correctly")
    print(f"=" * 50)

if __name__ == "__main__":
    asyncio.run(check_final_results())