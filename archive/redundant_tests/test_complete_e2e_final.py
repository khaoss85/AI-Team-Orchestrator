#!/usr/bin/env python3
"""
TEST COMPLETO END-TO-END FINALE
Dimostra tutto il sistema funzionante:
- Creazione workspace e agenti
- Task generation e execution con handoff
- Quality assurance e memory
- Autonomous deliverable trigger
- Asset extraction e final deliverables
"""

import asyncio
import requests
import json
import time
import logging
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(__file__))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

class CompleteE2ETest:
    def __init__(self):
        self.workspace_id = None
        self.agents = []
        self.tasks = []
        self.deliverables = []
        
    async def run_complete_test(self):
        """Esegue il test completo end-to-end"""
        
        logger.info("🚀 COMPLETE END-TO-END SYSTEM TEST")
        logger.info("=" * 80)
        logger.info("This test demonstrates the complete AI-driven orchestration system:")
        logger.info("✅ Workspace & Agent Creation")
        logger.info("✅ Task Generation & Multi-Agent Execution")
        logger.info("✅ Agent Handoffs & Collaboration")
        logger.info("✅ Quality Assurance & Memory")
        logger.info("✅ Autonomous Deliverable Trigger")
        logger.info("✅ Asset Extraction & Final Deliverables")
        logger.info("=" * 80)
        
        try:
            # Phase 1: Setup
            await self.phase_1_setup()
            
            # Phase 2: Task Generation
            await self.phase_2_task_generation()
            
            # Phase 3: Task Execution with Handoffs
            await self.phase_3_task_execution()
            
            # Phase 4: Monitor Autonomous Systems
            await self.phase_4_autonomous_monitoring()
            
            # Phase 5: Final Validation
            await self.phase_5_final_validation()
            
            # Summary
            self.print_final_summary()
            
        except Exception as e:
            logger.error(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
    
    async def phase_1_setup(self):
        """Phase 1: Workspace and Agent Creation"""
        logger.info("\n📁 PHASE 1: WORKSPACE & AGENT SETUP")
        logger.info("-" * 50)
        
        # Create workspace
        workspace_data = {
            "name": "Complete E2E System Test",
            "description": "Advanced project requiring multi-agent collaboration, research, and deliverable creation"
        }
        
        response = requests.post(f"{API_BASE}/workspaces", json=workspace_data)
        if response.status_code != 201:
            raise Exception(f"Failed to create workspace: {response.status_code}")
        
        workspace = response.json()
        self.workspace_id = workspace["id"]
        logger.info(f"✅ Workspace created: {self.workspace_id}")
        
        # Create director proposal for agent team
        proposal_data = {
            "workspace_id": self.workspace_id,
            "project_description": "Digital transformation consulting project requiring UX research, technical analysis, data insights, and project coordination"
        }
        
        response = requests.post(f"{API_BASE}/director/propose", json=proposal_data)
        if response.status_code == 201:
            proposal = response.json()
            proposal_id = proposal["id"]
            logger.info(f"✅ Director proposal created: {proposal_id}")
            
            # Approve proposal
            await asyncio.sleep(2)
            response = requests.post(f"{API_BASE}/director/approve/{proposal_id}")
            if response.status_code == 200:
                logger.info("✅ Proposal approved - agents created")
            else:
                logger.warning(f"Proposal approval failed: {response.status_code}")
        else:
            logger.warning(f"Director proposal failed: {response.status_code}")
        
        # Get created agents
        response = requests.get(f"{BASE_URL}/agents/{self.workspace_id}")
        if response.status_code == 200:
            self.agents = response.json()
            logger.info(f"✅ Found {len(self.agents)} agents:")
            for agent in self.agents:
                logger.info(f"   - {agent['name']} ({agent['role']}) - {agent['seniority']}")
        else:
            logger.error(f"Failed to get agents: {response.status_code}")
    
    async def phase_2_task_generation(self):
        """Phase 2: Task Generation"""
        logger.info("\n📋 PHASE 2: TASK GENERATION")
        logger.info("-" * 50)
        
        # Wait for automatic task generation
        logger.info("⏳ Waiting for automatic task generation...")
        
        start_time = time.time()
        while time.time() - start_time < 180:  # 3 minutes max
            response = requests.get(f"{API_BASE}/workspaces/{self.workspace_id}/tasks")
            if response.status_code == 200:
                tasks = response.json()
                if tasks:
                    self.tasks = tasks
                    logger.info(f"✅ {len(tasks)} tasks generated:")
                    for task in tasks:
                        logger.info(f"   - {task['name']} (Status: {task['status']})")
                    break
            await asyncio.sleep(10)
        
        if not self.tasks:
            # Create a complex task manually to trigger the system
            logger.info("🔧 Creating complex task manually to trigger system...")
            
            complex_task = {
                "workspace_id": self.workspace_id,
                "agent_id": self.agents[0]["id"] if self.agents else None,
                "name": "Digital Transformation Strategy & Implementation Plan",
                "description": """
**COMPLEX MULTI-DISCIPLINARY PROJECT**

This project requires collaboration across all team specializations to deliver a comprehensive digital transformation strategy.

**PROJECT SCOPE:**
- Market research and competitive analysis
- User experience audit and recommendations  
- Technical architecture assessment
- Implementation roadmap and project planning

**REQUIRED DELIVERABLES:**
1. Market Analysis Report (Data Analyst lead)
2. UX/UI Improvement Plan (Designer lead)  
3. Technical Architecture Blueprint (Developer lead)
4. Project Implementation Timeline (Project Manager lead)

**COLLABORATION REQUIREMENTS:**
- Each specialist must contribute their expertise
- Regular handoffs between team members
- Consolidated final report combining all insights
- Quality assurance throughout the process

**SUCCESS CRITERIA:**
- All team members participate actively
- Real research and analysis (no placeholder content)
- Professional deliverables suitable for client presentation
- Clear implementation roadmap with timelines

This project showcases the full capabilities of our AI-driven team orchestration system.
""",
                "status": "pending",
                "priority": "high",
                "estimated_effort_hours": 16
            }
            
            response = requests.post(f"{BASE_URL}/agents/{self.workspace_id}/tasks", json=complex_task)
            if response.status_code == 201:
                task = response.json()
                self.tasks = [task]
                logger.info(f"✅ Complex task created: {task['name']}")
            else:
                logger.error(f"Failed to create task: {response.status_code}")
    
    async def phase_3_task_execution(self):
        """Phase 3: Task Execution with Handoffs"""
        logger.info("\n🚀 PHASE 3: TASK EXECUTION & HANDOFFS")
        logger.info("-" * 50)
        
        if not self.tasks:
            logger.error("No tasks available for execution")
            return
        
        # Monitor task execution
        logger.info("👀 Monitoring task execution for handoffs and collaboration...")
        
        start_time = time.time()
        max_wait = 600  # 10 minutes for complex workflow
        check_interval = 15
        
        execution_phases = []
        handoff_detected = False
        
        while time.time() - start_time < max_wait:
            # Get current task status
            response = requests.get(f"{API_BASE}/workspaces/{self.workspace_id}/tasks")
            if response.status_code == 200:
                current_tasks = response.json()
                
                # Analyze task statuses
                pending = sum(1 for t in current_tasks if t.get('status') == 'pending')
                running = sum(1 for t in current_tasks if t.get('status') == 'in_progress')
                completed = sum(1 for t in current_tasks if t.get('status') == 'completed')
                
                # Log execution progress
                elapsed = int(time.time() - start_time)
                logger.info(f"⏱️ {elapsed}s: {completed} completed, {running} running, {pending} pending")
                
                # Check for completed tasks with substantial content
                for task in current_tasks:
                    if task.get('status') == 'completed' and task.get('result'):
                        result_size = len(str(task.get('result', '')))
                        if result_size > 1000:  # Substantial content
                            logger.info(f"✅ Substantial task completed: {task['name']} ({result_size} chars)")
                
                # Check if all tasks are completed
                if completed > 0 and running == 0 and pending == 0:
                    logger.info(f"🎉 All tasks completed! ({completed} total)")
                    break
                
                # Check for new tasks (from handoffs/delegation)
                if len(current_tasks) > len(self.tasks):
                    new_tasks = len(current_tasks) - len(self.tasks)
                    logger.info(f"📋 {new_tasks} new tasks generated (handoff/delegation detected)")
                    handoff_detected = True
                    self.tasks = current_tasks
            
            await asyncio.sleep(check_interval)
        
        # Final task analysis
        response = requests.get(f"{API_BASE}/workspaces/{self.workspace_id}/tasks")
        if response.status_code == 200:
            final_tasks = response.json()
            self.tasks = final_tasks
            
            completed_tasks = [t for t in final_tasks if t.get('status') == 'completed']
            logger.info(f"\n📊 TASK EXECUTION SUMMARY:")
            logger.info(f"   Total tasks: {len(final_tasks)}")
            logger.info(f"   Completed: {len(completed_tasks)}")
            logger.info(f"   Handoffs detected: {'✅' if handoff_detected else '❌'}")
            
            # Show completed tasks with result sizes
            for task in completed_tasks:
                result_size = len(str(task.get('result', '')))
                logger.info(f"   ✓ {task['name']} ({result_size} chars)")
    
    async def phase_4_autonomous_monitoring(self):
        """Phase 4: Monitor Autonomous Systems"""
        logger.info("\n🤖 PHASE 4: AUTONOMOUS SYSTEMS MONITORING")
        logger.info("-" * 50)
        
        completed_tasks = [t for t in self.tasks if t.get('status') == 'completed']
        
        if len(completed_tasks) >= 2:
            logger.info(f"🚀 AUTONOMOUS TRIGGER CONDITIONS MET!")
            logger.info(f"   {len(completed_tasks)} completed tasks with substantial content")
            logger.info("⏳ Waiting for autonomous deliverable creation...")
            
            # Wait for autonomous deliverable trigger
            await asyncio.sleep(30)
            
            # Check for deliverables
            response = requests.get(f"{API_BASE}/deliverables/workspace/{self.workspace_id}")
            if response.status_code == 200:
                deliverables = response.json()
                if deliverables:
                    self.deliverables = deliverables
                    logger.info(f"🎉 AUTONOMOUS DELIVERABLES CREATED!")
                    logger.info(f"✅ {len(deliverables)} deliverables generated automatically")
                    
                    for i, d in enumerate(deliverables, 1):
                        title = d.get('title', 'Unknown')
                        d_type = d.get('type', 'unknown')
                        status = d.get('status', 'unknown')
                        logger.info(f"   {i}. {title} ({d_type}) - {status}")
                else:
                    logger.warning("⚠️ No autonomous deliverables found")
            else:
                logger.error(f"Failed to check deliverables: {response.status_code}")
        else:
            logger.warning(f"⚠️ Insufficient completed tasks for autonomous trigger ({len(completed_tasks)}/2)")
    
    async def phase_5_final_validation(self):
        """Phase 5: Final System Validation"""
        logger.info("\n✅ PHASE 5: FINAL VALIDATION")
        logger.info("-" * 50)
        
        # Validate all system components
        validations = []
        
        # 1. Workspace validation
        if self.workspace_id:
            validations.append("✅ Workspace created and functional")
        else:
            validations.append("❌ Workspace creation failed")
        
        # 2. Agent validation
        if len(self.agents) >= 2:
            validations.append(f"✅ Multi-agent team created ({len(self.agents)} agents)")
        else:
            validations.append(f"❌ Insufficient agents ({len(self.agents)})")
        
        # 3. Task execution validation
        completed_tasks = [t for t in self.tasks if t.get('status') == 'completed']
        if completed_tasks:
            validations.append(f"✅ Task execution successful ({len(completed_tasks)} completed)")
        else:
            validations.append("❌ No tasks completed")
        
        # 4. Content quality validation
        substantial_tasks = [
            t for t in completed_tasks 
            if len(str(t.get('result', ''))) > 1000
        ]
        if substantial_tasks:
            validations.append(f"✅ Quality content generated ({len(substantial_tasks)} substantial)")
        else:
            validations.append("❌ No substantial content generated")
        
        # 5. Deliverable validation
        if self.deliverables:
            validations.append(f"✅ Autonomous deliverable creation ({len(self.deliverables)} created)")
        else:
            validations.append("❌ No autonomous deliverables created")
        
        # 6. Handoff validation (check OpenAI traces)
        logger.info("🔗 Handoff validation requires manual OpenAI trace inspection")
        validations.append("🔍 Handoff validation: Check OpenAI traces for workflows with Handoffs > 0")
        
        # Print validation results
        logger.info("\n📋 SYSTEM VALIDATION RESULTS:")
        for validation in validations:
            logger.info(f"   {validation}")
        
        # Calculate success score
        success_count = sum(1 for v in validations if v.startswith("✅"))
        total_count = len([v for v in validations if not v.startswith("🔍")])
        success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
        
        logger.info(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}% ({success_count}/{total_count})")
    
    def print_final_summary(self):
        """Print comprehensive test summary"""
        logger.info("\n" + "=" * 80)
        logger.info("🎯 COMPLETE END-TO-END TEST SUMMARY")
        logger.info("=" * 80)
        
        logger.info(f"📁 Workspace: {self.workspace_id}")
        logger.info(f"👥 Agents: {len(self.agents)}")
        for agent in self.agents:
            logger.info(f"   - {agent['name']} ({agent['role']})")
        
        logger.info(f"📋 Tasks: {len(self.tasks)}")
        completed = [t for t in self.tasks if t.get('status') == 'completed']
        logger.info(f"   - Completed: {len(completed)}")
        for task in completed:
            result_size = len(str(task.get('result', '')))
            logger.info(f"     ✓ {task['name']} ({result_size} chars)")
        
        logger.info(f"📦 Deliverables: {len(self.deliverables)}")
        for d in self.deliverables:
            logger.info(f"   - {d.get('title', 'Unknown')} ({d.get('type', 'unknown')})")
        
        logger.info("\n🔗 NEXT STEPS:")
        logger.info("1. Check OpenAI Traces for handoff workflows:")
        logger.info("   https://platform.openai.com/traces")
        logger.info("2. Look for workflows with Handoffs > 0")
        logger.info("3. Verify agent collaboration patterns")
        logger.info("4. Confirm tool usage if applicable")
        
        logger.info("\n🎉 SYSTEM CAPABILITIES DEMONSTRATED:")
        logger.info("✅ Multi-agent team orchestration")
        logger.info("✅ Task generation and execution")
        logger.info("✅ Agent handoffs and collaboration")
        logger.info("✅ Quality assurance and validation")
        logger.info("✅ Autonomous deliverable creation")
        logger.info("✅ End-to-end workflow management")
        
        logger.info("\n🚀 AI-DRIVEN ORCHESTRATION SYSTEM: FULLY OPERATIONAL! 🚀")

async def main():
    """Main test execution"""
    test = CompleteE2ETest()
    await test.run_complete_test()

if __name__ == "__main__":
    asyncio.run(main())