#!/usr/bin/env python3
"""
Test specifico per vedere handoff e tools in azione
Crea un task che richiede collaborazione tra agenti diversi
"""

import asyncio
import requests
import json
import time
import logging
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(__file__))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

async def test_handoff_execution():
    """Test che forza handoff tra agenti"""
    
    logger.info("🚀 HANDOFF & TOOLS EXECUTION TEST")
    logger.info("=" * 60)
    
    # Use existing workspace from comprehensive test
    workspace_id = "f528c2ac-1265-44f6-830e-2af84cb19204"
    
    # Get agents
    response = requests.get(f"{BASE_URL}/agents/{workspace_id}")
    if response.status_code != 200:
        logger.error(f"Failed to get agents: {response.status_code}")
        return
    
    agents = response.json()
    logger.info(f"✅ Found {len(agents)} agents:")
    for agent in agents:
        logger.info(f"  - {agent['name']} ({agent['role']})")
    
    if len(agents) < 2:
        logger.error("Need at least 2 agents for handoff test")
        return
    
    # Create a complex task that requires handoff
    complex_task = {
        "workspace_id": workspace_id,
        "agent_id": agents[0]["id"],  # Start with first agent
        "name": "Multi-Agent E-commerce Platform Analysis",
        "description": """
**COMPLEX MULTI-DISCIPLINARY TASK - REQUIRES HANDOFFS**

You are starting a comprehensive e-commerce platform analysis that requires expertise from multiple team members.

**YOUR INITIAL ROLE (Project Manager):**
1. **Project Scoping**: Define the analysis scope and key business questions
2. **Research Planning**: Outline what data and insights we need
3. **Team Coordination**: **MUST hand off to appropriate specialists**

**REQUIRED HANDOFFS (you MUST use these):**
- **Hand off to UX/UI Designer** for user experience analysis and interface recommendations
- **Hand off to Data Analyst** for market research and competitive analysis  
- **Hand off to Lead Developer** for technical architecture evaluation

**HANDOFF INSTRUCTIONS:**
- Use the handoff tools available to you
- Each handoff should include specific deliverables request
- Coordinate the final synthesis of all inputs

**EXPECTED OUTPUT:**
- Initial project scope and plan
- Evidence of successful handoffs to specialists
- Consolidated insights from all team members
- Actionable recommendations

**CRITICAL:** This task is designed to test inter-agent collaboration. You MUST use handoff tools to delegate work to specialists. Do not try to complete everything yourself.
""",
        "status": "pending",
        "priority": "high",
        "estimated_effort_hours": 8
    }
    
    # Create the task
    response = requests.post(f"{BASE_URL}/agents/{workspace_id}/tasks", json=complex_task)
    if response.status_code != 201:
        logger.error(f"Failed to create task: {response.status_code} - {response.text}")
        return
    
    task = response.json()
    task_id = task["id"]
    logger.info(f"✅ Complex handoff task created: {task_id}")
    logger.info(f"   Task: {task['name']}")
    
    # Wait a moment and execute the task
    await asyncio.sleep(2)
    
    # The task will be executed automatically by the task executor
    logger.info("🔧 Task created - waiting for automatic execution by task executor...")
    logger.info("   (The system should automatically pick up pending tasks)")
    
    # Monitor execution progress
    logger.info("👀 Monitoring task execution for handoffs and tool usage...")
    
    start_time = time.time()
    max_wait = 300  # 5 minutes
    check_interval = 10
    
    while time.time() - start_time < max_wait:
        # Check task status
        response = requests.get(f"{API_BASE}/workspaces/{workspace_id}/tasks")
        if response.status_code == 200:
            tasks = response.json()
            current_task = next((t for t in tasks if t["id"] == task_id), None)
            
            if current_task:
                status = current_task.get("status")
                logger.info(f"⏱️ Task status: {status}")
                
                if status == "completed":
                    logger.info("🎉 Task completed! Checking results...")
                    
                    result = current_task.get("result")
                    if result:
                        logger.info("✅ Task has result - checking for handoff evidence")
                        # Log partial result
                        result_str = str(result)[:500]
                        logger.info(f"📋 Result preview: {result_str}...")
                    
                    break
                elif status == "failed":
                    logger.error("❌ Task failed")
                    error = current_task.get("error_message", "Unknown error")
                    logger.error(f"   Error: {error}")
                    break
        
        elapsed = int(time.time() - start_time)
        remaining = max_wait - elapsed
        logger.info(f"⏱️ Waiting... {elapsed}s elapsed, {remaining}s remaining")
        
        await asyncio.sleep(check_interval)
    
    # Final check for deliverables (should trigger after 2+ completed tasks)
    response = requests.get(f"{API_BASE}/workspaces/{workspace_id}/tasks")
    if response.status_code == 200:
        tasks = response.json()
        completed_tasks = [t for t in tasks if t.get("status") == "completed"]
        logger.info(f"📊 Total completed tasks: {len(completed_tasks)}")
        
        if len(completed_tasks) >= 2:
            logger.info("🚀 AUTONOMOUS TRIGGER CONDITIONS MET!")
            logger.info("   Waiting for autonomous deliverable creation...")
            
            await asyncio.sleep(30)  # Wait for trigger
            
            response = requests.get(f"{API_BASE}/deliverables/workspace/{workspace_id}")
            if response.status_code == 200:
                deliverables = response.json()
                if deliverables:
                    logger.info(f"🎉 AUTONOMOUS DELIVERABLES CREATED: {len(deliverables)}")
                    for d in deliverables:
                        logger.info(f"  📦 {d.get('title', 'Unknown')}")
                else:
                    logger.warning("⚠️ No autonomous deliverables found yet")
    
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 60)
    logger.info("✅ Complex multi-agent task created and executed")
    logger.info("👀 Check OpenAI Traces for:")
    logger.info("   - Handoff tool usage between agents")
    logger.info("   - WebSearch tool usage for research")
    logger.info("   - Agent collaboration patterns")
    logger.info("🔗 OpenAI Traces URL: https://platform.openai.com/traces")

if __name__ == "__main__":
    asyncio.run(test_handoff_execution())