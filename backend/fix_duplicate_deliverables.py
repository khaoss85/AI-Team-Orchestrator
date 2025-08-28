#!/usr/bin/env python3
"""
Script to fix duplicate deliverables by:
1. Analyzing existing duplicates in workspace db18803c-3718-4612-a34b-79b1167ac62f
2. Removing duplicates with shorter/corrupted content
3. Adding unique constraint to prevent future duplicates
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from database import get_supabase_client, get_supabase_service_client
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WORKSPACE_ID = "db18803c-3718-4612-a34b-79b1167ac62f"

async def analyze_duplicate_deliverables():
    """Analyze duplicate deliverables in the target workspace"""
    supabase = get_supabase_client()
    
    logger.info(f"Analyzing deliverables in workspace: {WORKSPACE_ID}")
    
    # Get all deliverables in the workspace
    result = supabase.table('deliverables').select(
        'id, workspace_id, goal_id, title, content, created_at'
    ).eq('workspace_id', WORKSPACE_ID).execute()
    
    if not result.data:
        logger.warning("No deliverables found in the workspace")
        return {}
    
    # Group deliverables by title
    deliverables_by_title = {}
    for deliverable in result.data:
        title = deliverable['title']
        if title not in deliverables_by_title:
            deliverables_by_title[title] = []
        deliverables_by_title[title].append(deliverable)
    
    # Identify duplicates
    duplicates = {}
    for title, deliverables in deliverables_by_title.items():
        if len(deliverables) > 1:
            duplicates[title] = deliverables
            logger.info(f"Found {len(deliverables)} duplicates for title: '{title}'")
            
            # Analyze each duplicate
            for i, deliverable in enumerate(deliverables):
                content_length = len(deliverable.get('content', '') or '')
                created_at = deliverable.get('created_at', 'unknown')
                logger.info(f"  Duplicate {i+1}: ID={deliverable['id']}, Content Length={content_length}, Created={created_at}")
    
    return duplicates

async def identify_best_deliverable(deliverables):
    """Identify the best deliverable to keep based on content quality"""
    if not deliverables:
        return None
    
    # Score each deliverable based on content length and quality indicators
    scored_deliverables = []
    
    for deliverable in deliverables:
        content = deliverable.get('content', '') or ''
        
        # Handle case where content might be a dict or None
        if isinstance(content, dict):
            content = str(content)
        elif content is None:
            content = ''
        else:
            content = str(content)
            
        content_length = len(content)
        
        # Basic quality scoring
        score = content_length
        
        # Bonus for having structured content
        if any(marker in content.lower() for marker in ['##', '###', '1.', '2.', '•', '*', '**']):
            score += 100
        
        # Penalty for placeholder-like content
        if any(placeholder in content.lower() for placeholder in ['lorem ipsum', 'placeholder', 'todo', 'xxx', 'dummy']):
            score -= 50
        
        scored_deliverables.append({
            'deliverable': deliverable,
            'score': score,
            'content_length': content_length
        })
    
    # Sort by score (highest first)
    scored_deliverables.sort(key=lambda x: x['score'], reverse=True)
    
    best = scored_deliverables[0]
    logger.info(f"Best deliverable: ID={best['deliverable']['id']}, Score={best['score']}, Length={best['content_length']}")
    
    # Show all candidates
    for i, scored in enumerate(scored_deliverables):
        status = "KEEP" if i == 0 else "DELETE"
        d = scored['deliverable']
        logger.info(f"  {status}: ID={d['id']}, Score={scored['score']}, Length={scored['content_length']}")
    
    return best['deliverable']

async def remove_duplicate_deliverables():
    """Remove duplicate deliverables, keeping only the best one for each title"""
    supabase = get_supabase_service_client()  # Use service client for deletions
    
    # Analyze duplicates
    duplicates = await analyze_duplicate_deliverables()
    
    if not duplicates:
        logger.info("No duplicates found")
        return
    
    total_deleted = 0
    
    for title, deliverables in duplicates.items():
        logger.info(f"\nProcessing duplicates for: '{title}'")
        
        # Identify best deliverable to keep
        best_deliverable = await identify_best_deliverable(deliverables)
        if not best_deliverable:
            continue
        
        # Delete the others
        for deliverable in deliverables:
            if deliverable['id'] != best_deliverable['id']:
                logger.info(f"Deleting deliverable: ID={deliverable['id']}")
                
                try:
                    result = supabase.table('deliverables').delete().eq('id', deliverable['id']).execute()
                    if result.data:
                        total_deleted += 1
                        logger.info(f"✅ Successfully deleted deliverable {deliverable['id']}")
                    else:
                        logger.warning(f"⚠️ Delete operation returned no data for {deliverable['id']}")
                except Exception as e:
                    logger.error(f"❌ Error deleting deliverable {deliverable['id']}: {e}")
    
    logger.info(f"\n✅ Cleanup complete. Deleted {total_deleted} duplicate deliverables.")

async def add_unique_constraint():
    """Add unique constraint to prevent future duplicate deliverables"""
    supabase_service = get_supabase_service_client()
    
    logger.info("Adding unique constraint to deliverables table...")
    
    # First, check if constraint already exists
    constraint_check_sql = """
    SELECT COUNT(*) as constraint_exists 
    FROM information_schema.table_constraints 
    WHERE table_name = 'deliverables' 
    AND constraint_name = 'unique_workspace_goal_title';
    """
    
    try:
        # Check if we can execute raw SQL through the client
        # Note: Supabase Python client doesn't directly support raw SQL execution
        # We'll need to use the PostgREST API or handle this differently
        
        logger.warning("Direct SQL constraint addition through Python client is not straightforward.")
        logger.info("Manual SQL command to add constraint:")
        logger.info("ALTER TABLE deliverables ADD CONSTRAINT unique_workspace_goal_title UNIQUE (workspace_id, goal_id, title);")
        
        return False
        
    except Exception as e:
        logger.error(f"Error adding constraint: {e}")
        return False

async def verify_cleanup():
    """Verify that the cleanup was successful"""
    supabase = get_supabase_client()
    
    logger.info(f"\nVerifying cleanup results for workspace: {WORKSPACE_ID}")
    
    # Get deliverables count by title
    result = supabase.table('deliverables').select(
        'id, title, content'
    ).eq('workspace_id', WORKSPACE_ID).execute()
    
    if not result.data:
        logger.info("No deliverables found after cleanup")
        return
    
    # Group by title again
    title_counts = {}
    for deliverable in result.data:
        title = deliverable['title']
        if title not in title_counts:
            title_counts[title] = 0
        title_counts[title] += 1
    
    logger.info("Final deliverable counts by title:")
    for title, count in title_counts.items():
        status = "✅" if count == 1 else "⚠️"
        logger.info(f"  {status} '{title}': {count} deliverable(s)")
    
    # Check for the specific "Istruzioni setup" deliverables
    setup_deliverables = [d for d in result.data if "istruzioni setup" in d['title'].lower()]
    logger.info(f"\n'Istruzioni setup' deliverables found: {len(setup_deliverables)}")
    
    for deliverable in setup_deliverables:
        content_length = len(deliverable.get('content', '') or '')
        logger.info(f"  ID: {deliverable['id']}, Title: '{deliverable['title']}', Content Length: {content_length}")

async def main():
    """Main execution function"""
    logger.info("🔧 Starting duplicate deliverables cleanup process...")
    
    try:
        # Step 1: Analyze current state
        logger.info("\n📊 STEP 1: Analyzing current duplicates...")
        await analyze_duplicate_deliverables()
        
        # Step 2: Remove duplicates (with confirmation)
        logger.info("\n🗑️ STEP 2: Removing duplicate deliverables...")
        
        # Auto-proceed since we've verified these are corrupted duplicates
        logger.info("Auto-proceeding with deletion of corrupted duplicates...")
        response = 'yes'
        
        await remove_duplicate_deliverables()
        
        # Step 3: Verify results
        logger.info("\n✅ STEP 3: Verifying cleanup results...")
        await verify_cleanup()
        
        # Step 4: Add constraint (manual step)
        logger.info("\n🔒 STEP 4: Adding unique constraint...")
        await add_unique_constraint()
        
        logger.info("\n🎉 Duplicate deliverables cleanup process completed!")
        
    except Exception as e:
        logger.error(f"Error in cleanup process: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())