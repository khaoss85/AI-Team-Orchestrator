#!/usr/bin/env python3
"""
🔧 Goal Progress Reset Tool
Reset workspace goals that have been incorrectly marked as complete due to failed tasks
"""

import asyncio
import os
from database import supabase, get_workspace_goals

async def reset_incorrect_goals():
    """Reset goals that were incorrectly updated by failed tasks"""
    
    print("🔧 Starting goal progress reset...")
    
    try:
        # Get all workspace goals
        all_goals_response = supabase.table("workspace_goals").select("*").execute()
        
        if not all_goals_response.data:
            print("No goals found")
            return
        
        print(f"Found {len(all_goals_response.data)} total goals")
        
        # Reset goals that are 100% complete but have no real deliverables
        reset_count = 0
        
        for goal in all_goals_response.data:
            workspace_id = goal.get("workspace_id")
            goal_id = goal.get("id")
            current_value = goal.get("current_value", 0)
            target_value = goal.get("target_value", 1)
            completion_percentage = goal.get("completion_percentage", 0)
            
            # Check if goal is marked as complete
            if completion_percentage >= 100 or current_value >= target_value:
                # Check if there are any actual completed tasks for this workspace
                tasks_response = supabase.table("tasks").select("*").eq("workspace_id", workspace_id).eq("status", "completed").execute()
                
                completed_tasks = len(tasks_response.data) if tasks_response.data else 0
                
                # Check for deliverables
                deliverables_response = supabase.table("deliverables").select("*").eq("workspace_id", workspace_id).execute()
                deliverables_count = len(deliverables_response.data) if deliverables_response.data else 0
                
                print(f"Goal {goal_id}: {completion_percentage}% complete, {completed_tasks} completed tasks, {deliverables_count} deliverables")
                
                # Reset if no completed tasks or deliverables
                if completed_tasks == 0 and deliverables_count == 0:
                    print(f"  🔄 Resetting goal {goal_id} - no real completed tasks or deliverables")
                    
                    # Reset the goal
                    reset_data = {
                        "current_value": 0,
                        "completion_percentage": 0.0,
                        "status": "active"
                    }
                    
                    update_result = supabase.table("workspace_goals").update(reset_data).eq("id", goal_id).execute()
                    
                    if update_result.data:
                        print(f"  ✅ Successfully reset goal {goal_id}")
                        reset_count += 1
                    else:
                        print(f"  ❌ Failed to reset goal {goal_id}")
                else:
                    print(f"  ✅ Goal {goal_id} appears legitimate (has real content)")
        
        print(f"\n🎯 Reset complete: {reset_count} goals reset")
        
    except Exception as e:
        print(f"❌ Error during goal reset: {e}")

if __name__ == "__main__":
    asyncio.run(reset_incorrect_goals())