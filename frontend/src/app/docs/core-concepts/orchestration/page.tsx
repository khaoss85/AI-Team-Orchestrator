'use client'

import React from 'react'
import Link from 'next/link'
import { ArrowLeft, Users, Crown, Shield, Code, FileText, Zap, CheckCircle, AlertTriangle, ArrowRight, Brain } from 'lucide-react'

export default function OrchestrationPage() {
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
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Sub-Agent Orchestration</h1>
            <p className="text-gray-600">Director-led team coordination and specialized agent collaboration</p>
          </div>

          <div className="bg-white rounded-xl border p-8">
            {/* Overview */}
            <section className="mb-12">
              <div className="bg-purple-50 rounded-lg p-6 border border-purple-200 mb-6">
                <div className="flex items-center space-x-3">
                  <Crown className="w-6 h-6 text-purple-600" />
                  <div>
                    <h3 className="text-lg font-semibold text-purple-900">Director-Led Architecture</h3>
                    <p className="text-purple-700 mt-1">
                      A hierarchical system where a Director Agent analyzes projects and orchestrates specialized 
                      agents to work collaboratively, each contributing their expertise to achieve complex objectives.
                    </p>
                  </div>
                </div>
              </div>

              <div className="prose prose-lg max-w-none">
                <p>
                  Sub-Agent Orchestration enables the system to tackle complex, multi-faceted projects by breaking 
                  them down into specialized domains and assigning appropriate expert agents. This creates a 
                  collaborative AI team that mirrors how human expert teams work together.
                </p>
              </div>
            </section>

            {/* Orchestration Hierarchy */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <Users className="w-6 h-6 mr-3 text-indigo-600" />
                Orchestration Hierarchy
              </h2>

              <div className="space-y-8">
                {/* Director Level */}
                <div className="bg-gradient-to-r from-purple-50 to-purple-100 rounded-lg p-6 border border-purple-200">
                  <div className="flex items-center space-x-4 mb-4">
                    <div className="w-12 h-12 bg-purple-600 rounded-full flex items-center justify-center">
                      <Crown className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold text-purple-900">Director Agent</h3>
                      <p className="text-purple-700">Strategic coordinator and team composer</p>
                    </div>
                  </div>
                  
                  <div className="grid md:grid-cols-3 gap-4 text-sm">
                    <div className="bg-white rounded p-4 border border-purple-300">
                      <h4 className="font-semibold text-purple-900 mb-2">Project Analysis</h4>
                      <ul className="text-purple-700 space-y-1">
                        <li>• Requirement breakdown</li>
                        <li>• Complexity assessment</li>
                        <li>• Skill requirement mapping</li>
                      </ul>
                    </div>
                    <div className="bg-white rounded p-4 border border-purple-300">
                      <h4 className="font-semibold text-purple-900 mb-2">Team Composition</h4>
                      <ul className="text-purple-700 space-y-1">
                        <li>• Agent specialization matching</li>
                        <li>• Workload balancing</li>
                        <li>• Collaboration optimization</li>
                      </ul>
                    </div>
                    <div className="bg-white rounded p-4 border border-purple-300">
                      <h4 className="font-semibold text-purple-900 mb-2">Quality Oversight</h4>
                      <ul className="text-purple-700 space-y-1">
                        <li>• Progress monitoring</li>
                        <li>• Quality gate enforcement</li>
                        <li>• Strategic adjustments</li>
                      </ul>
                    </div>
                  </div>
                </div>

                {/* Specialist Level */}
                <div className="relative">
                  <div className="absolute left-6 top-0 w-0.5 h-full bg-gray-300"></div>
                  
                  <div className="grid md:grid-cols-2 gap-6 pl-16">
                    <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-6 border border-blue-200 relative">
                      <div className="absolute -left-16 top-6 w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center">
                        <FileText className="w-6 h-6 text-white" />
                      </div>
                      <h3 className="text-lg font-semibold text-blue-900 mb-2">Content Specialists</h3>
                      <p className="text-blue-800 text-sm mb-3">Expert-level content creation and strategy</p>
                      <ul className="text-sm text-blue-700 space-y-1">
                        <li>• Marketing copy and campaigns</li>
                        <li>• Blog posts and articles</li>
                        <li>• Email sequences</li>
                        <li>• Social media strategies</li>
                      </ul>
                    </div>

                    <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-6 border border-green-200 relative">
                      <div className="absolute -left-16 top-6 w-12 h-12 bg-green-600 rounded-full flex items-center justify-center">
                        <Code className="w-6 h-6 text-white" />
                      </div>
                      <h3 className="text-lg font-semibold text-green-900 mb-2">Technical Specialists</h3>
                      <p className="text-green-800 text-sm mb-3">Senior-level technical implementation</p>
                      <ul className="text-sm text-green-700 space-y-1">
                        <li>• System architecture design</li>
                        <li>• Code implementation</li>
                        <li>• API integrations</li>
                        <li>• Technical documentation</li>
                      </ul>
                    </div>

                    <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg p-6 border border-orange-200 relative">
                      <div className="absolute -left-16 top-6 w-12 h-12 bg-orange-600 rounded-full flex items-center justify-center">
                        <Shield className="w-6 h-6 text-white" />
                      </div>
                      <h3 className="text-lg font-semibold text-orange-900 mb-2">Strategy Specialists</h3>
                      <p className="text-orange-800 text-sm mb-3">Expert business and market strategy</p>
                      <ul className="text-sm text-orange-700 space-y-1">
                        <li>• Market analysis</li>
                        <li>• Competitive intelligence</li>
                        <li>• Business planning</li>
                        <li>• Go-to-market strategies</li>
                      </ul>
                    </div>

                    <div className="bg-gradient-to-br from-indigo-50 to-indigo-100 rounded-lg p-6 border border-indigo-200 relative">
                      <div className="absolute -left-16 top-6 w-12 h-12 bg-indigo-600 rounded-full flex items-center justify-center">
                        <Zap className="w-6 h-6 text-white" />
                      </div>
                      <h3 className="text-lg font-semibold text-indigo-900 mb-2">Operations Specialists</h3>
                      <p className="text-indigo-800 text-sm mb-3">Process optimization and automation</p>
                      <ul className="text-sm text-indigo-700 space-y-1">
                        <li>• Workflow design</li>
                        <li>• Process automation</li>
                        <li>• Quality assurance</li>
                        <li>• Performance optimization</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Collaboration Patterns */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <ArrowRight className="w-6 h-6 mr-3 text-indigo-600" />
                Collaboration Patterns
              </h2>

              <div className="space-y-6">
                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
                  <div className="flex items-center space-x-3 mb-4">
                    <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                      <span className="text-white font-bold text-sm">1</span>
                    </div>
                    <h3 className="font-semibold text-blue-900">Sequential Specialization</h3>
                  </div>
                  <p className="text-blue-800 text-sm mb-3">
                    Agents work in sequence, each building upon the previous specialist's output.
                  </p>
                  <div className="bg-white rounded p-4 border border-blue-300">
                    <p className="text-xs text-blue-700">
                      <strong>Example:</strong> Strategy Specialist creates market analysis → Content Specialist develops messaging → Technical Specialist implements solution
                    </p>
                  </div>
                </div>

                <div className="bg-gradient-to-r from-green-50 to-teal-50 rounded-lg p-6 border border-green-200">
                  <div className="flex items-center space-x-3 mb-4">
                    <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center">
                      <span className="text-white font-bold text-sm">2</span>
                    </div>
                    <h3 className="font-semibold text-green-900">Parallel Collaboration</h3>
                  </div>
                  <p className="text-green-800 text-sm mb-3">
                    Multiple specialists work simultaneously on different aspects of the same project.
                  </p>
                  <div className="bg-white rounded p-4 border border-green-300">
                    <p className="text-xs text-green-700">
                      <strong>Example:</strong> Content Specialist writes copy while Technical Specialist builds infrastructure, coordinated by Director
                    </p>
                  </div>
                </div>

                <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg p-6 border border-purple-200">
                  <div className="flex items-center space-x-3 mb-4">
                    <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center">
                      <span className="text-white font-bold text-sm">3</span>
                    </div>
                    <h3 className="font-semibold text-purple-900">Cross-Pollination</h3>
                  </div>
                  <p className="text-purple-800 text-sm mb-3">
                    Specialists share insights and validate each other's work across domains.
                  </p>
                  <div className="bg-white rounded p-4 border border-purple-300">
                    <p className="text-xs text-purple-700">
                      <strong>Example:</strong> Technical Specialist reviews strategy for feasibility while Strategy Specialist validates technical approach for market alignment
                    </p>
                  </div>
                </div>
              </div>
            </section>

            {/* AI-Driven Team Formation */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <Brain className="w-6 h-6 mr-3 text-indigo-600" />
                AI-Driven Team Formation
              </h2>

              <div className="bg-yellow-50 rounded-lg p-6 border border-yellow-200 mb-6">
                <div className="flex items-start space-x-3">
                  <AlertTriangle className="w-6 h-6 text-yellow-600 mt-1" />
                  <div>
                    <h3 className="text-lg font-semibold text-yellow-900">Dynamic Team Composition</h3>
                    <p className="text-yellow-700 mt-1">
                      The Director Agent uses AI analysis to determine optimal team composition based on project 
                      requirements, agent availability, and historical performance patterns.
                    </p>
                  </div>
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h4 className="font-semibold text-gray-900">Team Formation Factors</h4>
                  <div className="space-y-3">
                    <div className="flex items-start space-x-3">
                      <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
                      <div>
                        <div className="font-semibold text-gray-800">Skill Requirements</div>
                        <p className="text-sm text-gray-600">AI maps project needs to agent specializations</p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <CheckCircle className="w-5 h-5 text-blue-600 mt-0.5" />
                      <div>
                        <div className="font-semibold text-gray-800">Workload Balance</div>
                        <p className="text-sm text-gray-600">Distributes tasks to prevent bottlenecks</p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <CheckCircle className="w-5 h-5 text-purple-600 mt-0.5" />
                      <div>
                        <div className="font-semibold text-gray-800">Historical Performance</div>
                        <p className="text-sm text-gray-600">Learns from past collaboration patterns</p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <CheckCircle className="w-5 h-5 text-orange-600 mt-0.5" />
                      <div>
                        <div className="font-semibold text-gray-800">Domain Expertise</div>
                        <p className="text-sm text-gray-600">Matches industry knowledge to project context</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-lg p-6">
                  <h4 className="font-semibold text-gray-900 mb-4">Team Composition API</h4>
                  <div className="bg-gray-900 rounded p-4 text-sm">
                    <pre className="text-green-400 overflow-x-auto">
                      <code>{`POST /api/director/proposal
{
  "workspace_goal": "Launch SaaS product",
  "complexity": "high",
  "timeline": "6 weeks"
}

Response:
{
  "team_members": [
    {
      "role": "Strategy Specialist",
      "seniority": "Expert",
      "specialization": "SaaS GTM"
    },
    {
      "role": "Content Specialist", 
      "seniority": "Senior",
      "specialization": "B2B Marketing"
    }
  ]
}`}</code>
                    </pre>
                  </div>
                </div>
              </div>
            </section>

            {/* Quality Gates Integration */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Quality Gates Integration</h2>

              <div className="bg-red-50 rounded-lg p-6 border border-red-200 mb-6">
                <div className="flex items-start space-x-3">
                  <Shield className="w-6 h-6 text-red-600 mt-1" />
                  <div>
                    <h3 className="text-lg font-semibold text-red-900">Automated Quality Enforcement</h3>
                    <p className="text-red-700 mt-1">
                      Specialized quality gate agents automatically review all specialist outputs, ensuring 
                      consistency, completeness, and adherence to best practices before final delivery.
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div className="grid md:grid-cols-4 gap-4">
                  <div className="bg-blue-50 rounded-lg p-4 border border-blue-200 text-center">
                    <Shield className="w-6 h-6 text-blue-600 mx-auto mb-2" />
                    <h4 className="font-semibold text-blue-900 text-sm">System Architect</h4>
                    <p className="text-xs text-blue-700">Technical coherence</p>
                  </div>
                  <div className="bg-green-50 rounded-lg p-4 border border-green-200 text-center">
                    <FileText className="w-6 h-6 text-green-600 mx-auto mb-2" />
                    <h4 className="font-semibold text-green-900 text-sm">Docs Scribe</h4>
                    <p className="text-xs text-green-700">Documentation sync</p>
                  </div>
                  <div className="bg-purple-50 rounded-lg p-4 border border-purple-200 text-center">
                    <CheckCircle className="w-6 h-6 text-purple-600 mx-auto mb-2" />
                    <h4 className="font-semibold text-purple-900 text-sm">Principles Guardian</h4>
                    <p className="text-xs text-purple-700">15 Pillars compliance</p>
                  </div>
                  <div className="bg-orange-50 rounded-lg p-4 border border-orange-200 text-center">
                    <AlertTriangle className="w-6 h-6 text-orange-600 mx-auto mb-2" />
                    <h4 className="font-semibold text-orange-900 text-sm">Placeholder Police</h4>
                    <p className="text-xs text-orange-700">Content authenticity</p>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-lg p-6">
                  <h4 className="font-semibold text-gray-900 mb-3">Quality Gate Workflow</h4>
                  <div className="flex items-center justify-between text-sm">
                    <div className="text-center">
                      <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center mb-2">
                        <span className="text-white font-bold text-xs">1</span>
                      </div>
                      <p className="text-gray-600">Specialist completes task</p>
                    </div>
                    <ArrowRight className="w-4 h-4 text-gray-400" />
                    <div className="text-center">
                      <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center mb-2">
                        <span className="text-white font-bold text-xs">2</span>
                      </div>
                      <p className="text-gray-600">Quality gates auto-trigger</p>
                    </div>
                    <ArrowRight className="w-4 h-4 text-gray-400" />
                    <div className="text-center">
                      <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center mb-2">
                        <span className="text-white font-bold text-xs">3</span>
                      </div>
                      <p className="text-gray-600">Director approves delivery</p>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Performance Metrics */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Performance Metrics</h2>

              <div className="grid md:grid-cols-3 gap-6 mb-6">
                <div className="bg-green-50 rounded-lg p-6 text-center border border-green-200">
                  <div className="text-3xl font-bold text-green-900 mb-2">94%</div>
                  <div className="text-sm text-green-700">Cost reduction through smart triggering</div>
                </div>
                <div className="bg-blue-50 rounded-lg p-6 text-center border border-blue-200">
                  <div className="text-3xl font-bold text-blue-900 mb-2">3x</div>
                  <div className="text-sm text-blue-700">Faster project completion</div>
                </div>
                <div className="bg-purple-50 rounded-lg p-6 text-center border border-purple-200">
                  <div className="text-3xl font-bold text-purple-900 mb-2">85%</div>
                  <div className="text-sm text-purple-700">Quality gate pass rate</div>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-6">
                <h4 className="font-semibold text-gray-900 mb-4">Orchestration Benefits</h4>
                <div className="grid md:grid-cols-2 gap-6 text-sm text-gray-600">
                  <div>
                    <h5 className="font-semibold text-gray-800 mb-2">Efficiency Gains</h5>
                    <ul className="space-y-1">
                      <li>• Parallel task execution</li>
                      <li>• Specialized expertise application</li>
                      <li>• Reduced rework through quality gates</li>
                      <li>• Optimal resource allocation</li>
                    </ul>
                  </div>
                  <div>
                    <h5 className="font-semibold text-gray-800 mb-2">Quality Improvements</h5>
                    <ul className="space-y-1">
                      <li>• Expert-level domain knowledge</li>
                      <li>• Cross-domain validation</li>
                      <li>• Consistent standards enforcement</li>
                      <li>• Continuous learning from outcomes</li>
                    </ul>
                  </div>
                </div>
              </div>
            </section>

            {/* Configuration */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Configuration</h2>

              <div className="bg-gray-100 rounded-lg p-6">
                <h3 className="font-semibold text-gray-900 mb-4">Environment Variables</h3>
                <div className="space-y-3 text-sm">
                  <div className="flex flex-col space-y-1">
                    <code className="bg-gray-800 text-green-400 px-2 py-1 rounded">ENABLE_SUB_AGENT_ORCHESTRATION=true</code>
                    <span className="text-gray-600 text-xs">Enable the orchestration system</span>
                  </div>
                  <div className="flex flex-col space-y-1">
                    <code className="bg-gray-800 text-green-400 px-2 py-1 rounded">SUB_AGENT_MAX_CONCURRENT_AGENTS=5</code>
                    <span className="text-gray-600 text-xs">Maximum agents per task</span>
                  </div>
                  <div className="flex flex-col space-y-1">
                    <code className="bg-gray-800 text-green-400 px-2 py-1 rounded">SUB_AGENT_PERFORMANCE_TRACKING=true</code>
                    <span className="text-gray-600 text-xs">Enable performance metrics</span>
                  </div>
                  <div className="flex flex-col space-y-1">
                    <code className="bg-gray-800 text-green-400 px-2 py-1 rounded">ENABLE_AI_AGENT_MATCHING=true</code>
                    <span className="text-gray-600 text-xs">AI-driven agent-task matching</span>
                  </div>
                </div>
              </div>
            </section>

            {/* Related Concepts */}
            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Related Concepts</h2>
              
              <div className="grid md:grid-cols-3 gap-4">
                <Link 
                  href="/docs/core-concepts/agents"
                  className="block p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
                >
                  <Users className="w-5 h-5 text-blue-600 mb-2" />
                  <h3 className="font-semibold text-gray-900 mb-1">Agents</h3>
                  <p className="text-sm text-gray-600">Individual agent specializations</p>
                </Link>

                <Link 
                  href="/docs/ai-architecture/quality-gates"
                  className="block p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
                >
                  <Shield className="w-5 h-5 text-green-600 mb-2" />
                  <h3 className="font-semibold text-gray-900 mb-1">Quality Gates</h3>
                  <p className="text-sm text-gray-600">Automated quality assurance</p>
                </Link>

                <Link 
                  href="/docs/core-concepts/tasks"
                  className="block p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
                >
                  <CheckCircle className="w-5 h-5 text-purple-600 mb-2" />
                  <h3 className="font-semibold text-gray-900 mb-1">Tasks</h3>
                  <p className="text-sm text-gray-600">Task execution pipeline</p>
                </Link>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  )
}