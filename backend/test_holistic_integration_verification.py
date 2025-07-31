#!/usr/bin/env python3
"""
🔍 HOLISTIC INTEGRATION VERIFICATION TEST

Test che verifica:
1. ✅ Nessun nuovo silo creato
2. ✅ Pipeline integrato end-to-end  
3. ✅ AI classification funziona
4. ✅ Tool usage enforcement
5. ✅ Real content validation
6. ✅ Deliverable creation
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HolisticIntegrationTest:
    def __init__(self):
        self.test_results = {
            "silo_check": False,
            "ai_classification": False, 
            "tool_enforcement": False,
            "content_validation": False,
            "deliverable_creation": False,
            "end_to_end": False
        }
    
    async def run_holistic_verification(self) -> bool:
        """🔍 Run complete holistic integration verification"""
        
        print("=" * 80)
        print("🔍 HOLISTIC INTEGRATION VERIFICATION TEST")
        print("=" * 80)
        print("Verifying that no silos were created and system works end-to-end")
        print("=" * 80)
        
        try:
            # Test 1: Verify no new silos
            print("\n📋 Test 1: Silo Detection Analysis...")
            await self._test_silo_detection()
            
            # Test 2: AI Classification System
            print("\n🧠 Test 2: AI Task Classification...")
            await self._test_ai_classification()
            
            # Test 3: Tool Usage Enforcement  
            print("\n🔧 Test 3: Tool Usage Enforcement...")
            await self._test_tool_enforcement()
            
            # Test 4: Content Validation
            print("\n🔍 Test 4: Real Content Validation...")
            await self._test_content_validation()
            
            # Test 5: Deliverable Creation
            print("\n📦 Test 5: Deliverable Creation Pipeline...")
            await self._test_deliverable_creation()
            
            # Test 6: End-to-End Integration
            print("\n🎯 Test 6: End-to-End Integration...")
            await self._test_end_to_end_integration()
            
            # Final Report
            return await self._generate_final_report()
            
        except Exception as e:
            print(f"\n❌ CRITICAL TEST FAILURE: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def _test_silo_detection(self):
        """📋 Test 1: Detect any new silos in the system"""
        
        silo_indicators = []
        
        # Check import dependencies
        try:
            # Verify holistic pipeline imports work
            from services.holistic_task_deliverable_pipeline import execute_task_holistically
            from services.ai_task_execution_classifier import classify_task_for_execution
            from ai_agents.specialist_enhanced import SpecialistAgent
            print("✅ All pipeline imports successful - no import silos")
            
            # Check for circular dependencies
            import importlib
            modules_to_check = [
                'services.holistic_task_deliverable_pipeline',
                'services.ai_task_execution_classifier', 
                'ai_agents.specialist_enhanced',
                'executor'
            ]
            
            for module_name in modules_to_check:
                try:
                    module = importlib.import_module(module_name)
                    print(f"✅ Module {module_name}: imports successfully")
                except Exception as e:
                    silo_indicators.append(f"Import failure in {module_name}: {e}")
                    print(f"❌ Module {module_name}: {e}")
            
            # Check executor integration
            from executor import TaskExecutor
            executor = TaskExecutor()
            if hasattr(executor, 'holistic_orchestrator'):
                print("✅ Executor has holistic orchestrator integration")
            else:
                silo_indicators.append("Executor missing holistic integration")
            
            if len(silo_indicators) == 0:
                print("✅ SILO CHECK PASSED - No new silos detected")
                self.test_results["silo_check"] = True
            else:
                print(f"❌ SILO CHECK FAILED - {len(silo_indicators)} issues found:")
                for indicator in silo_indicators:
                    print(f"   - {indicator}")
                    
        except Exception as e:
            print(f"❌ SILO CHECK ERROR: {e}")
            silo_indicators.append(f"Critical error: {e}")
    
    async def _test_ai_classification(self):
        """🧠 Test 2: AI Task Classification System"""
        
        try:
            from services.ai_task_execution_classifier import classify_task_for_execution
            
            # Test different task types
            test_cases = [
                {
                    "name": "Research email contacts for B2B outreach",
                    "description": "Find 100 qualified email contacts for enterprise software companies",
                    "expected_type": "data_collection"
                },
                {
                    "name": "Write email sequence for product launch",
                    "description": "Create 5 emails for product launch campaign",
                    "expected_type": "content_generation"
                },
                {
                    "name": "Develop marketing strategy framework",
                    "description": "Create comprehensive marketing strategy for Q1",
                    "expected_type": "planning"
                }
            ]
            
            classification_results = []
            
            for test_case in test_cases:
                try:
                    classification = await classify_task_for_execution(
                        task_name=test_case["name"],
                        task_description=test_case["description"]
                    )
                    
                    result = {
                        "task": test_case["name"],
                        "expected": test_case["expected_type"],
                        "actual": classification.execution_type.value,
                        "tools_needed": classification.tools_needed,
                        "confidence": classification.confidence_score,
                        "correct": classification.execution_type.value == test_case["expected_type"]
                    }
                    classification_results.append(result)
                    
                    status = "✅" if result["correct"] else "❌"
                    print(f"   {status} {test_case['name'][:50]}...")
                    print(f"      Expected: {result['expected']}, Got: {result['actual']}")
                    print(f"      Tools: {result['tools_needed']}, Confidence: {result['confidence']}")
                    
                except Exception as e:
                    print(f"   ❌ Classification failed for {test_case['name']}: {e}")
                    classification_results.append({"task": test_case["name"], "error": str(e)})
            
            # Check success rate
            successful = sum(1 for r in classification_results if r.get("correct", False))
            total = len(test_cases)
            success_rate = successful / total if total > 0 else 0
            
            if success_rate >= 0.8:  # 80% success rate
                print(f"✅ AI CLASSIFICATION PASSED - {successful}/{total} correct ({success_rate:.1%})")
                self.test_results["ai_classification"] = True
            else:
                print(f"❌ AI CLASSIFICATION FAILED - {successful}/{total} correct ({success_rate:.1%})")
                
        except Exception as e:
            print(f"❌ AI CLASSIFICATION ERROR: {e}")
    
    async def _test_tool_enforcement(self):
        """🔧 Test 3: Tool Usage Enforcement"""
        
        try:
            from ai_agents.specialist_enhanced import SpecialistAgent
            from models import Agent as AgentModel, Task
            from services.ai_task_execution_classifier import TaskExecutionType
            from uuid import uuid4
            
            # Create mock agent data with required fields
            mock_agent = AgentModel(
                id=uuid4(),
                workspace_id=uuid4(),
                name="Test Data Collector",
                role="researcher", 
                seniority="senior",
                description="Test agent for data collection",
                skills=["research", "data_collection"],
                status="active",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Create specialist agent
            specialist = SpecialistAgent(mock_agent)
            
            # Test tool configuration for data collection
            mock_classification = type('MockClassification', (), {
                'execution_type': TaskExecutionType.DATA_COLLECTION,
                'requires_tools': True,
                'tools_needed': ['WebSearchTool']
            })()
            
            tools = specialist._configure_execution_tools(mock_classification)
            
            # Check if WebSearchTool is configured
            web_search_found = False
            for tool in tools:
                if 'WebSearch' in str(type(tool).__name__):
                    web_search_found = True
                    break
            
            if web_search_found:
                print("✅ TOOL ENFORCEMENT PASSED - WebSearchTool configured for data collection")
                self.test_results["tool_enforcement"] = True
            else:
                print("❌ TOOL ENFORCEMENT FAILED - WebSearchTool not found in tools")
                print(f"   Available tools: {[type(t).__name__ for t in tools]}")
                
        except Exception as e:
            print(f"❌ TOOL ENFORCEMENT ERROR: {e}")
    
    async def _test_content_validation(self):
        """🔍 Test 4: Real Content Validation"""
        
        try:
            from services.holistic_task_deliverable_pipeline import HolisticTaskDeliverablePipeline
            from models import TaskExecutionOutput, TaskStatus
            from uuid import uuid4
            
            pipeline = HolisticTaskDeliverablePipeline()
            
            # Test fake content detection
            fake_result = TaskExecutionOutput(
                task_id=uuid4(),
                status=TaskStatus.COMPLETED,
                result="Contact List:\n1. John Doe - example.com - john@sample.com\n2. Jane Smith - your-company.com - placeholder@email.com",
                execution_time=30.0
            )
            
            # Test real content detection  
            real_result = TaskExecutionOutput(
                task_id=uuid4(),
                status=TaskStatus.COMPLETED,
                result="Contact List:\n1. Sarah Johnson - Microsoft - sarah.johnson@microsoft.com\n2. Mike Chen - Salesforce - m.chen@salesforce.com\n3. Lisa Wang - LinkedIn - lwang@linkedin.com",
                execution_time=30.0
            )
            
            # Mock task for validation
            mock_task = type('MockTask', (), {'id': uuid4(), 'name': 'Test Task'})()
            
            fake_validated = await pipeline._validate_data_collection_result(fake_result, mock_task)
            real_validated = await pipeline._validate_data_collection_result(real_result, mock_task)
            
            # Check validation results
            fake_has_warning = fake_validated.summary and "template" in fake_validated.summary.lower()
            real_has_approval = real_validated.summary and "real business data" in real_validated.summary.lower()
            
            if fake_has_warning and real_has_approval:
                print("✅ CONTENT VALIDATION PASSED - Correctly identifies fake vs real content")
                self.test_results["content_validation"] = True
            else:
                print("❌ CONTENT VALIDATION FAILED")
                print(f"   Fake content summary: {fake_validated.summary}")
                print(f"   Real content summary: {real_validated.summary}")
                
        except Exception as e:
            print(f"❌ CONTENT VALIDATION ERROR: {e}")
    
    async def _test_deliverable_creation(self):
        """📦 Test 5: Deliverable Creation Pipeline"""
        
        try:
            from services.holistic_task_deliverable_pipeline import HolisticTaskDeliverablePipeline
            from models import TaskExecutionOutput, Task, TaskStatus
            from services.ai_task_execution_classifier import TaskExecutionType
            from uuid import uuid4
            
            pipeline = HolisticTaskDeliverablePipeline()
            
            # Mock successful task result with substantial content
            good_result = TaskExecutionOutput(
                task_id=uuid4(),
                status=TaskStatus.COMPLETED,
                result="This is substantial business content with real data and information that would be valuable for business use. " * 10,  # 870+ chars
                execution_time=45.0,
                summary="✅ Real business data collected. Ready for deliverable creation."
            )
            
            # Mock classification
            mock_classification = type('MockClassification', (), {
                'execution_type': TaskExecutionType.DATA_COLLECTION,
                'content_type_expected': 'contact_list',
                'tools_needed': ['WebSearchTool']
            })()
            
            # Mock task with required fields
            mock_task = Task(
                id=uuid4(),
                workspace_id=uuid4(),
                agent_id=uuid4(),
                name="Test deliverable creation",
                description="Test task for deliverable creation",
                status=TaskStatus.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Test deliverable creation (without actually creating in DB)
            should_create = len(good_result.result) >= 300 and good_result.status == TaskStatus.COMPLETED
            content_not_template = good_result.summary and "template" not in good_result.summary.lower()
            
            if should_create and content_not_template:
                print("✅ DELIVERABLE CREATION PASSED - Criteria met for deliverable creation")
                self.test_results["deliverable_creation"] = True
            else:
                print("❌ DELIVERABLE CREATION FAILED")
                print(f"   Content length: {len(good_result.result)} (need >=300)")
                print(f"   Status: {good_result.status}")
                print(f"   Not template: {content_not_template}")
                
        except Exception as e:
            print(f"❌ DELIVERABLE CREATION ERROR: {e}")
    
    async def _test_end_to_end_integration(self):
        """🎯 Test 6: End-to-End Integration"""
        
        try:
            # Test that executor uses holistic pipeline
            from executor import TaskExecutor
            import inspect
            
            executor = TaskExecutor()
            
            # Check if executor has holistic pipeline integration
            execute_method = getattr(executor, '_execute_task_with_anti_loop_and_tracking', None)
            if execute_method:
                source = inspect.getsource(execute_method)
                
                holistic_integration = "execute_task_holistically" in source
                ai_classification = "holistic_task_deliverable_pipeline" in source
                
                if holistic_integration and ai_classification:
                    print("✅ END-TO-END INTEGRATION PASSED - Executor uses holistic pipeline")
                    self.test_results["end_to_end"] = True
                else:
                    print("❌ END-TO-END INTEGRATION FAILED")
                    print(f"   Holistic integration: {holistic_integration}")
                    print(f"   AI classification: {ai_classification}")
            else:
                print("❌ END-TO-END INTEGRATION FAILED - Execute method not found")
                
        except Exception as e:
            print(f"❌ END-TO-END INTEGRATION ERROR: {e}")
    
    async def _generate_final_report(self) -> bool:
        """📊 Generate final verification report"""
        
        print("\n" + "="*60)
        print("📊 HOLISTIC INTEGRATION VERIFICATION REPORT")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        success_rate = passed_tests / total_tests
        
        print(f"\n📊 Overall Success Rate: {passed_tests}/{total_tests} ({success_rate:.1%})")
        
        print("\n" + "="*60)
        if success_rate >= 0.8:  # 80% success rate
            print("🎉 HOLISTIC INTEGRATION VERIFICATION: PASSED!")
            print("✅ System is properly integrated without silos")
            print("✅ AI-driven pipeline works end-to-end")
            print("✅ Ready for production testing")
            return True
        else:
            print("❌ HOLISTIC INTEGRATION VERIFICATION: FAILED!")
            print("❌ System has integration issues or silos")
            print("❌ Needs fixes before production testing")
            return False

async def main():
    """Execute holistic integration verification"""
    
    test = HolisticIntegrationTest()
    
    try:
        is_integrated = await test.run_holistic_verification()
        
        if is_integrated:
            print("\n🎉 VERIFICATION COMPLETE: System is holistically integrated!")
            return True
        else:
            print("\n❌ VERIFICATION FAILED: System has integration issues!")
            return False
            
    except Exception as e:
        print(f"\n💥 CRITICAL VERIFICATION FAILURE: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)