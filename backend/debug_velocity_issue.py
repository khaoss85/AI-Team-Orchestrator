#!/usr/bin/env python3
"""
Debug script to identify why goal validation optimizer reports 0.80 velocity
when goals are at 0% progress.
"""

import asyncio
from database import supabase
from services.goal_validation_optimizer import goal_validation_optimizer

async def debug_velocity_issue():
    workspace_id = 'e29a33af-b473-4d9c-b983-f5c1aa70a830'
    
    print("\n🔍 DEBUGGING VELOCITY CALCULATION ISSUE")
    print("=" * 70)
    
    # 1. Check tasks in workspace
    tasks_response = supabase.table("tasks").select("*").eq('workspace_id', workspace_id).execute()
    tasks = tasks_response.data or []
    
    print(f"\n📊 TASKS ANALYSIS:")
    print(f"Total tasks: {len(tasks)}")
    completed_tasks = [t for t in tasks if t.get('status') == 'completed']
    print(f"Completed tasks: {len(completed_tasks)}")
    
    if tasks:
        print(f"\nTask Details (first 5):")
        for task in tasks[:5]:
            print(f"  - {task['id']}: {task['status']} - {task['name'][:30]}...")
        
        # Calculate what the optimizer would see
        total_tasks = len(tasks)
        completed_count = len(completed_tasks)
        
        if total_tasks > 0:
            completion_rate = completed_count / total_tasks
            print(f"\n📈 VELOCITY CALCULATION:")
            print(f"Completion rate: {completed_count}/{total_tasks} = {completion_rate:.2f}")
            
            # Check if this matches 0.80
            if abs(completion_rate - 0.80) < 0.01:
                print(f"⚠️ FOUND THE ISSUE: Completion rate is {completion_rate:.2f} which matches the 0.80 velocity!")
                print("This means old completed tasks are being counted!")
    else:
        print("\n❌ No tasks found in workspace!")
    
    # 2. Check workspace progress analysis
    print(f"\n🔬 CHECKING GOAL VALIDATION OPTIMIZER:")
    analysis = await goal_validation_optimizer._get_workspace_progress_analysis(workspace_id)
    
    print(f"Total tasks: {analysis.total_tasks}")
    print(f"Completed tasks: {analysis.completed_tasks}")
    print(f"Overall completion rate: {analysis.overall_completion_rate:.2f}")
    print(f"Velocity classification: {analysis.velocity_classification.value}")
    print(f"Recent completions (24h): {analysis.recent_completions_24h}")
    
    # 3. Check goals progress
    goals_response = supabase.table('workspace_goals').select('*').eq('workspace_id', workspace_id).execute()
    goals = goals_response.data or []
    
    print(f"\n🎯 GOALS ANALYSIS:")
    for goal in goals:
        print(f"Goal: {goal['description'][:40]}...")
        print(f"  Progress: {goal.get('progress', 0)}%")
        print(f"  Status: {goal.get('status', 'unknown')}")
    
    # 4. THE REAL ISSUE
    print(f"\n❗ ROOT CAUSE ANALYSIS:")
    print("The system is looking at ALL tasks in the workspace, including OLD completed tasks.")
    print("It should only look at tasks related to CURRENT active goals with 0% progress.")
    print("\n🔧 SOLUTION:")
    print("1. Filter tasks by goal_id to only count tasks for active goals")
    print("2. For goals with 0% progress and no tasks, force validation to generate tasks")
    print("3. Don't skip validation based on overall workspace velocity when individual goals are stuck")

if __name__ == "__main__":
    asyncio.run(debug_velocity_issue())