#!/usr/bin/env python3
"""
Shared Document Manager Service
Extends OpenAI Assistant Manager to support document sharing across specialist agents
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from database import get_supabase_client

logger = logging.getLogger(__name__)

# Availability flag for other modules to check
SHARED_DOCUMENTS_AVAILABLE = True

class SharedDocumentManager:
    """
    Manages document sharing between conversational assistants and specialist agents
    
    Key responsibilities:
    - Share workspace vector stores with specialist agents
    - Create specialist-specific assistants with document access
    - Maintain document access permissions across agent types
    - Synchronize vector store updates across all workspace agents
    """
    
    def __init__(self):
        """Initialize the shared document manager"""
        from services.openai_assistant_manager import OpenAIAssistantManager
        self.assistant_manager = OpenAIAssistantManager()
        self.supabase = get_supabase_client()
        logger.info("Shared Document Manager initialized")
    
    async def create_specialist_assistant(
        self, 
        workspace_id: str,
        agent_id: str,
        agent_config: Dict[str, Any]
    ) -> Optional[str]:
        """
        Create an OpenAI assistant for a specialist agent with document access
        
        SIMPLIFIED APPROACH: Share the workspace conversational assistant
        This avoids creating multiple assistants per workspace and reuses existing infrastructure
        
        Args:
            workspace_id: The workspace identifier
            agent_id: The specialist agent identifier
            agent_config: Agent configuration (role, skills, etc.)
            
        Returns:
            OpenAI assistant ID or None if creation failed
        """
        try:
            # Get or create the workspace assistant (same one used by conversational agent)
            assistant = await self.assistant_manager.get_or_create_assistant(workspace_id)
            
            if not assistant:
                logger.error(f"Failed to get workspace assistant for specialist {agent_id}")
                return None
            
            assistant_id = assistant["id"]
            
            # Ensure workspace documents are attached (should already be done)
            await self._attach_workspace_documents(workspace_id, assistant_id)
            
            # Store specialist-assistant mapping (maps to shared assistant)
            await self._store_specialist_assistant_mapping(workspace_id, agent_id, assistant_id)
            
            logger.info(f"✅ Specialist {agent_id} will use shared workspace assistant {assistant_id}")
            return assistant_id
            
        except Exception as e:
            logger.error(f"Failed to create specialist assistant: {e}")
            return None
    
    async def _attach_workspace_documents(self, workspace_id: str, assistant_id: str) -> bool:
        """
        Attach all workspace documents to a specialist assistant
        
        Args:
            workspace_id: The workspace identifier
            assistant_id: The specialist assistant identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get workspace vector stores
            vector_store_ids = await self._get_workspace_vector_stores(workspace_id)
            
            if not vector_store_ids:
                logger.info(f"No vector stores found for workspace {workspace_id}")
                return True  # Not an error, just no documents yet
            
            # Update assistant with vector store access
            self.assistant_manager.client.beta.assistants.update(
                assistant_id=assistant_id,
                tool_resources={
                    "file_search": {
                        "vector_store_ids": vector_store_ids
                    }
                }
            )
            
            logger.info(f"✅ Attached {len(vector_store_ids)} vector stores to specialist {assistant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to attach workspace documents: {e}")
            return False
    
    async def _get_workspace_vector_stores(self, workspace_id: str) -> List[str]:
        """
        Get all vector store IDs associated with a workspace
        
        Args:
            workspace_id: The workspace identifier
            
        Returns:
            List of vector store IDs
        """
        try:
            # Query workspace_assistants table for vector stores
            result = self.supabase.table("workspace_assistants")\
                .select("vector_store_ids")\
                .eq("workspace_id", workspace_id)\
                .execute()
            
            if not result.data:
                return []
            
            # Collect all vector store IDs
            all_vector_stores = set()
            for row in result.data:
                vector_store_ids = row.get("vector_store_ids", [])
                if isinstance(vector_store_ids, list):
                    all_vector_stores.update(vector_store_ids)
            
            return list(all_vector_stores)
            
        except Exception as e:
            logger.error(f"Failed to get workspace vector stores: {e}")
            return []
    
    async def _store_specialist_assistant_mapping(
        self, 
        workspace_id: str, 
        agent_id: str, 
        assistant_id: str
    ) -> bool:
        """
        Store the mapping between specialist agent and OpenAI assistant
        
        Args:
            workspace_id: The workspace identifier
            agent_id: The specialist agent identifier  
            assistant_id: The OpenAI assistant identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Try to store in specialist_assistants table
            try:
                self.supabase.table("specialist_assistants").upsert({
                    "workspace_id": workspace_id,
                    "agent_id": agent_id,
                    "assistant_id": assistant_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }).execute()
                
                logger.info(f"✅ Stored specialist-assistant mapping: {agent_id} -> {assistant_id}")
                return True
                
            except Exception as db_error:
                # Fallback: Store in memory (for testing/development)
                if not hasattr(self, '_memory_mappings'):
                    self._memory_mappings = {}
                    
                mapping_key = f"{workspace_id}:{agent_id}"
                self._memory_mappings[mapping_key] = {
                    "assistant_id": assistant_id,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                logger.warning(f"⚠️ Using memory storage for specialist mapping: {agent_id} -> {assistant_id}")
                logger.warning(f"Database error: {db_error}")
                return True
            
        except Exception as e:
            logger.error(f"Failed to store specialist-assistant mapping: {e}")
            return False
    
    async def get_specialist_assistant_id(self, workspace_id: str, agent_id: str) -> Optional[str]:
        """
        Get the OpenAI assistant ID for a specialist agent
        
        Args:
            workspace_id: The workspace identifier
            agent_id: The specialist agent identifier
            
        Returns:
            Assistant ID or None if not found
        """
        try:
            # Try database first
            try:
                result = self.supabase.table("specialist_assistants")\
                    .select("assistant_id")\
                    .eq("workspace_id", workspace_id)\
                    .eq("agent_id", agent_id)\
                    .execute()
                
                if result.data:
                    return result.data[0]["assistant_id"]
                    
            except Exception as db_error:
                # Fallback to memory storage
                if hasattr(self, '_memory_mappings'):
                    mapping_key = f"{workspace_id}:{agent_id}"
                    mapping = self._memory_mappings.get(mapping_key)
                    if mapping:
                        logger.info(f"📦 Retrieved assistant ID from memory: {mapping['assistant_id']}")
                        return mapping["assistant_id"]
                
                logger.debug(f"Database query failed, checking memory: {db_error}")
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get specialist assistant ID: {e}")
            return None
    
    async def sync_documents_to_all_specialists(self, workspace_id: str) -> bool:
        """
        Synchronize document access across all specialist agents in workspace
        
        Args:
            workspace_id: The workspace identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all specialist assistants for workspace
            result = self.supabase.table("specialist_assistants")\
                .select("assistant_id")\
                .eq("workspace_id", workspace_id)\
                .execute()
            
            if not result.data:
                logger.info(f"No specialist assistants found for workspace {workspace_id}")
                return True
            
            # Update each specialist with current workspace documents
            success_count = 0
            for row in result.data:
                assistant_id = row["assistant_id"]
                if await self._attach_workspace_documents(workspace_id, assistant_id):
                    success_count += 1
            
            logger.info(f"✅ Synced documents to {success_count}/{len(result.data)} specialists")
            return success_count == len(result.data)
            
        except Exception as e:
            logger.error(f"Failed to sync documents to specialists: {e}")
            return False
    
    def _build_specialist_instructions(self, agent_config: Dict[str, Any]) -> str:
        """
        Build instruction text for specialist assistant
        
        Args:
            agent_config: Agent configuration
            
        Returns:
            Formatted instruction string
        """
        role = agent_config.get('role', 'Specialist')
        skills = agent_config.get('skills', [])
        seniority = agent_config.get('seniority', 'senior')
        
        instructions = f"""You are a {seniority} {role} specialist agent with the following expertise:

CORE SKILLS:
{chr(10).join(f"- {skill}" for skill in skills)}

DOCUMENT ACCESS:
You have access to all workspace documents through the file_search tool. When working on tasks:
1. Search relevant documents for context and information
2. Reference document sources in your responses
3. Use document information to inform your analysis and recommendations

TASK EXECUTION:
- Provide detailed, professional output based on your expertise
- Reference relevant documents when available
- Maintain high quality standards for all deliverables
- Follow the workspace's established patterns and guidelines

Always use your specialist knowledge combined with document insights to deliver the best possible results."""

        return instructions
    
    def _build_workspace_tools(self) -> Dict[str, Any]:
        """
        Build workspace-specific tools for specialist agents
        
        Returns:
            Tool definition for workspace operations
        """
        return {
            "name": "workspace_search",
            "description": "Search workspace documents and context",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for workspace documents"
                    },
                    "document_type": {
                        "type": "string",
                        "description": "Optional document type filter",
                        "enum": ["pdf", "doc", "txt", "all"]
                    }
                },
                "required": ["query"]
            }
        }

# Global instance for shared document management
shared_document_manager = SharedDocumentManager()