#!/usr/bin/env python3
"""
TEST FINALE COMPLETO: Handoff + Tools Usage
Crea un task che richiede sia handoff tra agenti che utilizzo intensivo di tools
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

async def test_complete_final():
    """Test finale che forza handoff + tools usage"""
    
    logger.info("🚀 COMPLETE FINAL TEST: HANDOFFS + TOOLS")
    logger.info("=" * 70)
    
    # Use existing workspace
    workspace_id = "f528c2ac-1265-44f6-830e-2af84cb19204"
    
    # Get agents
    response = requests.get(f"{BASE_URL}/agents/{workspace_id}")
    agents = response.json()
    logger.info(f"✅ Found {len(agents)} agents ready for collaboration")
    
    # Create a task that FORCES both handoff AND tool usage
    research_task = {
        "workspace_id": workspace_id,
        "agent_id": agents[0]["id"],  # Start with Project Manager
        "name": "AI Industry Research & Competitive Intelligence Report",
        "description": """
**RESEARCH-INTENSIVE TASK - REQUIRES TOOLS + HANDOFFS**

You are the Project Manager leading a comprehensive AI industry research project that requires BOTH real web research AND multi-agent collaboration.

**PHASE 1 - YOUR INITIAL RESEARCH (Project Manager):**
1. **Web Research** (MUST use WebSearchTool):
   - Search for "latest AI trends 2025" 
   - Search for "OpenAI competitors analysis"
   - Search for "enterprise AI adoption statistics"
   - Gather current market data and trends

2. **Document Findings** and create initial research summary

**PHASE 2 - MANDATORY HANDOFFS (you MUST delegate):**

**→ HANDOFF TO UX/UI DESIGNER:**
- Task: Research AI tools for design and user experience
- Required: Use WebSearchTool to find "AI design tools 2025" and "UX automation tools"
- Deliverable: UX-focused AI tools analysis

**→ HANDOFF TO DATA ANALYST:**  
- Task: Analyze AI market size and growth projections
- Required: Use WebSearchTool to find "AI market size 2025" and "machine learning ROI statistics"
- Deliverable: Data-driven market analysis with numbers

**→ HANDOFF TO LEAD DEVELOPER:**
- Task: Research AI development frameworks and technical trends  
- Required: Use WebSearchTool to find "AI frameworks 2025" and "machine learning infrastructure"
- Deliverable: Technical AI ecosystem analysis

**PHASE 3 - FINAL SYNTHESIS:**
- Coordinate all handoff results
- Create comprehensive report combining all research

**CRITICAL REQUIREMENTS:**
✅ **MUST use WebSearchTool extensively** - each agent should perform multiple searches
✅ **MUST perform all 3 handoffs** - delegate specific research areas
✅ **MUST gather REAL current data** - no placeholder content
✅ **MUST coordinate final synthesis** of all inputs

**EXPECTED OUTPUT:**
- Evidence of extensive web research (multiple search queries)
- Successful handoffs to all 3 specialists  
- Real market data and current information
- Comprehensive consolidated report

**SUCCESS CRITERIA:**
- At least 10+ web searches performed across all agents
- All 3 handoffs completed successfully
- Report contains real, current data (not generic content)
- Full collaboration workflow demonstrated
""",
        "status": "pending", 
        "priority": "urgent",
        "estimated_effort_hours": 12
    }
    
    # Create the research task
    response = requests.post(f"{BASE_URL}/agents/{workspace_id}/tasks", json=research_task)
    task = response.json()
    task_id = task["id"]
    
    logger.info(f"✅ Research-intensive task created: {task_id}")
    logger.info(f"   Task: {task['name']}")
    logger.info("🔍 This task should generate:")
    logger.info("   • Multiple web searches per agent")
    logger.info("   • 3 handoffs (PM → UX → Data → Dev)")
    logger.info("   • Real-time data gathering")
    logger.info("   • Collaborative report synthesis")
    
    # Monitor execution with detailed logging
    logger.info("\n👀 MONITORING EXECUTION FOR TOOLS + HANDOFFS...")
    
    start_time = time.time()
    max_wait = 600  # 10 minutes for complex task
    check_interval = 15
    
    last_status = None
    execution_phases = []
    
    while time.time() - start_time < max_wait:
        # Check task status
        response = requests.get(f"{API_BASE}/workspaces/{workspace_id}/tasks")
        if response.status_code == 200:
            tasks = response.json()
            current_task = next((t for t in tasks if t["id"] == task_id), None)
            
            if current_task:
                status = current_task.get("status")
                
                if status != last_status:
                    logger.info(f"🔄 Status changed: {last_status} → {status}")
                    execution_phases.append({
                        "status": status,
                        "timestamp": time.time() - start_time,
                        "phase": len(execution_phases) + 1
                    })
                    last_status = status
                
                if status == "completed":
                    logger.info("🎉 TASK COMPLETED! Analyzing results...")
                    
                    result = current_task.get("result")
                    if result:
                        result_str = str(result)
                        logger.info(f"📊 Result length: {len(result_str)} characters")
                        
                        # Check for evidence of tools usage
                        tools_evidence = []
                        if "search" in result_str.lower():
                            tools_evidence.append("✅ Web search evidence found")
                        if "data" in result_str.lower() and "market" in result_str.lower():
                            tools_evidence.append("✅ Market data evidence found")
                        if "current" in result_str.lower() or "2025" in result_str:
                            tools_evidence.append("✅ Current information evidence found")
                        
                        logger.info("🔍 TOOLS USAGE EVIDENCE:")
                        for evidence in tools_evidence:
                            logger.info(f"   {evidence}")
                        
                        # Preview result
                        preview = result_str[:800] + "..." if len(result_str) > 800 else result_str
                        logger.info(f"📋 Result preview:\n{preview}")
                    
                    break
                    
                elif status == "failed":
                    logger.error("❌ Task failed")
                    error = current_task.get("error_message", "Unknown error")
                    logger.error(f"   Error: {error}")
                    break
        
        elapsed = int(time.time() - start_time)
        remaining = max_wait - elapsed
        logger.info(f"⏱️ Monitoring... {elapsed}s elapsed, {remaining}s remaining (Status: {last_status})")
        
        await asyncio.sleep(check_interval)
    
    # Final comprehensive analysis
    logger.info("\n" + "=" * 70)
    logger.info("📊 FINAL COMPREHENSIVE ANALYSIS")
    logger.info("=" * 70)
    
    # Check all completed tasks
    response = requests.get(f"{API_BASE}/workspaces/{workspace_id}/tasks")
    if response.status_code == 200:
        tasks = response.json()
        completed_tasks = [t for t in tasks if t.get("status") == "completed"]
        
        logger.info(f"📋 WORKSPACE SUMMARY:")
        logger.info(f"   • Total tasks: {len(tasks)}")
        logger.info(f"   • Completed: {len(completed_tasks)}")
        logger.info(f"   • Task names:")
        for task in completed_tasks:
            logger.info(f"     - {task.get('name', 'Unknown')}")
    
    # Check deliverables
    response = requests.get(f"{API_BASE}/deliverables/workspace/{workspace_id}")
    if response.status_code == 200:
        deliverables = response.json()
        logger.info(f"📦 DELIVERABLES: {len(deliverables)} created")
        for d in deliverables:
            logger.info(f"   📄 {d.get('title', 'Unknown')} ({d.get('type', 'unknown')})")
    
    # Execution phases summary
    logger.info(f"🔄 EXECUTION PHASES:")
    for phase in execution_phases:
        logger.info(f"   Phase {phase['phase']}: {phase['status']} at {phase['timestamp']:.1f}s")
    
    logger.info("\n🔗 CHECK OPENAI TRACES NOW FOR:")
    logger.info("   ✅ Multiple handoffs between agents")
    logger.info("   ✅ WebSearchTool usage (should see 10+ searches)")
    logger.info("   ✅ Real-time data gathering")
    logger.info("   ✅ Agent collaboration patterns")
    logger.info("   ✅ Tool execution details")
    
    logger.info(f"\n🎯 OpenAI Traces: https://platform.openai.com/traces")
    logger.info("   Look for workflows with high Tool usage counts!")

if __name__ == "__main__":
    asyncio.run(test_complete_final())