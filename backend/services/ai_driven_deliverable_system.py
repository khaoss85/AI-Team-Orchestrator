"""
🤖 AI-Driven Deliverable System
Complete replacement for hardcoded template-based deliverable generation

Pillar 1: Goal-Driven - Proper goal-deliverable mapping
Pillar 4: Authentic Content - Only real, business-specific content
Pillar 7: Domain Agnostic - Works across any business domain
Pillar 8: No Hardcode - Zero templates, patterns, or assumptions
Pillar 9: Adaptive AI - Learns and adapts to content patterns
Pillar 11: Self-Enhancement - Improves through feedback loops
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from services.universal_ai_content_extractor import universal_ai_content_extractor, ContentAnalysisResult
from services.ai_semantic_mapper import ai_semantic_mapper, SemanticMappingResult
from services.ai_content_reality_validator import ai_content_reality_validator, ContentValidationResult, ContentRealityLevel
from services.ai_intelligent_asset_generator import ai_intelligent_asset_generator, AssetGenerationResult

logger = logging.getLogger(__name__)

@dataclass
class DeliverableCreationResult:
    """Complete result of AI-driven deliverable creation"""
    deliverable_content: Dict[str, Any]
    mapped_goal_id: Optional[str]
    content_quality_level: ContentRealityLevel
    business_specificity_score: float
    usability_score: float
    creation_confidence: float
    creation_reasoning: str
    quality_validations: Dict[str, Any]
    improvement_suggestions: List[str]
    processing_metadata: Dict[str, Any]

class AIDrivenDeliverableSystem:
    """
    🤖 Complete AI-Driven Deliverable Creation System
    Replaces all hardcoded template fallbacks with intelligent AI generation
    """
    
    def __init__(self):
        self.creation_history = []
        self.quality_thresholds = {
            "min_business_specificity": 75,
            "min_usability": 80,
            "min_confidence": 70,
            "max_template_tolerance": 10  # Max % of template content allowed
        }
        
    async def create_deliverable_from_tasks(
        self,
        workspace_id: str,
        completed_tasks: List[Dict[str, Any]],
        workspace_goals: List[Dict[str, Any]],
        workspace_context: Dict[str, Any] = None
    ) -> DeliverableCreationResult:
        """
        🤖 AI-DRIVEN: Create deliverable from completed tasks
        Complete pipeline replacing all hardcoded template generation
        
        Args:
            workspace_id: Workspace identifier
            completed_tasks: List of completed tasks with results
            workspace_goals: Available goals for mapping
            workspace_context: Business context for personalization
            
        Returns:
            DeliverableCreationResult with pure AI-generated content
        """
        try:
            logger.info(f"🤖 Starting AI-driven deliverable creation for workspace {workspace_id}")
            
            # Phase 1: AI Content Extraction (no assumptions about content types)
            logger.info("Phase 1: AI Content Discovery...")
            content_analysis = await universal_ai_content_extractor.extract_real_content(
                completed_tasks,
                self._extract_goal_context(workspace_goals),
                workspace_context
            )
            
            # Phase 2: AI Semantic Goal Mapping (no keyword matching)
            logger.info("Phase 2: AI Semantic Goal Mapping...")
            mapping_result = await ai_semantic_mapper.map_content_to_goals_semantically(
                content_analysis.discovered_content,
                workspace_goals,
                workspace_context
            )
            
            # Phase 3: AI Content Reality Validation (no hardcoded patterns)
            logger.info("Phase 3: AI Content Reality Validation...")
            validation_result = await ai_content_reality_validator.validate_content_authenticity(
                content_analysis.discovered_content,
                workspace_context,
                mapping_result.semantic_reasoning
            )
            
            # Phase 4: AI Asset Generation (if content is insufficient)
            generated_content = content_analysis.discovered_content
            generation_applied = False
            
            if (validation_result.reality_level in [ContentRealityLevel.TEMPLATE_GENERIC, ContentRealityLevel.PLACEHOLDER_FAKE] or
                validation_result.usability_score < self.quality_thresholds["min_usability"]):
                
                logger.info("Phase 4: AI Asset Generation (content insufficient)...")
                generation_result = await ai_intelligent_asset_generator.generate_intelligent_assets(
                    content_analysis.discovered_content,
                    self._extract_goal_context(workspace_goals, mapping_result.mapped_goal_id),
                    workspace_context,
                    content_analysis.missing_elements
                )
                
                # Use generated content if it's better quality
                if generation_result.business_specificity_score > validation_result.business_specificity_score:
                    generated_content = generation_result.generated_assets
                    generation_applied = True
                    logger.info("✅ AI-generated content is higher quality, using generated assets")
            
            # Phase 5: Final Quality Assurance
            logger.info("Phase 5: Final Quality Assurance...")
            final_validation = await ai_content_reality_validator.validate_content_authenticity(
                generated_content,
                workspace_context,
                mapping_result.semantic_reasoning
            )
            
            # Phase 6: Deliverable Structure Creation
            logger.info("Phase 6: AI Deliverable Structure Creation...")
            deliverable_content = await self._ai_create_deliverable_structure(
                generated_content,
                mapping_result,
                final_validation,
                workspace_context
            )
            
            # Phase 7: Final Reasoning Compilation
            creation_reasoning = await self._ai_compile_creation_reasoning(
                content_analysis,
                mapping_result,
                final_validation,
                generation_applied
            )
            
            # Compile final result
            result = DeliverableCreationResult(
                deliverable_content=deliverable_content,
                mapped_goal_id=mapping_result.mapped_goal_id,
                content_quality_level=final_validation.reality_level,
                business_specificity_score=final_validation.business_specificity_score,
                usability_score=final_validation.usability_score,
                creation_confidence=min(
                    content_analysis.confidence,
                    mapping_result.mapping_confidence,
                    final_validation.authenticity_confidence
                ),
                creation_reasoning=creation_reasoning,
                quality_validations={
                    "content_analysis": content_analysis,
                    "mapping_result": mapping_result,
                    "validation_result": final_validation
                },
                improvement_suggestions=final_validation.improvement_suggestions,
                processing_metadata={
                    "creation_timestamp": datetime.now().isoformat(),
                    "workspace_id": workspace_id,
                    "tasks_processed": len(completed_tasks),
                    "goals_available": len(workspace_goals),
                    "generation_applied": generation_applied,
                    "processing_phases": 7
                }
            )
            
            # Store for learning
            await self._store_creation_learning(workspace_id, completed_tasks, result)
            
            logger.info(f"✅ AI deliverable creation complete: Quality={final_validation.reality_level.value}, Confidence={result.creation_confidence:.1f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in AI deliverable creation: {e}")
            return self._create_error_result(workspace_id, str(e))
    
    async def _ai_create_deliverable_structure(
        self,
        content: Dict[str, Any],
        mapping_result: SemanticMappingResult,
        validation_result: ContentValidationResult,
        workspace_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        🤖 AI creation of deliverable structure (no hardcoded templates)
        """
        try:
            from ai_quality_assurance.smart_evaluator import smart_evaluator
            
            business_info = self._format_business_context(workspace_context)
            
            structure_prompt = f"""
Crea una struttura deliverable professionale per questo contenuto business.

CONTENUTO VALIDATO:
{json.dumps(content, indent=2)}

MAPPING RESULT:
Goal ID: {mapping_result.mapped_goal_id}
Confidence: {mapping_result.mapping_confidence}
Reasoning: {mapping_result.semantic_reasoning}

VALIDATION RESULT:
Quality Level: {validation_result.reality_level.value}
Business Specificity: {validation_result.business_specificity_score}
Usability: {validation_result.usability_score}

CONTESTO BUSINESS:
{business_info}

STRUTTURA RICHIESTA:
Organizza il contenuto in una struttura deliverable professionale che:
1. Presenta il contenuto in modo business-ready
2. Include executive summary del valore
3. Organizza asset in sezioni logiche
4. Fornisce implementation guidance specifica
5. Include business impact assessment

NON usare template predefiniti. Crea struttura ottimale per questo specifico contenuto.

Rispondi in JSON con struttura deliverable completa e professionale.
"""
            
            ai_response = await smart_evaluator.evaluate_with_ai(
                structure_prompt,
                context="deliverable_structure",
                max_tokens=2000
            )
            
            if isinstance(ai_response, str):
                try:
                    deliverable_structure = json.loads(ai_response)
                except json.JSONDecodeError:
                    deliverable_structure = self._parse_structure_fallback(ai_response, content)
            else:
                deliverable_structure = ai_response
                
            return deliverable_structure
            
        except Exception as e:
            logger.error(f"Error in AI deliverable structure creation: {e}")
            return {
                "error": f"Structure creation failed: {e}",
                "content": content,
                "fallback_structure": "Basic content presentation"
            }
    
    async def _ai_compile_creation_reasoning(
        self,
        content_analysis: ContentAnalysisResult,
        mapping_result: SemanticMappingResult,
        validation_result: ContentValidationResult,
        generation_applied: bool
    ) -> str:
        """
        🤖 AI compilation of comprehensive creation reasoning
        """
        try:
            from ai_quality_assurance.smart_evaluator import smart_evaluator
            
            reasoning_prompt = f"""
Compila una spiegazione chiara del processo di creazione deliverable.

ANALISI CONTENUTO:
- Reality Score: {content_analysis.reality_score}
- Usability Score: {content_analysis.usability_score}
- Confidence: {content_analysis.confidence}
- Reasoning: {content_analysis.reasoning}

MAPPING RESULT:
- Goal Mapped: {mapping_result.mapped_goal_id}
- Mapping Confidence: {mapping_result.mapping_confidence}
- Reasoning: {mapping_result.semantic_reasoning}

VALIDATION RESULT:
- Quality Level: {validation_result.reality_level.value}
- Business Specificity: {validation_result.business_specificity_score}
- Usability: {validation_result.usability_score}

GENERATION APPLIED: {generation_applied}

COMPILA SPIEGAZIONE:
Spiega in modo chiaro e professionale:
1. Cosa è stato estratto dai task completati
2. Come è stato mappato al goal appropriato
3. Qual è la qualità finale del deliverable
4. Perché l'utente può considerarlo business-ready
5. Se è stata applicata generazione AI e perché

Scrivi per un utente business, sii conciso ma informativo.

Rispondi solo con il testo della spiegazione.
"""
            
            ai_response = await smart_evaluator.evaluate_with_ai(
                reasoning_prompt,
                context="creation_reasoning",
                max_tokens=1000
            )
            
            if isinstance(ai_response, str):
                return ai_response.strip()
            else:
                return str(ai_response)
                
        except Exception as e:
            logger.error(f"Error in AI reasoning compilation: {e}")
            return f"Creation reasoning compilation failed: {e}"
    
    def _extract_goal_context(self, workspace_goals: List[Dict[str, Any]], specific_goal_id: str = None) -> str:
        """Extract goal context for AI analysis"""
        if specific_goal_id:
            # Find specific goal
            for goal in workspace_goals:
                if goal.get('id') == specific_goal_id:
                    return f"{goal.get('title', '')}: {goal.get('description', '')}"
        
        # Return general context
        if workspace_goals:
            goals_text = []
            for goal in workspace_goals:
                goals_text.append(f"- {goal.get('title', 'Unnamed Goal')}")
            return "Available goals: " + ", ".join(goals_text)
        
        return "No specific goal context available"
    
    def _format_business_context(self, workspace_context: Dict[str, Any]) -> str:
        """Format business context for AI analysis"""
        if not workspace_context:
            return "No specific business context available"
        
        context_parts = []
        
        relevant_fields = [
            'name', 'description', 'industry', 'target_audience', 
            'business_model', 'value_proposition'
        ]
        
        for field in relevant_fields:
            if field in workspace_context and workspace_context[field]:
                context_parts.append(f"{field.replace('_', ' ').title()}: {workspace_context[field]}")
        
        return "\n".join(context_parts) if context_parts else "General business context"
    
    async def _store_creation_learning(
        self,
        workspace_id: str,
        completed_tasks: List[Dict[str, Any]],
        result: DeliverableCreationResult
    ):
        """Store creation results for learning and improvement"""
        try:
            learning_entry = {
                "timestamp": datetime.now().isoformat(),
                "workspace_id": workspace_id,
                "tasks_count": len(completed_tasks),
                "content_quality": result.content_quality_level.value,
                "business_specificity": result.business_specificity_score,
                "usability_score": result.usability_score,
                "creation_confidence": result.creation_confidence,
                "goal_mapped": result.mapped_goal_id is not None,
                "generation_applied": result.processing_metadata.get('generation_applied', False)
            }
            
            self.creation_history.append(learning_entry)
            
            # Keep only recent entries
            if len(self.creation_history) > 100:
                self.creation_history = self.creation_history[-100:]
                
        except Exception as e:
            logger.debug(f"Creation learning storage failed: {e}")
    
    def _create_error_result(self, workspace_id: str, error_message: str) -> DeliverableCreationResult:
        """Create error result when creation fails"""
        return DeliverableCreationResult(
            deliverable_content={"error": error_message},
            mapped_goal_id=None,
            content_quality_level=ContentRealityLevel.PLACEHOLDER_FAKE,
            business_specificity_score=0,
            usability_score=0,
            creation_confidence=0,
            creation_reasoning=f"Deliverable creation failed: {error_message}",
            quality_validations={},
            improvement_suggestions=[f"Fix creation error: {error_message}"],
            processing_metadata={
                "error": error_message,
                "workspace_id": workspace_id,
                "creation_timestamp": datetime.now().isoformat()
            }
        )
    
    def _parse_structure_fallback(self, response: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback parser for deliverable structure"""
        return {
            "executive_summary": "Deliverable structure parsing failed",
            "content": content,
            "implementation_guidance": "Please review content manually",
            "business_impact": "Impact assessment unavailable",
            "parsing_note": f"Structure parsing fallback: {response[:200]}..."
        }

# Global instance
ai_driven_deliverable_system = AIDrivenDeliverableSystem()

# Export for easy import
__all__ = ["AIDrivenDeliverableSystem", "ai_driven_deliverable_system", "DeliverableCreationResult"]