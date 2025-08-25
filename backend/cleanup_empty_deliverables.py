#!/usr/bin/env python3
"""Clean up empty deliverables and fix goal status"""
import os
import asyncio
import json
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def has_meaningful_content(content) -> bool:
    """Check if deliverable content is meaningful"""
    if not content:
        return False
    
    if isinstance(content, dict):
        # Check for timeout/error indicators
        if any(key in content for key in ['timeout', 'error', 'failed']):
            return False
            
        # Check for meaningful content
        for key, value in content.items():
            if isinstance(value, str) and len(value.strip()) > 20:
                return True
            elif isinstance(value, (list, dict)) and value:
                return True
    
    elif isinstance(content, str) and len(content.strip()) > 20:
        return True
        
    return False

async def cleanup_empty_deliverables():
    load_dotenv()
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    supabase: Client = create_client(supabase_url, supabase_key)
    workspace_id = "a162f894-7114-4e63-8127-17bb144db222"
    
    logger.info(f"Cleaning up empty deliverables for workspace: {workspace_id}")
    
    try:
        # Get all deliverables for this workspace
        response = supabase.table('deliverables').select('*').eq('workspace_id', workspace_id).execute()
        
        empty_deliverables = []
        meaningful_deliverables = []
        
        for deliverable in response.data:
            content = deliverable.get('content')
            
            if has_meaningful_content(content):
                meaningful_deliverables.append(deliverable)
                logger.info(f"✅ Meaningful deliverable: {deliverable.get('title')}")
            else:
                empty_deliverables.append(deliverable)
                logger.warning(f"❌ Empty deliverable: {deliverable.get('title')} - Content: {content}")
        
        logger.info(f"\nSUMMARY:")
        logger.info(f"📦 Total deliverables: {len(response.data)}")
        logger.info(f"✅ Meaningful deliverables: {len(meaningful_deliverables)}")
        logger.info(f"❌ Empty deliverables: {len(empty_deliverables)}")
        
        if empty_deliverables:
            logger.info(f"\n🧹 CLEANUP OPTIONS:")
            logger.info(f"1. Mark empty deliverables as 'needs_review' instead of 'completed'")
            logger.info(f"2. Delete empty deliverables entirely")
            logger.info(f"3. Update goal status to 'active' instead of 'completed' for goals with only empty deliverables")
            
            # For now, just log what we would do
            for deliverable in empty_deliverables:
                goal_id = deliverable.get('goal_id')
                if goal_id:
                    logger.info(f"🔄 Would reset goal {goal_id} status to 'active'")
                    
                    # Update goal status to active if it's currently completed
                    goal_response = supabase.table('workspace_goals').select('*').eq('id', goal_id).execute()
                    if goal_response.data:
                        goal = goal_response.data[0]
                        if goal.get('status') == 'completed':
                            logger.info(f"🔄 Resetting goal status from 'completed' to 'active' for goal: {goal.get('description')}")
                            # Uncomment to actually update:
                            # supabase.table('workspace_goals').update({'status': 'active', 'progress_percentage': 0}).eq('id', goal_id).execute()
                            
                # Mark deliverable as needs review
                logger.info(f"📝 Would mark deliverable as 'needs_review': {deliverable.get('id')}")
                # Uncomment to actually update:
                # supabase.table('deliverables').update({'status': 'needs_review'}).eq('id', deliverable.get('id')).execute()
        else:
            logger.info("✅ No empty deliverables found!")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(cleanup_empty_deliverables())