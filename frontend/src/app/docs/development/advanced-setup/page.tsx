'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { 
  ArrowLeft, 
  Settings,
  Database,
  Shield,
  Zap,
  Code,
  Copy,
  CheckCircle,
  AlertTriangle,
  Terminal,
  GitBranch,
  Cpu,
  Lock,
  Globe
} from 'lucide-react'

const setupCategories = [
  {
    id: 'performance-optimization',
    title: 'Performance Optimization',
    icon: Zap,
    color: 'bg-yellow-50 border-yellow-200',
    description: 'Advanced performance configurations and monitoring setup',
    guides: [
      {
        title: 'Progressive Loading Architecture',
        description: 'Implement the 3-phase loading pattern for optimal user experience',
        complexity: 'intermediate',
        estimatedTime: '30-45 minutes',
        prerequisites: ['Basic React knowledge', 'Understanding of API patterns'],
        sections: [
          {
            title: 'Phase 1: Essential UI Setup',
            content: 'Configure essential data loading for immediate UI render',
            code: `// hooks/useProgressiveWorkspace.ts
export const useProgressiveWorkspace = (workspaceId: string) => {
  const [loading, setLoading] = useState(true)
  const [goalsLoading, setGoalsLoading] = useState(false)
  const [assetsLoading, setAssetsLoading] = useState(false)
  
  // Phase 1: Essential UI (0-200ms)
  useEffect(() => {
    const loadEssentialData = async () => {
      try {
        const [workspace, team] = await Promise.all([
          api.workspaces.get(workspaceId),
          api.agents.list(workspaceId)
        ])
        
        setWorkspaceContext({ workspace, team })
        setLoading(false) // UI ready!
        
        // Phase 2: Enhancement in background (50ms+)
        setTimeout(() => loadGoalsProgressive(), 50)
      } catch (error) {
        console.error('Essential data load failed:', error)
        setLoading(false) // Still show UI with fallbacks
      }
    }
    
    loadEssentialData()
  }, [workspaceId])
  
  return { loading, goalsLoading, assetsLoading, loadFullAssets }
}`
          },
          {
            title: 'Phase 2: Background Enhancement',
            content: 'Load goals and dynamic content without blocking UI',
            code: `const loadGoalsProgressive = async () => {
  setGoalsLoading(true)
  try {
    const goals = await api.workspaceGoals.getAll(workspaceId).catch(error => {
      setGoalsError(\`Failed to load goals: \${error.message}\`)
      return [] // Graceful fallback
    })
    
    // Generate dynamic chats from goals
    const dynamicChats = goals.map(goal => ({
      id: \`goal-\${goal.id}\`,
      name: goal.description,
      type: 'goal-based',
      goalId: goal.id
    }))
    
    setChats(prevChats => [...prevChats, ...dynamicChats])
  } catch (error) {
    console.error('Goals enhancement failed:', error)
  } finally {
    setGoalsLoading(false)
  }
}`
          },
          {
            title: 'Phase 3: On-Demand Heavy Assets',
            content: 'Load assets only when explicitly requested by user',
            code: `const loadFullAssets = async () => {
  setAssetsLoading(true)
  try {
    // Only call heavy unified-assets API when needed
    const response = await api.unifiedAssets.getWorkspace(workspaceId, {
      includeContent: true,
      includeMetrics: true
    })
    
    setArtifacts(prevArtifacts => ({
      ...prevArtifacts,
      fullAssets: response.data
    }))
  } catch (error) {
    console.error('Assets loading failed:', error)
    // Don't break the app - assets are enhancement only
  } finally {
    setAssetsLoading(false)
  }
}`
          }
        ],
        configOptions: [
          {
            key: 'PROGRESSIVE_LOADING_ENABLED',
            type: 'boolean',
            default: 'true',
            description: 'Enable progressive loading architecture'
          },
          {
            key: 'PHASE_DELAY_MS',
            type: 'integer',
            default: '50',
            description: 'Delay between essential and enhancement phases'
          }
        ]
      },
      {
        title: 'Infinite Loop Prevention System',
        description: 'Implement systematic protection against React infinite loops',
        complexity: 'advanced',
        estimatedTime: '60-90 minutes',
        prerequisites: ['React Hooks expertise', 'Understanding of circular dependencies'],
        sections: [
          {
            title: 'Circular Dependency Detection',
            content: 'Identify and break circular dependencies between useEffect hooks',
            code: `// Anti-pattern detection helper
const useCircularDependencyWarning = (dependencies: any[], hookName: string) => {
  const prevDeps = useRef<any[]>([])
  const renderCount = useRef(0)
  
  useEffect(() => {
    renderCount.current += 1
    
    if (renderCount.current > 10) {
      console.warn(\`🚨 Potential circular dependency in \${hookName}\`, {
        currentDeps: dependencies,
        previousDeps: prevDeps.current,
        renderCount: renderCount.current
      })
    }
    
    prevDeps.current = dependencies
  }, dependencies)
}`
          },
          {
            title: 'State-First URL Synchronization',
            content: 'Implement unidirectional URL-to-state flow to prevent loops',
            code: `// FIXED: Single source of truth pattern
const useURLStateSyncing = (goalId: string) => {
  const [switchingChat, setSwitchingChat] = useState(false)
  
  // URL controls state (unidirectional)
  useEffect(() => {
    if (goalId && chats.length > 0 && !switchingChat) {
      const targetChatId = \`goal-\${goalId}\`
      
      // CRITICAL: Only update if actually different
      if (activeChat?.id !== targetChatId) {
        const targetChat = chats.find(chat => chat.id === targetChatId)
        if (targetChat) {
          setSwitchingChat(true)
          setActiveChat(targetChat)
          
          // Prevent immediate re-triggers
          setTimeout(() => setSwitchingChat(false), 100)
        }
      }
    }
  }, [goalId, chats, setActiveChat]) // No activeChat in dependencies!
  
  return { switchingChat }
}`
          }
        ],
        configOptions: [
          {
            key: 'ENABLE_CIRCULAR_DEPENDENCY_DETECTION',
            type: 'boolean',
            default: 'true',
            description: 'Enable circular dependency warnings in development'
          },
          {
            key: 'SWITCHING_CHAT_DELAY_MS',
            type: 'integer',
            default: '100',
            description: 'Delay to prevent rapid chat switching loops'
          }
        ]
      }
    ]
  },
  {
    id: 'database-advanced',
    title: 'Advanced Database Configuration',
    icon: Database,
    color: 'bg-blue-50 border-blue-200',
    description: 'Complex database setup, migrations, and optimization',
    guides: [
      {
        title: 'Migration Management System',
        description: 'Set up automated migration execution and rollback procedures',
        complexity: 'advanced',
        estimatedTime: '45-60 minutes',
        prerequisites: ['PostgreSQL knowledge', 'Database administration experience'],
        sections: [
          {
            title: 'Migration Execution Order',
            content: 'Follow the documented execution order for database migrations',
            code: `-- Migration execution script (execute_migrations.sql)
-- CRITICAL: Execute in this exact order

-- 001: Base schema
\\i 001_initial_schema.sql

-- 012: AI-driven enhancements  
\\i 012_add_dual_format_display_fields.sql

-- 018: OpenAI Assistants support
\\i 018_add_openai_assistants_support.sql

-- Verify each migration
SELECT 
  schemaname, 
  tablename, 
  hasindexes 
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY tablename;`
          },
          {
            title: 'Data Integrity Monitoring',
            content: 'Set up automated data integrity checks',
            code: `-- integrity_check.sql
-- Check for orphaned deliverables
SELECT 
  'Orphaned Deliverables' as issue_type,
  COUNT(*) as count
FROM deliverables d 
LEFT JOIN workspace_goals wg ON d.goal_id = wg.id 
WHERE d.goal_id IS NOT NULL AND wg.id IS NULL;

-- Check foreign key constraints
SELECT 
  conname as constraint_name,
  conrelid::regclass as table_name,
  confrelid::regclass as referenced_table
FROM pg_constraint 
WHERE contype = 'f' 
  AND conrelid::regclass::text LIKE '%deliverables%';

-- Performance monitoring query
SELECT 
  query,
  calls,
  mean_time,
  total_time
FROM pg_stat_statements 
WHERE query LIKE '%workspace%' 
ORDER BY total_time DESC 
LIMIT 10;`
          }
        ],
        configOptions: [
          {
            key: 'AUTO_MIGRATE_ON_STARTUP',
            type: 'boolean',
            default: 'false',
            description: 'Automatically run migrations on application startup'
          },
          {
            key: 'MIGRATION_BACKUP_ENABLED',
            type: 'boolean',
            default: 'true',
            description: 'Create automatic backups before migrations'
          }
        ]
      },
      {
        title: 'Goal-Deliverable Mapping Optimization',
        description: 'Implement AI-driven semantic mapping with fallback systems',
        complexity: 'expert',
        estimatedTime: '90-120 minutes',
        prerequisites: ['AI Goal Matcher understanding', 'Database optimization knowledge'],
        sections: [
          {
            title: 'AI Goal Matcher Integration',
            content: 'Set up intelligent goal-deliverable mapping',
            code: `# services/ai_goal_matcher.py
class AIGoalMatcher:
    def __init__(self, openai_client, confidence_threshold=0.7):
        self.client = openai_client
        self.confidence_threshold = confidence_threshold
        self.memory_cache = {}
    
    async def match_deliverable_to_goal(
        self, 
        deliverable_content: dict,
        deliverable_title: str,
        goals: list
    ):
        # Check memory cache first
        cache_key = self._generate_cache_key(deliverable_title, goals)
        if cache_key in self.memory_cache:
            return self.memory_cache[cache_key]
        
        # AI semantic analysis
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[{
                "role": "system",
                "content": "Analyze deliverable content and match to most appropriate goal based on semantic similarity."
            }, {
                "role": "user", 
                "content": f"Deliverable: {deliverable_title}\\nGoals: {goals}\\nContent: {deliverable_content}"
            }]
        )
        
        match_result = self._parse_ai_response(response)
        
        # Cache successful matches
        if match_result.confidence >= self.confidence_threshold:
            self.memory_cache[cache_key] = match_result
            
        return match_result`
          },
          {
            title: 'Fallback System Implementation',
            content: 'Multiple fallback levels for reliable goal assignment',
            code: `# database.py - Enhanced goal mapping logic
async def assign_deliverable_to_goal(deliverable_data, workspace_goals):
    mapped_goal_id = None
    
    # Level 1: Explicit goal_id provided
    if deliverable_data.get("goal_id"):
        provided_goal_id = deliverable_data.get("goal_id")
        matching_goal = next(
            (g for g in workspace_goals if g.get("id") == provided_goal_id), 
            None
        )
        if matching_goal:
            mapped_goal_id = provided_goal_id
            logger.info(f"🎯 Using provided goal_id: {mapped_goal_id}")
    
    # Level 2: AI-driven semantic matching
    if not mapped_goal_id and workspace_goals:
        try:
            active_goals = [g for g in workspace_goals if g.get("status") == "active"]
            if active_goals:
                match_result = await AIGoalMatcher.match_deliverable_to_goal(
                    deliverable_content=deliverable_data.get("content", {}),
                    deliverable_title=deliverable_data.get("title", ""),
                    goals=active_goals
                )
                
                if match_result.success and match_result.confidence >= 0.7:
                    mapped_goal_id = match_result.goal_id
                    logger.info(f"🎯 AI Goal Matcher: {match_result.reasoning}")
        except Exception as e:
            logger.error(f"❌ AI Goal Matcher failed: {e}")
    
    # Level 3: Pattern-based content matching
    if not mapped_goal_id:
        mapped_goal_id = _pattern_based_goal_matching(deliverable_data, workspace_goals)
    
    # Level 4: Emergency fallback
    if not mapped_goal_id and workspace_goals:
        for goal in workspace_goals:
            if goal.get("status") == "active":
                mapped_goal_id = goal.get("id")
                logger.warning(f"🚨 Emergency fallback: Using first active goal")
                break
    
    return mapped_goal_id`
          }
        ],
        configOptions: [
          {
            key: 'ENABLE_AI_GOAL_MATCHING',
            type: 'boolean',
            default: 'true',
            description: 'Enable AI-driven goal-deliverable matching'
          },
          {
            key: 'AI_MATCHING_CONFIDENCE_THRESHOLD',
            type: 'float',
            default: '0.7',
            description: 'Minimum confidence score for AI goal matching'
          }
        ]
      }
    ]
  },
  {
    id: 'security-hardening',
    title: 'Security Hardening',
    icon: Shield,
    color: 'bg-red-50 border-red-200',
    description: 'Advanced security configurations and compliance setup',
    guides: [
      {
        title: 'Rate Limiting & API Protection',
        description: 'Implement comprehensive rate limiting and API security measures',
        complexity: 'advanced',
        estimatedTime: '60-90 minutes',
        prerequisites: ['FastAPI knowledge', 'Security concepts understanding'],
        sections: [
          {
            title: 'Multi-Level Rate Limiting',
            content: 'Configure different rate limits for various operation types',
            code: `# security/rate_limiter.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

# Configure different limits for different operations
RATE_LIMITS = {
    "auto_completion": "5/minute",
    "goal_unblock": "10/minute", 
    "api_standard": "100/minute",
    "api_heavy": "10/minute",
    "websocket": "50/minute"
}

class SmartRateLimiter:
    def __init__(self):
        self.operation_limits = RATE_LIMITS
        self.user_contexts = {}
    
    def get_limit_for_operation(self, operation_type: str, user_context: dict):
        # Adaptive limits based on user tier
        base_limit = self.operation_limits.get(operation_type, "60/minute")
        
        if user_context.get("tier") == "premium":
            return self._increase_limit(base_limit, multiplier=2)
        elif user_context.get("tier") == "enterprise":
            return self._increase_limit(base_limit, multiplier=5)
            
        return base_limit`
          },
          {
            title: 'Request Validation & Sanitization',
            content: 'Implement comprehensive input validation',
            code: `# security/validators.py
from pydantic import BaseModel, validator, Field
from typing import Optional, Dict, Any
import bleach

class SecureWorkspaceRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('name')
    def sanitize_name(cls, v):
        # Remove any HTML/script tags
        return bleach.clean(v, strip=True)
    
    @validator('description')
    def sanitize_description(cls, v):
        if v:
            return bleach.clean(v, strip=True)
        return v
    
    @validator('metadata')
    def validate_metadata(cls, v):
        if v:
            # Ensure no executable content in metadata
            return sanitize_metadata(v)
        return v

def sanitize_metadata(metadata: dict) -> dict:
    """Recursively sanitize metadata dictionary"""
    clean_metadata = {}
    for key, value in metadata.items():
        if isinstance(value, str):
            clean_metadata[key] = bleach.clean(value, strip=True)
        elif isinstance(value, dict):
            clean_metadata[key] = sanitize_metadata(value)
        elif isinstance(value, list):
            clean_metadata[key] = [
                sanitize_metadata(item) if isinstance(item, dict) 
                else bleach.clean(str(item), strip=True)
                for item in value
            ]
        else:
            clean_metadata[key] = value
    return clean_metadata`
          }
        ],
        configOptions: [
          {
            key: 'RATE_LIMITING_ENABLED',
            type: 'boolean',
            default: 'true',
            description: 'Enable API rate limiting protection'
          },
          {
            key: 'SECURITY_AUDIT_LOGGING',
            type: 'boolean',
            default: 'true',
            description: 'Enable detailed security event logging'
          }
        ]
      }
    ]
  },
  {
    id: 'development-workflow',
    title: 'Development Workflow',
    icon: GitBranch,
    color: 'bg-green-50 border-green-200',
    description: 'Advanced development setup and CI/CD configuration',
    guides: [
      {
        title: 'Claude Code Sub-Agents Integration',
        description: 'Configure and optimize Claude Code quality gates',
        complexity: 'expert',
        estimatedTime: '120+ minutes',
        prerequisites: ['Claude Code understanding', 'CI/CD experience'],
        sections: [
          {
            title: 'Agent Configuration Setup',
            content: 'Configure specialized sub-agents for quality assurance',
            code: `# .claude/agents/director.md
# Director Agent - Quality Gate Orchestrator

## Role
Orchestrates quality gates and triggers specialized agents in sequence.

## Auto-Activation Triggers
- Changes to \`backend/ai_agents/\`
- Changes to \`backend/services/\`  
- Changes to \`backend/routes/\`
- Changes to \`frontend/src/components/\`
- Changes to \`frontend/src/hooks/\`

## Quality Gate Sequence
1. **architecture-guardian**: Architectural consistency review
2. **sdk-guardian**: SDK compliance verification
3. **db-steward**: Database schema and migration safety
4. **api-contract-guardian**: API contract validation
5. **principles-guardian**: 15 Pillars compliance check
6. **placeholder-police**: Placeholder and TODO detection
7. **fallback-test-sentinel**: Test validation
8. **docs-scribe**: Documentation synchronization

## Blocking Rules
- Any quality gate failure blocks merge/deployment
- Critical violations require explicit resolution
- Documentation must be updated for architectural changes`
          },
          {
            title: 'Pre-commit Hook Configuration',
            content: 'Automated quality checks before commits',
            code: `#!/bin/bash
# .git/hooks/pre-commit

# Critical file patterns that trigger Director
CRITICAL_PATTERNS=(
    "backend/ai_agents/"
    "backend/services/" 
    "backend/routes/"
    "frontend/src/components/"
    "migrations/"
    "models.py"
)

# Check if any critical files changed
changed_files=$(git diff --cached --name-only)
trigger_director=false

for pattern in "\${CRITICAL_PATTERNS[@]}"; do
    if echo "$changed_files" | grep -q "$pattern"; then
        trigger_director=true
        break
    fi
done

if [ "$trigger_director" = true ]; then
    echo "🎯 Critical files detected - Triggering Director quality gates"
    
    # Auto-invoke Director using Claude Code
    echo "Please invoke the Director to review these changes"
    
    # Log the trigger for audit
    echo "$(date): Director triggered for files: $changed_files" >> .claude/director_audit.log
fi

# Standard pre-commit checks
npm run lint
npm run typecheck

exit 0`
          }
        ],
        configOptions: [
          {
            key: 'CLAUDE_CODE_AUTO_DIRECTOR',
            type: 'boolean',
            default: 'true',
            description: 'Automatically invoke Director on critical changes'
          },
          {
            key: 'QUALITY_GATE_BLOCKING',
            type: 'boolean',
            default: 'true',
            description: 'Block operations when quality gates fail'
          }
        ]
      }
    ]
  }
]

export default function AdvancedSetupPage() {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [selectedGuide, setSelectedGuide] = useState<string | null>(null)
  const [copiedCommand, setCopiedCommand] = useState<string | null>(null)

  const copyToClipboard = (text: string, commandId: string) => {
    navigator.clipboard.writeText(text)
    setCopiedCommand(commandId)
    setTimeout(() => setCopiedCommand(null), 2000)
  }

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'intermediate': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'advanced': return 'bg-orange-100 text-orange-800 border-orange-200'
      case 'expert': return 'bg-red-100 text-red-800 border-red-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center space-x-4">
            <Link 
              href="/docs"
              className="inline-flex items-center text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Documentation
            </Link>
          </div>
          <div className="mt-4">
            <h1 className="text-3xl font-bold text-gray-900">Advanced Setup Guide</h1>
            <p className="text-gray-600 mt-2">
              Expert-level configuration patterns and optimization strategies
            </p>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Overview */}
        <div className="bg-white rounded-xl border p-8 mb-8">
          <div className="flex items-center space-x-4 mb-6">
            <div className="p-3 bg-purple-50 rounded-xl">
              <Settings className="w-8 h-8 text-purple-600" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Advanced Configuration</h2>
              <p className="text-gray-600">
                These guides assume expertise in the respective areas and cover complex scenarios
              </p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-yellow-50 rounded-lg p-6">
              <Zap className="w-8 h-8 text-yellow-600 mb-3" />
              <h3 className="font-semibold text-yellow-900 mb-2">Performance</h3>
              <p className="text-yellow-700 text-sm">
                Progressive loading, infinite loop prevention, optimization patterns
              </p>
            </div>
            <div className="bg-blue-50 rounded-lg p-6">
              <Database className="w-8 h-8 text-blue-600 mb-3" />
              <h3 className="font-semibold text-blue-900 mb-2">Database</h3>
              <p className="text-blue-700 text-sm">
                Advanced migrations, AI goal matching, data integrity monitoring
              </p>
            </div>
            <div className="bg-red-50 rounded-lg p-6">
              <Shield className="w-8 h-8 text-red-600 mb-3" />
              <h3 className="font-semibold text-red-900 mb-2">Security</h3>
              <p className="text-red-700 text-sm">
                Rate limiting, input validation, API protection, audit logging
              </p>
            </div>
            <div className="bg-green-50 rounded-lg p-6">
              <GitBranch className="w-8 h-8 text-green-600 mb-3" />
              <h3 className="font-semibold text-green-900 mb-2">Workflow</h3>
              <p className="text-green-700 text-sm">
                Claude Code integration, quality gates, pre-commit automation
              </p>
            </div>
          </div>
        </div>

        {/* Setup Categories */}
        <div className="bg-white rounded-xl border p-8 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-6">Setup Categories</h2>
          
          <div className="space-y-6">
            {setupCategories.map((category) => {
              const CategoryIcon = category.icon
              const isSelected = selectedCategory === category.id
              
              return (
                <div key={category.id} className="relative">
                  <div 
                    className={`${category.color} border rounded-xl p-6 transition-all cursor-pointer hover:shadow-md ${
                      isSelected ? 'shadow-lg' : ''
                    }`}
                    onClick={() => setSelectedCategory(isSelected ? null : category.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="p-3 bg-white rounded-xl">
                          <CategoryIcon className="w-6 h-6 text-gray-600" />
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">{category.title}</h3>
                          <p className="text-gray-600 text-sm">{category.description}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-4">
                        <span className="text-sm font-medium text-gray-500">
                          {category.guides.length} guides
                        </span>
                        <Settings className={`w-5 h-5 transition-all ${
                          isSelected ? 'text-gray-600 rotate-90' : 'text-gray-400'
                        }`} />
                      </div>
                    </div>
                    
                    {isSelected && (
                      <div className="mt-6 space-y-4">
                        {category.guides.map((guide, index) => {
                          const guideId = `${category.id}-${index}`
                          const isGuideSelected = selectedGuide === guideId
                          
                          return (
                            <div key={index} className="bg-white rounded-lg border p-6">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  setSelectedGuide(isGuideSelected ? null : guideId)
                                }}
                                className="w-full text-left"
                              >
                                <div className="flex items-center justify-between mb-3">
                                  <h4 className="font-semibold text-gray-900">{guide.title}</h4>
                                  <div className="flex items-center space-x-2">
                                    <span className={`px-3 py-1 rounded-full text-xs font-medium border ${
                                      getComplexityColor(guide.complexity)
                                    }`}>
                                      {guide.complexity.toUpperCase()}
                                    </span>
                                    <Code className={`w-4 h-4 transition-all ${
                                      isGuideSelected ? 'text-gray-600 rotate-90' : 'text-gray-400'
                                    }`} />
                                  </div>
                                </div>
                                <p className="text-gray-600 text-sm mb-3">{guide.description}</p>
                                <div className="flex items-center space-x-4 text-xs text-gray-500">
                                  <span className="flex items-center space-x-1">
                                    <Terminal className="w-3 h-3" />
                                    <span>{guide.estimatedTime}</span>
                                  </span>
                                  <span>{guide.prerequisites.length} prerequisites</span>
                                </div>
                              </button>
                              
                              {isGuideSelected && (
                                <div className="mt-6 space-y-6">
                                  {/* Prerequisites */}
                                  <div>
                                    <h5 className="font-medium text-gray-900 mb-2">Prerequisites</h5>
                                    <ul className="space-y-1">
                                      {guide.prerequisites.map((prereq, i) => (
                                        <li key={i} className="flex items-center space-x-2">
                                          <CheckCircle className="w-4 h-4 text-green-600" />
                                          <span className="text-sm text-gray-600">{prereq}</span>
                                        </li>
                                      ))}
                                    </ul>
                                  </div>
                                  
                                  {/* Implementation Sections */}
                                  <div>
                                    <h5 className="font-medium text-gray-900 mb-4">Implementation Guide</h5>
                                    <div className="space-y-4">
                                      {guide.sections.map((section, sectionIndex) => (
                                        <div key={sectionIndex} className="border rounded-lg p-4">
                                          <div className="flex items-center justify-between mb-2">
                                            <h6 className="font-medium text-gray-900">{section.title}</h6>
                                            <button
                                              onClick={(e) => {
                                                e.stopPropagation()
                                                copyToClipboard(section.code, `${guideId}-${sectionIndex}`)
                                              }}
                                              className="flex items-center text-xs text-gray-500 hover:text-gray-700"
                                            >
                                              <Copy className="w-3 h-3 mr-1" />
                                              {copiedCommand === `${guideId}-${sectionIndex}` ? 'Copied!' : 'Copy'}
                                            </button>
                                          </div>
                                          <p className="text-gray-600 text-sm mb-3">{section.content}</p>
                                          <pre className="bg-gray-900 text-green-400 text-xs p-3 rounded-lg overflow-x-auto">
                                            <code>{section.code}</code>
                                          </pre>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                  
                                  {/* Configuration Options */}
                                  {guide.configOptions && (
                                    <div>
                                      <h5 className="font-medium text-gray-900 mb-3">Configuration Options</h5>
                                      <div className="overflow-x-auto">
                                        <table className="w-full border-collapse border border-gray-300">
                                          <thead>
                                            <tr className="bg-gray-50">
                                              <th className="border border-gray-300 px-4 py-2 text-left font-medium">Variable</th>
                                              <th className="border border-gray-300 px-4 py-2 text-left font-medium">Type</th>
                                              <th className="border border-gray-300 px-4 py-2 text-left font-medium">Default</th>
                                              <th className="border border-gray-300 px-4 py-2 text-left font-medium">Description</th>
                                            </tr>
                                          </thead>
                                          <tbody>
                                            {guide.configOptions.map((option, optIndex) => (
                                              <tr key={optIndex} className="hover:bg-gray-50">
                                                <td className="border border-gray-300 px-4 py-2">
                                                  <code className="text-sm bg-gray-100 px-2 py-1 rounded">{option.key}</code>
                                                </td>
                                                <td className="border border-gray-300 px-4 py-2 text-sm text-gray-600">{option.type}</td>
                                                <td className="border border-gray-300 px-4 py-2">
                                                  <code className="text-sm text-gray-700">{option.default}</code>
                                                </td>
                                                <td className="border border-gray-300 px-4 py-2 text-sm text-gray-600">{option.description}</td>
                                              </tr>
                                            ))}
                                          </tbody>
                                        </table>
                                      </div>
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Best Practices */}
        <div className="bg-white rounded-xl border p-8">
          <div className="flex items-center space-x-4 mb-6">
            <div className="p-3 bg-green-50 rounded-xl">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">Advanced Setup Best Practices</h2>
              <p className="text-gray-600">Critical guidelines for complex configurations</p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h3 className="font-semibold text-gray-900">Configuration Management</h3>
              <ul className="space-y-2">
                <li className="flex items-start space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span className="text-sm text-gray-600">Always externalize configuration via environment variables</span>
                </li>
                <li className="flex items-start space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span className="text-sm text-gray-600">Validate configuration on application startup</span>
                </li>
                <li className="flex items-start space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span className="text-sm text-gray-600">Use type-safe configuration schemas with Pydantic</span>
                </li>
                <li className="flex items-start space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span className="text-sm text-gray-600">Implement graceful degradation for optional features</span>
                </li>
              </ul>
            </div>
            
            <div className="space-y-4">
              <h3 className="font-semibold text-gray-900">Development Workflow</h3>
              <ul className="space-y-2">
                <li className="flex items-start space-x-2">
                  <AlertTriangle className="w-4 h-4 text-orange-600 mt-0.5 flex-shrink-0" />
                  <span className="text-sm text-gray-600">Test advanced configurations in isolated environments first</span>
                </li>
                <li className="flex items-start space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span className="text-sm text-gray-600">Document all custom configuration patterns thoroughly</span>
                </li>
                <li className="flex items-start space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span className="text-sm text-gray-600">Use version control for configuration management</span>
                </li>
                <li className="flex items-start space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span className="text-sm text-gray-600">Monitor system health after implementing advanced features</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}