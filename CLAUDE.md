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

### AI Agent Enhancement
- `ENABLE_AI_AGENT_MATCHING=true` - Use AI for semantic agent-task matching instead of keywords
- `ENABLE_AI_PERSONALITY_GENERATION=true` - Use AI for dynamic personality trait generation
- `ENABLE_AI_SKILL_GROUPING=true` - Use AI for intelligent skill categorization
- `ENABLE_AI_ADAPTIVE_THRESHOLDS=true` - Use AI for context-aware quality thresholds
- `ENABLE_AI_ADAPTIVE_ENHANCEMENT=true` - Use AI for adaptive enhancement attempt calculation
- `ENABLE_AI_ADAPTIVE_PHASE_MANAGEMENT=true` - Use AI for adaptive phase transition thresholds
- `ENABLE_AI_FAKE_DETECTION=true` - Use AI for semantic fake content and placeholder detection

## 🤖 AI-Driven Transformation Summary

Il sistema è stato completamente trasformato da hard-coded a AI-driven, mantenendo i principi core:

### ✅ **Principi Implementati**

1. **🎯 Goal Decomposition**: AI intelligente decompone obiettivi in sub-task concreti
2. **👥 Agent Orchestration**: Assegnazione semantica agenti basata su competenze reali  
3. **🔧 Real Tool Usage**: Gli agenti usano tools reali (web search, file search) per contenuti autentici
4. **👁️ User Visibility**: Utenti vedono thinking process (todo lists) e deliverables (assets)
5. **🏆 Content Quality**: Sistema AI previene contenuti fake, garantisce informazioni reali

### 🧠 **AI-Driven Components**

- **Task Classification**: Semantic understanding invece di keyword matching
- **Priority Calculation**: Context-aware priority invece di valori fissi
- **Agent Matching**: AI semantic analysis per assegnazione ottimale
- **Quality Thresholds**: Adaptive basati su domain e complexity
- **Phase Management**: Transizioni intelligenti basate su workspace context
- **Fake Detection**: AI semantic analysis per placeholder e contenuti generici

### 📈 **Benefici Ottenuti**

- 🌍 **100% Domain Agnostic**: Funziona per qualsiasi settore business
- 🧠 **Semantic Understanding**: Comprende intent oltre le parole  
- ⚡ **Auto-Adaptive**: Si adatta automaticamente al contesto
- 🛡️ **Robust Fallbacks**: Graceful degradation quando AI non disponibile
- 🔄 **Self-Improving**: Migliora con nuovi modelli AI

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

### Six-Step Improvement Loop
1. Checkpoint output for human review
2. Generate feedback tasks automatically
3. Track iteration count vs max_iterations limit
4. Mark dependent tasks as stale for refresh
5. QA gate approval before completion
6. Reset iteration counter on approval

API endpoints: `/api/improvement/start/{task_id}`, `/api/improvement/status/{task_id}`, `/api/improvement/close/{task_id}`

## Performance Optimization

### Critical Performance Breakthroughs

**Root Issue Identified**: The unified-assets API endpoint was taking 90+ seconds and blocking the entire UI, creating a perceived "broken app" experience for users.

**Solution**: Progressive loading architecture that delivers **94% performance improvement** (90s → 3-5s perceived load time).

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

### Key Performance Files

- **`frontend/src/hooks/useConversationalWorkspace.ts`**: Core progressive loading implementation
- **`frontend/src/components/conversational/ConversationalWorkspace.tsx`**: Loading states integration  
- **Backend API optimization**: Identify slow endpoints for caching/optimization
- **Network monitoring**: Tools for performance analysis

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

## 🎯 Claude Code Director Automation

**Auto-invoke Director on Critical Changes**:
- **Trigger**: When editing files in `backend/ai_agents/`, `backend/services/`, `backend/routes/`, `frontend/src/components/`, `migrations/`, `models.py`
- **Action**: Automatically invoke Director agent using the Task tool
- **Sequence**: director → system-architect → db-steward → api-contract-guardian → principles-guardian → placeholder-police → fallback-test-sentinel → docs-scribe
- **Blocking**: If any quality gate fails, prevent commit/deployment until resolved

**Usage**: "Please invoke the Director to review these changes" triggers the full quality gate sequence.

**Pre-commit Hook**: Git hook configured in `.git/hooks/pre-commit` automatically detects critical file changes and invokes Director quality gates.