#!/usr/bin/env python3
"""
🚨 HOTFIX SCRIPT: Fix Intermediate Deliverable Titles
Removes tool references from existing deliverables and makes titles business-friendly

Usage: python3 fix_intermediate_deliverable_titles.py [--dry-run] [--workspace-id WORKSPACE_ID]
"""

import os
import sys
import argparse
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
from dotenv import load_dotenv
from supabase import create_client

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.deliverable_title_sanitizer import sanitize_deliverable_title

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    logger.error("❌ Missing SUPABASE_URL or SUPABASE_KEY in environment")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)


def get_deliverables_with_tool_references(workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get all deliverables that have tool references in their titles"""
    
    query = supabase.table('deliverables').select('*')
    
    if workspace_id:
        query = query.eq('workspace_id', workspace_id)
    
    result = query.execute()
    
    if not result.data:
        return []
    
    # Filter deliverables with tool references
    tool_keywords = [
        'File Search Tool',
        'Internal Databases', 
        'Instagram Analytics Tool',
        'Web Search',
        'Database Query',
        ': File Search',
        ': Internal',
        ': Instagram',
        ': Web',
        'Research Data for',
        'Gather',
        'Find',
        '(Instance',
        'Duplicate Fix',
        'Final Mapping Fix'
    ]
    
    affected_deliverables = []
    for deliverable in result.data:
        title = deliverable.get('title', '')
        if any(keyword in title for keyword in tool_keywords):
            affected_deliverables.append(deliverable)
    
    return affected_deliverables


def get_goal_description(goal_id: str) -> Optional[str]:
    """Get goal description for better context in title generation"""
    
    if not goal_id:
        return None
    
    try:
        result = supabase.table('workspace_goals').select('description').eq('id', goal_id).execute()
        if result.data and len(result.data) > 0:
            return result.data[0].get('description')
    except Exception as e:
        logger.warning(f"Could not fetch goal description for {goal_id}: {e}")
    
    return None


async def fix_deliverable_titles(dry_run: bool = False, workspace_id: Optional[str] = None):
    """Main function to fix deliverable titles"""
    
    logger.info("🔍 Scanning for deliverables with tool references...")
    
    # Get affected deliverables
    affected_deliverables = get_deliverables_with_tool_references(workspace_id)
    
    if not affected_deliverables:
        logger.info("✅ No deliverables found with tool references!")
        return
    
    logger.info(f"📋 Found {len(affected_deliverables)} deliverables to fix")
    
    # Group by similar patterns for reporting
    pattern_groups = {
        'file_search': [],
        'internal_db': [],
        'instagram': [],
        'web_search': [],
        'research_gather': [],
        'instances': [],
        'other': []
    }
    
    for deliverable in affected_deliverables:
        title = deliverable.get('title', '')
        
        if 'File Search' in title:
            pattern_groups['file_search'].append(deliverable)
        elif 'Internal Database' in title:
            pattern_groups['internal_db'].append(deliverable)
        elif 'Instagram' in title:
            pattern_groups['instagram'].append(deliverable)
        elif 'Web Search' in title:
            pattern_groups['web_search'].append(deliverable)
        elif 'Research' in title or 'Gather' in title:
            pattern_groups['research_gather'].append(deliverable)
        elif 'Instance' in title:
            pattern_groups['instances'].append(deliverable)
        else:
            pattern_groups['other'].append(deliverable)
    
    # Report pattern distribution
    logger.info("\n📊 Pattern Distribution:")
    for pattern, items in pattern_groups.items():
        if items:
            logger.info(f"  {pattern}: {len(items)} deliverables")
    
    # Process each deliverable
    fixed_count = 0
    error_count = 0
    
    logger.info(f"\n{'🔧 DRY RUN - No changes will be made' if dry_run else '🔧 Applying fixes...'}\n")
    
    for deliverable in affected_deliverables:
        deliverable_id = deliverable.get('id')
        original_title = deliverable.get('title', '')
        goal_id = deliverable.get('goal_id')
        
        # Get goal description for context
        goal_description = get_goal_description(goal_id) if goal_id else None
        
        # Build context for sanitization
        context = {
            'goal_description': goal_description,
            'deliverable_type': deliverable.get('type'),
            'goal_id': goal_id
        }
        
        # Sanitize the title
        sanitized_title = sanitize_deliverable_title(original_title, context)
        
        # Skip if title didn't change
        if sanitized_title == original_title:
            logger.debug(f"⏭️ No changes needed for: {original_title[:50]}...")
            continue
        
        logger.info(f"📝 Fixing deliverable {deliverable_id}")
        logger.info(f"   Original: {original_title[:80]}{'...' if len(original_title) > 80 else ''}")
        logger.info(f"   Fixed:    {sanitized_title}")
        
        if not dry_run:
            try:
                # Update the deliverable title
                update_result = supabase.table('deliverables').update({
                    'title': sanitized_title,
                    'metadata': {
                        **deliverable.get('metadata', {}),
                        'title_sanitized': True,
                        'original_title': original_title,
                        'sanitization_timestamp': datetime.utcnow().isoformat()
                    }
                }).eq('id', deliverable_id).execute()
                
                if update_result.data:
                    fixed_count += 1
                    logger.info(f"   ✅ Fixed successfully")
                else:
                    error_count += 1
                    logger.error(f"   ❌ Failed to update")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"   ❌ Error updating deliverable {deliverable_id}: {e}")
        else:
            fixed_count += 1  # Count as would-be fixed in dry run
    
    # Final report
    logger.info("\n" + "=" * 60)
    logger.info("📊 FINAL REPORT")
    logger.info("=" * 60)
    logger.info(f"Total deliverables scanned: {len(affected_deliverables)}")
    logger.info(f"Deliverables {'would be' if dry_run else ''} fixed: {fixed_count}")
    
    if error_count > 0:
        logger.warning(f"Errors encountered: {error_count}")
    
    if dry_run:
        logger.info("\n⚠️ This was a DRY RUN - no changes were made")
        logger.info("Run without --dry-run to apply fixes")
    else:
        logger.info(f"\n✅ Successfully fixed {fixed_count} deliverable titles!")
    
    # Show examples of fixed titles
    if fixed_count > 0:
        logger.info("\n📝 Example transformations:")
        example_count = min(5, len(affected_deliverables))
        for i in range(example_count):
            deliverable = affected_deliverables[i]
            original = deliverable.get('title', '')
            
            context = {
                'goal_description': get_goal_description(deliverable.get('goal_id')),
                'deliverable_type': deliverable.get('type'),
                'goal_id': deliverable.get('goal_id')
            }
            
            sanitized = sanitize_deliverable_title(original, context)
            
            if sanitized != original:
                logger.info(f"\n  Before: {original[:60]}{'...' if len(original) > 60 else ''}")
                logger.info(f"  After:  {sanitized}")


def main():
    """Main entry point with argument parsing"""
    
    parser = argparse.ArgumentParser(
        description='Fix intermediate deliverable titles by removing tool references'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run in dry-run mode (no changes will be made)'
    )
    parser.add_argument(
        '--workspace-id',
        type=str,
        help='Only fix deliverables for a specific workspace'
    )
    
    args = parser.parse_args()
    
    logger.info("🚨 DELIVERABLE TITLE SANITIZATION HOTFIX")
    logger.info("=" * 60)
    
    if args.workspace_id:
        logger.info(f"Workspace filter: {args.workspace_id}")
    
    # Run the async function
    asyncio.run(fix_deliverable_titles(
        dry_run=args.dry_run,
        workspace_id=args.workspace_id
    ))


if __name__ == "__main__":
    main()