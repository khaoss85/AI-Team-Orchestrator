#!/usr/bin/env python3
"""
🎯 **TRUE PRODUCTION FLOW TEST**

Test del VERO flusso di produzione end-to-end che simula esattamente 
quello che succede quando un utente usa il sistema:

1. Crea workspace via API REST (come farebbe frontend)
2. Triggera orchestrazione autonoma via API
3. Aspetta che il sistema crei agent, deleghi task, esegua
4. Verifica deliverable creati DAL SISTEMA, non manualmente
5. Controlla QA e improvement cycles

NO shortcuts, NO chiamate dirette, NO bypass!
"""

import asyncio
import logging
import sys
import os
import json
import uuid
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import httpx

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrueProductionFlowTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_workspace_id = None
        self.team_proposal_id = None
        self.created_agents = []
        self.created_tasks = []
        self.deliverables = []
        self.start_time = None
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def run_true_production_test(self) -> bool:
        """🎯 Esegue il VERO test di produzione end-to-end"""
        
        print("\n" + "="*80)
        print("🎯 TRUE PRODUCTION FLOW TEST")
        print("="*80)
        print("Testing REAL production flow exactly as users would experience it")
        print("NO shortcuts, NO direct calls, NO bypass - just real API flow")
        print("="*80)
        
        self.start_time = time.time()
        
        try:
            # Step 1: Create workspace via API (like frontend would)
            print("\n📝 Step 1: Creating workspace via REST API...")
            await self._test_workspace_creation_api()
            
            # Step 2: Trigger Director proposal and approval (THE CORRECT FLOW)  
            print("\n🚀 Step 2: Director Proposal & Approval...")
            await self._test_orchestration_trigger()
            
            # Step 3: Monitor agent creation
            print("\n👥 Step 3: Monitoring autonomous agent creation...")
            await self._test_agent_creation()
            
            # Step 4: Monitor task delegation
            print("\n📋 Step 4: Monitoring task delegation...")
            await self._test_task_delegation()
            
            # Step 5: Monitor task execution
            print("\n⚙️ Step 5: Monitoring task execution by executor...")
            await self._test_task_execution()
            
            # Step 6: Verify deliverable creation
            print("\n📦 Step 6: Verifying deliverable creation by system...")
            await self._test_deliverable_creation()
            
            # Step 7: Check QA and improvements
            print("\n✅ Step 7: Checking QA and improvement cycles...")
            await self._test_qa_improvements()
            
            # Final validation
            print("\n🏁 Step 8: Final production validation...")
            return await self._final_validation()
            
        except Exception as e:
            print(f"\n❌ CRITICAL FAILURE: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await self.client.aclose()
    
    async def _test_workspace_creation_api(self):
        """Test workspace creation via real API endpoint"""
        
        workspace_data = {
            "name": "True Production Test - Email Campaign",
            "description": "Create comprehensive email marketing campaign for AI-powered project management tool launch",
            "goal": "Generate 1000 qualified leads through targeted email campaign for B2B SaaS product launch",
            "budget": 15000.0,
            "business_objective": "Launch AI project management tool to enterprise market"
        }
        
        # Call real API endpoint (correct path)
        response = await self.client.post(
            f"{self.base_url}/workspaces/",
            json=workspace_data
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            self.test_workspace_id = data.get("id")
            print(f"✅ Workspace created via API: {self.test_workspace_id}")
            print(f"   📊 Status: {data.get('status')}")
            print(f"   🎯 Goal: {workspace_data['goal']}")
        else:
            raise Exception(f"Workspace creation failed: {response.status_code} - {response.text}")
    
    async def _test_orchestration_trigger(self):
        """Trigger orchestration via real API endpoint - THE CORRECT WAY"""
        
        print("🤖 Step 2.1: Requesting team proposal from Director...")
        
        # First: Request team proposal from Director
        proposal_request = {
            "workspace_id": self.test_workspace_id,
            "goal": "Generate 1000 qualified leads through targeted email campaign for B2B SaaS product launch",
            "budget_constraint": {
                "max_amount": 15000,
                "currency": "USD",
                "categories": ["content_creation", "email_automation", "lead_generation"]
            },
            "user_id": str(uuid.uuid4()),
            "user_feedback": "I need a balanced team with email marketing expertise and content creation skills",
            "extracted_goals": [
                {
                    "type": "email_marketing",
                    "description": "Create comprehensive email marketing campaign with sequences and automation",
                    "metrics": {"emails": 5, "sequences": 3, "automation_workflows": 2}
                },
                {
                    "type": "lead_generation", 
                    "description": "Generate 1000+ qualified leads through targeted campaigns",
                    "metrics": {"monthly_leads": 1000, "conversion_rate": 0.05}
                }
            ]
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/director/proposal",
            json=proposal_request
        )
        
        if response.status_code == 200:
            proposal_response = response.json()
            self.team_proposal_id = proposal_response.get("proposal_id")
            print(f"✅ Team proposal received: {self.team_proposal_id}")
            
            # Wait for proposal processing
            await asyncio.sleep(3)
            
            print("🤖 Step 2.2: User approves team proposal...")
            
            # Second: Approve the team proposal (simulating user decision)
            approval_response = await self.client.post(
                f"{self.base_url}/api/director/approve/{self.test_workspace_id}",
                params={"proposal_id": self.team_proposal_id}
            )
            
            if approval_response.status_code == 200:
                print("✅ Team proposal approved - Autonomous orchestration starting!")
                # Give system time to start autonomous processing
                await asyncio.sleep(5)
            else:
                raise Exception(f"Team approval failed: {approval_response.status_code}")
        else:
            raise Exception(f"Director proposal failed: {response.status_code}")
    
    async def _test_agent_creation(self):
        """Monitor autonomous agent creation"""
        
        max_wait = 30  # seconds
        start = time.time()
        
        while time.time() - start < max_wait:
            # Check agents via API (correct endpoint)
            response = await self.client.get(
                f"{self.base_url}/agents/{self.test_workspace_id}"
            )
            
            if response.status_code == 200:
                agents = response.json()
                if agents and len(agents) > 0:
                    self.created_agents = agents
                    print(f"✅ Agents created autonomously: {len(agents)} agents")
                    for agent in agents[:3]:  # Show first 3
                        print(f"   👤 {agent.get('name')} - {agent.get('role')} ({agent.get('status')})")
                    return
            
            await asyncio.sleep(2)
        
        print("⚠️ No agents created after 30 seconds")
    
    async def _test_task_delegation(self):
        """Monitor task creation and delegation"""
        
        max_wait = 30
        start = time.time()
        
        while time.time() - start < max_wait:
            # Check tasks via API (correct endpoint)
            response = await self.client.get(
                f"{self.base_url}/workspaces/{self.test_workspace_id}/tasks"
            )
            
            if response.status_code == 200:
                tasks = response.json()
                if tasks and len(tasks) > 0:
                    self.created_tasks = tasks
                    print(f"✅ Tasks created and delegated: {len(tasks)} tasks")
                    
                    # Count by status
                    status_counts = {}
                    for task in tasks:
                        status = task.get('status', 'unknown')
                        status_counts[status] = status_counts.get(status, 0) + 1
                    
                    for status, count in status_counts.items():
                        print(f"   📊 {status}: {count} tasks")
                    
                    # Show sample tasks
                    for task in tasks[:3]:
                        print(f"   📋 {task.get('name')} -> Agent: {task.get('assigned_to')}")
                    return
            
            await asyncio.sleep(2)
        
        print("⚠️ No tasks created after 30 seconds")
    
    async def _test_task_execution(self):
        """Monitor task execution progress"""
        
        print("🔄 Monitoring task execution for 60 seconds...")
        
        execution_updates = []
        start = time.time()
        max_wait = 60
        
        while time.time() - start < max_wait:
            # Check task status (correct endpoint)
            response = await self.client.get(
                f"{self.base_url}/workspaces/{self.test_workspace_id}/tasks"
            )
            
            if response.status_code == 200:
                tasks = response.json()
                
                # Track status changes
                completed = sum(1 for t in tasks if t.get('status') == 'completed')
                in_progress = sum(1 for t in tasks if t.get('status') == 'in_progress')
                pending = sum(1 for t in tasks if t.get('status') == 'pending')
                
                update = f"Completed: {completed}, In Progress: {in_progress}, Pending: {pending}"
                if not execution_updates or execution_updates[-1] != update:
                    execution_updates.append(update)
                    print(f"   📊 {datetime.now().strftime('%H:%M:%S')} - {update}")
                
                # Check if making progress
                if completed > 0:
                    print(f"✅ Tasks are being executed! {completed} completed so far")
            
            await asyncio.sleep(5)
        
        # Final check
        if execution_updates:
            print(f"✅ Task execution monitored. Final: {execution_updates[-1]}")
        else:
            print("❌ No task execution detected")
    
    async def _test_deliverable_creation(self):
        """Verify deliverables created by the system"""
        
        # Wait for deliverables
        print("⏳ Waiting for system to create deliverables...")
        
        max_wait = 120  # 2 minutes
        start = time.time()
        
        while time.time() - start < max_wait:
            response = await self.client.get(
                f"{self.base_url}/api/deliverables/workspace/{self.test_workspace_id}"
            )
            
            if response.status_code == 200:
                deliverables = response.json()
                if deliverables and len(deliverables) > 0:
                    self.deliverables = deliverables
                    print(f"✅ Deliverables created by system: {len(deliverables)}")
                    
                    for deliverable in deliverables:
                        print(f"   📦 {deliverable.get('title', 'Untitled')}")
                        print(f"      Type: {deliverable.get('type')}")
                        print(f"      Status: {deliverable.get('status')}")
                        
                        # Check for real content
                        content = deliverable.get('content', {})
                        if isinstance(content, dict):
                            content_size = len(json.dumps(content))
                        else:
                            content_size = len(str(content))
                        
                        print(f"      Content Size: {content_size} chars")
                        
                        if content_size > 500:
                            print("      ✅ Contains substantial content")
                        else:
                            print("      ⚠️ Content seems minimal")
                    return
            
            await asyncio.sleep(10)
        
        print("❌ No deliverables created after 2 minutes")
    
    async def _test_qa_improvements(self):
        """Check QA and improvement cycles"""
        
        # Check for QA evaluations
        response = await self.client.get(
            f"{self.base_url}/api/quality/evaluations/workspace/{self.test_workspace_id}"
        )
        
        if response.status_code == 200:
            evaluations = response.json()
            if evaluations:
                print(f"✅ QA evaluations found: {len(evaluations)}")
                for eval in evaluations[:3]:
                    print(f"   🔍 Task: {eval.get('task_id')} - Score: {eval.get('quality_score')}")
        else:
            print("⚠️ No QA evaluations found")
        
        # Check for improvements
        response = await self.client.get(
            f"{self.base_url}/api/improvements/workspace/{self.test_workspace_id}"
        )
        
        if response.status_code == 200:
            improvements = response.json()
            if improvements:
                print(f"✅ Improvements triggered: {len(improvements)}")
        else:
            print("⚠️ No improvement cycles detected")
    
    async def _final_validation(self) -> bool:
        """Final validation of production flow"""
        
        elapsed_time = time.time() - self.start_time
        
        print("\n" + "="*60)
        print("📊 FINAL PRODUCTION FLOW VALIDATION")
        print("="*60)
        
        # Calculate scores
        scores = {
            "Workspace Created": 10 if self.test_workspace_id else 0,
            "Agents Created": 20 if len(self.created_agents) >= 3 else 10 if self.created_agents else 0,
            "Tasks Created": 20 if len(self.created_tasks) >= 5 else 10 if self.created_tasks else 0,
            "Tasks Executed": 20 if any(t.get('status') == 'completed' for t in self.created_tasks) else 0,
            "Deliverables Created": 20 if self.deliverables else 0,
            "Real Content": 10 if any(len(str(d.get('content', ''))) > 500 for d in self.deliverables) else 0
        }
        
        total_score = sum(scores.values())
        
        # Display results
        for criterion, score in scores.items():
            status = "✅" if score > 0 else "❌"
            print(f"{status} {criterion}: {score}/{'20' if 'Created' in criterion or 'Executed' in criterion else '10'}")
        
        print(f"\n📊 Total Score: {total_score}/100")
        print(f"⏱️ Execution Time: {elapsed_time:.1f} seconds")
        
        # Warnings
        if any("fallback" in str(t).lower() for t in self.created_tasks):
            print("\n⚠️ WARNING: Fallback detected in tasks!")
            total_score -= 20
        
        # No direct imports check
        if elapsed_time < 30:
            print("\n⚠️ WARNING: Execution too fast - possible shortcuts!")
            total_score -= 10
        
        # Final verdict
        print("\n" + "="*60)
        if total_score >= 90:
            print("🎉 RESULT: TRUE PRODUCTION READY!")
            print("✅ System works end-to-end as in production")
            print("✅ No shortcuts or bypasses detected")
            print("✅ Autonomous orchestration confirmed")
            return True
        elif total_score >= 70:
            print("⚠️ RESULT: PARTIALLY PRODUCTION READY")
            print("✅ Core flow works but with issues")
            print("⚠️ Some components may be bypassed")
            return False
        else:
            print("❌ RESULT: NOT PRODUCTION READY")
            print("❌ Major components not working")
            print("❌ System cannot orchestrate autonomously")
            return False

async def main():
    """Execute true production test"""
    
    # First check if server is running
    try:
        async with httpx.AsyncClient() as client:
            # Try multiple endpoints
            for endpoint in ["/api/health", "/health", "/"]:
                try:
                    response = await client.get(f"http://localhost:8000{endpoint}")
                    if response.status_code == 200:
                        print(f"✅ Server is running (tested {endpoint})")
                        break
                except:
                    continue
            else:
                print("❌ Server not responding on http://localhost:8000")
                print("Please start the server with: cd backend && python main.py")
                return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Please start the server with: cd backend && python main.py")
        return False
    
    test = TrueProductionFlowTest()
    
    try:
        is_production_ready = await test.run_true_production_test()
        
        if is_production_ready:
            print("\n🎉 TRUE PRODUCTION FLOW TEST: PASSED!")
            print("The system works exactly as it would in production.")
            return True
        else:
            print("\n❌ TRUE PRODUCTION FLOW TEST: FAILED!")
            print("The system is not working as it would in production.")
            return False
            
    except Exception as e:
        print(f"\n💥 CRITICAL TEST FAILURE: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)