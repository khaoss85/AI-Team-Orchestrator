#!/usr/bin/env python3
"""
Document Management Tools
Tools for uploading, managing, and searching documents in workspaces
"""

import logging
import base64
import mimetypes
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from services.document_manager import document_manager, DocumentMetadata

logger = logging.getLogger(__name__)

@dataclass
class DocumentUploadTool:
    """Tool for uploading documents to workspace"""
    name: str = "upload_document"
    description: str = "Upload a document to the workspace for team access"
    
    async def execute(
        self,
        file_data: str,  # base64 encoded file content
        filename: str,
        sharing_scope: str = "team",  # "team" or specific agent_id
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Upload document and add to vector store"""
        
        try:
            workspace_id = context.get("workspace_id") if context else None
            if not workspace_id:
                return "❌ Error: workspace_id required for document upload"
            
            # Decode base64 file content
            try:
                file_content = base64.b64decode(file_data)
            except Exception as e:
                return f"❌ Error decoding file data: {str(e)}"
            
            # Validate file size (limit to 5MB for chat uploads to avoid token limits)
            max_size_mb = 5
            max_size_bytes = max_size_mb * 1024 * 1024
            if len(file_content) > max_size_bytes:
                return f"❌ Error: File size ({len(file_content) / (1024*1024):.1f}MB) exceeds {max_size_mb}MB limit for chat uploads. Please use the API endpoint for larger files."
            
            # Validate filename
            if not filename or filename.startswith('.'):
                return "❌ Error: Invalid filename"
            
            # Validate sharing scope
            if sharing_scope not in ["team"] and not sharing_scope.startswith("agent-"):
                return "❌ Error: sharing_scope must be 'team' or 'agent-{agent_id}'"
            
            # Upload document
            doc_metadata = await document_manager.upload_document(
                workspace_id=workspace_id,
                file_content=file_content,
                filename=filename,
                uploaded_by="chat",
                sharing_scope=sharing_scope,
                description=description,
                tags=tags
            )
            
            # Create response
            scope_text = "team" if sharing_scope == "team" else f"agent {sharing_scope}"
            size_mb = round(doc_metadata.file_size / (1024 * 1024), 2)
            
            return f"""✅ Document uploaded successfully!
            
📄 **{doc_metadata.filename}**
📊 Size: {size_mb}MB
🔍 Type: {doc_metadata.mime_type}
👥 Shared with: {scope_text}
🆔 Document ID: {doc_metadata.id}

The document is now available for search by all agents in the workspace."""
            
        except Exception as e:
            logger.error(f"Document upload failed: {e}")
            return f"❌ Document upload failed: {str(e)}"

@dataclass
class DocumentListTool:
    """Tool for listing documents in workspace"""
    name: str = "list_documents"
    description: str = "List all documents uploaded to the workspace"
    
    async def execute(
        self,
        scope: Optional[str] = None,  # Filter by scope: "team" or agent_id
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """List documents in workspace"""
        
        try:
            workspace_id = context.get("workspace_id") if context else None
            if not workspace_id:
                return "❌ Error: workspace_id required"
            
            documents = await document_manager.list_documents(workspace_id, scope)
            
            if not documents:
                return "📁 No documents found in this workspace."
            
            # Group by scope
            team_docs = [doc for doc in documents if doc.sharing_scope == "team"]
            agent_docs = [doc for doc in documents if doc.sharing_scope != "team"]
            
            response_parts = []
            
            if team_docs:
                response_parts.append("👥 **Team Documents**:")
                for doc in team_docs:
                    size_mb = round(doc.file_size / (1024 * 1024), 2)
                    upload_date = doc.upload_date.strftime("%Y-%m-%d %H:%M")
                    response_parts.append(
                        f"  📄 **{doc.filename}** ({size_mb}MB) - {upload_date}"
                    )
                    if doc.description:
                        response_parts.append(f"     📝 {doc.description}")
                    if doc.tags:
                        response_parts.append(f"     🏷️ {', '.join(doc.tags)}")
            
            if agent_docs:
                response_parts.append("\n🤖 **Agent-Specific Documents**:")
                for doc in agent_docs:
                    size_mb = round(doc.file_size / (1024 * 1024), 2)
                    upload_date = doc.upload_date.strftime("%Y-%m-%d %H:%M")
                    response_parts.append(
                        f"  📄 **{doc.filename}** ({size_mb}MB) - {doc.sharing_scope} - {upload_date}"
                    )
                    if doc.description:
                        response_parts.append(f"     📝 {doc.description}")
                    if doc.tags:
                        response_parts.append(f"     🏷️ {', '.join(doc.tags)}")
            
            response_parts.append(f"\n📊 **Total**: {len(documents)} documents")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            logger.error(f"Document listing failed: {e}")
            return f"❌ Document listing failed: {str(e)}"

@dataclass
class DocumentDeleteTool:
    """Tool for deleting documents from workspace"""
    name: str = "delete_document"
    description: str = "Delete a document from the workspace"
    
    async def execute(
        self,
        document_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Delete document from workspace"""
        
        try:
            workspace_id = context.get("workspace_id") if context else None
            if not workspace_id:
                return "❌ Error: workspace_id required"
            
            if not document_id:
                return "❌ Error: document_id required"
            
            # Delete document
            success = await document_manager.delete_document(document_id, workspace_id)
            
            if success:
                return f"✅ Document deleted successfully (ID: {document_id})"
            else:
                return f"❌ Document not found or already deleted (ID: {document_id})"
                
        except Exception as e:
            logger.error(f"Document deletion failed: {e}")
            return f"❌ Document deletion failed: {str(e)}"

@dataclass
class DocumentSearchTool:
    """Enhanced tool for searching documents using OpenAI vector search"""
    name: str = "search_documents"
    description: str = "Search through uploaded documents using AI-powered search"
    
    async def execute(
        self,
        query: str,
        max_results: int = 5,
        agent_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Search documents using OpenAI vector search"""
        
        try:
            workspace_id = context.get("workspace_id") if context else None
            if not workspace_id:
                return "❌ Error: workspace_id required"
            
            if not query:
                return "❌ Error: search query required"
            
            # Get vector store IDs for this agent/workspace
            vector_store_ids = await document_manager.get_vector_store_ids_for_agent(
                workspace_id, agent_id
            )
            
            if not vector_store_ids:
                return "📁 No documents available for search. Upload documents first."
            
            # Use OpenAI vector search
            from tools.openai_sdk_tools import FileSearchTool
            
            file_search = FileSearchTool(
                vector_store_ids=vector_store_ids,
                max_num_results=max_results,
                include_search_results=True
            )
            
            # Execute search
            search_results = await file_search.execute(query, context)
            
            # Enhance results with document metadata
            documents = await document_manager.list_documents(workspace_id)
            doc_lookup = {doc.openai_file_id: doc for doc in documents if doc.openai_file_id}
            
            # Format enhanced results
            if "found" in search_results.lower():
                response_parts = [
                    f"🔍 **Search Results for**: \"{query}\"",
                    "",
                    search_results
                ]
                
                if doc_lookup:
                    response_parts.append("\n📄 **Available Documents**:")
                    for doc in documents[:5]:  # Show first 5 docs
                        response_parts.append(f"  • {doc.filename} ({doc.sharing_scope})")
                
                return "\n".join(response_parts)
            else:
                return search_results
                
        except Exception as e:
            logger.error(f"Document search failed: {e}")
            return f"❌ Document search failed: {str(e)}"

# Export all tools
document_tools = {
    "upload_document": DocumentUploadTool(),
    "list_documents": DocumentListTool(),
    "delete_document": DocumentDeleteTool(),
    "search_documents": DocumentSearchTool()
}