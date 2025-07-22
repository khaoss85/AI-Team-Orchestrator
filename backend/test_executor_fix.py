#!/usr/bin/env python3
"""
Test esplicito per verificare e riparare il TaskExecutor
"""

import asyncio
import requests
import json
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

async def test_executor_fix():
    """Test per verificare TaskExecutor e forzare l'esecuzione dei task"""
    logger.info("🔧 EXECUTOR FIX TEST - DIAGNOSING TASK EXECUTION ISSUE")
    logger.info("="*60)
    
    # Step 1: Import and check TaskExecutor
    logger.info("📋 Step 1: Importing TaskExecutor...")
    try:
        from executor import task_executor, start_task_executor
        logger.info("✅ TaskExecutor imported successfully")
        logger.info(f"📊 TaskExecutor running: {task_executor.running}")
        logger.info(f"📊 TaskExecutor paused: {task_executor.paused}")
    except Exception as e:
        logger.error(f"❌ Failed to import TaskExecutor: {e}")
        return False
    
    # Step 2: Force start TaskExecutor if not running
    if not task_executor.running:
        logger.info("🚀 Step 2: Starting TaskExecutor explicitly...")
        try:
            await start_task_executor()
            await asyncio.sleep(2)  # Give it time to start
            logger.info("✅ TaskExecutor started")
            logger.info(f"📊 TaskExecutor running: {task_executor.running}")
        except Exception as e:
            logger.error(f"❌ Failed to start TaskExecutor: {e}")
            return False
    else:
        logger.info("✅ Step 2: TaskExecutor already running")
    
    # Step 3: Check for pending tasks
    logger.info("📋 Step 3: Checking for pending tasks...")
    try:
        from database import supabase
        
        # Get all pending tasks
        response = await asyncio.to_thread(
            supabase.table("tasks").select("*").eq("status", "pending").execute
        )
        
        pending_tasks = response.data
        logger.info(f"📊 Found {len(pending_tasks)} pending tasks")
        
        if pending_tasks:
            for i, task in enumerate(pending_tasks[:3]):  # Show first 3
                logger.info(f"  Task {i+1}: {task['name']} (Agent: {task.get('agent_id', 'None')})")
        
    except Exception as e:
        logger.error(f"❌ Failed to check pending tasks: {e}")
        return False
    
    # Step 4: Check for agents to execute tasks
    logger.info("📋 Step 4: Checking for available agents...")
    try:
        response = await asyncio.to_thread(
            supabase.table("agents").select("*").eq("status", "active").execute
        )
        
        active_agents = response.data
        logger.info(f"📊 Found {len(active_agents)} active agents")
        
        if active_agents:
            for i, agent in enumerate(active_agents[:3]):  # Show first 3
                logger.info(f"  Agent {i+1}: {agent['name']} ({agent['role']})")
        
    except Exception as e:
        logger.error(f"❌ Failed to check active agents: {e}")
        return False
    
    # Step 5: Force manual task execution if needed
    if pending_tasks and active_agents:
        logger.info("🔧 Step 5: Forcing manual task execution...")
        try:
            # Force execution of first pending task
            task = pending_tasks[0]
            agent = active_agents[0]
            
            logger.info(f"🎯 Forcing execution of task: {task['name']}")
            logger.info(f"👤 Using agent: {agent['name']}")
            
            # Force assignment and execution
            await asyncio.to_thread(
                supabase.table("tasks").update({
                    "agent_id": agent["id"],
                    "status": "in_progress"
                }).eq("id", task["id"]).execute
            )
            
            logger.info("✅ Task manually assigned to agent")
            
            # Force TaskExecutor to process immediately
            if hasattr(task_executor, '_process_assigned_tasks'):
                await task_executor._process_assigned_tasks()
                logger.info("✅ TaskExecutor forced to process tasks")
            
        except Exception as e:
            logger.error(f"❌ Failed to force task execution: {e}")
            return False
    
    # Step 6: Monitor task progress for 30 seconds
    logger.info("📊 Step 6: Monitoring task progress for 30 seconds...")
    start_time = time.time()
    initial_pending = len(pending_tasks)
    
    while time.time() - start_time < 30:
        try:
            response = await asyncio.to_thread(
                supabase.table("tasks").select("status").eq("status", "pending").execute
            )
            current_pending = len(response.data)
            
            response = await asyncio.to_thread(
                supabase.table("tasks").select("status").eq("status", "completed").execute
            )
            completed = len(response.data)
            
            logger.info(f"📊 Pending: {current_pending}, Completed: {completed}")
            
            if current_pending < initial_pending:
                logger.info("🎉 Task execution is working!")
                return True
                
        except Exception as e:
            logger.error(f"Error monitoring: {e}")
            
        await asyncio.sleep(5)
    
    logger.info("📊 Final Status:")
    logger.info(f"  Initial pending: {initial_pending}")
    logger.info(f"  TaskExecutor running: {task_executor.running}")
    
    if pending_tasks and not task_executor.running:
        logger.error("❌ PROBLEM: TaskExecutor not running but tasks pending")
        return False
    elif pending_tasks and task_executor.running:
        logger.warning("⚠️ PROBLEM: TaskExecutor running but tasks not processing")
        return False
    else:
        logger.info("✅ System appears healthy")
        return True

if __name__ == "__main__":
    result = asyncio.run(test_executor_fix())
    print(f"\n{'✅ SUCCESS' if result else '❌ FAILURE'}: TaskExecutor diagnosis complete")
    exit(0 if result else 1)