#!/usr/bin/env python3
"""
Apply Email Sequence Goal-Deliverable Mapping Fix

This script fixes the deliverable-goal mapping issue where Email sequence
deliverables were incorrectly assigned to wrong goals, causing 200% progress
on some goals and 0 deliverables on others.

Usage: python3 apply_email_sequence_fix.py
"""

import os
import sys
from supabase import create_client
import json

# Set environment variables if not already set
if not os.environ.get('SUPABASE_URL'):
    os.environ['SUPABASE_URL'] = 'https://szerliaxjcverzdoisik.supabase.co'
if not os.environ.get('SUPABASE_KEY'):
    os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN6ZXJsaWF4amN2ZXJ6ZG9pc2lrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzU5MTQ5MjMsImV4cCI6MjA1MTQ5MDkyM30.KP9PjCQ3gCzYZBi8P2u_yX0F8i6C7zy9bHqQTvmqmBc'

def main():
    """Apply the email sequence goal mapping fix."""
    
    client = create_client(
        os.environ.get('SUPABASE_URL'),
        os.environ.get('SUPABASE_KEY')
    )
    
    workspace_id = '824eae92-6f35-4bfb-b128-8c66c0af52b3'
    
    # Goal mappings based on correct analysis
    goal_mappings = {
        'Email sequence 1': '8271841e-9f0c-45b0-8559-b2c33e8178dd',  # Target goal from user
        'Email sequence 2': 'b148c5e7-929c-481b-809b-127d9e17d189',
        'Email sequence 3': 'ecd86d23-72a2-41a5-b54d-568f62edea94',
        'Lista contatti ICP': 'd93059fe-353f-4391-a825-7546714bd853',
        'Numero totale di contatti': 'eb9b3979-b5e3-4869-9b2e-e62d72d50967'
    }
    
    print("🔧 APPLYING EMAIL SEQUENCE GOAL MAPPING FIX")
    print(f"Workspace: {workspace_id}")
    print("=" * 60)
    
    # Get current deliverables
    deliverables_result = client.table('deliverables').select('*').eq('workspace_id', workspace_id).execute()
    deliverables = deliverables_result.data
    
    print(f"📊 Found {len(deliverables)} deliverables in workspace")
    
    updates_applied = 0
    
    # Apply pattern-based mapping fixes
    for deliverable in deliverables:
        title = deliverable.get('title', '')
        current_goal_id = deliverable.get('goal_id')
        deliverable_id = deliverable.get('id')
        
        new_goal_id = None
        pattern_matched = None
        
        # Pattern matching logic
        for pattern, target_goal in goal_mappings.items():
            if pattern in title:
                new_goal_id = target_goal
                pattern_matched = pattern
                break
        
        # Apply update if needed
        if new_goal_id and new_goal_id != current_goal_id:
            try:
                update_result = client.table('deliverables').update({
                    'goal_id': new_goal_id
                }).eq('id', deliverable_id).execute()
                
                print(f"✅ UPDATED: {title[:50]}...")
                print(f"   Pattern: {pattern_matched}")
                print(f"   Old goal_id: {current_goal_id or 'NULL'}")
                print(f"   New goal_id: {new_goal_id}")
                print(f"   ---")
                
                updates_applied += 1
                
            except Exception as e:
                print(f"❌ ERROR updating deliverable {deliverable_id}: {e}")
    
    print(f"\n🎯 SUMMARY:")
    print(f"   Total updates applied: {updates_applied}")
    
    # Validation: Check final state
    print(f"\n🔍 VALIDATION:")
    
    # Get workspace goals for validation
    goals_result = client.table('workspace_goals').select('*').eq('workspace_id', workspace_id).execute()
    goals = {g['id']: g['description'] for g in goals_result.data}
    
    # Recheck deliverables after fix
    updated_deliverables = client.table('deliverables').select('*').eq('workspace_id', workspace_id).execute().data
    
    # Group by goal_id
    deliverables_by_goal = {}
    orphaned_count = 0
    
    for d in updated_deliverables:
        goal_id = d.get('goal_id')
        if not goal_id:
            orphaned_count += 1
        else:
            if goal_id not in deliverables_by_goal:
                deliverables_by_goal[goal_id] = []
            deliverables_by_goal[goal_id].append(d)
    
    print(f"   Remaining orphaned deliverables: {orphaned_count}")
    
    print(f"\n📋 GOAL-DELIVERABLE DISTRIBUTION:")
    for goal_id, goal_description in goals.items():
        count = len(deliverables_by_goal.get(goal_id, []))
        status = "✅" if count > 0 else "⚠️ "
        print(f"   {status} {goal_description[:50]}... ({count} deliverables)")
        
        # Check the target goal specifically
        if goal_id == '8271841e-9f0c-45b0-8559-b2c33e8178dd':
            print(f"   🎯 TARGET GOAL - Should now have deliverables: {count > 0}")
    
    print(f"\n🎉 Fix application completed!")
    
if __name__ == "__main__":
    main()