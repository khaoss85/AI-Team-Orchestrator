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
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    async def analyze_asset_quality(
        self, 
        asset_content: str, 
        asset_type: str,
        business_context: str,
        domain: str = "unknown"
    ) -> Dict[str, Any]:
        """
        🤖 AI-DRIVEN QUALITY ANALYSIS
        Universal quality analysis that works for any domain/asset type
        """
        try:
            prompt = f"""
Analyze the quality and business value of this asset using AI reasoning.

BUSINESS CONTEXT: {business_context}
ASSET TYPE: {asset_type}
DOMAIN: {domain}
CONTENT: {asset_content}

Perform a comprehensive analysis without using predefined criteria. Use AI reasoning to evaluate:

1. BUSINESS ACTIONABILITY: How immediately useful is this for business operations?
2. CONTENT COMPLETENESS: How complete and detailed is the information?
3. REAL-WORLD APPLICABILITY: Can this be used as-is in a professional setting?
4. DOMAIN APPROPRIATENESS: How well does this fit the business context?
5. PLACEHOLDER DETECTION: Does this contain fake/example data?

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
    "reasoning": {{
        "strengths": ["strength 1", "strength 2"],
        "weaknesses": ["weakness 1", "weakness 2"],
        "business_impact": "assessment of business value"
    }}
}}
"""

            # Use rate limiting if available
            try:
                from utils.rate_limiter import safe_openai_call
                response = await safe_openai_call(
                    self.client, "skill_analysis",
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an AI business analyst specializing in universal content quality assessment. Analyze any content type for any industry without relying on predefined criteria."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    response_format={"type": "json_object"}
                )
            except ImportError:
                # Fallback without rate limiting
                response = await self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an AI business analyst specializing in universal content quality assessment. Analyze any content type for any industry without relying on predefined criteria."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    response_format={"type": "json_object"}
                )
            
            analysis = json.loads(response.choices[0].message.content)
            analysis["analyzed_at"] = datetime.now().isoformat()
            analysis["analysis_method"] = "ai_driven_universal"
            
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
        🤖 AI-DRIVEN ASSET TYPE DETECTION
        Let AI determine what type of asset this is, no hardcoded types
        """
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

            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an AI business analyst that intelligently classifies any content into business asset types without predefined categories."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
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
        🤖 AI-DRIVEN ENHANCEMENT SUGGESTIONS
        Generate specific, actionable suggestions to improve content quality
        """
        try:
            prompt = f"""
Based on this quality analysis, suggest specific enhancement actions.

BUSINESS CONTEXT: {business_context}
CURRENT CONTENT: {current_content}
QUALITY ANALYSIS: {json.dumps(quality_analysis, indent=2)}

Generate 3-5 specific, actionable enhancement suggestions that will:
1. Replace placeholder content with real data
2. Improve business actionability
3. Enhance professional quality
4. Increase immediate usability

Each suggestion should be specific enough to implement.

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
    ],
    "content_gaps": ["gap 1", "gap 2"],
    "quick_wins": ["quick improvement 1", "quick improvement 2"],
    "strategic_improvements": ["strategic improvement 1", "strategic improvement 2"]
}}
"""

            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an AI business consultant specializing in content enhancement and business asset optimization."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            suggestions = json.loads(response.choices[0].message.content)
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