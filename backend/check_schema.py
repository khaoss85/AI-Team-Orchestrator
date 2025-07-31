#!/usr/bin/env python3
"""
Check actual database schema
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(__file__))

from database import supabase

async def check_schema():
    workspace_id = "3572a15c-ca7d-454e-8528-d19a7b6b7453"
    
    print(f"🔍 CHECKING DATABASE SCHEMA")
    print("="*60)
    
    # Try common table names
    tables_to_check = [
        "workspaces", "agents", "tasks", "deliverables", 
        "assets", "objectives", "team_proposals",
        "task_outputs", "workspace_assets", "agent_outputs"
    ]
    
    for table_name in tables_to_check:
        try:
            response = supabase.table(table_name).select("*").limit(1).execute()
            print(f"✅ Table '{table_name}' exists")
            
            # If table exists and we're checking the workspace, get the data
            if table_name in ["deliverables", "assets", "workspace_assets", "task_outputs"]:
                workspace_response = supabase.table(table_name).select("*").eq("workspace_id", workspace_id).execute()
                data = workspace_response.data if workspace_response.data else []
                print(f"   - {len(data)} records for workspace")
                
                if data and len(data) > 0:
                    # Show first record structure
                    print(f"   - Sample record keys: {list(data[0].keys())}")
                    
                    # Look for content fields
                    for record in data[:3]:  # Check first 3 records
                        for key, value in record.items():
                            if 'content' in key.lower() and value:
                                content_str = str(value)
                                if len(content_str) > 50:
                                    print(f"   - Found content in '{key}': {len(content_str)} chars")
                                    print(f"     Preview: {content_str[:200]}...")
                                    break
                    
        except Exception as e:
            if "does not exist" in str(e):
                print(f"❌ Table '{table_name}' does not exist")
            else:
                print(f"❌ Error checking table '{table_name}': {e}")

if __name__ == "__main__":
    asyncio.run(check_schema())