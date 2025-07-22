#!/usr/bin/env python3
"""
Debug approval flow per capire perché non vengono creati i task
"""

import asyncio
import requests
import json
import time
import logging
from datetime import datetime
from uuid import uuid4

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

async def debug_approval_flow():
    """Debug del flusso di approval step by step"""
    
    logger.info("🔍 Starting approval flow debugging")
    
    # Phase 1: Create workspace
    logger.info("📁 Phase 1: Creating workspace...")
    workspace_response = requests.post(f"{BASE_URL}/workspaces", json={
        "name": "Debug Approval Test",
        "description": "Debug workspace for approval flow"
    }, timeout=10)
    
    if workspace_response.status_code not in [200, 201]:
        logger.error(f"❌ Workspace creation failed: {workspace_response.status_code}")
        return False
    
    workspace_id = workspace_response.json()["id"]
    logger.info(f"✅ Workspace created: {workspace_id}")
    
    # Phase 2: Director proposal
    logger.info("🤖 Phase 2: Creating director proposal...")
    proposal_payload = {
        "workspace_id": workspace_id,
        "project_description": "Build a comprehensive content management system with AI features",
        "project_goals": ["Complete all core features", "Ensure high quality standards"]
    }
    
    try:
        logger.info("⏳ Sending director proposal request...")
        response = requests.post(f"{API_BASE}/director/proposal", json=proposal_payload, timeout=30)
        logger.info(f"📡 Director proposal response: {response.status_code}")
        
        if response.status_code == 200:
            proposal = response.json()
            proposal_id = proposal.get("proposal_id")
            logger.info(f"✅ Director proposal successful: {proposal_id}")
            
            # Show proposal details
            if "agents" in proposal:
                logger.info(f"👥 Proposed agents: {len(proposal['agents'])}")
                for agent in proposal["agents"]:
                    logger.info(f"  - {agent.get('name', 'Unknown')} ({agent.get('role', 'Unknown')})")
            
            # Phase 3: Approval with detailed logging
            logger.info("✅ Phase 3: Approving proposal...")
            if proposal_id:
                approval_url = f"{API_BASE}/director/approve/{workspace_id}"
                approval_params = {"proposal_id": proposal_id}
                
                logger.info(f"📡 Approval URL: {approval_url}")
                logger.info(f"📡 Approval params: {approval_params}")
                
                approval_response = requests.post(approval_url, params=approval_params, timeout=60)
                logger.info(f"📡 Approval response: {approval_response.status_code}")
                
                if approval_response.status_code in [200, 204]:
                    approval_data = approval_response.json() if approval_response.text else {}
                    logger.info(f"✅ Proposal approved successfully: {approval_data}")
                    
                    # Phase 4: Check agents created
                    logger.info("👥 Phase 4: Checking agents created...")
                    time.sleep(2)  # Give time for agent creation
                    
                    agents_response = requests.get(f"{BASE_URL}/workspaces/{workspace_id}/agents", timeout=10)
                    if agents_response.status_code == 200:
                        agents = agents_response.json()
                        logger.info(f"✅ Found {len(agents)} agents in workspace")
                        
                        for agent in agents:
                            logger.info(f"  - {agent.get('name', 'Unknown')} ({agent.get('role', 'Unknown')}) - Status: {agent.get('status', 'Unknown')}")
                    else:
                        logger.error(f"❌ Agents retrieval failed: {agents_response.status_code}")
                    
                    # Phase 5: Check task creation over time
                    logger.info("📋 Phase 5: Monitoring task creation...")
                    
                    for i in range(12):  # Check every 5 seconds for 60 seconds
                        time.sleep(5)
                        
                        tasks_response = requests.get(f"{API_BASE}/workspaces/{workspace_id}/tasks", timeout=10)
                        if tasks_response.status_code == 200:
                            tasks = tasks_response.json()
                            logger.info(f"📝 After {(i+1)*5}s: Found {len(tasks)} tasks")
                            
                            if len(tasks) > 0:
                                logger.info("✅ Tasks found! Breaking monitoring loop")
                                for task in tasks:
                                    logger.info(f"  - {task.get('name', 'Unknown')} - Status: {task.get('status', 'Unknown')}")
                                break
                        else:
                            logger.error(f"❌ Task retrieval failed: {tasks_response.status_code}")
                    
                    # Final task check
                    tasks_response = requests.get(f"{API_BASE}/workspaces/{workspace_id}/tasks", timeout=10)
                    if tasks_response.status_code == 200:
                        tasks = tasks_response.json()
                        logger.info(f"🏁 Final task count: {len(tasks)}")
                        
                        if len(tasks) == 0:
                            logger.error("❌ NO TASKS CREATED after approval!")
                            logger.error("This indicates a problem in the approval->task creation flow")
                        else:
                            logger.info("✅ Tasks successfully created after approval")
                    
                else:
                    logger.error(f"❌ Proposal approval failed: {approval_response.status_code} - {approval_response.text}")
                    
        else:
            logger.error(f"❌ Director proposal failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Error during approval flow: {e}")
    
    logger.info("🔍 Debug approval flow completed")
    return True

if __name__ == "__main__":
    asyncio.run(debug_approval_flow())