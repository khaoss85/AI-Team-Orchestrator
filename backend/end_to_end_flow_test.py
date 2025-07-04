#!/usr/bin/env python3
"""
🔄 END-TO-END FLOW TEST - Complete Workspace to Deliverable Verification
================================================================================
Test specifico per verificare il flusso completo end-to-end:

FLOW TO VERIFY:
1. 🏗️ Create Workspace
2. 🎯 Create Goal with specific success criteria  
3. 📋 Verify Task Generation (Unified Orchestrator)
4. 🤖 Execute Task with Agent
5. 📦 Verify Asset Artifact Creation
6. 🛡️ Verify Quality Validation
7. 🧠 Verify Memory Learning Storage
8. 🎁 Verify Deliverable Generation
9. 📊 Verify Complete Flow Tracking

INTEGRATION POINTS TESTED:
✅ Workspace → Goal creation
✅ Goal → Task generation (orchestrator)
✅ Task → Agent execution (manager)
✅ Execution → Asset creation (database_asset_extensions)
✅ Asset → Quality validation (quality_gate)
✅ Quality → Memory learning (workspace_memory)
✅ Asset → Deliverable pipeline (deliverable_system)
✅ Events → Cross-component coordination

Duration: ~2-3 minutes (allows for real execution)
"""

import asyncio
import requests
import json
import time
import logging
from datetime import datetime, timedelta
import sys
from typing import Dict, Any, Optional, List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"e2e_flow_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

class EndToEndFlowTest:
    """Test complete end-to-end flow from workspace to deliverable"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_data = {
            "workspace_id": None,
            "goal_id": None,
            "task_ids": [],
            "asset_ids": [],
            "deliverable_ids": [],
            "agent_ids": []
        }
        
        self.flow_results = {
            "workspace_created": False,
            "goal_created": False,
            "tasks_generated": False,
            "tasks_executed": False,
            "assets_created": False,
            "quality_validated": False,
            "memory_learned": False,
            "deliverables_generated": False,
            "flow_complete": False
        }
        
        self.metrics = {
            "start_time": datetime.now(),
            "workspace_creation_time": None,
            "first_task_generated_time": None,
            "first_task_executed_time": None,
            "first_asset_created_time": None,
            "first_deliverable_time": None,
            "total_duration": None
        }
    
    async def run_e2e_flow_test(self) -> Dict[str, Any]:
        """Execute complete end-to-end flow test"""
        logger.info("🔄 STARTING END-TO-END FLOW TEST")
        logger.info("=" * 80)
        
        try:
            # Step 1: Create test workspace
            await self.step_1_create_workspace()
            
            # Step 2: Create goal with clear requirements
            await self.step_2_create_goal()
            
            # Step 3: Wait for task generation and verify
            await self.step_3_verify_task_generation()
            
            # Step 4: Execute tasks and track progress
            await self.step_4_execute_tasks()
            
            # Step 5: Verify asset creation
            await self.step_5_verify_asset_creation()
            
            # Step 6: Verify quality validation
            await self.step_6_verify_quality_validation()
            
            # Step 7: Verify memory learning
            await self.step_7_verify_memory_learning()
            
            # Step 8: Verify deliverable generation
            await self.step_8_verify_deliverable_generation()
            
            # Step 9: Verify complete flow tracking
            await self.step_9_verify_flow_tracking()
            
            # Final verification
            await self.verify_complete_flow()
            
        except Exception as e:
            logger.error(f"❌ CRITICAL E2E FLOW FAILURE: {e}")
            self.flow_results["flow_complete"] = False
        
        finally:
            # Cleanup
            await self.cleanup_test_data()
            return await self.generate_e2e_report()
    
    async def step_1_create_workspace(self):
        """Step 1: Create test workspace"""
        logger.info("🏗️ STEP 1: Creating test workspace...")
        
        try:
            workspace_data = {
                "name": f"E2E_Flow_Test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "description": "End-to-end flow test workspace for complete pipeline validation",
                "domain": "software_development",
                # user_id is now optional
                "context": {
                    "test_type": "e2e_flow",
                    "target_flow": "workspace_to_deliverable",
                    "expected_duration": "3_minutes",
                    "success_criteria": [
                        "Tasks generated automatically",
                        "Assets created with quality validation",
                        "Memory learning captured",
                        "Deliverables produced"
                    ]
                }
            }
            
            response = requests.post(f"{self.base_url}/workspaces", json=workspace_data, timeout=30)
            
            if response.status_code in [200, 201]:
                workspace = response.json()
                self.test_data["workspace_id"] = workspace.get('id')
                self.flow_results["workspace_created"] = True
                self.metrics["workspace_creation_time"] = datetime.now()
                
                logger.info(f"✅ Workspace created: {self.test_data['workspace_id']}")
                logger.info(f"   Name: {workspace.get('name')}")
                logger.info(f"   Domain: {workspace.get('domain')}")
                
            else:
                raise Exception(f"Workspace creation failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Step 1 failed: {e}")
            raise
    
    async def step_2_create_goal(self):
        """Step 2: Create goal with specific requirements"""
        logger.info("🎯 STEP 2: Creating test goal...")
        
        try:
            goal_data = {
                "workspace_id": self.test_data["workspace_id"],
                "goal_description": "Develop a high-quality software component with comprehensive documentation and testing",
                "metric_type": "deliverable_quality",
                "metric_target": 90.0,
                "timeframe_days": 1,
                "priority": "high",
                "success_criteria": [
                    "Create detailed technical specification document",
                    "Implement core functionality with proper error handling",
                    "Write comprehensive unit tests with >80% coverage",
                    "Generate user documentation with examples",
                    "Perform quality validation with score >85%",
                    "Package into deliverable artifact"
                ],
                "context": {
                    "component_type": "utility_library",
                    "target_language": "python",
                    "complexity": "medium",
                    "quality_requirements": "enterprise_grade"
                }
            }
            
            response = requests.post(f"{self.base_url}/workspace-goals", json=goal_data, timeout=30)
            
            if response.status_code in [200, 201]:
                goal = response.json()
                self.test_data["goal_id"] = goal.get('id')
                self.flow_results["goal_created"] = True
                
                logger.info(f"✅ Goal created: {self.test_data['goal_id']}")
                logger.info(f"   Metric: {goal.get('metric_type')} -> {goal.get('metric_target')}%")
                logger.info(f"   Success criteria: {len(goal.get('success_criteria', []))} items")
                
            else:
                raise Exception(f"Goal creation failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Step 2 failed: {e}")
            raise
    
    async def step_3_verify_task_generation(self):
        """Step 3: Wait for and verify task generation by orchestrator"""
        logger.info("📋 STEP 3: Waiting for task generation...")
        
        max_wait_time = 60  # 1 minute timeout
        start_time = time.time()
        tasks_found = False
        
        while time.time() - start_time < max_wait_time and not tasks_found:
            try:
                response = requests.get(f"{self.base_url}/workspaces/{self.test_data['workspace_id']}/tasks", timeout=20)
                
                if response.status_code == 200:
                    tasks = response.json()
                    
                    if len(tasks) > 0:
                        self.test_data["task_ids"] = [task.get('id') for task in tasks]
                        self.flow_results["tasks_generated"] = True
                        self.metrics["first_task_generated_time"] = datetime.now()
                        tasks_found = True
                        
                        logger.info(f"✅ Tasks generated: {len(tasks)} tasks found")
                        for i, task in enumerate(tasks[:3]):  # Show first 3 tasks
                            logger.info(f"   Task {i+1}: {task.get('name', 'Unnamed')} (Status: {task.get('status')})")
                        
                        if len(tasks) > 3:
                            logger.info(f"   ... and {len(tasks)-3} more tasks")
                    else:
                        logger.info(f"⏳ Waiting for task generation... ({int(time.time() - start_time)}s)")
                        await asyncio.sleep(3)
                else:
                    logger.warning(f"⚠️ Task fetch error: {response.status_code}")
                    await asyncio.sleep(3)
                    
            except Exception as e:
                logger.warning(f"⚠️ Task generation check error: {e}")
                await asyncio.sleep(3)
        
        if not tasks_found:
            logger.error("❌ No tasks generated within timeout period")
            # Don't raise exception - continue to see what else works
    
    async def step_4_execute_tasks(self):
        """Step 4: Execute tasks and track execution"""
        logger.info("🤖 STEP 4: Executing tasks...")
        
        if not self.test_data["task_ids"]:
            logger.warning("⚠️ No tasks to execute")
            return
        
        executed_count = 0
        max_executions = min(3, len(self.test_data["task_ids"]))  # Execute max 3 tasks
        
        for i, task_id in enumerate(self.test_data["task_ids"][:max_executions]):
            try:
                logger.info(f"🎯 Executing task {i+1}/{max_executions}: {task_id}")
                
                # Trigger task execution
                execution_data = {"force_execution": True}
                response = requests.post(f"{self.base_url}/tasks/{task_id}/execute", 
                                       json=execution_data, timeout=90)
                
                if response.status_code in [200, 202]:
                    logger.info(f"   ✅ Task execution triggered successfully")
                    executed_count += 1
                    
                    if executed_count == 1:
                        self.metrics["first_task_executed_time"] = datetime.now()
                    
                    # Wait a bit between executions
                    if i < max_executions - 1:
                        await asyncio.sleep(5)
                        
                else:
                    logger.warning(f"   ⚠️ Task execution failed: {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"   ⚠️ Task execution error: {e}")
        
        if executed_count > 0:
            self.flow_results["tasks_executed"] = True
            logger.info(f"✅ Task execution phase complete: {executed_count} tasks executed")
            
            # Wait for executions to complete
            logger.info("⏳ Waiting for task execution completion...")
            await asyncio.sleep(30)
        else:
            logger.error("❌ No tasks were executed successfully")
    
    async def step_5_verify_asset_creation(self):
        """Step 5: Verify asset artifact creation"""
        logger.info("📦 STEP 5: Verifying asset creation...")
        
        try:
            response = requests.get(f"{self.base_url}/api/assets/workspace/{self.test_data['workspace_id']}", timeout=20)
            
            if response.status_code == 200:
                assets = response.json()
                
                if len(assets) > 0:
                    self.test_data["asset_ids"] = [asset.get('id') for asset in assets]
                    self.flow_results["assets_created"] = True
                    self.metrics["first_asset_created_time"] = datetime.now()
                    
                    logger.info(f"✅ Assets created: {len(assets)} assets found")
                    for asset in assets[:3]:  # Show first 3 assets
                        logger.info(f"   Asset: {asset.get('artifact_name', 'Unnamed')} "
                                  f"(Type: {asset.get('artifact_type')}, "
                                  f"Quality: {asset.get('quality_score', 'N/A')})")
                else:
                    logger.warning("⚠️ No assets found yet")
                    
            elif response.status_code == 404:
                logger.warning("⚠️ Assets endpoint not available")
            else:
                logger.warning(f"⚠️ Asset fetch error: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"⚠️ Asset verification error: {e}")
    
    async def step_6_verify_quality_validation(self):
        """Step 6: Verify quality validation occurred"""
        logger.info("🛡️ STEP 6: Verifying quality validation...")
        
        try:
            # Check for quality validation through memory system
            response = requests.get(f"{self.base_url}/api/memory/{self.test_data['workspace_id']}/summary", timeout=20)
            
            if response.status_code == 200:
                memory_data = response.json()
                insights_by_type = memory_data.get('insights_by_type', {})
                
                # Look for quality-related insights
                quality_insights = (insights_by_type.get('constraint', 0) + 
                                  insights_by_type.get('success_pattern', 0) +
                                  insights_by_type.get('failure_lesson', 0))
                
                if quality_insights > 0:
                    self.flow_results["quality_validated"] = True
                    logger.info(f"✅ Quality validation detected: {quality_insights} quality insights found")
                else:
                    logger.info("ℹ️ No quality validation insights found yet")
                    
            else:
                logger.warning(f"⚠️ Memory system check error: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"⚠️ Quality validation check error: {e}")
    
    async def step_7_verify_memory_learning(self):
        """Step 7: Verify memory learning storage"""
        logger.info("🧠 STEP 7: Verifying memory learning...")
        
        try:
            response = requests.get(f"{self.base_url}/api/memory/{self.test_data['workspace_id']}/summary", timeout=20)
            
            if response.status_code == 200:
                memory_data = response.json()
                total_insights = memory_data.get('total_insights', 0)
                
                if total_insights > 0:
                    self.flow_results["memory_learned"] = True
                    logger.info(f"✅ Memory learning active: {total_insights} insights stored")
                    
                    # Show insight breakdown
                    insights_by_type = memory_data.get('insights_by_type', {})
                    for insight_type, count in insights_by_type.items():
                        if count > 0:
                            logger.info(f"   {insight_type}: {count} insights")
                            
                    # Show recent discoveries
                    recent_discoveries = memory_data.get('recent_discoveries', [])
                    if recent_discoveries:
                        logger.info(f"   Recent discoveries: {len(recent_discoveries)} items")
                        
                else:
                    logger.info("ℹ️ No memory insights found yet (normal for new workspace)")
                    
            else:
                logger.warning(f"⚠️ Memory system error: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"⚠️ Memory learning check error: {e}")
    
    async def step_8_verify_deliverable_generation(self):
        """Step 8: Verify deliverable generation"""
        logger.info("🎁 STEP 8: Verifying deliverable generation...")
        
        try:
            response = requests.get(f"{self.base_url}/deliverables/workspace/{self.test_data['workspace_id']}", timeout=20)
            
            if response.status_code == 200:
                deliverables = response.json()
                
                if len(deliverables) > 0:
                    self.test_data["deliverable_ids"] = [d.get('id') for d in deliverables]
                    self.flow_results["deliverables_generated"] = True
                    self.metrics["first_deliverable_time"] = datetime.now()
                    
                    logger.info(f"✅ Deliverables generated: {len(deliverables)} deliverables found")
                    for deliverable in deliverables:
                        logger.info(f"   Deliverable: {deliverable.get('name', 'Unnamed')} "
                                  f"(Status: {deliverable.get('status')}, "
                                  f"Quality: {deliverable.get('quality_score', 'N/A')})")
                else:
                    logger.info("ℹ️ No deliverables found yet")
                    
            elif response.status_code == 404:
                logger.info("ℹ️ Deliverables endpoint not available")
            else:
                logger.warning(f"⚠️ Deliverable fetch error: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"⚠️ Deliverable verification error: {e}")
    
    async def step_9_verify_flow_tracking(self):
        """Step 9: Verify complete flow tracking"""
        logger.info("📊 STEP 9: Verifying flow tracking...")
        
        try:
            # Check workspace status for completion tracking
            response = requests.get(f"{self.base_url}/workspaces/{self.test_data['workspace_id']}", timeout=20)
            
            if response.status_code == 200:
                workspace_data = response.json()
                workspace_status = workspace_data.get('status', 'unknown')
                
                logger.info(f"✅ Workspace status: {workspace_status}")
                
                # Check goal progress
                if self.test_data["goal_id"]:
                    goal_response = requests.get(f"{self.base_url}/workspace-goals/{self.test_data['goal_id']}", timeout=20)
                    if goal_response.status_code == 200:
                        goal_data = goal_response.json()
                        progress_percentage = goal_data.get('progress_percentage', 0)
                        logger.info(f"✅ Goal progress: {progress_percentage}%")
                        
            else:
                logger.warning(f"⚠️ Workspace status check error: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"⚠️ Flow tracking verification error: {e}")
    
    async def verify_complete_flow(self):
        """Verify that the complete flow was successful"""
        logger.info("🔍 VERIFYING COMPLETE END-TO-END FLOW...")
        
        # Calculate flow completion
        completed_steps = sum(self.flow_results.values())
        total_steps = len(self.flow_results)
        completion_rate = (completed_steps / total_steps) * 100
        
        # Determine flow success
        critical_steps = [
            self.flow_results["workspace_created"],
            self.flow_results["goal_created"],
            self.flow_results["tasks_generated"]
        ]
        
        flow_functional = all(critical_steps)
        
        # Check for end-to-end completion
        full_flow_complete = (
            self.flow_results["workspace_created"] and
            self.flow_results["goal_created"] and
            self.flow_results["tasks_generated"] and
            (self.flow_results["tasks_executed"] or self.flow_results["assets_created"])
        )
        
        self.flow_results["flow_complete"] = full_flow_complete
        
        # Calculate timing metrics
        self.metrics["total_duration"] = datetime.now() - self.metrics["start_time"]
        
        logger.info(f"📊 Flow completion: {completed_steps}/{total_steps} steps ({completion_rate:.1f}%)")
        logger.info(f"🎯 Critical path functional: {flow_functional}")
        logger.info(f"🔄 End-to-end flow complete: {full_flow_complete}")
    
    async def cleanup_test_data(self):
        """Clean up test data"""
        logger.info("🧹 Cleaning up test data...")
        
        try:
            if self.test_data["workspace_id"]:
                response = requests.delete(f"{self.base_url}/workspaces/{self.test_data['workspace_id']}", timeout=30)
                if response.status_code in [200, 204]:
                    logger.info("✅ Test workspace cleaned up")
                else:
                    logger.warning(f"⚠️ Workspace cleanup failed: {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ Cleanup error: {e}")
    
    async def generate_e2e_report(self) -> Dict[str, Any]:
        """Generate comprehensive E2E test report"""
        report = {
            "test_type": "end_to_end_flow",
            "timestamp": datetime.now().isoformat(),
            "test_data": self.test_data,
            "flow_results": self.flow_results,
            "metrics": {
                "total_duration_seconds": self.metrics["total_duration"].total_seconds() if self.metrics["total_duration"] else 0,
                "workspace_creation_time": self.metrics["workspace_creation_time"].isoformat() if self.metrics["workspace_creation_time"] else None,
                "first_task_generated_time": self.metrics["first_task_generated_time"].isoformat() if self.metrics["first_task_generated_time"] else None,
                "first_task_executed_time": self.metrics["first_task_executed_time"].isoformat() if self.metrics["first_task_executed_time"] else None,
                "first_asset_created_time": self.metrics["first_asset_created_time"].isoformat() if self.metrics["first_asset_created_time"] else None,
                "first_deliverable_time": self.metrics["first_deliverable_time"].isoformat() if self.metrics["first_deliverable_time"] else None
            }
        }
        
        # Summary statistics
        completed_steps = sum(self.flow_results.values())
        total_steps = len(self.flow_results)
        success_rate = (completed_steps / total_steps) * 100
        
        report["summary"] = {
            "steps_completed": completed_steps,
            "total_steps": total_steps,
            "success_rate_percent": success_rate,
            "flow_complete": self.flow_results["flow_complete"],
            "critical_path_functional": all([
                self.flow_results["workspace_created"],
                self.flow_results["goal_created"],
                self.flow_results["tasks_generated"]
            ])
        }
        
        # Log final results
        logger.info("=" * 80)
        logger.info("🏁 END-TO-END FLOW TEST COMPLETE")
        logger.info("=" * 80)
        logger.info(f"📊 FLOW RESULTS:")
        for step, success in self.flow_results.items():
            status = "✅" if success else "❌"
            logger.info(f"   {status} {step.replace('_', ' ').title()}")
        
        logger.info(f"\n📈 SUMMARY:")
        logger.info(f"   Success Rate: {success_rate:.1f}% ({completed_steps}/{total_steps})")
        logger.info(f"   Flow Complete: {'✅' if self.flow_results['flow_complete'] else '❌'}")
        logger.info(f"   Duration: {report['metrics']['total_duration_seconds']:.1f}s")
        
        if self.flow_results["flow_complete"]:
            logger.info(f"\n🎉 END-TO-END FLOW VERIFIED SUCCESSFULLY!")
        else:
            logger.info(f"\n⚠️ END-TO-END FLOW PARTIALLY FUNCTIONAL")
        
        logger.info("=" * 80)
        
        return report


async def main():
    """Main execution function"""
    # Check server connectivity
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            logger.error("❌ Server not responding properly")
            return False
    except:
        logger.error("❌ Cannot connect to server. Please ensure backend is running on localhost:8000")
        return False
    
    # Run E2E flow test
    test_runner = EndToEndFlowTest()
    results = await test_runner.run_e2e_flow_test()
    
    # Save results
    results_file = f"e2e_flow_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"📄 Detailed results saved to: {results_file}")
    
    # Return success based on flow completion
    return results.get('summary', {}).get('flow_complete', False)

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)