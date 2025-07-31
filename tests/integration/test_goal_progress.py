#!/usr/bin/env python3
"""
Test Goal Progress Calculation

Tests the goal progress calculation system to ensure goals are properly
created, updated, and linked to task completion.
"""

import asyncio
import os
import sys
from datetime import datetime
from uuid import uuid4

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import supabase, update_goal_progress, get_workspace_goals
from automated_goal_monitor import automated_goal_monitor

async def main():
    """Test goal progress calculation system"""
    
    print("🧪 TESTING GOAL PROGRESS CALCULATION")
    print("=" * 60)
    
    # Test 1: Check existing workspaces and goals
    print(f"\n📊 TEST 1: Database State Analysis")
    
    # Check workspaces
    workspaces_response = supabase.table("workspaces").select("id, name, goal, status").execute()
    workspaces = workspaces_response.data or []
    
    print(f"   Total workspaces: {len(workspaces)}")
    
    if not workspaces:
        print(f"   ❌ No workspaces found - need to create test data")
        
        # Create a test workspace
        test_workspace_data = {
            'id': str(uuid4()),
            'name': 'Goal Progress Test Workspace',
            'description': 'Test workspace for goal progress validation',
            'goal': 'Create a comprehensive AI-driven project management system with automated task assignment, quality assurance, and deliverable generation',
            'status': 'active',
            'user_id': str(uuid4()),  # Dummy user ID for testing
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        try:
            workspace_result = supabase.table("workspaces").insert(test_workspace_data).execute()
            if workspace_result.data:
                workspace_id = workspace_result.data[0]['id']
                print(f"   ✅ Created test workspace: {workspace_id}")
                workspaces = [workspace_result.data[0]]
            else:
                print(f"   ❌ Failed to create test workspace")
                return
        except Exception as e:
            print(f"   ❌ Error creating workspace: {e}")
            return
    
    # Use first workspace for testing
    test_workspace = workspaces[0]
    workspace_id = test_workspace['id']
    workspace_goal = test_workspace.get('goal', '')
    
    print(f"   Using workspace: {test_workspace['name']}")
    print(f"   Workspace ID: {workspace_id}")
    print(f"   Goal text: {workspace_goal[:100]}{'...' if len(workspace_goal) > 100 else ''}")
    
    # Test 2: Check workspace goals (decomposed goals)
    print(f"\n🎯 TEST 2: Workspace Goals Analysis")
    
    try:
        workspace_goals = await get_workspace_goals(workspace_id)
        print(f"   Workspace goals found: {len(workspace_goals)}")
        
        if not workspace_goals:
            print(f"   ⚠️  No workspace goals found - may need goal decomposition")
            
            # Try to trigger goal creation
            print(f"   🔧 Attempting goal decomposition...")
            result = await automated_goal_monitor._trigger_immediate_goal_analysis(workspace_id)
            
            if result.get('success'):
                print(f"   ✅ Goal analysis triggered successfully")
                
                # Check again
                workspace_goals = await get_workspace_goals(workspace_id)
                print(f"   New workspace goals: {len(workspace_goals)}")
            else:
                print(f"   ❌ Goal analysis failed: {result.get('reason', 'unknown')}")
        
        # Display goal details
        for i, goal in enumerate(workspace_goals, 1):
            print(f"   Goal {i}:")
            print(f"      ID: {goal['id']}")
            print(f"      Metric: {goal['metric_type']}")
            print(f"      Progress: {goal['current_value']}/{goal['target_value']}")
            print(f"      Status: {goal.get('status', 'unknown')}")
            if goal.get('description'):
                desc_preview = goal['description'][:80] + '...' if len(goal['description']) > 80 else goal['description']
                print(f"      Description: {desc_preview}")
        
    except Exception as e:
        print(f"   ❌ Error checking workspace goals: {e}")
        workspace_goals = []
    
    # Test 3: Test goal progress update functionality
    print(f"\n📈 TEST 3: Goal Progress Update Test")
    
    if workspace_goals:
        test_goal = workspace_goals[0]
        goal_id = test_goal['id']
        
        print(f"   Testing with goal: {test_goal['metric_type']}")
        print(f"   Current progress: {test_goal['current_value']}/{test_goal['target_value']}")
        
        # Test progress increment
        increment_value = 5.0
        test_task_id = str(uuid4())
        
        try:
            business_context = {
                'quality_score': 0.85,
                'task_type': 'test_completion',
                'complexity': 'medium'
            }
            
            result = await update_goal_progress(
                goal_id=goal_id,
                increment=increment_value,
                task_id=test_task_id,
                task_business_context=business_context
            )
            
            if result:
                new_value = result.get('current_value', test_goal['current_value'])
                print(f"   ✅ Goal progress updated: {test_goal['current_value']} → {new_value}")
                print(f"   Increment applied: +{increment_value}")
                
                # Check if progress was logged
                logs_response = supabase.table("goal_progress_logs").select("*").eq("goal_id", goal_id).eq("task_id", test_task_id).execute()
                
                if logs_response.data:
                    log_entry = logs_response.data[0]
                    print(f"   ✅ Progress logged: {log_entry['progress_percentage']:.1f}%")
                    print(f"   Quality score: {log_entry.get('quality_score', 'N/A')}")
                else:
                    print(f"   ⚠️  Progress not logged in goal_progress_logs")
                    
            else:
                print(f"   ❌ Goal progress update failed")
                
        except Exception as e:
            print(f"   ❌ Error updating goal progress: {e}")
    else:
        print(f"   ⚠️  No goals available for progress testing")
    
    # Test 4: Check goal completion calculation
    print(f"\n🏁 TEST 4: Goal Completion Analysis")
    
    try:
        # Refresh workspace goals to see current state
        current_goals = await get_workspace_goals(workspace_id)
        
        total_goals = len(current_goals)
        completed_goals = len([g for g in current_goals if g.get('current_value', 0) >= g.get('target_value', 1)])
        completion_rate = (completed_goals / total_goals * 100) if total_goals > 0 else 0
        
        print(f"   Total goals: {total_goals}")
        print(f"   Completed goals: {completed_goals}")
        print(f"   Completion rate: {completion_rate:.1f}%")
        
        if completion_rate > 0:
            print(f"   ✅ Goal completion tracking working")
        else:
            print(f"   ⚠️  No completed goals found")
            
        # Check average progress
        if current_goals:
            total_progress = sum(
                (g.get('current_value', 0) / g.get('target_value', 1) * 100) if g.get('target_value', 0) > 0 else 0 
                for g in current_goals
            )
            avg_progress = total_progress / len(current_goals)
            print(f"   Average progress: {avg_progress:.1f}%")
            
            if avg_progress > 10:  # Some reasonable progress
                print(f"   ✅ Goals showing realistic progress")
            else:
                print(f"   ⚠️  Goals showing minimal progress")
        
    except Exception as e:
        print(f"   ❌ Error analyzing goal completion: {e}")
    
    # Test 5: Deliverable trigger conditions
    print(f"\n📦 TEST 5: Deliverable Trigger Analysis")
    
    try:
        from database import should_trigger_deliverable_aggregation
        
        should_trigger = await should_trigger_deliverable_aggregation(workspace_id)
        print(f"   Should trigger deliverable: {should_trigger}")
        
        # Check completed tasks
        completed_tasks = supabase.table("tasks").select("id, name, status").eq("workspace_id", workspace_id).eq("status", "completed").execute()
        completed_count = len(completed_tasks.data) if completed_tasks.data else 0
        
        print(f"   Completed tasks: {completed_count}")
        
        # Check existing deliverables
        deliverables = supabase.table("deliverables").select("id, title, status").eq("workspace_id", workspace_id).execute()
        deliverable_count = len(deliverables.data) if deliverables.data else 0
        
        print(f"   Existing deliverables: {deliverable_count}")
        
        if should_trigger and completed_count > 0:
            print(f"   ✅ Deliverable trigger conditions met")
        elif completed_count == 0:
            print(f"   ℹ️  No completed tasks for deliverable creation")
        else:
            print(f"   ⚠️  Deliverable trigger conditions not met despite completed tasks")
            
    except Exception as e:
        print(f"   ❌ Error checking deliverable triggers: {e}")
    
    # Summary
    print(f"\n📈 GOAL PROGRESS TEST SUMMARY")
    
    has_goals = len(workspace_goals) > 0
    goals_have_progress = any(g.get('current_value', 0) > 0 for g in workspace_goals) if workspace_goals else False
    progress_can_update = 'result' in locals() and result is not None
    
    print(f"   Goal Creation: {'✅ Working' if has_goals else '❌ Failed'}")
    print(f"   Goal Progress: {'✅ Working' if goals_have_progress else '⚠️  No progress'}")
    print(f"   Progress Updates: {'✅ Working' if progress_can_update else '❌ Failed'}")
    
    if has_goals and progress_can_update:
        print(f"\n🎉 PHASE 3 SUCCESS: Goal progress calculation working!")
    else:
        print(f"\n⚠️  PHASE 3 ISSUES: Goal system needs attention")
        if not has_goals:
            print(f"   - Goals not being created from workspace goal text")
        if not progress_can_update:
            print(f"   - Goal progress updates failing")

if __name__ == "__main__":
    asyncio.run(main())