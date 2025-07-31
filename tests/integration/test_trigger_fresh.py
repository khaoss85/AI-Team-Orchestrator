#!/usr/bin/env python3
"""
Test del trigger autonomo con un workspace nuovo
"""

import asyncio
import requests
import json
import sys
import os
sys.path.append(os.path.dirname(__file__))

from database import should_trigger_deliverable_aggregation, get_deliverables
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

async def test_fresh_trigger():
    logger.info("🚀 FRESH TRIGGER TEST - Creating new workspace and tasks")
    
    # Step 1: Create new workspace
    workspace_data = {
        "name": "Trigger Test Workspace",
        "description": "Testing autonomous deliverable trigger"
    }
    
    response = requests.post(f"{API_BASE}/workspaces", json=workspace_data)
    if response.status_code != 201:
        logger.error(f"Failed to create workspace: {response.status_code}")
        return
    
    workspace = response.json()
    workspace_id = workspace["id"]
    logger.info(f"✅ Workspace created: {workspace_id}")
    
    # Step 2: Create tasks directly
    for i in range(3):
        task_data = {
            "workspace_id": workspace_id,
            "name": f"Analysis Task {i+1}",
            "description": f"Complete analysis of component {i+1}",
            "status": "pending",
            "priority": 100 - i*10
        }
        
        response = requests.post(f"{BASE_URL}/workspaces/{workspace_id}/tasks", json=task_data)
        if response.status_code == 201:
            logger.info(f"✅ Task {i+1} created")
        else:
            logger.error(f"Failed to create task {i+1}: {response.status_code}")
    
    # Step 3: Get task IDs
    response = requests.get(f"{API_BASE}/workspaces/{workspace_id}/tasks")
    if response.status_code != 200:
        logger.error("Failed to get tasks")
        return
        
    tasks = response.json()
    logger.info(f"📋 Found {len(tasks)} tasks")
    
    # Step 4: Complete first 2 tasks via direct database update
    from database import supabase
    from datetime import datetime
    
    completed = 0
    for task in tasks[:2]:
        task_id = task["id"]
        
        # Contenuto sostanziale per il task
        result = {
            "execution_time": 150.0,
            "result": f"""
# Task Analysis Report

## Executive Summary
Comprehensive analysis completed for {task['name']} with the following key findings and recommendations.

## Key Findings
1. **Performance Metrics**: System operating at 92% efficiency
2. **Bottlenecks Identified**: Database queries need optimization (avg 800ms)
3. **Security Status**: All critical vulnerabilities patched

## Detailed Analysis
The analysis revealed multiple opportunities for optimization:
- Implement caching layer to reduce database load by 60%
- Optimize query patterns using indexed searches
- Add monitoring for real-time performance tracking

## Recommendations
1. Immediate: Implement database query caching
2. Short-term: Refactor data access patterns
3. Long-term: Consider microservices architecture

## Metrics
- Analysis depth: Comprehensive
- Data points analyzed: 10,000+
- Confidence level: 95%
- Time to complete: 2.5 hours

This analysis provides actionable insights for immediate implementation.
""",
            "quality_score": 0.93,
            "status": "completed"
        }
        
        # Update direttamente nel database
        update_result = supabase.table("tasks").update({
            "status": "completed",
            "result": result,
            "updated_at": datetime.now().isoformat()
        }).eq("id", task_id).execute()
        
        if update_result and update_result.data:
            completed += 1
            logger.info(f"✅ Task completed: {task_id}")
        else:
            logger.error(f"❌ Failed to complete task: {task_id}")
        
        await asyncio.sleep(2)
    
    logger.info(f"📊 Completed {completed} tasks")
    
    # Step 5: Check trigger condition
    logger.info("⏳ Checking trigger condition...")
    should_trigger = await should_trigger_deliverable_aggregation(workspace_id)
    logger.info(f"🔍 Trigger evaluation: {should_trigger}")
    
    if should_trigger:
        logger.info("🎉 TRIGGER CONDITION MET!")
        
        # Il trigger dovrebbe attivarsi automaticamente nel flusso normale
        # Ma per il test, possiamo monitorare i deliverable
        logger.info("⏳ Waiting 30 seconds for autonomous deliverable creation...")
        await asyncio.sleep(30)
        
        # Check deliverables
        deliverables = await get_deliverables(workspace_id)
        if deliverables:
            logger.info(f"✅ AUTONOMOUS TRIGGER SUCCESS! Found {len(deliverables)} deliverables")
            for d in deliverables[:3]:
                logger.info(f"  📋 {d.get('title', 'Unknown')}")
        else:
            logger.info("⚠️ No deliverables found yet (may need more time)")
    else:
        logger.info("❌ Trigger condition not met")
        
        # Debug: check completed tasks
        response = requests.get(f"{API_BASE}/workspaces/{workspace_id}/tasks")
        if response.status_code == 200:
            all_tasks = response.json()
            completed_count = sum(1 for t in all_tasks if t.get('status') == 'completed')
            logger.info(f"Debug: {completed_count} completed tasks in workspace")

if __name__ == "__main__":
    asyncio.run(test_fresh_trigger())