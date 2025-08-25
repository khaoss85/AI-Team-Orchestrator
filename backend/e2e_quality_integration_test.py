#!/usr/bin/env python3
"""
E2E Test for Quality-Deliverable Integration
Tests the complete flow from task creation to deliverable generation with AI quality assessment
"""
import os
import asyncio
import json
from supabase import create_client, Client
from dotenv import load_dotenv
import logging
from uuid import uuid4
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QualityIntegrationE2ETest:
    """E2E test for quality-deliverable integration"""
    
    def __init__(self):
        load_dotenv()
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        self.test_workspace_id = None
        self.test_goal_id = None
        self.test_results = {}
        
    async def create_test_workspace(self):
        """Use existing workspace for E2E testing"""
        logger.info("🏗️ Using existing test workspace...")
        
        # Use the existing workspace for testing
        self.test_workspace_id = "a162f894-7114-4e63-8127-17bb144db222"
        logger.info(f"✅ Using test workspace: {self.test_workspace_id}")
        return True
    
    async def create_test_goal(self):
        """Use existing goal for the workspace"""
        logger.info("🎯 Using existing test goal...")
        
        try:
            # Get existing goals from the workspace
            response = self.supabase.table('workspace_goals').select('*').eq('workspace_id', self.test_workspace_id).limit(1).execute()
            
            if response.data:
                self.test_goal_id = response.data[0]['id']
                logger.info(f"✅ Using existing goal: {self.test_goal_id}")
                return True
            else:
                logger.error("❌ No existing goals found")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to get goal: {e}")
            return False
    
    async def test_scenario_1_valid_content(self):
        """Test scenario 1: Task with valid business content"""
        logger.info("\n📝 TEST SCENARIO 1: Valid Business Content")
        
        task_data = {
            "id": str(uuid4()),
            "workspace_id": self.test_workspace_id,
            "goal_id": self.test_goal_id,
            "title": "Create onboarding guide",
            "description": "Create comprehensive customer onboarding guide",
            "status": "completed",
            "priority": "high",
            "result": {
                "content": """# Customer Onboarding Guide
                
## Welcome Process
1. Send welcome email with account details
2. Schedule kickoff call within 24 hours
3. Provide access to customer portal

## Documentation Package
- Account setup checklist
- Feature overview document
- Training schedule template
- Success metrics dashboard

## Day 1 Activities
- System access verification
- Initial configuration setup
- First training session
- Assign dedicated success manager

## Week 1 Milestones
- Complete basic training (4 sessions)
- Configure primary use cases
- Set up reporting preferences
- Schedule regular check-ins

## Success Metrics
- Time to first value: < 3 days
- Feature adoption rate: > 80% within 2 weeks
- Customer satisfaction score: > 4.5/5
- Support ticket volume: < 2 per week

This guide provides actionable steps for ensuring successful customer onboarding with clear timelines and measurable outcomes.""",
                "format": "markdown",
                "business_value": "high",
                "completeness": "100%"
            }
        }
        
        try:
            response = self.supabase.table('tasks').insert(task_data).execute()
            logger.info("✅ Valid content task created")
            
            # Test deliverable creation with this task
            from deliverable_system.unified_deliverable_engine import create_goal_specific_deliverable
            
            deliverable = await create_goal_specific_deliverable(
                self.test_workspace_id, 
                self.test_goal_id, 
                force=True
            )
            
            if deliverable:
                logger.info(f"✅ Deliverable created for valid content: {deliverable.get('id')}")
                quality_score = deliverable.get('business_value_score', 0)
                logger.info(f"📊 Final quality score: {quality_score}")
                
                self.test_results["scenario_1"] = {
                    "status": "success",
                    "deliverable_created": True,
                    "quality_score": quality_score,
                    "task_id": task_data["id"]
                }
            else:
                logger.warning("⚠️ No deliverable created for valid content")
                self.test_results["scenario_1"] = {
                    "status": "unexpected",
                    "deliverable_created": False,
                    "task_id": task_data["id"]
                }
                
        except Exception as e:
            logger.error(f"❌ Scenario 1 failed: {e}")
            self.test_results["scenario_1"] = {"status": "error", "error": str(e)}
    
    async def test_scenario_2_timeout_content(self):
        """Test scenario 2: Task with timeout (should NOT create deliverable)"""
        logger.info("\n⏰ TEST SCENARIO 2: Timeout Content (Should Fail)")
        
        task_data = {
            "id": str(uuid4()),
            "workspace_id": self.test_workspace_id,
            "goal_id": self.test_goal_id,
            "title": "Failed onboarding task",
            "description": "Task that timed out during execution",
            "status": "completed",  # Marked as completed but with timeout result
            "priority": "high",
            "result": {
                "timeout": "finalization_timeout",
                "error_type": "execution_timeout"
            }
        }
        
        try:
            response = self.supabase.table('tasks').insert(task_data).execute()
            logger.info("✅ Timeout task created")
            
            # Test deliverable creation with this task
            from deliverable_system.unified_deliverable_engine import create_goal_specific_deliverable
            
            deliverable = await create_goal_specific_deliverable(
                self.test_workspace_id, 
                self.test_goal_id, 
                force=True
            )
            
            if deliverable:
                logger.error(f"❌ UNEXPECTED: Deliverable created for timeout content: {deliverable.get('id')}")
                self.test_results["scenario_2"] = {
                    "status": "failed",
                    "deliverable_created": True,
                    "expected": False,
                    "task_id": task_data["id"]
                }
            else:
                logger.info("✅ CORRECT: No deliverable created for timeout content")
                self.test_results["scenario_2"] = {
                    "status": "success",
                    "deliverable_created": False,
                    "expected": False,
                    "task_id": task_data["id"]
                }
                
        except Exception as e:
            logger.error(f"❌ Scenario 2 failed: {e}")
            self.test_results["scenario_2"] = {"status": "error", "error": str(e)}
    
    async def test_scenario_3_low_quality_content(self):
        """Test scenario 3: Task with low quality content"""
        logger.info("\n📉 TEST SCENARIO 3: Low Quality Content")
        
        task_data = {
            "id": str(uuid4()),
            "workspace_id": self.test_workspace_id,
            "goal_id": self.test_goal_id,
            "title": "Low quality deliverable",
            "description": "Task with minimal, low-value content",
            "status": "completed",
            "priority": "high",
            "result": {
                "content": "TODO: Create guide. Need to think about it more. Maybe add some steps.",
                "format": "text",
                "notes": "Placeholder content"
            }
        }
        
        try:
            response = self.supabase.table('tasks').insert(task_data).execute()
            logger.info("✅ Low quality task created")
            
            # Test deliverable creation with this task
            from deliverable_system.unified_deliverable_engine import create_goal_specific_deliverable
            
            deliverable = await create_goal_specific_deliverable(
                self.test_workspace_id, 
                self.test_goal_id, 
                force=True
            )
            
            if deliverable:
                quality_score = deliverable.get('business_value_score', 0)
                deliverable_type = deliverable.get('type', 'unknown')
                
                if quality_score < 50 or deliverable_type == 'low_value_warning':
                    logger.info(f"✅ CORRECT: Low quality detected (score: {quality_score}, type: {deliverable_type})")
                    self.test_results["scenario_3"] = {
                        "status": "success",
                        "deliverable_created": True,
                        "quality_score": quality_score,
                        "type": deliverable_type,
                        "low_quality_detected": True,
                        "task_id": task_data["id"]
                    }
                else:
                    logger.warning(f"⚠️ UNEXPECTED: High quality score for low content (score: {quality_score})")
                    self.test_results["scenario_3"] = {
                        "status": "unexpected",
                        "deliverable_created": True,
                        "quality_score": quality_score,
                        "type": deliverable_type,
                        "low_quality_detected": False,
                        "task_id": task_data["id"]
                    }
            else:
                logger.info("✅ ALTERNATIVE: No deliverable created for low quality content")
                self.test_results["scenario_3"] = {
                    "status": "success",
                    "deliverable_created": False,
                    "task_id": task_data["id"]
                }
                
        except Exception as e:
            logger.error(f"❌ Scenario 3 failed: {e}")
            self.test_results["scenario_3"] = {"status": "error", "error": str(e)}
    
    async def cleanup_test_data(self):
        """Clean up test data"""
        logger.info("🧹 Cleaning up test data...")
        
        try:
            # Delete test tasks
            self.supabase.table('tasks').delete().eq('workspace_id', self.test_workspace_id).execute()
            
            # Delete test deliverables
            self.supabase.table('deliverables').delete().eq('workspace_id', self.test_workspace_id).execute()
            
            # Don't delete the existing goal
            # if self.test_goal_id:
            #     self.supabase.table('workspace_goals').delete().eq('id', self.test_goal_id).execute()
            
            # Don't delete the test workspace as it's not ours
            # if self.test_workspace_id:
            #     self.supabase.table('workspaces').delete().eq('id', self.test_workspace_id).execute()
            
            logger.info("✅ Test data cleaned up")
        except Exception as e:
            logger.error(f"⚠️ Cleanup warning: {e}")
    
    async def run_complete_test(self):
        """Run the complete E2E test"""
        logger.info("🧪 Starting Quality Integration E2E Test")
        logger.info("=" * 60)
        
        try:
            # Setup
            if not await self.create_test_workspace():
                return False
            
            if not await self.create_test_goal():
                return False
            
            # Run test scenarios
            await self.test_scenario_1_valid_content()
            await self.test_scenario_2_timeout_content()
            await self.test_scenario_3_low_quality_content()
            
            # Report results
            logger.info("\n" + "=" * 60)
            logger.info("📊 E2E TEST RESULTS")
            logger.info("=" * 60)
            
            total_tests = len(self.test_results)
            passed_tests = sum(1 for r in self.test_results.values() if r.get('status') == 'success')
            
            logger.info(f"📋 Total Scenarios: {total_tests}")
            logger.info(f"✅ Passed: {passed_tests}")
            logger.info(f"❌ Failed: {total_tests - passed_tests}")
            logger.info(f"🎯 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
            
            for scenario, result in self.test_results.items():
                status_emoji = "✅" if result.get('status') == 'success' else "❌"
                logger.info(f"   {status_emoji} {scenario}: {result.get('status', 'unknown')}")
            
            # Detailed analysis
            logger.info("\n📈 DETAILED ANALYSIS:")
            
            if self.test_results.get("scenario_1", {}).get("deliverable_created"):
                logger.info("   ✅ Valid content creates deliverables")
            else:
                logger.info("   ❌ Valid content should create deliverables")
                
            if not self.test_results.get("scenario_2", {}).get("deliverable_created"):
                logger.info("   ✅ Timeout content correctly rejected")
            else:
                logger.info("   ❌ Timeout content should be rejected")
                
            scenario_3 = self.test_results.get("scenario_3", {})
            if scenario_3.get("low_quality_detected") or not scenario_3.get("deliverable_created"):
                logger.info("   ✅ Low quality content properly handled")
            else:
                logger.info("   ❌ Low quality content should be handled differently")
            
            overall_success = passed_tests == total_tests
            logger.info(f"\n🏆 OVERALL RESULT: {'SUCCESS' if overall_success else 'NEEDS ATTENTION'}")
            
            return overall_success
            
        except Exception as e:
            logger.error(f"❌ E2E Test failed: {e}")
            return False
        
        finally:
            await self.cleanup_test_data()

async def main():
    """Run the E2E test"""
    test = QualityIntegrationE2ETest()
    success = await test.run_complete_test()
    
    if success:
        logger.info("🎉 E2E Quality Integration Test PASSED!")
        exit(0)
    else:
        logger.error("💥 E2E Quality Integration Test FAILED!")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())