# CLAUDE Detailed Configuration Reference

This file contains the complete environment configuration reference extracted from the main CLAUDE.md for performance optimization.

## Complete Environment Setup

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

### AI-Driven Content Display System
- `OPENAI_API_KEY=sk-...` - Required for AI transformations
- `AI_TRANSFORMATION_TIMEOUT=30` - Max processing time
- `FALLBACK_CONFIDENCE_THRESHOLD=60` - When to prefer fallback
- `DISPLAY_CONTENT_CACHE_TTL=3600` - Cache duration in seconds

### Performance Optimization
- `PROGRESSIVE_LOADING_ENABLED=true` - Enable progressive loading architecture
- `PHASE_DELAY_MS=50` - Delay between essential and enhancement phases
- `ENABLE_CIRCULAR_DEPENDENCY_DETECTION=true` - Enable circular dependency warnings in development
- `SWITCHING_CHAT_DELAY_MS=100` - Delay to prevent rapid chat switching loops

### Database Configuration
- `AUTO_MIGRATE_ON_STARTUP=false` - Automatically run migrations on application startup
- `MIGRATION_BACKUP_ENABLED=true` - Create automatic backups before migrations
- `ENABLE_AI_GOAL_MATCHING=true` - Enable AI-driven goal-deliverable matching
- `AI_MATCHING_CONFIDENCE_THRESHOLD=0.7` - Minimum confidence score for AI goal matching

### Security Configuration
- `RATE_LIMITING_ENABLED=true` - Enable API rate limiting protection
- `SECURITY_AUDIT_LOGGING=true` - Enable detailed security event logging
- `CLAUDE_CODE_AUTO_DIRECTOR=true` - Automatically invoke Director on critical changes
- `QUALITY_GATE_BLOCKING=true` - Block operations when quality gates fail

## Security Checklist for New Features

Before deploying any new auto-completion or goal management feature:

- [ ] ✅ Human feedback tasks are flagged for manual review (never auto-approved)
- [ ] ✅ All database access uses SDK-compliant functions
- [ ] ✅ Rate limiting is implemented with appropriate limits
- [ ] ✅ Configuration values are externalized via environment variables
- [ ] ✅ Security logging is implemented with clear indicators
- [ ] ✅ Error handling doesn't expose sensitive information
- [ ] ✅ Documentation is updated with security considerations

## Performance Configuration

### Critical Performance Settings
- **Progressive Loading**: Ensures UI renders in <200ms
- **Circular Dependency Detection**: Prevents infinite React loops
- **WebSocket Timeouts**: Balanced for reliability vs responsiveness
- **Rate Limiting**: Protects against resource exhaustion
- **Caching**: Optimizes repeated operations

### Monitoring Configuration
All performance-critical settings include monitoring and alerting capabilities to track system health and automatically adjust under load.

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

## Available Tools

The conversational AI system provides access to various tools through natural language commands or slash commands (`/`):

### Project Management Tools
- **`show_project_status`** (📊): Get comprehensive project overview
- **`show_goal_progress`** (🎯): Check progress on specific objectives
- **`show_deliverables`** (📦): View completed deliverables and assets
- **`create_goal`** (🎯): Create new project goals

### Team Management Tools  
- **`show_team_status`** (👥): See current team composition and activities
- **`add_team_member`** (➕): Add new team members with roles and skills

### Quality & Feedback Tools
- **`approve_all_feedback`** (✅): Bulk approve pending human feedback requests

### System Tools
- **`fix_workspace_issues`** (🔧): Automatically diagnose and restart failed tasks

### Tool Access Methods
1. **Slash Commands**: Type `/` in any chat input to see available tools
2. **Natural Language**: Describe what you want (e.g., "show me the project status")
3. **Quick Actions**: Use context-specific action buttons in chat interfaces