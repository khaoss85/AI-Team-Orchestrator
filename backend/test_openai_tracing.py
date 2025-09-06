#!/usr/bin/env python3
"""
Test OpenAI Agents SDK Tracing
Test script to verify that tools and handoffs appear in OpenAI Dashboard traces
"""

import asyncio
import sys
import os
import logging

sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

from database import create_task, list_agents, get_workspace
from models import TaskStatus
from ai_agents.manager import AgentManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_openai_tracing():
    """Test OpenAI tracing by creating and executing a task"""
    
    workspace_id = 'e29a33af-b473-4d9c-b983-f5c1aa70a830'
    
    print("=" * 80)
    print("🔍 OPENAI AGENTS SDK TRACING TEST")
    print("=" * 80)
    
    try:
        # Verify workspace exists
        workspace = await get_workspace(workspace_id)
        if not workspace:
            print(f"❌ Workspace {workspace_id} not found")
            return False
            
        print(f"✅ Workspace found: {workspace.get('name', 'Unknown')}")
        
        # Get available agents
        agents = await list_agents(workspace_id)
        if not agents:
            print(f"❌ No agents found in workspace {workspace_id}")
            return False
            
        print(f"✅ Found {len(agents)} agents")
        for agent in agents[:3]:  # Show first 3
            print(f"   - {agent['name']} ({agent['role']})")
        
        # Create a test task that requires tools and potential handoffs
        test_task_data = {
            'workspace_id': workspace_id,
            'name': 'OpenAI Tracing Test - Multi-Agent Research',
            'description': '''
Perform comprehensive research on "OpenAI Agents SDK best practices 2025" using web search tools.

This task is designed to test:
1. Tool usage (WebSearchTool) - should appear in OpenAI Dashboard traces
2. Agent handoffs - if the research requires specialist expertise  
3. SDK tracing - unique trace IDs and metadata should be visible

Requirements:
- Use web search to find current information
- Provide detailed analysis with sources
- If complexity requires specialist expertise, consider handoffs
            '''.strip(),
            'agent_id': agents[0]['id'],  # Assign to first available agent
            'priority': 'high',
            'status': TaskStatus.PENDING.value
        }
        
        # Create task
        task = await create_task(**test_task_data)
        task_id = task['id']
        
        print(f"✅ Created test task: {task_id}")
        print(f"   Name: {test_task_data['name']}")
        print(f"   Assigned to: {agents[0]['name']}")
        
        # Initialize AgentManager and execute the task
        print("\n🚀 Starting task execution...")
        print("   This will trigger OpenAI Agents SDK with tools and potential handoffs")
        print("   Check OpenAI Dashboard for trace visibility")
        
        manager = AgentManager(workspace_id)
        
        # Execute task (this will trigger the enhanced tracing)
        print(f"\n📊 TRACE MONITORING:")
        print(f"   - Task ID: {task_id}")
        print(f"   - Workspace: {workspace_id}")
        print(f"   - Expected tools: WebSearchTool, FileSearchTool")
        print(f"   - Expected handoffs: Available to {len(agents)-1} other agents")
        print("\n⏳ Executing task with full OpenAI Dashboard tracing...")
        
        execution_result = await manager.execute_task(task_id)
        
        if execution_result:
            print(f"\n✅ Task execution completed!")
            print(f"   Status: {execution_result.get('status', 'unknown')}")
            print(f"   Result: {str(execution_result.get('result', ''))[:100]}...")
        else:
            print(f"\n⚠️ Task execution returned no result")
            
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Starting OpenAI Agents SDK Tracing Test...")
    print("   This will create and execute a task designed to test tool usage and handoffs")
    print("   Monitor the OpenAI Dashboard for trace visibility")
    
    try:
        success = asyncio.run(test_openai_tracing())
        
        print("\n" + "=" * 80)
        if success:
            print("✅ TEST COMPLETED - Check OpenAI Dashboard traces")
            print("   You should now see:")
            print("   - Tool usage > 0 (WebSearchTool, FileSearchTool)")
            print("   - Handoffs > 0 (if agent requested collaboration)")
            print("   - Trace metadata with task and agent information")
        else:
            print("❌ TEST FAILED - Check error messages above")
        print("=" * 80)
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\n❌ Test script failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)