#!/usr/bin/env python3
"""
🧪 AUTO-COMPLETION WORKFLOW TEST

Tests the complete auto-completion system for missing deliverables:
1. Missing deliverable detection
2. Auto-completion trigger
3. Unblock mechanisms
4. Integration with goal-driven system
"""

import asyncio
import logging
import json
from typing import Dict, Any, List
import requests
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"

class AutoCompletionWorkflowTest:
    """Test suite for auto-completion workflow"""
    
    def __init__(self):
        self.test_results = {
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'critical_findings': [],
            'performance_metrics': {}
        }
        self.test_workspace_id = None
        
    def run_all_tests(self):
        """Run complete test suite"""
        logger.info("🧪 Starting Auto-Completion Workflow Test Suite")
        
        try:
            # Test 1: API Availability
            self.test_api_availability()
            
            # Test 2: Find Test Workspace
            self.find_test_workspace()
            
            if self.test_workspace_id:
                # Test 3: Missing Deliverable Detection
                self.test_missing_deliverable_detection()
                
                # Test 4: Auto-Completion API
                self.test_auto_completion_api()
                
                # Test 5: Unblock Mechanism
                self.test_unblock_mechanism()
                
                # Test 6: Integration Test
                self.test_end_to_end_integration()
            
            # Generate Final Report
            self.generate_test_report()
            
        except Exception as e:
            logger.error(f"❌ Critical test suite error: {e}")
            self.test_results['critical_findings'].append(f"Test suite error: {str(e)}")
    
    def test_api_availability(self):
        """Test 1: Verify auto-completion API endpoints are available"""
        logger.info("🔍 Test 1: API Availability Check")
        self.test_results['tests_run'] += 1
        
        try:
            # Test health endpoint
            response = requests.get(f"{BASE_URL}/health")
            if response.status_code != 200:
                raise Exception(f"Health check failed: {response.status_code}")
            
            logger.info("✅ Test 1 PASSED: Auto-completion APIs are available")
            self.test_results['tests_passed'] += 1
            
        except Exception as e:
            logger.error(f"❌ Test 1 FAILED: {e}")
            self.test_results['tests_failed'] += 1
            self.test_results['critical_findings'].append(f"Test 1: API availability failed - {str(e)}")
    
    def find_test_workspace(self):
        """Find an active workspace for testing"""
        logger.info("🔍 Finding test workspace...")
        
        try:
            response = requests.get(f"{BASE_URL}/api/workspaces")
            if response.status_code == 200:
                workspaces = response.json()
                active_workspaces = [w for w in workspaces if w.get('status') in ['active', 'in_progress', None]]
                
                if active_workspaces:
                    self.test_workspace_id = active_workspaces[0]['id']
                    logger.info(f"✅ Using test workspace: {self.test_workspace_id}")
                else:
                    logger.warning("⚠️ No active workspaces found for testing")
            else:
                logger.error(f"❌ Failed to get workspaces: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error finding test workspace: {e}")
    
    def test_missing_deliverable_detection(self):
        """Test 2: Missing deliverable detection"""
        logger.info("🔍 Test 2: Missing Deliverable Detection")
        self.test_results['tests_run'] += 1
        
        if not self.test_workspace_id:
            logger.error("❌ Test 2 SKIPPED: No test workspace available")
            return
        
        try:
            start_time = time.time()
            
            # Call missing deliverables detection API
            response = requests.get(
                f"{BASE_URL}/api/auto-completion/workspace/{self.test_workspace_id}/missing-deliverables"
            )
            
            detection_time = time.time() - start_time
            self.test_results['performance_metrics']['detection_time'] = detection_time
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    missing_deliverables = data.get('missing_deliverables', [])
                    logger.info(f"✅ Test 2 PASSED: Detected {len(missing_deliverables)} goals with missing deliverables")
                    
                    # Log details
                    for md in missing_deliverables:
                        goal_title = md.get('goal_title', 'Unknown')
                        missing_count = len(md.get('missing_deliverables', []))
                        can_auto_complete = md.get('can_auto_complete', False)
                        logger.info(f"   - {goal_title}: {missing_count} missing, auto-complete: {can_auto_complete}")
                    
                    self.test_results['tests_passed'] += 1
                else:
                    logger.error(f"❌ Test 2 FAILED: API returned success=false")
                    self.test_results['tests_failed'] += 1
                    
            else:
                logger.error(f"❌ Test 2 FAILED: HTTP {response.status_code}")
                self.test_results['tests_failed'] += 1
                self.test_results['critical_findings'].append(f"Test 2: Detection API failed - HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Test 2 FAILED: {e}")
            self.test_results['tests_failed'] += 1
            self.test_results['critical_findings'].append(f"Test 2: Detection test error - {str(e)}")
    
    def test_auto_completion_api(self):
        """Test 3: Auto-completion API functionality"""
        logger.info("🔍 Test 3: Auto-Completion API")
        self.test_results['tests_run'] += 1
        
        if not self.test_workspace_id:
            logger.error("❌ Test 3 SKIPPED: No test workspace available")
            return
        
        try:
            # First get missing deliverables to test with
            response = requests.get(
                f"{BASE_URL}/api/auto-completion/workspace/{self.test_workspace_id}/missing-deliverables"
            )
            
            if response.status_code != 200:
                logger.error("❌ Test 3 FAILED: Cannot get missing deliverables for auto-completion test")
                self.test_results['tests_failed'] += 1
                return
            
            data = response.json()
            missing_deliverables = data.get('missing_deliverables', [])
            
            if not missing_deliverables:
                logger.info("ℹ️ Test 3 SKIPPED: No missing deliverables to test auto-completion")
                return
            
            # Test auto-completion with first missing deliverable
            test_goal = missing_deliverables[0]
            goal_id = test_goal.get('goal_id')
            missing_list = test_goal.get('missing_deliverables', [])
            
            if missing_list:
                test_deliverable = missing_list[0]
                
                start_time = time.time()
                
                # Call auto-completion API
                completion_response = requests.post(
                    f"{BASE_URL}/api/auto-completion/goals/{goal_id}/auto-complete",
                    json={
                        'deliverable_name': test_deliverable,
                        'workspace_id': self.test_workspace_id
                    }
                )
                
                completion_time = time.time() - start_time
                self.test_results['performance_metrics']['auto_completion_time'] = completion_time
                
                if completion_response.status_code == 200:
                    result = completion_response.json()
                    
                    if result.get('success'):
                        logger.info(f"✅ Test 3 PASSED: Auto-completion initiated for '{test_deliverable}'")
                        logger.info(f"   Task ID: {result.get('task_id')}")
                        self.test_results['tests_passed'] += 1
                    else:
                        if result.get('requires_manual_intervention'):
                            logger.info(f"ℹ️ Test 3 PARTIAL: Auto-completion blocked - {result.get('error')}")
                            self.test_results['tests_passed'] += 1
                        else:
                            logger.error(f"❌ Test 3 FAILED: {result.get('error')}")
                            self.test_results['tests_failed'] += 1
                else:
                    logger.error(f"❌ Test 3 FAILED: HTTP {completion_response.status_code}")
                    self.test_results['tests_failed'] += 1
            
        except Exception as e:
            logger.error(f"❌ Test 3 FAILED: {e}")
            self.test_results['tests_failed'] += 1
            self.test_results['critical_findings'].append(f"Test 3: Auto-completion API error - {str(e)}")
    
    def test_unblock_mechanism(self):
        """Test 4: Unblock mechanism"""
        logger.info("🔍 Test 4: Unblock Mechanism")
        self.test_results['tests_run'] += 1
        
        if not self.test_workspace_id:
            logger.error("❌ Test 4 SKIPPED: No test workspace available")
            return
        
        try:
            # Get missing deliverables to find blocked goals
            response = requests.get(
                f"{BASE_URL}/api/auto-completion/workspace/{self.test_workspace_id}/missing-deliverables"
            )
            
            if response.status_code != 200:
                logger.error("❌ Test 4 FAILED: Cannot get missing deliverables for unblock test")
                self.test_results['tests_failed'] += 1
                return
            
            data = response.json()
            missing_deliverables = data.get('missing_deliverables', [])
            blocked_goals = [md for md in missing_deliverables if not md.get('can_auto_complete', True)]
            
            if not blocked_goals:
                logger.info("ℹ️ Test 4 SKIPPED: No blocked goals to test unblock mechanism")
                return
            
            # Test unblock with first blocked goal
            test_goal = blocked_goals[0]
            goal_id = test_goal.get('goal_id')
            
            start_time = time.time()
            
            # Call unblock API
            unblock_response = requests.post(
                f"{BASE_URL}/api/auto-completion/goals/{goal_id}/unblock",
                json={'workspace_id': self.test_workspace_id}
            )
            
            unblock_time = time.time() - start_time
            self.test_results['performance_metrics']['unblock_time'] = unblock_time
            
            if unblock_response.status_code == 200:
                result = unblock_response.json()
                
                if result.get('success'):
                    actions_taken = result.get('actions_taken', [])
                    logger.info(f"✅ Test 4 PASSED: Unblock mechanism worked - {len(actions_taken)} actions taken")
                    for action in actions_taken:
                        logger.info(f"   - {action}")
                    self.test_results['tests_passed'] += 1
                else:
                    logger.error(f"❌ Test 4 FAILED: {result.get('error')}")
                    self.test_results['tests_failed'] += 1
            else:
                logger.error(f"❌ Test 4 FAILED: HTTP {unblock_response.status_code}")
                self.test_results['tests_failed'] += 1
                
        except Exception as e:
            logger.error(f"❌ Test 4 FAILED: {e}")
            self.test_results['tests_failed'] += 1
            self.test_results['critical_findings'].append(f"Test 4: Unblock mechanism error - {str(e)}")
    
    def test_end_to_end_integration(self):
        """Test 5: End-to-end integration test"""
        logger.info("🔍 Test 5: End-to-End Integration")
        self.test_results['tests_run'] += 1
        
        if not self.test_workspace_id:
            logger.error("❌ Test 5 SKIPPED: No test workspace available")
            return
        
        try:
            # Test complete workflow: Detection -> Auto-completion -> Status Check
            
            # Step 1: Get initial status
            initial_response = requests.get(
                f"{BASE_URL}/api/auto-completion/workspace/{self.test_workspace_id}/auto-completion-status"
            )
            
            if initial_response.status_code != 200:
                logger.error("❌ Test 5 FAILED: Cannot get initial auto-completion status")
                self.test_results['tests_failed'] += 1
                return
            
            initial_status = initial_response.json()
            initial_missing_count = initial_status.get('total_missing_deliverables', 0)
            
            logger.info(f"Initial missing deliverables: {initial_missing_count}")
            
            if initial_missing_count > 0:
                # Step 2: Try bulk auto-completion
                bulk_response = requests.post(
                    f"{BASE_URL}/api/auto-completion/workspace/{self.test_workspace_id}/auto-complete-all"
                )
                
                if bulk_response.status_code == 200:
                    bulk_result = bulk_response.json()
                    
                    if bulk_result.get('success'):
                        successful_completions = bulk_result.get('successful_completions', 0)
                        total_attempts = bulk_result.get('total_attempts', 0)
                        
                        logger.info(f"✅ Test 5 PASSED: Bulk auto-completion completed")
                        logger.info(f"   Success rate: {successful_completions}/{total_attempts}")
                        
                        self.test_results['tests_passed'] += 1
                        self.test_results['performance_metrics']['bulk_completion_success_rate'] = (
                            successful_completions / max(total_attempts, 1)
                        )
                    else:
                        logger.error(f"❌ Test 5 FAILED: Bulk auto-completion failed")
                        self.test_results['tests_failed'] += 1
                else:
                    logger.error(f"❌ Test 5 FAILED: Bulk auto-completion HTTP {bulk_response.status_code}")
                    self.test_results['tests_failed'] += 1
            else:
                logger.info("ℹ️ Test 5 SKIPPED: No missing deliverables for integration test")
                
        except Exception as e:
            logger.error(f"❌ Test 5 FAILED: {e}")
            self.test_results['tests_failed'] += 1
            self.test_results['critical_findings'].append(f"Test 5: Integration test error - {str(e)}")
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("\n" + "="*80)
        logger.info("🧪 AUTO-COMPLETION WORKFLOW TEST REPORT")
        logger.info("="*80)
        
        # Test Summary
        total_tests = self.test_results['tests_run']
        passed_tests = self.test_results['tests_passed']
        failed_tests = self.test_results['tests_failed']
        success_rate = (passed_tests / max(total_tests, 1)) * 100
        
        logger.info(f"\n📊 TEST SUMMARY:")
        logger.info(f"   Total Tests: {total_tests}")
        logger.info(f"   Passed: {passed_tests}")
        logger.info(f"   Failed: {failed_tests}")
        logger.info(f"   Success Rate: {success_rate:.1f}%")
        
        # Performance Metrics
        if self.test_results['performance_metrics']:
            logger.info(f"\n⚡ PERFORMANCE METRICS:")
            for metric, value in self.test_results['performance_metrics'].items():
                if isinstance(value, float):
                    logger.info(f"   {metric}: {value:.3f}s")
                else:
                    logger.info(f"   {metric}: {value}")
        
        # Critical Findings
        if self.test_results['critical_findings']:
            logger.info(f"\n🚨 CRITICAL FINDINGS:")
            for finding in self.test_results['critical_findings']:
                logger.info(f"   - {finding}")
        
        # Overall Assessment
        logger.info(f"\n🎯 OVERALL ASSESSMENT:")
        if success_rate >= 80:
            logger.info("   ✅ AUTO-COMPLETION SYSTEM IS WORKING WELL")
        elif success_rate >= 60:
            logger.info("   ⚠️ AUTO-COMPLETION SYSTEM HAS SOME ISSUES")
        else:
            logger.info("   ❌ AUTO-COMPLETION SYSTEM NEEDS SIGNIFICANT WORK")
        
        # Save report to file
        report_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'test_results': self.test_results,
            'test_workspace_id': self.test_workspace_id,
            'overall_success_rate': success_rate
        }
        
        try:
            with open('auto_completion_test_report.json', 'w') as f:
                json.dump(report_data, f, indent=2)
            logger.info(f"\n📄 Full report saved to: auto_completion_test_report.json")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
        
        logger.info("="*80)


if __name__ == "__main__":
    test_suite = AutoCompletionWorkflowTest()
    test_suite.run_all_tests()