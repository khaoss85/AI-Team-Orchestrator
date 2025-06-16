#!/usr/bin/env python3
"""
Cleanup script per task orfani con assigned_to_role: 'no_agents_available'
Questi task non possono mai essere eseguiti e creano loop infiniti.
"""

import asyncio
import logging
from database import supabase
from models import TaskStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def cleanup_orphaned_tasks():
    """Pulisce tutti i task con assigned_to_role 'no_agents_available'"""
    try:
        # Get all tasks with no_agents_available role
        response = supabase.table("tasks").select("*").eq(
            "assigned_to_role", "no_agents_available"
        ).execute()
        
        orphaned_tasks = response.data or []
        
        if not orphaned_tasks:
            logger.info("✅ No orphaned tasks found")
            return
        
        logger.info(f"🧹 Found {len(orphaned_tasks)} orphaned tasks to clean up")
        
        # Group by workspace for reporting
        workspace_counts = {}
        for task in orphaned_tasks:
            workspace_id = task["workspace_id"]
            workspace_counts[workspace_id] = workspace_counts.get(workspace_id, 0) + 1
        
        logger.info("📊 Orphaned tasks by workspace:")
        for workspace_id, count in workspace_counts.items():
            logger.info(f"  - {workspace_id}: {count} tasks")
        
        # Delete all orphaned tasks
        task_ids = [task["id"] for task in orphaned_tasks]
        
        delete_response = supabase.table("tasks").delete().in_(
            "id", task_ids
        ).execute()
        
        logger.info(f"🗑️ Deleted {len(task_ids)} orphaned tasks")
        logger.info("✅ Cleanup completed successfully")
        
        return len(task_ids)
        
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}")
        return 0

async def cleanup_duplicate_urgent_tasks():
    """Pulisce task urgenti duplicati (stesso nome, stesso workspace)"""
    try:
        # Get all urgent tasks
        response = supabase.table("tasks").select("*").like(
            "name", "🚨 URGENT:%"
        ).execute()
        
        urgent_tasks = response.data or []
        
        if not urgent_tasks:
            logger.info("✅ No urgent tasks found")
            return
        
        # Group by workspace and name
        duplicates = {}
        for task in urgent_tasks:
            key = (task["workspace_id"], task["name"])
            if key not in duplicates:
                duplicates[key] = []
            duplicates[key].append(task)
        
        # Find duplicates (more than 1 task with same workspace+name)
        tasks_to_delete = []
        for key, task_list in duplicates.items():
            if len(task_list) > 1:
                # Keep the newest, delete the rest
                task_list.sort(key=lambda x: x["created_at"], reverse=True)
                tasks_to_delete.extend(task_list[1:])  # All except the first (newest)
        
        if not tasks_to_delete:
            logger.info("✅ No duplicate urgent tasks found")
            return 0
        
        logger.info(f"🧹 Found {len(tasks_to_delete)} duplicate urgent tasks to clean up")
        
        # Delete duplicates
        task_ids = [task["id"] for task in tasks_to_delete]
        
        delete_response = supabase.table("tasks").delete().in_(
            "id", task_ids
        ).execute()
        
        logger.info(f"🗑️ Deleted {len(task_ids)} duplicate urgent tasks")
        logger.info("✅ Duplicate cleanup completed successfully")
        
        return len(task_ids)
        
    except Exception as e:
        logger.error(f"❌ Error during duplicate cleanup: {e}")
        return 0

async def main():
    """Main cleanup function"""
    logger.info("🧹 Starting task cleanup process...")
    
    orphaned_count = await cleanup_orphaned_tasks()
    duplicate_count = await cleanup_duplicate_urgent_tasks()
    
    total_cleaned = orphaned_count + duplicate_count
    
    logger.info(f"🎯 Cleanup Summary:")
    logger.info(f"  - Orphaned tasks deleted: {orphaned_count}")
    logger.info(f"  - Duplicate tasks deleted: {duplicate_count}")
    logger.info(f"  - Total tasks cleaned: {total_cleaned}")
    logger.info("✅ All cleanup operations completed")

if __name__ == "__main__":
    asyncio.run(main())