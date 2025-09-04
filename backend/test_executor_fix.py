#!/usr/bin/env python3
"""Test script to verify the executor infinite loop fix"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the executor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from executor import TaskExecutor

async def test_adaptive_loop():
    """Test the adaptive execution loop behavior"""
    logger.info("Starting test of adaptive execution loop...")
    
    # Create executor instance
    executor = TaskExecutor()
    
    # Check if adaptive metrics are initialized
    if not hasattr(executor, 'executor_metrics'):
        logger.error("❌ FAILED: executor_metrics not initialized in __init__!")
        return False
        
    if not hasattr(executor, 'adaptive_intervals'):
        logger.error("❌ FAILED: adaptive_intervals not initialized in __init__!")
        return False
        
    logger.info(f"✅ Adaptive metrics initialized properly")
    logger.info(f"   Initial load level: {executor.executor_metrics['load_level']}")
    logger.info(f"   Adaptive intervals: {executor.adaptive_intervals}")
    
    # Start the executor
    await executor.start()
    
    # Let it run for 30 seconds to observe behavior
    logger.info("Monitoring executor behavior for 30 seconds...")
    await asyncio.sleep(30)
    
    # Check metrics
    logger.info(f"📊 Final metrics:")
    logger.info(f"   Loop count: {executor.executor_metrics['loop_count']}")
    logger.info(f"   Avg loop time: {executor.executor_metrics.get('avg_loop_time', 0):.2f}s")
    logger.info(f"   Current load level: {executor.executor_metrics['load_level']}")
    
    # Stop the executor
    await executor.stop()
    
    # Verify no excessive looping
    if executor.executor_metrics['loop_count'] > 10:
        logger.error(f"❌ FAILED: Too many loops in 30 seconds: {executor.executor_metrics['loop_count']}")
        logger.error("   This indicates the infinite loop issue is NOT fixed!")
        return False
    else:
        logger.info(f"✅ SUCCESS: Loop count reasonable: {executor.executor_metrics['loop_count']}")
        logger.info("   The infinite loop issue appears to be FIXED!")
        return True

async def main():
    """Main test function"""
    try:
        success = await test_adaptive_loop()
        if success:
            logger.info("🎉 TEST PASSED: Executor infinite loop fix verified!")
            sys.exit(0)
        else:
            logger.error("💥 TEST FAILED: Executor still has issues!")
            sys.exit(1)
    except Exception as e:
        logger.error(f"💥 TEST ERROR: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())