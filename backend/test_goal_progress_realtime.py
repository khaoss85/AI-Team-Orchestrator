#!/usr/bin/env python3
"""
Test Real-Time Goal Progress Updates
This script tests the real-time WebSocket broadcasting for goal progress updates.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_asset_extensions import AssetDrivenDatabaseManager
from uuid import UUID

async def test_goal_progress_update():
    """Test real-time goal progress update broadcasting"""
    
    # Initialize database extensions
    db_ext = AssetDrivenDatabaseManager()
    
    # Test workspace ID (replace with actual workspace ID)
    test_workspace_id = "80feb07a-bd04-42f0-ac52-c4973ba388d3"
    
    print(f"🔍 Testing goal progress update for workspace: {test_workspace_id}")
    
    try:
        # Get workspace goals
        goals = await db_ext.get_workspace_goals(test_workspace_id)
        
        if not goals:
            print("❌ No goals found in workspace")
            return
            
        print(f"📋 Found {len(goals)} goals in workspace")
        
        # Test progress update for first goal
        test_goal = goals[0]
        goal_id = UUID(str(test_goal.id))
        current_progress = getattr(test_goal, 'progress_percentage', 0) or 0
        
        print(f"🎯 Testing progress update for goal: {getattr(test_goal, 'description', 'Unknown')}")
        print(f"📊 Current progress: {current_progress}%")
        
        # Update progress with a test value
        new_progress = min(100, current_progress + 10)  # Add 10% or cap at 100%
        test_quality_score = 0.85
        
        print(f"🚀 Updating goal progress to {new_progress}% with quality score {test_quality_score}")
        
        # Call the update function (this should trigger WebSocket broadcast)
        success = await db_ext.update_goal_progress(
            goal_id=goal_id,
            progress_percentage=new_progress,
            quality_score=test_quality_score
        )
        
        if success:
            print("✅ Goal progress update successful!")
            print("📡 WebSocket broadcast should have been triggered")
            print("🎯 Check frontend for real-time goal pin updates")
        else:
            print("❌ Goal progress update failed")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Starting real-time goal progress update test...")
    asyncio.run(test_goal_progress_update())
    print("🏁 Test completed!")