#!/usr/bin/env python3
"""
Test diretto delle condizioni del trigger autonomo
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from database import should_trigger_deliverable_aggregation, trigger_deliverable_aggregation
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_trigger_conditions():
    workspace_id = "b80574de-905f-4ac3-ba54-93b386d427b0"  # From latest test
    
    logger.info(f"🔍 Testing trigger conditions for workspace: {workspace_id}")
    
    try:
        # Test the trigger condition
        should_trigger = await should_trigger_deliverable_aggregation(workspace_id)
        logger.info(f"📊 Trigger evaluation result: {should_trigger}")
        
        if should_trigger:
            logger.info("🎉 CONDITIONS MET - Trigger should activate!")
            
            # Test the actual trigger function
            logger.info("🚀 Testing trigger function...")
            await trigger_deliverable_aggregation(workspace_id)
            logger.info("✅ Trigger function completed")
            
        else:
            logger.info("❌ Conditions not met - analyzing why...")
            
            # Debug: Get task information
            from database import list_tasks
            
            # Check completed tasks
            completed_tasks = await list_tasks(workspace_id, status="completed", limit=10)
            logger.info(f"📋 Found {len(completed_tasks)} completed tasks")
            
            for i, task in enumerate(completed_tasks):
                result = task.get('result', {})
                if isinstance(result, dict):
                    result_content = result.get('result', '')
                else:
                    result_content = str(result)
                
                content_length = len(result_content) if result_content else 0
                logger.info(f"  Task {i+1}: {task.get('name', 'Unknown')} - {content_length} chars")
                
                # Check for placeholders
                if result_content:
                    has_placeholder = any(phrase in result_content.lower() for phrase in [
                        'lorem ipsum', 'placeholder', 'todo', 'tbd', 'coming soon', 
                        'under construction', 'not implemented', 'draft'
                    ])
                    logger.info(f"    Has placeholder content: {has_placeholder}")
                    logger.info(f"    Sample: {result_content[:100]}...")
            
            # Check cooldown
            from datetime import datetime, timedelta
            from database import supabase
            
            # Check if there's a recent deliverable
            recent_threshold = datetime.now() - timedelta(minutes=30)  # 30-minute cooldown
            recent_deliverables = supabase.table("deliverables").select("*").eq(
                "workspace_id", workspace_id
            ).gte("created_at", recent_threshold.isoformat()).execute()
            
            if recent_deliverables.data:
                logger.info(f"⏰ Recent deliverable found - cooldown active")
                for d in recent_deliverables.data:
                    logger.info(f"  📦 {d.get('title', 'Unknown')} created at {d.get('created_at')}")
            else:
                logger.info("⏰ No recent deliverables - cooldown not active")
                
    except Exception as e:
        logger.error(f"❌ Error testing trigger conditions: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_trigger_conditions())