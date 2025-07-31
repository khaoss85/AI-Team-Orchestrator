"""
🤖 AI Tool-Aware Task Completion Validator
Validates task completion by analyzing tool usage and real content generation

Pillar 3: Real Tool Usage - Ensures tasks use appropriate tools for real data collection
Pillar 8: No Hardcode - AI-driven tool requirement analysis, no predefined patterns
Pillar 11: Self-Enhancement - Learns optimal tool usage patterns over time
Pillar 12: Course Correction - Auto-detects missing tool usage and suggests corrections
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

class TaskCompletionLevel(Enum):
    """Levels of task completion quality"""
    COMPLETE_WITH_TOOLS = "complete_with_tools"  # Task completed using appropriate tools
    COMPLETE_NO_TOOLS = "complete_no_tools"  # Task completed but no tools used
    PARTIAL_TOOLS_MISSING = "partial_tools_missing"  # Some tools used but key ones missing
    PLANNING_ONLY = "planning_only"  # Only planning phase, no execution with tools
    INCOMPLETE = "incomplete"  # Task not properly completed

@dataclass
class ToolUsageAnalysis:
    """Analysis of tool usage in task execution"""
    tools_used: List[str]
    tools_required: List[str]
    tools_missing: List[str]
    tool_effectiveness_score: float  # 0-100
    real_data_collected: bool
    tool_usage_reasoning: str

@dataclass
class TaskCompletionValidation:
    """Complete validation result for task completion"""
    completion_level: TaskCompletionLevel
    completion_score: float  # 0-100
    tool_usage_analysis: ToolUsageAnalysis
    content_authenticity_score: float  # 0-100
    business_readiness_score: float  # 0-100
    missing_actions: List[str]
    auto_completion_plan: Dict[str, Any]
    validation_reasoning: str
    confidence: float  # 0-100

class AIToolAwareValidator:
    """
    🤖 AI-Driven Task Completion Validator with Tool Usage Analysis
    Validates that tasks actually complete objectives using real tools
    """
    
    def __init__(self):
        self.validation_history = []
        self.available_tools = []  # Will be populated dynamically
        
    async def _get_available_tools(self) -> List[str]:
        """🔧 **DYNAMIC TOOL REGISTRY**: Get list of available tools from registry"""
        try:
            # 🔧 **ELIMINATE TOOL REGISTRY SILO**: Use dynamic tool discovery
            from tools.registry import tool_registry
            from tools.openai_sdk_tools import openai_tools_manager
            
            available_tools = []
            
            # Get dynamic tools from registry
            await tool_registry.initialize()
            # Tool registry is primarily for user/agent-created custom tools
            # We get the base system tools from the OpenAI SDK tools manager
            
            # Get system tools from OpenAI SDK tools manager
            system_tools = openai_tools_manager.get_tool_descriptions()
            available_tools.extend(system_tools.keys())
            
            # Add core analysis tools that are always available
            core_analysis_tools = [
                "content_analyzer",
                "data_processor", 
                "competitor_research",
                "email_validator",
                "contact_discovery"
            ]
            available_tools.extend(core_analysis_tools)
            
            logger.info(f"🔧 Dynamic tool discovery: Found {len(available_tools)} available tools")
            return list(set(available_tools))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"❌ Dynamic tool discovery failed: {e}")
            logger.warning("🔄 Falling back to minimal tool set")
            # Fallback to minimal tool set if registry fails
            return ["web_search", "file_search", "content_analyzer"]
            
            # Note: content generation is NOT a tool - it's a pipeline stage
    
    async def validate_task_completion_with_tools(
        self,
        task_result: Dict[str, Any],
        task_name: str,
        task_objective: str,
        business_context: Dict[str, Any] = None
    ) -> TaskCompletionValidation:
        """
        🤖 AI-DRIVEN: Comprehensive task completion validation with tool analysis
        
        Args:
            task_result: The result/output from task execution
            task_name: Name/description of the task
            task_objective: The intended objective of the task
            business_context: Business context for validation
            
        Returns:
            TaskCompletionValidation with comprehensive analysis
        """
        try:
            logger.info(f"🔍 Validating task completion with tool analysis: {task_name}")
            
            # Step 0: Get dynamic tool list
            if not self.available_tools:
                self.available_tools = await self._get_available_tools()
            
            # Step 1: AI Analysis of Required Tools
            required_tools = await self._ai_analyze_required_tools(
                task_name,
                task_objective,
                business_context
            )
            
            # Step 2: AI Analysis of Actual Tool Usage
            actual_tool_usage = await self._ai_analyze_actual_tool_usage(
                task_result,
                task_name
            )
            
            # Step 3: AI Tool Effectiveness Analysis
            tool_effectiveness = await self._ai_analyze_tool_effectiveness(
                required_tools,
                actual_tool_usage,
                task_result
            )
            
            # Step 4: AI Content Authenticity Analysis
            content_authenticity = await self._ai_analyze_content_authenticity(
                task_result,
                actual_tool_usage
            )
            
            # Step 5: AI Business Readiness Assessment
            business_readiness = await self._ai_assess_business_readiness(
                task_result,
                task_objective,
                business_context
            )
            
            # Step 6: AI Completion Level Classification
            completion_level = await self._ai_classify_completion_level(
                required_tools,
                actual_tool_usage,
                content_authenticity,
                business_readiness
            )
            
            # Step 7: AI Auto-Completion Plan Generation
            auto_completion_plan = await self._ai_generate_completion_plan(
                completion_level,
                required_tools,
                actual_tool_usage,
                task_objective,
                business_context
            )
            
            # Compile validation result
            tool_usage_analysis = ToolUsageAnalysis(
                tools_used=actual_tool_usage.get("tools_identified", []),
                tools_required=required_tools.get("required_tools", []),
                tools_missing=[tool for tool in required_tools.get("required_tools", []) if tool not in actual_tool_usage.get("tools_identified", [])],
                tool_effectiveness_score=tool_effectiveness.get("effectiveness_score", 0),
                real_data_collected=actual_tool_usage.get("real_data_found", False),
                tool_usage_reasoning=tool_effectiveness.get("reasoning", "")
            )
            
            validation = TaskCompletionValidation(
                completion_level=completion_level,
                completion_score=self._calculate_completion_score(
                    tool_effectiveness.get("effectiveness_score", 0),
                    content_authenticity.get("authenticity_score", 0),
                    business_readiness.get("readiness_score", 0)
                ),
                tool_usage_analysis=tool_usage_analysis,
                content_authenticity_score=content_authenticity.get("authenticity_score", 0),
                business_readiness_score=business_readiness.get("readiness_score", 0),
                missing_actions=auto_completion_plan.get("missing_actions", []),
                auto_completion_plan=auto_completion_plan,
                validation_reasoning=self._compile_validation_reasoning(
                    completion_level,
                    tool_effectiveness,
                    content_authenticity,
                    business_readiness
                ),
                confidence=min(
                    tool_effectiveness.get("confidence", 0),
                    content_authenticity.get("confidence", 0),
                    business_readiness.get("confidence", 0)
                )
            )
            
            # Store for learning
            await self._store_validation_learning(task_name, task_result, validation)
            
            logger.info(f"✅ Task validation complete: Level={completion_level.value}, Score={validation.completion_score:.1f}")
            
            return validation
            
        except Exception as e:
            logger.error(f"Error in AI task validation: {e}")
            return self._create_error_validation(str(e))
    
    async def _ai_analyze_required_tools(
        self,
        task_name: str,
        task_objective: str,
        business_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        🤖 AI analysis of what tools should be required for this task
        """
        try:
            # 🤖 **AI PROVIDER ABSTRACTION**: Use unified AI provider instead of direct OpenAI
            from services.ai_provider_abstraction import ai_provider_manager
            
            # Create agent configuration for tool analysis
            tool_analysis_agent = {
                "name": "ToolRequirementsAnalyst",
                "role": "Expert tool orchestration analyst specializing in business task completion",
                "capabilities": ["tool_analysis", "business_requirements", "task_decomposition"]
            }
            
            prompt = f"""
Analizza quale tools dovrebbero essere usati per completare questo task in modo professionale.

TASK: {task_name}
OBJECTIVE: {task_objective}
BUSINESS CONTEXT: {json.dumps(business_context or {}, indent=2)}

AVAILABLE TOOLS:
{', '.join(self.available_tools)}

ANALISI RICHIESTA:
1. Quali tools sono ESSENZIALI per completare questo task con dati reali?
2. Quali tools sono OPZIONALI ma migliorerebbero la qualità?
3. Perché ogni tool è necessario per questo specifico objective?

Per esempio:
- Se il task è "Create email sequences" → websearch per esempi reali, competitor_analysis per best practices
- Se il task è "Find contacts" → websearch per company data, contact_finder per validation
- Se il task è "Research competitors" → websearch per analysis, data_analyzer per insights

Rispondi in JSON:
{{
    "required_tools": ["tool1", "tool2"],
    "optional_tools": ["tool3"],
    "tool_justification": {{
        "tool1": "perché è essenziale per...",
        "tool2": "necessario per raccogliere..."
    }},
    "expected_data_types": ["tipo di dato che ogni tool dovrebbe fornire"],
    "confidence": 0-100
}}
"""
            
            # Use AI Provider Abstraction for tool requirements analysis
            response = await ai_provider_manager.call_ai(
                provider_type='openai_sdk',
                agent=tool_analysis_agent,
                prompt=prompt,
                temperature=0.1,
                max_tokens=1000
            )
            
            # Extract AI response from provider abstraction
            ai_response = response if isinstance(response, str) else response.get('response', str(response))
            
            try:
                return json.loads(ai_response)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse required tools analysis: {ai_response}")
                return self._fallback_required_tools_analysis(task_name)
                
        except Exception as e:
            logger.error(f"❌ AI Provider Abstraction tool requirements analysis failed: {e}")
            logger.warning("🔄 Falling back to hardcoded analysis")
            return self._fallback_required_tools_analysis(task_name)
    
    async def _ai_analyze_actual_tool_usage(
        self,
        task_result: Dict[str, Any],
        task_name: str
    ) -> Dict[str, Any]:
        """
        🤖 AI analysis of what tools were actually used in task execution
        """
        try:
            # 🤖 **AI PROVIDER ABSTRACTION**: Use unified AI provider
            from services.ai_provider_abstraction import ai_provider_manager
            
            # Create agent configuration for actual tools analysis
            actual_tools_agent = {
                "name": "ActualToolsAnalyst",
                "role": "Expert at analyzing what tools were actually used in task completion",
                "capabilities": ["tool_detection", "content_analysis", "data_source_identification"]
            }
            
            # Extract relevant parts of task result for analysis
            task_result_sample = self._extract_task_result_sample(task_result)
            
            prompt = f"""
Analizza questo risultato di task per identificare quali tools sono stati usati.

TASK: {task_name}
TASK RESULT:
{task_result_sample}

ANALISI RICHIESTA:
1. Quali tools sono stati effettivamente usati? (cerca evidenze di websearch, data collection, ecc.)
2. Il task ha raccolto dati reali da fonti esterne?
3. Ci sono evidenze di tool execution vs solo planning/delegation?

Cerca indicatori come:
- "searched for...", "found data...", "analyzed competitors..." → websearch usato
- "processed files...", "analyzed documents..." → file_search usato  
- "generated based on research..." → content_generator usato
- "ANALYSIS phase", "delegated to..." → solo planning, no tools

Rispondi in JSON:
{{
    "tools_identified": ["tool1", "tool2"],
    "tool_evidence": {{
        "tool1": "evidenza nel risultato che indica uso del tool"
    }},
    "real_data_found": true/false,
    "execution_vs_planning": "execution/planning/mixed",
    "data_sources": ["source1", "source2"],
    "confidence": 0-100
}}
"""
            
            # Use AI Provider Abstraction for actual tools analysis
            response = await ai_provider_manager.call_ai(
                provider_type='openai_sdk',
                agent=actual_tools_agent,
                prompt=prompt,
                temperature=0.1,
                max_tokens=1000
            )
            
            # Extract AI response from provider abstraction
            ai_response = response if isinstance(response, str) else response.get('response', str(response))
            
            try:
                return json.loads(ai_response)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse actual tools analysis: {ai_response}")
                return self._fallback_actual_tools_analysis(task_result)
                
        except Exception as e:
            logger.error(f"Error in AI actual tools analysis: {e}")
            return self._fallback_actual_tools_analysis(task_result)
    
    async def _ai_analyze_tool_effectiveness(
        self,
        required_tools: Dict[str, Any],
        actual_tool_usage: Dict[str, Any],
        task_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        🤖 AI analysis of tool usage effectiveness
        """
        try:
            # 🤖 **AI PROVIDER ABSTRACTION**: Use unified AI provider
            from services.ai_provider_abstraction import ai_provider_manager
            
            # Create agent configuration for effectiveness analysis
            effectiveness_agent = {
                "name": "ToolEffectivenessAnalyst",
                "role": "Expert tool effectiveness evaluator specialized in business task completion",
                "capabilities": ["effectiveness_analysis", "quality_assessment", "tool_optimization"]
            }
            
            prompt = f"""
Valuta l'efficacia dell'uso dei tools per questo task.

TOOLS RICHIESTI:
{json.dumps(required_tools, indent=2)}

TOOLS EFFETTIVAMENTE USATI:
{json.dumps(actual_tool_usage, indent=2)}

VALUTAZIONE EFFICACIA:
1. Percentage di tools richiesti che sono stati usati?
2. I tools usati hanno prodotto dati utili e reali?
3. Mancano tools critici che compromettono la qualità?
4. Score complessivo di tool effectiveness (0-100)?

Considera:
- Se websearch era richiesto ma non usato → score basso
- Se solo planning senza tool execution → score molto basso  
- Se tools usati ma con dati generic/template → score medio
- Se tools usati con dati reali e specifici → score alto

Rispondi in JSON:
{{
    "effectiveness_score": 0-100,
    "tools_coverage_percentage": 0-100,
    "critical_tools_missing": ["tool1", "tool2"],
    "tools_used_effectively": ["tool1"],
    "data_quality_assessment": "real/generic/template",
    "reasoning": "spiegazione dettagliata del score",
    "confidence": 0-100
}}
"""
            
            # Use AI Provider Abstraction for effectiveness analysis
            response = await ai_provider_manager.call_ai(
                provider_type='openai_sdk',
                agent=effectiveness_agent,
                prompt=prompt,
                temperature=0.1,
                max_tokens=1000
            )
            
            # Extract AI response from provider abstraction
            ai_response = response if isinstance(response, str) else response.get('response', str(response))
            
            try:
                return json.loads(ai_response)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse tool effectiveness analysis: {ai_response}")
                return self._fallback_effectiveness_analysis(required_tools, actual_tool_usage)
                
        except Exception as e:
            logger.error(f"Error in AI tool effectiveness analysis: {e}")
            return self._fallback_effectiveness_analysis(required_tools, actual_tool_usage)
    
    async def _ai_analyze_content_authenticity(
        self,
        task_result: Dict[str, Any],
        actual_tool_usage: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        🤖 AI analysis of content authenticity vs template/generic content
        """
        try:
            # 🤖 **AI PROVIDER ABSTRACTION**: Use unified AI provider
            from services.ai_provider_abstraction import ai_provider_manager
            
            # Create agent configuration for authenticity analysis
            authenticity_agent = {
                "name": "ContentAuthenticityAnalyst",
                "role": "Expert content authenticity analyzer specialized in detecting real vs template content",
                "capabilities": ["authenticity_analysis", "content_validation", "data_source_detection"]
            }
            
            task_content = self._extract_task_result_sample(task_result)
            
            prompt = f"""
Valuta l'autenticità del contenuto generato dal task.

CONTENUTO TASK:
{task_content}

TOOLS USATI:
{json.dumps(actual_tool_usage, indent=2)}

VALUTAZIONE AUTENTICITÀ:
1. Il contenuto è specifico e business-ready o generico/template?
2. Ci sono evidenze di dati reali raccolti da tools?
3. Il contenuto è utilizzabile immediatamente o richiede personalizzazione?

Cerca indicatori:
- Nomi specifici, numeri reali, esempi concreti → alta autenticità
- "Aimed at...", "Designed to...", placeholder → bassa autenticità
- Dati da websearch, insights specifici → alta autenticità
- Solo planning e descrizioni generiche → bassa autenticità

Rispondi in JSON:
{{
    "authenticity_score": 0-100,
    "specific_elements": ["elementi specifici trovati"],
    "generic_elements": ["elementi generici/template trovati"],
    "real_data_indicators": ["indicatori di dati reali"],
    "business_readiness": "ready/needs_work/template",
    "confidence": 0-100
}}
"""
            
            # Use AI Provider Abstraction for authenticity analysis
            response = await ai_provider_manager.call_ai(
                provider_type='openai_sdk',
                agent=authenticity_agent,
                prompt=prompt,
                temperature=0.1,
                max_tokens=1000
            )
            
            # Extract AI response from provider abstraction
            ai_response = response if isinstance(response, str) else response.get('response', str(response))
            
            try:
                return json.loads(ai_response)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse content authenticity analysis: {ai_response}")
                return {"authenticity_score": 50, "confidence": 20}
                
        except Exception as e:
            logger.error(f"Error in AI content authenticity analysis: {e}")
            return {"authenticity_score": 50, "confidence": 20}
    
    async def _ai_assess_business_readiness(
        self,
        task_result: Dict[str, Any],
        task_objective: str,
        business_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        🤖 AI assessment of business readiness
        """
        # Simplified for now - can be enhanced
        authenticity_score = 70 if self._has_substantial_content(task_result) else 30
        return {
            "readiness_score": authenticity_score,
            "confidence": 60
        }
    
    async def _ai_classify_completion_level(
        self,
        required_tools: Dict[str, Any],
        actual_tool_usage: Dict[str, Any],
        content_authenticity: Dict[str, Any],
        business_readiness: Dict[str, Any]
    ) -> TaskCompletionLevel:
        """
        🤖 AI classification of task completion level
        """
        tools_used = len(actual_tool_usage.get("tools_identified", []))
        tools_required = len(required_tools.get("required_tools", []))
        authenticity = content_authenticity.get("authenticity_score", 0)
        readiness = business_readiness.get("readiness_score", 0)
        
        if tools_used >= tools_required and authenticity >= 70 and readiness >= 70:
            return TaskCompletionLevel.COMPLETE_WITH_TOOLS
        elif tools_used == 0 and authenticity >= 60:
            return TaskCompletionLevel.COMPLETE_NO_TOOLS
        elif tools_used > 0 and tools_used < tools_required:
            return TaskCompletionLevel.PARTIAL_TOOLS_MISSING
        elif "planning" in actual_tool_usage.get("execution_vs_planning", "").lower():
            return TaskCompletionLevel.PLANNING_ONLY
        else:
            return TaskCompletionLevel.INCOMPLETE
    
    async def _ai_generate_completion_plan(
        self,
        completion_level: TaskCompletionLevel,
        required_tools: Dict[str, Any],
        actual_tool_usage: Dict[str, Any],
        task_objective: str,
        business_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        🤖 AI generation of auto-completion plan
        """
        missing_tools = set(required_tools.get("required_tools", [])) - set(actual_tool_usage.get("tools_identified", []))
        
        completion_plan = {
            "missing_actions": [],
            "tool_execution_plan": [],
            "expected_improvements": []
        }
        
        if completion_level in [TaskCompletionLevel.PLANNING_ONLY, TaskCompletionLevel.INCOMPLETE]:
            completion_plan["missing_actions"] = [
                f"Execute {tool} to gather real data" for tool in missing_tools
            ]
            completion_plan["tool_execution_plan"] = [
                {
                    "tool": tool,
                    "action": f"Use {tool} to collect data for {task_objective}",
                    "expected_output": "Real data collection"
                }
                for tool in missing_tools
            ]
        
        return completion_plan
    
    def _extract_task_result_sample(self, task_result: Dict[str, Any]) -> str:
        """Extract relevant sample from task result for analysis"""
        sample_parts = []
        
        # Extract key fields
        for key in ['summary', 'detailed_results_json', 'output', 'result']:
            if key in task_result:
                value = task_result[key]
                if isinstance(value, str):
                    sample_parts.append(f"{key}: {value[:300]}...")
                elif isinstance(value, dict):
                    sample_parts.append(f"{key}: {json.dumps(value, default=str)[:300]}...")
        
        return "\n".join(sample_parts) or str(task_result)[:500] + "..."
    
    def _has_substantial_content(self, task_result: Dict[str, Any]) -> bool:
        """Check if task result has substantial content"""
        content_str = json.dumps(task_result, default=str)
        return len(content_str) > 200
    
    def _calculate_completion_score(
        self,
        tool_effectiveness: float,
        content_authenticity: float,
        business_readiness: float
    ) -> float:
        """Calculate overall completion score"""
        # Weighted average with tools being most important
        return (tool_effectiveness * 0.4 + content_authenticity * 0.3 + business_readiness * 0.3)
    
    def _compile_validation_reasoning(
        self,
        completion_level: TaskCompletionLevel,
        tool_effectiveness: Dict[str, Any],
        content_authenticity: Dict[str, Any],
        business_readiness: Dict[str, Any]
    ) -> str:
        """Compile comprehensive validation reasoning"""
        reasoning_parts = []
        
        reasoning_parts.append(f"COMPLETION LEVEL: {completion_level.value}")
        reasoning_parts.append(f"TOOL EFFECTIVENESS: {tool_effectiveness.get('reasoning', 'N/A')}")
        reasoning_parts.append(f"CONTENT AUTHENTICITY: {content_authenticity.get('authenticity_score', 0):.1f}/100")
        reasoning_parts.append(f"BUSINESS READINESS: {business_readiness.get('readiness_score', 0):.1f}/100")
        
        return " | ".join(reasoning_parts)
    
    async def _store_validation_learning(
        self,
        task_name: str,
        task_result: Dict[str, Any],
        validation: TaskCompletionValidation
    ):
        """Store validation results for learning"""
        try:
            learning_entry = {
                "timestamp": datetime.now().isoformat(),
                "task_name": task_name,
                "completion_level": validation.completion_level.value,
                "completion_score": validation.completion_score,
                "tools_used": validation.tool_usage_analysis.tools_used,
                "tools_required": validation.tool_usage_analysis.tools_required,
                "content_authenticity": validation.content_authenticity_score
            }
            
            self.validation_history.append(learning_entry)
            
            # Keep only recent entries
            if len(self.validation_history) > 100:
                self.validation_history = self.validation_history[-100:]
                
        except Exception as e:
            logger.debug(f"Validation learning storage failed: {e}")
    
    def _create_error_validation(self, error_message: str) -> TaskCompletionValidation:
        """Create error validation when analysis fails"""
        return TaskCompletionValidation(
            completion_level=TaskCompletionLevel.INCOMPLETE,
            completion_score=0,
            tool_usage_analysis=ToolUsageAnalysis(
                tools_used=[],
                tools_required=[],
                tools_missing=[],
                tool_effectiveness_score=0,
                real_data_collected=False,
                tool_usage_reasoning=f"Validation failed: {error_message}"
            ),
            content_authenticity_score=0,
            business_readiness_score=0,
            missing_actions=[f"Fix validation error: {error_message}"],
            auto_completion_plan={},
            validation_reasoning=f"Validation failed: {error_message}",
            confidence=0
        )
    
    # Fallback methods for when AI is not available
    def _fallback_required_tools_analysis(self, task_name: str) -> Dict[str, Any]:
        """Fallback analysis when AI not available - uses minimal tool set"""
        # When AI is not available, suggest minimal tools that are always safe
        # The actual tool selection should be done by AI whenever possible
        
        # Default to websearch as it's universally useful for gathering real data
        required_tools = ['websearch']
        
        # Note: Content generation is NOT a tool - it's handled by the pipeline's
        # Stage 3 (Content Generation) which uses memory_enhanced_ai_asset_generator
        
        return {
            "required_tools": required_tools,
            "optional_tools": ['data_analyzer'],  # Always useful for insights
            "tool_justification": {
                'websearch': f"Essential for gathering real data for {task_name}",
                'data_analyzer': "Optional for deeper insights and analysis"
            },
            "confidence": 30  # Low confidence as this is just a fallback
        }
    
    def _fallback_actual_tools_analysis(self, task_result: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback analysis of actual tool usage"""
        result_str = json.dumps(task_result, default=str).lower()
        
        tools_identified = []
        if any(keyword in result_str for keyword in ['search', 'found', 'analyzed']):
            tools_identified.append('websearch')
        if 'analysis phase' in result_str:
            tools_identified = []  # Planning only
        
        return {
            "tools_identified": tools_identified,
            "tool_evidence": {},
            "real_data_found": len(tools_identified) > 0,
            "execution_vs_planning": "planning" if not tools_identified else "execution",
            "confidence": 40
        }
    
    def _fallback_effectiveness_analysis(
        self,
        required_tools: Dict[str, Any],
        actual_tool_usage: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback effectiveness analysis"""
        required = len(required_tools.get("required_tools", []))
        used = len(actual_tool_usage.get("tools_identified", []))
        
        effectiveness_score = (used / required * 100) if required > 0 else 0
        
        return {
            "effectiveness_score": effectiveness_score,
            "tools_coverage_percentage": effectiveness_score,
            "critical_tools_missing": [],
            "reasoning": f"Basic analysis: {used}/{required} tools used",
            "confidence": 30
        }

# Global instance
ai_tool_aware_validator = AIToolAwareValidator()

# Export for easy import
__all__ = ["AIToolAwareValidator", "ai_tool_aware_validator", "TaskCompletionValidation", "TaskCompletionLevel"]