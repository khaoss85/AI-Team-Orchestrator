'use client'

import React from 'react'
import Link from 'next/link'
import { ArrowLeft, CheckSquare, Clock, Users, Zap, AlertTriangle, RefreshCw, Target, Brain } from 'lucide-react'

export default function TasksPage() {
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
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Task Execution System</h1>
            <p className="text-gray-600">Understanding the atomic units of work in the AI Team Orchestrator</p>
          </div>

          <div className="bg-white rounded-xl border p-8">
            {/* Overview */}
            <section className="mb-12">
              <div className="bg-blue-50 rounded-lg p-6 border border-blue-200 mb-6">
                <div className="flex items-center space-x-3">
                  <CheckSquare className="w-6 h-6 text-blue-600" />
                  <div>
                    <h3 className="text-lg font-semibold text-blue-900">Task-Driven Architecture</h3>
                    <p className="text-blue-700 mt-1">
                      Tasks are the atomic units of work that connect goals to concrete deliverables through specialized AI agents.
                    </p>
                  </div>
                </div>
              </div>

              <div className="prose prose-lg max-w-none">
                <p>
                  The Task Execution System is the operational backbone of the AI Team Orchestrator. Every action, 
                  from content creation to technical implementation, flows through the task system where specialized 
                  AI agents collaborate to achieve specific objectives.
                </p>
              </div>
            </section>

            {/* Task Lifecycle */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <Clock className="w-6 h-6 mr-3 text-indigo-600" />
                Task Lifecycle
              </h2>

              <div className="grid md:grid-cols-2 gap-6 mb-8">
                <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-6 border border-green-200">
                  <div className="flex items-center space-x-3 mb-3">
                    <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center">
                      <span className="text-white font-bold text-sm">1</span>
                    </div>
                    <h3 className="font-semibold text-green-900">Task Creation</h3>
                  </div>
                  <p className="text-green-800 text-sm">
                    Goals are decomposed into specific, actionable tasks by the Director Agent using AI-driven analysis.
                  </p>
                </div>

                <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-6 border border-blue-200">
                  <div className="flex items-center space-x-3 mb-3">
                    <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                      <span className="text-white font-bold text-sm">2</span>
                    </div>
                    <h3 className="font-semibold text-blue-900">Agent Assignment</h3>
                  </div>
                  <p className="text-blue-800 text-sm">
                    AI semantic matching assigns tasks to the most qualified specialist agents based on skills and context.
                  </p>
                </div>

                <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-6 border border-purple-200">
                  <div className="flex items-center space-x-3 mb-3">
                    <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center">
                      <span className="text-white font-bold text-sm">3</span>
                    </div>
                    <h3 className="font-semibold text-purple-900">Execution</h3>
                  </div>
                  <p className="text-purple-800 text-sm">
                    Agents execute tasks using real tools (web search, file operations, API calls) with full transparency.
                  </p>
                </div>

                <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg p-6 border border-orange-200">
                  <div className="flex items-center space-x-3 mb-3">
                    <div className="w-8 h-8 bg-orange-600 rounded-full flex items-center justify-center">
                      <span className="text-white font-bold text-sm">4</span>
                    </div>
                    <h3 className="font-semibold text-orange-900">Quality Assurance</h3>
                  </div>
                  <p className="text-orange-800 text-sm">
                    Automated QA gates validate outputs, ensure quality standards, and trigger improvements when needed.
                  </p>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-6 border">
                <h4 className="font-semibold text-gray-900 mb-3">Task Status Flow</h4>
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full">pending</span>
                  <span className="mx-2">→</span>
                  <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full">in_progress</span>
                  <span className="mx-2">→</span>
                  <span className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full">under_review</span>
                  <span className="mx-2">→</span>
                  <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full">completed</span>
                </div>
                <p className="text-gray-600 text-sm mt-3">
                  Failed tasks trigger autonomous recovery through specialized recovery agents.
                </p>
              </div>
            </section>

            {/* Agent Specialization */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <Users className="w-6 h-6 mr-3 text-indigo-600" />
                Agent Specialization
              </h2>

              <div className="space-y-6">
                <div className="border rounded-lg p-6">
                  <div className="flex items-center space-x-3 mb-4">
                    <Brain className="w-5 h-5 text-blue-600" />
                    <h3 className="font-semibold text-gray-900">Content Specialist</h3>
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">Expert</span>
                  </div>
                  <p className="text-gray-600 mb-3">
                    Specializes in content creation, copywriting, and marketing materials with domain expertise.
                  </p>
                  <div className="bg-gray-50 rounded p-3">
                    <p className="text-sm text-gray-700 font-mono">
                      <strong>Example Task:</strong> "Create email sequence for SaaS onboarding campaign"
                    </p>
                  </div>
                </div>

                <div className="border rounded-lg p-6">
                  <div className="flex items-center space-x-3 mb-4">
                    <Zap className="w-5 h-5 text-green-600" />
                    <h3 className="font-semibold text-gray-900">Technical Specialist</h3>
                    <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">Senior</span>
                  </div>
                  <p className="text-gray-600 mb-3">
                    Handles technical implementation, code review, and system architecture tasks.
                  </p>
                  <div className="bg-gray-50 rounded p-3">
                    <p className="text-sm text-gray-700 font-mono">
                      <strong>Example Task:</strong> "Implement OAuth authentication system"
                    </p>
                  </div>
                </div>

                <div className="border rounded-lg p-6">
                  <div className="flex items-center space-x-3 mb-4">
                    <Target className="w-5 h-5 text-purple-600" />
                    <h3 className="font-semibold text-gray-900">Strategy Specialist</h3>
                    <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded">Expert</span>
                  </div>
                  <p className="text-gray-600 mb-3">
                    Focuses on business strategy, market analysis, and high-level planning tasks.
                  </p>
                  <div className="bg-gray-50 rounded p-3">
                    <p className="text-sm text-gray-700 font-mono">
                      <strong>Example Task:</strong> "Develop go-to-market strategy for B2B product"
                    </p>
                  </div>
                </div>
              </div>
            </section>

            {/* Autonomous Recovery */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <RefreshCw className="w-6 h-6 mr-3 text-indigo-600" />
                Autonomous Recovery System
              </h2>

              <div className="bg-orange-50 rounded-lg p-6 border border-orange-200 mb-6">
                <div className="flex items-start space-x-3">
                  <AlertTriangle className="w-6 h-6 text-orange-600 mt-1" />
                  <div>
                    <h3 className="text-lg font-semibold text-orange-900">Zero Human Intervention</h3>
                    <p className="text-orange-700 mt-1">
                      When tasks fail, the system automatically analyzes the failure and applies recovery strategies 
                      without requiring human intervention.
                    </p>
                  </div>
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h4 className="font-semibold text-gray-900">Recovery Strategies</h4>
                  <ul className="space-y-2 text-sm text-gray-600">
                    <li className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                      <span>Retry with different agent specialization</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-600 rounded-full"></div>
                      <span>Decompose into smaller subtasks</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-purple-600 rounded-full"></div>
                      <span>Alternative approach methodology</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-orange-600 rounded-full"></div>
                      <span>Context reconstruction from memory</span>
                    </li>
                  </ul>
                </div>

                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-900 mb-3">Recovery Metrics</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Success Rate:</span>
                      <span className="font-semibold text-green-600">85%+</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Recovery Time:</span>
                      <span className="font-semibold text-blue-600">&lt; 60s</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Max Attempts:</span>
                      <span className="font-semibold text-purple-600">5</span>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Technical Architecture */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Technical Architecture</h2>

              <div className="bg-gray-900 rounded-lg p-6 text-white mb-6">
                <h3 className="text-lg font-semibold mb-4 text-green-400">Task Execution Pipeline</h3>
                <pre className="text-sm overflow-x-auto">
                  <code>{`# Task execution flow
1. Goal Decomposition  → AI breaks down objectives
2. Task Classification → Semantic categorization
3. Agent Matching     → Skills-based assignment
4. Tool Execution     → Real external tools
5. Quality Gates      → Automated validation
6. Deliverable Gen    → Asset creation
7. Memory Storage     → Pattern learning`}</code>
                </pre>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
                  <h4 className="font-semibold text-blue-900 mb-3">Database Integration</h4>
                  <ul className="text-sm text-blue-800 space-y-1">
                    <li>• Task lifecycle tracking</li>
                    <li>• Agent performance metrics</li>
                    <li>• Failure pattern analysis</li>
                    <li>• Recovery success rates</li>
                  </ul>
                </div>

                <div className="bg-green-50 rounded-lg p-6 border border-green-200">
                  <h4 className="font-semibold text-green-900 mb-3">Real-time Updates</h4>
                  <ul className="text-sm text-green-800 space-y-1">
                    <li>• WebSocket status broadcast</li>
                    <li>• Thinking process visibility</li>
                    <li>• Live progress tracking</li>
                    <li>• Error notifications</li>
                  </ul>
                </div>
              </div>
            </section>

            {/* Configuration */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Configuration</h2>

              <div className="bg-gray-100 rounded-lg p-6">
                <h3 className="font-semibold text-gray-900 mb-4">Key Environment Variables</h3>
                <div className="space-y-3 text-sm">
                  <div className="flex flex-col space-y-1">
                    <code className="bg-gray-800 text-green-400 px-2 py-1 rounded">MAX_CONCURRENT_TASKS=10</code>
                    <span className="text-gray-600 text-xs">Maximum tasks executing simultaneously</span>
                  </div>
                  <div className="flex flex-col space-y-1">
                    <code className="bg-gray-800 text-green-400 px-2 py-1 rounded">TASK_TIMEOUT_MINUTES=30</code>
                    <span className="text-gray-600 text-xs">Maximum execution time before timeout</span>
                  </div>
                  <div className="flex flex-col space-y-1">
                    <code className="bg-gray-800 text-green-400 px-2 py-1 rounded">ENABLE_AUTO_TASK_RECOVERY=true</code>
                    <span className="text-gray-600 text-xs">Enable autonomous failure recovery</span>
                  </div>
                  <div className="flex flex-col space-y-1">
                    <code className="bg-gray-800 text-green-400 px-2 py-1 rounded">MAX_AUTO_RECOVERY_ATTEMPTS=5</code>
                    <span className="text-gray-600 text-xs">Maximum recovery attempts per task</span>
                  </div>
                </div>
              </div>
            </section>

            {/* Related Concepts */}
            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Related Concepts</h2>
              
              <div className="grid md:grid-cols-3 gap-4">
                <Link 
                  href="/docs/core-concepts/goals"
                  className="block p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
                >
                  <Target className="w-5 h-5 text-blue-600 mb-2" />
                  <h3 className="font-semibold text-gray-900 mb-1">Goals</h3>
                  <p className="text-sm text-gray-600">Goal decomposition and tracking</p>
                </Link>

                <Link 
                  href="/docs/core-concepts/agents"
                  className="block p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
                >
                  <Users className="w-5 h-5 text-green-600 mb-2" />
                  <h3 className="font-semibold text-gray-900 mb-1">Agents</h3>
                  <p className="text-sm text-gray-600">AI agent specializations</p>
                </Link>

                <Link 
                  href="/docs/core-concepts/memory"
                  className="block p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
                >
                  <Brain className="w-5 h-5 text-purple-600 mb-2" />
                  <h3 className="font-semibold text-gray-900 mb-1">Memory</h3>
                  <p className="text-sm text-gray-600">Learning from task patterns</p>
                </Link>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  )
}