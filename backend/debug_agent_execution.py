#!/usr/bin/env python3
"""
Debug agent execution to find the real blocking issue
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from database import supabase

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

async def debug_agent_execution():
    """Debug why agents aren't executing tasks"""
    logger.info("🔍 DEBUGGING AGENT EXECUTION")
    logger.info("="*50)
    
    # Verify environment
    logger.info("🔑 Environment Check:")
    logger.info(f"  OPENAI_API_KEY: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Missing'}")
    logger.info(f"  SUPABASE_URL: {'✅ Set' if os.getenv('SUPABASE_URL') else '❌ Missing'}")
    
    # Get a task that's in progress
    try:
        response = await asyncio.to_thread(
            supabase.table("tasks").select("*").eq("status", "in_progress").limit(1).execute
        )
        
        if not response.data:
            logger.error("No tasks in progress")
            return
            
        task = response.data[0]
        agent_id = task.get('agent_id')
        
        logger.info(f"📋 Task: {task['name']}")
        logger.info(f"👤 Agent ID: {agent_id}")
        
        # Get the agent
        response = await asyncio.to_thread(
            supabase.table("agents").select("*").eq("id", agent_id).execute
        )
        
        if not response.data:
            logger.error(f"Agent {agent_id} not found")
            return
            
        agent = response.data[0]
        logger.info(f"✅ Agent: {agent['name']} ({agent['role']})")
        
        # Try to execute the agent
        logger.info("🚀 Attempting agent execution...")
        
        try:
            from ai_agents.manager import AgentManager
            
            # Initialize agent manager
            agent_manager = AgentManager()
            logger.info("✅ AgentManager initialized")
            
            # Try to execute task
            logger.info(f"Executing task {task['id']} with agent {agent['name']}...")
            
            # Check if agent SDK is available
            try:
                from agents import Agent as OpenAIAgent
                logger.info("✅ OpenAI Agents SDK available")
            except ImportError as e:
                logger.error(f"❌ OpenAI Agents SDK not available: {e}")
                
                # Try legacy SDK
                try:
                    from openai_agents import Agent as OpenAIAgent
                    logger.info("✅ Legacy OpenAI Agents SDK available")
                except ImportError as e2:
                    logger.error(f"❌ No agent SDK available: {e2}")
                    return
            
            # Check OpenAI client
            try:
                from openai import AsyncOpenAI
                client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                logger.info("✅ OpenAI client initialized")
                
                # Test API key
                models = await client.models.list()
                logger.info(f"✅ API key valid - {len(models.data)} models available")
                
            except Exception as e:
                logger.error(f"❌ OpenAI client error: {e}")
                return
            
            # Check agent execution method
            if hasattr(agent_manager, 'execute_agent_task'):
                logger.info("✅ execute_agent_task method exists")
                
                # Try to execute
                try:
                    result = await agent_manager.execute_agent_task(
                        agent_id=agent['id'],
                        task_id=task['id'],
                        task_name=task['name'],
                        task_description=task.get('description', ''),
                        workspace_id=task['workspace_id']
                    )
                    logger.info(f"🎉 Task execution result: {result}")
                except Exception as e:
                    logger.error(f"❌ Task execution failed: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                logger.error("❌ execute_agent_task method not found")
                
        except Exception as e:
            logger.error(f"❌ Agent execution setup failed: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        logger.error(f"Failed to debug execution: {e}")

if __name__ == "__main__":
    asyncio.run(debug_agent_execution())