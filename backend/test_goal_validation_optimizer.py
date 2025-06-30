#!/usr/bin/env python3
"""
🎯 GOAL VALIDATION OPTIMIZER TEST

Tests the GoalValidationOptimizer integration and functionality.
Verifies Fix #4: Intelligent Goal Validation Optimization implementation.
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that goal validation optimizer can be imported"""
    try:
        from services.goal_validation_optimizer import (
            goal_validation_optimizer, 
            ValidationDecision, 
            ProgressVelocity,
            ValidationOptimizationResult
        )
        from automated_goal_monitor import (
            automated_goal_monitor, 
            GOAL_VALIDATION_OPTIMIZER_AVAILABLE, 
            goal_validation_optimizer as monitor_optimizer
        )
        
        logger.info("✅ All goal validation optimizer components imported successfully")
        return True
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False

def test_optimization_decisions():
    """Test optimization decision enums"""
    try:
        from services.goal_validation_optimizer import ValidationDecision, ProgressVelocity
        
        # Test ValidationDecision enum
        expected_decisions = ["proceed_normal", "apply_grace_period", "velocity_acceptable", "threshold_adjusted", "skip_validation"]
        actual_decisions = [decision.value for decision in ValidationDecision]
        
        assert set(expected_decisions) == set(actual_decisions), f"Decision mismatch: expected {expected_decisions}, got {actual_decisions}"
        
        # Test ProgressVelocity enum
        expected_velocities = ["excellent", "good", "moderate", "slow", "stalled"]
        actual_velocities = [velocity.value for velocity in ProgressVelocity]
        
        assert set(expected_velocities) == set(actual_velocities), f"Velocity mismatch: expected {expected_velocities}, got {actual_velocities}"
        
        logger.info("✅ Optimization decision enums verified")
        return True
    except Exception as e:
        logger.error(f"❌ Optimization decisions test failed: {e}")
        return False

async def test_goal_validation_optimizer():
    """Test GoalValidationOptimizer functionality"""
    try:
        from services.goal_validation_optimizer import goal_validation_optimizer
        
        # Test initialization
        assert goal_validation_optimizer is not None, "GoalValidationOptimizer not initialized"
        
        # Test grace period calculation
        test_timestamp = datetime.now().isoformat()
        age_hours = goal_validation_optimizer._calculate_age_hours(test_timestamp)
        assert age_hours < 1, f"Age calculation incorrect: {age_hours}"
        
        # Test velocity classification
        from services.goal_validation_optimizer import ProgressVelocity
        velocity = goal_validation_optimizer._classify_velocity(0.9)
        assert velocity == ProgressVelocity.EXCELLENT, f"Velocity classification incorrect: {velocity}"
        
        logger.info("✅ GoalValidationOptimizer functionality verified")
        return True
    except Exception as e:
        logger.error(f"❌ GoalValidationOptimizer test failed: {e}")
        return False

async def test_optimization_integration():
    """Test integration with automated goal monitor"""
    try:
        from automated_goal_monitor import automated_goal_monitor, GOAL_VALIDATION_OPTIMIZER_AVAILABLE
        
        # Verify optimizer is available in goal monitor
        assert GOAL_VALIDATION_OPTIMIZER_AVAILABLE == True, "GoalValidationOptimizer not available in goal monitor"
        
        # Test optimization stats
        from services.goal_validation_optimizer import goal_validation_optimizer
        stats = await goal_validation_optimizer.get_optimization_stats()
        
        assert "optimization_enabled" in stats, "Optimization stats missing key fields"
        assert "grace_period_hours" in stats, "Grace period not in stats"
        assert "velocity_window_hours" in stats, "Velocity window not in stats"
        
        logger.info(f"✅ Optimization integration verified - stats: {stats}")
        return True
    except Exception as e:
        logger.error(f"❌ Optimization integration test failed: {e}")
        return False

async def test_mock_validation_decision():
    """Test validation decision with mock data"""
    try:
        from services.goal_validation_optimizer import goal_validation_optimizer
        
        # Create mock goal data (recently created)
        mock_goal = {
            "id": "test-goal-123",
            "metric_type": "test_metric",
            "created_at": datetime.now().isoformat(),
            "target_value": 100
        }
        
        # Test validation decision
        result = await goal_validation_optimizer.should_proceed_with_validation(
            workspace_id="test-workspace-123",
            goal_data=mock_goal,
            recent_tasks=[]
        )
        
        assert result is not None, "Validation result is None"
        assert hasattr(result, 'should_proceed'), "Result missing should_proceed"
        assert hasattr(result, 'decision'), "Result missing decision"
        assert hasattr(result, 'reason'), "Result missing reason"
        assert hasattr(result, 'confidence'), "Result missing confidence"
        
        logger.info(f"✅ Mock validation decision: {result.decision.value} - {result.reason}")
        return True
    except Exception as e:
        logger.error(f"❌ Mock validation test failed: {e}")
        return False

async def test_workspace_analysis():
    """Test workspace analysis with mock data"""
    try:
        from services.goal_validation_optimizer import goal_validation_optimizer
        
        # Test workspace analysis (will fail gracefully with non-existent workspace)
        analysis = await goal_validation_optimizer._generate_workspace_progress_analysis("test-workspace-nonexistent")
        
        assert analysis is not None, "Workspace analysis is None"
        assert hasattr(analysis, 'workspace_id'), "Analysis missing workspace_id"
        assert hasattr(analysis, 'velocity_classification'), "Analysis missing velocity_classification"
        assert hasattr(analysis, 'recommended_action'), "Analysis missing recommended_action"
        
        logger.info(f"✅ Workspace analysis verified - velocity: {analysis.velocity_classification.value}")
        return True
    except Exception as e:
        logger.error(f"❌ Workspace analysis test failed: {e}")
        return False

async def run_optimization_tests() -> Dict[str, Any]:
    """Run all goal validation optimization tests"""
    logger.info("🎯 STARTING GOAL VALIDATION OPTIMIZATION TESTS")
    
    results = {
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "test_results": {}
    }
    
    tests = [
        ("imports", test_imports),
        ("optimization_decisions", test_optimization_decisions),
        ("goal_validation_optimizer", test_goal_validation_optimizer),
        ("optimization_integration", test_optimization_integration),
        ("mock_validation_decision", test_mock_validation_decision),
        ("workspace_analysis", test_workspace_analysis)
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
    logger.info("🎯 GOAL VALIDATION OPTIMIZATION TESTS SUMMARY")
    logger.info(f"📊 Total: {results['total_tests']}, Passed: {results['passed_tests']}, Failed: {results['failed_tests']}")
    
    if results["failed_tests"] == 0:
        logger.info("🎉 ALL GOAL VALIDATION OPTIMIZATION TESTS PASSED! ✅")
        results["overall_status"] = "SUCCESS"
    else:
        logger.error(f"⚠️ {results['failed_tests']} tests failed")
        results["overall_status"] = "FAILED"
    
    return results

if __name__ == "__main__":
    # Run tests
    results = asyncio.run(run_optimization_tests())
    
    # Exit with appropriate code
    if results["overall_status"] == "SUCCESS":
        sys.exit(0)
    else:
        sys.exit(1)