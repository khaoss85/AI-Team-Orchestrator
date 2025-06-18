#!/usr/bin/env python3
"""
Check all feedback requests to understand the current state
"""

import asyncio
import logging
from database import supabase, get_human_feedback_requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_feedback_requests():
    """Check all feedback requests in the system"""
    
    workspace_id = "3b387b5e-51c0-43eb-8e8a-e279e38dbfb5"
    
    print("🔍 Checking All Feedback Requests")
    print("=" * 50)
    
    # Get all feedback requests (any status)
    response = supabase.table("human_feedback_requests").select("*").eq("workspace_id", workspace_id).execute()
    all_requests = response.data
    
    print(f"📋 Found {len(all_requests)} total feedback requests for workspace {workspace_id}")
    
    for req in all_requests:
        print(f"\n  Request ID: {req.get('id')}")
        print(f"  Task ID: {req.get('task_id')}")
        print(f"  Status: {req.get('status')}")
        print(f"  Type: {req.get('request_type')}")
        print(f"  Priority: {req.get('priority')}")
        print(f"  Created: {req.get('created_at')}")
        if req.get('responded_at'):
            print(f"  Responded: {req.get('responded_at')}")
        print(f"  Context: {req.get('context', {})}")
    
    # Check tasks in pending_verification
    print(f"\n📋 Tasks in pending_verification:")
    response = supabase.table("tasks").select("*").eq("workspace_id", workspace_id).eq("status", "pending_verification").execute()
    pending_tasks = response.data
    
    for task in pending_tasks:
        print(f"\n  Task ID: {task.get('id')}")
        print(f"  Name: {task.get('name')}")
        print(f"  Status: {task.get('status')}")
        print(f"  Updated: {task.get('updated_at')}")
        
        # Check if this task has any feedback requests
        matching_requests = [r for r in all_requests if r.get('task_id') == task.get('id')]
        if matching_requests:
            print(f"  📝 Feedback requests for this task:")
            for req in matching_requests:
                print(f"    - {req.get('id')} ({req.get('status')})")
        else:
            print(f"  ❌ No feedback requests found for this task")
    
    # Let's manually create a feedback request if none exist
    if not all_requests and pending_tasks:
        print(f"\n🔧 Creating manual feedback request for testing...")
        
        task = pending_tasks[0]
        task_id = task.get('id')
        
        # Create a feedback request manually
        feedback_data = {
            "workspace_id": workspace_id,
            "task_id": task_id,
            "request_type": "critical_asset_verification",
            "status": "pending",
            "priority": "high",
            "title": f"Verify task: {task.get('name', 'Unknown')}",
            "description": "Manual verification request for testing goal updates",
            "context": {
                "task_name": task.get('name'),
                "created_for_testing": True
            },
            "expires_at": "2025-06-19T10:00:00Z"
        }
        
        response = supabase.table("human_feedback_requests").insert(feedback_data).execute()
        if response.data:
            new_request = response.data[0]
            print(f"  ✅ Created feedback request: {new_request.get('id')}")
            return new_request.get('id')
        else:
            print(f"  ❌ Failed to create feedback request")
    
    return None

if __name__ == "__main__":
    asyncio.run(check_feedback_requests())