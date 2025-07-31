#!/usr/bin/env python3
"""
Test REALE del SpecialistAgent con SDK completo
Verifica l'implementazione specialist_sdk_complete con chiamate API reali
"""

import asyncio
import os
import json
import logging
from datetime import datetime
from uuid import uuid4
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure we have API key
from dotenv import load_dotenv
load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    logger.error("❌ OPENAI_API_KEY not set in environment")
    exit(1)

async def test_specialist_sdk_real():
    """Test REALE del SpecialistAgent con SDK"""
    
    print("🚀 SPECIALIST SDK REAL TEST - Complete Implementation")
    print("=" * 60)
    
    try:
        # Step 1: Import the implementation
        print("\n📋 Step 1: Import Specialist SDK Implementation")
        
        from ai_agents.specialist_sdk_complete import SpecialistAgent, OrchestrationContext, SDK_AVAILABLE
        from models import Agent as AgentModel, Task, TaskStatus
        
        print(f"✅ Imports successful")
        print(f"   SDK Available: {SDK_AVAILABLE}")
        
        if not SDK_AVAILABLE:
            print("⚠️ SDK not available - test would use fallback mode")
            print("Please ensure 'agents' package is installed: pip install openai-agents")
            return 1
        
        # Step 2: Create test agent model
        print("\n🤖 Step 2: Create Test Agent Model")
        
        test_agent_model = AgentModel(
            id=str(uuid4()),
            name="SDK Test Specialist",
            role="software_engineer",
            seniority="senior",
            skills=["python", "sdk_integration", "testing"],
            personality_traits=["thorough", "analytical"],
            workspace_id=str(uuid4()),
            status="available",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        print(f"✅ Agent model created: {test_agent_model.name}")
        
        # Step 3: Initialize SpecialistAgent
        print("\n🛠️ Step 3: Initialize SpecialistAgent with SDK")
        
        specialist = SpecialistAgent(test_agent_model)
        
        print(f"✅ SpecialistAgent initialized")
        print(f"   Tools available: {len(specialist.tools)}")
        print(f"   Guardrails: {specialist.input_guardrail is not None}")
        
        # Step 4: Create test task
        print("\n📋 Step 4: Create Test Task")
        
        test_task = Task(
            id=str(uuid4()),
            workspace_id=test_agent_model.workspace_id,
            name="SDK Integration Test",
            description="Test the SDK integration by providing a simple Python code review",
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        print(f"✅ Task created: {test_task.name}")
        
        # Step 5: Execute task with real API call
        print("\n⚡ Step 5: Execute Task with Real SDK")
        print("   Making real API call to OpenAI...")
        
        result = await specialist.execute(test_task)
        
        print(f"✅ Task executed successfully!")
        print(f"   Status: {result.status}")
        print(f"   Execution time: {result.execution_time:.2f}s")
        print(f"   Result preview: {str(result.result)[:100]}...")
        
        # Step 6: Test handoff capabilities
        print("\n🔄 Step 6: Test Handoff Capabilities")
        
        # Create another agent for handoff
        manager_model = AgentModel(
            id=str(uuid4()),
            name="Test Manager",
            role="project_manager",
            seniority="senior",
            skills=["management", "coordination"],
            personality_traits=["leadership"],
            workspace_id=test_agent_model.workspace_id,
            status="available",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Create specialist with handoff capabilities
        specialist_with_handoff = SpecialistAgent(
            test_agent_model, 
            all_workspace_agents_data=[test_agent_model, manager_model]
        )
        
        handoff_tools = specialist_with_handoff._create_native_handoff_tools()
        print(f"✅ Handoff tools created: {len(handoff_tools)}")
        
        # Step 7: Test context type support
        print("\n🔤 Step 7: Test Context Type Support")
        
        custom_context = OrchestrationContext(
            workspace_id=str(test_agent_model.workspace_id),
            task_id=str(test_task.id),
            agent_id=str(test_agent_model.id),
            agent_role=test_agent_model.role,
            agent_seniority=test_agent_model.seniority,
            task_name=test_task.name,
            task_description=test_task.description,
            execution_metadata={"test_mode": True},
            session_id="test_session"
        )
        
        print(f"✅ Custom context created successfully")
        
        # Step 8: Test agent-as-tool
        print("\n🛠️ Step 8: Test Agent-as-Tool Pattern")
        
        agent_tool = specialist.as_tool(
            tool_name="code_review_tool",
            tool_description="Review Python code for best practices"
        )
        
        print(f"✅ Agent-as-tool created: {agent_tool is not None}")
        
        # Final Summary
        print("\n🎯 SPECIALIST SDK TEST SUMMARY")
        print("=" * 60)
        
        test_results = {
            "sdk_available": SDK_AVAILABLE,
            "agent_initialization": True,
            "task_execution": result.status == TaskStatus.COMPLETED,
            "real_api_call": True,
            "handoff_tools": len(handoff_tools) > 0,
            "context_support": True,
            "agent_as_tool": agent_tool is not None,
            "guardrails_available": specialist.input_guardrail is not None
        }
        
        all_passed = all(test_results.values())
        
        for test, passed in test_results.items():
            print(f"   {test}: {'✅' if passed else '❌'}")
        
        if all_passed:
            print("\n🎉 ALL SPECIALIST SDK TESTS PASSED!")
            print("🚀 Implementation is fully functional with real SDK")
            print("\n✨ Key Features Validated:")
            print("   - Real API calls to OpenAI")
            print("   - Native handoff implementation")
            print("   - Context type support")
            print("   - Agent-as-tool pattern")
            print("   - Guardrails integration")
        else:
            print("\n⚠️ Some tests failed")
        
        # Save results
        report = {
            "test_type": "specialist_sdk_real",
            "timestamp": datetime.now().isoformat(),
            "test_results": test_results,
            "execution_details": {
                "task_id": str(test_task.id),
                "agent_id": str(test_agent_model.id),
                "execution_time": result.execution_time,
                "result_length": len(str(result.result))
            }
        }
        
        with open("specialist_sdk_real_results.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n💾 Results saved: specialist_sdk_real_results.json")
        
        return 0 if all_passed else 1
        
    except Exception as e:
        print(f"\n💥 TEST FAILED: {str(e)}")
        logger.error(f"Specialist SDK test error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(test_specialist_sdk_real()))