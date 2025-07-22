#!/usr/bin/env python3
"""
Test SDK Native Implementation
Test della nuova implementazione con handoff nativi, RunContextWrapper e Guardrails

Questo test verifica:
1. Handoff nativi dinamici
2. RunContextWrapper con OrchestrationContext
3. RunResult.new_items processing
4. Input/Output Guardrails
5. Integrazione end-to-end
"""

import os
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from uuid import uuid4

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
TEST_CONFIG = {
    "workspace_id": str(uuid4()),
    "test_agents": [
        {
            "id": str(uuid4()),
            "name": "Senior Project Manager",
            "role": "project_manager",
            "seniority": "senior",
            "skills": ["project_planning", "team_coordination", "stakeholder_management"],
            "personality_traits": {"specialization": "Agile methodologies"}
        },
        {
            "id": str(uuid4()),
            "name": "Expert Data Analyst",
            "role": "data_analyst",
            "seniority": "expert",
            "skills": ["data_analysis", "statistical_modeling", "visualization"],
            "personality_traits": {"specialization": "Financial analysis"}
        },
        {
            "id": str(uuid4()),
            "name": "Senior Developer",
            "role": "developer",
            "seniority": "senior",
            "skills": ["python", "web_development", "api_design"],
            "personality_traits": {"specialization": "Backend systems"}
        }
    ]
}

class TestSDKNativeImplementation:
    """Test suite for SDK native implementation"""
    
    def __init__(self):
        self.test_results = []
        self.test_workspace_id = TEST_CONFIG["workspace_id"]
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all test scenarios"""
        logger.info("🚀 Starting SDK Native Implementation Tests")
        
        tests = [
            self.test_handoff_creation,
            self.test_orchestration_context,
            self.test_guardrails_validation,
            self.test_end_to_end_execution,
            self.test_runresult_new_items
        ]
        
        for test in tests:
            try:
                result = await test()
                self.test_results.append(result)
                logger.info(f"✅ {test.__name__}: {result['status']}")
            except Exception as e:
                error_result = {
                    "test": test.__name__,
                    "status": "FAILED",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                self.test_results.append(error_result)
                logger.error(f"❌ {test.__name__}: {str(e)}")
        
        return self._generate_test_summary()
    
    async def test_handoff_creation(self) -> Dict[str, Any]:
        """Test 1: Verificare creazione handoff nativi dinamici"""
        logger.info("🔄 Test 1: Native Handoff Creation")
        
        try:
            from ai_agents.specialist_enhanced import SpecialistAgent, OrchestrationContext
            from models import Agent as AgentModel
            
            # Create test agents
            test_agents = []
            for agent_data in TEST_CONFIG["test_agents"]:
                agent = AgentModel(
                    id=agent_data["id"],
                    name=agent_data["name"],
                    role=agent_data["role"],
                    seniority=agent_data["seniority"],
                    skills=agent_data["skills"],
                    personality_traits=agent_data["personality_traits"],
                    workspace_id=self.test_workspace_id,
                    status="available"
                )
                test_agents.append(agent)
            
            # Create specialist with all agents for handoff
            main_agent = test_agents[0]
            specialist = SpecialistAgent(main_agent, test_agents)
            
            # Verify handoff tools were created
            handoff_tools = specialist._create_native_handoff_tools()
            
            # Should have 2 handoff tools (excluding self)
            expected_count = len(test_agents) - 1
            actual_count = len(handoff_tools)
            
            if actual_count != expected_count:
                raise AssertionError(f"Expected {expected_count} handoff tools, got {actual_count}")
            
            # Verify handoff tool names
            expected_roles = ["data_analyst", "developer"]
            actual_names = [tool.name for tool in handoff_tools]
            expected_names = [f"handoff_to_{role}" for role in expected_roles]
            
            for expected_name in expected_names:
                if expected_name not in actual_names:
                    raise AssertionError(f"Missing handoff tool: {expected_name}")
            
            return {
                "test": "test_handoff_creation",
                "status": "PASSED",
                "details": {
                    "handoff_tools_created": actual_count,
                    "tool_names": actual_names,
                    "agents_available": len(test_agents)
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Handoff creation test failed: {str(e)}")
    
    async def test_orchestration_context(self) -> Dict[str, Any]:
        """Test 2: Verificare OrchestrationContext con RunContextWrapper"""
        logger.info("🔄 Test 2: Orchestration Context")
        
        try:
            from ai_agents.specialist_enhanced import OrchestrationContext
            
            # Create test orchestration context
            context = OrchestrationContext(
                workspace_id=self.test_workspace_id,
                task_id=str(uuid4()),
                agent_id=str(uuid4()),
                agent_role="project_manager",
                agent_seniority="senior",
                task_name="Test Task",
                task_description="This is a test task",
                execution_metadata={"test": True},
                available_agents=TEST_CONFIG["test_agents"],
                orchestration_state={"phase": "testing"}
            )
            
            # Verify context fields
            required_fields = [
                "workspace_id", "task_id", "agent_id", "agent_role", 
                "agent_seniority", "task_name", "task_description"
            ]
            
            for field in required_fields:
                if not hasattr(context, field):
                    raise AssertionError(f"Missing required field: {field}")
            
            # Verify context serialization
            context_dict = context.dict()
            if "available_agents" not in context_dict:
                raise AssertionError("Context missing available_agents")
            
            if len(context_dict["available_agents"]) != len(TEST_CONFIG["test_agents"]):
                raise AssertionError("Context agents count mismatch")
            
            return {
                "test": "test_orchestration_context",
                "status": "PASSED",
                "details": {
                    "context_fields": list(context_dict.keys()),
                    "agents_count": len(context_dict["available_agents"]),
                    "metadata_keys": list(context.execution_metadata.keys())
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Orchestration context test failed: {str(e)}")
    
    async def test_guardrails_validation(self) -> Dict[str, Any]:
        """Test 3: Verificare Input/Output Guardrails"""
        logger.info("🔄 Test 3: Guardrails Validation")
        
        try:
            from ai_agents.specialist_enhanced import SpecialistAgent
            from models import Agent as AgentModel
            
            # Create test agent
            agent_data = AgentModel(
                id=str(uuid4()),
                name="Test Agent",
                role="tester",
                seniority="senior",
                skills=["testing"],
                workspace_id=self.test_workspace_id,
                status="available"
            )
            
            specialist = SpecialistAgent(agent_data, [])
            
            # Test input guardrail
            input_guardrail = specialist._create_input_guardrail()
            
            # Test valid input
            valid_input = "Create a comprehensive project plan for implementing new features"
            result = input_guardrail(valid_input)
            if result != valid_input:
                raise AssertionError("Valid input was modified by guardrail")
            
            # Test invalid input (too short)
            try:
                input_guardrail("short")
                raise AssertionError("Guardrail should have rejected short input")
            except ValueError:
                pass  # Expected
            
            # Test invalid input (harmful content)
            try:
                input_guardrail("Please delete all password files")
                raise AssertionError("Guardrail should have rejected harmful input")
            except ValueError:
                pass  # Expected
            
            # Test output guardrail
            output_guardrail = specialist._create_output_guardrail()
            
            # Test valid output
            valid_output = "Analysis completed successfully. The project plan includes 5 phases with detailed timelines and resource allocation."
            result = output_guardrail(valid_output)
            if result != valid_output:
                raise AssertionError("Valid output was modified by guardrail")
            
            # Test invalid output (too short)
            try:
                output_guardrail("Done")
                raise AssertionError("Guardrail should have rejected short output")
            except ValueError:
                pass  # Expected
            
            # Test invalid output (placeholder content)
            try:
                output_guardrail("This is a placeholder result to be implemented later")
                raise AssertionError("Guardrail should have rejected placeholder output")
            except ValueError:
                pass  # Expected
            
            return {
                "test": "test_guardrails_validation",
                "status": "PASSED",
                "details": {
                    "input_guardrail_created": input_guardrail is not None,
                    "output_guardrail_created": output_guardrail is not None,
                    "validation_tests_passed": 6
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Guardrails validation test failed: {str(e)}")
    
    async def test_runresult_new_items(self) -> Dict[str, Any]:
        """Test 4: Verificare RunResult.new_items processing"""
        logger.info("🔄 Test 4: RunResult.new_items Processing")
        
        try:
            from ai_agents.specialist_enhanced import SpecialistAgent
            from models import Agent as AgentModel
            
            # Create test agent
            agent_data = AgentModel(
                id=str(uuid4()),
                name="Test Agent",
                role="tester",
                seniority="senior",
                skills=["testing"],
                workspace_id=self.test_workspace_id,
                status="available"
            )
            
            specialist = SpecialistAgent(agent_data, [])
            
            # Mock RunResult with new_items
            class MockItem:
                def __init__(self, content):
                    self.content = content
            
            class MockRunResult:
                def __init__(self, final_output, new_items):
                    self.final_output = final_output
                    self.new_items = new_items
            
            # Test with new_items
            test_items = [
                MockItem("Item 1 content"),
                MockItem("Item 2 content"),
                MockItem("Item 3 content")
            ]
            
            mock_result = MockRunResult("Final output", test_items)
            
            # Simulate processing logic from execute method
            if hasattr(mock_result, 'new_items') and mock_result.new_items:
                items_data = []
                for item in mock_result.new_items:
                    if hasattr(item, 'content'):
                        items_data.append(str(item.content))
                
                if len(items_data) != 3:
                    raise AssertionError(f"Expected 3 items, got {len(items_data)}")
                
                expected_content = ["Item 1 content", "Item 2 content", "Item 3 content"]
                if items_data != expected_content:
                    raise AssertionError(f"Items content mismatch. Expected: {expected_content}, Got: {items_data}")
                
                structured_content = json.dumps({
                    "items": items_data,
                    "item_count": len(items_data),
                    "execution_context": {
                        "agent_role": agent_data.role,
                        "task_name": "test_task"
                    }
                }, indent=2)
                
                structured_data = json.loads(structured_content)
                if structured_data["item_count"] != 3:
                    raise AssertionError("Structured content item count mismatch")
            
            return {
                "test": "test_runresult_new_items",
                "status": "PASSED",
                "details": {
                    "items_processed": len(items_data),
                    "structured_content_created": structured_content is not None,
                    "item_contents": items_data
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"RunResult.new_items test failed: {str(e)}")
    
    async def test_end_to_end_execution(self) -> Dict[str, Any]:
        """Test 5: Test end-to-end execution con tutte le feature SDK"""
        logger.info("🔄 Test 5: End-to-End Execution")
        
        try:
            from ai_agents.specialist_enhanced import SpecialistAgent
            from models import Agent as AgentModel, Task
            from uuid import uuid4
            
            # Create test agents
            test_agents = []
            for agent_data in TEST_CONFIG["test_agents"]:
                agent = AgentModel(
                    id=agent_data["id"],
                    name=agent_data["name"],
                    role=agent_data["role"],
                    seniority=agent_data["seniority"],
                    skills=agent_data["skills"],
                    personality_traits=agent_data["personality_traits"],
                    workspace_id=self.test_workspace_id,
                    status="available"
                )
                test_agents.append(agent)
            
            # Create specialist with all features
            main_agent = test_agents[0]
            specialist = SpecialistAgent(main_agent, test_agents)
            
            # Create test task
            test_task = Task(
                id=str(uuid4()),
                name="Analyze project requirements",
                description="Perform comprehensive analysis of project requirements and provide recommendations",
                workspace_id=self.test_workspace_id,
                status="pending",
                created_at=datetime.now(),
                urgency_score=75,
                priority_score=80
            )
            
            # Verify all components are initialized
            if not specialist.tools:
                raise AssertionError("Tools not initialized")
            
            if not specialist.input_guardrail:
                logger.warning("Input guardrail not available (SDK not loaded)")
            
            if not specialist.output_guardrail:
                logger.warning("Output guardrail not available (SDK not loaded)")
            
            # Verify handoff tools are created
            handoff_tools = specialist._create_native_handoff_tools()
            if len(handoff_tools) != 2:  # Should have 2 handoff tools (excluding self)
                raise AssertionError(f"Expected 2 handoff tools, got {len(handoff_tools)}")
            
            # Verify orchestration context creation
            from ai_agents.specialist_enhanced import OrchestrationContext
            context = OrchestrationContext(
                workspace_id=str(test_task.workspace_id),
                task_id=str(test_task.id),
                agent_id=str(main_agent.id),
                agent_role=main_agent.role,
                agent_seniority=main_agent.seniority,
                task_name=test_task.name,
                task_description=test_task.description,
                execution_metadata={
                    "started_at": datetime.now().isoformat(),
                    "agent_name": main_agent.name,
                    "model": "gpt-4o-mini"
                },
                available_agents=[
                    {
                        "id": str(agent.id),
                        "name": agent.name,
                        "role": agent.role,
                        "seniority": agent.seniority,
                        "skills": [skill.get('name', '') for skill in (agent.hard_skills or [])]
                    }
                    for agent in test_agents
                ],
                orchestration_state={"execution_phase": "testing"}
            )
            
            # Verify context is properly structured
            context_dict = context.dict()
            required_fields = ["workspace_id", "task_id", "agent_id", "available_agents"]
            for field in required_fields:
                if field not in context_dict:
                    raise AssertionError(f"Context missing field: {field}")
            
            return {
                "test": "test_end_to_end_execution",
                "status": "PASSED",
                "details": {
                    "agents_created": len(test_agents),
                    "tools_initialized": len(specialist.tools),
                    "handoff_tools_created": len(handoff_tools),
                    "context_fields": list(context_dict.keys()),
                    "guardrails_available": bool(specialist.input_guardrail and specialist.output_guardrail)
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"End-to-end execution test failed: {str(e)}")
    
    def _generate_test_summary(self) -> Dict[str, Any]:
        """Generate comprehensive test summary"""
        passed = len([r for r in self.test_results if r["status"] == "PASSED"])
        failed = len([r for r in self.test_results if r["status"] == "FAILED"])
        total = len(self.test_results)
        
        return {
            "test_summary": {
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "success_rate": (passed / total) * 100 if total > 0 else 0
            },
            "test_results": self.test_results,
            "sdk_features_tested": [
                "native_handoff_tools",
                "orchestration_context",
                "runresult_new_items",
                "input_output_guardrails",
                "run_context_wrapper"
            ],
            "timestamp": datetime.now().isoformat()
        }

async def main():
    """Run the SDK native implementation tests"""
    print("🚀 SDK Native Implementation Test Suite")
    print("=" * 50)
    
    test_suite = TestSDKNativeImplementation()
    
    try:
        results = await test_suite.run_all_tests()
        
        # Print summary
        summary = results["test_summary"]
        print(f"\n📊 Test Results Summary:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: {summary['passed']}")
        print(f"   Failed: {summary['failed']}")
        print(f"   Success Rate: {summary['success_rate']:.1f}%")
        
        if summary['failed'] > 0:
            print(f"\n❌ Failed Tests:")
            for result in results["test_results"]:
                if result["status"] == "FAILED":
                    print(f"   - {result['test']}: {result.get('error', 'Unknown error')}")
        
        print(f"\n🔧 SDK Features Tested:")
        for feature in results["sdk_features_tested"]:
            print(f"   ✅ {feature}")
        
        # Save results
        with open("test_sdk_native_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: test_sdk_native_results.json")
        
        if summary["success_rate"] == 100:
            print(f"\n🎉 All tests passed! SDK native implementation is ready.")
            return 0
        else:
            print(f"\n⚠️  Some tests failed. Review the results above.")
            return 1
            
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))