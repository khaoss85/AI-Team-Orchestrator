#!/usr/bin/env python3
"""
Monitor del progresso del test comprehensive E2E
"""

import requests
import time
import json

workspace_id = "f528c2ac-1265-44f6-830e-2af84cb19204"
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

def monitor_progress():
    print("🔍 MONITORING E2E TEST PROGRESS")
    print("=" * 50)
    
    while True:
        try:
            # Check tasks
            response = requests.get(f"{API_BASE}/workspaces/{workspace_id}/tasks")
            if response.status_code == 200:
                tasks = response.json()
                
                print(f"\n📋 TASK STATUS ({len(tasks)} total):")
                for task in tasks:
                    status = task.get('status', 'unknown')
                    name = task.get('name', 'Unknown')[:60]
                    agent_id = task.get('agent_id', 'unassigned')
                    print(f"  {status.upper():<10} | {name}")
                
                # Count by status
                pending = sum(1 for t in tasks if t.get('status') == 'pending')
                running = sum(1 for t in tasks if t.get('status') == 'in_progress')
                completed = sum(1 for t in tasks if t.get('status') == 'completed')
                
                print(f"\n📊 SUMMARY: {completed} completed, {running} running, {pending} pending")
                
                # Check deliverables
                response = requests.get(f"{API_BASE}/deliverables/workspace/{workspace_id}")
                if response.status_code == 200:
                    deliverables = response.json()
                    print(f"📦 DELIVERABLES: {len(deliverables)} created")
                    
                    if deliverables:
                        for d in deliverables:
                            title = d.get('title', 'Unknown')[:40]
                            print(f"  📄 {title}")
                
                # Check autonomous trigger condition
                if completed >= 2:
                    print("\n🚀 AUTONOMOUS TRIGGER CONDITIONS MET!")
                    print(f"   {completed} tasks completed - trigger should activate")
                
                # Stop if test seems complete
                if completed >= 3 and pending == 0 and running == 0:
                    print("\n✅ Test appears to be complete!")
                    break
                    
            else:
                print(f"❌ Error getting tasks: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print(f"\n⏱️ Checking again in 15 seconds...")
        time.sleep(15)

if __name__ == "__main__":
    monitor_progress()