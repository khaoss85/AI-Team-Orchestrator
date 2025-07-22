"""
🚀 CONTINUOUS AUTONOMOUS VIRTUOUS CYCLE TEST
Tests the full autonomous cycle with continuous monitoring of:
- Multiple task execution
- Agent handoffs
- Tool usage
- Asset creation
- Deliverable aggregation
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

import requests
from database import supabase, supabase_service, get_supabase_service_client
from ai_agents.manager import AgentManager
from models import TaskStatus

# Logging Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

API_BASE = "http://localhost:8000/api"

class ContinuousAutonomousTest:
    def __init__(self):
        self.workspace_id = None
        self.executed_tasks = []
        self.created_assets = []
        self.deliverables = []
        self.handoffs_observed = []
        self.tools_used = []
        self.results = {
            "test_start": datetime.now().isoformat(),
            "phases": {},
            "continuous_monitoring": {
                "tasks_executed": 0,
                "tasks_completed": 0,
                "tasks_failed": 0,
                "handoffs_count": 0,
                "tools_used_count": 0,
                "assets_created": 0,
                "deliverables_created": 0
            }
        }

    def _log_phase_result(self, phase_name: str, success: bool, details: Any):
        self.results["phases"][phase_name] = {
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        
    async def run_continuous_test(self):
        logger.info("🚀 Starting CONTINUOUS AUTONOMOUS VIRTUOUS CYCLE TEST")
        logger.info("=" * 80)
        
        try:
            # PHASE 1: Setup workspace and goals
            await self.phase_1_setup()
            
            # PHASE 2: Create team
            await self.phase_2_team_creation()
            
            # PHASE 3: Continuous task monitoring and execution
            await self.phase_3_continuous_execution()
            
            # Generate final report
            self._generate_final_report()
            
        except Exception as e:
            logger.error(f"❌ Test execution failed: {e}", exc_info=True)
            self.results["overall_success"] = False
        finally:
            # Always save results, even on error or timeout
            self.results["test_end"] = datetime.now().isoformat()
            results_file = f"continuous_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            logger.info(f"💾 Results saved to: {results_file}")

    async def phase_1_setup(self):
        logger.info("\n📋 PHASE 1: Workspace Setup and Goal Creation")
        
        # Create workspace
        workspace_data = {
            "name": "Continuous Autonomous Test",
            "description": "Test continuous execution with handoffs and tools"
        }
        response = requests.post(f"{API_BASE}/workspaces", json=workspace_data, timeout=10)
        response.raise_for_status()
        workspace = response.json()
        self.workspace_id = workspace["id"]
        logger.info(f"✅ Workspace created: {self.workspace_id}")
        
        # Create goals directly in database
        from database import supabase
        
        goals = [
            {
                "id": str(uuid.uuid4()),
                "workspace_id": self.workspace_id,
                "description": "Create a comprehensive Python string utility library with 10+ functions",
                "metric_type": "deliverable_utility_library",
                "target_value": 10,
                "current_value": 0,
                "status": "active",
                "priority": 1
            },
            {
                "id": str(uuid.uuid4()),
                "workspace_id": self.workspace_id,
                "description": "Implement unit tests with 90% coverage",
                "metric_type": "test_coverage",
                "target_value": 90,
                "current_value": 0,
                "status": "active",
                "priority": 2
            },
            {
                "id": str(uuid.uuid4()),
                "workspace_id": self.workspace_id,
                "description": "Create comprehensive documentation",
                "metric_type": "deliverable_documentation",
                "target_value": 1,
                "current_value": 0,
                "status": "active",
                "priority": 3
            }
        ]
        
        for goal in goals:
            result = supabase.table("workspace_goals").insert(goal).execute()
            if result.data:
                logger.info(f"✅ Goal created: {goal['description'][:50]}...")
        
        self._log_phase_result("setup", True, {"workspace_id": self.workspace_id, "goals_created": len(goals)})

    async def phase_2_team_creation(self):
        logger.info("\n👥 PHASE 2: Team Creation and Approval")
        
        proposal_payload = {
            "workspace_id": self.workspace_id,
            "project_description": "Develop a Python string utility library with tests and documentation",
            "budget": 100.0,
            "max_team_size": 4
        }
        
        proposal_response = requests.post(f"{API_BASE}/director/proposal", json=proposal_payload, timeout=60)
        proposal_response.raise_for_status()
        proposal_id = proposal_response.json()["proposal_id"]
        
        approval_response = requests.post(
            f"{API_BASE}/director/approve/{self.workspace_id}",
            params={"proposal_id": proposal_id},
            timeout=45
        )
        approval_response.raise_for_status()
        logger.info("✅ Team created and approved")
        
        self._log_phase_result("team_creation", True, {"proposal_id": proposal_id})

    async def phase_3_continuous_execution(self):
        logger.info("\n🔄 PHASE 3: Continuous Task Monitoring and Execution")
        
        # Initialize AgentManager
        manager = AgentManager(UUID(self.workspace_id))
        await manager.initialize()
        
        # Monitor for a maximum time
        max_monitoring_time = 600  # 10 minutes
        start_time = time.time()
        check_interval = 10
        
        while time.time() - start_time < max_monitoring_time:
            try:
                # Get all tasks in workspace
                tasks_response = requests.get(f"{API_BASE}/workspaces/{self.workspace_id}/tasks", timeout=10)
                if tasks_response.status_code == 200:
                    all_tasks = tasks_response.json()
                    
                    # Log task status distribution
                    status_counts = {}
                    for task in all_tasks:
                        status = task.get('status', 'unknown')
                        status_counts[status] = status_counts.get(status, 0) + 1
                    
                    logger.info(f"\n📊 Task Status Summary: {status_counts}")
                    logger.info(f"   Total tasks: {len(all_tasks)}")
                    
                    # Process pending tasks
                    pending_tasks = [t for t in all_tasks if t.get('status') == 'pending']
                    
                    for task in pending_tasks[:1]:  # Execute one task at a time
                        task_id = task.get('id')
                        task_name = task.get('name', 'Unknown')
                        
                        logger.info(f"\n🎯 Executing task: {task_name} ({task_id})")
                        
                        try:
                            # Execute task
                            result = await manager.execute_task(UUID(task_id))
                            
                            # Log execution details
                            self.executed_tasks.append({
                                "id": task_id,
                                "name": task_name,
                                "status": "completed",
                                "execution_time": getattr(result, 'execution_time', 0)
                            })
                            
                            self.results["continuous_monitoring"]["tasks_executed"] += 1
                            self.results["continuous_monitoring"]["tasks_completed"] += 1
                            
                            # Check for handoffs in result
                            await self._check_for_handoffs(task_id)
                            
                            # Check for tool usage
                            await self._check_for_tool_usage(task_id)
                            
                        except Exception as e:
                            logger.error(f"❌ Task execution failed: {e}")
                            self.results["continuous_monitoring"]["tasks_failed"] += 1
                    
                    # Check for new assets
                    await self._check_for_assets()
                    
                    # Check for deliverables
                    await self._check_for_deliverables()
                    
                    # Trigger goal validation if no new tasks after some completions
                    if completed_count >= 2 and len(pending_tasks) == 0:
                        logger.info("\n🔄 Triggering goal validation to generate new tasks...")
                        try:
                            validation_response = requests.post(
                                f"{API_BASE}/workspaces/{self.workspace_id}/validate-goals",
                                timeout=30
                            )
                            if validation_response.status_code == 200:
                                logger.info("   ✅ Goal validation triggered successfully")
                        except Exception as e:
                            logger.warning(f"   ⚠️ Could not trigger goal validation: {e}")
                    
                    # Check if we should continue
                    completed_count = status_counts.get('completed', 0)
                    if completed_count >= 5 and len(self.deliverables) >= 2:
                        logger.info("\n🎉 Autonomous cycle completed successfully!")
                        logger.info(f"   - Tasks completed: {completed_count}")
                        logger.info(f"   - Assets created: {len(self.created_assets)}")
                        logger.info(f"   - Deliverables: {len(self.deliverables)}")
                        break
                    
                    # Also exit if we've been monitoring for too long without progress
                    if time.time() - start_time > 300 and completed_count >= 2:  # 5 minutes
                        logger.info("\n✅ Test completed with partial success")
                        logger.info(f"   - Tasks completed: {completed_count}")
                        logger.info(f"   - Assets created: {len(self.created_assets)}")
                        logger.info(f"   - Deliverables: {len(self.deliverables)}")
                        break
                
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(check_interval)
        
        self._log_phase_result("continuous_execution", True, {
            "monitoring_duration": time.time() - start_time,
            "tasks_executed": len(self.executed_tasks)
        })

    async def _check_for_handoffs(self, task_id: str):
        """Check if the task execution involved any handoffs"""
        try:
            # Query task executions table for handoff events
            res = supabase.table("tasks").select("context_data").eq("id", task_id).execute()
            if res.data and res.data[0].get('context_data'):
                context = res.data[0]['context_data']
                if 'delegation_chain' in context and len(context['delegation_chain']) > 0:
                    handoff_count = len(context['delegation_chain'])
                    self.handoffs_observed.append({
                        "task_id": task_id,
                        "handoff_count": handoff_count,
                        "chain": context['delegation_chain']
                    })
                    self.results["continuous_monitoring"]["handoffs_count"] += handoff_count
                    logger.info(f"   🔄 Detected {handoff_count} handoff(s) in task")
        except Exception as e:
            logger.debug(f"Error checking handoffs: {e}")

    async def _check_for_tool_usage(self, task_id: str):
        """Check if the task execution used any tools"""
        try:
            # Check task result for tool usage indicators
            res = supabase.table("tasks").select("result").eq("id", task_id).execute()
            if res.data and res.data[0].get('result'):
                result = res.data[0]['result']
                result_str = str(result).lower()
                
                # Look for tool usage patterns
                tools = []
                if 'websearchtool' in result_str:
                    tools.append("WebSearchTool")
                if 'filesearchtool' in result_str:
                    tools.append("FileSearchTool")
                if 'search results' in result_str or 'found the following' in result_str:
                    tools.append("SearchTool")
                
                if tools:
                    self.tools_used.extend(tools)
                    self.results["continuous_monitoring"]["tools_used_count"] += len(tools)
                    logger.info(f"   🔧 Tools used: {', '.join(tools)}")
        except Exception as e:
            logger.debug(f"Error checking tool usage: {e}")

    async def _check_for_assets(self):
        """Check for newly created assets"""
        try:
            res = supabase.table("asset_artifacts").select("*").eq(
                "workspace_id", self.workspace_id
            ).execute()
            
            if res.data:
                new_assets = [a for a in res.data if a['id'] not in [x['id'] for x in self.created_assets]]
                for asset in new_assets:
                    self.created_assets.append(asset)
                    self.results["continuous_monitoring"]["assets_created"] += 1
                    logger.info(f"   📦 New asset created: {asset.get('name', 'Unknown')}")
        except Exception as e:
            logger.debug(f"Error checking assets: {e}")

    async def _check_for_deliverables(self):
        """Check for newly created deliverables"""
        try:
            res = supabase.table("deliverables").select("*").eq(
                "workspace_id", self.workspace_id
            ).execute()
            
            if res.data:
                new_deliverables = [d for d in res.data if d['id'] not in [x['id'] for x in self.deliverables]]
                for deliverable in new_deliverables:
                    self.deliverables.append(deliverable)
                    self.results["continuous_monitoring"]["deliverables_created"] += 1
                    logger.info(f"   🎁 New deliverable created: {deliverable.get('title', 'Unknown')}")
                    logger.info(f"      Type: {deliverable.get('type', 'Unknown')}")
        except Exception as e:
            logger.debug(f"Error checking deliverables: {e}")

    def _generate_final_report(self):
        """Generate comprehensive test report"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 FINAL TEST REPORT")
        logger.info("=" * 80)
        
        monitoring = self.results["continuous_monitoring"]
        
        logger.info(f"\n✅ Tasks:")
        logger.info(f"   - Total Executed: {monitoring['tasks_executed']}")
        logger.info(f"   - Completed: {monitoring['tasks_completed']}")
        logger.info(f"   - Failed: {monitoring['tasks_failed']}")
        
        logger.info(f"\n🔄 Handoffs:")
        logger.info(f"   - Total Count: {monitoring['handoffs_count']}")
        if self.handoffs_observed:
            for handoff in self.handoffs_observed[:3]:  # Show first 3
                logger.info(f"   - Task {handoff['task_id'][:8]}...: {handoff['handoff_count']} handoff(s)")
        
        logger.info(f"\n🔧 Tool Usage:")
        logger.info(f"   - Total Uses: {monitoring['tools_used_count']}")
        if self.tools_used:
            tool_counts = {}
            for tool in self.tools_used:
                tool_counts[tool] = tool_counts.get(tool, 0) + 1
            for tool, count in tool_counts.items():
                logger.info(f"   - {tool}: {count} uses")
        
        logger.info(f"\n📦 Assets & Deliverables:")
        logger.info(f"   - Assets Created: {monitoring['assets_created']}")
        logger.info(f"   - Deliverables: {monitoring['deliverables_created']}")
        
        # Determine overall success
        success = (
            monitoring['tasks_completed'] >= 2 and
            monitoring['assets_created'] >= 1 and
            monitoring['deliverables_created'] >= 1
        )
        
        self.results["overall_success"] = success
        
        if success:
            logger.info("\n🎉 AUTONOMOUS VIRTUOUS CYCLE: SUCCESS!")
        else:
            logger.info("\n❌ AUTONOMOUS VIRTUOUS CYCLE: INCOMPLETE")
        
        logger.info("=" * 80)


async def main():
    test = ContinuousAutonomousTest()
    await test.run_continuous_test()


if __name__ == "__main__":
    asyncio.run(main())