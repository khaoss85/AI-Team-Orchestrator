#!/usr/bin/env python3
"""
Conversation Routes - AI-Driven Knowledge Insights Remediation Patch

This file contains the updated implementation for the knowledge insights endpoint
that replaces hardcoded keyword matching with AI-driven semantic categorization.

To apply this patch:
1. Backup the original routes/conversation.py file
2. Replace lines 1048-1074 in routes/conversation.py with the code from this file
3. Add the necessary imports at the top of routes/conversation.py

Required imports to add:
from services.ai_knowledge_categorization import get_categorization_service
from config.knowledge_insights_config import get_config
"""

# REPLACE LINES 1048-1074 in routes/conversation.py WITH THIS CODE:

# Initialize services (add this at module level after other imports)
categorization_service = None
knowledge_config = None

def _get_services():
    """Lazy initialization of services"""
    global categorization_service, knowledge_config
    if categorization_service is None:
        from services.ai_knowledge_categorization import get_categorization_service
        categorization_service = get_categorization_service()
    if knowledge_config is None:
        from config.knowledge_insights_config import get_config
        knowledge_config = get_config()
    return categorization_service, knowledge_config

# UPDATED CATEGORIZATION LOGIC (replaces lines 1048-1074):
async def categorize_deliverable_content(deliverable, insights, best_practices, learnings, workspace_id, logger):
    """
    Categorize deliverable content using AI-driven semantic analysis.
    This function replaces the hardcoded keyword matching.
    """
    categorization_service, config = _get_services()
    
    if deliverable.get("content"):
        content_str = deliverable.get("content", "")
        
        # Extract meaningful content preview
        if isinstance(content_str, str):
            content_preview = content_str[:500] + "..." if len(content_str) > 500 else content_str
            
            # Create base knowledge item
            knowledge_item = {
                "id": deliverable.get("id"),
                "type": config.get_fallback_category(),  # Will be updated by AI
                "content": f"{deliverable.get('title', 'Deliverable')}: {content_preview}",
                "confidence": deliverable.get("content_quality_score", 0.7) / 100.0 if deliverable.get("content_quality_score") else 0.7,
                "created_at": deliverable.get("created_at", ""),
                "tags": []
            }
            
            # AI-driven semantic categorization
            if config.should_use_ai():
                try:
                    # Perform AI categorization
                    categorization = await categorization_service.categorize_knowledge(
                        content=content_str,
                        title=deliverable.get('title', ''),
                        workspace_context={
                            'workspace_id': workspace_id,
                            'goal': deliverable.get('goal_description', '')
                        }
                    )
                    
                    # Update knowledge item with AI results
                    knowledge_item["type"] = categorization["type"]
                    knowledge_item["tags"] = categorization["tags"]
                    knowledge_item["confidence"] = categorization["confidence"]
                    
                    # Add metadata if available
                    if "language" in categorization:
                        knowledge_item["language"] = categorization["language"]
                    if "reasoning" in categorization:
                        knowledge_item["ai_reasoning"] = categorization["reasoning"]
                    
                    # Route to appropriate list based on AI categorization
                    if categorization["type"] in ["success_pattern", "strategy"]:
                        best_practices.append(knowledge_item.copy())
                        logger.info(f"AI categorized '{deliverable.get('title', '')[:50]}...' as {categorization['type']} (confidence: {categorization['confidence']:.2f})")
                    elif categorization["type"] in ["optimization", "discovery", "analysis"]:
                        insights.append(knowledge_item.copy())
                        logger.info(f"AI categorized '{deliverable.get('title', '')[:50]}...' as {categorization['type']} (confidence: {categorization['confidence']:.2f})")
                    elif categorization["type"] in ["learning", "constraint", "research"]:
                        learnings.append(knowledge_item.copy())
                        logger.info(f"AI categorized '{deliverable.get('title', '')[:50]}...' as {categorization['type']} (confidence: {categorization['confidence']:.2f})")
                    else:
                        # Default to insights for unknown types
                        insights.append(knowledge_item.copy())
                        logger.info(f"AI categorized '{deliverable.get('title', '')[:50]}...' as {categorization['type']} (defaulting to insights)")
                        
                except Exception as e:
                    logger.warning(f"AI categorization failed for deliverable {deliverable.get('id')}, using fallback: {e}")
                    # Use configuration-based fallback
                    knowledge_item["type"] = config.get_fallback_category()
                    knowledge_item["tags"] = config.get_fallback_tags()
                    knowledge_item["ai_reasoning"] = f"Fallback categorization (AI error: {str(e)[:100]})"
                    insights.append(knowledge_item.copy())
            else:
                # Configuration-based fallback when AI is disabled
                knowledge_item["type"] = config.get_fallback_category()
                knowledge_item["tags"] = config.get_fallback_tags()
                knowledge_item["ai_reasoning"] = "AI categorization disabled"
                
                # Simple routing based on configuration
                if knowledge_item["type"] == "success_pattern":
                    best_practices.append(knowledge_item.copy())
                elif knowledge_item["type"] in ["optimization", "discovery"]:
                    insights.append(knowledge_item.copy())
                else:
                    learnings.append(knowledge_item.copy())
                    
                logger.info(f"Using fallback categorization for '{deliverable.get('title', '')[:50]}...' (AI disabled)")
        else:
            # Non-string content - add to insights with minimal processing
            knowledge_item = {
                "id": deliverable.get("id"),
                "type": config.get_fallback_category(),
                "content": deliverable.get("title", ""),
                "confidence": 0.3,
                "created_at": deliverable.get("created_at", ""),
                "tags": config.get_fallback_tags(limit=3),
                "ai_reasoning": "Non-text content"
            }
            insights.append(knowledge_item)
    else:
        # No content available - add minimal entry to insights
        knowledge_item = {
            "id": deliverable.get("id"),
            "type": config.get_fallback_category(),
            "content": deliverable.get("title", "Deliverable"),
            "confidence": 0.2,
            "created_at": deliverable.get("created_at", ""),
            "tags": config.get_fallback_tags(limit=2),
            "ai_reasoning": "No content available"
        }
        insights.append(knowledge_item)


# IMPLEMENTATION INSTRUCTIONS:
# 
# In routes/conversation.py, replace the entire block from lines 1048-1074 with:
#
# ```python
# # Process each deliverable with AI categorization
# for deliverable in deliverables:
#     await categorize_deliverable_content(
#         deliverable, insights, best_practices, learnings, workspace_id, logger
#     )
# ```
#
# And add the categorize_deliverable_content function from this file.

# ALSO UPDATE THE SUMMARY GENERATION (line 1069-1075):
def generate_dynamic_summary(deliverables, insights, best_practices, learnings, config):
    """
    Generate dynamic summary based on actual content, not hardcoded values.
    """
    # Get configuration
    if config is None:
        from config.knowledge_insights_config import get_config
        config = get_config()
    
    # Extract top tags from categorized items
    all_tags = []
    for item_list in [insights, best_practices, learnings]:
        for item in item_list:
            all_tags.extend(item.get("tags", []))
    
    # Count tag frequency
    from collections import Counter
    tag_counts = Counter(all_tags)
    top_tags = [tag for tag, _ in tag_counts.most_common(10)]
    
    # If no tags found, use configuration defaults
    if not top_tags:
        top_tags = config.get_fallback_tags()
    
    # Create dynamic summary
    summary = {
        "recent_discoveries": [
            item.get("content", "")[:100] 
            for item in insights[:3] 
            if item.get("content")
        ],
        "key_constraints": [
            item.get("content", "")[:100]
            for item in learnings
            if item.get("type") == "constraint"
        ][:3],
        "success_patterns": [
            item.get("content", "")[:100]
            for item in best_practices
            if item.get("content")
        ][:3],
        "top_tags": top_tags[:config.max_tags]
    }
    
    return summary


# COMPLETE UPDATED get_knowledge_insights FUNCTION:
# This shows how the entire fallback section should look after remediation

"""
# After line 1068, replace the summary generation (lines 1069-1075) with:

# Create dynamic summary from categorized deliverables
summary = generate_dynamic_summary(deliverables, insights, best_practices, learnings, knowledge_config)

return {
    "workspace_id": workspace_id,
    "total_insights": len(deliverables),
    "insights": insights,
    "bestPractices": best_practices,
    "learnings": learnings,
    "summary": summary,
    "ai_enabled": knowledge_config.ai_enabled if knowledge_config else False
}
"""