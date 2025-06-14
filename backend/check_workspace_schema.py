#!/usr/bin/env python3
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Check existing workspace structure
result = supabase.table('workspaces').select('*').limit(1).execute()
if result.data:
    workspace = result.data[0]
    print("📋 WORKSPACE SCHEMA:")
    for key, value in workspace.items():
        print(f"  {key}: {type(value).__name__}")
else:
    print("❌ No workspace found to inspect")