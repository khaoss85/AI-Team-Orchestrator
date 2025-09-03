'use client'

import React from 'react'
import Link from 'next/link'
import { ArrowLeft, Play, ArrowRight, CheckCircle, Users, Brain, Zap, AlertTriangle, Target, Package, RefreshCw } from 'lucide-react'

export default function TaskExecutionFlowPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-5xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <Link 
              href="/docs"
              className="inline-flex items-center text-blue-600 hover:text-blue-800 transition-colors mb-4"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Documentation
            </Link>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Task Execution Flow</h1>
            <p className="text-gray-600">Complete workflow from goal decomposition to deliverable creation</p>
          </div>

          <div className="bg-white rounded-xl border p-8">
            {/* Overview */}
            <section className="mb-12">
              <div className="bg-blue-50 rounded-lg p-6 border border-blue-200 mb-6">
                <div className="flex items-center space-x-3">
                  <Play className="w-6 h-6 text-blue-600" />
                  <div>
                    <h3 className="text-lg font-semibold text-blue-900">End-to-End Execution Pipeline</h3>
                    <p className="text-blue-700 mt-1">
                      From abstract goals to concrete deliverables through AI-orchestrated specialist collaboration, 
                      quality gates, and autonomous recovery mechanisms.
                    </p>
                  </div>
                </div>
              </div>

              <div className="prose prose-lg max-w-none">
                <p>
                  The Task Execution Flow represents the core operational workflow of the AI Team Orchestrator. 
                  This end-to-end process demonstrates how human objectives transform into professional deliverables 
                  through coordinated AI agent collaboration.
                </p>
              </div>
            </section>

            {/* Complete Flow Diagram */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Complete Flow Overview</h2>
              
              <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-8 border border-gray-200">
                <div className="flex flex-col space-y-8">
                  {/* Phase 1: Goal Analysis */}
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      <div className="w-12 h-12 bg-purple-600 rounded-full flex items-center justify-center">
                        <Target className="w-6 h-6 text-white" />
                      </div>
                    </div>
                    <div className="flex-1 bg-white rounded-lg p-4 border border-purple-200">
                      <h3 className="font-semibold text-purple-900 mb-1">Goal Analysis & Decomposition</h3>
                      <p className="text-sm text-purple-700">Director Agent breaks down objectives into actionable tasks</p>
                    </div>
                    <ArrowRight className="w-5 h-5 text-gray-400" />
                  </div>

                  {/* Phase 2: Team Formation */}
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center">
                        <Users className="w-6 h-6 text-white" />
                      </div>
                    </div>
                    <div className="flex-1 bg-white rounded-lg p-4 border border-blue-200">
                      <h3 className="font-semibold text-blue-900 mb-1">AI Team Formation</h3>
                      <p className="text-sm text-blue-700">Semantic matching assigns tasks to specialized agents</p>
                    </div>
                    <ArrowRight className="w-5 h-5 text-gray-400" />
                  </div>

                  {/* Phase 3: Task Execution */}
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      <div className="w-12 h-12 bg-green-600 rounded-full flex items-center justify-center">
                        <Zap className="w-6 h-6 text-white" />
                      </div>
                    </div>
                    <div className="flex-1 bg-white rounded-lg p-4 border border-green-200">
                      <h3 className="font-semibold text-green-900 mb-1">Specialist Execution</h3>
                      <p className="text-sm text-green-700">Agents execute tasks using real tools and domain expertise</p>
                    </div>
                    <ArrowRight className="w-5 h-5 text-gray-400" />
                  </div>

                  {/* Phase 4: Quality Gates */}
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      <div className="w-12 h-12 bg-orange-600 rounded-full flex items-center justify-center">
                        <CheckCircle className="w-6 h-6 text-white" />
                      </div>
                    </div>
                    <div className="flex-1 bg-white rounded-lg p-4 border border-orange-200">
                      <h3 className="font-semibold text-orange-900 mb-1">Quality Assurance</h3>
                      <p className="text-sm text-orange-700">Automated gates validate outputs and ensure standards</p>
                    </div>
                    <ArrowRight className="w-5 h-5 text-gray-400" />
                  </div>

                  {/* Phase 5: Deliverable Creation */}
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      <div className="w-12 h-12 bg-indigo-600 rounded-full flex items-center justify-center">
                        <Package className="w-6 h-6 text-white" />
                      </div>
                    </div>
                    <div className="flex-1 bg-white rounded-lg p-4 border border-indigo-200">
                      <h3 className="font-semibold text-indigo-900 mb-1">Deliverable Generation</h3>
                      <p className="text-sm text-indigo-700">AI transforms outputs into professional business assets</p>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Detailed Phase Breakdown */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Detailed Phase Breakdown</h2>

              <div className="space-y-8">
                {/* Phase 1 */}
                <div className="bg-gradient-to-r from-purple-50 to-purple-100 rounded-lg p-6 border border-purple-200">
                  <div className="flex items-center space-x-3 mb-6">
                    <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center">
                      <span className="text-white font-bold text-sm">1</span>
                    </div>
                    <h3 className="text-xl font-semibold text-purple-900">Goal Analysis & Decomposition</h3>
                    <span className="px-3 py-1 bg-purple-200 text-purple-800 text-xs rounded-full">Director Agent</span>
                  </div>

                  <div className="grid md:grid-cols-3 gap-4 mb-4">
                    <div className="bg-white rounded p-4 border border-purple-300">
                      <h4 className="font-semibold text-purple-900 mb-2">Input Analysis</h4>
                      <ul className="text-sm text-purple-700 space-y-1">
                        <li>• Parse user objectives</li>
                        <li>• Identify domain requirements</li>
                        <li>• Assess complexity level</li>
                        <li>• Extract success criteria</li>
                      </ul>
                    </div>
                    <div className="bg-white rounded p-4 border border-purple-300">
                      <h4 className="font-semibold text-purple-900 mb-2">Task Creation</h4>
                      <ul className="text-sm text-purple-700 space-y-1">
                        <li>• Break down into actionable items</li>
                        <li>• Set priority levels</li>
                        <li>• Define dependencies</li>
                        <li>• Estimate effort requirements</li>
                      </ul>
                    </div>
                    <div className="bg-white rounded p-4 border border-purple-300">
                      <h4 className="font-semibold text-purple-900 mb-2">Planning Output</h4>
                      <ul className="text-sm text-purple-700 space-y-1">
                        <li>• Structured task hierarchy</li>
                        <li>• Skill requirement mapping</li>
                        <li>• Timeline estimation</li>
                        <li>• Resource allocation plan</li>
                      </ul>
                    </div>
                  </div>

                  <div className="bg-purple-100 rounded p-4 border border-purple-300">
                    <h4 className="font-semibold text-purple-900 mb-2">Example Decomposition</h4>
                    <div className="text-sm text-purple-800">
                      <strong>Input:</strong> "Launch a SaaS product for small businesses"<br/>
                      <strong>Output:</strong> 
                      <ul className="mt-2 ml-4 space-y-1">
                        <li>• Market research and competitor analysis (Strategy Specialist)</li>
                        <li>• Create go-to-market strategy (Strategy Specialist)</li>
                        <li>• Develop marketing content and campaigns (Content Specialist)</li>
                        <li>• Design technical architecture (Technical Specialist)</li>
                        <li>• Create launch communication materials (Content Specialist)</li>
                      </ul>
                    </div>
                  </div>
                </div>

                {/* Phase 2 */}
                <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg p-6 border border-blue-200">
                  <div className="flex items-center space-x-3 mb-6">
                    <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                      <span className="text-white font-bold text-sm">2</span>
                    </div>
                    <h3 className="text-xl font-semibold text-blue-900">AI Team Formation</h3>
                    <span className="px-3 py-1 bg-blue-200 text-blue-800 text-xs rounded-full">Semantic Matching</span>
                  </div>

                  <div className="grid md:grid-cols-2 gap-6 mb-4">
                    <div>
                      <h4 className="font-semibold text-blue-900 mb-3">Agent Selection Process</h4>
                      <div className="space-y-3">
                        <div className="flex items-center space-x-3">
                          <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center text-xs font-bold text-blue-600">1</div>
                          <span className="text-sm text-blue-700">Analyze task requirements and context</span>
                        </div>
                        <div className="flex items-center space-x-3">
                          <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center text-xs font-bold text-blue-600">2</div>
                          <span className="text-sm text-blue-700">Match skills to available specialists</span>
                        </div>
                        <div className="flex items-center space-x-3">
                          <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center text-xs font-bold text-blue-600">3</div>
                          <span className="text-sm text-blue-700">Consider agent availability and workload</span>
                        </div>
                        <div className="flex items-center space-x-3">
                          <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center text-xs font-bold text-blue-600">4</div>
                          <span className="text-sm text-blue-700">Optimize for team collaboration patterns</span>
                        </div>
                      </div>
                    </div>

                    <div className="bg-white rounded p-4 border border-blue-300">
                      <h4 className="font-semibold text-blue-900 mb-3">Team Composition API</h4>
                      <div className="bg-gray-900 rounded p-3 text-xs">
                        <pre className="text-green-400 overflow-x-auto">
                          <code>{`{
  "team_members": [
    {
      "agent_id": "strategy_001",
      "role": "Strategy Specialist",
      "seniority": "Expert",
      "specialization": "SaaS GTM",
      "confidence": 0.92
    },
    {
      "agent_id": "content_003", 
      "role": "Content Specialist",
      "seniority": "Senior",
      "specialization": "B2B Marketing",
      "confidence": 0.88
    }
  ]
}`}</code>
                        </pre>
                      </div>
                    </div>
                  </div>

                  <div className="bg-blue-100 rounded p-4 border border-blue-300">
                    <p className="text-sm text-blue-800">
                      <strong>Key Innovation:</strong> AI semantic matching ensures optimal agent-task pairing based on 
                      content analysis, not just keyword matching, resulting in higher success rates and better output quality.
                    </p>
                  </div>
                </div>

                {/* Phase 3 */}
                <div className="bg-gradient-to-r from-green-50 to-green-100 rounded-lg p-6 border border-green-200">
                  <div className="flex items-center space-x-3 mb-6">
                    <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center">
                      <span className="text-white font-bold text-sm">3</span>
                    </div>
                    <h3 className="text-xl font-semibold text-green-900">Specialist Execution</h3>
                    <span className="px-3 py-1 bg-green-200 text-green-800 text-xs rounded-full">Real Tools</span>
                  </div>

                  <div className="grid md:grid-cols-3 gap-4 mb-4">
                    <div className="bg-white rounded p-4 border border-green-300">
                      <h4 className="font-semibold text-green-900 mb-2">Tool Execution</h4>
                      <ul className="text-sm text-green-700 space-y-1">
                        <li>• Web search for research</li>
                        <li>• File system operations</li>
                        <li>• API integrations</li>
                        <li>• Content generation</li>
                      </ul>
                    </div>
                    <div className="bg-white rounded p-4 border border-green-300">
                      <h4 className="font-semibold text-green-900 mb-2">Thinking Process</h4>
                      <ul className="text-sm text-green-700 space-y-1">
                        <li>• Real-time reasoning display</li>
                        <li>• Step-by-step problem solving</li>
                        <li>• Alternative consideration</li>
                        <li>• Decision justification</li>
                      </ul>
                    </div>
                    <div className="bg-white rounded p-4 border border-green-300">
                      <h4 className="font-semibold text-green-900 mb-2">Progress Tracking</h4>
                      <ul className="text-sm text-green-700 space-y-1">
                        <li>• WebSocket status updates</li>
                        <li>• Milestone completion</li>
                        <li>• Resource utilization</li>
                        <li>• Quality metrics</li>
                      </ul>
                    </div>
                  </div>

                  <div className="bg-green-100 rounded p-4 border border-green-300">
                    <h4 className="font-semibold text-green-900 mb-2">Execution Patterns</h4>
                    <div className="grid md:grid-cols-2 gap-4 text-sm text-green-800">
                      <div>
                        <strong>Sequential:</strong> Strategy Specialist creates market analysis → Content Specialist develops messaging based on insights
                      </div>
                      <div>
                        <strong>Parallel:</strong> Content and Technical Specialists work simultaneously while Director coordinates dependencies
                      </div>
                    </div>
                  </div>
                </div>

                {/* Phase 4 */}
                <div className="bg-gradient-to-r from-orange-50 to-orange-100 rounded-lg p-6 border border-orange-200">
                  <div className="flex items-center space-x-3 mb-6">
                    <div className="w-8 h-8 bg-orange-600 rounded-full flex items-center justify-center">
                      <span className="text-white font-bold text-sm">4</span>
                    </div>
                    <h3 className="text-xl font-semibold text-orange-900">Quality Assurance Gates</h3>
                    <span className="px-3 py-1 bg-orange-200 text-orange-800 text-xs rounded-full">Automated</span>
                  </div>

                  <div className="grid md:grid-cols-4 gap-4 mb-4">
                    <div className="bg-white rounded p-4 border border-orange-300 text-center">
                      <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-2">
                        <Brain className="w-4 h-4 text-white" />
                      </div>
                      <h4 className="font-semibold text-orange-900 text-sm mb-1">System Architect</h4>
                      <p className="text-xs text-orange-700">Technical coherence and architecture review</p>
                    </div>
                    <div className="bg-white rounded p-4 border border-orange-300 text-center">
                      <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-2">
                        <CheckCircle className="w-4 h-4 text-white" />
                      </div>
                      <h4 className="font-semibold text-orange-900 text-sm mb-1">Principles Guardian</h4>
                      <p className="text-xs text-orange-700">15 Pillars compliance validation</p>
                    </div>
                    <div className="bg-white rounded p-4 border border-orange-300 text-center">
                      <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center mx-auto mb-2">
                        <AlertTriangle className="w-4 h-4 text-white" />
                      </div>
                      <h4 className="font-semibold text-orange-900 text-sm mb-1">Placeholder Police</h4>
                      <p className="text-xs text-orange-700">Content authenticity and completeness</p>
                    </div>
                    <div className="bg-white rounded p-4 border border-orange-300 text-center">
                      <div className="w-8 h-8 bg-indigo-600 rounded-full flex items-center justify-center mx-auto mb-2">
                        <Zap className="w-4 h-4 text-white" />
                      </div>
                      <h4 className="font-semibold text-orange-900 text-sm mb-1">Docs Scribe</h4>
                      <p className="text-xs text-orange-700">Documentation consistency check</p>
                    </div>
                  </div>

                  <div className="bg-orange-100 rounded p-4 border border-orange-300">
                    <p className="text-sm text-orange-800">
                      <strong>Smart Triggering:</strong> Quality gates use AI to determine when to activate, achieving 94% cost reduction 
                      while maintaining comprehensive coverage. Gates only trigger when needed based on content analysis.
                    </p>
                  </div>
                </div>

                {/* Phase 5 */}
                <div className="bg-gradient-to-r from-indigo-50 to-indigo-100 rounded-lg p-6 border border-indigo-200">
                  <div className="flex items-center space-x-3 mb-6">
                    <div className="w-8 h-8 bg-indigo-600 rounded-full flex items-center justify-center">
                      <span className="text-white font-bold text-sm">5</span>
                    </div>
                    <h3 className="text-xl font-semibold text-indigo-900">Deliverable Generation</h3>
                    <span className="px-3 py-1 bg-indigo-200 text-indigo-800 text-xs rounded-full">Dual Format</span>
                  </div>

                  <div className="grid md:grid-cols-2 gap-6 mb-4">
                    <div>
                      <h4 className="font-semibold text-indigo-900 mb-3">AI Transformation Process</h4>
                      <div className="space-y-3">
                        <div className="flex items-center space-x-3">
                          <div className="w-6 h-6 bg-indigo-100 rounded-full flex items-center justify-center text-xs font-bold text-indigo-600">1</div>
                          <span className="text-sm text-indigo-700">Analyze raw task output structure</span>
                        </div>
                        <div className="flex items-center space-x-3">
                          <div className="w-6 h-6 bg-indigo-100 rounded-full flex items-center justify-center text-xs font-bold text-indigo-600">2</div>
                          <span className="text-sm text-indigo-700">Apply business context and formatting</span>
                        </div>
                        <div className="flex items-center space-x-3">
                          <div className="w-6 h-6 bg-indigo-100 rounded-full flex items-center justify-center text-xs font-bold text-indigo-600">3</div>
                          <span className="text-sm text-indigo-700">Generate professional HTML/Markdown</span>
                        </div>
                        <div className="flex items-center space-x-3">
                          <div className="w-6 h-6 bg-indigo-100 rounded-full flex items-center justify-center text-xs font-bold text-indigo-600">4</div>
                          <span className="text-sm text-indigo-700">Apply confidence scoring and validation</span>
                        </div>
                      </div>
                    </div>

                    <div className="bg-white rounded p-4 border border-indigo-300">
                      <h4 className="font-semibold text-indigo-900 mb-3">Output Quality</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-indigo-700">AI Confidence Average:</span>
                          <span className="font-semibold text-green-600">85%+</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-indigo-700">Transformation Time:</span>
                          <span className="font-semibold text-blue-600">&lt; 1.5s</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-indigo-700">Fallback Reliability:</span>
                          <span className="font-semibold text-purple-600">100%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-indigo-700">Professional Format Rate:</span>
                          <span className="font-semibold text-orange-600">94%</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="bg-indigo-100 rounded p-4 border border-indigo-300">
                    <p className="text-sm text-indigo-800">
                      <strong>Business Value:</strong> Users receive professional business documents, not raw JSON data. 
                      The dual-format architecture ensures both system processing capability and user-friendly presentation.
                    </p>
                  </div>
                </div>
              </div>
            </section>

            {/* Error Handling & Recovery */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <RefreshCw className="w-6 h-6 mr-3 text-indigo-600" />
                Error Handling & Recovery
              </h2>

              <div className="bg-red-50 rounded-lg p-6 border border-red-200 mb-6">
                <div className="flex items-start space-x-3">
                  <AlertTriangle className="w-6 h-6 text-red-600 mt-1" />
                  <div>
                    <h3 className="text-lg font-semibold text-red-900">Autonomous Failure Recovery</h3>
                    <p className="text-red-700 mt-1">
                      When any step in the flow fails, the autonomous recovery system automatically analyzes 
                      the failure and applies contextual recovery strategies without human intervention.
                    </p>
                  </div>
                </div>
              </div>

              <div className="grid md:grid-cols-3 gap-6">
                <div className="bg-yellow-50 rounded-lg p-6 border border-yellow-200">
                  <h4 className="font-semibold text-yellow-900 mb-3">Detection</h4>
                  <ul className="text-sm text-yellow-800 space-y-1">
                    <li>• Real-time execution monitoring</li>
                    <li>• Timeout detection</li>
                    <li>• Quality gate failures</li>
                    <li>• Agent unresponsiveness</li>
                  </ul>
                </div>

                <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
                  <h4 className="font-semibold text-blue-900 mb-3">Analysis</h4>
                  <ul className="text-sm text-blue-800 space-y-1">
                    <li>• AI failure pattern recognition</li>
                    <li>• Context reconstruction</li>
                    <li>• Strategy selection (90%+ confidence)</li>
                    <li>• Resource availability check</li>
                  </ul>
                </div>

                <div className="bg-green-50 rounded-lg p-6 border border-green-200">
                  <h4 className="font-semibold text-green-900 mb-3">Recovery</h4>
                  <ul className="text-sm text-green-800 space-y-1">
                    <li>• Retry with different agent</li>
                    <li>• Task decomposition</li>
                    <li>• Alternative methodology</li>
                    <li>• Fallback deliverable (80% completion)</li>
                  </ul>
                </div>
              </div>
            </section>

            {/* Performance Metrics */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Flow Performance Metrics</h2>

              <div className="grid md:grid-cols-4 gap-6 mb-6">
                <div className="bg-green-50 rounded-lg p-6 text-center border border-green-200">
                  <div className="text-3xl font-bold text-green-900 mb-2">94%</div>
                  <div className="text-sm text-green-700">Cost optimization through smart triggering</div>
                </div>
                <div className="bg-blue-50 rounded-lg p-6 text-center border border-blue-200">
                  <div className="text-3xl font-bold text-blue-900 mb-2">85%</div>
                  <div className="text-sm text-blue-700">Task completion success rate</div>
                </div>
                <div className="bg-purple-50 rounded-lg p-6 text-center border border-purple-200">
                  <div className="text-3xl font-bold text-purple-900 mb-2">&lt; 60s</div>
                  <div className="text-sm text-purple-700">Average failure recovery time</div>
                </div>
                <div className="bg-orange-50 rounded-lg p-6 text-center border border-orange-200">
                  <div className="text-3xl font-bold text-orange-900 mb-2">3x</div>
                  <div className="text-sm text-orange-700">Faster than traditional approaches</div>
                </div>
              </div>
            </section>

            {/* Related Concepts */}
            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Related Concepts</h2>
              
              <div className="grid md:grid-cols-3 gap-4">
                <Link 
                  href="/docs/core-concepts/tasks"
                  className="block p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
                >
                  <CheckCircle className="w-5 h-5 text-blue-600 mb-2" />
                  <h3 className="font-semibold text-gray-900 mb-1">Tasks</h3>
                  <p className="text-sm text-gray-600">Individual task execution details</p>
                </Link>

                <Link 
                  href="/docs/core-concepts/orchestration"
                  className="block p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
                >
                  <Users className="w-5 h-5 text-green-600 mb-2" />
                  <h3 className="font-semibold text-gray-900 mb-1">Orchestration</h3>
                  <p className="text-sm text-gray-600">Agent collaboration patterns</p>
                </Link>

                <Link 
                  href="/docs/core-concepts/recovery"
                  className="block p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
                >
                  <RefreshCw className="w-5 h-5 text-purple-600 mb-2" />
                  <h3 className="font-semibold text-gray-900 mb-1">Recovery</h3>
                  <p className="text-sm text-gray-600">Autonomous failure handling</p>
                </Link>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  )
}