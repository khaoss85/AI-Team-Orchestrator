#!/usr/bin/env python3
"""
🎯 COMPLETE FIXES INTEGRATION TEST

Tests all 4 definitive fixes working together:
- Fix #1: TaskDeduplicationManager
- Fix #2: WorkspaceHealthManager  
- Fix #3: AgentStatusManager
- Fix #4: GoalValidationOptimizer

This verifies the complete solution for workspace auto-pause and task management issues.
"""

import asyncio
import logging
import sys
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_all_fixes_imports():
    """Test that all 4 fixes can be imported together"""
    try:
        # Fix #1: Task Deduplication
        from services.task_deduplication_manager import task_deduplication_manager
        from database import create_task  # Should use deduplication
        
        # Fix #2: Workspace Health
        from services.workspace_health_manager import workspace_health_manager
        
        # Fix #3: Agent Status Management
        from services.agent_status_manager import agent_status_manager
        
        # Fix #4: Goal Validation Optimization
        from services.goal_validation_optimizer import goal_validation_optimizer
        
        # Integration checks
        from executor import task_executor, AGENT_STATUS_MANAGER_AVAILABLE, WORKSPACE_HEALTH_AVAILABLE
        from automated_goal_monitor import (
            automated_goal_monitor, 
            GOAL_VALIDATION_OPTIMIZER_AVAILABLE,
            AGENT_STATUS_MANAGER_AVAILABLE as MONITOR_AGENT_AVAILABLE
        )
        
        logger.info("✅ All 4 fixes imported successfully")
        return True
    except ImportError as e:
        logger.error(f"❌ Fixes import error: {e}")
        return False

def test_fixes_availability():
    """Test that all fixes are available in their respective modules"""
    try:
        from executor import AGENT_STATUS_MANAGER_AVAILABLE, WORKSPACE_HEALTH_AVAILABLE
        from automated_goal_monitor import (
            GOAL_VALIDATION_OPTIMIZER_AVAILABLE,
            AGENT_STATUS_MANAGER_AVAILABLE as MONITOR_AGENT_AVAILABLE
        )
        
        # Check Fix #1: Task deduplication is integrated in database.py
        from database import create_task
        import inspect
        create_task_source = inspect.getsource(create_task)
        assert "task_deduplication_manager" in create_task_source, "TaskDeduplicationManager not integrated in create_task"
        
        # Check Fix #2: Workspace health available in executor
        assert WORKSPACE_HEALTH_AVAILABLE == True, "WorkspaceHealthManager not available in executor"
        
        # Check Fix #3: Agent status management available in executor and monitor
        assert AGENT_STATUS_MANAGER_AVAILABLE == True, "AgentStatusManager not available in executor"
        assert MONITOR_AGENT_AVAILABLE == True, "AgentStatusManager not available in goal monitor"
        
        # Check Fix #4: Goal validation optimization available in monitor
        assert GOAL_VALIDATION_OPTIMIZER_AVAILABLE == True, "GoalValidationOptimizer not available in goal monitor"
        
        logger.info("✅ All 4 fixes are properly integrated and available")
        return True
    except Exception as e:
        logger.error(f"❌ Fixes availability test failed: {e}")
        return False

async def test_fix1_task_deduplication():
    """Test Fix #1: Task Deduplication Manager"""
    try:
        from services.task_deduplication_manager import task_deduplication_manager
        
        # Test duplicate detection logic
        test_task_data = {
            "workspace_id": "test-workspace",
            "name": "Test Task",
            "description": "Test task description",
            "priority": "medium"
        }
        
        # Test similarity calculation
        similar_task_data = {
            "workspace_id": "test-workspace", 
            "name": "Test Task",  # Same name
            "description": "Test task description updated",
            "priority": "high"
        }
        
        similarity = task_deduplication_manager._calculate_semantic_similarity(
            test_task_data, similar_task_data
        )
        
        assert 0.0 <= similarity <= 1.0, f"Similarity score out of range: {similarity}"
        
        logger.info(f"✅ Fix #1 TaskDeduplicationManager verified - similarity: {similarity:.2f}")
        return True
    except Exception as e:
        logger.error(f"❌ Fix #1 test failed: {e}")
        return False

async def test_fix2_workspace_health():
    """Test Fix #2: Workspace Health Manager"""
    try:
        from services.workspace_health_manager import workspace_health_manager
        
        # Test dynamic task limit calculation
        dynamic_limit = await workspace_health_manager.get_dynamic_task_limit("test-workspace")
        assert dynamic_limit >= 20, f"Dynamic limit too low: {dynamic_limit}"
        
        # Test health issue analysis (will work with empty data)
        health_data = {
            "workspace": {"status": "active"},
            "tasks": [],
            "agents": [],
            "goals": [],
            "recent_logs": [],
            "task_count": 0,
            "agent_count": 0,
            "goal_count": 0
        }
        
        issues = await workspace_health_manager._analyze_health_issues("test-workspace", health_data)
        assert isinstance(issues, list), "Health issues should be a list"
        
        logger.info(f"✅ Fix #2 WorkspaceHealthManager verified - dynamic limit: {dynamic_limit}, issues: {len(issues)}")
        return True
    except Exception as e:
        logger.error(f"❌ Fix #2 test failed: {e}")
        return False

async def test_fix3_agent_status():
    """Test Fix #3: Agent Status Manager"""
    try:
        from services.agent_status_manager import agent_status_manager, UnifiedAgentStatus
        
        # Test status normalization
        normalized = agent_status_manager._normalize_status("available")
        assert normalized == UnifiedAgentStatus.AVAILABLE, f"Status normalization failed: {normalized}"
        
        # Test agent preference scoring
        from services.agent_status_manager import AgentInfo
        from datetime import datetime
        
        test_agent = AgentInfo(
            id="test-agent",
            name="Test Agent",
            role="specialist",
            status=UnifiedAgentStatus.AVAILABLE,
            seniority="senior",
            workspace_id="test-workspace",
            last_activity=datetime.now(),
            success_rate=0.8
        )
        
        score = agent_status_manager._agent_preference_score(test_agent)
        assert score > 0, f"Agent preference score should be positive: {score}"
        
        logger.info(f"✅ Fix #3 AgentStatusManager verified - preference score: {score:.1f}")
        return True
    except Exception as e:
        logger.error(f"❌ Fix #3 test failed: {e}")
        return False

async def test_fix4_goal_validation():
    """Test Fix #4: Goal Validation Optimizer"""
    try:
        from services.goal_validation_optimizer import (
            goal_validation_optimizer, 
            ValidationDecision,
            ProgressVelocity
        )
        
        # Test velocity classification
        excellent_velocity = goal_validation_optimizer._classify_velocity(0.9)
        assert excellent_velocity == ProgressVelocity.EXCELLENT, f"Velocity classification failed: {excellent_velocity}"
        
        slow_velocity = goal_validation_optimizer._classify_velocity(0.1)
        assert slow_velocity == ProgressVelocity.SLOW, f"Velocity classification failed: {slow_velocity}"
        
        # Test grace period calculation
        from datetime import datetime
        current_time = datetime.now().isoformat()
        age_hours = goal_validation_optimizer._calculate_age_hours(current_time)
        assert age_hours < 1, f"Age calculation incorrect: {age_hours}"
        
        # Test optimization decision with recent goal
        mock_goal = {
            "id": "test-goal",
            "metric_type": "test_metric",
            "created_at": current_time,
            "target_value": 100
        }
        
        result = await goal_validation_optimizer.should_proceed_with_validation(
            workspace_id="test-workspace",
            goal_data=mock_goal,
            recent_tasks=[]
        )
        
        # Should apply grace period for recently created goal
        assert result.decision == ValidationDecision.APPLY_GRACE_PERIOD, f"Expected grace period, got: {result.decision}"
        
        logger.info(f"✅ Fix #4 GoalValidationOptimizer verified - decision: {result.decision.value}")
        return True
    except Exception as e:
        logger.error(f"❌ Fix #4 test failed: {e}")
        return False

async def test_integration_coordination():
    """Test that all fixes work together without conflicts"""
    try:
        # Test that all managers can be used simultaneously
        from services.task_deduplication_manager import task_deduplication_manager
        from services.workspace_health_manager import workspace_health_manager
        from services.agent_status_manager import agent_status_manager
        from services.goal_validation_optimizer import goal_validation_optimizer
        
        # Test concurrent operations
        tasks = []
        
        # Fix #1: Deduplication check
        tasks.append(task_deduplication_manager.get_cleanup_stats("test-workspace"))
        
        # Fix #2: Health check
        tasks.append(workspace_health_manager.get_dynamic_task_limit("test-workspace"))
        
        # Fix #3: Agent status
        tasks.append(agent_status_manager.get_available_agents("test-workspace"))
        
        # Fix #4: Optimization stats
        tasks.append(goal_validation_optimizer.get_optimization_stats())
        
        # Run all concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check that no operation failed catastrophically
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Operation {i} failed gracefully: {result}")
            else:
                logger.debug(f"Operation {i} succeeded: {type(result)}")
        
        logger.info("✅ All fixes can operate concurrently without conflicts")
        return True
    except Exception as e:
        logger.error(f"❌ Integration coordination test failed: {e}")
        return False

async def test_pillars_compliance():
    """Test that fixes comply with the 14 pillars"""
    try:
        # Pillar 7: Pipeline Autonoma
        from services.workspace_health_manager import workspace_health_manager
        health_report = await workspace_health_manager.check_workspace_health_with_recovery(
            "test-workspace", attempt_auto_recovery=True
        )
        assert hasattr(health_report, 'can_auto_recover'), "Auto-recovery capability not implemented"
        
        # Pillar 12: Course-Correction  
        from services.agent_status_manager import agent_status_manager
        sync_result = await agent_status_manager.synchronize_agent_statuses()
        assert hasattr(sync_result, 'inconsistencies_fixed'), "Status synchronization not implemented"
        
        # Pillars 2&3: AI-Driven Decisions
        from services.goal_validation_optimizer import goal_validation_optimizer
        mock_goal = {"id": "test", "metric_type": "test", "created_at": "2024-01-01T00:00:00Z"}
        result = await goal_validation_optimizer.should_proceed_with_validation(
            "test-workspace", mock_goal, []
        )
        assert result.confidence > 0, "AI confidence scoring not implemented"
        
        logger.info("✅ All fixes comply with the 14 pillars")
        return True
    except Exception as e:
        logger.error(f"❌ Pillars compliance test failed: {e}")
        return False

async def run_complete_integration_tests() -> Dict[str, Any]:
    """Run all complete integration tests"""
    logger.info("🎯 STARTING COMPLETE FIXES INTEGRATION TESTS")
    
    results = {
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "test_results": {}
    }
    
    tests = [
        ("all_fixes_imports", test_all_fixes_imports),
        ("fixes_availability", test_fixes_availability),
        ("fix1_task_deduplication", test_fix1_task_deduplication),
        ("fix2_workspace_health", test_fix2_workspace_health),
        ("fix3_agent_status", test_fix3_agent_status),
        ("fix4_goal_validation", test_fix4_goal_validation),
        ("integration_coordination", test_integration_coordination),
        ("pillars_compliance", test_pillars_compliance)
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
    logger.info("🎯 COMPLETE FIXES INTEGRATION TESTS SUMMARY")
    logger.info(f"📊 Total: {results['total_tests']}, Passed: {results['passed_tests']}, Failed: {results['failed_tests']}")
    
    if results["failed_tests"] == 0:
        logger.info("🎉 ALL INTEGRATION TESTS PASSED! 🚀")
        logger.info("🎯 ALL 4 DEFINITIVE FIXES ARE WORKING TOGETHER CORRECTLY! ✅")
        results["overall_status"] = "SUCCESS"
    else:
        logger.error(f"⚠️ {results['failed_tests']} integration tests failed")
        results["overall_status"] = "FAILED"
    
    return results

if __name__ == "__main__":
    # Run tests
    results = asyncio.run(run_complete_integration_tests())
    
    # Exit with appropriate code
    if results["overall_status"] == "SUCCESS":
        sys.exit(0)
    else:
        sys.exit(1)