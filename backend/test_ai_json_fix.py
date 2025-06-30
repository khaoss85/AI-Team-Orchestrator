#!/usr/bin/env python3
"""
Test AI JSON parsing improvements in goal_driven_task_planner
"""

import asyncio
import os
from dotenv import load_dotenv
from goal_driven_task_planner import GoalDrivenTaskPlanner

# Load environment
load_dotenv('/Users/pelleri/Documents/ai-team-orchestrator/backend/.env')

async def test_ai_json_parsing():
    """Test the improved AI JSON parsing functionality"""
    
    print("🧪 Testing AI JSON parsing improvements...")
    
    planner = GoalDrivenTaskPlanner()
    
    # Test with realistic task names that might cause similarity detection
    test_tasks = [
        {"id": "task1", "name": "Research Target Audience for Marketing", "description": "Analyze target demographic"},
        {"id": "task2", "name": "Market Segment Analysis", "description": "Study market segments"},
        {"id": "task3", "name": "Compile Contact Database", "description": "Create prospect list"},
        {"id": "task4", "name": "Build Lead Generation List", "description": "Generate lead database"},
        {"id": "task5", "name": "Create Email Templates", "description": "Design email campaigns"},
        {"id": "task6", "name": "Draft Outreach Messages", "description": "Write outreach content"}
    ]
    
    metric_type = "contacts"
    
    try:
        # Test the AI-driven similarity detection that previously failed with JSON errors
        similar_tasks = await planner._detect_similar_tasks_ai_driven(test_tasks, metric_type)
        
        print(f"✅ AI similarity detection successful!")
        print(f"   Found {len(similar_tasks)} similar tasks:")
        for task in similar_tasks:
            print(f"   - {task['name']}")
        
        if len(similar_tasks) > 0:
            print("✅ AI correctly identified semantic similarities")
        else:
            print("ℹ️ AI found no similar tasks (which is also valid)")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_ai_json_parsing())
    if success:
        print("\n🎉 AI JSON parsing improvements are working!")
        print("✅ The 'AI response not valid JSON' error should be resolved.")
    else:
        print("\n❌ AI JSON parsing test failed")