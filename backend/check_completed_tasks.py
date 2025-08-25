#!/usr/bin/env python3
"""Check completed tasks for actual content"""
import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_completed_tasks():
    load_dotenv()
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    supabase: Client = create_client(supabase_url, supabase_key)
    workspace_id = "a162f894-7114-4e63-8127-17bb144db222"
    
    logger.info(f"Checking completed tasks for workspace: {workspace_id}")
    
    try:
        # Get completed tasks
        response = supabase.table('tasks').select('*').eq('workspace_id', workspace_id).eq('status', 'completed').execute()
        
        if response.data:
            logger.info(f"Found {len(response.data)} completed tasks")
            
            for idx, task in enumerate(response.data):
                logger.info(f"\n--- Task {idx + 1} ---")
                logger.info(f"ID: {task.get('id')}")
                logger.info(f"Title: {task.get('title', 'No title')}")
                logger.info(f"Description: {task.get('description', 'No description')}")
                logger.info(f"Created: {task.get('created_at')}")
                logger.info(f"Completed: {task.get('completed_at')}")
                
                result = task.get('result')
                if result:
                    if isinstance(result, str):
                        logger.info(f"Result type: String, Length: {len(result)}")
                        if "CSV" in result.upper() or "," in result:
                            logger.info(f"Potential CSV content preview:\n{result[:500]}")
                        else:
                            logger.info(f"Result preview: {result[:200]}...")
                    elif isinstance(result, dict):
                        logger.info(f"Result type: Dictionary")
                        logger.info(f"Result keys: {list(result.keys())}")
                        # Check for common CSV content keys
                        for key in ['csv', 'contacts', 'list', 'data', 'content']:
                            if key in result:
                                logger.info(f"Found '{key}' in result:")
                                content = result[key]
                                if isinstance(content, str):
                                    logger.info(f"Content preview:\n{content[:500]}")
                    else:
                        logger.info(f"Result type: {type(result)}")
                else:
                    logger.warning("No result found!")
                    
        else:
            logger.warning("No completed tasks found")
            
        # Also check for task with specific ID from deliverable
        task_id = "eea2dcf6-ca2e-4d38-91d5-82346f0a3ce3"
        logger.info(f"\n\nChecking specific task: {task_id}")
        response2 = supabase.table('tasks').select('*').eq('id', task_id).execute()
        
        if response2.data:
            task = response2.data[0]
            logger.info(f"Task found: {task.get('title')}")
            result = task.get('result')
            if result:
                logger.info(f"Task result: {json.dumps(result, indent=2, default=str)}")
        else:
            logger.warning(f"Task {task_id} not found")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    check_completed_tasks()