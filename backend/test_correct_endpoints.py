#!/usr/bin/env python3
"""
Test con gli endpoint corretti per agents e deliverables
"""

import asyncio
import requests
import json
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

async def test_correct_endpoints():
    """Test con gli endpoint corretti"""
    
    logger.info("🔍 Testing correct endpoints")
    
    # Phase 1: Create workspace
    logger.info("📁 Phase 1: Creating workspace...")
    workspace_response = requests.post(f"{BASE_URL}/workspaces", json={
        "name": "Correct Endpoints Test",
        "description": "Testing correct endpoint URLs"
    }, timeout=10)
    
    if workspace_response.status_code not in [200, 201]:
        logger.error(f"❌ Workspace creation failed: {workspace_response.status_code}")
        return False
    
    workspace_id = workspace_response.json()["id"]
    logger.info(f"✅ Workspace created: {workspace_id}")
    
    # Phase 2: Director proposal and approval
    logger.info("🤖 Phase 2: Director proposal and approval...")
    proposal_payload = {
        "workspace_id": workspace_id,
        "project_description": "Test project for endpoint validation",
        "project_goals": ["Test goal 1", "Test goal 2"]
    }
    
    # Create proposal
    response = requests.post(f"{API_BASE}/director/proposal", json=proposal_payload, timeout=30)
    if response.status_code != 200:
        logger.error(f"❌ Director proposal failed: {response.status_code}")
        return False
    
    proposal = response.json()
    proposal_id = proposal.get("proposal_id")
    logger.info(f"✅ Director proposal successful: {proposal_id}")
    
    # Approve proposal
    approval_response = requests.post(f"{API_BASE}/director/approve/{workspace_id}", 
                                    params={"proposal_id": proposal_id}, timeout=30)
    if approval_response.status_code not in [200, 204]:
        logger.error(f"❌ Proposal approval failed: {approval_response.status_code}")
        return False
    
    approval_data = approval_response.json()
    logger.info(f"✅ Proposal approved - {len(approval_data.get('created_agent_ids', []))} agents created")
    
    # Phase 3: Test CORRECT agents endpoint
    logger.info("👥 Phase 3: Testing CORRECT agents endpoint...")
    
    # Correct endpoint: /agents/{workspace_id}
    agents_response = requests.get(f"{BASE_URL}/agents/{workspace_id}", timeout=10)
    if agents_response.status_code == 200:
        agents = agents_response.json()
        logger.info(f"✅ CORRECT agents endpoint works: Found {len(agents)} agents")
        
        for agent in agents:
            logger.info(f"  - {agent.get('name', 'Unknown')} ({agent.get('role', 'Unknown')}) - Status: {agent.get('status', 'Unknown')}")
    else:
        logger.error(f"❌ CORRECT agents endpoint failed: {agents_response.status_code} - {agents_response.text}")
    
    # Phase 4: Test CORRECT deliverables endpoint
    logger.info("📦 Phase 4: Testing CORRECT deliverables endpoint...")
    
    # Wait for potential deliverables to be created
    time.sleep(10)
    
    # Correct endpoint: /api/deliverables/workspace/{workspace_id}
    deliverables_response = requests.get(f"{API_BASE}/deliverables/workspace/{workspace_id}", timeout=10)
    if deliverables_response.status_code == 200:
        deliverables = deliverables_response.json()
        logger.info(f"✅ CORRECT deliverables endpoint works: Found {len(deliverables)} deliverables")
        
        for deliverable in deliverables:
            logger.info(f"  - {deliverable.get('name', 'Unknown')} - Status: {deliverable.get('status', 'Unknown')}")
    else:
        logger.error(f"❌ CORRECT deliverables endpoint failed: {deliverables_response.status_code} - {deliverables_response.text}")
    
    # Phase 5: Test tasks endpoint (this one should work)
    logger.info("📋 Phase 5: Testing tasks endpoint...")
    
    # Wait for tasks to be created
    time.sleep(30)
    
    tasks_response = requests.get(f"{API_BASE}/workspaces/{workspace_id}/tasks", timeout=10)
    if tasks_response.status_code == 200:
        tasks = tasks_response.json()
        logger.info(f"✅ Tasks endpoint works: Found {len(tasks)} tasks")
        
        for task in tasks:
            logger.info(f"  - {task.get('name', 'Unknown')} - Status: {task.get('status', 'Unknown')}")
    else:
        logger.error(f"❌ Tasks endpoint failed: {tasks_response.status_code} - {tasks_response.text}")
    
    logger.info("🔍 Correct endpoints test completed")
    return True

if __name__ == "__main__":
    asyncio.run(test_correct_endpoints())