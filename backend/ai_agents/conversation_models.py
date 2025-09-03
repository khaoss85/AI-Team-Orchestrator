"""
Shared models for conversational agents
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ConversationResponse(BaseModel):
    """Unified response model for all conversational agents"""
    message: str
    message_type: str = "text"
    artifacts: Optional[List[Dict[str, Any]]] = None
    actions_performed: Optional[List[Dict[str, Any]]] = None
    needs_confirmation: bool = False
    confirmation_id: Optional[str] = None
    suggested_actions: Optional[List[Dict[str, Any]]] = None
    # Additional fields for OpenAI Assistants
    citations: Optional[List[Dict[str, Any]]] = None
    thread_id: Optional[str] = None
    run_id: Optional[str] = None
    
    model_config = {"extra": "allow"}  # Allow extra fields for compatibility