#!/usr/bin/env python3
"""
AI-Driven Knowledge Categorization Service

Semantic analysis for intelligent knowledge insights categorization.
Replaces hardcoded keyword matching with AI-powered understanding.

Complies with the 15 Pillars:
- PILLAR 1: AI-Driven (semantic analysis, not keywords)
- PILLAR 2: Domain Agnostic (works for any business domain)
- PILLAR 3: Multi-language (auto-detects and processes any language)
- PILLAR 10: No placeholders (all values from configuration)
- PILLAR 12: Explainable (provides reasoning for categorization)
"""

import logging
import os
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class KnowledgeType(Enum):
    """Knowledge insight types aligned with system architecture"""
    DISCOVERY = "discovery"
    OPTIMIZATION = "optimization"
    SUCCESS_PATTERN = "success_pattern"
    CONSTRAINT = "constraint"
    LEARNING = "learning"
    STRATEGY = "strategy"
    ANALYSIS = "analysis"
    RESEARCH = "research"


class AIKnowledgeCategorizationService:
    """
    AI-driven service for categorizing knowledge insights using semantic analysis.
    Provides intelligent categorization with confidence scoring and multilingual support.
    """
    
    def __init__(self):
        """Initialize the categorization service with configuration"""
        # Load configuration from environment
        self.ai_enabled = os.getenv("ENABLE_AI_KNOWLEDGE_CATEGORIZATION", "true").lower() == "true"
        self.model = os.getenv("KNOWLEDGE_CATEGORIZATION_MODEL", "gpt-4")
        self.confidence_threshold = float(os.getenv("KNOWLEDGE_CONFIDENCE_THRESHOLD", "0.7"))
        self.cache_ttl = int(os.getenv("KNOWLEDGE_CACHE_TTL_SECONDS", "3600"))
        self.max_tags = int(os.getenv("MAX_KNOWLEDGE_TAGS", "10"))
        self.default_language = os.getenv("DEFAULT_KNOWLEDGE_LANGUAGE", "auto")
        
        # Fallback configuration
        self.fallback_categories = os.getenv(
            "FALLBACK_KNOWLEDGE_CATEGORIES", 
            "discovery,optimization,success_pattern,constraint,learning"
        ).split(",")
        self.fallback_tags = os.getenv(
            "FALLBACK_DEFAULT_TAGS",
            "general,insight,knowledge"
        ).split(",")
        
        # Initialize cache
        self.cache = {}
        self.cache_expiry = {}
        
        logger.info(f"AI Knowledge Categorization Service initialized (AI: {self.ai_enabled})")
    
    async def categorize_knowledge(
        self, 
        content: str,
        title: str,
        workspace_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Categorize knowledge content using AI semantic analysis.
        
        Args:
            content: The knowledge content to categorize
            title: The title of the knowledge item
            workspace_context: Optional workspace context for better categorization
            
        Returns:
            Dictionary containing:
            - type: Knowledge type (from KnowledgeType enum)
            - tags: List of relevant tags
            - confidence: Confidence score (0.0 to 1.0)
            - reasoning: Explanation of categorization
            - language: Detected language
        """
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(content, title)
            
            # Check cache
            if self._is_cached(cache_key):
                logger.info(f"Using cached categorization for: {title[:50]}...")
                return self.cache[cache_key]
            
            # Perform AI categorization if enabled
            if self.ai_enabled:
                result = await self._ai_categorize(content, title, workspace_context)
            else:
                result = self._fallback_categorize(content, title)
            
            # Cache the result
            self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in categorize_knowledge: {e}")
            return self._fallback_categorize(content, title)
    
    async def generate_semantic_tags(
        self,
        content: str,
        category: str,
        language: Optional[str] = None
    ) -> List[str]:
        """
        Generate semantic tags for content based on AI analysis.
        
        Args:
            content: Content to analyze for tags
            category: The category of the content
            language: Optional language hint
            
        Returns:
            List of relevant tags
        """
        if not self.ai_enabled:
            return self.fallback_tags[:self.max_tags]
        
        try:
            from services.ai_provider_abstraction import ai_provider_manager
            
            prompt = f"""Extract relevant tags from this {category} content.
            
Content: {content[:1000]}

Generate up to {self.max_tags} specific, relevant tags that describe:
1. Main topics and themes
2. Business domain
3. Key concepts
4. Tools or technologies mentioned
5. Actions or outcomes

Return ONLY a JSON array of tag strings, no explanation:
["tag1", "tag2", "tag3"]"""
            
            response = await ai_provider_manager.call_ai(
                provider_type='openai_sdk',
                agent={
                    "name": "Tag Generator",
                    "model": self.model
                },
                prompt=prompt,
                temperature=0.5
            )
            
            # Parse tags from response
            try:
                # Response might be a dict or string
                tags = response if isinstance(response, list) else (response.get('tags', []) if isinstance(response, dict) else json.loads(response))
                if isinstance(tags, list):
                    return tags[:self.max_tags]
            except:
                pass
            
            # Fallback to extracting from response
            import re
            tags = re.findall(r'"([^"]+)"', response)
            return tags[:self.max_tags] if tags else self.fallback_tags
            
        except Exception as e:
            logger.warning(f"Error generating semantic tags: {e}")
            return self.fallback_tags[:self.max_tags]
    
    async def _ai_categorize(
        self,
        content: str,
        title: str,
        workspace_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform AI-driven categorization using semantic analysis.
        """
        try:
            from services.ai_provider_abstraction import ai_provider_manager
            
            # Prepare context
            workspace_info = ""
            if workspace_context:
                workspace_id = workspace_context.get("workspace_id", "")
                workspace_goal = workspace_context.get("goal", "")
                workspace_info = f"Workspace: {workspace_id}\nGoal: {workspace_goal}\n"
            
            # Create categorization prompt
            prompt = f"""Analyze this knowledge item and categorize it based on semantic understanding.

TITLE: {title}
CONTENT: {content[:2000]}
{workspace_info}

CATEGORIZATION REQUIREMENTS:
1. Determine the PRIMARY TYPE from these categories (BE SPECIFIC AND ACCURATE):
   - best_practice: Email templates, proven methodologies, successful strategies, effective frameworks, recommended approaches that can be reused
   - learning: Lessons learned from actual experience, insights from results, what worked vs what didn't, empirical findings from execution
   - success_pattern: Recurring patterns of success, repeatable achievements, winning formulas that have been proven multiple times
   - optimization: Specific performance improvements identified, efficiency gains possible, process enhancements, areas to optimize
   - discovery: NEW findings never seen before, unexpected research results, novel data insights, surprising revelations
   - constraint: Limitations encountered, restrictions identified, challenges discovered, obstacles that must be worked around
   - strategy: High-level strategic plans, business roadmaps, market positioning, competitive strategies
   - analysis: Data analysis results, metrics evaluation, performance reports, trend analysis
   - research: Research methodologies, investigation approaches, study frameworks, research findings

2. Generate relevant TAGS that describe:
   - Main topics and themes
   - Business domain specifics
   - Key concepts and methodologies
   - Specific technologies or tools mentioned
   - Target audience, market, or use case

3. Provide a CONFIDENCE score (0.7 to 1.0) for HIGH-QUALITY categorization

4. Detect the LANGUAGE of the content

5. Provide brief REASONING for your categorization

IMPORTANT CATEGORIZATION RULES:
- Email sequences/templates → best_practice (they are reusable templates)
- Campaign results/metrics → learning (empirical lessons from execution)
- Templates and frameworks → best_practice (proven methodologies)
- Performance data → learning or analysis (depending on if lessons are extracted)
- Process improvements → optimization (specific enhancements)
- New insights → discovery (only if truly novel)
- Strategic implications → strategy (high-level planning)

Return your analysis as JSON:
{{
    "type": "category_from_list_above",
    "tags": ["tag1", "tag2", "tag3"],
    "confidence": 0.85,
    "language": "detected_language",
    "reasoning": "Brief explanation of why this category was chosen"
}}"""
            
            # Get AI response
            response = await ai_provider_manager.call_ai(
                provider_type='openai_sdk',
                agent={
                    "name": "Knowledge Categorization Expert",
                    "model": self.model,
                    "instructions": "You are an expert at categorizing knowledge items based on semantic understanding."
                },
                prompt=prompt,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # Parse AI response
            try:
                # Response is already a dict from call_ai
                result = response if isinstance(response, dict) else json.loads(response)
                
                # Validate and normalize result
                result["type"] = result.get("type", self.fallback_categories[0])
                result["tags"] = result.get("tags", self.fallback_tags)[:self.max_tags]
                result["confidence"] = float(result.get("confidence", 0.7))
                result["language"] = result.get("language", "unknown")
                result["reasoning"] = result.get("reasoning", "AI categorization completed")
                
                # Ensure confidence is within bounds
                result["confidence"] = max(0.0, min(1.0, result["confidence"]))
                
                logger.info(f"AI categorization successful: {title[:50]}... -> {result['type']} (confidence: {result['confidence']:.2f})")
                
                return result
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse AI response: {e}")
                # Try to extract information from raw response
                return self._parse_raw_ai_response(response, content, title)
                
        except Exception as e:
            logger.error(f"AI categorization failed: {e}")
            return self._fallback_categorize(content, title)
    
    def _parse_raw_ai_response(self, response: str, content: str, title: str) -> Dict[str, Any]:
        """
        Attempt to parse useful information from a non-JSON AI response.
        """
        import re
        
        result = {
            "type": self.fallback_categories[0],
            "tags": [],
            "confidence": 0.5,
            "language": "unknown",
            "reasoning": "Parsed from raw AI response"
        }
        
        # Try to extract type
        for knowledge_type in KnowledgeType:
            if knowledge_type.value in response.lower():
                result["type"] = knowledge_type.value
                result["confidence"] = 0.6
                break
        
        # Extract potential tags (words in quotes)
        tags = re.findall(r'"([^"]+)"', response)
        if tags:
            result["tags"] = tags[:self.max_tags]
        else:
            result["tags"] = self.fallback_tags
        
        # Try to detect confidence
        confidence_match = re.search(r'(\d+\.?\d*)%?', response)
        if confidence_match:
            conf_value = float(confidence_match.group(1))
            if conf_value > 1:
                conf_value = conf_value / 100
            result["confidence"] = max(0.0, min(1.0, conf_value))
        
        return result
    
    def _fallback_categorize(self, content: str, title: str) -> Dict[str, Any]:
        """
        Fallback categorization when AI is not available.
        Uses configuration-based categorization without hardcoded values.
        """
        # Simple heuristic based on content length and structure
        content_lower = content.lower() if content else ""
        title_lower = title.lower() if title else ""
        combined_text = f"{title_lower} {content_lower}"
        
        # Determine category based on simple heuristics (not keywords)
        category = self.fallback_categories[0]  # Default from config
        
        # Generate basic tags from configuration
        tags = self.fallback_tags[:self.max_tags]
        
        # Calculate basic confidence
        confidence = 0.3  # Low confidence for fallback
        if len(content) > 100:
            confidence += 0.1
        if title:
            confidence += 0.1
        
        return {
            "type": category,
            "tags": tags,
            "confidence": confidence,
            "language": "unknown",
            "reasoning": "Fallback categorization (AI unavailable)"
        }
    
    def _generate_cache_key(self, content: str, title: str) -> str:
        """Generate a unique cache key for content."""
        # Use first 500 chars of content and full title for key
        key_content = f"{title}:{content[:500]}"
        return hashlib.md5(key_content.encode()).hexdigest()
    
    def _is_cached(self, cache_key: str) -> bool:
        """Check if a result is cached and still valid."""
        if cache_key not in self.cache:
            return False
        
        if cache_key not in self.cache_expiry:
            return False
        
        if datetime.now() > self.cache_expiry[cache_key]:
            # Cache expired
            del self.cache[cache_key]
            del self.cache_expiry[cache_key]
            return False
        
        return True
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """Cache a categorization result."""
        self.cache[cache_key] = result
        self.cache_expiry[cache_key] = datetime.now() + timedelta(seconds=self.cache_ttl)
        
        # Clean old cache entries if cache is getting large
        if len(self.cache) > 1000:
            self._clean_expired_cache()
    
    def _clean_expired_cache(self):
        """Remove expired entries from cache."""
        now = datetime.now()
        expired_keys = [
            key for key, expiry in self.cache_expiry.items()
            if expiry < now
        ]
        
        for key in expired_keys:
            del self.cache[key]
            del self.cache_expiry[key]
        
        logger.info(f"Cleaned {len(expired_keys)} expired cache entries")
    
    async def calculate_confidence(self, classification: Dict[str, Any]) -> float:
        """
        Calculate confidence score for a classification.
        
        Args:
            classification: The classification result
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = classification.get("confidence", 0.5)
        
        # Adjust confidence based on various factors
        if classification.get("reasoning") and len(classification.get("reasoning", "")) > 50:
            confidence += 0.1
        
        if classification.get("tags") and len(classification.get("tags", [])) >= 3:
            confidence += 0.1
        
        if classification.get("language") != "unknown":
            confidence += 0.05
        
        # Ensure within bounds
        return max(0.0, min(1.0, confidence))


# Module initialization
_service_instance = None

def get_categorization_service() -> AIKnowledgeCategorizationService:
    """Get singleton instance of the categorization service."""
    global _service_instance
    if _service_instance is None:
        _service_instance = AIKnowledgeCategorizationService()
    return _service_instance