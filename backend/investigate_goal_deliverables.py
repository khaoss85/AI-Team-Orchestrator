#!/usr/bin/env python3
"""
Investigation script for goal-deliverable mapping issues in workspace.
This script analyzes the current state and identifies problems.
"""

import os
import sys
from typing import Dict, List, Any
from supabase import create_client, Client
from dotenv import load_dotenv
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Load environment
load_dotenv('.env')

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
if not supabase_url or not supabase_key:
    print("ERROR: Missing SUPABASE_URL or SUPABASE_KEY")
    sys.exit(1)

supabase: Client = create_client(supabase_url, supabase_key)

def investigate_workspace(workspace_id: str):
    """Comprehensive investigation of goal-deliverable issues."""
    
    print(f"🔍 INVESTIGATING WORKSPACE: {workspace_id}")
    print("=" * 80)
    
    # 1. Get all goals in workspace
    goals_response = supabase.table('workspace_goals').select('*').eq('workspace_id', workspace_id).execute()
    goals = goals_response.data if goals_response else []
    
    print(f"\n📊 GOALS ANALYSIS ({len(goals)} total goals)")
    print("-" * 80)
    
    goals_by_id = {g['id']: g for g in goals}
    
    # Analyze each goal
    for goal in sorted(goals, key=lambda x: x.get('description', '')):
        print(f"\n🎯 Goal: {goal['description'][:60]}...")
        print(f"   ID: {goal['id']}")
        print(f"   Type: {goal.get('metric_type', 'unknown')}")
        print(f"   Progress: {goal.get('progress', 0)}% (current: {goal.get('current_value', 0)}/{goal.get('target_value', 0)})")
        print(f"   Status: {goal.get('status', 'unknown')}")
    
    # 2. Get all deliverables in workspace
    deliverables_response = supabase.table('deliverables').select('*').eq('workspace_id', workspace_id).execute()
    deliverables = deliverables_response.data if deliverables_response else []
    
    print(f"\n📦 DELIVERABLES ANALYSIS ({len(deliverables)} total deliverables)")
    print("-" * 80)
    
    # Group deliverables by goal
    deliverables_by_goal: Dict[str, List[Any]] = {}
    orphaned_deliverables = []
    
    for deliv in deliverables:
        goal_id = deliv.get('goal_id')
        if goal_id and goal_id in goals_by_id:
            if goal_id not in deliverables_by_goal:
                deliverables_by_goal[goal_id] = []
            deliverables_by_goal[goal_id].append(deliv)
        else:
            orphaned_deliverables.append(deliv)
    
    # 3. Identify issues
    print("\n🚨 IDENTIFIED ISSUES:")
    print("-" * 80)
    
    # Issue 1: Goals with 0% progress but should have deliverables
    zero_progress_goals = [g for g in goals if g.get('progress', 0) == 0]
    print(f"\n1️⃣ GOALS STUCK AT 0% ({len(zero_progress_goals)} goals):")
    for goal in zero_progress_goals:
        goal_id = goal['id']
        delivs = deliverables_by_goal.get(goal_id, [])
        if delivs:
            completed = sum(1 for d in delivs if d.get('status') == 'completed')
            print(f"   ❌ {goal['description'][:50]}...")
            print(f"      Has {len(delivs)} deliverables ({completed} completed) but shows 0%")
        else:
            print(f"   ⚠️  {goal['description'][:50]}... - No deliverables assigned")
    
    # Issue 2: Content mismatches
    print(f"\n2️⃣ CONTENT MISMATCHES:")
    for goal_id, delivs in deliverables_by_goal.items():
        goal = goals_by_id[goal_id]
        for deliv in delivs:
            # Check for obvious mismatches
            goal_keywords = goal['description'].lower().split()
            deliv_title = deliv.get('title', '').lower()
            
            # Special case checks
            if 'csv' in goal['description'].lower() and 'hubspot' in goal['description'].lower():
                if 'csv' not in deliv_title and 'hubspot' not in deliv_title and 'import' not in deliv_title:
                    print(f"   ❌ Mismatch: Goal '{goal['description'][:40]}...'")
                    print(f"      Has deliverable: '{deliv['title'][:60]}...'")
                    print(f"      Status: {deliv.get('status')}")
    
    # Issue 3: Display content issues  
    print(f"\n3️⃣ DISPLAY CONTENT ISSUES:")
    no_display_content = 0
    has_raw_json = 0
    
    for deliv in deliverables:
        display_content = deliv.get('display_content')
        if not display_content:
            no_display_content += 1
        elif display_content and (display_content.startswith('{') or display_content.startswith('[')):
            has_raw_json += 1
            print(f"   ❌ Raw JSON in display_content: {deliv['title'][:50]}...")
            print(f"      Display content preview: {display_content[:100]}...")
    
    print(f"\n   📊 Statistics:")
    print(f"      - Missing display_content: {no_display_content}/{len(deliverables)}")
    print(f"      - Raw JSON in display_content: {has_raw_json}/{len(deliverables)}")
    
    # Issue 4: Orphaned deliverables
    if orphaned_deliverables:
        print(f"\n4️⃣ ORPHANED DELIVERABLES ({len(orphaned_deliverables)} deliverables):")
        for deliv in orphaned_deliverables[:5]:  # Show first 5
            print(f"   - {deliv['title'][:60]}... (goal_id: {deliv.get('goal_id')})")
    
    # 5. Progress calculation analysis
    print("\n📈 PROGRESS CALCULATION ANALYSIS:")
    print("-" * 80)
    
    for goal in goals:
        goal_id = goal['id']
        delivs = deliverables_by_goal.get(goal_id, [])
        
        if delivs:
            total = len(delivs)
            completed = sum(1 for d in delivs if d.get('status') == 'completed')
            calculated_progress = (completed / total * 100) if total > 0 else 0
            reported_progress = goal.get('progress', 0)
            
            if abs(calculated_progress - reported_progress) > 5:  # More than 5% discrepancy
                print(f"\n   ⚠️ Progress discrepancy for: {goal['description'][:50]}...")
                print(f"      Reported: {reported_progress}%")
                print(f"      Calculated: {calculated_progress:.1f}% ({completed}/{total} deliverables)")
                print(f"      Discrepancy: {abs(calculated_progress - reported_progress):.1f}%")
    
    # 6. Get specific problem goal details
    problem_goal_id = '2491a9e0-c4ef-41fc-b2b4-e9eb41666972'
    if problem_goal_id in goals_by_id:
        print(f"\n🔍 DETAILED ANALYSIS OF PROBLEM GOAL:")
        print("-" * 80)
        problem_goal = goals_by_id[problem_goal_id]
        print(f"Goal: {problem_goal['description']}")
        print(f"Expected content: CSV file for HubSpot import")
        
        problem_delivs = deliverables_by_goal.get(problem_goal_id, [])
        for deliv in problem_delivs:
            print(f"\n   Deliverable: {deliv['title']}")
            print(f"   Status: {deliv.get('status')}")
            print(f"   Has display_content: {bool(deliv.get('display_content'))}")
            
            # Check content semantics
            content = deliv.get('content', {})
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except:
                    pass
            
            if isinstance(content, dict):
                print(f"   Content type: {content.get('type', 'unknown')}")
                print(f"   Content keys: {list(content.keys())[:5]}")
    
    print("\n" + "=" * 80)
    print("🏁 INVESTIGATION COMPLETE")
    
    # Summary recommendations
    print("\n💡 RECOMMENDATIONS:")
    print("1. Run goal progress recalculation for all goals")
    print("2. Trigger AI content display transformation for deliverables missing display_content")
    print("3. Re-run AI Goal Matcher for mismatched deliverables")
    print("4. Validate that new deliverables are using correct goal matching logic")

if __name__ == "__main__":
    workspace_id = "3adfdc92-b316-442f-b9ca-a8d1df49e200"
    investigate_workspace(workspace_id)