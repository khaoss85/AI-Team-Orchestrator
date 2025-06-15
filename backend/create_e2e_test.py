#!/usr/bin/env python3
"""
Create and monitor E2E test project
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

def create_test_project():
    """Create the E2E test project"""
    project_data = {
        "name": f"Test E2E - ICP Contacts SaaS Europe {datetime.now().strftime('%H:%M')}",
        "description": "Raccogliere 50 contatti ICP (CMO/CTO di aziende SaaS europee) e suggerire almeno 3 sequenze email da impostare su Hubspot",
        "status": "planning"
    }
    
    print("🚀 Creating E2E test project...")
    response = requests.post(f"{BASE_URL}/workspaces", json=project_data)
    
    if response.status_code == 200:
        project = response.json()
        print(f"✅ Project created successfully!")
        print(f"   ID: {project['id']}")
        print(f"   Name: {project['name']}")
        print(f"   Status: {project['status']}")
        return project['id']
    else:
        print(f"❌ Failed to create project: {response.status_code}")
        print(response.text)
        return None

def monitor_project(workspace_id):
    """Monitor project progress"""
    print(f"\n📊 Monitoring project {workspace_id}...")
    
    # Wait for initial processing
    print("\n⏳ Waiting for AI processing...")
    time.sleep(5)
    
    # Check goals
    print("\n🎯 Checking extracted goals...")
    goals_response = requests.get(f"{BASE_URL}/workspaces/{workspace_id}/goals")
    if goals_response.status_code == 200:
        goals_data = goals_response.json()
        print(f"   Total goals extracted: {goals_data['total_goals']}")
        for goal in goals_data['goals']:
            print(f"   - {goal['description']}")
            print(f"     Target: {goal['target_value']} {goal['unit']}")
            print(f"     Type: {goal['goal_type']} | Metric: {goal['metric_type']}")
    
    # Check agents
    print("\n👥 Checking AI-selected agents...")
    agents_response = requests.get(f"{BASE_URL}/workspaces/{workspace_id}/agents")
    if agents_response.status_code == 200:
        agents = agents_response.json()
        print(f"   Total agents: {len(agents)}")
        for agent in agents[:5]:  # Show first 5
            print(f"   - {agent['role']} ({agent['seniority']}) - {agent['status']}")
    
    # Check tasks
    print("\n📋 Checking AI-generated tasks...")
    tasks_response = requests.get(f"{BASE_URL}/workspaces/{workspace_id}/tasks")
    if tasks_response.status_code == 200:
        tasks = tasks_response.json()
        print(f"   Total tasks: {len(tasks)}")
        
        # Group by status
        by_status = {}
        for task in tasks:
            status = task['status']
            by_status[status] = by_status.get(status, 0) + 1
            
        print(f"   Status breakdown:")
        for status, count in by_status.items():
            print(f"     - {status}: {count}")
        
        print(f"\n   First 5 tasks:")
        for task in tasks[:5]:
            print(f"   - [{task['status']}] {task['name']}")
            if task.get('assigned_to'):
                print(f"     Assigned to: Agent {task['assigned_to']}")
            elif task.get('assigned_to_role'):
                print(f"     Assigned to role: {task['assigned_to_role']}")
    
    # Check memory insights
    print("\n🧠 Checking memory insights...")
    memory_response = requests.get(f"{BASE_URL}/workspaces/{workspace_id}/memory")
    if memory_response.status_code == 200:
        memory_data = memory_response.json()
        print(f"   Total insights: {memory_data.get('total_insights', 0)}")
        if 'insights' in memory_data:
            for insight in memory_data['insights'][:3]:  # Show first 3
                print(f"   - [{insight['insight_type']}] {insight['content'][:100]}...")
    
    print(f"\n🔗 Frontend URL: http://localhost:3000/projects/{workspace_id}")
    print(f"   Open this URL to see the visual progress!")

def main():
    workspace_id = create_test_project()
    if workspace_id:
        monitor_project(workspace_id)
        
        print("\n\n📊 Continuing to monitor... Press Ctrl+C to stop")
        print("=" * 60)
        
        # Continue monitoring every 30 seconds
        try:
            while True:
                time.sleep(30)
                print(f"\n⏰ Update at {datetime.now().strftime('%H:%M:%S')}")
                monitor_project(workspace_id)
                print("=" * 60)
        except KeyboardInterrupt:
            print("\n\n✅ Monitoring stopped")

if __name__ == "__main__":
    main()