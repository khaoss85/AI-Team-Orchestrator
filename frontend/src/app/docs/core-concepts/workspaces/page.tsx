'use client'

import React from 'react'
import Link from 'next/link'
import { ArrowLeft, Building2, Users, Shield, Activity, Settings, Database, Globe, CheckCircle, AlertTriangle, Zap, TrendingUp } from 'lucide-react'

export default function WorkspacesPage() {
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
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Workspace Management</h1>
            <p className="text-gray-600">Multi-tenant workspace system with AI-driven health monitoring</p>
          </div>

          <div className="bg-white rounded-xl border p-8">
            {/* Overview */}
            <section className="mb-12">
              <div className="bg-blue-50 rounded-lg p-6 border border-blue-200 mb-6">
                <div className="flex items-center space-x-3">
                  <Building2 className="w-6 h-6 text-blue-600" />
                  <div>
                    <h3 className="text-lg font-semibold text-blue-900">Multi-Tenant Architecture</h3>
                    <p className="text-blue-700 mt-1">
                      Complete workspace isolation with per-workspace AI teams, goals, deliverables, and 
                      autonomous health monitoring. Each workspace operates as an independent AI organization.
                    </p>
                  </div>
                </div>
              </div>

              <div className="prose prose-lg max-w-none">
                <p>
                  The Workspace Management system provides complete multi-tenancy with workspace-scoped AI teams, 
                  goals, tasks, and deliverables. Each workspace functions as an isolated AI organization with 
                  its own memory, health monitoring, and autonomous recovery capabilities.
                </p>
              </div>
            </section>

            {/* Workspace Architecture */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <Database className="w-6 h-6 mr-3 text-indigo-600" />
                Workspace Architecture
              </h2>

              <div className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-lg p-6 border border-gray-200 mb-6">
                <h3 className="font-semibold text-gray-900 mb-4">Complete Data Isolation</h3>
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-semibold text-gray-800 mb-3">Workspace-Scoped Resources</h4>
                    <ul className="text-sm text-gray-600 space-y-2">
                      <li className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                        <span>**AI Agents & Teams** - Specialized agents per workspace</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-green-600 rounded-full"></div>
                        <span>**Goals & Objectives** - Strategic objectives and tracking</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-purple-600 rounded-full"></div>
                        <span>**Tasks & Execution** - Work breakdown and agent assignments</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-orange-600 rounded-full"></div>
                        <span>**Deliverables & Assets** - Generated outputs and documents</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-indigo-600 rounded-full"></div>
                        <span>**Memory System** - Workspace-specific learning patterns</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-red-600 rounded-full"></div>
                        <span>**Document Stores** - Vector stores and file management</span>
                      </li>
                    </ul>
                  </div>

                  <div className="bg-white rounded p-4 border border-gray-300">
                    <h4 className="font-semibold text-gray-800 mb-3">Database Schema</h4>
                    <div className="bg-gray-900 rounded p-3 text-xs">
                      <pre className="text-green-400 overflow-x-auto">
                        <code>{`-- Core workspace table
CREATE TABLE workspaces (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  status workspace_status DEFAULT 'active',
  created_at TIMESTAMP DEFAULT NOW(),
  settings JSONB DEFAULT '{}'
);

-- All resources reference workspace_id
CREATE TABLE workspace_goals (
  id UUID PRIMARY KEY,
  workspace_id UUID REFERENCES workspaces(id),
  description TEXT NOT NULL,
  -- ... other fields
);`}</code>
                      </pre>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-yellow-50 rounded-lg p-6 border border-yellow-200">
                <div className="flex items-start space-x-3">
                  <Shield className="w-6 h-6 text-yellow-600 mt-1" />
                  <div>
                    <h3 className="text-lg font-semibold text-yellow-900">Data Security & Isolation</h3>
                    <p className="text-yellow-700 mt-1">
                      Complete tenant isolation ensures workspace data never crosses boundaries. All database 
                      operations include workspace_id filtering, and AI agents only access workspace-scoped resources.
                    </p>
                  </div>
                </div>
              </div>
            </section>

            {/* Workspace Lifecycle */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <Activity className="w-6 h-6 mr-3 text-indigo-600" />
                Workspace Lifecycle & Status
              </h2>

              <div className="space-y-6">
                <div className="bg-gradient-to-r from-green-50 to-green-100 rounded-lg p-6 border border-green-200">
                  <div className="flex items-center space-x-3 mb-4">
                    <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center">
                      <CheckCircle className="w-5 h-5 text-white" />
                    </div>
                    <h3 className="font-semibold text-green-900">Active State</h3>
                    <span className="px-3 py-1 bg-green-200 text-green-800 text-xs rounded-full">Normal Operation</span>
                  </div>
                  <div className="grid md:grid-cols-3 gap-4">
                    <div>
                      <h4 className="font-semibold text-green-800 mb-2">Full Functionality</h4>
                      <ul className="text-sm text-green-700 space-y-1">
                        <li>• All AI agents operational</li>
                        <li>• Task execution running</li>
                        <li>• Goal tracking active</li>
                        <li>• Deliverable generation enabled</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-semibold text-green-800 mb-2">Health Monitoring</h4>
                      <ul className="text-sm text-green-700 space-y-1">
                        <li>• Real-time performance tracking</li>
                        <li>• Resource utilization monitoring</li>
                        <li>• Agent health checks</li>
                        <li>• Proactive issue detection</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-semibold text-green-800 mb-2">Autonomous Operations</h4>
                      <ul className="text-sm text-green-700 space-y-1">
                        <li>• Continuous task processing</li>
                        <li>• Automatic goal updates</li>
                        <li>• Self-healing capabilities</li>
                        <li>• Memory learning active</li>
                      </ul>
                    </div>
                  </div>
                </div>

                <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg p-6 border border-blue-200">
                  <div className="flex items-center space-x-3 mb-4">
                    <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                      <Activity className="w-5 h-5 text-white" />
                    </div>
                    <h3 className="font-semibold text-blue-900">Auto-Recovering State</h3>
                    <span className="px-3 py-1 bg-blue-200 text-blue-800 text-xs rounded-full">AI-Driven Recovery</span>
                  </div>
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-semibold text-blue-800 mb-2">Recovery Actions</h4>
                      <ul className="text-sm text-blue-700 space-y-1">
                        <li>• Failed task restart and reassignment</li>
                        <li>• Agent health restoration</li>
                        <li>• Resource reallocation</li>
                        <li>• Context reconstruction from memory</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-semibold text-blue-800 mb-2">Recovery Timeline</h4>
                      <ul className="text-sm text-blue-700 space-y-1">
                        <li>• **0-5s**: Issue detection and analysis</li>
                        <li>• **5-30s**: AI strategy selection</li>
                        <li>• **30s-2min**: Recovery execution</li>
                        <li>• **2min+**: Status verification and transition</li>
                      </ul>
                    </div>
                  </div>
                </div>

                <div className="bg-gradient-to-r from-orange-50 to-orange-100 rounded-lg p-6 border border-orange-200">
                  <div className="flex items-center space-x-3 mb-4">
                    <div className="w-8 h-8 bg-orange-600 rounded-full flex items-center justify-center">
                      <AlertTriangle className="w-5 h-5 text-white" />
                    </div>
                    <h3 className="font-semibold text-orange-900">Degraded Mode</h3>
                    <span className="px-3 py-1 bg-orange-200 text-orange-800 text-xs rounded-full">Reduced Functionality</span>
                  </div>
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-semibold text-orange-800 mb-2">Available Operations</h4>
                      <ul className="text-sm text-orange-700 space-y-1">
                        <li>• Basic task execution (reduced capacity)</li>
                        <li>• Limited agent functionality</li>
                        <li>• Essential goal tracking</li>
                        <li>• Fallback deliverable creation</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-semibold text-orange-800 mb-2">Recovery Path</h4>
                      <ul className="text-sm text-orange-700 space-y-1">
                        <li>• Continuous background recovery attempts</li>
                        <li>• Resource optimization strategies</li>
                        <li>• Gradual capability restoration</li>
                        <li>• Automatic transition to active when stable</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Health Monitoring System */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <TrendingUp className="w-6 h-6 mr-3 text-indigo-600" />
                AI-Driven Health Monitoring
              </h2>

              <div className="bg-gradient-to-r from-purple-50 to-purple-100 rounded-lg p-6 border border-purple-200 mb-6">
                <h3 className="font-semibold text-purple-900 mb-4">Proactive Health Detection</h3>
                <p className="text-purple-800 text-sm mb-4">
                  The health monitoring system continuously analyzes workspace patterns and proactively 
                  identifies issues before they cause failures.
                </p>

                <div className="grid md:grid-cols-3 gap-4">
                  <div className="bg-white rounded p-4 border border-purple-300">
                    <h4 className="font-semibold text-purple-900 mb-2">Performance Metrics</h4>
                    <ul className="text-sm text-purple-700 space-y-1">
                      <li>• Task completion rates</li>
                      <li>• Agent response times</li>
                      <li>• Goal progress velocity</li>
                      <li>• Resource utilization</li>
                    </ul>
                  </div>
                  <div className="bg-white rounded p-4 border border-purple-300">
                    <h4 className="font-semibold text-purple-900 mb-2">Error Pattern Analysis</h4>
                    <ul className="text-sm text-purple-700 space-y-1">
                      <li>• Failure frequency tracking</li>
                      <li>• Error type classification</li>
                      <li>• Recovery success patterns</li>
                      <li>• Bottleneck identification</li>
                    </ul>
                  </div>
                  <div className="bg-white rounded p-4 border border-purple-300">
                    <h4 className="font-semibold text-purple-900 mb-2">Predictive Indicators</h4>
                    <ul className="text-sm text-purple-700 space-y-1">
                      <li>• Memory usage trends</li>
                      <li>• Database connection health</li>
                      <li>• API rate limit proximity</li>
                      <li>• Context reconstruction needs</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <div className="bg-gray-50 rounded-lg p-6">
                  <h4 className="font-semibold text-gray-900 mb-4">Health Check Implementation</h4>
                  <div className="bg-gray-900 rounded p-4 text-sm">
                    <pre className="text-green-400 overflow-x-auto">
                      <code>{`# Workspace health monitoring
class WorkspaceHealthMonitor:
    async def check_workspace_health(
        self, workspace_id: str
    ) -> HealthStatus:
        
        # Multi-dimensional health check
        metrics = await self.gather_metrics(
            workspace_id
        )
        
        # AI-driven health scoring
        health_score = await self.ai_health_analyzer
            .calculate_health_score(metrics)
        
        # Proactive issue detection
        issues = await self.detect_potential_issues(
            metrics, health_score
        )
        
        return HealthStatus(
            score=health_score,
            issues=issues,
            recommendations=self.get_recommendations(issues)
        )`}</code>
                    </pre>
                  </div>
                </div>

                <div className="space-y-4">
                  <h4 className="font-semibold text-gray-900">Health Scoring System</h4>
                  <div className="space-y-3">
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-3 bg-green-500 rounded-full"></div>
                      <div>
                        <span className="font-semibold text-green-900">85-100%</span>
                        <p className="text-sm text-green-700">Excellent health - optimal performance</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-3 bg-yellow-500 rounded-full"></div>
                      <div>
                        <span className="font-semibold text-yellow-900">60-84%</span>
                        <p className="text-sm text-yellow-700">Good health - minor optimizations needed</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-3 bg-orange-500 rounded-full"></div>
                      <div>
                        <span className="font-semibold text-orange-900">40-59%</span>
                        <p className="text-sm text-orange-700">Fair health - proactive recovery triggered</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-3 bg-red-500 rounded-full"></div>
                      <div>
                        <span className="font-semibold text-red-900">0-39%</span>
                        <p className="text-sm text-red-700">Poor health - immediate recovery required</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Team & User Management */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <Users className="w-6 h-6 mr-3 text-indigo-600" />
                Team & User Management
              </h2>

              <div className="bg-blue-50 rounded-lg p-6 border border-blue-200 mb-6">
                <div className="flex items-start space-x-3">
                  <Users className="w-6 h-6 text-blue-600 mt-1" />
                  <div>
                    <h3 className="text-lg font-semibold text-blue-900">Dynamic AI Team Formation</h3>
                    <p className="text-blue-700 mt-1">
                      AI agents are dynamically created and assigned to workspaces based on project requirements. 
                      Teams can be scaled up or down automatically based on workload and complexity.
                    </p>
                  </div>
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-6 mb-6">
                <div>
                  <h4 className="font-semibold text-gray-900 mb-4">Agent Roles & Specializations</h4>
                  <div className="space-y-3">
                    <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                      <div className="w-3 h-3 bg-blue-600 rounded-full"></div>
                      <div>
                        <div className="font-semibold text-gray-800">Content Specialists</div>
                        <p className="text-xs text-gray-600">Marketing copy, blog posts, email campaigns</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                      <div className="w-3 h-3 bg-green-600 rounded-full"></div>
                      <div>
                        <div className="font-semibold text-gray-800">Technical Specialists</div>
                        <p className="text-xs text-gray-600">Code implementation, architecture, APIs</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                      <div className="w-3 h-3 bg-purple-600 rounded-full"></div>
                      <div>
                        <div className="font-semibold text-gray-800">Strategy Specialists</div>
                        <p className="text-xs text-gray-600">Business planning, market analysis, GTM</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                      <div className="w-3 h-3 bg-orange-600 rounded-full"></div>
                      <div>
                        <div className="font-semibold text-gray-800">Operations Specialists</div>
                        <p className="text-xs text-gray-600">Process optimization, QA, monitoring</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold text-gray-900 mb-4">Seniority Levels</h4>
                  <div className="space-y-3">
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold text-gray-800">Expert</span>
                        <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded">Advanced</span>
                      </div>
                      <p className="text-sm text-gray-600">Complex projects, strategic decisions, mentoring</p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold text-gray-800">Senior</span>
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">Experienced</span>
                      </div>
                      <p className="text-sm text-gray-600">Independent execution, quality delivery</p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold text-gray-800">Junior</span>
                        <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">Learning</span>
                      </div>
                      <p className="text-sm text-gray-600">Guided tasks, skill development</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-gray-100 rounded-lg p-6">
                <h4 className="font-semibold text-gray-900 mb-4">Team Management API</h4>
                <div className="bg-gray-900 rounded p-4 text-sm">
                  <pre className="text-green-400 overflow-x-auto">
                    <code>{`# Add team member
POST /api/workspaces/{workspace_id}/team
{
  "role": "Content Specialist",
  "seniority": "Senior", 
  "skills": ["B2B Marketing", "Email Campaigns"],
  "specialization": "SaaS Marketing"
}

# Get team status
GET /api/workspaces/{workspace_id}/team
{
  "team_members": [
    {
      "id": "agent_001",
      "role": "Content Specialist",
      "seniority": "Senior",
      "status": "active",
      "current_tasks": 3,
      "success_rate": 0.87
    }
  ]
}`}</code>
                  </pre>
                </div>
              </div>
            </section>

            {/* Configuration & Settings */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <Settings className="w-6 h-6 mr-3 text-indigo-600" />
                Configuration & Settings
              </h2>

              <div className="grid md:grid-cols-2 gap-6">
                <div className="bg-gray-50 rounded-lg p-6">
                  <h4 className="font-semibold text-gray-900 mb-4">Workspace Settings</h4>
                  <div className="space-y-3 text-sm">
                    <div>
                      <label className="font-semibold text-gray-800">Language & Localization</label>
                      <p className="text-gray-600">Primary language, timezone, date formats</p>
                    </div>
                    <div>
                      <label className="font-semibold text-gray-800">AI Behavior</label>
                      <p className="text-gray-600">Agent creativity, risk tolerance, collaboration style</p>
                    </div>
                    <div>
                      <label className="font-semibold text-gray-800">Resource Limits</label>
                      <p className="text-gray-600">Maximum agents, concurrent tasks, memory usage</p>
                    </div>
                    <div>
                      <label className="font-semibold text-gray-800">Quality Standards</label>
                      <p className="text-gray-600">QA gate thresholds, review requirements</p>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-lg p-6">
                  <h4 className="font-semibold text-gray-900 mb-4">Environment Variables</h4>
                  <div className="space-y-2 text-sm">
                    <div>
                      <code className="bg-gray-800 text-green-400 px-2 py-1 rounded text-xs">WORKSPACE_MAX_AGENTS=10</code>
                      <p className="text-xs text-gray-600 mt-1">Maximum agents per workspace</p>
                    </div>
                    <div>
                      <code className="bg-gray-800 text-green-400 px-2 py-1 rounded text-xs">WORKSPACE_HEALTH_CHECK_INTERVAL=300</code>
                      <p className="text-xs text-gray-600 mt-1">Health check frequency (seconds)</p>
                    </div>
                    <div>
                      <code className="bg-gray-800 text-green-400 px-2 py-1 rounded text-xs">WORKSPACE_MEMORY_RETENTION_DAYS=30</code>
                      <p className="text-xs text-gray-600 mt-1">Memory pattern retention</p>
                    </div>
                    <div>
                      <code className="bg-gray-800 text-green-400 px-2 py-1 rounded text-xs">AUTO_RECOVERY_ENABLED=true</code>
                      <p className="text-xs text-gray-600 mt-1">Enable autonomous recovery</p>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Performance Metrics */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Performance & Scalability</h2>

              <div className="grid md:grid-cols-4 gap-6 mb-6">
                <div className="bg-green-50 rounded-lg p-6 text-center border border-green-200">
                  <div className="text-3xl font-bold text-green-900 mb-2">100%</div>
                  <div className="text-sm text-green-700">Data isolation guarantee</div>
                </div>
                <div className="bg-blue-50 rounded-lg p-6 text-center border border-blue-200">
                  <div className="text-3xl font-bold text-blue-900 mb-2">99.9%</div>
                  <div className="text-sm text-blue-700">Health monitoring uptime</div>
                </div>
                <div className="bg-purple-50 rounded-lg p-6 text-center border border-purple-200">
                  <div className="text-3xl font-bold text-purple-900 mb-2">&lt; 30s</div>
                  <div className="text-sm text-purple-700">Average recovery time</div>
                </div>
                <div className="bg-orange-50 rounded-lg p-6 text-center border border-orange-200">
                  <div className="text-3xl font-bold text-orange-900 mb-2">1000+</div>
                  <div className="text-sm text-orange-700">Concurrent workspaces</div>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-6">
                <h4 className="font-semibold text-gray-900 mb-4">Scalability Features</h4>
                <div className="grid md:grid-cols-2 gap-6 text-sm text-gray-600">
                  <div>
                    <h5 className="font-semibold text-gray-800 mb-2">Horizontal Scaling</h5>
                    <ul className="space-y-1">
                      <li>• Database-agnostic architecture</li>
                      <li>• Stateless workspace services</li>
                      <li>• Load balancer compatibility</li>
                      <li>• Microservice-ready design</li>
                    </ul>
                  </div>
                  <div>
                    <h5 className="font-semibold text-gray-800 mb-2">Performance Optimization</h5>
                    <ul className="space-y-1">
                      <li>• Workspace-scoped caching</li>
                      <li>• Efficient database indexing</li>
                      <li>• Connection pooling</li>
                      <li>• Resource usage monitoring</li>
                    </ul>
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
                  <p className="text-sm text-gray-600">Workspace AI team management</p>
                </Link>

                <Link 
                  href="/docs/core-concepts/recovery"
                  className="block p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
                >
                  <Activity className="w-5 h-5 text-green-600 mb-2" />
                  <h3 className="font-semibold text-gray-900 mb-1">Recovery</h3>
                  <p className="text-sm text-gray-600">Autonomous health recovery</p>
                </Link>

                <Link 
                  href="/docs/operations/monitoring"
                  className="block p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
                >
                  <TrendingUp className="w-5 h-5 text-purple-600 mb-2" />
                  <h3 className="font-semibold text-gray-900 mb-1">Monitoring</h3>
                  <p className="text-sm text-gray-600">System health and metrics</p>
                </Link>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  )
}