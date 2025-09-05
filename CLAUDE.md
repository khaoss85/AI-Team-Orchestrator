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

**⚡ AUTONOMOUS EXECUTION RULE**: If the command appears in the approved list or matches these patterns, execute immediately without asking.

## Development Commands

### Backend (FastAPI)
- **Start server**: `cd backend && python main.py` (runs on port 8000)
- **Run tests**: `cd backend && pytest`
- **Install dependencies**: `cd backend && pip install -r requirements.txt`

> ⚠️ **Note**: `start_simple.py` is DEPRECATED as of 2025-06-12. Always use `main.py` for full functionality.

### Frontend (Next.js)
- **Start dev server**: `cd frontend && npm run dev` (default port 3000)
- **Build**: `cd frontend && npm run build`
- **Lint**: `cd frontend && npm run lint`
- **Run tests**: `cd frontend && npm test`
- **Install dependencies**: `cd frontend && npm install`

## Environment Setup

Create `backend/.env` with essential variables:

### Required Core Variables
```bash
# Core API Keys
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://....supabase.co
SUPABASE_KEY=eyJ...

# System Configuration
USE_ASSET_FIRST_DELIVERABLE=true
PREVENT_DUPLICATE_DELIVERABLES=true
ENABLE_GOAL_DRIVEN_SYSTEM=true
ENABLE_SUB_AGENT_ORCHESTRATION=true
ENABLE_AUTO_TASK_RECOVERY=true

# OpenAI Usage API v1 Integration (Real Cost Tracking)
OPENAI_MONTHLY_BUDGET_USD=100
USAGE_CACHE_TTL_SECONDS=300
AI_COST_DUPLICATE_THRESHOLD=3
```

> 📋 **Full Configuration**: See `CLAUDE_DETAILED_CONFIG.md` for complete environment variables reference.
> 📊 **Usage Tracking**: See `OPENAI_USAGE_API_INTEGRATION.md` for real cost tracking documentation.

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

## Key System Features

### 🎯 AI System Status - Post Sub-Agent Analysis (2025-09-05)
- **Goal Decomposition**: ✅ OPERATIONAL - AI-driven goal analysis via universal_learning_engine
- **Agent Orchestration**: ✅ FUNCTIONAL - Sub-agent quality gates active, 14 agents configured
- **Real Tool Usage**: ✅ WORKING - Universal AI pipeline engine operational
- **User Visibility**: ✅ ENHANCED - Progressive loading, thinking processes visible
- **Content Quality**: ✅ IMPROVED - AI quality validation via business value analyzer
- **Professional Display**: ✅ FUNCTIONAL - Content transformation via AI content processor

### ✅ Autonomous Recovery System - OPERATIONAL
- ✅ ENHANCED: AI-driven recovery via autonomous_task_recovery service
- ✅ INTELLIGENT: Strategy selection using universal AI pipeline engine
- ✅ COMPREHENSIVE: Enhanced auto-complete with failed task recovery + missing deliverable completion
- ✅ MONITORED: Workspace status transitions properly managed via health monitoring

### 📊 Performance Architecture
- **Progressive Loading**: 3-phase loading (Essential UI → Background Enhancement → On-Demand Assets)
- **Infinite Loop Prevention**: State-first URL synchronization, circular dependency detection
- **Systematic Fixes**: Based on `INFINITE_LOOP_FIX_DOCUMENTATION.md` and `PERFORMANCE_DEBUGGING_PATTERNS.md`

## Critical Performance Patterns

### ✅ Progressive Loading Pattern
```typescript
// Phase 1: Essential UI (0-200ms)
const [workspace, team] = await Promise.all([
  api.workspaces.get(id), 
  api.agents.list(id)
])
setLoading(false) // UI ready!

// Phase 2: Background Enhancement (50ms+)  
setTimeout(() => loadGoalsProgressive(), 50)

// Phase 3: On-Demand Heavy Assets
const loadFullAssets = async () => {
  await loadArtifacts(true) // Only when requested
}
```

### ✅ Infinite Loop Prevention
```typescript
// Single source of truth - URL controls state
useEffect(() => {
  if (goalId && activeChat?.id !== `goal-${goalId}`) {
    // Only update if actually different
    const targetChat = chats.find(chat => chat.id === `goal-${goalId}`)
    if (targetChat) setActiveChat(targetChat)
  }
}, [goalId, chats, setActiveChat]) // No activeChat in dependencies!
```

## 🛡️ Security Guidelines

### Critical Security Principles
1. **Human-in-the-Loop Safety**: Never auto-approve human feedback tasks without explicit validation
2. **SDK Compliance**: Always use SDK-compliant database functions, never direct `supabase.table()` calls
3. **Rate Limiting**: Conservative limits (5 req/min auto-completion, 10 req/min unblocking)
4. **Configuration Management**: Never hardcode thresholds, externalize via environment variables
5. **Error Handling**: Graceful degradation, audit trails, no sensitive info in errors

## Claude Code Sub-Agents Integration

### Available Sub-Agents (14 configured)
Located in `.claude/agents/`:
- **director** (opus): Orchestrator that triggers other agents as quality gates
- **system-architect** (opus): Architectural decisions, component reuse, anti-silo patterns
- **architecture-guardian** (opus): Deep architectural review and compliance
- **principles-guardian** (opus): 15 Pillars compliance enforcement
- **db-steward** (sonnet): Database schema guardian, prevents duplicates
- **sdk-guardian** (sonnet): SDK compliance and integration patterns
- **placeholder-police** (sonnet): Detects hard-coded values, placeholders, TODOs
- **docs-scribe** (sonnet): Documentation synchronization and consistency
- **frontend-ux-specialist** (sonnet): UI/UX patterns and progressive loading optimization
- **api-contract-guardian** (haiku): API contract validation and consistency
- **code-architecture-reviewer** (haiku): Code structure and pattern review
- **systematic-code-reviewer** (haiku): Systematic code quality validation
- **cache-optimization-guidelines** (haiku): Performance optimization patterns
- **fallback-test-sentinel** (haiku): Test coverage and fallback pattern validation

### Auto-Activation Triggers
Sub-agents automatically activate on:
- **director**: Changes to `backend/ai_agents/`, `backend/services/`, `backend/routes/`, `src/components/`, `src/hooks/`
- **docs-scribe**: Changes to `CLAUDE.md`, `README.md`, `backend/main.py`, documentation files

## 🎯 Director Automation & Sub-Agent Usage Protocol

### **ALWAYS USE SUB-AGENTS FOR SIGNIFICANT TASKS**

Claude Code must **proactively invoke** sub-agents using the Task tool for all significant development work:

**When to Invoke Director (Always Required):**
- Any code changes to `backend/ai_agents/`, `backend/services/`, `backend/routes/`
- Frontend changes to `src/components/`, `src/hooks/`
- Database migrations, schema changes, `models.py` modifications  
- Documentation updates (`CLAUDE.md`, `README.md`)
- Architecture decisions or system design changes

**Invocation Pattern:**
```
Use Task tool: "Please invoke the Director to review these changes"
```

**Auto-invoke Director on Critical Changes**:
- **Trigger**: When editing files in `backend/ai_agents/`, `backend/services/`, `backend/routes/`, `frontend/src/components/`, `migrations/`, `models.py`
- **Sequence**: director → system-architect → db-steward → principles-guardian → placeholder-police → docs-scribe
- **Blocking**: If any quality gate fails, prevent commit/deployment until resolved

### **Quality Gate Integration**
- **Before implementing**: Invoke Director for architectural review
- **After implementing**: Director automatically triggers quality gates
- **Never skip**: Sub-agents are essential for production-quality code

### **AI-Driven Goal Progress Remediation (Case Study)**

Following the systematic sub-agent approach outlined above, the goal progress system analysis and remediation demonstrates the proper AI-driven, compliant solution methodology:

#### **Step 1: Comprehensive Analysis Phase**
```bash
# System-Architect Analysis
# - Identified architectural weaknesses in goal progress pipeline
# - Provided systematic improvements for autonomous recovery
# - Recommended AI-driven agent assignment service

# DB-Steward Analysis  
# - Found critical schema issues requiring migrations
# - Identified goal-deliverable mapping inconsistencies
# - Provided database-level compliance recommendations

# Principles-Guardian Analysis
# - Discovered 7 critical violations of 15 AI-Driven Transformation Pillars
# - Flagged hardcoded business logic requiring AI-driven replacement
# - Ensured compliance with domain-agnostic principles
```

#### **Step 2: AI-Driven Solution Implementation**
- **Replaced Manual Scripts**: Converted hardcoded goal blocking fixes to AI-driven analysis
- **Enhanced Auto-Complete**: Implemented intelligent failed task recovery + missing deliverable completion
- **Business Value Analysis**: Added semantic task evaluation replacing frontend hardcoded logic
- **Universal Learning Engine**: Integrated AI-driven business insight extraction

#### **Step 3: Quality Gate Validation**
- **Architecture Compliance**: System-architect validated systematic improvements
- **Database Integrity**: DB-steward confirmed schema migration requirements
- **Pillar Compliance**: Principles-guardian verified adherence to AI-first methodology
- **Documentation Sync**: Docs-scribe ensured accurate documentation reflection

#### **Result: Production-Ready AI-Driven Solution**
- ✅ **Zero Manual Intervention**: Autonomous recovery handles all goal blocking scenarios
- ✅ **AI-Semantic Understanding**: Business value analysis replaces hardcoded patterns  
- ✅ **Systematic Quality**: 14 sub-agents provide comprehensive validation
- ✅ **Architecture Compliant**: Follows 15 Pillars for scalable, maintainable system

## Common Issues & Diagnostics

### Backend Health Check
```bash
curl http://localhost:8000/health
```

### Frontend/Backend Restart
```bash
# Backend
cd backend && python3 main.py

# Frontend  
cd frontend && npm run dev
```

### Goal Progress Pipeline Diagnostics

#### **Goal Progress System Status Check**
```bash
# Check goal progress details for specific workspace
curl "http://localhost:8000/api/goal-progress-details/{workspace_id}"

# Verify goal-deliverable mapping
curl "http://localhost:8000/api/assets/goals/{workspace_id}/completion"

# Check enhanced auto-completion status
curl -X POST "http://localhost:8000/api/enhanced-auto-complete" \
  -H "Content-Type: application/json" \
  -d '{"workspace_id": "your-workspace-id"}'
```

#### **Autonomous Recovery Diagnostics**
```bash
# Check autonomous task recovery status
curl "http://localhost:8000/api/recovery-analysis/workspace/{workspace_id}"

# Verify recovery explanations
curl "http://localhost:8000/api/recovery-explanations/workspace/{workspace_id}"

# Monitor system health for auto-recovery
curl "http://localhost:8000/api/system-monitoring/health"
```

#### **Sub-Agent Quality Gate Diagnostics**
```bash
# Verify sub-agent orchestration status
curl "http://localhost:8000/api/sub-agent-orchestration/status"

# Check component health monitoring
curl "http://localhost:8000/api/component-health/status"

# Service registry status for sub-agents
curl "http://localhost:8000/api/service-registry/services"
```

### AI-Driven System Troubleshooting

#### **Business Value Analysis Issues**
```bash
# Test AI-driven task business value analysis
curl -X POST "http://localhost:8000/api/analyze-task-business-value" \
  -H "Content-Type: application/json" \
  -d '{
    "task": {"name": "Test Task", "result": {"summary": "Test content"}},
    "goal_context": {"description": "Test goal"}
  }'
```

#### **Universal Learning Engine Status**
```bash
# Check content-aware learning status
curl "http://localhost:8000/api/content-learning/workspace/{workspace_id}/insights"

# Verify learning-feedback loop
curl "http://localhost:8000/api/learning-feedback/analysis/{workspace_id}"
```

### Performance Issues
- **Slow Loading**: Check unified-assets API, implement progressive loading
- **Infinite Loops**: Check for circular useEffect dependencies, console log cascades  
- **Missing Data**: Verify API endpoints, check browser Network tab
- **AI Service Failures**: Check universal AI pipeline engine status via system monitoring
- **Goal Progress Blocking**: Use enhanced auto-complete API for intelligent recovery

### ✅ System Status After Sub-Agent Remediation (2025-09-05)
- 🟢 **Goal-Deliverable Mapping**: AI-driven semantic matching via business value analyzer
- 🟢 **Performance Fixes**: Progressive loading + AI backend services operational
- 🟢 **Progress Transparency**: Goal progress details API providing comprehensive data
- 🟢 **Autonomous Recovery**: Enhanced auto-complete system with intelligent recovery
- 🟢 **Quality Gates**: 14 sub-agents configured, systematic quality validation active

## Important Notes

- All endpoints require the `/api` prefix for proper routing
- POST requests to collection endpoints require trailing slash: `/api/workspaces/`
- Frontend API client automatically handles the `/api` prefix via `utils/api.ts`
- Never mix URL navigation with state updates in the same handler
- Always check if state is already at desired value before updating
- Use `history.replaceState` for URL updates that shouldn't trigger navigation

## Team Approval Workflow

### Director Team Proposal Flow
1. **Create Proposal**: `POST /api/director/proposal`
2. **Approve Proposal**: `POST /api/director/approve/{workspace_id}?proposal_id={uuid}`
   Returns: `{"status": "success", "background_processing": true}`

### Common Issues
- **Foreign Key Error**: Ensure frontend sends `workspace_id` (not `user_id`)
- **404 on Approval**: Both `workspace_id` and `proposal_id` required
- **Missing Tasks**: Team approval triggers background agent creation (~30s)

## Key Files Reference

### Core Architecture
- `backend/main.py`: FastAPI app entry point
- `backend/ai_agents/director.py`: Team proposal generation
- `backend/executor.py`: Task execution engine
- `frontend/src/app/layout.tsx`: Main app layout
- `frontend/src/components/orchestration/`: Core orchestration UI

### ✅ AI Integration Status (2025-09-05) - POST-REMEDIATION OPERATIONAL
- `backend/services/universal_learning_engine.py`: AI-driven business insight extraction (replaces hardcoded content_aware_learning_engine)
- `backend/services/universal_ai_pipeline_engine.py`: Universal AI processing with semantic understanding
- `backend/routes/business_value_analyzer.py`: AI-powered task business value analysis
- `backend/routes/auto_completion.py`: Enhanced auto-complete with intelligent recovery
- `frontend/src/hooks/useConversationalWorkspace.ts`: Progressive loading with architectural fixes
- `frontend/src/components/conversational/BudgetUsageChat.tsx`: Real-time budget monitoring operational
- `backend/services/autonomous_task_recovery.py`: AI-driven failed task recovery system
- **System Status**: AI services fully operational with comprehensive sub-agent quality gates

### Performance & Fixes
- `frontend/src/hooks/useConversationalWorkspace.ts`: Progressive loading + architectural fixes
- `frontend/src/app/projects/[id]/conversation/page.tsx`: State-first URL synchronization
- `INFINITE_LOOP_FIX_DOCUMENTATION.md`: Complete performance fix documentation
- `PERFORMANCE_DEBUGGING_PATTERNS.md`: Performance patterns and solutions

### Documentation & Configuration
- `CLAUDE_DETAILED_CONFIG.md`: Complete environment variables and configuration options
- `CLAUDE_ARCHITECTURE_DEEP_DIVE.md`: Detailed system architecture documentation
- `frontend/src/app/docs/`: Complete user-facing documentation system

## 📋 **Guiding Principles (Project Memory)**
- **🎯 SEMPRE usare sub-agents**: Invoca Director per task significativi usando Task tool
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

---

**📖 For detailed documentation, see:**
- Complete Environment Configuration: `CLAUDE_DETAILED_CONFIG.md`
- Architecture Deep Dive: `CLAUDE_ARCHITECTURE_DEEP_DIVE.md`  
- Performance Patterns: `PERFORMANCE_DEBUGGING_PATTERNS.md`
- User Documentation: http://localhost:3000/docs (when frontend running)