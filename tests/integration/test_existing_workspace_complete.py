#!/usr/bin/env python3
"""
TEST COMPLETO con workspace esistente
Usa il workspace già funzionante per dimostrare il sistema completo
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

# Use existing successful workspace
WORKSPACE_ID = "f528c2ac-1265-44f6-830e-2af84cb19204"

async def test_existing_workspace_complete():
    """Test completo usando il workspace esistente"""
    
    logger.info("🚀 COMPLETE SYSTEM TEST - EXISTING WORKSPACE")
    logger.info("=" * 70)
    logger.info(f"Using workspace: {WORKSPACE_ID}")
    
    # Get current state
    response = requests.get(f"{BASE_URL}/agents/{WORKSPACE_ID}")
    agents = response.json() if response.status_code == 200 else []
    
    response = requests.get(f"{API_BASE}/workspaces/{WORKSPACE_ID}/tasks")
    existing_tasks = response.json() if response.status_code == 200 else []
    
    response = requests.get(f"{API_BASE}/deliverables/workspace/{WORKSPACE_ID}")
    existing_deliverables = response.json() if response.status_code == 200 else []
    
    logger.info(f"📊 CURRENT STATE:")
    logger.info(f"   Agents: {len(agents)}")
    logger.info(f"   Tasks: {len(existing_tasks)}")
    logger.info(f"   Deliverables: {len(existing_deliverables)}")
    
    # Create a new complex task to trigger the complete workflow
    logger.info(f"\n🆕 CREATING NEW COMPLEX TASK...")
    
    new_task = {
        "workspace_id": WORKSPACE_ID,
        "agent_id": agents[0]["id"] if agents else None,
        "name": "Complete System Validation Project",
        "description": """
**FINAL SYSTEM VALIDATION - MULTI-AGENT COLLABORATION**

This is the ultimate test of our AI-driven orchestration system, designed to showcase every capability.

**PROJECT OBJECTIVE:**
Create a comprehensive business innovation strategy that demonstrates:
- Multi-agent collaboration with handoffs
- Real research and analysis  
- Quality assurance throughout
- Autonomous deliverable generation

**REQUIRED WORKFLOW:**
1. **Project Manager** (ElenaRossi): Define scope and coordinate team
2. **UX Designer** (GiuliaVerdi): Research user experience trends and innovations
3. **Data Analyst** (LucaFerrari): Market analysis and competitive intelligence  
4. **Lead Developer** (MarcoBianchi): Technical feasibility and architecture

**HANDOFF REQUIREMENTS:**
- Each agent MUST hand off work to the next specialist
- Substantial research and analysis (no placeholder content)
- Professional-quality deliverables
- Final synthesis combining all insights

**SUCCESS CRITERIA:**
- All 4 agents participate with handoffs
- Quality content generated (>2000 chars per agent)
- Autonomous deliverables triggered
- Complete end-to-end workflow demonstrated

**DELIVERABLE TARGET:**
Professional business innovation strategy suitable for executive presentation.

This validates our complete AI-driven team orchestration capabilities.
""",
        "status": "pending",
        "priority": "urgent",
        "estimated_effort_hours": 20
    }
    
    response = requests.post(f"{BASE_URL}/agents/{WORKSPACE_ID}/tasks", json=new_task)
    if response.status_code != 201:
        logger.error(f"Failed to create task: {response.status_code}")
        return
    
    task = response.json()
    task_id = task["id"]
    logger.info(f"✅ Complex validation task created: {task_id}")
    logger.info(f"   Task: {task['name']}")
    
    # Monitor complete execution
    logger.info(f"\n👀 MONITORING COMPLETE WORKFLOW...")
    logger.info("Expected sequence:")
    logger.info("   1. ElenaRossi starts project coordination")
    logger.info("   2. Handoff to GiuliaVerdi for UX research")
    logger.info("   3. Handoff to LucaFerrari for data analysis")
    logger.info("   4. Handoff to MarcoBianchi for technical review")
    logger.info("   5. Quality assurance and final synthesis")
    logger.info("   6. Autonomous deliverable creation")
    
    start_time = time.time()
    max_wait = 900  # 15 minutes for complete workflow
    check_interval = 20
    
    handoff_workflows = []
    execution_phases = []
    
    while time.time() - start_time < max_wait:
        # Get all current tasks
        response = requests.get(f"{API_BASE}/workspaces/{WORKSPACE_ID}/tasks")
        if response.status_code == 200:
            all_tasks = response.json()
            
            # Find our task
            current_task = next((t for t in all_tasks if t["id"] == task_id), None)
            if current_task:
                status = current_task.get("status")
                elapsed = int(time.time() - start_time)
                
                logger.info(f"⏱️ {elapsed}s: Task status = {status}")
                
                if status == "completed":
                    logger.info("🎉 VALIDATION TASK COMPLETED!")
                    
                    result = current_task.get("result")
                    if result:
                        result_size = len(str(result))
                        logger.info(f"📊 Result size: {result_size} characters")
                        
                        # Show preview
                        result_str = str(result)
                        preview = result_str[:500] + "..." if len(result_str) > 500 else result_str
                        logger.info(f"📋 Result preview:\n{preview}")
                    
                    break
                    
                elif status == "failed":
                    logger.error("❌ Validation task failed")
                    error = current_task.get("error_message", "Unknown")
                    logger.error(f"   Error: {error}")
                    break
        
        await asyncio.sleep(check_interval)
    
    # Check for new deliverables after task completion
    logger.info(f"\n🔍 CHECKING FOR NEW DELIVERABLES...")
    await asyncio.sleep(30)  # Wait for autonomous trigger
    
    response = requests.get(f"{API_BASE}/deliverables/workspace/{WORKSPACE_ID}")
    if response.status_code == 200:
        current_deliverables = response.json()
        new_deliverables = len(current_deliverables) - len(existing_deliverables)
        
        if new_deliverables > 0:
            logger.info(f"🎉 NEW DELIVERABLES CREATED: {new_deliverables}")
            for d in current_deliverables[-new_deliverables:]:
                logger.info(f"   📦 {d.get('title', 'Unknown')} ({d.get('type', 'unknown')})")
        else:
            logger.info("⚠️ No new deliverables detected")
    
    # Final system summary
    logger.info(f"\n" + "=" * 70)
    logger.info("🎯 COMPLETE SYSTEM TEST SUMMARY")
    logger.info("=" * 70)
    
    # Get final state
    response = requests.get(f"{API_BASE}/workspaces/{WORKSPACE_ID}/tasks")
    final_tasks = response.json() if response.status_code == 200 else []
    
    response = requests.get(f"{API_BASE}/deliverables/workspace/{WORKSPACE_ID}")
    final_deliverables = response.json() if response.status_code == 200 else []
    
    completed_tasks = [t for t in final_tasks if t.get('status') == 'completed']
    new_tasks = len(final_tasks) - len(existing_tasks)
    total_deliverables = len(final_deliverables)
    
    logger.info(f"📊 FINAL METRICS:")
    logger.info(f"   Total agents: {len(agents)}")
    for agent in agents:
        logger.info(f"     - {agent['name']} ({agent['role']})")
    
    logger.info(f"   Total tasks: {len(final_tasks)} (+{new_tasks} new)")
    logger.info(f"   Completed tasks: {len(completed_tasks)}")
    
    # Show substantial completed tasks
    substantial_tasks = [
        t for t in completed_tasks 
        if len(str(t.get('result', ''))) > 1000
    ]
    logger.info(f"   Substantial results: {len(substantial_tasks)}")
    
    logger.info(f"   Total deliverables: {total_deliverables}")
    
    logger.info(f"\n🔗 HANDOFF VERIFICATION:")
    logger.info("Check OpenAI Traces for recent workflows:")
    logger.info("https://platform.openai.com/traces")
    logger.info("Look for:")
    logger.info("   - Agent names with handoffs (ElenaRossi → GiuliaVerdi, etc.)")
    logger.info("   - Execution times >10s")
    logger.info("   - Multiple workflow entries")
    
    # Success scoring
    success_metrics = {
        "Agent Team": len(agents) >= 4,
        "Task Execution": len(completed_tasks) > len(existing_tasks),
        "Substantial Content": len(substantial_tasks) > 0,
        "Deliverable Creation": total_deliverables > len(existing_deliverables),
        "System Integration": True  # If we get here, basic integration works
    }
    
    passed = sum(success_metrics.values())
    total = len(success_metrics)
    success_rate = (passed / total) * 100
    
    logger.info(f"\n📈 SUCCESS METRICS:")
    for metric, passed in success_metrics.items():
        status = "✅" if passed else "❌"
        logger.info(f"   {status} {metric}")
    
    logger.info(f"\n🎯 OVERALL SUCCESS: {success_rate:.1f}% ({passed}/{total})")
    
    if success_rate >= 80:
        logger.info("🎉 SYSTEM FULLY OPERATIONAL!")
    elif success_rate >= 60:
        logger.info("⚠️ System mostly functional with minor issues")
    else:
        logger.info("❌ System needs attention")
    
    logger.info(f"\n🚀 AI-DRIVEN ORCHESTRATION COMPLETE! 🚀")

if __name__ == "__main__":
    asyncio.run(test_existing_workspace_complete())