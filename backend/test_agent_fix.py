#!/usr/bin/env python3
"""Test script to verify OpenAI SDK Agent creation works"""

import logging
import asyncio
import uuid
from datetime import datetime

# Configure logging to see issues
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_agent_creation():
    """Test that agent creation works with current SDK"""
    try:
        # Import after logging is configured
        from ai_agents.specialist_enhanced import SpecialistAgent
        from models import Agent as AgentModel, Task, TaskStatus
        
        # Create a test agent
        agent_data = AgentModel(
            id=uuid.uuid4(),
            workspace_id=uuid.uuid4(),
            name='Test Agent',
            role='developer',
            status='active',
            seniority='senior',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        logger.info("Creating SpecialistAgent...")
        specialist = SpecialistAgent(agent_data)
        
        # Create a test task
        task = Task(
            id=uuid.uuid4(),
            workspace_id=agent_data.workspace_id,
            name='Test Task',
            description='Test task description',
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        logger.info("Executing task with agent...")
        result = await specialist.execute(task)
        
        print("✅ SUCCESS: Agent creation and task execution worked!")
        print(f"Result: {result}")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_agent_creation())
    exit(0 if success else 1)