"""
Memory System - Pillar 6: Memory System Implementation
Provides context retention, learning patterns, and memory-driven decision making.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import UUID, uuid4
from openai import AsyncOpenAI

from database import get_supabase_client, supabase_retry

logger = logging.getLogger(__name__)

class MemorySystem:
    """
    Memory System for context retention and learning (Pillar 6: Memory System)
    
    Provides:
    - Context storage and retrieval
    - Learning pattern recognition
    - Memory-driven insights
    - Historical context for decisions
    """
    
    def __init__(self, openai_client: AsyncOpenAI = None):
        self.openai_client = openai_client or AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.supabase = get_supabase_client()
        
        # Configuration
        self.memory_retention_days = int(os.getenv("MEMORY_RETENTION_DAYS", "30"))
        self.learning_threshold = float(os.getenv("LEARNING_THRESHOLD", "0.7"))
        self.max_context_entries = int(os.getenv("MAX_CONTEXT_ENTRIES", "100"))
        
        logger.info("🧠 Memory System initialized")
    
    @supabase_retry(max_attempts=3)
    async def store_context(self, workspace_id: UUID, context: str, importance: str = "medium", 
                          context_type: str = "general", metadata: Optional[Dict] = None) -> str:
        """Store context in memory with importance weighting"""
        try:
            context_id = str(uuid4())
            
            # AI-driven importance scoring
            importance_score = await self._calculate_importance_score(context, importance)
            
            context_data = {
                "id": context_id,
                "workspace_id": str(workspace_id),
                "context": context,
                "context_type": context_type,
                "importance": importance,
                "importance_score": importance_score,
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(days=self.memory_retention_days)).isoformat()
            }
            
            response = self.supabase.table("memory_context").insert(context_data).execute()
            
            if response.data:
                logger.info(f"💾 Stored context: {context_id} (importance: {importance_score:.2f})")
                
                # Trigger learning pattern update
                await self._update_learning_patterns(workspace_id, context, context_type)
                
                return context_id
            
            raise Exception("No data returned from context storage")
            
        except Exception as e:
            logger.error(f"Failed to store context: {e}")
            raise
    
    @supabase_retry(max_attempts=3)
    async def retrieve_context(self, workspace_id: UUID, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve relevant context based on query"""
        try:
            # AI-driven semantic search for context
            relevant_contexts = await self._semantic_context_search(workspace_id, query, limit)
            
            logger.info(f"🔍 Retrieved {len(relevant_contexts)} relevant contexts for query")
            return relevant_contexts
            
        except Exception as e:
            logger.error(f"Failed to retrieve context: {e}")
            return []
    
    @supabase_retry(max_attempts=3) 
    async def get_memory_insights(self, workspace_id: UUID) -> Dict[str, Any]:
        """Get memory insights and patterns for workspace"""
        try:
            # Get recent context
            recent_response = self.supabase.table("memory_context") \
                .select("*") \
                .eq("workspace_id", str(workspace_id)) \
                .gte("created_at", (datetime.utcnow() - timedelta(days=7)).isoformat()) \
                .order("importance_score", desc=True) \
                .limit(self.max_context_entries) \
                .execute()
            
            # Get learning patterns
            patterns_response = self.supabase.table("learning_patterns") \
                .select("*") \
                .eq("workspace_id", str(workspace_id)) \
                .order("pattern_strength", desc=True) \
                .limit(20) \
                .execute()
            
            insights = {
                "total_context_entries": len(recent_response.data),
                "high_importance_entries": len([c for c in recent_response.data if c["importance_score"] > 0.8]),
                "learning_patterns": patterns_response.data,
                "context_types": self._analyze_context_types(recent_response.data),
                "memory_health": self._calculate_memory_health(recent_response.data),
                "retention_rate": self._calculate_retention_rate(workspace_id)
            }
            
            logger.info(f"🧠 Generated memory insights for workspace {workspace_id}")
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get memory insights: {e}")
            return {}
    
    async def _calculate_importance_score(self, context: str, importance: str) -> float:
        """AI-driven importance scoring"""
        try:
            # Base score from importance level
            base_scores = {"low": 0.3, "medium": 0.6, "high": 0.9, "critical": 1.0}
            base_score = base_scores.get(importance, 0.6)
            
            # AI enhancement of importance
            enhancement_prompt = f"""
            Analyze the importance of this context for future decision making:
            
            Context: {context}
            Base importance: {importance}
            
            Rate the long-term value of this context on a scale of 0.0 to 1.0 considering:
            - Actionability for future decisions
            - Business impact potential  
            - Learning value for AI system
            - Relevance to project goals
            
            Return only a number between 0.0 and 1.0.
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": enhancement_prompt}],
                temperature=0.1,
                max_tokens=50
            )
            
            try:
                ai_score = float(response.choices[0].message.content.strip())
                # Blend base score with AI score
                final_score = (base_score * 0.4) + (ai_score * 0.6)
                return min(max(final_score, 0.0), 1.0)
            except:
                return base_score
                
        except Exception as e:
            logger.warning(f"AI importance scoring failed, using base score: {e}")
            return base_scores.get(importance, 0.6)
    
    async def _semantic_context_search(self, workspace_id: UUID, query: str, limit: int) -> List[Dict[str, Any]]:
        """AI-driven semantic search for relevant context"""
        try:
            # Get all context for workspace (limited by retention period)
            response = self.supabase.table("memory_context") \
                .select("*") \
                .eq("workspace_id", str(workspace_id)) \
                .gte("created_at", (datetime.utcnow() - timedelta(days=self.memory_retention_days)).isoformat()) \
                .order("importance_score", desc=True) \
                .execute()
            
            contexts = response.data
            
            if not contexts:
                return []
            
            # AI-driven relevance scoring
            relevance_prompt = f"""
            Query: {query}
            
            Rate the relevance of each context to this query on a scale of 0.0 to 1.0:
            
            {json.dumps([{"id": c["id"], "context": c["context"][:200]} for c in contexts[:20]], indent=2)}
            
            Return a JSON object with context IDs as keys and relevance scores as values.
            Only include contexts with relevance > 0.3.
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": relevance_prompt}],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            relevance_scores = json.loads(response.choices[0].message.content)
            
            # Sort contexts by relevance and return top results
            relevant_contexts = []
            for context in contexts:
                context_id = context["id"]
                if context_id in relevance_scores:
                    context["relevance_score"] = relevance_scores[context_id]
                    relevant_contexts.append(context)
            
            relevant_contexts.sort(key=lambda x: x["relevance_score"], reverse=True)
            return relevant_contexts[:limit]
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            # Fallback to simple text matching
            return self._simple_text_search(workspace_id, query, limit)
    
    def _simple_text_search(self, workspace_id: UUID, query: str, limit: int) -> List[Dict[str, Any]]:
        """Fallback text search when AI search fails"""
        try:
            # Simple text matching fallback
            response = self.supabase.table("memory_context") \
                .select("*") \
                .eq("workspace_id", str(workspace_id)) \
                .ilike("context", f"%{query}%") \
                .order("importance_score", desc=True) \
                .limit(limit) \
                .execute()
            
            return response.data
            
        except Exception as e:
            logger.error(f"Simple text search failed: {e}")
            return []
    
    async def _update_learning_patterns(self, workspace_id: UUID, context: str, context_type: str):
        """Update learning patterns based on new context"""
        try:
            # Simple pattern tracking
            pattern_key = f"{context_type}_frequency"
            
            # Get or create pattern
            existing = self.supabase.table("learning_patterns") \
                .select("*") \
                .eq("workspace_id", str(workspace_id)) \
                .eq("pattern_key", pattern_key) \
                .execute()
            
            if existing.data:
                # Update existing pattern
                pattern = existing.data[0]
                new_count = pattern["occurrence_count"] + 1
                new_strength = min(new_count / 100.0, 1.0)  # Normalize to 0-1
                
                self.supabase.table("learning_patterns") \
                    .update({
                        "occurrence_count": new_count,
                        "pattern_strength": new_strength,
                        "last_seen": datetime.utcnow().isoformat()
                    }) \
                    .eq("id", pattern["id"]) \
                    .execute()
            else:
                # Create new pattern
                pattern_data = {
                    "id": str(uuid4()),
                    "workspace_id": str(workspace_id),
                    "pattern_key": pattern_key,
                    "pattern_type": "context_frequency",
                    "occurrence_count": 1,
                    "pattern_strength": 0.01,
                    "metadata": {"context_type": context_type},
                    "first_seen": datetime.utcnow().isoformat(),
                    "last_seen": datetime.utcnow().isoformat()
                }
                
                self.supabase.table("learning_patterns").insert(pattern_data).execute()
            
        except Exception as e:
            logger.warning(f"Learning pattern update failed: {e}")
    
    def _analyze_context_types(self, contexts: List[Dict]) -> Dict[str, int]:
        """Analyze distribution of context types"""
        type_counts = {}
        for context in contexts:
            context_type = context.get("context_type", "general")
            type_counts[context_type] = type_counts.get(context_type, 0) + 1
        return type_counts
    
    def _calculate_memory_health(self, contexts: List[Dict]) -> Dict[str, float]:
        """Calculate memory system health metrics"""
        if not contexts:
            return {"score": 0.0, "status": "empty"}
        
        # Calculate health based on context diversity and importance
        avg_importance = sum(c["importance_score"] for c in contexts) / len(contexts)
        type_diversity = len(set(c.get("context_type", "general") for c in contexts))
        
        health_score = (avg_importance * 0.7) + (min(type_diversity / 5.0, 1.0) * 0.3)
        
        status = "excellent" if health_score > 0.8 else \
                "good" if health_score > 0.6 else \
                "fair" if health_score > 0.4 else "poor"
        
        return {"score": health_score, "status": status}
    
    def _calculate_retention_rate(self, workspace_id: UUID) -> float:
        """Calculate context retention rate"""
        try:
            # Simple retention rate calculation
            total_response = self.supabase.table("memory_context") \
                .select("id", count="exact") \
                .eq("workspace_id", str(workspace_id)) \
                .execute()
            
            active_response = self.supabase.table("memory_context") \
                .select("id", count="exact") \
                .eq("workspace_id", str(workspace_id)) \
                .gte("created_at", (datetime.utcnow() - timedelta(days=self.memory_retention_days)).isoformat()) \
                .execute()
            
            total_count = total_response.count or 0
            active_count = active_response.count or 0
            
            return (active_count / total_count) if total_count > 0 else 1.0
            
        except Exception as e:
            logger.warning(f"Retention rate calculation failed: {e}")
            return 0.0

# Global memory system instance
memory_system = MemorySystem()

# Convenience functions
async def store_context(workspace_id: UUID, context: str, importance: str = "medium", 
                       context_type: str = "general", metadata: Optional[Dict] = None) -> str:
    return await memory_system.store_context(workspace_id, context, importance, context_type, metadata)

async def retrieve_context(workspace_id: UUID, query: str, limit: int = 10) -> List[Dict[str, Any]]:
    return await memory_system.retrieve_context(workspace_id, query, limit)

async def get_memory_insights(workspace_id: UUID) -> Dict[str, Any]:
    return await memory_system.get_memory_insights(workspace_id)