#!/usr/bin/env python3
"""Diagnose why deliverable creation is blocked"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import supabase
from deliverable_system.unified_deliverable_engine import UnifiedDeliverableEngine


async def main():
    """Main diagnostic function"""
    workspace_id = "12e63f24-1cda-44aa-b5b1-caef243bb18c"
    
    print("🔍 DELIVERABLE PIPELINE BLOCKAGE DIAGNOSIS")
    print("=" * 60)
    
    # 1. Get workspace details
    workspace = supabase.table('workspaces').select('*').eq('id', workspace_id).single().execute()
    workspace_data = workspace.data
    
    print(f"\n📁 WORKSPACE:")
    print(f"  Name: {workspace_data['name']}")
    print(f"  Status: {workspace_data['status']}")
    print(f"  Created: {workspace_data['created_at']}")
    
    # 2. Get workspace goals
    workspace_goals = supabase.table('workspace_goals').select('*').eq('workspace_id', workspace_id).execute()
    print(f"\n🎯 WORKSPACE GOALS: {len(workspace_goals.data)} found")
    
    completed_goals = 0
    for goal in workspace_goals.data:
        progress = (goal.get('current_value', 0) / goal.get('target_value', 100) * 100) if goal.get('target_value', 100) > 0 else 0
        status_icon = "✅" if goal.get('status') == 'completed' else "🔄"
        print(f"  {status_icon} {goal.get('description', 'No description')[:60]}...")
        print(f"     Progress: {progress:.1f}% (current: {goal.get('current_value', 0)}, target: {goal.get('target_value', 1)})")
        print(f"     Status: {goal.get('status')}")
        
        if goal.get('status') == 'completed':
            completed_goals += 1
    
    # 3. Get tasks
    all_tasks = supabase.table('tasks').select('*').eq('workspace_id', workspace_id).execute()
    task_counts = {}
    quality_scores = []
    
    for task in all_tasks.data:
        status = task['status']
        task_counts[status] = task_counts.get(status, 0) + 1
        
        if status == 'completed' and task.get('quality_score'):
            quality_scores.append(task['quality_score'])
    
    print(f"\n✅ TASKS:")
    for status, count in task_counts.items():
        print(f"  {status}: {count}")
    
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
    print(f"  Average Quality Score: {avg_quality * 100:.1f}%")
    
    # 4. Get existing deliverables
    deliverables = supabase.table('deliverables').select('*').eq('workspace_id', workspace_id).execute()
    print(f"\n📦 EXISTING DELIVERABLES: {len(deliverables.data)}")
    for d in deliverables.data:
        print(f"  - {d.get('type', 'Unknown')} (created: {d['created_at']})")
    
    # 5. Check environment configuration
    print(f"\n🔧 ENVIRONMENT CONFIGURATION:")
    env_vars = {
        'MIN_COMPLETED_TASKS_FOR_DELIVERABLE': os.getenv('MIN_COMPLETED_TASKS_FOR_DELIVERABLE', '2'),
        'DELIVERABLE_READINESS_THRESHOLD': os.getenv('DELIVERABLE_READINESS_THRESHOLD', '100'),
        'BUSINESS_VALUE_THRESHOLD': os.getenv('BUSINESS_VALUE_THRESHOLD', '70.0'),
        'MAX_DELIVERABLES_PER_WORKSPACE': os.getenv('MAX_DELIVERABLES_PER_WORKSPACE', '3'),
        'ENABLE_IMMEDIATE_DELIVERABLE_CREATION': os.getenv('ENABLE_IMMEDIATE_DELIVERABLE_CREATION', 'false'),
        'IMMEDIATE_DELIVERABLE_THRESHOLD': os.getenv('IMMEDIATE_DELIVERABLE_THRESHOLD', '70'),
        'DELIVERABLE_CHECK_COOLDOWN_SECONDS': os.getenv('DELIVERABLE_CHECK_COOLDOWN_SECONDS', '30')
    }
    
    for key, value in env_vars.items():
        print(f"  {key}: {value}")
    
    # 6. Analyze trigger conditions
    print(f"\n📋 TRIGGER CONDITION ANALYSIS:")
    
    # Condition 1: Workspace status
    workspace_active = workspace_data['status'] == 'active'
    print(f"  {'✅' if workspace_active else '❌'} Workspace Active: {workspace_data['status']} {'(required: active)' if not workspace_active else ''}")
    
    # Condition 2: Completed tasks
    completed_tasks = task_counts.get('completed', 0)
    min_tasks = int(env_vars['MIN_COMPLETED_TASKS_FOR_DELIVERABLE'])
    tasks_sufficient = completed_tasks >= min_tasks
    print(f"  {'✅' if tasks_sufficient else '❌'} Sufficient Tasks: {completed_tasks} >= {min_tasks}")
    
    # Condition 3: Deliverable limit
    max_deliverables = int(env_vars['MAX_DELIVERABLES_PER_WORKSPACE'])
    under_limit = len(deliverables.data) < max_deliverables
    print(f"  {'✅' if under_limit else '❌'} Under Limit: {len(deliverables.data)} < {max_deliverables}")
    
    # Condition 4: Goal progress (using workspace_goals)
    goal_threshold = int(env_vars['DELIVERABLE_READINESS_THRESHOLD'])
    goal_ready = False
    
    if env_vars['ENABLE_IMMEDIATE_DELIVERABLE_CREATION'].lower() == 'true':
        immediate_threshold = int(env_vars['IMMEDIATE_DELIVERABLE_THRESHOLD'])
        for goal in workspace_goals.data:
            progress = (goal.get('current_value', 0) / goal.get('target_value', 100) * 100) if goal.get('target_value', 100) > 0 else 0
            if progress >= immediate_threshold:
                goal_ready = True
                break
        print(f"  {'✅' if goal_ready else '❌'} Goal Progress (Immediate): Any goal >= {immediate_threshold}%")
    else:
        # Check if completed goals meet threshold
        goal_ready = completed_goals > 0
        print(f"  {'✅' if goal_ready else '❌'} Completed Goals: {completed_goals} > 0")
    
    # Condition 5: Business value
    business_threshold = float(env_vars['BUSINESS_VALUE_THRESHOLD']) / 100
    business_value_met = avg_quality >= business_threshold
    print(f"  {'✅' if business_value_met else '❌'} Business Value: {avg_quality * 100:.1f}% >= {float(env_vars['BUSINESS_VALUE_THRESHOLD'])}%")
    
    # Condition 6: Cooldown
    cooldown_met = True
    if deliverables.data:
        latest = max(deliverables.data, key=lambda d: d['created_at'])
        created_at = datetime.fromisoformat(latest['created_at'].replace('Z', '+00:00'))
        seconds_since = (datetime.now(created_at.tzinfo) - created_at).total_seconds()
        cooldown_seconds = int(env_vars['DELIVERABLE_CHECK_COOLDOWN_SECONDS'])
        cooldown_met = seconds_since >= cooldown_seconds
        print(f"  {'✅' if cooldown_met else '❌'} Cooldown: {seconds_since:.0f}s >= {cooldown_seconds}s")
    else:
        print(f"  ✅ Cooldown: N/A (no deliverables yet)")
    
    # Summary
    all_conditions = [
        workspace_active,
        tasks_sufficient,
        under_limit,
        goal_ready,
        business_value_met,
        cooldown_met
    ]
    
    all_met = all(all_conditions)
    
    print(f"\n🚦 OVERALL STATUS: {'✅ READY' if all_met else '❌ BLOCKED'}")
    
    # Root cause analysis
    print(f"\n🔍 ROOT CAUSE ANALYSIS:")
    
    if not workspace_active:
        print(f"\n❌ PRIMARY BLOCKER: Workspace status is '{workspace_data['status']}', not 'active'")
        print(f"   - The unified_deliverable_engine only processes 'active' workspaces")
        print(f"   - Current status suggests tasks are still being processed")
        
        # Check why it's not transitioning
        pending_or_in_progress = task_counts.get('pending', 0) + task_counts.get('in_progress', 0)
        if pending_or_in_progress == 0:
            print(f"\n   ⚠️  All tasks appear to be completed/cancelled")
            print(f"   ⚠️  Workspace should transition to 'active' automatically")
            print(f"   ⚠️  This might be a bug in the task processor")
        else:
            print(f"\n   ℹ️  {pending_or_in_progress} tasks still pending/in progress")
            print(f"   ℹ️  Workspace will transition when all tasks complete")
    
    elif not goal_ready:
        print(f"\n❌ PRIMARY BLOCKER: No goals meet the progress threshold")
        print(f"   - Goals need {goal_threshold}% progress for deliverables")
        print(f"   - Or {env_vars['IMMEDIATE_DELIVERABLE_THRESHOLD']}% for immediate creation")
    
    elif not business_value_met:
        print(f"\n❌ PRIMARY BLOCKER: Average quality score too low")
        print(f"   - Current: {avg_quality * 100:.1f}%")
        print(f"   - Required: {env_vars['BUSINESS_VALUE_THRESHOLD']}%")
    
    else:
        print(f"\n✅ All conditions appear to be met!")
        print(f"   - Deliverables should be created on next check cycle")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if not workspace_active and pending_or_in_progress == 0:
        print(f"\n1. FIX WORKSPACE STATUS:")
        print(f"   The workspace has all tasks completed but hasn't transitioned to 'active'")
        print(f"   Run: python3 diagnose_deliverable_blockage.py --fix-status")
    
    elif not workspace_active:
        print(f"\n1. WAIT FOR TASK COMPLETION:")
        print(f"   {pending_or_in_progress} tasks are still being processed")
        print(f"   The workspace will automatically transition when done")
    
    if all_met:
        print(f"\n2. TRIGGER DELIVERABLE CHECK:")
        print(f"   All conditions are met, trigger a manual check")
        print(f"   Run: python3 diagnose_deliverable_blockage.py --trigger-check")
    
    # Handle command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--fix-status':
            print(f"\n🔧 FIXING WORKSPACE STATUS...")
            result = supabase.table('workspaces').update({
                'status': 'active',
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', workspace_id).execute()
            
            if result.data:
                print(f"✅ Workspace status updated to 'active'")
                print(f"   Deliverables should be created within the next check cycle")
            else:
                print(f"❌ Failed to update workspace status")
        
        elif sys.argv[1] == '--trigger-check':
            print(f"\n🚀 TRIGGERING DELIVERABLE CHECK...")
            engine = UnifiedDeliverableEngine()
            
            try:
                should_trigger = await engine.should_trigger_deliverable_aggregation(workspace_id)
                print(f"   Should trigger: {should_trigger}")
                
                if should_trigger:
                    deliverable = await engine.aggregate_deliverables(workspace_id)
                    if deliverable:
                        print(f"   ✅ Deliverable created: {deliverable.get('id')}")
                    else:
                        print(f"   ❌ Failed to create deliverable")
                else:
                    print(f"   ❌ Trigger conditions not met according to engine")
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())