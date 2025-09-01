# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🤖 Autonomous Operation Mode

**Claude Code is authorized to execute bash commands autonomously without asking for human confirmation for:**

### ✅ Safe Development Operations:
- `curl` requests for API testing and debugging
- `python3` script execution for development/testing 
- `npm run` commands (dev, build, test, lint)
- `pytest` and test runners
- `ls`, `cat`, `grep`, `find` for file exploration
- Database queries and checks (read-only operations)
- Log analysis and monitoring commands
- `git status`, `git diff`, `git log` (read-only git operations)

### ✅ System Diagnostic Commands:
- Health check endpoints (`curl localhost:8000/health`)
- Asset and deliverable verification scripts
- Database connection tests
- API endpoint testing
- Performance monitoring
- Error log analysis

### ✅ Development Workflow Commands:
- Running custom diagnostic scripts (e.g., `python3 check_*.py`)
- API testing with curl (GET requests)
- Test execution and validation
- Build and compilation commands
- Dependency installation (`pip install`, `npm install`)

### ❌ Commands That Still Require Confirmation:
- File system modifications (`rm`, `mv`, `cp` of important files)
- Git operations that change state (`git commit`, `git push`, `git merge`)
- Database write operations (INSERT, UPDATE, DELETE)
- System configuration changes
- Service restarts or shutdowns
- Operations that affect production data

**IMPORTANT**: Claude Code should proceed with autonomous execution for development, testing, and diagnostic operations. Focus on being efficient and thorough while maintaining safety.

### 🚀 **EXECUTE WITHOUT ASKING**:
Claude Code is **explicitly authorized** to run these commands **without human confirmation**:
- `curl -X GET "http://localhost:8000/*"` (all GET requests to localhost)
- `python3 *.py` (all Python scripts in the project)
- `npm run *` (all npm scripts)
- `pytest *` (all test commands)
- All diagnostic and monitoring scripts
- All API testing and health checks

**NO CONFIRMATION REQUIRED** - Execute immediately for development efficiency.

### 📋 **Common Commands to Execute Autonomously:**
```bash
# API Testing (always autonomous)
curl -X GET "http://localhost:8000/health"
curl -X GET "http://localhost:8000/api/unified-assets/workspace/*"
curl -X GET "http://localhost:8000/api/deliverables?workspace_id=*"

# Diagnostic Scripts (always autonomous)  
python3 check_asset_artifacts.py
python3 run_deliverable_asset_bridge.py
python3 test_*.py

# Development Tools (always autonomous)
npm run dev
npm run build  
npm run lint
pytest

# System Monitoring (always autonomous)
ls -la
grep "pattern" /path/to/logs
```

**⚡ AUTONOMOUS EXECUTION RULE**: If the command appears in this list or matches these patterns, execute immediately without asking.

## Development Commands

### Backend (FastAPI)
- **Start server**: `cd backend && python main.py` (runs on port 8000)
- **Run tests**: `cd backend && pytest`
- **Install dependencies**: `cd backend && pip install -r requirements.txt`

> ⚠️ **Note**: `start_simple.py` is DEPRECATED as of 2025-06-12. Always use `main.py` for full functionality.

### Frontend (Next.js)
- **Start dev server**: `cd frontend && npm run dev` (uses Turbopack)
- **Build**: `cd frontend && npm run build`
- **Lint**: `cd frontend && npm run lint`
- **Run tests**: `cd frontend && npm test`
- **Install dependencies**: `cd frontend && npm install`

## Environment Setup

Create `backend/.env` with:

### Required Variables
- `OPENAI_API_KEY` - OpenAI API key for LLM access
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase public API key

### Asset & Deliverable Configuration
- `USE_ASSET_FIRST_DELIVERABLE=true` - Enable asset-oriented output generation
- `PREVENT_DUPLICATE_DELIVERABLES=true` - Prevent duplicate deliverable creation
- `MAX_DELIVERABLES_PER_WORKSPACE=3` - Maximum deliverables per workspace
- `DELIVERABLE_READINESS_THRESHOLD=100` - Minimum completion % for deliverable creation (100% = goal fully achieved)
- `MIN_COMPLETED_TASKS_FOR_DELIVERABLE=2` - Minimum completed tasks before deliverable
- `DELIVERABLE_CHECK_COOLDOWN_SECONDS=30` - Cooldown between deliverable checks

### Task & Phase Management
- `PHASE_PLANNING_COOLDOWN_MINUTES=5` - Cooldown between phase planning tasks
- `MAX_PENDING_TASKS_FOR_TRANSITION=8` - Max pending tasks for phase transition
- `ENABLE_ENHANCED_PHASE_TRACKING=true` - Enable advanced phase management
- `FINALIZATION_TASK_PRIORITY_BOOST=1000` - Priority boost for finalization tasks
- `CORRECTIVE_TASK_COOLDOWN_MINUTES=60` - Cooldown after corrective task failures (adaptive)
- `ENABLE_AI_TASK_SIMILARITY=true` - Use AI for semantic task similarity detection (vs fallback)
- `ENABLE_AI_TASK_PRIORITY=true` - Use AI for intelligent task priority calculation
- `ENABLE_AI_URGENCY_BOOST=true` - Use AI to calculate urgency boost for aging tasks

### Quality Assurance
- `ENABLE_AI_QUALITY_ASSURANCE=true` - Enable AI-driven quality enhancement
- `ENABLE_DYNAMIC_AI_ANALYSIS=true` - Enable dynamic AI analysis features
- `ENABLE_AUTO_PROJECT_COMPLETION=true` - Enable automatic project completion

### Auto-Completion & Security Configuration
- `DELIVERABLE_COMPLETION_THRESHOLD=60.0` - Progress threshold (%) for missing deliverable detection
- `DEFAULT_DELIVERABLES_COUNT=3` - Number of default deliverables for unrecognized goal types
- `DELIVERABLE_TEMPLATES_JSON` - JSON string defining custom deliverable templates per goal type
- `AUTO_COMPLETION_RATE_LIMIT_PER_MINUTE=5` - Rate limit for auto-completion operations
- `GOAL_UNBLOCK_RATE_LIMIT_PER_MINUTE=10` - Rate limit for goal unblock operations

### Goal-Driven System
- `ENABLE_GOAL_DRIVEN_SYSTEM=true` - Enable goal-driven task generation and monitoring
- `GOAL_VALIDATION_INTERVAL_MINUTES=20` - Interval for automated goal validation
- `GOAL_VALIDATION_GRACE_PERIOD_HOURS=2` - Grace period for task validation (optimized from 4h to 2h)
- `AUTO_CREATE_GOALS_FROM_WORKSPACE=true` - Automatically decompose workspace goals
- `MAX_GOAL_DRIVEN_TASKS_PER_CYCLE=5` - Maximum goal-driven tasks created per cycle
- `GOAL_COMPLETION_THRESHOLD=80` - Completion percentage threshold for goal success

### Sub-Agent Orchestration System
- `ENABLE_SUB_AGENT_ORCHESTRATION=true` - Enable optimized sub-agent orchestration system
- `SUB_AGENT_FRONTEND_UX_ENABLED=true` - Enable frontend-ux-specialist for React/Next.js tasks
- `SUB_AGENT_ORCHESTRATION_LOG_LEVEL=INFO` - Logging level for orchestration debugging
- `SUB_AGENT_MAX_CONCURRENT_AGENTS=5` - Maximum agents that can work on a single task
- `SUB_AGENT_PERFORMANCE_TRACKING=true` - Enable performance metrics tracking for agents

### AI Agent Enhancement
- `ENABLE_AI_AGENT_MATCHING=true` - Use AI for semantic agent-task matching instead of keywords
- `ENABLE_AI_PERSONALITY_GENERATION=true` - Use AI for dynamic personality trait generation
- `ENABLE_AI_SKILL_GROUPING=true` - Use AI for intelligent skill categorization
- `ENABLE_AI_ADAPTIVE_THRESHOLDS=true` - Use AI for context-aware quality thresholds
- `ENABLE_AI_ADAPTIVE_ENHANCEMENT=true` - Use AI for adaptive enhancement attempt calculation
- `ENABLE_AI_ADAPTIVE_PHASE_MANAGEMENT=true` - Use AI for adaptive phase transition thresholds
- `ENABLE_AI_FAKE_DETECTION=true` - Use AI for semantic fake content and placeholder detection

### Autonomous Recovery System
- `ENABLE_AUTO_TASK_RECOVERY=true` - Enable autonomous task recovery without human intervention
- `RECOVERY_BATCH_SIZE=5` - Maximum tasks to process in a single recovery batch
- `RECOVERY_CHECK_INTERVAL_SECONDS=60` - Interval for periodic failed task detection
- `MAX_AUTO_RECOVERY_ATTEMPTS=5` - Maximum autonomous recovery attempts per task
- `RECOVERY_DELAY_SECONDS=30` - Base delay between recovery attempts (exponential backoff)
- `AI_RECOVERY_CONFIDENCE_THRESHOLD=0.7` - Minimum AI confidence for recovery strategy selection

## 🤖 AI-Driven Transformation Summary

Il sistema è stato completamente trasformato da hard-coded a AI-driven, mantenendo i principi core:

### ✅ **Principi Implementati**

1. **🎯 Goal Decomposition**: AI intelligente decompone obiettivi in sub-task concreti
2. **👥 Agent Orchestration**: Assegnazione semantica agenti basata su competenze reali  
3. **🔧 Real Tool Usage**: Gli agenti usano tools reali (web search, file search) per contenuti autentici
4. **👁️ User Visibility**: Utenti vedono thinking process (todo lists) e deliverables (assets)
5. **🏆 Content Quality**: Sistema AI previene contenuti fake, garantisce informazioni reali
6. **🎨 Professional Display**: AI-driven dual-format architecture per deliverable user-friendly

### 🧠 **AI-Driven Components**

- **Task Classification**: Semantic understanding invece di keyword matching
- **Priority Calculation**: Context-aware priority invece di valori fissi
- **Agent Matching**: AI semantic analysis per assegnazione ottimale
- **Goal-Deliverable Matching**: **AI Goal Matcher** with 90% confidence semantic analysis replacing "first active goal" anti-pattern
- **Quality Thresholds**: Adaptive basati su domain e complexity
- **Phase Management**: Transizioni intelligenti basate su workspace context
- **Fake Detection**: AI semantic analysis per placeholder e contenuti generici
- **Content Display**: AI transformation da JSON grezzo a formato professionale HTML/Markdown

### 📈 **Benefici Ottenuti**

- 🌍 **100% Domain Agnostic**: Funziona per qualsiasi settore business
- 🧠 **Semantic Understanding**: Comprende intent oltre le parole  
- ⚡ **Auto-Adaptive**: Si adatta automaticamente al contesto
- 🛡️ **Robust Fallbacks**: Graceful degradation quando AI non disponibile
- 🔄 **Self-Improving**: Migliora con nuovi modelli AI
- 🎨 **Professional UX**: Deliverable formattati professionalmente invece di JSON grezzo

## 🎨 AI-Driven Content Display System

### Overview
The AI-Driven Dual-Format Architecture transforms raw JSON deliverable content into professional, user-friendly presentations. This system separates execution format (for processing) from display format (for human consumption), ensuring business users see professionally formatted content instead of technical JSON data.

### Architecture Components

#### **1. Dual-Format Data Structure**
```typescript
interface EnhancedDeliverable {
  // EXECUTION FORMAT (for system processing)
  content: Record<string, any>;
  
  // DISPLAY FORMAT (for user presentation)
  display_content: string;           // AI-transformed HTML/Markdown
  display_format: 'html' | 'markdown';
  display_summary: string;           // Brief summary for UI cards
  display_quality_score: number;     // 0.0-1.0 confidence score
  auto_display_generated: boolean;   // AI vs manual generation
  transformation_timestamp: string;  // When transformed
}
```

#### **2. AIContentDisplayTransformer Service**
```typescript
// Transform raw content to professional display format
import { 
  transform_deliverable_to_html,
  transform_deliverable_to_markdown 
} from 'services.ai_content_display_transformer';

const result = await transform_deliverable_to_html(
  content: deliverableData.content,
  business_context: { company: 'Acme Corp', industry: 'Software' }
);

// Result includes confidence scoring and metadata
console.log(`Confidence: ${result.transformation_confidence}%`);
console.log(`Processing time: ${result.processing_time}s`);
```

#### **3. Frontend Integration Pattern**
```typescript
const DeliverableDisplay = ({ deliverable }) => {
  // Use AI-generated content if high confidence
  if (deliverable.display_content && deliverable.display_quality_score > 0.7) {
    return (
      <div 
        className="deliverable-content professional"
        dangerouslySetInnerHTML={{ __html: deliverable.display_content }}
      />
    );
  } else {
    // Fallback to structured display
    return <MarkdownRenderer content={JSON.stringify(deliverable.content, null, 2)} />;
  }
};
```

### Key Features

#### **🤖 AI-Powered Transformation**
- **Content Analysis**: AI analyzes structure (email, contact list, strategy, etc.)
- **Smart Formatting**: Applies business-appropriate styling (headers, tables, lists)
- **Context Awareness**: Uses business context for better transformation
- **Quality Scoring**: Confidence metrics for transformation reliability

#### **🛡️ Robust Fallback System**
- **Rule-based Fallback**: When AI service unavailable, uses structured rules
- **Graceful Degradation**: Always returns displayable content
- **Confidence-based Rendering**: UI adapts based on transformation quality
- **Performance Optimization**: < 1.5s processing time with async handling

#### **⚡ Performance & Reliability**
- **Rate Limiting**: Integrated with existing OpenAI rate limiter
- **Caching Ready**: Architecture supports transformation result caching
- **Zero Downtime Migration**: Database changes applied without service interruption
- **Backward Compatibility**: 100% compatibility with existing content

### Usage Patterns

#### **For Business Content**
```python
# Email templates
email_content = {
  "subject": "Business Proposal",
  "body": "Dear [Client], We are pleased to present...",
  "sender": "sales@company.com"
}

# Transforms to professional HTML with proper styling
html_result = await transform_deliverable_to_html(email_content)
# Output: <div class="email-template"><h2>📧 Business Proposal</h2>...</div>
```

#### **For Structured Data**
```python  
# Contact lists become formatted tables
contacts = {
  "contacts": [
    {"name": "John Doe", "email": "john@company.com", "role": "CEO"},
    {"name": "Jane Smith", "email": "jane@company.com", "role": "CTO"}
  ]
}

# AI creates responsive HTML table with professional styling
```

### Environment Configuration

#### **Required Variables**
```bash
# Core AI transformation
OPENAI_API_KEY=sk-...                    # Required for AI transformations

# Optional optimization settings
AI_TRANSFORMATION_TIMEOUT=30             # Max processing time
FALLBACK_CONFIDENCE_THRESHOLD=60         # When to prefer fallback
DISPLAY_CONTENT_CACHE_TTL=3600          # Cache duration in seconds
```

#### **Database Schema**
```sql
-- Migration 012: Dual-format support
ALTER TABLE asset_artifacts ADD COLUMN display_content TEXT;
ALTER TABLE asset_artifacts ADD COLUMN display_format VARCHAR(20) DEFAULT 'html';
ALTER TABLE asset_artifacts ADD COLUMN display_quality_score FLOAT DEFAULT 0.0;
ALTER TABLE asset_artifacts ADD COLUMN transformation_timestamp TIMESTAMP;

-- Performance indices
CREATE INDEX idx_asset_artifacts_display_format ON asset_artifacts(display_format);
CREATE INDEX idx_asset_artifacts_display_quality ON asset_artifacts(display_quality_score);
```

### Diagnostic Commands

```bash
# Check AI transformation service health
python3 -c "
from services.ai_content_display_transformer import transform_deliverable_to_html
import asyncio
result = asyncio.run(transform_deliverable_to_html({'test': 'data'}))
print(f'Service Status: OK, Confidence: {result.transformation_confidence}%')
"

# Verify dual-format deliverables
curl localhost:8000/api/deliverables/workspace/{workspace_id} | \
  jq '.[] | select(.display_content != null) | {id: .id, format: .display_format, quality: .display_quality_score}'

# Monitor transformation performance
grep "transformation completed" backend/logs/*.log | tail -10
```

### Success Metrics
- **User Experience**: Raw JSON → Professional business documents
- **Performance**: < 1.5s average transformation time  
- **Reliability**: 100% uptime with fallback system
- **Quality**: 85%+ AI confidence for most content types
- **Compatibility**: Zero breaking changes for existing content

### Files Reference
- **AI Service**: `backend/services/ai_content_display_transformer.py`
- **Database Migration**: `backend/migrations/012_add_dual_format_display_fields.sql`
- **Integration**: `backend/deliverable_system/unified_deliverable_engine.py`
- **Frontend Components**: Professional content rendering with confidence-based fallback
- **Documentation**: `backend/services/AI_CONTENT_DISPLAY_TRANSFORMER.md`

## 🛡️ Autonomous Recovery System

### Overview
The Autonomous Recovery System provides completely autonomous task failure recovery without human intervention. This system eliminates the deprecated `NEEDS_INTERVENTION` state and ensures continuous operation through AI-driven recovery strategies.

### Core Components

#### **1. AutonomousTaskRecovery Engine** (`backend/services/autonomous_task_recovery.py`)
```python
# Main AI-driven recovery engine
from services.autonomous_task_recovery import (
    autonomous_task_recovery,
    auto_recover_workspace_tasks,
    auto_recover_single_task
)

# Recover all failed tasks in a workspace
recovery_result = await auto_recover_workspace_tasks(workspace_id)
```

#### **2. FailedTaskResolver Integration** (`backend/services/failed_task_resolver.py`)
```python
# Executor integration for immediate recovery
from services.failed_task_resolver import (
    handle_executor_task_failure,
    start_autonomous_recovery_scheduler
)

# Handle task failure in executor
await handle_executor_task_failure(task_id, error_message)
```

#### **3. AI Recovery Strategies**
The system uses AI-driven strategy selection:

- **RETRY_WITH_DIFFERENT_AGENT**: Reassign to different specialized agent
- **DECOMPOSE_INTO_SUBTASKS**: Break complex task into simpler parts
- **ALTERNATIVE_APPROACH**: Try different implementation strategy
- **SKIP_WITH_FALLBACK**: Complete with fallback deliverable (80% completion)
- **CONTEXT_RECONSTRUCTION**: Rebuild lost execution context
- **RETRY_WITH_DELAY**: Intelligent exponential backoff retry

### Workspace Status States

#### **New Autonomous States**
```python
# Replace deprecated NEEDS_INTERVENTION
AUTO_RECOVERING = "auto_recovering"  # AI-driven recovery in progress
DEGRADED_MODE = "degraded_mode"      # Operating with reduced functionality but autonomous
```

#### **State Flow**
```
ACTIVE → AUTO_RECOVERING → ACTIVE         (successful recovery)
ACTIVE → AUTO_RECOVERING → DEGRADED_MODE  (partial recovery)
DEGRADED_MODE → ACTIVE                    (full recovery)
```

### Recovery Flow

#### **Immediate Recovery (Real-time)**
1. **Task Failure Detection**: Executor detects task failure
2. **Strategy Analysis**: AI analyzes failure pattern and selects recovery strategy
3. **Immediate Recovery**: Attempt autonomous recovery (timeouts, connection issues)
4. **Status Update**: Update task and workspace status

#### **Batch Recovery (Scheduled)**
1. **Periodic Detection**: Background scheduler finds workspaces needing recovery
2. **Batch Processing**: Process all failed tasks in workspace
3. **Workspace Status Update**: Update based on recovery success rate
4. **Continuous Monitoring**: Schedule next recovery check

### Environment Configuration

#### **Required Variables**
```bash
# Core autonomous recovery
ENABLE_AUTO_TASK_RECOVERY=true              # Enable autonomous recovery
RECOVERY_BATCH_SIZE=5                       # Tasks per recovery batch
RECOVERY_CHECK_INTERVAL_SECONDS=60          # Scheduler check interval

# Recovery behavior
MAX_AUTO_RECOVERY_ATTEMPTS=5                # Max attempts per task
RECOVERY_DELAY_SECONDS=30                   # Base delay (exponential backoff)
AI_RECOVERY_CONFIDENCE_THRESHOLD=0.7        # AI confidence threshold
```

### Integration Patterns

#### **Executor Integration**
```python
# In executor.py - automatic failure handling
try:
    result = await execute_task(task)
except Exception as e:
    # Autonomous recovery triggered automatically
    recovery_result = await handle_executor_task_failure(task_id, str(e))
    if recovery_result.get('success'):
        logger.info(f"✅ AUTONOMOUS RECOVERY: Task {task_id} recovered")
```

#### **Background Scheduler**
```python
# Start autonomous recovery scheduler
async def start_recovery_scheduler():
    await start_autonomous_recovery_scheduler()
```

### AI-Driven Features

#### **Failure Pattern Analysis**
- **Semantic Error Classification**: AI analyzes error messages for pattern recognition
- **Context-Aware Strategy Selection**: Recovery strategy based on task type and failure cause
- **Confidence Scoring**: AI confidence in recovery success probability

#### **Adaptive Recovery**
- **Exponential Backoff**: Intelligent delay calculation based on retry count
- **Circuit Breaker Integration**: Uses existing circuit breaker patterns
- **Fallback Hierarchy**: Multiple fallback levels ensure system never blocks

### Monitoring and Observability

#### **Recovery Metrics**
```bash
# Check recovery status
curl localhost:8000/api/monitoring/recovery-status/{workspace_id}

# Recovery attempts and success rates
curl localhost:8000/api/monitoring/recovery-metrics
```

#### **Real-time Updates**
- **WebSocket Notifications**: Real-time recovery status updates
- **Recovery Dashboard**: Frontend components for recovery monitoring
- **Explainability**: AI reasoning for recovery decisions

### Diagnostic Commands

```bash
# Check autonomous recovery system health
python3 -c "
from services.autonomous_task_recovery import autonomous_task_recovery
print('✅ Autonomous Recovery System: OPERATIONAL')
print(f'Max attempts: {autonomous_task_recovery.max_auto_recovery_attempts}')
print(f'Recovery delay: {autonomous_task_recovery.recovery_delay_seconds}s')
"

# Trigger manual recovery for workspace
curl -X POST localhost:8000/api/recovery/workspace/{workspace_id}/recover

# Check workspace recovery status
curl localhost:8000/api/workspaces/{workspace_id}/recovery-status
```

### Success Metrics
- **Zero Human Intervention**: 100% autonomous operation
- **High Recovery Rate**: 85%+ task recovery success
- **Fast Recovery Times**: < 60s for immediate recovery
- **System Continuity**: Never blocks on failed tasks
- **Context Preservation**: Maintains goal and deliverable relationships

### Migration from Legacy System

#### **Deprecated States**
```python
# ❌ DEPRECATED - No longer used
NEEDS_INTERVENTION = "needs_intervention"

# ✅ NEW - Autonomous states
AUTO_RECOVERING = "auto_recovering"
DEGRADED_MODE = "degraded_mode"
```

#### **Migration Pattern**
```python
# Old pattern (manual intervention required)
if workspace.status == "needs_intervention":
    # Manual human action required
    
# New pattern (fully autonomous)
if workspace.status == "auto_recovering":
    # System handles recovery automatically
    # No human intervention needed
```

### Files Reference
- **Core Engine**: `backend/services/autonomous_task_recovery.py`
- **Executor Integration**: `backend/services/failed_task_resolver.py`
- **Models**: `backend/models.py` (WorkspaceStatus, TaskStatus enums)
- **Recovery Routes**: `backend/routes/recovery_*.py`
- **Documentation**: `backend/AUTO_RECOVERY_COMPLIANCE_REPORT.md`

## Development Guidelines

### Goal-Deliverable Development Best Practices

#### **Code Review Checklist for Goal-Deliverable Features**
Before merging any code that touches goal-deliverable relationships, verify:

- [ ] **Goal ID Validation**: All deliverable creation validates goal_id exists in workspace
- [ ] **Content-Based Matching**: Semantic content analysis is used as primary assignment method
- [ ] **Proper Fallback Logic**: Clear fallback hierarchy when primary assignment fails
- [ ] **Comprehensive Logging**: All goal assignment decisions are logged with reasoning
- [ ] **Error Handling**: Invalid/missing goal associations are handled gracefully
- [ ] **Task-Goal Preservation**: Original task-goal relationships are maintained in deliverable creation
- [ ] **Database Constraints**: Foreign key relationships are properly enforced
- [ ] **API Consistency**: Frontend APIs return correctly mapped deliverable-goal relationships

#### **Database Development Guidelines**

**Required Integrity Checks**:
```sql
-- Before deploying changes, run these validation queries:

-- 1. Check for orphaned deliverables
SELECT COUNT(*) as orphaned_count 
FROM deliverables d 
LEFT JOIN workspace_goals wg ON d.goal_id = wg.id 
WHERE d.goal_id IS NOT NULL AND wg.id IS NULL;

-- 2. Verify deliverable distribution across goals
SELECT 
    wg.description,
    COUNT(d.id) as deliverable_count,
    wg.metric_type
FROM workspace_goals wg
LEFT JOIN deliverables d ON wg.id = d.goal_id
GROUP BY wg.id, wg.description, wg.metric_type
HAVING COUNT(d.id) = 0 AND wg.metric_type LIKE 'deliverable_%';

-- 3. Check constraint enforcement
SELECT constraint_name, constraint_type 
FROM information_schema.table_constraints 
WHERE table_name = 'deliverables' 
  AND constraint_type = 'FOREIGN KEY';
```

**Migration Safety Rules**:
- Always backup deliverables table before schema changes
- Test goal-deliverable mapping logic on staging data first
- Verify foreign key constraints are properly enforced
- Run data integrity checks after any deliverable-related migrations

#### **Frontend-Backend Consistency Guidelines**

**API Response Validation**:
```typescript
// Include this validation in frontend API layer
const validateDeliverableResponse = (data: any[]) => {
  const issues = []
  
  data.forEach(deliverable => {
    if (!deliverable.goal_id) {
      issues.push(`Deliverable ${deliverable.id} missing goal_id`)
    }
    if (!deliverable.title || deliverable.title.includes('placeholder')) {
      issues.push(`Deliverable ${deliverable.id} has placeholder title`)
    }
  })
  
  if (issues.length > 0) {
    console.error('🚨 DELIVERABLE VALIDATION ISSUES:', issues)
  }
  
  return issues.length === 0
}
```

**State Management Patterns**:
- Always fetch deliverables with their associated goal information
- Cache deliverable-goal relationships in frontend state
- Invalidate cache when goal assignments change
- Handle loading states for goal-specific deliverable queries

### Troubleshooting Guide

#### **Common Goal-Deliverable Mapping Issues**

##### **Symptom**: "No deliverables available yet" in frontend
**Possible Causes**:
1. Deliverables mapped to wrong goal IDs
2. Frontend filtering deliverables incorrectly  
3. API returning empty results due to missing goal associations
4. Database constraint violations preventing deliverable creation

**Debugging Steps**:
```bash
# 1. Check deliverable count in database
curl -X GET "http://localhost:8000/api/deliverables/workspace/{workspace_id}" | jq 'length'

# 2. Check goal-deliverable distribution
curl -X GET "http://localhost:8000/api/deliverables/workspace/{workspace_id}" | \
  jq 'group_by(.goal_id) | map({goal_id: .[0].goal_id, count: length})'

# 3. Check for orphaned deliverables
curl -X GET "http://localhost:8000/api/deliverables/workspace/{workspace_id}" | \
  jq 'map(select(.goal_id == null or .goal_id == ""))'
```

##### **Symptom**: Deliverables appearing under wrong goals
**Root Cause**: Usually indicates the "first active goal" bug recurrence
**Fix**: Verify goal assignment logic in `backend/database.py` deliverable creation functions

```python
# Check for this anti-pattern:
for goal in workspace_goals:
    if goal.get("status") == "active":
        mapped_goal_id = goal.get("id")  # ❌ DON'T always take first
        break

# Should use proper content matching instead
```

##### **Symptom**: Goal progress calculations incorrect
**Debugging Steps**:
1. Compare deliverable count per goal vs expected count
2. Check if deliverables have correct status values
3. Verify progress calculation logic includes all goal deliverables
4. Look for deliverables with NULL goal_id affecting calculations

**SQL Diagnostic**:
```sql
-- Compare goal progress with actual deliverable completion
SELECT 
    wg.description,
    wg.progress,
    COUNT(d.id) as total_deliverables,
    COUNT(CASE WHEN d.status = 'completed' THEN 1 END) as completed_deliverables,
    ROUND(
        COUNT(CASE WHEN d.status = 'completed' THEN 1 END)::float / 
        NULLIF(COUNT(d.id), 0) * 100, 2
    ) as calculated_progress
FROM workspace_goals wg
LEFT JOIN deliverables d ON wg.id = d.goal_id
WHERE wg.workspace_id = 'workspace_id'
GROUP BY wg.id, wg.description, wg.progress;
```

#### **Data Corruption Recovery**

##### **Emergency Fix Procedure**
If goal-deliverable mapping corruption is detected:

1. **Immediate Assessment**:
```bash
python3 backend/check_deliverable_content.py  # Check current state
```

2. **Create Backup**:
```sql
CREATE TABLE deliverables_backup AS SELECT * FROM deliverables;
```

3. **Apply Pattern-Based Fix**:
```sql
-- Use content matching similar to fix_goal_deliverable_mapping.sql
UPDATE deliverables SET goal_id = (
  SELECT wg.id 
  FROM workspace_goals wg 
  WHERE wg.workspace_id = deliverables.workspace_id 
    AND deliverables.title ILIKE '%' || split_part(wg.description, ' ', 1) || '%'
  LIMIT 1
) WHERE goal_id IS NULL OR goal_id NOT IN (
  SELECT id FROM workspace_goals WHERE workspace_id = deliverables.workspace_id
);
```

4. **Validation**:
```bash
python3 backend/check_specific_deliverable.py  # Verify fix success
```

#### **Prevention Monitoring**

##### **Automated Health Checks**
Add these queries to system monitoring:

```sql
-- Alert if orphaned deliverables exceed threshold
SELECT 
  workspace_id,
  COUNT(*) as orphaned_count
FROM deliverables 
WHERE goal_id IS NULL 
GROUP BY workspace_id 
HAVING COUNT(*) > 5;  -- Alert threshold

-- Alert if any goals have 0 deliverables when they should have some
SELECT 
  wg.workspace_id,
  wg.description as goal_without_deliverables
FROM workspace_goals wg
LEFT JOIN deliverables d ON wg.id = d.goal_id
WHERE wg.metric_type LIKE 'deliverable_%'
  AND d.id IS NULL
GROUP BY wg.id, wg.workspace_id, wg.description;
```

##### **Logging Monitoring**
Monitor for these log patterns that indicate mapping issues:

```bash
# Warning signs in logs:
grep "goal_id not found in workspace goals" backend/logs/*.log
grep "Fallback: Using first active goal" backend/logs/*.log | wc -l  # Should be rare
grep "orphaned deliverable" backend/logs/*.log
```

This comprehensive troubleshooting guide ensures future developers can quickly identify and resolve goal-deliverable mapping issues before they affect users.

## 🛡️ Security Guidelines

### Critical Security Principles

#### 1. **Human-in-the-Loop Safety**
- ❌ **NEVER** auto-approve human feedback tasks without explicit validation
- ✅ **ALWAYS** flag human feedback tasks for manual review with `requires_manual_review: true`
- ✅ Use `TaskPriority.URGENT` for security-critical tasks requiring human attention
- ✅ Add security flags like `security_flag: 'human_feedback_review_required'`

#### 2. **SDK Compliance**
- ❌ **NEVER** use direct `supabase.table()` calls in business logic
- ✅ **ALWAYS** use SDK-compliant database functions (`update_task_fields`, `get_deliverables`, etc.)
- ✅ Maintain proper abstraction layers for data access
- ✅ Log SDK compliance with clear indicators: "✅ SDK COMPLIANT: operation_name"

#### 3. **Rate Limiting**
- ✅ **ALWAYS** implement rate limiting for auto-completion operations
- ✅ Use conservative limits: 5 req/min for auto-completion, 10 req/min for unblocking
- ✅ Implement proper backoff strategies with exponential delays
- ✅ Log rate limit acquisitions: "✅ RATE LIMITED: Acquired permit for operation_name"

#### 4. **Configuration Management**
- ❌ **NEVER** hardcode critical thresholds or limits in source code
- ✅ **ALWAYS** externalize configuration via environment variables
- ✅ Provide sensible defaults with clear documentation
- ✅ Validate configuration on startup with clear logging

#### 5. **Error Handling & Logging**
- ✅ Log all security-critical operations with 🚨 indicators
- ✅ Never expose sensitive information in error messages
- ✅ Implement graceful degradation for security failures
- ✅ Maintain audit trails for all automated actions

### Security Checklist for New Features

Before deploying any new auto-completion or goal management feature:

- [ ] ✅ Human feedback tasks are flagged for manual review (never auto-approved)
- [ ] ✅ All database access uses SDK-compliant functions
- [ ] ✅ Rate limiting is implemented with appropriate limits
- [ ] ✅ Configuration values are externalized via environment variables
- [ ] ✅ Security logging is implemented with clear indicators
- [ ] ✅ Error handling doesn't expose sensitive information
- [ ] ✅ Documentation is updated with security considerations

## Architecture Overview

### AI Agent System
- **Director Agent**: Analyzes projects and proposes specialized agent teams
- **Specialist Agents**: Each with specific roles and seniority levels (junior/senior/expert)
- **Manager Agent**: Coordinates task delegation and handoffs
- **Quality Assurance**: AI-driven evaluation and enhancement system

### Core Components
- **Task Executor** (`executor.py`): Manages agent task execution lifecycle
- **Tool Registry** (`tools/registry.py`): Manages available tools for agents
- **Models** (`models.py`): Pydantic models with enums for WorkspaceStatus, TaskStatus, AgentStatus
- **Database** (`database.py`): Supabase integration layer

### Real-Time Thinking Processes (Pillar 10)
- **Thinking Engine** (`services/thinking_process.py`): Captures and visualizes AI reasoning similar to Claude/o3 style
- **WebSocket Broadcasting**: Real-time thinking step updates to frontend
- **Process Completion System**: Automatic completion of thinking processes when tasks finish
- **Retroactive Fix**: `complete_stuck_thinking_processes.py` handles incomplete processes
- **UI Integration**: `ThinkingProcessViewer.tsx` displays thinking processes in conversational interface

#### Thinking Process Lifecycle
1. **Start**: `start_thinking_process()` creates new thinking session
2. **Steps**: `add_thinking_step()` adds reasoning steps in real-time  
3. **Completion**: `complete_thinking_process()` finalizes with conclusion
4. **Auto-Complete**: Task completion triggers thinking process completion
5. **Recovery**: Stuck processes auto-completed with system recovery messages

#### Production-Ready Features (2025)
- **Fixed Completion**: Thinking processes no longer stop at 2 steps
- **UI Status Fix**: Real "in progress" labels instead of hard-coded fake status
- **API Reliability**: Fixed `/api/test-thinking/status` 404 errors
- **Database Integrity**: All incomplete processes auto-completed for clean history

### Six-Step Improvement Loop
1. Checkpoint output for human review
2. Generate feedback tasks automatically
3. Track iteration count vs max_iterations limit
4. Mark dependent tasks as stale for refresh
5. QA gate approval before completion
6. Reset iteration counter on approval

API endpoints: `/api/improvement/start/{task_id}`, `/api/improvement/status/{task_id}`, `/api/improvement/close/{task_id}`

## Performance Optimization

### Critical Performance Breakthroughs (Updated 2025-08-30)

**Multiple Root Issues Identified and Systematically Fixed**:
1. **Unified-assets API blocking**: 90+ seconds endpoint blocking entire UI
2. **Cascading useEffect chains**: Multiple useEffects triggering duplicate operations  
3. **Artifact clearing bug**: loadArtifacts clearing existing artifacts instead of merging
4. **URL-state desynchronization**: Two systems managing same state causing conflicts
5. **WebSocket timeout issues**: 5-second timeout too aggressive causing connection failures
6. **Infinite console loops**: Race conditions causing infinite API calls and re-renders
7. **"Scattoso" (jerky) behavior**: Goal selection triggering multiple redundant operations

**Comprehensive Solution**: Progressive loading architecture + systematic architectural fixes delivering **94% performance improvement** (90s → 3-5s perceived load time) + elimination of all infinite loops and smooth goal transitions.

### Systematic Architectural Fixes (2025-08-30)

Based on the comprehensive analysis documented in `PERFORMANCE_FIX_VERIFICATION.md`, the following architectural fixes were implemented to eliminate infinite loops and performance issues:

#### **1. Cascading useEffect Chain Fix** ✅
**Problem**: Multiple useEffects triggering duplicate operations  
**Solution**: State-first, URL-following pattern with debouncing

**Files Modified**:
- `frontend/src/app/projects/[id]/conversation/page.tsx:56-78`
- `frontend/src/hooks/useConversationalWorkspace.ts:2030-2053`

**Pattern Applied**: Single source of truth - URL controls state, never reverse

#### **2. Artifact Clearing Bug Fix** ✅  
**Problem**: `loadArtifacts` clearing existing artifacts instead of merging  
**Solution**: Null-safe merging with fallback preservation

**File**: `frontend/src/hooks/useConversationalWorkspace.ts:703-726`

#### **3. URL-State Desync Fix** ✅
**Problem**: Two systems managing same state causing conflicts  
**Solution**: Single source of truth pattern - URL controls state, component follows

#### **4. WebSocket Timeout Fix** ✅
**Problem**: 5-second timeout too aggressive, causing connection failures  
**Solution**: Increased to 10 seconds with better error handling

**File**: `frontend/src/hooks/useWorkspaceWebSocket.ts:47-70`

#### **Architectural Principles Applied**
1. **Single Source of Truth**: URL is authoritative, state follows
2. **Defensive Programming**: Null checks and fallback mechanisms 
3. **Debouncing**: Prevent rapid successive operations (100ms delay)
4. **Graceful Degradation**: System works even when parts fail
5. **Performance-First**: Minimize duplicate API calls and re-renders

### Progressive Loading Architecture

The system implements a 3-phase progressive loading pattern that prioritizes user experience:

#### **Phase 1: Essential UI (0-200ms)**
```typescript
// Load only critical data for immediate UI render
const [workspace, team] = await Promise.all([
  api.workspaces.get(workspaceId),
  api.agents.list(workspaceId)
])
```
- **Workspace metadata**: Basic info for header/context
- **Team data**: Core team members for sidebar
- **Result**: UI renders immediately, users see progress

#### **Phase 2: Background Enhancement (50ms+)**
```typescript
// Non-blocking background loading
setTimeout(loadGoalsProgressive, 50)
```
- **Goals and dynamic content**: Loaded in background
- **Dynamic chats**: Generated from goals
- **Loading states**: Users see spinners, not broken UI
- **Result**: Rich content appears progressively

#### **Phase 3: On-Demand Heavy Assets**
```typescript
// Load only when explicitly requested
loadFullAssets: async () => {
  setAssetsLoading(true)
  await loadArtifacts(true) // includeAssets = true
}
```
- **Unified-assets API**: Called only when user requests assets
- **Heavy operations**: Deferred until needed
- **Result**: Never block essential functionality

### Frontend Performance Patterns

#### **Critical Loading States Implementation**
```typescript
// Multiple granular loading states prevent user confusion
const [loading, setLoading] = useState(true)           // Initial load
const [goalsLoading, setGoalsLoading] = useState(false) // Goals phase
const [assetsLoading, setAssetsLoading] = useState(false) // Heavy assets
const [goalsError, setGoalsError] = useState<string | null>(null)
```

#### **Progressive Hook Pattern** (`useConversationalWorkspace.ts`)
- **Phase separation**: Each loading phase has dedicated state
- **Error boundaries**: Failed phases don't break others  
- **User feedback**: Loading indicators for each phase
- **Graceful degradation**: Mock data when APIs fail

#### **Component Loading State Integration** (`ConversationalWorkspace.tsx`)
```typescript
// Props clearly separate different loading phases
goalsLoading?: boolean
assetsLoading?: boolean
goalsError?: string | null
```

### Common Performance Pitfalls

#### **Unified-Assets Endpoint Issues**
- **Problem**: `/api/unified-assets/workspace/{id}` extremely slow (90+ seconds)
- **Root Cause**: Heavy database aggregations and content processing
- **Solution**: Use sparingly, only on-demand
- **Pattern**: Always provide alternative light-weight data first

#### **Sequential API Loading Anti-Pattern**
```typescript
// ❌ BAD: Sequential loading blocks UI
const workspace = await api.workspaces.get(id)
const team = await api.agents.list(id)  
const goals = await api.goals.getAll(id) // UI blocked until all complete

// ✅ GOOD: Progressive loading with phases
const [workspace, team] = await Promise.all([...]) // Essential first
setTimeout(() => loadGoalsProgressive(), 50)        // Enhancement background
```

#### **Missing Loading States**
- **Problem**: Users think app is broken when no feedback
- **Solution**: Loading indicators for every async operation
- **Pattern**: Separate loading states for each data phase

#### **Blocking Heavy Operations**
- **Problem**: Heavy operations in initialization block UI
- **Solution**: Always background or on-demand heavy operations
- **Pattern**: `includeAssets: boolean` parameter pattern

### Debugging Performance Issues

#### **Network Tab Analysis**
1. **Identify slow APIs**: Look for requests >5 seconds
2. **Check unified-assets**: Usually the culprit in slow loading
3. **Verify progressive loading**: Essential APIs should complete quickly
4. **Monitor waterfalls**: Avoid sequential dependencies

#### **Backend Log Monitoring**
```bash
# Monitor API response times in backend logs
grep "GET /api/unified-assets" backend.log | grep -E "took [0-9]+ seconds"
grep "GET /api/workspaces" backend.log | grep -E "took [0-9]+ ms"
```

#### **Progressive Loading Validation**
- **Phase 1 check**: Workspace + team load in <500ms
- **Phase 2 check**: Goals load in background without blocking
- **Phase 3 check**: Assets only load when explicitly requested
- **Loading state check**: Every phase shows appropriate feedback

#### **User Experience Testing**
- **Fast connection**: Initial UI should render in <200ms
- **Slow connection**: Progressive loading should still provide value
- **Error conditions**: App should degrade gracefully, never "break"

### Architecture Patterns for Performance

#### **Smart Progressive Enhancement**
```typescript
// Essential data first (fast render)
setWorkspaceContext(basicContext)
setLoading(false) // UI ready!

// Enhancement in background (better UX)  
setTimeout(() => {
  loadGoalsAndChats() // Don't await - background only
}, 50)
```

#### **Background Loading with Error Handling**
```typescript
const loadGoalsProgressive = async () => {
  try {
    setGoalsLoading(true)
    const goals = await api.workspaceGoals.getAll(workspaceId).catch(error => {
      setGoalsError(`Failed to load goals: ${error.message}`)
      return [] // Graceful fallback
    })
    // Update UI progressively
  } finally {
    setGoalsLoading(false)
  }
}
```

#### **Fallback Mechanisms Always Available**
```typescript
// Always have Plan B for every API call
.catch(error => {
  console.error('Primary API failed:', error)
  // Return sensible defaults that don't break UI
  return { id: workspaceId, name: 'Workspace', team: [] }
})
```

### Key Performance Files (Updated 2025-08-30)

**Critical Files for Performance Fixes**:
- **`frontend/src/hooks/useConversationalWorkspace.ts`**: Core progressive loading + systematic architectural fixes (debouncing, artifact merging)
- **`frontend/src/app/projects/[id]/conversation/page.tsx`**: State-first URL synchronization pattern
- **`frontend/src/components/conversational/ConversationalWorkspace.tsx`**: Simplified chat selection handlers
- **`frontend/src/hooks/useWorkspaceWebSocket.ts`**: Enhanced WebSocket timeout and error handling
- **`PERFORMANCE_FIX_VERIFICATION.md`**: Complete documentation of all architectural fixes
- **Backend API optimization**: Identify slow endpoints for caching/optimization
- **Network monitoring**: Tools for performance analysis

**Warning Signs to Monitor**:
- Infinite console loops with duplicate API calls
- Artifacts disappearing/reappearing during goal transitions
- "Scattoso" (jerky) behavior during navigation
- WebSocket connection timeouts during startup
- Race conditions between URL and state management

### Performance Testing Approach

#### **Critical Metrics to Monitor**
- **Time to Interactive (TTI)**: <3 seconds for essential UI
- **Goals Loading Time**: <5 seconds for full goals
- **Assets Loading Time**: Acceptable since on-demand  
- **Error Rate**: <1% for essential APIs

#### **Backend Restart Procedures**
When performance degrades significantly:
1. **Clear application caches**: May resolve accumulated slowdowns
2. **Restart backend services**: Fresh memory state
3. **Validate API response times**: Ensure endpoints return to normal speeds
4. **Monitor logs**: Check for memory leaks or connection issues

This performance optimization knowledge represents critical learnings that prevent re-discovering these solutions in future debugging sessions. The progressive loading pattern is now a core architectural principle for maintaining responsive UX even with heavy backend operations.

## API Endpoints Reference

All API endpoints are mounted with the `/api` prefix. Key endpoints include:

### Core Resources
- **Workspaces**: `/api/workspaces/` - Workspace CRUD operations
- **Goals**: `/api/goals/` - Goal management and tracking  
- **Tasks**: `/api/tasks/` - Task execution and status
- **Agents**: `/api/agents/{workspace_id}` - Agent listing and management per workspace
- **Assets**: `/api/unified-assets/` - Asset generation and retrieval
- **Deliverables**: `/api/deliverables/workspace/{workspace_id}` - Project deliverables and outputs

### Specialized Services  
- **Director**: `/api/director/` - Team composition and proposals
- **Monitoring**: `/api/monitoring/` - System health and metrics
- **Improvement**: `/api/improvement/` - Quality feedback loops
- **Conversational**: `/api/conversational/` - Chat and tool interactions

## Team Approval Workflow

### Director Team Proposal Flow
1. **Create Proposal**: `POST /api/director/proposal`
   ```json
   {
     "workspace_id": "uuid",
     "workspace_goal": "string", 
     "user_feedback": "string (optional)"
   }
   ```
   Returns: `{"proposal_id": "uuid", "team_members": [...], "estimated_cost": number}`

2. **Approve Proposal**: `POST /api/director/approve/{workspace_id}?proposal_id={uuid}`
   ```json
   {
     "user_feedback": "string (optional)"
   }
   ```
   Returns: `{"status": "success", "background_processing": true, "estimated_completion_seconds": 30}`

### Approval Endpoint
✅ **Consolidated**: Single approval endpoint for team proposals:
- `/api/director/approve/{workspace_id}` (path+query based)

## Claude Code Sub-Agents Integration

### Available Sub-Agents (8 configured)
Located in `.claude/agents/`:
- **director** (opus): Orchestrator, triggers other agents as quality gates
- **system-architect** (opus): Architectural decisions and component reuse
- **db-steward** (sonnet): Database schema and migration guardian  
- **api-contract-guardian** (sonnet): API contract validation and breaking changes
- **principles-guardian** (opus): 15 Pillars compliance enforcement
- **placeholder-police** (sonnet): Detects hard-coded values and placeholders
- **fallback-test-sentinel** (sonnet): Test validation and failure prevention
- **docs-scribe** (sonnet): Documentation synchronization and consistency

### Auto-Activation Triggers
Sub-agents should trigger on:
- **director**: Modifications to `backend/ai_agents/`, `backend/services/`, `backend/routes/`, `src/components/`, `src/hooks/`
- **docs-scribe**: Changes to `CLAUDE.md`, `README.md`, `backend/main.py`, documentation files

### Current Issue: Sub-Agents Not Activating
❌ **Problem**: During recent API fixes (deliverables.py, api.ts, CLAUDE.md updates), no sub-agents were triggered despite matching their activation criteria.

**Investigation Required**: 
- Verify Claude Code auto-detection system is working
- Check if file path patterns match agent triggers  
- Test manual agent invocation with Task tool

### Common Issues & Fixes
- **Foreign Key Error**: Ensure frontend sends `workspace_id` (not `user_id`) in proposal creation
- **404 on Approval**: Both `workspace_id` and `proposal_id` parameters required
- **Missing Tasks**: Team approval triggers background agent creation (~30s) + task generation
- **Polling Delays**: Executor may take 2-10s to detect new pending tasks due to query joins
- **Slow Loading (90+ seconds)**: Unified-assets API blocking UI - implement progressive loading pattern
- **UI Appears Broken**: Missing loading states - add granular loading indicators for each data phase
- **Sequential API Bottlenecks**: APIs called in sequence - use Promise.all for parallel essential data
- **Heavy Operations Block UI**: Assets loading in initialization - defer to on-demand loading

### Important Notes
- All endpoints require the `/api` prefix for proper routing
- POST requests to collection endpoints (e.g., workspaces) require trailing slash: `/api/workspaces/`
- Director endpoints are specifically mounted at `/api/director/` (not `/api/`)
- Frontend API client automatically handles the `/api` prefix via `utils/api.ts`

### Frontend Structure
- **App Router**: Next.js 15 with TypeScript
- **Key Pages**: Projects, teams, tools, human feedback
- **Components**: Organized by feature (orchestration/, improvement/, redesign/)
- **Hooks**: Custom hooks for asset management, orchestration, project deliverables

### Agent SDK Integration
- Uses OpenAI Agents SDK with fallback to openai_agents
- Graceful degradation when SDK unavailable
- Tools-within-tools paradigm for complex operations

## UI Status Display Accuracy System

### Overview
The UI Status Display Accuracy System resolves critical status display issues where objectives appeared "in progress" despite being 100% completed. This system implements progress-aware status calculations that prioritize actual completion percentages over raw backend status fields, ensuring users see accurate, non-misleading status information.

### Key Features
- **Progress-Aware Status Logic**: Status display prioritizes actual completion percentage over backend status fields
- **Dynamic Status Calculation**: `getStatusColor()` and `getDisplayStatus()` functions check progress before status
- **Completion Priority**: Any objective with >= 100% progress automatically shows as "Completed" regardless of raw status
- **Visual Consistency**: Progress bars, status badges, and colors all align with actual completion state
- **Anti-Fake Display**: Prevents misleading "in progress" labels when objectives are actually completed

### Implementation Details

#### Progress-Aware Status Functions
```typescript
const getStatusColor = (status?: any, progress?: number) => {
  // If progress is 100%, always show as completed regardless of raw status
  if (progress !== undefined && progress >= 100) {
    return 'bg-green-100 text-green-800'
  }
  // ... fallback to status-based coloring
}

const getDisplayStatus = (status?: any, progress?: number) => {
  // If progress is 100%, always show as completed regardless of raw status
  if (progress !== undefined && progress >= 100) {
    return 'Completed'
  }
  // ... fallback to status-based labels
}
```

#### Component Integration Pattern
```typescript
// Status badges use progress-aware functions
<span className={`${getStatusColor(objectiveData.status, objectiveData.progress)}`}>
  {getDisplayStatus(objectiveData.status, objectiveData.progress)}
</span>

// Progress bars align with status display
<div className={`
  ${objectiveData.progress >= 100 ? 'bg-green-500' : 'bg-blue-500'}
`} style={{ width: `${Math.min(objectiveData.progress, 100)}%` }} />
```

#### Deliverables Tab Filtering Enhancement
- **Real Data Only**: In Progress tab shows only non-completed deliverables from real API data
- **Status-Based Filtering**: Filters out deliverables with 'completed' status regardless of progress
- **No Mock Data**: Eliminates placeholder/mock deliverables that caused confusion

### Usage Guidelines

#### For Frontend Developers
1. **Always use progress-aware functions**: Use `getStatusColor()` and `getDisplayStatus()` with both status and progress parameters
2. **Prioritize completion percentage**: When progress >= 100%, always show as completed
3. **Filter completed items**: In progress views, exclude items with 'completed' status
4. **Maintain visual consistency**: Ensure all UI elements (badges, bars, colors) align with completion state

#### For Backend Developers
1. **Reliable progress calculation**: Ensure progress percentages accurately reflect actual completion
2. **Status field accuracy**: Keep status fields updated, but UI will prioritize progress when >= 100%
3. **API consistency**: Deliverable status should align with actual completion state

### Files Modified
- **`frontend/src/components/conversational/ObjectiveArtifact.tsx`**: Core progress-aware status logic
- **Progress functions**: Lines 100-140 implement the progress-first status calculation
- **Status integration**: Lines 300-301, 322-324 apply progress-aware styling
- **Deliverable filtering**: Lines 214-218 filter out completed deliverables from In Progress tab

### Benefits Achieved
- **Eliminates fake status displays**: No more "in progress" labels when objectives are 100% complete
- **User confidence**: Status information is now reliable and trustworthy
- **Visual consistency**: All UI elements reflect the true completion state
- **Developer clarity**: Clear progress-first logic that's easy to understand and maintain

## Goal-Deliverable Mapping System

### Overview
The Goal-Deliverable Mapping System ensures proper association between deliverables and their corresponding goals using **AI-driven semantic matching** instead of hard-coded logic. This system addresses critical data integrity issues where deliverables were incorrectly mapped to goal IDs, causing frontend issues like "No deliverables available yet" and confusion in the UI.

### AI Goal Matcher Service (New in 2025)
The system now uses an **AI Goal Matcher** (`backend/services/ai_goal_matcher.py`) that implements Pillar-compliant semantic matching:

#### **Key Features**
- **Semantic Content Analysis**: AI analyzes deliverable content and goal descriptions for conceptual alignment
- **Confidence Scoring**: Each match includes a confidence score (0.0-1.0) and reasoning
- **Memory-Based Learning**: Stores successful matches for pattern reuse (Workspace Memory)
- **Graceful Fallback**: Multiple fallback levels ensure deliverables always have goal associations

#### **Architecture**
```python
# AI Goal Matcher integration in database.py
from services.ai_goal_matcher import AIGoalMatcher

# Use AI for semantic matching instead of "first active goal" anti-pattern
match_result = await AIGoalMatcher.match_deliverable_to_goal(
    deliverable_content=pipeline_result.output,
    deliverable_title=deliverable_data.get("title"),
    goals=active_goals
)

if match_result.success:
    mapped_goal_id = match_result.goal_id
    logger.info(f"🎯 AI Goal Matcher: {match_result.reasoning} (confidence: {match_result.confidence:.2f})")
```

### How the System Works Correctly

#### **Proper Mapping Logic**
The system uses a multi-step approach to ensure deliverables are correctly associated with goals:

1. **Explicit Goal ID Assignment**: If the deliverable creation includes a specific `goal_id`, the system validates it exists in the workspace
2. **AI-Driven Semantic Matching**: Uses AI Goal Matcher for intelligent content-based goal association (replaces old pattern matching)
3. **Confidence-Based Selection**: Chooses the goal with highest semantic similarity confidence score
4. **Memory Pattern Reuse**: Leverages successful past matches from Workspace Memory
5. **Validation and Fallback**: Ensures every deliverable has a valid goal association with proper error handling

#### **Database Integration**
Located in `backend/database.py`, the mapping logic follows this pattern:

```python
# 🎯 FIX: Check if deliverable_data already contains a specific goal_id
if deliverable_data.get("goal_id"):
    # Validate that the provided goal_id exists in the workspace
    provided_goal_id = deliverable_data.get("goal_id")
    matching_goal = next((g for g in workspace_goals if g.get("id") == provided_goal_id), None)
    
    if matching_goal:
        mapped_goal_id = provided_goal_id
        logger.info(f"🎯 Using provided goal_id: {mapped_goal_id} for deliverable")
    else:
        logger.warning(f"⚠️ Provided goal_id {provided_goal_id} not found in workspace goals, falling back to goal matching")

# AI-Driven Semantic Matching (replaces old "first active goal" anti-pattern)
if not mapped_goal_id and workspace_goals:
    try:
        # Filter active goals for AI matching
        active_goals = [g for g in workspace_goals if g.get("status") == "active"]
        
        if active_goals:
            # Use AI Goal Matcher for semantic matching
            match_result = await AIGoalMatcher.match_deliverable_to_goal(
                deliverable_content=pipeline_result.output,
                deliverable_title=deliverable_data.get("title"),
                goals=active_goals
            )
            
            if match_result.success:
                mapped_goal_id = match_result.goal_id
                logger.info(f"🎯 AI Goal Matcher: {match_result.reasoning} (confidence: {match_result.confidence:.2f})")
    except Exception as e:
        logger.error(f"❌ AI Goal Matcher failed: {e}, using emergency fallback")
        # Emergency fallback only if AI fails
        for goal in workspace_goals:
            if goal.get("status") == "active":
                mapped_goal_id = goal.get("id")
                logger.info(f"🎯 Emergency fallback: Using first active goal")
                break
```

#### **Test Results & Validation**
**Successful Test Case**:
- **Deliverable**: "Email sequence 2" with content about case studies and social proof
- **AI Reasoning**: "The deliverable specifically focuses on writing content for an email sequence that emphasizes case studies and social proof"
- **Confidence Score**: 90%
- **Result**: Correctly mapped to appropriate marketing goal instead of "first active goal"

#### **Pillar Compliance Integration**
The AI Goal Matcher enhancement demonstrates compliance with all 15 pillars:

- **Pillar 1 (Real Tools)**: Uses official OpenAI SDK, not direct API calls
- **Pillar 6 (Memory System)**: Integrates with Workspace Memory for pattern learning
- **Pillar 10 (Explainability)**: Provides clear reasoning for all matching decisions
- **Pillar 12 (Quality Assurance)**: Confidence scoring prevents low-quality matches
- **Anti-Pattern Prevention**: Eliminates hard-coded "first active goal" logic

#### **Performance & Reliability**
- **Processing Time**: < 2 seconds for typical goal matching
- **Success Rate**: 90%+ confidence in semantic matches
- **Fallback Safety**: Multiple fallback levels ensure no deliverable goes unmapped
- **Memory Efficiency**: Patterns stored in Workspace Memory reduce future processing

#### **Files Modified in Enhancement**
- **`backend/database.py` (lines 502-506)**: Core deliverable assignment logic transformation
- **`backend/services/ai_goal_matcher.py`**: New AI semantic matching service
- **Integration tests**: Validation of AI matching accuracy and fallback behavior
- **Architecture reports**: Generated by principles-guardian and placeholder-police quality gates

### The Bug That Was Fixed

#### **Root Cause**
**File**: `backend/database.py` in deliverable creation functions  
**Bug**: The system was mapping ALL deliverables to the FIRST active goal instead of the correct goal associated with the task.

**Before (Broken Logic)**:
```python
# ❌ ALWAYS ASSIGNED TO FIRST ACTIVE GOAL
for goal in workspace_goals:
    if goal.get("status") == "active":
        mapped_goal_id = goal.get("id")  # Always took the first match
        break
```

**After (Fixed Logic)**:
Now uses proper validation, content matching, and task goal_id relationships with comprehensive fallback logic.

#### **Symptoms of the Bug**
- Frontend displayed "No deliverables available yet" despite deliverables existing
- Deliverables appeared under wrong goals in UI
- Progress calculations were incorrect
- Goal completion metrics were misleading
- Data integrity violations in deliverable-goal relationships

### Data Correction Process

#### **Files Created for Fix**
- **`backend/fix_goal_deliverable_mapping.sql`**: Corrective SQL script for existing data
- **`backend/goal_deliverable_fix_report.md`**: Detailed analysis and fix documentation

#### **Pattern-Based Content Matching**
The fix applied intelligent string matching based on deliverable titles:

```sql
-- Fix deliverables related to "Piano editoriale mensile"
UPDATE deliverables 
SET goal_id = '22f28697-e628-48a1-977d-4cf69496f486'
WHERE workspace_id = 'workspace_id'
  AND title LIKE '%Piano editoriale%';

-- Fix deliverables related to "Strategia di interazione"
UPDATE deliverables 
SET goal_id = 'd707a492-db77-4501-ad7e-cc446efd5f35'
WHERE workspace_id = 'workspace_id'
  AND title LIKE '%Strategia di interazione%';
```

### Debugging Mapping Issues

#### **Diagnostic Queries**
```sql
-- Check deliverable-goal distribution
SELECT 
    wg.description as goal_description,
    wg.id as goal_id,
    COUNT(d.id) as deliverable_count
FROM workspace_goals wg
LEFT JOIN deliverables d ON wg.id = d.goal_id 
WHERE wg.workspace_id = 'workspace_id'
GROUP BY wg.id, wg.description
ORDER BY wg.description;

-- Find orphaned deliverables
SELECT id, title, goal_id 
FROM deliverables 
WHERE workspace_id = 'workspace_id' 
  AND goal_id IS NULL;
```

#### **Backend Logging Verification**
```bash
# Check goal assignment logs
grep "Using provided goal_id" backend/logs/*.log
grep "Fallback: Using first active goal" backend/logs/*.log
grep "goal_id not found in workspace goals" backend/logs/*.log
```

#### **API Endpoints for Debugging**
```bash
# Check deliverable-goal relationships
curl -X GET "http://localhost:8000/api/deliverables/workspace/{workspace_id}" | \
  jq '.[] | {id: .id, title: .title, goal_id: .goal_id}'

# Verify goal-specific deliverables
curl -X GET "http://localhost:8000/api/deliverables?workspace_id={workspace_id}&goal_id={goal_id}"
```

#### **AI Goal Matcher Testing**
```bash
# Test AI Goal Matcher service health
python3 -c "
from services.ai_goal_matcher import AIGoalMatcher
import asyncio
print('✅ AI Goal Matcher Service: OPERATIONAL')
print('Testing semantic matching capability...')
"

# Monitor AI goal matching decisions in logs
grep "AI Goal Matcher:" backend/logs/*.log | tail -10
grep "confidence:" backend/logs/*.log | tail -5

# Check for anti-pattern fallback usage (should be rare)
grep "Emergency fallback: Using first active goal" backend/logs/*.log | wc -l
```

### Prevention Measures

#### **Code Review Checklist for Goal-Deliverable Relationships**
- [ ] ✅ Deliverable creation validates goal_id existence in workspace
- [ ] ✅ Content-based matching has fallback for failed explicit assignments
- [ ] ✅ Proper logging shows goal assignment reasoning
- [ ] ✅ Error handling for invalid or missing goal associations
- [ ] ✅ Task-goal relationships are preserved in deliverable creation

#### **Database Integrity Checks**
```sql
-- Regular validation query to run
SELECT 
    COUNT(*) as total_deliverables,
    COUNT(goal_id) as deliverables_with_goals,
    COUNT(*) - COUNT(goal_id) as orphaned_deliverables
FROM deliverables 
WHERE workspace_id = 'workspace_id';

-- Constraint validation
SELECT constraint_name, constraint_type 
FROM information_schema.table_constraints 
WHERE table_name = 'deliverables' 
  AND constraint_type = 'FOREIGN KEY';
```

### Frontend-Backend Data Consistency

#### **Verification Steps**
1. **Backend Data Check**: Ensure deliverables have correct goal_id associations
2. **Frontend API Response**: Verify API returns properly mapped deliverables  
3. **UI Display Validation**: Confirm deliverables appear under correct goals
4. **Progress Calculation**: Check that goal progress reflects correct deliverable count

#### **API Response Validation**
```typescript
// Verify deliverable-goal consistency in frontend
const validateDeliverableGoalMapping = (deliverables: Deliverable[], goals: Goal[]) => {
  const goalIds = new Set(goals.map(g => g.id))
  const orphanedDeliverables = deliverables.filter(d => d.goal_id && !goalIds.has(d.goal_id))
  
  if (orphanedDeliverables.length > 0) {
    console.error('🚨 MAPPING ERROR: Deliverables with invalid goal_id:', orphanedDeliverables)
  }
  
  return orphanedDeliverables.length === 0
}
```

## Goal Progress Transparency System

### Overview
The Goal Progress Transparency System addresses the critical "67% progress discrepancy" issue where goals showed incomplete progress despite all deliverables being completed. This system provides complete visibility into deliverable statuses and actionable unblocking mechanisms.

### Key Features
- **Progress Discrepancy Detection**: Compares reported vs calculated completion percentages
- **Complete Status Breakdown**: Shows all deliverable states (completed/failed/pending/in_progress/unknown)
- **Visibility Gap Analysis**: Identifies items hidden from UI with transparency indicators
- **Interactive Unblocking**: One-click retry/resume actions for blocked deliverables
- **Visual Status Indicators**: Clear feedback using emojis (✅❌⏳🔄❓)

### API Endpoints

#### GET `/api/goal-progress-details/{workspace_id}/{goal_id}`
```bash
# Get comprehensive goal progress analysis
curl -X GET "http://localhost:8000/api/goal-progress-details/{workspace_id}/{goal_id}?include_hidden=true"
```

**Response includes:**
- `progress_analysis`: Reported vs calculated progress comparison
- `deliverable_breakdown`: Complete status categorization
- `visibility_analysis`: Transparency gap detection
- `unblocking`: Available actions and recommendations

#### POST `/api/goal-progress-details/{workspace_id}/{goal_id}/unblock`
```bash
# Execute unblocking actions
curl -X POST "http://localhost:8000/api/goal-progress-details/{workspace_id}/{goal_id}/unblock?action=retry_failed"
```

**Available Actions:**
- `retry_failed`: Retry all failed deliverables
- `resume_pending`: Resume stuck deliverables  
- `escalate_all`: Flag for human intervention
- `retry_specific`: Target specific deliverable IDs

### Frontend Integration
The system integrates seamlessly into the `ObjectiveArtifact.tsx` component with:

- **Progress Discrepancy Alerts**: Visual warnings when reported != calculated progress
- **Transparency Gap Notices**: Information about hidden deliverables
- **Unblocking Action Panel**: Interactive buttons for issue resolution
- **Status Overview Grid**: Comprehensive deliverable state visualization
- **Real-time Updates**: WebSocket integration for live progress tracking

### TypeScript Support
Complete type safety provided through `/frontend/src/types/goal-progress.ts`:

```typescript
interface GoalProgressDetail {
  progress_analysis: ProgressAnalysis
  deliverable_breakdown: DeliverableBreakdown
  visibility_analysis: VisibilityAnalysis
  unblocking: UnblockingSummary
  // ... complete type definitions
}
```

### Configuration
Status display and action configurations centralized in:
- `DELIVERABLE_STATUS_CONFIG`: Visual styling for each status
- `UNBLOCK_ACTION_CONFIG`: Action button configurations and behaviors

### Usage Patterns

**For Developers:**
1. Use the API to diagnose progress discrepancies
2. Implement custom unblocking workflows
3. Extend status types for domain-specific needs

**For Users:**
1. View comprehensive progress breakdown in ObjectiveArtifact
2. Click unblock actions to resolve issues automatically
3. Monitor transparency gaps to understand system health

### Documentation
Complete system documentation available in:
- `/docs/GOAL_PROGRESS_TRANSPARENCY_SYSTEM.md` - Full technical documentation
- API schemas and configuration details included

## Available Tools

The conversational AI system provides access to various tools through natural language commands or slash commands (`/`). When users type `/` in the chat input, they can discover and use these tools:

### Project Management Tools
- **`show_project_status`** (📊): Get comprehensive project overview including metrics, goals, and current status
- **`show_goal_progress`** (🎯): Check progress on specific objectives and goal completion percentages  
- **`show_deliverables`** (📦): View completed deliverables, assets, and project outputs
- **`create_goal`** (🎯): Create new project goals with specific metrics and targets

### Team Management Tools  
- **`show_team_status`** (👥): See current team composition, member activities, and workload distribution
- **`add_team_member`** (➕): Add new team members with specific roles, skills, and seniority levels

### Quality & Feedback Tools
- **`approve_all_feedback`** (✅): Bulk approve all pending human feedback requests in the workspace

### System Tools
- **`fix_workspace_issues`** (🔧): Automatically diagnose and restart failed tasks, resolve common workspace issues

### Tool Access Methods
1. **Slash Commands**: Type `/` in any chat input to see available tools
2. **Natural Language**: Describe what you want (e.g., "show me the project status")
3. **Quick Actions**: Use context-specific action buttons in chat interfaces

### Usage Notes
- Tools are context-aware and adapt to the current workspace
- Most tools provide real-time data from the database
- Results are formatted for easy reading and include actionable insights
- Tools can be chained together in conversations for complex workflows

### Tool Maintenance Guidelines
When adding new tools to the system, ensure you update these locations:

1. **Backend Implementation**: Add tool logic to `backend/ai_agents/conversational_simple.py` in the `_execute_tool` method
2. **Frontend Discovery**: Update the `slashCommands` array in `frontend/src/components/conversational/ConversationInput.tsx`
3. **AI Suggestions**: Add tool to `actionable_tools` dictionary in `conversational_simple.py` `_extract_suggested_actions` method
4. **Documentation**: Update this CLAUDE.md section with tool description and usage
5. **Tool Registry**: Register in `backend/tools/registry.py` if applicable

**Critical**: Always maintain consistency between the backend tool implementation and frontend discovery interface. Test both slash command discovery and natural language invocation.

## Key Files
- `backend/main.py`: FastAPI app entry point
- `backend/ai_agents/director.py`: Team proposal generation
- `backend/executor.py`: Task execution engine
- `backend/improvement_loop.py`: Quality feedback system
- `frontend/src/app/layout.tsx`: Main app layout
- `frontend/src/components/orchestration/`: Core orchestration UI
- `frontend/src/components/conversational/ConversationInput.tsx`: Slash command implementation
- # Guiding Principles (Project Memory)
- Rileva lingua utente e rispondi coerentemente (IT/EN/…).
- Evita hard-coding; usa config/env e SDK ufficiali dove esistono (Agents SDK/OpenAI).
- Agnostico di dominio, multi-tenant/multi-lingua.
- Goal-first: collega task → goal; aggiorna progresso.
- Workspace Memory: salva success_pattern, failure_lesson e riusali.
- Pipeline autonoma: Task → Goal → Enhancement → Memory → Correction.
- QA AI-first con HiTL solo su deliverable critici.
- UI/UX minimale (Claude/ChatGPT style).
- Codice production-ready & testato; niente placeholder/mock.
- Deliverable concreti; niente lorem ipsum: sostituisci con dati reali.
- Course-correction automatico da gap detection.
- Explainability: mostra reasoning steps e alternative quando richiesto.
- Tool/Service-layer modulare; registry unico di tool.
- Conversazione context-aware via endpoints conversazionali / Agents SDK.

## 🤖 Claude Code Sub-Agents Configuration

### Available Sub-Agents (6 configured)
Located in `.claude/agents/`:

#### **Quality Gates & Architecture**
- **director** (opus): Orchestrator that triggers other agents as quality gates
- **system-architect** (opus): Architectural decisions, component reuse, anti-silo patterns
- **principles-guardian** (opus): 15 Pillars compliance enforcement, blocks critical violations

#### **Specialized Guardians**
- **db-steward** (sonnet): Database schema guardian, prevents duplicates, ensures migrations safety
- **placeholder-police** (sonnet): Detects hard-coded values, placeholders, TODOs, incomplete implementations

#### **Frontend & Documentation**
- **frontend-ux-specialist** (sonnet): **MINIMAL UI/UX** specialist following **ChatGPT/Claude design patterns**
  - **Design Philosophy**: Clean, uncluttered interfaces without visual bloat
  - **Anti-patterns**: ❌ Excessive colors, gradients, animations, complex hierarchies
  - **Success Metrics**: Professional minimal appearance, fast interactions, intuitive flows
- **docs-scribe** (sonnet): Documentation synchronization and consistency

### Design Philosophy for frontend-ux-specialist
**MINIMAL IS BETTER** - Follow ChatGPT/Claude principles:
- Clean typography without decorations
- Subtle color schemes (grays, whites, minimal accent colors)  
- No unnecessary animations or visual effects
- Focus on content and functionality over aesthetics
- Plenty of whitespace and breathing room
- Simple, intuitive interactions
- Clear hierarchy without visual clutter

### Auto-Activation Triggers
Sub-agents automatically activate on:
- **director**: Changes to `backend/ai_agents/`, `backend/services/`, `backend/routes/`, `src/components/`, `src/hooks/`
- **frontend-ux-specialist**: Frontend component changes, UI modifications, styling updates
- **docs-scribe**: Changes to `CLAUDE.md`, `README.md`, `backend/main.py`, documentation files

### Usage
- **Manual**: Use Task tool with specific agent: `/task director Review these changes`
- **Automatic**: Agents should trigger on matching file patterns (investigation needed for activation issues)

## 🎯 Claude Code Director Automation

**Auto-invoke Director on Critical Changes**:
- **Trigger**: When editing files in `backend/ai_agents/`, `backend/services/`, `backend/routes/`, `frontend/src/components/`, `migrations/`, `models.py`
- **Action**: Automatically invoke Director agent using the Task tool
- **Sequence**: director → architecture-guardian → sdk-guardian → db-steward → api-contract-guardian → principles-guardian → placeholder-police → fallback-test-sentinel → docs-scribe
- **Blocking**: If any quality gate fails, prevent commit/deployment until resolved

**Usage**: "Please invoke the Director to review these changes" triggers the full quality gate sequence.

**Pre-commit Hook**: Git hook configured in `.git/hooks/pre-commit` automatically detects critical file changes and invokes Director quality gates.