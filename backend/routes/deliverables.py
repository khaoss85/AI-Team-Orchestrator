# backend/routes/deliverables.py

from fastapi import Request, APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from middleware.trace_middleware import get_trace_id, create_traced_logger, TracedDatabaseOperation
import logging
import json
from database import supabase, create_deliverable, get_deliverables, get_deliverable_by_id, update_deliverable, delete_deliverable
from models import *

router = APIRouter(prefix="/deliverables", tags=["deliverables"])
logger = logging.getLogger(__name__)

@router.get("/workspace/{workspace_id}")
async def get_workspace_deliverables(request: Request, workspace_id: str):
    """Get all deliverables for a workspace"""
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_workspace_deliverables called for workspace {workspace_id}", endpoint="get_workspace_deliverables", trace_id=trace_id)
    try:
        logger.info(f"Querying deliverables for workspace {workspace_id}...")
        deliverables = await get_deliverables(workspace_id)
        logger.info(f"Deliverables query completed for workspace {workspace_id}. Found {len(deliverables)} deliverables. Data: {deliverables}")
        return deliverables
    except Exception as e:
        logger.error(f"❌ Error fetching deliverables for workspace {workspace_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch deliverables: {str(e)}")

@router.post("/workspace/{workspace_id}/create")
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
        
        return {
            "success": True,
            "deliverable": deliverable,
            "message": "Deliverable created successfully"
        }
            
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
            return {
                "success": True,
                "deliverable": deliverable,
                "message": "Deliverable updated successfully"
            }
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
    """Get deliverables for a specific goal"""
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_goal_deliverables called for goal {goal_id}", endpoint="get_goal_deliverables", trace_id=trace_id)
    try:
        logger.info(f"Querying deliverables for goal {goal_id} in workspace {workspace_id}...")
        deliverables = await get_deliverables(workspace_id, goal_id=goal_id)
        logger.info(f"Goal deliverables query completed. Found {len(deliverables)} deliverables for goal {goal_id}")
        return deliverables
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