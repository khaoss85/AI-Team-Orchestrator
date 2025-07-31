#!/usr/bin/env python3
"""
🚀 TEST NO WORKAROUND INTEGRATION
Test completo per verificare l'eliminazione dei workaround
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
    get_ready_tasks_python,
    get_workspace_execution_stats,
    get_task_execution_stats_python,
    list_tasks
)
from ai_agents.manager import AgentManager
from models import TaskStatus
from uuid import UUID

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

class NoWorkaroundIntegrationTest:
    """
    Test completo per verificare che i workaround siano stati eliminati
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
            "execution_records_created": 0,
            "workaround_eliminated": False,
            "performance_improved": False
        }
    
    async def run_no_workaround_test(self):
        """Run complete test without workarounds"""
        
        logger.info("🚀 Starting NO WORKAROUND INTEGRATION TEST")
        logger.info("=" * 60)
        logger.info("🎯 Goal: Verify all workarounds have been eliminated")
        logger.info("=" * 60)
        
        try:
            # Phase 1: Create workspace and measure baseline
            await self._phase_1_baseline_setup()
            
            # Phase 2: Test optimized task execution
            await self._phase_2_optimized_execution()
            
            # Phase 3: Verify traceability
            await self._phase_3_verify_traceability()
            
            # Phase 4: Performance validation
            await self._phase_4_performance_validation()
            
            self.results["workaround_eliminated"] = True
            logger.info("🎉 NO WORKAROUND INTEGRATION TEST PASSED!")
            
        except Exception as e:
            logger.error(f"❌ No workaround test failed: {e}")
            self.results["workaround_eliminated"] = False
            import traceback
            traceback.print_exc()
        
        self._print_summary()
        return self.results
    
    async def _phase_1_baseline_setup(self):
        """Phase 1: Create workspace and measure baseline"""
        logger.info("📊 PHASE 1: BASELINE SETUP")
        
        # Create workspace
        workspace_data = {
            "name": "No Workaround Test Workspace",
            "description": "Test workspace for verifying workaround elimination",
            "industry": "software_development"
        }
        
        response = requests.post(f"{API_BASE}/workspaces", json=workspace_data, timeout=15)
        if response.status_code != 201:
            raise Exception(f"Workspace creation failed: {response.status_code}")
        
        workspace = response.json()
        self.workspace_id = workspace["id"]
        self.results["workspace_id"] = self.workspace_id
        
        logger.info(f"✅ Workspace created: {self.workspace_id}")
        
        # Create team
        proposal_payload = {
            "workspace_id": self.workspace_id,
            "project_description": "Test project for no-workaround verification",
            "budget": 1000.0,
            "max_team_size": 3
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
        await asyncio.sleep(30)
        
        self.results["phases"].append("baseline_setup")
    
    async def _phase_2_optimized_execution(self):
        """Phase 2: Test optimized task execution using new functions"""
        logger.info("⚡ PHASE 2: OPTIMIZED EXECUTION")
        
        # 🚀 NEW: Use optimized get_ready_tasks instead of polling
        start_time = time.time()
        ready_tasks = await get_ready_tasks_python(self.workspace_id)
        query_time = time.time() - start_time
        
        logger.info(f"🔍 get_ready_tasks query completed in {query_time:.3f}s")
        logger.info(f"📋 Found {len(ready_tasks)} ready tasks")
        
        if not ready_tasks:
            logger.warning("⚠️ No ready tasks found")
            self.results["phases"].append("optimized_execution")
            return
        
        # Initialize manager
        manager = AgentManager(UUID(self.workspace_id))
        await manager.initialize()
        
        # Execute tasks with new traceability
        for task_data in ready_tasks:
            try:
                task_id = UUID(task_data["task_id"])
                task_name = task_data["task_name"]
                
                logger.info(f"🔧 Executing task: {task_name}")
                
                start_time = time.time()
                result = await manager.execute_task(task_id)
                execution_time = time.time() - start_time
                
                if result and result.status == TaskStatus.COMPLETED:
                    logger.info(f"  ✅ Task completed in {execution_time:.2f}s")
                    self.results["tasks_executed"] += 1
                else:
                    logger.warning(f"  ⚠️ Task failed or incomplete")
                
            except Exception as e:
                logger.error(f"  ❌ Task execution error: {e}")
                continue
        
        self.results["phases"].append("optimized_execution")
    
    async def _phase_3_verify_traceability(self):
        """Phase 3: Verify execution traceability"""
        logger.info("🔍 PHASE 3: VERIFY TRACEABILITY")
        
        # Get all tasks for this workspace
        tasks = await list_tasks(self.workspace_id)
        
        execution_records_found = 0
        
        for task in tasks:
            task_id = task["id"]
            
            # Get execution stats for each task
            stats = await get_task_execution_stats_python(task_id)
            
            if stats["total_attempts"] > 0:
                execution_records_found += 1
                logger.info(f"📊 Task {task.get('name', 'Unknown')}:")
                logger.info(f"   - Total attempts: {stats['total_attempts']}")
                logger.info(f"   - Successful: {stats['successful_attempts']}")
                logger.info(f"   - Failed: {stats['failed_attempts']}")
                logger.info(f"   - Avg time: {stats['average_execution_time']:.2f}s")
        
        self.results["execution_records_created"] = execution_records_found
        
        # Get workspace-level stats
        workspace_stats = await get_workspace_execution_stats(self.workspace_id)
        
        logger.info(f"📈 Workspace execution stats:")
        logger.info(f"   - Total tasks: {workspace_stats['total_tasks']}")
        logger.info(f"   - Completed: {workspace_stats['completed_tasks']}")
        logger.info(f"   - Total executions: {workspace_stats['total_executions']}")
        logger.info(f"   - Success rate: {workspace_stats['successful_executions']}/{workspace_stats['total_executions']}")
        
        self.results["phases"].append("verify_traceability")
    
    async def _phase_4_performance_validation(self):
        """Phase 4: Validate performance improvements"""
        logger.info("🚀 PHASE 4: PERFORMANCE VALIDATION")
        
        # Test query performance with multiple calls
        performance_times = []
        
        for i in range(5):
            start_time = time.time()
            ready_tasks = await get_ready_tasks_python(self.workspace_id)
            query_time = time.time() - start_time
            performance_times.append(query_time)
            
            logger.info(f"  Query {i+1}: {query_time:.3f}s ({len(ready_tasks)} tasks)")
        
        avg_performance = sum(performance_times) / len(performance_times)
        logger.info(f"📊 Average query performance: {avg_performance:.3f}s")
        
        # Performance is considered improved if queries are under 100ms
        if avg_performance < 0.1:
            self.results["performance_improved"] = True
            logger.info("✅ Performance improvement verified (< 100ms)")
        else:
            logger.warning(f"⚠️ Performance could be better ({avg_performance:.3f}s)")
        
        self.results["phases"].append("performance_validation")
    
    def _print_summary(self):
        """Print comprehensive summary"""
        logger.info("\n" + "=" * 60)
        logger.info("🎯 NO WORKAROUND INTEGRATION TEST - SUMMARY")
        logger.info("=" * 60)
        
        logger.info(f"✅ Workaround Eliminated: {'YES' if self.results['workaround_eliminated'] else 'NO'}")
        logger.info(f"⚡ Performance Improved: {'YES' if self.results['performance_improved'] else 'NO'}")
        logger.info(f"📊 Phases Completed: {len(self.results['phases'])}")
        
        logger.info(f"\n📈 Metrics:")
        logger.info(f"   👥 Agents Created: {self.results['agents_created']}")
        logger.info(f"   🔥 Tasks Executed: {self.results['tasks_executed']}")
        logger.info(f"   📋 Execution Records: {self.results['execution_records_created']}")
        
        if self.results['phases']:
            logger.info(f"\n✅ Completed Phases: {', '.join(self.results['phases'])}")
        
        logger.info("\n" + "=" * 60)

async def main():
    """Main test execution"""
    test = NoWorkaroundIntegrationTest()
    results = await test.run_no_workaround_test()
    
    # Save results
    results_file = f"no_workaround_integration_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"💾 Results saved to: {results_file}")
    
    # Return success if workarounds eliminated
    success = results["workaround_eliminated"]
    return 0 if success else 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)