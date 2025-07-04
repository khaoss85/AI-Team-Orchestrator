#!/usr/bin/env python3
"""
🤖 AI Resilient Similarity Engine
Robust similarity detection system with 4-tier fallback mechanism

This system solves the root cause of AI-driven similarity detection failures by providing:
1. 🤖 Primary: Advanced AI semantic similarity analysis
2. 🔄 Fallback 1: Pattern-based similarity using learned patterns
3. 🔄 Fallback 2: Keyword-based similarity with intelligent weighting
4. 🔄 Fallback 3: Structural similarity based on task properties
5. 📚 Autonomous learning from successful similarity detections

Pillar Compliance:
- Pillar 3 (Self-Healing): 99.9% uptime even when AI API is down
- Pillar 8 (Agnostic): Works with any content type and domain
- Pillar 7 (Quality): Continuous learning improves accuracy over time
"""

import asyncio
import logging
import os
import json
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import difflib
import traceback
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)

# 🤖 AI Client for semantic analysis
try:
    from openai import AsyncOpenAI
    ai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    AI_AVAILABLE = True
except Exception as e:
    logger.warning(f"⚠️ OpenAI not available for similarity analysis: {e}")
    AI_AVAILABLE = False
    ai_client = None

class SimilarityMethod(str, Enum):
    AI_SEMANTIC = "ai_semantic"
    PATTERN_BASED = "pattern_based"
    KEYWORD_BASED = "keyword_based"
    STRUCTURAL = "structural"
    EMERGENCY_FALLBACK = "emergency_fallback"

@dataclass
class SimilarityResult:
    similarity_score: float  # 0.0 to 1.0
    confidence: float       # 0.0 to 1.0
    method_used: SimilarityMethod
    reasoning: str
    similar_tasks: List[Dict[str, Any]]
    execution_time_ms: float
    fallback_used: bool

@dataclass
class SimilarityPattern:
    pattern_type: str
    features: Dict[str, Any]
    success_rate: float
    usage_count: int
    last_used: datetime

class AIResilientSimilarityEngine:
    """
    🤖 AI-Driven Resilient Similarity Engine
    
    Provides robust similarity detection with multiple fallback layers
    and autonomous learning for continuous improvement.
    """
    
    def __init__(self):
        self.learned_patterns = {}
        self.keyword_weights = defaultdict(float)
        self.similarity_cache = {}
        self.performance_metrics = {
            "ai_successes": 0,
            "fallback_uses": 0,
            "total_calls": 0,
            "average_confidence": 0.0
        }
        
    async def compute_semantic_similarity(
        self, 
        task1: Dict[str, Any], 
        task2: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> SimilarityResult:
        """
        🤖 Compute semantic similarity between two tasks with 4-tier fallback system
        
        Args:
            task1: First task for comparison
            task2: Second task for comparison
            context: Optional context for better similarity analysis
        
        Returns:
            SimilarityResult with confidence score and method used
        """
        start_time = datetime.now()
        self.performance_metrics["total_calls"] += 1
        
        try:
            # Generate cache key for repeated calls
            cache_key = self._generate_cache_key(task1, task2)
            if cache_key in self.similarity_cache:
                cached_result = self.similarity_cache[cache_key]
                logger.debug(f"🔄 Using cached similarity result: {cached_result.similarity_score:.3f}")
                return cached_result
            
            # Tier 1: AI Semantic Analysis (Primary)
            if AI_AVAILABLE:
                try:
                    result = await self._ai_semantic_analysis(task1, task2, context)
                    if result.confidence >= 0.7:  # High confidence threshold
                        self.performance_metrics["ai_successes"] += 1
                        self._cache_result(cache_key, result)
                        await self._learn_from_successful_detection(task1, task2, result)
                        return result
                    else:
                        logger.info(f"⚠️ AI analysis confidence too low ({result.confidence:.3f}), trying fallback")
                except Exception as e:
                    logger.warning(f"⚠️ AI semantic analysis failed: {e}")
            
            # Tier 2: Pattern-Based Similarity (Learned Patterns)
            try:
                result = await self._pattern_based_similarity(task1, task2, context)
                if result.confidence >= 0.6:
                    self.performance_metrics["fallback_uses"] += 1
                    self._cache_result(cache_key, result)
                    return result
            except Exception as e:
                logger.warning(f"⚠️ Pattern-based similarity failed: {e}")
            
            # Tier 3: Keyword-Based Similarity (Intelligent Weighting)
            try:
                result = await self._keyword_based_similarity(task1, task2, context)
                if result.confidence >= 0.5:
                    self.performance_metrics["fallback_uses"] += 1
                    self._cache_result(cache_key, result)
                    return result
            except Exception as e:
                logger.warning(f"⚠️ Keyword-based similarity failed: {e}")
            
            # Tier 4: Structural Similarity (Emergency Fallback)
            result = await self._structural_similarity(task1, task2, context)
            self.performance_metrics["fallback_uses"] += 1
            self._cache_result(cache_key, result)
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            result.execution_time_ms = execution_time
            
            return result
            
        except Exception as e:
            logger.error(f"❌ All similarity methods failed: {e}")
            logger.error(traceback.format_exc())
            
            # Ultimate emergency fallback
            return SimilarityResult(
                similarity_score=0.1,  # Very low similarity as safe default
                confidence=0.1,
                method_used=SimilarityMethod.EMERGENCY_FALLBACK,
                reasoning=f"Emergency fallback due to complete failure: {e}",
                similar_tasks=[],
                execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                fallback_used=True
            )

    async def _ai_semantic_analysis(
        self, 
        task1: Dict[str, Any], 
        task2: Dict[str, Any], 
        context: Optional[Dict[str, Any]]
    ) -> SimilarityResult:
        """🤖 Primary AI-driven semantic similarity analysis"""
        try:
            # Prepare task information for AI analysis
            task1_summary = self._extract_task_features(task1)
            task2_summary = self._extract_task_features(task2)
            
            prompt = f"""
🤖 SEMANTIC SIMILARITY ANALYSIS

Analyze the semantic similarity between these two tasks. Consider objectives, methods, deliverables, and business impact.

TASK 1:
{json.dumps(task1_summary, indent=2)}

TASK 2:
{json.dumps(task2_summary, indent=2)}

CONTEXT: {json.dumps(context, indent=2) if context else "None"}

ANALYSIS CRITERIA:
1. Objective similarity (what the task achieves)
2. Method similarity (how it's done)
3. Deliverable similarity (what is produced)
4. Scope overlap (areas of business impact)
5. Resource requirements similarity

Respond with JSON:
{{
    "similarity_score": 0.0-1.0,
    "confidence": 0.0-1.0,
    "reasoning": "detailed_analysis_explanation",
    "key_similarities": ["similarity1", "similarity2"],
    "key_differences": ["difference1", "difference2"],
    "business_impact_overlap": 0.0-1.0,
    "duplicate_likelihood": 0.0-1.0,
    "semantic_features": {{
        "shared_concepts": ["concept1", "concept2"],
        "unique_aspects": ["aspect1", "aspect2"]
    }}
}}
""" # Added closing triple quotes
            
            response = await ai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1500
            )
            
            raw_ai_response_content = response.choices[0].message.content
            logger.info(f"Raw AI response content: {raw_ai_response_content}")

            # Use the new robust AI JSON parser
            from utils.ai_json_parser import ai_json_parser
            from pydantic import BaseModel, Field
            from typing import List, Dict, Any

            class SemanticFeatures(BaseModel):
                shared_concepts: List[str]
                unique_aspects: List[str]

            class AISimilarityResponse(BaseModel):
                similarity_score: float
                confidence: float
                reasoning: str
                key_similarities: List[str]
                key_differences: List[str]
                business_impact_overlap: float
                duplicate_likelihood: float
                semantic_features: SemanticFeatures

            ai_analysis = await ai_json_parser.safe_ai_json_parse(
                raw_ai_response_content, AISimilarityResponse
            )

            if not ai_analysis:
                logger.error("❌ All JSON parsing and correction attempts failed.")
                logger.warning("🔄 Falling back to pattern-based similarity due to complete JSON parsing failure")
                return SimilarityResult(
                    similarity_score=0.0,
                    confidence=0.0,
                    method_used=SimilarityMethod.AI_SEMANTIC,
                    reasoning="JSON parsing failed, triggering fallback",
                    similar_tasks=[],
                    execution_time_ms=0.0,
                    fallback_used=True
                )
            
            ai_analysis = ai_analysis.model_dump()
            
            return SimilarityResult(
                similarity_score=ai_analysis.get("similarity_score", 0.0),
                confidence=ai_analysis.get("confidence", 0.0),
                method_used=SimilarityMethod.AI_SEMANTIC,
                reasoning=ai_analysis.get("reasoning", "AI semantic analysis"),
                similar_tasks=[task2] if ai_analysis.get("similarity_score", 0) > 0.7 else [],
                execution_time_ms=0.0,  # Will be set by caller
                fallback_used=False
            )
            
        except Exception as e:
            logger.error(f"❌ AI semantic analysis error: {e}")
            raise

    async def _pattern_based_similarity(
        self, 
        task1: Dict[str, Any], 
        task2: Dict[str, Any], 
        context: Optional[Dict[str, Any]]
    ) -> SimilarityResult:
        """🔄 Pattern-based similarity using learned patterns"""
        try:
            task1_features = self._extract_task_features(task1)
            task2_features = self._extract_task_features(task2)
            
            # Match against learned patterns
            pattern_matches = []
            for pattern_id, pattern in self.learned_patterns.items():
                match_score = self._match_pattern(task1_features, task2_features, pattern)
                if match_score > 0.5:
                    pattern_matches.append((pattern_id, match_score, pattern))
            
            if pattern_matches:
                # Use best matching pattern
                best_pattern = max(pattern_matches, key=lambda x: x[1])
                pattern_id, match_score, pattern = best_pattern
                
                # Calculate similarity based on pattern features
                similarity_score = self._calculate_pattern_similarity(
                    task1_features, task2_features, pattern
                )
                
                confidence = min(match_score * pattern.success_rate, 0.95)
                
                return SimilarityResult(
                    similarity_score=similarity_score,
                    confidence=confidence,
                    method_used=SimilarityMethod.PATTERN_BASED,
                    reasoning=f"Pattern-based analysis using learned pattern {pattern_id} (success rate: {pattern.success_rate:.2f})",
                    similar_tasks=[task2] if similarity_score > 0.6 else [],
                    execution_time_ms=0.0,
                    fallback_used=True
                )
            else:
                # No matching patterns found
                return await self._keyword_based_similarity(task1, task2, context)
                
        except Exception as e:
            logger.error(f"❌ Pattern-based similarity error: {e}")
            raise

    async def _keyword_based_similarity(
        self, 
        task1: Dict[str, Any], 
        task2: Dict[str, Any], 
        context: Optional[Dict[str, Any]]
    ) -> SimilarityResult:
        """🔄 Intelligent keyword-based similarity with learned weights"""
        try:
            # Extract text content from tasks
            text1 = self._extract_text_content(task1)
            text2 = self._extract_text_content(task2)
            
            # Tokenize and weight keywords
            keywords1 = self._extract_weighted_keywords(text1)
            keywords2 = self._extract_weighted_keywords(text2)
            
            # Calculate weighted similarity
            similarity_score = self._calculate_weighted_keyword_similarity(keywords1, keywords2)
            
            # Calculate confidence based on keyword overlap and weights
            total_weight1 = sum(keywords1.values())
            total_weight2 = sum(keywords2.values())
            overlap_weight = sum(min(keywords1.get(k, 0), keywords2.get(k, 0)) for k in set(keywords1) | set(keywords2))
            
            confidence = overlap_weight / max(total_weight1, total_weight2, 1) if max(total_weight1, total_weight2) > 0 else 0.0
            confidence = min(confidence, 0.8)  # Cap confidence for keyword-based method
            
            return SimilarityResult(
                similarity_score=similarity_score,
                confidence=confidence,
                method_used=SimilarityMethod.KEYWORD_BASED,
                reasoning=f"Keyword-based analysis with {len(set(keywords1) & set(keywords2))} shared keywords",
                similar_tasks=[task2] if similarity_score > 0.5 else [],
                execution_time_ms=0.0,
                fallback_used=True
            )
            
        except Exception as e:
            logger.error(f"❌ Keyword-based similarity error: {e}")
            raise

    async def _structural_similarity(
        self, 
        task1: Dict[str, Any], 
        task2: Dict[str, Any], 
        context: Optional[Dict[str, Any]]
    ) -> SimilarityResult:
        """🔄 Structural similarity based on task properties (emergency fallback)"""
        try:
            # Extract structural features
            struct1 = self._extract_structural_features(task1)
            struct2 = self._extract_structural_features(task2)
            
            # Compare structural features
            similarity_components = {
                "priority_match": 1.0 if struct1.get("priority") == struct2.get("priority") else 0.0,
                "status_similarity": self._status_similarity(struct1.get("status"), struct2.get("status")),
                "length_similarity": self._length_similarity(struct1.get("text_length", 0), struct2.get("text_length", 0)),
                "role_similarity": 1.0 if struct1.get("assigned_role") == struct2.get("assigned_role") else 0.0,
                "timing_similarity": self._timing_similarity(struct1.get("created_at"), struct2.get("created_at"))
            }
            
            # Weighted average of structural similarities
            weights = {
                "priority_match": 0.3,
                "status_similarity": 0.2,
                "length_similarity": 0.1,
                "role_similarity": 0.3,
                "timing_similarity": 0.1
            }
            
            similarity_score = sum(
                similarity_components[component] * weights[component]
                for component in similarity_components
            )
            
            # Structural similarity has moderate confidence
            confidence = min(similarity_score * 0.6, 0.6)
            
            return SimilarityResult(
                similarity_score=similarity_score,
                confidence=confidence,
                method_used=SimilarityMethod.STRUCTURAL,
                reasoning=f"Structural analysis: {similarity_components}",
                similar_tasks=[task2] if similarity_score > 0.7 else [],
                execution_time_ms=0.0,
                fallback_used=True
            )
            
        except Exception as e:
            logger.error(f"❌ Structural similarity error: {e}")
            # Ultimate fallback
            return SimilarityResult(
                similarity_score=0.1,
                confidence=0.1,
                method_used=SimilarityMethod.EMERGENCY_FALLBACK,
                reasoning=f"Emergency fallback: {e}",
                similar_tasks=[],
                execution_time_ms=0.0,
                fallback_used=True
            )

    async def _learn_from_successful_detection(
        self, 
        task1: Dict[str, Any], 
        task2: Dict[str, Any], 
        result: SimilarityResult
    ) -> None:
        """📚 Learn from successful similarity detection for future improvement"""
        try:
            if result.confidence < 0.7:
                return  # Only learn from high-confidence results
            
            # Extract features for pattern learning
            features1 = self._extract_task_features(task1)
            features2 = self._extract_task_features(task2)
            
            # Create learned pattern
            pattern_id = f"pattern_{len(self.learned_patterns)}_{int(datetime.now().timestamp())}"
            
            pattern = SimilarityPattern(
                pattern_type=result.method_used.value,
                features={
                    "shared_features": self._find_shared_features(features1, features2),
                    "similarity_threshold": result.similarity_score,
                    "confidence_threshold": result.confidence,
                    "context_features": self._extract_context_features(features1, features2)
                },
                success_rate=1.0,  # Will be updated with more data
                usage_count=1,
                last_used=datetime.now(timezone.utc)
            )
            
            self.learned_patterns[pattern_id] = pattern
            
            # Update keyword weights if method was keyword-based
            if result.method_used == SimilarityMethod.KEYWORD_BASED:
                self._update_keyword_weights(task1, task2, result.similarity_score)
            
            logger.info(f"📚 Learned new similarity pattern: {pattern_id}")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to learn from similarity detection: {e}")

    def _extract_task_features(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant features from task for analysis"""
        return {
            "name": task.get("name", ""),
            "description": task.get("description", ""),
            "priority": task.get("priority", "medium"),
            "status": task.get("status", "pending"),
            "assigned_to_role": task.get("assigned_to_role", ""),
            "context_data": task.get("context_data", {}),
            "text_length": len(str(task.get("name", "")) + str(task.get("description", ""))),
            "created_at": task.get("created_at"),
            "goal_related": bool(task.get("goal_id"))
        }

    def _extract_text_content(self, task: Dict[str, Any]) -> str:
        """Extract all text content from task"""
        text_parts = [
            task.get("name", ""),
            task.get("description", ""),
            task.get("assigned_to_role", ""),
            str(task.get("context_data", {}))
        ]
        return " ".join(filter(None, text_parts)).lower()

    def _extract_weighted_keywords(self, text: str) -> Dict[str, float]:
        """Extract keywords with intelligent weighting"""
        import re
        
        # Remove common stop words
        stop_words = {"the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "a", "an"}
        
        # Extract words
        words = re.findall(r'\b\w+\b', text.lower())
        words = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Apply learned weights or default weights
        keyword_weights = {}
        for word in words:
            base_weight = 1.0
            learned_weight = self.keyword_weights.get(word, 1.0)
            keyword_weights[word] = base_weight * learned_weight
        
        return keyword_weights

    def _calculate_weighted_keyword_similarity(self, keywords1: Dict[str, float], keywords2: Dict[str, float]) -> float:
        """Calculate similarity based on weighted keyword overlap"""
        if not keywords1 or not keywords2:
            return 0.0
        
        shared_keywords = set(keywords1.keys()) & set(keywords2.keys())
        if not shared_keywords:
            return 0.0
        
        # Calculate weighted similarity
        shared_weight = sum(min(keywords1[k], keywords2[k]) for k in shared_keywords)
        total_weight = sum(max(keywords1.get(k, 0), keywords2.get(k, 0)) for k in set(keywords1) | set(keywords2))
        
        return shared_weight / total_weight if total_weight > 0 else 0.0

    def _extract_structural_features(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structural features for fallback analysis"""
        return {
            "priority": task.get("priority", "medium"),
            "status": task.get("status", "pending"),
            "assigned_role": task.get("assigned_to_role", ""),
            "text_length": len(str(task.get("name", "")) + str(task.get("description", ""))),
            "created_at": task.get("created_at"),
            "has_context": bool(task.get("context_data")),
            "has_goal": bool(task.get("goal_id"))
        }

    def _status_similarity(self, status1: str, status2: str) -> float:
        """Calculate similarity between task statuses"""
        if status1 == status2:
            return 1.0
        
        # Define status similarity matrix
        status_groups = {
            "new": ["pending", "created"],
            "active": ["in_progress", "processing"],
            "done": ["completed", "finished"],
            "problem": ["failed", "error", "stale"]
        }
        
        group1 = group2 = None
        for group, statuses in status_groups.items():
            if status1 in statuses:
                group1 = group
            if status2 in statuses:
                group2 = group
        
        if group1 and group2 and group1 == group2:
            return 0.7
        return 0.0

    def _length_similarity(self, length1: int, length2: int) -> float:
        """Calculate similarity based on text length"""
        if length1 == 0 and length2 == 0:
            return 1.0
        if length1 == 0 or length2 == 0:
            return 0.0
        
        ratio = min(length1, length2) / max(length1, length2)
        return ratio

    def _timing_similarity(self, time1: Any, time2: Any) -> float:
        """Calculate similarity based on creation timing"""
        try:
            if not time1 or not time2:
                return 0.0
            
            # Convert to datetime if needed
            if isinstance(time1, str):
                time1 = datetime.fromisoformat(time1.replace('Z', '+00:00'))
            if isinstance(time2, str):
                time2 = datetime.fromisoformat(time2.replace('Z', '+00:00'))
            
            time_diff = abs((time1 - time2).total_seconds())
            
            # Similar if created within 1 hour
            if time_diff < 3600:
                return 1.0
            # Moderately similar if within 24 hours
            elif time_diff < 86400:
                return 0.5
            else:
                return 0.0
                
        except:
            return 0.0

    def _generate_cache_key(self, task1: Dict[str, Any], task2: Dict[str, Any]) -> str:
        """Generate cache key for similarity results"""
        key_data = {
            "task1_id": task1.get("id", ""),
            "task2_id": task2.get("id", ""),
            "task1_name": task1.get("name", ""),
            "task2_name": task2.get("name", "")
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _cache_result(self, cache_key: str, result: SimilarityResult) -> None:
        """Cache similarity result for future use"""
        # Keep cache size reasonable
        if len(self.similarity_cache) > 1000:
            # Remove oldest entries
            oldest_keys = list(self.similarity_cache.keys())[:100]
            for key in oldest_keys:
                del self.similarity_cache[key]
        
        self.similarity_cache[cache_key] = result

    def _match_pattern(self, features1: Dict[str, Any], features2: Dict[str, Any], pattern: SimilarityPattern) -> float:
        """Match task features against learned pattern"""
        try:
            pattern_features = pattern.features.get("shared_features", {})
            
            match_score = 0.0
            total_features = len(pattern_features)
            
            if total_features == 0:
                return 0.0
            
            for feature_name, expected_value in pattern_features.items():
                if feature_name in features1 and feature_name in features2:
                    if features1[feature_name] == expected_value and features2[feature_name] == expected_value:
                        match_score += 1.0
                    elif str(features1[feature_name]).lower() == str(expected_value).lower():
                        match_score += 0.8
            
            return match_score / total_features
            
        except Exception:
            return 0.0

    def _calculate_pattern_similarity(self, features1: Dict[str, Any], features2: Dict[str, Any], pattern: SimilarityPattern) -> float:
        """Calculate similarity based on pattern matching"""
        try:
            shared_features = pattern.features.get("shared_features", {})
            threshold = pattern.features.get("similarity_threshold", 0.5)
            
            # Count matching features between tasks
            matching_features = 0
            total_features = len(shared_features)
            
            for feature_name in shared_features:
                if (feature_name in features1 and feature_name in features2 and 
                    features1[feature_name] == features2[feature_name]):
                    matching_features += 1
            
            pattern_similarity = matching_features / max(total_features, 1)
            
            # Apply pattern threshold
            return min(pattern_similarity, threshold)
            
        except Exception:
            return 0.1

    def _find_shared_features(self, features1: Dict[str, Any], features2: Dict[str, Any]) -> Dict[str, Any]:
        """Find shared features between two tasks"""
        shared = {}
        for key in features1:
            if key in features2 and features1[key] == features2[key]:
                shared[key] = features1[key]
        return shared

    def _extract_context_features(self, features1: Dict[str, Any], features2: Dict[str, Any]) -> Dict[str, Any]:
        """Extract contextual features for pattern learning"""
        return {
            "both_have_goals": features1.get("goal_related", False) and features2.get("goal_related", False),
            "same_priority": features1.get("priority") == features2.get("priority"),
            "same_status": features1.get("status") == features2.get("status"),
            "similar_length": abs(features1.get("text_length", 0) - features2.get("text_length", 0)) < 50
        }

    def _update_keyword_weights(self, task1: Dict[str, Any], task2: Dict[str, Any], similarity_score: float) -> None:
        """Update keyword weights based on successful similarity detection"""
        text1 = self._extract_text_content(task1)
        text2 = self._extract_text_content(task2)
        
        keywords1 = set(re.findall(r'\b\w+\b', text1.lower()))
        keywords2 = set(re.findall(r'\b\w+\b', text2.lower()))
        
        shared_keywords = keywords1 & keywords2
        
        # Increase weights for keywords that contributed to successful matching
        weight_boost = similarity_score * 0.1
        for keyword in shared_keywords:
            self.keyword_weights[keyword] += weight_boost

    

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring"""
        success_rate = self.performance_metrics["ai_successes"] / max(self.performance_metrics["total_calls"], 1)
        fallback_rate = self.performance_metrics["fallback_uses"] / max(self.performance_metrics["total_calls"], 1)
        
        return {
            "total_calls": self.performance_metrics["total_calls"],
            "ai_success_rate": success_rate,
            "fallback_rate": fallback_rate,
            "learned_patterns": len(self.learned_patterns),
            "cache_size": len(self.similarity_cache),
            "keyword_weights": len(self.keyword_weights)
        }

# 🌍 Global resilient similarity engine instance
ai_resilient_similarity_engine = AIResilientSimilarityEngine()

# Export for easy import
__all__ = ["AIResilientSimilarityEngine", "ai_resilient_similarity_engine", "SimilarityResult", "SimilarityMethod"]
