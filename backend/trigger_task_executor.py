#!/usr/bin/env python3
"""
Trigger the task executor to pick up pending tasks for the workspace
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

workspace_id = "f79d87cc-b61f-491d-9226-4220e39e71ad"
backend_url = "http://localhost:8000"

print("\n" + "="*80)
print("🚀 TRIGGERING TASK EXECUTOR")
print("="*80)

# 1. First check task status
print("\n📊 Checking current task status...")
try:
    response = requests.get(f"{backend_url}/api/tasks", params={"workspace_id": workspace_id})
    if response.status_code == 200:
        tasks = response.json()
        
        # Count by status
        status_count = {}
        for task in tasks:
            status = task.get("status", "unknown")
            status_count[status] = status_count.get(status, 0) + 1
        
        print(f"Total tasks: {len(tasks)}")
        for status, count in status_count.items():
            print(f"  - {status}: {count}")
            
        pending_count = status_count.get("pending", 0)
        if pending_count > 0:
            print(f"\n⚠️ {pending_count} tasks are pending and need execution")
    else:
        print(f"❌ Failed to fetch tasks: {response.status_code}")
except Exception as e:
    print(f"❌ Error fetching tasks: {e}")

# 2. Trigger health check which may restart executor
print("\n🔧 Triggering system health check...")
try:
    response = requests.get(f"{backend_url}/api/health")
    if response.status_code == 200:
        health = response.json()
        print(f"✅ System health: {health.get('overall_status', 'unknown')}")
        print(f"   Score: {health.get('health_score', 0)}/100")
        
        executor_status = health.get("components", {}).get("executor", {})
        print(f"   Executor: {executor_status.get('status', 'unknown')}")
    else:
        print(f"❌ Health check failed: {response.status_code}")
except Exception as e:
    print(f"❌ Error checking health: {e}")

# 3. Try to trigger immediate goal validation which may create corrective tasks
print("\n🎯 Triggering immediate goal validation...")
try:
    response = requests.post(
        f"{backend_url}/api/workspaces/{workspace_id}/validate-goals",
        json={"immediate": True}
    )
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"✅ Goal validation triggered")
        if "corrective_tasks_created" in result:
            print(f"   Corrective tasks created: {result['corrective_tasks_created']}")
    else:
        print(f"⚠️ Goal validation returned: {response.status_code}")
except Exception as e:
    print(f"⚠️ Could not trigger goal validation: {e}")

# 4. Check executor status
print("\n🤖 Checking executor status...")
try:
    response = requests.get(f"{backend_url}/api/executor/status")
    if response.status_code == 200:
        status = response.json()
        print(f"✅ Executor is {status.get('status', 'unknown')}")
        print(f"   Queue size: {status.get('queue_size', 0)}")
        print(f"   Processed: {status.get('processed_count', 0)}")
    else:
        print(f"⚠️ Could not check executor status: {response.status_code}")
except Exception as e:
    print(f"⚠️ Error checking executor: {e}")

print("\n" + "="*80)
print("💡 RECOMMENDATIONS:")
print("="*80)
print("1. The task executor runs automatically every 30 seconds")
print("2. Pending tasks should be picked up in the next cycle")
print("3. Check the backend logs for task execution details")
print("4. Monitor /api/tasks endpoint to see status changes")
print("="*80)