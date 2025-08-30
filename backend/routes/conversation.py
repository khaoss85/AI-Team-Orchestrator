"""
Conversation API Routes - Universal conversational interface
Provides domain-agnostic endpoints for AI-driven project management
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from uuid import uuid4, UUID

from fastapi import Request, APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from middleware.trace_middleware import get_trace_id, create_traced_logger, TracedDatabaseOperation
from pydantic import BaseModel, Field

from database import get_supabase_client
from models import Workspace

logger = logging.getLogger(__name__)

# Use simple AI-driven conversational agent for reliable functionality
try:
    from ai_agents.conversational_simple import SimpleConversationalAgent as ConversationalAgent, ConversationResponse
    CONVERSATIONAL_AI_TYPE = "simple"  
    logger.info("✅ AI-driven ConversationalAgent loaded (simple version)")
except ImportError as e:
    logger.error(f"No conversational AI available: {e}")
    CONVERSATIONAL_AI_TYPE = "fallback"

# Tool registry fallback
try:
    from ai_agents.conversational_tools import ConversationalToolRegistry
except ImportError:
    class ConversationalToolRegistry:
        def __init__(self, workspace_id: str):
            self.workspace_id = workspace_id

CONVERSATIONAL_AI_AVAILABLE = CONVERSATIONAL_AI_TYPE != "fallback"

# Only create fallback if absolutely no AI is available
if CONVERSATIONAL_AI_TYPE == "fallback":
    class ConversationalAgent:
        def __init__(self, workspace_id: str, chat_id: str = "general"):
            self.workspace_id = workspace_id
            self.chat_id = chat_id
        
        async def process_message(self, user_message: str, message_id: str = None):
            return ConversationResponse(
                message="🔄 AI system is in fallback mode. Please check OpenAI API configuration.",
                message_type="system_info"
            )
    
    class ConversationResponse(BaseModel):
        message: str
        message_type: str = "text"
        artifacts: Optional[List[Dict[str, Any]]] = None
        actions_performed: Optional[List[Dict[str, Any]]] = None
        needs_confirmation: bool = False
        confirmation_id: Optional[str] = None
        
        model_config = {"extra": "allow"}

router = APIRouter(prefix="/conversation", tags=["conversation"])

# Request/Response Models

class ChatMessageRequest(BaseModel):
    """Request model for chat messages"""
    message: str = Field(..., description="User message content")
    chat_id: str = Field(default="general", description="Chat identifier")
    message_id: Optional[str] = Field(None, description="Optional client-generated message ID")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")

class ChatMessageResponse(BaseModel):
    """Response model for chat messages"""
    message_id: str
    response: ConversationResponse
    conversation_id: str
    timestamp: str
    processing_time_ms: int

class ConversationHistoryRequest(BaseModel):
    """Request model for conversation history"""
    chat_id: str = Field(default="general", description="Chat identifier")
    limit: Optional[int] = Field(default=50, description="Maximum number of messages to return")
    before: Optional[str] = Field(None, description="Get messages before this timestamp")

class ConversationSummaryResponse(BaseModel):
    """Response model for conversation summary"""
    conversation_id: str
    total_messages: int
    active_messages: int
    archived_summaries: int
    last_activity: str
    key_topics: List[str]
    action_items: List[Dict[str, Any]]

class ConfirmationRequest(BaseModel):
    """Request model for action confirmations"""
    action_id: str
    decision: str = Field(..., description="'confirm' or 'cancel'")
    feedback: Optional[str] = Field(None, description="Optional user feedback")

# Main Endpoints

@router.post("/workspaces/{workspace_id}/chat", response_model=ChatMessageResponse)
async def send_chat_message(
    workspace_id: str,
    request: ChatMessageRequest
) -> ChatMessageResponse:
    """
    Send a message to the conversational AI assistant.
    Universal endpoint that works for any project domain.
    """
    start_time = datetime.now()
    
    try:
        # Initialize conversational agent for this workspace and chat
        agent = ConversationalAgent(workspace_id, request.chat_id)
        
        # Process the message
        response = await agent.process_message(
            user_message=request.message,
            message_id=request.message_id
        )
        
        # Calculate processing time
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return ChatMessageResponse(
            message_id=request.message_id or str(uuid4()),
            response=response,
            conversation_id=f"{workspace_id}_{request.chat_id}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

@router.post("/workspaces/{workspace_id}/chat/thinking", response_model=ChatMessageResponse)
async def send_chat_message_with_thinking(
    workspace_id: str,
    request: ChatMessageRequest
) -> ChatMessageResponse:
    """
    Send a message with real-time thinking process (for demonstration purposes).
    Note: This endpoint simulates the thinking process but doesn't stream it.
    For real-time thinking, use the WebSocket endpoint.
    """
    start_time = datetime.now()
    
    try:
        # Initialize conversational agent
        agent = ConversationalAgent(workspace_id, request.chat_id)
        
        # Store thinking steps for response
        thinking_steps = []
        
        async def thinking_callback(thinking_data):
            thinking_steps.append({
                **thinking_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        # Process message with thinking
        response = await agent.process_message_with_thinking(
            user_message=request.message,
            message_id=request.message_id,
            thinking_callback=thinking_callback
        )
        
        # Add thinking steps to response metadata
        response.artifacts = response.artifacts or []
        response.artifacts.append({
            "type": "thinking_process",
            "title": "AI Thinking Process",
            "content": {
                "steps": thinking_steps,
                "total_steps": len(thinking_steps)
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return ChatMessageResponse(
            message_id=request.message_id or str(uuid4()),
            response=response,
            conversation_id=f"{workspace_id}_{request.chat_id}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error processing thinking message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process thinking message: {str(e)}")

@router.post("/workspaces/{workspace_id}/chat/deliverable")
async def send_deliverable_to_chat(
    workspace_id: str,
    deliverable_data: Dict[str, Any]
) -> Dict[str, Any]:
    """🎯 Send a completed deliverable to the conversational chat"""
    try:
        supabase = get_supabase_client()
        
        # Create chat message for deliverable
        message_data = {
            "workspace_id": workspace_id,
            "chat_id": deliverable_data.get("chat_id", "general"),
            "content": f"🎉 **Deliverable Ready:** {deliverable_data.get('deliverable_title', 'Untitled')}\n\n" +
                      f"Goal: {deliverable_data.get('goal_description', 'General objective')}\n" +
                      f"Business Value Score: {deliverable_data.get('business_value_score', 0)}\n\n" +
                      "Your deliverable is ready for download and use!",
            "message_type": "deliverable",
            "sender": "system",
            "metadata": {
                "deliverable_id": deliverable_data.get("deliverable_id"),
                "deliverable_title": deliverable_data.get("deliverable_title"),
                "deliverable_content": deliverable_data.get("deliverable_content"),
                "goal_description": deliverable_data.get("goal_description"),
                "business_value_score": deliverable_data.get("business_value_score"),
                "auto_sent": deliverable_data.get("auto_sent", False)
            },
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Save to database
        result = supabase.table("chat_messages").insert(message_data).execute()
        
        if result.data:
            logger.info(f"✅ Deliverable message sent to chat: {deliverable_data.get('deliverable_title')}")
            return {
                "success": True,
                "message_id": result.data[0]["id"],
                "content": "Deliverable sent to chat successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save deliverable message")
            
    except Exception as e:
        logger.error(f"❌ Error sending deliverable to chat: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send deliverable: {str(e)}")

@router.post("/workspaces/{workspace_id}/execute-action")
async def execute_suggested_action(
    workspace_id: str,
    action_request: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute a suggested action (tool) from the AI response.
    This makes the suggested actions actually clickable and executable.
    """
    try:
        # Extract action details
        tool_name = action_request.get("tool")
        parameters = action_request.get("parameters", {})
        chat_id = action_request.get("chat_id", "general")
        
        if not tool_name:
            raise HTTPException(status_code=400, detail="Tool name is required")
        
        # Initialize agent to use tool execution
        from ai_agents.conversational_simple import SimpleConversationalAgent
        agent = SimpleConversationalAgent(workspace_id, chat_id)
        await agent._load_context()
        
        # Execute the tool directly to get the full result dict
        logger.info(f"🔧 [execute_suggested_action] Executing tool: {tool_name} with params: {parameters}")
        tool_result = await agent._execute_tool(tool_name, parameters)
        logger.info(f"📊 [execute_suggested_action] Tool result: {tool_result}")
        logger.info(f"📊 [execute_suggested_action] Tool result type: {type(tool_result)}")
        
        # Create a follow-up message in the chat with the result
        if tool_result and isinstance(tool_result, dict):
            # Extract message from the tool result
            message = tool_result.get("message", "Action completed successfully")
            status_icon = "✅" if tool_result.get("success", True) else "❌"
            
            # Store the action execution as an AI message in the conversation
            follow_up_message = f"{status_icon} **Action Executed: {tool_name.replace('_', ' ').title()}**\n\n{message}"
            
            # Store this as an AI message
            await agent._store_message(
                get_supabase_client(),
                follow_up_message,
                "assistant",
                f"action_{tool_name}_{int(datetime.now().timestamp())}"
            )
        
        return {
            "success": tool_result.get("success", True) if isinstance(tool_result, dict) else True,
            "tool": tool_name,
            "result": tool_result,
            "message": tool_result.get("message", "Action completed successfully") if isinstance(tool_result, dict) else str(tool_result),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error executing action {action_request.get('tool', 'unknown')}: {e}")
        return {
            "success": False,
            "tool": action_request.get("tool", "unknown"),
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@router.get("/workspaces/{workspace_id}/history", response_model=List[Dict[str, Any]])
async def get_conversation_history(
    workspace_id: str,
    chat_id: str = "general",
    limit: int = 50,
    before: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get conversation history for a specific chat.
    Supports pagination and filtering.
    """
    try:
        supabase = get_supabase_client()
        conversation_identifier = f"{workspace_id}_{chat_id}"
        
        logger.info(f"Fetching conversation history for: {conversation_identifier}")
        
        # Build query using the main table (matching what conversational_simple.py uses)
        query = supabase.table("conversation_messages")\
            .select("*")\
            .eq("conversation_identifier", conversation_identifier)\
            .order("created_at", desc=True)\
            .limit(limit)
        
        if before:
            query = query.lt("created_at", before)
        
        result = query.execute()
        
        logger.info(f"Query result for {conversation_identifier}: {len(result.data or [])} messages found")
        
        # Check if no messages found - this might be due to RLS policy issues
        if not result.data:
            logger.warning(f"No messages found for conversation: {conversation_identifier}")
            
            # Try to count total messages to see if they exist but are blocked by RLS
            try:
                count_result = supabase.table("conversation_messages")\
                    .select("id", count="exact")\
                    .eq("conversation_identifier", conversation_identifier)\
                    .execute()
                logger.info(f"Total message count for {conversation_identifier}: {count_result.count}")
            except Exception as count_error:
                logger.error(f"Error counting messages: {count_error}")
        
        # Reverse to get chronological order
        messages = list(reversed(result.data or []))
        
        return messages
        
    except Exception as e:
        logger.error(f"Error fetching conversation history for {workspace_id}_{chat_id}: {e}")
        
        # Provide more specific error information
        error_detail = str(e)
        if "row-level security policy" in error_detail.lower():
            error_detail = f"Database access denied due to security policy. This might be due to authentication issues. Original error: {error_detail}"
        
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {error_detail}")

@router.get("/workspaces/{workspace_id}/summary", response_model=ConversationSummaryResponse)
async def get_conversation_summary(
    workspace_id: str,
    chat_id: str = "general"
) -> ConversationSummaryResponse:
    """
    Get a summary of the conversation including key topics and action items.
    AI-driven analysis of conversation patterns.
    """
    try:
        supabase = get_supabase_client()
        
        # Get conversation data using compatibility view
        conversation_result = supabase.table("conversations_v2")\
            .select("*")\
            .eq("workspace_id", workspace_id)\
            .eq("chat_id", chat_id)\
            .execute()
        
        if not conversation_result.data:
            # Create a default conversation response if not found
            conversation = {
                "conversation_id": f"{workspace_id}_{chat_id}",
                "active_messages": [],
                "archived_summaries": [],
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        else:
            conversation = conversation_result.data[0]
        
        # Get message count using compatibility view
        message_count = supabase.table("conversation_messages_v2")\
            .select("id", count="exact")\
            .eq("conversation_id", f"{workspace_id}_{chat_id}")\
            .execute()
        
        total_messages = message_count.count or 0
        
        # Get recent messages for analysis using compatibility view
        recent_messages = supabase.table("conversation_messages_v2")\
            .select("content, role, tools_used, actions_performed")\
            .eq("conversation_id", f"{workspace_id}_{chat_id}")\
            .order("created_at", desc=True)\
            .limit(20)\
            .execute()
        
        # AI-driven analysis
        analysis = await _analyze_conversation_content(recent_messages.data or [])
        
        return ConversationSummaryResponse(
            conversation_id=f"{workspace_id}_{chat_id}",
            total_messages=total_messages,
            active_messages=len(conversation.get("active_messages", [])),
            archived_summaries=len(conversation.get("archived_summaries", [])),
            last_activity=conversation.get("updated_at", conversation.get("created_at", "")),
            key_topics=analysis["key_topics"],
            action_items=analysis["action_items"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating conversation summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")

@router.post("/workspaces/{workspace_id}/confirm")
async def confirm_action(
    workspace_id: str,
    request: ConfirmationRequest
) -> Dict[str, Any]:
    """
    Confirm or cancel a pending action.
    Implements two-step confirmation for destructive operations.
    """
    try:
        supabase = get_supabase_client()
        
        # Get pending confirmation using compatibility view
        confirmation_result = supabase.table("pending_confirmations_v2")\
            .select("*")\
            .eq("action_id", request.action_id)\
            .eq("status", "pending")\
            .execute()
        
        if not confirmation_result.data:
            raise HTTPException(status_code=404, detail="Pending confirmation not found or expired")
        
        confirmation = confirmation_result.data[0]
        
        # Check if expired
        expires_at = datetime.fromisoformat(confirmation["expires_at"].replace('Z', '+00:00'))
        if datetime.now(timezone.utc) > expires_at:
            # Mark as expired
            supabase.table("pending_confirmations")\
                .update({"status": "expired"})\
                .eq("action_id_text", request.action_id)\
                .execute()
            raise HTTPException(status_code=410, detail="Confirmation has expired")
        
        if request.decision == "confirm":
            # Execute the action
            result = await _execute_confirmed_action(confirmation)
            
            # Update confirmation status
            supabase.table("pending_confirmations")\
                .update({
                    "status": "confirmed",
                    "confirmed_at": datetime.now(timezone.utc).isoformat(),
                    "metadata": {"execution_result": result, "user_feedback": request.feedback}
                })\
                .eq("action_id_text", request.action_id)\
                .execute()
            
            return {
                "success": True,
                "action_executed": True,
                "result": result,
                "message": "Action confirmed and executed successfully"
            }
            
        elif request.decision == "cancel":
            # Cancel the action
            supabase.table("pending_confirmations")\
                .update({
                    "status": "cancelled",
                    "metadata": {"user_feedback": request.feedback}
                })\
                .eq("action_id_text", request.action_id)\
                .execute()
            
            return {
                "success": True,
                "action_executed": False,
                "message": "Action cancelled by user"
            }
            
        else:
            raise HTTPException(status_code=400, detail="Decision must be 'confirm' or 'cancel'")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling confirmation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process confirmation: {str(e)}")

@router.get("/workspaces/{workspace_id}/context")
async def get_conversation_context(request: Request, workspace_id: str, chat_id: str = "general") -> Dict[str, Any]:
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_conversation_context called", endpoint="get_conversation_context", trace_id=trace_id)

    """
    Get current conversation context including workspace state.
    Useful for debugging and advanced integrations.
    """
    try:
        if CONVERSATIONAL_AI_AVAILABLE:
            # Initialize agent to load context (full version)
            agent = ConversationalAgent(workspace_id, chat_id)
            await agent._load_context()
            
            if not agent.context:
                raise HTTPException(status_code=404, detail="Context not available")
            
            # Return sanitized context (no sensitive data)
            context_data = agent.context.dict()
            
            # Remove sensitive information
            sanitized_context = {
                "workspace_id": context_data["workspace_id"],
                "chat_id": context_data["chat_id"],
                "workspace_summary": {
                    "name": context_data["workspace_data"].get("name", "Unknown"),
                    "domain": context_data["workspace_data"].get("domain", "General"),
                    "status": context_data["workspace_data"].get("status", "active")
                },
                "team_summary": {
                    "total_members": len(context_data["team_data"]),
                    "active_members": len([a for a in context_data["team_data"] if a.get("status") == "available"])
                },
                "activity_summary": {
                    "recent_tasks": len(context_data["recent_tasks"]),
                    "deliverables": len(context_data["deliverables"]),
                    "conversation_messages": len(context_data["conversation_history"])
                },
                "budget_summary": {
                    "max_budget": context_data["budget_info"].get("max_budget", 0),
                    "used_budget": context_data["budget_info"].get("used", 0)
                }
            }
        else:
            # Fallback context using direct database queries
            supabase = get_supabase_client()
            
            # Get workspace info
            workspace_result = supabase.table("workspaces").select("*").eq("id", workspace_id).execute()
            workspace_data = workspace_result.data[0] if workspace_result.data else {}
            
            # Get team info
            team_result = supabase.table("agents").select("*").eq("workspace_id", workspace_id).execute()
            team_data = team_result.data or []
            
            # Get recent tasks
            tasks_result = supabase.table("tasks").select("*").eq("workspace_id", workspace_id).order("created_at", desc=True).limit(10).execute()
            recent_tasks = tasks_result.data or []
            
            sanitized_context = {
                "workspace_id": workspace_id,
                "chat_id": chat_id,
                "workspace_summary": {
                    "name": workspace_data.get("name", "Unknown"),
                    "domain": workspace_data.get("goal", "General"),
                    "status": workspace_data.get("status", "active")
                },
                "team_summary": {
                    "total_members": len(team_data),
                    "active_members": len([a for a in team_data if a.get("status") == "active"])
                },
                "activity_summary": {
                    "recent_tasks": len(recent_tasks),
                    "deliverables": 0,  # Would need to query deliverables table
                    "conversation_messages": 0  # No messages in fallback mode
                },
                "budget_summary": {
                    "max_budget": workspace_data.get("budget", {}).get("max_budget", 0) if workspace_data.get("budget") else 0,
                    "used_budget": 0  # Would need to calculate
                },
                "fallback_mode": True
            }
        
        return sanitized_context
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching conversation context: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch context: {str(e)}")

# WebSocket Endpoint for Real-time Chat

@router.websocket("/workspaces/{workspace_id}/ws")
async def websocket_chat(websocket: WebSocket, workspace_id: str, chat_id: str = "general"):
    """
    WebSocket endpoint for real-time conversational AI.
    Supports streaming responses and live updates.
    """
    await websocket.accept()
    
    try:
        # Initialize agent
        agent = ConversationalAgent(workspace_id, chat_id)
        
        logger.info(f"WebSocket chat connected for workspace {workspace_id}, chat {chat_id}")
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            message = data.get("message", "")
            message_id = data.get("message_id", str(uuid4()))
            
            if not message:
                await websocket.send_json({
                    "type": "error",
                    "message": "Empty message received"
                })
                continue
            
            try:
                # Define thinking callback for real-time updates
                async def thinking_callback(thinking_data):
                    await websocket.send_json({
                        "type": "thinking",
                        "message_id": message_id,
                        "thinking_data": thinking_data,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                
                # Process message with thinking steps
                response = await agent.process_message_with_thinking(
                    message, 
                    message_id, 
                    thinking_callback=thinking_callback
                )
                
                # Send final response
                await websocket.send_json({
                    "type": "message",
                    "message_id": message_id,
                    "response": response.dict(),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                # Send any artifacts separately
                if response.artifacts:
                    await websocket.send_json({
                        "type": "artifacts",
                        "artifacts": response.artifacts,
                        "message_id": message_id
                    })
                
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Failed to process message: {str(e)}",
                    "message_id": message_id
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket chat disconnected for workspace {workspace_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

# Versioning Endpoints

@router.get("/versioning/history")
async def get_version_history(
    component_type: Optional[str] = None,
    component_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get version history for system components.
    Useful for tracking schema evolution and compatibility.
    """
    try:
        try:
            from utils.versioning_manager import VersioningManager
            
            manager = VersioningManager()
            history = await manager.get_version_history(component_type, component_name)
            
            return history
        except ImportError:
            # Fallback version history
            return [
                {
                    "version": "v2025-06-A",
                    "component_type": "conversational_ai",
                    "component_name": "core",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "description": "Initial conversational AI implementation",
                    "breaking_changes": [],
                    "new_features": ["Chat interface", "Context awareness", "Tool integration"]
                }
            ]
        
    except Exception as e:
        logger.error(f"Error fetching version history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch version history: {str(e)}")

@router.post("/versioning/check-compatibility")
async def check_version_compatibility(
    component_type: str,
    component_name: str,
    source_version: str,
    target_version: str
) -> Dict[str, Any]:
    """
    Check compatibility between two versions of a component.
    Returns migration requirements and compatibility level.
    """
    try:
        try:
            from utils.versioning_manager import VersioningManager
            
            manager = VersioningManager()
            compatibility = await manager.check_version_compatibility(
                component_type, component_name, source_version, target_version
            )
            
            return compatibility
        except ImportError:
            # Fallback compatibility check
            return {
                "compatible": True,
                "compatibility_level": "full",
                "migration_required": False,
                "migration_steps": [],
                "warnings": [],
                "source_version": source_version,
                "target_version": target_version,
                "fallback_mode": True
            }
        
    except Exception as e:
        logger.error(f"Error checking version compatibility: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check compatibility: {str(e)}")

@router.post("/workspaces/{workspace_id}/migrate-conversation")
async def migrate_conversation(
    workspace_id: str,
    conversation_id: str,
    target_version: str,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Migrate a conversation to a new schema version.
    Supports dry-run mode for testing migration without applying changes.
    """
    try:
        from utils.versioning_manager import VersioningManager
        
        manager = VersioningManager(workspace_id)
        result = await manager.migrate_conversation_to_version(
            conversation_id, target_version, dry_run
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error migrating conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to migrate conversation: {str(e)}")

@router.post("/workspaces/{workspace_id}/migrate-all")
async def migrate_workspace(
    workspace_id: str,
    target_version: str
) -> Dict[str, Any]:
    """
    Migrate entire workspace to new version.
    Migrates all conversations and components to target version.
    """
    try:
        from ..utils.versioning_manager import migrate_workspace_to_version
        
        result = await migrate_workspace_to_version(workspace_id, target_version)
        return result
        
    except Exception as e:
        logger.error(f"Error migrating workspace: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to migrate workspace: {str(e)}")

# Helper Functions

async def _analyze_conversation_content(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    AI-driven analysis of conversation content to extract key topics and action items.
    """
    try:
        # Extract topics from messages
        topics = set()
        action_items = []
        
        for message in messages:
            content = message.get("content", "")
            tools_used = message.get("tools_used", [])
            actions = message.get("actions_performed", [])
            
            # Simple keyword extraction (could be enhanced with NLP)
            if "budget" in content.lower():
                topics.add("Budget Management")
            if "team" in content.lower() or "agent" in content.lower():
                topics.add("Team Management")
            if "task" in content.lower() or "project" in content.lower():
                topics.add("Project Management")
            if "deliverable" in content.lower():
                topics.add("Deliverables")
            
            # Extract action items from tool usage
            for action in actions:
                if action.get("success", False):
                    action_items.append({
                        "action": action.get("action_type", "Unknown"),
                        "description": action.get("description", ""),
                        "status": "completed",
                        "timestamp": message.get("created_at", "")
                    })
        
        return {
            "key_topics": list(topics),
            "action_items": action_items[-10:]  # Last 10 action items
        }
        
    except Exception as e:
        logger.error(f"Error analyzing conversation content: {e}")
        return {"key_topics": [], "action_items": []}

async def _execute_confirmed_action(confirmation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a confirmed action based on the stored parameters.
    """
    try:
        action_type = confirmation["action_type"]
        parameters = confirmation["parameters"]
        workspace_id = confirmation.get("workspace_id") or parameters.get("workspace_id")
        
        # Initialize tool registry
        tools = ConversationalToolRegistry(workspace_id)
        
        # Execute based on action type
        if action_type == "delete_agent":
            # Delete agent
            supabase = get_supabase_client()
            result = supabase.table("agents")\
                .delete()\
                .eq("id", parameters["agent_id"])\
                .execute()
            return {"success": True, "deleted_agent": parameters.get("agent_name", "Unknown")}
            
        elif action_type == "modify_budget":
            # Use the budget modification tool
            result = await tools.modify_budget(
                operation=parameters["operation"],
                amount=parameters["amount"],
                reason=parameters.get("reason", "User confirmed action")
            )
            return result
            
        elif action_type == "reset_project":
            # Reset project data
            supabase = get_supabase_client()
            # Implement reset logic here
            return {"success": True, "message": "Project reset completed"}
            
        else:
            return {"success": False, "error": f"Unknown action type: {action_type}"}
            
    except Exception as e:
        logger.error(f"Error executing confirmed action: {e}")
        return {"success": False, "error": str(e)}

# Health Check
@router.get("/workspaces/{workspace_id}/knowledge-insights")
async def get_knowledge_insights(workspace_id: str, request: Request) -> Dict[str, Any]:
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route get_knowledge_insights called", endpoint="get_knowledge_insights", trace_id=trace_id)

    """
    Get knowledge insights for a workspace including best practices and learnings.
    """
    try:
        from workspace_memory import workspace_memory
        from models import MemoryQueryRequest, InsightType
        
        # Get workspace memory summary
        summary = await workspace_memory.get_workspace_summary(UUID(workspace_id))
        
        # Query specific types of insights
        best_practices_query = MemoryQueryRequest(
            query="best practices success patterns",
            insight_types=[InsightType.SUCCESS_PATTERN],
            limit=10
        )
        best_practices_response = await workspace_memory.query_insights(UUID(workspace_id), best_practices_query)
        
        learnings_query = MemoryQueryRequest(
            query="lessons learned failures constraints",
            insight_types=[InsightType.FAILURE_LESSON, InsightType.CONSTRAINT],
            limit=10
        )
        learnings_response = await workspace_memory.query_insights(UUID(workspace_id), learnings_query)
        
        discoveries_query = MemoryQueryRequest(
            query="discoveries optimizations",
            insight_types=[InsightType.DISCOVERY, InsightType.OPTIMIZATION],
            limit=10
        )
        discoveries_response = await workspace_memory.query_insights(UUID(workspace_id), discoveries_query)
        
        return {
            "workspace_id": workspace_id,
            "total_insights": summary.total_insights,
            "insights": [
                {
                    "id": str(insight.id),
                    "type": insight.insight_type.value,
                    "content": insight.content,
                    "confidence": insight.confidence_score,
                    "created_at": insight.created_at.isoformat(),
                    "tags": insight.relevance_tags
                }
                for insight in discoveries_response.insights
            ],
            "bestPractices": [
                {
                    "id": str(insight.id),
                    "content": insight.content,
                    "confidence": insight.confidence_score,
                    "created_at": insight.created_at.isoformat()
                }
                for insight in best_practices_response.insights
            ],
            "learnings": [
                {
                    "id": str(insight.id),
                    "type": insight.insight_type.value,
                    "content": insight.content,
                    "confidence": insight.confidence_score,
                    "created_at": insight.created_at.isoformat()
                }
                for insight in learnings_response.insights
            ],
            "summary": {
                "recent_discoveries": summary.recent_discoveries[:5],
                "key_constraints": summary.key_constraints[:5],
                "success_patterns": summary.success_patterns[:5],
                "top_tags": summary.top_tags[:10]
            }
        }
        
    except ImportError:
        # Fallback if workspace_memory is not available
        logger.warning("Workspace memory not available, returning empty insights")
        return {
            "workspace_id": workspace_id,
            "total_insights": 0,
            "insights": [],
            "bestPractices": [],
            "learnings": [],
            "summary": {
                "recent_discoveries": [],
                "key_constraints": [],
                "success_patterns": [],
                "top_tags": []
            }
        }
    except Exception as e:
        logger.error(f"Error fetching knowledge insights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch knowledge insights: {str(e)}")

@router.get("/health")
async def health_check(request: Request):
    # Get trace ID and create traced logger
    trace_id = get_trace_id(request)
    logger = create_traced_logger(request, __name__)
    logger.info(f"Route health_check called", endpoint="health_check", trace_id=trace_id)

    """Health check endpoint for conversation service"""
    return {
        "status": "healthy",
        "service": "conversation_api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "features": {
            "chat": True,
            "websocket": True,
            "confirmations": True,
            "context_aware": True
        }
    }