#!/usr/bin/env python3
"""
Fix goal progress calculation for goals showing 0% despite having completed deliverables.
This script recalculates progress based on actual deliverable completion.
"""

import os
import sys
from typing import Dict, List, Any
from supabase import create_client, Client
from dotenv import load_dotenv
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
load_dotenv('.env')

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

def recalculate_goal_progress(workspace_id: str, dry_run: bool = False):
    """
    Recalculate goal progress based on actual deliverable completion.
    
    Args:
        workspace_id: The workspace to fix
        dry_run: If True, only show what would be changed without updating
    """
    
    print(f"🔧 FIXING GOAL PROGRESS CALCULATION")
    print(f"   Workspace: {workspace_id}")
    print(f"   Mode: {'DRY RUN' if dry_run else 'LIVE UPDATE'}")
    print("=" * 80)
    
    # Get all goals in workspace
    goals_response = supabase.table('workspace_goals').select('*').eq('workspace_id', workspace_id).execute()
    goals = goals_response.data if goals_response else []
    
    # Get all deliverables in workspace
    deliverables_response = supabase.table('deliverables').select('*').eq('workspace_id', workspace_id).execute()
    deliverables = deliverables_response.data if deliverables_response else []
    
    # Group deliverables by goal
    deliverables_by_goal: Dict[str, List[Any]] = {}
    for deliv in deliverables:
        goal_id = deliv.get('goal_id')
        if goal_id:
            if goal_id not in deliverables_by_goal:
                deliverables_by_goal[goal_id] = []
            deliverables_by_goal[goal_id].append(deliv)
    
    fixes_applied = 0
    
    for goal in goals:
        goal_id = goal['id']
        goal_desc = goal['description'][:50] + "..."
        metric_type = goal.get('metric_type', '')
        
        # Get deliverables for this goal
        goal_deliverables = deliverables_by_goal.get(goal_id, [])
        
        if goal_deliverables:
            # Calculate actual progress
            total = len(goal_deliverables)
            completed = sum(1 for d in goal_deliverables if d.get('status') == 'completed')
            calculated_progress = round((completed / total * 100) if total > 0 else 0, 1)
            
            # Check current values
            current_progress = goal.get('progress', 0)
            current_value = goal.get('current_value', 0)
            target_value = goal.get('target_value', 1)
            
            # Determine what needs updating
            needs_update = False
            updates = {}
            
            # Update progress if wrong
            if abs(calculated_progress - current_progress) > 0.1:
                updates['progress'] = calculated_progress
                needs_update = True
            
            # For deliverable-based goals, update current_value to match completed count
            if 'deliverable' in metric_type.lower() or metric_type in ['csv_imports', 'dashboards', 'sales_scripts', 'email_sequences']:
                if current_value != completed:
                    updates['current_value'] = float(completed)
                    needs_update = True
                
                # Also ensure target_value is at least the total deliverables
                if target_value < total:
                    updates['target_value'] = float(total)
                    needs_update = True
            
            # Update status if completed
            if calculated_progress >= 100 and goal.get('status') != 'completed':
                updates['status'] = 'completed'
                needs_update = True
            
            if needs_update:
                print(f"\n📊 Goal: {goal_desc}")
                print(f"   ID: {goal_id}")
                print(f"   Type: {metric_type}")
                print(f"   Deliverables: {completed}/{total} completed")
                print(f"   Current Progress: {current_progress}% → {calculated_progress}%")
                
                if 'current_value' in updates:
                    print(f"   Current Value: {current_value} → {updates['current_value']}")
                if 'target_value' in updates:
                    print(f"   Target Value: {target_value} → {updates['target_value']}")
                if 'status' in updates:
                    print(f"   Status: {goal.get('status')} → {updates['status']}")
                
                if not dry_run:
                    # Apply the update
                    update_response = supabase.table('workspace_goals').update(updates).eq('id', goal_id).execute()
                    
                    if update_response.data:
                        print("   ✅ FIXED")
                        fixes_applied += 1
                    else:
                        print("   ❌ Update failed")
                else:
                    print("   🔍 Would fix (dry run)")
                    fixes_applied += 1
        
        # Check for goals that should have deliverables but don't
        elif 'deliverable' in metric_type.lower() and goal.get('progress', 0) > 0:
            print(f"\n⚠️ Goal with no deliverables but shows progress:")
            print(f"   Goal: {goal_desc}")
            print(f"   ID: {goal_id}")
            print(f"   Type: {metric_type}")
            print(f"   Progress: {goal.get('progress')}%")
            
            if not dry_run:
                # Reset progress to 0 if no deliverables
                updates = {'progress': 0, 'current_value': 0.0}
                update_response = supabase.table('workspace_goals').update(updates).eq('id', goal_id).execute()
                if update_response.data:
                    print("   ✅ Reset to 0%")
                    fixes_applied += 1
    
    print("\n" + "=" * 80)
    print(f"🏁 PROGRESS RECALCULATION COMPLETE")
    print(f"   Fixed: {fixes_applied} goals")
    
    if dry_run:
        print(f"\n💡 To apply these fixes, run with dry_run=False")
    
    return fixes_applied

if __name__ == "__main__":
    workspace_id = "3adfdc92-b316-442f-b9ca-a8d1df49e200"
    
    # First do a dry run
    print("🔍 DRY RUN - Checking what would be fixed...")
    print()
    recalculate_goal_progress(workspace_id, dry_run=True)
    
    print("\n" + "=" * 80)
    print("\n🚀 APPLYING FIXES...")
    print()
    recalculate_goal_progress(workspace_id, dry_run=False)