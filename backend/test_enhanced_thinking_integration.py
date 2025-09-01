#!/usr/bin/env python3
"""
Test script to verify Enhanced Thinking Process integration with Task Executor
"""

import asyncio
import logging
from uuid import uuid4
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_enhanced_thinking_integration():
    """Test the enhanced thinking process integration"""
    print("🧠 Testing Enhanced Thinking Process Integration")
    print("=" * 60)
    
    # Test 1: Import the enhanced thinking engine
    try:
        from services.thinking_process import thinking_engine
        print("✅ Successfully imported thinking_engine")
    except ImportError as e:
        print(f"❌ Failed to import thinking_engine: {e}")
        return False
    
    # Test 2: Test enhanced methods availability
    try:
        # Check if enhanced methods are available
        methods_to_check = [
            'add_agent_thinking_step',
            'add_tool_execution_step', 
            'add_multi_agent_collaboration_step',
            'get_agent_performance_metrics',
            'get_tool_usage_statistics'
        ]
        
        for method in methods_to_check:
            if hasattr(thinking_engine, method):
                print(f"✅ Method '{method}' is available")
            else:
                print(f"❌ Method '{method}' is missing")
                return False
                
    except Exception as e:
        print(f"❌ Error checking enhanced methods: {e}")
        return False
    
    # Test 3: Test basic thinking process workflow
    try:
        workspace_id = uuid4()
        
        # Start a thinking process
        process_id = await thinking_engine.start_thinking_process(
            workspace_id=workspace_id,
            context="Testing enhanced integration",
            process_type="integration_test"
        )
        print(f"✅ Started thinking process: {process_id}")
        
        # Test agent thinking step
        agent_info = {
            "id": str(uuid4()),
            "name": "TestAgent",
            "role": "test_specialist",
            "seniority": "senior",
            "skills": ["testing", "integration"],
            "status": "assigned",
            "workspace_id": str(workspace_id),
            "task_id": str(uuid4())
        }
        
        agent_step_id = await thinking_engine.add_agent_thinking_step(
            process_id=process_id,
            agent_info=agent_info,
            action_description="executing integration test",
            confidence=0.9
        )
        print(f"✅ Added agent thinking step: {agent_step_id}")
        
        # Test tool execution step
        tool_results = {
            "tool_name": "IntegrationTestTool",
            "tool_type": "test",
            "execution_time_ms": 1500,
            "success": True,
            "parameters": {"test_mode": "integration"},
            "output_type": "dict",
            "output_size": 256,
            "summary": "Integration test completed successfully",
            "agent_id": agent_info["id"],
            "task_id": agent_info["task_id"]
        }
        
        tool_step_id = await thinking_engine.add_tool_execution_step(
            process_id=process_id,
            tool_results=tool_results,
            step_description="completed integration test execution",
            confidence=0.95
        )
        print(f"✅ Added tool execution step: {tool_step_id}")
        
        # Complete the thinking process
        completed_process = await thinking_engine.complete_thinking_process(
            process_id=process_id,
            conclusion="Enhanced thinking process integration test completed successfully",
            overall_confidence=0.92
        )
        print(f"✅ Completed thinking process with {len(completed_process.steps)} steps")
        
    except Exception as e:
        print(f"❌ Error in thinking process workflow test: {e}")
        return False
    
    # Test 4: Test performance metrics
    try:
        # Test agent performance metrics
        agent_metrics = await thinking_engine.get_agent_performance_metrics(
            workspace_id=str(workspace_id)
        )
        print(f"✅ Retrieved agent performance metrics (found {len(agent_metrics)} agents)")
        
        # Test tool usage statistics  
        tool_stats = await thinking_engine.get_tool_usage_statistics(
            workspace_id=str(workspace_id),
            time_window_hours=1
        )
        print(f"✅ Retrieved tool usage statistics: {tool_stats.get('total_executions', 0)} executions")
        
    except Exception as e:
        print(f"❌ Error in performance metrics test: {e}")
        return False
    
    print("\n🎉 All Enhanced Thinking Process Integration Tests Passed!")
    return True

async def test_executor_integration():
    """Test that the executor properly integrates with enhanced thinking"""
    print("\n🔧 Testing Executor Integration")
    print("=" * 40)
    
    try:
        # Check if holistic pipeline accepts thinking_process_id
        from services.holistic_task_deliverable_pipeline import execute_task_holistically
        import inspect
        
        sig = inspect.signature(execute_task_holistically)
        if 'thinking_process_id' in sig.parameters:
            print("✅ Holistic pipeline accepts thinking_process_id parameter")
        else:
            print("❌ Holistic pipeline missing thinking_process_id parameter")
            return False
            
        # Check if SpecialistAgent execute method accepts thinking_process_id
        from ai_agents.specialist_enhanced import SpecialistAgent
        sig = inspect.signature(SpecialistAgent.execute)
        if 'thinking_process_id' in sig.parameters:
            print("✅ SpecialistAgent.execute accepts thinking_process_id parameter")
        else:
            print("❌ SpecialistAgent.execute missing thinking_process_id parameter")
            return False
        
        print("✅ Executor integration parameters are correctly configured")
        return True
        
    except Exception as e:
        print(f"❌ Error in executor integration test: {e}")
        return False

async def main():
    """Run all integration tests"""
    print("🚀 Enhanced Thinking Process Integration Test Suite")
    print("=" * 70)
    
    # Run tests
    basic_test_passed = await test_enhanced_thinking_integration()
    executor_test_passed = await test_executor_integration()
    
    print("\n📊 Test Results Summary:")
    print("=" * 30)
    print(f"Basic Integration Test: {'✅ PASSED' if basic_test_passed else '❌ FAILED'}")
    print(f"Executor Integration Test: {'✅ PASSED' if executor_test_passed else '❌ FAILED'}")
    
    if basic_test_passed and executor_test_passed:
        print("\n🎉 ALL TESTS PASSED - Enhanced Thinking Process integration is working correctly!")
        return True
    else:
        print("\n❌ Some tests failed - check the output above for details")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)