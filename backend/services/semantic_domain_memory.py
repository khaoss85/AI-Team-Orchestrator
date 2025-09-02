"""
Semantic Domain Memory System
Learn and remember domain patterns without keywords

This service provides semantic memory capabilities for domain classification,
enabling the system to learn from past classifications and improve over time.

Pillar Compliance:
- Pillar 6: Workspace Memory integration
- Pillar 10: Explainable pattern matching
- Pillar 11: AI-driven learning
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import hashlib
from openai import AsyncOpenAI
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class SemanticMemoryEntry:
    """A semantic memory entry for domain classification"""
    id: str
    embedding: List[float]
    goal_text: str
    domain: str
    domain_category: str
    confidence: float
    specialists: List[Dict[str, Any]]
    semantic_tags: List[str]
    workspace_id: Optional[str]
    timestamp: datetime
    success_score: float  # How successful was this classification (based on user feedback)
    usage_count: int  # How many times this pattern has been referenced

@dataclass
class SimilarProject:
    """A similar project found in semantic memory"""
    id: str
    goal_text: str
    domain: str
    similarity: float
    confidence: float
    specialists: List[Dict[str, Any]]
    semantic_tags: List[str]
    timestamp: datetime


class SemanticDomainMemory:
    """
    Semantic memory system for domain classification patterns
    
    This system stores successful domain classifications and uses semantic
    similarity to suggest domains for new projects, enabling continuous learning.
    """
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.enabled = os.getenv("ENABLE_SEMANTIC_MEMORY", "true").lower() == "true"
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        self.similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.85"))
        self.memory_ttl_days = int(os.getenv("MEMORY_TTL_DAYS", "90"))
        
        # In-memory cache for this implementation
        # In production, this would use a vector database like Pinecone or Weaviate
        self.memory_store: Dict[str, SemanticMemoryEntry] = {}
        
        logger.info(f"🧠 Semantic Domain Memory initialized")
        logger.info(f"  - Enabled: {self.enabled}")
        logger.info(f"  - Embedding Model: {self.embedding_model}")
        logger.info(f"  - Similarity Threshold: {self.similarity_threshold}")
    
    async def store_classification(
        self,
        goal: str,
        classification: Any,  # DomainClassification from pure_ai_domain_classifier
        workspace_id: Optional[str] = None,
        success_score: float = 1.0
    ) -> str:
        """
        Store a successful classification in semantic memory
        
        Args:
            goal: The project goal text
            classification: The domain classification result
            workspace_id: Optional workspace ID for context
            success_score: How successful this classification was (0.0-1.0)
            
        Returns:
            Memory entry ID
        """
        if not self.enabled:
            return ""
        
        try:
            # Generate embedding for the goal
            embedding = await self._generate_embedding(goal)
            
            # Create unique ID
            entry_id = self._generate_id(goal, classification.primary_domain)
            
            # Check if similar entry exists and update instead of duplicate
            existing = await self._find_duplicate(embedding, classification.primary_domain)
            if existing:
                # Update existing entry
                existing.usage_count += 1
                existing.success_score = (existing.success_score + success_score) / 2
                existing.timestamp = datetime.now()
                logger.info(f"📝 Updated existing memory entry: {existing.id}")
                return existing.id
            
            # Create new memory entry
            entry = SemanticMemoryEntry(
                id=entry_id,
                embedding=embedding,
                goal_text=goal[:500],  # Store truncated version
                domain=classification.primary_domain,
                domain_category=classification.domain_category,
                confidence=classification.confidence,
                specialists=classification.specialists[:5],  # Store top 5 specialists
                semantic_tags=classification.semantic_tags[:10],  # Store top 10 tags
                workspace_id=workspace_id,
                timestamp=datetime.now(),
                success_score=success_score,
                usage_count=1
            )
            
            # Store in memory
            self.memory_store[entry_id] = entry
            
            # Clean old entries
            await self._cleanup_old_entries()
            
            logger.info(f"📝 Stored new semantic memory: {entry_id} for domain '{classification.primary_domain}'")
            return entry_id
            
        except Exception as e:
            logger.error(f"❌ Failed to store classification: {e}")
            return ""
    
    async def find_similar_projects(
        self,
        goal: str,
        threshold: Optional[float] = None,
        limit: int = 5
    ) -> List[SimilarProject]:
        """
        Find semantically similar past projects
        
        Args:
            goal: The project goal to match
            threshold: Similarity threshold (0.0-1.0)
            limit: Maximum number of results
            
        Returns:
            List of similar projects sorted by similarity
        """
        if not self.enabled or not self.memory_store:
            return []
        
        try:
            # Generate embedding for the goal
            query_embedding = await self._generate_embedding(goal)
            
            # Calculate similarities
            similarities = []
            for entry_id, entry in self.memory_store.items():
                similarity = self._cosine_similarity(query_embedding, entry.embedding)
                if similarity >= (threshold or self.similarity_threshold):
                    similarities.append((similarity, entry))
            
            # Sort by similarity
            similarities.sort(key=lambda x: x[0], reverse=True)
            
            # Convert to SimilarProject objects
            results = []
            for similarity, entry in similarities[:limit]:
                results.append(SimilarProject(
                    id=entry.id,
                    goal_text=entry.goal_text,
                    domain=entry.domain,
                    similarity=similarity,
                    confidence=entry.confidence,
                    specialists=entry.specialists,
                    semantic_tags=entry.semantic_tags,
                    timestamp=entry.timestamp
                ))
            
            if results:
                logger.info(f"🔍 Found {len(results)} similar projects (top similarity: {results[0].similarity:.3f})")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to find similar projects: {e}")
            return []
    
    async def suggest_domain_from_memory(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Suggest domain based on semantic similarity to past projects
        
        Args:
            goal: The project goal
            context: Optional context for refinement
            
        Returns:
            Domain suggestion with confidence and reasoning
        """
        if not self.enabled:
            return None
        
        try:
            # Find similar projects
            similar = await self.find_similar_projects(goal, threshold=0.8, limit=3)
            
            if not similar:
                return None
            
            # If very high similarity, use directly
            if similar[0].similarity > 0.95:
                return {
                    "domain": similar[0].domain,
                    "confidence": similar[0].similarity,
                    "reasoning": f"Nearly identical to past project: '{similar[0].goal_text[:100]}...'",
                    "source": "semantic_memory",
                    "similar_projects": [s.goal_text[:100] for s in similar]
                }
            
            # Aggregate suggestions from multiple similar projects
            domain_votes = {}
            specialist_pool = {}
            tag_pool = set()
            
            for project in similar:
                weight = project.similarity * project.confidence
                
                # Weight domain votes
                if project.domain not in domain_votes:
                    domain_votes[project.domain] = 0
                domain_votes[project.domain] += weight
                
                # Collect specialists
                for specialist in project.specialists:
                    role = specialist.get("role", "Unknown")
                    if role not in specialist_pool:
                        specialist_pool[role] = []
                    specialist_pool[role].append(specialist)
                
                # Collect semantic tags
                tag_pool.update(project.semantic_tags)
            
            # Determine consensus domain
            best_domain = max(domain_votes.items(), key=lambda x: x[1])
            confidence = min(best_domain[1] / len(similar), 0.9)  # Normalized confidence
            
            # Build reasoning
            reasoning_parts = []
            reasoning_parts.append(f"Based on {len(similar)} similar past projects")
            reasoning_parts.append(f"with average similarity of {np.mean([s.similarity for s in similar]):.2f}")
            if len(domain_votes) > 1:
                reasoning_parts.append(f"(considered {len(domain_votes)} different domains)")
            
            return {
                "domain": best_domain[0],
                "confidence": confidence,
                "reasoning": ". ".join(reasoning_parts),
                "source": "semantic_memory_aggregation",
                "similar_projects": [s.goal_text[:100] for s in similar],
                "alternative_domains": [
                    {"domain": d, "weight": w} 
                    for d, w in sorted(domain_votes.items(), key=lambda x: x[1], reverse=True)[1:3]
                ],
                "suggested_specialists": list(specialist_pool.keys())[:5],
                "semantic_tags": list(tag_pool)[:10]
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to suggest domain from memory: {e}")
            return None
    
    async def get_domain_patterns(
        self,
        domain: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get common patterns for a specific domain
        
        Args:
            domain: The domain to analyze
            limit: Maximum number of patterns
            
        Returns:
            List of patterns with examples and insights
        """
        if not self.enabled:
            return []
        
        try:
            # Find all entries for this domain
            domain_entries = [
                entry for entry in self.memory_store.values()
                if entry.domain == domain
            ]
            
            if not domain_entries:
                return []
            
            # Sort by success score and usage count
            domain_entries.sort(
                key=lambda x: x.success_score * x.usage_count,
                reverse=True
            )
            
            # Extract patterns
            patterns = []
            specialist_frequency = {}
            tag_frequency = {}
            
            for entry in domain_entries[:limit]:
                # Count specialist roles
                for specialist in entry.specialists:
                    role = specialist.get("role", "Unknown")
                    specialist_frequency[role] = specialist_frequency.get(role, 0) + 1
                
                # Count semantic tags
                for tag in entry.semantic_tags:
                    tag_frequency[tag] = tag_frequency.get(tag, 0) + 1
                
                patterns.append({
                    "example": entry.goal_text[:200],
                    "confidence": entry.confidence,
                    "success_score": entry.success_score,
                    "usage_count": entry.usage_count
                })
            
            # Build pattern summary
            return {
                "domain": domain,
                "total_examples": len(domain_entries),
                "patterns": patterns[:5],
                "common_specialists": sorted(
                    specialist_frequency.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5],
                "common_tags": sorted(
                    tag_frequency.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10],
                "avg_confidence": np.mean([e.confidence for e in domain_entries]),
                "avg_success": np.mean([e.success_score for e in domain_entries])
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get domain patterns: {e}")
            return []
    
    async def update_success_score(
        self,
        entry_id: str,
        new_score: float
    ) -> bool:
        """
        Update the success score of a memory entry based on feedback
        
        Args:
            entry_id: The memory entry ID
            new_score: New success score (0.0-1.0)
            
        Returns:
            True if updated successfully
        """
        if not self.enabled:
            return False
        
        try:
            if entry_id in self.memory_store:
                entry = self.memory_store[entry_id]
                # Weighted average with existing score
                entry.success_score = (entry.success_score + new_score) / 2
                entry.usage_count += 1
                logger.info(f"📊 Updated success score for {entry_id}: {entry.success_score:.2f}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to update success score: {e}")
            return False
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using OpenAI
        """
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=text[:8000]  # Limit text length
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"❌ Failed to generate embedding: {e}")
            # Return random embedding as fallback
            return [0.0] * 1536  # Default dimension for text-embedding-3-small
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors
        """
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
            
        except Exception as e:
            logger.error(f"❌ Failed to calculate similarity: {e}")
            return 0.0
    
    def _generate_id(self, goal: str, domain: str) -> str:
        """
        Generate unique ID for memory entry
        """
        content = f"{goal}:{domain}:{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    async def _find_duplicate(
        self,
        embedding: List[float],
        domain: str
    ) -> Optional[SemanticMemoryEntry]:
        """
        Find duplicate entry to avoid redundancy
        """
        for entry in self.memory_store.values():
            if entry.domain == domain:
                similarity = self._cosine_similarity(embedding, entry.embedding)
                if similarity > 0.98:  # Very high similarity
                    return entry
        return None
    
    async def _cleanup_old_entries(self):
        """
        Remove old entries beyond TTL
        """
        if not self.memory_ttl_days:
            return
        
        cutoff = datetime.now() - timedelta(days=self.memory_ttl_days)
        
        # Find entries to remove
        to_remove = []
        for entry_id, entry in self.memory_store.items():
            if entry.timestamp < cutoff and entry.usage_count < 5:
                to_remove.append(entry_id)
        
        # Remove old entries
        for entry_id in to_remove:
            del self.memory_store[entry_id]
        
        if to_remove:
            logger.info(f"🧹 Cleaned up {len(to_remove)} old memory entries")
    
    def export_memory(self) -> Dict[str, Any]:
        """
        Export memory for persistence or analysis
        """
        return {
            "version": "1.0",
            "export_date": datetime.now().isoformat(),
            "entries": [
                {
                    "id": entry.id,
                    "domain": entry.domain,
                    "goal_text": entry.goal_text,
                    "confidence": entry.confidence,
                    "success_score": entry.success_score,
                    "usage_count": entry.usage_count,
                    "timestamp": entry.timestamp.isoformat()
                }
                for entry in self.memory_store.values()
            ],
            "statistics": {
                "total_entries": len(self.memory_store),
                "unique_domains": len(set(e.domain for e in self.memory_store.values())),
                "avg_success_score": np.mean([e.success_score for e in self.memory_store.values()]) if self.memory_store else 0,
                "total_usage": sum(e.usage_count for e in self.memory_store.values())
            }
        }
    
    def import_memory(self, data: Dict[str, Any]) -> bool:
        """
        Import memory from exported data
        """
        try:
            # This would restore memory from exported data
            # Implementation depends on persistence strategy
            return True
        except Exception as e:
            logger.error(f"❌ Failed to import memory: {e}")
            return False


# Singleton instance
semantic_memory = SemanticDomainMemory()


# Public API
async def store_domain_classification(
    goal: str,
    classification: Any,
    workspace_id: Optional[str] = None
) -> str:
    """Store a successful domain classification"""
    return await semantic_memory.store_classification(goal, classification, workspace_id)


async def suggest_domain(goal: str, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Suggest domain based on semantic memory"""
    return await semantic_memory.suggest_domain_from_memory(goal, context)


async def find_similar_goals(goal: str, limit: int = 5) -> List[SimilarProject]:
    """Find similar project goals"""
    return await semantic_memory.find_similar_projects(goal, limit=limit)