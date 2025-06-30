"""
🤖 AI Intelligent Asset Generator
Pure AI-driven generation of real, business-specific assets

Pillar 4: Authentic Content - Generates real, business-ready content not templates
Pillar 7: Domain Agnostic - Works for any business domain without hardcoded types
Pillar 8: No Hardcode - Zero predefined templates or asset formats
Pillar 9: Adaptive AI - Learns optimal generation patterns from context
Pillar 11: Self-Enhancement - Improves generation quality through feedback
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class GenerationStrategy(Enum):
    """AI generation strategies"""
    COMPLETE_FROM_PARTIAL = "complete_from_partial"  # Complete partial real content
    GENERATE_FROM_CONTEXT = "generate_from_context"  # Generate from business context
    ENHANCE_EXISTING = "enhance_existing"  # Enhance existing content quality
    CREATE_NEW_ASSET = "create_new_asset"  # Create entirely new asset

@dataclass
class AssetGenerationResult:
    """Result of AI asset generation"""
    generated_assets: Dict[str, Any]
    generation_strategy: GenerationStrategy
    business_specificity_score: float  # 0-100, how specific to the business
    usability_score: float  # 0-100, how ready to use immediately
    generation_confidence: float  # 0-100, AI confidence in the generation
    generation_reasoning: str  # AI explanation of generation approach
    self_validation_result: Dict[str, Any]  # AI self-validation of generated content
    improvement_applied: List[str]  # Improvements made during generation
    metadata: Dict[str, Any]  # Generation metadata

class AIIntelligentAssetGenerator:
    """
    🤖 Pure AI-Driven Intelligent Asset Generation
    Zero hardcoded templates or asset types
    """
    
    def __init__(self):
        self.generation_history = []  # For self-learning
        self.quality_standards = {
            "min_business_specificity": 80,
            "min_usability": 85,
            "min_generation_confidence": 75
        }
        
    async def generate_intelligent_assets(
        self,
        partial_content: Dict[str, Any],
        goal_context: str,
        business_context: Dict[str, Any] = None,
        missing_elements: List[str] = None,
        quality_requirements: Dict[str, Any] = None
    ) -> AssetGenerationResult:
        """
        🤖 AI-DRIVEN: Generate business-specific assets intelligently
        
        Args:
            partial_content: Existing partial content to build upon
            goal_context: Goal this asset should satisfy
            business_context: Business context for specificity
            missing_elements: Specific elements that need generation
            quality_requirements: Quality standards for generation
            
        Returns:
            AssetGenerationResult with generated business-ready assets
        """
        try:
            logger.info("🤖 Starting intelligent AI asset generation...")
            
            # Step 1: AI Strategy Selection
            generation_strategy = await self._ai_select_generation_strategy(
                partial_content,
                goal_context,
                missing_elements
            )
            
            # Step 2: AI Business Context Analysis
            business_intelligence = await self._ai_analyze_business_intelligence(
                business_context,
                goal_context
            )
            
            # Step 3: AI Asset Generation
            generated_assets = await self._ai_generate_assets(
                partial_content,
                goal_context,
                business_intelligence,
                generation_strategy,
                missing_elements
            )
            
            # Step 4: AI Self-Validation
            self_validation = await self._ai_self_validate_generation(
                generated_assets,
                business_context,
                goal_context,
                quality_requirements
            )
            
            # Step 5: AI Quality Enhancement (if needed)
            if self_validation.get('needs_improvement', False):
                enhanced_assets = await self._ai_enhance_generated_assets(
                    generated_assets,
                    self_validation,
                    business_intelligence
                )
                # Re-validate enhanced version
                enhanced_validation = await self._ai_self_validate_generation(
                    enhanced_assets,
                    business_context,
                    goal_context,
                    quality_requirements
                )
                generated_assets = enhanced_assets
                self_validation = enhanced_validation
            
            # Step 6: AI Reasoning Generation
            generation_reasoning = await self._ai_generate_creation_reasoning(
                generation_strategy,
                business_intelligence,
                self_validation
            )
            
            # Compile result
            result = AssetGenerationResult(
                generated_assets=generated_assets,
                generation_strategy=generation_strategy,
                business_specificity_score=self_validation.get('business_specificity', 0),
                usability_score=self_validation.get('usability_score', 0),
                generation_confidence=self_validation.get('generation_confidence', 0),
                generation_reasoning=generation_reasoning,
                self_validation_result=self_validation,
                improvement_applied=self_validation.get('improvements_applied', []),
                metadata={
                    "generation_timestamp": datetime.now().isoformat(),
                    "strategy_used": generation_strategy.value,
                    "business_context_available": business_context is not None,
                    "partial_content_size": len(str(partial_content))
                }
            )
            
            # Self-learning: Store generation for improvement
            await self._store_generation_learning(partial_content, result)
            
            logger.info(f"✅ AI generation complete: Strategy={generation_strategy.value}, Specificity={result.business_specificity_score:.1f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in AI asset generation: {e}")
            return self._create_error_result(str(e))
    
    async def _ai_select_generation_strategy(
        self,
        partial_content: Dict[str, Any],
        goal_context: str,
        missing_elements: List[str]
    ) -> GenerationStrategy:
        """
        🤖 AI selection of optimal generation strategy
        """
        try:
            from ai_quality_assurance.smart_evaluator import smart_evaluator
            
            strategy_prompt = f"""
Seleziona la strategia ottimale per generare asset di qualità business.

CONTENUTO PARZIALE ESISTENTE:
{json.dumps(partial_content, indent=2)}

CONTESTO GOAL:
{goal_context}

ELEMENTI MANCANTI:
{missing_elements or ["No specific missing elements identified"]}

STRATEGIE DISPONIBILI:
1. COMPLETE_FROM_PARTIAL: Completa contenuto parziale esistente di qualità
2. GENERATE_FROM_CONTEXT: Genera nuovo contenuto dal contesto business
3. ENHANCE_EXISTING: Migliora qualità del contenuto esistente
4. CREATE_NEW_ASSET: Crea asset completamente nuovo

SELEZIONE CRITERI:
- Qualità del contenuto esistente
- Quantità di contenuto utilizzabile
- Specificità del contesto disponibile
- Completezza rispetto al goal

Seleziona la strategia che produrrà il miglior risultato business-ready.

Rispondi solo con uno di questi valori:
- complete_from_partial
- generate_from_context  
- enhance_existing
- create_new_asset
"""
            
            ai_response = await smart_evaluator.evaluate_with_ai(
                strategy_prompt,
                context="strategy_selection",
                max_tokens=500
            )
            
            # Parse strategy response
            strategy_text = str(ai_response).strip().lower()
            
            if "complete_from_partial" in strategy_text:
                return GenerationStrategy.COMPLETE_FROM_PARTIAL
            elif "generate_from_context" in strategy_text:
                return GenerationStrategy.GENERATE_FROM_CONTEXT
            elif "enhance_existing" in strategy_text:
                return GenerationStrategy.ENHANCE_EXISTING
            elif "create_new_asset" in strategy_text:
                return GenerationStrategy.CREATE_NEW_ASSET
            else:
                # Default fallback
                return GenerationStrategy.GENERATE_FROM_CONTEXT
                
        except Exception as e:
            logger.error(f"Error in AI strategy selection: {e}")
            return GenerationStrategy.GENERATE_FROM_CONTEXT
    
    async def _ai_analyze_business_intelligence(
        self,
        business_context: Dict[str, Any],
        goal_context: str
    ) -> Dict[str, Any]:
        """
        🤖 AI analysis of business context for intelligent generation
        """
        try:
            from ai_quality_assurance.smart_evaluator import smart_evaluator
            
            business_info = self._format_business_context(business_context)
            
            intelligence_prompt = f"""
Analizza il contesto business per generare asset altamente specifici e utilizzabili.

CONTESTO BUSINESS:
{business_info}

CONTESTO GOAL:
{goal_context}

INTELLIGENCE RICHIESTA:
1. Caratteristiche uniche di questo business
2. Target audience specifico
3. Value proposition distintiva  
4. Tone of voice appropriato
5. Specifiche tecniche/operative rilevanti
6. Dettagli che renderebbero l'asset unico per questo business

Estrai intelligence ACTIONABLE per generazione asset specifici.

Rispondi in JSON:
{{
    "business_uniqueness": ["caratteristiche uniche di questo business"],
    "target_audience_specifics": ["dettagli specifici del target"],
    "value_proposition": "value proposition distintiva",
    "tone_and_style": "tone of voice appropriato",
    "technical_specifics": ["specifiche tecniche/operative rilevanti"],
    "competitive_differentiators": ["elementi di differenziazione"],
    "business_goals_context": ["contesto obiettivi business"],
    "industry_considerations": ["considerazioni specifiche del settore"],
    "customization_opportunities": ["opportunità di personalizzazione specifica"],
    "intelligence_confidence": 0-100
}}
"""
            
            ai_response = await smart_evaluator.evaluate_with_ai(
                intelligence_prompt,
                context="business_intelligence",
                max_tokens=1500
            )
            
            if isinstance(ai_response, str):
                try:
                    intelligence = json.loads(ai_response)
                except json.JSONDecodeError:
                    intelligence = self._parse_intelligence_fallback(ai_response)
            else:
                intelligence = ai_response
                
            return intelligence
            
        except Exception as e:
            logger.error(f"Error in AI business intelligence: {e}")
            return {
                "business_uniqueness": [],
                "target_audience_specifics": [],
                "value_proposition": "Generic business value",
                "tone_and_style": "Professional",
                "technical_specifics": [],
                "competitive_differentiators": [],
                "business_goals_context": [],
                "industry_considerations": [],
                "customization_opportunities": [],
                "intelligence_confidence": 0
            }
    
    async def _ai_generate_assets(
        self,
        partial_content: Dict[str, Any],
        goal_context: str,
        business_intelligence: Dict[str, Any],
        generation_strategy: GenerationStrategy,
        missing_elements: List[str]
    ) -> Dict[str, Any]:
        """
        🤖 AI generation of business-specific assets
        """
        try:
            from ai_quality_assurance.smart_evaluator import smart_evaluator
            
            generation_prompt = f"""
Genera asset BUSINESS-SPECIFIC di alta qualità usando questa intelligence.

STRATEGIA: {generation_strategy.value}

CONTENUTO PARZIALE:
{json.dumps(partial_content, indent=2)}

GOAL DA SODDISFARE:
{goal_context}

BUSINESS INTELLIGENCE:
{json.dumps(business_intelligence, indent=2)}

ELEMENTI MANCANTI:
{missing_elements or ["Complete asset generation needed"]}

ISTRUZIONI GENERAZIONE:
1. Genera contenuto SPECIFICO per questo business (non template)
2. Usa la business intelligence per personalizzazione profonda
3. Includi dettagli concreti e actionable
4. Rendi l'asset immediatamente utilizzabile
5. Integra value proposition e tone specifici
6. NO contenuto generico o placeholder

QUALITÀ RICHIESTA:
- Business-specific (non applicabile ad altri business)
- Immediatamente utilizzabile senza modifiche
- Dettagli concreti e implementabili
- Aligned con goal e contesto business

Genera asset completi e dettagliati.

Rispondi in JSON con la struttura più appropriata per l'asset generato.
Organizza il contenuto in modo logico e utilizzabile.
"""
            
            ai_response = await smart_evaluator.evaluate_with_ai(
                generation_prompt,
                context="asset_generation",
                max_tokens=3000
            )
            
            if isinstance(ai_response, str):
                try:
                    generated_assets = json.loads(ai_response)
                except json.JSONDecodeError:
                    # Try to extract structured content from text response
                    generated_assets = self._parse_assets_from_text(ai_response)
            else:
                generated_assets = ai_response
                
            return generated_assets
            
        except Exception as e:
            logger.error(f"Error in AI asset generation: {e}")
            return {
                "error": f"Asset generation failed: {e}",
                "fallback_content": "Asset generation encountered an error"
            }
    
    async def _ai_self_validate_generation(
        self,
        generated_assets: Dict[str, Any],
        business_context: Dict[str, Any],
        goal_context: str,
        quality_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        🤖 AI self-validation of generated assets
        """
        try:
            from ai_quality_assurance.smart_evaluator import smart_evaluator
            
            business_info = self._format_business_context(business_context)
            
            validation_prompt = f"""
Auto-valida la qualità degli asset generati con standard elevati.

ASSET GENERATI:
{json.dumps(generated_assets, indent=2)}

CONTESTO BUSINESS:
{business_info}

GOAL ORIGINALE:
{goal_context}

VALIDAZIONE RICHIESTA:
1. Gli asset sono SPECIFICI per questo business o generici?
2. Sono immediatamente utilizzabili senza modifiche?
3. Contengono dettagli concreti e actionable?
4. Soddisfano completamente il goal?
5. Sono di qualità business-professional?

STANDARD QUALITÀ:
- Business specificity: deve essere >80/100
- Usability: deve essere >85/100  
- Authenticity: zero template language
- Completeness: deve soddisfare completamente il goal

Sii critico e onesto nella valutazione.

Rispondi in JSON:
{{
    "business_specificity": 0-100,
    "usability_score": 0-100,
    "authenticity_score": 0-100,
    "goal_satisfaction": 0-100,
    "generation_confidence": 0-100,
    "needs_improvement": true/false,
    "quality_assessment": {{
        "strengths": ["punti di forza degli asset"],
        "weaknesses": ["aree di miglioramento"],
        "template_indicators": ["elementi che sembrano template"],
        "specific_indicators": ["elementi che sono business-specific"]
    }},
    "improvement_suggestions": ["suggerimenti specifici per migliorare"],
    "overall_quality": "excellent/good/fair/poor",
    "validation_reasoning": "spiegazione dettagliata della valutazione"
}}
"""
            
            ai_response = await smart_evaluator.evaluate_with_ai(
                validation_prompt,
                context="self_validation",
                max_tokens=1500
            )
            
            if isinstance(ai_response, str):
                try:
                    validation = json.loads(ai_response)
                except json.JSONDecodeError:
                    validation = self._parse_validation_fallback(ai_response)
            else:
                validation = ai_response
                
            return validation
            
        except Exception as e:
            logger.error(f"Error in AI self-validation: {e}")
            return {
                "business_specificity": 0,
                "usability_score": 0,
                "authenticity_score": 0,
                "goal_satisfaction": 0,
                "generation_confidence": 0,
                "needs_improvement": True,
                "quality_assessment": {"strengths": [], "weaknesses": ["Validation failed"], "template_indicators": [], "specific_indicators": []},
                "improvement_suggestions": ["Fix validation error"],
                "overall_quality": "poor",
                "validation_reasoning": f"Validation failed: {e}"
            }
    
    async def _ai_enhance_generated_assets(
        self,
        generated_assets: Dict[str, Any],
        validation_result: Dict[str, Any],
        business_intelligence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        🤖 AI enhancement of generated assets based on self-validation
        """
        try:
            from ai_quality_assurance.smart_evaluator import smart_evaluator
            
            enhancement_prompt = f"""
Migliora gli asset generati basandoti sulla self-validation.

ASSET ATTUALI:
{json.dumps(generated_assets, indent=2)}

RISULTATO VALIDAZIONE:
{json.dumps(validation_result, indent=2)}

BUSINESS INTELLIGENCE:
{json.dumps(business_intelligence, indent=2)}

MIGLIORAMENTI RICHIESTI:
1. Applica i suggerimenti dalla validazione
2. Aumenta business specificity se <80
3. Migliora usability se <85
4. Elimina qualsiasi linguaggio template
5. Aggiungi dettagli business-specific mancanti

FOCUS ENHANCEMENT:
- Sostituisci elementi generici con specifici
- Aggiungi dettagli implementabili
- Personalizza per questo business
- Rendi immediatamente utilizzabile

Genera la versione migliorata completa degli asset.

Rispondi in JSON con gli asset migliorati nella stessa struttura.
"""
            
            ai_response = await smart_evaluator.evaluate_with_ai(
                enhancement_prompt,
                context="asset_enhancement",
                max_tokens=3000
            )
            
            if isinstance(ai_response, str):
                try:
                    enhanced_assets = json.loads(ai_response)
                except json.JSONDecodeError:
                    enhanced_assets = self._parse_assets_from_text(ai_response)
            else:
                enhanced_assets = ai_response
                
            return enhanced_assets
            
        except Exception as e:
            logger.error(f"Error in AI asset enhancement: {e}")
            return generated_assets  # Return original if enhancement fails
    
    async def _ai_generate_creation_reasoning(
        self,
        generation_strategy: GenerationStrategy,
        business_intelligence: Dict[str, Any],
        validation_result: Dict[str, Any]
    ) -> str:
        """
        🤖 AI generation of comprehensive creation reasoning
        """
        try:
            from ai_quality_assurance.smart_evaluator import smart_evaluator
            
            reasoning_prompt = f"""
Spiega il processo di generazione asset in modo comprensibile.

STRATEGIA USATA: {generation_strategy.value}

BUSINESS INTELLIGENCE:
{json.dumps(business_intelligence, indent=2)}

RISULTATO VALIDAZIONE:
{json.dumps(validation_result, indent=2)}

GENERA SPIEGAZIONE:
1. Perché è stata scelta questa strategia di generazione
2. Come è stata usata la business intelligence
3. Che livello di qualità è stato raggiunto
4. Perché questi asset sono business-specific
5. Come l'utente può utilizzarli immediatamente

Scrivi per un utente business, non tecnico. Sii conciso ma informativo.

Rispondi solo con il testo della spiegazione.
"""
            
            ai_response = await smart_evaluator.evaluate_with_ai(
                reasoning_prompt,
                context="creation_reasoning",
                max_tokens=800
            )
            
            if isinstance(ai_response, str):
                return ai_response.strip()
            else:
                return str(ai_response)
                
        except Exception as e:
            logger.error(f"Error in AI reasoning generation: {e}")
            return f"Creation reasoning generation failed: {e}"
    
    def _format_business_context(self, business_context: Dict[str, Any]) -> str:
        """Format business context for AI analysis"""
        if not business_context:
            return "No specific business context available"
        
        context_parts = []
        
        relevant_fields = [
            'name', 'description', 'industry', 'target_audience', 
            'business_model', 'value_proposition', 'competitive_advantage',
            'company_size', 'geographic_focus', 'key_challenges'
        ]
        
        for field in relevant_fields:
            if field in business_context and business_context[field]:
                context_parts.append(f"{field.replace('_', ' ').title()}: {business_context[field]}")
        
        return "\n".join(context_parts) if context_parts else "General business context"
    
    def _parse_assets_from_text(self, text_response: str) -> Dict[str, Any]:
        """Parse assets from text response when JSON parsing fails"""
        try:
            # Try to find JSON-like content in the text
            import re
            
            # Look for JSON blocks
            json_match = re.search(r'\{.*\}', text_response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            
            # Fallback: structure the text response
            return {
                "generated_content": text_response,
                "content_type": "structured_text",
                "parsing_note": "AI response parsed from text format"
            }
            
        except Exception as e:
            return {
                "error": f"Text parsing failed: {e}",
                "raw_response": text_response[:500] + "..." if len(text_response) > 500 else text_response
            }
    
    async def _store_generation_learning(
        self,
        partial_content: Dict[str, Any],
        generation_result: AssetGenerationResult
    ):
        """Store generation results for self-learning improvement"""
        try:
            learning_entry = {
                "timestamp": datetime.now().isoformat(),
                "strategy_used": generation_result.generation_strategy.value,
                "business_specificity": generation_result.business_specificity_score,
                "usability_score": generation_result.usability_score,
                "generation_confidence": generation_result.generation_confidence,
                "improvements_count": len(generation_result.improvement_applied),
                "input_content_size": len(str(partial_content)),
                "output_content_size": len(str(generation_result.generated_assets))
            }
            
            self.generation_history.append(learning_entry)
            
            # Keep only recent entries for memory efficiency
            if len(self.generation_history) > 100:
                self.generation_history = self.generation_history[-100:]
                
        except Exception as e:
            logger.debug(f"Generation learning storage failed: {e}")
    
    def _create_error_result(self, error_message: str) -> AssetGenerationResult:
        """Create error result when generation fails"""
        return AssetGenerationResult(
            generated_assets={"error": error_message},
            generation_strategy=GenerationStrategy.CREATE_NEW_ASSET,
            business_specificity_score=0,
            usability_score=0,
            generation_confidence=0,
            generation_reasoning=f"Generation failed: {error_message}",
            self_validation_result={"error": error_message},
            improvement_applied=[],
            metadata={"error": error_message}
        )
    
    # Fallback parsers for when AI response is not valid JSON
    def _parse_intelligence_fallback(self, response: str) -> Dict[str, Any]:
        """Fallback parser for business intelligence"""
        return {
            "business_uniqueness": ["Parsing failed"],
            "target_audience_specifics": ["Unknown"],
            "value_proposition": "Generic business value",
            "tone_and_style": "Professional",
            "technical_specifics": ["Unknown"],
            "competitive_differentiators": ["Unknown"],
            "business_goals_context": ["Unknown"],
            "industry_considerations": ["Unknown"],
            "customization_opportunities": ["Unknown"],
            "intelligence_confidence": 10
        }
    
    def _parse_validation_fallback(self, response: str) -> Dict[str, Any]:
        """Fallback parser for validation result"""
        return {
            "business_specificity": 20,
            "usability_score": 20,
            "authenticity_score": 20,
            "goal_satisfaction": 20,
            "generation_confidence": 20,
            "needs_improvement": True,
            "quality_assessment": {"strengths": [], "weaknesses": ["Validation parsing failed"], "template_indicators": [], "specific_indicators": []},
            "improvement_suggestions": ["Fix validation parsing"],
            "overall_quality": "poor",
            "validation_reasoning": f"Validation parsing fallback: {response[:200]}..."
        }

# Global instance
ai_intelligent_asset_generator = AIIntelligentAssetGenerator()

# Export for easy import
__all__ = ["AIIntelligentAssetGenerator", "ai_intelligent_asset_generator", "AssetGenerationResult", "GenerationStrategy"]