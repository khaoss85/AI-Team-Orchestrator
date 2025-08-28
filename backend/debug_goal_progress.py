#!/usr/bin/env python3
"""
Debug script per investigare il goal progress vs deliverables discrepancy
"""
import asyncio
import json
from database import get_workspace_goals, get_deliverables, get_tasks

async def debug_goal_progress():
    workspace_id = "db18803c-3718-4612-a34b-79b1167ac62f"
    goal_id = "36228534-d5db-4f12-8cda-21efe0c6373c"  # Email campaign goal al 67%
    
    print(f"🔍 Debugging Goal Progress for: {goal_id}")
    print("=" * 80)
    
    try:
        # Get goal data
        goals = await get_workspace_goals(workspace_id)
        goal_data = next((g for g in goals if g['id'] == goal_id), None)
        
        if not goal_data:
            print(f"❌ Goal {goal_id} not found!")
            return
        
        print(f"📊 GOAL OVERVIEW:")
        print(f"   Title: {goal_data.get('title', 'N/A')}")
        print(f"   Progress: {goal_data.get('progress', 0)}%")
        print(f"   Status: {goal_data.get('status', 'unknown')}")
        print(f"   Current Value: {goal_data.get('current_value', 0)}")
        print(f"   Target Value: {goal_data.get('target_value', 0)}")
        print()
        
        # Get related data
        tasks = await get_tasks(workspace_id)
        goal_tasks = [t for t in tasks if t.get('goal_id') == goal_id]
        
        deliverables = await get_deliverables(workspace_id, goal_id=goal_id)
        
        print(f"📋 TASKS BREAKDOWN ({len(goal_tasks)} total):")
        
        task_stats = {}
        for task in goal_tasks:
            status = task.get('status', 'unknown')
            task_stats[status] = task_stats.get(status, 0) + 1
            
            print(f"   • {task.get('title', 'No title')[:60]}")
            print(f"     Status: {status} | Priority: {task.get('priority', 'N/A')}")
            print(f"     Created: {task.get('created_at', 'N/A')}")
            print(f"     Updated: {task.get('updated_at', 'N/A')}")
            print()
        
        print(f"📈 TASK STATUS SUMMARY:")
        for status, count in task_stats.items():
            percentage = (count / len(goal_tasks) * 100) if goal_tasks else 0
            print(f"   {status}: {count} tasks ({percentage:.1f}%)")
        print()
        
        # Analyze deliverables
        print(f"📦 DELIVERABLES BREAKDOWN ({len(deliverables)} total):")
        
        deliverable_stats = {}
        for deliverable in deliverables:
            status = deliverable.get('status', 'unknown')
            deliverable_stats[status] = deliverable_stats.get(status, 0) + 1
            
            print(f"   • {deliverable.get('title', 'No title')[:60]}")
            print(f"     Status: {status} | Type: {deliverable.get('type', 'N/A')}")
            print(f"     Task ID: {deliverable.get('task_id', 'None')}")
            print(f"     Business Value: {deliverable.get('business_value_score', 'N/A')}")
            print()
        
        print(f"📊 DELIVERABLE STATUS SUMMARY:")
        for status, count in deliverable_stats.items():
            percentage = (count / len(deliverables) * 100) if deliverables else 0
            print(f"   {status}: {count} deliverables ({percentage:.1f}%)")
        print()
        
        # Calculate expected progress based on tasks
        completed_tasks = task_stats.get('completed', 0)
        total_tasks = len(goal_tasks)
        calculated_progress = (completed_tasks / total_tasks * 100) if total_tasks else 0
        
        print(f"🔢 PROGRESS CALCULATION ANALYSIS:")
        print(f"   Reported Progress: {goal_data.get('progress', 0)}%")
        print(f"   Calculated from Tasks: {calculated_progress:.1f}%")
        print(f"   Total Tasks: {total_tasks}")
        print(f"   Completed Tasks: {completed_tasks}")
        print()
        
        # Identify discrepancy
        reported_progress = goal_data.get('progress', 0)
        discrepancy = abs(reported_progress - calculated_progress)
        
        if discrepancy > 5:  # Allow for small rounding differences
            print(f"⚠️  DISCREPANCY DETECTED:")
            print(f"   Gap: {discrepancy:.1f}%")
            print(f"   This suggests progress is calculated differently than task completion")
            print()
        
        # Show what UI is missing
        non_completed_deliverables = [d for d in deliverables if d.get('status') != 'completed']
        if non_completed_deliverables:
            print(f"👀 HIDDEN FROM UI ({len(non_completed_deliverables)} items):")
            for deliverable in non_completed_deliverables:
                print(f"   • {deliverable.get('title', 'No title')[:60]}")
                print(f"     Status: {deliverable.get('status')} | Why hidden: Status not 'completed'")
            print()
        
        print("🎯 RECOMMENDATIONS:")
        print("   1. Show ALL deliverable statuses in UI, not just 'completed'")
        print("   2. Add status indicators (completed/failed/pending/in_progress)")
        print("   3. Provide unblocking actions for failed/pending items")
        print("   4. Match UI progress display with backend calculation method")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_goal_progress())