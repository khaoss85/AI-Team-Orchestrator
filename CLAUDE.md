# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Backend (FastAPI)
- **Start server**: `cd backend && python main.py` (runs on port 8000)
- **Run tests**: `cd backend && pytest`
- **Install dependencies**: `cd backend && pip install -r requirements.txt`

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
- `DELIVERABLE_READINESS_THRESHOLD=50` - Minimum completion % for deliverable creation
- `MIN_COMPLETED_TASKS_FOR_DELIVERABLE=1` - Minimum completed tasks before deliverable
- `DELIVERABLE_CHECK_COOLDOWN_SECONDS=30` - Cooldown between deliverable checks

### Task & Phase Management
- `PHASE_PLANNING_COOLDOWN_MINUTES=5` - Cooldown between phase planning tasks
- `MAX_PENDING_TASKS_FOR_TRANSITION=8` - Max pending tasks for phase transition
- `ENABLE_ENHANCED_PHASE_TRACKING=true` - Enable advanced phase management
- `FINALIZATION_TASK_PRIORITY_BOOST=1000` - Priority boost for finalization tasks

### Quality Assurance
- `ENABLE_AI_QUALITY_ASSURANCE=true` - Enable AI-driven quality enhancement
- `ENABLE_DYNAMIC_AI_ANALYSIS=true` - Enable dynamic AI analysis features
- `ENABLE_AUTO_PROJECT_COMPLETION=true` - Enable automatic project completion

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

## Key Files
- `backend/main.py`: FastAPI app entry point
- `backend/ai_agents/director.py`: Team proposal generation
- `backend/executor.py`: Task execution engine
- `backend/improvement_loop.py`: Quality feedback system
- `frontend/src/app/layout.tsx`: Main app layout
- `frontend/src/components/orchestration/`: Core orchestration UI