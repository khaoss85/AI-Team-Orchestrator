#!/usr/bin/env python3
"""
Transform existing deliverables to add AI-enhanced display content
This script processes all existing deliverables and asset_artifacts to add
the display_content field using the AI Content Display Transformer.
"""

import asyncio
import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def transform_existing_deliverables(workspace_id: Optional[str] = None, limit: Optional[int] = None):
    """
    Transform existing deliverables to add display_content using AI transformation
    
    Args:
        workspace_id: Optional - Only process deliverables for specific workspace
        limit: Optional - Maximum number of deliverables to process
    """
    try:
        from database import supabase, get_deliverables, get_workspace
        from services.ai_content_display_transformer import transform_deliverable_to_html
        import json
        
        logger.info("🎨 Starting transformation of existing deliverables to AI-enhanced display content")
        
        # Get deliverables to process
        if workspace_id:
            logger.info(f"Processing deliverables for workspace {workspace_id}")
            deliverables = await get_deliverables(workspace_id, limit=limit)
        else:
            logger.info("Processing all deliverables across all workspaces")
            # Get all deliverables (no workspace filter)
            result = supabase.table('deliverables').select('*').order('created_at', desc=True)
            if limit:
                result = result.limit(limit)
            deliverables = result.execute().data or []
        
        logger.info(f"Found {len(deliverables)} deliverables to process")
        
        # Statistics
        total_processed = 0
        successful_transforms = 0
        failed_transforms = 0
        skipped = 0
        
        for deliverable in deliverables:
            deliverable_id = deliverable.get('id')
            workspace_id = deliverable.get('workspace_id')
            title = deliverable.get('title', 'Unknown')
            
            logger.info(f"\n📦 Processing deliverable: {title} (ID: {deliverable_id})")
            
            # Check if already has display content in asset_artifacts
            try:
                # Check if asset_artifact exists for this deliverable
                artifact_result = supabase.table('asset_artifacts')\
                    .select('id, display_content, content_transformation_status')\
                    .eq('metadata->>original_deliverable_id', deliverable_id)\
                    .execute()
                
                if artifact_result.data:
                    artifact = artifact_result.data[0]
                    if artifact.get('display_content'):
                        logger.info(f"✅ Deliverable already has display_content, skipping")
                        skipped += 1
                        continue
                    
                    # Update existing artifact with display content
                    artifact_id = artifact.get('id')
                    await transform_and_update_artifact(artifact_id, deliverable, workspace_id)
                    successful_transforms += 1
                else:
                    # Create new artifact with display content
                    logger.info(f"Creating new asset_artifact for deliverable {deliverable_id}")
                    from database import convert_deliverable_to_asset_artifact
                    result = await convert_deliverable_to_asset_artifact(deliverable)
                    if result:
                        successful_transforms += 1
                    else:
                        failed_transforms += 1
                        
                total_processed += 1
                
            except Exception as e:
                logger.error(f"❌ Error processing deliverable {deliverable_id}: {e}")
                failed_transforms += 1
                total_processed += 1
                continue
        
        # Final report
        logger.info("\n" + "="*60)
        logger.info("🎨 TRANSFORMATION COMPLETE")
        logger.info("="*60)
        logger.info(f"Total deliverables found: {len(deliverables)}")
        logger.info(f"Total processed: {total_processed}")
        logger.info(f"✅ Successful transformations: {successful_transforms}")
        logger.info(f"❌ Failed transformations: {failed_transforms}")
        logger.info(f"⏭️  Skipped (already had display content): {skipped}")
        logger.info("="*60)
        
        return {
            "total_found": len(deliverables),
            "total_processed": total_processed,
            "successful": successful_transforms,
            "failed": failed_transforms,
            "skipped": skipped
        }
        
    except Exception as e:
        logger.error(f"❌ Fatal error in transformation process: {e}")
        raise

async def transform_and_update_artifact(artifact_id: str, deliverable: dict, workspace_id: str):
    """
    Transform deliverable content and update existing artifact with display content
    """
    try:
        from database import supabase, get_workspace
        from services.ai_content_display_transformer import transform_deliverable_to_html
        import json
        
        logger.info(f"🎨 Transforming content for artifact {artifact_id}")
        
        # Extract content from deliverable
        content = deliverable.get('content', {})
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                content = {"raw_content": content}
        
        # Get business context for better transformation
        business_context = {}
        if workspace_id:
            try:
                workspace = await get_workspace(workspace_id)
                if workspace:
                    business_context = {
                        "company_name": workspace.get("company_name", ""),
                        "industry": workspace.get("industry", ""),
                        "workspace_name": workspace.get("name", "")
                    }
            except Exception as e:
                logger.warning(f"Could not get workspace context: {e}")
        
        # Transform to HTML format
        transformation_result = await transform_deliverable_to_html(content, business_context)
        
        if transformation_result:
            # Update artifact with display content
            update_data = {
                "display_content": transformation_result.transformed_content,
                "display_format": transformation_result.display_format,
                "display_quality_score": transformation_result.transformation_confidence / 100.0,
                "content_transformation_status": "success",
                "transformation_timestamp": datetime.now().isoformat(),
                "auto_display_generated": True
            }
            
            result = supabase.table('asset_artifacts')\
                .update(update_data)\
                .eq('id', artifact_id)\
                .execute()
            
            if result.data:
                logger.info(f"✅ Successfully updated artifact {artifact_id} with display content")
                logger.info(f"   Confidence: {transformation_result.transformation_confidence}%")
                logger.info(f"   Processing time: {transformation_result.processing_time}s")
            else:
                logger.error(f"❌ Failed to update artifact {artifact_id}")
        else:
            logger.warning(f"⚠️ Transformation returned no result for artifact {artifact_id}")
            
    except Exception as e:
        logger.error(f"❌ Error transforming artifact {artifact_id}: {e}")
        raise

async def check_transformation_status():
    """
    Check the current status of deliverable transformations
    """
    try:
        from database import supabase
        
        logger.info("\n🔍 CHECKING TRANSFORMATION STATUS")
        logger.info("="*60)
        
        # Count total asset_artifacts
        total_result = supabase.table('asset_artifacts').select('id', count='exact').execute()
        total_artifacts = total_result.count if hasattr(total_result, 'count') else len(total_result.data or [])
        
        # Count artifacts with display_content
        with_display_result = supabase.table('asset_artifacts')\
            .select('id')\
            .not_.is_('display_content', 'null')\
            .execute()
        with_display = len(with_display_result.data or [])
        
        # Count by transformation status
        status_result = supabase.table('asset_artifacts')\
            .select('content_transformation_status')\
            .execute()
        
        status_counts = {}
        for item in (status_result.data or []):
            status = item.get('content_transformation_status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        logger.info(f"Total asset_artifacts: {total_artifacts}")
        logger.info(f"With display_content: {with_display}")
        logger.info(f"Without display_content: {total_artifacts - with_display}")
        logger.info("\nTransformation Status Breakdown:")
        for status, count in status_counts.items():
            logger.info(f"  {status}: {count}")
        
        if total_artifacts > 0:
            completion_percentage = (with_display / total_artifacts) * 100
            logger.info(f"\n📊 Completion: {completion_percentage:.1f}%")
        
        logger.info("="*60)
        
        return {
            "total_artifacts": total_artifacts,
            "with_display_content": with_display,
            "without_display_content": total_artifacts - with_display,
            "status_breakdown": status_counts
        }
        
    except Exception as e:
        logger.error(f"❌ Error checking transformation status: {e}")
        raise

async def main():
    """
    Main function to run the transformation process
    """
    import sys
    
    # Parse command line arguments
    workspace_id = None
    limit = None
    check_only = False
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--check':
            check_only = True
        elif sys.argv[1] == '--help':
            print("""
Usage: python transform_existing_deliverables.py [OPTIONS]

Options:
    --check              Check transformation status without processing
    --workspace <id>     Process only deliverables for specific workspace
    --limit <number>     Process only the first N deliverables
    --help              Show this help message

Examples:
    python transform_existing_deliverables.py                    # Process all deliverables
    python transform_existing_deliverables.py --check           # Check status only
    python transform_existing_deliverables.py --workspace abc123 # Process specific workspace
    python transform_existing_deliverables.py --limit 10        # Process first 10 deliverables
""")
            return
        else:
            # Parse workspace and limit arguments
            args = sys.argv[1:]
            for i, arg in enumerate(args):
                if arg == '--workspace' and i + 1 < len(args):
                    workspace_id = args[i + 1]
                elif arg == '--limit' and i + 1 < len(args):
                    limit = int(args[i + 1])
    
    if check_only:
        # Just check status
        await check_transformation_status()
    else:
        # Run transformation
        logger.info("🚀 Starting AI Content Display Transformation Process")
        logger.info(f"Workspace: {workspace_id or 'ALL'}")
        logger.info(f"Limit: {limit or 'NO LIMIT'}")
        
        result = await transform_existing_deliverables(workspace_id, limit)
        
        # Show final status
        await check_transformation_status()

if __name__ == "__main__":
    asyncio.run(main())