#!/usr/bin/env python3

import asyncio
import logging
import json
from database import get_task, get_workspace_goals, _extract_task_achievements, _calculate_goal_increment

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_goal_tracking(task_id: str):
    """Debug specific task goal tracking"""
    
    print(f"\n🔍 DEBUGGING GOAL TRACKING FOR TASK: {task_id}")
    print("=" * 60)
    
    # Get task details
    task = await get_task(task_id)
    if not task:
        print(f"❌ Task {task_id} not found!")
        return
        
    workspace_id = task.get("workspace_id")
    task_name = task.get("name", "")
    result_payload = task.get("result", {})
    
    print(f"📝 Task Name: {task_name}")
    print(f"🏢 Workspace ID: {workspace_id}")
    print(f"📊 Result payload keys: {list(result_payload.keys()) if result_payload else 'None'}")
    
    # Get workspace goals
    workspace_goals = await get_workspace_goals(workspace_id, status="active")
    print(f"\n🎯 WORKSPACE GOALS ({len(workspace_goals)} active):")
    for i, goal in enumerate(workspace_goals, 1):
        metric_type = goal.get("metric_type", "")
        current = goal.get("current_value", 0)
        target = goal.get("target_value", 0)
        print(f"  {i}. {metric_type}: {current}/{target}")
    
    if not workspace_goals:
        print("❌ No active workspace goals found!")
        return
    
    # Extract achievements
    print(f"\n📊 EXTRACTING ACHIEVEMENTS FROM TASK RESULT:")
    achievements = await _extract_task_achievements(result_payload, task_name)
    
    print(f"Raw achievements: {achievements}")
    non_zero = {k: v for k, v in achievements.items() if v > 0}
    if non_zero:
        print(f"Non-zero achievements: {non_zero}")
    else:
        print("❌ No achievements extracted!")
    
    # Test goal mapping
    print(f"\n🎯 TESTING GOAL MAPPING:")
    for goal in workspace_goals:
        goal_metric_type = goal.get("metric_type", "")
        increment = _calculate_goal_increment(achievements, goal_metric_type)
        print(f"  {goal_metric_type} -> increment: {increment}")
    
    # Show result payload details for analysis
    print(f"\n📋 RESULT PAYLOAD ANALYSIS:")
    if result_payload:
        print(f"Result payload structure:")
        for key, value in result_payload.items():
            if isinstance(value, list):
                print(f"  {key} (list): {len(value)} items")
                if value and len(value) <= 3:
                    print(f"    Sample: {value}")
            elif isinstance(value, dict):
                print(f"  {key} (dict): {len(value)} keys")
                if len(value) <= 5:
                    print(f"    Keys: {list(value.keys())}")
            else:
                print(f"  {key}: {type(value).__name__} = {str(value)[:100]}...")
    else:
        print("❌ No result payload!")

async def debug_specific_task():
    """Debug a specific task from the log"""
    
    # Based on the log, this task created email sequences but wasn't counted
    task_id = "b75f4de9-4eef-41c0-83a1-9e9b75779e97"  # Email sequence task from log
    
    await debug_goal_tracking(task_id)

if __name__ == "__main__":
    asyncio.run(debug_specific_task())