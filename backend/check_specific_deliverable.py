#!/usr/bin/env python3
"""Check specific deliverable content"""
import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_specific_deliverable():
    load_dotenv()
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Check the most recent deliverable
    deliverable_id = "cbd3d86b-5b1e-4cc4-9d90-d94e9d02e42f"
    
    logger.info(f"Checking deliverable: {deliverable_id}")
    
    try:
        response = supabase.table('deliverables').select('*').eq('id', deliverable_id).execute()
        
        if response.data:
            deliverable = response.data[0]
            logger.info(f"Title: {deliverable.get('title')}")
            content = deliverable.get('content')
            
            if content:
                logger.info(f"Content type: {type(content)}")
                logger.info(f"Content keys: {list(content.keys()) if isinstance(content, dict) else 'Not a dict'}")
                
                if isinstance(content, dict) and 'prospect_list_csv' in content:
                    csv_content = content['prospect_list_csv']
                    logger.info(f"CSV Content type: {type(csv_content)}")
                    if isinstance(csv_content, str):
                        logger.info(f"CSV Content length: {len(csv_content)}")
                        logger.info(f"CSV Content preview:\n{csv_content[:500]}")
                    else:
                        logger.info(f"CSV Content: {csv_content}")
                        
                # Print full content structure
                logger.info(f"Full content structure: {json.dumps(content, indent=2, default=str)}")
            else:
                logger.warning("No content found!")
                
    except Exception as e:
        logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    check_specific_deliverable()