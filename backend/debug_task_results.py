#!/usr/bin/env python3
"""
Debug task results to see what's being stored
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from database import list_tasks
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_task_results():
    workspace_id = "70609f08-3ad9-4b6e-8e20-9352207ee27c"
    
    logger.info(f"🔍 Debugging task results for workspace: {workspace_id}")
    
    try:
        completed_tasks = await list_tasks(workspace_id, status="completed", limit=10)
        logger.info(f"📋 Found {len(completed_tasks)} completed tasks")
        
        for i, task in enumerate(completed_tasks):
            logger.info(f"\n📝 Task {i+1}: {task.get('name')}")
            logger.info(f"   ID: {task.get('id')}")
            logger.info(f"   Status: {task.get('status')}")
            
            # Detailed result analysis
            result = task.get('result')
            logger.info(f"   Result type: {type(result)}")
            logger.info(f"   Result value: {result}")
            
            if result:
                if isinstance(result, dict):
                    logger.info(f"   Result keys: {list(result.keys())}")
                    if 'result' in result:
                        content = result['result']
                        logger.info(f"   Content type: {type(content)}")
                        logger.info(f"   Content length: {len(str(content))}")
                        logger.info(f"   Content preview: {str(content)[:200]}...")
                else:
                    logger.info(f"   Direct result length: {len(str(result))}")
                    logger.info(f"   Direct result preview: {str(result)[:200]}...")
            else:
                logger.info("   ❌ No result content found")
                
    except Exception as e:
        logger.error(f"❌ Error debugging tasks: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(debug_task_results())