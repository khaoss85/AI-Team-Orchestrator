# backend/ai_quality_assurance/ai_evaluator.py

import logging
import json
import re
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from backend.ai_quality_assurance.quality_validator import AIQualityValidator

logger = logging.getLogger(__name__)

# Import per LLM calls - adatta in base al tuo setup
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available - quality evaluation will use fallback logic")

class AIQualityEvaluator:
    """
    Evaluatore AI che usa prompt specifici per valutare la qualità degli output
    Sostituisce la logica hardcoded con valutazione AI flessibile
    """
    
    def __init__(self):
        if OPENAI_AVAILABLE:
            self.client = AsyncOpenAI()
        self.model = "gpt-4.1"  # Aggiornato al nuovo modello GPT-4.1
        
        # Fallback patterns per quando AI non è disponibile
        self.fallback_fake_patterns = [
            r"john\s+doe", r"jane\s+smith", r"example\.com", r"test@", 
            r"555[-\s]?\d{3}[-\s]?\d{4}", r"lorem\s+ipsum", r"placeholder",
            r"sample\s+data", r"xxx+", r"tbd", r"to\s+be\s+determined"
        ]
    
    async def evaluate_content_authenticity(
        self, 
        content: str, 
        context: Dict[str, Any]
    ) -> Tuple[float, str]:
        """
        Evalua l'autenticità del contenuto usando AI
        Returns: (score 0.0-1.0, reasoning)
        """
        
        if OPENAI_AVAILABLE:
            return await self._ai_evaluate_authenticity(content, context)
        else:
            return self._fallback_evaluate_authenticity(content)
    
    async def evaluate_actionability(
        self, 
        content: str, 
        asset_type: str,
        context: Dict[str, Any]
    ) -> Tuple[float, str]:
        """
        Evalua quanto l'asset sia azionabile usando AI
        Returns: (score 0.0-1.0, reasoning)
        """
        
        if OPENAI_AVAILABLE:
            return await self._ai_evaluate_actionability(content, asset_type, context)
        else:
            return self._fallback_evaluate_actionability(content, asset_type)
    
    async def detect_fake_content_with_ai(self, content: str) -> Dict[str, Any]:
        """
        Rileva contenuto fake usando AI invece di pattern fissi
        """
        
        if OPENAI_AVAILABLE:
            return await self._ai_detect_fake_content(content)
        else:
            return self._fallback_detect_fake_content(content)
    
    async def suggest_specific_improvements(
        self,
        content: str,
        asset_type: str,
        identified_issues: List[str],
        context: Dict[str, Any]
    ) -> List[str]:
        """
        Genera suggerimenti specifici usando AI
        """
        
        if OPENAI_AVAILABLE:
            return await self._ai_suggest_improvements(content, asset_type, identified_issues, context)
        else:
            return self._fallback_suggest_improvements(asset_type, identified_issues)
    
    # === AI-POWERED EVALUATION METHODS ===
    
    async def _ai_evaluate_authenticity(self, content: str, context: Dict) -> Tuple[float, str]:
        """
        Usa AI per valutare l'autenticità del contenuto
        """
        
        try:
            project_goal = context.get("workspace_goal", "")
            content_sample = content[:2000]  # Limita per token
            
            prompt = f"""You are an expert business analyst evaluating the authenticity of business deliverable content.

PROJECT CONTEXT: {project_goal}

CONTENT TO EVALUATE:
{content_sample}

EVALUATION CRITERIA:
Assess the authenticity of this business content on a scale of 0.0 to 1.0 where:
- 1.0 = Completely authentic, real business data with specific facts, numbers, names, dates
- 0.8 = Mostly authentic with minor generic elements
- 0.6 = Mix of real and generic content
- 0.4 = Mostly generic with some realistic elements  
- 0.2 = Heavily generic/template content
- 0.0 = Completely fake/placeholder content

Look for these POSITIVE indicators:
- Specific company names, real people, actual addresses
- Concrete numbers, dates, metrics from real research
- Industry-specific terminology and insights
- Realistic business scenarios and outcomes
- Actionable data that could be immediately implemented

Look for these NEGATIVE indicators:
- Placeholder names like "John Doe", "ABC Company", "Your Company"
- Generic emails like "info@example.com" or fake phone numbers
- Template language or Lorem ipsum text
- Vague metrics without specific sources
- Obviously fictional or example data

Respond with exactly this format:
SCORE: [0.0-1.0]
REASONING: [Brief explanation of why this score was assigned]
SPECIFIC_ISSUES: [List any fake/placeholder content found]
AUTHENTIC_ELEMENTS: [List any real/specific content found]"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )
            
            result = response.choices[0].message.content
            return self._parse_ai_evaluation_response(result)
            
        except Exception as e:
            logger.error(f"AI authenticity evaluation failed: {e}")
            return self._fallback_evaluate_authenticity(content)
    
    async def _ai_evaluate_actionability(self, content: str, asset_type: str, context: Dict) -> Tuple[float, str]:
        """
        Usa AI per valutare l'azionabilità
        """
        
        try:
            project_goal = context.get("workspace_goal", "")
            content_sample = content[:2000]
            
            prompt = f"""You are an expert business consultant evaluating the immediate actionability of a {asset_type} deliverable.

PROJECT CONTEXT: {project_goal}

{asset_type.upper()} CONTENT TO EVALUATE:
{content_sample}

ACTIONABILITY EVALUATION:
Rate how immediately actionable this {asset_type} is on a scale of 0.0 to 1.0 where:
- 1.0 = Completely ready to implement immediately without any modifications
- 0.8 = Ready to use with minimal customization (< 30 minutes)
- 0.6 = Needs moderate customization but structure is solid
- 0.4 = Requires significant work to make business-ready
- 0.2 = More of a template/framework than actionable content
- 0.0 = Not actionable, just conceptual or incomplete

For a high-quality {asset_type}, look for:
- Specific, implementable steps or data
- Clear instructions that can be followed immediately
- Complete information without gaps or "TBD" sections
- Realistic timelines and resource requirements
- Measurable success criteria
- Professional formatting ready for business use

Red flags that reduce actionability:
- Missing critical information or steps
- Vague instructions or placeholder content
- Incomplete sections requiring research
- Generic advice without specific application
- No clear next steps or implementation guidance

Respond with exactly this format:
SCORE: [0.0-1.0]
REASONING: [Why this score for actionability]
IMMEDIATE_ACTIONS: [What can be done right now with this asset]
MISSING_ELEMENTS: [What's needed to make it fully actionable]"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )
            
            result = response.choices[0].message.content
            return self._parse_ai_evaluation_response(result)
            
        except Exception as e:
            logger.error(f"AI actionability evaluation failed: {e}")
            return self._fallback_evaluate_actionability(content, asset_type)
    
    async def _ai_detect_fake_content(self, content: str) -> Dict[str, Any]:
        """
        Usa AI per rilevare contenuto fake/placeholder
        """
        
        try:
            content_sample = content[:1500]
            
            prompt = f"""You are a content authenticity detector. Analyze this business content for fake, placeholder, or example data.

CONTENT TO ANALYZE:
{content_sample}

DETECTION TASK:
Identify all instances of fake, placeholder, or example content including:

1. FAKE PERSONAL DATA:
   - Example names (John Doe, Jane Smith, etc.)
   - Fake email addresses (using example.com, test domains)
   - Placeholder phone numbers (555-xxxx, 123-456-7890)
   - Generic addresses (123 Main St, etc.)

2. PLACEHOLDER TEXT:
   - Lorem ipsum or template text
   - Brackets like [Your Company], [Insert Name]
   - "TBD", "To Be Determined", "Coming Soon"
   - "Sample", "Example", "Template" content

3. GENERIC BUSINESS DATA:
   - Unrealistic perfect numbers (exactly 100%, round numbers)
   - Generic company names (ABC Corp, XYZ Inc)
   - Template metrics without sources
   - Copy-paste content from examples

4. STRUCTURAL PLACEHOLDERS:
   - Empty sections marked for completion
   - Instruction text meant for the creator
   - Obvious copy-paste from templates

Respond with exactly this format:
HAS_FAKE_CONTENT: [true/false]
FAKE_CONFIDENCE: [0.0-1.0 confidence that fake content exists]
FAKE_ITEMS: [List each fake/placeholder item found]
AUTHENTIC_RATIO: [Percentage of content that appears authentic]
SEVERITY: [low/medium/high - how much fake content affects usability]"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=400
            )
            
            result = response.choices[0].message.content
            return self._parse_fake_detection_response(result)
            
        except Exception as e:
            logger.error(f"AI fake detection failed: {e}")
            return self._fallback_detect_fake_content(content)
    
    async def _ai_suggest_improvements(
        self, 
        content: str, 
        asset_type: str, 
        issues: List[str], 
        context: Dict
    ) -> List[str]:
        """
        Genera suggerimenti specifici usando AI
        """
        
        try:
            project_goal = context.get("workspace_goal", "")
            content_sample = content[:1500]
            issues_str = ", ".join(issues)
            
            prompt = f"""You are a business deliverable improvement consultant. Given a {asset_type} with quality issues, provide specific, actionable improvement suggestions.

PROJECT CONTEXT: {project_goal}

CURRENT {asset_type.upper()} CONTENT:
{content_sample}

IDENTIFIED QUALITY ISSUES: {issues_str}

IMPROVEMENT TASK:
Generate 3-5 specific, actionable suggestions to transform this into a high-quality, immediately usable {asset_type}. Focus on:

1. REPLACING FAKE/PLACEHOLDER CONTENT:
   - What specific research needs to be done
   - What real data sources to use
   - How to gather authentic information

2. IMPROVING ACTIONABILITY:
   - What missing steps or information to add
   - How to make instructions more specific
   - What success criteria to include

3. ENHANCING PROFESSIONAL QUALITY:
   - Formatting improvements
   - Structure enhancements
   - Professional presentation tips

Make each suggestion:
- Specific and implementable
- Focused on the identified issues
- Realistic given the project context
- Oriented toward immediate business use

Respond with exactly this format:
SUGGESTION_1: [Specific actionable improvement]
SUGGESTION_2: [Specific actionable improvement]  
SUGGESTION_3: [Specific actionable improvement]
SUGGESTION_4: [Specific actionable improvement]
SUGGESTION_5: [Specific actionable improvement]"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=600
            )
            
            result = response.choices[0].message.content
            return self._parse_suggestions_response(result)
            
        except Exception as e:
            logger.error(f"AI suggestions failed: {e}")
            return self._fallback_suggest_improvements(asset_type, issues)
    
    # === RESPONSE PARSING METHODS ===
    
    def _parse_ai_evaluation_response(self, response: str) -> Tuple[float, str]:
        """Parse AI evaluation response"""
        
        try:
            lines = response.strip().split('\n')
            score = 0.5  # default
            reasoning = "AI evaluation parsing failed"
            
            for line in lines:
                if line.startswith('SCORE:'):
                    score_str = line.replace('SCORE:', '').strip()
                    score = float(score_str)
                elif line.startswith('REASONING:'):
                    reasoning = line.replace('REASONING:', '').strip()
            
            return score, reasoning
            
        except Exception as e:
            logger.error(f"Error parsing AI evaluation: {e}")
            return 0.5, f"Parsing error: {str(e)}"
    
    def _parse_fake_detection_response(self, response: str) -> Dict[str, Any]:
        """Parse fake content detection response"""
        
        try:
            lines = response.strip().split('\n')
            result = {
                "has_fake_content": True,
                "fake_confidence": 0.5,
                "fake_items": [],
                "authentic_ratio": 0.5,
                "severity": "medium"
            }
            
            for line in lines:
                if line.startswith('HAS_FAKE_CONTENT:'):
                    result["has_fake_content"] = 'true' in line.lower()
                elif line.startswith('FAKE_CONFIDENCE:'):
                    conf_str = line.replace('FAKE_CONFIDENCE:', '').strip()
                    result["fake_confidence"] = float(conf_str)
                elif line.startswith('FAKE_ITEMS:'):
                    items_str = line.replace('FAKE_ITEMS:', '').strip()
                    result["fake_items"] = [item.strip() for item in items_str.split(',') if item.strip()]
                elif line.startswith('AUTHENTIC_RATIO:'):
                    ratio_str = line.replace('AUTHENTIC_RATIO:', '').strip().replace('%', '')
                    result["authentic_ratio"] = float(ratio_str) / 100 if ratio_str.isdigit() else 0.5
                elif line.startswith('SEVERITY:'):
                    result["severity"] = line.replace('SEVERITY:', '').strip().lower()
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing fake detection: {e}")
            return {"has_fake_content": True, "fake_confidence": 0.5, "fake_items": ["parsing_error"], "authentic_ratio": 0.5, "severity": "medium"}
    
    def _parse_suggestions_response(self, response: str) -> List[str]:
        """Parse improvement suggestions response"""
        
        try:
            lines = response.strip().split('\n')
            suggestions = []
            
            for line in lines:
                if line.startswith('SUGGESTION_'):
                    suggestion = line.split(':', 1)[1].strip() if ':' in line else line.strip()
                    if suggestion:
                        suggestions.append(suggestion)
            
            return suggestions if suggestions else ["AI suggestion parsing failed - manual review recommended"]
            
        except Exception as e:
            logger.error(f"Error parsing suggestions: {e}")
            return [f"Suggestion parsing error: {str(e)}"]
    
    # === FALLBACK METHODS (quando AI non è disponibile) ===
    
    def _fallback_evaluate_authenticity(self, content: str) -> Tuple[float, str]:
        """Fallback authenticity evaluation using pattern matching"""
        
        content_lower = content.lower()
        fake_count = 0
        total_patterns = len(self.fallback_fake_patterns)
        
        for pattern in self.fallback_fake_patterns:
            if re.search(pattern, content_lower):
                fake_count += 1
        
        # Inverse score: more fake patterns = lower authenticity
        authenticity_score = max(0.0, 1.0 - (fake_count / total_patterns * 2))
        
        reasoning = f"Pattern-based evaluation: {fake_count}/{total_patterns} fake patterns detected"
        
        return authenticity_score, reasoning
    
    def _fallback_evaluate_actionability(self, content: str, asset_type: str) -> Tuple[float, str]:
        """Fallback actionability evaluation"""
        
        # Basic heuristics
        content_lower = content.lower()
        actionability_indicators = [
            "specific" in content_lower,
            "step" in content_lower or "action" in content_lower,
            len(content) > 500,  # Substantial content
            "@" in content or "http" in content,  # Contact info or links
            any(char.isdigit() for char in content)  # Contains numbers/metrics
        ]
        
        score = sum(actionability_indicators) / len(actionability_indicators)
        reasoning = f"Heuristic evaluation: {sum(actionability_indicators)}/{len(actionability_indicators)} actionability indicators present"
        
        return score, reasoning
    
    def _fallback_detect_fake_content(self, content: str) -> Dict[str, Any]:
        """Fallback fake content detection"""
        
        content_lower = content.lower()
        fake_items = []
        
        for pattern in self.fallback_fake_patterns:
            matches = re.findall(pattern, content_lower)
            if matches:
                fake_items.extend([f"Pattern '{pattern}': {len(matches)} matches" for _ in matches[:2]])
        
        return {
            "has_fake_content": len(fake_items) > 0,
            "fake_confidence": min(len(fake_items) * 0.2, 1.0),
            "fake_items": fake_items[:5],  # Limit to 5 items
            "authentic_ratio": max(0.0, 1.0 - len(fake_items) * 0.15),
            "severity": "high" if len(fake_items) > 3 else "medium" if len(fake_items) > 1 else "low"
        }
    
    def _fallback_suggest_improvements(self, asset_type: str, issues: List[str]) -> List[str]:
        """Fallback improvement suggestions"""
        
        suggestions = [
            f"Conduct specific research to gather real data for {asset_type}",
            "Replace all placeholder content with authentic business information",
            "Add specific implementation steps and success criteria",
            "Include concrete examples and measurable outcomes",
            "Ensure professional formatting and presentation"
        ]
        
        # Customize based on issues
        if "fake_content" in str(issues).lower():
            suggestions.insert(0, "Priority: Replace all fake/example data with real business information")
        
        if "actionability" in str(issues).lower():
            suggestions.insert(1, "Add specific, step-by-step implementation instructions")
        
        return suggestions[:5]


# === INTEGRATION WITH EXISTING QUALITY VALIDATOR ===

# Modifica alla classe AIQualityValidator esistente per usare AI evaluator
class EnhancedAIQualityValidator(AIQualityValidator):
    """
    Enhanced version che usa AI evaluator invece di logica hardcoded
    """
    
    def __init__(self):
        super().__init__()
        self.ai_evaluator = AIQualityEvaluator()
    
    async def _assess_content_authenticity(self, asset_data: Dict, context: Dict) -> float:
        """Override per usare AI evaluation"""
        
        data_sample = self._extract_data_sample(asset_data)
        score, reasoning = await self.ai_evaluator.evaluate_content_authenticity(data_sample, context)
        
        logger.info(f"AI Authenticity Assessment: {score:.2f} - {reasoning}")
        return score
    
    async def _assess_actionability(self, asset_data: Dict, asset_type: str, context: Dict) -> float:
        """Override per usare AI evaluation"""
        
        data_sample = self._extract_data_sample(asset_data)
        score, reasoning = await self.ai_evaluator.evaluate_actionability(data_sample, asset_type, context)
        
        logger.info(f"AI Actionability Assessment: {score:.2f} - {reasoning}")
        return score
    
    def _detect_fake_content(self, asset_data: Dict) -> Dict[str, Any]:
        """Override per usare AI detection"""
        
        data_sample = self._extract_data_sample(asset_data)
        
        # Usa async in modo sicuro
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            fake_report = loop.run_until_complete(
                self.ai_evaluator.detect_fake_content_with_ai(data_sample)
            )
        except:
            # Fallback se problemi con async
            fake_report = super()._detect_fake_content(asset_data)
        
        return {
            "has_fake_content": fake_report.get("has_fake_content", False),
            "fake_score": fake_report.get("fake_confidence", 0.0),
            "details": f"AI Detection: {len(fake_report.get('fake_items', []))} fake items found. Severity: {fake_report.get('severity', 'unknown')}"
        }
    
    async def _generate_improvement_suggestions(
        self,
        asset_data: Dict,
        asset_type: str,
        quality_issues: List,
        context: Dict
    ) -> List[str]:
        """Override per usare AI suggestions"""
        
        data_sample = self._extract_data_sample(asset_data)
        issue_names = [issue.value if hasattr(issue, 'value') else str(issue) for issue in quality_issues]
        
        ai_suggestions = await self.ai_evaluator.suggest_specific_improvements(
            data_sample, asset_type, issue_names, context
        )
        
        # Combina con suggerimenti base
        base_suggestions = await super()._generate_improvement_suggestions(asset_data, asset_type, quality_issues, context)
        
        # Unisci e dedup
        all_suggestions = ai_suggestions + base_suggestions
        unique_suggestions = []
        for suggestion in all_suggestions:
            if suggestion not in unique_suggestions:
                unique_suggestions.append(suggestion)
        
        return unique_suggestions[:5]  # Limita a 5