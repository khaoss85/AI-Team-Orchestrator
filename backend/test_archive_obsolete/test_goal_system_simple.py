#!/usr/bin/env python3
"""
🎯 SIMPLE GOAL SYSTEM TEST
Test semplificato per verificare il sistema goal-driven
"""

import asyncio
import sys
import os
from uuid import UUID
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import supabase
# Universal metric types - no hardcoded business enums

async def test_basic_setup():
    """Test base per verificare che le tabelle esistano e siano accessibili"""
    print("🔍 TEST SETUP BASE")
    print("="*50)
    
    # 1. Check workspace_goals table
    try:
        response = supabase.table("workspace_goals").select("*").limit(1).execute()
        print("✅ workspace_goals table accessible")
        print(f"   Existing goals: {len(response.data) if response.data else 0}")
    except Exception as e:
        print(f"❌ workspace_goals error: {e}")
        return False
    
    # 2. Check workspace_insights table
    try:
        response = supabase.table("workspace_insights").select("*").limit(1).execute()
        print("✅ workspace_insights table accessible")
        print(f"   Existing insights: {len(response.data) if response.data else 0}")
    except Exception as e:
        print(f"❌ workspace_insights error: {e}")
        return False
    
    # 3. Check tasks table has new columns
    try:
        response = supabase.table("tasks").select("goal_id,metric_type,is_corrective").limit(1).execute()
        print("✅ tasks table has goal-driven columns")
    except Exception as e:
        print(f"❌ tasks columns error: {e}")
        return False
    
    # 4. Get a workspace for testing
    response = supabase.table("workspaces").select("*").limit(1).execute()
    if response.data:
        workspace = response.data[0]
        print(f"\n📁 Test Workspace: {workspace['name']}")
        print(f"   ID: {workspace['id']}")
        print(f"   Goal: {workspace.get('goal', 'No goal set')[:80]}...")
        return workspace['id']
    else:
        print("❌ No workspace found for testing")
        return None

async def test_goal_creation(workspace_id):
    """Test creating a workspace goal"""
    print("\n🎯 TEST GOAL CREATION")
    print("="*50)
    
    # Simple goal data
    goal_data = {
        "workspace_id": workspace_id,
        "metric_type": "contacts",
        "target_value": 50,
        "unit": "contacts",
        "description": "Test: Collect 50 ICP contacts",
        "priority": 1,
        "status": "active"
    }
    
    try:
        # Check if already exists
        existing = supabase.table("workspace_goals").select("*").eq(
            "workspace_id", workspace_id
        ).eq(
            "metric_type", "contacts"
        ).execute()
        
        if existing.data:
            print(f"ℹ️ Goal already exists for contacts metric")
            goal = existing.data[0]
        else:
            # Create new goal
            response = supabase.table("workspace_goals").insert(goal_data).execute()
            if response.data:
                goal = response.data[0]
                print(f"✅ Created goal: {goal['metric_type']} - Target: {goal['target_value']}")
            else:
                print("❌ Failed to create goal")
                return None
        
        # Display goal details
        print(f"\n📊 Goal Details:")
        print(f"   ID: {goal['id']}")
        print(f"   Metric: {goal['metric_type']}")
        print(f"   Progress: {goal['current_value']}/{goal['target_value']}")
        print(f"   Status: {goal['status']}")
        
        return goal['id']
        
    except Exception as e:
        print(f"❌ Error creating goal: {e}")
        return None

async def test_task_with_goal(workspace_id, goal_id):
    """Test creating a goal-driven task"""
    print("\n📋 TEST GOAL-DRIVEN TASK CREATION")
    print("="*50)
    
    task_data = {
        "workspace_id": workspace_id,
        "name": "Test: Collect 10 ICP contacts",
        "description": "Find and collect 10 high-quality ICP contacts with emails",
        "status": "pending",
        "priority": "high",
        "goal_id": goal_id,
        "metric_type": "contacts",
        "contribution_expected": 10,
        "numerical_target": {
            "metric": "contacts_collected",
            "target": 10,
            "unit": "contacts"
        },
        "is_corrective": False,
        "success_criteria": [
            "Find 10 real contacts with valid emails",
            "Complete profile information required",
            "No fake or placeholder data"
        ]
    }
    
    try:
        response = supabase.table("tasks").insert(task_data).execute()
        if response.data:
            task = response.data[0]
            print(f"✅ Created goal-driven task: {task['name']}")
            print(f"   ID: {task['id']}")
            print(f"   Goal ID: {task['goal_id']}")
            print(f"   Expected Contribution: {task['contribution_expected']}")
            return task['id']
        else:
            print("❌ Failed to create task")
            return None
    except Exception as e:
        print(f"❌ Error creating task: {e}")
        return None

async def test_views():
    """Test the analysis views"""
    print("\n📊 TEST ANALYSIS VIEWS")
    print("="*50)
    
    try:
        # Test workspace_goals_progress view
        response = supabase.table("workspace_goals_progress").select("*").limit(5).execute()
        print(f"✅ workspace_goals_progress view: {len(response.data)} active goals")
        
        for goal in response.data:
            print(f"   • {goal['metric_type']}: {goal['completion_percentage']}% complete")
            print(f"     Needs validation: {goal['needs_validation']}")
        
        # Test goal_task_performance view
        response = supabase.table("goal_task_performance").select("*").limit(5).execute()
        print(f"\n✅ goal_task_performance view: {len(response.data)} goal metrics")
        
        for metric in response.data:
            print(f"   • {metric['metric_type']}: {metric['completed_tasks']}/{metric['total_tasks']} tasks")
            print(f"     Completion rate: {metric['task_completion_rate']}%")
            
    except Exception as e:
        print(f"❌ Error testing views: {e}")

async def main():
    """Run simple tests"""
    print("🚀 SIMPLE GOAL-DRIVEN SYSTEM TEST")
    print(f"⏰ {asyncio.get_event_loop().time()}")
    print()
    
    # Test 1: Basic setup
    workspace_id = await test_basic_setup()
    if not workspace_id:
        print("\n❌ Setup failed. Check RLS policies or database connection.")
        return
    
    # Test 2: Goal creation
    goal_id = await test_goal_creation(workspace_id)
    
    # Test 3: Task creation
    if goal_id:
        await test_task_with_goal(workspace_id, goal_id)
    
    # Test 4: Views
    await test_views()
    
    print("\n✅ TESTS COMPLETED!")

if __name__ == "__main__":
    asyncio.run(main())