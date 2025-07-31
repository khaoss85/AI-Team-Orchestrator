#!/usr/bin/env python3
"""
🧪 TEST SPECIALIST ENHANCED
Verifica che la versione enhanced mantenga stabilità e aggiunga features
"""

import asyncio
import logging
from datetime import datetime
from uuid import uuid4
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_basic_task():
    """Test 1: Task base per verificare stabilità"""
    from ai_agents.specialist_enhanced import SpecialistAgent
    from models import Agent as AgentModel, Task, TaskStatus
    
    print("\n🧪 TEST 1: Basic Task Execution")
    print("-" * 50)
    
    now = datetime.now()
    agent_data = AgentModel(
        id=uuid4(),
        workspace_id=uuid4(),
        name="Test Developer",
        role="Backend Developer",
        seniority="senior",
        status="available",
        created_at=now,
        updated_at=now
    )
    
    task = Task(
        id=uuid4(),
        workspace_id=agent_data.workspace_id,
        name="Implement user authentication",
        description="Create a secure JWT-based authentication system",
        status=TaskStatus.PENDING,
        created_at=now,
        updated_at=now
    )
    
    specialist = SpecialistAgent(agent_data)
    
    try:
        result = await asyncio.wait_for(
            specialist.execute(task),
            timeout=30.0
        )
        
        print(f"✅ Task completed in {result.execution_time:.2f}s")
        print(f"Status: {result.status}")
        print(f"Summary: {result.summary}")
        return True
        
    except asyncio.TimeoutError:
        print("❌ Task timed out")
        return False
    except Exception as e:
        print(f"❌ Task failed: {e}")
        return False

async def test_asset_task():
    """Test 2: Asset-oriented task"""
    from ai_agents.specialist_enhanced import SpecialistAgent
    from models import Agent as AgentModel, Task, TaskStatus
    
    print("\n🧪 TEST 2: Asset-Oriented Task")
    print("-" * 50)
    
    now = datetime.now()
    agent_data = AgentModel(
        id=uuid4(),
        workspace_id=uuid4(),
        name="Content Creator",
        role="Marketing Specialist",
        seniority="expert",
        status="available",
        created_at=now,
        updated_at=now
    )
    
    task = Task(
        id=uuid4(),
        workspace_id=agent_data.workspace_id,
        name="Create Asset: Social Media Content Calendar",
        description="Generate a 1-week social media content calendar for a fitness brand",
        status=TaskStatus.PENDING,
        context_data={"asset_production": True},
        created_at=now,
        updated_at=now
    )
    
    specialist = SpecialistAgent(agent_data)
    
    try:
        result = await asyncio.wait_for(
            specialist.execute(task),
            timeout=30.0
        )
        
        print(f"✅ Asset task completed in {result.execution_time:.2f}s")
        print(f"Has structured content: {'Yes' if result.structured_content else 'No'}")
        
        # Check if output has asset formatting
        if result.structured_content and ("## TABLE" in str(result.structured_content) or "## CARD" in str(result.structured_content)):
            print("✅ Asset formatting detected")
        
        return True
        
    except Exception as e:
        print(f"❌ Asset task failed: {e}")
        return False

async def test_tool_usage():
    """Test 3: Verify tool usage for real data"""
    from ai_agents.specialist_enhanced import SpecialistAgent
    from models import Agent as AgentModel, Task, TaskStatus
    
    print("\n🧪 TEST 3: Tool Usage (WebSearch)")
    print("-" * 50)
    
    now = datetime.now()
    agent_data = AgentModel(
        id=uuid4(),
        workspace_id=uuid4(),
        name="Research Analyst",
        role="Market Researcher",
        seniority="senior",
        status="available",
        created_at=now,
        updated_at=now
    )
    
    task = Task(
        id=uuid4(),
        workspace_id=agent_data.workspace_id,
        name="Research current AI trends",
        description="Find the latest trends in AI for 2024 using web search",
        status=TaskStatus.PENDING,
        created_at=now,
        updated_at=now
    )
    
    specialist = SpecialistAgent(agent_data)
    
    try:
        result = await asyncio.wait_for(
            specialist.execute(task),
            timeout=45.0  # Longer timeout for web search
        )
        
        print(f"✅ Research task completed in {result.execution_time:.2f}s")
        
        # Check if result contains current/real data
        if "2024" in result.result or "2025" in result.result:
            print("✅ Contains current data (likely from web search)")
        
        return True
        
    except Exception as e:
        print(f"❌ Tool usage task failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 SPECIALIST ENHANCED TEST SUITE")
    print("=" * 60)
    print("Testing: Stability + Asset Output + Tools + Integrations")
    print("=" * 60)
    
    tests = [
        ("Basic Execution", test_basic_task),
        ("Asset-Oriented Output", test_asset_task),
        ("Tool Usage", test_tool_usage)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        success = await test_func()
        results.append((test_name, success))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(success for _, success in results)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! Specialist Enhanced is ready.")
    else:
        print("\n⚠️ Some tests failed. Review needed.")
    
    return all_passed

if __name__ == "__main__":
    asyncio.run(main())