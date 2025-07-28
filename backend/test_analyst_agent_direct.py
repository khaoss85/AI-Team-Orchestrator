#!/usr/bin/env python3
"""
Test diretto dell'Analyst Agent per verificare la nuova architettura
"""

import asyncio
import logging
import sys
import os
import requests
import time
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"

def make_request(method, endpoint, data=None):
    """Make HTTP request with error handling"""
    try:
        url = f"{BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Request failed: {method} {endpoint} - {e}")
        return None

async def test_analyst_agent_direct():
    """Test diretto della creazione workspace con goal complesso che richiede dati"""
    
    logger.info("🔍 TESTING ANALYST AGENT - DIRECT APPROACH")
    
    # Step 1: Create workspace with complex goal that requires data gathering
    workspace_data = {
        "name": "Analyst Agent Test - Email Marketing",
        "description": "E-commerce business selling premium outdoor gear to adventure enthusiasts",
        "domain": "E-commerce/Marketing",
        "primary_goal": "Create a personalized welcome email sequence for new customers using real client testimonials and product highlights"
    }
    
    logger.info(f"📦 Creating workspace with complex goal that should trigger Analyst Agent...")
    workspace = make_request("POST", "/workspaces", workspace_data)
    if not workspace:
        logger.error("❌ Failed to create workspace")
        return False
    
    workspace_id = workspace["id"]
    logger.info(f"✅ Created workspace: {workspace_id}")
    
    # Step 2: Wait for goal decomposition 
    logger.info("⏳ Waiting 10 seconds for goal decomposition...")
    await asyncio.sleep(10)
    
    # Step 3: Check if goals were created
    goals_response = make_request("GET", f"/api/workspaces/{workspace_id}/goals")
    if not goals_response:
        logger.error("❌ Failed to get goals")
        return False
    
    goals = goals_response.get("goals", [])
    logger.info(f"📊 Found {len(goals)} goals")
    
    if len(goals) == 0:
        logger.warning("⚠️ No goals found. Triggering manual goal decomposition...")
        # Force goal creation by calling the goal decomposition endpoint
        decomposition_response = make_request("POST", f"/workspaces/{workspace_id}/decompose-goals", {})
        if decomposition_response:
            logger.info("✅ Manual goal decomposition triggered")
            await asyncio.sleep(5)
            goals_response = make_request("GET", f"/api/workspaces/{workspace_id}/goals")
            goals = goals_response.get("goals", []) if goals_response else []
            logger.info(f"📊 After manual decomposition: {len(goals)} goals")
    
    # Step 4: Wait for task generation by goal-driven planner
    logger.info("⏳ Waiting 15 seconds for goal-driven task generation...")
    await asyncio.sleep(15)
    
    # Step 5: Check generated tasks
    tasks_response = make_request("GET", f"/api/workspaces/{workspace_id}/tasks")
    if not tasks_response:
        logger.error("❌ Failed to get tasks")
        return False
    
    tasks = tasks_response.get("tasks", [])
    logger.info(f"📝 Found {len(tasks)} tasks")
    
    # Step 6: Analyze task structure for new Analyst Agent patterns
    logger.info("\n🔍 ANALYZING TASKS FOR NEW ARCHITECTURE PATTERNS:")
    
    analyst_agent_indicators = []
    data_gathering_tasks = []
    assembly_tasks = []
    direct_tasks = []
    
    for i, task in enumerate(tasks):
        task_name = task.get('name', '')
        task_description = task.get('description', '')
        
        logger.info(f"\n  📝 TASK {i+1}: {task_name}")
        logger.info(f"     Description: {task_description[:200]}...")
        
        # Look for new architecture patterns
        if "Create Asset:" in task_name and any(indicator in task_name.lower() for indicator in [
            "list of", "document with", "testimonials", "highlights", "data", "information"
        ]):
            data_gathering_tasks.append(task)
            analyst_agent_indicators.append("data_gathering")
            logger.info(f"     🎯 ANALYST AGENT PATTERN: Data Gathering Task")
            
        elif "final" in task_name.lower() and any(indicator in task_description.lower() for indicator in [
            "using", "gathered", "previous tasks", "data from"
        ]):
            assembly_tasks.append(task)
            analyst_agent_indicators.append("assembly")
            logger.info(f"     🎯 ANALYST AGENT PATTERN: Assembly Task")
            
        elif "Create Asset:" in task_name:
            direct_tasks.append(task)
            analyst_agent_indicators.append("direct")
            logger.info(f"     🎯 ANALYST AGENT PATTERN: Direct Task")
        
        # Check task description for Analyst Agent influence
        if any(phrase in task_description.lower() for phrase in [
            "task 1 of", "task 2 of", "gather the following data", "required for the final asset"
        ]):
            logger.info(f"     ✅ ANALYST AGENT LANGUAGE DETECTED")
            analyst_agent_indicators.append("analyst_language")
    
    # Step 7: Results analysis
    logger.info(f"\n📊 ANALYST AGENT ARCHITECTURE ANALYSIS:")
    logger.info(f"  🔍 Data Gathering Tasks: {len(data_gathering_tasks)}")
    logger.info(f"  🔧 Assembly Tasks: {len(assembly_tasks)}")
    logger.info(f"  🎯 Direct Tasks: {len(direct_tasks)}")
    logger.info(f"  🤖 Analyst Agent Indicators: {len(analyst_agent_indicators)}")
    
    # Check if the new architecture is working
    new_architecture_working = len(analyst_agent_indicators) > 0
    two_stage_planning = len(data_gathering_tasks) > 0 and len(assembly_tasks) > 0
    improved_task_descriptions = len([i for i in analyst_agent_indicators if i == "analyst_language"]) > 0
    
    logger.info(f"\n🎯 ANALYST AGENT TEST RESULTS:")
    logger.info(f"  ✅ New Architecture Active: {'YES' if new_architecture_working else 'NO'}")
    logger.info(f"  ✅ Two-Stage Planning: {'YES' if two_stage_planning else 'NO'}")
    logger.info(f"  ✅ Improved Task Language: {'YES' if improved_task_descriptions else 'NO'}")
    
    # Wait for some task execution
    logger.info("\n⏳ Waiting 20 seconds for task execution...")
    await asyncio.sleep(20)
    
    # Check task completion and results
    tasks_response = make_request("GET", f"/api/workspaces/{workspace_id}/tasks")
    if tasks_response:
        updated_tasks = tasks_response.get("tasks", [])
        completed_tasks = [t for t in updated_tasks if t.get('status') == 'completed']
        logger.info(f"✅ Completed tasks: {len(completed_tasks)}")
        
        # Analyze completed task results for quality improvement
        high_quality_results = 0
        for task in completed_tasks:
            result = task.get('result', '')
            if isinstance(result, str) and any(quality_indicator in result.lower() for quality_indicator in [
                "specific", "concrete", "testimonial", "example", "data", "information"
            ]):
                high_quality_results += 1
        
        logger.info(f"✅ High-quality results: {high_quality_results}/{len(completed_tasks)}")
    
    # Final assessment
    success = new_architecture_working and (two_stage_planning or len(direct_tasks) > 0)
    
    logger.info(f"\n🏆 FINAL RESULT: {'✅ SUCCESS - ANALYST AGENT WORKING' if success else '❌ FAILURE'}")
    
    # Save test results
    test_results = {
        "timestamp": datetime.now().isoformat(),
        "workspace_id": workspace_id,
        "success": success,
        "new_architecture_working": new_architecture_working,
        "two_stage_planning": two_stage_planning,
        "improved_task_descriptions": improved_task_descriptions,
        "task_counts": {
            "total": len(tasks),
            "data_gathering": len(data_gathering_tasks),
            "assembly": len(assembly_tasks),
            "direct": len(direct_tasks)
        },
        "analyst_agent_indicators": len(analyst_agent_indicators)
    }
    
    with open(f"analyst_agent_direct_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        json.dump(test_results, f, indent=2)
    
    return success

if __name__ == "__main__":
    asyncio.run(test_analyst_agent_direct())