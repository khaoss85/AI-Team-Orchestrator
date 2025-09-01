#!/usr/bin/env python3
"""
Example integration of Enhanced Thinking Process with Executor
Shows how to capture agent and tool metadata during task execution.
"""

import asyncio
import logging
from uuid import UUID
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def enhanced_task_execution_with_metadata(
    task_dict: Dict[str, Any],
    thinking_process_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Example of how to integrate enhanced thinking process metadata capture
    into the task execution flow.
    """
    
    # Import enhanced thinking functions
    from services.thinking_process import (
        add_agent_thinking_step,
        add_tool_execution_step,
        add_multi_agent_collaboration_step
    )
    
    task_id = task_dict.get("id")
    task_name = task_dict.get("name", "Unknown Task")
    agent_id = task_dict.get("agent_id")
    
    logger.info(f"🚀 Starting enhanced task execution for: {task_name}")
    
    # 1. AGENT METADATA CAPTURE
    if thinking_process_id and agent_id:
        # Prepare agent information
        agent_info = {
            "id": agent_id,
            "name": task_dict.get("agent_name", "AI Agent"),
            "role": task_dict.get("agent_role", "Specialist"),
            "seniority": task_dict.get("agent_seniority", "senior"),
            "skills": task_dict.get("agent_skills", []),
            "status": "active",
            "workspace_id": task_dict.get("workspace_id"),
            "task_id": task_id
        }
        
        # Add agent thinking step
        await add_agent_thinking_step(
            process_id=thinking_process_id,
            agent_info=agent_info,
            action_description=f"Starting execution of task: {task_name}. Analyzing requirements and preparing execution strategy.",
            confidence=0.8
        )
        logger.info(f"✅ Added agent metadata to thinking process")
    
    # 2. TOOL EXECUTION CAPTURE
    # Simulate tool execution (replace with actual tool calls)
    tool_results = await simulate_tool_execution(task_dict)
    
    if thinking_process_id and tool_results:
        # Add tool execution metadata
        await add_tool_execution_step(
            process_id=thinking_process_id,
            tool_results=tool_results,
            step_description=f"Executed {tool_results.get('tool_name')} for {task_name}",
            confidence=0.85 if tool_results.get("success") else 0.4
        )
        logger.info(f"✅ Added tool execution metadata to thinking process")
    
    # 3. MULTI-AGENT COLLABORATION (if applicable)
    if task_dict.get("requires_collaboration"):
        collaborating_agents = [
            {
                "id": agent_id,
                "role": task_dict.get("agent_role"),
                "seniority": task_dict.get("agent_seniority"),
                "responsibility": "Primary task execution"
            },
            {
                "id": "reviewer_agent_id",
                "role": "Quality Reviewer",
                "seniority": "expert",
                "responsibility": "Review and validate output"
            }
        ]
        
        if thinking_process_id:
            await add_multi_agent_collaboration_step(
                process_id=thinking_process_id,
                agents=collaborating_agents,
                collaboration_type="sequential",
                description=f"Agent handoff for quality review of {task_name}"
            )
            logger.info(f"✅ Added collaboration metadata to thinking process")
    
    # 4. FINAL RESULT WITH METADATA
    result = {
        "success": tool_results.get("success", False) if tool_results else False,
        "task_id": task_id,
        "task_name": task_name,
        "agent_metadata_captured": bool(thinking_process_id and agent_id),
        "tool_metadata_captured": bool(thinking_process_id and tool_results),
        "collaboration_metadata_captured": bool(thinking_process_id and task_dict.get("requires_collaboration")),
        "output": tool_results.get("output") if tool_results else None
    }
    
    # 5. CAPTURE COMPLETION METADATA
    if thinking_process_id:
        completion_agent_info = {
            "id": agent_id,
            "role": task_dict.get("agent_role"),
            "seniority": task_dict.get("agent_seniority"),
            "task_completion_status": "completed" if result["success"] else "failed"
        }
        
        await add_agent_thinking_step(
            process_id=thinking_process_id,
            agent_info=completion_agent_info,
            action_description=f"Task '{task_name}' execution {'completed successfully' if result['success'] else 'failed'}. Finalizing outputs and updating status.",
            confidence=0.9 if result["success"] else 0.5
        )
    
    return result

async def simulate_tool_execution(task_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate tool execution with realistic metadata.
    In real implementation, this would call actual tools.
    """
    import time
    import random
    
    # Simulate execution time
    start_time = time.time()
    await asyncio.sleep(random.uniform(0.5, 2.0))  # Simulate processing
    execution_time_ms = int((time.time() - start_time) * 1000)
    
    # Simulate different tool types based on task
    task_name = task_dict.get("name", "").lower()
    
    if "analyze" in task_name or "review" in task_name:
        tool_name = "code_analyzer"
        tool_type = "analysis"
        success = random.random() > 0.2  # 80% success rate
        output = {
            "files_analyzed": random.randint(5, 50),
            "issues_found": random.randint(0, 10) if success else None,
            "suggestions": random.randint(1, 5) if success else 0
        }
    elif "test" in task_name:
        tool_name = "test_runner"
        tool_type = "testing"
        success = random.random() > 0.3  # 70% success rate
        output = {
            "tests_run": random.randint(10, 100),
            "tests_passed": random.randint(5, 95) if success else 0,
            "tests_failed": random.randint(0, 5) if success else random.randint(5, 20)
        }
    elif "generate" in task_name or "create" in task_name:
        tool_name = "content_generator"
        tool_type = "generation"
        success = random.random() > 0.1  # 90% success rate
        output = {
            "content_type": "code" if "code" in task_name else "documentation",
            "lines_generated": random.randint(50, 500) if success else 0,
            "quality_score": random.uniform(0.7, 0.95) if success else 0
        }
    else:
        tool_name = "generic_processor"
        tool_type = "processing"
        success = random.random() > 0.15  # 85% success rate
        output = {"processed": success}
    
    # Build tool results with metadata
    tool_results = {
        "tool_name": tool_name,
        "tool_type": tool_type,
        "parameters": {
            "task_id": task_dict.get("id"),
            "task_name": task_dict.get("name"),
            "mode": "enhanced"
        },
        "execution_time_ms": execution_time_ms,
        "success": success,
        "output": output,
        "output_type": "json",
        "output_size": len(str(output)),
        "summary": f"{'Successfully' if success else 'Failed to'} execute {tool_name} for task",
        "artifacts_created": [f"{tool_name}_output.json"] if success else [],
        "agent_id": task_dict.get("agent_id"),
        "task_id": task_dict.get("id")
    }
    
    if not success:
        tool_results["error"] = f"SimulatedError: {tool_name} failed due to simulated condition"
    
    return tool_results

async def demonstrate_executor_integration():
    """
    Demonstrate how the enhanced thinking process integrates with executor.
    """
    from services.thinking_process import thinking_engine
    
    # Create a test workspace and start thinking process
    test_workspace_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    
    logger.info("🧠 Starting thinking process for task execution demonstration")
    thinking_process_id = await thinking_engine.start_thinking_process(
        workspace_id=test_workspace_id,
        context="Demonstrating enhanced task execution with agent and tool metadata capture",
        process_type="task_execution"
    )
    
    # Simulate multiple tasks with different characteristics
    test_tasks = [
        {
            "id": "task_001",
            "name": "Analyze codebase for security vulnerabilities",
            "agent_id": "agent_001",
            "agent_name": "Security Analyst",
            "agent_role": "Security Specialist",
            "agent_seniority": "expert",
            "agent_skills": ["security", "code_analysis", "vulnerability_assessment"],
            "workspace_id": str(test_workspace_id),
            "requires_collaboration": False
        },
        {
            "id": "task_002",
            "name": "Generate unit tests for authentication module",
            "agent_id": "agent_002",
            "agent_name": "Test Engineer",
            "agent_role": "QA Specialist",
            "agent_seniority": "senior",
            "agent_skills": ["testing", "automation", "test_generation"],
            "workspace_id": str(test_workspace_id),
            "requires_collaboration": True
        },
        {
            "id": "task_003",
            "name": "Test API endpoints for performance",
            "agent_id": "agent_003",
            "agent_name": "Performance Tester",
            "agent_role": "Performance Engineer",
            "agent_seniority": "senior",
            "agent_skills": ["performance_testing", "load_testing", "optimization"],
            "workspace_id": str(test_workspace_id),
            "requires_collaboration": False
        }
    ]
    
    # Execute tasks with metadata capture
    results = []
    for task in test_tasks:
        logger.info(f"\n{'='*60}")
        logger.info(f"Executing task: {task['name']}")
        logger.info(f"{'='*60}")
        
        result = await enhanced_task_execution_with_metadata(
            task_dict=task,
            thinking_process_id=thinking_process_id
        )
        results.append(result)
        
        logger.info(f"Task result: {'✅ SUCCESS' if result['success'] else '❌ FAILED'}")
        await asyncio.sleep(1)  # Small delay between tasks
    
    # Complete the thinking process
    success_count = sum(1 for r in results if r["success"])
    conclusion = f"Executed {len(test_tasks)} tasks with {success_count}/{len(test_tasks)} successful. All metadata captured successfully."
    
    await thinking_engine.complete_thinking_process(
        process_id=thinking_process_id,
        conclusion=conclusion,
        overall_confidence=success_count / len(test_tasks) if test_tasks else 0
    )
    
    logger.info(f"\n{'='*60}")
    logger.info("📊 Execution Summary:")
    logger.info(f"  Total Tasks: {len(test_tasks)}")
    logger.info(f"  Successful: {success_count}")
    logger.info(f"  Failed: {len(test_tasks) - success_count}")
    logger.info(f"  Success Rate: {(success_count/len(test_tasks)*100):.1f}%")
    
    # Get and display performance metrics
    from services.thinking_process import get_agent_performance_metrics, get_tool_usage_statistics
    
    agent_metrics = await get_agent_performance_metrics(str(test_workspace_id))
    if agent_metrics:
        logger.info("\n📈 Agent Performance Metrics:")
        for agent_id, metrics in agent_metrics.items():
            logger.info(f"  {metrics.get('role', 'Unknown')}: {metrics.get('total_actions', 0)} actions, "
                       f"avg confidence: {metrics.get('average_confidence', 0):.2f}")
    
    tool_stats = await get_tool_usage_statistics(str(test_workspace_id), time_window_hours=1)
    if tool_stats and "tools" in tool_stats:
        logger.info(f"\n🔧 Tool Usage Statistics:")
        logger.info(f"  Overall Success Rate: {tool_stats.get('overall_success_rate', 0):.1f}%")
        for tool_name, stats in tool_stats.get("tools", {}).items():
            logger.info(f"  {tool_name}: {stats.get('executions', 0)} executions, "
                       f"{stats.get('success_rate', 0):.1f}% success rate")

async def main():
    """Main entry point"""
    logger.info("🚀 Starting Enhanced Executor Integration Demo")
    logger.info("=" * 60)
    
    try:
        await demonstrate_executor_integration()
        logger.info("\n✅ Demo completed successfully!")
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())