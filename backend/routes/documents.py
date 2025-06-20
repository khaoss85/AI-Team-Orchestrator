#!/usr/bin/env python3
"""
Document Management API Routes
Handles document upload, listing, and management
"""

from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from typing import List, Optional
import logging
import base64

from services.document_manager import document_manager, DocumentMetadata
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

class DocumentUploadRequest(BaseModel):
    """Request model for document upload via base64"""
    file_data: str  # base64 encoded
    filename: str
    sharing_scope: str = "team"
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class DocumentListResponse(BaseModel):
    """Response model for document listing"""
    documents: List[dict]
    total: int

@router.post("/{workspace_id}/upload")
async def upload_document(
    workspace_id: str,
    request: DocumentUploadRequest
):
    """Upload a document to workspace"""
    try:
        # Decode base64 file content
        try:
            file_content = base64.b64decode(request.file_data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid base64 file data: {str(e)}"
            )
        
        # Upload document
        doc_metadata = await document_manager.upload_document(
            workspace_id=workspace_id,
            file_content=file_content,
            filename=request.filename,
            uploaded_by="chat",
            sharing_scope=request.sharing_scope,
            description=request.description,
            tags=request.tags
        )
        
        return {
            "success": True,
            "document": {
                "id": doc_metadata.id,
                "filename": doc_metadata.filename,
                "file_size": doc_metadata.file_size,
                "mime_type": doc_metadata.mime_type,
                "sharing_scope": doc_metadata.sharing_scope,
                "vector_store_id": doc_metadata.vector_store_id,
                "upload_date": doc_metadata.upload_date.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document upload failed: {str(e)}"
        )

@router.post("/{workspace_id}/upload-file")
async def upload_document_file(
    workspace_id: str,
    file: UploadFile = File(...),
    sharing_scope: str = Form("team"),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None)  # Comma-separated tags
):
    """Upload a document file directly (multipart form)"""
    try:
        # Read file content
        file_content = await file.read()
        
        # Parse tags if provided
        tag_list = [tag.strip() for tag in tags.split(",")] if tags else None
        
        # Upload document
        doc_metadata = await document_manager.upload_document(
            workspace_id=workspace_id,
            file_content=file_content,
            filename=file.filename,
            uploaded_by="api",
            sharing_scope=sharing_scope,
            description=description,
            tags=tag_list
        )
        
        return {
            "success": True,
            "document": {
                "id": doc_metadata.id,
                "filename": doc_metadata.filename,
                "file_size": doc_metadata.file_size,
                "mime_type": doc_metadata.mime_type,
                "sharing_scope": doc_metadata.sharing_scope,
                "vector_store_id": doc_metadata.vector_store_id,
                "upload_date": doc_metadata.upload_date.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document upload failed: {str(e)}"
        )

@router.get("/{workspace_id}")
async def list_documents(
    workspace_id: str,
    scope: Optional[str] = None
):
    """List all documents in workspace"""
    try:
        documents = await document_manager.list_documents(workspace_id, scope)
        
        # Convert to JSON-serializable format
        doc_list = []
        for doc in documents:
            doc_list.append({
                "id": doc.id,
                "filename": doc.filename,
                "file_size": doc.file_size,
                "mime_type": doc.mime_type,
                "upload_date": doc.upload_date.isoformat(),
                "uploaded_by": doc.uploaded_by,
                "sharing_scope": doc.sharing_scope,
                "description": doc.description,
                "tags": doc.tags
            })
        
        return DocumentListResponse(
            documents=doc_list,
            total=len(doc_list)
        )
        
    except Exception as e:
        logger.error(f"Document listing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document listing failed: {str(e)}"
        )

@router.delete("/{workspace_id}/{document_id}")
async def delete_document(
    workspace_id: str,
    document_id: str
):
    """Delete a document from workspace"""
    try:
        success = await document_manager.delete_document(document_id, workspace_id)
        
        if success:
            return {"success": True, "message": "Document deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document deletion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document deletion failed: {str(e)}"
        )

@router.get("/{workspace_id}/vector-stores")
async def get_vector_stores(workspace_id: str):
    """Get vector stores for workspace"""
    try:
        vector_store_ids = await document_manager.get_vector_store_ids_for_agent(
            workspace_id, None
        )
        
        return {
            "workspace_id": workspace_id,
            "vector_store_ids": vector_store_ids,
            "count": len(vector_store_ids)
        }
        
    except Exception as e:
        logger.error(f"Failed to get vector stores: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get vector stores: {str(e)}"
        )