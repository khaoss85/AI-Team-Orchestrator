"""
Universal Language Engine - Pillar 3: Universal & Language-Agnostic
Provides automatic language detection, content localization, and domain-agnostic features.
"""

import os
import re
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from uuid import UUID
from datetime import datetime
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class UniversalLanguageEngine:
    """
    Universal Language Support Engine (Pillar 3: 100% Implementation)
    
    Provides:
    - Automatic language detection
    - Content localization and translation
    - Domain-agnostic content generation
    - Cultural adaptation for global markets
    - Language-agnostic quality assessment
    """
    
    def __init__(self, openai_client: AsyncOpenAI = None):
        self.openai_client = openai_client or AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Configuration
        self.default_language = os.getenv("DEFAULT_LANGUAGE", "en")
        self.supported_languages = os.getenv("SUPPORTED_LANGUAGES", "en,es,fr,de,it,pt,zh,ja,ko,ar,hi").split(",")
        self.auto_translation_enabled = os.getenv("AUTO_TRANSLATION_ENABLED", "true").lower() == "true"
        self.cultural_adaptation_enabled = os.getenv("CULTURAL_ADAPTATION_ENABLED", "true").lower() == "true"
        
        # Language patterns for detection
        self.language_patterns = {
            'en': [r'\b(the|and|or|but|in|on|at|to|for|of|with|by)\b', r'\b(is|are|was|were|have|has|had)\b'],
            'es': [r'\b(el|la|los|las|y|o|pero|en|de|con|por|para)\b', r'\b(es|son|era|fueron|tiene|tenía)\b'],
            'fr': [r'\b(le|la|les|et|ou|mais|en|de|avec|par|pour)\b', r'\b(est|sont|était|étaient|avoir|avait)\b'],
            'de': [r'\b(der|die|das|und|oder|aber|in|auf|zu|für|von)\b', r'\b(ist|sind|war|waren|haben|hatte)\b'],
            'it': [r'\b(il|la|i|le|e|o|ma|in|di|con|per)\b', r'\b(è|sono|era|erano|avere|aveva)\b'],
            'pt': [r'\b(o|a|os|as|e|ou|mas|em|de|com|por|para)\b', r'\b(é|são|era|eram|ter|tinha)\b'],
            'zh': [r'[\u4e00-\u9fff]', r'[的|和|或|但|在|是|有|了|要|会]'],
            'ja': [r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]', r'[です|である|が|を|に|は|と|で]'],
            'ko': [r'[\uac00-\ud7af]', r'[이|가|을|를|에|는|과|와|로]'],
            'ar': [r'[\u0600-\u06ff]', r'[في|من|على|إلى|مع|هذا|التي|التي]'],
            'hi': [r'[\u0900-\u097f]', r'[का|की|को|में|से|और|या|है]']
        }
        
        logger.info("🌍 Universal Language Engine initialized - Pillar 3: Global Support")
    
    async def detect_language(self, content: str) -> Dict[str, Any]:
        """
        Detect language of content using pattern matching + AI verification
        """
        try:
            # Pattern-based detection (fast)
            pattern_scores = {}
            for lang, patterns in self.language_patterns.items():
                score = 0
                for pattern in patterns:
                    matches = len(re.findall(pattern, content.lower(), re.IGNORECASE))
                    score += matches
                
                # Normalize by content length
                pattern_scores[lang] = score / max(len(content.split()), 1)
            
            # Get top candidates
            top_candidates = sorted(pattern_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            
            # AI verification for ambiguous cases
            if len(top_candidates) > 1 and top_candidates[0][1] - top_candidates[1][1] < 0.1:
                ai_detection = await self._ai_language_detection(content, [c[0] for c in top_candidates])
                detected_language = ai_detection.get("language", top_candidates[0][0])
                confidence = ai_detection.get("confidence", 0.7)
            else:
                detected_language = top_candidates[0][0]
                confidence = min(top_candidates[0][1] * 10, 1.0)
            
            return {
                "detected_language": detected_language,
                "confidence": confidence,
                "pattern_scores": dict(top_candidates[:3]),
                "is_multilingual": len([s for s in pattern_scores.values() if s > 0.1]) > 1
            }
            
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return {
                "detected_language": self.default_language,
                "confidence": 0.5,
                "error": str(e)
            }
    
    async def _ai_language_detection(self, content: str, candidates: List[str]) -> Dict[str, Any]:
        """AI-powered language detection for ambiguous cases"""
        try:
            prompt = f"""
            Detect the primary language of this content. Choose from: {', '.join(candidates)}
            
            Content: "{content[:500]}..."
            
            Respond with JSON:
            {{
                "language": "language_code",
                "confidence": 0.95,
                "reasoning": "brief explanation"
            }}
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"AI language detection failed: {e}")
            return {"language": candidates[0], "confidence": 0.6}
    
    async def translate_content(self, content: str, target_language: str, 
                              source_language: str = None, preserve_structure: bool = True) -> Dict[str, Any]:
        """
        Translate content while preserving business context and structure
        """
        try:
            if not source_language:
                detection = await self.detect_language(content)
                source_language = detection["detected_language"]
            
            # Skip translation if already in target language
            if source_language == target_language:
                return {
                    "translated_content": content,
                    "source_language": source_language,
                    "target_language": target_language,
                    "translation_quality": 1.0,
                    "skipped": True
                }
            
            # AI-powered translation with business context preservation
            translation_result = await self._ai_translate_with_context(
                content, source_language, target_language, preserve_structure
            )
            
            return translation_result
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return {
                "translated_content": content,
                "error": str(e),
                "translation_quality": 0.0
            }
    
    async def _ai_translate_with_context(self, content: str, source_lang: str, 
                                       target_lang: str, preserve_structure: bool) -> Dict[str, Any]:
        """AI translation with business context and structure preservation"""
        try:
            structure_instruction = ""
            if preserve_structure:
                structure_instruction = """
                IMPORTANT: Preserve all formatting, structure, and business terminology.
                - Keep technical terms, product names, and company names unchanged
                - Maintain bullet points, numbered lists, and headers
                - Preserve any JSON, code, or data structures exactly
                - Adapt cultural references appropriately for target market
                """
            
            prompt = f"""
            Translate the following business content from {source_lang} to {target_lang}.
            
            {structure_instruction}
            
            Focus on:
            1. Business accuracy and professional tone
            2. Cultural appropriateness for {target_lang} markets
            3. Industry-standard terminology
            4. Clear, actionable language for business stakeholders
            
            Content to translate:
            {content}
            
            Respond with JSON:
            {{
                "translated_content": "professionally translated content",
                "translation_quality": 0.95,
                "cultural_adaptations": ["list of any cultural adaptations made"],
                "preserved_terms": ["list of terms kept unchanged"],
                "notes": "any important translation notes"
            }}
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            # Add metadata
            result.update({
                "source_language": source_lang,
                "target_language": target_lang,
                "translation_method": "ai_contextual",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"AI translation failed: {e}")
            return {
                "translated_content": content,
                "translation_quality": 0.0,
                "error": str(e)
            }
    
    async def generate_domain_agnostic_content(self, requirements: Dict[str, Any], 
                                             target_language: str = None) -> Dict[str, Any]:
        """
        Generate content that works across different business domains and languages
        """
        try:
            target_language = target_language or self.default_language
            
            # Extract domain-agnostic requirements
            content_type = requirements.get("content_type", "document")
            purpose = requirements.get("purpose", "general")
            audience = requirements.get("audience", "business_stakeholders")
            industry = requirements.get("industry", "generic")
            
            prompt = f"""
            Generate domain-agnostic {content_type} content in {target_language} that can be adapted for any industry.
            
            Requirements:
            - Purpose: {purpose}
            - Target Audience: {audience}
            - Industry Context: {industry}
            - Language: {target_language}
            
            Create content that:
            1. Uses universal business principles
            2. Avoids industry-specific jargon
            3. Includes adaptable templates/frameworks
            4. Provides clear, actionable guidance
            5. Works across cultural contexts
            6. Maintains professional standards globally
            
            Focus on universal business concepts like:
            - Goal achievement and progress tracking
            - Quality improvement processes
            - Team collaboration frameworks
            - Decision-making methodologies
            - Performance measurement approaches
            
            Respond with JSON:
            {{
                "content": "domain-agnostic content",
                "adaptability_score": 0.9,
                "universal_principles": ["list of universal principles used"],
                "customization_points": ["areas where industry-specific adaptation can be made"],
                "language_quality": 0.95,
                "cultural_considerations": ["relevant cultural considerations"]
            }}
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            # Add metadata
            result.update({
                "generated_for": requirements,
                "target_language": target_language,
                "generation_method": "domain_agnostic_ai",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Domain-agnostic content generation failed: {e}")
            return {
                "content": "Error generating content",
                "error": str(e),
                "adaptability_score": 0.0
            }
    
    async def assess_language_quality(self, content: str, language: str = None) -> Dict[str, Any]:
        """
        Language-agnostic quality assessment
        """
        try:
            if not language:
                detection = await self.detect_language(content)
                language = detection["detected_language"]
            
            # Universal quality metrics that work across languages
            assessment = await self._ai_universal_quality_assessment(content, language)
            
            return assessment
            
        except Exception as e:
            logger.error(f"Language quality assessment failed: {e}")
            return {
                "overall_quality": 0.5,
                "error": str(e)
            }
    
    async def _ai_universal_quality_assessment(self, content: str, language: str) -> Dict[str, Any]:
        """AI-powered universal quality assessment"""
        try:
            prompt = f"""
            Assess the quality of this {language} content using universal quality principles.
            
            Content: "{content}"
            
            Evaluate on universal dimensions (0.0-1.0):
            1. CLARITY: Is the message clear and easy to understand?
            2. COMPLETENESS: Does it provide sufficient information?
            3. COHERENCE: Is the content logically structured?
            4. CORRECTNESS: Is the information accurate and well-presented?
            5. CULTURAL_APPROPRIATENESS: Is it suitable for the target culture?
            6. ACTIONABILITY: Can readers take concrete action based on this?
            7. PROFESSIONAL_STANDARD: Does it meet professional business standards?
            
            Respond with JSON:
            {{
                "overall_quality": 0.85,
                "clarity": 0.9,
                "completeness": 0.8,
                "coherence": 0.9,
                "correctness": 0.85,
                "cultural_appropriateness": 0.8,
                "actionability": 0.9,
                "professional_standard": 0.85,
                "language_specific_notes": "any language-specific observations",
                "improvement_suggestions": ["specific suggestions for improvement"],
                "universal_principles_met": ["list of universal quality principles satisfied"]
            }}
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            result.update({
                "assessed_language": language,
                "assessment_method": "universal_ai",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Universal quality assessment failed: {e}")
            return {
                "overall_quality": 0.5,
                "error": str(e)
            }
    
    async def batch_process_multilingual_content(self, content_items: List[Dict[str, Any]], 
                                               target_language: str) -> Dict[str, Any]:
        """
        Batch process multiple content items for language support
        """
        try:
            results = []
            
            for item in content_items:
                content = item.get("content", "")
                item_id = item.get("id", "unknown")
                
                # Detect source language
                detection = await self.detect_language(content)
                
                # Translate if needed
                if detection["detected_language"] != target_language:
                    translation = await self.translate_content(content, target_language)
                    processed_content = translation["translated_content"]
                    quality = translation.get("translation_quality", 0.0)
                else:
                    processed_content = content
                    quality = 1.0
                
                # Assess quality
                quality_assessment = await self.assess_language_quality(processed_content, target_language)
                
                results.append({
                    "item_id": item_id,
                    "original_content": content,
                    "processed_content": processed_content,
                    "source_language": detection["detected_language"],
                    "target_language": target_language,
                    "translation_quality": quality,
                    "content_quality": quality_assessment["overall_quality"],
                    "processing_notes": {
                        "language_detection": detection,
                        "quality_assessment": quality_assessment
                    }
                })
            
            # Summary
            total_items = len(results)
            translations_needed = len([r for r in results if r["source_language"] != r["target_language"]])
            avg_quality = sum(r["content_quality"] for r in results) / total_items if total_items > 0 else 0
            
            return {
                "processed_items": results,
                "summary": {
                    "total_items": total_items,
                    "translations_performed": translations_needed,
                    "average_quality": avg_quality,
                    "languages_detected": list(set(r["source_language"] for r in results)),
                    "target_language": target_language,
                    "processing_timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Batch multilingual processing failed: {e}")
            return {
                "error": str(e),
                "processed_items": []
            }

# Global instance
universal_language_engine = UniversalLanguageEngine()

# Convenience functions
async def detect_content_language(content: str) -> Dict[str, Any]:
    """Detect language of content"""
    return await universal_language_engine.detect_language(content)

async def translate_to_language(content: str, target_language: str) -> Dict[str, Any]:
    """Translate content to target language"""
    return await universal_language_engine.translate_content(content, target_language)

async def generate_universal_content(requirements: Dict[str, Any], language: str = "en") -> Dict[str, Any]:
    """Generate domain-agnostic content"""
    return await universal_language_engine.generate_domain_agnostic_content(requirements, language)