#!/usr/bin/env python3
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Check existing goal metric types
result = supabase.table('workspace_goals').select('metric_type').execute()
if result.data:
    metric_types = list(set(goal['metric_type'] for goal in result.data))
    print("📊 METRIC TYPES ESISTENTI:")
    for metric in metric_types:
        print(f"  ✅ {metric}")
else:
    print("❌ No goals found to inspect")