#!/usr/bin/env python3
"""
Test script for thinking process UX enhancement
"""
import asyncio
import json
from uuid import UUID
from services.thinking_process import thinking_engine

async def test_thinking_enhancement():
    """Test the enhanced thinking process with title generation"""
    
    workspace_id = UUID("f79d87cc-b61f-491d-9226-4220e39e71ad")
    
    # Start a new thinking process with various contexts to test title generation
    test_contexts = [
        ("Analyzing market requirements and customer feedback to identify opportunities", "analysis"),
        ("Planning product roadmap and development strategy for Q2 2025", "planning"),
        ("Evaluating technical feasibility and resource allocation", "evaluation"),
        ("Implementing new authentication system with OAuth2", "implementation"),
        ("Testing performance optimization strategies", "testing")
    ]
    
    for context, process_type in test_contexts:
        print(f"\n{'='*60}")
        print(f"Testing: {context[:50]}...")
        print(f"Process Type: {process_type}")
        
        # Start thinking process
        process_id = await thinking_engine.start_thinking_process(
            workspace_id=workspace_id,
            context=context,
            process_type=process_type
        )
        
        print(f"Started process: {process_id}")
        
        # Add some thinking steps with agent metadata
        agent_info = {
            "id": "test-agent-001",
            "name": "TestAgent",
            "role": "system-analyst",
            "seniority": "senior",
            "skills": ["analysis", "planning", "documentation"]
        }
        
        # Add agent thinking step
        await thinking_engine.add_agent_thinking_step(
            process_id=process_id,
            agent_info=agent_info,
            action_description="Analyzing the requirements and breaking down the problem",
            confidence=0.8
        )
        
        # Add tool execution step
        tool_results = {
            "tool_name": "data-analyzer",
            "tool_type": "analysis",
            "success": True,
            "execution_time_ms": 250,
            "summary": "Analyzed 1500 data points, identified 3 key patterns"
        }
        
        await thinking_engine.add_tool_execution_step(
            process_id=process_id,
            tool_results=tool_results,
            step_description="Performed comprehensive data analysis",
            confidence=0.9
        )
        
        # Complete the process
        completed = await thinking_engine.complete_thinking_process(
            process_id=process_id,
            conclusion="Successfully completed the analysis with actionable insights",
            overall_confidence=0.85
        )
        
        # Display results
        print(f"\n✅ Completed Process:")
        print(f"  Title: {completed.title}")
        print(f"  Steps: {len(completed.steps)}")
        
        if completed.summary_metadata:
            print(f"\n📊 Summary Metadata:")
            print(f"  Primary Agent: {completed.summary_metadata.get('primary_agent')}")
            print(f"  Tools Used: {completed.summary_metadata.get('tools_used')}")
            print(f"  Duration: {completed.summary_metadata.get('duration_ms')}ms")
            print(f"  Estimated Tokens: {completed.summary_metadata.get('estimated_tokens')}")
        
    # Now fetch all processes to verify they're stored correctly
    print(f"\n{'='*60}")
    print("Fetching all thinking processes for workspace...")
    
    processes = await thinking_engine.get_workspace_thinking(workspace_id, limit=5)
    
    print(f"\nFound {len(processes)} processes:")
    for p in processes:
        status = "✅" if p.completed_at else "⏳"
        print(f"  {status} {p.title or 'Untitled'} - {len(p.steps)} steps")
        if p.summary_metadata:
            agent = p.summary_metadata.get('primary_agent', 'Unknown')
            duration = p.summary_metadata.get('duration_ms', 0)
            print(f"      Agent: {agent}, Duration: {duration}ms")

if __name__ == "__main__":
    asyncio.run(test_thinking_enhancement())