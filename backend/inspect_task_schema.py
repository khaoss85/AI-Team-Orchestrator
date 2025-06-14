#!/usr/bin/env python3
"""
Script per ispezionare la struttura della tabella tasks
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("❌ SUPABASE_URL and SUPABASE_KEY environment variables required")
    sys.exit(1)

supabase: Client = create_client(url, key)

workspace_id = "bf197714-28c4-402a-84d1-e57cea3df330"

print("🔍 ISPEZIONE SCHEMA TABELLA TASKS")
print("=" * 50)

# Get one existing task to see the actual schema
result = supabase.table('tasks').select('*').eq('workspace_id', workspace_id).limit(1).execute()

if result.data:
    task = result.data[0]
    print("\n📋 COLONNE DISPONIBILI NELLA TABELLA TASKS:")
    for key, value in task.items():
        value_preview = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
        print(f"  {key}: {type(value).__name__} = {value_preview}")
else:
    print("❌ Nessuna task trovata per ispezionare lo schema")