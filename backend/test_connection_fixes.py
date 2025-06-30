#!/usr/bin/env python3
"""
Test per verificare che i fix per WebSocket e Task Deduplication funzionino
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

async def test_task_deduplication_fixes():
    """Test che i fix per None handling nel task deduplication funzionino"""
    logger.info("🧪 Testing Task Deduplication None handling fixes")
    
    try:
        from services.task_deduplication_manager import TaskDeduplicationManager
        
        dedup_manager = TaskDeduplicationManager()
        
        # Test con dati che potrebbero avere None
        test_cases = [
            # Case 1: Dati normali
            {"name": "Test Task", "description": "Test Description", "assigned_to_role": "developer"},
            # Case 2: Name è None
            {"name": None, "description": "Test Description", "assigned_to_role": "developer"},
            # Case 3: Description è None
            {"name": "Test Task", "description": None, "assigned_to_role": "developer"},
            # Case 4: Assigned role è None
            {"name": "Test Task", "description": "Test Description", "assigned_to_role": None},
            # Case 5: Tutti None
            {"name": None, "description": None, "assigned_to_role": None},
            # Case 6: Valori mancanti (non presenti nel dict)
            {},
        ]
        
        for i, task_data in enumerate(test_cases):
            logger.info(f"  Testing case {i+1}: {task_data}")
            try:
                # Test hash creation (dove avveniva l'errore)
                hash_result = dedup_manager._create_task_hash(task_data)
                logger.info(f"    ✅ Hash created successfully: {hash_result[:16]}...")
                
                # Test similarity comparison method that exists
                is_similar = dedup_manager._are_urgent_tasks_similar("Task 1", "Task 2")
                logger.info(f"    ✅ Similarity check passed: {is_similar}")
                
            except Exception as e:
                logger.error(f"    ❌ Case {i+1} failed: {e}")
                return False
        
        logger.info("✅ All task deduplication None handling tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Task deduplication test setup failed: {e}")
        return False

async def test_websocket_error_handling():
    """Test che i fix per WebSocket error handling funzionino"""
    logger.info("🧪 Testing WebSocket error handling fixes")
    
    try:
        from utils.websocket_health_manager import WebSocketHealthManager
        from dataclasses import dataclass
        from enum import Enum
        
        # Mock WebSocket che simula stati diversi
        mock_websocket = MagicMock()
        
        # Test 1: WebSocket normale
        logger.info("  Test 1: Normal WebSocket")
        mock_websocket.client_state.name = "CONNECTED"
        mock_websocket.send_json = AsyncMock()
        
        manager = WebSocketHealthManager(heartbeat_interval=1, max_heartbeat_failures=2)
        
        # Simula connection info
        from utils.websocket_health_manager import ConnectionInfo, ConnectionState
        connection_info = ConnectionInfo(
            websocket=mock_websocket,
            workspace_id="test-workspace",
            client_id="test-client-1"
        )
        
        # Test heartbeat normale
        await manager._send_heartbeat("test-client-1", connection_info)
        assert mock_websocket.send_json.called, "WebSocket send_json should be called"
        logger.info("    ✅ Normal heartbeat passed")
        
        # Test 2: WebSocket disconnesso
        logger.info("  Test 2: Disconnected WebSocket")
        mock_websocket_disconnected = MagicMock()
        mock_websocket_disconnected.client_state.name = "DISCONNECTED"
        mock_websocket_disconnected.send_json = AsyncMock()
        
        connection_info_2 = ConnectionInfo(
            websocket=mock_websocket_disconnected,
            workspace_id="test-workspace",
            client_id="test-client-2"
        )
        
        # Registra la connessione per il test
        manager.connections["test-client-2"] = connection_info_2
        
        # Test heartbeat su connessione disconnessa
        await manager._send_heartbeat("test-client-2", connection_info_2)
        assert not mock_websocket_disconnected.send_json.called, "Should not send to disconnected WebSocket"
        logger.info("    ✅ Disconnected WebSocket handling passed")
        
        # Test 3: WebSocket con errore
        logger.info("  Test 3: WebSocket with send error")
        mock_websocket_error = MagicMock()
        mock_websocket_error.client_state.name = "CONNECTED"
        mock_websocket_error.send_json = AsyncMock(side_effect=Exception("Connection lost"))
        
        connection_info_3 = ConnectionInfo(
            websocket=mock_websocket_error,
            workspace_id="test-workspace",
            client_id="test-client-3"
        )
        
        manager.connections["test-client-3"] = connection_info_3
        
        # Test heartbeat con errore
        await manager._send_heartbeat("test-client-3", connection_info_3)
        assert connection_info_3.heartbeat_failures > 0, "Should record heartbeat failure"
        logger.info("    ✅ WebSocket error handling passed")
        
        logger.info("✅ All WebSocket error handling tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ WebSocket test failed: {e}")
        return False

async def main():
    """Run all connection fix tests"""
    logger.info("🔧 TESTING CONNECTION FIXES")
    logger.info("="*50)
    
    results = []
    
    # Test Task Deduplication fixes
    logger.info("Test Suite 1: Task Deduplication None Handling")
    result1 = await test_task_deduplication_fixes()
    results.append(result1)
    
    logger.info("-" * 30)
    
    # Test WebSocket error handling fixes
    logger.info("Test Suite 2: WebSocket Error Handling")
    result2 = await test_websocket_error_handling()
    results.append(result2)
    
    logger.info("="*50)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        logger.info(f"🎉 ALL TESTS PASSED ({passed}/{total})")
        logger.info("✅ Connection fixes are working correctly!")
    else:
        logger.error(f"❌ SOME TESTS FAILED ({passed}/{total})")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)