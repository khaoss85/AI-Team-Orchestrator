#!/usr/bin/env python3
"""Check database schema and tables"""

import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import supabase

# Get list of tables
print("Checking available tables in the database...\n")

# Try common table names
tables_to_check = [
    'workspaces',
    'tasks', 
    'agents',
    'deliverables',
    'goals',
    'workspace_goals',
    'assets',
    'quality_rules',
    'memory_sessions',
    'semantic_memories'
]

existing_tables = []
missing_tables = []

for table in tables_to_check:
    try:
        # Try to query the table (limit 1 to be fast)
        result = supabase.table(table).select('*').limit(1).execute()
        existing_tables.append(table)
        print(f"✅ {table} - exists")
    except Exception as e:
        if 'does not exist' in str(e):
            missing_tables.append(table)
            print(f"❌ {table} - does not exist")
        else:
            print(f"⚠️  {table} - error: {str(e)}")

print(f"\nSummary:")
print(f"Existing tables: {len(existing_tables)}")
print(f"Missing tables: {len(missing_tables)}")

# Check workspace_goals specifically since goals might not exist
if 'workspace_goals' in existing_tables:
    print("\n📊 Checking workspace_goals table:")
    workspace_goals = supabase.table('workspace_goals').select('*').limit(5).execute()
    print(f"Found {len(workspace_goals.data)} workspace goals")
    
    if workspace_goals.data:
        print("\nSample workspace goal:")
        goal = workspace_goals.data[0]
        for key, value in goal.items():
            print(f"  {key}: {value}")