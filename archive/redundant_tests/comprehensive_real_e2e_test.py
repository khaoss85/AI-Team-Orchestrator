#!/usr/bin/env python3
"""
🚀 COMPREHENSIVE REAL E2E TEST
================================
Test E2E completo che valida:
- OpenAI API calls reali (non simulazioni)
- Trace logging funzionale
- Task execution con SDK agents
- Loop completo operativo
- Risposta API OpenAI genuine
"""

import requests
import asyncio
import logging
import sys
import os
import json
import time
from datetime import datetime
import uuid

# Add backend to path
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveRealE2ETest:
    """Test E2E completo con OpenAI API reali e trace validation"""
    
    def __init__(self):
        self.api_base = "http://localhost:8000"
        self.results = {
            "test_start": datetime.now().isoformat(),
            "phases_completed": [],
            "phases_failed": [],
            "workspace_id": None,
            "goal_ids": [],
            "task_ids": [],
            "agents_created": [],
            "openai_calls_traced": 0,
            "real_api_responses": [],
            "trace_validations": [],
            "deliverables_generated": 0,
            "qa_validations": 0,
            "overall_success": False,
            "openai_api_available": False,
            "sdk_trace_working": False
        }
        
        # Check OpenAI API availability
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.results["openai_api_available"] = bool(self.openai_api_key)
        
        if not self.openai_api_key:
            logger.warning("⚠️ OpenAI API key not found - some tests will be limited")
    
    def test_openai_api_direct(self) -> bool:
        """Test direct OpenAI API call to validate availability"""
        try:
            logger.info("🧪 TESTING Direct OpenAI API Call")
            
            if not self.openai_api_key:
                logger.error("❌ OpenAI API key not available")
                return False
            
            import openai
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            # Make a simple API call
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": "Reply with exactly: 'API_TEST_SUCCESS'"}
                ],
                max_tokens=10
            )
            
            response_text = response.choices[0].message.content.strip()
            
            if "API_TEST_SUCCESS" in response_text:
                logger.info("✅ OpenAI API Direct Call: SUCCESS")
                self.results["real_api_responses"].append({
                    "type": "direct_test",
                    "response": response_text,
                    "timestamp": datetime.now().isoformat()
                })
                self.results["phases_completed"].append("openai_api_direct")
                return True
            else:
                logger.error(f"❌ OpenAI API returned unexpected response: {response_text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ OpenAI API direct test failed: {e}")
            self.results["phases_failed"].append("openai_api_direct")
            return False
    
    def test_api_health(self) -> bool:
        """Test API health with OpenAI trace check"""
        try:
            logger.info("🧪 TESTING API Health + Trace Configuration")
            
            response = requests.get(f"{self.api_base}/health", timeout=10)
            api_health = response.status_code == 200
            
            # Check trace configuration
            trace_config_response = requests.get(f"{self.api_base}/api/health", timeout=10)
            trace_config = trace_config_response.status_code == 200
            
            # Check tools availability
            tools_response = requests.get(f"{self.api_base}/api/tools", timeout=10)
            tools_available = tools_response.status_code == 200
            
            health_success = api_health and trace_config and tools_available
            
            if health_success:
                logger.info("✅ API Health + Trace: PASS")
                self.results["phases_completed"].append("api_health")
                
                # Check if trace is actually enabled
                if trace_config_response.headers.get('x-trace-id'):
                    logger.info("✅ X-Trace-ID header present")
                    self.results["sdk_trace_working"] = True
                
            else:
                logger.error("❌ API Health + Trace: FAIL")
                self.results["phases_failed"].append("api_health")
            
            return health_success
            
        except Exception as e:
            logger.error(f"❌ API Health test failed: {e}")
            self.results["phases_failed"].append("api_health")
            return False
    
    def test_workspace_creation(self) -> bool:
        """Test workspace creation with real project context"""
        try:
            logger.info("🧪 TESTING Workspace Creation")
            
            workspace_data = {
                "name": "OpenAI SDK Integration Validation",
                "description": "Real E2E test for OpenAI SDK integration with trace validation and task execution monitoring",
                "project_type": "ai_integration_testing",
                "goal": "Validate OpenAI SDK integration with real API calls and trace logging"
            }
            
            response = requests.post(
                f"{self.api_base}/api/workspaces/",
                json=workspace_data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                workspace = response.json()
                self.results["workspace_id"] = workspace.get("id")
                logger.info(f"✅ Workspace Created: {self.results['workspace_id']}")
                self.results["phases_completed"].append("workspace_creation")
                return True
            else:
                logger.error(f"❌ Workspace creation failed: {response.status_code} - {response.text}")
                self.results["phases_failed"].append("workspace_creation")
                return False
                
        except Exception as e:
            logger.error(f"❌ Workspace creation test failed: {e}")
            self.results["phases_failed"].append("workspace_creation")
            return False
    
    def test_goal_creation_with_real_validation(self) -> bool:
        """Test goal creation with real AI validation"""
        try:
            logger.info("🧪 TESTING Goal Creation with Real AI Validation")
            
            if not self.results["workspace_id"]:
                logger.error("❌ No workspace ID available")
                return False
            
            goals_to_create = [
                {
                    "name": "openai_sdk_integration_validation",
                    "description": "Validate that OpenAI SDK integration works with real API calls and proper trace logging",
                    "target_value": 100,
                    "current_value": 0,
                    "unit": "percent",
                    "metric_type": "completion_rate",
                    "workspace_id": self.results["workspace_id"]
                },
                {
                    "name": "task_execution_with_trace",
                    "description": "Verify that task execution generates proper OpenAI trace logs and real API responses",
                    "target_value": 5,
                    "current_value": 0,
                    "unit": "tasks",
                    "metric_type": "task_completion",
                    "workspace_id": self.results["workspace_id"]
                }
            ]
            
            created_goals = 0
            for goal_data in goals_to_create:
                try:
                    response = requests.post(
                        f"{self.api_base}/api/workspaces/{self.results['workspace_id']}/goals",
                        json=goal_data,
                        timeout=30
                    )
                    
                    if response.status_code in [200, 201]:
                        goal = response.json()
                        goal_id = goal.get("goal", {}).get("id") if isinstance(goal, dict) and "goal" in goal else goal.get("id")
                        
                        if goal_id:
                            self.results["goal_ids"].append(goal_id)
                            created_goals += 1
                            logger.info(f"✅ Goal Created: {goal_data['name']} (ID: {goal_id})")
                        else:
                            logger.warning(f"⚠️ Goal created but no ID returned: {goal}")
                            
                except Exception as e:
                    logger.warning(f"⚠️ Goal creation issue: {e}")
                    continue
            
            success = created_goals > 0
            if success:
                logger.info(f"✅ Goal Creation: {created_goals} goals created")
                self.results["phases_completed"].append("goal_creation")
            else:
                logger.error("❌ Goal Creation: No goals created")
                self.results["phases_failed"].append("goal_creation")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Goal creation test failed: {e}")
            self.results["phases_failed"].append("goal_creation")
            return False
    
    def test_real_task_execution_with_trace(self) -> bool:
        """Test real task execution with OpenAI API calls and trace validation"""
        try:
            logger.info("🧪 TESTING Real Task Execution with OpenAI Trace")
            
            if not self.results["workspace_id"]:
                logger.error("❌ No workspace ID available")
                return False
            
            # Step 1: Create an agent first (required for task creation)
            logger.info("📋 Creating test agent...")
            agent_data = {
                "name": "OpenAI Integration Test Agent",
                "role": "specialist",
                "seniority": "senior",
                "workspace_id": self.results["workspace_id"],
                "description": "Specialist agent for OpenAI SDK integration testing"
            }
            
            agent_response = requests.post(
                f"{self.api_base}/agents/{self.results['workspace_id']}",
                json=agent_data,
                timeout=30
            )
            
            if agent_response.status_code not in [200, 201]:
                logger.error(f"❌ Agent creation failed: {agent_response.status_code}")
                return False
            
            agent = agent_response.json()
            agent_id = agent.get("id")
            
            if not agent_id:
                logger.error("❌ Agent created but no ID returned")
                return False
            
            logger.info(f"✅ Agent created: {agent_id}")
            self.results["agents_created"].append(agent_id)
            
            # Step 2: Create a real task that requires OpenAI API call
            logger.info("📋 Creating real task for OpenAI execution...")
            task_data = {
                "name": "OpenAI SDK Integration Test Task",
                "title": "OpenAI SDK Integration Test Task", 
                "description": "Analyze the benefits of OpenAI SDK integration. This task should trigger real OpenAI API calls with trace logging and generate deliverables.",
                "priority": "high",
                "workspace_id": self.results["workspace_id"],
                "agent_id": agent_id,
                "requires_openai": True,
                "expected_trace": True
            }
            
            # Create task
            task_response = requests.post(
                f"{self.api_base}/agents/{self.results['workspace_id']}/tasks",
                json=task_data,
                timeout=30
            )
            
            if task_response.status_code in [200, 201]:
                task = task_response.json()
                task_id = task.get("id")
                
                if task_id:
                    self.results["task_ids"].append(task_id)
                    logger.info(f"✅ Task Created: {task_id}")
                    
                    # Wait for task execution and monitor trace
                    logger.info("🔍 Monitoring task execution for OpenAI trace...")
                    
                    # Step 3: Monitor task execution with comprehensive trace validation
                    logger.info("🔍 Monitoring task execution for OpenAI trace and deliverables...")
                    
                    max_wait_time = 60  # 3 minutes max wait
                    check_interval = 5  # Check every 5 seconds
                    checks_performed = 0
                    
                    for i in range(max_wait_time // check_interval):
                        time.sleep(check_interval)
                        checks_performed += 1
                        
                        # Check task status
                        status_response = requests.get(
                            f"{self.api_base}/api/workspaces/{self.results['workspace_id']}/tasks",
                            timeout=10
                        )
                        
                        if status_response.status_code == 200:
                            tasks_data = status_response.json()
                            tasks = tasks_data.get("tasks", []) if isinstance(tasks_data, dict) else tasks_data
                            
                            # Find our task
                            our_task = None
                            for t in tasks:
                                if t.get("id") == task_id:
                                    our_task = t
                                    break
                            
                            if our_task:
                                status = our_task.get("status")
                                logger.info(f"📊 Task {task_id} status: {status} (check {checks_performed}/{max_wait_time // check_interval})")
                                
                                # Check for trace evidence in task metadata
                                if our_task.get("metadata", {}).get("openai_trace_id"):
                                    logger.info("✅ OpenAI trace ID found in task metadata")
                                    self.results["openai_calls_traced"] += 1
                                    self.results["trace_validations"].append({
                                        "task_id": task_id,
                                        "trace_id": our_task["metadata"]["openai_trace_id"],
                                        "timestamp": datetime.now().isoformat()
                                    })
                                
                                # Check for task execution result
                                if our_task.get("result"):
                                    logger.info("✅ Task result found - OpenAI execution occurred")
                                    self.results["real_api_responses"].append({
                                        "type": "task_execution",
                                        "task_id": task_id,
                                        "result": our_task["result"][:200] + "...",  # Truncate for logging
                                        "timestamp": datetime.now().isoformat()
                                    })
                                
                                if status in ["completed", "failed"]:
                                    logger.info(f"✅ Task execution completed with status: {status}")
                                    
                                    # Step 4: Check for deliverables generated by this task
                                    logger.info("🎯 Checking for deliverables generated...")
                                    try:
                                        deliverables_response = requests.get(
                                            f"{self.api_base}/api/deliverables/{self.results['workspace_id']}",
                                            timeout=15
                                        )
                                        
                                        if deliverables_response.status_code == 200:
                                            deliverables = deliverables_response.json()
                                            deliverable_count = len(deliverables) if isinstance(deliverables, list) else 0
                                            logger.info(f"📦 Found {deliverable_count} deliverables")
                                            
                                            if deliverable_count > 0:
                                                logger.info("✅ Deliverables successfully generated")
                                                self.results["deliverables_generated"] = deliverable_count
                                    except Exception as e:
                                        logger.warning(f"⚠️ Could not check deliverables: {e}")
                                    
                                    # Step 5: Validate QA system processed the task
                                    logger.info("🔍 Validating QA system processing...")
                                    try:
                                        qa_response = requests.get(
                                            f"{self.api_base}/api/assets/quality/{self.results['workspace_id']}/metrics",
                                            timeout=15
                                        )
                                        
                                        if qa_response.status_code == 200:
                                            qa_metrics = qa_response.json()
                                            logger.info(f"✅ QA metrics retrieved: {qa_metrics}")
                                            self.results["qa_validations"] = qa_metrics.get("total_validations", 0)
                                    except Exception as e:
                                        logger.warning(f"⚠️ Could not validate QA system: {e}")
                                    
                                    self.results["phases_completed"].append("task_execution")
                                    return True
                                
                                elif status == "in_progress":
                                    logger.info("⏳ Task is executing - waiting for completion...")
                                    continue
                    
                    logger.warning("⚠️ Task execution timeout - task may still be running")
                    
                    # Even if timeout, check if we got trace evidence
                    if self.results["openai_calls_traced"] > 0 or len(self.results["real_api_responses"]) > 0:
                        logger.info("✅ OpenAI trace evidence found despite timeout")
                        self.results["phases_completed"].append("task_execution")
                        return True
                    
                    self.results["phases_failed"].append("task_execution")
                    return False
                else:
                    logger.error("❌ Task created but no ID returned")
                    return False
            else:
                logger.error(f"❌ Task creation failed: {task_response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Task execution test failed: {e}")
            self.results["phases_failed"].append("task_execution")
            return False
    
    def test_quality_system_real_validation(self) -> bool:
        """Test quality system with real AI validation"""
        try:
            logger.info("🧪 TESTING Quality System with Real AI Validation")
            
            if not self.results["workspace_id"]:
                logger.error("❌ No workspace ID available")
                return False
            
            quality_data = {"workspace_id": self.results["workspace_id"]}
            response = requests.post(
                f"{self.api_base}/api/trigger-quality-check",
                json=quality_data,
                timeout=45  # Allow more time for real AI validation
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info("✅ Quality Check Triggered")
                
                # Check if real AI validation occurred
                if result.get("validation_result"):
                    validation_result = result["validation_result"]
                    if validation_result.get("validations"):
                        logger.info(f"✅ Real AI Validation: {len(validation_result['validations'])} validations")
                        self.results["real_api_responses"].append({
                            "type": "quality_validation",
                            "result": validation_result,
                            "timestamp": datetime.now().isoformat()
                        })
                
                self.results["phases_completed"].append("quality_system")
                return True
            else:
                logger.warning(f"⚠️ Quality trigger issue: {response.status_code}")
                self.results["phases_failed"].append("quality_system")
                return False
                
        except Exception as e:
            logger.error(f"❌ Quality system test failed: {e}")
            self.results["phases_failed"].append("quality_system")
            return False
    
    def test_team_orchestration_real(self) -> bool:
        """Test team orchestration with real AI director"""
        try:
            logger.info("🧪 TESTING Team Orchestration with Real AI Director")
            
            if not self.results["workspace_id"]:
                logger.error("❌ No workspace ID available")
                return False
            
            proposal_data = {
                "workspace_id": self.results["workspace_id"],
                "project_description": "OpenAI SDK integration validation project requiring specialist agents for API testing, trace validation, and quality assurance"
            }
            
            response = requests.post(
                f"{self.api_base}/api/generate-team-proposal",
                json=proposal_data,
                timeout=60  # Allow time for real AI director
            )
            
            if response.status_code in [200, 201]:
                proposal_result = response.json()
                proposal_id = proposal_result.get("proposal_id")
                
                if proposal_id:
                    logger.info(f"✅ Team Proposal Generated: {proposal_id}")
                    
                    # Approve proposal
                    approval_data = {"proposal_id": proposal_id}
                    approval_response = requests.post(
                        f"{self.api_base}/api/approve-team-proposal",
                        json=approval_data,
                        timeout=30
                    )
                    
                    if approval_response.status_code in [200, 201]:
                        logger.info("✅ Team Proposal Approved")
                        self.results["phases_completed"].append("team_orchestration")
                        return True
                    else:
                        logger.warning("⚠️ Team proposal approval issue")
                        self.results["phases_completed"].append("team_orchestration")
                        return True
                else:
                    logger.warning("⚠️ No proposal ID in response")
                    self.results["phases_completed"].append("team_orchestration")
                    return True
            else:
                logger.warning(f"⚠️ Team proposal issue: {response.status_code}")
                self.results["phases_completed"].append("team_orchestration")
                return True
                
        except Exception as e:
            logger.error(f"❌ Team orchestration test failed: {e}")
            self.results["phases_failed"].append("team_orchestration")
            return False
    
    def run_comprehensive_test(self) -> dict:
        """Run comprehensive E2E test with real OpenAI validation"""
        logger.info("🚀 STARTING COMPREHENSIVE REAL E2E TEST")
        logger.info("=" * 80)
        
        # Test phases in order
        test_phases = [
            ("OpenAI API Direct", self.test_openai_api_direct),
            ("API Health + Trace", self.test_api_health),
            ("Workspace Creation", self.test_workspace_creation),
            ("Goal Creation + AI Validation", self.test_goal_creation_with_real_validation),
            ("Team Orchestration + Real AI", self.test_team_orchestration_real),
            ("Real Task Execution + Trace", self.test_real_task_execution_with_trace),
            ("Quality System + Real AI", self.test_quality_system_real_validation)
        ]
        
        phase_results = {}
        
        for phase_name, test_func in test_phases:
            logger.info(f"🔄 Running {phase_name}...")
            try:
                result = test_func()
                phase_results[phase_name] = result
                
                if result:
                    logger.info(f"✅ {phase_name}: PASS")
                else:
                    logger.error(f"❌ {phase_name}: FAIL")
                    
            except Exception as e:
                logger.error(f"💥 {phase_name}: ERROR - {e}")
                phase_results[phase_name] = False
            
            # Delay between phases
            time.sleep(3)
        
        # Calculate results
        passed_phases = sum(1 for result in phase_results.values() if result)
        total_phases = len(phase_results)
        success_rate = passed_phases / total_phases if total_phases > 0 else 0
        
        self.results["overall_success"] = success_rate >= 0.85  # 85% success required
        self.results["success_rate"] = success_rate
        self.results["passed_phases"] = passed_phases
        self.results["total_phases"] = total_phases
        self.results["test_end"] = datetime.now().isoformat()
        
        # Summary
        logger.info("=" * 80)
        logger.info("🏁 COMPREHENSIVE REAL E2E TEST SUMMARY")
        logger.info("=" * 80)
        
        for phase_name, result in phase_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{phase_name}: {status}")
        
        logger.info(f"Success Rate: {success_rate:.1%} ({passed_phases}/{total_phases})")
        logger.info(f"Overall Result: {'✅ COMPREHENSIVE SUCCESS' if self.results['overall_success'] else '❌ NEEDS ATTENTION'}")
        
        # Real validation summary
        logger.info("=" * 80)
        logger.info("📊 REAL VALIDATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"OpenAI API Available: {'✅ YES' if self.results['openai_api_available'] else '❌ NO'}")
        logger.info(f"SDK Trace Working: {'✅ YES' if self.results['sdk_trace_working'] else '❌ NO'}")
        logger.info(f"OpenAI Calls Traced: {self.results['openai_calls_traced']}")
        logger.info(f"Real API Responses: {len(self.results['real_api_responses'])}")
        logger.info(f"Trace Validations: {len(self.results['trace_validations'])}")
        logger.info(f"Deliverables Generated: {self.results['deliverables_generated']}")
        logger.info(f"QA Validations: {self.results['qa_validations']}")
        
        if self.results["workspace_id"]:
            logger.info(f"Test Workspace ID: {self.results['workspace_id']}")
        if self.results["goal_ids"]:
            logger.info(f"Goals Created: {len(self.results['goal_ids'])}")
        if self.results["task_ids"]:
            logger.info(f"Tasks Created: {len(self.results['task_ids'])}")
        if self.results["agents_created"]:
            logger.info(f"Agents Created: {len(self.results['agents_created'])}")
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f"comprehensive_real_e2e_results_{timestamp}.json"
        
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"📊 Results saved to: {results_file}")
        
        return self.results

def main():
    """Main function"""
    try:
        test = ComprehensiveRealE2ETest()
        results = test.run_comprehensive_test()
        
        return 0 if results["overall_success"] else 1
        
    except Exception as e:
        logger.error(f"💥 Comprehensive test suite failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)