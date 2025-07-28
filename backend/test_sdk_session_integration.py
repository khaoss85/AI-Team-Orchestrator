#!/usr/bin/env python3
"""
Test SDK Session Integration - Verifica l'integrazione delle Sessions nell'agent specialist
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime
from uuid import uuid4

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Task, TaskStatus, Agent as AgentModel
from ai_agents.specialist_enhanced import SpecialistAgent
from services.sdk_memory_bridge import create_workspace_session

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_session_integration():
    """Test completo dell'integrazione SDK Session"""
    
    logger.info("🧪 TESTING SDK SESSION INTEGRATION")
    
    # Step 1: Create test workspace and agent
    workspace_id = str(uuid4())
    agent_id = str(uuid4())
    
    # Create test agent data
    agent_data = AgentModel(
        id=agent_id,
        workspace_id=workspace_id,
        name="Test Specialist",
        role="Software Developer",
        seniority="Senior",
        status="active",
        hard_skills=[{"name": "Python"}, {"name": "Testing"}, {"name": "SDK Integration"}],
        soft_skills=[{"name": "Problem Solving"}],
        personality_traits=["Detail-oriented"],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Create specialist agent
    specialist = SpecialistAgent(agent_data, [agent_data])
    
    # Step 2: Create test tasks
    test_tasks = [
        {
            "id": str(uuid4()),
            "workspace_id": workspace_id,
            "name": "Create Asset: Test Report",
            "description": "Generate a test report showing SDK session functionality",
            "status": TaskStatus.PENDING,
            "priority": "high",
            "agent_id": agent_id,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "id": str(uuid4()),
            "workspace_id": workspace_id,
            "name": "Analyze Previous Results",
            "description": "Analyze the results from the previous task using session memory",
            "status": TaskStatus.PENDING,
            "priority": "high",
            "agent_id": agent_id,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
    ]
    
    # Create Task objects
    tasks = [Task(**task_data) for task_data in test_tasks]
    
    logger.info(f"📝 Created {len(tasks)} test tasks")
    
    # Step 3: Test WITHOUT session (baseline)
    logger.info("\n🔬 TEST 1: Execution WITHOUT session")
    
    try:
        result1 = await specialist.execute(tasks[0], session=None)
        logger.info(f"✅ Task 1 completed without session")
        logger.info(f"   Result preview: {result1.result[:200]}...")
    except Exception as e:
        logger.error(f"❌ Task 1 failed: {e}")
        return False
    
    # Step 4: Test WITH session 
    logger.info("\n🔬 TEST 2: Execution WITH SDK session")
    
    # Create session
    session = create_workspace_session(workspace_id, agent_id)
    
    try:
        # Execute first task with session
        result2 = await specialist.execute(tasks[0], session=session)
        logger.info(f"✅ Task 1 completed with session")
        logger.info(f"   Result preview: {result2.result[:200]}...")
        
        # Check session items
        session_items = await session.get_items()
        logger.info(f"📚 Session has {len(session_items)} items after first task")
        
        # Execute second task with same session (should have context)
        result3 = await specialist.execute(tasks[1], session=session)
        logger.info(f"✅ Task 2 completed with session (has context from task 1)")
        logger.info(f"   Result preview: {result3.result[:200]}...")
        
        # Check session items again
        session_items_after = await session.get_items()
        logger.info(f"📚 Session has {len(session_items_after)} items after second task")
        
    except Exception as e:
        logger.error(f"❌ Session test failed: {e}")
        return False
    
    # Step 5: Verify session persistence
    logger.info("\n🔬 TEST 3: Session persistence verification")
    
    try:
        # Pop last item
        last_item = await session.pop_item()
        if last_item:
            logger.info(f"✅ Successfully popped last item: {last_item.get('role', 'unknown')}")
        
        # Clear session
        await session.clear_session()
        logger.info(f"✅ Session cleared successfully")
        
        # Verify empty
        final_items = await session.get_items()
        logger.info(f"📚 Session has {len(final_items)} items after clear")
        
    except Exception as e:
        logger.error(f"❌ Session persistence test failed: {e}")
        return False
    
    # Step 6: Performance comparison
    logger.info("\n📊 PERFORMANCE ANALYSIS:")
    logger.info(f"  Without session: {result1.execution_time:.2f}s")
    logger.info(f"  With session (task 1): {result2.execution_time:.2f}s")
    logger.info(f"  With session (task 2 with context): {result3.execution_time:.2f}s")
    
    # Success criteria
    all_tasks_completed = all(r.status == TaskStatus.COMPLETED for r in [result1, result2, result3])
    session_working = len(session_items_after) > len(session_items)
    
    success = all_tasks_completed and session_working
    
    logger.info(f"\n🏆 TEST RESULT: {'✅ SUCCESS' if success else '❌ FAILURE'}")
    logger.info(f"  - All tasks completed: {'✅' if all_tasks_completed else '❌'}")
    logger.info(f"  - Session accumulating items: {'✅' if session_working else '❌'}")
    
    # Save test results
    test_results = {
        "timestamp": datetime.now().isoformat(),
        "workspace_id": workspace_id,
        "agent_id": agent_id,
        "test_passed": success,
        "execution_times": {
            "without_session": result1.execution_time,
            "with_session_task1": result2.execution_time,
            "with_session_task2": result3.execution_time
        },
        "session_stats": {
            "items_after_task1": len(session_items),
            "items_after_task2": len(session_items_after),
            "persistence_test_passed": last_item is not None
        }
    }
    
    with open(f"sdk_session_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        json.dump(test_results, f, indent=2)
    
    return success

if __name__ == "__main__":
    # Set required environment variables for test
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
    os.environ["SUPABASE_URL"] = os.getenv("SUPABASE_URL", "")
    os.environ["SUPABASE_KEY"] = os.getenv("SUPABASE_KEY", "")
    
    success = asyncio.run(test_session_integration())
    
    if success:
        logger.info("\n✅ SDK SESSION INTEGRATION TEST PASSED")
        logger.info("The specialist agent now supports SDK native sessions for memory persistence!")
    else:
        logger.info("\n❌ SDK SESSION INTEGRATION TEST FAILED")
        
    sys.exit(0 if success else 1)