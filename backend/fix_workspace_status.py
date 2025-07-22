#!/usr/bin/env python3
"""
Quick script to fix workspace status from 'error' to 'active'
"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Load environment
load_dotenv()

def fix_workspace_status(workspace_id: str):
    """Fix workspace status to active"""
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            print("❌ Missing Supabase credentials")
            return False
            
        supabase = create_client(supabase_url, supabase_key)
        
        # Update workspace status to active
        result = supabase.table("workspaces").update({
            "status": "active"
        }).eq("id", workspace_id).execute()
        
        if result.data:
            print(f"✅ Updated workspace {workspace_id} status to 'active'")
            return True
        else:
            print(f"❌ Failed to update workspace {workspace_id}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    workspace_id = "956590ae-a112-4352-ba3b-6b607948f586"
    fix_workspace_status(workspace_id)