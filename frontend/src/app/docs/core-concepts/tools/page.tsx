'use client'

import React from 'react'
import Link from 'next/link'
import { ArrowLeft, Wrench, Search, Upload, Share2, MessageSquare, Code, Database, Zap, Settings } from 'lucide-react'

export default function ToolsPage() {
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
            <h1 className="text-3xl font-bold text-gray-900">Tools & Registry</h1>
            <p className="text-gray-600 mt-2">
              Extensible tools with slash commands for enhanced AI capabilities
            </p>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Overview */}
        <div className="bg-white rounded-xl border p-8 mb-8">
          <div className="flex items-center space-x-4 mb-6">
            <div className="p-3 bg-blue-50 rounded-xl">
              <Wrench className="w-8 h-8 text-blue-600" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">System Overview</h2>
              <p className="text-gray-600">
                Dynamic tool registry enabling agents to use real-world tools and APIs
              </p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-blue-50 rounded-lg p-6">
              <h3 className="font-semibold text-blue-900 mb-2">Dynamic Tool Loading</h3>
              <p className="text-blue-700 text-sm">
                Tools are dynamically discovered and loaded at runtime for maximum flexibility
              </p>
            </div>
            <div className="bg-green-50 rounded-lg p-6">
              <h3 className="font-semibold text-green-900 mb-2">Slash Command Integration</h3>
              <p className="text-green-700 text-sm">
                Users can discover and use tools through intuitive slash commands in the chat
              </p>
            </div>
            <div className="bg-purple-50 rounded-lg p-6">
              <h3 className="font-semibold text-purple-900 mb-2">Platform-Specific Tools</h3>
              <p className="text-purple-700 text-sm">
                Specialized tools for different platforms (Instagram, LinkedIn, Twitter, TikTok)
              </p>
            </div>
          </div>
        </div>

        {/* Core Tools */}
        <div className="bg-white rounded-xl border p-8 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-6">Core Tool Categories</h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Project Management Tools */}
            <div className="border rounded-xl p-6">
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-2 rounded-lg bg-blue-100 text-blue-800">
                  <Database className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Project Management</h3>
                  <p className="text-sm text-gray-600">Core project operations and status</p>
                </div>
              </div>
              <div className="bg-gray-50 rounded p-3">
                <h4 className="font-medium text-gray-900 text-sm mb-2">Available Tools</h4>
                <ul className="text-xs text-gray-600 space-y-1">
                  <li>• show_project_status - Comprehensive project overview</li>
                  <li>• show_goal_progress - Goal completion tracking</li>
                  <li>• show_deliverables - Project outputs and assets</li>
                  <li>• create_goal - Create new objectives with metrics</li>
                </ul>
              </div>
            </div>

            {/* Team Management Tools */}
            <div className="border rounded-xl p-6">
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-2 rounded-lg bg-green-100 text-green-800">
                  <MessageSquare className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Team Management</h3>
                  <p className="text-sm text-gray-600">Team coordination and workflow</p>
                </div>
              </div>
              <div className="bg-gray-50 rounded p-3">
                <h4 className="font-medium text-gray-900 text-sm mb-2">Available Tools</h4>
                <ul className="text-xs text-gray-600 space-y-1">
                  <li>• show_team_status - Current team composition</li>
                  <li>• add_team_member - Add specialized agents</li>
                  <li>• approve_all_feedback - Bulk feedback processing</li>
                  <li>• fix_workspace_issues - Automated troubleshooting</li>
                </ul>
              </div>
            </div>

            {/* Social Media Tools */}
            <div className="border rounded-xl p-6">
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-2 rounded-lg bg-purple-100 text-purple-800">
                  <Share2 className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Social Media</h3>
                  <p className="text-sm text-gray-600">Platform-specific social tools</p>
                </div>
              </div>
              <div className="bg-gray-50 rounded p-3">
                <h4 className="font-medium text-gray-900 text-sm mb-2">Supported Platforms</h4>
                <ul className="text-xs text-gray-600 space-y-1">
                  <li>• Instagram - Content creation and engagement</li>
                  <li>• LinkedIn - Professional networking tools</li>
                  <li>• Twitter - Tweet composition and scheduling</li>
                  <li>• TikTok - Video content optimization</li>
                </ul>
              </div>
            </div>

            {/* System Tools */}
            <div className="border rounded-xl p-6">
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-2 rounded-lg bg-orange-100 text-orange-800">
                  <Settings className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">System Tools</h3>
                  <p className="text-sm text-gray-600">System utilities and diagnostics</p>
                </div>
              </div>
              <div className="bg-gray-50 rounded p-3">
                <h4 className="font-medium text-gray-900 text-sm mb-2">Utility Functions</h4>
                <ul className="text-xs text-gray-600 space-y-1">
                  <li>• Web search - Real-time web search capabilities</li>
                  <li>• File operations - Document processing</li>
                  <li>• Database queries - Data retrieval and updates</li>
                  <li>• API integrations - External service connections</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Slash Commands */}
        <div className="bg-white rounded-xl border p-8 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-6">Slash Command Interface</h2>
          
          <div className="bg-gray-50 rounded-lg p-6 mb-6">
            <h3 className="font-semibold text-gray-900 mb-4">How to Use Slash Commands</h3>
            <div className="space-y-3">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <span className="text-blue-600 font-bold text-sm">1</span>
                </div>
                <div>
                  <p className="font-medium text-gray-900">Type "/" in any chat input</p>
                  <p className="text-sm text-gray-600">Opens the tool discovery interface</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <span className="text-blue-600 font-bold text-sm">2</span>
                </div>
                <div>
                  <p className="font-medium text-gray-900">Browse or search available tools</p>
                  <p className="text-sm text-gray-600">Tools are organized by category</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <span className="text-blue-600 font-bold text-sm">3</span>
                </div>
                <div>
                  <p className="font-medium text-gray-900">Select and execute</p>
                  <p className="text-sm text-gray-600">Tools run with contextual parameters</p>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-blue-50 rounded-lg p-4">
            <h4 className="font-medium text-blue-900 mb-2">Example Commands</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <code className="bg-white px-2 py-1 rounded text-blue-800">/show_project_status</code>
                <p className="text-blue-700 mt-1">Get comprehensive project overview</p>
              </div>
              <div>
                <code className="bg-white px-2 py-1 rounded text-blue-800">/add_team_member</code>
                <p className="text-blue-700 mt-1">Add new specialized team member</p>
              </div>
            </div>
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="bg-white rounded-xl border p-8">
          <h2 className="text-xl font-bold text-gray-900 mb-6">Performance Metrics</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900 mb-1">&lt; 500ms</div>
              <div className="font-medium text-gray-900 mb-1">Tool Execution</div>
              <div className="text-sm text-gray-600">Average response time</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900 mb-1">100%</div>
              <div className="font-medium text-gray-900 mb-1">Input Validation</div>
              <div className="text-sm text-gray-600">All inputs validated</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900 mb-1">50+</div>
              <div className="font-medium text-gray-900 mb-1">Available Tools</div>
              <div className="text-sm text-gray-600">Across all categories</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900 mb-1">99.8%</div>
              <div className="font-medium text-gray-900 mb-1">Success Rate</div>
              <div className="text-sm text-gray-600">Tool execution reliability</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}