# backend/services/unified_memory_engine.py
"""
Unified Memory Engine - Production v1.0
Consolidates 3 memory system files into a single, coherent engine
Eliminates duplicate functionality while maintaining backward compatibility

Consolidates:
- memory_system.py (core memory system with context storage)
- universal_memory_architecture.py (UMA with AI-driven context resolution)
- memory_enhanced_ai_asset_generator.py (AI asset generation with memory patterns)
"""

import asyncio
import logging
import json
import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from uuid import UUID, uuid4
from enum import Enum

# Standard imports with graceful fallbacks
try:
    from openai import AsyncOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    AsyncOpenAI = None

# Database imports with fallbacks
try:
    from database import get_supabase_client, supabase_retry
except ImportError:
    get_supabase_client = supabase_retry = None

# Configuration imports with fallbacks
try:
    from config.quality_system_config import get_env_bool, get_env_int, get_env_float
except ImportError:
    # Fallback configuration functions
    def get_env_bool(key: str, default: bool = False) -> bool:
        return os.getenv(key, str(default)).lower() == "true"
    
    def get_env_int(key: str, default: int = 0) -> int:
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default
    
    def get_env_float(key: str, default: float = 0.0) -> float:
        try:
            return float(os.getenv(key, str(default)))
        except ValueError:
            return default

logger = logging.getLogger(__name__)

# Configuration from environment
MEMORY_RETENTION_DAYS = get_env_int("MEMORY_RETENTION_DAYS", 90)
MAX_CONTEXT_ENTRIES = get_env_int("MAX_CONTEXT_ENTRIES", 1000)
MEMORY_SIMILARITY_THRESHOLD = get_env_float("MEMORY_SIMILARITY_THRESHOLD", 0.7)
ENABLE_CROSS_WORKSPACE_LEARNING = get_env_bool("ENABLE_CROSS_WORKSPACE_LEARNING", True)
ENABLE_ADAPTIVE_MEMORY_POLICIES = get_env_bool("ENABLE_ADAPTIVE_MEMORY_POLICIES", True)


# === DATA CLASSES ===

class ContentQuality(Enum):
    """Quality levels for generated content (from memory_enhanced_ai_asset_generator)"""
    EXCELLENT = "excellent"  # Business-ready, highly specific
    GOOD = "good"  # Useful but may need minor refinement
    ACCEPTABLE = "acceptable"  # Basic content that meets requirements
    POOR = "poor"  # Generic or incomplete content
    FAILED = "failed"  # Generation failed


@dataclass
class ContextEntry:
    """Structured context entry for memory storage (from universal_memory_architecture)"""
    id: str
    workspace_id: str
    context_type: str
    content: Dict[str, Any]
    created_at: datetime
    relevance_score: float = 1.0
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "context_type": self.context_type,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "relevance_score": self.relevance_score,
            "metadata": self.metadata or {}
        }


@dataclass
class MemoryPattern:
    """Learned pattern from successful content generation (from memory_enhanced_ai_asset_generator)"""
    pattern_id: str
    content_type: str
    business_context: str
    successful_approach: Dict[str, Any]
    success_metrics: Dict[str, float]
    usage_count: int = 0
    last_used: Optional[datetime] = None
    effectiveness_score: float = 0.0


@dataclass
class AssetGenerationResult:
    """Result of asset generation process (from memory_enhanced_ai_asset_generator)"""
    generated_content: Dict[str, Any]
    content_quality: ContentQuality
    business_specificity_score: float  # 0-100
    tool_integration_score: float  # 0-100
    memory_enhancement_score: float  # 0-100
    generation_reasoning: str
    source_tools_used: List[str]
    memory_patterns_applied: List[str]
    auto_improvements: List[str]
    confidence: float  # 0-100


class UnifiedMemoryEngine:
    """
    Unified Memory Engine - Production v1.0
    
    Consolidates all memory system functionality:
    - MemorySystem (context storage and retrieval)
    - UniversalMemoryArchitecture (AI-driven context resolution)
    - MemoryEnhancedAIAssetGenerator (AI asset generation with patterns)
    
    Eliminates duplicate functionality while maintaining full compatibility
    """
    
    def __init__(self, openai_client: Optional[AsyncOpenAI] = None):
        """Initialize unified memory engine with all subsystems"""
        
        # AI client initialization
        self.openai_client = openai_client
        if not self.openai_client and HAS_OPENAI and os.getenv("OPENAI_API_KEY"):
            try:
                self.openai_client = AsyncOpenAI()
                logger.info("✅ AI client initialized for memory processing")
            except Exception as e:
                logger.warning(f"AI client initialization failed: {e}")
        
        # Database client
        self.supabase = get_supabase_client() if get_supabase_client else None
        
        # Memory storage (consolidated from memory_system.py)
        self.context_storage: Dict[str, ContextEntry] = {}
        self.workspace_contexts: Dict[str, List[ContextEntry]] = {}
        
        # Pattern storage (from memory_enhanced_ai_asset_generator.py)
        self.learned_patterns: Dict[str, MemoryPattern] = {}
        self.pattern_effectiveness: Dict[str, float] = {}
        
        # UMA storage (from universal_memory_architecture.py)
        self.semantic_index: Dict[str, List[str]] = {}  # semantic_key -> entry_ids
        self.cross_workspace_patterns: Dict[str, Any] = {}
        
        # Caches for performance
        self.relevance_cache: Dict[str, Tuple[List[ContextEntry], datetime]] = {}
        self.generation_cache: Dict[str, AssetGenerationResult] = {}
        
        # Configuration
        self.retention_days = MEMORY_RETENTION_DAYS
        self.max_entries = MAX_CONTEXT_ENTRIES
        self.similarity_threshold = MEMORY_SIMILARITY_THRESHOLD
        
        # Statistics tracking
        self.stats = {
            "total_contexts_stored": 0,
            "total_contexts_retrieved": 0,
            "total_patterns_learned": 0,
            "total_assets_generated": 0,
            "ai_calls_made": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "cross_workspace_insights": 0
        }
        
        logger.info("🧠 Unified Memory Engine initialized successfully")
    
    # === CORE MEMORY SYSTEM (from memory_system.py) ===
    
    async def store_context(
        self,
        workspace_id: str,
        context_type: str,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        relevance_score: float = 1.0
    ) -> str:
        """
        Store context in memory system
        Consolidates functionality from MemorySystem.store_context
        """
        
        self.stats["total_contexts_stored"] += 1
        
        try:
            # Create context entry
            entry_id = str(uuid4())
            context_entry = ContextEntry(
                id=entry_id,
                workspace_id=workspace_id,
                context_type=context_type,
                content=content,
                created_at=datetime.now(),
                relevance_score=relevance_score,
                metadata=metadata or {}
            )
            
            # Store in memory
            self.context_storage[entry_id] = context_entry
            
            # Update workspace index
            if workspace_id not in self.workspace_contexts:
                self.workspace_contexts[workspace_id] = []
            self.workspace_contexts[workspace_id].append(context_entry)
            
            # Update semantic index
            await self._update_semantic_index(context_entry)
            
            # Persist to database if available
            if self.supabase:
                await self._persist_context_to_db(context_entry)
            
            # Cleanup old entries if needed
            await self._cleanup_old_contexts(workspace_id)
            
            logger.debug(f"✅ Context stored: {entry_id} ({context_type}) for workspace {workspace_id}")
            
            return entry_id
            
        except Exception as e:
            logger.error(f"Error storing context: {e}", exc_info=True)
            return ""
    
    async def get_relevant_context(
        self,
        workspace_id: str,
        query: str,
        context_types: Optional[List[str]] = None,
        max_results: int = 10
    ) -> List[ContextEntry]:
        """
        Retrieve relevant context using AI-driven similarity
        Consolidates functionality from MemorySystem.get_relevant_context and UMA
        """
        
        self.stats["total_contexts_retrieved"] += 1
        
        # Check cache first
        cache_key = f"{workspace_id}_{hash(query)}_{str(context_types)}_{max_results}"
        if cache_key in self.relevance_cache:
            cached_results, cache_time = self.relevance_cache[cache_key]
            if datetime.now() - cache_time < timedelta(minutes=30):  # Cache for 30 minutes
                self.stats["cache_hits"] += 1
                return cached_results
        
        self.stats["cache_misses"] += 1
        
        try:
            # Get workspace contexts
            workspace_contexts = self.workspace_contexts.get(workspace_id, [])
            
            # Filter by context types if specified
            if context_types:
                workspace_contexts = [
                    ctx for ctx in workspace_contexts 
                    if ctx.context_type in context_types
                ]
            
            if not workspace_contexts:
                return []
            
            # AI-powered semantic search if client available
            if self.openai_client:
                relevant_contexts = await self._ai_semantic_search(
                    query, workspace_contexts, max_results
                )
                self.stats["ai_calls_made"] += 1
            else:
                # Fallback to keyword matching
                relevant_contexts = self._keyword_search(
                    query, workspace_contexts, max_results
                )
            
            # Sort by relevance score
            relevant_contexts.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Cache results
            self.relevance_cache[cache_key] = (relevant_contexts, datetime.now())
            
            logger.debug(f"✅ Retrieved {len(relevant_contexts)} relevant contexts for query: {query[:50]}...")
            
            return relevant_contexts
            
        except Exception as e:
            logger.error(f"Error retrieving relevant context: {e}", exc_info=True)
            return []
    
    async def _ai_semantic_search(
        self,
        query: str,
        contexts: List[ContextEntry],
        max_results: int
    ) -> List[ContextEntry]:
        """AI-powered semantic search for context retrieval"""
        
        try:
            # Create embeddings for query and contexts (simplified approach)
            context_summaries = []
            for ctx in contexts:
                summary = f"{ctx.context_type}: {str(ctx.content)[:200]}..."
                context_summaries.append({
                    "id": ctx.id,
                    "summary": summary,
                    "context": ctx
                })
            
            # Use AI to rank contexts by relevance
            ranking_prompt = f"""
Rank these contexts by relevance to the query: "{query}"

Contexts:
{json.dumps([cs["summary"] for cs in context_summaries[:20]], indent=2)}

Return relevance scores (0.0-1.0) as JSON:
{{"rankings": [{{"context_index": 0, "relevance_score": 0.95}}, ...]}}

Focus on semantic similarity and business relevance.
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at semantic similarity ranking."},
                    {"role": "user", "content": ranking_prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            ranking_result = json.loads(response.choices[0].message.content)
            rankings = ranking_result.get("rankings", [])
            
            # Apply rankings to contexts
            relevant_contexts = []
            for ranking in rankings:
                context_index = ranking.get("context_index", 0)
                relevance_score = ranking.get("relevance_score", 0.0)
                
                if (context_index < len(context_summaries) and 
                    relevance_score >= self.similarity_threshold):
                    
                    context = context_summaries[context_index]["context"]
                    context.relevance_score = relevance_score
                    relevant_contexts.append(context)
            
            # Return top results
            return relevant_contexts[:max_results]
            
        except Exception as e:
            logger.warning(f"AI semantic search failed: {e}")
            return self._keyword_search(query, contexts, max_results)
    
    def _keyword_search(
        self,
        query: str,
        contexts: List[ContextEntry],
        max_results: int
    ) -> List[ContextEntry]:
        """Fallback keyword-based search"""
        
        query_words = query.lower().split()
        relevant_contexts = []
        
        for context in contexts:
            content_str = json.dumps(context.content, default=str).lower()
            
            # Calculate keyword match score
            matches = sum(1 for word in query_words if word in content_str)
            match_score = matches / len(query_words) if query_words else 0
            
            if match_score > 0.2:  # At least 20% keyword match
                context.relevance_score = match_score
                relevant_contexts.append(context)
        
        # Sort by match score and return top results
        relevant_contexts.sort(key=lambda x: x.relevance_score, reverse=True)
        return relevant_contexts[:max_results]
    
    async def _update_semantic_index(self, context_entry: ContextEntry):
        """Update semantic index for faster retrieval"""
        
        try:
            # Extract key terms from content
            content_str = json.dumps(context_entry.content, default=str).lower()
            
            # Simple keyword extraction (could be enhanced with NLP)
            words = content_str.split()
            key_terms = [word for word in words if len(word) > 3][:10]  # Top 10 meaningful words
            
            # Add to semantic index
            for term in key_terms:
                if term not in self.semantic_index:
                    self.semantic_index[term] = []
                self.semantic_index[term].append(context_entry.id)
            
        except Exception as e:
            logger.warning(f"Error updating semantic index: {e}")
    
    async def _persist_context_to_db(self, context_entry: ContextEntry):
        """Persist context to database"""
        
        if not self.supabase:
            return
        
        try:
            # Store in memory_contexts table
            context_data = context_entry.to_dict()
            
            result = self.supabase.table("memory_contexts").upsert(context_data).execute()
            
            if result.data:
                logger.debug(f"✅ Context persisted to DB: {context_entry.id}")
            
        except Exception as e:
            logger.warning(f"Failed to persist context to DB: {e}")
    
    async def _cleanup_old_contexts(self, workspace_id: str):
        """Cleanup old contexts based on retention policy"""
        
        try:
            workspace_contexts = self.workspace_contexts.get(workspace_id, [])
            
            # Remove contexts older than retention period
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            contexts_to_remove = [
                ctx for ctx in workspace_contexts 
                if ctx.created_at < cutoff_date
            ]
            
            for ctx in contexts_to_remove:
                # Remove from storage
                if ctx.id in self.context_storage:
                    del self.context_storage[ctx.id]
                
                # Remove from workspace index
                if ctx in workspace_contexts:
                    workspace_contexts.remove(ctx)
            
            # Limit total contexts per workspace
            if len(workspace_contexts) > self.max_entries:
                # Keep most recent contexts
                workspace_contexts.sort(key=lambda x: x.created_at, reverse=True)
                contexts_to_remove = workspace_contexts[self.max_entries:]
                
                for ctx in contexts_to_remove:
                    if ctx.id in self.context_storage:
                        del self.context_storage[ctx.id]
                    workspace_contexts.remove(ctx)
            
            if contexts_to_remove:
                logger.debug(f"🧹 Cleaned up {len(contexts_to_remove)} old contexts from workspace {workspace_id}")
            
        except Exception as e:
            logger.warning(f"Error cleaning up old contexts: {e}")
    
    # === MEMORY PATTERN LEARNING (from memory_enhanced_ai_asset_generator.py) ===
    
    async def learn_pattern_from_success(
        self,
        content_type: str,
        business_context: str,
        successful_approach: Dict[str, Any],
        success_metrics: Dict[str, float]
    ) -> str:
        """
        Learn pattern from successful content generation
        Consolidates functionality from MemoryEnhancedAIAssetGenerator
        """
        
        self.stats["total_patterns_learned"] += 1
        
        try:
            pattern_id = str(uuid4())
            
            # Create memory pattern
            pattern = MemoryPattern(
                pattern_id=pattern_id,
                content_type=content_type,
                business_context=business_context,
                successful_approach=successful_approach,
                success_metrics=success_metrics,
                usage_count=0,
                last_used=None,
                effectiveness_score=self._calculate_effectiveness_score(success_metrics)
            )
            
            # Store pattern
            self.learned_patterns[pattern_id] = pattern
            self.pattern_effectiveness[pattern_id] = pattern.effectiveness_score
            
            # Update cross-workspace patterns if enabled
            if ENABLE_CROSS_WORKSPACE_LEARNING:
                await self._update_cross_workspace_patterns(pattern)
            
            logger.info(f"🧠 Learned new pattern: {pattern_id} for {content_type} "
                       f"(effectiveness: {pattern.effectiveness_score:.2f})")
            
            return pattern_id
            
        except Exception as e:
            logger.error(f"Error learning pattern from success: {e}", exc_info=True)
            return ""
    
    async def get_applicable_patterns(
        self,
        content_type: str,
        business_context: str,
        max_patterns: int = 5
    ) -> List[MemoryPattern]:
        """Get applicable patterns for content generation"""
        
        try:
            # Find patterns matching content type and similar business context
            applicable_patterns = []
            
            for pattern in self.learned_patterns.values():
                if pattern.content_type == content_type:
                    # Calculate context similarity
                    similarity = await self._calculate_context_similarity(
                        business_context, pattern.business_context
                    )
                    
                    if similarity >= self.similarity_threshold:
                        pattern.relevance_score = similarity * pattern.effectiveness_score
                        applicable_patterns.append(pattern)
            
            # Sort by relevance and return top patterns
            applicable_patterns.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return applicable_patterns[:max_patterns]
            
        except Exception as e:
            logger.error(f"Error getting applicable patterns: {e}")
            return []
    
    async def generate_memory_enhanced_asset(
        self,
        content_type: str,
        business_context: str,
        requirements: Dict[str, Any],
        workspace_id: str
    ) -> AssetGenerationResult:
        """
        Generate asset using memory patterns and AI
        Consolidates functionality from MemoryEnhancedAIAssetGenerator
        """
        
        self.stats["total_assets_generated"] += 1
        
        try:
            # Get relevant context from memory
            relevant_contexts = await self.get_relevant_context(
                workspace_id,
                f"{content_type} {business_context}",
                max_results=5
            )
            
            # Get applicable patterns
            applicable_patterns = await self.get_applicable_patterns(
                content_type, business_context
            )
            
            # Generate content using AI with memory enhancement
            if self.openai_client:
                generation_result = await self._ai_generate_with_memory(
                    content_type, business_context, requirements,
                    relevant_contexts, applicable_patterns
                )
                self.stats["ai_calls_made"] += 1
            else:
                # Fallback generation without AI
                generation_result = self._fallback_generate_content(
                    content_type, business_context, requirements
                )
            
            # Store successful generation as context for future use
            if generation_result.content_quality in [ContentQuality.EXCELLENT, ContentQuality.GOOD]:
                await self.store_context(
                    workspace_id,
                    f"generated_{content_type}",
                    {
                        "generated_content": generation_result.generated_content,
                        "generation_approach": generation_result.generation_reasoning,
                        "quality_metrics": {
                            "content_quality": generation_result.content_quality.value,
                            "business_specificity": generation_result.business_specificity_score,
                            "confidence": generation_result.confidence
                        }
                    },
                    metadata={
                        "content_type": content_type,
                        "business_context": business_context,
                        "generation_timestamp": datetime.now().isoformat()
                    }
                )
            
            logger.info(f"🤖 Generated {content_type} asset with quality: {generation_result.content_quality.value}")
            
            return generation_result
            
        except Exception as e:
            logger.error(f"Error generating memory-enhanced asset: {e}", exc_info=True)
            return AssetGenerationResult(
                generated_content={},
                content_quality=ContentQuality.FAILED,
                business_specificity_score=0.0,
                tool_integration_score=0.0,
                memory_enhancement_score=0.0,
                generation_reasoning=f"Generation failed: {str(e)}",
                source_tools_used=[],
                memory_patterns_applied=[],
                auto_improvements=[],
                confidence=0.0
            )
    
    async def _ai_generate_with_memory(
        self,
        content_type: str,
        business_context: str,
        requirements: Dict[str, Any],
        relevant_contexts: List[ContextEntry],
        applicable_patterns: List[MemoryPattern]
    ) -> AssetGenerationResult:
        """Generate content using AI with memory enhancement"""
        
        try:
            # Prepare context for AI
            context_summaries = [
                f"Context {i+1}: {ctx.context_type} - {str(ctx.content)[:200]}..."
                for i, ctx in enumerate(relevant_contexts[:3])
            ]
            
            pattern_summaries = [
                f"Pattern {i+1}: {pattern.content_type} approach - {str(pattern.successful_approach)[:200]}..."
                for i, pattern in enumerate(applicable_patterns[:3])
            ]
            
            generation_prompt = f"""
Generate a high-quality {content_type} for this business context: {business_context}

Requirements: {json.dumps(requirements, indent=2)}

Relevant Memory Context:
{chr(10).join(context_summaries)}

Successful Patterns to Apply:
{chr(10).join(pattern_summaries)}

Generate business-ready content that:
1. Uses specific, real business data (not generic examples)
2. Applies successful patterns from memory
3. Integrates relevant context for personalization
4. Provides immediately actionable information
5. Maintains professional quality standards

Respond with JSON:
{{
    "generated_content": {{structured_content}},
    "generation_reasoning": "explanation of approach",
    "memory_patterns_applied": ["pattern1", "pattern2"],
    "business_specificity_score": 0-100,
    "confidence": 0-100
}}
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"You are an expert {content_type} generator with access to memory patterns and context."},
                    {"role": "user", "content": generation_prompt}
                ],
                temperature=0.4,
                response_format={"type": "json_object"}
            )
            
            ai_response = json.loads(response.choices[0].message.content)
            
            # Extract generation results
            generated_content = ai_response.get("generated_content", {})
            generation_reasoning = ai_response.get("generation_reasoning", "")
            patterns_applied = ai_response.get("memory_patterns_applied", [])
            business_specificity = ai_response.get("business_specificity_score", 0)
            confidence = ai_response.get("confidence", 0)
            
            # Determine content quality
            content_quality = self._assess_content_quality(
                generated_content, business_specificity, confidence
            )
            
            # Calculate enhancement scores
            memory_enhancement_score = len(patterns_applied) * 20 + len(relevant_contexts) * 10
            tool_integration_score = 50 if generated_content else 0  # Basic scoring
            
            return AssetGenerationResult(
                generated_content=generated_content,
                content_quality=content_quality,
                business_specificity_score=business_specificity,
                tool_integration_score=tool_integration_score,
                memory_enhancement_score=min(100, memory_enhancement_score),
                generation_reasoning=generation_reasoning,
                source_tools_used=["ai_generation", "memory_patterns"],
                memory_patterns_applied=patterns_applied,
                auto_improvements=[],
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"AI generation with memory failed: {e}")
            raise e
    
    def _fallback_generate_content(
        self,
        content_type: str,
        business_context: str,
        requirements: Dict[str, Any]
    ) -> AssetGenerationResult:
        """Fallback content generation when AI unavailable"""
        
        # Basic template-based generation
        generated_content = {
            "content_type": content_type,
            "business_context": business_context,
            "requirements": requirements,
            "generated_at": datetime.now().isoformat(),
            "note": "Generated using fallback method - AI unavailable"
        }
        
        return AssetGenerationResult(
            generated_content=generated_content,
            content_quality=ContentQuality.ACCEPTABLE,
            business_specificity_score=30.0,
            tool_integration_score=0.0,
            memory_enhancement_score=0.0,
            generation_reasoning="Fallback generation used - AI client unavailable",
            source_tools_used=["fallback_generator"],
            memory_patterns_applied=[],
            auto_improvements=[],
            confidence=50.0
        )
    
    def _assess_content_quality(
        self,
        content: Dict[str, Any],
        business_specificity: float,
        confidence: float
    ) -> ContentQuality:
        """Assess quality of generated content"""
        
        if not content:
            return ContentQuality.FAILED
        
        # Simple quality assessment based on metrics
        if business_specificity >= 80 and confidence >= 80:
            return ContentQuality.EXCELLENT
        elif business_specificity >= 60 and confidence >= 70:
            return ContentQuality.GOOD
        elif business_specificity >= 40 and confidence >= 60:
            return ContentQuality.ACCEPTABLE
        else:
            return ContentQuality.POOR
    
    def _calculate_effectiveness_score(self, success_metrics: Dict[str, float]) -> float:
        """Calculate effectiveness score for a pattern"""
        
        # Weight different success metrics
        weights = {
            "quality_score": 0.4,
            "business_specificity": 0.3,
            "user_satisfaction": 0.2,
            "time_to_complete": 0.1
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for metric, value in success_metrics.items():
            weight = weights.get(metric, 0.1)
            total_score += value * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.5
    
    async def _calculate_context_similarity(self, context1: str, context2: str) -> float:
        """Calculate similarity between business contexts"""
        
        if not context1 or not context2:
            return 0.0
        
        # Simple keyword-based similarity (could be enhanced with embeddings)
        words1 = set(context1.lower().split())
        words2 = set(context2.lower().split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    async def _update_cross_workspace_patterns(self, pattern: MemoryPattern):
        """Update cross-workspace learning patterns"""
        
        if not ENABLE_CROSS_WORKSPACE_LEARNING:
            return
        
        try:
            # Generalize pattern for cross-workspace use
            generalized_key = f"{pattern.content_type}_{pattern.business_context[:50]}"
            
            if generalized_key not in self.cross_workspace_patterns:
                self.cross_workspace_patterns[generalized_key] = {
                    "patterns": [],
                    "average_effectiveness": 0.0,
                    "usage_count": 0
                }
            
            # Add pattern to cross-workspace collection
            cross_pattern = self.cross_workspace_patterns[generalized_key]
            cross_pattern["patterns"].append(pattern)
            cross_pattern["usage_count"] += 1
            
            # Update average effectiveness
            all_scores = [p.effectiveness_score for p in cross_pattern["patterns"]]
            cross_pattern["average_effectiveness"] = sum(all_scores) / len(all_scores)
            
            self.stats["cross_workspace_insights"] += 1
            
        except Exception as e:
            logger.warning(f"Error updating cross-workspace patterns: {e}")
    
    # === UTILITY METHODS ===
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive engine statistics"""
        
        return {
            "unified_memory_engine": "v1.0",
            "total_contexts_stored": self.stats["total_contexts_stored"],
            "total_contexts_retrieved": self.stats["total_contexts_retrieved"],
            "total_patterns_learned": self.stats["total_patterns_learned"],
            "total_assets_generated": self.stats["total_assets_generated"],
            "ai_calls_made": self.stats["ai_calls_made"],
            "cache_hits": self.stats["cache_hits"],
            "cache_misses": self.stats["cache_misses"],
            "cache_hit_ratio": self.stats["cache_hits"] / max(1, self.stats["cache_hits"] + self.stats["cache_misses"]),
            "cross_workspace_insights": self.stats["cross_workspace_insights"],
            "active_contexts": len(self.context_storage),
            "learned_patterns": len(self.learned_patterns),
            "cross_workspace_patterns": len(self.cross_workspace_patterns),
            "semantic_index_terms": len(self.semantic_index),
            "relevance_cache_size": len(self.relevance_cache),
            "generation_cache_size": len(self.generation_cache),
            "configuration": {
                "retention_days": self.retention_days,
                "max_entries": self.max_entries,
                "similarity_threshold": self.similarity_threshold,
                "cross_workspace_learning": ENABLE_CROSS_WORKSPACE_LEARNING,
                "adaptive_policies": ENABLE_ADAPTIVE_MEMORY_POLICIES
            },
            "ai_client_available": self.openai_client is not None,
            "database_available": self.supabase is not None
        }
    
    def reset_stats(self):
        """Reset all statistics and caches"""
        
        self.stats = {
            "total_contexts_stored": 0,
            "total_contexts_retrieved": 0,
            "total_patterns_learned": 0,
            "total_assets_generated": 0,
            "ai_calls_made": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "cross_workspace_insights": 0
        }
        
        self.relevance_cache.clear()
        self.generation_cache.clear()
        
        logger.info("🔄 Unified Memory Engine stats and caches reset")
    
    def clear_memory(self, workspace_id: Optional[str] = None):
        """Clear memory storage"""
        
        if workspace_id:
            # Clear specific workspace
            if workspace_id in self.workspace_contexts:
                contexts_to_remove = self.workspace_contexts[workspace_id]
                for ctx in contexts_to_remove:
                    if ctx.id in self.context_storage:
                        del self.context_storage[ctx.id]
                del self.workspace_contexts[workspace_id]
                logger.info(f"🧹 Cleared memory for workspace {workspace_id}")
        else:
            # Clear all memory
            self.context_storage.clear()
            self.workspace_contexts.clear()
            self.learned_patterns.clear()
            self.pattern_effectiveness.clear()
            self.cross_workspace_patterns.clear()
            self.semantic_index.clear()
            self.relevance_cache.clear()
            self.generation_cache.clear()
            logger.info("🧹 Cleared all memory storage")
    
    # === BACKWARD COMPATIBILITY METHODS ===
    
    async def get_memory_context(
        self,
        workspace_id: str,
        context_type: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Backward compatibility method for get_memory_context"""
        
        contexts = await self.get_relevant_context(
            workspace_id, context_type, [context_type], limit
        )
        
        return [ctx.to_dict() for ctx in contexts]
    
    async def add_memory(
        self,
        workspace_id: str,
        memory_type: str,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Backward compatibility method for add_memory"""
        
        return await self.store_context(
            workspace_id, memory_type, content, metadata
        )


# Create singleton instance for backward compatibility
unified_memory_engine = UnifiedMemoryEngine()

# Backward compatibility aliases and functions
memory_system = unified_memory_engine
universal_memory_architecture = unified_memory_engine
memory_enhanced_ai_asset_generator = unified_memory_engine

# Singleton access function for UMA compatibility
def get_universal_memory_architecture() -> UnifiedMemoryEngine:
    """Get universal memory architecture instance (backward compatibility)"""
    return unified_memory_engine

# For imports from individual modules
MemorySystem = UnifiedMemoryEngine
UniversalMemoryArchitecture = UnifiedMemoryEngine
MemoryEnhancedAIAssetGenerator = UnifiedMemoryEngine

logger.info("🧠 Unified Memory Engine module loaded successfully with backward compatibility")