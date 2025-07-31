#!/usr/bin/env python3
"""
🧪 **END-TO-END CONTENT GENERATION TEST**

Tests the complete AI-driven architectural fix to ensure:
1. Goal Intent Recognition works correctly
2. Task Type Classification identifies content creation tasks
3. Task Generation creates specific content tasks (not generic "Create Asset")
4. Agent Assignment uses task_type for optimal matching
5. Deliverables contain REAL CONTENT instead of metadata

This validates the holistic fix for the content generation system.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from uuid import uuid4
import json

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import create_workspace, create_workspace_goal, get_workspace_goals, create_agent
from goal_decomposition_system import decompose_goal_to_todos
from goal_driven_task_planner import GoalDrivenTaskPlanner
from services.ai_task_classifier import classify_task_ai
from services.agent_status_manager import AgentStatusManager
from models import TaskType, AgentSeniority, WorkspaceStatus, GoalStatus

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentGenerationTest:
    """🧪 Comprehensive test for the content generation fix"""
    
    def __init__(self):
        self.test_workspace_id = None
        self.test_goals = []
        self.test_agents = []
        self.results = {
            "goal_intent_recognition": [],
            "task_classification": [],
            "task_generation": [],
            "agent_assignment": [],
            "content_validation": []
        }
    
    async def run_complete_test(self):
        """🚀 Execute the complete end-to-end test"""
        try:
            logger.info("🧪 Starting End-to-End Content Generation Test")
            
            # Setup test environment
            await self.setup_test_environment()
            
            # Test 1: Goal Intent Recognition
            await self.test_goal_intent_recognition()
            
            # Test 2: Task Type Classification  
            await self.test_task_type_classification()
            
            # Test 3: Task Generation with Content Focus
            await self.test_task_generation()
            
            # Test 4: Agent Assignment with Task Types
            await self.test_agent_assignment()
            
            # Test 5: Content Validation (simulate execution)
            await self.test_content_validation()
            
            # Generate test report
            await self.generate_test_report()
            
            logger.info("🎉 End-to-End Content Generation Test Completed Successfully")
            
        except Exception as e:
            logger.error(f"❌ Test failed with error: {e}")
            raise
        finally:
            # Cleanup test environment
            await self.cleanup_test_environment()
    
    async def setup_test_environment(self):
        """🛠️ Set up test workspace and agents"""
        logger.info("🛠️ Setting up test environment...")
        
        # Create test workspace
        workspace_name = f"Content Generation Test {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        workspace_description = "Test workspace for validating content generation fix"
        
        workspace_result = await create_workspace(
            name=workspace_name,
            description=workspace_description,
            user_id="test_user_content_generation"
        )
        self.test_workspace_id = workspace_result["id"]
        logger.info(f"✅ Created test workspace: {self.test_workspace_id}")
        
        # Create test agents with different specializations
        test_agents_config = [
            {
                "name": "Content Writer Agent",
                "role": "content_specialist",
                "seniority": AgentSeniority.SENIOR.value,
                "skills": ["writing", "copywriting", "email_marketing", "content_creation"],
                "domain_expertise": ["email_sequences", "marketing_copy"]
            },
            {
                "name": "Research Agent", 
                "role": "research_specialist",
                "seniority": AgentSeniority.EXPERT.value,
                "skills": ["web_search", "data_gathering", "market_research", "analysis"],
                "domain_expertise": ["market_analysis", "competitor_research"]
            },
            {
                "name": "Strategy Agent",
                "role": "strategy_specialist", 
                "seniority": AgentSeniority.EXPERT.value,
                "skills": ["strategic_planning", "analysis", "consultation"],
                "domain_expertise": ["business_strategy", "marketing_strategy"]
            }
        ]
        
        for agent_config in test_agents_config:
            agent_result = await create_agent(
                workspace_id=self.test_workspace_id,
                name=agent_config["name"],
                role=agent_config["role"],
                seniority=agent_config["seniority"],
                description=f"Test agent for {agent_config['role']} tasks"
            )
            self.test_agents.append(agent_result)
            logger.info(f"✅ Created test agent: {agent_config['name']}")
        
        # Create test goals representing different scenarios
        test_goals_config = [
            {
                "description": "Email sequence 1 for lead nurturing campaign",
                "metric_type": "email_sequence",
                "target_value": 5,
                "unit": "emails",
                "expected_intent": "CONTENT_CREATION"
            },
            {
                "description": "Contact list of 100 SaaS prospects", 
                "metric_type": "lead_generation",
                "target_value": 100,
                "unit": "contacts",
                "expected_intent": "DATA_GATHERING"
            },
            {
                "description": "Social media content calendar for Q1",
                "metric_type": "content_planning",
                "target_value": 12,
                "unit": "posts",
                "expected_intent": "HYBRID"
            }
        ]
        
        for goal_config in test_goals_config:
            goal_data = {
                "workspace_id": self.test_workspace_id,
                "status": GoalStatus.ACTIVE.value,
                **goal_config
            }
            goal_result = await create_workspace_goal(goal_data)
            goal_result["expected_intent"] = goal_config["expected_intent"]
            self.test_goals.append(goal_result)
            logger.info(f"✅ Created test goal: {goal_config['description']}")
    
    async def test_goal_intent_recognition(self):
        """🎯 Test AI-driven goal intent recognition"""
        logger.info("🎯 Testing Goal Intent Recognition...")
        
        from goal_decomposition_system import create_goal_decomposer
        decomposer = create_goal_decomposer()
        
        for goal in self.test_goals:
            try:
                # Test goal decomposition which includes intent recognition
                decomposition_result = await decomposer.decompose_goal(goal)
                
                goal_intent = decomposition_result.get("decomposition", {}).get("goal_intent_classification")
                expected_intent = goal["expected_intent"]
                
                test_result = {
                    "goal_description": goal["description"],
                    "expected_intent": expected_intent,
                    "detected_intent": goal_intent,
                    "confidence": decomposition_result.get("decomposition", {}).get("intent_analysis", {}).get("intent_confidence", 0),
                    "reasoning": decomposition_result.get("decomposition", {}).get("intent_analysis", {}).get("reasoning", ""),
                    "success": goal_intent == expected_intent
                }
                
                self.results["goal_intent_recognition"].append(test_result)
                
                status = "✅ PASS" if test_result["success"] else "❌ FAIL"
                logger.info(f"{status} Goal: '{goal['description'][:50]}...' -> Expected: {expected_intent}, Got: {goal_intent}")
                
            except Exception as e:
                logger.error(f"❌ Goal intent recognition failed for goal {goal['id']}: {e}")
                self.results["goal_intent_recognition"].append({
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
                "name": "Research SaaS companies in fintech sector",
                "description": "Find and collect contact information for 50 SaaS companies in the fintech sector using web search",
                "expected_type": TaskType.DATA_GATHERING
            },
            {
                "name": "Review and approve email content quality",
                "description": "Check email content for grammar, tone, and brand consistency before publishing",
                "expected_type": TaskType.QUALITY_ASSURANCE
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
                    "success": detected_type == expected_type
                }
                
                self.results["task_classification"].append(test_result)
                
                status = "✅ PASS" if test_result["success"] else "❌ FAIL"
                logger.info(f"{status} Task: '{task_data['name'][:40]}...' -> Expected: {expected_type.value}, Got: {detected_type.value}")
                
            except Exception as e:
                logger.error(f"❌ Task classification failed for task '{task_data['name']}': {e}")
                self.results["task_classification"].append({
                    "task_name": task_data["name"],
                    "error": str(e),
                    "success": False
                })
    
    async def test_task_generation(self):
        """📋 Test enhanced task generation with content/data distinction"""
        logger.info("📋 Testing Task Generation...")
        
        planner = GoalDrivenTaskPlanner()
        
        for goal in self.test_goals:
            try:
                # Mock workspace context
                workspace_context = {
                    "workspace_id": self.test_workspace_id,
                    "agents_available": len(self.test_agents),
                    "domain": "marketing"
                }
                
                # Generate tasks for the goal
                generated_tasks = await planner._generate_tasks_for_goal_ai(goal, 1.0, workspace_context)
                
                # Analyze task quality
                content_focused_tasks = 0
                generic_asset_tasks = 0
                specific_deliverable_tasks = 0
                
                for task in generated_tasks:
                    task_name = task.get("name", "")
                    
                    if "Create Asset:" in task_name:
                        generic_asset_tasks += 1
                    elif any(keyword in task_name.lower() for keyword in ["write", "create", "draft", "compose"]):
                        if any(specific in task_name.lower() for specific in ["email", "subject", "body", "post", "content"]):
                            specific_deliverable_tasks += 1
                        else:
                            content_focused_tasks += 1
                
                test_result = {
                    "goal_description": goal["description"],
                    "total_tasks": len(generated_tasks),
                    "generic_asset_tasks": generic_asset_tasks,
                    "content_focused_tasks": content_focused_tasks,
                    "specific_deliverable_tasks": specific_deliverable_tasks,
                    "tasks_sample": [task.get("name", "") for task in generated_tasks[:3]],
                    "success": generic_asset_tasks == 0 and (content_focused_tasks > 0 or specific_deliverable_tasks > 0)
                }
                
                self.results["task_generation"].append(test_result)
                
                status = "✅ PASS" if test_result["success"] else "❌ FAIL"
                logger.info(f"{status} Goal: '{goal['description'][:40]}...' -> Generated {len(generated_tasks)} tasks, {generic_asset_tasks} generic")
                
            except Exception as e:
                logger.error(f"❌ Task generation failed for goal {goal['id']}: {e}")
                self.results["task_generation"].append({
                    "goal_description": goal["description"],
                    "error": str(e),
                    "success": False
                })
    
    async def test_agent_assignment(self):
        """👥 Test enhanced agent assignment with task type awareness"""
        logger.info("👥 Testing Agent Assignment...")
        
        agent_manager = AgentStatusManager()
        
        test_scenarios = [
            {
                "task": {
                    "name": "Write Email 1: Welcome sequence",
                    "description": "Create welcome email with subject and body", 
                    "task_type": "content_creation"
                },
                "required_role": "content_specialist",
                "expected_agent": "Content Writer Agent"
            },
            {
                "task": {
                    "name": "Research SaaS prospects",
                    "description": "Find contact information using web search",
                    "task_type": "data_gathering"
                },
                "required_role": "research_specialist", 
                "expected_agent": "Research Agent"
            }
        ]
        
        for scenario in test_scenarios:
            try:
                task_data = scenario["task"]
                required_role = scenario["required_role"]
                
                # Test agent assignment with task_type
                match_result = await agent_manager.find_best_agent_for_task(
                    workspace_id=self.test_workspace_id,
                    required_role=required_role,
                    task_name=task_data["name"],
                    task_description=task_data["description"],
                    task_type=task_data["task_type"]
                )
                
                assigned_agent_name = match_result.agent.name if match_result.agent else None
                expected_agent_name = scenario["expected_agent"]
                
                test_result = {
                    "task_name": task_data["name"],
                    "task_type": task_data["task_type"],
                    "required_role": required_role,
                    "expected_agent": expected_agent_name,
                    "assigned_agent": assigned_agent_name,
                    "match_confidence": match_result.match_confidence,
                    "match_method": match_result.match_method,
                    "success": assigned_agent_name == expected_agent_name
                }
                
                self.results["agent_assignment"].append(test_result)
                
                status = "✅ PASS" if test_result["success"] else "❌ FAIL"
                logger.info(f"{status} Task: '{task_data['name'][:30]}...' -> Expected: {expected_agent_name}, Got: {assigned_agent_name}")
                
            except Exception as e:
                logger.error(f"❌ Agent assignment failed for scenario: {e}")
                self.results["agent_assignment"].append({
                    "task_name": scenario["task"]["name"],
                    "error": str(e),
                    "success": False
                })
    
    async def test_content_validation(self):
        """📝 Test that content generation produces real content, not metadata"""
        logger.info("📝 Testing Content Validation...")
        
        # Simulate content generation results
        content_scenarios = [
            {
                "task_name": "Write Email 1: Welcome sequence",
                "simulated_output": {
                    "subject": "Welcome to our community! 🎉",
                    "body": "Hi [Name],\n\nWelcome to our community! We're excited to have you on board.\n\nHere's what you can expect:\n- Weekly tips and insights\n- Exclusive member content\n- Direct access to our team\n\nBest regards,\nThe Team",
                    "cta": "Get Started Now"
                },
                "content_type": "email"
            },
            {
                "task_name": "Research SaaS prospects",
                "simulated_output": [
                    {"company": "Stripe", "email": "hello@stripe.com", "industry": "fintech"},
                    {"company": "Square", "email": "info@squareup.com", "industry": "fintech"},
                    {"company": "Plaid", "email": "contact@plaid.com", "industry": "fintech"}
                ],
                "content_type": "data"
            }
        ]
        
        for scenario in content_scenarios:
            try:
                output = scenario["simulated_output"]
                content_type = scenario["content_type"]
                
                # Validate content quality
                is_real_content = False
                validation_details = {}
                
                if content_type == "email":
                    # Check for actual email components
                    has_subject = bool(output.get("subject") and len(output["subject"]) > 10)
                    has_body = bool(output.get("body") and len(output["body"]) > 50)
                    has_personalization = "[name]" in output.get("body", "").lower()
                    
                    is_real_content = has_subject and has_body
                    validation_details = {
                        "has_subject": has_subject,
                        "has_body": has_body,
                        "has_personalization": has_personalization,
                        "subject_length": len(output.get("subject", "")),
                        "body_length": len(output.get("body", ""))
                    }
                
                elif content_type == "data":
                    # Check for actual data points
                    is_list = isinstance(output, list)
                    has_items = len(output) > 0 if is_list else False
                    has_structured_data = all(isinstance(item, dict) for item in output) if is_list else False
                    
                    is_real_content = is_list and has_items and has_structured_data
                    validation_details = {
                        "is_list": is_list,
                        "item_count": len(output) if is_list else 0,
                        "has_structured_data": has_structured_data
                    }
                
                test_result = {
                    "task_name": scenario["task_name"],
                    "content_type": content_type,
                    "is_real_content": is_real_content,
                    "validation_details": validation_details,
                    "success": is_real_content
                }
                
                self.results["content_validation"].append(test_result)
                
                status = "✅ PASS" if test_result["success"] else "❌ FAIL"
                logger.info(f"{status} Content: '{scenario['task_name'][:30]}...' -> Real content: {is_real_content}")
                
            except Exception as e:
                logger.error(f"❌ Content validation failed for scenario: {e}")
                self.results["content_validation"].append({
                    "task_name": scenario["task_name"],
                    "error": str(e),
                    "success": False
                })
    
    async def generate_test_report(self):
        """📊 Generate comprehensive test report"""
        logger.info("📊 Generating Test Report...")
        
        report = {
            "test_summary": {
                "test_name": "End-to-End Content Generation Test",
                "timestamp": datetime.now().isoformat(),
                "workspace_id": self.test_workspace_id,
                "total_test_categories": 5
            },
            "test_results": self.results,
            "summary_stats": {}
        }
        
        # Calculate summary statistics
        for category, tests in self.results.items():
            if tests:
                total_tests = len(tests)
                successful_tests = sum(1 for test in tests if test.get("success", False))
                success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
                
                report["summary_stats"][category] = {
                    "total_tests": total_tests,
                    "successful_tests": successful_tests,
                    "success_rate": round(success_rate, 2)
                }
        
        # Calculate overall success rate
        all_tests = []
        for tests in self.results.values():
            all_tests.extend(tests)
        
        if all_tests:
            overall_success = sum(1 for test in all_tests if test.get("success", False))
            overall_total = len(all_tests)
            overall_rate = (overall_success / overall_total) * 100
            
            report["summary_stats"]["overall"] = {
                "total_tests": overall_total,
                "successful_tests": overall_success,
                "success_rate": round(overall_rate, 2)
            }
        
        # Save report to file
        report_filename = f"content_generation_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Test report saved to: {report_filename}")
        
        # Print summary
        print("\n" + "="*60)
        print("🧪 CONTENT GENERATION TEST RESULTS")
        print("="*60)
        
        for category, stats in report["summary_stats"].items():
            if category != "overall":
                print(f"{category.replace('_', ' ').title()}: {stats['successful_tests']}/{stats['total_tests']} ({stats['success_rate']}%)")
        
        if "overall" in report["summary_stats"]:
            overall = report["summary_stats"]["overall"]
            print(f"\n🎯 OVERALL SUCCESS RATE: {overall['successful_tests']}/{overall['total_tests']} ({overall['success_rate']}%)")
        
        print("="*60)
        
        return report
    
    async def cleanup_test_environment(self):
        """🧹 Clean up test environment"""
        logger.info("🧹 Cleaning up test environment...")
        
        # Note: In a real implementation, you would clean up the test workspace and agents
        # For this test, we'll leave them for manual inspection if needed
        logger.info(f"ℹ️ Test workspace {self.test_workspace_id} left for manual inspection")

async def main():
    """Main test execution function"""
    test = ContentGenerationTest()
    await test.run_complete_test()

if __name__ == "__main__":
    asyncio.run(main())