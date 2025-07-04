# backend/ai_quality_assurance/smart_evaluator.py

import json
import logging
import re
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import asyncio

# Graceful imports with fallbacks
try:
    from openai import AsyncOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    AsyncOpenAI = None

try:
    from models import AssetSchema, AssetQualityMetrics
except ImportError:
    # Fallback model definitions
    from pydantic import BaseModel, Field
    class AssetQualityMetrics(BaseModel):
        overall_quality: float = Field(..., ge=0.0, le=1.0)
        actionability_score: float = Field(..., ge=0.0, le=1.0)
        completeness_score: float = Field(..., ge=0.0, le=1.0)
        concreteness_score: float = Field(..., ge=0.0, le=1.0)
        business_value_score: float = Field(..., ge=0.0, le=1.0)
        needs_enhancement: bool = Field(...)
        enhancement_suggestions: List[str] = Field(default_factory=list)

try:
    from config.quality_system_config import QualitySystemConfig
except ImportError:
    # Fallback config
    class QualitySystemConfig:
        QUALITY_SCORE_THRESHOLD = 0.8
        ACTIONABILITY_THRESHOLD = 0.7

logger = logging.getLogger(__name__)

class SmartDeliverableEvaluator:
    """
    Sistema AI-powered per valutazione intelligente dei deliverable
    Usa AI per rilevare concretezza, actionability e valore business
    """
    
    def __init__(self):
        self.client = None
        if HAS_OPENAI:
            if os.getenv("OPENAI_API_KEY"):
                try:
                    self.client = AsyncOpenAI()
                except Exception as e:
                    logger.warning(f"OpenAI client initialization failed: {e}")
            else:
                logger.warning("OPENAI_API_KEY environment variable not set. OpenAI client will not be initialized.")
        else:
            logger.warning("OpenAI library not found. OpenAI client will not be initialized.")
        
        # Thresholds stringenti per asset concreti
        self.concrete_threshold = 0.85
        self.actionability_threshold = 0.90
        self.completeness_threshold = 0.85
        
        # Cache per performance
        self.evaluation_cache = {}
        
        # Pattern per rilevare contenuto teorico/placeholder
        self.theoretical_patterns = [
            r"potrebbe essere",
            r"dovresti considerare", 
            r"potresti valutare",
            r"potrebbe includere",
            r"è importante",
            r"strategia generale",
            r"approccio consigliato",
            r"marketing generale",
            r"vari canali",
            r"pubblico target",
            r"\[placeholder\]",
            r"\[inserire qui\]",
            r"esempio:",
            r"template:",
            r"generico",
            r"da definire",
            r"da personalizzare",
            r"should consider",
            r"could include",
            r"might want",
            r"general strategy"
        ]
        
        # Pattern per contenuto concreto
        self.concrete_patterns = [
            r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",  # Date specifiche
            r"#\w+",  # Hashtag reali
            r"@\w+",  # Mention utenti
            r"\d+:\d+",  # Orari specifici
            r"€?\d+",  # Valori numerici
            r"https?://",  # Link diretti
            r'"[^"]+"',  # Testo quotato specifico
            r'\[[^\]]+\]',  # Contenuto strutturato
        ]
    
    async def evaluate_deliverable_quality(
        self, 
        deliverable_data: Dict[str, Any],
        workspace_goal: str
    ) -> AssetQualityMetrics:
        """
        Valuta la qualità complessiva di un deliverable usando AI
        """
        
        try:
            # Estrai assets dal deliverable
            assets = deliverable_data.get("assets", [])
            
            if not assets:
                return AssetQualityMetrics(
                    overall_quality=0.0,
                    actionability_score=0.0,
                    completeness_score=0.0,
                    concreteness_score=0.0,
                    business_value_score=0.0,
                    needs_enhancement=True,
                    enhancement_suggestions=["No assets found in deliverable"]
                )
            
            # Valuta ogni asset
            asset_scores = []
            enhancement_suggestions = []
            
            for asset in assets:
                score, suggestions = await self._evaluate_single_asset(
                    asset, workspace_goal
                )
                asset_scores.append(score)
                enhancement_suggestions.extend(suggestions)
            
            # Calcola metriche aggregate
            avg_scores = self._aggregate_asset_scores(asset_scores)
            
            # Determina se serve enhancement
            needs_enhancement = (
                avg_scores["concreteness"] < self.concrete_threshold or
                avg_scores["actionability"] < self.actionability_threshold or
                avg_scores["completeness"] < self.completeness_threshold
            )
            
            # Crea metriche finali
            metrics = AssetQualityMetrics(
                overall_quality=avg_scores["overall"],
                actionability_score=avg_scores["actionability"],
                completeness_score=avg_scores["completeness"],
                concreteness_score=avg_scores["concreteness"],
                business_value_score=avg_scores["business_value"],
                needs_enhancement=needs_enhancement,
                enhancement_suggestions=enhancement_suggestions[:5]  # Top 5
            )
            
            logger.info(f"📊 Deliverable Quality Evaluated: "
                       f"Overall={metrics.overall_quality:.2f}, "
                       f"Concrete={metrics.concreteness_score:.2f}, "
                       f"Enhancement Needed={needs_enhancement}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error evaluating deliverable quality: {e}")
            return AssetQualityMetrics(
                overall_quality=0.5,
                actionability_score=0.5,
                completeness_score=0.5,
                concreteness_score=0.5,
                business_value_score=0.5,
                needs_enhancement=True,
                enhancement_suggestions=[f"Evaluation error: {str(e)}"]
            )
    
    async def _evaluate_single_asset(
        self, 
        asset: Dict[str, Any],
        workspace_goal: str
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Valuta un singolo asset usando AI + rule-based analysis
        """
        
        asset_type = asset.get("type", "unknown")
        content = json.dumps(asset.get("content", {}), default=str)
        
        # Quick rule-based check first
        rule_scores = self._rule_based_evaluation(content)
        
        # Se ovviamente teorico, skip AI call
        if rule_scores["concreteness"] < 0.3:
            return rule_scores, [
                f"Asset '{asset_type}' contains mostly theoretical content",
                "Add specific dates, names, numbers, and actionable items"
            ]
        
        # AI evaluation per casi complessi
        ai_scores, ai_suggestions = await self._ai_powered_evaluation(
            asset_type, content, workspace_goal
        )
        
        # Combina rule-based e AI scores
        combined_scores = {
            "concreteness": (rule_scores["concreteness"] + ai_scores["concreteness"]) / 2,
            "actionability": ai_scores["actionability"],
            "completeness": ai_scores["completeness"],
            "business_value": ai_scores["business_value"],
            "overall": 0.0  # Calcolato dopo
        }
        
        # Overall score ponderato
        combined_scores["overall"] = (
            combined_scores["concreteness"] * 0.4 +
            combined_scores["actionability"] * 0.3 +
            combined_scores["completeness"] * 0.2 +
            combined_scores["business_value"] * 0.1
        )
        
        return combined_scores, ai_suggestions
    
    def _rule_based_evaluation(self, content: str) -> Dict[str, float]:
        """
        Valutazione veloce basata su pattern regex
        """
        
        content_lower = content.lower()
        
        # Conta pattern teorici
        theoretical_count = sum(
            len(re.findall(pattern, content_lower)) 
            for pattern in self.theoretical_patterns
        )
        
        # Conta pattern concreti
        concrete_count = sum(
            len(re.findall(pattern, content)) 
            for pattern in self.concrete_patterns
        )
        
        # Calcola score concretezza con logica più severa
        if theoretical_count > 0:
            # Se ha pattern teorici, penalizza pesantemente
            if theoretical_count >= 4:
                concreteness = 0.05  # Molto teorico  
            elif theoretical_count >= 3:
                concreteness = 0.15  # Molto teorico
            elif theoretical_count >= 2:
                concreteness = 0.25  # Abbastanza teorico
            else:
                concreteness = 0.4   # Un po' teorico
            
            # Aggiusta leggermente se ha anche pattern concreti
            if concrete_count > 0:
                concreteness = min(0.5, concreteness + (concrete_count * 0.05))
        else:
            # Nessun pattern teorico, valuta sui concreti
            if concrete_count > 3:
                concreteness = 0.9
            elif concrete_count > 0:
                concreteness = 0.7
            else:
                concreteness = 0.5  # Neutro
        
        return {
            "concreteness": min(1.0, concreteness),
            "actionability": 0.5,  # Default, AI determinerà
            "completeness": 0.5,   # Default, AI determinerà
            "business_value": 0.5, # Default, AI determinerà
            "overall": concreteness * 0.5
        }
    
    async def _ai_powered_evaluation(
        self,
        asset_type: str,
        content: str,
        workspace_goal: str
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Valutazione AI sofisticata per asset quality
        """
        
        # Check cache
        cache_key = f"{asset_type}_{hash(content[:200])}"
        if cache_key in self.evaluation_cache:
            return self.evaluation_cache[cache_key]
        
        # Fallback to rule-based if no AI available or client not initialized
        if not self.client:
            logger.info("AI evaluation unavailable or client not initialized, using enhanced rule-based scoring")
            return self._enhanced_rule_based_evaluation(asset_type, content, workspace_goal)
        
        try:
            # Prompt ottimizzato per valutazione concreta
            evaluation_prompt = f"""
You are an expert business asset evaluator. Evaluate this {asset_type} asset for immediate business use.

Workspace Goal: {workspace_goal}
Asset Content: {content[:2000]}  # Truncate per token limit

Evaluate on these STRICT criteria:

1. CONCRETENESS (0.0-1.0):
   - 0.9-1.0: Specific names, dates, numbers, real examples
   - 0.5-0.8: Some specifics but still generic elements
   - 0.0-0.4: Mostly theoretical, templates, or placeholders

2. ACTIONABILITY (0.0-1.0):
   - 0.9-1.0: Can be used immediately without changes
   - 0.5-0.8: Needs minor customization
   - 0.0-0.4: Requires significant work to use

3. COMPLETENESS (0.0-1.0):
   - 0.9-1.0: All required elements present
   - 0.5-0.8: Most elements present, some gaps
   - 0.0-0.4: Major elements missing

4. BUSINESS VALUE (0.0-1.0):
   - 0.9-1.0: High ROI, immediate impact
   - 0.5-0.8: Moderate value, useful
   - 0.0-0.4: Low value, minimal impact

Provide response as JSON:
{{
    "scores": {{
        "concreteness": 0.0-1.0,
        "actionability": 0.0-1.0,
        "completeness": 0.0-1.0,
        "business_value": 0.0-1.0
    }},
    "suggestions": ["specific improvement 1", "specific improvement 2"]
}}

Be HARSH in scoring. Only give high scores to truly exceptional, ready-to-use assets.
"""
            
            # Call AI
            response = await self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "You are a strict business asset quality evaluator."},
                    {"role": "user", "content": evaluation_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            evaluation = json.loads(response.choices[0].message.content)
            scores = evaluation.get("scores", {})
            suggestions = evaluation.get("suggestions", [])
            
            # Ensure all scores present
            final_scores = {
                "concreteness": scores.get("concreteness", 0.5),
                "actionability": scores.get("actionability", 0.5),
                "completeness": scores.get("completeness", 0.5),
                "business_value": scores.get("business_value", 0.5)
            }
            
            # Cache result
            self.evaluation_cache[cache_key] = (final_scores, suggestions)
            
            return final_scores, suggestions
            
        except Exception as e:
            logger.error(f"AI evaluation failed: {e}")
            # Fallback scores
            return {
                "concreteness": 0.5,
                "actionability": 0.5,
                "completeness": 0.5,
                "business_value": 0.5
            }, ["AI evaluation unavailable"]
    
    def _enhanced_rule_based_evaluation(
        self, 
        asset_type: str, 
        content: str, 
        workspace_goal: str
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Enhanced rule-based evaluation when AI is unavailable
        """
        
        content_lower = content.lower()
        suggestions = []
        
        # Concreteness analysis
        concrete_indicators = sum([
            len(re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', content)),  # dates
            len(re.findall(r'#\w+', content)),  # hashtags
            len(re.findall(r'@\w+', content)),  # mentions
            len(re.findall(r'https?://', content)),  # links
            len(re.findall(r'€?\d+', content)),  # numbers/prices
        ])
        
        theoretical_indicators = sum([
            content_lower.count('should'),
            content_lower.count('could'),
            content_lower.count('example'),
            content_lower.count('template'),
            content_lower.count('placeholder'),
        ])
        
        # Concreteness score
        if concrete_indicators > theoretical_indicators * 2:
            concreteness = min(0.9, 0.6 + (concrete_indicators / 10))
        elif concrete_indicators > theoretical_indicators:
            concreteness = 0.7
        else:
            concreteness = max(0.3, 0.6 - (theoretical_indicators / 10))
            suggestions.append("Add specific dates, numbers, and real examples")
        
        # Actionability analysis based on asset type
        actionability = 0.5  # default
        if asset_type == "content_calendar":
            if "caption" in content_lower and "hashtag" in content_lower:
                actionability = 0.85
            else:
                suggestions.append("Include complete captions and hashtags")
        elif asset_type == "contact_database":
            if "@" in content and "name" in content_lower:
                actionability = 0.8
            else:
                suggestions.append("Include complete contact information")
        elif asset_type == "email_templates":
            if "subject" in content_lower and len(content) > 100:
                actionability = 0.8
            else:
                suggestions.append("Include subject line and complete email body")
        
        # Completeness based on content length and structure
        if len(content) > 500:
            completeness = 0.8
        elif len(content) > 200:
            completeness = 0.6
        else:
            completeness = 0.4
            suggestions.append("Expand content with more detailed information")
        
        # Business value based on goal alignment
        goal_lower = workspace_goal.lower()
        goal_keywords = [word for word in goal_lower.split() if len(word) > 3]
        matches = sum(1 for keyword in goal_keywords if keyword in content_lower)
        business_value = min(0.9, 0.5 + (matches / len(goal_keywords)) * 0.4) if goal_keywords else 0.5
        
        scores = {
            "concreteness": concreteness,
            "actionability": actionability,
            "completeness": completeness,
            "business_value": business_value
        }
        
        return scores, suggestions[:3]  # Top 3 suggestions
    
    def _aggregate_asset_scores(
        self, 
        asset_scores: List[Dict[str, float]]
    ) -> Dict[str, float]:
        """
        Aggrega scores di multipli asset
        """
        
        if not asset_scores:
            return {
                "overall": 0.0,
                "concreteness": 0.0,
                "actionability": 0.0,
                "completeness": 0.0,
                "business_value": 0.0
            }
        
        # Media ponderata con penalty per asset scarsi
        aggregated = {}
        for metric in ["concreteness", "actionability", "completeness", "business_value", "overall"]:
            scores = [s.get(metric, 0) for s in asset_scores]
            
            # Media con penalty per outlier negativi
            avg = sum(scores) / len(scores)
            min_score = min(scores)
            
            # Se c'è un asset molto scarso, penalizza il totale
            if min_score < 0.5:
                avg *= (0.7 + min_score * 0.6)
            
            aggregated[metric] = avg
        
        return aggregated
    
    async def generate_enhancement_tasks(
        self,
        deliverable_data: Dict[str, Any],
        quality_metrics: AssetQualityMetrics
    ) -> List[Dict[str, Any]]:
        """
        Genera task specifici per migliorare la qualità del deliverable
        """
        
        enhancement_tasks = []
        
        # Se concretezza bassa
        if quality_metrics.concreteness_score < self.concrete_threshold:
            enhancement_tasks.append({
                "name": "Make deliverable content concrete and specific",
                "description": f"Current concreteness score: {quality_metrics.concreteness_score:.2f}. "
                             "Replace all theoretical content with specific examples, real data, "
                             "actual dates, names, and actionable items.",
                "priority": "critical",
                "estimated_effort": "medium",
                "success_criteria": [
                    "All placeholders replaced with real content",
                    "Specific dates and timelines added",
                    "Real examples and case studies included",
                    f"Concreteness score above {self.concrete_threshold}"
                ]
            })
        
        # Se actionability bassa
        if quality_metrics.actionability_score < self.actionability_threshold:
            enhancement_tasks.append({
                "name": "Enhance deliverable actionability",
                "description": f"Current actionability score: {quality_metrics.actionability_score:.2f}. "
                             "Add step-by-step instructions, templates, and ready-to-use materials.",
                "priority": "high",
                "estimated_effort": "medium",
                "success_criteria": [
                    "Clear next steps for each asset",
                    "Templates ready for immediate use",
                    "No additional work needed to implement",
                    f"Actionability score above {self.actionability_threshold}"
                ]
            })
        
        # Task specifici basati sui suggerimenti
        for idx, suggestion in enumerate(quality_metrics.enhancement_suggestions[:3]):
            enhancement_tasks.append({
                "name": f"Address quality issue: {suggestion[:50]}...",
                "description": suggestion,
                "priority": "medium",
                "estimated_effort": "low",
                "success_criteria": ["Issue resolved", "Quality improved"]
            })
        
        return enhancement_tasks
    
    def validate_asset_concreteness(self, asset_content: Dict[str, Any]) -> bool:
        """
        Validazione rapida per verificare se un asset è concreto
        """
        
        content_str = json.dumps(asset_content, default=str).lower()
        
        # Check per pattern teorici
        theoretical_count = sum(
            1 for pattern in self.theoretical_patterns 
            if re.search(pattern, content_str)
        )
        
        # Check per pattern concreti
        concrete_count = sum(
            1 for pattern in self.concrete_patterns 
            if re.search(pattern, json.dumps(asset_content, default=str))
        )
        
        # Asset è concreto se ha più pattern concreti che teorici
        return concrete_count > theoretical_count * 2

    async def evaluate_with_ai(self, prompt: str, context: str, max_tokens: int = 500) -> Optional[Dict[str, Any]]:
        """
        Generic method to call OpenAI API for evaluation.
        """
        if not self.client:
            logger.warning(f"OpenAI client not initialized for evaluate_with_ai in context: {context}")
            return None
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # Or another suitable model
                messages=[
                    {"role": "system", "content": f"You are an expert AI assistant for {context}."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=max_tokens,
                response_format={"type": "json_object"}
            )
            return {"raw_response": json.loads(response.choices[0].message.content.strip())}
        except Exception as e:
            logger.error(f"Error calling OpenAI API for {context} evaluation: {e}")
            return None

# Singleton instance
smart_evaluator = SmartDeliverableEvaluator()