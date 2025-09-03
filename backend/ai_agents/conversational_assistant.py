#!/usr/bin/env python3
"""
Conversational Assistant using OpenAI Assistants API
Provides native RAG capabilities through vector search
"""

import os
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from pydantic import BaseModel
from database import get_supabase_client
from services.openai_assistant_manager import assistant_manager, MessageResponse
from utils.context_manager import get_workspace_context

# Import shared conversation response model
from ai_agents.conversation_models import ConversationResponse

logger = logging.getLogger(__name__)

class ConversationalAssistant:
    """
    Enhanced conversational agent using OpenAI Assistants API
    
    Features:
    - Native file_search through Assistants API
    - Persistent conversation threads
    - Automatic vector store attachment
    - Tool execution through OpenAI
    - Document citation and references
    """
    
    def __init__(self, workspace_id: str, chat_id: str = "general"):
        """
        Initialize the conversational assistant
        
        Args:
            workspace_id: The workspace identifier
            chat_id: The chat/conversation identifier
        """
        self.workspace_id = workspace_id
        self.chat_id = chat_id
        self.assistant = None
        self.thread_id = None
        self.context = None
        self.supabase = get_supabase_client()
        
        logger.info(f"Initializing ConversationalAssistant for workspace {workspace_id}")
    
    async def initialize(self):
        """
        Initialize assistant and thread (async initialization)
        Must be called before processing messages
        """
        try:
            # Get or create assistant for workspace
            self.assistant = await assistant_manager.get_or_create_assistant(self.workspace_id)
            logger.info(f"Assistant initialized: {self.assistant['id']}")
            
            # Get or create thread
            self.thread_id = await assistant_manager.get_or_create_thread(self.workspace_id)
            logger.info(f"Thread initialized: {self.thread_id}")
            
            # Load workspace context for additional information
            self.context = await get_workspace_context(self.workspace_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize assistant: {e}")
            raise
    
    async def process_message(
        self, 
        user_message: str, 
        message_id: str = None,
        thinking_callback=None
    ) -> ConversationResponse:
        """
        Process user message through OpenAI Assistants API
        
        Args:
            user_message: The user's message
            message_id: Optional message identifier
            thinking_callback: Optional callback for thinking process updates
            
        Returns:
            ConversationResponse with assistant's reply and metadata
        """
        try:
            # Ensure initialization
            if not self.assistant or not self.thread_id:
                await self.initialize()
            
            # Broadcast thinking step if callback provided
            if thinking_callback:
                await thinking_callback({
                    "type": "thinking_step",
                    "step": "assistant_processing",
                    "title": "🤖 Processing with OpenAI Assistant",
                    "description": "Sending message to AI assistant with document search capabilities",
                    "status": "in_progress"
                })
            
            # Check if user is asking about documents
            if self._is_document_query(user_message):
                # Add context about available documents
                doc_context = await self._get_document_context()
                if doc_context:
                    enhanced_message = f"{user_message}\n\nContext: {doc_context}"
                else:
                    enhanced_message = user_message
            else:
                enhanced_message = user_message
            
            # Send message and create run
            run = await assistant_manager.send_message(
                thread_id=self.thread_id,
                message=enhanced_message
            )
            
            if thinking_callback:
                await thinking_callback({
                    "type": "thinking_step",
                    "step": "document_search",
                    "title": "📄 Searching Documents",
                    "description": "Using vector search to find relevant information in uploaded files",
                    "status": "in_progress"
                })
            
            # Process the run and get response
            response = await assistant_manager.process_run(
                thread_id=self.thread_id,
                run_id=run["id"]
            )
            
            if thinking_callback:
                if response.citations:
                    await thinking_callback({
                        "type": "thinking_step",
                        "step": "document_search",
                        "title": "📄 Documents Found",
                        "description": f"Found {len(response.citations)} relevant document references",
                        "status": "completed"
                    })
                else:
                    await thinking_callback({
                        "type": "thinking_step",
                        "step": "document_search",
                        "title": "📄 Search Complete",
                        "description": "Document search completed",
                        "status": "completed"
                    })
            
            # Store conversation in database
            await self._store_conversation(user_message, response.content, message_id, response)
            
            # Extract suggested actions based on response
            suggested_actions = self._extract_suggested_actions(response.content)
            
            # Format citations for display
            formatted_citations = None
            if response.citations:
                formatted_citations = await self._format_citations(response.citations)
            
            return ConversationResponse(
                message=response.content,
                message_type=response.message_type,
                artifacts=None,
                actions_performed=None,
                needs_confirmation=False,
                suggested_actions=suggested_actions,
                citations=formatted_citations,
                thread_id=response.thread_id,
                run_id=response.run_id
            )
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            
            # Fallback response
            return ConversationResponse(
                message=f"I encountered an error processing your request: {str(e)}. Please try again.",
                message_type="error"
            )
    
    async def process_message_with_thinking(
        self, 
        user_message: str, 
        message_id: str = None,
        thinking_callback=None
    ) -> ConversationResponse:
        """
        Process message with visible thinking steps
        
        This method provides the same functionality as process_message
        but with enhanced thinking process visibility
        """
        # Store thinking steps for later reference
        self._current_thinking_steps = []
        
        # Create wrapper for thinking callback
        async def storing_thinking_callback(step_data):
            enriched_step = {
                **step_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "workspace_id": self.workspace_id,
                "chat_id": self.chat_id
            }
            self._current_thinking_steps.append(enriched_step)
            
            # Broadcast via WebSocket if available
            try:
                from routes.websocket import broadcast_thinking_step
                await broadcast_thinking_step(self.workspace_id, enriched_step)
            except Exception as e:
                logger.debug(f"Could not broadcast thinking step: {e}")
            
            # Call original callback
            if thinking_callback:
                await thinking_callback(step_data)
        
        # Process with enhanced callback
        return await self.process_message(
            user_message, 
            message_id, 
            storing_thinking_callback
        )
    
    def _is_document_query(self, message: str) -> bool:
        """Check if the message is asking about documents"""
        doc_keywords = [
            "document", "file", "pdf", "upload", "search",
            "find", "look for", "content", "written", "says",
            "mentioned", "reference", "source", "citation"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in doc_keywords)
    
    async def _get_document_context(self) -> Optional[str]:
        """Get context about available documents"""
        try:
            # Get list of documents in workspace
            documents = self.supabase.table("workspace_documents")\
                .select("filename, description, upload_date")\
                .eq("workspace_id", self.workspace_id)\
                .execute()
            
            if documents.data:
                doc_list = []
                for doc in documents.data[:5]:  # Limit to 5 most recent
                    desc = doc.get("description", "No description")
                    doc_list.append(f"- {doc['filename']}: {desc}")
                
                return f"Available documents in workspace:\n" + "\n".join(doc_list)
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get document context: {e}")
            return None
    
    async def _format_citations(self, citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format citations with file information"""
        formatted = []
        
        for citation in citations:
            try:
                # Look up file information
                file_info = self.supabase.table("workspace_documents")\
                    .select("filename, description")\
                    .eq("openai_file_id", citation.get("file_id"))\
                    .execute()
                
                if file_info.data:
                    formatted.append({
                        "filename": file_info.data[0]["filename"],
                        "description": file_info.data[0].get("description"),
                        "quote": citation.get("quote", ""),
                        "file_id": citation.get("file_id")
                    })
                else:
                    formatted.append(citation)
                    
            except Exception as e:
                logger.warning(f"Failed to format citation: {e}")
                formatted.append(citation)
        
        return formatted
    
    def _extract_suggested_actions(self, response_text: str) -> Optional[List[Dict[str, Any]]]:
        """Extract suggested actions from response"""
        actions = []
        
        # Check for document-related suggestions
        if "upload" in response_text.lower() or "document" in response_text.lower():
            actions.append({
                "id": "upload_document",
                "label": "📄 Upload Document",
                "description": "Add more documents to the knowledge base",
                "icon": "📄"
            })
        
        # Check for search-related suggestions
        if "search" in response_text.lower() or "find" in response_text.lower():
            actions.append({
                "id": "search_documents",
                "label": "🔍 Search Documents",
                "description": "Search through uploaded documents",
                "icon": "🔍"
            })
        
        # Check for project status suggestions
        if "status" in response_text.lower() or "progress" in response_text.lower():
            actions.append({
                "id": "show_project_status",
                "label": "📊 Show Project Status",
                "description": "View current project metrics and progress",
                "icon": "📊"
            })
        
        return actions if actions else None
    
    async def _store_conversation(
        self, 
        user_message: str, 
        ai_response: str, 
        message_id: str = None,
        response_obj: MessageResponse = None
    ):
        """Store conversation in database"""
        try:
            import uuid
            conversation_identifier = f"{self.workspace_id}_{self.chat_id}"
            conversation_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, conversation_identifier))
            
            # Ensure conversation exists
            try:
                existing = self.supabase.table("conversations")\
                    .select("id")\
                    .eq("id", conversation_uuid)\
                    .execute()
                
                if not existing.data:
                    self.supabase.table("conversations").insert({
                        "id": conversation_uuid,
                        "workspace_id": self.workspace_id,
                        "chat_id": self.chat_id,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }).execute()
                    
            except Exception as e:
                logger.warning(f"Could not create/check conversation: {e}")
            
            # Store user message
            if not message_id:
                message_id = f"msg_{int(datetime.now().timestamp() * 1000)}_user"
            
            user_data = {
                "conversation_identifier": conversation_identifier,
                "conversation_id": conversation_uuid,
                "message_id": message_id,
                "role": "user",
                "content": user_message,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            self.supabase.table("conversation_messages").insert(user_data).execute()
            
            # Store AI response with metadata
            ai_metadata = {
                "thread_id": response_obj.thread_id if response_obj else None,
                "run_id": response_obj.run_id if response_obj else None,
                "citations": response_obj.citations if response_obj else None,
                "assistant_id": self.assistant["id"] if self.assistant else None
            }
            
            if hasattr(self, '_current_thinking_steps'):
                ai_metadata['thinking_steps'] = self._current_thinking_steps
            
            ai_data = {
                "conversation_identifier": conversation_identifier,
                "conversation_id": conversation_uuid,
                "message_id": f"{message_id}_response",
                "role": "assistant",
                "content": ai_response,
                "metadata": json.dumps(ai_metadata),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            self.supabase.table("conversation_messages").insert(ai_data).execute()
            
            logger.info(f"Conversation stored successfully for {conversation_identifier}")
            
        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")
    
    async def upload_document(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Upload a document to the assistant's vector store
        
        Args:
            file_content: The file content as bytes
            filename: The name of the file
            
        Returns:
            Upload result with file information
        """
        try:
            from services.document_manager import document_manager
            
            # Upload document through document manager
            doc_metadata = await document_manager.upload_document(
                workspace_id=self.workspace_id,
                file_content=file_content,
                filename=filename,
                uploaded_by=f"assistant_{self.chat_id}",
                sharing_scope="team"
            )
            
            # Update assistant's vector stores
            if self.assistant:
                vector_store_ids = await document_manager.get_vector_store_ids_for_agent(
                    self.workspace_id
                )
                
                await assistant_manager.update_assistant_vector_stores(
                    self.assistant["id"],
                    vector_store_ids
                )
            
            return {
                "success": True,
                "message": f"Document '{filename}' uploaded successfully",
                "document_id": doc_metadata.id,
                "file_size": doc_metadata.file_size,
                "extracted_text_length": len(doc_metadata.extracted_text) if doc_metadata.extracted_text else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to upload document: {e}")
            return {
                "success": False,
                "message": f"Failed to upload document: {str(e)}"
            }
    
    async def search_documents(self, query: str) -> str:
        """
        Search documents using the assistant
        
        Args:
            query: The search query
            
        Returns:
            Search results as formatted text
        """
        try:
            # Use the assistant to search documents
            search_prompt = f"""Search for information about: {query}
            
            Please search through all available documents and provide:
            1. Relevant information found
            2. Source documents
            3. Key quotes or excerpts
            """
            
            response = await self.process_message(search_prompt)
            return response.message
            
        except Exception as e:
            logger.error(f"Document search failed: {e}")
            return f"Search failed: {str(e)}"