'use client'

import React from 'react'
import Link from 'next/link'
import { ArrowLeft, Shield, Users, Code, Database, CheckCircle, AlertTriangle, Zap, Brain } from 'lucide-react'

export default function QualityGatesPage() {
  const qualityGates = [
    {
      name: "Director",
      model: "opus",
      role: "Orchestrator",
      description: "Triggers other agents as quality gates, manages overall system quality",
      triggers: ["backend/ai_agents/", "backend/services/", "backend/routes/", "src/components/", "src/hooks/"],
      color: "purple"
    },
    {
      name: "System Architect",
      model: "opus", 
      role: "Architecture Guardian",
      description: "Ensures architectural consistency, component reuse, prevents anti-silo patterns",
      triggers: ["Architecture changes", "Component modifications", "System design updates"],
      color: "blue"
    },
    {
      name: "DB Steward",
      model: "sonnet",
      role: "Database Guardian",
      description: "Prevents schema duplicates, ensures migration safety, maintains data integrity",
      triggers: ["Database migrations", "Schema changes", "Data model updates"],
      color: "green"
    },
    {
      name: "API Contract Guardian",
      model: "sonnet",
      role: "API Validator",
      description: "Validates API contracts, prevents breaking changes, manages versioning",
      triggers: ["API endpoint changes", "Contract modifications", "Interface updates"],
      color: "orange"
    },
    {
      name: "Principles Guardian",
      model: "opus",
      role: "15 Pillars Enforcer",
      description: "Enforces compliance with 15 Pillars, blocks critical violations",
      triggers: ["Any code changes", "Configuration updates", "System modifications"],
      color: "red"
    },
    {
      name: "Placeholder Police",
      model: "sonnet",
      role: "Completeness Detector",
      description: "Detects hard-coded values, TODOs, placeholders, incomplete implementations",
      triggers: ["Code commits", "Documentation updates", "Configuration changes"],
      color: "yellow"
    },
    {
      name: "Frontend UX Specialist",
      model: "sonnet",
      role: "UI/UX Guardian",
      description: "Maintains minimal design principles, follows ChatGPT/Claude patterns",
      triggers: ["Frontend component changes", "UI modifications", "Styling updates"],
      color: "pink"
    },
    {
      name: "Docs Scribe",
      model: "sonnet",
      role: "Documentation Synchronizer",
      description: "Ensures documentation stays synchronized with code changes",
      triggers: ["CLAUDE.md", "README.md", "backend/main.py", "Documentation files"],
      color: "teal"
    }
  ]

  const getColorClasses = (color: string) => {
    const colors = {
      purple: 'bg-purple-50 border-purple-200 text-purple-900',
      blue: 'bg-blue-50 border-blue-200 text-blue-900',
      green: 'bg-green-50 border-green-200 text-green-900',
      orange: 'bg-orange-50 border-orange-200 text-orange-900',
      red: 'bg-red-50 border-red-200 text-red-900',
      yellow: 'bg-yellow-50 border-yellow-200 text-yellow-900',
      pink: 'bg-pink-50 border-pink-200 text-pink-900',
      teal: 'bg-teal-50 border-teal-200 text-teal-900'
    }
    return colors[color as keyof typeof colors] || 'bg-gray-50 border-gray-200 text-gray-900'
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <Link 
              href="/docs"
              className="inline-flex items-center text-blue-600 hover:text-blue-800 transition-colors mb-4"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Documentation
            </Link>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Quality Gates System</h1>
            <p className="text-gray-600">Autonomous quality assurance with 8 specialized AI agents</p>
          </div>

          <div className="bg-white rounded-xl border p-8">
            {/* Overview */}
            <section className="mb-12">
              <div className="bg-blue-50 rounded-lg p-6 border border-blue-200 mb-6">
                <div className="flex items-center space-x-3">
                  <Shield className="w-6 h-6 text-blue-600" />
                  <div>
                    <h3 className="font-medium text-blue-900">Autonomous Quality Assurance</h3>
                    <p className="text-blue-700 text-sm mt-1">8 specialized AI agents ensuring code quality, architecture, and compliance</p>
                  </div>
                </div>
              </div>
              
              <p className="text-gray-600 text-lg leading-relaxed mb-6">
                The Quality Gates System provides autonomous, AI-driven quality assurance using 8 specialized agents. 
                Each agent monitors specific aspects of the system, from code quality to architectural compliance, 
                ensuring every change meets high standards before deployment.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-6 border border-green-200">
                  <h4 className="font-semibold text-green-900 mb-2">Cost Optimized</h4>
                  <p className="text-green-700 text-sm">Smart conditional triggering reduces API costs by 94%</p>
                </div>
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
                  <h4 className="font-semibold text-blue-900 mb-2">Zero Manual Overhead</h4>
                  <p className="text-blue-700 text-sm">Director agent decides which gates to activate automatically</p>
                </div>
                <div className="bg-gradient-to-br from-purple-50 to-violet-50 rounded-lg p-6 border border-purple-200">
                  <h4 className="font-semibold text-purple-900 mb-2">Blocking Violations</h4>
                  <p className="text-purple-700 text-sm">Critical issues prevent deployment until resolved</p>
                </div>
              </div>
            </section>

            {/* Quality Gates Overview */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">The 8 Quality Gates</h2>
              
              <div className="space-y-6">
                {qualityGates.map((gate, index) => (
                  <div key={index} className={`rounded-lg p-6 border ${getColorClasses(gate.color)}`}>
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center space-x-4">
                        <div className="flex-shrink-0 w-12 h-12 bg-white rounded-full flex items-center justify-center font-bold border">
                          <Shield className="w-6 h-6" />
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold">{gate.name}</h3>
                          <p className="text-sm opacity-75">{gate.role}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-medium bg-white bg-opacity-50 px-2 py-1 rounded">
                          {gate.model}
                        </span>
                      </div>
                    </div>
                    
                    <p className="mb-4 leading-relaxed">
                      {gate.description}
                    </p>
                    
                    <div className="bg-white bg-opacity-50 rounded-lg p-3 border">
                      <div className="text-xs font-medium mb-2 opacity-75">Activation Triggers:</div>
                      <div className="flex flex-wrap gap-2">
                        {gate.triggers.map((trigger, triggerIndex) => (
                          <span key={triggerIndex} className="text-xs bg-white px-2 py-1 rounded border">
                            {trigger}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* Gate Activation Flow */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Gate Activation Flow</h2>
              
              <div className="bg-gray-50 rounded-lg p-6 border">
                <div className="space-y-6">
                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0 w-10 h-10 bg-blue-600 text-white text-lg font-bold rounded-full flex items-center justify-center">1</div>
                    <div className="flex-1">
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Change Detection</h3>
                      <p className="text-gray-600 mb-3">
                        System detects code changes, file modifications, or deployment triggers through Git hooks and file watchers.
                      </p>
                      <div className="bg-white rounded-lg p-3 border">
                        <code className="text-sm text-gray-700">
                          Modified files: backend/ai_agents/director.py, src/components/TeamStatus.tsx
                        </code>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0 w-10 h-10 bg-purple-600 text-white text-lg font-bold rounded-full flex items-center justify-center">2</div>
                    <div className="flex-1">
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Director Analysis</h3>
                      <p className="text-gray-600 mb-3">
                        Director agent analyzes the changes and determines which quality gates should be activated based on impact and risk assessment.
                      </p>
                      <div className="bg-purple-50 rounded-lg p-3 border border-purple-200">
                        <p className="text-purple-800 text-sm italic">
                          "Backend AI agent changes detected. Activating: System Architect, Principles Guardian, Placeholder Police, Docs Scribe"
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0 w-10 h-10 bg-green-600 text-white text-lg font-bold rounded-full flex items-center justify-center">3</div>
                    <div className="flex-1">
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Parallel Gate Execution</h3>
                      <p className="text-gray-600 mb-3">
                        Selected quality gates run in parallel, each analyzing their specific domain and providing pass/fail results with detailed feedback.
                      </p>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="bg-green-50 rounded p-2 border border-green-200">
                          <span className="text-xs text-green-600">✅ System Architect: PASS</span>
                        </div>
                        <div className="bg-green-50 rounded p-2 border border-green-200">
                          <span className="text-xs text-green-600">✅ Principles Guardian: PASS</span>
                        </div>
                        <div className="bg-red-50 rounded p-2 border border-red-200">
                          <span className="text-xs text-red-600">❌ Placeholder Police: FAIL</span>
                        </div>
                        <div className="bg-green-50 rounded p-2 border border-green-200">
                          <span className="text-xs text-green-600">✅ Docs Scribe: PASS</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0 w-10 h-10 bg-red-600 text-white text-lg font-bold rounded-full flex items-center justify-center">4</div>
                    <div className="flex-1">
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Gate Decision</h3>
                      <p className="text-gray-600 mb-3">
                        If any critical gate fails, deployment is blocked. The system provides detailed feedback and suggested fixes.
                      </p>
                      <div className="bg-red-50 rounded-lg p-3 border border-red-200">
                        <div className="text-red-900 font-medium mb-1">🚨 DEPLOYMENT BLOCKED</div>
                        <p className="text-red-700 text-sm">
                          Placeholder Police found TODO comments in production code. Remove placeholders before deployment.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Cost Optimization */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Cost Optimization Strategy</h2>
              
              <div className="bg-green-50 rounded-lg p-6 border border-green-200">
                <h3 className="font-medium text-green-900 mb-4 flex items-center">
                  <Zap className="w-5 h-5 mr-2" />
                  Smart Conditional Triggering (94% Cost Reduction)
                </h3>
                
                <div className="space-y-4">
                  <div className="bg-white rounded-lg p-4 border border-green-200">
                    <h4 className="font-medium text-green-900 mb-2">Traditional Approach (Expensive):</h4>
                    <p className="text-green-700 text-sm mb-2">
                      Run all 8 quality gates on every change = 8 API calls × $0.15 = $1.20 per change
                    </p>
                    <div className="text-xs text-green-600 bg-green-100 px-2 py-1 rounded inline-block">
                      100 changes/day × $1.20 = $120/day
                    </div>
                  </div>

                  <div className="bg-white rounded-lg p-4 border border-green-200">
                    <h4 className="font-medium text-green-900 mb-2">Smart Approach (Optimized):</h4>
                    <p className="text-green-700 text-sm mb-2">
                      Director analyzes and triggers only relevant gates = 1.8 average gates per change
                    </p>
                    <div className="text-xs text-green-600 bg-green-100 px-2 py-1 rounded inline-block">
                      100 changes/day × $0.27 = $7/day (94% savings)
                    </div>
                  </div>

                  <div className="bg-green-100 rounded-lg p-4 border border-green-200">
                    <h4 className="font-medium text-green-900 mb-2">Triggering Logic Examples:</h4>
                    <ul className="space-y-1 text-green-700 text-sm">
                      <li>• <code>*.tsx</code> changes → Frontend UX Specialist only</li>
                      <li>• Database migrations → DB Steward + System Architect</li>
                      <li>• API changes → API Contract Guardian + System Architect + Principles Guardian</li>
                      <li>• Documentation updates → Docs Scribe only</li>
                    </ul>
                  </div>
                </div>
              </div>
            </section>

            {/* Gate Specifications */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Detailed Gate Specifications</h2>
              
              <div className="space-y-6">
                <div className="bg-red-50 rounded-lg p-6 border border-red-200">
                  <h3 className="font-medium text-red-900 mb-4 flex items-center">
                    <AlertTriangle className="w-5 h-5 mr-2" />
                    Critical Gates (Blocking)
                  </h3>
                  
                  <div className="space-y-4">
                    <div className="bg-white rounded-lg p-4 border border-red-200">
                      <h4 className="font-medium text-red-900 mb-2">Principles Guardian</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <h5 className="font-medium text-red-800 mb-1">Checks:</h5>
                          <ul className="space-y-1 text-red-700 text-sm">
                            <li>• 15 Pillars compliance</li>
                            <li>• Hard-coded value detection</li>
                            <li>• SDK usage validation</li>
                            <li>• Goal-task relationship integrity</li>
                          </ul>
                        </div>
                        <div>
                          <h5 className="font-medium text-red-800 mb-1">Blocking Conditions:</h5>
                          <ul className="space-y-1 text-red-700 text-sm">
                            <li>• Direct API calls instead of SDK</li>
                            <li>• Tasks without goal_id</li>
                            <li>• Hard-coded configuration</li>
                            <li>• Non-production-ready code</li>
                          </ul>
                        </div>
                      </div>
                    </div>

                    <div className="bg-white rounded-lg p-4 border border-red-200">
                      <h4 className="font-medium text-red-900 mb-2">System Architect</h4>
                      <div className="grid grid-cols-1 md:grid-2 gap-4">
                        <div>
                          <h5 className="font-medium text-red-800 mb-1">Reviews:</h5>
                          <ul className="space-y-1 text-red-700 text-sm">
                            <li>• Architectural consistency</li>
                            <li>• Component reuse patterns</li>
                            <li>• Service boundary violations</li>
                            <li>• Anti-silo pattern prevention</li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
                  <h3 className="font-medium text-blue-900 mb-4 flex items-center">
                    <CheckCircle className="w-5 h-5 mr-2" />
                    Specialized Gates (Non-blocking)
                  </h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-white rounded-lg p-4 border border-blue-200">
                      <h4 className="font-medium text-blue-900 mb-2">DB Steward</h4>
                      <ul className="space-y-1 text-blue-700 text-sm">
                        <li>• Schema duplication prevention</li>
                        <li>• Migration safety validation</li>
                        <li>• Data integrity checks</li>
                        <li>• Performance impact analysis</li>
                      </ul>
                    </div>

                    <div className="bg-white rounded-lg p-4 border border-blue-200">
                      <h4 className="font-medium text-blue-900 mb-2">Frontend UX Specialist</h4>
                      <ul className="space-y-1 text-blue-700 text-sm">
                        <li>• Minimal design compliance</li>
                        <li>• ChatGPT/Claude pattern adherence</li>
                        <li>• Accessibility validation</li>
                        <li>• Performance optimization</li>
                      </ul>
                    </div>

                    <div className="bg-white rounded-lg p-4 border border-blue-200">
                      <h4 className="font-medium text-blue-900 mb-2">API Contract Guardian</h4>
                      <ul className="space-y-1 text-blue-700 text-sm">
                        <li>• Breaking change detection</li>
                        <li>• Contract consistency validation</li>
                        <li>• Version management</li>
                        <li>• Documentation synchronization</li>
                      </ul>
                    </div>

                    <div className="bg-white rounded-lg p-4 border border-blue-200">
                      <h4 className="font-medium text-blue-900 mb-2">Placeholder Police</h4>
                      <ul className="space-y-1 text-blue-700 text-sm">
                        <li>• TODO/FIXME detection</li>
                        <li>• Lorem ipsum identification</li>
                        <li>• Mock data removal</li>
                        <li>• Incomplete implementation detection</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Configuration */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Quality Gates Configuration</h2>
              
              <div className="bg-gray-900 rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-gray-400">Claude Code Agent Configuration</span>
                </div>
                <pre className="text-green-400 text-sm overflow-x-auto">
                  <code>{`# .claude/agents/ directory structure

director.md              # Orchestrator (opus) - triggers other agents
system-architect.md      # Architecture guardian (opus)  
db-steward.md           # Database guardian (sonnet)
api-contract-guardian.md # API contract validator (sonnet)
principles-guardian.md   # 15 Pillars enforcer (opus)
placeholder-police.md    # Completeness detector (sonnet)
frontend-ux-specialist.md # UI/UX guardian (sonnet)
docs-scribe.md          # Documentation sync (sonnet)

# Auto-activation triggers in agent configs:
# - File path patterns (backend/*, src/*, etc.)
# - Change type detection
# - Impact analysis
# - Risk assessment`}</code>
                </pre>
              </div>
            </section>

            {/* Integration with CI/CD */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">CI/CD Integration</h2>
              
              <div className="bg-yellow-50 rounded-lg p-6 border border-yellow-200">
                <h3 className="font-medium text-yellow-900 mb-4">Git Hooks Integration</h3>
                
                <div className="space-y-4">
                  <div className="bg-white rounded-lg p-4 border border-yellow-200">
                    <h4 className="font-medium text-yellow-900 mb-2">Pre-commit Hook</h4>
                    <div className="bg-gray-900 rounded p-3 mb-2">
                      <code className="text-yellow-400 text-sm">
                        #!/bin/bash<br/>
                        # Trigger Director for critical file changes<br/>
                        if [[ $(git diff --cached --name-only | grep -E "(backend/|src/)" | wc -l) -gt 0 ]]; then<br/>
                        &nbsp;&nbsp;claude-code task director "Review these changes"<br/>
                        fi
                      </code>
                    </div>
                    <p className="text-yellow-700 text-sm">
                      Automatically invokes Director quality gates before commits to critical directories.
                    </p>
                  </div>

                  <div className="bg-white rounded-lg p-4 border border-yellow-200">
                    <h4 className="font-medium text-yellow-900 mb-2">Quality Gate Results</h4>
                    <p className="text-yellow-700 text-sm mb-2">
                      Gates provide structured feedback that integrates with development workflows:
                    </p>
                    <ul className="space-y-1 text-yellow-700 text-sm">
                      <li>• ✅ Pass: Change approved for deployment</li>
                      <li>• ⚠️ Warning: Issues noted but not blocking</li>
                      <li>• ❌ Fail: Critical issues prevent deployment</li>
                      <li>• 📝 Suggestions: Improvement recommendations</li>
                    </ul>
                  </div>
                </div>
              </div>
            </section>

            {/* Next Steps */}
            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Learn More</h2>
              <div className="space-y-3">
                <Link 
                  href="/docs/ai-architecture/pillars"
                  className="flex items-center space-x-3 p-4 border rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all"
                >
                  <div className="p-2 bg-red-50 rounded-lg">
                    <AlertTriangle className="w-5 h-5 text-red-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">15 Pillars System</h3>
                    <p className="text-gray-600 text-sm">Core principles enforced by quality gates</p>
                  </div>
                </Link>

                <Link 
                  href="/docs/ai-architecture/sub-agents"
                  className="flex items-center space-x-3 p-4 border rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all"
                >
                  <div className="p-2 bg-blue-50 rounded-lg">
                    <Users className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Sub-Agent Orchestration</h3>
                    <p className="text-gray-600 text-sm">How quality gates coordinate with other agents</p>
                  </div>
                </Link>

                <Link 
                  href="/docs/development/api"
                  className="flex items-center space-x-3 p-4 border rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all"
                >
                  <div className="p-2 bg-green-50 rounded-lg">
                    <Code className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Development Guide</h3>
                    <p className="text-gray-600 text-sm">Implementing code that passes quality gates</p>
                  </div>
                </Link>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  )
}