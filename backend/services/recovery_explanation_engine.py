#!/usr/bin/env python3
"""
🔍 RECOVERY EXPLANATION ENGINE
================================

Provides transparent, human-understandable explanations for all task failure
recovery decisions to achieve 95%+ compliance on the Explainability pillar.

This engine transforms opaque AI-driven recovery processes into clear,
actionable insights for users.
"""

import logging
import re
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Environment configuration
import os
from dotenv import load_dotenv
load_dotenv()

ENABLE_AI_FAILURE_ANALYSIS = os.getenv('ENABLE_AI_FAILURE_ANALYSIS', 'true').lower() == 'true'
ENABLE_AI_EXPLANATIONS = os.getenv('ENABLE_AI_EXPLANATIONS', 'true').lower() == 'true'
RECOVERY_EXPLANATION_DETAIL_LEVEL = os.getenv('RECOVERY_EXPLANATION_DETAIL_LEVEL', 'standard')
ERROR_PATTERN_CONFIDENCE_THRESHOLD = float(os.getenv('ERROR_PATTERN_CONFIDENCE_THRESHOLD', '0.8'))

# Import existing monitoring components
try:
    from task_execution_monitor import ExecutionStage, TaskExecutionTrace
    TASK_MONITOR_AVAILABLE = True
except ImportError:
    TASK_MONITOR_AVAILABLE = False
    ExecutionStage = None

try:
    from workspace_recovery_system import WorkspaceRecoverySystem
    WORKSPACE_RECOVERY_AVAILABLE = True
except ImportError:
    WORKSPACE_RECOVERY_AVAILABLE = False

try:
    from models import TaskStatus, AgentStatus, WorkspaceStatus, HealthStatus
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False

# AI client for complex explanations
AI_CLIENT_AVAILABLE = False
try:
    import openai
    if os.getenv('OPENAI_API_KEY'):
        AI_CLIENT_AVAILABLE = True
        logger.info("✅ OpenAI client available for AI-powered explanations")
except ImportError:
    logger.warning("⚠️ OpenAI client not available")

class FailureCategory(str, Enum):
    """Categorization of failure types based on observed patterns"""
    
    # Technical Failures - AI/SDK Related
    PYDANTIC_VALIDATION_ERROR = "pydantic_validation_error"
    JSON_PARSING_ERROR = "json_parsing_error" 
    OPENAI_API_TIMEOUT = "openai_api_timeout"
    OPENAI_API_RATE_LIMIT = "openai_api_rate_limit"
    OPENAI_SDK_ERROR = "openai_sdk_error"
    OPENAI_CONTENT_FILTER = "openai_content_filter"
    
    # Database and Infrastructure
    DATABASE_CONNECTION_ERROR = "database_connection_error"
    SUPABASE_ERROR = "supabase_error"
    NETWORK_ERROR = "network_error"
    MEMORY_EXHAUSTION = "memory_exhaustion"
    
    # Business Logic Failures
    AGENT_ASSIGNMENT_FAILED = "agent_assignment_failed"
    AGENT_NOT_AVAILABLE = "agent_not_available"
    TASK_DEPENDENCY_MISSING = "task_dependency_missing"
    WORKSPACE_STATE_INVALID = "workspace_state_invalid"
    QUALITY_THRESHOLD_NOT_MET = "quality_threshold_not_met"
    
    # Execution Failures
    TASK_HANGING = "task_hanging"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    INFINITE_LOOP_DETECTED = "infinite_loop_detected"
    EXECUTION_TIMEOUT = "execution_timeout"
    
    # Complex/Unknown
    COMPLEX_MULTI_FACTOR = "complex_multi_factor"
    UNKNOWN_ERROR = "unknown_error"

class RetryRecommendation(str, Enum):
    """Recommendations for retry behavior"""
    IMMEDIATE_RETRY = "immediate_retry"              # Safe to retry immediately
    DELAYED_RETRY_1M = "delayed_retry_1m"           # Retry after 1 minute
    DELAYED_RETRY_5M = "delayed_retry_5m"           # Retry after 5 minutes  
    DELAYED_RETRY_30M = "delayed_retry_30m"         # Retry after 30 minutes
    CONDITIONAL_RETRY = "conditional_retry"          # Retry only if conditions met
    NO_RETRY_TRANSIENT = "no_retry_transient"       # Don't retry, issue will resolve
    NO_RETRY_PERMANENT = "no_retry_permanent"       # Don't retry, requires intervention
    ESCALATE_TO_HUMAN = "escalate_to_human"         # Human intervention needed

class RecoveryStrategy(str, Enum):
    """Available recovery strategies"""
    IMMEDIATE_RETRY = "immediate_retry"
    DELAYED_RETRY = "delayed_retry"
    RETRY_WITH_DIFFERENT_AGENT = "retry_with_different_agent"
    RETRY_WITH_FALLBACK_MODEL = "retry_with_fallback_model"
    RESET_TASK_DEPENDENCIES = "reset_task_dependencies"
    RESTART_WORKSPACE = "restart_workspace"
    ESCALATE_TO_WORKSPACE_RECOVERY = "escalate_to_workspace_recovery"
    MARK_FAILED_NO_RETRY = "mark_failed_no_retry"
    PAUSE_TASK_FOR_MANUAL_REVIEW = "pause_task_for_manual_review"

@dataclass
class ErrorPattern:
    """Pattern matching definition for known errors"""
    pattern: str                                    # Regex pattern
    category: FailureCategory
    is_transient: bool
    retry_recommendation: RetryRecommendation
    explanation_template: str
    user_friendly_cause: str
    confidence_score: float = 0.9
    examples: List[str] = field(default_factory=list)

@dataclass
class FailureContext:
    """Context information about task failure"""
    task_id: str
    workspace_id: str
    agent_id: Optional[str]
    task_name: Optional[str] = None
    error_message: str = ""
    error_type: str = ""
    execution_stage: Optional[str] = None
    attempt_count: int = 1
    failure_timestamp: datetime = field(default_factory=datetime.now)
    execution_metadata: Dict[str, Any] = field(default_factory=dict)
    similar_failures: List[str] = field(default_factory=list)
    stack_trace: Optional[str] = None

@dataclass
class FailureAnalysis:
    """Results of failure analysis"""
    failure_category: FailureCategory
    root_cause: str
    is_transient: bool
    confidence_score: float
    retry_recommendation: RetryRecommendation
    explanation_context: Dict[str, Any]
    matched_pattern: Optional[ErrorPattern] = None
    ai_analysis_used: bool = False

@dataclass
class RecoveryDecision:
    """Decision about how to recover from failure"""
    strategy: RecoveryStrategy
    confidence_score: float
    reasoning: str
    risk_assessment: str
    expected_outcome: str
    estimated_time: Optional[str] = None
    fallback_strategy: Optional[RecoveryStrategy] = None
    requires_user_action: bool = False

@dataclass
class RecoveryExplanation:
    """Complete explanation of recovery decision"""
    task_id: str
    task_name: Optional[str]
    failure_summary: str                    # "Task failed due to missing required fields"
    root_cause: str                        # "Pydantic validation error - agent response incomplete"
    retry_decision: str                    # "Not retrying - requires agent improvement"  
    confidence_explanation: str            # "High confidence (95%) - known pattern"
    user_action_required: Optional[str]    # "Review task requirements with agent"
    estimated_resolution_time: Optional[str]  # "Manual review needed - no ETA"
    
    # Technical details for developers
    technical_details: Dict[str, Any] = field(default_factory=dict)
    error_pattern_matched: Optional[str] = None
    ai_analysis_used: bool = False
    
    # Display formatting
    severity_level: str = "medium"         # "low", "medium", "high", "critical"
    display_category: str = "Unknown Issue"
    
    # Timestamps
    failure_time: datetime = field(default_factory=datetime.now)
    explanation_generated_time: datetime = field(default_factory=datetime.now)

@dataclass
class ExplanationTemplate:
    """Template for generating explanations"""
    failure_summary: str
    root_cause_template: str
    retry_decision_template: str
    user_action_template: Optional[str]
    confidence_explanation: str
    display_category: str
    severity_level: str

class FailureAnalyzer:
    """Categorizes failures and provides retry recommendations"""
    
    def __init__(self):
        self.pattern_matchers = self._initialize_pattern_matchers()
        self.ai_analyzer = AIFailureAnalyzer() if ENABLE_AI_FAILURE_ANALYSIS and AI_CLIENT_AVAILABLE else None
        
    def _initialize_pattern_matchers(self) -> List[ErrorPattern]:
        """Initialize known error patterns based on observed codebase failures"""
        return [
            # Pydantic Validation Errors
            ErrorPattern(
                pattern=r"ValidationError.*field required",
                category=FailureCategory.PYDANTIC_VALIDATION_ERROR,
                is_transient=False,
                retry_recommendation=RetryRecommendation.NO_RETRY_PERMANENT,
                explanation_template="Task output validation failed - missing required fields: {missing_fields}",
                user_friendly_cause="The AI assistant didn't provide all the required information in its response",
                examples=["ValidationError: 1 validation error for TaskOutput\ntitle\n  field required"]
            ),
            
            ErrorPattern(
                pattern=r"ValidationError.*value is not a valid",
                category=FailureCategory.PYDANTIC_VALIDATION_ERROR,
                is_transient=False,
                retry_recommendation=RetryRecommendation.CONDITIONAL_RETRY,
                explanation_template="Task output validation failed - invalid field format: {invalid_fields}",
                user_friendly_cause="The AI assistant provided information in the wrong format"
            ),
            
            # OpenAI API Errors
            ErrorPattern(
                pattern=r"rate_limit_exceeded|RateLimitError",
                category=FailureCategory.OPENAI_API_RATE_LIMIT,
                is_transient=True,
                retry_recommendation=RetryRecommendation.DELAYED_RETRY_5M,
                explanation_template="OpenAI API rate limit reached - will retry in 5 minutes",
                user_friendly_cause="Too many AI requests at once. The system is waiting for capacity to free up",
                confidence_score=0.95
            ),
            
            ErrorPattern(
                pattern=r"timeout.*openai|OpenAI.*timeout|APITimeoutError",
                category=FailureCategory.OPENAI_API_TIMEOUT,
                is_transient=True,
                retry_recommendation=RetryRecommendation.IMMEDIATE_RETRY,
                explanation_template="OpenAI API request timed out - retrying immediately",
                user_friendly_cause="The AI service took too long to respond. Usually resolves on retry"
            ),
            
            ErrorPattern(
                pattern=r"content_filter|ContentFilterError",
                category=FailureCategory.OPENAI_CONTENT_FILTER,
                is_transient=False,
                retry_recommendation=RetryRecommendation.NO_RETRY_PERMANENT,
                explanation_template="Content was filtered by OpenAI safety systems",
                user_friendly_cause="The task content triggered safety filters and cannot be processed"
            ),
            
            # JSON Parsing Errors
            ErrorPattern(
                pattern=r"JSONDecodeError|json.*decode|Invalid JSON",
                category=FailureCategory.JSON_PARSING_ERROR,
                is_transient=False,
                retry_recommendation=RetryRecommendation.CONDITIONAL_RETRY,
                explanation_template="AI response was not valid JSON format",
                user_friendly_cause="The AI assistant didn't format its response correctly"
            ),
            
            # Database Errors  
            ErrorPattern(
                pattern=r"supabase.*error|PostgrestAPIError",
                category=FailureCategory.SUPABASE_ERROR,
                is_transient=True,
                retry_recommendation=RetryRecommendation.DELAYED_RETRY_1M,
                explanation_template="Database connection issue - retrying in 1 minute",
                user_friendly_cause="Temporary database connectivity issue"
            ),
            
            ErrorPattern(
                pattern=r"connection.*refused|ConnectionError|ConnectionRefusedError",
                category=FailureCategory.DATABASE_CONNECTION_ERROR,
                is_transient=True,
                retry_recommendation=RetryRecommendation.DELAYED_RETRY_1M,
                explanation_template="Database connection refused - retrying after brief delay",
                user_friendly_cause="Database server is temporarily unavailable"
            ),
            
            # Agent Assignment Errors
            ErrorPattern(
                pattern=r"No.*agent.*available|agent.*not.*found|AgentNotFoundError",
                category=FailureCategory.AGENT_NOT_AVAILABLE,
                is_transient=True,
                retry_recommendation=RetryRecommendation.DELAYED_RETRY_5M,
                explanation_template="No suitable agent available - waiting for agent to become available",
                user_friendly_cause="All AI assistants are currently busy with other tasks"
            ),
            
            # Execution Timeouts
            ErrorPattern(
                pattern=r"TimeoutError|execution.*timeout|Task.*timed.*out",
                category=FailureCategory.EXECUTION_TIMEOUT,
                is_transient=True,
                retry_recommendation=RetryRecommendation.IMMEDIATE_RETRY,
                explanation_template="Task execution timed out - retrying with fresh context",
                user_friendly_cause="The task took too long to complete, possibly due to system load"
            ),
            
            # Memory Issues
            ErrorPattern(
                pattern=r"MemoryError|out.*of.*memory|memory.*exhausted",
                category=FailureCategory.MEMORY_EXHAUSTION,
                is_transient=True,
                retry_recommendation=RetryRecommendation.DELAYED_RETRY_5M,
                explanation_template="System memory exhausted - waiting for resources to free up",
                user_friendly_cause="The system ran out of available memory. Will retry when resources are available"
            ),
            
            # Network Errors
            ErrorPattern(
                pattern=r"NetworkError|network.*unreachable|ConnectionTimeout",
                category=FailureCategory.NETWORK_ERROR,
                is_transient=True,
                retry_recommendation=RetryRecommendation.DELAYED_RETRY_1M,
                explanation_template="Network connectivity issue - retrying after brief delay",
                user_friendly_cause="Temporary network connectivity problem"
            )
        ]
    
    async def analyze_failure(self, context: FailureContext) -> FailureAnalysis:
        """Analyzes failure and categorizes it"""
        
        # 1. Pattern matching against known errors
        pattern_result = self._match_error_patterns(context)
        
        # 2. AI-driven analysis for complex cases  
        ai_result = None
        if self.ai_analyzer and not pattern_result:
            try:
                ai_result = await self.ai_analyzer.analyze_complex_failure(context)
            except Exception as e:
                logger.warning(f"AI failure analysis failed: {e}")
        
        # 3. Combine results and generate analysis
        return self._synthesize_analysis(pattern_result, ai_result, context)
    
    def _match_error_patterns(self, context: FailureContext) -> Optional[FailureAnalysis]:
        """Match error message against known patterns"""
        error_text = f"{context.error_message} {context.error_type}".lower()
        
        for pattern in self.pattern_matchers:
            if re.search(pattern.pattern.lower(), error_text):
                logger.info(f"🎯 Matched error pattern: {pattern.category.value}")
                
                return FailureAnalysis(
                    failure_category=pattern.category,
                    root_cause=pattern.user_friendly_cause,
                    is_transient=pattern.is_transient,
                    confidence_score=pattern.confidence_score,
                    retry_recommendation=pattern.retry_recommendation,
                    explanation_context={
                        "pattern_matched": pattern.pattern,
                        "error_examples": pattern.examples
                    },
                    matched_pattern=pattern
                )
        
        return None
    
    def _synthesize_analysis(
        self, 
        pattern_result: Optional[FailureAnalysis],
        ai_result: Optional[FailureAnalysis], 
        context: FailureContext
    ) -> FailureAnalysis:
        """Synthesize final analysis from pattern matching and AI analysis"""
        
        # Prefer pattern matching for known issues
        if pattern_result and pattern_result.confidence_score >= ERROR_PATTERN_CONFIDENCE_THRESHOLD:
            return pattern_result
        
        # Use AI analysis if available and confident
        if ai_result and ai_result.confidence_score >= 0.7:
            ai_result.ai_analysis_used = True
            return ai_result
        
        # Fall back to pattern matching even if confidence is lower
        if pattern_result:
            return pattern_result
        
        # Default unknown error analysis
        return FailureAnalysis(
            failure_category=FailureCategory.UNKNOWN_ERROR,
            root_cause=f"Unknown error: {context.error_message[:100]}...",
            is_transient=True,  # Assume transient for safety
            confidence_score=0.3,
            retry_recommendation=RetryRecommendation.DELAYED_RETRY_5M,
            explanation_context={
                "raw_error": context.error_message,
                "error_type": context.error_type
            }
        )

class AIFailureAnalyzer:
    """AI-powered analysis for complex failures"""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY')) if AI_CLIENT_AVAILABLE else None
        
    async def analyze_complex_failure(self, context: FailureContext) -> Optional[FailureAnalysis]:
        """Use AI to analyze complex failures"""
        if not self.client:
            return None
            
        try:
            analysis_prompt = f"""
            Analyze this task failure and categorize it:
            
            Task ID: {context.task_id}
            Task Name: {context.task_name}
            Error Message: {context.error_message}
            Error Type: {context.error_type}
            Execution Stage: {context.execution_stage}
            Attempt Count: {context.attempt_count}
            
            Provide analysis in JSON format:
            {{
                "failure_category": "one of: pydantic_validation_error, json_parsing_error, openai_api_timeout, etc.",
                "root_cause": "brief explanation of what went wrong",
                "is_transient": true/false,
                "confidence_score": 0.0-1.0,
                "retry_recommendation": "immediate_retry, delayed_retry_5m, no_retry_permanent, etc.",
                "reasoning": "why this categorization and recommendation"
            }}
            """
            
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=300,
                temperature=0.1
            )
            
            analysis_json = json.loads(response.choices[0].message.content)
            
            return FailureAnalysis(
                failure_category=FailureCategory(analysis_json["failure_category"]),
                root_cause=analysis_json["root_cause"],
                is_transient=analysis_json["is_transient"],
                confidence_score=analysis_json["confidence_score"],
                retry_recommendation=RetryRecommendation(analysis_json["retry_recommendation"]),
                explanation_context={"ai_reasoning": analysis_json["reasoning"]},
                ai_analysis_used=True
            )
            
        except Exception as e:
            logger.error(f"AI failure analysis error: {e}")
            return None

class RecoveryDecisionEngine:
    """Makes intelligent recovery decisions with full explanations"""
    
    def __init__(self):
        self.recovery_rules = self._initialize_recovery_rules()
        
    async def decide_recovery_strategy(
        self, 
        failure_analysis: FailureAnalysis,
        context: FailureContext
    ) -> RecoveryDecision:
        """Decides on recovery strategy with full reasoning"""
        
        # Map retry recommendation to recovery strategy
        strategy_map = {
            RetryRecommendation.IMMEDIATE_RETRY: RecoveryStrategy.IMMEDIATE_RETRY,
            RetryRecommendation.DELAYED_RETRY_1M: RecoveryStrategy.DELAYED_RETRY,
            RetryRecommendation.DELAYED_RETRY_5M: RecoveryStrategy.DELAYED_RETRY,
            RetryRecommendation.DELAYED_RETRY_30M: RecoveryStrategy.DELAYED_RETRY,
            RetryRecommendation.CONDITIONAL_RETRY: RecoveryStrategy.RETRY_WITH_DIFFERENT_AGENT,
            RetryRecommendation.NO_RETRY_TRANSIENT: RecoveryStrategy.MARK_FAILED_NO_RETRY,
            RetryRecommendation.NO_RETRY_PERMANENT: RecoveryStrategy.PAUSE_TASK_FOR_MANUAL_REVIEW,
            RetryRecommendation.ESCALATE_TO_HUMAN: RecoveryStrategy.PAUSE_TASK_FOR_MANUAL_REVIEW
        }
        
        strategy = strategy_map.get(failure_analysis.retry_recommendation, RecoveryStrategy.DELAYED_RETRY)
        
        # Check for circuit breaker conditions
        if context.attempt_count >= 5:
            strategy = RecoveryStrategy.PAUSE_TASK_FOR_MANUAL_REVIEW
            
        # Generate decision with reasoning
        return RecoveryDecision(
            strategy=strategy,
            confidence_score=failure_analysis.confidence_score,
            reasoning=self._generate_reasoning(failure_analysis, strategy),
            risk_assessment=self._assess_risk(failure_analysis, strategy),
            expected_outcome=self._predict_outcome(failure_analysis, strategy),
            estimated_time=self._estimate_resolution_time(failure_analysis, strategy),
            requires_user_action=strategy in [
                RecoveryStrategy.PAUSE_TASK_FOR_MANUAL_REVIEW,
                RecoveryStrategy.MARK_FAILED_NO_RETRY
            ]
        )
    
    def _generate_reasoning(self, analysis: FailureAnalysis, strategy: RecoveryStrategy) -> str:
        """Generate reasoning for recovery decision"""
        base_reasoning = f"Failure categorized as {analysis.failure_category.value} with {analysis.confidence_score:.0%} confidence."
        
        if strategy == RecoveryStrategy.IMMEDIATE_RETRY:
            return f"{base_reasoning} This is a transient issue that typically resolves on retry."
        elif strategy == RecoveryStrategy.DELAYED_RETRY:
            return f"{base_reasoning} Adding delay to allow system resources to recover."
        elif strategy == RecoveryStrategy.PAUSE_TASK_FOR_MANUAL_REVIEW:
            return f"{base_reasoning} This requires human intervention to resolve."
        else:
            return f"{base_reasoning} Applying standard recovery strategy."
    
    def _assess_risk(self, analysis: FailureAnalysis, strategy: RecoveryStrategy) -> str:
        """Assess risk of recovery strategy"""
        if analysis.is_transient and strategy in [RecoveryStrategy.IMMEDIATE_RETRY, RecoveryStrategy.DELAYED_RETRY]:
            return "Low risk - transient issue with safe retry strategy"
        elif not analysis.is_transient and strategy == RecoveryStrategy.PAUSE_TASK_FOR_MANUAL_REVIEW:
            return "Low risk - permanent issue correctly flagged for manual review"
        else:
            return "Medium risk - strategy may not match failure type"
    
    def _predict_outcome(self, analysis: FailureAnalysis, strategy: RecoveryStrategy) -> str:
        """Predict likely outcome of recovery strategy"""
        if analysis.is_transient and strategy in [RecoveryStrategy.IMMEDIATE_RETRY, RecoveryStrategy.DELAYED_RETRY]:
            return "High likelihood of success on retry"
        elif strategy == RecoveryStrategy.PAUSE_TASK_FOR_MANUAL_REVIEW:
            return "Manual review required - outcome depends on intervention"
        else:
            return "Moderate likelihood of success"
    
    def _estimate_resolution_time(self, analysis: FailureAnalysis, strategy: RecoveryStrategy) -> Optional[str]:
        """Estimate time to resolution"""
        if strategy == RecoveryStrategy.IMMEDIATE_RETRY:
            return "< 1 minute"
        elif strategy == RecoveryStrategy.DELAYED_RETRY:
            return "5-10 minutes"
        elif strategy == RecoveryStrategy.PAUSE_TASK_FOR_MANUAL_REVIEW:
            return "Manual review required - no ETA"
        else:
            return "5-30 minutes"
    
    def _initialize_recovery_rules(self) -> Dict[str, Any]:
        """Initialize recovery decision rules"""
        return {
            "max_retry_attempts": 5,
            "circuit_breaker_threshold": 3,
            "transient_error_retry_delay": 300,  # 5 minutes
            "permanent_error_escalation": True
        }

class ExplanationGenerator:
    """Generates human-friendly explanations"""
    
    def __init__(self):
        self.templates = self._load_explanation_templates()
        
    async def generate_explanation(
        self,
        failure_analysis: FailureAnalysis,
        recovery_decision: RecoveryDecision, 
        context: FailureContext
    ) -> RecoveryExplanation:
        """Generates comprehensive explanation"""
        
        # Get template for failure category
        template = self.templates.get(failure_analysis.failure_category)
        
        if template:
            return self._apply_template(template, failure_analysis, recovery_decision, context)
        else:
            return self._generate_generic_explanation(failure_analysis, recovery_decision, context)
    
    def _apply_template(
        self,
        template: ExplanationTemplate,
        analysis: FailureAnalysis,
        decision: RecoveryDecision,
        context: FailureContext
    ) -> RecoveryExplanation:
        """Apply explanation template"""
        
        return RecoveryExplanation(
            task_id=context.task_id,
            task_name=context.task_name,
            failure_summary=template.failure_summary,
            root_cause=template.root_cause_template.format(
                error_message=context.error_message[:100],
                missing_fields="unknown"  # Could be extracted from error
            ),
            retry_decision=template.retry_decision_template.format(
                retry_delay=decision.estimated_time or "unknown"
            ),
            confidence_explanation=f"{template.confidence_explanation} ({analysis.confidence_score:.0%} confidence)",
            user_action_required=template.user_action_template,
            estimated_resolution_time=decision.estimated_time,
            technical_details={
                "failure_category": analysis.failure_category.value,
                "error_message": context.error_message,
                "attempt_count": context.attempt_count,
                "recovery_strategy": decision.strategy.value
            },
            error_pattern_matched=analysis.matched_pattern.pattern if analysis.matched_pattern else None,
            ai_analysis_used=analysis.ai_analysis_used,
            severity_level=template.severity_level,
            display_category=template.display_category
        )
    
    def _generate_generic_explanation(
        self,
        analysis: FailureAnalysis, 
        decision: RecoveryDecision,
        context: FailureContext
    ) -> RecoveryExplanation:
        """Generate generic explanation for unknown patterns"""
        
        return RecoveryExplanation(
            task_id=context.task_id,
            task_name=context.task_name,
            failure_summary="Task execution failed",
            root_cause=analysis.root_cause,
            retry_decision=decision.reasoning,
            confidence_explanation=f"Analysis confidence: {analysis.confidence_score:.0%}",
            user_action_required="Monitor task progress" if decision.requires_user_action else None,
            estimated_resolution_time=decision.estimated_time,
            technical_details={
                "failure_category": analysis.failure_category.value,
                "error_message": context.error_message,
                "recovery_strategy": decision.strategy.value
            },
            ai_analysis_used=analysis.ai_analysis_used,
            severity_level="medium",
            display_category="System Issue"
        )
    
    def _load_explanation_templates(self) -> Dict[FailureCategory, ExplanationTemplate]:
        """Load human-friendly explanation templates"""
        return {
            FailureCategory.PYDANTIC_VALIDATION_ERROR: ExplanationTemplate(
                failure_summary="Task output validation failed",
                root_cause_template="The AI assistant's response was missing required information or had incorrect formatting",
                retry_decision_template="Not retrying automatically - the agent needs to provide complete information",
                user_action_template="Review the task requirements and ensure the agent understands what information is needed",
                confidence_explanation="High confidence - this is a known validation pattern",
                display_category="Agent Response Issue", 
                severity_level="medium"
            ),
            
            FailureCategory.OPENAI_API_RATE_LIMIT: ExplanationTemplate(
                failure_summary="AI service rate limit reached",
                root_cause_template="Too many requests to OpenAI API in a short time",
                retry_decision_template="Automatically retrying in {retry_delay} - this usually resolves quickly",
                user_action_template=None,  # No user action needed
                confidence_explanation="High confidence - standard rate limiting behavior",
                display_category="Temporary Service Issue",
                severity_level="low"
            ),
            
            FailureCategory.OPENAI_API_TIMEOUT: ExplanationTemplate(
                failure_summary="AI service timeout", 
                root_cause_template="OpenAI API request timed out due to high load or connectivity issues",
                retry_decision_template="Retrying immediately - timeouts usually resolve quickly",
                user_action_template=None,
                confidence_explanation="High confidence - known timeout pattern",
                display_category="Temporary Service Issue",
                severity_level="low"
            ),
            
            FailureCategory.JSON_PARSING_ERROR: ExplanationTemplate(
                failure_summary="Invalid AI response format",
                root_cause_template="AI response was not properly formatted JSON",
                retry_decision_template="Trying with a different agent - formatting issues often resolve with retry",
                user_action_template="If this persists, review the task instructions for clarity",
                confidence_explanation="High confidence - known formatting issue",
                display_category="Agent Response Issue",
                severity_level="medium"
            ),
            
            FailureCategory.AGENT_NOT_AVAILABLE: ExplanationTemplate(
                failure_summary="No AI assistants available",
                root_cause_template="All suitable AI assistants are currently busy with other tasks",
                retry_decision_template="Waiting for an assistant to become available - will retry in {retry_delay}",
                user_action_template=None,
                confidence_explanation="High confidence - resource availability issue",
                display_category="Resource Availability",
                severity_level="low"
            ),
            
            FailureCategory.DATABASE_CONNECTION_ERROR: ExplanationTemplate(
                failure_summary="Database connectivity issue",
                root_cause_template="Temporary connection problem with the database",
                retry_decision_template="Retrying after brief delay - connectivity issues usually resolve quickly",
                user_action_template=None,
                confidence_explanation="High confidence - known infrastructure issue",
                display_category="System Infrastructure",
                severity_level="low"
            )
        }

class RecoveryExplanationEngine:
    """
    🔍 EXPLAINABLE RECOVERY ENGINE
    
    Main engine that coordinates failure analysis, recovery decisions,
    and explanation generation to achieve 95%+ explainability compliance.
    """
    
    def __init__(self):
        self.failure_analyzer = FailureAnalyzer()
        self.decision_engine = RecoveryDecisionEngine()
        self.explanation_generator = ExplanationGenerator()
        
        # Statistics tracking
        self.explanations_generated = 0
        self.pattern_matches = 0
        self.ai_analyses_used = 0
        
        logger.info("🔍 RecoveryExplanationEngine initialized")
    
    async def explain_recovery_decision(
        self,
        task_id: str,
        workspace_id: str,
        error_message: str,
        error_type: str = "",
        agent_id: Optional[str] = None,
        task_name: Optional[str] = None,
        execution_stage: Optional[str] = None,
        attempt_count: int = 1,
        execution_metadata: Optional[Dict[str, Any]] = None
    ) -> RecoveryExplanation:
        """Main entry point for recovery explanation generation"""
        
        # Create failure context
        context = FailureContext(
            task_id=task_id,
            workspace_id=workspace_id,
            agent_id=agent_id,
            task_name=task_name,
            error_message=error_message,
            error_type=error_type,
            execution_stage=execution_stage,
            attempt_count=attempt_count,
            execution_metadata=execution_metadata or {}
        )
        
        try:
            # Analyze the failure
            failure_analysis = await self.failure_analyzer.analyze_failure(context)
            
            # Make recovery decision
            recovery_decision = await self.decision_engine.decide_recovery_strategy(
                failure_analysis, context
            )
            
            # Generate explanation
            explanation = await self.explanation_generator.generate_explanation(
                failure_analysis, recovery_decision, context
            )
            
            # Update statistics
            self.explanations_generated += 1
            if failure_analysis.matched_pattern:
                self.pattern_matches += 1
            if failure_analysis.ai_analysis_used:
                self.ai_analyses_used += 1
                
            logger.info(f"✅ Generated recovery explanation for task {task_id} "
                       f"(category: {failure_analysis.failure_category.value}, "
                       f"confidence: {failure_analysis.confidence_score:.0%})")
            
            return explanation
            
        except Exception as e:
            logger.error(f"❌ Failed to generate recovery explanation for task {task_id}: {e}")
            
            # Return minimal explanation as fallback
            return RecoveryExplanation(
                task_id=task_id,
                task_name=task_name,
                failure_summary="Task execution failed",
                root_cause=f"Error: {error_message[:100]}...",
                retry_decision="System will determine appropriate retry strategy",
                confidence_explanation="Low confidence - explanation generation failed",
                technical_details={
                    "explanation_error": str(e),
                    "original_error": error_message
                },
                severity_level="medium",
                display_category="System Issue"
            )
    
    async def get_explanation_stats(self) -> Dict[str, Any]:
        """Get statistics about explanation generation"""
        return {
            "explanations_generated": self.explanations_generated,
            "pattern_matches": self.pattern_matches,
            "ai_analyses_used": self.ai_analyses_used,
            "pattern_match_rate": self.pattern_matches / max(1, self.explanations_generated),
            "ai_analysis_rate": self.ai_analyses_used / max(1, self.explanations_generated)
        }

# Singleton instance
recovery_explanation_engine = RecoveryExplanationEngine()

# Convenience functions for easy integration
async def explain_task_failure(
    task_id: str,
    workspace_id: str, 
    error_message: str,
    **kwargs
) -> RecoveryExplanation:
    """Convenient wrapper for task failure explanation"""
    return await recovery_explanation_engine.explain_recovery_decision(
        task_id=task_id,
        workspace_id=workspace_id,
        error_message=error_message,
        **kwargs
    )

def get_explanation_stats() -> Dict[str, Any]:
    """Get explanation engine statistics"""
    return asyncio.run(recovery_explanation_engine.get_explanation_stats())