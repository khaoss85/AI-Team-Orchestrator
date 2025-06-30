#!/usr/bin/env python3
"""
Simple Deliverable Debug Script

Directly queries the database to find workspaces and check deliverable creation status.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import supabase, get_workspace, list_tasks
from deliverable_aggregator import deliverable_aggregator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def get_all_workspaces() -> List[Dict]:
    """Get all workspaces from database"""
    try:
        result = supabase.table("workspaces").select("*").order("created_at", desc=True).limit(20).execute()
        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Error getting workspaces: {e}")
        return []

async def analyze_workspace_deliverable_issue(workspace_id: str) -> Dict[str, Any]:
    """Analyze specific workspace for deliverable creation issues"""
    
    analysis = {
        "workspace_id": workspace_id,
        "analysis_time": datetime.now().isoformat(),
        "issues_found": [],
        "status": "unknown"
    }
    
    try:
        # Get workspace
        workspace = await get_workspace(workspace_id)
        if not workspace:
            analysis["issues_found"].append("Workspace not found")
            analysis["status"] = "workspace_missing"
            return analysis
        
        # Get tasks
        tasks = await list_tasks(workspace_id)
        completed_tasks = [t for t in tasks if t.get("status") == "completed"]
        
        logger.info(f"Workspace {workspace_id}: {len(completed_tasks)}/{len(tasks)} completed tasks")
        
        # Check min tasks threshold
        min_tasks = deliverable_aggregator.min_completed_tasks
        if len(completed_tasks) < min_tasks:
            analysis["issues_found"].append(f"Not enough completed tasks: {len(completed_tasks)} < {min_tasks}")
        
        # Check completion rate
        completion_rate = len(completed_tasks) / len(tasks) if tasks else 0
        threshold = deliverable_aggregator.readiness_threshold
        if completion_rate < threshold:
            analysis["issues_found"].append(f"Completion rate too low: {completion_rate:.2%} < {threshold:.2%}")
        
        # Check if deliverable already exists
        try:
            deliverable_exists = await deliverable_aggregator._deliverable_exists(workspace_id)
            if deliverable_exists:
                analysis["issues_found"].append("Deliverable already exists")
        except Exception as e:
            analysis["issues_found"].append(f"Error checking deliverable existence: {e}")
        
        # Check readiness using internal method
        try:
            is_ready = await deliverable_aggregator._is_ready_for_deliverable(workspace_id)
            analysis["ready_for_deliverable"] = is_ready
            if not is_ready:
                analysis["issues_found"].append("Internal readiness check failed")
        except Exception as e:
            analysis["issues_found"].append(f"Error in readiness check: {e}")
        
        # Check for structured output
        structured_output_tasks = []
        for task in completed_tasks:
            result = task.get('result', {}) or {}
            detailed_json = result.get('detailed_results_json', '')
            summary = result.get('summary', '')
            
            if detailed_json or (summary and len(summary) > 100):
                structured_output_tasks.append(task.get("id"))
        
        if not structured_output_tasks:
            analysis["issues_found"].append("No tasks with structured output")
        
        analysis["data"] = {
            "workspace_goal": workspace.get("goal", ""),
            "total_tasks": len(tasks),
            "completed_tasks": len(completed_tasks),
            "completion_rate": completion_rate,
            "structured_output_tasks": len(structured_output_tasks),
            "min_tasks_threshold": min_tasks,
            "readiness_threshold": threshold
        }
        
        if not analysis["issues_found"]:
            analysis["status"] = "ready_for_deliverable"
        else:
            analysis["status"] = "blocked"
        
        return analysis
        
    except Exception as e:
        analysis["issues_found"].append(f"Analysis error: {e}")
        analysis["status"] = "error"
        return analysis

async def main():
    """Main function"""
    
    print("🔍 DELIVERABLE CREATION DEBUG ANALYSIS")
    print("="*60)
    
    # Get workspaces
    workspaces = await get_all_workspaces()
    print(f"Found {len(workspaces)} workspaces")
    
    if not workspaces:
        print("❌ No workspaces found")
        return
    
    # Analyze each workspace
    ready_count = 0
    blocked_count = 0
    
    for workspace in workspaces[:10]:  # Limit to first 10
        workspace_id = workspace.get("id")
        if not workspace_id:
            continue
            
        analysis = await analyze_workspace_deliverable_issue(workspace_id)
        
        status_emoji = {
            "ready_for_deliverable": "✅",
            "blocked": "❌", 
            "error": "⚠️",
            "workspace_missing": "🚫",
            "unknown": "❓"
        }.get(analysis["status"], "❓")
        
        print(f"\n{status_emoji} Workspace: {workspace_id}")
        print(f"   Goal: {workspace.get('goal', 'No goal')[:80]}...")
        print(f"   Status: {analysis['status']}")
        
        if "data" in analysis:
            data = analysis["data"]
            print(f"   Tasks: {data['completed_tasks']}/{data['total_tasks']} completed ({data['completion_rate']:.1%})")
            print(f"   Structured Output Tasks: {data['structured_output_tasks']}")
            print(f"   Thresholds: ≥{data['min_tasks_threshold']} tasks, ≥{data['readiness_threshold']:.1%} completion")
        
        if analysis["issues_found"]:
            print("   Issues:")
            for issue in analysis["issues_found"]:
                print(f"     - {issue}")
        
        if analysis["status"] == "ready_for_deliverable":
            ready_count += 1
        elif analysis["status"] == "blocked":
            blocked_count += 1
    
    print(f"\n📊 SUMMARY:")
    print(f"   Ready for deliverable: {ready_count}")
    print(f"   Blocked: {blocked_count}")
    print(f"   Other: {len(workspaces) - ready_count - blocked_count}")
    
    # Configuration info
    print(f"\n⚙️ CONFIGURATION:")
    print(f"   Min completed tasks: {deliverable_aggregator.min_completed_tasks}")
    print(f"   Readiness threshold: {deliverable_aggregator.readiness_threshold:.1%}")
    
    # Environment variables
    import os
    print(f"\n🌍 ENVIRONMENT:")
    print(f"   DELIVERABLE_READINESS_THRESHOLD: {os.getenv('DELIVERABLE_READINESS_THRESHOLD', 'not set')}")
    print(f"   MIN_COMPLETED_TASKS_FOR_DELIVERABLE: {os.getenv('MIN_COMPLETED_TASKS_FOR_DELIVERABLE', 'not set')}")
    print(f"   USE_ASSET_FIRST_DELIVERABLE: {os.getenv('USE_ASSET_FIRST_DELIVERABLE', 'not set')}")
    print(f"   ENABLE_AUTO_PROJECT_COMPLETION: {os.getenv('ENABLE_AUTO_PROJECT_COMPLETION', 'not set')}")

if __name__ == "__main__":
    asyncio.run(main())