#!/usr/bin/env python3
"""
🚀 TEST AUTONOMOUS DELIVERABLE TRIGGER
Test specifico per verificare il trigger autonomo dei deliverable
"""

import asyncio
import requests
import json
import time
import logging
from datetime import datetime
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(__file__))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

class AutonomousDeliverableTriggerTest:
    """
    Test minimo per verificare il trigger autonomo dei deliverable
    """
    
    def __init__(self):
        self.workspace_id = None
        self.agent_ids = []
        self.task_ids = []
        self.results = {
            "test_start": datetime.now().isoformat(),
            "workspace_id": None,
            "tasks_executed": 0,
            "deliverables_generated": 0,
            "trigger_activated": False,
            "test_success": False
        }
    
    async def run_test(self):
        """Esegue il test del trigger autonomo"""
        
        logger.info("🚀 Starting AUTONOMOUS DELIVERABLE TRIGGER TEST")
        logger.info("=" * 60)
        
        try:
            # Step 1: Create workspace
            await self.step_1_create_workspace()
            
            # Step 2: Create team
            await self.step_2_create_team()
            
            # Step 3: Wait for task generation
            await self.step_3_wait_for_tasks()
            
            # Step 4: Execute tasks manually (simulating AgentManager)
            await self.step_4_execute_tasks()
            
            # Step 5: Wait and check for autonomous deliverable
            await self.step_5_check_deliverable_trigger()
            
            # Determine success
            if self.results["deliverables_generated"] > 0:
                self.results["test_success"] = True
                logger.info("🎉 AUTONOMOUS DELIVERABLE TRIGGER TEST PASSED!")
            else:
                logger.error("❌ Test FAILED - No autonomous deliverables generated")
            
            self.results["test_end"] = datetime.now().isoformat()
            
            # Save results
            results_file = f"autonomous_deliverable_trigger_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            
            logger.info(f"💾 Results saved to: {results_file}")
            
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    async def step_1_create_workspace(self):
        """Create test workspace"""
        logger.info("📁 STEP 1: CREATE WORKSPACE")
        
        workspace_data = {
            "name": "Autonomous Deliverable Test",
            "description": "Test workspace for autonomous deliverable trigger"
        }
        
        response = requests.post(f"{API_BASE}/workspaces", json=workspace_data)
        if response.status_code == 201:
            workspace = response.json()
            self.workspace_id = workspace["id"]
            self.results["workspace_id"] = self.workspace_id
            logger.info(f"✅ Workspace created: {self.workspace_id}")
        else:
            raise Exception(f"Workspace creation failed: {response.status_code}")
    
    async def step_2_create_team(self):
        """Create and approve team"""
        logger.info("👥 STEP 2: CREATE TEAM")
        
        # Create proposal
        proposal_payload = {
            "workspace_id": self.workspace_id,
            "project_description": "Create a simple analysis project to test deliverable generation",
            "budget": 1000.0,
            "max_team_size": 3
        }
        
        proposal_response = requests.post(f"{API_BASE}/director/proposal", json=proposal_payload, timeout=60)
        if proposal_response.status_code != 200:
            raise Exception(f"Proposal failed: {proposal_response.status_code}")
        
        proposal_data = proposal_response.json()
        proposal_id = proposal_data["proposal_id"]
        
        # Approve proposal
        approval_response = requests.post(f"{API_BASE}/director/approve/{self.workspace_id}", 
                                        params={"proposal_id": proposal_id}, timeout=45)
        
        if approval_response.status_code in [200, 204]:
            approval_data = approval_response.json()
            self.agent_ids = approval_data.get("created_agent_ids", [])
            logger.info(f"✅ Team created with {len(self.agent_ids)} agents")
        else:
            raise Exception(f"Approval failed: {approval_response.status_code}")
    
    async def step_3_wait_for_tasks(self):
        """Wait for task generation"""
        logger.info("📋 STEP 3: WAIT FOR TASK GENERATION")
        
        max_wait = 120
        check_interval = 10
        
        for i in range(max_wait // check_interval):
            await asyncio.sleep(check_interval)
            
            tasks_response = requests.get(f"{API_BASE}/workspaces/{self.workspace_id}/tasks")
            if tasks_response.status_code == 200:
                tasks = tasks_response.json()
                if len(tasks) > 0:
                    self.task_ids = [task["id"] for task in tasks]
                    logger.info(f"✅ Found {len(tasks)} tasks")
                    return
            
            logger.info(f"⏳ Waiting for tasks... {(i+1)*check_interval}s")
        
        raise Exception("No tasks generated within timeout")
    
    async def step_4_execute_tasks(self):
        """Execute tasks to trigger deliverable generation"""
        logger.info("🔧 STEP 4: EXECUTE TASKS")
        
        # We'll manually update task status to simulate execution
        # In production, AgentManager would do this
        
        executed = 0
        for task_id in self.task_ids[:2]:  # Execute first 2 tasks
            try:
                # Simulate task completion with result
                result_payload = {
                    "result": f"Task {task_id} completed successfully with analysis results",
                    "execution_time": 5.0,
                    "status": "completed"
                }
                
                # Update task status directly via API
                update_response = requests.patch(
                    f"{API_BASE}/tasks/{task_id}",
                    json={
                        "status": "completed",
                        "result": result_payload
                    }
                )
                
                if update_response.status_code in [200, 204]:
                    executed += 1
                    logger.info(f"✅ Task {task_id} marked as completed")
                else:
                    logger.warning(f"Failed to update task {task_id}: {update_response.status_code}")
                
                # Small delay between tasks
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error executing task {task_id}: {e}")
        
        self.results["tasks_executed"] = executed
        logger.info(f"📊 Executed {executed} tasks")
    
    async def step_5_check_deliverable_trigger(self):
        """Check if deliverable was triggered autonomously"""
        logger.info("📦 STEP 5: CHECK AUTONOMOUS DELIVERABLE TRIGGER")
        
        logger.info("⏳ Waiting for autonomous deliverable generation...")
        logger.info("   The system should trigger deliverable creation after 2+ tasks complete")
        
        max_wait = 90  # 90 seconds
        check_interval = 10
        
        for i in range(max_wait // check_interval):
            await asyncio.sleep(check_interval)
            
            # Check for deliverables
            deliverables_response = requests.get(f"{API_BASE}/deliverables/workspace/{self.workspace_id}")
            
            if deliverables_response.status_code == 200:
                deliverables = deliverables_response.json()
                
                if deliverables and len(deliverables) > 0:
                    self.results["deliverables_generated"] = len(deliverables)
                    self.results["trigger_activated"] = True
                    
                    logger.info(f"🎉 AUTONOMOUS TRIGGER SUCCESS!")
                    logger.info(f"✅ Found {len(deliverables)} deliverables generated autonomously")
                    
                    for d in deliverables:
                        logger.info(f"  📋 {d.get('title', 'Unknown')} - {d.get('type', 'Unknown')}")
                    
                    return
            
            logger.info(f"⏱️ Waiting for autonomous trigger... {(i+1)*check_interval}s elapsed")
        
        logger.warning("⚠️ No deliverables generated within timeout")
        logger.info("   This may indicate the trigger is not working properly")

async def main():
    test = AutonomousDeliverableTriggerTest()
    await test.run_test()

if __name__ == "__main__":
    asyncio.run(main())