# backend/routes/deliverables.py

from fastapi import Request, APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from middleware.trace_middleware import get_trace_id, create_traced_logger, TracedDatabaseOperation
import logging
import json
import os
from database import supabase, create_deliverable, get_deliverables, get_deliverable_by_id, update_deliverable as db_update_deliverable, delete_deliverable, get_workspace
from models import *

router = APIRouter(prefix="/deliverables", tags=["deliverables"])
logger = logging.getLogger(__name__)

async def enhance_deliverables_with_display_content(deliverables: List[Dict[str, Any]], workspace_id: str) -> List[Dict[str, Any]]:
    """
    🎨 PERSISTENT enhancement of deliverables with AI-transformed display content
    This function now SAVES transformed content to database to prevent infinite OpenAI loops
    
    CRITICAL FIX: Deliverables are transformed ONCE and persisted, not re-transformed on every request
    """
    try:
        import asyncio
        from datetime import datetime
        from services.ai_content_display_transformer import transform_deliverable_to_html
        
        # Limit the number of deliverables to transform (to prevent timeouts)
        MAX_TRANSFORM = int(os.getenv("AI_TRANSFORM_MAX_BATCH", "5"))  # Configurable batch size
        TRANSFORM_TIMEOUT = float(os.getenv("AI_TRANSFORM_TIMEOUT", "10.0"))  # Configurable timeout
        
        # Get workspace context for better transformation
        business_context = {}
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
        
        # CRITICAL: Separate deliverables based on PERSISTENT display_content
        to_transform = []
        already_enhanced = []
        cached_from_db = []
        
        for deliverable in deliverables:
            # Check if already has PERSISTED display_content (not just runtime)
            if deliverable.get('display_content') and deliverable.get('transformation_timestamp'):
                # Has persisted display content - use cached version
                cached_from_db.append(deliverable)
                logger.info(f"✅ Using CACHED display_content for deliverable {deliverable.get('id')} (transformed at {deliverable.get('transformation_timestamp')})")
            elif deliverable.get('display_content'):
                # Has runtime display_content but not persisted - still need to save
                already_enhanced.append(deliverable)
            else:
                # No display_content at all - needs transformation
                to_transform.append(deliverable)
        
        # Limit transformations
        if len(to_transform) > MAX_TRANSFORM:
            logger.info(f"⚠️ Limiting transformation to first {MAX_TRANSFORM} of {len(to_transform)} deliverables")
            remaining = to_transform[MAX_TRANSFORM:]
            to_transform = to_transform[:MAX_TRANSFORM]
        else:
            remaining = []
        
        # Transform deliverables asynchronously
        async def transform_single(deliverable):
            """Transform a single deliverable with timeout AND PERSIST TO DATABASE"""
            try:
                # Create a copy to avoid modifying original
                enhanced = deliverable.copy()
                deliverable_id = enhanced.get('id')
                
                # Extract content
                content = enhanced.get('content', {})
                if isinstance(content, str):
                    try:
                        content = json.loads(content)
                    except json.JSONDecodeError:
                        content = {"raw_content": content}
                
                # Transform with timeout
                logger.info(f"🎨 Transforming deliverable {deliverable_id} to display format")
                
                transformation_result = await asyncio.wait_for(
                    transform_deliverable_to_html(content, business_context),
                    timeout=TRANSFORM_TIMEOUT
                )
                
                if transformation_result:
                    # Add display fields to deliverable
                    enhanced['display_content'] = transformation_result.transformed_content
                    enhanced['display_format'] = transformation_result.display_format
                    enhanced['display_quality_score'] = transformation_result.transformation_confidence / 100.0
                    enhanced['auto_display_generated'] = True
                    enhanced['transformation_timestamp'] = datetime.now().isoformat()
                    enhanced['content_transformation_status'] = 'success'
                    enhanced['transformation_method'] = 'ai'
                    enhanced['ai_confidence'] = transformation_result.transformation_confidence / 100.0
                    
                    # 🚀 CRITICAL: PERSIST TO DATABASE to prevent re-transformation
                    try:
                        update_data = {
                            'display_content': transformation_result.transformed_content,
                            'display_format': transformation_result.display_format,
                            'display_quality_score': transformation_result.transformation_confidence / 100.0,
                            'auto_display_generated': True,
                            'transformation_timestamp': datetime.now().isoformat(),
                            'content_transformation_status': 'success',
                            'transformation_method': 'ai',
                            'ai_confidence': transformation_result.transformation_confidence / 100.0
                        }
                        
                        # Use the update_deliverable function from database.py
                        # Note: db_update_deliverable expects only 2 args: deliverable_id and update_data
                        await db_update_deliverable(deliverable_id, update_data)
                        logger.info(f"💾 PERSISTED display_content for deliverable {deliverable_id} to database - will use cache on next request")
                        
                    except Exception as db_error:
                        logger.error(f"⚠️ Failed to persist display_content for deliverable {deliverable_id}: {db_error}")
                        # Continue even if persistence fails - at least return transformed content for this request
                    
                    logger.info(f"✅ Enhanced deliverable {deliverable_id} with display content (confidence: {transformation_result.transformation_confidence}%)")
                else:
                    logger.warning(f"⚠️ Transformation returned no result for deliverable {deliverable_id}")
                
                return enhanced
                
            except asyncio.TimeoutError:
                logger.warning(f"⏱️ Transformation timed out for deliverable {deliverable.get('id')}")
                # Mark as failed in database to avoid retrying
                try:
                    await db_update_deliverable(deliverable.get('id'), {
                        'content_transformation_status': 'failed',
                        'content_transformation_error': 'Transformation timeout'
                    })
                except:
                    pass
                return deliverable
            except Exception as e:
                logger.error(f"❌ Failed to transform deliverable {deliverable.get('id')}: {e}")
                # Mark as failed in database to avoid retrying
                try:
                    await db_update_deliverable(deliverable.get('id'), {
                        'content_transformation_status': 'failed', 
                        'content_transformation_error': str(e)
                    })
                except:
                    pass
                return deliverable
        
        # Process transformations concurrently
        if to_transform:
            logger.info(f"🎨 Transforming {len(to_transform)} deliverables concurrently...")
            transformation_tasks = [transform_single(d) for d in to_transform]
            transformed = await asyncio.gather(*transformation_tasks, return_exceptions=False)
        else:
            transformed = []
        
        # Combine all deliverables (include cached ones first!)
        all_enhanced = cached_from_db + already_enhanced + transformed + remaining
        
        # Log summary with cache statistics
        total_with_display = sum(1 for d in all_enhanced if d.get('display_content'))
        total_cached = len(cached_from_db)
        total_transformed = len(transformed)
        logger.info(f"📊 Enhancement summary: {total_with_display}/{len(all_enhanced)} deliverables have display content")
        logger.info(f"💾 Cache statistics: {total_cached} cached (no OpenAI calls), {total_transformed} newly transformed")
        
        # Calculate OpenAI calls saved
        if total_cached > 0:
            logger.info(f"🎉 SAVED {total_cached} OpenAI API calls by using cached display_content!")
        
        return all_enhanced
        
    except Exception as e:
        logger.error(f"❌ Error enhancing deliverables: {e}")
        # Return original deliverables if enhancement fails
        return deliverables

@router.get("/workspace/{workspace_id}")
async def get_workspace_deliverables(request: Request, workspace_id: str):
    """Get all deliverables for a workspace with AI-enhanced display content"""
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_workspace_deliverables called for workspace {workspace_id}", endpoint="get_workspace_deliverables", trace_id=trace_id)
    try:
        logger.info(f"Querying deliverables for workspace {workspace_id}...")
        deliverables = await get_deliverables(workspace_id)
        logger.info(f"Deliverables query completed for workspace {workspace_id}. Found {len(deliverables)} deliverables.")
        
        # 🎨 RUNTIME TRANSFORMATION: Add display_content to deliverables
        # This is a temporary solution until database schema is updated
        enhanced_deliverables = await enhance_deliverables_with_display_content(deliverables, workspace_id)
        
        return enhanced_deliverables
    except Exception as e:
        logger.error(f"❌ Error fetching deliverables for workspace {workspace_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch deliverables: {str(e)}")

@router.post("/workspace/{workspace_id}/create", status_code=201)
async def create_workspace_deliverable(workspace_id: str, deliverable_data: Dict[str, Any], request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route create_workspace_deliverable called", endpoint="create_workspace_deliverable", trace_id=trace_id)

    """Create a new deliverable for a workspace"""
    try:
        logger.info(f"📝 Creating deliverable for workspace {workspace_id}")
        
        # Validate required fields
        required_fields = ['title', 'type', 'content']
        for field in required_fields:
            if field not in deliverable_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Prepare deliverable data
        create_data = {
            'title': deliverable_data['title'],
            'type': deliverable_data.get('type', 'final_report'),
            'content': deliverable_data['content'],
            'status': deliverable_data.get('status', 'completed'),
            'readiness_score': deliverable_data.get('readiness_score', 85),
            'completion_percentage': deliverable_data.get('completion_percentage', 100),
            'business_value_score': deliverable_data.get('business_value_score', 80),
            'quality_metrics': deliverable_data.get('quality_metrics', {}),
            'metadata': deliverable_data.get('metadata', {})
        }
        
        # Use CRUD function
        deliverable = await create_deliverable(workspace_id, create_data)
        
        return deliverable
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating deliverable for workspace {workspace_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create deliverable: {str(e)}")

@router.put("/{deliverable_id}")
async def update_deliverable(deliverable_id: str, update_data: Dict[str, Any], request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route update_deliverable called", endpoint="update_deliverable", trace_id=trace_id)

    """Update a deliverable"""
    try:
        logger.info(f"🔄 Updating deliverable {deliverable_id}")
        
        # Update deliverable
        result = supabase.table('deliverables').update(update_data).eq('id', deliverable_id).execute()
        
        if result.data:
            deliverable = result.data[0]
            logger.info(f"✅ Updated deliverable {deliverable_id}")
            return deliverable
        else:
            raise HTTPException(status_code=404, detail="Deliverable not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating deliverable {deliverable_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update deliverable: {str(e)}")

@router.delete("/{deliverable_id}")
async def delete_deliverable(deliverable_id: str, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route delete_deliverable called", endpoint="delete_deliverable", trace_id=trace_id)

    """Delete a deliverable"""
    try:
        logger.info(f"🗑️ Deleting deliverable {deliverable_id}")
        
        # Delete deliverable
        result = supabase.table('deliverables').delete().eq('id', deliverable_id).execute()
        
        if result.data:
            logger.info(f"✅ Deleted deliverable {deliverable_id}")
            return {
                "success": True,
                "message": "Deliverable deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Deliverable not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting deliverable {deliverable_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete deliverable: {str(e)}")

@router.get("/{deliverable_id}")
async def get_deliverable(deliverable_id: str, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_deliverable called", endpoint="get_deliverable", trace_id=trace_id)

    """Get a specific deliverable by ID"""
    try:
        logger.info(f"🔍 Fetching deliverable {deliverable_id}")
        
        result = supabase.table('deliverables').select('*').eq('id', deliverable_id).execute()
        
        if result.data:
            deliverable = result.data[0]
            logger.info(f"📦 Found deliverable {deliverable_id}")
            return {
                "deliverable": deliverable,
                "success": True
            }
        else:
            raise HTTPException(status_code=404, detail="Deliverable not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching deliverable {deliverable_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch deliverable: {str(e)}")

@router.post("/workspace/{workspace_id}/force-finalize")
async def force_finalize_deliverables(workspace_id: str, request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route force_finalize_deliverables called", endpoint="force_finalize_deliverables", trace_id=trace_id)

    """Force creation of final deliverables for completed goals"""
    try:
        logger.info(f"🚀 Force finalizing deliverables for workspace {workspace_id}")
        
        # Import the AI-driven deliverable creation logic
        from deliverable_system.unified_deliverable_engine import check_and_create_final_deliverable
        
        # Run the AI-driven deliverable creation (force mode)
        await check_and_create_final_deliverable(workspace_id, force=True)
        
        # Return updated deliverables using the proper function
        deliverables = await get_deliverables(workspace_id)
        
        logger.info(f"✅ Force finalization complete. {len(deliverables)} deliverables available")
        
        return {
            "success": True,
            "deliverables": deliverables,
            "count": len(deliverables),
            "message": f"Created {len(deliverables)} deliverables"
        }
        
    except Exception as e:
        logger.error(f"❌ Error force finalizing deliverables for workspace {workspace_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to force finalize deliverables: {str(e)}")

@router.get("/workspace/{workspace_id}/goal/{goal_id}")
async def get_goal_deliverables(request: Request, workspace_id: str, goal_id: str):
    """Get deliverables for a specific goal with AI-enhanced display content"""
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_goal_deliverables called for goal {goal_id}", endpoint="get_goal_deliverables", trace_id=trace_id)
    try:
        logger.info(f"Querying deliverables for goal {goal_id} in workspace {workspace_id}...")
        deliverables = await get_deliverables(workspace_id, goal_id=goal_id)
        logger.info(f"Goal deliverables query completed. Found {len(deliverables)} deliverables for goal {goal_id}")
        
        # 🎨 RUNTIME TRANSFORMATION: Add display_content to deliverables
        enhanced_deliverables = await enhance_deliverables_with_display_content(deliverables, workspace_id)
        
        return enhanced_deliverables
    except Exception as e:
        logger.error(f"❌ Error fetching deliverables for goal {goal_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch goal deliverables: {str(e)}")

@router.post("/workspace/{workspace_id}/goal/{goal_id}/create")
async def create_goal_deliverable(workspace_id: str, goal_id: str, request: Request):
    """Force creation of deliverable for a specific goal"""
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route create_goal_deliverable called for goal {goal_id}", endpoint="create_goal_deliverable", trace_id=trace_id)
    
    try:
        logger.info(f"🎯 Force creating goal-specific deliverable for goal {goal_id} in workspace {workspace_id}")
        
        # Import the goal-specific deliverable creation logic
        from deliverable_system.unified_deliverable_engine import create_goal_specific_deliverable
        
        # Create goal-specific deliverable (force mode)
        deliverable = await create_goal_specific_deliverable(workspace_id, goal_id, force=True)
        
        if deliverable:
            logger.info(f"✅ Goal-specific deliverable created: {deliverable.get('id')}")
            return {
                "success": True,
                "deliverable": deliverable,
                "message": f"Goal-specific deliverable created successfully"
            }
        else:
            logger.warning(f"⚠️ No deliverable created for goal {goal_id}")
            return {
                "success": False,
                "message": "No deliverable was created (conditions not met or no completed tasks)"
            }
        
    except Exception as e:
        logger.error(f"❌ Error creating goal-specific deliverable for goal {goal_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create goal deliverable: {str(e)}")