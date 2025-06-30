#!/usr/bin/env python3
"""
Test that thinking_steps now works with created_at column
"""

import asyncio
from dotenv import load_dotenv
from services.thinking_process import RealTimeThinkingEngine, ThinkingStep
import uuid

# Load environment
load_dotenv('/Users/pelleri/Documents/ai-team-orchestrator/backend/.env')

async def test_thinking_process():
    """Test thinking process creation and retrieval"""
    
    print("🧪 Testing thinking process after schema fix...")
    
    manager = RealTimeThinkingEngine()
    workspace_id = "bc41beb3-4380-434a-8280-92821006840e"
    
    # Create a test thinking process
    process_id = f"test_process_{uuid.uuid4().hex[:8]}"
    process = await manager.create_process(
        process_id=process_id,
        workspace_id=workspace_id,
        context="Testing thinking_steps schema fix"
    )
    
    print(f"✅ Created thinking process: {process.process_id}")
    
    # Add some thinking steps
    steps = [
        ThinkingStep(
            step_id=f"step1_{uuid.uuid4().hex[:8]}",
            step_type="analysis",
            content="Analyzing the schema fix requirements",
            confidence=0.8
        ),
        ThinkingStep(
            step_id=f"step2_{uuid.uuid4().hex[:8]}",
            step_type="reasoning",
            content="The created_at column is now available",
            confidence=0.9
        ),
        ThinkingStep(
            step_id=f"step3_{uuid.uuid4().hex[:8]}",
            step_type="conclusion",
            content="Schema fix successfully applied",
            confidence=0.95
        )
    ]
    
    for step in steps:
        try:
            await manager.add_step(process_id, step)
            print(f"✅ Added step: {step.step_type} - {step.content[:50]}...")
        except Exception as e:
            print(f"❌ Failed to add step: {e}")
            return False
    
    # Retrieve the process to verify
    retrieved = await manager.get_process(process_id)
    if retrieved:
        print(f"\n✅ Retrieved process with {len(retrieved.steps)} steps")
        for i, step in enumerate(retrieved.steps):
            print(f"   Step {i+1}: {step.step_type} (confidence: {step.confidence})")
    else:
        print("❌ Failed to retrieve process")
        return False
    
    # Complete the process
    await manager.complete_process(
        process_id=process_id,
        conclusion="Schema fix test completed successfully",
        confidence=0.95
    )
    
    print(f"\n✅ Process completed successfully!")
    
    # Test recent processes retrieval
    recent = await manager.get_recent_processes(workspace_id, limit=5)
    print(f"\n✅ Found {len(recent)} recent processes in workspace")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_thinking_process())
    if success:
        print("\n🎉 Thinking process system is working correctly!")
        print("The 'Failed to store thinking step' error should be resolved.")
    else:
        print("\n❌ Thinking process system test failed")