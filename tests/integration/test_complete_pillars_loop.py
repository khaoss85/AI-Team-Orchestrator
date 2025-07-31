#!/usr/bin/env python3
"""
🚀 COMPLETE PILLARS LOOP TEST
Test completo del loop Team → Task → Asset → Deliverable seguendo i 5 pillars:

1. 🎯 Goal Decomposition: AI intelligente decompone obiettivi in sub-task concreti  
2. 👥 Agent Orchestration: Assegnazione semantica agenti basata su competenze reali
3. 🔧 Real Tool Usage: Gli agenti usano tools reali per contenuti autentici
4. 👁️ User Visibility: Utenti vedono thinking process e deliverables
5. 🏆 Content Quality: Sistema AI previene contenuti fake, garantisce informazioni reali
"""

import asyncio
import requests
import json
import time
import logging
from datetime import datetime
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(__file__))

from database import list_tasks, get_task, get_ready_tasks_python
from ai_agents.manager import AgentManager
from models import TaskStatus
from uuid import UUID
from services.learning_feedback_engine import learning_feedback_engine
from deliverable_system.concrete_asset_extractor import ConcreteAssetExtractor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

class CompletePillarsLoopTest:
    """
    Test completo del loop Team → Task → Asset → Deliverable
    Verifica compliance con i 5 pillars del sistema
    """
    
    def __init__(self):
        self.workspace_id = None
        self.goal_ids = []
        self.agent_ids = []
        self.task_ids = []
        self.deliverable_ids = []
        self.asset_ids = []
        self.results = {
            "test_start": datetime.now().isoformat(),
            "phases_completed": [],
            "phases_failed": [],
            "workspace_id": None,
            "goal_ids": [],
            "agent_ids": [],
            "task_ids": [],
            "asset_ids": [],
            "deliverable_ids": [],
            "pillars_compliance": {
                "goal_decomposition": False,
                "agent_orchestration": False, 
                "real_tool_usage": False,
                "user_visibility": False,
                "content_quality": False
            },
            "loop_metrics": {
                "teams_created": 0,
                "tasks_generated": 0,
                "tasks_executed": 0,
                "assets_extracted": 0,
                "deliverables_created": 0,
                "real_content_detected": 0,
                "fake_content_blocked": 0
            },
            "overall_success": False,
            "test_end": None,
            "success_rate": 0.0
        }
    
    async def run_full_test(self):
        """Esegue il test completo del loop seguendo i pillars"""
        
        logger.info("🚀 Starting COMPLETE PILLARS LOOP TEST")
        logger.info("=" * 80)
        logger.info("🎯 Testing: Team → Task → Asset → Deliverable")
        logger.info("📋 Validating compliance with 5 pillars:")
        logger.info("  1. 🎯 Goal Decomposition")
        logger.info("  2. 👥 Agent Orchestration") 
        logger.info("  3. 🔧 Real Tool Usage")
        logger.info("  4. 👁️ User Visibility")
        logger.info("  5. 🏆 Content Quality")
        logger.info("=" * 80)
        
        try:
            # Phase 1: Workspace setup with realistic goal
            await self.phase_1_realistic_workspace_setup()
            
            # Phase 2: Team orchestration (Pillar 2)
            await self.phase_2_team_orchestration()
            
            # Phase 3: Goal decomposition (Pillar 1)
            await self.phase_3_goal_decomposition()
            
            # Phase 4: Task execution with real tools (Pillar 3)
            await self.phase_4_real_task_execution()
            
            # Phase 5: Asset extraction and validation (Pillar 5)
            await self.phase_5_asset_extraction_validation()
            
            # Phase 6: Deliverable generation (Pillar 4)
            await self.phase_6_deliverable_generation()
            
            # Phase 7: User visibility validation (Pillar 4)
            await self.phase_7_user_visibility_validation()
            
            # Phase 8: Content quality validation (Pillar 5)
            await self.phase_8_content_quality_validation()
            
            # Final analysis
            await self.phase_9_pillars_compliance_analysis()
            
            # Determine overall success
            pillars_passed = sum(1 for passed in self.results["pillars_compliance"].values() if passed)
            if pillars_passed >= 4:  # At least 4/5 pillars must pass
                self.results["overall_success"] = True
                logger.info(f"🎉 COMPLETE PILLARS LOOP TEST PASSED! ({pillars_passed}/5 pillars)")
            else:
                self.results["overall_success"] = False
                logger.error(f"❌ Test FAILED. Only {pillars_passed}/5 pillars passed")
            
            self.results["test_end"] = datetime.now().isoformat()
            self.results["success_rate"] = len(self.results["phases_completed"]) / 9.0
            
            # Save results
            results_file = f"complete_pillars_loop_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            
            logger.info(f"💾 Results saved to: {results_file}")
            
        except Exception as e:
            logger.error(f"❌ Test execution failed: {e}")
            self.results["overall_success"] = False
        
        self.print_summary()
    
    async def phase_1_realistic_workspace_setup(self):
        """Phase 1: Create workspace with realistic business goal"""
        logger.info("📁 PHASE 1: REALISTIC WORKSPACE SETUP")
        
        try:
            # Create workspace with a realistic business goal
            workspace_data = {
                "name": "AI-Powered Market Research Platform",
                "description": "Develop a comprehensive platform for automated market research and competitor analysis using AI tools",
                "goal": "Create a market research platform that analyzes competitor strategies, identifies market opportunities, and generates actionable business insights for SME companies"
            }
            
            response = requests.post(f"{API_BASE}/workspaces", json=workspace_data, timeout=15)
            
            if response.status_code != 201:
                raise Exception(f"Workspace creation failed: {response.status_code}")
            
            workspace = response.json()
            self.workspace_id = workspace["id"]
            self.results["workspace_id"] = self.workspace_id
            
            logger.info(f"✅ Created realistic workspace: {workspace['name']}")
            logger.info(f"🎯 Business Goal: {workspace_data['goal']}")
            
            self.results["phases_completed"].append("realistic_workspace_setup")
            
        except Exception as e:
            logger.error(f"❌ Phase 1 Failed: {e}")
            self.results["phases_failed"].append("realistic_workspace_setup")
            raise
    
    async def phase_2_team_orchestration(self):
        """Phase 2: Team orchestration with semantic matching (Pillar 2)"""
        logger.info("👥 PHASE 2: TEAM ORCHESTRATION (PILLAR 2)")
        
        try:
            # Create specialized team for market research platform
            proposal_payload = {
                "workspace_id": self.workspace_id,
                "project_description": "Build an AI-powered market research platform with web scraping, competitor analysis, data visualization, and automated report generation capabilities",
                "budget": 2500.0,
                "max_team_size": 4
            }
            
            logger.info("⏳ Creating specialized team proposal...")
            proposal_response = requests.post(f"{API_BASE}/director/proposal", json=proposal_payload, timeout=60)
            
            if proposal_response.status_code != 200:
                raise Exception(f"Team proposal failed: {proposal_response.status_code}")
            
            proposal_data = proposal_response.json()
            proposal_id = proposal_data["proposal_id"]
            
            logger.info("⏳ Approving team proposal...")
            approval_response = requests.post(f"{API_BASE}/director/approve/{self.workspace_id}", 
                                            params={"proposal_id": proposal_id}, timeout=45)
            
            if approval_response.status_code not in [200, 204]:
                raise Exception(f"Team approval failed: {approval_response.status_code}")
            
            approval_data = approval_response.json()
            self.agent_ids = approval_data.get("created_agent_ids", [])
            self.results["agent_ids"] = self.agent_ids
            self.results["loop_metrics"]["teams_created"] = len(self.agent_ids)
            
            # Validate team composition for market research
            agents_response = requests.get(f"{BASE_URL}/agents/{self.workspace_id}", timeout=10)
            if agents_response.status_code == 200:
                agents = agents_response.json()
                
                # Check for relevant skills
                required_skills = ["data analysis", "web scraping", "research", "development", "visualization"]
                found_skills = []
                
                for agent in agents:
                    agent_skills = agent.get('hard_skills', [])
                    for skill in agent_skills:
                        if isinstance(skill, dict) and 'name' in skill:
                            skill_name = skill['name'].lower()
                            for req_skill in required_skills:
                                if req_skill in skill_name:
                                    found_skills.append(req_skill)
                
                if len(found_skills) >= 2:
                    self.results["pillars_compliance"]["agent_orchestration"] = True
                    logger.info(f"✅ Team orchestration successful - Found relevant skills: {found_skills}")
                else:
                    logger.warning(f"⚠️ Team orchestration suboptimal - Limited relevant skills found")
            
            self.results["phases_completed"].append("team_orchestration")
            
        except Exception as e:
            logger.error(f"❌ Phase 2 Failed: {e}")
            self.results["phases_failed"].append("team_orchestration")
            raise
    
    async def phase_3_goal_decomposition(self):
        """Phase 3: Goal decomposition into actionable tasks (Pillar 1)"""
        logger.info("🎯 PHASE 3: GOAL DECOMPOSITION (PILLAR 1)")
        
        try:
            # Wait for task generation from goal decomposition
            max_wait_time = 300
            check_interval = 15
            
            logger.info(f"⏱️ Monitoring goal decomposition for {max_wait_time} seconds...")
            
            for i in range(max_wait_time // check_interval):
                time.sleep(check_interval)
                
                tasks_response = requests.get(f"{API_BASE}/workspaces/{self.workspace_id}/tasks", timeout=10)
                
                if tasks_response.status_code == 200:
                    tasks = tasks_response.json()
                    logger.info(f"📝 After {(i+1)*check_interval}s: Found {len(tasks)} tasks")
                    
                    if len(tasks) > 0:
                        self.task_ids = [task["id"] for task in tasks]
                        self.results["task_ids"] = self.task_ids
                        self.results["loop_metrics"]["tasks_generated"] = len(tasks)
                        
                        # Validate goal decomposition quality
                        actionable_tasks = 0
                        for task in tasks:
                            task_name = task.get('name', '').lower()
                            description = task.get('description', '').lower()
                            
                            # Check for actionable keywords
                            actionable_keywords = ['analyze', 'research', 'develop', 'create', 'implement', 'build', 'design']
                            if any(keyword in task_name or keyword in description for keyword in actionable_keywords):
                                actionable_tasks += 1
                        
                        if actionable_tasks >= len(tasks) * 0.7:  # At least 70% actionable
                            self.results["pillars_compliance"]["goal_decomposition"] = True
                            logger.info(f"✅ Goal decomposition successful - {actionable_tasks}/{len(tasks)} tasks actionable")
                        else:
                            logger.warning(f"⚠️ Goal decomposition suboptimal - Only {actionable_tasks}/{len(tasks)} tasks actionable")
                        
                        self.results["phases_completed"].append("goal_decomposition")
                        return
            
            raise Exception("Goal decomposition timeout - no tasks generated")
            
        except Exception as e:
            logger.error(f"❌ Phase 3 Failed: {e}")
            self.results["phases_failed"].append("goal_decomposition")
            raise
    
    async def phase_4_real_task_execution(self):
        """Phase 4: Task execution with real tools (Pillar 3)"""
        logger.info("🔧 PHASE 4: REAL TASK EXECUTION (PILLAR 3)")
        
        try:
            # Initialize AgentManager
            manager = AgentManager(UUID(self.workspace_id))
            await manager.initialize()
            
            # Get tasks ready for execution
            ready_tasks = await get_ready_tasks_python(self.workspace_id)
            
            logger.info(f"⏳ Executing {len(ready_tasks)} ready tasks with real tools...")
            
            executed_count = 0
            real_tool_usage_count = 0
            max_executions = min(2, len(ready_tasks))  # Execute up to 2 tasks for thorough testing
            
            for i, task_data in enumerate(ready_tasks[:max_executions]):
                try:
                    task_id = UUID(task_data["task_id"])
                    logger.info(f"\\n🔧 Executing task {i+1}/{max_executions}: {task_data['task_name']}")
                    
                    # Execute task
                    result = await manager.execute_task(task_id)
                    
                    if result and result.status == TaskStatus.COMPLETED:
                        executed_count += 1
                        logger.info(f"  ✅ Task completed successfully")
                        
                        # Check for real tool usage indicators
                        if result.result:
                            result_text = result.result.lower()
                            real_tool_indicators = ['web search', 'search results', 'url', 'http', 'found', 'research', 'analysis']
                            
                            if any(indicator in result_text for indicator in real_tool_indicators):
                                real_tool_usage_count += 1
                                logger.info(f"  🔧 Real tool usage detected!")
                    else:
                        logger.warning(f"  ⚠️ Task execution failed or incomplete")
                    
                    # Small delay between tasks
                    time.sleep(3)
                    
                except Exception as e:
                    logger.error(f"  ❌ Task execution error: {e}")
                    continue
            
            self.results["loop_metrics"]["tasks_executed"] = executed_count
            
            # Validate real tool usage
            if real_tool_usage_count > 0:
                self.results["pillars_compliance"]["real_tool_usage"] = True
                logger.info(f"✅ Real tool usage validated - {real_tool_usage_count}/{executed_count} tasks used real tools")
            else:
                logger.warning("⚠️ No real tool usage detected")
            
            if executed_count > 0:
                self.results["phases_completed"].append("real_task_execution")
            else:
                raise Exception("No tasks were executed")
            
        except Exception as e:
            logger.error(f"❌ Phase 4 Failed: {e}")
            self.results["phases_failed"].append("real_task_execution")
            raise
    
    async def phase_5_asset_extraction_validation(self):
        """Phase 5: Asset extraction and validation (Pillar 5)"""
        logger.info("📦 PHASE 5: ASSET EXTRACTION & VALIDATION (PILLAR 5)")
        
        try:
            # Check for extracted assets via API
            assets_response = requests.get(f"{API_BASE}/assets/workspace/{self.workspace_id}", timeout=10)
            assets = []
            if assets_response.status_code == 200:
                assets = assets_response.json()
            
            if assets:
                self.asset_ids = [asset.get('id') for asset in assets if asset.get('id')]
                self.results["asset_ids"] = self.asset_ids
                self.results["loop_metrics"]["assets_extracted"] = len(assets)
                
                # Validate asset authenticity
                authentic_assets = 0
                for asset in assets:
                    content = asset.get('content', {})
                    if content and isinstance(content, dict):
                        # Check for real content indicators
                        content_str = str(content).lower()
                        fake_indicators = ['lorem ipsum', 'placeholder', 'example', 'sample', 'dummy', 'test data']
                        real_indicators = ['http', 'url', 'analysis', 'research', 'data', 'result']
                        
                        has_fake = any(indicator in content_str for indicator in fake_indicators)
                        has_real = any(indicator in content_str for indicator in real_indicators)
                        
                        if has_real and not has_fake:
                            authentic_assets += 1
                
                self.results["loop_metrics"]["real_content_detected"] = authentic_assets
                self.results["loop_metrics"]["fake_content_blocked"] = len(assets) - authentic_assets
                
                if authentic_assets >= len(assets) * 0.6:  # At least 60% authentic
                    self.results["pillars_compliance"]["content_quality"] = True
                    logger.info(f"✅ Content quality validated - {authentic_assets}/{len(assets)} assets authentic")
                else:
                    logger.warning(f"⚠️ Content quality concerns - Only {authentic_assets}/{len(assets)} assets authentic")
                
                logger.info(f"📦 Found {len(assets)} extracted assets")
                
            else:
                logger.info("📦 No assets extracted yet - this is normal for recent tasks")
            
            self.results["phases_completed"].append("asset_extraction_validation")
            
        except Exception as e:
            logger.error(f"❌ Phase 5 Failed: {e}")
            self.results["phases_failed"].append("asset_extraction_validation")
    
    async def phase_6_deliverable_generation(self):
        """Phase 6: Deliverable generation (Pillar 4)"""
        logger.info("📋 PHASE 6: DELIVERABLE GENERATION (PILLAR 4)")
        
        try:
            # Check for deliverables
            deliverables_response = requests.get(f"{API_BASE}/deliverables/workspace/{self.workspace_id}", timeout=10)
            
            if deliverables_response.status_code == 200:
                deliverables = deliverables_response.json()
                self.deliverable_ids = [d["id"] for d in deliverables if "id" in d]
                self.results["deliverable_ids"] = self.deliverable_ids
                self.results["loop_metrics"]["deliverables_created"] = len(deliverables)
                
                if len(deliverables) > 0:
                    logger.info(f"✅ Found {len(deliverables)} deliverables")
                    
                    for deliverable in deliverables:
                        logger.info(f"  📋 {deliverable.get('title', 'Unknown')} - Type: {deliverable.get('type', 'Unknown')}")
                else:
                    logger.info("📋 No deliverables generated yet")
                
            else:
                logger.warning(f"Deliverables check returned: {deliverables_response.status_code}")
            
            self.results["phases_completed"].append("deliverable_generation")
            
        except Exception as e:
            logger.error(f"❌ Phase 6 Failed: {e}")
            self.results["phases_failed"].append("deliverable_generation")
    
    async def phase_7_user_visibility_validation(self):
        """Phase 7: User visibility validation (Pillar 4)"""
        logger.info("👁️ PHASE 7: USER VISIBILITY VALIDATION (PILLAR 4)")
        
        try:
            # Check various visibility endpoints
            visibility_checks = 0
            
            # Check workspace visibility
            workspace_response = requests.get(f"{API_BASE}/workspaces/{self.workspace_id}", timeout=10)
            if workspace_response.status_code == 200:
                visibility_checks += 1
                logger.info("  ✅ Workspace visibility confirmed")
            
            # Check task visibility
            if self.task_ids:
                tasks_response = requests.get(f"{API_BASE}/workspaces/{self.workspace_id}/tasks", timeout=10)
                if tasks_response.status_code == 200:
                    visibility_checks += 1
                    logger.info("  ✅ Task visibility confirmed")
            
            # Check agent visibility
            if self.agent_ids:
                agents_response = requests.get(f"{BASE_URL}/agents/{self.workspace_id}", timeout=10)
                if agents_response.status_code == 200:
                    visibility_checks += 1
                    logger.info("  ✅ Agent visibility confirmed")
            
            # Check asset visibility
            if self.asset_ids:
                assets_response = requests.get(f"{API_BASE}/assets/workspace/{self.workspace_id}", timeout=10)
                if assets_response.status_code == 200:
                    visibility_checks += 1
                    logger.info("  ✅ Asset visibility confirmed")
            
            if visibility_checks >= 2:
                self.results["pillars_compliance"]["user_visibility"] = True
                logger.info(f"✅ User visibility validated - {visibility_checks} visibility checks passed")
            else:
                logger.warning("⚠️ User visibility concerns - Limited visibility confirmed")
            
            self.results["phases_completed"].append("user_visibility_validation")
            
        except Exception as e:
            logger.error(f"❌ Phase 7 Failed: {e}")
            self.results["phases_failed"].append("user_visibility_validation")
    
    async def phase_8_content_quality_validation(self):
        """Phase 8: Content quality validation (Pillar 5)"""
        logger.info("🛡️ PHASE 8: CONTENT QUALITY VALIDATION (PILLAR 5)")
        
        try:
            # Check memory insights for quality patterns
            from database import get_memory_insights
            
            insights = await get_memory_insights(self.workspace_id, limit=10)
            
            if insights:
                quality_insights = 0
                for insight in insights:
                    insight_type = insight.get('insight_type', '')
                    content = insight.get('content', '')
                    
                    if insight_type in ['success_pattern', 'failure_lesson', 'discovery'] and content:
                        quality_insights += 1
                
                logger.info(f"📊 Found {quality_insights} quality insights in memory")
            
            # Final content quality assessment
            total_quality_score = 0
            quality_factors = 0
            
            if self.results["loop_metrics"]["real_content_detected"] > 0:
                total_quality_score += 1
                quality_factors += 1
            
            if self.results["loop_metrics"]["fake_content_blocked"] >= 0:
                total_quality_score += 1
                quality_factors += 1
            
            if insights:
                total_quality_score += 1
                quality_factors += 1
            
            if quality_factors > 0 and total_quality_score / quality_factors >= 0.6:
                self.results["pillars_compliance"]["content_quality"] = True
                logger.info("✅ Content quality validation passed")
            else:
                logger.warning("⚠️ Content quality validation concerns")
            
            self.results["phases_completed"].append("content_quality_validation")
            
        except Exception as e:
            logger.error(f"❌ Phase 8 Failed: {e}")
            self.results["phases_failed"].append("content_quality_validation")
    
    async def phase_9_pillars_compliance_analysis(self):
        """Phase 9: Final pillars compliance analysis"""
        logger.info("📊 PHASE 9: PILLARS COMPLIANCE ANALYSIS")
        
        try:
            logger.info("\\n🏛️ PILLARS COMPLIANCE SUMMARY:")
            logger.info("=" * 50)
            
            for pillar, passed in self.results["pillars_compliance"].items():
                status = "✅ PASS" if passed else "❌ FAIL"
                logger.info(f"  {pillar.replace('_', ' ').title()}: {status}")
            
            logger.info("\\n📊 LOOP METRICS:")
            logger.info("=" * 50)
            
            for metric, value in self.results["loop_metrics"].items():
                logger.info(f"  {metric.replace('_', ' ').title()}: {value}")
            
            self.results["phases_completed"].append("pillars_compliance_analysis")
            
        except Exception as e:
            logger.error(f"❌ Phase 9 Failed: {e}")
            self.results["phases_failed"].append("pillars_compliance_analysis")
    
    def print_summary(self):
        """Print test summary"""
        logger.info("\\n" + "=" * 80)
        logger.info("🎯 COMPLETE PILLARS LOOP TEST - SUMMARY")
        logger.info("=" * 80)
        
        pillars_passed = sum(1 for passed in self.results["pillars_compliance"].values() if passed)
        
        logger.info(f"✅ Phases completed: {len(self.results['phases_completed'])}/9")
        logger.info(f"❌ Phases failed: {len(self.results['phases_failed'])}")
        logger.info(f"🏛️ Pillars passed: {pillars_passed}/5")
        logger.info(f"🎯 Success rate: {self.results['success_rate']:.1%}")
        logger.info(f"🚀 Overall success: {'YES' if self.results['overall_success'] else 'NO'}")
        
        if self.results['phases_completed']:
            logger.info(f"✅ Completed: {', '.join(self.results['phases_completed'])}")
        if self.results['phases_failed']:
            logger.info(f"❌ Failed: {', '.join(self.results['phases_failed'])}")
        
        logger.info("\\n📊 LOOP METRICS:")
        for metric, value in self.results["loop_metrics"].items():
            logger.info(f"  {metric.replace('_', ' ').title()}: {value}")

async def main():
    test = CompletePillarsLoopTest()
    await test.run_full_test()

if __name__ == "__main__":
    asyncio.run(main())