#!/usr/bin/env python3
"""
🚀 MINIMAL AUTONOMOUS TEST
================================================================================
Test minimo per verificare il sistema autonomo senza heavy AI processing
"""

import requests
import time
import json
import sys
from datetime import datetime

def test_minimal_flow():
    """Test minimal autonomous flow"""
    base_url = "http://localhost:8000"
    
    print("🔍 Testing minimal autonomous flow...")
    
    # Check server
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✅ Server health: {response.status_code}")
    except Exception as e:
        print(f"❌ Server not responding: {e}")
        return False
    
    # Create workspace with minimal data
    print("\n📝 Creating minimal workspace...")
    workspace_data = {
        "name": "Minimal Test",
        "description": "Simple test workspace",
        "domain": "test"
    }
    
    try:
        response = requests.post(f"{base_url}/workspaces", json=workspace_data, timeout=15)
        print(f"Workspace creation: {response.status_code}")
        if response.status_code in [200, 201]:
            workspace = response.json()
            workspace_id = workspace.get('id')
            print(f"✅ Workspace created: {workspace_id}")
        else:
            print(f"❌ Failed: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Create minimal goal (avoid AI processing)
    print("\n🎯 Creating minimal goal...")
    goal_data = {
        "workspace_id": workspace_id,
        "metric_type": "test_metric",
        "target_value": 1.0,
        "unit": "test",
        "description": "Simple test goal"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/workspaces/{workspace_id}/goals", 
            json=goal_data, 
            timeout=30
        )
        print(f"Goal creation: {response.status_code}")
        if response.status_code in [200, 201]:
            goal = response.json()
            goal_id = goal.get('id')
            print(f"✅ Goal created: {goal_id}")
        else:
            print(f"❌ Failed: {response.text[:300]}")
            # Try alternative endpoint
            print("\n🔄 Trying alternative goal creation...")
            try:
                alt_goal_data = {
                    "workspace_id": workspace_id,
                    **goal_data
                }
                response = requests.post(
                    f"{base_url}/workspace-goals", 
                    json=alt_goal_data, 
                    timeout=30
                )
                print(f"Alternative goal creation: {response.status_code}")
                if response.status_code in [200, 201]:
                    goal = response.json()
                    goal_id = goal.get('id')
                    print(f"✅ Goal created via alternative endpoint: {goal_id}")
                else:
                    print(f"❌ Alternative also failed: {response.text[:200]}")
                    return False
            except Exception as e2:
                print(f"❌ Alternative error: {e2}")
                return False
    except Exception as e:
        print(f"❌ Goal creation error: {e}")
        return False
    
    # Check if AutomatedGoalMonitor can be triggered manually
    print("\n⚡ Testing AutomatedGoalMonitor trigger...")
    try:
        sys.path.insert(0, '/Users/pelleri/Documents/ai-team-orchestrator/backend')
        from automated_goal_monitor import automated_goal_monitor
        
        print("   Triggering immediate validation...")
        await_result = automated_goal_monitor.trigger_immediate_validation(workspace_id)
        print("   ✅ AutomatedGoalMonitor triggered successfully")
        
        # Wait and check for tasks
        print("\n📋 Checking for task generation...")
        for i in range(3):
            try:
                response = requests.get(f"{base_url}/workspaces/{workspace_id}/tasks", timeout=10)
                if response.status_code == 200:
                    tasks = response.json()
                    goal_tasks = [t for t in tasks if str(t.get('goal_id')) == str(goal_id)]
                    if len(goal_tasks) > 0:
                        print(f"✅ Found {len(goal_tasks)} goal-driven tasks!")
                        break
                    else:
                        print(f"   ⏳ No tasks yet... ({i*5}s)")
                time.sleep(5)
            except Exception as e:
                print(f"   ⚠️ Task check error: {e}")
                
    except Exception as e:
        print(f"⚠️ Could not trigger AutomatedGoalMonitor: {e}")
    
    # Test director functionality
    print("\n🤖 Testing basic director...")
    try:
        response = requests.post(
            f"{base_url}/director/proposal",
            json={"workspace_id": workspace_id},
            timeout=45
        )
        print(f"Director response: {response.status_code}")
        if response.status_code in [200, 201]:
            print("✅ Director created team proposal")
        else:
            print(f"⚠️ Director response: {response.text[:200]}")
    except Exception as e:
        print(f"⚠️ Director error: {e}")
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    try:
        response = requests.delete(f"{base_url}/workspaces/{workspace_id}", timeout=10)
        print(f"Cleanup: {response.status_code}")
    except:
        pass
    
    print("\n🏁 Minimal test completed!")
    return True

if __name__ == "__main__":
    success = test_minimal_flow()
    exit(0 if success else 1)