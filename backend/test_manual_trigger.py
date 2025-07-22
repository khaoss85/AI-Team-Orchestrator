#!/usr/bin/env python3
"""
Test manuale del trigger autonomo dei deliverable
Crea workspace, task e li completa per verificare il trigger
"""

import asyncio
import requests
import json
import time
from datetime import datetime
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

async def test_manual_trigger():
    """Test manuale del trigger autonomo"""
    
    logger.info("🚀 MANUAL TRIGGER TEST - Creating scenario for autonomous deliverable trigger")
    
    # Step 1: Create workspace
    workspace_data = {
        "name": "Manual Trigger Test",
        "description": "Testing autonomous deliverable trigger with manual task completion"
    }
    
    response = requests.post(f"{API_BASE}/workspaces", json=workspace_data)
    if response.status_code != 201:
        logger.error(f"Failed to create workspace: {response.status_code}")
        return
    
    workspace = response.json()
    workspace_id = workspace["id"]
    logger.info(f"✅ Workspace created: {workspace_id}")
    
    # Step 2: Create tasks manually
    tasks = []
    for i in range(3):
        task_data = {
            "workspace_id": workspace_id,
            "name": f"Test Task {i+1} - Analysis and Documentation",
            "description": f"Complete analysis of system component {i+1} and create comprehensive documentation",
            "status": "pending",
            "priority": 100 - i*10,
            "estimated_effort_hours": 4
        }
        
        response = requests.post(f"{BASE_URL}/workspaces/{workspace_id}/tasks", json=task_data)
        if response.status_code == 201:
            task = response.json()
            tasks.append(task)
            logger.info(f"✅ Task created: {task['name']}")
        else:
            logger.error(f"Failed to create task: {response.status_code}")
    
    if len(tasks) < 2:
        logger.error("Not enough tasks created for trigger test")
        return
    
    # Step 3: Complete tasks with substantial results
    from database import update_task_status
    
    completed = 0
    for i, task in enumerate(tasks[:2]):  # Complete first 2 tasks
        try:
            result_payload = {
                "execution_time": 120.5,
                "result": f"""
## Task Completion Report: {task['name']}

### Executive Summary
Successfully completed comprehensive analysis and documentation for system component {i+1}.

### Key Findings
1. **Performance Analysis**: System component shows 95% efficiency under normal load
2. **Bottlenecks Identified**: Database queries taking >500ms need optimization
3. **Security Assessment**: All critical vulnerabilities patched, 2 minor issues remain

### Deliverables Created
- Technical documentation (45 pages)
- Architecture diagrams (12 diagrams)
- Performance benchmarks report
- Security audit report

### Recommendations
1. Implement caching layer for frequent queries
2. Upgrade database connection pooling
3. Add monitoring for real-time performance tracking

### Metrics Achieved
- Documentation coverage: 100%
- Code review completion: 100%
- Test coverage: 87%
- Performance improvement: 23%

This comprehensive analysis provides the foundation for the next phase of development.
""",
                "status": "completed",
                "quality_score": 0.92
            }
            
            # Update task status using database function
            await update_task_status(task["id"], "completed", result_payload)
            completed += 1
            logger.info(f"✅ Task {task['id']} marked as completed with substantial content")
            
            # Small delay between completions
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"Error completing task {task['id']}: {e}")
    
    logger.info(f"📊 Completed {completed} tasks with substantial results")
    
    # Step 4: Wait and check for autonomous trigger
    logger.info("⏳ Waiting for autonomous deliverable trigger...")
    logger.info("   The trigger should activate after detecting 2+ completed tasks")
    
    # Monitor server logs in real-time (if possible)
    start_time = time.time()
    max_wait = 120  # 2 minutes
    check_interval = 10
    
    while time.time() - start_time < max_wait:
        # Check for deliverables
        response = requests.get(f"{API_BASE}/deliverables/workspace/{workspace_id}")
        
        if response.status_code == 200:
            deliverables = response.json()
            if deliverables and len(deliverables) > 0:
                logger.info(f"🎉 AUTONOMOUS TRIGGER SUCCESS!")
                logger.info(f"✅ Found {len(deliverables)} deliverables created autonomously")
                
                for d in deliverables:
                    logger.info(f"  📋 {d.get('title', 'Unknown')} - {d.get('type', 'Unknown')}")
                
                return
        
        elapsed = int(time.time() - start_time)
        logger.info(f"⏱️ Waiting... {elapsed}s elapsed (checking every {check_interval}s)")
        await asyncio.sleep(check_interval)
    
    logger.warning("⚠️ No autonomous deliverables detected within timeout")
    logger.info("   This may indicate the trigger needs investigation")
    
    # Final check - list all tasks
    response = requests.get(f"{API_BASE}/workspaces/{workspace_id}/tasks")
    if response.status_code == 200:
        all_tasks = response.json()
        completed_count = sum(1 for t in all_tasks if t.get('status') == 'completed')
        logger.info(f"📊 Final task status: {completed_count}/{len(all_tasks)} completed")

if __name__ == "__main__":
    asyncio.run(test_manual_trigger())