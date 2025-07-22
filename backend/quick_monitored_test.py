#!/usr/bin/env python3
"""
🔍 Quick Monitored Test - Verifica SDK 0.1.0 con task execution monitoring
================================================================================
Test veloce per verificare se l'aggiornamento a openai-agents 0.1.0 e il 
monitoring hanno risolto i problemi di task execution.
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'monitored_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

async def test_sdk_availability():
    """Test se SQLiteSession è ora disponibile con SDK 0.1.0"""
    logger.info("🔍 Testing SDK 0.1.0 availability...")
    
    try:
        from agents import SQLiteSession, Runner, Agent
        logger.info("✅ SQLiteSession available in agents SDK 0.1.0")
        
        # Test session creation
        session = SQLiteSession(db_path="test_session.db")
        logger.info("✅ SQLiteSession creation successful")
        
        return True
    except ImportError as e:
        logger.error(f"❌ SDK import failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Session creation failed: {e}")
        return False

async def test_task_monitoring():
    """Test task execution monitoring system"""
    logger.info("🔍 Testing task execution monitoring...")
    
    try:
        from task_execution_monitor import (
            task_monitor, ExecutionStage, 
            trace_task_start, trace_stage, 
            trace_error, trace_task_complete,
            start_monitoring
        )
        logger.info("✅ Task monitoring import successful")
        
        # Start monitoring
        await start_monitoring()
        logger.info("✅ Monitoring started")
        
        # Test trace operations
        test_task_id = "test_task_123"
        test_workspace_id = "test_workspace_456"
        
        # Start trace
        trace_task_start(test_task_id, test_workspace_id, "test_agent")
        logger.info("✅ Task trace started")
        
        # Test stage transitions
        trace_stage(test_task_id, ExecutionStage.AGENT_ASSIGNED, "Test agent assigned")
        trace_stage(test_task_id, ExecutionStage.RUNNER_START, "Test runner starting")
        trace_stage(test_task_id, ExecutionStage.RUNNER_COMPLETED, "Test completed")
        logger.info("✅ Stage transitions recorded")
        
        # Complete trace
        trace_task_complete(test_task_id, success=True)
        logger.info("✅ Task trace completed")
        
        # Get trace summary
        summary = task_monitor.get_trace_summary(test_task_id)
        if summary:
            logger.info(f"✅ Trace summary retrieved: {len(summary.get('stages', []))} stages")
        else:
            logger.warning("⚠️ No trace summary found")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Task monitoring test failed: {e}")
        return False

async def test_session_adapter():
    """Test orchestrator session adapter with SDK 0.1.0"""
    logger.info("🔍 Testing orchestrator session adapter...")
    
    try:
        from services.orchestrator_session_adapter import orchestrator_session_adapter
        logger.info("✅ Session adapter import successful")
        
        # Test session creation
        session = await orchestrator_session_adapter.get_agent_session(
            agent_id="test_agent_789",
            workspace_id="test_workspace_456",
            task_id="test_task_123"
        )
        
        if session:
            logger.info("✅ SDK session created successfully")
        else:
            logger.warning("⚠️ Session creation returned None (fallback mode)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Session adapter test failed: {e}")
        return False

async def test_simple_task_execution():
    """Test semplice task execution per verificare che non ci siano più hanging"""
    logger.info("🔍 Testing simple task execution...")
    
    try:
        # Import necessary components
        from database import create_workspace, create_task, get_task
        from models import TaskStatus
        from executor import TaskExecutor
        import uuid
        
        # Create test workspace
        workspace_data = {
            "name": "Test Monitoring Workspace",
            "description": "Test workspace for monitoring verification"
        }
        workspace = await create_workspace(workspace_data)
        workspace_id = str(workspace["id"])
        logger.info(f"✅ Test workspace created: {workspace_id}")
        
        # Create simple test task
        task_data = {
            "workspace_id": workspace_id,
            "name": "Simple Test Task",
            "description": "Test task for monitoring verification",
            "status": TaskStatus.PENDING.value,
            "priority": "high",
            "assigned_to_role": "AI Agent"
        }
        task = await create_task(task_data)
        task_id = str(task["id"])
        logger.info(f"✅ Test task created: {task_id}")
        
        # Initialize task executor with monitoring
        executor = TaskExecutor()
        logger.info("✅ TaskExecutor initialized with monitoring")
        
        # Run task execution with timeout (shorter than before)
        logger.info("🚀 Starting monitored task execution...")
        start_time = datetime.now()
        
        try:
            # Run with 2 minute timeout instead of 5
            await asyncio.wait_for(
                executor.execute_pending_tasks_cycle(),
                timeout=120.0
            )
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Task execution cycle completed in {execution_time:.2f}s")
            
        except asyncio.TimeoutError:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.warning(f"⏰ Task execution timed out after {execution_time:.2f}s")
        
        # Check final task status
        final_task = await get_task(task_id)
        if final_task:
            final_status = final_task.get("status", "unknown")
            logger.info(f"📊 Final task status: {final_status}")
            
            if final_status == TaskStatus.COMPLETED.value:
                logger.info("✅ Task completed successfully!")
                return True
            elif final_status == TaskStatus.IN_PROGRESS.value:
                logger.warning("⚠️ Task still in progress (potential hanging)")
                return False
            else:
                logger.info(f"ℹ️ Task ended with status: {final_status}")
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Task execution test failed: {e}")
        return False

async def main():
    """Main test function"""
    logger.info("🚀 Starting Quick Monitored Test for SDK 0.1.0")
    logger.info("="*80)
    
    results = {}
    
    # Test 1: SDK Availability
    logger.info("\n1️⃣ Testing SDK 0.1.0 availability...")
    results["sdk_available"] = await test_sdk_availability()
    
    # Test 2: Task Monitoring
    logger.info("\n2️⃣ Testing task execution monitoring...")
    results["monitoring_works"] = await test_task_monitoring()
    
    # Test 3: Session Adapter
    logger.info("\n3️⃣ Testing session adapter...")
    results["adapter_works"] = await test_session_adapter()
    
    # Test 4: Simple Task Execution
    logger.info("\n4️⃣ Testing simple task execution...")
    results["task_execution"] = await test_simple_task_execution()
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("="*80)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{test_name:20}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    logger.info(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        logger.info("🎉 All tests passed! SDK 0.1.0 integration successful!")
    elif passed_tests >= total_tests * 0.75:
        logger.info("🟡 Most tests passed. Some issues remain but progress made.")
    else:
        logger.info("🔴 Multiple test failures. Further investigation needed.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit_code = 0 if success else 1
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test failed with unexpected error: {e}")
        sys.exit(1)