#!/usr/bin/env python3
"""
Manual trigger for autonomous task recovery
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from services.autonomous_task_recovery import auto_recover_workspace_tasks
from database import list_tasks, get_workspace

async def main():
    workspace_id = "0de74da8-d2a6-47c3-9f08-3824bf1604e0"
    
    print(f"🔧 MANUAL RECOVERY TRIGGER for workspace {workspace_id}")
    print("=" * 60)
    
    # Check workspace
    workspace = await get_workspace(workspace_id)
    if not workspace:
        print(f"❌ Workspace {workspace_id} not found")
        return
    
    print(f"✅ Found workspace: {workspace['name']}")
    print(f"   Status: {workspace['status']}")
    
    # Check failed tasks
    tasks = await list_tasks(workspace_id)
    failed_tasks = [t for t in tasks if t.get('status') == 'failed']
    
    print(f"\n📊 Task Status:")
    print(f"   Total tasks: {len(tasks)}")
    print(f"   Failed tasks: {len(failed_tasks)}")
    
    if failed_tasks:
        print(f"\n🚨 Failed Tasks:")
        for task in failed_tasks:
            error_msg = task.get('result', {}).get('error_message', 'Unknown error')
            print(f"   - {task['id'][:8]}... {task['name']}")
            print(f"     Error: {error_msg}")
    
    if not failed_tasks:
        print("\n✅ No failed tasks to recover")
        return
    
    # Trigger recovery
    print(f"\n🤖 TRIGGERING AUTONOMOUS RECOVERY...")
    print("-" * 40)
    
    try:
        result = await auto_recover_workspace_tasks(workspace_id)
        
        print(f"\n📈 RECOVERY RESULTS:")
        print(f"   Success: {result.get('success')}")
        print(f"   Total failed tasks: {result.get('total_failed_tasks', 0)}")
        print(f"   Successfully recovered: {result.get('successful_recoveries', 0)}")
        print(f"   Recovery rate: {result.get('recovery_rate', 0):.1%}")
        
        if result.get('recovery_results'):
            print(f"\n📝 Recovery Details:")
            for recovery in result.get('recovery_results', []):
                task_id = recovery.get('task_id', 'unknown')
                success = recovery.get('success', False)
                strategy = recovery.get('strategy', 'unknown')
                status = "✅" if success else "❌"
                print(f"   {status} Task {task_id[:8]}... - Strategy: {strategy}")
                if not success and recovery.get('error'):
                    print(f"      Error: {recovery['error']}")
        
        print(f"\n✅ RECOVERY COMPLETE")
        
    except Exception as e:
        print(f"\n❌ RECOVERY FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())