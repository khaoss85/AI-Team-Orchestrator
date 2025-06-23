#!/usr/bin/env python3
"""
Cleanup script to remove duplicate tasks and reset workspace status
"""

import os
import sys
import logging
from datetime import datetime
from collections import defaultdict
from typing import Dict, List

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import supabase

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_duplicate_tasks(workspace_id: str = None) -> Dict[str, int]:
    """
    Remove duplicate tasks keeping only the oldest instance of each unique task name
    """
    try:
        # Get all tasks, optionally filtered by workspace
        query = supabase.table("tasks").select("*")
        if workspace_id:
            query = query.eq("workspace_id", workspace_id)
        
        response = query.execute()
        all_tasks = response.data or []
        
        logger.info(f"Found {len(all_tasks)} total tasks to analyze")
        
        # Group tasks by workspace and name
        workspace_tasks = defaultdict(lambda: defaultdict(list))
        
        for task in all_tasks:
            ws_id = task.get("workspace_id")
            task_name = task.get("name", "").strip()
            workspace_tasks[ws_id][task_name].append(task)
        
        # Find duplicates and mark for deletion
        tasks_to_delete = []
        stats = {
            "total_tasks": len(all_tasks),
            "duplicate_groups": 0,
            "tasks_to_delete": 0,
            "workspaces_affected": 0
        }
        
        for ws_id, tasks_by_name in workspace_tasks.items():
            workspace_has_duplicates = False
            
            for task_name, task_group in tasks_by_name.items():
                if len(task_group) > 1:
                    # Sort by created_at to keep the oldest
                    task_group.sort(key=lambda x: x.get("created_at", ""))
                    
                    # Keep the first (oldest), delete the rest
                    keep_task = task_group[0]
                    duplicates = task_group[1:]
                    
                    logger.info(f"Found {len(duplicates)} duplicates of '{task_name}' in workspace {ws_id}")
                    logger.info(f"  Keeping task {keep_task['id']} (created: {keep_task.get('created_at')})")
                    
                    for dup in duplicates:
                        logger.info(f"  Deleting task {dup['id']} (created: {dup.get('created_at')})")
                        tasks_to_delete.append(dup['id'])
                    
                    stats["duplicate_groups"] += 1
                    workspace_has_duplicates = True
            
            if workspace_has_duplicates:
                stats["workspaces_affected"] += 1
        
        stats["tasks_to_delete"] = len(tasks_to_delete)
        
        # Delete duplicate tasks
        if tasks_to_delete:
            logger.info(f"Deleting {len(tasks_to_delete)} duplicate tasks...")
            
            # Delete in batches to avoid API limits
            batch_size = 50
            deleted_count = 0
            
            for i in range(0, len(tasks_to_delete), batch_size):
                batch = tasks_to_delete[i:i + batch_size]
                
                response = supabase.table("tasks").delete().in_("id", batch).execute()
                
                if response.data:
                    deleted_count += len(response.data)
                    logger.info(f"Deleted batch of {len(response.data)} tasks")
            
            logger.info(f"Successfully deleted {deleted_count} duplicate tasks")
            stats["tasks_deleted"] = deleted_count
        else:
            logger.info("No duplicate tasks found")
            stats["tasks_deleted"] = 0
        
        return stats
        
    except Exception as e:
        logger.error(f"Error cleaning duplicate tasks: {e}")
        return {"error": str(e)}

def reset_workspace_status(workspace_id: str = None) -> Dict[str, int]:
    """
    Reset workspace status from needs_intervention back to active
    """
    try:
        query = supabase.table("workspaces").select("id, name, status")
        if workspace_id:
            query = query.eq("id", workspace_id)
        
        response = query.eq("status", "needs_intervention").execute()
        workspaces = response.data or []
        
        logger.info(f"Found {len(workspaces)} workspaces in 'needs_intervention' status")
        
        reset_count = 0
        for workspace in workspaces:
            ws_id = workspace["id"]
            ws_name = workspace.get("name", "Unknown")
            
            # Reset to active status
            update_response = supabase.table("workspaces").update({
                "status": "active",
                "updated_at": datetime.now().isoformat()
            }).eq("id", ws_id).execute()
            
            if update_response.data:
                logger.info(f"Reset workspace '{ws_name}' ({ws_id}) from needs_intervention to active")
                reset_count += 1
        
        return {"workspaces_reset": reset_count}
        
    except Exception as e:
        logger.error(f"Error resetting workspace status: {e}")
        return {"error": str(e)}

def main():
    """Main cleanup function"""
    logger.info("🧹 Starting duplicate task cleanup...")
    
    # Check if specific workspace ID provided
    workspace_id = None
    if len(sys.argv) > 1:
        workspace_id = sys.argv[1]
        logger.info(f"Cleaning workspace: {workspace_id}")
    else:
        logger.info("Cleaning all workspaces")
    
    # Clean duplicate tasks
    cleanup_stats = clean_duplicate_tasks(workspace_id)
    
    if "error" in cleanup_stats:
        logger.error(f"Cleanup failed: {cleanup_stats['error']}")
        return 1
    
    # Reset workspace status
    reset_stats = reset_workspace_status(workspace_id)
    
    # Summary
    logger.info("🎉 Cleanup completed!")
    logger.info(f"📊 Summary:")
    logger.info(f"  - Total tasks analyzed: {cleanup_stats.get('total_tasks', 0)}")
    logger.info(f"  - Duplicate groups found: {cleanup_stats.get('duplicate_groups', 0)}")
    logger.info(f"  - Tasks deleted: {cleanup_stats.get('tasks_deleted', 0)}")
    logger.info(f"  - Workspaces affected: {cleanup_stats.get('workspaces_affected', 0)}")
    logger.info(f"  - Workspaces reset: {reset_stats.get('workspaces_reset', 0)}")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)