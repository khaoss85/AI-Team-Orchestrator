# backend/services/unified_memory_engine.py
"""
Unified Memory Engine - Production v2.0
Consolidates 3 memory system files into a single, coherent, and database-first engine.
Eliminates duplicate functionality, resolves circular dependencies, and ensures backward compatibility.

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
from dataclasses import dataclass, asdict, field
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
    # This fallback allows the module to be imported even if the database is not available.
    def get_supabase_client(): return None
    def supabase_retry(max_attempts):
        def decorator(func):
            return func
        return decorator

logger = logging.getLogger(__name__)

# --- Configuration ---
MEMORY_RETENTION_DAYS = int(os.getenv("MEMORY_RETENTION_DAYS", "90"))
MAX_CONTEXT_ENTRIES = int(os.getenv("MAX_CONTEXT_ENTRIES", "1000"))
MEMORY_SIMILARITY_THRESHOLD = float(os.getenv("MEMORY_SIMILARITY_THRESHOLD", "0.7"))
ENABLE_CROSS_WORKSPACE_LEARNING = os.getenv("ENABLE_CROSS_WORKSPACE_LEARNING", "true").lower() == "true"
CACHE_EXPIRATION_MINUTES = int(os.getenv("CACHE_EXPIRATION_MINUTES", "60"))


# === ENUMS and DATA CLASSES (Consolidated) ===

class ContentQuality(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    FAILED = "failed"

@dataclass
class ContextEntry:
    id: str
    workspace_id: str
    context_type: str
    content: Dict[str, Any]
    importance_score: float
    semantic_hash: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)

@dataclass
class MemoryPattern:
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
    generated_content: Dict[str, Any]
    content_quality: ContentQuality
    business_specificity_score: float
    tool_integration_score: float
    memory_enhancement_score: float
    generation_reasoning: str
    source_tools_used: List[str]
    memory_patterns_applied: List[str]
    auto_improvements: List[str]
    confidence: float


class UnifiedMemoryEngine:
    """
    Unified Memory Engine - Production v2.0
    A single, coherent engine for all memory-related operations.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(UnifiedMemoryEngine, cls).__new__(cls)
        return cls._instance

    def __init__(self, openai_client: Optional[AsyncOpenAI] = None):
        # Ensure __init__ is called only once for the singleton
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True

        self.openai_client = openai_client
        if not self.openai_client and HAS_OPENAI and os.getenv("OPENAI_API_KEY"):
            try:
                self.openai_client = AsyncOpenAI()
                logger.info("✅ AI client initialized for memory processing")
            except Exception as e:
                logger.warning(f"AI client initialization failed: {e}")

        self.supabase = get_supabase_client()
        self.relevance_cache: Dict[str, Tuple[List[ContextEntry], datetime]] = {}

        self.stats = {
            "contexts_stored": 0,
            "contexts_retrieved": 0,
            "patterns_learned": 0,
            "assets_generated": 0,
            "ai_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }
        logger.info("🧠 Unified Memory Engine initialized successfully")

    # === CORE CONTEXT MANAGEMENT (from memory_system.py & UMA) ===

    @supabase_retry(max_attempts=3)
    async def store_context(
        self,
        workspace_id: Union[str, UUID],
        context_type: str,
        content: Dict[str, Any],
        importance_score: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Stores a context entry in the database. Database-first approach."""
        self.stats["contexts_stored"] += 1
        workspace_id_str = str(workspace_id)
        
        try:
            entry_id = str(uuid4())
            semantic_hash = hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()
            
            context_entry = ContextEntry(
                id=entry_id,
                workspace_id=workspace_id_str,
                context_type=context_type,
                content=content,
                importance_score=importance_score,
                semantic_hash=semantic_hash,
                metadata=metadata or {}
            )

            if not self.supabase:
                logger.warning("Supabase client not available. Storing context in-memory only.")
                return entry_id # Fallback for environments without DB

            db_record = asdict(context_entry)
            db_record['created_at'] = db_record['created_at'].isoformat()

            response = await self.supabase.table("memory_context").insert(db_record).execute()

            if response.data:
                logger.debug(f"✅ Context stored in DB: {entry_id} for workspace {workspace_id_str}")
                return entry_id
            else:
                raise Exception(f"Failed to store context in DB: {response.error}")

        except Exception as e:
            logger.error(f"Error storing context: {e}", exc_info=True)
            return ""

    @supabase_retry(max_attempts=3)
    async def get_relevant_context(
        self,
        workspace_id: Union[str, UUID],
        query: str,
        context_types: Optional[List[str]] = None,
        max_results: int = 10
    ) -> List[ContextEntry]:
        """Retrieves relevant context using AI-driven semantic search from the database."""
        self.stats["contexts_retrieved"] += 1
        workspace_id_str = str(workspace_id)

        cache_key = f"{workspace_id_str}_{query}_{str(context_types)}_{max_results}"
        if cache_key in self.relevance_cache:
            cached_results, cache_time = self.relevance_cache[cache_key]
            if datetime.utcnow() - cache_time < timedelta(minutes=CACHE_EXPIRATION_MINUTES):
                self.stats["cache_hits"] += 1
                return cached_results
        
        self.stats["cache_misses"] += 1

        try:
            if not self.supabase:
                logger.warning("Supabase client not available. Cannot retrieve context.")
                return []

            # Base query
            query_builder = self.supabase.table("memory_context").select("*") \
                .eq("workspace_id", workspace_id_str) \
                .gte("created_at", (datetime.utcnow() - timedelta(days=MEMORY_RETENTION_DAYS)).isoformat())
            
            if context_types:
                query_builder = query_builder.in_("context_type", context_types)

            response = await query_builder.order("importance_score", desc=True).limit(100).execute() # Fetch a larger pool for AI ranking
            
            if not response.data:
                return []

            all_contexts = [ContextEntry(**d) for d in response.data]

            if self.openai_client:
                self.stats["ai_calls"] += 1
                relevant_contexts = await self._ai_semantic_search(query, all_contexts, max_results)
            else:
                relevant_contexts = self._keyword_search(query, all_contexts, max_results)
            
            self.relevance_cache[cache_key] = (relevant_contexts, datetime.utcnow())
            logger.debug(f"✅ Retrieved {len(relevant_contexts)} relevant contexts for query: {query[:50]}...")
            return relevant_contexts

        except Exception as e:
            logger.error(f"Error retrieving relevant context: {e}", exc_info=True)
            return []

    async def _ai_semantic_search(self, query: str, contexts: List[ContextEntry], max_results: int) -> List[ContextEntry]:
        """AI-powered semantic search to rank contexts."""
        context_summaries = [{"id": ctx.id, "summary": f"{ctx.context_type}: {str(ctx.content)[:200]}..."} for ctx in contexts]
        
        ranking_prompt = f"""
        Rank these contexts by relevance to the query: "{query}"
        Contexts:
        {json.dumps(context_summaries, indent=2)}
        Return a JSON list of context IDs, ordered from most to least relevant.
        Example: {{\"ranked_ids\": [\"id1\", \"id3\", \"id2\"]}}
        """
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert semantic relevance ranker."},
                    {"role": "user", "content": ranking_prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            ranking_result = json.loads(response.choices[0].message.content)
            ranked_ids = ranking_result.get("ranked_ids", [])
            
            context_map = {ctx.id: ctx for ctx in contexts}
            
            # Reorder contexts based on AI ranking
            ordered_contexts = [context_map[id] for id in ranked_ids if id in context_map]
            
            # Add remaining contexts at the end
            remaining_contexts = [ctx for ctx in contexts if ctx.id not in ranked_ids]
            ordered_contexts.extend(remaining_contexts)
            
            return ordered_contexts[:max_results]

        except Exception as e:
            logger.warning(f"AI semantic search failed: {e}. Falling back to keyword search.")
            return self._keyword_search(query, contexts, max_results)

    def _keyword_search(self, query: str, contexts: List[ContextEntry], max_results: int) -> List[ContextEntry]:
        """Fallback keyword-based search."""
        query_words = set(query.lower().split())
        
        def score_func(context):
            content_str = json.dumps(context.content, default=str).lower()
            content_words = set(content_str.split())
            matches = len(query_words.intersection(content_words))
            return matches * context.importance_score

        contexts.sort(key=score_func, reverse=True)
        return contexts[:max_results]

    # === MEMORY PATTERN & ASSET GENERATION (from memory_enhanced_ai_asset_generator.py) ===

    @supabase_retry(max_attempts=3)
    async def learn_pattern_from_success(
        self,
        content_type: str,
        business_context: str,
        successful_approach: Dict[str, Any],
        success_metrics: Dict[str, float]
    ) -> str:
        """Learns and stores a pattern from a successful operation in the database."""
        self.stats["patterns_learned"] += 1
        try:
            pattern_id = str(uuid4())
            effectiveness_score = sum(success_metrics.values()) / len(success_metrics) if success_metrics else 0.0
            
            pattern = MemoryPattern(
                pattern_id=pattern_id,
                content_type=content_type,
                business_context=business_context,
                successful_approach=successful_approach,
                success_metrics=success_metrics,
                effectiveness_score=effectiveness_score,
            )
            
            if not self.supabase:
                logger.warning("Supabase client not available. Storing pattern in-memory only.")
                return pattern_id

            db_record = asdict(pattern)
            db_record['last_used'] = None # Ensure it's null on creation

            response = await self.supabase.table("learning_patterns").insert(db_record).execute()

            if response.data:
                logger.info(f"🧠 Learned new pattern: {pattern_id} for {content_type}")
                return pattern_id
            else:
                raise Exception(f"Failed to store learning pattern: {response.error}")

        except Exception as e:
            logger.error(f"Error learning pattern: {e}", exc_info=True)
            return ""

    @supabase_retry(max_attempts=3)
    async def get_applicable_patterns(
        self,
        content_type: str,
        business_context: str,
        max_patterns: int = 5
    ) -> List[MemoryPattern]:
        """Gets applicable patterns from the database based on content type and context."""
        try:
            if not self.supabase:
                logger.warning("Supabase client not available. Cannot retrieve patterns.")
                return []

            response = await self.supabase.table("learning_patterns") \
                .select("*") \
                .eq("content_type", content_type) \
                .order("effectiveness_score", desc=True) \
                .limit(50) \
                .execute()

            if not response.data:
                return []

            all_patterns = [MemoryPattern(**p) for p in response.data]
            
            # Simple keyword-based similarity for filtering
            business_context_words = set(business_context.lower().split())
            scored_patterns = []
            for p in all_patterns:
                pattern_context_words = set(p.business_context.lower().split())
                similarity = len(business_context_words.intersection(pattern_context_words)) / len(business_context_words.union(pattern_context_words))
                if similarity > 0.1: # Low threshold to allow for broader matches
                    p.relevance_score = similarity * p.effectiveness_score
                    scored_patterns.append(p)
            
            scored_patterns.sort(key=lambda p: p.relevance_score, reverse=True)
            return scored_patterns[:max_patterns]

        except Exception as e:
            logger.error(f"Error getting applicable patterns: {e}", exc_info=True)
            return []

    async def generate_memory_enhanced_asset(
        self,
        workspace_id: Union[str, UUID],
        content_type: str,
        business_context: str,
        requirements: Dict[str, Any]
    ) -> AssetGenerationResult:
        """Generates an asset using memory patterns, context, and AI."""
        self.stats["assets_generated"] += 1
        workspace_id_str = str(workspace_id)

        try:
            if not self.openai_client:
                logger.warning("AI client not available. Using fallback generation.")
                return self._fallback_generate_content(content_type, business_context)

            # 1. Gather intelligence
            context_query = f"Data for generating {content_type} regarding {business_context}"
            relevant_contexts = await self.get_relevant_context(workspace_id_str, context_query, max_results=5)
            applicable_patterns = await self.get_applicable_patterns(content_type, business_context, max_patterns=3)

            # 2. Generate with AI
            self.stats["ai_calls"] += 1
            generation_result = await self._ai_generate_with_memory(
                content_type, business_context, requirements, relevant_contexts, applicable_patterns
            )

            # 3. Post-processing and learning
            if generation_result.content_quality in [ContentQuality.EXCELLENT, ContentQuality.GOOD]:
                await self.store_context(
                    workspace_id=workspace_id_str,
                    context_type=f"generated_{content_type}",
                    content={
                        "generated_content": generation_result.generated_content,
                        "generation_reasoning": generation_result.generation_reasoning,
                    },
                    importance_score=generation_result.confidence / 100.0,
                    metadata={"source": "asset_generation"}
                )
            
            logger.info(f"🤖 Generated {content_type} asset with quality: {generation_result.content_quality.value}")
            return generation_result

        except Exception as e:
            logger.error(f"Error generating memory-enhanced asset: {e}", exc_info=True)
            return self._create_error_result(str(e))

    async def _ai_generate_with_memory(
        self, content_type, business_context, requirements, contexts, patterns
    ) -> AssetGenerationResult:
        """Internal AI generation logic."""
        context_summaries = [f"Context: {ctx.context_type} - {str(ctx.content)[:150]}..." for ctx in contexts]
        pattern_summaries = [f"Pattern: {p.successful_approach.get('name', 'Unnamed')} - Effectiveness: {p.effectiveness_score:.2f}" for p in patterns]

        prompt = f"""
        Generate a high-quality, business-ready '{content_type}'.
        Business Context: {business_context}
        Requirements: {json.dumps(requirements)}

        Leverage the following intelligence:
        Relevant Context from Memory:
        {json.dumps(context_summaries, indent=2)}

        Successful Patterns from Past Operations:
        {json.dumps(pattern_summaries, indent=2)}

        Instructions:
        1. Synthesize insights from the provided context and patterns.
        2. Generate concrete, specific, and immediately usable content. NO PLACEHOLDERS.
        3. Adhere strictly to the requirements.
        4. Respond with a JSON object containing the generated content and quality metrics.

        JSON Response Format:
        {{
            "generated_content": {{ ... structured content for the asset ... }},
            "generation_reasoning": "Detailed explanation of how memory and patterns were used.",
            "memory_patterns_applied": ["pattern_id_1", "pattern_id_2"],
            "business_specificity_score": <0-100 score>,
            "confidence": <0-100 score>
        }}
        """
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"You are an expert {content_type} generator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            ai_response = json.loads(response.choices[0].message.content)
            
            specificity = ai_response.get("business_specificity_score", 0)
            confidence = ai_response.get("confidence", 0)
            quality = self._assess_content_quality(specificity, confidence)

            return AssetGenerationResult(
                generated_content=ai_response.get("generated_content", {}),
                content_quality=quality,
                business_specificity_score=specificity,
                tool_integration_score=50, # Placeholder
                memory_enhancement_score=len(ai_response.get("memory_patterns_applied", [])) * 25 + len(contexts) * 5,
                generation_reasoning=ai_response.get("generation_reasoning", ""),
                source_tools_used=["ai_generation", "memory_retrieval"],
                memory_patterns_applied=ai_response.get("memory_patterns_applied", []),
                auto_improvements=[],
                confidence=confidence
            )
        except Exception as e:
            logger.error(f"AI generation with memory failed: {e}")
            return self._create_error_result(f"AI generation failed: {e}")

    # === UTILITY & FALLBACK METHODS ===

    def _assess_content_quality(self, specificity: float, confidence: float) -> ContentQuality:
        score = (specificity + confidence) / 2
        if score >= 85: return ContentQuality.EXCELLENT
        if score >= 70: return ContentQuality.GOOD
        if score >= 50: return ContentQuality.ACCEPTABLE
        return ContentQuality.POOR

    def _create_error_result(self, error_message: str) -> AssetGenerationResult:
        return AssetGenerationResult({}, ContentQuality.FAILED, 0, 0, 0, error_message, [], [], [], 0)

    def _fallback_generate_content(self, content_type: str, business_context: str) -> AssetGenerationResult:
        return AssetGenerationResult(
            generated_content={"error": "AI client unavailable, used fallback."},
            content_quality=ContentQuality.POOR,
            business_specificity_score=10,
            tool_integration_score=0,
            memory_enhancement_score=0,
            generation_reasoning="Fallback generation due to unavailable AI client.",
            source_tools_used=["fallback_generator"],
            memory_patterns_applied=[],
            auto_improvements=[],
            confidence=20
        )

    def get_stats(self) -> Dict[str, Any]:
        """Returns current engine statistics."""
        cache_efficiency = self.stats["cache_hits"] / max(1, self.stats["cache_hits"] + self.stats["cache_misses"])
        return {**self.stats, "cache_hit_ratio": f"{cache_efficiency:.2%}"}

    # === AGENT PERFORMANCE MEMORY ===

    @supabase_retry(max_attempts=3)
    async def store_agent_performance_metric(
        self,
        agent_id: Union[str, UUID],
        workspace_id: Union[str, UUID],
        quality_score: float,
        duration_seconds: float
    ):
        """Stores or updates an agent's performance metrics."""
        if not self.supabase:
            logger.warning("Supabase client not available. Cannot store agent performance.")
            return

        try:
            # Use an RPC call to an upsert function for atomic updates
            await self.supabase.rpc(
                'update_agent_performance',
                {
                    'p_agent_id': str(agent_id),
                    'p_workspace_id': str(workspace_id),
                    'p_quality_score': quality_score,
                    'p_duration_seconds': duration_seconds
                }
            ).execute()
            logger.info(f"🧠 Stored performance metric for agent {agent_id}")
        except Exception as e:
            logger.error(f"Error storing agent performance metric: {e}", exc_info=True)

    @supabase_retry(max_attempts=3)
    async def get_best_performing_agents(
        self,
        workspace_id: Union[str, UUID],
        role: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Gets the best performing agents for a specific role."""
        if not self.supabase:
            logger.warning("Supabase client not available. Cannot get best performing agents.")
            return []
        
        try:
            response = await self.supabase.table('agent_performance_metrics') \
                .select('agent_id, avg_quality_score, agents(name, role, seniority)') \
                .eq('workspace_id', str(workspace_id)) \
                .ilike('agents.role', f'%{role}%') \
                .order('avg_quality_score', desc=True) \
                .limit(limit) \
                .execute()
            
            if response.data:
                return response.data
            return []
        except Exception as e:
            logger.error(f"Error getting best performing agents: {e}", exc_info=True)
            return []

    # === BACKWARD COMPATIBILITY ALIASES ===
    
    async def store_insight(self, workspace_id: str, insight_type: str, content: str, 
                           relevance_tags: List[str] = None, confidence_score: float = 0.8, 
                           metadata: Optional[Dict] = None) -> str:
        """Backward compatibility for memory_system.store_insight"""
        context_content = {
            "insight_content": content,
            "relevance_tags": relevance_tags or []
        }
        full_metadata = {"insight_type": insight_type, **(metadata or {})}
        return await self.store_context(
            workspace_id, "insight", context_content, confidence_score, full_metadata
        )

# --- SINGLETON INSTANCE ---
unified_memory_engine = UnifiedMemoryEngine()

# --- BACKWARD COMPATIBILITY EXPORTS ---
memory_system = unified_memory_engine
universal_memory_architecture = unified_memory_engine
memory_enhanced_ai_asset_generator = unified_memory_engine

def get_universal_memory_architecture() -> UnifiedMemoryEngine:
    return unified_memory_engine

MemorySystem = UnifiedMemoryEngine
UniversalMemoryArchitecture = UnifiedMemoryEngine
MemoryEnhancedAIAssetGenerator = UnifiedMemoryEngine

logger.info("✅ Unified Memory Engine module loaded with backward compatibility.")
