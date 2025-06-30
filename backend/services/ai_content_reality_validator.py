"""
🤖 AI Content Reality Validator
Pure AI-driven validation of authentic vs template content

Pillar 4: Authentic Content - Ensures only real, business-specific content is delivered
Pillar 8: No Hardcode - Zero predefined patterns for fake content detection
Pillar 9: Adaptive AI - Learns to distinguish real vs template content across domains
Pillar 11: Self-Enhancement - Improves validation accuracy through feedback
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ContentRealityLevel(Enum):
    """Levels of content reality"""
    AUTHENTIC_BUSINESS_READY = "authentic_business_ready"  # Real, specific, immediately usable
    REAL_BUT_INCOMPLETE = "real_but_incomplete"  # Real content but missing elements
    SEMI_GENERIC = "semi_generic"  # Mix of real and template elements
    TEMPLATE_GENERIC = "template_generic"  # Generic template content
    PLACEHOLDER_FAKE = "placeholder_fake"  # Clear placeholder/fake content

@dataclass
class ContentValidationResult:
    """Result of AI content reality validation"""
    reality_level: ContentRealityLevel
    business_specificity_score: float  # 0-100, how specific to the business
    usability_score: float  # 0-100, how ready to use without modification
    authenticity_confidence: float  # 0-100, AI confidence in the assessment
    validation_reasoning: str  # AI explanation of the validation
    improvement_suggestions: List[str]  # How to make content more real/specific
    quality_gates_passed: Dict[str, bool]  # Specific quality checks
    validation_metadata: Dict[str, Any]  # Additional validation data

class AIContentRealityValidator:
    """
    🤖 Pure AI-Driven Content Reality Validation
    Zero hardcoded patterns for fake/template detection
    """
    
    def __init__(self):
        self.validation_history = []  # For self-learning
        self.quality_thresholds = {
            "business_specificity_min": 70,
            "usability_min": 80,
            "authenticity_confidence_min": 75
        }
        
    async def validate_content_authenticity(
        self,
        content: Dict[str, Any],
        business_context: Dict[str, Any] = None,
        goal_context: str = None
    ) -> ContentValidationResult:
        """
        🤖 AI-DRIVEN: Validate content authenticity vs template nature
        
        Args:
            content: Content to validate
            business_context: Business context for specificity validation
            goal_context: Goal context for relevance validation
            
        Returns:
            ContentValidationResult with AI assessment
        """
        try:
            logger.info("🤖 Starting AI content reality validation...")
            
            # Step 1: AI Authenticity Assessment
            authenticity_analysis = await self._ai_assess_authenticity(
                content, 
                business_context
            )
            
            # Step 2: AI Business Specificity Analysis
            specificity_analysis = await self._ai_analyze_business_specificity(
                content,
                business_context
            )
            
            # Step 3: AI Usability Assessment
            usability_analysis = await self._ai_assess_usability(
                content,
                goal_context
            )
            
            # Step 4: AI Quality Gates Evaluation
            quality_gates = await self._ai_evaluate_quality_gates(
                content,
                authenticity_analysis,
                specificity_analysis,
                usability_analysis
            )
            
            # Step 5: AI Reality Level Classification
            reality_level = await self._ai_classify_reality_level(
                authenticity_analysis,
                specificity_analysis,
                usability_analysis
            )
            
            # Step 6: AI Improvement Suggestions
            improvements = await self._ai_generate_improvement_suggestions(
                content,
                reality_level,
                authenticity_analysis,
                business_context
            )
            
            # Compile validation result
            result = ContentValidationResult(
                reality_level=reality_level,
                business_specificity_score=specificity_analysis.get('specificity_score', 0),
                usability_score=usability_analysis.get('usability_score', 0),
                authenticity_confidence=authenticity_analysis.get('confidence', 0),
                validation_reasoning=self._compile_validation_reasoning(
                    authenticity_analysis,
                    specificity_analysis,
                    usability_analysis,
                    reality_level
                ),
                improvement_suggestions=improvements,
                quality_gates_passed=quality_gates,
                validation_metadata={
                    "validation_timestamp": datetime.now().isoformat(),
                    "business_context_available": business_context is not None,
                    "goal_context_available": goal_context is not None,
                    "content_size": len(str(content))
                }
            )
            
            # Self-learning: Store validation for improvement
            await self._store_validation_learning(content, result)
            
            logger.info(f"✅ AI validation complete: Level={reality_level.value}, Specificity={result.business_specificity_score:.1f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in AI content validation: {e}")
            return self._create_error_result(str(e))
    
    async def _ai_assess_authenticity(
        self, 
        content: Dict[str, Any], 
        business_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        🤖 AI assessment of content authenticity vs template nature
        """
        try:
            from ai_quality_assurance.smart_evaluator import smart_evaluator
            
            business_info = self._format_business_context(business_context)
            
            authenticity_prompt = f"""
Valuta l'AUTENTICITÀ di questo contenuto usando solo comprensione semantica.

CONTENUTO DA VALIDARE:
{json.dumps(content, indent=2)}

CONTESTO BUSINESS:
{business_info}

VALUTAZIONE RICHIESTA:
Analizza semanticamente se il contenuto è:

1. AUTENTICO: Contenuto specifico, concreto, implementabile
   - Contiene dettagli specifici e actionable?
   - È personalizzato per un business reale?
   - È immediatamente utilizzabile?

2. TEMPLATE: Contenuto generico, placeholder, esempi
   - Usa linguaggio generico ("Aimed at...", "Designed to...")?
   - Contiene placeholder o esempi generici?
   - Richiede personalizzazione significativa?

3. MISTO: Combinazione di elementi reali e template

NON usare pattern matching predefiniti. Usa comprensione semantica profonda.

Rispondi in JSON:
{{
    "authenticity_assessment": "autentico/template/misto",
    "confidence": 0-100,
    "specific_indicators": {{
        "authentic_elements": ["elementi che indicano contenuto reale"],
        "template_elements": ["elementi che indicano template/generico"],
        "mixed_elements": ["elementi ambigui"]
    }},
    "business_alignment": 0-100,
    "implementation_readiness": 0-100,
    "detailed_reasoning": "spiegazione dettagliata della valutazione",
    "improvement_areas": ["aree dove il contenuto potrebbe essere più autentico"]
}}
"""
            
            ai_response = await smart_evaluator.evaluate_with_ai(
                authenticity_prompt,
                context="authenticity_assessment",
                max_tokens=1500
            )
            
            if isinstance(ai_response, str):
                try:
                    assessment = json.loads(ai_response)
                except json.JSONDecodeError:
                    assessment = self._parse_authenticity_fallback(ai_response)
            else:
                assessment = ai_response
                
            return assessment
            
        except Exception as e:
            logger.error(f"Error in AI authenticity assessment: {e}")
            return {
                "authenticity_assessment": "unknown",
                "confidence": 0,
                "specific_indicators": {"authentic_elements": [], "template_elements": [], "mixed_elements": []},
                "business_alignment": 0,
                "implementation_readiness": 0,
                "detailed_reasoning": f"Assessment failed: {e}",
                "improvement_areas": ["Assessment error"]
            }
    
    async def _ai_analyze_business_specificity(
        self,
        content: Dict[str, Any],
        business_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        🤖 AI analysis of business specificity vs generic content
        """
        try:
            from ai_quality_assurance.smart_evaluator import smart_evaluator
            
            business_info = self._format_business_context(business_context)
            
            specificity_prompt = f"""
Analizza quanto questo contenuto è SPECIFICO per questo business vs generico.

CONTENUTO:
{json.dumps(content, indent=2)}

CONTESTO BUSINESS:
{business_info}

ANALISI RICHIESTA:
1. Il contenuto è personalizzato per questo business specifico?
2. Contiene elementi che lo rendono unico per questo caso d'uso?
3. È applicabile solo a questo business o a qualsiasi business simile?
4. Quanto effort servirebbe per adattarlo ad un altro business?

Valuta specificità semantica, non solo presenza di nomi/brand.

Rispondi in JSON:
{{
    "specificity_score": 0-100,
    "specificity_level": "altamente_specifico/moderatamente_specifico/generico/molto_generico",
    "unique_elements": ["elementi che lo rendono unico per questo business"],
    "generic_elements": ["elementi che sono generici/universali"],
    "customization_indicators": ["indicatori di personalizzazione specifica"],
    "portability_assessment": "quanto facilmente portabile ad altri business",
    "business_context_integration": 0-100,
    "specificity_reasoning": "spiegazione del score di specificità"
}}
"""
            
            ai_response = await smart_evaluator.evaluate_with_ai(
                specificity_prompt,
                context="business_specificity",
                max_tokens=1200
            )
            
            if isinstance(ai_response, str):
                try:
                    analysis = json.loads(ai_response)
                except json.JSONDecodeError:
                    analysis = self._parse_specificity_fallback(ai_response)
            else:
                analysis = ai_response
                
            return analysis
            
        except Exception as e:
            logger.error(f"Error in AI specificity analysis: {e}")
            return {
                "specificity_score": 0,
                "specificity_level": "unknown",
                "unique_elements": [],
                "generic_elements": ["Analysis failed"],
                "customization_indicators": [],
                "portability_assessment": "unknown",
                "business_context_integration": 0,
                "specificity_reasoning": f"Analysis failed: {e}"
            }
    
    async def _ai_assess_usability(
        self,
        content: Dict[str, Any],
        goal_context: str
    ) -> Dict[str, Any]:
        """
        🤖 AI assessment of content usability (ready to use vs needs work)
        """
        try:
            from ai_quality_assurance.smart_evaluator import smart_evaluator
            
            usability_prompt = f"""
Valuta quanto questo contenuto è UTILIZZABILE direttamente senza modifiche.

CONTENUTO:
{json.dumps(content, indent=2)}

CONTESTO GOAL:
{goal_context or "No specific goal context"}

VALUTAZIONE USABILITÀ:
1. È utilizzabile immediatamente "as-is"?
2. Che modifiche/completamenti richiede?
3. Quanto effort serve per renderlo business-ready?
4. Mancano elementi critici per l'utilizzo?

Focus su USABILITÀ PRATICA, non solo completezza teorica.

Rispondi in JSON:
{{
    "usability_score": 0-100,
    "immediate_usability": true/false,
    "required_modifications": ["modifiche necessarie per l'uso"],
    "missing_critical_elements": ["elementi critici mancanti"],
    "effort_to_business_ready": "nessuno/minimo/moderato/significativo/estensivo",
    "usability_blockers": ["elementi che bloccano l'utilizzo immediato"],
    "ready_to_use_elements": ["parti utilizzabili immediatamente"],
    "usability_assessment": "explanation of usability level",
    "improvement_priority": ["modifiche in ordine di priorità"]
}}
"""
            
            ai_response = await smart_evaluator.evaluate_with_ai(
                usability_prompt,
                context="usability_assessment",
                max_tokens=1200
            )
            
            if isinstance(ai_response, str):
                try:
                    assessment = json.loads(ai_response)
                except json.JSONDecodeError:
                    assessment = self._parse_usability_fallback(ai_response)
            else:
                assessment = ai_response
                
            return assessment
            
        except Exception as e:
            logger.error(f"Error in AI usability assessment: {e}")
            return {
                "usability_score": 0,
                "immediate_usability": False,
                "required_modifications": ["Assessment failed"],
                "missing_critical_elements": ["Unknown"],
                "effort_to_business_ready": "unknown",
                "usability_blockers": ["Assessment error"],
                "ready_to_use_elements": [],
                "usability_assessment": f"Assessment failed: {e}",
                "improvement_priority": []
            }
    
    async def _ai_evaluate_quality_gates(
        self,
        content: Dict[str, Any],
        authenticity_analysis: Dict[str, Any],
        specificity_analysis: Dict[str, Any],
        usability_analysis: Dict[str, Any]
    ) -> Dict[str, bool]:
        """
        🤖 AI evaluation of quality gates for content approval
        """
        try:
            quality_gates = {}
            
            # Gate 1: Authenticity Gate
            authenticity_score = authenticity_analysis.get('confidence', 0)
            quality_gates['authenticity_gate'] = authenticity_score >= self.quality_thresholds['authenticity_confidence_min']
            
            # Gate 2: Business Specificity Gate
            specificity_score = specificity_analysis.get('specificity_score', 0)
            quality_gates['business_specificity_gate'] = specificity_score >= self.quality_thresholds['business_specificity_min']
            
            # Gate 3: Usability Gate
            usability_score = usability_analysis.get('usability_score', 0)
            quality_gates['usability_gate'] = usability_score >= self.quality_thresholds['usability_min']
            
            # Gate 4: Template Detection Gate (inverse logic)
            template_indicators = authenticity_analysis.get('specific_indicators', {}).get('template_elements', [])
            quality_gates['template_free_gate'] = len(template_indicators) == 0
            
            # Gate 5: Implementation Readiness Gate
            implementation_readiness = authenticity_analysis.get('implementation_readiness', 0)
            quality_gates['implementation_ready_gate'] = implementation_readiness >= 70
            
            # Gate 6: Business Alignment Gate
            business_alignment = authenticity_analysis.get('business_alignment', 0)
            quality_gates['business_aligned_gate'] = business_alignment >= 70
            
            return quality_gates
            
        except Exception as e:
            logger.error(f"Error in quality gates evaluation: {e}")
            return {
                'authenticity_gate': False,
                'business_specificity_gate': False,
                'usability_gate': False,
                'template_free_gate': False,
                'implementation_ready_gate': False,
                'business_aligned_gate': False
            }
    
    async def _ai_classify_reality_level(
        self,
        authenticity_analysis: Dict[str, Any],
        specificity_analysis: Dict[str, Any],
        usability_analysis: Dict[str, Any]
    ) -> ContentRealityLevel:
        """
        🤖 AI classification of content reality level
        """
        try:
            # Extract scores
            authenticity_confidence = authenticity_analysis.get('confidence', 0)
            authenticity_assessment = authenticity_analysis.get('authenticity_assessment', 'unknown')
            specificity_score = specificity_analysis.get('specificity_score', 0)
            usability_score = usability_analysis.get('usability_score', 0)
            implementation_readiness = authenticity_analysis.get('implementation_readiness', 0)
            
            # AI-driven classification logic
            if (authenticity_assessment == 'autentico' and 
                specificity_score >= 80 and 
                usability_score >= 80 and 
                implementation_readiness >= 80):
                return ContentRealityLevel.AUTHENTIC_BUSINESS_READY
            
            elif (authenticity_assessment == 'autentico' and 
                  specificity_score >= 60 and 
                  usability_score >= 50):
                return ContentRealityLevel.REAL_BUT_INCOMPLETE
            
            elif authenticity_assessment == 'misto':
                return ContentRealityLevel.SEMI_GENERIC
            
            elif authenticity_assessment == 'template':
                return ContentRealityLevel.TEMPLATE_GENERIC
            
            else:
                # Low scores across the board
                if authenticity_confidence < 30 or specificity_score < 30:
                    return ContentRealityLevel.PLACEHOLDER_FAKE
                else:
                    return ContentRealityLevel.TEMPLATE_GENERIC
                    
        except Exception as e:
            logger.error(f"Error in reality level classification: {e}")
            return ContentRealityLevel.PLACEHOLDER_FAKE
    
    async def _ai_generate_improvement_suggestions(
        self,
        content: Dict[str, Any],
        reality_level: ContentRealityLevel,
        authenticity_analysis: Dict[str, Any],
        business_context: Dict[str, Any]
    ) -> List[str]:
        """
        🤖 AI generation of specific improvement suggestions
        """
        try:
            from ai_quality_assurance.smart_evaluator import smart_evaluator
            
            business_info = self._format_business_context(business_context)
            
            improvement_prompt = f"""
Genera suggerimenti specifici e actionable per migliorare questo contenuto.

CONTENUTO ATTUALE:
{json.dumps(content, indent=2)}

LIVELLO REALTÀ: {reality_level.value}

ANALISI AUTENTICITÀ:
{json.dumps(authenticity_analysis, indent=2)}

CONTESTO BUSINESS:
{business_info}

SUGGERIMENTI RICHIESTI:
1. Come rendere il contenuto più specifico per questo business?
2. Come eliminare elementi template/generici?
3. Come migliorare l'usabilità immediata?
4. Che dettagli specifici aggiungere?

Fornisci suggerimenti CONCRETI e IMPLEMENTABILI, non generici.

Rispondi in JSON:
{{
    "priority_improvements": ["miglioramenti critici in ordine di priorità"],
    "specific_additions": ["elementi specifici da aggiungere"],
    "template_replacements": ["come sostituire elementi template con contenuto reale"],
    "business_customizations": ["personalizzazioni specifiche per questo business"],
    "usability_enhancements": ["come migliorare l'utilizzo immediato"],
    "implementation_steps": ["passi per implementare i miglioramenti"]
}}
"""
            
            ai_response = await smart_evaluator.evaluate_with_ai(
                improvement_prompt,
                context="improvement_suggestions",
                max_tokens=1500
            )
            
            if isinstance(ai_response, str):
                try:
                    suggestions = json.loads(ai_response)
                    # Flatten all suggestions into a single list
                    all_suggestions = []
                    for key, value in suggestions.items():
                        if isinstance(value, list):
                            all_suggestions.extend(value)
                    return all_suggestions
                except json.JSONDecodeError:
                    return [f"Improvement suggestion parsing failed: {ai_response[:200]}..."]
            else:
                return ["AI response format error"]
                
        except Exception as e:
            logger.error(f"Error in AI improvement suggestions: {e}")
            return [f"Improvement suggestion generation failed: {e}"]
    
    def _format_business_context(self, business_context: Dict[str, Any]) -> str:
        """Format business context for AI analysis"""
        if not business_context:
            return "No specific business context available"
        
        context_parts = []
        
        if 'name' in business_context:
            context_parts.append(f"Business/Project: {business_context['name']}")
        
        if 'description' in business_context:
            context_parts.append(f"Description: {business_context['description']}")
        
        if 'industry' in business_context:
            context_parts.append(f"Industry: {business_context['industry']}")
        
        if 'target_audience' in business_context:
            context_parts.append(f"Target Audience: {business_context['target_audience']}")
        
        if 'business_model' in business_context:
            context_parts.append(f"Business Model: {business_context['business_model']}")
        
        return "\n".join(context_parts) if context_parts else "General business context"
    
    def _compile_validation_reasoning(
        self,
        authenticity_analysis: Dict[str, Any],
        specificity_analysis: Dict[str, Any],
        usability_analysis: Dict[str, Any],
        reality_level: ContentRealityLevel
    ) -> str:
        """Compile comprehensive validation reasoning"""
        reasoning_parts = []
        
        # Authenticity reasoning
        auth_reasoning = authenticity_analysis.get('detailed_reasoning', '')
        if auth_reasoning:
            reasoning_parts.append(f"AUTHENTICITY: {auth_reasoning}")
        
        # Specificity reasoning
        spec_reasoning = specificity_analysis.get('specificity_reasoning', '')
        if spec_reasoning:
            reasoning_parts.append(f"SPECIFICITY: {spec_reasoning}")
        
        # Usability reasoning
        usab_reasoning = usability_analysis.get('usability_assessment', '')
        if usab_reasoning:
            reasoning_parts.append(f"USABILITY: {usab_reasoning}")
        
        # Overall classification
        reasoning_parts.append(f"CLASSIFICATION: Content classified as {reality_level.value}")
        
        return " | ".join(reasoning_parts)
    
    async def _store_validation_learning(
        self,
        content: Dict[str, Any],
        validation_result: ContentValidationResult
    ):
        """Store validation results for self-learning improvement"""
        try:
            learning_entry = {
                "timestamp": datetime.now().isoformat(),
                "content_size": len(str(content)),
                "reality_level": validation_result.reality_level.value,
                "business_specificity": validation_result.business_specificity_score,
                "usability_score": validation_result.usability_score,
                "authenticity_confidence": validation_result.authenticity_confidence,
                "quality_gates_passed": sum(validation_result.quality_gates_passed.values()),
                "total_quality_gates": len(validation_result.quality_gates_passed)
            }
            
            self.validation_history.append(learning_entry)
            
            # Keep only recent entries for memory efficiency
            if len(self.validation_history) > 100:
                self.validation_history = self.validation_history[-100:]
                
        except Exception as e:
            logger.debug(f"Validation learning storage failed: {e}")
    
    def _create_error_result(self, error_message: str) -> ContentValidationResult:
        """Create error result when validation fails"""
        return ContentValidationResult(
            reality_level=ContentRealityLevel.PLACEHOLDER_FAKE,
            business_specificity_score=0,
            usability_score=0,
            authenticity_confidence=0,
            validation_reasoning=f"Validation failed: {error_message}",
            improvement_suggestions=[f"Fix validation error: {error_message}"],
            quality_gates_passed={},
            validation_metadata={"error": error_message}
        )
    
    # Fallback parsers for when AI response is not valid JSON
    def _parse_authenticity_fallback(self, response: str) -> Dict[str, Any]:
        """Fallback parser for authenticity assessment"""
        return {
            "authenticity_assessment": "unknown",
            "confidence": 20,
            "specific_indicators": {"authentic_elements": [], "template_elements": ["Parsing failed"], "mixed_elements": []},
            "business_alignment": 20,
            "implementation_readiness": 20,
            "detailed_reasoning": f"Parsing fallback: {response[:200]}...",
            "improvement_areas": ["Fix AI response parsing"]
        }
    
    def _parse_specificity_fallback(self, response: str) -> Dict[str, Any]:
        """Fallback parser for specificity analysis"""
        return {
            "specificity_score": 20,
            "specificity_level": "unknown",
            "unique_elements": [],
            "generic_elements": ["Parsing failed"],
            "customization_indicators": [],
            "portability_assessment": "unknown",
            "business_context_integration": 20,
            "specificity_reasoning": f"Parsing fallback: {response[:200]}..."
        }
    
    def _parse_usability_fallback(self, response: str) -> Dict[str, Any]:
        """Fallback parser for usability assessment"""
        return {
            "usability_score": 20,
            "immediate_usability": False,
            "required_modifications": ["Parsing failed"],
            "missing_critical_elements": ["Unknown"],
            "effort_to_business_ready": "unknown",
            "usability_blockers": ["Parsing error"],
            "ready_to_use_elements": [],
            "usability_assessment": f"Parsing fallback: {response[:200]}...",
            "improvement_priority": []
        }

# Global instance
ai_content_reality_validator = AIContentRealityValidator()

# Export for easy import
__all__ = ["AIContentRealityValidator", "ai_content_reality_validator", "ContentValidationResult", "ContentRealityLevel"]