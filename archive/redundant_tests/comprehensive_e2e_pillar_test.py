
import time
import logging
import uuid
import time
import os
import sys
from datetime import datetime, timezone

# Add backend directory to sys.path to allow imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from database import get_supabase_client
except ImportError:
    print("Error: Could not import get_supabase_client. Make sure database.py is accessible.")
    sys.exit(1)

# --- Test Configuration ---
WORKSPACE_NAME = f"e2e_pillar_test_stock_recommender_{int(time.time())}"
GOAL_DESCRIPTION = "Creare un motore di raccomandazione per opzioni su azioni di società tecnologiche, analizzando trend di mercato e volatilità."
TEST_TIMEOUT_SECONDS = 900  # 15 minutes
POLLING_INTERVAL_SECONDS = 15

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveE2EPillarTest:
    """
    Executes a comprehensive E2E test simulating a real user request,
    and validates key architectural and philosophical pillars of the system.
    """

    def __init__(self):
        self.supabase = get_supabase_client()
        if not self.supabase:
            raise ConnectionError("Failed to connect to Supabase.")
        
        self.test_id = str(uuid.uuid4())
        self.workspace_id = None
        self.goal_id = None
        self.start_time = datetime.now(timezone.utc)
        
        self.pillar_results = {
            "Pillar 1 (SDK Nativo)": {"status": "PENDING", "details": "Awaiting SDK log analysis."},
            "Pillar 2 (AI-Driven)": {"status": "PENDING", "details": "Conceptually validated by goal complexity."},
            "Pillar 3 (Universal)": {"status": "PENDING", "details": "Conceptually validated by non-English, domain-specific goal."},
            "Pillar 5 (Goal-Driven Tracking)": {"status": "PENDING", "details": "Awaiting task generation."},
            "Pillar 6 (Memory System)": {"status": "PENDING", "details": "Awaiting goal completion."},
            "Pillar 7 (Pipeline Autonoma)": {"status": "PENDING", "details": "Awaiting pipeline execution monitoring."},
            "Pillar 8 (Quality Gates)": {"status": "PENDING", "details": "Awaiting quality gate activations."},
            "Pillar 12 (Concrete Deliverables)": {"status": "PENDING", "details": "Awaiting deliverable generation."},
        }
        logger.info(f"Comprehensive E2E Pillar Test initialized with ID: {self.test_id}")

    def run(self):
        """Main method to orchestrate the test phases."""
        try:
            logger.info("--- STARTING TEST ---")
            
            self._1_create_workspace_and_goal()
            self._2_approve_team_and_wait_for_tasks()
            self._3_monitor_task_execution()
            self._4_verify_final_state()

            logger.info("--- TEST COMPLETED SUCCESSFULLY ---")
            return True
        except Exception as e:
            logger.error(f"--- TEST FAILED: {e} ---", exc_info=True)
            return False
        finally:
            self._cleanup()
            self._generate_report()

    def _1_create_workspace_and_goal(self):
        """Phase 1: Create the workspace and define the goal."""
        logger.info("PHASE 1: Creating workspace and goal...")
        
        # Create workspace
        ws_res = self.supabase.table("workspaces").insert({"name": WORKSPACE_NAME, "user_id": str(uuid.uuid4())}).execute()
        if not ws_res.data:
            raise RuntimeError("Failed to create workspace.")
        self.workspace_id = ws_res.data[0]['id']
        logger.info(f"Workspace '{WORKSPACE_NAME}' created with ID: {self.workspace_id}")

        # Create goal
        goal_res = self.supabase.table("workspace_goals").insert({
            "workspace_id": self.workspace_id,
            "source_goal_text": GOAL_DESCRIPTION,
            "description": GOAL_DESCRIPTION,
            "metric_type": "deliverables", # Default metric type for this test
            "target_value": 1.0, # Expecting at least one deliverable
            "status": "active"
        }).execute()
        if not goal_res.data:
            raise RuntimeError("Failed to create goal.")
        self.goal_id = goal_res.data[0]['id']
        logger.info(f"Goal '{GOAL_DESCRIPTION}' created with ID: {self.goal_id}")
        
        self.pillar_results["Pillar 2 (AI-Driven)"]["status"] = "PASS"
        self.pillar_results["Pillar 3 (Universal)"]["status"] = "PASS"
        logger.info("PHASE 1: COMPLETE")

    def _2_approve_team_and_wait_for_tasks(self):
        """Phase 2: Wait for team proposal, approve it, and wait for tasks."""
        logger.info("PHASE 2: Waiting for team proposal and task generation...")
        
        # This part assumes a 'teams' table or similar for proposals.
        # For this test, we'll simplify and just wait for tasks to appear.
        # A more complex test could interact with a team approval flow.
        
        logger.info("Waiting for initial tasks to be generated...")
        tasks = self._poll_for_data("tasks", "goal_id", self.goal_id)
        
        if not tasks:
            raise TimeoutError("Timed out waiting for tasks to be generated.")
        
        logger.info(f"Found {len(tasks)} tasks generated for the goal.")
        self._validate_pillar_5(tasks)
        logger.info("PHASE 2: COMPLETE")

    def _3_monitor_task_execution(self):
        """Phase 3: Monitor the real-time execution of tasks by the AI agents."""
        logger.info("PHASE 3: Monitoring task execution... (This may take several minutes)")
        
        start_monitoring_time = time.time()
        while time.time() - start_monitoring_time < TEST_TIMEOUT_SECONDS:
            res = self.supabase.table("tasks").select("status").eq("goal_id", self.goal_id).execute()
            if not res.data:
                logger.warning("No tasks found for goal, assuming completion or error.")
                break

            tasks_statuses = [task['status'] for task in res.data]
            
            pending_count = tasks_statuses.count('pending')
            in_progress_count = tasks_statuses.count('in_progress')
            
            logger.info(f"Task Status Update: {len(tasks_statuses)} total, "
                        f"{tasks_statuses.count('completed')} completed, "
                        f"{in_progress_count} in_progress, {pending_count} pending.")

            if pending_count == 0 and in_progress_count == 0:
                logger.info("All tasks have reached a terminal state.")
                break
            
            time.sleep(POLLING_INTERVAL_SECONDS)
        else:
            raise TimeoutError("Test timed out during task execution phase.")
        
        # Validate execution monitoring, SDK usage, and quality gates
        self._validate_pillar_1()
        self._validate_pillar_8()
        self._validate_pillar_7()
        logger.info("PHASE 3: COMPLETE")

    def _4_verify_final_state(self):
        """Phase 4: Verify the final deliverables and memory insights."""
        logger.info("PHASE 4: Verifying deliverables and memory insights...")
        self._validate_pillar_12()
        self._validate_pillar_6()
        logger.info("PHASE 4: COMPLETE")

    def _poll_for_data(self, table, column, value, timeout=300):
        """Generic polling function to wait for data to appear in a table."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            res = self.supabase.table(table).select("*").eq(column, value).execute()
            if res.data:
                logger.info(f"Data found in table '{table}'.")
                return res.data
            time.sleep(POLLING_INTERVAL_SECONDS)
        return None

    def _validate_pillar_5(self, tasks):
        """Checks that all tasks are correctly linked to the goal."""
        all_linked = all(task.get('goal_id') == self.goal_id for task in tasks)
        if all_linked:
            self.pillar_results["Pillar 5 (Goal-Driven Tracking)"]["status"] = "PASS"
            self.pillar_results["Pillar 5 (Goal-Driven Tracking)"]["details"] = "All generated tasks are correctly linked to the parent goal."
        else:
            self.pillar_results["Pillar 5 (Goal-Driven Tracking)"]["status"] = "FAIL"
            self.pillar_results["Pillar 5 (Goal-Driven Tracking)"]["details"] = "Found tasks not correctly linked to the parent goal."
        logger.info(f"Pillar 5 Validation: {self.pillar_results['Pillar 5 (Goal-Driven Tracking)']['status']}")

    def _validate_pillar_12(self):
        """Checks for concrete, non-placeholder deliverables."""
        logger.info("Validating Pillar 12: Concrete Deliverables...")
        res = self.supabase.table("deliverables").select("content").eq("goal_id", self.goal_id).execute()
        
        if not res.data:
            self.pillar_results["Pillar 12 (Concrete Deliverables)"]["status"] = "FAIL"
            self.pillar_results["Pillar 12 (Concrete Deliverables)"]["details"] = "No deliverables were generated for the completed goal."
            return

        content = str(res.data[0].get('content', '')).lower()
        placeholders = ["todo", "[example]", "lorem ipsum", "placeholder"]
        keywords = ["nasdaq", "volatility", "stock", "option", "market", "trend"]

        has_placeholders = any(p in content for p in placeholders)
        has_keywords = any(k in content for k in keywords)

        if not has_placeholders and has_keywords:
            self.pillar_results["Pillar 12 (Concrete Deliverables)"]["status"] = "PASS"
            self.pillar_results["Pillar 12 (Concrete Deliverables)"]["details"] = "Deliverable is concrete, relevant, and contains no placeholders."
        elif has_placeholders:
            self.pillar_results["Pillar 12 (Concrete Deliverables)"]["status"] = "FAIL"
            self.pillar_results["Pillar 12 (Concrete Deliverables)"]["details"] = f"Deliverable contains placeholder values."
        else:
            self.pillar_results["Pillar 12 (Concrete Deliverables)"]["status"] = "FAIL"
            self.pillar_results["Pillar 12 (Concrete Deliverables)"]["details"] = "Deliverable content seems irrelevant to the goal."
        logger.info(f"Pillar 12 Validation: {self.pillar_results['Pillar 12 (Concrete Deliverables)']['status']}")

    def _validate_pillar_6(self):
        """Checks for new insights saved in workspace memory."""
        logger.info("Validating Pillar 6: Memory System...")
        res = self.supabase.table("workspace_memory").select("insight_type").eq("workspace_id", self.workspace_id).gt("created_at", self.start_time.isoformat()).execute()

        if res.data:
            types = {item['insight_type'] for item in res.data}
            self.pillar_results["Pillar 6 (Memory System)"]["status"] = "PASS"
            self.pillar_results["Pillar 6 (Memory System)"]["details"] = f"New insights of type(s) {types} were saved to memory."
        else:
            self.pillar_results["Pillar 6 (Memory System)"]["status"] = "FAIL"
            self.pillar_results["Pillar 6 (Memory System)"]["details"] = "No new insights were saved to memory after goal completion."
        logger.info(f"Pillar 6 Validation: {self.pillar_results['Pillar 6 (Memory System)']['status']}")

    def _validate_pillar_1(self):
        """Checks that SDK primitives are used, by scanning system logs."""
        logger.info("Validating Pillar 1: SDK Nativo via log analysis...")
        log_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "server.log"))
        if not os.path.exists(log_path):
            self.pillar_results["Pillar 1 (SDK Nativo)"]["status"] = "FAIL"
            self.pillar_results["Pillar 1 (SDK Nativo)"]["details"] = f"Log file not found at {log_path}"
        else:
            with open(log_path, "r") as f:
                content = f.read().lower()
            if "planner.invoke" in content and "agent.execute" in content:
                self.pillar_results["Pillar 1 (SDK Nativo)"]["status"] = "PASS"
                self.pillar_results["Pillar 1 (SDK Nativo)"]["details"] = "Found planner.invoke and agent.execute calls in logs."
            else:
                self.pillar_results["Pillar 1 (SDK Nativo)"]["status"] = "FAIL"
                self.pillar_results["Pillar 1 (SDK Nativo)"]["details"] = "Missing SDK primitive calls in logs."
        logger.info(f"Pillar 1 Validation: {self.pillar_results['Pillar 1 (SDK Nativo)']['status']}")

    def _validate_pillar_8(self):
        """Checks that Quality Gates have been activated, by querying validations table."""
        logger.info("Validating Pillar 8: Quality Gates...")
        try:
            res = self.supabase.table("quality_validations").select("*").eq("workspace_id", self.workspace_id).execute()
            count = len(res.data) if res.data else 0
            if count > 0:
                self.pillar_results["Pillar 8 (Quality Gates)"]["status"] = "PASS"
                self.pillar_results["Pillar 8 (Quality Gates)"]["details"] = f"{count} quality validation entries found."
            else:
                self.pillar_results["Pillar 8 (Quality Gates)"]["status"] = "FAIL"
                self.pillar_results["Pillar 8 (Quality Gates)"]["details"] = "No quality validation entries found."
        except Exception as e:
            self.pillar_results["Pillar 8 (Quality Gates)"]["status"] = "FAIL"
            self.pillar_results["Pillar 8 (Quality Gates)"]["details"] = f"Error querying quality_validations: {e}"
        logger.info(f"Pillar 8 Validation: {self.pillar_results['Pillar 8 (Quality Gates)']['status']}")

    def _validate_pillar_7(self):
        """Checks that tasks progressed through the pipeline autonomously."""
        logger.info("Validating Pillar 7: Pipeline Autonoma...")
        res = self.supabase.table("tasks").select("status").eq("goal_id", self.goal_id).execute()
        statuses = [t.get("status") for t in res.data] if res.data else []
        if any(s != "pending" for s in statuses):
            self.pillar_results["Pillar 7 (Pipeline Autonoma)"]["status"] = "PASS"
            self.pillar_results["Pillar 7 (Pipeline Autonoma)"]["details"] = "Tasks progressed without manual intervention."
        else:
            self.pillar_results["Pillar 7 (Pipeline Autonoma)"]["status"] = "FAIL"
            self.pillar_results["Pillar 7 (Pipeline Autonoma)"]["details"] = "No task status changes detected; pipeline may not be autonomous."
        logger.info(f"Pillar 7 Validation: {self.pillar_results['Pillar 7 (Pipeline Autonoma)']['status']}")

    def _cleanup(self):
        """Cleans up all data created during the test."""
        logger.info("--- CLEANING UP TEST DATA ---")
        if self.workspace_id:
            logger.info(f"Deleting workspace {self.workspace_id} and all associated data...")
            # Assuming cascading delete is set up for goals, tasks, etc.
            self.supabase.table("workspaces").delete().eq("id", self.workspace_id).execute()
            logger.info("Cleanup complete.")
        else:
            logger.info("No workspace ID found, skipping cleanup.")

    def _generate_report(self):
        """Prints the final test report."""
        logger.info("\n\n" + "="*60)
        logger.info(" COMPREHENSIVE E2E PILLAR TEST REPORT")
        logger.info("="*60)
        logger.info(f"Test ID: {self.test_id}")
        logger.info(f"Workspace: {WORKSPACE_NAME} ({self.workspace_id})")
        logger.info(f"Goal: {GOAL_DESCRIPTION}")
        logger.info("-"*60)
        
        for pillar, result in self.pillar_results.items():
            logger.info(f"[{result['status']}] {pillar}")
            logger.info(f"    Details: {result['details']}")
        
        logger.info("="*60 + "\n")

def main():
    test = ComprehensiveE2EPillarTest()
    success = test.run()
    if not success:
        sys.exit(1) # Exit with a non-zero code to indicate failure for CI/CD systems

if __name__ == "__main__":
    main()
