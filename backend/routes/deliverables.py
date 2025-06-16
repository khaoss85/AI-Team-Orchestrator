# backend/routes/deliverables.py

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
import logging
import json
from database import supabase, create_deliverable, get_deliverables, get_deliverable_by_id, update_deliverable, delete_deliverable
from models import *

router = APIRouter(prefix="/deliverables", tags=["deliverables"])
logger = logging.getLogger(__name__)

@router.get("/workspace/{workspace_id}")
async def get_workspace_deliverables(workspace_id: str):
    """Get all deliverables for a workspace - Frontend compatible format"""
    try:
        logger.info(f"🔍 Fetching deliverables for workspace {workspace_id}")
        
        # Use CRUD function
        deliverables = await get_deliverables(workspace_id)
        
        # Transform deliverables to frontend-expected format
        key_outputs = []
        for deliverable in deliverables:
            # Transform deliverable to ProjectOutput format
            output = {
                "id": deliverable["id"],
                "title": deliverable["title"],
                "task_name": deliverable["title"],  # Alias for compatibility
                "description": deliverable.get("metadata", {}).get("description", ""),
                "type": deliverable["type"],
                "category": "final_deliverable" if deliverable["type"] == "final_report" else deliverable["type"],
                "content": deliverable["content"],
                "status": deliverable["status"],
                "created_at": deliverable["created_at"],
                "updated_at": deliverable.get("updated_at", deliverable["created_at"]),
                "readiness_score": deliverable.get("readiness_score", 100),
                "completion_percentage": deliverable.get("completion_percentage", 100),
                "business_value_score": deliverable.get("business_value_score", 85),
                "quality_metrics": deliverable.get("quality_metrics", {}),
                "metadata": deliverable.get("metadata", {}),
                # Frontend expected fields
                "key_insights": [],
                "metrics": deliverable.get("quality_metrics", {}),
                "actionable_assets": deliverable.get("content", {}),
                "actionability_score": deliverable.get("readiness_score", 100),
                "automation_ready": deliverable.get("completion_percentage", 0) >= 100,
                "visual_summary": None
            }
            key_outputs.append(output)
        
        # Return in frontend-expected format
        return {
            "workspace_id": workspace_id,
            "total_tasks": len(deliverables),
            "completed_tasks": len([d for d in deliverables if d["status"] == "completed"]),
            "key_outputs": key_outputs,
            "business_impact": {
                "deliverable_count": len(deliverables),
                "readiness_average": sum(d.get("readiness_score", 100) for d in deliverables) / len(deliverables) if deliverables else 0,
                "business_value_average": sum(d.get("business_value_score", 85) for d in deliverables) / len(deliverables) if deliverables else 0
            },
            "project_phase": "completed" if any(d["status"] == "completed" for d in deliverables) else "active",
            "last_updated": max([d["updated_at"] for d in deliverables], default=None) if deliverables else None
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching deliverables for workspace {workspace_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch deliverables: {str(e)}")

@router.post("/workspace/{workspace_id}/create")
async def create_workspace_deliverable(workspace_id: str, deliverable_data: Dict[str, Any]):
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
async def update_deliverable(deliverable_id: str, update_data: Dict[str, Any]):
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
async def delete_deliverable(deliverable_id: str):
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
async def get_deliverable(deliverable_id: str):
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
async def force_finalize_deliverables(workspace_id: str):
    """Force creation of final deliverables for completed goals"""
    try:
        logger.info(f"🚀 Force finalizing deliverables for workspace {workspace_id}")
        
        # Import the AI-driven deliverable creation logic
        from fix_deliverable_creation import check_and_fix_deliverable_creation
        
        # Run the AI-driven deliverable creation
        await check_and_fix_deliverable_creation()
        
        # Return updated deliverables
        result = supabase.table('deliverables').select('*').eq('workspace_id', workspace_id).execute()
        deliverables = result.data or []
        
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