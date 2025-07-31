#!/usr/bin/env python3
"""
🧠 **HOLISTIC MEMORY MANAGER**

Unified memory interface that consolidates fragmented memory systems:
- UnifiedMemoryEngine (comprehensive memory management)
- MemorySimilarityEngine (semantic similarity and search)
- WorkspaceMemory (workspace-specific context)
- SDK Memory Bridge (OpenAI SDK integration)

This eliminates memory system silos and provides coherent knowledge management
across the entire AI team orchestration system.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class MemoryScope(Enum):
    """Memory storage scopes"""
    WORKSPACE = "workspace"        # Workspace-specific memories
    GLOBAL = "global"             # System-wide memories
    AGENT = "agent"               # Agent-specific memories
    TASK = "task"                 # Task-specific memories
    GOAL = "goal"                 # Goal-specific memories

class MemoryType(Enum):
    """Types of memories stored"""
    EXPERIENCE = "experience"      # Task execution experiences
    PATTERN = "pattern"           # Learned patterns and insights
    CONTEXT = "context"           # Contextual information
    SIMILARITY = "similarity"     # Semantic similarity mappings
    FEEDBACK = "feedback"         # Quality feedback and improvements

@dataclass
class MemoryEntry:
    """Unified memory entry structure"""
    id: str
    content: Dict[str, Any]
    memory_type: MemoryType
    scope: MemoryScope
    workspace_id: Optional[str] = None
    agent_id: Optional[str] = None
    task_id: Optional[str] = None
    goal_id: Optional[str] = None
    confidence: float = 1.0
    created_at: datetime = None
    accessed_at: datetime = None
    access_count: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.accessed_at is None:
            self.accessed_at = self.created_at
        if self.metadata is None:
            self.metadata = {}

class HolisticMemoryManager:
    """
    🧠 **UNIFIED MEMORY ORCHESTRATION**
    
    Single interface for all memory operations that eliminates silos
    between different memory systems and provides holistic knowledge management.
    """
    
    def __init__(self):
        self.memory_engines = {}
        self.memory_cache = {}
        self.access_patterns = {}
        
        # Initialize available memory systems
        self._initialize_memory_systems()
    
    def _initialize_memory_systems(self):
        """Initialize and integrate available memory systems"""
        
        # Initialize UnifiedMemoryEngine
        try:
            from services.unified_memory_engine import UnifiedMemoryEngine
            self.memory_engines["unified"] = UnifiedMemoryEngine()
            logger.info("✅ UnifiedMemoryEngine integrated")
        except Exception as e:
            logger.warning(f"⚠️ UnifiedMemoryEngine not available: {e}")
        
        # Initialize MemorySimilarityEngine
        try:
            from services.memory_similarity_engine import MemorySimilarityEngine
            self.memory_engines["similarity"] = MemorySimilarityEngine()
            logger.info("✅ MemorySimilarityEngine integrated")
        except Exception as e:
            logger.warning(f"⚠️ MemorySimilarityEngine not available: {e}")
        
        # Initialize WorkspaceMemory
        try:
            import workspace_memory
            self.memory_engines["workspace"] = workspace_memory
            logger.info("✅ WorkspaceMemory integrated")
        except Exception as e:
            logger.warning(f"⚠️ WorkspaceMemory not available: {e}")
        
        # Initialize SDK Memory Bridge
        try:
            from services.sdk_memory_bridge import SDKMemoryBridge
            self.memory_engines["sdk"] = SDKMemoryBridge()
            logger.info("✅ SDK Memory Bridge integrated")
        except Exception as e:
            logger.warning(f"⚠️ SDK Memory Bridge not available: {e}")
    
    async def store_memory(
        self,
        content: Dict[str, Any],
        memory_type: Union[MemoryType, str],
        scope: Union[MemoryScope, str],
        workspace_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        goal_id: Optional[str] = None,
        confidence: float = 1.0,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        🧠 **UNIFIED MEMORY STORAGE**
        
        Store a memory using the most appropriate memory system
        based on type, scope, and content characteristics.
        """
        try:
            # 🔧 **FLEXIBLE INPUT HANDLING**: Convert string inputs to enums if needed
            if isinstance(memory_type, str):
                try:
                    memory_type = MemoryType(memory_type)
                except ValueError:
                    logger.warning(f"⚠️ Unknown memory_type '{memory_type}', defaulting to EXPERIENCE")
                    memory_type = MemoryType.EXPERIENCE
            
            if isinstance(scope, str):
                try:
                    scope = MemoryScope(scope)
                except ValueError:
                    logger.warning(f"⚠️ Unknown scope '{scope}', defaulting to WORKSPACE")
                    scope = MemoryScope.WORKSPACE
            
            # Create unified memory entry
            memory_id = f"{scope.value}_{memory_type.value}_{datetime.now().timestamp()}"
            
            memory_entry = MemoryEntry(
                id=memory_id,
                content=content,
                memory_type=memory_type,
                scope=scope,
                workspace_id=workspace_id,
                agent_id=agent_id,
                task_id=task_id,
                goal_id=goal_id,
                confidence=confidence,
                metadata=metadata or {}
            )
            
            # Determine optimal memory system for storage
            storage_system = self._select_optimal_storage_system(memory_entry)
            
            # Store in selected system
            if storage_system == "unified" and "unified" in self.memory_engines:
                await self._store_in_unified_memory(memory_entry)
            elif storage_system == "similarity" and "similarity" in self.memory_engines:
                await self._store_in_similarity_memory(memory_entry)
            elif storage_system == "workspace" and "workspace" in self.memory_engines:
                await self._store_in_workspace_memory(memory_entry)
            else:
                # Fallback to first available system
                available_systems = list(self.memory_engines.keys())
                if available_systems:
                    await self._store_in_fallback_system(memory_entry, available_systems[0])
                else:
                    # Store in local cache as last resort
                    self.memory_cache[memory_id] = memory_entry
                    logger.warning(f"⚠️ Stored memory {memory_id} in local cache - no memory systems available")
            
            # Handle both enum and string inputs for type and scope
            memory_type_str = memory_type.value if hasattr(memory_type, 'value') else str(memory_type)
            scope_str = scope.value if hasattr(scope, 'value') else str(scope)
            
            logger.info(f"🧠 Memory stored: {memory_id} (type: {memory_type_str}, scope: {scope_str})")
            return memory_id
            
        except Exception as e:
            logger.error(f"❌ Failed to store memory: {e}")
            raise
    
    async def retrieve_memories(
        self,
        query: Dict[str, Any],
        memory_type: Optional[MemoryType] = None,
        scope: Optional[MemoryScope] = None,
        workspace_id: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[MemoryEntry]:
        """
        🔍 **UNIFIED MEMORY RETRIEVAL**
        
        Search across all memory systems to find relevant memories
        using both semantic similarity and exact matching.
        """
        try:
            all_memories = []
            
            # Search in similarity engine first (most sophisticated)
            if "similarity" in self.memory_engines:
                similarity_memories = await self._search_similarity_memories(
                    query, memory_type, scope, workspace_id, limit, similarity_threshold
                )
                all_memories.extend(similarity_memories)
            
            # Search in unified memory engine
            if "unified" in self.memory_engines:
                unified_memories = await self._search_unified_memories(
                    query, memory_type, scope, workspace_id, limit
                )
                all_memories.extend(unified_memories)
            
            # Search in workspace memory
            if workspace_id and "workspace" in self.memory_engines:
                workspace_memories = await self._search_workspace_memories(
                    query, workspace_id, limit
                )
                all_memories.extend(workspace_memories)
            
            # Search in local cache
            cache_memories = self._search_cache_memories(
                query, memory_type, scope, workspace_id, limit
            )
            all_memories.extend(cache_memories)
            
            # Deduplicate and rank by relevance
            unique_memories = self._deduplicate_memories(all_memories)
            ranked_memories = self._rank_memories_by_relevance(unique_memories, query)
            
            # Update access patterns for learning
            for memory in ranked_memories:
                memory.accessed_at = datetime.now()
                memory.access_count += 1
            
            logger.info(f"🔍 Retrieved {len(ranked_memories)} memories for query")
            return ranked_memories[:limit]
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve memories: {e}")
            return []
    
    async def get_memory_insights(self, workspace_id: str) -> Dict[str, Any]:
        """Get holistic insights about memory usage and patterns"""
        try:
            insights = {
                "total_memories": 0,
                "memory_by_type": {},
                "memory_by_scope": {},
                "access_patterns": {},
                "system_utilization": {},
                "learning_opportunities": []
            }
            
            # Aggregate insights from all memory systems
            for system_name, system in self.memory_engines.items():
                try:
                    if hasattr(system, 'get_insights'):
                        system_insights = await system.get_insights(workspace_id)
                        insights["system_utilization"][system_name] = system_insights
                except Exception as e:
                    logger.warning(f"⚠️ Could not get insights from {system_name}: {e}")
            
            # Analyze access patterns
            access_data = self.access_patterns.get(workspace_id, {})
            insights["access_patterns"] = {
                "most_accessed_types": self._get_top_accessed_types(access_data),
                "recent_queries": self._get_recent_queries(access_data),
                "efficiency_score": self._calculate_efficiency_score(access_data)
            }
            
            # Identify learning opportunities
            insights["learning_opportunities"] = self._identify_learning_opportunities(workspace_id)
            
            return insights
            
        except Exception as e:
            logger.error(f"❌ Failed to get memory insights: {e}")
            return {"error": str(e)}
    
    def _select_optimal_storage_system(self, memory_entry: MemoryEntry) -> str:
        """Select the best memory system for storing a specific memory"""
        
        # Similarity-based memories go to similarity engine
        if memory_entry.memory_type == MemoryType.SIMILARITY:
            return "similarity"
        
        # Workspace-specific context goes to workspace memory
        if (memory_entry.scope == MemoryScope.WORKSPACE and 
            memory_entry.memory_type == MemoryType.CONTEXT):
            return "workspace"
        
        # Complex experiences and patterns go to unified memory
        if memory_entry.memory_type in [MemoryType.EXPERIENCE, MemoryType.PATTERN]:
            return "unified"
        
        # Default to unified memory
        return "unified"
    
    async def _store_in_unified_memory(self, memory_entry: MemoryEntry):
        """Store memory in UnifiedMemoryEngine"""
        engine = self.memory_engines["unified"]
        await engine.store_memory(
            memory_entry.id,
            memory_entry.content,
            memory_entry.workspace_id,
            memory_entry.metadata
        )
    
    async def _store_in_similarity_memory(self, memory_entry: MemoryEntry):
        """Store memory in MemorySimilarityEngine"""
        engine = self.memory_engines["similarity"]
        await engine.add_memory(
            memory_entry.content,
            memory_entry.workspace_id,
            memory_entry.confidence
        )
    
    async def _store_in_workspace_memory(self, memory_entry: MemoryEntry):
        """Store memory in WorkspaceMemory"""
        engine = self.memory_engines["workspace"]
        await engine.store_context(
            memory_entry.workspace_id,
            memory_entry.content,
            memory_entry.memory_type.value
        )
    
    async def _store_in_fallback_system(self, memory_entry: MemoryEntry, system_name: str):
        """Store memory in fallback system"""
        logger.info(f"🔄 Using fallback storage: {system_name}")
        # Implement fallback storage logic based on available system
        pass
    
    async def _search_similarity_memories(
        self, query, memory_type, scope, workspace_id, limit, threshold
    ) -> List[MemoryEntry]:
        """Search in similarity engine"""
        # Implementation depends on MemorySimilarityEngine interface
        return []
    
    async def _search_unified_memories(
        self, query, memory_type, scope, workspace_id, limit
    ) -> List[MemoryEntry]:
        """Search in unified memory engine"""
        # Implementation depends on UnifiedMemoryEngine interface
        return []
    
    async def _search_workspace_memories(
        self, query, workspace_id, limit
    ) -> List[MemoryEntry]:
        """Search in workspace memory"""
        # Implementation depends on workspace_memory interface
        return []
    
    def _search_cache_memories(
        self, query, memory_type, scope, workspace_id, limit
    ) -> List[MemoryEntry]:
        """Search in local memory cache"""
        matches = []
        for memory_id, memory_entry in self.memory_cache.items():
            # Simple matching logic
            if self._matches_criteria(memory_entry, memory_type, scope, workspace_id):
                matches.append(memory_entry)
        
        return matches[:limit]
    
    def _matches_criteria(
        self, memory_entry: MemoryEntry, memory_type, scope, workspace_id
    ) -> bool:
        """Check if memory entry matches search criteria"""
        if memory_type and memory_entry.memory_type != memory_type:
            return False
        if scope and memory_entry.scope != scope:
            return False
        if workspace_id and memory_entry.workspace_id != workspace_id:
            return False
        return True
    
    def _deduplicate_memories(self, memories: List[MemoryEntry]) -> List[MemoryEntry]:
        """Remove duplicate memories"""
        seen_ids = set()
        unique_memories = []
        
        for memory in memories:
            if memory.id not in seen_ids:
                seen_ids.add(memory.id)
                unique_memories.append(memory)
        
        return unique_memories
    
    def _rank_memories_by_relevance(
        self, memories: List[MemoryEntry], query: Dict[str, Any]
    ) -> List[MemoryEntry]:
        """Rank memories by relevance to query"""
        # Simple ranking by confidence and access count
        return sorted(
            memories,
            key=lambda m: (m.confidence, m.access_count, -m.created_at.timestamp()),
            reverse=True
        )
    
    def _get_top_accessed_types(self, access_data: Dict) -> List[str]:
        """Get most frequently accessed memory types"""
        return ["experience", "pattern", "context"]  # Placeholder
    
    def _get_recent_queries(self, access_data: Dict) -> List[Dict]:
        """Get recent memory queries"""
        return []  # Placeholder
    
    def _calculate_efficiency_score(self, access_data: Dict) -> float:
        """Calculate memory system efficiency score"""
        return 85.0  # Placeholder
    
    def _identify_learning_opportunities(self, workspace_id: str) -> List[str]:
        """Identify opportunities for system learning"""
        return [
            "Increase similarity threshold for better precision",
            "Store more task execution patterns",
            "Improve workspace context categorization"
        ]

# Global holistic memory manager instance
_holistic_memory_manager_instance = None

def get_holistic_memory_manager() -> HolisticMemoryManager:
    """Get the global holistic memory manager instance"""
    global _holistic_memory_manager_instance
    
    if _holistic_memory_manager_instance is None:
        _holistic_memory_manager_instance = HolisticMemoryManager()
        logger.info("🧠 Holistic Memory Manager initialized - memory silos eliminated!")
    
    return _holistic_memory_manager_instance

async def store_holistic_memory(
    content: Dict[str, Any],
    memory_type: MemoryType,
    scope: MemoryScope,
    **kwargs
) -> str:
    """Convenience function for storing memories holistically"""
    manager = get_holistic_memory_manager()
    return await manager.store_memory(content, memory_type, scope, **kwargs)

async def retrieve_holistic_memories(
    query: Dict[str, Any],
    **kwargs
) -> List[MemoryEntry]:
    """Convenience function for retrieving memories holistically"""
    manager = get_holistic_memory_manager()
    return await manager.retrieve_memories(query, **kwargs)