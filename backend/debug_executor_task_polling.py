#!/usr/bin/env python3
"""
Debug script to investigate executor task polling mechanism
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

# Import database functions directly to test
import sys
import os
sys.path.append(os.path.dirname(__file__))

from database import list_tasks, get_workspaces_with_pending_tasks
from models import TaskStatus

async def debug_executor_polling():
    """Debug the executor's task polling mechanism"""
    
    logger.info("🔍 Starting executor task polling debug")
    
    # Use existing workspace with tasks
    workspace_id = "5756d14c-6ff7-4d9e-a889-14b12bdf293c"
    
    logger.info(f"📁 Debugging workspace: {workspace_id}")
    
    # 1. Check workspaces with pending tasks
    logger.info("📋 1. Checking workspaces with pending tasks...")
    try:
        workspaces_with_pending = await get_workspaces_with_pending_tasks()
        logger.info(f"✅ Workspaces with pending tasks: {workspaces_with_pending}")
        
        if workspace_id in workspaces_with_pending:
            logger.info(f"✅ Target workspace {workspace_id} is in pending workspaces list")
        else:
            logger.error(f"❌ Target workspace {workspace_id} NOT in pending workspaces list")
            # Check if there are actually pending tasks
            all_pending_tasks = await list_tasks(workspace_id, status="pending")
            logger.info(f"📊 Direct query shows {len(all_pending_tasks)} pending tasks")
            for task in all_pending_tasks[:3]:
                logger.info(f"  - {task.get('name', 'Unknown')}: {task.get('status')} (assigned to: {task.get('assigned_to')})")
            
    except Exception as e:
        logger.error(f"❌ Error checking workspaces with pending tasks: {e}")
        return False
    
    # 2. Check all tasks for workspace
    logger.info("📋 2. Checking all tasks for workspace...")
    try:
        all_tasks = await list_tasks(workspace_id)
        logger.info(f"✅ Found {len(all_tasks)} total tasks")
        
        # Count by status
        status_counts = {}
        for task in all_tasks:
            status = task.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        logger.info(f"📊 Task status distribution: {status_counts}")
        
        # Show pending tasks
        pending_tasks = [t for t in all_tasks if t.get('status') == TaskStatus.PENDING.value]
        logger.info(f"📋 Pending tasks ({len(pending_tasks)}):")
        
        for i, task in enumerate(pending_tasks[:5]):
            task_id = task.get('id')
            task_name = task.get('name', 'Unknown')
            assigned_to = task.get('assigned_to')
            created_at = task.get('created_at')
            logger.info(f"  {i+1}. {task_name[:50]}")
            logger.info(f"     ID: {task_id}")
            logger.info(f"     Assigned to: {assigned_to}")
            logger.info(f"     Created: {created_at}")
            
    except Exception as e:
        logger.error(f"❌ Error listing tasks: {e}")
        return False
    
    # 3. Check executor status
    logger.info("🤖 3. Checking executor status...")
    try:
        executor_response = requests.get(f"{BASE_URL}/executor-status", timeout=10)
        if executor_response.status_code == 200:
            executor_status = executor_response.json()
            logger.info(f"✅ Executor status: {json.dumps(executor_status, indent=2)}")
            
            # Key metrics
            is_running = executor_status.get('is_running', False)
            is_paused = executor_status.get('is_paused', False)
            tasks_in_queue = executor_status.get('tasks_in_queue', 0)
            active_tasks = executor_status.get('active_tasks', 0)
            tasks_completed = executor_status.get('tasks_completed_successfully', 0)
            tasks_failed = executor_status.get('tasks_failed', 0)
            
            logger.info(f"🔍 Key metrics:")
            logger.info(f"   Running: {is_running}")
            logger.info(f"   Paused: {is_paused}")
            logger.info(f"   Tasks in queue: {tasks_in_queue}")
            logger.info(f"   Active tasks: {active_tasks}")
            logger.info(f"   Tasks completed: {tasks_completed}")
            logger.info(f"   Tasks failed: {tasks_failed}")
            
            if is_running and not is_paused and tasks_in_queue == 0:
                logger.warning("⚠️ ISSUE DETECTED: Executor is running but has 0 tasks in queue despite pending tasks!")
                
        else:
            logger.error(f"❌ Executor status request failed: {executor_response.status_code}")
            
    except Exception as e:
        logger.error(f"❌ Error checking executor status: {e}")
    
    # 4. Test the specific executor logic that filters tasks
    logger.info("🧪 4. Testing executor task filtering logic...")
    try:
        # Simulate the executor's filtering logic
        all_tasks_for_workspace = await list_tasks(workspace_id)
        
        # Filter for PENDING tasks not already completed (simplified version)
        pending_eligible_tasks = [
            t for t in all_tasks_for_workspace
            if t.get("status") == TaskStatus.PENDING.value
        ]
        
        logger.info(f"🔍 Executor filtering simulation:")
        logger.info(f"   Total tasks: {len(all_tasks_for_workspace)}")
        logger.info(f"   Pending eligible: {len(pending_eligible_tasks)}")
        
        if pending_eligible_tasks:
            logger.info(f"✅ Executor should find {len(pending_eligible_tasks)} tasks to process")
            
            # Show first few tasks
            for i, task in enumerate(pending_eligible_tasks[:3]):
                logger.info(f"   {i+1}. {task.get('name', 'Unknown')[:50]} (ID: {task.get('id')})")
        else:
            logger.error("❌ Executor filtering would find NO tasks to process!")
            
    except Exception as e:
        logger.error(f"❌ Error in filtering simulation: {e}")
    
    # 5. Monitor executor for a short period
    logger.info("👀 5. Monitoring executor activity for 30 seconds...")
    try:
        for i in range(6):  # 6 checks over 30 seconds
            time.sleep(5)
            
            # Check executor status
            executor_response = requests.get(f"{BASE_URL}/executor-status", timeout=5)
            if executor_response.status_code == 200:
                status = executor_response.json()
                tasks_in_queue = status.get('tasks_in_queue', 0)
                active_tasks = status.get('active_tasks', 0)
                
                # Check task status
                current_tasks = await list_tasks(workspace_id, status="pending")
                
                logger.info(f"   Check {i+1}: Queue={tasks_in_queue}, Active={active_tasks}, Pending={len(current_tasks)}")
                
                if tasks_in_queue > 0 or active_tasks > 0:
                    logger.info("🚀 ACTIVITY DETECTED! Executor is processing tasks")
                    break
            else:
                logger.warning(f"   Check {i+1}: Executor status unavailable")
        
    except Exception as e:
        logger.error(f"❌ Error monitoring executor: {e}")
    
    logger.info("🏁 Debug session complete")
    return True

if __name__ == "__main__":
    result = asyncio.run(debug_executor_polling())
    if result:
        print("✅ Debug session completed successfully")
    else:
        print("❌ Debug session failed")