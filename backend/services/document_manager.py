#!/usr/bin/env python3
"""
Document Management Service
Handles file uploads, vector store management, and document sharing
"""

import os
import logging
import asyncio
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4, UUID
import mimetypes
import hashlib

from openai import OpenAI
from database import get_supabase_client
from models import AgentStatus

logger = logging.getLogger(__name__)

@dataclass
class DocumentMetadata:
    """Metadata for uploaded documents"""
    id: str
    workspace_id: str
    filename: str
    file_size: int
    mime_type: str
    upload_date: datetime
    uploaded_by: str  # chat or agent_id
    sharing_scope: str  # "team" or specific agent_id
    vector_store_id: Optional[str] = None
    openai_file_id: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = None
    file_hash: Optional[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass
class VectorStoreInfo:
    """Information about OpenAI vector stores"""
    id: str
    workspace_id: str
    name: str
    scope: str  # "team" or agent_id
    file_count: int
    created_at: datetime
    last_updated: datetime

class DocumentManager:
    """Manages document upload, storage, and vector store operations"""
    
    def __init__(self):
        self.openai_client = None
        self.supabase = get_supabase_client()
        
        # Initialize OpenAI client with Beta headers for Vector Stores
        try:
            self.openai_client = OpenAI(
                default_headers={"OpenAI-Beta": "assistants=v2"}
            )
            logger.info("OpenAI client initialized for document management with Beta headers")
        except Exception as e:
            logger.warning(f"OpenAI client not available: {e}")
    
    async def upload_document(
        self,
        workspace_id: str,
        file_content: bytes,
        filename: str,
        uploaded_by: str = "chat",
        sharing_scope: str = "team",
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> DocumentMetadata:
        """Upload a document and create vector store entry"""
        
        if not self.openai_client:
            raise Exception("OpenAI client not available for document upload")
        
        # Generate file hash for deduplication
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # Check for existing file
        existing = self.supabase.table("workspace_documents")\
            .select("*")\
            .eq("workspace_id", workspace_id)\
            .eq("file_hash", file_hash)\
            .execute()
        
        if existing.data:
            logger.info(f"Document already exists: {filename}")
            return DocumentMetadata(**existing.data[0])
        
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            mime_type = "application/octet-stream"
        
        # Upload to OpenAI
        try:
            # Create temporary file for OpenAI upload
            temp_file_path = f"/tmp/{uuid4()}-{filename}"
            with open(temp_file_path, "wb") as f:
                f.write(file_content)
            
            # Upload to OpenAI Files API
            with open(temp_file_path, "rb") as f:
                openai_file = self.openai_client.files.create(
                    file=f,
                    purpose="assistants"
                )
            
            # Clean up temp file
            os.unlink(temp_file_path)
            
            logger.info(f"File uploaded to OpenAI: {openai_file.id}")
            
        except Exception as e:
            logger.error(f"Failed to upload file to OpenAI: {e}")
            raise Exception(f"Document upload failed: {str(e)}")
        
        # Get or create vector store
        vector_store_id = await self._get_or_create_vector_store(
            workspace_id, sharing_scope
        )
        
        # Add file to vector store using real OpenAI API
        try:
            vector_store_file = self.openai_client.beta.vector_stores.files.create(
                vector_store_id=vector_store_id,
                file_id=openai_file.id
            )
            logger.info(f"File added to vector store: {vector_store_id}, file status: {vector_store_file.status}")
            
            # Wait for file processing to complete (optional)
            import time
            max_wait = 30  # Wait max 30 seconds
            waited = 0
            while vector_store_file.status == "in_progress" and waited < max_wait:
                time.sleep(2)
                waited += 2
                vector_store_file = self.openai_client.beta.vector_stores.files.retrieve(
                    vector_store_id=vector_store_id,
                    file_id=openai_file.id
                )
                logger.info(f"File processing status: {vector_store_file.status}")
            
        except Exception as e:
            logger.error(f"Failed to add file to vector store: {e}")
            # Continue anyway, the document is still uploaded to OpenAI
        
        # Create document metadata
        doc_metadata = DocumentMetadata(
            id=str(uuid4()),
            workspace_id=workspace_id,
            filename=filename,
            file_size=len(file_content),
            mime_type=mime_type,
            upload_date=datetime.now(),
            uploaded_by=uploaded_by,
            sharing_scope=sharing_scope,
            vector_store_id=vector_store_id,
            openai_file_id=openai_file.id,
            description=description,
            tags=tags or [],
            file_hash=file_hash
        )
        
        # Save to database
        doc_data = {
            "id": doc_metadata.id,
            "workspace_id": workspace_id,
            "filename": filename,
            "file_size": len(file_content),
            "mime_type": mime_type,
            "upload_date": doc_metadata.upload_date.isoformat(),
            "uploaded_by": uploaded_by,
            "sharing_scope": sharing_scope,
            "vector_store_id": vector_store_id,
            "openai_file_id": openai_file.id,
            "description": description,
            "tags": tags or [],
            "file_hash": file_hash
        }
        
        result = self.supabase.table("workspace_documents").insert(doc_data).execute()
        
        if not result.data:
            raise Exception("Failed to save document metadata")
        
        logger.info(f"Document uploaded successfully: {filename}")
        return doc_metadata
    
    async def _get_or_create_vector_store(
        self, 
        workspace_id: str, 
        scope: str
    ) -> str:
        """Get existing or create new vector store for scope"""
        
        # Check for existing vector store
        existing = self.supabase.table("workspace_vector_stores")\
            .select("*")\
            .eq("workspace_id", workspace_id)\
            .eq("scope", scope)\
            .execute()
        
        if existing.data:
            return existing.data[0]["openai_vector_store_id"]
        
        # Create new vector store using real OpenAI API
        try:
            store_name = f"workspace-{workspace_id}-{scope}"
            
            # Create vector store with OpenAI Beta API
            vector_store = self.openai_client.beta.vector_stores.create(
                name=store_name,
                expires_after={
                    "anchor": "last_active_at",
                    "days": 365  # Keep for 1 year
                }
            )
            
            # Save to database
            store_data = {
                "id": str(uuid4()),
                "workspace_id": workspace_id,
                "openai_vector_store_id": vector_store.id,
                "name": store_name,
                "scope": scope,
                "file_count": 0,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
            
            self.supabase.table("workspace_vector_stores").insert(store_data).execute()
            
            logger.info(f"Created real vector store: {vector_store.id}")
            return vector_store.id
            
        except Exception as e:
            logger.error(f"Failed to create vector store: {e}")
            raise Exception(f"Vector store creation failed: {str(e)}")
    
    async def list_documents(
        self, 
        workspace_id: str, 
        scope: Optional[str] = None
    ) -> List[DocumentMetadata]:
        """List documents in workspace, optionally filtered by scope"""
        
        query = self.supabase.table("workspace_documents")\
            .select("*")\
            .eq("workspace_id", workspace_id)
        
        if scope:
            query = query.eq("sharing_scope", scope)
        
        result = query.execute()
        
        documents = []
        for doc_data in result.data:
            # Convert upload_date string back to datetime
            doc_data["upload_date"] = datetime.fromisoformat(doc_data["upload_date"])
            # Remove extra fields that aren't in DocumentMetadata
            doc_data.pop("created_at", None)
            doc_data.pop("updated_at", None)
            documents.append(DocumentMetadata(**doc_data))
        
        return documents
    
    async def delete_document(self, document_id: str, workspace_id: str) -> bool:
        """Delete document from vector store and database"""
        
        # Get document metadata
        doc_result = self.supabase.table("workspace_documents")\
            .select("*")\
            .eq("id", document_id)\
            .eq("workspace_id", workspace_id)\
            .execute()
        
        if not doc_result.data:
            logger.warning(f"Document not found: {document_id}")
            return False
        
        doc_data = doc_result.data[0]
        
        try:
            # Remove from vector store using real OpenAI API
            if doc_data.get("vector_store_id") and doc_data.get("openai_file_id"):
                deleted_vs_file = self.openai_client.beta.vector_stores.files.delete(
                    vector_store_id=doc_data["vector_store_id"],
                    file_id=doc_data["openai_file_id"]
                )
                logger.info(f"Removed file from vector store: {deleted_vs_file.deleted}")
            
            # Delete OpenAI file
            if doc_data.get("openai_file_id"):
                deleted_file = self.openai_client.files.delete(doc_data["openai_file_id"])
                logger.info(f"Deleted OpenAI file: {deleted_file.deleted}")
            
        except Exception as e:
            logger.error(f"Failed to delete from OpenAI: {e}")
            # Continue with database deletion
        
        # Delete from database
        self.supabase.table("workspace_documents")\
            .delete()\
            .eq("id", document_id)\
            .execute()
        
        logger.info(f"Document deleted: {document_id}")
        return True
    
    async def get_vector_store_ids_for_agent(
        self, 
        workspace_id: str, 
        agent_id: Optional[str] = None
    ) -> List[str]:
        """Get vector store IDs that an agent should have access to"""
        
        # Get team-wide vector stores
        team_stores = self.supabase.table("workspace_vector_stores")\
            .select("openai_vector_store_id")\
            .eq("workspace_id", workspace_id)\
            .eq("scope", "team")\
            .execute()
        
        vector_store_ids = [store["openai_vector_store_id"] for store in team_stores.data]
        
        # Add agent-specific stores if agent_id provided
        if agent_id:
            agent_stores = self.supabase.table("workspace_vector_stores")\
                .select("openai_vector_store_id")\
                .eq("workspace_id", workspace_id)\
                .eq("scope", agent_id)\
                .execute()
            
            vector_store_ids.extend(
                store["openai_vector_store_id"] for store in agent_stores.data
            )
        
        return vector_store_ids

# Global instance
document_manager = DocumentManager()