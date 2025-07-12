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
    
    print("\n🤖 Testing director proposal...")
    try:
        # Correctly build the DirectorTeamProposal payload
        proposal_payload = {
            "workspace_id": workspace_id,
            "requirements": "Test autonomous goal processing",
            "budget_limit": 100.0
        }
        response = requests.post(f"{base_url}/api/director/proposal", json=proposal_payload, timeout=30)
        print(f"Director proposal response: {response.status_code}")
        if response.status_code in [200, 201]:
            proposal = response.json()
            print(f"✅ Team proposal created: {proposal.get('id', 'No ID')}")
            
            # Approve the proposal to trigger task generation
            proposal_id = proposal.get("id")
            if proposal_id:
                print("\n✅ Approving team proposal...")
                approval_response = requests.post(f"{base_url}/api/director/approve/{workspace_id}", params={"proposal_id": proposal_id}, timeout=10)
                print(f"Approval response: {approval_response.status_code}")
                assert approval_response.status_code in [200, 204], "Proposal approval failed"
                print("✅ Team proposal approved!")
        else:
            print(f"❌ Director proposal failed: {response.text}")
            assert False, "Director proposal failed"
    except Exception as e:
        print(f"❌ Director proposal error: {e}")
        assert False, f"Director proposal error: {e}"
    
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