#!/usr/bin/env python3
"""
Test Workspace Recovery System

Tests the new workspace health manager's ability to detect and recover
from workspaces stuck in 'processing_tasks' status.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import supabase
from services.workspace_health_manager import workspace_health_manager

async def main():
    """Test workspace recovery system"""
    
    print("🧪 TESTING WORKSPACE RECOVERY SYSTEM")
    print("=" * 60)
    
    # 1. Find an available workspace
    print(f"\n📍 STEP 1: Finding available workspace")
    all_workspaces = supabase.table("workspaces").select("id, name, status").execute()
    
    if not all_workspaces.data:
        print(f"❌ No workspaces found in database")
        return
    
    workspace = all_workspaces.data[0]  # Use first workspace
    workspace_id = workspace["id"]
    
    print(f"   Using workspace: {workspace['name']} ({workspace_id})")
    print(f"   Current status: {workspace['status']}")
    
    # Get full workspace details
    workspace_response = supabase.table("workspaces").select("*").eq("id", workspace_id).single().execute()
    
    if not workspace_response.data:
        print(f"❌ Workspace {workspace_id} not found")
        return
    
    workspace = workspace_response.data
    current_status = workspace.get("status")
    print(f"   Current status: {current_status}")
    print(f"   Last updated: {workspace.get('updated_at')}")
    
    # 2. If not already stuck, simulate stuck state for testing
    if current_status != "processing_tasks":
        print(f"\n🔧 STEP 2: Simulating stuck 'processing_tasks' state")
        
        # Set to processing_tasks with old timestamp to simulate stuck state
        old_timestamp = "2025-01-01T00:00:00.000000Z"  # Very old timestamp
        supabase.table("workspaces").update({
            "status": "processing_tasks",
            "updated_at": old_timestamp
        }).eq("id", workspace_id).execute()
        
        print(f"   ✅ Set workspace to 'processing_tasks' with old timestamp")
    else:
        print(f"\n🔍 STEP 2: Workspace already in 'processing_tasks' state")
    
    # 3. Test individual workspace health check
    print(f"\n🏥 STEP 3: Running individual workspace health check")
    health_report = await workspace_health_manager.check_workspace_health_with_recovery(
        workspace_id, attempt_auto_recovery=True
    )
    
    print(f"   Health score: {health_report.overall_score:.1f}%")
    print(f"   Is healthy: {health_report.is_healthy}")
    print(f"   Issues found: {len(health_report.issues)}")
    print(f"   Can auto-recover: {health_report.can_auto_recover}")
    
    if health_report.issues:
        print(f"\n   📋 Issues detected:")
        for issue in health_report.issues:
            print(f"      - {issue.level.value.upper()}: {issue.description}")
            if issue.auto_recoverable:
                print(f"        → Auto-recoverable with {issue.recovery_confidence:.0%} confidence")
    
    if health_report.recommended_actions:
        print(f"\n   💡 Recommendations:")
        for action in health_report.recommended_actions:
            print(f"      - {action}")
    
    # 4. Test system-wide monitoring
    print(f"\n🌐 STEP 4: Running system-wide workspace monitoring")
    system_monitoring_result = await workspace_health_manager.monitor_all_workspaces_for_stuck_processing()
    
    print(f"   Stuck workspaces found: {system_monitoring_result.get('stuck_workspaces', 0)}")
    print(f"   Workspaces recovered: {system_monitoring_result.get('recovered', 0)}")
    
    if 'error' in system_monitoring_result:
        print(f"   ❌ Error: {system_monitoring_result['error']}")
    
    if system_monitoring_result.get('details'):
        print(f"\n   📊 Recovery details:")
        for ws_id, details in system_monitoring_result['details'].items():
            print(f"      - {details['name']} ({ws_id[:8]}...)")
            print(f"        Recovered: {details['was_recovered']}")
            print(f"        Health score: {details['health_score']:.1f}%")
    
    # 5. Final status check
    print(f"\n📍 STEP 5: Final workspace status check")
    final_workspace = supabase.table("workspaces").select("status, updated_at").eq("id", workspace_id).single().execute()
    
    if final_workspace.data:
        final_status = final_workspace.data.get("status")
        final_updated = final_workspace.data.get("updated_at")
        print(f"   Final status: {final_status}")
        print(f"   Last updated: {final_updated}")
        
        if final_status == "active":
            print(f"   ✅ SUCCESS: Workspace recovered to 'active' status")
        elif final_status == "processing_tasks":
            print(f"   ⚠️  WARNING: Workspace still in 'processing_tasks' status")
        else:
            print(f"   ℹ️  INFO: Workspace in '{final_status}' status")
    
    # 6. Summary
    print(f"\n📈 RECOVERY TEST SUMMARY")
    print(f"   Health Manager: {'✅ Working' if health_report else '❌ Failed'}")
    print(f"   Issue Detection: {'✅ Working' if health_report.issues else '⚠️  No issues detected'}")
    print(f"   Auto Recovery: {'✅ Attempted' if health_report.can_auto_recover else '❌ Not attempted'}")
    print(f"   System Monitor: {'✅ Working' if system_monitoring_result else '❌ Failed'}")
    
    if final_workspace.data and final_workspace.data.get("status") == "active":
        print(f"\n🎉 OVERALL RESULT: Recovery system is working correctly!")
    else:
        print(f"\n⚠️  OVERALL RESULT: Recovery system may need additional work")

if __name__ == "__main__":
    asyncio.run(main())