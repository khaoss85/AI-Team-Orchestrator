"""
🤖 Memory-Enhanced AI Asset Generator
Generates real business content using tool results, learned patterns, and memory system

Pillar 3: Real Tool Usage - Uses WebSearch and other tools for current data
Pillar 8: No Hardcode - 100% AI-driven content generation, no templates
Pillar 11: Self-Enhancement - Learns from successful patterns and improves
Pillar 12: Course Correction - Auto-detects and corrects content quality issues
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ContentQuality(Enum):
    """Quality levels for generated content"""
    EXCELLENT = "excellent"  # Business-ready, highly specific
    GOOD = "good"  # Useful but may need minor refinement
    ACCEPTABLE = "acceptable"  # Basic content that meets requirements
    POOR = "poor"  # Generic or incomplete content
    FAILED = "failed"  # Generation failed

@dataclass
class AssetGenerationResult:
    """Result of asset generation process"""
    generated_content: Dict[str, Any]
    content_quality: ContentQuality
    business_specificity_score: float  # 0-100
    tool_integration_score: float  # 0-100
    memory_enhancement_score: float  # 0-100
    generation_reasoning: str
    source_tools_used: List[str]
    memory_patterns_applied: List[str]
    auto_improvements: List[str]
    confidence: float  # 0-100

@dataclass
class MemoryPattern:
    """Learned pattern from successful content generation"""
    pattern_id: str
    content_type: str
    business_context: str
    successful_approach: Dict[str, Any]
    quality_indicators: List[str]
    tool_sequence: List[str]
    created_at: datetime
    success_rate: float
    usage_count: int

class MemoryEnhancedAIAssetGenerator:
    """
    🤖 AI-Driven Asset Generator with Memory and Tool Integration
    Generates real business content by combining tool results and learned patterns
    """
    
    def __init__(self):
        self.memory_patterns = []
        self.generation_history = []
        self.tool_orchestrator = None
        self._initialize_components()
        
    def _initialize_components(self):
        """Initialize components and import dependencies"""
        try:
            # Import AI Tool Orchestrator
            from services.ai_tool_orchestrator import ai_tool_orchestrator
            self.tool_orchestrator = ai_tool_orchestrator
            logger.info("✅ Tool orchestrator integrated successfully")
        except ImportError:
            logger.warning("⚠️ Tool orchestrator not available, will use fallback")
            
    async def generate_real_business_asset(
        self,
        asset_type: str,
        business_context: Dict[str, Any],
        task_results: List[Dict[str, Any]] = None,
        goal_context: str = "",
        required_tools: List[str] = None
    ) -> AssetGenerationResult:
        """
        🤖 AI-DRIVEN: Generate real business asset with tool integration and memory
        
        Args:
            asset_type: Type of asset to generate (e.g., "email_sequences")
            business_context: Business context for personalization
            task_results: Existing task results to build upon
            goal_context: Goal context for content direction  
            required_tools: Tools that should be used for data collection
            
        Returns:
            AssetGenerationResult with generated content and quality metrics
        """
        try:
            logger.info(f"🎯 Generating real business asset: {asset_type}")
            
            # Step 1: Retrieve Memory Patterns
            relevant_patterns = await self._retrieve_memory_patterns(
                asset_type, 
                business_context
            )
            
            # Step 2: Determine Required Tools (AI-driven)
            if not required_tools:
                required_tools = await self._ai_determine_required_tools(
                    asset_type, 
                    business_context,
                    goal_context
                )
            
            # Step 3: Execute Tools for Real Data Collection
            tool_results = await self._execute_tools_for_data(
                asset_type,
                business_context,
                required_tools,
                task_results
            )
            
            # Step 4: AI Content Generation with Memory + Tools
            generated_content = await self._ai_generate_content_with_memory_and_tools(
                asset_type,
                business_context,
                tool_results,
                relevant_patterns,
                goal_context
            )
            
            # Step 5: AI Quality Assessment
            quality_assessment = await self._ai_assess_content_quality(
                generated_content,
                asset_type,
                business_context
            )
            
            # Step 6: Auto-Improvements if needed
            auto_improvements = []
            if quality_assessment.get("quality_score", 0) < 80:
                improved_content = await self._ai_auto_improve_content(
                    generated_content,
                    quality_assessment,
                    tool_results
                )
                if improved_content:
                    generated_content = improved_content
                    auto_improvements.append("Applied AI auto-improvements")
            
            # Step 7: Store Pattern for Learning
            if quality_assessment.get("quality_score", 0) >= 70:
                await self._store_successful_pattern(
                    asset_type,
                    business_context,
                    tool_results,
                    generated_content,
                    quality_assessment
                )
            
            # Compile result
            result = AssetGenerationResult(
                generated_content=generated_content,
                content_quality=self._classify_content_quality(quality_assessment.get("quality_score", 0)),
                business_specificity_score=quality_assessment.get("specificity_score", 0),
                tool_integration_score=quality_assessment.get("tool_integration_score", 0),
                memory_enhancement_score=len(relevant_patterns) * 20,  # Simple scoring
                generation_reasoning=quality_assessment.get("reasoning", ""),
                source_tools_used=[r.get("tool", "") for r in tool_results if r.get("success")],
                memory_patterns_applied=[p.pattern_id for p in relevant_patterns],
                auto_improvements=auto_improvements,
                confidence=min(
                    quality_assessment.get("confidence", 0),
                    90 if tool_results else 50  # Higher confidence with tool data
                )
            )
            
            # Store generation for learning
            await self._store_generation_learning(asset_type, result)
            
            logger.info(f"✅ Asset generation complete: Quality={result.content_quality.value}, Score={result.business_specificity_score:.1f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in AI asset generation: {e}")
            return self._create_error_result(str(e))
    
    async def _ai_determine_required_tools(
        self,
        asset_type: str,
        business_context: Dict[str, Any],
        goal_context: str
    ) -> List[str]:
        """
        🤖 AI determines what tools are needed for this asset type
        """
        try:
            import os
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            if not client.api_key:
                return self._fallback_tool_determination(asset_type)
            
            prompt = f"""
Determina quali tools sono necessari per generare questo asset con dati reali.

ASSET TYPE: {asset_type}
BUSINESS CONTEXT: {json.dumps(business_context, indent=2)}
GOAL CONTEXT: {goal_context}

TOOLS DISPONIBILI:
- websearch: Ricerca web per esempi, best practices, dati attuali
- competitor_analysis: Analisi competitor e benchmarking
- content_generator: Generazione contenuti basata su dati raccolti
- data_analyzer: Analisi e insights da dati raccolti

PER ESEMPIO:
- "email_sequences" → websearch per esempi reali + competitor_analysis per best practices
- "lead_list" → websearch per company data + data_analyzer per qualification
- "content_strategy" → websearch per trends + competitor_analysis + data_analyzer

Rispondi in JSON:
{{
    "required_tools": ["tool1", "tool2"],
    "tool_sequence": ["primo", "secondo", "terzo"],
    "data_collection_strategy": "come usare ogni tool",
    "expected_data_types": ["tipo di dato da ogni tool"]
}}
"""
            
            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert tool orchestration planner. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.1
            )
            
            ai_response = response.choices[0].message.content
            
            try:
                result = json.loads(ai_response)
                return result.get("required_tools", ["websearch"])
            except json.JSONDecodeError:
                logger.error(f"Failed to parse tool determination: {ai_response}")
                return self._fallback_tool_determination(asset_type)
                
        except Exception as e:
            logger.error(f"Error in AI tool determination: {e}")
            return self._fallback_tool_determination(asset_type)
    
    async def _execute_tools_for_data(
        self,
        asset_type: str,
        business_context: Dict[str, Any],
        required_tools: List[str],
        existing_task_results: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute tools to collect real data for asset generation
        """
        try:
            if not self.tool_orchestrator:
                return self._fallback_data_collection(asset_type, business_context)
            
            # Build task objective for tool orchestration
            task_objective = f"Collect real data for generating {asset_type} for {business_context.get('company_name', 'business')}"
            
            # Execute tool orchestration
            orchestration_result = await self.tool_orchestrator.orchestrate_tools_for_task(
                task_objective=task_objective,
                required_tools=required_tools,
                business_context=business_context,
                existing_data=self._extract_existing_data(existing_task_results)
            )
            
            # Extract tool results
            tool_results = []
            for tool_result in orchestration_result.tool_results:
                tool_results.append({
                    "tool": tool_result.tool_name,
                    "success": tool_result.status.value == "success",
                    "data": tool_result.data_collected,
                    "quality_score": tool_result.data_quality_score,
                    "confidence": tool_result.confidence
                })
            
            # Include synthesized data
            if orchestration_result.synthesized_data:
                tool_results.append({
                    "tool": "synthesis",
                    "success": True,
                    "data": orchestration_result.synthesized_data,
                    "quality_score": orchestration_result.data_quality_score,
                    "confidence": 80
                })
            
            logger.info(f"🔧 Tool execution complete: {len(tool_results)} results, Success: {orchestration_result.overall_success}")
            
            return tool_results
            
        except Exception as e:
            logger.error(f"Error executing tools for data: {e}")
            return self._fallback_data_collection(asset_type, business_context)
    
    async def _ai_generate_content_with_memory_and_tools(
        self,
        asset_type: str,
        business_context: Dict[str, Any],
        tool_results: List[Dict[str, Any]],
        memory_patterns: List[MemoryPattern],
        goal_context: str
    ) -> Dict[str, Any]:
        """
        🤖 AI content generation using both tool results and memory patterns
        """
        try:
            import os
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            if not client.api_key:
                return self._fallback_content_generation(asset_type, business_context)
            
            # Prepare tool data
            tool_data_summary = []
            for result in tool_results:
                if result.get("success"):
                    tool_data_summary.append({
                        "tool": result["tool"],
                        "data": result["data"],
                        "quality": result.get("quality_score", 0)
                    })
            
            # Prepare memory patterns
            pattern_insights = []
            for pattern in memory_patterns:
                pattern_insights.append({
                    "approach": pattern.successful_approach,
                    "quality_indicators": pattern.quality_indicators,
                    "success_rate": pattern.success_rate
                })
            
            prompt = f"""
Genera {asset_type} business-ready utilizzando dati reali dai tools e pattern di successo.

BUSINESS CONTEXT:
{json.dumps(business_context, indent=2)}

GOAL CONTEXT: {goal_context}

DATI REALI DAI TOOLS:
{json.dumps(tool_data_summary, indent=2, default=str)}

PATTERN DI SUCCESSO (Memory):
{json.dumps(pattern_insights, indent=2, default=str)}

GENERAZIONE RICHIESTA:
1. Usa i dati reali raccolti dai tools (non inventare)
2. Applica i pattern di successo dalla memory
3. Crea contenuto immediatamente utilizzabile
4. Personalizza per il business context specifico
5. NO template generici o placeholder

Per {asset_type}:
- Se "email_sequences": Crea email complete con subject, body, CTA usando dati reali
- Se "lead_list": Genera lista contact qualificati con dati company reali
- Se "content_strategy": Piano strategico basato su competitor analysis reali

Struttura la risposta JSON appropriata per {asset_type}.
"""
            
            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": f"You are an expert {asset_type} creator. Generate real, business-ready content using provided data."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=3000,
                temperature=0.2
            )
            
            ai_response = response.choices[0].message.content
            
            try:
                return json.loads(ai_response)
            except json.JSONDecodeError:
                # Return structured response even if not valid JSON
                return {
                    "generated_content": ai_response,
                    "content_type": asset_type,
                    "generation_method": "ai_text_response",
                    "data_sources": [r["tool"] for r in tool_results if r.get("success")]
                }
                
        except Exception as e:
            logger.error(f"Error in AI content generation: {e}")
            return self._fallback_content_generation(asset_type, business_context)
    
    async def _ai_assess_content_quality(
        self,
        generated_content: Dict[str, Any],
        asset_type: str,
        business_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        🤖 AI assessment of generated content quality
        """
        try:
            import os
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            if not client.api_key:
                return self._fallback_quality_assessment(generated_content)
            
            prompt = f"""
Valuta la qualità di questo contenuto generato.

CONTENT TYPE: {asset_type}
BUSINESS CONTEXT: {json.dumps(business_context, indent=2)}

GENERATED CONTENT:
{json.dumps(generated_content, indent=2, default=str)}

CRITERI DI VALUTAZIONE:
1. BUSINESS SPECIFICITY: È specifico per questo business o generico?
2. TOOL INTEGRATION: Usa dati reali raccolti o è inventato?
3. IMMEDIATE USABILITY: È utilizzabile subito o serve personalizzazione?
4. PROFESSIONAL QUALITY: È professionale e business-ready?

SCORE 0-100 per ogni criterio.

Rispondi in JSON:
{{
    "quality_score": 0-100,
    "specificity_score": 0-100,
    "tool_integration_score": 0-100,
    "usability_score": 0-100,
    "professional_score": 0-100,
    "strengths": ["punto forte 1", "punto forte 2"],
    "weaknesses": ["debolezza 1", "debolezza 2"],
    "improvement_suggestions": ["suggerimento 1"],
    "reasoning": "spiegazione dettagliata",
    "confidence": 0-100
}}
"""
            
            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert content quality assessor. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            ai_response = response.choices[0].message.content
            
            try:
                return json.loads(ai_response)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse quality assessment: {ai_response}")
                return self._fallback_quality_assessment(generated_content)
                
        except Exception as e:
            logger.error(f"Error in AI quality assessment: {e}")
            return self._fallback_quality_assessment(generated_content)
    
    async def _ai_auto_improve_content(
        self,
        content: Dict[str, Any],
        quality_assessment: Dict[str, Any],
        tool_results: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        🤖 AI auto-improvement of content based on quality assessment
        """
        try:
            weaknesses = quality_assessment.get("weaknesses", [])
            suggestions = quality_assessment.get("improvement_suggestions", [])
            
            if not weaknesses and not suggestions:
                return None
            
            import os
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            if not client.api_key:
                return None
            
            prompt = f"""
Migliora questo contenuto basandoti sui problemi identificati.

CONTENUTO CORRENTE:
{json.dumps(content, indent=2, default=str)}

PROBLEMI IDENTIFICATI:
{json.dumps(weaknesses, indent=2)}

SUGGERIMENTI:
{json.dumps(suggestions, indent=2)}

DATI DISPONIBILI:
{json.dumps([r["data"] for r in tool_results if r.get("success")], indent=2, default=str)}

MIGLIORAMENTO RICHIESTO:
1. Fixa i problemi identificati
2. Usa più dati reali disponibili
3. Rendi più specifico e business-ready
4. Mantieni la struttura originale

Restituisci il contenuto migliorato nella stessa struttura JSON.
"""
            
            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert content improver. Enhance content based on feedback."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=3000,
                temperature=0.1
            )
            
            ai_response = response.choices[0].message.content
            
            try:
                return json.loads(ai_response)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse improved content: {ai_response}")
                return None
                
        except Exception as e:
            logger.error(f"Error in AI content improvement: {e}")
            return None
    
    async def _retrieve_memory_patterns(
        self,
        asset_type: str,
        business_context: Dict[str, Any]
    ) -> List[MemoryPattern]:
        """
        Retrieve relevant memory patterns for content generation
        """
        try:
            relevant_patterns = []
            
            # Filter patterns by asset type and business context
            for pattern in self.memory_patterns:
                if pattern.content_type == asset_type:
                    # Simple relevance scoring
                    relevance_score = 0
                    
                    # Business context matching
                    if pattern.business_context:
                        business_keywords = pattern.business_context.lower().split()
                        context_text = json.dumps(business_context, default=str).lower()
                        
                        matches = sum(1 for keyword in business_keywords if keyword in context_text)
                        relevance_score = matches / len(business_keywords) if business_keywords else 0
                    
                    # High success rate patterns get priority
                    if pattern.success_rate >= 0.7:
                        relevance_score += 0.3
                    
                    # Add if relevant enough
                    if relevance_score >= 0.4:
                        relevant_patterns.append(pattern)
            
            # Sort by success rate and usage count
            relevant_patterns.sort(key=lambda p: (p.success_rate, p.usage_count), reverse=True)
            
            # Return top 3 most relevant patterns
            return relevant_patterns[:3]
            
        except Exception as e:
            logger.error(f"Error retrieving memory patterns: {e}")
            return []
    
    async def _store_successful_pattern(
        self,
        asset_type: str,
        business_context: Dict[str, Any],
        tool_results: List[Dict[str, Any]],
        generated_content: Dict[str, Any],
        quality_assessment: Dict[str, Any]
    ):
        """
        Store successful generation pattern for future learning
        """
        try:
            pattern_id = f"{asset_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Extract successful approach
            successful_approach = {
                "tool_sequence": [r["tool"] for r in tool_results if r.get("success")],
                "data_integration_method": "tool_results_and_memory",
                "quality_indicators": quality_assessment.get("strengths", []),
                "generation_parameters": {
                    "business_specificity": quality_assessment.get("specificity_score", 0),
                    "tool_integration": quality_assessment.get("tool_integration_score", 0),
                    "professional_quality": quality_assessment.get("professional_score", 0)
                }
            }
            
            pattern = MemoryPattern(
                pattern_id=pattern_id,
                content_type=asset_type,
                business_context=json.dumps(business_context, default=str),
                successful_approach=successful_approach,
                quality_indicators=quality_assessment.get("strengths", []),
                tool_sequence=[r["tool"] for r in tool_results if r.get("success")],
                created_at=datetime.now(),
                success_rate=1.0,  # Initial success rate
                usage_count=1
            )
            
            self.memory_patterns.append(pattern)
            
            # Keep only recent patterns (memory management)
            if len(self.memory_patterns) > 50:
                # Remove oldest patterns with low success rates
                self.memory_patterns.sort(key=lambda p: (p.success_rate, p.created_at))
                self.memory_patterns = self.memory_patterns[-50:]
            
            logger.info(f"💾 Stored successful pattern: {pattern_id}")
            
        except Exception as e:
            logger.debug(f"Pattern storage failed: {e}")
    
    async def _store_generation_learning(
        self,
        asset_type: str,
        result: AssetGenerationResult
    ):
        """
        Store generation results for learning
        """
        try:
            learning_entry = {
                "timestamp": datetime.now().isoformat(),
                "asset_type": asset_type,
                "content_quality": result.content_quality.value,
                "business_specificity_score": result.business_specificity_score,
                "tool_integration_score": result.tool_integration_score,
                "tools_used": result.source_tools_used,
                "memory_patterns_applied": result.memory_patterns_applied,
                "auto_improvements": result.auto_improvements,
                "confidence": result.confidence
            }
            
            self.generation_history.append(learning_entry)
            
            # Keep recent history
            if len(self.generation_history) > 100:
                self.generation_history = self.generation_history[-100:]
                
        except Exception as e:
            logger.debug(f"Generation learning storage failed: {e}")
    
    def _extract_existing_data(self, task_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract existing data from task results"""
        if not task_results:
            return {}
        
        existing_data = {}
        for task in task_results:
            if task.get("result"):
                task_name = task.get("name", "unknown")
                existing_data[task_name] = task["result"]
        
        return existing_data
    
    def _classify_content_quality(self, quality_score: float) -> ContentQuality:
        """Classify content quality based on score"""
        if quality_score >= 90:
            return ContentQuality.EXCELLENT
        elif quality_score >= 75:
            return ContentQuality.GOOD
        elif quality_score >= 60:
            return ContentQuality.ACCEPTABLE
        elif quality_score >= 30:
            return ContentQuality.POOR
        else:
            return ContentQuality.FAILED
    
    def _create_error_result(self, error_message: str) -> AssetGenerationResult:
        """Create error result when generation fails"""
        return AssetGenerationResult(
            generated_content={"error": error_message},
            content_quality=ContentQuality.FAILED,
            business_specificity_score=0,
            tool_integration_score=0,
            memory_enhancement_score=0,
            generation_reasoning=f"Generation failed: {error_message}",
            source_tools_used=[],
            memory_patterns_applied=[],
            auto_improvements=[f"Fix generation error: {error_message}"],
            confidence=0
        )
    
    # Fallback methods for when components are not available
    def _fallback_tool_determination(self, asset_type: str) -> List[str]:
        """Fallback tool determination"""
        tool_mapping = {
            "email_sequences": ["websearch", "competitor_analysis"],
            "lead_list": ["websearch", "data_analyzer"],
            "content_strategy": ["websearch", "competitor_analysis", "data_analyzer"]
        }
        return tool_mapping.get(asset_type, ["websearch"])
    
    def _fallback_data_collection(self, asset_type: str, business_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback data collection"""
        return [{
            "tool": "fallback_data",
            "success": True,
            "data": {
                "note": "Fallback data collection",
                "asset_type": asset_type,
                "business_context": business_context
            },
            "quality_score": 30,
            "confidence": 20
        }]
    
    def _fallback_content_generation(self, asset_type: str, business_context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback content generation"""
        return {
            "fallback_content": f"Generated {asset_type} for {business_context.get('company_name', 'business')}",
            "generation_method": "fallback",
            "note": "Limited content generation without AI"
        }
    
    def _fallback_quality_assessment(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback quality assessment"""
        content_size = len(json.dumps(content, default=str))
        
        if content_size > 500:
            quality_score = 60
        elif content_size > 200:
            quality_score = 40
        else:
            quality_score = 20
        
        return {
            "quality_score": quality_score,
            "specificity_score": quality_score,
            "tool_integration_score": 30,
            "usability_score": quality_score,
            "professional_score": quality_score,
            "reasoning": "Fallback assessment based on content size",
            "confidence": 30
        }

# Global instance
memory_enhanced_ai_asset_generator = MemoryEnhancedAIAssetGenerator()

# Export for easy import
__all__ = ["MemoryEnhancedAIAssetGenerator", "memory_enhanced_ai_asset_generator", "AssetGenerationResult", "ContentQuality"]