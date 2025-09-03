'use client'

import React from 'react'
import Link from 'next/link'
import { ArrowLeft, Play, Users, Target, CheckCircle, MessageSquare, Zap } from 'lucide-react'

export default function FirstProjectPage() {
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
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Your First Project</h1>
            <p className="text-gray-600">Create and run your first AI team project in minutes</p>
          </div>

          <div className="bg-white rounded-xl border p-8">
            {/* Introduction */}
            <section className="mb-12">
              <div className="bg-blue-50 rounded-lg p-6 border border-blue-200 mb-6">
                <div className="flex items-center space-x-3">
                  <Zap className="w-6 h-6 text-blue-600" />
                  <div>
                    <h3 className="font-medium text-blue-900">What you'll learn</h3>
                    <p className="text-blue-700 text-sm mt-1">How to create a project, set goals, and watch your AI team work together</p>
                  </div>
                </div>
              </div>
              
              <p className="text-gray-600 text-lg leading-relaxed">
                In this guide, we'll walk through creating your first AI team project. You'll see how the Director agent analyzes your goals, assembles a specialized team, and coordinates their work to deliver concrete results.
              </p>
            </section>

            {/* Step 1: Access the Platform */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4 flex items-center">
                <span className="inline-flex items-center justify-center w-8 h-8 bg-blue-600 text-white text-sm font-semibold rounded-full mr-3">1</span>
                Access the Platform
              </h2>
              <div className="space-y-4">
                <p className="text-gray-600">
                  With your installation complete, navigate to <code className="bg-gray-100 px-2 py-1 rounded">http://localhost:3000</code> in your browser.
                </p>
                <div className="bg-gray-50 rounded-lg p-4 border">
                  <p className="text-sm text-gray-700">
                    <strong>💡 Tip:</strong> You should see the main workspace with "New Project" and "My Projects" options.
                  </p>
                </div>
              </div>
            </section>

            {/* Step 2: Create a New Project */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4 flex items-center">
                <span className="inline-flex items-center justify-center w-8 h-8 bg-blue-600 text-white text-sm font-semibold rounded-full mr-3">2</span>
                Create a New Project
              </h2>
              
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2 flex items-center">
                    <MessageSquare className="w-5 h-5 text-blue-600 mr-2" />
                    Click "New Project"
                  </h3>
                  <p className="text-gray-600 mb-4">This will open the project creation form where you'll define your goals.</p>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Fill in Project Details</h3>
                  <div className="space-y-4">
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h4 className="font-medium text-gray-900 mb-2">Example Project</h4>
                      <div className="space-y-2 text-sm">
                        <p><strong>Name:</strong> Marketing Campaign for New Product Launch</p>
                        <p><strong>Description:</strong> Create a comprehensive marketing strategy for our new eco-friendly water bottle</p>
                        <p><strong>Goal:</strong> Develop a complete marketing campaign including brand positioning, target audience analysis, content calendar with 30 social media posts, email sequence for launch week, influencer outreach strategy, and performance tracking dashboard. The campaign should focus on sustainability messaging and target millennials and Gen Z consumers interested in eco-friendly lifestyle products.</p>
                        <p><strong>Budget:</strong> €1,500</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                  <h4 className="font-medium text-blue-900 mb-2">Goal Writing Tips</h4>
                  <ul className="space-y-1 text-blue-700 text-sm">
                    <li>• Be specific about deliverables you want</li>
                    <li>• Include context about your business/industry</li>
                    <li>• Mention target audience or use cases</li>
                    <li>• Don't worry about being too detailed - the AI will understand!</li>
                  </ul>
                </div>
              </div>
            </section>

            {/* Step 3: Team Assembly */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4 flex items-center">
                <span className="inline-flex items-center justify-center w-8 h-8 bg-green-600 text-white text-sm font-semibold rounded-full mr-3">3</span>
                Watch Your AI Team Assemble
              </h2>
              
              <div className="space-y-6">
                <p className="text-gray-600">
                  After clicking "Create Project", you'll be redirected to the team configuration page where the Director agent will:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                    <div className="flex items-center space-x-2 mb-2">
                      <Target className="w-5 h-5 text-blue-600" />
                      <h4 className="font-medium text-blue-900">Analyze Goals</h4>
                    </div>
                    <p className="text-blue-700 text-sm">Break down your objectives into specific, measurable tasks</p>
                  </div>

                  <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                    <div className="flex items-center space-x-2 mb-2">
                      <Users className="w-5 h-5 text-green-600" />
                      <h4 className="font-medium text-green-900">Assemble Team</h4>
                    </div>
                    <p className="text-green-700 text-sm">Select specialized agents based on required skills and seniority</p>
                  </div>

                  <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                    <div className="flex items-center space-x-2 mb-2">
                      <Play className="w-5 h-5 text-purple-600" />
                      <h4 className="font-medium text-purple-900">Start Execution</h4>
                    </div>
                    <p className="text-purple-700 text-sm">Coordinate agent work and manage task dependencies</p>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-lg p-4 border">
                  <h4 className="font-medium text-gray-900 mb-2">Expected Team for Marketing Campaign:</h4>
                  <div className="space-y-2 text-sm text-gray-700">
                    <p>• <strong>Marketing Strategist (Senior):</strong> Brand positioning and campaign strategy</p>
                    <p>• <strong>Content Creator (Expert):</strong> Social media posts and email sequences</p>
                    <p>• <strong>Market Researcher (Senior):</strong> Target audience analysis</p>
                    <p>• <strong>Data Analyst (Junior):</strong> Performance tracking dashboard</p>
                  </div>
                </div>
              </div>
            </section>

            {/* Step 4: Monitor Progress */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4 flex items-center">
                <span className="inline-flex items-center justify-center w-8 h-8 bg-purple-600 text-white text-sm font-semibold rounded-full mr-3">4</span>
                Monitor Your AI Team at Work
              </h2>
              
              <div className="space-y-6">
                <p className="text-gray-600">
                  Once you approve the team proposal, you'll enter the conversational workspace where you can:
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h4 className="font-medium text-gray-900">Real-Time Features:</h4>
                    <ul className="space-y-2 text-gray-600">
                      <li className="flex items-center space-x-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        <span>Live chat with your AI team</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        <span>Real-time thinking processes</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        <span>Task progress tracking</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        <span>Deliverable creation in real-time</span>
                      </li>
                    </ul>
                  </div>

                  <div className="space-y-4">
                    <h4 className="font-medium text-gray-900">What You'll See:</h4>
                    <ul className="space-y-2 text-gray-600">
                      <li className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                        <span>Agent conversations and collaboration</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-green-600 rounded-full"></div>
                        <span>Completed deliverables (docs, strategies, etc.)</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-purple-600 rounded-full"></div>
                        <span>Quality assurance and improvements</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-orange-600 rounded-full"></div>
                        <span>Project completion notifications</span>
                      </li>
                    </ul>
                  </div>
                </div>

                <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
                  <h4 className="font-medium text-yellow-900 mb-2">💡 Pro Tip: Interact with Your Team</h4>
                  <p className="text-yellow-800 text-sm">
                    You can chat with your AI team anytime! Ask questions, request changes, or provide additional context. 
                    They'll adapt their work based on your feedback.
                  </p>
                </div>
              </div>
            </section>

            {/* Step 5: Review Results */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4 flex items-center">
                <span className="inline-flex items-center justify-center w-8 h-8 bg-green-600 text-white text-sm font-semibold rounded-full mr-3">5</span>
                Review Your Results
              </h2>
              
              <div className="space-y-6">
                <p className="text-gray-600">
                  Within minutes to hours (depending on project complexity), your AI team will deliver:
                </p>

                <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-6 border">
                  <h4 className="font-medium text-gray-900 mb-4">Expected Deliverables for Marketing Campaign:</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        <span className="text-sm">Brand positioning document</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        <span className="text-sm">Target audience analysis</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        <span className="text-sm">30-post content calendar</span>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        <span className="text-sm">Email sequence templates</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        <span className="text-sm">Influencer outreach strategy</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        <span className="text-sm">Performance tracking dashboard</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                  <h4 className="font-medium text-blue-900 mb-2">🎉 Congratulations!</h4>
                  <p className="text-blue-700 text-sm">
                    You've successfully run your first AI team project. All deliverables are ready to use in your business, 
                    with no placeholder content - everything is tailored to your specific goals and context.
                  </p>
                </div>
              </div>
            </section>

            {/* Next Steps */}
            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">What's Next?</h2>
              <div className="space-y-3">
                <Link 
                  href="/docs/core-concepts/agents"
                  className="flex items-center space-x-3 p-4 border rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all"
                >
                  <div className="p-2 bg-blue-50 rounded-lg">
                    <Users className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Learn About AI Agents</h3>
                    <p className="text-gray-600 text-sm">Understand how different agent types work together</p>
                  </div>
                </Link>

                <Link 
                  href="/docs/core-concepts/goals"
                  className="flex items-center space-x-3 p-4 border rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all"
                >
                  <div className="p-2 bg-green-50 rounded-lg">
                    <Target className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Goal-Driven Planning</h3>
                    <p className="text-gray-600 text-sm">Master the art of writing effective project goals</p>
                  </div>
                </Link>

                <div className="bg-gray-50 rounded-lg p-4 border">
                  <h4 className="font-medium text-gray-900 mb-2">💡 Try These Project Ideas Next:</h4>
                  <ul className="space-y-1 text-gray-600 text-sm">
                    <li>• Social media growth strategy for your business</li>
                    <li>• Investment portfolio analysis and recommendations</li>
                    <li>• Technical documentation for a software project</li>
                    <li>• Customer survey design and analysis plan</li>
                  </ul>
                </div>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  )
}