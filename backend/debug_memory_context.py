#!/usr/bin/env python3
"""
Debug memory context storage - Verifica cosa viene salvato nel database
"""

import asyncio
import logging
from database import get_supabase_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_memory_context(workspace_id=None):
    """Check what's in the memory_context table"""
    
    supabase = get_supabase_client()
    
    if workspace_id:
        logger.info(f"Checking for specific workspace: {workspace_id}")
    
    # Check if table exists and has data
    try:
        result = supabase.table("memory_context").select("*").limit(10).execute()
        logger.info(f"Found {len(result.data)} items in memory_context table")
        
        for item in result.data:
            logger.info(f"Context: {item.get('context_type')} - {item.get('workspace_id')[:8]}... - {item.get('created_at')}")
            
    except Exception as e:
        logger.error(f"Error querying memory_context: {e}")
        
    # Check the CORRECT table name
    try:
        if workspace_id:
            result = supabase.table("memory_context_entries").select("*").eq("workspace_id", workspace_id).order("created_at", desc=True).execute()
            logger.info(f"\nFound {len(result.data)} items in memory_context_entries for workspace {workspace_id}")
        else:
            result = supabase.table("memory_context_entries").select("*").order("created_at", desc=True).limit(10).execute()
            logger.info(f"\nFound {len(result.data)} items in memory_context_entries table (CORRECT TABLE)")
        
        for item in result.data:
            logger.info(f"Context Entry: {item.get('context_type')} - {item.get('workspace_id')[:8]}... - {item.get('created_at')}")
            logger.info(f"  Content: {str(item.get('content'))[:100]}...")
            
    except Exception as e:
        logger.error(f"Error querying memory_context_entries: {e}")
        
    # Check memory_patterns table
    try:
        result = supabase.table("memory_patterns").select("*").limit(10).execute()
        logger.info(f"\nFound {len(result.data)} items in memory_patterns table")
        
        for item in result.data:
            logger.info(f"Pattern: {item.get('pattern_type')} - {item.get('workspace_id')[:8]}...")
            
    except Exception as e:
        logger.error(f"Error querying memory_patterns: {e}")

if __name__ == "__main__":
    import sys
    workspace_id = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(debug_memory_context(workspace_id))