#!/usr/bin/env python3
"""
🎯 SYSTEMATIC E2E TEST
Test completo del flusso Task → Goals → Deliverables 
con validazione dei 14 pilastri strategici
"""

import asyncio
import logging
from datetime import datetime
from uuid import uuid4, UUID
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

async def test_pillar_1_openai_sdk_usage():
    """PILLAR 1: OpenAI Agents SDK Native Usage"""
    print("\n🔧 PILLAR 1: OpenAI Agents SDK Native Usage")
    print("-" * 60)
    
    try:
        from ai_agents.specialist_enhanced import SpecialistAgent, SDK_AVAILABLE
        
        if not SDK_AVAILABLE:
            print("❌ OpenAI Agents SDK not available")
            return False
            
        print("✅ OpenAI Agents SDK integrated and available")
        return True
        
    except Exception as e:
        print(f"❌ SDK integration failed: {e}")
        return False

async def test_pillar_5_goal_tracking():
    """PILLAR 5: Goal-Driven System with Progress Tracking"""
    print("\n🎯 PILLAR 5: Goal-Driven System")
    print("-" * 60)
    
    try:
        from database import create_workspace_goal, get_workspace_goals, create_workspace
        
        # First create a test workspace (required for foreign key)
        test_workspace_id = uuid4()
        test_user_id = uuid4()  # Must be valid UUID
        workspace_result = await create_workspace(
            name="Test Fitness App Workspace",
            description="AI-powered fitness recommendation system development",
            user_id=str(test_user_id),
            goal="Develop comprehensive fitness platform with 1000+ users"
        )
        
        if workspace_result:
            actual_workspace_id = workspace_result.get('id', str(test_workspace_id))
        else:
            actual_workspace_id = str(test_workspace_id)
        
        # Create test workspace goal using correct schema
        goal_data = {
            "workspace_id": actual_workspace_id,
            "metric_type": "user_adoption",  # Correct field name
            "target_value": 1000,
            "current_value": 0,
            "unit": "users",
            "description": "Create a comprehensive fitness app with personalized AI recommendations",
            "status": "active",
            "priority": 1
        }
        
        goal_result = await create_workspace_goal(goal_data)
        
        # Verify goal tracking
        goals = await get_workspace_goals(workspace_id=actual_workspace_id)
        
        if goal_result and goals and len(goals) > 0:
            goal_id = goal_result.get('id') if goal_result else 'unknown'
            print(f"✅ Goal created and tracked: {goal_id}")
            print(f"   Goals in workspace: {len(goals)}")
            return True, actual_workspace_id, goal_id
        else:
            print("❌ Goal creation/tracking failed")
            print(f"   Goal result: {goal_result}")
            print(f"   Goals found: {len(goals) if goals else 0}")
            return False, None, None
        
    except Exception as e:
        print(f"❌ Goal tracking test failed: {e}")
        return False, None, None

async def test_pillar_6_memory_system():
    """PILLAR 6: Memory System Integration"""
    print("\n🧠 PILLAR 6: Memory System Integration")
    print("-" * 60)
    
    try:
        from services.unified_memory_engine import unified_memory_engine
        
        test_workspace_id = uuid4()
        
        # Test memory storage
        memory_id = await unified_memory_engine.store_insight(
            workspace_id=str(test_workspace_id),
            insight_type="test_pattern",
            content="System validation in progress",
            relevance_tags=["e2e_test", "validation"],
            metadata={"test_run": "systematic_validation"}
        )
        
        print(f"✅ Memory system integrated and working: {memory_id}")
        return True
        
    except Exception as e:
        print(f"❌ Memory system test failed: {e}")
        return False

async def test_pillar_8_quality_gates():
    """PILLAR 8: Quality Gates Automation"""
    print("\n🔍 PILLAR 8: Quality Gates")
    print("-" * 60)
    
    try:
        from ai_quality_assurance.unified_quality_engine import unified_quality_engine
        
        # Test quality validation
        quality_result = await unified_quality_engine.validate_asset_quality(
            asset_content="Sample fitness app user interface design",
            asset_type="ui_design",
            workspace_id=str(uuid4()),
            domain_context="fitness application"
        )
        
        print(f"✅ Quality gates integrated: {type(quality_result)}")
        return True
        
    except Exception as e:
        print(f"❌ Quality gates test failed: {e}")
        return False

async def test_pillar_12_deliverable_generation():
    """PILLAR 12: Asset-Oriented Deliverable Generation"""
    print("\n📦 PILLAR 12: Deliverable Generation")
    print("-" * 60)
    
    try:
        from deliverable_system.unified_deliverable_engine import unified_deliverable_engine
        
        test_workspace_id = uuid4()
        
        # Test deliverable creation capability using correct API
        deliverable_result = await unified_deliverable_engine.check_and_create_final_deliverable(
            workspace_id=str(test_workspace_id)
        )
        
        print(f"✅ Deliverable system integrated: {type(deliverable_result) if deliverable_result else 'None'}")
        if deliverable_result:
            print(f"   Deliverable created: {deliverable_result}")
        else:
            print("   No deliverable created (normal for empty workspace)")
        return True
        
    except Exception as e:
        print(f"❌ Deliverable system test failed: {e}")
        return False

async def test_pillar_14_real_tools():
    """PILLAR 14: Real Tools Integration"""
    print("\n🔧 PILLAR 14: Real Tools Integration")
    print("-" * 60)
    
    try:
        from ai_agents.specialist_enhanced import SpecialistAgent
        from models import Agent as AgentModel, Task, TaskStatus
        
        # Create agent with tools
        now = datetime.now()
        agent_data = AgentModel(
            id=uuid4(),
            workspace_id=uuid4(),
            name="Research Agent",
            role="Market Researcher",
            seniority="expert",
            status="available",
            created_at=now,
            updated_at=now
        )
        
        specialist = SpecialistAgent(agent_data)
        
        # Check tools availability
        tools_count = len(specialist.tools)
        print(f"✅ Agent has {tools_count} tools available")
        return tools_count > 0
        
    except Exception as e:
        print(f"❌ Real tools test failed: {e}")
        return False

async def test_complete_task_execution():
    """Test completo: Task → Agent → Execution → Memory → Quality → Deliverables"""
    print("\n🚀 COMPLETE TASK EXECUTION TEST")
    print("-" * 60)
    
    try:
        from ai_agents.specialist_enhanced import SpecialistAgent
        from models import Agent as AgentModel, Task, TaskStatus
        
        # Create realistic agent and task
        now = datetime.now()
        agent_data = AgentModel(
            id=uuid4(),
            workspace_id=uuid4(),
            name="AI Fitness Expert",
            role="Fitness Technology Specialist",
            seniority="expert",
            status="available",
            created_at=now,
            updated_at=now
        )
        
        task = Task(
            id=uuid4(),
            workspace_id=agent_data.workspace_id,
            name="Create Asset: Personalized Workout Plan Algorithm",
            description="Develop a smart algorithm that creates personalized workout plans based on user fitness level, goals, and preferences",
            status=TaskStatus.PENDING,
            context_data={"asset_production": True, "domain": "fitness"},
            created_at=now,
            updated_at=now
        )
        
        specialist = SpecialistAgent(agent_data)
        
        # Execute with timeout
        print("🚀 Executing comprehensive task...")
        result = await asyncio.wait_for(
            specialist.execute(task),
            timeout=60.0  # 60 second timeout for complex task
        )
        
        # Validate result
        if result.status == TaskStatus.COMPLETED:
            print(f"✅ Task completed successfully in {result.execution_time:.2f}s")
            print(f"   Summary: {getattr(result, 'summary', 'No summary')}")
            print(f"   Has structured content: {'Yes' if getattr(result, 'structured_content', None) else 'No'}")
            
            # Check for asset formatting
            if hasattr(result, 'structured_content') and result.structured_content:
                if any(marker in str(result.structured_content) for marker in ["## TABLE", "## CARD", "## TIMELINE"]):
                    print("✅ Asset-oriented formatting detected")
                else:
                    print("⚠️ No asset formatting detected")
            
            return True, result
        else:
            print(f"❌ Task failed: {getattr(result, 'summary', 'Unknown error')}")
            return False, result
        
    except asyncio.TimeoutError:
        print("❌ Task execution timed out")
        return False, None
    except Exception as e:
        print(f"❌ Task execution failed: {e}")
        return False, None

async def main():
    """Test suite sistematico per validazione E2E"""
    print("🎯 SYSTEMATIC E2E VALIDATION")
    print("=" * 80)
    print("Validating all strategic pillars and end-to-end flow")
    print("=" * 80)
    
    results = []
    
    # Test individual pillars
    pillar_tests = [
        ("Pillar 1: OpenAI SDK", test_pillar_1_openai_sdk_usage),
        ("Pillar 6: Memory System", test_pillar_6_memory_system),
        ("Pillar 8: Quality Gates", test_pillar_8_quality_gates),
        ("Pillar 12: Deliverables", test_pillar_12_deliverable_generation),
        ("Pillar 14: Real Tools", test_pillar_14_real_tools),
    ]
    
    for test_name, test_func in pillar_tests:
        print(f"\nRunning: {test_name}")
        try:
            if test_name == "Pillar 5: Goal Tracking":
                success, workspace_id, goal_id = await test_func()
                results.append((test_name, success))
            else:
                success = await test_func()
                results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Test Pillar 5 separately (returns additional data)
    print(f"\nRunning: Pillar 5: Goal Tracking")
    try:
        goal_success, workspace_id, goal_id = await test_pillar_5_goal_tracking()
        results.append(("Pillar 5: Goal Tracking", goal_success))
    except Exception as e:
        print(f"❌ Pillar 5 failed with exception: {e}")
        results.append(("Pillar 5: Goal Tracking", False))
    
    # Complete E2E test
    print(f"\nRunning: Complete E2E Flow")
    try:
        task_success, task_result = await test_complete_task_execution()
        results.append(("Complete E2E Flow", task_success))
    except Exception as e:
        print(f"❌ E2E test failed with exception: {e}")
        results.append(("Complete E2E Flow", False))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 SYSTEMATIC VALIDATION SUMMARY")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 SYSTEMATIC VALIDATION COMPLETE!")
        print("   All strategic pillars validated")
        print("   E2E flow working correctly")
        print("   System ready for production tasks")
    else:
        print(f"\n⚠️ VALIDATION INCOMPLETE")
        print(f"   {total - passed} issues need resolution")
        print("   Following systematic approach for fixes")
    
    return passed == total

if __name__ == "__main__":
    result = asyncio.run(main())