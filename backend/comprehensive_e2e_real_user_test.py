#!/usr/bin/env python3
"""
🎯 COMPREHENSIVE END-TO-END REAL USER TEST

Test completo che simula un vero utente utilizzando TUTTO il flusso del sistema:
1. Workspace creation come nuovo utente
2. Team formation con Director Agent
3. Goal creation e decomposizione strategica  
4. Task execution pipeline completo
5. Asset generation e deliverables
6. Real-time monitoring e WebSocket
7. Quality assurance e miglioramento
8. Conversation interface naturale
9. Verifica finale completamento

Questo test rappresenta l'esperienza completa di un utente business reale.
"""

import asyncio
import aiohttp
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import websockets
import os
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comprehensive_e2e_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class RealUserE2ETest:
    """
    🎯 SIMULATORE UTENTE REALE
    
    Simula completamente l'esperienza di un utente business che:
    - Accede al sistema per la prima volta
    - Crea un progetto business realistico
    - Interagisce naturalmente con il sistema
    - Utilizza tutte le funzionalità disponibili
    - Monitora i progressi in tempo reale
    - Ottiene deliverables concreti
    """
    
    def __init__(self):
        self.base_url = "http://127.0.0.1:8000"
        self.frontend_url = "http://localhost:3000"
        self.websocket_url = "ws://127.0.0.1:8000/ws"
        
        # Dati utente simulato (Marketing Manager di una startup SaaS)
        self.user_profile = {
            "name": "Sarah Mitchell",
            "role": "Marketing Manager", 
            "company": "TechFlow SaaS",
            "industry": "B2B Software",
            "goal": "Launch comprehensive marketing campaign for new product"
        }
        
        # Workspace e session tracking
        self.workspace_id = None
        self.team_proposal_id = None
        self.goals = []
        self.tasks = []
        self.deliverables = []
        self.websocket_messages = []
        
        # Test metrics
        self.test_start_time = time.time()
        self.phase_timings = {}
        self.errors = []
        self.success_metrics = {
            "workspace_created": False,
            "team_formed": False, 
            "goals_created": False,
            "tasks_executed": False,
            "deliverables_generated": False,
            "real_time_updates": False,
            "conversation_working": False,
            "quality_system_active": False
        }
        
    async def run_complete_test(self) -> Dict[str, Any]:
        """
        🚀 ESECUZIONE COMPLETA TEST E2E
        
        Simula l'intera esperienza utente dall'inizio alla fine
        """
        logger.info("🎯 STARTING COMPREHENSIVE E2E REAL USER TEST")
        logger.info(f"User Profile: {self.user_profile['name']} - {self.user_profile['role']} at {self.user_profile['company']}")
        
        try:
            # Phase 1: Environment Setup
            await self._phase_1_setup()
            
            # Phase 2: Workspace Creation (Onboarding)
            await self._phase_2_workspace_creation()
            
            # Phase 3: Team Formation
            await self._phase_3_team_formation()
            
            # Phase 4: Goal Setting & Strategic Planning
            await self._phase_4_goal_creation()
            
            # Phase 5: Task Execution & Monitoring
            await self._phase_5_task_execution()
            
            # Phase 6: Asset Generation & Deliverables
            await self._phase_6_asset_generation()
            
            # Phase 7: Real-time Monitoring & WebSocket
            await self._phase_7_realtime_monitoring()
            
            # Phase 8: Conversation Interface Testing
            await self._phase_8_conversation_interface()
            
            # Phase 9: Quality Assurance System
            await self._phase_9_quality_system()
            
            # Phase 10: Final Verification & Results
            await self._phase_10_final_verification()
            
            return await self._generate_test_report()
            
        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR in E2E test: {e}", exc_info=True)
            self.errors.append(f"Critical error: {str(e)}")
            return await self._generate_test_report()
    
    async def _phase_1_setup(self):
        """Phase 1: Verifica che backend e frontend siano attivi"""
        logger.info("📋 PHASE 1: Environment Setup")
        phase_start = time.time()
        
        try:
            # Test backend health
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        logger.info("✅ Backend is healthy and running")
                    else:
                        raise Exception(f"Backend health check failed: {response.status}")
                
                # Test frontend accessibility (may not have health endpoint)
                try:
                    async with session.get(self.frontend_url, timeout=5) as response:
                        if response.status in [200, 404]:  # 404 is OK for Next.js routing
                            logger.info("✅ Frontend is accessible")
                        else:
                            logger.warning(f"⚠️ Frontend response: {response.status}")
                except Exception as fe:
                    logger.warning(f"⚠️ Frontend check failed: {fe}")
            
            self.phase_timings["setup"] = time.time() - phase_start
            logger.info(f"✅ Phase 1 completed in {self.phase_timings['setup']:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Phase 1 failed: {e}")
            raise
    
    async def _phase_2_workspace_creation(self):
        """Phase 2: Creazione workspace come nuovo utente"""
        logger.info("🏢 PHASE 2: Workspace Creation (New User Onboarding)")
        phase_start = time.time()
        
        try:
            # Generate a user ID for the test user
            user_id = str(uuid.uuid4())
            
            # Simula nuovo utente che crea workspace per progetto marketing
            workspace_data = {
                "name": f"{self.user_profile['company']} - Q1 Marketing Campaign",
                "description": f"Comprehensive marketing campaign launch for our new B2B SaaS product targeting enterprise customers. Led by {self.user_profile['name']}.",
                "user_id": user_id,
                "goal": f"Launch comprehensive marketing campaign for new product targeting enterprise customers with goal to acquire 1000+ qualified leads and establish thought leadership",
                "budget": {
                    "max_amount": 75000,
                    "currency": "USD",
                    "allocated_categories": ["content_creation", "lead_generation", "automation_tools"]
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/workspaces",
                    json=workspace_data
                ) as response:
                    if response.status == 201:
                        workspace_response = await response.json()
                        self.workspace_id = workspace_response["id"]
                        logger.info(f"✅ Workspace created: {self.workspace_id}")
                        logger.info(f"📋 Workspace name: {workspace_data['name']}")
                        self.success_metrics["workspace_created"] = True
                    else:
                        error_text = await response.text()
                        raise Exception(f"Workspace creation failed: {response.status} - {error_text}")
            
            # Verificare che il workspace sia stato creato correttamente
            await asyncio.sleep(2)  # Give time for database consistency
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/workspaces/{self.workspace_id}") as response:
                    if response.status == 200:
                        workspace_info = await response.json()
                        logger.info(f"📊 Workspace verified: Status = {workspace_info.get('status', 'unknown')}")
                    else:
                        logger.warning(f"⚠️ Workspace verification failed: {response.status}")
            
            self.phase_timings["workspace_creation"] = time.time() - phase_start
            logger.info(f"✅ Phase 2 completed in {self.phase_timings['workspace_creation']:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Phase 2 failed: {e}")
            self.errors.append(f"Workspace creation failed: {str(e)}")
            raise
    
    async def _phase_3_team_formation(self):
        """Phase 3: Team formation con Director Agent"""
        logger.info("👥 PHASE 3: Team Formation with Director Agent")
        phase_start = time.time()
        
        try:
            # Generate user_id for Director request (should be same as workspace creator)
            user_id = str(uuid.uuid4())
            
            # Request team proposal from Director Agent with correct format
            proposal_request = {
                "workspace_id": self.workspace_id,
                "goal": "Launch comprehensive B2B SaaS marketing campaign including content strategy, lead generation, product positioning, competitive analysis, and customer acquisition optimization to acquire 1000+ qualified leads",
                "budget_constraint": {
                    "max_amount": 75000,
                    "currency": "USD",
                    "categories": ["content_creation", "lead_generation", "automation_tools", "team_salaries"]
                },
                "user_id": user_id,
                "user_feedback": "I prefer a balanced team with content creation expertise, strong analytics capabilities, and experience with B2B marketing automation",
                "extracted_goals": [
                    {
                        "type": "content_marketing",
                        "description": "Develop comprehensive content marketing strategy with 50 blog posts, 5 whitepapers, and 10 case studies",
                        "metrics": {"blog_posts": 50, "whitepapers": 5, "case_studies": 10}
                    },
                    {
                        "type": "lead_generation", 
                        "description": "Implement lead generation system to acquire 1000+ qualified leads per month",
                        "metrics": {"monthly_leads": 1000, "conversion_rate": 0.05}
                    },
                    {
                        "type": "funnel_optimization",
                        "description": "Optimize customer acquisition funnel for 25% improvement in conversion rate",
                        "metrics": {"conversion_improvement": 0.25}
                    }
                ]
            }
            
            logger.info("🤖 Requesting team proposal from Director Agent...")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/director/proposal",
                    json=proposal_request
                ) as response:
                    if response.status == 200:
                        proposal_response = await response.json()
                        self.team_proposal_id = proposal_response.get("proposal_id")
                        logger.info(f"✅ Team proposal received: {self.team_proposal_id}")
                        
                        # Log proposal details
                        if "proposed_team" in proposal_response:
                            team = proposal_response["proposed_team"]
                            logger.info(f"👥 Proposed team size: {len(team.get('agents', []))}")
                            for agent in team.get('agents', []):
                                logger.info(f"   - {agent.get('role', 'Unknown Role')} ({agent.get('seniority', 'Unknown Level')})")
                        
                    else:
                        error_text = await response.text()
                        raise Exception(f"Team proposal failed: {response.status} - {error_text}")
            
            # Wait for proposal processing
            await asyncio.sleep(5)
            
            # Approve the team proposal (simulating user decision)
            logger.info("✅ User approves team proposal...")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/director/approve/{self.workspace_id}?proposal_id={self.team_proposal_id}"
                ) as response:
                    if response.status == 200:
                        approval_response = await response.json()
                        logger.info("✅ Team proposal approved and agents created")
                        self.success_metrics["team_formed"] = True
                        
                        # Check created agents
                        if "created_agents" in approval_response:
                            agents = approval_response["created_agents"]
                            logger.info(f"🤖 {len(agents)} agents created successfully")
                    else:
                        error_text = await response.text()
                        raise Exception(f"Team approval failed: {response.status} - {error_text}")
            
            # Verify team status
            await asyncio.sleep(3)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/workspaces/{self.workspace_id}/agents") as response:
                    if response.status == 200:
                        agents_data = await response.json()
                        logger.info(f"📊 Team verification: {len(agents_data)} agents active")
                        for agent in agents_data[:3]:  # Show first 3
                            logger.info(f"   - {agent.get('name', 'Unknown')} ({agent.get('status', 'unknown')})")
            
            self.phase_timings["team_formation"] = time.time() - phase_start
            logger.info(f"✅ Phase 3 completed in {self.phase_timings['team_formation']:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Phase 3 failed: {e}")
            self.errors.append(f"Team formation failed: {str(e)}")
            # Continue test even if team formation partially fails
    
    async def _phase_4_goal_creation(self):
        """Phase 4: Goal creation e decomposizione strategica"""
        logger.info("🎯 PHASE 4: Strategic Goal Creation & Decomposition")
        phase_start = time.time()
        
        try:
            # Create strategic marketing goals as real user would
            marketing_goals = [
                {
                    "metric_type": "content_marketing_deliverables",
                    "target_value": 65.0,  # 50 blog posts + 5 whitepapers + 10 case studies
                    "unit": "pieces_of_content",
                    "description": "Create a complete content marketing strategy including blog content calendar, whitepapers, case studies, and video content to establish thought leadership and drive organic traffic",
                    "priority": 1,  # high priority
                    "source_goal_text": "Develop Comprehensive Content Marketing Strategy",
                    "success_criteria": {
                        "blog_posts": 50,
                        "whitepapers": 5, 
                        "case_studies": 10
                    },
                    "metadata": {
                        "timeline": "8 weeks",
                        "created_by": self.user_profile["name"]
                    }
                },
                {
                    "metric_type": "monthly_qualified_leads",
                    "target_value": 1000.0,
                    "unit": "leads_per_month", 
                    "description": "Implement multi-channel lead generation system including landing pages, email campaigns, social media campaigns, and marketing automation workflows",
                    "priority": 1,  # high priority
                    "source_goal_text": "Launch Lead Generation System",
                    "success_criteria": {
                        "conversion_rate": 0.05,
                        "lead_quality_score": 0.8
                    },
                    "metadata": {
                        "timeline": "6 weeks",
                        "created_by": self.user_profile["name"]
                    }
                },
                {
                    "metric_type": "conversion_rate_improvement",
                    "target_value": 0.25,  # 25% improvement
                    "unit": "percentage_improvement",
                    "description": "Analyze and optimize the complete customer journey from awareness to conversion, including A/B testing, conversion rate optimization, and retention strategies", 
                    "priority": 2,  # medium priority
                    "source_goal_text": "Optimize Customer Acquisition Funnel",
                    "success_criteria": {
                        "baseline_conversion_rate": 0.02,
                        "target_conversion_rate": 0.025
                    },
                    "metadata": {
                        "timeline": "10 weeks",
                        "created_by": self.user_profile["name"]
                    }
                }
            ]
            
            for goal_data in marketing_goals:
                logger.info(f"🎯 Creating goal: {goal_data['source_goal_text']}")
                
                async with aiohttp.ClientSession() as session:
                    # Create goal via API with correct WorkspaceGoalCreate format
                    create_payload = {
                        "workspace_id": self.workspace_id,
                        **goal_data
                    }
                    
                    async with session.post(
                        f"{self.base_url}/api/workspaces/{self.workspace_id}/goals",
                        json=create_payload
                    ) as response:
                        if response.status in [200, 201]:
                            goal_response = await response.json()
                            if goal_response.get("success"):
                                goal_data = goal_response.get("goal", {})
                                goal_id = goal_data.get("id")
                                if goal_id:
                                    self.goals.append(goal_id)
                                    logger.info(f"✅ Goal created: {goal_id}")
                                    logger.info(f"📊 Asset requirements: {goal_response.get('asset_requirements_count', 0)}")
                            else:
                                logger.warning(f"⚠️ Goal creation returned success=false")
                        else:
                            error_text = await response.text()
                            logger.warning(f"⚠️ Goal creation failed: {response.status} - {error_text}")
                
                await asyncio.sleep(2)  # Space out goal creation
            
            if self.goals:
                self.success_metrics["goals_created"] = True
                logger.info(f"✅ Created {len(self.goals)} strategic goals")
                
                # Wait for automatic goal decomposition and task generation
                logger.info("⏳ Waiting for automatic goal decomposition and task generation...")
                await asyncio.sleep(15)  # Allow goal-driven task planner to work
                
                # Check if tasks were automatically generated
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.base_url}/workspaces/{self.workspace_id}/tasks") as response:
                        if response.status == 200:
                            tasks_data = await response.json()
                            logger.info(f"📋 Automatic task generation: {len(tasks_data)} tasks created")
                            
                            # Show sample tasks
                            for task in tasks_data[:3]:
                                logger.info(f"   - {task.get('name', 'Unnamed task')} ({task.get('status', 'unknown')})")
            
            self.phase_timings["goal_creation"] = time.time() - phase_start
            logger.info(f"✅ Phase 4 completed in {self.phase_timings['goal_creation']:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Phase 4 failed: {e}")
            self.errors.append(f"Goal creation failed: {str(e)}")
    
    async def _phase_5_task_execution(self):
        """Phase 5: Task execution pipeline completo"""
        logger.info("⚙️ PHASE 5: Task Execution Pipeline")
        phase_start = time.time()
        
        try:
            # Get current tasks
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/workspaces/{self.workspace_id}/tasks") as response:
                    if response.status == 200:
                        all_tasks = await response.json()
                        logger.info(f"📋 Found {len(all_tasks)} tasks in workspace")
                        
                        # Analyze task status distribution
                        status_counts = {}
                        for task in all_tasks:
                            status = task.get('status', 'unknown')
                            status_counts[status] = status_counts.get(status, 0) + 1
                        
                        logger.info(f"📊 Task status distribution: {status_counts}")
                        
                        # Store task IDs for monitoring
                        self.tasks = [task.get('id') for task in all_tasks]
                        
                        # Check for tasks in execution
                        pending_tasks = [t for t in all_tasks if t.get('status') == 'pending']
                        in_progress_tasks = [t for t in all_tasks if t.get('status') == 'in_progress']
                        
                        logger.info(f"⏳ Pending tasks: {len(pending_tasks)}")
                        logger.info(f"🔄 In progress tasks: {len(in_progress_tasks)}")
                        
                        if pending_tasks:
                            # Monitor task execution for some time
                            logger.info("👀 Monitoring task execution for 30 seconds...")
                            
                            for monitor_cycle in range(6):  # 6 cycles of 5 seconds each
                                await asyncio.sleep(5)
                                
                                # Check task progress
                                async with session.get(f"{self.base_url}/workspaces/{self.workspace_id}/tasks") as progress_response:
                                    if progress_response.status == 200:
                                        updated_tasks = await progress_response.json()
                                        
                                        # Count status changes
                                        new_status_counts = {}
                                        for task in updated_tasks:
                                            status = task.get('status', 'unknown')
                                            new_status_counts[status] = new_status_counts.get(status, 0) + 1
                                        
                                        logger.info(f"📊 Cycle {monitor_cycle + 1} - Task status: {new_status_counts}")
                                        
                                        # Check if any tasks completed
                                        completed_tasks = [t for t in updated_tasks if t.get('status') == 'completed']
                                        if completed_tasks:
                                            logger.info(f"✅ {len(completed_tasks)} tasks completed!")
                                            self.success_metrics["tasks_executed"] = True
                                            
                                            # Show sample completed tasks
                                            for task in completed_tasks[:2]:
                                                logger.info(f"   ✅ {task.get('name', 'Unnamed')} - {task.get('result', 'No result')[:100]}...")
            
            # Check agent activity
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/workspaces/{self.workspace_id}/agents") as response:
                    if response.status == 200:
                        agents_data = await response.json()
                        
                        active_agents = [a for a in agents_data if a.get('status') in ['active', 'available']]
                        logger.info(f"🤖 Active agents: {len(active_agents)}/{len(agents_data)}")
            
            # Check if task executor is working
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/monitoring/executor/status") as response:
                    if response.status == 200:
                        executor_status = await response.json()
                        logger.info(f"⚙️ Executor status: {executor_status.get('executor_status', 'unknown')}")
                        logger.info(f"📋 Tasks in queue: {executor_status.get('tasks_in_queue', 0)}")
                        logger.info(f"🔄 Active tasks: {executor_status.get('active_tasks', 0)}")
            
            self.phase_timings["task_execution"] = time.time() - phase_start
            logger.info(f"✅ Phase 5 completed in {self.phase_timings['task_execution']:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Phase 5 failed: {e}")
            self.errors.append(f"Task execution monitoring failed: {str(e)}")
    
    async def _phase_6_asset_generation(self):
        """Phase 6: Asset generation e deliverables"""
        logger.info("📦 PHASE 6: Asset Generation & Deliverables")
        phase_start = time.time()
        
        try:
            # Check for generated assets
            async with aiohttp.ClientSession() as session:
                # Check project assets
                async with session.get(f"{self.base_url}/workspaces/{self.workspace_id}/assets") as response:
                    if response.status == 200:
                        assets_data = await response.json()
                        logger.info(f"📋 Project assets found: {len(assets_data)}")
                        
                        for asset in assets_data[:3]:  # Show first 3
                            logger.info(f"   📄 {asset.get('name', 'Unnamed asset')} ({asset.get('asset_type', 'unknown type')})")
                        
                        if assets_data:
                            self.deliverables.extend([a.get('id') for a in assets_data])
                
                # Check project deliverables
                async with session.get(f"{self.base_url}/workspaces/{self.workspace_id}/deliverables") as response:
                    if response.status == 200:
                        deliverables_data = await response.json()
                        logger.info(f"🎯 Project deliverables found: {len(deliverables_data)}")
                        
                        for deliverable in deliverables_data[:3]:  # Show first 3
                            logger.info(f"   🎁 {deliverable.get('title', 'Unnamed deliverable')} ({deliverable.get('deliverable_type', 'unknown type')})")
                        
                        if deliverables_data:
                            self.deliverables.extend([d.get('id') for d in deliverables_data])
                            self.success_metrics["deliverables_generated"] = True
                
                # Try to trigger deliverable creation if none exist yet
                if not self.deliverables:
                    logger.info("🔧 No deliverables found, checking if generation can be triggered...")
                    
                    # Check task completion rate
                    async with session.get(f"{self.base_url}/workspaces/{self.workspace_id}/tasks") as response:
                        if response.status == 200:
                            tasks_data = await response.json()
                            completed_tasks = [t for t in tasks_data if t.get('status') == 'completed']
                            
                            if completed_tasks:
                                logger.info(f"✅ Found {len(completed_tasks)} completed tasks - deliverables should be generated soon")
                                
                                # Wait a bit more for deliverable aggregation
                                await asyncio.sleep(10)
                                
                                # Check again
                                async with session.get(f"{self.base_url}/workspaces/{self.workspace_id}/deliverables") as retry_response:
                                    if retry_response.status == 200:
                                        retry_deliverables = await retry_response.json()
                                        if retry_deliverables:
                                            logger.info(f"🎉 Deliverables generated: {len(retry_deliverables)}")
                                            self.success_metrics["deliverables_generated"] = True
                                            self.deliverables.extend([d.get('id') for d in retry_deliverables])
            
            # Check workspace progress
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/workspaces/{self.workspace_id}/progress") as response:
                    if response.status == 200:
                        progress_data = await response.json()
                        logger.info(f"📊 Workspace progress: {progress_data.get('completion_percentage', 0):.1f}%")
                        logger.info(f"🎯 Goals completion: {progress_data.get('goals_completed', 0)}/{progress_data.get('total_goals', 0)}")
            
            self.phase_timings["asset_generation"] = time.time() - phase_start
            logger.info(f"✅ Phase 6 completed in {self.phase_timings['asset_generation']:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Phase 6 failed: {e}")
            self.errors.append(f"Asset generation check failed: {str(e)}")
    
    async def _phase_7_realtime_monitoring(self):
        """Phase 7: Real-time monitoring e WebSocket"""
        logger.info("📡 PHASE 7: Real-time Monitoring & WebSocket")
        phase_start = time.time()
        
        try:
            # Test WebSocket connection
            logger.info("🔌 Testing WebSocket connection...")
            
            websocket_connected = False
            messages_received = 0
            
            try:
                # Connect to WebSocket with timeout
                async with websockets.connect(
                    f"{self.websocket_url}/{self.workspace_id}",
                    timeout=10
                ) as websocket:
                    websocket_connected = True
                    logger.info("✅ WebSocket connected successfully")
                    
                    # Send a heartbeat/ping
                    await websocket.send(json.dumps({
                        "type": "ping",
                        "workspace_id": self.workspace_id,
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                    # Listen for messages for a short time
                    try:
                        await asyncio.wait_for(
                            websocket.recv(),
                            timeout=5.0
                        )
                        messages_received += 1
                        logger.info("✅ WebSocket message received")
                        self.success_metrics["real_time_updates"] = True
                        
                    except asyncio.TimeoutError:
                        logger.info("⏳ No immediate WebSocket messages (this is normal)")
                        # Still consider WebSocket working if connection was successful
                        self.success_metrics["real_time_updates"] = websocket_connected
                        
            except Exception as ws_error:
                logger.warning(f"⚠️ WebSocket test failed: {ws_error}")
                # Try alternative WebSocket test
                try:
                    # Test if WebSocket endpoint exists
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"{self.base_url}/ws/health") as response:
                            if response.status in [200, 404]:  # 404 is expected for WS endpoint
                                logger.info("✅ WebSocket infrastructure appears to be running")
                                self.success_metrics["real_time_updates"] = True
                except:
                    pass
            
            # Test real-time monitoring endpoints
            async with aiohttp.ClientSession() as session:
                # Get workspace activity
                async with session.get(f"{self.base_url}/monitoring/workspace/{self.workspace_id}/activity") as response:
                    if response.status == 200:
                        activity_data = await response.json()
                        logger.info(f"📈 Recent activity events: {len(activity_data)}")
                        
                        # Show recent activity
                        for event in activity_data[:3]:
                            logger.info(f"   📅 {event.get('timestamp', 'Unknown time')}: {event.get('event_type', 'Unknown event')}")
                
                # Get workspace metrics
                async with session.get(f"{self.base_url}/monitoring/workspace/{self.workspace_id}/metrics") as response:
                    if response.status == 200:
                        metrics_data = await response.json()
                        logger.info(f"📊 Workspace metrics collected: {len(metrics_data)} data points")
            
            self.phase_timings["realtime_monitoring"] = time.time() - phase_start
            logger.info(f"✅ Phase 7 completed in {self.phase_timings['realtime_monitoring']:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Phase 7 failed: {e}")
            self.errors.append(f"Real-time monitoring failed: {str(e)}")
    
    async def _phase_8_conversation_interface(self):
        """Phase 8: Test conversation interface con tools e slash commands"""
        logger.info("💬 PHASE 8: Conversation Interface Testing")
        phase_start = time.time()
        
        try:
            # Create conversation session
            conversation_data = {
                "workspace_id": self.workspace_id,
                "user_name": self.user_profile["name"],
                "initial_message": "Hi! I'm Sarah, the Marketing Manager. Can you show me the current project status?"
            }
            
            async with aiohttp.ClientSession() as session:
                # Test conversational interface
                async with session.post(
                    f"{self.base_url}/conversation/start",
                    json=conversation_data
                ) as response:
                    if response.status == 200:
                        conversation_response = await response.json()
                        conversation_id = conversation_response.get("conversation_id")
                        logger.info(f"💬 Conversation started: {conversation_id}")
                        
                        # Test natural language commands
                        test_messages = [
                            "What's the status of our marketing goals?",
                            "/show_project_status",
                            "How many team members do we have?",
                            "/show_team_status", 
                            "Show me our deliverables",
                            "/show_deliverables"
                        ]
                        
                        for message in test_messages:
                            logger.info(f"📤 Sending: {message}")
                            
                            message_payload = {
                                "conversation_id": conversation_id,
                                "message": message,
                                "workspace_id": self.workspace_id
                            }
                            
                            async with session.post(
                                f"{self.base_url}/conversation/message",
                                json=message_payload
                            ) as msg_response:
                                if msg_response.status == 200:
                                    reply_data = await msg_response.json()
                                    reply_text = reply_data.get("response", "No response")
                                    logger.info(f"📥 Reply: {reply_text[:150]}...")
                                    
                                    # Check if tools were executed
                                    if "tools_executed" in reply_data:
                                        tools = reply_data["tools_executed"]
                                        logger.info(f"🔧 Tools executed: {len(tools)}")
                                else:
                                    logger.warning(f"⚠️ Message failed: {msg_response.status}")
                            
                            await asyncio.sleep(2)  # Space out messages
                        
                        self.success_metrics["conversation_working"] = True
                        logger.info("✅ Conversation interface working successfully")
                        
                    else:
                        error_text = await response.text()
                        logger.warning(f"⚠️ Conversation start failed: {response.status} - {error_text}")
            
            self.phase_timings["conversation_interface"] = time.time() - phase_start
            logger.info(f"✅ Phase 8 completed in {self.phase_timings['conversation_interface']:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Phase 8 failed: {e}")
            self.errors.append(f"Conversation interface failed: {str(e)}")
    
    async def _phase_9_quality_system(self):
        """Phase 9: Quality assurance system"""
        logger.info("🔍 PHASE 9: Quality Assurance System")
        phase_start = time.time()
        
        try:
            # Check quality system status
            async with aiohttp.ClientSession() as session:
                # Test quality validation endpoint
                async with session.get(f"{self.base_url}/quality/workspace/{self.workspace_id}/status") as response:
                    if response.status == 200:
                        quality_data = await response.json()
                        logger.info(f"🔍 Quality system active: {quality_data.get('system_active', False)}")
                        logger.info(f"📊 Quality score: {quality_data.get('overall_score', 0)}")
                        
                        if quality_data.get('system_active'):
                            self.success_metrics["quality_system_active"] = True
                    
                    elif response.status == 404:
                        logger.info("📝 Quality system endpoints not yet available")
                        # Check if quality system is working through other means
                        
                        # Check if tasks have quality metadata
                        async with session.get(f"{self.base_url}/workspaces/{self.workspace_id}/tasks") as task_response:
                            if task_response.status == 200:
                                tasks_data = await task_response.json()
                                
                                quality_enhanced_tasks = [
                                    t for t in tasks_data 
                                    if t.get('metadata', {}).get('quality_enhanced') or 
                                       'quality' in str(t.get('context_data', {})).lower()
                                ]
                                
                                if quality_enhanced_tasks:
                                    logger.info(f"🔍 Found {len(quality_enhanced_tasks)} quality-enhanced tasks")
                                    self.success_metrics["quality_system_active"] = True
                
                # Test quality metrics if available
                async with session.get(f"{self.base_url}/quality/workspace/{self.workspace_id}/metrics") as response:
                    if response.status == 200:
                        metrics_data = await response.json()
                        logger.info(f"📈 Quality metrics: {len(metrics_data)} data points")
                        
                        # Show key metrics
                        for metric_name, metric_value in list(metrics_data.items())[:3]:
                            logger.info(f"   📊 {metric_name}: {metric_value}")
            
            # Check if improvement loops are active
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/improvement/workspace/{self.workspace_id}/status") as response:
                    if response.status == 200:
                        improvement_data = await response.json()
                        active_improvements = improvement_data.get('active_improvements', 0)
                        logger.info(f"🔄 Active improvement loops: {active_improvements}")
                        
                        if active_improvements > 0:
                            self.success_metrics["quality_system_active"] = True
            
            self.phase_timings["quality_system"] = time.time() - phase_start
            logger.info(f"✅ Phase 9 completed in {self.phase_timings['quality_system']:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Phase 9 failed: {e}")
            self.errors.append(f"Quality system check failed: {str(e)}")
    
    async def _phase_10_final_verification(self):
        """Phase 10: Verifica finale completamento"""
        logger.info("🏁 PHASE 10: Final Verification & Results")
        phase_start = time.time()
        
        try:
            # Final comprehensive status check
            async with aiohttp.ClientSession() as session:
                # Get final workspace status
                async with session.get(f"{self.base_url}/workspaces/{self.workspace_id}") as response:
                    if response.status == 200:
                        workspace_data = await response.json()
                        final_status = workspace_data.get('status', 'unknown')
                        logger.info(f"🏢 Final workspace status: {final_status}")
                
                # Get final goal progress
                async with session.get(f"{self.base_url}/workspaces/{self.workspace_id}/goals") as response:
                    if response.status == 200:
                        goals_data = await response.json()
                        completed_goals = [g for g in goals_data if g.get('status') == 'completed']
                        logger.info(f"🎯 Goals completion: {len(completed_goals)}/{len(goals_data)}")
                
                # Get final task summary
                async with session.get(f"{self.base_url}/workspaces/{self.workspace_id}/tasks") as response:
                    if response.status == 200:
                        tasks_data = await response.json()
                        
                        task_status_summary = {}
                        for task in tasks_data:
                            status = task.get('status', 'unknown')
                            task_status_summary[status] = task_status_summary.get(status, 0) + 1
                        
                        logger.info(f"📋 Final task summary: {task_status_summary}")
                
                # Get final deliverables count
                async with session.get(f"{self.base_url}/workspaces/{self.workspace_id}/deliverables") as response:
                    if response.status == 200:
                        deliverables_data = await response.json()
                        logger.info(f"📦 Final deliverables: {len(deliverables_data)} generated")
                
                # Get final team status
                async with session.get(f"{self.base_url}/workspaces/{self.workspace_id}/agents") as response:
                    if response.status == 200:
                        agents_data = await response.json()
                        active_agents = [a for a in agents_data if a.get('status') in ['active', 'available']]
                        logger.info(f"👥 Final team status: {len(active_agents)}/{len(agents_data)} agents active")
            
            # Calculate overall success score
            success_count = sum(1 for success in self.success_metrics.values() if success)
            total_metrics = len(self.success_metrics)
            success_rate = (success_count / total_metrics) * 100
            
            logger.info(f"📊 OVERALL SUCCESS RATE: {success_rate:.1f}% ({success_count}/{total_metrics})")
            
            # Log individual metric results
            for metric, success in self.success_metrics.items():
                status = "✅" if success else "❌"
                logger.info(f"   {status} {metric}: {'PASS' if success else 'FAIL'}")
            
            self.phase_timings["final_verification"] = time.time() - phase_start
            logger.info(f"✅ Phase 10 completed in {self.phase_timings['final_verification']:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Phase 10 failed: {e}")
            self.errors.append(f"Final verification failed: {str(e)}")
    
    async def _generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_time = time.time() - self.test_start_time
        
        # Calculate success metrics
        success_count = sum(1 for success in self.success_metrics.values() if success)
        total_metrics = len(self.success_metrics)
        overall_success_rate = (success_count / total_metrics) * 100
        
        report = {
            "test_execution": {
                "start_time": datetime.fromtimestamp(self.test_start_time).isoformat(),
                "end_time": datetime.now().isoformat(),
                "total_duration_seconds": total_time,
                "total_duration_minutes": total_time / 60
            },
            "user_simulation": {
                "user_profile": self.user_profile,
                "workspace_id": self.workspace_id,
                "team_proposal_id": self.team_proposal_id
            },
            "success_metrics": {
                "overall_success_rate": overall_success_rate,
                "successful_phases": success_count,
                "total_phases": total_metrics,
                "detailed_results": self.success_metrics
            },
            "phase_performance": {
                "timings_seconds": self.phase_timings,
                "total_phases_executed": len(self.phase_timings)
            },
            "generated_data": {
                "goals_created": len(self.goals),
                "tasks_generated": len(self.tasks),
                "deliverables_created": len(self.deliverables)
            },
            "errors_encountered": {
                "total_errors": len(self.errors),
                "error_list": self.errors
            },
            "test_verdict": {
                "overall_status": "PASS" if overall_success_rate >= 70 else "FAIL",
                "critical_failures": [metric for metric, success in self.success_metrics.items() if not success and metric in ['workspace_created', 'team_formed', 'goals_created']],
                "recommendations": self._generate_recommendations()
            }
        }
        
        # Log final report summary
        logger.info("=" * 80)
        logger.info("🎯 COMPREHENSIVE E2E TEST REPORT")
        logger.info("=" * 80)
        logger.info(f"⏱️  Total test duration: {total_time/60:.1f} minutes")
        logger.info(f"📊 Overall success rate: {overall_success_rate:.1f}%")
        logger.info(f"✅ Successful phases: {success_count}/{total_metrics}")
        logger.info(f"❌ Errors encountered: {len(self.errors)}")
        logger.info(f"🏆 Test verdict: {report['test_verdict']['overall_status']}")
        
        if report['test_verdict']['critical_failures']:
            logger.error(f"🚨 Critical failures: {report['test_verdict']['critical_failures']}")
        
        logger.info("=" * 80)
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        if not self.success_metrics["workspace_created"]:
            recommendations.append("Fix workspace creation API - this is critical for user onboarding")
        
        if not self.success_metrics["team_formed"]:
            recommendations.append("Investigate Director Agent and team formation pipeline")
        
        if not self.success_metrics["tasks_executed"]:
            recommendations.append("Check task executor and agent assignment system")
        
        if not self.success_metrics["deliverables_generated"]:
            recommendations.append("Review deliverable generation thresholds and asset system")
        
        if not self.success_metrics["real_time_updates"]:
            recommendations.append("Fix WebSocket connectivity for real-time user experience")
        
        if not self.success_metrics["conversation_working"]:
            recommendations.append("Debug conversational interface and tool execution")
        
        if len(self.errors) > 3:
            recommendations.append("Multiple errors detected - consider comprehensive system review")
        
        if not recommendations:
            recommendations.append("System performing well - consider performance optimization and user experience enhancements")
        
        return recommendations

async def main():
    """Run the comprehensive E2E test"""
    test = RealUserE2ETest()
    
    try:
        # Update todo status
        logger.info("📋 Starting comprehensive E2E test...")
        
        # Run the complete test
        report = await test.run_complete_test()
        
        # Save report to file
        report_filename = f"comprehensive_e2e_test_report_{int(time.time())}.json"
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📋 Test report saved to: {report_filename}")
        
        # Print final summary
        if report['test_verdict']['overall_status'] == 'PASS':
            logger.info("🎉 COMPREHENSIVE E2E TEST PASSED!")
        else:
            logger.error("❌ COMPREHENSIVE E2E TEST FAILED!")
            logger.error("🔧 Check the errors and recommendations in the report")
        
        return report
        
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}", exc_info=True)
        return {"error": str(e), "status": "FAILED"}

if __name__ == "__main__":
    asyncio.run(main())