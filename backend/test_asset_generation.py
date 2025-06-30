#!/usr/bin/env python3
"""
🔍 Test specifico per Asset Requirements Generation
"""

import requests
import json
import time
import uuid

BASE_URL = "http://localhost:8000"

def test_goal_creation_and_asset_generation():
    """Test the complete goal → asset requirements flow"""
    
    print("🚀 TESTING GOAL → ASSET REQUIREMENTS GENERATION")
    print("=" * 60)
    
    # Step 1: Create workspace
    workspace_data = {
        "name": f"Asset Generation Test {int(time.time())}",
        "description": "Test automatic asset requirements generation",
        "status": "active",
        "user_id": str(uuid.uuid4())
    }
    
    print("📋 Creating workspace...")
    response = requests.post(f"{BASE_URL}/workspaces/", json=workspace_data)
    if response.status_code != 201:
        print(f"❌ Failed to create workspace: {response.status_code} - {response.text}")
        return
    
    workspace = response.json()
    workspace_id = workspace["id"]
    print(f"✅ Created workspace: {workspace_id}")
    
    # Step 2: Create goal with asset generation
    goal_data = {
        "workspace_id": workspace_id,
        "metric_type": "api_documentation",
        "target_value": 100.0,
        "current_value": 0.0,
        "description": "Create comprehensive REST API documentation with examples, authentication guide, and deployment instructions",
        "measurement_unit": "percentage",
        "goal_category": "documentation"
    }
    
    print("\n🎯 Creating goal with automatic asset generation...")
    response = requests.post(f"{BASE_URL}/api/workspaces/{workspace_id}/goals", json=goal_data)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code != 200:
        print(f"❌ Failed to create goal: {response.status_code} - {response.text}")
        return
    
    goal_response = response.json()
    goal_id = goal_response.get("goal", {}).get("id") if "goal" in goal_response else goal_response.get("id")
    asset_requirements_count = goal_response.get("asset_requirements_count", 0)
    
    print(f"✅ Goal created: {goal_id}")
    print(f"📦 Asset requirements generated: {asset_requirements_count}")
    
    # Step 3: Check asset requirements via API
    print("\n🔍 Checking asset requirements via API...")
    
    # Wait a moment for async processing
    time.sleep(2)
    
    response = requests.get(f"{BASE_URL}/api/assets/requirements/workspace/{workspace_id}")
    print(f"Asset requirements API status: {response.status_code}")
    
    if response.status_code == 200:
        requirements = response.json()
        print(f"📋 Found {len(requirements)} asset requirements:")
        for req in requirements:
            print(f"  • {req.get('asset_name', 'Unknown')} ({req.get('asset_type', 'Unknown type')})")
    else:
        print(f"❌ Failed to get asset requirements: {response.text}")
    
    # Step 4: Test workspace asset status
    print("\n📊 Checking workspace asset status...")
    response = requests.get(f"{BASE_URL}/api/assets/workspace/{workspace_id}/status")
    print(f"Workspace status API: {response.status_code}")
    
    if response.status_code == 200:
        status = response.json()
        print(f"Asset status: {json.dumps(status, indent=2)}")
    else:
        print(f"❌ Failed to get workspace status: {response.text}")
    
    # Step 5: Test goal completion endpoint
    print("\n🎯 Checking goal completion data...")
    response = requests.get(f"{BASE_URL}/api/assets/goals/{workspace_id}/completion")
    print(f"Goal completion API: {response.status_code}")
    
    if response.status_code == 200:
        completion = response.json()
        print(f"Goal completion: {json.dumps(completion, indent=2)}")
    else:
        print(f"❌ Failed to get goal completion: {response.text}")
    
    print("\n" + "=" * 60)
    print("🏁 ASSET GENERATION TEST COMPLETED")

if __name__ == "__main__":
    test_goal_creation_and_asset_generation()