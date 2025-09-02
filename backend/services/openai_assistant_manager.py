#!/usr/bin/env python3
"""
OpenAI Assistant Manager Service
Manages OpenAI Assistants lifecycle for workspace-based RAG functionality
"""

import os
import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum

from openai import OpenAI
from database import get_supabase_client

logger = logging.getLogger(__name__)

class RunStatus(Enum):
    """OpenAI Run status enumeration"""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    REQUIRES_ACTION = "requires_action"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    FAILED = "failed"
    COMPLETED = "completed"
    EXPIRED = "expired"

@dataclass
class AssistantConfig:
    """Configuration for OpenAI Assistant"""
    name: str
    instructions: str
    model: str = "gpt-4-turbo-preview"
    temperature: float = 0.7
    max_tokens: int = 4096
    tools: List[Dict[str, Any]] = None
    file_search_max_results: int = 10
    
    def __post_init__(self):
        if self.tools is None:
            self.tools = [
                {"type": "file_search"},
                {"type": "code_interpreter"}
            ]

@dataclass
class MessageResponse:
    """Response from assistant message processing"""
    content: str
    message_type: str = "assistant"
    citations: Optional[List[Dict[str, Any]]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    thread_id: Optional[str] = None
    run_id: Optional[str] = None
    status: str = "completed"
    error: Optional[str] = None

class OpenAIAssistantManager:
    """
    Manages OpenAI Assistants lifecycle for workspace-based RAG
    
    Key responsibilities:
    - Create/update assistants per workspace
    - Manage assistant-vector store associations
    - Handle thread creation and message processing
    - Execute tools through Assistants API
    """
    
    def __init__(self):
        """Initialize the assistant manager"""
        self.client = OpenAI()
        self.supabase = get_supabase_client()
        
        # Configuration from environment
        self.default_model = os.getenv("OPENAI_ASSISTANT_MODEL", "gpt-4-turbo-preview")
        self.default_temperature = float(os.getenv("OPENAI_ASSISTANT_TEMPERATURE", "0.7"))
        self.default_max_tokens = int(os.getenv("OPENAI_ASSISTANT_MAX_TOKENS", "4096"))
        self.file_search_max_results = int(os.getenv("OPENAI_FILE_SEARCH_MAX_RESULTS", "10"))
        
        logger.info("OpenAI Assistant Manager initialized")
    
    async def get_or_create_assistant(
        self, 
        workspace_id: str,
        config: Optional[AssistantConfig] = None
    ) -> Dict[str, Any]:
        """
        Get existing assistant or create new one for workspace
        
        Args:
            workspace_id: The workspace identifier
            config: Optional assistant configuration
            
        Returns:
            Assistant object with id and configuration
        """
        try:
            # Check for existing assistant in database
            existing = self.supabase.table("workspace_assistants")\
                .select("*")\
                .eq("workspace_id", workspace_id)\
                .execute()
            
            if existing.data:
                assistant_id = existing.data[0]["assistant_id"]
                logger.info(f"Found existing assistant {assistant_id} for workspace {workspace_id}")
                
                # Retrieve assistant from OpenAI
                try:
                    assistant = self.client.beta.assistants.retrieve(assistant_id)
                    
                    # Update vector stores if needed
                    await self._sync_vector_stores(workspace_id, assistant_id)
                    
                    return {
                        "id": assistant.id,
                        "name": assistant.name,
                        "model": assistant.model,
                        "instructions": assistant.instructions,
                        "tools": assistant.tools,
                        "created_at": assistant.created_at
                    }
                except Exception as e:
                    logger.warning(f"Failed to retrieve assistant {assistant_id}: {e}")
                    # Assistant doesn't exist in OpenAI, create new one
            
            # Create new assistant
            if not config:
                config = self._get_default_config(workspace_id)
            
            # Get workspace information for context
            workspace_info = await self._get_workspace_info(workspace_id)
            
            # Create assistant with file_search tool
            assistant = self.client.beta.assistants.create(
                name=config.name,
                instructions=config.instructions.format(
                    workspace_name=workspace_info.get("name", "Unknown"),
                    workspace_goal=workspace_info.get("goal", "Not specified")
                ),
                model=config.model,
                tools=config.tools,
                temperature=config.temperature,
                tool_resources={
                    "file_search": {
                        "vector_store_ids": await self._get_vector_store_ids(workspace_id)
                    }
                }
            )
            
            # Register in database
            await self._register_assistant(workspace_id, assistant.id)
            
            logger.info(f"Created new assistant {assistant.id} for workspace {workspace_id}")
            
            return {
                "id": assistant.id,
                "name": assistant.name,
                "model": assistant.model,
                "instructions": assistant.instructions,
                "tools": assistant.tools,
                "created_at": assistant.created_at
            }
            
        except Exception as e:
            logger.error(f"Failed to get/create assistant: {e}")
            raise
    
    async def update_assistant_vector_stores(
        self, 
        assistant_id: str, 
        vector_store_ids: List[str]
    ) -> bool:
        """
        Update assistant with new vector store IDs
        
        Args:
            assistant_id: The assistant identifier
            vector_store_ids: List of vector store IDs to attach
            
        Returns:
            Success status
        """
        try:
            # Update assistant with vector stores
            self.client.beta.assistants.update(
                assistant_id,
                tool_resources={
                    "file_search": {
                        "vector_store_ids": vector_store_ids
                    }
                }
            )
            
            logger.info(f"Updated assistant {assistant_id} with {len(vector_store_ids)} vector stores")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update assistant vector stores: {e}")
            return False
    
    async def create_thread(
        self, 
        workspace_id: str,
        initial_messages: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Create a new conversation thread
        
        Args:
            workspace_id: The workspace identifier
            initial_messages: Optional initial messages for the thread
            
        Returns:
            Thread object with id
        """
        try:
            # Create thread with optional initial messages
            thread_params = {}
            if initial_messages:
                thread_params["messages"] = initial_messages
            
            thread = self.client.beta.threads.create(**thread_params)
            
            # Update database with thread ID
            self.supabase.table("workspace_assistants")\
                .update({"thread_id": thread.id, "last_updated": datetime.now(timezone.utc).isoformat()})\
                .eq("workspace_id", workspace_id)\
                .execute()
            
            logger.info(f"Created thread {thread.id} for workspace {workspace_id}")
            
            return {
                "id": thread.id,
                "created_at": thread.created_at,
                "metadata": thread.metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to create thread: {e}")
            raise
    
    async def send_message(
        self, 
        thread_id: str, 
        message: str,
        file_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send a message to a thread and create a run
        
        Args:
            thread_id: The thread identifier
            message: The user message
            file_ids: Optional file IDs to attach
            
        Returns:
            Run object with id and status
        """
        try:
            # Add message to thread
            message_params = {
                "thread_id": thread_id,
                "role": "user",
                "content": message
            }
            
            if file_ids:
                message_params["attachments"] = [
                    {"file_id": file_id, "tools": [{"type": "file_search"}]}
                    for file_id in file_ids
                ]
            
            thread_message = self.client.beta.threads.messages.create(**message_params)
            
            logger.info(f"Added message to thread {thread_id}")
            
            # Get assistant ID from thread's workspace
            assistant_id = await self._get_assistant_id_for_thread(thread_id)
            
            if not assistant_id:
                raise ValueError(f"No assistant found for thread {thread_id}")
            
            # Create run
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id
            )
            
            logger.info(f"Created run {run.id} for thread {thread_id}")
            
            return {
                "id": run.id,
                "thread_id": run.thread_id,
                "assistant_id": run.assistant_id,
                "status": run.status,
                "created_at": run.created_at
            }
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise
    
    async def process_run(
        self, 
        thread_id: str, 
        run_id: str,
        timeout: int = 60
    ) -> MessageResponse:
        """
        Process a run and get the response
        
        Args:
            thread_id: The thread identifier
            run_id: The run identifier
            timeout: Maximum time to wait for completion
            
        Returns:
            MessageResponse with assistant's reply
        """
        try:
            import time
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # Get run status
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run_id
                )
                
                logger.debug(f"Run {run_id} status: {run.status}")
                
                if run.status == RunStatus.COMPLETED.value:
                    # Get the assistant's response
                    messages = self.client.beta.threads.messages.list(
                        thread_id=thread_id,
                        order="desc",
                        limit=1
                    )
                    
                    if messages.data:
                        latest_message = messages.data[0]
                        
                        # Extract content and citations
                        content = ""
                        citations = []
                        
                        for content_item in latest_message.content:
                            if content_item.type == "text":
                                content += content_item.text.value
                                
                                # Extract citations if present
                                if hasattr(content_item.text, 'annotations'):
                                    for annotation in content_item.text.annotations:
                                        if annotation.type == "file_citation":
                                            citation_data = {
                                                "file_id": annotation.file_citation.file_id,
                                            }
                                            # Add quote if available (not always present)
                                            if hasattr(annotation.file_citation, 'quote'):
                                                citation_data["quote"] = annotation.file_citation.quote
                                            citations.append(citation_data)
                        
                        return MessageResponse(
                            content=content,
                            message_type="assistant",
                            citations=citations if citations else None,
                            thread_id=thread_id,
                            run_id=run_id,
                            status="completed"
                        )
                    
                elif run.status == RunStatus.REQUIRES_ACTION.value:
                    # Handle tool calls
                    tool_outputs = await self.handle_tool_calls(
                        run_id, 
                        run.required_action.submit_tool_outputs.tool_calls
                    )
                    
                    # Submit tool outputs
                    self.client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread_id,
                        run_id=run_id,
                        tool_outputs=tool_outputs
                    )
                    
                elif run.status in [RunStatus.FAILED.value, RunStatus.CANCELLED.value, RunStatus.EXPIRED.value]:
                    error_msg = f"Run {run_id} failed with status: {run.status}"
                    if run.last_error:
                        error_msg += f" - {run.last_error.message}"
                    
                    return MessageResponse(
                        content=error_msg,
                        message_type="error",
                        thread_id=thread_id,
                        run_id=run_id,
                        status=run.status,
                        error=error_msg
                    )
                
                # Wait before polling again
                time.sleep(1)
            
            # Timeout reached
            return MessageResponse(
                content="Processing timeout. Please try again.",
                message_type="error",
                thread_id=thread_id,
                run_id=run_id,
                status="timeout",
                error="Run processing exceeded timeout"
            )
            
        except Exception as e:
            logger.error(f"Failed to process run: {e}")
            return MessageResponse(
                content=f"Error processing message: {str(e)}",
                message_type="error",
                thread_id=thread_id,
                run_id=run_id,
                status="error",
                error=str(e)
            )
    
    async def handle_tool_calls(
        self, 
        run_id: str, 
        tool_calls: List[Any]
    ) -> List[Dict[str, str]]:
        """
        Handle tool calls from the assistant
        
        Args:
            run_id: The run identifier
            tool_calls: List of tool calls to handle
            
        Returns:
            List of tool outputs
        """
        tool_outputs = []
        
        for tool_call in tool_calls:
            try:
                output = await self._execute_tool(tool_call)
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": json.dumps(output) if isinstance(output, dict) else str(output)
                })
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": f"Tool execution error: {str(e)}"
                })
        
        return tool_outputs
    
    async def get_or_create_thread(
        self, 
        workspace_id: str
    ) -> str:
        """
        Get existing thread or create new one for workspace
        
        Args:
            workspace_id: The workspace identifier
            
        Returns:
            Thread ID
        """
        try:
            # Check for existing thread
            existing = self.supabase.table("workspace_assistants")\
                .select("thread_id")\
                .eq("workspace_id", workspace_id)\
                .execute()
            
            if existing.data and existing.data[0].get("thread_id"):
                thread_id = existing.data[0]["thread_id"]
                
                # Verify thread still exists
                try:
                    thread = self.client.beta.threads.retrieve(thread_id)
                    logger.info(f"Using existing thread {thread_id} for workspace {workspace_id}")
                    return thread_id
                except:
                    logger.warning(f"Thread {thread_id} no longer exists, creating new one")
            
            # Create new thread
            thread = await self.create_thread(workspace_id)
            return thread["id"]
            
        except Exception as e:
            logger.error(f"Failed to get/create thread: {e}")
            raise
    
    # Private helper methods
    
    def _get_default_config(self, workspace_id: str) -> AssistantConfig:
        """Get default assistant configuration"""
        return AssistantConfig(
            name=f"Workspace {workspace_id} Assistant",
            instructions="""You are an AI assistant for a software development team working on {workspace_name}.
            Project Goal: {workspace_goal}
            
            You have access to uploaded documents and can search through them to answer questions.
            Use the file_search tool to find relevant information in documents.
            Provide specific, actionable answers based on the content you find.
            When citing documents, always mention the source file name.
            
            Key capabilities:
            - Search through uploaded PDFs and documents
            - Analyze code and technical documentation
            - Provide insights based on project context
            - Answer questions about project deliverables and assets
            """,
            model=self.default_model,
            temperature=self.default_temperature,
            max_tokens=self.default_max_tokens,
            file_search_max_results=self.file_search_max_results
        )
    
    async def _get_workspace_info(self, workspace_id: str) -> Dict[str, Any]:
        """Get workspace information from database"""
        try:
            result = self.supabase.table("workspaces")\
                .select("*")\
                .eq("id", workspace_id)\
                .execute()
            
            if result.data:
                return result.data[0]
            return {}
        except Exception as e:
            logger.error(f"Failed to get workspace info: {e}")
            return {}
    
    async def _get_vector_store_ids(self, workspace_id: str) -> List[str]:
        """Get vector store IDs for workspace"""
        try:
            from services.document_manager import document_manager
            return await document_manager.get_vector_store_ids_for_agent(workspace_id)
        except Exception as e:
            logger.warning(f"Failed to get vector stores: {e}")
            return []
    
    async def _register_assistant(self, workspace_id: str, assistant_id: str):
        """Register assistant in database"""
        try:
            data = {
                "workspace_id": workspace_id,
                "assistant_id": assistant_id,
                "configuration": {
                    "model": self.default_model,
                    "temperature": self.default_temperature,
                    "max_tokens": self.default_max_tokens
                },
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
            # Upsert to handle existing records
            self.supabase.table("workspace_assistants")\
                .upsert(data, on_conflict="workspace_id")\
                .execute()
                
        except Exception as e:
            logger.error(f"Failed to register assistant: {e}")
    
    async def _sync_vector_stores(self, workspace_id: str, assistant_id: str):
        """Sync vector stores between database and assistant"""
        try:
            vector_store_ids = await self._get_vector_store_ids(workspace_id)
            if vector_store_ids:
                await self.update_assistant_vector_stores(assistant_id, vector_store_ids)
        except Exception as e:
            logger.warning(f"Failed to sync vector stores: {e}")
    
    async def _get_assistant_id_for_thread(self, thread_id: str) -> Optional[str]:
        """Get assistant ID associated with a thread"""
        try:
            result = self.supabase.table("workspace_assistants")\
                .select("assistant_id")\
                .eq("thread_id", thread_id)\
                .execute()
            
            if result.data:
                return result.data[0]["assistant_id"]
            return None
        except Exception as e:
            logger.error(f"Failed to get assistant ID for thread: {e}")
            return None
    
    async def _execute_tool(self, tool_call: Any) -> Any:
        """Execute a tool call (for custom tools)"""
        # This is where you'd implement custom tool execution
        # For now, we rely on OpenAI's built-in tools
        logger.info(f"Tool call: {tool_call.type} - {tool_call.id}")
        return {"status": "Tool execution not implemented"}

# Global instance
assistant_manager = OpenAIAssistantManager()