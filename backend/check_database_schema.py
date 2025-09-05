#!/usr/bin/env python3
"""
Check the actual database schema to understand table structure
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

print("\n" + "="*80)
print("📊 DATABASE SCHEMA CHECK")
print("="*80)

# Try to list all tables by querying different known tables
tables_to_check = [
    "workspaces",
    "goals",
    "goal_workspace",
    "tasks", 
    "agents",
    "deliverables",
    "assets",
    "messages",
    "project_understanding",
    "workspace_memory",
    "team_proposals"
]

existing_tables = []
missing_tables = []

for table_name in tables_to_check:
    try:
        # Try a simple count query
        result = supabase.table(table_name).select("id", count='exact').limit(1).execute()
        existing_tables.append(table_name)
        print(f"✅ Table '{table_name}' exists (count: {result.count if hasattr(result, 'count') else 'N/A'})")
    except Exception as e:
        if "does not exist" in str(e):
            missing_tables.append(table_name)
            print(f"❌ Table '{table_name}' does not exist")
        else:
            print(f"⚠️ Table '{table_name}' - error: {str(e)[:100]}")

print("\n" + "-"*40)
print("SUMMARY:")
print(f"Existing tables: {', '.join(existing_tables)}")
print(f"Missing tables: {', '.join(missing_tables)}")

# Check workspace_goals (the actual table name)
print("\n" + "-"*40)
print("Checking for workspace_goals table (actual goal storage):")
try:
    result = supabase.table("workspace_goals").select("*").limit(5).execute()
    print(f"✅ Table 'workspace_goals' exists with {len(result.data)} records (showing max 5)")
    if result.data:
        print("\nSample record structure:")
        sample = result.data[0]
        for key in sample.keys():
            print(f"  - {key}: {type(sample[key]).__name__}")
except Exception as e:
    print(f"❌ Error accessing workspace_goals: {str(e)[:200]}")

print("\n" + "="*80)