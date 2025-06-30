"""
🤖 AI Semantic Mapper
Pure AI-driven goal-deliverable mapping without hardcoded patterns

Pillar 7: Domain Agnostic - Semantic understanding across any business domain
Pillar 8: No Hardcode - Zero keyword matching or predefined mapping rules
Pillar 9: Adaptive AI - Learns mapping patterns from context and intent
Pillar 10: Real-time Reasoning - AI semantic analysis for goal satisfaction
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from uuid import UUID

logger = logging.getLogger(__name__)

@dataclass
class SemanticMappingResult:
    """Result of AI semantic mapping between content and goals"""
    mapped_goal_id: Optional[str]
    mapping_confidence: float  # 0-100
    goal_satisfaction_score: float  # 0-100, how well content satisfies the goal
    semantic_reasoning: str  # AI explanation of the mapping
    alternative_mappings: List[Dict[str, Any]]  # Other possible goal mappings
    requires_user_confirmation: bool  # If mapping is uncertain
    content_goal_alignment: Dict[str, Any]  # Detailed alignment analysis

class AISemanticMapper:
    """
    🤖 Pure AI-Driven Semantic Goal Mapping
    Zero hardcoded patterns, keyword matching, or predefined rules
    """
    
    def __init__(self):
        self.mapping_history = []  # For self-learning
        self.confidence_threshold = 75  # Minimum confidence for auto-mapping
        
    async def map_content_to_goals_semantically(
        self,
        extracted_content: Dict[str, Any],
        workspace_goals: List[Dict[str, Any]],
        workspace_context: Dict[str, Any] = None
    ) -> SemanticMappingResult:
        """
        🤖 AI-DRIVEN: Semantic mapping of content to goals
        
        Args:
            extracted_content: Content discovered by UniversalAIContentExtractor
            workspace_goals: Available goals in the workspace
            workspace_context: Business context for better mapping
            
        Returns:
            SemanticMappingResult with AI semantic analysis
        """
        try:
            logger.info("🤖 Starting AI semantic goal mapping...")
            
            if not workspace_goals:
                return self._create_no_goals_result(extracted_content)
            
            # Step 1: AI Semantic Analysis of Content Intent
            content_intent = await self._ai_analyze_content_intent(extracted_content)
            
            # Step 2: AI Goal Satisfaction Analysis
            goal_satisfaction_analysis = await self._ai_analyze_goal_satisfaction(
                extracted_content,
                workspace_goals,
                content_intent
            )
            
            # Step 3: AI Confidence Assessment & Best Match Selection
            mapping_decision = await self._ai_select_best_mapping(
                goal_satisfaction_analysis,
                content_intent,
                workspace_context
            )
            
            # Step 4: AI Reasoning Generation
            semantic_reasoning = await self._ai_generate_mapping_reasoning(
                extracted_content,
                mapping_decision,
                goal_satisfaction_analysis
            )
            
            # Compile result
            result = SemanticMappingResult(
                mapped_goal_id=mapping_decision.get('best_goal_id'),
                mapping_confidence=mapping_decision.get('confidence', 0),
                goal_satisfaction_score=mapping_decision.get('satisfaction_score', 0),
                semantic_reasoning=semantic_reasoning,
                alternative_mappings=mapping_decision.get('alternatives', []),
                requires_user_confirmation=mapping_decision.get('confidence', 0) < self.confidence_threshold,
                content_goal_alignment=mapping_decision.get('alignment_details', {})
            )
            
            # Self-learning: Store mapping for pattern improvement
            await self._store_mapping_learning(extracted_content, workspace_goals, result)
            
            logger.info(f"✅ AI mapping complete: Goal={result.mapped_goal_id}, Confidence={result.mapping_confidence:.1f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in AI semantic mapping: {e}")
            return self._create_error_result(str(e))
    
    async def _ai_analyze_content_intent(self, extracted_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        🤖 AI analysis of content intent and purpose
        """
        try:
            from ai_quality_assurance.smart_evaluator import smart_evaluator
            
            intent_prompt = f"""
Analizza questo contenuto per comprendere il suo INTENT e PURPOSE senza assumere categorizzazioni predefinite.

CONTENUTO DA ANALIZZARE:
{json.dumps(extracted_content, indent=2)}

ANALISI RICHIESTA:
1. Qual è l'intent primario di questo contenuto?
2. Che problema business risolve?
3. Che outcome produce per l'utente?
4. Che valore genera?

NON usare categorie predefinite. Descrivi l'intent in modo semantico e funzionale.

Rispondi in JSON:
{{
    "primary_intent": "intent principale del contenuto",
    "business_problem_solved": "problema business che risolve",
    "expected_outcome": "outcome atteso dall'utilizzo",
    "value_generated": "valore generato per l'utente",
    "functional_purpose": "scopo funzionale specifico",
    "semantic_keywords": ["parole chiave semantiche (non letterali)"],
    "intent_confidence": 0-100,
    "intent_clarity": "chiaro/vago/ambiguo"
}}
"""
            
            ai_response = await smart_evaluator.evaluate_with_ai(
                intent_prompt,
                context="content_intent_analysis",
                max_tokens=1000
            )
            
            if isinstance(ai_response, str):
                try:
                    intent_analysis = json.loads(ai_response)
                except json.JSONDecodeError:
                    intent_analysis = self._parse_intent_fallback(ai_response)
            else:
                intent_analysis = ai_response
                
            return intent_analysis
            
        except Exception as e:
            logger.error(f"Error in AI intent analysis: {e}")
            return {
                "primary_intent": "unknown",
                "business_problem_solved": "analysis failed",
                "expected_outcome": "unknown",
                "value_generated": "unknown",
                "functional_purpose": "unknown",
                "semantic_keywords": [],
                "intent_confidence": 0,
                "intent_clarity": "ambiguo"
            }
    
    async def _ai_analyze_goal_satisfaction(
        self,
        extracted_content: Dict[str, Any],
        workspace_goals: List[Dict[str, Any]],
        content_intent: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        🤖 AI analysis of how well content satisfies each goal
        """
        try:
            from ai_quality_assurance.smart_evaluator import smart_evaluator
            
            # Prepare goals for analysis
            goals_text = self._format_goals_for_analysis(workspace_goals)
            
            satisfaction_prompt = f"""
Analizza semanticamente quanto questo contenuto soddisfa ciascun obiettivo.

CONTENUTO E SUO INTENT:
{json.dumps(extracted_content, indent=2)}

INTENT ANALIZZATO:
{json.dumps(content_intent, indent=2)}

OBIETTIVI DISPONIBILI:
{goals_text}

VALUTAZIONE RICHIESTA:
Per ogni obiettivo, determina:
1. Quanto il contenuto soddisfa semanticamente l'obiettivo (non keyword matching)
2. Alignment tra intent del contenuto e purpose dell'obiettivo
3. Gap rimanenti se il contenuto fosse assegnato a questo obiettivo
4. Fit semantico complessivo

Usa comprensione semantica profonda, non pattern matching superficiale.

Rispondi in JSON:
{{
    "goal_satisfaction_analysis": [
        {{
            "goal_id": "id dell'obiettivo",
            "goal_title": "titolo dell'obiettivo",
            "satisfaction_score": 0-100,
            "semantic_alignment": 0-100,
            "intent_match": "perfetto/buono/parziale/scarso",
            "remaining_gaps": ["gap specifici se assegnato a questo goal"],
            "fit_reasoning": "perché questo contenuto fits/non fits questo obiettivo",
            "confidence": 0-100
        }}
    ],
    "overall_analysis_confidence": 0-100
}}
"""
            
            ai_response = await smart_evaluator.evaluate_with_ai(
                satisfaction_prompt,
                context="goal_satisfaction_analysis",
                max_tokens=2000
            )
            
            if isinstance(ai_response, str):
                try:
                    satisfaction_analysis = json.loads(ai_response)
                except json.JSONDecodeError:
                    satisfaction_analysis = self._parse_satisfaction_fallback(ai_response, workspace_goals)
            else:
                satisfaction_analysis = ai_response
                
            return satisfaction_analysis.get('goal_satisfaction_analysis', [])
            
        except Exception as e:
            logger.error(f"Error in AI goal satisfaction analysis: {e}")
            return []
    
    async def _ai_select_best_mapping(
        self,
        goal_satisfaction_analysis: List[Dict[str, Any]],
        content_intent: Dict[str, Any],
        workspace_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        🤖 AI selection of best goal mapping based on comprehensive analysis
        """
        try:
            from ai_quality_assurance.smart_evaluator import smart_evaluator
            
            # Prepare context
            business_context = self._extract_business_context_for_mapping(workspace_context)
            
            selection_prompt = f"""
Seleziona il mapping ottimale basandoti su analisi semantica profonda.

ANALISI SODDISFAZIONE GOAL:
{json.dumps(goal_satisfaction_analysis, indent=2)}

INTENT CONTENUTO:
{json.dumps(content_intent, indent=2)}

CONTESTO BUSINESS:
{business_context}

DECISIONE RICHIESTA:
1. Seleziona il goal che ha il miglior fit semantico complessivo
2. Considera non solo satisfaction score ma anche:
   - Semantic alignment
   - Intent match quality
   - Business context fit
   - Remaining gaps impact

3. Calcola confidence della decisione
4. Identifica alternative valide
5. Determina se serve conferma utente

Priorità: QUALITÀ del fit semantico > SCORE numerico

Rispondi in JSON:
{{
    "best_goal_id": "id del goal selezionato (null se nessun buon match)",
    "confidence": 0-100,
    "satisfaction_score": 0-100,
    "selection_reasoning": "perché questo è il miglior match",
    "alternatives": [
        {{
            "goal_id": "id alternativo",
            "score": 0-100,
            "why_alternative": "perché potrebbe essere valido"
        }}
    ],
    "alignment_details": {{
        "semantic_fit": 0-100,
        "intent_alignment": 0-100,
        "business_context_fit": 0-100,
        "completeness": 0-100
    }},
    "requires_confirmation": true/false,
    "decision_confidence": 0-100
}}
"""
            
            ai_response = await smart_evaluator.evaluate_with_ai(
                selection_prompt,
                context="mapping_selection",
                max_tokens=1500
            )
            
            if isinstance(ai_response, str):
                try:
                    selection_result = json.loads(ai_response)
                except json.JSONDecodeError:
                    selection_result = self._parse_selection_fallback(ai_response, goal_satisfaction_analysis)
            else:
                selection_result = ai_response
                
            return selection_result
            
        except Exception as e:
            logger.error(f"Error in AI mapping selection: {e}")
            return {
                "best_goal_id": None,
                "confidence": 0,
                "satisfaction_score": 0,
                "selection_reasoning": f"Selection failed: {e}",
                "alternatives": [],
                "alignment_details": {},
                "requires_confirmation": True,
                "decision_confidence": 0
            }
    
    async def _ai_generate_mapping_reasoning(
        self,
        extracted_content: Dict[str, Any],
        mapping_decision: Dict[str, Any],
        goal_satisfaction_analysis: List[Dict[str, Any]]
    ) -> str:
        """
        🤖 AI generation of comprehensive mapping reasoning
        """
        try:
            from ai_quality_assurance.smart_evaluator import smart_evaluator
            
            reasoning_prompt = f"""
Genera una spiegazione chiara e comprensibile del mapping decisionale.

CONTENUTO MAPPATO:
{json.dumps(extracted_content, indent=2)}

DECISIONE MAPPING:
{json.dumps(mapping_decision, indent=2)}

ANALISI COMPLETA GOAL:
{json.dumps(goal_satisfaction_analysis, indent=2)}

GENERA:
Una spiegazione in linguaggio naturale che spiega:
1. Perché questo contenuto è stato mappato a questo goal
2. Punti di forza del mapping
3. Eventuali limitazioni o gap
4. Cosa rende questo il miglior fit semantico

Scrivi per un utente business, non tecnico. Sii conciso ma completo.

Rispondi solo con il testo della spiegazione.
"""
            
            ai_response = await smart_evaluator.evaluate_with_ai(
                reasoning_prompt,
                context="mapping_reasoning",
                max_tokens=800
            )
            
            if isinstance(ai_response, str):
                return ai_response.strip()
            else:
                return str(ai_response)
                
        except Exception as e:
            logger.error(f"Error in AI reasoning generation: {e}")
            return f"Mapping reasoning generation failed: {e}"
    
    def _format_goals_for_analysis(self, workspace_goals: List[Dict[str, Any]]) -> str:
        """Format goals for AI analysis"""
        formatted_goals = []
        
        for goal in workspace_goals:
            goal_text = f"""
GOAL ID: {goal.get('id', 'unknown')}
TITLE: {goal.get('title', 'No title')}
DESCRIPTION: {goal.get('description', 'No description')}
STATUS: {goal.get('status', 'unknown')}
PROGRESS: {goal.get('progress_percentage', 0)}%
CONTEXT: {goal.get('context', 'No additional context')}
---"""
            formatted_goals.append(goal_text)
        
        return "\n".join(formatted_goals)
    
    def _extract_business_context_for_mapping(self, workspace_context: Dict[str, Any]) -> str:
        """Extract business context for mapping decisions"""
        if not workspace_context:
            return "No specific business context available"
        
        context_parts = []
        
        if 'name' in workspace_context:
            context_parts.append(f"Project: {workspace_context['name']}")
        
        if 'description' in workspace_context:
            context_parts.append(f"Context: {workspace_context['description']}")
        
        if 'business_type' in workspace_context:
            context_parts.append(f"Business Type: {workspace_context['business_type']}")
        
        if 'target_audience' in workspace_context:
            context_parts.append(f"Target: {workspace_context['target_audience']}")
        
        return "\n".join(context_parts) if context_parts else "General business context"
    
    async def _store_mapping_learning(
        self,
        extracted_content: Dict[str, Any],
        workspace_goals: List[Dict[str, Any]],
        mapping_result: SemanticMappingResult
    ):
        """Store mapping results for self-learning improvement"""
        try:
            learning_entry = {
                "timestamp": datetime.now().isoformat(),
                "content_types": list(extracted_content.keys()),
                "goals_count": len(workspace_goals),
                "mapping_confidence": mapping_result.mapping_confidence,
                "goal_satisfaction": mapping_result.goal_satisfaction_score,
                "required_confirmation": mapping_result.requires_user_confirmation,
                "mapped_goal_id": mapping_result.mapped_goal_id
            }
            
            self.mapping_history.append(learning_entry)
            
            # Keep only recent entries for memory efficiency
            if len(self.mapping_history) > 100:
                self.mapping_history = self.mapping_history[-100:]
                
        except Exception as e:
            logger.debug(f"Mapping learning storage failed: {e}")
    
    def _create_no_goals_result(self, extracted_content: Dict[str, Any]) -> SemanticMappingResult:
        """Create result when no goals are available"""
        return SemanticMappingResult(
            mapped_goal_id=None,
            mapping_confidence=0,
            goal_satisfaction_score=0,
            semantic_reasoning="No goals available in workspace for mapping",
            alternative_mappings=[],
            requires_user_confirmation=True,
            content_goal_alignment={}
        )
    
    def _create_error_result(self, error_message: str) -> SemanticMappingResult:
        """Create error result when mapping fails"""
        return SemanticMappingResult(
            mapped_goal_id=None,
            mapping_confidence=0,
            goal_satisfaction_score=0,
            semantic_reasoning=f"Mapping failed: {error_message}",
            alternative_mappings=[],
            requires_user_confirmation=True,
            content_goal_alignment={}
        )
    
    # Fallback parsers for when AI response is not valid JSON
    def _parse_intent_fallback(self, response: str) -> Dict[str, Any]:
        """Fallback parser for intent analysis"""
        return {
            "primary_intent": "analysis_failed",
            "business_problem_solved": "unknown",
            "expected_outcome": "unknown",
            "value_generated": "unknown",
            "functional_purpose": "unknown",
            "semantic_keywords": [],
            "intent_confidence": 10,
            "intent_clarity": "ambiguo"
        }
    
    def _parse_satisfaction_fallback(self, response: str, workspace_goals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback parser for satisfaction analysis"""
        fallback_analysis = []
        
        for goal in workspace_goals:
            fallback_analysis.append({
                "goal_id": goal.get('id', 'unknown'),
                "goal_title": goal.get('title', 'Unknown Goal'),
                "satisfaction_score": 30,
                "semantic_alignment": 20,
                "intent_match": "scarso",
                "remaining_gaps": ["Analysis failed"],
                "fit_reasoning": "Fallback analysis due to parsing error",
                "confidence": 10
            })
        
        return {
            "goal_satisfaction_analysis": fallback_analysis,
            "overall_analysis_confidence": 10
        }
    
    def _parse_selection_fallback(self, response: str, goal_satisfaction_analysis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback parser for selection decision"""
        best_goal = None
        if goal_satisfaction_analysis:
            # Pick the first goal as fallback
            best_goal = goal_satisfaction_analysis[0].get('goal_id')
        
        return {
            "best_goal_id": best_goal,
            "confidence": 20,
            "satisfaction_score": 30,
            "selection_reasoning": "Fallback selection due to parsing error",
            "alternatives": [],
            "alignment_details": {},
            "requires_confirmation": True,
            "decision_confidence": 20
        }

# Global instance
ai_semantic_mapper = AISemanticMapper()

# Export for easy import
__all__ = ["AISemanticMapper", "ai_semantic_mapper", "SemanticMappingResult"]