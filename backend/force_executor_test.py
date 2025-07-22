#!/usr/bin/env python3
"""
Force executor test - Verificare che l'executor processi i task
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

async def force_executor_test():
    """Force a test to verify executor processes tasks"""
    
    logger.info("🔥 Starting FORCE EXECUTOR TEST")
    
    workspace_id = "5756d14c-6ff7-4d9e-a889-14b12bdf293c"
    task_id = "48205181-048a-45fa-b2df-23fb29c9fa23"
    
    logger.info(f"📁 Workspace: {workspace_id}")
    logger.info(f"📝 Task: {task_id}")
    
    # 1. Verify executor is running
    logger.info("🤖 1. Checking executor status...")
    try:
        response = requests.get(f"{BASE_URL}/monitoring/executor/status", timeout=5)
        if response.status_code == 200:
            status = response.json()
            logger.info(f"✅ Executor: {status}")
            if not status.get('is_running'):
                logger.error("❌ Executor is not running!")
                return False
        else:
            logger.error(f"❌ Executor status failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Executor status error: {e}")
        return False
    
    # 2. Check initial task status
    logger.info("📋 2. Checking initial task status...")
    try:
        response = requests.get(f"{BASE_URL}/api/workspaces/{workspace_id}/tasks", timeout=10)
        if response.status_code == 200:
            tasks = response.json()
            target_task = None
            for task in tasks:
                if task.get('id') == task_id:
                    target_task = task
                    break
            
            if target_task:
                logger.info(f"✅ Found task: {target_task.get('name')}")
                logger.info(f"   Status: {target_task.get('status')}")
                logger.info(f"   Agent ID: {target_task.get('agent_id')}")
                initial_status = target_task.get('status')
            else:
                logger.error("❌ Target task not found!")
                return False
        else:
            logger.error(f"❌ Tasks request failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Tasks check error: {e}")
        return False
    
    # 3. Monitor for task status changes
    logger.info("👀 3. Monitoring task execution for 2 minutes...")
    
    status_changes = []
    last_status = initial_status
    
    for i in range(24):  # 24 checks over 2 minutes (5 second intervals)
        time.sleep(5)
        
        try:
            response = requests.get(f"{BASE_URL}/api/workspaces/{workspace_id}/tasks", timeout=5)
            if response.status_code == 200:
                tasks = response.json()
                current_task = None
                for task in tasks:
                    if task.get('id') == task_id:
                        current_task = task
                        break
                
                if current_task:
                    current_status = current_task.get('status')
                    updated_at = current_task.get('updated_at')
                    
                    if current_status != last_status:
                        change = {
                            'time': (i + 1) * 5,
                            'from': last_status,
                            'to': current_status,
                            'timestamp': updated_at
                        }
                        status_changes.append(change)
                        logger.info(f"🔄 STATUS CHANGE: {last_status} → {current_status} at {updated_at}")
                        last_status = current_status
                    
                    # Check for completion
                    if current_status == 'completed':
                        logger.info("🎉 TASK COMPLETED!")
                        result = current_task.get('result', '')
                        if result:
                            logger.info(f"📝 Result: {result[:200]}...")
                        break
                    elif current_status == 'failed':
                        logger.error("💥 TASK FAILED!")
                        error = current_task.get('error_message', 'No error details')
                        logger.error(f"Error: {error}")
                        break
                    elif current_status == 'in_progress':
                        logger.info(f"🚀 Task is IN PROGRESS (check {i+1}/24)")
                    else:
                        logger.info(f"📊 Status: {current_status} (check {i+1}/24)")
                        
        except Exception as e:
            logger.warning(f"⚠️ Check {i+1} failed: {e}")
    
    # 4. Final summary
    logger.info("\n" + "="*50)
    logger.info("🏁 FORCE EXECUTOR TEST SUMMARY")
    logger.info("="*50)
    
    if status_changes:
        logger.info(f"✅ Detected {len(status_changes)} status changes:")
        for change in status_changes:
            logger.info(f"   {change['time']}s: {change['from']} → {change['to']}")
        
        if any(change['to'] in ['completed', 'in_progress'] for change in status_changes):
            logger.info("🎉 SUCCESS: Executor IS processing tasks!")
            return True
        else:
            logger.warning("⚠️ PARTIAL: Task status changed but didn't progress to execution")
            return False
    else:
        logger.error("❌ FAILURE: No status changes detected - executor may not be processing tasks")
        
        # Additional diagnostic info
        try:
            response = requests.get(f"{BASE_URL}/monitoring/executor/status", timeout=5)
            if response.status_code == 200:
                final_status = response.json()
                logger.info(f"Final executor status: {final_status}")
        except Exception as e:
            logger.error(f"Failed to get final executor status: {e}")
        
        return False

if __name__ == "__main__":
    result = asyncio.run(force_executor_test())
    if result:
        print("✅ EXECUTOR IS WORKING - Task execution verified!")
    else:
        print("❌ EXECUTOR ISSUE - Task execution not verified")