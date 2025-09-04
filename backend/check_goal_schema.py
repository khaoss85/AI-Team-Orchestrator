#!/usr/bin/env python3
"""
Check the actual schema of workspace_goals table.
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

# Get a sample goal to see its structure
goals_response = supabase.table('workspace_goals').select('*').limit(1).execute()

if goals_response.data:
    goal = goals_response.data[0]
    print("WORKSPACE_GOALS TABLE COLUMNS:")
    print("=" * 80)
    for key, value in goal.items():
        print(f"  {key}: {type(value).__name__}")
    
    print("\nSample values:")
    print(f"  current_value: {goal.get('current_value')}")
    print(f"  target_value: {goal.get('target_value')}")
    
    # Check if progress is calculated
    if goal.get('current_value') is not None and goal.get('target_value'):
        calculated_progress = (goal['current_value'] / goal['target_value'] * 100) if goal['target_value'] > 0 else 0
        print(f"  Calculated progress: {calculated_progress:.1f}%")
else:
    print("No goals found")