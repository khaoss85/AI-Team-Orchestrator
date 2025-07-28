#!/usr/bin/env python3
"""Diagnose why deliverable pipeline is blocked"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import supabase
from deliverable_system.unified_deliverable_engine import UnifiedDeliverableEngine
from services.course_correction_engine import CourseCorrectionEngine
from models import WorkspaceStatus


async def check_workspace_state():
    """Check current workspace state and task completion data"""
    
    # Get active workspaces
    workspaces = supabase.table('workspaces').select('*').eq('status', 'active').execute()
    
    results = []
    for workspace in workspaces.data:
        workspace_id = workspace['id']
        
        # Get goals for this workspace
        goals = supabase.table('goals').select('*').eq('workspace_id', workspace_id).execute()
        
        # Get completed tasks
        completed_tasks = supabase.table('tasks').select('*').eq('workspace_id', workspace_id).eq('status', 'completed').execute()
        
        # Get all tasks for statistics
        all_tasks = supabase.table('tasks').select('*').eq('workspace_id', workspace_id).execute()
        
        # Get existing deliverables
        deliverables = supabase.table('deliverables').select('*').eq('workspace_id', workspace_id).execute()
        
        # Get quality scores
        quality_scores = []
        for task in completed_tasks.data:
            if task.get('quality_score'):
                quality_scores.append(task['quality_score'])
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Calculate time since creation
        created_at = datetime.fromisoformat(workspace['created_at'].replace('Z', '+00:00'))
        hours_active = (datetime.now(created_at.tzinfo) - created_at).total_seconds() / 3600
        
        results.append({
            'workspace_id': workspace_id,
            'workspace_name': workspace['name'],
            'status': workspace['status'],
            'created_at': workspace['created_at'],
            'hours_active': round(hours_active, 2),
            'goals': len(goals.data),
            'goal_details': [
                {
                    'id': g['id'],
                    'goal_text': g['goal_text'],
                    'current_value': g.get('current_value', 0),
                    'target_value': g.get('target_value', 100),
                    'progress': (g.get('current_value', 0) / g.get('target_value', 100) * 100) if g.get('target_value', 100) > 0 else 0
                }
                for g in goals.data
            ],
            'completed_tasks': len(completed_tasks.data),
            'total_tasks': len(all_tasks.data),
            'avg_quality_score': avg_quality,
            'existing_deliverables': len(deliverables.data),
            'deliverable_details': [
                {
                    'id': d['id'],
                    'type': d.get('type'),
                    'created_at': d['created_at']
                }
                for d in deliverables.data
            ]
        })
    
    return results


async def check_trigger_conditions(workspace_id: str):
    """Check each trigger condition for deliverable creation"""
    
    print(f"\n🔍 Checking trigger conditions for workspace: {workspace_id}")
    
    # Initialize engines
    deliverable_engine = UnifiedDeliverableEngine()
    correction_engine = CourseCorrectionEngine()
    
    # Get environment variables
    env_vars = {
        'MIN_COMPLETED_TASKS_FOR_DELIVERABLE': int(os.getenv('MIN_COMPLETED_TASKS_FOR_DELIVERABLE', '2')),
        'DELIVERABLE_READINESS_THRESHOLD': int(os.getenv('DELIVERABLE_READINESS_THRESHOLD', '100')),
        'BUSINESS_VALUE_THRESHOLD': float(os.getenv('BUSINESS_VALUE_THRESHOLD', '70.0')),
        'DELIVERABLE_CHECK_COOLDOWN_SECONDS': int(os.getenv('DELIVERABLE_CHECK_COOLDOWN_SECONDS', '30')),
        'MAX_DELIVERABLES_PER_WORKSPACE': int(os.getenv('MAX_DELIVERABLES_PER_WORKSPACE', '3')),
        'ENABLE_IMMEDIATE_DELIVERABLE_CREATION': os.getenv('ENABLE_IMMEDIATE_DELIVERABLE_CREATION', 'false').lower() == 'true',
        'IMMEDIATE_DELIVERABLE_THRESHOLD': int(os.getenv('IMMEDIATE_DELIVERABLE_THRESHOLD', '70'))
    }
    
    print("\n📊 Environment Configuration:")
    for key, value in env_vars.items():
        print(f"  {key}: {value}")
    
    # Check workspace status
    workspace = supabase.table('workspaces').select('*').eq('id', workspace_id).single().execute()
    print(f"\n📁 Workspace Status: {workspace.data['status']}")
    
    # Check completed tasks
    completed_tasks = supabase.table('tasks').select('*').eq('workspace_id', workspace_id).eq('status', 'completed').execute()
    completed_count = len(completed_tasks.data)
    print(f"\n✅ Completed Tasks: {completed_count} (required: {env_vars['MIN_COMPLETED_TASKS_FOR_DELIVERABLE']})")
    
    # Check existing deliverables
    existing_deliverables = supabase.table('deliverables').select('*').eq('workspace_id', workspace_id).execute()
    deliverable_count = len(existing_deliverables.data)
    print(f"\n📦 Existing Deliverables: {deliverable_count} (max: {env_vars['MAX_DELIVERABLES_PER_WORKSPACE']})")
    
    # Check cooldown
    if existing_deliverables.data:
        latest_deliverable = max(existing_deliverables.data, key=lambda d: d['created_at'])
        created_at = datetime.fromisoformat(latest_deliverable['created_at'].replace('Z', '+00:00'))
        seconds_since_last = (datetime.now(created_at.tzinfo) - created_at).total_seconds()
        cooldown_met = seconds_since_last >= env_vars['DELIVERABLE_CHECK_COOLDOWN_SECONDS']
        print(f"\n⏱️  Cooldown Status: {seconds_since_last:.0f}s since last deliverable (required: {env_vars['DELIVERABLE_CHECK_COOLDOWN_SECONDS']}s)")
        print(f"   Cooldown Met: {cooldown_met}")
    else:
        print("\n⏱️  Cooldown Status: No deliverables yet, cooldown not applicable")
        cooldown_met = True
    
    # Check goal progress
    goals = supabase.table('goals').select('*').eq('workspace_id', workspace_id).execute()
    
    if goals.data:
        print("\n🎯 Goal Progress:")
        goal_ready = False
        for goal in goals.data:
            progress = (goal.get('current_value', 0) / goal.get('target_value', 100) * 100) if goal.get('target_value', 100) > 0 else 0
            print(f"   - {goal['goal_text'][:50]}...")
            print(f"     Progress: {progress:.1f}% (current: {goal.get('current_value', 0)}, target: {goal.get('target_value', 100)})")
            
            if env_vars['ENABLE_IMMEDIATE_DELIVERABLE_CREATION'] and progress >= env_vars['IMMEDIATE_DELIVERABLE_THRESHOLD']:
                print(f"     ⚡ Immediate creation eligible (>= {env_vars['IMMEDIATE_DELIVERABLE_THRESHOLD']}%)")
                goal_ready = True
            elif progress >= env_vars['DELIVERABLE_READINESS_THRESHOLD']:
                print(f"     ✅ Goal ready for deliverable (>= {env_vars['DELIVERABLE_READINESS_THRESHOLD']}%)")
                goal_ready = True
            else:
                print(f"     ❌ Not ready (< {env_vars['DELIVERABLE_READINESS_THRESHOLD']}%)")
    else:
        print("\n🎯 Goal Progress: No goals found")
        goal_ready = False
    
    # Check business value
    if completed_tasks.data:
        quality_scores = [t.get('quality_score', 0) for t in completed_tasks.data if t.get('quality_score')]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        business_value_met = avg_quality >= (env_vars['BUSINESS_VALUE_THRESHOLD'] / 100)
        print(f"\n💎 Business Value: {avg_quality * 100:.1f}% (required: {env_vars['BUSINESS_VALUE_THRESHOLD']}%)")
        print(f"   Business Value Met: {business_value_met}")
    else:
        print("\n💎 Business Value: No quality scores available")
        business_value_met = False
    
    # Summary
    print("\n📋 TRIGGER CONDITION SUMMARY:")
    conditions = {
        'Workspace Active': workspace.data['status'] == 'active',
        'Sufficient Completed Tasks': completed_count >= env_vars['MIN_COMPLETED_TASKS_FOR_DELIVERABLE'],
        'Under Deliverable Limit': deliverable_count < env_vars['MAX_DELIVERABLES_PER_WORKSPACE'],
        'Cooldown Met': cooldown_met,
        'Goal Ready': goal_ready,
        'Business Value Met': business_value_met
    }
    
    all_met = all(conditions.values())
    for condition, met in conditions.items():
        status = "✅" if met else "❌"
        print(f"   {status} {condition}")
    
    print(f"\n🚦 Overall Status: {'✅ READY for deliverable creation' if all_met else '❌ NOT READY - conditions not met'}")
    
    # Try to trigger deliverable creation if ready
    if all_met:
        print("\n🚀 Attempting to trigger deliverable creation...")
        try:
            should_trigger = await deliverable_engine.should_trigger_deliverable_aggregation(workspace_id)
            print(f"   Engine says should_trigger: {should_trigger}")
            
            if should_trigger:
                deliverable = await deliverable_engine.aggregate_deliverables(workspace_id)
                if deliverable:
                    print(f"   ✅ Deliverable created: {deliverable['id']}")
                else:
                    print("   ❌ Deliverable creation failed")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    return conditions


async def main():
    """Main diagnostic function"""
    print("🔍 DELIVERABLE PIPELINE DIAGNOSTIC")
    print("=" * 50)
    
    # Check workspace states
    workspaces = await check_workspace_state()
    
    if not workspaces:
        print("\n❌ No active workspaces found")
        return
    
    print(f"\n📊 Found {len(workspaces)} active workspace(s)")
    
    for workspace in workspaces:
        print(f"\n{'=' * 50}")
        print(f"Workspace: {workspace['workspace_name']}")
        print(f"ID: {workspace['workspace_id']}")
        print(f"Status: {workspace['status']}")
        print(f"Active for: {workspace['hours_active']} hours")
        print(f"Goals: {workspace['goals']}")
        print(f"Completed Tasks: {workspace['completed_tasks']} / {workspace['total_tasks']}")
        print(f"Avg Quality Score: {workspace['avg_quality_score'] * 100:.1f}%")
        print(f"Existing Deliverables: {workspace['existing_deliverables']}")
        
        if workspace['goal_details']:
            print("\nGoal Progress:")
            for goal in workspace['goal_details']:
                print(f"  - {goal['goal_text'][:60]}...")
                print(f"    Progress: {goal['progress']:.1f}% ({goal['current_value']}/{goal['target_value']})")
        
        # Check trigger conditions for this workspace
        await check_trigger_conditions(workspace['workspace_id'])


if __name__ == "__main__":
    asyncio.run(main())