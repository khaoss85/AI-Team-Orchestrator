#!/usr/bin/env python3
"""
Fix Goal Progress Calculations - Critical Database Correction
Date: 2025-09-04
Purpose: Correct goal progress inconsistencies after deliverable mapping fix
"""

import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment
load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
workspace_id = '3adfdc92-b316-442f-b9ca-a8d1df49e200'

def main():
    print('🔧 APPLYING GOAL PROGRESS FIXES USING SUPABASE CLIENT')
    print('='*60)

    try:
        # STEP 1: Get all goals that need fixing (current_value > target_value)
        print('\n📊 STEP 1: Identifying goals with excessive progress...')
        excessive_goals = supabase.table('workspace_goals').select('id, description, current_value, target_value').eq('workspace_id', workspace_id).execute()
        
        excessive_count = 0
        for goal in excessive_goals.data:
            if goal['current_value'] > goal['target_value']:
                excessive_count += 1
                print(f'  - Goal: {goal["description"][:50]}... | Progress: {goal["current_value"]}/{goal["target_value"]}')
                
                # Fix: Set current_value = target_value
                supabase.table('workspace_goals').update({
                    'current_value': goal['target_value']
                }).eq('id', goal['id']).execute()
                
        print(f'✅ Fixed {excessive_count} goals with excessive progress')
        
        # STEP 2: Recalculate progress for all goals based on completed deliverables
        print('\n🔄 STEP 2: Recalculating progress based on deliverable completion...')
        
        all_goals = supabase.table('workspace_goals').select('id, description, target_value').eq('workspace_id', workspace_id).execute()
        
        updated_count = 0
        for goal in all_goals.data:
            # Count completed deliverables for this goal
            deliverables = supabase.table('deliverables').select('status').eq('goal_id', goal['id']).execute()
            completed_count = len([d for d in deliverables.data if d['status'] == 'completed'])
            
            # Calculate new current_value (capped at target_value)
            new_current_value = min(completed_count, goal['target_value'])
            
            # Update goal
            supabase.table('workspace_goals').update({
                'current_value': new_current_value
            }).eq('id', goal['id']).execute()
            
            updated_count += 1
            progress_pct = (new_current_value / goal['target_value'] * 100) if goal['target_value'] > 0 else 0
            print(f'  - {goal["description"][:50]}... | New progress: {new_current_value}/{goal["target_value"]} ({progress_pct:.1f}%)')
        
        print(f'✅ Updated progress for {updated_count} goals')
        
        # STEP 3: Update goal status for completed goals
        print('\n🎯 STEP 3: Updating status for completed goals...')
        
        # Get goals that should be marked as completed
        goals_for_completion = supabase.table('workspace_goals').select('id, description, current_value, target_value, status').eq('workspace_id', workspace_id).execute()
        
        completed_count = 0
        for goal in goals_for_completion.data:
            if goal['current_value'] >= goal['target_value'] and goal['status'] != 'completed':
                supabase.table('workspace_goals').update({
                    'status': 'completed'
                }).eq('id', goal['id']).execute()
                
                completed_count += 1
                print(f'  - Marked as completed: {goal["description"][:50]}...')
        
        print(f'✅ Marked {completed_count} goals as completed')
        
        # STEP 4: Verification - Show final state
        print('\n📊 STEP 4: VERIFICATION - Final goal states...')
        final_goals = supabase.table('workspace_goals').select('id, description, current_value, target_value, status').eq('workspace_id', workspace_id).execute()
        
        print('\nFinal Goal States:')
        print('-' * 80)
        for goal in final_goals.data:
            progress_pct = (goal['current_value'] / goal['target_value'] * 100) if goal['target_value'] > 0 else 0
            
            # Get deliverable count for verification
            deliverables = supabase.table('deliverables').select('status').eq('goal_id', goal['id']).execute()
            completed_deliverables = len([d for d in deliverables.data if d['status'] == 'completed'])
            total_deliverables = len(deliverables.data)
            
            print(f'{goal["description"][:60]:<60} | {progress_pct:6.1f}% | {goal["current_value"]}/{goal["target_value"]} | {completed_deliverables}/{total_deliverables} deliverables | {goal["status"]}')
        
        print('\n🎯 GOAL PROGRESS FIX COMPLETED SUCCESSFULLY!')
        print('Next: Test frontend UI to verify progress displays correctly')
        
    except Exception as e:
        print(f'❌ Error during fix: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()