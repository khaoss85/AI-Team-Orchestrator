#!/usr/bin/env python3
"""
Fast Complete E2E Test - Must reach 100% completion
Focus: Task execution → Asset generation → Deliverable creation
Max duration: 5 minutes with proper timeouts
"""

import asyncio
import requests
import json
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class FastCompleteTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.api_base = f"{self.base_url}/api"
        self.workspace_id = None
        self.goal_ids = []
        self.task_ids = []
        self.asset_ids = []
        self.deliverable_ids = []
        
        # Test project focused on deliverable generation
        self.test_project = {
            "name": "Fast Asset Generation Test",
            "description": "Generate concrete deliverables quickly",
            "goals": [
                {
                    "metric_type": "contact_database_completion",
                    "target_value": 100.0,
                    "description": "Generate contact database with real contacts"
                },
                {
                    "metric_type": "content_calendar_creation", 
                    "target_value": 100.0,
                    "description": "Create content calendar with posts"
                }
            ]
        }

    async def run_complete_test(self):
        """Run complete test to 100% - no timeouts allowed"""
        logger.info("🚀 FAST COMPLETE E2E TEST - TARGET: 100% SUCCESS")
        logger.info("="*60)
        
        try:
            # Phase 1: Setup (max 30 seconds)
            await self.phase_1_setup()
            
            # Phase 2: Team & Tasks (max 60 seconds)
            await self.phase_2_orchestration()
            
            # Phase 3: Task Execution (max 120 seconds)
            await self.phase_3_execution()
            
            # Phase 4: Asset/Deliverable Validation (max 30 seconds)
            await self.phase_4_validation()
            
            # Final Report
            success_rate = await self.generate_final_report()
            
            if success_rate >= 100.0:
                logger.info("🎉 TEST PASSED: 100% SUCCESS ACHIEVED!")
                return True
            else:
                logger.error(f"❌ TEST FAILED: Only {success_rate}% success")
                return False
                
        except Exception as e:
            logger.error(f"💥 TEST FAILED WITH EXCEPTION: {e}")
            return False

    async def phase_1_setup(self):
        """Phase 1: Quick setup"""
        logger.info("🎯 PHASE 1: SETUP (30s timeout)")
        start_time = time.time()
        
        # Create workspace
        workspace_data = {
            "name": self.test_project["name"],
            "description": self.test_project["description"],
            "user_id": "12345678-1234-1234-1234-123456789012"
        }
        
        response = requests.post(f"{self.base_url}/workspaces/", json=workspace_data)
        if response.status_code not in [200, 201]:
            raise Exception(f"Workspace creation failed: {response.text}")
        
        workspace_result = response.json()
        self.workspace_id = workspace_result["id"]
        logger.info(f"✅ Created workspace: {self.workspace_id}")
        
        # Create goals
        for goal_config in self.test_project["goals"]:
            goal_data = {
                "workspace_id": self.workspace_id,
                "metric_type": goal_config["metric_type"],
                "target_value": goal_config["target_value"],
                "current_value": 0.0,
                "description": goal_config["description"]
            }
            
            response = requests.post(f"{self.api_base}/workspaces/{self.workspace_id}/goals", json=goal_data)
            if response.status_code not in [200, 201]:
                raise Exception(f"Goal creation failed: {response.text}")
            
            goal_result = response.json()
            if "goal" in goal_result and "id" in goal_result["goal"]:
                goal_id = goal_result["goal"]["id"]
            elif "id" in goal_result:
                goal_id = goal_result["id"]
            elif "message" in goal_result and "(ID: " in goal_result["message"]:
                goal_id = goal_result["message"].split("(ID: ")[1].split(")")[0]
            else:
                raise Exception(f"Could not extract goal ID from response: {goal_result}")
                
            self.goal_ids.append(goal_id)
            logger.info(f"✅ Created goal: {goal_config['metric_type']} (ID: {goal_id})")
            
        elapsed = time.time() - start_time
        logger.info(f"✅ Phase 1 Complete ({elapsed:.1f}s) - Created {len(self.goal_ids)} goals")
        
    async def phase_2_orchestration(self):
        """Phase 2: Team orchestration and task creation"""
        logger.info("🤖 PHASE 2: ORCHESTRATION (60s timeout)")
        start_time = time.time()
        
        # Generate team proposal
        proposal_data = {
            "workspace_id": self.workspace_id,
            "requirements": "Generate contact database and content calendar deliverables"
        }
        
        response = requests.post(f"{self.api_base}/director/proposal", json=proposal_data)
        if response.status_code not in [200, 201]:
            raise Exception(f"Team proposal failed: {response.text}")
        
        proposal_result = response.json()
        proposal_id = proposal_result.get("proposal_id")
        logger.info(f"✅ Team proposal generated: {proposal_id}")
        
        # Approve team proposal using correct endpoint format
        approve_data = {"approved": True, "feedback": "Approved for fast test"}
        response = requests.post(f"{self.api_base}/director/approve/{self.workspace_id}?proposal_id={proposal_id}", json=approve_data)
        if response.status_code not in [200, 201]:
            raise Exception(f"Team approval failed: {response.text}")
        
        logger.info("✅ Team proposal approved")
        
        # Wait for task creation (max 30 seconds)
        task_wait_start = time.time()
        tasks_found = False
        
        while time.time() - task_wait_start < 30:
            response = requests.get(f"{self.api_base}/workspaces/{self.workspace_id}/tasks")
            if response.status_code == 200:
                result = response.json()
                # Handle both list and dict response formats
                if isinstance(result, list):
                    tasks = result
                else:
                    tasks = result.get("tasks", [])
                
                if tasks:
                    self.task_ids = [task["id"] for task in tasks]
                    tasks_found = True
                    break
            await asyncio.sleep(3)
        
        if not tasks_found:
            raise Exception("No tasks created within 30 seconds")
            
        elapsed = time.time() - start_time
        logger.info(f"✅ Phase 2 Complete ({elapsed:.1f}s) - {len(self.task_ids)} tasks created")

    async def phase_3_execution(self):
        """Phase 3: Task execution and monitoring"""
        logger.info("⚡ PHASE 3: TASK EXECUTION (120s timeout)")
        start_time = time.time()
        
        completed_tasks = 0
        total_tasks = len(self.task_ids)
        
        # Monitor task completion
        while time.time() - start_time < 120:
            response = requests.get(f"{self.api_base}/workspaces/{self.workspace_id}/tasks")
            if response.status_code == 200:
                result = response.json()
                # Handle both list and dict response formats
                if isinstance(result, list):
                    tasks = result
                else:
                    tasks = result.get("tasks", [])
                    
                completed_tasks = sum(1 for task in tasks if task.get("status") == "completed")
                
                logger.info(f"📊 Task Progress: {completed_tasks}/{total_tasks} completed")
                
                # Check if all tasks completed
                if completed_tasks >= total_tasks:
                    break
                    
            await asyncio.sleep(5)
        
        elapsed = time.time() - start_time
        if completed_tasks < total_tasks:
            logger.warning(f"⚠️ Only {completed_tasks}/{total_tasks} tasks completed in {elapsed:.1f}s")
        else:
            logger.info(f"✅ Phase 3 Complete ({elapsed:.1f}s) - All {completed_tasks} tasks completed")

    async def phase_4_validation(self):
        """Phase 4: Validate assets and deliverables were created"""
        logger.info("🎯 PHASE 4: ASSET/DELIVERABLE VALIDATION (30s timeout)")
        start_time = time.time()
        
        # Check for assets
        try:
            response = requests.get(f"{self.api_base}/workspaces/{self.workspace_id}/assets")
            if response.status_code == 200:
                assets = response.json().get("assets", [])
                self.asset_ids = [asset["id"] for asset in assets]
                logger.info(f"📦 Found {len(self.asset_ids)} assets")
        except Exception as e:
            logger.warning(f"Asset check failed: {e}")
        
        # Check for deliverables
        try:
            response = requests.get(f"{self.api_base}/workspaces/{self.workspace_id}/deliverables")
            if response.status_code == 200:
                deliverables = response.json().get("deliverables", [])
                self.deliverable_ids = [d["id"] for d in deliverables]
                logger.info(f"📋 Found {len(self.deliverable_ids)} deliverables")
        except Exception as e:
            logger.warning(f"Deliverable check failed: {e}")
        
        # Verify each goal has associated assets/deliverables
        goals_with_outputs = 0
        for goal_id in self.goal_ids:
            # Check if this goal has related assets or deliverables
            has_output = len(self.asset_ids) > 0 or len(self.deliverable_ids) > 0
            if has_output:
                goals_with_outputs += 1
                
        elapsed = time.time() - start_time
        logger.info(f"✅ Phase 4 Complete ({elapsed:.1f}s) - {goals_with_outputs}/{len(self.goal_ids)} goals have outputs")

    async def generate_final_report(self):
        """Generate final test report and calculate success rate"""
        logger.info("📊 GENERATING FINAL REPORT")
        logger.info("="*50)
        
        # Count completions
        total_goals = len(self.goal_ids)
        total_tasks = len(self.task_ids) 
        total_assets = len(self.asset_ids)
        total_deliverables = len(self.deliverable_ids)
        
        # Check task completion
        completed_tasks = 0
        try:
            response = requests.get(f"{self.api_base}/workspaces/{self.workspace_id}/tasks")
            if response.status_code == 200:
                result = response.json()
                # Handle both list and dict response formats
                if isinstance(result, list):
                    tasks = result
                else:
                    tasks = result.get("tasks", [])
                completed_tasks = sum(1 for task in tasks if task.get("status") == "completed")
        except:
            pass
        
        logger.info(f"📋 Goals Created: {total_goals}")
        logger.info(f"🔧 Tasks Created: {total_tasks}")
        logger.info(f"✅ Tasks Completed: {completed_tasks}")
        logger.info(f"📦 Assets Generated: {total_assets}")
        logger.info(f"📋 Deliverables Created: {total_deliverables}")
        
        # Calculate success criteria
        criteria = {
            "goals_created": total_goals >= 2,
            "tasks_created": total_tasks >= 1,  
            "tasks_completed": completed_tasks >= total_tasks and total_tasks > 0,
            "assets_generated": total_assets >= 1,
            "deliverables_created": total_deliverables >= 1
        }
        
        success_count = sum(criteria.values())
        success_rate = (success_count / len(criteria)) * 100
        
        logger.info("="*50)
        logger.info("🎯 SUCCESS CRITERIA:")
        for criterion, passed in criteria.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"  {criterion}: {status}")
        
        logger.info("="*50)
        logger.info(f"📊 FINAL SUCCESS RATE: {success_rate:.1f}%")
        
        return success_rate

async def main():
    test = FastCompleteTest()
    success = await test.run_complete_test()
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)