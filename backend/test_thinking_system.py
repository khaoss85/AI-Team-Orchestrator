#!/usr/bin/env python3
"""
Test script to verify thinking system is working end-to-end
"""

import asyncio
import logging
from uuid import UUID
from services.thinking_process import thinking_engine

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_thinking_system():
    """Test the thinking system end-to-end"""
    workspace_id = UUID("f5c4f1e0-a887-4431-b43e-aea6d62f2d4a")  # Use existing workspace ID
    
    print("🧠 Testing Thinking System...")
    print("=" * 50)
    
    try:
        # Step 1: Start a thinking process
        print("📝 Starting thinking process...")
        process_id = await thinking_engine.start_thinking_process(
            workspace_id=workspace_id,
            context="Testing the real-time thinking system with WebSocket integration",
            process_type="test"
        )
        print(f"✅ Started thinking process: {process_id}")
        
        # Step 2: Add thinking steps
        print("\n💭 Adding thinking steps...")
        
        step1_id = await thinking_engine.add_thinking_step(
            process_id=process_id,
            step_type="analysis",
            content="🔍 Analyzing the current test scenario. I need to verify that thinking steps are properly broadcast via WebSocket to connected clients.",
            confidence=0.9
        )
        print(f"✅ Added analysis step: {step1_id}")
        
        # Wait a moment for WebSocket broadcast
        await asyncio.sleep(1)
        
        step2_id = await thinking_engine.add_thinking_step(
            process_id=process_id,
            step_type="reasoning",
            content="💡 Reasoning through the implementation: The thinking engine should store steps in database AND broadcast them real-time via WebSocket to frontend clients.",
            confidence=0.8
        )
        print(f"✅ Added reasoning step: {step2_id}")
        
        await asyncio.sleep(1)
        
        step3_id = await thinking_engine.add_thinking_step(
            process_id=process_id,
            step_type="evaluation",
            content="⚖️ Evaluating the system: If WebSocket clients receive these steps in real-time, the thinking display should show live updates like Claude's thinking process.",
            confidence=0.9
        )
        print(f"✅ Added evaluation step: {step3_id}")
        
        await asyncio.sleep(1)
        
        # Step 3: Complete the process
        print("\n🏁 Completing thinking process...")
        conclusion = "✨ Test completed successfully! The thinking system is now properly integrated with WebSocket broadcasting for real-time display."
        completed_process = await thinking_engine.complete_thinking_process(
            process_id=process_id,
            conclusion=conclusion,
            overall_confidence=0.9
        )
        print(f"✅ Completed process with {len(completed_process.steps)} steps")
        
        # Step 4: Verify data
        print("\n📊 Verifying stored data...")
        retrieved_process = await thinking_engine.get_thinking_process(process_id)
        if retrieved_process:
            print(f"✅ Process retrieved: {len(retrieved_process.steps)} steps stored")
            print(f"   └─ Conclusion: {retrieved_process.final_conclusion}")
        else:
            print("❌ Could not retrieve process from database")
        
        print("\n🎉 Thinking system test completed!")
        print("   Check the frontend 'Thinking' tab for real-time updates")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_thinking_system())