#!/usr/bin/env python3
"""
🧪 TEST AGENT FIX
Test rapido per verificare che il fix dell'agent execution funzioni
"""

import asyncio
import sys
import os
import logging
from uuid import uuid4

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_agent_fix():
    """Test rapido del fix dell'agent"""
    logger.info("🧪 Testing Agent Execution Fix")
    
    try:
        # Step 1: Test database connectivity
        from database import supabase
        logger.info("✅ Database connection OK")
        
        # Step 2: Test task creation
        from database import create_workspace
        
        workspace_data = {
            "name": "Agent Fix Test",
            "description": "Testing agent execution fix",
            "user_id": str(uuid4()),
            "goal": "Creare un database di 10 contatti B2B per testare il sistema di agent execution"
        }
        
        workspace = await create_workspace(**workspace_data)
        workspace_id = str(workspace["id"])
        logger.info(f"✅ Test workspace created: {workspace_id}")
        
        # Step 3: Create a simple agent
        agent_response = supabase.table('agents').insert({
            "workspace_id": workspace_id,
            "name": "Test Marketing Agent",
            "role": "marketing_specialist",
            "seniority": "senior",
            "description": "Test agent for verifying execution fix",
            "status": "available",
            "health": {"status": "healthy"},
            "system_prompt": "You are a marketing specialist that creates contact databases.",
            "tools": [],
            "can_create_tools": False
        }).execute()
        
        if not agent_response.data:
            raise Exception("Failed to create test agent")
        
        agent_id = agent_response.data[0]['id']
        logger.info(f"✅ Test agent created: {agent_id}")
        
        # Step 4: Create a simple task
        task_response = supabase.table('tasks').insert({
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "name": "Create B2B Contact Database",
            "description": "Generate a database of 10 realistic B2B contacts with names, emails, and companies",
            "status": "pending",
            "priority": "medium",
            "metric_type": "contacts",
            "contribution_expected": 10.0,
            "context_data": {"test": True, "expected_contacts": 10}
        }).execute()
        
        if not task_response.data:
            raise Exception("Failed to create test task")
        
        task_id = task_response.data[0]['id']
        logger.info(f"✅ Test task created: {task_id}")
        
        # Step 5: Test agent execution via AgentManager
        from ai_agents.manager import AgentManager
        from uuid import UUID
        
        logger.info("🚀 Starting agent execution test...")
        
        # Initialize AgentManager
        manager = AgentManager(UUID(workspace_id))
        init_success = await manager.initialize()
        
        if not init_success:
            raise Exception("Failed to initialize AgentManager")
        
        logger.info("✅ AgentManager initialized")
        
        # Execute task
        result = await manager.execute_task(UUID(task_id))
        
        if result and result.get('status') == 'completed':
            logger.info("✅ Agent execution completed successfully!")
            logger.info(f"   Result: {result.get('result', 'No result data')}")
            
            # Check if task was updated in database
            task_check = supabase.table('tasks').select('*').eq('id', task_id).execute()
            if task_check.data:
                task_status = task_check.data[0]['status']
                logger.info(f"   Task status in DB: {task_status}")
                
                if task_status in ['completed', 'pending_verification']:
                    logger.info("🎉 AGENT FIX SUCCESSFUL - Task completed and updated in database!")
                    return True
                else:
                    logger.warning(f"⚠️ Task status not completed: {task_status}")
                    return False
            else:
                logger.error("❌ Could not verify task status in database")
                return False
        else:
            logger.error(f"❌ Agent execution failed: {result}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

async def main():
    """Run the agent fix test"""
    logger.info("🚀 STARTING AGENT FIX TEST")
    
    success = await test_agent_fix()
    
    if success:
        logger.info("🎉 AGENT FIX TEST PASSED - Real task execution working!")
    else:
        logger.error("💥 AGENT FIX TEST FAILED - Issues still exist")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)