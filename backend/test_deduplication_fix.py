#!/usr/bin/env python3
"""
Test Deduplication Logic
Verifies that the new deduplication system prevents duplicate insights
"""

import asyncio
import logging
from services.universal_learning_engine import universal_learning_engine, UniversalBusinessInsight as BusinessInsight
# Note: DomainType enum removed as Universal Learning Engine is domain-agnostic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_deduplication():
    """Test the deduplication logic with duplicate insights"""
    
    workspace_id = "1f1bf9cf-3c46-48ed-96f3-ec826742ee02"  # Social Growth workspace
    
    print("🧪 Testing Insight Deduplication Logic")
    print("=" * 50)
    
    # Create a duplicate insight (should be blocked)
    test_insight = BusinessInsight(
        insight_type="engagement_pattern",
        domain_context='instagram_marketing',  # Now using string instead of enum
        metric_name="engagement_optimization",
        metric_value=0.25,
        actionable_recommendation="Strategia Content Marketing Instagram Italia: Strategia completa di content marketing per Instagram in Italia",
        confidence_score=0.9,
        evidence_sources=["test_deliverable_1"],
        extraction_method="test_deduplication"
    )
    
    print(f"1. Testing duplicate insight detection...")
    print(f"   Insight: {test_insight.to_learning_format()[:60]}...")
    
    # Generate hash for comparison
    content_hash = universal_learning_engine._generate_insight_hash(test_insight)
    print(f"   Content Hash: {content_hash}")
    
    # Check if it exists (should return True due to existing similar insight)
    exists = await universal_learning_engine._check_insight_exists(workspace_id, content_hash)
    print(f"   Duplicate Detected: {exists}")
    
    # Try to store it (should be blocked)
    stored = await universal_learning_engine._store_insight(workspace_id, test_insight)
    print(f"   Storage Result: {'Blocked (Good!)' if not stored else 'Stored (Bad - deduplication failed!)'}")
    
    print(f"\n2. Testing new unique insight...")
    
    # Create a unique insight (should be stored)
    unique_insight = BusinessInsight(
        insight_type="new_test_pattern",
        domain_context='instagram_marketing',  # Now using string instead of enum
        metric_name="test_metric",
        metric_value=0.75,
        actionable_recommendation="This is a completely unique test insight that should be stored successfully for deduplication testing purposes",
        confidence_score=0.8,
        evidence_sources=["test_deliverable_unique"],
        extraction_method="test_deduplication_unique"
    )
    
    print(f"   Insight: {unique_insight.to_learning_format()[:60]}...")
    
    unique_hash = universal_learning_engine._generate_insight_hash(unique_insight)
    print(f"   Content Hash: {unique_hash}")
    
    exists_unique = await universal_learning_engine._check_insight_exists(workspace_id, unique_hash)
    print(f"   Duplicate Detected: {exists_unique}")
    
    stored_unique = await universal_learning_engine._store_insight(workspace_id, unique_insight)
    print(f"   Storage Result: {'Stored (Good!)' if stored_unique else 'Blocked (Bad - unique insight rejected!)'}")
    
    print(f"\n3. Testing edge cases...")
    
    # Test with very similar but slightly different insight
    similar_insight = BusinessInsight(
        insight_type="engagement_pattern",
        domain_context='instagram_marketing',  # Now using string instead of enum
        metric_name="engagement_optimization",
        metric_value=0.25,
        actionable_recommendation="Strategia Content Marketing Instagram Italia: Strategia completa di content marketing per Instagram in Italia con piccola modifica",
        confidence_score=0.9,
        evidence_sources=["test_deliverable_2"],
        extraction_method="test_similar"
    )
    
    similar_hash = universal_learning_engine._generate_insight_hash(similar_insight)
    exists_similar = await universal_learning_engine._check_insight_exists(workspace_id, similar_hash)
    stored_similar = await universal_learning_engine._store_insight(workspace_id, similar_insight)
    
    print(f"   Similar Insight Hash: {similar_hash}")
    print(f"   Duplicate Detected: {exists_similar}")
    print(f"   Storage Result: {'Blocked' if not stored_similar else 'Stored'}")
    
    print(f"\n=" * 50)
    print("✅ Deduplication Test Complete!")
    print(f"\nResults Summary:")
    print(f"- Exact duplicates: {'✅ Blocked' if not stored else '❌ Not blocked'}")
    print(f"- Unique insights: {'✅ Stored' if stored_unique else '❌ Not stored'}")
    print(f"- Similar insights: {'Blocked' if not stored_similar else 'Stored'}")
    
    return {
        "duplicate_blocked": not stored,
        "unique_stored": stored_unique,
        "similar_handled": True  # Either outcome is acceptable for similar insights
    }

if __name__ == "__main__":
    asyncio.run(test_deduplication())