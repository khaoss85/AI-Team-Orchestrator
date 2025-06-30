#!/usr/bin/env python3
"""
Debug Database Structure

Check what data exists in the database and the table structure.
"""

import os
import sys
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import supabase

def check_table_structure():
    """Check what tables and data exist"""
    
    tables_to_check = [
        "workspaces",
        "tasks", 
        "agents",
        "workspace_goals",
        "deliverables",
        "asset_artifacts",
        "asset_requirements"
    ]
    
    print("🔍 DATABASE STRUCTURE ANALYSIS")
    print("="*60)
    
    for table in tables_to_check:
        try:
            # Get record count
            result = supabase.table(table).select("*", count="exact").limit(1).execute()
            count = result.count if hasattr(result, 'count') else len(result.data) if result.data else 0
            
            print(f"\n📊 Table: {table}")
            print(f"   Records: {count}")
            
            # Get a sample record if exists
            if result.data:
                sample = result.data[0]
                print("   Sample fields:")
                for key in list(sample.keys())[:10]:  # First 10 fields
                    value = sample[key]
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                    print(f"     {key}: {value}")
                
                if len(sample.keys()) > 10:
                    print(f"     ... and {len(sample.keys()) - 10} more fields")
            else:
                print("   No records found")
                
        except Exception as e:
            print(f"\n❌ Table: {table}")
            print(f"   Error: {e}")
    
    # Check for any recent workspace activity
    print(f"\n🔍 LOOKING FOR RECENT ACTIVITY...")
    
    try:
        # Try to find any workspaces with recent activity
        recent_result = supabase.table("workspaces").select("*").order("created_at", desc=True).limit(5).execute()
        if recent_result.data:
            print(f"Found {len(recent_result.data)} recent workspaces:")
            for ws in recent_result.data:
                print(f"  - {ws.get('id')}: {ws.get('goal', 'No goal')[:60]}...")
        else:
            print("No recent workspaces found")
            
    except Exception as e:
        print(f"Error checking recent workspaces: {e}")
    
    # Check for tasks
    try:
        tasks_result = supabase.table("tasks").select("*").limit(5).execute()
        if tasks_result.data:
            print(f"\nFound {len(tasks_result.data)} recent tasks:")
            for task in tasks_result.data:
                print(f"  - {task.get('id')}: {task.get('name', 'No name')[:60]}... (Status: {task.get('status')})")
        else:
            print("\nNo tasks found")
            
    except Exception as e:
        print(f"\nError checking tasks: {e}")

if __name__ == "__main__":
    check_table_structure()