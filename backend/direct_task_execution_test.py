#!/usr/bin/env python3
"""
Direct task execution test to validate OpenAI trace
"""

import asyncio
import logging
import os
from uuid import UUID, uuid4
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Enable OpenAI trace
os.environ['OPENAI_TRACE'] = 'true'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

from models import Task, TaskStatus, Agent as AgentModel, AgentStatus
from ai_agents.specialist_enhanced import SpecialistAgent
# Remove database dependency for direct testing

async def test_direct_task_execution():
    """Test direct task execution with OpenAI trace"""
    
    logger.info("🚀 Starting direct task execution test with OpenAI trace enabled")
    
    # Create test workspace ID (proper UUID)
    workspace_id = uuid4()
    
    # Create agent model directly without database
    agent_model = AgentModel(
        id=uuid4(),
        workspace_id=workspace_id,
        name="Test Specialist Agent",
        role="Content Specialist",
        seniority="Senior",
        hard_skills=[{"name": "Research", "level": "Advanced"}],
        soft_skills=[{"name": "Communication", "level": "Advanced"}],
        personality_traits=["analytical", "creative", "specialized"],
        status="available",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    logger.info(f"👤 Created test agent: {agent_model.id}")
    
    # Create a test task
    task_data = {
        "id": uuid4(),
        "workspace_id": workspace_id,
        "agent_id": agent_model.id,
        "name": "Test Task for OpenAI Trace",
        "description": "This is a test task to validate OpenAI trace functionality. Please analyze the current state of artificial intelligence and provide insights.",
        "status": TaskStatus.PENDING,
        "priority": "high",
        "context_data": {"test": True},
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    task = Task(**task_data)
    logger.info(f"📋 Created test task: {task.id}")
    
    # Initialize specialist agent
    specialist = SpecialistAgent(agent_model)
    
    # Execute the task
    logger.info("🚀 Executing task with OpenAI trace...")
    result = await specialist.execute(task)
    
    # Check the results
    logger.info(f"✅ Task execution completed!")
    logger.info(f"📊 Status: {result.status}")
    logger.info(f"⏱️ Execution time: {result.execution_time:.2f}s")
    
    if result.status == TaskStatus.COMPLETED:
        logger.info(f"✅ Task completed successfully!")
        logger.info(f"📝 Result length: {len(result.result)} characters")
        logger.info(f"📝 Result preview: {result.result[:200]}...")
        
        if result.summary:
            logger.info(f"📋 Summary: {result.summary}")
        
        if result.structured_content:
            logger.info(f"🏗️ Structured content available: {len(result.structured_content)} characters")
        
        return True
    else:
        logger.error(f"❌ Task failed: {result.error_message}")
        return False

async def main():
    """Main test function"""
    success = await test_direct_task_execution()
    
    if success:
        logger.info("🎉 Direct task execution test passed!")
        return 0
    else:
        logger.error("❌ Direct task execution test failed!")
        return 1

if __name__ == "__main__":
    import sys
    result = asyncio.run(main())
    sys.exit(result)