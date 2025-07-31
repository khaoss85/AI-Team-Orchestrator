#!/usr/bin/env python3
"""
Test single task execution to verify the complete loop works
"""

import asyncio
import logging
import os
import time
from dotenv import load_dotenv
from database import supabase

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

async def test_single_task_execution():
    """Test single task execution end-to-end"""
    logger.info("🧪 TESTING SINGLE TASK EXECUTION")
    logger.info("="*50)
    
    # Verify environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("❌ OPENAI_API_KEY not found")
        return False
    
    logger.info(f"✅ OpenAI API Key: {api_key[:10]}...")
    
    # Get first task in progress
    try:
        response = await asyncio.to_thread(
            supabase.table("tasks").select("*").eq("status", "in_progress").limit(1).execute
        )
        
        if not response.data:
            logger.error("❌ No tasks in progress")
            return False
            
        task = response.data[0]
        task_id = task['id']
        agent_id = task['agent_id']
        
        # Convert to UUID for AgentManager
        from uuid import UUID
        task_uuid = UUID(task_id)
        
        logger.info(f"📋 Task: {task['name']} (ID: {task_id})")
        logger.info(f"👤 Agent ID: {agent_id}")
        
        # Get agent data
        agent_response = await asyncio.to_thread(
            supabase.table("agents").select("*").eq("id", agent_id).execute
        )
        
        if not agent_response.data:
            logger.error(f"❌ Agent {agent_id} not found")
            return False
        
        agent = agent_response.data[0]
        logger.info(f"✅ Agent: {agent['name']} ({agent['role']})")
        
        # Try to execute task directly
        logger.info("🚀 Testing direct task execution...")
        
        try:
            # Import and test AgentManager
            from ai_agents.manager import AgentManager
            
            agent_manager = AgentManager(workspace_id=task['workspace_id'])
            logger.info("✅ AgentManager initialized")
            
            # Test execute_task method
            start_time = time.time()
            # Initialize agent manager first
            await agent_manager.initialize()
            result = await agent_manager.execute_task(task_id=task_uuid)
            
            execution_time = time.time() - start_time
            logger.info(f"⏱️ Execution time: {execution_time:.2f}s")
            
            if result:
                logger.info("🎉 SUCCESS! Task executed successfully")
                logger.info(f"📊 Result: {result}")
                
                # Check if task status changed
                updated_response = await asyncio.to_thread(
                    supabase.table("tasks").select("*").eq("id", task_id).execute
                )
                
                if updated_response.data:
                    updated_task = updated_response.data[0]
                    logger.info(f"📈 Task status: {updated_task['status']}")
                    
                    if updated_task['status'] == 'completed':
                        logger.info("✅ Task marked as completed!")
                        return True
                    else:
                        logger.warning(f"⚠️ Task still in status: {updated_task['status']}")
                        return False
                else:
                    logger.error("❌ Could not verify task status update")
                    return False
            else:
                logger.error("❌ Task execution returned no result")
                return False
                
        except Exception as e:
            logger.error(f"❌ Task execution failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        logger.error(f"❌ Test setup failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_single_task_execution())
    print(f"\n{'✅ SUCCESS' if result else '❌ FAILURE'}: Single task execution test")
    exit(0 if result else 1)