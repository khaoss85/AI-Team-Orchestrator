#!/usr/bin/env python3
"""Debug the aggregation process for the failed task"""
import os
import asyncio
import json
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_aggregation():
    load_dotenv()
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Get the specific task that failed
    task_id = "eea2dcf6-ca2e-4d38-91d5-82346f0a3ce3"
    workspace_id = "a162f894-7114-4e63-8127-17bb144db222"
    
    logger.info(f"Debugging aggregation for task: {task_id}")
    
    try:
        # Get the task
        response = supabase.table('tasks').select('*').eq('id', task_id).execute()
        
        if response.data:
            task = response.data[0]
            logger.info(f"Task title: {task.get('title')}")
            logger.info(f"Task description: {task.get('description')}")
            logger.info(f"Task status: {task.get('status')}")
            logger.info(f"Task result: {json.dumps(task.get('result'), indent=2)}")
            
            # Check what the aggregation logic would do with this task
            result = task.get('result', {})
            
            # Simulate the aggregation logic
            if isinstance(result, dict):
                if 'timeout' in result:
                    logger.warning("⚠️ Task result contains timeout - this explains the empty deliverable!")
                    logger.info("The task failed with timeout but was marked as 'completed' in database")
                    
                if 'content' in result:
                    logger.info(f"Task has content: {result['content'][:200]}...")
                else:
                    logger.warning("Task has NO content field")
                    
                # Check if there are any useful fields
                useful_fields = []
                for key, value in result.items():
                    if isinstance(value, str) and len(value) > 50:
                        useful_fields.append(key)
                        
                if useful_fields:
                    logger.info(f"Task has potentially useful fields: {useful_fields}")
                else:
                    logger.warning("Task has NO useful content to aggregate")
                    
        else:
            logger.error(f"Task {task_id} not found")
            
        # Also check goal information
        logger.info("\nChecking goal information...")
        goals_response = supabase.table('workspace_goals').select('*').eq('workspace_id', workspace_id).execute()
        
        if goals_response.data:
            for goal in goals_response.data:
                logger.info(f"Goal: {goal.get('description')} - Status: {goal.get('status')} - Progress: {goal.get('progress_percentage', 0)}%")
        else:
            logger.warning("No goals found for workspace")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(debug_aggregation())