# RecoveryExplanationEngine Design Document

## Executive Summary

The RecoveryExplanationEngine is designed to achieve 95%+ compliance on the Explainability pillar by providing transparent, human-understandable explanations for all task failure recovery decisions. This engine transforms opaque AI-driven recovery processes into clear, actionable insights for users.

## Architecture Overview

### Core Components

```
RecoveryExplanationEngine
├── FailureAnalyzer          # Categorizes and analyzes failures
├── RecoveryDecisionEngine   # Makes recovery decisions with explanations
├── ExplanationGenerator     # Formats explanations for users
├── PatternMatcher          # Identifies known error patterns
└── UserNotificationService # Delivers explanations to users
```

## Class Design

### 1. RecoveryExplanationEngine

```python
class RecoveryExplanationEngine:
    """
    🔍 EXPLAINABLE RECOVERY ENGINE
    
    Provides transparent explanations for all task failure recovery decisions,
    ensuring users understand why failures occurred and why specific recovery
    strategies are being applied.
    """
    
    def __init__(self):
        self.failure_analyzer = FailureAnalyzer()
        self.decision_engine = RecoveryDecisionEngine() 
        self.explanation_generator = ExplanationGenerator()
        self.pattern_matcher = PatternMatcher()
        self.notification_service = UserNotificationService()
        self.ai_explainer = AIExplainerClient() if ENABLE_AI_EXPLANATIONS else None
        
    async def explain_recovery_decision(
        self, 
        task_id: str, 
        failure_context: FailureContext,
        recovery_strategy: RecoveryStrategy
    ) -> RecoveryExplanation:
        """Main entry point for recovery explanation generation"""
        pass
        
    async def analyze_and_explain_failure(
        self, 
        task_id: str, 
        error_message: str,
        execution_context: Dict[str, Any]
    ) -> FailureExplanation:
        """Analyzes failure and generates explanation"""
        pass
```

### 2. FailureAnalyzer

```python
@dataclass
class FailureContext:
    """Context information about task failure"""
    task_id: str
    workspace_id: str
    agent_id: Optional[str]
    error_message: str
    error_type: str
    execution_stage: ExecutionStage
    attempt_count: int
    failure_timestamp: datetime
    execution_metadata: Dict[str, Any]
    similar_failures: List[str] = None  # Similar recent failures

@dataclass 
class FailureAnalysis:
    """Results of failure analysis"""
    failure_category: FailureCategory
    root_cause: str
    is_transient: bool
    confidence_score: float
    retry_recommendation: RetryRecommendation
    explanation_context: Dict[str, Any]

class FailureCategory(str, Enum):
    # Technical Failures
    PYDANTIC_VALIDATION_ERROR = "pydantic_validation_error"
    JSON_PARSING_ERROR = "json_parsing_error"
    OPENAI_API_TIMEOUT = "openai_api_timeout"  
    OPENAI_API_RATE_LIMIT = "openai_api_rate_limit"
    OPENAI_SDK_ERROR = "openai_sdk_error"
    DATABASE_CONNECTION_ERROR = "database_connection_error"
    NETWORK_ERROR = "network_error"
    
    # Business Logic Failures
    AGENT_ASSIGNMENT_FAILED = "agent_assignment_failed"
    TASK_DEPENDENCY_MISSING = "task_dependency_missing"
    WORKSPACE_STATE_INVALID = "workspace_state_invalid"
    QUALITY_THRESHOLD_NOT_MET = "quality_threshold_not_met"
    
    # System Resource Failures
    MEMORY_EXHAUSTION = "memory_exhaustion"
    CPU_TIMEOUT = "cpu_timeout"
    DISK_SPACE_ERROR = "disk_space_error"
    
    # Unknown/Complex
    COMPLEX_MULTI_FACTOR = "complex_multi_factor"
    UNKNOWN_ERROR = "unknown_error"

class RetryRecommendation(str, Enum):
    IMMEDIATE_RETRY = "immediate_retry"          # Safe to retry immediately
    DELAYED_RETRY = "delayed_retry"              # Retry after delay
    CONDITIONAL_RETRY = "conditional_retry"      # Retry only if conditions met
    NO_RETRY_TRANSIENT_ISSUE = "no_retry_transient"  # Don't retry, issue will resolve
    NO_RETRY_PERMANENT_ISSUE = "no_retry_permanent"  # Don't retry, requires intervention
    ESCALATE_TO_HUMAN = "escalate_to_human"     # Human intervention needed

class FailureAnalyzer:
    """Categorizes failures and provides retry recommendations"""
    
    def __init__(self):
        self.pattern_matchers = self._initialize_pattern_matchers()
        self.ai_analyzer = AIFailureAnalyzer() if ENABLE_AI_FAILURE_ANALYSIS else None
        
    async def analyze_failure(self, context: FailureContext) -> FailureAnalysis:
        """Analyzes failure and categorizes it"""
        
        # 1. Pattern matching against known errors
        pattern_result = await self._match_error_patterns(context)
        
        # 2. AI-driven analysis for complex cases
        ai_result = None
        if self.ai_analyzer and not pattern_result:
            ai_result = await self.ai_analyzer.analyze_complex_failure(context)
            
        # 3. Combine results and generate analysis
        return await self._synthesize_analysis(pattern_result, ai_result, context)
        
    def _initialize_pattern_matchers(self) -> List[ErrorPattern]:
        """Initialize known error patterns with explanations"""
        return [
            ErrorPattern(
                pattern=r"ValidationError.*field required",
                category=FailureCategory.PYDANTIC_VALIDATION_ERROR,
                is_transient=False,
                retry_recommendation=RetryRecommendation.NO_RETRY_PERMANENT_ISSUE,
                explanation_template="Task output is missing required fields. The agent needs to provide complete information before this task can be completed.",
                user_friendly_cause="The AI assistant didn't provide all the required information in its response."
            ),
            ErrorPattern(
                pattern=r"rate_limit_exceeded",
                category=FailureCategory.OPENAI_API_RATE_LIMIT,
                is_transient=True,
                retry_recommendation=RetryRecommendation.DELAYED_RETRY,
                explanation_template="OpenAI API rate limit reached. This is temporary - the system will retry automatically after a brief delay.",
                user_friendly_cause="Too many AI requests at once. The system is waiting for capacity to free up."
            ),
            ErrorPattern(
                pattern=r"timeout.*openai",
                category=FailureCategory.OPENAI_API_TIMEOUT,
                is_transient=True,
                retry_recommendation=RetryRecommendation.IMMEDIATE_RETRY,
                explanation_template="OpenAI API request timed out. This is usually temporary - retrying immediately.",
                user_friendly_cause="The AI service took too long to respond. Usually resolves on retry."
            ),
            # ... more patterns
        ]
```

### 3. RecoveryDecisionEngine

```python
@dataclass
class RecoveryDecision:
    """Decision about how to recover from failure"""
    strategy: RecoveryStrategy
    confidence_score: float
    reasoning: str
    risk_assessment: str
    expected_outcome: str
    fallback_strategy: Optional[RecoveryStrategy]

class RecoveryStrategy(str, Enum):
    IMMEDIATE_RETRY = "immediate_retry"
    DELAYED_RETRY_5M = "delayed_retry_5m" 
    DELAYED_RETRY_30M = "delayed_retry_30m"
    RETRY_WITH_DIFFERENT_AGENT = "retry_with_different_agent"
    RETRY_WITH_FALLBACK_MODEL = "retry_with_fallback_model"
    RESET_TASK_DEPENDENCIES = "reset_task_dependencies"
    ESCALATE_TO_WORKSPACE_RECOVERY = "escalate_to_workspace_recovery"
    MARK_FAILED_NO_RETRY = "mark_failed_no_retry"
    PAUSE_TASK_FOR_MANUAL_REVIEW = "pause_task_for_manual_review"

class RecoveryDecisionEngine:
    """Makes intelligent recovery decisions with full explanations"""
    
    async def decide_recovery_strategy(
        self, 
        failure_analysis: FailureAnalysis,
        recovery_context: RecoveryContext
    ) -> RecoveryDecision:
        """Decides on recovery strategy with full reasoning"""
        
        # 1. Check circuit breaker status
        if await self._is_circuit_breaker_tripped(recovery_context):
            return self._create_circuit_breaker_decision()
            
        # 2. AI-driven decision making
        if self.ai_decision_engine:
            ai_decision = await self.ai_decision_engine.recommend_strategy(
                failure_analysis, recovery_context
            )
            if ai_decision.confidence_score > 0.8:
                return ai_decision
                
        # 3. Rule-based fallback
        return self._apply_rule_based_decision(failure_analysis, recovery_context)

@dataclass 
class RecoveryContext:
    """Context for recovery decision making"""
    task_id: str
    workspace_id: str
    previous_attempts: int
    recent_failures_count: int
    workspace_health_status: HealthStatus
    available_agents: List[str]
    system_load: float
    time_since_last_failure: timedelta
```

### 4. ExplanationGenerator

```python
@dataclass
class RecoveryExplanation:
    """Complete explanation of recovery decision"""
    task_id: str
    failure_summary: str           # "Task failed due to missing required fields"
    root_cause: str               # "Pydantic validation error - agent response incomplete" 
    retry_decision: str           # "Not retrying - requires agent improvement"
    confidence_explanation: str   # "High confidence (95%) - known pattern"
    user_action_required: Optional[str]  # "Review task requirements with agent"
    estimated_resolution_time: Optional[str]  # "Manual review needed - no ETA"
    
    # Technical details for developers
    technical_details: Dict[str, Any]
    error_pattern_matched: Optional[str]
    ai_analysis_used: bool
    
    # Display formatting
    severity_level: str  # "low", "medium", "high", "critical"
    display_category: str  # "Temporary Issue", "Configuration Problem", etc.
    
class ExplanationGenerator:
    """Generates human-friendly explanations"""
    
    def __init__(self):
        self.templates = self._load_explanation_templates()
        self.ai_explainer = AIExplainerClient() if ENABLE_AI_EXPLANATIONS else None
        
    async def generate_explanation(
        self,
        failure_analysis: FailureAnalysis,
        recovery_decision: RecoveryDecision,
        context: Dict[str, Any]
    ) -> RecoveryExplanation:
        """Generates comprehensive explanation"""
        
        # 1. Use template-based explanation for known patterns  
        if failure_analysis.failure_category in self.templates:
            template_explanation = self._apply_template(
                failure_analysis.failure_category, 
                context
            )
        else:
            template_explanation = None
            
        # 2. Enhance with AI explanation for complex cases
        ai_explanation = None
        if self.ai_explainer and failure_analysis.failure_category == FailureCategory.COMPLEX_MULTI_FACTOR:
            ai_explanation = await self.ai_explainer.generate_explanation(
                failure_analysis, recovery_decision, context
            )
            
        # 3. Synthesize final explanation
        return self._synthesize_explanation(
            template_explanation, ai_explanation, failure_analysis, recovery_decision
        )
        
    def _load_explanation_templates(self) -> Dict[FailureCategory, ExplanationTemplate]:
        """Load human-friendly explanation templates"""
        return {
            FailureCategory.PYDANTIC_VALIDATION_ERROR: ExplanationTemplate(
                failure_summary="Task output validation failed",
                root_cause_template="The AI assistant's response was missing required information: {missing_fields}",
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
            # ... more templates
        }
```

### 5. Integration Points

```python
# Integration with existing recovery system
class WorkspaceRecoverySystemIntegration:
    """Integrates with existing workspace_recovery_system.py"""
    
    def __init__(self, explanation_engine: RecoveryExplanationEngine):
        self.explanation_engine = explanation_engine
        
    async def explain_workspace_recovery(
        self, 
        workspace_id: str, 
        diagnosis: Dict[str, Any],
        recovery_strategy: str,
        actions_taken: List[str]
    ) -> WorkspaceRecoveryExplanation:
        """Explains workspace-level recovery decisions"""
        pass

# Integration with task execution monitor  
class TaskMonitorIntegration:
    """Integrates with task_execution_monitor.py"""
    
    def __init__(self, explanation_engine: RecoveryExplanationEngine):
        self.explanation_engine = explanation_engine
        
    async def explain_hanging_task_recovery(
        self,
        task_trace: TaskExecutionTrace,
        recovery_action: str
    ) -> HangingTaskExplanation:
        """Explains recovery from hanging tasks"""
        pass
```

## UI/API Response Formats

### 1. Real-time Notifications

```json
{
  "type": "task_recovery_explanation",
  "task_id": "uuid",
  "workspace_id": "uuid", 
  "timestamp": "2025-01-15T10:30:00Z",
  "explanation": {
    "summary": "Task failed due to incomplete AI response",
    "root_cause": "The AI assistant didn't provide the required 'title' and 'description' fields",
    "decision": "Not retrying - agent needs to understand requirements better", 
    "confidence": "High confidence (95%) - known validation pattern",
    "severity": "medium",
    "category": "Agent Response Issue",
    "user_action": "Review task requirements with the AI assistant",
    "technical_details": {
      "error_type": "pydantic_validation_error",
      "missing_fields": ["title", "description"],
      "error_pattern": "ValidationError.*field required"
    }
  }
}
```

### 2. Dashboard Display Format

```json
{
  "recovery_explanations": [
    {
      "task_id": "uuid",
      "task_name": "Create marketing email campaign", 
      "failure_time": "2025-01-15T10:30:00Z",
      "explanation": {
        "title": "Task Output Validation Failed",
        "description": "The AI assistant's response was missing required information",
        "status": "Waiting for manual review", 
        "severity": "medium",
        "icon": "validation-error",
        "actions": [
          {
            "label": "Review Task Requirements",
            "action": "review_task",
            "primary": true
          },
          {
            "label": "View Technical Details", 
            "action": "show_technical_details",
            "primary": false
          }
        ]
      }
    }
  ]
}
```

### 3. Historical Tracking API

```json
{
  "recovery_history": {
    "task_id": "uuid",
    "attempts": [
      {
        "attempt_number": 1,
        "failure_time": "2025-01-15T10:30:00Z",
        "failure_reason": "Pydantic validation error - missing fields",
        "recovery_decision": "no_retry_permanent_issue", 
        "explanation": "Agent response incomplete - requires manual review",
        "confidence": 0.95
      }
    ],
    "current_status": "failed_needs_review",
    "next_recommended_action": "Review task requirements with agent"
  }
}
```

## Environment Configuration

```bash
# Explainability Engine Configuration
ENABLE_RECOVERY_EXPLANATIONS=true
ENABLE_AI_FAILURE_ANALYSIS=true  # Use AI for complex failure analysis
ENABLE_AI_EXPLANATIONS=true      # Use AI to generate explanations
RECOVERY_EXPLANATION_DETAIL_LEVEL=standard  # minimal, standard, detailed

# Pattern Matching Configuration  
ERROR_PATTERN_CONFIDENCE_THRESHOLD=0.8
UNKNOWN_ERROR_AI_ANALYSIS_THRESHOLD=3  # Use AI after 3 unknown errors

# Notification Configuration
ENABLE_RECOVERY_NOTIFICATIONS=true
RECOVERY_NOTIFICATION_CHANNELS=websocket,database  # websocket, email, slack, database

# Fallback Configuration
FALLBACK_TO_RULE_BASED_EXPLANATIONS=true
MAX_AI_EXPLANATION_TIMEOUT_SECONDS=10

# Debugging and Development
RECOVERY_EXPLANATION_DEBUG_MODE=false
LOG_ALL_RECOVERY_DECISIONS=true
RECOVERY_EXPLANATION_CACHE_TTL_SECONDS=300
```

## Implementation Plan

### Phase 1: Core Engine (Week 1)
1. Implement `FailureAnalyzer` with pattern matching
2. Create `RecoveryDecisionEngine` with rule-based decisions
3. Build `ExplanationGenerator` with templates
4. Add basic integration points

### Phase 2: AI Enhancement (Week 2)  
1. Integrate AI failure analysis for complex cases
2. Add AI-powered explanation generation
3. Implement confidence scoring and fallbacks
4. Create advanced pattern matching

### Phase 3: User Experience (Week 3)
1. Build UI components for explanation display
2. Implement real-time notifications
3. Create historical tracking and analytics
4. Add user feedback collection

### Phase 4: Integration & Testing (Week 4)
1. Full integration with existing recovery systems
2. Comprehensive testing across failure scenarios
3. Performance optimization
4. Documentation and training materials

## Success Metrics

- **95%+ Explainability Compliance**: All recovery decisions have clear explanations
- **<2 second explanation generation**: Fast response times for user experience
- **90%+ user understanding**: Users can understand and act on explanations  
- **80%+ pattern recognition**: Known errors are automatically categorized
- **99.9% availability**: System remains functional even during failures

This design ensures that every task failure recovery decision is transparent, explainable, and actionable for users, achieving the critical 95%+ compliance target for the Explainability pillar.