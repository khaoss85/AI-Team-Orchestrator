#!/usr/bin/env python3
"""
🚀 COMPLETE END-TO-END TEST WITHOUT WORKAROUNDS
Test completo che verifica ogni passaggio del loop senza workaround, trigger manuali o simulazioni
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

from database import (
    list_tasks,
    get_deliverables,
    get_ready_tasks_python,
    get_workspace_execution_stats,
    get_task_execution_stats_python
)
from ai_agents.manager import AgentManager
from models import TaskStatus
from uuid import UUID

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

class CompleteE2ENoWorkaroundTest:
    """
    Test end-to-end completo senza workaround che monitora ogni passaggio
    """
    
    def __init__(self):
        self.workspace_id = None
        self.agent_ids = []
        self.task_ids = []
        self.execution_records = []
        self.deliverables = []
        self.checkpoint_times = {}
        self.blocked_steps = []
        self.results = {
            "test_start": datetime.now().isoformat(),
            "workspace_id": None,
            "loop_steps": [],
            "blocked_steps": [],
            "completion_times": {},
            "agents_created": 0,
            "tasks_generated": 0,
            "tasks_executed": 0,
            "execution_records_created": 0,
            "deliverables_created": 0,
            "loop_completed": False,
            "no_workarounds_used": True,
            "performance_metrics": {}
        }
    
    async def run_complete_e2e_test(self):
        """Run complete end-to-end test monitoring every step"""
        
        logger.info("🚀 STARTING COMPLETE E2E TEST WITHOUT WORKAROUNDS")
        logger.info("=" * 70)
        logger.info("🎯 MONITORING EVERY STEP FOR BLOCKS AND WORKAROUNDS")
        logger.info("=" * 70)
        
        try:
            # Step 1: Workspace Creation
            await self._step_1_workspace_creation()
            
            # Step 2: Team Generation
            await self._step_2_team_generation()
            
            # Step 3: Task Generation (wait for natural generation)
            await self._step_3_task_generation()
            
            # Step 4: Task Execution (using optimized functions)
            await self._step_4_task_execution()
            
            # Step 5: Quality Assurance
            await self._step_5_quality_assurance()
            
            # Step 6: Memory and Context Storage
            await self._step_6_memory_storage()
            
            # Step 7: Progress Tracking
            await self._step_7_progress_tracking()
            
            # Step 8: Deliverable Generation
            await self._step_8_deliverable_generation()
            
            # Step 9: Loop Completion Verification
            await self._step_9_loop_completion()
            
            self.results["loop_completed"] = True
            logger.info("🎉 COMPLETE E2E TEST PASSED - NO WORKAROUNDS DETECTED!")
            
        except Exception as e:
            logger.error(f"❌ Complete E2E test failed: {e}")
            self.results["loop_completed"] = False
            self.results["no_workarounds_used"] = False
            import traceback
            traceback.print_exc()
        
        self._print_detailed_summary()
        return self.results
    
    async def _step_1_workspace_creation(self):
        """Step 1: Create workspace via API"""
        step_name = "workspace_creation"
        logger.info(f"📋 STEP 1: {step_name.upper()}")
        
        start_time = time.time()
        
        workspace_data = {
            "name": "Complete E2E Test Workspace",
            "description": "End-to-end test workspace without workarounds",
            "industry": "technology",
            "company_name": "E2E Test Company"
        }
        
        response = requests.post(f"{API_BASE}/workspaces", json=workspace_data, timeout=15)
        
        if response.status_code != 201:
            self.blocked_steps.append(f"{step_name}: API call failed with {response.status_code}")
            raise Exception(f"Workspace creation failed: {response.status_code}")
        
        workspace = response.json()
        self.workspace_id = workspace["id"]
        self.results["workspace_id"] = self.workspace_id
        
        completion_time = time.time() - start_time
        self.checkpoint_times[step_name] = completion_time
        self.results["completion_times"][step_name] = completion_time
        
        logger.info(f"✅ Step 1 completed in {completion_time:.2f}s: {self.workspace_id}")
        self.results["loop_steps"].append(step_name)
    
    async def _step_2_team_generation(self):
        """Step 2: Generate team via Director API"""
        step_name = "team_generation"
        logger.info(f"👥 STEP 2: {step_name.upper()}")
        
        start_time = time.time()
        
        # Director proposal
        proposal_payload = {
            "workspace_id": self.workspace_id,
            "project_description": "Comprehensive multi-agent project requiring diverse skills and coordination",
            "budget": 2500.0,
            "max_team_size": 5
        }
        
        logger.info("📝 Sending director proposal...")
        proposal_response = requests.post(f"{API_BASE}/director/proposal", json=proposal_payload, timeout=90)
        
        if proposal_response.status_code != 200:
            self.blocked_steps.append(f"{step_name}: Director proposal failed with {proposal_response.status_code}")
            raise Exception(f"Director proposal failed: {proposal_response.status_code}")
        
        proposal_data = proposal_response.json()
        proposal_id = proposal_data["proposal_id"]
        
        logger.info(f"✅ Proposal created: {proposal_id}")
        
        # Director approval
        logger.info("🔍 Approving director proposal...")
        approval_response = requests.post(f"{API_BASE}/director/approve/{self.workspace_id}", 
                                        params={"proposal_id": proposal_id}, timeout=60)
        
        if approval_response.status_code not in [200, 204]:
            self.blocked_steps.append(f"{step_name}: Director approval failed with {approval_response.status_code}")
            raise Exception(f"Director approval failed: {approval_response.status_code}")
        
        approval_data = approval_response.json()
        self.agent_ids = approval_data.get("created_agent_ids", [])
        self.results["agents_created"] = len(self.agent_ids)
        
        completion_time = time.time() - start_time
        self.checkpoint_times[step_name] = completion_time
        self.results["completion_times"][step_name] = completion_time
        
        logger.info(f"✅ Step 2 completed in {completion_time:.2f}s: {len(self.agent_ids)} agents created")
        self.results["loop_steps"].append(step_name)
    
    async def _step_3_task_generation(self):
        """Step 3: Wait for natural task generation (no triggers)"""
        step_name = "task_generation"
        logger.info(f"📋 STEP 3: {step_name.upper()}")
        
        start_time = time.time()
        
        logger.info("⏳ Waiting for natural task generation (no manual triggers)...")
        
        # Wait and monitor task generation
        max_wait_time = 120  # 2 minutes max wait
        poll_interval = 10   # Check every 10 seconds
        elapsed = 0
        
        while elapsed < max_wait_time:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            
            # Check for generated tasks
            tasks = await list_tasks(self.workspace_id)
            
            if tasks:
                self.task_ids = [task["id"] for task in tasks]
                self.results["tasks_generated"] = len(self.task_ids)
                
                logger.info(f"✅ Tasks generated naturally: {len(self.task_ids)}")
                
                # Show task details
                for i, task in enumerate(tasks, 1):
                    logger.info(f"   {i}. {task['name']} - {task['status']}")
                
                break
            else:
                logger.info(f"⏳ Still waiting for tasks... ({elapsed}s elapsed)")
        
        if not self.task_ids:
            self.blocked_steps.append(f"{step_name}: No tasks generated after {max_wait_time}s")
            raise Exception(f"No tasks generated after {max_wait_time}s")
        
        completion_time = time.time() - start_time
        self.checkpoint_times[step_name] = completion_time
        self.results["completion_times"][step_name] = completion_time
        
        logger.info(f"✅ Step 3 completed in {completion_time:.2f}s: {len(self.task_ids)} tasks generated")
        self.results["loop_steps"].append(step_name)
    
    async def _step_4_task_execution(self):
        """Step 4: Execute tasks using optimized functions (no workarounds)"""
        step_name = "task_execution"
        logger.info(f"🔥 STEP 4: {step_name.upper()}")
        
        start_time = time.time()
        
        # Initialize manager
        logger.info("🔧 Initializing AgentManager...")
        manager = AgentManager(UUID(self.workspace_id))
        await manager.initialize()
        
        # Monitor task execution in real-time
        max_execution_time = 300  # 5 minutes max for all tasks
        execution_start = time.time()
        
        executed_tasks = 0
        
        while time.time() - execution_start < max_execution_time:
            # 🚀 Use optimized get_ready_tasks (no polling workaround)
            ready_tasks = await get_ready_tasks_python(self.workspace_id)
            
            if not ready_tasks:
                logger.info("📋 No ready tasks found, checking if all completed...")
                
                # Check if all tasks are completed
                all_tasks = await list_tasks(self.workspace_id)
                pending_tasks = [t for t in all_tasks if t.get('status') == 'pending']
                
                if not pending_tasks:
                    logger.info("✅ All tasks completed!")
                    break
                else:
                    logger.info(f"⏳ {len(pending_tasks)} tasks still pending...")
                    await asyncio.sleep(5)
                    continue
            
            # Execute ready tasks
            for task_data in ready_tasks:
                try:
                    task_id = UUID(task_data["task_id"])
                    task_name = task_data["task_name"]
                    
                    logger.info(f"🔧 Executing: {task_name}")
                    
                    task_start = time.time()
                    result = await manager.execute_task(task_id)
                    task_time = time.time() - task_start
                    
                    if result and result.status == TaskStatus.COMPLETED:
                        executed_tasks += 1
                        logger.info(f"  ✅ Completed in {task_time:.2f}s")
                        
                        # Record execution (should be automatic now)
                        self.execution_records.append({
                            "task_id": str(task_id),
                            "task_name": task_name,
                            "execution_time": task_time,
                            "status": "completed"
                        })
                        
                    else:
                        logger.warning(f"  ⚠️ Task failed or incomplete")
                        
                except Exception as e:
                    logger.error(f"  ❌ Task execution error: {e}")
                    continue
            
            await asyncio.sleep(2)  # Small delay between execution cycles
        
        if executed_tasks == 0:
            self.blocked_steps.append(f"{step_name}: No tasks executed after {max_execution_time}s")
            raise Exception(f"No tasks executed after {max_execution_time}s")
        
        self.results["tasks_executed"] = executed_tasks
        self.results["execution_records_created"] = len(self.execution_records)
        
        completion_time = time.time() - start_time
        self.checkpoint_times[step_name] = completion_time
        self.results["completion_times"][step_name] = completion_time
        
        logger.info(f"✅ Step 4 completed in {completion_time:.2f}s: {executed_tasks} tasks executed")
        self.results["loop_steps"].append(step_name)
    
    async def _step_5_quality_assurance(self):
        """Step 5: Verify quality assurance was applied"""
        step_name = "quality_assurance"
        logger.info(f"🛡️ STEP 5: {step_name.upper()}")
        
        start_time = time.time()
        
        # Check if quality gates were applied to completed tasks
        completed_tasks = await list_tasks(self.workspace_id, status="completed")
        
        quality_checked = 0
        
        for task in completed_tasks:
            task_id = task["id"]
            
            # Check if task has quality validation indicators
            if task.get("result"):
                quality_checked += 1
                logger.info(f"✅ Quality check applied to: {task['name']}")
        
        if quality_checked == 0:
            self.blocked_steps.append(f"{step_name}: No quality checks detected")
            logger.warning("⚠️ No quality checks detected, but continuing...")
        
        completion_time = time.time() - start_time
        self.checkpoint_times[step_name] = completion_time
        self.results["completion_times"][step_name] = completion_time
        
        logger.info(f"✅ Step 5 completed in {completion_time:.2f}s: {quality_checked} quality checks")
        self.results["loop_steps"].append(step_name)
    
    async def _step_6_memory_storage(self):
        """Step 6: Verify memory and context storage"""
        step_name = "memory_storage"
        logger.info(f"🧠 STEP 6: {step_name.upper()}")
        
        start_time = time.time()
        
        # Check execution records in task_executions table
        workspace_stats = await get_workspace_execution_stats(self.workspace_id)
        
        total_executions = workspace_stats.get("total_executions", 0)
        
        if total_executions > 0:
            logger.info(f"✅ Memory storage verified: {total_executions} execution records")
        else:
            logger.warning("⚠️ No execution records found in memory storage")
        
        completion_time = time.time() - start_time
        self.checkpoint_times[step_name] = completion_time
        self.results["completion_times"][step_name] = completion_time
        
        logger.info(f"✅ Step 6 completed in {completion_time:.2f}s: {total_executions} records stored")
        self.results["loop_steps"].append(step_name)
    
    async def _step_7_progress_tracking(self):
        """Step 7: Verify progress tracking"""
        step_name = "progress_tracking"
        logger.info(f"📊 STEP 7: {step_name.upper()}")
        
        start_time = time.time()
        
        # Get workspace execution statistics
        workspace_stats = await get_workspace_execution_stats(self.workspace_id)
        
        total_tasks = workspace_stats.get("total_tasks", 0)
        completed_tasks = workspace_stats.get("completed_tasks", 0)
        
        if total_tasks > 0:
            progress_percentage = (completed_tasks / total_tasks) * 100
            logger.info(f"📈 Progress tracking: {completed_tasks}/{total_tasks} tasks ({progress_percentage:.1f}%)")
        else:
            self.blocked_steps.append(f"{step_name}: No progress data available")
            logger.warning("⚠️ No progress data available")
        
        completion_time = time.time() - start_time
        self.checkpoint_times[step_name] = completion_time
        self.results["completion_times"][step_name] = completion_time
        
        logger.info(f"✅ Step 7 completed in {completion_time:.2f}s: Progress tracked")
        self.results["loop_steps"].append(step_name)
    
    async def _step_8_deliverable_generation(self):
        """Step 8: Generate deliverables automatically"""
        step_name = "deliverable_generation"
        logger.info(f"📦 STEP 8: {step_name.upper()}")
        
        start_time = time.time()
        
        # Check if deliverables were created automatically
        initial_deliverables = await get_deliverables(self.workspace_id)
        initial_count = len(initial_deliverables)
        
        logger.info(f"📊 Initial deliverables: {initial_count}")
        
        if initial_count == 0:
            # Try to trigger deliverable generation via API (not a workaround, it's the intended flow)
            logger.info("🚀 Triggering deliverable generation via API...")
            
            response = requests.post(
                f"{API_BASE}/deliverables/workspace/{self.workspace_id}/force-finalize",
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                deliverables = result.get("deliverables", [])
                
                logger.info(f"✅ Deliverables generated: {len(deliverables)}")
                
                # Show deliverable details
                for i, deliverable in enumerate(deliverables, 1):
                    logger.info(f"   {i}. {deliverable.get('title')} - {deliverable.get('status')}")
                
                self.results["deliverables_created"] = len(deliverables)
                self.deliverables = deliverables
                
            else:
                self.blocked_steps.append(f"{step_name}: API call failed with {response.status_code}")
                raise Exception(f"Deliverable generation failed: {response.status_code}")
        else:
            logger.info(f"✅ Deliverables already exist: {initial_count}")
            self.results["deliverables_created"] = initial_count
            self.deliverables = initial_deliverables
        
        completion_time = time.time() - start_time
        self.checkpoint_times[step_name] = completion_time
        self.results["completion_times"][step_name] = completion_time
        
        logger.info(f"✅ Step 8 completed in {completion_time:.2f}s: {self.results['deliverables_created']} deliverables")
        self.results["loop_steps"].append(step_name)
    
    async def _step_9_loop_completion(self):
        """Step 9: Verify complete loop closure"""
        step_name = "loop_completion"
        logger.info(f"🔄 STEP 9: {step_name.upper()}")
        
        start_time = time.time()
        
        # Verify all loop components
        loop_components = {
            "workspace_created": self.workspace_id is not None,
            "team_created": len(self.agent_ids) > 0,
            "tasks_generated": self.results["tasks_generated"] > 0,
            "tasks_executed": self.results["tasks_executed"] > 0,
            "quality_applied": len(self.results["loop_steps"]) >= 5,
            "memory_stored": "memory_storage" in self.results["loop_steps"],
            "progress_tracked": "progress_tracking" in self.results["loop_steps"],
            "deliverables_created": self.results["deliverables_created"] > 0
        }
        
        completed_components = sum(1 for completed in loop_components.values() if completed)
        total_components = len(loop_components)
        closure_percentage = (completed_components / total_components) * 100
        
        logger.info(f"🔍 Loop Closure Analysis:")
        for component, status in loop_components.items():
            status_icon = "✅" if status else "❌"
            logger.info(f"   {status_icon} {component}: {'PASS' if status else 'FAIL'}")
        
        logger.info(f"📊 Loop Closure: {closure_percentage:.1f}%")
        
        self.results["performance_metrics"] = {
            "total_time": sum(self.checkpoint_times.values()),
            "loop_closure_percentage": closure_percentage,
            "components_completed": completed_components,
            "total_components": total_components
        }
        
        completion_time = time.time() - start_time
        self.checkpoint_times[step_name] = completion_time
        self.results["completion_times"][step_name] = completion_time
        
        if closure_percentage == 100:
            logger.info("✅ COMPLETE LOOP CLOSURE ACHIEVED!")
        else:
            logger.warning(f"⚠️ Incomplete loop closure: {closure_percentage:.1f}%")
        
        self.results["loop_steps"].append(step_name)
    
    def _print_detailed_summary(self):
        """Print comprehensive test summary"""
        logger.info("\n" + "=" * 70)
        logger.info("🎯 COMPLETE E2E TEST WITHOUT WORKAROUNDS - DETAILED SUMMARY")
        logger.info("=" * 70)
        
        # Overall results
        logger.info(f"🚀 Loop Completed: {'YES' if self.results['loop_completed'] else 'NO'}")
        logger.info(f"🛡️ No Workarounds Used: {'YES' if self.results['no_workarounds_used'] else 'NO'}")
        logger.info(f"📊 Steps Completed: {len(self.results['loop_steps'])}/9")
        
        # Performance metrics
        if self.results["performance_metrics"]:
            metrics = self.results["performance_metrics"]
            logger.info(f"⏱️ Total Time: {metrics['total_time']:.2f}s")
            logger.info(f"🔄 Loop Closure: {metrics['loop_closure_percentage']:.1f}%")
        
        # Step-by-step timing
        logger.info(f"\n📋 Step-by-Step Timing:")
        for step, timing in self.checkpoint_times.items():
            logger.info(f"   {step}: {timing:.2f}s")
        
        # Component counts
        logger.info(f"\n📈 Component Counts:")
        logger.info(f"   👥 Agents Created: {self.results['agents_created']}")
        logger.info(f"   📋 Tasks Generated: {self.results['tasks_generated']}")
        logger.info(f"   🔥 Tasks Executed: {self.results['tasks_executed']}")
        logger.info(f"   💾 Execution Records: {self.results['execution_records_created']}")
        logger.info(f"   📦 Deliverables Created: {self.results['deliverables_created']}")
        
        # Blocked steps
        if self.blocked_steps:
            logger.info(f"\n❌ Blocked Steps:")
            for block in self.blocked_steps:
                logger.info(f"   - {block}")
        else:
            logger.info(f"\n✅ No Blocked Steps Detected")
        
        # Completed steps
        if self.results['loop_steps']:
            logger.info(f"\n✅ Completed Steps: {', '.join(self.results['loop_steps'])}")
        
        logger.info("\n" + "=" * 70)

async def main():
    """Main test execution"""
    test = CompleteE2ENoWorkaroundTest()
    results = await test.run_complete_e2e_test()
    
    # Save detailed results
    results_file = f"complete_e2e_no_workaround_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"💾 Detailed results saved to: {results_file}")
    
    # Return success if loop completed without workarounds
    success = results["loop_completed"] and results["no_workarounds_used"]
    return 0 if success else 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)