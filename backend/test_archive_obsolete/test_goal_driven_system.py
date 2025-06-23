#!/usr/bin/env python3
"""
🎯 TEST GOAL-DRIVEN SYSTEM
Test completo del nuovo sistema goal-driven per verificare:
1. Goal decomposition
2. Task generation goal-driven
3. Memory integration
4. Course correction
5. Automated monitoring
"""

import asyncio
import sys
import os
from uuid import UUID
from datetime import datetime
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import supabase
from models import WorkspaceGoal, WorkspaceGoalCreate, GoalStatus
from goal_driven_task_planner import goal_driven_task_planner
from goal_driven_project_manager import create_goal_driven_pm
from automated_goal_monitor import automated_goal_monitor
from ai_quality_assurance.goal_validator import goal_validator

# Test configuration
TEST_WORKSPACE_ID = None  # Will be set from actual workspace

async def setup_test_workspace():
    """Get or create a test workspace"""
    global TEST_WORKSPACE_ID
    
    # Get an existing workspace or create one
    response = supabase.table("workspaces").select("*").limit(1).execute()
    
    if response.data:
        workspace = response.data[0]
        TEST_WORKSPACE_ID = workspace["id"]
        print(f"✅ Using existing workspace: {workspace['name']} (ID: {TEST_WORKSPACE_ID})")
        
        # Update workspace goal to our test goal
        supabase.table("workspaces").update({
            "goal": "Raccogliere 50 contatti ICP (CMO/CTO di aziende SaaS europee) e creare 3 sequenze email per B2B outreach con ≥30% open rate"
        }).eq("id", TEST_WORKSPACE_ID).execute()
    else:
        print("❌ No workspace found. Please create a workspace first.")
        sys.exit(1)
    
    return TEST_WORKSPACE_ID

async def test_1_goal_decomposition():
    """Test 1: Decompose workspace goal into explicit numerical goals"""
    print("\n" + "="*60)
    print("🎯 TEST 1: GOAL DECOMPOSITION")
    print("="*60)
    
    workspace_goal = "Raccogliere 50 contatti ICP (CMO/CTO di aziende SaaS europee) e creare 3 sequenze email per B2B outreach con ≥30% open rate"
    print(f"📝 Original goal: {workspace_goal}")
    
    # Create explicit goals
    goals_to_create = [
        {
            "workspace_id": TEST_WORKSPACE_ID,
            "metric_type": "quantified_outputs",
            "target_value": 50,
            "unit": "contacts",
            "description": "Collect 50 ICP contacts (CMO/CTO di aziende SaaS europee)",
            "source_goal_text": workspace_goal,
            "priority": 1,
            "success_criteria": {
                "profile": "CMO/CTO",
                "company_type": "SaaS",
                "region": "Europe",
                "email_required": True
            }
        },
        {
            "workspace_id": TEST_WORKSPACE_ID,
            "metric_type": "quantified_outputs",
            "target_value": 3,
            "unit": "sequences",
            "description": "Create 3 email sequences for B2B outreach",
            "source_goal_text": workspace_goal,
            "priority": 2,
            "success_criteria": {
                "target_open_rate": 30,
                "sequence_length": "3-5 emails",
                "ready_for_deployment": True
            }
        }
    ]
    
    created_goals = []
    for goal_data in goals_to_create:
        # Check if goal already exists
        existing = supabase.table("workspace_goals").select("*").eq(
            "workspace_id", TEST_WORKSPACE_ID
        ).eq(
            "metric_type", goal_data["metric_type"].value
        ).execute()
        
        if existing.data:
            print(f"  ℹ️ Goal already exists: {goal_data['metric_type'].value}")
            created_goals.append(existing.data[0])
        else:
            response = supabase.table("workspace_goals").insert(goal_data).execute()
            if response.data:
                created_goals.append(response.data[0])
                print(f"  ✅ Created goal: {goal_data['metric_type'].value} - Target: {goal_data['target_value']}")
    
    # Verify goals
    print("\n📊 Workspace Goals Status:")
    for goal in created_goals:
        print(f"  • {goal['metric_type']}: {goal['current_value']}/{goal['target_value']} ({goal['status']})")
    
    return created_goals

async def test_2_goal_driven_task_generation():
    """Test 2: Generate concrete tasks from unmet goals"""
    print("\n" + "="*60)
    print("🎯 TEST 2: GOAL-DRIVEN TASK GENERATION")
    print("="*60)
    
    # Generate tasks using Goal-Driven Task Planner
    tasks = await goal_driven_task_planner.generate_tasks_for_unmet_goals(
        workspace_id=UUID(TEST_WORKSPACE_ID)
    )
    
    print(f"\n📋 Generated {len(tasks)} goal-driven tasks:")
    for i, task in enumerate(tasks, 1):
        print(f"\n{i}. Task: {task['name']}")
        print(f"   Type: {task.get('type', 'N/A')}")
        print(f"   Goal: {task.get('metric_type', 'N/A')}")
        print(f"   Expected Contribution: {task.get('contribution_expected', 0)}")
        print(f"   Priority: {task.get('priority', 'N/A')}")
        print(f"   Success Criteria: {len(task.get('success_criteria', []))} items")
        
        # Show numerical target
        if task.get('numerical_target'):
            target = task['numerical_target']
            print(f"   🎯 Numerical Target: {target.get('target')} {target.get('unit')}")
    
    return tasks

async def test_3_pm_review_and_approval():
    """Test 3: PM reviews and approves generated tasks"""
    print("\n" + "="*60)
    print("🎯 TEST 3: PM REVIEW AND APPROVAL (PM as Reviewer)")
    print("="*60)
    
    # Create Goal-Driven PM
    pm = create_goal_driven_pm(UUID(TEST_WORKSPACE_ID))
    
    # Orchestrate workspace goals
    result = await pm.orchestrate_workspace_goals()
    
    print(f"\n📊 Orchestration Result:")
    print(f"  Status: {result['status']}")
    print(f"  Tasks Generated: {result.get('tasks_generated', 0)}")
    print(f"  Tasks Approved: {result.get('tasks_approved', 0)}")
    print(f"  Tasks Created: {result.get('tasks_created', 0)}")
    print(f"  Tasks Needing Refinement: {result.get('requires_refinement', 0)}")
    
    if result.get('goal_analysis'):
        analysis = result['goal_analysis']
        print(f"\n📈 Goal Analysis:")
        print(f"  Active Goals: {analysis['active_goals']}")
        print(f"  Overall Progress: {analysis['overall_progress_pct']}%")
        
        for goal_data in analysis.get('goals_data', []):
            print(f"  • {goal_data['metric_type']}: {goal_data['current']}/{goal_data['target']} ({goal_data['completion_pct']}%)")
    
    if result.get('next_actions'):
        print(f"\n🎯 Recommended Next Actions:")
        for action in result['next_actions']:
            print(f"  • {action}")
    
    return result

async def test_4_simulate_task_completion():
    """Test 4: Simulate task completion and check goal progress update"""
    print("\n" + "="*60)
    print("🎯 TEST 4: SIMULATE TASK COMPLETION")
    print("="*60)
    
    # Get a pending goal-driven task
    response = supabase.table("tasks").select("*").eq(
        "workspace_id", TEST_WORKSPACE_ID
    ).not_.is_("goal_id", "null").eq(
        "status", "pending"
    ).limit(1).execute()
    
    if not response.data:
        print("❌ No pending goal-driven tasks found")
        return None
    
    task = response.data[0]
    print(f"\n📋 Simulating completion of task: {task['name']}")
    print(f"   Goal ID: {task['goal_id']}")
    print(f"   Expected Contribution: {task.get('contribution_expected', 0)}")
    
    # Simulate task completion with result
    if task['metric_type'] == 'contacts':
        # Simulate finding 10 contacts
        result = {
            "summary": "Successfully found 10 high-quality ICP contacts",
            "actionable_assets": {
                "contact_database": {
                    "data": {
                        "contacts": [
                            {"name": f"Test Contact {i}", "email": f"contact{i}@saascompany.eu", "title": "CTO", "company": f"SaaS Corp {i}"}
                            for i in range(1, 11)
                        ]
                    }
                }
            }
        }
        print("   📊 Simulated Result: Found 10 contacts")
    else:
        result = {
            "summary": "Task completed successfully",
            "contribution": task.get('contribution_expected', 1)
        }
    
    # Update task status to completed
    update_response = supabase.table("tasks").update({
        "status": "completed",
        "result": result,
        "updated_at": datetime.now().isoformat()
    }).eq("id", task['id']).execute()
    
    if update_response.data:
        print("   ✅ Task marked as completed")
        
        # Wait for trigger to update goal progress
        await asyncio.sleep(2)
        
        # Check goal progress
        goal_response = supabase.table("workspace_goals").select("*").eq(
            "id", task['goal_id']
        ).execute()
        
        if goal_response.data:
            goal = goal_response.data[0]
            print(f"\n📊 Goal Progress Updated:")
            print(f"   {goal['metric_type']}: {goal['current_value']}/{goal['target_value']} ({round(goal['current_value']/goal['target_value']*100, 1)}%)")
    
    return task

async def test_5_goal_validation_and_correction():
    """Test 5: Validate goals and trigger corrective actions if needed"""
    print("\n" + "="*60)
    print("🎯 TEST 5: GOAL VALIDATION & COURSE CORRECTION")
    print("="*60)
    
    # Get completed tasks for validation
    completed_tasks = supabase.table("tasks").select("*").eq(
        "workspace_id", TEST_WORKSPACE_ID
    ).eq("status", "completed").execute().data
    
    workspace_goal = "Raccogliere 50 contatti ICP (CMO/CTO di aziende SaaS europee) e creare 3 sequenze email per B2B outreach con ≥30% open rate"
    
    # Validate workspace goal achievement
    validation_results = await goal_validator.validate_workspace_goal_achievement(
        workspace_goal=workspace_goal,
        completed_tasks=completed_tasks,
        workspace_id=TEST_WORKSPACE_ID
    )
    
    print(f"\n📊 Validation Results: {len(validation_results)} requirements checked")
    
    for validation in validation_results:
        print(f"\n• Requirement: {validation.target_requirement}")
        print(f"  Actual: {validation.actual_achievement}")
        print(f"  Gap: {validation.gap_percentage:.1f}%")
        print(f"  Severity: {validation.severity.value}")
        print(f"  Valid: {'✅' if validation.is_valid else '❌'}")
        
        if validation.recommendations:
            print("  Recommendations:")
            for rec in validation.recommendations[:2]:
                print(f"    - {rec}")
    
    # Trigger corrective actions if needed
    corrective_tasks = await goal_validator.trigger_corrective_actions(
        validation_results=validation_results,
        workspace_id=TEST_WORKSPACE_ID
    )
    
    if corrective_tasks:
        print(f"\n🚨 Generated {len(corrective_tasks)} corrective tasks:")
        for task in corrective_tasks:
            print(f"  • {task['name']}")
            print(f"    Priority: HIGH (24hr deadline)")
            print(f"    Expected Contribution: {task.get('contribution_expected', 0)}")
    else:
        print("\n✅ No corrective actions needed")
    
    return validation_results

async def test_6_automated_monitoring():
    """Test 6: Test automated goal monitoring"""
    print("\n" + "="*60)
    print("🎯 TEST 6: AUTOMATED GOAL MONITORING")
    print("="*60)
    
    # Get monitoring status
    status = await automated_goal_monitor.get_monitoring_status()
    
    print(f"\n📊 Monitoring Status:")
    print(f"  Running: {status.get('is_running', False)}")
    print(f"  Interval: {status.get('monitor_interval_minutes', 20)} minutes")
    print(f"  Active Workspaces: {status.get('active_workspaces', 0)}")
    print(f"  Corrective Tasks Today: {status.get('corrective_tasks_today', 0)}")
    
    # Trigger immediate validation
    print(f"\n🚨 Triggering immediate validation for workspace...")
    validation_result = await automated_goal_monitor.trigger_immediate_validation(TEST_WORKSPACE_ID)
    
    print(f"\n📋 Immediate Validation Result:")
    print(f"  Success: {validation_result['success']}")
    print(f"  Corrective Tasks Created: {validation_result.get('corrective_tasks_created', 0)}")
    
    if validation_result.get('tasks'):
        print(f"  New Tasks:")
        for task in validation_result['tasks']:
            print(f"    • {task['name']}")
    
    return status

async def view_current_system_state():
    """View current state of goals and tasks"""
    print("\n" + "="*60)
    print("📊 CURRENT SYSTEM STATE")
    print("="*60)
    
    # Get workspace goals
    goals = supabase.table("workspace_goals").select("*").eq(
        "workspace_id", TEST_WORKSPACE_ID
    ).execute().data
    
    print(f"\n🎯 Workspace Goals:")
    for goal in goals:
        completion_pct = (goal['current_value'] / goal['target_value'] * 100) if goal['target_value'] > 0 else 0
        print(f"  • {goal['metric_type']}: {goal['current_value']}/{goal['target_value']} ({completion_pct:.1f}%)")
        print(f"    Status: {goal['status']}")
        print(f"    Priority: {goal['priority']}")
    
    # Get goal-driven tasks
    tasks = supabase.table("tasks").select("*").eq(
        "workspace_id", TEST_WORKSPACE_ID
    ).not_.is_("goal_id", "null").order("created_at", desc=True).limit(10).execute().data
    
    print(f"\n📋 Recent Goal-Driven Tasks:")
    for task in tasks[:5]:
        print(f"  • {task['name']}")
        print(f"    Status: {task['status']}")
        print(f"    Metric: {task.get('metric_type', 'N/A')}")
        print(f"    Contribution: {task.get('contribution_expected', 0)}")
        print(f"    Corrective: {'🚨 YES' if task.get('is_corrective') else 'No'}")
    
    # Get workspace insights
    insights = supabase.table("workspace_insights").select("*").eq(
        "workspace_id", TEST_WORKSPACE_ID
    ).order("created_at", desc=True).limit(5).execute().data
    
    print(f"\n🧠 Recent Workspace Insights:")
    for insight in insights:
        print(f"  • {insight['insight_type']}: {insight['content'][:80]}...")
        print(f"    Tags: {', '.join(insight.get('relevance_tags', []))}")

async def main():
    """Run all tests in sequence"""
    print("🚀 STARTING GOAL-DRIVEN SYSTEM TEST SUITE")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Setup
        await setup_test_workspace()
        
        # View initial state
        await view_current_system_state()
        
        # Run tests
        await test_1_goal_decomposition()
        await test_2_goal_driven_task_generation()
        await test_3_pm_review_and_approval()
        
        # Optional: simulate completion
        completed_task = await test_4_simulate_task_completion()
        
        # Validation and correction
        await test_5_goal_validation_and_correction()
        
        # Monitoring
        await test_6_automated_monitoring()
        
        # Final state
        await view_current_system_state()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())