"""
🤖 Universal AI Content Extractor
100% AI-Driven, Domain Agnostic, Zero Hardcode Approach

Pillar 7: Domain Agnostic - Works for any business domain without modifications
Pillar 8: No Hardcode - Zero pattern matching, categorization, or assumptions
Pillar 9: Adaptive AI - AI understands any content type autonomously  
Pillar 10: Real-time Reasoning - AI semantic analysis for content discovery
Pillar 11: Self-Enhancement - AI auto-validates and improves own analysis
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ContentAnalysisResult:
    """AI analysis result for discovered content"""
    discovered_content: Dict[str, Any]
    reality_score: float  # 0-100, how real vs template the content is
    usability_score: float  # 0-100, how directly usable the content is
    business_specificity: float  # 0-100, how specific to this business vs generic
    confidence: float  # 0-100, AI confidence in the analysis
    reasoning: str  # AI explanation of the analysis
    missing_elements: List[str]  # What's missing to complete the deliverable
    suggested_completions: List[Dict[str, Any]]  # AI suggestions for completion

class UniversalAIContentExtractor:
    """
    🤖 Pure AI-Driven Content Extractor
    Zero hardcoded patterns, types, or assumptions
    """
    
    def __init__(self):
        self.extraction_history = []  # For self-learning
        
    async def extract_real_content(
        self, 
        task_results: List[Dict[str, Any]], 
        goal_context: str,
        workspace_context: Dict[str, Any] = None
    ) -> ContentAnalysisResult:
        """
        🤖 AI-DRIVEN: Semantic content discovery without assumptions
        
        Args:
            task_results: Raw results from completed tasks
            goal_context: The goal this content should satisfy
            workspace_context: Business context for validation
            
        Returns:
            ContentAnalysisResult with pure AI analysis
        """
        try:
            logger.info("🤖 Starting pure AI semantic content extraction...")
            
            # Step 1: AI Content Discovery (no assumptions)
            discovered_content = await self._ai_discover_content(task_results)
            
            # Step 2: AI Reality Assessment (real vs template)
            reality_analysis = await self._ai_assess_content_reality(
                discovered_content, 
                workspace_context
            )
            
            # Step 3: AI Usability Evaluation
            usability_analysis = await self._ai_evaluate_usability(
                discovered_content,
                goal_context
            )
            
            # Step 4: AI Gap Analysis & Completion Suggestions
            gap_analysis = await self._ai_analyze_gaps(
                discovered_content,
                goal_context,
                reality_analysis.get('missing_elements', [])
            )
            
            # Compile results
            result = ContentAnalysisResult(
                discovered_content=discovered_content,
                reality_score=reality_analysis.get('reality_score', 0),
                usability_score=usability_analysis.get('usability_score', 0),
                business_specificity=reality_analysis.get('business_specificity', 0),
                confidence=min(
                    reality_analysis.get('confidence', 0),
                    usability_analysis.get('confidence', 0)
                ),
                reasoning=self._compile_reasoning(
                    reality_analysis, 
                    usability_analysis, 
                    gap_analysis
                ),
                missing_elements=gap_analysis.get('missing_elements', []),
                suggested_completions=gap_analysis.get('suggestions', [])
            )
            
            # Self-learning: Store for pattern improvement
            await self._store_extraction_learning(task_results, result)
            
            logger.info(f"✅ AI extraction complete: Reality={result.reality_score:.1f}, Usability={result.usability_score:.1f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in AI content extraction: {e}")
            return self._create_error_result(str(e))
    
    async def _ai_discover_content(self, task_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        🤖 AI semantic content discovery without type assumptions
        """
        try:
            # Import OpenAI directly for AI analysis
            import os
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # Prepare task results for AI analysis
            results_text = self._prepare_results_for_analysis(task_results)
            
            discovery_prompt = f"""
Analizza questi risultati di task senza assumere cosa dovrebbero contenere.
Non usare categorizzazioni predefinite (email, contatti, strategie, ecc.).

RISULTATI DA ANALIZZARE:
{results_text}

ISTRUZIONI:
1. Identifica tutto il contenuto concreto e utilizzabile presente
2. Distingui tra:
   - Contenuto REALE (specifico, implementabile, business-ready)
   - Contenuto TEMPLATE (generico, placeholder, "Aimed at...", "Designed to...")
   - Contenuto PARZIALE (iniziato ma incompleto)

3. Per ogni elemento identificato, estrai:
   - Il contenuto esatto come fornito
   - La funzione/scopo di questo contenuto
   - Quanto è specifico vs generico

4. NON categorizzare in tipi predefiniti, descrivere cosa è realmente presente

Rispondi in JSON con questa struttura:
{{
    "discovered_items": [
        {{
            "content": "contenuto esatto estratto",
            "purpose": "a cosa serve questo contenuto",
            "completeness": "completo/parziale/template",
            "specificity": "specifico/generico/misto",
            "source_task": "nome del task da cui proviene"
        }}
    ],
    "overall_assessment": "valutazione generale di cosa è stato prodotto",
    "content_types_found": ["tipi di contenuto scoperti organicamente"],
    "extraction_confidence": 0-100
}}
"""
            
            # Get AI analysis using OpenAI
            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert content analyzer. Respond only with valid JSON."},
                    {"role": "user", "content": discovery_prompt}
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            ai_response = response.choices[0].message.content
            
            # Parse AI response
            if isinstance(ai_response, str):
                try:
                    discovered = json.loads(ai_response)
                except json.JSONDecodeError:
                    # Fallback parsing
                    discovered = self._parse_ai_response_fallback(ai_response)
            else:
                discovered = ai_response
                
            return discovered
            
        except Exception as e:
            logger.error(f"Error in AI content discovery: {e}")
            return {
                "discovered_items": [],
                "overall_assessment": f"Discovery failed: {e}",
                "content_types_found": [],
                "extraction_confidence": 0
            }
    
    async def _ai_assess_content_reality(
        self, 
        discovered_content: Dict[str, Any], 
        workspace_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        🤖 AI assessment of content reality vs template nature
        """
        try:
            from ai_quality_assurance.smart_evaluator import smart_evaluator
            
            business_info = self._extract_business_context(workspace_context)
            
            reality_prompt = f"""
Valuta la REALTÀ di questo contenuto senza usare pattern predefiniti di fake content.

CONTENUTO DA VALUTARE:
{json.dumps(discovered_content, indent=2)}

CONTESTO BUSINESS:
{business_info}

ISTRUZIONI:
1. Per ogni elemento, determina se è:
   - REALE: Specifico, implementabile, pronto per l'uso business
   - TEMPLATE: Descrizioni generiche, placeholder, esempi
   - PARZIALE: Iniziato ma richiede completamento

2. Valuta specificità per questo business:
   - È personalizzato per questo business specifico?
   - Contiene dettagli specifici o è generico?
   - È utilizzabile così com'è o richiede personalizzazione?

3. Identifica elementi mancanti per renderlo completamente utilizzabile

NO pattern matching hardcoded. Usa solo comprensione semantica.

Rispondi in JSON:
{{
    "reality_score": 0-100,
    "business_specificity": 0-100,
    "detailed_assessment": [
        {{
            "item": "contenuto valutato",
            "reality_level": "reale/template/parziale",
            "business_specific": true/false,
            "usable_as_is": true/false,
            "reasoning": "perché questa valutazione"
        }}
    ],
    "missing_elements": ["cosa manca per renderlo completamente reale"],
    "confidence": 0-100,
    "overall_reasoning": "spiegazione della valutazione generale"
}}
"""
            
            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert content reality validator. Respond only with valid JSON."},
                    {"role": "user", "content": reality_prompt}
                ],
                max_tokens=1500,
                temperature=0.1
            )
            
            ai_response = response.choices[0].message.content
            
            if isinstance(ai_response, str):
                try:
                    assessment = json.loads(ai_response)
                except json.JSONDecodeError:
                    assessment = self._parse_reality_assessment_fallback(ai_response)
            else:
                assessment = ai_response
                
            return assessment
            
        except Exception as e:
            logger.error(f"Error in AI reality assessment: {e}")
            return {
                "reality_score": 0,
                "business_specificity": 0,
                "detailed_assessment": [],
                "missing_elements": ["Assessment failed"],
                "confidence": 0,
                "overall_reasoning": f"Assessment error: {e}"
            }
    
    async def _ai_evaluate_usability(
        self, 
        discovered_content: Dict[str, Any], 
        goal_context: str
    ) -> Dict[str, Any]:
        """
        🤖 AI evaluation of content usability for the specific goal
        """
        try:
            from ai_quality_assurance.smart_evaluator import smart_evaluator
            
            usability_prompt = f"""
Valuta quanto questo contenuto soddisfa l'obiettivo in modo UTILIZZABILE.

CONTENUTO:
{json.dumps(discovered_content, indent=2)}

OBIETTIVO DA SODDISFARE:
{goal_context}

VALUTAZIONE RICHIESTA:
1. Il contenuto presente risolve l'obiettivo?
2. È utilizzabile direttamente dall'utente?
3. Cosa manca per considerarlo "deliverable completo"?
4. Quanto effort richiede per essere business-ready?

Non assumere cosa dovrebbe essere il contenuto. Valuta solo quanto quello presente serve all'obiettivo.

Rispondi in JSON:
{{
    "usability_score": 0-100,
    "goal_satisfaction": 0-100,
    "directly_usable": true/false,
    "effort_required": "nessuno/minimo/moderato/significativo",
    "specific_gaps": ["cosa specificamente manca"],
    "usability_reasoning": "spiegazione dettagliata",
    "confidence": 0-100
}}
"""
            
            ai_response = await smart_evaluator.evaluate_with_ai(
                usability_prompt,
                context="usability_evaluation",
                max_tokens=1000
            )
            
            if isinstance(ai_response, str):
                try:
                    evaluation = json.loads(ai_response)
                except json.JSONDecodeError:
                    evaluation = self._parse_usability_evaluation_fallback(ai_response)
            else:
                evaluation = ai_response
                
            return evaluation
            
        except Exception as e:
            logger.error(f"Error in AI usability evaluation: {e}")
            return {
                "usability_score": 0,
                "goal_satisfaction": 0,
                "directly_usable": False,
                "effort_required": "unknown",
                "specific_gaps": ["Evaluation failed"],
                "usability_reasoning": f"Evaluation error: {e}",
                "confidence": 0
            }
    
    async def _ai_analyze_gaps(
        self, 
        discovered_content: Dict[str, Any], 
        goal_context: str,
        missing_elements: List[str]
    ) -> Dict[str, Any]:
        """
        🤖 AI gap analysis and intelligent completion suggestions
        """
        try:
            from ai_quality_assurance.smart_evaluator import smart_evaluator
            
            gap_prompt = f"""
Analizza i gap in questo contenuto e suggerisci completamenti INTELLIGENTI.

CONTENUTO ATTUALE:
{json.dumps(discovered_content, indent=2)}

OBIETTIVO:
{goal_context}

ELEMENTI MANCANTI IDENTIFICATI:
{missing_elements}

COMPITO:
1. Identifica cosa manca per rendere il contenuto completamente utilizzabile
2. Suggerisci completamenti SPECIFICI e IMPLEMENTABILI (non template)
3. Prioritizza i completamenti per impatto

NON suggerire template o placeholder. Suggerisci contenuto business-ready specifico.

Rispondi in JSON:
{{
    "critical_gaps": ["gap che bloccano l'utilizzo"],
    "nice_to_have_gaps": ["gap che migliorerebbero la qualità"],
    "completion_suggestions": [
        {{
            "gap": "cosa manca",
            "suggested_completion": "completamento specifico suggerito",
            "priority": "critico/alto/medio/basso",
            "implementation_effort": "facile/medio/difficile",
            "business_impact": "alto/medio/basso"
        }}
    ],
    "overall_completeness": 0-100,
    "analysis_confidence": 0-100
}}
"""
            
            ai_response = await smart_evaluator.evaluate_with_ai(
                gap_prompt,
                context="gap_analysis",
                max_tokens=1500
            )
            
            if isinstance(ai_response, str):
                try:
                    analysis = json.loads(ai_response)
                except json.JSONDecodeError:
                    analysis = self._parse_gap_analysis_fallback(ai_response)
            else:
                analysis = ai_response
                
            # Convert to the format expected by ContentAnalysisResult
            return {
                "missing_elements": analysis.get("critical_gaps", []) + analysis.get("nice_to_have_gaps", []),
                "suggestions": analysis.get("completion_suggestions", []),
                "completeness": analysis.get("overall_completeness", 0),
                "confidence": analysis.get("analysis_confidence", 0)
            }
            
        except Exception as e:
            logger.error(f"Error in AI gap analysis: {e}")
            return {
                "missing_elements": ["Gap analysis failed"],
                "suggestions": [],
                "completeness": 0,
                "confidence": 0
            }
    
    def _prepare_results_for_analysis(self, task_results: List[Dict[str, Any]]) -> str:
        """Prepare task results for AI analysis"""
        formatted_results = []
        
        for i, task_result in enumerate(task_results):
            task_name = task_result.get('name', f'Task {i+1}')
            task_status = task_result.get('status', 'unknown')
            
            # Extract actual results/content
            result_content = ""
            if 'result' in task_result:
                result = task_result['result']
                if isinstance(result, dict):
                    # Look for various result formats
                    if 'detailed_results_json' in result:
                        result_content = str(result['detailed_results_json'])
                    elif 'summary' in result:
                        result_content = str(result['summary'])
                    elif 'output' in result:
                        result_content = str(result['output'])
                    else:
                        result_content = str(result)
                else:
                    result_content = str(result)
            
            formatted_results.append(f"""
TASK: {task_name}
STATUS: {task_status}
CONTENT:
{result_content}
---""")
        
        return "\n".join(formatted_results)
    
    def _extract_business_context(self, workspace_context: Dict[str, Any]) -> str:
        """Extract business context for AI analysis"""
        if not workspace_context:
            return "No specific business context available"
        
        context_parts = []
        
        # Extract business information
        if 'name' in workspace_context:
            context_parts.append(f"Business/Project: {workspace_context['name']}")
        
        if 'description' in workspace_context:
            context_parts.append(f"Description: {workspace_context['description']}")
        
        if 'industry' in workspace_context:
            context_parts.append(f"Industry: {workspace_context['industry']}")
        
        if 'goals' in workspace_context:
            context_parts.append(f"Goals: {workspace_context['goals']}")
        
        return "\n".join(context_parts) if context_parts else "General business context"
    
    def _compile_reasoning(
        self, 
        reality_analysis: Dict[str, Any], 
        usability_analysis: Dict[str, Any], 
        gap_analysis: Dict[str, Any]
    ) -> str:
        """Compile comprehensive reasoning from all AI analyses"""
        reasoning_parts = []
        
        # Reality reasoning
        if 'overall_reasoning' in reality_analysis:
            reasoning_parts.append(f"REALITY: {reality_analysis['overall_reasoning']}")
        
        # Usability reasoning  
        if 'usability_reasoning' in usability_analysis:
            reasoning_parts.append(f"USABILITY: {usability_analysis['usability_reasoning']}")
        
        # Gap analysis
        if gap_analysis.get('completeness', 0) < 80:
            reasoning_parts.append(f"GAPS: Content needs completion to be fully usable")
        
        return " | ".join(reasoning_parts)
    
    async def _store_extraction_learning(
        self, 
        task_results: List[Dict[str, Any]], 
        analysis_result: ContentAnalysisResult
    ):
        """Store extraction results for self-learning improvement"""
        try:
            learning_entry = {
                "timestamp": datetime.now().isoformat(),
                "input_tasks_count": len(task_results),
                "reality_score": analysis_result.reality_score,
                "usability_score": analysis_result.usability_score,
                "confidence": analysis_result.confidence,
                "content_types_discovered": list(analysis_result.discovered_content.keys())
            }
            
            self.extraction_history.append(learning_entry)
            
            # Keep only recent entries for memory efficiency
            if len(self.extraction_history) > 100:
                self.extraction_history = self.extraction_history[-100:]
                
        except Exception as e:
            logger.debug(f"Learning storage failed: {e}")
    
    def _create_error_result(self, error_message: str) -> ContentAnalysisResult:
        """Create error result when extraction fails"""
        return ContentAnalysisResult(
            discovered_content={"error": error_message},
            reality_score=0,
            usability_score=0,
            business_specificity=0,
            confidence=0,
            reasoning=f"Extraction failed: {error_message}",
            missing_elements=["Complete content extraction"],
            suggested_completions=[]
        )
    
    # Fallback parsers for when AI response is not valid JSON
    def _parse_ai_response_fallback(self, response: str) -> Dict[str, Any]:
        """Fallback parser for discovery response"""
        return {
            "discovered_items": [{"content": response, "purpose": "Raw AI response", "completeness": "unknown", "specificity": "unknown", "source_task": "ai_analysis"}],
            "overall_assessment": "Fallback parsing used",
            "content_types_found": ["text"],
            "extraction_confidence": 30
        }
    
    def _parse_reality_assessment_fallback(self, response: str) -> Dict[str, Any]:
        """Fallback parser for reality assessment"""
        return {
            "reality_score": 50,
            "business_specificity": 30,
            "detailed_assessment": [],
            "missing_elements": ["Proper AI analysis"],
            "confidence": 20,
            "overall_reasoning": f"Fallback used: {response[:200]}..."
        }
    
    def _parse_usability_evaluation_fallback(self, response: str) -> Dict[str, Any]:
        """Fallback parser for usability evaluation"""
        return {
            "usability_score": 30,
            "goal_satisfaction": 20,
            "directly_usable": False,
            "effort_required": "unknown",
            "specific_gaps": ["Proper evaluation"],
            "usability_reasoning": f"Fallback used: {response[:200]}...",
            "confidence": 20
        }
    
    def _parse_gap_analysis_fallback(self, response: str) -> Dict[str, Any]:
        """Fallback parser for gap analysis"""
        return {
            "critical_gaps": ["Analysis failed"],
            "nice_to_have_gaps": [],
            "completion_suggestions": [],
            "overall_completeness": 10,
            "analysis_confidence": 10
        }

# Global instance
universal_ai_content_extractor = UniversalAIContentExtractor()

# Export for easy import
__all__ = ["UniversalAIContentExtractor", "universal_ai_content_extractor", "ContentAnalysisResult"]