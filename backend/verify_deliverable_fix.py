#!/usr/bin/env python3
"""
Script to verify the duplicate deliverables fix
"""

import asyncio
import sys
import os
from pathlib import Path
import logging

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from database import get_supabase_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WORKSPACE_ID = "db18803c-3718-4612-a34b-79b1167ac62f"

async def verify_cleanup_results():
    """Verify the results of the duplicate cleanup"""
    supabase = get_supabase_client()
    
    logger.info("🔍 VERIFICATION REPORT: Duplicate Deliverables Fix")
    logger.info("=" * 60)
    
    # Get all deliverables in the target workspace
    result = supabase.table('deliverables').select(
        'id, workspace_id, goal_id, title, content, created_at'
    ).eq('workspace_id', WORKSPACE_ID).execute()
    
    if not result.data:
        logger.warning("❌ No deliverables found in the workspace")
        return
    
    logger.info(f"📊 Total deliverables in workspace: {len(result.data)}")
    logger.info("")
    
    # Analyze by title
    title_counts = {}
    detailed_info = {}
    
    for deliverable in result.data:
        title = deliverable['title']
        
        if title not in title_counts:
            title_counts[title] = 0
            detailed_info[title] = []
        
        title_counts[title] += 1
        
        # Get content info
        content = deliverable.get('content', '') or ''
        if isinstance(content, dict):
            content = str(content)
        elif content is None:
            content = ''
        else:
            content = str(content)
        
        detailed_info[title].append({
            'id': deliverable['id'],
            'content_length': len(content),
            'created_at': deliverable['created_at']
        })
    
    # Report results
    logger.info("📋 DELIVERABLES BY TITLE:")
    logger.info("-" * 60)
    
    duplicates_found = False
    
    for title, count in title_counts.items():
        status_icon = "✅" if count == 1 else "⚠️"
        if count > 1:
            duplicates_found = True
        
        logger.info(f"{status_icon} {title[:80]}...")
        logger.info(f"   Count: {count}")
        
        # Show details for each
        for i, info in enumerate(detailed_info[title]):
            logger.info(f"   [{i+1}] ID: {info['id']}, Content: {info['content_length']} chars, Created: {info['created_at']}")
        logger.info("")
    
    # Summary
    logger.info("📊 SUMMARY:")
    logger.info("-" * 30)
    logger.info(f"Total unique titles: {len(title_counts)}")
    logger.info(f"Total deliverables: {len(result.data)}")
    logger.info(f"Duplicates detected: {'Yes' if duplicates_found else 'No'}")
    
    if not duplicates_found:
        logger.info("✅ SUCCESS: No duplicates found!")
    else:
        logger.warning("⚠️ WARNING: Duplicates still exist!")
    
    # Check specifically for "Istruzioni setup" deliverables
    setup_deliverables = [d for d in result.data if "istruzioni setup" in d['title'].lower()]
    logger.info(f"\n🎯 'Istruzioni setup' deliverables: {len(setup_deliverables)}")
    
    if len(setup_deliverables) == 1:
        logger.info("✅ SUCCESS: Only 1 'Istruzioni setup' deliverable remains")
        setup = setup_deliverables[0]
        content = str(setup.get('content', '') or '')
        logger.info(f"   ID: {setup['id']}")
        logger.info(f"   Content length: {len(content)} characters")
        logger.info(f"   Created: {setup['created_at']}")
    elif len(setup_deliverables) == 0:
        logger.warning("⚠️ WARNING: No 'Istruzioni setup' deliverables found!")
    else:
        logger.warning(f"⚠️ WARNING: {len(setup_deliverables)} 'Istruzioni setup' deliverables still exist!")
    
    return not duplicates_found

async def check_constraint_status():
    """Check if the constraint is working by testing duplicate creation"""
    supabase = get_supabase_client()
    
    logger.info("\n🔒 CONSTRAINT STATUS CHECK:")
    logger.info("-" * 40)
    
    try:
        # Get an existing deliverable to test with
        result = supabase.table('deliverables').select('workspace_id, goal_id, title').limit(1).execute()
        
        if not result.data:
            logger.warning("No existing deliverables to test constraint with")
            return False
        
        existing = result.data[0]
        logger.info("Testing constraint by attempting duplicate creation...")
        
        # Try to create a duplicate
        duplicate_data = {
            'workspace_id': existing['workspace_id'],
            'goal_id': existing['goal_id'],
            'title': existing['title'],
            'content': 'Test duplicate for constraint verification',
            'type': 'document',
            'status': 'draft'
        }
        
        try:
            duplicate_result = supabase.table('deliverables').insert(duplicate_data).execute()
            
            # If we get here, constraint is not working
            logger.warning("⚠️ CONSTRAINT NOT ACTIVE: Duplicate was created successfully")
            
            # Clean up the duplicate
            if duplicate_result.data:
                supabase.table('deliverables').delete().eq('id', duplicate_result.data[0]['id']).execute()
                logger.info("   (Test duplicate cleaned up)")
            
            return False
            
        except Exception as constraint_error:
            error_msg = str(constraint_error).lower()
            if any(keyword in error_msg for keyword in ['unique', 'duplicate', 'constraint', 'violates']):
                logger.info("✅ CONSTRAINT ACTIVE: Duplicate creation failed as expected")
                return True
            else:
                logger.error(f"Unexpected error: {constraint_error}")
                return False
                
    except Exception as e:
        logger.error(f"Error checking constraint status: {e}")
        return False

async def provide_manual_constraint_instructions():
    """Provide instructions for manual constraint addition"""
    logger.info("\n🔧 MANUAL CONSTRAINT ADDITION REQUIRED:")
    logger.info("=" * 50)
    logger.info("To prevent future duplicates, execute this SQL in your Supabase dashboard:")
    logger.info("")
    logger.info("1. Go to https://supabase.com/dashboard/")
    logger.info("2. Select your project")
    logger.info("3. Go to SQL Editor")
    logger.info("4. Execute this SQL:")
    logger.info("")
    logger.info("-" * 50)
    
    sql = """-- Add unique constraint to prevent duplicate deliverables
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.table_constraints 
        WHERE table_name = 'deliverables' 
        AND constraint_name = 'unique_workspace_goal_title'
    ) THEN
        ALTER TABLE deliverables 
        ADD CONSTRAINT unique_workspace_goal_title 
        UNIQUE (workspace_id, goal_id, title);
        RAISE NOTICE 'Added unique constraint: unique_workspace_goal_title';
    ELSE
        RAISE NOTICE 'Unique constraint already exists';
    END IF;
END
$$;"""
    
    logger.info(sql)
    logger.info("-" * 50)
    logger.info("")
    logger.info("5. You should see a success message")
    logger.info("6. Run this verification script again to confirm it's working")

async def main():
    """Main verification function"""
    logger.info("🏁 FINAL VERIFICATION: Duplicate Deliverables Fix")
    logger.info("=" * 60)
    
    try:
        # Verify cleanup results
        cleanup_successful = await verify_cleanup_results()
        
        # Check constraint status
        constraint_active = await check_constraint_status()
        
        # Overall assessment
        logger.info("\n🏆 FINAL ASSESSMENT:")
        logger.info("=" * 30)
        logger.info(f"Cleanup successful: {'✅ Yes' if cleanup_successful else '❌ No'}")
        logger.info(f"Constraint active: {'✅ Yes' if constraint_active else '❌ No'}")
        
        if cleanup_successful and constraint_active:
            logger.info("\n🎉 COMPLETE SUCCESS!")
            logger.info("✅ Duplicates removed")
            logger.info("✅ Constraint active")
            logger.info("✅ Future duplicates prevented")
        elif cleanup_successful and not constraint_active:
            logger.info("\n⚠️ PARTIAL SUCCESS!")
            logger.info("✅ Duplicates removed")
            logger.info("❌ Constraint not active")
            await provide_manual_constraint_instructions()
        else:
            logger.info("\n❌ ISSUES DETECTED!")
            logger.info("Issues found - review logs above")
        
    except Exception as e:
        logger.error(f"Error in verification process: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())