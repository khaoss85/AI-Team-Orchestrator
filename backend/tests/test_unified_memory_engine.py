# backend/tests/test_unified_memory_engine.py
import pytest
import asyncio
import json
from uuid import uuid4
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# Import the singleton instance from the unified engine
from services.unified_memory_engine import (
    unified_memory_engine,
    ContentQuality,
    AssetGenerationResult,
    ContextEntry,
    MemoryPattern
)

# Mock the database and AI client for isolated testing
@pytest.fixture(autouse=True)
def mock_dependencies():
    # Reset the engine state before each test
    # Use MagicMock for the supabase client to allow chaining
    unified_memory_engine.supabase = MagicMock()
    unified_memory_engine.openai_client = AsyncMock()
    
    # Clear in-memory caches and stats for test isolation
    if hasattr(unified_memory_engine, 'relevance_cache'):
        unified_memory_engine.relevance_cache.clear()
    
    unified_memory_engine.stats = {
        "contexts_stored": 0, "contexts_retrieved": 0, "patterns_learned": 0,
        "assets_generated": 0, "ai_calls": 0, "cache_hits": 0, "cache_misses": 0,
    }
    yield

@pytest.mark.asyncio
async def test_store_and_retrieve_context():
    """Test basic context storage and retrieval."""
    workspace_id = str(uuid4())
    context_content = {"test_key": "test_value"}
    
    # Mock Supabase response for storage
    # The final 'execute' call is what needs to be an AsyncMock
    execute_mock = AsyncMock()
    execute_mock.return_value = MagicMock(data=[{"id": "123"}])
    unified_memory_engine.supabase.table.return_value.insert.return_value.execute = execute_mock

    # Store context
    context_id = await unified_memory_engine.store_context(
        workspace_id=workspace_id,
        context_type="test_context",
        content=context_content,
        importance_score=0.8
    )
    
    assert context_id is not None
    assert unified_memory_engine.stats["contexts_stored"] == 1
    
    # Mock Supabase response for retrieval
    retrieve_execute_mock = AsyncMock()
    retrieve_execute_mock.return_value = MagicMock(
        data=[{
            "id": context_id,
            "workspace_id": workspace_id,
            "context_type": "test_context",
            "content": context_content,
            "importance_score": 0.8,
            "semantic_hash": "hash123",
            "created_at": datetime.utcnow().isoformat(),
            "metadata": {}
        }]
    )
    unified_memory_engine.supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.order.return_value.limit.return_value.execute = retrieve_execute_mock
    
    # Mock AI response for semantic search
    unified_memory_engine.openai_client.chat.completions.create.return_value = AsyncMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps({"ranked_ids": [context_id]})))]
    )

    # Retrieve context
    retrieved_contexts = await unified_memory_engine.get_relevant_context(
        workspace_id=workspace_id,
        query="test"
    )
    
    assert len(retrieved_contexts) == 1
    assert retrieved_contexts[0].id == context_id
    assert retrieved_contexts[0].content["test_key"] == "test_value"
    assert unified_memory_engine.stats["contexts_retrieved"] == 1
    assert unified_memory_engine.stats["ai_calls"] == 1

@pytest.mark.asyncio
async def test_learn_and_apply_pattern():
    """Test learning a pattern and applying it in asset generation."""
    workspace_id = str(uuid4())
    content_type = "email_campaign"
    business_context = "B2B SaaS launch"
    
    # Mock Supabase response for learning
    learn_execute_mock = AsyncMock()
    learn_execute_mock.return_value = MagicMock(data=[{"id": "p123"}])
    unified_memory_engine.supabase.table.return_value.insert.return_value.execute = learn_execute_mock

    # Learn a pattern
    pattern_id = await unified_memory_engine.learn_pattern_from_success(
        content_type=content_type,
        business_context=business_context,
        successful_approach={"name": "Aggressive CTA"},
        success_metrics={"conversion_rate": 0.15}
    )
    
    assert pattern_id is not None
    assert unified_memory_engine.stats["patterns_learned"] == 1
    
    # Mock Supabase for retrieving the pattern
    retrieve_pattern_mock = AsyncMock()
    retrieve_pattern_mock.return_value = MagicMock(
        data=[{
            "pattern_id": pattern_id,
            "content_type": content_type,
            "business_context": business_context,
            "successful_approach": {"name": "Aggressive CTA"},
            "success_metrics": {"conversion_rate": 0.15},
            "usage_count": 0,
            "last_used": None,
            "effectiveness_score": 0.15
        }]
    )
    unified_memory_engine.supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute = retrieve_pattern_mock
    
    # Mock AI for asset generation
    unified_memory_engine.openai_client.chat.completions.create.return_value = AsyncMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps({
            "generated_content": {"subject": "New SaaS Launch!"},
            "generation_reasoning": "Used Aggressive CTA pattern.",
            "memory_patterns_applied": [pattern_id],
            "business_specificity_score": 85,
            "confidence": 90
        })))]
    )
    
    # Generate asset, which should apply the learned pattern
    result = await unified_memory_engine.generate_memory_enhanced_asset(
        workspace_id=workspace_id,
        content_type=content_type,
        business_context=business_context,
        requirements={"target_audience": "tech_leads"}
    )
    
    assert result.content_quality == ContentQuality.EXCELLENT
    assert result.generated_content["subject"] == "New SaaS Launch!"
    assert pattern_id in result.memory_patterns_applied
    assert unified_memory_engine.stats["assets_generated"] == 1

@pytest.mark.asyncio
async def test_cache_logic():
    """Test the caching mechanism for context retrieval."""
    workspace_id = str(uuid4())
    query = "cached query"
    
    # Mock DB and AI for the first call (cache miss)
    cache_miss_mock = AsyncMock()
    cache_miss_mock.return_value = MagicMock(
        data=[{"id": "c1", "workspace_id": workspace_id, "content": {}, "context_type": "generic", "importance_score": 1, "semantic_hash": "h1", "created_at": datetime.utcnow().isoformat()}]
    )
    unified_memory_engine.supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.order.return_value.limit.return_value.execute = cache_miss_mock
    
    unified_memory_engine.openai_client.chat.completions.create.return_value = AsyncMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps({"ranked_ids": ["c1"]})))]
    )
    
    # First call - should be a cache miss
    await unified_memory_engine.get_relevant_context(workspace_id, query)
    assert unified_memory_engine.stats["cache_misses"] == 1
    assert unified_memory_engine.stats["cache_hits"] == 0
    assert unified_memory_engine.stats["ai_calls"] == 1
    
    # Second call - should be a cache hit
    await unified_memory_engine.get_relevant_context(workspace_id, query)
    assert unified_memory_engine.stats["cache_misses"] == 1
    assert unified_memory_engine.stats["cache_hits"] == 1
    # AI should not be called again
    assert unified_memory_engine.stats["ai_calls"] == 1

@pytest.mark.asyncio
async def test_backward_compatibility_aliases():
    """Ensure backward compatibility aliases point to the unified engine."""
    from backend.services.unified_memory_engine import (
        memory_system,
        universal_memory_architecture,
        memory_enhanced_ai_asset_generator,
        get_universal_memory_architecture,
        MemorySystem,
        UniversalMemoryArchitecture,
        MemoryEnhancedAIAssetGenerator
    )
    
    assert memory_system is unified_memory_engine
    assert universal_memory_architecture is unified_memory_engine
    assert memory_enhanced_ai_asset_generator is unified_memory_engine
    assert get_universal_memory_architecture() is unified_memory_engine
    assert MemorySystem is type(unified_memory_engine)
    assert UniversalMemoryArchitecture is type(unified_memory_engine)
    assert MemoryEnhancedAIAssetGenerator is type(unified_memory_engine)

@pytest.mark.asyncio
async def test_error_handling_in_generation():
    """Test that asset generation fails gracefully."""
    workspace_id = str(uuid4())
    
    # Mock AI to raise an exception
    unified_memory_engine.openai_client.chat.completions.create.side_effect = Exception("AI provider is down")
    
    # Mock DB to return no contexts or patterns
    error_mock = AsyncMock()
    error_mock.return_value = MagicMock(data=[])
    unified_memory_engine.supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.order.return_value.limit.return_value.execute = error_mock
    unified_memory_engine.supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute = error_mock

    result = await unified_memory_engine.generate_memory_enhanced_asset(
        workspace_id=workspace_id,
        content_type="any",
        business_context="any",
        requirements={}
    )
    
    assert result.content_quality == ContentQuality.FAILED
    assert "AI generation failed" in result.generation_reasoning
