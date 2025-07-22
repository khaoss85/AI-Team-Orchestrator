#!/usr/bin/env python3
"""
Force task execution test per verificare se i task vengono processati
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

async def force_task_execution_test():
    """Test per forzare l'esecuzione di un task esistente"""
    
    logger.info("🔍 Starting force task execution test")
    
    # Use existing workspace from successful test
    workspace_id = "5756d14c-6ff7-4d9e-a889-14b12bdf293c"
    
    logger.info(f"📁 Using existing workspace: {workspace_id}")
    
    # Check existing tasks
    logger.info("📋 Checking existing tasks...")
    
    tasks_response = requests.get(f"{API_BASE}/workspaces/{workspace_id}/tasks", timeout=10)
    if tasks_response.status_code != 200:
        logger.error(f"❌ Tasks retrieval failed: {tasks_response.status_code}")
        return False
    
    tasks = tasks_response.json()
    logger.info(f"✅ Found {len(tasks)} tasks")
    
    if len(tasks) == 0:
        logger.error("❌ No tasks found to test")
        return False
    
    # Get the first task
    task = tasks[0]
    task_id = task["id"]
    task_name = task["name"]
    task_status = task["status"]
    agent_id = task.get("agent_id")
    
    logger.info(f"📝 Task to test: {task_name}")
    logger.info(f"🆔 Task ID: {task_id}")
    logger.info(f"📊 Current status: {task_status}")
    logger.info(f"👤 Assigned agent: {agent_id}")
    
    # If task is already completed or failed, create a new one
    if task_status in ["completed", "failed"]:
        logger.info("🔄 Task already processed, creating a new test task...")
        
        # Create a simple test task directly
        test_task_data = {
            "name": "Simple Test Task for Execution",
            "description": "This is a simple test task to verify task execution functionality. Please provide a brief analysis of the current weather.",
            "workspace_id": workspace_id,
            "priority": "high"
        }
        
        # Try to create task via API (if endpoint exists)
        try:
            create_response = requests.post(f"{API_BASE}/workspaces/{workspace_id}/tasks", 
                                          json=test_task_data, timeout=10)
            if create_response.status_code in [200, 201]:
                new_task = create_response.json()
                task_id = new_task["id"]
                logger.info(f"✅ New test task created: {task_id}")
            else:
                logger.error(f"❌ Task creation failed: {create_response.status_code}")
                logger.info("Using existing task for monitoring...")
        except Exception as e:
            logger.warning(f"⚠️ Task creation error: {e}")
            logger.info("Using existing task for monitoring...")
    
    # Monitor task execution with detailed logging
    logger.info("👀 Monitoring task execution with detailed tracking...")
    
    initial_status = task_status
    status_changes = []
    
    for i in range(60):  # Monitor for 5 minutes
        time.sleep(5)
        
        # Get updated task details
        tasks_response = requests.get(f"{API_BASE}/workspaces/{workspace_id}/tasks", timeout=10)
        if tasks_response.status_code == 200:
            updated_tasks = tasks_response.json()
            current_task = None
            
            for t in updated_tasks:
                if t["id"] == task_id:
                    current_task = t
                    break
            
            if current_task:
                current_status = current_task.get("status", "unknown")
                current_agent = current_task.get("agent_id")
                updated_at = current_task.get("updated_at")
                result = current_task.get("result", "")
                error_msg = current_task.get("error_message", "")
                
                # Track status changes
                if current_status != initial_status:
                    status_changes.append({
                        "time": (i+1)*5,
                        "from": initial_status,
                        "to": current_status,
                        "timestamp": updated_at
                    })
                    initial_status = current_status
                    logger.info(f"🔄 Status changed to: {current_status} at {updated_at}")
                
                logger.info(f"📊 After {(i+1)*5}s: Status={current_status}, Agent={current_agent}")
                
                if current_status == "in_progress":
                    logger.info("🚀 Task is IN PROGRESS - executor picked it up!")
                
                if current_status == "completed":
                    logger.info("✅ Task COMPLETED successfully!")
                    logger.info(f"📝 Result: {result[:200]}..." if len(result) > 200 else f"📝 Result: {result}")
                    break
                
                if current_status == "failed":
                    logger.error("❌ Task FAILED!")
                    logger.error(f"💥 Error: {error_msg}")
                    break
            else:
                logger.warning(f"⚠️ Task {task_id} not found in response")
        else:
            logger.warning(f"⚠️ Task retrieval failed: {tasks_response.status_code}")
    
    # Summary
    logger.info("📊 Execution Summary:")
    logger.info(f"🔄 Status changes detected: {len(status_changes)}")
    
    for change in status_changes:
        logger.info(f"  - {change['time']}s: {change['from']} → {change['to']}")
    
    if len(status_changes) == 0:
        logger.error("❌ NO STATUS CHANGES DETECTED!")
        logger.error("This indicates the executor is not processing the task")
        return False
    
    if any(change['to'] == 'completed' for change in status_changes):
        logger.info("🎉 Task execution SUCCESSFUL!")
        return True
    
    if any(change['to'] == 'in_progress' for change in status_changes):
        logger.warning("⚠️ Task started but didn't complete")
        logger.warning("This might indicate execution hanging or timeout issues")
        return False
    
    logger.error("❌ Task execution didn't progress beyond initial status")
    return False

if __name__ == "__main__":
    result = asyncio.run(force_task_execution_test())
    if result:
        print("✅ Task execution test PASSED")
    else:
        print("❌ Task execution test FAILED")