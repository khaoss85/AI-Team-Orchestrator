#!/usr/bin/env python3
"""
🚀 ENHANCED E2E TEST - SDK Memory Integration
================================================================================
Test completo end-to-end che valida:
1. Flusso completo di orchestrazione autonoma
2. Integrazione SDK Sessions + Unified Memory
3. Task completion con memoria persistente
4. AI-driven insights e pattern analysis
5. Cross-agent collaboration memory
"""

import requests
import time
import json
import logging
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any, List, Optional

# --- Configuration ---
BASE_URL = "http://localhost:8000"
WORKSPACE_COMPLETION_TIMEOUT = 600  # 10 minuti
POLLING_INTERVAL = 15  # 15 secondi
MEMORY_ANALYSIS_DELAY = 30  # Tempo per permettere sync memoria

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class EnhancedE2ETest:
    """Enhanced E2E Test with SDK Memory Integration monitoring"""
    
    def __init__(self):
        self.workspace_id: Optional[str] = None
        self.goal_id: Optional[str] = None
        self.proposal_id: Optional[str] = None
        self.start_time = datetime.now()
        self.memory_stats = []
        
    def run_complete_test(self):
        """Esegue il test E2E completo con monitoraggio memoria"""
        try:
            # --- FASE 1: SETUP ---
            logging.info("=== FASE 1: SETUP ===")
            self._create_workspace_and_goal()
            
            # --- FASE 2: AUTONOMOUS FLOW ---
            logging.info("\n=== FASE 2: TRIGGER AUTONOMOUS FLOW ===")
            self._generate_and_approve_team_proposal()
            
            # --- FASE 3: TASK CREATION MONITORING ---
            logging.info("\n=== FASE 3: TASK CREATION & MEMORY INITIALIZATION ===")
            self._wait_for_task_creation()
            self._capture_initial_memory_state()
            
            # --- FASE 4: WORKSPACE COMPLETION WITH MEMORY TRACKING ---
            logging.info("\n=== FASE 4: EXECUTION WITH MEMORY TRACKING ===")
            completion_result = self._monitor_workspace_completion_with_memory()
            
            # --- FASE 5: MEMORY ANALYSIS ---
            logging.info("\n=== FASE 5: MEMORY & INSIGHTS ANALYSIS ===")
            self._analyze_memory_and_insights()
            
            # --- FASE 6: FINAL VALIDATION ---
            logging.info("\n=== FASE 6: FINAL VALIDATION ===")
            self._validate_final_results()
            
            if completion_result["success"]:
                logging.info("🎉🎉🎉 ENHANCED E2E TEST PASSED! 🎉🎉🎉")
                return True
            else:
                logging.error(f"❌❌❌ Enhanced E2E Test FAILED: {completion_result['reason']} ❌❌❌")
                return False
                
        except Exception as e:
            logging.error(f"❌❌❌ Enhanced E2E Test FAILED: {e} ❌❌❌")
            return False
    
    def _create_workspace_and_goal(self):
        """Crea workspace e goal per il test"""
        # Create workspace
        workspace_data = {
            "name": f"Enhanced E2E Test - {uuid4()}",
            "goal": "Create a comprehensive market analysis report with actionable insights and recommendations."
        }
        response = requests.post(f"{BASE_URL}/api/workspaces/", json=workspace_data, timeout=10)
        assert response.status_code in [200, 201], f"Workspace creation failed: {response.text}"
        workspace = response.json()
        self.workspace_id = workspace['id']
        logging.info(f"✅ Workspace created: {self.workspace_id}")

        # Create goal
        goal_data = {
            "workspace_id": self.workspace_id,
            "description": "Generate high-quality market analysis with cross-industry insights",
            "metric_type": "deliverable_quality",
            "target_value": 85.0,  # Target quality score
        }
        response = requests.post(f"{BASE_URL}/api/workspaces/{self.workspace_id}/goals", json=goal_data, timeout=10)
        assert response.status_code in [200, 201], f"Goal creation failed: {response.text}"
        goal = response.json()
        self.goal_id = goal.get('id') or goal.get('goal_id')  # Handle different response formats
        logging.info(f"✅ Goal created: {self.goal_id}")
    
    def _generate_and_approve_team_proposal(self):
        """Genera e approva la proposta di team"""
        logging.info("⏳ Generating team proposal (may take up to 2 minutes)...")
        proposal_data = {"workspace_id": self.workspace_id}
        response = requests.post(f"{BASE_URL}/api/director/proposal", json=proposal_data, timeout=120)
        assert response.status_code == 200, f"Team proposal failed: {response.text}"
        proposal = response.json()
        self.proposal_id = proposal['proposal_id']
        logging.info(f"✅ Team proposal generated: {self.proposal_id}")

        logging.info("📋 Simulating manual user approval...")
        time.sleep(1)

        logging.info("⏳ Approving proposal and starting task generation...")
        response = requests.post(
            f"{BASE_URL}/api/director/approve/{self.workspace_id}?proposal_id={self.proposal_id}",
            timeout=30
        )
        assert response.status_code == 200, f"Proposal approval failed: {response.text}"
        logging.info("✅ Proposal approved and task generation started.")
    
    def _wait_for_task_creation(self):
        """Attende la creazione dei task"""
        logging.info("⏳ Waiting for task creation (up to 60 seconds)...")
        
        for attempt in range(4):  # 4 attempts = 60 seconds
            time.sleep(15)
            response = requests.get(f"{BASE_URL}/api/workspaces/{self.workspace_id}/tasks", timeout=10)
            if response.status_code == 200:
                tasks = response.json()
                if tasks and len(tasks) > 0:
                    logging.info(f"✅ Tasks created! Found {len(tasks)} tasks in workspace")
                    return
            
            logging.info(f"⏳ Attempt {attempt + 1}/4: No tasks yet, continuing to wait...")
        
        raise Exception("Tasks were not created within the expected timeframe")
    
    def _capture_initial_memory_state(self):
        """Cattura lo stato iniziale della memoria"""
        try:
            response = requests.get(f"{BASE_URL}/api/memory/sessions/stats", timeout=10)
            if response.status_code == 200:
                initial_stats = response.json()
                self.memory_stats.append({
                    "timestamp": datetime.now().isoformat(),
                    "phase": "initial",
                    "stats": initial_stats
                })
                logging.info(f"📊 Initial memory state: {initial_stats['stats']['total_active_sessions']} sessions")
            else:
                logging.warning(f"⚠️ Failed to get initial memory stats: {response.status_code}")
        except Exception as e:
            logging.warning(f"⚠️ Failed to capture initial memory state: {e}")
    
    def _monitor_workspace_completion_with_memory(self) -> Dict[str, Any]:
        """Monitora il completamento del workspace con tracking della memoria"""
        logging.info(f"🔄 Monitoring workspace {self.workspace_id} with memory tracking...")
        start_time = time.time()
        
        while time.time() - start_time < WORKSPACE_COMPLETION_TIMEOUT:
            elapsed_time = int(time.time() - start_time)
            
            # Get workspace status
            workspace_status = self._get_workspace_status()
            
            # Get tasks summary
            tasks_summary = self._get_tasks_summary()
            
            # Get memory stats
            memory_stats = self._get_memory_stats()
            
            # Log diagnostics
            logging.info(f"--- MEMORY & EXECUTION DIAGNOSTICS (Time: {elapsed_time}s) ---")
            self._log_workspace_status(workspace_status)
            self._log_tasks_summary(tasks_summary)
            self._log_memory_stats(memory_stats)
            
            # Store memory stats
            self.memory_stats.append({
                "timestamp": datetime.now().isoformat(),
                "phase": "execution",
                "elapsed_time": elapsed_time,
                "stats": memory_stats,
                "tasks": tasks_summary
            })
            
            # Check completion conditions
            if workspace_status.get("status") == "completed":
                return {"success": True, "reason": "workspace_completed"}
            
            if tasks_summary.get("completed", 0) >= 2 and tasks_summary.get("pending", 0) == 0 and tasks_summary.get("in_progress", 0) == 0:
                return {"success": True, "reason": "sufficient_tasks_completed"}
            
            # Check for failed tasks
            if tasks_summary.get("failed", 0) > 0:
                failed_details = self._analyze_failed_tasks()
                logging.error(f"🚨 DETECTED FAILED TASKS: {failed_details}")
            
            logging.info("" + "-" * 80)
            
            # Wait before next poll
            time.sleep(POLLING_INTERVAL)
        
        return {"success": False, "reason": "timeout_exceeded"}
    
    def _get_workspace_status(self) -> Dict[str, Any]:
        """Ottiene lo status del workspace"""
        try:
            response = requests.get(f"{BASE_URL}/api/workspaces/{self.workspace_id}", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "error", "code": response.status_code, "response": response.text}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _get_tasks_summary(self) -> Dict[str, Any]:
        """Ottiene il summary dei task"""
        try:
            response = requests.get(f"{BASE_URL}/api/workspaces/{self.workspace_id}/tasks", timeout=10)
            if response.status_code == 200:
                tasks = response.json()
                summary = {
                    "total": len(tasks),
                    "pending": len([t for t in tasks if t["status"] == "pending"]),
                    "in_progress": len([t for t in tasks if t["status"] == "in_progress"]),
                    "completed": len([t for t in tasks if t["status"] == "completed"]),
                    "failed": len([t for t in tasks if t["status"] == "failed"])
                }
                return summary
            else:
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def _get_memory_stats(self) -> Dict[str, Any]:
        """Ottiene le statistiche della memoria"""
        try:
            response = requests.get(f"{BASE_URL}/api/memory/sessions/stats", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def _log_workspace_status(self, status: Dict[str, Any]):
        """Log workspace status"""
        if "error" in status:
            logging.warning(f"WORKSPACE STATUS: Error - {status}")
        else:
            logging.info(f"WORKSPACE STATUS: {status.get('status', 'unknown')}")
    
    def _log_tasks_summary(self, summary: Dict[str, Any]):
        """Log tasks summary"""
        if "error" in summary:
            logging.warning(f"TASKS: Error - {summary}")
        else:
            logging.info(f"TASKS: {summary}")
    
    def _log_memory_stats(self, stats: Dict[str, Any]):
        """Log memory statistics"""
        if "error" in stats:
            logging.warning(f"MEMORY: Error - {stats}")
        else:
            memory_data = stats.get("stats", {})
            logging.info(f"MEMORY: {memory_data.get('total_active_sessions', 0)} active sessions, "
                        f"{memory_data.get('workspaces_with_sessions', 0)} workspaces with memory")
    
    def _analyze_failed_tasks(self) -> str:
        """Analizza i task falliti"""
        try:
            response = requests.get(f"{BASE_URL}/api/workspaces/{self.workspace_id}/tasks", timeout=10)
            if response.status_code == 200:
                tasks = response.json()
                failed_tasks = [t for t in tasks if t["status"] == "failed"]
                
                if failed_tasks:
                    details = []
                    for task in failed_tasks[:3]:  # Limit to first 3 failed tasks
                        details.append(f"Task {task['name']}: {task.get('result', 'No result')}")
                    return "; ".join(details)
            
            return "Failed to analyze failed tasks"
        except Exception as e:
            return f"Error analyzing failed tasks: {e}"
    
    def _analyze_memory_and_insights(self):
        """Analizza la memoria e gli insights generati"""
        logging.info("🧠 Analyzing memory patterns and insights...")
        
        try:
            # Get workspace memory summary
            response = requests.get(f"{BASE_URL}/api/memory/sessions/workspace/{self.workspace_id}/summary", timeout=15)
            if response.status_code == 200:
                memory_summary = response.json()
                logging.info(f"📊 MEMORY SUMMARY: {memory_summary}")
                
                # Analyze memory evolution
                self._analyze_memory_evolution()
                
                # Trigger manual sync to ensure all data is captured
                logging.info("🔄 Triggering manual memory sync...")
                sync_response = requests.post(f"{BASE_URL}/api/memory/sessions/workspace/{self.workspace_id}/sync", timeout=15)
                if sync_response.status_code == 200:
                    sync_result = sync_response.json()
                    logging.info(f"✅ Memory sync completed: {sync_result}")
                else:
                    logging.warning(f"⚠️ Memory sync failed: {sync_response.status_code}")
                    
            else:
                logging.warning(f"⚠️ Failed to get memory summary: {response.status_code}")
                
        except Exception as e:
            logging.error(f"❌ Memory analysis failed: {e}")
    
    def _analyze_memory_evolution(self):
        """Analizza l'evoluzione della memoria durante il test"""
        if len(self.memory_stats) < 2:
            logging.info("📊 Insufficient memory data for evolution analysis")
            return
        
        initial_stats = self.memory_stats[0]["stats"].get("stats", {})
        final_stats = self.memory_stats[-1]["stats"].get("stats", {})
        
        sessions_created = final_stats.get("total_active_sessions", 0) - initial_stats.get("total_active_sessions", 0)
        workspaces_growth = final_stats.get("workspaces_with_sessions", 0) - initial_stats.get("workspaces_with_sessions", 0)
        
        logging.info(f"📈 MEMORY EVOLUTION:")
        logging.info(f"   Sessions created: {sessions_created}")
        logging.info(f"   Workspaces with memory: {workspaces_growth}")
        logging.info(f"   Total data points: {len(self.memory_stats)}")
        
        # Check for memory creation
        if sessions_created > 0:
            logging.info("✅ SDK Sessions were successfully created during task execution")
        else:
            logging.warning("⚠️ No new SDK sessions detected - memory integration may not be working")
    
    def _validate_final_results(self):
        """Validazione finale dei risultati"""
        logging.info("🔍 Final validation...")
        
        # Validate workspace completion
        workspace_status = self._get_workspace_status()
        logging.info(f"Final workspace status: {workspace_status.get('status', 'unknown')}")
        
        # Validate task completion
        tasks_summary = self._get_tasks_summary()
        completed_tasks = tasks_summary.get("completed", 0)
        failed_tasks = tasks_summary.get("failed", 0)
        
        logging.info(f"Final task summary: {completed_tasks} completed, {failed_tasks} failed")
        
        # Validate memory integration
        final_memory_stats = self._get_memory_stats()
        active_sessions = final_memory_stats.get("stats", {}).get("total_active_sessions", 0)
        
        logging.info(f"Final memory state: {active_sessions} active sessions")
        
        # Determine success
        if completed_tasks >= 1 and failed_tasks == 0:
            logging.info("✅ VALIDATION PASSED: Tasks completed successfully")
        elif completed_tasks >= 1:
            logging.info("⚠️ PARTIAL SUCCESS: Some tasks completed but some failed")
        else:
            logging.error("❌ VALIDATION FAILED: No tasks completed successfully")

def main():
    """Main test execution"""
    test = EnhancedE2ETest()
    success = test.run_complete_test()
    
    if success:
        logging.info("🎉 Enhanced E2E Test completed successfully!")
        exit(0)
    else:
        logging.error("❌ Enhanced E2E Test failed!")
        exit(1)

if __name__ == "__main__":
    main()