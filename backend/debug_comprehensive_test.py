#!/usr/bin/env python3
"""
Debug test per capire dove si blocca comprehensive_e2e_test.py
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

async def debug_comprehensive_flow():
    """Debug del flusso comprehensive step by step"""
    
    logger.info("🔍 Starting comprehensive test debugging")
    
    # Phase 1: Create workspace
    logger.info("📁 Phase 1: Creating workspace...")
    workspace_response = requests.post(f"{BASE_URL}/workspaces", json={
        "name": "Debug Test Workspace",
        "description": "Debug workspace for comprehensive test"
    }, timeout=10)
    
    if workspace_response.status_code not in [200, 201]:
        logger.error(f"❌ Workspace creation failed: {workspace_response.status_code}")
        return False
    
    workspace_id = workspace_response.json()["id"]
    logger.info(f"✅ Workspace created: {workspace_id}")
    
    # Phase 2: Create goals
    logger.info("🎯 Phase 2: Creating goals...")
    goals_data = [
        {
            "name": "Feature Completion",
            "description": "Complete all core features",
            "metric_type": "completion",
            "target_value": 100.0,
            "workspace_id": workspace_id
        },
        {
            "name": "Quality Assurance",
            "description": "Ensure high quality standards",
            "metric_type": "quality",
            "target_value": 95.0,
            "workspace_id": workspace_id
        }
    ]
    
    goal_ids = []
    for goal_data in goals_data:
        try:
            goal_response = requests.post(f"{BASE_URL}/workspaces/{workspace_id}/goals", json=goal_data, timeout=10)
            if goal_response.status_code in [200, 201]:
                goal_info = goal_response.json()
                goal_id = goal_info.get("goal", {}).get("id") or goal_info.get("id")
                goal_ids.append(goal_id)
                logger.info(f"✅ Goal created: {goal_id}")
            else:
                logger.error(f"❌ Goal creation failed: {goal_response.status_code} - {goal_response.text}")
        except Exception as e:
            logger.error(f"❌ Goal creation error: {e}")
    
    # Phase 3: Director proposal
    logger.info("🤖 Phase 3: Testing director proposal...")
    proposal_payload = {
        "workspace_id": workspace_id,
        "project_description": "Build a comprehensive content management system",
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
            
            # Phase 4: Test proposal approval
            logger.info("✅ Phase 4: Testing proposal approval...")
            if proposal_id:
                approval_response = requests.post(f"{API_BASE}/director/approve/{workspace_id}", 
                                                params={"proposal_id": proposal_id}, timeout=30)
                logger.info(f"📡 Approval response: {approval_response.status_code}")
                
                if approval_response.status_code in [200, 204]:
                    logger.info("✅ Proposal approved successfully")
                else:
                    logger.error(f"❌ Proposal approval failed: {approval_response.status_code} - {approval_response.text}")
            
        else:
            logger.error(f"❌ Director proposal failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Director proposal error: {e}")
    
    # Phase 5: Check task creation
    logger.info("📋 Phase 5: Checking task creation...")
    try:
        # Wait a bit for task creation
        time.sleep(5)
        
        tasks_response = requests.get(f"{API_BASE}/workspaces/{workspace_id}/tasks", timeout=10)
        if tasks_response.status_code == 200:
            tasks = tasks_response.json()
            logger.info(f"✅ Found {len(tasks)} tasks in workspace")
            
            for task in tasks:
                logger.info(f"📝 Task: {task.get('name', 'Unknown')} - Status: {task.get('status', 'Unknown')}")
                
        else:
            logger.error(f"❌ Task retrieval failed: {tasks_response.status_code}")
            
    except Exception as e:
        logger.error(f"❌ Task retrieval error: {e}")
    
    # Phase 6: Test deliverables
    logger.info("📦 Phase 6: Testing deliverables...")
    try:
        deliverables_response = requests.get(f"{BASE_URL}/workspaces/{workspace_id}/deliverables", timeout=10)
        if deliverables_response.status_code == 200:
            deliverables = deliverables_response.json()
            logger.info(f"✅ Found {len(deliverables)} deliverables in workspace")
        else:
            logger.error(f"❌ Deliverables retrieval failed: {deliverables_response.status_code} - {deliverables_response.text}")
    except Exception as e:
        logger.error(f"❌ Deliverables retrieval error: {e}")
    
    logger.info("🔍 Debug test completed")
    return True

if __name__ == "__main__":
    asyncio.run(debug_comprehensive_flow())