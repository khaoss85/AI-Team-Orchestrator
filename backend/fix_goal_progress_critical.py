#!/usr/bin/env python3
"""
CRITICAL FIX: Goal Progress Calculation System
Date: 2025-09-05
Issue: Goals showing 0% progress despite having deliverables
Root Cause: Progress calculated from current_value/target_value, but current_value never updated when deliverables created

DIRECTOR ANALYSIS SUMMARY:
1. system-architect: Progress calculation disconnected from deliverable lifecycle
2. db-steward: current_value field not updated by deliverable operations
3. principles-guardian: Anti-pattern - two separate progress tracking systems
4. placeholder-police: No hardcoded values found, but missing integration detected
"""

import os
import sys
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, List, Tuple

# Load environment
load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ ERROR: Missing SUPABASE_URL or SUPABASE_KEY in environment")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def diagnose_workspace(workspace_id: str) -> Dict:
    """Comprehensive diagnosis of goal-deliverable-progress relationships"""
    print(f"\n🔍 DIAGNOSING WORKSPACE: {workspace_id}")
    print("="*80)
    
    diagnosis = {
        'workspace_id': workspace_id,
        'issues': [],
        'goals': [],
        'deliverables_summary': {},
        'recommendations': []
    }
    
    try:
        # 1. Get all goals
        goals = supabase.table('workspace_goals').select('*').eq('workspace_id', workspace_id).execute()
        
        if not goals.data:
            diagnosis['issues'].append("NO_GOALS: Workspace has no goals")
            return diagnosis
        
        print(f"\n📊 Found {len(goals.data)} goals")
        
        # 2. Analyze each goal
        for goal in goals.data:
            goal_id = goal['id']
            description = goal['description'][:50] + '...' if len(goal['description']) > 50 else goal['description']
            
            # Get deliverables for this goal
            deliverables = supabase.table('deliverables').select('*').eq('goal_id', goal_id).execute()
            
            # Count by status
            status_counts = {'completed': 0, 'in_progress': 0, 'draft': 0, 'failed': 0, 'pending': 0, 'unknown': 0}
            for d in deliverables.data:
                status = d.get('status', 'unknown')
                if status in status_counts:
                    status_counts[status] += 1
                else:
                    status_counts['unknown'] += 1
            
            total_deliverables = len(deliverables.data)
            
            # Calculate what progress SHOULD be
            if goal.get('metric_type', '').startswith('deliverable'):
                # For deliverable-based goals, progress = completed deliverables
                calculated_progress = status_counts['completed']
            else:
                # For other goals, could be based on different metrics
                calculated_progress = status_counts['completed']
            
            # Get current database values
            current_value = goal.get('current_value', 0)
            target_value = goal.get('target_value', 1)
            db_progress_pct = (current_value / target_value * 100) if target_value > 0 else 0
            
            # Calculate what progress SHOULD be as percentage
            should_be_progress_pct = (calculated_progress / target_value * 100) if target_value > 0 else 0
            
            # Identify discrepancy
            discrepancy = abs(db_progress_pct - should_be_progress_pct)
            
            goal_analysis = {
                'id': goal_id,
                'description': description,
                'metric_type': goal.get('metric_type', 'unknown'),
                'status': goal.get('status', 'unknown'),
                'current_value': current_value,
                'target_value': target_value,
                'db_progress_pct': db_progress_pct,
                'total_deliverables': total_deliverables,
                'deliverable_status_counts': status_counts,
                'calculated_progress': calculated_progress,
                'should_be_progress_pct': should_be_progress_pct,
                'discrepancy': discrepancy,
                'needs_fix': discrepancy > 1  # More than 1% difference
            }
            
            diagnosis['goals'].append(goal_analysis)
            
            # Print analysis
            status_str = f"✅{status_counts['completed']} 🔄{status_counts['in_progress']} 📝{status_counts['draft']}"
            
            if goal_analysis['needs_fix']:
                print(f"\n❌ ISSUE FOUND: {description}")
                print(f"   DB Progress: {db_progress_pct:.1f}% ({current_value}/{target_value})")
                print(f"   Should Be: {should_be_progress_pct:.1f}% based on {calculated_progress} completed deliverables")
                print(f"   Deliverables: {total_deliverables} total ({status_str})")
                print(f"   Discrepancy: {discrepancy:.1f}%")
                
                diagnosis['issues'].append(f"Goal '{description}' shows {db_progress_pct:.1f}% but should be {should_be_progress_pct:.1f}%")
            else:
                print(f"\n✅ OK: {description}")
                print(f"   Progress: {db_progress_pct:.1f}% ({current_value}/{target_value})")
                print(f"   Deliverables: {total_deliverables} ({status_str})")
        
        # 3. Check for orphaned deliverables
        all_deliverables = supabase.table('deliverables').select('*').eq('workspace_id', workspace_id).execute()
        orphaned = [d for d in all_deliverables.data if not d.get('goal_id')]
        
        if orphaned:
            diagnosis['issues'].append(f"ORPHANED_DELIVERABLES: {len(orphaned)} deliverables without goal_id")
            print(f"\n⚠️ Found {len(orphaned)} orphaned deliverables")
        
        diagnosis['deliverables_summary'] = {
            'total': len(all_deliverables.data),
            'orphaned': len(orphaned),
            'mapped': len(all_deliverables.data) - len(orphaned)
        }
        
        # 4. Generate recommendations
        if any(g['needs_fix'] for g in diagnosis['goals']):
            diagnosis['recommendations'].append("RUN_FIX: Execute fix_progress() to recalculate goal progress")
            diagnosis['recommendations'].append("IMPLEMENT_TRIGGER: Add database trigger to update goal progress on deliverable changes")
            diagnosis['recommendations'].append("REFACTOR_SYSTEM: Consider using deliverable-based progress calculation in API")
        
        return diagnosis
        
    except Exception as e:
        diagnosis['issues'].append(f"DIAGNOSTIC_ERROR: {str(e)}")
        return diagnosis


def fix_progress(workspace_id: str, dry_run: bool = False) -> Dict:
    """Fix goal progress by recalculating from deliverables"""
    print(f"\n🔧 {'DRY RUN - ' if dry_run else ''}FIXING GOAL PROGRESS")
    print("="*80)
    
    fix_report = {
        'workspace_id': workspace_id,
        'goals_fixed': 0,
        'goals_completed': 0,
        'changes': []
    }
    
    try:
        # Get all goals for workspace
        goals = supabase.table('workspace_goals').select('*').eq('workspace_id', workspace_id).execute()
        
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
                print(f"\n📝 Updating: {description}")
                print(f"   Old Progress: {old_value}/{target_value} ({old_value/target_value*100:.1f}%)")
                print(f"   New Progress: {new_value}/{target_value} ({new_value/target_value*100:.1f}%)")
                print(f"   Based on: {completed_count}/{total_count} completed deliverables")
                
                if not dry_run:
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
                        fix_report['goals_completed'] += 1
                    
                    result = supabase.table('workspace_goals').update(update_data).eq('id', goal_id).execute()
                    
                    if result.data:
                        print(f"   ✅ Updated successfully")
                    else:
                        print(f"   ❌ Update failed")
                
                fix_report['goals_fixed'] += 1
                fix_report['changes'].append({
                    'goal': description,
                    'old_value': old_value,
                    'new_value': new_value,
                    'target_value': target_value,
                    'deliverables': f"{completed_count}/{total_count}"
                })
        
        return fix_report
        
    except Exception as e:
        fix_report['error'] = str(e)
        return fix_report


def implement_automatic_update(workspace_id: str) -> None:
    """
    Implement a function to be called whenever deliverables change status.
    This should be integrated into database.py
    """
    print("\n🚀 RECOMMENDED IMPLEMENTATION")
    print("="*80)
    print("""
Add this to database.py after deliverable creation/update:

async def update_goal_progress_from_deliverable(goal_id: str):
    '''Update goal progress when deliverable status changes'''
    try:
        # Count completed deliverables for this goal
        deliverables = supabase.table('deliverables').select('status').eq('goal_id', goal_id).execute()
        completed_count = len([d for d in deliverables.data if d['status'] == 'completed'])
        
        # Get goal target
        goal = supabase.table('workspace_goals').select('target_value, current_value').eq('id', goal_id).single().execute()
        
        if goal.data:
            new_value = min(completed_count, goal.data['target_value'])
            
            # Only update if changed
            if new_value != goal.data['current_value']:
                update_data = {
                    'current_value': new_value,
                    'updated_at': datetime.now().isoformat()
                }
                
                # Mark complete if reached target
                if new_value >= goal.data['target_value']:
                    update_data['status'] = 'completed'
                    update_data['completed_at'] = datetime.now().isoformat()
                
                supabase.table('workspace_goals').update(update_data).eq('id', goal_id).execute()
                logger.info(f"✅ Updated goal {goal_id} progress: {new_value}/{goal.data['target_value']}")
                
    except Exception as e:
        logger.error(f"Failed to update goal progress: {e}")

# Call after create_deliverable:
if mapped_goal_id:
    await update_goal_progress_from_deliverable(mapped_goal_id)

# Call after update_deliverable when status changes:
if 'status' in update_data and deliverable.get('goal_id'):
    await update_goal_progress_from_deliverable(deliverable['goal_id'])
""")


def main():
    """Main execution"""
    print("\n" + "="*80)
    print("🎯 GOAL PROGRESS CALCULATION FIX - CRITICAL SYSTEM REPAIR")
    print("="*80)
    
    # Get workspace ID from command line or use default
    workspace_id = sys.argv[1] if len(sys.argv) > 1 else 'e29a33af-b473-4d9c-b983-f5c1aa70a830'
    
    # Step 1: Diagnose
    print("\n📋 PHASE 1: DIAGNOSIS")
    diagnosis = diagnose_workspace(workspace_id)
    
    if not diagnosis['issues']:
        print("\n✅ No issues found! Goal progress is accurate.")
        return
    
    print("\n⚠️ ISSUES FOUND:")
    for issue in diagnosis['issues']:
        print(f"  - {issue}")
    
    print("\n💡 RECOMMENDATIONS:")
    for rec in diagnosis['recommendations']:
        print(f"  - {rec}")
    
    # Step 2: Fix (with confirmation)
    print("\n📋 PHASE 2: FIX")
    
    # First do dry run
    print("\n🔍 Performing dry run...")
    dry_run_report = fix_progress(workspace_id, dry_run=True)
    
    if dry_run_report['goals_fixed'] == 0:
        print("\n✅ No fixes needed!")
        return
    
    print(f"\n📊 Dry run would fix {dry_run_report['goals_fixed']} goals")
    
    # Ask for confirmation
    response = input("\n❓ Apply fixes? (yes/no): ").strip().lower()
    
    if response == 'yes':
        print("\n🚀 Applying fixes...")
        fix_report = fix_progress(workspace_id, dry_run=False)
        
        print("\n✅ FIX COMPLETE!")
        print(f"  - Goals Fixed: {fix_report['goals_fixed']}")
        print(f"  - Goals Completed: {fix_report['goals_completed']}")
        
        # Verify fix
        print("\n📋 PHASE 3: VERIFICATION")
        verification = diagnose_workspace(workspace_id)
        
        if not verification['issues']:
            print("\n🎉 SUCCESS! All goal progress calculations are now correct!")
        else:
            print("\n⚠️ Some issues remain:")
            for issue in verification['issues']:
                print(f"  - {issue}")
    else:
        print("\n❌ Fix cancelled")
    
    # Step 3: Show implementation guide
    print("\n📋 PHASE 4: PREVENTION")
    implement_automatic_update(workspace_id)


if __name__ == '__main__':
    main()