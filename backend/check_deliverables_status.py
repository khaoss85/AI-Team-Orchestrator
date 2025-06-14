#!/usr/bin/env python3
"""
Script per verificare lo stato dei deliverable e goal del workspace bloccato
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

print("🔍 DIAGNOSTICA WORKSPACE BLOCCATO")
print(f"Workspace ID: {workspace_id}")
print("=" * 60)

# 1. Check deliverables (trying different table names)
print("\n📦 DELIVERABLE STATUS:")
tables_to_check = ['deliverable_progress', 'workspace_deliverables', 'deliverables']

for table_name in tables_to_check:
    try:
        result = supabase.table(table_name).select('*').eq('workspace_id', workspace_id).execute()
        if result.data:
            print(f"  Trovati {len(result.data)} in tabella '{table_name}'")
            for item in result.data[:3]:  # Show first 3
                print(f"    ID: {item.get('id', 'N/A')[:8] if item.get('id') else 'N/A'}...")
                print(f"    Status: {item.get('status', 'N/A')}")
                print(f"    Data: {item.get('created_at', 'N/A')[:19] if item.get('created_at') else 'N/A'}")
    except Exception as e:
        continue

# 2. Check workspace goals
print("\n🎯 WORKSPACE GOALS STATUS:")
result = supabase.table('workspace_goals').select('*').eq('workspace_id', workspace_id).execute()
total_progress = 0

for goal in result.data:
    current = goal['current_value']
    target = goal['target_value']
    progress = (current / target * 100) if target > 0 else 0
    total_progress += progress
    
    print(f"  {goal['metric_type']}: {current}/{target} ({progress:.1f}%)")

avg_progress = total_progress / len(result.data) if result.data else 0
print(f"\n📊 PROGRESSO MEDIO: {avg_progress:.1f}%")
print(f"🚦 SOGLIA FINALIZZAZIONE: 95.0%")
print(f"Status: {'✅ SBLOCCATO' if avg_progress >= 95 else '🚫 BLOCCATO'}")

# 3. Check pending feedback requests (try different table names)
print("\n💬 RICHIESTE FEEDBACK PENDING:")
try:
    result = supabase.table('human_feedback_requests').select('*').eq('workspace_id', workspace_id).eq('status', 'pending').execute()
    print(f"Richieste in attesa: {len(result.data)}")
    for req in result.data[:3]:
        print(f"  ID: {req['id'][:8]}... - {req.get('request_type', 'N/A')}")
        print(f"  Task: {req.get('task_id', 'N/A')[:8] if req.get('task_id') else 'N/A'}...")
        print(f"  Created: {req.get('created_at', 'N/A')[:19] if req.get('created_at') else 'N/A'}")
except Exception as e:
    print(f"Tabella feedback non trovata: {e}")
    try:
        # Try feedback table
        result = supabase.table('feedback').select('*').eq('workspace_id', workspace_id).execute()
        print(f"Feedback generici: {len(result.data)}")
    except:
        print("Nessuna tabella feedback trovata")

# 4. Check tasks status 
print("\n📋 TASKS STATUS:")
result = supabase.table('tasks').select('*').eq('workspace_id', workspace_id).execute()
status_counts = {}
for task in result.data:
    status = task['status']
    status_counts[status] = status_counts.get(status, 0) + 1

for status, count in status_counts.items():
    print(f"  {status}: {count}")

print(f"\nTotale task: {len(result.data)}")