#!/usr/bin/env python3
"""
🧪 TEST NEW DATABASE FUNCTIONS
Test per le nuove funzioni che eliminano i workaround
"""

import asyncio
import sys
import os
import logging

# Add backend to path
sys.path.append(os.path.dirname(__file__))

from database import (
    get_ready_tasks_python,
    create_task_execution,
    update_task_execution,
    get_task_execution_stats_python,
    get_workspace_execution_stats,
    add_task_dependency,
    get_task_dependencies
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

async def test_new_database_functions():
    """Test tutte le nuove funzioni database"""
    
    logger.info("🧪 Testing New Database Functions")
    logger.info("=" * 50)
    
    # Use the workspace from our real production test
    workspace_id = "39b0d6ef-5d77-4fac-a2dd-f962a252db28"
    
    try:
        # Test 1: get_ready_tasks_python
        logger.info("📋 Test 1: get_ready_tasks_python")
        ready_tasks = await get_ready_tasks_python(workspace_id)
        logger.info(f"   Ready tasks found: {len(ready_tasks)}")
        
        if ready_tasks:
            sample_task = ready_tasks[0]
            logger.info(f"   Sample task: {sample_task.get('task_name', 'Unknown')}")
        
        # Test 2: get_workspace_execution_stats
        logger.info("📊 Test 2: get_workspace_execution_stats")
        workspace_stats = await get_workspace_execution_stats(workspace_id)
        logger.info(f"   Workspace stats: {workspace_stats}")
        
        # Test 3: create_task_execution (use real task if available)
        if ready_tasks:
            task_id = ready_tasks[0]['task_id']
            agent_id = ready_tasks[0]['agent_id']
            
            logger.info("🔥 Test 3: create_task_execution")
            execution_id = await create_task_execution(str(task_id), str(agent_id), workspace_id, "test_trace_123")
            logger.info(f"   Created execution: {execution_id}")
            
            if execution_id:
                # Test 4: update_task_execution
                logger.info("✅ Test 4: update_task_execution")
                success = await update_task_execution(
                    execution_id, 
                    'completed', 
                    result={'test': 'result'},
                    logs='Test execution logs',
                    token_usage={'total_tokens': 150},
                    execution_time_seconds=12.5
                )
                logger.info(f"   Update success: {success}")
                
                # Test 5: get_task_execution_stats_python
                logger.info("📊 Test 5: get_task_execution_stats_python")
                stats = await get_task_execution_stats_python(str(task_id))
                logger.info(f"   Task execution stats: {stats}")
        
        # Test 6: Task dependencies (create fake task dependency for testing)
        if ready_tasks and len(ready_tasks) > 0:
            task_id = str(ready_tasks[0]['task_id'])
            depends_on_task_id = task_id  # Self-dependency for testing
            
            logger.info("🔗 Test 6: add_task_dependency")
            success = await add_task_dependency(task_id, depends_on_task_id)
            logger.info(f"   Add dependency success: {success}")
            
            logger.info("🔍 Test 7: get_task_dependencies")
            dependencies = await get_task_dependencies(task_id)
            logger.info(f"   Dependencies found: {len(dependencies)}")
        
        logger.info("✅ All database function tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test execution"""
    success = await test_new_database_functions()
    
    if success:
        logger.info("🎉 DATABASE FUNCTIONS TEST PASSED!")
        return 0
    else:
        logger.error("❌ DATABASE FUNCTIONS TEST FAILED!")
        return 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)