#!/usr/bin/env python3
"""
DEBUG SCRIPT for get_ready_tasks function.

This script helps diagnose why tasks that are expected to be "ready" are not being
returned by the get_ready_tasks SQL function.

It performs the following steps:
1.  Finds the most recent workspace_id from the test logs.
2.  Connects to the database.
3.  Lists all tasks in that workspace, focusing on the 'pending' ones.
4.  For each pending task, it checks for entries in the 'task_dependencies' table.
5.  Finally, it calls the 'get_ready_tasks' RPC function to see the output.
"""
import asyncio
import logging
import os
import re
from typing import List, Dict, Any

# Add backend to path
import sys
sys.path.append(os.path.dirname(__file__))

from database import supabase_service

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

LOG_FILE = 'server.log'

def find_latest_workspace_id_from_logs() -> str:
    """Parses the log file to find the most recent workspace ID."""
    try:
        if not os.path.exists(LOG_FILE):
            logger.error(f"Log file not found: {LOG_FILE}")
            return None

        with open(LOG_FILE, 'r') as f:
            content = f.read()
        
        # Regex più robusta per trovare qualsiasi UUID associato a "workspace"
        workspace_ids = re.findall(r'workspace(?:_id)?\s*[:=]?\s*[\'\"]?([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})', content)
        
        if not workspace_ids:
            logger.error("No workspace IDs found in the log file.")
            return None
        
        latest_workspace_id = workspace_ids[-1]
        logger.info(f"Found latest workspace ID: {latest_workspace_id}")
        return latest_workspace_id
    except Exception as e:
        logger.error(f"Failed to read workspace ID from logs: {e}")
        return None

async def inspect_task_dependencies(workspace_id: str):
    """Inspects tasks and their dependencies for a given workspace."""
    if not workspace_id:
        logger.error("Cannot inspect tasks without a workspace ID.")
        return

    logger.info(f"\n--- INSPECTING WORKSPACE: {workspace_id} ---")

    try:
        # 1. Get all pending tasks for the workspace
        tasks_res = supabase_service.table("tasks").select("id, name, status").eq("workspace_id", workspace_id).eq("status", "pending").execute()
        pending_tasks = tasks_res.data
        
        if not pending_tasks:
            logger.warning("No pending tasks found for this workspace.")
        else:
            logger.info(f"Found {len(pending_tasks)} pending task(s):")
            for task in pending_tasks:
                logger.info(f"  - Task ID: {task['id']}, Name: '{task['name']}'")

        # 2. For each pending task, check its dependencies
        for task in pending_tasks:
            task_id = task['id']
            logger.info(f"\n--- Checking dependencies for task: {task_id} ---")
            
            deps_res = await supabase_service.table("task_dependencies").select("*").eq("task_id", task_id).execute()
            dependencies = deps_res.data

            if not dependencies:
                logger.info(f"  -> This task has NO dependencies listed in 'task_dependencies'. It should be READY.")
            else:
                logger.warning(f"  -> This task has {len(dependencies)} dependency/dependencies:")
                for dep in dependencies:
                    depends_on_id = dep['depends_on_task_id']
                    dep_task_res = await supabase_service.table("tasks").select("status").eq("id", depends_on_id).execute()
                    dep_status = dep_task_res.data[0]['status'] if dep_task_res.data else 'UNKNOWN'
                    logger.warning(f"    - Depends on: {depends_on_id} (Status: {dep_status})")
                    if dep_status != 'completed':
                        logger.error(f"      -> BLOCKER: This dependency is not completed.")

        # 3. Call the RPC function and see what it returns
        logger.info("\n--- Calling get_ready_tasks() RPC function ---")
        rpc_res = supabase_service.rpc('get_ready_tasks', {'p_workspace_id': workspace_id}).execute()
        
        if rpc_res.data:
            logger.info(f"✅ get_ready_tasks() returned {len(rpc_res.data)} task(s):")
            for ready_task in rpc_res.data:
                logger.info(f"  - {ready_task}")
        else:
            logger.error("❌ get_ready_tasks() returned NO tasks.")

    except Exception as e:
        logger.error(f"An error occurred during inspection: {e}", exc_info=True)

async def main():
    workspace_id = find_latest_workspace_id_from_logs()
    if workspace_id:
        await inspect_task_dependencies(workspace_id)

if __name__ == "__main__":
    asyncio.run(main())
