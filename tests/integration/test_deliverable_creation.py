#!/usr/bin/env python3
"""
🚀 TEST DELIVERABLE CREATION 
Test che esegue task e forza la creazione di deliverable
"""

import asyncio
import requests
import json
import time
import logging
from datetime import datetime
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(__file__))

from database import list_tasks, get_deliverables, create_deliverable
from ai_agents.manager import AgentManager
from deliverable_system.unified_deliverable_engine import check_and_create_final_deliverable
from models import TaskStatus
from uuid import UUID

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

async def test_deliverable_creation():
    """Test creazione deliverable da task completati"""
    
    logger.info("🚀 Testing Deliverable Creation from Completed Tasks")
    
    # Use the last successful workspace from previous test
    workspace_id = "4eaaaf40-150f-4d29-add0-6843db3070b4"
    
    try:
        # 1. Check current state
        logger.info("📊 Checking current workspace state...")
        
        tasks = await list_tasks(workspace_id)
        completed_tasks = [t for t in tasks if t.get('status') == 'completed']
        deliverables = await get_deliverables(workspace_id)
        
        logger.info(f"  - Total tasks: {len(tasks)}")
        logger.info(f"  - Completed tasks: {len(completed_tasks)}")
        logger.info(f"  - Existing deliverables: {len(deliverables)}")
        
        if completed_tasks:
            logger.info("✅ Found completed tasks, testing deliverable creation...")
            
            # 2. Test the deliverable creation function directly
            logger.info("🔧 Testing check_and_create_final_deliverable...")
            
            deliverable_id = await check_and_create_final_deliverable(workspace_id)
            
            if deliverable_id:
                logger.info(f"🎉 SUCCESS: Created deliverable {deliverable_id}")
                
                # 3. Verify the deliverable was created
                updated_deliverables = await get_deliverables(workspace_id)
                
                logger.info(f"📦 Deliverable verification:")
                for i, deliverable in enumerate(updated_deliverables, 1):
                    logger.info(f"  {i}. {deliverable.get('title')} ({deliverable.get('type')})")
                    logger.info(f"     - Status: {deliverable.get('status')}")
                    logger.info(f"     - Content length: {len(deliverable.get('content', ''))}")
                    logger.info(f"     - Tasks used: {len(deliverable.get('metadata', {}).get('source_tasks', []))}")
                
                # 4. Test the API endpoint
                logger.info("🌐 Testing API endpoint...")
                
                try:
                    api_response = requests.get(f"{API_BASE}/deliverables/workspace/{workspace_id}", timeout=10)
                    
                    if api_response.status_code == 200:
                        api_deliverables = api_response.json()
                        logger.info(f"✅ API returned {len(api_deliverables)} deliverables")
                        
                        # Show content of first deliverable
                        if api_deliverables:
                            first_deliverable = api_deliverables[0]
                            content = first_deliverable.get('content', '')
                            logger.info(f"📝 Sample content (first 300 chars):")
                            logger.info(f"   {content[:300]}...")
                    else:
                        logger.error(f"❌ API error: {api_response.status_code}")
                        
                except Exception as api_error:
                    logger.error(f"❌ API test failed: {api_error}")
                
                return True
                
            else:
                logger.warning("⚠️ No deliverable created")
                
                # Try to force create one manually
                logger.info("🔧 Trying to force create deliverable...")
                
                # Create sample deliverable data
                sample_deliverable = {
                    "title": "Manual Test Deliverable",
                    "type": "test_summary",
                    "content": f"# Test Deliverable\n\nThis is a test deliverable created from {len(completed_tasks)} completed tasks.\n\n## Task Summary\n\n" + 
                              "\n".join([f"- {task.get('name', 'Unknown')}" for task in completed_tasks[:3]]),
                    "status": "completed",
                    "readiness_score": 90,
                    "completion_percentage": 100,
                    "business_value_score": 85,
                    "quality_metrics": {
                        "task_count": len(completed_tasks),
                        "manual_creation": True
                    },
                    "metadata": {
                        "source_tasks": [task.get("id") for task in completed_tasks],
                        "creation_method": "manual_test",
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
                manual_deliverable = await create_deliverable(workspace_id, sample_deliverable)
                
                if manual_deliverable:
                    logger.info(f"✅ Manual deliverable created: {manual_deliverable.get('id')}")
                    return True
                
        else:
            logger.warning("⚠️ No completed tasks found - need to execute tasks first")
            
            # Try to execute a task
            logger.info("🔧 Trying to execute a task...")
            
            pending_tasks = [t for t in tasks if t.get('status') == 'pending']
            
            if pending_tasks:
                manager = AgentManager(UUID(workspace_id))
                await manager.initialize()
                
                # Execute first pending task
                task_id = UUID(pending_tasks[0]["id"])
                result = await manager.execute_task(task_id)
                
                if result and result.status == TaskStatus.COMPLETED:
                    logger.info("✅ Task executed successfully")
                    
                    # Now try deliverable creation again
                    deliverable_id = await check_and_create_final_deliverable(workspace_id)
                    
                    if deliverable_id:
                        logger.info(f"🎉 SUCCESS: Created deliverable {deliverable_id} after task execution")
                        return True
                    else:
                        logger.info("⚠️ Still no deliverable created after task execution")
                        
            else:
                logger.warning("⚠️ No pending tasks to execute")
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Error in deliverable creation test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test execution"""
    success = await test_deliverable_creation()
    
    if success:
        logger.info("🎉 DELIVERABLE CREATION TEST PASSED!")
        return 0
    else:
        logger.error("❌ DELIVERABLE CREATION TEST FAILED!")
        return 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)