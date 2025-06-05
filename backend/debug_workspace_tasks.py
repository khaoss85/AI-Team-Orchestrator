#!/usr/bin/env python3
"""
Debug script to investigate workspace task data
"""
import os
import sys
import asyncio
import json
from typing import Dict, Any, List

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from database import list_tasks, supabase
from models import TaskStatus

def _is_asset_task(task: Dict) -> bool:
    """Return True if the task appears to be asset-oriented."""
    context_data = task.get("context_data", {}) or {}
    if not isinstance(context_data, dict):
        return False
    return (
        context_data.get("asset_production")
        or context_data.get("asset_oriented_task")
        or "PRODUCE ASSET:" in task.get("name", "").upper()
    )

def _is_final_deliverable_task(task: Dict) -> bool:
    """Check if task has final deliverable flags in context_data"""
    context_data = task.get("context_data", {}) or {}
    if not isinstance(context_data, dict):
        return False
    return (
        context_data.get("final_deliverable", False)
        or context_data.get("is_final_deliverable", False)
        or context_data.get("deliverable_complete", False)
        or task.get("creation_type") == "intelligent_ai_deliverable"
    )

async def debug_workspace_tasks(workspace_id: str):
    """Debug workspace tasks for deliverable analysis"""
    print(f"🔍 Debugging workspace: {workspace_id}")
    print("=" * 60)
    
    try:
        # Get all tasks for workspace
        all_tasks = await list_tasks(workspace_id)
        print(f"📊 Total tasks found: {len(all_tasks)}")
        
        if not all_tasks:
            print("❌ No tasks found in workspace")
            return
        
        # Analyze task breakdown
        status_counts = {}
        creation_type_counts = {}
        asset_tasks = []
        final_deliverable_tasks = []
        intelligent_ai_deliverable_tasks = []
        
        for task in all_tasks:
            # Status breakdown
            status = task.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Creation type breakdown
            creation_type = task.get("creation_type", "unknown")
            creation_type_counts[creation_type] = creation_type_counts.get(creation_type, 0) + 1
            
            # Check if asset task
            if _is_asset_task(task):
                asset_tasks.append(task)
            
            # Check if final deliverable task
            if _is_final_deliverable_task(task):
                final_deliverable_tasks.append(task)
            
            # Check specifically for intelligent_ai_deliverable
            if creation_type == "intelligent_ai_deliverable":
                intelligent_ai_deliverable_tasks.append(task)
        
        # Print status breakdown
        print("\n📈 Task Status Breakdown:")
        for status, count in status_counts.items():
            print(f"  • {status}: {count}")
        
        # Print creation type breakdown
        print("\n🏗️ Creation Type Breakdown:")
        for creation_type, count in creation_type_counts.items():
            print(f"  • {creation_type}: {count}")
        
        # Print asset tasks
        print(f"\n🎯 Asset Tasks Found: {len(asset_tasks)}")
        for task in asset_tasks[:5]:  # Show first 5
            print(f"  • {task.get('name', 'Unnamed')} (ID: {task.get('id')}, Status: {task.get('status')})")
        
        # Print final deliverable tasks
        print(f"\n🚀 Final Deliverable Tasks Found: {len(final_deliverable_tasks)}")
        for task in final_deliverable_tasks[:5]:  # Show first 5
            context_data = task.get("context_data", {})
            print(f"  • {task.get('name', 'Unnamed')}")
            print(f"    - ID: {task.get('id')}")
            print(f"    - Status: {task.get('status')}")
            print(f"    - Creation Type: {task.get('creation_type')}")
            print(f"    - Context flags: {json.dumps({k: v for k, v in context_data.items() if 'final' in k.lower() or 'deliverable' in k.lower()}, indent=6)}")
        
        # Print intelligent AI deliverable tasks specifically
        print(f"\n🤖 Intelligent AI Deliverable Tasks: {len(intelligent_ai_deliverable_tasks)}")
        for task in intelligent_ai_deliverable_tasks:
            print(f"  • {task.get('name', 'Unnamed')}")
            print(f"    - ID: {task.get('id')}")
            print(f"    - Status: {task.get('status')}")
            print(f"    - Created: {task.get('created_at')}")
            print(f"    - Updated: {task.get('updated_at')}")
            
            # Detailed context analysis
            context_data = task.get("context_data", {})
            print(f"    - Context data keys: {list(context_data.keys()) if isinstance(context_data, dict) else 'Not a dict'}")
            
            # Check for result payload
            result = task.get("result")
            if result:
                print(f"    - Has result payload: Yes (type: {type(result).__name__})")
                if isinstance(result, dict):
                    print(f"    - Result keys: {list(result.keys())}")
            else:
                print(f"    - Has result payload: No")
        
        # Check if there are tasks that might be missing from API response
        completed_tasks = [t for t in all_tasks if t.get("status") == "completed"]
        print(f"\n✅ Completed Tasks: {len(completed_tasks)}")
        
        # Find tasks that should be final deliverables but might be missed
        potential_missed_deliverables = []
        for task in completed_tasks:
            task_name = task.get("name", "").upper()
            if any(keyword in task_name for keyword in ["FINAL", "DELIVERABLE", "SUMMARY", "COMPLETE", "PACKAGE"]):
                potential_missed_deliverables.append(task)
        
        print(f"\n🎯 Potential Missed Deliverables (by name pattern): {len(potential_missed_deliverables)}")
        for task in potential_missed_deliverables[:3]:
            print(f"  • {task.get('name')} (Status: {task.get('status')}, Creation: {task.get('creation_type')})")
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main function to run workspace debugging"""
    # You can set a specific workspace ID here or pass as argument
    workspace_id = input("Enter workspace ID to debug (or press Enter for default): ").strip()
    
    if not workspace_id:
        # Try to find the most recent workspace with tasks
        print("🔍 Looking for recent workspace with tasks...")
        try:
            result = supabase.table("workspaces").select("id, name, created_at").order("created_at", desc=True).limit(10).execute()
            
            if result.data:
                print("Recent workspaces:")
                for i, ws in enumerate(result.data[:5]):
                    print(f"  {i+1}. {ws.get('name', 'Unnamed')} (ID: {ws['id']})")
                
                choice = input("Enter workspace number (1-5) or workspace ID: ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(result.data):
                    workspace_id = result.data[int(choice)-1]['id']
                else:
                    workspace_id = choice
        except Exception as e:
            print(f"Error finding workspaces: {e}")
            return
    
    if not workspace_id:
        print("❌ No workspace ID provided")
        return
    
    await debug_workspace_tasks(workspace_id)

if __name__ == "__main__":
    asyncio.run(main())