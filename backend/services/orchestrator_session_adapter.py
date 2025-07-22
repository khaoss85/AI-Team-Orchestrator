# backend/services/orchestrator_session_adapter.py
"""
Orchestrator Session Adapter - Integration Bridge
Connects OpenAI Agents SDK Sessions with our Unified Memory Engine
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional, Protocol
from uuid import UUID
from datetime import datetime
from pathlib import Path

# SDK Integration
try:
    from agents import SQLiteSession
    from agents.memory import Session as SDKSession
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    SQLiteSession = None
    SDKSession = None

# Our systems
from services.unified_memory_engine import unified_memory_engine
from database import supabase

logger = logging.getLogger(__name__)

class OrchestratorSessionAdapter:
    """
    🎯 Orchestrator Session Adapter
    
    Bridges OpenAI Agents SDK Session memory with our Unified Memory Engine.
    
    Features:
    - Agent-scoped SQLite sessions (SDK native)
    - Workspace-wide memory consolidation (our system)
    - Automatic context synchronization
    - AI-driven cross-session insights
    """
    
    def __init__(self):
        self.agent_sessions: Dict[str, SQLiteSession] = {}
        self.session_workspace_mapping: Dict[str, str] = {}
        self.db_path = Path("agent_sessions.db")
        
    async def get_agent_session(
        self, 
        agent_id: str, 
        workspace_id: str,
        task_id: Optional[str] = None
    ) -> Optional[SQLiteSession]:
        """
        🤖 Get or create an SDK session for a specific agent
        
        Creates agent-scoped SQLite sessions with SDK 0.1.0
        """
        if not SDK_AVAILABLE:
            logger.warning(f"SDK sessions not available - using fallback for agent {agent_id}")
            session_id = f"agent_{agent_id}"
            if task_id:
                session_id = f"agent_{agent_id}_task_{task_id}"
            self.session_workspace_mapping[session_id] = workspace_id
            return None
        
        session_id = f"agent_{agent_id}"
        if task_id:
            session_id = f"agent_{agent_id}_task_{task_id}"
        
        # Check if session already exists
        if session_id in self.agent_sessions:
            return self.agent_sessions[session_id]
        
        try:
            # Create new SQLiteSession for this agent
            session_db_path = f"sessions/{session_id}.db"
            session = SQLiteSession(db_path=session_db_path)
            
            self.agent_sessions[session_id] = session
            self.session_workspace_mapping[session_id] = workspace_id
            
            logger.info(f"✅ Created SDK session for agent {agent_id} (session: {session_id})")
            return session
            
        except Exception as e:
            logger.error(f"❌ Failed to create SDK session for agent {agent_id}: {e}")
            return None
    
    async def sync_session_to_unified_memory(
        self, 
        session_id: str, 
        agent_id: str, 
        workspace_id: str
    ) -> bool:
        """
        🔄 Sync SDK session data to our Unified Memory Engine
        
        Process:
        1. Extract conversation history from SDK session
        2. Transform to our memory format
        3. Store in Supabase via unified memory engine
        4. Trigger AI analysis for insights
        """
        if session_id not in self.agent_sessions:
            return False
            
        try:
            session = self.agent_sessions[session_id]
            
            # Get conversation history from SDK session
            conversation_items = await session.get_items()
            
            if not conversation_items:
                return True  # Nothing to sync
            
            # Transform to our memory context format
            memory_context = {
                "session_id": session_id,
                "agent_id": agent_id,
                "workspace_id": workspace_id,
                "conversation_history": conversation_items,
                "sync_timestamp": datetime.now().isoformat(),
                "source": "sdk_session"
            }
            
            # Store in unified memory engine
            await unified_memory_engine.store_context(
                workspace_id=workspace_id,
                context_type="agent_conversation",
                context_data=memory_context,
                metadata={
                    "agent_id": agent_id,
                    "session_id": session_id,
                    "conversation_length": len(conversation_items)
                }
            )
            
            # Trigger AI analysis for cross-session insights
            await self._analyze_session_patterns(workspace_id, agent_id, conversation_items)
            
            logger.info(f"✅ Synced session {session_id} to unified memory ({len(conversation_items)} items)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to sync session {session_id}: {e}")
            return False
    
    async def _analyze_session_patterns(
        self, 
        workspace_id: str, 
        agent_id: str, 
        conversation_items: List[Dict[str, Any]]
    ):
        """
        🧠 AI-driven analysis of conversation patterns
        
        Extracts:
        - Key topics discussed
        - Decision points
        - Unresolved questions
        - Cross-agent collaboration opportunities
        """
        try:
            # Extract conversation summary
            conversation_text = self._extract_conversation_text(conversation_items)
            
            if len(conversation_text) < 50:  # Skip very short conversations
                return
            
            # Query unified memory engine for analysis
            analysis_result = await unified_memory_engine.analyze_context_patterns(
                workspace_id=workspace_id,
                context_data={
                    "conversation": conversation_text,
                    "agent_id": agent_id,
                    "message_count": len(conversation_items)
                },
                analysis_type="conversation_insights"
            )
            
            # Store insights for orchestrator use
            if analysis_result:
                await self._store_conversation_insights(
                    workspace_id, agent_id, analysis_result
                )
                
        except Exception as e:
            logger.error(f"❌ Failed to analyze session patterns: {e}")
    
    def _extract_conversation_text(self, items: List[Dict[str, Any]]) -> str:
        """Extract readable text from conversation items"""
        texts = []
        for item in items:
            if item.get("role") == "user":
                texts.append(f"User: {item.get('content', '')}")
            elif item.get("role") == "assistant":
                texts.append(f"Assistant: {item.get('content', '')}")
        return "\n".join(texts)
    
    async def _store_conversation_insights(
        self, 
        workspace_id: str, 
        agent_id: str, 
        insights: Dict[str, Any]
    ):
        """Store AI-generated insights in Supabase"""
        try:
            insight_record = {
                "workspace_id": workspace_id,
                "agent_id": agent_id,
                "insight_type": "conversation_analysis",
                "insight_data": insights,
                "confidence_score": insights.get("confidence", 0.8),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            await supabase.table("workspace_insights").insert(insight_record).execute()
            
        except Exception as e:
            logger.error(f"❌ Failed to store conversation insights: {e}")
    
    async def get_workspace_conversation_summary(
        self, 
        workspace_id: str
    ) -> Dict[str, Any]:
        """
        📊 Get consolidated conversation summary for entire workspace
        
        Combines:
        - All agent conversations
        - Cross-session patterns
        - Key insights and decisions
        """
        try:
            # Get all sessions for this workspace
            workspace_sessions = {
                sid: session for sid, session in self.agent_sessions.items()
                if self.session_workspace_mapping.get(sid) == workspace_id
            }
            
            summary = {
                "workspace_id": workspace_id,
                "total_sessions": len(workspace_sessions),
                "agent_summaries": {},
                "cross_session_insights": {},
                "last_updated": datetime.now().isoformat()
            }
            
            # Summarize each agent's conversations
            for session_id, session in workspace_sessions.items():
                agent_id = session_id.replace("agent_", "").split("_task_")[0]
                items = await session.get_items()
                
                summary["agent_summaries"][agent_id] = {
                    "message_count": len(items),
                    "last_activity": self._get_last_activity(items),
                    "session_id": session_id
                }
            
            # Get cross-session insights from unified memory
            insights = await unified_memory_engine.query_context(
                workspace_id=workspace_id,
                query="conversation insights and patterns",
                context_types=["agent_conversation"]
            )
            
            summary["cross_session_insights"] = insights
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Failed to get workspace conversation summary: {e}")
            return {"workspace_id": workspace_id, "error": str(e)}
    
    def _get_last_activity(self, items: List[Dict[str, Any]]) -> Optional[str]:
        """Extract timestamp of last activity from conversation items"""
        if not items:
            return None
        
        # Look for timestamp in last item
        last_item = items[-1]
        return last_item.get("timestamp") or datetime.now().isoformat()
    
    async def cleanup_old_sessions(self, days_old: int = 7):
        """
        🧹 Cleanup old sessions to prevent memory bloat
        
        Strategy:
        - Keep active workspace sessions
        - Archive old sessions to unified memory
        - Clean up SQLite files
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            sessions_to_cleanup = []
            for session_id, session in self.agent_sessions.items():
                # Check if session is old and inactive
                items = await session.get_items(limit=1)
                if items:
                    last_activity = self._get_last_activity(items)
                    if last_activity and datetime.fromisoformat(last_activity.replace('Z', '+00:00')) < cutoff_date:
                        sessions_to_cleanup.append(session_id)
            
            # Archive and cleanup
            for session_id in sessions_to_cleanup:
                workspace_id = self.session_workspace_mapping.get(session_id)
                if workspace_id:
                    # Sync to unified memory before cleanup
                    agent_id = session_id.replace("agent_", "").split("_task_")[0]
                    await self.sync_session_to_unified_memory(session_id, agent_id, workspace_id)
                
                # Close and remove session
                session = self.agent_sessions[session_id]
                session.close()
                del self.agent_sessions[session_id]
                del self.session_workspace_mapping[session_id]
            
            logger.info(f"🧹 Cleaned up {len(sessions_to_cleanup)} old sessions")
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup old sessions: {e}")

# Global instance
orchestrator_session_adapter = OrchestratorSessionAdapter()