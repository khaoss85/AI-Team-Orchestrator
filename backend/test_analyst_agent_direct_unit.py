#!/usr/bin/env python3
"""
Test unitario dell'Analyst Agent - Testa solo la logica senza database
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from goal_driven_task_planner import GoalDrivenTaskPlanner
from models import WorkspaceGoal

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_analyst_agent_unit():
    """Test unitario dell'Analyst Agent senza database"""
    
    logger.info("🔍 TESTING ANALYST AGENT - UNIT TEST")
    
    # Initialize planner
    planner = GoalDrivenTaskPlanner()
    
    workspace_context = {
        "name": "Test E-commerce Business", 
        "description": "E-commerce business selling premium outdoor gear to adventure enthusiasts",
        "domain": "E-commerce/Marketing"
    }
    
    # Test cases that should trigger different Analyst Agent behaviors
    test_cases = [
        {
            "name": "Complex Goal Requiring Data",
            "goal": WorkspaceGoal(
                id="test-1",
                workspace_id="test-workspace",
                metric_type="marketing_content_creation",
                target_value=1.0,
                current_value=0.0,
                unit="email_sequence",
                description="Create a personalized welcome email sequence using real client testimonials and product highlights",
                status="active",
                priority="high"
            ),
            "expected_data_gathering": True
        },
        {
            "name": "Simple Goal Not Requiring Data",
            "goal": WorkspaceGoal(
                id="test-2",
                workspace_id="test-workspace", 
                metric_type="template_creation",
                target_value=1.0,
                current_value=0.0,
                unit="template",
                description="Write a generic welcome email template with placeholders",
                status="active",
                priority="medium"
            ),
            "expected_data_gathering": False
        },
        {
            "name": "Business Analysis Requiring Research",
            "goal": WorkspaceGoal(
                id="test-3",
                workspace_id="test-workspace",
                metric_type="business_analysis", 
                target_value=1.0,
                current_value=0.0,
                unit="report",
                description="Create a competitor analysis report for our outdoor gear market",
                status="active",
                priority="high"
            ),
            "expected_data_gathering": True
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        logger.info(f"\n🧪 TESTING: {test_case['name']}")
        logger.info(f"   Goal: {test_case['goal'].description}")
        
        try:
            # Test 1: Analyst Agent Analysis
            logger.info("🤖 Step 1: Testing Analyst Agent...")
            analysis = await planner._analyze_goal_requirements_ai(test_case['goal'], workspace_context)
            
            requires_data = analysis.get('requires_data_gathering', False)
            data_points = analysis.get('data_points_needed', [])
            
            logger.info(f"📊 ANALYST AGENT RESULT:")
            logger.info(f"   - Requires data gathering: {requires_data}")
            logger.info(f"   - Data points needed: {len(data_points)}")
            for dp in data_points:
                logger.info(f"     • {dp}")
            
            # Test 2: Task Generation
            logger.info("🛠️ Step 2: Testing Task Generation...")
            tasks = await planner._generate_ai_driven_tasks_legacy(test_case['goal'], workspace_context)
            
            logger.info(f"📝 GENERATED TASKS ({len(tasks)}):")
            
            data_gathering_tasks = []
            assembly_tasks = []
            direct_tasks = []
            
            for i, task in enumerate(tasks):
                task_name = task.get('name', 'Unknown')
                task_desc = task.get('description', '')
                logger.info(f"   {i+1}. {task_name}")
                logger.info(f"      Description: {task_desc[:120]}...")
                logger.info(f"      Priority: {task.get('priority')}")
                logger.info(f"      Contribution: {task.get('contribution_expected')}")
                
                # Classify task type
                if "Create Asset:" in task_name:
                    if any(indicator in task_name.lower() for indicator in ["list of", "document with", "testimonials", "data"]):
                        data_gathering_tasks.append(task)
                        logger.info(f"      🎯 TYPE: Data Gathering Task")
                    elif "final" in task_name.lower() and ("using" in task_desc.lower() or "gathered" in task_desc.lower()):
                        assembly_tasks.append(task)
                        logger.info(f"      🎯 TYPE: Assembly Task")
                    else:
                        direct_tasks.append(task)
                        logger.info(f"      🎯 TYPE: Direct Task")
            
            # Assessment
            test_passed = True
            assessment = {
                "test_case": test_case['name'],
                "goal_description": test_case['goal'].description,
                "analyst_agent_result": {
                    "requires_data_gathering": requires_data,
                    "data_points_count": len(data_points),
                    "data_points": data_points
                },
                "task_generation_result": {
                    "total_tasks": len(tasks),
                    "data_gathering_tasks": len(data_gathering_tasks),
                    "assembly_tasks": len(assembly_tasks),
                    "direct_tasks": len(direct_tasks)
                },
                "expected_vs_actual": {
                    "expected_data_gathering": test_case['expected_data_gathering'],
                    "actual_data_gathering": requires_data,
                    "match": requires_data == test_case['expected_data_gathering']
                }
            }
            
            # Validate results
            if test_case['expected_data_gathering']:
                # Should have data gathering tasks or assembly tasks
                if len(data_gathering_tasks) > 0 or len(assembly_tasks) > 0:
                    logger.info(f"   ✅ PASSED: Complex goal correctly generated multi-stage tasks")
                else:
                    logger.info(f"   ❌ FAILED: Complex goal should have generated data gathering or assembly tasks")
                    test_passed = False
            else:
                # Should have direct tasks only
                if len(direct_tasks) > 0 and len(data_gathering_tasks) == 0:
                    logger.info(f"   ✅ PASSED: Simple goal correctly generated direct tasks")
                else:
                    logger.info(f"   ❌ FAILED: Simple goal should have generated only direct tasks")
                    test_passed = False
            
            assessment["test_passed"] = test_passed
            results.append(assessment)
            
        except Exception as e:
            logger.error(f"❌ ERROR in test case '{test_case['name']}': {e}", exc_info=True)
            results.append({
                "test_case": test_case['name'],
                "error": str(e),
                "test_passed": False
            })
    
    # Final Summary
    passed_tests = sum(1 for r in results if r.get('test_passed', False))
    total_tests = len(results)
    
    logger.info(f"\n🏆 FINAL ANALYST AGENT TEST RESULTS:")
    logger.info(f"   ✅ Passed: {passed_tests}/{total_tests}")
    logger.info(f"   ❌ Failed: {total_tests - passed_tests}/{total_tests}")
    
    overall_success = passed_tests == total_tests
    logger.info(f"   🎯 Overall Result: {'✅ SUCCESS' if overall_success else '❌ FAILURE'}")
    
    # Detailed Analysis
    logger.info(f"\n📊 DETAILED ANALYSIS:")
    for result in results:
        if result.get('test_passed') is not None:
            match_result = result.get('expected_vs_actual', {}).get('match', False)
            logger.info(f"   • {result['test_case']}: {'✅' if result['test_passed'] else '❌'}")
            logger.info(f"     Analyst Agent prediction accuracy: {'✅' if match_result else '❌'}")
    
    # Save results
    final_results = {
        "timestamp": datetime.now().isoformat(),
        "test_type": "analyst_agent_unit_test",
        "overall_success": overall_success,
        "passed_tests": passed_tests,
        "total_tests": total_tests,
        "detailed_results": results
    }
    
    with open(f"analyst_agent_unit_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        json.dump(final_results, f, indent=2)
    
    return overall_success

if __name__ == "__main__":
    asyncio.run(test_analyst_agent_unit())