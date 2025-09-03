'use client'

import React from 'react'
import Link from 'next/link'
import { ArrowLeft, Brain, Zap, Eye, MessageSquare, CheckCircle, Clock, Users } from 'lucide-react'

export default function ThinkingPage() {
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
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Real-Time Thinking Processes</h1>
            <p className="text-gray-600">Claude/o3-style AI reasoning visualization and transparency</p>
          </div>

          <div className="bg-white rounded-xl border p-8">
            {/* Overview */}
            <section className="mb-12">
              <div className="bg-blue-50 rounded-lg p-6 border border-blue-200 mb-6">
                <div className="flex items-center space-x-3">
                  <Brain className="w-6 h-6 text-blue-600" />
                  <div>
                    <h3 className="font-medium text-blue-900">Transparent AI Reasoning</h3>
                    <p className="text-blue-700 text-sm mt-1">Watch AI agents think step-by-step as they work on your projects</p>
                  </div>
                </div>
              </div>
              
              <p className="text-gray-600 text-lg leading-relaxed mb-6">
                The AI Team Orchestrator provides unprecedented visibility into AI reasoning processes. Just like Claude and OpenAI's o3 models, you can watch agents think through problems, make decisions, and collaborate in real-time, making AI work completely transparent and explainable.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-6 border border-green-200">
                  <h4 className="font-semibold text-green-900 mb-2">Live Reasoning</h4>
                  <p className="text-green-700 text-sm">See agents think through problems step-by-step in real-time</p>
                </div>
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
                  <h4 className="font-semibold text-blue-900 mb-2">Decision Transparency</h4>
                  <p className="text-blue-700 text-sm">Understand why agents make specific choices and trade-offs</p>
                </div>
                <div className="bg-gradient-to-br from-purple-50 to-violet-50 rounded-lg p-6 border border-purple-200">
                  <h4 className="font-semibold text-purple-900 mb-2">Collaborative Intelligence</h4>
                  <p className="text-purple-700 text-sm">Watch agents share insights and build on each other's work</p>
                </div>
              </div>
            </section>

            {/* How It Works */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">How Thinking Processes Work</h2>
              
              <div className="space-y-8">
                {/* Step 1 */}
                <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
                  <div className="flex items-center space-x-4 mb-4">
                    <div className="flex-shrink-0 w-10 h-10 bg-blue-600 text-white text-lg font-bold rounded-full flex items-center justify-center">1</div>
                    <div>
                      <h3 className="text-xl font-bold text-blue-900">Process Initiation</h3>
                      <p className="text-blue-700">Agent receives a task and starts thinking process</p>
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg p-4 border border-blue-200">
                    <h4 className="font-medium text-blue-900 mb-3">Example Thinking Start:</h4>
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <Clock className="w-4 h-4 text-blue-600" />
                        <span className="text-sm text-blue-800">14:23:15 - Marketing Strategist starts thinking</span>
                      </div>
                      <div className="bg-blue-50 rounded p-3 ml-6">
                        <p className="text-blue-800 text-sm italic">
                          "I need to create a brand positioning document for an eco-friendly water bottle. Let me first analyze the target market and competitive landscape..."
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
                      <h3 className="text-xl font-bold text-green-900">Step-by-Step Reasoning</h3>
                      <p className="text-green-700">Agent works through the problem with visible thinking steps</p>
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg p-4 border border-green-200">
                    <h4 className="font-medium text-green-900 mb-3">Thinking Steps Example:</h4>
                    <div className="space-y-3">
                      <div className="border-l-4 border-green-400 pl-4">
                        <div className="text-xs text-green-600 mb-1">Step 1: Market Analysis</div>
                        <p className="text-green-800 text-sm">
                          "Looking at the eco-friendly product market, I see growing demand among millennials (65% willing to pay premium) and Gen Z (78% consider sustainability)..."
                        </p>
                      </div>
                      <div className="border-l-4 border-green-400 pl-4">
                        <div className="text-xs text-green-600 mb-1">Step 2: Competitive Positioning</div>
                        <p className="text-green-800 text-sm">
                          "Key competitors include Hydro Flask and S'well, but they focus mainly on design. Our unique angle could be verified carbon neutrality and ocean plastic reduction..."
                        </p>
                      </div>
                      <div className="border-l-4 border-green-400 pl-4">
                        <div className="text-xs text-green-600 mb-1">Step 3: Value Proposition</div>
                        <p className="text-green-800 text-sm">
                          "The positioning should emphasize 'Sustainable by Design, Impact by Choice' - appealing to values-driven consumers who want visible environmental impact..."
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Step 3 */}
                <div className="bg-purple-50 rounded-lg p-6 border border-purple-200">
                  <div className="flex items-center space-x-4 mb-4">
                    <div className="flex-shrink-0 w-10 h-10 bg-purple-600 text-white text-lg font-bold rounded-full flex items-center justify-center">3</div>
                    <div>
                      <h3 className="text-xl font-bold text-purple-900">Collaborative Thinking</h3>
                      <p className="text-purple-700">Agents share insights and build on each other's reasoning</p>
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg p-4 border border-purple-200">
                    <h4 className="font-medium text-purple-900 mb-3">Agent Collaboration Example:</h4>
                    <div className="space-y-3">
                      <div className="flex items-start space-x-3">
                        <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                          <span className="text-xs text-purple-600 font-bold">MS</span>
                        </div>
                        <div className="flex-1">
                          <div className="text-xs text-purple-600 mb-1">Marketing Strategist shares insight</div>
                          <p className="text-purple-800 text-sm">
                            "I've identified 'verified impact' as our key differentiator. @ContentCreator, can you develop messaging that emphasizes measurable environmental benefits?"
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-start space-x-3">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                          <span className="text-xs text-blue-600 font-bold">CC</span>
                        </div>
                        <div className="flex-1">
                          <div className="text-xs text-blue-600 mb-1">Content Creator responds</div>
                          <p className="text-blue-800 text-sm">
                            "Perfect! I'm thinking taglines like 'Every Sip Saves the Ocean' with specific metrics: '1 bottle = 50 plastic bottles removed from ocean'. This makes impact tangible."
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Step 4 */}
                <div className="bg-orange-50 rounded-lg p-6 border border-orange-200">
                  <div className="flex items-center space-x-4 mb-4">
                    <div className="flex-shrink-0 w-10 h-10 bg-orange-600 text-white text-lg font-bold rounded-full flex items-center justify-center">4</div>
                    <div>
                      <h3 className="text-xl font-bold text-orange-900">Process Completion</h3>
                      <p className="text-orange-700">Agent concludes with final reasoning and deliverable creation</p>
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg p-4 border border-orange-200">
                    <h4 className="font-medium text-orange-900 mb-3">Completion Example:</h4>
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <CheckCircle className="w-4 h-4 text-orange-600" />
                        <span className="text-sm text-orange-800">14:31:42 - Thinking process completed</span>
                      </div>
                      <div className="bg-orange-50 rounded p-3 ml-6">
                        <p className="text-orange-800 text-sm italic">
                          "Based on my analysis, I've created a comprehensive brand positioning document that positions our eco-friendly bottle as the first 'verified impact' hydration solution. The document includes market analysis, competitive positioning, value proposition, and messaging framework ready for implementation."
                        </p>
                      </div>
                      <div className="flex items-center space-x-2 ml-6 mt-2">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <span className="text-xs text-green-700">Deliverable: Brand Positioning Document.pdf created</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* UI Components */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Thinking Process UI Features</h2>
              
              <div className="space-y-6">
                <div className="bg-gray-50 rounded-lg p-6 border">
                  <h3 className="font-medium text-gray-900 mb-4 flex items-center">
                    <Eye className="w-5 h-5 mr-2" />
                    Real-Time Display Components
                  </h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">Thinking Steps Viewer:</h4>
                      <ul className="space-y-1 text-gray-600 text-sm">
                        <li>• Live streaming of reasoning steps</li>
                        <li>• Timestamp for each thought</li>
                        <li>• Agent identification and avatars</li>
                        <li>• Step categorization (analysis, decision, etc.)</li>
                        <li>• Expandable/collapsible step details</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">Collaboration Panel:</h4>
                      <ul className="space-y-1 text-gray-600 text-sm">
                        <li>• Inter-agent communication display</li>
                        <li>• Insight sharing and @mentions</li>
                        <li>• Real-time response threads</li>
                        <li>• Knowledge handoff visualization</li>
                        <li>• Collaborative decision points</li>
                      </ul>
                    </div>
                  </div>
                </div>

                <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
                  <h3 className="font-medium text-blue-900 mb-4 flex items-center">
                    <MessageSquare className="w-5 h-5 mr-2" />
                    Interactive Features
                  </h3>
                  
                  <div className="space-y-4">
                    <div className="bg-white rounded-lg p-4 border border-blue-200">
                      <h4 className="font-medium text-blue-900 mb-2">Ask Questions During Thinking:</h4>
                      <p className="text-blue-700 text-sm mb-3">
                        You can interact with agents while they're thinking, asking for clarification or providing additional context.
                      </p>
                      <div className="bg-blue-50 rounded p-3">
                        <div className="text-xs text-blue-600 mb-1">Example User Interruption:</div>
                        <p className="text-blue-800 text-sm italic">
                          "Hey Marketing Strategist, could you also consider the corporate gifting market? We have interest from several companies."
                        </p>
                      </div>
                    </div>
                    
                    <div className="bg-white rounded-lg p-4 border border-blue-200">
                      <h4 className="font-medium text-blue-900 mb-2">Thinking Speed Control:</h4>
                      <p className="text-blue-700 text-sm">
                        Adjust the display speed of thinking processes - from real-time to accelerated playback for completed processes.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Technical Implementation */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Technical Architecture</h2>
              
              <div className="space-y-6">
                <div className="bg-green-50 rounded-lg p-6 border border-green-200">
                  <h3 className="font-medium text-green-900 mb-4 flex items-center">
                    <Zap className="w-5 h-5 mr-2" />
                    WebSocket Real-Time Streaming
                  </h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-medium text-green-900 mb-2">Backend Implementation:</h4>
                      <ul className="space-y-1 text-green-700 text-sm">
                        <li>• <code className="bg-white px-1 rounded">thinking_process.py</code> service</li>
                        <li>• WebSocket broadcasting system</li>
                        <li>• Process state management</li>
                        <li>• Automatic completion detection</li>
                        <li>• Recovery for stuck processes</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium text-green-900 mb-2">Frontend Integration:</h4>
                      <ul className="space-y-1 text-green-700 text-sm">
                        <li>• <code className="bg-white px-1 rounded">ThinkingProcessViewer.tsx</code></li>
                        <li>• Real-time WebSocket connection</li>
                        <li>• State synchronization</li>
                        <li>• Conversation tab integration</li>
                        <li>• Performance optimization</li>
                      </ul>
                    </div>
                  </div>
                </div>

                <div className="bg-purple-50 rounded-lg p-6 border border-purple-200">
                  <h3 className="font-medium text-purple-900 mb-4 flex items-center">
                    <Brain className="w-5 h-5 mr-2" />
                    Thinking Process Lifecycle
                  </h3>
                  
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-purple-200">
                      <span className="text-sm text-purple-800 font-medium">start_thinking_process()</span>
                      <span className="text-xs text-purple-600 bg-purple-100 px-2 py-1 rounded">Creates new thinking session</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-purple-200">
                      <span className="text-sm text-purple-800 font-medium">add_thinking_step()</span>
                      <span className="text-xs text-purple-600 bg-purple-100 px-2 py-1 rounded">Adds reasoning steps in real-time</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-purple-200">
                      <span className="text-sm text-purple-800 font-medium">complete_thinking_process()</span>
                      <span className="text-xs text-purple-600 bg-purple-100 px-2 py-1 rounded">Finalizes with conclusion</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-purple-200">
                      <span className="text-sm text-purple-800 font-medium">auto_complete_stuck_processes()</span>
                      <span className="text-xs text-purple-600 bg-purple-100 px-2 py-1 rounded">Recovery for incomplete processes</span>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Benefits */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Benefits of Thinking Transparency</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h3 className="font-medium text-green-900 flex items-center">
                    <CheckCircle className="w-5 h-5 mr-2" />
                    For Users
                  </h3>
                  <ul className="space-y-2 text-gray-600 text-sm">
                    <li>• <strong>Build Trust:</strong> See exactly how AI makes decisions</li>
                    <li>• <strong>Learn from AI:</strong> Understand expert reasoning patterns</li>
                    <li>• <strong>Quality Assurance:</strong> Catch errors in reasoning early</li>
                    <li>• <strong>Interactive Guidance:</strong> Provide input during the process</li>
                    <li>• <strong>Process Understanding:</strong> Know why deliverables were created this way</li>
                  </ul>
                </div>
                
                <div className="space-y-4">
                  <h3 className="font-medium text-blue-900 flex items-center">
                    <Zap className="w-5 h-5 mr-2" />
                    For the System
                  </h3>
                  <ul className="space-y-2 text-gray-600 text-sm">
                    <li>• <strong>Better Collaboration:</strong> Agents build on each other's insights</li>
                    <li>• <strong>Quality Improvement:</strong> Reasoning steps can be reviewed and improved</li>
                    <li>• <strong>Debugging:</strong> Easy to identify where processes go wrong</li>
                    <li>• <strong>Learning:</strong> Successful reasoning patterns can be replicated</li>
                    <li>• <strong>Accountability:</strong> Clear audit trail for all decisions</li>
                  </ul>
                </div>
              </div>
            </section>

            {/* Next Steps */}
            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Explore More</h2>
              <div className="space-y-3">
                <Link 
                  href="/docs/core-concepts/agents"
                  className="flex items-center space-x-3 p-4 border rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all"
                >
                  <div className="p-2 bg-blue-50 rounded-lg">
                    <Users className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">AI Agent System</h3>
                    <p className="text-gray-600 text-sm">Learn about the agents doing the thinking</p>
                  </div>
                </Link>

                <Link 
                  href="/docs/development/websockets"
                  className="flex items-center space-x-3 p-4 border rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all"
                >
                  <div className="p-2 bg-green-50 rounded-lg">
                    <Zap className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">WebSocket Events</h3>
                    <p className="text-gray-600 text-sm">Technical details of real-time communication</p>
                  </div>
                </Link>

                <Link 
                  href="/docs/getting-started/first-project"
                  className="flex items-center space-x-3 p-4 border rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all"
                >
                  <div className="p-2 bg-purple-50 rounded-lg">
                    <Eye className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">See It In Action</h3>
                    <p className="text-gray-600 text-sm">Create a project and watch agents think</p>
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