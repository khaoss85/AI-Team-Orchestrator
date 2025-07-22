#!/usr/bin/env python3
"""
Quick check for deliverables in the workspace from the test
"""

import requests
import sys

workspace_id = "b80574de-905f-4ac3-ba54-93b386d427b0"  # From the latest test output
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

print(f"🔍 Checking deliverables for workspace: {workspace_id}")

# Check deliverables
try:
    response = requests.get(f"{API_BASE}/deliverables/workspace/{workspace_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        deliverables = response.json()
        print(f"📦 Found {len(deliverables)} deliverables")
        
        if deliverables:
            print("🎉 AUTONOMOUS TRIGGER SUCCESS!")
            for i, d in enumerate(deliverables):
                print(f"  {i+1}. {d.get('title', 'Unknown')} - {d.get('type', 'Unknown')}")
        else:
            print("⚠️ No deliverables found")
    else:
        print(f"❌ Error: {response.text}")
        
except Exception as e:
    print(f"❌ Error checking deliverables: {e}")

# Check tasks status
try:
    response = requests.get(f"{API_BASE}/workspaces/{workspace_id}/tasks")
    if response.status_code == 200:
        tasks = response.json()
        completed = [t for t in tasks if t.get('status') == 'completed']
        print(f"\n📋 Task status: {len(completed)}/{len(tasks)} completed")
        for t in completed:
            print(f"  ✓ {t['name']}")
    else:
        print(f"❌ Error getting tasks: {response.text}")
except Exception as e:
    print(f"❌ Error checking tasks: {e}")