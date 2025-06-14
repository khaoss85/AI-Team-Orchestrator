#!/usr/bin/env python3
"""
🧠 PREDICTIVE AUTO-APPROVAL ENGINE
Sistema predittivo per auto-approvare richieste basandosi su pattern ML
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import Counter, defaultdict
import re

logger = logging.getLogger(__name__)

class PredictiveApprovalEngine:
    """
    Engine predittivo che analizza pattern per auto-approvare richieste
    """
    
    def __init__(self):
        self.approval_patterns = defaultdict(list)
        self.feature_weights = {
            "quality_score": 0.35,
            "content_completeness": 0.25,
            "historical_similarity": 0.20,
            "agent_track_record": 0.15,
            "task_complexity": 0.05
        }
        self.prediction_cache = {}
        
    async def predict_approval_probability(
        self, 
        request_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predice probabilità di approvazione usando pattern analysis
        """
        
        try:
            # Extract features from request
            features = await self._extract_prediction_features(request_data, context)
            
            # Calculate prediction score
            prediction_score = await self._calculate_prediction_score(features)
            
            # Determine confidence level
            confidence = await self._calculate_prediction_confidence(features, prediction_score)
            
            # Make auto-approval decision
            auto_approve_threshold = 0.85  # 85% confidence for auto-approval
            can_auto_approve = prediction_score >= auto_approve_threshold and confidence >= 0.80
            
            result = {
                "approval_probability": prediction_score,
                "confidence": confidence,
                "can_auto_approve": can_auto_approve,
                "features": features,
                "reasoning": await self._generate_prediction_reasoning(features, prediction_score),
                "prediction_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"🧠 PREDICTION: {prediction_score:.1%} approval probability, "
                       f"confidence: {confidence:.1%}, auto-approve: {can_auto_approve}")
            
            return result
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return {
                "approval_probability": 0.5,
                "confidence": 0.0,
                "can_auto_approve": False,
                "error": str(e)
            }
    
    async def _extract_prediction_features(
        self, 
        request_data: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Estrae features per il modello predittivo
        """
        
        features = {}
        
        # 1. Quality Score Feature
        features["quality_score"] = request_data.get("quality_score", 0.0)
        
        # 2. Content Completeness Feature
        content = request_data.get("content", {})
        if isinstance(content, dict):
            filled_fields = sum(1 for v in content.values() if v and str(v).strip())
            total_fields = len(content) if content else 1
            features["content_completeness"] = filled_fields / total_fields
        else:
            features["content_completeness"] = 0.7  # Default for non-dict content
        
        # 3. Historical Similarity Feature
        features["historical_similarity"] = await self._calculate_historical_similarity(request_data)
        
        # 4. Agent Track Record Feature
        agent_id = context.get("agent_id", "unknown")
        features["agent_track_record"] = await self._get_agent_track_record_score(agent_id)
        
        # 5. Task Complexity Feature
        features["task_complexity"] = await self._assess_task_complexity(request_data, context)
        
        # 6. Additional context features
        features["request_type"] = context.get("request_type", "unknown")
        features["workspace_id"] = context.get("workspace_id", "unknown")
        features["has_placeholder_content"] = await self._detect_placeholder_content(content)
        features["content_length"] = len(str(content))
        
        return features
    
    async def _calculate_prediction_score(self, features: Dict[str, Any]) -> float:
        """
        Calcola score predittivo pesato
        """
        
        score = 0.0
        
        # Weighted combination of features
        for feature_name, weight in self.feature_weights.items():
            feature_value = features.get(feature_name, 0.0)
            score += feature_value * weight
        
        # Bonus/penalty adjustments
        
        # Bonus for high completeness + high quality
        if features.get("content_completeness", 0) > 0.9 and features.get("quality_score", 0) > 0.8:
            score += 0.05
        
        # Penalty for placeholder content
        if features.get("has_placeholder_content", False):
            score -= 0.10
        
        # Bonus for proven agent
        if features.get("agent_track_record", 0) > 0.9:
            score += 0.03
        
        # Penalty for very low content
        if features.get("content_length", 0) < 100:
            score -= 0.05
        
        return max(0.0, min(1.0, score))
    
    async def _calculate_prediction_confidence(
        self, 
        features: Dict[str, Any], 
        prediction_score: float
    ) -> float:
        """
        Calcola confidence nella predizione
        """
        
        confidence = 0.5  # Base confidence
        
        # High confidence indicators
        if features.get("historical_similarity", 0) > 0.8:
            confidence += 0.2
        
        if features.get("agent_track_record", 0) > 0.85:
            confidence += 0.15
        
        if features.get("quality_score", 0) > 0.8:
            confidence += 0.1
        
        # Extreme predictions are less confident
        if 0.3 <= prediction_score <= 0.7:  # Middle predictions less confident
            confidence -= 0.1
        elif prediction_score < 0.2 or prediction_score > 0.9:  # Extreme predictions more confident
            confidence += 0.1
        
        return max(0.0, min(1.0, confidence))
    
    async def _calculate_historical_similarity(self, request_data: Dict[str, Any]) -> float:
        """
        Calcola similarità con richieste storiche approvate
        """
        
        # Simplified similarity calculation
        # In production, this would use more sophisticated ML similarity metrics
        
        request_type = request_data.get("type", "unknown")
        quality_score = request_data.get("quality_score", 0.0)
        
        # Simulate historical data lookup
        historical_approvals = self.approval_patterns.get(request_type, [])
        
        if not historical_approvals:
            return 0.5  # No historical data
        
        # Find similar quality scores
        similar_scores = [score for score in historical_approvals if abs(score - quality_score) < 0.15]
        
        if len(similar_scores) >= 3:  # Sufficient similar cases
            return 0.85
        elif len(similar_scores) >= 1:
            return 0.65
        else:
            return 0.35
    
    async def _get_agent_track_record_score(self, agent_id: str) -> float:
        """
        Ottiene score track record agent
        """
        
        # Simulate agent performance lookup
        # This would integrate with adaptive_threshold_manager in production
        
        if agent_id == "unknown":
            return 0.5
        
        # Simulate different agent performance levels
        agent_performance_sim = {
            "excellent": 0.95,
            "good": 0.80,
            "average": 0.65,
            "needs_improvement": 0.40
        }
        
        # Simple hash-based simulation for consistency
        agent_hash = hash(agent_id) % 4
        performance_levels = list(agent_performance_sim.values())
        return performance_levels[agent_hash]
    
    async def _assess_task_complexity(
        self, 
        request_data: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> float:
        """
        Valuta complessità del task (0 = semplice, 1 = complesso)
        """
        
        complexity = 0.5  # Base complexity
        
        # Check content complexity indicators
        content = str(request_data.get("content", ""))
        
        # Length complexity
        if len(content) > 2000:
            complexity += 0.2
        elif len(content) < 500:
            complexity -= 0.1
        
        # Structural complexity
        if isinstance(request_data.get("content"), dict):
            nested_levels = self._count_nested_levels(request_data["content"])
            complexity += min(0.2, nested_levels * 0.05)
        
        # Task type complexity
        task_type = context.get("task_type", "").lower()
        complex_types = ["strategic", "financial", "analysis", "planning"]
        simple_types = ["research", "data", "collection", "basic"]
        
        if any(ct in task_type for ct in complex_types):
            complexity += 0.1
        elif any(st in task_type for st in simple_types):
            complexity -= 0.1
        
        return max(0.0, min(1.0, complexity))
    
    async def _detect_placeholder_content(self, content: Any) -> bool:
        """
        Rileva se il contenuto ha placeholder
        """
        
        content_str = str(content).lower()
        
        placeholder_patterns = [
            r'\[.*?\]', r'\{.*?\}', r'<.*?>', 
            r'placeholder', r'example', r'sample',
            r'your\s+(?:company|name|email)',
            r'insert\s+(?:here|your)',
            r'lorem\s+ipsum'
        ]
        
        for pattern in placeholder_patterns:
            if re.search(pattern, content_str):
                return True
        
        return False
    
    def _count_nested_levels(self, data: Any, current_level: int = 0) -> int:
        """
        Conta livelli di nesting nella struttura dati
        """
        
        if current_level > 5:  # Prevent infinite recursion
            return current_level
        
        max_level = current_level
        
        if isinstance(data, dict):
            for value in data.values():
                level = self._count_nested_levels(value, current_level + 1)
                max_level = max(max_level, level)
        elif isinstance(data, list) and data:
            for item in data[:3]:  # Check first 3 items only
                level = self._count_nested_levels(item, current_level + 1)
                max_level = max(max_level, level)
        
        return max_level
    
    async def _generate_prediction_reasoning(
        self, 
        features: Dict[str, Any], 
        prediction_score: float
    ) -> str:
        """
        Genera reasoning leggibile per la predizione
        """
        
        reasons = []
        
        # Quality-based reasoning
        quality = features.get("quality_score", 0)
        if quality > 0.8:
            reasons.append(f"High quality score ({quality:.1%})")
        elif quality < 0.5:
            reasons.append(f"Low quality score ({quality:.1%})")
        
        # Completeness reasoning
        completeness = features.get("content_completeness", 0)
        if completeness > 0.85:
            reasons.append(f"Well-structured content ({completeness:.1%} complete)")
        elif completeness < 0.6:
            reasons.append(f"Incomplete content ({completeness:.1%} complete)")
        
        # Historical reasoning
        similarity = features.get("historical_similarity", 0)
        if similarity > 0.8:
            reasons.append("Strong similarity to previously approved requests")
        elif similarity < 0.4:
            reasons.append("Limited historical precedent")
        
        # Agent reasoning
        track_record = features.get("agent_track_record", 0)
        if track_record > 0.85:
            reasons.append("Excellent agent track record")
        elif track_record < 0.6:
            reasons.append("Agent needs performance improvement")
        
        # Placeholder warning
        if features.get("has_placeholder_content", False):
            reasons.append("⚠️ Contains placeholder content")
        
        if not reasons:
            reasons = ["Standard prediction based on available features"]
        
        return "; ".join(reasons)
    
    def update_approval_pattern(
        self, 
        request_type: str, 
        quality_score: float, 
        was_approved: bool
    ):
        """
        Aggiorna pattern di approvazione per migliorare predizioni future
        """
        
        if was_approved:
            self.approval_patterns[request_type].append(quality_score)
            
            # Keep only recent patterns (last 100)
            if len(self.approval_patterns[request_type]) > 100:
                self.approval_patterns[request_type] = self.approval_patterns[request_type][-100:]
        
        logger.debug(f"📚 PATTERN UPDATE: {request_type} - Quality: {quality_score:.2f}, Approved: {was_approved}")

# Global instance
predictive_approval_engine = PredictiveApprovalEngine()
