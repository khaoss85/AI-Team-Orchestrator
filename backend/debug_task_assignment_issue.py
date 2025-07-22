#!/usr/bin/env python3
"""
Debug script to check task assignment issue
"""

import asyncio
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

# Import database functions
import sys
import os
sys.path.append(os.path.dirname(__file__))

from database import list_tasks, list_agents

async def debug_task_assignment():
    """Debug why tasks don't have assigned agents"""
    
    logger.info("🔍 Starting task assignment debug")
    
    workspace_id = "5756d14c-6ff7-4d9e-a889-14b12bdf293c"
    
    # 1. Check agents in workspace
    logger.info("👥 1. Checking agents in workspace...")
    try:
        agents = await list_agents(workspace_id)
        logger.info(f"✅ Found {len(agents)} agents in workspace")
        
        for i, agent in enumerate(agents):
            logger.info(f"  {i+1}. {agent.get('name', 'Unknown')} (ID: {agent.get('id')})")
            logger.info(f"     Role: {agent.get('role', 'Unknown')}")
            logger.info(f"     Status: {agent.get('status', 'Unknown')}")
            logger.info(f"     Available: {agent.get('available', 'Unknown')}")
            
    except Exception as e:
        logger.error(f"❌ Error listing agents: {e}")
        return False
    
    # 2. Check executor status via correct endpoint
    logger.info("🤖 2. Checking executor status via correct endpoint...")
    try:
        executor_response = requests.get(f"{API_BASE}/monitoring/executor/status", timeout=10)
        if executor_response.status_code == 200:
            executor_status = executor_response.json()
            logger.info(f"✅ Executor status: {json.dumps(executor_status, indent=2)}")
        else:
            logger.error(f"❌ Executor status failed: {executor_response.status_code}")
            logger.error(f"Response: {executor_response.text}")
            
    except Exception as e:
        logger.error(f"❌ Error checking executor status: {e}")
    
    # 3. Check task details
    logger.info("📋 3. Checking task assignment details...")
    try:
        tasks = await list_tasks(workspace_id)
        for task in tasks:
            task_id = task.get('id')
            task_name = task.get('name', 'Unknown')
            assigned_to = task.get('assigned_to')
            agent_id = task.get('agent_id')  # Alternative field name
            status = task.get('status')
            
            logger.info(f"📝 Task: {task_name}")
            logger.info(f"   ID: {task_id}")
            logger.info(f"   Status: {status}")
            logger.info(f"   assigned_to: {assigned_to}")
            logger.info(f"   agent_id: {agent_id}")
            
            # Check all fields for debugging
            logger.info(f"   All fields: {list(task.keys())}")
            
    except Exception as e:
        logger.error(f"❌ Error checking task details: {e}")
    
    # 4. Check if agents endpoint works
    logger.info("🌐 4. Testing agents API endpoint...")
    try:
        agents_response = requests.get(f"{BASE_URL}/agents/{workspace_id}", timeout=10)
        if agents_response.status_code == 200:
            agents_data = agents_response.json()
            logger.info(f"✅ Agents API returned {len(agents_data)} agents")
            for agent in agents_data[:3]:
                logger.info(f"   - {agent.get('name', 'Unknown')} (available: {agent.get('available', 'Unknown')})")
        else:
            logger.error(f"❌ Agents API failed: {agents_response.status_code}")
            
    except Exception as e:
        logger.error(f"❌ Error testing agents API: {e}")
    
    logger.info("🏁 Task assignment debug complete")
    return True

if __name__ == "__main__":
    result = asyncio.run(debug_task_assignment())
    if result:
        print("✅ Task assignment debug completed")
    else:
        print("❌ Task assignment debug failed")