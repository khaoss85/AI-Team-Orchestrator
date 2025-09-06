#!/usr/bin/env python3
"""
Test script to verify that the velocity calculation fix is working.
This will force validation for goals at 0% progress.
"""

import asyncio
from database import supabase
from services.goal_validation_optimizer import goal_validation_optimizer
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_velocity_fix():
    workspace_id = 'e29a33af-b473-4d9c-b983-f5c1aa70a830'
    
    print("\n🔍 TESTING VELOCITY FIX FOR 0% GOALS")
    print("=" * 70)
    
    # 1. Get all workspace goals and calculate their progress
    goals_response = supabase.table("workspace_goals").select("*").eq('workspace_id', workspace_id).execute()
    all_goals = goals_response.data or []
    
    # Filter for goals at 0% progress (calculate based on current_value/target_value)
    goals = []
    for goal in all_goals:
        # Simple progress calculation
        current = goal.get("current_value", 0)
        target = goal.get("target_value", 100)
        progress = (current / target * 100) if target > 0 else 0
        goal['progress'] = progress
        
        if progress <= 0:
            goals.append(goal)
    
    print(f"\n📊 GOALS AT 0% PROGRESS: {len(goals)} out of {len(all_goals)} total")
    
    for goal in goals[:3]:  # Test first 3 goals
        goal_id = goal.get("id")
        description = goal.get("description")
        progress = goal.get("progress", 0)
        
        print(f"\n🎯 Testing Goal: {description[:40]}...")
        print(f"   ID: {goal_id}")
        print(f"   Progress: {progress}%")
        
        # Test the optimizer's decision
        optimization_result = await goal_validation_optimizer.should_proceed_with_validation(
            workspace_id=workspace_id,
            goal_data=goal,
            recent_tasks=[]
        )
        
        print(f"\n   🚦 OPTIMIZATION RESULT:")
        print(f"      Should Proceed: {optimization_result.should_proceed}")
        print(f"      Decision: {optimization_result.decision.value}")
        print(f"      Reason: {optimization_result.reason}")
        print(f"      Confidence: {optimization_result.confidence}")
        
        if optimization_result.should_proceed:
            print(f"   ✅ SUCCESS: Goal at 0% progress will be validated!")
        else:
            print(f"   ❌ FAILED: Goal at 0% progress is still being skipped")
    
    # 2. Check workspace velocity analysis
    print(f"\n\n📈 WORKSPACE VELOCITY ANALYSIS:")
    workspace_analysis = await goal_validation_optimizer._get_workspace_progress_analysis(workspace_id)
    
    print(f"   Total tasks: {workspace_analysis.total_tasks}")
    print(f"   Completed tasks: {workspace_analysis.completed_tasks}")
    print(f"   Overall completion rate: {workspace_analysis.overall_completion_rate:.2f}")
    print(f"   Velocity classification: {workspace_analysis.velocity_classification.value}")
    
    print(f"\n✅ FIX VERIFICATION COMPLETE")
    
    # 3. Force update last_validation_at to trigger validation
    print(f"\n🔧 FORCING VALIDATION BY CLEARING last_validation_at...")
    # Get goal IDs at 0% progress
    goal_ids_at_zero = [g['id'] for g in goals]
    if goal_ids_at_zero:
        update_response = supabase.table("workspace_goals").update({
            "last_validation_at": None
        }).in_('id', goal_ids_at_zero).execute()
    
        if update_response.data:
            print(f"   ✅ Cleared last_validation_at for {len(update_response.data)} goals")
            print(f"   Goals should now be picked up in the next monitoring cycle")

if __name__ == "__main__":
    asyncio.run(test_velocity_fix())