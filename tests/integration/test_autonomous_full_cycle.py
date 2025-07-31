#!/usr/bin/env python3
"""
🔄 COMPLETE AUTONOMOUS CYCLE TEST
Test the entire autonomous task generation system with both fixes applied:
1. AutomatedGoalMonitor started in main.py
2. Goal extraction from workspace.goal during team approval
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any
import requests
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

API_BASE = "http://localhost:8000/api"

class AutonomousFullCycleTest:
    def __init__(self):
        self.workspace_id = None
        self.test_results = {
            "workspace_creation": None,
            "team_proposal": None, 
            "team_approval": None,
            "goal_extraction": None,
            "autonomous_monitoring": None,
            "task_generation_cycles": [],
            "final_metrics": None
        }
        
    async def run_complete_test(self):
        logger.info("🚀 STARTING COMPLETE AUTONOMOUS CYCLE TEST")
        logger.info("=" * 80)
        
        try:
            # Phase 1: Setup (manual)
            await self._phase_1_setup()
            
            # Phase 2: Trigger team approval (should auto-extract goals)
            await self._phase_2_trigger_goal_extraction()
            
            # Phase 3: Monitor autonomous task generation  
            await self._phase_3_monitor_autonomous_cycles()
            
            # Phase 4: Analyze results
            await self._phase_4_analyze_results()
            
        except Exception as e:
            logger.error(f"❌ Test failed: {e}", exc_info=True)

    async def _phase_1_setup(self):
        logger.info("\n📋 PHASE 1: WORKSPACE & TEAM SETUP")
        
        # Create workspace with detailed goal
        workspace_data = {
            "name": f"Autonomous Test {datetime.now().strftime('%H%M%S')}",
            "description": "Complete test of autonomous task generation system",
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "goal": "Generate 50 customer contacts with full contact details, preferences, and purchase history. Create customer acquisition strategy document. Build product catalog with 20 items and pricing.",
            "budget": 2000
        }
        
        response = requests.post(f"{API_BASE}/workspaces", json=workspace_data, timeout=10)
        response.raise_for_status()
        workspace = response.json()
        self.workspace_id = workspace["id"]
        
        self.test_results["workspace_creation"] = {
            "success": True,
            "workspace_id": self.workspace_id,
            "goal_text": workspace_data["goal"]
        }
        
        logger.info(f"✅ Workspace created: {self.workspace_id}")
        logger.info(f"📝 Goal text: {workspace_data['goal']}")
        
        # Create team proposal
        proposal_data = {
            "workspace_id": self.workspace_id,
            "project_description": workspace_data["goal"],
            "budget": 2000.0,
            "max_team_size": 5
        }
        
        proposal_response = requests.post(f"{API_BASE}/director/proposal", json=proposal_data, timeout=90)
        proposal_response.raise_for_status()
        proposal_id = proposal_response.json()["proposal_id"]
        
        self.test_results["team_proposal"] = {
            "success": True,
            "proposal_id": proposal_id
        }
        
        logger.info(f"✅ Team proposal created: {proposal_id}")

    async def _phase_2_trigger_goal_extraction(self):
        logger.info("\n🎯 PHASE 2: TRIGGER GOAL EXTRACTION VIA TEAM APPROVAL")
        
        # Approve team proposal - this should trigger goal extraction
        approval_response = requests.post(
            f"{API_BASE}/director/approve/{self.workspace_id}",
            params={"proposal_id": self.test_results["team_proposal"]["proposal_id"]},
            timeout=60
        )
        approval_response.raise_for_status()
        approval_result = approval_response.json()
        
        logger.info(f"✅ Team approved: {approval_result.get('message', 'No message')}")
        
        self.test_results["team_approval"] = {
            "success": True,
            "message": approval_result.get('message'),
            "auto_start_triggered": approval_result.get('auto_start_triggered', False),
            "created_agents": len(approval_result.get('created_agent_ids', []))
        }
        
        # Wait a moment for goal extraction to complete
        await asyncio.sleep(3)
        
        # Check if goals were extracted
        goals_response = requests.get(f"{API_BASE}/workspaces/{self.workspace_id}/goals")
        if goals_response.status_code == 200:
            goals_data = goals_response.json()
            goals = goals_data.get("goals", [])
            
            self.test_results["goal_extraction"] = {
                "success": len(goals) > 0,
                "goals_count": len(goals),
                "goals": goals[:3]  # Store first 3 for debugging
            }
            
            logger.info(f"✅ Goal extraction: {len(goals)} goals created")
            for i, goal in enumerate(goals[:3], 1):
                logger.info(f"   Goal {i}: {goal.get('metric_type', 'Unknown')} = {goal.get('target_value', 0)} {goal.get('unit', '')}")
        else:
            self.test_results["goal_extraction"] = {
                "success": False,
                "error": f"Failed to get goals: {goals_response.status_code}"
            }
            logger.warning(f"⚠️ Failed to get goals: {goals_response.status_code}")

    async def _phase_3_monitor_autonomous_cycles(self):
        logger.info("\n🔄 PHASE 3: MONITOR AUTONOMOUS TASK GENERATION CYCLES")
        
        # Monitor for 5 minutes to see autonomous task generation
        start_time = time.time()
        monitoring_duration = 300  # 5 minutes
        check_interval = 30  # Check every 30 seconds
        
        cycle_count = 0
        last_task_count = 0
        
        while time.time() - start_time < monitoring_duration:
            cycle_count += 1
            logger.info(f"\n🔍 Monitoring Cycle {cycle_count} ({int((time.time() - start_time)/60)}m {int((time.time() - start_time)%60)}s elapsed)")
            
            # Check current tasks
            tasks_response = requests.get(f"{API_BASE}/workspaces/{self.workspace_id}/tasks", timeout=10)
            if tasks_response.status_code == 200:
                tasks = tasks_response.json()
                current_task_count = len(tasks)
                
                # Check for new tasks
                new_tasks_generated = current_task_count > last_task_count
                
                cycle_result = {
                    "cycle": cycle_count,
                    "timestamp": datetime.now().isoformat(),
                    "total_tasks": current_task_count,
                    "new_tasks": current_task_count - last_task_count if new_tasks_generated else 0,
                    "tasks_by_status": {},
                    "new_tasks_generated": new_tasks_generated
                }
                
                # Count tasks by status
                for task in tasks:
                    status = task.get('status', 'unknown')
                    cycle_result["tasks_by_status"][status] = cycle_result["tasks_by_status"].get(status, 0) + 1
                
                self.test_results["task_generation_cycles"].append(cycle_result)
                
                logger.info(f"   📊 Tasks: {current_task_count} total (+{cycle_result['new_tasks']} new)")
                logger.info(f"   📈 Status breakdown: {cycle_result['tasks_by_status']}")
                
                if new_tasks_generated:
                    logger.info(f"   🎉 NEW TASKS GENERATED! System is working autonomously")
                
                last_task_count = current_task_count
            else:
                logger.warning(f"   ⚠️ Failed to get tasks: {tasks_response.status_code}")
            
            # Check AutomatedGoalMonitor status
            try:
                monitor_response = requests.get("http://localhost:8000/status/automated-goal-monitor", timeout=5)
                if monitor_response.status_code == 200:
                    monitor_status = monitor_response.json()
                    logger.info(f"   🤖 Goal Monitor: Running={monitor_status.get('is_running', False)}, "
                              f"Next cycle in {monitor_status.get('next_cycle_in_minutes', 'N/A')} min")
                else:
                    logger.warning(f"   ⚠️ Could not get monitor status: {monitor_response.status_code}")
            except Exception as e:
                logger.warning(f"   ⚠️ Monitor status check failed: {e}")
            
            # Wait for next check
            await asyncio.sleep(check_interval)
        
        self.test_results["autonomous_monitoring"] = {
            "duration_minutes": monitoring_duration / 60,
            "cycles_completed": cycle_count,
            "total_task_generation_events": sum(1 for cycle in self.test_results["task_generation_cycles"] if cycle["new_tasks_generated"])
        }
        
        logger.info(f"\n✅ Monitoring completed: {cycle_count} cycles over {monitoring_duration/60} minutes")

    async def _phase_4_analyze_results(self):
        logger.info("\n📊 PHASE 4: FINAL ANALYSIS")
        
        # Get final task count
        final_tasks_response = requests.get(f"{API_BASE}/workspaces/{self.workspace_id}/tasks", timeout=10)
        final_task_count = 0
        final_tasks_by_status = {}
        
        if final_tasks_response.status_code == 200:
            final_tasks = final_tasks_response.json()
            final_task_count = len(final_tasks)
            
            for task in final_tasks:
                status = task.get('status', 'unknown')
                final_tasks_by_status[status] = final_tasks_by_status.get(status, 0) + 1
        
        self.test_results["final_metrics"] = {
            "total_tasks_generated": final_task_count,
            "tasks_by_status": final_tasks_by_status,
            "autonomous_cycles_with_generation": sum(1 for cycle in self.test_results["task_generation_cycles"] if cycle["new_tasks_generated"]),
            "total_monitoring_cycles": len(self.test_results["task_generation_cycles"]),
            "system_autonomous": final_task_count > 3  # More than initial tasks
        }
        
        # Print comprehensive report
        logger.info("=" * 80)
        logger.info("🎯 AUTONOMOUS SYSTEM TEST RESULTS")
        logger.info("=" * 80)
        
        # Workspace & Goals
        logger.info(f"📋 Workspace: {self.test_results['workspace_creation']['workspace_id']}")
        logger.info(f"🎯 Goals Extracted: {self.test_results['goal_extraction']['success']} ({self.test_results['goal_extraction']['goals_count']} goals)")
        
        # Team Setup
        logger.info(f"👥 Team Setup: {self.test_results['team_approval']['success']} ({self.test_results['team_approval']['created_agents']} agents)")
        logger.info(f"🚀 Auto-start Triggered: {self.test_results['team_approval']['auto_start_triggered']}")
        
        # Autonomous Operation
        final_metrics = self.test_results["final_metrics"]
        logger.info(f"🔄 Total Tasks Generated: {final_metrics['total_tasks_generated']}")
        logger.info(f"📊 Task Status: {final_metrics['tasks_by_status']}")
        logger.info(f"🤖 Autonomous Cycles with New Tasks: {final_metrics['autonomous_cycles_with_generation']}/{final_metrics['total_monitoring_cycles']}")
        logger.info(f"✅ System is Autonomous: {final_metrics['system_autonomous']}")
        
        # Overall Assessment
        if final_metrics['system_autonomous'] and self.test_results['goal_extraction']['success']:
            logger.info("🎉 SUCCESS: Autonomous task generation system is working correctly!")
        else:
            logger.warning("❌ ISSUE: System may not be fully autonomous")
            
            if not self.test_results['goal_extraction']['success']:
                logger.warning("   - Goal extraction failed")
            if not final_metrics['system_autonomous']:
                logger.warning(f"   - Only {final_metrics['total_tasks_generated']} tasks generated (expected >3)")
        
        # Save detailed results
        results_file = f"autonomous_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        logger.info(f"💾 Detailed results saved to: {results_file}")

async def main():
    test = AutonomousFullCycleTest()
    await test.run_complete_test()

if __name__ == "__main__":
    asyncio.run(main())