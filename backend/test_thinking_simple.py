#!/usr/bin/env python3
"""
Simple test for thinking_steps with created_at column
"""

import asyncio
from dotenv import load_dotenv
from services.thinking_process import RealTimeThinkingEngine
from uuid import UUID

# Load environment
load_dotenv('/Users/pelleri/Documents/ai-team-orchestrator/backend/.env')

async def test_thinking_simple():
    """Simple test of thinking process functionality"""
    
    print("🧪 Testing thinking process after schema fix...")
    
    engine = RealTimeThinkingEngine()
    workspace_id = UUID("bc41beb3-4380-434a-8280-92821006840e")
    
    try:
        # Start a thinking process
        process_id = await engine.start_thinking_process(
            workspace_id=workspace_id,
            context="Testing thinking_steps created_at column fix",
            process_type="analysis"
        )
        print(f"✅ Started thinking process: {process_id}")
        
        # Add some thinking steps
        await engine.add_thinking_step(
            process_id=process_id,
            step_type="analysis",
            content="Verifying that created_at column now exists",
            confidence=0.8
        )
        print("✅ Added analysis step")
        
        await engine.add_thinking_step(
            process_id=process_id,
            step_type="reasoning",
            content="The schema migration has been applied successfully",
            confidence=0.9
        )
        print("✅ Added reasoning step")
        
        # Complete the process
        completed_process = await engine.complete_thinking_process(
            process_id=process_id,
            conclusion="Thinking steps table now has created_at column and works correctly",
            overall_confidence=0.95
        )
        print(f"✅ Completed thinking process with {len(completed_process.steps)} steps")
        
        # Retrieve to verify
        retrieved = await engine.get_thinking_process(process_id)
        if retrieved:
            print(f"\n✅ Successfully retrieved process:")
            print(f"   Process ID: {retrieved.process_id}")
            print(f"   Steps: {len(retrieved.steps)}")
            print(f"   Confidence: {retrieved.overall_confidence}")
            print(f"   Conclusion: {retrieved.final_conclusion}")
            
            for i, step in enumerate(retrieved.steps):
                print(f"   Step {i+1}: {step.step_type} - {step.content[:50]}...")
        else:
            print("❌ Failed to retrieve process")
            return False
        
        print("\n🎉 Thinking process system is working correctly!")
        print("✅ The 'Failed to store thinking step' error has been resolved!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_thinking_simple())