#!/usr/bin/env python3
"""
Accurate test to see if our fix actually added goal progress
"""

import asyncio
import logging
from database import supabase, get_workspace_goals

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_goal_progress_accurately():
    """Test if our verification approval actually added goal progress"""
    
    workspace_id = "3b387b5e-51c0-43eb-8e8a-e279e38dbfb5"
    
    print("🔍 Accurate Goal Progress Analysis")
    print("=" * 50)
    
    # Show current state
    print(f"\n📊 Current Goals State:")
    goals = await get_workspace_goals(workspace_id, status="active")
    
    for goal in goals:
        completion_pct = (goal['current_value'] / goal['target_value'] * 100) if goal['target_value'] > 0 else 0
        print(f"  - {goal['metric_type']}: {goal['current_value']}/{goal['target_value']} ({completion_pct:.1f}%)")
        
        # Check for recent updates
        last_progress = goal.get('last_progress_date')
        if last_progress:
            print(f"    📅 Last progress: {last_progress}")
        else:
            print(f"    📅 Last progress: Never")
    
    # Check our test task details
    test_task_id = "625ee706-427d-4589-b70d-e58f35d94fd8"
    print(f"\n📋 Test Task Analysis:")
    response = supabase.table("tasks").select("*").eq("id", test_task_id).execute()
    
    if response.data:
        task = response.data[0]
        print(f"  Task: {task.get('name')}")
        print(f"  Status: {task.get('status')}")
        print(f"  Updated: {task.get('updated_at')}")
        
        result = task.get('result', {})
        achievements = result.get('achievements', {})
        print(f"  Achievements in result:")
        for key, value in achievements.items():
            print(f"    - {key}: {value}")
        
        # Check if verification was approved
        verification_approved = result.get('verification_approved_at')
        if verification_approved:
            print(f"  ✅ Verification approved at: {verification_approved}")
        else:
            print(f"  ❌ No verification approval found")
    
    # Key insight: Check if the task status was actually updated to completed
    print(f"\n🔍 Key Issue Analysis:")
    if response.data:
        task = response.data[0]
        status = task.get('status')
        result = task.get('result', {})
        
        if status == "pending_verification":
            print(f"  ❌ ISSUE FOUND: Task is still in 'pending_verification' status")
            print(f"      This means our direct database update didn't work")
            print(f"      Goal updates only trigger when status = 'completed'")
            
            if result.get('verification_approved_at'):
                print(f"  ✅ But verification WAS approved, so the issue is in the task completion step")
            else:
                print(f"  ❌ Verification was not properly approved")
        
        elif status == "completed":
            print(f"  ✅ Task is completed - goal updates should have triggered")
            
            # Check if goal updates actually ran
            goals_with_recent_updates = [g for g in goals if g.get('last_progress_date')]
            if goals_with_recent_updates:
                print(f"  ✅ Found {len(goals_with_recent_updates)} goals with recent updates")
            else:
                print(f"  ❌ No goals have recent progress updates")
    
    # Test the goal update function directly
    print(f"\n🧪 Testing Goal Update Function Directly:")
    if response.data:
        task = response.data[0]
        result = task.get('result', {})
        
        print(f"  Testing _update_goal_progress_from_task_completion...")
        
        try:
            from database import _update_goal_progress_from_task_completion
            await _update_goal_progress_from_task_completion(test_task_id, result)
            print(f"  ✅ Goal update function completed without errors")
            
            # Check goals again
            print(f"\n📊 Goals After Direct Function Call:")
            updated_goals = await get_workspace_goals(workspace_id, status="active")
            
            changes_detected = False
            for i, updated_goal in enumerate(updated_goals):
                old_value = goals[i]['current_value']
                new_value = updated_goal['current_value']
                
                if new_value != old_value:
                    change = new_value - old_value
                    completion_pct = (new_value / updated_goal['target_value'] * 100) if updated_goal['target_value'] > 0 else 0
                    print(f"    🎉 {updated_goal['metric_type']}: {old_value} → {new_value} (+{change}) ({completion_pct:.1f}%)")
                    changes_detected = True
                else:
                    completion_pct = (new_value / updated_goal['target_value'] * 100) if updated_goal['target_value'] > 0 else 0
                    print(f"    ➡️ {updated_goal['metric_type']}: {new_value}/{updated_goal['target_value']} (no change) ({completion_pct:.1f}%)")
            
            if changes_detected:
                print(f"\n  🎉 SUCCESS: Direct function call updated goals!")
                print(f"  💡 The issue was that the task wasn't properly completed")
            else:
                print(f"\n  ❌ ISSUE: Even direct function call didn't update goals")
                print(f"  💡 There may be an issue with the goal update logic itself")
        
        except Exception as e:
            print(f"  ❌ Error calling goal update function: {e}")
    
    print(f"\n" + "=" * 50)

if __name__ == "__main__":
    asyncio.run(test_goal_progress_accurately())