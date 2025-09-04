'use client'

import React from 'react'
import Link from 'next/link'
import { ArrowLeft, Activity, AlertTriangle, CheckCircle, Copy, Terminal, Database } from 'lucide-react'

export default function MonitoringPage() {
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="mb-8">
            <Link 
              href="/docs"
              className="inline-flex items-center text-blue-600 hover:text-blue-800 transition-colors mb-4"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Documentation
            </Link>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Monitoring & Logging</h1>
            <p className="text-gray-600">System health monitoring, debugging, and performance optimization</p>
          </div>

          <div className="bg-white rounded-xl border p-8">
            <section className="mb-12">
              <div className="bg-blue-50 rounded-lg p-6 border border-blue-200 mb-6">
                <div className="flex items-center space-x-3">
                  <Activity className="w-6 h-6 text-blue-600" />
                  <div>
                    <h3 className="font-medium text-blue-900">Comprehensive Monitoring</h3>
                    <p className="text-blue-700 text-sm mt-1">Real-time system health, performance metrics, and intelligent alerting</p>
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-6 border border-green-200">
                  <h4 className="font-semibold text-green-900 mb-2">Health Monitoring</h4>
                  <p className="text-green-700 text-sm">System, database, and API health checks with scoring</p>
                </div>
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
                  <h4 className="font-semibold text-blue-900 mb-2">Performance Metrics</h4>
                  <p className="text-blue-700 text-sm">Response times, agent efficiency, and resource usage</p>
                </div>
                <div className="bg-gradient-to-br from-purple-50 to-violet-50 rounded-lg p-6 border border-purple-200">
                  <h4 className="font-semibold text-purple-900 mb-2">Intelligent Debugging</h4>
                  <p className="text-purple-700 text-sm">Structured logging with context and error tracking</p>
                </div>
              </div>
            </section>

            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Health Monitoring</h2>
              
              <div className="space-y-6">
                <div className="border rounded-lg p-6">
                  <div className="flex items-center space-x-3 mb-4">
                    <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">GET</span>
                    <code className="text-lg font-mono">/health</code>
                  </div>
                  <p className="text-gray-600 mb-4">Overall system health check with scored assessment</p>
                  
                  <div className="bg-gray-900 rounded-lg p-4 mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-gray-400 text-sm">Example Response</span>
                      <button 
                        onClick={() => copyToClipboard('curl -X GET "http://localhost:8000/health"')}
                        className="text-gray-400 hover:text-white transition-colors"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                    </div>
                    <pre className="text-green-400 text-sm overflow-x-auto">
                      <code>{`{
  "status": "healthy",
  "score": 95,
  "timestamp": "2025-01-01T14:30:00Z",
  "components": {
    "database": {
      "status": "connected",
      "response_time": "12ms",
      "active_connections": 8
    },
    "openai": {
      "status": "operational",
      "last_request": "2025-01-01T14:29:45Z",
      "rate_limit_remaining": 4850
    },
    "agents": {
      "active_agents": 12,
      "idle_agents": 3,
      "failed_agents": 0
    }
  },
  "version": "1.0.0",
  "uptime": 86400
}`}</code>
                    </pre>
                  </div>

                  <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                    <h4 className="font-medium text-blue-900 mb-2">Health Score Breakdown:</h4>
                    <ul className="space-y-1 text-blue-700 text-sm">
                      <li>• 90-100: Excellent health, all systems optimal</li>
                      <li>• 70-89: Good health, minor issues present</li>
                      <li>• 50-69: Fair health, attention needed</li>
                      <li>• Below 50: Poor health, immediate action required</li>
                    </ul>
                  </div>
                </div>

                <div className="border rounded-lg p-6">
                  <div className="flex items-center space-x-3 mb-4">
                    <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">GET</span>
                    <code className="text-lg font-mono">/api/monitoring/workspace/[id]/health</code>
                  </div>
                  <p className="text-gray-600 mb-4">Detailed workspace health and activity status</p>
                  
                  <div className="bg-gray-900 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-gray-400 text-sm">Workspace Health Response</span>
                    </div>
                    <pre className="text-green-400 text-sm overflow-x-auto">
                      <code>{`{
  "workspace_id": "workspace-uuid",
  "status": "active",
  "health_score": 92,
  "agent_status": {
    "total": 5,
    "active": 3,
    "idle": 2,
    "failed": 0
  },
  "task_metrics": {
    "pending": 2,
    "in_progress": 1,
    "completed": 18,
    "failed": 0
  },
  "goal_progress": {
    "total_goals": 3,
    "completed_goals": 1,
    "average_progress": 67.5
  },
  "last_activity": "2025-01-01T14:29:30Z",
  "issues": [],
  "performance": {
    "avg_task_completion_time": "45m",
    "agent_efficiency": 0.89
  }
}`}</code>
                    </pre>
                  </div>
                </div>
              </div>
            </section>

            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Logging System</h2>
              
              <div className="space-y-6">
                <div className="bg-gray-50 rounded-lg p-6 border">
                  <h3 className="font-medium text-gray-900 mb-4 flex items-center">
                    <Terminal className="w-5 h-5 mr-2" />
                    Structured Logging Format
                  </h3>
                  
                  <div className="bg-gray-900 rounded-lg p-4 mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-gray-400 text-sm">Log Entry Example</span>
                    </div>
                    <pre className="text-green-400 text-sm overflow-x-auto">
                      <code>{`[2025-01-01T14:30:15.123Z] INFO  [TaskExecutor] 
  Goal Progress Update: marketing-campaign-goal (75.5% -> 82.3%)
  Context: {
    "workspace_id": "ws-123",
    "goal_id": "goal-456", 
    "task_id": "task-789",
    "agent": "Marketing Strategist (Senior)",
    "deliverable": "Brand Positioning Document",
    "duration": "32m",
    "quality_score": 0.92
  }`}</code>
                    </pre>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">Log Levels:</h4>
                      <ul className="space-y-1 text-gray-600 text-sm">
                        <li>• ERROR - System errors, failures</li>
                        <li>• WARN - Warnings, fallbacks used</li>
                        <li>• INFO - Important events, progress</li>
                        <li>• DEBUG - Detailed execution info</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">Log Categories:</h4>
                      <ul className="space-y-1 text-gray-600 text-sm">
                        <li>• TaskExecutor - Task execution events</li>
                        <li>• AgentOrchestrator - Agent coordination</li>
                        <li>• GoalManager - Goal progress tracking</li>
                        <li>• QualityGates - Quality assurance</li>
                      </ul>
                    </div>
                  </div>
                </div>

                <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
                  <h3 className="font-medium text-blue-900 mb-4 flex items-center">
                    <Database className="w-5 h-5 mr-2" />
                    Common Monitoring Commands
                  </h3>
                  
                  <div className="space-y-4">
                    <div className="bg-gray-900 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-gray-400 text-sm">Monitor Goal Progress Updates</span>
                        <button 
                          onClick={() => copyToClipboard('grep "Goal Progress Update" backend/logs/*.log | tail -10')}
                          className="text-gray-400 hover:text-white transition-colors"
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                      </div>
                      <pre className="text-green-400 text-sm">
                        <code>grep "Goal Progress Update" backend/logs/*.log | tail -10</code>
                      </pre>
                    </div>

                    <div className="bg-gray-900 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-gray-400 text-sm">Check System Health</span>
                        <button 
                          onClick={() => copyToClipboard('curl -s localhost:8000/health | jq')}
                          className="text-gray-400 hover:text-white transition-colors"
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                      </div>
                      <pre className="text-green-400 text-sm">
                        <code>curl -s localhost:8000/health | jq</code>
                      </pre>
                    </div>

                    <div className="bg-gray-900 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-gray-400 text-sm">Find Error Patterns</span>
                        <button 
                          onClick={() => copyToClipboard('grep "ERROR\\|WARN" backend/logs/*.log | tail -20')}
                          className="text-gray-400 hover:text-white transition-colors"
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                      </div>
                      <pre className="text-green-400 text-sm">
                        <code>grep "ERROR\\|WARN" backend/logs/*.log | tail -20</code>
                      </pre>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Common Issues & Troubleshooting</h2>
              
              <div className="space-y-6">
                <div className="border rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-red-900 mb-4 flex items-center">
                    <AlertTriangle className="w-5 h-5 mr-2" />
                    Performance Issues (90+ second load times)
                  </h3>
                  
                  <div className="space-y-4">
                    <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                      <h4 className="font-medium text-red-900 mb-2">Symptoms:</h4>
                      <ul className="space-y-1 text-red-700 text-sm">
                        <li>• Frontend loading for 90+ seconds</li>
                        <li>• Unified-assets API extremely slow</li>
                        <li>• Users see "broken" or unresponsive interface</li>
                        <li>• Multiple cascading API calls</li>
                      </ul>
                    </div>

                    <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                      <h4 className="font-medium text-green-900 mb-2">Solutions:</h4>
                      <div className="space-y-2 text-green-700 text-sm">
                        <div>1. Check Progressive Loading Implementation</div>
                        <div>2. Monitor Unified-Assets API Performance</div>
                        <div>3. Restart Backend Services if Necessary</div>
                        <div>4. Implement Loading States for Better UX</div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="border rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-orange-900 mb-4 flex items-center">
                    <Database className="w-5 h-5 mr-2" />
                    Database Connection Issues
                  </h3>
                  
                  <div className="space-y-4">
                    <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
                      <h4 className="font-medium text-orange-900 mb-2">Common Symptoms:</h4>
                      <ul className="space-y-1 text-orange-700 text-sm">
                        <li>• Connection timeout errors</li>
                        <li>• Intermittent data loading failures</li>
                        <li>• Slow query performance</li>
                        <li>• Connection pool exhaustion</li>
                      </ul>
                    </div>

                    <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                      <h4 className="font-medium text-green-900 mb-2">Diagnostic Steps:</h4>
                      <div className="space-y-1 text-green-700 text-sm">
                        <li>• Check database connection pool status</li>
                        <li>• Monitor query execution times</li>
                        <li>• Verify environment configuration</li>
                        <li>• Review connection limits and timeouts</li>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Related Documentation</h2>
              <div className="space-y-3">
                <Link 
                  href="/docs/operations/performance"
                  className="flex items-center space-x-3 p-4 border rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all"
                >
                  <div className="p-2 bg-yellow-50 rounded-lg">
                    <Activity className="w-5 h-5 text-yellow-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Performance Optimization</h3>
                    <p className="text-gray-600 text-sm">Advanced performance tuning and scaling strategies</p>
                  </div>
                </Link>

                <Link 
                  href="/docs/operations/troubleshooting"
                  className="flex items-center space-x-3 p-4 border rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all"
                >
                  <div className="p-2 bg-red-50 rounded-lg">
                    <AlertTriangle className="w-5 h-5 text-red-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Troubleshooting Guide</h3>
                    <p className="text-gray-600 text-sm">Comprehensive problem diagnosis and solutions</p>
                  </div>
                </Link>

                <Link 
                  href="/docs/development/api"
                  className="flex items-center space-x-3 p-4 border rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all"
                >
                  <div className="p-2 bg-blue-50 rounded-lg">
                    <Database className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">API Reference</h3>
                    <p className="text-gray-600 text-sm">Complete API documentation with monitoring endpoints</p>
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