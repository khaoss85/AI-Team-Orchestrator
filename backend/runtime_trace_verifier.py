

import os
import uuid
import time
import logging
import requests
import psycopg2
from psycopg2.extras import DictCursor

# --- TODO: Configuration - Replace with your actual environment details ---
API_BASE_URL = os.getenv("API_URL", "http://localhost:8000")
DB_CONNECTION_STRING = os.getenv("DATABASE_URL", "postgresql://user:password@host:port/dbname")
SERVER_LOG_PATH = os.getenv("LOG_PATH", "/path/to/your/server.log") # Or use an API endpoint if available
# --- End of Configuration ---

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class EndToEndTraceAuditor:

    def __init__(self, api_base_url, db_conn_string, log_path):
        self.api_base_url = api_base_url
        self.db_connection_string = db_conn_string
        self.log_path = log_path
        self.trace_id = str(uuid.uuid4())
        self.db_conn = None

    def _get_db_connection(self):
        """Establishes and returns a database connection."""
        if not self.db_conn or self.db_conn.closed:
            try:
                self.db_conn = psycopg2.connect(self.db_connection_string)
                logging.info("✅ Successfully connected to the database.")
            except psycopg2.OperationalError as e:
                logging.error(f"❌ DATABASE CONNECTION FAILED. Please check DB_CONNECTION_STRING. Error: {e}")
                raise
        return self.db_conn

    def run_audit(self, goal_payload: dict):
        """Executes the full audit workflow."""
        logging.info(f"🚀 Starting End-to-End Audit with Trace ID: {self.trace_id}")

        try:
            # 1. Inject Goal and capture Trace ID
            self.inject_goal(goal_payload)

            # 2. Wait for propagation
            logging.info("⏳ Waiting 15 seconds for event propagation...")
            time.sleep(15)

            # 3. Verify propagation across all systems
            results = {
                "trace_id": self.trace_id,
                "checks": {
                    "api_header_propagation": self.verify_api_header(),
                    "database_trace_propagation": self.verify_database_trace(),
                    "log_file_trace_propagation": self.verify_log_file_trace(),
                    "data_consistency_checks": self.run_data_consistency_checks()
                }
            }
            
            self.print_summary(results)

        finally:
            if self.db_conn and not self.db_conn.closed:
                self.db_conn.close()
                logging.info("🔌 Database connection closed.")

    def inject_goal(self, goal_payload: dict):
        """Step 1: Inject a goal via API and verify the trace ID is returned."""
        headers = {"X-Trace-ID": self.trace_id, "Content-Type": "application/json"}
        url = f"{self.api_base_url}/workspaces" # TODO: Adjust endpoint if necessary
        
        logging.info(f"🎯 Injecting goal into workspace via POST {url}...")
        try:
            response = requests.post(url, json=goal_payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            workspace_id = data.get("id")
            logging.info(f"✅ Goal injected successfully. Workspace created: {workspace_id}")

            returned_trace_id = response.headers.get("X-Trace-ID")
            if returned_trace_id == self.trace_id:
                logging.info("✅ Trace ID correctly returned in response header.")
            else:
                logging.warning(f"⚠️ Trace ID mismatch in response header! Expected {self.trace_id}, got {returned_trace_id}")

        except requests.exceptions.RequestException as e:
            logging.error(f"❌ FAILED to inject goal via API. Error: {e}")
            raise

    def verify_api_header(self) -> dict:
        """Placeholder to verify trace ID is handled by a generic endpoint."""
        # This confirms the middleware is active globally
        headers = {"X-Trace-ID": self.trace_id}
        url = f"{self.api_base_url}/health" # A simple, fast endpoint
        try:
            response = requests.get(url, headers=headers, timeout=10)
            return {"status": "SUCCESS" if response.headers.get("X-Trace-ID") == self.trace_id else "FAILURE"}
        except requests.exceptions.RequestException as e:
            return {"status": "ERROR", "details": str(e)}

    def verify_database_trace(self) -> dict:
        """Step 2: Check if the trace ID is present in key database tables."""
        # TODO: This check WILL FAIL until a `trace_id` column is added to tables.
        logging.info("Verifying database trace propagation...")
        conn = self._get_db_connection()
        results = {}
        
        # TODO: Add all tables that should contain the trace_id
        tables_to_check = ["workspaces", "tasks", "execution_logs", "asset_artifacts"]

        with conn.cursor(cursor_factory=DictCursor) as cur:
            for table in tables_to_check:
                # This query assumes a `trace_id` column exists.
                query = f"SELECT COUNT(*) FROM {table} WHERE trace_id = %s;"
                try:
                    cur.execute(query, (self.trace_id,))
                    count = cur.fetchone()[0]
                    results[table] = {"status": "SUCCESS" if count > 0 else "FAILURE", "count": count}
                except psycopg2.errors.UndefinedColumn:
                    results[table] = {"status": "ERROR", "details": f"Column 'trace_id' does not exist in table '{table}'."}
        
        return results

    def verify_log_file_trace(self) -> dict:
        """Step 3: Scan the main log file for the trace ID."""
        logging.info(f"Scanning log file at {self.log_path}...")
        try:
            with open(self.log_path, 'r') as f:
                logs = f.read()
            if self.trace_id in logs:
                return {"status": "SUCCESS", "details": "Trace ID found in log file."}
            else:
                return {"status": "FAILURE", "details": "Trace ID not found in log file."}
        except FileNotFoundError:
            return {"status": "ERROR", "details": f"Log file not found at {self.log_path}."}

    def run_data_consistency_checks(self) -> dict:
        """Step 4: Check for duplicates and inconsistencies."""
        # TODO: This check WILL FAIL until `trace_id` is available for filtering.
        logging.info("Running data consistency checks (e.g., for duplicate tasks)...")
        conn = self._get_db_connection()
        results = {}

        with conn.cursor(cursor_factory=DictCursor) as cur:
            # Check for duplicate tasks created within the context of this trace
            query = """
                SELECT name, COUNT(*)
                FROM tasks
                WHERE trace_id = %s 
                GROUP BY name
                HAVING COUNT(*) > 1;
            """
            try:
                cur.execute(query, (self.trace_id,))
                duplicates = cur.fetchall()
                if duplicates:
                    results["duplicate_tasks"] = {"status": "FAILURE", "details": dict(duplicates)}
                else:
                    results["duplicate_tasks"] = {"status": "SUCCESS", "details": "No duplicate tasks found for this trace."}
            except psycopg2.errors.UndefinedColumn:
                results["duplicate_tasks"] = {"status": "ERROR", "details": "Cannot check for duplicates without 'trace_id'."}

        return results

    def print_summary(self, results: dict):
        """Prints a final summary of the audit."""
        logging.info("\n" + "="*50)
        logging.info("          Audit Summary Report")
        logging.info("="*50)
        logging.info(f"Trace ID: {results['trace_id']}\n")

        for check, result in results["checks"].items():
            logging.info(f"▶️ Check: {check}")
            if isinstance(result, dict) and "status" in result:
                 logging.info(f"  - Global Status: {result['status']}")
                 if "details" in result:
                     logging.info(f"    - Details: {result['details']}")
            else: # Nested checks
                for sub_check, sub_result in result.items():
                    logging.info(f"  - Component: {sub_check}")
                    logging.info(f"    - Status: {sub_result['status']}")
                    if "details" in sub_result:
                        logging.info(f"      - Details: {sub_result['details']}")
        logging.info("="*50)


if __name__ == "__main__":
    # --- Example Usage ---
    auditor = EndToEndTraceAuditor(API_BASE_URL, DB_CONNECTION_STRING, SERVER_LOG_PATH)

    # Define a realistic goal to trigger the workflow
    test_goal_payload = {
        "name": f"Audit Test Workspace - {int(time.time())}",
        "goal": "Develop a comprehensive Q3 marketing strategy for a new product launch.",
        "user_id": str(uuid.uuid4()) # Mock user ID
    }
    
    auditor.run_audit(test_goal_payload)

