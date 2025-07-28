#!/usr/bin/env python3
"""
Test semplificato dell'Analyst Agent - Test solo le funzioni core
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime
from uuid import uuid4

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from goal_driven_task_planner import GoalDrivenTaskPlanner

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_analyst_agent_simple():
    """Test semplificato delle funzioni core dell'Analyst Agent"""
    
    logger.info("🔍 TESTING ANALYST AGENT - SIMPLE CORE FUNCTIONS")
    
    # Initialize planner
    planner = GoalDrivenTaskPlanner()
    
    workspace_context = {
        "name": "Test E-commerce Business",
        "description": "E-commerce business selling premium outdoor gear to adventure enthusiasts",
        "domain": "E-commerce/Marketing"
    }
    
    # Create simplified goal objects (bypassing Pydantic validation)
    test_cases = [
        {
            "name": "Complex Goal Requiring Data",
            "goal": {
                "id": str(uuid4()),
                "workspace_id": str(uuid4()),
                "metric_type": "marketing_content_creation",
                "target_value": 1.0,
                "current_value": 0.0,
                "unit": "email_sequence",
                "description": "Create a personalized welcome email sequence using real client testimonials and product highlights",
                "status": "active",
                "priority": "high"
            },
            "expected_data_gathering": True
        },
        {
            "name": "Simple Template Goal",
            "goal": {
                "id": str(uuid4()),
                "workspace_id": str(uuid4()),
                "metric_type": "template_creation",
                "target_value": 1.0,
                "current_value": 0.0,
                "unit": "template",
                "description": "Write a generic welcome email template with placeholders",
                "status": "active",
                "priority": "medium"
            },
            "expected_data_gathering": False
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        logger.info(f"\n🧪 TESTING: {test_case['name']}")
        logger.info(f"   Goal: {test_case['goal']['description']}")
        
        try:
            # Test the Analyst Agent function directly
            logger.info("🤖 Testing Analyst Agent...")
            
            # Create a simple goal object that the function can handle
            class SimpleGoal:
                def __init__(self, data):
                    for key, value in data.items():
                        setattr(self, key, value)
            
            goal = SimpleGoal(test_case['goal'])
            
            # Call the Analyst Agent
            analysis = await planner._analyze_goal_requirements_ai(goal, workspace_context)
            
            requires_data = analysis.get('requires_data_gathering', False)
            data_points = analysis.get('data_points_needed', [])
            
            logger.info(f"📊 ANALYST AGENT RESULT:")
            logger.info(f"   - Requires data gathering: {requires_data}")
            logger.info(f"   - Data points needed: {len(data_points)}")
            for i, dp in enumerate(data_points):
                logger.info(f"     {i+1}. {dp}")
            
            # Validate against expectation
            expected = test_case['expected_data_gathering']
            match = requires_data == expected
            
            result = {
                "test_case": test_case['name'],
                "goal_description": test_case['goal']['description'],
                "expected_data_gathering": expected,
                "actual_data_gathering": requires_data,
                "data_points_count": len(data_points),
                "data_points": data_points,
                "prediction_accurate": match,
                "test_passed": match
            }
            
            if match:
                logger.info(f"   ✅ PASSED: Analyst Agent correctly predicted data requirement")
            else:
                logger.info(f"   ❌ FAILED: Expected {expected}, got {requires_data}")
            
            results.append(result)
            
        except Exception as e:
            logger.error(f"❌ ERROR in test case '{test_case['name']}': {e}", exc_info=True)
            results.append({
                "test_case": test_case['name'],
                "error": str(e),
                "test_passed": False
            })
    
    # Summary
    passed_tests = sum(1 for r in results if r.get('test_passed', False))
    total_tests = len(results)
    
    logger.info(f"\n🏆 ANALYST AGENT TEST SUMMARY:")
    logger.info(f"   ✅ Passed: {passed_tests}/{total_tests}")
    logger.info(f"   ❌ Failed: {total_tests - passed_tests}/{total_tests}")
    
    overall_success = passed_tests == total_tests
    
    if overall_success:
        logger.info(f"   🎯 Result: ✅ ANALYST AGENT IS WORKING CORRECTLY")
        logger.info(f"      The new architecture can distinguish between goals that need data gathering and those that don't.")
    else:
        logger.info(f"   🎯 Result: ❌ ANALYST AGENT NEEDS REFINEMENT")
    
    # Test the enhanced task generation logic briefly
    if passed_tests > 0:
        logger.info(f"\n🛠️ TESTING ENHANCED TASK GENERATION LOGIC...")
        try:
            goal = SimpleGoal(test_cases[0]['goal'])  # Use first test case
            tasks = await planner._generate_ai_driven_tasks_legacy(goal, workspace_context)
            
            logger.info(f"📝 Generated {len(tasks)} tasks using new architecture")
            for i, task in enumerate(tasks):
                logger.info(f"   {i+1}. {task.get('name', 'Unknown')}")
            
            if len(tasks) > 0:
                logger.info(f"   ✅ Task generation is working with Analyst Agent")
            else:
                logger.info(f"   ⚠️ Task generation produced no tasks")
                
        except Exception as e:
            logger.error(f"❌ Task generation test failed: {e}")
    
    # Save results
    final_results = {
        "timestamp": datetime.now().isoformat(),
        "test_type": "analyst_agent_simple_test",
        "overall_success": overall_success,
        "passed_tests": passed_tests,
        "total_tests": total_tests,
        "analyst_agent_working": overall_success,
        "detailed_results": results
    }
    
    with open(f"analyst_agent_simple_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        json.dump(final_results, f, indent=2)
    
    logger.info(f"\n🎯 FINAL ASSESSMENT:")
    logger.info(f"   Analyst Agent Architecture: {'✅ IMPLEMENTED AND WORKING' if overall_success else '❌ NEEDS DEBUGGING'}")
    
    return overall_success

if __name__ == "__main__":
    asyncio.run(test_analyst_agent_simple())