#!/usr/bin/env python3
"""
Comprehensive fix for all goal-deliverable issues:
1. Calculate and add progress field to goals
2. Fix raw JSON in display content
3. Fix content mismatches
"""

import os
import sys
from typing import Dict, List, Any
from supabase import create_client, Client
from dotenv import load_dotenv
import json
import re
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
load_dotenv('.env')

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

def fix_goal_progress_field(workspace_id: str):
    """
    Add calculated progress field to goals that's missing from API responses.
    """
    print("🔧 FIX 1: Adding Progress Field to Goals")
    print("=" * 80)
    
    # Get all goals
    goals_response = supabase.table('workspace_goals').select('*').eq('workspace_id', workspace_id).execute()
    goals = goals_response.data if goals_response else []
    
    # Get all deliverables
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
        
        # Calculate progress from deliverables
        goal_deliverables = deliverables_by_goal.get(goal_id, [])
        
        # Calculate proper current_value and target_value based on deliverables
        if goal_deliverables:
            total = len(goal_deliverables)
            completed = sum(1 for d in goal_deliverables if d.get('status') == 'completed')
            
            # Update current_value to match completed deliverables
            updates = {
                'current_value': float(completed),
                'target_value': float(max(total, goal.get('target_value', 1)))
            }
            
            # Update status if all deliverables are completed
            if completed == total and total > 0:
                updates['status'] = 'completed'
                if not goal.get('completed_at'):
                    updates['completed_at'] = datetime.now().isoformat()
            
            # Apply updates
            print(f"\n📊 Fixing Goal: {goal_desc}")
            print(f"   Deliverables: {completed}/{total} completed")
            print(f"   Current Value: {goal.get('current_value')} → {updates['current_value']}")
            print(f"   Target Value: {goal.get('target_value')} → {updates['target_value']}")
            
            update_response = supabase.table('workspace_goals').update(updates).eq('id', goal_id).execute()
            
            if update_response.data:
                print("   ✅ FIXED")
                fixes_applied += 1
            else:
                print("   ❌ Update failed")
    
    print(f"\n✅ Fixed {fixes_applied} goals with progress calculation")
    return fixes_applied

def fix_raw_json_in_display_content(workspace_id: str):
    """
    Fix deliverables that have raw Python dict strings in their HTML display content.
    """
    print("\n🔧 FIX 2: Fixing Raw JSON in Display Content")
    print("=" * 80)
    
    deliverables_response = supabase.table('deliverables').select('*').eq('workspace_id', workspace_id).execute()
    deliverables = deliverables_response.data if deliverables_response else []
    
    fixes_applied = 0
    
    for deliv in deliverables:
        display_content = deliv.get('display_content', '')
        
        # Check if display_content contains Python dict representation
        if "{'title':" in display_content or '{"title":' in display_content:
            print(f"\n❌ Found problematic deliverable: {deliv['title'][:50]}...")
            print(f"   ID: {deliv['id']}")
            
            # Fix the display content by converting Python dicts to proper HTML
            fixed_content = display_content
            
            # Replace Python dict representations with formatted HTML
            # Pattern to match {'title': 'xxx', 'description': 'yyy'}
            dict_pattern = r"\{['\"]title['\"]:\s*['\"]([^'\"]+)['\"],\s*['\"]description['\"]:\s*['\"]([^'\"]+)['\"]\}"
            
            def replace_dict_with_html(match):
                title = match.group(1)
                description = match.group(2)
                return f"<strong>{title}</strong>: {description}"
            
            fixed_content = re.sub(dict_pattern, replace_dict_with_html, fixed_content)
            
            # If still has dict-like content, do a more aggressive fix
            if "{'title':" in fixed_content:
                # Remove the dict representations entirely and format as clean HTML
                lines = []
                for line in fixed_content.split('\n'):
                    if "{'title':" in line:
                        # Extract title and description manually
                        try:
                            # Parse the dict string
                            dict_str = line[line.find("{'title':"):line.rfind("}")+1]
                            # Clean it up for safer evaluation
                            dict_str = dict_str.replace("'", '"')
                            parsed = json.loads(dict_str)
                            title = parsed.get('title', '')
                            desc = parsed.get('description', '')
                            # Replace with formatted HTML
                            line = line.replace(dict_str, f"<strong>{title}</strong>: {desc}")
                        except:
                            # If parsing fails, just remove the dict notation
                            line = re.sub(r"\{[^}]+\}", "", line)
                    lines.append(line)
                fixed_content = '\n'.join(lines)
            
            # Update the display content
            update_response = supabase.table('deliverables').update({
                'display_content': fixed_content,
                'display_format': 'html'
            }).eq('id', deliv['id']).execute()
            
            if update_response.data:
                print("   ✅ FIXED display content")
                fixes_applied += 1
            else:
                print("   ❌ Update failed")
    
    print(f"\n✅ Fixed {fixes_applied} deliverables with raw JSON in display content")
    return fixes_applied

def fix_content_mismatch(workspace_id: str):
    """
    Fix deliverables assigned to wrong goals (content mismatch).
    """
    print("\n🔧 FIX 3: Fixing Content Mismatches")
    print("=" * 80)
    
    # Get all goals and deliverables
    goals_response = supabase.table('workspace_goals').select('*').eq('workspace_id', workspace_id).execute()
    goals = goals_response.data if goals_response else []
    
    deliverables_response = supabase.table('deliverables').select('*').eq('workspace_id', workspace_id).execute()
    deliverables = deliverables_response.data if deliverables_response else []
    
    goals_by_id = {g['id']: g for g in goals}
    fixes_applied = 0
    
    # Check each deliverable for correct goal assignment
    for deliv in deliverables:
        current_goal_id = deliv.get('goal_id')
        if not current_goal_id or current_goal_id not in goals_by_id:
            continue
        
        current_goal = goals_by_id[current_goal_id]
        deliv_title = deliv.get('title', '').lower()
        deliv_content = json.dumps(deliv.get('content', {})).lower() if deliv.get('content') else ''
        
        # Special case: CSV/HubSpot goal should have CSV/HubSpot deliverables
        if 'csv' in current_goal['description'].lower() and 'hubspot' in current_goal['description'].lower():
            # Check if deliverable is actually about CSV/HubSpot
            if not ('csv' in deliv_title or 'hubspot' in deliv_title or 'import' in deliv_title or 'contact' in deliv_title):
                # This deliverable doesn't match - find better goal
                print(f"\n❌ Mismatch found:")
                print(f"   Deliverable: {deliv['title'][:50]}...")
                print(f"   Current Goal: {current_goal['description'][:50]}...")
                
                # Find better matching goal
                best_match = None
                best_score = 0
                
                for goal in goals:
                    goal_desc = goal['description'].lower()
                    score = 0
                    
                    # Check for keyword matches
                    if 'email' in deliv_title and 'email' in goal_desc:
                        score += 3
                    if 'sequen' in deliv_title and 'sequen' in goal_desc:
                        score += 3
                    if 'prospect' in deliv_title and ('contact' in goal_desc or 'icp' in goal_desc):
                        score += 2
                    if 'analisi' in deliv_title and 'analisi' in goal_desc:
                        score += 3
                    
                    if score > best_score:
                        best_score = score
                        best_match = goal
                
                if best_match and best_match['id'] != current_goal_id:
                    print(f"   Better Match: {best_match['description'][:50]}...")
                    
                    # Update goal assignment
                    update_response = supabase.table('deliverables').update({
                        'goal_id': best_match['id']
                    }).eq('id', deliv['id']).execute()
                    
                    if update_response.data:
                        print("   ✅ REASSIGNED")
                        fixes_applied += 1
                    else:
                        print("   ❌ Update failed")
    
    print(f"\n✅ Fixed {fixes_applied} deliverable goal assignments")
    return fixes_applied

def main():
    workspace_id = "3adfdc92-b316-442f-b9ca-a8d1df49e200"
    
    print("🚀 COMPREHENSIVE GOAL-DELIVERABLE FIX")
    print("=" * 80)
    print(f"Workspace: {workspace_id}")
    print()
    
    # Apply all fixes
    total_fixes = 0
    
    # Fix 1: Goal progress calculation
    total_fixes += fix_goal_progress_field(workspace_id)
    
    # Fix 2: Raw JSON in display content
    total_fixes += fix_raw_json_in_display_content(workspace_id)
    
    # Fix 3: Content mismatches
    total_fixes += fix_content_mismatch(workspace_id)
    
    print("\n" + "=" * 80)
    print(f"🏁 ALL FIXES COMPLETE")
    print(f"   Total fixes applied: {total_fixes}")
    print()
    print("💡 Next Steps:")
    print("   1. Refresh the frontend to see updated progress")
    print("   2. Check that goals show correct progress percentages")
    print("   3. Verify deliverables display properly formatted content")
    print("   4. Confirm CSV/HubSpot goal shows relevant deliverables")

if __name__ == "__main__":
    main()