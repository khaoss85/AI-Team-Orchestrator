#!/usr/bin/env python3
"""
Test that all critical fixes are working correctly
"""

import asyncio
from dotenv import load_dotenv

# Load environment
load_dotenv('/Users/pelleri/Documents/ai-team-orchestrator/backend/.env')

async def test_critical_fixes():
    """Test all the critical fixes we implemented"""
    
    print("🧪 Testing all critical fixes...")
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: AssetArtifact model schema
    total_tests += 1
    try:
        from models import AssetArtifact
        from uuid import uuid4
        
        # Test creating AssetArtifact with new fields
        artifact = AssetArtifact(
            requirement_id=uuid4(),
            artifact_name="Test Artifact",
            artifact_type="text",
            workspace_id=uuid4(),  # This should not fail now
            artifact_format="markdown"  # This should not fail now
        )
        
        # Test accessing the new attributes
        _ = artifact.workspace_id
        _ = artifact.artifact_format
        
        print("✅ Test 1: AssetArtifact model schema - PASSED")
        tests_passed += 1
        
    except Exception as e:
        print(f"❌ Test 1: AssetArtifact model schema - FAILED: {e}")
    
    # Test 2: PerformanceMetrics schema
    total_tests += 1
    try:
        from monitoring.asset_system_monitor import PerformanceMetrics
        
        # Create PerformanceMetrics with percentage
        metrics = PerformanceMetrics(
            avg_response_time_ms=100.0,
            throughput_per_minute=50.0,
            error_rate_percentage=5.0,  # 5%
            memory_usage_mb=512.0,
            active_connections=10,
            queue_depth=5
        )
        
        # Test accessing error_rate property (should be 0.05)
        error_rate = metrics.error_rate
        assert abs(error_rate - 0.05) < 0.001, f"Expected 0.05, got {error_rate}"
        
        print("✅ Test 2: PerformanceMetrics schema - PASSED")
        tests_passed += 1
        
    except Exception as e:
        print(f"❌ Test 2: PerformanceMetrics schema - FAILED: {e}")
    
    # Test 3: Route imports
    total_tests += 1
    try:
        # Test importing the routes that should now be available
        from routes.assets import router as assets_router
        from routes.websocket_assets import router as websocket_assets_router
        
        # Verify they are router objects
        assert hasattr(assets_router, 'routes'), "assets_router should have routes"
        assert hasattr(websocket_assets_router, 'routes'), "websocket_assets_router should have routes"
        
        print("✅ Test 3: Route imports - PASSED")
        tests_passed += 1
        
    except Exception as e:
        print(f"❌ Test 3: Route imports - FAILED: {e}")
    
    # Test 4: Thinking process system
    total_tests += 1
    try:
        from services.thinking_process import RealTimeThinkingEngine
        from uuid import UUID
        
        engine = RealTimeThinkingEngine()
        workspace_id = UUID("bc41beb3-4380-434a-8280-92821006840e")
        
        # Start a simple thinking process
        process_id = await engine.start_thinking_process(
            workspace_id=workspace_id,
            context="Testing critical fixes",
            process_type="test"
        )
        
        # Add a step
        await engine.add_thinking_step(
            process_id=process_id,
            step_type="analysis",
            content="All critical fixes appear to be working",
            confidence=0.95
        )
        
        # Complete it
        completed = await engine.complete_thinking_process(
            process_id=process_id,
            conclusion="Critical fixes test completed successfully",
            overall_confidence=0.95
        )
        
        assert completed is not None, "Should return completed process"
        
        print("✅ Test 4: Thinking process system - PASSED")
        tests_passed += 1
        
    except Exception as e:
        print(f"❌ Test 4: Thinking process system - FAILED: {e}")
    
    # Test 5: AI JSON parsing robustness
    total_tests += 1
    try:
        from goal_driven_task_planner import GoalDrivenTaskPlanner
        
        planner = GoalDrivenTaskPlanner()
        
        # Test with sample tasks
        test_tasks = [
            {"id": "task1", "name": "Test Task 1", "description": "First test"},
            {"id": "task2", "name": "Test Task 2", "description": "Second test"}
        ]
        
        # This should not crash with JSON parsing errors
        result = await planner._detect_similar_tasks_ai_driven(test_tasks, "test_metric")
        
        # Result should be a list (empty or with items)
        assert isinstance(result, list), f"Expected list, got {type(result)}"
        
        print("✅ Test 5: AI JSON parsing robustness - PASSED")
        tests_passed += 1
        
    except Exception as e:
        print(f"❌ Test 5: AI JSON parsing robustness - FAILED: {e}")
    
    # Test 6: Workspace health recovery
    total_tests += 1
    try:
        from workspace_health_recovery import WorkspaceHealthRecovery
        
        recovery = WorkspaceHealthRecovery()
        result = await recovery.diagnose_and_recover_workspaces()
        
        # Should return a dict with expected keys
        assert isinstance(result, dict), "Should return dict"
        
        print("✅ Test 6: Workspace health recovery - PASSED")
        tests_passed += 1
        
    except Exception as e:
        print(f"❌ Test 6: Workspace health recovery - FAILED: {e}")
    
    # Final results
    print(f"\n🏁 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All critical fixes are working correctly!")
        return True
    else:
        print(f"⚠️ {total_tests - tests_passed} tests failed - some issues remain")
        return False

if __name__ == "__main__":
    asyncio.run(test_critical_fixes())