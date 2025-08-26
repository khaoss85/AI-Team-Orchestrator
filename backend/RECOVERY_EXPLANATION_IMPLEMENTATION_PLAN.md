# RecoveryExplanationEngine Implementation Plan

## Overview
This document provides a comprehensive implementation plan for integrating the RecoveryExplanationEngine into the existing AI Team Orchestrator system to achieve 95%+ compliance on the Explainability pillar.

## Phase 1: Core Engine Integration (Week 1)

### 1.1 Database Schema Setup
First, create the database table for storing recovery explanations:

```sql
-- Create recovery_explanations table
CREATE TABLE recovery_explanations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id),
    workspace_id UUID NOT NULL REFERENCES workspaces(id),
    task_name TEXT,
    failure_summary TEXT NOT NULL,
    root_cause TEXT NOT NULL,
    retry_decision TEXT NOT NULL,
    confidence_explanation TEXT NOT NULL,
    user_action_required TEXT,
    estimated_resolution_time TEXT,
    severity_level TEXT NOT NULL CHECK (severity_level IN ('low', 'medium', 'high', 'critical')),
    display_category TEXT NOT NULL,
    failure_time TIMESTAMP WITH TIME ZONE NOT NULL,
    technical_details JSONB,
    error_pattern_matched TEXT,
    ai_analysis_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_recovery_explanations_task_id ON recovery_explanations(task_id);
CREATE INDEX idx_recovery_explanations_workspace_id ON recovery_explanations(workspace_id);
CREATE INDEX idx_recovery_explanations_created_at ON recovery_explanations(created_at DESC);
CREATE INDEX idx_recovery_explanations_severity ON recovery_explanations(severity_level);
CREATE INDEX idx_recovery_explanations_category ON recovery_explanations(display_category);
```

### 1.2 Environment Variables
Add the following environment variables to `.env`:

```bash
# Recovery Explanation Engine
ENABLE_RECOVERY_EXPLANATIONS=true
ENABLE_AI_FAILURE_ANALYSIS=true
ENABLE_AI_EXPLANATIONS=true
RECOVERY_EXPLANATION_DETAIL_LEVEL=standard
ERROR_PATTERN_CONFIDENCE_THRESHOLD=0.8
UNKNOWN_ERROR_AI_ANALYSIS_THRESHOLD=3

# Notification Configuration
ENABLE_RECOVERY_NOTIFICATIONS=true
RECOVERY_NOTIFICATION_CHANNELS=websocket,database

# Fallback and Performance
FALLBACK_TO_RULE_BASED_EXPLANATIONS=true
MAX_AI_EXPLANATION_TIMEOUT_SECONDS=10
RECOVERY_EXPLANATION_DEBUG_MODE=false
LOG_ALL_RECOVERY_DECISIONS=true
RECOVERY_EXPLANATION_CACHE_TTL_SECONDS=300
```

### 1.3 Integration Points

#### A. Integrate with TaskExecutor
Modify `backend/executor.py` to generate explanations on task failures:

```python
# Add import at top of executor.py
try:
    from services.recovery_explanation_engine import explain_task_failure
    RECOVERY_EXPLANATION_AVAILABLE = True
except ImportError:
    RECOVERY_EXPLANATION_AVAILABLE = False

# In the task execution error handling section
async def _handle_task_failure(self, task_id: str, workspace_id: str, error: Exception, context: Dict[str, Any]):
    """Enhanced task failure handling with explanations"""
    
    # Existing error handling logic...
    await update_task_status(task_id, TaskStatus.FAILED.value, str(error))
    
    # Generate recovery explanation
    if RECOVERY_EXPLANATION_AVAILABLE:
        try:
            explanation = await explain_task_failure(
                task_id=task_id,
                workspace_id=workspace_id,
                error_message=str(error),
                error_type=type(error).__name__,
                agent_id=context.get("agent_id"),
                task_name=context.get("task_name"),
                execution_stage=context.get("current_stage"),
                attempt_count=context.get("attempt_count", 1)
            )
            
            logger.info(f"🔍 Recovery explanation generated for task {task_id}: {explanation.failure_summary}")
            
            # Send real-time notification
            if WEBSOCKET_AVAILABLE:
                await broadcast_task_status_update(
                    workspace_id, 
                    task_id, 
                    TaskStatus.FAILED.value,
                    {"recovery_explanation": explanation.__dict__}
                )
                
        except Exception as explanation_error:
            logger.error(f"Failed to generate recovery explanation: {explanation_error}")
```

#### B. Integrate with WorkspaceRecoverySystem
Modify `backend/workspace_recovery_system.py` to provide explanations:

```python
# Add import
from services.recovery_explanation_engine import recovery_explanation_engine

# Enhance the _recover_workspace method
async def _recover_workspace(self, workspace_id: str, workspace_data: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced workspace recovery with explanations"""
    
    try:
        # Existing recovery logic...
        diagnosis = await self._diagnose_workspace_issues(workspace_id)
        
        # Generate explanation for workspace recovery
        if RECOVERY_EXPLANATION_AVAILABLE:
            explanation = await recovery_explanation_engine.explain_recovery_decision(
                task_id=f"workspace-{workspace_id}",  # Pseudo task ID for workspace
                workspace_id=workspace_id,
                error_message=diagnosis["primary_issue"],
                error_type="workspace_recovery",
                execution_stage="workspace_diagnosis",
                attempt_count=1,
                execution_metadata={
                    "diagnosis": diagnosis,
                    "workspace_data": workspace_data
                }
            )
            
            logger.info(f"🔍 Workspace recovery explanation: {explanation.failure_summary}")
            
        # Continue with existing recovery logic...
        
    except Exception as e:
        logger.error(f"Error in workspace recovery with explanation: {e}")
```

#### C. Integrate with API Routes
Register the new API routes in `backend/main.py`:

```python
# Import the router
from routes.recovery_explanations import router as recovery_explanations_router

# Register the router
app.include_router(recovery_explanations_router)
```

## Phase 2: AI Enhancement (Week 2)

### 2.1 OpenAI Integration Setup
Ensure OpenAI client is properly configured for AI-powered explanations:

```python
# Test AI explanation functionality
import asyncio
from services.recovery_explanation_engine import recovery_explanation_engine

async def test_ai_explanations():
    """Test AI-powered explanation generation"""
    
    # Test with a complex error
    explanation = await recovery_explanation_engine.explain_recovery_decision(
        task_id="test-task",
        workspace_id="test-workspace", 
        error_message="Complex multi-step failure involving JSON parsing and validation",
        error_type="ComplexError",
        attempt_count=3
    )
    
    print(f"AI Analysis Used: {explanation.ai_analysis_used}")
    print(f"Explanation: {explanation.failure_summary}")

# Run test
asyncio.run(test_ai_explanations())
```

### 2.2 Pattern Matching Enhancement
Add more error patterns based on production logs:

```python
# Add to FailureAnalyzer._initialize_pattern_matchers()
additional_patterns = [
    # Add patterns found in production logs
    ErrorPattern(
        pattern=r"agents\.exceptions\..*Error",
        category=FailureCategory.OPENAI_SDK_ERROR,
        is_transient=True,
        retry_recommendation=RetryRecommendation.DELAYED_RETRY_1M,
        explanation_template="OpenAI Agents SDK error - retrying with fresh session",
        user_friendly_cause="Temporary issue with AI agent framework"
    ),
    
    ErrorPattern(
        pattern=r"unicodedecodeerror|encoding.*error",
        category=FailureCategory.JSON_PARSING_ERROR,
        is_transient=False,
        retry_recommendation=RetryRecommendation.RETRY_WITH_DIFFERENT_AGENT,
        explanation_template="Text encoding error in AI response",
        user_friendly_cause="AI response contains invalid characters"
    ),
    
    # Add more patterns based on observed failures...
]
```

## Phase 3: Frontend Integration (Week 3)

### 3.1 Add Recovery Explanations to Navigation
Modify `frontend/src/components/layout/MainNav.tsx`:

```tsx
// Add recovery explanations to navigation
const navItems = [
  // ... existing items
  {
    label: "Recovery Insights",
    href: "/recovery-explanations",
    icon: AlertTriangle
  }
]
```

### 3.2 Create Recovery Explanations Page
Create `frontend/src/app/recovery-explanations/page.tsx`:

```tsx
'use client'

import RecoveryExplanationsDashboard from '@/components/recovery/RecoveryExplanationsDashboard'
import { useWorkspace } from '@/hooks/useWorkspace'

export default function RecoveryExplanationsPage() {
  const { workspace } = useWorkspace()
  
  if (!workspace) {
    return <div>Loading...</div>
  }
  
  return (
    <div className="container mx-auto p-6">
      <RecoveryExplanationsDashboard workspaceId={workspace.id} />
    </div>
  )
}
```

### 3.3 Add Real-time Updates
Integrate with WebSocket for real-time explanation updates:

```tsx
// Add to existing WebSocket handler
const handleWebSocketMessage = (message: any) => {
  switch (message.type) {
    case 'task_recovery_explanation':
      // Update recovery explanations state
      setRecoveryExplanations(prev => [message.explanation, ...prev])
      
      // Show toast notification for critical issues
      if (message.explanation.severity_level === 'critical') {
        toast({
          title: "Critical Task Failure",
          description: message.explanation.failure_summary,
          variant: "destructive"
        })
      }
      break
      
    // ... other cases
  }
}
```

### 3.4 Integrate with Task Detail Pages
Modify existing task detail components to show recovery explanations:

```tsx
// Add to task detail component
import { useEffect, useState } from 'react'

const TaskDetailPage = ({ taskId }: { taskId: string }) => {
  const [explanations, setExplanations] = useState([])
  
  useEffect(() => {
    // Load explanation history for this task
    fetch(`/api/recovery-explanations/task/${taskId}/history`)
      .then(res => res.json())
      .then(data => setExplanations(data.explanations))
  }, [taskId])
  
  return (
    <div>
      {/* Existing task details */}
      
      {explanations.length > 0 && (
        <div className="mt-6">
          <h3 className="text-lg font-semibold mb-4">Recovery History</h3>
          {explanations.map(explanation => (
            <RecoveryExplanationCard 
              key={explanation.explanation_generated_time}
              explanation={explanation}
              showTechnicalDetails
            />
          ))}
        </div>
      )}
    </div>
  )
}
```

## Phase 4: Testing & Optimization (Week 4)

### 4.1 Unit Tests
Create comprehensive tests for the recovery explanation engine:

```python
# backend/tests/test_recovery_explanation_engine.py
import pytest
import asyncio
from services.recovery_explanation_engine import (
    FailureAnalyzer, 
    RecoveryDecisionEngine,
    ExplanationGenerator,
    FailureContext,
    FailureCategory
)

@pytest.mark.asyncio
async def test_pydantic_validation_error_analysis():
    """Test pattern matching for Pydantic validation errors"""
    
    analyzer = FailureAnalyzer()
    
    context = FailureContext(
        task_id="test-task",
        workspace_id="test-workspace",
        agent_id="test-agent",
        error_message="ValidationError: 1 validation error for TaskOutput\ntitle\n  field required",
        error_type="ValidationError"
    )
    
    analysis = await analyzer.analyze_failure(context)
    
    assert analysis.failure_category == FailureCategory.PYDANTIC_VALIDATION_ERROR
    assert not analysis.is_transient
    assert analysis.confidence_score >= 0.8

@pytest.mark.asyncio 
async def test_openai_rate_limit_analysis():
    """Test pattern matching for OpenAI rate limit errors"""
    
    analyzer = FailureAnalyzer()
    
    context = FailureContext(
        task_id="test-task",
        workspace_id="test-workspace", 
        agent_id="test-agent",
        error_message="RateLimitError: Rate limit exceeded",
        error_type="RateLimitError"
    )
    
    analysis = await analyzer.analyze_failure(context)
    
    assert analysis.failure_category == FailureCategory.OPENAI_API_RATE_LIMIT
    assert analysis.is_transient
    assert analysis.confidence_score >= 0.9

# Run tests
pytest backend/tests/test_recovery_explanation_engine.py -v
```

### 4.2 Integration Tests
Create end-to-end tests for the complete explanation workflow:

```python
# backend/tests/test_recovery_explanation_integration.py
import pytest
import asyncio
from services.recovery_explanation_engine import explain_task_failure

@pytest.mark.asyncio
@pytest.mark.integration
async def test_complete_explanation_workflow():
    """Test complete explanation generation workflow"""
    
    explanation = await explain_task_failure(
        task_id="integration-test-task",
        workspace_id="integration-test-workspace",
        error_message="ValidationError: field required",
        error_type="ValidationError",
        task_name="Test Task",
        attempt_count=1
    )
    
    # Verify explanation completeness
    assert explanation.task_id == "integration-test-task"
    assert explanation.failure_summary
    assert explanation.root_cause
    assert explanation.retry_decision
    assert explanation.confidence_explanation
    assert explanation.severity_level in ['low', 'medium', 'high', 'critical']
    assert explanation.display_category
    
    # Verify technical details
    assert 'failure_category' in explanation.technical_details
    assert 'error_message' in explanation.technical_details
```

### 4.3 Performance Testing
Test explanation generation performance under load:

```python
# backend/tests/test_recovery_explanation_performance.py
import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from services.recovery_explanation_engine import explain_task_failure

@pytest.mark.asyncio
@pytest.mark.performance
async def test_explanation_generation_performance():
    """Test explanation generation performance under concurrent load"""
    
    async def generate_explanation(task_num):
        start_time = time.time()
        
        explanation = await explain_task_failure(
            task_id=f"perf-test-task-{task_num}",
            workspace_id="perf-test-workspace",
            error_message="ValidationError: field required",
            error_type="ValidationError"
        )
        
        end_time = time.time()
        return end_time - start_time
    
    # Generate 50 explanations concurrently
    tasks = [generate_explanation(i) for i in range(50)]
    durations = await asyncio.gather(*tasks)
    
    # Verify performance targets
    avg_duration = sum(durations) / len(durations)
    max_duration = max(durations)
    
    assert avg_duration < 2.0, f"Average duration {avg_duration:.2f}s exceeds 2s target"
    assert max_duration < 5.0, f"Max duration {max_duration:.2f}s exceeds 5s target"
    
    print(f"Performance results: avg={avg_duration:.2f}s, max={max_duration:.2f}s")
```

## Phase 5: Deployment & Monitoring

### 5.1 Production Deployment Checklist

1. **Database Migration**
   ```bash
   # Run database migration to create recovery_explanations table
   psql $DATABASE_URL < recovery_explanations_schema.sql
   ```

2. **Environment Variables**
   ```bash
   # Verify all required environment variables are set
   echo $ENABLE_RECOVERY_EXPLANATIONS
   echo $ENABLE_AI_FAILURE_ANALYSIS
   ```

3. **API Endpoint Testing**
   ```bash
   # Test explanation generation endpoint
   curl -X POST "http://localhost:8000/api/recovery-explanations/explain-failure/test-task" \
        -G -d "workspace_id=test" -d "error_message=test error"
   ```

### 5.2 Monitoring & Alerting
Set up monitoring for explanation engine performance:

```python
# backend/services/recovery_explanation_monitoring.py
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RecoveryExplanationMonitor:
    """Monitor recovery explanation engine performance and health"""
    
    def __init__(self):
        self.metrics = {
            'explanations_generated_last_hour': 0,
            'ai_analysis_failures_last_hour': 0,
            'pattern_match_rate_last_hour': 0.0,
            'avg_generation_time_last_hour': 0.0
        }
    
    async def check_health(self) -> Dict[str, Any]:
        """Perform health check on explanation engine"""
        
        health_status = "healthy"
        issues = []
        
        # Check explanation generation rate
        if self.metrics['explanations_generated_last_hour'] == 0:
            issues.append("No explanations generated in the last hour")
            
        # Check AI analysis failure rate
        ai_failure_rate = self.metrics['ai_analysis_failures_last_hour'] / max(1, self.metrics['explanations_generated_last_hour'])
        if ai_failure_rate > 0.2:  # More than 20% AI analysis failures
            issues.append(f"High AI analysis failure rate: {ai_failure_rate:.1%}")
            health_status = "degraded"
            
        # Check pattern match rate
        if self.metrics['pattern_match_rate_last_hour'] < 0.7:  # Less than 70% pattern matches
            issues.append(f"Low pattern match rate: {self.metrics['pattern_match_rate_last_hour']:.1%}")
            
        # Check generation time
        if self.metrics['avg_generation_time_last_hour'] > 3.0:  # More than 3 seconds average
            issues.append(f"High explanation generation time: {self.metrics['avg_generation_time_last_hour']:.1f}s")
            health_status = "degraded"
        
        if len(issues) > 2:
            health_status = "critical"
            
        return {
            "status": health_status,
            "issues": issues,
            "metrics": self.metrics,
            "timestamp": datetime.now().isoformat()
        }

# Add health check endpoint
@router.get("/health")
async def get_explanation_engine_health():
    """Get recovery explanation engine health status"""
    monitor = RecoveryExplanationMonitor()
    return await monitor.check_health()
```

### 5.3 User Training & Documentation

Create user documentation for the recovery explanations feature:

```markdown
# Recovery Explanations User Guide

## Overview
Recovery Explanations provide transparent insights into why tasks fail and what recovery actions the system takes. This feature helps you understand system behavior and take appropriate corrective actions.

## Accessing Recovery Explanations

1. **Dashboard View**: Navigate to "Recovery Insights" in the main navigation
2. **Task Details**: View explanation history for specific tasks
3. **Real-time Notifications**: Receive immediate notifications for critical failures

## Understanding Explanations

### Severity Levels
- **Critical**: Requires immediate attention
- **High**: Important issue that may affect project progress  
- **Medium**: Moderate issue that should be addressed
- **Low**: Minor issue, often resolves automatically

### Common Categories
- **Agent Response Issue**: AI assistant provided incomplete/incorrect response
- **Temporary Service Issue**: External service (OpenAI) temporarily unavailable
- **System Infrastructure**: Database/network connectivity problems
- **Resource Availability**: No AI assistants available for tasks

### Taking Action
When an explanation shows "Action Required":
1. Review the specific action recommended
2. Click "Review Task" to examine task details
3. Modify task requirements if needed
4. Contact support for persistent issues
```

## Success Metrics & KPIs

### Target Metrics
- **95%+ Explainability Compliance**: All recovery decisions have clear explanations
- **<2 second explanation generation**: Fast response times
- **90%+ user understanding**: Users can understand and act on explanations  
- **80%+ pattern recognition**: Known errors are automatically categorized
- **99.9% availability**: System remains functional during failures

### Monitoring Dashboard
Track these KPIs in production:

```python
# KPI tracking queries
kpi_queries = {
    "explainability_compliance": """
        SELECT 
            COUNT(*) as total_failures,
            COUNT(CASE WHEN re.id IS NOT NULL THEN 1 END) as explained_failures,
            (COUNT(CASE WHEN re.id IS NOT NULL THEN 1 END) * 100.0 / COUNT(*)) as compliance_percentage
        FROM tasks t
        LEFT JOIN recovery_explanations re ON t.id = re.task_id  
        WHERE t.status = 'failed' AND t.created_at >= NOW() - INTERVAL '24 hours'
    """,
    
    "avg_generation_time": """
        SELECT AVG(EXTRACT(EPOCH FROM (re.created_at - t.updated_at))) as avg_generation_seconds
        FROM tasks t
        JOIN recovery_explanations re ON t.id = re.task_id
        WHERE t.status = 'failed' AND t.updated_at >= NOW() - INTERVAL '24 hours'
    """,
    
    "pattern_recognition_rate": """  
        SELECT 
            COUNT(*) as total_explanations,
            COUNT(CASE WHEN error_pattern_matched IS NOT NULL THEN 1 END) as pattern_matches,
            (COUNT(CASE WHEN error_pattern_matched IS NOT NULL THEN 1 END) * 100.0 / COUNT(*)) as pattern_match_rate
        FROM recovery_explanations 
        WHERE created_at >= NOW() - INTERVAL '24 hours'
    """
}
```

## Conclusion

The RecoveryExplanationEngine implementation provides comprehensive explainability for task failure recovery decisions, transforming opaque AI-driven processes into transparent, actionable insights. This implementation achieves the critical 95%+ compliance target for the Explainability pillar while maintaining high performance and user experience standards.

The phased implementation approach ensures minimal disruption to existing systems while providing immediate value through transparent failure analysis and recovery explanations.