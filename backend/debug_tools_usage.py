#!/usr/bin/env python3
"""
Debug tools usage - verifica perché i tools non appaiono nei traces
"""

import asyncio
import requests
import json
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(__file__))

# Import agent manager to check tools configuration
from ai_agents.manager import AgentManager
from ai_agents.specialist_enhanced import SpecialistAgent

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
workspace_id = "f528c2ac-1265-44f6-830e-2af84cb19204"

async def debug_tools():
    """Debug tools configuration and usage"""
    
    logger.info("🔍 DEBUGGING TOOLS CONFIGURATION")
    logger.info("=" * 50)
    
    # 1. Check agent tools configuration from database
    response = requests.get(f"{BASE_URL}/agents/{workspace_id}")
    agents = response.json()
    
    logger.info(f"📋 AGENTS TOOLS CONFIGURATION:")
    for agent in agents:
        name = agent.get('name')
        tools = agent.get('tools', [])
        logger.info(f"  {name}:")
        logger.info(f"    Tools count: {len(tools)}")
        for tool in tools:
            tool_name = tool.get('name', 'Unknown')
            logger.info(f"    - {tool_name}")
    
    # 2. Initialize AgentManager and check SpecialistAgent tools
    logger.info(f"\n🤖 CHECKING SPECIALIST AGENT TOOLS:")
    try:
        agent_manager = AgentManager(workspace_id)
        await agent_manager.initialize()
        
        for agent_id, specialist in agent_manager.agents.items():
            if isinstance(specialist, SpecialistAgent):
                agent_name = specialist.agent_data.name
                
                # Check OpenAI Agent tools
                if hasattr(specialist, 'agent') and specialist.agent:
                    openai_tools = getattr(specialist.agent, 'tools', [])
                    logger.info(f"  {agent_name} (OpenAI Agent):")
                    logger.info(f"    OpenAI tools count: {len(openai_tools)}")
                    for tool in openai_tools:
                        tool_name = getattr(tool, 'name', str(type(tool).__name__))
                        logger.info(f"    - {tool_name}")
                
                # Check handoff tools
                handoff_tools = getattr(specialist, 'handoff_tools', [])
                logger.info(f"    Handoff tools: {len(handoff_tools)}")
                
    except Exception as e:
        logger.error(f"Error initializing AgentManager: {e}")
    
    # 3. Create a simple task specifically to test WebSearch
    logger.info(f"\n🔍 CREATING WEB SEARCH TEST TASK:")
    
    simple_task = {
        "workspace_id": workspace_id,
        "agent_id": agents[0]["id"],  # Use first agent
        "name": "Simple Web Search Test",
        "description": """
**SIMPLE WEB SEARCH TEST**

Your task is extremely simple and focused:

1. **Use WebSearchTool to search for "OpenAI news 2025"**
2. **Use WebSearchTool to search for "artificial intelligence latest"** 
3. **Report what you found**

**REQUIREMENTS:**
- You MUST use the WebSearchTool for both searches
- Do NOT use any other tools
- Do NOT delegate to other agents
- Just perform the web searches and report results

**Expected Output:**
- Results from both web searches
- Summary of current AI/OpenAI news

This is a simple test to verify WebSearchTool is working and traced correctly.
""",
        "status": "pending",
        "priority": "urgent"
    }
    
    response = requests.post(f"{BASE_URL}/agents/{workspace_id}/tasks", json=simple_task)
    if response.status_code == 201:
        task = response.json()
        task_id = task["id"]
        logger.info(f"✅ Simple web search task created: {task_id}")
        
        # Monitor execution
        logger.info("⏳ Monitoring web search execution...")
        
        import time
        start_time = time.time()
        while time.time() - start_time < 120:  # 2 minutes max
            response = requests.get(f"{BASE_URL}/api/workspaces/{workspace_id}/tasks")
            if response.status_code == 200:
                tasks = response.json()
                current_task = next((t for t in tasks if t["id"] == task_id), None)
                
                if current_task and current_task.get("status") == "completed":
                    logger.info("✅ Web search task completed!")
                    
                    result = current_task.get("result")
                    if result:
                        result_str = str(result)
                        logger.info(f"📊 Result length: {len(result_str)} chars")
                        
                        # Check for web search evidence
                        if "search" in result_str.lower():
                            logger.info("✅ Search evidence found in result")
                        if "openai" in result_str.lower():
                            logger.info("✅ OpenAI content found in result")
                        if "news" in result_str.lower():
                            logger.info("✅ News content found in result")
                            
                        # Show preview
                        preview = result_str[:500] + "..." if len(result_str) > 500 else result_str
                        logger.info(f"📋 Result preview:\n{preview}")
                    
                    break
                elif current_task and current_task.get("status") == "failed":
                    logger.error("❌ Web search task failed")
                    error = current_task.get("error_message", "Unknown")
                    logger.error(f"Error: {error}")
                    break
            
            await asyncio.sleep(10)
        
    else:
        logger.error(f"Failed to create task: {response.status_code}")
    
    logger.info(f"\n🎯 CHECK TRACES AGAIN FOR:")
    logger.info(f"   - Recent task with WebSearchTool usage")
    logger.info(f"   - Tools column should show > 0")
    logger.info(f"   - Look for agent: {agents[0]['name']}")

if __name__ == "__main__":
    asyncio.run(debug_tools())