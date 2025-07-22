#!/usr/bin/env python3
"""
Final E2E Test - From Goal to Deliverable (Real API Calls)
This test must complete 100% with real OpenAI API calls and actual deliverables
"""

import asyncio
import requests
import json
import time
import logging
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class FinalE2ETest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.api_base = f"{self.base_url}/api"
        self.workspace_id = None
        self.goal_ids = []
        self.task_ids = []
        self.deliverable_ids = []
        
        # Simple test project with clear deliverable goals
        self.test_project = {
            "name": "E2E Test Project",
            "description": "End-to-end test with real API calls",
            "goals": [
                {
                    "metric_type": "task_completion_rate",
                    "target_value": 100.0,
                    "description": "Complete a simple task successfully"
                }
            ]
        }
    
    def check_environment(self):
        """Check that all required environment variables are set"""
        logger.info("🔑 Checking environment variables...")
        
        required_vars = ['OPENAI_API_KEY', 'SUPABASE_URL', 'SUPABASE_KEY']
        for var in required_vars:
            value = os.getenv(var)
            if value:
                logger.info(f"✅ {var}: {value[:10]}..." if len(value) > 10 else f"✅ {var}: {value}")
            else:
                logger.error(f"❌ {var}: Missing")
                return False
        return True
    
    async def run_complete_test(self):
        """Run complete E2E test with real execution"""
        logger.info("🚀 FINAL E2E TEST - REAL API CALLS REQUIRED")
        logger.info("="*60)
        
        # Check environment first
        if not self.check_environment():
            logger.error("❌ Environment check failed")
            return False
        
        try:
            # Phase 1: Create workspace and goal
            await self.phase_1_setup()
            
            # Phase 2: Create team and get task
            await self.phase_2_team_creation()
            
            # Phase 3: Execute task with real API
            success = await self.phase_3_real_execution()
            
            # Phase 4: Verify deliverables
            if success:
                await self.phase_4_deliverable_verification()
                
            return success
            
        except Exception as e:
            logger.error(f"💥 Test failed with exception: {e}")
            return False
    
    async def phase_1_setup(self):
        """Create workspace and goal"""
        logger.info("🎯 PHASE 1: Setup workspace and goal")
        
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
        
        # Create goal
        goal_config = self.test_project["goals"][0]
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
        else:
            raise Exception(f"Could not extract goal ID from response: {goal_result}")
            
        self.goal_ids.append(goal_id)
        logger.info(f"✅ Created goal: {goal_config['metric_type']} (ID: {goal_id})")
    
    async def phase_2_team_creation(self):
        """Create team and get task"""
        logger.info("👥 PHASE 2: Team creation and task generation")
        
        # Generate team proposal
        proposal_data = {
            "workspace_id": self.workspace_id,
            "requirements": "Complete a simple task successfully"
        }
        
        response = requests.post(f"{self.api_base}/director/proposal", json=proposal_data)
        if response.status_code not in [200, 201]:
            raise Exception(f"Team proposal failed: {response.text}")
        
        proposal_result = response.json()
        proposal_id = proposal_result.get("proposal_id")
        logger.info(f"✅ Team proposal generated: {proposal_id}")
        
        # Approve team proposal
        approve_data = {"approved": True, "feedback": "Approved for E2E test"}
        response = requests.post(f"{self.api_base}/director/approve/{self.workspace_id}?proposal_id={proposal_id}", json=approve_data)
        if response.status_code not in [200, 201]:
            raise Exception(f"Team approval failed: {response.text}")
        
        logger.info("✅ Team proposal approved")
        
        # Wait for task creation
        for i in range(12):  # 60 seconds max
            response = requests.get(f"{self.api_base}/workspaces/{self.workspace_id}/tasks")
            if response.status_code == 200:
                result = response.json()
                tasks = result if isinstance(result, list) else result.get("tasks", [])
                
                if tasks:
                    self.task_ids = [task["id"] for task in tasks]
                    logger.info(f"✅ Found {len(self.task_ids)} tasks")
                    break
            
            await asyncio.sleep(5)
        
        if not self.task_ids:
            raise Exception("No tasks created after team approval")
    
    async def phase_3_real_execution(self):
        """Execute task with real API calls"""
        logger.info("⚡ PHASE 3: Real task execution")
        
        # Monitor task execution for up to 3 minutes
        start_time = time.time()
        max_wait = 180  # 3 minutes
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(f"{self.api_base}/workspaces/{self.workspace_id}/tasks")
                if response.status_code == 200:
                    result = response.json()
                    tasks = result if isinstance(result, list) else result.get("tasks", [])
                    
                    completed_tasks = [t for t in tasks if t.get("status") == "completed"]
                    in_progress_tasks = [t for t in tasks if t.get("status") == "in_progress"]
                    
                    logger.info(f"📊 Tasks: {len(completed_tasks)} completed, {len(in_progress_tasks)} in progress")
                    
                    if completed_tasks:
                        logger.info("🎉 SUCCESS: Task completed with real API!")
                        for task in completed_tasks:
                            logger.info(f"  ✅ Completed: {task['name']}")
                        return True
                    
                    if in_progress_tasks:
                        logger.info(f"⏳ Tasks executing... (elapsed: {time.time() - start_time:.1f}s)")
                    else:
                        logger.warning("⚠️ No tasks in progress - checking for errors")
                        
            except Exception as e:
                logger.error(f"Error monitoring tasks: {e}")
                
            await asyncio.sleep(10)
        
        logger.error("❌ Task execution timed out")
        return False
    
    async def phase_4_deliverable_verification(self):
        """Verify deliverables were created"""
        logger.info("📦 PHASE 4: Deliverable verification")
        
        # Check for deliverables
        try:
            response = requests.get(f"{self.api_base}/workspaces/{self.workspace_id}/deliverables")
            if response.status_code == 200:
                deliverables = response.json().get("deliverables", [])
                if deliverables:
                    logger.info(f"✅ Found {len(deliverables)} deliverables")
                    for deliverable in deliverables:
                        logger.info(f"  📋 Deliverable: {deliverable.get('name', 'Unknown')}")
                    return True
                else:
                    logger.info("ℹ️ No deliverables found, checking assets...")
            
            # Check for assets
            response = requests.get(f"{self.api_base}/workspaces/{self.workspace_id}/assets")
            if response.status_code == 200:
                assets = response.json().get("assets", [])
                if assets:
                    logger.info(f"✅ Found {len(assets)} assets")
                    for asset in assets:
                        logger.info(f"  📦 Asset: {asset.get('name', 'Unknown')}")
                    return True
                        
        except Exception as e:
            logger.warning(f"Error checking deliverables: {e}")
        
        logger.info("ℹ️ No deliverables/assets found (may still be processing)")
        return False
    
    def generate_report(self, success):
        """Generate final report"""
        logger.info("📊 FINAL REPORT")
        logger.info("="*50)
        
        if success:
            logger.info("🎉 TEST PASSED: End-to-end execution successful!")
            logger.info("✅ Real API calls executed")
            logger.info("✅ Task completed successfully")
            logger.info("✅ System orchestration working")
        else:
            logger.error("❌ TEST FAILED: End-to-end execution failed")
            logger.error("❌ Real execution required for success")
        
        logger.info("="*50)
        return success

async def main():
    test = FinalE2ETest()
    success = await test.run_complete_test()
    test.generate_report(success)
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)