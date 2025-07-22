#!/usr/bin/env python3
"""
Test specifico per verificare tools nativi OpenAI
"""

import asyncio
import requests
import json
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(__file__))

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
workspace_id = "f528c2ac-1265-44f6-830e-2af84cb19204"

async def test_native_tools():
    """Test che forza l'uso di tools nativi OpenAI"""
    
    logger.info("🔧 TESTING NATIVE OPENAI TOOLS")
    logger.info("=" * 50)
    
    # Get agents
    response = requests.get(f"{BASE_URL}/agents/{workspace_id}")
    agents = response.json()
    
    # Create a task specifically designed to use tools that OpenAI can trace
    tools_task = {
        "workspace_id": workspace_id,
        "agent_id": agents[0]["id"],  # ElenaRossi
        "name": "Tools Tracing Test",
        "description": """
**TOOLS TRACING TEST - FORCE TOOL USAGE**

You are testing the tools integration. Your task is:

1. **Web Search for Current Information:**
   - Search for "Microsoft quarterly earnings 2025"
   - Search for "Google AI announcements January 2025"  
   - Search for "Tesla stock price today"

2. **Process and Analyze:**
   - Compare the search results
   - Extract key data points
   - Create a brief analysis

**CRITICAL INSTRUCTIONS:**
- You MUST use web search tools for each search
- Do NOT make up or assume any information
- Only use data from your searches
- Be explicit about which tool you're using

**Expected Output:**
- Evidence of tool usage in your response
- Real data from web searches
- Clear indication of search results

This test verifies that tools are working and being traced correctly.
""",
        "status": "pending",
        "priority": "urgent"
    }
    
    # Create task
    response = requests.post(f"{BASE_URL}/agents/{workspace_id}/tasks", json=tools_task)
    if response.status_code == 201:
        task = response.json()
        task_id = task["id"]
        logger.info(f"✅ Tools test task created: {task_id}")
        logger.info(f"   Agent: {agents[0]['name']}")
        
        # Monitor with detailed logging
        import time
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < 180:  # 3 minutes
            response = requests.get(f"{BASE_URL}/api/workspaces/{workspace_id}/tasks")
            if response.status_code == 200:
                tasks = response.json()
                current_task = next((t for t in tasks if t["id"] == task_id), None)
                
                if current_task:
                    status = current_task.get("status")
                    
                    if status != last_status:
                        elapsed = time.time() - start_time
                        logger.info(f"🔄 Status: {status} (at {elapsed:.1f}s)")
                        last_status = status
                    
                    if status == "completed":
                        logger.info("🎉 Tools test completed!")
                        
                        result = current_task.get("result")
                        if result:
                            result_str = str(result)
                            logger.info(f"📊 Result size: {len(result_str)} characters")
                            
                            # Detailed tool usage analysis
                            search_count = result_str.lower().count('search')
                            microsoft_mentions = result_str.lower().count('microsoft')
                            google_mentions = result_str.lower().count('google')
                            tesla_mentions = result_str.lower().count('tesla')
                            
                            logger.info("🔍 TOOL USAGE ANALYSIS:")
                            logger.info(f"   'search' mentions: {search_count}")
                            logger.info(f"   Microsoft mentions: {microsoft_mentions}")
                            logger.info(f"   Google mentions: {google_mentions}")
                            logger.info(f"   Tesla mentions: {tesla_mentions}")
                            
                            # Check for tool evidence
                            tool_keywords = ['using', 'searched', 'found', 'results', 'query']
                            tool_evidence = []
                            for keyword in tool_keywords:
                                if keyword in result_str.lower():
                                    tool_evidence.append(f"✅ '{keyword}'")
                                else:
                                    tool_evidence.append(f"❌ '{keyword}'")
                            
                            logger.info("🛠️ TOOL EVIDENCE:")
                            for evidence in tool_evidence:
                                logger.info(f"   {evidence}")
                            
                            # Show structured preview
                            lines = result_str.split('\n')[:10]
                            logger.info("📋 RESULT PREVIEW (first 10 lines):")
                            for i, line in enumerate(lines, 1):
                                logger.info(f"   {i:2d}: {line.strip()[:80]}")
                        
                        break
                        
                    elif status == "failed":
                        logger.error("❌ Tools test failed")
                        error = current_task.get("error_message", "Unknown")
                        logger.error(f"   Error: {error}")
                        break
            
            await asyncio.sleep(10)
    
    else:
        logger.error(f"Failed to create tools test: {response.status_code}")
        logger.error(f"Response: {response.text}")
    
    logger.info(f"\n🎯 NOW CHECK OPENAI TRACES:")
    logger.info(f"   - Look for recent ElenaRossi workflow")
    logger.info(f"   - Should show Tools > 0 if tracing works")
    logger.info(f"   - Duration should be >30s for web searches")
    logger.info(f"   - https://platform.openai.com/traces")

if __name__ == "__main__":
    asyncio.run(test_native_tools())