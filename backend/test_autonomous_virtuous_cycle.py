#!/usr/bin/env python3
"""
🚀 TEST AUTONOMOUS VIRTUOUS CYCLE
Verifica il ciclo completo: Esecuzione -> Asset -> QA -> Memoria -> Deliverable
partendo da zero, senza input manuali (dopo il setup iniziale).
"""

import asyncio
import requests
import json
import time
import logging
from datetime import datetime
import sys
import os
from uuid import UUID, uuid4

# Add backend to path
sys.path.append(os.path.dirname(__file__))

from database import (
    list_tasks, get_task, get_ready_tasks_python, supabase_service
)
from ai_agents.manager import AgentManager
from models import TaskStatus

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

class TestAutonomousVirtuousCycle:
    
    def __init__(self):
        self.workspace_id = None
        self.executed_task_id = None
        self.created_artifact_id = None
        self.results = {
            "test_start": datetime.now().isoformat(),
            "phases": {},
            "overall_success": False,
            "test_end": None
        }

    def _log_phase_result(self, phase_name, success, details):
        self.results["phases"][phase_name] = {"success": success, "details": details}

    async def run_full_test(self):
        logger.info("🚀 Starting AUTONOMOUS VIRTUOUS CYCLE TEST")
        logger.info("=" * 80)
        
        try:
            await self.phase_1_and_2_setup_and_execution()
            await self.phase_3_asset_and_qa_verification()
            await self.phase_4_memory_verification()
            await self.phase_5_deliverable_verification()

            failed_phases = [p for p, r in self.results["phases"].items() if not r["success"]]
            if not failed_phases:
                self.results["overall_success"] = True
                logger.info("🎉 AUTONOMOUS CYCLE VALIDATION PASSED!")
            else:
                self.results["overall_success"] = False
                logger.error(f"❌ Test FAILED. Failed phases: {failed_phases}")
            
        except Exception as e:
            logger.error(f"❌ Test execution failed critically: {e}", exc_info=True)
            self.results["overall_success"] = False
        
        self.results["test_end"] = datetime.now().isoformat()
        results_file = f"autonomous_cycle_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"💾 Results saved to: {results_file}")

    async def phase_1_and_2_setup_and_execution(self):
        logger.info(" PHASES 1 & 2: Workspace Setup, Team Creation, and Task Execution")
        
        # == PHASE 1: WORKSPACE SETUP ==
        workspace_data = {"name": "Autonomous Cycle Test", "description": "Test for the full virtuous cycle"}
        response = requests.post(f"{API_BASE}/workspaces", json=workspace_data, timeout=10)
        response.raise_for_status()
        workspace = response.json()
        self.workspace_id = workspace["id"]
        logger.info(f"✅ Workspace created: {self.workspace_id}")

        # == CREATE WORKSPACE GOALS ==
        # The system needs goals to generate tasks autonomously
        # Create goals directly in database
        from database import supabase
        import uuid
        
        goal1_data = {
            "id": str(uuid.uuid4()),
            "workspace_id": self.workspace_id,
            "description": "Create a comprehensive Python string utility library",
            "metric_type": "deliverable_string_utility",
            "target_value": 1,
            "current_value": 0,
            "status": "active",
            "priority": 1
        }
        
        goal2_data = {
            "id": str(uuid.uuid4()),
            "workspace_id": self.workspace_id,
            "description": "Implement unit tests with 90% coverage",
            "metric_type": "test_coverage",
            "target_value": 90,
            "current_value": 0,
            "status": "active",
            "priority": 2
        }
        
        # Insert goals directly
        result1 = supabase.table("workspace_goals").insert(goal1_data).execute()
        result2 = supabase.table("workspace_goals").insert(goal2_data).execute()
        
        if result1.data and result2.data:
            logger.info("✅ Workspace goals created: 2 goals")
        else:
            logger.warning("⚠️ Failed to create workspace goals")
        
        # == PHASE 2: DIRECTOR ORCHESTRATION ==
        proposal_payload = {
            "workspace_id": self.workspace_id,
            "project_description": "Develop a set of Python string utility functions.",
            "budget": 100.0, "max_team_size": 2
        }
        proposal_response = requests.post(f"{API_BASE}/director/proposal", json=proposal_payload, timeout=60)
        proposal_response.raise_for_status()
        proposal_id = proposal_response.json()["proposal_id"]
        
        approval_response = requests.post(f"{API_BASE}/director/approve/{self.workspace_id}", params={"proposal_id": proposal_id}, timeout=45)
        approval_response.raise_for_status()
        logger.info("✅ Team created and approved.")

        # === TASK GENERATION & FETCHING (Robust logic from comprehensive_e2e_with_execution.py) ===
        logger.info("--- Polling for autonomous task generation via API ---")
        ready_tasks = []
        max_wait_time = 90  # Wait for up to 90 seconds
        check_interval = 10
        
        for i in range(max_wait_time // check_interval):
            logger.info(f"Polling for tasks... (Attempt {i+1})")
            tasks_response = requests.get(f"{API_BASE}/workspaces/{self.workspace_id}/tasks", timeout=10)
            if tasks_response.status_code == 200 and tasks_response.json():
                all_tasks = tasks_response.json()
                pending_tasks = [t for t in all_tasks if t.get('status') == 'pending']
                if pending_tasks:
                    logger.info(f"✅ Found {len(pending_tasks)} pending task(s).")
                    ready_tasks = pending_tasks
                    break
            await asyncio.sleep(check_interval)

        if not ready_tasks:
            raise Exception("No ready tasks found for execution after polling the API.")

        manager = AgentManager(UUID(self.workspace_id))
        await manager.initialize()
        
        task_to_execute = ready_tasks[0]
        self.executed_task_id = task_to_execute.get('id')
        
        logger.info(f"Executing task: {task_to_execute.get('name')} ({self.executed_task_id})")
        await manager.execute_task(UUID(self.executed_task_id))
        
        self._log_phase_result("setup_and_execution", True, f"Task {self.executed_task_id} executed successfully.")

    async def phase_3_asset_and_qa_verification(self):
        logger.info(" PHASE 3: Verifying Asset Creation and QA Validation")
        
        artifact = await self._poll_for_record("asset_artifacts", "task_id", self.executed_task_id)
        
        if not artifact:
            self._log_phase_result("asset_creation", False, "Asset artifact was not created.")
            raise Exception("Asset creation failed.")
        
        self.created_artifact_id = artifact['id']
        self._log_phase_result("asset_creation", True, f"Asset {self.created_artifact_id} created.")

        validation = await self._poll_for_record("quality_validations", "artifact_id", self.created_artifact_id)

        if not validation:
            self._log_phase_result("qa_validation", False, "Quality validation was not performed.")
            raise Exception("QA validation failed.")

        score = validation.get('score', 0)
        if score < 0.7:
             self._log_phase_result("qa_validation", False, f"QA score {score} is below threshold.")
        else:
            self._log_phase_result("qa_validation", True, f"Asset passed QA with score {score}.")

    async def phase_4_memory_verification(self):
        logger.info(" PHASE 4: Verifying Memory Insight Creation")
        insight = await self._poll_for_record("workspace_insights", "task_id", self.executed_task_id)

        if not insight:
            self._log_phase_result("memory_creation", False, "Memory insight was not created.")
            raise Exception("Memory insight creation failed.")
        
        self._log_phase_result("memory_creation", True, f"Insight of type '{insight['insight_type']}' created.")

    async def phase_5_deliverable_verification(self):
        logger.info(" PHASE 5: Verifying Autonomous Deliverable Aggregation")
        deliverable = await self._poll_for_record("deliverables", "workspace_id", self.workspace_id, timeout=60)

        if not deliverable:
            self._log_phase_result("deliverable_aggregation", False, "Autonomous deliverable aggregation did not trigger.")
            raise Exception("Deliverable aggregation failed.")

        if self.created_artifact_id and self.created_artifact_id not in deliverable.get('content', ''):
             self._log_phase_result("deliverable_aggregation", False, "Deliverable content does not contain the created asset.")
        else:
            self._log_phase_result("deliverable_aggregation", True, "Deliverable created and contains the correct asset.")

    async def _poll_for_record(self, table, column, value, timeout=30, interval=5):
        logger.info(f"Polling DB table '{table}' for '{column}' = '{value}'...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                res = supabase_service.table(table).select("*").eq(column, value).limit(1).execute()
                if res.data:
                    logger.info(f"Found record in '{table}'.")
                    return res.data[0]
            except Exception as e:
                logger.error(f"Polling error: {e}")
            await asyncio.sleep(interval)
        logger.error(f"Timeout: Could not find record in '{table}' after {timeout}s.")
        return None

async def main():
    test = TestAutonomousVirtuousCycle()
    await test.run_full_test()

if __name__ == "__main__":
    asyncio.run(main())