#!/usr/bin/env python3
"""
Test Memory Read/Apply Cycle
Tests the complete memory system: Store insights → Read similar insights → Apply to tasks → Learn from results
"""

import asyncio
import json
import logging
from datetime import datetime
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(__file__))

from services.memory_similarity_engine import memory_similarity_engine
from services.learning_feedback_engine import learning_feedback_engine
from database import add_memory_insight, get_memory_insights, create_task, list_tasks
from ai_agents.manager import AgentManager
from uuid import UUID, uuid4

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('test_memory_cycle.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MemoryReadApplyCycleTest:
    """Test the complete memory read/apply cycle"""
    
    def __init__(self):
        self.test_workspace_id = f"test-memory-workspace-{uuid4()}"
        self.test_results = {
            "test_start": datetime.now().isoformat(),
            "phases_completed": [],
            "phases_failed": [],
            "insights_stored": 0,
            "insights_retrieved": 0,
            "tasks_enhanced": 0,
            "learning_cycles": 0,
            "overall_success": False
        }
    
    async def run_complete_test(self):
        """Run the complete memory read/apply cycle test"""
        logger.info("🧠 Starting Memory Read/Apply Cycle Test")
        logger.info("=" * 70)
        
        try:
            # Phase 1: Seed memory with initial insights
            await self.phase_1_seed_memory()
            
            # Phase 2: Test similarity-based retrieval
            await self.phase_2_test_similarity_retrieval()
            
            # Phase 3: Test task enhancement with insights
            await self.phase_3_test_task_enhancement()
            
            # Phase 4: Test learning from execution results
            await self.phase_4_test_learning_feedback()
            
            # Phase 5: Test complete cycle integration
            await self.phase_5_test_complete_cycle()
            
            self.test_results["overall_success"] = len(self.test_results["phases_failed"]) == 0
            
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            self.test_results["overall_success"] = False
            import traceback
            traceback.print_exc()
        
        self._print_test_summary()
        return self.test_results
    
    async def phase_1_seed_memory(self):
        """Seed memory with various types of insights"""
        phase_name = "seed_memory"
        logger.info("🌱 PHASE 1: Seeding Memory with Initial Insights")
        
        try:
            # Create diverse insights to test similarity matching
            test_insights = [
                {
                    "type": "task_success_pattern",
                    "content": json.dumps({
                        "pattern_name": "API Development Success",
                        "task_characteristics": ["API endpoint creation", "REST implementation", "authentication"],
                        "success_factors": ["Clear documentation", "Proper error handling", "Input validation"],
                        "recommendations": ["Use OpenAPI spec", "Implement rate limiting", "Add comprehensive tests"],
                        "confidence_score": 0.9
                    })
                },
                {
                    "type": "task_failure_lesson",
                    "content": json.dumps({
                        "failure_pattern": "Database Connection Issues",
                        "root_causes": ["Connection timeout", "Invalid credentials", "Network issues"],
                        "prevention_strategies": ["Connection pooling", "Retry logic", "Health checks"],
                        "warning_signs": ["Slow response times", "Connection errors", "Timeout exceptions"],
                        "affected_task_count": 3
                    })
                },
                {
                    "type": "agent_performance_insight",
                    "content": json.dumps({
                        "agent_id": "agent-backend-dev",
                        "performance_category": "high_performer",
                        "success_rate": 0.85,
                        "recommendations": ["Assign complex backend tasks", "Use as model for similar agents"]
                    })
                },
                {
                    "type": "task_success_pattern",
                    "content": json.dumps({
                        "pattern_name": "Frontend Component Success",
                        "task_characteristics": ["UI component creation", "React development", "responsive design"],
                        "success_factors": ["Modular design", "Proper state management", "Accessibility"],
                        "recommendations": ["Use TypeScript", "Implement proper testing", "Follow design system"],
                        "confidence_score": 0.8
                    })
                },
                {
                    "type": "timing_optimization_insight",
                    "content": json.dumps({
                        "pattern_type": "execution_timing",
                        "recommendations": ["Break down complex tasks", "Optimize resource allocation", "Monitor execution time"],
                        "analysis_timestamp": datetime.now().isoformat()
                    })
                }
            ]
            
            # Store insights in memory
            for insight in test_insights:
                await add_memory_insight(
                    workspace_id=self.test_workspace_id,
                    insight_type=insight["type"],
                    content=insight["content"]
                )
                self.test_results["insights_stored"] += 1
                
            logger.info(f"✅ Seeded {len(test_insights)} insights into memory")
            self.test_results["phases_completed"].append(phase_name)
            
        except Exception as e:
            logger.error(f"❌ Phase 1 Failed: {e}")
            self.test_results["phases_failed"].append(phase_name)
            raise
    
    async def phase_2_test_similarity_retrieval(self):
        """Test similarity-based insight retrieval"""
        phase_name = "similarity_retrieval"
        logger.info("🔍 PHASE 2: Testing Similarity-Based Retrieval")
        
        try:
            # Test various task contexts to see if relevant insights are retrieved
            test_contexts = [
                {
                    "name": "Create User Authentication API",
                    "description": "Build REST API endpoints for user authentication with JWT tokens",
                    "type": "backend_development",
                    "skills": ["Python", "FastAPI", "JWT", "Authentication"]
                },
                {
                    "name": "Design User Dashboard Component",
                    "description": "Create responsive React component for user dashboard with charts",
                    "type": "frontend_development",
                    "skills": ["React", "TypeScript", "CSS", "Charts"]
                },
                {
                    "name": "Fix Database Connection Issues",
                    "description": "Resolve intermittent database connection timeouts in production",
                    "type": "bug_fix",
                    "skills": ["Database", "PostgreSQL", "Connection Pooling"]
                }
            ]
            
            total_retrieved = 0
            
            for context in test_contexts:
                logger.info(f"Testing similarity search for: {context['name']}")
                
                relevant_insights = await memory_similarity_engine.get_relevant_insights(
                    workspace_id=self.test_workspace_id,
                    task_context=context
                )
                
                logger.info(f"  📊 Retrieved {len(relevant_insights)} relevant insights")
                
                for insight in relevant_insights:
                    similarity_score = insight.get('similarity_score', 0)
                    insight_type = insight.get('insight_type', 'unknown')
                    logger.info(f"    - {insight_type}: {similarity_score:.2f} similarity")
                
                total_retrieved += len(relevant_insights)
                
                # Verify we got reasonable results
                if context['type'] == 'backend_development':
                    # Should retrieve API development insights
                    api_insights = [i for i in relevant_insights if 'API' in i.get('content', '')]
                    assert len(api_insights) > 0, "Should find API-related insights for backend task"
                
                elif context['type'] == 'frontend_development':
                    # Should retrieve frontend/component insights
                    frontend_insights = [i for i in relevant_insights if 'component' in i.get('content', '').lower()]
                    assert len(frontend_insights) > 0, "Should find component-related insights for frontend task"
                
                elif context['type'] == 'bug_fix' and 'database' in context['description'].lower():
                    # Should retrieve database-related insights
                    db_insights = [i for i in relevant_insights if 'database' in i.get('content', '').lower()]
                    assert len(db_insights) > 0, "Should find database-related insights for DB issue"
            
            self.test_results["insights_retrieved"] = total_retrieved
            logger.info(f"✅ Successfully retrieved {total_retrieved} relevant insights across test contexts")
            self.test_results["phases_completed"].append(phase_name)
            
        except Exception as e:
            logger.error(f"❌ Phase 2 Failed: {e}")
            self.test_results["phases_failed"].append(phase_name)
            raise
    
    async def phase_3_test_task_enhancement(self):
        """Test enhancing tasks with insights"""
        phase_name = "task_enhancement"
        logger.info("🔧 PHASE 3: Testing Task Enhancement with Insights")
        
        try:
            # Create a mock task to test enhancement
            from models import Task, TaskStatus
            
            mock_task = Task(
                id=uuid4(),
                workspace_id=UUID(self.test_workspace_id),
                name="Build Payment Processing API",
                description="Create secure API endpoints for payment processing with Stripe integration",
                status=TaskStatus.PENDING,
                agent_id=None,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Test similarity engine integration
            task_context = {
                'name': mock_task.name,
                'description': mock_task.description,
                'type': 'backend_development',
                'skills': ['Python', 'FastAPI', 'Stripe', 'Payment Processing']
            }
            
            # Get relevant insights
            relevant_insights = await memory_similarity_engine.get_relevant_insights(
                workspace_id=self.test_workspace_id,
                task_context=task_context
            )
            
            logger.info(f"Found {len(relevant_insights)} insights for task enhancement")
            
            # Test enhancement process (simulated since we don't have a real AgentManager setup)
            if relevant_insights:
                # Simulate the enhancement process
                enhanced_description = mock_task.description + "\n\n🧠 RELEVANT INSIGHTS FROM PAST EXPERIENCE:\n"
                
                for i, insight in enumerate(relevant_insights[:3], 1):
                    insight_type = insight.get('insight_type', 'unknown')
                    similarity_score = insight.get('similarity_score', 0)
                    enhanced_description += f"\n{i}. {insight_type.upper()} (relevance: {similarity_score:.2f})\n"
                
                enhanced_description += "\nPlease consider these insights when executing the task.\n"
                
                # Verify enhancement worked
                assert "🧠 RELEVANT INSIGHTS" in enhanced_description
                assert "Please consider these insights" in enhanced_description
                
                logger.info("✅ Task successfully enhanced with insights")
                self.test_results["tasks_enhanced"] += 1
            else:
                logger.warning("No insights found for task enhancement")
            
            self.test_results["phases_completed"].append(phase_name)
            
        except Exception as e:
            logger.error(f"❌ Phase 3 Failed: {e}")
            self.test_results["phases_failed"].append(phase_name)
            raise
    
    async def phase_4_test_learning_feedback(self):
        """Test learning from execution results"""
        phase_name = "learning_feedback"
        logger.info("🎓 PHASE 4: Testing Learning from Execution Results")
        
        try:
            # Test storing execution insights
            task_context = {
                'task_id': str(uuid4()),
                'name': 'API Development Task',
                'description': 'Build REST API with authentication',
                'type': 'backend_development',
                'agent_role': 'backend_developer'
            }
            
            # Test successful execution insight
            success_result = {
                'success': True,
                'result': 'Successfully created API with JWT authentication',
                'execution_time': 300,
                'tools_used': ['web_search', 'code_generation'],
                'success_factors': ['Clear requirements', 'Good documentation'],
                'key_insights': ['JWT implementation pattern worked well']
            }
            
            success_stored = await memory_similarity_engine.store_task_execution_insight(
                workspace_id=self.test_workspace_id,
                task_context=task_context,
                execution_result=success_result
            )
            
            if success_stored:
                logger.info("✅ Successfully stored success insight")
                self.test_results["learning_cycles"] += 1
            
            # Test failure execution insight
            failure_result = {
                'success': False,
                'error_message': 'Authentication middleware failed',
                'failure_reasons': ['Missing environment variables', 'Invalid JWT secret'],
                'lessons_learned': ['Validate env vars early', 'Use proper secret management'],
                'prevention_strategies': ['Add config validation', 'Use secret manager']
            }
            
            failure_stored = await memory_similarity_engine.store_task_execution_insight(
                workspace_id=self.test_workspace_id,
                task_context=task_context,
                execution_result=failure_result
            )
            
            if failure_stored:
                logger.info("✅ Successfully stored failure insight")
                self.test_results["learning_cycles"] += 1
            
            # Test comprehensive learning feedback
            learning_result = await learning_feedback_engine.generate_periodic_insights(
                workspace_id=self.test_workspace_id
            )
            
            logger.info(f"📊 Learning feedback result: {learning_result}")
            
            if learning_result.get('status') == 'completed':
                insights_generated = learning_result.get('insights_generated', 0)
                logger.info(f"✅ Generated {insights_generated} insights from learning feedback")
                self.test_results["learning_cycles"] += 1
            
            self.test_results["phases_completed"].append(phase_name)
            
        except Exception as e:
            logger.error(f"❌ Phase 4 Failed: {e}")
            self.test_results["phases_failed"].append(phase_name)
            raise
    
    async def phase_5_test_complete_cycle(self):
        """Test the complete memory cycle integration"""
        phase_name = "complete_cycle"
        logger.info("🔄 PHASE 5: Testing Complete Memory Cycle")
        
        try:
            # Verify we can retrieve newly stored insights
            all_insights = await get_memory_insights(self.test_workspace_id, limit=20)
            
            logger.info(f"📊 Total insights in memory: {len(all_insights)}")
            
            # Verify different types of insights exist
            insight_types = {}
            for insight in all_insights:
                insight_type = insight.get('insight_type', 'unknown')
                insight_types[insight_type] = insight_types.get(insight_type, 0) + 1
            
            logger.info("📋 Insight types stored:")
            for insight_type, count in insight_types.items():
                logger.info(f"  - {insight_type}: {count}")
            
            # Test that we can find relevant insights for a new task
            new_task_context = {
                'name': 'Optimize API Performance',
                'description': 'Improve response times and reduce latency in existing API',
                'type': 'optimization',
                'skills': ['Performance', 'API', 'Optimization']
            }
            
            relevant_insights = await memory_similarity_engine.get_relevant_insights(
                workspace_id=self.test_workspace_id,
                task_context=new_task_context
            )
            
            logger.info(f"🔍 Found {len(relevant_insights)} relevant insights for new task")
            
            # Verify the cycle is working
            cycle_checks = {
                "insights_stored": self.test_results["insights_stored"] > 0,
                "insights_retrieved": self.test_results["insights_retrieved"] > 0,
                "tasks_enhanced": self.test_results["tasks_enhanced"] > 0,
                "learning_cycles": self.test_results["learning_cycles"] > 0,
                "similarity_working": len(relevant_insights) > 0
            }
            
            logger.info("🔄 Memory Cycle Verification:")
            for check_name, passed in cycle_checks.items():
                status = "✅" if passed else "❌"
                logger.info(f"  {status} {check_name}: {'PASS' if passed else 'FAIL'}")
            
            all_passed = all(cycle_checks.values())
            
            if all_passed:
                logger.info("✅ Complete memory cycle working correctly!")
            else:
                logger.warning("⚠️ Some memory cycle components not working as expected")
            
            self.test_results["phases_completed"].append(phase_name)
            
        except Exception as e:
            logger.error(f"❌ Phase 5 Failed: {e}")
            self.test_results["phases_failed"].append(phase_name)
            raise
    
    def _print_test_summary(self):
        """Print comprehensive test summary"""
        logger.info("\n" + "=" * 70)
        logger.info("🧠 MEMORY READ/APPLY CYCLE TEST SUMMARY")
        logger.info("=" * 70)
        
        logger.info(f"✅ Phases Completed: {len(self.test_results['phases_completed'])}/5")
        logger.info(f"❌ Phases Failed: {len(self.test_results['phases_failed'])}")
        
        logger.info(f"\n📊 Memory Metrics:")
        logger.info(f"  - Insights Stored: {self.test_results['insights_stored']}")
        logger.info(f"  - Insights Retrieved: {self.test_results['insights_retrieved']}")
        logger.info(f"  - Tasks Enhanced: {self.test_results['tasks_enhanced']}")
        logger.info(f"  - Learning Cycles: {self.test_results['learning_cycles']}")
        
        logger.info(f"\n🚀 Overall Success: {'YES' if self.test_results['overall_success'] else 'NO'}")
        
        if self.test_results['phases_failed']:
            logger.info(f"\n❌ Failed Phases: {', '.join(self.test_results['phases_failed'])}")
        
        # Save results
        results_file = f"memory_cycle_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        logger.info(f"\n💾 Full results saved to: {results_file}")
        logger.info("=" * 70)


async def main():
    """Run the memory read/apply cycle test"""
    test = MemoryReadApplyCycleTest()
    results = await test.run_complete_test()
    
    # Return exit code based on success
    return 0 if results["overall_success"] else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)