#!/usr/bin/env python3
"""
Final Validation Test - Check if architectural fixes resolved task execution
"""

import asyncio
import logging
import time
from database import supabase

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

async def monitor_task_completion():
    """Monitor task completion after architectural fixes"""
    logger.info("🔧 FINAL VALIDATION TEST - Monitoring Task Completion")
    logger.info("="*60)
    
    start_time = time.time()
    initial_in_progress = 0
    initial_completed = 0
    
    # Get baseline counts
    try:
        response = await asyncio.to_thread(
            supabase.table("tasks").select("status").eq("status", "in_progress").execute
        )
        initial_in_progress = len(response.data)
        
        response = await asyncio.to_thread(
            supabase.table("tasks").select("status").eq("status", "completed").execute
        )
        initial_completed = len(response.data)
        
        logger.info(f"📊 Initial state: {initial_in_progress} in_progress, {initial_completed} completed")
        
    except Exception as e:
        logger.error(f"Failed to get initial state: {e}")
        return False
    
    # Monitor for 45 seconds
    while time.time() - start_time < 45:
        try:
            response = await asyncio.to_thread(
                supabase.table("tasks").select("status").eq("status", "in_progress").execute
            )
            current_in_progress = len(response.data)
            
            response = await asyncio.to_thread(
                supabase.table("tasks").select("status").eq("status", "completed").execute
            )
            current_completed = len(response.data)
            
            completed_delta = current_completed - initial_completed
            progress_delta = initial_in_progress - current_in_progress
            
            logger.info(f"📊 Current: {current_in_progress} in_progress (+{completed_delta} completed)")
            
            # Check for task completion progress
            if completed_delta > 0:
                logger.info(f"🎉 SUCCESS: {completed_delta} tasks completed!")
                
                # Get details of completed tasks
                response = await asyncio.to_thread(
                    supabase.table("tasks").select("*").eq("status", "completed").order("updated_at", desc=True).limit(3).execute
                )
                
                for task in response.data:
                    logger.info(f"  ✅ Completed: {task['name']} (Agent: {task.get('agent_id', 'None')})")
                
                return True
            
            if progress_delta > 0:
                logger.info(f"📈 Progress detected: {progress_delta} tasks moved from in_progress")
            
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
            
        await asyncio.sleep(5)
    
    elapsed = time.time() - start_time
    logger.info(f"⏰ Monitoring complete after {elapsed:.1f}s")
    
    if completed_delta > 0:
        logger.info("✅ Task completion working!")
        return True
    else:
        logger.warning("⚠️ No task completion detected - checking for other issues")
        
        # Check for specific blocking issues
        try:
            response = await asyncio.to_thread(
                supabase.table("tasks").select("*").eq("status", "in_progress").limit(1).execute
            )
            
            if response.data:
                task = response.data[0]
                logger.info(f"🔍 In-progress task details:")
                logger.info(f"  Task: {task['name']}")
                logger.info(f"  Agent ID: {task.get('agent_id', 'None')}")
                logger.info(f"  Created: {task.get('created_at', 'Unknown')}")
                logger.info(f"  Updated: {task.get('updated_at', 'Unknown')}")
                
                # Check agent status
                if task.get('agent_id'):
                    agent_response = await asyncio.to_thread(
                        supabase.table("agents").select("*").eq("id", task["agent_id"]).execute
                    )
                    
                    if agent_response.data:
                        agent = agent_response.data[0]
                        logger.info(f"  Agent: {agent['name']} ({agent['status']}) - {agent['role']}")
                    else:
                        logger.warning(f"  ❌ Agent {task['agent_id']} not found")
                        
        except Exception as e:
            logger.error(f"Error checking task details: {e}")
        
        return False

if __name__ == "__main__":
    result = asyncio.run(monitor_task_completion())
    print(f"\n{'✅ SUCCESS' if result else '❌ INCOMPLETE'}: Task execution validation")
    exit(0 if result else 1)