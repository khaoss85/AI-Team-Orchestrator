#!/usr/bin/env python3
"""
Test script for Enhanced Thinking Process with Agent and Tool Metadata
Tests the new methods for capturing agent and tool execution metadata.
"""

import asyncio
import logging
from uuid import uuid4, UUID
from datetime import datetime
import json
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_enhanced_thinking_process():
    """Test the enhanced thinking process with agent and tool metadata"""
    
    try:
        # Import the enhanced thinking engine
        from services.thinking_process import (
            thinking_engine,
            add_agent_thinking_step,
            add_tool_execution_step,
            update_step_with_agent_info,
            update_step_with_tool_info,
            add_multi_agent_collaboration_step,
            get_agent_performance_metrics,
            get_tool_usage_statistics
        )
        
        logger.info("✅ Successfully imported enhanced thinking process module")
        
        # Create a test workspace ID
        test_workspace_id = UUID("550e8400-e29b-41d4-a716-446655440000")
        
        # 1. Start a thinking process
        logger.info("\n🧠 Starting enhanced thinking process...")
        process_id = await thinking_engine.start_thinking_process(
            workspace_id=test_workspace_id,
            context="Testing enhanced thinking process with agent and tool metadata",
            process_type="test_enhanced"
        )
        logger.info(f"✅ Started thinking process: {process_id}")
        
        # 2. Add agent thinking step
        logger.info("\n🤖 Adding agent thinking step...")
        agent_info = {
            "id": str(uuid4()),
            "name": "TestAgent",
            "role": "Senior Developer",
            "seniority": "senior",
            "skills": ["Python", "FastAPI", "Testing"],
            "status": "active",
            "workspace_id": str(test_workspace_id),
            "task_id": str(uuid4())
        }
        
        agent_step_id = await add_agent_thinking_step(
            process_id=process_id,
            agent_info=agent_info,
            action_description="Analyzing the codebase and preparing test execution plan",
            confidence=0.85
        )
        logger.info(f"✅ Added agent thinking step: {agent_step_id}")
        
        # 3. Add tool execution step
        logger.info("\n🔧 Adding tool execution step...")
        tool_results = {
            "tool_name": "code_analyzer",
            "tool_type": "analysis",
            "parameters": {"target": "backend/services/", "depth": 2},
            "execution_time_ms": 1250,
            "success": True,
            "output_type": "json",
            "output_size": 2048,
            "summary": "Analyzed 15 Python files, found 3 potential improvements",
            "artifacts_created": ["analysis_report.json", "metrics.csv"],
            "agent_id": agent_info["id"],
            "task_id": agent_info["task_id"]
        }
        
        tool_step_id = await add_tool_execution_step(
            process_id=process_id,
            tool_results=tool_results,
            step_description="Successfully analyzed codebase structure and dependencies",
            confidence=0.9
        )
        logger.info(f"✅ Added tool execution step: {tool_step_id}")
        
        # 4. Test multi-agent collaboration
        logger.info("\n👥 Adding multi-agent collaboration step...")
        collaborating_agents = [
            {
                "id": str(uuid4()),
                "role": "Code Reviewer",
                "seniority": "expert",
                "responsibility": "Review code quality and suggest improvements"
            },
            {
                "id": str(uuid4()),
                "role": "Test Engineer",
                "seniority": "senior",
                "responsibility": "Design and implement test cases"
            }
        ]
        
        collab_step_id = await add_multi_agent_collaboration_step(
            process_id=process_id,
            agents=collaborating_agents,
            collaboration_type="parallel",
            description="Code review and test case generation running in parallel"
        )
        logger.info(f"✅ Added collaboration step: {collab_step_id}")
        
        # 5. Add another tool execution with failure
        logger.info("\n❌ Adding failed tool execution step...")
        failed_tool_results = {
            "tool_name": "test_runner",
            "tool_type": "testing",
            "parameters": {"test_file": "test_enhanced_thinking.py"},
            "execution_time_ms": 5000,
            "success": False,
            "error": "TimeoutError: Test execution exceeded 5 seconds",
            "agent_id": agent_info["id"],
            "task_id": agent_info["task_id"]
        }
        
        failed_step_id = await add_tool_execution_step(
            process_id=process_id,
            tool_results=failed_tool_results,
            step_description="Test execution failed due to timeout",
            confidence=0.3
        )
        logger.info(f"✅ Added failed tool execution step: {failed_step_id}")
        
        # 6. Update existing step with additional agent info
        logger.info("\n📝 Updating step with additional agent info...")
        updated_agent_info = {
            "id": agent_info["id"],
            "name": agent_info["name"],
            "role": agent_info["role"],
            "seniority": agent_info["seniority"],
            "additional_context": "Agent identified performance bottleneck"
        }
        
        update_success = await update_step_with_agent_info(agent_step_id, updated_agent_info)
        logger.info(f"✅ Updated step with agent info: {update_success}")
        
        # 7. Complete the thinking process
        logger.info("\n🏁 Completing thinking process...")
        completed_process = await thinking_engine.complete_thinking_process(
            process_id=process_id,
            conclusion="Successfully tested enhanced thinking process with agent and tool metadata capture",
            overall_confidence=0.88
        )
        logger.info(f"✅ Completed thinking process with {len(completed_process.steps)} steps")
        
        # 8. Test performance metrics retrieval
        logger.info("\n📊 Testing performance metrics retrieval...")
        
        # Get agent performance metrics
        agent_metrics = await get_agent_performance_metrics(
            workspace_id=str(test_workspace_id),
            agent_id=agent_info["id"]
        )
        
        if agent_metrics:
            logger.info("📈 Agent Performance Metrics:")
            for agent_id, metrics in agent_metrics.items():
                logger.info(f"  Agent: {metrics.get('role', 'Unknown')}")
                logger.info(f"  Total Actions: {metrics.get('total_actions', 0)}")
                logger.info(f"  Average Confidence: {metrics.get('average_confidence', 0):.2f}")
        
        # Get tool usage statistics
        tool_stats = await get_tool_usage_statistics(
            workspace_id=str(test_workspace_id),
            time_window_hours=1  # Last hour
        )
        
        if tool_stats and "tools" in tool_stats:
            logger.info("\n🔧 Tool Usage Statistics:")
            logger.info(f"  Total Executions: {tool_stats.get('total_executions', 0)}")
            logger.info(f"  Success Rate: {tool_stats.get('overall_success_rate', 0):.1f}%")
            
            for tool_name, stats in tool_stats.get("tools", {}).items():
                logger.info(f"\n  Tool: {tool_name}")
                logger.info(f"    Executions: {stats.get('executions', 0)}")
                logger.info(f"    Success Rate: {stats.get('success_rate', 0):.1f}%")
                if stats.get('average_execution_time_ms'):
                    logger.info(f"    Avg Time: {stats.get('average_execution_time_ms', 0):.0f}ms")
        
        # 9. Retrieve and display the complete process
        logger.info("\n📋 Retrieving complete thinking process...")
        retrieved_process = await thinking_engine.get_thinking_process(process_id)
        
        if retrieved_process:
            logger.info(f"\n🧠 Complete Thinking Process Report:")
            logger.info(f"Process ID: {retrieved_process.process_id}")
            logger.info(f"Context: {retrieved_process.context}")
            logger.info(f"Steps: {len(retrieved_process.steps)}")
            logger.info(f"Confidence: {retrieved_process.overall_confidence}")
            logger.info(f"Conclusion: {retrieved_process.final_conclusion}")
            
            logger.info("\n📝 Thinking Steps with Metadata:")
            for i, step in enumerate(retrieved_process.steps, 1):
                logger.info(f"\n  Step {i}: {step.step_type}")
                logger.info(f"    Content: {step.content[:100]}...")
                logger.info(f"    Confidence: {step.confidence}")
                
                if step.metadata:
                    if "agent" in step.metadata:
                        logger.info(f"    Agent: {step.metadata['agent'].get('role', 'Unknown')}")
                    if "tool" in step.metadata:
                        tool_info = step.metadata['tool']
                        logger.info(f"    Tool: {tool_info.get('name', 'Unknown')}")
                        logger.info(f"    Success: {tool_info.get('success', False)}")
                    if "collaboration" in step.metadata:
                        collab_info = step.metadata['collaboration']
                        logger.info(f"    Collaboration Type: {collab_info.get('type', 'Unknown')}")
                        logger.info(f"    Agents: {len(collab_info.get('agents', []))}")
        
        logger.info("\n✅ All enhanced thinking process tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}", exc_info=True)
        return False

async def main():
    """Main test runner"""
    logger.info("🚀 Starting Enhanced Thinking Process Test Suite")
    logger.info("=" * 60)
    
    success = await test_enhanced_thinking_process()
    
    if success:
        logger.info("\n✅ TEST SUITE PASSED: Enhanced thinking process is working correctly!")
    else:
        logger.info("\n❌ TEST SUITE FAILED: Please check the errors above")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())