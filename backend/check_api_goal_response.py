#!/usr/bin/env python3
"""
Check how the API returns goal data to understand the progress field issue.
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
load_dotenv('.env')

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

workspace_id = "3adfdc92-b316-442f-b9ca-a8d1df49e200"

# Get goals as the API would
goals_response = supabase.table('workspace_goals').select('*').eq('workspace_id', workspace_id).execute()
goals = goals_response.data if goals_response else []

print("API GOAL RESPONSE STRUCTURE:")
print("=" * 80)

if goals:
    # Show first goal structure
    goal = goals[0]
    print(f"Goal: {goal.get('description', 'Unknown')[:50]}...")
    print()
    
    # Check for progress field
    if 'progress' in goal:
        print(f"✅ Has 'progress' field: {goal['progress']}")
    else:
        print("❌ No 'progress' field in response")
    
    # Show values for progress calculation
    current = goal.get('current_value', 0)
    target = goal.get('target_value', 1)
    calculated_progress = (current / target * 100) if target > 0 else 0
    
    print(f"   current_value: {current}")
    print(f"   target_value: {target}")
    print(f"   Calculated progress: {calculated_progress:.1f}%")
    
    # Show all fields
    print("\nAll fields in goal object:")
    for key in goal.keys():
        print(f"   - {key}")
else:
    print("No goals found")