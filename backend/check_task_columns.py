#!/usr/bin/env python3
"""
Check the actual columns in the tasks table
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

print("\n📊 Checking tasks table structure...")

# Get a sample task to see all columns
result = supabase.table("tasks").select("*").limit(1).execute()

if result.data:
    sample_task = result.data[0]
    print("\nColumns in tasks table:")
    for column_name in sample_task.keys():
        print(f"  - {column_name}: {type(sample_task[column_name]).__name__}")
    
    # Check for agent-related columns
    print("\n🔍 Agent-related columns:")
    agent_columns = [col for col in sample_task.keys() if 'agent' in col.lower()]
    if agent_columns:
        for col in agent_columns:
            print(f"  - {col}: {sample_task[col]}")
    else:
        print("  No columns with 'agent' in the name found")
    
    # Check for goal-related columns
    print("\n🎯 Goal-related columns:")
    goal_columns = [col for col in sample_task.keys() if 'goal' in col.lower()]
    if goal_columns:
        for col in goal_columns:
            print(f"  - {col}: {sample_task[col]}")
    else:
        print("  No columns with 'goal' in the name found")
else:
    print("No tasks found in the table")