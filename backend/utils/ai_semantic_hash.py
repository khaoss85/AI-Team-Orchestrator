# utils/ai_semantic_hash.py
"""
AI-Driven Semantic Hashing for Task Deduplication
Replaces simple string concatenation with semantic understanding
"""

import hashlib
import logging
from typing import Optional, Dict, Any, List
from uuid import UUID

logger = logging.getLogger(__name__)

async def generate_ai_semantic_hash(
    name: str,
    description: Optional[str] = None,
    goal_id: Optional[UUID] = None,
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate AI-driven semantic hash for task deduplication.
    
    This replaces the basic string concatenation approach with AI semantic understanding.
    Instead of just concatenating strings, we extract semantic meaning and create 
    a hash based on the actual intent and content.
    """
    try:
        # Use AI to extract semantic essence
        semantic_essence = await _extract_semantic_essence(name, description, context)
        
        if semantic_essence:
            # Create hash from semantic essence instead of raw strings
            hash_input = f"{semantic_essence}|{str(goal_id)}"
            return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
            
    except Exception as e:
        logger.warning(f"⚠️ AI semantic hashing failed: {e}, using fallback")
    
    # Fallback to improved string-based approach (better than current)
    return _generate_improved_string_hash(name, description, goal_id, context)


async def _extract_semantic_essence(name: str, description: Optional[str], context: Optional[Dict[str, Any]]) -> Optional[str]:
    """Extract the semantic essence of a task using AI."""
    try:
        from services.ai_provider_abstraction import ai_provider_manager
        
        # Build comprehensive task context
        task_info = f"Task Name: {name}"
        if description:
            task_info += f"\nDescription: {description}"
        if context:
            task_info += f"\nContext: {str(context)}"
        
        prompt = f"""Analyze this task and extract its semantic essence for deduplication purposes.

Task Information:
{task_info}

Extract the core semantic meaning by identifying:
1. Primary action/verb (e.g., "create", "analyze", "research")
2. Main object/target (e.g., "email sequence", "contact list", "report")
3. Key context/domain (e.g., "marketing", "technical", "compliance")
4. Essential parameters/constraints

Return a normalized semantic identifier that captures the essence, ignoring:
- Formatting variations
- Minor word choice differences  
- Non-essential details
- Temporal references unless critical

Example:
- "Create marketing email sequence #1" → "create_email_sequence_marketing"
- "Research ICP contacts for sales" → "research_contacts_sales"
- "Generate 3 email templates for lead nurturing" → "create_email_templates_nurturing"

Respond with just the semantic identifier (lowercase, underscores, no spaces):"""

        evaluator_agent = {
            "name": "SemanticTaskAnalyzer",
            "model": "gpt-4o-mini",
            "instructions": "Extract semantic essence for task deduplication. Focus on core meaning, ignore formatting."
        }

        response = await ai_provider_manager.call_ai(
            provider_type='openai_sdk',
            agent=evaluator_agent,
            prompt=prompt,
            max_tokens=100,
            temperature=0.1
        )
        
        if response and isinstance(response, dict):
            essence = response.get('content', '').strip().lower()
            # Validate and clean the essence
            if essence and len(essence.split()) <= 5:  # Reasonable length check
                import re
                # Clean to alphanumeric and underscores only
                essence = re.sub(r'[^a-z0-9_]', '', essence)
                if len(essence) >= 3:  # Minimum meaningful length
                    return essence
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Error extracting semantic essence: {e}")
        return None


def _generate_improved_string_hash(
    name: str, 
    description: Optional[str], 
    goal_id: Optional[UUID], 
    context: Optional[Dict[str, Any]]
) -> str:
    """
    Improved string-based hash generation (fallback).
    Better than current implementation but not AI-driven.
    """
    # Normalize strings for better matching
    normalized_name = _normalize_text(name)
    normalized_desc = _normalize_text(description) if description else ""
    
    # Extract key terms instead of full text
    name_terms = _extract_key_terms(normalized_name)
    desc_terms = _extract_key_terms(normalized_desc) if normalized_desc else []
    
    # Combine essential terms only
    essential_terms = list(set(name_terms + desc_terms))  # Remove duplicates
    essential_terms.sort()  # Consistent ordering
    
    # Create context string from relevant fields only
    context_str = ""
    if context:
        relevant_fields = ['agent_role', 'deliverable_type', 'priority']
        context_str = "|".join([
            f"{k}:{str(v).lower()}" 
            for k, v in context.items() 
            if k in relevant_fields and v
        ])
    
    # Build hash input with normalized components
    hash_input = f"{' '.join(essential_terms)}|{context_str}|{str(goal_id)}"
    
    return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()


def _normalize_text(text: str) -> str:
    """Normalize text for consistent comparison."""
    if not text:
        return ""
    
    import re
    # Convert to lowercase, remove extra whitespace, normalize punctuation
    normalized = re.sub(r'\s+', ' ', text.lower().strip())
    # Remove common filler words that don't affect meaning
    filler_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
    words = normalized.split()
    meaningful_words = [w for w in words if w not in filler_words or len(w) > 3]
    
    return ' '.join(meaningful_words)


def _extract_key_terms(text: str, max_terms: int = 5) -> List[str]:
    """Extract key terms from text for semantic matching."""
    if not text:
        return []
    
    import re
    # Split into words, remove very short words
    words = [w for w in re.findall(r'\b\w+\b', text.lower()) if len(w) >= 3]
    
    # Remove duplicates while preserving order
    unique_words = []
    seen = set()
    for word in words:
        if word not in seen:
            unique_words.append(word)
            seen.add(word)
    
    # Return most important terms (first few are usually most relevant)
    return unique_words[:max_terms]


# Enhanced semantic similarity for related tasks
async def calculate_ai_semantic_similarity(task1_name: str, task1_desc: str, task2_name: str, task2_desc: str) -> float:
    """Calculate semantic similarity between two tasks using AI understanding."""
    try:
        from services.ai_provider_abstraction import ai_provider_manager
        
        prompt = f"""Compare these two tasks and determine their semantic similarity on a scale from 0.0 to 1.0:

Task 1:
Name: {task1_name}
Description: {task1_desc or 'No description'}

Task 2:
Name: {task2_name}  
Description: {task2_desc or 'No description'}

Consider:
- Same core action/purpose (high similarity)
- Same target/deliverable (high similarity)
- Same domain/context (medium similarity)
- Different approaches to same goal (medium similarity)
- Completely different purposes (low similarity)

Examples:
- "Create email sequence 1" vs "Create email sequence 2" = 0.9 (very similar)
- "Research ICP contacts" vs "Generate contact list" = 0.7 (related purpose)
- "Create email template" vs "Create presentation template" = 0.4 (same action, different domain)
- "Research contacts" vs "Send invoices" = 0.1 (completely different)

Return only a number between 0.0 and 1.0:"""

        evaluator_agent = {
            "name": "TaskSimilarityAnalyzer",
            "model": "gpt-4o-mini", 
            "instructions": "Compare task semantic similarity. Return only numeric score 0.0-1.0."
        }

        response = await ai_provider_manager.call_ai(
            provider_type='openai_sdk',
            agent=evaluator_agent,
            prompt=prompt,
            max_tokens=50,
            temperature=0.1
        )
        
        if response and isinstance(response, dict):
            content = response.get('content', '').strip()
            try:
                similarity = float(content)
                return max(0.0, min(1.0, similarity))  # Clamp to valid range
            except ValueError:
                pass
        
        return 0.5  # Default moderate similarity if parsing fails
        
    except Exception as e:
        logger.error(f"❌ Error calculating AI semantic similarity: {e}")
        return 0.5  # Safe default