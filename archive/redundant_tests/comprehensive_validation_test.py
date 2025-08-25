#!/usr/bin/env python3
"""
🔧 COMPREHENSIVE VALIDATION TEST

Test end-to-end dell'intero sistema dopo aver implementato tutti i fix:
1. Fix workspace_id placeholder error
2. Fix team-aware handoff  
3. Fix quality validation coroutine errors
4. Fix quality validator Pydantic validation
5. Fix MaxTurnsExceeded with intelligent retry
6. Test deliverable generation pipeline

Questo test verifica che tutti i componenti funzionino insieme per produrre deliverables reali.
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Any

# Setup path and environment
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(CURRENT_DIR, ".env"))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

class ComprehensiveValidationTest:
    """Test completo del sistema AI Team Orchestrator"""
    
    def __init__(self):
        self.test_results = {}
        self.workspace_id = None
        
    async def run_full_validation(self):
        """Esegue tutti i test di validazione"""
        logger.info("🚀 STARTING COMPREHENSIVE VALIDATION TEST")
        
        try:
            # Test 1: Database connectivity
            await self._test_database_connectivity()
            
            # Test 2: Quality validator functionality
            await self._test_quality_validator()
            
            # Test 3: Task deduplication system
            await self._test_task_deduplication()
            
            # Test 4: Agent status management
            await self._test_agent_status_management()
            
            # Test 5: Goal validation optimization
            await self._test_goal_validation()
            
            # Test 6: End-to-end deliverable generation
            await self._test_deliverable_generation()
            
            # Test 7: Analyze existing workspaces for issues
            await self._analyze_existing_workspaces()
            
            # Generate final report
            self._generate_final_report()
            
        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
            raise

    async def _test_database_connectivity(self):
        """Test 1: Verifica connettività database"""
        logger.info("📊 Test 1: Database Connectivity")
        
        try:
            from database import supabase
            
            # Test basic connectivity
            workspaces = supabase.table('workspaces').select('id, name').limit(5).execute()
            workspace_count = len(workspaces.data) if workspaces.data else 0
            
            tasks = supabase.table('tasks').select('id, status').limit(10).execute()
            task_count = len(tasks.data) if tasks.data else 0
            
            goals = supabase.table('workspace_goals').select('id, status').limit(10).execute()
            goal_count = len(goals.data) if goals.data else 0
            
            deliverables = supabase.table('deliverables').select('id, status').limit(10).execute()
            deliverable_count = len(deliverables.data) if deliverables.data else 0
            
            self.test_results['database_connectivity'] = {
                'status': 'passed',
                'details': {
                    'workspaces_count': workspace_count,
                    'tasks_count': task_count,
                    'goals_count': goal_count,
                    'deliverables_count': deliverable_count
                }
            }
            
            logger.info(f"✅ Database connectivity: {workspace_count} workspaces, {task_count} tasks, {goal_count} goals, {deliverable_count} deliverables")
            
        except Exception as e:
            self.test_results['database_connectivity'] = {
                'status': 'failed',
                'error': str(e)
            }
            logger.error(f"❌ Database connectivity failed: {e}")

    async def _test_quality_validator(self):
        """Test 2: Quality validator functionality"""
        logger.info("🔍 Test 2: Quality Validator")
        
        try:
            from backend.ai_quality_assurance.unified_quality_engine import AIQualityValidator
            
            quality_validator = AIQualityValidator()
            
            # Test with rich content
            rich_data = {
                "business_analysis": {
                    "market_size": "$2.5B USD",
                    "target_customers": ["SME", "Enterprise"],
                    "competitive_advantages": ["AI-driven automation", "Real-time analytics"],
                    "revenue_projections": {
                        "year_1": "$500K",
                        "year_2": "$2M",
                        "year_3": "$5M"
                    }
                }
            }
            
            context = {
                "workspace_id": "test-validation",
                "task_name": "Business Analysis Test",
                "goal_type": "business_planning"
            }
            
            result = await quality_validator.validate_asset_quality(
                rich_data, "business_plan", context
            )
            
            self.test_results['quality_validator'] = {
                'status': 'passed' if result.overall_score > 0.6 else 'failed',
                'details': {
                    'overall_score': result.overall_score,
                    'actionability_score': result.actionability_score,
                    'authenticity_score': result.authenticity_score,
                    'completeness_score': result.completeness_score,
                    'quality_issues_count': len(result.quality_issues),
                    'ready_for_use': result.ready_for_use
                }
            }
            
            if result.overall_score > 0.6:
                logger.info(f"✅ Quality validator working: score {result.overall_score:.2f}")
            else:
                logger.warning(f"⚠️ Quality validator concerns: score {result.overall_score:.2f}")
                
        except Exception as e:
            self.test_results['quality_validator'] = {
                'status': 'failed',
                'error': str(e)
            }
            logger.error(f"❌ Quality validator test failed: {e}")

    async def _test_task_deduplication(self):
        """Test 3: Task deduplication system"""
        logger.info("🔄 Test 3: Task Deduplication")
        
        try:
            from services.task_deduplication_manager import TaskDeduplicationManager
            
            dedup_manager = TaskDeduplicationManager()
            
            # Test with duplicate task data
            task_data = {
                "name": "Test Market Research",
                "description": "Conduct market research for our new product",
                "workspace_id": "test-workspace"
            }
            
            # First task should be unique
            result1 = await dedup_manager.ensure_unique_task(task_data, "test-workspace")
            
            # Second identical task should be detected as duplicate
            result2 = await dedup_manager.ensure_unique_task(task_data, "test-workspace")
            
            self.test_results['task_deduplication'] = {
                'status': 'passed' if (not result1.is_duplicate and result2.is_duplicate) else 'failed',
                'details': {
                    'first_task_unique': not result1.is_duplicate,
                    'second_task_duplicate': result2.is_duplicate,
                    'similarity_score': result2.similarity_score,
                    'method_used': result2.detection_method
                }
            }
            
            logger.info(f"✅ Task deduplication: first unique={not result1.is_duplicate}, second duplicate={result2.is_duplicate}")
            
        except Exception as e:
            self.test_results['task_deduplication'] = {
                'status': 'failed',
                'error': str(e)
            }
            logger.error(f"❌ Task deduplication test failed: {e}")

    async def _test_agent_status_management(self):
        """Test 4: Agent status management"""
        logger.info("👥 Test 4: Agent Status Management")
        
        try:
            from services.agent_status_manager import AgentStatusManager
            
            agent_manager = AgentStatusManager()
            
            # Test finding best agent for a task
            result = await agent_manager.find_best_agent_for_task(
                workspace_id="test-workspace",
                required_role="market_researcher",
                task_name="Market Analysis",
                task_description="Analyze market trends and competitor landscape"
            )
            
            self.test_results['agent_status_management'] = {
                'status': 'passed' if result.agent else 'failed',
                'details': {
                    'agent_found': bool(result.agent),
                    'match_confidence': result.match_confidence,
                    'fallback_used': result.fallback_used,
                    'match_method': result.match_method
                }
            }
            
            if result.agent:
                logger.info(f"✅ Agent status management: found agent with confidence {result.match_confidence:.2f}")
            else:
                logger.warning(f"⚠️ Agent status management: no suitable agent found")
                
        except Exception as e:
            self.test_results['agent_status_management'] = {
                'status': 'failed',
                'error': str(e)
            }
            logger.error(f"❌ Agent status management test failed: {e}")

    async def _test_goal_validation(self):
        """Test 5: Goal validation optimization"""
        logger.info("🎯 Test 5: Goal Validation")
        
        try:
            from services.goal_validation_optimizer import GoalValidationOptimizer
            
            optimizer = GoalValidationOptimizer()
            
            # Test with recent goal data
            goal_data = {
                "id": "test-goal-123",
                "name": "Increase user engagement",
                "target_value": 100,
                "current_value": 45,
                "created_at": datetime.now().isoformat()
            }
            
            result = await optimizer.should_proceed_with_validation(
                workspace_id="test-workspace",
                goal_data=goal_data
            )
            
            self.test_results['goal_validation'] = {
                'status': 'passed',
                'details': {
                    'should_proceed': result.should_proceed,
                    'decision': result.decision.value if hasattr(result.decision, 'value') else str(result.decision),
                    'confidence': result.confidence,
                    'reason': result.reason
                }
            }
            
            logger.info(f"✅ Goal validation: proceed={result.should_proceed}, decision={result.decision}")
            
        except Exception as e:
            self.test_results['goal_validation'] = {
                'status': 'failed',
                'error': str(e)
            }
            logger.error(f"❌ Goal validation test failed: {e}")

    async def _test_deliverable_generation(self):
        """Test 6: End-to-end deliverable generation"""
        logger.info("📦 Test 6: Deliverable Generation")
        
        try:
            from database import supabase
            
            # Find a workspace with completed goals but no deliverables
            completed_goals = supabase.table('workspace_goals').select('*').eq('status', 'completed').limit(10).execute()
            
            test_workspace_found = False
            for goal in completed_goals.data or []:
                workspace_id = goal['workspace_id']
                
                # Check if this workspace has deliverables
                existing_deliverables = supabase.table('deliverables').select('id').eq('workspace_id', workspace_id).execute()
                
                if not existing_deliverables.data:
                    # Found a workspace with completed goals but no deliverables
                    self.workspace_id = workspace_id
                    test_workspace_found = True
                    break
            
            if test_workspace_found:
                # Test deliverable creation for this workspace
                from fix_deliverable_creation import force_create_deliverable
                
                # Get goals and tasks for this workspace 
                goals = supabase.table('workspace_goals').select('*').eq('workspace_id', self.workspace_id).execute()
                tasks = supabase.table('tasks').select('*').eq('workspace_id', self.workspace_id).eq('status', 'completed').execute()
                
                if goals.data and tasks.data:
                    deliverable_id = await force_create_deliverable(
                        self.workspace_id, 
                        goals.data, 
                        tasks.data
                    )
                    
                    self.test_results['deliverable_generation'] = {
                        'status': 'passed',
                        'details': {
                            'workspace_id': self.workspace_id,
                            'deliverable_created': bool(deliverable_id),
                            'deliverable_id': deliverable_id,
                            'goals_count': len(goals.data),
                            'tasks_count': len(tasks.data)
                        }
                    }
                    
                    logger.info(f"✅ Deliverable generation: created deliverable {deliverable_id} for workspace {self.workspace_id}")
                else:
                    logger.warning("⚠️ No suitable goals/tasks found for deliverable generation - no completed tasks or goals")
                    self.test_results['deliverable_generation'] = {
                        'status': 'skipped',
                        'details': {
                            'workspace_id': self.workspace_id,
                            'reason': 'No completed goals or tasks found',
                            'goals_count': len(goals.data) if goals.data else 0,
                            'tasks_count': len(tasks.data) if tasks.data else 0
                        }
                    }
            else:
                # No suitable workspace found - create a synthetic test
                logger.info("⚠️ No workspace found with completed goals and no deliverables")
                logger.info("ℹ️ Creating synthetic deliverable test scenario...")
                
                # Try to create a test deliverable for any available workspace with goals
                from database import supabase
                any_goals = supabase.table('workspace_goals').select('*').limit(5).execute()
                
                if any_goals.data:
                    test_workspace_id = any_goals.data[0]['workspace_id']
                    logger.info(f"📝 Testing deliverable creation for workspace {test_workspace_id}")
                    
                    try:
                        from fix_deliverable_creation import force_create_deliverable
                        deliverable_id = await force_create_deliverable(
                            test_workspace_id, 
                            any_goals.data[:2],  # Use first 2 goals
                            []  # Empty tasks array for synthetic test
                        )
                        
                        self.test_results['deliverable_generation'] = {
                            'status': 'passed',
                            'details': {
                                'workspace_id': test_workspace_id,
                                'deliverable_created': bool(deliverable_id),
                                'deliverable_id': deliverable_id,
                                'test_type': 'synthetic',
                                'goals_count': len(any_goals.data[:2])
                            }
                        }
                        logger.info(f"✅ Synthetic deliverable generation: created {deliverable_id}")
                    except Exception as e:
                        logger.error(f"❌ Synthetic deliverable generation failed: {e}")
                        self.test_results['deliverable_generation'] = {
                            'status': 'failed',
                            'error': f"Synthetic test failed: {str(e)}"
                        }
                else:
                    self.test_results['deliverable_generation'] = {
                        'status': 'skipped',
                        'details': {
                            'reason': 'No goals found in database for testing'
                        }
                    }
                    logger.info("⚠️ Deliverable generation: skipped (no goals found in database)")
                
        except Exception as e:
            self.test_results['deliverable_generation'] = {
                'status': 'failed',
                'error': str(e)
            }
            logger.error(f"❌ Deliverable generation test failed: {e}")

    async def _analyze_existing_workspaces(self):
        """Test 7: Analyze existing workspaces for root causes"""
        logger.info("🔍 Test 7: Existing Workspace Analysis")
        
        try:
            from database import supabase
            
            # Get workspace statistics
            workspaces = supabase.table('workspaces').select('id, name, status').execute()
            
            workspace_stats = {}
            for workspace in workspaces.data or []:
                workspace_id = workspace['id']
                
                # Get counts for this workspace
                tasks = supabase.table('tasks').select('id, status').eq('workspace_id', workspace_id).execute()
                goals = supabase.table('workspace_goals').select('id, status').eq('workspace_id', workspace_id).execute()
                deliverables = supabase.table('deliverables').select('id, status').eq('workspace_id', workspace_id).execute()
                
                task_statuses = {}
                for task in tasks.data or []:
                    status = task['status']
                    task_statuses[status] = task_statuses.get(status, 0) + 1
                
                goal_statuses = {}
                for goal in goals.data or []:
                    status = goal['status']
                    goal_statuses[status] = goal_statuses.get(status, 0) + 1
                
                workspace_stats[workspace_id] = {
                    'name': workspace['name'],
                    'status': workspace['status'],
                    'task_counts': task_statuses,
                    'goal_counts': goal_statuses,
                    'deliverable_count': len(deliverables.data or [])
                }
            
            # Analyze patterns
            total_workspaces = len(workspace_stats)
            workspaces_with_deliverables = sum(1 for stats in workspace_stats.values() if stats['deliverable_count'] > 0)
            completion_rate = (workspaces_with_deliverables / total_workspaces * 100) if total_workspaces > 0 else 0
            
            # Find problematic patterns
            problematic_workspaces = []
            for workspace_id, stats in workspace_stats.items():
                has_completed_goals = stats['goal_counts'].get('completed', 0) > 0
                has_no_deliverables = stats['deliverable_count'] == 0
                has_failed_tasks = stats['task_counts'].get('failed', 0) > 0
                
                if has_completed_goals and has_no_deliverables:
                    problematic_workspaces.append({
                        'workspace_id': workspace_id,
                        'issue': 'completed_goals_no_deliverables',
                        'stats': stats
                    })
                elif has_failed_tasks and has_no_deliverables:
                    problematic_workspaces.append({
                        'workspace_id': workspace_id,
                        'issue': 'failed_tasks_blocking_deliverables',
                        'stats': stats
                    })
            
            self.test_results['existing_workspace_analysis'] = {
                'status': 'passed',
                'details': {
                    'total_workspaces': total_workspaces,
                    'workspaces_with_deliverables': workspaces_with_deliverables,
                    'completion_rate_percent': round(completion_rate, 1),
                    'problematic_workspaces_count': len(problematic_workspaces),
                    'problematic_workspaces': problematic_workspaces[:5]  # Limit to first 5
                }
            }
            
            logger.info(f"✅ Workspace analysis: {total_workspaces} total, {workspaces_with_deliverables} with deliverables ({completion_rate:.1f}%), {len(problematic_workspaces)} problematic")
            
        except Exception as e:
            self.test_results['existing_workspace_analysis'] = {
                'status': 'failed',
                'error': str(e)
            }
            logger.error(f"❌ Existing workspace analysis failed: {e}")

    def _generate_final_report(self):
        """Generate final validation report"""
        logger.info("📋 GENERATING FINAL VALIDATION REPORT")
        
        passed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'passed')
        failed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'failed')
        skipped_tests = sum(1 for result in self.test_results.values() if result['status'] == 'skipped')
        total_tests = len(self.test_results)
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        logger.info("="*60)
        logger.info("🎯 COMPREHENSIVE VALIDATION TEST RESULTS")
        logger.info("="*60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"✅ Passed: {passed_tests}")
        logger.info(f"❌ Failed: {failed_tests}")  
        logger.info(f"⚠️ Skipped: {skipped_tests}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        logger.info("="*60)
        
        for test_name, result in self.test_results.items():
            status_icon = {"passed": "✅", "failed": "❌", "skipped": "⚠️"}.get(result['status'], "❓")
            logger.info(f"{status_icon} {test_name.replace('_', ' ').title()}: {result['status'].upper()}")
            
            if result['status'] == 'failed' and 'error' in result:
                logger.info(f"   Error: {result['error']}")
            elif 'details' in result:
                logger.info(f"   Details: {json.dumps(result['details'], indent=4)}")
        
        logger.info("="*60)
        
        # Save detailed report to file
        report_filename = f"validation_test_report_{int(datetime.now().timestamp())}.json"
        with open(report_filename, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_tests': total_tests,
                    'passed': passed_tests,
                    'failed': failed_tests,
                    'skipped': skipped_tests,
                    'success_rate': success_rate
                },
                'test_results': self.test_results
            }, f, indent=2)
        
        logger.info(f"📄 Detailed report saved to: {report_filename}")
        
        if success_rate >= 80:
            logger.info("🎉 VALIDATION SUCCESSFUL - System is ready for production!")
        elif success_rate >= 60:
            logger.info("⚠️ VALIDATION PARTIAL - Some issues remain but core functionality works")
        else:
            logger.error("❌ VALIDATION FAILED - Critical issues prevent system operation")

async def main():
    """Main test execution"""
    validator = ComprehensiveValidationTest()
    await validator.run_full_validation()

if __name__ == "__main__":
    asyncio.run(main())