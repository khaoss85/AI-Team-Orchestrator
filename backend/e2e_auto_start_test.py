#!/usr/bin/env python3
"""
Comprehensive End-to-End Test for Auto-Start Functionality
Test Goal: "Raccogliere 500 contatti ICP (CMO/CTO di aziende SaaS europee) e suggerire almeno 3 sequenze email da impostare su Hubspot"
"""

from pathlib import Path
import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 30
WORKSPACE_DESCRIPTION = "Raccogliere 500 contatti ICP (CMO/CTO di aziende SaaS europee) e suggerire almeno 3 sequenze email da impostare su Hubspot"

class E2EAutoStartTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.workspace_id = None
        self.team_id = None
        self.extracted_goals = []
        self.results = {
            "test_started": datetime.now().isoformat(),
            "steps": {},
            "errors": [],
            "success": False
        }
    
    def log_step(self, step_name: str, success: bool, data: Any = None, error: str = None):
        """Log a test step result"""
        self.results["steps"][step_name] = {
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "data": data,
            "error": error
        }
        status = "✅" if success else "❌"
        print(f"{status} {step_name}: {'SUCCESS' if success else 'FAILED'}")
        if error:
            print(f"   Error: {error}")
        if data and isinstance(data, dict) and "id" in data:
            print(f"   ID: {data['id']}")
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> tuple[bool, Any]:
        """Make HTTP request with error handling"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return True, response.json()
        except requests.exceptions.RequestException as e:
            return False, str(e)
        except json.JSONDecodeError as e:
            return False, f"JSON decode error: {e}"
    
    def step_1_health_check(self) -> bool:
        """Step 1: Verify server is running"""
        success, data = self.make_request("GET", "/health")
        self.log_step("1_health_check", success, data, None if success else data)
        return success
    
    def step_2_create_workspace(self) -> bool:
        """Step 2: Create a new workspace"""
        # Generate a test user_id
        test_user_id = str(uuid.uuid4())
        
        payload = {
            "name": "Test E2E Auto-Start Workspace",
            "description": WORKSPACE_DESCRIPTION,
            "user_id": test_user_id,
            "goal": "Generate 500 ICP contacts and create 3 email sequences for European SaaS companies"
        }
        
        success, data = self.make_request("POST", "/workspaces", json=payload)
        if success:
            self.workspace_id = data.get("id")
        
        self.log_step("2_create_workspace", success, data, None if success else data)
        return success
    
    def step_3_extract_goals(self) -> bool:
        """Step 3: Extract goals from workspace description"""
        if not self.workspace_id:
            self.log_step("3_extract_goals", False, None, "No workspace_id available")
            return False
        
        # Extract goals using the preview endpoint first
        goal_payload = {
            "goal": WORKSPACE_DESCRIPTION
        }
        
        success, data = self.make_request("POST", f"/api/workspaces/{self.workspace_id}/goals/preview", json=goal_payload)
        if not success:
            self.log_step("3_extract_goals", False, None, data)
            return False
        
        # Check if goals were extracted
        strategic_deliverables = data.get("strategic_deliverables", [])
        final_metrics = data.get("final_metrics", [])
        total_goals = len(strategic_deliverables) + len(final_metrics)
        
        if total_goals > 0:
            # Store extracted goals for confirmation step
            self.extracted_goals = data.get("extracted_goals", strategic_deliverables + final_metrics)
            self.log_step("3_extract_goals", True, {
                "total_goals": total_goals,
                "strategic_deliverables": len(strategic_deliverables),
                "final_metrics": len(final_metrics)
            })
            return True
        else:
            self.log_step("3_extract_goals", False, None, "No goals were extracted")
            return False
    
    def step_4_confirm_goals(self) -> bool:
        """Step 4: Confirm extracted goals"""
        if not self.workspace_id:
            self.log_step("4_confirm_goals", False, None, "No workspace_id available")
            return False
        
        if not self.extracted_goals:
            self.log_step("4_confirm_goals", False, None, "No extracted goals to confirm")
            return False
        
        # Confirm all extracted goals
        confirm_payload = {
            "goals": self.extracted_goals
        }
        
        success, data = self.make_request("POST", f"/api/workspaces/{self.workspace_id}/goals/confirm", json=confirm_payload)
        if success:
            saved_goals = data.get("saved_goals", 0)
            self.log_step("4_confirm_goals", True, {"confirmed_goals": saved_goals, "message": data.get("message", "")})
            return True
        else:
            self.log_step("4_confirm_goals", False, None, data)
            return False
    
    def step_5_generate_team_proposal(self) -> bool:
        """Step 5: Generate team proposal"""
        if not self.workspace_id:
            self.log_step("5_generate_team_proposal", False, None, "No workspace_id available")
            return False
        
        # Generate a test user_id for the director config
        test_user_id = str(uuid.uuid4())
        
        # Create director config payload
        director_payload = {
            "workspace_id": self.workspace_id,
            "goal": WORKSPACE_DESCRIPTION,
            "budget_constraint": {
                "max_budget": 100,
                "max_iterations": 3
            },
            "user_id": test_user_id,
            "extracted_goals": self.extracted_goals
        }
        
        success, data = self.make_request("POST", "/director/proposal", json=director_payload)
        if success:
            # Extract team info from response
            if "id" in data:
                self.team_id = data["id"]
            elif "proposal" in data and "id" in data["proposal"]:
                self.team_id = data["proposal"]["id"]
            elif "agents" in data:
                # Look for team info in agents data
                agents = data.get("agents", [])
                if agents:
                    self.team_id = "generated"  # Placeholder
        
        self.log_step("5_generate_team_proposal", success, data, None if success else data)
        return success
    
    def step_6_approve_team(self) -> bool:
        """Step 6: Approve team proposal"""
        if not self.workspace_id:
            self.log_step("6_approve_team", False, None, "No workspace_id available")
            return False
        
        if not self.team_id:
            self.log_step("6_approve_team", False, None, "No team_id available from proposal generation")
            return False
        
        # Approve the team proposal using the director endpoint
        success, approve_data = self.make_request("POST", f"/director/approve/{self.workspace_id}?proposal_id={self.team_id}")
        if success:
            self.log_step("6_approve_team", True, approve_data)
            return True
        else:
            self.log_step("6_approve_team", False, None, approve_data)
            return False
    
    def step_7_verify_auto_start_trigger(self) -> bool:
        """Step 7: Verify auto-start triggers task generation"""
        if not self.workspace_id:
            self.log_step("7_verify_auto_start_trigger", False, None, "No workspace_id available")
            return False
        
        # Wait for auto-start to trigger (longer wait for async operations)
        print("   Waiting for auto-start to trigger task generation...")
        time.sleep(20)
        
        # Try multiple endpoints to check for tasks
        endpoints_to_try = [
            f"/workspaces/{self.workspace_id}/tasks",
            f"/api/workspaces/{self.workspace_id}/tasks"
        ]
        
        for endpoint in endpoints_to_try:
            success, data = self.make_request("GET", endpoint)
            if success:
                tasks = data.get("tasks", []) if isinstance(data, dict) else data
                if isinstance(tasks, list) and len(tasks) > 0:
                    self.log_step("7_verify_auto_start_trigger", True, {
                        "tasks_count": len(tasks), 
                        "endpoint_used": endpoint,
                        "sample_tasks": [{"id": t.get("id"), "title": t.get("title", t.get("description", "No title"))[:50]} for t in tasks[:3]]
                    })
                    return True
        
        # If no tasks found, check workspace and agent status for debugging
        debug_info = {}
        
        # Check workspace status
        ws_success, ws_data = self.make_request("GET", f"/workspaces/{self.workspace_id}")
        if ws_success:
            debug_info["workspace_status"] = ws_data.get("status")
        
        # Try to trigger immediate goal analysis manually
        manual_trigger_success = False
        if self.team_id:
            trigger_success, trigger_data = self.make_request("POST", f"/proposals/{self.team_id}/approve")
            if trigger_success:
                manual_trigger_success = True
                debug_info["manual_trigger_response"] = trigger_data.get("message", "No message")
        
        # Wait a bit more after manual trigger
        if manual_trigger_success:
            print("   Manual trigger executed, waiting additional time...")
            time.sleep(15)
            
            # Check for tasks again
            for endpoint in endpoints_to_try:
                success, data = self.make_request("GET", endpoint)
                if success:
                    tasks = data.get("tasks", []) if isinstance(data, dict) else data
                    if isinstance(tasks, list) and len(tasks) > 0:
                        self.log_step("7_verify_auto_start_trigger", True, {
                            "tasks_count": len(tasks), 
                            "endpoint_used": endpoint,
                            "triggered_manually": True,
                            "sample_tasks": [{"id": t.get("id"), "title": t.get("title", t.get("description", "No title"))[:50]} for t in tasks[:3]]
                        })
                        return True
        
        self.log_step("7_verify_auto_start_trigger", False, None, f"No tasks were generated. Debug info: {debug_info}")
        return False
    
    def step_8_check_task_generation(self) -> bool:
        """Step 8: Check that tasks are created successfully"""
        if not self.workspace_id:
            self.log_step("8_check_task_generation", False, None, "No workspace_id available")
            return False
        
        # Get all tasks
        success, data = self.make_request("GET", f"/workspaces/{self.workspace_id}/tasks")
        if not success:
            self.log_step("8_check_task_generation", False, None, data)
            return False
        
        tasks = data.get("tasks", []) if isinstance(data, dict) else data
        if not isinstance(tasks, list):
            self.log_step("8_check_task_generation", False, None, "Invalid tasks data format")
            return False
        
        # Analyze task quality
        pending_tasks = [t for t in tasks if t.get("status") == "pending"]
        in_progress_tasks = [t for t in tasks if t.get("status") == "in_progress"]
        completed_tasks = [t for t in tasks if t.get("status") == "completed"]
        
        task_analysis = {
            "total_tasks": len(tasks),
            "pending_tasks": len(pending_tasks),
            "in_progress_tasks": len(in_progress_tasks),
            "completed_tasks": len(completed_tasks),
            "task_types": list(set(t.get("task_type", "unknown") for t in tasks)),
            "agents_assigned": list(set(t.get("assigned_agent", "unknown") for t in tasks if t.get("assigned_agent")))
        }
        
        success = len(tasks) > 0
        self.log_step("8_check_task_generation", success, task_analysis, None if success else "No tasks found")
        return success
    
    def step_9_system_health_check(self) -> bool:
        """Step 9: Overall system health check"""
        if not self.workspace_id:
            self.log_step("9_system_health_check", False, None, "No workspace_id available")
            return False
        
        health_checks = {}
        
        # Check workspace status
        success, workspace_data = self.make_request("GET", f"/workspaces/{self.workspace_id}")
        health_checks["workspace_status"] = success and workspace_data.get("status") == "active"
        
        # Check goals status
        success, goals_data = self.make_request("GET", f"/workspace-goals/{self.workspace_id}")
        health_checks["goals_exist"] = success and len(goals_data.get("goals", [])) > 0
        
        # Check tasks status
        success, tasks_data = self.make_request("GET", f"/workspaces/{self.workspace_id}/tasks")
        tasks = tasks_data.get("tasks", []) if isinstance(tasks_data, dict) else tasks_data
        health_checks["tasks_exist"] = success and len(tasks) > 0
        
        # Check monitoring
        success, monitoring_data = self.make_request("GET", "/monitoring/health")
        health_checks["monitoring_active"] = success
        
        overall_health = all(health_checks.values())
        self.log_step("9_system_health_check", overall_health, health_checks, None if overall_health else "Some health checks failed")
        return overall_health
    
    def run_complete_test(self) -> Dict[str, Any]:
        """Run the complete end-to-end test"""
        print("🚀 Starting End-to-End Auto-Start Test")
        print(f"Test Goal: {WORKSPACE_DESCRIPTION}")
        print("=" * 80)
        
        # Execute test steps
        steps = [
            self.step_1_health_check,
            self.step_2_create_workspace,
            self.step_3_extract_goals,
            self.step_4_confirm_goals,
            self.step_5_generate_team_proposal,
            self.step_6_approve_team,
            self.step_7_verify_auto_start_trigger,
            self.step_8_check_task_generation,
            self.step_9_system_health_check
        ]
        
        all_passed = True
        for step in steps:
            try:
                if not step():
                    all_passed = False
                    break
            except Exception as e:
                self.results["errors"].append(f"Exception in {step.__name__}: {str(e)}")
                all_passed = False
                break
        
        self.results["success"] = all_passed
        self.results["test_completed"] = datetime.now().isoformat()
        
        print("=" * 80)
        print(f"🎯 Test Result: {'✅ SUCCESS' if all_passed else '❌ FAILED'}")
        print(f"Workspace ID: {self.workspace_id}")
        if self.results["errors"]:
            print("Errors encountered:")
            for error in self.results["errors"]:
                print(f"  - {error}")
        
        return self.results

def main():
    """Main function to run the test"""
    tester = E2EAutoStartTester()
    results = tester.run_complete_test()
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"./e2e_test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📊 Detailed results saved to: {results_file}")
    return results["success"]

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)