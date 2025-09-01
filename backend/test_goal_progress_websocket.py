#!/usr/bin/env python3
"""
Test WebSocket Goal Progress Broadcasting
This script directly tests the WebSocket broadcasting mechanism.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_websocket_broadcast():
    """Test WebSocket broadcasting for goal progress updates"""
    
    try:
        from routes.websocket_assets import broadcast_goal_progress_update
        
        # Test data
        workspace_id = "80feb07a-bd04-42f0-ac52-c4973ba388d3"
        goal_id = "a460c140-55a0-4da0-8561-eebb6e33545c"  # The main ICP collection goal
        progress = 25.0  # Test progress
        asset_completion_rate = 25.0
        quality_score = 0.85
        
        print(f"🧪 Testing WebSocket broadcast for goal progress update")
        print(f"📊 Workspace: {workspace_id}")
        print(f"🎯 Goal: {goal_id}")
        print(f"📈 Progress: {progress}%")
        
        # Call the broadcast function
        await broadcast_goal_progress_update(
            workspace_id=workspace_id,
            goal_id=goal_id,
            progress=progress,
            asset_completion_rate=asset_completion_rate,
            quality_score=quality_score
        )
        
        print("✅ WebSocket broadcast completed successfully!")
        print("🎯 Check frontend for real-time goal pin updates")
        print("📡 Message should appear in browser WebSocket console")
        
    except Exception as e:
        print(f"❌ WebSocket broadcast test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Starting WebSocket goal progress broadcast test...")
    asyncio.run(test_websocket_broadcast())
    print("🏁 Test completed!")