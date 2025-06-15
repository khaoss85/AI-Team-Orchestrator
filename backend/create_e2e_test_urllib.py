#!/usr/bin/env python3
"""
Create and monitor E2E test project using urllib
"""
import urllib.request
import urllib.parse
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def make_request(method, endpoint, data=None):
    """Make HTTP request using urllib"""
    url = f"{BASE_URL}{endpoint}"
    headers = {'Content-Type': 'application/json'}
    
    if data:
        data = json.dumps(data).encode('utf-8')
    
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"Error: {e.code} - {e.reason}")
        return None

def create_test_project():
    """Create the E2E test project"""
    project_data = {
        "name": f"Test E2E - ICP Contacts SaaS Europe {datetime.now().strftime('%H:%M')}",
        "description": "Raccogliere 50 contatti ICP (CMO/CTO di aziende SaaS europee) e suggerire almeno 3 sequenze email da impostare su Hubspot",
        "status": "planning",
        "user_id": "test-user-e2e"
    }
    
    print("🚀 Creating E2E test project...")
    project = make_request('POST', '/workspaces/', project_data)
    
    if project:
        print(f"✅ Project created successfully!")
        print(f"   ID: {project['id']}")
        print(f"   Name: {project['name']}")
        print(f"   Status: {project['status']}")
        return project['id']
    else:
        print("❌ Failed to create project")
        return None

def monitor_project(workspace_id):
    """Monitor project progress"""
    print(f"\n📊 Monitoring project {workspace_id}...")
    
    # Check goals
    print("\n🎯 Checking extracted goals...")
    goals_data = make_request('GET', f'/api/workspaces/{workspace_id}/goals')
    if goals_data:
        print(f"   Total goals extracted: {goals_data['total_goals']}")
        for goal in goals_data['goals']:
            print(f"   - {goal['description']}")
            print(f"     Target: {goal['target_value']} {goal['unit']}")
            print(f"     Type: {goal['goal_type']} | Metric: {goal['metric_type']}")
    
    # Check agents
    print("\n👥 Checking AI-selected agents...")
    agents = make_request('GET', f'/agents/{workspace_id}')
    if agents:
        print(f"   Total agents: {len(agents)}")
        for agent in agents[:5]:  # Show first 5
            print(f"   - {agent['role']} ({agent['seniority']}) - {agent['status']}")
    
    # Check tasks
    print("\n📋 Checking AI-generated tasks...")
    tasks = make_request('GET', f'/tasks/?workspace_id={workspace_id}')
    if tasks:
        print(f"   Total tasks: {len(tasks)}")
        
        # Group by status
        by_status = {}
        for task in tasks:
            status = task['status']
            by_status[status] = by_status.get(status, 0) + 1
            
        print(f"   Status breakdown:")
        for status, count in by_status.items():
            print(f"     - {status}: {count}")
        
        print(f"\n   Sample tasks:")
        for task in tasks[:5]:
            print(f"   - [{task['status']}] {task['name']}")
            if task.get('assigned_to'):
                print(f"     Assigned to: Agent {task['assigned_to']}")
            elif task.get('assigned_to_role'):
                print(f"     Assigned to role: {task['assigned_to_role']}")
    
    # Check memory insights
    print("\n🧠 Checking memory insights...")
    memory_data = make_request('GET', f'/memory/{workspace_id}')
    if memory_data:
        print(f"   Total insights: {memory_data.get('total_insights', 0)}")
        insights = memory_data.get('insights', [])
        for insight in insights[:3]:  # Show first 3
            print(f"   - [{insight['insight_type']}] {insight['content'][:80]}...")
    
    print(f"\n🔗 Frontend URL: http://localhost:3000/projects/{workspace_id}")

def main():
    workspace_id = create_test_project()
    if workspace_id:
        # Initial wait
        print("\n⏳ Waiting for AI processing...")
        time.sleep(10)
        
        monitor_project(workspace_id)
        
        # Write workspace ID to file for reference
        with open('last_test_workspace.txt', 'w') as f:
            f.write(workspace_id)
        
        print(f"\n✅ Test project created! Workspace ID saved to last_test_workspace.txt")
        print(f"   Continue monitoring with: python3 monitor_e2e_test.py")

if __name__ == "__main__":
    main()