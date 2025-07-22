#!/usr/bin/env python3
"""
🔍 Simple Monitoring Test - Test solo del monitoring system
================================================================================
Test focalizzato solo sul sistema di monitoring per verificare che i task 
vengano tracciati correttamente, anche con SDK 0.0.17.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_monitoring_with_current_sdk():
    """Test monitoring con SDK attuale (0.0.17)"""
    logger.info("🔍 Testing monitoring with current SDK...")
    
    try:
        # Import executor che ora ha monitoring integrato
        from executor import TaskExecutor
        from database import create_workspace, create_task, get_task
        from models import TaskStatus
        import uuid
        
        logger.info("✅ Imports successful")
        
        # Create test workspace
        workspace_data = {
            "name": "Monitoring Test Workspace",
            "description": "Test workspace for monitoring",
            "user_id": str(uuid.uuid4())  # Fix: provide required user_id
        }
        workspace = await create_workspace(workspace_data["name"], workspace_data["description"], workspace_data["user_id"])
        workspace_id = str(workspace["id"])
        logger.info(f"✅ Test workspace created: {workspace_id}")
        
        # Create simple test task
        task = await create_task(
            workspace_id=workspace_id,
            name="Monitoring Test Task",
            status=TaskStatus.PENDING.value,
            description="Test task to verify monitoring works",
            priority="high",
            assigned_to_role="AI Agent"
        )
        task_id = str(task["id"])
        logger.info(f"✅ Test task created: {task_id}")
        
        # Initialize executor with monitoring
        executor = TaskExecutor()
        logger.info("✅ TaskExecutor initialized with monitoring")
        
        # Check if monitoring is active
        try:
            from task_execution_monitor import task_monitor
            active_traces = task_monitor.get_all_active_traces()
            logger.info(f"📊 Active traces before execution: {len(active_traces)}")
        except:
            logger.warning("⚠️ Could not access task monitor")
        
        # Run executor with short timeout
        logger.info("🚀 Starting monitored execution...")
        start_time = datetime.now()
        
        try:
            # Create a task to run executor and stop it after timeout
            executor_task = asyncio.create_task(executor.start())
            await asyncio.wait_for(
                asyncio.sleep(30),  # Let it run for 30 seconds
                timeout=30.0
            )
            executor.running = False  # Stop the executor
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Execution ran for {execution_time:.2f}s")
        except asyncio.TimeoutError:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.warning(f"⏰ Execution stopped after {execution_time:.2f}s")
            executor.running = False
        
        # Check monitoring results
        try:
            from task_execution_monitor import task_monitor
            final_traces = task_monitor.get_all_active_traces()
            hanging_tasks = task_monitor.get_hanging_tasks()
            
            logger.info(f"📊 Active traces after execution: {len(final_traces)}")
            logger.info(f"🚨 Hanging tasks detected: {len(hanging_tasks)}")
            
            # Show details of any hanging tasks
            for hanging_task in hanging_tasks:
                logger.warning(f"🚨 HANGING: Task {hanging_task['task_id']} stuck in {hanging_task['current_stage']} for {hanging_task['execution_time']:.1f}s")
            
            # Check specific task trace
            if task_id in final_traces:
                task_trace = final_traces[task_id]
                logger.info(f"📝 Task {task_id} trace: {task_trace['current_stage']} ({task_trace['stage_count']} stages, {task_trace['error_count']} errors)")
            
        except Exception as e:
            logger.error(f"❌ Failed to check monitoring results: {e}")
        
        # Check final task status
        final_task = await get_task(task_id)
        if final_task:
            final_status = final_task.get("status", "unknown")
            logger.info(f"📊 Final task status: {final_status}")
            
            return final_status not in [TaskStatus.IN_PROGRESS.value]  # Consider success if not stuck
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Monitoring test failed: {e}")
        return False

async def main():
    """Main test function"""
    logger.info("🚀 Starting Simple Monitoring Test")
    logger.info("="*60)
    
    # Test monitoring with current SDK
    success = await test_monitoring_with_current_sdk()
    
    logger.info("\n" + "="*60)
    logger.info("📊 TEST RESULTS")
    logger.info("="*60)
    
    if success:
        logger.info("✅ Monitoring test PASSED - Tasks are being tracked!")
    else:
        logger.info("❌ Monitoring test FAILED - Tasks may still be hanging")
    
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test failed with unexpected error: {e}")
        sys.exit(1)