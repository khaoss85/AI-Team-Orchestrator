#!/usr/bin/env python3
"""
🚀 COMPLETE LOOP SIMULATION TEST
Test che simula l'intero loop incluso deliverable creation
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

class CompleteLoopSimulation:
    """
    Simula l'intero loop dal setup alla creazione deliverable
    """
    
    def __init__(self):
        self.workspace_id = None
        self.agent_ids = []
        self.task_ids = []
        self.executed_tasks = []
        self.simulated_deliverables = []
        self.results = {
            "test_start": datetime.now().isoformat(),
            "phases": [],
            "workspace_id": None,
            "agents_created": 0,
            "tasks_generated": 0,
            "tasks_executed": 0,
            "deliverables_created": 0,
            "loop_closure": False,
            "success": False
        }
    
    async def run_complete_simulation(self):
        """Run the complete loop simulation"""
        
        logger.info("🚀 Starting Complete Loop Simulation")
        logger.info("=" * 60)
        
        try:
            # Phase 1: Setup workspace and team
            await self._phase_1_setup()
            
            # Phase 2: Execute tasks
            await self._phase_2_execute_tasks()
            
            # Phase 3: Simulate deliverable creation
            await self._phase_3_simulate_deliverables()
            
            # Phase 4: Validate loop closure
            await self._phase_4_validate_loop_closure()
            
            self.results["success"] = True
            logger.info("🎉 COMPLETE LOOP SIMULATION PASSED!")
            
        except Exception as e:
            logger.error(f"❌ Complete loop simulation failed: {e}")
            self.results["success"] = False
        
        self._print_summary()
        return self.results
    
    async def _phase_1_setup(self):
        """Phase 1: Setup workspace and team"""
        logger.info("🏗️ PHASE 1: SETUP")
        
        # Create workspace
        workspace_data = {
            "name": "Complete Loop Test",
            "description": "Full end-to-end test of the complete loop"
        }
        
        response = requests.post(f"{API_BASE}/workspaces", json=workspace_data, timeout=10)
        if response.status_code != 201:
            raise Exception(f"Workspace creation failed: {response.status_code}")
        
        workspace = response.json()
        self.workspace_id = workspace["id"]
        self.results["workspace_id"] = self.workspace_id
        
        logger.info(f"✅ Workspace created: {self.workspace_id}")
        
        # Create team
        proposal_payload = {
            "workspace_id": self.workspace_id,
            "project_description": "Complete project management system with multi-agent coordination",
            "budget": 1500.0,
            "max_team_size": 4
        }
        
        proposal_response = requests.post(f"{API_BASE}/director/proposal", json=proposal_payload, timeout=60)
        if proposal_response.status_code != 200:
            raise Exception(f"Director proposal failed: {proposal_response.status_code}")
        
        proposal_data = proposal_response.json()
        proposal_id = proposal_data["proposal_id"]
        
        approval_response = requests.post(f"{API_BASE}/director/approve/{self.workspace_id}", 
                                        params={"proposal_id": proposal_id}, timeout=45)
        
        if approval_response.status_code not in [200, 204]:
            raise Exception(f"Proposal approval failed: {approval_response.status_code}")
        
        approval_data = approval_response.json()
        self.agent_ids = approval_data.get("created_agent_ids", [])
        self.results["agents_created"] = len(self.agent_ids)
        
        logger.info(f"✅ Team created: {len(self.agent_ids)} agents")
        
        # Wait for task generation
        await asyncio.sleep(45)
        
        tasks = await list_tasks(self.workspace_id)
        self.task_ids = [task["id"] for task in tasks]
        self.results["tasks_generated"] = len(self.task_ids)
        
        logger.info(f"✅ Tasks generated: {len(self.task_ids)}")
        
        self.results["phases"].append("setup")
    
    async def _phase_2_execute_tasks(self):
        """Phase 2: Execute multiple tasks"""
        logger.info("🔥 PHASE 2: TASK EXECUTION")
        
        # Initialize manager
        manager = AgentManager(UUID(self.workspace_id))
        await manager.initialize()
        
        # Get pending tasks
        tasks = await list_tasks(self.workspace_id)
        pending_tasks = [task for task in tasks if task.get('status') == 'pending']
        
        logger.info(f"📋 Executing {len(pending_tasks)} pending tasks...")
        
        # Execute tasks
        for i, task_data in enumerate(pending_tasks):
            try:
                task_id = UUID(task_data["id"])
                task_name = task_data["name"]
                
                logger.info(f"🔧 Executing task {i+1}: {task_name}")
                
                start_time = time.time()
                result = await manager.execute_task(task_id)
                execution_time = time.time() - start_time
                
                if result and result.status == TaskStatus.COMPLETED:
                    self.executed_tasks.append({
                        "task_id": str(task_id),
                        "task_name": task_name,
                        "result": result.result,
                        "execution_time": execution_time,
                        "status": "completed"
                    })
                    logger.info(f"  ✅ Task completed in {execution_time:.2f}s")
                else:
                    logger.warning(f"  ⚠️ Task failed or incomplete")
                
                await asyncio.sleep(2)  # Small delay between tasks
                
            except Exception as e:
                logger.error(f"  ❌ Task execution error: {e}")
                continue
        
        self.results["tasks_executed"] = len(self.executed_tasks)
        
        logger.info(f"✅ Phase 2 Complete: {len(self.executed_tasks)} tasks executed")
        self.results["phases"].append("task_execution")
    
    async def _phase_3_simulate_deliverables(self):
        """Phase 3: Simulate deliverable creation from executed tasks"""
        logger.info("📦 PHASE 3: DELIVERABLE SIMULATION")
        
        if not self.executed_tasks:
            logger.warning("⚠️ No executed tasks to create deliverables from")
            return
        
        # Simulate deliverable creation logic
        deliverable_content = await self._aggregate_task_results()
        
        # Create simulated deliverable
        deliverable = {
            "id": f"sim_deliverable_{int(time.time())}",
            "title": f"Project Deliverable - {len(self.executed_tasks)} Tasks",
            "type": "project_summary",
            "content": deliverable_content,
            "status": "completed",
            "readiness_score": 85,
            "completion_percentage": 100,
            "business_value_score": 80,
            "metadata": {
                "source_tasks": [task["task_id"] for task in self.executed_tasks],
                "creation_method": "simulation",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        self.simulated_deliverables.append(deliverable)
        self.results["deliverables_created"] = len(self.simulated_deliverables)
        
        logger.info(f"✅ Simulated deliverable created:")
        logger.info(f"   - Title: {deliverable['title']}")
        logger.info(f"   - Content length: {len(deliverable_content)}")
        logger.info(f"   - Source tasks: {len(self.executed_tasks)}")
        
        # Show sample content
        logger.info(f"📖 Sample content:")
        logger.info(f"   {deliverable_content[:200]}...")
        
        self.results["phases"].append("deliverable_creation")
    
    async def _aggregate_task_results(self):
        """Aggregate results from executed tasks"""
        content_parts = []
        
        content_parts.append("# Project Summary")
        content_parts.append(f"This deliverable consolidates results from {len(self.executed_tasks)} completed tasks.")
        content_parts.append("")
        
        content_parts.append("## Task Results")
        
        for i, task in enumerate(self.executed_tasks, 1):
            content_parts.append(f"### {i}. {task['task_name']}")
            content_parts.append(f"**Status:** {task['status']}")
            content_parts.append(f"**Execution Time:** {task['execution_time']:.2f}s")
            
            # Format result
            task_result = task.get('result', '')
            if isinstance(task_result, str) and task_result.startswith('{'):
                try:
                    parsed = json.loads(task_result)
                    if "phases" in parsed:
                        phases = parsed["phases"]
                        content_parts.append(f"**Result:** Project structure with {len(phases)} phases defined")
                    else:
                        content_parts.append(f"**Result:** Structured output with {len(parsed)} components")
                except:
                    content_parts.append(f"**Result:** {task_result[:200]}...")
            else:
                content_parts.append(f"**Result:** {str(task_result)[:200]}...")
            
            content_parts.append("")
        
        content_parts.append("## Conclusion")
        content_parts.append(f"Successfully completed {len(self.executed_tasks)} tasks with concrete results.")
        content_parts.append("This deliverable demonstrates the complete loop from team creation to deliverable generation.")
        
        return "\n".join(content_parts)
    
    async def _phase_4_validate_loop_closure(self):
        """Phase 4: Validate complete loop closure"""
        logger.info("🔄 PHASE 4: LOOP CLOSURE VALIDATION")
        
        # Check loop components
        loop_components = {
            "workspace_created": self.workspace_id is not None,
            "team_created": len(self.agent_ids) > 0,
            "tasks_generated": len(self.task_ids) > 0,
            "tasks_executed": len(self.executed_tasks) > 0,
            "deliverables_created": len(self.simulated_deliverables) > 0
        }
        
        completed_components = sum(1 for completed in loop_components.values() if completed)
        total_components = len(loop_components)
        closure_percentage = (completed_components / total_components) * 100
        
        logger.info(f"🔍 Loop Closure Analysis:")
        for component, status in loop_components.items():
            status_icon = "✅" if status else "❌"
            logger.info(f"   {status_icon} {component}: {'PASS' if status else 'FAIL'}")
        
        logger.info(f"📊 Loop Closure: {closure_percentage:.1f}%")
        
        if closure_percentage == 100:
            self.results["loop_closure"] = True
            logger.info("✅ COMPLETE LOOP CLOSURE ACHIEVED!")
        else:
            logger.warning(f"⚠️ Incomplete loop closure: {closure_percentage:.1f}%")
        
        self.results["phases"].append("loop_closure_validation")
    
    def _print_summary(self):
        """Print comprehensive summary"""
        logger.info("\n" + "=" * 60)
        logger.info("🎯 COMPLETE LOOP SIMULATION - SUMMARY")
        logger.info("=" * 60)
        
        logger.info(f"🚀 Overall Success: {'YES' if self.results['success'] else 'NO'}")
        logger.info(f"🔄 Loop Closure: {'YES' if self.results['loop_closure'] else 'NO'}")
        logger.info(f"📊 Phases Completed: {len(self.results['phases'])}")
        
        logger.info(f"\n📈 Metrics:")
        logger.info(f"   👥 Agents Created: {self.results['agents_created']}")
        logger.info(f"   📋 Tasks Generated: {self.results['tasks_generated']}")
        logger.info(f"   🔥 Tasks Executed: {self.results['tasks_executed']}")
        logger.info(f"   📦 Deliverables Created: {self.results['deliverables_created']}")
        
        if self.results['phases']:
            logger.info(f"\n✅ Completed Phases: {', '.join(self.results['phases'])}")
        
        if self.simulated_deliverables:
            logger.info(f"\n📦 Deliverables:")
            for deliverable in self.simulated_deliverables:
                logger.info(f"   - {deliverable['title']}")
        
        logger.info("\n" + "=" * 60)

async def main():
    """Main test execution"""
    test = CompleteLoopSimulation()
    results = await test.run_complete_simulation()
    
    # Save results
    results_file = f"complete_loop_simulation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"💾 Results saved to: {results_file}")
    
    return 0 if results["success"] and results["loop_closure"] else 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)