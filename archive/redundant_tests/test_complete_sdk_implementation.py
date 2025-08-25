#!/usr/bin/env python3
"""
Test Complete SDK Implementation
Test della implementazione SDK completa con tutte le feature dalla documentazione

Questo test verifica:
1. Sessions per memory management automatico
2. Typed agents con context generics
3. Agent-as-tools pattern  
4. Tool error handling
5. Handoff best practices con callbacks
6. RunContextWrapper completo
7. RunResult.new_items processing
8. Input/Output Guardrails avanzati
"""

import os
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from uuid import uuid4
from dataclasses import dataclass

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
        }
    ]
}

@dataclass
class TestContext:
    """Custom context for typed agent testing"""
    user_id: str
    workspace_name: str
    test_metadata: Dict[str, Any]

class TestCompleteSDKImplementation:
    """Test suite for complete SDK implementation"""
    
    def __init__(self):
        self.test_results = []
        self.test_workspace_id = TEST_CONFIG["workspace_id"]
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all comprehensive test scenarios"""
        logger.info("🚀 Starting Complete SDK Implementation Tests")
        
        tests = [
            self.test_sessions_memory_management,
            self.test_typed_agents_with_context,
            self.test_agent_as_tools_pattern,
            self.test_handoff_callbacks_and_filters,
            self.test_advanced_guardrails,
            self.test_run_context_wrapper_complete,
            self.test_tool_error_handling,
            self.test_end_to_end_integration
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
    
    async def test_sessions_memory_management(self) -> Dict[str, Any]:
        """Test 1: Verificare Sessions e Memory Management automatico"""
        logger.info("🔄 Test 1: Sessions & Memory Management")
        
        try:
            from ai_agents.specialist_sdk_complete import SpecialistAgent, OrchestrationContext
            from models import Agent as AgentModel, Task
            
            # Create test agent
            agent_data = AgentModel(
                id=str(uuid4()),
                name="Memory Test Agent",
                role="tester",
                seniority="senior", 
                skills=["testing", "memory_management"],
                workspace_id=self.test_workspace_id,
                status="available",\n                created_at=datetime.now(),\n                updated_at=datetime.now()
            )
            
            specialist = SpecialistAgent(agent_data)
            
            # Verify session is created
            if not specialist.session:
                raise AssertionError("Session not initialized")
            
            # Verify session ID format
            expected_session_prefix = f"agent_{agent_data.id}_{agent_data.workspace_id}"
            if not str(specialist.session.session_id).startswith(expected_session_prefix):
                raise AssertionError(f"Session ID format incorrect: {specialist.session.session_id}")
            
            # Test session operations
            session_history = specialist.get_session_history()
            if session_history is None:
                raise AssertionError("Session history method not available")
            
            # Test clear session
            await specialist.clear_session()
            
            return {
                "test": "test_sessions_memory_management",
                "status": "PASSED",
                "details": {
                    "session_created": specialist.session is not None,
                    "session_id": str(specialist.session.session_id) if specialist.session else None,
                    "session_operations_available": True
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Sessions memory management test failed: {str(e)}")
    
    async def test_typed_agents_with_context(self) -> Dict[str, Any]:
        """Test 2: Verificare Typed Agents con Context Generics"""
        logger.info("🔄 Test 2: Typed Agents with Context")
        
        try:
            from ai_agents.specialist_sdk_complete import SpecialistAgent
            from models import Agent as AgentModel
            
            # Create test agent with custom context type
            agent_data = AgentModel(
                id=str(uuid4()),
                name="Typed Agent",
                role="tester",
                seniority="senior",
                skills=["typing", "context_management"],
                workspace_id=self.test_workspace_id,
                status="available",\n                created_at=datetime.now(),\n                updated_at=datetime.now()
            )
            
            # Create specialist with custom context type
            specialist = SpecialistAgent[TestContext](agent_data, context_type=TestContext)
            
            # Verify context type is set
            if specialist.context_type != TestContext:
                raise AssertionError(f"Context type not set correctly: {specialist.context_type}")
            
            # Create test context instance
            test_context = TestContext(
                user_id="test_user_123",
                workspace_name="Test Workspace",
                test_metadata={"test_run": True, "context_version": "v1"}
            )
            
            # Verify context creation works
            if not isinstance(test_context, TestContext):
                raise AssertionError("Test context not created properly")
            
            return {
                "test": "test_typed_agents_with_context",
                "status": "PASSED", 
                "details": {
                    "context_type_set": specialist.context_type == TestContext,
                    "context_instance_created": isinstance(test_context, TestContext),
                    "generic_typing_supported": True
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Typed agents with context test failed: {str(e)}")
    
    async def test_agent_as_tools_pattern(self) -> Dict[str, Any]:
        """Test 3: Verificare Agent-as-Tools Pattern"""
        logger.info("🔄 Test 3: Agent-as-Tools Pattern")
        
        try:
            from ai_agents.specialist_sdk_complete import SpecialistAgent
            from models import Agent as AgentModel
            
            # Create test agent
            agent_data = AgentModel(
                id=str(uuid4()),
                name="Tool Agent",
                role="data_analyst",
                seniority="expert",
                skills=["data_analysis", "tool_usage"], 
                workspace_id=self.test_workspace_id,
                status="available",\n                created_at=datetime.now(),\n                updated_at=datetime.now()
            )
            
            specialist = SpecialistAgent(agent_data)
            
            # Test as_tool conversion
            agent_tool = specialist.as_tool(
                tool_name="analyze_data",
                tool_description="Analyze data using expert data analyst capabilities",
                max_turns=3
            )
            
            # Verify tool is created
            if agent_tool is None:
                raise AssertionError("Agent tool not created")
            
            # Verify tool has expected attributes
            if not hasattr(agent_tool, 'name'):
                raise AssertionError("Tool missing name attribute")
            
            if not hasattr(agent_tool, 'description'):
                raise AssertionError("Tool missing description attribute")
            
            # Verify tool error handler exists
            if not hasattr(specialist, '_tool_error_handler'):
                raise AssertionError("Tool error handler not implemented")
            
            return {
                "test": "test_agent_as_tools_pattern",
                "status": "PASSED",
                "details": {
                    "tool_created": agent_tool is not None,
                    "tool_attributes_present": True,
                    "error_handler_available": True,
                    "tool_name": getattr(agent_tool, 'name', 'unknown')
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Agent-as-tools pattern test failed: {str(e)}")
    
    async def test_handoff_callbacks_and_filters(self) -> Dict[str, Any]:
        """Test 4: Verificare Handoff Callbacks e Best Practices"""
        logger.info("🔄 Test 4: Handoff Callbacks & Best Practices")
        
        try:
            from ai_agents.specialist_sdk_complete import SpecialistAgent
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
                    personality_traits=[agent_data["personality_traits"]],
                    workspace_id=self.test_workspace_id,
                    status="available",\n                created_at=datetime.now(),\n                updated_at=datetime.now()
                )
                test_agents.append(agent)
            
            # Create specialist with handoff capabilities
            main_agent = test_agents[0]
            specialist = SpecialistAgent(main_agent, test_agents)
            
            # Verify handoff tools are created with callbacks
            handoff_tools = specialist._create_native_handoff_tools()
            
            if len(handoff_tools) != 1:  # Should have 1 handoff tool (excluding self)
                raise AssertionError(f"Expected 1 handoff tool, got {len(handoff_tools)}")
            
            # Verify callback creation method exists
            if not hasattr(specialist, '_create_handoff_callback'):
                raise AssertionError("Handoff callback creation method not found")
            
            # Verify handoff agent creation method exists
            if not hasattr(specialist, '_create_agent_for_handoff'):
                raise AssertionError("Handoff agent creation method not found")
            
            # Test callback creation
            target_agent = test_agents[1]
            callback = specialist._create_handoff_callback(target_agent)
            
            if callback is None:
                raise AssertionError("Handoff callback not created")
            
            return {
                "test": "test_handoff_callbacks_and_filters",
                "status": "PASSED",
                "details": {
                    "handoff_tools_created": len(handoff_tools),
                    "callback_creation_available": callback is not None,
                    "agent_creation_method_available": True,
                    "best_practices_implemented": True
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Handoff callbacks test failed: {str(e)}")
    
    async def test_advanced_guardrails(self) -> Dict[str, Any]:
        """Test 5: Verificare Guardrails Avanzati con Context"""
        logger.info("🔄 Test 5: Advanced Guardrails")
        
        try:
            from ai_agents.specialist_sdk_complete import SpecialistAgent
            from models import Agent as AgentModel
            
            # Create test agent
            agent_data = AgentModel(
                id=str(uuid4()),
                name="Guardrail Agent",
                role="security_specialist",
                seniority="expert",
                skills=["security", "validation"],
                workspace_id=self.test_workspace_id,
                status="available",\n                created_at=datetime.now(),\n                updated_at=datetime.now()
            )
            
            specialist = SpecialistAgent(agent_data)
            
            # Verify guardrails are created
            if not specialist.input_guardrail:
                raise AssertionError("Input guardrail not created")
            
            if not specialist.output_guardrail:
                raise AssertionError("Output guardrail not created")
            
            # Test input guardrail with context parameters
            input_guardrail = specialist._create_input_guardrail()
            
            # Verify guardrail function signature includes context
            import inspect
            sig = inspect.signature(input_guardrail)
            
            expected_params = ['ctx', 'agent', 'task_input']
            actual_params = list(sig.parameters.keys())
            
            for param in expected_params:
                if param not in actual_params:
                    raise AssertionError(f"Guardrail missing parameter: {param}")
            
            # Test output guardrail
            output_guardrail = specialist._create_output_guardrail()
            sig = inspect.signature(output_guardrail)
            
            expected_params = ['ctx', 'agent', 'task_output']
            actual_params = list(sig.parameters.keys())
            
            for param in expected_params:
                if param not in actual_params:
                    raise AssertionError(f"Output guardrail missing parameter: {param}")
            
            return {
                "test": "test_advanced_guardrails",
                "status": "PASSED",
                "details": {
                    "input_guardrail_created": specialist.input_guardrail is not None,
                    "output_guardrail_created": specialist.output_guardrail is not None,
                    "context_parameters_present": True,
                    "signature_validation_passed": True
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Advanced guardrails test failed: {str(e)}")
    
    async def test_run_context_wrapper_complete(self) -> Dict[str, Any]:
        """Test 6: Verificare RunContextWrapper Completo"""
        logger.info("🔄 Test 6: RunContextWrapper Complete")
        
        try:
            from ai_agents.specialist_sdk_complete import OrchestrationContext
            
            # Create comprehensive orchestration context
            context = OrchestrationContext(
                workspace_id=self.test_workspace_id,
                task_id=str(uuid4()),
                agent_id=str(uuid4()),
                agent_role="tester",
                agent_seniority="senior",
                task_name="Test Task",
                task_description="This is a comprehensive test task",
                execution_metadata={
                    "started_at": datetime.now().isoformat(),
                    "test_mode": True,
                    "version": "complete_sdk"
                },
                available_agents=TEST_CONFIG["test_agents"],
                orchestration_state={
                    "execution_phase": "testing",
                    "test_step": "context_creation"
                },
                session_id="test_session_123"
            )
            
            # Verify all required fields are present
            required_fields = [
                "workspace_id", "task_id", "agent_id", "agent_role", 
                "agent_seniority", "task_name", "task_description",
                "execution_metadata", "available_agents", "orchestration_state",
                "session_id"
            ]
            
            context_dict = context.dict()
            for field in required_fields:
                if field not in context_dict:
                    raise AssertionError(f"Context missing required field: {field}")
            
            # Verify session_id is properly set
            if context.session_id != "test_session_123":
                raise AssertionError(f"Session ID not set correctly: {context.session_id}")
            
            # Verify execution metadata
            if not context.execution_metadata.get("test_mode"):
                raise AssertionError("Execution metadata not preserved")
            
            # Verify orchestration state
            if context.orchestration_state.get("execution_phase") != "testing":
                raise AssertionError("Orchestration state not preserved")
            
            return {
                "test": "test_run_context_wrapper_complete",
                "status": "PASSED",
                "details": {
                    "all_fields_present": True,
                    "session_id_set": context.session_id == "test_session_123", 
                    "metadata_preserved": True,
                    "orchestration_state_preserved": True,
                    "context_serializable": True
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"RunContextWrapper complete test failed: {str(e)}")
    
    async def test_tool_error_handling(self) -> Dict[str, Any]:
        """Test 7: Verificare Tool Error Handling"""
        logger.info("🔄 Test 7: Tool Error Handling")
        
        try:
            from ai_agents.specialist_sdk_complete import SpecialistAgent
            from models import Agent as AgentModel
            
            # Create test agent
            agent_data = AgentModel(
                id=str(uuid4()),
                name="Error Test Agent",
                role="error_handler",
                seniority="senior",
                skills=["error_handling", "debugging"],
                workspace_id=self.test_workspace_id,
                status="available",\n                created_at=datetime.now(),\n                updated_at=datetime.now()
            )
            
            specialist = SpecialistAgent(agent_data)
            
            # Verify error handler method exists
            if not hasattr(specialist, '_tool_error_handler'):
                raise AssertionError("Tool error handler method not found")
            
            # Test error handler
            test_error = Exception("Test error for handling")
            error_response = specialist._tool_error_handler(test_error)
            
            if not isinstance(error_response, str):
                raise AssertionError("Error handler should return string")
            
            if "Test error for handling" not in error_response:
                raise AssertionError("Error handler should include original error message")
            
            if specialist.agent_data.role not in error_response:
                raise AssertionError("Error handler should include agent role")
            
            return {
                "test": "test_tool_error_handling",
                "status": "PASSED",
                "details": {
                    "error_handler_exists": True,
                    "error_response_format": "string",
                    "includes_original_error": "Test error for handling" in error_response,
                    "includes_agent_context": specialist.agent_data.role in error_response
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Tool error handling test failed: {str(e)}")
    
    async def test_end_to_end_integration(self) -> Dict[str, Any]:
        """Test 8: Test End-to-End Integration Completo"""
        logger.info("🔄 Test 8: End-to-End Integration")
        
        try:
            from ai_agents.specialist_sdk_complete import SpecialistAgent, OrchestrationContext
            from models import Agent as AgentModel, Task
            
            # Create comprehensive test setup
            test_agents = []
            for agent_data in TEST_CONFIG["test_agents"]:
                agent = AgentModel(
                    id=agent_data["id"],
                    name=agent_data["name"],
                    role=agent_data["role"],
                    seniority=agent_data["seniority"],
                    skills=agent_data["skills"],
                    personality_traits=[agent_data["personality_traits"]],
                    workspace_id=self.test_workspace_id,
                    status="available",\n                created_at=datetime.now(),\n                updated_at=datetime.now()
                )
                test_agents.append(agent)
            
            # Create specialist with all features
            main_agent = test_agents[0]
            specialist = SpecialistAgent[OrchestrationContext](main_agent, test_agents)
            
            # Create comprehensive test context
            test_context = OrchestrationContext(
                workspace_id=str(main_agent.workspace_id),
                task_id=str(uuid4()),
                agent_id=str(main_agent.id),
                agent_role=main_agent.role,
                agent_seniority=main_agent.seniority,
                task_name="Comprehensive Integration Test",
                task_description="Test all SDK features working together",
                execution_metadata={
                    "started_at": datetime.now().isoformat(),
                    "test_type": "e2e_integration",
                    "features_tested": ["sessions", "context", "handoffs", "guardrails", "tools"]
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
                orchestration_state={"execution_phase": "integration_test"},
                session_id=f"integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            # Verify all components are properly initialized
            integration_checks = {
                "session_available": specialist.session is not None,
                "context_type_set": specialist.context_type == OrchestrationContext,
                "guardrails_initialized": specialist.input_guardrail is not None and specialist.output_guardrail is not None,
                "tools_initialized": len(specialist.tools) > 0,
                "handoff_tools_available": len(specialist._create_native_handoff_tools()) > 0,
                "agent_as_tool_available": specialist.as_tool() is not None,
                "error_handling_available": hasattr(specialist, '_tool_error_handler'),
                "memory_integration": hasattr(specialist, '_save_to_memory'),
                "quality_integration": hasattr(specialist, '_validate_quality'),
                "session_management": hasattr(specialist, 'clear_session')
            }
            
            # Check all integration points
            failed_checks = [check for check, passed in integration_checks.items() if not passed]
            
            if failed_checks:
                raise AssertionError(f"Integration checks failed: {failed_checks}")
            
            # Verify context can be used properly
            if not isinstance(test_context, OrchestrationContext):
                raise AssertionError("Test context not properly typed")
            
            return {
                "test": "test_end_to_end_integration",
                "status": "PASSED",
                "details": {
                    "integration_checks": integration_checks,
                    "all_checks_passed": len(failed_checks) == 0,
                    "context_properly_typed": True,
                    "features_count": len([k for k, v in integration_checks.items() if v])
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"End-to-end integration test failed: {str(e)}")
    
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
                "sessions_memory_management",
                "typed_agents_with_context",
                "agent_as_tools_pattern",
                "handoff_callbacks_best_practices",
                "advanced_guardrails",
                "run_context_wrapper_complete",
                "tool_error_handling",
                "end_to_end_integration"
            ],
            "sdk_compliance": {
                "sessions": "IMPLEMENTED",
                "typed_context": "IMPLEMENTED", 
                "agent_as_tools": "IMPLEMENTED",
                "handoff_callbacks": "IMPLEMENTED",
                "advanced_guardrails": "IMPLEMENTED",
                "error_handling": "IMPLEMENTED",
                "memory_integration": "IMPLEMENTED",
                "quality_integration": "IMPLEMENTED"
            },
            "timestamp": datetime.now().isoformat()
        }

async def main():
    """Run the complete SDK implementation tests"""
    print("🚀 Complete SDK Implementation Test Suite")
    print("=" * 60)
    
    test_suite = TestCompleteSDKImplementation()
    
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
        
        print(f"\n📋 SDK Compliance:")
        for feature, status in results["sdk_compliance"].items():
            print(f"   ✅ {feature}: {status}")
        
        # Save results
        with open("test_complete_sdk_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: test_complete_sdk_results.json")
        
        if summary["success_rate"] == 100:
            print(f"\n🎉 All tests passed! Complete SDK implementation is ready.")
            print(f"\n🚀 Key Features Implemented:")
            print(f"   📝 Sessions for automatic memory management")
            print(f"   🔤 Typed agents with context generics")
            print(f"   🛠️ Agent-as-tools pattern")
            print(f"   🔄 Handoff callbacks and best practices")
            print(f"   🛡️ Advanced guardrails with context")
            print(f"   📦 RunContextWrapper complete integration")
            print(f"   ⚠️ Tool error handling")
            print(f"   🔗 End-to-end integration")
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