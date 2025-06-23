#!/usr/bin/env python3
"""
Cleanup orphaned workspaces and tasks
This script identifies and optionally cleans up:
1. Workspaces with status 'created' but no agents (no team approved)
2. Tasks in workspaces without agents
"""

import asyncio
import sys
import os
from typing import List, Dict, Any
from datetime import datetime, timedelta

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_supabase_client

class OrphanedWorkspaceCleanup:
    def __init__(self, dry_run: bool = True):
        self.supabase = get_supabase_client()
        self.dry_run = dry_run
        
    async def find_orphaned_workspaces(self) -> List[Dict[str, Any]]:
        """Find workspaces with status 'created' and no agents"""
        try:
            # Get all workspaces with status 'created'
            workspaces_response = self.supabase.table('workspaces').select('*').eq('status', 'created').execute()
            workspaces = workspaces_response.data or []
            
            orphaned = []
            
            for workspace in workspaces:
                workspace_id = workspace['id']
                
                # Check if workspace has any agents
                agents_response = self.supabase.table('agents').select('id').eq('workspace_id', workspace_id).execute()
                agents = agents_response.data or []
                
                # Check if workspace has any tasks
                tasks_response = self.supabase.table('tasks').select('id,description,status').eq('workspace_id', workspace_id).execute()
                tasks = tasks_response.data or []
                
                if len(agents) == 0:  # No agents = orphaned
                    orphaned.append({
                        'workspace': workspace,
                        'agent_count': len(agents),
                        'task_count': len(tasks),
                        'tasks': tasks,
                        'created_days_ago': self._calculate_days_ago(workspace['created_at'])
                    })
            
            return orphaned
            
        except Exception as e:
            print(f"Error finding orphaned workspaces: {e}")
            return []
    
    async def find_tasks_without_agents(self) -> List[Dict[str, Any]]:
        """Find tasks in workspaces that have no agents"""
        try:
            # Get all pending tasks
            tasks_response = self.supabase.table('tasks').select('*').eq('status', 'pending').execute()
            tasks = tasks_response.data or []
            
            problematic_tasks = []
            
            for task in tasks:
                workspace_id = task['workspace_id']
                
                # Check if workspace has any agents
                agents_response = self.supabase.table('agents').select('id,role').eq('workspace_id', workspace_id).execute()
                agents = agents_response.data or []
                
                if len(agents) == 0:
                    problematic_tasks.append({
                        'task': task,
                        'workspace_id': workspace_id,
                        'agent_count': len(agents)
                    })
            
            return problematic_tasks
            
        except Exception as e:
            print(f"Error finding tasks without agents: {e}")
            return []
    
    async def cleanup_orphaned_workspaces(self, orphaned_workspaces: List[Dict[str, Any]], max_age_days: int = 1):
        """Cleanup orphaned workspaces older than max_age_days"""
        cleaned_count = 0
        
        for orphaned in orphaned_workspaces:
            workspace = orphaned['workspace']
            workspace_id = workspace['id']
            days_old = orphaned['created_days_ago']
            
            if days_old >= max_age_days:
                print(f"\n🗑️ Cleaning workspace {workspace_id} ('{workspace['name']}') - {days_old} days old")
                print(f"   Tasks to remove: {orphaned['task_count']}")
                
                if not self.dry_run:
                    try:
                        # First, delete all tasks in the workspace
                        tasks_delete = self.supabase.table('tasks').delete().eq('workspace_id', workspace_id).execute()
                        print(f"   ✅ Deleted {len(tasks_delete.data or [])} tasks")
                        
                        # Delete workspace goals
                        goals_delete = self.supabase.table('workspace_goals').delete().eq('workspace_id', workspace_id).execute()
                        print(f"   ✅ Deleted {len(goals_delete.data or [])} goals")
                        
                        # Delete workspace insights
                        insights_delete = self.supabase.table('workspace_insights').delete().eq('workspace_id', workspace_id).execute()
                        print(f"   ✅ Deleted {len(insights_delete.data or [])} insights")
                        
                        # Delete the workspace itself
                        workspace_delete = self.supabase.table('workspaces').delete().eq('id', workspace_id).execute()
                        print(f"   ✅ Deleted workspace")
                        
                        cleaned_count += 1
                        
                    except Exception as e:
                        print(f"   ❌ Failed to delete workspace {workspace_id}: {e}")
                else:
                    print(f"   🔍 DRY RUN: Would delete workspace and {orphaned['task_count']} tasks")
                    cleaned_count += 1
            else:
                print(f"\n⏳ Keeping workspace {workspace_id} - only {days_old} days old (threshold: {max_age_days})")
        
        return cleaned_count
    
    async def cleanup_orphaned_tasks(self, orphaned_tasks: List[Dict[str, Any]]):
        """Cleanup tasks without agents"""
        cleaned_count = 0
        
        for orphaned in orphaned_tasks:
            task = orphaned['task']
            task_id = task['id']
            workspace_id = orphaned['workspace_id']
            
            print(f"\n🗑️ Cleaning task {task_id} in workspace {workspace_id}")
            print(f"   Description: {task.get('description', 'No description')}")
            
            if not self.dry_run:
                try:
                    task_delete = self.supabase.table('tasks').delete().eq('id', task_id).execute()
                    print(f"   ✅ Deleted task")
                    cleaned_count += 1
                except Exception as e:
                    print(f"   ❌ Failed to delete task {task_id}: {e}")
            else:
                print(f"   🔍 DRY RUN: Would delete task")
                cleaned_count += 1
        
        return cleaned_count
    
    def _calculate_days_ago(self, timestamp_str: str) -> int:
        """Calculate days ago from a timestamp string"""
        try:
            # Handle different timestamp formats
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1] + '+00:00'
            elif not timestamp_str.endswith('+00:00') and 'T' in timestamp_str:
                if '+' not in timestamp_str:
                    timestamp_str += '+00:00'
            
            created_time = datetime.fromisoformat(timestamp_str)
            now = datetime.now(created_time.tzinfo)  # Use same timezone
            return (now - created_time).days
        except Exception as e:
            print(f"Warning: Could not parse timestamp {timestamp_str}: {e}")
            return 0

async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Cleanup orphaned workspaces and tasks')
    parser.add_argument('--dry-run', action='store_true', default=True, help='Show what would be cleaned without actually deleting')
    parser.add_argument('--execute', action='store_true', help='Actually perform the cleanup')
    parser.add_argument('--max-age-days', type=int, default=1, help='Maximum age in days for workspaces to keep (default: 1)')
    
    args = parser.parse_args()
    
    dry_run = not args.execute
    if dry_run:
        print("🔍 DRY RUN MODE - No actual changes will be made")
        print("Use --execute to actually perform cleanup")
    else:
        print("⚠️ EXECUTION MODE - Changes will be made!")
    
    print("=" * 60)
    
    cleanup = OrphanedWorkspaceCleanup(dry_run=dry_run)
    
    # Find orphaned workspaces
    print("\n📊 Finding orphaned workspaces...")
    orphaned_workspaces = await cleanup.find_orphaned_workspaces()
    
    print(f"\n📋 Found {len(orphaned_workspaces)} orphaned workspaces:")
    for orphaned in orphaned_workspaces:
        workspace = orphaned['workspace']
        print(f"  • {workspace['id']} - '{workspace['name']}' ({orphaned['created_days_ago']} days old, {orphaned['task_count']} tasks)")
    
    # Find orphaned tasks
    print("\n📊 Finding tasks without agents...")
    orphaned_tasks = await cleanup.find_tasks_without_agents()
    
    print(f"\n📋 Found {len(orphaned_tasks)} tasks without agents:")
    for orphaned in orphaned_tasks:
        task = orphaned['task']
        print(f"  • {task['id']} - '{task.get('description', 'No description')}' (workspace: {orphaned['workspace_id']})")
    
    # Perform cleanup if requested
    if len(orphaned_workspaces) > 0 or len(orphaned_tasks) > 0:
        print(f"\n🧹 Cleanup Summary:")
        
        # Cleanup orphaned workspaces
        if len(orphaned_workspaces) > 0:
            workspaces_cleaned = await cleanup.cleanup_orphaned_workspaces(orphaned_workspaces, args.max_age_days)
            print(f"   Orphaned workspaces processed: {workspaces_cleaned}")
        
        # Cleanup orphaned tasks
        if len(orphaned_tasks) > 0:
            tasks_cleaned = await cleanup.cleanup_orphaned_tasks(orphaned_tasks)
            print(f"   Orphaned tasks processed: {tasks_cleaned}")
        
        if dry_run:
            print("\n🔍 This was a dry run. Use --execute to actually perform the cleanup.")
        else:
            print("\n✅ Cleanup completed!")
    else:
        print("\n✨ No orphaned workspaces or tasks found!")

if __name__ == "__main__":
    asyncio.run(main())