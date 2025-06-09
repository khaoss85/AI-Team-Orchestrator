# backend/ai_quality_assurance/quality_validator.py

import logging
import json
import re
import os
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

# OpenAI SDK import compatibile con il sistema esistente
try:
    import openai
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    logging.warning("OpenAI SDK not available. Quality validation will use fallback methods.")
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

class QualityIssueType(str, Enum):
    PLACEHOLDER_DATA = "placeholder_data"
    FAKE_CONTENT = "fake_content"
    GENERIC_STRUCTURE = "generic_structure"
    INCOMPLETE_DATA = "incomplete_data"
    NON_ACTIONABLE = "non_actionable"
    INCONSISTENT_FORMAT = "inconsistent_format"

class QualityAssessment(BaseModel):
    """Assessment della qualità di un asset"""
    overall_score: float = Field(..., ge=0.0, le=1.0)
    actionability_score: float = Field(..., ge=0.0, le=1.0)
    authenticity_score: float = Field(..., ge=0.0, le=1.0)
    completeness_score: float = Field(..., ge=0.0, le=1.0)
    
    quality_issues: List[QualityIssueType] = Field(default_factory=list)
    issue_details: Dict[str, str] = Field(default_factory=dict)
    
    improvement_suggestions: List[str] = Field(default_factory=list)
    enhancement_priority: str = Field(default="medium")  # low, medium, high, critical
    
    ready_for_use: bool = Field(default=False)
    needs_enhancement: bool = Field(default=True)
    
    # Metadati per tracking
    ai_model_used: Optional[str] = None
    total_tokens_used: Optional[int] = None
    validation_cost: Optional[float] = None
    validation_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class AIQualityValidator:
    """Valida la qualità degli asset usando AI per analisi flessibile"""
    
    def __init__(self):
        # Inizializza OpenAI client
        self.openai_client = None
        self.openai_available = OPENAI_AVAILABLE
        
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            try:
                self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                logger.info("✅ OpenAI client initialized for quality validation")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.openai_available = False
        else:
            logger.warning("OpenAI not available - quality validation will use fallback methods")
            self.openai_available = False
        
        # Configurazioni modelli allineate con il sistema esistente
        self.model_config = {
            "primary_model": "gpt-4.1-mini",  # Modello principale per quality validation
            "fallback_model": "gpt-4.1-nano",  # Fallback se primary non disponibile
            "max_tokens": 1000,  # Limite token per risposte
            "temperature": 0.1,  # Bassa temperatura per consistenza
            "timeout": 30.0  # Timeout per chiamate AI
        }
        
        # Token costs allineati con executor.py
        self.token_costs = {
            "gpt-4.1": {"input": 0.002, "output": 0.008},           # $2.00/$8.00 per 1K tokens
            "gpt-4.1-mini": {"input": 0.0004, "output": 0.0016},    # $0.40/$1.60 per 1K tokens
            "gpt-4.1-nano": {"input": 0.0001, "output": 0.0004},    # $0.10/$0.40 per 1K tokens
            "gpt-4o": {"input": 0.0025, "output": 0.01},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03}
        }
        
        # Pattern per fake content detection
        self.fake_content_patterns = [
            r"john\s+doe", r"jane\s+smith", r"example\.com", r"test@", 
            r"lorem\s+ipsum", r"placeholder", r"sample\s+data",
            r"xxx+", r"tbd", r"to\s+be\s+determined", r"coming\s+soon",
            r"mario\s+rossi", r"giuseppe\s+verdi"  # Common Italian fake names
        ]
        
        # Tracking per budget e performance
        self.total_tokens_used = 0
        self.total_cost = 0.0
        self.validation_count = 0
        
    async def validate_asset_quality(
        self, 
        asset_data: Dict[str, Any], 
        asset_type: str,
        context: Dict[str, Any]
    ) -> QualityAssessment:
        """
        Valuta la qualità di un asset usando AI reale o fallback
        """
        
        start_time = datetime.now()
        validation_cost = 0.0
        total_tokens = 0
        model_used = None
        
        try:
            logger.info(f"🔍 QUALITY VALIDATION: Starting for {asset_type}")
            
            # Analisi multi-dimensionale con AI reale
            if self.openai_available:
                authenticity_result = await self._assess_content_authenticity_ai(asset_data, context)
                actionability_result = await self._assess_actionability_ai(asset_data, asset_type, context)
                completeness_result = await self._assess_completeness_ai(asset_data, asset_type)
                
                # Estrai scores e metadati
                authenticity_score = authenticity_result["score"]
                actionability_score = actionability_result["score"]
                completeness_score = completeness_result["score"]
                
                # Accumula costi e token
                total_tokens = (authenticity_result.get("tokens", 0) + 
                              actionability_result.get("tokens", 0) + 
                              completeness_result.get("tokens", 0))
                validation_cost = (authenticity_result.get("cost", 0) + 
                                 actionability_result.get("cost", 0) + 
                                 completeness_result.get("cost", 0))
                model_used = authenticity_result.get("model")
                
                logger.info(f"✅ AI ANALYSIS: Auth={authenticity_score:.2f}, Action={actionability_score:.2f}, Complete={completeness_score:.2f}")
            else:
                # Fallback a analisi rule-based
                logger.warning("🔄 FALLBACK: Using rule-based quality analysis")
                authenticity_score = self._assess_content_authenticity_fallback(asset_data, context)
                actionability_score = self._assess_actionability_fallback(asset_data, asset_type)
                completeness_score = self._assess_completeness_fallback(asset_data, asset_type)
                model_used = "rule_based_fallback"
            
            # Rileva issue specifici (sempre rule-based per affidabilità)
            quality_issues = []
            issue_details = {}
            
            # Fake content detection
            fake_content_report = self._detect_fake_content(asset_data)
            if fake_content_report["has_fake_content"]:
                quality_issues.append(QualityIssueType.FAKE_CONTENT)
                issue_details["fake_content"] = fake_content_report["details"]
                
            # Placeholder detection
            placeholder_report = self._detect_placeholders(asset_data)
            if placeholder_report["has_placeholders"]:
                quality_issues.append(QualityIssueType.PLACEHOLDER_DATA)
                issue_details["placeholder_data"] = placeholder_report["details"]
                
            # Generic structure detection
            if await self._is_generic_structure(asset_data, asset_type):
                quality_issues.append(QualityIssueType.GENERIC_STRUCTURE)
                issue_details["generic_structure"] = "Asset has generic structure instead of domain-specific format"
                
            # Incomplete data detection
            if completeness_score < 0.5:
                quality_issues.append(QualityIssueType.INCOMPLETE_DATA)
                issue_details["incomplete_data"] = "Asset lacks sufficient data for business use"
                
            # Non-actionable content detection
            if actionability_score < 0.6:
                quality_issues.append(QualityIssueType.NON_ACTIONABLE)
                issue_details["non_actionable"] = "Asset requires significant modification before use"
            
            # Calcola score complessivo con penalità per issue
            base_score = (authenticity_score + actionability_score + completeness_score) / 3
            issue_penalty = min(len(quality_issues) * 0.1, 0.3)  # Max 30% penalty
            overall_score = max(0.0, base_score - issue_penalty)
            
            # Determina priorità di enhancement
            enhancement_priority = self._determine_enhancement_priority(
                overall_score, quality_issues, context
            )
            
            # Genera suggerimenti di miglioramento
            if self.openai_available:
                improvement_suggestions = await self._generate_improvement_suggestions_ai(
                    asset_data, asset_type, quality_issues, context
                )
                if improvement_suggestions.get("cost"):
                    validation_cost += improvement_suggestions["cost"]
                    total_tokens += improvement_suggestions.get("tokens", 0)
                suggestions = improvement_suggestions.get("suggestions", [])
            else:
                suggestions = self._generate_improvement_suggestions_fallback(
                    asset_type, quality_issues
                )
            
            # Update tracking
            self.validation_count += 1
            self.total_tokens_used += total_tokens
            self.total_cost += validation_cost
            
            # Log final results
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"🎯 QUALITY VALIDATION COMPLETE: Score={overall_score:.2f}, "
                       f"Issues={len(quality_issues)}, Priority={enhancement_priority}, "
                       f"Time={execution_time:.1f}s, Cost=${validation_cost:.6f}")
            
            return QualityAssessment(
                overall_score=overall_score,
                actionability_score=actionability_score,
                authenticity_score=authenticity_score,
                completeness_score=completeness_score,
                quality_issues=quality_issues,
                issue_details=issue_details,
                improvement_suggestions=suggestions,
                enhancement_priority=enhancement_priority,
                ready_for_use=overall_score >= 0.8 and len(quality_issues) == 0,
                needs_enhancement=overall_score < 0.7 or len(quality_issues) > 0,
                ai_model_used=model_used,
                total_tokens_used=total_tokens,
                validation_cost=validation_cost
            )
            
        except Exception as e:
            logger.error(f"❌ QUALITY VALIDATION ERROR: {e}", exc_info=True)
            return QualityAssessment(
                overall_score=0.0,
                actionability_score=0.0,
                authenticity_score=0.0,
                completeness_score=0.0,
                quality_issues=[QualityIssueType.INCOMPLETE_DATA],
                issue_details={"validation_error": str(e)},
                improvement_suggestions=["Manual review required due to validation error"],
                enhancement_priority="critical",
                ready_for_use=False,
                needs_enhancement=True,
                ai_model_used=model_used or "error",
                total_tokens_used=total_tokens,
                validation_cost=validation_cost
            )
    
    async def _assess_content_authenticity_ai(self, asset_data: Dict, context: Dict) -> Dict[str, Any]:
        """
        Usa AI reale per valutare l'autenticità del contenuto
        """
        
        data_sample = self._extract_data_sample(asset_data)
        project_context = context.get("workspace_goal", "")
        
        prompt = f"""You are a business data quality expert. Analyze the authenticity of this business data.

PROJECT CONTEXT: {project_context}

DATA SAMPLE:
{data_sample}

Evaluate the authenticity on a scale of 0.0-1.0 based on:
- Does this contain real, specific business data?
- Are there concrete facts, numbers, names, dates?
- Is it derived from actual research/analysis?
- Avoid generic examples or placeholder content

Respond in this exact JSON format:
{{
    "score": 0.0-1.0,
    "reasoning": "brief explanation of score",
    "authenticity_indicators": ["list", "of", "positive", "indicators"],
    "fake_indicators": ["list", "of", "fake", "or", "generic", "elements"]
}}"""

        return await self._call_openai_api(prompt, "authenticity_assessment")
    
    async def _assess_actionability_ai(self, asset_data: Dict, asset_type: str, context: Dict) -> Dict[str, Any]:
        """
        Valuta quanto l'asset sia immediatamente azionabile
        """
        
        data_sample = self._extract_data_sample(asset_data)
        
        prompt = f"""You are a business consultant evaluating the actionability of a {asset_type} asset.

ASSET DATA:
{data_sample}

Evaluate actionability on a scale of 0.0-1.0 based on:
- Can this be used immediately without modification?
- Does it contain specific, implementable actions?
- Are there clear next steps and instructions?
- Is it complete enough for business use?

Respond in this exact JSON format:
{{
    "score": 0.0-1.0,
    "reasoning": "brief explanation",
    "ready_to_use_elements": ["list", "of", "immediately", "usable", "parts"],
    "missing_elements": ["list", "of", "missing", "or", "incomplete", "parts"],
    "actionability_level": "ready_to_use|needs_customization|template_only"
}}"""

        return await self._call_openai_api(prompt, "actionability_assessment")
    
    async def _assess_completeness_ai(self, asset_data: Dict, asset_type: str) -> Dict[str, Any]:
        """
        Valuta la completezza dell'asset
        """
        
        field_count = self._count_populated_fields(asset_data)
        data_depth = self._calculate_data_depth(asset_data)
        data_sample = self._extract_data_sample(asset_data)
        
        prompt = f"""You are evaluating the completeness of a {asset_type} business asset.

ASSET STRUCTURE: {field_count} populated fields, {data_depth} levels deep
DATA SAMPLE:
{data_sample}

For a high-quality {asset_type}, evaluate completeness on a scale of 0.0-1.0:
- Are all necessary sections present?
- Is the data sufficient for business use?
- Are there significant gaps or missing information?

Respond in this exact JSON format:
{{
    "score": 0.0-1.0,
    "reasoning": "brief explanation",
    "complete_sections": ["list", "of", "well", "populated", "sections"],
    "missing_sections": ["list", "of", "missing", "or", "incomplete", "sections"],
    "data_density": "sparse|adequate|rich"
}}"""

        return await self._call_openai_api(prompt, "completeness_assessment")
    
    async def _generate_improvement_suggestions_ai(
        self, 
        asset_data: Dict, 
        asset_type: str, 
        quality_issues: List[QualityIssueType],
        context: Dict
    ) -> Dict[str, Any]:
        """
        Genera suggerimenti specifici di miglioramento usando AI
        """
        
        data_sample = self._extract_data_sample(asset_data, max_length=300)
        issues_str = ", ".join([issue.value for issue in quality_issues])
        
        prompt = f"""You are a business consultant providing specific improvement suggestions for a {asset_type}.

CURRENT ISSUES: {issues_str}
PROJECT CONTEXT: {context.get('workspace_goal', '')}
ASSET SAMPLE: {data_sample}

Generate 3-5 specific, actionable improvement suggestions that will:
1. Address the identified quality issues
2. Make the asset more business-ready and actionable
3. Provide concrete next steps

Respond in this exact JSON format:
{{
    "suggestions": [
        "Specific improvement suggestion 1",
        "Specific improvement suggestion 2", 
        "Specific improvement suggestion 3"
    ],
    "priority_order": ["most", "important", "improvements", "first"],
    "implementation_difficulty": "easy|medium|hard"
}}"""

        return await self._call_openai_api(prompt, "improvement_suggestions")
    
    async def _call_openai_api(self, prompt: str, operation_type: str) -> Dict[str, Any]:
        """
        Effettua chiamata OpenAI con gestione errori, retry e tracking costi
        """
        
        if not self.openai_available or not self.openai_client:
            raise Exception("OpenAI client not available")
        
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                # Prova con il modello principale
                model_to_use = self.model_config["primary_model"]
                
                logger.debug(f"🤖 AI CALL: {operation_type} with {model_to_use} (attempt {attempt + 1})")
                
                response = await asyncio.wait_for(
                    self.openai_client.chat.completions.create(
                        model=model_to_use,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a professional business data quality analyst. Always respond with valid JSON in the exact format requested."
                            },
                            {
                                "role": "user", 
                                "content": prompt
                            }
                        ],
                        max_tokens=self.model_config["max_tokens"],
                        temperature=self.model_config["temperature"],
                        response_format={"type": "json_object"}  # Force JSON response
                    ),
                    timeout=self.model_config["timeout"]
                )
                
                # Estrai e valida la risposta
                content = response.choices[0].message.content
                result_data = json.loads(content)
                
                # Calcola costi
                usage = response.usage
                input_tokens = usage.prompt_tokens
                output_tokens = usage.completion_tokens
                total_tokens = usage.total_tokens
                
                costs = self.token_costs.get(model_to_use, self.token_costs["gpt-3.5-turbo"])
                cost = (input_tokens * costs["input"] / 1000) + (output_tokens * costs["output"] / 1000)
                
                logger.debug(f"✅ AI SUCCESS: {operation_type} - Tokens: {total_tokens}, Cost: ${cost:.6f}")
                
                # Aggiungi metadati alla risposta
                if "score" in result_data:
                    # Per assessment calls
                    return {
                        "score": float(result_data.get("score", 0.0)),
                        "reasoning": result_data.get("reasoning", ""),
                        "model": model_to_use,
                        "tokens": total_tokens,
                        "cost": cost,
                        "raw_response": result_data
                    }
                else:
                    # Per suggestion calls
                    return {
                        "suggestions": result_data.get("suggestions", []),
                        "model": model_to_use,
                        "tokens": total_tokens,
                        "cost": cost,
                        "raw_response": result_data
                    }
                
            except asyncio.TimeoutError:
                logger.warning(f"⏰ AI TIMEOUT: {operation_type} attempt {attempt + 1}")
                if attempt == max_retries - 1:
                    raise Exception(f"AI call timed out after {max_retries} attempts")
                    
            except json.JSONDecodeError as e:
                logger.warning(f"📝 JSON PARSE ERROR: {operation_type} - {e}")
                if attempt == max_retries - 1:
                    raise Exception(f"Invalid JSON response from AI: {e}")
                    
            except openai.RateLimitError:
                delay = base_delay * (2 ** attempt)
                logger.warning(f"🚫 RATE LIMIT: {operation_type}, waiting {delay}s")
                await asyncio.sleep(delay)
                if attempt == max_retries - 1:
                    raise Exception("Rate limit exceeded")
                    
            except openai.APIError as e:
                logger.warning(f"🔥 API ERROR: {operation_type} - {e}")
                # Try fallback model on API errors
                if attempt == 0 and model_to_use == self.model_config["primary_model"]:
                    self.model_config["primary_model"] = self.model_config["fallback_model"]
                    continue
                if attempt == max_retries - 1:
                    raise Exception(f"API error: {e}")
                    
            except Exception as e:
                logger.warning(f"❌ UNEXPECTED ERROR: {operation_type} - {e}")
                if attempt == max_retries - 1:
                    raise Exception(f"Unexpected error in AI call: {e}")
            
            # Delay before retry
            if attempt < max_retries - 1:
                await asyncio.sleep(base_delay * (attempt + 1))
        
        raise Exception(f"AI call failed after {max_retries} attempts")
    
    # === FALLBACK METHODS (Rule-based quando AI non disponibile) ===
    
    def _assess_content_authenticity_fallback(self, asset_data: Dict, context: Dict) -> float:
        """Fallback rule-based per authenticity assessment"""
        
        score = 0.7  # Base score
        
        # Penalità per fake content
        fake_report = self._detect_fake_content(asset_data)
        if fake_report["has_fake_content"]:
            score -= fake_report["fake_score"] * 0.5
        
        # Penalità per placeholder
        placeholder_report = self._detect_placeholders(asset_data)
        if placeholder_report["has_placeholders"]:
            score -= placeholder_report["placeholder_score"] * 0.3
        
        # Bonus per dati specifici
        data_str = json.dumps(asset_data, default=str).lower()
        if any(indicator in data_str for indicator in ["€", "$", "%", "http", "@", "+"]):
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _assess_actionability_fallback(self, asset_data: Dict, asset_type: str) -> float:
        """Fallback rule-based per actionability assessment"""
        
        score = 0.6  # Base score
        
        # Analisi struttura
        field_count = self._count_populated_fields(asset_data)
        if field_count > 10:
            score += 0.2
        elif field_count < 5:
            score -= 0.2
        
        # Bonus per asset type specifici
        data_str = json.dumps(asset_data, default=str).lower()
        
        if asset_type == "contact_database":
            if any(field in data_str for field in ["email", "phone", "company", "name"]):
                score += 0.2
        elif asset_type == "content_calendar":
            if any(field in data_str for field in ["date", "post", "caption", "hashtag"]):
                score += 0.2
        
        return max(0.0, min(1.0, score))
    
    def _assess_completeness_fallback(self, asset_data: Dict, asset_type: str) -> float:
        """Fallback rule-based per completeness assessment"""
        
        field_count = self._count_populated_fields(asset_data)
        data_depth = self._calculate_data_depth(asset_data)
        
        # Score basato su densità dati
        if field_count >= 15 and data_depth >= 2:
            return 0.9
        elif field_count >= 10 and data_depth >= 2:
            return 0.7
        elif field_count >= 5:
            return 0.5
        else:
            return 0.3
    
    def _generate_improvement_suggestions_fallback(
        self, 
        asset_type: str, 
        quality_issues: List[QualityIssueType]
    ) -> List[str]:
        """Fallback rule-based per improvement suggestions"""
        
        suggestions = []
        
        if QualityIssueType.FAKE_CONTENT in quality_issues:
            suggestions.append(f"Replace fake/example data with real {asset_type} data based on actual research")
        
        if QualityIssueType.PLACEHOLDER_DATA in quality_issues:
            suggestions.append("Fill in all placeholder fields with specific, actionable content")
        
        if QualityIssueType.GENERIC_STRUCTURE in quality_issues:
            suggestions.append(f"Restructure asset to follow {asset_type} industry standards")
        
        if QualityIssueType.NON_ACTIONABLE in quality_issues:
            suggestions.append("Add specific implementation steps and clear action items")
        
        if QualityIssueType.INCOMPLETE_DATA in quality_issues:
            suggestions.append("Complete all missing data fields and sections")
        
        # Asset-specific suggestions
        if asset_type == "contact_database":
            suggestions.append("Ensure all contacts have complete information (name, email, phone, company)")
        elif asset_type == "content_calendar":
            suggestions.append("Add specific posting dates, captions, and hashtags for each content piece")
        
        return suggestions[:5]
    
    # === DETECTION METHODS (Sempre rule-based per affidabilità) ===
    
    def _detect_fake_content(self, asset_data: Dict) -> Dict[str, Any]:
        """Rileva contenuto fake usando pattern matching"""
        
        data_str = json.dumps(asset_data, default=str).lower()
        
        fake_indicators = []
        
        # Pattern matching per contenuto fake comune
        for pattern in self.fake_content_patterns:
            matches = re.findall(pattern, data_str, re.IGNORECASE)
            if matches:
                fake_indicators.append(f"Found fake pattern: {pattern} ({len(matches)} times)")
        
        # Rileva email fake
        fake_emails = re.findall(
            r'\b[a-zA-Z0-9._%+-]+@(?:example|test|fake|dummy|placeholder|domain)\.[a-zA-Z]{2,}\b', 
            data_str
        )
        if fake_emails:
            fake_indicators.append(f"Fake emails detected: {len(fake_emails)}")
        
        # Rileva numeri di telefono fake
        fake_phones = re.findall(r'\b(?:555-?|123-?|000-?|111-?)\d{3,4}\b', data_str)
        if fake_phones:
            fake_indicators.append(f"Fake phone numbers: {len(fake_phones)}")
        
        # Rileva indirizzi fake
        fake_addresses = re.findall(
            r'\b(?:123 main st|fake street|example ave|test road|via roma 1|corso italia)\b', 
            data_str, re.IGNORECASE
        )
        if fake_addresses:
            fake_indicators.append(f"Fake addresses: {len(fake_addresses)}")
        
        return {
            "has_fake_content": len(fake_indicators) > 0,
            "fake_score": min(len(fake_indicators) * 0.2, 1.0),
            "details": "; ".join(fake_indicators) if fake_indicators else "No fake content detected"
        }
    
    def _detect_placeholders(self, asset_data: Dict) -> Dict[str, Any]:
        """Rileva placeholder e contenuto incompleto"""
        
        data_str = json.dumps(asset_data, default=str).lower()
        
        placeholder_patterns = [
            r'\[.*?\]',  # [placeholder]
            r'\{.*?\}',  # {placeholder}
            r'<.*?>',    # <placeholder>
            r'your\s+(?:company|name|email|website)',
            r'insert\s+(?:here|your|data)',
            r'add\s+(?:your|data|information)',
            r'customize\s+(?:this|here)',
            r'fill\s+(?:in|out|this)',
            r'replace\s+(?:with|this)',
            r'esempio\s+(?:di|azienda|nome)',  # Italian placeholders
            r'inserire\s+(?:qui|dati)'
        ]
        
        placeholder_indicators = []
        
        for pattern in placeholder_patterns:
            matches = re.findall(pattern, data_str, re.IGNORECASE)
            if matches:
                placeholder_indicators.append(f"Placeholder pattern: {pattern} ({len(matches)} times)")
        
        # Rileva valori generici
        generic_values = [
            "string", "number", "date", "email", "phone", "url", "address",
            "name", "title", "description", "value", "amount", "quantity",
            "stringa", "numero", "data", "valore"  # Italian generics
        ]
        
        for value in generic_values:
            if f'"{value}"' in data_str or f"'{value}'" in data_str:
                placeholder_indicators.append(f"Generic value used as data: {value}")
        
        return {
            "has_placeholders": len(placeholder_indicators) > 0,
            "placeholder_score": min(len(placeholder_indicators) * 0.15, 1.0),
            "details": "; ".join(placeholder_indicators) if placeholder_indicators else "No placeholders detected"
        }
    
    async def _is_generic_structure(self, asset_data: Dict, asset_type: str) -> bool:
        """Determina se l'asset ha una struttura generica"""
        
        # Rileva se l'asset ha una struttura troppo generica
        generic_indicators = [
            "task_summary" in asset_data,
            "task_metadata" in asset_data,
            "unparsed_json" in asset_data,
            "error" in asset_data,
            len(asset_data) < 3,
            all(isinstance(v, str) and len(str(v)) < 50 for v in asset_data.values() if v),
            "original_error" in str(asset_data).lower(),
            "original_output" in str(asset_data).lower()
        ]
        
        generic_score = sum(generic_indicators) / len(generic_indicators)
        return generic_score > 0.4
    
    def _determine_enhancement_priority(
        self, 
        overall_score: float, 
        quality_issues: List[QualityIssueType],
        context: Dict
    ) -> str:
        """Determina la priorità di enhancement"""
        
        # Priorità basata su score
        if overall_score < 0.3:
            return "critical"
        elif overall_score < 0.5:
            return "high"
        elif overall_score < 0.7:
            return "medium"
        
        # Aumenta priorità per issue critici
        critical_issues = [
            QualityIssueType.FAKE_CONTENT,
            QualityIssueType.PLACEHOLDER_DATA,
            QualityIssueType.NON_ACTIONABLE
        ]
        
        if any(issue in quality_issues for issue in critical_issues):
            return "high"
        
        return "low"
    
    # === UTILITY METHODS ===
    
    def _extract_data_sample(self, asset_data: Dict, max_length: int = 500) -> str:
        """Estrae un campione rappresentativo dei dati per l'analisi AI"""
        
        sample_data = {}
        
        # Estrai campi più significativi
        for key, value in asset_data.items():
            if key in ["task_metadata", "task_summary", "error", "original_error"]:
                continue  # Skip metadati generici
                
            if isinstance(value, (str, int, float)):
                sample_data[key] = value
            elif isinstance(value, dict):
                sample_data[key] = {k: v for k, v in list(value.items())[:3]}
            elif isinstance(value, list):
                sample_data[key] = value[:3] if value else []
        
        sample_str = json.dumps(sample_data, indent=2, default=str, ensure_ascii=False)
        
        if len(sample_str) > max_length:
            sample_str = sample_str[:max_length] + "..."
        
        return sample_str
    
    def _count_populated_fields(self, data: Dict, max_depth: int = 3, current_depth: int = 0) -> int:
        """Conta i campi popolati nell'asset"""
        
        if current_depth > max_depth:
            return 0
        
        count = 0
        for key, value in data.items():
            if value is not None and value != "" and value != []:
                count += 1
                if isinstance(value, dict):
                    count += self._count_populated_fields(value, max_depth, current_depth + 1)
                elif isinstance(value, list) and value:
                    count += len([item for item in value if item is not None and item != ""])
        
        return count
    
    def _calculate_data_depth(self, data: Dict, current_depth: int = 0) -> int:
        """Calcola la profondità della struttura dati"""
        
        if current_depth > 5:  # Limite ricorsione
            return current_depth
        
        max_depth = current_depth
        
        for value in data.values():
            if isinstance(value, dict):
                depth = self._calculate_data_depth(value, current_depth + 1)
                max_depth = max(max_depth, depth)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                depth = self._calculate_data_depth(value[0], current_depth + 1)
                max_depth = max(max_depth, depth)
        
        return max_depth
    
    # === STATS AND MONITORING ===
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Ottiene statistiche delle validazioni"""
        
        return {
            "total_validations": self.validation_count,
            "total_tokens_used": self.total_tokens_used,
            "total_cost": round(self.total_cost, 6),
            "average_cost_per_validation": round(self.total_cost / max(self.validation_count, 1), 6),
            "ai_available": self.openai_available,
            "primary_model": self.model_config["primary_model"],
            "fallback_model": self.model_config["fallback_model"]
        }
    
    def reset_stats(self):
        """Reset delle statistiche"""
        self.validation_count = 0
        self.total_tokens_used = 0
        self.total_cost = 0.0
        logger.info("Quality validator stats reset")