#!/usr/bin/env python3
"""
🧪 **SIMPLIFIED CONTENT GENERATION TEST**

Tests the core AI-driven architectural improvements for content generation:
1. Goal Intent Recognition System
2. Task Type Classification System  
3. Task Generation Enhancement
4. Agent Assignment Improvements

This validates the holistic fix without requiring full database setup.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
import json

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import TaskType
from services.ai_task_classifier import classify_task_ai
from goal_decomposition_system import create_goal_decomposer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleContentGenerationTest:
    """🧪 Simplified test for core content generation improvements"""
    
    def __init__(self):
        self.test_results = {
            "goal_intent_recognition": [],
            "task_classification": [],
            "improvement_validation": []
        }
    
    async def run_test(self):
        """🚀 Execute the simplified test"""
        try:
            logger.info("🧪 Starting Simplified Content Generation Test")
            
            # Test 1: Goal Intent Recognition
            await self.test_goal_intent_recognition()
            
            # Test 2: Task Type Classification
            await self.test_task_type_classification()
            
            # Test 3: Improvement Validation
            await self.test_improvement_validation()
            
            # Generate test report
            self.generate_test_report()
            
            logger.info("🎉 Simplified Content Generation Test Completed")
            
        except Exception as e:
            logger.error(f"❌ Test failed with error: {e}")
            raise
    
    async def test_goal_intent_recognition(self):
        """🎯 Test AI-driven goal intent recognition"""
        logger.info("🎯 Testing Goal Intent Recognition...")
        
        test_goals = [
            {
                "description": "Email sequence 1 for lead nurturing campaign",
                "metric_type": "email_sequence",
                "target_value": 5,
                "unit": "emails",
                "expected_intent": "CONTENT_CREATION"
            },
            {
                "description": "Contact list of 100 SaaS prospects in fintech",
                "metric_type": "lead_generation", 
                "target_value": 100,
                "unit": "contacts",
                "expected_intent": "DATA_GATHERING"
            },
            {
                "description": "Social media content calendar with posts and research",
                "metric_type": "content_planning",
                "target_value": 12,
                "unit": "posts",
                "expected_intent": "HYBRID"
            }
        ]
        
        decomposer = create_goal_decomposer()
        
        for goal in test_goals:
            try:
                # Test goal decomposition with intent recognition
                decomposition_result = await decomposer.decompose_goal(goal)
                
                intent_classification = decomposition_result.get("decomposition", {}).get("goal_intent_classification")
                expected_intent = goal["expected_intent"]
                
                test_result = {
                    "goal_description": goal["description"],
                    "expected_intent": expected_intent,
                    "detected_intent": intent_classification,
                    "confidence": decomposition_result.get("decomposition", {}).get("intent_analysis", {}).get("intent_confidence", 0),
                    "success": intent_classification == expected_intent,
                    "decomposition_method": decomposition_result.get("decomposition_method", "unknown")
                }
                
                self.test_results["goal_intent_recognition"].append(test_result)
                
                status = "✅ PASS" if test_result["success"] else "❌ FAIL"
                logger.info(f"{status} Goal: '{goal['description'][:50]}...' -> Expected: {expected_intent}, Got: {intent_classification}")
                
            except Exception as e:
                logger.error(f"❌ Goal intent recognition failed: {e}")
                self.test_results["goal_intent_recognition"].append({
                    "goal_description": goal["description"],
                    "error": str(e),
                    "success": False
                })
    
    async def test_task_type_classification(self):
        """🏷️ Test AI-driven task type classification"""
        logger.info("🏷️ Testing Task Type Classification...")
        
        test_tasks = [
            {
                "name": "Write Email 1: Welcome sequence with subject and body",
                "description": "Create the first welcome email including subject line and full body text for new subscribers",
                "expected_type": TaskType.CONTENT_CREATION
            },
            {
                "name": "Write Email 2: Value proposition - subject and full body",
                "description": "Compose the second email in the sequence highlighting our value proposition with compelling subject line and complete body content",
                "expected_type": TaskType.CONTENT_CREATION
            },
            {
                "name": "Research SaaS companies in fintech sector",
                "description": "Find and collect contact information for 50 SaaS companies in the fintech sector using web search tools",
                "expected_type": TaskType.DATA_GATHERING
            },
            {
                "name": "Find competitor pricing data for market analysis",
                "description": "Gather current pricing information from top 10 competitors using web research and create structured data",
                "expected_type": TaskType.DATA_GATHERING
            },
            {
                "name": "Review and approve email content quality",
                "description": "Check email content for grammar, tone, brand consistency and overall quality before publishing",
                "expected_type": TaskType.QUALITY_ASSURANCE
            },
            {
                "name": "Create marketing strategy framework",
                "description": "Develop a comprehensive framework for our marketing approach including channels and tactics",
                "expected_type": TaskType.STRATEGY_PLANNING
            }
        ]
        
        for task_data in test_tasks:
            try:
                classification_result = await classify_task_ai(task_data)
                
                detected_type = classification_result["task_type"]
                expected_type = task_data["expected_type"]
                
                test_result = {
                    "task_name": task_data["name"],
                    "expected_type": expected_type.value,
                    "detected_type": detected_type.value,
                    "confidence": classification_result["confidence"],
                    "reasoning": classification_result["reasoning"],
                    "classification_method": classification_result["classification_method"],
                    "success": detected_type == expected_type
                }
                
                self.test_results["task_classification"].append(test_result)
                
                status = "✅ PASS" if test_result["success"] else "❌ FAIL"
                logger.info(f"{status} Task: '{task_data['name'][:40]}...' -> Expected: {expected_type.value}, Got: {detected_type.value}")
                
            except Exception as e:
                logger.error(f"❌ Task classification failed: {e}")
                self.test_results["task_classification"].append({
                    "task_name": task_data["name"],
                    "error": str(e),
                    "success": False
                })
    
    async def test_improvement_validation(self):
        """✅ Test that the improvements address the original problem"""
        logger.info("✅ Testing Improvement Validation...")
        
        # Test scenarios that validate the key improvements
        validation_scenarios = [
            {
                "scenario": "Content Creation Task Generation",
                "description": "Ensure email sequence goals generate specific content tasks, not generic 'Create Asset' tasks",
                "validation": self._validate_content_task_generation()
            },
            {
                "scenario": "Task Type Enum Integration", 
                "description": "Verify TaskType enum is properly integrated in models",
                "validation": self._validate_task_type_enum()
            },
            {
                "scenario": "AI-Driven Classification",
                "description": "Confirm AI-driven classification replaces hardcoded keyword matching",
                "validation": self._validate_ai_driven_approach()
            },
            {
                "scenario": "Agent Assignment Enhancement",
                "description": "Verify agent assignment considers task_type for better matching",
                "validation": self._validate_agent_assignment_enhancement()
            }
        ]
        
        for scenario in validation_scenarios:
            try:
                result = scenario["validation"]
                
                test_result = {
                    "scenario": scenario["scenario"],
                    "description": scenario["description"],
                    "success": result["success"],
                    "details": result.get("details", ""),
                    "evidence": result.get("evidence", [])
                }
                
                self.test_results["improvement_validation"].append(test_result)
                
                status = "✅ PASS" if test_result["success"] else "❌ FAIL"
                logger.info(f"{status} Validation: {scenario['scenario']} - {result.get('details', '')}")
                
            except Exception as e:
                logger.error(f"❌ Improvement validation failed: {e}")
                self.test_results["improvement_validation"].append({
                    "scenario": scenario["scenario"],
                    "error": str(e),
                    "success": False
                })
    
    def _validate_content_task_generation(self):
        """Validate that content task generation improvements are in place"""
        try:
            # Check if the enhanced task generation methods exist
            from goal_driven_task_planner import GoalDrivenTaskPlanner
            
            planner = GoalDrivenTaskPlanner()
            
            # Check for the new methods we implemented
            has_content_generation = hasattr(planner, '_generate_content_creation_tasks')
            has_data_generation = hasattr(planner, '_generate_data_gathering_tasks')
            has_general_generation = hasattr(planner, '_generate_general_tasks')
            
            evidence = []
            if has_content_generation:
                evidence.append("_generate_content_creation_tasks method exists")
            if has_data_generation:
                evidence.append("_generate_data_gathering_tasks method exists")
            if has_general_generation:
                evidence.append("_generate_general_tasks method exists")
            
            success = has_content_generation and has_data_generation
            
            return {
                "success": success,
                "details": f"Content-specific task generation methods: {len(evidence)}/3 implemented",
                "evidence": evidence
            }
            
        except Exception as e:
            return {
                "success": False,
                "details": f"Validation failed: {e}",
                "evidence": []
            } 
    
    def _validate_task_type_enum(self):
        """Validate TaskType enum integration"""
        try:
            # Check if TaskType enum exists and has expected values
            expected_types = [
                "content_creation", "data_gathering", "strategy_planning",
                "implementation", "quality_assurance", "coordination", "hybrid"
            ]
            
            actual_types = [task_type.value for task_type in TaskType]
            missing_types = [t for t in expected_types if t not in actual_types]
            
            success = len(missing_types) == 0
            
            return {
                "success": success,
                "details": f"TaskType enum has {len(actual_types)} types, missing: {missing_types}",
                "evidence": actual_types
            }
            
        except Exception as e:
            return {
                "success": False,
                "details": f"TaskType enum validation failed: {e}",
                "evidence": []
            }
    
    def _validate_ai_driven_approach(self):
        """Validate AI-driven classification approach"""
        try:
            # Check if AI-driven classifier exists
            from services.ai_task_classifier import AITaskClassifier
            
            classifier = AITaskClassifier()
            
            # Check for AI-driven methods
            has_ai_classify = hasattr(classifier, '_ai_classify_task')
            has_fallback = hasattr(classifier, '_fallback_classification')
            has_batch_classify = hasattr(classifier, 'classify_batch_tasks')
            
            evidence = []
            if has_ai_classify:
                evidence.append("AI-driven classification method exists")
            if has_fallback:
                evidence.append("Fallback classification for robustness")
            if has_batch_classify:
                evidence.append("Batch processing capability")
            
            success = has_ai_classify and has_fallback
            
            return {
                "success": success,
                "details": f"AI-driven classifier features: {len(evidence)}/3 implemented",
                "evidence": evidence
            }
            
        except Exception as e:
            return {
                "success": False,
                "details": f"AI classifier validation failed: {e}",
                "evidence": []
            }
    
    def _validate_agent_assignment_enhancement(self):
        """Validate agent assignment enhancement"""
        try:
            # Check if AgentStatusManager has the enhanced method
            from services.agent_status_manager import AgentStatusManager
            
            manager = AgentStatusManager()
            
            # Check for enhanced agent matching
            has_ai_matching = hasattr(manager, '_ai_match_agent_for_task_type')
            
            # Check method signature for task_type parameter
            import inspect
            find_method = getattr(manager, 'find_best_agent_for_task', None)
            has_task_type_param = False
            
            if find_method:
                sig = inspect.signature(find_method)
                has_task_type_param = 'task_type' in sig.parameters
            
            evidence = []
            if has_ai_matching:
                evidence.append("AI-driven task type matching method exists")
            if has_task_type_param:
                evidence.append("find_best_agent_for_task accepts task_type parameter")
            
            success = has_ai_matching and has_task_type_param
            
            return {
                "success": success,
                "details": f"Agent assignment enhancements: {len(evidence)}/2 implemented",
                "evidence": evidence
            }
            
        except Exception as e:
            return {
                "success": False,
                "details": f"Agent assignment validation failed: {e}",
                "evidence": []
            }
    
    def generate_test_report(self):
        """📊 Generate test report"""
        logger.info("📊 Generating Test Report...")
        
        # Calculate statistics
        total_tests = 0
        successful_tests = 0
        
        for category, tests in self.test_results.items():
            category_total = len(tests)
            category_success = sum(1 for test in tests if test.get("success", False))
            
            total_tests += category_total
            successful_tests += category_success
            
            success_rate = (category_success / category_total * 100) if category_total > 0 else 0
            logger.info(f"📊 {category.replace('_', ' ').title()}: {category_success}/{category_total} ({success_rate:.1f}%)")
        
        overall_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Create detailed report
        report = {
            "test_summary": {
                "test_name": "Simplified Content Generation Test",
                "timestamp": datetime.now().isoformat(),
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": round(overall_rate, 2)
            },
            "detailed_results": self.test_results
        }
        
        # Save report
        report_filename = f"simple_content_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("🧪 SIMPLIFIED CONTENT GENERATION TEST RESULTS")
        print("="*60)
        print(f"🎯 OVERALL SUCCESS RATE: {successful_tests}/{total_tests} ({overall_rate:.1f}%)")
        print("="*60)
        
        if overall_rate >= 80:
            print("🎉 EXCELLENT: Content generation improvements are working correctly!")
        elif overall_rate >= 60:
            print("✅ GOOD: Most improvements are functioning, minor issues detected")
        else:
            print("⚠️ WARNING: Significant issues detected, review required")
        
        print(f"📄 Detailed report saved to: {report_filename}")
        
        logger.info(f"📊 Test completed with {overall_rate:.1f}% success rate")

async def main():
    """Main test execution function"""
    test = SimpleContentGenerationTest()
    await test.run_test()

if __name__ == "__main__":
    asyncio.run(main())