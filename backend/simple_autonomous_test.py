#!/usr/bin/env python3
"""
🚀 SIMPLE AUTONOMOUS TEST
================================================================================
Test semplificato per verificare il flusso base del sistema autonomo
"""

import requests
import time
import json
from datetime import datetime

def test_basic_flow():
    """Test basic autonomous flow"""
    base_url = "http://localhost:8000"
    
    # Check server
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✅ Server health: {response.status_code}")
    except Exception as e:
        print(f"❌ Server not responding: {e}")
        return False
    
    # Create workspace
    print("\n📝 Creating workspace...")
    workspace_data = {
        "name": "Test Autonomous Workspace",
        "description": "Test workspace for autonomous flow",
        "domain": "test",
        "goal": "Test autonomous goal processing"
    }
    
    try:
        response = requests.post(f"{base_url}/workspaces", json=workspace_data, timeout=10)
        print(f"Workspace response: {response.status_code}")
        if response.status_code in [200, 201]:
            workspace = response.json()
            workspace_id = workspace.get('id')
            print(f"✅ Workspace created: {workspace_id}")
        else:
            print(f"❌ Workspace creation failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Workspace creation error: {e}")
        return False
    
    # Create goal
    print("\n🎯 Creating goal...")
    goal_data = {
        "workspace_id": workspace_id,
        "description": "Test goal for autonomous processing",
        "metric_type": "deliverables",
        "target_value": 1.0,
        "unit": "test_components"
    }
    
    try:
        response = requests.post(f"{base_url}/api/workspaces/{workspace_id}/goals", json=goal_data, timeout=10)
        print(f"Goal response: {response.status_code}")
        if response.status_code in [200, 201]:
            goal = response.json()
            goal_id = goal.get('id')
            print(f"✅ Goal created: {goal_id}")
        else:
            print(f"❌ Goal creation failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Goal creation error: {e}")
        return False
    
    # Test director proposal creation
    print("\n🤖 Testing director proposal...")
    try:
        response = requests.post(f"{base_url}/director/proposal", json={"workspace_id": workspace_id}, timeout=30)
        print(f"Director proposal response: {response.status_code}")
        if response.status_code in [200, 201]:
            proposal = response.json()
            print(f"✅ Team proposal created: {proposal.get('id', 'No ID')}")
            
            # Check if we can retrieve proposals
            time.sleep(2)
            response = requests.get(f"{base_url}/director/proposals?workspace_id={workspace_id}", timeout=10)
            print(f"Proposals lookup response: {response.status_code}")
            if response.status_code == 200:
                proposals = response.json()
                print(f"✅ Found {len(proposals)} proposals")
                if len(proposals) > 0:
                    proposal_id = proposals[0].get('id')
                    print(f"✅ Proposal ID: {proposal_id}")
                    
                    # Try to approve the proposal
                    print("\n✅ Approving team proposal...")
                    approval_response = requests.post(f"{base_url}/proposals/{proposal_id}/approve", timeout=10)
                    print(f"Approval response: {approval_response.status_code}")
                    if approval_response.status_code in [200, 204]:
                        print("✅ Team proposal approved!")
                    else:
                        print(f"⚠️ Approval returned: {approval_response.text}")
            else:
                print(f"❌ Proposals lookup failed: {response.text}")
        else:
            print(f"❌ Director proposal failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Director proposal error: {e}")
        return False
    
    # Check for task generation
    print("\n📋 Checking for task generation...")
    for i in range(6):  # Wait up to 30 seconds
        try:
            response = requests.get(f"{base_url}/workspaces/{workspace_id}/tasks", timeout=10)
            if response.status_code == 200:
                tasks = response.json()
                goal_tasks = [t for t in tasks if t.get('goal_id') == goal_id]
                if len(goal_tasks) > 0:
                    print(f"✅ Found {len(goal_tasks)} goal-driven tasks!")
                    for task in goal_tasks[:3]:
                        print(f"   - {task.get('name', 'Unnamed')}")
                    break
                else:
                    print(f"   ⏳ No goal tasks yet, waiting... ({i*5}s)")
            else:
                print(f"   ⚠️ Task check failed: {response.status_code}")
        except Exception as e:
            print(f"   ⚠️ Task check error: {e}")
        
        time.sleep(5)
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    try:
        response = requests.delete(f"{base_url}/workspaces/{workspace_id}", timeout=10)
        print(f"Cleanup response: {response.status_code}")
    except:
        pass
    
    print("\n🏁 Simple autonomous test completed!")
    return True

if __name__ == "__main__":
    success = test_basic_flow()
    exit(0 if success else 1)