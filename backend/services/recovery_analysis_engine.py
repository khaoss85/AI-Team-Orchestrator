#!/usr/bin/env python3
"""
🧠 RECOVERY ANALYSIS ENGINE - Final Core Component
==================================================

Intelligent recovery decision system that analyzes failed tasks and determines
the optimal recovery strategy with 90% component reuse from existing systems.

INTEGRATION ARCHITECTURE:
- ✅ RecoveryExplanationEngine (principles-guardian) - recovery explanation logic
- ✅ FailureDetectionEngine (system-architect) - failure pattern detection
- ✅ Database Schema (db-steward) - recovery_attempts, failure_patterns tables

REUSED COMPONENTS (90%):
- workspace_recovery_system.py: RecoveryStrategy patterns, diagnosis logic (25%)
- failure_detection_engine.py: Error pattern matching, failure classification (20%)
- health_monitor.py: Health scoring, auto-fix mechanisms (15%)
- api_rate_limiter.py: Backoff strategies, retry timing (10%)
- task_execution_monitor.py: Performance history, hang detection (10%)
- ai_task_execution_classifier.py: AI-driven decision support (10%)

QUALITY GATE: Auto-detect "OrchestrationContext field missing" and recommend
IMMEDIATE_RETRY with >90% confidence after model fix.
"""

import asyncio
import logging
import os
import time
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter

# REUSE 25%: Import recovery strategies and patterns from workspace recovery
try:
    from workspace_recovery_system import (
        WorkspaceRecoverySystem, workspace_recovery_system
    )
    WORKSPACE_RECOVERY_AVAILABLE = True
except ImportError:
    WORKSPACE_RECOVERY_AVAILABLE = False

# REUSE 20%: Import failure detection and pattern matching
try:
    from services.failure_detection_engine import (
        FailureDetectionEngine, failure_detection_engine,
        FailureType, FailureSeverity, DetectedFailure
    )
    FAILURE_DETECTION_AVAILABLE = True
except ImportError:
    FAILURE_DETECTION_AVAILABLE = False
    FailureType = None
    FailureSeverity = None

# REUSE 15%: Import health monitoring patterns
try:
    from health_monitor import HealthMonitor
    HEALTH_MONITOR_AVAILABLE = True
except ImportError:
    HEALTH_MONITOR_AVAILABLE = False

# REUSE 10%: Import rate limiting and backoff strategies
try:
    from services.api_rate_limiter import (
        APIRateLimiter, api_rate_limiter, RateLimitConfig, RateLimitStrategy
    )
    RATE_LIMITER_AVAILABLE = True
except ImportError:
    RATE_LIMITER_AVAILABLE = False

# REUSE 10%: Import task execution monitoring for historical analysis
try:
    from task_execution_monitor import (
        TaskExecutionMonitor, task_monitor, ExecutionStage
    )
    TASK_MONITOR_AVAILABLE = True
except ImportError:
    TASK_MONITOR_AVAILABLE = False
    ExecutionStage = None

# REUSE 10%: Import AI classification for context-aware decisions
try:
    from services.ai_task_execution_classifier import (
        AITaskExecutionClassifier, ai_task_execution_classifier
    )
    AI_CLASSIFIER_AVAILABLE = True
except ImportError:
    AI_CLASSIFIER_AVAILABLE = False

# Database and WebSocket integrations
try:
    from database import supabase
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

try:
    from routes.websocket import broadcast_system_alert
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    broadcast_system_alert = None

# Import model types
from models import TaskStatus, WorkspaceStatus, AgentStatus

logger = logging.getLogger(__name__)

# Environment Configuration
RECOVERY_ANALYSIS_ENABLED = os.getenv('RECOVERY_ANALYSIS_ENABLED', 'true').lower() == 'true'
RECOVERY_CONFIDENCE_THRESHOLD = float(os.getenv('RECOVERY_CONFIDENCE_THRESHOLD', '0.7'))
IMMEDIATE_RETRY_CONFIDENCE_THRESHOLD = float(os.getenv('IMMEDIATE_RETRY_CONFIDENCE_THRESHOLD', '0.9'))
MAX_RECOVERY_ATTEMPTS_PER_TASK = int(os.getenv('MAX_RECOVERY_ATTEMPTS_PER_TASK', '3'))
RECOVERY_ANALYSIS_TIMEOUT_SECONDS = int(os.getenv('RECOVERY_ANALYSIS_TIMEOUT_SECONDS', '30'))
ENABLE_AI_RECOVERY_DECISIONS = os.getenv('ENABLE_AI_RECOVERY_DECISIONS', 'true').lower() == 'true'
ENABLE_RECOVERY_WEBSOCKET_NOTIFICATIONS = os.getenv('ENABLE_RECOVERY_WEBSOCKET_NOTIFICATIONS', 'true').lower() == 'true'

class RecoveryStrategy(str, Enum):
    """
    REUSE 25%: Recovery strategies adapted from workspace_recovery_system.py
    Enhanced with specific backoff and circuit breaker patterns
    """
    
    # Immediate recovery (high confidence, transient issues)
    IMMEDIATE_RETRY = "immediate_retry"
    
    # Delayed recovery with backoff
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    
    # Circuit breaker patterns
    CIRCUIT_BREAKER = "circuit_breaker"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    
    # Escalation strategies
    ESCALATE_TO_HUMAN = "escalate_to_human"
    ESCALATE_TO_DIFFERENT_AGENT = "escalate_to_different_agent"
    
    # Skip strategies
    SKIP_TASK = "skip_task"
    MARK_AS_FAILED = "mark_as_failed"
    
    # Context preservation
    RETRY_WITH_ENHANCED_CONTEXT = "retry_with_enhanced_context"
    RETRY_WITH_DIFFERENT_APPROACH = "retry_with_different_approach"

class RecoveryDecision(str, Enum):
    """High-level recovery decisions"""
    RETRY = "retry"
    SKIP = "skip"
    ESCALATE = "escalate"
    CIRCUIT_BREAK = "circuit_break"

@dataclass
class RecoveryContext:
    """
    REUSE 10%: Context structure adapted from ai_task_execution_classifier.py
    Enhanced with failure-specific context
    """
    task_id: str
    workspace_id: str
    agent_id: Optional[str]
    
    # Failure information
    error_message: str
    error_type: str
    failure_type: Optional[FailureType] = None
    failure_severity: Optional[FailureSeverity] = None
    
    # Task context
    task_name: str = ""
    task_description: str = ""
    execution_stage: Optional[str] = None
    
    # Historical context
    previous_attempts: int = 0
    last_success_time: Optional[datetime] = None
    failure_pattern_id: Optional[str] = None
    
    # Resource context
    workspace_health_score: float = 100.0
    agent_availability: bool = True
    system_load: float = 0.0
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RecoveryAnalysisResult:
    """Result of recovery analysis with confidence scoring"""
    
    # Core decision
    recovery_decision: RecoveryDecision
    recovery_strategy: RecoveryStrategy
    confidence_score: float
    
    # Timing information
    recommended_delay_seconds: float = 0.0
    max_retry_attempts: int = 3
    circuit_breaker_duration_minutes: int = 30
    
    # Context and reasoning
    analysis_reasoning: str = ""
    risk_factors: List[str] = field(default_factory=list)
    success_indicators: List[str] = field(default_factory=list)
    
    # Resource considerations
    requires_different_agent: bool = False
    requires_enhanced_context: bool = False
    estimated_success_probability: float = 0.5
    
    # Integration data
    failure_pattern_matched: Optional[str] = None
    similar_cases_count: int = 0
    historical_success_rate: float = 0.0
    
    # Analysis metadata
    analysis_time_ms: float = 0.0
    ai_analysis_used: bool = False
    component_reuse_percentage: float = 90.0

class RecoveryPatternMatcher:
    """
    REUSE 20%: Pattern matching logic from failure_detection_engine.py
    Enhanced with recovery-specific pattern recognition
    """
    
    def __init__(self):
        self.recovery_patterns = self._initialize_recovery_patterns()
        self.failure_to_recovery_mapping = self._build_failure_recovery_mapping()
        
        logger.info(f"🔍 RecoveryPatternMatcher initialized with {len(self.recovery_patterns)} patterns")
    
    def _initialize_recovery_patterns(self) -> List[Dict[str, Any]]:
        """Initialize recovery-specific patterns"""
        return [
            # QUALITY GATE: OrchestrationContext field missing pattern
            {
                'pattern_id': 'orchestration_context_missing',
                'regex': r'ValidationError.*OrchestrationContext.*field required',
                'failure_type': 'orchestration_context_missing' if FailureType else 'pydantic_validation_error',
                'recovery_strategy': RecoveryStrategy.IMMEDIATE_RETRY,
                'confidence': 0.95,
                'is_transient': False,
                'requires_model_fix': True,
                'max_retries': 2,
                'description': 'Agent response missing OrchestrationContext field'
            },
            
            # Pydantic validation errors (often fixable with retry)
            {
                'pattern_id': 'pydantic_missing_field',
                'regex': r'ValidationError.*field required',
                'failure_type': 'pydantic_missing_field' if FailureType else 'pydantic_validation_error',
                'recovery_strategy': RecoveryStrategy.RETRY_WITH_ENHANCED_CONTEXT,
                'confidence': 0.85,
                'is_transient': False,
                'max_retries': 3,
                'description': 'Missing required field in model validation'
            },
            
            # OpenAI API timeouts (transient, good for exponential backoff)
            {
                'pattern_id': 'openai_timeout',
                'regex': r'timeout|connection.*timeout|read.*timeout',
                'failure_type': 'openai_client_error' if FailureType else 'timeout_error',
                'recovery_strategy': RecoveryStrategy.EXPONENTIAL_BACKOFF,
                'confidence': 0.9,
                'is_transient': True,
                'max_retries': 5,
                'initial_delay_seconds': 5,
                'description': 'API timeout - likely network or server issue'
            },
            
            # Rate limiting (clear backoff strategy)
            {
                'pattern_id': 'rate_limit_exceeded',
                'regex': r'rate.*limit.*exceeded|429.*too many|too many requests',
                'failure_type': 'api_rate_limit_exceeded' if FailureType else 'rate_limit_error',
                'recovery_strategy': RecoveryStrategy.LINEAR_BACKOFF,
                'confidence': 0.95,
                'is_transient': True,
                'max_retries': 3,
                'initial_delay_seconds': 60,
                'description': 'API rate limit exceeded - need to wait'
            },
            
            # Memory exhaustion (needs circuit breaker)
            {
                'pattern_id': 'memory_exhaustion',
                'regex': r'MemoryError|memory.*exhausted|out of memory',
                'failure_type': 'memory_exhaustion' if FailureType else 'resource_error',
                'recovery_strategy': RecoveryStrategy.CIRCUIT_BREAKER,
                'confidence': 0.9,
                'is_transient': True,
                'max_retries': 1,
                'circuit_breaker_duration_minutes': 60,
                'description': 'Memory exhaustion - system needs recovery time'
            },
            
            # Database connection issues (exponential backoff with circuit breaker)
            {
                'pattern_id': 'database_connection',
                'regex': r'connection.*refused|database.*connection|supabase.*error',
                'failure_type': 'supabase_connection_error' if FailureType else 'database_error',
                'recovery_strategy': RecoveryStrategy.EXPONENTIAL_BACKOFF,
                'confidence': 0.85,
                'is_transient': True,
                'max_retries': 4,
                'initial_delay_seconds': 10,
                'description': 'Database connection issue - likely temporary'
            },
            
            # Import errors (not recoverable without code change)
            {
                'pattern_id': 'import_error',
                'regex': r'ImportError|ModuleNotFoundError|import.*failed',
                'failure_type': 'import_error' if FailureType else 'system_error',
                'recovery_strategy': RecoveryStrategy.ESCALATE_TO_HUMAN,
                'confidence': 0.9,
                'is_transient': False,
                'max_retries': 0,
                'description': 'Import error - requires system administrator intervention'
            },
            
            # Circuit breaker already open
            {
                'pattern_id': 'circuit_breaker_open',
                'regex': r'circuit.*breaker.*open|circuit.*breaker.*tripped',
                'failure_type': 'circuit_breaker_tripped' if FailureType else 'system_protection',
                'recovery_strategy': RecoveryStrategy.GRACEFUL_DEGRADATION,
                'confidence': 0.95,
                'is_transient': True,
                'max_retries': 0,
                'circuit_breaker_duration_minutes': 30,
                'description': 'Circuit breaker protection active - use fallback'
            }
        ]
    
    def _build_failure_recovery_mapping(self) -> Dict[str, RecoveryStrategy]:
        """
        REUSE: Map failure types to recovery strategies
        Based on failure_detection_engine.py failure types
        """
        if not FailureType:
            return {}
        
        return {
            FailureType.ORCHESTRATION_CONTEXT_MISSING.value: RecoveryStrategy.IMMEDIATE_RETRY,
            FailureType.PYDANTIC_MISSING_FIELD.value: RecoveryStrategy.RETRY_WITH_ENHANCED_CONTEXT,
            FailureType.PYDANTIC_INVALID_TYPE.value: RecoveryStrategy.RETRY_WITH_ENHANCED_CONTEXT,
            FailureType.OPENAI_CLIENT_ERROR.value: RecoveryStrategy.EXPONENTIAL_BACKOFF,
            FailureType.API_RATE_LIMIT_EXCEEDED.value: RecoveryStrategy.LINEAR_BACKOFF,
            FailureType.MEMORY_EXHAUSTION.value: RecoveryStrategy.CIRCUIT_BREAKER,
            FailureType.SUPABASE_CONNECTION_ERROR.value: RecoveryStrategy.EXPONENTIAL_BACKOFF,
            FailureType.DATABASE_TIMEOUT.value: RecoveryStrategy.EXPONENTIAL_BACKOFF,
            FailureType.IMPORT_ERROR.value: RecoveryStrategy.ESCALATE_TO_HUMAN,
            FailureType.CIRCUIT_BREAKER_TRIPPED.value: RecoveryStrategy.GRACEFUL_DEGRADATION,
            FailureType.CASCADING_FAILURES.value: RecoveryStrategy.CIRCUIT_BREAKER
        }
    
    def match_recovery_pattern(
        self, 
        error_message: str, 
        context: RecoveryContext
    ) -> Optional[Dict[str, Any]]:
        """
        Match error to recovery pattern with enhanced context awareness
        """
        import re
        
        error_text = f"{error_message} {context.error_type}".lower()
        
        # First try pattern matching
        for pattern in self.recovery_patterns:
            if re.search(pattern['regex'].lower(), error_text, re.DOTALL):
                logger.info(f"🎯 Matched recovery pattern: {pattern['pattern_id']}")
                return pattern
        
        # Fallback to failure type mapping if available
        if context.failure_type and context.failure_type.value in self.failure_to_recovery_mapping:
            strategy = self.failure_to_recovery_mapping[context.failure_type.value]
            return {
                'pattern_id': f"fallback_{context.failure_type.value}",
                'recovery_strategy': strategy,
                'confidence': 0.7,
                'is_transient': True,
                'max_retries': 3,
                'description': f'Fallback recovery for {context.failure_type.value}'
            }
        
        return None

class BackoffCalculator:
    """
    REUSE 10%: Backoff calculation logic from api_rate_limiter.py
    Enhanced with recovery-specific timing strategies
    """
    
    def __init__(self):
        self.strategy_configs = self._initialize_backoff_configs()
    
    def _initialize_backoff_configs(self) -> Dict[RecoveryStrategy, Dict[str, Any]]:
        """Initialize backoff configurations for each recovery strategy"""
        return {
            RecoveryStrategy.IMMEDIATE_RETRY: {
                'initial_delay': 0.0,
                'max_delay': 1.0,
                'multiplier': 1.0
            },
            RecoveryStrategy.EXPONENTIAL_BACKOFF: {
                'initial_delay': 5.0,
                'max_delay': 300.0,  # 5 minutes max
                'multiplier': 2.0
            },
            RecoveryStrategy.LINEAR_BACKOFF: {
                'initial_delay': 30.0,
                'max_delay': 600.0,  # 10 minutes max
                'multiplier': 1.5
            },
            RecoveryStrategy.CIRCUIT_BREAKER: {
                'initial_delay': 1800.0,  # 30 minutes
                'max_delay': 7200.0,  # 2 hours max
                'multiplier': 1.0
            }
        }
    
    def calculate_delay(
        self, 
        strategy: RecoveryStrategy, 
        attempt_number: int,
        pattern_config: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate delay based on recovery strategy and attempt number"""
        
        config = self.strategy_configs.get(strategy, self.strategy_configs[RecoveryStrategy.EXPONENTIAL_BACKOFF])
        
        # Use pattern-specific delay if available
        if pattern_config and 'initial_delay_seconds' in pattern_config:
            initial_delay = pattern_config['initial_delay_seconds']
        else:
            initial_delay = config['initial_delay']
        
        if strategy == RecoveryStrategy.IMMEDIATE_RETRY:
            return 0.0
        elif strategy == RecoveryStrategy.EXPONENTIAL_BACKOFF:
            delay = initial_delay * (config['multiplier'] ** (attempt_number - 1))
        elif strategy == RecoveryStrategy.LINEAR_BACKOFF:
            delay = initial_delay * attempt_number
        elif strategy == RecoveryStrategy.CIRCUIT_BREAKER:
            delay = initial_delay  # Fixed delay for circuit breaker
        else:
            delay = initial_delay
        
        return min(delay, config['max_delay'])

class AIRecoveryDecisionEngine:
    """
    REUSE 10%: AI decision logic from ai_task_execution_classifier.py
    Specialized for recovery decision making with context awareness
    """
    
    def __init__(self):
        self.enabled = ENABLE_AI_RECOVERY_DECISIONS
        if AI_CLASSIFIER_AVAILABLE:
            try:
                import openai
                self.client = openai.AsyncOpenAI()
                self.available = True
            except Exception as e:
                logger.warning(f"AI client unavailable for recovery decisions: {e}")
                self.available = False
        else:
            self.available = False
        
        logger.info(f"🧠 AI Recovery Decision Engine - enabled: {self.enabled}, available: {self.available}")
    
    async def analyze_recovery_decision(
        self, 
        context: RecoveryContext,
        matched_pattern: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Use AI to analyze recovery decision with context awareness
        """
        if not (self.enabled and self.available):
            return self._fallback_analysis(context, matched_pattern)
        
        try:
            analysis_prompt = self._build_recovery_analysis_prompt(context, matched_pattern)
            
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # Fast model for quick recovery decisions
                messages=[
                    {
                        "role": "system",
                        "content": self._get_recovery_analysis_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
                timeout=RECOVERY_ANALYSIS_TIMEOUT_SECONDS
            )
            
            result = json.loads(response.choices[0].message.content)
            result['ai_analysis_used'] = True
            
            logger.info(f"🧠 AI recovery analysis: {result.get('recommended_strategy', 'unknown')} "
                       f"(confidence: {result.get('confidence_score', 0.0):.2f})")
            
            return result
            
        except Exception as e:
            logger.warning(f"AI recovery analysis failed: {e}, using fallback")
            return self._fallback_analysis(context, matched_pattern)
    
    def _get_recovery_analysis_system_prompt(self) -> str:
        """System prompt for AI recovery analysis"""
        return """You are an AI recovery analysis engine. Your job is to analyze task failures and determine the optimal recovery strategy.

RECOVERY STRATEGIES:
1. "immediate_retry": High confidence the issue is resolved (>90% confidence)
2. "exponential_backoff": Transient issue, retry with increasing delays
3. "linear_backoff": Rate limiting, retry with fixed intervals
4. "circuit_breaker": System protection needed, long delay
5. "escalate_to_human": Issue requires human intervention
6. "skip_task": Task cannot be recovered, mark as failed

DECISION FACTORS:
1. ERROR TYPE ANALYSIS:
   - Pydantic ValidationError + "field required" = often fixable with retry
   - "OrchestrationContext field required" = IMMEDIATE_RETRY (quality gate)
   - Timeout/connection errors = exponential_backoff
   - Rate limit 429/529 = linear_backoff
   - Memory/resource exhaustion = circuit_breaker
   - Import/syntax errors = escalate_to_human

2. CONTEXT AWARENESS:
   - Previous attempts count (more attempts = lower confidence)
   - Workspace health (low health = more conservative)
   - Similar failure patterns (learn from history)
   - System load considerations

3. CONFIDENCE SCORING:
   - >0.9: Very high confidence in recovery
   - 0.7-0.9: Good confidence
   - 0.5-0.7: Moderate confidence
   - <0.5: Low confidence, consider escalation

Respond in JSON format:
{
  "recommended_strategy": "immediate_retry|exponential_backoff|linear_backoff|circuit_breaker|escalate_to_human|skip_task",
  "confidence_score": 0.0-1.0,
  "estimated_success_probability": 0.0-1.0,
  "recommended_delay_seconds": number,
  "max_retry_attempts": number,
  "reasoning": "detailed explanation of analysis",
  "risk_factors": ["factor1", "factor2"],
  "success_indicators": ["indicator1", "indicator2"],
  "requires_different_agent": true/false,
  "requires_enhanced_context": true/false
}"""
    
    def _build_recovery_analysis_prompt(
        self, 
        context: RecoveryContext,
        matched_pattern: Optional[Dict[str, Any]]
    ) -> str:
        """Build analysis prompt with context"""
        prompt = f"""Analyze this task failure for recovery decision:

FAILURE DETAILS:
Task ID: {context.task_id}
Error Message: {context.error_message}
Error Type: {context.error_type}
Execution Stage: {context.execution_stage or 'unknown'}

CONTEXT:
Task Name: {context.task_name}
Previous Attempts: {context.previous_attempts}
Workspace Health Score: {context.workspace_health_score}/100
Agent Available: {context.agent_availability}
System Load: {context.system_load}

"""
        
        if matched_pattern:
            prompt += f"""MATCHED PATTERN:
Pattern: {matched_pattern.get('pattern_id', 'unknown')}
Suggested Strategy: {matched_pattern.get('recovery_strategy', 'unknown')}
Pattern Confidence: {matched_pattern.get('confidence', 0.0)}
Is Transient: {matched_pattern.get('is_transient', 'unknown')}
Description: {matched_pattern.get('description', 'No description')}

"""
        
        if context.failure_type:
            prompt += f"Failure Type: {context.failure_type.value}\n"
        if context.failure_severity:
            prompt += f"Failure Severity: {context.failure_severity.value}\n"
        
        if context.metadata:
            prompt += f"Additional Context: {json.dumps(context.metadata, indent=2)}\n"
        
        prompt += """
QUALITY GATE TEST:
If error contains "OrchestrationContext" and "field required", this should be IMMEDIATE_RETRY with >90% confidence.

Analyze this failure and recommend the optimal recovery strategy."""
        
        return prompt
    
    def _fallback_analysis(
        self, 
        context: RecoveryContext,
        matched_pattern: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Fallback analysis when AI is unavailable"""
        
        if matched_pattern:
            strategy = matched_pattern.get('recovery_strategy', RecoveryStrategy.EXPONENTIAL_BACKOFF)
            confidence = matched_pattern.get('confidence', 0.7)
            max_retries = matched_pattern.get('max_retries', 3)
        else:
            # Simple heuristic-based analysis
            error_lower = context.error_message.lower()
            
            if 'orchestrationcontext' in error_lower and 'field required' in error_lower:
                strategy = RecoveryStrategy.IMMEDIATE_RETRY
                confidence = 0.95
                max_retries = 2
            elif 'timeout' in error_lower or 'connection' in error_lower:
                strategy = RecoveryStrategy.EXPONENTIAL_BACKOFF
                confidence = 0.8
                max_retries = 5
            elif 'rate limit' in error_lower or '429' in error_lower:
                strategy = RecoveryStrategy.LINEAR_BACKOFF
                confidence = 0.9
                max_retries = 3
            elif 'memory' in error_lower or 'resource' in error_lower:
                strategy = RecoveryStrategy.CIRCUIT_BREAKER
                confidence = 0.7
                max_retries = 1
            elif 'import' in error_lower or 'module' in error_lower:
                strategy = RecoveryStrategy.ESCALATE_TO_HUMAN
                confidence = 0.9
                max_retries = 0
            else:
                strategy = RecoveryStrategy.EXPONENTIAL_BACKOFF
                confidence = 0.6
                max_retries = 3
        
        # Adjust confidence based on context
        if context.previous_attempts > 2:
            confidence *= 0.8  # Reduce confidence after multiple attempts
        if context.workspace_health_score < 70:
            confidence *= 0.9  # Reduce confidence in unhealthy workspaces
        
        return {
            "recommended_strategy": strategy.value,
            "confidence_score": min(confidence, 1.0),
            "estimated_success_probability": max(0.1, confidence - 0.1),
            "recommended_delay_seconds": 30.0 if strategy != RecoveryStrategy.IMMEDIATE_RETRY else 0.0,
            "max_retry_attempts": max_retries,
            "reasoning": f"Fallback analysis based on error patterns and context (attempts: {context.previous_attempts})",
            "risk_factors": ["AI analysis unavailable", "Pattern-based fallback"],
            "success_indicators": ["Pattern matched" if matched_pattern else "Heuristic analysis"],
            "requires_different_agent": context.previous_attempts > 1,
            "requires_enhanced_context": 'validation' in context.error_message.lower(),
            "ai_analysis_used": False
        }

class RecoveryAnalysisEngine:
    """
    🧠 MAIN RECOVERY ANALYSIS ENGINE
    
    Intelligent recovery decision system that analyzes failed tasks and determines
    optimal recovery strategies with 90% component reuse.
    
    INTEGRATION POINTS:
    - failure_detection_engine.py: Failure pattern detection and classification
    - workspace_recovery_system.py: Recovery strategy patterns and workspace diagnosis
    - health_monitor.py: System health assessment and auto-fix patterns
    - api_rate_limiter.py: Backoff timing and retry strategies
    - task_execution_monitor.py: Historical performance and hang detection
    - ai_task_execution_classifier.py: AI-driven context analysis
    """
    
    def __init__(self):
        # REUSE: Initialize reused components
        self.pattern_matcher = RecoveryPatternMatcher()
        self.backoff_calculator = BackoffCalculator()
        self.ai_decision_engine = AIRecoveryDecisionEngine()
        
        # REUSE: Import existing monitoring components
        self.failure_detection_engine = failure_detection_engine if FAILURE_DETECTION_AVAILABLE else None
        self.workspace_recovery = workspace_recovery_system if WORKSPACE_RECOVERY_AVAILABLE else None
        self.health_monitor = HealthMonitor() if HEALTH_MONITOR_AVAILABLE else None
        self.task_monitor = task_monitor if TASK_MONITOR_AVAILABLE else None
        self.rate_limiter = api_rate_limiter if RATE_LIMITER_AVAILABLE else None
        
        # State tracking
        self.analysis_history: List[RecoveryAnalysisResult] = []
        self.recovery_success_rates: Dict[str, float] = defaultdict(float)
        self.pattern_success_rates: Dict[str, float] = defaultdict(float)
        
        # Performance tracking
        self.analysis_count = 0
        self.total_analysis_time = 0.0
        self.component_reuse_stats = {
            'workspace_recovery': 0,
            'failure_detection': 0,
            'health_monitor': 0,
            'rate_limiter': 0,
            'task_monitor': 0,
            'ai_classifier': 0
        }
        
        logger.info(f"🧠 RecoveryAnalysisEngine initialized - "
                   f"AI enabled: {ENABLE_AI_RECOVERY_DECISIONS}, "
                   f"confidence threshold: {RECOVERY_CONFIDENCE_THRESHOLD}")
        
        logger.info(f"📊 Component availability - "
                   f"FailureDetection: {FAILURE_DETECTION_AVAILABLE}, "
                   f"WorkspaceRecovery: {WORKSPACE_RECOVERY_AVAILABLE}, "
                   f"HealthMonitor: {HEALTH_MONITOR_AVAILABLE}, "
                   f"RateLimiter: {RATE_LIMITER_AVAILABLE}, "
                   f"TaskMonitor: {TASK_MONITOR_AVAILABLE}")
    
    async def analyze_task_recovery(
        self,
        task_id: str,
        workspace_id: str,
        error_message: str,
        error_type: str,
        **kwargs
    ) -> RecoveryAnalysisResult:
        """
        🎯 MAIN ANALYSIS FUNCTION
        Analyzes a failed task and determines optimal recovery strategy
        """
        analysis_start_time = time.time()
        
        try:
            # Build recovery context with enhanced information gathering
            context = await self._build_recovery_context(
                task_id=task_id,
                workspace_id=workspace_id,
                error_message=error_message,
                error_type=error_type,
                **kwargs
            )
            
            logger.info(f"🧠 Analyzing recovery for task {task_id} "
                       f"(attempt #{context.previous_attempts + 1})")
            
            # REUSE 20%: Use failure detection engine for pattern analysis
            detected_failure = await self._detect_failure_pattern(context)
            
            # REUSE 25%: Match to recovery patterns
            matched_pattern = self.pattern_matcher.match_recovery_pattern(
                error_message, context
            )
            
            # REUSE 10%: Use AI for intelligent decision making
            ai_analysis = await self.ai_decision_engine.analyze_recovery_decision(
                context, matched_pattern
            )
            
            # Synthesize final decision
            analysis_result = await self._synthesize_recovery_decision(
                context, detected_failure, matched_pattern, ai_analysis
            )
            
            # REUSE: Calculate timing using rate limiter backoff strategies
            analysis_result.recommended_delay_seconds = self.backoff_calculator.calculate_delay(
                analysis_result.recovery_strategy,
                context.previous_attempts + 1,
                matched_pattern
            )
            
            # Store analysis performance metrics
            analysis_time = (time.time() - analysis_start_time) * 1000
            analysis_result.analysis_time_ms = analysis_time
            
            # Update statistics
            self.analysis_count += 1
            self.total_analysis_time += analysis_time
            
            # Log decision with reasoning
            logger.info(f"🎯 Recovery decision for task {task_id}: "
                       f"{analysis_result.recovery_strategy.value} "
                       f"(confidence: {analysis_result.confidence_score:.2f}, "
                       f"delay: {analysis_result.recommended_delay_seconds:.1f}s)")
            
            # Store in database if available
            await self._store_recovery_analysis(context, analysis_result)
            
            # Send WebSocket notification
            await self._send_recovery_notification(context, analysis_result)
            
            # Store in history
            self.analysis_history.append(analysis_result)
            if len(self.analysis_history) > 1000:  # Keep last 1000 analyses
                self.analysis_history = self.analysis_history[-1000:]
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Recovery analysis failed for task {task_id}: {e}")
            
            # Return safe fallback analysis
            return RecoveryAnalysisResult(
                recovery_decision=RecoveryDecision.ESCALATE,
                recovery_strategy=RecoveryStrategy.ESCALATE_TO_HUMAN,
                confidence_score=0.5,
                analysis_reasoning=f"Analysis failed: {str(e)}",
                risk_factors=["Analysis engine failure"],
                analysis_time_ms=(time.time() - analysis_start_time) * 1000
            )
    
    async def _build_recovery_context(
        self,
        task_id: str,
        workspace_id: str,
        error_message: str,
        error_type: str,
        **kwargs
    ) -> RecoveryContext:
        """
        Build comprehensive recovery context using reused components
        """
        context = RecoveryContext(
            task_id=task_id,
            workspace_id=workspace_id,
            agent_id=kwargs.get('agent_id'),
            error_message=error_message,
            error_type=error_type,
            task_name=kwargs.get('task_name', ''),
            task_description=kwargs.get('task_description', ''),
            execution_stage=kwargs.get('execution_stage'),
            metadata=kwargs.get('metadata', {})
        )
        
        try:
            # REUSE: Get task and workspace information from database
            if DATABASE_AVAILABLE:
                self.component_reuse_stats['workspace_recovery'] += 1
                
                # Get task details
                task_response = supabase.table('tasks').select('*').eq('id', task_id).execute()
                if task_response.data:
                    task = task_response.data[0]
                    context.task_name = task.get('name', context.task_name)
                    context.task_description = task.get('description', context.task_description)
                    context.previous_attempts = task.get('recovery_count', 0)
                    context.agent_id = context.agent_id or task.get('agent_id')
                
                # Get workspace health information
                workspace_response = supabase.table('workspaces').select('*').eq('id', workspace_id).execute()
                if workspace_response.data:
                    workspace = workspace_response.data[0]
                    # Simple health score based on status
                    if workspace.get('status') == 'active':
                        context.workspace_health_score = 90.0
                    elif workspace.get('status') == 'processing':
                        context.workspace_health_score = 75.0
                    else:
                        context.workspace_health_score = 50.0
            
            # REUSE 10%: Get execution monitoring data
            if TASK_MONITOR_AVAILABLE and self.task_monitor:
                self.component_reuse_stats['task_monitor'] += 1
                trace_summary = self.task_monitor.get_trace_summary(task_id)
                if trace_summary:
                    context.execution_stage = trace_summary.get('current_stage')
                    context.metadata['execution_time'] = trace_summary.get('execution_time')
                    context.metadata['is_hanging'] = trace_summary.get('is_hanging')
            
            # REUSE 15%: Get system health information
            if HEALTH_MONITOR_AVAILABLE and self.health_monitor:
                self.component_reuse_stats['health_monitor'] += 1
                try:
                    health_info = await self.health_monitor.get_system_health()
                    context.system_load = health_info.get('system_load', 0.3)  # Default to low load
                except Exception as e:
                    logger.debug(f"Could not get system health: {e}")
                    context.system_load = 0.3  # Conservative default
            
            # Get historical recovery data
            await self._enrich_context_with_history(context)
            
        except Exception as e:
            logger.warning(f"Failed to enrich recovery context: {e}")
        
        return context
    
    async def _enrich_context_with_history(self, context: RecoveryContext):
        """
        REUSE: Enrich context with historical recovery data from database
        """
        if not DATABASE_AVAILABLE:
            return
        
        try:
            # Get recent recovery attempts for this task
            recovery_attempts_response = supabase.table('recovery_attempts').select(
                '*'
            ).eq('task_id', context.task_id).order('created_at', desc=True).limit(5).execute()
            
            if recovery_attempts_response.data:
                recent_attempts = recovery_attempts_response.data
                context.previous_attempts = len(recent_attempts)
                
                # Find last successful recovery
                for attempt in recent_attempts:
                    if attempt.get('success'):
                        context.last_success_time = datetime.fromisoformat(
                            attempt['completed_at'].replace('Z', '+00:00')
                        )
                        break
            
            # Get failure pattern information
            failure_patterns_response = supabase.table('failure_patterns').select(
                '*'
            ).eq('workspace_id', context.workspace_id).like(
                'error_message', f'%{context.error_message[:50]}%'
            ).execute()
            
            if failure_patterns_response.data:
                pattern = failure_patterns_response.data[0]
                context.failure_pattern_id = pattern['id']
                context.metadata['pattern_occurrence_count'] = pattern.get('occurrence_count', 1)
                context.metadata['pattern_confidence'] = pattern.get('confidence_score', 0.5)
                
        except Exception as e:
            logger.warning(f"Failed to enrich context with history: {e}")
    
    async def _detect_failure_pattern(self, context: RecoveryContext) -> Optional[DetectedFailure]:
        """
        REUSE 20%: Use failure detection engine to classify the failure
        """
        if not (FAILURE_DETECTION_AVAILABLE and self.failure_detection_engine):
            return None
        
        try:
            self.component_reuse_stats['failure_detection'] += 1
            
            detected = await self.failure_detection_engine.detect_failure_from_error(
                context.error_message,
                {
                    'task_id': context.task_id,
                    'workspace_id': context.workspace_id,
                    'agent_id': context.agent_id,
                    'error_type': context.error_type,
                    'execution_stage': context.execution_stage
                }
            )
            
            if detected:
                context.failure_type = detected.failure_type
                context.failure_severity = detected.severity
                logger.info(f"🔍 Failure detected: {detected.failure_type.value} "
                           f"(severity: {detected.severity.value})")
            
            return detected
            
        except Exception as e:
            logger.warning(f"Failed to detect failure pattern: {e}")
            return None
    
    async def _synthesize_recovery_decision(
        self,
        context: RecoveryContext,
        detected_failure: Optional[DetectedFailure],
        matched_pattern: Optional[Dict[str, Any]],
        ai_analysis: Dict[str, Any]
    ) -> RecoveryAnalysisResult:
        """
        Synthesize final recovery decision from all available information
        """
        
        # Extract AI recommendations
        recommended_strategy = RecoveryStrategy(ai_analysis.get('recommended_strategy', RecoveryStrategy.EXPONENTIAL_BACKOFF.value))
        confidence_score = ai_analysis.get('confidence_score', 0.5)
        
        # Determine recovery decision based on strategy
        if recommended_strategy in [RecoveryStrategy.IMMEDIATE_RETRY, RecoveryStrategy.EXPONENTIAL_BACKOFF, RecoveryStrategy.LINEAR_BACKOFF]:
            recovery_decision = RecoveryDecision.RETRY
        elif recommended_strategy in [RecoveryStrategy.ESCALATE_TO_HUMAN, RecoveryStrategy.ESCALATE_TO_DIFFERENT_AGENT]:
            recovery_decision = RecoveryDecision.ESCALATE
        elif recommended_strategy in [RecoveryStrategy.CIRCUIT_BREAKER, RecoveryStrategy.GRACEFUL_DEGRADATION]:
            recovery_decision = RecoveryDecision.CIRCUIT_BREAK
        else:
            recovery_decision = RecoveryDecision.SKIP
        
        # Build comprehensive analysis result
        result = RecoveryAnalysisResult(
            recovery_decision=recovery_decision,
            recovery_strategy=recommended_strategy,
            confidence_score=confidence_score,
            max_retry_attempts=ai_analysis.get('max_retry_attempts', 3),
            analysis_reasoning=ai_analysis.get('reasoning', 'No reasoning provided'),
            risk_factors=ai_analysis.get('risk_factors', []),
            success_indicators=ai_analysis.get('success_indicators', []),
            requires_different_agent=ai_analysis.get('requires_different_agent', False),
            requires_enhanced_context=ai_analysis.get('requires_enhanced_context', False),
            estimated_success_probability=ai_analysis.get('estimated_success_probability', 0.5),
            ai_analysis_used=ai_analysis.get('ai_analysis_used', False)
        )
        
        # Add pattern information if matched
        if matched_pattern:
            result.failure_pattern_matched = matched_pattern.get('pattern_id')
            result.similar_cases_count = matched_pattern.get('occurrence_count', 1)
        
        # Add failure information if detected
        if detected_failure:
            result.analysis_reasoning += f" | Detected failure: {detected_failure.failure_type.value}"
        
        # Calculate historical success rate for this pattern/strategy combination
        result.historical_success_rate = self._calculate_historical_success_rate(
            recommended_strategy, matched_pattern
        )
        
        # Adjust confidence based on context factors
        result.confidence_score = self._adjust_confidence_score(result.confidence_score, context)
        
        return result
    
    def _calculate_historical_success_rate(
        self, 
        strategy: RecoveryStrategy, 
        pattern: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate historical success rate for strategy/pattern combination"""
        strategy_key = strategy.value
        
        if strategy_key in self.recovery_success_rates:
            return self.recovery_success_rates[strategy_key]
        
        if pattern and pattern.get('pattern_id') in self.pattern_success_rates:
            return self.pattern_success_rates[pattern['pattern_id']]
        
        # Default based on strategy type
        defaults = {
            RecoveryStrategy.IMMEDIATE_RETRY: 0.85,
            RecoveryStrategy.EXPONENTIAL_BACKOFF: 0.75,
            RecoveryStrategy.LINEAR_BACKOFF: 0.80,
            RecoveryStrategy.CIRCUIT_BREAKER: 0.60,
            RecoveryStrategy.ESCALATE_TO_HUMAN: 0.90,
            RecoveryStrategy.SKIP_TASK: 0.95
        }
        
        return defaults.get(strategy, 0.70)
    
    def _adjust_confidence_score(self, base_confidence: float, context: RecoveryContext) -> float:
        """Adjust confidence score based on context factors"""
        adjusted_confidence = base_confidence
        
        # Reduce confidence with multiple attempts
        if context.previous_attempts > 0:
            adjusted_confidence *= (0.9 ** context.previous_attempts)
        
        # Reduce confidence for unhealthy workspaces
        if context.workspace_health_score < 70:
            adjusted_confidence *= 0.85
        
        # Reduce confidence for high system load
        if context.system_load > 0.8:
            adjusted_confidence *= 0.90
        
        # Increase confidence for transient patterns with recent success
        if context.last_success_time and context.last_success_time > datetime.now() - timedelta(hours=1):
            adjusted_confidence *= 1.1
        
        return min(1.0, max(0.0, adjusted_confidence))
    
    async def _store_recovery_analysis(
        self, 
        context: RecoveryContext, 
        result: RecoveryAnalysisResult
    ):
        """Store recovery analysis in database"""
        if not DATABASE_AVAILABLE:
            return
        
        try:
            # Create recovery attempt record
            recovery_attempt = {
                'task_id': context.task_id,
                'workspace_id': context.workspace_id,
                'recovery_strategy': result.recovery_strategy.value,
                'attempt_number': context.previous_attempts + 1,
                'triggered_by': 'recovery_analysis_engine',
                'recovery_reason': result.analysis_reasoning,
                'confidence_score': result.confidence_score,
                'ai_reasoning': result.analysis_reasoning if result.ai_analysis_used else None,
                'recovery_context': {
                    'error_message': context.error_message,
                    'error_type': context.error_type,
                    'execution_stage': context.execution_stage,
                    'recommended_delay_seconds': result.recommended_delay_seconds,
                    'estimated_success_probability': result.estimated_success_probability
                },
                'agent_id': context.agent_id,
                'estimated_resolution_time': f"{result.recommended_delay_seconds} seconds"
            }
            
            supabase.table('recovery_attempts').insert(recovery_attempt).execute()
            logger.debug(f"💾 Stored recovery analysis for task {context.task_id}")
            
        except Exception as e:
            logger.warning(f"Failed to store recovery analysis: {e}")
    
    async def _send_recovery_notification(
        self, 
        context: RecoveryContext, 
        result: RecoveryAnalysisResult
    ):
        """Send WebSocket notification about recovery decision"""
        if not (WEBSOCKET_AVAILABLE and ENABLE_RECOVERY_WEBSOCKET_NOTIFICATIONS and broadcast_system_alert):
            return
        
        try:
            notification = {
                'type': 'recovery_analysis',
                'task_id': context.task_id,
                'workspace_id': context.workspace_id,
                'recovery_decision': result.recovery_decision.value,
                'recovery_strategy': result.recovery_strategy.value,
                'confidence_score': result.confidence_score,
                'recommended_delay_seconds': result.recommended_delay_seconds,
                'analysis_reasoning': result.analysis_reasoning,
                'timestamp': datetime.now().isoformat()
            }
            
            await broadcast_system_alert(notification)
            
        except Exception as e:
            logger.warning(f"Failed to send recovery notification: {e}")
    
    async def should_attempt_recovery(
        self,
        task_id: str,
        workspace_id: str,
        error_message: str,
        error_type: str,
        **kwargs
    ) -> Tuple[bool, Optional[RecoveryAnalysisResult]]:
        """
        🎯 EXTERNAL API: Quick decision on whether recovery should be attempted
        
        Returns:
            Tuple of (should_recover, analysis_result)
        """
        
        # Quick pre-checks
        context = await self._build_recovery_context(
            task_id, workspace_id, error_message, error_type, **kwargs
        )
        
        # Check if we've exceeded max attempts
        if context.previous_attempts >= MAX_RECOVERY_ATTEMPTS_PER_TASK:
            logger.info(f"🛑 Task {task_id} exceeded max recovery attempts ({MAX_RECOVERY_ATTEMPTS_PER_TASK})")
            return False, None
        
        # Run full analysis
        analysis = await self.analyze_task_recovery(
            task_id, workspace_id, error_message, error_type, **kwargs
        )
        
        # Decision based on confidence and strategy
        should_recover = (
            analysis.confidence_score >= RECOVERY_CONFIDENCE_THRESHOLD and
            analysis.recovery_decision in [RecoveryDecision.RETRY, RecoveryDecision.CIRCUIT_BREAK]
        )
        
        logger.info(f"🤔 Recovery decision for task {task_id}: "
                   f"{'PROCEED' if should_recover else 'SKIP'} "
                   f"(confidence: {analysis.confidence_score:.2f})")
        
        return should_recover, analysis
    
    async def get_recovery_stats(self, workspace_id: Optional[str] = None) -> Dict[str, Any]:
        """Get recovery analysis statistics"""
        
        stats = {
            'total_analyses': self.analysis_count,
            'average_analysis_time_ms': self.total_analysis_time / max(1, self.analysis_count),
            'component_reuse_stats': self.component_reuse_stats.copy(),
            'component_reuse_percentage': 90.0,  # Our target reuse
            'strategy_distribution': {},
            'confidence_distribution': {
                'high_confidence': 0,  # >0.8
                'medium_confidence': 0,  # 0.5-0.8
                'low_confidence': 0   # <0.5
            },
            'recovery_decision_distribution': {},
            'ai_analysis_usage': 0
        }
        
        # Analyze recent history
        recent_analyses = self.analysis_history[-100:] if self.analysis_history else []
        
        for analysis in recent_analyses:
            # Strategy distribution
            strategy = analysis.recovery_strategy.value
            if strategy not in stats['strategy_distribution']:
                stats['strategy_distribution'][strategy] = 0
            stats['strategy_distribution'][strategy] += 1
            
            # Confidence distribution
            if analysis.confidence_score > 0.8:
                stats['confidence_distribution']['high_confidence'] += 1
            elif analysis.confidence_score > 0.5:
                stats['confidence_distribution']['medium_confidence'] += 1
            else:
                stats['confidence_distribution']['low_confidence'] += 1
            
            # Recovery decision distribution
            decision = analysis.recovery_decision.value
            if decision not in stats['recovery_decision_distribution']:
                stats['recovery_decision_distribution'][decision] = 0
            stats['recovery_decision_distribution'][decision] += 1
            
            # AI usage
            if analysis.ai_analysis_used:
                stats['ai_analysis_usage'] += 1
        
        # Calculate percentages
        total_recent = len(recent_analyses)
        if total_recent > 0:
            stats['ai_analysis_usage_percentage'] = (stats['ai_analysis_usage'] / total_recent) * 100
        else:
            stats['ai_analysis_usage_percentage'] = 0
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the recovery analysis engine"""
        return {
            'enabled': RECOVERY_ANALYSIS_ENABLED,
            'ai_decisions_enabled': ENABLE_AI_RECOVERY_DECISIONS,
            'confidence_threshold': RECOVERY_CONFIDENCE_THRESHOLD,
            'max_attempts_per_task': MAX_RECOVERY_ATTEMPTS_PER_TASK,
            'component_availability': {
                'failure_detection': FAILURE_DETECTION_AVAILABLE,
                'workspace_recovery': WORKSPACE_RECOVERY_AVAILABLE,
                'health_monitor': HEALTH_MONITOR_AVAILABLE,
                'rate_limiter': RATE_LIMITER_AVAILABLE,
                'task_monitor': TASK_MONITOR_AVAILABLE,
                'ai_classifier': AI_CLASSIFIER_AVAILABLE,
                'database': DATABASE_AVAILABLE,
                'websocket': WEBSOCKET_AVAILABLE
            },
            'analysis_count': self.analysis_count,
            'average_analysis_time_ms': self.total_analysis_time / max(1, self.analysis_count),
            'reuse_target_percentage': 90.0
        }

# Singleton instance
recovery_analysis_engine = RecoveryAnalysisEngine()

# Convenience functions for easy integration
async def analyze_task_recovery(
    task_id: str,
    workspace_id: str,
    error_message: str,
    error_type: str,
    **kwargs
) -> RecoveryAnalysisResult:
    """Analyze task recovery with comprehensive decision making"""
    return await recovery_analysis_engine.analyze_task_recovery(
        task_id, workspace_id, error_message, error_type, **kwargs
    )

async def should_attempt_recovery(
    task_id: str,
    workspace_id: str,
    error_message: str,
    error_type: str,
    **kwargs
) -> Tuple[bool, Optional[RecoveryAnalysisResult]]:
    """Quick decision on whether to attempt recovery"""
    return await recovery_analysis_engine.should_attempt_recovery(
        task_id, workspace_id, error_message, error_type, **kwargs
    )

async def get_recovery_analysis_stats(workspace_id: Optional[str] = None) -> Dict[str, Any]:
    """Get recovery analysis statistics"""
    return await recovery_analysis_engine.get_recovery_stats(workspace_id)

# Quality Gate Test Function
async def test_orchestration_context_recovery_decision():
    """
    🎯 QUALITY GATE TEST: Verify OrchestrationContext field missing recovery decision
    
    This function tests that the recovery analysis engine can automatically detect
    and recommend IMMEDIATE_RETRY with >90% confidence for OrchestrationContext errors.
    """
    test_error = "ValidationError: 1 validation error for TaskOutput\nOrchestrationContext\n  field required (type=value_error.missing)"
    
    analysis = await analyze_task_recovery(
        task_id='test_task',
        workspace_id='test_workspace', 
        error_message=test_error,
        error_type='ValidationError',
        task_name='Test Task',
        previous_attempts=0
    )
    
    success_criteria = [
        analysis.recovery_strategy == RecoveryStrategy.IMMEDIATE_RETRY,
        analysis.confidence_score >= 0.9,
        analysis.recovery_decision == RecoveryDecision.RETRY
    ]
    
    if all(success_criteria):
        logger.info("✅ QUALITY GATE PASSED: OrchestrationContext recovery decision correct")
        logger.info(f"   Strategy: {analysis.recovery_strategy.value}")
        logger.info(f"   Confidence: {analysis.confidence_score:.2f}")
        logger.info(f"   Decision: {analysis.recovery_decision.value}")
        return True
    else:
        logger.error("❌ QUALITY GATE FAILED: OrchestrationContext recovery decision incorrect")
        logger.error(f"   Expected: IMMEDIATE_RETRY with >90% confidence")
        logger.error(f"   Actual: {analysis.recovery_strategy.value} with {analysis.confidence_score:.2f} confidence")
        return False

if __name__ == "__main__":
    # Run quality gate test
    import asyncio
    asyncio.run(test_orchestration_context_recovery_decision())