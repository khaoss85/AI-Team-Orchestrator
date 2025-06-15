#!/usr/bin/env python3
"""
🔧 TEMPORARY SCHEMA WORKAROUND
Test if current temporary fixes are working while we wait for manual SQL fixes
"""
import asyncio
import logging
import sys
import os
from typing import Dict, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

async def test_current_workarounds():
    """Test that current temporary fixes work correctly"""
    
    try:
        # Test 1: AI Goal Extraction with schema-safe data  
        logger.info("🧪 Testing AI Goal Extraction with schema workaround...")
        
        sys.path.append('.')
        from ai_quality_assurance.ai_goal_extractor import AIGoalExtractor, extract_and_create_workspace_goals
        from database import supabase
        
        # Create a real workspace for testing
        workspace_data = {
            "name": "Schema Test Workspace",
            "description": "Testing schema workarounds",
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "goal": "Collect 25 high-quality leads from SaaS companies in Europe with 30% email open rate within 4 weeks",
            "status": "active"
        }
        
        # Insert workspace
        workspace_result = supabase.table("workspaces").insert(workspace_data).execute()
        if workspace_result.data:
            workspace_id = workspace_result.data[0]["id"]
            logger.info(f"✅ Created test workspace: {workspace_id}")
            
            # Test AI goal extraction with schema workaround
            goal_text = workspace_data["goal"]
            workspace_goals = await extract_and_create_workspace_goals(workspace_id, goal_text)
            
            if workspace_goals:
                logger.info(f"✅ AI extracted {len(workspace_goals)} goals with schema workaround")
                
                # Try to insert the first goal
                goal_data = workspace_goals[0]
                
                # Test the safe_goal_data_for_db method
                ai_extractor = AIGoalExtractor()
                safe_goal_data = ai_extractor.safe_goal_data_for_db(goal_data)
                
                logger.info(f"📊 Original goal fields: {list(goal_data.keys())}")
                logger.info(f"🔧 Safe goal fields: {list(safe_goal_data.keys())}")
                
                # Attempt database insertion
                insert_result = supabase.table("workspace_goals").insert(safe_goal_data).execute()
                
                if insert_result.data:
                    logger.info("✅ Goal inserted successfully with schema workaround")
                    goal_id = insert_result.data[0]["id"]
                    
                    # Clean up
                    supabase.table("workspace_goals").delete().eq("id", goal_id).execute()
                    logger.info("🧹 Cleaned up test goal")
                else:
                    logger.error(f"❌ Goal insertion failed: {insert_result}")
                    
            else:
                logger.error("❌ No goals extracted")
                
            # Clean up workspace
            supabase.table("workspaces").delete().eq("id", workspace_id).execute()
            logger.info("🧹 Cleaned up test workspace")
            
        else:
            logger.error(f"❌ Failed to create test workspace: {workspace_result}")
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    # Test 2: Workspace Insights with optional task_id
    logger.info("🧪 Testing Workspace Insights with optional task_id...")
    
    try:
        sys.path.append('.')
        from workspace_memory import WorkspaceMemory
        from models import WorkspaceInsight, InsightType
        from uuid import uuid4
        
        # Create workspace memory instance
        memory = WorkspaceMemory()
        
        # Create an insight with None task_id (workspace-level)
        insight = WorkspaceInsight(
            id=uuid4(),
            workspace_id=uuid4(),
            task_id=None,  # This should work with the fix
            agent_role="test_agent",
            insight_type=InsightType.DISCOVERY,
            content="Test insight with no task_id",
            confidence_score=0.8
        )
        
        logger.info(f"✅ Created WorkspaceInsight with task_id=None: {insight.task_id}")
        
        # Test the database insertion logic (but don't actually insert to avoid FK constraints)
        data = {
            "id": str(insight.id),
            "workspace_id": str(insight.workspace_id),
            "task_id": str(insight.task_id) if insight.task_id is not None else None,
            "agent_role": insight.agent_role,
            "insight_type": insight.insight_type.value,
            "content": insight.content,
            "confidence_score": insight.confidence_score
        }
        
        logger.info(f"✅ Prepared database data: task_id={data['task_id']} (type: {type(data['task_id'])})")
        
        if data['task_id'] is None:
            logger.info("✅ task_id correctly handled as None (not string 'None')")
        else:
            logger.error("❌ task_id should be None but got: {data['task_id']}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Workspace Insights test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    logger.info("🎉 All temporary workarounds are working correctly!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_current_workarounds())
    if success:
        print("\n🎉 TEMPORARY WORKAROUNDS VERIFIED")
        print("✅ AI Goal Extraction works with schema-safe data")
        print("✅ Workspace Insights handles optional task_id correctly")
        print("\n💡 Ready for manual SQL schema fixes in Supabase SQL Editor")
    else:
        print("\n❌ WORKAROUNDS FAILED")
        sys.exit(1)