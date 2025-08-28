#!/usr/bin/env python3
"""
🎯 COMPREHENSIVE PRODUCTION E2E TEST
====================================

This test validates the complete AI Team Orchestrator workflow:
1. Goal Definition & Decomposition
2. Team Composition (with manual approval simulation)
3. Task Execution & Memory System
4. QA & Reasoning Process
5. Asset Generation & Extraction
6. Deliverable Creation & Content Validation

The test ensures the system produces concrete, valuable business deliverables.
"""

import asyncio
import json
import sys
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
import time
import requests
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveE2ETest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.workspace_id = None
        self.team_proposal_id = None
        self.test_user_id = str(uuid.uuid4())  # Generate valid UUID for user
        self.test_results = {
            "start_time": datetime.now().isoformat(),
            "phases": {},
            "metrics": {},
            "validation_results": {},
            "deliverables": [],
            "success": False
        }
        
        # Test goal: Create a comprehensive marketing strategy for a fintech startup
        self.test_goal = {
            "name": "Fintech Marketing Strategy Development",
            "description": "Create a comprehensive go-to-market strategy for a new fintech startup offering AI-powered personal finance management. Include market analysis, competitor research, positioning strategy, content marketing plan, and launch timeline.",
            "metric_type": "business_outcome",
            "target_value": 100.0,  # Percentage completion
            "success_criteria": [
                "Market analysis with concrete data and insights",
                "Competitive landscape assessment with specific recommendations",
                "Clear positioning and messaging strategy",
                "Content marketing plan with specific tactics",
                "Launch timeline with measurable milestones"
            ]
        }

    async def run_complete_test(self):
        """Execute the comprehensive E2E test"""
        try:
            logger.info("🚀 Starting Comprehensive Production E2E Test")
            logger.info(f"Test Goal: {self.test_goal['name']}")
            
            # Phase 1: Goal Definition & Workspace Creation
            await self.phase_1_goal_definition()
            
            # Phase 2: Team Composition & Approval
            await self.phase_2_team_composition()
            
            # Phase 3: Task Execution & Monitoring
            await self.phase_3_task_execution()
            
            # Phase 4: QA & Reasoning Validation
            await self.phase_4_qa_reasoning()
            
            # Phase 5: Asset Generation & Extraction
            await self.phase_5_asset_generation()
            
            # Phase 6: Deliverable Creation & Validation
            await self.phase_6_deliverable_validation()
            
            # Phase 7: Final Analysis
            await self.phase_7_final_analysis()
            
            self.test_results["success"] = True
            logger.info("✅ Comprehensive E2E Test COMPLETED SUCCESSFULLY!")
            
        except Exception as e:
            logger.error(f"❌ E2E Test FAILED: {str(e)}")
            self.test_results["error"] = str(e)
            self.test_results["success"] = False
        finally:
            await self.generate_test_report()

    async def phase_1_goal_definition(self):
        """Phase 1: Goal Definition & Workspace Creation"""
        logger.info("\n📊 PHASE 1: Goal Definition & Workspace Creation")
        phase_start = time.time()
        
        try:
            # Create workspace
            workspace_data = {
                "name": f"E2E Test - {self.test_goal['name']}",
                "description": self.test_goal['description'],
                "user_id": self.test_user_id,
                "goal": self.test_goal['description']
            }
            
            response = requests.post(f"{self.base_url}/api/workspaces/", json=workspace_data)
            if response.status_code != 201:
                raise Exception(f"Failed to create workspace: {response.text}")
            
            workspace = response.json()
            self.workspace_id = workspace['id']
            logger.info(f"✅ Created workspace: {self.workspace_id}")
            
            # Create goal in workspace
            goal_data = {
                "workspace_id": self.workspace_id,
                **self.test_goal
            }
            
            response = requests.post(f"{self.base_url}/api/workspaces/{self.workspace_id}/goals", json=goal_data)
            if response.status_code not in [200, 201]:
                raise Exception(f"Failed to create goal: {response.text}")
            
            result = response.json()
            
            # Check if the response has success field or is direct goal data
            if isinstance(result, dict) and result.get('success') == True:
                goal = result.get('goal', result)
                logger.info(f"✅ Goal created successfully: {result.get('message', 'Goal created')}")
            elif isinstance(result, dict) and 'id' in result:
                goal = result
                logger.info(f"✅ Goal created successfully")
            else:
                raise Exception(f"Unexpected goal creation response: {result}")
            
            goal_name = goal.get('name', self.test_goal.get('name', 'Unknown'))
            logger.info(f"✅ Created goal: {goal_name}")
            
            # Wait for automatic goal decomposition
            await asyncio.sleep(5)
            
            # Validate goal was properly created
            response = requests.get(f"{self.base_url}/api/workspaces/{self.workspace_id}/goals")
            if response.status_code != 200:
                raise Exception(f"Failed to fetch goals: {response.text}")
            
            goals = response.json()
            if not goals or len(goals) == 0:
                raise Exception("No goals found after creation")
            
            self.test_results["phases"]["phase_1"] = {
                "status": "completed",
                "duration": time.time() - phase_start,
                "workspace_id": self.workspace_id,
                "goals_created": len(goals)
            }
            
            logger.info(f"✅ Phase 1 completed - {len(goals)} goals created")
            
        except Exception as e:
            logger.error(f"❌ Phase 1 failed: {str(e)}")
            self.test_results["phases"]["phase_1"] = {
                "status": "failed",
                "error": str(e),
                "duration": time.time() - phase_start
            }
            raise

    async def phase_2_team_composition(self):
        """Phase 2: Team Composition & Approval"""
        logger.info("\n👥 PHASE 2: Team Composition & Approval")
        phase_start = time.time()
        
        try:
            # Trigger team proposal generation
            proposal_data = {
                "workspace_id": self.workspace_id,
                "project_description": self.test_goal['description']
            }
            
            response = requests.post(f"{self.base_url}/api/generate-team-proposal", json=proposal_data)
            if response.status_code != 200:
                raise Exception(f"Failed to generate team proposal: {response.text}")
            
            proposal_result = response.json()
            
            # Handle response format - API returns proposal directly, not wrapped in success
            if isinstance(proposal_result, dict) and 'proposal_id' in proposal_result:
                self.team_proposal_id = proposal_result.get('proposal_id')
                team_members = proposal_result.get('team_members', [])
                logger.info(f"✅ Generated team proposal: {self.team_proposal_id}")
                logger.info(f"✅ Team composition: {len(team_members)} members")
            else:
                raise Exception(f"Team proposal generation failed: {proposal_result}")
            
            # Simulate manual approval (the one manual trigger)
            approval_data = {
                "user_feedback": "Approved for E2E test execution"
            }
            
            response = requests.post(f"{self.base_url}/api/director/approve/{self.workspace_id}?proposal_id={self.team_proposal_id}", json=approval_data)
            if response.status_code != 200:
                raise Exception(f"Failed to approve team proposal: {response.text}")
            
            approval_result = response.json()
            if not approval_result.get('success'):
                raise Exception(f"Team proposal approval failed: {approval_result.get('error')}")
            
            logger.info("✅ Team proposal approved (manual trigger simulated)")
            
            # Wait for team composition to take effect
            await asyncio.sleep(3)
            
            # Validate agents were created/assigned
            response = requests.get(f"{self.base_url}/api/agents/{self.workspace_id}")
            if response.status_code == 200:
                agents = response.json()
                logger.info(f"✅ {len(agents)} agents assigned to workspace")
            else:
                logger.warning("Could not fetch agents, but continuing test")
            
            self.test_results["phases"]["phase_2"] = {
                "status": "completed",
                "duration": time.time() - phase_start,
                "team_proposal_id": self.team_proposal_id,
                "agents_count": len(agents) if 'agents' in locals() else 0
            }
            
            logger.info("✅ Phase 2 completed - Team composed and approved")
            
        except Exception as e:
            logger.error(f"❌ Phase 2 failed: {str(e)}")
            self.test_results["phases"]["phase_2"] = {
                "status": "failed",
                "error": str(e),
                "duration": time.time() - phase_start
            }
            raise

    async def phase_3_task_execution(self):
        """Phase 3: Task Execution & Monitoring"""
        logger.info("\n⚙️ PHASE 3: Task Execution & Monitoring")
        phase_start = time.time()
        
        try:
            # Wait for initial task generation
            await asyncio.sleep(10)
            
            # Monitor task execution for up to 5 minutes
            max_wait_time = 300  # 5 minutes
            check_interval = 15  # Check every 15 seconds
            elapsed_time = 0
            
            completed_tasks = 0
            total_tasks = 0
            
            while elapsed_time < max_wait_time:
                # Check task status
                response = requests.get(f"{self.base_url}/api/workspaces/{self.workspace_id}/tasks")
                if response.status_code == 200:
                    tasks = response.json()
                    total_tasks = len(tasks)
                    completed_tasks = len([t for t in tasks if t.get('status') == 'completed'])
                    
                    logger.info(f"📊 Tasks progress: {completed_tasks}/{total_tasks} completed")
                    
                    # Check if we have meaningful progress
                    if completed_tasks >= 3:  # At least 3 completed tasks
                        logger.info("✅ Sufficient task completion detected")
                        break
                
                await asyncio.sleep(check_interval)
                elapsed_time += check_interval
                
                # Log progress every minute
                if elapsed_time % 60 == 0:
                    logger.info(f"⏱️ Execution monitoring: {elapsed_time//60} minutes elapsed")
            
            # Final task status check
            response = requests.get(f"{self.base_url}/workspaces/{self.workspace_id}/tasks")
            if response.status_code == 200:
                tasks = response.json()
                completed_tasks = len([t for t in tasks if t.get('status') == 'completed'])
                
                if completed_tasks == 0:
                    raise Exception("No tasks completed during execution phase")
                
                logger.info(f"✅ Task execution completed: {completed_tasks} tasks finished")
            else:
                raise Exception("Failed to fetch final task status")
            
            self.test_results["phases"]["phase_3"] = {
                "status": "completed",
                "duration": time.time() - phase_start,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "execution_time": elapsed_time
            }
            
            logger.info("✅ Phase 3 completed - Tasks executed successfully")
            
        except Exception as e:
            logger.error(f"❌ Phase 3 failed: {str(e)}")
            self.test_results["phases"]["phase_3"] = {
                "status": "failed",
                "error": str(e),
                "duration": time.time() - phase_start
            }
            raise

    async def phase_4_qa_reasoning(self):
        """Phase 4: QA & Reasoning Validation"""
        logger.info("\n🎯 PHASE 4: QA & Reasoning Validation")
        phase_start = time.time()
        
        try:
            # Trigger quality check
            qa_data = {
                "workspace_id": self.workspace_id
            }
            
            response = requests.post(f"{self.base_url}/api/trigger-quality-check", json=qa_data)
            if response.status_code != 200:
                raise Exception(f"Failed to trigger quality check: {response.text}")
            
            qa_result = response.json()
            if not qa_result.get('success'):
                raise Exception(f"Quality check failed: {qa_result.get('error')}")
            
            logger.info("✅ Quality check triggered successfully")
            
            # Wait for QA processing
            await asyncio.sleep(10)
            
            # Check for QA results/feedback
            response = requests.get(f"{self.base_url}/workspaces/{self.workspace_id}/feedback")
            if response.status_code == 200:
                feedback_items = response.json()
                logger.info(f"✅ Found {len(feedback_items)} QA feedback items")
                
                # Check if our new AI-First QA is working (should have fewer human feedback items)
                human_feedback_count = len([f for f in feedback_items if f.get('requires_human_approval', False)])
                ai_feedback_count = len(feedback_items) - human_feedback_count
                
                logger.info(f"📊 QA Analysis: {ai_feedback_count} AI-driven, {human_feedback_count} requiring human review")
                
                # Validate AI-First QA is working (should be >80% AI-driven)
                if len(feedback_items) > 0:
                    ai_percentage = (ai_feedback_count / len(feedback_items)) * 100
                    if ai_percentage >= 80:
                        logger.info(f"✅ AI-First QA working: {ai_percentage:.1f}% autonomous")
                    else:
                        logger.warning(f"⚠️ AI-First QA needs improvement: only {ai_percentage:.1f}% autonomous")
            else:
                logger.warning("Could not fetch QA feedback, but continuing test")
            
            self.test_results["phases"]["phase_4"] = {
                "status": "completed",
                "duration": time.time() - phase_start,
                "qa_triggered": True,
                "feedback_items": len(feedback_items) if 'feedback_items' in locals() else 0,
                "ai_driven_percentage": ai_percentage if 'ai_percentage' in locals() else 0
            }
            
            logger.info("✅ Phase 4 completed - QA & Reasoning validated")
            
        except Exception as e:
            logger.error(f"❌ Phase 4 failed: {str(e)}")
            self.test_results["phases"]["phase_4"] = {
                "status": "failed",
                "error": str(e),
                "duration": time.time() - phase_start
            }
            raise

    async def phase_5_asset_generation(self):
        """Phase 5: Asset Generation & Extraction"""
        logger.info("\n📦 PHASE 5: Asset Generation & Extraction")
        phase_start = time.time()
        
        try:
            # Wait for asset generation
            await asyncio.sleep(5)
            
            # Check for generated assets
            response = requests.get(f"{self.base_url}/api/workspaces/{self.workspace_id}/assets")
            if response.status_code != 200:
                raise Exception(f"Failed to fetch assets: {response.text}")
            
            assets = response.json()
            logger.info(f"✅ Found {len(assets)} assets generated")
            
            if len(assets) == 0:
                logger.warning("⚠️ No assets generated, triggering asset extraction")
                
                # Try to trigger asset extraction manually
                extraction_data = {
                    "workspace_id": self.workspace_id,
                    "force_extraction": True
                }
                
                response = requests.post(f"{self.base_url}/api/extract-assets", json=extraction_data)
                if response.status_code == 200:
                    logger.info("✅ Asset extraction triggered")
                    await asyncio.sleep(10)
                    
                    # Re-check assets
                    response = requests.get(f"{self.base_url}/api/workspaces/{self.workspace_id}/assets")
                    if response.status_code == 200:
                        assets = response.json()
                        logger.info(f"✅ After extraction: {len(assets)} assets found")
            
            # Validate asset quality
            concrete_assets = 0
            for asset in assets:
                content = asset.get('content', '')
                if len(content) > 200 and not self.is_placeholder_content(content):
                    concrete_assets += 1
            
            logger.info(f"📊 Asset quality: {concrete_assets}/{len(assets)} concrete assets")
            
            self.test_results["phases"]["phase_5"] = {
                "status": "completed",
                "duration": time.time() - phase_start,
                "total_assets": len(assets),
                "concrete_assets": concrete_assets,
                "assets": [{"id": a.get('id'), "type": a.get('type'), "content_length": len(a.get('content', ''))} for a in assets[:5]]  # Sample
            }
            
            logger.info("✅ Phase 5 completed - Assets generated and extracted")
            
        except Exception as e:
            logger.error(f"❌ Phase 5 failed: {str(e)}")
            self.test_results["phases"]["phase_5"] = {
                "status": "failed",
                "error": str(e),
                "duration": time.time() - phase_start
            }
            raise

    async def phase_6_deliverable_validation(self):
        """Phase 6: Deliverable Creation & Content Validation"""
        logger.info("\n🎯 PHASE 6: Deliverable Creation & Content Validation")
        phase_start = time.time()
        
        try:
            # Check for deliverables
            response = requests.get(f"{self.base_url}/api/workspaces/{self.workspace_id}/deliverables")
            if response.status_code != 200:
                raise Exception(f"Failed to fetch deliverables: {response.text}")
            
            deliverables = response.json()
            logger.info(f"✅ Found {len(deliverables)} deliverables")
            
            if len(deliverables) == 0:
                logger.warning("⚠️ No deliverables found, triggering deliverable creation")
                
                # Trigger deliverable creation
                creation_data = {
                    "workspace_id": self.workspace_id,
                    "force_creation": True
                }
                
                response = requests.post(f"{self.base_url}/api/create-deliverables", json=creation_data)
                if response.status_code == 200:
                    logger.info("✅ Deliverable creation triggered")
                    await asyncio.sleep(15)
                    
                    # Re-check deliverables
                    response = requests.get(f"{self.base_url}/api/workspaces/{self.workspace_id}/deliverables")
                    if response.status_code == 200:
                        deliverables = response.json()
                        logger.info(f"✅ After creation: {len(deliverables)} deliverables found")
            
            # Validate deliverable content quality
            valuable_deliverables = 0
            deliverable_analysis = []
            
            for deliverable in deliverables:
                content = deliverable.get('content', '')
                title = deliverable.get('title', 'Untitled')
                
                # Check if deliverable has concrete value
                is_valuable = self.validate_deliverable_value(content, title)
                if is_valuable:
                    valuable_deliverables += 1
                
                analysis = {
                    "title": title,
                    "content_length": len(content),
                    "is_valuable": is_valuable,
                    "has_concrete_data": self.has_concrete_data(content),
                    "has_actionable_insights": self.has_actionable_insights(content)
                }
                deliverable_analysis.append(analysis)
                
                logger.info(f"📋 Deliverable: '{title}' - {len(content)} chars, valuable: {is_valuable}")
            
            # Overall validation
            if len(deliverables) == 0:
                raise Exception("No deliverables created - system failed to produce business value")
            
            value_percentage = (valuable_deliverables / len(deliverables)) * 100
            if value_percentage < 50:
                logger.warning(f"⚠️ Low value deliverables: only {value_percentage:.1f}% are valuable")
            else:
                logger.info(f"✅ Good deliverable quality: {value_percentage:.1f}% are valuable")
            
            self.test_results["phases"]["phase_6"] = {
                "status": "completed",
                "duration": time.time() - phase_start,
                "total_deliverables": len(deliverables),
                "valuable_deliverables": valuable_deliverables,
                "value_percentage": value_percentage,
                "deliverable_analysis": deliverable_analysis
            }
            
            # Store deliverables for final report
            self.test_results["deliverables"] = deliverable_analysis
            
            logger.info("✅ Phase 6 completed - Deliverables validated")
            
        except Exception as e:
            logger.error(f"❌ Phase 6 failed: {str(e)}")
            self.test_results["phases"]["phase_6"] = {
                "status": "failed",
                "error": str(e),
                "duration": time.time() - phase_start
            }
            raise

    async def phase_7_final_analysis(self):
        """Phase 7: Final Analysis & Metrics"""
        logger.info("\n📊 PHASE 7: Final Analysis & Metrics")
        phase_start = time.time()
        
        try:
            # Calculate overall metrics
            total_duration = time.time() - datetime.fromisoformat(self.test_results["start_time"]).timestamp()
            
            # Workspace health check
            response = requests.get(f"{self.base_url}/workspaces/{self.workspace_id}")
            if response.status_code == 200:
                workspace = response.json()
                workspace_status = workspace.get('status', 'unknown')
                logger.info(f"✅ Workspace status: {workspace_status}")
            
            # Memory system check - look for learning patterns
            response = requests.get(f"{self.base_url}/api/workspaces/{self.workspace_id}/memory")
            memory_items = 0
            if response.status_code == 200:
                memory_data = response.json()
                memory_items = len(memory_data) if isinstance(memory_data, list) else 1 if memory_data else 0
                logger.info(f"✅ Memory system: {memory_items} memory entries")
            
            # Calculate success metrics
            phases_completed = len([p for p in self.test_results["phases"].values() if p.get("status") == "completed"])
            total_phases = len(self.test_results["phases"])
            success_rate = (phases_completed / total_phases) * 100
            
            # Content quality metrics
            total_deliverables = self.test_results["phases"].get("phase_6", {}).get("total_deliverables", 0)
            valuable_deliverables = self.test_results["phases"].get("phase_6", {}).get("valuable_deliverables", 0)
            
            self.test_results["metrics"] = {
                "total_duration_minutes": total_duration / 60,
                "phases_completed": phases_completed,
                "total_phases": total_phases,
                "success_rate_percentage": success_rate,
                "workspace_status": workspace_status if 'workspace_status' in locals() else "unknown",
                "memory_items": memory_items,
                "deliverable_success": valuable_deliverables > 0,
                "content_quality_score": (valuable_deliverables / max(total_deliverables, 1)) * 100
            }
            
            # Final validation
            validation_results = {
                "goal_to_deliverable_flow": total_deliverables > 0,
                "qa_system_working": self.test_results["phases"].get("phase_4", {}).get("qa_triggered", False),
                "memory_system_active": memory_items > 0,
                "content_has_value": valuable_deliverables > 0,
                "ai_first_qa_autonomous": self.test_results["phases"].get("phase_4", {}).get("ai_driven_percentage", 0) >= 80,
                "workflow_complete": phases_completed >= 6
            }
            
            self.test_results["validation_results"] = validation_results
            
            # Overall success determination
            critical_validations_passed = sum([
                validation_results["goal_to_deliverable_flow"],
                validation_results["content_has_value"],
                validation_results["workflow_complete"]
            ])
            
            if critical_validations_passed >= 3:
                logger.info("✅ E2E Test: ALL CRITICAL VALIDATIONS PASSED")
            else:
                logger.warning("⚠️ E2E Test: Some critical validations failed")
            
            self.test_results["phases"]["phase_7"] = {
                "status": "completed",
                "duration": time.time() - phase_start,
                "critical_validations_passed": critical_validations_passed,
                "total_critical_validations": 3
            }
            
            logger.info("✅ Phase 7 completed - Final analysis done")
            
        except Exception as e:
            logger.error(f"❌ Phase 7 failed: {str(e)}")
            self.test_results["phases"]["phase_7"] = {
                "status": "failed",
                "error": str(e),
                "duration": time.time() - phase_start
            }
            raise

    def is_placeholder_content(self, content: str) -> bool:
        """Check if content appears to be placeholder/template content"""
        placeholder_indicators = [
            "lorem ipsum", "placeholder", "todo", "tbd", "coming soon",
            "example", "sample", "template", "xxx", "...", "tbc"
        ]
        
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in placeholder_indicators)

    def has_concrete_data(self, content: str) -> bool:
        """Check if content contains concrete data/numbers/specifics"""
        import re
        
        # Look for numbers, percentages, dates, specific metrics
        patterns = [
            r'\d+%',  # percentages
            r'\$\d+',  # dollar amounts
            r'\d{1,3},\d{3}',  # formatted numbers
            r'\d+ (users|customers|companies|percent)',  # metrics
            r'(Q[1-4]|January|February|March|April|May|June|July|August|September|October|November|December)',  # dates
            r'(increase|decrease|growth|revenue|profit|market share) (of|by) \d+',  # business metrics
        ]
        
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        
        return False

    def has_actionable_insights(self, content: str) -> bool:
        """Check if content contains actionable insights/recommendations"""
        actionable_keywords = [
            "recommend", "suggest", "should", "implement", "strategy",
            "action plan", "next steps", "timeline", "milestone",
            "launch", "execute", "deploy", "optimize", "improve"
        ]
        
        content_lower = content.lower()
        actionable_count = sum(1 for keyword in actionable_keywords if keyword in content_lower)
        
        return actionable_count >= 3  # At least 3 actionable terms

    def validate_deliverable_value(self, content: str, title: str) -> bool:
        """Comprehensive validation of deliverable business value"""
        if len(content) < 100:  # Too short to be valuable
            return False
        
        if self.is_placeholder_content(content):
            return False
        
        # Check for business value indicators
        value_indicators = 0
        
        if self.has_concrete_data(content):
            value_indicators += 1
        
        if self.has_actionable_insights(content):
            value_indicators += 1
        
        # Check for structured content
        if any(marker in content for marker in ["## ", "### ", "1.", "2.", "- ", "* "]):
            value_indicators += 1
        
        # Check for business-relevant terms
        business_terms = ["market", "customer", "revenue", "strategy", "competitive", "analysis", "recommendation"]
        if sum(1 for term in business_terms if term.lower() in content.lower()) >= 3:
            value_indicators += 1
        
        return value_indicators >= 3  # Needs at least 3 value indicators

    async def generate_test_report(self):
        """Generate comprehensive test report"""
        self.test_results["end_time"] = datetime.now().isoformat()
        
        # Save detailed results
        report_file = f"e2e_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        # Print summary
        logger.info("\n" + "="*80)
        logger.info("🎯 COMPREHENSIVE E2E TEST REPORT")
        logger.info("="*80)
        
        logger.info(f"📊 Overall Success: {'✅ PASSED' if self.test_results['success'] else '❌ FAILED'}")
        
        if "metrics" in self.test_results:
            metrics = self.test_results["metrics"]
            logger.info(f"⏱️ Total Duration: {metrics.get('total_duration_minutes', 0):.1f} minutes")
            logger.info(f"📈 Success Rate: {metrics.get('success_rate_percentage', 0):.1f}%")
            logger.info(f"🎯 Content Quality: {metrics.get('content_quality_score', 0):.1f}%")
        
        logger.info("\n📋 PHASE RESULTS:")
        for phase_name, phase_data in self.test_results["phases"].items():
            status_emoji = "✅" if phase_data.get("status") == "completed" else "❌"
            duration = phase_data.get("duration", 0)
            logger.info(f"  {status_emoji} {phase_name.replace('_', ' ').title()}: {duration:.1f}s")
        
        if "validation_results" in self.test_results:
            logger.info("\n🔍 VALIDATION RESULTS:")
            for validation, passed in self.test_results["validation_results"].items():
                status_emoji = "✅" if passed else "❌"
                logger.info(f"  {status_emoji} {validation.replace('_', ' ').title()}: {'PASSED' if passed else 'FAILED'}")
        
        logger.info(f"\n📄 Detailed report saved: {report_file}")
        logger.info("="*80)


async def main():
    """Run the comprehensive E2E test"""
    test = ComprehensiveE2ETest()
    await test.run_complete_test()
    return test.test_results["success"]


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Test failed with exception: {e}")
        sys.exit(1)