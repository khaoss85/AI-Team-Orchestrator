#!/usr/bin/env python3
"""
🚀 QUICK TASK EXECUTION TEST - Post SDK Update
================================================================================
Test mirato per verificare se l'aggiornamento dell'SDK ha risolto i problemi
di esecuzione dei task.
"""

import requests
import time
import json
import logging
from uuid import uuid4

# --- Configuration ---
BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 180  # 3 minuti per test rapido

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_quick_task_test():
    """
    Test veloce per verificare l'esecuzione di un singolo task
    """
    try:
        # --- STEP 1: Crea workspace semplice ---
        logging.info("=== STEP 1: Creating test workspace ===")
        workspace_data = {
            "name": f"Quick Task Test - {uuid4()}",
            "goal": "Write a simple hello world message."
        }
        response = requests.post(f"{BASE_URL}/api/workspaces/", json=workspace_data, timeout=10)
        assert response.status_code in [200, 201], f"Workspace creation failed: {response.text}"
        workspace = response.json()
        workspace_id = workspace['id']
        logging.info(f"✅ Workspace created: {workspace_id}")

        # --- STEP 2: Crea goal semplice ---
        logging.info("=== STEP 2: Creating simple goal ===")
        goal_data = {
            "workspace_id": workspace_id,
            "description": "Complete hello world task successfully",
            "metric_type": "deliverable_quality",
            "target_value": 80.0,
        }
        response = requests.post(f"{BASE_URL}/api/workspaces/{workspace_id}/goals", json=goal_data, timeout=10)
        assert response.status_code in [200, 201], f"Goal creation failed: {response.text}"
        logging.info("✅ Goal created")

        # --- STEP 3: Genera proposta minimale ---
        logging.info("=== STEP 3: Generating team proposal ===")
        proposal_data = {"workspace_id": workspace_id}
        response = requests.post(f"{BASE_URL}/api/director/proposal", json=proposal_data, timeout=60)
        assert response.status_code == 200, f"Team proposal failed: {response.text}"
        proposal = response.json()
        proposal_id = proposal['proposal_id']
        logging.info(f"✅ Team proposal generated: {proposal_id}")

        # --- STEP 4: Approva proposta ---
        logging.info("=== STEP 4: Approving proposal ===")
        response = requests.post(
            f"{BASE_URL}/api/director/approve/{workspace_id}?proposal_id={proposal_id}",
            timeout=30
        )
        assert response.status_code == 200, f"Proposal approval failed: {response.text}"
        logging.info("✅ Proposal approved")

        # --- STEP 5: Attendi creazione task ---
        logging.info("=== STEP 5: Waiting for task creation ===")
        tasks_created = False
        for attempt in range(6):  # 30 seconds max
            time.sleep(5)
            response = requests.get(f"{BASE_URL}/api/workspaces/{workspace_id}/tasks", timeout=10)
            if response.status_code == 200:
                tasks = response.json()
                if tasks and len(tasks) > 0:
                    logging.info(f"✅ Tasks created! Found {len(tasks)} tasks")
                    tasks_created = True
                    break
            logging.info(f"⏳ Attempt {attempt + 1}/6: Waiting for tasks...")
        
        assert tasks_created, "No tasks were created within expected timeframe"

        # --- STEP 6: Monitora esecuzione per tempo limitato ---
        logging.info("=== STEP 6: Monitoring task execution ===")
        start_time = time.time()
        
        while time.time() - start_time < TEST_TIMEOUT:
            elapsed_time = int(time.time() - start_time)
            
            # Check tasks status
            response = requests.get(f"{BASE_URL}/api/workspaces/{workspace_id}/tasks", timeout=10)
            if response.status_code == 200:
                tasks = response.json()
                
                task_summary = {
                    "total": len(tasks),
                    "pending": len([t for t in tasks if t["status"] == "pending"]),
                    "in_progress": len([t for t in tasks if t["status"] == "in_progress"]),
                    "completed": len([t for t in tasks if t["status"] == "completed"]),
                    "failed": len([t for t in tasks if t["status"] == "failed"])
                }
                
                logging.info(f"⏱️  Time: {elapsed_time}s - Tasks: {task_summary}")
                
                # Success conditions
                if task_summary["completed"] > 0:
                    logging.info("🎉 SUCCESS: At least one task completed!")
                    
                    # Show completed task details
                    completed_tasks = [t for t in tasks if t["status"] == "completed"]
                    for task in completed_tasks[:1]:  # Show first completed task
                        logging.info(f"📝 Completed task: {task['name']}")
                        logging.info(f"   Result: {task.get('result', 'No result')[:100]}...")
                    
                    return True
                
                # Check for failed tasks
                if task_summary["failed"] > 0:
                    failed_tasks = [t for t in tasks if t["status"] == "failed"]
                    for task in failed_tasks[:1]:  # Show first failed task
                        logging.error(f"❌ Failed task: {task['name']}")
                        logging.error(f"   Result: {task.get('result', 'No result')}")
                    
                    # Continue monitoring - maybe other tasks will succeed
            
            time.sleep(10)  # Check every 10 seconds
        
        logging.warning(f"⏰ Test timeout after {TEST_TIMEOUT} seconds")
        return False
        
    except Exception as e:
        logging.error(f"❌ Quick task test failed: {e}")
        return False

if __name__ == "__main__":
    success = run_quick_task_test()
    if success:
        logging.info("🎉 Quick task test PASSED!")
        exit(0)
    else:
        logging.error("❌ Quick task test FAILED!")
        exit(1)