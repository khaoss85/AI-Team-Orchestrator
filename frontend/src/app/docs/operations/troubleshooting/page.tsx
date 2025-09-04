'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { 
  ArrowLeft, 
  AlertTriangle,
  CheckCircle,
  Code,
  Terminal,
  Zap,
  RefreshCw,
  Database,
  Globe,
  Search,
  Copy,
  ExternalLink,
  Play,
  Bug,
  Settings,
  Monitor
} from 'lucide-react'

const troubleshootingCategories = [
  {
    id: 'performance',
    title: 'Performance Issues',
    icon: Zap,
    color: 'bg-yellow-50 border-yellow-200',
    issues: [
      {
        problem: 'Infinite Loop in React Components',
        symptoms: ['Rapid console logs switching between states', 'Browser freezing', 'High CPU usage'],
        rootCause: 'Circular dependencies between useEffect hooks and state updates',
        solutions: [
          'Implement early return checks for already-active states',
          'Use single source of truth pattern (URL controls state)',
          'Add debouncing for rapid state changes',
          'Remove console.logs that trigger re-renders'
        ],
        codeExample: `// ❌ PROBLEMATIC: Creates infinite loop
useEffect(() => {
  if (goalId && goalId !== activeChat?.goalId) {
    setActiveChat(targetChat) // Triggers another useEffect
  }
}, [goalId, activeChat, setActiveChat])

// ✅ SOLUTION: Early return pattern
useEffect(() => {
  if (!goalId || goalId === activeChat?.goalId) return // Early exit
  const targetChat = chats.find(c => c.goalId === goalId)
  if (targetChat && targetChat.id !== activeChat?.id) {
    setActiveChat(targetChat) // Only update when necessary
  }
}, [goalId, activeChat?.id]) // Specific dependencies`
      },
      {
        problem: 'Slow Page Loading (90+ seconds)',
        symptoms: ['Pages taking extremely long to load', 'UI appears broken', 'Users think app crashed'],
        rootCause: 'Heavy API calls blocking essential UI rendering',
        solutions: [
          'Implement progressive loading architecture',
          'Load essential UI first, enhancement data in background',
          'Use Promise.all for parallel API calls',
          'Defer heavy operations like unified-assets to on-demand'
        ],
        codeExample: `// ✅ SOLUTION: Progressive Loading Pattern
// Phase 1: Essential UI (0-200ms)
const [workspace, team] = await Promise.all([
  api.workspaces.get(id), 
  api.agents.list(id)
])
setLoading(false) // UI ready!

// Phase 2: Background Enhancement (50ms+)
setTimeout(() => {
  loadGoalsProgressive() // Don't block UI
}, 50)

// Phase 3: On-Demand Heavy Assets
const loadFullAssets = async () => {
  await loadArtifacts(true) // Only when requested
}`
      }
    ]
  },
  {
    id: 'api',
    title: 'API & Backend Issues',
    icon: Globe,
    color: 'bg-blue-50 border-blue-200',
    issues: [
      {
        problem: '"Failed to fetch" Errors',
        symptoms: ['API calls returning network errors', 'Frontend can\'t reach backend', '500 or network timeout errors'],
        rootCause: 'Backend service not running or incorrect port configuration',
        solutions: [
          'Verify backend is running on port 8000',
          'Check backend process with ps aux | grep python',
          'Restart backend with: cd backend && python3 main.py',
          'Verify environment variables are loaded'
        ],
        codeExample: `# Diagnostic Commands
curl http://localhost:8000/health
ps aux | grep python
cd backend && python3 main.py

# Check environment variables
cd backend && python3 -c "from database import supabase; print('✅ DB Connected')"`
      },
      {
        problem: 'CORS Issues in Development',
        symptoms: ['CORS policy errors in browser console', 'Blocked cross-origin requests'],
        rootCause: 'Incorrect CORS configuration between frontend and backend',
        solutions: [
          'Ensure CORS middleware allows localhost:3000-3004',
          'Check CORS configuration in main.py',
          'Verify frontend API calls use correct base URL',
          'Use proxy configuration in Next.js if needed'
        ],
        codeExample: `# Backend CORS Configuration (main.py)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3004"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)`
      }
    ]
  },
  {
    id: 'database',
    title: 'Database Issues',
    icon: Database,
    color: 'bg-green-50 border-green-200',
    issues: [
      {
        problem: 'Database Column Missing Errors',
        symptoms: ['PostgreSQL column does not exist errors', 'Migration errors', 'Table structure issues'],
        rootCause: 'Database migrations not applied or incomplete schema updates',
        solutions: [
          'Run SQL migrations in order using EXECUTE_IN_ORDER.md',
          'Check Supabase dashboard for table structure',
          'Verify migration files are executed completely',
          'Use manual SQL commands file if needed'
        ],
        codeExample: `-- Check if migration was applied
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'workspace_insights' AND column_name = 'display_content';

-- Apply missing migration
ALTER TABLE workspace_insights ADD COLUMN display_content TEXT;
ALTER TABLE workspace_insights ADD COLUMN display_format VARCHAR(20) DEFAULT 'html';`
      },
      {
        problem: 'Foreign Key Constraint Violations',
        symptoms: ['Insert/update operations failing', 'Foreign key constraint errors', 'Data integrity issues'],
        rootCause: 'References to non-existent records or incorrect relationship setup',
        solutions: [
          'Verify referenced records exist before insert/update',
          'Check foreign key relationships in database schema',
          'Use proper cascade settings for deletions',
          'Validate workspace_id and other foreign keys'
        ],
        codeExample: `-- Verify workspace exists before inserting
SELECT id FROM workspaces WHERE id = 'workspace_id_here';

-- Check constraint violations
SELECT conname, conrelid::regclass, confrelid::regclass 
FROM pg_constraint WHERE contype = 'f' AND conname LIKE '%workspace%';`
      }
    ]
  },
  {
    id: 'ui',
    title: 'Frontend & UI Issues',
    icon: Monitor,
    color: 'bg-purple-50 border-purple-200',
    issues: [
      {
        problem: 'Components Not Rendering',
        symptoms: ['Blank screens', 'Missing UI elements', 'JavaScript errors in console'],
        rootCause: 'Missing dependencies, compilation errors, or state management issues',
        solutions: [
          'Check browser console for JavaScript errors',
          'Verify all imports are correct and dependencies installed',
          'Clear .next cache and restart development server',
          'Check if components are properly exported/imported'
        ],
        codeExample: `# Clear Next.js cache and restart
rm -rf .next
npm run dev

# Check for missing dependencies
npm install
npm audit fix

# Verify component exports
export default function ComponentName() { /* ... */ }`
      },
      {
        problem: 'Navigation Issues in SPA',
        symptoms: ['URLs not updating', 'Back/forward button issues', 'Router navigation broken'],
        rootCause: 'Next.js router configuration issues or conflicting navigation logic',
        solutions: [
          'Use Next.js router.push() instead of window.location',
          'Ensure proper use of Link components',
          'Check for conflicting onClick handlers',
          'Verify route structure matches file system'
        ],
        codeExample: `// ✅ CORRECT: Next.js navigation
import { useRouter } from 'next/navigation'
const router = useRouter()
router.push('/docs/troubleshooting')

// ❌ AVOID: Direct window navigation in SPA
window.location.href = '/docs/troubleshooting'`
      }
    ]
  },
  {
    id: 'integration',
    title: 'Integration Issues',
    icon: Settings,
    color: 'bg-red-50 border-red-200',
    issues: [
      {
        problem: 'OpenAI API Integration Failures',
        symptoms: ['AI features not working', 'OpenAI API errors', 'Assistant not responding'],
        rootCause: 'API key issues, rate limiting, or incorrect OpenAI integration',
        solutions: [
          'Verify OPENAI_API_KEY is set and valid',
          'Check API key has correct permissions (Assistants API)',
          'Monitor rate limits and usage quotas',
          'Verify USE_OPENAI_ASSISTANTS=true in environment'
        ],
        codeExample: `# Environment variables check
echo $OPENAI_API_KEY
grep OPENAI .env

# Test API connection
curl -H "Authorization: Bearer $OPENAI_API_KEY" \\
     https://api.openai.com/v1/models`
      },
      {
        problem: 'Supabase Connection Issues',
        symptoms: ['Database queries failing', 'Authentication errors', 'Connection timeouts'],
        rootCause: 'Incorrect Supabase configuration or network connectivity issues',
        solutions: [
          'Verify SUPABASE_URL and SUPABASE_KEY in environment',
          'Check Supabase project status and quotas',
          'Test database connection with simple query',
          'Verify network connectivity to Supabase'
        ],
        codeExample: `# Test Supabase connection
cd backend
python3 -c "
from database import supabase
result = supabase.table('workspaces').select('*').limit(1).execute()
print(f'✅ Connected: {len(result.data)} records')
"`
      }
    ]
  }
]

const diagnosticCommands = [
  {
    category: 'System Health',
    commands: [
      { 
        description: 'Check all services status',
        command: 'ps aux | grep -E "(python|node|npm)" | grep -v grep'
      },
      {
        description: 'Test backend health endpoint',
        command: 'curl http://localhost:8000/health'
      },
      {
        description: 'Check frontend development server',
        command: 'curl -I http://localhost:3004'
      }
    ]
  },
  {
    category: 'Database Diagnostics',
    commands: [
      {
        description: 'Test database connection',
        command: 'cd backend && python3 -c "from database import supabase; print(\'✅ DB Connected\')"'
      },
      {
        description: 'Check recent migrations',
        command: 'ls -la backend/sql_migrations/ | head -10'
      },
      {
        description: 'Verify table structure',
        command: 'psql -c "\\d workspace_insights" your_database'
      }
    ]
  },
  {
    category: 'Performance Analysis',
    commands: [
      {
        description: 'Monitor API response times',
        command: 'curl -w "Time: %{time_total}s\\n" -o /dev/null -s http://localhost:8000/api/workspaces'
      },
      {
        description: 'Check memory usage',
        command: 'ps aux --sort=-%mem | head -10'
      },
      {
        description: 'Monitor network connections',
        command: 'netstat -an | grep -E "(3000|3004|8000)"'
      }
    ]
  }
]

export default function TroubleshootingPage() {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [selectedIssue, setSelectedIssue] = useState<string | null>(null)
  const [copiedCommand, setCopiedCommand] = useState<string | null>(null)

  const copyToClipboard = (text: string, commandId: string) => {
    navigator.clipboard.writeText(text)
    setCopiedCommand(commandId)
    setTimeout(() => setCopiedCommand(null), 2000)
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
            <h1 className="text-3xl font-bold text-gray-900">Troubleshooting Guide</h1>
            <p className="text-gray-600 mt-2">
              Complete guide to diagnosing and resolving common issues in the AI Team Orchestrator
            </p>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Quick Diagnostics */}
        <div className="bg-white rounded-xl border p-8 mb-8">
          <div className="flex items-center space-x-4 mb-6">
            <div className="p-3 bg-red-50 rounded-xl">
              <Bug className="w-8 h-8 text-red-600" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Quick Diagnostics</h2>
              <p className="text-gray-600">
                Run these commands first to identify common issues
              </p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {diagnosticCommands.map((category) => (
              <div key={category.category} className="border rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-3">{category.category}</h3>
                <div className="space-y-3">
                  {category.commands.map((cmd, index) => (
                    <div key={index}>
                      <div className="flex items-center justify-between mb-1">
                        <p className="text-sm font-medium text-gray-700">{cmd.description}</p>
                        <button
                          onClick={() => copyToClipboard(cmd.command, `${category.category}-${index}`)}
                          className="text-xs text-gray-500 hover:text-gray-700"
                        >
                          <Copy className="w-3 h-3" />
                        </button>
                      </div>
                      <pre className="bg-gray-900 text-green-400 text-xs p-2 rounded overflow-x-auto">
                        <code>{cmd.command}</code>
                      </pre>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Issue Categories */}
        <div className="bg-white rounded-xl border p-8 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-6">Common Issues by Category</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
            {troubleshootingCategories.map((category) => {
              const CategoryIcon = category.icon
              const isSelected = selectedCategory === category.id
              
              return (
                <button
                  key={category.id}
                  onClick={() => setSelectedCategory(isSelected ? null : category.id)}
                  className={`${category.color} border rounded-xl p-4 text-left transition-all hover:shadow-md ${
                    isSelected ? 'shadow-lg ring-2 ring-blue-200' : ''
                  }`}
                >
                  <div className="flex items-center space-x-3 mb-2">
                    <CategoryIcon className="w-6 h-6 text-gray-600" />
                    <h3 className="font-semibold text-gray-900">{category.title}</h3>
                  </div>
                  <p className="text-sm text-gray-600">
                    {category.issues.length} common issues
                  </p>
                </button>
              )
            })}
          </div>

          {selectedCategory && (
            <div className="border-t pt-6">
              {(() => {
                const category = troubleshootingCategories.find(c => c.id === selectedCategory)!
                return (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      {category.title} - Common Issues
                    </h3>
                    <div className="space-y-6">
                      {category.issues.map((issue, index) => {
                        const issueId = `${category.id}-${index}`
                        const isIssueSelected = selectedIssue === issueId
                        
                        return (
                          <div key={index} className="border rounded-lg p-6">
                            <button
                              onClick={() => setSelectedIssue(isIssueSelected ? null : issueId)}
                              className="w-full text-left"
                            >
                              <div className="flex items-center justify-between">
                                <h4 className="font-semibold text-gray-900">{issue.problem}</h4>
                                <AlertTriangle className={`w-5 h-5 transition-transform ${
                                  isIssueSelected ? 'rotate-180 text-red-600' : 'text-gray-400'
                                }`} />
                              </div>
                            </button>
                            
                            {isIssueSelected && (
                              <div className="mt-4 space-y-4">
                                {/* Symptoms */}
                                <div>
                                  <h5 className="font-medium text-gray-900 mb-2">Symptoms</h5>
                                  <ul className="space-y-1">
                                    {issue.symptoms.map((symptom, i) => (
                                      <li key={i} className="flex items-center space-x-2">
                                        <div className="w-1.5 h-1.5 bg-red-400 rounded-full" />
                                        <span className="text-sm text-gray-600">{symptom}</span>
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                                
                                {/* Root Cause */}
                                <div>
                                  <h5 className="font-medium text-gray-900 mb-2">Root Cause</h5>
                                  <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded">
                                    {issue.rootCause}
                                  </p>
                                </div>
                                
                                {/* Solutions */}
                                <div>
                                  <h5 className="font-medium text-gray-900 mb-2">Solutions</h5>
                                  <ul className="space-y-2">
                                    {issue.solutions.map((solution, i) => (
                                      <li key={i} className="flex items-start space-x-2">
                                        <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                                        <span className="text-sm text-gray-600">{solution}</span>
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                                
                                {/* Code Example */}
                                {issue.codeExample && (
                                  <div>
                                    <div className="flex items-center justify-between mb-2">
                                      <h5 className="font-medium text-gray-900">Code Example</h5>
                                      <button
                                        onClick={() => copyToClipboard(issue.codeExample!, `issue-${issueId}`)}
                                        className="text-xs text-gray-500 hover:text-gray-700"
                                      >
                                        <Copy className="w-3 h-3" />
                                      </button>
                                    </div>
                                    <pre className="bg-gray-900 text-green-400 text-xs p-3 rounded-lg overflow-x-auto">
                                      <code>{issue.codeExample}</code>
                                    </pre>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )
              })()}
            </div>
          )}
        </div>

        {/* Emergency Procedures */}
        <div className="bg-white rounded-xl border p-8">
          <div className="flex items-center space-x-4 mb-6">
            <div className="p-3 bg-red-50 rounded-xl">
              <RefreshCw className="w-8 h-8 text-red-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">Emergency Procedures</h2>
              <p className="text-gray-600">When everything else fails, try these steps in order</p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-red-50 rounded-lg p-6">
              <h3 className="font-semibold text-red-900 mb-4">System Reset Procedure</h3>
              <ol className="space-y-2 text-sm">
                <li className="flex items-center space-x-2">
                  <span className="w-5 h-5 bg-red-100 rounded-full flex items-center justify-center text-xs font-bold">1</span>
                  <span>Stop all services (Ctrl+C on frontend and backend)</span>
                </li>
                <li className="flex items-center space-x-2">
                  <span className="w-5 h-5 bg-red-100 rounded-full flex items-center justify-center text-xs font-bold">2</span>
                  <span>Clear Next.js cache: rm -rf .next</span>
                </li>
                <li className="flex items-center space-x-2">
                  <span className="w-5 h-5 bg-red-100 rounded-full flex items-center justify-center text-xs font-bold">3</span>
                  <span>Restart backend: cd backend && python3 main.py</span>
                </li>
                <li className="flex items-center space-x-2">
                  <span className="w-5 h-5 bg-red-100 rounded-full flex items-center justify-center text-xs font-bold">4</span>
                  <span>Restart frontend: npm run dev</span>
                </li>
                <li className="flex items-center space-x-2">
                  <span className="w-5 h-5 bg-red-100 rounded-full flex items-center justify-center text-xs font-bold">5</span>
                  <span>Test health endpoints</span>
                </li>
              </ol>
            </div>
            
            <div className="bg-blue-50 rounded-lg p-6">
              <h3 className="font-semibold text-blue-900 mb-4">Get Help</h3>
              <div className="space-y-3 text-sm">
                <div>
                  <p className="font-medium text-blue-900">Check Logs</p>
                  <p className="text-blue-700">Browser console, terminal output, and server logs</p>
                </div>
                <div>
                  <p className="font-medium text-blue-900">Search Documentation</p>
                  <p className="text-blue-700">Use browser search (Ctrl+F) in documentation pages</p>
                </div>
                <div>
                  <p className="font-medium text-blue-900">Reproduce Issue</p>
                  <p className="text-blue-700">Document exact steps to reproduce the problem</p>
                </div>
                <div className="pt-2 border-t border-blue-200">
                  <p className="text-blue-600 text-xs">
                    💡 Tip: Include error messages, browser version, and operating system when reporting issues
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}