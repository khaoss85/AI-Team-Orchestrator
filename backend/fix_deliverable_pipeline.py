"""
Fix for the deliverable creation pipeline - ensures deliverables are properly saved to the database
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

async def fix_deliverable_creation_in_aggregator():
    """
    Patches the deliverable aggregator to properly save deliverables to the database
    instead of just creating them as tasks.
    """
    try:
        # Import the necessary modules
        from deliverable_aggregator import IntelligentDeliverableAggregator
        from database import create_deliverable
        
        # Store the original method
        original_create_task = IntelligentDeliverableAggregator._create_intelligent_deliverable_task
        
        async def patched_create_intelligent_deliverable_task(
            self,
            workspace_id: str,
            workspace: Dict,
            intelligent_deliverable: Any,
            deliverable_analysis: Dict[str, Any],
            quality_enhanced_data: Optional[Dict] = None
        ) -> Optional[str]:
            """Enhanced version that saves to deliverables table"""
            
            try:
                # First, save the deliverable to the deliverables table
                deliverable_data = {
                    'title': f"AI-Generated {deliverable_analysis.get('deliverable_type', 'Business Package')}",
                    'type': deliverable_analysis.get('deliverable_type', 'final_report'),
                    'content': {
                        'executive_summary': intelligent_deliverable.executive_summary,
                        'actionable_assets': {
                            asset_id: asset.model_dump() if hasattr(asset, 'model_dump') else asset
                            for asset_id, asset in intelligent_deliverable.actionable_assets.items()
                        },
                        'usage_guide': intelligent_deliverable.usage_guide,
                        'next_steps': intelligent_deliverable.next_steps,
                        'meta': intelligent_deliverable.meta
                    },
                    'status': 'completed',
                    'readiness_score': intelligent_deliverable.actionability_score * 100,
                    'completion_percentage': 100,
                    'business_value_score': deliverable_analysis.get('confidence_score', 0.8) * 100,
                    'quality_metrics': {
                        'ai_confidence': deliverable_analysis.get('confidence_score', 0.8),
                        'total_assets': len(intelligent_deliverable.actionable_assets),
                        'automation_ready': intelligent_deliverable.automation_ready,
                        'quality_enhanced': quality_enhanced_data is not None
                    },
                    'metadata': {
                        'deliverable_id': intelligent_deliverable.deliverable_id,
                        'workspace_goal': workspace.get('goal', ''),
                        'creation_timestamp': datetime.now().isoformat(),
                        'ai_analysis': deliverable_analysis,
                        'quality_enhancement': quality_enhanced_data
                    }
                }
                
                # Save to deliverables table
                saved_deliverable = await create_deliverable(workspace_id, deliverable_data)
                
                if saved_deliverable:
                    logger.critical(f"✅ DELIVERABLE SAVED TO DATABASE: {saved_deliverable['id']} for workspace {workspace_id}")
                    
                    # Also create the task for backward compatibility
                    task_id = await original_create_task(
                        self, workspace_id, workspace, intelligent_deliverable, 
                        deliverable_analysis, quality_enhanced_data
                    )
                    
                    # Update the task to reference the deliverable
                    if task_id:
                        from database import update_task_status
                        await update_task_status(
                            task_id, 
                            "completed",
                            {"deliverable_id": saved_deliverable['id']}
                        )
                    
                    return saved_deliverable['id']
                else:
                    logger.error(f"Failed to save deliverable to database for workspace {workspace_id}")
                    # Fall back to original behavior
                    return await original_create_task(
                        self, workspace_id, workspace, intelligent_deliverable, 
                        deliverable_analysis, quality_enhanced_data
                    )
                    
            except Exception as e:
                logger.error(f"Error in patched deliverable creation: {e}")
                # Fall back to original behavior
                return await original_create_task(
                    self, workspace_id, workspace, intelligent_deliverable, 
                    deliverable_analysis, quality_enhanced_data
                )
        
        # Apply the patch
        IntelligentDeliverableAggregator._create_intelligent_deliverable_task = patched_create_intelligent_deliverable_task
        logger.info("✅ Successfully patched deliverable creation to save to database")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to patch deliverable creation: {e}")
        return False


async def convert_existing_deliverable_tasks():
    """
    Finds existing deliverable tasks and converts them to proper deliverable records
    """
    try:
        from database import list_tasks, create_deliverable, get_supabase_client
        
        supabase = get_supabase_client()
        
        # Find all workspaces
        workspaces_result = supabase.table('workspaces').select('id').execute()
        
        converted_count = 0
        
        for workspace in workspaces_result.data or []:
            workspace_id = workspace['id']
            
            # Find deliverable tasks
            tasks = await list_tasks(workspace_id)
            
            for task in tasks:
                context_data = task.get('context_data', {})
                
                # Check if this is a deliverable task
                if (context_data.get('is_final_deliverable') or 
                    context_data.get('deliverable_aggregation') or
                    context_data.get('intelligent_deliverable')):
                    
                    # Check if already converted
                    existing_check = supabase.table('deliverables')\
                        .select('id')\
                        .eq('workspace_id', workspace_id)\
                        .eq('metadata->>task_id', task['id'])\
                        .execute()
                    
                    if existing_check.data:
                        continue
                    
                    # Extract deliverable data
                    precomputed = context_data.get('precomputed_deliverable', {})
                    
                    if precomputed:
                        deliverable_data = {
                            'title': task.get('name', 'Converted Deliverable'),
                            'type': context_data.get('deliverable_type', 'final_report'),
                            'content': precomputed,
                            'status': 'completed' if task.get('status') == 'completed' else 'draft',
                            'readiness_score': precomputed.get('actionability_score', 0.8) * 100,
                            'completion_percentage': 100 if task.get('status') == 'completed' else 50,
                            'business_value_score': context_data.get('ai_analysis_confidence', 0.8) * 100,
                            'quality_metrics': {
                                'total_assets': context_data.get('total_assets', 0),
                                'automation_ready': context_data.get('automation_ready', False),
                                'quality_enhanced': context_data.get('quality_enhanced', False)
                            },
                            'metadata': {
                                'task_id': task['id'],
                                'converted_from_task': True,
                                'conversion_timestamp': datetime.now().isoformat(),
                                'original_context': context_data
                            }
                        }
                        
                        # Create deliverable record
                        deliverable = await create_deliverable(workspace_id, deliverable_data)
                        
                        if deliverable:
                            converted_count += 1
                            logger.info(f"✅ Converted task {task['id']} to deliverable {deliverable['id']}")
                        
        logger.info(f"🎉 Successfully converted {converted_count} deliverable tasks to proper deliverables")
        return converted_count
        
    except Exception as e:
        logger.error(f"Error converting existing deliverable tasks: {e}")
        return 0


async def main():
    """Run the fix"""
    logging.basicConfig(level=logging.INFO)
    
    # First patch the aggregator
    logger.info("🔧 Patching deliverable aggregator...")
    patch_success = await fix_deliverable_creation_in_aggregator()
    
    if patch_success:
        logger.info("✅ Patch applied successfully")
        
        # Then convert existing tasks
        logger.info("🔄 Converting existing deliverable tasks...")
        converted = await convert_existing_deliverable_tasks()
        
        logger.info(f"✅ Fix complete! Converted {converted} existing deliverables")
    else:
        logger.error("❌ Failed to apply patch")


if __name__ == "__main__":
    asyncio.run(main())