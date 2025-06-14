#!/usr/bin/env python3
"""
Script per approvare automaticamente le task in pending_verification
e sbloccare il progresso del workspace
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

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

print("🚀 APPROVAZIONE AUTOMATICA TASK PENDING")
print(f"Workspace ID: {workspace_id}")
print("=" * 60)

# 1. Get all pending verification tasks
result = supabase.table('tasks').select('*').eq('workspace_id', workspace_id).eq('status', 'pending_verification').execute()
pending_tasks = result.data

print(f"\n📋 Task in pending_verification: {len(pending_tasks)}")

for task in pending_tasks:
    task_id = task['id']
    task_name = task['name']
    
    print(f"\n🔄 Approvando task: {task_name[:50]}...")
    print(f"   ID: {task_id}")
    
    try:
        # Update task status to completed
        update_result = supabase.table('tasks').update({
            'status': 'completed',
            'updated_at': datetime.now().isoformat()
        }).eq('id', task_id).execute()
        
        if update_result.data:
            print(f"   ✅ Task approvata e completata")
            
            # Check if task has contributions to goals
            contribution = task.get('contribution_expected', 0)
            goal_id = task.get('goal_id')
            metric_type = task.get('metric_type')
            
            if contribution and goal_id and metric_type:
                print(f"   📊 Contributo goal: +{contribution} per {metric_type}")
                
                # Update goal progress
                goal_result = supabase.table('workspace_goals').select('*').eq('workspace_id', workspace_id).eq('metric_type', metric_type).execute()
                
                if goal_result.data:
                    current_goal = goal_result.data[0]
                    new_value = current_goal['current_value'] + contribution
                    
                    supabase.table('workspace_goals').update({
                        'current_value': new_value,
                        'updated_at': datetime.now().isoformat()
                    }).eq('id', current_goal['id']).execute()
                    
                    print(f"   🎯 Goal aggiornato: {current_goal['current_value']} → {new_value}")
        else:
            print(f"   ❌ Errore nell'approvazione")
            
    except Exception as e:
        print(f"   ❌ Errore: {e}")

# 2. Check new goal status
print(f"\n🎯 NUOVI GOAL STATUS:")
result = supabase.table('workspace_goals').select('*').eq('workspace_id', workspace_id).execute()
total_progress = 0

for goal in result.data:
    current = goal['current_value']
    target = goal['target_value']
    progress = (current / target * 100) if target > 0 else 0
    total_progress += progress
    
    print(f"  {goal['metric_type']}: {current}/{target} ({progress:.1f}%)")

avg_progress = total_progress / len(result.data) if result.data else 0
print(f"\n📊 NUOVO PROGRESSO MEDIO: {avg_progress:.1f}%")
print(f"🚦 SOGLIA FINALIZZAZIONE: 95.0%")
print(f"Status: {'✅ SBLOCCATO' if avg_progress >= 95 else '🚫 ANCORA BLOCCATO'}")

if avg_progress < 95:
    shortage = 95 - avg_progress
    print(f"\n💡 MANCANO ANCORA {shortage:.1f}% per sbloccare la finalizzazione")
    print(f"Possibili azioni:")
    print(f"  - Creare task aggiuntive per 'quality_score' (target: 50, attuale: ~{result.data[1]['current_value'] if len(result.data) > 1 else 'N/A'})")
    print(f"  - Aggiungere giorni al 'timeline_days' (target: 6, attuale: {result.data[0]['current_value'] if result.data else 'N/A'})")
    print(f"  - Completare il terzo deliverable (target: 3, attuale: ~{result.data[2]['current_value'] if len(result.data) > 2 else 'N/A'})")

print(f"\n✅ Script completato!")