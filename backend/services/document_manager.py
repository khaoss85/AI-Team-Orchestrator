#!/usr/bin/env python3
"""
Document Management Service
Handles file uploads, vector store management, and document sharing
"""

import os
import logging
import asyncio
import json
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4, UUID
import mimetypes
import hashlib

from openai import OpenAI
from database import get_supabase_client
from models import AgentStatus
from services.pdf_content_extractor import pdf_extractor, PDFContent

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
    extracted_text: Optional[str] = None  # Full extracted text content
    text_chunks: Optional[List[Dict[str, Any]]] = None  # Chunked text for retrieval
    extraction_confidence: Optional[float] = None  # Confidence in extraction quality
    extraction_method: Optional[str] = None  # Method used for extraction
    page_count: Optional[int] = None  # Number of pages in document
    extraction_timestamp: Optional[datetime] = None  # When extraction happened
    created_at: Optional[datetime] = None  # Database creation timestamp
    updated_at: Optional[datetime] = None  # Database update timestamp

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        # Convert string timestamps to datetime if needed
        if isinstance(self.upload_date, str):
            from dateutil import parser
            self.upload_date = parser.parse(self.upload_date)
        if isinstance(self.extraction_timestamp, str):
            from dateutil import parser
            self.extraction_timestamp = parser.parse(self.extraction_timestamp)
        if isinstance(self.created_at, str):
            from dateutil import parser
            self.created_at = parser.parse(self.created_at)
        if isinstance(self.updated_at, str):
            from dateutil import parser
            self.updated_at = parser.parse(self.updated_at)

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
        self.supabase = get_supabase_client()
        
        # Initialize OpenAI client for file operations (SDK NATIVE)
        try:
            self.openai_client = OpenAI()
            logger.info("✅ SDK COMPLIANT: OpenAI client initialized for document management")
        except Exception as e:
            logger.warning(f"OpenAI client not available: {e}")
            self.openai_client = None
    
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
            # Parse the existing data properly
            existing_doc = existing.data[0]
            # Handle extracted_text and text_chunks which might be stored as JSON strings
            if 'extracted_text' in existing_doc and existing_doc['extracted_text']:
                existing_doc['extracted_text'] = existing_doc['extracted_text']
            if 'text_chunks' in existing_doc and existing_doc['text_chunks']:
                if isinstance(existing_doc['text_chunks'], str):
                    try:
                        existing_doc['text_chunks'] = json.loads(existing_doc['text_chunks'])
                    except:
                        existing_doc['text_chunks'] = None
            return DocumentMetadata(**existing_doc)
        
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            mime_type = "application/octet-stream"
        
        # Extract content if PDF
        extracted_text = None
        text_chunks = None
        extraction_confidence = None
        extraction_method = None
        page_count = None
        
        if mime_type == "application/pdf" or filename.lower().endswith('.pdf'):
            logger.info(f"📄 Extracting content from PDF: {filename}")
            try:
                pdf_content = await pdf_extractor.extract_content(
                    file_content=file_content,
                    filename=filename,
                    chunk_size=1000,
                    overlap=200
                )
                
                if pdf_content:
                    extracted_text = pdf_content.text
                    text_chunks = pdf_content.chunks
                    extraction_confidence = pdf_content.confidence
                    extraction_method = pdf_content.extraction_method
                    page_count = pdf_content.page_count
                    logger.info(f"✅ Extracted {len(extracted_text)} chars from PDF with {extraction_confidence:.0%} confidence")
                    
                    # Add extraction info to description
                    extraction_info = f" [Extracted: {len(extracted_text)} chars, {len(text_chunks)} chunks]"
                    if description:
                        description = description + extraction_info
                    else:
                        description = f"PDF document{extraction_info}"
            except Exception as e:
                logger.error(f"PDF extraction failed: {e}")
                # Continue with upload even if extraction fails
        
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
        
        # Add file to vector store using native OpenAI SDK
        try:
            # ✅ SDK COMPLIANT: Use native vector store file creation
            vector_store_file = self.openai_client.beta.vector_stores.files.create(
                vector_store_id=vector_store_id,
                file_id=openai_file.id
            )
            logger.info(f"✅ SDK COMPLIANT: File added to vector store: {vector_store_id}, file status: {vector_store_file.status}")
            
            # Wait for file processing to complete using native SDK
            import time
            max_wait = 30  # Wait max 30 seconds
            waited = 0
            while vector_store_file.status == "in_progress" and waited < max_wait:
                time.sleep(2)
                waited += 2
                
                # ✅ SDK COMPLIANT: Check status using native SDK
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
            file_hash=file_hash,
            extracted_text=extracted_text,
            text_chunks=text_chunks,
            extraction_confidence=extraction_confidence,
            extraction_method=extraction_method,
            page_count=page_count
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
            "file_hash": file_hash,
            "extracted_text": extracted_text[:5000] if extracted_text else None,  # Store first 5000 chars
            "text_chunks": json.dumps(text_chunks[:10]) if text_chunks else None,  # Store first 10 chunks as JSON
            "extraction_confidence": extraction_confidence,
            "extraction_method": extraction_method,
            # "page_count": page_count  # TODO: Re-enable after migration 017 is applied
        }
        
        # TODO: TEMPORARY FIX - Remove page_count until migration 017 is applied
        # After running: ALTER TABLE workspace_documents ADD COLUMN page_count INTEGER;
        # Uncomment the page_count line above
        
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
        
        # Create new vector store using native OpenAI SDK
        try:
            store_name = f"workspace-{workspace_id}-{scope}"
            
            # ✅ SDK COMPLIANT: Create vector store using native SDK
            vector_store = self.openai_client.beta.vector_stores.create(
                name=store_name,
                expires_after={
                    "anchor": "last_active_at",
                    "days": 365
                }
            )
            vector_store_id = vector_store.id
            
            # Save to database
            store_data = {
                "id": str(uuid4()),
                "workspace_id": workspace_id,
                "openai_vector_store_id": vector_store_id,
                "name": store_name,
                "scope": scope,
                "file_count": 0,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
            
            self.supabase.table("workspace_vector_stores").insert(store_data).execute()
            
            logger.info(f"✅ SDK COMPLIANT: Created vector store: {vector_store_id}")
            return vector_store_id
            
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
    
    async def retrieve_document(
        self, 
        document_id: str, 
        workspace_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a document's content for viewing"""
        
        logger.info(f"Attempting to retrieve document: {document_id} from workspace: {workspace_id}")
        
        # Get document metadata from database
        doc_result = self.supabase.table("workspace_documents")\
            .select("*")\
            .eq("id", document_id)\
            .eq("workspace_id", workspace_id)\
            .execute()
        
        if not doc_result.data:
            logger.warning(f"Document not found in database: {document_id} for workspace: {workspace_id}")
            return None
        
        doc_data = doc_result.data[0]
        openai_file_id = doc_data.get("openai_file_id")
        
        logger.info(f"Found document metadata: filename={doc_data.get('filename')}, openai_file_id={openai_file_id}")
        
        if not openai_file_id:
            logger.error(f"No OpenAI file ID for document: {document_id}")
            return None
        
        try:
            # Since files with purpose "assistants" can't be downloaded directly,
            # we need to use a different approach. For now, we'll return the original
            # uploaded content if we still have it, or provide a placeholder.
            
            # Try to download using the content endpoint (this might fail for assistant files)
            logger.info(f"Attempting to retrieve content from OpenAI for file_id: {openai_file_id}")
            
            # For assistant files, we can't download them directly.
            # As a workaround, we'll return a placeholder or the cached content.
            # In a production system, you might want to store the original content separately.
            
            # Check if we can get file metadata at least
            try:
                file_obj = self.openai_client.files.retrieve(openai_file_id)
                logger.info(f"File metadata: filename={file_obj.filename}, bytes={file_obj.bytes}, purpose={file_obj.purpose}")
                
                # For assistant files, we can't download the content directly
                # Return a message explaining this limitation
                if file_obj.purpose == "assistants":
                    # Create a placeholder content explaining the limitation
                    placeholder_message = f"""This document was uploaded to OpenAI for assistant usage.
                    
File Information:
- Filename: {doc_data.get('filename', 'Unknown')}
- Size: {doc_data.get('file_size', 0)} bytes
- Type: {doc_data.get('mime_type', 'Unknown')}
- Uploaded: {doc_data.get('upload_date', 'Unknown')}
- Description: {doc_data.get('description', 'No description')}

Note: OpenAI does not allow direct download of files uploaded with purpose 'assistants'.
To view the original content, you would need to re-upload the file or store it separately."""
                    
                    content_bytes = placeholder_message.encode('utf-8')
                    
                    # Override mime type to text/plain for the placeholder
                    mime_type = "text/plain"
                else:
                    # Try to download for other file purposes
                    file_content = self.openai_client.files.content(openai_file_id)
                    content_bytes = file_content.read()
                    mime_type = doc_data.get("mime_type", "application/octet-stream")
                    
            except Exception as e:
                logger.warning(f"Could not retrieve file metadata: {e}")
                # Return a basic error message
                error_message = f"Unable to retrieve document content: {str(e)}"
                content_bytes = error_message.encode('utf-8')
                mime_type = "text/plain"
            
            logger.info(f"Returning {len(content_bytes)} bytes for document {document_id}")
            
            # Return document data with content and metadata
            return {
                "content": content_bytes,
                "metadata": {
                    "id": doc_data["id"],
                    "filename": doc_data["filename"],
                    "mime_type": mime_type,
                    "file_size": len(content_bytes),
                    "upload_date": doc_data.get("upload_date"),
                    "sharing_scope": doc_data.get("sharing_scope", "team"),
                    "description": doc_data.get("description"),
                    "tags": doc_data.get("tags", [])
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to retrieve document from OpenAI: {e}")
            return None
    
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
            # ✅ SDK COMPLIANT: Remove from vector store using native SDK
            if doc_data.get("vector_store_id") and doc_data.get("openai_file_id"):
                deleted_vs_file = self.openai_client.beta.vector_stores.files.delete(
                    vector_store_id=doc_data['vector_store_id'],
                    file_id=doc_data['openai_file_id']
                )
                logger.info(f"✅ SDK COMPLIANT: Removed file from vector store: {deleted_vs_file.deleted}")
            
            # ✅ SDK COMPLIANT: Delete OpenAI file using native SDK
            if doc_data.get("openai_file_id"):
                deleted_file = self.openai_client.files.delete(doc_data["openai_file_id"])
                logger.info(f"✅ SDK COMPLIANT: Deleted OpenAI file: {deleted_file.deleted}")
            
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