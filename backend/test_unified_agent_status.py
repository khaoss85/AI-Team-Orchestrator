#!/usr/bin/env python3
"""
🎯 UNIFIED AGENT STATUS SYSTEM TEST

Tests the complete integration of the AgentStatusManager across all components.
This verifies Fix #3: Unified Agent Status Management implementation.
"""

import asyncio
import logging
import sys
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all unified agent status components can be imported"""
    try:
        from services.agent_status_manager import agent_status_manager, UnifiedAgentStatus, AgentInfo
        from services.workspace_health_manager import workspace_health_manager
        from executor import task_executor
        from automated_goal_monitor import automated_goal_monitor
        
        logger.info("✅ All unified status components imported successfully")
        return True
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False

def test_unified_status_definitions():
    """Test unified status definitions"""
    try:
        from services.agent_status_manager import UnifiedAgentStatus
        
        expected_statuses = ["available", "active", "busy", "inactive", "failed", "terminated"]
        actual_statuses = [status.value for status in UnifiedAgentStatus]
        
        assert set(expected_statuses) == set(actual_statuses), f"Status mismatch: expected {expected_statuses}, got {actual_statuses}"
        
        logger.info(f"✅ Unified status definitions correct: {actual_statuses}")
        return True
    except Exception as e:
        logger.error(f"❌ Unified status test failed: {e}")
        return False

async def test_agent_status_manager():
    """Test AgentStatusManager functionality"""
    try:
        from services.agent_status_manager import agent_status_manager
        
        # Test initialization
        assert agent_status_manager is not None, "AgentStatusManager not initialized"
        
        # Test status normalization
        test_status = agent_status_manager._normalize_status("available")
        assert test_status.value == "available", f"Status normalization failed: {test_status.value}"
        
        logger.info("✅ AgentStatusManager functionality verified")
        return True
    except Exception as e:
        logger.error(f"❌ AgentStatusManager test failed: {e}")
        return False

async def test_workspace_health_manager():
    """Test WorkspaceHealthManager functionality"""
    try:
        from services.workspace_health_manager import workspace_health_manager
        
        # Test initialization
        assert workspace_health_manager is not None, "WorkspaceHealthManager not initialized"
        
        # Test dynamic task limit calculation (fallback to default)
        dynamic_limit = await workspace_health_manager.get_dynamic_task_limit("test-workspace-id")
        assert dynamic_limit >= 20, f"Dynamic limit too low: {dynamic_limit}"
        
        logger.info(f"✅ WorkspaceHealthManager functionality verified (dynamic limit: {dynamic_limit})")
        return True
    except Exception as e:
        logger.error(f"❌ WorkspaceHealthManager test failed: {e}")
        return False

def test_executor_integration():
    """Test that executor has AgentStatusManager integration"""
    try:
        from executor import task_executor, AGENT_STATUS_MANAGER_AVAILABLE, agent_status_manager
        
        # Verify AgentStatusManager is available in executor
        assert AGENT_STATUS_MANAGER_AVAILABLE == True, "AgentStatusManager not available in executor"
        assert agent_status_manager is not None, "AgentStatusManager not imported in executor"
        
        logger.info("✅ Executor integration verified")
        return True
    except Exception as e:
        logger.error(f"❌ Executor integration test failed: {e}")
        return False

def test_goal_monitor_integration():
    """Test that goal monitor has AgentStatusManager integration"""
    try:
        from automated_goal_monitor import automated_goal_monitor, AGENT_STATUS_MANAGER_AVAILABLE, agent_status_manager
        
        # Verify AgentStatusManager is available in goal monitor
        assert AGENT_STATUS_MANAGER_AVAILABLE == True, "AgentStatusManager not available in goal monitor"
        assert agent_status_manager is not None, "AgentStatusManager not imported in goal monitor"
        
        logger.info("✅ Goal monitor integration verified")
        return True
    except Exception as e:
        logger.error(f"❌ Goal monitor integration test failed: {e}")
        return False

async def run_unified_status_tests() -> Dict[str, Any]:
    """Run all unified agent status tests"""
    logger.info("🎯 STARTING UNIFIED AGENT STATUS SYSTEM TESTS")
    
    results = {
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "test_results": {}
    }
    
    tests = [
        ("imports", test_imports),
        ("status_definitions", test_unified_status_definitions),
        ("agent_status_manager", test_agent_status_manager),
        ("workspace_health_manager", test_workspace_health_manager),
        ("executor_integration", test_executor_integration),
        ("goal_monitor_integration", test_goal_monitor_integration)
    ]
    
    for test_name, test_func in tests:
        results["total_tests"] += 1
        logger.info(f"🧪 Running test: {test_name}")
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                success = await test_func()
            else:
                success = test_func()
            
            if success:
                results["passed_tests"] += 1
                results["test_results"][test_name] = "PASSED"
                logger.info(f"✅ Test {test_name}: PASSED")
            else:
                results["failed_tests"] += 1
                results["test_results"][test_name] = "FAILED"
                logger.error(f"❌ Test {test_name}: FAILED")
                
        except Exception as e:
            results["failed_tests"] += 1
            results["test_results"][test_name] = f"ERROR: {e}"
            logger.error(f"💥 Test {test_name}: ERROR - {e}")
    
    # Summary
    logger.info("🎯 UNIFIED AGENT STATUS TESTS SUMMARY")
    logger.info(f"📊 Total: {results['total_tests']}, Passed: {results['passed_tests']}, Failed: {results['failed_tests']}")
    
    if results["failed_tests"] == 0:
        logger.info("🎉 ALL UNIFIED AGENT STATUS TESTS PASSED! ✅")
        results["overall_status"] = "SUCCESS"
    else:
        logger.error(f"⚠️ {results['failed_tests']} tests failed")
        results["overall_status"] = "FAILED"
    
    return results

if __name__ == "__main__":
    # Run tests
    results = asyncio.run(run_unified_status_tests())
    
    # Exit with appropriate code
    if results["overall_status"] == "SUCCESS":
        sys.exit(0)
    else:
        sys.exit(1)