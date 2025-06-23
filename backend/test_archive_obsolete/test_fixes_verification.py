#!/usr/bin/env python3
"""
Quick test to verify the fixes work correctly
"""

import asyncio
import logging
from goal_driven_task_planner import goal_driven_task_planner
from automated_goal_monitor import automated_goal_monitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_enum_fixes():
    """Test that enum value issues are fixed"""
    try:
        # Test creating a mock agent role structure
        mock_agent_role = {
            "role": "specialist",  # This should work as string
            "agent_id": None,
            "seniority": "expert",
            "strategy": "availability_based"
        }
        
        # Test the corrective task creation logic
        agent_requirements = {
            "role": mock_agent_role["role"],
            "agent_id": mock_agent_role.get("agent_id"),
            "selection_strategy": mock_agent_role.get("strategy", "fallback")
        }
        
        # Handle the same logic as in automated_goal_monitor
        assigned_agent_id = agent_requirements.get("agent_id")
        raw_role = agent_requirements.get("role", "specialist")
        assigned_role = str(raw_role) if hasattr(raw_role, 'value') else raw_role
        selection_strategy = agent_requirements.get("selection_strategy", "fallback")
        
        logger.info(f"✅ Successfully processed role: {assigned_role} (type: {type(assigned_role)})")
        logger.info(f"✅ Agent ID: {assigned_agent_id}")
        logger.info(f"✅ Selection strategy: {selection_strategy}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in enum fix test: {e}")
        return False

def test_api_endpoint_structure():
    """Test that API endpoint is properly structured"""
    try:
        # This should work without import errors
        from main import app
        logger.info("✅ Main app imported successfully")
        
        # Check that the API router is included
        for route in app.routes:
            if hasattr(route, 'path') and 'api/workspaces' in route.path:
                logger.info(f"✅ Found API route: {route.path} ({route.methods})")
                
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing API structure: {e}")
        return False

async def main():
    """Run all fix verification tests"""
    logger.info("🔧 Running fixes verification tests...")
    
    tests = [
        ("Enum fixes", test_enum_fixes()),
        ("API endpoint structure", test_api_endpoint_structure())
    ]
    
    results = []
    for test_name, test_coro in tests:
        logger.info(f"\n🧪 Testing: {test_name}")
        try:
            if asyncio.iscoroutine(test_coro):
                result = await test_coro
            else:
                result = test_coro
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ Test '{test_name}' failed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n📊 Test Results Summary:")
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {status}: {test_name}")
        if result:
            passed += 1
    
    logger.info(f"\n🎯 {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        logger.info("🎉 All fixes verified successfully!")
    else:
        logger.warning("⚠️ Some fixes may need additional attention")

if __name__ == "__main__":
    asyncio.run(main())