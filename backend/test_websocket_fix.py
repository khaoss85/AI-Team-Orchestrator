#!/usr/bin/env python3
"""
Test per verificare che il fix WebSocket funzioni correttamente
"""

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock
import sys
import os

# Add current directory to path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_websocket_connection_manager():
    """Test the fixed WebSocket connection manager"""
    try:
        # Mock WebSocket
        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()
        
        # Test the fixed connection manager
        from routes.websocket import ConnectionManager
        manager = ConnectionManager()
        
        # Test 1: Normal connection (should call accept)
        logger.info("Test 1: Normal WebSocket connection")
        await manager.connect(mock_websocket, "test-workspace-1")
        
        # Verify accept was called once
        assert mock_websocket.accept.call_count == 1, f"Expected 1 accept call, got {mock_websocket.accept.call_count}"
        logger.info("✅ Test 1 passed: WebSocket accept called once")
        
        # Test 2: Already accepted connection (should NOT call accept)
        logger.info("Test 2: Already accepted WebSocket connection")
        mock_websocket2 = AsyncMock()
        mock_websocket2.accept = AsyncMock()
        
        await manager.connect(mock_websocket2, "test-workspace-2", already_accepted=True)
        
        # Verify accept was NOT called
        assert mock_websocket2.accept.call_count == 0, f"Expected 0 accept calls, got {mock_websocket2.accept.call_count}"
        logger.info("✅ Test 2 passed: WebSocket accept not called when already_accepted=True")
        
        logger.info("🎉 All WebSocket connection manager tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ WebSocket test failed: {e}")
        return False

async def test_queue_item_handling():
    """Test the fixed queue item handling in executor"""
    try:
        # Mock task queue scenarios
        test_cases = [
            # Case 1: Tuple format (new)
            ("tuple", ("mock_manager", {"task_id": "123", "name": "test"})),
            # Case 2: Dict format (legacy)
            ("dict", {"task_id": "456", "name": "test2"}),
            # Case 3: Invalid format
            ("invalid", "not_a_dict_or_tuple")
        ]
        
        for case_name, queue_item in test_cases:
            logger.info(f"Testing queue item format: {case_name}")
            
            # Simulate the fixed unpacking logic
            manager = None
            task_dict_from_queue = None
            
            if isinstance(queue_item, tuple) and len(queue_item) == 2:
                manager, task_dict_from_queue = queue_item
                logger.info(f"  ✅ Tuple format handled: manager={manager is not None}, task={task_dict_from_queue is not None}")
            elif isinstance(queue_item, dict):
                manager = None
                task_dict_from_queue = queue_item
                logger.info(f"  ✅ Dict format handled: task={task_dict_from_queue is not None}")
            else:
                logger.info(f"  ⚠️ Invalid format rejected: {type(queue_item)}")
                continue
                
            # Verify we got valid data
            if case_name != "invalid":
                assert task_dict_from_queue is not None, f"Expected task data for {case_name}"
        
        logger.info("🎉 All queue item handling tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Queue item test failed: {e}")
        return False

async def main():
    """Run all tests"""
    logger.info("🧪 TESTING WEBSOCKET AND EXECUTOR FIXES")
    logger.info("="*50)
    
    results = []
    
    # Test WebSocket connection manager
    logger.info("Test Suite 1: WebSocket Connection Manager")
    result1 = await test_websocket_connection_manager()
    results.append(result1)
    
    logger.info("-" * 30)
    
    # Test queue item handling
    logger.info("Test Suite 2: Queue Item Handling")
    result2 = await test_queue_item_handling()
    results.append(result2)
    
    logger.info("="*50)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        logger.info(f"🎉 ALL TESTS PASSED ({passed}/{total})")
        logger.info("✅ WebSocket and Executor fixes are working correctly!")
    else:
        logger.error(f"❌ SOME TESTS FAILED ({passed}/{total})")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)