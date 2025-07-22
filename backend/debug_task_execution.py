#!/usr/bin/env python3
"""
Debug task execution per capire perché i task non vengono eseguiti
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

async def debug_task_execution():
    """Debug del task execution flow"""
    
    logger.info("🔍 Starting task execution debugging")
    
    # Phase 1: Create workspace and get existing task
    logger.info("📁 Phase 1: Create workspace and generate task...")
    workspace_response = requests.post(f"{BASE_URL}/workspaces", json={
        "name": "Task Execution Debug",
        "description": "Debug task execution flow"
    }, timeout=10)
    
    if workspace_response.status_code not in [200, 201]:
        logger.error(f"❌ Workspace creation failed: {workspace_response.status_code}")
        return False
    
    workspace_id = workspace_response.json()["id"]
    logger.info(f"✅ Workspace created: {workspace_id}")
    
    # Create proposal and approve to get tasks
    proposal_payload = {
        "workspace_id": workspace_id,
        "project_description": "Simple test project for task execution debugging",
        "project_goals": ["Complete the test task successfully"]
    }
    
    # Create and approve proposal
    proposal_response = requests.post(f"{API_BASE}/director/proposal", json=proposal_payload, timeout=30)
    if proposal_response.status_code != 200:
        logger.error(f"❌ Proposal creation failed: {proposal_response.status_code}")
        return False
    
    proposal_data = proposal_response.json()
    proposal_id = proposal_data.get("proposal_id")
    
    approval_response = requests.post(f"{API_BASE}/director/approve/{workspace_id}", 
                                    params={"proposal_id": proposal_id}, timeout=30)
    if approval_response.status_code not in [200, 204]:
        logger.error(f"❌ Proposal approval failed: {approval_response.status_code}")
        return False
    
    logger.info("✅ Proposal approved, waiting for task generation...")
    
    # Wait for task generation
    task_id = None
    for i in range(12):  # Wait up to 60 seconds
        time.sleep(5)
        
        tasks_response = requests.get(f"{API_BASE}/workspaces/{workspace_id}/tasks", timeout=10)
        if tasks_response.status_code == 200:
            tasks = tasks_response.json()
            if len(tasks) > 0:
                task_id = tasks[0]["id"]
                task_name = tasks[0]["name"]
                task_status = tasks[0]["status"]
                logger.info(f"✅ Task found: {task_name} (ID: {task_id}) - Status: {task_status}")
                break
        
        logger.info(f"⏳ Waiting for task generation... ({(i+1)*5}s)")
    
    if not task_id:
        logger.error("❌ No task generated within timeout")
        return False
    
    # Phase 2: Monitor task execution
    logger.info("📋 Phase 2: Monitoring task execution...")
    
    # Check task status over time
    execution_started = False
    execution_completed = False
    
    for i in range(24):  # Monitor for 2 minutes
        time.sleep(5)
        
        # Get task details
        task_response = requests.get(f"{API_BASE}/workspaces/{workspace_id}/tasks", timeout=10)
        if task_response.status_code == 200:
            tasks = task_response.json()
            current_task = None
            
            for task in tasks:
                if task["id"] == task_id:
                    current_task = task
                    break
            
            if current_task:
                status = current_task.get("status", "unknown")
                agent_id = current_task.get("agent_id")
                updated_at = current_task.get("updated_at")
                
                logger.info(f"📝 Task status after {(i+1)*5}s: {status}")
                
                if agent_id:
                    logger.info(f"👤 Assigned to agent: {agent_id}")
                
                if status == "in_progress" and not execution_started:
                    execution_started = True
                    logger.info("🚀 Task execution STARTED!")
                
                if status == "completed" and not execution_completed:
                    execution_completed = True
                    result = current_task.get("result", "No result")
                    logger.info(f"✅ Task execution COMPLETED!")
                    logger.info(f"📝 Result: {result[:200]}..." if len(result) > 200 else f"📝 Result: {result}")
                    break
                
                if status == "failed":
                    error = current_task.get("error_message", "No error message")
                    logger.error(f"❌ Task execution FAILED: {error}")
                    break
            
        else:
            logger.warning(f"⚠️ Task retrieval failed: {task_response.status_code}")
    
    # Phase 3: Check executor status
    logger.info("⚙️ Phase 3: Checking executor status...")
    
    try:
        # Check if there's an executor status endpoint
        executor_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if executor_response.status_code == 200:
            logger.info("✅ System health check passed")
        else:
            logger.warning(f"⚠️ System health check failed: {executor_response.status_code}")
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
    
    # Phase 4: Check agent status
    logger.info("👥 Phase 4: Checking agent status...")
    
    try:
        agents_response = requests.get(f"{BASE_URL}/agents/{workspace_id}", timeout=10)
        if agents_response.status_code == 200:
            agents = agents_response.json()
            logger.info(f"✅ Found {len(agents)} agents:")
            
            for agent in agents:
                agent_id = agent.get("id")
                agent_name = agent.get("name")
                agent_status = agent.get("status")
                logger.info(f"  - {agent_name} (ID: {agent_id}) - Status: {agent_status}")
        else:
            logger.warning(f"⚠️ Agents retrieval failed: {agents_response.status_code}")
    except Exception as e:
        logger.error(f"❌ Agents check error: {e}")
    
    # Phase 5: Final summary
    logger.info("📊 Phase 5: Final summary...")
    
    if execution_completed:
        logger.info("🎉 Task execution completed successfully!")
        logger.info("✅ This means the executor is working and tasks are being processed")
    elif execution_started:
        logger.warning("⚠️ Task execution started but didn't complete within timeout")
        logger.warning("This might indicate slow execution or hanging tasks")
    else:
        logger.error("❌ Task execution never started")
        logger.error("This indicates a problem with the task executor or task assignment")
    
    return execution_completed

if __name__ == "__main__":
    asyncio.run(debug_task_execution())