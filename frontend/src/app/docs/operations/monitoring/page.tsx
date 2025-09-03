'use client'

import React from 'react'
import Link from 'next/link'
import { ArrowLeft, Activity, AlertTriangle, CheckCircle, Copy, Terminal, Database, Zap, Clock, TrendingUp } from 'lucide-react'

export default function MonitoringPage() {
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

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
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Monitoring & Logging</h1>
            <p className="text-gray-600">System health monitoring, debugging, and performance optimization</p>
          </div>

          <div className="bg-white rounded-xl border p-8">
            {/* Overview */}
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

            {/* Health Endpoints */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Health Monitoring</h2>
              
              <div className="space-y-6">
                {/* System Health */}
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
                        onClick={() => copyToClipboard(`curl -X GET "http://localhost:8000/health"`)}
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
                      <li>• <code>90-100</code>: Excellent health, all systems optimal</li>
                      <li>• <code>70-89</code>: Good health, minor issues present</li>
                      <li>• <code>50-69</code>: Fair health, attention needed</li>
                      <li>• <code>Below 50</code>: Poor health, immediate action required</li>
                    </ul>
                  </div>
                </div>

                {/* Workspace Health */}
                <div className="border rounded-lg p-6">
                  <div className="flex items-center space-x-3 mb-4">
                    <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">GET</span>
                    <code className="text-lg font-mono">/api/monitoring/workspace/{`{id}`}/health</code>
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

            {/* Logging System */}
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
  🎯 Goal Progress Update: marketing-campaign-goal (75.5% -> 82.3%)
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
                        <li>• <code className="bg-red-100 text-red-800 px-1 rounded">ERROR</code> - System errors, failures</li>
                        <li>• <code className="bg-orange-100 text-orange-800 px-1 rounded">WARN</code> - Warnings, fallbacks used</li>
                        <li>• <code className="bg-blue-100 text-blue-800 px-1 rounded">INFO</code> - Important events, progress</li>
                        <li>• <code className="bg-gray-100 text-gray-800 px-1 rounded">DEBUG</code> - Detailed execution info</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">Log Categories:</h4>
                      <ul className="space-y-1 text-gray-600 text-sm">
                        <li>• <code>TaskExecutor</code> - Task execution events</li>
                        <li>• <code>AgentOrchestrator</code> - Agent coordination</li>
                        <li>• <code>GoalManager</code> - Goal progress tracking</li>
                        <li>• <code>QualityGates</code> - Quality assurance</li>
                      </ul>
                    </div>
                  </div>
                </div>

                {/* Log Analysis Commands */}
                <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
                  <h3 className="font-medium text-blue-900 mb-4 flex items-center">
                    <Database className="w-5 h-5 mr-2" />
                    Log Analysis Commands
                  </h3>
                  
                  <div className="space-y-4">
                    <div className="bg-gray-900 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-gray-400 text-sm">Monitor Goal Progress Updates</span>
                        <button 
                          onClick={() => copyToClipboard(`grep "Goal Progress Update" backend/logs/*.log | tail -10`)}
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
                        <span className="text-gray-400 text-sm">Check AI Goal Matcher Performance</span>
                        <button 
                          onClick={() => copyToClipboard(`grep "AI Goal Matcher:" backend/logs/*.log | grep "confidence:" | tail -5`)}
                          className="text-gray-400 hover:text-white transition-colors"
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                      </div>
                      <pre className="text-green-400 text-sm">
                        <code>grep "AI Goal Matcher:" backend/logs/*.log | grep "confidence:" | tail -5</code>
                      </pre>
                    </div>

                    <div className="bg-gray-900 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-gray-400 text-sm">Monitor Task Recovery</span>
                        <button 
                          onClick={() => copyToClipboard(`grep "AUTONOMOUS RECOVERY" backend/logs/*.log | tail -10`)}
                          className="text-gray-400 hover:text-white transition-colors"
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                      </div>
                      <pre className="text-green-400 text-sm">
                        <code>grep "AUTONOMOUS RECOVERY" backend/logs/*.log | tail -10</code>
                      </pre>
                    </div>

                    <div className="bg-gray-900 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-gray-400 text-sm">Find Error Patterns</span>
                        <button 
                          onClick={() => copyToClipboard(`grep "ERROR\\|WARN" backend/logs/*.log | grep -v "expected" | tail -20`)}
                          className="text-gray-400 hover:text-white transition-colors"
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                      </div>
                      <pre className="text-green-400 text-sm">
                        <code>grep "ERROR\\|WARN" backend/logs/*.log | grep -v "expected" | tail -20</code>
                      </pre>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Performance Monitoring */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Performance Monitoring</h2>
              
              <div className="space-y-6">
                <div className="bg-yellow-50 rounded-lg p-6 border border-yellow-200">
                  <h3 className="font-medium text-yellow-900 mb-4 flex items-center">
                    <Clock className="w-5 h-5 mr-2" />
                    Critical Performance Metrics
                  </h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-medium text-yellow-900 mb-2">Response Time Targets:</h4>
                      <ul className="space-y-1 text-yellow-700 text-sm">
                        <li>• <strong>Essential UI Load:</strong> &lt; 3 seconds</li>
                        <li>• <strong>API Responses:</strong> &lt; 500ms (typical)</li>
                        <li>• <strong>Database Queries:</strong> &lt; 100ms</li>
                        <li>• <strong>AI Operations:</strong> &lt; 30s (complex tasks)</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium text-yellow-900 mb-2">Resource Limits:</h4>
                      <ul className="space-y-1 text-yellow-700 text-sm">
                        <li>• <strong>Memory Usage:</strong> &lt; 2GB per workspace</li>
                        <li>• <strong>DB Connections:</strong> &lt; 20 active</li>
                        <li>• <strong>OpenAI Rate Limits:</strong> &lt; 80% usage</li>
                        <li>• <strong>WebSocket Connections:</strong> &lt; 100</li>
                      </ul>
                    </div>
                  </div>
                </div>

                {/* Performance Commands */}
                <div className="bg-green-50 rounded-lg p-6 border border-green-200">
                  <h3 className="font-medium text-green-900 mb-4 flex items-center">
                    <TrendingUp className="w-5 h-5 mr-2" />
                    Performance Diagnostic Commands
                  </h3>
                  
                  <div className="space-y-4">
                    <div className="bg-gray-900 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-gray-400 text-sm">Monitor API Response Times</span>
                      </div>
                      <pre className="text-green-400 text-sm overflow-x-auto">
                        <code>grep "took [0-9]* ms" backend/logs/*.log | awk '{{print $(NF-1)}}' | sort -n | tail -20</code>
                      </pre>
                    </div>

                    <div className="bg-gray-900 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-gray-400 text-sm">Check for Slow Operations</span>
                      </div>
                      <pre className="text-green-400 text-sm overflow-x-auto">
                        <code>grep "took [5-9][0-9]* seconds\\|took [0-9][0-9][0-9]* seconds" backend/logs/*.log</code>
                      </pre>
                    </div>

                    <div className="bg-gray-900 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-gray-400 text-sm">Memory Usage Monitoring</span>
                      </div>
                      <pre className="text-green-400 text-sm overflow-x-auto">
                        <code>ps aux | grep "python.*main.py" | awk '{{print "Memory: " $6/1024 "MB, CPU: " $3 "%"}}'</code>
                      </pre>
                    </div>

                    <div className="bg-gray-900 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-gray-400 text-sm">Database Connection Health</span>
                      </div>
                      <pre className="text-green-400 text-sm overflow-x-auto">
                        <code>curl -s localhost:8000/health | jq '.components.database'</code>
                      </pre>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Common Issues & Solutions */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Common Issues & Troubleshooting</h2>
              
              <div className="space-y-6">
                {/* Performance Issues */}
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
                        <div>1. <strong>Check Progressive Loading:</strong></div>
                        <div className="ml-4 bg-gray-900 rounded p-2 text-green-400 font-mono text-xs">
                          grep "Progressive loading" frontend/src/hooks/useConversationalWorkspace.ts
                        </div>
                        
                        <div>2. <strong>Monitor Unified-Assets Usage:</strong></div>
                        <div className="ml-4 bg-gray-900 rounded p-2 text-green-400 font-mono text-xs">
                          grep "unified-assets" backend/logs/*.log | grep "took.*seconds"
                        </div>
                        
                        <div>3. <strong>Restart Backend Services:</strong></div>
                        <div className="ml-4 bg-gray-900 rounded p-2 text-green-400 font-mono text-xs">
                          pkill -f "python.*main.py" && cd backend && python3 main.py &
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Goal-Deliverable Mapping Issues */}
                <div className="border rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-orange-900 mb-4 flex items-center">
                    <Database className="w-5 h-5 mr-2" />
                    Goal-Deliverable Mapping Issues
                  </h3>
                  
                  <div className="space-y-4">
                    <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
                      <h4 className="font-medium text-orange-900 mb-2">Symptoms:</h4>
                      <ul className="space-y-1 text-orange-700 text-sm">
                        <li>• "No deliverables available yet" in frontend</li>
                        <li>• Deliverables appearing under wrong goals</li>
                        <li>• Incorrect goal progress calculations</li>
                        <li>• AI Goal Matcher confidence warnings</li>
                      </ul>
                    </div>

                    <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                      <h4 className="font-medium text-green-900 mb-2">Diagnostic Commands:</h4>
                      <div className="space-y-2 text-green-700 text-sm">
                        <div className="bg-gray-900 rounded p-2 text-green-400 font-mono text-xs">
                          curl localhost:8000/api/deliverables/workspace/&#123;id&#125; | jq 'length'
                        </div>
                        <div className="bg-gray-900 rounded p-2 text-green-400 font-mono text-xs">
                          grep "AI Goal Matcher:" backend/logs/*.log | tail -10
                        </div>
                        <div className="bg-gray-900 rounded p-2 text-green-400 font-mono text-xs">
                          grep "Emergency fallback: Using first active goal" backend/logs/*.log | wc -l
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* WebSocket Connection Issues */}
                <div className="border rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-blue-900 mb-4 flex items-center">
                    <Zap className="w-5 h-5 mr-2" />
                    WebSocket Connection Issues
                  </h3>
                  
                  <div className="space-y-4">
                    <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                      <h4 className="font-medium text-blue-900 mb-2">Common Issues:</h4>
                      <ul className="space-y-1 text-blue-700 text-sm">
                        <li>• Real-time thinking processes not displaying</li>
                        <li>• WebSocket timeout errors (5-second timeout too aggressive)</li>
                        <li>• Connection drops during goal transitions</li>
                        <li>• Race conditions in state management</li>
                      </ul>
                    </div>

                    <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                      <h4 className="font-medium text-green-900 mb-2">Solutions:</h4>
                      <div className="space-y-2 text-green-700 text-sm">
                        <div>• Check <code>useWorkspaceWebSocket.ts</code> timeout settings (should be 10s+)</div>
                        <div>• Monitor WebSocket connection status in browser DevTools</div>
                        <div>• Verify WebSocket endpoint accessibility</div>
                        <div>• Check for port conflicts or firewall issues</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Alerting Configuration */}
            <section className="mb-12">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Monitoring Alerts</h2>
              
              <div className="bg-purple-50 rounded-lg p-6 border border-purple-200">
                <h3 className="font-medium text-purple-900 mb-4">Recommended Alert Thresholds</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-medium text-purple-900 mb-2">System Health:</h4>
                    <ul className="space-y-1 text-purple-700 text-sm">
                      <li>• Health score &lt; 70 → Warning</li>
                      <li>• Health score &lt; 50 → Critical</li>
                      <li>• Database response &gt; 500ms → Warning</li>
                      <li>• OpenAI rate limit &gt; 90% → Warning</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-medium text-purple-900 mb-2">Performance:</h4>
                    <ul className="space-y-1 text-purple-700 text-sm">
                      <li>• API response &gt; 5s → Critical</li>
                      <li>• Memory usage &gt; 2GB → Warning</li>
                      <li>• Failed tasks &gt; 5% → Warning</li>
                      <li>• WebSocket disconnects &gt; 10/min → Warning</li>
                    </ul>
                  </div>
                </div>

                <div className="mt-4 bg-white rounded-lg p-4 border border-purple-200">
                  <h4 className="font-medium text-purple-900 mb-2">Sample Alert Script:</h4>
                  <div className="bg-gray-900 rounded p-3">
                    <pre className="text-purple-400 text-sm overflow-x-auto">
                      <code>{`#!/bin/bash
# health_check_alert.sh
HEALTH_SCORE=$(curl -s localhost:8000/health | jq '.score')

if [ "$HEALTH_SCORE" -lt 50 ]; then
  echo "CRITICAL: System health score: $HEALTH_SCORE"
  # Send alert to monitoring system
elif [ "$HEALTH_SCORE" -lt 70 ]; then
  echo "WARNING: System health score: $HEALTH_SCORE" 
fi`}</code>
                    </pre>
                  </div>
                </div>
              </div>
            </section>

            {/* Next Steps */}
            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Related Documentation</h2>
              <div className="space-y-3">
                <Link 
                  href="/docs/operations/performance"
                  className="flex items-center space-x-3 p-4 border rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all"
                >
                  <div className="p-2 bg-yellow-50 rounded-lg">
                    <TrendingUp className="w-5 h-5 text-yellow-600" />
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