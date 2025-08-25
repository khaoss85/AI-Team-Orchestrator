#!/usr/bin/env python3
"""Check deliverable content for a specific workspace"""
import os
import asyncio
import json
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def check_deliverable_content():
    load_dotenv()
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("Missing Supabase credentials")
        return
        
    supabase: Client = create_client(supabase_url, supabase_key)
    workspace_id = "a162f894-7114-4e63-8127-17bb144db222"
    
    logger.info(f"Checking deliverables for workspace: {workspace_id}")
    
    try:
        # Get all deliverables for this workspace
        response = supabase.table('deliverables').select('*').eq('workspace_id', workspace_id).execute()
        
        if response.data:
            logger.info(f"Found {len(response.data)} deliverables")
            
            for idx, deliverable in enumerate(response.data):
                logger.info(f"\n--- Deliverable {idx + 1} ---")
                logger.info(f"ID: {deliverable.get('id')}")
                logger.info(f"Title: {deliverable.get('title', 'No title')}")
                logger.info(f"Type: {deliverable.get('type', 'Unknown')}")
                logger.info(f"Created: {deliverable.get('created_at')}")
                
                content = deliverable.get('content')
                if content:
                    if isinstance(content, str):
                        logger.info(f"Content type: String, Length: {len(content)}")
                        logger.info(f"Content preview: {content[:200]}...")
                    elif isinstance(content, dict):
                        logger.info(f"Content type: Dictionary")
                        logger.info(f"Content keys: {list(content.keys())}")
                        if 'content' in content:
                            inner_content = content['content']
                            logger.info(f"Inner content type: {type(inner_content)}")
                            if isinstance(inner_content, str):
                                logger.info(f"Inner content preview: {inner_content[:200]}...")
                    else:
                        logger.info(f"Content type: {type(content)}")
                else:
                    logger.warning("No content found!")
                    
        else:
            logger.warning("No deliverables found for this workspace")
            
        # Also check asset_artifacts table
        logger.info("\n\nChecking asset_artifacts table...")
        response2 = supabase.table('asset_artifacts').select('*').eq('workspace_id', workspace_id).execute()
        
        if response2.data:
            logger.info(f"Found {len(response2.data)} asset artifacts")
            for artifact in response2.data[:3]:  # Show first 3
                logger.info(f"Asset ID: {artifact.get('id')}, Type: {artifact.get('asset_type')}")
                content = artifact.get('content')
                if content:
                    if isinstance(content, str):
                        logger.info(f"Content preview: {content[:100]}...")
                    elif isinstance(content, dict):
                        logger.info(f"Content keys: {list(content.keys())}")
                        
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        
if __name__ == "__main__":
    asyncio.run(check_deliverable_content())