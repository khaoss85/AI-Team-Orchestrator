#!/usr/bin/env python3

"""
Test script to validate the thinking process completion fix.

This script:
1. Creates an incomplete thinking process (simulating what happens during task execution)
2. Calls the new completion method
3. Verifies that the thinking process is properly completed
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

from services.thinking_process import thinking_engine
from executor import complete_thinking_processes_for_task
from models import TaskStatus
from database import get_supabase_client

async def test_thinking_completion():
    print("🧠 Testing Thinking Process Completion Fix")
    print("=" * 50)
    
    # Test workspace ID (needs to be valid UUID)
    import uuid
    test_workspace = str(uuid.uuid4())
    test_task_id = str(uuid.uuid4())
    
    try:
        # Step 1: Create an incomplete thinking process (simulating executor behavior)
        print("1. Creating incomplete thinking process...")
        
        process_id = await thinking_engine.start_thinking_process(
            workspace_id=test_workspace,
            context=f"Testing task execution: {test_task_id}",
            process_type="task_execution"
        )
        
        # Add initial steps (as executor does)
        await thinking_engine.add_thinking_step(
            process_id=process_id,
            step_type="analysis",
            content="✦ Starting task execution for test",
            confidence=0.8
        )
        
        await thinking_engine.add_thinking_step(
            process_id=process_id,
            step_type="context_loading", 
            content="🔍 Loading task context and workspace environment",
            confidence=0.8
        )
        
        print(f"   Created process: {process_id}")
        
        # Step 2: Verify it's incomplete
        supabase = get_supabase_client()
        process_check = supabase.table("thinking_processes") \
            .select("completed_at") \
            .eq("process_id", process_id) \
            .execute()
            
        if process_check.data and process_check.data[0]["completed_at"] is None:
            print("   ✓ Process is incomplete (as expected)")
        else:
            print("   ✗ Process is already completed (unexpected)")
            return False
        
        # Step 3: Test the completion fix
        print("\n2. Testing completion fix...")
        
        # Call the global completion function
        await complete_thinking_processes_for_task(
            workspace_id=test_workspace,
            task_id=test_task_id,
            status=TaskStatus.COMPLETED.value,
            reason="Test completion successful"
        )
        
        # Step 4: Verify completion
        print("\n3. Verifying completion...")
        
        process_check = supabase.table("thinking_processes") \
            .select("completed_at,final_conclusion,overall_confidence") \
            .eq("process_id", process_id) \
            .execute()
        
        if process_check.data:
            result = process_check.data[0]
            if result["completed_at"] is not None:
                print("   ✓ Process is now completed!")
                print(f"   ✓ Final conclusion: {result['final_conclusion']}")
                print(f"   ✓ Overall confidence: {result['overall_confidence']}")
                
                # Check steps count
                steps_count = supabase.table("thinking_steps") \
                    .select("*", count="exact") \
                    .eq("process_id", process_id) \
                    .execute()
                
                print(f"   ✓ Total steps: {steps_count.count if hasattr(steps_count, 'count') else 'unknown'}")
                
                return True
            else:
                print("   ✗ Process is still incomplete")
                return False
        else:
            print("   ✗ Process not found")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup: Remove test process
        try:
            supabase.table("thinking_steps").delete().eq("process_id", process_id).execute()
            supabase.table("thinking_processes").delete().eq("process_id", process_id).execute()
            print(f"\n🧹 Cleaned up test process: {process_id}")
        except Exception as cleanup_error:
            print(f"⚠️ Cleanup error: {cleanup_error}")

async def main():
    success = await test_thinking_completion()
    if success:
        print("\n🎉 THINKING COMPLETION FIX TEST PASSED!")
        print("The fix should now complete thinking processes when tasks finish.")
    else:
        print("\n💥 THINKING COMPLETION FIX TEST FAILED!")
        print("The fix needs additional debugging.")
    
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)