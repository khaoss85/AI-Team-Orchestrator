#!/usr/bin/env python3
"""
Conversational Agent Factory
Provides seamless switching between SimpleConversationalAgent and ConversationalAssistant
"""

import os
import logging
from typing import Union

logger = logging.getLogger(__name__)

def get_conversational_agent(workspace_id: str, chat_id: str = "general") -> Union:
    """
    Factory method to get the appropriate conversational agent
    
    Args:
        workspace_id: The workspace identifier
        chat_id: The chat/conversation identifier
        
    Returns:
        Either SimpleConversationalAgent or ConversationalAssistant based on configuration
    """
    use_assistants = os.getenv("USE_OPENAI_ASSISTANTS", "false").lower() == "true"
    
    if use_assistants:
        try:
            from ai_agents.conversational_assistant import ConversationalAssistant
            logger.info(f"🤖 Using OpenAI Assistants API for workspace {workspace_id}")
            return ConversationalAssistant(workspace_id, chat_id)
        except Exception as e:
            logger.warning(f"Failed to initialize ConversationalAssistant: {e}, falling back to simple agent")
            # Fall back to simple agent if assistant fails
    
    # Default to simple agent
    from ai_agents.conversational_simple import SimpleConversationalAgent
    logger.info(f"💬 Using Simple Conversational Agent for workspace {workspace_id}")
    return SimpleConversationalAgent(workspace_id, chat_id)

async def create_and_initialize_agent(workspace_id: str, chat_id: str = "general"):
    """
    Create and initialize the appropriate conversational agent
    
    This method handles the async initialization required by ConversationalAssistant
    
    Args:
        workspace_id: The workspace identifier
        chat_id: The chat/conversation identifier
        
    Returns:
        Initialized conversational agent
    """
    agent = get_conversational_agent(workspace_id, chat_id)
    
    # Initialize if it's the new assistant (has initialize method)
    if hasattr(agent, 'initialize'):
        try:
            await agent.initialize()
            logger.info(f"✅ ConversationalAssistant initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ConversationalAssistant: {e}")
            # Fall back to simple agent
            from ai_agents.conversational_simple import SimpleConversationalAgent
            logger.info(f"Falling back to SimpleConversationalAgent due to initialization failure")
            agent = SimpleConversationalAgent(workspace_id, chat_id)
    
    return agent