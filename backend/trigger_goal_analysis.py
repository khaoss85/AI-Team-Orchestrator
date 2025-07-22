#!/usr/bin/env python3
"""
Manually trigger goal analysis for workspace to test autonomous task generation
"""
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_goal_analysis():
    """Test goal analysis trigger"""
    try:
        from automated_goal_monitor import automated_goal_monitor
        
        workspace_id = "956590ae-a112-4352-ba3b-6b607948f586"
        
        logger.info(f"🎯 Triggering immediate goal analysis for workspace {workspace_id}")
        
        result = await automated_goal_monitor._trigger_immediate_goal_analysis(workspace_id)
        
        logger.info(f"✅ Goal analysis result: {result}")
        
        # Check if tasks were created
        import requests
        tasks_response = requests.get(f"http://localhost:8000/api/workspaces/{workspace_id}/tasks")
        if tasks_response.status_code == 200:
            tasks = tasks_response.json()
            logger.info(f"📊 Tasks after analysis: {len(tasks)} tasks")
            for task in tasks[:3]:  # Show first 3 tasks
                logger.info(f"   - {task.get('name', 'Unknown')}: {task.get('status', 'Unknown')}")
        else:
            logger.warning(f"Failed to get tasks: {tasks_response.status_code}")
            
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_goal_analysis())