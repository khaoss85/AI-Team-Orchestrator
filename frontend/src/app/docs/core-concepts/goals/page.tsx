'use client'

import React from 'react'
import Link from 'next/link'
import { ArrowLeft, Target, Brain, Zap, CheckCircle, AlertTriangle, Lightbulb } from 'lucide-react'

export default function GoalsPage() {
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
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Goal-Driven Planning</h1>
            <p className="text-gray-600">How AI decomposes objectives into concrete deliverables</p>
          </div>

          <div className="bg-white rounded-xl border p-8">
            {/* Overview */}
            <section className="mb-12">
              <div className="bg-blue-50 rounded-lg p-6 border border-blue-200 mb-6">
                <div className="flex items-center space-x-3">
                  <Target className="w-6 h-6 text-blue-600" />
                  <div>
                    <h3 className="font-medium text-blue-900">AI-Driven Goal Decomposition</h3>
                    <p className="text-blue-700 text-sm mt-1">Transform vague objectives into specific, measurable tasks automatically</p>
                  </div>
                </div>
              </div>
              
              <p className="text-gray-600 text-lg leading-relaxed mb-6">
                The AI Team Orchestrator uses advanced goal decomposition to break down high-level objectives into specific, actionable tasks that specialized AI agents can execute. This process ensures every project delivers concrete, measurable results.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-6 border border-green-200">
                  <h4 className="font-semibold text-green-900 mb-2">Automatic Decomposition</h4>
                  <p className="text-green-700 text-sm">AI analyzes your goals and creates specific sub-objectives</p>
                </div>
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
                  <h4 className="font-semibold text-blue-900 mb-2">Smart Task Assignment</h4>
                  <p className="text-blue-700 text-sm">Each sub-goal matched to appropriate agent skills</p>
                </div>
                <div className="bg-gradient-to-br from-purple-50 to-violet-50 rounded-lg p-6 border border-purple-200">
                  <h4 className="font-semibold text-purple-900 mb-2">Progress Tracking</h4>
                  <p className="text-purple-700 text-sm">Real-time goal completion monitoring and reporting</p>
                </div>
              </div>
            </section>

            {/* Goal Decomposition Process */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">How Goal Decomposition Works</h2>
              
              <div className="space-y-8">
                {/* Step 1 */}
                <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
                  <div className="flex items-center space-x-4 mb-4">
                    <div className="flex-shrink-0 w-10 h-10 bg-blue-600 text-white text-lg font-bold rounded-full flex items-center justify-center">1</div>
                    <div>
                      <h3 className="text-xl font-bold text-blue-900">Goal Analysis</h3>
                      <p className="text-blue-700">AI Director analyzes your high-level objective</p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-medium text-blue-900 mb-2">What the AI looks for:</h4>
                      <ul className="space-y-1 text-blue-700 text-sm">
                        <li>• Target audience and market context</li>
                        <li>• Required deliverable types (documents, strategies, etc.)</li>
                        <li>• Success metrics and measurable outcomes</li>
                        <li>• Timeline and resource constraints</li>
                        <li>• Domain expertise requirements</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium text-blue-900 mb-2">Example Input:</h4>
                      <div className="bg-white rounded-lg p-3 border border-blue-200 text-sm">
                        <p className="text-gray-700">
                          "Create a marketing campaign for our new eco-friendly water bottle targeting millennials and Gen Z consumers interested in sustainability."
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Step 2 */}
                <div className="bg-green-50 rounded-lg p-6 border border-green-200">
                  <div className="flex items-center space-x-4 mb-4">
                    <div className="flex-shrink-0 w-10 h-10 bg-green-600 text-white text-lg font-bold rounded-full flex items-center justify-center">2</div>
                    <div>
                      <h3 className="text-xl font-bold text-green-900">Sub-Goal Creation</h3>
                      <p className="text-green-700">AI creates specific, measurable sub-objectives</p>
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg p-4 border border-green-200">
                    <h4 className="font-medium text-green-900 mb-3">Generated Sub-Goals (Example):</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <div className="flex items-center space-x-2">
                          <CheckCircle className="w-4 h-4 text-green-600" />
                          <span className="text-sm text-green-800">Brand positioning document</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <CheckCircle className="w-4 h-4 text-green-600" />
                          <span className="text-sm text-green-800">Target audience analysis</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <CheckCircle className="w-4 h-4 text-green-600" />
                          <span className="text-sm text-green-800">Content calendar (30 posts)</span>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center space-x-2">
                          <CheckCircle className="w-4 h-4 text-green-600" />
                          <span className="text-sm text-green-800">Email marketing sequence</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <CheckCircle className="w-4 h-4 text-green-600" />
                          <span className="text-sm text-green-800">Influencer outreach strategy</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <CheckCircle className="w-4 h-4 text-green-600" />
                          <span className="text-sm text-green-800">Performance tracking dashboard</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Step 3 */}
                <div className="bg-purple-50 rounded-lg p-6 border border-purple-200">
                  <div className="flex items-center space-x-4 mb-4">
                    <div className="flex-shrink-0 w-10 h-10 bg-purple-600 text-white text-lg font-bold rounded-full flex items-center justify-center">3</div>
                    <div>
                      <h3 className="text-xl font-bold text-purple-900">Agent Assignment</h3>
                      <p className="text-purple-700">Each sub-goal assigned to specialized agents</p>
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg p-4 border border-purple-200">
                    <h4 className="font-medium text-purple-900 mb-3">Agent-Goal Mapping:</h4>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
                        <span className="text-sm text-purple-800 font-medium">Brand positioning document</span>
                        <span className="text-xs text-purple-600 bg-purple-100 px-2 py-1 rounded">Marketing Strategist (Senior)</span>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
                        <span className="text-sm text-purple-800 font-medium">Content calendar (30 posts)</span>
                        <span className="text-xs text-purple-600 bg-purple-100 px-2 py-1 rounded">Content Creator (Expert)</span>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
                        <span className="text-sm text-purple-800 font-medium">Target audience analysis</span>
                        <span className="text-xs text-purple-600 bg-purple-100 px-2 py-1 rounded">Market Researcher (Senior)</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Writing Effective Goals */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Writing Effective Project Goals</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Good Examples */}
                <div className="space-y-6">
                  <h3 className="text-lg font-medium text-green-900 flex items-center">
                    <CheckCircle className="w-5 h-5 mr-2" />
                    ✅ Effective Goals
                  </h3>
                  
                  <div className="space-y-4">
                    <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                      <h4 className="font-medium text-green-900 mb-2">Marketing Campaign</h4>
                      <p className="text-green-700 text-sm">
                        "Create a comprehensive marketing campaign for our new eco-friendly water bottle including brand positioning, target audience analysis, content calendar with 30 social media posts, email sequence, influencer outreach strategy, and performance tracking dashboard targeting millennials and Gen Z."
                      </p>
                    </div>
                    
                    <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                      <h4 className="font-medium text-green-900 mb-2">Investment Strategy</h4>
                      <p className="text-green-700 text-sm">
                        "Develop a personalized investment portfolio allocation with specific stock picks and percentage allocations, Excel tracker with automated P&L calculation, monthly screening reports, risk assessment, and 12-month investment calendar for a €50,000 portfolio."
                      </p>
                    </div>
                  </div>
                </div>

                {/* Bad Examples */}
                <div className="space-y-6">
                  <h3 className="text-lg font-medium text-red-900 flex items-center">
                    <AlertTriangle className="w-5 h-5 mr-2" />
                    ❌ Vague Goals
                  </h3>
                  
                  <div className="space-y-4">
                    <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                      <h4 className="font-medium text-red-900 mb-2">Too Vague</h4>
                      <p className="text-red-700 text-sm mb-2">
                        "Help me with marketing"
                      </p>
                      <p className="text-red-600 text-xs">
                        Missing: target audience, deliverables, context, success metrics
                      </p>
                    </div>
                    
                    <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                      <h4 className="font-medium text-red-900 mb-2">Too Generic</h4>
                      <p className="text-red-700 text-sm mb-2">
                        "Create a business plan"
                      </p>
                      <p className="text-red-600 text-xs">
                        Missing: industry, business type, specific sections needed, audience
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Goal Writing Tips */}
              <div className="mt-8 bg-blue-50 rounded-lg p-6 border border-blue-200">
                <div className="flex items-center space-x-3 mb-4">
                  <Lightbulb className="w-6 h-6 text-blue-600" />
                  <h3 className="font-medium text-blue-900">Goal Writing Best Practices</h3>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-medium text-blue-900 mb-2">Include Context:</h4>
                    <ul className="space-y-1 text-blue-700 text-sm">
                      <li>• Industry or business domain</li>
                      <li>• Target audience or users</li>
                      <li>• Current situation or challenges</li>
                      <li>• Timeline or deadlines</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-medium text-blue-900 mb-2">Specify Deliverables:</h4>
                    <ul className="space-y-1 text-blue-700 text-sm">
                      <li>• Documents or reports needed</li>
                      <li>• Tools or templates to create</li>
                      <li>• Analysis or research required</li>
                      <li>• Implementation plans or strategies</li>
                    </ul>
                  </div>
                </div>
              </div>
            </section>

            {/* Goal Lifecycle */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Goal Lifecycle Management</h2>
              
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="bg-blue-50 rounded-lg p-4 border border-blue-200 text-center">
                    <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto mb-2">
                      <Target className="w-6 h-6" />
                    </div>
                    <h4 className="font-medium text-blue-900 mb-1">Created</h4>
                    <p className="text-blue-700 text-xs">Goal decomposed into sub-objectives</p>
                  </div>
                  
                  <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200 text-center">
                    <div className="w-12 h-12 bg-yellow-600 text-white rounded-full flex items-center justify-center mx-auto mb-2">
                      <Brain className="w-6 h-6" />
                    </div>
                    <h4 className="font-medium text-yellow-900 mb-1">In Progress</h4>
                    <p className="text-yellow-700 text-xs">Agents working on assigned tasks</p>
                  </div>
                  
                  <div className="bg-orange-50 rounded-lg p-4 border border-orange-200 text-center">
                    <div className="w-12 h-12 bg-orange-600 text-white rounded-full flex items-center justify-center mx-auto mb-2">
                      <Zap className="w-6 h-6" />
                    </div>
                    <h4 className="font-medium text-orange-900 mb-1">Under Review</h4>
                    <p className="text-orange-700 text-xs">Quality gates validating deliverables</p>
                  </div>
                  
                  <div className="bg-green-50 rounded-lg p-4 border border-green-200 text-center">
                    <div className="w-12 h-12 bg-green-600 text-white rounded-full flex items-center justify-center mx-auto mb-2">
                      <CheckCircle className="w-6 h-6" />
                    </div>
                    <h4 className="font-medium text-green-900 mb-1">Completed</h4>
                    <p className="text-green-700 text-xs">All deliverables ready for use</p>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-lg p-6 border">
                  <h4 className="font-medium text-gray-900 mb-4">Real-time Goal Tracking Features:</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h5 className="font-medium text-gray-900 mb-2">Progress Monitoring:</h5>
                      <ul className="space-y-1 text-gray-600 text-sm">
                        <li>• Percentage completion tracking</li>
                        <li>• Task dependency visualization</li>
                        <li>• Agent activity status</li>
                        <li>• Deliverable creation milestones</li>
                      </ul>
                    </div>
                    <div>
                      <h5 className="font-medium text-gray-900 mb-2">Quality Assurance:</h5>
                      <ul className="space-y-1 text-gray-600 text-sm">
                        <li>• Automatic quality gate validation</li>
                        <li>• Human feedback integration</li>
                        <li>• Continuous improvement loops</li>
                        <li>• Final approval checkpoints</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Advanced Features */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Advanced Goal Features</h2>
              
              <div className="space-y-6">
                <div className="bg-purple-50 rounded-lg p-6 border border-purple-200">
                  <h3 className="font-medium text-purple-900 mb-3 flex items-center">
                    <Brain className="w-5 h-5 mr-2" />
                    AI Goal Matcher
                  </h3>
                  <p className="text-purple-700 text-sm mb-4">
                    Uses semantic analysis to match deliverables with the most appropriate goals, ensuring perfect organization and progress tracking.
                  </p>
                  <div className="bg-white rounded-lg p-3 border border-purple-200">
                    <div className="text-xs text-purple-600 mb-1">Example:</div>
                    <p className="text-purple-800 text-sm">
                      Email sequence deliverable → Marketing Campaign goal (90% confidence)
                    </p>
                  </div>
                </div>

                <div className="bg-green-50 rounded-lg p-6 border border-green-200">
                  <h3 className="font-medium text-green-900 mb-3 flex items-center">
                    <Target className="w-5 h-5 mr-2" />
                    Workspace Memory Integration
                  </h3>
                  <p className="text-green-700 text-sm mb-4">
                    The system learns from successful goal patterns and applies this knowledge to future projects, improving decomposition quality over time.
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div className="bg-white rounded-lg p-3 border border-green-200">
                      <div className="text-xs text-green-600 mb-1">Success Patterns:</div>
                      <p className="text-green-800 text-sm">Remembers what worked for similar goals</p>
                    </div>
                    <div className="bg-white rounded-lg p-3 border border-green-200">
                      <div className="text-xs text-green-600 mb-1">Failure Lessons:</div>
                      <p className="text-green-800 text-sm">Avoids patterns that led to incomplete deliverables</p>
                    </div>
                  </div>
                </div>

                <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
                  <h3 className="font-medium text-blue-900 mb-3 flex items-center">
                    <Zap className="w-5 h-5 mr-2" />
                    Autonomous Recovery
                  </h3>
                  <p className="text-blue-700 text-sm mb-4">
                    When goals encounter issues, the system automatically attempts recovery strategies without human intervention.
                  </p>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                      <span className="text-blue-800 text-sm">Retry failed tasks with different agents</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                      <span className="text-blue-800 text-sm">Decompose complex goals into simpler sub-goals</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                      <span className="text-blue-800 text-sm">Alternative approach generation</span>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Next Steps */}
            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Learn More</h2>
              <div className="space-y-3">
                <Link 
                  href="/docs/core-concepts/agents"
                  className="flex items-center space-x-3 p-4 border rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all"
                >
                  <div className="p-2 bg-blue-50 rounded-lg">
                    <Brain className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">AI Agent System</h3>
                    <p className="text-gray-600 text-sm">How agents execute goal-driven tasks</p>
                  </div>
                </Link>

                <Link 
                  href="/docs/core-concepts/memory"
                  className="flex items-center space-x-3 p-4 border rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all"
                >
                  <div className="p-2 bg-green-50 rounded-lg">
                    <Target className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Workspace Memory</h3>
                    <p className="text-gray-600 text-sm">How the system learns and improves</p>
                  </div>
                </Link>

                <Link 
                  href="/docs/getting-started/first-project"
                  className="flex items-center space-x-3 p-4 border rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all"
                >
                  <div className="p-2 bg-purple-50 rounded-lg">
                    <Zap className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Try It Yourself</h3>
                    <p className="text-gray-600 text-sm">Create your first goal-driven project</p>
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