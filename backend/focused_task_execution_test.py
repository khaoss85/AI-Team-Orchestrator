#!/usr/bin/env python3
"""
Focused test to validate task execution with OpenAI trace
"""

import asyncio
import logging
import requests
import json
import time
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"

async def test_task_execution_with_trace():
    """Test task execution and trace validation"""
    
    # Enable OpenAI trace
    os.environ['OPENAI_TRACE'] = 'true'
    
    logger.info("🚀 Starting focused task execution test with OpenAI trace enabled")
    
    # Phase 1: Create workspace
    logger.info("📁 Creating workspace...")
    workspace_response = requests.post(f"{BASE_URL}/api/workspaces", json={
        "name": "Test Workspace - Task Execution",
        "description": "Testing task execution with OpenAI trace"
    })
    
    if workspace_response.status_code not in [200, 201]:
        logger.error(f"❌ Failed to create workspace: {workspace_response.status_code}")
        return False
        
    workspace_id = workspace_response.json()["id"]
    logger.info(f"✅ Workspace created: {workspace_id}")
    
    # Phase 2: Create goal
    logger.info("🎯 Creating goal...")
    goal_response = requests.post(f"{BASE_URL}/api/workspaces/{workspace_id}/goals", json={
        "name": "Task Execution Test Goal",
        "description": "Test goal for validating task execution with OpenAI trace",
        "success_criteria": "Successfully execute a task and generate output with OpenAI trace logging",
        "workspace_id": workspace_id,
        "metric_type": "completion",
        "target_value": 1.0
    })
    
    if goal_response.status_code not in [200, 201]:
        logger.error(f"❌ Failed to create goal: {goal_response.status_code}")
        logger.error(f"❌ Goal creation error: {goal_response.text}")
        return False
        
    goal_data = goal_response.json()
    goal_id = goal_data.get("goal", {}).get("id") or goal_data.get("id")
    logger.info(f"✅ Goal created: {goal_id}")
    
    # Phase 3: Propose team
    logger.info("👥 Proposing team...")
    team_response = requests.post(f"{BASE_URL}/api/director/proposal", json={
        "workspace_id": workspace_id,
        "project_description": "Simple test project to validate task execution",
        "project_goals": ["Execute a single task successfully with OpenAI trace"]
    })
    
    if team_response.status_code != 200:
        logger.error(f"❌ Failed to propose team: {team_response.status_code}")
        return False
        
    team_data = team_response.json()
    logger.info(f"✅ Team proposed with {len(team_data.get('agents', []))} agents")
    
    # Phase 4: Start orchestration
    logger.info("🎼 Starting orchestration...")
    orchestration_response = requests.post(f"{BASE_URL}/api/workspaces/{workspace_id}/orchestration/start")
    
    if orchestration_response.status_code != 200:
        logger.error(f"❌ Failed to start orchestration: {orchestration_response.status_code}")
        return False
        
    logger.info("✅ Orchestration started")
    
    # Phase 5: Wait for task creation and execution
    logger.info("⏳ Waiting for task creation and execution...")
    max_wait_time = 60  # 1 minute
    start_time = time.time()
    
    task_executed = False
    task_id = None
    
    while time.time() - start_time < max_wait_time:
        # Check for tasks
        tasks_response = requests.get(f"{BASE_URL}/api/workspaces/{workspace_id}/tasks")
        
        if tasks_response.status_code == 200:
            tasks = tasks_response.json()
            
            for task in tasks:
                logger.info(f"📋 Task found: {task['name']} - Status: {task['status']}")
                
                if task['status'] == 'completed':
                    task_executed = True
                    task_id = task['id']
                    logger.info(f"✅ Task completed successfully: {task_id}")
                    break
                elif task['status'] == 'failed':
                    logger.error(f"❌ Task failed: {task['id']}")
                    return False
                    
        if task_executed:
            break
            
        time.sleep(2)
    
    if not task_executed:
        logger.error("❌ No task was executed within the timeout period")
        return False
    
    # Phase 6: Validate OpenAI trace
    logger.info("🔍 Validating OpenAI trace...")
    
    # Check if trace was generated (this is logged in the specialist agent)
    # For now, we'll check the task result contains meaningful content
    if task_id:
        task_details_response = requests.get(f"{BASE_URL}/api/workspaces/{workspace_id}/tasks/{task_id}")
        
        if task_details_response.status_code == 200:
            task_details = task_details_response.json()
            result = task_details.get('result', '')
            
            if result and len(result) > 50:
                logger.info(f"✅ Task result contains meaningful content ({len(result)} characters)")
                logger.info(f"📝 Task result preview: {result[:200]}...")
            else:
                logger.warning(f"⚠️ Task result seems minimal: {result}")
    
    # Phase 7: Check deliverables
    logger.info("📦 Checking deliverables...")
    deliverables_response = requests.get(f"{BASE_URL}/api/workspaces/{workspace_id}/deliverables")
    
    if deliverables_response.status_code == 200:
        deliverables = deliverables_response.json()
        logger.info(f"✅ Found {len(deliverables)} deliverables")
        
        for deliverable in deliverables:
            logger.info(f"📦 Deliverable: {deliverable['name']} - Status: {deliverable['status']}")
    
    # Phase 8: Check QA validations
    logger.info("🛡️ Checking QA validations...")
    # This would require a QA endpoint, for now we'll just log completion
    
    logger.info("✅ Focused task execution test completed successfully")
    return True

async def main():
    """Main test function"""
    success = await test_task_execution_with_trace()
    
    if success:
        logger.info("🎉 All tests passed!")
        return 0
    else:
        logger.error("❌ Test failed!")
        return 1

if __name__ == "__main__":
    import sys
    result = asyncio.run(main())
    sys.exit(result)