#!/usr/bin/env python3
"""
Test script to verify workspace team creation status
"""
import requests
import json
from datetime import datetime

WORKSPACE_ID = "acd598e4-587a-4a25-83f4-fd37e0878e0a"
BASE_URL = "http://localhost:8000/api"

def check_workspace_status():
    """Check comprehensive workspace status"""
    
    print("=" * 60)
    print("WORKSPACE TEAM CREATION STATUS CHECK")
    print("=" * 60)
    print(f"Workspace ID: {WORKSPACE_ID}")
    print(f"Check time: {datetime.now()}")
    print("-" * 60)
    
    # 1. Check workspace
    try:
        resp = requests.get(f"{BASE_URL}/workspaces/{WORKSPACE_ID}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"\n✅ Workspace found:")
            print(f"   Name: {data.get('name')}")
            print(f"   Status: {data.get('status')}")
            print(f"   Created: {data.get('created_at')}")
        else:
            print(f"\n❌ Workspace not found: {resp.status_code}")
            return
    except Exception as e:
        print(f"\n❌ Error fetching workspace: {e}")
        return
    
    # 2. Check agents/team
    try:
        resp = requests.get(f"{BASE_URL}/agents/{WORKSPACE_ID}")
        if resp.status_code == 200:
            agents = resp.json()
            if agents:
                print(f"\n✅ Team created with {len(agents)} agents:")
                for agent in agents:
                    print(f"   - {agent['name']} ({agent['role']}) - {agent['seniority']} - Status: {agent['status']}")
            else:
                print(f"\n❌ NO TEAM CREATED - Empty agent list")
        else:
            print(f"\n❌ Error fetching team: {resp.status_code}")
    except Exception as e:
        print(f"\n❌ Error fetching agents: {e}")
    
    # 3. Check tasks
    try:
        resp = requests.get(f"{BASE_URL}/workspaces/{WORKSPACE_ID}/tasks")
        if resp.status_code == 200:
            tasks = resp.json()
            status_counts = {}
            for task in tasks:
                status = task.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            print(f"\n📋 Tasks status ({len(tasks)} total):")
            for status, count in status_counts.items():
                print(f"   {status}: {count}")
        else:
            print(f"\n❌ Error fetching tasks: {resp.status_code}")
    except Exception as e:
        print(f"\n❌ Error fetching tasks: {e}")
    
    # 4. Check deliverables
    try:
        resp = requests.get(f"{BASE_URL}/deliverables/workspace/{WORKSPACE_ID}")
        if resp.status_code == 200:
            deliverables = resp.json()
            print(f"\n📦 Deliverables: {len(deliverables)} created")
            if deliverables:
                for d in deliverables[:3]:  # Show first 3
                    print(f"   - {d['title'][:50]}... (Status: {d['status']})")
        else:
            print(f"\n❌ Error fetching deliverables: {resp.status_code}")
    except Exception as e:
        print(f"\n❌ Error fetching deliverables: {e}")
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS:")
    print("-" * 60)
    
    # Diagnosis
    try:
        resp = requests.get(f"{BASE_URL}/agents/{WORKSPACE_ID}")
        agents = resp.json() if resp.status_code == 200 else []
        
        if not agents:
            print("🚨 ISSUE CONFIRMED: No team created for this workspace")
            print("\nPossible causes:")
            print("1. Team proposal was never approved")
            print("2. Agent creation failed during approval")
            print("3. SDK parameter filtering blocked agent creation")
            print("4. Database constraint violations")
        else:
            print("✅ Team creation successful - No regression detected")
            print(f"   {len(agents)} agents created and active")
            
            # Check if tasks are being generated
            resp = requests.get(f"{BASE_URL}/workspaces/{WORKSPACE_ID}/tasks")
            tasks = resp.json() if resp.status_code == 200 else []
            if tasks:
                print(f"   {len(tasks)} tasks generated")
                print("\n🎯 System is working correctly!")
            else:
                print("   ⚠️ No tasks generated yet - may need time")
    except Exception as e:
        print(f"❌ Diagnosis error: {e}")

if __name__ == "__main__":
    check_workspace_status()