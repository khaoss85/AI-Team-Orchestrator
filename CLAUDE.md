# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

API endpoints: `/improvement/start/{task_id}`, `/improvement/status/{task_id}`, `/improvement/close/{task_id}`

### Frontend Structure
- **App Router**: Next.js 15 with TypeScript
- **Key Pages**: Projects, teams, tools, human feedback
- **Components**: Organized by feature (orchestration/, improvement/, redesign/)
- **Hooks**: Custom hooks for asset management, orchestration, project deliverables

### Agent SDK Integration
- Uses OpenAI Agents SDK with fallback to openai_agents
- Graceful degradation when SDK unavailable
- Tools-within-tools paradigm for complex operations

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