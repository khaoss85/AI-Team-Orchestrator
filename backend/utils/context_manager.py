"""
Context Manager - Universal context management for conversational AI
Handles context loading, summarization, and memory management across any domain
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from openai import OpenAI

from database import get_supabase_client
from models import Workspace

logger = logging.getLogger(__name__)

class ConversationContextManager:
    """
    Universal context manager that scales across any project domain.
    Implements progressive summarization to handle large conversation histories.
    """
    
    def __init__(self, workspace_id: str, max_context_tokens: int = 100000):
        self.workspace_id = workspace_id
        self.max_context_tokens = max_context_tokens
        self.supabase = get_supabase_client()
        self.openai_client = OpenAI()
        
        # Context windows
        self.active_window_size = 20  # Keep last 20 messages active
        self.summary_chunk_size = 10  # Summarize in chunks of 10 messages
        
    async def get_workspace_context(self) -> Dict[str, Any]:
        """
        Get comprehensive workspace context for AI processing.
        Universal and domain-agnostic.
        """
        try:
            context = {}
            
            # 1. Workspace Information
            workspace_data = await self._get_workspace_data()
            context["workspace"] = workspace_data
            
            # 2. Team Information
            team_data = await self._get_team_data()
            context["agents"] = team_data
            
            # 3. Recent Tasks and Activity
            tasks_data = await self._get_recent_tasks()
            context["recent_tasks"] = tasks_data
            
            # 4. Project Deliverables
            deliverables_data = await self._get_deliverables()
            context["deliverables"] = deliverables_data
            
            # 5. Budget and Resource Information
            budget_data = await self._get_budget_info(workspace_data)
            context["budget"] = budget_data
            
            # 6. Goals and Objectives
            goals_data = await self._get_goals()
            context["goals"] = goals_data
            
            # 7. Memory Insights
            memory_data = await self._get_memory_insights()
            context["memory_insights"] = memory_data
            
            # 8. Cross-workspace Learning (anonymized)
            learning_data = await self._get_learning_insights(workspace_data.get("domain"))
            context["learning_insights"] = learning_data
            
            logger.info(f"Loaded comprehensive context for workspace {self.workspace_id}")
            return context
            
        except Exception as e:
            logger.error(f"Failed to load workspace context: {e}")
            return self._get_minimal_context()
    
    async def manage_conversation_context(self, conversation_id: str) -> Dict[str, Any]:
        """
        Manage conversation context with progressive summarization.
        Keeps recent messages active and summarizes older content.
        """
        try:
            # Get current conversation state
            conversation = await self._get_conversation(conversation_id)
            
            if not conversation:
                return await self._create_new_conversation(conversation_id)
            
            # Get all messages for this conversation
            all_messages = await self._get_all_messages(conversation_id)
            
            # Check if we need to summarize
            if len(all_messages) > self.active_window_size:
                await self._perform_progressive_summarization(conversation_id, all_messages)
                # Reload conversation after summarization
                conversation = await self._get_conversation(conversation_id)
            
            # Prepare context for AI
            context = {
                "conversation_id": conversation_id,
                "active_messages": conversation.get("active_messages", []),
                "archived_summaries": conversation.get("archived_summaries", []),
                "total_messages": len(all_messages),
                "context_size_estimate": await self._estimate_context_size(conversation),
                "last_summarization": conversation.get("last_summarization"),
                "conversation_metadata": conversation.get("metadata", {})
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to manage conversation context: {e}")
            return {"error": str(e)}
    
    async def _perform_progressive_summarization(self, conversation_id: str, all_messages: List[Dict]) -> None:
        """
        Perform progressive summarization of older messages.
        Keeps conversation context manageable while preserving important information.
        """
        try:
            # Identify messages to summarize (older than active window)
            messages_to_keep = all_messages[-self.active_window_size:]
            messages_to_summarize = all_messages[:-self.active_window_size]
            
            if not messages_to_summarize:
                return
            
            # Group messages into chunks for summarization
            chunks = [
                messages_to_summarize[i:i + self.summary_chunk_size] 
                for i in range(0, len(messages_to_summarize), self.summary_chunk_size)
            ]
            
            new_summaries = []
            
            for chunk in chunks:
                summary = await self._create_message_chunk_summary(chunk)
                new_summaries.append(summary)
            
            # Update conversation with new summaries and active messages
            conversation_updates = {
                "active_messages": [self._serialize_message(msg) for msg in messages_to_keep],
                "archived_summaries": new_summaries,
                "last_summarization": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            workspace_id, chat_id = conversation_id.split("_", 1)
            
            self.supabase.table("conversations")\
                .update(conversation_updates)\
                .eq("workspace_id", workspace_id)\
                .eq("chat_id", chat_id)\
                .execute()
            
            logger.info(f"Summarized {len(messages_to_summarize)} messages into {len(new_summaries)} summaries")
            
        except Exception as e:
            logger.error(f"Failed to perform progressive summarization: {e}")
    
    async def _create_message_chunk_summary(self, message_chunk: List[Dict]) -> Dict[str, Any]:
        """
        Create AI-driven summary of a message chunk.
        Preserves key information while reducing token count.
        """
        try:
            # Prepare messages for summarization
            conversation_text = self._format_messages_for_summarization(message_chunk)
            
            # AI-driven summarization
            summary_prompt = f"""
            Summarize this conversation chunk preserving key information:
            
            CONVERSATION:
            {conversation_text}
            
            Create a concise summary that includes:
            - Main topics discussed
            - Important decisions made
            - Actions taken or planned
            - Key insights or conclusions
            - Any unresolved questions or issues
            
            Focus on actionable information and project-relevant content.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert at summarizing project conversations while preserving key actionable information."},
                    {"role": "user", "content": summary_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            summary_text = response.choices[0].message.content
            
            # Extract metadata from chunk
            chunk_metadata = self._extract_chunk_metadata(message_chunk)
            
            return {
                "id": str(uuid4()),
                "time_period": {
                    "start": message_chunk[0]["created_at"],
                    "end": message_chunk[-1]["created_at"]
                },
                "message_count": len(message_chunk),
                "summary": summary_text,
                "key_actions": chunk_metadata["key_actions"],
                "tools_used": chunk_metadata["tools_used"],
                "participants": chunk_metadata["participants"],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to create message chunk summary: {e}")
            return {
                "id": str(uuid4()),
                "summary": f"Failed to summarize chunk of {len(message_chunk)} messages",
                "error": str(e),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
    
    def _format_messages_for_summarization(self, messages: List[Dict]) -> str:
        """Format messages into readable text for AI summarization"""
        formatted_messages = []
        
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            timestamp = msg.get("created_at", "")
            tools_used = msg.get("tools_used", [])
            
            message_text = f"[{timestamp}] {role.upper()}: {content}"
            
            if tools_used:
                message_text += f" [Tools: {', '.join(tools_used)}]"
            
            formatted_messages.append(message_text)
        
        return "\n\n".join(formatted_messages)
    
    def _extract_chunk_metadata(self, message_chunk: List[Dict]) -> Dict[str, Any]:
        """Extract key metadata from message chunk"""
        key_actions = []
        tools_used = set()
        participants = set()
        
        for msg in message_chunk:
            # Extract participants
            participants.add(msg.get("role", "unknown"))
            
            # Extract tools used
            msg_tools = msg.get("tools_used", [])
            tools_used.update(msg_tools)
            
            # Extract actions performed
            actions = msg.get("actions_performed", [])
            for action in actions:
                if action.get("success", False):
                    key_actions.append({
                        "action": action.get("action_type", "unknown"),
                        "description": action.get("description", ""),
                        "timestamp": msg.get("created_at", "")
                    })
        
        return {
            "key_actions": key_actions,
            "tools_used": list(tools_used),
            "participants": list(participants)
        }
    
    async def _estimate_context_size(self, conversation: Dict[str, Any]) -> int:
        """
        Estimate total token count for conversation context.
        Helps manage context window limits.
        """
        try:
            # Simple estimation: ~4 characters per token
            active_messages = conversation.get("active_messages", [])
            archived_summaries = conversation.get("archived_summaries", [])
            
            active_chars = sum(len(json.dumps(msg)) for msg in active_messages)
            summary_chars = sum(len(summary.get("summary", "")) for summary in archived_summaries)
            
            estimated_tokens = (active_chars + summary_chars) // 4
            
            return estimated_tokens
            
        except Exception as e:
            logger.error(f"Failed to estimate context size: {e}")
            return 0
    
    def _serialize_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize message for storage, removing large objects"""
        return {
            "id": message.get("id"),
            "role": message.get("role"),
            "content": message.get("content", "")[:2000],  # Limit content size
            "tools_used": message.get("tools_used", []),
            "created_at": message.get("created_at"),
            "metadata": {
                "has_artifacts": bool(message.get("artifacts_generated")),
                "action_count": len(message.get("actions_performed", []))
            }
        }
    
    # Data Loading Methods
    
    async def _get_workspace_data(self) -> Dict[str, Any]:
        """Get workspace information"""
        try:
            result = self.supabase.table("workspaces")\
                .select("*")\
                .eq("id", self.workspace_id)\
                .execute()
            
            if result.data:
                return result.data[0]
            else:
                return self._get_default_workspace_data()
                
        except Exception as e:
            logger.error(f"Failed to get workspace data: {e}")
            return self._get_default_workspace_data()
    
    async def _get_team_data(self) -> List[Dict[str, Any]]:
        """Get team/agents information"""
        try:
            result = self.supabase.table("agents")\
                .select("*")\
                .eq("workspace_id", self.workspace_id)\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get team data: {e}")
            return []
    
    async def _get_recent_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent tasks and activities"""
        try:
            # Get tasks from last 30 days
            thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
            
            result = self.supabase.table("tasks")\
                .select("*")\
                .eq("workspace_id", self.workspace_id)\
                .gte("created_at", thirty_days_ago.isoformat())\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get recent tasks: {e}")
            return []
    
    async def _get_deliverables(self) -> List[Dict[str, Any]]:
        """Get project deliverables"""
        try:
            result = self.supabase.table("deliverables")\
                .select("*")\
                .eq("workspace_id", self.workspace_id)\
                .order("created_at", desc=True)\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get deliverables: {e}")
            return []
    
    async def _get_budget_info(self, workspace_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get budget and resource information"""
        try:
            return {
                "max_budget": workspace_data.get("max_budget", 10000),
                "used": workspace_data.get("budget_used", 0),
                "currency": workspace_data.get("currency", "EUR"),
                "budget_period": workspace_data.get("budget_period", "project"),
                "last_updated": workspace_data.get("budget_updated_at")
            }
            
        except Exception as e:
            logger.error(f"Failed to get budget info: {e}")
            return {"max_budget": 10000, "used": 0, "currency": "EUR"}
    
    async def _get_goals(self) -> List[Dict[str, Any]]:
        """Get workspace goals and objectives"""
        try:
            result = self.supabase.table("workspace_goals")\
                .select("*")\
                .eq("workspace_id", self.workspace_id)\
                .order("priority", desc=True)\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get goals: {e}")
            return []
    
    async def _get_memory_insights(self) -> List[Dict[str, Any]]:
        """Get AI memory insights for the workspace"""
        try:
            # This would integrate with AI Memory Intelligence system
            # For now, return structured insights
            
            # Get completed tasks for insight generation
            completed_tasks = self.supabase.table("tasks")\
                .select("*")\
                .eq("workspace_id", self.workspace_id)\
                .eq("status", "completed")\
                .order("created_at", desc=True)\
                .limit(20)\
                .execute()
            
            tasks = completed_tasks.data or []
            
            # Generate simple insights
            insights = []
            
            if len(tasks) > 5:
                insights.append({
                    "type": "productivity",
                    "insight": f"Team has completed {len(tasks)} tasks recently, showing good productivity",
                    "confidence": 0.8,
                    "actionable": "Consider scaling up for increased capacity"
                })
            
            if tasks:
                avg_duration = sum(task.get("estimated_hours", 4) for task in tasks) / len(tasks)
                insights.append({
                    "type": "estimation",
                    "insight": f"Average task duration is {avg_duration:.1f} hours",
                    "confidence": 0.7,
                    "actionable": "Use this data for better future estimations"
                })
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get memory insights: {e}")
            return []
    
    async def _get_learning_insights(self, domain: str = None) -> List[Dict[str, Any]]:
        """Get cross-workspace learning insights (anonymized)"""
        try:
            if not domain:
                return []
            
            result = self.supabase.table("cross_workspace_insights")\
                .select("*")\
                .eq("domain", domain)\
                .gte("confidence_score", 70)\
                .order("confidence_score", desc=True)\
                .limit(5)\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get learning insights: {e}")
            return []
    
    # Helper methods for conversation management
    
    async def _get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation record"""
        try:
            workspace_id, chat_id = conversation_id.split("_", 1)
            
            result = self.supabase.table("conversations")\
                .select("*")\
                .eq("workspace_id", workspace_id)\
                .eq("chat_id", chat_id)\
                .execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Failed to get conversation: {e}")
            return None
    
    async def _get_all_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all messages for conversation"""
        try:
            result = self.supabase.table("conversation_messages")\
                .select("*")\
                .eq("conversation_id", conversation_id)\
                .order("created_at", desc=False)\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get all messages: {e}")
            return []
    
    async def _create_new_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """Create new conversation record"""
        try:
            workspace_id, chat_id = conversation_id.split("_", 1)
            
            conversation_data = {
                "workspace_id": workspace_id,
                "chat_id": chat_id,
                "schema_version": "v2025-06-A",
                "title": f"Conversation: {chat_id}",
                "description": f"AI assistant conversation for {chat_id}",
                "active_messages": [],
                "archived_summaries": [],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            result = self.supabase.table("conversations").insert(conversation_data).execute()
            
            return conversation_data
            
        except Exception as e:
            logger.error(f"Failed to create new conversation: {e}")
            return {"error": str(e)}
    
    def _get_minimal_context(self) -> Dict[str, Any]:
        """Return minimal context for error cases"""
        return {
            "workspace": self._get_default_workspace_data(),
            "agents": [],
            "recent_tasks": [],
            "deliverables": [],
            "budget": {"max_budget": 10000, "used": 0, "currency": "EUR"},
            "goals": [],
            "memory_insights": [],
            "learning_insights": []
        }
    
    def _get_default_workspace_data(self) -> Dict[str, Any]:
        """Default workspace data for error cases"""
        return {
            "id": self.workspace_id,
            "name": "Default Workspace",
            "domain": "general",
            "description": "AI-driven project workspace",
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat()
        }

# Global function for easy access
async def get_workspace_context(workspace_id: str) -> Dict[str, Any]:
    """
    Global function to get workspace context.
    Used throughout the application for consistent context loading.
    """
    context_manager = ConversationContextManager(workspace_id)
    return await context_manager.get_workspace_context()