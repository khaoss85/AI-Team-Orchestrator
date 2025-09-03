'use client'

import React from 'react'
import Link from 'next/link'
import { ArrowLeft, Brain, Users, Shield, Zap, CheckCircle, AlertCircle } from 'lucide-react'

export default function AgentsPage() {
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
            <h1 className="text-3xl font-bold text-gray-900 mb-2">AI Agent System</h1>
            <p className="text-gray-600">Understanding how AI agents work together in teams</p>
          </div>

          <div className="bg-white rounded-xl border p-8">
            {/* Overview */}
            <section className="mb-12">
              <div className="bg-blue-50 rounded-lg p-6 border border-blue-200 mb-6">
                <div className="flex items-center space-x-3">
                  <Brain className="w-6 h-6 text-blue-600" />
                  <div>
                    <h3 className="font-medium text-blue-900">Multi-Agent Architecture</h3>
                    <p className="text-blue-700 text-sm mt-1">Each AI agent has specialized skills, seniority levels, and specific roles</p>
                  </div>
                </div>
              </div>
              
              <p className="text-gray-600 text-lg leading-relaxed mb-6">
                The AI Team Orchestrator uses a sophisticated multi-agent system where different AI agents specialize in specific domains and work together to complete complex projects. Think of it like a real company with different departments and expertise levels.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
                  <h4 className="font-semibold text-blue-900 mb-2">50+ Agent Types</h4>
                  <p className="text-blue-700 text-sm">Marketing, development, analysis, design, and more</p>
                </div>
                <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-6 border border-green-200">
                  <h4 className="font-semibold text-green-900 mb-2">3 Seniority Levels</h4>
                  <p className="text-green-700 text-sm">Junior, Senior, and Expert for different complexity needs</p>
                </div>
                <div className="bg-gradient-to-br from-purple-50 to-violet-50 rounded-lg p-6 border border-purple-200">
                  <h4 className="font-semibold text-purple-900 mb-2">Autonomous Coordination</h4>
                  <p className="text-purple-700 text-sm">Agents collaborate and hand off tasks automatically</p>
                </div>
              </div>
            </section>

            {/* Agent Hierarchy */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Agent Hierarchy</h2>
              
              <div className="space-y-6">
                {/* Director Agent */}
                <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg p-6 border border-purple-200">
                  <div className="flex items-center space-x-4 mb-4">
                    <div className="p-3 bg-purple-100 rounded-lg">
                      <Brain className="w-8 h-8 text-purple-600" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-purple-900">Director Agent</h3>
                      <p className="text-purple-700">The orchestrator and strategic planner</p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-medium text-purple-900 mb-2">Responsibilities:</h4>
                      <ul className="space-y-1 text-purple-700 text-sm">
                        <li>• Analyze project goals and requirements</li>
                        <li>• Propose optimal team composition</li>
                        <li>• Coordinate agent activities and handoffs</li>
                        <li>• Manage project timeline and priorities</li>
                        <li>• Quality assurance and final approval</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium text-purple-900 mb-2">Key Features:</h4>
                      <ul className="space-y-1 text-purple-700 text-sm">
                        <li>• Uses GPT-4 for strategic thinking</li>
                        <li>• Context-aware team selection</li>
                        <li>• Manages budget and resource allocation</li>
                        <li>• Triggers quality gates automatically</li>
                        <li>• Handles escalations and conflicts</li>
                      </ul>
                    </div>
                  </div>
                </div>

                {/* Specialist Agents */}
                <div className="bg-gradient-to-r from-blue-50 to-cyan-50 rounded-lg p-6 border border-blue-200">
                  <div className="flex items-center space-x-4 mb-4">
                    <div className="p-3 bg-blue-100 rounded-lg">
                      <Users className="w-8 h-8 text-blue-600" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-blue-900">Specialist Agents</h3>
                      <p className="text-blue-700">Domain experts with specific skills</p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div className="bg-white rounded-lg p-4 border border-blue-200">
                      <h5 className="font-medium text-blue-900 mb-2">Junior Level</h5>
                      <ul className="space-y-1 text-blue-700 text-sm">
                        <li>• Basic task execution</li>
                        <li>• Data collection and research</li>
                        <li>• Simple content creation</li>
                        <li>• Standard procedures</li>
                      </ul>
                    </div>
                    <div className="bg-white rounded-lg p-4 border border-blue-200">
                      <h5 className="font-medium text-blue-900 mb-2">Senior Level</h5>
                      <ul className="space-y-1 text-blue-700 text-sm">
                        <li>• Complex problem solving</li>
                        <li>• Strategic recommendations</li>
                        <li>• Cross-functional coordination</li>
                        <li>• Quality assurance</li>
                      </ul>
                    </div>
                    <div className="bg-white rounded-lg p-4 border border-blue-200">
                      <h5 className="font-medium text-blue-900 mb-2">Expert Level</h5>
                      <ul className="space-y-1 text-blue-700 text-sm">
                        <li>• Innovation and thought leadership</li>
                        <li>• Complex system design</li>
                        <li>• High-stakes decision making</li>
                        <li>• Mentoring other agents</li>
                      </ul>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg p-4 border border-blue-200">
                    <h4 className="font-medium text-blue-900 mb-3">Common Agent Types:</h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                      <div className="text-blue-700">Marketing Strategist</div>
                      <div className="text-blue-700">Content Creator</div>
                      <div className="text-blue-700">Data Analyst</div>
                      <div className="text-blue-700">Software Developer</div>
                      <div className="text-blue-700">UX Designer</div>
                      <div className="text-blue-700">Market Researcher</div>
                      <div className="text-blue-700">Financial Analyst</div>
                      <div className="text-blue-700">Technical Writer</div>
                    </div>
                  </div>
                </div>

                {/* Quality Gates */}
                <div className="bg-gradient-to-r from-green-50 to-teal-50 rounded-lg p-6 border border-green-200">
                  <div className="flex items-center space-x-4 mb-4">
                    <div className="p-3 bg-green-100 rounded-lg">
                      <Shield className="w-8 h-8 text-green-600" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-green-900">Quality Gate Agents</h3>
                      <p className="text-green-700">Autonomous quality assurance and compliance</p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h4 className="font-medium text-green-900 mb-2">8 Specialized Sub-Agents:</h4>
                      <ul className="space-y-1 text-green-700 text-sm">
                        <li>• <strong>System Architect:</strong> Technical design review</li>
                        <li>• <strong>DB Steward:</strong> Database schema validation</li>
                        <li>• <strong>API Guardian:</strong> Contract compliance</li>
                        <li>• <strong>Principles Guardian:</strong> 15 Pillars compliance</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium text-green-900 mb-2">Additional Guards:</h4>
                      <ul className="space-y-1 text-green-700 text-sm">
                        <li>• <strong>Placeholder Police:</strong> Detect incomplete work</li>
                        <li>• <strong>Frontend Specialist:</strong> UI/UX validation</li>
                        <li>• <strong>Fallback Sentinel:</strong> Test compliance</li>
                        <li>• <strong>Docs Scribe:</strong> Documentation sync</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Agent Collaboration */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">How Agents Work Together</h2>
              
              <div className="space-y-6">
                <div className="bg-gray-50 rounded-lg p-6 border">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Typical Workflow:</h3>
                  <div className="space-y-4">
                    <div className="flex items-start space-x-4">
                      <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white text-sm font-semibold rounded-full flex items-center justify-center">1</div>
                      <div>
                        <h4 className="font-medium text-gray-900">Goal Analysis</h4>
                        <p className="text-gray-600 text-sm">Director analyzes project requirements and identifies needed skills</p>
                      </div>
                    </div>
                    
                    <div className="flex items-start space-x-4">
                      <div className="flex-shrink-0 w-8 h-8 bg-green-600 text-white text-sm font-semibold rounded-full flex items-center justify-center">2</div>
                      <div>
                        <h4 className="font-medium text-gray-900">Team Formation</h4>
                        <p className="text-gray-600 text-sm">Optimal agent team is assembled based on skills, seniority, and budget</p>
                      </div>
                    </div>
                    
                    <div className="flex items-start space-x-4">
                      <div className="flex-shrink-0 w-8 h-8 bg-purple-600 text-white text-sm font-semibold rounded-full flex items-center justify-center">3</div>
                      <div>
                        <h4 className="font-medium text-gray-900">Task Distribution</h4>
                        <p className="text-gray-600 text-sm">Work is divided among agents based on their specializations</p>
                      </div>
                    </div>
                    
                    <div className="flex items-start space-x-4">
                      <div className="flex-shrink-0 w-8 h-8 bg-orange-600 text-white text-sm font-semibold rounded-full flex items-center justify-center">4</div>
                      <div>
                        <h4 className="font-medium text-gray-900">Collaborative Execution</h4>
                        <p className="text-gray-600 text-sm">Agents work together, share insights, and hand off completed work</p>
                      </div>
                    </div>
                    
                    <div className="flex items-start space-x-4">
                      <div className="flex-shrink-0 w-8 h-8 bg-red-600 text-white text-sm font-semibold rounded-full flex items-center justify-center">5</div>
                      <div>
                        <h4 className="font-medium text-gray-900">Quality Assurance</h4>
                        <p className="text-gray-600 text-sm">Quality gates review work and ensure compliance before delivery</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                    <div className="flex items-center space-x-2 mb-2">
                      <CheckCircle className="w-5 h-5 text-blue-600" />
                      <h4 className="font-medium text-blue-900">Agent Benefits</h4>
                    </div>
                    <ul className="space-y-1 text-blue-700 text-sm">
                      <li>• Specialized expertise in each domain</li>
                      <li>• Parallel execution for faster delivery</li>
                      <li>• Quality improvements through collaboration</li>
                      <li>• Cost optimization through right-sizing</li>
                    </ul>
                  </div>

                  <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                    <div className="flex items-center space-x-2 mb-2">
                      <Zap className="w-5 h-5 text-green-600" />
                      <h4 className="font-medium text-green-900">Smart Features</h4>
                    </div>
                    <ul className="space-y-1 text-green-700 text-sm">
                      <li>• AI-driven task assignment</li>
                      <li>• Automatic handoff coordination</li>
                      <li>• Real-time progress sharing</li>
                      <li>• Context preservation across agents</li>
                    </ul>
                  </div>
                </div>
              </div>
            </section>

            {/* Agent Communication */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Agent Communication Patterns</h2>
              
              <div className="bg-yellow-50 rounded-lg p-6 border border-yellow-200 mb-6">
                <div className="flex items-center space-x-3">
                  <AlertCircle className="w-6 h-6 text-yellow-600" />
                  <div>
                    <h3 className="font-medium text-yellow-900">Real-Time Thinking Processes</h3>
                    <p className="text-yellow-700 text-sm mt-1">Watch agents think step-by-step, similar to Claude/o3 reasoning display</p>
                  </div>
                </div>
              </div>
              
              <div className="space-y-4">
                <div className="bg-white rounded-lg p-4 border">
                  <h4 className="font-medium text-gray-900 mb-2">Communication Types:</h4>
                  <ul className="space-y-2 text-gray-600 text-sm">
                    <li>• <strong>Task Handoffs:</strong> Completed work passed to next agent with context</li>
                    <li>• <strong>Collaborative Reviews:</strong> Agents review and improve each other's work</li>
                    <li>• <strong>Status Updates:</strong> Progress shared across the team in real-time</li>
                    <li>• <strong>Quality Feedback:</strong> Improvement suggestions from quality gates</li>
                    <li>• <strong>User Interaction:</strong> Direct communication with human stakeholders</li>
                  </ul>
                </div>

                <div className="bg-white rounded-lg p-4 border">
                  <h4 className="font-medium text-gray-900 mb-2">Coordination Features:</h4>
                  <ul className="space-y-2 text-gray-600 text-sm">
                    <li>• <strong>Workspace Memory:</strong> Shared learning and context across projects</li>
                    <li>• <strong>Dependency Management:</strong> Automatic task ordering based on requirements</li>
                    <li>• <strong>Conflict Resolution:</strong> Director mediates disagreements between agents</li>
                    <li>• <strong>Resource Allocation:</strong> Smart distribution of computing resources</li>
                  </ul>
                </div>
              </div>
            </section>

            {/* Next Steps */}
            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Learn More About Agents</h2>
              <div className="space-y-3">
                <Link 
                  href="/docs/core-concepts/goals"
                  className="flex items-center space-x-3 p-4 border rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all"
                >
                  <div className="p-2 bg-blue-50 rounded-lg">
                    <Brain className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Goal-Driven Planning</h3>
                    <p className="text-gray-600 text-sm">How AI decomposes objectives into agent tasks</p>
                  </div>
                </Link>

                <Link 
                  href="/docs/ai-architecture/quality-gates"
                  className="flex items-center space-x-3 p-4 border rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all"
                >
                  <div className="p-2 bg-green-50 rounded-lg">
                    <Shield className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Quality Gates System</h3>
                    <p className="text-gray-600 text-sm">Deep dive into autonomous quality assurance</p>
                  </div>
                </Link>

                <Link 
                  href="/docs/core-concepts/thinking"
                  className="flex items-center space-x-3 p-4 border rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all"
                >
                  <div className="p-2 bg-purple-50 rounded-lg">
                    <Zap className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Real-Time Thinking</h3>
                    <p className="text-gray-600 text-sm">Claude/o3-style reasoning processes</p>
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