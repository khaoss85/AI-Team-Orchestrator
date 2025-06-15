#!/usr/bin/env python3
"""
Simple monitor for the last created workspace
"""
import urllib.request
import json
import sys

def check_workspace(workspace_id):
    """Check workspace status"""
    BASE_URL = "http://localhost:8000"
    
    try:
        # Check goals
        url = f"{BASE_URL}/api/workspaces/{workspace_id}/goals"
        with urllib.request.urlopen(url) as response:
            goals = json.loads(response.read().decode('utf-8'))
            print(f"✅ Workspace {workspace_id} is active!")
            print(f"   Goals: {goals['total_goals']}")
            for goal in goals['goals'][:3]:
                print(f"   - {goal['description']} ({goal['target_value']} {goal['unit']})")
        
        # Check tasks
        url = f"{BASE_URL}/tasks/?workspace_id={workspace_id}"
        with urllib.request.urlopen(url) as response:
            tasks = json.loads(response.read().decode('utf-8'))
            print(f"\n   Tasks: {len(tasks)}")
            
        # Check agents
        url = f"{BASE_URL}/agents/{workspace_id}"
        with urllib.request.urlopen(url) as response:
            agents = json.loads(response.read().decode('utf-8'))
            print(f"   Agents: {len(agents)}")
            
        print(f"\n🔗 Frontend: http://localhost:3000/projects/{workspace_id}")
        
    except Exception as e:
        print(f"❌ Error checking workspace: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        workspace_id = sys.argv[1]
    else:
        # Try to find a recent workspace
        print("Usage: python3 monitor_e2e_simple.py <workspace_id>")
        sys.exit(1)
    
    check_workspace(workspace_id)