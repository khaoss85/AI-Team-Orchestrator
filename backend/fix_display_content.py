#!/usr/bin/env python3
"""
Fix display content formatting issue by clearing poorly cached display_content 
and forcing proper AI regeneration.

The issue: Display content was generated using fallback method that just wraps
raw content in basic HTML, instead of proper AI transformation.
"""

import asyncio
import os
import sys
from database import supabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_display_content():
    """Clear poorly formatted display_content to force proper AI regeneration"""
    
    # Get all deliverables with display_content that starts with fallback pattern
    logger.info("Fetching deliverables with poor display content...")
    
    try:
        # Query deliverables with the fallback pattern
        result = supabase.table('deliverables') \
            .select('id, title, display_content') \
            .not_.is_('display_content', 'null') \
            .execute()
        
        deliverables = result.data
        logger.info(f"Found {len(deliverables)} deliverables with display_content")
        
        # Identify poorly formatted ones (fallback pattern)
        poor_format_ids = []
        for d in deliverables:
            display_content = d.get('display_content', '')
            # Check for fallback pattern: starts with <div class="content"><h3>Raw Content</h3>
            if display_content.startswith('<div class="content">\n<h3>Raw Content</h3>') or \
               display_content.startswith('<div class="content"><h3>'):
                poor_format_ids.append(d['id'])
                logger.info(f"Found poorly formatted: {d['title'][:50]}...")
        
        if not poor_format_ids:
            logger.info("No poorly formatted display_content found!")
            return
        
        logger.info(f"\nFound {len(poor_format_ids)} deliverables with poor formatting")
        logger.info("Clearing display_content to force AI regeneration...")
        
        # Clear display_content for these deliverables
        for deliverable_id in poor_format_ids:
            result = supabase.table('deliverables') \
                .update({
                    'display_content': None,
                    'display_format': None,
                    'display_quality_score': None,
                    'transformation_timestamp': None,
                    'content_transformation_status': None,
                    'transformation_method': None,
                    'ai_confidence': None
                }) \
                .eq('id', deliverable_id) \
                .execute()
            
            if result.data:
                logger.info(f"✅ Cleared display_content for {deliverable_id}")
            else:
                logger.error(f"❌ Failed to clear display_content for {deliverable_id}")
        
        logger.info(f"\n🎉 Successfully cleared {len(poor_format_ids)} poorly formatted display_content entries")
        logger.info("Next API request will trigger proper AI transformation with beautiful formatting!")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(fix_display_content())