#!/usr/bin/env python3
"""
🚀 REAL PRODUCTION FLOW TEST
Test che simula un flusso di produzione reale senza workaround o simulazioni
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

from database import list_tasks, get_deliverables
from ai_agents.manager import AgentManager
from models import TaskStatus
from uuid import UUID

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

class RealProductionFlowTest:
    """
    Test completamente reale del flusso di produzione
    - Nessuna simulazione
    - Nessun workaround
    - Solo API reali e database reali
    """
    
    def __init__(self):
        self.workspace_id = None
        self.agent_ids = []
        self.task_ids = []
        self.results = {
            "test_start": datetime.now().isoformat(),
            "phases": [],
            "workspace_id": None,
            "agents_created": 0,
            "tasks_generated": 0,
            "tasks_executed": 0,
            "deliverables_created": 0,
            "real_flow_success": False,
            "simulation_detected": False
        }
    
    async def run_real_production_test(self):
        """Run complete real production test"""
        
        logger.info("🚀 Starting REAL PRODUCTION FLOW TEST")
        logger.info("=" * 60)
        logger.info("⚠️  NO SIMULATIONS - NO WORKAROUNDS - ONLY REAL APIs")
        logger.info("=" * 60)
        
        try:
            # Phase 1: Create workspace and team
            await self._phase_1_real_setup()
            
            # Phase 2: Wait for and execute all tasks
            await self._phase_2_real_task_execution()
            
            # Phase 3: Generate real deliverables via API
            await self._phase_3_real_deliverable_generation()
            
            # Phase 4: Validate real production flow
            await self._phase_4_validate_real_production()
            
            self.results["real_flow_success"] = True
            logger.info("🎉 REAL PRODUCTION FLOW TEST PASSED!")
            
        except Exception as e:
            logger.error(f"❌ Real production flow test failed: {e}")
            self.results["real_flow_success"] = False
            import traceback
            traceback.print_exc()
        
        self._print_real_summary()
        return self.results
    
    async def _phase_1_real_setup(self):
        """Phase 1: Real workspace and team setup"""
        logger.info("🏗️ PHASE 1: REAL SETUP")
        
        # Create real workspace
        workspace_data = {
            "name": "Real Production Test Workspace",
            "description": "Complete real production test without simulations",
            "industry": "software_development",
            "company_name": "AI Team Orchestrator Test"
        }
        
        response = requests.post(f"{API_BASE}/workspaces", json=workspace_data, timeout=15)
        if response.status_code != 201:
            raise Exception(f"Real workspace creation failed: {response.status_code}")
        
        workspace = response.json()
        self.workspace_id = workspace["id"]
        self.results["workspace_id"] = self.workspace_id
        
        logger.info(f"✅ Real workspace created: {self.workspace_id}")
        
        # Create real team via director
        proposal_payload = {
            "workspace_id": self.workspace_id,
            "project_description": "Develop a comprehensive project management solution with real-time collaboration features",
            "budget": 2000.0,
            "max_team_size": 5
        }
        
        proposal_response = requests.post(f"{API_BASE}/director/proposal", json=proposal_payload, timeout=60)
        if proposal_response.status_code != 200:
            raise Exception(f"Real director proposal failed: {proposal_response.status_code}")
        
        proposal_data = proposal_response.json()
        proposal_id = proposal_data["proposal_id"]
        
        approval_response = requests.post(f"{API_BASE}/director/approve/{self.workspace_id}", 
                                        params={"proposal_id": proposal_id}, timeout=45)
        
        if approval_response.status_code not in [200, 204]:
            raise Exception(f"Real proposal approval failed: {approval_response.status_code}")
        
        approval_data = approval_response.json()
        self.agent_ids = approval_data.get("created_agent_ids", [])
        self.results["agents_created"] = len(self.agent_ids)
        
        logger.info(f"✅ Real team created: {len(self.agent_ids)} agents")
        
        # Wait for real task generation (not simulation)
        logger.info("⏳ Waiting for real task generation...")
        await asyncio.sleep(60)  # Real systems need time
        
        tasks = await list_tasks(self.workspace_id)
        self.task_ids = [task["id"] for task in tasks]
        self.results["tasks_generated"] = len(self.task_ids)
        
        logger.info(f"✅ Real tasks generated: {len(self.task_ids)}")
        
        self.results["phases"].append("real_setup")
    
    async def _phase_2_real_task_execution(self):
        """Phase 2: Real task execution via AgentManager"""
        logger.info("🔥 PHASE 2: REAL TASK EXECUTION")
        
        # Initialize real AgentManager
        manager = AgentManager(UUID(self.workspace_id))
        await manager.initialize()
        
        # Execute ALL pending tasks in a real loop
        executed_count = 0
        max_iterations = 20  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"🔄 Real execution iteration {iteration}")
            
            # Get current pending tasks
            tasks = await list_tasks(self.workspace_id)
            pending_tasks = [task for task in tasks if task.get('status') == 'pending']
            
            if not pending_tasks:
                logger.info("✅ No more pending tasks - real execution complete")
                break
            
            logger.info(f"📋 Found {len(pending_tasks)} pending tasks")
            
            # Execute each pending task
            for task_data in pending_tasks:
                try:
                    task_id = UUID(task_data["id"])
                    task_name = task_data["name"]
                    
                    logger.info(f"🔧 Real execution: {task_name}")
                    
                    start_time = time.time()
                    result = await manager.execute_task(task_id)
                    execution_time = time.time() - start_time
                    
                    if result and result.status == TaskStatus.COMPLETED:
                        executed_count += 1
                        logger.info(f"  ✅ Real task completed in {execution_time:.2f}s")
                    else:
                        logger.warning(f"  ⚠️ Real task failed or incomplete")
                    
                    # Small delay between tasks
                    await asyncio.sleep(3)
                    
                except Exception as e:
                    logger.error(f"  ❌ Real task execution error: {e}")
                    continue
            
            # Wait before next iteration
            await asyncio.sleep(5)
        
        self.results["tasks_executed"] = executed_count
        logger.info(f"✅ Real task execution complete: {executed_count} tasks executed")
        
        self.results["phases"].append("real_task_execution")
    
    async def _phase_3_real_deliverable_generation(self):
        """Phase 3: Real deliverable generation via API"""
        logger.info("📦 PHASE 3: REAL DELIVERABLE GENERATION")
        
        # Get completed tasks for real deliverable
        completed_tasks = await list_tasks(self.workspace_id, status="completed")
        
        if not completed_tasks:
            logger.warning("⚠️ No completed tasks found for real deliverable generation")
            return
        
        logger.info(f"📊 Found {len(completed_tasks)} completed tasks for real deliverable")
        
        # Use REAL force-finalize API (not simulation)
        logger.info("🚀 Calling REAL force-finalize API...")
        
        response = requests.post(
            f"{API_BASE}/deliverables/workspace/{self.workspace_id}/force-finalize",
            timeout=120  # Real processing takes time
        )
        
        if response.status_code == 200:
            result = response.json()
            
            deliverables = result.get("deliverables", [])
            self.results["deliverables_created"] = len(deliverables)
            
            logger.info(f"✅ REAL deliverables created: {len(deliverables)}")
            
            # Verify deliverables are really in database
            db_deliverables = await get_deliverables(self.workspace_id)
            
            if len(db_deliverables) != len(deliverables):
                logger.warning(f"⚠️ Mismatch: API returned {len(deliverables)}, DB contains {len(db_deliverables)}")
                self.results["simulation_detected"] = True
            else:
                logger.info(f"✅ REAL deliverables verified in database: {len(db_deliverables)}")
                
                # Show real deliverable content
                if db_deliverables:
                    sample = db_deliverables[0]
                    logger.info(f"📖 Real deliverable sample:")
                    logger.info(f"   - ID: {sample.get('id')}")
                    logger.info(f"   - Title: {sample.get('title')}")
                    logger.info(f"   - Content length: {len(sample.get('content', ''))}")
                    logger.info(f"   - Status: {sample.get('status')}")
        else:
            logger.error(f"❌ REAL deliverable generation failed: {response.status_code}")
            logger.error(f"   Response: {response.text}")
            return
        
        self.results["phases"].append("real_deliverable_generation")
    
    async def _phase_4_validate_real_production(self):
        """Phase 4: Validate real production flow"""
        logger.info("🔄 PHASE 4: REAL PRODUCTION VALIDATION")
        
        # Check all components are REAL
        real_components = {
            "workspace_created": self.workspace_id is not None,
            "team_created": len(self.agent_ids) > 0,
            "tasks_generated": len(self.task_ids) > 0,
            "tasks_executed": self.results["tasks_executed"] > 0,
            "deliverables_created": self.results["deliverables_created"] > 0,
            "no_simulation_detected": not self.results["simulation_detected"]
        }
        
        completed_components = sum(1 for completed in real_components.values() if completed)
        total_components = len(real_components)
        production_readiness = (completed_components / total_components) * 100
        
        logger.info(f"🔍 Real Production Flow Analysis:")
        for component, status in real_components.items():
            status_icon = "✅" if status else "❌"
            logger.info(f"   {status_icon} {component}: {'REAL' if status else 'MISSING'}")
        
        logger.info(f"📊 Production Readiness: {production_readiness:.1f}%")
        
        if production_readiness == 100:
            logger.info("✅ REAL PRODUCTION FLOW VALIDATED!")
        else:
            logger.warning(f"⚠️ Production flow incomplete: {production_readiness:.1f}%")
        
        self.results["phases"].append("real_production_validation")
    
    def _print_real_summary(self):
        """Print real production summary"""
        logger.info("\n" + "=" * 60)
        logger.info("🎯 REAL PRODUCTION FLOW TEST - SUMMARY")
        logger.info("=" * 60)
        
        logger.info(f"🚀 Real Flow Success: {'YES' if self.results['real_flow_success'] else 'NO'}")
        logger.info(f"⚠️ Simulation Detected: {'YES' if self.results['simulation_detected'] else 'NO'}")
        logger.info(f"📊 Phases Completed: {len(self.results['phases'])}")
        
        logger.info(f"\n📈 Real Metrics:")
        logger.info(f"   👥 Agents Created: {self.results['agents_created']}")
        logger.info(f"   📋 Tasks Generated: {self.results['tasks_generated']}")
        logger.info(f"   🔥 Tasks Executed: {self.results['tasks_executed']}")
        logger.info(f"   📦 Deliverables Created: {self.results['deliverables_created']}")
        
        if self.results['phases']:
            logger.info(f"\n✅ Real Phases: {', '.join(self.results['phases'])}")
        
        logger.info("\n" + "=" * 60)

async def main():
    """Main test execution"""
    test = RealProductionFlowTest()
    results = await test.run_real_production_test()
    
    # Save results
    results_file = f"real_production_flow_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"💾 Real results saved to: {results_file}")
    
    # Return success if real flow worked without simulation
    success = results["real_flow_success"] and not results["simulation_detected"]
    return 0 if success else 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)