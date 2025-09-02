"""
Workspace Monitoring Routes
Endpoints for monitoring workspace resources and detecting leaks
"""

from fastapi import APIRouter, HTTPException, Request, status
from services.workspace_cleanup_service import workspace_cleanup_service
from utils.auth_utils import get_trace_id, create_traced_logger
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/orphaned-resources", status_code=status.HTTP_200_OK)
async def check_orphaned_resources(request: Request):
    """
    Detect orphaned OpenAI resources not linked to active workspaces
    Useful for monitoring and cost leak detection
    """
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info("Route check_orphaned_resources called", endpoint="check_orphaned_resources", trace_id=trace_id)
    
    try:
        results = await workspace_cleanup_service.detect_orphaned_resources()
        
        if results.get("detection_failed"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to detect orphaned resources: {results.get('error')}"
            )
        
        return {
            "success": True,
            "orphaned_resources": results,
            "requires_attention": results.get("requires_cleanup", False)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking orphaned resources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check orphaned resources: {str(e)}"
        )

@router.get("/cleanup-test/{workspace_id}", status_code=status.HTTP_200_OK)
async def test_workspace_cleanup(workspace_id: str, request: Request):
    """
    Test workspace cleanup process without actually deleting the workspace
    Shows what resources would be cleaned up
    """
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route test_workspace_cleanup called for workspace {workspace_id}", 
               endpoint="test_workspace_cleanup", trace_id=trace_id)
    
    try:
        # This is a dry-run simulation
        from database import get_supabase_client
        supabase = get_supabase_client()
        
        # Check documents that would be cleaned
        documents_response = supabase.table("workspace_documents")\
            .select("id, filename, openai_file_id")\
            .eq("workspace_id", workspace_id)\
            .execute()
        
        documents = documents_response.data if documents_response.data else []
        
        # Check vector stores that would be cleaned
        stores_response = supabase.table("workspace_vector_stores")\
            .select("id, openai_vector_store_id")\
            .eq("workspace_id", workspace_id)\
            .execute()
        
        stores = stores_response.data if stores_response.data else []
        
        return {
            "success": True,
            "workspace_id": workspace_id,
            "simulation": True,
            "would_cleanup": {
                "documents_count": len(documents),
                "documents": [{"id": doc["id"], "filename": doc["filename"]} for doc in documents],
                "vector_stores_count": len(stores),
                "vector_stores": [{"id": store["id"], "openai_id": store["openai_vector_store_id"]} for store in stores],
                "openai_files_count": len([doc for doc in documents if doc.get("openai_file_id")])
            }
        }
        
    except Exception as e:
        logger.error(f"Error testing workspace cleanup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test workspace cleanup: {str(e)}"
        )

@router.get("/resources-summary", status_code=status.HTTP_200_OK)
async def get_resources_summary(request: Request):
    """
    Get summary of all workspace resources across the system
    Useful for cost monitoring and capacity planning
    """
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info("Route get_resources_summary called", endpoint="get_resources_summary", trace_id=trace_id)
    
    try:
        from database import get_supabase_client
        supabase = get_supabase_client()
        
        # Count total documents
        docs_count = supabase.table("workspace_documents")\
            .select("id", count="exact")\
            .execute()
        
        # Count total vector stores
        stores_count = supabase.table("workspace_vector_stores")\
            .select("id", count="exact")\
            .execute()
        
        # Count documents with OpenAI files
        openai_files_count = supabase.table("workspace_documents")\
            .select("id", count="exact")\
            .not_.is_("openai_file_id", "null")\
            .execute()
        
        # Get per-workspace breakdown
        workspace_breakdown = supabase.table("workspace_documents")\
            .select("workspace_id")\
            .execute()
        
        workspaces_with_docs = {}
        if workspace_breakdown.data:
            for doc in workspace_breakdown.data:
                ws_id = doc["workspace_id"]
                workspaces_with_docs[ws_id] = workspaces_with_docs.get(ws_id, 0) + 1
        
        return {
            "success": True,
            "summary": {
                "total_documents": docs_count.count or 0,
                "total_vector_stores": stores_count.count or 0,
                "total_openai_files": openai_files_count.count or 0,
                "workspaces_with_documents": len(workspaces_with_docs),
                "per_workspace_counts": workspaces_with_docs
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting resources summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get resources summary: {str(e)}"
        )