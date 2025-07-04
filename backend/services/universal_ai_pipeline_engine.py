"""
Universal AI Pipeline Engine - Core Foundation

Centralizes ALL AI operations for the system to ensure:
- Intelligent rate limiting with circuit breaker pattern
- Semantic caching for performance optimization
- Universal fallback strategies
- Pipeline consistency across all components
- Producer-ready reliability and monitoring
"""

import asyncio
import time
import json
import hashlib
import os
from typing import Any, Dict, List, Optional, Union, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from contextlib import asynccontextmanager

import openai
from openai import AsyncOpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class PipelineStepType(Enum):
    """Enumeration of all possible AI pipeline steps in the system"""
    ASSET_REQUIREMENTS_GENERATION = "asset_requirements_generation"
    TASK_GENERATION = "task_generation"
    QUALITY_VALIDATION = "quality_validation"
    CONTENT_ENHANCEMENT = "content_enhancement"
    SKILL_ANALYSIS = "skill_analysis"
    GOAL_DECOMPOSITION = "goal_decomposition"
    PRIORITY_CALCULATION = "priority_calculation"
    SIMILARITY_MATCHING = "similarity_matching"
    FAKE_DETECTION = "fake_detection"
    SEMANTIC_ANALYSIS = "semantic_analysis"
    # Legacy compatibility
    ASSET_DECOMPOSITION = "asset_decomposition"
    SEMANTIC_SIMILARITY = "semantic_similarity"

class CircuitBreakerState(Enum):
    """Circuit breaker states for fault tolerance"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing fast
    HALF_OPEN = "half_open"  # Testing recovery

@dataclass
class PipelineContext:
    """Context information for pipeline execution"""
    workspace_id: Optional[str] = None
    goal_id: Optional[str] = None
    task_id: Optional[str] = None
    user_context: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 30
    cache_enabled: bool = True
    fallback_enabled: bool = True

@dataclass
class PipelineResult:
    """Result of pipeline execution"""
    success: bool
    data: Any = None
    output_data: Any = None  # Legacy compatibility
    reasoning: str = ""
    confidence: float = 1.0
    error: Optional[str] = None
    execution_time: float = 0.0
    cached: bool = False
    fallback_used: bool = False
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

class UniversalAIPipelineEngine:
    """
    Universal AI Pipeline Engine that centralizes all AI operations
    
    Features:
    - Circuit breaker pattern for fault tolerance
    - Intelligent rate limiting with exponential backoff
    - Semantic caching for performance
    - Universal fallback strategies
    - Comprehensive monitoring and logging
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        max_requests_per_minute: int = 50,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: int = 60,
        cache_ttl_seconds: int = 3600
    ):
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=api_key) if api_key else None
        self.ai_available = bool(api_key)
        
        # Rate limiting
        self.max_requests_per_minute = max_requests_per_minute
        self.request_times: List[float] = []
        self._request_timestamps = self.request_times  # Alias for compatibility
        self.rate_limit_lock = asyncio.Lock()
        
        # Circuit breaker
        self.circuit_state = CircuitBreakerState.CLOSED
        self._circuit_breaker_state = self.circuit_state  # Alias for compatibility
        self.failure_count = 0
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_timeout = circuit_breaker_timeout
        self.last_failure_time = 0
        
        # Caching
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl_seconds = cache_ttl_seconds
        
        # Statistics
        self.total_requests = 0
        self.successful_requests = 0
        self.cached_requests = 0
        self.fallback_requests = 0
        
        logger.info("🤖 UniversalAIPipelineEngine initialized with advanced features")
        
    async def execute_pipeline_step(
        self,
        step_type: PipelineStepType,
        input_data: Any,
        context: PipelineContext,
        custom_prompt: Optional[str] = None,
        model: str = "gpt-4o-mini"
    ) -> PipelineResult:
        """
        Execute any AI pipeline step with universal handling
        
        Args:
            step_type: Type of pipeline step to execute
            input_data: Input data for the step
            context: Execution context
            custom_prompt: Optional custom prompt override
            model: OpenAI model to use
            
        Returns:
            PipelineResult with execution results
        """
        start_time = time.time()
        self.total_requests += 1
        
        try:
            # Backwards compatibility - map data to output_data
            def _ensure_backward_compatibility(result: PipelineResult) -> PipelineResult:
                if result.data is not None and result.output_data is None:
                    result.output_data = result.data
                return result
            
            # Check if AI is available
            if not self.ai_available:
                logger.warning("🚫 AI client not available, using fallback")
                result = await self._execute_fallback(step_type, input_data, context, start_time)
                return _ensure_backward_compatibility(result)
            
            # Check circuit breaker
            if not await self._is_circuit_closed():
                if context.fallback_enabled:
                    logger.warning(f"🔄 Circuit breaker OPEN, using fallback for {step_type.value}")
                    result = await self._execute_fallback(step_type, input_data, context, start_time)
                    return _ensure_backward_compatibility(result)
                else:
                    return PipelineResult(
                        success=False,
                        error="Circuit breaker is OPEN and no fallback available",
                        execution_time=time.time() - start_time,
                        reasoning="Circuit breaker protection active"
                    )
            
            # Check cache first
            if context.cache_enabled:
                cached_result = await self._get_cached_result(step_type, input_data, context)
                if cached_result:
                    self.cached_requests += 1
                    logger.info(f"🎯 Cache HIT for {step_type.value}")
                    return _ensure_backward_compatibility(cached_result)
            
            # Rate limiting
            await self._enforce_rate_limit()
            
            # Execute AI request
            prompt = custom_prompt or self._get_default_prompt(step_type, input_data, context)
            
            ai_response = await self._execute_ai_request(prompt, model, context)
            
            # Process and cache result
            processed_result = await self._process_ai_response(step_type, ai_response, context, start_time)
            
            if context.cache_enabled and processed_result.success:
                await self._cache_result(step_type, input_data, context, processed_result)
            
            # Update circuit breaker on success
            await self._record_success()
            
            self.successful_requests += 1
            logger.info(f"✅ Pipeline step {step_type.value} completed successfully")
            
            return _ensure_backward_compatibility(processed_result)
            
        except Exception as e:
            logger.error(f"❌ Pipeline step {step_type.value} failed: {str(e)}")
            
            # Record failure for circuit breaker
            await self._record_failure()
            
            # Try fallback if enabled
            if context.fallback_enabled and context.retry_count < context.max_retries:
                context.retry_count += 1
                logger.info(f"🔄 Retrying {step_type.value} (attempt {context.retry_count})")
                await asyncio.sleep(2 ** context.retry_count)  # Exponential backoff
                return await self.execute_pipeline_step(step_type, input_data, context, custom_prompt, model)
            
            result = PipelineResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time,
                retry_count=context.retry_count,
                reasoning=f"Failed after {context.retry_count} retries"
            )
            return _ensure_backward_compatibility(result)
    
    async def _is_circuit_closed(self) -> bool:
        """Check if circuit breaker allows requests"""
        current_time = time.time()
        
        if self.circuit_state == CircuitBreakerState.CLOSED:
            return True
        elif self.circuit_state == CircuitBreakerState.OPEN:
            if current_time - self.last_failure_time > self.circuit_breaker_timeout:
                self.circuit_state = CircuitBreakerState.HALF_OPEN
                logger.info("🔄 Circuit breaker moving to HALF_OPEN")
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    async def _enforce_rate_limit(self):
        """Enforce rate limiting with intelligent queuing"""
        async with self.rate_limit_lock:
            current_time = time.time()
            
            # Remove old requests (older than 1 minute)
            self.request_times = [t for t in self.request_times if current_time - t < 60]
            
            # Check if we need to wait
            if len(self.request_times) >= self.max_requests_per_minute:
                wait_time = 60 - (current_time - self.request_times[0])
                if wait_time > 0:
                    logger.info(f"⏳ Rate limiting: waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
            
            self.request_times.append(current_time)
    
    async def _execute_ai_request(self, prompt: str, model: str, context: PipelineContext) -> str:
        """Execute actual AI request with timeout"""
        try:
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=2000
                ),
                timeout=context.timeout_seconds
            )
            return response.choices[0].message.content
        except asyncio.TimeoutError:
            raise Exception(f"AI request timed out after {context.timeout_seconds}s")
        except openai.RateLimitError as e:
            logger.warning(f"🚫 OpenAI rate limit hit: {str(e)}")
            raise
        except Exception as e:
            raise Exception(f"AI request failed: {str(e)}")
    
    def _get_default_prompt(self, step_type: PipelineStepType, input_data: Any, context: PipelineContext) -> str:
        """Get default prompt for each pipeline step type"""
        
        # Handle legacy step types
        if step_type == PipelineStepType.ASSET_DECOMPOSITION:
            step_type = PipelineStepType.ASSET_REQUIREMENTS_GENERATION
        elif step_type == PipelineStepType.SEMANTIC_SIMILARITY:
            step_type = PipelineStepType.SIMILARITY_MATCHING
        
        prompts = {
            PipelineStepType.ASSET_REQUIREMENTS_GENERATION: self._get_asset_requirements_prompt(input_data, context),
            PipelineStepType.TASK_GENERATION: self._get_task_generation_prompt(input_data, context),
            PipelineStepType.QUALITY_VALIDATION: self._get_quality_validation_prompt(input_data, context),
            PipelineStepType.CONTENT_ENHANCEMENT: self._get_content_enhancement_prompt(input_data, context),
            PipelineStepType.SKILL_ANALYSIS: self._get_skill_analysis_prompt(input_data, context),
            PipelineStepType.GOAL_DECOMPOSITION: self._get_goal_decomposition_prompt(input_data, context),
            PipelineStepType.PRIORITY_CALCULATION: self._get_priority_calculation_prompt(input_data, context),
            PipelineStepType.SIMILARITY_MATCHING: self._get_similarity_matching_prompt(input_data, context),
            PipelineStepType.FAKE_DETECTION: self._get_fake_detection_prompt(input_data, context),
            PipelineStepType.SEMANTIC_ANALYSIS: self._get_semantic_analysis_prompt(input_data, context),
        }
        
        return prompts.get(step_type, f"Analyze the following data: {json.dumps(input_data, indent=2)}")
    
    def _get_asset_requirements_prompt(self, input_data: Any, context: PipelineContext) -> str:
        """Generate prompt for asset requirements generation"""
        return f"""
As an expert business analyst, analyze the following goal and generate specific, actionable asset requirements.

GOAL CONTEXT:
{json.dumps(input_data, indent=2) if hasattr(input_data, '__dict__') else str(input_data)}

WORKSPACE CONTEXT:
{json.dumps(context.user_context, indent=2)}

Generate a JSON response with this structure:
{{
    "requirements": [
        {{
            "type": "content|data|analysis|design|development",
            "title": "Clear requirement title",
            "description": "Detailed description of what needs to be created",
            "priority": "high|medium|low",
            "complexity": "simple|medium|complex",
            "estimated_effort": "time estimate",
            "dependencies": ["list of dependencies"],
            "acceptance_criteria": ["specific criteria for completion"]
        }}
    ],
    "success_metrics": ["measurable success criteria"],
    "constraints": ["any limitations or constraints"]
}}

Focus on creating actionable, specific requirements that lead to concrete deliverables.
"""

    def _get_task_generation_prompt(self, input_data: Any, context: PipelineContext) -> str:
        """Generate prompt for task generation"""
        return f"""
As an expert project manager, convert the following asset requirement into specific, actionable tasks.

ASSET REQUIREMENT:
{json.dumps(input_data, indent=2) if hasattr(input_data, '__dict__') else str(input_data)}

CONTEXT:
{json.dumps(context.user_context, indent=2)}

Generate a JSON response with this structure:
{{
    "tasks": [
        {{
            "title": "Clear, action-oriented task title",
            "description": "Detailed task description with specific deliverables",
            "type": "research|analysis|creation|review|validation",
            "priority": 1-100,
            "estimated_duration": "time estimate",
            "required_skills": ["specific skills needed"],
            "dependencies": ["task dependencies"],
            "deliverables": ["specific outputs expected"],
            "acceptance_criteria": ["criteria for task completion"]
        }}
    ]
}}

Ensure tasks are:
1. Specific and actionable
2. Have clear deliverables
3. Are properly sequenced
4. Include realistic time estimates
"""

    def _get_quality_validation_prompt(self, input_data: Any, context: PipelineContext) -> str:
        """Generate prompt for quality validation"""
        return f"""
As an expert quality assurance analyst, evaluate the following content for quality, completeness, and adherence to requirements.

CONTENT TO VALIDATE:
{json.dumps(input_data, indent=2) if hasattr(input_data, '__dict__') else str(input_data)}

CONTEXT:
{json.dumps(context.user_context, indent=2)}

Provide a JSON response with this structure:
{{
    "overall_score": 0-100,
    "quality_metrics": {{
        "completeness": 0-100,
        "accuracy": 0-100,
        "clarity": 0-100,
        "relevance": 0-100,
        "actionability": 0-100
    }},
    "issues": [
        {{
            "severity": "critical|major|minor",
            "category": "completeness|accuracy|clarity|format|other",
            "description": "Detailed issue description",
            "suggested_fix": "Specific recommendation for improvement"
        }}
    ],
    "strengths": ["list of identified strengths"],
    "recommendations": ["specific improvement recommendations"],
    "approval_status": "approved|needs_revision|rejected"
}}

Focus on constructive feedback that improves the content's value and usability.
"""

    def _get_content_enhancement_prompt(self, input_data: Any, context: PipelineContext) -> str:
        """Generate prompt for content enhancement"""
        return f"""
As an expert content strategist, enhance the following content to make it more valuable, clear, and actionable.

CONTENT TO ENHANCE:
{json.dumps(input_data, indent=2) if hasattr(input_data, '__dict__') else str(input_data)}

CONTEXT:
{json.dumps(context.user_context, indent=2)}

Provide enhanced content that:
1. Improves clarity and readability
2. Adds actionable insights
3. Includes specific examples where relevant
4. Maintains accuracy while improving value
5. Follows best practices for the content type

Return the enhanced content with clear improvements marked.
"""

    def _get_skill_analysis_prompt(self, input_data: Any, context: PipelineContext) -> str:
        """Generate prompt for skill analysis"""
        return f"""
As an expert HR analyst, analyze the skills required for the following task/role and match against available resources.

TASK/ROLE REQUIREMENTS:
{json.dumps(input_data, indent=2) if hasattr(input_data, '__dict__') else str(input_data)}

CONTEXT:
{json.dumps(context.user_context, indent=2)}

Provide a JSON response with this structure:
{{
    "required_skills": [
        {{
            "skill": "skill name",
            "category": "technical|business|creative|analytical",
            "importance": "critical|important|nice-to-have",
            "proficiency_level": "beginner|intermediate|advanced|expert"
        }}
    ],
    "skill_gaps": ["identified gaps"],
    "recommendations": ["specific recommendations for skill development or resource allocation"]
}}
"""

    def _get_goal_decomposition_prompt(self, input_data: Any, context: PipelineContext) -> str:
        """Generate prompt for goal decomposition"""
        return f"""
As an expert strategic planner, decompose the following high-level goal into specific, measurable sub-goals.

GOAL TO DECOMPOSE:
{json.dumps(input_data, indent=2) if hasattr(input_data, '__dict__') else str(input_data)}

CONTEXT:
{json.dumps(context.user_context, indent=2)}

Provide a JSON response with this structure:
{{
    "sub_goals": [
        {{
            "title": "Clear sub-goal title",
            "description": "Detailed description",
            "success_metrics": ["measurable outcomes"],
            "timeline": "realistic timeline",
            "dependencies": ["dependencies on other goals"],
            "priority": "high|medium|low"
        }}
    ],
    "success_criteria": ["overall success criteria"],
    "milestones": ["key milestones for tracking progress"]
}}
"""

    def _get_priority_calculation_prompt(self, input_data: Any, context: PipelineContext) -> str:
        """Generate prompt for priority calculation"""
        return f"""
As an expert project manager, calculate the priority for the following item based on business value, urgency, and resource constraints.

ITEM TO PRIORITIZE:
{json.dumps(input_data, indent=2) if hasattr(input_data, '__dict__') else str(input_data)}

CONTEXT:
{json.dumps(context.user_context, indent=2)}

Provide a JSON response with this structure:
{{
    "priority_score": 1-100,
    "factors": {{
        "business_value": 1-10,
        "urgency": 1-10,
        "effort_required": 1-10,
        "risk_level": 1-10,
        "strategic_alignment": 1-10
    }},
    "rationale": "Clear explanation of priority calculation",
    "recommended_action": "immediate|planned|deferred"
}}
"""

    def _get_similarity_matching_prompt(self, input_data: Any, context: PipelineContext) -> str:
        """Generate prompt for similarity matching"""
        return f"""
As an expert data analyst, analyze the semantic similarity between the given items.

ITEMS TO COMPARE:
{json.dumps(input_data, indent=2) if hasattr(input_data, '__dict__') else str(input_data)}

CONTEXT:
{json.dumps(context.user_context, indent=2)}

Provide a JSON response with this structure:
{{
    "similarity_score": 0.0-1.0,
    "similarity_factors": [
        {{
            "factor": "specific similarity aspect",
            "score": 0.0-1.0,
            "explanation": "why this aspect is similar/different"
        }}
    ],
    "overall_assessment": "detailed similarity analysis",
    "recommendation": "merge|keep_separate|partial_overlap"
}}
"""

    def _get_fake_detection_prompt(self, input_data: Any, context: PipelineContext) -> str:
        """Generate prompt for fake detection"""
        return f"""
As an expert content validator, analyze the following content to detect if it contains fake, placeholder, or low-quality information.

CONTENT TO ANALYZE:
{json.dumps(input_data, indent=2) if hasattr(input_data, '__dict__') else str(input_data)}

CONTEXT:
{json.dumps(context.user_context, indent=2)}

Provide a JSON response with this structure:
{{
    "is_fake": true/false,
    "confidence": 0.0-1.0,
    "fake_indicators": [
        {{
            "type": "placeholder|generic|unrealistic|inconsistent",
            "location": "where found",
            "description": "what makes it fake",
            "severity": "low|medium|high"
        }}
    ],
    "quality_score": 0-100,
    "recommendations": ["specific improvements needed"]
}}
"""

    def _get_semantic_analysis_prompt(self, input_data: Any, context: PipelineContext) -> str:
        """Generate prompt for semantic analysis"""
        return f"""
As an expert semantic analyst, perform deep semantic analysis of the following content.

CONTENT TO ANALYZE:
{json.dumps(input_data, indent=2) if hasattr(input_data, '__dict__') else str(input_data)}

CONTEXT:
{json.dumps(context.user_context, indent=2)}

Provide a JSON response with this structure:
{{
    "semantic_themes": ["key themes identified"],
    "intent": "primary intent of the content",
    "sentiment": "positive|negative|neutral",
    "complexity": "simple|medium|complex",
    "key_concepts": [
        {{
            "concept": "concept name",
            "relevance": 0.0-1.0,
            "related_terms": ["related terminology"]
        }}
    ],
    "semantic_relationships": ["relationships between concepts"],
    "recommendations": ["actionable insights from analysis"]
}}
"""

    async def _process_ai_response(self, step_type: PipelineStepType, response: str, context: PipelineContext, start_time: float) -> PipelineResult:
        """Process AI response based on step type"""
        try:
            # Try to parse as JSON first
            if response and response.strip().startswith('{') or response.strip().startswith('['):
                data = json.loads(response)
            else:
                data = {"response": response}
            
            return PipelineResult(
                success=True,
                data=data,
                execution_time=time.time() - start_time,
                retry_count=context.retry_count,
                reasoning=f"AI pipeline step {step_type.value} completed successfully"
            )
        except json.JSONDecodeError:
            # If not valid JSON, return as text
            return PipelineResult(
                success=True,
                data={"response": response},
                execution_time=time.time() - start_time,
                retry_count=context.retry_count,
                metadata={"format": "text"},
                reasoning=f"AI response not JSON, returned as text"
            )
    
    async def _get_cached_result(self, step_type: PipelineStepType, input_data: Any, context: PipelineContext) -> Optional[PipelineResult]:
        """Get cached result if available and valid"""
        cache_key = self._generate_cache_key(step_type, input_data, context)
        
        if cache_key in self.cache:
            cached_entry = self.cache[cache_key]
            
            # Check if cache is still valid
            if time.time() - cached_entry["timestamp"] < self.cache_ttl_seconds:
                cached_result = cached_entry["result"]
                cached_result.cached = True
                return cached_result
            else:
                # Remove expired cache entry
                del self.cache[cache_key]
        
        return None
    
    async def _cache_result(self, step_type: PipelineStepType, input_data: Any, context: PipelineContext, result: PipelineResult):
        """Cache successful result"""
        cache_key = self._generate_cache_key(step_type, input_data, context)
        
        self.cache[cache_key] = {
            "timestamp": time.time(),
            "result": result
        }
        
        # Cleanup old cache entries if cache gets too large
        if len(self.cache) > 1000:
            await self._cleanup_cache()
    
    def _generate_cache_key(self, step_type: PipelineStepType, input_data: Any, context: PipelineContext) -> str:
        """Generate unique cache key for the request"""
        # Create a deterministic hash of the input
        input_str = json.dumps({
            "step_type": step_type.value,
            "input_data": str(input_data),
            "workspace_id": context.workspace_id,
            "goal_id": context.goal_id
        }, sort_keys=True)
        
        return hashlib.md5(input_str.encode()).hexdigest()
    
    async def _cleanup_cache(self):
        """Remove old cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time - entry["timestamp"] > self.cache_ttl_seconds
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        logger.info(f"🧹 Cache cleanup: removed {len(expired_keys)} expired entries")
    
    async def _record_success(self):
        """Record successful request for circuit breaker"""
        if self.circuit_state == CircuitBreakerState.HALF_OPEN:
            self.circuit_state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            logger.info("✅ Circuit breaker back to CLOSED state")
    
    async def _record_failure(self):
        """Record failed request for circuit breaker"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.circuit_breaker_threshold:
            self.circuit_state = CircuitBreakerState.OPEN
            logger.warning(f"🔴 Circuit breaker OPEN after {self.failure_count} failures")
    
    async def _execute_fallback(self, step_type: PipelineStepType, input_data: Any, context: PipelineContext, start_time: float) -> PipelineResult:
        """Execute fallback strategy when AI is unavailable"""
        self.fallback_requests += 1
        
        fallback_responses = {
            PipelineStepType.ASSET_REQUIREMENTS_GENERATION: {
                "requirements": [{
                    "type": "analysis",
                    "title": "System Analysis Required",
                    "description": "Comprehensive analysis needed for goal achievement",
                    "priority": "high",
                    "complexity": "medium",
                    "estimated_effort": "2-4 hours",
                    "dependencies": [],
                    "acceptance_criteria": ["Complete analysis document", "Actionable recommendations"]
                }],
                "success_metrics": ["Analysis completed", "Recommendations provided"],
                "constraints": ["Limited by available information"]
            },
            PipelineStepType.TASK_GENERATION: {
                "tasks": [{
                    "title": "Execute Requirement Analysis",
                    "description": "Analyze and implement the specified requirement",
                    "type": "analysis",
                    "priority": 75,
                    "estimated_duration": "2-3 hours",
                    "required_skills": ["analysis", "problem-solving"],
                    "dependencies": [],
                    "deliverables": ["Analysis report", "Implementation plan"],
                    "acceptance_criteria": ["Clear analysis", "Actionable plan"]
                }]
            },
            PipelineStepType.QUALITY_VALIDATION: {
                "overall_score": 70,
                "quality_metrics": {
                    "completeness": 70,
                    "accuracy": 75,
                    "clarity": 65,
                    "relevance": 80,
                    "actionability": 70
                },
                "issues": [],
                "strengths": ["Addresses core requirements"],
                "recommendations": ["Review and enhance when AI service available"],
                "approval_status": "needs_revision"
            },
            # Legacy compatibility
            PipelineStepType.ASSET_DECOMPOSITION: {
                "requirements": [{
                    "type": "analysis",
                    "title": "System Analysis Required",
                    "description": "Comprehensive analysis needed for goal achievement",
                    "priority": "high",
                    "complexity": "medium",
                    "estimated_effort": "2-4 hours",
                    "dependencies": [],
                    "acceptance_criteria": ["Complete analysis document", "Actionable recommendations"]
                }]
            },
            PipelineStepType.SEMANTIC_SIMILARITY: {
                "similarity_score": 0.5,
                "overall_assessment": "Moderate similarity detected - requires AI analysis when available",
                "recommendation": "keep_separate"
            }
        }
        
        fallback_data = fallback_responses.get(step_type, {"response": "Fallback response - AI service temporarily unavailable"})
        
        return PipelineResult(
            success=True,
            data=fallback_data,
            execution_time=time.time() - start_time,
            fallback_used=True,
            reasoning="Used fallback due to AI unavailability",
            metadata={"source": "fallback", "reason": "ai_unavailable"}
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics"""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "cached_requests": self.cached_requests,
            "fallback_requests": self.fallback_requests,
            "success_rate": self.successful_requests / max(self.total_requests, 1),
            "cache_hit_rate": self.cached_requests / max(self.total_requests, 1),
            "circuit_state": self.circuit_state.value,
            "failure_count": self.failure_count,
            "cache_size": len(self.cache),
            "ai_available": self.ai_available
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            if not self.ai_available:
                return {
                    "status": "degraded",
                    "error": "AI client not available",
                    "circuit_state": self.circuit_state.value,
                    "statistics": self.get_statistics()
                }
            
            # Test a simple AI request
            test_context = PipelineContext(cache_enabled=False, fallback_enabled=False)
            result = await self.execute_pipeline_step(
                PipelineStepType.SEMANTIC_ANALYSIS,
                {"test": "health check"},
                test_context,
                custom_prompt="Respond with: {'status': 'healthy'}"
            )
            
            return {
                "status": "healthy" if result.success else "degraded",
                "circuit_state": self.circuit_state.value,
                "last_error": result.error if not result.success else None,
                "statistics": self.get_statistics()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "circuit_state": self.circuit_state.value,
                "statistics": self.get_statistics()
            }

# Singleton instance for backward compatibility
universal_ai_pipeline_engine = UniversalAIPipelineEngine()
