# backend/ai_skill_analyzer.py
"""
🤖 AI-Driven Skill Analysis System
Universal skill analysis without hardcoding, using AI to interpret results
"""

import logging
import json
import openai
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class AISkillAnalyzer:
    """
    🌍 AI-DRIVEN UNIVERSAL SKILL ANALYZER
    Analyzes any content/deliverable using AI without hardcoded business logic
    """
    
    def __init__(self):
        # The AI client is now managed by the AIProviderManager
        pass
    
    async def analyze_asset_quality(
        self, 
        asset_content: str, 
        asset_type: str,
        business_context: str,
        domain: str = "unknown"
    ) -> Dict[str, Any]:
        """
        🤖 AI-DRIVEN QUALITY ANALYSIS (MIGRATED TO SDK)
        Universal quality analysis that works for any domain/asset type
        """
        from services.ai_provider_abstraction import ai_provider_manager
        from project_agents.asset_quality_analyzer_agent import ASSET_QUALITY_ANALYZER_AGENT_CONFIG
        
        try:
            prompt = f"""
Analyze the quality and business value of this asset using AI reasoning.

BUSINESS CONTEXT: {business_context}
ASSET TYPE: {asset_type}
DOMAIN: {domain}
CONTENT: {asset_content}

Perform a comprehensive analysis without using predefined criteria. Use AI reasoning to evaluate:
1. BUSINESS ACTIONABILITY
2. CONTENT COMPLETENESS
3. REAL-WORLD APPLICABILITY
4. DOMAIN APPROPRIATENESS
5. PLACEHOLDER DETECTION

Provide scores (0-100) and detailed reasoning for each dimension.

Response format:
{{
    "overall_quality_score": 0-100,
    "business_actionability": 0-100,
    "content_completeness": 0-100,
    "real_world_applicability": 0-100,
    "domain_appropriateness": 0-100,
    "has_placeholder_content": true/false,
    "quality_tier": "excellent|good|fair|poor",
    "enhancement_suggestions": ["specific suggestion 1", "specific suggestion 2"],
    "usability_assessment": "detailed explanation of how this can be used",
    "improvement_priority": "high|medium|low",
    "reasoning": {{ ... }}
}}
"""
            analysis = await ai_provider_manager.call_ai(
                provider_type='openai_sdk',
                agent=ASSET_QUALITY_ANALYZER_AGENT_CONFIG,
                prompt=prompt,
                response_format={"type": "json_object"}
            )
            
            analysis["analyzed_at"] = datetime.now().isoformat()
            analysis["analysis_method"] = "ai_driven_universal_sdk"
            
            return analysis
            
        except Exception as e:
            logger.error(f"🤖 AI skill analysis failed: {e}")
            return self._fallback_analysis()
    
    async def detect_asset_type_ai(
        self,
        content: str,
        business_context: str
    ) -> Dict[str, Any]:
        """
        🤖 AI-DRIVEN ASSET TYPE DETECTION (MIGRATED TO SDK)
        Let AI determine what type of asset this is, no hardcoded types
        """
        from services.ai_provider_abstraction import ai_provider_manager
        from project_agents.asset_type_detector_agent import ASSET_TYPE_DETECTOR_AGENT_CONFIG
        
        try:
            prompt = f"""
Analyze this content and determine what type of business asset it represents.

BUSINESS CONTEXT: {business_context}
CONTENT: {content}

Use AI reasoning to classify this asset. Don't limit yourself to predefined categories.
Consider what this content actually provides and how it would be used in business.

Response format:
{{
    "primary_type": "descriptive name for the asset type",
    "secondary_types": ["alternative classification 1", "alternative classification 2"],
    "business_function": "what business function this serves",
    "use_cases": ["use case 1", "use case 2", "use case 3"],
    "target_audience": "who would use this asset",
    "format_classification": "database|document|template|dashboard|strategy|analysis",
    "confidence": 0-100,
    "reasoning": "why this classification makes sense"
}}
"""
            return await ai_provider_manager.call_ai(
                provider_type='openai_sdk',
                agent=ASSET_TYPE_DETECTOR_AGENT_CONFIG,
                prompt=prompt,
                response_format={"type": "json_object"}
            )
            
        except Exception as e:
            logger.error(f"🤖 AI asset type detection failed: {e}")
            return {
                "primary_type": "strategy_document",
                "confidence": 50,
                "reasoning": "Fallback classification due to analysis error"
            }
    
    async def suggest_enhancement_actions(
        self,
        current_content: str,
        quality_analysis: Dict[str, Any],
        business_context: str
    ) -> List[Dict[str, Any]]:
        """
        🤖 AI-DRIVEN ENHANCEMENT SUGGESTIONS (MIGRATED TO SDK)
        Generate specific, actionable suggestions to improve content quality
        """
        from services.ai_provider_abstraction import ai_provider_manager
        from project_agents.enhancement_suggester_agent import ENHANCEMENT_SUGGESTER_AGENT_CONFIG
        
        try:
            prompt = f"""
Based on this quality analysis, suggest specific enhancement actions.

BUSINESS CONTEXT: {business_context}
CURRENT CONTENT: {current_content}
QUALITY ANALYSIS: {json.dumps(quality_analysis, indent=2)}

Generate 3-5 specific, actionable enhancement suggestions.

Response format:
{{
    "enhancement_actions": [
        {{
            "action": "specific action to take",
            "reasoning": "why this improvement is needed",
            "impact": "what business impact this will have",
            "effort": "low|medium|high",
            "priority": "high|medium|low",
            "implementation": "how to implement this"
        }}
    ]
}}
"""
            suggestions = await ai_provider_manager.call_ai(
                provider_type='openai_sdk',
                agent=ENHANCEMENT_SUGGESTER_AGENT_CONFIG,
                prompt=prompt,
                response_format={"type": "json_object"}
            )
            
            return suggestions.get("enhancement_actions", [])
            
        except Exception as e:
            logger.error(f"🤖 AI enhancement suggestions failed: {e}")
            return []
    
    def _fallback_analysis(self) -> Dict[str, Any]:
        """Fallback analysis when AI analysis fails"""
        return {
            "overall_quality_score": 50,
            "business_actionability": 50,
            "content_completeness": 50,
            "real_world_applicability": 50,
            "domain_appropriateness": 50,
            "has_placeholder_content": True,
            "quality_tier": "fair",
            "enhancement_suggestions": ["Review content for completeness", "Add specific business data"],
            "usability_assessment": "Requires enhancement for business use",
            "improvement_priority": "medium",
            "reasoning": {
                "strengths": ["Structured format"],
                "weaknesses": ["Analysis failed, requires manual review"],
                "business_impact": "Limited due to analysis failure"
            },
            "analyzed_at": datetime.now().isoformat(),
            "analysis_method": "fallback"
        }

# Global instance
ai_skill_analyzer = AISkillAnalyzer()