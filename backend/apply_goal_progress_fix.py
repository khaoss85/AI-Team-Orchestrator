#!/usr/bin/env python3
"""
AUTOMATIC FIX: Apply Goal Progress Calculation Fix
No user input required - applies fix directly
"""

import os
import sys
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime

# Load environment
load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ ERROR: Missing SUPABASE_URL or SUPABASE_KEY in environment")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def apply_fix(workspace_id: str):
    """Apply the goal progress fix automatically"""
    print(f"\n🔧 APPLYING GOAL PROGRESS FIX FOR WORKSPACE: {workspace_id}")
    print("="*80)
    
    fixed_goals = []
    completed_goals = []
    
    try:
        # Get all goals
        goals = supabase.table('workspace_goals').select('*').eq('workspace_id', workspace_id).execute()
        
        print(f"\n📊 Processing {len(goals.data)} goals...")
        
        for goal in goals.data:
            goal_id = goal['id']
            description = goal['description'][:50] + '...' if len(goal['description']) > 50 else goal['description']
            
            # Count completed deliverables
            deliverables = supabase.table('deliverables').select('status').eq('goal_id', goal_id).execute()
            completed_count = len([d for d in deliverables.data if d['status'] == 'completed'])
            total_count = len(deliverables.data)
            
            # Calculate new current_value
            old_value = goal.get('current_value', 0)
            target_value = goal.get('target_value', 1)
            
            # For deliverable-based goals, current_value = completed deliverables
            new_value = min(completed_count, target_value)  # Cap at target
            
            # Check if needs update
            if old_value != new_value:
                print(f"\n📝 Fixing: {description}")
                print(f"   Old Progress: {old_value}/{target_value} ({old_value/target_value*100:.1f}%)")
                print(f"   New Progress: {new_value}/{target_value} ({new_value/target_value*100:.1f}%)")
                print(f"   Based on: {completed_count}/{total_count} deliverables")
                
                # Update the goal
                update_data = {
                    'current_value': new_value,
                    'updated_at': datetime.now().isoformat()
                }
                
                # If goal is complete, update status
                if new_value >= target_value and goal.get('status') != 'completed':
                    update_data['status'] = 'completed'
                    update_data['completed_at'] = datetime.now().isoformat()
                    print(f"   🎯 Marking as COMPLETED!")
                    completed_goals.append(description)
                
                result = supabase.table('workspace_goals').update(update_data).eq('id', goal_id).execute()
                
                if result.data:
                    print(f"   ✅ Fixed successfully")
                    fixed_goals.append(description)
                else:
                    print(f"   ❌ Fix failed")
        
        # Final report
        print("\n" + "="*80)
        print("📊 FIX COMPLETE!")
        print(f"  - Goals Fixed: {len(fixed_goals)}")
        print(f"  - Goals Marked Complete: {len(completed_goals)}")
        
        if fixed_goals:
            print("\n✅ Fixed Goals:")
            for goal in fixed_goals:
                print(f"  - {goal}")
        
        if completed_goals:
            print("\n🎯 Completed Goals:")
            for goal in completed_goals:
                print(f"  - {goal}")
        
        # Verify final state
        print("\n📋 VERIFICATION - Final Goal States:")
        print("-"*80)
        
        final_goals = supabase.table('workspace_goals').select('*').eq('workspace_id', workspace_id).execute()
        
        for goal in final_goals.data:
            desc = goal['description'][:50] + '...' if len(goal['description']) > 50 else goal['description']
            current = goal.get('current_value', 0)
            target = goal.get('target_value', 1)
            progress = (current / target * 100) if target > 0 else 0
            status = goal.get('status', 'unknown')
            
            # Get deliverable count
            deliverables = supabase.table('deliverables').select('status').eq('goal_id', goal['id']).execute()
            completed = len([d for d in deliverables.data if d['status'] == 'completed'])
            total = len(deliverables.data)
            
            status_icon = "🎯" if status == 'completed' else "🔄" if status == 'active' else "❓"
            print(f"{status_icon} {desc:<50} | {progress:6.1f}% | {current}/{target} | {completed}/{total} deliverables")
        
        print("\n✅ Goal progress calculation system is now FIXED!")
        
    except Exception as e:
        print(f"\n❌ Error during fix: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    workspace_id = sys.argv[1] if len(sys.argv) > 1 else 'e29a33af-b473-4d9c-b983-f5c1aa70a830'
    apply_fix(workspace_id)