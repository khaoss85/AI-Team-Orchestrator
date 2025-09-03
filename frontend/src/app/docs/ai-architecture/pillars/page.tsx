'use client'

import React from 'react'
import Link from 'next/link'
import { ArrowLeft, Shield, CheckCircle, AlertTriangle, Code, Brain, Users, Zap } from 'lucide-react'

export default function PillarsPage() {
  const pillars = [
    {
      id: 1,
      title: "Real Tools Usage",
      description: "Use official SDKs and real tools, never direct API calls or mock implementations",
      example: "OpenAI Agents SDK, not direct HTTP requests to OpenAI API",
      importance: "critical"
    },
    {
      id: 2,
      title: "No Hard-Coding",
      description: "All configuration externalized via environment variables and config files",
      example: "DELIVERABLE_READINESS_THRESHOLD=100 instead of hardcoded values",
      importance: "critical"
    },
    {
      id: 3,
      title: "Domain Agnostic",
      description: "System works for any business sector without domain-specific assumptions",
      example: "Marketing, finance, tech, healthcare - all supported equally",
      importance: "high"
    },
    {
      id: 4,
      title: "Goal-First Architecture",
      description: "All tasks must be linked to goals, with progress tracking and updates",
      example: "Every task has goal_id and updates goal progress upon completion",
      importance: "critical"
    },
    {
      id: 5,
      title: "Multi-Tenant Ready",
      description: "Support multiple users, languages, and workspace isolation",
      example: "user_id isolation, i18n support, workspace-specific data",
      importance: "high"
    },
    {
      id: 6,
      title: "Workspace Memory",
      description: "Learn from successes and failures, store patterns for reuse",
      example: "success_pattern and failure_lesson storage with pattern matching",
      importance: "high"
    },
    {
      id: 7,
      title: "Autonomous Pipeline",
      description: "Task → Goal → Enhancement → Memory → Correction flow without human intervention",
      example: "Auto-recovery, quality gates, improvement loops",
      importance: "critical"
    },
    {
      id: 8,
      title: "AI-First Quality Assurance",
      description: "AI-driven quality checks with human-in-the-loop only for critical decisions",
      example: "AI quality gates, human feedback only for deliverable approval",
      importance: "high"
    },
    {
      id: 9,
      title: "Minimal UI/UX",
      description: "Claude/ChatGPT style clean interfaces, no visual bloat",
      example: "Simple typography, subtle colors, focus on content over decoration",
      importance: "medium"
    },
    {
      id: 10,
      title: "Explainability",
      description: "Show AI reasoning steps and alternative approaches when requested",
      example: "Real-time thinking processes, decision transparency, reasoning visibility",
      importance: "high"
    },
    {
      id: 11,
      title: "Production-Ready Code",
      description: "No placeholders, TODOs, or mock data in production systems",
      example: "Real implementations, complete error handling, no lorem ipsum",
      importance: "critical"
    },
    {
      id: 12,
      title: "Real Content Only",
      description: "Replace placeholder content with actual business-relevant data",
      example: "Actual market data instead of 'Sample Company XYZ'",
      importance: "high"
    },
    {
      id: 13,
      title: "Auto-Correction",
      description: "Detect gaps and automatically trigger corrective actions",
      example: "Gap detection → task creation → quality validation",
      importance: "medium"
    },
    {
      id: 14,
      title: "Service Layer Modularity",
      description: "Clean service boundaries with unified tool registry",
      example: "Separate services for each domain with clear interfaces",
      importance: "medium"
    },
    {
      id: 15,
      title: "Context-Aware Conversation",
      description: "Maintain conversation context via endpoints and Agents SDK",
      example: "Conversation history, context preservation, intelligent responses",
      importance: "high"
    }
  ]

  const getImportanceColor = (importance: string) => {
    switch (importance) {
      case 'critical': return 'bg-red-50 border-red-200 text-red-900'
      case 'high': return 'bg-orange-50 border-orange-200 text-orange-900'
      case 'medium': return 'bg-blue-50 border-blue-200 text-blue-900'
      default: return 'bg-gray-50 border-gray-200 text-gray-900'
    }
  }

  const getImportanceIcon = (importance: string) => {
    switch (importance) {
      case 'critical': return <AlertTriangle className="w-4 h-4 text-red-600" />
      case 'high': return <CheckCircle className="w-4 h-4 text-orange-600" />
      case 'medium': return <Zap className="w-4 h-4 text-blue-600" />
      default: return <Shield className="w-4 h-4 text-gray-600" />
    }
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
            <h1 className="text-3xl font-bold text-gray-900 mb-2">15 Pillars System</h1>
            <p className="text-gray-600">Core architectural principles governing the AI Team Orchestrator</p>
          </div>

          <div className="bg-white rounded-xl border p-8">
            {/* Overview */}
            <section className="mb-12">
              <div className="bg-blue-50 rounded-lg p-6 border border-blue-200 mb-6">
                <div className="flex items-center space-x-3">
                  <Shield className="w-6 h-6 text-blue-600" />
                  <div>
                    <h3 className="font-medium text-blue-900">Architectural Foundation</h3>
                    <p className="text-blue-700 text-sm mt-1">15 foundational principles ensuring system quality, reliability, and maintainability</p>
                  </div>
                </div>
              </div>
              
              <p className="text-gray-600 text-lg leading-relaxed mb-6">
                The 15 Pillars System represents the core architectural principles that govern every aspect of the AI Team Orchestrator. 
                These principles ensure consistent quality, prevent technical debt, and maintain system integrity across all components.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-gradient-to-br from-red-50 to-orange-50 rounded-lg p-6 border border-red-200">
                  <h4 className="font-semibold text-red-900 mb-2 flex items-center">
                    <AlertTriangle className="w-5 h-5 mr-2" />
                    5 Critical Pillars
                  </h4>
                  <p className="text-red-700 text-sm">Non-negotiable principles that block deployment if violated</p>
                </div>
                <div className="bg-gradient-to-br from-orange-50 to-yellow-50 rounded-lg p-6 border border-orange-200">
                  <h4 className="font-semibold text-orange-900 mb-2 flex items-center">
                    <CheckCircle className="w-5 h-5 mr-2" />
                    7 High Priority
                  </h4>
                  <p className="text-orange-700 text-sm">Important principles that significantly impact system quality</p>
                </div>
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
                  <h4 className="font-semibold text-blue-900 mb-2 flex items-center">
                    <Zap className="w-5 h-5 mr-2" />
                    3 Medium Priority
                  </h4>
                  <p className="text-blue-700 text-sm">Best practices that improve maintainability and user experience</p>
                </div>
              </div>
            </section>

            {/* Pillars Detail */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">The 15 Pillars</h2>
              
              <div className="space-y-6">
                {pillars.map((pillar) => (
                  <div key={pillar.id} className={`rounded-lg p-6 border ${getImportanceColor(pillar.importance)}`}>
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <div className="flex-shrink-0 w-8 h-8 bg-white rounded-full flex items-center justify-center font-bold text-sm border">
                          {pillar.id}
                        </div>
                        <h3 className="text-lg font-semibold">{pillar.title}</h3>
                      </div>
                      <div className="flex items-center space-x-2">
                        {getImportanceIcon(pillar.importance)}
                        <span className="text-xs font-medium uppercase tracking-wide">
                          {pillar.importance}
                        </span>
                      </div>
                    </div>
                    
                    <p className="mb-4 leading-relaxed">
                      {pillar.description}
                    </p>
                    
                    <div className="bg-white bg-opacity-50 rounded-lg p-3 border">
                      <div className="text-xs font-medium mb-1 opacity-75">Example:</div>
                      <p className="text-sm font-mono">{pillar.example}</p>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* Implementation Enforcement */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Pillar Enforcement</h2>
              
              <div className="space-y-6">
                <div className="bg-green-50 rounded-lg p-6 border border-green-200">
                  <h3 className="font-medium text-green-900 mb-4 flex items-center">
                    <Shield className="w-5 h-5 mr-2" />
                    Principles Guardian Agent
                  </h3>
                  <p className="text-green-700 text-sm mb-4">
                    Automated agent that reviews all code changes and blocks violations of critical pillars.
                  </p>
                  <div className="bg-white rounded-lg p-4 border border-green-200">
                    <h4 className="font-medium text-green-900 mb-2">Guardian Responsibilities:</h4>
                    <ul className="space-y-1 text-green-700 text-sm">
                      <li>• Scans code for hard-coded values and configuration violations</li>
                      <li>• Validates SDK compliance and prevents direct API usage</li>
                      <li>• Checks goal-task relationships and data flow</li>
                      <li>• Identifies placeholder content and incomplete implementations</li>
                      <li>• Enforces service layer boundaries and modularity</li>
                    </ul>
                  </div>
                </div>

                <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
                  <h3 className="font-medium text-blue-900 mb-4 flex items-center">
                    <Code className="w-5 h-5 mr-2" />
                    Quality Gate Integration
                  </h3>
                  <p className="text-blue-700 text-sm mb-4">
                    Multiple specialized agents work together to ensure pillar compliance:
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-3">
                      <div className="bg-white rounded-lg p-3 border border-blue-200">
                        <h5 className="font-medium text-blue-900 mb-1">Placeholder Police</h5>
                        <p className="text-blue-700 text-xs">Detects TODOs, placeholders, and incomplete code</p>
                      </div>
                      <div className="bg-white rounded-lg p-3 border border-blue-200">
                        <h5 className="font-medium text-blue-900 mb-1">System Architect</h5>
                        <p className="text-blue-700 text-xs">Ensures architectural consistency and patterns</p>
                      </div>
                      <div className="bg-white rounded-lg p-3 border border-blue-200">
                        <h5 className="font-medium text-blue-900 mb-1">DB Steward</h5>
                        <p className="text-blue-700 text-xs">Validates database schema and relationships</p>
                      </div>
                    </div>
                    <div className="space-y-3">
                      <div className="bg-white rounded-lg p-3 border border-blue-200">
                        <h5 className="font-medium text-blue-900 mb-1">API Contract Guardian</h5>
                        <p className="text-blue-700 text-xs">Enforces API consistency and contracts</p>
                      </div>
                      <div className="bg-white rounded-lg p-3 border border-blue-200">
                        <h5 className="font-medium text-blue-900 mb-1">Frontend UX Specialist</h5>
                        <p className="text-blue-700 text-xs">Maintains minimal UI/UX principles</p>
                      </div>
                      <div className="bg-white rounded-lg p-3 border border-blue-200">
                        <h5 className="font-medium text-blue-900 mb-1">Docs Scribe</h5>
                        <p className="text-blue-700 text-xs">Keeps documentation synchronized with code</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Pillar Categories */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Pillar Categories</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="space-y-6">
                  <div className="bg-red-50 rounded-lg p-6 border border-red-200">
                    <h3 className="font-medium text-red-900 mb-4 flex items-center">
                      <AlertTriangle className="w-5 h-5 mr-2" />
                      Critical Pillars (1, 2, 4, 7, 11)
                    </h3>
                    <ul className="space-y-2 text-red-700 text-sm">
                      <li>• <strong>Pillar 1:</strong> Real Tools Usage - No direct API calls</li>
                      <li>• <strong>Pillar 2:</strong> No Hard-Coding - Everything configurable</li>
                      <li>• <strong>Pillar 4:</strong> Goal-First - All tasks linked to goals</li>
                      <li>• <strong>Pillar 7:</strong> Autonomous Pipeline - No human blocks</li>
                      <li>• <strong>Pillar 11:</strong> Production-Ready - No placeholders</li>
                    </ul>
                  </div>

                  <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
                    <h3 className="font-medium text-blue-900 mb-4 flex items-center">
                      <Zap className="w-5 h-5 mr-2" />
                      Medium Priority (9, 13, 14)
                    </h3>
                    <ul className="space-y-2 text-blue-700 text-sm">
                      <li>• <strong>Pillar 9:</strong> Minimal UI/UX - Clean interfaces</li>
                      <li>• <strong>Pillar 13:</strong> Auto-Correction - Gap detection</li>
                      <li>• <strong>Pillar 14:</strong> Service Modularity - Clean boundaries</li>
                    </ul>
                  </div>
                </div>

                <div className="space-y-6">
                  <div className="bg-orange-50 rounded-lg p-6 border border-orange-200">
                    <h3 className="font-medium text-orange-900 mb-4 flex items-center">
                      <CheckCircle className="w-5 h-5 mr-2" />
                      High Priority (3, 5, 6, 8, 10, 12, 15)
                    </h3>
                    <ul className="space-y-2 text-orange-700 text-sm">
                      <li>• <strong>Pillar 3:</strong> Domain Agnostic - Works for any sector</li>
                      <li>• <strong>Pillar 5:</strong> Multi-Tenant - User isolation</li>
                      <li>• <strong>Pillar 6:</strong> Workspace Memory - Learning system</li>
                      <li>• <strong>Pillar 8:</strong> AI-First QA - Automated quality</li>
                      <li>• <strong>Pillar 10:</strong> Explainability - Reasoning visibility</li>
                      <li>• <strong>Pillar 12:</strong> Real Content - No lorem ipsum</li>
                      <li>• <strong>Pillar 15:</strong> Context-Aware - Conversation state</li>
                    </ul>
                  </div>

                  <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
                    <h3 className="font-medium text-gray-900 mb-4 flex items-center">
                      <Brain className="w-5 h-5 mr-2" />
                      AI-Driven Transformation
                    </h3>
                    <p className="text-gray-700 text-sm">
                      The 15 Pillars System enabled the complete transformation from hard-coded logic to AI-driven intelligence, 
                      ensuring every component follows consistent principles while maintaining flexibility and adaptability.
                    </p>
                  </div>
                </div>
              </div>
            </section>

            {/* Violation Consequences */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Violation Consequences</h2>
              
              <div className="space-y-4">
                <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                  <h4 className="font-medium text-red-900 mb-2 flex items-center">
                    <AlertTriangle className="w-4 h-4 mr-2" />
                    Critical Pillar Violations
                  </h4>
                  <ul className="space-y-1 text-red-700 text-sm">
                    <li>• <strong>Deployment Block:</strong> Code cannot be merged or deployed</li>
                    <li>• <strong>Automatic Rollback:</strong> System reverts to last compliant state</li>
                    <li>• <strong>Guardian Alert:</strong> Principles Guardian agent reports violation</li>
                    <li>• <strong>Required Fix:</strong> Must be resolved before proceeding</li>
                  </ul>
                </div>

                <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
                  <h4 className="font-medium text-orange-900 mb-2 flex items-center">
                    <CheckCircle className="w-4 h-4 mr-2" />
                    High Priority Violations
                  </h4>
                  <ul className="space-y-1 text-orange-700 text-sm">
                    <li>• <strong>Quality Warning:</strong> Flagged for review but not blocking</li>
                    <li>• <strong>Technical Debt:</strong> Added to improvement backlog</li>
                    <li>• <strong>Performance Impact:</strong> May affect system performance</li>
                    <li>• <strong>Monitoring Alert:</strong> Tracked in system health metrics</li>
                  </ul>
                </div>

                <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                  <h4 className="font-medium text-blue-900 mb-2 flex items-center">
                    <Zap className="w-4 h-4 mr-2" />
                    Medium Priority Violations
                  </h4>
                  <ul className="space-y-1 text-blue-700 text-sm">
                    <li>• <strong>Style Warning:</strong> Noted in code review</li>
                    <li>• <strong>Best Practice:</strong> Suggested improvement</li>
                    <li>• <strong>User Experience:</strong> May affect UX quality</li>
                    <li>• <strong>Future Consideration:</strong> Address in future iterations</li>
                  </ul>
                </div>
              </div>
            </section>

            {/* Practical Examples */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Practical Implementation Examples</h2>
              
              <div className="space-y-6">
                <div className="bg-green-50 rounded-lg p-6 border border-green-200">
                  <h3 className="font-medium text-green-900 mb-3">✅ Compliant Implementation</h3>
                  <div className="bg-gray-900 rounded-lg p-4">
                    <pre className="text-green-400 text-sm overflow-x-auto">
                      <code>{`# Pillar 1 & 2 Compliant: SDK usage with configuration
from agents import AgentSDK

# Environment variable configuration (Pillar 2)
MAX_RETRIES = os.getenv('MAX_RECOVERY_ATTEMPTS', 5)
CONFIDENCE_THRESHOLD = float(os.getenv('AI_RECOVERY_CONFIDENCE_THRESHOLD', 0.7))

# Official SDK usage (Pillar 1)
agent = AgentSDK.create(
    model='gpt-4',
    max_retries=MAX_RETRIES
)

# Goal-linked task creation (Pillar 4)
task = TaskManager.create_task(
    goal_id=goal.id,
    description=task_description,
    agent_id=agent.id
)

# Update goal progress (Pillar 4)
await GoalManager.update_progress(goal.id, task.completion_percentage)`}</code>
                    </pre>
                  </div>
                </div>

                <div className="bg-red-50 rounded-lg p-6 border border-red-200">
                  <h3 className="font-medium text-red-900 mb-3">❌ Non-Compliant Implementation</h3>
                  <div className="bg-gray-900 rounded-lg p-4">
                    <pre className="text-red-400 text-sm overflow-x-auto">
                      <code>{`# VIOLATIONS: Direct API call (Pillar 1), Hard-coding (Pillar 2), No goal link (Pillar 4)

import requests

# Hard-coded values violate Pillar 2
API_KEY = "sk-hardcoded-key"  # ❌ Should be env var
MAX_RETRIES = 3               # ❌ Should be configurable

# Direct API call violates Pillar 1
response = requests.post(
    "https://api.openai.com/v1/chat/completions",  # ❌ Should use SDK
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={"model": "gpt-4", "messages": messages}
)

# Task without goal connection violates Pillar 4
task = {
    "id": "task-123",
    "description": "TODO: Complete this later",  # ❌ Pillar 11 violation
    # ❌ Missing goal_id connection
}

# No goal progress update - violates Pillar 4`}</code>
                    </pre>
                  </div>
                </div>
              </div>
            </section>

            {/* Next Steps */}
            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Learn More</h2>
              <div className="space-y-3">
                <Link 
                  href="/docs/ai-architecture/quality-gates"
                  className="flex items-center space-x-3 p-4 border rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all"
                >
                  <div className="p-2 bg-green-50 rounded-lg">
                    <Shield className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Quality Gates System</h3>
                    <p className="text-gray-600 text-sm">How quality gates enforce the 15 pillars</p>
                  </div>
                </Link>

                <Link 
                  href="/docs/security/sdk-compliance"
                  className="flex items-center space-x-3 p-4 border rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all"
                >
                  <div className="p-2 bg-blue-50 rounded-lg">
                    <Code className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">SDK Compliance</h3>
                    <p className="text-gray-600 text-sm">Implementing Pillar 1 correctly</p>
                  </div>
                </Link>

                <Link 
                  href="/docs/development/api"
                  className="flex items-center space-x-3 p-4 border rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all"
                >
                  <div className="p-2 bg-purple-50 rounded-lg">
                    <Users className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">API Reference</h3>
                    <p className="text-gray-600 text-sm">See pillars in action through API design</p>
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