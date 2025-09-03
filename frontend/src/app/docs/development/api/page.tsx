'use client'

import React from 'react'
import Link from 'next/link'
import { ArrowLeft, Code, Database, Zap, Users, Target, Copy, CheckCircle } from 'lucide-react'

export default function APIPage() {
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <Link 
              href="/docs"
              className="inline-flex items-center text-blue-600 hover:text-blue-800 transition-colors mb-4"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Documentation
            </Link>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">API Reference</h1>
            <p className="text-gray-600">Complete REST API documentation for the AI Team Orchestrator</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
            {/* Navigation Sidebar */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-xl border p-6 sticky top-8">
                <h2 className="font-semibold text-gray-900 mb-4">API Sections</h2>
                <nav className="space-y-2">
                  <a href="#overview" className="block text-blue-600 hover:text-blue-800 text-sm">Overview</a>
                  <a href="#authentication" className="block text-gray-600 hover:text-gray-800 text-sm">Authentication</a>
                  <a href="#workspaces" className="block text-gray-600 hover:text-gray-800 text-sm">Workspaces</a>
                  <a href="#goals" className="block text-gray-600 hover:text-gray-800 text-sm">Goals</a>
                  <a href="#agents" className="block text-gray-600 hover:text-gray-800 text-sm">Agents</a>
                  <a href="#tasks" className="block text-gray-600 hover:text-gray-800 text-sm">Tasks</a>
                  <a href="#deliverables" className="block text-gray-600 hover:text-gray-800 text-sm">Deliverables</a>
                  <a href="#conversational" className="block text-gray-600 hover:text-gray-800 text-sm">Conversational</a>
                  <a href="#monitoring" className="block text-gray-600 hover:text-gray-800 text-sm">Monitoring</a>
                </nav>
              </div>
            </div>

            {/* Main Content */}
            <div className="lg:col-span-3">
              <div className="bg-white rounded-xl border p-8">
                {/* Overview */}
                <section id="overview" className="mb-12">
                  <h2 className="text-2xl font-semibold text-gray-900 mb-6">API Overview</h2>
                  
                  <div className="bg-blue-50 rounded-lg p-6 border border-blue-200 mb-6">
                    <h3 className="font-medium text-blue-900 mb-3">Base URL</h3>
                    <div className="bg-gray-900 rounded-lg p-3">
                      <div className="flex items-center justify-between">
                        <code className="text-green-400">http://localhost:8000/api</code>
                        <button 
                          onClick={() => copyToClipboard('http://localhost:8000/api')}
                          className="text-gray-400 hover:text-white transition-colors"
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                    <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                      <h4 className="font-medium text-green-900 mb-2">Request Format</h4>
                      <p className="text-green-700 text-sm">JSON requests with application/json content-type</p>
                    </div>
                    <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                      <h4 className="font-medium text-blue-900 mb-2">Response Format</h4>
                      <p className="text-blue-700 text-sm">JSON responses with standard HTTP status codes</p>
                    </div>
                  </div>

                  <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
                    <h4 className="font-medium text-yellow-900 mb-2">Important Notes</h4>
                    <ul className="space-y-1 text-yellow-700 text-sm">
                      <li>• All endpoints require the <code>/api</code> prefix</li>
                      <li>• POST requests to collections need trailing slash (e.g., <code>/api/workspaces/</code>)</li>
                      <li>• WebSocket connections available for real-time updates</li>
                      <li>• Rate limiting applies to auto-completion endpoints</li>
                    </ul>
                  </div>
                </section>

                {/* Authentication */}
                <section id="authentication" className="mb-12">
                  <h2 className="text-2xl font-semibold text-gray-900 mb-6">Authentication</h2>
                  
                  <div className="bg-gray-50 rounded-lg p-6 border">
                    <p className="text-gray-700 mb-4">
                      The current version uses development mode with mock user authentication. 
                      Production authentication will be implemented in future versions.
                    </p>
                    
                    <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                      <h4 className="font-medium text-blue-900 mb-2">Development Mode</h4>
                      <p className="text-blue-700 text-sm">
                        Mock user ID: <code className="bg-white px-2 py-1 rounded">123e4567-e89b-12d3-a456-426614174000</code>
                      </p>
                    </div>
                  </div>
                </section>

                {/* Workspaces API */}
                <section id="workspaces" className="mb-12">
                  <h2 className="text-2xl font-semibold text-gray-900 mb-6 flex items-center">
                    <Database className="w-6 h-6 text-blue-600 mr-3" />
                    Workspaces API
                  </h2>
                  
                  <div className="space-y-6">
                    {/* GET Workspaces */}
                    <div className="border rounded-lg p-6">
                      <div className="flex items-center space-x-3 mb-4">
                        <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">GET</span>
                        <code className="text-lg font-mono">/api/workspaces/</code>
                      </div>
                      <p className="text-gray-600 mb-4">Retrieve all workspaces for the current user</p>
                      
                      <div className="bg-gray-900 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-gray-400 text-sm">Example Response</span>
                          <button 
                            onClick={() => copyToClipboard(`[
  {
    "id": "workspace-uuid",
    "name": "Marketing Campaign Project",
    "description": "Complete marketing strategy for new product",
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "status": "active",
    "created_at": "2025-01-01T10:00:00Z",
    "budget": {
      "max_amount": 1500,
      "currency": "EUR"
    }
  }
]`)}
                            className="text-gray-400 hover:text-white transition-colors"
                          >
                            <Copy className="w-4 h-4" />
                          </button>
                        </div>
                        <pre className="text-green-400 text-sm overflow-x-auto">
                          <code>{`[
  {
    "id": "workspace-uuid",
    "name": "Marketing Campaign Project",
    "description": "Complete marketing strategy for new product",
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "status": "active",
    "created_at": "2025-01-01T10:00:00Z",
    "budget": {
      "max_amount": 1500,
      "currency": "EUR"
    }
  }
]`}</code>
                        </pre>
                      </div>
                    </div>

                    {/* POST Workspaces */}
                    <div className="border rounded-lg p-6">
                      <div className="flex items-center space-x-3 mb-4">
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded">POST</span>
                        <code className="text-lg font-mono">/api/workspaces/</code>
                      </div>
                      <p className="text-gray-600 mb-4">Create a new workspace</p>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-gray-900 rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-gray-400 text-sm">Request Body</span>
                            <button 
                              onClick={() => copyToClipboard(`{
  "name": "New Project",
  "description": "Project description",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "goal": "Detailed project goal with deliverables",
  "budget": {
    "max_amount": 1200,
    "currency": "EUR"
  }
}`)}
                              className="text-gray-400 hover:text-white transition-colors"
                            >
                              <Copy className="w-4 h-4" />
                            </button>
                          </div>
                          <pre className="text-yellow-400 text-sm overflow-x-auto">
                            <code>{`{
  "name": "New Project",
  "description": "Project description",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "goal": "Detailed project goal with deliverables",
  "budget": {
    "max_amount": 1200,
    "currency": "EUR"
  }
}`}</code>
                          </pre>
                        </div>

                        <div className="bg-gray-900 rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-gray-400 text-sm">Response (201)</span>
                          </div>
                          <pre className="text-green-400 text-sm overflow-x-auto">
                            <code>{`{
  "id": "new-workspace-uuid",
  "name": "New Project",
  "status": "created",
  "redirect_url": "/projects/{id}/configure"
}`}</code>
                          </pre>
                        </div>
                      </div>
                    </div>

                    {/* GET Single Workspace */}
                    <div className="border rounded-lg p-6">
                      <div className="flex items-center space-x-3 mb-4">
                        <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">GET</span>
                        <code className="text-lg font-mono">/api/workspaces/{`{id}`}</code>
                      </div>
                      <p className="text-gray-600 mb-4">Retrieve a specific workspace by ID</p>
                      
                      <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                        <h5 className="font-medium text-blue-900 mb-2">Path Parameters:</h5>
                        <ul className="space-y-1 text-blue-700 text-sm">
                          <li>• <code>id</code> (string): Workspace UUID</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </section>

                {/* Goals API */}
                <section id="goals" className="mb-12">
                  <h2 className="text-2xl font-semibold text-gray-900 mb-6 flex items-center">
                    <Target className="w-6 h-6 text-green-600 mr-3" />
                    Goals API
                  </h2>
                  
                  <div className="space-y-6">
                    <div className="border rounded-lg p-6">
                      <div className="flex items-center space-x-3 mb-4">
                        <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">GET</span>
                        <code className="text-lg font-mono">/api/goals/workspace/{`{workspace_id}`}</code>
                      </div>
                      <p className="text-gray-600 mb-4">Get all goals for a specific workspace</p>
                      
                      <div className="bg-gray-900 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-gray-400 text-sm">Example Response</span>
                          <button 
                            onClick={() => copyToClipboard(`[
  {
    "id": "goal-uuid",
    "workspace_id": "workspace-uuid",
    "description": "Create brand positioning document",
    "status": "active",
    "progress": 75.5,
    "metric_type": "deliverable_completion",
    "target_value": 100,
    "current_value": 75.5,
    "created_at": "2025-01-01T10:00:00Z"
  }
]`)}
                            className="text-gray-400 hover:text-white transition-colors"
                          >
                            <Copy className="w-4 h-4" />
                          </button>
                        </div>
                        <pre className="text-green-400 text-sm overflow-x-auto">
                          <code>{`[
  {
    "id": "goal-uuid",
    "workspace_id": "workspace-uuid",
    "description": "Create brand positioning document",
    "status": "active",
    "progress": 75.5,
    "metric_type": "deliverable_completion",
    "target_value": 100,
    "current_value": 75.5,
    "created_at": "2025-01-01T10:00:00Z"
  }
]`}</code>
                        </pre>
                      </div>
                    </div>

                    <div className="border rounded-lg p-6">
                      <div className="flex items-center space-x-3 mb-4">
                        <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs font-semibold rounded">PUT</span>
                        <code className="text-lg font-mono">/api/goals/{`{id}`}/progress</code>
                      </div>
                      <p className="text-gray-600 mb-4">Update goal progress</p>
                      
                      <div className="bg-gray-900 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-gray-400 text-sm">Request Body</span>
                        </div>
                        <pre className="text-yellow-400 text-sm overflow-x-auto">
                          <code>{`{
  "progress": 85.0,
  "current_value": 85.0,
  "quality_score": 92.5
}`}</code>
                        </pre>
                      </div>
                    </div>
                  </div>
                </section>

                {/* Agents API */}
                <section id="agents" className="mb-12">
                  <h2 className="text-2xl font-semibold text-gray-900 mb-6 flex items-center">
                    <Users className="w-6 h-6 text-purple-600 mr-3" />
                    Agents API
                  </h2>
                  
                  <div className="space-y-6">
                    <div className="border rounded-lg p-6">
                      <div className="flex items-center space-x-3 mb-4">
                        <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">GET</span>
                        <code className="text-lg font-mono">/api/agents/{`{workspace_id}`}</code>
                      </div>
                      <p className="text-gray-600 mb-4">Get all agents assigned to a workspace</p>
                      
                      <div className="bg-gray-900 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-gray-400 text-sm">Example Response</span>
                        </div>
                        <pre className="text-green-400 text-sm overflow-x-auto">
                          <code>{`[
  {
    "id": "agent-uuid",
    "name": "Marketing Strategist",
    "type": "marketing_strategist",
    "seniority": "senior",
    "status": "active",
    "skills": ["brand_positioning", "market_analysis", "strategy"],
    "workspace_id": "workspace-uuid",
    "current_task_id": "task-uuid"
  }
]`}</code>
                        </pre>
                      </div>
                    </div>

                    <div className="border rounded-lg p-6">
                      <div className="flex items-center space-x-3 mb-4">
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded">POST</span>
                        <code className="text-lg font-mono">/api/director/proposal</code>
                      </div>
                      <p className="text-gray-600 mb-4">Create team proposal for workspace</p>
                      
                      <div className="bg-gray-900 rounded-lg p-4 mb-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-gray-400 text-sm">Request Body</span>
                        </div>
                        <pre className="text-yellow-400 text-sm overflow-x-auto">
                          <code>{`{
  "workspace_id": "workspace-uuid",
  "workspace_goal": "Create marketing campaign for eco-friendly bottle",
  "user_feedback": "Focus on Gen Z sustainability messaging"
}`}</code>
                        </pre>
                      </div>

                      <div className="bg-gray-900 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-gray-400 text-sm">Response (200)</span>
                        </div>
                        <pre className="text-green-400 text-sm overflow-x-auto">
                          <code>{`{
  "proposal_id": "proposal-uuid",
  "team_members": [
    {
      "name": "Marketing Strategist",
      "type": "marketing_strategist",
      "seniority": "senior",
      "skills": ["brand_positioning", "market_analysis"],
      "estimated_cost": 450
    }
  ],
  "estimated_cost": 1200,
  "estimated_duration": "3-5 days"
}`}</code>
                        </pre>
                      </div>
                    </div>

                    <div className="border rounded-lg p-6">
                      <div className="flex items-center space-x-3 mb-4">
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded">POST</span>
                        <code className="text-lg font-mono">/api/director/approve/{`{workspace_id}`}</code>
                      </div>
                      <p className="text-gray-600 mb-4">Approve team proposal and start execution</p>
                      
                      <div className="bg-blue-50 rounded-lg p-4 border border-blue-200 mb-4">
                        <h5 className="font-medium text-blue-900 mb-2">Query Parameters:</h5>
                        <ul className="space-y-1 text-blue-700 text-sm">
                          <li>• <code>proposal_id</code> (required): UUID of the proposal to approve</li>
                        </ul>
                      </div>

                      <div className="bg-gray-900 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-gray-400 text-sm">Response (200)</span>
                        </div>
                        <pre className="text-green-400 text-sm overflow-x-auto">
                          <code>{`{
  "status": "success",
  "background_processing": true,
  "estimated_completion_seconds": 30,
  "message": "Team approved and agents are being created"
}`}</code>
                        </pre>
                      </div>
                    </div>
                  </div>
                </section>

                {/* Tasks API */}
                <section id="tasks" className="mb-12">
                  <h2 className="text-2xl font-semibold text-gray-900 mb-6 flex items-center">
                    <CheckCircle className="w-6 h-6 text-orange-600 mr-3" />
                    Tasks API
                  </h2>
                  
                  <div className="space-y-6">
                    <div className="border rounded-lg p-6">
                      <div className="flex items-center space-x-3 mb-4">
                        <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">GET</span>
                        <code className="text-lg font-mono">/api/tasks/workspace/{`{workspace_id}`}</code>
                      </div>
                      <p className="text-gray-600 mb-4">Get all tasks for a workspace</p>
                      
                      <div className="bg-gray-900 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-gray-400 text-sm">Example Response</span>
                        </div>
                        <pre className="text-green-400 text-sm overflow-x-auto">
                          <code>{`[
  {
    "id": "task-uuid",
    "workspace_id": "workspace-uuid",
    "goal_id": "goal-uuid",
    "title": "Create brand positioning document",
    "description": "Develop positioning for eco-friendly water bottle",
    "status": "completed",
    "priority": 85,
    "agent_id": "agent-uuid",
    "created_at": "2025-01-01T10:00:00Z",
    "completed_at": "2025-01-01T12:30:00Z"
  }
]`}</code>
                        </pre>
                      </div>
                    </div>

                    <div className="border rounded-lg p-6">
                      <div className="flex items-center space-x-3 mb-4">
                        <span className="px-2 py-1 bg-orange-100 text-orange-800 text-xs font-semibold rounded">PATCH</span>
                        <code className="text-lg font-mono">/api/tasks/{`{id}`}/status</code>
                      </div>
                      <p className="text-gray-600 mb-4">Update task status</p>
                      
                      <div className="bg-gray-900 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-gray-400 text-sm">Request Body</span>
                        </div>
                        <pre className="text-yellow-400 text-sm overflow-x-auto">
                          <code>{`{
  "status": "in_progress",
  "agent_id": "agent-uuid",
  "progress_notes": "Started market analysis phase"
}`}</code>
                        </pre>
                      </div>
                    </div>
                  </div>
                </section>

                {/* Deliverables API */}
                <section id="deliverables" className="mb-12">
                  <h2 className="text-2xl font-semibold text-gray-900 mb-6 flex items-center">
                    <Code className="w-6 h-6 text-indigo-600 mr-3" />
                    Deliverables API
                  </h2>
                  
                  <div className="space-y-6">
                    <div className="border rounded-lg p-6">
                      <div className="flex items-center space-x-3 mb-4">
                        <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">GET</span>
                        <code className="text-lg font-mono">/api/deliverables/workspace/{`{workspace_id}`}</code>
                      </div>
                      <p className="text-gray-600 mb-4">Get all deliverables for a workspace</p>
                      
                      <div className="bg-gray-900 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-gray-400 text-sm">Example Response</span>
                        </div>
                        <pre className="text-green-400 text-sm overflow-x-auto">
                          <code>{`[
  {
    "id": "deliverable-uuid",
    "workspace_id": "workspace-uuid",
    "goal_id": "goal-uuid",
    "title": "Brand Positioning Document",
    "type": "document",
    "status": "completed",
    "content": {...},
    "display_content": "<h1>Brand Positioning...</h1>",
    "display_format": "html",
    "display_quality_score": 0.92,
    "created_at": "2025-01-01T12:30:00Z"
  }
]`}</code>
                        </pre>
                      </div>
                    </div>

                    <div className="border rounded-lg p-6">
                      <div className="flex items-center space-x-3 mb-4">
                        <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">GET</span>
                        <code className="text-lg font-mono">/api/unified-assets/workspace/{`{workspace_id}`}</code>
                      </div>
                      <p className="text-gray-600 mb-4">Get comprehensive workspace assets (heavy operation)</p>
                      
                      <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200 mb-4">
                        <h5 className="font-medium text-yellow-900 mb-2">⚠️ Performance Warning</h5>
                        <p className="text-yellow-700 text-sm">
                          This endpoint can take 90+ seconds and should be used sparingly. 
                          Use progressive loading patterns in frontends.
                        </p>
                      </div>

                      <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                        <h5 className="font-medium text-blue-900 mb-2">Query Parameters:</h5>
                        <ul className="space-y-1 text-blue-700 text-sm">
                          <li>• <code>includeAssets</code> (boolean): Include heavy asset processing</li>
                          <li>• <code>goalId</code> (string): Filter by specific goal</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </section>

                {/* Conversational API */}
                <section id="conversational" className="mb-12">
                  <h2 className="text-2xl font-semibold text-gray-900 mb-6 flex items-center">
                    <Zap className="w-6 h-6 text-yellow-600 mr-3" />
                    Conversational API
                  </h2>
                  
                  <div className="space-y-6">
                    <div className="border rounded-lg p-6">
                      <div className="flex items-center space-x-3 mb-4">
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded">POST</span>
                        <code className="text-lg font-mono">/api/conversational/chat/{`{workspace_id}`}</code>
                      </div>
                      <p className="text-gray-600 mb-4">Send message to AI team</p>
                      
                      <div className="bg-gray-900 rounded-lg p-4 mb-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-gray-400 text-sm">Request Body</span>
                        </div>
                        <pre className="text-yellow-400 text-sm overflow-x-auto">
                          <code>{`{
  "message": "Can you update the brand positioning to focus more on Gen Z?",
  "chat_id": "chat-uuid",
  "context": {
    "goal_id": "goal-uuid",
    "reference_deliverable": "deliverable-uuid"
  }
}`}</code>
                        </pre>
                      </div>

                      <div className="bg-gray-900 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-gray-400 text-sm">Response (200)</span>
                        </div>
                        <pre className="text-green-400 text-sm overflow-x-auto">
                          <code>{`{
  "message_id": "message-uuid",
  "status": "processing",
  "estimated_response_time": 30,
  "thinking_process_id": "thinking-uuid"
}`}</code>
                        </pre>
                      </div>
                    </div>

                    <div className="border rounded-lg p-6">
                      <div className="flex items-center space-x-3 mb-4">
                        <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">GET</span>
                        <code className="text-lg font-mono">/api/conversational/tools/execute</code>
                      </div>
                      <p className="text-gray-600 mb-4">Execute conversational tools (slash commands)</p>
                      
                      <div className="bg-blue-50 rounded-lg p-4 border border-blue-200 mb-4">
                        <h5 className="font-medium text-blue-900 mb-2">Available Tools:</h5>
                        <div className="grid grid-cols-2 gap-2 text-blue-700 text-sm">
                          <div>• show_project_status</div>
                          <div>• show_goal_progress</div>
                          <div>• show_deliverables</div>
                          <div>• show_team_status</div>
                          <div>• create_goal</div>
                          <div>• fix_workspace_issues</div>
                        </div>
                      </div>

                      <div className="bg-gray-900 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-gray-400 text-sm">Query Parameters</span>
                        </div>
                        <pre className="text-yellow-400 text-sm overflow-x-auto">
                          <code>{`?tool=show_project_status&workspace_id=workspace-uuid&args={"detailed": true}`}</code>
                        </pre>
                      </div>
                    </div>
                  </div>
                </section>

                {/* Monitoring API */}
                <section id="monitoring" className="mb-12">
                  <h2 className="text-2xl font-semibold text-gray-900 mb-6">Monitoring & Health API</h2>
                  
                  <div className="space-y-6">
                    <div className="border rounded-lg p-6">
                      <div className="flex items-center space-x-3 mb-4">
                        <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">GET</span>
                        <code className="text-lg font-mono">/health</code>
                      </div>
                      <p className="text-gray-600 mb-4">System health check</p>
                      
                      <div className="bg-gray-900 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-gray-400 text-sm">Response (200)</span>
                        </div>
                        <pre className="text-green-400 text-sm overflow-x-auto">
                          <code>{`{
  "status": "healthy",
  "database": "connected",
  "openai": "operational",
  "version": "1.0.0",
  "uptime": 86400,
  "score": 95
}`}</code>
                        </pre>
                      </div>
                    </div>

                    <div className="border rounded-lg p-6">
                      <div className="flex items-center space-x-3 mb-4">
                        <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">GET</span>
                        <code className="text-lg font-mono">/api/monitoring/workspace/{`{id}`}/health</code>
                      </div>
                      <p className="text-gray-600 mb-4">Workspace-specific health status</p>
                      
                      <div className="bg-gray-900 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-gray-400 text-sm">Response (200)</span>
                        </div>
                        <pre className="text-green-400 text-sm overflow-x-auto">
                          <code>{`{
  "workspace_id": "workspace-uuid",
  "status": "active",
  "agent_status": "operational",
  "tasks_pending": 2,
  "tasks_in_progress": 1,
  "last_activity": "2025-01-01T14:30:00Z",
  "issues": []
}`}</code>
                        </pre>
                      </div>
                    </div>
                  </div>
                </section>

                {/* Error Handling */}
                <section className="mb-12">
                  <h2 className="text-2xl font-semibold text-gray-900 mb-6">Error Handling</h2>
                  
                  <div className="space-y-4">
                    <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                      <h4 className="font-medium text-red-900 mb-2">HTTP Status Codes</h4>
                      <div className="space-y-2 text-red-700 text-sm">
                        <div>• <code>200</code> - Success</div>
                        <div>• <code>201</code> - Created</div>
                        <div>• <code>400</code> - Bad Request (validation error)</div>
                        <div>• <code>404</code> - Not Found</div>
                        <div>• <code>429</code> - Rate Limited</div>
                        <div>• <code>500</code> - Internal Server Error</div>
                      </div>
                    </div>

                    <div className="bg-gray-900 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-gray-400 text-sm">Error Response Format</span>
                      </div>
                      <pre className="text-red-400 text-sm overflow-x-auto">
                        <code>{`{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Workspace name is required",
    "details": {
      "field": "name",
      "constraint": "required"
    }
  }
}`}</code>
                      </pre>
                    </div>
                  </div>
                </section>

                {/* Rate Limiting */}
                <section>
                  <h2 className="text-2xl font-semibold text-gray-900 mb-6">Rate Limiting</h2>
                  
                  <div className="bg-yellow-50 rounded-lg p-6 border border-yellow-200">
                    <h3 className="font-medium text-yellow-900 mb-4">Rate Limits</h3>
                    <div className="space-y-2 text-yellow-700 text-sm">
                      <div>• <strong>Auto-completion operations:</strong> 5 requests per minute</div>
                      <div>• <strong>Goal unblock operations:</strong> 10 requests per minute</div>
                      <div>• <strong>General API calls:</strong> 100 requests per minute</div>
                      <div>• <strong>WebSocket connections:</strong> 5 concurrent per user</div>
                    </div>
                    
                    <div className="mt-4 bg-white rounded-lg p-3 border border-yellow-200">
                      <h4 className="font-medium text-yellow-900 mb-2">Rate Limit Headers</h4>
                      <div className="space-y-1 text-yellow-700 text-sm font-mono">
                        <div>X-RateLimit-Limit: 100</div>
                        <div>X-RateLimit-Remaining: 95</div>
                        <div>X-RateLimit-Reset: 1640995200</div>
                      </div>
                    </div>
                  </div>
                </section>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}