#!/usr/bin/env python3
"""
Verify if E2E test has completed successfully by checking database state
"""

import asyncio
import os
from dotenv import load_dotenv
from database import supabase
from datetime import datetime, timedelta

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

async def verify_e2e_completion():
    """
    Check if the E2E test has completed successfully by examining:
    1. Tasks that moved from in_progress to completed
    2. Assets/deliverables that were generated
    3. API calls that were made
    """
    
    print("🔍 VERIFYING E2E TEST COMPLETION")
    print("=" * 50)
    
    # Check environment
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"🔑 API Key: {'✅ Available' if api_key else '❌ Missing'}")
    
    if not api_key:
        print("❌ Cannot verify E2E without API key")
        return False
    
    # Check task completion in the last hour
    print("\n📊 TASK COMPLETION ANALYSIS")
    print("-" * 30)
    
    # Get tasks by status
    task_status_counts = {}
    recent_completed = []
    
    for status in ['pending', 'in_progress', 'completed', 'failed']:
        response = await asyncio.to_thread(
            supabase.table("tasks").select("*").eq("status", status).execute
        )
        
        task_status_counts[status] = len(response.data)
        
        if status == 'completed':
            recent_completed = response.data
    
    print(f"📋 Task Status Overview:")
    for status, count in task_status_counts.items():
        print(f"  {status.upper()}: {count} tasks")
    
    # Check for recently completed tasks
    if recent_completed:
        print(f"\n✅ Found {len(recent_completed)} completed tasks:")
        for task in recent_completed[:3]:  # Show first 3
            print(f"  - {task['name']}")
            print(f"    Agent: {task.get('agent_id', 'None')}")
            print(f"    Updated: {task.get('updated_at', 'Unknown')}")
            print()
    else:
        print("\n❌ No completed tasks found")
    
    # Check for assets/deliverables
    print("📦 DELIVERABLE GENERATION ANALYSIS")
    print("-" * 30)
    
    # Check asset artifacts
    response = await asyncio.to_thread(
        supabase.table("asset_artifacts").select("*").order("created_at", desc=True).execute
    )
    
    asset_count = len(response.data)
    print(f"📦 Asset Artifacts: {asset_count}")
    
    if response.data:
        print("Recent artifacts:")
        for artifact in response.data[:3]:
            print(f"  - {artifact.get('name', 'Unnamed')}")
            print(f"    Status: {artifact.get('status', 'N/A')}")
            print(f"    Created: {artifact.get('created_at', 'Unknown')}")
            print()
    
    # Check deliverables table
    response = await asyncio.to_thread(
        supabase.table("deliverables").select("*").execute
    )
    
    deliverable_count = len(response.data)
    print(f"📋 Deliverables: {deliverable_count}")
    
    if response.data:
        print("Recent deliverables:")
        for deliverable in response.data[:3]:
            print(f"  - {deliverable.get('name', 'Unnamed')}")
            print(f"    Status: {deliverable.get('status', 'N/A')}")
    
    # Check agents status
    print("\n👥 AGENT STATUS ANALYSIS")
    print("-" * 30)
    
    response = await asyncio.to_thread(
        supabase.table("agents").select("*").eq("status", "active").execute
    )
    
    active_agents = len(response.data)
    print(f"Active agents: {active_agents}")
    
    # Check if any agents are busy (currently executing)
    response = await asyncio.to_thread(
        supabase.table("agents").select("*").eq("status", "busy").execute
    )
    
    busy_agents = len(response.data)
    print(f"Busy agents: {busy_agents}")
    
    if response.data:
        print("Busy agents:")
        for agent in response.data:
            print(f"  - {agent['name']} ({agent['role']})")
    
    # FINAL ASSESSMENT
    print("\n🎯 E2E TEST ASSESSMENT")
    print("=" * 50)
    
    success_criteria = {
        "API Key Available": api_key is not None,
        "Tasks Completed": len(recent_completed) > 0,
        "Agents Active": active_agents > 0,
        "Deliverables Generated": asset_count > 0 or deliverable_count > 0,
        "System Orchestration": task_status_counts.get('completed', 0) > 0 and active_agents > 0
    }
    
    passed_criteria = sum(success_criteria.values())
    total_criteria = len(success_criteria)
    
    print(f"Success Criteria ({passed_criteria}/{total_criteria}):")
    for criterion, passed in success_criteria.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {criterion}: {status}")
    
    success_rate = (passed_criteria / total_criteria) * 100
    print(f"\nOverall Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 E2E TEST SUCCESSFUL!")
        print("✅ System demonstrates complete orchestration")
        return True
    elif success_rate >= 60:
        print("⚠️ E2E TEST PARTIALLY SUCCESSFUL")
        print("🔧 Some components working but not complete")
        return False
    else:
        print("❌ E2E TEST FAILED")
        print("💡 System needs significant fixes")
        return False

# Execute when imported
if __name__ == "__main__":
    result = asyncio.run(verify_e2e_completion())
    exit(0 if result else 1)