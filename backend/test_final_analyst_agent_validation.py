#!/usr/bin/env python3
"""
Test finale per validare la nuova architettura Analyst Agent
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

from database import list_tasks, get_workspace_goals, get_deliverables

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

async def test_new_analyst_agent_architecture():
    """Test completo della nuova architettura con Analyst Agent"""
    
    logger.info("🔍 TESTING NEW ANALYST AGENT ARCHITECTURE")
    
    # Step 1: Create new workspace
    workspace_data = {
        "name": "Test Analyst Agent",
        "description": "Testing the new two-stage task planning with Analyst Agent",
        "domain": "Marketing",
        "primary_goal": "Create personalized email sequences for client engagement"
    }
    
    workspace = make_request("POST", "/workspaces", workspace_data)
    if not workspace:
        logger.error("❌ Failed to create workspace")
        return False
    
    workspace_id = workspace["id"]
    logger.info(f"✅ Created test workspace: {workspace_id}")
    
    # Step 2: Wait for goal creation and task generation
    logger.info("⏳ Waiting for goal decomposition and task generation...")
    await asyncio.sleep(5)
    
    # Step 3: Check generated goals
    goals = await get_workspace_goals(workspace_id)
    logger.info(f"📊 Found {len(goals)} goals")
    
    # Step 4: Check generated tasks
    all_tasks = await list_tasks(workspace_id)
    logger.info(f"📝 Found {len(all_tasks)} tasks")
    
    # Step 5: Analyze task structure for Analyst Agent patterns
    logger.info("\n🔍 ANALYZING TASK STRUCTURE:")
    
    data_gathering_tasks = []
    assembly_tasks = []
    direct_tasks = []
    
    for task in all_tasks:
        task_name = task.get('name', '')
        task_description = task.get('description', '')
        
        logger.info(f"  📝 Task: {task_name}")
        logger.info(f"     Description: {task_description[:100]}...")
        
        # Classify tasks based on new architecture patterns
        if "Create Asset:" in task_name and ("List of" in task_name or "Document with" in task_name):
            data_gathering_tasks.append(task)
            logger.info(f"     ✅ IDENTIFIED: Data Gathering Task")
        elif "Final" in task_name and "using" in task_description.lower():
            assembly_tasks.append(task)
            logger.info(f"     ✅ IDENTIFIED: Assembly Task")
        elif "Create Asset:" in task_name:
            direct_tasks.append(task)
            logger.info(f"     ✅ IDENTIFIED: Direct Task")
    
    logger.info(f"\n📊 TASK CLASSIFICATION RESULTS:")
    logger.info(f"  🔍 Data Gathering Tasks: {len(data_gathering_tasks)}")
    logger.info(f"  🔧 Assembly Tasks: {len(assembly_tasks)}")
    logger.info(f"  🎯 Direct Tasks: {len(direct_tasks)}")
    
    # Step 6: Wait for task execution
    logger.info("\n⏳ Waiting for task execution...")
    await asyncio.sleep(15)
    
    # Step 7: Check task results
    completed_tasks = await list_tasks(workspace_id, status="completed")
    logger.info(f"\n✅ Completed tasks: {len(completed_tasks)}")
    
    # Step 8: Analyze task results for content quality
    logger.info("\n🔍 ANALYZING TASK RESULTS:")
    high_quality_results = 0
    low_quality_results = 0
    
    for task in completed_tasks:
        result = task.get('result', '')
        if isinstance(result, str):
            result_text = result
        else:
            result_text = str(result)
        
        task_name = task.get('name', 'Unknown')
        logger.info(f"  📝 Task: {task_name}")
        logger.info(f"     Result preview: {result_text[:150]}...")
        
        # Quality assessment
        if any(pattern in result_text.lower() for pattern in [
            "step 1", "step 2", "create a plan", "outline", "template", 
            "structure the", "framework for", "approach to"
        ]):
            low_quality_results += 1
            logger.info(f"     ❌ LOW QUALITY: Contains planning/template language")
        elif any(pattern in result_text for pattern in [
            "Subject:", "Dear", "testimonial", "specific", "data", 
            "example", "client", "product"
        ]):
            high_quality_results += 1
            logger.info(f"     ✅ HIGH QUALITY: Contains concrete content")
        else:
            logger.info(f"     ⚡ NEUTRAL: Unable to classify")
    
    # Step 9: Check deliverables
    await asyncio.sleep(5)
    deliverables = await get_deliverables(workspace_id)
    logger.info(f"\n📦 Found {len(deliverables)} deliverables")
    
    warning_deliverables = 0
    good_deliverables = 0
    
    for deliverable in deliverables:
        deliverable_type = deliverable.get('type', '')
        title = deliverable.get('title', '')
        
        logger.info(f"  📦 Deliverable: {title}")
        logger.info(f"     Type: {deliverable_type}")
        
        if deliverable_type == "low_value_warning":
            warning_deliverables += 1
            logger.info(f"     ⚠️ WARNING DELIVERABLE DETECTED")
        else:
            good_deliverables += 1
            logger.info(f"     ✅ GOOD DELIVERABLE")
    
    # Step 10: Final assessment
    logger.info(f"\n🎯 FINAL ASSESSMENT:")
    logger.info(f"  📊 Tasks - Data Gathering: {len(data_gathering_tasks)}, Assembly: {len(assembly_tasks)}, Direct: {len(direct_tasks)}")
    logger.info(f"  📊 Results - High Quality: {high_quality_results}, Low Quality: {low_quality_results}")
    logger.info(f"  📊 Deliverables - Good: {good_deliverables}, Warning: {warning_deliverables}")
    
    # Success criteria
    architecture_working = (len(data_gathering_tasks) > 0 or len(assembly_tasks) > 0) or len(direct_tasks) > 0
    content_improved = high_quality_results > low_quality_results
    fewer_warnings = warning_deliverables == 0
    
    success = architecture_working and content_improved and fewer_warnings
    
    logger.info(f"\n🏆 TEST RESULT: {'✅ SUCCESS' if success else '❌ FAILURE'}")
    logger.info(f"  - New Architecture Working: {'✅' if architecture_working else '❌'}")
    logger.info(f"  - Content Quality Improved: {'✅' if content_improved else '❌'}")
    logger.info(f"  - Fewer Warning Deliverables: {'✅' if fewer_warnings else '❌'}")
    
    # Save detailed results
    test_results = {
        "timestamp": datetime.now().isoformat(),
        "workspace_id": workspace_id,
        "architecture_working": architecture_working,
        "content_improved": content_improved,
        "fewer_warnings": fewer_warnings,
        "overall_success": success,
        "task_classification": {
            "data_gathering": len(data_gathering_tasks),
            "assembly": len(assembly_tasks),
            "direct": len(direct_tasks)
        },
        "content_quality": {
            "high_quality": high_quality_results,
            "low_quality": low_quality_results
        },
        "deliverables": {
            "good": good_deliverables,
            "warning": warning_deliverables
        }
    }
    
    with open(f"analyst_agent_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        json.dump(test_results, f, indent=2)
    
    return success

if __name__ == "__main__":
    asyncio.run(test_new_analyst_agent_architecture())