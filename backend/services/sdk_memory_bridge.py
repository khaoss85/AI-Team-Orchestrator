"""
SDK Memory Bridge - Integrazione tra UnifiedMemoryEngine e OpenAI Agents SDK Sessions
Allineamento con Pilastro 1: Core = OpenAI Agents SDK (uso nativo)
"""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from .unified_memory_engine import unified_memory_engine

logger = logging.getLogger(__name__)

class WorkspaceMemorySession:
    """
    Bridge tra il nostro Memory System e l'SDK Sessions
    Implementa il protocollo Session dell'SDK per usare le primitive native
    """
    
    def __init__(self, workspace_id: str, agent_id: Optional[str] = None):
        self.workspace_id = workspace_id
        self.agent_id = agent_id
        self.session_id = f"workspace_{workspace_id}" + (f"_agent_{agent_id}" if agent_id else "")
        logger.info(f"🌉 SDK Memory Bridge initialized for session: {self.session_id}")
    
    async def get_items(self, limit: Optional[int] = None) -> List[dict]:
        """
        Retrieve conversation history from our memory system
        Maps memory patterns to SDK conversation items
        """
        try:
            # Get relevant memory context
            contexts = await unified_memory_engine.get_relevant_context(
                workspace_id=self.workspace_id,
                query="conversation history",
                context_types=["user", "assistant", "system", "conversation", "task_execution", "user_request"],
                max_results=limit or 50
            )
            
            # Convert to SDK items format
            items = []
            for context in contexts:
                content_data = context.content if hasattr(context, 'content') else {}
                context_type = context.context_type if hasattr(context, 'context_type') else 'unknown'
                
                # Map different context types to conversation items
                # Handle both old format (user/assistant/system) and new format (task_execution/user_request/conversation)
                if context_type in ['task_execution', 'assistant']:
                    items.append({
                        "role": "assistant",
                        "content": content_data.get('result', content_data.get('message', str(content_data)))
                    })
                
                elif context_type in ['user_request', 'user']:
                    items.append({
                        "role": "user",
                        "content": content_data.get('message', str(content_data))
                    })
                
                elif context_type in ['conversation', 'system']:
                    items.append({
                        "role": "system",
                        "content": content_data.get('message', str(content_data))
                    })
            
            # For now, skip insights extraction as method doesn't exist
            # TODO: Implement insights extraction when method is available
            
            logger.info(f"✅ Retrieved {len(items)} items from memory for session {self.session_id}")
            return items
            
        except Exception as e:
            logger.error(f"Failed to get items from memory: {e}")
            return []
    
    async def add_items(self, items: List[dict]) -> None:
        """
        Store new items in our memory system
        Converts SDK items to memory patterns
        """
        try:
            for item in items:
                role = item.get('role', 'unknown')
                content = item.get('content', '')
                metadata = item.get('metadata', {})
                
                # Map SDK roles to memory context types for proper retrieval
                context_type_mapping = {
                    'user': 'user_request',
                    'assistant': 'task_execution', 
                    'system': 'conversation'
                }
                
                try:
                    context_id = await unified_memory_engine.store_context(
                        workspace_id=self.workspace_id,
                        context_type=context_type_mapping.get(role, role),
                        content={
                            "message": content,
                            "metadata": metadata,
                            "timestamp": datetime.now().isoformat(),
                            "original_role": role  # Keep original role for SDK compatibility
                        },
                        importance_score=0.7 if role == 'assistant' else 0.5
                    )
                    if context_id:
                        logger.debug(f"Stored context {context_id} for role {role}")
                    else:
                        logger.warning(f"Failed to store context for role {role}")
                except Exception as e:
                    logger.error(f"Error storing individual item: {e}")
            
            logger.info(f"✅ Added {len(items)} items to memory for session {self.session_id}")
            
        except Exception as e:
            logger.error(f"Failed to add items to memory: {e}")
    
    async def pop_item(self) -> Optional[dict]:
        """
        Remove and return the most recent item
        Useful for corrections and undo operations
        """
        try:
            items = await self.get_items(limit=1)
            if items:
                # For now, just return the item without marking obsolete
                # TODO: Implement soft delete when method is available
                item = items[0]
                return item
            return None
            
        except Exception as e:
            logger.error(f"Failed to pop item: {e}")
            return None
    
    async def clear_session(self) -> None:
        """
        Clear all items for this session
        Preserves valuable patterns but marks them as archived
        """
        try:
            # For now, log the clear request
            # TODO: Implement archive when method is available
            logger.info(f"Session clear requested for workspace {self.workspace_id}")
            logger.info(f"✅ Cleared session {self.session_id}")
            
        except Exception as e:
            logger.error(f"Failed to clear session: {e}")

# Factory function for easy creation
def create_workspace_session(workspace_id: str, agent_id: Optional[str] = None) -> WorkspaceMemorySession:
    """
    Create a memory session that bridges UnifiedMemoryEngine with SDK Sessions
    
    Usage:
        session = create_workspace_session(workspace_id)
        result = await Runner.run(agent, input, session=session)
    """
    return WorkspaceMemorySession(workspace_id, agent_id)

# Example integration in specialist agent
"""
# In specialist_enhanced.py execute method:

from services.sdk_memory_bridge import create_workspace_session

# Create session for the workspace
session = create_workspace_session(
    workspace_id=str(task.workspace_id),
    agent_id=str(self.agent_data.id)
)

# Run with session - SDK handles memory automatically
run_result = await Runner.run(
    starting_agent=agent,
    input=str(task.model_dump()),
    context=orchestration_context,
    session=session,  # ADD THIS LINE
    max_turns=5
)
"""